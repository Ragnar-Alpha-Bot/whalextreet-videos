"""Qué escenas y metáforas usan los vídeos: resumen de un guion para el registro y informe de uso del catálogo.

    python caja/informe_metaforas.py proyectos            # recorre proyectos/*/storyboard.json
    python caja/informe_metaforas.py carpeta1 carpeta2    # cualquier carpeta con storyboard.json (p. ej. artefactos descargados)

Sirve para la revisión semanal: qué metáforas salen más, cuáles no salen nunca (candidatas a retirar o a mejorar) y qué escenas elige Gemini.
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from escenas_meta import CATALOGO  # noqa: E402


def resumen_escenas(sb):
    """Una línea para el registro: «gancho(billete_se_va) · metafora(hucha) · pasos · checklist · cta»."""
    partes = []
    for e in sb.get("escenas", []):
        m = e.get("motivo")
        partes.append(f"{e.get('tipo')}({m})" if m else str(e.get("tipo")))
    return " · ".join(partes)


def contar(storyboards):
    """Devuelve (contador de motivos, contador de tipos de escena, nº de vídeos)."""
    motivos, tipos = collections.Counter(), collections.Counter()
    for sb in storyboards:
        for e in sb.get("escenas", []):
            tipos[e.get("tipo")] += 1
            if e.get("motivo"):
                motivos[e["motivo"]] += 1
    return motivos, tipos, len(storyboards)


def informe(storyboards):
    motivos, tipos, n = contar(storyboards)
    sal = ["Informe de uso — %d vídeos" % n, "", "Escenas más usadas: " + (", ".join(f"{k} {v}" for k, v in tipos.most_common()) or "ninguna"), ""]
    sal.append("Metáforas más usadas: " + (", ".join(f"{k} {v}" for k, v in motivos.most_common(10)) or "ninguna"))
    nunca = sorted(set(CATALOGO) - set(motivos))
    sal.append(f"Metáforas que no han salido nunca ({len(nunca)} de {len(CATALOGO)}): " + (", ".join(nunca) or "ninguna"))
    desconocidas = sorted(set(motivos) - set(CATALOGO))
    if desconocidas:
        sal.append("AVISO, motivos que ya no existen en el catálogo: " + ", ".join(desconocidas))
    return "\n".join(sal)


def cargar(rutas):
    sbs = []
    for r in rutas:
        r = Path(r)
        for f in ([r] if r.is_file() else sorted(r.rglob("storyboard.json"))):
            try:
                sbs.append(json.loads(f.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                print("aviso: no pude leer", f)
    return sbs


if __name__ == "__main__":
    print(informe(cargar(sys.argv[1:] or ["proyectos"])))
