"""Límite 429 de Gemini: backoff exponencial con jitter, respeto de Retry-After/retryDelay y tope diario repartido. Todo simulado: sin red ni claves."""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "caja"))
import cuota
import gemini

os.environ["GEMINI_API_KEY"] = "clave-de-prueba"


class R:
    def __init__(self, status, texto="", cabeceras=None, datos=None):
        self.status_code, self.text, self.headers, self._d = status, texto, cabeceras or {}, datos

    def json(self):
        return self._d

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


OK = R(200, datos={"candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}]})


def cliente(respuestas):
    llamadas = []
    it = iter(respuestas)

    def post(url, **kw):
        llamadas.append(url)
        return next(it)
    return post, llamadas


def cuota_tmp(**kw):
    return cuota.CuotaDiaria(archivo=Path(tempfile.mkdtemp()) / "c.json", **kw)


# 1. parseo de Retry-After (segundos, fecha HTTP) y del retryDelay de Gemini
assert cuota.parsear_retry_after({"Retry-After": "7"}) == 7
assert cuota.parsear_retry_after({"retry-after": "2.5"}) == 2.5
from datetime import datetime, timezone
ref = datetime(2026, 11, 17, 10, 0, 0, tzinfo=timezone.utc)
assert cuota.parsear_retry_after({"Retry-After": "Tue, 17 Nov 2026 10:00:30 GMT"}, ahora=ref) == 30
assert cuota.parsear_retry_after({}, '{"error":{"details":[{"retryDelay":"34s"}]}}') == 34
assert cuota.parsear_retry_after({}, "Please retry in 12.5s.") == 12.5
assert cuota.parsear_retry_after({}, "sin pista") is None

# 2. backoff exponencial con jitter: crece, está acotado y el jitter varía
techos = [cuota.BASE_S * 2 ** n for n in range(8)]
for n, t in enumerate(techos):
    t = min(t, cuota.TOPE_ESPERA_S)
    bajo, alto = cuota.espera_backoff(n, azar=lambda: 0.0), cuota.espera_backoff(n, azar=lambda: 0.999999)
    assert abs(bajo - t / 2) < 1e-9 and t / 2 <= alto <= t, (n, bajo, alto)
assert cuota.espera_backoff(0, azar=lambda: 0.0) < cuota.espera_backoff(3, azar=lambda: 0.0)
assert cuota.espera_backoff(20, azar=lambda: 0.999) <= cuota.TOPE_ESPERA_S          # nunca pasa del tope
assert len({round(cuota.espera_backoff(3), 6) for _ in range(20)}) > 1                # con azar real, las esperas difieren
# con Retry-After se espera al menos eso (y no más de 1 s extra de jitter)
assert 9 <= cuota.espera_backoff(0, retry_after=9, azar=lambda: 0.0) < 10 and cuota.espera_backoff(5, retry_after=9, azar=lambda: 0.99) < 10

# 3. 429, 429, 200 con Retry-After: duerme lo pedido y acaba bien
post, llamadas = cliente([R(429, cabeceras={"Retry-After": "3"}), R(429, cabeceras={"Retry-After": "5"}), OK])
dormidas = []
res = gemini.generar_json("s", "p", cuota=cuota_tmp(), dormir=dormidas.append, azar=lambda: 0.0, post=post)
assert res == {"ok": True} and len(llamadas) == 3, (res, llamadas)
assert dormidas == [3.0], dormidas                       # lo que pidió el servidor (jitter 0); la 2.ª saturación cambia de modelo sin esperar
assert llamadas[1].split("/models/")[1] != llamadas[2].split("/models/")[1]
post, llamadas = cliente([R(429, cabeceras={"Retry-After": "3"}), R(200, datos=OK._d)])
dormidas = []
gemini.generar_json("s", "p", cuota=cuota_tmp(), dormir=dormidas.append, azar=lambda: 0.0, post=post)
assert dormidas == [3.0]

# 4. 429 sin Retry-After: esperas exponenciales crecientes (jitter fijado en el mínimo)
post, llamadas = cliente([R(429), R(429), R(429), OK])
dormidas = []
gemini.generar_json("s", "p", cuota=cuota_tmp(), dormir=dormidas.append, azar=lambda: 0.0, post=post)
assert len(dormidas) >= 2 and all(b >= a for a, b in zip(dormidas, dormidas[1:])) and dormidas[-1] > dormidas[0], dormidas
assert all(d <= cuota.TOPE_ESPERA_S for d in dormidas)

# 5. un 429 con retryDelay enorme (cuota diaria de Google) no se espera: se aborta con CuotaAgotada
post, llamadas = cliente([R(429, texto='{"retryDelay":"3600s"}')])
dormidas = []
try:
    gemini.generar_json("s", "p", cuota=cuota_tmp(), dormir=dormidas.append, post=post)
    raise AssertionError("debía abortar")
except cuota.CuotaAgotada:
    pass
assert dormidas == [] and len(llamadas) == 1

# 6. 429 permanente: se rinde dentro del tiempo máximo (no se pasa 8 minutos reintentando) y sin dormir de verdad
post, llamadas = cliente([R(429)] * 60)
dormidas = []
try:
    gemini.generar_json("s", "p", cuota=cuota_tmp(), dormir=dormidas.append, azar=lambda: 0.5, post=post)
    raise AssertionError("debía rendirse")
except RuntimeError as e:
    assert "429" in str(e), e
assert sum(dormidas) <= 300, sum(dormidas)

# 7. tope diario y reparto: videos=40 %, borradores=60 % de 10 peticiones
c = cuota_tmp(tope=10, reparto={"videos": 40, "borradores": 60})
assert c.limite_de("videos") == 4 and c.limite_de("borradores") == 6 and c.limite_de("otro") == 0   # sin reparto para «otro»: nada
for _ in range(4):
    c.registrar("videos")
try:
    c.registrar("videos")
    raise AssertionError("debía agotarse")
except cuota.CuotaAgotada:
    pass
assert c.registrar("borradores") == 1 and c.usadas("videos") == 4 and c.restantes("videos") == 0 and c.restantes("borradores") == 5

# 8. con el tope agotado no se llama a la red
c = cuota_tmp(tope=2, reparto={"videos": 100})
post, llamadas = cliente([R(429), R(429), OK])
try:
    gemini.generar_json("s", "p", cuota=c, dormir=lambda s: None, azar=lambda: 0.0, post=post)
    raise AssertionError("debía agotar el tope")
except cuota.CuotaAgotada:
    pass
assert len(llamadas) == 2, llamadas                       # la tercera petición ni se intentó

# 9. el contador se reinicia al cambiar de día y sin tope (0) no limita
dia = ["2026-11-17"]
c = cuota.CuotaDiaria(archivo=Path(tempfile.mkdtemp()) / "c.json", tope=1, reparto={}, hoy=lambda: dia[0])
c.registrar("videos")
dia[0] = "2026-11-18"
assert c.usadas("videos") == 0 and c.registrar("videos") == 1
libre = cuota_tmp(tope=0)
for _ in range(50):
    libre.registrar("videos")
assert libre.restantes("videos") is None

# 10. un 5xx también reintenta con backoff y el modelo de reserva entra tras 2 saturaciones
post, llamadas = cliente([R(503), R(503), OK])
gemini.generar_json("s", "p", cuota=cuota_tmp(), dormir=lambda s: None, azar=lambda: 0.0, post=post)
assert llamadas[0].split("/models/")[1] != llamadas[2].split("/models/")[1], llamadas
print("OK: límite 429 de Gemini (backoff con jitter, Retry-After, tope diario repartido)")
