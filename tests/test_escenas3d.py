"""Las escenas 3D están registradas, validan sus datos y apuntan a archivos que existen (el fallo de la primera prueba: ruta mal puesta, escena vacía)."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import escenas3d  # noqa: E402
from escenas import ESCENAS  # noqa: E402
from guion import validar  # noqa: E402

assert "barras3d" in ESCENAS and "moneda3d" in ESCENAS
for ruta in ("three.module.js", "three.core.js"):
    assert (RAIZ / "marca" / ruta).exists(), ruta
assert '"./assets/three.module.js"' in escenas3d.BASE        # el motor copia marca/ a assets/
validar(json.loads((RAIZ / "proyectos" / "prueba-3d" / "storyboard.json").read_text(encoding="utf-8")))
errores = []
ESCENAS["moneda3d"][1]({"titulo": "x" * 60}, errores.append)
assert errores, "debe rechazar un título largo y la falta de símbolo"
import fidelidad  # noqa: E402
import storyboard_ia  # noqa: E402
assert "barras3d" in storyboard_ia.SISTEMA and "moneda3d" in storyboard_ia.SISTEMA
base = {"tema": "bolsa", "escenas": [
    {"tipo": "moneda3d", "voz": "x", "titulo": "AHORRO", "simbolo": "€", "subtitulo": "Ganó 87 %"},
    {"tipo": "barras3d", "voz": "x", "titulo": "A", "items": [{"n": "a", "v": 44}, {"n": "b", "v": 61}]}]}
probs = fidelidad.comprobar(base, "Un post sin esas cifras")
assert any("87" in x for x in probs) and any("44" in x or "61" in x for x in probs), probs      # las cifras de las escenas 3D también se vigilan
base["escenas"][1].update(ilustrativo=True, titulo="A (ilustrativo)")
assert not any("barras3d" in x for x in fidelidad.comprobar(base, "Un post sin esas cifras")), "barras3d puede ser ilustrativa"
print("OK: test_escenas3d")
