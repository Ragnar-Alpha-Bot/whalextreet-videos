// Muñecos 2D de WhaleXtreet para las escenas «versus» (novato contra pro). Código propio, sin dependencias, gratis.
// Como las metáforas (motivos.js): cada acción se dibuja en un <canvas> 2D SOLO a partir del tiempo t (segundos desde que entra el panel),
// así cada fotograma sale igual en cualquier ordenador. Coordenadas virtuales: ancho 1000, origen en el centro, suelo en y = H/2 - 60.
// Dos personajes con la paleta del tema: «novato» (gris, sudadera con gorra) y «pro» (chaqueta del color de acento, corbata, pelo peinado).
// Ninguna acción escribe cifras ni datos: solo formas, colores y movimiento.
const TAU = Math.PI * 2;
const cl = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
const eo = k => 1 - Math.pow(1 - cl(k), 3);
const mx = (a, b, k) => a + (b - a) * k;
const hs = n => { const v = Math.sin(n * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };
const col = (c, a = 1) => { let h = c.replace("#", ""); if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2]; return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`; };
const circ = (g, x, y, r) => { g.beginPath(); g.arc(x, y, r, 0, TAU); };
const rr = (g, x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };
const vg = (g, y0, y1, c0, c1) => { const q = g.createLinearGradient(0, y0, 0, y1); q.addColorStop(0, c0); q.addColorStop(1, c1); return q; };

export const ACCIONES = {};
const acc = (id, fn) => { ACCIONES[id] = fn; };
const PIEL = "#F2C9A0";

function colores(rol, K) {
  return rol === "pro"
    ? { ropa: K.acc, ropa2: K.acc2 || K.acc, pant: "#1B2440", zap: "#E8ECF5", pelo: "#2B2118", det: K.res }
    : { ropa: "#8B93A3", ropa2: "#6F7787", pant: "#3B4150", zap: "#C9CED8", pelo: "#4A3A2C", det: "#C2575F" };
}

// Extremidad de dos tramos. Ángulos desde «hacia abajo»: 0 = colgando, positivo = hacia delante (+x). Devuelve la punta.
function miembro(g, x, y, a1, a2, L1, L2, w, c) {
  const x1 = x + Math.sin(a1) * L1, y1 = y + Math.cos(a1) * L1, x2 = x1 + Math.sin(a1 + a2) * L2, y2 = y1 + Math.cos(a1 + a2) * L2;
  g.lineCap = "round"; g.lineJoin = "round"; g.strokeStyle = c; g.lineWidth = w;
  g.beginPath(); g.moveTo(x, y); g.lineTo(x1, y1); g.lineTo(x2, y2); g.stroke();
  return [x2, y2];
}
// Cinemática inversa de dos tramos: ángulos para que la punta llegue a (tx, ty). dir = 1 codo hacia atrás (brazos), -1 rodilla hacia delante (piernas).
function ik(sx, sy, tx, ty, L1, L2, dir = 1) {
  const dx = tx - sx, dy = ty - sy, d = Math.min(Math.hypot(dx, dy), L1 + L2 - 0.5);
  const E = Math.acos(cl((L1 * L1 + L2 * L2 - d * d) / (2 * L1 * L2), -1, 1)), S = Math.acos(cl((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1));
  return [Math.atan2(dx, dy) - dir * S, dir * (Math.PI - E)];
}

// Persona entera, de perfil mirando a +x (dir = -1 la gira). o.x, o.y = cadera. Poses: ángulos de brazos/piernas, inclinación y cara.
function persona(g, K, rol, o) {
  const C = colores(rol, K), s = o.s || 0.7;
  g.save(); g.translate(o.x, o.y); g.scale(s * (o.dir || 1), s);
  const pie = (x, y, a) => { g.save(); g.translate(x, y); g.rotate(-a); g.fillStyle = C.zap; rr(g, -8, -6, 46, 20, 9); g.fill(); g.restore(); };
  const pD = o.piernaD || [0, 0], pI = o.piernaI || [0, 0];
  let e = miembro(g, -6, 0, pI[0], pI[1], 95, 95, 34, C.pant); pie(e[0], e[1], pI[0] + pI[1]);
  e = miembro(g, 6, 0, pD[0], pD[1], 95, 95, 34, C.pant); pie(e[0], e[1], pD[0] + pD[1]);
  g.save(); g.rotate(o.tronco || 0);
  const bI = o.brazoI || [0.1, 0.3], bD = o.brazoD || [0.1, 0.3], hombro = [0, -128];
  const manoI = miembro(g, hombro[0] - 4, hombro[1], bI[0], bI[1], 70, 65, 26, C.ropa2); g.fillStyle = PIEL; circ(g, manoI[0], manoI[1], 15); g.fill();
  g.fillStyle = C.ropa; rr(g, -40, -152, 80, 156, 32); g.fill();
  if (rol === "pro") { g.fillStyle = C.det; g.beginPath(); g.moveTo(8, -140); g.lineTo(22, -118); g.lineTo(14, -70); g.lineTo(2, -118); g.closePath(); g.fill(); g.fillStyle = col("#FFFFFF", .85); g.beginPath(); g.moveTo(-6, -146); g.lineTo(8, -130); g.lineTo(-18, -122); g.closePath(); g.fill(); }
  else { g.strokeStyle = col("#FFFFFF", .4); g.lineWidth = 5; g.beginPath(); g.moveTo(-8, -140); g.lineTo(-8, -100); g.moveTo(14, -140); g.lineTo(14, -100); g.stroke(); }
  const manoD = miembro(g, hombro[0] + 4, hombro[1], bD[0], bD[1], 70, 65, 26, C.ropa); g.fillStyle = PIEL; circ(g, manoD[0], manoD[1], 15); g.fill();
  // cabeza
  g.save(); g.translate(8, -196); g.rotate(o.cabeza || 0);
  g.fillStyle = PIEL; g.fillRect(-12, 30, 24, 22); circ(g, 0, 0, 48); g.fill();
  if (rol === "pro") { g.fillStyle = C.pelo; g.beginPath(); g.arc(0, -4, 50, Math.PI * 1.02, Math.PI * 1.98); g.quadraticCurveTo(30, -34, -4, -30); g.quadraticCurveTo(-34, -28, -48, -4); g.fill(); }
  else { g.fillStyle = C.det; g.beginPath(); g.arc(0, -6, 51, Math.PI, TAU); g.closePath(); g.fill(); rr(g, 18, -16, 46, 14, 7); g.fill(); }
  const cara = o.cara || "normal";
  g.fillStyle = "#1A1F2B"; g.strokeStyle = "#1A1F2B"; g.lineWidth = 5; g.lineCap = "round";
  if (cara === "dormido") { g.beginPath(); g.moveTo(8, 2); g.lineTo(26, 2); g.stroke(); }
  else if (cara === "feliz") { g.beginPath(); g.arc(18, 0, 8, Math.PI * 1.1, Math.PI * 1.9); g.stroke(); }
  else { circ(g, 18, 0, cara === "panico" ? 8 : 6); g.fill(); }
  if (cara === "panico") { g.beginPath(); g.moveTo(6, -18); g.lineTo(30, -26); g.stroke(); g.fillStyle = "#7A2630"; g.beginPath(); g.ellipse(22, 26, 9, 13, 0, 0, TAU); g.fill(); }
  else if (cara === "duda") { g.beginPath(); g.moveTo(8, -20); g.lineTo(28, -14); g.stroke(); g.beginPath(); g.moveTo(10, 24); g.quadraticCurveTo(20, 18, 32, 26); g.stroke(); }
  else if (cara === "feliz") { g.beginPath(); g.arc(20, 18, 14, 0.1, Math.PI - 0.1); g.stroke(); }
  else if (cara !== "dormido") { g.beginPath(); g.moveTo(12, 24); g.lineTo(30, 24); g.stroke(); }
  if (cara === "sudor" || cara === "panico") { g.fillStyle = col("#7DD3FC", .95); const k = (o.t || 0) % 1; g.beginPath(); g.ellipse(-22, -14 + k * 30, 6, 10, 0, 0, TAU); g.fill(); }
  g.restore(); g.restore(); g.restore();
  return { mano: [manoD, manoI] };
}

// ---------------------------------------------------------------- escenario ---------------------------------------------------
function fondo(g, rol, t, K, H) {
  const y0 = -H / 2, suelo = H / 2 - 60;
  if (rol === "pro") {
    g.fillStyle = vg(g, y0, H / 2, col(K.acc, .42), col(K.bg, 1)); g.fillRect(-500, y0, 1000, H);
    g.strokeStyle = col(K.acc, .28); g.lineWidth = 2;
    for (let i = -10; i <= 10; i++) { g.beginPath(); g.moveTo(i * 40, suelo); g.lineTo(i * 150, H / 2); g.stroke(); }
    for (let j = 0; j < 4; j++) { const y = suelo + 8 + j * j * 6 + j * 4; g.beginPath(); g.moveTo(-500, y); g.lineTo(500, y); g.stroke(); }
  } else {
    g.fillStyle = vg(g, y0, H / 2, "#2D323D", "#14171D"); g.fillRect(-500, y0, 1000, H);
    for (let i = 0; i < 7; i++) { const x = ((hs(i) * 1200 + t * (10 + hs(i + 3) * 14)) % 1300) - 650; g.fillStyle = col("#6B7384", .18); circ(g, x, y0 + 40 + hs(i + 9) * 110, 70 + hs(i + 4) * 60); g.fill(); }
    g.fillStyle = col("#000000", .22); g.fillRect(-500, suelo, 1000, H / 2 - suelo);
  }
  g.fillStyle = col(rol === "pro" ? K.acc : "#9AA3B5", .55); g.fillRect(-500, suelo, 1000, 4);
  return suelo;
}
function sombra(g, x, y, r) { g.fillStyle = col("#000000", .3); g.beginPath(); g.ellipse(x, y, r, r * .16, 0, 0, TAU); g.fill(); }
function lineasVel(g, x, y, t, c, n = 5) { g.strokeStyle = c; g.lineWidth = 5; g.lineCap = "round"; for (let i = 0; i < n; i++) { const k = ((t * 3 + hs(i)) % 1), yy = y - 30 + i * 22; g.globalAlpha = (1 - k) * .8; g.beginPath(); g.moveTo(x - 20 - k * 120, yy); g.lineTo(x - 70 - k * 120, yy); g.stroke(); } g.globalAlpha = 1; }
function estrellas(g, x, y, t, c) { for (let i = 0; i < 4; i++) { const a = t * 6 + i * TAU / 4; g.fillStyle = c; circ(g, x + Math.cos(a) * 34, y + Math.sin(a) * 14, 6); g.fill(); } }

// ---------------------------------------------------------------- acciones ----------------------------------------------------
// correr: el pro corre rápido y erguido con estela; el novato va lento, encorvado y sudando.
acc("correr", (g, t, K, rol, H) => {
  const suelo = fondo(g, rol, t, K, H), pro = rol === "pro", ph = t * (pro ? 11 : 6.5);
  for (let i = 0; i < 9; i++) { const x = ((i * 150 - t * (pro ? 420 : 140)) % 1350 + 1350) % 1350 - 675, h = 70 + hs(i + 5) * 120; g.fillStyle = col(pro ? K.acc : "#5A6272", .22); g.fillRect(x, suelo - h, 70, h); }
  const x = pro ? mx(-260, 20, eo(t / 1.4)) : -150 + Math.sin(t * 1.4) * 10, bob = Math.abs(Math.sin(ph)) * (pro ? 10 : 5);
  sombra(g, x, suelo + 4, 70);
  if (pro) lineasVel(g, x - 60, suelo - 150, t, col(K.res, .9));
  persona(g, K, rol, { x, y: suelo - 95 * .7 - bob, s: .7, tronco: pro ? .24 : .06, cabeza: pro ? .04 : .16, t,
    piernaD: [Math.sin(ph) * 1.0, -Math.max(0, Math.cos(ph)) * 1.4], piernaI: [Math.sin(ph + Math.PI) * 1.0, -Math.max(0, Math.cos(ph + Math.PI)) * 1.4],
    brazoD: [Math.sin(ph + Math.PI) * 1.0, 1.0], brazoI: [Math.sin(ph) * 1.0, 1.0], cara: pro ? "feliz" : "sudor" });
});

// teclear: sentado ante el portátil con un reloj; el pro trabaja tranquilo, el novato se agobia y acaba rendido sobre la mesa.
acc("teclear", (g, t, K, rol, H) => {
  const suelo = fondo(g, rol, t, K, H), pro = rol === "pro", s = .7, hx = -150, hy = suelo - 95 * s;
  const rendido = !pro && t > 2.4, k = rendido ? eo((t - 2.4) / .6) : 0;
  g.save(); g.translate(hx, hy); g.scale(s, s);
  sombra(g, 150, 95, 230);
  g.fillStyle = "#3A2F28"; g.fillRect(70, -30, 270, 16); g.fillRect(90, -14, 14, 109); g.fillRect(306, -14, 14, 109);          // mesa
  g.fillStyle = "#222833"; rr(g, -50, 12, 110, 14, 6); g.fill(); g.fillRect(-4, 24, 10, 71);                                  // silla
  g.fillStyle = "#C9D1E3"; rr(g, 104, -42, 130, 12, 5); g.fill();                                                               // base del portátil
  g.fillStyle = "#11151D"; g.beginPath(); g.moveTo(208, -42); g.lineTo(236, -42); g.lineTo(256, -178); g.lineTo(226, -178); g.closePath(); g.fill(); // pantalla
  g.fillStyle = col(pro ? K.up : K.down, .8);
  for (let i = 0; i < 4; i++) { const w = 12 + hs(i + (pro ? 3 : 8)) * 10; g.fillRect(234 + i * 3 - 4, -150 + i * 26, w, 8); }
  // reloj
  const cx = 300, cy = -150; g.fillStyle = "#F4F6FB"; circ(g, cx, cy, 46); g.fill(); g.strokeStyle = "#1A1F2B"; g.lineWidth = 6; circ(g, cx, cy, 46); g.stroke();
  const va = t * (pro ? .5 : 3.2); g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.sin(va) * 34, cy - Math.cos(va) * 34); g.moveTo(cx, cy); g.lineTo(cx + Math.sin(va / 12) * 22, cy - Math.cos(va / 12) * 22); g.stroke();
  g.restore();
  const base = [hx + 105 * s, hy - 46 * s];
  const tec = (i) => [105 + Math.sin(t * (pro ? 14 : 22) + i * 2) * 6, -50 + Math.abs(Math.sin(t * (pro ? 14 : 22) + i * 2)) * -6];
  const aD = ik(0, -128, ...tec(0), 70, 65, 1), aI = ik(0, -128, ...tec(1), 70, 65, 1);
  persona(g, K, rol, { x: hx, y: hy, s, tronco: pro ? .04 : .1 + .55 * k, cabeza: pro ? 0 : .1 + .5 * k, t, brazoD: rendido ? [.5, 1.2] : aD, brazoI: rendido ? [.7, 1.0] : aI,
    piernaD: [1.5708, -1.5708], piernaI: [1.5708, -1.5708], cara: pro ? "feliz" : (rendido ? "dormido" : "sudor") });
  if (rendido && k > .8) { g.fillStyle = col(K.text, .9); g.font = "700 46px InterW, sans-serif"; g.textAlign = "center"; for (let i = 0; i < 3; i++) { const q = ((t * .7 + i / 3) % 1); g.globalAlpha = Math.sin(q * Math.PI); g.fillText("z", hx + 40 + i * 22, hy - 190 - q * 90); } g.globalAlpha = 1; }
});

// mirar_grafico: ante una pantalla con velas; el novato entra en pánico con la caída, el pro la mira con calma.
acc("mirar_grafico", (g, t, K, rol, H) => {
  const suelo = fondo(g, rol, t, K, H), pro = rol === "pro", s = .7, x = -230;
  g.fillStyle = "#0F131B"; rr(g, 40, suelo - 280, 380, 220, 18); g.fill(); g.strokeStyle = col(pro ? K.acc : "#6B7384", .8); g.lineWidth = 5; rr(g, 40, suelo - 280, 380, 220, 18); g.stroke();
  g.fillStyle = "#222833"; g.fillRect(215, suelo - 60, 30, 40); g.fillRect(170, suelo - 24, 120, 12);
  const n = 9, k = eo(t / 1.2);
  for (let i = 0; i < n; i++) {
    const sube = pro ? i % 4 !== 2 : i % 4 === 1, h = (34 + hs(i + 4) * 44) * k, cx = 78 + i * 38, cy = suelo - 170 + (pro ? 22 - i * 9 : -34 + i * 9);
    g.fillStyle = sube ? K.up : K.down; g.fillRect(cx - 1.5, cy - h / 2 - 12, 3, h + 24); g.fillRect(cx - 10, cy - h / 2, 20, h);
  }
  sombra(g, x, suelo + 4, 70);
  const tiembla = pro ? 0 : Math.sin(t * 40) * 3;
  if (pro) persona(g, K, rol, { x, y: suelo - 190 * .7, s, tronco: .03, t, brazoD: [.7, 2.0], brazoI: [.9, 1.9], cabeza: .04, cara: "feliz" });
  else persona(g, K, rol, { x: x + tiembla, y: suelo - 190 * .7, s, tronco: -.05, t, brazoD: [2.7 + Math.sin(t * 9) * .12, .6], brazoI: [2.5 + Math.cos(t * 9) * .12, .6], cabeza: -.08, cara: "panico" });
  g.fillStyle = pro ? K.up : K.down; g.font = "700 90px InterW, sans-serif"; g.textAlign = "center"; g.textBaseline = "middle";
  const q = eo((t - .5) / .4); g.globalAlpha = q; g.fillText(pro ? "✓" : "!", x + 150, suelo - 300 - (1 - q) * 20); g.globalAlpha = 1;
});

// saltar_valla: el pro salta la valla sin esfuerzo; el novato tropieza y se cae.
acc("saltar_valla", (g, t, K, rol, H) => {
  const suelo = fondo(g, rol, t, K, H), pro = rol === "pro", s = .7, p = t / 2.4, vx = 90;
  const cae = !pro && p > .62, kc = cae ? eo((p - .62) / .3) : 0;
  const x = pro ? mx(-380, 330, cl(p)) : mx(-380, vx - 20, cl(p / .62)) + (cae ? kc * 60 : 0);
  const salto = pro && p > .38 && p < .62 ? Math.sin((p - .38) / .24 * Math.PI) * 120 : 0, ph = t * (pro ? 11 : 8.5);
  g.save(); g.translate(vx, suelo); if (cae) g.rotate(kc * -.9); g.fillStyle = col(pro ? K.res : K.warn, .95); g.fillRect(-4, -86, 8, 86); g.fillRect(76, -86, 8, 86); g.fillRect(-4, -92, 88, 12); g.restore();
  sombra(g, x, suelo + 4, 70 - salto * .25);
  const aire = pro && salto > 4, pl = aire ? [[1.4, -1.5], [-.5, -.8]] : [[Math.sin(ph) * 1.0, -Math.max(0, Math.cos(ph)) * 1.4], [Math.sin(ph + Math.PI) * 1.0, -Math.max(0, Math.cos(ph + Math.PI)) * 1.4]];
  if (cae) persona(g, K, rol, { x, y: suelo - 95 * .7 + kc * 70, s, t, tronco: .2 + kc * 1.35, cabeza: .1 + kc * .4, piernaD: [-.6, -.4], piernaI: [-.9, -.6], brazoD: [2.4, .3], brazoI: [2.1, .3], cara: "panico" });
  else persona(g, K, rol, { x, y: suelo - 95 * .7 - salto, s, t, tronco: pro ? .22 : .08, cabeza: .05, piernaD: pl[0], piernaI: pl[1], brazoD: [Math.sin(ph + Math.PI) * 1.0, 1.0], brazoI: [Math.sin(ph) * 1.0, 1.0], cara: pro ? "feliz" : "sudor" });
  if (cae && kc > .7) estrellas(g, x + 80, suelo - 120, t, K.warn);
  if (pro && p > .75) { g.fillStyle = K.up; g.font = "700 80px InterW, sans-serif"; g.textAlign = "center"; g.globalAlpha = eo((p - .75) / .1); g.fillText("✓", x, suelo - 240); g.globalAlpha = 1; }
});

// resultado: el pro celebra con confeti; el novato se rasca la cabeza sin entender qué ha pasado.
acc("resultado", (g, t, K, rol, H) => {
  const suelo = fondo(g, rol, t, K, H), pro = rol === "pro", s = .7, x = -40;
  sombra(g, x, suelo + 4, 70);
  if (pro) {
    const bote = Math.abs(Math.sin(t * 5)) * 26;
    persona(g, K, rol, { x, y: suelo - 190 * .7 - bote, s, t, tronco: 0, cabeza: -.05, brazoD: [2.9 + Math.sin(t * 8) * .15, .4], brazoI: [2.7 + Math.cos(t * 8) * .15, .4], piernaD: [.15, 0], piernaI: [-.15, 0], cara: "feliz" });
    const cc = [K.acc, K.res, K.up, K.warn];
    for (let i = 0; i < 36; i++) { const ph = (t * .8 + hs(i)) % 1, xx = x + (hs(i + 11) - .5) * 520, yy = suelo - 330 + ph * 330; g.save(); g.translate(xx, yy); g.rotate(ph * 9 + i); g.fillStyle = cc[i % 4]; g.globalAlpha = 1 - ph * .5; g.fillRect(-6, -3, 12, 6); g.restore(); }
    g.globalAlpha = 1;
  } else {
    persona(g, K, rol, { x, y: suelo - 190 * .7, s, t, tronco: -.03, cabeza: .22 + Math.sin(t * 3) * .05, brazoD: [2.6, 2.4 + Math.sin(t * 7) * .15], brazoI: [.2, .5], piernaD: [.05, 0], piernaI: [-.05, 0], cara: "duda" });
    for (let i = 0; i < 3; i++) { const ph = (t * .6 + i / 3) % 1; g.fillStyle = col(K.text, Math.sin(ph * Math.PI)); g.font = `700 ${60 + i * 12}px InterW, sans-serif`; g.textAlign = "center"; g.fillText("?", x + 70 + i * 54, suelo - 290 - ph * 40 - i * 14); }
  }
});

// Envoltorio común: dibuja la acción en el lienzo; el alto virtual sale del propio lienzo (ancho virtual = 1000). Todo depende solo de t.
export function dibujarAccion(id, g, w, h, t, K, opciones = {}) {
  const f = ACCIONES[id]; if (!f) throw new Error("acción desconocida: " + id);
  const sc = w / 1000, H = h / sc;
  g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, w, h); g.save(); g.translate(w / 2, h / 2); g.scale(sc, sc);
  g.beginPath(); g.rect(-500, -H / 2, 1000, H); g.clip();
  f(g, Math.max(t, 0), K, opciones.rol === "pro" ? "pro" : "novato", H); g.restore();
}
