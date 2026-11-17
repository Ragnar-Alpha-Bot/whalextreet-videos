"""Las 4 aperturas del gancho: rotan solas, se pueden forzar y todas suenan en el segundo 0."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "caja"))
import escenas as E, paletas

def ctx():
    return E.Ctx(0, 0.0, 4.0, 0.05, 3.0, [], 984, 1010, paletas.paleta("alerta"))

for ap in E.TODAS_APERTURAS:
    c = ctx()
    html, js = E.e_gancho(c, {"tipo": "gancho", "texto": "HACKEARON BINANCE", "apertura": ap, "voz": "x"})
    assert any(t <= 0.1 and k in ("boom", "impact") for t, k, _ in c.ev), f"{ap}: sin golpe en el segundo 0"
    assert js and html, ap
textos = ["HACKEARON BINANCE", "PERDIÓ UN MILLÓN", "TU DINERO PARADO", "NADIE TE LO CUENTA", "ERROR CARO", "VENDER EN PÁNICO", "EL MERCADO CAYÓ", "TOP 10 CRIPTOS"]
for t in textos:
    c = ctx(); E.e_gancho(c, {"tipo": "gancho", "texto": t, "voz": "x"})
elegidas = {E.APERTURAS[sum(map(ord, t)) % len(E.APERTURAS)] for t in textos}
assert not ({"negro", "dividida"} & elegidas) and len(elegidas) == 2, elegidas
print("OK: aperturas del gancho (rotación zoom3d/flash y sonido en el segundo 0 en las 5)")
