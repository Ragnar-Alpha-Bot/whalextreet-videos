"""Envío a Telegram del vídeo terminado (o de un aviso si algo falla). Claves solo por variables de entorno; nunca se imprimen.
Con DRY_RUN=1 no envía nada y lo cuenta por pantalla."""
import os
from pathlib import Path

import requests

LIMITE_BOT = 50 * 1024 * 1024


def _dry():
    return os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")


def _cred():
    tok, chat = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip(), (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not tok or not chat:
        raise RuntimeError("Faltan los secretos TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID.")
    return tok, chat


def aviso(texto):
    if _dry():
        print(f"[SIMULACIÓN Telegram] aviso: {texto}")
        return
    tok, chat = _cred()
    r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", json={"chat_id": chat, "text": texto[:4000]}, timeout=30)
    r.raise_for_status()


def enviar_video(ruta, pie):
    ruta = Path(ruta)
    if ruta.stat().st_size > LIMITE_BOT:
        raise RuntimeError(f"el vídeo pesa {ruta.stat().st_size / 1e6:.0f} MB y Telegram admite 50 MB a los bots")
    if _dry():
        print(f"[SIMULACIÓN Telegram] vídeo {ruta.name} ({ruta.stat().st_size / 1e6:.1f} MB): {pie}")
        return None
    tok, chat = _cred()
    with open(ruta, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{tok}/sendVideo",
                          data={"chat_id": chat, "caption": pie[:1000], "supports_streaming": "true", "width": 1080, "height": 1920},
                          files={"video": ("video.mp4", f, "video/mp4")}, timeout=180)
    r.raise_for_status()
    return r.json()["result"]["message_id"]
