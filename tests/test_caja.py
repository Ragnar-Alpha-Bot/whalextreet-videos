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
        {"tipo": "gancho", "voz": "¿Compraste solo porque subía?", "texto": "¿Compraste porque subía?", "resalte": "subía", "icono": "alerta"},
        {"tipo": "titulo", "voz": VOZ, "titulo": "El PER en 20 segundos", "subtitulo": "Un número, una idea", "etiqueta": "BOLSA"},
        {"tipo": "numero", "voz": VOZ, "valor": 15.5, "decimales": 1, "sufijo": "x", "etiqueta": "PER", "detalle": "15 € entre 1 €", "delta": -2.5},
        {"tipo": "grafico", "voz": VOZ, "titulo": "Precio", "puntos": [10, 12, 11, 15, 14, 18], "etiquetas": ["Ene", "Jun"], "unidad": "€",
         "anotaciones": [{"i": 3, "texto": "Máximo", "cuando": "frase"}]},
        {"tipo": "barras", "voz": VOZ, "titulo": "PER por sector", "unidad": "x", "items": [{"n": "A", "v": 8}, {"n": "B", "v": 15, "cuando": "prueba"}, {"n": "C", "v": 30}]},
        {"tipo": "donut", "voz": VOZ, "titulo": "Reparto", "segmentos": [{"n": "Uno", "v": 60}, {"n": "Dos", "v": 25}, {"n": "Tres", "v": 15}]},
        {"tipo": "lista", "voz": VOZ, "titulo": "Revisa", "items": [{"t": "Deuda", "cuando": "frase"}, "Beneficios", "Sector"]},
        {"tipo": "tarjetas", "voz": VOZ, "items": [{"etiqueta": "Margen", "valor": "12,4 %", "tono": "up", "nota": "ilustrativo"}, {"etiqueta": "Deuda", "valor": "3x", "tono": "down"}]},
        {"tipo": "pregunta", "voz": VOZ, "pregunta": "¿Qué miras primero?", "opciones": ["El PER", "La deuda"]},
        {"tipo": "cta"},
    ],
}

# --- 1. Validador ---------------------------------------------------------------------------------------------------
comprobar("un guion completo y correcto se acepta", guion.validar(copy.deepcopy(BUENO)) is not None)
comprobar("se rellenan valores por defecto (ilustrativo, tipo_post)", guion.validar(copy.deepcopy(BUENO))["ilustrativo"] is True and guion.validar({**copy.deepcopy(BUENO), "tipo_post": "datos"})["tipo_post"] == "datos")
comprobar("una línea de voz por escena (l1…l8)", list(guion.lineas(BUENO)) == [f"l{i}" for i in range(1, 11)])
m = copy.deepcopy(BUENO); m["tema"] = "inventado"; rechaza("tema desconocido se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"] = m["escenas"][:1]; rechaza("una sola escena se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"] = m["escenas"] * 2; rechaza("más de 8 escenas se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][0]["tipo"] = "video_de_stock"; rechaza("tipo de escena desconocido se rechaza", m)
m = copy.deepcopy(BUENO); del m["escenas"][1]["voz"]; rechaza("escena sin voz se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][1]["voz"] = "x" * 301; rechaza("voz demasiado larga se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][1]["titulo"] = "x" * 49; rechaza("título demasiado largo se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][2]["valor"] = float("nan"); rechaza("número NaN se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][2]["valor"] = "quince"; rechaza("valor que no es número se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][3]["puntos"] = [3]; rechaza("gráfico con un solo punto se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][3]["anotaciones"][0]["i"] = 99; rechaza("anotación fuera del gráfico se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][4]["destacar"] = 7; rechaza("barra destacada inexistente se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][5]["segmentos"][0]["v"] = 0; rechaza("segmento con valor 0 se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][6]["items"][0] = {"t": "x" * 40}; rechaza("punto de lista demasiado largo se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][7]["items"][0]["tono"] = "rosa"; rechaza("tono de tarjeta desconocido se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][8]["opciones"] = ["solo una"]; rechaza("pregunta con una opción se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][2]["valor"] = "x"; m["escenas"][3]["puntos"] = [1]
try:
    guion.validar(m)
except ValueError as e:
    comprobar("el error lista todos los fallos a la vez", "escena 3" in str(e) and "escena 4" in str(e))

m = copy.deepcopy(BUENO); m["escenas"].pop(0); rechaza("sin gancho inicial se rechaza (obligatorio)", m)
m = copy.deepcopy(BUENO); m["escenas"].pop(-1); rechaza("sin cta final se rechaza (obligatorio)", m)
m = copy.deepcopy(BUENO); m["escenas"][0], m["escenas"][1] = m["escenas"][1], m["escenas"][0]; rechaza("el gancho no puede ir en segundo lugar", m)
m = copy.deepcopy(BUENO); m["escenas"].insert(3, {"tipo": "cta"}); rechaza("un cta en medio se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"].insert(3, copy.deepcopy(m["escenas"][0])); rechaza("un segundo gancho se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][0]["voz"] = "x" * 111; rechaza("la voz del gancho debe ser corta", m)
m = copy.deepcopy(BUENO); m["escenas"][0]["resalte"] = "inventada"; rechaza("el resalte debe ser una palabra del texto del gancho", m)
m = copy.deepcopy(BUENO); m["escenas"][0]["texto"] = "x" * 43; rechaza("texto del gancho demasiado largo se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][0]["icono"] = "calavera"; rechaza("icono desconocido se rechaza", m)
for frase in ("Ganancias GARANTIZADAS", "Inversión sin riesgo", "Hazte  rico ya", "No puedes perder", "Dinero fácil"):
    m = copy.deepcopy(BUENO); m["escenas"][1]["subtitulo"] = frase; rechaza(f"frase prohibida «{frase}» se rechaza (mayúsculas, tildes y espacios incluidos)", m)
m = copy.deepcopy(BUENO); m["escenas"][1]["voz"] = "Esto tiene riesgo, no es seguro nada."
comprobar("hablar del riesgo no se confunde con prometer sin riesgo", guion.validar(m) is not None)
ok = guion.validar(copy.deepcopy(BUENO))
comprobar("el cta sin voz usa la de marca/redes.json", ok["escenas"][-1]["voz"] == E.marca_redes()["cta_voz"] and guion.lineas(ok)["l10"] == E.marca_redes()["cta_voz"])
comprobar("el cta es de la marca: «Síguenos en WhaleXtreet» y las redes", "WhaleXtreet" in E.marca_redes()["cta_texto"] and len(E.marca_redes()["redes"]) >= 3)

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
        gancho = e["tipo"] == "gancho"
        ctx = E.Ctx(i, 0.0 if gancho else 2.0, 8.0, 0.05 if gancho else 2.3, 7.5, palabras, ancho, 1010, paletas.paleta("bolsa"))
        html, js = E.ESCENAS[e["tipo"]][0](ctx, e)
        js_txt = "\n".join(js)
        ids_html = set(re.findall(r'id="([^"]+)"', html))
        ids_js = set(re.findall(SEL, js_txt)) - ({"flash", f"S{i}"} if gancho else set())
        ok = (len(html) > 50 and js and "NaN" not in html + js_txt and "None" not in html + js_txt and "undefined" not in html + js_txt
              and ids_js <= ids_html and ctx.ev and all(ctx.t0 - 0.01 <= t <= ctx.t1 + 0.01 for t, _, _ in ctx.ev)
              and all(v <= 1 for _, _, v in ctx.ev))
        for _, clave, _ in ctx.ev:
            sfx.sonido(clave)
        comprobar(f"escena «{e['tipo']}» a {ancho}px: html/js coherentes, ids existen, sonidos dentro de la escena", ok)
        if not ok:
            print("   ids que faltan:", ids_js - ids_html)

# --- 6. Motor completo con voz sintética ----------------------------------------------------------------------------
def proyecto_falso(tmp, tipo_post, tema="bolsa", duplicados=False, sb_custom=None):
    _n[0] += 1
    d = Path(tmp) / f"p{_n[0]}_{tipo_post}"
    voz = d / "assets" / "voz"
    voz.mkdir(parents=True)
    sb = copy.deepcopy(sb_custom or BUENO); sb["tipo_post"] = tipo_post; sb["tema"] = tema
    (d / "storyboard.json").write_text(json.dumps(sb), encoding="utf-8")
    dur, pal = {}, {}
    for i in range(1, len(sb["escenas"]) + 1):
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
    for tipo_post, esperado in (("datos", [2, 10]), ("leccion", list(range(2, 11))), ("noticia", [])):
        d = proyecto_falso(tmp, tipo_post)
        r = motor.construir(d)
        html = (d / "index.html").read_text(encoding="utf-8")
        falta = selectores_ok(html)
        comprobar(f"motor «{tipo_post}»: profesor en escenas {esperado or 'ninguna'}", r["profesor_en"] == esperado and (('id="av_profesor"' in html) == bool(esperado)))
        comprobar(f"motor «{tipo_post}»: todos los selectores del JS existen en el HTML (faltan: {sorted(falta) or 'ninguno'})", not falta)
        comprobar(f"motor «{tipo_post}»: las 10 escenas y el flash del gancho están, con sonido mezclado", all(f'id="S{i}"' in html for i in range(10)) and 'id="flash"' in html and (d / "assets" / "sfx_mix.wav").exists() and r["pico_sfx"] <= 0.95)
        comprobar(f"motor «{tipo_post}»: la duración total cuadra con la voz", r["total"] > sum(3.0 + 0.2 * i for i in range(1, 11)))
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

# --- 6b. Gancho y cierre ------------------------------------------------------------------------------------------------
gc = E.Ctx(0, 0.0, 4.0, 0.05, 3.0, palabras, 984, 1010, paletas.paleta("alerta"))
E.e_gancho(gc, BUENO["escenas"][0])
comprobar("el gancho suena en el segundo 0 (golpe + transición) y sus palabras entran en el primer segundo", any(t <= 0.1 and k == "impact" for t, k, _ in gc.ev) and max(t for t, k, _ in gc.ev if k == "tick") < 1.0)
with tempfile.TemporaryDirectory() as tmp:
    d = proyecto_falso(tmp, "datos")
    r = motor.construir(d)
    html = (d / "index.html").read_text(encoding="utf-8")
    comprobar("la voz del gancho arranca a los 0,05 s y la primera escena aparece al instante", 'id="al1" src="assets/voz/l1.wav" data-start="0.05"' in html and re.search(r'id="S0" data-start="0.0"', html) is not None)
    m_ = re.search(r'id="S9" data-start="([\d.]+)" data-duration="([\d.]+)"', html)
    comprobar("el cta se queda en pantalla hasta el último fotograma", m_ is not None and abs(float(m_.group(1)) + float(m_.group(2)) - r["total"]) < 0.02)
    comprobar("el profesor nunca sale en el gancho a pantalla completa", 1 not in r["profesor_en"])
    zona = re.search(r"#foot \{[^}]*top:(\d+)px", html)
    area = re.search(r"\.scene \{ position:absolute; top:(\d+)px; height:(\d+)px", html)
    comprobar("zona segura: el contenido termina por encima de 1.540 px (las redes tapan la parte de abajo)", int(area.group(1)) + int(area.group(2)) <= 1540 and int(zona.group(1)) <= 1540)
import vozcache  # noqa: E402
pid_a, pid_b = vozcache.id_perfil(RAIZ / "perfiles" / "voz_D.pt"), "otra_voz"
comprobar("caché de voz: mismo texto y voz = misma clave; los espacios sobrantes no cuentan", vozcache.clave("Hola  mundo", pid_a) == vozcache.clave("Hola mundo", pid_a))
comprobar("caché de voz: otro texto u otra voz = otra clave (no reutiliza audio equivocado)", vozcache.clave("Hola mundo", pid_a) != vozcache.clave("Hola mundo.", pid_a) and vozcache.clave("Hola", pid_a) != vozcache.clave("Hola", pid_b))

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

# --- 8. Fallos vistos en el vídeo real: palabra del gancho que no cabía y porcentaje con decimal absurdo ---------------------------------------
for texto in ("¿Compraste porque subía?", "NADIE TE CUENTA ESTO", "Stop loss", "¡Cuidado con las criptomonedas pequeñas!", "Rentabilidad extraordinaria"):
    cg = E.Ctx(0, 0.0, 4.0, 0.05, 3.0, palabras, 984, 1010, paletas.paleta("alerta"))
    hg, _ = E.e_gancho(cg, {"tipo": "gancho", "voz": "x", "texto": texto[:42], "icono": "alerta"})
    fs = int(re.search(r'class="big" style="font-size:(\d+)px', hg).group(1))
    larga = max(len(w) for w in texto[:42].split())
    comprobar(f"gancho «{texto[:30]}»: la palabra más larga cabe en pantalla (fuente {fs}px)", 0.70 * larga * fs <= 984 * 0.93)
cg = E.Ctx(3, 2.0, 8.0, 2.3, 7.5, palabras, 648, 1010, paletas.paleta("alerta"))
hg, _ = E.e_grafico(cg, {"tipo": "grafico", "voz": "x", "titulo": "t", "puntos": [10, 11, 12, 14, 18, 25, 37, 34]})
comprobar("un cambio de +240 % se escribe sin decimales y uno pequeño con uno", "+240 %" in hg and ",0 %" not in hg)
hg2, _ = E.e_grafico(cg, {"tipo": "grafico", "voz": "x", "titulo": "t", "puntos": [100, 101.5, 103.2]})
comprobar("un cambio de +3,2 % conserva el decimal", "+3,2 %" in hg2)

# --- 9. Dos avatares: el profesor (aprobado, sin tocar) y el rubio ------------------------------------------------------------------------
m = copy.deepcopy(BUENO); m["avatar"] = "payaso"; rechaza("un avatar desconocido se rechaza", m)
for av in ("profesor", "rubio"):
    m = copy.deepcopy(BUENO); m["avatar"] = av
    comprobar(f"el avatar «{av}» es válido", guion.validar(m) is not None)
    svg = (RAIZ / "marca" / motor.AVATARES[av]).read_text(encoding="utf-8")
    comprobar(f"el avatar «{av}» trae todo lo que el motor anima (boca, párpados, brazo) y el marcador de la boca intermedia",
              all(x in svg for x in ('id="boca_cerrada"', 'id="boca_abierta"', 'id="parpados"', 'id="brazo_d"', 'M193 322 Q201 328 209 322 Q201 318 193 322Z')))
for av, esta, ausente in (("profesor", "#22252D", "#7A818E"), ("rubio", "#7A818E", "#22252D")):
    with tempfile.TemporaryDirectory() as tmp:
        d = proyecto_falso(tmp, "leccion")
        sbj = json.loads((d / "storyboard.json").read_text(encoding="utf-8"))
        sbj["avatar"] = av
        (d / "storyboard.json").write_text(json.dumps(sbj), encoding="utf-8")
        motor.construir(d)
        h = (d / "index.html").read_text(encoding="utf-8")
        comprobar(f"con avatar «{av}» el vídeo usa su traje ({esta}) y no el del otro", esta in h and ausente not in h and f'id="{"a_" if av == "profesor" else "b_"}boca_media"' in h)
with tempfile.TemporaryDirectory() as tmp:
    d = proyecto_falso(tmp, "leccion")
    motor.construir(d)
    comprobar("sin indicar avatar se usa el profesor, como antes", "#22252D" in (d / "index.html").read_text(encoding="utf-8"))
comprobar("el profesor aprobado no se ha tocado: sigue siendo traje negro, ojos verdes y barba castaña", all(x in (RAIZ / "marca" / "profesor_TAL_CUAL.svg").read_text(encoding="utf-8") for x in ("#22252D", "#3FB06A", "#8F6256")))

# --- 10. Dos avatares: lados, espejo, voz de cada uno y conversación ---------------------------------------------------------------------
import pipeline as _pipeline  # noqa: E402


def conversacion():
    sb = copy.deepcopy(BUENO)
    sb["avatar"] = "ambos"
    esc = sb["escenas"]
    esc.insert(1, {"tipo": "dialogo", "habla": "profesor", "rol": "pregunta", "texto": "¿Qué es un stop loss?", "voz": VOZ})
    esc.insert(2, {"tipo": "dialogo", "habla": "rubio", "rol": "respuesta", "texto": "Una orden que te saca si el precio cae hasta tu límite.", "voz": VOZ})
    for e in esc:
        if e["tipo"] == "lista":
            e["habla"] = "rubio"
        if e["tipo"] == "numero":
            e["habla"] = "profesor"
    return sb


m = conversacion(); guion.validar(m)
comprobar("una conversación con los dos avatares es válida", True)
m = copy.deepcopy(BUENO); m["escenas"].insert(1, {"tipo": "dialogo", "texto": "Hola", "voz": VOZ}); rechaza("una escena «dialogo» en un vídeo de un solo avatar se rechaza", m)
m = copy.deepcopy(BUENO); m["escenas"][2]["habla"] = "rubio"; rechaza("hablar con el otro avatar sin avatar «ambos» se rechaza", m)
m = conversacion(); m["escenas"][1]["habla"] = "robot"; rechaza("un hablante desconocido se rechaza", m)
m = conversacion(); m["escenas"][1]["rol"] = "grito"; rechaza("un rol de diálogo desconocido se rechaza", m)
m = conversacion(); m["escenas"][1]["texto"] = "x" * 91; rechaza("el texto del globo no puede pasar de 90 caracteres", m)
comprobar("quién habla: por defecto el avatar del vídeo; en «ambos», el profesor salvo que se indique",
          guion.hablantes({"avatar": "rubio", "escenas": [{}, {}]}) == ["rubio", "rubio"] and guion.hablantes({"avatar": "ambos", "escenas": [{}, {"habla": "rubio"}]}) == ["profesor", "rubio"])
voces = json.loads((RAIZ / "marca" / "voces.json").read_text(encoding="utf-8"))
comprobar("cada avatar tiene su voz y su perfil existe (profesor = D, rubio = C)", voces["profesor"] == "voz_D.pt" and voces["rubio"] == "voz_C.pt" and all((RAIZ / "perfiles" / voces[a]).exists() for a in ("profesor", "rubio")))
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp) / "v"
    (d / "assets" / "voz").mkdir(parents=True)
    (d / "assets" / "voz" / "l1.wav").write_bytes(b"x")
    (d / "assets" / "voz" / "duraciones.json").write_text(json.dumps({"l1": {"texto": "hola", "segundos": 1, "voz": "profesor", "huella": __import__("frases").huella_audio()}}), encoding="utf-8")
    comprobar("la voz se regenera si cambia quién habla (misma frase, otro avatar)", _pipeline.voz_al_dia(d, {"l1": "hola"}, {"l1": "profesor"}) and not _pipeline.voz_al_dia(d, {"l1": "hola"}, {"l1": "rubio"}))

with tempfile.TemporaryDirectory() as tmp:
    d = proyecto_falso(tmp, "leccion", sb_custom=conversacion())
    r = motor.construir(d)
    html = (d / "index.html").read_text(encoding="utf-8")
    ids = re.findall(r'\bid="([^"]+)"', html.split("<script>")[0])
    comprobar("con los dos avatares ningún identificador se repite en la página", len(ids) == len(set(ids)))
    comprobar("el HTML de la conversación no tiene unidades de CSS dobles (pxpx), que dejan sin dibujar el globo y su símbolo", "pxpx" not in html and not re.search(r"\dpx px|-px", html))
    comprobar("el globo muestra su flecha y el símbolo central de «?» y «✓»", html.count("border-top:") >= 2 and ">?<" in html and ">✓<" in html)
    comprobar("todos los selectores del JS existen (con los identificadores de cada avatar)", not selectores_ok(html))
    comprobar("salen los dos avatares: el profesor a la izquierda y el rubio a la derecha", 'id="av_profesor" class="av izq"' in html and 'id="av_rubio" class="av der"' in html)
    comprobar("solo el rubio va en espejo (levanta el brazo contrario)", 'tl.set("#flip_rubio",{scaleX:-1}' in html and 'tl.set("#flip_profesor",{scaleX:-1}' not in html)
    comprobar("en las escenas de diálogo los avatares bajan para dejar sitio al globo", html.count("y:274") >= 2)
    s1 = re.search(r'id="S1" [^>]*style="left:(\d+)px;width:(\d+)px"', html)
    comprobar("la escena de diálogo ocupa todo el ancho", s1.groups() == ("48", "984"))
    lista = [i for i, e in enumerate(conversacion()["escenas"]) if e["tipo"] == "lista"][0]
    num = [i for i, e in enumerate(conversacion()["escenas"]) if e["tipo"] == "numero"][0]
    sl = re.search(rf'id="S{lista}" [^>]*style="left:(\d+)px;width:(\d+)px"', html)
    sn = re.search(rf'id="S{num}" [^>]*style="left:(\d+)px;width:(\d+)px"', html)
    comprobar("el contenido va al lado contrario del que habla: con el rubio (derecha) a la izquierda, con el profesor a la derecha", sl.groups() == ("48", "648") and sn.groups() == ("384", "648"))
    # la boca solo se mueve en las frases de quien habla
    audio = {k: (float(a), float(b)) for k, a, b in re.findall(r'<audio id="a(l\d+)" src="[^"]+" data-start="([\d.]+)" data-duration="([\d.]+)"', html)}
    hab = guion.hablantes(guion.validar(conversacion()))
    rangos = {av: [(audio[f"l{i + 1}"][0] - 0.01, audio[f"l{i + 1}"][0] + audio[f"l{i + 1}"][1] + 0.06) for i, h in enumerate(hab) if h == av] for av in ("profesor", "rubio")}
    for av, pref in (("profesor", "a_"), ("rubio", "b_")):
        tiempos = [float(t) for t in re.findall(rf'tl\.set\("#{pref}boca_abierta",\{{opacity:\d\}},([\d.]+)\)', html)]
        comprobar(f"la boca del {av} se mueve (hay {len(tiempos)} cambios) y solo mientras habla él", len(tiempos) > 0 and all(any(a <= t <= b for a, b in rangos[av]) for t in tiempos))
    comprobar("el profesor y el rubio parpadean a destiempo", "#a_parpados" in html and "#b_parpados" in html)

with tempfile.TemporaryDirectory() as tmp:
    sbr = copy.deepcopy(BUENO); sbr["avatar"] = "rubio"
    d = proyecto_falso(tmp, "leccion", sb_custom=sbr)
    motor.construir(d)
    html = (d / "index.html").read_text(encoding="utf-8")
    comprobar("un vídeo solo con el rubio: sale solo él, a la derecha y en espejo, con el contenido a la izquierda",
              'id="av_rubio"' in html and 'id="av_profesor"' not in html and 'tl.set("#flip_rubio",{scaleX:-1}' in html and 'style="left:48px;width:648px"' in html and 'style="left:384px' not in html)
    sbp = copy.deepcopy(BUENO)
    d2 = proyecto_falso(tmp, "leccion", sb_custom=sbp)
    motor.construir(d2)
    h2 = (d2 / "index.html").read_text(encoding="utf-8")
    comprobar("un vídeo solo con el profesor sigue igual que siempre: a la izquierda, sin espejo y con el contenido a la derecha",
              'id="av_profesor"' in h2 and 'id="av_rubio"' not in h2 and "scaleX:-1" not in h2 and 'style="left:384px;width:648px"' in h2)

# --- 11. Ritmo y dinamismo del montaje ----------------------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    d = proyecto_falso(tmp, "leccion", sb_custom=conversacion())
    r = motor.construir(d)
    html = (d / "index.html").read_text(encoding="utf-8")
    segs = sum(3.0 + 0.2 * i for i in range(1, len(conversacion()["escenas"]) + 1))
    comprobar(f"el hueco entre escenas es el de la marca (0,2 s): duración {r['total']} s frente a {segs + 0.35 * 12 + 0.05 + 2.8:.1f} s con el hueco antiguo", r["total"] < segs + 0.35 * 12 + 0.05 + 2.8)
    comprobar("cada escena lleva su empuje de cámara lento (zoom 3,5 %)", html.count('"scale":1.035,"duration"') >= len(conversacion()["escenas"]))
    comprobar("las transiciones son rápidas (entrada 0,12 s, salida 0,15 s)", '"opacity":1,"duration":0.12' in html and '"opacity":0,"duration":0.15' in html)
    comprobar("el avatar que empieza a hablar da un pulso (el rubio, en espejo, conserva su signo)", 'tl.to("#flip_rubio",{scaleX:-1.035,scaleY:1.035' in html and 'tl.to("#flip_profesor",{scaleX:1.035,scaleY:1.035' in html)

print("\nTODO CORRECTO" if not fallos else f"\nFALLOS ({len(fallos)}): {fallos}")
sys.exit(1 if fallos else 0)
