"""Diagnóstico: modelos de Gemini disponibles y cuánto tarda cada uno en un encargo grande (como el de los borradores). Nunca imprime la clave."""
import json
import os
import time

import requests

CLAVE = (os.environ.get("GEMINI_API_KEY") or "").strip()
if not CLAVE:
    raise SystemExit("Falta GEMINI_API_KEY")
H = {"x-goog-api-key": CLAVE}

r = requests.get("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200", headers=H, timeout=30)
print("Lista de modelos: HTTP", r.status_code)
disponibles = []
if r.ok:
    for m in r.json().get("models", []):
        nombre = m["name"].split("/")[-1]
        if "generateContent" in m.get("supportedGenerationMethods", []) and "gemini" in nombre:
            disponibles.append(nombre)
    print("Modelos Gemini con generateContent:", ", ".join(sorted(disponibles)))
else:
    print(r.text[:300])

pedidos = [x.strip() for x in os.environ.get("MODELOS", "").split(",") if x.strip()]
candidatos = pedidos or ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.5-pro", "gemini-3.6-pro", "gemini-3.8-pro"]
candidatos = [c for c in candidatos if c in disponibles or pedidos] or disponibles[:6]

PROMPT = ("Escribe 5 hilos de 3 o 4 posts cada uno (máx. 270 caracteres por post) sobre inversión para principiantes: comparaciones A vs B, "
          "con un ejemplo hipotético marcado y una pregunta final de dos opciones. Responde SOLO con JSON: "
          '{"posts": [{"slot": 1, "parts": ["post 1", "post 2", "post 3"]}]}')
print("\nPrueba con un encargo grande (5 hilos):")
for modelo in candidatos:
    t0 = time.time()
    try:
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent", headers=H, timeout=170,
                          json={"contents": [{"role": "user", "parts": [{"text": PROMPT}]}], "generationConfig": {"temperature": 0.8, "responseMimeType": "application/json"}})
        seg = time.time() - t0
        info = f"HTTP {r.status_code} en {seg:.0f} s"
        if r.ok:
            try:
                partes = r.json()["candidates"][0]["content"]["parts"]
                texto = "".join(p.get("text", "") for p in partes if not p.get("thought"))
                hilos = json.loads(texto)["posts"]
                info += f" · {len(hilos)} hilos · {sum(len(h['parts']) for h in hilos)} posts · máx. {max(len(p) for h in hilos for p in h['parts'])} caracteres por post"
            except Exception as e:  # noqa: BLE001
                info += f" · respuesta no válida ({e.__class__.__name__})"
        else:
            info += " · " + r.text[:160].replace("\n", " ")
    except requests.RequestException as e:
        info = f"sin respuesta tras {time.time() - t0:.0f} s ({e.__class__.__name__})"
    print(f"  {modelo:28s} {info}", flush=True)
