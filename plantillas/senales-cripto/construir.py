"""Vídeo «Dos señales de alarma» (1080x1920) con el profesor de WhaleXtreet y la voz D.
Se ejecuta con el Python de qwen3tts (necesita numpy y soundfile). Lee las duraciones reales de la voz,
calcula el volumen de cada audio para mover la boca y escribe index.html.
Los gráficos son ilustrativos: este vídeo no usa datos de mercado."""
import json, re, shutil
from pathlib import Path
import numpy as np, soundfile as sf

AQUI = Path(__file__).parent
DUR = json.loads((AQUI / "assets/voz/duraciones.json").read_text(encoding="utf-8"))
orden = ["l1", "l2", "l3", "l4"]

GAP, LEAD, TAIL = 0.35, 0.3, 3.4
t, inicio = LEAD, {}
for k in orden:
    inicio[k] = round(t, 2)
    t += DUR[k]["segundos"] + GAP
TOTAL = round(t - GAP + TAIL, 2)
fin = {k: round(inicio[k] + DUR[k]["segundos"], 2) for k in orden}
H = GAP / 2

# --- Personaje: el SVG exacto aprobado por el usuario (+ una boca intermedia oculta para hablar) ---
shutil.copy(AQUI.parent.parent / "profesor" / "profesor_TAL_CUAL.svg", AQUI / "assets/profesor.svg")
svg = (AQUI / "assets/profesor.svg").read_text(encoding="utf-8").strip()
marca = '<path d="M193 322 Q201 328 209 322 Q201 318 193 322Z" fill="#E36F78"/></g>'
assert marca in svg
svg = svg.replace(marca, marca + '<g id="boca_media" opacity="0"><path d="M184 309 Q201 328 218 309 Q201 316 184 309Z" fill="#6E1F27"/>'
                  '<path d="M188 310 Q201 318 214 310 L214 312 Q201 320 188 312Z" fill="#FFFFFF"/></g>', 1)


def estados(k):
    """Estado de la boca en cada fotograma (30 fps): 0 cerrada, 1 media, 2 abierta, según el volumen de la voz."""
    x, sr = sf.read(AQUI / f"assets/voz/{k}.wav")
    if x.ndim > 1:
        x = x.mean(axis=1)
    hop = int(sr / 30)
    rms = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop + 1, hop)])
    ref = np.percentile(rms, 90) or 1.0
    st = [0 if r < 0.16 * ref else (1 if r < 0.5 * ref else 2) for r in rms]
    for i in range(1, len(st) - 1):          # sin parpadeos de un solo fotograma
        if st[i - 1] == st[i + 1] != st[i]:
            st[i] = st[i - 1]
    return st


boca_js = []
actual = 0
for k in orden:
    st = estados(k)
    for i, e in enumerate(st):
        if e != actual:
            tt = round(inicio[k] + i / 30, 3)
            boca_js.append(f'tl.set("#boca_cerrada",{{opacity:{1 if e == 0 else 0}}},{tt});'
                           f'tl.set("#boca_media",{{opacity:{1 if e == 1 else 0}}},{tt});'
                           f'tl.set("#boca_abierta",{{opacity:{1 if e == 2 else 0}}},{tt});')
            actual = e
    cierre = round(fin[k] + 0.02, 3)
    if actual != 0:
        boca_js.append(f'tl.set("#boca_cerrada",{{opacity:1}},{cierre});tl.set("#boca_media",{{opacity:0}},{cierre});tl.set("#boca_abierta",{{opacity:0}},{cierre});')
        actual = 0
boca_js = "\n".join(boca_js)


# --- Subtítulos: trozos de ≤ 22 caracteres y ≤ 5 palabras, con el tiempo repartido por caracteres ---
def trozos(k):
    palabras = re.sub(r"\s+", " ", DUR[k]["texto"]).split(" ")
    grupos, cur = [], []
    for p in palabras:
        cur.append(p)
        if len(cur) >= 5 or len(" ".join(cur)) >= 22 or (re.search(r"[.:?!]$", p) and len(cur) >= 3):
            grupos.append(" ".join(cur)); cur = []
    if cur:
        grupos.append(" ".join(cur))
    total = sum(len(g) for g in grupos)
    out, a = [], inicio[k]
    for g in grupos:
        d = DUR[k]["segundos"] * len(g) / total
        out.append((g, round(a, 2), round(a + d, 2)))
        a += d
    return out


subs = [x for k in orden for x in trozos(k)]
subs_html = "\n".join(f'<div class="sub clip" id="sub{i}" data-start="{a}" data-duration="{round(b - a, 2)}" data-track-index="5">{txt}</div>'
                      for i, (txt, a, b) in enumerate(subs))
subs_js = "\n".join(f'tl.fromTo("#sub{i}",{{opacity:0,y:18,scale:.97}},{{opacity:1,y:0,scale:1,duration:.16,ease:"power3.out"}},{a});'
                    for i, (txt, a, b) in enumerate(subs))
audio_html = "\n".join(f'<audio id="a{k}" src="assets/voz/{k}.wav" data-start="{inicio[k]}" data-duration="{DUR[k]["segundos"]}" data-volume="1"></audio>' for k in orden)

BRAZO = {"l1": 0, "l2": 16, "l3": 24, "l4": 6}
brazo_js = "\n".join(
    f'tl.to("#brazo_d",{{rotation:{BRAZO[k]},svgOrigin:"274 286",duration:.55,ease:"power2.inOut"}},{inicio[k] - 0.05});'
    f'tl.to("#brazo_d",{{rotation:{BRAZO[k] + 5},svgOrigin:"274 286",duration:.45,ease:"sine.inOut",yoyo:true,repeat:{max(1, int(DUR[k]["segundos"] / 0.9))}}},{inicio[k] + 0.6});'
    for k in orden)

# parpadeos cada ~3,3 s
parp = []
tb = 1.6
while tb < TOTAL - 0.5:
    parp.append(f'tl.set("#parpados",{{opacity:1}},{round(tb, 2)});tl.set("#parpados",{{opacity:0}},{round(tb + 0.13, 2)});')
    tb += 3.3
parp_js = "\n".join(parp)

# partición de la escena 3 en dos fases (tokens concentrados / desbloqueos)
t3a = round(inicio["l3"] + DUR["l3"]["segundos"] * 0.46, 2)

FLAG = ('<svg viewBox="0 0 64 64" width="%d" height="%d"><path d="M14 6 V58" stroke="#B2BED1" stroke-width="6" stroke-linecap="round"/>'
        '<path d="M17 8 H52 L43 21 L52 34 H17Z" fill="#FF7A7A"/></svg>')

CSS = """
@font-face { font-family:"InterW"; src:url("assets/fonts/Inter-Bold.otf"); font-weight:700; }
@font-face { font-family:"InterW"; src:url("assets/fonts/Inter-SemiBold.otf"); font-weight:600; }
@font-face { font-family:"PlexW"; src:url("assets/fonts/IBMPlexMono-Bold.ttf"); font-weight:700; }
:root { --bg:#0B1020; --surface:#121A2B; --raised:#1B263B; --text:#F4F7FC; --muted:#B2BED1; --border:#35435B;
  --brand:#A5B4FC; --accent:#67D4E8; --warn:#F2C879; --down:#FF7A7A; }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:var(--bg); }
#root { position:relative; width:1080px; height:1920px; overflow:hidden; font-family:"InterW",sans-serif; color:var(--text);
  background: radial-gradient(900px 700px at 80% 12%, rgba(103,212,232,.14), transparent 60%),
              radial-gradient(900px 800px at 10% 70%, rgba(165,180,252,.12), transparent 60%), var(--bg); }
#grid { position:absolute; inset:-80px; opacity:.5; background-image: linear-gradient(rgba(178,190,209,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(178,190,209,.07) 1px, transparent 1px); background-size:72px 72px; }
.mono { font-family:"PlexW",monospace; font-weight:700; }
#top { position:absolute; left:64px; right:64px; top:150px; display:flex; align-items:center; justify-content:space-between; z-index:20; }
#top img { height:54px; }
#pill { font-family:"PlexW",monospace; font-weight:700; font-size:28px; letter-spacing:.14em; color:var(--down); border:2px solid rgba(255,122,122,.5); padding:10px 22px; border-radius:999px; }
#prof { position:absolute; left:-6px; top:566px; width:366px; height:640px; z-index:15; }
#prof svg { width:366px; height:640px; display:block; overflow:visible; }
.scene { position:absolute; left:384px; right:40px; top:250px; height:900px; }
.chip { display:inline-block; font-family:"PlexW",monospace; font-weight:700; font-size:34px; letter-spacing:.12em; padding:12px 28px; border-radius:999px; background:rgba(255,122,122,.14); color:var(--down); border:2px solid rgba(255,122,122,.5); }
.cap { font-family:"PlexW",monospace; font-weight:700; font-size:28px; letter-spacing:.1em; color:var(--muted); }
.big { font-weight:700; letter-spacing:-.03em; line-height:1.02; }
.sub { position:absolute; left:64px; right:64px; top:1214px; height:200px; display:flex; align-items:center; justify-content:center; text-align:center; font-weight:700; font-size:70px; line-height:1.1; letter-spacing:-.02em; z-index:30; text-shadow:0 4px 30px rgba(0,0,0,.65); }
#foot { position:absolute; left:40px; right:40px; top:1436px; font-family:"PlexW",monospace; font-size:28px; line-height:1.35; color:rgba(178,190,209,.8); text-align:center; z-index:20; }
/* escena 1 */
#n2 { font-weight:700; font-size:380px; letter-spacing:-.05em; line-height:1; color:var(--down); margin-top:40px; }
#t1 { font-weight:700; font-size:64px; letter-spacing:-.02em; line-height:1.05; }
#fl { display:flex; gap:26px; margin-top:34px; }
/* tarjetas */
.card { background:var(--surface); border:2px solid var(--border); border-radius:40px; padding:36px 34px; }
.tit { font-weight:700; font-size:70px; letter-spacing:-.03em; line-height:1.04; margin-top:22px; }
.li { display:flex; align-items:center; gap:18px; font-weight:600; font-size:42px; margin-top:22px; color:var(--text); }
.x { width:46px; height:46px; flex:none; border-radius:50%; background:rgba(255,122,122,.18); border:2px solid var(--down); display:flex; align-items:center; justify-content:center; color:var(--down); font-weight:700; font-size:30px; }
.nota { font-weight:600; font-size:40px; color:var(--muted); margin-top:26px; line-height:1.2; }
/* opciones */
.opt { display:flex; align-items:center; gap:24px; background:var(--surface); border:2px solid var(--border); border-radius:34px; padding:26px 28px; margin-top:28px; font-weight:700; font-size:46px; line-height:1.08; }
.opt b { flex:none; width:96px; height:96px; border-radius:50%; background:var(--accent); color:#0B1020; display:flex; align-items:center; justify-content:center; font-size:56px; }
.opt.o2 b { background:var(--brand); }
#s5 { display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }
#logo5 { width:420px; }
#nom5 { font-weight:700; font-size:84px; letter-spacing:-.03em; margin-top:34px; }
#tag5 { font-weight:600; font-size:48px; color:var(--accent); margin-top:14px; }
"""

HTML_BODY = """
<div id="root" data-composition-id="main" data-start="0" data-duration="%%TOTAL%%" data-width="1080" data-height="1920">
  <div id="grid"></div>
  <div id="top"><img src="assets/isotipo.png" alt="WhaleXtreet" /><div id="pill">ALERTA CRIPTO</div></div>
  <div id="prof">%%SVG%%</div>

  <div class="scene clip" id="s1" data-start="0" data-duration="%%S1%%" data-track-index="1">
    <div class="cap" id="k1">ANTES DE MIRAR UN PROYECTO CRIPTO PEQUEÑO</div>
    <div id="n2">2</div>
    <div id="t1">SEÑALES DE ALARMA</div>
    <div id="fl"><div id="f1">%%FLAG%%</div><div id="f2">%%FLAG%%</div></div>
  </div>

  <div class="scene clip" id="s2" data-start="%%S2A%%" data-duration="%%S2D%%" data-track-index="1">
    <div class="card" id="c2">
      <span class="chip" id="chip2">SEÑAL 1</span>
      <div style="text-align:center;margin-top:18px">
        <svg viewBox="0 0 300 250" width="320" height="266" id="ico2"><circle cx="150" cy="96" r="62" fill="#1B263B" stroke="#35435B" stroke-width="5"/>
          <path d="M40 250 Q44 178 150 170 Q256 178 260 250Z" fill="#1B263B" stroke="#35435B" stroke-width="5"/>
          <text x="150" y="124" text-anchor="middle" font-family="InterW" font-weight="700" font-size="104" fill="#FF7A7A">?</text></svg>
      </div>
      <div class="tit" id="tit2">Equipo anónimo</div>
      <div class="li" id="li2"><span class="x">✕</span>Sin historial verificable</div>
      <div class="nota" id="nota2">Si nadie responde, la responsabilidad desaparece.</div>
    </div>
  </div>

  <div class="scene clip" id="s3" data-start="%%S3A%%" data-duration="%%S3D%%" data-track-index="1">
    <div class="card" id="c3a" style="position:absolute;left:0;right:0;top:0">
      <span class="chip">SEÑAL 2</span>
      <div class="tit" style="font-size:64px">Tokens en pocas manos</div>
      <div style="text-align:center;margin-top:10px">
        <svg viewBox="0 0 400 400" width="420" height="420"><circle cx="200" cy="200" r="140" fill="none" stroke="#A5B4FC" stroke-width="58" opacity=".55"/>
          <circle id="don" cx="200" cy="200" r="140" fill="none" stroke="#FF7A7A" stroke-width="58" stroke-dasharray="0 880" transform="rotate(-90 200 200)"/></svg>
      </div>
      <div class="nota" style="text-align:center;margin-top:0">Casi todo, en pocas direcciones</div>
      <div class="cap" style="text-align:center;margin-top:14px">GRÁFICO ILUSTRATIVO</div>
    </div>
    <div class="card" id="c3b" style="position:absolute;left:0;right:0;top:0;opacity:0">
      <span class="chip">SEÑAL 2</span>
      <div class="tit" style="font-size:64px">Desbloqueos masivos</div>
      <svg viewBox="0 0 560 330" width="580" height="342" style="margin-top:12px">
        <path d="M20 300 H540" stroke="#35435B" stroke-width="4"/>
        <rect class="bb" x="30" y="268" width="56" height="32" rx="8" fill="#A5B4FC" opacity=".6"/><rect class="bb" x="108" y="262" width="56" height="38" rx="8" fill="#A5B4FC" opacity=".6"/>
        <rect class="bb" x="186" y="256" width="56" height="44" rx="8" fill="#A5B4FC" opacity=".6"/><rect class="bb" x="264" y="250" width="56" height="50" rx="8" fill="#A5B4FC" opacity=".6"/>
        <rect id="bg1" x="352" y="300" width="66" height="0" rx="8" fill="#FF7A7A"/><rect id="bg2" x="436" y="300" width="66" height="0" rx="8" fill="#FF7A7A"/>
      </svg>
      <div class="nota" style="text-align:center;margin-top:6px">Oferta de golpe en el mercado</div>
      <div class="cap" style="text-align:center;margin-top:14px">GRÁFICO ILUSTRATIVO</div>
    </div>
  </div>

  <div class="scene clip" id="s4" data-start="%%S4A%%" data-duration="%%S4D%%" data-track-index="1">
    <span class="chip" id="chip4">RIESGO MUY ALTO</span>
    <div class="big" id="q4" style="font-size:78px;margin-top:26px">¿Qué te frena más?</div>
    <div class="opt" id="oa"><b>A</b>Anonimato del equipo</div>
    <div class="opt o2" id="ob"><b>B</b>Desbloqueos de oferta</div>
    <div class="cap" id="r4" style="margin-top:32px">RESPONDE A O B</div>
  </div>

  <div class="scene clip" id="s5" data-start="%%S5A%%" data-duration="%%S5D%%" data-track-index="1">
    <img id="logo5" src="assets/isotipo-cierre.png" alt="" />
    <div id="nom5">WhaleXtreet</div>
    <div id="tag5">El mercado, con contexto.</div>
  </div>

  %%SUBS%%
  <div id="foot">Información, no asesoramiento financiero<br/>Gráficos ilustrativos, sin datos reales</div>
  %%AUDIO%%
</div>
"""

JS = """
const tl = gsap.timeline({ paused: true });
tl.fromTo("#grid", { y:0 }, { y:-72, duration:%%TOTAL%%, ease:"none" }, 0);
tl.fromTo("#top", { opacity:0, y:-20 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, .05);
tl.fromTo("#prof", { y:0 }, { y:-5, duration:.9, ease:"sine.inOut", yoyo:true, repeat:%%BOB%% }, 0);
tl.fromTo("#prof", { rotation:-.6, transformOrigin:"50% 100%" }, { rotation:.6, duration:1.7, ease:"sine.inOut", yoyo:true, repeat:%%SWAY%% }, 0);

// 1 · gancho
tl.set("#n2", { opacity:1 }, 0);
tl.fromTo("#n2", { scale:.6 }, { scale:1, duration:.7, ease:"back.out(2)" }, .1);
tl.fromTo("#t1", { opacity:0, y:30 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, .6);
tl.fromTo("#f1", { opacity:0, scale:.5 }, { opacity:1, scale:1, duration:.45, ease:"back.out(2.4)" }, 1.1);
tl.fromTo("#f2", { opacity:0, scale:.5 }, { opacity:1, scale:1, duration:.45, ease:"back.out(2.4)" }, 1.4);
tl.to("#s1", { opacity:0, duration:.25 }, %%S1OUT%%);

// 2 · equipo anónimo
const s2 = %%S2A%%;
tl.fromTo("#s2", { opacity:0 }, { opacity:1, duration:.2 }, s2);
tl.fromTo("#c2", { opacity:0, y:60, scale:.96 }, { opacity:1, y:0, scale:1, duration:.6, ease:"power3.out" }, s2);
tl.fromTo("#ico2", { opacity:0, scale:.6 }, { opacity:1, scale:1, duration:.6, ease:"back.out(2)" }, s2 + .35);
tl.fromTo("#tit2", { opacity:0, y:24 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, s2 + 1.0);
tl.fromTo("#li2", { opacity:0, x:-30 }, { opacity:1, x:0, duration:.5, ease:"power3.out" }, s2 + 2.4);
tl.fromTo("#nota2", { opacity:0, y:20 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, s2 + %%N2T%%);
tl.to("#s2", { opacity:0, duration:.25 }, %%S2OUT%%);

// 3 · concentración y desbloqueos
const s3 = %%S3A%%, s3b = %%T3A%%;
tl.fromTo("#s3", { opacity:0 }, { opacity:1, duration:.2 }, s3);
tl.fromTo("#c3a", { opacity:0, y:60, scale:.96 }, { opacity:1, y:0, scale:1, duration:.6, ease:"power3.out" }, s3);
tl.to("#don", { attr:{ "stroke-dasharray":"640 880" }, duration:1.6, ease:"power3.out" }, s3 + .7);
tl.to("#c3a", { opacity:0, y:-30, duration:.3 }, s3b - .2);
tl.fromTo("#c3b", { opacity:0, y:50 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, s3b);
tl.to("#bg1", { attr:{ y:70, height:230 }, duration:.7, ease:"power3.out" }, s3b + 1.4);
tl.to("#bg2", { attr:{ y:100, height:200 }, duration:.7, ease:"power3.out" }, s3b + 1.6);
tl.to("#s3", { opacity:0, duration:.25 }, %%S3OUT%%);

// 4 · pregunta
const s4 = %%S4A%%;
tl.fromTo("#s4", { opacity:0 }, { opacity:1, duration:.2 }, s4);
tl.fromTo("#chip4", { opacity:0, scale:.7 }, { opacity:1, scale:1, duration:.5, ease:"back.out(2)" }, s4 + .1);
tl.fromTo("#q4", { opacity:0, y:30 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, s4 + %%Q4T%%);
tl.fromTo("#oa", { opacity:0, x:60 }, { opacity:1, x:0, duration:.5, ease:"power3.out" }, s4 + %%OAT%%);
tl.fromTo("#ob", { opacity:0, x:60 }, { opacity:1, x:0, duration:.5, ease:"power3.out" }, s4 + %%OBT%%);
tl.fromTo("#r4", { opacity:0 }, { opacity:1, duration:.4 }, s4 + %%OBT%% + .8);
tl.to("#s4", { opacity:0, duration:.3 }, %%S4OUT%%);

// 5 · cierre
const s5 = %%S5A%%;
tl.fromTo("#s5", { opacity:0 }, { opacity:1, duration:.3 }, s5);
tl.fromTo("#logo5", { opacity:0, scale:.8 }, { opacity:1, scale:1, duration:.7, ease:"back.out(1.8)" }, s5 + .1);
tl.fromTo("#nom5", { opacity:0, y:30 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, s5 + .5);
tl.fromTo("#tag5", { opacity:0, y:24 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, s5 + .9);

// profesor: boca con la voz, parpadeo y brazo
%%BOCA%%
%%PARP%%
%%BRAZO%%
%%SUBSJS%%
window.__timelines["main"] = tl;
tl.seek(0);
"""

s2a, s3a, s4a = [round(inicio[k] - H, 2) for k in ("l2", "l3", "l4")]
s5a = round(fin["l4"] + H, 2)
rep = {
    "%%TOTAL%%": str(TOTAL), "%%SVG%%": svg, "%%FLAG%%": FLAG % (110, 110),
    "%%S1%%": str(round(fin["l1"] + H, 2)), "%%S1OUT%%": str(round(fin["l1"] + H - .25, 2)),
    "%%S2A%%": str(s2a), "%%S2D%%": str(round(fin["l2"] - inicio["l2"] + GAP, 2)), "%%S2OUT%%": str(round(fin["l2"] + H - .25, 2)),
    "%%N2T%%": str(round(max(3.4, DUR["l2"]["segundos"] * 0.62), 2)),
    "%%S3A%%": str(s3a), "%%S3D%%": str(round(fin["l3"] - inicio["l3"] + GAP, 2)), "%%S3OUT%%": str(round(fin["l3"] + H - .25, 2)), "%%T3A%%": str(t3a),
    "%%S4A%%": str(s4a), "%%S4D%%": str(round(fin["l4"] - inicio["l4"] + GAP, 2)), "%%S4OUT%%": str(round(fin["l4"] + H - .25, 2)),
    "%%Q4T%%": str(round(DUR["l4"]["segundos"] * 0.40, 2)), "%%OAT%%": str(round(DUR["l4"]["segundos"] * 0.62, 2)), "%%OBT%%": str(round(DUR["l4"]["segundos"] * 0.80, 2)),
    "%%S5A%%": str(s5a), "%%S5D%%": str(round(TOTAL - s5a, 2)),
    "%%BOB%%": str(int(TOTAL / 0.9)), "%%SWAY%%": str(int(TOTAL / 1.7)),
    "%%SUBS%%": subs_html, "%%AUDIO%%": audio_html, "%%BOCA%%": boca_js, "%%PARP%%": parp_js, "%%BRAZO%%": brazo_js, "%%SUBSJS%%": subs_js,
}
cuerpo, js = HTML_BODY, JS
for a, b in rep.items():
    cuerpo = cuerpo.replace(a, b)
    js = js.replace(a, b)

html = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="UTF-8" />\n<meta name="viewport" content="width=1080, height=1920" />\n'
        '<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>\n<style>' + CSS + '</style>\n</head>\n<body>\n'
        + cuerpo + '\n<script>' + js + '</script>\n</body>\n</html>\n')
(AQUI / "index.html").write_text(html, encoding="utf-8")
cambios = boca_js.count("#boca_media")
print("index.html listo · %s s · %d subtítulos · %d cambios de boca" % (TOTAL, len(subs), cambios))
