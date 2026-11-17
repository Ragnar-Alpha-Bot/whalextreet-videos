"""Límite de uso de Gemini (HTTP 429): reintentos con backoff exponencial y jitter, respeto de «Retry-After» y tope diario repartido.

Sin red y sin claves: solo cálculo de esperas y un contador diario en un archivo JSON local. Lo usa `gemini.py`.

Variables de entorno (todas opcionales):
  GEMINI_TOPE_DIARIO    máximo de peticiones a Gemini por día (UTC). Sin definir o 0 = sin tope propio (solo manda el 429 de Google).
  GEMINI_REPARTO        reparto del tope entre usos, p. ej. «videos=40,borradores=60» (porcentajes; lo que no se nombre comparte el resto).
  GEMINI_USO            quién consume en este proceso (por defecto «videos»).
  GEMINI_CUOTA_ARCHIVO  dónde se guarda el contador (por defecto .cuota/gemini.json, ignorado por git).
  GEMINI_ESPERA_MAX     segundos máximos de espera acumulada por petición antes de rendirse (por defecto 300).

Aviso honesto: en GitHub Actions cada ejecución parte de cero, así que el tope diario solo se arrastra entre ejecuciones si el archivo se
conserva (por ejemplo con actions/cache). Sin eso, el tope vale por ejecución. Ver docs de la PR.
"""
import json
import os
import random
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

BASE_S = 2.0          # primera espera sin Retry-After
TOPE_ESPERA_S = 60.0  # una sola espera calculada nunca pasa de aquí (la pedida por Google sí puede ser mayor, hasta ESPERA_UNICA_MAX_S)
ESPERA_UNICA_MAX_S = 120.0   # si Google pide más que esto, no merece la pena esperar dentro de una ejecución


class CuotaAgotada(RuntimeError):
    """Se acabó el tope diario propio o Google pide una espera demasiado larga: no seguir pidiendo."""


def parsear_retry_after(cabeceras=None, cuerpo=None, ahora=None):
    """Segundos que pide el servidor, o None. Mira la cabecera «Retry-After» (segundos o fecha HTTP) y, si no está, el «retryDelay» de Gemini
    (p. ej. «34s» o «34.5s» en el JSON de error, o «Please retry in 34.5s» en el mensaje)."""
    cab = {str(k).lower(): v for k, v in (cabeceras or {}).items()}
    v = cab.get("retry-after")
    if v is not None:
        v = str(v).strip()
        if re.fullmatch(r"\d+(\.\d+)?", v):
            return float(v)
        try:
            f = parsedate_to_datetime(v)
            ref = ahora or datetime.now(timezone.utc)
            return max(0.0, (f - ref).total_seconds())
        except (TypeError, ValueError):
            pass
    if cuerpo:
        m = re.search(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"', cuerpo) or re.search(r"retry in (\d+(?:\.\d+)?)\s*s", cuerpo, re.I)
        if m:
            return float(m.group(1))
    return None


def espera_backoff(intento, retry_after=None, base=BASE_S, tope=TOPE_ESPERA_S, azar=random.random):
    """Segundos a esperar antes del reintento número `intento` (0 = el primero).
    - Con `retry_after`: se respeta como mínimo (más hasta 1 s de jitter para que varios procesos no vuelvan a chocar a la vez).
    - Sin él: exponencial con jitter «equal»: mitad fija + mitad aleatoria de min(tope, base·2^intento)."""
    if retry_after is not None:
        return float(retry_after) + azar() * 1.0
    techo = min(tope, base * (2 ** intento))
    return techo / 2 + azar() * techo / 2


def _reparto(texto):
    out = {}
    for trozo in (texto or "").split(","):
        if "=" in trozo:
            k, v = trozo.split("=", 1)
            try:
                out[k.strip()] = max(0.0, float(v))
            except ValueError:
                pass
    return out


class CuotaDiaria:
    """Contador de peticiones por día y por uso. `tope` = total diario (0/None = sin tope propio); `reparto` = {uso: porcentaje}."""

    def __init__(self, archivo=None, tope=None, reparto=None, hoy=None):
        self.archivo = Path(archivo or os.environ.get("GEMINI_CUOTA_ARCHIVO") or Path(__file__).resolve().parent.parent / ".cuota" / "gemini.json")
        if tope is None:
            try:
                tope = int(os.environ.get("GEMINI_TOPE_DIARIO") or 0)
            except ValueError:
                tope = 0
        self.tope = int(tope or 0)
        self.reparto = reparto if reparto is not None else _reparto(os.environ.get("GEMINI_REPARTO"))
        self._hoy = hoy or (lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    def _leer(self):
        try:
            d = json.loads(self.archivo.read_text(encoding="utf-8"))
            if d.get("dia") == self._hoy():
                return d
        except (OSError, ValueError):
            pass
        return {"dia": self._hoy(), "usos": {}}

    def limite_de(self, uso):
        """Peticiones diarias permitidas a este uso (None = sin tope)."""
        if not self.tope:
            return None
        if uso in self.reparto:
            return int(self.tope * self.reparto[uso] / 100)
        resto = max(0.0, 100.0 - sum(self.reparto.values()))
        return int(self.tope * resto / 100) if self.reparto else self.tope

    def usadas(self, uso):
        return int(self._leer()["usos"].get(uso, 0))

    def restantes(self, uso):
        lim = self.limite_de(uso)
        return None if lim is None else max(0, lim - self.usadas(uso))

    def registrar(self, uso):
        """Anota una petición. Lanza CuotaAgotada (sin anotar) si el uso ya llegó a su tope diario."""
        lim = self.limite_de(uso)
        d = self._leer()
        n = int(d["usos"].get(uso, 0))
        if lim is not None and n >= lim:
            raise CuotaAgotada(f"tope diario de Gemini agotado para «{uso}» ({n}/{lim} peticiones hoy)")
        d["usos"][uso] = n + 1
        try:
            self.archivo.parent.mkdir(parents=True, exist_ok=True)
            self.archivo.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass    # sin disco no se bloquea el vídeo: solo se pierde el recuento
        return n + 1
