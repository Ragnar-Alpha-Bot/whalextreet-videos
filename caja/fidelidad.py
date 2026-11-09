"""Fidelidad de las cifras: un vídeo hecho a partir de un post aprobado no puede inventar datos.

Toda cifra que se muestre (valor, puntos de un gráfico, barras, porcentajes, tarjetas, textos) debe aparecer en el post o en sus datos,
salvo en escenas marcadas «ilustrativo»: true (solo gráfico, barras, donut y número), cuyo título debe decir «ilustrativo».
Los números pequeños (≤ 10, como «3 señales») se permiten siempre.
"""
import re

_NUM = re.compile(r"\d[\d.,]*")
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
        return [e.get("texto")]
    if t == "titulo":
        return [e.get("titulo"), e.get("subtitulo"), e.get("etiqueta")]
    if t == "numero":
        return [e.get("valor"), e.get("delta"), e.get("etiqueta"), e.get("detalle"), e.get("prefijo"), e.get("sufijo")]
    if t == "grafico":
        return [e.get("titulo"), e.get("puntos"), e.get("etiquetas"), [a.get("texto") for a in e.get("anotaciones", [])]]
    if t == "barras":
        return [e.get("titulo"), [(x.get("n"), x.get("v")) for x in e.get("items", [])]]
    if t == "donut":
        return [e.get("titulo"), [(x.get("n"), x.get("v")) for x in e.get("segmentos", [])]]
    if t == "lista":
        return [e.get("titulo"), [x if isinstance(x, str) else x.get("t") for x in e.get("items", [])]]
    if t == "tarjetas":
        return [e.get("titulo"), [(x.get("etiqueta"), x.get("valor"), x.get("nota")) for x in e.get("items", [])]]
    if t == "pregunta":
        return [e.get("pregunta"), [x if isinstance(x, str) else x.get("t") for x in e.get("opciones", [])]]
    return []


def comprobar(sb, texto_fuente, datos=None):
    """Devuelve la lista de problemas (vacía = todo trazable). texto_fuente: texto del post; datos: datos reales del post (opcional)."""
    permitidos = numeros(texto_fuente) | numeros_de(datos or {})
    problemas = []
    for i, e in enumerate(sb["escenas"], 1):
        if e.get("ilustrativo"):
            if e["tipo"] not in ("grafico", "barras", "donut", "numero"):
                problemas.append(f"escena {i} ({e['tipo']}): solo grafico, barras, donut y numero pueden ser ilustrativos")
            elif "ilustrativo" not in str(e.get("titulo") or e.get("etiqueta") or "").lower():
                problemas.append(f"escena {i} ({e['tipo']}): una escena ilustrativa debe decir «(ilustrativo)» en su título o etiqueta")
            continue
        for n in sorted(numeros_de(_visibles(e))):
            if n > SIEMPRE_OK and not _cerca(n, permitidos):
                problemas.append(f"escena {i} ({e['tipo']}): la cifra {n:g} no aparece en el post ni en sus datos (si es un ejemplo, marca la escena «ilustrativo»: true)")
    return problemas
