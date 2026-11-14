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
from escenas_meta import lista_para_gemini, sugeridos  # noqa: E402
from escenas_ui import lista_iconos  # noqa: E402
from escenas_versus import ACCIONES, lista_acciones_para_gemini  # noqa: E402
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
  ENTENDIBLE POR SÍ SOLO (lo que más falla): el gancho se entiende sin ver nada más. Di DE QUÉ HABLA con nombre propio o de algo que se reconozca (una empresa, un ETF, el ahorro, el interés compuesto…) y qué le pasa al espectador; nunca cifras sueltas sin decir de qué son («cien euros, doscientos cuarenta y seis o sesenta» no se entiende). Mejor un caso concreto con una pregunta abierta («Cien euros en AMD hace un año: hoy, doscientos cuarenta y seis. ¿Y en Nike?»). Si usas siglas (ETF), explica en la escena siguiente qué son.
  REGLAS: la «voz» del gancho tiene MÁXIMO 15 palabras (ideal 10-15); PROHIBIDO empezar con «Hola», «¿Sabías que…?», «En este vídeo te enseño…», «Hoy vamos a hablar de…»
  ni con preguntas retóricas obvias. Usa UNO de estos 5 ángulos (campo «angulo»): «error» (una equivocación costosa que mucha gente comete sin saberlo),
  «verdad» (una verdad incómoda opuesta al sentido común), «secreto» (una ventaja o dato que la mayoría desconoce), «urgencia» (un escenario extremo de pérdida,
  ganancia o cambio inminente) o «pregunta» (una pregunta incisiva que confronta al espectador sobre sus finanzas; nunca obvia).
  TRANSICIÓN: la voz de la escena 2 retoma de inmediato el hueco que abrió el gancho, sin saludos ni introducciones; cada escena deja una razón para seguir viendo hasta el cta.
  Usa SIEMPRE kicker + subtexto y elige un gráfico llamativo:
  {"tipo":"gancho","angulo":"error|verdad|secreto|urgencia|pregunta","voz":"frase corta hablada (máx. 15 palabras y 110 caracteres)","texto":"TEXTO ENORME (máx. 42 caracteres)","resalte":"una palabra del texto",
  "kicker":"etiqueta corta sobre el texto, máx. 22, p. ej. ERROR COMÚN, ALERTA, NADIE LO MIRA","subtexto":"frase de apoyo, máx. 70, que da más contexto o promete la explicación",
  "icono":"alerta|subida|bajada|pregunta|ninguno","grafico":"pulso|caida|subida|cifra|ninguno","motivo":"id de la lista de METÁFORAS (muy recomendado)"}
  «motivo» pone una animación grande bajo el kicker que APOYA el gancho de forma literal (p. ej. «grafico_cae» si habla de caídas, «billete_se_va» si habla de perder valor).
  Elígelo siempre que haya uno que encaje: un gancho con imagen retiene mucho más. Con «cifra» gigante manda la cifra y no se usa motivo.
  Gráficos: «pulso» (anillos que laten, genérico), «caida» / «subida» (línea que se dibuja, solo para ilustrar una dirección, sin cifras),
  «cifra» (número gigante que cuenta, SOLO si el post da esa cifra): añade "cifra":{"valor":número,"decimales":0-2,"prefijo":"","sufijo":"%"}.

RADAR (si el POST trae un campo «radar»): es la adaptación de un short que ya ha funcionado en otro idioma. Sigue su FÓRMULA (el tipo de gancho, la idea y la estructura que da el texto del post), pero escríbelo todo de nuevo en español de España, con nuestra voz y con las cifras reales del post. NO traduzcas frases: reescribe. NO uses cifras, nombres ni afirmaciones del vídeo original: solo las del bloque «DATOS REALES». Ni «necesitas», ni «para toda la vida», ni recomendaciones de compra.

RETENCIÓN (pauta de la skill yt-script, para todos los vídeos): el espectador decide en los primeros segundos y vuelve a decidir en cada escena.
- El gancho hace TRES trabajos a la vez: promete algo concreto, abre una pregunta que solo se cierra viendo el vídeo y deja ver que hay recompensa.
- Escena 2: en una frase di qué vas a enseñar y empieza ya. PROHIBIDO presentarte, saludar, «antes de empezar», «en este vídeo», pedir seguir, suscribirse o dar «me gusta».
- Bucle abierto: en la escena 2 o 3 anticipa algo que llega después («y el último punto es el que casi nadie mira») y cúmplelo.
- Una idea por escena; lo que se ve cambia en cada escena (no repitas el mismo tipo dos veces seguidas).
- Antes del cierre, una frase que diga que ya has entregado lo prometido. El cierre pide UNA sola cosa.

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
- animal3d: {"animal":"toro|oso","titulo":"máx. 44","subtitulo":"máx. 60, opcional"} un TORO (mercado alcista, optimismo) u OSO (mercado bajista, caídas) 3D galopando con la cámara girando. SOLO si el post habla de mercado alcista o bajista; sin datos ni cifras.
- lingotes3d: {"titulo":"máx. 44","subtitulo":"máx. 60, opcional"} pila de lingotes de oro que cae lingote a lingote, con monedas. Para ahorro, oro, patrimonio o valor refugio; sin cifras.
- linea3d: igual que «grafico» (titulo, puntos, unidad, etiquetas; sin anotaciones) pero en 3D (cinta brillante con área y cámara que gira). Úsala para la evolución de un dato REAL del post (2 a 40 puntos); misma regla de cifras que «grafico» (si es un ejemplo, "ilustrativo": true y «(ilustrativo)» en el título).
- grafico_pro: {"titulo":"máx. 44","modo":"area|linea|velas","puntos":[2 a 260 números],"velas":[{"o":..,"h":..,"l":..,"c":..}] (2 a 150, solo con modo velas),"etiquetas":["inicio","fin"],"unidad":"","zoom":true|false,"anotaciones":[{"i":posición,"texto":"máx. 28","cuando":"palabra"}] (0 a 3)}
  gráfico profesional (estilo TradingView) con la serie REAL del post que se va dibujando, con zoom y anotaciones. SOLO si el post trae una serie real de datos (datos_reales) con al menos 8 puntos o velas; las cifras visibles (anotaciones, etiquetas) deben estar en el post o en sus datos. Si no hay serie real, usa «grafico».
- escudo3d: {"titulo":"máx. 44","subtitulo":"máx. 60, opcional"} escudo 3D con un visto bueno y anillos que giran. Para proteger el capital, stop loss, gestión del riesgo; sin cifras.
- ciudad3d: {"titulo":"máx. 44","subtitulo":"máx. 60, opcional"} ciudad de rascacielos que crece mientras la cámara avanza por la avenida. Para economía, crecimiento o mercados en general; es una ilustración, sin datos.
- donut:{"titulo":"máx. 44","segmentos":[{"n":"máx. 22","v":número>0,"cuando":"palabra"}] (2 a 5)}
- lista: {"titulo":"máx. 44","items":[{"t":"máx. 36","cuando":"palabra"}] (2 a 5)}
- tarjetas: {"titulo":"máx. 44","items":[{"etiqueta":"máx. 30","valor":"texto de máx. 12","nota":"máx. 44","tono":"acc|up|down|warn","cuando":"palabra"}] (2 a 4)}
- pregunta: {"pregunta":"máx. 70","opciones":["máx. 26 cada una"] (2 a 3),"pie":"opcional"}
- pasos: {"fase":"máx. 30, p. ej. «FASE 1 · TU PLAN»","titulo":"máx. 44, opcional","items":[{"n":"máx. 24, el paso","etiqueta":"máx. 28, opcional, p. ej. «PRIMERO»","icono":"__ICONOS__","cuando":"palabra"}] (2 a 4)}
  recuadros numerados (01, 02…) con marco de neón que entran uno a uno al decir cada paso. Úsala para un plan, un método o una secuencia de pasos (no para cifras).
- checklist: {"titulo":"máx. 44","etiqueta":"máx. 24, opcional, p. ej. «ANTES DE INVERTIR»","items":[{"t":"máx. 40","cuando":"palabra"}] (2 a 6)}
  casillas que se marcan con un tick verde al decir cada punto, con contador y barra de progreso. Úsala para checklists, errores a evitar, requisitos o resumen final.
- metafora: {"motivo":"id de la lista de METÁFORAS","titulo":"máx. 44, opcional","subtitulo":"máx. 60, opcional"} animación a pantalla completa que ilustra de forma LITERAL lo que dice la voz de esa escena. No lleva datos ni cifras.
  Incluye 2 o 3 escenas «metafora» por vídeo (las que mejor ilustren la voz) y NO repitas el mismo motivo en el vídeo (tampoco el del gancho). Es lo que hace el vídeo vistoso y profesional.
Elige las escenas por lo que mejor explique ESTE post; no repitas siempre la misma estructura.

RECURSOS ESPECIALES (opcionales; la MAYORÍA de los vídeos NO los lleva: úsalos solo si el post lo pide de verdad y como máximo 2 recursos distintos en un mismo vídeo; las rondas «versus» de una misma comparación cuentan como un solo recurso)
- ranking: {"titulo":"máx. 44","items":[{"valor":"la cifra EXACTA del post, máx. 8, p. ej. «3,86x» o «+12 %»","t":"máx. 44","sub":"máx. 30, opcional","tono":"acc|up|down|warn","cuando":"palabra"}] (2 a 4, ordenadas de mayor a menor)}
  filas con una cifra grande y su título que entran de borroso a nítido. SOLO si el post compara 2-4 elementos con su cifra real (rendimientos, multiplicadores, posiciones). Si no hay cifras reales, no la uses.
- terminal: {"titulo":"máx. 30, p. ej. «Claude Code»","lineas":[{"t":"máx. 56","tipo":"cmd|ok|nota","cuando":"palabra"}] (2 a 6)}
  ventana de terminal con comandos que se escriben solos. SOLO si el post trae comandos o instrucciones de instalación LITERALES: cada línea «cmd» debe copiarse tal cual del post (si no está, el vídeo se rechaza).
  Las líneas «ok» y «nota» son respuestas cortas de apoyo sin cifras («Listo», «Instalado»). Para temas de finanzas normales NO la uses.
- sello (campo extra de una escena «metafora»): "sello":"máx. 14, p. ej. GRATIS". Sello inclinado que cae como un tampón. SOLO si el post dice que algo es gratis, nuevo o está en oferta real.
- acento: dentro de los títulos de pantalla (campo «titulo» de metafora, pasos, checklist, ranking, lista…) puedes poner UNA palabra entre asteriscos, *así*, para que salga en cursiva serif de color. Máximo una palabra por escena y en pocas escenas del vídeo; no la pongas en el campo «voz».
- "subs":"recuadro" (campo del guion, junto a «tema»): la palabra que se está diciendo va en un recuadro de color en vez de subrayada. Úsalo solo en vídeos de herramientas, trucos o tutoriales; en el resto, no pongas «subs».
- versus: {"ronda":{"n":"1","titulo":"máx. 30, p. ej. ANTES DE ENTRAR"},"novato":{"accion":"__ACCIONES__","texto":"máx. 36","etiqueta":"máx. 28, opcional","chip":"máx. 12, opcional","tono":"acc|up|down|warn"},"pro":{ …igual… },"cuando_pro":"palabra en la que entra el pro"}
  dos paneles apilados con muñecos 2D animados: arriba el NOVATO (fondo gris), abajo el PRO. Úsala SOLO para un post que compara dos maneras de hacer algo (novato contra pro, error contra buena práctica, antes y después):
  una escena «versus» por ronda (2 o 3 rondas en el vídeo). La «voz» cuenta primero lo del novato y luego lo del pro (pon «cuando_pro» en la palabra donde empieza el pro). Acciones de los muñecos (elige la que ilustre cada texto):
__LISTA_ACCIONES__
  El texto de cada panel es una frase corta de conducta, nunca una promesa («Escribe su plan antes», no «Gana siempre»). Una «etiqueta» con cifra solo si la cifra viene del post. En el mismo vídeo no repitas la misma acción más de dos veces.
- movil: {"titulo":"máx. 20, nombre de la app","mensajes":[{"de":"yo|ia","t":"máx. 70","cuando":"palabra"}] (2 a 5),"sello":"máx. 14, opcional, p. ej. SATURADO","cuando_sello":"palabra"}
  pantalla de móvil con una conversación que se escribe sola. SOLO si el post trata de una conversación, pregunta-respuesta o consejo recibido; los mensajes se copian o resumen del post, nunca se inventan respuestas de una IA o de un experto.
- calendario: {"titulo":"máx. 30","etiqueta":"máx. 24, opcional","marcas":[{"dia":0-6,"tipo":"ok|fallo","cuando":"palabra"}] (1 a 7, el día 0 es lunes),"pie":"máx. 40, opcional"}
  semana con casillas que se marcan (✓ cumplido, ✕ fallo). SOLO para constancia, hábito o aportaciones periódicas; sin cifras que no estén en el post.
- panel: {"titulo":"máx. 30","busqueda":"máx. 36, opcional","items":[{"n":"máx. 28","valor":"cifra EXACTA del post, máx. 10, con coma decimal y sin puntos de miles (p. ej. «2,4 M»)","sub":"máx. 20","badge":"máx. 8","tono":"acc|up|down|warn","cuando":"palabra"}] (2 a 4)}
  filas con una cifra grande que cuenta hasta su valor y una mini gráfica. SOLO si el post da 2-4 cifras reales comparables; si no hay cifras reales, no la uses.
- OFERTA (cierre «Comenta X y sígueme»): si el POST trae un campo «oferta», el vídeo es CORTO (máx. 120 palabras de voz, ~45 s) y en las 3 primeras escenas una «voz» avisa de ella con «al final» y «gratis» (p. ej. «Al final te dejo la guía totalmente gratis»): casi nadie llega al cierre de un vídeo largo. TODO el vídeo se construye para llevar a ella: gancho brutal, valor real en las escenas intermedias y, al final, el cierre lo pone el código (no escribas el cta con oferta ni inventes recursos ni palabras clave). Si el POST no trae «oferta», no prometas enviar nada.
- cierre «compartir» (campo extra de la escena cta): {"tipo":"cta","compartir":"ese amigo que …, máx. 40","cuando_respuesta":"palabra"}: maqueta de chat «Envíaselo a ese amigo que…». Úsalo en vídeos de comparación o de error común
  que alguien reconocería en un conocido; la «voz» del cta debe decirlo («Envíaselo a ese amigo que… y síguenos en WhaleXtreet»). En el resto de vídeos, el cta normal.
- captura: NO la uses (necesita una imagen que tú no puedes aportar).
"""
SISTEMA = SISTEMA.replace("__ICONOS__", lista_iconos().replace(", ", "|"))
SISTEMA = SISTEMA.replace("__ACCIONES__", "|".join(ACCIONES)).replace("__LISTA_ACCIONES__", lista_acciones_para_gemini())
SISTEMA += ("\nMETÁFORAS DISPONIBLES (campo «motivo»; elige por lo que dice la voz):\n" + lista_para_gemini() + "\n\n")
SISTEMA += BIBLIOTECA + """

SALIDA
{"tema":"cripto|bolsa|alerta|macro|educativo","etiqueta":"máx. 24, p. ej. BOLSA · ACCIONES","escenas":[ ... ]}
El «tema» fija el color: cripto, bolsa (acciones), alerta (riesgos y errores), macro (economía), educativo (conceptos).
"""


FIGURAS_3D = ["barras3d", "donut3d", "esfera3d", "velas3d", "moneda3d", "animal3d", "lingotes3d", "linea3d", "escudo3d", "ciudad3d"]


def sugerencia_3d(post):
    """Reparte las figuras 3D entre vídeos (según el texto del post, siempre igual para el mismo post) para que no se repita siempre la misma:
    uno de cada tres vídeos sale sin 3D y el resto recibe una figura distinta que Gemini solo cambia si no encaja con el contenido."""
    n = zlib.crc32("\n".join(post.get("parts") or []).encode("utf-8"))
    if n % 3 == 0:
        return "ESCENAS 3D: en este vídeo NO uses ninguna escena 3D (usa las 2D normales)."
    fig = FIGURAS_3D[(n // 3) % len(FIGURAS_3D)]
    return (f"ESCENAS 3D: como máximo UNA escena 3D en todo el vídeo. La figura sugerida para este vídeo es «{fig}»; úsala si encaja con el contenido, "
            "y si no encaja, no uses ninguna. No uses moneda3d, animal3d, lingotes3d, escudo3d ni ciudad3d salvo que sea la sugerida (son figuras decorativas); linea3d solo si el post trae una serie de datos reales.")


ESTRUCTURA_SOLUCION = (
    "ESTRUCTURA GANCHO-PROBLEMA-SOLUCIÓN-PEDIDO (idea de un short de 30 s que funciona; solo la estructura, ningún recurso visual copiado). "
    "ÚSALA SOLO si el recurso ofrecido resuelve un problema concreto que el espectador tiene (no es obligatoria; si no encaja, ignórala y haz el vídeo normal):\n"
    " 1) GANCHO (≈3 s): entendible por sí solo, nombra el problema o la promesa realista.\n"
    " 2) PROBLEMA (≈40 % del vídeo): muestra el error o la dificultad con un caso concreto y datos reales del post, para que el espectador piense «me pasa a mí».\n"
    " 3) SOLUCIÓN (≈40 %): enseña cómo se resuelve, paso a paso y solo con hechos del post; di cuánto aporta el recurso («esto está resumido en…»).\n"
    " 4) PEDIDO: lo pone el código («Comenta X y sígueme…»). Deja la última frase como puente natural a él.\n"
    "Puedes nombrar la fase en voz una vez, de forma natural («el problema es…», «la solución es…»), sin pedir suscripciones antes del cierre."
)


def _prompt(post, errores=None, anterior=None):
    p = {"formato_del_post": post.get("format"), "plataformas": post.get("platforms"), "texto_del_post": post.get("parts")}
    if post.get("chart"):
        p["datos_reales"] = post["chart"]
    if isinstance(post.get("radar"), dict):
        p["radar"] = {k: post["radar"].get(k) for k in ("tipo_gancho", "adaptar")}   # solo la fórmula: nada de cifras ni frases del original
    oferta = post.get("oferta") if isinstance(post.get("oferta"), dict) and post["oferta"].get("keyword") else None
    if oferta:
        p["oferta"] = {"palabra_clave": str(oferta["keyword"]).upper(), "recurso": oferta.get("name")}
    txt = ("POST APROBADO:\n" + json.dumps(p, ensure_ascii=False, indent=1) + "\n\n" + sugerencia_3d(post)
           + (f"\n\nOFERTA REAL DE ESTE VÍDEO: al final se ofrece «{oferta.get('name')}» a quien comente «{str(oferta['keyword']).upper()}» y siga la cuenta. "
              "Construye el vídeo para llegar a ella: gancho BRUTAL, valor real y concreto en las escenas intermedias (lo que da ese recurso, solo con los hechos del post) "
              "y deja el hueco para el cierre. El cierre («Comenta X y sígueme…») lo pone el código; no lo escribas ni inventes otros recursos.\n" + ESTRUCTURA_SOLUCION
              if oferta else "")
           + "\n\nMETÁFORAS SUGERIDAS PARA ESTE VÍDEO (úsalas si encajan con la voz; si otras encajan mejor, elige otras de la lista): "
           + ", ".join(sugeridos("\n".join(post.get("parts") or []))))
    if errores:
        txt += ("\n\nTU RESPUESTA ANTERIOR NO ERA VÁLIDA:\n" + json.dumps(anterior, ensure_ascii=False)[:6000]
                + "\n\nERRORES A CORREGIR:\n - " + "\n - ".join(errores) + "\n\nDevuelve el JSON completo corregido.")
    return txt


def resumen_oferta(nombre):
    """«la guía en PDF para instalar las 11 skills…» -> «la guía en PDF» (lo que se dice y se ve en el cierre; máx. 40 caracteres)."""
    corto = " ".join(str(nombre).split()).split(" para ")[0].strip()
    if len(corto) > 40:
        corto = corto[:40].rsplit(" ", 1)[0]
    return corto


def cierre(post, de_la_ia):
    """El cta final. Con oferta REAL en el post: «Comenta X y sígueme y te envío Y por privado» (palabra y recurso salen del post, nunca de la IA).
    Sin oferta: la IA solo puede proponer «compartir» («Envíaselo a ese amigo que…»); el texto de la voz lo pone el código. Si no, el cierre de siempre."""
    oferta = post.get("oferta") if isinstance(post.get("oferta"), dict) else None
    if oferta and oferta.get("keyword") and oferta.get("name"):
        corto = oferta.get("short") if isinstance(oferta.get("short"), str) and 3 <= len(oferta["short"].strip()) <= 40 else None
        return {"tipo": "cta", "oferta": {"palabra": str(oferta["keyword"]).upper(), "que": corto.strip() if corto else resumen_oferta(oferta["name"])}}
    c = de_la_ia.get("compartir") if isinstance(de_la_ia, dict) else None
    if isinstance(c, str) and c.strip():
        c = " ".join(c.split())[:40].rstrip(" ,.")
        return {"tipo": "cta", "compartir": c, "voz": f"Envíaselo a {c}, y síguenos en WhaleXtreet."}
    return {"tipo": "cta"}


INTROS_PROHIBIDOS = ("hola", "bienvenid", "en este vídeo", "en este video", "antes de empezar", "hoy vamos", "suscríbete", "suscribete", "dale a like", "no olvides")


def problemas_retencion(sb):
    """Retención (yt-script): la escena 2 y siguientes no abren con saludo, presentación ni petición de suscripción."""
    out = []
    for i, e in enumerate(sb.get("escenas", [])[1:-1], start=2):
        voz = str(e.get("voz") or "").lower().lstrip(" ¡¿«\"'")
        if voz.startswith(INTROS_PROHIBIDOS):
            out.append(f"la escena {i} empieza con un saludo o una introducción («{voz[:25]}…»): empieza directamente con lo que enseñas")
    return out


MAX_PALABRAS_OFERTA = 125   # ~45 s hablados: casi nadie llega al final de un vídeo largo, y ahí está el «Comenta X»


def problemas_oferta(sb, post):
    """Con oferta, el vídeo es corto y avisa pronto de ella (si no, casi nadie llega al cierre). Lista de problemas (vacía si está bien)."""
    oferta = post.get("oferta") if isinstance(post.get("oferta"), dict) and post["oferta"].get("keyword") else None
    if not oferta:
        return []
    voces = [str(e.get("voz") or "") for e in sb.get("escenas", [])[:-1]]   # el cierre lo escribe el código
    out = []
    n = sum(len(v.split()) for v in voces)
    if n > MAX_PALABRAS_OFERTA:
        out.append(f"el vídeo con oferta tiene {n} palabras de «voz» antes del cierre: máximo {MAX_PALABRAS_OFERTA} (unos 45 s)")
    avisa = " ".join(voces[:3]).lower()
    if "al final" not in avisa or "gratis" not in avisa:
        out.append("en las 3 primeras escenas, una «voz» debe avisar de la oferta con las palabras «al final» y «gratis» "
                   "(p. ej. «Al final te dejo la guía totalmente gratis»), para que se queden hasta el cierre")
    return out


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
            esc.append(cierre(post, {}))           # el cierre es obligatorio: lo pone el código
        elif isinstance(esc, list) and esc and isinstance(esc[-1], dict):
            esc[-1] = cierre(post, esc[-1])        # el cta lo decide la marca (y la oferta del post), no la IA
        try:
            sb = validar(sb)
            problemas = fidelidad.comprobar(sb, fuente, post.get("chart")) + problemas_oferta(sb, post) + problemas_retencion(sb)
        except ValueError as e:
            problemas = [l.strip(" -") for l in str(e).splitlines()[1:]] or [str(e)]
        if not problemas:
            sb["ilustrativo"] = any(e.get("ilustrativo") for e in sb["escenas"])
            return sb
        errores, anterior = problemas, crudo
    raise StoryboardError("Gemini no logró un guion válido: " + "; ".join(errores[:4]))
