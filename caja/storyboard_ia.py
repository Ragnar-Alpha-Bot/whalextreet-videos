"""De un post aprobado a un guion de escenas (storyboard) con Gemini, con validación y reparación.

    from storyboard_ia import crear
    sb = crear({"id": "abc", "format": "leccion", "parts": ["texto del post"], "chart": {...}})

Si Gemini devuelve un guion no válido (formato, frases prohibidas, cifras inventadas…), se le devuelven los errores para que lo corrija
(hasta 3 intentos). Si no lo logra, lanza StoryboardError: es mejor avisar «no pude hacer el vídeo» que publicar uno malo.
"""
import copy
import json
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fidelidad  # noqa: E402
from ganchos import BIBLIOTECA  # noqa: E402
from guion import validar  # noqa: E402
from paletas import TEMAS  # noqa: E402


class StoryboardError(Exception):
    pass


SISTEMA = """Eres el director de vídeos cortos verticales (TikTok, Instagram Reels, YouTube Shorts) de WhaleXtreet, una marca de educación financiera \
en español de España. Conviertes un post YA APROBADO en un guion de escenas en JSON. Responde SOLO con el objeto JSON.

REGLAS DE LA MARCA (innegociables)
- Datos reales siempre: usa solo cifras que aparezcan en el post o en sus «datos». No inventes estadísticas, precios ni resultados.
  Si necesitas un gráfico o un ejemplo sin datos reales, marca esa escena con "ilustrativo": true y pon «(ilustrativo)» en su título o etiqueta
  (solo grafico, barras, barras3d, donut y numero pueden ser ilustrativos).
- Habla de «probabilidad estimada»; nunca prometas ganancias ni resultados asegurados, ni presentes la inversión como algo exento de pérdidas.
- Tono educativo, cercano y claro. Nada de consejos de inversión personalizados.

ESTRUCTURA
- Entre 5 y 8 escenas. La PRIMERA es siempre un «gancho»; la ÚLTIMA siempre {"tipo": "cta"}. En medio, las que encajen con el contenido.
- Objetivo: 30-45 segundos hablados en total (90-130 palabras entre todas las «voz»).
- Cada escena lleva «voz»: lo que se locuta, en español de España natural y hablado. Sin emojis, hashtags ni URLs. Escribe en letra los números
  pequeños y las siglas difíciles de leer en voz alta (en pantalla sí van en cifras). Máx. 300 caracteres por «voz».
- GANCHO (pauta de la marca, OBLIGATORIO y BRUTAL: tiene que hacer PARAR el vídeo en 2 segundos; si no lo consigue, reescríbelo): lo más importante del vídeo. Eres un copywriter experto en contenido viral de finanzas, bolsa, trading y cripto. Los 2 primeros segundos
  deben romper el patrón de scroll: generar curiosidad extrema, tocar un dolor financiero o lanzar un dato contraintuitivo, con MUCHA información visual e intensidad,
  pero siempre con fundamento. CLICKBAIT CON FUNDAMENTO (clave para crecer): pon en juego dinero o una decisión concreta (lo que el espectador puede perder, ganar, ahorrar o evitar). Si el post trae
  datos reales, abre con el dato más fuerte, con su cifra; si no, apóyate en consecuencias reales y comprobables (comisiones, perder un 50 % exige ganar un 100 %, interés compuesto, vender en pánico).
  Puede ser provocador y llamativo. ÚNICO LÍMITE: que sea verdad y el vídeo lo cumpla; nada de porcentajes de gente («el 90 %…») ni cifras que no estén en el post, ni promesas de ganancias.
  REGLAS: la «voz» del gancho tiene MÁXIMO 15 palabras (ideal 10-15); PROHIBIDO empezar con «Hola», «¿Sabías que…?», «En este vídeo te enseño…», «Hoy vamos a hablar de…»
  ni con preguntas retóricas obvias. Usa UNO de estos 5 ángulos (campo «angulo»): «error» (una equivocación costosa que mucha gente comete sin saberlo),
  «verdad» (una verdad incómoda opuesta al sentido común), «secreto» (una ventaja o dato que la mayoría desconoce), «urgencia» (un escenario extremo de pérdida,
  ganancia o cambio inminente) o «pregunta» (una pregunta incisiva que confronta al espectador sobre sus finanzas; nunca obvia).
  TRANSICIÓN: la voz de la escena 2 retoma de inmediato el hueco que abrió el gancho, sin saludos ni introducciones; cada escena deja una razón para seguir viendo hasta el cta.
  Usa SIEMPRE kicker + subtexto y elige un gráfico llamativo:
  {"tipo":"gancho","angulo":"error|verdad|secreto|urgencia|pregunta","voz":"frase corta hablada (máx. 15 palabras y 110 caracteres)","texto":"TEXTO ENORME (máx. 42 caracteres)","resalte":"una palabra del texto",
  "kicker":"etiqueta corta sobre el texto, máx. 22, p. ej. ERROR COMÚN, ALERTA, NADIE LO MIRA","subtexto":"frase de apoyo, máx. 70, que da más contexto o promete la explicación",
  "icono":"alerta|subida|bajada|pregunta|ninguno","grafico":"pulso|caida|subida|cifra|ninguno"}
  Gráficos: «pulso» (anillos que laten, genérico), «caida» / «subida» (línea que se dibuja, solo para ilustrar una dirección, sin cifras),
  «cifra» (número gigante que cuenta, SOLO si el post da esa cifra): añade "cifra":{"valor":número,"decimales":0-2,"prefijo":"","sufijo":"%"}.

ESCENAS DISPONIBLES (todas con "voz"; «cuando» = una palabra de la voz en la que aparece ese elemento)
- titulo: {"titulo":"máx. 48","subtitulo":"máx. 70, opcional","etiqueta":"máx. 24, opcional"}
- numero: {"valor":número,"decimales":0-3,"prefijo":"","sufijo":"%","etiqueta":"máx. 44","detalle":"máx. 50, opcional","delta":número opcional,"cuando":"palabra"}
- grafico: {"titulo":"máx. 44","puntos":[2 a 40 números],"etiquetas":["inicio","fin"],"unidad":"","anotaciones":[{"i":posición,"texto":"máx. 28","cuando":"palabra"}]}
- barras: {"titulo":"máx. 44","unidad":"","destacar":posición,"items":[{"n":"máx. 24","v":número,"cuando":"palabra"}] (2 a 6)}
- barras3d: igual que «barras» pero en 3D (cámara que gira, barras con volumen). Úsala para el gráfico principal de comparación cuando haya 2 a 4 cifras; en el mismo vídeo no mezcles barras y barras3d.
- moneda3d: {"titulo":"máx. 44","simbolo":"máx. 4: $, € o BTC/ETH","subtitulo":"máx. 60, opcional"} moneda dorada en 3D que gira (solo si el post trata de dinero concreto, ahorro o cripto).
- donut3d: igual que «donut» pero en 3D (tarta con volumen que gira); mismas reglas de cifras.
- esfera3d: {"titulo":"máx. 44","subtitulo":"máx. 60, opcional","etiquetas":["máx. 18 cada una"] (0 a 4)} globo con anillos y satélites; sirve para ideas globales: mercados mundiales, macroeconomía, diversificación. Sin cifras.
- velas3d: {"titulo":"máx. 44 y DEBE incluir «(ilustrativo)»","tendencia":"alcista|bajista|lateral"} velas japonesas 3D que se levantan una a una; es una ilustración de un concepto (tendencia, volatilidad), nunca datos reales.
- donut:{"titulo":"máx. 44","segmentos":[{"n":"máx. 22","v":número>0,"cuando":"palabra"}] (2 a 5)}
- lista: {"titulo":"máx. 44","items":[{"t":"máx. 36","cuando":"palabra"}] (2 a 5)}
- tarjetas: {"titulo":"máx. 44","items":[{"etiqueta":"máx. 30","valor":"texto de máx. 12","nota":"máx. 44","tono":"acc|up|down|warn","cuando":"palabra"}] (2 a 4)}
- pregunta: {"pregunta":"máx. 70","opciones":["máx. 26 cada una"] (2 a 3),"pie":"opcional"}
Elige las escenas por lo que mejor explique ESTE post; no repitas siempre la misma estructura.
"""
SISTEMA += BIBLIOTECA + """

SALIDA
{"tema":"cripto|bolsa|alerta|macro|educativo","etiqueta":"máx. 24, p. ej. BOLSA · ACCIONES","escenas":[ ... ]}
El «tema» fija el color: cripto, bolsa (acciones), alerta (riesgos y errores), macro (economía), educativo (conceptos).
"""


FIGURAS_3D = ["barras3d", "donut3d", "esfera3d", "velas3d", "moneda3d"]


def sugerencia_3d(post):
    """Reparte las figuras 3D entre vídeos (según el texto del post, siempre igual para el mismo post) para que no se repita siempre la misma:
    uno de cada tres vídeos sale sin 3D y el resto recibe una figura distinta que Gemini solo cambia si no encaja con el contenido."""
    n = zlib.crc32("\n".join(post.get("parts") or []).encode("utf-8"))
    if n % 3 == 0:
        return "ESCENAS 3D: en este vídeo NO uses ninguna escena 3D (usa las 2D normales)."
    fig = FIGURAS_3D[(n // 3) % len(FIGURAS_3D)]
    return (f"ESCENAS 3D: como máximo UNA escena 3D en todo el vídeo. La figura sugerida para este vídeo es «{fig}»; úsala si encaja con el contenido, "
            "y si no encaja, no uses ninguna. No uses moneda3d salvo que sea la sugerida.")


def _prompt(post, errores=None, anterior=None):
    p = {"formato_del_post": post.get("format"), "plataformas": post.get("platforms"), "texto_del_post": post.get("parts")}
    if post.get("chart"):
        p["datos_reales"] = post["chart"]
    txt = "POST APROBADO:\n" + json.dumps(p, ensure_ascii=False, indent=1) + "\n\n" + sugerencia_3d(post)
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
