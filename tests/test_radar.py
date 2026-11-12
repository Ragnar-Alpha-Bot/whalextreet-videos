"""Radar de formatos: fichas válidas, salvaguardas (cita corta, sin cifras del original, sin copiar frases), encargo con datos reales y adaptaciones que pasan todas las comprobaciones."""
import copy
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import fidelidad  # noqa: E402
import radar  # noqa: E402
import storyboard_ia  # noqa: E402
from guion import validar  # noqa: E402

# --- las fichas reales son válidas --------------------------------------------------------------------------------------------------------
fichas = radar.fichas()
assert len(fichas) >= 6, "deben estar las 6 primeras fichas"
for f in fichas:
    assert not radar.validar(f), (f["id"], radar.validar(f))
assert len({f["id"] for f in fichas}) == len(fichas), "ids únicos"
assert radar.main(["validar"]) == 0

# --- salvaguardas -----------------------------------------------------------------------------------------------------------------------------
base = copy.deepcopy(next(f for f in fichas if f["id"] == "yt-64KJuekj5NM"))
assert radar.validar(dict(base, plataforma="myspace")), "plataforma desconocida"
assert radar.validar(dict(base, evidencia="me lo contaron")), "evidencia desconocida"
largo = dict(base, gancho_original="uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis diecisiete dieciocho diecinueve veinte veintiuno veintidos veintitres veinticuatro veinticinco veintiseis")
assert any("máximo" in p for p in radar.validar(largo)), "no se guarda el guion entero: solo una cita"
con_cifras = copy.deepcopy(base)
con_cifras["formula"]["estructura"][0]["beat"] = "gancho: cien dólares en Google dan 148 dólares en un año"
assert any("cifras" in p for p in radar.validar(con_cifras)), "las cifras del vídeo original no pasan al encargo"
sin_estructura = copy.deepcopy(base)
sin_estructura["formula"]["estructura"] = [{"beat": "uno"}]
assert radar.validar(sin_estructura), "la estructura necesita al menos 3 pasos"
assert radar.validar(dict(base, metricas={"vistas": "muchas"})), "las visualizaciones son un número real"

# --- parecido literal (fuente en el mismo idioma) -------------------------------------------------------------------------------------------------
a = "Tu fondo puede costarte más de lo que crees y no lo ves"
assert radar.parecido(a, a) == 1.0
assert radar.parecido(a, "Cuánto te cobra de verdad tu ETF cada año sin que lo notes") == 0.0
es = dict(base, idioma="es", gancho_original=a)
sb_copia = {"escenas": [{"tipo": "gancho", "voz": a}]}
assert radar.revisar_adaptacion(es, sb_copia), "copiar la frase de una fuente en español se rechaza"
assert not radar.revisar_adaptacion(base, sb_copia), "con fuente en inglés no hay frase que copiar"

# --- encargo: la fórmula y los datos reales, sin cifras del original -------------------------------------------------------------------------------
datos = json.loads((RAIZ / "radar" / "datos" / "yt-64KJuekj5NM.json").read_text(encoding="utf-8"))
post = radar.encargo(base, datos, oferta={"keyword": "FICHA", "name": "la guía de 5 cosas que mirar en la ficha de un ETF", "short": "la guía en PDF"})
assert post["format"] == "radar" and post["radar"]["tipo_gancho"] == "contraste_cifras" and post["oferta"]["keyword"] == "FICHA"
texto = " ".join(post["parts"])
assert "146,4" in texto and "148" not in texto and "$" not in texto, "solo los datos reales propios, nada del original"
for roto in ({}, {"texto": []}):
    try:
        radar.encargo(base, roto)
        raise AssertionError("sin datos reales no hay encargo")
    except ValueError:
        pass
p = storyboard_ia._prompt(post)
assert "tipo_gancho" in p and "contraste_cifras" in p and "radar" in p.lower()
assert "148" not in p and "Google" not in p, "el prompt no lleva nada del original"
assert "RADAR" in storyboard_ia.SISTEMA and "NO traduzcas frases" in storyboard_ia.SISTEMA

# --- las adaptaciones ya hechas cumplen TODAS las pautas ---------------------------------------------------------------------------------------------
PARES = {"radar-100-euros": ("yt-64KJuekj5NM", "FICHA"), "radar-comisiones": ("tt-7697033270348827917", "INTERES")}
for proyecto, (fid, palabra) in PARES.items():
    f = radar.cargar(radar.CARPETA / f"{fid}.json")
    d = radar.cargar(radar.DATOS / f"{fid}.json")
    post = radar.encargo(f, d, oferta={"keyword": palabra, "name": "x"})
    sb = validar(json.loads((RAIZ / "proyectos" / proyecto / "storyboard.json").read_text(encoding="utf-8")))
    fuente = "\n".join(post["parts"])
    assert not fidelidad.comprobar(sb, fuente), (proyecto, fidelidad.comprobar(sb, fuente))
    assert not storyboard_ia.problemas_oferta(sb, post), (proyecto, storyboard_ia.problemas_oferta(sb, post))
    assert not storyboard_ia.problemas_retencion(sb), proyecto
    assert not radar.revisar_adaptacion(f, sb), proyecto
    assert sb["escenas"][-1]["oferta"]["palabra"] == palabra

print("OK: radar de formatos")
