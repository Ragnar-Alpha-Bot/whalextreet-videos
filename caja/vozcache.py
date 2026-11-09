"""Caché de voz: una frase con el mismo texto y la misma voz no se vuelve a generar (el cierre «Síguenos en WhaleXtreet» se repite en todos los vídeos).

La clave depende del texto exacto y del perfil de voz (perfiles/voz_D.pt): si cambia cualquiera de los dos, se genera de nuevo.
"""
import hashlib
from pathlib import Path


def id_perfil(ruta_perfil):
    return hashlib.sha1(Path(ruta_perfil).read_bytes()).hexdigest()[:10]


def clave(texto, perfil_id):
    return hashlib.sha1(f"{perfil_id}|{' '.join(texto.split())}".encode("utf-8")).hexdigest()[:20]


def ruta(cache_dir, k):
    return Path(cache_dir) / f"{k}.wav"
