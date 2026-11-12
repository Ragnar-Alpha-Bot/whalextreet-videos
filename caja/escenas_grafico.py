"""Gráfico profesional con DATOS REALES: «grafico_pro» (línea, área o velas japonesas) con la librería TradingView Lightweight Charts
(Apache 2.0, v4.2.0 incluida en marca/; exige mostrar su atribución, y la escena la pone siempre al pie).

La librería pinta en un contenedor oculto y la escena copia cada fotograma a su propio <canvas> con takeScreenshot(): así el dibujo depende SOLO del
tiempo del vídeo (evento hf-seek de HyperFrames), no del reloj del navegador, y sale igual en cualquier ordenador.

Estructura de la escena:
  {"tipo": "grafico_pro", "titulo": "máx. 44", "modo": "area|linea|velas",
   "puntos": [2 a 260 números]            # modo area o linea (cierres diarios, por ejemplo)
   "velas": [{"o":..,"h":..,"l":..,"c":..}] (2 a 150)   # modo velas
   "etiquetas": ["inicio", "fin"], "unidad": "", "zoom": true|false,
   "anotaciones": [{"i": posición, "texto": "máx. 28", "cuando": "palabra"}] (0 a 3)}

Las cifras visibles (primer y último valor, anotaciones) deben estar en el post o en sus datos (caja/fidelidad.py). No se dibujan los ejes de precios
a propósito: los números de los ejes serían cifras que no salen del post.
"""
import json

from escenas import ESCENAS, _num, _txt, es, esc, fromTo

MAX_PUNTOS, MAX_VELAS = 260, 150


def _canvas(c, ident, alto_px):
    """Igual que en escenas3d.py (no se importa de allí para evitar un import circular)."""
    w, h = int(c.W), c.n(alto_px)
    return w, h, f'<canvas id="{ident}" width="{w}" height="{h}" style="display:block;width:{w}px;height:{h}px"></canvas>'

LW = """
await document.fonts.load('700 40px InterW');
const cv = document.getElementById("__CV__"), ctx = cv.getContext("2d");
const D = __DATOS__;
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim() || "#ffffff";
const ease = {out: k => 1 - Math.pow(1 - k, 3), inout: k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2};
const clamp = k => Math.min(Math.max(k, 0), 1);
const col = css(D.sube ? "--up" : "--down");
const chart = LightweightCharts.createChart(document.getElementById("__LW__"), {
  width: __W__, height: __H__,
  layout: {background: {type: "solid", color: "rgba(0,0,0,0)"}, textColor: css("--muted"), fontFamily: "InterW"},
  grid: {vertLines: {color: "rgba(160,180,210,.07)"}, horzLines: {color: "rgba(160,180,210,.10)"}},
  rightPriceScale: {visible: false, scaleMargins: {top: .12, bottom: .1}}, leftPriceScale: {visible: false},
  timeScale: {visible: false, rightOffset: 0, fixLeftEdge: true, fixRightEdge: true},
  crosshair: {mode: 0, vertLine: {visible: false}, horzLine: {visible: false}},
  handleScroll: false, handleScale: false, localization: {locale: "es-ES"},
});
const t0u = Date.UTC(2020, 0, 1) / 1000, DIA = 86400;
const N = D.n;
let serie;
if (D.modo === "velas") {
  serie = chart.addCandlestickSeries({upColor: css("--up"), downColor: css("--down"), borderVisible: false, wickUpColor: css("--up"), wickDownColor: css("--down"), lastValueVisible: false, priceLineVisible: false});
} else if (D.modo === "linea") {
  serie = chart.addLineSeries({color: col, lineWidth: 5, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false});
} else {
  serie = chart.addAreaSeries({lineColor: col, lineWidth: 5, topColor: col + "66", bottomColor: col + "00", lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false});
}
const invisible = () => chart.addLineSeries({color: "rgba(0,0,0,0)", lineWidth: 1, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false});
const todos = D.modo === "velas" ? D.velas.map((v, i) => ({time: t0u + i * DIA, open: v[0], high: v[1], low: v[2], close: v[3]})) : D.puntos.map((v, i) => ({time: t0u + i * DIA, value: v}));
// series invisibles con TODOS los datos: fijan la escala vertical (y la reajustan al hacer zoom) mientras la serie visible se va dibujando
if (D.modo === "velas") { invisible().setData(todos.map(x => ({time: x.time, value: x.high}))); invisible().setData(todos.map(x => ({time: x.time, value: x.low}))); }
else { invisible().setData(todos); }
let listo = false, ultimo = window.__hfThreeTime ?? 0;
function frame(t) {
  const k = ease.out(clamp((t - D.t0) / D.dur2)), n = Math.max(2, Math.round(k * N));
  serie.setData(todos.slice(0, n));
  let desde = 0;
  if (D.zoom) { const z = ease.inout(clamp((t - D.t0 - D.dur2 - .3) / .9)); desde = z * (N - 1) * .62; }
  chart.timeScale().setVisibleLogicalRange({from: desde, to: N - 1 + .5});
  const shot = chart.takeScreenshot();
  ctx.clearRect(0, 0, cv.width, cv.height); ctx.drawImage(shot, 0, 0, cv.width, cv.height);
  D.notas.forEach(a => {   // anotaciones: etiqueta grande (se lee en el móvil) sobre el punto, con una flecha
    if (t < a.t || a.i > n - 1) return;
    const x = chart.timeScale().timeToCoordinate(todos[a.i].time), y = serie.priceToCoordinate(D.modo === "velas" ? todos[a.i].high : todos[a.i].value);
    if (x == null || y == null) return;
    const k = ease.out(clamp((t - a.t) / .35));
    ctx.save(); ctx.globalAlpha = k; ctx.font = "700 36px InterW";
    const w = ctx.measureText(a.texto).width + 40, h = 60, bx = Math.min(Math.max(x - w / 2, 8), cv.width - w - 8), by = Math.max(y - 26 - h - (1 - k) * 22, 4);
    ctx.fillStyle = css("--warn"); ctx.beginPath(); ctx.roundRect(bx, by, w, h, 14); ctx.fill();
    ctx.beginPath(); ctx.moveTo(x - 12, by + h - 1); ctx.lineTo(x + 12, by + h - 1); ctx.lineTo(x, by + h + 16); ctx.closePath(); ctx.fill();
    ctx.fillStyle = "#0B1020"; ctx.textBaseline = "middle"; ctx.textAlign = "center"; ctx.fillText(a.texto, bx + w / 2, by + h / 2 + 2); ctx.restore();
  });
}
function dibujar(t) { ultimo = t; if (!listo) return; frame(t); }
window.addEventListener("hf-seek", e => dibujar(e.detail?.time ?? window.__hfThreeTime ?? 0));
listo = true; dibujar(ultimo);
"""


def v_grafico_pro(d, err):
    _txt(d, "titulo", err, 44)
    modo = d.get("modo", "area")
    if modo not in ("area", "linea", "velas"):
        err("«modo» debe ser area, linea o velas")
        return
    if modo == "velas":
        v = d.get("velas")
        if not isinstance(v, list) or not (2 <= len(v) <= MAX_VELAS):
            err(f"«velas» debe ser una lista de 2 a {MAX_VELAS} velas")
        else:
            for k, x in enumerate(v):
                if not isinstance(x, dict) or not all(_num(x.get(c)) for c in "ohlc") or x["h"] < max(x["o"], x["c"]) or x["l"] > min(x["o"], x["c"]):
                    err(f"la vela {k + 1} no es válida (hacen falta o, h, l, c con h ≥ máximo y l ≤ mínimo)")
                    break
    else:
        p = d.get("puntos")
        if not isinstance(p, list) or not (2 <= len(p) <= MAX_PUNTOS) or not all(_num(x) for x in p):
            err(f"«puntos» debe ser una lista de 2 a {MAX_PUNTOS} números")
    n = len(d.get("velas") if modo == "velas" and isinstance(d.get("velas"), list) else d.get("puntos") if isinstance(d.get("puntos"), list) else [])
    et = d.get("etiquetas")
    if et is not None and (not isinstance(et, list) or len(et) != 2 or not all(isinstance(x, str) and len(x) <= 16 for x in et)):
        err("«etiquetas» debe ser una lista de 2 textos de hasta 16 caracteres")
    _txt(d, "unidad", err, 4, req=False)
    an = d.get("anotaciones", [])
    if not isinstance(an, list) or len(an) > 3:
        err("«anotaciones» admite hasta 3")
        return
    for a in an:
        if not isinstance(a, dict) or not isinstance(a.get("texto"), str) or not (1 <= len(a["texto"]) <= 28) or not isinstance(a.get("i"), int) or not (0 <= a["i"] < max(n, 1)):
            err("cada anotación necesita «i» (posición válida) y «texto» de hasta 28 caracteres")
            break


def e_grafico_pro(c, d):
    modo = d.get("modo", "area")
    if modo == "velas":
        vel = [[x["o"], x["h"], x["l"], x["c"]] for x in d["velas"]]
        primero, ultimo, n = vel[0][0], vel[-1][3], len(vel)
        datos = {"velas": vel}
    else:
        primero, ultimo, n = d["puntos"][0], d["puntos"][-1], len(d["puntos"])
        datos = {"puntos": d["puntos"]}
    dur2 = max(2.0, min(c.dur * .7, 6.0))
    notas = [{"i": a["i"], "texto": a["texto"], "t": c.T(a.get("cuando"), min(.35 + .2 * k, .9))} for k, a in enumerate(d.get("anotaciones", []))]
    datos.update({"modo": modo, "n": n, "sube": ultimo >= primero, "notas": notas, "zoom": bool(d.get("zoom")), "t0": round(c.t0 + .15, 2), "dur2": round(dur2, 2)})
    unidad = d.get("unidad", "")
    fmt = lambda v: es(v, 2 if v != int(v) and abs(v) < 1000 else 0) + unidad
    ident, lw = f"{c.pf}cv", f"{c.pf}lw"
    w, h, canvas = _canvas(c, ident, 800)
    et = d.get("etiquetas")
    col = "var(--up)" if ultimo >= primero else "var(--down)"
    html = (f'<div class="col" style="justify-content:center;align-items:center">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;align-self:stretch"><div class="lab" style="font-size:{c.fs(34)}">{esc(d["titulo"])}</div>'
            f'<div id="{c.pf}fin" class="h" style="font-weight:700;font-size:{c.fs(60)};color:{col}">{esc(fmt(ultimo))}</div></div>'
            f'<div style="position:relative;width:{w}px;height:{h}px">'
            f'<div id="{lw}" data-layout-ignore style="position:absolute;left:0;top:0;width:{w}px;height:{h}px;opacity:0;pointer-events:none"></div>{canvas}</div>'
            + (f'<div style="display:flex;justify-content:space-between;align-self:stretch;font-size:{c.fs(30)};color:var(--muted);font-weight:600"><span>{esc(et[0])}</span><span>{esc(et[1])}</span></div>' if et else "")
            + f'<div style="align-self:stretch;margin-top:{c.px(10)};font-size:{c.fs(28)};color:var(--muted);font-weight:600">Gráfico: TradingView Lightweight Charts™ · tradingview.com</div></div>'
            + '<script src="./assets/lightweight-charts.standalone.production.js"></script>'
            + '<script type="module">' + LW.replace("__CV__", ident).replace("__LW__", lw).replace("__W__", str(w)).replace("__H__", str(h))
            .replace("__DATOS__", json.dumps(datos, ensure_ascii=False)) + "</script>")
    js = [fromTo(f"#{c.pf}fin", {"opacity": 0, "y": 20}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, c.t0 + .15 + dur2)]
    c.snd(c.t0 + .15, "swipe", .4)
    c.snd(c.t0 + .15 + dur2, "ding:1", .4)
    return html, js


ESCENAS.update({"grafico_pro": (e_grafico_pro, v_grafico_pro)})
