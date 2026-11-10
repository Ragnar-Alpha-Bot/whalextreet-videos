// Biblioteca de metáforas visuales de WhaleXtreet (código propio, sin dependencias, gratis).
// Cada motivo dibuja en un <canvas> 2D SOLO a partir del tiempo t (segundos desde que empieza la escena), así cada fotograma sale igual en
// cualquier ordenador. Coordenadas virtuales: 1000 x 1000 con el origen en el centro (x e y de -500 a 500).
// Reglas de la marca: ningún motivo escribe cifras ni precios (nunca datos inventados): solo formas, colores y movimiento.
const TAU = Math.PI * 2;
const cl = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
const eo = k => 1 - Math.pow(1 - cl(k), 3);
const eb = k => { k = cl(k); const c1 = 1.8, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); };
const mx = (a, b, k) => a + (b - a) * k;
const hs = n => { const v = Math.sin(n * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };
const col = (c, a = 1) => { let h = c.replace("#", ""); if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2]; return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`; };
const gl = (g, c, b) => { g.shadowColor = c; g.shadowBlur = b; };
const ng = g => { g.shadowBlur = 0; };
const vg = (g, y0, y1, c0, c1) => { const q = g.createLinearGradient(0, y0, 0, y1); q.addColorStop(0, c0); q.addColorStop(1, c1); return q; };
const rg = (g, x, y, r0, r1, c0, c1) => { const q = g.createRadialGradient(x, y, r0, x, y, r1); q.addColorStop(0, c0); q.addColorStop(1, c1); return q; };
const rr = (g, x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };
const circ = (g, x, y, r) => { g.beginPath(); g.arc(x, y, r, 0, TAU); };

function moneda(g, x, y, r, rot, K, simb) {
  const s = Math.cos(rot), a = Math.abs(s);
  g.save(); g.translate(x, y); g.scale(Math.max(a, 0.04), 1);
  gl(g, col(K.warn, .55), r * .5);
  g.fillStyle = rg(g, -r * .3, -r * .3, r * .1, r * 1.1, "#FFF1C4", K.warn); circ(g, 0, 0, r); g.fill(); ng(g);
  g.strokeStyle = col("#8A5E10", .55); g.lineWidth = r * .09; circ(g, 0, 0, r * .8); g.stroke();
  if (simb && a > .35) { g.fillStyle = col("#7A520C", .9); g.font = `700 ${r * 1.05}px InterW, sans-serif`; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(simb, 0, r * .05); }
  g.restore();
}
function chispas(g, t, n, K, cx, cy, rad, vel, c, tam = 5, ciclo = 1.4) {
  for (let i = 0; i < n; i++) {
    const ph = ((t / ciclo) + hs(i)) % 1, a = hs(i + 50) * TAU, d = rad * eo(ph);
    g.fillStyle = col(c || K.res, (1 - ph) * .9); circ(g, cx + Math.cos(a) * d * (0.5 + hs(i + 9)), cy + Math.sin(a) * d * (0.5 + hs(i + 3)) - vel * ph * 40, tam * (1 - ph) + 1); g.fill();
  }
}
function flecha(g, x, y, ang, len, w, c) {
  g.save(); g.translate(x, y); g.rotate(ang); g.fillStyle = c;
  g.beginPath(); g.moveTo(0, -w / 2); g.lineTo(len - w * 1.4, -w / 2); g.lineTo(len - w * 1.4, -w * 1.2); g.lineTo(len, 0); g.lineTo(len - w * 1.4, w * 1.2); g.lineTo(len - w * 1.4, w / 2); g.lineTo(0, w / 2); g.closePath(); g.fill(); g.restore();
}

export const MOTIVOS = {};
const def = (id, fn) => { MOTIVOS[id] = fn; };

// ---------------------------------------------------------------- MERCADO / BOLSA ------------------------------------------------
def("ciudad_velas", (g, t, K) => {
  const n = 11, base = 250;
  for (let i = 0; i < n; i++) {
    const x = -450 + i * 90 + 45, sube = hs(i + 3) > .36, c = sube ? K.up : K.down, k = eo((t - .07 * i) / .8), h = (140 + hs(i + 9) * 380) * k, w = 56;
    const mecha = 50 + hs(i + 21) * 70;
    g.fillStyle = col(c, .9); gl(g, col(c, .7), 26); g.fillRect(x - 3.5, base - h - mecha * k, 7, h + mecha * k + 40 * k);
    g.fillStyle = vg(g, base - h, base, col(c, .95), col(c, .3)); g.fillRect(x - w / 2, base - h, w, h); ng(g);
    g.fillStyle = col("#FFFFFF", .22);
    for (let f = 0; f < 6; f++) for (let cc = 0; cc < 2; cc++) if (hs(i * 13 + f * 3 + cc + Math.floor(t * 2)) > .55 && (f + 1) * 52 < h) g.fillRect(x - 20 + cc * 24, base - h + 14 + f * 52, 14, 22);
  }
  g.fillStyle = col(K.border, .8); g.fillRect(-500, base, 1000, 6);
  g.fillStyle = vg(g, base, 500, col(K.acc, .18), "rgba(0,0,0,0)"); g.fillRect(-500, base + 6, 1000, 250);
});
def("grafico_sube", (g, t, K) => {
  const pts = [[-440, 330], [-330, 250], [-250, 300], [-130, 120], [-40, 170], [90, -30], [180, 30], [330, -230], [440, -330]], k = eo(t / 1.3);
  const hasta = k * (pts.length - 1);
  g.strokeStyle = col(K.border, .5); g.lineWidth = 3;
  for (let i = -3; i <= 3; i++) { g.beginPath(); g.moveTo(-480, i * 130); g.lineTo(480, i * 130); g.stroke(); }
  const tr = () => { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i <= Math.floor(hasta); i++) g.lineTo(pts[i][0], pts[i][1]); const f = hasta % 1, i = Math.floor(hasta); if (i < pts.length - 1) g.lineTo(mx(pts[i][0], pts[i + 1][0], f), mx(pts[i][1], pts[i + 1][1], f)); };
  tr(); g.lineTo(mx(pts[Math.min(Math.floor(hasta), 7)][0], pts[Math.min(Math.floor(hasta) + 1, 8)][0], hasta % 1), 420); g.lineTo(-440, 420); g.closePath(); g.fillStyle = vg(g, -330, 420, col(K.up, .35), col(K.up, 0)); g.fill();
  tr(); g.strokeStyle = K.up; g.lineWidth = 16; g.lineCap = "round"; g.lineJoin = "round"; gl(g, K.up, 34); g.stroke(); ng(g);
  const i = Math.min(Math.floor(hasta), 7), f = hasta - i, px = mx(pts[i][0], pts[i + 1][0], f), py = mx(pts[i][1], pts[i + 1][1], f);
  g.fillStyle = "#fff"; gl(g, K.up, 40); circ(g, px, py, 24); g.fill(); ng(g);
  if (k >= 1) chispas(g, t, 14, K, px, py, 150, 1, K.up, 6);
});
def("grafico_cae", (g, t, K) => {
  const pts = [[-440, -330], [-330, -250], [-250, -300], [-130, -120], [-40, -170], [90, 30], [180, -30], [330, 230], [440, 330]], k = eo(t / 1.1), hasta = k * (pts.length - 1);
  const sacu = t > 1.0 && t < 1.5 ? Math.sin(t * 90) * 8 * (1.5 - t) : 0; g.translate(sacu, 0);
  g.strokeStyle = col(K.border, .5); g.lineWidth = 3;
  for (let i = -3; i <= 3; i++) { g.beginPath(); g.moveTo(-480, i * 130); g.lineTo(480, i * 130); g.stroke(); }
  const i = Math.min(Math.floor(hasta), 7), f = hasta - i, px = mx(pts[i][0], pts[i + 1][0], f), py = mx(pts[i][1], pts[i + 1][1], f);
  const tr = () => { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let j = 1; j <= i; j++) g.lineTo(pts[j][0], pts[j][1]); g.lineTo(px, py); };
  tr(); g.lineTo(px, -420); g.lineTo(-440, -420); g.closePath(); g.fillStyle = vg(g, 330, -420, col(K.down, .35), col(K.down, 0)); g.fill();
  tr(); g.strokeStyle = K.down; g.lineWidth = 16; g.lineCap = "round"; g.lineJoin = "round"; gl(g, K.down, 34); g.stroke(); ng(g);
  g.fillStyle = "#fff"; gl(g, K.down, 40); circ(g, px, py, 24); g.fill(); ng(g);
  if (k >= 1) flecha(g, 360, 120 + Math.sin(t * 6) * 10, Math.PI / 2, 130, 40, col(K.down, .9));
});
def("montana_rusa", (g, t, K) => {
  const y = x => -80 + Math.sin(x / 95) * 150 + Math.sin(x / 41 + 1) * 40, k = eo(t / 1.1);
  g.strokeStyle = col(K.acc, .9); g.lineWidth = 12; g.lineCap = "round"; gl(g, K.acc, 24); g.beginPath();
  for (let x = -480; x <= -480 + 960 * k; x += 6) { if (x === -480) g.moveTo(x, y(x)); else g.lineTo(x, y(x)); } g.stroke(); ng(g);
  g.strokeStyle = col(K.border, .8); g.lineWidth = 6;
  for (let x = -480; x <= -480 + 960 * k; x += 60) { g.beginPath(); g.moveTo(x, y(x) + 6); g.lineTo(x, 400); g.stroke(); }
  const cx = -440 + ((t * 260) % 880), cy = y(cx), dy = y(cx + 2) - y(cx - 2);
  g.save(); g.translate(cx, cy - 26); g.rotate(Math.atan2(dy, 4)); g.fillStyle = K.res; gl(g, K.res, 24); rr(g, -34, -22, 68, 40, 12); g.fill(); ng(g); g.fillStyle = K.bg; circ(g, -10, -4, 8); g.fill(); circ(g, 14, -4, 8); g.fill(); g.restore();
});
def("toro", (g, t, K) => {
  const k = eb(t / .6), sc = (.55 + .45 * k) * (1 + Math.sin(t * 7) * .015); g.save(); g.translate(0, 40); g.scale(sc * 1.15, sc * 1.15);
  gl(g, K.up, 40); g.fillStyle = col(K.up, .95);
  g.beginPath(); g.moveTo(-95, -60); g.bezierCurveTo(-260, -80, -300, -230, -220, -300); g.bezierCurveTo(-250, -200, -190, -130, -110, -140); g.closePath(); g.fill();
  g.beginPath(); g.moveTo(95, -60); g.bezierCurveTo(260, -80, 300, -230, 220, -300); g.bezierCurveTo(250, -200, 190, -130, 110, -140); g.closePath(); g.fill();
  g.beginPath(); g.ellipse(-150, -20, 70, 34, -.4, 0, TAU); g.fill(); g.beginPath(); g.ellipse(150, -20, 70, 34, .4, 0, TAU); g.fill();
  g.beginPath(); g.moveTo(-110, -150); g.bezierCurveTo(-130, 40, -90, 150, -60, 190); g.lineTo(60, 190); g.bezierCurveTo(90, 150, 130, 40, 110, -150); g.bezierCurveTo(60, -190, -60, -190, -110, -150); g.fill(); ng(g);
  g.fillStyle = col(K.bg, .9); circ(g, -52, -40, 15); g.fill(); circ(g, 52, -40, 15); g.fill();
  g.fillStyle = col("#FFFFFF", .22); g.beginPath(); g.ellipse(0, 130, 68, 52, 0, 0, TAU); g.fill();
  g.fillStyle = col(K.bg, .9); circ(g, -24, 134, 10); g.fill(); circ(g, 24, 134, 10); g.fill();
  g.restore(); flecha(g, 340, 280 - eo(t / .8) * 90, -Math.PI / 2, 150, 40, col(K.up, .95)); chispas(g, t, 10, K, 0, -150, 260, 1.5, K.up);
});
def("oso", (g, t, K) => {
  const k = eb(t / .6), sc = (.55 + .45 * k) * (1 + Math.sin(t * 5) * .012); g.save(); g.translate(0, 40); g.scale(sc * 1.15, sc * 1.15);
  gl(g, K.down, 40); g.fillStyle = col(K.down, .95);
  circ(g, -125, -150, 62); g.fill(); circ(g, 125, -150, 62); g.fill(); circ(g, 0, 0, 175); g.fill(); ng(g);
  g.fillStyle = col(K.bg, .35); circ(g, -125, -150, 32); g.fill(); circ(g, 125, -150, 32); g.fill();
  g.fillStyle = col("#FFFFFF", .22); g.beginPath(); g.ellipse(0, 60, 80, 60, 0, 0, TAU); g.fill();
  g.fillStyle = col(K.bg, .95); circ(g, -62, -30, 16); g.fill(); circ(g, 62, -30, 16); g.fill(); g.beginPath(); g.ellipse(0, 40, 24, 16, 0, 0, TAU); g.fill();
  g.strokeStyle = col(K.bg, .9); g.lineWidth = 8; g.lineCap = "round"; g.beginPath(); g.arc(0, 90, 34, Math.PI * 1.15, Math.PI * 1.85); g.stroke();
  g.restore(); flecha(g, 340, 150 + eo(t / .8) * 90, Math.PI / 2, 150, 40, col(K.down, .95));
});
def("pared_pantallas", (g, t, K) => {
  const cols = [K.acc, K.acc2, K.res, K.up, K.down], cw = 150, ch = 270;
  for (let c = -3; c <= 3; c++) {
    const off = ((t * (40 + (Math.abs(c) % 3) * 22) * (c % 2 ? 1 : -1)) % 330 + 330) % 330 - 330;
    for (let r = -1; r < 5; r++) {
      const x = c * 165 - cw / 2, y = off + r * 330 - 380, id = (c + 5) * 7 + r, a = cols[Math.floor(hs(id) * 5)], dist = Math.abs(c) / 3;
      g.save(); g.globalAlpha = 1 - dist * .55; g.fillStyle = col(K.surface, 1); rr(g, x, y, cw, ch, 20); g.fill(); g.strokeStyle = col(K.border, 1); g.lineWidth = 3; g.stroke();
      g.save(); rr(g, x + 8, y + 8, cw - 16, ch - 16, 14); g.clip();
      g.fillStyle = vg(g, y, y + ch, col(a, .9), col(a, .12)); g.fillRect(x, y, cw, ch);
      g.fillStyle = col("#000", .35); const b = 30 + hs(id + 4) * 110; g.beginPath(); g.moveTo(x, y + ch); g.lineTo(x + cw * .3, y + ch - b); g.lineTo(x + cw * .55, y + ch - b * .5); g.lineTo(x + cw * .8, y + ch - b * 1.3); g.lineTo(x + cw, y + ch); g.fill(); g.restore();
      g.fillStyle = col("#FFFFFF", .8); circ(g, x + 22, y + ch - 24, 6); g.fill(); g.fillRect(x + 34, y + ch - 28, 30 + hs(id) * 40, 8); g.restore();
    }
  }
  const dy = 320 - eo(t / .7) * 260 + Math.sin(t * 3.2) * 24, dx = 90;
  g.save(); g.translate(dx, dy); g.rotate(-.18); g.fillStyle = "#F4C9A8"; gl(g, "rgba(0,0,0,.5)", 30); rr(g, -48, 0, 96, 420, 48); g.fill(); ng(g); g.fillStyle = "#E3A77F"; rr(g, -30, 6, 60, 46, 22); g.fill(); g.restore();
});
def("ticker", (g, t, K) => {
  for (let f = 0; f < 5; f++) {
    const y = -380 + f * 190, dir = f % 2 ? 1 : -1, off = (t * 150 * dir) % 380;
    g.fillStyle = col(K.surface, .9); g.fillRect(-500, y - 62, 1000, 124); g.fillStyle = col(K.border, .8); g.fillRect(-500, y - 62, 1000, 3); g.fillRect(-500, y + 59, 1000, 3);
    for (let i = -3; i < 4; i++) {
      const x = i * 380 + off, id = f * 10 + i + (dir > 0 ? 0 : 5), sube = hs(id + 7) > .45, c = sube ? K.up : K.down;
      g.fillStyle = col(K.text, .85); g.fillRect(x - 150, y - 12, 50 + hs(id) * 70, 22); g.fillStyle = col(K.muted, .6); g.fillRect(x - 150, y + 18, 90, 12);
      g.fillStyle = c; gl(g, c, 18); g.beginPath(); if (sube) { g.moveTo(x + 60, y - 26); g.lineTo(x + 90, y + 24); g.lineTo(x + 30, y + 24); } else { g.moveTo(x + 60, y + 26); g.lineTo(x + 90, y - 24); g.lineTo(x + 30, y - 24); } g.fill(); ng(g);
      g.fillRect(x + 110, y - 10, 50 + hs(id + 2) * 40, 20);
    }
  }
});
def("balanza", (g, t, K) => {
  const ang = Math.sin(cl(t / 1.4) * Math.PI * 1.5) * (1 - cl(t / 1.6) * .35) * .42 - .12 * eo((t - 1) / .6);
  g.fillStyle = col(K.border, 1); g.fillRect(-12, -300, 24, 560); rr(g, -150, 250, 300, 40, 16); g.fill(); circ(g, 0, -300, 30); g.fill();
  g.save(); g.translate(0, -290); g.rotate(ang); g.fillStyle = col(K.acc2, .95); gl(g, K.acc2, 24); rr(g, -380, -10, 760, 20, 10); g.fill(); ng(g);
  [[-1, K.down], [1, K.up]].forEach(([s, c]) => {
    const px = s * 360; g.save(); g.translate(px, 0); g.rotate(-ang); g.strokeStyle = col(K.muted, .7); g.lineWidth = 4;
    g.beginPath(); g.moveTo(0, 0); g.lineTo(-90, 210); g.moveTo(0, 0); g.lineTo(90, 210); g.stroke();
    g.fillStyle = col(c, .9); gl(g, c, 28); g.beginPath(); g.ellipse(0, 220, 120, 30, 0, 0, TAU); g.fill(); ng(g);
    const n = s < 0 ? 2 : 5; for (let i = 0; i < n; i++) { g.fillStyle = col(c, .95); circ(g, (i % 3 - 1) * 56, 190 - Math.floor(i / 3) * 42, 24); g.fill(); }
    g.restore();
  });
  g.restore();
});
def("semaforo", (g, t, K) => {
  const fase = Math.floor(t / .7) % 3, cs = [K.down, K.res, K.up];
  g.fillStyle = col(K.surface, 1); rr(g, -150, -380, 300, 760, 80); g.fill(); g.strokeStyle = col(K.border, 1); g.lineWidth = 8; g.stroke();
  for (let i = 0; i < 3; i++) { const on = i === fase; g.fillStyle = on ? cs[i] : col(cs[i], .14); if (on) gl(g, cs[i], 70); circ(g, 0, -230 + i * 230, 88); g.fill(); ng(g); }
  g.fillStyle = col(K.border, 1); g.fillRect(-14, 380, 28, 130);
});
def("bola_nieve", (g, t, K) => {
  g.strokeStyle = col(K.border, .9); g.lineWidth = 8; g.beginPath(); g.moveTo(-500, -260); g.lineTo(500, 340); g.stroke();
  g.fillStyle = vg(g, -260, 500, col("#FFFFFF", .10), "rgba(0,0,0,0)"); g.beginPath(); g.moveTo(-500, -260); g.lineTo(500, 340); g.lineTo(500, 500); g.lineTo(-500, 500); g.fill();
  const k = cl(t / 3), x = mx(-420, 330, k), y = mx(-290, 300, k), r = mx(30, 200, k * k * .5 + k * .5), ang = t * 2.4;
  for (let i = 0; i < 14; i++) { const ph = (t * 1.3 + i / 14) % 1; g.fillStyle = col("#FFFFFF", (1 - ph) * .7); circ(g, x - 30 - ph * 220 + hs(i) * 40, y - r * .3 - ph * 110 - hs(i + 2) * 70, 8 * (1 - ph) + 2); g.fill(); }
  g.save(); g.translate(x, y - r * .95); gl(g, K.acc, 40); g.fillStyle = rg(g, -r * .3, -r * .35, r * .1, r * 1.05, "#FFFFFF", "#A9BEDD"); g.beginPath();
  for (let i = 0; i <= 36; i++) { const a = i / 36 * TAU, rr_ = r * (1 + Math.sin(a * 5 + ang) * .035 + Math.sin(a * 3 - ang * .7) * .03); if (!i) g.moveTo(Math.cos(a) * rr_, Math.sin(a) * rr_); else g.lineTo(Math.cos(a) * rr_, Math.sin(a) * rr_); }
  g.closePath(); g.fill(); ng(g); g.strokeStyle = col("#7F96BA", .55); g.lineWidth = Math.max(r * .035, 3); for (let i = 0; i < 3; i++) { g.beginPath(); g.arc(0, 0, r * (.35 + i * .22), ang + i * 2, ang + i * 2 + 1.6); g.stroke(); } g.restore();
});
def("arbol_monedas", (g, t, K) => {
  const k = eo(t / 1.4); g.strokeStyle = "#B98655"; g.lineCap = "round";
  const rama = (x, y, a, l, d, i) => {
    const e = cl(k * 2 - d * .4); if (e <= 0 || l < 12) return; const x2 = x + Math.cos(a) * l * e, y2 = y + Math.sin(a) * l * e;
    g.lineWidth = Math.max(l / 7, 3); g.beginPath(); g.moveTo(x, y); g.lineTo(x2, y2); g.stroke();
    if (l < 60) { const q = eb((t - .5 - d * .18 - hs(i) * .5) / .5); if (q > 0) moneda(g, x2, y2, 26 * q, t * 2 + i, K, "$"); return; }
    rama(x2, y2, a - .5 - hs(i) * .2, l * .72, d + 1, i * 2 + 1); rama(x2, y2, a + .5 + hs(i + 1) * .2, l * .72, d + 1, i * 2 + 2);
  };
  rama(0, 420, -Math.PI / 2, 200, 0, 1);
  g.fillStyle = col(K.up, .25); g.beginPath(); g.ellipse(0, 430, 230, 36, 0, 0, TAU); g.fill();
});
def("diversificar", (g, t, K) => {
  const cs = [K.acc, K.acc2, K.res, K.up];
  for (let i = 0; i < 4; i++) {
    const x = -330 + i * 220, k = eo((t - .5 - i * .25) / .7);
    g.fillStyle = col(K.surface, 1); g.strokeStyle = col(cs[i], .9); g.lineWidth = 7; gl(g, cs[i], 18); g.beginPath(); g.moveTo(x - 85, 90); g.lineTo(x - 65, 330); g.lineTo(x + 65, 330); g.lineTo(x + 85, 90); g.stroke(); ng(g);
    for (let j = 0; j < 4; j++) if (k * 4 > j) moneda(g, x + (j % 2 - .5) * 70, 290 - Math.floor(j / 2) * 56, 30, 0, K, "");
    const px = mx(0, x, k), py = mx(-250, 40, k) - Math.sin(k * Math.PI) * 140;
    if (k > 0 && k < 1) moneda(g, px, py, 34, t * 14, K, "$");
  }
  moneda(g, 0, -300, 90 * (1 - cl((t - .3) / 1.6) * .35), t * 1.2, K, "$"); chispas(g, t, 8, K, 0, -300, 160, 0, K.res);
});
def("hucha", (g, t, K) => {
  g.save(); g.translate(0, 120); const sq = 1 + Math.sin(t * 5) * .012; g.scale(sq, 2 - sq);
  gl(g, col(K.acc, .5), 40); g.fillStyle = vg(g, -170, 170, "#FFB6C9", "#E8718F");
  g.beginPath(); g.ellipse(0, 0, 250, 175, 0, 0, TAU); g.fill(); ng(g);
  g.beginPath(); g.moveTo(-90, -150); g.lineTo(-60, -230); g.lineTo(-10, -165); g.fill();
  [[-150, 150], [-50, 150], [70, 150], [170, 150]].forEach(([x, y]) => { rr(g, x - 28, y - 10, 56, 90, 20); g.fill(); });
  g.fillStyle = "#F7A1B8"; g.beginPath(); g.ellipse(250, 30, 56, 70, 0, 0, TAU); g.fill(); g.fillStyle = "#B2435F"; circ(g, 252, 10, 9); g.fill(); circ(g, 252, 50, 9); g.fill();
  g.fillStyle = "#1B263B"; circ(g, 160, -50, 14); g.fill(); rr(g, -80, -176, 160, 22, 11); g.fill();
  g.beginPath(); g.moveTo(-250, 10); g.quadraticCurveTo(-330, -20, -300, -80); g.strokeStyle = "#E8718F"; g.lineWidth = 12; g.stroke();
  g.restore();
  for (let i = 0; i < 3; i++) { const ph = ((t * .9 + i / 3) % 1), y = mx(-460, -50, eo(ph)), a = cl(1 - (ph - .85) / .15); if (a > 0) { g.globalAlpha = a; moneda(g, 0, y, 52, t * 8 + i, K, "$"); g.globalAlpha = 1; } }
});
def("lluvia_monedas", (g, t, K) => {
  for (let i = 0; i < 26; i++) { const ph = ((t * (.35 + hs(i + 1) * .3) + hs(i)) % 1), x = -440 + hs(i + 11) * 880, y = -560 + ph * 1120, r = 28 + hs(i + 4) * 30; moneda(g, x, y, r, t * (3 + hs(i) * 4) + i, K, i % 3 ? "$" : "€"); }
});
def("billete_se_va", (g, t, K) => {
  const k = cl((t - .2) / 2.2);
  g.save(); g.translate(0, 0); g.rotate(-.08);
  for (let i = 0; i < 60; i++) {
    const cx = -330 + (i % 10) * 66 + 33, cy = -150 + Math.floor(i / 10) * 50 + 25, ph = cl(k * 1.6 - (i % 10) / 10 * 1.0 + hs(i) * .2), a = 1 - ph;
    if (a <= 0) continue; g.fillStyle = col(K.up, .9 * a); g.save(); g.translate(cx + ph * 420 + hs(i) * 60 * ph, cy - ph * 240 * hs(i + 3) + ph * 60); g.rotate(ph * 4 * (hs(i + 5) - .5)); g.fillRect(-30 * (1 - ph * .6), -22 * (1 - ph * .6), 60 * (1 - ph * .6), 44 * (1 - ph * .6)); g.restore();
  }
  g.restore();
  g.strokeStyle = col(K.up, .9); g.lineWidth = 6; g.globalAlpha = 1 - k * .8; rr(g, -330, -150, 660, 300, 22); g.stroke(); circ(g, 0, 0, 80); g.stroke(); g.globalAlpha = 1;
  g.fillStyle = col(K.down, .85); flecha(g, 120, 330, Math.PI / 2, 130, 38, col(K.down, .9)); flecha(g, -120, 330, Math.PI / 2, 130, 38, col(K.down, .9));
});
def("cubo_agujero", (g, t, K) => {
  const nivel = mx(-60, 190, cl(t / 3)); g.save(); g.beginPath(); g.moveTo(-210, -150); g.lineTo(-150, 280); g.lineTo(150, 280); g.lineTo(210, -150); g.closePath(); g.fillStyle = col(K.surface, .95); g.fill(); g.clip();
  g.fillStyle = vg(g, nivel, 280, col(K.warn, .55), col(K.warn, .25)); g.fillRect(-250, nivel, 500, 400);
  for (let i = 0; i < 9; i++) moneda(g, -120 + (i % 3) * 120 + (hs(i) - .5) * 30, 250 - Math.floor(i / 3) * 52 - (nivel < 200 ? 0 : 0), 30, 0, K, "");
  g.restore(); g.strokeStyle = col(K.muted, .95); g.lineWidth = 12; g.lineJoin = "round"; g.beginPath(); g.moveTo(-210, -150); g.lineTo(-150, 280); g.lineTo(150, 280); g.lineTo(210, -150); g.stroke();
  g.fillStyle = col(K.bg, 1); g.beginPath(); g.ellipse(0, 280, 40, 14, 0, 0, TAU); g.fill();
  for (let i = 0; i < 5; i++) { const ph = (t * .8 + i / 5) % 1; moneda(g, (hs(i) - .5) * 200, mx(-480, -100, eo(ph)), 36, t * 6 + i, K, "$"); }
  for (let i = 0; i < 8; i++) { const ph = (t * 1.1 + i / 8) % 1; g.globalAlpha = 1 - ph; moneda(g, (hs(i + 4) - .5) * 120 * ph, 295 + ph * 190, 28, t * 9 + i, K, "$"); g.globalAlpha = 1; }
});
def("caja_fuerte", (g, t, K) => {
  const ab = eo((t - 1.3) / .8); g.fillStyle = col(K.warn, .35 * ab); g.beginPath(); g.ellipse(0, 20, 260 * ab, 200 * ab, 0, 0, TAU); g.fill();
  if (ab > 0) { for (let i = 0; i < 7; i++) moneda(g, (i - 3) * 62, 70 - Math.abs(i - 3) * 20, 34 * ab, t * 2 + i, K, "$"); }
  g.fillStyle = col(K.raised, 1); rr(g, -330, -330, 660, 660, 40); g.fill(); g.strokeStyle = col(K.border, 1); g.lineWidth = 14; g.stroke();
  g.save(); g.translate(-330, 0); g.scale(Math.cos(ab * 1.2), 1); g.translate(330, 0);
  g.fillStyle = vg(g, -300, 300, "#34445F", "#1B263B"); rr(g, -290, -290, 580, 580, 28); g.fill(); g.strokeStyle = col(K.acc, .8); g.lineWidth = 8; rr(g, -250, -250, 500, 500, 20); g.stroke();
  g.save(); g.rotate(eo(t / 1.2) * 7 - ab * 2); g.fillStyle = col(K.res, 1); gl(g, K.res, 24); circ(g, 0, 0, 96); g.fill(); ng(g);
  g.strokeStyle = col(K.bg, .8); g.lineWidth = 8; for (let i = 0; i < 8; i++) { g.beginPath(); g.moveTo(Math.cos(i * TAU / 8) * 40, Math.sin(i * TAU / 8) * 40); g.lineTo(Math.cos(i * TAU / 8) * 92, Math.sin(i * TAU / 8) * 92); g.stroke(); } g.restore();
  g.fillStyle = col(K.up, 1); circ(g, 180, -190, 14); g.fill(); g.restore();
});
def("lupa", (g, t, K) => {
  for (let i = 0; i < 9; i++) { const h = 100 + hs(i + 2) * 260, x = -400 + i * 100; g.fillStyle = col(hs(i) > .5 ? K.up : K.down, .35); g.fillRect(x - 26, 330 - h, 52, h); }
  const cx = Math.sin(t * 1.3) * 250, cy = Math.cos(t * .9) * 90 - 40;
  g.save(); circ(g, cx, cy, 170); g.clip(); g.fillStyle = col(K.bg, .9); g.fillRect(-500, -500, 1000, 1000); g.translate(cx, cy); g.scale(1.55, 1.55); g.translate(-cx, -cy);
  for (let i = 0; i < 9; i++) { const h = 100 + hs(i + 2) * 260, x = -400 + i * 100; g.fillStyle = col(hs(i) > .5 ? K.up : K.down, .9); g.fillRect(x - 26, 330 - h, 52, h); } g.restore();
  g.strokeStyle = col(K.acc, 1); g.lineWidth = 22; gl(g, K.acc, 24); circ(g, cx, cy, 170); g.stroke(); ng(g); g.lineWidth = 36; g.lineCap = "round"; g.beginPath(); g.moveTo(cx + 120, cy + 120); g.lineTo(cx + 280, cy + 280); g.stroke();
});
def("reloj", (g, t, K) => {
  g.fillStyle = col(K.surface, 1); gl(g, K.acc, 36); circ(g, 0, 0, 330); g.fill(); ng(g); g.strokeStyle = col(K.acc, 1); g.lineWidth = 14; g.stroke();
  for (let i = 0; i < 12; i++) { const a = i * TAU / 12; g.strokeStyle = col(K.muted, .9); g.lineWidth = i % 3 ? 6 : 12; g.beginPath(); g.moveTo(Math.cos(a) * 285, Math.sin(a) * 285); g.lineTo(Math.cos(a) * 310, Math.sin(a) * 310); g.stroke(); }
  const m = t * 5, h = m / 12; g.lineCap = "round"; g.strokeStyle = K.text; g.lineWidth = 16; g.beginPath(); g.moveTo(0, 0); g.lineTo(Math.cos(h - 1.57) * 170, Math.sin(h - 1.57) * 170); g.stroke();
  g.strokeStyle = K.res; g.lineWidth = 10; g.beginPath(); g.moveTo(0, 0); g.lineTo(Math.cos(m - 1.57) * 250, Math.sin(m - 1.57) * 250); g.stroke(); g.fillStyle = K.res; circ(g, 0, 0, 18); g.fill();
  for (let i = 0; i < 6; i++) { const ph = (t * .6 + i / 6) % 1, a = i * 1.05 + t; g.globalAlpha = Math.sin(ph * Math.PI); moneda(g, Math.cos(a) * 420, Math.sin(a) * 420, 30, t * 5 + i, K, "$"); g.globalAlpha = 1; }
});
def("cohete", (g, t, K) => {
  for (let i = 0; i < 40; i++) { const x = (hs(i) - .5) * 1000, ph = (t * (.5 + hs(i + 3)) + hs(i + 9)) % 1, y = -500 + ph * 1000; g.fillStyle = col("#FFFFFF", .3 + hs(i) * .5); g.fillRect(x, y, 3, 10 + hs(i) * 24); }
  const y = mx(250, -80, eo(t / 1.6)) + Math.sin(t * 25) * 3, x = Math.sin(t * 40) * 2;
  for (let i = 0; i < 22; i++) { const ph = (t * 2.6 + i / 22) % 1; g.fillStyle = col(i % 2 ? K.res : K.down, (1 - ph) * .85); circ(g, x + (hs(i) - .5) * 60 * ph, y + 150 + ph * 330, 34 * (1 - ph) + 6); g.fill(); }
  g.save(); g.translate(x, y); gl(g, K.acc, 40); g.fillStyle = vg(g, -200, 160, "#FFFFFF", "#C7D3E6"); g.beginPath(); g.moveTo(0, -240); g.bezierCurveTo(110, -130, 100, 40, 70, 150); g.lineTo(-70, 150); g.bezierCurveTo(-100, 40, -110, -130, 0, -240); g.fill(); ng(g);
  g.fillStyle = col(K.down, 1); g.beginPath(); g.moveTo(-70, 70); g.lineTo(-150, 190); g.lineTo(-70, 150); g.fill(); g.beginPath(); g.moveTo(70, 70); g.lineTo(150, 190); g.lineTo(70, 150); g.fill();
  g.fillStyle = col(K.acc, 1); circ(g, 0, -80, 44); g.fill(); g.fillStyle = col(K.bg, .8); circ(g, 0, -80, 28); g.fill(); g.restore();
});
def("ruleta", (g, t, K) => {
  const giro = eo(t / 3) * 14; g.save(); g.rotate(giro);
  for (let i = 0; i < 16; i++) { g.fillStyle = i % 2 ? col(K.down, .9) : col(K.surface, 1); if (i === 0) g.fillStyle = col(K.up, .9); g.beginPath(); g.moveTo(0, 0); g.arc(0, 0, 330, i * TAU / 16, (i + 1) * TAU / 16); g.fill(); }
  g.strokeStyle = col(K.res, .9); g.lineWidth = 10; circ(g, 0, 0, 330); g.stroke(); circ(g, 0, 0, 120); g.stroke(); g.fillStyle = col(K.raised, 1); circ(g, 0, 0, 110); g.fill(); g.restore();
  const a = -giro * 1.6 - t * .5, r = mx(300, 215, eo(t / 3)); g.fillStyle = "#fff"; gl(g, "#fff", 26); circ(g, Math.cos(a) * r, Math.sin(a) * r, 18); g.fill(); ng(g);
});
def("dados", (g, t, K) => {
  const dado = (x, y, s, rot, n, c) => {
    g.save(); g.translate(x, y); g.rotate(rot); gl(g, col(c, .6), 30); g.fillStyle = "#F4F7FC"; rr(g, -s / 2, -s / 2, s, s, s * .18); g.fill(); ng(g); g.fillStyle = c;
    const P = { 1: [[0, 0]], 2: [[-1, -1], [1, 1]], 3: [[-1, -1], [0, 0], [1, 1]], 4: [[-1, -1], [1, -1], [-1, 1], [1, 1]], 5: [[-1, -1], [1, -1], [0, 0], [-1, 1], [1, 1]], 6: [[-1, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [1, 1]] };
    P[n].forEach(([a, b]) => { circ(g, a * s * .26, b * s * .26, s * .075); g.fill(); }); g.restore();
  };
  const k = eo(t / 1.3), rodando = t < 1.3, n1 = rodando ? 1 + Math.floor(t * 14) % 6 : 5, n2 = rodando ? 1 + Math.floor(t * 11 + 2) % 6 : 2;
  dado(mx(-420, -130, k), mx(-300, 60, k) - Math.abs(Math.sin(t * 7)) * 90 * (1 - k), 250, t * 5 * (1 - k * .9), n1, K.down); dado(mx(420, 150, k), mx(-380, 120, k) - Math.abs(Math.sin(t * 6)) * 90 * (1 - k), 220, -t * 4 * (1 - k * .9), n2, K.acc2);
});
def("escudo", (g, t, K) => {
  const k = eb(t / .7); g.save(); g.scale(k, k);
  for (let i = 0; i < 3; i++) { const ph = (t * .8 + i / 3) % 1; g.strokeStyle = col(K.acc, (1 - ph) * .7); g.lineWidth = 8; g.beginPath(); g.arc(0, 0, 250 + ph * 230, 0, TAU); g.stroke(); }
  gl(g, K.acc, 50); g.fillStyle = vg(g, -300, 300, col(K.acc, .95), col(K.acc2, .75)); g.beginPath(); g.moveTo(0, -300); g.bezierCurveTo(130, -230, 230, -230, 260, -240); g.bezierCurveTo(260, 40, 180, 200, 0, 310); g.bezierCurveTo(-180, 200, -260, 40, -260, -240); g.bezierCurveTo(-230, -230, -130, -230, 0, -300); g.fill(); ng(g);
  g.strokeStyle = K.bg; g.lineWidth = 36; g.lineCap = "round"; g.lineJoin = "round"; const c = eo((t - .5) / .5); g.beginPath(); g.moveTo(-95, 10); g.lineTo(mx(-95, -25, cl(c * 2)), mx(10, 100, cl(c * 2))); if (c > .5) g.lineTo(mx(-25, 110, (c - .5) * 2), mx(100, -80, (c - .5) * 2)); g.stroke(); g.restore();
});
def("alarma", (g, t, K) => {
  const a = t * 5; for (let i = 0; i < 12; i++) { g.save(); g.rotate(a + i * TAU / 12); const gr = g.createLinearGradient(0, 0, 520, 0); gr.addColorStop(0, col(K.down, .5)); gr.addColorStop(1, col(K.down, 0)); g.fillStyle = gr; if (i % 2 === 0) { g.beginPath(); g.moveTo(0, 0); g.lineTo(540, -70); g.lineTo(540, 70); g.fill(); } g.restore(); }
  g.fillStyle = col(K.raised, 1); rr(g, -190, 140, 380, 90, 20); g.fill(); gl(g, K.down, 70 + Math.sin(a * 2) * 30); g.fillStyle = vg(g, -170, 150, "#FFB3B3", K.down); g.beginPath(); g.moveTo(-150, 150); g.lineTo(-150, -20); g.bezierCurveTo(-150, -190, 150, -190, 150, -20); g.lineTo(150, 150); g.fill(); ng(g);
  g.fillStyle = "#fff"; rr(g, -60, -140, 40, 130, 20); g.fill();
});
def("cuenta_atras", (g, t, K) => {
  const n = 3 - Math.floor(t / .85), f = (t % .85) / .85; g.lineWidth = 26; g.lineCap = "round";
  g.strokeStyle = col(K.border, .8); circ(g, 0, 0, 300); g.stroke(); g.strokeStyle = n > 1 ? K.acc : K.down; gl(g, g.strokeStyle, 36); g.beginPath(); g.arc(0, 0, 300, -Math.PI / 2, -Math.PI / 2 + TAU * (1 - f)); g.stroke(); ng(g);
  if (n >= 1 && t < 2.55) { g.fillStyle = K.text; g.font = "700 420px InterW, sans-serif"; g.textAlign = "center"; g.textBaseline = "middle"; const s = 1 + (1 - f) * .25; g.save(); g.scale(s, s); g.globalAlpha = .4 + f * .6; g.fillText(String(n), 0, 20); g.restore(); g.globalAlpha = 1; }
  else { moneda(g, 0, 0, 160 * eb((t - 2.55) / .5), t * 7, K, "$"); }
});
def("pulso_mercado", (g, t, K) => {
  const col2 = t % 3 < 1.5 ? K.up : K.down; g.strokeStyle = col(K.border, .45); g.lineWidth = 3; for (let i = -3; i <= 3; i++) { g.beginPath(); g.moveTo(-500, i * 120); g.lineTo(500, i * 120); g.stroke(); }
  const y = x => { const q = ((x + t * 380) % 400 + 400) % 400, w = [[0, 0], [60, 0], [85, -60], [110, 40], [140, -320], [175, 280], [205, -40], [240, 0], [300, -70], [330, 0], [400, 0]]; for (let i = 1; i < w.length; i++) if (q <= w[i][0]) return mx(w[i - 1][1], w[i][1], (q - w[i - 1][0]) / (w[i][0] - w[i - 1][0])); return 0; };
  g.strokeStyle = col2; g.lineWidth = 12; g.lineJoin = "round"; gl(g, col2, 30); g.beginPath(); for (let x = -480; x <= 480; x += 5) { if (x === -480) g.moveTo(x, y(x)); else g.lineTo(x, y(x)); } g.stroke(); ng(g);
  g.fillStyle = "#fff"; gl(g, col2, 34); circ(g, 460, y(460), 14); g.fill(); ng(g);
});
def("radar", (g, t, K) => {
  g.strokeStyle = col(K.up, .5); g.lineWidth = 4; for (let i = 1; i <= 4; i++) { circ(g, 0, 0, i * 100); g.stroke(); } g.beginPath(); g.moveTo(-400, 0); g.lineTo(400, 0); g.moveTo(0, -400); g.lineTo(0, 400); g.stroke();
  const a = t * 2.6; g.save(); g.rotate(a); const gr = g.createLinearGradient(0, 0, 400, 0); gr.addColorStop(0, col(K.up, .55)); gr.addColorStop(1, col(K.up, 0)); g.fillStyle = gr; g.beginPath(); g.moveTo(0, 0); g.arc(0, 0, 400, -.55, 0); g.fill(); g.restore();
  for (let i = 0; i < 6; i++) { const ba = hs(i) * TAU, r = 90 + hs(i + 4) * 280, d = (((a - ba) % TAU) + TAU) % TAU, v = Math.max(0, 1 - d / 3.2); g.fillStyle = col(i % 3 ? K.up : K.res, v); gl(g, K.res, 18 * v); circ(g, Math.cos(ba) * r, Math.sin(ba) * r, 10 + v * 12); g.fill(); ng(g); }
});
def("pantalla_trading", (g, t, K) => {
  [[-170, -250, 320, 280, 0], [190, -250, 300, 280, 1], [-250, 70, 310, 260, 2], [110, 70, 380, 260, 3]].forEach(([x, y, w, h, s], i) => {
    const k = eb((t - i * .18) / .5); g.save(); g.translate(x + w / 2, y + h / 2); g.scale(k, k); g.translate(-w / 2, -h / 2);
    g.fillStyle = col(K.surface, 1); rr(g, 0, 0, w, h, 18); g.fill(); g.strokeStyle = col(i % 2 ? K.acc : K.acc2, .9); g.lineWidth = 5; g.stroke(); g.save(); rr(g, 6, 6, w - 12, h - 12, 14); g.clip();
    if (i % 2 === 0) { g.strokeStyle = col(i ? K.down : K.up, 1); g.lineWidth = 6; g.beginPath(); for (let j = 0; j <= 30; j++) { const yy = h / 2 + Math.sin(j * .5 + t * 3 + s) * 40 + (i ? j * 2 : -j * 3) + Math.sin(j * 1.7 + s) * 14; if (!j) g.moveTo(14, yy); else g.lineTo(14 + j * (w - 28) / 30, yy); } g.stroke(); }
    else for (let j = 0; j < 14; j++) { const hh = 30 + hs(j + s * 5 + Math.floor(t * 3)) * (h - 90); g.fillStyle = col(hs(j + s) > .45 ? K.up : K.down, .85); g.fillRect(16 + j * ((w - 32) / 14), h - 16 - hh, (w - 32) / 14 - 6, hh); }
    g.restore(); g.restore();
  });
});
def("diana", (g, t, K) => {
  const cs = [K.text, K.down, K.text, K.down, K.res]; for (let i = 0; i < 5; i++) { g.fillStyle = col(cs[i], i === 4 ? 1 : .85); circ(g, 0, 0, 300 - i * 58); g.fill(); }
  const k = eo((t - .3) / .5), ax = mx(380, 0, k), ay = mx(-420, 0, k); if (t > .3) { g.save(); g.translate(ax, ay); g.rotate(-.9); g.fillStyle = col(K.acc, 1); g.fillRect(0, -6, 260, 12); g.fillStyle = "#fff"; g.beginPath(); g.moveTo(260, -20); g.lineTo(330, 0); g.lineTo(260, 20); g.fill(); g.restore(); }
  if (t > .75) chispas(g, t - .75, 14, K, 0, 0, 200, 0, K.res, 7, 1);
});
def("flechas_dir", (g, t, K) => {
  for (let i = 0; i < 5; i++) { const ph = (t * .8 + i / 5) % 1, x = -380 + i * 190, up = hs(i + 1) > .4; g.globalAlpha = Math.sin(ph * Math.PI); flecha(g, x, mx(up ? 330 : -330, up ? -330 : 330, ph), up ? -Math.PI / 2 : Math.PI / 2, 200, 56, up ? col(K.up, .95) : col(K.down, .95)); g.globalAlpha = 1; }
});
def("vela_gigante", (g, t, K) => {
  const k = eo(t / 1.1), c = K.up; gl(g, c, 50); g.fillStyle = c; g.fillRect(-10, -340 * k + 40, 20, 640 * k); g.fillStyle = vg(g, -200, 200, "#BFF5DA", c); rr(g, -110, mx(150, -170, k), 220, mx(0, 330, k), 14); g.fill(); ng(g);
  const q = eo((t - 1) / .5); g.strokeStyle = col(K.text, .9 * q); g.lineWidth = 5; g.setLineDash([14, 12]); [[-170, -330], [-170, 170], [-170, -170]].forEach(([x, y]) => { g.beginPath(); g.moveTo(x, y); g.lineTo(-480 + 150 * (1 - q), y); g.stroke(); }); g.setLineDash([]);
  chispas(g, t, 12, K, 0, -200, 280, 0, K.up);
});
def("flujo_monedas", (g, t, K) => {
  const yy = u => -80 + 160 * Math.sin(Math.min(u, .5) * Math.PI) - 160 * Math.sin(Math.max(u - .5, 0) * Math.PI);
  g.strokeStyle = col(K.border, 1); g.lineWidth = 8; g.beginPath(); for (let x = -440; x <= 440; x += 8) { const y = yy((x + 440) / 880); if (x === -440) g.moveTo(x, y); else g.lineTo(x, y); } g.stroke();
  for (let i = 0; i < 9; i++) { const p = (t * .28 + i / 9) % 1; moneda(g, mx(-440, 440, p), yy(p), 34, t * 4 + i, K, "$"); }
});
def("pilas_monedas", (g, t, K) => {
  const alt = [2, 3, 5, 7, 10, 13];
  alt.forEach((n, i) => { const x = -400 + i * 160, k = (t - .15 * i) / .9; for (let j = 0; j < n; j++) { const e = eb(k * n - j * .6); if (e <= 0) break; g.fillStyle = vg(g, 0, 40, K.res, "#B58626"); gl(g, col(K.warn, .4), 12); g.beginPath(); g.ellipse(x, 420 - j * 28 - (1 - e) * 80, 62, 20, 0, 0, TAU); g.fill(); ng(g); g.strokeStyle = col("#8A5E10", .6); g.lineWidth = 3; g.stroke(); } });
});
def("escalera", (g, t, K) => {
  for (let i = 0; i < 7; i++) { const k = eo((t - i * .12) / .5), x = -420 + i * 125, y = 380 - i * 100; g.fillStyle = vg(g, y, 500, col(K.acc, .95), col(K.acc2, .25)); g.fillRect(x - 55, y + (1 - k) * 160, 110, 560); g.fillStyle = col("#fff", .35 * k); g.fillRect(x - 55, y + (1 - k) * 160, 110, 8); }
  const p = cl((t - .6) / 1.8) * 6, i = Math.floor(p), f = p - i, x = mx(-420 + i * 125, -420 + Math.min(i + 1, 6) * 125, eo(f)), y = mx(380 - i * 100, 380 - Math.min(i + 1, 6) * 100, eo(f)) - 60 - Math.sin(f * Math.PI) * 50;
  gl(g, K.res, 30); g.fillStyle = K.res; circ(g, x, y, 34); g.fill(); ng(g);
});
def("pastel_reparto", (g, t, K) => {
  const trozos = [[.5, K.acc], [.3, K.acc2], [.2, K.res]]; let a0 = -Math.PI / 2;
  trozos.forEach(([v, c], i) => { const k = eb((t - .2 - i * .35) / .6), a1 = a0 + v * TAU, m = (a0 + a1) / 2, d = 26 * k; g.save(); g.translate(Math.cos(m) * d, Math.sin(m) * d); g.scale(.4 + .6 * k, .4 + .6 * k); g.fillStyle = col(c, .95); gl(g, col(c, .6), 30); g.beginPath(); g.moveTo(0, 0); g.arc(0, 0, 330, a0, a1); g.closePath(); g.fill(); ng(g); g.strokeStyle = K.bg; g.lineWidth = 10; g.stroke(); g.restore(); a0 = a1; });
});
def("engranajes", (g, t, K) => {
  const eng = (x, y, r, dientes, rot, c) => { g.save(); g.translate(x, y); g.rotate(rot); g.fillStyle = col(c, .95); gl(g, col(c, .5), 24); g.beginPath(); for (let i = 0; i < dientes * 2; i++) { const a = i * Math.PI / dientes, rr_ = i % 2 ? r * .82 : r; g.lineTo(Math.cos(a) * rr_, Math.sin(a) * rr_); } g.closePath(); g.fill(); ng(g); g.fillStyle = K.bg; circ(g, 0, 0, r * .32); g.fill(); g.restore(); };
  eng(-120, -80, 260, 14, t * .7, K.acc); eng(220, 190, 170, 10, -t * .7 * 1.4 + .2, K.acc2); eng(-290, 270, 110, 7, -t * .7 * 2.3, K.res);
});
def("globo_mundo", (g, t, K) => {
  const R = 330; g.strokeStyle = col(K.acc, .35); g.lineWidth = 3; circ(g, 0, 0, R + 10); g.stroke();
  for (let i = 0; i < 360; i++) { const la = Math.asin(1 - 2 * (i + .5) / 360), lo = i * 2.39996 + t * .7, x = Math.cos(la) * Math.sin(lo) * R, y = -Math.sin(la) * R, z = Math.cos(la) * Math.cos(lo); if (z < 0) continue; g.fillStyle = col(i % 9 === 0 ? K.res : K.acc, .25 + z * .75); circ(g, x, y, 3 + z * 4); g.fill(); }
  for (let i = 0; i < 4; i++) { const a0 = t * .7 + i * 1.7, a1 = a0 + 1.2, p = (t * .5 + i * .25) % 1; g.strokeStyle = col(K.res, .8 * Math.sin(p * Math.PI)); g.lineWidth = 6; g.beginPath(); g.arc(0, 0, R * 1.18 + i * 16, a0, a1); g.stroke(); }
});
def("multitud_moviles", (g, t, K) => {
  for (let fila = 0; fila < 3; fila++) for (let i = -5; i <= 5; i++) {
    const x = i * 95 + (fila % 2) * 45, y = 120 + fila * 140 + Math.sin(t * 2 + i + fila) * 5, s = 1 + fila * .25, c = fila === 0 ? col(K.acc2, .3) : fila === 1 ? col(K.acc2, .5) : col(K.surface, 1);
    g.fillStyle = c; circ(g, x, y - 60 * s, 34 * s); g.fill(); g.beginPath(); g.ellipse(x, y + 30 * s, 52 * s, 68 * s, 0, Math.PI, TAU); g.fill();
    if (hs(i + fila * 7) > .35) { g.fillStyle = col(hs(i * 3 + fila) > .5 ? K.res : K.acc, .6 + Math.sin(t * 4 + i) * .3); gl(g, K.acc, 22); rr(g, x + 14 * s, y - 140 * s, 24 * s, 42 * s, 5); g.fill(); ng(g); }
  }
  chispas(g, t, 24, K, 0, -120, 420, 1, K.acc2, 4, 1.8);
});
def("anzuelo", (g, t, K) => {
  const y = mx(-480, -60, eo(t / 1.1)) + Math.sin(t * 3) * 10; g.strokeStyle = col(K.muted, .8); g.lineWidth = 4; g.beginPath(); g.moveTo(0, -520); g.lineTo(0, y - 110); g.stroke();
  g.strokeStyle = "#D8E1EF"; g.lineWidth = 22; g.lineCap = "round"; gl(g, K.acc, 24); g.beginPath(); g.moveTo(0, y - 110); g.lineTo(0, y + 130); g.arc(-80, y + 130, 80, 0, Math.PI * .95); g.lineTo(-155, y + 90); g.stroke(); ng(g);
  moneda(g, -80, y + 150, 46 + Math.sin(t * 6) * 3, t * 2, K, "$");
  for (let i = 0; i < 3; i++) { const p = (t * .3 + i / 3) % 1, fx = mx(520, -300, p) * (i % 2 ? -1 : 1), fy = 200 + i * 120 + Math.sin(t * 4 + i) * 18; g.save(); g.translate(fx, fy); g.scale(i % 2 ? -1 : 1, 1); g.fillStyle = col(K.acc, .55); g.beginPath(); g.ellipse(0, 0, 70, 30, 0, 0, TAU); g.fill(); g.beginPath(); g.moveTo(70, 0); g.lineTo(115, -28); g.lineTo(115, 28); g.fill(); g.fillStyle = K.bg; circ(g, -38, -6, 5); g.fill(); g.restore(); }
});
def("interrogante", (g, t, K) => {
  for (let i = 0; i < 8; i++) { const a = t * .9 + i * TAU / 8; g.fillStyle = col(i % 2 ? K.acc : K.res, .7); gl(g, K.acc, 16); circ(g, Math.cos(a) * 330, Math.sin(a) * 330 * .55 + 20, 12 + Math.sin(t * 3 + i) * 4); g.fill(); ng(g); }
  g.fillStyle = vg(g, -300, 300, "#FFFFFF", K.acc); gl(g, K.acc, 60 + Math.sin(t * 4) * 20); g.font = "700 760px InterW, sans-serif"; g.textAlign = "center"; g.textBaseline = "middle"; const k = eb(t / .6); g.save(); g.scale(k, k); g.fillText("?", 0, 40); g.restore(); ng(g);
});
def("exclamacion", (g, t, K) => {
  for (let i = 0; i < 3; i++) { const ph = (t * .9 + i / 3) % 1; g.strokeStyle = col(K.down, (1 - ph) * .7); g.lineWidth = 10; g.beginPath(); g.arc(0, 0, 200 + ph * 300, 0, TAU); g.stroke(); }
  const k = eb(t / .5); g.save(); g.scale(k, k); gl(g, K.down, 60); g.fillStyle = vg(g, -300, 300, "#FFE3E3", K.down); rr(g, -60, -330, 120, 410, 56); g.fill(); circ(g, 0, 200, 72); g.fill(); ng(g); g.restore();
});
def("noticias", (g, t, K) => {
  for (let i = 0; i < 5; i++) { const k = eb((t - i * .22) / .5), x = -250 + i * 125, y = -200 + i * 80, r = (i - 2) * .09; g.save(); g.translate(x, y + (1 - k) * 600); g.rotate(r); g.fillStyle = col(i % 2 ? K.surface : K.raised, 1); gl(g, "rgba(0,0,0,.5)", 28); rr(g, -190, -130, 380, 260, 22); g.fill(); ng(g); g.strokeStyle = col(K.border, 1); g.lineWidth = 3; g.stroke();
    g.fillStyle = col([K.acc, K.res, K.up, K.down, K.acc2][i], .95); g.fillRect(-160, -102, 120, 74); g.fillStyle = col(K.text, .85); g.fillRect(-20, -100, 170, 20); g.fillRect(-20, -66, 130, 14); g.fillRect(-160, 10, 300, 12); g.fillRect(-160, 44, 250, 12); g.fillRect(-160, 78, 280, 12); g.restore(); }
});
def("burbuja", (g, t, K) => {
  const k = cl(t / 2), r = mx(40, 300, eo(k)), pop = t > 2.1, wob = Math.sin(t * 9) * (4 + k * 10);
  if (!pop) { g.save(); g.translate(wob, 0); g.strokeStyle = col(K.acc, .95); g.lineWidth = 8; gl(g, K.acc, 36); g.fillStyle = rg(g, -r * .3, -r * .3, r * .05, r, col("#fff", .35), col(K.acc2, .12)); circ(g, 0, 0, r); g.fill(); g.stroke(); ng(g); g.fillStyle = col("#fff", .75); g.beginPath(); g.ellipse(-r * .4, -r * .45, r * .14, r * .08, -.6, 0, TAU); g.fill(); g.restore(); }
  else { const p = (t - 2.1) / .9; for (let i = 0; i < 40; i++) { const a = i * TAU / 40, d = 300 + p * 320 * (.6 + hs(i) * .6); g.fillStyle = col(i % 2 ? K.acc : K.acc2, cl(1 - p)); circ(g, Math.cos(a) * d, Math.sin(a) * d, 12 * (1 - p) + 2); g.fill(); } g.strokeStyle = col(K.acc, cl(1 - p * 1.6)); g.lineWidth = 10; circ(g, 0, 0, 300 + p * 120); g.stroke(); }
});
def("banco", (g, t, K) => {
  const k = eo(t / .9); g.fillStyle = col(K.acc, .95); g.beginPath(); g.moveTo(-380, -110); g.lineTo(0, -330 * k + 0); g.lineTo(380, -110); g.closePath(); g.fill();
  for (let i = 0; i < 5; i++) { const e = eo((t - .3 - i * .1) / .6), x = -290 + i * 145; g.fillStyle = vg(g, -100, 280, "#FFFFFF", K.muted); g.fillRect(x - 38, 280 - 380 * e, 76, 380 * e); }
  g.fillStyle = col(K.acc2, .95); g.fillRect(-400, 290, 800, 50); g.fillRect(-430, 340, 860, 40);
  g.fillStyle = col(K.bg, .9); circ(g, 0, -170, 36); g.fill(); moneda(g, 0, -170, 28, t * 3, K, "$");
});
def("dominos", (g, t, K) => {
  const n = 10, base = 260, ancho = 56, alto = 270, paso = 92, caida = i => cl((t - .25 - i * .27) / .62);
  g.fillStyle = col(K.border, 1); g.fillRect(-500, base, 1000, 12);
  for (let i = 0; i < n; i++) {
    const x = -430 + i * paso, k = caida(i), a = (k * k * (3 - 2 * k)) * 1.38, c = k > 0 ? K.down : K.acc2;
    g.save(); g.translate(x + ancho / 2, base); g.rotate(a); g.translate(-ancho / 2, 0); g.fillStyle = col(c, .95); gl(g, col(c, .6), 20); rr(g, -ancho / 2, -alto, ancho, alto, 8); g.fill(); ng(g);
    g.fillStyle = col(K.bg, .55); for (let j = 1; j <= 3; j++) { circ(g, 0, -alto + j * 62, 8); g.fill(); } g.restore();
  }
});
def("blockchain", (g, t, K) => {
  const n = 4; for (let i = 0; i < n; i++) {
    const x = -425 + i * 230, k = eb((t - i * .3) / .5); g.save(); g.translate(x + 80, 0); g.scale(k, k); g.translate(-80, 0);
    gl(g, col(K.acc, .6), 24); g.fillStyle = col(K.surface, 1); rr(g, 0, -140, 160, 280, 24); g.fill(); g.strokeStyle = col(K.acc, 1); g.lineWidth = 7; g.stroke(); ng(g);
    g.fillStyle = col(K.acc2, .9); g.fillRect(24, -105, 112, 18); g.fillStyle = col(K.muted, .7); g.fillRect(24, -60, 90, 12); g.fillRect(24, -30, 100, 12); g.fillRect(24, 0, 70, 12); g.fillStyle = col(hs(i) > .5 ? K.up : K.res, 1); circ(g, 80, 80, 22); g.fill(); g.restore();
    if (i < n - 1) { const p = cl((t - i * .3 - .35) / .3); g.strokeStyle = col(K.acc, .95); g.lineWidth = 9; g.beginPath(); g.moveTo(x + 160, 0); g.lineTo(x + 160 + 70 * p, 0); g.stroke(); const q = (t * .9 + i * .3) % 1; if (p >= 1) { g.fillStyle = "#fff"; gl(g, K.acc, 20); circ(g, x + 160 + 70 * q, 0, 8); g.fill(); ng(g); } }
  }
});
def("red_nodos", (g, t, K) => {
  const N = []; for (let i = 0; i < 20; i++) N.push([Math.cos(i * 2.4 + t * .15 * (i % 2 ? 1 : -1)) * (130 + (i % 5) * 80), Math.sin(i * 2.4 + t * .15 * (i % 2 ? 1 : -1)) * (130 + (i % 5) * 80) * .95]);
  N.forEach((a, i) => N.forEach((b, j) => { if (j > i && Math.hypot(a[0] - b[0], a[1] - b[1]) < 300) { g.strokeStyle = col(K.acc, .4); g.lineWidth = 3; g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); const p = (t * .7 + hs(i + j)) % 1; g.fillStyle = K.res; circ(g, mx(a[0], b[0], p), mx(a[1], b[1], p), 5); g.fill(); } }));
  N.forEach((a, i) => { gl(g, K.acc, 22); g.fillStyle = i % 5 === 0 ? K.res : K.acc; circ(g, a[0], a[1], 16 + Math.sin(t * 4 + i) * 3); g.fill(); ng(g); });
});
def("matriz", (g, t, K) => {
  g.font = "700 38px PlexW, monospace"; g.textAlign = "center"; const letras = "01ABCDEF$€";
  for (let c = -12; c <= 12; c++) for (let r = 0; r < 20; r++) { const v = 1 + hs(c + 30) * 1.5, y = -520 + (((t * 220 * v + hs(c) * 1400) % 1500) - r * 46); if (y < -520 || y > 520) continue; const a = r === 0 ? 1 : Math.max(0, 1 - r / 14); g.fillStyle = r === 0 ? "#fff" : col(K.up, a * .8); g.fillText(letras[Math.floor(hs(c * 7 + r + Math.floor(t * 6)) * letras.length)], c * 40, y); }
});
def("candado", (g, t, K) => {
  const ab = eo((t - 1.1) / .5), glitch = t > 1.0 && t < 1.7;
  g.save(); if (glitch) g.translate((hs(Math.floor(t * 40)) - .5) * 26, 0);
  g.strokeStyle = col(K.muted, 1); g.lineWidth = 46; g.lineCap = "round"; g.beginPath(); g.arc(0, -90 - ab * 60, 130, Math.PI, 0); g.lineTo(130, -90 - ab * 60 + (ab > .5 ? 0 : 120)); g.stroke();
  gl(g, glitch ? K.down : K.acc, 40); g.fillStyle = vg(g, -80, 300, glitch ? K.down : K.acc, col(K.acc2, .7)); rr(g, -190, -80, 380, 330, 40); g.fill(); ng(g);
  g.fillStyle = col(K.bg, .9); circ(g, 0, 70, 38); g.fill(); g.fillRect(-12, 80, 24, 80); g.restore();
  if (glitch) for (let i = 0; i < 6; i++) { g.fillStyle = col(K.down, .5); g.fillRect(-300, -300 + hs(i + Math.floor(t * 30)) * 600, 600, 8 + hs(i) * 14); }
});
def("bitcoin", (g, t, K) => {
  const rot = t * 2.6, cs = Math.cos(rot), a = Math.abs(cs); moneda(g, 0, 0, 240, rot, K, "");
  if (a > .35) { g.save(); g.scale(a, 1); g.fillStyle = col("#7A520C", .95); g.font = "700 300px InterW, sans-serif"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("B", 0, 14); g.fillRect(-26, -170, 14, 60); g.fillRect(14, -170, 14, 60); g.fillRect(-26, 110, 14, 60); g.fillRect(14, 110, 14, 60); g.restore(); }
  for (let i = 0; i < 3; i++) { const ph = (t * .7 + i / 3) % 1; g.strokeStyle = col(K.warn, (1 - ph) * .6); g.lineWidth = 7; circ(g, 0, 0, 260 + ph * 220); g.stroke(); }
});
def("ballena", (g, t, K) => {
  const y = Math.sin(t * 1.8) * 26, tail = Math.sin(t * 3.2) * .2;
  for (let i = 0; i < 6; i++) { const p = (t * .7 + i / 6) % 1; g.fillStyle = col(K.acc, (1 - p) * .35); circ(g, -380 + hs(i) * 760, 400 - p * 800, 10 + hs(i + 3) * 14); g.fill(); }
  g.save(); g.translate(0, y); gl(g, K.acc, 44); g.fillStyle = vg(g, -170, 140, col(K.acc, 1), col(K.acc2, .8));
  g.beginPath(); g.moveTo(-340, 10); g.bezierCurveTo(-340, -130, -130, -190, 110, -130); g.bezierCurveTo(200, -105, 250, -70, 290, -50);
  g.save(); g.translate(290, -50); g.rotate(tail); g.bezierCurveTo(10, -20, 40, -90, 30, -160); g.bezierCurveTo(60, -120, 100, -130, 140, -150); g.bezierCurveTo(130, -70, 100, -10, 40, 30); g.bezierCurveTo(80, 40, 120, 90, 150, 100); g.bezierCurveTo(100, 110, 40, 80, 0, 50); g.restore();
  g.bezierCurveTo(230, 20, 150, 90, 30, 110); g.bezierCurveTo(-140, 130, -340, 90, -340, 10); g.fill(); ng(g);
  g.fillStyle = col("#fff", .22); g.beginPath(); g.moveTo(-320, 50); g.bezierCurveTo(-200, 100, 60, 100, 190, 20); g.bezierCurveTo(60, 70, -200, 60, -320, 50); g.fill();
  g.fillStyle = K.bg; circ(g, -230, -20, 13); g.fill(); g.restore();
  g.strokeStyle = col("#fff", .8); g.lineWidth = 8; g.lineCap = "round"; for (let i = 0; i < 3; i++) { const p = (t * 1.1 + i / 3) % 1; g.globalAlpha = Math.sin(p * Math.PI); g.beginPath(); g.moveTo(-190 + (i - 1) * 24, -190 + y - p * 80); g.lineTo(-190 + (i - 1) * 54, -240 + y - p * 130); g.stroke(); } g.globalAlpha = 1;
});
def("onda_audio", (g, t, K) => {
  for (let i = -24; i <= 24; i++) { const h = 30 + (Math.sin(i * .5 + t * 6) * .5 + .5) * 240 * (.4 + hs(i + 40 + Math.floor(t * 5)) * .8) * Math.exp(-Math.abs(i) / 30); g.fillStyle = i < 0 ? col(K.acc2, .95) : col(K.res, .95); gl(g, g.fillStyle, 14); rr(g, i * 20 - 6, -h, 12, h * 2, 6); g.fill(); ng(g); }
});

// Envoltorio común: halo de color, entrada suave, empuje de cámara lento y polvo flotante. Todo depende solo de t.
export function dibujar(id, g, w, h, t, K, opciones = {}) {
  const f = MOTIVOS[id]; if (!f) throw new Error("motivo desconocido: " + id);
  g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, w, h); g.save(); g.translate(w / 2, h / 2);
  const s = Math.min(w, h) / 1000 * (opciones.escala || 1), ent = eb(t / .45), zoom = 1 + cl(t / 6) * .05;
  g.scale(s * (.9 + .1 * ent) * zoom, s * (.9 + .1 * ent) * zoom); g.globalAlpha = cl(t / .25);
  g.fillStyle = rg(g, 0, 0, 40, 520, col(opciones.halo || K.acc, .22 + Math.sin(t * 2) * .03), "rgba(0,0,0,0)"); g.fillRect(-600, -600, 1200, 1200);
  for (let i = 0; i < 26; i++) { const ph = (t * (.04 + hs(i) * .05) + hs(i + 7)) % 1; g.fillStyle = col(K.text, .16 * Math.sin(ph * Math.PI)); circ(g, (hs(i + 2) - .5) * 1100 + Math.sin(t + i) * 14, 520 - ph * 1040, 2 + hs(i + 5) * 3); g.fill(); }
  g.save(); f(g, t, K); g.restore(); g.restore();
}
