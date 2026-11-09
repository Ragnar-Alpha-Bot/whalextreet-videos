"""Cliente mínimo de Gemini (capa gratuita) para pedir JSON. Mismo criterio que el de la agencia: varios modelos de reserva y reintentos.
Claves: solo por variables de entorno (GEMINI_API_KEY, GEMINI_MODEL opcional). Nunca se imprimen."""
import json
import os
import re
import time

import requests

DEFAULT_MODEL = "gemini-3.8-flash"
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.6-flash"]


def _extraer_json(texto):
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto.strip(), flags=re.S)
    return json.loads(texto)


def generar_json(sistema, prompt, temperatura=0.8):
    clave = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not clave:
        raise RuntimeError("Falta el secreto GEMINI_API_KEY.")
    modelos = [(os.environ.get("GEMINI_MODEL") or "").strip() or DEFAULT_MODEL] + FALLBACK_MODELS
    cuerpo = {
        "systemInstruction": {"parts": [{"text": sistema}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperatura, "responseMimeType": "application/json", "thinkingConfig": {"thinkingLevel": "low"}},
    }
    ultimo, idx, saturado = None, 0, {}
    for _ in range(10 + 2 * len(modelos)):
        modelo = modelos[idx]
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
                              headers={"x-goog-api-key": clave}, json=cuerpo, timeout=70)
        except (requests.Timeout, requests.ConnectionError) as e:
            ultimo = e.__class__.__name__
            if idx + 1 < len(modelos):
                idx += 1
            else:
                time.sleep(5)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            ultimo = f"HTTP {r.status_code}"
            saturado[modelo] = saturado.get(modelo, 0) + 1
            if saturado[modelo] >= 2 and idx + 1 < len(modelos):
                idx += 1
            else:
                time.sleep(min(10 * saturado[modelo], 40))
            continue
        if r.status_code == 400 and "thinking" in r.text.lower() and "thinkingConfig" in cuerpo["generationConfig"]:
            del cuerpo["generationConfig"]["thinkingConfig"]
            continue
        if r.status_code == 404:
            ultimo = f"modelo «{modelo}» no encontrado"
            if idx + 1 >= len(modelos):
                raise RuntimeError("Ningún modelo de Gemini disponible. Define la variable GEMINI_MODEL con uno válido.")
            idx += 1
            continue
        r.raise_for_status()
        try:
            partes = r.json()["candidates"][0]["content"]["parts"]
            return _extraer_json("".join(p.get("text", "") for p in partes if not p.get("thought")))
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            ultimo = f"respuesta no válida: {e}"
            time.sleep(3)
    raise RuntimeError(f"Gemini no respondió bien tras varios intentos ({ultimo})")
