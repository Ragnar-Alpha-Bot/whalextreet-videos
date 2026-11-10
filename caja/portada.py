"""Portada automática: el primer fotograma del vídeo pasa a ser el del gancho ya completo.

Redes como Threads o Instagram usan el primer fotograma como portada si no eliges una, y ahí el gancho aún no ha aparecido (sale gris o vacío).
Se coge el fotograma de los 0,8 s (texto del gancho, etiqueta, animación y primer subtítulo ya en pantalla), se guarda como PNG junto al vídeo
(<nombre>_portada.png) y se pone SOLO en el primer fotograma (1/30 s): el resto del vídeo y el audio quedan exactamente igual.
"""
import shutil
import subprocess
from pathlib import Path

SEGUNDO_PORTADA = 0.8


def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("no encuentro ffmpeg")
    return exe


def poner_portada(mp4, segundo=SEGUNDO_PORTADA):
    """Devuelve la ruta del PNG de portada. Sustituye el MP4 por una copia con la portada como primer fotograma."""
    mp4 = Path(mp4)
    png = mp4.with_name(mp4.stem + "_portada.png")
    ff = _ffmpeg()
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-ss", str(segundo), "-i", str(mp4), "-frames:v", "1", str(png)], check=True)
    if not png.exists() or png.stat().st_size == 0:
        raise RuntimeError("no pude sacar el fotograma de portada")
    tmp = mp4.with_suffix(".portada.mp4")
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", str(mp4), "-i", str(png),
                    "-filter_complex", "[0:v][1:v]overlay=0:0:enable='lt(t,0.02)'[v]", "-map", "[v]", "-map", "0:a?",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(tmp)], check=True)
    tmp.replace(mp4)
    return png
