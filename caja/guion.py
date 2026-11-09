"""Validación del guion de escenas (storyboard). Un guion mal formado (por ejemplo, uno generado por una IA) se rechaza con un
mensaje claro en lugar de producir un vídeo roto.

Formato (JSON):
{
  "tema": "bolsa",                      # cripto | bolsa | alerta | macro | educativo  -> color de acento
  "tipo_post": "datos",                 # tipo de post de la agencia -> cuándo sale el profesor (formatos_video.json)
  "etiqueta": "BOLSA · ACCIONES",       # opcional, texto de la píldora de arriba (máx. 24)
  "ilustrativo": true,                  # opcional: añade «Gráficos ilustrativos, sin datos reales» al pie
  "cierre": "El mercado, con contexto.",# opcional
  "escenas": [ {"tipo": "titulo", "voz": "texto que se locuta", ...campos de la escena...}, ... ]   # de 2 a 8
}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from escenas import ESCENAS  # noqa: E402
from paletas import TEMAS  # noqa: E402

MAX_ESCENAS = 8


def validar(sb):
    errores = []
    if not isinstance(sb, dict):
        raise ValueError("el guion debe ser un objeto JSON")
    if sb.get("tema") not in TEMAS:
        errores.append(f"«tema» debe ser uno de {sorted(TEMAS)}")
    if not isinstance(sb.get("tipo_post", "datos"), str):
        errores.append("«tipo_post» debe ser texto")
    for k, mx in (("etiqueta", 24), ("cierre", 48)):
        v = sb.get(k)
        if v is not None and (not isinstance(v, str) or not v or len(v) > mx):
            errores.append(f"«{k}» debe ser un texto de hasta {mx} caracteres")
    esc = sb.get("escenas")
    if not isinstance(esc, list) or not 2 <= len(esc) <= MAX_ESCENAS:
        errores.append(f"«escenas» debe ser una lista de 2 a {MAX_ESCENAS} escenas")
        esc = []
    for i, e in enumerate(esc, 1):
        def err(m, i=i, e=e):
            errores.append(f"escena {i} ({e.get('tipo') if isinstance(e, dict) else '?'}): {m}")
        if not isinstance(e, dict) or e.get("tipo") not in ESCENAS:
            errores.append(f"escena {i}: «tipo» debe ser uno de {sorted(ESCENAS)}")
            continue
        voz = e.get("voz")
        if not isinstance(voz, str) or not voz.strip():
            err("falta «voz» (el texto que se locuta)")
        elif len(voz) > 300:
            err(f"«voz» es demasiado larga ({len(voz)} > 300 caracteres)")
        ESCENAS[e["tipo"]][1](e, err)
    if errores:
        raise ValueError("Guion de escenas no válido:\n - " + "\n - ".join(errores))
    out = dict(sb)
    out.setdefault("tipo_post", "datos")
    out.setdefault("ilustrativo", True)
    out.setdefault("cierre", "El mercado, con contexto.")
    return out


def lineas(sb):
    """Una línea de voz por escena: {"l1": "...", "l2": "..."}."""
    return {f"l{i}": e["voz"].strip() for i, e in enumerate(sb["escenas"], 1)}
