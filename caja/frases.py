"""Locución natural: cada frase de un guion se parte en trozos cortos (una idea cada uno) con pausas de duración distinta según la puntuación.

Una voz sintética leyendo 25 palabras de un tirón suena plana y apresurada; en trozos de 4-12 palabras, con una pausa breve entre ellos,
el ritmo se parece al de una persona (≈148 palabras/min en la referencia del usuario; ≈186 con la frase entera).
"""
import json
import re
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "marca" / "audio.json"
DEFECTO = {"velocidad": 1.06, "pausas_s": {"coma": 0.14, "medio": 0.22, "fin": 0.30}, "min_palabras_trozo": 4, "volumen_objetivo_rms": 0.07,
           "gap_escenas_s": 0.2, "zoom_escena": 0.035, "pulso_avatar": 0.035, "musica": {"activa": True, "nivel_db": -24}}


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


# ---- Control de calidad: una voz sintética a veces se «come» media frase o devuelve casi silencio ----
SEG_MIN_POR_PALABRA = 0.2   # nadie dice más de 5 palabras por segundo
ACTIVO_MIN = 0.12           # al menos el 12 % de las muestras debe tener voz


def duracion_minima(frase):
    return max(0.5, SEG_MIN_POR_PALABRA * len(frase.split()))


def plausible(audio, sr, frase):
    """False si el audio es más corto de lo que da la frase, está vacío o casi mudo (señal de que el modelo se saltó palabras)."""
    import numpy as np
    a = np.asarray(audio, dtype="float32")
    if len(a) == 0 or len(a) / sr < duracion_minima(frase):
        return False
    return float(np.mean(np.abs(a) > 0.01)) >= ACTIVO_MIN


def con_reintentos(generar, frase, intentos=30):
    """Llama a generar() -> (audio, sr) hasta obtener un audio plausible. El fallo es aleatorio y depende de la frase (medido: con la voz C, «Donde tu idea deje de tener sentido,» solo sale bien 1 de cada 4 veces)
    y los intentos fallidos cuestan ~8 s, así que 30 reintentos dejan la probabilidad de fallar todos por debajo del 0,1 % incluso en ese caso. Si aun así no sale, error claro (mejor parar que publicar una frase a medias)."""
    for n in range(1, intentos + 1):
        audio, sr = generar()
        if plausible(audio, sr, frase):
            return audio, sr
        print(f"  Aviso: «{frase[:40]}» salió truncada ({len(audio) / sr:.1f} s para {len(frase.split())} palabras); intento {n} de {intentos}", flush=True)
    raise RuntimeError(f"La voz no logra decir «{frase[:50]}» tras {intentos} intentos")


def huella_audio(cfg=None):
    """Resumen de los ajustes que cambian el audio de una frase (velocidad, pausas, trozos). Si cambian, la voz ya generada deja de valer."""
    cfg = cfg or config_audio()
    return json.dumps([cfg["velocidad"], cfg["pausas_s"], cfg["min_palabras_trozo"]], sort_keys=True)


def acelerar(audio, sr, velocidad):
    """Acelera la voz sin cambiar el tono (filtro atempo de FFmpeg). velocidad 1.0 = sin cambios."""
    import shutil
    import subprocess
    import tempfile

    import numpy as np
    import soundfile as sf
    if abs(velocidad - 1.0) < 1e-3:
        return np.asarray(audio, dtype="float32")
    ff = shutil.which("ffmpeg")
    if not ff:
        raise RuntimeError("no encuentro ffmpeg para acelerar la voz")
    with tempfile.TemporaryDirectory() as tmp:
        a, b = f"{tmp}/in.wav", f"{tmp}/out.wav"
        sf.write(a, np.asarray(audio, dtype="float32"), sr)
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", a, "-filter:a", f"atempo={velocidad}", b], check=True)
        y, sr2 = sf.read(b, dtype="float32")
    assert sr2 == sr
    return y
