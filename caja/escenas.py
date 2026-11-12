"""Escenas de la caja de herramientas de WhaleXtreet.

Cada escena es una función  e_<tipo>(ctx, d) -> (html, js, eventos_de_sonido)  más un validador  v_<tipo>(d, err).
El motor (motor.py) las coloca según el guion de escenas (storyboard) y la voz. Las apariciones se enganchan a palabras de la
locución con el campo "cuando" (una palabra de la voz); si no existe, se reparten a lo largo de la frase.

Escenas: titulo, numero, grafico, barras, donut, lista, tarjetas, pregunta
"""
import html as _html
import json
import math
import re
import unicodedata
from pathlib import Path

J = lambda d: json.dumps(d, separators=(",", ":"), ensure_ascii=False)
r2 = lambda x: round(float(x), 2)
_ACENTO = re.compile(r"\*([^*\n]{1,40})\*")


def esc(s):
    """Escapa el texto para HTML. Lo que va entre asteriscos (*palabra*) sale en cursiva serif con el color de acento (recurso de estilo, usar con cuentagotas)."""
    t = re.sub(r"(\d) %", "\\1\u00a0%", _html.escape(str(s), quote=False))      # el «%» no se queda solo en otra línea
    return _ACENTO.sub(r'<em class="ac">\1</em>', t)


def es(n, dec=0):
    s = f"{abs(n):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if n < 0 else "") + s


def norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


class Ctx:
    """Datos de una escena: tiempos, tamaño disponible, paleta y palabras de su locución."""

    def __init__(self, i, t0, t1, l0, l1, words, W, H, p):
        self.i, self.t0, self.t1, self.l0, self.l1, self.words, self.W, self.H, self.p = i, t0, t1, l0, l1, words, W, H, p
        self.pf = f"s{i}_"
        self.u = W / 984
        self.dur = l1 - l0
        self.ev, self.avisos = [], []
        self.proyecto = None                  # carpeta del proyecto (la pone el motor; lo usa «captura» para comprobar su imagen)

    def px(self, n):
        return f"{round(n * self.u)}px"

    def n(self, v):
        return round(v * self.u)

    def T(self, x, frac=0.5):
        """Segundo absoluto: una palabra de la voz (str), una fracción 0-1 de la frase (número) o la fracción por defecto."""
        if isinstance(x, str) and x.strip():
            for w in self.words:
                if norm(w["t"]) == norm(x):
                    return r2(self.l0 + w["ini"])
            self.avisos.append(f"escena {self.i}: la palabra «{x}» no está en la voz; se reparte a lo largo de la frase")
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            frac = min(max(float(x), 0.0), 1.0)
        return r2(self.l0 + frac * self.dur)

    def snd(self, t, clave, vol=0.4):
        self.ev.append((r2(t), clave, vol))


def fromTo(sel, a, b, t):
    return f'tl.fromTo("{sel}",{J(a)},{J(b)},{r2(t)});'


def to(sel, b, t):
    return f'tl.to("{sel}",{J(b)},{r2(t)});'


def chip(c, texto, idn, tamano=30, tono="acc"):
    return (f'<span class="chip h" id="{idn}" style="font-size:{c.px(tamano)};--c:var(--{tono})">{esc(texto)}</span>')


# ---------------------------------------------------------------------------------------------------------------------
# Validación (ayudantes)
# ---------------------------------------------------------------------------------------------------------------------
def _txt(d, k, err, max_=60, req=True):
    v = d.get(k)
    if v is None or v == "":
        if req:
            err(f"falta «{k}»")
        return
    if not isinstance(v, str):
        err(f"«{k}» debe ser texto")
    elif len(v) > max_:
        err(f"«{k}» es demasiado largo ({len(v)} > {max_} caracteres)")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _items(d, k, err, lo, hi):
    it = d.get(k)
    if not isinstance(it, list) or not (lo <= len(it) <= hi):
        err(f"«{k}» debe ser una lista de {lo} a {hi} elementos")
        return []
    return it


# ---------------------------------------------------------------------------------------------------------------------
# 1 · TÍTULO
# ---------------------------------------------------------------------------------------------------------------------
def v_titulo(d, err):
    _txt(d, "titulo", err, 48)
    _txt(d, "subtitulo", err, 70, req=False)
    _txt(d, "etiqueta", err, 24, req=False)


def e_titulo(c, d):
    t = d["titulo"]
    n = len(t)
    fs = 150 if n <= 14 else 122 if n <= 24 else 100 if n <= 36 else 84
    ws = t.split()
    spans = "".join(f'<span class="tw" id="{c.pf}w{j}" style="display:inline-block;margin:0 .14em;opacity:0">{esc(w)}</span>' for j, w in enumerate(ws))
    sub = d.get("subtitulo")
    html = (f'<div class="col" style="align-items:center;justify-content:center;text-align:center;gap:{c.px(36)}">'
            + (chip(c, d["etiqueta"], c.pf + "chip") if d.get("etiqueta") else "")
            + f'<div class="big" style="font-size:{c.px(fs)}">{spans}</div>'
            + f'<div id="{c.pf}ln" class="linea" style="width:{c.px(280)}"></div>'
            + (f'<div class="nota h" id="{c.pf}sub" style="font-size:{c.px(46)}">{esc(sub)}</div>' if sub else "") + '</div>')
    js, t0 = [], c.t0
    if d.get("etiqueta"):
        js.append(fromTo(f"#{c.pf}chip", {"opacity": 0, "scale": .6}, {"opacity": 1, "scale": 1, "duration": .4, "ease": "back.out(2.4)"}, t0 + .2))
        c.snd(t0 + .2, "pop:0", .45)
    for j in range(len(ws)):
        js.append(fromTo(f"#{c.pf}w{j}", {"opacity": 0, "y": 70}, {"opacity": 1, "y": 0, "duration": .5, "ease": "back.out(1.7)"}, t0 + .35 + .13 * j))
    c.snd(t0 + .35, "impact", .5)
    js.append(fromTo(f"#{c.pf}ln", {"scaleX": 0}, {"scaleX": 1, "duration": .5, "ease": "power3.out", "transformOrigin": "center"}, t0 + .5 + .13 * len(ws)))
    c.snd(t0 + .5 + .13 * len(ws), "swipe", .3)
    if sub:
        js.append(fromTo(f"#{c.pf}sub", {"opacity": 0, "y": 24}, {"opacity": 1, "y": 0, "duration": .5, "ease": "power3.out"}, t0 + 1.0 + .13 * len(ws)))
        c.snd(t0 + 1.0 + .13 * len(ws), "pop:2", .3)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# 2 · NÚMERO GIGANTE
# ---------------------------------------------------------------------------------------------------------------------
def v_numero(d, err):
    if not _num(d.get("valor")):
        err("«valor» debe ser un número")
    for k in ("decimales",):
        if k in d and (not isinstance(d[k], int) or not 0 <= d[k] <= 3):
            err("«decimales» debe ser un entero de 0 a 3")
    if "desde" in d and not _num(d["desde"]):
        err("«desde» debe ser un número")
    if "delta" in d and not _num(d["delta"]):
        err("«delta» debe ser un número")
    for k in ("prefijo", "sufijo"):
        _txt(d, k, err, 6, req=False)
    _txt(d, "etiqueta", err, 44, req=False)
    _txt(d, "detalle", err, 50, req=False)


def e_numero(c, d):
    dec = d.get("decimales", 0)
    pre, suf = d.get("prefijo", ""), d.get("sufijo", "")
    v, v0 = d["valor"], d.get("desde", 0)
    final = pre + es(v, dec) + suf
    fs = min(300, 1480 / max(len(final), 1))
    ide = f"{c.pf}num"
    html = (f'<div class="col" style="align-items:center;justify-content:center;text-align:center;gap:{c.px(24)}">'
            + (f'<div class="lab h" id="{c.pf}lab" style="font-size:{c.px(34)}">{esc(d["etiqueta"])}</div>' if d.get("etiqueta") else "")
            + f'<div class="big" id="{ide}" style="font-size:{c.px(fs)};color:var(--acc);line-height:1">{esc(pre + es(v0, dec) + suf)}</div>'
            + (f'<div class="pildora h" id="{c.pf}det" style="font-size:{c.px(40)}">{esc(d["detalle"])}</div>' if d.get("detalle") else "")
            + (f'<div class="chip h" id="{c.pf}dl" style="font-size:{c.px(44)};--c:var(--{"up" if d["delta"] >= 0 else "down"})">'
               f'{"▲ +" if d["delta"] >= 0 else "▼ −"}{es(abs(d["delta"]), 1)} {esc(d.get("delta_unidad", "%"))}</div>' if "delta" in d else "") + '</div>')
    t = c.T(d.get("cuando"), 0.18)
    dur = 1.5
    js = []
    if d.get("etiqueta"):
        js.append(fromTo(f"#{c.pf}lab", {"opacity": 0, "y": -20}, {"opacity": 1, "y": 0, "duration": .4, "ease": "power3.out"}, c.t0 + .2))
        c.snd(c.t0 + .2, "pop:2", .35)
    js.append(f'const {c.pf}o={{v:{v0}}};tl.to({c.pf}o,{{v:{v},duration:{dur},ease:"power2.out",onUpdate(){{document.getElementById("{ide}").textContent={J(pre)}+fm({c.pf}o.v,{dec})+{J(suf)}}}}},{t});')
    js.append(fromTo(f"#{ide}", {"opacity": 0, "scale": .92}, {"opacity": 1, "scale": 1, "duration": .5, "ease": "back.out(2)"}, max(t - .15, c.t0 + .3)))
    js.append(fromTo(f"#{ide}", {"scale": 1}, {"scale": 1.06, "duration": .14, "yoyo": True, "repeat": 1, "ease": "power2.out", "immediateRender": False}, t + dur))
    for k in range(int(dur / .1)):
        c.snd(t + .1 * k, "tick", .16 + .12 * k / (dur / .1))
    c.snd(t + dur, "ding:1", .4)
    if d.get("detalle"):
        js.append(fromTo(f"#{c.pf}det", {"opacity": 0, "y": 24}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, t + dur + .15))
        c.snd(t + dur + .15, "card", .4)
    if "delta" in d:
        js.append(fromTo(f"#{c.pf}dl", {"opacity": 0, "scale": .5}, {"opacity": 1, "scale": 1, "duration": .4, "ease": "back.out(3)"}, t + dur + .45))
        c.snd(t + dur + .45, "pop:1" if d["delta"] >= 0 else "error", .45)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# 3 · GRÁFICO DE LÍNEAS
# ---------------------------------------------------------------------------------------------------------------------
def v_grafico(d, err):
    _txt(d, "titulo", err, 44)
    p = d.get("puntos")
    if not isinstance(p, list) or not (2 <= len(p) <= 40) or not all(_num(x) for x in p):
        err("«puntos» debe ser una lista de 2 a 40 números")
    _txt(d, "unidad", err, 6, req=False)
    et = d.get("etiquetas")
    if et is not None and not (isinstance(et, list) and len(et) == 2 and all(isinstance(x, str) and len(x) <= 14 for x in et)):
        err("«etiquetas» debe ser una lista de 2 textos cortos (inicio y fin)")
    an = d.get("anotaciones", [])
    if not isinstance(an, list) or len(an) > 3:
        err("«anotaciones» admite hasta 3")
    else:
        n = len(p) if isinstance(p, list) else 0
        for a in an:
            if not isinstance(a, dict) or not isinstance(a.get("i"), int) or not 0 <= a["i"] < n or not isinstance(a.get("texto"), str) or len(a["texto"]) > 28:
                err("cada anotación necesita «i» (posición del punto) y «texto» de hasta 28 caracteres")


def e_grafico(c, d):
    pts = d["puntos"]
    n = len(pts)
    VW, VH = c.n(984) if c.W >= 984 else c.W, c.n(560)
    VW = c.W
    lo, hi = min(pts), max(pts)
    rng = (hi - lo) or 1.0
    top, bot = c.n(50), c.n(40)
    X = lambda i: i * VW / (n - 1)
    Y = lambda v: VH - bot - (v - lo) / rng * (VH - top - bot)
    path = "M" + " L".join(f"{X(i):.1f} {Y(v):.1f}" for i, v in enumerate(pts))
    area = path + f" L{VW:.0f} {VH:.0f} L0 {VH:.0f}Z"
    sube = pts[-1] >= pts[0]
    col = "var(--up)" if sube else "var(--down)"
    unidad = d.get("unidad", "")
    cambio = ""
    if pts[0] != 0:
        ch = (pts[-1] / pts[0] - 1) * 100
        cambio = f'{"▲ +" if ch >= 0 else "▼ −"}{es(abs(ch), 0 if abs(ch) >= 100 else 1)} %'
    grid = "".join(f'<path d="M0 {VH * k / 4:.0f} H{VW:.0f}" stroke="var(--border)" stroke-width="2" opacity=".55"/>' for k in range(1, 4))
    pins, pin_js = "", []
    for k, a in enumerate(d.get("anotaciones", [])):
        cx, cy = X(a["i"]), Y(pts[a["i"]])
        pw = len(a["texto"]) * c.n(19) + c.n(44)
        left = min(max(cx - pw / 2, 0), VW - pw)
        above = cy > VH * 0.45
        ty = cy - c.n(92) if above else cy + c.n(30)
        pins += (f'<div class="pin h" id="{c.pf}pin{k}" style="left:{cx - c.n(11):.0f}px;top:{cy - c.n(11):.0f}px;width:{c.n(22)}px;height:{c.n(22)}px"></div>'
                 f'<div class="pildora h" id="{c.pf}an{k}" style="position:absolute;left:{left:.0f}px;top:{ty:.0f}px;font-size:{c.px(32)};padding:{c.px(8)} {c.px(20)}">{esc(a["texto"])}</div>')
        ta = c.T(a.get("cuando"), 0.55 + 0.12 * k)
        pin_js += [fromTo(f"#{c.pf}pin{k}", {"opacity": 0, "scale": 0}, {"opacity": 1, "scale": 1, "duration": .35, "ease": "back.out(3)"}, ta),
                   fromTo(f"#{c.pf}an{k}", {"opacity": 0, "y": 12}, {"opacity": 1, "y": 0, "duration": .35, "ease": "power3.out"}, ta + .12)]
        c.snd(ta, "pop:" + str(k % 4), .45)
    et = d.get("etiquetas")
    html = (f'<div class="col" style="justify-content:center;gap:{c.px(20)}">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
            f'<div class="lab" style="font-size:{c.px(34)}">{esc(d["titulo"])}</div>'
            f'<div class="h" id="{c.pf}val" style="font-weight:700;font-size:{c.px(64)};color:{col}">{esc(es(pts[-1], 1 if abs(pts[-1]) < 100 and pts[-1] != int(pts[-1]) else 0))}{esc(unidad)}</div></div>'
            f'<div style="position:relative;width:{VW}px;height:{VH}px">'
            f'<svg viewBox="0 0 {VW} {VH}" width="{VW}" height="{VH}" style="overflow:visible">{grid}'
            f'<path id="{c.pf}ar" d="{area}" fill="{col}" opacity="0"/>'
            f'<path id="{c.pf}ln" d="{path}" fill="none" stroke="{col}" stroke-width="{c.n(10)}" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>'
            f'<circle id="{c.pf}dot" cx="{X(n - 1):.1f}" cy="{Y(pts[-1]):.1f}" r="{c.n(15)}" fill="{col}" opacity="0"/></svg>{pins}</div>'
            + (f'<div style="display:flex;justify-content:space-between" class="lab"><span style="font-size:{c.px(28)}">{esc(et[0])}</span><span style="font-size:{c.px(28)}">{esc(et[1])}</span></div>' if et else "")
            + (f'<div class="chip h" id="{c.pf}chg" style="font-size:{c.px(44)};--c:{col};align-self:center">{cambio}</div>' if cambio else "") + '</div>')
    t = c.t0 + .55
    dur = min(2.2, max(1.2, c.dur * .45))
    js = [fromTo(f"#{c.pf}ln", {"attr": {"stroke-dashoffset": 1}}, {"attr": {"stroke-dashoffset": 0}, "duration": dur, "ease": "power1.inOut"}, t),
          to(f"#{c.pf}ar", {"opacity": .13, "duration": .6}, t + dur * .6),
          fromTo(f"#{c.pf}dot", {"opacity": 0, "scale": 0, "transformOrigin": "center"}, {"opacity": 1, "scale": 1, "duration": .35, "ease": "back.out(3)"}, t + dur),
          fromTo(f"#{c.pf}val", {"opacity": 0, "y": -16}, {"opacity": 1, "y": 0, "duration": .4, "ease": "power3.out"}, t + dur)] + pin_js
    if cambio:
        js.append(fromTo(f"#{c.pf}chg", {"opacity": 0, "scale": .5}, {"opacity": 1, "scale": 1, "duration": .4, "ease": "back.out(3)"}, t + dur + .25))
    c.snd(c.t0 + .25, "card", .4)
    c.snd(t, "riser:1", .32)
    c.snd(t + dur, "ding:0" if sube else "error", .4)
    if cambio:
        c.snd(t + dur + .25, "pop:1", .4)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# 4 · BARRAS
# ---------------------------------------------------------------------------------------------------------------------
def v_barras(d, err):
    _txt(d, "titulo", err, 44)
    _txt(d, "unidad", err, 6, req=False)
    it = _items(d, "items", err, 2, 6)
    for x in it:
        if not isinstance(x, dict) or not isinstance(x.get("n"), str) or len(x["n"]) > 24 or not _num(x.get("v")) or x["v"] < 0:
            err("cada barra necesita «n» (nombre de hasta 24 caracteres) y «v» (número ≥ 0)")
            break
    if "destacar" in d and not (isinstance(d["destacar"], int) and 0 <= d["destacar"] < len(it)):
        err("«destacar» debe ser la posición de una barra")


def e_barras(c, d):
    it = d["items"]
    n = len(it)
    mx = max(x["v"] for x in it) or 1
    unidad = d.get("unidad", "")
    dest = d.get("destacar", max(range(n), key=lambda k: it[k]["v"]))
    rh = min(150, (860 - 120) / n)
    rows = ""
    for k, x in enumerate(it):
        colr = "var(--acc)" if k == dest else "var(--acc2)"
        rows += (f'<div class="h" id="{c.pf}r{k}" style="height:{c.px(rh)}"><div class="lab" style="font-size:{c.px(32)};color:var(--text);letter-spacing:.02em">{esc(x["n"])}</div>'
                 f'<div style="display:flex;align-items:center;gap:{c.px(20)};margin-top:{c.px(10)}"><div class="pista" style="flex:1;height:{c.px(46)}">'
                 f'<div id="{c.pf}b{k}" style="height:100%;width:0;border-radius:{c.px(23)};background:{colr};opacity:{1 if k == dest else .7}"></div></div>'
                 f'<div class="h" id="{c.pf}v{k}" style="font-weight:700;font-size:{c.px(44)};min-width:{c.px(130)};text-align:right;color:{colr}">{esc(es(x["v"], 1 if x["v"] != int(x["v"]) else 0))}{esc(unidad)}</div></div></div>')
    html = (f'<div class="col" style="justify-content:center;gap:{c.px(14)}"><div class="lab" style="font-size:{c.px(34)};margin-bottom:{c.px(16)}">{esc(d["titulo"])}</div>{rows}</div>')
    js = []
    c.snd(c.t0 + .2, "card", .4)
    for k, x in enumerate(it):
        t = c.T(x.get("cuando"), 0.12 + 0.62 * k / max(n - 1, 1))
        js += [fromTo(f"#{c.pf}r{k}", {"opacity": 0, "x": -40}, {"opacity": 1, "x": 0, "duration": .35, "ease": "power3.out"}, t - .1),
               to(f"#{c.pf}b{k}", {"width": f"{x['v'] / mx * 100:.1f}%", "duration": .8, "ease": "power3.out"}, t),
               fromTo(f"#{c.pf}v{k}", {"opacity": 0}, {"opacity": 1, "duration": .3}, t + .6)]
        c.snd(t - .1, "swipe", .22)
        c.snd(t + .6, f"blip:{k}", .42)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# 5 · GRÁFICO CIRCULAR
# ---------------------------------------------------------------------------------------------------------------------
def v_donut(d, err):
    _txt(d, "titulo", err, 44)
    it = _items(d, "segmentos", err, 2, 5)
    for x in it:
        if not isinstance(x, dict) or not isinstance(x.get("n"), str) or len(x["n"]) > 22 or not _num(x.get("v")) or x["v"] <= 0:
            err("cada segmento necesita «n» (hasta 22 caracteres) y «v» (número > 0)")
            break


def e_donut(c, d):
    seg = d["segmentos"]
    tot = sum(x["v"] for x in seg)
    cols = ["var(--acc)", "var(--acc2)", "var(--warn)", "var(--down)", "var(--up)"]
    R = 150.0
    C = 2 * math.pi * R
    size = min(c.W * .64, c.n(470))
    circ, leg, js, ang = "", "", [], 0.0
    mayor = max(range(len(seg)), key=lambda k: seg[k]["v"])
    c.snd(c.t0 + .2, "card", .4)
    for k, x in enumerate(seg):
        frac = x["v"] / tot
        ln = max(C * frac - 4, 1)
        circ += (f'<circle id="{c.pf}c{k}" cx="200" cy="200" r="{R}" fill="none" stroke="{cols[k]}" stroke-width="64" stroke-dasharray="0 {C:.1f}" '
                 f'transform="rotate({-90 + ang * 360:.2f} 200 200)"/>')
        leg += (f'<div class="h" id="{c.pf}g{k}" style="display:flex;align-items:center;gap:{c.px(18)};font-weight:700;font-size:{c.px(44)};margin-top:{c.px(12)}">'
                f'<span style="width:{c.px(30)};height:{c.px(30)};border-radius:50%;background:{cols[k]};flex:none"></span><span style="flex:1">{esc(x["n"])}</span>'
                f'<span style="color:{cols[k]}">{es(frac * 100, 0)} %</span></div>')
        t = c.T(x.get("cuando"), 0.1 + 0.6 * k / max(len(seg) - 1, 1))
        js += [to(f"#{c.pf}c{k}", {"attr": {"stroke-dasharray": f"{ln:.1f} {C - ln:.1f}"}, "duration": .8, "ease": "power2.out"}, t),
               fromTo(f"#{c.pf}g{k}", {"opacity": 0, "x": 40}, {"opacity": 1, "x": 0, "duration": .35, "ease": "power3.out"}, t + .1)]
        c.snd(t, f"blip:{k}", .42)
        ang += frac
    html = (f'<div class="col" style="align-items:center;justify-content:center;gap:{c.px(18)}"><div class="lab" style="font-size:{c.px(34)};align-self:flex-start">{esc(d["titulo"])}</div>'
            f'<div style="position:relative;width:{size:.0f}px;height:{size:.0f}px"><svg viewBox="0 0 400 400" width="{size:.0f}" height="{size:.0f}">'
            f'<circle cx="200" cy="200" r="{R}" fill="none" stroke="var(--raised)" stroke-width="64"/>{circ}</svg>'
            f'<div class="h" id="{c.pf}ct" style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">'
            f'<div style="font-weight:700;font-size:{c.px(96)};line-height:1;color:{cols[mayor]}">{es(seg[mayor]["v"] / tot * 100, 0)} %</div>'
            f'<div class="lab" style="font-size:{c.px(26)};margin-top:{c.px(8)}">{esc(seg[mayor]["n"])}</div></div></div>'
            f'<div style="width:100%">{leg}</div></div>')
    tf = c.t0 + c.dur * .72
    js.append(fromTo(f"#{c.pf}ct", {"opacity": 0, "scale": .7}, {"opacity": 1, "scale": 1, "duration": .45, "ease": "back.out(2.4)"}, tf))
    c.snd(tf, "ding:2", .35)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# 6 · LISTA CON CHECKS
# ---------------------------------------------------------------------------------------------------------------------
def v_lista(d, err):
    _txt(d, "titulo", err, 44, req=False)
    it = _items(d, "items", err, 2, 5)
    for x in it:
        t = x.get("t") if isinstance(x, dict) else x
        if not isinstance(t, str) or not t or len(t) > 36:
            err("cada punto de la lista debe ser un texto de hasta 36 caracteres")
            break


def e_lista(c, d):
    it = [x if isinstance(x, dict) else {"t": x} for x in d["items"]]
    n = len(it)
    rows = "".join(f'<div class="fila h" id="{c.pf}r{k}" style="font-size:{c.px(54)};height:{c.px(122)};gap:{c.px(24)}">'
                   f'<div class="ck" id="{c.pf}ck{k}" style="width:{c.px(68)};height:{c.px(68)};font-size:{c.px(44)}">✓</div>{esc(x["t"])}</div>' for k, x in enumerate(it))
    html = (f'<div class="col" style="justify-content:center;gap:{c.px(18)}">'
            + (f'<div class="lab" style="font-size:{c.px(34)};margin-bottom:{c.px(10)}">{esc(d["titulo"])}</div>' if d.get("titulo") else "") + rows + '</div>')
    js = []
    c.snd(c.t0 + .2, "card", .35)
    for k, x in enumerate(it):
        t = c.T(x.get("cuando"), 0.15 + 0.6 * k / max(n - 1, 1))
        js += [fromTo(f"#{c.pf}r{k}", {"opacity": 0, "x": 50}, {"opacity": 1, "x": 0, "duration": .35, "ease": "power3.out"}, t),
               f'tl.set("#{c.pf}ck{k}",{{backgroundColor:"var(--acc)",borderColor:"var(--acc)",color:"#0B1020"}},{r2(t + .35)});',
               fromTo(f"#{c.pf}ck{k}", {"scale": .5}, {"scale": 1, "duration": .3, "ease": "back.out(3)", "immediateRender": False}, t + .35)]
        c.snd(t, "pop:" + str(k % 4), .5)
        c.snd(t + .35, "ding:" + str(k % 3), .32)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# 7 · TARJETAS DE DATOS
# ---------------------------------------------------------------------------------------------------------------------
def v_tarjetas(d, err):
    _txt(d, "titulo", err, 44, req=False)
    it = _items(d, "items", err, 2, 4)
    for x in it:
        if (not isinstance(x, dict) or not isinstance(x.get("etiqueta"), str) or len(x["etiqueta"]) > 30 or not isinstance(x.get("valor"), str) or not x["valor"]
                or len(x["valor"]) > 12 or (x.get("nota") is not None and (not isinstance(x["nota"], str) or len(x["nota"]) > 44))
                or x.get("tono", "acc") not in ("acc", "up", "down", "warn")):
            err("cada tarjeta necesita «etiqueta» (hasta 30), «valor» (texto de hasta 12), «nota» opcional (hasta 44) y «tono» opcional (acc, up, down, warn)")
            break


def e_tarjetas(c, d):
    it = d["items"]
    n = len(it)
    ch = min(300, (900 - 90) / n - 20)
    cards = ""
    for k, x in enumerate(it):
        tono = x.get("tono", "acc")
        cards += (f'<div class="tarjeta h" id="{c.pf}t{k}" style="height:{c.px(ch)};padding:{c.px(24)} {c.px(34)}">'
                  f'<div class="lab" style="font-size:{c.px(28)}">{esc(x["etiqueta"])}</div>'
                  f'<div style="font-weight:700;font-size:{c.px(min(120, ch * .46))};letter-spacing:-.03em;line-height:1.05;color:var(--{tono})">{esc(x["valor"])}</div>'
                  + (f'<div class="nota" style="font-size:{c.px(32)};margin-top:{c.px(4)}">{esc(x["nota"])}</div>' if x.get("nota") else "") + '</div>')
    html = (f'<div class="col" style="justify-content:center;gap:{c.px(20)}">'
            + (f'<div class="lab" style="font-size:{c.px(34)}">{esc(d["titulo"])}</div>' if d.get("titulo") else "") + cards + '</div>')
    js = []
    for k, x in enumerate(it):
        t = c.T(x.get("cuando"), 0.1 + 0.6 * k / max(n - 1, 1))
        js.append(fromTo(f"#{c.pf}t{k}", {"opacity": 0, "y": 70, "scale": .96}, {"opacity": 1, "y": 0, "scale": 1, "duration": .5, "ease": "power3.out"}, t))
        c.snd(t, "card", .5)
        c.snd(t + .25, "pop:" + str((k + 1) % 4), .3)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# 8 · PREGUNTA PARA EL ESPECTADOR
# ---------------------------------------------------------------------------------------------------------------------
def v_pregunta(d, err):
    _txt(d, "pregunta", err, 70)
    op = _items(d, "opciones", err, 2, 3)
    for x in op:
        t = x.get("t") if isinstance(x, dict) else x
        if not isinstance(t, str) or not t or len(t) > 26:
            err("cada opción debe ser un texto de hasta 26 caracteres")
            break
    _txt(d, "pie", err, 40, req=False)


def e_pregunta(c, d):
    op = [x if isinstance(x, dict) else {"t": x} for x in d["opciones"]]
    n = len(op)
    letras = "ABC"
    opts = "".join(f'<div class="opcion h" id="{c.pf}o{k}" style="font-size:{c.px(62)};gap:{c.px(28)};padding:{c.px(26)} {c.px(32)}">'
                   f'<b style="width:{c.px(110)};height:{c.px(110)};font-size:{c.px(64)};background:var(--{"acc" if k % 2 == 0 else "acc2"})">{letras[k]}</b>{esc(x["t"])}</div>' for k, x in enumerate(op))
    html = (f'<div class="col" style="justify-content:center;align-items:flex-start;gap:{c.px(26)}">{chip(c, "AHORA TÚ", c.pf + "chip", 32)}'
            f'<div class="big h" id="{c.pf}q" style="font-size:{c.px(88 if len(d["pregunta"]) < 40 else 74)}">{esc(d["pregunta"])}</div>{opts}'
            f'<div class="lab h" id="{c.pf}pie" style="font-size:{c.px(34)};color:var(--acc)">{esc(d.get("pie", "RESPONDE EN LOS COMENTARIOS"))}</div></div>')
    js = [fromTo(f"#{c.pf}chip", {"opacity": 0, "scale": .6}, {"opacity": 1, "scale": 1, "duration": .4, "ease": "back.out(2.4)"}, c.t0 + .2),
          fromTo(f"#{c.pf}q", {"opacity": 0, "y": 30}, {"opacity": 1, "y": 0, "duration": .5, "ease": "power3.out"}, c.t0 + .35)]
    c.snd(c.t0 + .2, "pop:0", .45)
    c.snd(c.t0 + .35, "swipe", .3)
    tl_ = 0
    for k, x in enumerate(op):
        t = c.T(x.get("cuando"), 0.5 + 0.2 * k)
        t = max(t - .15, c.t0 + .9 + .25 * k)
        tl_ = t
        js.append(fromTo(f"#{c.pf}o{k}", {"opacity": 0, "x": 80}, {"opacity": 1, "x": 0, "duration": .45, "ease": "power3.out"}, t))
        c.snd(t, "pop:" + str(k + 1), .5)
    js.append(fromTo(f"#{c.pf}pie", {"opacity": 0}, {"opacity": 1, "duration": .4}, tl_ + .6))
    c.snd(tl_ + .6, "ding:1", .35)
    return html, js


ESCENAS = {
    "titulo": (e_titulo, v_titulo), "numero": (e_numero, v_numero), "grafico": (e_grafico, v_grafico), "barras": (e_barras, v_barras),
    "donut": (e_donut, v_donut), "lista": (e_lista, v_lista), "tarjetas": (e_tarjetas, v_tarjetas), "pregunta": (e_pregunta, v_pregunta),
}


# ---------------------------------------------------------------------------------------------------------------------
# 9 · GANCHO INICIAL (obligatoria, siempre la primera): frena el scroll en el primer segundo
# ---------------------------------------------------------------------------------------------------------------------
ICONOS = {
    "alerta": ('<svg viewBox="0 0 100 100"><path d="M50 8 L96 90 H4Z" fill="none" stroke="var(--acc)" stroke-width="8" stroke-linejoin="round"/>'
               '<path d="M50 38 V62" stroke="var(--acc)" stroke-width="9" stroke-linecap="round"/><circle cx="50" cy="77" r="5.5" fill="var(--acc)"/></svg>'),
    "subida": ('<svg viewBox="0 0 100 100"><path d="M6 80 L34 52 L54 66 L90 22" fill="none" stroke="var(--up)" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>'
               '<path d="M66 20 H92 V46" fill="none" stroke="var(--up)" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/></svg>'),
    "bajada": ('<svg viewBox="0 0 100 100"><path d="M6 22 L34 50 L54 36 L90 80" fill="none" stroke="var(--down)" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>'
               '<path d="M66 82 H92 V56" fill="none" stroke="var(--down)" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/></svg>'),
    "pregunta": ('<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="42" fill="none" stroke="var(--acc)" stroke-width="8"/>'
                 '<text x="50" y="72" text-anchor="middle" font-family="InterW" font-weight="700" font-size="64" fill="var(--acc)">?</text></svg>'),
}


GRAFICOS_GANCHO = ("pulso", "caida", "subida", "cifra", "ninguno")


def v_gancho(d, err):
    if d.get("angulo") is not None and d["angulo"] not in ("error", "verdad", "secreto", "urgencia", "pregunta"):
        err("«angulo» debe ser error, verdad, secreto, urgencia o pregunta")
    _txt(d, "texto", err, 42)
    _txt(d, "resalte", err, 20, req=False)
    _txt(d, "kicker", err, 22, req=False)
    _txt(d, "subtexto", err, 70, req=False)
    t, r = d.get("texto"), d.get("resalte")
    if isinstance(t, str) and isinstance(r, str) and r and norm(r) not in [norm(w) for w in t.split()]:
        err("«resalte» debe ser una palabra que aparezca en «texto»")
    if d.get("icono", "alerta") not in list(ICONOS) + ["ninguno"]:
        err(f"«icono» debe ser uno de {list(ICONOS) + ['ninguno']}")
    if d.get("motivo") is not None:
        from escenas_meta import v_motivo
        v_motivo(d, err)
    g = d.get("grafico", "pulso")
    if g not in GRAFICOS_GANCHO:
        err(f"«grafico» debe ser uno de {list(GRAFICOS_GANCHO)}")
    if g == "cifra":
        cf = d.get("cifra")
        if not isinstance(cf, dict) or not _num(cf.get("valor")):
            err("el gráfico «cifra» necesita «cifra»: {\"valor\": número, \"decimales\": 0-2, \"prefijo\": \"\", \"sufijo\": \"%\"}")
        else:
            if not isinstance(cf.get("decimales", 0), int) or not 0 <= cf.get("decimales", 0) <= 2:
                err("«cifra.decimales» debe ser un entero de 0 a 2")
            for k in ("prefijo", "sufijo"):
                if not isinstance(cf.get(k, ""), str) or len(cf.get(k, "")) > 4:
                    err(f"«cifra.{k}» debe ser un texto de hasta 4 caracteres")


AREA_UTIL = 1010 - 60                      # alto de la zona de escena (motor.AREA_H) menos margen: lo que se pase tapa los subtítulos de arriba o el pie


def _lineas_texto(ws, fs, ancho, factor=.68):
    """Líneas que ocupará un texto en mayúsculas al ajustarse al ancho (estimación prudente)."""
    n, cur = 1, 0.0
    for w in ws:
        px = len(w) * fs * factor + fs * .26
        if cur and cur + px > ancho * .94:
            n, cur = n + 1, px
        else:
            cur += px
    return n


def _alto_fijo_gancho(ws, fs, d):
    """Alto de todo lo del gancho salvo el gráfico: kicker, texto enorme, subtexto y huecos."""
    h = _lineas_texto(ws, fs, 984) * fs * 1.02
    h += 34 * 2.0 + 30 if d.get("kicker") else 0
    if d.get("subtexto"):
        h += _lineas_texto(d["subtexto"].split(), 50, 860, factor=.52) * 50 * 1.22 + 30
    return h + 30


def altura_motivo_gancho(ws, fs, d):
    return int(max(200, min(430, AREA_UTIL - _alto_fijo_gancho(ws, fs, d))))


def _ajustar_fs_gancho(ws, fs, d, graf, motivo, ancho):
    """Reduce la letra del gancho hasta que quepa todo (gráfico incluido) en la zona de escena."""
    graf_h = 430 if motivo else {"pulso": 260, "caida": 300, "subida": 300, "cifra": 240}.get(graf, 0)
    graf_h = min(graf_h, 300) if motivo else graf_h
    while fs > 84 and _alto_fijo_gancho(ws, fs, d) + graf_h + 30 > AREA_UTIL:
        fs = int(fs * .92)
    return fs


def _palabras(t):
    """Palabras del texto del gancho; un «%» suelto se pega al número anterior para que no quede huérfano en otra línea."""
    out = []
    for w in t.split():
        if out and re.fullmatch(r"%\W*", w):
            out[-1] += " " + w
        else:
            out.append(w)
    return out


def e_gancho(c, d):
    t = d["texto"]
    n = len(t)
    fs = 200 if n <= 14 else 160 if n <= 24 else 128 if n <= 34 else 106
    fs = min(fs, int(0.92 * 984 / (0.70 * max(len(w) for w in _palabras(t)))))   # la palabra más larga debe caber en el ancho
    res = norm(d.get("resalte") or "")
    ws = _palabras(t)
    icono = d.get("icono", "alerta")
    graf = d.get("grafico", "pulso")
    motivo = d.get("motivo") if graf != "cifra" else None        # una animación de metáfora apoya el gancho (si hay cifra gigante, manda la cifra)
    if motivo:
        graf = "ninguno"
    if graf == "pulso" and icono == "ninguno":
        graf = "ninguno"
    fs = _ajustar_fs_gancho(ws, fs, d, graf, motivo, c.W / c.u)
    pf = c.pf
    spans = "".join(f'<span id="{pf}w{j}" style="display:inline-block;margin:0 .13em;{"color:var(--acc);" if res and norm(w) == res else ""}">{esc(w)}</span>' for j, w in enumerate(ws))
    # --- gráfico llamativo ---
    gr_html, gr_js = "", []
    if graf == "pulso":
        anillos = "".join(f'<div id="{pf}ring{k}" style="position:absolute;left:50%;top:50%;width:{c.px(190)};height:{c.px(190)};margin:-{c.px(95)} 0 0 -{c.px(95)};'
                          f'border:{c.px(7)} solid var(--acc);border-radius:50%;opacity:0"></div>' for k in range(3))
        gr_html = (f'<div style="position:relative;width:{c.px(300)};height:{c.px(260)};display:flex;align-items:center;justify-content:center">{anillos}'
                   f'<div id="{pf}ico" style="position:relative;width:{c.px(190)};height:{c.px(190)}">{ICONOS[icono]}</div></div>')
        gr_js = [fromTo(f"#{pf}ico", {"opacity": 1, "scale": 1.8, "rotation": -18}, {"scale": 1, "rotation": 0, "duration": .32, "ease": "back.out(3)"}, 0)]
        for k in range(3):
            gr_js.append(fromTo(f"#{pf}ring{k}", {"opacity": .85, "scale": .5}, {"opacity": 0, "scale": 2.6, "duration": .9, "ease": "power2.out", "repeat": 2, "repeatDelay": .05}, .04 + .28 * k))
    elif graf in ("caida", "subida"):
        pts = [(10, 30), (120, 62), (205, 48), (300, 118), (385, 96), (520, 196), (605, 172), (740, 270)]
        if graf == "subida":
            pts = [(x, 300 - y) for x, y in pts]
        col = "var(--down)" if graf == "caida" else "var(--up)"
        ruta = "M" + " L".join(f"{x} {y}" for x, y in pts)
        gr_html = (f'<svg id="{pf}svg" viewBox="0 0 750 300" width="{c.px(750)[:-2]}" height="{c.px(300)[:-2]}" style="overflow:visible;filter:drop-shadow(0 0 {c.px(18)} {col})">'
                   f'<path id="{pf}ln" d="{ruta}" fill="none" stroke="{col}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>'
                   f'<circle id="{pf}dot" cx="{pts[-1][0]}" cy="{pts[-1][1]}" r="22" fill="{col}" opacity="0"/></svg>')
        gr_js = [fromTo(f"#{pf}ln", {"attr": {"stroke-dashoffset": 1}}, {"attr": {"stroke-dashoffset": 0}, "duration": .55, "ease": "power2.in"}, .02),
                 fromTo(f"#{pf}dot", {"opacity": 0, "scale": 0, "transformOrigin": "center"}, {"opacity": 1, "scale": 1, "duration": .25, "ease": "back.out(4)"}, .5)]
        c.snd(.02, "riser:0", .35)
        c.snd(.55, "error" if graf == "caida" else "ding:2", .4)
    elif graf == "cifra":
        cf = d["cifra"]
        dec, pre, suf = cf.get("decimales", 0), cf.get("prefijo", ""), cf.get("sufijo", "")
        col = "var(--down)" if cf["valor"] < 0 else "var(--up)"
        final = pre + es(cf["valor"], dec) + suf
        fsz = min(240, 1500 / max(len(final), 1))
        gr_html = f'<div id="{pf}cifra" class="big" style="font-size:{c.px(fsz)};line-height:1;color:{col};text-shadow:0 0 {c.px(40)} {col}">{esc(pre + es(0, dec) + suf)}</div>'
        gr_js = [f'const {pf}o={{v:0}};tl.to({pf}o,{{v:{cf["valor"]},duration:.7,ease:"power3.out",onUpdate(){{document.getElementById("{pf}cifra").textContent={J(pre)}+fm({pf}o.v,{dec})+{J(suf)}}}}},0.02);',
                 fromTo(f"#{pf}cifra", {"scale": 1.5}, {"scale": 1, "duration": .35, "ease": "power4.out"}, 0)]
        for k in range(10):
            c.snd(.03 + .065 * k, "tick", .3)
        c.snd(.72, "error" if cf["valor"] < 0 else "ding:2", .45)
    if motivo:
        import escenas_meta
        ident = f"{pf}mv"
        gr_html = escenas_meta.canvas(ident, c.W, c.n(altura_motivo_gancho(ws, fs, d))) + escenas_meta.modulo(ident, motivo, c.t0 + .02, {"escala": 1.3})
        escenas_meta.sonido_entrada(c, motivo, .05)
    # --- estructura: kicker, gráfico, texto enorme, subtexto ---
    kicker = (f'<span class="chip" id="{pf}kick" style="font-size:{c.px(34)};--c:var(--acc)">{esc(d["kicker"])}</span>' if d.get("kicker") else "")
    sub = (f'<div id="{pf}sub" class="nota" style="font-size:{c.px(50)};max-width:{c.px(860)}">{esc(d["subtexto"])}</div>' if d.get("subtexto") else "")
    html = (f'<div id="{pf}in" style="height:100%"><div class="col" style="align-items:center;justify-content:center;text-align:center;gap:{c.px(30)}">'
            f'{kicker}{gr_html}<div id="{pf}tt" class="big" style="font-size:{c.px(fs)};line-height:1.0;text-transform:uppercase;text-shadow:0 6px 40px rgba(0,0,0,.6)">{spans}</div>{sub}</div></div>')
    acc = c.p["acc"]
    js = [fromTo("#flash", {"opacity": .6, "backgroundColor": "#FFFFFF"}, {"opacity": 0, "duration": .1, "ease": "none"}, 0),           # doble destello: blanco…
          fromTo("#flash", {"opacity": .42, "backgroundColor": acc}, {"opacity": 0, "duration": .3, "ease": "power2.out", "immediateRender": False}, .1),   # …y de color
          fromTo(f"#{pf}in", {"scale": 1.14}, {"scale": 1, "duration": .4, "ease": "power4.out"}, 0),                                       # golpe de zoom
          fromTo(f"#S{c.i}", {"x": -20}, {"x": 20, "duration": .04, "repeat": 9, "yoyo": True, "ease": "none"}, .02),                       # sacudida
          to(f"#S{c.i}", {"x": 0, "duration": .05}, .42),
          fromTo(f"#{pf}tt", {"textShadow": "12px 0 #FF7A7A, -12px 0 #67D4E8"}, {"textShadow": "0px 0 rgba(0,0,0,0), 0px 0 rgba(0,0,0,0)", "duration": .5, "ease": "power2.out"}, 0)] + gr_js   # glitch RGB
    for j in range(len(ws)):                    # visibles desde el primer fotograma (miniatura): entran grandes y encajan
        js.append(fromTo(f"#{pf}w{j}", {"opacity": 1, "scale": 1.9, "y": -34, "rotation": 3 if j % 2 else -3}, {"scale": 1, "y": 0, "rotation": 0, "duration": .24, "ease": "back.out(2.2)"}, .02 + .08 * j))
        c.snd(.02 + .08 * j, "tick", .35)
    if d.get("kicker"):
        js.append(fromTo(f"#{pf}kick", {"opacity": 1, "scale": 1.6, "y": -20}, {"scale": 1, "y": 0, "duration": .25, "ease": "back.out(3)"}, .03))
        c.snd(.05, "pop:2", .4)
    if d.get("subtexto"):
        js.append(fromTo(f"#{pf}sub", {"opacity": 0, "y": 26}, {"opacity": 1, "y": 0, "duration": .4, "ease": "power3.out"}, .55))
        c.snd(.55, "swipe", .3)
    c.snd(0.0, "boom", .75)
    c.snd(0.0, "impact", .45)
    c.snd(0.0, "whoosh:2", .4)
    c.snd(0.02, "glitch", .3)
    c.snd(0.35, "pop:3", .4)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# 10 · LLAMADA A LA ACCIÓN (obligatoria, siempre la última): «Síguenos en WhaleXtreet»
# ---------------------------------------------------------------------------------------------------------------------
def marca_redes():
    ruta = Path(__file__).resolve().parent.parent / "marca" / "redes.json"
    base = {"cta_texto": "Síguenos en WhaleXtreet", "cta_voz": "Síguenos en WhaleXtreet para más ideas como esta.", "redes": ["Instagram", "TikTok", "YouTube Shorts"], "usuario": None, "web": None}
    if ruta.exists():
        base.update(json.loads(ruta.read_text(encoding="utf-8")))
    return base


def v_cta(d, err):
    _txt(d, "texto", err, 40, req=False)
    _txt(d, "usuario", err, 24, req=False)
    _txt(d, "web", err, 40, req=False)
    _txt(d, "compartir", err, 40, req=False)      # cierre «Envíaselo a ese amigo que…» (maqueta de chat); ver escenas_versus.py
    o = d.get("oferta")                           # cierre «Comenta X y sígueme y te envío Y por privado» (solo cuando el post trae una oferta real)
    if o is not None:
        if not (isinstance(o, dict) and isinstance(o.get("palabra"), str) and re.fullmatch(r"[A-ZÁÉÍÓÚÜÑ0-9]{3,12}", o["palabra"])
                and isinstance(o.get("que"), str) and 3 <= len(o["que"]) <= 40):
            err("«oferta» necesita «palabra» (3-12 letras o cifras en mayúsculas, fácil de decir) y «que» (qué se envía, 3-40 caracteres, p. ej. «la guía en PDF»)")
        if d.get("compartir"):
            err("un cierre no puede llevar a la vez «oferta» y «compartir»")
    r = d.get("redes")
    if r is not None and not (isinstance(r, list) and 1 <= len(r) <= 4 and all(isinstance(x, str) and 0 < len(x) <= 16 for x in r)):
        err("«redes» debe ser una lista de 1 a 4 nombres cortos")


def e_cta(c, d):
    if d.get("oferta"):
        from escenas_versus import e_comenta
        return e_comenta(c, d)
    if d.get("compartir"):
        from escenas_versus import e_compartir
        return e_compartir(c, d)
    cfg = marca_redes()
    texto = d.get("texto") or cfg["cta_texto"]
    redes = d.get("redes") or cfg["redes"]
    usuario, web = d.get("usuario") or cfg.get("usuario"), d.get("web") or cfg.get("web")
    pills = "".join(f'<span class="pildora h" id="{c.pf}r{j}" style="font-size:{c.px(40)};margin:{c.px(8)}">{esc(x)}</span>' for j, x in enumerate(redes))
    html = (f'<div class="col" style="align-items:center;justify-content:center;text-align:center;gap:{c.px(26)}">'
            f'<img class="h" id="{c.pf}logo" src="assets/isotipo-cierre.png" alt="" style="width:{c.px(330)}"/>'
            f'{chip(c, "SÍGUENOS", c.pf + "chip", 40)}'
            f'<div class="big h" id="{c.pf}tx" style="font-size:{c.px(84)};padding:0 {c.px(20)}">{esc(texto)}</div>'
            f'<div style="display:flex;flex-wrap:wrap;justify-content:center">{pills}</div>'
            + (f'<div class="big h" id="{c.pf}us" style="font-size:{c.px(64)};color:var(--acc)">{esc(usuario)}</div>' if usuario else "")
            + (f'<div class="nota h" id="{c.pf}web" style="font-size:{c.px(42)}">{esc(web)}</div>' if web else "") + '</div>')
    t = c.t0
    js = [fromTo(f"#{c.pf}logo", {"opacity": 0, "scale": .7}, {"opacity": 1, "scale": 1, "duration": .6, "ease": "back.out(1.8)"}, t + .1),
          fromTo(f"#{c.pf}chip", {"opacity": 0, "scale": .6}, {"opacity": 1, "scale": 1, "duration": .4, "ease": "back.out(2.4)"}, t + .45),
          fromTo(f"#{c.pf}tx", {"opacity": 0, "y": 30}, {"opacity": 1, "y": 0, "duration": .5, "ease": "power3.out"}, t + .6)]
    c.snd(t + .1, "card", .5)
    c.snd(t + .45, "ding:1", .45)
    c.snd(t + .6, "swipe", .3)
    for j in range(len(redes)):
        js.append(fromTo(f"#{c.pf}r{j}", {"opacity": 0, "scale": .5}, {"opacity": 1, "scale": 1, "duration": .35, "ease": "back.out(3)"}, t + 1.0 + .16 * j))
        c.snd(t + 1.0 + .16 * j, "pop:" + str(j % 4), .45)
    k = 1.0 + .16 * len(redes)
    for idn, ok in ((f"{c.pf}us", usuario), (f"{c.pf}web", web)):
        if ok:
            js.append(fromTo(f"#{idn}", {"opacity": 0, "y": 20}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, t + k + .2))
            c.snd(t + k + .2, "pop:2", .4)
            k += .4
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# 11 · DIÁLOGO (solo en vídeos con avatar «ambos»): los dos avatares abajo y un globo sobre el que habla
# ---------------------------------------------------------------------------------------------------------------------
def v_dialogo(d, err):
    _txt(d, "texto", err, 90)
    if d.get("rol") not in (None, "", "pregunta", "respuesta"):
        err("«rol» debe ser «pregunta» o «respuesta»")


def e_dialogo(c, d):
    quien = d.get("_habla", "profesor")
    der = (d.get("_lado") or ("der" if quien == "rubio" else "izq")) == "der"
    color = "var(--acc2)" if quien == "rubio" else "var(--acc)"
    rol = d.get("rol") or ""
    etiqueta = {"pregunta": "PREGUNTA", "respuesta": "RESPUESTA"}.get(rol)
    simbolo = {"pregunta": "?", "respuesta": "✓"}.get(rol)
    texto = d["texto"]
    fs = 68 if len(texto) <= 40 else 58 if len(texto) <= 65 else 50
    lado = "right" if der else "left"
    sombra = "bottom right" if der else "bottom left"
    html = (f'<div style="position:relative;height:100%">'
            f'<div id="{c.pf}bub" class="h" style="position:absolute;top:0;{lado}:0;width:{c.px(840)};background:var(--surface);border:{c.px(5)} solid {color};'
            f'border-radius:{c.px(50)};padding:{c.px(30)} {c.px(44)} {c.px(38)}">'
            + (f'<span class="chip" style="font-size:{c.px(30)};--c:{color}">{etiqueta}</span>' if etiqueta else "")
            + f'<div class="big" style="font-size:{c.px(fs)};margin-top:{c.px(14)}">{esc(texto)}</div>'
            f'<div style="position:absolute;bottom:-{c.px(28)};{lado}:{c.px(110)};width:0;height:0;border-left:{c.px(28)} solid transparent;'
            f'border-right:{c.px(28)} solid transparent;border-top:{c.px(32)} solid {color}"></div></div>'
            + (f'<div id="{c.pf}sym" class="h" style="position:absolute;left:{c.px(342)};top:{c.px(540)};width:{c.px(300)};text-align:center;'
               f'font-weight:700;font-size:{c.px(230)};line-height:1;color:{color}">{simbolo}</div>' if simbolo else "") + '</div>')
    js = [fromTo(f"#{c.pf}bub", {"opacity": 0, "scale": .86, "y": -24, "transformOrigin": sombra}, {"opacity": 1, "scale": 1, "y": 0, "duration": .45, "ease": "back.out(2)"}, c.t0 + .2)]
    if simbolo:
        js.append(fromTo(f"#{c.pf}sym", {"opacity": 0, "scale": .3}, {"opacity": .9, "scale": 1, "duration": .5, "ease": "back.out(3)"}, c.t0 + .45))
    if rol == "pregunta":
        c.snd(c.t0 + .2, "pop:1", .5)
        c.snd(c.t0 + .45, "riser:0", .25)
    else:
        c.snd(c.t0 + .2, "card", .5)
        c.snd(c.t0 + .45, "ding:1", .4)
    return html, js


ESCENAS.update({"gancho": (e_gancho, v_gancho), "cta": (e_cta, v_cta), "dialogo": (e_dialogo, v_dialogo)})

import escenas3d  # noqa: E402,F401  (registra las escenas 3D: barras3d, moneda3d)
import escenas_meta  # noqa: E402,F401  (registra la escena «metafora» y el «motivo» del gancho)
import escenas_ui  # noqa: E402,F401  (registra «pasos» y «checklist»)
import escenas_recursos  # noqa: E402,F401  (registra «terminal», «ranking» y «captura»: recursos que se usan solo cuando el tema lo pide)
import escenas_versus  # noqa: E402,F401  (registra «versus» con muñecos, «movil», «calendario» y «panel»; el cierre «compartir» se pide desde e_cta)
import escenas_grafico  # noqa: E402,F401  (registra «grafico_pro»: gráfico de línea, área o velas con datos reales, TradingView Lightweight Charts)
