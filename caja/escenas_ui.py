"""Escenas de «interfaz» con aire de panel de control: recuadros de fase numerados y listas con ticks verdes.

  · «pasos»     recuadros con marco de neón, número grande, icono y título subrayado que entran uno a uno al decir cada palabra clave
                («FASE 1 · TU PLAN»  →  01 TU PRESUPUESTO · 02 TU FONDO · 03 TU INVERSIÓN).
  · «checklist» casillas que se marcan con un tick verde dibujado a mano al decir cada punto, con contador (2/5) y barra de progreso.

Los números «01», «02»… y el contador son solo numeración (no son datos). Cualquier cifra que escriba la IA en los textos pasa la comprobación de
datos reales como en el resto de escenas.
"""
from escenas import ESCENAS, _items, _txt, esc, fromTo, r2, to

ICONOS_PASO = {
    "persona": '<circle cx="50" cy="32" r="16"/><path d="M18 88 C18 62 82 62 82 88"/>',
    "barras": '<path d="M16 86 V54 M42 86 V30 M68 86 V44 M90 86 V16" />',
    "diana": '<circle cx="50" cy="50" r="38"/><circle cx="50" cy="50" r="22"/><circle cx="50" cy="50" r="6" fill="currentColor"/>',
    "etiqueta": '<path d="M10 52 L50 12 H88 V50 L48 90 Z"/><circle cx="68" cy="32" r="6" fill="currentColor"/>',
    "moneda": '<circle cx="50" cy="50" r="38"/><path d="M50 28 V72 M38 40 H58 C66 40 66 52 58 52 H42 C34 52 34 64 42 64 H62"/>',
    "reloj": '<circle cx="50" cy="50" r="38"/><path d="M50 26 V50 L68 62"/>',
    "lupa": '<circle cx="42" cy="42" r="28"/><path d="M64 64 L90 90"/>',
    "escudo": '<path d="M50 10 L86 24 V50 C86 72 68 86 50 92 C32 86 14 72 14 50 V24 Z"/><path d="M34 50 L46 62 L68 38"/>',
    "candado": '<rect x="20" y="44" width="60" height="44" rx="8"/><path d="M32 44 V30 C32 12 68 12 68 30 V44"/>',
    "rayo": '<path d="M56 8 L22 56 H46 L40 92 L78 40 H54 Z"/>',
    "libro": '<path d="M12 22 C28 14 42 16 50 24 C58 16 72 14 88 22 V80 C72 72 58 74 50 82 C42 74 28 72 12 80 Z M50 24 V82"/>',
    "cartera": '<rect x="12" y="26" width="76" height="56" rx="10"/><path d="M12 42 H88"/><circle cx="72" cy="62" r="5" fill="currentColor"/>',
    "grafico": '<path d="M10 80 L34 54 L52 68 L90 20"/><path d="M68 20 H90 V42"/>',
    "check": '<circle cx="50" cy="50" r="38"/><path d="M32 52 L45 65 L70 38"/>',
}
ORDEN_ICONOS = ["persona", "barras", "diana", "etiqueta", "moneda", "reloj"]


def _icono(nombre, px):
    return (f'<svg viewBox="0 0 100 100" width="{px}" height="{px}" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">'
            f'{ICONOS_PASO[nombre]}</svg>')


def lista_iconos():
    return ", ".join(ICONOS_PASO)


# ---------------------------------------------------------------------------------------------------------------------
# PASOS
# ---------------------------------------------------------------------------------------------------------------------
def v_pasos(d, err):
    _txt(d, "fase", err, 30, req=False)
    _txt(d, "titulo", err, 44, req=False)
    for x in _items(d, "items", err, 2, 4):
        if (not isinstance(x, dict) or not isinstance(x.get("n"), str) or not x["n"] or len(x["n"]) > 24
                or (x.get("etiqueta") is not None and (not isinstance(x["etiqueta"], str) or len(x["etiqueta"]) > 28))
                or (x.get("icono") is not None and x["icono"] not in ICONOS_PASO)):
            err(f"cada paso necesita «n» (título, hasta 24), «etiqueta» opcional (hasta 28) e «icono» opcional ({lista_iconos()})")
            break


def e_pasos(c, d):
    it = d["items"]
    n = len(it)
    alto = int(min(236, (930 - (86 if d.get("fase") or d.get("titulo") else 0) - 22 * (n - 1)) / n))
    cab = ""
    if d.get("fase") or d.get("titulo"):
        cab = (f'<div id="{c.pf}fase" class="h" style="display:flex;align-items:center;gap:{c.px(18)};margin-bottom:{c.px(12)}">'
               + (f'<span class="chip" style="font-size:{c.px(30)};--c:var(--acc)">{esc(d["fase"])}</span>' if d.get("fase") else "")
               + (f'<span class="lab" style="font-size:{c.px(32)}">{esc(d["titulo"])}</span>' if d.get("titulo") else "") + '</div>')
    tarj = ""
    for k, x in enumerate(it):
        ico = x.get("icono") or ORDEN_ICONOS[k % len(ORDEN_ICONOS)]
        et = x.get("etiqueta")
        tarj += (f'<div id="{c.pf}c{k}" class="h" style="position:relative;display:flex;align-items:center;gap:{c.px(26)};height:{c.px(alto)};padding:0 {c.px(30)};'
                 f'border:{c.px(4)} solid var(--acc);border-radius:{c.px(26)};'
                 f'background:linear-gradient(100deg,color-mix(in srgb,var(--acc) 16%,var(--surface)),var(--surface) 70%);'
                 f'box-shadow:0 0 {c.px(34)} color-mix(in srgb,var(--acc) 50%,transparent), inset 0 0 {c.px(30)} color-mix(in srgb,var(--acc) 14%,transparent)">'
                 f'<div style="flex:none;width:{c.px(104)};text-align:center;font-family:PlexW,monospace;font-weight:700;font-size:{c.px(76)};line-height:1;color:var(--acc);'
                 f'text-shadow:0 0 {c.px(22)} var(--acc)">{k + 1:02d}</div>'
                 f'<div style="flex:1;min-width:0">'
                 + (f'<div class="lab" style="font-size:{c.px(26)};margin-bottom:{c.px(6)};color:var(--acc2)">{esc(et)}</div>' if et else "")
                 + f'<div class="big" style="font-size:{c.px(58 if len(x["n"]) <= 16 else 48)};line-height:1.05;text-transform:uppercase">{esc(x["n"])}</div>'
                 f'<div id="{c.pf}u{k}" style="height:{c.px(7)};width:{c.px(190)};border-radius:{c.px(4)};background:var(--resalte);margin-top:{c.px(10)};transform-origin:left center;transform:scaleX(0);'
                 f'box-shadow:0 0 {c.px(14)} var(--resalte)"></div></div>'
                 f'<div style="flex:none;color:var(--acc);filter:drop-shadow(0 0 {c.px(10)} var(--acc))">{_icono(ico, c.n(96))}</div></div>')
    html = f'<div class="col" style="justify-content:center;gap:{c.px(22)}">{cab}{tarj}</div>'
    js = []
    if cab:
        js.append(fromTo(f"#{c.pf}fase", {"opacity": 0, "y": -24}, {"opacity": 1, "y": 0, "duration": .4, "ease": "power3.out"}, c.t0 + .15))
        c.snd(c.t0 + .15, "swipe", .35)
    for k in range(n):
        t = c.T(it[k].get("cuando"), .12 + .6 * k / max(n - 1, 1))
        js += [fromTo(f"#{c.pf}c{k}", {"opacity": 0, "x": -90, "scale": .94}, {"opacity": 1, "x": 0, "scale": 1, "duration": .45, "ease": "back.out(1.6)"}, t),
               fromTo(f"#{c.pf}u{k}", {"scaleX": 0}, {"scaleX": 1, "duration": .5, "ease": "power3.out", "immediateRender": False}, t + .25),
               fromTo(f"#{c.pf}c{k}", {"filter": "brightness(1.9)"}, {"filter": "brightness(1)", "duration": .5, "ease": "power2.out", "immediateRender": False}, t)]
        c.snd(t, "whoosh:" + str(k % 3), .42)
        c.snd(t + .2, "pop:" + str(k % 4), .45)
        c.snd(t + .45, "ding:" + str(k % 3), .3)
    return html, js


# ---------------------------------------------------------------------------------------------------------------------
# CHECKLIST
# ---------------------------------------------------------------------------------------------------------------------
def v_checklist(d, err):
    _txt(d, "titulo", err, 44)
    _txt(d, "etiqueta", err, 24, req=False)
    for x in _items(d, "items", err, 2, 6):
        t = x.get("t") if isinstance(x, dict) else x
        if not isinstance(t, str) or not t or len(t) > 40:
            err("cada punto de la checklist debe ser un texto de hasta 40 caracteres")
            break


def e_checklist(c, d):
    it = [x if isinstance(x, dict) else {"t": x} for x in d["items"]]
    n = len(it)
    alto = int(min(132, (700 - 20 * (n - 1)) / n))
    filas = ""
    for k, x in enumerate(it):
        filas += (f'<div id="{c.pf}r{k}" class="h" style="display:flex;align-items:center;gap:{c.px(26)};height:{c.px(alto)};padding:0 {c.px(30)};'
                  f'background:var(--surface);border:{c.px(3)} solid var(--border);border-radius:{c.px(22)}">'
                  f'<div id="{c.pf}b{k}" style="flex:none;width:{c.px(alto * .56)};height:{c.px(alto * .56)};border:{c.px(5)} solid var(--muted);border-radius:{c.px(12)};'
                  f'display:flex;align-items:center;justify-content:center">'
                  f'<svg viewBox="0 0 100 100" width="{c.n(alto * .5)}" height="{c.n(alto * .5)}" fill="none" stroke="var(--up)" stroke-width="16" stroke-linecap="round" stroke-linejoin="round">'
                  f'<path id="{c.pf}t{k}" d="M16 54 L40 78 L86 24" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" style="filter:drop-shadow(0 0 6px var(--up))"/></svg></div>'
                  f'<div class="big" style="font-size:{c.px(48 if len(x["t"]) <= 26 else 40)};line-height:1.1">{esc(x["t"])}</div></div>')
    cont = "".join(f'<span id="{c.pf}n{j}" style="position:absolute;right:0;top:0;opacity:{1 if j == 0 else 0}">{j}/{n}</span>' for j in range(n + 1))
    cab = (f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:{c.px(10)}">'
           f'<div id="{c.pf}hd" class="h"><div class="chip" style="font-size:{c.px(28)};--c:var(--up)">{esc(d.get("etiqueta") or "CHECKLIST")}</div>'
           f'<div class="big" style="font-size:{c.px(58)};margin-top:{c.px(12)}">{esc(d["titulo"])}</div></div>'
           f'<div style="position:relative;width:{c.px(190)};height:{c.px(90)};font-family:PlexW,monospace;font-weight:700;font-size:{c.px(76)};color:var(--up);'
           f'text-shadow:0 0 {c.px(18)} var(--up)">{cont}</div></div>')
    barra = (f'<div style="height:{c.px(16)};border-radius:{c.px(8)};background:var(--raised);margin-top:{c.px(8)};overflow:hidden">'
             f'<div id="{c.pf}pg" style="height:100%;width:100%;transform-origin:left center;transform:scaleX(0);background:var(--up);box-shadow:0 0 {c.px(16)} var(--up)"></div></div>')
    html = f'<div class="col" style="justify-content:center;gap:{c.px(18)}">{cab}{filas}{barra}</div>'
    js = [fromTo(f"#{c.pf}hd", {"opacity": 0, "y": -22}, {"opacity": 1, "y": 0, "duration": .4, "ease": "power3.out"}, c.t0 + .12)]
    c.snd(c.t0 + .12, "card", .4)
    for k in range(n):
        t = c.T(it[k].get("cuando"), .18 + .62 * k / max(n - 1, 1))
        tk = t + .32
        js += [fromTo(f"#{c.pf}r{k}", {"opacity": 0, "x": 60}, {"opacity": 1, "x": 0, "duration": .35, "ease": "power3.out"}, t),
               f'tl.set("#{c.pf}b{k}",{{borderColor:"var(--up)",backgroundColor:"rgba(110,231,168,.16)"}},{r2(tk)});',
               f'tl.set("#{c.pf}r{k}",{{borderColor:"var(--up)"}},{r2(tk)});',
               fromTo(f"#{c.pf}t{k}", {"attr": {"stroke-dashoffset": 1}}, {"attr": {"stroke-dashoffset": 0}, "duration": .28, "ease": "power2.out", "immediateRender": False}, tk),
               fromTo(f"#{c.pf}b{k}", {"scale": .7}, {"scale": 1, "duration": .3, "ease": "back.out(3)", "immediateRender": False}, tk),
               f'tl.set("#{c.pf}n{k}",{{opacity:0}},{r2(tk)});',
               f'tl.set("#{c.pf}n{k + 1}",{{opacity:1}},{r2(tk)});',
               fromTo(f"#{c.pf}pg", {"scaleX": k / n}, {"scaleX": (k + 1) / n, "duration": .3, "ease": "power2.out", "immediateRender": False}, tk)]
        c.snd(t, "swipe", .3)
        c.snd(tk, "tick", .4)
        c.snd(tk + .05, "ding:" + str(k % 3), .38)
    return html, js


ESCENAS["pasos"] = (e_pasos, v_pasos)
ESCENAS["checklist"] = (e_checklist, v_checklist)
