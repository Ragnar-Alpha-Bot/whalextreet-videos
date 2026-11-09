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
    voces = json.loads((RAIZ / "marca" / "voces.json").read_text(encoding="utf-8"))
    hab_f = proyecto / "hablantes.json"
    hablantes = json.loads(hab_f.read_text(encoding="utf-8")) if hab_f.exists() else {}
    prompts = {}
    cfg = frases.config_audio()
    objetivo = cfg["volumen_objetivo_rms"]

    modelo = None
    duraciones = {}
    for k, texto in lineas.items():
        trozos = []
        sr = None
        quien = hablantes.get(k, "profesor")
        perfil_ruta = RAIZ / "perfiles" / voces[quien]
        pid = vozcache.id_perfil(perfil_ruta)
        for frase, pausa in frases.trocear(texto, cfg):
            c = vozcache.ruta(cache, vozcache.clave(frase, pid))
            audio = None
            if c.exists():
                audio, sr_c = sf.read(c, dtype="float32")
                if frases.plausible(audio, sr_c, frase):
                    print(f"  [{k}] «{frase[:40]}» de la caché", flush=True)
                else:                                  # una frase mala guardada antes no debe reutilizarse
                    print(f"  Aviso: la caché tenía «{frase[:40]}» truncada; se regenera", flush=True)
                    c.unlink()
                    audio = None
            if audio is None:
                if modelo is None:
                    import torch
                    from qwen_tts import Qwen3TTSModel
                    t0 = time.time()
                    modelo = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.float32)
                    print(f"Modelo listo en {time.time() - t0:.0f} s", flush=True)
                if quien not in prompts:
                    prompts[quien] = torch.load(perfil_ruta, weights_only=False)
                t1 = time.time()

                def generar(frase=frase, quien=quien):
                    w, s_ = modelo.generate_voice_clone(text=frase, language="Spanish", voice_clone_prompt=prompts[quien])
                    return np.asarray(w[0], dtype=np.float32), s_

                audio, sr_c = frases.con_reintentos(generar, frase)
                sf.write(c, audio, sr_c)               # solo se guarda en la caché lo que ha pasado el control
                print(f"  [{k}] «{frase[:40]}» {len(audio) / sr_c:.1f} s en {time.time() - t1:.0f} s", flush=True)
            sr = sr or sr_c
            assert sr_c == sr, "las frases deben tener la misma frecuencia de muestreo"
            trozos.append((frases.acelerar(audio, sr_c, cfg["velocidad"]), pausa))
        final = unir(trozos, sr, objetivo)
        sf.write(salida / f"{k}.wav", final, sr)
        duraciones[k] = {"texto": texto, "segundos": round(len(final) / sr, 2), "voz": quien, "huella": frases.huella_audio(cfg)}
        print(f"[{k}] {duraciones[k]['segundos']} s de audio en {len(trozos)} trozos", flush=True)
    (salida / "duraciones.json").write_text(json.dumps(duraciones, ensure_ascii=False, indent=1), encoding="utf-8")
    print("LISTO", flush=True)
