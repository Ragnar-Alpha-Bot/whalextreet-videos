"""Más figuras 3D para que los vídeos no repitan siempre lo mismo: «donut3d» (tarta con volumen), «esfera3d» (globo con anillos y satélites) y
«velas3d» (velas japonesas que se levantan una a una; siempre ilustrativas). Misma base que escenas3d.py."""
from escenas import ESCENAS, _txt, es, esc, fromTo
from escenas3d import BASE, _canvas, _modulo

DONUT = """
const D = %(datos)s;
const tot = D.seg.reduce((a, x) => a + x.v, 0), Ro = 2.5, Ri = 1.3, cols = ["--acc", "--acc2", "--warn", "--down", "--up"];
const grupo = new THREE.Group(); scene.add(grupo);
let a0 = 0;
const rebanadas = D.seg.map((x, i) => {
  const a1 = a0 + x.v / tot * Math.PI * 2, gap = 0.035, sh = new THREE.Shape();
  sh.absarc(0, 0, Ro, a0 + gap, a1 - gap, false); sh.absarc(0, 0, Ri, a1 - gap, a0 + gap, true); sh.closePath();
  const g = new THREE.ExtrudeGeometry(sh, {depth: 0.9, bevelEnabled: true, bevelSize: 0.05, bevelThickness: 0.05, bevelSegments: 2, curveSegments: 40}); g.rotateX(-Math.PI / 2);
  const col = new THREE.Color(css(cols[i])), m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({color: col, roughness: .35, metalness: .2, emissive: col, emissiveIntensity: i === D.mayor ? .25 : .07}));
  grupo.add(m);
  const am = (a0 + a1) / 2, lab = texto(x.n + "  " + x.pct, 46, css(cols[i])); scene.add(lab);
  const r = {m, am, lab, t: x.t, i}; a0 = a1; return r;
});
function frame(t) {
  const u = t - D.t0, giro = Math.sin(u * 0.55) * 0.55 + u * 0.12;
  grupo.rotation.y = giro; cam.position.set(0, 9.2, 10.8); cam.lookAt(0, 0, 2.3);
  rebanadas.forEach(r => {
    const k = ease.back(clamp((t - r.t) / 0.6)), s = Math.max(k, 0.001);
    r.m.scale.set(s, s, s); r.m.position.y = (1 - clamp((t - r.t) / 0.6)) * 1.4;
    const aw = r.am + giro, e = clamp((t - r.t - 0.15) / 0.3);
    r.lab.position.set(0, 0.6, 3.9 + r.i * 0.62); r.lab.scale.setScalar(Math.max(e, 0.001));
  });
}
"""

ESFERA = """
const D = %(datos)s;
cam.position.set(0, 1.2, 10.5); cam.lookAt(0, 0, 0);
const col = new THREE.Color(css("--acc")), col2 = new THREE.Color(css("--resalte"));
const globo = new THREE.Group(); scene.add(globo);
globo.add(new THREE.Mesh(new THREE.SphereGeometry(1.92, 48, 32), new THREE.MeshStandardMaterial({color: css("--surface"), roughness: .5, metalness: .3})));
const malla = new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.IcosahedronGeometry(2.0, 2)), new THREE.LineBasicMaterial({color: col2, transparent: true, opacity: .55})); globo.add(malla);
const vert = new THREE.IcosahedronGeometry(2.02, 1).getAttribute("position");
for (let i = 0; i < vert.count; i += 3) { const p = new THREE.Mesh(new THREE.SphereGeometry(0.075, 12, 8), new THREE.MeshBasicMaterial({color: (i / 3) %% 2 ? col : col2})); p.position.set(vert.getX(i), vert.getY(i), vert.getZ(i)); globo.add(p); }
const anillos = [0, 1].map(i => { const a = new THREE.Mesh(new THREE.TorusGeometry(3.0 + i * 0.5, 0.025, 8, 120), new THREE.MeshBasicMaterial({color: i ? col2 : col})); scene.add(a); return a; });
const sats = [0, 1, 2].map(i => { const m = new THREE.Mesh(new THREE.SphereGeometry(0.17, 16, 12), new THREE.MeshStandardMaterial({color: col, emissive: col, emissiveIntensity: .6})); scene.add(m); return m; });
const sitios = [[-3.3, 2.6], [3.2, 1.4], [-3.1, -2.2], [3.3, -2.6]];
const etiquetas = D.etiquetas.map((x, i) => { const l = texto(x.txt, 42, css("--text")); l.position.set(sitios[i][0], sitios[i][1], 0.8); scene.add(l); return {l, t: x.t}; });
function frame(t) {
  const u = t - D.t0, e = ease.back(clamp(u / 0.8));
  globo.scale.setScalar(Math.max(e, 0.001)); globo.rotation.y = u * 0.5; globo.rotation.x = 0.35;
  anillos.forEach((a, i) => { a.rotation.x = 1.15 + i * 0.5; a.rotation.y = u * (0.3 + i * 0.2); a.scale.setScalar(Math.max(ease.out(clamp((u - 0.2 - i * 0.2) / 0.7)), 0.001)); });
  sats.forEach((m, i) => { const a = u * (0.9 + i * 0.25) + i * 2.1, r = 3.0 + (i %% 2) * 0.5; m.position.set(Math.cos(a) * r, Math.sin(a) * r * 0.55, Math.sin(a) * r * 0.5); });
  etiquetas.forEach(x => x.l.scale.setScalar(Math.max(ease.back(clamp((t - x.t) / 0.4)), 0.001)));
}
"""

VELAS = """
const D = %(datos)s;
let semilla = 7; const azar = () => { semilla = (semilla + 0x6D2B79F5) | 0; let z = Math.imul(semilla ^ (semilla >>> 15), 1 | semilla); z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z; return ((z ^ (z >>> 14)) >>> 0) / 4294967296; };
const N = 16, deriva = D.tendencia === "alcista" ? 0.22 : D.tendencia === "bajista" ? -0.22 : 0;
let precio = 2.2; const velas = [];
for (let i = 0; i < N; i++) { const o = precio, c = Math.max(0.5, Math.min(3.8, o + deriva + (azar() - 0.5) * 1.2)), h = Math.max(o, c) + azar() * 0.45, l = Math.max(0.3, Math.min(o, c) - azar() * 0.45); velas.push({o, c, h, l}); precio = c; }
const suelo = new THREE.Mesh(new THREE.BoxGeometry(N * 0.5 + 1, 0.12, 2.4), new THREE.MeshStandardMaterial({color: css("--raised"), roughness: .6})); suelo.position.y = -0.06; scene.add(suelo);
const grid = new THREE.GridHelper(N * 0.5 + 1, N, css("--border"), css("--border")); grid.position.y = 0.01; grid.material.transparent = true; grid.material.opacity = .3; scene.add(grid);
const objs = velas.map((v, i) => {
  const sube = v.c >= v.o, col = new THREE.Color(css(sube ? "--up" : "--down")), mat = new THREE.MeshStandardMaterial({color: col, roughness: .35, metalness: .2, emissive: col, emissiveIntensity: .15});
  const g = new THREE.Group(), cuerpo = new THREE.Mesh(new THREE.BoxGeometry(0.34, 1, 0.34), mat), mecha = new THREE.Mesh(new THREE.BoxGeometry(0.06, 1, 0.06), mat);
  g.position.x = (i - (N - 1) / 2) * 0.5; g.add(cuerpo); g.add(mecha); scene.add(g); return {cuerpo, mecha, v, t: D.t0 + 0.25 + i * D.paso};
});
function frame(t) {
  const u = t - D.t0, a = -0.5 + 0.55 * ease.out(clamp(u / D.dur));
  cam.position.set(Math.sin(a) * 11.8, 3.8, Math.cos(a) * 11.8); cam.lookAt(0, 1.5, 0);
  objs.forEach(o => {
    const k = ease.out(clamp((t - o.t) / 0.35)), v = o.v, lo = Math.min(v.o, v.c), hi = Math.max(v.o, v.c), cu = Math.max((hi - lo) * k, 0.001);
    o.cuerpo.scale.y = cu; o.cuerpo.position.y = lo * k + cu / 2; const ha = Math.max((v.h - v.l) * k, 0.001); o.mecha.scale.y = ha; o.mecha.position.y = v.l * k + ha / 2;
  });
}
"""


def e_donut3d(c, d):
    seg = d["segmentos"]
    tot = sum(x["v"] for x in seg)
    ident = f"{c.pf}cv"
    w, h, canvas = _canvas(c, ident, 800)
    datos = {"seg": [], "mayor": max(range(len(seg)), key=lambda k: seg[k]["v"]), "t0": c.t0 + .1}
    c.snd(c.t0 + .2, "card", .4)
    for k, x in enumerate(seg):
        t = c.T(x.get("cuando"), 0.1 + 0.6 * k / max(len(seg) - 1, 1))
        datos["seg"].append({"n": x["n"], "v": x["v"], "t": t, "pct": es(x["v"] / tot * 100, 0) + " %"})
        c.snd(t, f"blip:{k}", .42)
    html = (f'<div class="col" style="justify-content:center;align-items:center"><div class="lab" style="font-size:{c.fs(34)};align-self:flex-start;margin-bottom:{c.px(8)}">{esc(d["titulo"])}</div>'
            f'{canvas}</div>' + _modulo(BASE, DONUT, w, h, ident, datos))
    return html, []


def v_esfera3d(d, err):
    _txt(d, "titulo", err, 44)
    _txt(d, "subtitulo", err, 60, req=False)
    et = d.get("etiquetas", [])
    if not isinstance(et, list) or len(et) > 4 or any(not isinstance(x, str) or len(x) > 18 for x in et):
        err("«etiquetas» debe ser una lista de hasta 4 textos de máx. 18 caracteres")


def e_esfera3d(c, d):
    ident = f"{c.pf}cv"
    w, h, canvas = _canvas(c, ident, 760)
    et = d.get("etiquetas", [])
    datos = {"t0": c.t0 + .05, "etiquetas": [{"txt": x, "t": c.T(None, 0.2 + 0.5 * k / max(len(et) - 1, 1))} for k, x in enumerate(et)]}
    sub = d.get("subtitulo")
    html = (f'<div class="col" style="justify-content:center;align-items:center"><div class="lab" style="font-size:{c.fs(34)};align-self:flex-start">{esc(d["titulo"])}</div>{canvas}'
            + (f'<div class="h" id="{c.pf}sub" style="font-weight:700;font-size:{c.fs(48)};text-align:center;color:var(--acc2);margin-top:{c.px(6)}">{esc(sub)}</div>' if sub else "")
            + '</div>' + _modulo(BASE, ESFERA, w, h, ident, datos))
    js = [fromTo(f"#{c.pf}sub", {"opacity": 0, "y": 30}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, c.t0 + .7)] if sub else []
    c.snd(c.t0 + .1, "whoosh", .4)
    c.snd(c.t0 + .6, "ding:2", .3)
    return html, js


def v_velas3d(d, err):
    _txt(d, "titulo", err, 44)
    if "ilustrativo" not in str(d.get("titulo", "")).lower():
        err("«velas3d» siempre es una ilustración: el título debe decir «(ilustrativo)»")
    if d.get("tendencia", "lateral") not in ("alcista", "bajista", "lateral"):
        err("«tendencia» debe ser alcista, bajista o lateral")


def e_velas3d(c, d):
    ident = f"{c.pf}cv"
    w, h, canvas = _canvas(c, ident, 760)
    paso = max(c.dur * .6 / 16, .12)
    datos = {"t0": c.t0 + .1, "dur": c.dur, "paso": round(paso, 3), "tendencia": d.get("tendencia", "lateral")}
    for k in range(0, 16, 3):
        c.snd(c.t0 + .35 + k * paso, "tick", .25)
    html = (f'<div class="col" style="justify-content:center;align-items:center"><div class="lab" style="font-size:{c.fs(34)};align-self:flex-start;margin-bottom:{c.px(8)}">{esc(d["titulo"])}</div>'
            f'{canvas}</div>' + _modulo(BASE, VELAS, w, h, ident, datos))
    return html, []


ESCENAS.update({"donut3d": (e_donut3d, ESCENAS["donut"][1]), "esfera3d": (e_esfera3d, v_esfera3d), "velas3d": (e_velas3d, v_velas3d)})
