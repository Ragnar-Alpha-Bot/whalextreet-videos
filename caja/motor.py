"""Motor de la caja de herramientas: guion de escenas + voz + tiempos de palabras  ->  proyecto HyperFrames (index.html) y pista de sonidos.

    from motor import construir
    construir(Path("proyectos/bolsa-per"))

Necesita en <proyecto>/: storyboard.json y assets/voz/{duraciones.json, palabras.json, l1.wav...} (los crea pipeline.py).
Qué hace por su cuenta: colores del tema, subtítulos palabra a palabra, profesor según la regla de formatos (presentador / cameo /
solo_datos), un sonido en cada transición y aparición, y el cierre con la marca.
"""
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(RAIZ))
from escenas import ESCENAS, Ctx, J, fromTo, to  # noqa: E402
from formatos_video import formato_para, profesor_en  # noqa: E402
from guion import validar  # noqa: E402
from paletas import paleta, rgb  # noqa: E402
from sfx import mezclar  # noqa: E402

GAP, LEAD, TAIL = 0.35, 0.05, 2.8              # la voz del gancho arranca a los 0,05 s
MIN_BLOQUE = 0.2                     # duración mínima de un bloque de subtítulos (s)
H = GAP / 2
AREA_TOP, AREA_H = 470, 1010                  # zona segura: TikTok/Instagram/Shorts tapan la parte de abajo
ANGULO = [10, 4, 22, 14, 18, 8, 16, 12]

CSS = """
@font-face { font-family:"InterW"; src:url("assets/Inter-Bold.otf"); font-weight:700; }
@font-face { font-family:"InterW"; src:url("assets/Inter-SemiBold.otf"); font-weight:600; }
@font-face { font-family:"PlexW"; src:url("assets/IBMPlexMono-Bold.ttf"); font-weight:700; }
:root { %%VARS%% }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:var(--bg); }
#root { position:relative; width:1080px; height:1920px; overflow:hidden; font-family:"InterW",sans-serif; color:var(--text);
  background: radial-gradient(900px 700px at 85% 10%, %%GLOW1%%, transparent 60%), radial-gradient(900px 800px at 10% 80%, %%GLOW2%%, transparent 60%), var(--bg); }
#grid { position:absolute; inset:-80px; opacity:.5; background-image: linear-gradient(rgba(178,190,209,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(178,190,209,.07) 1px, transparent 1px); background-size:72px 72px; }
.h { opacity:0; }
#top { position:absolute; left:64px; right:64px; top:110px; display:flex; align-items:center; justify-content:space-between; z-index:20; }
#top img { height:54px; }
#pill { font-family:"PlexW",monospace; font-weight:700; font-size:26px; letter-spacing:.14em; color:var(--acc); border:2px solid var(--acc); padding:10px 22px; border-radius:999px; }
.sub { position:absolute; left:50px; right:50px; top:232px; height:220px; display:flex; align-items:center; justify-content:center; flex-wrap:wrap; gap:0 18px; text-align:center; font-weight:700; font-size:80px; line-height:1.08; letter-spacing:-.02em; z-index:30; text-shadow:0 4px 30px rgba(0,0,0,.7); }
.w { position:relative; display:inline-block; opacity:.38; color:var(--text); }
.u { position:absolute; left:0; right:0; bottom:-4px; height:9px; border-radius:5px; background:var(--resalte); transform-origin:left center; transform:scaleX(0); }
.scene { position:absolute; top:%%TOP%%px; height:%%AH%%px; z-index:6; }
.col { display:flex; flex-direction:column; height:100%; }
.chip { display:inline-block; font-family:"PlexW",monospace; font-weight:700; letter-spacing:.12em; padding:.32em .85em; border-radius:999px; color:var(--c); border:2px solid var(--c); background:color-mix(in srgb, var(--c) 14%, transparent); }
.lab { font-family:"PlexW",monospace; font-weight:700; letter-spacing:.1em; color:var(--muted); }
.big { font-weight:700; letter-spacing:-.03em; line-height:1.04; }
.nota { font-weight:600; color:var(--muted); line-height:1.2; }
.pildora { display:inline-block; font-weight:700; padding:.3em .85em; border-radius:999px; background:var(--raised); border:2px solid var(--border); color:var(--text); }
.linea { height:10px; border-radius:5px; background:var(--acc); }
.pin { position:absolute; border-radius:50%; background:var(--text); border:4px solid var(--acc); }
.pista { background:var(--raised); border-radius:999px; overflow:hidden; }
.fila { display:flex; align-items:center; background:var(--raised); border:2px solid var(--border); border-radius:28px; padding:0 28px; font-weight:700; }
.ck { flex:none; border-radius:50%; border:3px solid var(--border); display:flex; align-items:center; justify-content:center; color:transparent; }
.tarjeta { display:flex; flex-direction:column; justify-content:center; background:var(--surface); border:2px solid var(--border); border-radius:38px; }
.opcion { display:flex; align-items:center; background:var(--surface); border:3px solid var(--border); border-radius:42px; font-weight:700; }
.opcion b { flex:none; border-radius:50%; color:#0B1020; display:flex; align-items:center; justify-content:center; }
#prof { position:absolute; left:-6px; top:566px; width:366px; height:640px; z-index:15; opacity:0; }
#prof svg { width:366px; height:640px; display:block; overflow:visible; }
#foot { position:absolute; left:40px; right:40px; top:1510px; font-family:"PlexW",monospace; font-size:27px; line-height:1.35; color:rgba(178,190,209,.8); text-align:center; z-index:20; }
#flash { position:absolute; inset:0; background:#fff; opacity:0; z-index:50; pointer-events:none; }
"""


def _estados_boca(wav):
    x, sr = sf.read(wav)
    if x.ndim > 1:
        x = x.mean(axis=1)
    hop = int(sr / 30)
    rms = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop + 1, hop)])
    ref = np.percentile(rms, 90) or 1.0
    st = [0 if r < 0.16 * ref else (1 if r < 0.5 * ref else 2) for r in rms]
    for i in range(1, len(st) - 1):
        if st[i - 1] == st[i + 1] != st[i]:
            st[i] = st[i - 1]
    return st


def _profesor_svg():
    svg = (RAIZ / "marca" / "profesor_TAL_CUAL.svg").read_text(encoding="utf-8").strip()
    marca = '<path d="M193 322 Q201 328 209 322 Q201 318 193 322Z" fill="#E36F78"/></g>'
    assert marca in svg, "el SVG del profesor no es el aprobado"
    return svg.replace(marca, marca + '<g id="boca_media" opacity="0"><path d="M184 309 Q201 328 218 309 Q201 316 184 309Z" fill="#6E1F27"/>'
                       '<path d="M188 310 Q201 318 214 310 L214 312 Q201 320 188 312Z" fill="#FFFFFF"/></g>', 1)


def construir(proyecto):
    proyecto = Path(proyecto).resolve()
    sb = validar(json.loads((proyecto / "storyboard.json").read_text(encoding="utf-8")))
    voz = proyecto / "assets" / "voz"
    DUR = json.loads((voz / "duraciones.json").read_text(encoding="utf-8"))
    PAL = json.loads((voz / "palabras.json").read_text(encoding="utf-8"))
    escenas = sb["escenas"]
    n = len(escenas)
    ks = [f"l{i}" for i in range(1, n + 1)]
    for k in ks:
        assert k in DUR and k in PAL, f"falta la voz de {k}: ejecuta pipeline.py"
    p = paleta(sb["tema"])

    # --- tiempos ---------------------------------------------------------------------------------------------------
    t, inicio = LEAD, {}
    for k in ks:
        inicio[k] = round(t, 2)
        t += DUR[k]["segundos"] + GAP
    fin = {k: round(inicio[k] + DUR[k]["segundos"], 2) for k in ks}
    s_end = round(fin[ks[-1]] + H, 2)
    TOTAL = round(s_end + TAIL, 2)
    t0s = [0.0 if i == 0 else round(inicio[k] - H, 2) for i, k in enumerate(ks)]
    t1s = [t0s[i + 1] if i + 1 < n else TOTAL for i in range(n)]       # el cta se queda en pantalla hasta el final

    # --- profesor según la regla de formatos -----------------------------------------------------------------------
    formato = formato_para(sb["tipo_post"])
    # escena 0 = gancho a pantalla completa (sin profesor); la 1ª escena de contenido hace de «gancho» de la regla; la última (cta) de «cierre»
    momento = lambda i: "gancho" if i == 1 else ("cierre" if i == n - 1 else "cuerpo")
    visible = [False if i == 0 else profesor_en(sb["tipo_post"], momento(i)) for i in range(n)]
    tramos, cur = [], None
    for i in range(n):
        if visible[i]:
            cur = [i, i] if cur is None else [cur[0], i]
        elif cur:
            tramos.append(tuple(cur)); cur = None
    if cur:
        tramos.append(tuple(cur))

    # --- escenas -----------------------------------------------------------------------------------------------------
    EV, avisos, html_esc, js_esc = [], [], [], []
    for i, e in enumerate(escenas):
        W, left = (648, 384) if visible[i] else (984, 48)
        ctx = Ctx(i, t0s[i], t1s[i], inicio[ks[i]], fin[ks[i]], PAL[ks[i]], W, AREA_H, p)
        h, js = ESCENAS[e["tipo"]][0](ctx, e)
        sid = f"S{i}"
        html_esc.append(f'<div class="scene clip" id="{sid}" data-start="{t0s[i]}" data-duration="{round(t1s[i] - t0s[i], 2)}" data-track-index="1" style="left:{left}px;width:{W}px">{h}</div>')
        js_esc.append(fromTo(f"#{sid}", {"opacity": 0}, {"opacity": 1, "duration": .05 if i == 0 else .2}, t0s[i]))
        js_esc += js
        if i < n - 1:
            js_esc.append(to(f"#{sid}", {"opacity": 0, "duration": .25}, t1s[i] - .25))
        EV += ctx.ev
        avisos += ctx.avisos
        EV.append((0.1 if i == 0 else t0s[i], f"whoosh:{i % 3}", .4 if i == 0 else .45))

    # --- subtítulos palabra a palabra ------------------------------------------------------------------------------
    sub_html, sub_js, nch = [], [], 0
    for k in ks:
        ws = PAL[k]
        grupos, cur = [], []
        for i, w in enumerate(ws):
            cur.append(i)
            txt = " ".join(ws[j]["t"] for j in cur)
            if len(cur) >= 4 or len(txt) >= 22 or (re.search(r"[.:?!,]$", w["t"]) and len(cur) >= 2):
                grupos.append(cur); cur = []
        if cur:
            grupos.append(cur)
        if len(grupos) > 1 and len(grupos[-1]) == 1:
            grupos[-2] += grupos.pop()
        arranques, previo = [], -1.0
        for g in grupos:                       # arranques estrictamente crecientes (una duración 0 dejaría el bloque en pantalla para siempre)
            a_ = max(0.0, round(inicio[k] + ws[g[0]]["ini"] - 0.05, 2), round(previo + MIN_BLOQUE, 2))
            arranques.append(a_)
            previo = a_
        for gi, g in enumerate(grupos):
            a = arranques[gi]
            b = arranques[gi + 1] if gi + 1 < len(grupos) else round(max(fin[k] + 0.12, a + MIN_BLOQUE), 2)
            spans = "".join(f'<span class="w" id="w{nch}_{j}">{ws[i]["t"]}<i class="u" id="u{nch}_{j}"></i></span> ' for j, i in enumerate(g))
            sub_html.append(f'<div class="sub clip" id="c{nch}" data-start="{a}" data-duration="{round(b - a, 2)}" data-track-index="6">{spans}</div>')
            sub_js.append(fromTo(f"#c{nch}", {"opacity": 0, "y": 16, "scale": .97}, {"opacity": 1, "y": 0, "scale": 1, "duration": .14, "ease": "power3.out"}, a))
            EV.append((a, "tick", 0.16))
            for j, i in enumerate(g):
                t0 = round(inicio[k] + ws[i]["ini"], 3)
                t1 = round(inicio[k] + ws[g[j + 1]]["ini"], 3) if j + 1 < len(g) else round(inicio[k] + ws[i]["fin"] + 0.05, 3)
                sub_js.append(f'tl.set("#w{nch}_{j}",{{opacity:1,color:"{p["resalte"]}"}},{t0});tl.fromTo("#u{nch}_{j}",{{scaleX:0}},{{scaleX:1,duration:.14,ease:"power2.out"}},{t0});'
                              f'tl.set("#w{nch}_{j}",{{color:"{p["text"]}"}},{t1});tl.set("#u{nch}_{j}",{{opacity:0}},{t1});')
            nch += 1

    # --- profesor: entra/sale, boca con la voz, parpadeo, brazo ----------------------------------------------------
    prof_js = []
    if any(visible):
        prof_js.append('tl.set("#prof",{opacity:0,x:-430},0);')
        parp = []
        for a, b in tramos:
            ta = 0.05 if a == 0 else round(t0s[a], 2)
            tf = TOTAL if b == n - 1 else round(t1s[b], 2)
            prof_js.append(f'tl.to("#prof",{{opacity:1,x:0,duration:.55,ease:"power3.out"}},{ta});')
            EV.append((ta, "swipe", .4))
            if b != n - 1:
                prof_js.append(f'tl.to("#prof",{{opacity:0,x:-430,duration:.45,ease:"power2.in"}},{round(tf - .45, 2)});')
                EV.append((round(tf - .45, 2), "swipe", .3))
            tb = max(ta + 1.0, 1.6)
            while tb < tf - 0.4:
                parp.append(f'tl.set("#parpados",{{opacity:1}},{round(tb, 2)});tl.set("#parpados",{{opacity:0}},{round(tb + 0.13, 2)});')
                tb += 3.3
        prof_js.append(f'tl.fromTo("#prof",{{y:0}},{{y:-5,duration:.9,ease:"sine.inOut",yoyo:true,repeat:{int(TOTAL / 0.9)}}},0);')
        actual = 0
        for i, k in enumerate(ks):
            if not visible[i]:
                continue
            for fr, e_ in enumerate(_estados_boca(voz / f"{k}.wav")):
                if e_ != actual:
                    tt = round(inicio[k] + fr / 30, 3)
                    prof_js.append(f'tl.set("#boca_cerrada",{{opacity:{1 if e_ == 0 else 0}}},{tt});tl.set("#boca_media",{{opacity:{1 if e_ == 1 else 0}}},{tt});tl.set("#boca_abierta",{{opacity:{1 if e_ == 2 else 0}}},{tt});')
                    actual = e_
            if actual != 0:
                cc = round(fin[k] + 0.02, 3)
                prof_js.append(f'tl.set("#boca_cerrada",{{opacity:1}},{cc});tl.set("#boca_media",{{opacity:0}},{cc});tl.set("#boca_abierta",{{opacity:0}},{cc});')
                actual = 0
            ang = ANGULO[i % len(ANGULO)]
            prof_js.append(f'tl.to("#brazo_d",{{rotation:{ang},svgOrigin:"274 286",duration:.55,ease:"power2.inOut"}},{round(inicio[k] - 0.05, 2)});'
                           f'tl.to("#brazo_d",{{rotation:{ang + 5},svgOrigin:"274 286",duration:.45,ease:"sine.inOut",yoyo:true,repeat:{max(1, int(DUR[k]["segundos"] / 0.9))}}},{round(inicio[k] + 0.6, 2)});')
        prof_js += parp

    # --- cierre y sonidos -------------------------------------------------------------------------------------------
    (proyecto / "assets").mkdir(parents=True, exist_ok=True)
    for f in (RAIZ / "marca").iterdir():
        shutil.copy(f, proyecto / "assets" / f.name)
    n_ef, pico = mezclar(EV, TOTAL, str(proyecto / "assets" / "sfx_mix.wav"))

    audio = "\n".join(f'<audio id="a{k}" src="assets/voz/{k}.wav" data-start="{inicio[k]}" data-duration="{DUR[k]["segundos"]}" data-volume="1"></audio>' for k in ks)
    audio += f'\n<audio id="asfx" src="assets/sfx_mix.wav" data-start="0" data-duration="{TOTAL}" data-volume="0.6"></audio>'
    etiqueta = sb.get("etiqueta") or p["etiqueta"]
    pie = "Contenido educativo, no es asesoramiento financiero" + ("<br/>Gráficos ilustrativos, sin datos reales" if sb["ilustrativo"] else "")
    vars_ = ";".join(f"--{k}:{p[k]}" for k in ("bg", "surface", "raised", "text", "muted", "border", "up", "down", "warn", "acc", "acc2", "resalte"))
    css = CSS.replace("%%VARS%%", vars_).replace("%%GLOW1%%", rgb(p["acc"], .12)).replace("%%GLOW2%%", rgb(p["acc2"], .13)).replace("%%TOP%%", str(AREA_TOP)).replace("%%AH%%", str(AREA_H))

    body = (f'<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">\n'
            f'<div id="grid"></div>\n<div id="top"><img src="assets/isotipo.png" alt="WhaleXtreet" /><div id="pill">{etiqueta}</div></div>\n'
            + ("\n".join(sub_html)) + "\n" + ("\n".join(html_esc)) + "\n"
            + (f'<div id="prof">{_profesor_svg()}</div>\n' if any(visible) else "")
            + f'<div id="foot">{pie}</div>\n'
            f'<div id="flash"></div>\n{audio}\n</div>')

    js = ("const fm=(v,d)=>{const neg=v<0;let s=Math.abs(v).toFixed(d);let [a,b]=s.split('.');a=a.replace(/\\B(?=(\\d{3})+(?!\\d))/g,'.');return (neg?'-':'')+(b?a+','+b:a)};\n"
          "const tl = gsap.timeline({ paused: true });\n"
          f'tl.fromTo("#grid",{{y:0}},{{y:-72,duration:{TOTAL},ease:"none"}},0);\n'
          'tl.fromTo("#top",{opacity:0,y:-20},{opacity:1,y:0,duration:.5,ease:"power3.out"},.05);\n'
          + "\n".join(js_esc) + "\n"
          + "\n"
          + "\n".join(prof_js) + "\n" + "\n".join(sub_js) + '\nwindow.__timelines["main"] = tl;\ntl.seek(0);\n')

    html = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="UTF-8" />\n<meta name="viewport" content="width=1080, height=1920" />\n'
            '<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>\n<style>' + css + '</style>\n</head>\n<body>\n'
            + body + '\n<script>' + js + '</script>\n</body>\n</html>\n')
    (proyecto / "index.html").write_text(html, encoding="utf-8")
    nombre = proyecto.name
    (proyecto / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}, "media": {"autoProxy": True}}, indent=2), encoding="utf-8")
    (proyecto / "meta.json").write_text(json.dumps({"id": nombre, "name": nombre}, indent=2), encoding="utf-8")
    (proyecto / "package.json").write_text(json.dumps({"name": nombre, "private": True, "type": "module", "scripts": {
        "check": "npx --yes hyperframes@0.9.25 check", "render": "npx --yes hyperframes@0.9.25 render"}}, indent=2), encoding="utf-8")
    resumen = {"total": TOTAL, "formato": formato, "escenas": n, "profesor_en": [i + 1 for i in range(n) if visible[i]], "efectos": n_ef, "pico_sfx": pico, "avisos": avisos}
    print(f"index.html listo · {TOTAL} s · formato {formato} · profesor en escenas {resumen['profesor_en'] or 'ninguna'} · {nch} bloques de subtítulos · {n_ef} efectos de sonido")
    for a in avisos:
        print("AVISO:", a)
    return resumen
