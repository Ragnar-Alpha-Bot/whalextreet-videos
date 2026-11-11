"""Escenas 3D del nicho: animal3d (toro y oso), lingotes3d, linea3d, escudo3d y ciudad3d. Validación, HTML, sintaxis del código de Three.js y fidelidad de datos."""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import escenas3d  # noqa: E402,F401
import fidelidad  # noqa: E402
import storyboard_ia  # noqa: E402
from escenas import ESCENAS, Ctx  # noqa: E402
from guion import validar  # noqa: E402
from paletas import paleta  # noqa: E402

NUEVAS = ("animal3d", "lingotes3d", "linea3d", "escudo3d", "ciudad3d")
for t in NUEVAS:
    assert t in ESCENAS, t
    assert t in storyboard_ia.FIGURAS_3D and f"- {t}" in storyboard_ia.SISTEMA, t


def val(tipo, d):
    e = []
    ESCENAS[tipo][1](d, e.append)
    return e


def ctx(i=2):
    return Ctx(i, 4.0, 14.0, 4.1, 13.5, [{"t": "x", "ini": 0.3, "fin": 0.5}], 984, 1010, paleta("bolsa"))


CASOS = {
    "animal3d": {"animal": "toro", "titulo": "MERCADO ALCISTA", "subtitulo": "Embiste"},
    "lingotes3d": {"titulo": "AHORRO", "subtitulo": "Lingote a lingote"},
    "linea3d": {"titulo": "EVOLUCIÓN", "puntos": [10, 12, 11, 15, 14, 19, 23, 21, 28, 35], "unidad": " %", "etiquetas": ["Inicio", "Hoy"]},
    "escudo3d": {"titulo": "PROTEGE TU CAPITAL"},
    "ciudad3d": {"titulo": "ECONOMÍA", "subtitulo": "Crece la ciudad"},
}
for t, d in CASOS.items():
    assert not val(t, d), (t, val(t, d))
    assert val(t, dict(d, titulo="x" * 60)), f"{t}: título demasiado largo"
    h, js = ESCENAS[t][0](ctx(), d)
    assert "<canvas" in h and 'type="module"' in h and "./assets/three.module.js" in h, t
    assert "undefined" not in h and "%(" not in h, f"{t}: marcador sin sustituir"

assert val("animal3d", {"titulo": "x", "animal": "dragón"}), "solo toro u oso"
assert val("animal3d", {"titulo": "x"}), "falta el animal"
assert "oso" in ESCENAS["animal3d"][0](ctx(), dict(CASOS["animal3d"], animal="oso"))[0]
assert val("linea3d", dict(CASOS["linea3d"], puntos=[1])), "mínimo 2 puntos"
assert val("linea3d", dict(CASOS["linea3d"], anotaciones=[{"i": 1, "texto": "x"}])), "sin anotaciones"
h, _ = ESCENAS["linea3d"][0](ctx(), CASOS["linea3d"])
assert "35 %" in h, "la cifra final se ve en pantalla"

# --- el código de Three.js de cada escena es JavaScript válido (si hay Node) -----------------------------------------------------------
node = shutil.which("node")
if node:
    with tempfile.TemporaryDirectory() as tmp:
        for t, d in CASOS.items():
            for animal in (("toro", "oso") if t == "animal3d" else (None,)):
                dd = dict(d, animal=animal) if animal else d
                h, _ = ESCENAS[t][0](ctx(), dd)
                codigo = re.search(r'<script type="module">(.*)</script>', h, re.S).group(1)
                f = Path(tmp) / f"{t}_{animal}.mjs"
                f.write_text(codigo, encoding="utf-8")
                r = subprocess.run([node, "--check", str(f)], capture_output=True, text=True)
                assert r.returncode == 0, f"{t}: {r.stderr[:300]}"

# --- fidelidad ----------------------------------------------------------------------------------------------------------------------
sb = {"tema": "bolsa", "escenas": [{"tipo": "linea3d", "voz": "x", "titulo": "Evolución", "puntos": [100, 250, 480]}]}
p = fidelidad.comprobar(sb, "texto sin cifras")
assert p and "linea3d" in p[0], p
assert not fidelidad.comprobar(sb, "100, 250 y 480")
sb["escenas"][0].update(ilustrativo=True, titulo="Evolución (ilustrativo)")
assert not fidelidad.comprobar(sb, "texto sin cifras"), "linea3d puede ser ilustrativa"
sb = {"tema": "bolsa", "escenas": [{"tipo": "escudo3d", "voz": "x", "titulo": "Pierde 87 %"}]}
assert fidelidad.comprobar(sb, "sin cifras"), "una cifra en el título de una escena 3D decorativa también se comprueba"

# --- un guion completo con las figuras valida --------------------------------------------------------------------------------------
validar({"tema": "bolsa", "escenas": [{"tipo": "gancho", "voz": "Toro u oso, tú eliges cómo protegerte.", "texto": "TORO U OSO"}, dict(CASOS["animal3d"], tipo="animal3d", voz="x"),
         dict(CASOS["escudo3d"], tipo="escudo3d", voz="x"), {"tipo": "cta"}]})
print("OK: escenas 3D del nicho (toro, oso, lingotes, línea, escudo, ciudad)")
