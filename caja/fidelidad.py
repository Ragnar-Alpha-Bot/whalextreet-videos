"""Fidelidad de las cifras: un vídeo hecho a partir de un post aprobado no puede inventar datos.

Toda cifra que se muestre (valor, puntos de un gráfico, barras, porcentajes, tarjetas, textos) debe aparecer en el post o en sus datos,
salvo en escenas marcadas «ilustrativo»: true (solo gráfico, barras, barras3d, donut y número), cuyo título debe decir «ilustrativo».
Los números pequeños (≤ 10, como «3 señales») se permiten siempre.
"""
import json
import re

_NUM = re.compile(r"\d[\d.,]*")


def _sin_espacios(s):
    return re.sub(r"\s+", "", str(s)).lower()
SIEMPRE_OK = 10


def _a_float(token):
    t = token.strip(".,")
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    elif "." in t and re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    try:
        return float(t)
    except ValueError:
        return None


def numeros(texto):
    """Todos los números de un texto, como float (acepta 1.234,5 · 12,4 % · 3.2)."""
    return {n for n in (_a_float(t) for t in _NUM.findall(str(texto))) if n is not None}


def numeros_de(obj):
    """Números dentro de cualquier estructura (texto, listas, diccionarios, números sueltos)."""
    if isinstance(obj, bool):
        return set()
    if isinstance(obj, (int, float)):
        return {float(obj)}
    if isinstance(obj, str):
        return numeros(obj)
    if isinstance(obj, dict):
        return set().union(*[numeros_de(v) for v in obj.values()]) if obj else set()
    if isinstance(obj, (list, tuple)):
        return set().union(*[numeros_de(v) for v in obj]) if obj else set()
    return set()


def _cerca(n, permitidos):
    return any(abs(n - p) <= max(0.051, abs(p) * 0.0005) for p in permitidos)


def _visibles(e):
    """Campos de una escena que se ven en pantalla (los números de la voz se revisan aparte: van en letra)."""
    t = e["tipo"]
    if t == "gancho":
        return [e.get("texto"), e.get("subtexto"), e.get("kicker"), (e.get("cifra") or {}).get("valor")]
    if t == "titulo":
        return [e.get("titulo"), e.get("subtitulo"), e.get("etiqueta")]
    if t == "numero":
        return [e.get("valor"), e.get("delta"), e.get("etiqueta"), e.get("detalle"), e.get("prefijo"), e.get("sufijo")]
    if t == "grafico":
        return [e.get("titulo"), e.get("puntos"), e.get("etiquetas"), [a.get("texto") for a in e.get("anotaciones", [])]]
    if t in ("barras", "barras3d"):
        return [e.get("titulo"), [(x.get("n"), x.get("v")) for x in e.get("items", [])]]
    if t in ("moneda3d", "esfera3d"):
        return [e.get("titulo"), e.get("subtitulo")]
    if t in ("donut", "donut3d"):
        return [e.get("titulo"), [(x.get("n"), x.get("v")) for x in e.get("segmentos", [])]]
    if t == "lista":
        return [e.get("titulo"), [x if isinstance(x, str) else x.get("t") for x in e.get("items", [])]]
    if t == "tarjetas":
        return [e.get("titulo"), [(x.get("etiqueta"), x.get("valor"), x.get("nota")) for x in e.get("items", [])]]
    if t == "metafora":
        return [e.get("titulo"), e.get("subtitulo"), e.get("sello")]
    if t == "ranking":
        return [e.get("titulo"), [(x.get("valor"), x.get("t"), x.get("sub")) for x in e.get("items", []) if isinstance(x, dict)]]
    if t == "terminal":
        return [e.get("titulo"), [(x if isinstance(x, str) else x.get("t")) for x in e.get("lineas", [])]]
    if t == "captura":
        return [e.get("titulo"), e.get("pie")]
    if t == "versus":
        return [e.get("ronda"), [(e.get(l) or {}).get("texto") for l in ("novato", "pro")], [(e.get(l) or {}).get("etiqueta") for l in ("novato", "pro")]]
    if t == "movil":
        return [e.get("titulo"), [x.get("t") for x in e.get("mensajes", []) if isinstance(x, dict)], e.get("sello")]
    if t == "calendario":
        return [e.get("titulo"), e.get("pie"), e.get("etiqueta")]
    if t == "panel":
        return [e.get("titulo"), e.get("busqueda"), [(x.get("n"), x.get("valor"), x.get("sub"), x.get("badge")) for x in e.get("items", []) if isinstance(x, dict)]]
    if t == "pasos":
        return [e.get("fase"), e.get("titulo"), [(x.get("n"), x.get("etiqueta")) for x in e.get("items", []) if isinstance(x, dict)]]
    if t == "checklist":
        return [e.get("titulo"), e.get("etiqueta"), [x if isinstance(x, str) else x.get("t") for x in e.get("items", [])]]
    if t == "dialogo":
        return [e.get("texto")]
    if t == "pregunta":
        return [e.get("pregunta"), [x if isinstance(x, str) else x.get("t") for x in e.get("opciones", [])]]
    return []


def comprobar(sb, texto_fuente, datos=None):
    """Devuelve la lista de problemas (vacía = todo trazable). texto_fuente: texto del post; datos: datos reales del post (opcional)."""
    permitidos = numeros(texto_fuente) | numeros_de(datos or {})
    problemas = []
    for i, e in enumerate(sb["escenas"], 1):
        if e.get("ilustrativo"):
            if e["tipo"] not in ("grafico", "barras", "barras3d", "donut", "donut3d", "numero"):
                problemas.append(f"escena {i} ({e['tipo']}): solo grafico, barras, barras3d, donut y numero pueden ser ilustrativos")
            elif "ilustrativo" not in str(e.get("titulo") or e.get("etiqueta") or "").lower():
                problemas.append(f"escena {i} ({e['tipo']}): una escena ilustrativa debe decir «(ilustrativo)» en su título o etiqueta")
            continue
        if e["tipo"] in ("ranking", "panel"):                       # las cifras del ranking son datos: valen aunque sean pequeñas (3,86x), no hay «número libre»
            for x in e.get("items", []):
                for n in sorted(numeros_de(x.get("valor") if isinstance(x, dict) else None)):
                    if not _cerca(n, permitidos):
                        problemas.append(f"escena {i} (ranking): la cifra {n:g} no aparece en el post ni en sus datos")
        if e["tipo"] == "versus":                        # las etiquetas del versus (p. ej. «4 horas») también son datos: tienen que venir del post
            for lado in ("novato", "pro"):
                for n in sorted(numeros_de((e.get(lado) or {}).get("etiqueta"))):
                    if not _cerca(n, permitidos):
                        problemas.append(f"escena {i} (versus): la cifra {n:g} de la etiqueta de «{lado}» no aparece en el post ni en sus datos")
        if e["tipo"] == "terminal":                      # un comando de terminal se copia tal cual del post; las respuestas son solo texto de apoyo breve
            fuente = _sin_espacios(texto_fuente) + _sin_espacios(json.dumps(datos or {}, ensure_ascii=False))
            for x in e.get("lineas", []):
                x = {"t": x, "tipo": "cmd"} if isinstance(x, str) else x
                if x.get("tipo", "cmd") == "cmd" and _sin_espacios(x.get("t", "")) not in fuente:
                    problemas.append(f"escena {i} (terminal): el comando «{x.get('t')}» no aparece literalmente en el post (los comandos no se inventan)")
        for n in sorted(numeros_de(_visibles(e))):
            if n > SIEMPRE_OK and not _cerca(n, permitidos):
                problemas.append(f"escena {i} ({e['tipo']}): la cifra {n:g} no aparece en el post ni en sus datos (si es un ejemplo, marca la escena «ilustrativo»: true)")
    return problemas
