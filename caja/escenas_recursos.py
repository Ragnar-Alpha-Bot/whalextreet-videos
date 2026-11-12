"""Recursos extra de edición, para usar SOLO cuando el tema del vídeo lo pida (no en todos los vídeos).

Salieron de analizar un vídeo de referencia sobre herramientas (maquetas de interfaz que se animan al nombrar cada función):

  · «terminal»  ventana de terminal en la que se escriben comandos letra a letra (vídeos sobre herramientas, instalaciones, atajos).
                Los comandos («cmd») tienen que aparecer literalmente en el post: no se inventan.
  · «ranking»   2-4 filas con una cifra grande a la izquierda y un título a la derecha; entran de borroso a nítido (comparativas con datos del post).
  · «captura»   una captura real (PNG/JPG guardada en <proyecto>/assets/) con un recuadro que ilumina lo importante y zoom hacia él. Es un recurso
                MANUAL: la IA no puede aportar imágenes; sirve para vídeos que montas tú (p. ej. enseñar la página de un repositorio).

Además, en otros módulos:  «sello» (en la escena metafora, p. ej. GRATIS), «*palabra*» (acento en cursiva serif en cualquier texto de pantalla)
y "subs": "recuadro" (subtítulos con la palabra activa en un recuadro de color).
"""
import html as _html
import re
from pathlib import Path

from escenas import ESCENAS, _items, _txt, esc, fromTo, r2

TONOS = ("acc", "up", "down", "warn")
_RE_IMAGEN = re.compile(r"^[\w-]+\.(png|jpg|jpeg|webp)$", re.I)


def _plano(s):
    return _html.escape(str(s), quote=False)       # en el terminal los asteriscos son asteriscos (no acento)


# ---------------------------------------------------------------------------------------------------------------------
# TERMINAL
# ---------------------------------------------------------------------------------------------------------------------
TIPOS_LINEA = ("cmd", "ok", "nota")
MAX_LINEA = 56


def _linea(x):
    if isinstance(x, str):
        return {"t": x, "tipo": "cmd"}
    return {"tipo": "cmd", **x}


def v_terminal(d, err):
    _txt(d, "titulo", err, 30, req=False)
    for x in _items(d, "lineas", err, 2, 6):
        x = _linea(x) if isinstance(x, (str, dict)) else None
        if (not x or not isinstance(x.get("t"), str) or not x["t"].strip() or len(x["t"]) > MAX_LINEA or x["tipo"] not in TIPOS_LINEA
                or (x.get("cuando") is not None and not isinstance(x["cuando"], str))):
            err(f"cada línea del terminal necesita «t» (hasta {MAX_LINEA} caracteres), «tipo» opcional ({', '.join(TIPOS_LINEA)}) y «cuando» opcional")
            break
    ls = [_linea(x) for x in d.get("lineas", []) if isinstance(x, (str, dict))]
    if ls and all(l.get("tipo") != "cmd" for l in ls):
        err("el terminal necesita al menos una línea «cmd» (un comando que se escribe)")


def e_terminal(c, d):
    ls = [_linea(x) for x in d["lineas"]]
    n = len(ls)
    maxlen = max(len(l["t"]) + 2 for l in ls)
    fs = max(24, min(40, int(860 / (0.6 * maxlen))))          # píxeles virtuales (el contexto los escala)
    lh = int(fs * 1.75)
    pref = {"cmd": ("›", "var(--acc)", "var(--text)"), "ok": ("✓", "var(--up)", "var(--up)"), "nota": ("·", "var(--muted)", "var(--muted)")}
    cuerpo = ""
    for k, l in enumerate(ls):
        p, pc, tc = pref[l["tipo"]]
        cuerpo += (f'<div class="h" id="{c.pf}l{k}" style="display:flex;align-items:center;height:{c.px(lh)};font-family:PlexW,monospace;font-weight:700;font-size:{c.fs(fs)};color:{tc}">'
                   f'<span style="display:inline-block;width:1.7ch;color:{pc};font-family:InterW,sans-serif">{p}</span>'
                   f'<span id="{c.pf}t{k}" style="display:inline-block;overflow:hidden;white-space:pre;width:0ch;vertical-align:bottom">{_plano(l["t"])}</span>'
                   f'<span id="{c.pf}c{k}" style="display:inline-block;width:.6ch;height:1.1em;margin-left:.25ch;background:var(--acc);opacity:0"></span></div>')
    barra = (f'<div style="display:flex;align-items:center;gap:{c.px(14)};height:{c.px(82)};padding:0 {c.px(30)};border-bottom:2px solid var(--border)">'
             + "".join(f'<i style="width:{c.px(22)};height:{c.px(22)};border-radius:50%;background:var(--{t})"></i>' for t in ("down", "warn", "up"))
             + f'<span class="lab" style="margin-left:{c.px(18)};font-size:{c.fs(26)}">{_plano(d.get("titulo") or "Terminal")}</span></div>')
    html = (f'<div class="col" style="justify-content:center"><div id="{c.pf}win" class="h" style="background:var(--surface);border:{c.px(3)} solid var(--border);'
            f'border-radius:{c.px(30)};overflow:hidden;box-shadow:0 0 {c.px(46)} color-mix(in srgb,var(--acc) 30%,transparent)">'
            f'{barra}<div style="padding:{c.px(26)} {c.px(34)} {c.px(34)}">{cuerpo}</div></div></div>')
    # calendario: cada comando se escribe a ~25 letras/s; las respuestas (ok / nota) aparecen de golpe
    plan, t = [], c.t0 + .45
    for l in ls:
        if l["tipo"] == "cmd":
            ini = max(t, c.T(l["cuando"], 0) if l.get("cuando") else t)
            dur = min(1.8, max(.5, len(l["t"]) * .04))
        else:
            ini, dur = t, .25
        plan.append((ini, dur))
        t = ini + dur + (.32 if l["tipo"] == "cmd" else .22)
    limite = c.t1 - .6
    if t > limite and t > c.t0 + .45:                            # no cabe: se comprime el calendario
        f = max(.35, (limite - c.t0 - .45) / (t - c.t0 - .45))
        plan = [(c.t0 + .45 + (a - c.t0 - .45) * f, b * f) for a, b in plan]
    js = [fromTo(f"#{c.pf}win", {"opacity": 0, "y": 50, "scale": .96}, {"opacity": 1, "y": 0, "scale": 1, "duration": .5, "ease": "power3.out"}, c.t0 + .05)]
    c.snd(c.t0 + .05, "card", .45)
    for k, (l, (ini, dur)) in enumerate(zip(ls, plan)):
        js.append(fromTo(f"#{c.pf}l{k}", {"opacity": 0}, {"opacity": 1, "duration": .12}, ini))
        if l["tipo"] == "cmd":
            largo = len(l["t"])
            js.append(fromTo(f"#{c.pf}t{k}", {"width": "0ch"}, {"width": f"{largo}ch", "duration": r2(dur), "ease": f"steps({largo})", "immediateRender": False}, ini))
            js.append(f'tl.set("#{c.pf}c{k}",{{opacity:1}},{r2(ini)});')
            fin = ini + dur
            if k == n - 1 or all(x["tipo"] != "cmd" for x in ls[k + 1:]):
                rep = max(0, min(40, int((c.t1 - fin - .3) / .5)))
                js.append(fromTo(f"#{c.pf}c{k}", {"opacity": 1}, {"opacity": 0, "duration": .5, "repeat": rep, "yoyo": True, "ease": "steps(1)", "immediateRender": False}, fin + .05))
            else:
                js.append(f'tl.set("#{c.pf}c{k}",{{opacity:0}},{r2(fin + .12)});')
            c.snd(ini, "click", .35)
            for j in range(1, min(12, largo // 3)):
                c.snd(ini + dur * j * 3 / largo, "tick", .16)
        else:
            js.append(f'tl.set("#{c.pf}t{k}",{{width:"{len(l["t"])}ch"}},{r2(ini)});')
            c.snd(ini, "ding:1" if l["tipo"] == "ok" else "pop:0", .35 if l["tipo"] == "ok" else .22)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# RANKING
# ---------------------------------------------------------------------------------------------------------------------
def v_ranking(d, err):
    _txt(d, "titulo", err, 44, req=False)
    for x in _items(d, "items", err, 2, 4):
        if (not isinstance(x, dict) or not isinstance(x.get("valor"), str) or not x["valor"].strip() or len(x["valor"]) > 8
                or not isinstance(x.get("t"), str) or not x["t"].strip() or len(x["t"]) > 44
                or (x.get("sub") is not None and (not isinstance(x["sub"], str) or len(x["sub"]) > 30))
                or x.get("tono", "acc") not in TONOS):
            err("cada fila del ranking necesita «valor» (texto de hasta 8, p. ej. «3,86x»), «t» (título, hasta 44), «sub» opcional (hasta 30) y «tono» opcional (acc, up, down, warn)")
            break


def e_ranking(c, d):
    it = d["items"]
    n = len(it)
    alto = int(min(215, (880 - (84 if d.get("titulo") else 0) - 24 * (n - 1)) / n))
    filas = ""
    for k, x in enumerate(it):
        tono = x.get("tono", "acc")
        primero = k == 0
        filas += (f'<div id="{c.pf}r{k}" class="h" style="display:flex;align-items:center;gap:{c.px(26)};height:{c.px(alto)};padding:0 {c.px(34)};'
                  f'background:var(--surface);border:{c.px(4 if primero else 3)} solid var({"--acc" if primero else "--border"});border-radius:{c.px(30)};'
                  + (f'box-shadow:0 0 {c.px(36)} color-mix(in srgb,var(--acc) 40%,transparent)' if primero else "") + '">'
                  f'<div id="{c.pf}v{k}" style="flex:none;width:{c.px(318)};font-weight:700;white-space:nowrap;font-size:{c.fs(min(112, alto * .52, 300 / (.6 * max(3, len(x['valor'])))))};letter-spacing:-.03em;line-height:1;color:var(--{tono})">{esc(x["valor"])}</div>'
                  f'<div style="flex:1;min-width:0"><div class="big" style="font-size:{c.fs(44 if len(x["t"]) <= 30 else 38)};line-height:1.1">{esc(x["t"])}</div>'
                  + (f'<div class="lab" style="font-size:{c.fs(25)};margin-top:{c.px(8)}">{esc(x["sub"])}</div>' if x.get("sub") else "") + '</div></div>')
    cab = f'<div id="{c.pf}hd" class="lab h" style="font-size:{c.fs(34)};margin-bottom:{c.px(8)}">{esc(d["titulo"])}</div>' if d.get("titulo") else ""
    html = f'<div class="col" style="justify-content:center;gap:{c.px(24)}">{cab}{filas}</div>'
    js = []
    if cab:
        js.append(fromTo(f"#{c.pf}hd", {"opacity": 0, "y": -20}, {"opacity": 1, "y": 0, "duration": .4, "ease": "power3.out"}, c.t0 + .12))
    for k in range(n):
        t = c.T(it[k].get("cuando"), .12 + .6 * k / max(n - 1, 1))
        js += [fromTo(f"#{c.pf}r{k}", {"opacity": 0, "y": 60, "filter": "blur(18px)"}, {"opacity": 1, "y": 0, "filter": "blur(0px)", "duration": .6, "ease": "power3.out"}, t),
               fromTo(f"#{c.pf}v{k}", {"scale": 1.18}, {"scale": 1, "duration": .5, "ease": "back.out(2.4)", "immediateRender": False}, t + .25)]
        c.snd(t, "swipe", .35)
        c.snd(t + .28, "pop:" + str(k % 4), .42)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# CAPTURA (manual)
# ---------------------------------------------------------------------------------------------------------------------
def v_captura(d, err):
    _txt(d, "titulo", err, 44, req=False)
    _txt(d, "pie", err, 60, req=False)
    im = d.get("imagen")
    if not isinstance(im, str) or not _RE_IMAGEN.match(im):
        err("«imagen» es el nombre de un archivo PNG/JPG/WEBP guardado en <proyecto>/assets/ (solo el nombre, sin carpetas)")
    r = d.get("resalte")
    if r is not None:
        ok = isinstance(r, dict) and all(isinstance(r.get(k), (int, float)) and not isinstance(r.get(k), bool) for k in ("x", "y", "w", "h"))
        if not ok or not (0 <= r["x"] < 100 and 0 <= r["y"] < 100 and 0 < r["w"] <= 100 and 0 < r["h"] <= 100):
            err("«resalte» es {x, y, w, h} en % de la imagen (0-100)")


def e_captura(c, d):
    carpeta = getattr(c, "proyecto", None)
    if carpeta is not None and not (Path(carpeta) / "assets" / d["imagen"]).exists():
        raise ValueError(f"escena {c.i + 1} (captura): falta el archivo assets/{d['imagen']} en el proyecto")
    r = d.get("resalte")
    cab = f'<div id="{c.pf}hd" class="lab h" style="font-size:{c.fs(34)};margin-bottom:{c.px(14)}">{esc(d["titulo"])}</div>' if d.get("titulo") else ""
    pie = f'<div id="{c.pf}pie" class="nota h" style="font-size:{c.fs(34)};text-align:center;margin-top:{c.px(18)}">{esc(d["pie"])}</div>' if d.get("pie") else ""
    caja = ""
    if r:
        caja = (f'<div id="{c.pf}rs" style="position:absolute;left:{r["x"]}%;top:{r["y"]}%;width:{r["w"]}%;height:{r["h"]}%;border:{c.px(6)} solid var(--acc);border-radius:{c.px(10)};'
                f'box-shadow:0 0 0 3000px rgba(4,7,16,.58),0 0 {c.px(30)} var(--acc);opacity:0"></div>')
    origen = f'{r["x"] + r["w"] / 2:.1f}% {r["y"] + r["h"] / 2:.1f}%' if r else "50% 50%"
    html = (f'<div class="col" style="justify-content:center">{cab}'
            f'<div id="{c.pf}marco" class="h" style="position:relative;overflow:hidden;max-height:{c.px(760)};border-radius:{c.px(26)};border:{c.px(3)} solid var(--border);'
            f'box-shadow:0 0 {c.px(40)} color-mix(in srgb,var(--acc) 25%,transparent)">'
            f'<div id="{c.pf}zm" style="position:relative;transform-origin:{origen}"><img src="assets/{d["imagen"]}" alt="" style="display:block;width:100%;height:auto"/>{caja}</div></div>{pie}</div>')
    js = []
    if cab:
        js.append(fromTo(f"#{c.pf}hd", {"opacity": 0, "y": -18}, {"opacity": 1, "y": 0, "duration": .4, "ease": "power3.out"}, c.t0 + .1))
    js.append(fromTo(f"#{c.pf}marco", {"opacity": 0, "y": 60, "scale": .96}, {"opacity": 1, "y": 0, "scale": 1, "duration": .55, "ease": "power3.out"}, c.t0 + .1))
    c.snd(c.t0 + .1, "card", .45)
    if pie:
        js.append(fromTo(f"#{c.pf}pie", {"opacity": 0, "y": 20}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, c.t0 + .9))
    if r:
        t = c.T(d.get("cuando"), .3)
        js += [fromTo(f"#{c.pf}rs", {"opacity": 0, "scale": 1.25}, {"opacity": 1, "scale": 1, "duration": .4, "ease": "back.out(2)"}, t),
               fromTo(f"#{c.pf}zm", {"scale": 1}, {"scale": 1.45, "duration": 1.4, "ease": "power2.inOut", "immediateRender": False}, t + .35)]
        c.snd(t, "impact", .35)
    else:
        js.append(fromTo(f"#{c.pf}zm", {"scale": 1}, {"scale": 1.12, "duration": max(1.0, c.dur), "ease": "none", "immediateRender": False}, c.t0 + .3))
    return html, js


ESCENAS["terminal"] = (e_terminal, v_terminal)
ESCENAS["ranking"] = (e_ranking, v_ranking)
ESCENAS["captura"] = (e_captura, v_captura)
