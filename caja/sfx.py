"""Efectos de sonido propios de WhaleXtreet, generados con código (sin bancos de sonidos ni licencias de terceros).

Cada tipo de elemento tiene su sonido, y la mayoría tiene variantes para que no suene siempre igual: "pop:2", "whoosh:1"...
    from sfx import mezclar
    mezclar([(1.2, "whoosh:0", 0.5), (1.4, "card", 0.6)], total=30.0, ruta="sfx_mix.wav")

whoosh  transición entre escenas (3 variantes)     swipe  transición corta
pop     aparece un elemento pequeño (4 variantes)  card   aparece una tarjeta o recuadro
click   pulsación                                   tick   contador, tecla o cambio de subtítulo
ding    acierto o check (3 variantes)               impact golpe de título
error   fallo o caída                               riser  gráfico que se dibuja (subida de tono)
blip    barra o segmento que crece: "blip:0", "blip:1"... sube de nota con el número
"""
from pathlib import Path
import numpy as np
import soundfile as sf

SR = 44100
_rng = np.random.default_rng(7)


def _norm(x, pico=0.9):
    m = np.max(np.abs(x)) or 1.0
    return (x / m * pico).astype(np.float32)


def _lowpass(x, cutoff):
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def _t(dur):
    return np.arange(int(SR * dur)) / SR


def whoosh(dur=0.5, f0=250, f1=6000, inverso=False):
    t = _t(dur)
    ruido = _rng.standard_normal(len(t))
    corte = np.geomspace(f0, f1, len(t))
    y = _lowpass(ruido, corte) - 0.6 * _lowpass(ruido, corte * 0.35)
    forma = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    if inverso:
        forma = forma[::-1] * np.linspace(0.2, 1, len(t))
    return _norm(y * forma)


def swipe():
    return whoosh(0.22, 500, 7000)


def pop(f=1.0):
    t = _t(0.14)
    fr = (260 + 700 * np.exp(-t * 38)) * f
    return _norm(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 30))


def card():
    t = _t(0.16)
    cuerpo = np.sin(2 * np.pi * (170 + 90 * np.exp(-t * 40)) * t) * np.exp(-t * 26)
    roce = _lowpass(_rng.standard_normal(len(t)), np.full(len(t), 3500.0)) * np.exp(-t * 60)
    return _norm(cuerpo + 0.45 * roce)


def click():
    t = _t(0.05)
    return _norm(_rng.standard_normal(len(t)) * np.exp(-t * 320) * 0.6 + np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 180) * 0.5)


def tick():
    t = _t(0.035)
    return _norm(np.sin(2 * np.pi * 2300 * t) * np.exp(-t * 130))


def ding(f=1.0):
    t = _t(0.7)
    y = (np.sin(2 * np.pi * 1318 * f * t) + 0.5 * np.sin(2 * np.pi * 1976 * f * t) + 0.25 * np.sin(2 * np.pi * 2637 * f * t)) * np.exp(-t * 6.5)
    y[:int(SR * 0.004)] *= np.linspace(0, 1, int(SR * 0.004))
    return _norm(y)


def impact():
    t = _t(0.6)
    cuerpo = np.sin(2 * np.pi * np.cumsum(38 + 120 * np.exp(-t * 14)) / SR) * np.exp(-t * 7)
    golpe = _lowpass(_rng.standard_normal(len(t)), np.full(len(t), 1800.0)) * np.exp(-t * 40)
    return _norm(cuerpo + 0.5 * golpe)


def error():
    t = _t(0.28)
    y = np.sign(np.sin(2 * np.pi * 150 * t)) * 0.4 + np.sin(2 * np.pi * 220 * t)
    return _norm(y * np.exp(-t * 9))


def riser(dur=0.9):
    t = _t(dur)
    f = 300 * np.exp(np.log(1500 / 300) * t / dur)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / dur) ** 1.3 * np.exp(-((t / dur) ** 8) * 3)
    return _norm(y + 0.15 * np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * (t / dur))


def blip(i=0):
    t = _t(0.16)
    f = 392 * 2 ** (i / 4.0)
    return _norm((np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t * 18))


def boom():
    """Golpe grave de cine (para el gancho): caída de 60 a 28 Hz con ruido corto al principio."""
    t = _t(1.0)
    cuerpo = np.sin(2 * np.pi * np.cumsum(28 + 70 * np.exp(-t * 9)) / SR) * np.exp(-t * 3.6)
    choque = _lowpass(_rng.standard_normal(len(t)), np.full(len(t), 900.0)) * np.exp(-t * 28)
    return _norm(cuerpo + 0.55 * choque)


def glitch():
    """Ráfaga digital corta (para el efecto glitch del texto): ruido troceado y cuantizado."""
    t = _t(0.28)
    ruido = _rng.standard_normal(len(t))
    paso = (np.floor(t * 38) % 2) * 1.0 + 0.25                       # se corta y reanuda varias veces
    y = np.round(ruido * 4) / 4 * paso * np.exp(-t * 5)
    return _norm(y + 0.4 * np.sign(np.sin(2 * np.pi * 330 * t)) * np.exp(-t * 14))


_WHOOSH = [(0.50, 250, 6000, False), (0.45, 400, 5000, False), (0.55, 200, 7000, True)]
_POP = [1.0, 1.18, 0.88, 1.35]
_DING = [1.0, 1.19, 0.89]
SONIDOS = ["whoosh", "swipe", "pop", "card", "click", "tick", "ding", "impact", "error", "riser", "blip", "boom", "glitch"]
_cache = {}


def _crear(nombre, var):
    if nombre == "whoosh":
        return whoosh(*_WHOOSH[var % 3])
    if nombre == "pop":
        return pop(_POP[var % 4])
    if nombre == "ding":
        return ding(_DING[var % 3])
    if nombre == "blip":
        return blip(var)
    if nombre == "riser":
        return riser(0.7 + 0.2 * (var % 3))
    return {"swipe": swipe, "card": card, "click": click, "tick": tick, "impact": impact, "error": error, "boom": boom, "glitch": glitch}[nombre]()


def sonido(clave):
    """clave: 'pop' o 'pop:2'."""
    nombre, _, v = clave.partition(":")
    if nombre not in SONIDOS:
        raise ValueError(f"sonido desconocido: {clave!r}. Disponibles: {SONIDOS}")
    var = int(v) if v else 0
    if clave not in _cache:
        _cache[clave] = _crear(nombre, var)
    return _cache[clave]


def mezclar(eventos, total, ruta):
    """eventos: lista de (segundo, clave, volumen 0-1). Escribe un wav con todos los efectos colocados. Devuelve (n, pico)."""
    pista = np.zeros(int(SR * (total + 1)), dtype=np.float32)
    n = 0
    for seg, clave, vol in eventos:
        s = sonido(clave)
        i = int(seg * SR)
        if i < 0 or i >= len(pista):
            continue
        fin = min(len(pista), i + len(s))
        pista[i:fin] += s[:fin - i] * vol
        n += 1
    pico = float(np.max(np.abs(pista)))
    if pico > 0.95:
        pista *= 0.95 / pico
    sf.write(ruta, pista[: int(SR * total)], SR, subtype="PCM_16")
    return n, round(float(np.max(np.abs(pista))), 2)


if __name__ == "__main__":
    carpeta = Path(__file__).parent / "muestras"
    carpeta.mkdir(exist_ok=True)
    claves = ["whoosh:0", "whoosh:1", "whoosh:2", "swipe", "pop:0", "pop:1", "pop:2", "pop:3", "card", "click", "tick", "ding:0", "ding:1", "ding:2",
              "impact", "error", "riser:0", "blip:0", "blip:1", "blip:2"]
    for c in claves:
        sf.write(carpeta / (c.replace(":", "_") + ".wav"), sonido(c), SR, subtype="PCM_16")
        print("OK", c, f"{len(sonido(c)) / SR:.2f} s")
