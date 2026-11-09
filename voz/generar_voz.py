"""Genera la locución de un proyecto con la voz D clonada (Qwen3-TTS, licencia Apache 2.0).
Lee <proyecto>/guion.json ({"l1": "texto", ...}) y escribe <proyecto>/assets/voz/lN.wav + duraciones.json.
Las frases ya generadas antes (mismo texto y misma voz) salen de voz_cache/ sin recalcular; el modelo solo se carga si hace falta.
Uso:  python voz/generar_voz.py proyectos/bolsa-per"""
import json
import shutil
import sys
import time
from pathlib import Path

import soundfile as sf

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import vozcache  # noqa: E402

proyecto = Path(sys.argv[1]).resolve()
lineas = json.loads((proyecto / "guion.json").read_text(encoding="utf-8"))
salida = proyecto / "assets" / "voz"
salida.mkdir(parents=True, exist_ok=True)
cache = RAIZ / "voz_cache"
cache.mkdir(exist_ok=True)
perfil_ruta = RAIZ / "perfiles" / "voz_D.pt"
pid = vozcache.id_perfil(perfil_ruta)

modelo = prompt = None
duraciones = {}
for k, texto in lineas.items():
    c = vozcache.ruta(cache, vozcache.clave(texto, pid))
    destino = salida / f"{k}.wav"
    if c.exists():
        shutil.copy(c, destino)
        info = sf.info(str(destino))
        duraciones[k] = {"texto": texto, "segundos": round(info.frames / info.samplerate, 2)}
        print(f"[{k}] {duraciones[k]['segundos']} s de audio (de la caché, sin recalcular)", flush=True)
        continue
    if modelo is None:
        import torch
        from qwen_tts import Qwen3TTSModel
        prompt = torch.load(perfil_ruta, weights_only=False)
        t0 = time.time()
        modelo = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.float32)
        print(f"Modelo listo en {time.time() - t0:.0f} s", flush=True)
    t1 = time.time()
    wavs, sr = modelo.generate_voice_clone(text=texto, language="Spanish", voice_clone_prompt=prompt)
    sf.write(destino, wavs[0], sr)
    shutil.copy(destino, c)
    duraciones[k] = {"texto": texto, "segundos": round(len(wavs[0]) / sr, 2)}
    print(f"[{k}] {duraciones[k]['segundos']} s de audio en {time.time() - t1:.0f} s", flush=True)
(salida / "duraciones.json").write_text(json.dumps(duraciones, ensure_ascii=False, indent=1), encoding="utf-8")
print("LISTO", flush=True)
