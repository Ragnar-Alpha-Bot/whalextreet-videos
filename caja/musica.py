"""Fondo musical propio, generado por código (sin bancos de música ni licencias de terceros).

Un colchón de acordes suave y lento, con una tonalidad distinta por tema, que va muy por debajo de la voz. Da continuidad entre las pausas
y hace que el vídeo suene «producido» en lugar de una voz suelta. Su volumen se calcula respecto al de la voz (nivel_db), no a ojo.
"""
import numpy as np
import soundfile as sf

SR = 44100

# Notas (Hz) de cada acorde; la primera es la fundamental
ACORDES = {
    "cripto":    [146.83, 220.00, 329.63, 493.88],   # Re sus2 add9: abierto, tecnológico
    "bolsa":     [130.81, 196.00, 293.66, 329.63],   # Do add9: luminoso, optimista
    "alerta":    [110.00, 164.81, 261.63, 392.00],   # La menor 7: tenso, serio
    "macro":     [174.61, 261.63, 329.63, 440.00],   # Fa mayor 7: amplio, sereno
    "educativo": [196.00, 293.66, 329.63, 493.88],   # Sol 6: cálido, claro
}


def _filtro_paso_bajo(x, corte, sr=SR):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / sr)
    X *= 1 / (1 + (f / corte) ** 4)
    return np.fft.irfft(X, len(x))


def generar(ruta, duracion, tema, rms_voz, nivel_db=-24.0):
    """Escribe un wav mono de `duracion` s. Su nivel medio queda `nivel_db` dB por debajo de rms_voz (el volumen medio de la voz)."""
    if tema not in ACORDES:
        raise ValueError(f"tema desconocido: {tema!r}")
    n = int(SR * duracion)
    t = np.arange(n) / SR
    rng = np.random.default_rng(sum(map(ord, tema)))   # determinista por tema: el mismo tema suena igual en cada vídeo
    y = np.zeros(n)
    for i, f0 in enumerate(ACORDES[tema]):
        for desafino in (-3.0, 0.0, 3.0):                      # tres copias ligeramente desafinadas: «coro» suave
            f = f0 * 2 ** (desafino / 1200)
            fase = rng.uniform(0, 2 * np.pi)
            lfo = 0.6 + 0.4 * np.sin(2 * np.pi * (0.06 + 0.035 * i) * t + rng.uniform(0, 2 * np.pi))   # respiración lenta
            y += lfo * (np.sin(2 * np.pi * f * t + fase) + 0.35 * np.sin(2 * np.pi * 2 * f * t + fase) + 0.12 * np.sin(2 * np.pi * 3 * f * t + fase))
    y += 0.9 * np.sin(2 * np.pi * ACORDES[tema][0] / 2 * t)      # fundamental una octava más grave
    y = _filtro_paso_bajo(y, 1400.0)
    ataque, cola = int(SR * 1.5), int(SR * 2.2)
    env = np.ones(n)
    env[:ataque] = np.linspace(0, 1, ataque) ** 2
    env[-cola:] = np.linspace(1, 0, cola) ** 2
    y *= env
    objetivo = rms_voz * 10 ** (nivel_db / 20)
    y *= objetivo / float(np.sqrt(np.mean(y ** 2)))
    sf.write(ruta, y.astype(np.float32), SR, subtype="PCM_16")
    return round(float(np.sqrt(np.mean(y ** 2))), 5)
