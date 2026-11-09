"""De un post aprobado a un guion de escenas (storyboard) con Gemini, con validación y reparación.

    from storyboard_ia import crear
    sb = crear({"id": "abc", "format": "leccion", "parts": ["texto del post"], "chart": {...}})

Si Gemini devuelve un guion no válido (formato, frases prohibidas, cifras inventadas…), se le devuelven los errores para que lo corrija
(hasta 3 intentos). Si no lo logra, lanza StoryboardError: es mejor avisar «no pude hacer el vídeo» que publicar uno malo.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fidelidad  # noqa: E402
from guion import validar  # noqa: E402
from paletas import TEMAS  # noqa: E402


class StoryboardError(Exception):
    pass


SISTEMA = """Eres el director de vídeos cortos verticales (TikTok, Instagram Reels, YouTube Shorts) de WhaleXtreet, una marca de educación financiera \
en español de España. Conviertes un post YA APROBADO en un guion de escenas en JSON. Responde SOLO con el objeto JSON.

REGLAS DE LA MARCA (innegociables)
- Datos reales siempre: usa solo cifras que aparezcan en el post o en sus «datos». No inventes estadísticas, precios ni resultados.
  Si necesitas un gráfico o un ejemplo sin datos reales, marca esa escena con "ilustrativo": true y pon «(ilustrativo)» en su título o etiqueta
  (solo grafico, barras, donut y numero pueden ser ilustrativos).
- Habla de «probabilidad estimada», nunca de «seguro» ni de ganancias garantizadas. Prohibido: garantizado, sin riesgo, hazte rico, dinero fácil.
- Tono educativo, cercano y claro. Nada de consejos de inversión personalizados.

ESTRUCTURA
- Entre 5 y 8 escenas. La PRIMERA es siempre un «gancho»; la ÚLTIMA siempre {"tipo": "cta"}. En medio, las que encajen con el contenido.
- Objetivo: 30-45 segundos hablados en total (90-130 palabras entre todas las «voz»).
- Cada escena lleva «voz»: lo que se locuta, en español de España natural y hablado. Sin emojis, hashtags ni URLs. Escribe en letra los números
  pequeños y las siglas difíciles de leer en voz alta (en pantalla sí van en cifras). Máx. 300 caracteres por «voz».
- GANCHO: frena el scroll en el primer segundo y es honesto con el contenido (nada de promesas falsas). Fórmulas: pregunta que incomoda,
  error común, dato llamativo del post, contraste, aviso. {"tipo":"gancho","voz":"frase corta hablada (máx. 110 caracteres)","texto":"TEXTO GRANDE (máx. 42 caracteres)",
  "resalte":"una palabra del texto","icono":"alerta|subida|bajada|pregunta|ninguno"}

ESCENAS DISPONIBLES (todas con "voz"; «cuando» = una palabra de la voz en la que aparece ese elemento)
- titulo: {"titulo":"máx. 48","subtitulo":"máx. 70, opcional","etiqueta":"máx. 24, opcional"}
- numero: {"valor":número,"decimales":0-3,"prefijo":"","sufijo":"%","etiqueta":"máx. 44","detalle":"máx. 50, opcional","delta":número opcional,"cuando":"palabra"}
- grafico: {"titulo":"máx. 44","puntos":[2 a 40 números],"etiquetas":["inicio","fin"],"unidad":"","anotaciones":[{"i":posición,"texto":"máx. 28","cuando":"palabra"}]}
- barras: {"titulo":"máx. 44","unidad":"","destacar":posición,"items":[{"n":"máx. 24","v":número,"cuando":"palabra"}] (2 a 6)}
- donut: {"titulo":"máx. 44","segmentos":[{"n":"máx. 22","v":número>0,"cuando":"palabra"}] (2 a 5)}
- lista: {"titulo":"máx. 44","items":[{"t":"máx. 36","cuando":"palabra"}] (2 a 5)}
- tarjetas: {"titulo":"máx. 44","items":[{"etiqueta":"máx. 30","valor":"texto de máx. 12","nota":"máx. 44","tono":"acc|up|down|warn","cuando":"palabra"}] (2 a 4)}
- pregunta: {"pregunta":"máx. 70","opciones":["máx. 26 cada una"] (2 a 3),"pie":"opcional"}
Elige las escenas por lo que mejor explique ESTE post; no repitas siempre la misma estructura.

SALIDA
{"tema":"cripto|bolsa|alerta|macro|educativo","etiqueta":"máx. 24, p. ej. BOLSA · ACCIONES","escenas":[ ... ]}
El «tema» fija el color: cripto, bolsa (acciones), alerta (riesgos y errores), macro (economía), educativo (conceptos).
"""


def _prompt(post, errores=None, anterior=None):
    p = {"formato_del_post": post.get("format"), "plataformas": post.get("platforms"), "texto_del_post": post.get("parts")}
    if post.get("chart"):
        p["datos_reales"] = post["chart"]
    txt = "POST APROBADO:\n" + json.dumps(p, ensure_ascii=False, indent=1)
    if errores:
        txt += ("\n\nTU RESPUESTA ANTERIOR NO ERA VÁLIDA:\n" + json.dumps(anterior, ensure_ascii=False)[:6000]
                + "\n\nERRORES A CORREGIR:\n - " + "\n - ".join(errores) + "\n\nDevuelve el JSON completo corregido.")
    return txt


def crear(post, cliente=None, intentos=3):
    """Devuelve un storyboard validado. cliente(sistema, prompt) -> dict (por defecto, Gemini)."""
    if cliente is None:
        from gemini import generar_json
        cliente = generar_json
    fuente = "\n".join(post.get("parts") or [])
    if not fuente.strip():
        raise StoryboardError("el post no tiene texto")
    errores, anterior = None, None
    for n in range(1, intentos + 1):
        try:
            crudo = cliente(SISTEMA, _prompt(post, errores, anterior))
        except Exception as e:  # noqa: BLE001
            raise StoryboardError(f"Gemini no respondió: {e.__class__.__name__}") from e
        if not isinstance(crudo, dict):
            errores, anterior = ["la respuesta debe ser un objeto JSON"], crudo
            continue
        sb = copy.deepcopy(crudo)
        sb["tipo_post"] = post.get("format") or "datos"
        sb.setdefault("tema", "educativo")
        if sb["tema"] not in TEMAS:
            sb["tema"] = "educativo"
        esc = sb.get("escenas")
        if isinstance(esc, list) and esc and isinstance(esc[-1], dict) and esc[-1].get("tipo") != "cta":
            esc.append({"tipo": "cta"})            # el cierre es obligatorio y siempre igual: lo pone el código
        elif isinstance(esc, list) and esc and isinstance(esc[-1], dict):
            esc[-1] = {"tipo": "cta"}              # el cta lo decide la marca, no la IA
        try:
            sb = validar(sb)
            problemas = fidelidad.comprobar(sb, fuente, post.get("chart"))
        except ValueError as e:
            problemas = [l.strip(" -") for l in str(e).splitlines()[1:]] or [str(e)]
        if not problemas:
            sb["ilustrativo"] = any(e.get("ilustrativo") for e in sb["escenas"])
            return sb
        errores, anterior = problemas, crudo
    raise StoryboardError("Gemini no logró un guion válido: " + "; ".join(errores[:4]))
