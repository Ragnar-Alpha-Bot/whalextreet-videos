"""Genera la locución de un proyecto con la voz D clonada (Qwen3-TTS, licencia Apache 2.0), en trozos cortos con pausas.
Lee <proyecto>/guion.json ({"l1": "texto", ...}) y escribe <proyecto>/assets/voz/lN.wav + duraciones.json.
Cada trozo se genera aparte (y se guarda en voz_cache/ para no repetirlo), se iguala de volumen y se une con pausas según la puntuación.
Uso:  python voz/generar_voz.py proyectos/bolsa-per"""
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import frases  # noqa: E402
import vozcache  # noqa: E402

FADE_S = 0.004


def igualar(x, objetivo):
    """Lleva el volumen medio de la parte hablada de un trozo a un nivel común (sin pasar de 0,97 de pico)."""
    activo = x[np.abs(x) > 0.01]
    if len(activo) == 0:
        return x
    g = objetivo / float(np.sqrt(np.mean(activo ** 2)))
    pico = float(np.max(np.abs(x))) * g
    if pico > 0.97:
        g *= 0.97 / pico
    return (x * g).astype(np.float32)


def unir(trozos, sr, objetivo):
    """trozos: [(audio, pausa_despues_s)] -> un solo audio con pausas y pequeños fundidos para que no haya clics."""
    n = max(1, int(sr * FADE_S))
    partes = []
    for audio, pausa in trozos:
        a = igualar(np.asarray(audio, dtype=np.float32), objetivo).copy()
        a[:n] *= np.linspace(0, 1, n)
        a[-n:] *= np.linspace(1, 0, n)
        partes.append(a)
        if pausa > 0:
            partes.append(np.zeros(int(sr * pausa), dtype=np.float32))
    return np.concatenate(partes)


if __name__ == "__main__":
    proyecto = Path(sys.argv[1]).resolve()
    lineas = json.loads((proyecto / "guion.json").read_text(encoding="utf-8"))
    salida = proyecto / "assets" / "voz"
    salida.mkdir(parents=True, exist_ok=True)
    cache = RAIZ / "voz_cache"
    cache.mkdir(exist_ok=True)
    perfil_ruta = RAIZ / "perfiles" / "voz_D.pt"
    pid = vozcache.id_perfil(perfil_ruta)
    cfg = frases.config_audio()
    objetivo = cfg["volumen_objetivo_rms"]

    modelo = prompt = None
    duraciones = {}
    for k, texto in lineas.items():
        trozos = []
        sr = None
        for frase, pausa in frases.trocear(texto, cfg):
            c = vozcache.ruta(cache, vozcache.clave(frase, pid))
            if c.exists():
                audio, sr_c = sf.read(c, dtype="float32")
                print(f"  [{k}] «{frase[:40]}» de la caché", flush=True)
            else:
                if modelo is None:
                    import torch
                    from qwen_tts import Qwen3TTSModel
                    prompt = torch.load(perfil_ruta, weights_only=False)
                    t0 = time.time()
                    modelo = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.float32)
                    print(f"Modelo listo en {time.time() - t0:.0f} s", flush=True)
                t1 = time.time()
                wavs, sr_c = modelo.generate_voice_clone(text=frase, language="Spanish", voice_clone_prompt=prompt)
                audio = np.asarray(wavs[0], dtype=np.float32)
                sf.write(c, audio, sr_c)
                print(f"  [{k}] «{frase[:40]}» {len(audio) / sr_c:.1f} s en {time.time() - t1:.0f} s", flush=True)
            sr = sr or sr_c
            assert sr_c == sr, "las frases deben tener la misma frecuencia de muestreo"
            trozos.append((audio, pausa))
        final = unir(trozos, sr, objetivo)
        sf.write(salida / f"{k}.wav", final, sr)
        duraciones[k] = {"texto": texto, "segundos": round(len(final) / sr, 2)}
        print(f"[{k}] {duraciones[k]['segundos']} s de audio en {len(trozos)} trozos", flush=True)
    (salida / "duraciones.json").write_text(json.dumps(duraciones, ensure_ascii=False, indent=1), encoding="utf-8")
    print("LISTO", flush=True)
