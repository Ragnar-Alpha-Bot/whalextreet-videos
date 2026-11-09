"""Regresión: la voz leyó «Kodak» como «CODA» y el vídeo entero fallaba; ahora se repite solo esa línea (hasta 3 rondas)."""
import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import frases  # noqa: E402
import motor  # noqa: E402
import palabras  # noqa: E402
import pipeline  # noqa: E402


def prueba(fallos_whisper):
    with tempfile.TemporaryDirectory() as t:
        proyecto = Path(t) / "p"
        (proyecto / "assets" / "voz").mkdir(parents=True)
        (proyecto / "storyboard.json").write_text((RAIZ / "proyectos" / "dialogo-stop" / "storyboard.json").read_text(encoding="utf-8"), encoding="utf-8")
        n = {"voz": 0, "whisper": 0, "borrado": []}

        def falso_run(cmd, **kw):
            n["voz"] += 1
            lin = json.loads((proyecto / "guion.json").read_text(encoding="utf-8"))
            (proyecto / "assets" / "voz" / "duraciones.json").write_text(json.dumps({k: {"texto": x, "voz": "profesor", "huella": frases.huella_audio()} for k, x in lin.items()}), encoding="utf-8")
            for k in lin:
                (proyecto / "assets" / "voz" / f"{k}.wav").write_bytes(b"x")

        def falso_procesar(p):
            n["whisper"] += 1
            (proyecto / "assets" / "voz" / "palabras.json").write_text("{}", encoding="utf-8")
            if n["whisper"] <= fallos_whisper:
                raise palabras.VozMala("mal", ["l2"])

        orig = (pipeline.subprocess.run, palabras.procesar, pipeline.borrar_cache_de_lineas, motor.construir)
        pipeline.subprocess.run, palabras.procesar = falso_run, falso_procesar
        pipeline.borrar_cache_de_lineas = lambda lin, hab, claves: n["borrado"].append(claves)
        motor.construir = lambda p: {}
        try:
            pipeline.main(proyecto, render=False)
            return n, None
        except palabras.VozMala as e:
            return n, e
        finally:
            pipeline.subprocess.run, palabras.procesar, pipeline.borrar_cache_de_lineas, motor.construir = orig


n, err = prueba(1)
assert err is None and n["voz"] == 2 and n["whisper"] == 2 and n["borrado"] == [["l2"]], n
n, err = prueba(99)                     # si la voz nunca acierta, tras 3 rondas se aborta (no se publica audio malo)
assert isinstance(err, palabras.VozMala) and n["whisper"] == 3, n
print("OK: test_reintento_voz")
