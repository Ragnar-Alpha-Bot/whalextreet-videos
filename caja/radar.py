"""Radar de formatos: aprende de shorts que ya han funcionado (en cualquier idioma) y los adapta al español, a la marca y a datos REALES.

Qué se toma de un vídeo viral: el TEMA, la FÓRMULA del gancho (el tipo y la idea), la ESTRUCTURA (qué pasa y cuándo) y el tipo de cierre.
Qué NO se toma: su guion traducido palabra por palabra, sus cifras, sus imágenes, su voz ni sus afirmaciones sin comprobar. Todo se vuelve a escribir
con nuestra voz y con cifras reales y fechadas (ver fidelidad.py). Una ficha guarda solo una cita corta del gancho original (máx. 25 palabras) para poder
estudiarlo, nunca el guion entero.

Flujo:
  1. Buscar vídeos que funcionan en el nicho (YouTube Shorts y TikTok, en español e inglés) y anotar sus cifras y su transcripción.
  2. Escribir una ficha en radar/fichas/<id>.json (ver radar/README.md) y validarla:  python caja/radar.py validar
  3. Reunir los DATOS REALES del tema (radar/datos/<id>.json) y construir el encargo:  python caja/radar.py encargo <id>
  4. El encargo se convierte en un guion de escenas (Gemini con storyboard_ia.py, o a mano) y sigue el pipeline de siempre.

    python caja/radar.py lista             # fichas ordenadas por visualizaciones
    python caja/radar.py validar           # comprueba todas las fichas
    python caja/radar.py encargo <id>      # escribe el texto del encargo (y lo muestra)
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import fidelidad  # noqa: E402

CARPETA = RAIZ / "radar" / "fichas"
DATOS = RAIZ / "radar" / "datos"
PLATAFORMAS = ("youtube_shorts", "tiktok", "instagram_reels")
EVIDENCIAS = ("transcripcion", "descripcion", "visto_a_mano")
TIPOS_GANCHO = ("contraste_cifras", "lista_numerada", "pregunta_directa", "error_costoso", "verdad_incomoda", "regla_simple", "reto")
MAX_CITA = 25            # palabras de gancho original que se guardan (una cita para estudiar, no el guion)
MAX_PARECIDO = 0.25      # si la fuente está en español: como mucho esta fracción de secuencias de 4 palabras puede coincidir con el gancho adaptado


def cargar(ruta):
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def fichas():
    return [cargar(p) for p in sorted(CARPETA.glob("*.json"))]


def _palabras(t):
    return re.findall(r"[\wáéíóúüñ]+", str(t).lower())


def parecido(a, b, n=4):
    """Fracción de secuencias de n palabras de `a` que también aparecen en `b` (0-1). Sirve para no copiar frases de una fuente en el mismo idioma."""
    pa, pb = _palabras(a), _palabras(b)
    ga = {tuple(pa[i:i + n]) for i in range(len(pa) - n + 1)}
    gb = {tuple(pb[i:i + n]) for i in range(len(pb) - n + 1)}
    return len(ga & gb) / len(ga) if ga else 0.0


def _texto_adaptable(f):
    """Todo el texto de la ficha que se pasa al generador de guiones (no puede llevar cifras del vídeo original)."""
    fo, ad = f.get("formula", {}), f.get("adaptar", {})
    return " ".join([fo.get("tema", ""), fo.get("promesa", ""), fo.get("cierre", ""), fo.get("visual", ""), ad.get("tema_es", ""), ad.get("idea_gancho_es", ""),
                     " ".join(b.get("beat", "") for b in fo.get("estructura", [])), " ".join(ad.get("cuidado", []))])


def validar(f):
    """Lista de problemas de una ficha (vacía = correcta)."""
    err = []
    for k in ("id", "plataforma", "url", "idioma", "titulo_original", "metricas", "consultado", "duracion_s", "evidencia", "gancho_original", "formula", "por_que_funciona", "adaptar"):
        if k not in f:
            err.append(f"falta «{k}»")
    if err:
        return err
    if f["plataforma"] not in PLATAFORMAS:
        err.append(f"plataforma debe ser una de {PLATAFORMAS}")
    if f["evidencia"] not in EVIDENCIAS:
        err.append(f"evidencia debe ser una de {EVIDENCIAS}")
    if not str(f["url"]).startswith("https://"):
        err.append("la url debe empezar por https://")
    v = (f["metricas"] or {}).get("vistas")
    if not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0:
        err.append("metricas.vistas debe ser un número real")
    if len(_palabras(f["gancho_original"])) > MAX_CITA:
        err.append(f"gancho_original es una cita para estudiar: máximo {MAX_CITA} palabras (no se guarda el guion entero)")
    fo, ad = f["formula"], f["adaptar"]
    if fo.get("tipo_gancho") not in TIPOS_GANCHO:
        err.append(f"formula.tipo_gancho debe ser uno de {TIPOS_GANCHO}")
    if not isinstance(fo.get("estructura"), list) or len(fo["estructura"]) < 3 or not all(isinstance(b, dict) and b.get("beat") for b in fo["estructura"]):
        err.append("formula.estructura necesita al menos 3 pasos con «beat»")
    for k in ("tema_es", "idea_gancho_es", "datos_reales_necesarios"):
        if not ad.get(k):
            err.append(f"adaptar.{k} es obligatorio")
    grandes = sorted(n for n in fidelidad.numeros(_texto_adaptable(f)) if n > fidelidad.SIEMPRE_OK)
    if grandes:
        err.append(f"el texto de la ficha lleva cifras ({', '.join(f'{n:g}' for n in grandes)}): las cifras del vídeo original no se pasan; se usan datos reales propios")
    return err


def estructura(f):
    return " → ".join(f"({b.get('seg', '?')} s) {b['beat']}" for b in f["formula"]["estructura"])


def brief(f):
    """Texto del encargo: la fórmula a seguir, SIN cifras ni frases del original."""
    fo, ad = f["formula"], f["adaptar"]
    lineas = [
        f"ADAPTACIÓN AL ESPAÑOL DE UN FORMATO QUE YA HA FUNCIONADO (tema: {fo['tema']}).",
        f"Fórmula del gancho: «{fo['tipo_gancho']}». Idea del gancho en español: {ad['idea_gancho_es']}",
        f"Estructura a seguir: {estructura(f)}.",
        f"Cierre: {fo.get('cierre', 'el de siempre')}.",
        f"Tema para el público de España: {ad['tema_es']}.",
        "Cuidado: " + "; ".join(ad.get("cuidado", [])) + "." if ad.get("cuidado") else "",
    ]
    return "\n".join(x for x in lineas if x)


def encargo(f, datos, oferta=None, plataformas=("tiktok", "youtube", "instagram")):
    """Convierte una ficha y sus datos reales en un «post» para el generador de guiones (storyboard_ia.crear).

    datos = {"texto": ["frase con cifra real y su fuente y fecha", ...], "serie": {...opcional, para un gráfico real...}}.
    El texto del post (parts) = el encargo + los datos reales: es la fuente que usa fidelidad.py, así que solo estas cifras pueden salir en el vídeo.
    """
    problemas = validar(f)
    if problemas:
        raise ValueError("ficha no válida: " + "; ".join(problemas))
    if not datos or not datos.get("texto"):
        raise ValueError("faltan los datos reales del tema (radar/datos/<id>.json)")
    post = {"id": "radar-" + f["id"], "format": "radar", "platforms": list(plataformas),
            "parts": [brief(f), "DATOS REALES (úsalos tal cual, con su fecha): " + " ".join(datos["texto"])],
            "radar": {"id": f["id"], "tipo_gancho": f["formula"]["tipo_gancho"], "idioma_original": f["idioma"], "metricas": f["metricas"], "adaptar": f["adaptar"]["idea_gancho_es"]}}
    if datos.get("serie"):
        post["chart"] = datos["serie"]
    if oferta:
        post["oferta"] = oferta
    return post


def revisar_adaptacion(f, storyboard):
    """Problemas de una adaptación ya escrita: no copia el gancho (si la fuente está en español) y no arrastra cifras del original."""
    out = []
    voz_gancho = " ".join(e.get("voz", "") for e in storyboard["escenas"][:1])
    if f["idioma"] == "es" and parecido(voz_gancho, f["gancho_original"]) > MAX_PARECIDO:
        out.append("el gancho se parece demasiado al original (misma lengua): reescríbelo con tus palabras")
    return out


def main(argv):
    if not argv or argv[0] == "lista":
        for f in sorted(fichas(), key=lambda x: -x["metricas"]["vistas"]):
            print(f"{f['metricas']['vistas']:>12,} | {f['plataforma']:<14} | {f['formula']['tipo_gancho']:<18} | {f['id']} | {f['titulo_original'][:50]}")
        return 0
    if argv[0] == "validar":
        mal = 0
        for f in fichas():
            p = validar(f)
            print(("✖ " if p else "✔ ") + f.get("id", "?") + ("" if not p else ": " + "; ".join(p)))
            mal += bool(p)
        return 1 if mal else 0
    if argv[0] == "encargo" and len(argv) > 1:
        f = cargar(CARPETA / f"{argv[1]}.json")
        post = encargo(f, cargar(DATOS / f"{argv[1]}.json"))
        print("\n\n".join(post["parts"]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
