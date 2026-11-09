"""Tiempos exactos de cada palabra de la locución (Whisper, MIT) alineados con el texto del guion.

Uso (con el Python de qwen3tts):  python palabras.py hyperframes/novato-vs-pro
Lee <proyecto>/assets/voz/duraciones.json y los .wav; escribe <proyecto>/assets/voz/palabras.json:
    {"l1": [{"t": "Novato", "ini": 0.12, "fin": 0.55}, ...], ...}   (segundos desde el inicio de cada audio)
El texto que se muestra es siempre el del guion; Whisper solo aporta los tiempos.
"""
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s)


def alinear(texto, ww, dur):
    """Asigna tiempo a cada palabra del guion usando las palabras que oyó Whisper (las que no casan se interpolan)."""
    toks = texto.split()
    ns = [norm(t) for t in toks]
    nw = [norm(w.word) for w in ww]
    ini = [None] * len(toks)
    fin = [None] * len(toks)
    for bloque in difflib.SequenceMatcher(None, ns, nw, autojunk=False).get_matching_blocks():
        for d in range(bloque.size):
            ini[bloque.a + d] = ww[bloque.b + d].start
            fin[bloque.a + d] = ww[bloque.b + d].end
    # huecos: reparto proporcional a la longitud entre las palabras conocidas más cercanas
    i = 0
    while i < len(toks):
        if ini[i] is not None:
            i += 1
            continue
        j = i
        while j < len(toks) and ini[j] is None:
            j += 1
        a = fin[i - 1] if i > 0 else 0.0
        b = ini[j] if j < len(toks) else dur
        pesos = [max(1, len(ns[x])) for x in range(i, j)]
        tot = sum(pesos)
        t = a
        for x, p in zip(range(i, j), pesos):
            d = (b - a) * p / tot
            ini[x], fin[x] = t, t + d
            t += d
        i = j
    out, prev = [], None
    for t, a, b in zip(toks, ini, fin):
        a = max(a, 0.0 if prev is None else prev + 0.04)      # cada palabra empieza después de la anterior
        a = min(a, max(dur - 0.05, 0.0))
        b = max(b, a + 0.05)
        out.append({"t": t, "ini": round(a, 3), "fin": round(min(b, dur), 3)})
        prev = a
    return out


COBERTURA_MIN = 0.7   # fracción del texto del guion que Whisper debe reconocer en la voz


def cobertura(texto, ww):
    """Qué fracción de las palabras del guion aparece (en orden) en lo que Whisper oyó. 1.0 = la voz dice todo el texto."""
    ns = [norm(t) for t in texto.split()]
    nw = [norm(w.word) for w in ww]
    if not ns:
        return 1.0
    return sum(b.size for b in difflib.SequenceMatcher(None, ns, nw, autojunk=False).get_matching_blocks()) / len(ns)


def procesar(proyecto):
    """Escribe <proyecto>/assets/voz/palabras.json con el tiempo de cada palabra de cada frase."""
    proyecto = Path(proyecto).resolve()
    voz = proyecto / "assets" / "voz"
    dur = json.loads((voz / "duraciones.json").read_text(encoding="utf-8"))
    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    res, bajas = {}, []
    for k, info in dur.items():
        x, sr = sf.read(voz / f"{k}.wav", dtype="float32")
        if x.ndim > 1:
            x = x.mean(axis=1)
        x16 = np.interp(np.arange(0, len(x) / sr, 1 / 16000), np.arange(len(x)) / sr, x).astype("float32")   # a 16 kHz
        segs, _ = modelo.transcribe(x16, language="es", word_timestamps=True, beam_size=5)
        ww = [w for s in segs for w in (s.words or [])]
        res[k] = alinear(info["texto"], ww, info["segundos"])
        cob = cobertura(info["texto"], ww)
        print(f"[{k}] whisper oyó ({cob:.0%} del texto): " + " ".join(w.word.strip() for w in ww))
        if cob < COBERTURA_MIN:
            bajas.append(f"{k} ({cob:.0%}): «{info['texto'][:50]}»")
    (voz / "palabras.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("LISTO palabras.json")
    if bajas:
        raise RuntimeError("La voz no dice lo que debería en: " + "; ".join(bajas) + ". Se rehace con --forzar.")


if __name__ == "__main__":
    procesar(sys.argv[1])
