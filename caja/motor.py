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
from guion import hablantes as _hablantes, validar  # noqa: E402
from paletas import paleta, rgb  # noqa: E402
from sfx import mezclar  # noqa: E402
import musica  # noqa: E402
from frases import config_audio  # noqa: E402

GAP, LEAD, TAIL = 0.35, 0.05, 2.8              # la voz del gancho arranca a los 0,05 s
MIN_BLOQUE = 0.2                     # duración mínima de un bloque de subtítulos (s)
H = GAP / 2
AREA_TOP, AREA_H = 470, 1010                  # zona segura: TikTok/Instagram/Shorts tapan la parte de abajo
HUD_HTML = ('<div id="hud"><div id="suelo"></div><div id="vineta"></div><div id="scan"></div><div id="barrido"></div>'
            '<i class="esq e1"></i><i class="esq e2"></i><i class="esq e3"></i><i class="esq e4"></i></div>\n')   # fondo de panel: rejilla en perspectiva, marcos y escaneo (color del tema)
HUD_JS = ('tl.fromTo("#suelo",{backgroundPositionY:0},{backgroundPositionY:"%%TOTAL%%px",duration:%%TOTAL%%,ease:"none"},0);\n'
          'tl.fromTo("#barrido",{y:0},{y:1930,duration:6,ease:"none",repeat:Math.ceil(%%TOTAL%%/6)},0);\n'
          'tl.fromTo(".esq",{opacity:0,scale:.6},{opacity:.7,scale:1,duration:.6,ease:"back.out(2)",stagger:.08},.1);\n')
ANGULO = [10, 4, 22, 14, 18, 8, 16, 12]
ANCHO_COMPLETO = ("terminal", "captura")       # escenas que necesitan todo el ancho para leerse: en ellas no sale el avatar (la voz sigue)

CSS = """
@font-face { font-family:"InterW"; src:url("assets/Inter-Bold.otf"); font-weight:700; }
@font-face { font-family:"InterW"; src:url("assets/Inter-SemiBold.otf"); font-weight:600; }
@font-face { font-family:"PlexW"; src:url("assets/IBMPlexMono-Bold.ttf"); font-weight:700; }
@font-face { font-family:"SerifW"; src:url("assets/InstrumentSerif-Italic.ttf"); font-style:italic; font-weight:400; }
.ac { font-family:"SerifW",Georgia,serif; font-style:italic; font-weight:400; color:var(--acc); letter-spacing:0; text-transform:none; font-size:1.16em; }
.sub.rc .u { display:none; } .sub.rc .w { padding:0 .16em; border-radius:.2em; background:transparent; }
:root { %%VARS%% }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:var(--bg); }
#root { position:relative; width:1080px; height:1920px; overflow:hidden; font-family:"InterW",sans-serif; color:var(--text);
  background: radial-gradient(900px 700px at 85% 10%, %%GLOW1%%, transparent 60%), radial-gradient(900px 800px at 10% 80%, %%GLOW2%%, transparent 60%), var(--bg); }
#grid { position:absolute; inset:-80px; opacity:.5; background-image: linear-gradient(rgba(178,190,209,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(178,190,209,.07) 1px, transparent 1px); background-size:72px 72px; }
.h { opacity:0; }
#hud { position:absolute; inset:0; z-index:2; pointer-events:none; overflow:hidden; }
#suelo { position:absolute; left:-70%; right:-70%; top:1130px; height:1100px; transform:perspective(560px) rotateX(66deg); transform-origin:top center; opacity:.34;
  background-image: linear-gradient(var(--acc) 2px, transparent 2px), linear-gradient(90deg, var(--acc) 2px, transparent 2px); background-size:96px 96px;
  -webkit-mask-image: linear-gradient(to bottom, transparent 0%, #000 45%, #000 100%); mask-image: linear-gradient(to bottom, transparent 0%, #000 45%, #000 100%); }
.esq { position:absolute; width:74px; height:74px; border:0 solid var(--acc); opacity:.7; filter:drop-shadow(0 0 10px var(--acc)); }
.e1 { left:30px; top:30px; border-left-width:5px; border-top-width:5px; } .e2 { right:30px; top:30px; border-right-width:5px; border-top-width:5px; }
.e3 { left:30px; bottom:30px; border-left-width:5px; border-bottom-width:5px; } .e4 { right:30px; bottom:30px; border-right-width:5px; border-bottom-width:5px; }
#scan { position:absolute; inset:0; background:repeating-linear-gradient(0deg, rgba(255,255,255,.028) 0 2px, transparent 2px 6px); }
#barrido { position:absolute; left:0; right:0; top:-8px; height:6px; background:linear-gradient(90deg, transparent, var(--acc), transparent); opacity:.22; filter:blur(1px); }
#vineta { position:absolute; inset:0; background:radial-gradient(ellipse at center, transparent 55%, rgba(4,7,16,.55) 100%); }
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
.av { position:absolute; top:566px; width:366px; height:640px; z-index:15; opacity:0; }
.av.izq { left:-6px; } .av.der { left:720px; }
.av svg { width:366px; height:640px; display:block; overflow:visible; }
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


AVATARES = {"profesor": "profesor_TAL_CUAL.svg", "rubio": "avatar_rubio.svg"}   # los dos avatares de la marca
LISTA_AVATARES = ("profesor", "rubio")
LADO = {"profesor": "izq", "rubio": "der"}      # A a la izquierda; B a la derecha (y en espejo: levanta el brazo contrario)
PREF = {"profesor": "a_", "rubio": "b_"}        # prefijo de los identificadores de cada avatar
BAJADA_DIALOGO = 274                            # en las escenas de diálogo los avatares bajan para dejar sitio al globo


def _svg_avatar(av):
    svg = (RAIZ / "marca" / AVATARES[av]).read_text(encoding="utf-8").strip()
    marca = '<path d="M193 322 Q201 328 209 322 Q201 318 193 322Z" fill="#E36F78"/></g>'
    assert marca in svg, f"el SVG del avatar «{av}» no tiene la boca esperada"
    svg = svg.replace(marca, marca + '<g id="boca_media" opacity="0"><path d="M184 309 Q201 328 218 309 Q201 316 184 309Z" fill="#6E1F27"/>'
                      '<path d="M188 310 Q201 318 214 310 L214 312 Q201 320 188 312Z" fill="#FFFFFF"/></g>', 1)
    pref = PREF[av]
    svg = re.sub(r'id="([^"]+)"', lambda m: f'id="{pref}{m.group(1)}"', svg)
    return re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{pref}{m.group(1)})", svg)


def construir(proyecto):
    proyecto = Path(proyecto).resolve()
    sb = validar(json.loads((proyecto / "storyboard.json").read_text(encoding="utf-8")))
    voz = proyecto / "assets" / "voz"
    DUR = json.loads((voz / "duraciones.json").read_text(encoding="utf-8"))
    PAL = json.loads((voz / "palabras.json").read_text(encoding="utf-8"))
    global GAP, H
    cfg_ritmo = config_audio()
    GAP = cfg_ritmo["gap_escenas_s"]
    H = GAP / 2
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

    # --- avatares: cuándo salen según la regla de formatos y quién habla en cada escena -------------------------------------
    formato = formato_para(sb["tipo_post"])
    habla = _hablantes(sb)
    # escena 0 = gancho a pantalla completa (sin avatar); la 1ª escena de contenido hace de «gancho» de la regla; la última (cta) de «cierre».
    # Las escenas «dialogo» muestran siempre a los dos; en el resto sale solo el que habla (si la regla de formatos lo permite).
    momento = lambda i: "gancho" if i == 1 else ("cierre" if i == n - 1 else "cuerpo")
    quienes = []
    for i, e in enumerate(escenas):
        if e["tipo"] == "dialogo":
            quienes.append(set(LISTA_AVATARES))
        elif i > 0 and e["tipo"] not in ANCHO_COMPLETO and profesor_en(sb["tipo_post"], momento(i)):
            quienes.append({habla[i]})
        else:
            quienes.append(set())
    visible = [bool(q) for q in quienes]

    # --- escenas -----------------------------------------------------------------------------------------------------
    EV, avisos, html_esc, js_esc = [], [], [], []
    for i, e in enumerate(escenas):
        if e["tipo"] == "dialogo" or len(quienes[i]) != 1:
            W, left = 984, 48
        else:
            W, left = (648, 384) if LADO[next(iter(quienes[i]))] == "izq" else (648, 48)   # el contenido se pone en el lado contrario al avatar
        ctx = Ctx(i, t0s[i], t1s[i], inicio[ks[i]], fin[ks[i]], PAL[ks[i]], W, AREA_H, p)
        ctx.proyecto = proyecto
        h, js = ESCENAS[e["tipo"]][0](ctx, dict(e, _habla=habla[i], _lado=LADO[habla[i]]))
        sid = f"S{i}"
        html_esc.append(f'<div class="scene clip" id="{sid}" data-start="{t0s[i]}" data-duration="{round(t1s[i] - t0s[i], 2)}" data-track-index="1" style="left:{left}px;width:{W}px">{h}</div>')
        js_esc.append(fromTo(f"#{sid}", {"opacity": 0}, {"opacity": 1, "duration": .05 if i == 0 else .12}, t0s[i]))
        if cfg_ritmo["zoom_escena"]:                      # empuje de cámara muy lento: nada se queda quieto
            js_esc.append(fromTo(f"#{sid}", {"scale": 1}, {"scale": round(1 + cfg_ritmo["zoom_escena"], 4), "duration": round(t1s[i] - t0s[i], 2), "ease": "none"}, t0s[i]))
        js_esc += js
        if i < n - 1:
            js_esc.append(to(f"#{sid}", {"opacity": 0, "duration": .15}, t1s[i] - .15))
        EV += ctx.ev
        avisos += ctx.avisos
        EV.append((0.1 if i == 0 else t0s[i], f"whoosh:{i % 3}", .4 if i == 0 else .45))

    # --- subtítulos palabra a palabra ------------------------------------------------------------------------------
    sub_html, sub_js, nch = [], [], 0
    rc = sb.get("subs") == "recuadro"           # estilo opcional de subtítulos (por defecto: palabra activa subrayada)
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
            sub_html.append(f'<div class="sub clip{" rc" if rc else ""}" id="c{nch}" data-start="{a}" data-duration="{round(b - a, 2)}" data-track-index="6">{spans}</div>')
            sub_js.append(fromTo(f"#c{nch}", {"opacity": 0, "y": 16, "scale": .97}, {"opacity": 1, "y": 0, "scale": 1, "duration": .14, "ease": "power3.out"}, a))
            EV.append((a, "tick", 0.16))
            for j, i in enumerate(g):
                t0 = round(inicio[k] + ws[i]["ini"], 3)
                t1 = round(inicio[k] + ws[g[j + 1]]["ini"], 3) if j + 1 < len(g) else round(inicio[k] + ws[i]["fin"] + 0.05, 3)
                if rc:                          # recuadro: la palabra activa va en un cuadro de color con letra oscura
                    sub_js.append(f'tl.set("#w{nch}_{j}",{{opacity:1,color:"#0B1020",backgroundColor:"{p["resalte"]}"}},{t0});'
                                  f'tl.set("#w{nch}_{j}",{{color:"{p["text"]}",backgroundColor:"rgba(0,0,0,0)"}},{t1});')
                    continue
                sub_js.append(f'tl.set("#w{nch}_{j}",{{opacity:1,color:"{p["resalte"]}"}},{t0});tl.fromTo("#u{nch}_{j}",{{scaleX:0}},{{scaleX:1,duration:.14,ease:"power2.out"}},{t0});'
                              f'tl.set("#w{nch}_{j}",{{color:"{p["text"]}"}},{t1});tl.set("#u{nch}_{j}",{{opacity:0}},{t1});')
            nch += 1

    # --- avatares: entran/salen, boca con la voz de quien habla, parpadeo, brazo ---------------------------------------------
    prof_js = []
    for av in LISTA_AVATARES:
        vis = [av in q for q in quienes]
        if not any(vis):
            continue
        tramos, cur = [], None
        for i in range(n):
            if vis[i]:
                cur = [i, i] if cur is None else [cur[0], i]
            elif cur:
                tramos.append(tuple(cur)); cur = None
        if cur:
            tramos.append(tuple(cur))
        pref, sel = PREF[av], f"#av_{av}"
        signo = -1 if LADO[av] == "izq" else 1
        prof_js.append(f'tl.set("{sel}",{{opacity:0,x:{signo * 430}}},0);')
        if LADO[av] == "der":
            prof_js.append(f'tl.set("#flip_{av}",{{scaleX:-1}},0);')            # espejo: levanta el brazo contrario
        parp = []
        for a, b in tramos:
            ta = 0.05 if a == 0 else round(t0s[a], 2)
            tf = TOTAL if b == n - 1 else round(t1s[b], 2)
            baja = lambda i: BAJADA_DIALOGO if escenas[i]["tipo"] == "dialogo" else 0
            prof_js.append(f'tl.set("{sel}",{{y:{baja(a)}}},{round(max(ta - .01, 0), 2)});')
            prof_js.append(f'tl.to("{sel}",{{opacity:1,x:0,duration:.55,ease:"power3.out"}},{ta});')
            EV.append((ta, "swipe", .4))
            for i in range(a + 1, b + 1):
                if baja(i) != baja(i - 1):
                    prof_js.append(f'tl.to("{sel}",{{y:{baja(i)},duration:.5,ease:"power2.inOut"}},{round(t0s[i], 2)});')
            if b != n - 1:
                prof_js.append(f'tl.to("{sel}",{{opacity:0,x:{signo * 430},duration:.45,ease:"power2.in"}},{round(tf - .45, 2)});')
                EV.append((round(tf - .45, 2), "swipe", .3))
            tb = max(ta + 1.0, 1.6) + (0.9 if av == "rubio" else 0)       # parpadean a destiempo
            while tb < tf - 0.4:
                parp.append(f'tl.set("#{pref}parpados",{{opacity:1}},{round(tb, 2)});tl.set("#{pref}parpados",{{opacity:0}},{round(tb + 0.13, 2)});')
                tb += 3.3
        prof_js.append(f'tl.fromTo("#flip_{av}",{{y:0}},{{y:-5,duration:.9,ease:"sine.inOut",yoyo:true,repeat:{int(TOTAL / 0.9)}}},0);')
        actual = 0
        for i, k in enumerate(ks):
            if not vis[i] or habla[i] != av:                                   # solo mueve la boca y gesticula el que habla
                continue
            for fr, e_ in enumerate(_estados_boca(voz / f"{k}.wav")):
                if e_ != actual:
                    tt = round(inicio[k] + fr / 30, 3)
                    prof_js.append(f'tl.set("#{pref}boca_cerrada",{{opacity:{1 if e_ == 0 else 0}}},{tt});tl.set("#{pref}boca_media",{{opacity:{1 if e_ == 1 else 0}}},{tt});tl.set("#{pref}boca_abierta",{{opacity:{1 if e_ == 2 else 0}}},{tt});')
                    actual = e_
            if actual != 0:
                cc = round(fin[k] + 0.02, 3)
                prof_js.append(f'tl.set("#{pref}boca_cerrada",{{opacity:1}},{cc});tl.set("#{pref}boca_media",{{opacity:0}},{cc});tl.set("#{pref}boca_abierta",{{opacity:0}},{cc});')
                actual = 0
            if cfg_ritmo["pulso_avatar"]:                                      # pequeño pulso al empezar a hablar
                sx = -1 if LADO[av] == "der" else 1
                prof_js.append(f'tl.to("#flip_{av}",{{scaleX:{round(sx * (1 + cfg_ritmo["pulso_avatar"]), 4)},scaleY:{round(1 + cfg_ritmo["pulso_avatar"], 4)},duration:.16,yoyo:true,repeat:1,ease:"power2.out"}},{round(inicio[k], 2)});')
            ang = ANGULO[i % len(ANGULO)]
            prof_js.append(f'tl.to("#{pref}brazo_d",{{rotation:{ang},svgOrigin:"274 286",duration:.55,ease:"power2.inOut"}},{round(inicio[k] - 0.05, 2)});'
                           f'tl.to("#{pref}brazo_d",{{rotation:{ang + 5},svgOrigin:"274 286",duration:.45,ease:"sine.inOut",yoyo:true,repeat:{max(1, int(DUR[k]["segundos"] / 0.9))}}},{round(inicio[k] + 0.6, 2)});')
        prof_js += parp

    # --- cierre y sonidos -------------------------------------------------------------------------------------------
    (proyecto / "assets").mkdir(parents=True, exist_ok=True)
    for f in (RAIZ / "marca").iterdir():
        shutil.copy(f, proyecto / "assets" / f.name)
    n_ef, pico = mezclar(EV, TOTAL, str(proyecto / "assets" / "sfx_mix.wav"))

    audio = "\n".join(f'<audio id="a{k}" src="assets/voz/{k}.wav" data-start="{inicio[k]}" data-duration="{DUR[k]["segundos"]}" data-volume="1"></audio>' for k in ks)
    audio += f'\n<audio id="asfx" src="assets/sfx_mix.wav" data-start="0" data-duration="{TOTAL}" data-volume="0.6"></audio>'
    cfg_audio = config_audio()
    if cfg_audio["musica"]["activa"]:                       # fondo musical propio, siempre por debajo de la voz
        rms = []
        for k in ks:
            v, _ = sf.read(voz / f"{k}.wav", dtype="float32")
            v = v if v.ndim == 1 else v.mean(axis=1)
            act = v[np.abs(v) > 0.01]
            if len(act):
                rms.append(float(np.sqrt(np.mean(act ** 2))))
        musica.generar(str(proyecto / "assets" / "musica.wav"), TOTAL, sb["tema"], float(np.mean(rms)) if rms else 0.07, cfg_audio["musica"]["nivel_db"])
        audio += f'\n<audio id="amus" src="assets/musica.wav" data-start="0" data-duration="{TOTAL}" data-volume="1"></audio>'
    etiqueta = sb.get("etiqueta") or p["etiqueta"]
    pie = "Contenido educativo, no es asesoramiento financiero" + ("<br/>Gráficos ilustrativos, sin datos reales" if sb["ilustrativo"] else "")
    vars_ = ";".join(f"--{k}:{p[k]}" for k in ("bg", "surface", "raised", "text", "muted", "border", "up", "down", "warn", "acc", "acc2", "resalte"))
    css = CSS.replace("%%VARS%%", vars_).replace("%%GLOW1%%", rgb(p["acc"], .12)).replace("%%GLOW2%%", rgb(p["acc2"], .13)).replace("%%TOP%%", str(AREA_TOP)).replace("%%AH%%", str(AREA_H))

    body = (f'<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">\n'
            f'<div id="grid"></div>\n' + HUD_HTML + f'<div id="top"><img src="assets/isotipo.png" alt="WhaleXtreet" /><div id="pill">{etiqueta}</div></div>\n'
            + ("\n".join(sub_html)) + "\n" + ("\n".join(html_esc)) + "\n"
            + "".join(f'<div id="av_{av}" class="av {LADO[av]}"><div id="flip_{av}">{_svg_avatar(av)}</div></div>\n' for av in LISTA_AVATARES if any(av in q for q in quienes))
            + f'<div id="foot">{pie}</div>\n'
            f'<div id="flash"></div>\n{audio}\n</div>')

    js = ("const fm=(v,d)=>{const neg=v<0;let s=Math.abs(v).toFixed(d);let [a,b]=s.split('.');a=a.replace(/\\B(?=(\\d{3})+(?!\\d))/g,'.');return (neg?'-':'')+(b?a+','+b:a)};\n"
          "const tl = gsap.timeline({ paused: true });\n"
          f'tl.fromTo("#grid",{{y:0}},{{y:-72,duration:{TOTAL},ease:"none"}},0);\n'
          + HUD_JS.replace("%%TOTAL%%", str(TOTAL)) +
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
