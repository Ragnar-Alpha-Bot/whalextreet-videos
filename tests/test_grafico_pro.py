"""«grafico_pro»: gráfico de línea, área o velas con datos reales (TradingView Lightweight Charts). Validación, HTML, sintaxis del JavaScript y fidelidad de datos."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import fidelidad  # noqa: E402
from escenas import ESCENAS, Ctx  # noqa: E402
from guion import validar  # noqa: E402
from paletas import paleta  # noqa: E402

assert "grafico_pro" in ESCENAS
assert (RAIZ / "marca" / "lightweight-charts.standalone.production.js").exists(), "falta la librería en marca/"
assert (RAIZ / "marca" / "lightweight-charts.LICENSE.txt").exists(), "falta su licencia (Apache 2.0)"
assert "v4.2.0" in (RAIZ / "marca" / "lightweight-charts.standalone.production.js").read_text(encoding="utf-8")[:200], "versión fijada: 4.2.0"

DATOS = json.loads((RAIZ / "tests" / "datos" / "smh_semanal.json").read_text(encoding="utf-8"))   # SMH semanal real (stockanalysis.com, 12-nov-2026)
CIERRES = DATOS["cierres"]
VELAS = [{"o": a, "h": b, "l": c, "c": d} for a, b, c, d in DATOS["velas_ultimas_12"]]
assert len(CIERRES) == 52 and len(VELAS) == 12


def val(d):
    e = []
    ESCENAS["grafico_pro"][1](d, e.append)
    return e


def ctx(i=2):
    return Ctx(i, 4.0, 14.0, 4.1, 13.5, [{"t": "máximo", "ini": 0.3, "fin": 0.5}], 984, 1010, paleta("bolsa"))


AREA = {"titulo": "SMH · 1 AÑO", "modo": "area", "puntos": CIERRES, "etiquetas": ["nov 2025", "nov 2026"], "zoom": True,
        "anotaciones": [{"i": 30, "texto": "máximo: 659,88", "cuando": "máximo"}]}
LINEA = {"titulo": "SMH · 1 AÑO", "modo": "linea", "puntos": CIERRES}
CANDLES = {"titulo": "SMH · 12 SEMANAS", "modo": "velas", "velas": VELAS}
for nombre, d in (("area", AREA), ("linea", LINEA), ("velas", CANDLES)):
    assert not val(d), (nombre, val(d))

# --- validación ---------------------------------------------------------------------------------------------------------------------------
assert val(dict(AREA, titulo="x" * 60)), "título demasiado largo"
assert val(dict(AREA, modo="barras")), "modo desconocido"
assert val(dict(AREA, puntos=[1])), "mínimo 2 puntos"
assert val(dict(AREA, puntos=list(range(300)))), "máximo 260 puntos"
assert val(dict(AREA, puntos=[1, "x"])), "solo números"
assert val(dict(CANDLES, velas=[{"o": 1, "h": 2, "l": 0.5, "c": 1.5}])), "mínimo 2 velas"
assert val(dict(CANDLES, velas=[{"o": 10, "h": 9, "l": 8, "c": 9.5}, {"o": 1, "h": 2, "l": 0.5, "c": 1.5}])), "el máximo de la vela no puede ser menor que la apertura"
assert val(dict(AREA, anotaciones=[{"i": 99, "texto": "x"}])), "anotación fuera de rango"
assert val(dict(AREA, anotaciones=[{"i": 1, "texto": "x"}] * 4)), "hasta 3 anotaciones"
assert val(dict(AREA, etiquetas=["solo una"])), "dos etiquetas"

# --- HTML ---------------------------------------------------------------------------------------------------------------------------------
for nombre, d in (("area", AREA), ("linea", LINEA), ("velas", CANDLES)):
    h, js = ESCENAS["grafico_pro"][0](ctx(), d)
    assert "./assets/lightweight-charts.standalone.production.js" in h and "<canvas" in h and 'type="module"' in h, nombre
    assert "TradingView Lightweight Charts" in h, f"{nombre}: la atribución exigida por la licencia debe verse"
    assert "undefined" not in h and "__" not in h.replace("__hf", ""), f"{nombre}: marcador sin sustituir"
    assert "data-layout-ignore" in h, "el contenedor oculto no debe ensuciar la revisión de calidad"
h, _ = ESCENAS["grafico_pro"][0](ctx(), AREA)
assert "501,73" in h, "el último valor se ve en pantalla, con coma decimal"

# --- el JavaScript es válido (si hay Node) ------------------------------------------------------------------------------------------------------
node = shutil.which("node")
if node:
    with tempfile.TemporaryDirectory() as tmp:
        for nombre, d in (("area", AREA), ("velas", CANDLES)):
            h, _ = ESCENAS["grafico_pro"][0](ctx(), d)
            codigo = re.search(r'<script type="module">(.*)</script>', h, re.S).group(1)
            f = Path(tmp) / f"{nombre}.mjs"
            f.write_text(codigo, encoding="utf-8")
            r = subprocess.run([node, "--check", str(f)], capture_output=True, text=True)
            assert r.returncode == 0, f"{nombre}: {r.stderr[:300]}"

# --- fidelidad: las cifras salen de los datos reales del post -------------------------------------------------------------------------------------
sb = {"tema": "bolsa", "escenas": [dict(AREA, tipo="grafico_pro", voz="x")]}
assert fidelidad.comprobar(sb, "texto sin cifras"), "sin datos del post, las cifras del gráfico no se aceptan"
assert not fidelidad.comprobar(sb, "máximo 659,88", {"cierres": CIERRES, "primera": DATOS["primera"], "ultima": DATOS["ultima"]}), "con los datos reales como fuente, pasa"
sb["escenas"][0]["puntos"] = CIERRES[:-1] + [999.99]
assert fidelidad.comprobar(sb, "máximo 659,88", {"cierres": CIERRES, "primera": DATOS["primera"], "ultima": DATOS["ultima"]}), "un punto inventado se detecta"
sb2 = {"tema": "bolsa", "escenas": [dict(CANDLES, tipo="grafico_pro", voz="x", ilustrativo=True)]}
assert fidelidad.comprobar(sb2, "x"), "ilustrativo exige decirlo en el título"
sb2["escenas"][0]["titulo"] = "EJEMPLO (ilustrativo)"
assert not fidelidad.comprobar(sb2, "x")

# --- un guion completo valida -------------------------------------------------------------------------------------------------------------------
validar({"tema": "bolsa", "escenas": [{"tipo": "gancho", "voz": "Un ETF de chips subió y cayó con fuerza.", "texto": "SUBE Y CAE"}, dict(AREA, tipo="grafico_pro", voz="x"), {"tipo": "cta"}]})
print("OK: grafico_pro (área, línea y velas con datos reales)")
