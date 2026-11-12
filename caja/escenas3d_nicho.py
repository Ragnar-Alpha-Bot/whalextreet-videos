"""Más escenas 3D hechas a medida de nuestro nicho (Three.js, igual que escenas3d.py; se mueven solo con el tiempo del vídeo):

  · «animal3d»   un TORO (mercado alcista) o un OSO (mercado bajista) 3D galopando, con la cámara girando a su alrededor.
  · «lingotes3d» pila de lingotes de oro que cae lingote a lingote, con monedas (ahorro, patrimonio, oro, valor refugio).
  · «linea3d»    gráfico de líneas en 3D con los puntos REALES del post (cinta brillante, área y cámara que gira). Mismos datos que «grafico».
  · «escudo3d»   escudo con un visto bueno y anillos que giran (proteger el capital, stop loss, gestión del riesgo).
  · «ciudad3d»   una ciudad de rascacielos que crece mientras la cámara avanza por la avenida (economía, crecimiento, mercados). Ilustración, sin datos.

Se usan SOLO cuando el tema lo pide y como máximo una escena 3D por vídeo (cuestan tiempo de render). Ninguna escribe cifras salvo «linea3d», cuyos
valores salen de los puntos del post y pasan la comprobación de datos reales.
"""
from escenas import ESCENAS, _txt, _num, es, esc, fromTo
from escenas3d import BASE, FIN, _canvas, _modulo

# ---------------------------------------------------------------------------------------------------------------------
# TORO / OSO
# ---------------------------------------------------------------------------------------------------------------------
ANIMAL = """
const D = %(datos)s;
const toro = D.animal === "toro";
const colP = new THREE.Color(css(toro ? "--up" : "--down")); if (!toro) colP.multiplyScalar(.7).lerp(new THREE.Color("#5A3A2A"), .35);
const piel = new THREE.MeshStandardMaterial({color: colP, roughness: .5, metalness: .08, emissive: colP, emissiveIntensity: toro ? .14 : .08});
const claro = new THREE.MeshStandardMaterial({color: toro ? "#F3E9D2" : "#EAD7C0", roughness: .5});
const oscuro = new THREE.MeshStandardMaterial({color: "#12161F", roughness: .6});
const oro = new THREE.MeshStandardMaterial({color: css("--warn"), roughness: .25, metalness: .7});
const animal = new THREE.Group(); scene.add(animal);
const alto = toro ? 1.95 : 1.8;
const cuerpo = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 28), piel);
cuerpo.scale.set(toro ? 1.8 : 1.55, toro ? 1.0 : 1.18, toro ? 1.0 : 1.12); cuerpo.position.y = alto; animal.add(cuerpo);
const joroba = new THREE.Mesh(new THREE.SphereGeometry(toro ? .78 : .85, 28, 20), piel); joroba.position.set(toro ? .85 : .75, alto + (toro ? .62 : .55), 0); animal.add(joroba);
const cabeza = new THREE.Group(); cabeza.position.set(toro ? 2.3 : 2.0, alto + .1, 0); animal.add(cabeza);
const cr = new THREE.Mesh(new THREE.SphereGeometry(.72, 28, 20), piel); cr.scale.set(1.15, .95, .95); cabeza.add(cr);
const hocico = new THREE.Mesh(new THREE.SphereGeometry(toro ? .46 : .38, 24, 16), claro); hocico.position.set(toro ? .66 : .72, toro ? -.2 : -.16, 0); hocico.scale.set(toro ? 1.25 : 1.5, toro ? .85 : .8, 1); cabeza.add(hocico);
[-1, 1].forEach(s => {
  const o = new THREE.Mesh(new THREE.SphereGeometry(.09, 12, 10), oscuro); o.position.set(.42, .2, s * .38); cabeza.add(o);
  const f = new THREE.Mesh(new THREE.SphereGeometry(.06, 10, 8), oscuro); f.position.set(1.12, -.14, s * .17); cabeza.add(f);
});
if (toro) {
  [-1, 1].forEach(s => {
    const a = new THREE.Mesh(new THREE.CylinderGeometry(.09, .14, .6, 12), claro); a.position.set(-.05, .62, s * .62); a.rotation.x = s * 1.0; cabeza.add(a);
    const b = new THREE.Mesh(new THREE.ConeGeometry(.095, .72, 12), claro); b.position.set(.18, 1.02, s * .98); b.rotation.set(s * .35, 0, -.65); cabeza.add(b);
  });
  const aro = new THREE.Mesh(new THREE.TorusGeometry(.17, .035, 10, 24), oro); aro.position.set(1.13, -.42, 0); aro.rotation.y = Math.PI / 2; cabeza.add(aro);
} else {
  [-1, 1].forEach(s => { const e = new THREE.Mesh(new THREE.SphereGeometry(.34, 16, 12), piel); e.position.set(-.1, .7, s * .5); cabeza.add(e);
    const i = new THREE.Mesh(new THREE.SphereGeometry(.15, 12, 10), claro); i.position.set(.02, .7, s * .5); i.scale.set(.55, 1, 1); cabeza.add(i); });
}
const patas = [[1.0, .56, 0], [1.0, -.56, Math.PI], [-1.0, .56, Math.PI], [-1.0, -.56, 0]].map(p => {
  const g = new THREE.Group(); g.position.set(p[0] * (toro ? 1 : .92), alto - .35, p[1]); animal.add(g);
  const largo = toro ? 1.5 : 1.3, rad = toro ? .2 : .3;
  const m = new THREE.Mesh(new THREE.CylinderGeometry(rad * .85, rad, largo, 14), piel); m.position.y = -largo / 2; g.add(m);
  const pez = new THREE.Mesh(new THREE.BoxGeometry(rad * 1.7, .16, rad * 1.5), oscuro); pez.position.set(.04, -largo, 0); g.add(pez);
  return {g, fase: p[2]};
});
const cola = new THREE.Mesh(new THREE.CylinderGeometry(.05, .08, 1.1, 8), piel); cola.position.set(toro ? -1.85 : -1.5, alto + .35, 0); cola.rotation.z = .7; animal.add(cola);
const suelo = new THREE.GridHelper(60, 60, css("--acc"), css("--border")); suelo.material.transparent = true; suelo.material.opacity = .5; scene.add(suelo);
const base = new THREE.Mesh(new THREE.CircleGeometry(30, 48), new THREE.MeshStandardMaterial({color: css("--raised"), roughness: .8})); base.rotation.x = -Math.PI / 2; base.position.y = -.02; scene.add(base);
const polvo = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => { const m = new THREE.Mesh(new THREE.SphereGeometry(.32, 10, 8), new THREE.MeshBasicMaterial({color: css("--muted"), transparent: true, opacity: .3})); scene.add(m); return m; });
function frame(t) {
  const u = Math.max(t - D.t0, 0), e = ease.back(clamp(u / .8)), vel = toro ? 8.5 : 4.2, fase = u * vel;
  animal.scale.setScalar(Math.max(e, .001));
  animal.position.y = Math.abs(Math.sin(fase)) * (toro ? .16 : .09);
  animal.rotation.z = Math.sin(fase) * (toro ? .035 : .02);
  patas.forEach(p => { p.g.rotation.z = Math.sin(fase + p.fase) * (toro ? .85 : .5); });
  cabeza.rotation.z = (toro ? -.28 : -.05) + Math.sin(fase * 2) * .05;
  cola.rotation.z = .7 + Math.sin(fase * 1.5) * .35;
  suelo.position.x = -((u * (toro ? 9 : 3.4)) %% 1);
  polvo.forEach((m, i) => { const k = (u * (toro ? 1.8 : .9) + i / 10) %% 1; m.position.set(-2.4 - k * 4.4, .25 + k * .9, ((i * 7) %% 5 - 2) * .35); m.scale.setScalar(.5 + k * 1.6); m.material.opacity = (1 - k) * .3 * clamp(u / .8); });
  const a = -1.0 + .9 * ease.out(clamp(u / D.dur)) + Math.sin(u * .5) * .08;
  cam.position.set(Math.sin(a) * 11.2 + 1.0, 3.3 + Math.sin(u * .6) * .2, Math.cos(a) * 11.2); cam.lookAt(.7, 1.8, 0);
}
"""


def v_animal3d(d, err):
    _txt(d, "titulo", err, 44)
    _txt(d, "subtitulo", err, 60, req=False)
    if d.get("animal") not in ("toro", "oso"):
        err("«animal» debe ser «toro» (mercado alcista) u «oso» (mercado bajista)")


# ---------------------------------------------------------------------------------------------------------------------
# LINGOTES
# ---------------------------------------------------------------------------------------------------------------------
LINGOTES = """
const D = %(datos)s;
const oro = new THREE.Color(css("--warn"));
const mat = new THREE.MeshStandardMaterial({color: oro, roughness: .24, metalness: .75, emissive: oro, emissiveIntensity: .1});
const geo = new THREE.CylinderGeometry(.62, .8, .48, 4, 1); geo.rotateY(Math.PI / 4);
const suelo = new THREE.Mesh(new THREE.CylinderGeometry(5.2, 5.2, .2, 64), new THREE.MeshStandardMaterial({color: css("--raised"), roughness: .6, metalness: .2})); suelo.position.y = -.1; scene.add(suelo);
const anillo = new THREE.Mesh(new THREE.TorusGeometry(5.05, .04, 8, 96), new THREE.MeshBasicMaterial({color: css("--acc")})); anillo.rotation.x = Math.PI / 2; anillo.position.y = .02; scene.add(anillo);
const barras = []; let k = 0;
for (let capa = 0; capa < 4; capa++) for (let fila = 0; fila < 2; fila++) for (let i = 0; i < 4 - capa; i++) {
  const m = new THREE.Mesh(geo, mat); m.scale.set(1.3, 1, .72);
  const x = (i - (3 - capa) / 2) * 2.1, z = (fila - .5) * 1.25 + (capa %% 2 ? .0 : 0);
  barras.push({m, x, y: .24 + capa * .5, z, t: D.t0 + .25 + k * D.paso}); scene.add(m); k++;
}
const monedas = [];
for (let i = 0; i < 16; i++) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(.42, .42, .09, 28), mat), ang = i * 2.399, r = 2.9 + (i %% 5) * .4;
  monedas.push({m, x: Math.cos(ang) * r, z: Math.sin(ang) * r * .75, t: D.t0 + .8 + i * D.paso * 1.2, giro: i * .9}); scene.add(m);
}
function frame(t) {
  const u = t - D.t0, a = -.7 + 1.25 * ease.out(clamp(u / D.dur));
  cam.position.set(Math.sin(a) * 12.5, 5.6, Math.cos(a) * 12.5); cam.lookAt(0, .9, 0);
  barras.forEach(b => { const q = clamp((t - b.t) / .5), caida = (1 - ease.out(q)) * 6; b.m.visible = q > 0; b.m.position.set(b.x, b.y + caida, b.z); b.m.rotation.y = (1 - q) * .8; });
  monedas.forEach(c => { const q = clamp((t - c.t) / .55), cae = 1 - ease.out(q), asentada = q >= 1; c.m.visible = q > 0;
    c.m.position.set(c.x, .06 + (asentada ? 0 : cae * 5 + Math.abs(Math.sin(q * 9)) * .3 * (1 - q)), c.z); c.m.rotation.x = asentada ? 0 : c.giro + (1 - q) * 6; });
}
"""


def v_lingotes3d(d, err):
    _txt(d, "titulo", err, 44)
    _txt(d, "subtitulo", err, 60, req=False)


# ---------------------------------------------------------------------------------------------------------------------
# LÍNEA 3D (con datos reales)
# ---------------------------------------------------------------------------------------------------------------------
LINEA = """
const D = %(datos)s;
const n = D.pts.length, X = i => -4.6 + 9.2 * i / (n - 1), Y = v => .35 + v * 3.3, col = new THREE.Color(css(D.sube ? "--up" : "--down"));
const puntos = D.pts.map((v, i) => new THREE.Vector3(X(i), Y(v), 0));
const curva = new THREE.CatmullRomCurve3(puntos, false, "catmullrom", .15);
const SEG = Math.max(120, n * 14), RAD = 10, tubo = new THREE.TubeGeometry(curva, SEG, .11, RAD, false);
const cinta = new THREE.Mesh(tubo, new THREE.MeshStandardMaterial({color: col, roughness: .25, metalness: .2, emissive: col, emissiveIntensity: .55})); scene.add(cinta);
const forma = new THREE.Shape(); forma.moveTo(0, 0);
for (let i = 0; i < n; i++) forma.lineTo(X(i) + 4.6, Y(D.pts[i]));
forma.lineTo(9.2, 0); forma.closePath();
const area = new THREE.Mesh(new THREE.ExtrudeGeometry(forma, {depth: 1.1, bevelEnabled: false}), new THREE.MeshStandardMaterial({color: col, roughness: .5, transparent: true, opacity: .26, emissive: col, emissiveIntensity: .12}));
area.position.set(-4.6, 0, -.55); scene.add(area);
const suelo = new THREE.Mesh(new THREE.BoxGeometry(11, .14, 3.2), new THREE.MeshStandardMaterial({color: css("--raised"), roughness: .6})); suelo.position.y = -.07; scene.add(suelo);
const rej = new THREE.GridHelper(11, 11, css("--border"), css("--border")); rej.scale.z = .3; rej.position.y = .01; rej.material.transparent = true; rej.material.opacity = .35; scene.add(rej);
const pared = new THREE.GridHelper(11, 11, css("--border"), css("--border")); pared.rotation.x = Math.PI / 2; pared.position.set(0, 5.5, -1.6); pared.scale.y = .6; pared.material.transparent = true; pared.material.opacity = .22; scene.add(pared);
const cabeza = new THREE.Mesh(new THREE.SphereGeometry(.28, 20, 16), new THREE.MeshBasicMaterial({color: "#ffffff"})); scene.add(cabeza);
const luz = new THREE.PointLight(col, 18, 7); scene.add(luz);
const etFin = texto(D.txtFin, 78, css(D.sube ? "--up" : "--down")); scene.add(etFin);
const etIni = D.eti ? texto(D.eti[0], 38, css("--muted"), 600) : null, etFi2 = D.eti ? texto(D.eti[1], 38, css("--muted"), 600) : null;
if (etIni) { etIni.position.set(-4.6, -.5, 1.9); scene.add(etIni); etFi2.position.set(4.6, -.5, 1.9); scene.add(etFi2); }
function frame(t) {
  const u = t - D.t0, k = ease.out(clamp(u / D.dur2)), a = -.85 + .7 * ease.out(clamp(u / (D.dur2 + 1.2)));
  cam.position.set(Math.sin(a) * 11.5, 3.7 + (1 - k) * .6, Math.cos(a) * 11.5); cam.lookAt(0, 2.0, 0);
  const cuenta = Math.floor(k * SEG) * RAD * 6; tubo.setDrawRange(0, cuenta);
  area.scale.set(Math.max(k, .001), 1, 1);
  const p = curva.getPoint(k); cabeza.position.copy(p); luz.position.set(p.x, p.y + .6, 1.2);
  cabeza.scale.setScalar(Math.max(ease.back(clamp(u / .5)), .001));
  const e = clamp((u - D.dur2 + .1) / .4); etFin.position.set(p.x - .2, p.y + 1.0, .3); etFin.scale.setScalar(Math.max(ease.back(e), .001));
}
"""


def v_linea3d(d, err):
    _txt(d, "titulo", err, 44)
    p = d.get("puntos")
    if not isinstance(p, list) or not (2 <= len(p) <= 40) or not all(_num(x) for x in p):
        err("«puntos» debe ser una lista de 2 a 40 números")
    _txt(d, "unidad", err, 6, req=False)
    et = d.get("etiquetas")
    if et is not None and not (isinstance(et, list) and len(et) == 2 and all(isinstance(x, str) and len(x) <= 14 for x in et)):
        err("«etiquetas» debe ser una lista de 2 textos cortos (inicio y fin)")
    if d.get("anotaciones"):
        err("«linea3d» no admite «anotaciones»; usa «grafico» si las necesitas")


# ---------------------------------------------------------------------------------------------------------------------
# ESCUDO
# ---------------------------------------------------------------------------------------------------------------------
ESCUDO = """
const D = %(datos)s;
const col = new THREE.Color(css("--acc")), col2 = new THREE.Color(css("--resalte"));
const sh = new THREE.Shape();
sh.moveTo(0, 2.6); sh.bezierCurveTo(.9, 2.2, 1.6, 2.1, 2.0, 2.15); sh.lineTo(2.0, .6); sh.bezierCurveTo(2.0, -.9, .9, -1.9, 0, -2.5);
sh.bezierCurveTo(-.9, -1.9, -2.0, -.9, -2.0, .6); sh.lineTo(-2.0, 2.15); sh.bezierCurveTo(-1.6, 2.1, -.9, 2.2, 0, 2.6);
const geo = new THREE.ExtrudeGeometry(sh, {depth: .5, bevelEnabled: true, bevelSize: .14, bevelThickness: .14, bevelSegments: 5, curveSegments: 40}); geo.center();
const grupo = new THREE.Group(); scene.add(grupo);
grupo.add(new THREE.Mesh(geo, new THREE.MeshStandardMaterial({color: col, roughness: .22, metalness: .6, emissive: col, emissiveIntensity: .2})));
const dentro = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({color: css("--surface"), roughness: .5, metalness: .3})); dentro.scale.set(.8, .8, 1.15); dentro.position.z = .06; grupo.add(dentro);
const check = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([new THREE.Vector3(-.95, .05, 0), new THREE.Vector3(-.3, -.62, 0), new THREE.Vector3(1.0, .95, 0)], false, "catmullrom", 0), 30, .2, 12, false),
  new THREE.MeshStandardMaterial({color: "#ffffff", roughness: .25, emissive: "#ffffff", emissiveIntensity: .45}));
check.position.z = .62; grupo.add(check);
const anillos = [0, 1].map(i => { const a = new THREE.Mesh(new THREE.TorusGeometry(3.5 + i * .55, .035, 8, 140), new THREE.MeshBasicMaterial({color: i ? col2 : col})); scene.add(a); return a; });
const chispas = [0, 1, 2, 3, 4, 5, 6, 7].map(i => { const m = new THREE.Mesh(new THREE.SphereGeometry(.12, 12, 10), new THREE.MeshBasicMaterial({color: i %% 2 ? col : col2})); scene.add(m); return m; });
function frame(t) {
  const u = Math.max(t - D.t0, 0), e = ease.back(clamp(u / .9));
  grupo.scale.setScalar(Math.max(e, .001)); grupo.rotation.y = Math.sin(u * .9) * .55; grupo.rotation.x = Math.sin(u * .6) * .08; grupo.position.y = Math.sin(u * 1.6) * .12;
  const c = clamp((u - .5) / .5); check.scale.setScalar(Math.max(ease.back(c), .001));
  anillos.forEach((a, i) => { a.rotation.x = 1.2 + i * .45; a.rotation.y = u * (.35 + i * .2); a.scale.setScalar(Math.max(ease.out(clamp((u - .2 - i * .2) / .7)), .001)); });
  chispas.forEach((m, i) => { const ang = u * (1.1 + (i %% 3) * .2) + i * .785, r = 3.5 + (i %% 2) * .55; m.position.set(Math.cos(ang) * r, Math.sin(ang) * r * .5, Math.sin(ang) * r * .6); });
  cam.position.set(0, .4, 11.5); cam.lookAt(0, 0, 0);
}
"""


def v_escudo3d(d, err):
    _txt(d, "titulo", err, 44)
    _txt(d, "subtitulo", err, 60, req=False)


# ---------------------------------------------------------------------------------------------------------------------
# CIUDAD
# ---------------------------------------------------------------------------------------------------------------------
CIUDAD = """
const D = %(datos)s;
let semilla = 11; const azar = () => { semilla = (semilla + 0x6D2B79F5) | 0; let z = Math.imul(semilla ^ (semilla >>> 15), 1 | semilla); z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z; return ((z ^ (z >>> 14)) >>> 0) / 4294967296; };
scene.fog = new THREE.Fog(css("--bg"), 10, 34);
function ventanas(luz) {
  const c = document.createElement("canvas"); c.width = 64; c.height = 128; const x = c.getContext("2d"); x.fillStyle = "#0b0f1a"; x.fillRect(0, 0, 64, 128);
  for (let f = 0; f < 16; f++) for (let k = 0; k < 6; k++) { x.fillStyle = azar() > .45 ? luz : "#161c2c"; x.fillRect(4 + k * 10, 4 + f * 8, 6, 5); }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.magFilter = THREE.NearestFilter; return tex;
}
const texturas = [css("--acc"), css("--resalte"), "#ffe9a8"].map(ventanas);
const edificios = [];
for (let i = 0; i < 14; i++) for (const lado of [-1, 1]) {
  const alto = 2.5 + azar() * 7.5, ancho = 1.3 + azar() * .7, tex = texturas[(i + (lado > 0 ? 1 : 0)) %% 3];
  const m = new THREE.Mesh(new THREE.BoxGeometry(ancho, 1, ancho), new THREE.MeshStandardMaterial({color: "#1a2034", map: tex, emissiveMap: tex, emissive: "#ffffff", emissiveIntensity: .85, roughness: .6}));
  m.position.set(lado * (3.3 + azar() * 1.4), 0, -i * 2.5); scene.add(m); edificios.push({m, alto, t: D.t0 + .1 + i * D.paso});
}
const calle = new THREE.Mesh(new THREE.PlaneGeometry(60, 80), new THREE.MeshStandardMaterial({color: "#0c101b", roughness: .9})); calle.rotation.x = -Math.PI / 2; calle.position.set(0, 0, -30); scene.add(calle);
const lineas = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map(i => { const m = new THREE.Mesh(new THREE.BoxGeometry(.12, .02, 1.2), new THREE.MeshBasicMaterial({color: css("--acc")})); m.position.set(0, .02, -i * 3.2); scene.add(m); return m; });
const coches = [0, 1, 2, 3, 4, 5].map(i => { const m = new THREE.Mesh(new THREE.BoxGeometry(.5, .25, 1.1), new THREE.MeshBasicMaterial({color: i %% 2 ? css("--up") : css("--resalte")})); scene.add(m); return {m, x: (i %% 2 ? 1.1 : -1.1), v: 2 + i * .5, o: i * 7}; });
function frame(t) {
  const u = Math.max(t - D.t0, 0), k = ease.out(clamp(u / D.dur));
  edificios.forEach(b => { const q = ease.back(clamp((t - b.t) / .55)), h = Math.max(b.alto * q, .001); b.m.scale.y = h; b.m.position.y = h / 2; });
  const z = 7 - 22 * k;
  cam.position.set(Math.sin(u * .5) * 1.0, 2.4 + 1.4 * ease.out(clamp(u / 2.5)), z); cam.lookAt(Math.sin(u * .4) * .8, 3.2, z - 9);
  coches.forEach(c => { const zz = -((u * c.v + c.o) %% 40) + 4; c.m.position.set(c.x, .14, zz); });
  lineas.forEach((m, i) => { m.position.z = -(((i * 3.2 + u * 6) %% 38)) + 5; });
}
"""


def v_ciudad3d(d, err):
    _txt(d, "titulo", err, 44)
    _txt(d, "subtitulo", err, 60, req=False)


# ---------------------------------------------------------------------------------------------------------------------
# Escenas
# ---------------------------------------------------------------------------------------------------------------------
def _escena(c, d, cuerpo, datos, alto_px=760, derecha=None):
    ident = f"{c.pf}cv"
    w, h, canvas = _canvas(c, ident, alto_px)
    sub = d.get("subtitulo")
    cab = (f'<div style="display:flex;justify-content:space-between;align-items:baseline"><div class="lab" style="font-size:{c.fs(34)}">{esc(d["titulo"])}</div>{derecha or ""}</div>')
    html = (f'<div class="col" style="justify-content:center;align-items:center">{cab}{canvas}'
            + (f'<div class="h" id="{c.pf}sub" style="font-weight:700;font-size:{c.fs(48)};text-align:center;color:var(--acc2);margin-top:{c.px(6)}">{esc(sub)}</div>' if sub else "")
            + '</div>' + _modulo(BASE, cuerpo, w, h, ident, datos))
    js = [fromTo(f"#{c.pf}sub", {"opacity": 0, "y": 30}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, c.t0 + .8)] if sub else []
    return html, js


def e_animal3d(c, d):
    html, js = _escena(c, d, ANIMAL, {"animal": d["animal"], "t0": c.t0 + .05, "dur": c.dur})
    c.snd(c.t0 + .05, "whoosh", .45)
    c.snd(c.t0 + .6, "boom" if d["animal"] == "toro" else "impact", .35)
    for k in range(1, int(c.dur * 2)):
        c.snd(c.t0 + .9 + k * .5, "tick", .12)
    return html, js


def e_lingotes3d(c, d):
    paso = max(.16, min(.32, c.dur * .45 / 20))
    html, js = _escena(c, d, LINGOTES, {"t0": c.t0 + .05, "dur": c.dur, "paso": round(paso, 3)})
    for k in range(0, 20, 2):
        c.snd(c.t0 + .3 + k * paso, "pop:" + str(k // 2 % 4), .3)
    c.snd(c.t0 + .3 + 20 * paso, "ding:2", .4)
    return html, js


def e_linea3d(c, d):
    pts = d["puntos"]
    lo, hi = min(pts), max(pts)
    rng = (hi - lo) or 1.0
    unidad = d.get("unidad", "")
    fin = es(pts[-1], 1 if abs(pts[-1]) < 100 and pts[-1] != int(pts[-1]) else 0) + unidad
    dur2 = max(1.6, min(c.dur * .6, 4.0))
    datos = {"pts": [round((v - lo) / rng, 4) for v in pts], "sube": pts[-1] >= pts[0], "txtFin": fin, "eti": d.get("etiquetas"), "t0": c.t0 + .1, "dur2": round(dur2, 2)}
    col = "var(--up)" if pts[-1] >= pts[0] else "var(--down)"
    html, js = _escena(c, d, LINEA, datos, derecha=f'<div style="font-weight:700;font-size:{c.fs(64)};color:{col}">{esc(fin)}</div>')
    c.snd(c.t0 + .1, "swipe", .4)
    c.snd(c.t0 + .1 + dur2, "ding:1", .4)
    return html, js


def e_escudo3d(c, d):
    html, js = _escena(c, d, ESCUDO, {"t0": c.t0 + .05})
    c.snd(c.t0 + .1, "pop", .45)
    c.snd(c.t0 + .6, "impact", .35)
    c.snd(c.t0 + .9, "ding:2", .35)
    return html, js


def e_ciudad3d(c, d):
    paso = max(.1, min(.22, c.dur * .5 / 14))
    html, js = _escena(c, d, CIUDAD, {"t0": c.t0 + .05, "dur": c.dur, "paso": round(paso, 3)})
    c.snd(c.t0 + .05, "riser:0", .4)
    c.snd(c.t0 + 1.2, "whoosh", .35)
    return html, js


ESCENAS.update({"animal3d": (e_animal3d, v_animal3d), "lingotes3d": (e_lingotes3d, v_lingotes3d), "linea3d": (e_linea3d, v_linea3d),
                "escudo3d": (e_escudo3d, v_escudo3d), "ciudad3d": (e_ciudad3d, v_ciudad3d)})
