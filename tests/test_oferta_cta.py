"""Cierre con oferta: «Comenta X y sígueme y te envío Y por privado». La palabra y el recurso salen del post (nunca de la IA); sin oferta en el post no se promete nada."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import storyboard_ia  # noqa: E402
from escenas import ESCENAS, Ctx  # noqa: E402
from guion import lineas, validar  # noqa: E402
from paletas import paleta  # noqa: E402

NOMBRE = "la guía en PDF para instalar las 11 skills de trading en Claude"
POST = {"id": "t1", "format": "oferta", "platforms": ["x"], "oferta": {"keyword": "CLAUDE", "name": NOMBRE},
        "parts": ["1/ 11 ayudantes de trading dentro de Claude 🧵", "2/ Uno escanea gráficos y otro fija tu stop antes de entrar.",
                  "3/ Nada se ejecuta sin que tú digas que sí.", "4/ Comenta «CLAUDE» y sígueme, y te envío la guía por privado."]}
SIN_OFERTA = {k: v for k, v in POST.items() if k != "oferta"} | {"format": "hilo"}


def val(d):
    e = []
    ESCENAS["cta"][1](d, e.append)
    return e


def ctx():
    return Ctx(5, 4.0, 14.0, 4.1, 13.5, [{"t": "x", "ini": 0.3, "fin": 0.5}], 984, 1010, paleta("bolsa"))


# --- el resumen del recurso -------------------------------------------------------------------------------------------------------------
assert storyboard_ia.resumen_oferta(NOMBRE) == "la guía en PDF"
assert storyboard_ia.resumen_oferta("una plantilla de plan de trading") == "una plantilla de plan de trading"
assert len(storyboard_ia.resumen_oferta("una guía larguísima " * 6)) <= 40

CHECK = {"keyword": "CHECKLIST", "name": "la checklist de 10 preguntas antes de comprar una acción", "short": "la checklist en PDF"}
assert storyboard_ia.cierre(dict(POST, oferta=CHECK), {})["oferta"] == {"palabra": "CHECKLIST", "que": "la checklist en PDF"}, "usa el texto corto de la oferta"
sin_corto = storyboard_ia.cierre(dict(POST, oferta={k: v for k, v in CHECK.items() if k != "short"}), {})["oferta"]["que"]
assert 3 <= len(sin_corto) <= 40, "sin texto corto, el resumen automático sigue cabiendo"

# --- el cierre lo decide el código ----------------------------------------------------------------------------------------------------------
assert storyboard_ia.cierre(POST, {}) == {"tipo": "cta", "oferta": {"palabra": "CLAUDE", "que": "la guía en PDF"}}
assert storyboard_ia.cierre(POST, {"tipo": "cta", "oferta": {"palabra": "OTRA", "que": "algo"}, "voz": "inventada"}) == storyboard_ia.cierre(POST, {}), "la IA no decide la oferta"
assert storyboard_ia.cierre(SIN_OFERTA, {"tipo": "cta", "oferta": {"palabra": "GUIA", "que": "una guía"}}) == {"tipo": "cta"}, "sin oferta en el post, no se promete nada"
c = storyboard_ia.cierre(SIN_OFERTA, {"tipo": "cta", "compartir": "ese amigo que compra por impulso, "})
assert c["compartir"] == "ese amigo que compra por impulso" and "síguenos en WhaleXtreet" in c["voz"], c
assert storyboard_ia.cierre(SIN_OFERTA, {"tipo": "cta", "voz": "texto libre"}) == {"tipo": "cta"}, "el cierre normal no admite texto de la IA"

# --- validación de la escena ------------------------------------------------------------------------------------------------------------------
OK = {"tipo": "cta", "oferta": {"palabra": "CLAUDE", "que": "la guía en PDF"}}
assert not val(OK), val(OK)
for malo in ({"palabra": "claude", "que": "la guía"}, {"palabra": "AB", "que": "la guía"}, {"palabra": "DEMASIADOLARGO", "que": "la guía"}, {"palabra": "CLAUDE", "que": "x"},
             {"palabra": "CLAU DE", "que": "la guía"}, {"que": "la guía"}):
    assert val({"tipo": "cta", "oferta": malo}), malo
assert val(dict(OK, compartir="ese amigo")), "no se pueden mezclar oferta y compartir"

# --- vídeo completo: la voz del cierre sale sola -------------------------------------------------------------------------------------------------
base = {"tema": "bolsa", "escenas": [{"tipo": "gancho", "voz": "Once ayudantes de trading dentro de Claude, gratis.", "texto": "11 AYUDANTES DE TRADING", "motivo": "pared_pantallas"},
                                      {"tipo": "metafora", "voz": "Cada uno hace una sola tarea. Al final te dejo la guía gratis.", "motivo": "engranajes"}, dict(OK)]}
sb = validar(base)
voz = sb["escenas"][-1]["voz"]
assert voz == "Comenta Claude y sígueme en WhaleXtreet, y te envío la guía en PDF por privado.", voz
assert lineas(sb)["l3"] == voz
sin = validar({**base, "escenas": base["escenas"][:-1] + [{"tipo": "cta"}]})
assert "Comenta" not in sin["escenas"][-1]["voz"]

# --- la escena se dibuja ----------------------------------------------------------------------------------------------------------------------
h, js = ESCENAS["cta"][0](ctx(), OK)
assert "«CLAUDE»" in h and "COMENTA" in h and "sígueme" in h and "te envío la guía en PDF por privado" in h and "Instagram" in h, h[:300]
assert "Envíaselo" not in h
assert "scale" in "".join(js)
h2, _ = ESCENAS["cta"][0](ctx(), {"tipo": "cta"})
assert "COMENTA" not in h2 and "SÍGUENOS" in h2, "sin oferta, el cierre es el de siempre"

# --- crear(): lo que dice la IA no cambia la oferta del post ---------------------------------------------------------------------------------------
def cliente_falso(sistema, prompt):
    assert ("OFERTA REAL DE ESTE VÍDEO" in prompt) == ("oferta" in prompt and "palabra_clave" in prompt)
    return {"tema": "bolsa", "escenas": [
        {"tipo": "gancho", "angulo": "secreto", "voz": "Once ayudantes de trading dentro de Claude, y gratis.", "texto": "11 AYUDANTES", "resalte": "11", "motivo": "pared_pantallas"},
        {"tipo": "metafora", "voz": "Uno escanea gráficos y otro fija tu stop antes de entrar. Al final te dejo la guía gratis.", "motivo": "engranajes"},
        {"tipo": "metafora", "voz": "Nada se ejecuta sin que tú digas que sí.", "motivo": "escudo"},
        {"tipo": "cta", "oferta": {"palabra": "INVENTADA", "que": "un regalo que no existe"}, "voz": "Comenta INVENTADA y te regalo un coche."}]}


sb = storyboard_ia.crear(POST, cliente_falso)
cta = sb["escenas"][-1]
assert cta["oferta"] == {"palabra": "CLAUDE", "que": "la guía en PDF"} and "voz" in cta and "INVENTADA" not in str(cta) and "coche" not in str(cta), cta
sb2 = storyboard_ia.crear(SIN_OFERTA, cliente_falso)
assert "oferta" not in sb2["escenas"][-1] and "coche" not in str(sb2["escenas"][-1]), "sin oferta en el post, ni palabra clave ni promesas"
assert "OFERTA REAL DE ESTE VÍDEO" in storyboard_ia._prompt(POST) and "OFERTA REAL" not in storyboard_ia._prompt(SIN_OFERTA)
assert "OFERTA (cierre" in storyboard_ia.SISTEMA

# --- el cierre «compartir» que propone la IA ya no se pierde (antes el código lo borraba) ------------------------------------------------------------------
def cliente_compartir(sistema, prompt):
    d = cliente_falso(sistema, prompt)
    d["escenas"][-1] = {"tipo": "cta", "compartir": "ese amigo que compra por impulso"}
    return d


sb3 = storyboard_ia.crear(SIN_OFERTA, cliente_compartir)
assert sb3["escenas"][-1]["compartir"] == "ese amigo que compra por impulso" and "síguenos en WhaleXtreet" in sb3["escenas"][-1]["voz"], sb3["escenas"][-1]
# --- con oferta: vídeo corto y aviso temprano (casi nadie llega al cierre de un vídeo largo) ---------------------------------------
def sbv(voces):
    return {"escenas": [{"tipo": "gancho", "voz": v} for v in voces] + [{"tipo": "cta"}]}

bien = sbv(["Perder dinero cuesta caro.", "Al final te dejo la guía totalmente gratis.", "Primero, lo básico."])
assert storyboard_ia.problemas_oferta(bien, POST) == [], "aviso correcto"
sin_aviso = storyboard_ia.problemas_oferta(sbv(["Hola a todos.", "Te cuento algo.", "Y más cosas."]), POST)
assert len(sin_aviso) == 1 and "al final" in sin_aviso[0]
largo = storyboard_ia.problemas_oferta(sbv(["Al final te dejo la guía gratis."] + ["palabra " * 30] * 5), POST)
assert any("máximo" in p for p in largo), "demasiado largo para un vídeo con oferta"
assert storyboard_ia.problemas_oferta(sbv(["Hola."] * 3), SIN_OFERTA) == [], "sin oferta no se exige nada (puede durar 60-70 s)"
print("OK: cierre con oferta («Comenta X y sígueme»)")
