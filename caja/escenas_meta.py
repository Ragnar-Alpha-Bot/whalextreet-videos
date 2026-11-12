"""Metáforas visuales: animaciones a pantalla completa que ilustran de forma literal lo que dice la voz (una ciudad de velas que sube, una hucha
que se llena, una caja fuerte que se abre, un toro, un oso, un cohete…). Se dibujan en un <canvas> con marca/motivos.js, solo a partir del tiempo
del vídeo (evento hf-seek de HyperFrames), así cada fotograma sale igual en cualquier ordenador. Nunca llevan cifras ni precios: son decoración
que apoya la frase, no datos.

Dos usos:
  · escena «metafora»: {"tipo": "metafora", "motivo": "hucha", "voz": "...", "titulo": "opcional", "subtitulo": "opcional"}
  · «motivo» dentro del «gancho»: la animación ocupa el sitio del gráfico y apoya visualmente el gancho.
"""
import json
import re
import zlib
from pathlib import Path

from escenas import ESCENAS, _txt, esc, fromTo

RAIZ = Path(__file__).resolve().parent.parent

# id -> (para qué sirve: lo lee Gemini para elegir) ----------------------------------------------------------------------------------
CATALOGO = {
    # mercado y bolsa
    "ciudad_velas": "ciudad de velas japonesas verdes y rojas que crece: mercado de acciones, volatilidad, un día de bolsa",
    "grafico_sube": "línea que sube dibujándose con un punto brillante: subida, ganancias, recuperación, tendencia alcista",
    "grafico_cae": "línea que se desploma en rojo con flecha hacia abajo: caída, corrección, pérdidas, crash",
    "montana_rusa": "vagoneta en una montaña rusa: volatilidad, altibajos, nervios, mercado que sube y baja",
    "toro": "cabeza de toro verde con flecha hacia arriba: mercado alcista, optimismo, subidas",
    "oso": "cara de oso rojo con flecha hacia abajo: mercado bajista, pesimismo, caídas",
    "pared_pantallas": "pared de pantallas de móvil con scroll y un dedo: atención, redes sociales, ruido, viralidad, FOMO",
    "ticker": "cinta de cotizaciones con flechas verdes y rojas: bolsa en directo, precios, panel de acciones",
    "balanza": "balanza que se inclina entre riesgo y recompensa: riesgo vs beneficio, decidir, comparar",
    "semaforo": "semáforo que cambia de rojo a verde: señal de compra o venta, esperar, cuándo actuar",
    "bola_nieve": "bola de nieve que rueda y crece: interés compuesto, efecto bola de nieve, crecer con el tiempo",
    "arbol_monedas": "árbol que crece y da monedas: inversión a largo plazo, paciencia, hacer crecer el dinero",
    "diversificar": "una gran moneda que se reparte en cuatro vasijas: diversificar, no poner todos los huevos en la misma cesta",
    "vela_gigante": "una vela japonesa gigante con mecha y niveles: explicar qué es una vela, soporte y resistencia",
    "flechas_dir": "flechas verdes y rojas que suben y bajan: tendencias, dirección del mercado, sube o baja",
    "pulso_mercado": "latido de electrocardiograma que cambia de color: pulso del mercado, volatilidad, miedo, ritmo",
    "pantalla_trading": "cuatro monitores de trading con gráficos vivos: trading, analizar el mercado, el escritorio del trader",
    "diana": "diana con flecha clavada en el centro: objetivo, take profit, meta financiera, precisión",
    "dominos": "fichas de dominó que caen en cadena: contagio, crisis en cadena, efecto dominó, riesgo sistémico",
    "burbuja": "burbuja que se infla y estalla: burbuja financiera, exceso de optimismo, euforia, sobrevaloración",
    "radar": "radar que detecta puntos: buscar oportunidades, escanear el mercado, vigilar",
    "lupa": "lupa que revisa un gráfico: analizar, leer la letra pequeña, comprobar comisiones, mirar con atención",
    "banco": "edificio de banco con columnas: bancos, banco central, tipos de interés, instituciones, dinero en el banco",
    "globo_mundo": "globo terráqueo de puntos con arcos: mercados globales, macroeconomía, economía mundial, divisas",
    "noticias": "tarjetas de noticias que entran volando: noticias, titulares, informes, resultados de empresas",
    "engranajes": "engranajes que giran: sistema, estrategia, automatizar, cómo funciona por dentro",
    # dinero y finanzas personales
    "hucha": "hucha de cerdito con monedas que caen: ahorro, ahorrar poco a poco, hábito de ahorro",
    "lluvia_monedas": "lluvia de monedas: ingresos, dividendos, ganar dinero, cobrar, abundancia",
    "pilas_monedas": "pilas de monedas que crecen cada vez más altas: ahorro mensual, constancia, acumular",
    "flujo_monedas": "monedas que fluyen por un canal: flujo de dinero, ingresos pasivos, rentas, cobros periódicos",
    "billete_se_va": "billetes que se deshacen y se van volando: inflación, el dinero pierde valor, dinero parado",
    "cubo_agujero": "cubo con un agujero por el que se escapan monedas: comisiones, gastos hormiga, fugas de dinero",
    "caja_fuerte": "caja fuerte que se abre mostrando monedas: seguridad, proteger el dinero, fondo de emergencia",
    "reloj": "reloj que gira con monedas alrededor: tiempo, largo plazo, cuánto tarda, el tiempo es tu aliado",
    "escalera": "escalera de barras con una bola que sube peldaño a peldaño: progreso paso a paso, plan, avanzar",
    "pastel_reparto": "círculo que se reparte en tres trozos: repartir el sueldo, presupuesto, regla 50/30/20, asignar",
    "cuenta_atras": "cuenta atrás 3-2-1 que termina en una moneda: urgencia, plazo, empezar ya, última oportunidad",
    "escudo": "escudo azul con un visto bueno: proteger, seguridad, gestión del riesgo, stop loss, cuidar el capital",
    # riesgo, azar y psicología
    "alarma": "sirena roja giratoria: alerta, peligro, aviso urgente, riesgo alto, estafa",
    "exclamacion": "gran signo de exclamación rojo con ondas: atención, cuidado, error grave, advertencia",
    "interrogante": "gran interrogante brillante con órbitas: duda, misterio, la pregunta que casi nadie se hace",
    "ruleta": "ruleta que gira con una bola: azar, apostar, especular sin plan, suerte",
    "dados": "dos dados que ruedan: suerte, azar, probabilidad, apuesta",
    "multitud_moviles": "multitud de siluetas con móviles encendidos: la masa, efecto manada, todo el mundo compra, FOMO",
    "anzuelo": "anzuelo con una moneda de cebo y peces: trampa, cebo, estafa, promesas fáciles, ganchos",
    "cohete": "cohete que despega entre estrellas: a la luna, pump, subidón, explosión de precio, lanzamiento",
    "onda_audio": "onda de sonido de colores: ruido, opiniones, rumores, voces del mercado",
    # cripto
    "bitcoin": "moneda de Bitcoin girando con ondas: bitcoin, cripto, el rey de las criptomonedas",
    "blockchain": "cadena de bloques que se enlazan uno a uno: blockchain, cómo funciona, transparencia, registro",
    "red_nodos": "red de nodos conectados con impulsos: descentralización, redes, DeFi, ecosistema cripto",
    "matriz": "lluvia de código estilo matriz: tecnología, programación, hackeo, mundo digital, algoritmos",
    "candado": "candado que se abre con interferencias: seguridad cripto, hackeo, claves, custodia, wallet",
    "ballena": "ballena azul nadando: las ballenas (grandes inversores) del cripto y de la bolsa, la marca",
}

SONIDOS = {  # sonido de entrada según la intención (por defecto: card + ding)
    "grafico_cae": ("error", "whoosh"), "oso": ("error", "whoosh"), "alarma": ("boom", "impact"), "exclamacion": ("boom", "impact"),
    "billete_se_va": ("error", "swipe"), "cubo_agujero": ("tick", "swipe"), "dominos": ("tick", "impact"), "burbuja": ("riser:0", "pop:2"),
    "candado": ("glitch", "tick"), "matriz": ("glitch", "swipe"), "cohete": ("riser:0", "whoosh"), "cuenta_atras": ("tick", "tick"),
    "ruleta": ("tick", "swipe"), "dados": ("tick", "pop:1"), "interrogante": ("pop:1", "riser:0"), "anzuelo": ("swipe", "pop:2"),
}

MAX_TITULO, MAX_SUBTITULO = 44, 60


def motivos_js():
    """Ids definidos en marca/motivos.js (la prueba comprueba que coinciden con CATALOGO)."""
    return set(re.findall(r'^def\("([a-z0-9_]+)"', (RAIZ / "marca" / "motivos.js").read_text(encoding="utf-8"), re.M))


def lista_para_gemini():
    return "\n".join(f"  · {k}: {v}" for k, v in CATALOGO.items())


def sugeridos(post_texto, n=6):
    """Motivos sugeridos para un vídeo concreto: el mismo post siempre recibe los mismos, y entre posts se reparten por todo el catálogo
    (así Gemini no usa siempre las mismas cinco metáforas). Gemini puede elegir otras si encajan mejor."""
    ids = sorted(CATALOGO)
    base = zlib.crc32(post_texto.encode("utf-8"))
    orden = sorted(ids, key=lambda k: zlib.crc32(f"{base}-{k}".encode("utf-8")))
    return orden[:n]


MODULO = """
import {dibujar} from "./assets/motivos.js";
await document.fonts.load('700 40px InterW'); await document.fonts.load('700 40px PlexW');
const cv = document.getElementById("%(id)s"), g = cv.getContext("2d");
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim() || "#ffffff";
const K = {acc: css("--acc"), acc2: css("--acc2"), res: css("--resalte"), up: css("--up"), down: css("--down"), warn: css("--warn"), text: css("--text"),
  muted: css("--muted"), bg: css("--bg"), surface: css("--surface"), raised: css("--raised"), border: css("--border")};
const T0 = %(t0)s;
function pintar(t) { dibujar("%(motivo)s", g, cv.width, cv.height, Math.max(t - T0, 0), K, %(opc)s); }
window.addEventListener("hf-seek", e => pintar(e.detail?.time ?? window.__hfThreeTime ?? 0));
pintar(window.__hfThreeTime ?? 0);
"""


def modulo(ident, motivo, t0, opciones=None):
    return '<script type="module">' + MODULO % {"id": ident, "motivo": motivo, "t0": t0, "opc": json.dumps(opciones or {})} + "</script>"


def canvas(ident, w, h):
    return f'<canvas id="{ident}" width="{int(w)}" height="{int(h)}" style="display:block;width:{int(w)}px;height:{int(h)}px"></canvas>'


def v_motivo(d, err, requerido=True):
    m = d.get("motivo")
    if m is None and not requerido:
        return
    if m not in CATALOGO:
        err(f"«motivo» debe ser uno de: {', '.join(sorted(CATALOGO))}")


def v_metafora(d, err):
    v_motivo(d, err)
    _txt(d, "titulo", err, MAX_TITULO, req=False)
    _txt(d, "subtitulo", err, MAX_SUBTITULO, req=False)
    _txt(d, "sello", err, 14, req=False)          # recurso opcional: sello inclinado tipo «GRATIS» (solo si el post lo dice)


def sonido_entrada(c, motivo, t):
    a, b = SONIDOS.get(motivo, ("card", "ding:2"))
    c.snd(t, a, .42)
    c.snd(t + .22, b, .32)
    if motivo == "burbuja":
        c.snd(t + 2.1, "pop:3", .55)


def e_metafora(c, d):
    ident = f"{c.pf}mv"
    tit, sub = d.get("titulo"), d.get("subtitulo")
    alto = c.n(960) - (c.n(110) if tit else 0) - (c.n(90) if sub else 0)
    html = ('<div class="col" style="justify-content:center;align-items:center">'
            + (f'<div class="lab h" id="{c.pf}tit" style="font-size:{c.fs(36)};align-self:flex-start;margin-bottom:{c.px(10)}">{esc(tit)}</div>' if tit else "")
            + canvas(ident, c.W, alto)
            + (f'<div class="h" id="{c.pf}sub" style="font-weight:700;font-size:{c.fs(52)};text-align:center;color:var(--acc2);margin-top:{c.px(8)}">{esc(sub)}</div>' if sub else "")
            + (f'<div class="h" id="{c.pf}sello" style="position:absolute;right:{c.px(6)};top:{c.px(150)};padding:{c.px(6)} {c.px(26)};border:{c.px(8)} double var(--resalte);'
               f'border-radius:{c.px(16)};color:var(--resalte);font-family:PlexW,monospace;font-weight:700;font-size:{c.fs(76)};letter-spacing:.08em;'
               f'text-transform:uppercase;background:rgba(4,7,16,.55);transform:rotate(-9deg)">{esc(d["sello"])}</div>' if d.get("sello") else "")
            + '</div>' + modulo(ident, d["motivo"], c.t0 + .02, {"escala": 1.2 if c.W >= 900 else 1.0}))
    js = []
    if d.get("sello"):                      # el sello cae desde grande, como un golpe de tampón, hacia la mitad de la escena
        ts = c.T(d.get("cuando_sello"), .35)
        js.append(fromTo(f"#{c.pf}sello", {"opacity": 0, "scale": 2.6, "rotation": -22}, {"opacity": .95, "scale": 1, "rotation": -9, "duration": .35, "ease": "back.out(1.7)"}, ts))
        c.snd(ts + .22, "impact", .5)
    if tit:
        js.append(fromTo(f"#{c.pf}tit", {"opacity": 0, "y": -20}, {"opacity": 1, "y": 0, "duration": .4, "ease": "power3.out"}, c.t0 + .15))
    if sub:
        js.append(fromTo(f"#{c.pf}sub", {"opacity": 0, "y": 26}, {"opacity": 1, "y": 0, "duration": .45, "ease": "power3.out"}, c.t0 + .8))
    sonido_entrada(c, d["motivo"], c.t0 + .05)
    return html, js


ESCENAS["metafora"] = (e_metafora, v_metafora)
