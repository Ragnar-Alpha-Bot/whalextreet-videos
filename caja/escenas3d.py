"""Escenas en 3D (Three.js, licencia MIT, incluido en marca/). Se dibujan en un <canvas> y se mueven SOLO con el tiempo del vídeo (evento hf-seek de
HyperFrames), así cada fotograma sale igual en cualquier ordenador. Tipos nuevos: «barras3d» (mismos datos que «barras») y «moneda3d».
"""
import json

from escenas import ESCENAS, _txt, es, esc, fromTo, v_barras

# --- parte común: renderizador, etiquetas de texto y puerta de tiempo ---------------------------------------------------
BASE = """
import * as THREE from "./assets/three.module.js";
await document.fonts.load('700 40px InterW');
const cv = document.getElementById("%(id)s");
const R = new THREE.WebGLRenderer({canvas: cv, antialias: true, alpha: true});
R.setPixelRatio(1); R.setSize(%(w)d, %(h)d, false);
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim() || "#ffffff";
const scene = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(36, %(w)d / %(h)d, 0.1, 100);
scene.add(new THREE.AmbientLight(0xffffff, 0.75));
const sun = new THREE.DirectionalLight(0xffffff, 2.4); sun.position.set(4, 8, 6); scene.add(sun);
const rim = new THREE.DirectionalLight(0x67D4E8, 1.1); rim.position.set(-6, 3, -4); scene.add(rim);
const ease = {out: k => 1 - Math.pow(1 - k, 3), back: k => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); }};
const clamp = (k) => Math.min(Math.max(k, 0), 1);
const billboards = [];
function texto(txt, px, color, peso = 700) {
  const ctx0 = document.createElement("canvas").getContext("2d"); ctx0.font = peso + " " + px + "px InterW";
  const w = Math.ceil(ctx0.measureText(txt).width) + 24, h = Math.ceil(px * 1.5);
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const x = c.getContext("2d"); x.font = peso + " " + px + "px InterW"; x.fillStyle = color; x.textBaseline = "middle"; x.textAlign = "center"; x.fillText(txt, w / 2, h / 2 + px * 0.04);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w / 100, h / 100), new THREE.MeshBasicMaterial({map: tex, transparent: true, depthWrite: false}));
  billboards.push(m); return m;
}
let listo = false, ultimo = window.__hfThreeTime ?? 0;
function dibujar(t) { ultimo = t; if (!listo) return; frame(t); billboards.forEach(b => { if (b.userData.mira !== false) b.quaternion.copy(cam.quaternion); }); R.render(scene, cam); }
window.addEventListener("hf-seek", e => dibujar(e.detail?.time ?? window.__hfThreeTime ?? 0));
"""
FIN = "\nlisto = true; dibujar(ultimo);\n"

BARRAS = """
const D = %(datos)s;
const n = D.items.length, sep = Math.min(1.9, 7.2 / n), alto = 4.2;
const suelo = new THREE.Mesh(new THREE.BoxGeometry(n * sep + 1.2, 0.16, 3), new THREE.MeshStandardMaterial({color: css("--raised"), roughness: .6}));
suelo.position.y = -0.08; scene.add(suelo);
const grid = new THREE.GridHelper(n * sep + 1.2, n * 2, css("--border"), css("--border")); grid.position.y = 0.01; grid.material.transparent = true; grid.material.opacity = .35; scene.add(grid);
const barras = D.items.map((x, i) => {
  const dest = i === D.dest, col = new THREE.Color(css(dest ? "--acc" : "--acc2"));
  const m = new THREE.Mesh(new THREE.BoxGeometry(sep * .58, 1, sep * .58), new THREE.MeshStandardMaterial({color: col, roughness: .3, metalness: .25, emissive: col, emissiveIntensity: dest ? .22 : .06}));
  m.position.x = (i - (n - 1) / 2) * sep; scene.add(m);
  const v = texto(x.txt, 62, dest ? css("--acc") : css("--text")); scene.add(v);
  const nom = texto(x.n, 34, css("--muted"), 600); nom.position.set(m.position.x, -0.45, 1.45); scene.add(nom);
  return {m, v, h: Math.max(x.v / D.mx, 0.04) * alto, t0: x.t};
});
function frame(t) {
  const tt = clamp((t - D.t0) / D.dur), a = -0.55 + 0.85 * ease.out(tt);
  const r = 9.6 + (n - 3) * 0.6;
  cam.position.set(Math.sin(a) * r, 4.6 - 1.2 * tt, Math.cos(a) * r); cam.lookAt(0, 1.2, 0);
  barras.forEach(b => {
    const k = ease.out(clamp((t - b.t0) / 0.9)), alt = Math.max(b.h * k, 0.001);
    b.m.scale.y = alt; b.m.position.y = alt / 2; b.v.position.set(b.m.position.x, alt + 0.55, 0.2);
    b.v.scale.setScalar(Math.max(ease.back(clamp((t - b.t0 - .45) / .4)), 0.001));
  });
}
"""

MONEDA = """
const D = %(datos)s;
cam.position.set(0, 0.4, 9.4); cam.lookAt(0, 0, 0);
const oro = new THREE.Color(css("--warn"));
function moneda(radio, simb) {
  const g = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({color: oro, roughness: .28, metalness: .55, emissive: oro, emissiveIntensity: .12});
  const cuerpo = new THREE.Mesh(new THREE.CylinderGeometry(radio, radio, radio * .17, 72), mat); cuerpo.rotation.x = Math.PI / 2; g.add(cuerpo);
  const aro = new THREE.Mesh(new THREE.TorusGeometry(radio * .93, radio * .045, 16, 72), mat); aro.position.z = radio * .085; g.add(aro);
  const aro2 = aro.clone(); aro2.position.z = -radio * .085; g.add(aro2);
  [1, -1].forEach(s => { const tx = texto(simb, 150, "#5A3E0B", 700); tx.userData.mira = false; tx.scale.setScalar(radio * .62); tx.position.z = s * (radio * .095); tx.rotation.y = s > 0 ? 0 : Math.PI; g.add(tx); });
  return g;
}
const grande = moneda(2.1, D.simbolo); grande.position.y = 0.1; scene.add(grande);
const sat = [0, 1, 2].map(i => { const m = moneda(0.62, D.simbolo.slice(0, 1)); scene.add(m); return m; });
function frame(t) {
  const k = ease.back(clamp((t - D.t0) / 0.7)), s = Math.max(k, 0.001), u = t - D.t0;
  grande.scale.setScalar(s); grande.rotation.y = u * 2.3; grande.rotation.x = Math.sin(u * 1.3) * 0.18; grande.position.y = 0.1 + Math.sin(u * 2.1) * 0.18;
  sat.forEach((m, i) => { const a = u * 1.15 + i * 2.094, e = ease.out(clamp((u - 0.3 - i * 0.18) / 0.8));
    m.position.set(Math.cos(a) * 2.9 * e, Math.sin(a * 1.4) * 1.5 * e - 0.2, Math.sin(a) * 1.8); m.scale.setScalar(Math.max(e, 0.001)); m.rotation.y = -a * 2.2; m.rotation.x = 0.4; });
}
"""


def _canvas(c, ident, alto_px):
    w, h = int(c.W), c.n(alto_px)
    return w, h, f'<canvas id="{ident}" width="{w}" height="{h}" style="display:block;width:{w}px;height:{h}px"></canvas>'


def _modulo(base, cuerpo, w, h, ident, datos):
    return '<script type="module">' + (base % {"id": ident, "w": w, "h": h}) + (cuerpo % {"datos": json.dumps(datos, ensure_ascii=False)}) + FIN + "</script>"


def e_barras3d(c, d):
    it = d["items"]
    n = len(it)
    mx = max(x["v"] for x in it) or 1
    unidad = d.get("unidad", "")
    dest = d.get("destacar", max(range(n), key=lambda k: it[k]["v"]))
    ident = f"{c.pf}cv"
    w, h, canvas = _canvas(c, ident, 800)
    datos = {"items": [], "mx": mx, "dest": dest, "t0": c.t0 + .1, "dur": c.dur}
    c.snd(c.t0 + .2, "card", .4)
    for k, x in enumerate(it):
        t = c.T(x.get("cuando"), 0.12 + 0.62 * k / max(n - 1, 1))
        datos["items"].append({"n": x["n"], "v": x["v"], "t": t, "txt": es(x["v"], 1 if x["v"] != int(x["v"]) else 0) + unidad})
        c.snd(t, "swipe", .22)
        c.snd(t + .5, f"blip:{k}", .42)
    html = (f'<div class="col" style="justify-content:center;align-items:center"><div class="lab" style="font-size:{c.px(34)};align-self:flex-start;margin-bottom:{c.px(8)}">{esc(d["titulo"])}</div>'
            f'{canvas}</div>' + _modulo(BASE, BARRAS, w, h, ident, datos))
    return html, []


def v_moneda3d(d, err):
    _txt(d, "titulo", err, 44)
    _txt(d, "simbolo", err, 4)
    _txt(d, "subtitulo", err, 60, req=False)


def e_moneda3d(c, d):
    ident = f"{c.pf}cv"
    w, h, canvas = _canvas(c, ident, 700)
    datos = {"simbolo": d["simbolo"], "t0": c.t0 + .05}
    sub = d.get("subtitulo")
    html = (f'<div class="col" style="justify-content:center;align-items:center"><div class="lab" style="font-size:{c.px(34)};align-self:flex-start">{esc(d["titulo"])}</div>{canvas}'
            + (f'<div class="h" id="{c.pf}sub" style="font-weight:700;font-size:{c.px(48)};text-align:center;color:var(--acc2);margin-top:{c.px(6)}">{esc(sub)}</div>' if sub else "")
            + '</div>' + _modulo(BASE, MONEDA, w, h, ident, datos))
    js = [fromTo(f"#{c.pf}sub", {"opacity": 0, "y": 30}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, c.t0 + .7)] if sub else []
    c.snd(c.t0 + .1, "pop", .45)
    c.snd(c.t0 + .1, "ding:2", .3)
    return html, js


ESCENAS.update({"barras3d": (e_barras3d, v_barras), "moneda3d": (e_moneda3d, v_moneda3d)})

import escenas3d_mas  # noqa: E402,F401  (donut3d, esfera3d, velas3d)
import escenas3d_nicho  # noqa: E402,F401  (animal3d: toro y oso, lingotes3d, linea3d, escudo3d, ciudad3d)
