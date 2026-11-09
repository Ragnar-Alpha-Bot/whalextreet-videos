"""Pruebas del camino «post aprobado → guion de escenas → vídeo» con un Gemini simulado (sin red, sin claves).
Ejecutar desde la raíz del repo:  python tests/test_post.py"""
import copy
import io
import json
import os
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
sys.path.insert(0, str(RAIZ))
os.environ["DRY_RUN"] = "1"
for k in ("GEMINI_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
    os.environ.pop(k, None)

import desde_post  # noqa: E402
import fidelidad  # noqa: E402
import storyboard_ia as S  # noqa: E402
import telegram_envio  # noqa: E402

fallos = []


def comprobar(nombre, cond):
    print(("OK   " if cond else "FALLA"), nombre)
    if not cond:
        fallos.append(nombre)


POST = {"id": "abc123", "format": "error_principiante", "platforms": ["x", "threads"],
        "parts": ["Comprar solo porque un precio sube rápido es una trampa clásica. Antes de entrar, define tu plan, tu stop y cuánto estás dispuesto a perder."]}
POST_DATOS = {"id": "d1", "format": "datos", "platforms": ["x"], "parts": ["El Ibex 35 cerró hoy en 11.250 puntos, un 1,2 % más que ayer."],
              "chart": {"title": "Ibex 35", "series": [11116, 11180, 11250]}}


def sb_valido(**cambios):
    sb = {"tema": "alerta", "etiqueta": "ALERTA · IMPULSO", "escenas": [
        {"tipo": "gancho", "voz": "¿Compraste solo porque subía?", "texto": "¿Compraste porque subía?", "resalte": "subía"},
        {"tipo": "lista", "voz": "Define tu plan, tu stop y cuánto estás dispuesto a perder.", "titulo": "ANTES DE COMPRAR",
         "items": [{"t": "Tu plan", "cuando": "plan"}, {"t": "Tu stop", "cuando": "stop"}, {"t": "Tu riesgo", "cuando": "perder"}]},
        {"tipo": "pregunta", "voz": "¿Te ha pasado alguna vez?", "pregunta": "¿Te ha pasado?", "opciones": ["Sí", "No"]},
        {"tipo": "cta"}]}
    sb.update(cambios)
    return sb


class Falso:
    """Gemini simulado: devuelve las respuestas en orden y recuerda los prompts recibidos."""
    def __init__(self, *respuestas):
        self.r, self.prompts = list(respuestas), []

    def __call__(self, sistema, prompt):
        self.prompts.append(prompt)
        x = self.r.pop(0) if len(self.r) > 1 else self.r[0]
        if isinstance(x, Exception):
            raise x
        return copy.deepcopy(x)


def falla(post, cliente, intentos=3):
    try:
        S.crear(post, cliente, intentos)
        return None
    except S.StoryboardError as e:
        return str(e)


# --- 1. Fidelidad de cifras -----------------------------------------------------------------------------------------
comprobar("lee números a la española e inglesa (1.234,5 · 12,4 · 3.2 · 11.250)", fidelidad.numeros("1.234,5 y 12,4 % y 3.2 y 11.250") == {1234.5, 12.4, 3.2, 11250.0})
comprobar("una cifra que está en el post es válida", fidelidad.comprobar(sb_valido(escenas=[{"tipo": "numero", "voz": "x", "valor": 11250}]), POST_DATOS["parts"][0]) == [])
comprobar("una cifra inventada se detecta", len(fidelidad.comprobar({"escenas": [{"tipo": "numero", "voz": "x", "valor": 87}]}, POST["parts"][0])) == 1)
comprobar("los números pequeños (≤ 10, como «3 señales») siempre valen", fidelidad.comprobar({"escenas": [{"tipo": "titulo", "voz": "x", "titulo": "3 señales de alarma"}]}, "nada") == [])
comprobar("las cifras de los datos reales del post valen aunque no estén en su texto", fidelidad.comprobar({"escenas": [{"tipo": "grafico", "voz": "x", "titulo": "Ibex", "puntos": [11116, 11180, 11250]}]}, "sin cifras", POST_DATOS["chart"]) == [])
comprobar("puntos de un gráfico inventados se detectan", len(fidelidad.comprobar({"escenas": [{"tipo": "grafico", "voz": "x", "titulo": "Ibex", "puntos": [11116, 11999]}]}, "sin cifras", POST_DATOS["chart"])) == 1)
comprobar("una escena ilustrativa con «(ilustrativo)» en el título puede llevar cifras propias",
          fidelidad.comprobar({"escenas": [{"tipo": "grafico", "voz": "x", "titulo": "Subida (ilustrativo)", "puntos": [10, 25, 37], "ilustrativo": True}]}, "nada") == [])
comprobar("una escena ilustrativa SIN avisarlo en pantalla se rechaza", len(fidelidad.comprobar({"escenas": [{"tipo": "grafico", "voz": "x", "titulo": "Subida", "puntos": [10, 25, 37], "ilustrativo": True}]}, "nada")) == 1)
comprobar("solo gráfico, barras, donut y número pueden ser ilustrativos", len(fidelidad.comprobar({"escenas": [{"tipo": "lista", "voz": "x", "titulo": "Lista (ilustrativo)", "items": ["a", "b"], "ilustrativo": True}]}, "nada")) == 1)
comprobar("una cifra de un texto de pantalla (tarjeta) también se vigila", len(fidelidad.comprobar({"escenas": [{"tipo": "tarjetas", "voz": "x", "items": [{"etiqueta": "Margen", "valor": "47 %"}]}]}, "nada")) == 1)

# --- 2. Guion de escenas desde un post ------------------------------------------------------------------------------
f = Falso(sb_valido())
sb = S.crear(POST, f)
comprobar("un guion válido de Gemini se acepta y fija el tipo de post de la agencia", sb["tipo_post"] == "error_principiante" and sb["escenas"][0]["tipo"] == "gancho")
comprobar("el prompt lleva el texto del post y las reglas de marca", "trampa clásica" in f.prompts[0] and "datos_reales" not in f.prompts[0])
comprobar("los datos reales del post viajan en el prompt (y solo si los hay)", "datos_reales" in S._prompt(POST_DATOS) and "11116" in S._prompt(POST_DATOS) and "datos_reales" not in S._prompt(POST))
comprobar("el cierre «cta» lo pone el código: si Gemini no lo trae, se añade", S.crear(POST, Falso(sb_valido(escenas=sb_valido()["escenas"][:-1])))["escenas"][-1]["tipo"] == "cta")
m = sb_valido(); m["escenas"][-1] = {"tipo": "cta", "texto": "Compra ya mi curso", "voz": "Compra mi curso"}
comprobar("el cta lo decide la marca, no la IA (ignora texto y voz que invente)", S.crear(POST, Falso(m))["escenas"][-1].get("texto") is None)
comprobar("un tema inventado cae a «educativo»", S.crear(POST, Falso(sb_valido(tema="telepatia")))["tema"] == "educativo")
comprobar("sin escenas ilustrativas la marca no avisa de «gráficos ilustrativos»", S.crear(POST, Falso(sb_valido()))["ilustrativo"] is False)
ilu = sb_valido(); ilu["escenas"].insert(1, {"tipo": "grafico", "voz": "Cuando algo sube rápido.", "titulo": "Subida rápida (ilustrativo)", "puntos": [10, 25, 37], "ilustrativo": True})
comprobar("con una escena ilustrativa el vídeo avisa «gráficos ilustrativos»", S.crear(POST, Falso(ilu))["ilustrativo"] is True)

# --- 3. Reparación y fallos -----------------------------------------------------------------------------------------
sin_gancho = sb_valido(); sin_gancho["escenas"].pop(0)
f = Falso(sin_gancho, sb_valido())
sb = S.crear(POST, f)
comprobar("si el primer guion no es válido se reintenta y el 2º prompt incluye los errores", len(f.prompts) == 2 and "gancho" in f.prompts[1] and "ERRORES A CORREGIR" in f.prompts[1] and sb is not None)
inventado = sb_valido(); inventado["escenas"].insert(1, {"tipo": "numero", "voz": "Casi nadie lo logra.", "valor": 87, "etiqueta": "Éxito"})
f = Falso(inventado, sb_valido())
S.crear(POST, f)
comprobar("una cifra inventada obliga a corregir y el error nombra la cifra", "87" in f.prompts[1])
promesa = sb_valido(); promesa["escenas"][1]["voz"] = "Con este método tus ganancias están garantizadas."
f = Falso(promesa, sb_valido())
S.crear(POST, f)
comprobar("una promesa de ganancias («garantizadas») se rechaza y se corrige", "prohibida" in f.prompts[1])
msg = falla(POST, Falso(sin_gancho))
comprobar("si tras 3 intentos sigue mal: error claro, sin vídeo a medias", msg is not None and "no logró" in msg)
comprobar("si Gemini no responde: error claro", "Gemini no respondió" in (falla(POST, Falso(RuntimeError("caído"))) or ""))
comprobar("una respuesta que no es un objeto JSON se trata como fallo", falla(POST, Falso(["no", "es", "objeto"])) is not None)
comprobar("un post sin texto no llega ni a Gemini", falla({"id": "x", "format": "mito", "parts": []}, Falso(sb_valido())) is not None)
f3 = Falso(sin_gancho)
falla(POST, f3, intentos=2)
comprobar("el número de intentos se respeta", len(f3.prompts) == 2)

# --- 4. De post a proyecto y avisos ---------------------------------------------------------------------------------
comprobar("el nombre del proyecto se limpia (sin rutas ni caracteres raros)", desde_post.nombre_proyecto({"id": "../../etc/x y"}) == "post-etcxy" and desde_post.nombre_proyecto({}) == "post-sin-id")
POST_T = {**POST, "id": "prueba_tests_post"}
carpeta = RAIZ / "proyectos" / desde_post.nombre_proyecto(POST_T)
try:
    proyecto, mp4 = desde_post.main(POST_T, render=False, cliente=Falso(sb_valido()))
    guardado = json.loads((proyecto / "storyboard.json").read_text(encoding="utf-8"))
    comprobar("desde un post se escribe el guion de escenas en su carpeta (sin render)", mp4 is None and guardado["escenas"][0]["tipo"] == "gancho" and guardado["tipo_post"] == "error_principiante")
    buf = io.StringIO()
    with redirect_stdout(buf):
        try:
            desde_post.main({**POST_T, "id": "prueba_tests_post2"}, render=False, cliente=Falso(sin_gancho))
            avisado = False
        except S.StoryboardError:
            avisado = True
    comprobar("si el guion falla se avisa por Telegram («No pude hacer el vídeo») y se termina con error", avisado and "No pude hacer el vídeo" in buf.getvalue())
finally:
    for p in (carpeta, RAIZ / "proyectos" / "post-prueba_tests_post2"):
        shutil.rmtree(p, ignore_errors=True)

# --- 5. Telegram ----------------------------------------------------------------------------------------------------
buf = io.StringIO()
with redirect_stdout(buf):
    telegram_envio.aviso("hola")
comprobar("en simulación el aviso no sale de la máquina", "SIMULACIÓN" in buf.getvalue())
os.environ.pop("DRY_RUN")
try:
    telegram_envio.aviso("hola")
    comprobar("sin secretos de Telegram da un error claro (no llama a nadie)", False)
except RuntimeError as e:
    comprobar("sin secretos de Telegram da un error claro (no llama a nadie)", "TELEGRAM_BOT_TOKEN" in str(e))
os.environ["DRY_RUN"] = "1"
grande = RAIZ / "proyectos" / "_grande.tmp"
try:
    with open(grande, "wb") as fh:
        fh.truncate(telegram_envio.LIMITE_BOT + 1)
    try:
        telegram_envio.enviar_video(grande, "x")
        comprobar("un vídeo de más de 50 MB se rechaza antes de enviarlo", False)
    except RuntimeError:
        comprobar("un vídeo de más de 50 MB se rechaza antes de enviarlo", True)
finally:
    grande.unlink(missing_ok=True)

print("\nTODO CORRECTO" if not fallos else f"\nFALLOS ({len(fallos)}): {fallos}")
sys.exit(1 if fallos else 0)
