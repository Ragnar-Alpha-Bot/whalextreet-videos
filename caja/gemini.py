"""Cliente mínimo de Gemini (capa gratuita) para pedir JSON. Mismo criterio que el de la agencia: varios modelos de reserva y reintentos.
Claves: solo por variables de entorno (GEMINI_API_KEY, GEMINI_MODEL opcional). Nunca se imprimen."""
import json
import os
import random
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cuota import CuotaAgotada, CuotaDiaria, ESPERA_UNICA_MAX_S, espera_backoff, parsear_retry_after  # noqa: E402

DEFAULT_MODEL = "gemini-3.8-flash"
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.6-flash"]


def _extraer_json(texto):
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto.strip(), flags=re.S)
    return json.loads(texto)


def generar_json(sistema, prompt, temperatura=0.8, uso=None, cuota=None, dormir=time.sleep, azar=None, post=None):
    """Pide un JSON a Gemini. Ante 429/5xx espera con backoff exponencial + jitter (o lo que pida «Retry-After»/«retryDelay») y cambia de modelo.
    `uso` = quién consume la cuota diaria («videos» por defecto); `cuota`, `dormir`, `azar` y `post` se pueden inyectar en las pruebas."""
    clave = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not clave:
        raise RuntimeError("Falta el secreto GEMINI_API_KEY.")
    uso = uso or os.environ.get("GEMINI_USO") or "videos"
    cuota = cuota or CuotaDiaria()
    post = post or requests.post
    azar = azar or random.random
    try:
        espera_max = float(os.environ.get("GEMINI_ESPERA_MAX") or 300)
    except ValueError:
        espera_max = 300.0
    modelos = [(os.environ.get("GEMINI_MODEL") or "").strip() or DEFAULT_MODEL] + FALLBACK_MODELS
    cuerpo = {
        "systemInstruction": {"parts": [{"text": sistema}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperatura, "responseMimeType": "application/json", "thinkingConfig": {"thinkingLevel": "low"}},
    }
    ultimo, idx, saturado, esperado, fallos = None, 0, {}, 0.0, 0

    def esperar(retry_after=None):
        nonlocal esperado, fallos
        s = espera_backoff(fallos, retry_after, azar=azar)
        fallos += 1
        if retry_after is not None and retry_after > ESPERA_UNICA_MAX_S:
            raise CuotaAgotada(f"Gemini pide esperar {retry_after:.0f} s (HTTP 429): no se reintenta dentro de esta ejecución")
        if esperado + s > espera_max:
            raise RuntimeError(f"Gemini no respondió bien tras {esperado:.0f} s de espera ({ultimo})")
        esperado += s
        dormir(s)

    for _ in range(10 + 2 * len(modelos)):
        modelo = modelos[idx]
        cuota.registrar(uso)                       # lanza CuotaAgotada si el uso ya gastó su tope diario: no se llama a la red
        try:
            r = post(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
                     headers={"x-goog-api-key": clave}, json=cuerpo, timeout=70)
        except (requests.Timeout, requests.ConnectionError) as e:
            ultimo = e.__class__.__name__
            if idx + 1 < len(modelos):
                idx += 1
            else:
                esperar()
            continue
        if r.status_code == 429 or r.status_code >= 500:
            ultimo = f"HTTP {r.status_code}"
            saturado[modelo] = saturado.get(modelo, 0) + 1
            pedida = parsear_retry_after(getattr(r, "headers", None), getattr(r, "text", "")) if r.status_code == 429 else None
            if saturado[modelo] >= 2 and idx + 1 < len(modelos):
                idx += 1                           # otro modelo tiene su propia cuota: se prueba sin esperar
            else:
                esperar(pedida)
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
            dormir(3)
    raise RuntimeError(f"Gemini no respondió bien tras varios intentos ({ultimo})")
