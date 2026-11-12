"""Revisión automática de calidad de un vídeo ANTES de enviarlo: textos cortados o solapados, contraste, errores de la página y una hoja de fotogramas.

    python caja/qa.py proyectos/<nombre>             # revisa el proyecto montado (index.html) y escribe proyectos/<nombre>/qa.txt
    python caja/qa.py proyectos/<nombre> --hoja      # además, crea la hoja de fotogramas del último MP4 de renders/
    python caja/qa.py proyectos/<nombre> --estricta  # sale con error (1) si hay problemas graves

Usa `npx hyperframes check` (el mismo motor que renderiza): mide en un navegador real cada texto de la composición en varios instantes.
Solo cuenta como GRAVE lo que se nota en el vídeo: errores de la página, textos que se salen del cuadro o se pisan, y contraste muy bajo.
Los avisos de estilo (líneas de subtítulo muy rápidas, estructura del HTML) solo se cuentan, no molestan.
"""
import json
import subprocess
import sys
from pathlib import Path

VERSION_HF = "0.9.25"          # la misma que usa el render (caja/pipeline.py)
MUESTRAS = 9                   # instantes que mide por vídeo (más muestras = más tardanza)
# códigos que SÍ se notan en pantalla: se muestran siempre
GRAVES = {"text_overflow", "container_overflow", "canvas_overflow", "content_overlap", "occluded_text", "canvas_covered", "panel_out_of_canvas",
          "escaped_container", "text_clipped", "contrast_aa_failure", "text_below_floor"}   # «first_frame_empty» no: la portada se hace aparte (caja/portada.py)


def _codigo(f):
    return f.get("code") or f.get("rule") or "?"


def analizar(d):
    """Separa lo grave (se nota en el vídeo) de los avisos menores. d = informe JSON de `hyperframes check`."""
    graves, avisos = [], {}
    for seccion in ("runtime", "layout", "contrast", "craft", "lint"):
        for f in (d.get(seccion) or {}).get("findings", []):
            cod = _codigo(f)
            if f.get("severity") == "error" or (cod in GRAVES and seccion != "lint"):
                graves.append((seccion, cod, f))
            else:
                avisos[cod] = avisos.get(cod, 0) + 1
    return graves, avisos


def informe(graves, avisos):
    lineas = []
    if not graves:
        lineas.append("✔ Sin textos cortados ni solapados, sin errores de la página y con contraste suficiente.")
    for seccion, cod, f in graves:
        t = f.get("time")
        donde = f" a los {t:.1f} s" if isinstance(t, (int, float)) else ""
        txt = (f.get("text") or "").strip()
        lineas.append(f"✖ {cod}{donde}: {f.get('message', '')[:140]}" + (f" [{txt[:40]}]" if txt else "") + f" ({f.get('selector', '')})")
    if avisos:
        lineas.append("Avisos menores (no bloquean): " + ", ".join(f"{k} ×{v}" for k, v in sorted(avisos.items())))
    return lineas


def revisar(proyecto):
    """Ejecuta el `check` y devuelve (informe en texto, ¿hay problemas graves?)."""
    proyecto = Path(proyecto)
    r = subprocess.run(["npx", f"hyperframes@{VERSION_HF}", "check", str(proyecto), "--json", "--samples", str(MUESTRAS)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900, shell=(sys.platform == "win32"))
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return f"No se pudo leer el informe de `check` (código {r.returncode}): {(r.stdout or r.stderr)[:300]}", True
    if d.get("browserSkipped"):
        return "La revisión no pudo abrir el navegador: no se ha comprobado nada.", True
    graves, avisos = analizar(d)
    n = d["layout"].get("samples", "?")
    n = len(n) if isinstance(n, list) else n
    lineas = [f"Revisión automática de «{proyecto.name}» ({n} instantes de {d['layout'].get('duration', 0):.0f} s)"]
    lineas += informe(graves, avisos)
    (proyecto / "qa.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return "\n".join(lineas), bool(graves)


def hoja(proyecto, columnas=6, filas=3):
    """Hoja de contacto con fotogramas repartidos por el último MP4 de renders/. Devuelve la ruta del PNG (o None)."""
    proyecto = Path(proyecto)
    mp4s = sorted((proyecto / "renders").glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    if not mp4s:
        return None
    mp4 = mp4s[-1]
    sal = mp4.with_name(mp4.stem + "_hoja.png")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                               capture_output=True, text=True).stdout.strip() or 0)
    n = columnas * filas
    fps = n / max(dur, 1)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4), "-vf", f"fps={fps:.5f},scale=270:-1,tile={columnas}x{filas}", "-frames:v", "1", str(sal)], check=True)
    return sal


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    texto, hay_graves = revisar(args[0])
    print(texto)
    if "--hoja" in argv:
        h = hoja(args[0])
        print("Hoja de fotogramas:", h or "(no hay MP4 todavía)")
    return 1 if (hay_graves and "--estricta" in argv) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
