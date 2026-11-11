"""Recursos opcionales de edición: terminal, ranking, captura, sello, acento serif y subtítulos con recuadro (validación, HTML y fidelidad de datos)."""
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import fidelidad  # noqa: E402
import storyboard_ia  # noqa: E402
from escenas import ESCENAS, Ctx, esc  # noqa: E402
from guion import validar  # noqa: E402
from paletas import paleta  # noqa: E402

PALABRAS = [{"t": w, "ini": 0.3 * i, "fin": 0.3 * i + 0.25} for i, w in enumerate("primero el escáner luego noticias después analista y pelosi".split())]


def ctx(i=2, W=984, proyecto=None):
    c = Ctx(i, 4.0, 14.0, 4.1, 13.5, PALABRAS, W, 1010, paleta("bolsa"))
    c.proyecto = proyecto
    return c


def val(tipo, d):
    e = []
    ESCENAS[tipo][1](d, e.append)
    return e


# --- acento serif ---------------------------------------------------------------------------------------------------
assert esc("Claude acaba de *pasarse* YouTube") == 'Claude acaba de <em class="ac">pasarse</em> YouTube'
assert esc("a < b & c") == "a &lt; b &amp; c", "sigue escapando el HTML"
assert "<em" not in esc("2 * 3 = 6"), "un asterisco suelto no es acento"
motor = (RAIZ / "caja" / "motor.py").read_text(encoding="utf-8")
assert "SerifW" in motor and (RAIZ / "marca" / "InstrumentSerif-Italic.ttf").exists() and (RAIZ / "marca" / "InstrumentSerif-OFL.txt").exists(), "fuente y licencia"

# --- terminal -------------------------------------------------------------------------------------------------------
T = {"tipo": "terminal", "titulo": "Claude Code", "voz": "x",
     "lineas": [{"t": "/plugin install ejemplo", "tipo": "cmd", "cuando": "escáner"}, {"t": "Listo", "tipo": "ok"}, "/yt-script una idea"]}
assert not val("terminal", T), val("terminal", T)
assert val("terminal", dict(T, lineas=[{"t": "x" * 60}, "b"])), "línea demasiado larga"
assert val("terminal", dict(T, lineas=[{"t": "Listo", "tipo": "ok"}, {"t": "Hecho", "tipo": "nota"}])), "sin ningún comando no hay terminal"
assert val("terminal", dict(T, lineas=["solo una"])), "mínimo 2 líneas"
assert val("terminal", dict(T, lineas=[{"t": "a", "tipo": "raro"}, "b"])), "tipo desconocido"
h, js = ESCENAS["terminal"][0](ctx(), T)
assert "steps(" in "".join(js) and "width:0ch" in h and "Claude Code" in h, "el comando se escribe letra a letra"
assert "<em" not in ESCENAS["terminal"][0](ctx(), dict(T, lineas=["ls *.txt *", "b"]))[0], "en el terminal los asteriscos no son acento"
h2, _ = ESCENAS["terminal"][0](ctx(W=648), T)
assert "s2_win" in h2

# --- ranking --------------------------------------------------------------------------------------------------------
R = {"tipo": "ranking", "titulo": "LOS 4 MEJORES", "voz": "x",
     "items": [{"valor": "3,86x", "t": "Un vídeo muy bueno", "sub": "su canal", "tono": "up", "cuando": "escáner"}, {"valor": "2,29x", "t": "Otro vídeo"}]}
assert not val("ranking", R), val("ranking", R)
assert val("ranking", dict(R, items=[{"valor": "123456789", "t": "x"}, {"valor": "1", "t": "y"}])), "valor demasiado largo"
assert val("ranking", dict(R, items=[{"valor": "1x"}, {"valor": "2x", "t": "y"}])), "falta el título"
assert val("ranking", dict(R, items=R["items"][:1])), "mínimo 2 filas"
h, js = ESCENAS["ranking"][0](ctx(), R)
assert "blur(18px)" in "".join(js) and "3,86x" in h

# --- captura --------------------------------------------------------------------------------------------------------
C = {"tipo": "captura", "imagen": "repo.png", "resalte": {"x": 10, "y": 20, "w": 40, "h": 10}, "titulo": "EL REPO", "pie": "Código abierto", "voz": "x"}
assert not val("captura", C), val("captura", C)
assert val("captura", dict(C, imagen="../secreto.png")), "solo el nombre del archivo, sin carpetas"
assert val("captura", dict(C, imagen="repo.exe")), "solo imágenes"
assert val("captura", dict(C, resalte={"x": 10, "y": 20, "w": 0, "h": 10})), "recuadro sin tamaño"
with tempfile.TemporaryDirectory() as tmp:
    (Path(tmp) / "assets").mkdir()
    try:
        ESCENAS["captura"][0](ctx(proyecto=tmp), C)
        raise SystemExit("debía avisar de que falta la imagen")
    except ValueError as ex:
        assert "repo.png" in str(ex)
    (Path(tmp) / "assets" / "repo.png").write_bytes(b"x")
    h, js = ESCENAS["captura"][0](ctx(proyecto=tmp), C)
    assert 'src="assets/repo.png"' in h and "rgba(4,7,16,.58)" in h and "scale" in "".join(js)

# --- sello y subtítulos con recuadro --------------------------------------------------------------------------------
assert not val("metafora", {"motivo": "hucha", "sello": "GRATIS"})
assert val("metafora", {"motivo": "hucha", "sello": "x" * 20}), "sello demasiado largo"
h, js = ESCENAS["metafora"][0](ctx(), {"motivo": "hucha", "sello": "GRATIS"})
assert "GRATIS" in h and "rotation" in "".join(js)
assert "sello" not in ESCENAS["metafora"][0](ctx(), {"motivo": "hucha"})[0]
base = {"tema": "bolsa", "escenas": [{"tipo": "gancho", "voz": "Tu dinero parado pierde valor.", "texto": "TU DINERO SE DESHACE"},
                                     {"tipo": "ranking", "voz": "Mira esto.", "items": R["items"]}, {"tipo": "cta"}]}
validar(dict(base, subs="recuadro"))
validar(base)
try:
    validar(dict(base, subs="neón"))
    raise SystemExit("debía rechazar un estilo de subtítulos desconocido")
except ValueError as ex:
    assert "subs" in str(ex)

# --- fidelidad: los datos del ranking y los comandos del terminal no se inventan -----------------------------------
sb = {"tema": "bolsa", "escenas": [{"tipo": "ranking", "voz": "x", "items": [{"valor": "3,86x", "t": "a"}, {"valor": "2,29x", "t": "b"}]}]}
assert not fidelidad.comprobar(sb, "Este vídeo multiplicó 3,86x y el otro 2,29x su media"), "cifras del post: bien"
p = fidelidad.comprobar(sb, "Este vídeo multiplicó 3,86x su media")
assert p and "2.29" in p[0], p                                   # 2,29 es pequeño pero en un ranking es dato: tiene que estar en el post
sb = {"tema": "bolsa", "escenas": [{"tipo": "terminal", "voz": "x", "lineas": ["/plugin install ejemplo", {"t": "Listo", "tipo": "ok"}]}]}
assert not fidelidad.comprobar(sb, "Escribe: /plugin  install ejemplo y listo")
p = fidelidad.comprobar(sb, "Instala la herramienta con el comando de su web")
assert p and "no aparece literalmente" in p[0], p
sb = {"tema": "bolsa", "escenas": [{"tipo": "metafora", "voz": "x", "motivo": "hucha", "sello": "OFERTA 50 %"}]}
assert fidelidad.comprobar(sb, "texto sin cifras"), "una cifra en el sello también se comprueba"

# --- la IA sabe cuándo usarlos --------------------------------------------------------------------------------------
for palabra in ("RECURSOS ESPECIALES", "ranking:", "terminal:", "sello", "acento", '"subs":"recuadro"', "NO la uses"):
    assert palabra in storyboard_ia.SISTEMA, palabra
assert "la MAYORÍA de los vídeos NO" in storyboard_ia.SISTEMA, "debe quedar claro que son recursos de uso puntual"
print("OK: recursos opcionales (terminal, ranking, captura, sello, acento serif, subtítulos con recuadro)")
