"""Volumen final estándar para redes: todos los vídeos salen al mismo nivel (≈ -14 LUFS, pico ≤ -1,5 dB) sin tocar la imagen.

Normalización en dos pasadas con el filtro loudnorm de FFmpeg (estándar EBU R128): primero mide, luego aplica la ganancia exacta.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

OBJETIVO_LUFS = -14.0
PICO_MAX_DB = -1.5


def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("no encuentro ffmpeg")
    return exe


def medir(mp4):
    """Devuelve el volumen integrado (LUFS) y el pico real (dBTP) del audio de un archivo."""
    r = subprocess.run([_ffmpeg(), "-hide_banner", "-nostats", "-i", str(mp4), "-vn", "-af", f"loudnorm=I={OBJETIVO_LUFS}:TP={PICO_MAX_DB}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        raise RuntimeError("no pude medir el volumen")
    d = json.loads(m.group(0))
    return {"lufs": float(d["input_i"]), "pico_db": float(d["input_tp"]), "lra": float(d["input_lra"]), "umbral": float(d["input_thresh"]), "offset": float(d["target_offset"])}


def normalizar(mp4, objetivo=OBJETIVO_LUFS, pico=PICO_MAX_DB):
    """Sustituye el archivo por una copia con el audio normalizado (el vídeo se copia sin recodificar). Devuelve (antes, después) en LUFS."""
    mp4 = Path(mp4)
    m = medir(mp4)
    if abs(m["lufs"] - objetivo) < 0.5 and m["pico_db"] <= pico + 0.2:
        return m["lufs"], m["lufs"]
    filtro = (f"loudnorm=I={objetivo}:TP={pico}:LRA=11:measured_I={m['lufs']}:measured_TP={m['pico_db']}:measured_LRA={m['lra']}"
              f":measured_thresh={m['umbral']}:offset={m['offset']}:linear=true")
    tmp = mp4.with_suffix(".norm.mp4")
    subprocess.run([_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(mp4), "-c:v", "copy", "-af", filtro, "-ar", "44100", "-c:a", "aac", "-b:a", "192k", str(tmp)], check=True)
    tmp.replace(mp4)
    return m["lufs"], medir(mp4)["lufs"]
