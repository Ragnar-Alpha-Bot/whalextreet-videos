"""Locución natural: trozos con pausas, volumen igualado, fondo musical propio. Datos sintéticos, sin voz real.
Ejecutar desde la raíz del repo:  python tests/test_voz.py"""
import importlib.util
import random
import re
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
sys.path.insert(0, str(RAIZ))
import frases  # noqa: E402
import musica  # noqa: E402

fallos = []


def comprobar(nombre, cond):
    print(("OK   " if cond else "FALLA"), nombre)
    if not cond:
        fallos.append(nombre)


spec = importlib.util.spec_from_file_location("generar_voz", RAIZ / "voz" / "generar_voz.py")
gv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gv)        # solo define funciones: el modelo no se carga (todo va bajo __main__)

CFG = frases.config_audio()
FRASES = [
    "Cuando un precio sube muy rápido, aparece el miedo a quedarte fuera, y ahí es donde muchos compran demasiado tarde.",
    "¿Y tú, qué miras primero al analizar una acción: el PER, A, o la deuda, B?",
    "Síguenos en WhaleXtreet para más ideas como esta.",
    "Tres señales de que compras por impulso: no tienes un plan, no sabes dónde saldrías si te equivocas, y solo miras el precio.",
    "Hola.", "Sí, claro, vale, bien, ya.", "Sin signos de puntuación todo seguido sin parar nunca jamás", "¿Qué?", "Uno. Dos. Tres. Cuatro cinco seis siete.",
]

# --- 1. Trozos ---------------------------------------------------------------------------------------------------------
comprobar("los trozos, unidos, dan SIEMPRE el texto original (nada se pierde ni se duplica)",
          all(" ".join(t for t, _ in frases.trocear(f, CFG)) == " ".join(f.split()) for f in FRASES))
random.seed(7)
palabras = "el precio sube, baja; mira: dato. ¿qué? vale! y entonces… nada plan stop riesgo compra venta".split()
azar = [" ".join(random.choice(palabras) for _ in range(random.randint(1, 40))) for _ in range(300)]
comprobar("propiedad con 300 textos al azar: unidos = original, sin trozos vacíos", all(
    " ".join(t for t, _ in frases.trocear(x, CFG)) == " ".join(x.split()) and all(t.strip() for t, _ in frases.trocear(x, CFG)) for x in azar if x.strip()))
t1 = frases.trocear(FRASES[0], CFG)
comprobar("la frase larga se parte en 3 ideas con pausa de coma entre ellas y ninguna al final", len(t1) == 3 and [p for _, p in t1] == [CFG["pausas_s"]["coma"], CFG["pausas_s"]["coma"], 0.0])
comprobar("la pausa depende de la puntuación: dos puntos más larga que coma", [p for _, p in frases.trocear(FRASES[3], CFG)] == [CFG["pausas_s"]["medio"], CFG["pausas_s"]["coma"], CFG["pausas_s"]["coma"], 0.0] and CFG["pausas_s"]["coma"] < CFG["pausas_s"]["medio"] < CFG["pausas_s"]["fin"])
comprobar("una frase corta sin puntuación queda en un solo trozo sin pausa", frases.trocear(FRASES[2], CFG) == [(FRASES[2], 0.0)])
comprobar("ningún trozo tiene menos de 4 palabras salvo que la frase entera sea más corta", all(
    len(t.split()) >= CFG["min_palabras_trozo"] for f in FRASES if len(f.split()) >= 4 for t, _ in frases.trocear(f, CFG)))
comprobar("el trozo de la pregunta conserva su principio «¿Y tú,»", frases.trocear(FRASES[1], CFG)[0][0].startswith("¿Y tú,"))
comprobar("la configuración de marca se lee y los ajustes del usuario mandan sobre los de por defecto", CFG["pausas_s"]["fin"] == 0.30 and CFG["velocidad"] == 1.06 and CFG["musica"]["activa"] is True)

# --- 2. Unir trozos ----------------------------------------------------------------------------------------------------
sr = 24000
t = np.arange(sr) / sr
suave = (0.05 * np.sin(2 * np.pi * 180 * t)).astype(np.float32)
fuerte = (0.4 * np.sin(2 * np.pi * 180 * t)).astype(np.float32)
unido = gv.unir([(suave, 0.2), (fuerte, 0.0)], sr, 0.07)
mitad = len(suave) + int(sr * 0.2)
rms = lambda x: float(np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2)))
comprobar("trozos de volumen muy distinto salen al mismo nivel (±10 %)", abs(rms(unido[:len(suave)]) / rms(unido[mitad:]) - 1) < 0.10)
comprobar("la duración es la de los trozos más la pausa y sin pausa final", abs(len(unido) - (len(suave) + len(fuerte) + int(sr * 0.2))) <= 1)
comprobar("las pausas son silencio real", float(np.max(np.abs(unido[len(suave) + 10: len(suave) + int(sr * 0.2) - 10]))) < 1e-4)
comprobar("el audio no satura (pico ≤ 0,97) ni tiene clics en los empalmes", float(np.max(np.abs(unido))) <= 0.97 and abs(unido[len(suave) - 1]) < 0.01 and abs(unido[mitad]) < 0.01)
comprobar("un trozo en silencio no rompe la función", gv.unir([(np.zeros(sr, dtype=np.float32), 0.1)], sr, 0.07) is not None)

# --- 3. Fondo musical --------------------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    r = {}
    for tema in musica.ACORDES:
        ruta = Path(tmp) / f"{tema}.wav"
        musica.generar(str(ruta), 6.0, tema, 0.07, -24.0)
        y, srm = sf.read(ruta)
        r[tema] = y
    y = r["bolsa"]
    comprobar("la música dura lo pedido y no satura", abs(len(y) / srm - 6.0) < 0.01 and float(np.max(np.abs(y))) < 0.5)
    nivel = 20 * np.log10(float(np.sqrt(np.mean(y ** 2))) / 0.07)
    comprobar(f"su nivel queda -24 dB respecto a la voz (medido {nivel:.1f} dB)", abs(nivel + 24) < 1.0)
    comprobar("entra y sale con fundido (sin golpe al empezar ni al acabar)", abs(y[0]) < 1e-3 and abs(y[-1]) < 1e-3)
    comprobar("cada tema suena distinto (tonalidades distintas)", len({round(float(np.argmax(np.abs(np.fft.rfft(v[srm:3 * srm])))), 0) for v in r.values()}) >= 4)
    musica.generar(str(Path(tmp) / "otra.wav"), 6.0, "bolsa", 0.07, -24.0)
    comprobar("determinista: el mismo tema suena igual en cada vídeo", np.array_equal(y, sf.read(Path(tmp) / "otra.wav")[0]))
    try:
        musica.generar(str(Path(tmp) / "x.wav"), 1.0, "rock", 0.07)
        comprobar("tema desconocido da error", False)
    except ValueError:
        comprobar("tema desconocido da error", True)
    musica.generar(str(Path(tmp) / "fuerte.wav"), 3.0, "alerta", 0.2, -24.0)
    comprobar("el nivel sigue a la voz: voz más fuerte = fondo proporcionalmente más fuerte", float(np.sqrt(np.mean(sf.read(Path(tmp) / "fuerte.wav")[0] ** 2))) > float(np.sqrt(np.mean(r["alerta"][: 3 * srm] ** 2))) * 2)

# --- 4. Volumen final estándar -----------------------------------------------------------------------------------------
import shutil as _sh
import subprocess as _sp
import volumen  # noqa: E402
if _sh.which("ffmpeg"):
    with tempfile.TemporaryDirectory() as tmp:
        v = Path(tmp) / "bajo.mp4"
        _sp.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=160x284:d=6:r=30", "-f", "lavfi", "-i", "sine=f=220:d=6",
                 "-af", "volume=-24dB", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(v)], check=True)
        antes0 = volumen.medir(v)["lufs"]
        a, d = volumen.normalizar(v)
        info = _sp.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,codec_type", "-of", "csv=p=0", str(v)], capture_output=True, text=True).stdout
        comprobar(f"un vídeo muy bajo ({antes0:.1f} LUFS) sale a -14 LUFS (±1): medido {d:.1f}", antes0 < -20 and abs(d + 14) < 1.0)
        comprobar("la normalización no recodifica la imagen (sigue h264) y deja el audio en aac", "h264" in info and "aac" in info)
        comprobar("un vídeo que ya está al nivel correcto no se toca", volumen.normalizar(v)[0] == volumen.normalizar(v)[1])
else:
    print("AVISO: no hay ffmpeg; se omiten las pruebas de volumen")

# --- 5. Control de calidad de la voz (fallo real: una frase del rubio salió sin la mitad del texto) -------------------------------------------
from types import SimpleNamespace as NS
import palabras as _pal

FRASE7 = "Donde tu idea deje de tener sentido,"
habla = lambda seg: (0.3 * np.sin(2 * np.pi * 170 * np.arange(int(24000 * seg)) / 24000) * (0.5 + 0.5 * np.sin(2 * np.pi * 3.3 * np.arange(int(24000 * seg)) / 24000))).astype("float32")
comprobar("una frase de 7 palabras dicha en 2,2 s es plausible", frases.plausible(habla(2.2), 24000, FRASE7))
comprobar("la misma frase en 1,0 s (truncada) NO es plausible: se le ha comido palabras", not frases.plausible(habla(1.0), 24000, FRASE7))
comprobar("un audio vacío o casi mudo NO es plausible", not frases.plausible(np.zeros(0, dtype="float32"), 24000, FRASE7) and not frases.plausible(np.zeros(24000 * 3, dtype="float32"), 24000, FRASE7))
comprobar("una frase de una sola palabra no exige más de medio segundo", frases.plausible(habla(0.6), 24000, "Hola."))
intentos = []


def mala_mala_buena():
    intentos.append(1)
    return (habla(0.8), 24000) if len(intentos) < 3 else (habla(2.4), 24000)


a, sr_ = frases.con_reintentos(mala_mala_buena, FRASE7)
comprobar("si el modelo falla dos veces y acierta a la tercera, se queda con la buena (3 intentos)", len(intentos) == 3 and len(a) / sr_ > 2)
intentos.clear()
try:
    frases.con_reintentos(lambda: (intentos.append(1), (habla(0.5), 24000))[1], FRASE7, intentos=3)
    comprobar("si nunca sale bien, error claro (no se publica una frase a medias)", False)
except RuntimeError as e:
    comprobar("si nunca sale bien, error claro (no se publica una frase a medias)", len(intentos) == 3 and "no logra decir" in str(e))
ww = lambda t: [NS(word=x, start=0, end=0) for x in t.split()]
TEXTO = "Donde tu idea deje de tener sentido, no donde te duela menos. Y antes de entrar, decide cuánto estás dispuesto a perder."
comprobar("Whisper oye todo el texto: cobertura 100 %", _pal.cobertura(TEXTO, ww("donde tu idea deje de tener sentido no donde te duela menos y antes de entrar decide cuánto estás dispuesto a perder")) == 1.0)
cob = _pal.cobertura(TEXTO, ww("decide cuánto estás dispuesto a perder"))
comprobar(f"el caso real (solo se oye el final) da cobertura baja ({cob:.0%}) y por debajo del umbral", cob < _pal.COBERTURA_MIN)
comprobar("palabras de más que oye Whisper no restan cobertura, y mayúsculas, tildes y signos no cuentan", _pal.cobertura("Hola, ¿qué tal?", ww("pues HOLA que tal amigo")) == 1.0)
comprobar("un texto vacío no rompe la cobertura", _pal.cobertura("", ww("hola")) == 1.0)

# --- 6. Ritmo: voz más rápida sin cambiar el tono, pausas cortas, ajustes coherentes -------------------------------------------------------
import json as _json
cfg_archivo = _json.loads((RAIZ / "marca" / "audio.json").read_text(encoding="utf-8"))
comprobar("los valores por defecto del código coinciden con marca/audio.json (nadie cambia el ritmo sin querer)",
          all(frases.DEFECTO[k] == cfg_archivo[k] for k in frases.DEFECTO))
comprobar("el ritmo de la marca: voz un 6 % más rápida, pausas de 0,14 / 0,22 / 0,30 s y un hueco de 0,2 s entre escenas",
          CFG["velocidad"] == 1.06 and CFG["pausas_s"] == {"coma": 0.14, "medio": 0.22, "fin": 0.30} and CFG["gap_escenas_s"] == 0.2)
h1 = frases.huella_audio(CFG)
h2 = frases.huella_audio({**CFG, "velocidad": 1.0})
h3 = frases.huella_audio({**CFG, "pausas_s": {**CFG["pausas_s"], "fin": 0.5}})
comprobar("la huella cambia si cambia la velocidad o las pausas (y entonces la voz se rehace)", h1 != h2 and h1 != h3 and h1 == frases.huella_audio(CFG))
import shutil as _sh2
if _sh2.which("ffmpeg"):
    tono = np.sin(2 * np.pi * 180 * np.arange(24000 * 3) / 24000).astype("float32") * 0.3
    rapido = frases.acelerar(tono, 24000, 1.06)
    pico = lambda y: float(np.argmax(np.abs(np.fft.rfft(y[: 24000]))))      # frecuencia dominante en Hz (1 s de ventana)
    comprobar(f"acelerar 1,06 acorta un 6 % ({len(rapido) / 24000:.2f} s de 3,00 s)", abs(len(rapido) / len(tono) - 1 / 1.06) < 0.02)
    comprobar("acelerar NO cambia el tono (180 Hz antes y después)", abs(pico(rapido) - pico(tono)) <= 3)
    comprobar("velocidad 1,0 no toca el audio", np.array_equal(frases.acelerar(tono, 24000, 1.0), tono))
else:
    print("AVISO: no hay ffmpeg; se omiten las pruebas de aceleración")

print("\nTODO CORRECTO" if not fallos else f"\nFALLOS ({len(fallos)}): {fallos}")
sys.exit(1 if fallos else 0)
