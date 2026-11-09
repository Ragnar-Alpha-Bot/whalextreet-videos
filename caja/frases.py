"""Locución natural: cada frase de un guion se parte en trozos cortos (una idea cada uno) con pausas de duración distinta según la puntuación.

Una voz sintética leyendo 25 palabras de un tirón suena plana y apresurada; en trozos de 4-12 palabras, con una pausa breve entre ellos,
el ritmo se parece al de una persona (≈148 palabras/min en la referencia del usuario; ≈186 con la frase entera).
"""
import json
import re
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "marca" / "audio.json"
DEFECTO = {"pausas_s": {"coma": 0.2, "medio": 0.3, "fin": 0.42}, "min_palabras_trozo": 4, "volumen_objetivo_rms": 0.07, "musica": {"activa": True, "nivel_db": -24}}


def config_audio():
    cfg = json.loads(json.dumps(DEFECTO))
    if CONFIG.exists():
        usuario = json.loads(CONFIG.read_text(encoding="utf-8"))
        for k, v in usuario.items():
            if k.startswith("_"):
                continue
            if isinstance(v, dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg


def _pausa(trozo, pausas):
    ultimo = trozo.rstrip()[-1:]
    if ultimo in ".!?…":
        return pausas["fin"]
    if ultimo in ";:":
        return pausas["medio"]
    return pausas["coma"]


def trocear(texto, cfg=None):
    """Devuelve [(trozo, pausa_en_segundos_despues)]; la última pausa es 0. Los trozos de menos de N palabras se unen al vecino."""
    cfg = cfg or config_audio()
    minimo = cfg["min_palabras_trozo"]
    t = " ".join(texto.split())
    trozos = [x.strip() for x in re.findall(r"[^,;:.!?…]+[,;:.!?…]*", t) if x.strip()]
    if not trozos:
        return [(t, 0.0)]
    out = []
    for x in trozos:
        if out and len(out[-1].split()) < minimo:
            out[-1] = out[-1] + " " + x
        else:
            out.append(x)
    if len(out) > 1 and len(out[-1].split()) < minimo:
        ultimo = out.pop()            # (no usar «out[-2] += out.pop()»: el índice se resuelve después del pop y pisa otro trozo)
        out[-1] += " " + ultimo
    res = [(x, _pausa(x, cfg["pausas_s"])) for x in out]
    res[-1] = (res[-1][0], 0.0)
    return res
