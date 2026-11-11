"""Formato «novato contra pro»: muñecos 2D (marca/personajes.js), escenas versus, movil, calendario, panel y cierre «compartir»."""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import escenas_versus  # noqa: E402
import fidelidad  # noqa: E402
import motor  # noqa: E402
import storyboard_ia  # noqa: E402
from escenas import ESCENAS, Ctx  # noqa: E402
from guion import validar  # noqa: E402
from paletas import paleta  # noqa: E402

PAL = [{"t": w, "ini": 0.3 * i, "fin": 0.3 * i + 0.25} for i, w in enumerate("primero el novato luego el pro y despues todo cambia cuando mira".split())]


def ctx(W=984, i=2):
    return Ctx(i, 4.0, 14.0, 4.1, 13.5, PAL, W, 1010, paleta("bolsa"))


def val(tipo, d):
    e = []
    ESCENAS[tipo][1](d, e.append)
    return e


# --- los muñecos: el catálogo de Python y el de personajes.js coinciden; sin cifras ni azar -----------------------------
js = (RAIZ / "marca" / "personajes.js").read_text(encoding="utf-8")
ids_js = set(re.findall(r'^acc\("([a-z_]+)"', js, re.M))
assert ids_js == set(escenas_versus.ACCIONES), ids_js ^ set(escenas_versus.ACCIONES)
assert "Math.random" not in js, "los muñecos no usan azar (cada render debe salir igual)"
assert not re.search(r'fillText\("[0-9]', js), "los muñecos no escriben cifras"
assert "versus" in motor.ANCHO_COMPLETO and "panel" in motor.ANCHO_COMPLETO

# --- versus --------------------------------------------------------------------------------------------------------------
V = {"tipo": "versus", "ronda": {"n": "1", "titulo": "ANTES DE ENTRAR"}, "voz": "x", "cuando_pro": "pro",
     "novato": {"accion": "mirar_grafico", "texto": "Compra porque sube", "etiqueta": "Sin plan"},
     "pro": {"accion": "teclear", "texto": "Escribe su plan antes", "tono": "up"}}
assert not val("versus", V), val("versus", V)
assert val("versus", dict(V, novato={"accion": "volar", "texto": "x"})), "acción desconocida"
assert val("versus", dict(V, pro={"accion": "correr", "texto": "x" * 50})), "texto demasiado largo"
assert val("versus", {k: v for k, v in V.items() if k != "pro"}), "falta el pro"
assert val("versus", dict(V, ronda={"n": "1234"})), "ronda demasiado larga"
h, j = ESCENAS["versus"][0](ctx(), V)
assert h.count("<canvas") == 2 and h.count('type="module"') == 2 and "personajes.js" in h and "NOVATO" in h and "PRO" in h and "ANTES DE ENTRAR" in h
assert "pn_novato" in "".join(j) and "0.55" in "".join(j), "al entrar el pro, el novato se atenúa y sube a su sitio"
sin_ronda = ESCENAS["versus"][0](ctx(), {k: v for k, v in V.items() if k != "ronda"})[0]
assert "ron" not in sin_ronda.replace("rol", "")

# --- movil ----------------------------------------------------------------------------------------------------------------
M = {"tipo": "movil", "titulo": "Chat", "voz": "x", "sello": "SATURADO",
     "mensajes": [{"de": "yo", "t": "Dame ideas"}, {"de": "ia", "t": "Aquí tienes las de siempre", "cuando": "luego"}]}
assert not val("movil", M), val("movil", M)
assert val("movil", dict(M, mensajes=[{"de": "yo", "t": "solo uno"}])), "mínimo 2 mensajes"
assert val("movil", dict(M, mensajes=[{"de": "otro", "t": "x"}, {"de": "ia", "t": "y"}])), "quién habla"
h, j = ESCENAS["movil"][0](ctx(), M)
assert "SATURADO" in h and "rotation" in "".join(j) and "Aquí tienes" in h

# --- calendario -----------------------------------------------------------------------------------------------------------
C = {"tipo": "calendario", "titulo": "CONSTANCIA", "voz": "x", "pie": "Sin saltarse el plan",
     "marcas": [{"dia": 0}, {"dia": 1}, {"dia": 2, "tipo": "ok"}, {"dia": 5, "tipo": "fallo"}]}
assert not val("calendario", C), val("calendario", C)
assert val("calendario", dict(C, marcas=[{"dia": 9}])), "día fuera de la semana"
assert val("calendario", dict(C, marcas=[{"dia": 1}, {"dia": 1}])), "día repetido"
h, j = ESCENAS["calendario"][0](ctx(), C)
assert h.count("✓") + h.count("✕") == 7 and "var(--up)" in "".join(j)

# --- panel ----------------------------------------------------------------------------------------------------------------
P = {"tipo": "panel", "titulo": "CANALES", "voz": "x", "busqueda": "canales pequeños",
     "items": [{"n": "Historias ocultas", "valor": "310 K", "sub": "hace 24 días", "badge": "x41"}, {"n": "Datos", "valor": "2,4 M", "tono": "acc"}]}
assert not val("panel", P), val("panel", P)
assert val("panel", dict(P, items=[{"n": "a", "valor": "sin número"}, {"n": "b", "valor": "1"}])), "el valor necesita un número"
assert val("panel", dict(P, items=[{"n": "a", "valor": "1.234"}, {"n": "b", "valor": "1"}])), "sin separador de miles"
h, j = ESCENAS["panel"][0](ctx(), P)
assert "fm(" in "".join(j) and "2,4" not in h.split("s2_v1")[1][:200].split(">")[1][:12], "el contador arranca en cero y cuenta hasta el valor"

# --- cierre «compartir» ---------------------------------------------------------------------------------------------------
assert not val("cta", {"compartir": "ese amigo que compra por impulso"})
assert val("cta", {"compartir": "x" * 50})
h, j = ESCENAS["cta"][0](ctx(i=7), {"compartir": "ese amigo que compra por impulso"})
assert "ese amigo que compra por impulso" in h and "Este eres tú" in h and "Síguenos en WhaleXtreet" in h
assert "Envíaselo" not in ESCENAS["cta"][0](ctx(i=7), {})[0], "sin «compartir» el cierre es el de siempre"

# --- el guion completo valida; fidelidad de las cifras ------------------------------------------------------------------------
sb = {"tema": "bolsa", "tipo_post": "hilo", "escenas": [
    {"tipo": "gancho", "voz": "Mismo dinero, mismo mercado, dos formas distintas.", "texto": "AMATEUR VS PRO", "resalte": "PRO"}, dict(V), dict(M), dict(C), dict(P),
    {"tipo": "cta", "compartir": "ese amigo", "voz": "Envíaselo a ese amigo y síguenos en WhaleXtreet."}]}
validar(sb)
p = fidelidad.comprobar(sb, "texto con 310 K y 2,4 M, hace 24 días, x41")
assert not p, p
p = fidelidad.comprobar(sb, "texto sin esas cifras")
assert any("310" in x for x in p) and any("2.4" in x for x in p), p
sb2 = {"tema": "bolsa", "escenas": [dict(V, novato=dict(V["novato"], etiqueta="4 horas por vídeo"))]}
assert fidelidad.comprobar(sb2, "sin cifras"), "una cifra pequeña en la etiqueta del versus también tiene que venir del post"
assert not fidelidad.comprobar(sb2, "tarda 4 horas por vídeo")

# --- la IA sabe cuándo usarlas ----------------------------------------------------------------------------------------------
for palabra in ("- versus:", "- movil:", "- calendario:", "- panel:", "compartir", "saltar_valla", "SOLO"):
    assert palabra in storyboard_ia.SISTEMA, palabra
assert "__" not in storyboard_ia.SISTEMA.split("RECURSOS ESPECIALES")[1][:3000]
print("OK: formato novato contra pro (muñecos, versus, móvil, calendario, panel, compartir)")
