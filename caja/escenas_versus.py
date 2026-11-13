"""Recursos de formato «novato contra pro» (salen de un vídeo de referencia). Se usan SOLO cuando el tema lo pide: comparar dos maneras de hacer algo,
mostrar una constancia semanal, una conversación en el móvil o un panel de cifras reales. No van en todos los vídeos.

  · «versus»      dos paneles apilados con muñecos 2D animados (marca/personajes.js): arriba el novato (fondo gris con nubes), abajo el pro (fondo del color
                  del tema). Cada panel tiene su acción (correr, teclear, mirar_grafico, saltar_valla, resultado), una frase y una etiqueta opcional.
  · «movil»       pantalla de móvil con una conversación que se escribe sola; con sello opcional (p. ej. SATURADO).
  · «calendario»  semana con casillas que se marcan (✓ cumplido, ✕ fallo): constancia, aportaciones periódicas, hábitos.
  · «panel»       filas con nombre, mini gráfica y una cifra grande que cuenta hasta su valor (cifras SIEMPRE del post).
  · cierre «compartir»  (campo extra de la escena cta): maqueta de chat «Envíaselo a ese amigo que…».

Todo lo que se escribe en pantalla pasa la comprobación de datos reales como en el resto de escenas.
"""
import re

from escenas import ESCENAS, J, _items, _txt, chip, es, esc, fromTo, marca_redes, r2, to

# Qué hace cada acción de los muñecos (la IA elige por esto). Deben coincidir con los ids de marca/personajes.js.
ACCIONES = {
    "correr": "corre por una ciudad: el pro rápido y erguido con estela, el novato lento, encorvado y sudando (ritmo, avance, constancia)",
    "teclear": "sentado ante un portátil con un reloj: el pro trabaja tranquilo y organizado, el novato se agobia y acaba rendido sobre la mesa (preparar, planificar, esfuerzo manual)",
    "mirar_grafico": "ante una pantalla de velas: el novato entra en pánico con la caída y se agarra la cabeza, el pro la mira con calma y con un visto bueno (reaccionar al mercado, emociones)",
    "saltar_valla": "salto de una valla: el pro la supera sin esfuerzo, el novato tropieza y cae (riesgo, obstáculos, preparación)",
    "resultado": "el pro celebra con confeti, el novato se rasca la cabeza sin entender qué ha pasado (resultado final, conclusión)",
}
TONOS = ("acc", "up", "down", "warn")
GRIS = "#8B93A3"


def _panel_ok(x):
    return (isinstance(x, dict) and x.get("accion") in ACCIONES and isinstance(x.get("texto"), str) and 0 < len(x["texto"]) <= 36
            and (x.get("etiqueta") is None or (isinstance(x["etiqueta"], str) and 0 < len(x["etiqueta"]) <= 28))
            and (x.get("chip") is None or (isinstance(x["chip"], str) and 0 < len(x["chip"]) <= 12))
            and x.get("tono", "down") in TONOS)


def lista_acciones_para_gemini():
    return "\n".join(f"  · {k}: {v}" for k, v in ACCIONES.items())


# ---------------------------------------------------------------------------------------------------------------------
# VERSUS
# ---------------------------------------------------------------------------------------------------------------------
def v_versus(d, err):
    r = d.get("ronda")
    if r is not None and not (isinstance(r, dict) and isinstance(r.get("n"), str) and 0 < len(r["n"]) <= 3
                              and (r.get("titulo") is None or (isinstance(r["titulo"], str) and len(r["titulo"]) <= 30))):
        err("«ronda» es {\"n\": \"1\", \"titulo\": \"máx. 30\"}")
    for lado in ("novato", "pro"):
        if not _panel_ok(d.get(lado)):
            err(f"«{lado}» necesita «accion» ({', '.join(ACCIONES)}), «texto» (hasta 36), «etiqueta» opcional (hasta 28), «chip» opcional (hasta 12) y «tono» opcional ({', '.join(TONOS)})")
    if d.get("cuando_pro") is not None and not isinstance(d["cuando_pro"], str):
        err("«cuando_pro» es una palabra de la voz")


MODULO_ACCION = """
import {dibujarAccion} from "./assets/personajes.js";
await document.fonts.load('700 40px InterW');
const cv = document.getElementById("%(id)s"), g = cv.getContext("2d");
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim() || "#ffffff";
const K = {acc: css("--acc"), acc2: css("--acc2"), res: css("--resalte"), up: css("--up"), down: css("--down"), warn: css("--warn"), text: css("--text"), bg: css("--bg")};
const T0 = %(t0)s;
function pintar(t) { dibujarAccion("%(accion)s", g, cv.width, cv.height, Math.max(t - T0, 0), K, {rol: "%(rol)s"}); }
window.addEventListener("hf-seek", e => pintar(e.detail?.time ?? window.__hfThreeTime ?? 0));
pintar(window.__hfThreeTime ?? 0);
"""


def e_versus(c, d):
    r = d.get("ronda")
    cab_h = 96 if r else 0
    gap = 22
    ph = (c.H - cab_h - gap) / 2
    cap_h = 70
    cv_h = ph - cap_h
    tp = c.T(d.get("cuando_pro"), .5)
    cab = ""
    if r:
        cab = (f'<div id="{c.pf}ron" class="h" style="display:flex;align-items:center;gap:{c.px(24)};height:{c.px(cab_h - 12)}">'
               f'<span class="big" style="font-size:{c.fs(88)};color:var(--acc);text-shadow:0 0 {c.px(24)} var(--acc)">{esc(r["n"])}</span>'
               + (f'<span class="big" style="font-size:{c.fs(46)};text-transform:uppercase">{esc(r["titulo"])}</span>' if r.get("titulo") else "") + '</div>')
    paneles, js, mods = "", [], ""
    desplaza = c.n((ph + gap) / 2)
    for lado, t0 in (("novato", c.t0 + .12), ("pro", tp)):
        x = d[lado]
        pro = lado == "pro"
        borde = "var(--acc)" if pro else "#4A5162"
        chipc = "var(--acc)" if pro else GRIS
        ident = f"{c.pf}cv_{lado}"
        et = x.get("etiqueta")
        tono = x.get("tono", "up" if pro else "down")
        brillo = f";box-shadow:0 0 {c.px(40)} color-mix(in srgb,var(--acc) 35%,transparent)" if pro else ""
        paneles += (f'<div id="{c.pf}pn_{lado}" class="h" style="position:relative;height:{c.px(ph)};border-radius:{c.px(30)};overflow:hidden;border:{c.px(3)} solid {borde};'
                    f'background:#14171D{brillo}">'
                    f'<canvas id="{ident}" width="{int(c.W)}" height="{c.n(cv_h)}" style="display:block;width:{int(c.W)}px;height:{c.n(cv_h)}px"></canvas>'
                    f'<span class="chip" style="position:absolute;left:{c.px(20)};top:{c.px(16)};font-size:{c.fs(32)};--c:{chipc}">{esc(x.get("chip") or lado.upper())}</span>'
                    + (f'<span class="chip" style="position:absolute;right:{c.px(20)};top:{c.px(16)};font-size:{c.fs(28)};--c:var(--{tono})">{esc(et)}</span>' if et else "")
                    + f'<div class="big" style="position:absolute;left:0;right:0;bottom:0;height:{c.px(cap_h)};display:flex;align-items:center;justify-content:center;text-align:center;'
                    f'font-size:{c.fs(40)};background:rgba(4,7,16,.45);padding:0 {c.px(20)}">{esc(x["texto"])}</div></div>')
        mods += '<script type="module">' + MODULO_ACCION % {"id": ident, "accion": x["accion"], "rol": lado, "t0": r2(t0 + .05)} + "</script>"
        y0 = 0 if pro else desplaza          # el novato entra CENTRADO (aún no hay panel debajo) y sube a su sitio cuando entra el pro
        js.append(fromTo(f"#{c.pf}pn_{lado}", {"opacity": 0, "y": y0 + (70 if pro else 40), "scale": .97}, {"opacity": 1, "y": y0, "scale": 1, "duration": .5, "ease": "power3.out"}, t0))
        c.snd(t0, "whoosh:" + ("1" if pro else "0"), .45)
        c.snd(t0 + .3, "ding:1" if pro else "pop:1", .35)
    js.append(to(f"#{c.pf}pn_novato", {"opacity": .55, "y": 0, "duration": .5, "ease": "power3.inOut"}, tp))
    if cab:
        js.append(fromTo(f"#{c.pf}ron", {"opacity": 0, "x": -40}, {"opacity": 1, "x": 0, "duration": .4, "ease": "power3.out"}, c.t0 + .05))
        c.snd(c.t0 + .05, "card", .4)
    html = f'<div class="col" style="gap:{c.px(gap)}">{cab}{paneles}</div>{mods}'
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# MÓVIL (conversación)
# ---------------------------------------------------------------------------------------------------------------------
def v_movil(d, err):
    _txt(d, "titulo", err, 20, req=False)
    _txt(d, "sello", err, 14, req=False)
    for x in _items(d, "mensajes", err, 2, 5):
        if (not isinstance(x, dict) or x.get("de") not in ("yo", "ia") or not isinstance(x.get("t"), str) or not x["t"].strip() or len(x["t"]) > 70
                or (x.get("cuando") is not None and not isinstance(x["cuando"], str))):
            err("cada mensaje necesita «de» (yo o ia), «t» (hasta 70 caracteres) y «cuando» opcional")
            break


def e_movil(c, d):
    ms = d["mensajes"]
    n = len(ms)
    pw, ph = 560, min(940, c.H / c.u - 10)
    burbujas = ""
    for k, m in enumerate(ms):
        yo = m["de"] == "yo"
        if yo:
            burbujas += (f'<div id="{c.pf}b{k}" class="h" style="align-self:flex-end;max-width:78%;background:#E4E7F1;color:#1A1F2B;border-radius:{c.px(26)};padding:{c.px(16)} {c.px(24)};'
                         f'font-weight:600;font-size:{c.fs(30)};line-height:1.2">{esc(m["t"])}</div>')
        else:
            burbujas += (f'<div id="{c.pf}p{k}" class="h" style="align-self:flex-start;display:flex;gap:{c.px(8)};padding:{c.px(10)} {c.px(6)}">'
                         + "".join(f'<i id="{c.pf}pd{k}_{j}" style="width:{c.px(14)};height:{c.px(14)};border-radius:50%;background:#9AA3B5"></i>' for j in range(3)) + '</div>'
                         f'<div id="{c.pf}b{k}" class="h" style="align-self:flex-start;max-width:92%;color:#1A1F2B;font-weight:600;font-size:{c.fs(30)};line-height:1.25;padding:{c.px(4)} {c.px(6)}">{esc(m["t"])}</div>')
    sello = (f'<div id="{c.pf}sello" class="h" style="position:absolute;right:{c.px(-10)};top:{c.px(330)};padding:{c.px(6)} {c.px(26)};border:{c.px(9)} solid var(--down);border-radius:{c.px(16)};'
             f'color:var(--down);font-family:PlexW,monospace;font-weight:700;font-size:{c.fs(78)};letter-spacing:.06em;text-transform:uppercase;background:rgba(255,255,255,.78);transform:rotate(-8deg)">{esc(d["sello"])}</div>'
             if d.get("sello") else "")
    html = (f'<div class="col" style="align-items:center;justify-content:center"><div id="{c.pf}tel" class="h" style="position:relative;width:{c.px(pw)};height:{c.px(ph)};background:#F6F7FB;'
            f'border:{c.px(10)} solid #1B1F2A;border-radius:{c.px(70)};box-shadow:0 0 {c.px(40)} color-mix(in srgb,var(--acc) 30%,transparent);overflow:hidden">'
            f'<div style="width:{c.px(150)};height:{c.px(30)};background:#1B1F2A;border-radius:{c.px(16)};margin:{c.px(16)} auto 0"></div>'
            f'<div style="text-align:center;font-weight:700;font-size:{c.fs(30)};color:#1A1F2B;padding:{c.px(16)} 0 {c.px(12)};border-bottom:2px solid #E1E4EE">{esc(d.get("titulo") or "Chat")}</div>'
            f'<div style="display:flex;flex-direction:column;gap:{c.px(14)};padding:{c.px(22)}">{burbujas}</div>{sello}</div></div>')
    js = [fromTo(f"#{c.pf}tel", {"opacity": 0, "y": 80, "scale": .95}, {"opacity": 1, "y": 0, "scale": 1, "duration": .55, "ease": "power3.out"}, c.t0 + .05)]
    c.snd(c.t0 + .05, "card", .45)
    for k, m in enumerate(ms):
        t = c.T(m.get("cuando"), .08 + .62 * k / max(n - 1, 1))
        if m["de"] == "yo":
            js.append(fromTo(f"#{c.pf}b{k}", {"opacity": 0, "y": 30, "scale": .9}, {"opacity": 1, "y": 0, "scale": 1, "duration": .35, "ease": "back.out(2)"}, t))
            c.snd(t, "pop:" + str(k % 4), .4)
        else:                                                    # la respuesta tarda un instante: primero «escribiendo…» y luego el texto
            js.append(f'tl.set("#{c.pf}p{k}",{{opacity:1}},{r2(t)});tl.set("#{c.pf}p{k}",{{display:"none"}},{r2(t + .7)});')
            for j in range(3):
                js.append(fromTo(f"#{c.pf}pd{k}_{j}", {"y": 0}, {"y": -8, "duration": .22, "yoyo": True, "repeat": 3, "ease": "sine.inOut", "immediateRender": False}, t + .12 * j))
            js.append(fromTo(f"#{c.pf}b{k}", {"opacity": 0, "y": 16}, {"opacity": 1, "y": 0, "duration": .4, "ease": "power3.out"}, t + .7))
            c.snd(t, "tick", .25)
            c.snd(t + .7, "swipe", .3)
    if d.get("sello"):
        ts = c.T(d.get("cuando_sello"), .8)
        js.append(fromTo(f"#{c.pf}sello", {"opacity": 0, "scale": 2.4, "rotation": -20}, {"opacity": .96, "scale": 1, "rotation": -8, "duration": .35, "ease": "back.out(1.7)"}, ts))
        c.snd(ts + .22, "impact", .55)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# CALENDARIO (constancia)
# ---------------------------------------------------------------------------------------------------------------------
DIAS = ["L", "M", "X", "J", "V", "S", "D"]


def v_calendario(d, err):
    _txt(d, "titulo", err, 30, req=False)
    _txt(d, "pie", err, 40, req=False)
    _txt(d, "etiqueta", err, 24, req=False)
    vistos = set()
    for x in _items(d, "marcas", err, 1, 7):
        if (not isinstance(x, dict) or not isinstance(x.get("dia"), int) or isinstance(x.get("dia"), bool) or not 0 <= x["dia"] <= 6 or x.get("tipo", "ok") not in ("ok", "fallo")
                or x["dia"] in vistos or (x.get("cuando") is not None and not isinstance(x["cuando"], str))):
            err("cada marca necesita «dia» (0 = lunes … 6 = domingo, sin repetir), «tipo» opcional (ok o fallo) y «cuando» opcional")
            break
        vistos.add(x["dia"])


def e_calendario(c, d):
    ms = sorted(d["marcas"], key=lambda m: m["dia"])
    por_dia = {m["dia"]: m for m in d["marcas"]}
    celda = 104
    cab = (f'<div id="{c.pf}hd" class="h" style="margin-bottom:{c.px(18)}">' + (f'<span class="chip" style="font-size:{c.fs(28)};--c:var(--acc)">{esc(d["etiqueta"])}</span>' if d.get("etiqueta") else "")
           + (f'<div class="big" style="font-size:{c.fs(54)};margin-top:{c.px(12)}">{esc(d["titulo"])}</div>' if d.get("titulo") else "") + '</div>') if (d.get("titulo") or d.get("etiqueta")) else ""
    dias = "".join(f'<div style="width:{c.px(celda)};text-align:center;font-family:PlexW,monospace;font-weight:700;font-size:{c.fs(34)};color:var(--muted)">{x}</div>' for x in DIAS)
    celdas = ""
    for i in range(7):
        celdas += (f'<div id="{c.pf}c{i}" style="position:relative;width:{c.px(celda)};height:{c.px(celda)};border-radius:{c.px(22)};background:var(--raised);border:{c.px(3)} solid var(--border);'
                   f'display:flex;align-items:center;justify-content:center;font-weight:700;font-size:{c.fs(64)};color:transparent">{"✓" if por_dia.get(i, {}).get("tipo", "ok") == "ok" else "✕"}</div>')
    pie = f'<div id="{c.pf}pie" class="pildora h" style="font-size:{c.fs(40)};margin-top:{c.px(26)};align-self:center">{esc(d["pie"])}</div>' if d.get("pie") else ""
    html = (f'<div class="col" style="justify-content:center">{cab}<div id="{c.pf}card" class="h" style="background:var(--surface);border:{c.px(3)} solid var(--border);border-radius:{c.px(34)};padding:{c.px(30)} {c.px(26)};'
            f'box-shadow:0 0 {c.px(40)} color-mix(in srgb,var(--acc) 22%,transparent)"><div style="display:flex;gap:{c.px(12)};margin-bottom:{c.px(14)}">{dias}</div>'
            f'<div style="display:flex;gap:{c.px(12)}">{celdas}</div></div>{pie}</div>')
    js = []
    if cab:
        js.append(fromTo(f"#{c.pf}hd", {"opacity": 0, "y": -20}, {"opacity": 1, "y": 0, "duration": .4, "ease": "power3.out"}, c.t0 + .1))
    js.append(fromTo(f"#{c.pf}card", {"opacity": 0, "y": 60, "scale": .96}, {"opacity": 1, "y": 0, "scale": 1, "duration": .5, "ease": "power3.out"}, c.t0 + .15))
    c.snd(c.t0 + .15, "card", .45)
    for k, m in enumerate(ms):
        t = c.T(m.get("cuando"), .18 + .6 * k / max(len(ms) - 1, 1))
        ok = m.get("tipo", "ok") == "ok"
        css = {"backgroundColor": "var(--up)" if ok else "rgba(150,158,176,.35)", "borderColor": "var(--up)" if ok else "rgba(150,158,176,.6)", "color": "#0B1020" if ok else "#C9CED8"}
        js.append(f'tl.set("#{c.pf}c{m["dia"]}",{J(css)},{r2(t)});')
        js.append(fromTo(f"#{c.pf}c{m['dia']}", {"scale": .6}, {"scale": 1, "duration": .35, "ease": "back.out(3)", "immediateRender": False}, t))
        c.snd(t, "tick" if ok else "error", .4 if ok else .3)
        if ok:
            c.snd(t + .05, "ding:" + str(k % 3), .3)
    if pie:
        js.append(fromTo(f"#{c.pf}pie", {"opacity": 0, "y": 24}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, c.T(d.get("cuando_pie"), .85)))
        c.snd(c.T(d.get("cuando_pie"), .85), "pop:2", .4)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# PANEL (filas con cifra que cuenta)
# ---------------------------------------------------------------------------------------------------------------------
_RE_VALOR = re.compile(r"^([^\d]*)(\d+(?:,\d+)?)(.*)$")


def v_panel(d, err):
    _txt(d, "titulo", err, 30, req=False)
    _txt(d, "busqueda", err, 36, req=False)
    for x in _items(d, "items", err, 2, 4):
        m = _RE_VALOR.match(x.get("valor", "")) if isinstance(x, dict) and isinstance(x.get("valor"), str) else None
        if (not isinstance(x, dict) or not isinstance(x.get("n"), str) or not x["n"].strip() or len(x["n"]) > 28 or not m or len(x["valor"]) > 10 or "." in x["valor"]
                or (x.get("sub") is not None and (not isinstance(x["sub"], str) or len(x["sub"]) > 20))
                or (x.get("badge") is not None and (not isinstance(x["badge"], str) or len(x["badge"]) > 8)) or x.get("tono", "up") not in TONOS):
            err("cada fila del panel necesita «n» (hasta 28), «valor» (hasta 10, con un número: usa coma decimal y sin separador de miles, p. ej. «2,4 M»), «sub» opcional (hasta 20), «badge» opcional (hasta 8) y «tono» opcional")
            break


def e_panel(c, d):
    it = d["items"]
    n = len(it)
    alto = int(min(200, (860 - (150 if d.get("busqueda") or d.get("titulo") else 0) - 22 * (n - 1)) / n))
    cab = ""
    if d.get("titulo") or d.get("busqueda"):
        cab = (f'<div id="{c.pf}hd" class="h" style="margin-bottom:{c.px(6)}">' + (f'<div class="lab" style="font-size:{c.fs(32)}">{esc(d["titulo"])}</div>' if d.get("titulo") else "")
               + (f'<div style="margin-top:{c.px(12)};padding:{c.px(14)} {c.px(26)};border-radius:{c.px(18)};background:var(--raised);border:2px solid var(--border);font-weight:600;font-size:{c.fs(32)};color:var(--muted)">⌕ {esc(d["busqueda"])}</div>' if d.get("busqueda") else "") + '</div>')
    filas, js = "", []
    for k, x in enumerate(it):
        tono = x.get("tono", "up")
        pre, num, suf = _RE_VALOR.match(x["valor"]).groups()
        dec = len(num.split(",")[1]) if "," in num else 0
        v = float(num.replace(",", "."))
        filas += (f'<div id="{c.pf}r{k}" class="h" style="display:flex;align-items:center;gap:{c.px(22)};height:{c.px(alto)};padding:0 {c.px(28)};background:var(--surface);border:{c.px(3)} solid var(--border);border-radius:{c.px(28)}">'
                  f'<div style="flex:none;width:{c.px(78)};height:{c.px(78)};border-radius:50%;background:color-mix(in srgb,var(--{tono}) 28%,transparent);border:{c.px(4)} solid var(--{tono});display:flex;align-items:center;justify-content:center;font-size:{c.fs(34)};color:var(--{tono})">▶</div>'
                  f'<div style="flex:1;min-width:0"><div class="big" style="font-size:{c.fs(38)};line-height:1.1">{esc(x["n"])}</div>'
                  + (f'<div class="lab" style="font-size:{c.fs(24)};margin-top:{c.px(6)}">{esc(x["sub"])}</div>' if x.get("sub") else "") + '</div>'
                  + (f'<span class="chip" style="font-size:{c.fs(26)};--c:var(--warn)">{esc(x["badge"])}</span>' if x.get("badge") else "")
                  + f'<svg viewBox="0 0 100 40" style="flex:none;width:{c.px(130)};height:{c.px(52)}" fill="none" stroke="var(--{tono})" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">'
                  f'<path id="{c.pf}sp{k}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" d="M2 34 L22 28 L42 30 L62 18 L82 20 L98 5"/></svg>'
                  f'<div id="{c.pf}v{k}" class="big" style="flex:none;min-width:{c.px(190)};text-align:right;font-size:{c.fs(min(70, 640 / max(len(x["valor"]), 4)))};color:var(--{tono})">{esc(pre + es(0, dec) + suf)}</div></div>')
        t = c.T(x.get("cuando"), .12 + .55 * k / max(n - 1, 1))
        js += [fromTo(f"#{c.pf}r{k}", {"opacity": 0, "y": 50}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, t),
               fromTo(f"#{c.pf}sp{k}", {"attr": {"stroke-dashoffset": 1}}, {"attr": {"stroke-dashoffset": 0}, "duration": 1.0, "ease": "power2.out", "immediateRender": False}, t + .2),
               f'const {c.pf}o{k}={{v:0}};tl.to({c.pf}o{k},{{v:{v},duration:1.1,ease:"power2.out",onUpdate(){{document.getElementById("{c.pf}v{k}").textContent={J(pre)}+fm({c.pf}o{k}.v,{dec})+{J(suf)}}}}},{r2(t + .15)});']
        c.snd(t, "card", .4)
        c.snd(t + 1.2, "ding:" + str(k % 3), .3)
    if cab:
        js.append(fromTo(f"#{c.pf}hd", {"opacity": 0, "y": -20}, {"opacity": 1, "y": 0, "duration": .4, "ease": "power3.out"}, c.t0 + .1))
    html = f'<div class="col" style="justify-content:center;gap:{c.px(22)}">{cab}{filas}</div>'
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# CIERRE «COMPARTIR»: se llama desde la escena cta cuando trae el campo «compartir»
# ---------------------------------------------------------------------------------------------------------------------
def e_compartir(c, d):
    cfg = marca_redes()
    quien = d["compartir"]
    redes = d.get("redes") or cfg["redes"]
    pills = "".join(f'<span class="pildora h" id="{c.pf}r{j}" style="font-size:{c.fs(34)};margin:{c.px(6)}">{esc(x)}</span>' for j, x in enumerate(redes))
    html = (f'<div class="col" style="align-items:center;justify-content:center;text-align:center;gap:{c.px(20)}">'
            f'<div id="{c.pf}tx" class="big h" style="font-size:{c.fs(68)};padding:0 {c.px(10)}">Envíaselo a<br><span style="color:var(--acc)">{esc(quien)}</span></div>'
            f'<div id="{c.pf}tel" class="h" style="width:{c.px(500)};background:#F6F7FB;border:{c.px(9)} solid #1B1F2A;border-radius:{c.px(56)};padding:{c.px(20)} {c.px(22)} {c.px(26)};text-align:left;box-shadow:0 0 {c.px(36)} color-mix(in srgb,var(--acc) 30%,transparent)">'
            f'<div style="font-weight:700;font-size:{c.fs(28)};color:#1A1F2B;border-bottom:2px solid #E1E4EE;padding-bottom:{c.px(12)}">‹ Ese amigo <span style="font-weight:600;color:#6B7384;font-size:{c.fs(22)}">en línea</span></div>'
            f'<div id="{c.pf}vid" class="h" style="margin:{c.px(16)} 0 {c.px(10)} auto;width:{c.px(250)};height:{c.px(150)};border-radius:{c.px(18)};background:linear-gradient(135deg,#0B1020,color-mix(in srgb,var(--acc) 60%,#0B1020));display:flex;align-items:center;justify-content:center;color:#fff;font-size:{c.fs(54)}">▶</div>'
            f'<div id="{c.pf}rp" class="h" style="margin-left:auto;width:max-content;background:#D6F5E0;color:#1A1F2B;font-weight:600;font-size:{c.fs(28)};border-radius:{c.px(20)};padding:{c.px(10)} {c.px(18)}">Este eres tú ✓✓</div></div>'
            f'<div style="display:flex;flex-wrap:wrap;justify-content:center">{pills}</div>'
            f'<div id="{c.pf}sg" class="big h" style="font-size:{c.fs(46)};color:var(--acc)">{esc(cfg["cta_texto"])}</div></div>')
    t = c.t0
    js = [fromTo(f"#{c.pf}tx", {"opacity": 0, "y": 30}, {"opacity": 1, "y": 0, "duration": .5, "ease": "power3.out"}, t + .1),
          fromTo(f"#{c.pf}tel", {"opacity": 0, "y": 70, "scale": .95}, {"opacity": 1, "y": 0, "scale": 1, "duration": .55, "ease": "power3.out"}, t + .35),
          fromTo(f"#{c.pf}vid", {"opacity": 0, "x": 60}, {"opacity": 1, "x": 0, "duration": .4, "ease": "power3.out"}, t + 1.0),
          fromTo(f"#{c.pf}rp", {"opacity": 0, "y": 20, "scale": .85}, {"opacity": 1, "y": 0, "scale": 1, "duration": .4, "ease": "back.out(2)"}, c.T(d.get("cuando_respuesta"), .8))]
    c.snd(t + .1, "card", .45)
    c.snd(t + .35, "whoosh:1", .35)
    c.snd(t + 1.0, "swipe", .35)
    c.snd(c.T(d.get("cuando_respuesta"), .8), "pop:1", .45)
    for j in range(len(redes)):
        js.append(fromTo(f"#{c.pf}r{j}", {"opacity": 0, "scale": .5}, {"opacity": 1, "scale": 1, "duration": .35, "ease": "back.out(3)"}, t + 1.4 + .15 * j))
        c.snd(t + 1.4 + .15 * j, "pop:" + str(j % 4), .4)
    js.append(fromTo(f"#{c.pf}sg", {"opacity": 0, "y": 20}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, t + 1.4 + .15 * len(redes) + .1))
    return html, js


def e_comenta(c, d):
    """Cierre con oferta: «COMENTA «PALABRA» y sígueme · te envío <qué> por privado». Comentar le dice a la red que el vídeo interesa y seguir da seguidores."""
    cfg = marca_redes()
    o = d["oferta"]
    palabra = o["palabra"]
    redes = d.get("redes") or cfg["redes"]
    pills = "".join(f'<span class="pildora h" id="{c.pf}r{j}" style="font-size:{c.fs(34)};margin:{c.px(6)}">{esc(x)}</span>' for j, x in enumerate(redes))
    fs = min(150, int(860 / (0.8 * max(len(palabra) + 2, 6))))
    html = (f'<div class="col" style="align-items:center;justify-content:center;text-align:center;gap:{c.px(24)}">'
            f'<img class="h" id="{c.pf}logo" src="assets/isotipo-cierre.png" alt="" style="width:{c.px(220)}"/>'
            f'{chip(c, "COMENTA", c.pf + "chip", 44)}'
            f'<div id="{c.pf}kw" class="big h" style="font-size:{c.fs(fs)};color:var(--acc);padding:{c.px(10)} {c.px(40)};border:{c.px(8)} solid var(--acc);border-radius:{c.px(36)};'
            f'background:color-mix(in srgb,var(--acc) 12%,#0B1020);text-shadow:0 0 {c.px(30)} var(--acc);box-shadow:0 0 {c.px(50)} color-mix(in srgb,var(--acc) 45%,transparent)">«{esc(palabra)}»</div>'
            f'<div id="{c.pf}sg" class="big h" style="font-size:{c.fs(74)}">y <span style="color:var(--acc)">sígueme</span></div>'
            f'<div id="{c.pf}qe" class="nota h" style="font-size:{c.fs(44)};padding:0 {c.px(16)}">te envío {esc(o["que"])} por privado</div>'
            f'<div style="display:flex;flex-wrap:wrap;justify-content:center">{pills}</div></div>')
    t = c.t0
    tk, ts, tq = c.T(palabra, .12), c.T("sígueme", .42), c.T("envío", .62)       # cada elemento entra cuando la voz lo dice
    js = [fromTo(f"#{c.pf}logo", {"opacity": 0, "scale": .7}, {"opacity": 1, "scale": 1, "duration": .5, "ease": "back.out(1.8)"}, t + .1),
          fromTo(f"#{c.pf}chip", {"opacity": 0, "scale": .6}, {"opacity": 1, "scale": 1, "duration": .4, "ease": "back.out(2.4)"}, t + .4),
          fromTo(f"#{c.pf}kw", {"opacity": 0, "scale": 1.7}, {"opacity": 1, "scale": 1, "duration": .45, "ease": "back.out(1.7)"}, max(tk, t + .6)),
          fromTo(f"#{c.pf}sg", {"opacity": 0, "y": 30}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, max(ts, t + 1.0)),
          fromTo(f"#{c.pf}qe", {"opacity": 0, "y": 24}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, max(tq, t + 1.4))]
    c.snd(t + .1, "card", .45)
    c.snd(t + .4, "ding:1", .4)
    c.snd(max(tk, t + .6) + .25, "impact", .5)
    c.snd(max(ts, t + 1.0), "pop:2", .4)
    c.snd(max(tq, t + 1.4), "swipe", .3)
    for j in range(len(redes)):
        js.append(fromTo(f"#{c.pf}r{j}", {"opacity": 0, "scale": .5}, {"opacity": 1, "scale": 1, "duration": .35, "ease": "back.out(3)"}, t + 1.8 + .15 * j))
        c.snd(t + 1.8 + .15 * j, "pop:" + str(j % 4), .4)
    return html, js


def e_comenta_libre(c, d):
    """Cierre «COMENTA <algo> y sígueme · <para qué>»: invita a opinar y a seguir la cuenta, sin prometer ningún recurso (series por partes, vídeos de análisis)."""
    cm = d["comenta"]
    que = cm["que"].upper()
    redes = d.get("redes") or marca_redes()["redes"]
    pills = "".join(f'<span class="pildora h" id="{c.pf}r{j}" style="font-size:{c.fs(34)};margin:{c.px(6)}">{esc(x)}</span>' for j, x in enumerate(redes))
    fs = min(120, int(860 / (0.62 * max(len(que) + 2, 6))))
    html = (f'<div class="col" style="align-items:center;justify-content:center;text-align:center;gap:{c.px(24)}">'
            f'<img class="h" id="{c.pf}logo" src="assets/isotipo-cierre.png" alt="" style="width:{c.px(220)}"/>'
            f'{chip(c, "COMENTA", c.pf + "chip", 44)}'
            f'<div id="{c.pf}kw" class="big h" style="font-size:{c.fs(fs)};color:var(--acc);padding:{c.px(10)} {c.px(40)};border:{c.px(8)} solid var(--acc);border-radius:{c.px(36)};'
            f'background:color-mix(in srgb,var(--acc) 12%,#0B1020);text-shadow:0 0 {c.px(30)} var(--acc);box-shadow:0 0 {c.px(50)} color-mix(in srgb,var(--acc) 45%,transparent)">{esc(que)}</div>'
            f'<div id="{c.pf}sg" class="big h" style="font-size:{c.fs(74)}">y <span style="color:var(--acc)">sígueme</span></div>'
            + (f'<div id="{c.pf}qe" class="nota h" style="font-size:{c.fs(44)};padding:0 {c.px(16)}">{esc(cm["sigue"])}</div>' if cm.get("sigue") else "")
            + f'<div style="display:flex;flex-wrap:wrap;justify-content:center">{pills}</div></div>')
    t = c.t0
    tk, ts, tq = c.T(cm["que"].split()[0], .12), c.T("sígueme", .42), c.T(cm["sigue"].split()[0] if cm.get("sigue") else None, .7)
    js = [fromTo(f"#{c.pf}logo", {"opacity": 0, "scale": .7}, {"opacity": 1, "scale": 1, "duration": .5, "ease": "back.out(1.8)"}, t + .1),
          fromTo(f"#{c.pf}chip", {"opacity": 0, "scale": .6}, {"opacity": 1, "scale": 1, "duration": .4, "ease": "back.out(2.4)"}, t + .4),
          fromTo(f"#{c.pf}kw", {"opacity": 0, "scale": 1.7}, {"opacity": 1, "scale": 1, "duration": .45, "ease": "back.out(1.7)"}, max(tk, t + .6)),
          fromTo(f"#{c.pf}sg", {"opacity": 0, "y": 30}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, max(ts, t + 1.0))]
    if cm.get("sigue"):
        js.append(fromTo(f"#{c.pf}qe", {"opacity": 0, "y": 24}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, max(tq, t + 1.4)))
        c.snd(max(tq, t + 1.4), "swipe", .3)
    c.snd(t + .1, "card", .45)
    c.snd(t + .4, "ding:1", .4)
    c.snd(max(tk, t + .6) + .25, "impact", .5)
    c.snd(max(ts, t + 1.0), "pop:2", .4)
    for j in range(len(redes)):
        js.append(fromTo(f"#{c.pf}r{j}", {"opacity": 0, "scale": .5}, {"opacity": 1, "scale": 1, "duration": .35, "ease": "back.out(3)"}, t + 1.8 + .15 * j))
        c.snd(t + 1.8 + .15 * j, "pop:" + str(j % 4), .4)
    return html, js


ESCENAS["versus"] = (e_versus, v_versus)
ESCENAS["movil"] = (e_movil, v_movil)
ESCENAS["calendario"] = (e_calendario, v_calendario)
ESCENAS["panel"] = (e_panel, v_panel)
