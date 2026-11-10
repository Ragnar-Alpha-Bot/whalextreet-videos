"""La portada: el primer fotograma del vídeo es el del gancho completo (no gris ni vacío) y el resto del vídeo no cambia."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
    print("AVISO: no hay ffmpeg/ffprobe; se omite test_portada")
    raise SystemExit(0)
import portada  # noqa: E402

d = Path(tempfile.mkdtemp())
mp4 = d / "v.mp4"
# vídeo sintético de 2 s: gris claro los primeros 0,5 s (como un primer fotograma vacío) y rojo después, con audio
subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=0xAAAAAA:s=270x480:r=30:d=0.5", "-f", "lavfi", "-i", "color=c=0xCC2222:s=270x480:r=30:d=1.5",
                "-f", "lavfi", "-i", "sine=frequency=440:d=2", "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]", "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(mp4)], check=True)


def color_en(archivo, t):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(t), "-i", str(archivo), "-frames:v", "1", "-vf", "scale=1:1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    return tuple(r.stdout[:3])


def duracion(archivo):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(archivo)], capture_output=True, text=True).stdout)


antes = color_en(mp4, 0)
assert antes[0] < 200 and abs(antes[0] - antes[2]) < 12, antes           # empieza gris
d0 = duracion(mp4)
png = portada.poner_portada(mp4, segundo=1.0)
assert png.exists() and png.stat().st_size > 0
primero = color_en(mp4, 0)
assert primero[0] > 150 and primero[1] < 80, primero                     # ahora el primer fotograma es el del gancho (rojo)
medio = color_en(mp4, 0.3)
assert abs(medio[0] - antes[0]) < 15, medio                              # el resto no cambia (a los 0,3 s sigue gris)
assert abs(duracion(mp4) - d0) < 0.1, (duracion(mp4), d0)
print("OK: test_portada")
