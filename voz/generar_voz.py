"""Genera la locución de una plantilla con la voz D clonada (Qwen3-TTS, licencia Apache 2.0).
Lee <plantilla>/guion.json ({"l1": "texto", ...}) y escribe <plantilla>/assets/voz/lN.wav + duraciones.json.
Uso:  python voz/generar_voz.py plantillas/senales-cripto"""
import json, sys, time
from pathlib import Path
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

RAIZ = Path(__file__).resolve().parent.parent
plantilla = Path(sys.argv[1]).resolve()
lineas = json.loads((plantilla / "guion.json").read_text(encoding="utf-8"))
salida = plantilla / "assets" / "voz"
salida.mkdir(parents=True, exist_ok=True)

prompt = torch.load(RAIZ / "perfiles" / "voz_D.pt", weights_only=False)
t0 = time.time()
modelo = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.float32)
print(f"Modelo listo en {time.time() - t0:.0f} s", flush=True)

duraciones = {}
for k, texto in lineas.items():
    t1 = time.time()
    wavs, sr = modelo.generate_voice_clone(text=texto, language="Spanish", voice_clone_prompt=prompt)
    sf.write(salida / f"{k}.wav", wavs[0], sr)
    duraciones[k] = {"texto": texto, "segundos": round(len(wavs[0]) / sr, 2)}
    print(f"[{k}] {duraciones[k]['segundos']} s de audio en {time.time() - t1:.0f} s", flush=True)
(salida / "duraciones.json").write_text(json.dumps(duraciones, ensure_ascii=False, indent=1), encoding="utf-8")
print("LISTO", flush=True)
