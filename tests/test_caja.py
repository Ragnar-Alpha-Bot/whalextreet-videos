"""Pruebas de la caja de herramientas con datos sintéticos (sin voz real, sin red, sin render).
Ejecutar desde la raíz del repo:  python tests/test_caja.py"""
import copy
import json
import math
import re
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
sys.path.insert(0, str(RAIZ))

import escenas as E  # noqa: E402
import guion  # noqa: E402
import motor  # noqa: E402
import paletas  # noqa: E402
import palabras as pal_mod  # noqa: E402
import sfx  # noqa: E402

fallos = []
SEL = r'tl\.(?:to|fromTo|set)\(\s*"#([A-Za-z0-9_]+)"'   # primer argumento de cada animación: el id de un elemento
_n = [0]


def comprobar(nombre, cond):
    print(("OK   " if cond else "FALLA"), nombre)
    if not cond:
        fallos.append(nombre)


def rechaza(nombre, sb):
    try:
        guion.validar(sb)
        comprobar(nombre, False)
    except ValueError:
        comprobar(nombre, True)


VOZ = "Esta es una frase de prueba para la locución del vídeo."
BUENO = {
    "tema": "bolsa", "tipo_post": "datos",
    "escenas": [
        {"tipo": "titulo", "voz": VOZ, "titulo": "El PER en 20 segundos", "subtitulo": "Un número, una idea", "etiqueta": "BOLSA"},
        {"tipo": "numero", "voz": VOZ, "valor": 15.5, "decimales": 1, "sufijo": "x", "etiqueta": "PER", "detalle": "15 € entre 1 €", "delta": -2.5},
        {"tipo": "grafico", "voz": VOZ, "titulo": "Precio", "puntos": [10, 12, 11, 15, 14, 18], "etiquetas": ["Ene", "Jun"], "unidad": "€",
         "anotaciones": [{"i": 3, "texto": "Máximo", "cuando": "frase"}]},
        {"tipo": "barras", "voz": VOZ, "titulo": "PER por sector", "unidad": "x", "items": [{"n": "A", "v": 8}, {"n": "B", "v": 15, "cuando": "prueba"}, {"n": "C", "v": 30}]},
        {"tipo": "donut", "voz": VOZ, "titulo": "Reparto", "segmentos": [{"n": "Uno", "v": 60}, {"n": "Dos", "v": 25}, {"n": "Tres", "v": 15}]},
        {"tipo": "lista", "voz": VOZ, "titulo": "Revisa", "items": [{"t": "Deuda", "cuando": "frase"}, "Beneficios", "Sector"]},
        {"tipo": "tarjetas", "voz": VOZ, "items": [{"etiqueta": "Margen", "valor": "12,4 %", "tono": "up", "nota": "ilustrativo"}, {"etiqueta": "Deuda", "valor": "3x", "tono": "down"}]},
        {"tipo": "pregunta", "voz": VOZ, "pregunta": "¿Qué miras primero?", "opciones": ["El PER", "La deuda"]},
    ],
}

# --- 1. Validador ---------------------------------------------------------------------------------------------------
comprobar("un guion completo y correcto se acepta", guion.validar(copy.deepcopy(BUENO)) is not None)
comprobar("se rellenan valores por defecto (cierre, ilustrativo)", guion.validar(copy.deepcopy(BUENO))["cierre"] and guion.validar(copy.deepcopy(BUENO))["ilustrativo"] is True)
comprobar("una línea de voz por escena (l1…l8)", list(guion.lineas(BUENO)) == [f"l{i}" for i in range(1, 9)])
m = copy.deepcopy(BUENO); m["tema"] = "inventado"; rechaza("tema desconocido se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"] = m["escenas"][:1]; rechaza("una sola escena se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"] = m["escenas"] * 2; rechaza("más de 8 escenas se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][0]["tipo"] = "video_de_stock"; rechaza("tipo de escena desconocido se rechaza", m)
m = copy.deepcopy(BUENO); del m["escenas"][1]["voz"]; rechaza("escena sin voz se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][1]["voz"] = "x" * 301; rechaza("voz demasiado larga se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][0]["titulo"] = "x" * 49; rechaza("título demasiado largo se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][1]["valor"] = float("nan"); rechaza("número NaN se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][1]["valor"] = "quince"; rechaza("valor que no es número se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][2]["puntos"] = [3]; rechaza("gráfico con un solo punto se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][2]["anotaciones"][0]["i"] = 99; rechaza("anotación fuera del gráfico se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][3]["destacar"] = 7; rechaza("barra destacada inexistente se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][4]["segmentos"][0]["v"] = 0; rechaza("segmento con valor 0 se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][5]["items"][0] = {"t": "x" * 40}; rechaza("punto de lista demasiado largo se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][6]["items"][0]["tono"] = "rosa"; rechaza("tono de tarjeta desconocido se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][7]["opciones"] = ["solo una"]; rechaza("pregunta con una opción se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][1]["valor"] = "x"; m["escenas"][2]["puntos"] = [1]
try:
    guion.validar(m)
except ValueError as e:
    comprobar("el error lista todos los fallos a la vez", "escena 2" in str(e) and "escena 3" in str(e))

# --- 2. Sonidos -----------------------------------------------------------------------------------------------------
claves = ["whoosh:0", "whoosh:1", "whoosh:2", "swipe", "pop:0", "pop:1", "pop:2", "pop:3", "card", "click", "tick", "ding:0", "ding:1", "ding:2", "impact", "error", "riser:0", "riser:2", "blip:0", "blip:5"]
comprobar("todos los sonidos y variantes se generan finitos y con volumen", all(np.isfinite(sfx.sonido(c)).all() and np.max(np.abs(sfx.sonido(c))) > 0.3 for c in claves))
comprobar("las variantes de un sonido son distintas", not np.array_equal(sfx.sonido("pop:0"), sfx.sonido("pop:1")) and not np.array_equal(sfx.sonido("ding:0"), sfx.sonido("ding:2")))
try:
    sfx.sonido("trompeta")
    comprobar("sonido desconocido da error", False)
except ValueError:
    comprobar("sonido desconocido da error", True)
with tempfile.TemporaryDirectory() as tmp:
    n, pico = sfx.mezclar([(0.1, "impact", 1.0)] * 6 + [(0.2, "whoosh:0", 1.0), (-5, "pop", 1), (999, "pop", 1)], 3.0, str(Path(tmp) / "m.wav"))
    comprobar("la mezcla no satura (pico ≤ 0,95) y descarta eventos fuera de tiempo", pico <= 0.95 and n == 7)

# --- 3. Paletas -----------------------------------------------------------------------------------------------------
claves_p = {"bg", "surface", "raised", "text", "muted", "border", "up", "down", "warn", "acc", "acc2", "resalte", "etiqueta"}
comprobar("las 5 paletas tienen todos los colores", len(paletas.TEMAS) == 5 and all(claves_p <= set(paletas.paleta(t)) for t in paletas.TEMAS))
comprobar("el fondo de marca es el mismo en todos los temas", len({paletas.paleta(t)["bg"] for t in paletas.TEMAS}) == 1)
comprobar("el acento cambia entre temas", len({paletas.paleta(t)["acc"] for t in paletas.TEMAS}) == 5)
try:
    paletas.paleta("rosa")
    comprobar("tema desconocido da error", False)
except ValueError:
    comprobar("tema desconocido da error", True)

# --- 4. Contexto de tiempos -----------------------------------------------------------------------------------------
palabras = [{"t": "Esta", "ini": 0.1, "fin": 0.4}, {"t": "frase,", "ini": 0.5, "fin": 0.9}, {"t": "prueba.", "ini": 1.0, "fin": 1.6}]
c = E.Ctx(1, 5.0, 8.0, 5.2, 7.2, palabras, 984, 1180, paletas.paleta("bolsa"))
comprobar("T(palabra) devuelve el segundo absoluto de esa palabra (ignora tildes y signos)", c.T("FRASE") == 5.7 and c.T("prueba") == 6.2)
comprobar("T(fracción) reparte a lo largo de la frase", c.T(0.5) == 6.2 and c.T(0) == 5.2 and c.T(3) == 7.2)
comprobar("T(palabra inexistente) usa la fracción por defecto y deja un aviso", c.T("zzz", 0.25) == 5.7 and len(c.avisos) == 1)
comprobar("es() formatea a la española", E.es(1234.5, 1) == "1.234,5" and E.es(-0.5, 1) == "-0,5" and E.es(15) == "15")

# --- 5. Escenas: estructura, ids, sonidos dentro de tiempo ----------------------------------------------------------
for ancho in (984, 648):
    for i, e in enumerate(BUENO["escenas"]):
        ctx = E.Ctx(i, 2.0, 8.0, 2.3, 7.5, palabras, ancho, 1180, paletas.paleta("bolsa"))
        html, js = E.ESCENAS[e["tipo"]][0](ctx, e)
        js_txt = "\n".join(js)
        ids_html = set(re.findall(r'id="([^"]+)"', html))
        ids_js = set(re.findall(SEL, js_txt))
        ok = (len(html) > 50 and js and "NaN" not in html + js_txt and "None" not in html + js_txt and "undefined" not in html + js_txt
              and ids_js <= ids_html and ctx.ev and all(ctx.t0 - 0.01 <= t <= ctx.t1 + 0.01 for t, _, _ in ctx.ev)
              and all(v <= 1 for _, _, v in ctx.ev))
        for _, clave, _ in ctx.ev:
            sfx.sonido(clave)
        comprobar(f"escena «{e['tipo']}» a {ancho}px: html/js coherentes, ids existen, sonidos dentro de la escena", ok)
        if not ok:
            print("   ids que faltan:", ids_js - ids_html)

# --- 6. Motor completo con voz sintética ----------------------------------------------------------------------------
def proyecto_falso(tmp, tipo_post, tema="bolsa", duplicados=False):
    _n[0] += 1
    d = Path(tmp) / f"p{_n[0]}_{tipo_post}"
    voz = d / "assets" / "voz"
    voz.mkdir(parents=True)
    sb = copy.deepcopy(BUENO); sb["tipo_post"] = tipo_post; sb["tema"] = tema
    (d / "storyboard.json").write_text(json.dumps(sb), encoding="utf-8")
    dur, pal = {}, {}
    for i in range(1, 9):
        seg = 3.0 + 0.2 * i
        t = np.arange(int(24000 * seg)) / 24000
        sf.write(voz / f"l{i}.wav", (0.3 * np.sin(2 * np.pi * 180 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t))).astype("float32"), 24000)
        ws = VOZ.split()
        dur[f"l{i}"] = {"texto": VOZ, "segundos": round(seg, 2)}
        pal[f"l{i}"] = [{"t": w, "ini": 0.15 if duplicados else round(0.15 + k * (seg - 0.5) / len(ws), 3), "fin": round(0.15 + (k + 0.8) * (seg - 0.5) / len(ws), 3)} for k, w in enumerate(ws)]
    (voz / "duraciones.json").write_text(json.dumps(dur), encoding="utf-8")
    (voz / "palabras.json").write_text(json.dumps(pal), encoding="utf-8")
    return d


def selectores_ok(html):
    ids = set(re.findall(r'id="([^"]+)"', html))
    usados = set(re.findall(SEL, html.split("<script>")[-1]))
    return usados - ids


with tempfile.TemporaryDirectory() as tmp:
    for tipo_post, esperado in (("datos", [1, 8]), ("leccion", list(range(1, 9))), ("noticia", [])):
        d = proyecto_falso(tmp, tipo_post)
        r = motor.construir(d)
        html = (d / "index.html").read_text(encoding="utf-8")
        falta = selectores_ok(html)
        comprobar(f"motor «{tipo_post}»: profesor en escenas {esperado or 'ninguna'}", r["profesor_en"] == esperado and (('id="prof"' in html) == bool(esperado)))
        comprobar(f"motor «{tipo_post}»: todos los selectores del JS existen en el HTML (faltan: {sorted(falta) or 'ninguno'})", not falta)
        comprobar(f"motor «{tipo_post}»: las 8 escenas y el cierre están, con sonido mezclado", all(f'id="S{i}"' in html for i in range(8)) and 'id="fin"' in html and (d / "assets" / "sfx_mix.wav").exists() and r["pico_sfx"] <= 0.95)
        comprobar(f"motor «{tipo_post}»: la duración total cuadra con la voz", r["total"] > sum(3.0 + 0.2 * i for i in range(1, 9)))
    d = proyecto_falso(tmp, "datos")
    motor.construir(d)
    html = (d / "index.html").read_text(encoding="utf-8")
    comprobar("con profesor la escena es estrecha (648) y sin él ancha (984)", 'id="S0" data-start="0.0" data-duration' in html and "width:648px" in html and "width:984px" in html)
    resultados = {}
    for tema in paletas.TEMAS:
        dd = proyecto_falso(tmp + "/" + tema, "datos", tema)
        motor.construir(dd)
        resultados[tema] = (dd / "index.html").read_text(encoding="utf-8")
    comprobar("cada tema pinta su color de acento y conserva el fondo de marca", all(f"--acc:{paletas.paleta(t)['acc']}" in h and "--bg:#0B1020" in h for t, h in resultados.items()))
    comprobar("el pie avisa de que es educativo y los gráficos son ilustrativos", "no es asesoramiento financiero" in html and "Gráficos ilustrativos" in html)

# --- 7. Fallo real encontrado: palabras con el mismo tiempo dejaban un bloque de subtítulos con duración 0 (se quedaba en pantalla) ---------
from types import SimpleNamespace as NS
ww = [NS(word="uno", start=0.5, end=0.6), NS(word="dos", start=0.5, end=0.7), NS(word="tres", start=0.5, end=0.7), NS(word="cuatro", start=2.0, end=2.1)]
al = pal_mod.alinear("uno dos tres cuatro cinco", ww, 2.4)
ini = [w["ini"] for w in al]
comprobar("palabras con el mismo tiempo se separan: tiempos estrictamente crecientes", all(b - a >= 0.039 for a, b in zip(ini, ini[1:])) and ini[-1] <= 2.4)
comprobar("las palabras no oídas por Whisper se interpolan entre las vecinas", al[3]["ini"] >= 2.0 and al[4]["ini"] > al[3]["ini"])
with tempfile.TemporaryDirectory() as tmp:
    d = proyecto_falso(tmp, "datos", duplicados=True)
    motor.construir(d)
    html = (d / "index.html").read_text(encoding="utf-8")
    duraciones = [float(x) for x in re.findall(r'class="sub clip" id="c\d+" data-start="[\d.]+" data-duration="([\d.-]+)"', html)]
    comprobar(f"ningún bloque de subtítulos dura menos de 0,2 s (mínimo: {min(duraciones)} s, de {len(duraciones)} bloques)", bool(duraciones) and min(duraciones) >= 0.2)
    comprobar("todos los elementos con duración tienen duración positiva", all(float(x) > 0 for x in re.findall(r'data-duration="([\d.-]+)"', html)))

print("\nTODO CORRECTO" if not fallos else f"\nFALLOS ({len(fallos)}): {fallos}")
sys.exit(1 if fallos else 0)
