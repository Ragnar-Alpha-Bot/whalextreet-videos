"""Serie «8 acciones de la cadena de la IA» (3 partes): guiones válidos, cifras trazables a los datos reales, retención y cierre «comenta y sígueme» sin recurso."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import fidelidad  # noqa: E402
import storyboard_ia  # noqa: E402
from guion import lineas, validar  # noqa: E402

DATOS = json.loads((RAIZ / "tests" / "datos" / "ia_ocho_acciones.json").read_text(encoding="utf-8"))
assert len(DATOS["acciones"]) == 8
fuente = json.dumps(DATOS, ensure_ascii=False)

vistas = []
for n in (1, 2, 3):
    sb = validar(json.loads((RAIZ / "proyectos" / f"ia-8-acciones-{n}" / "storyboard.json").read_text(encoding="utf-8")))
    esc = sb["escenas"]
    assert not fidelidad.comprobar(sb, fuente), (n, fidelidad.comprobar(sb, fuente))
    assert not storyboard_ia.problemas_retencion(sb), n
    assert sum(1 for e in esc if e["tipo"] in ("barras3d", "esfera3d", "animal3d", "ciudad3d", "linea3d")) <= 1, "como mucho una escena 3D por vídeo"
    assert all(a["tipo"] != e["tipo"] or e["tipo"] in ("tarjetas", "metafora") for a, e in zip(esc, esc[1:])), "no repetir el mismo tipo de escena seguido (salvo tarjetas y metáforas, que cambian de contenido)"
    cierre = esc[-1]
    assert cierre["tipo"] == "cta" and cierre["comenta"] and not cierre.get("oferta"), "cierre sin PDF ni recurso: solo comenta y sígueme"
    voz = lineas(sb)[f"l{len(esc)}"]
    assert voz.startswith("Comenta ") and "sígueme en WhaleXtreet" in voz and ("parte" in voz or "análisis" in voz), voz
    palabras = sum(len(e.get("voz", "").split()) for e in esc[:-1])
    assert 100 <= palabras <= 205, (n, palabras)
    vistas.append(" ".join(e.get("voz", "") for e in esc).lower())

# las ocho acciones salen explicadas, una vez cada una, repartidas en las tres partes
todo = " ".join(vistas)
for nombre in ("nvidia", "broadcom", "marvell", "tsmc", "micron", "vertiv", "palantir", "alphabet"):
    assert nombre in todo, nombre
# el «por quince» del hilo se usa como ESCENARIO (la cuenta de lo que tendría que valer cada empresa), nunca como promesa
assert "multiplicarse por quince" in vistas[0], "el gancho de la parte 1 plantea el x15"
for n, v in enumerate(vistas, 1):
    assert "por quince" in v, f"parte {n}: hace la cuenta del por quince"
    assert any(f in v for f in ("escenario optimista", "no es una recomendación", "nadie lo puede garantizar")), f"parte {n}: lo presenta como escenario, no como promesa"
for t in ("hazte rico", "millonario", "seguro que", "garantizado", "sin riesgo", "te hará rico", "irán a por"):
    assert t not in todo, t
# la cuenta es aritmética sobre datos reales: valor en bolsa × 15
for k, v in DATOS["acciones"].items():
    base = v.get("valor_bolsa_billones") or v["valor_bolsa_mil_millones"] / 1000
    assert abs(v["valor_si_por_15_billones"] - base * 15) < 0.01, k
print("OK: serie de las 8 acciones de la cadena de la IA")
# --- cada vídeo deja constancia de que es una parte de una serie: etiqueta fija arriba y cierre que apunta a la siguiente ---------------------------------------
for n in (1, 2, 3):
    sbn = json.loads((RAIZ / "proyectos" / f"ia-8-acciones-{n}" / "storyboard.json").read_text(encoding="utf-8"))
    assert sbn["etiqueta"] == f"IA · PARTE {n} DE 3", sbn["etiqueta"]
    assert f"parte {n} de 3" in sbn["escenas"][0]["kicker"].lower()
    if n < 3:
        assert ("parte dos", "parte tres")[n - 1] in sbn["escenas"][-1]["comenta"]["sigue"], n
print("OK: la serie deja constancia de las partes")

# --- las partes 2 y 3 abren con un gancho propio que dice qué serie es y qué parte (para quien no vio la parte 1) ---------------------------------------
for n, txt in ((2, "parte dos"), (3, "parte tres")):
    sbn = json.loads((RAIZ / "proyectos" / f"ia-8-acciones-{n}" / "storyboard.json").read_text(encoding="utf-8"))
    g0 = sbn["escenas"][0]
    assert g0["tipo"] == "gancho" and "quince" in g0["voz"] and txt in g0["voz"].lower(), g0["voz"]
    assert "X15" in g0["texto"] and f"PARTE {n} DE 3" in g0["kicker"] and "serie" in g0["subtexto"].lower()
print("OK: partes 2 y 3 con gancho propio")
