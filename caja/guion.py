"""Validación del guion de escenas (storyboard). Un guion mal formado (por ejemplo, uno generado por una IA) se rechaza con un
mensaje claro en lugar de producir un vídeo roto.

Reglas fijas de la marca:
  · La PRIMERA escena es siempre un «gancho» (frena el scroll en el primer segundo) y la ÚLTIMA siempre un «cta» (Síguenos en WhaleXtreet).
  · Ninguna frase puede prometer ganancias ni ausencia de riesgo (lista PROHIBIDAS).

Formato (JSON):
{
  "tema": "bolsa",                      # cripto | bolsa | alerta | macro | educativo  -> color de acento
  "tipo_post": "datos",                 # tipo de post de la agencia -> cuándo sale el profesor (formatos_video.json)
  "etiqueta": "BOLSA · ACCIONES",       # opcional, texto de la píldora de arriba (máx. 24)
  "ilustrativo": true,                  # opcional: añade «Gráficos ilustrativos, sin datos reales» al pie
  "escenas": [
    {"tipo": "gancho", "voz": "...", "texto": "¿COMPRASTE PORQUE SUBÍA?", "resalte": "SUBÍA", "icono": "alerta"},
    {"tipo": "numero", "voz": "...", ...},          # escenas intermedias: titulo, numero, grafico, barras, donut, lista, tarjetas, pregunta
    {"tipo": "cta"}                                 # «voz», texto y redes salen de marca/redes.json si no se indican
  ]
}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from escenas import ESCENAS, marca_redes, norm  # noqa: E402
from paletas import TEMAS  # noqa: E402

MIN_ESCENAS, MAX_ESCENAS = 3, 12
PROHIBIDAS = ["garantizado", "garantizada", "garantizados", "garantizadas", "sin riesgo", "dinero facil", "hazte rico", "ganancia segura",
              "ganancias seguras", "100% seguro", "seguro que ganas", "no puedes perder"]


def _textos(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from _textos(v)
    elif isinstance(x, list):
        for v in x:
            yield from _textos(v)


def validar(sb):
    errores = []
    if not isinstance(sb, dict):
        raise ValueError("el guion debe ser un objeto JSON")
    if sb.get("tema") not in TEMAS:
        errores.append(f"«tema» debe ser uno de {sorted(TEMAS)}")
    if not isinstance(sb.get("tipo_post", "datos"), str):
        errores.append("«tipo_post» debe ser texto")
    modo = sb.get("avatar", "profesor")
    if modo not in ("profesor", "rubio", "ambos"):
        errores.append("«avatar» debe ser «profesor», «rubio» o «ambos» (los dos, para conversaciones)")
    if sb.get("subs", "subrayado") not in ("subrayado", "recuadro"):
        errores.append("«subs» debe ser «subrayado» (por defecto) o «recuadro» (la palabra activa en un cuadro de color)")
    v = sb.get("etiqueta")
    if v is not None and (not isinstance(v, str) or not v or len(v) > 24):
        errores.append("«etiqueta» debe ser un texto de hasta 24 caracteres")
    esc = sb.get("escenas")
    if not isinstance(esc, list) or not MIN_ESCENAS <= len(esc) <= MAX_ESCENAS:
        errores.append(f"«escenas» debe ser una lista de {MIN_ESCENAS} a {MAX_ESCENAS} escenas")
        esc = []
    if esc:
        if not isinstance(esc[0], dict) or esc[0].get("tipo") != "gancho":
            errores.append("la primera escena debe ser un «gancho» (obligatorio: frena el scroll en el primer segundo)")
        if not isinstance(esc[-1], dict) or esc[-1].get("tipo") != "cta":
            errores.append("la última escena debe ser un «cta» (obligatorio: «Síguenos en WhaleXtreet»)")
        for i, e in enumerate(esc[1:-1], 2):
            if isinstance(e, dict) and e.get("tipo") in ("gancho", "cta"):
                errores.append(f"escena {i}: «{e['tipo']}» solo puede ir {'al principio' if e['tipo'] == 'gancho' else 'al final'}")
    cfg = marca_redes()
    for i, e in enumerate(esc, 1):
        def err(m, i=i, e=e):
            errores.append(f"escena {i} ({e.get('tipo') if isinstance(e, dict) else '?'}): {m}")
        if not isinstance(e, dict) or e.get("tipo") not in ESCENAS:
            errores.append(f"escena {i}: «tipo» debe ser uno de {sorted(ESCENAS)}")
            continue
        if "habla" in e:
            if e["habla"] not in ("profesor", "rubio"):
                err("«habla» debe ser «profesor» o «rubio»")
            elif modo != "ambos" and e["habla"] != modo:
                err(f"habla «{e['habla']}» pero el vídeo es de «{modo}»: usa «avatar»: «ambos» para que hablen los dos")
        if e["tipo"] == "dialogo" and modo != "ambos":
            err("las escenas «dialogo» solo existen en vídeos con «avatar»: «ambos»")
        voz = e.get("voz")
        if e["tipo"] == "cta" and not voz:
            voz = cfg["cta_voz"]
        if not isinstance(voz, str) or not voz.strip():
            err("falta «voz» (el texto que se locuta)")
        elif len(voz) > 300:
            err(f"«voz» es demasiado larga ({len(voz)} > 300 caracteres)")
        elif e["tipo"] == "gancho" and len(voz) > 110:
            err(f"la «voz» del gancho debe ser corta (máx. 110 caracteres; tiene {len(voz)}): el gancho dura 2-4 segundos")
        elif e["tipo"] == "gancho" and len(voz.split()) > MAX_PALABRAS_GANCHO:
            err(f"la «voz» del gancho tiene {len(voz.split())} palabras: máximo {MAX_PALABRAS_GANCHO} (se dice en menos de 3 segundos)")
        elif e["tipo"] == "gancho" and norm_espacios(voz).lstrip("¡¿ ").startswith(APERTURAS_PROHIBIDAS):
            err("el gancho no puede empezar con «Hola», «¿Sabías que…?», «En este vídeo…», «Hoy vamos a hablar de…» ni fórmulas genéricas: empieza directo con el golpe")
        ESCENAS[e["tipo"]][1](e, err)
    vistos = {}
    for i, e in enumerate(esc, 1):          # la misma animación dos veces en un vídeo se nota: cada metáfora, una sola vez
        m = e.get("motivo") if isinstance(e, dict) and e.get("tipo") in ("metafora", "gancho") else None
        if m:
            if m in vistos:
                errores.append(f"escena {i}: el motivo «{m}» ya se usó en la escena {vistos[m]}; elige otra metáfora")
            vistos.setdefault(m, i)
    for t in _textos({"tema": sb.get("tema"), "escenas": esc}):
        for frase in PROHIBIDAS:
            if frase in norm_espacios(t):
                errores.append(f"frase prohibida «{frase}» en «{t[:50]}»: la marca no promete ganancias ni ausencia de riesgo")
    if errores:
        raise ValueError("Guion de escenas no válido:\n - " + "\n - ".join(errores))
    out = dict(sb)
    out.setdefault("tipo_post", "datos")
    out.setdefault("ilustrativo", True)
    out["escenas"] = [dict(e, voz=cfg["cta_voz"]) if e["tipo"] == "cta" and not e.get("voz") else e for e in esc]
    return out


MAX_PALABRAS_GANCHO = 15
APERTURAS_PROHIBIDAS = ("hola", "sabias que", "en este video", "hoy vamos", "hoy hablamos", "hoy hablaremos", "hoy te cuento", "hoy te ensenare",
                        "te ensenare", "te voy a ensenar", "te ensenio", "bienvenid", "buenas", "vamos a ver")


def norm_espacios(t):
    """Minúsculas, sin tildes y con espacios simples, para buscar frases prohibidas."""
    import re
    import unicodedata
    s = unicodedata.normalize("NFD", t.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s)


def hablantes(sb):
    """Quién habla en cada escena: «profesor» o «rubio». Por defecto, el avatar del vídeo (en «ambos», el profesor)."""
    modo = sb.get("avatar", "profesor")
    defecto = modo if modo in ("profesor", "rubio") else "profesor"
    return [e.get("habla") or defecto for e in sb["escenas"]]


def lineas(sb):
    """Una línea de voz por escena: {"l1": "...", "l2": "..."} (el cta usa la voz de marca/redes.json si no trae)."""
    cfg = marca_redes()
    return {f"l{i}": (e.get("voz") or cfg["cta_voz"]).strip() for i, e in enumerate(sb["escenas"], 1)}
