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
comprobar("la frase larga se parte en 3 ideas con pausa de coma entre ellas y ninguna al final", len(t1) == 3 and [p for _, p in t1] == [0.2, 0.2, 0.0])
comprobar("la pausa depende de la puntuación: dos puntos 0,3 s, punto 0,42 s, coma 0,2 s", [p for _, p in frases.trocear(FRASES[3], CFG)] == [0.3, 0.2, 0.2, 0.0])
comprobar("una frase corta sin puntuación queda en un solo trozo sin pausa", frases.trocear(FRASES[2], CFG) == [(FRASES[2], 0.0)])
comprobar("ningún trozo tiene menos de 4 palabras salvo que la frase entera sea más corta", all(
    len(t.split()) >= CFG["min_palabras_trozo"] for f in FRASES if len(f.split()) >= 4 for t, _ in frases.trocear(f, CFG)))
comprobar("el trozo de la pregunta conserva su principio «¿Y tú,»", frases.trocear(FRASES[1], CFG)[0][0].startswith("¿Y tú,"))
comprobar("la configuración de marca se lee y los ajustes del usuario mandan sobre los de por defecto", CFG["pausas_s"]["fin"] == 0.42 and CFG["musica"]["activa"] is True)

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

print("\nTODO CORRECTO" if not fallos else f"\nFALLOS ({len(fallos)}): {fallos}")
sys.exit(1 if fallos else 0)
