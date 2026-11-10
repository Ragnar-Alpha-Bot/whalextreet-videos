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
print("OK: test_escenas3d")
