"""Regresión: Whisper oye «100 euros» y el guion dice «cien euros»; antes eso bajaba la cobertura y abortaba vídeos con voz perfecta."""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "caja"))
import palabras  # noqa: E402


def oyo(txt):
    return [SimpleNamespace(word=w) for w in txt.split()]


c = palabras.cobertura("Cien euros pueden convertirse en setecientos sesenta y uno. Solo con tiempo.", oyo("100 euros pueden convertirse en 761, solo con tiempo."))
assert c >= 0.95, c
c = palabras.cobertura("A los diez años serían unos ciento noventa y siete euros.", oyo("A los 10 años serían unos 197 euros."))
assert c >= 0.95, c
c = palabras.cobertura("ganan un siete por ciento cada año", oyo("ganan un 7 % cada año"))
assert c >= 0.95, c
# una voz que de verdad falla sigue detectándose
c = palabras.cobertura("En mil novecientos setenta y cinco, un ingeniero de Kodak inventó la primera cámara digital.", oyo("En 1975, un ingeniero de CODA que inventó la primera cámara digital."))
assert c >= 0.7, c
c = palabras.cobertura("Es una orden que cierra tu operación sola si el precio cae", oyo("Es una orden"))
assert c < 0.7, c
print("OK: test_cobertura_numeros")
