"""De guion de escenas a vídeo MP4, todo seguido.

    python caja/pipeline.py proyectos/bolsa-per            # voz + palabras + montaje + render
    python caja/pipeline.py proyectos/bolsa-per --sin-render
    python caja/pipeline.py proyectos/bolsa-per --forzar   # rehace la voz aunque ya exista

Pasos: 1 validar guion · 2 voz D (Qwen3-TTS) · 3 tiempos de palabra (Whisper) · 4 montaje (HyperFrames HTML) · 5 render.
La voz se reutiliza si el texto no ha cambiado. Necesita el Python con qwen-tts y faster-whisper instalados.
"""
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))
from guion import hablantes, lineas, validar  # noqa: E402


def voz_al_dia(proyecto, lin, hab=None):
    f = proyecto / "assets" / "voz" / "duraciones.json"
    if not f.exists():
        return False
    d = json.loads(f.read_text(encoding="utf-8"))
    hab = hab or {}
    import frases
    huella = frases.huella_audio()
    return set(d) == set(lin) and all(d[k]["texto"] == lin[k] and d[k].get("voz", "profesor") == hab.get(k, "profesor") and d[k].get("huella") == huella
                                      and (proyecto / "assets" / "voz" / f"{k}.wav").exists() for k in lin)


def borrar_cache_de_lineas(lin, hab, claves):
    """Quita de voz_cache los trozos de esas líneas para que se vuelvan a generar (el modelo no habla igual dos veces)."""
    import frases
    import vozcache
    voces = json.loads((RAIZ / "marca" / "voces.json").read_text(encoding="utf-8"))
    cfg = frases.config_audio()
    for k in claves:
        pid = vozcache.id_perfil(RAIZ / "perfiles" / voces[hab.get(k, "profesor")])
        for frase, _ in frases.trocear(lin[k], cfg):
            vozcache.ruta(RAIZ / "voz_cache", vozcache.clave(frase, pid)).unlink(missing_ok=True)


def main(proyecto, render=True, forzar=False):
    proyecto = Path(proyecto).resolve()
    sb = validar(json.loads((proyecto / "storyboard.json").read_text(encoding="utf-8")))
    lin = lineas(sb)
    print(f"1/5 guion válido: {len(lin)} escenas, tema {sb['tema']}")
    (proyecto / "guion.json").write_text(json.dumps(lin, ensure_ascii=False, indent=1), encoding="utf-8")
    hab = {f"l{i}": h for i, h in enumerate(hablantes(sb), 1)}
    (proyecto / "hablantes.json").write_text(json.dumps(hab, ensure_ascii=False, indent=1), encoding="utf-8")
    for ronda in range(1, 4):                      # si la voz lee mal una frase, se repite solo esa frase (hasta 3 rondas)
        if forzar or not voz_al_dia(proyecto, lin, hab):
            print("2/5 generando la voz D (unos 10 s de cálculo por cada segundo de audio en CPU)…")
            subprocess.run([sys.executable, "-X", "utf8", str(RAIZ / "voz" / "generar_voz.py"), str(proyecto)], check=True)
            palabras_listas = False
        else:
            print("2/5 la voz ya está al día, se reutiliza")
            palabras_listas = (proyecto / "assets" / "voz" / "palabras.json").exists()
        if palabras_listas:
            print("3/5 tiempos de palabra ya calculados")
            break
        print("3/5 tiempos exactos de cada palabra (Whisper)…")
        import palabras
        try:
            palabras.procesar(proyecto)
            break
        except palabras.VozMala as e:
            if ronda == 3:
                raise
            print(f"Aviso: {e} Ronda {ronda}/3: se repiten solo esas frases.", flush=True)
            borrar_cache_de_lineas(lin, hab, e.claves)
            for f in ("duraciones.json", "palabras.json"):          # sin esto la voz «ya está al día» y no se rehace
                (proyecto / "assets" / "voz" / f).unlink(missing_ok=True)
            forzar = False
    print("4/5 montaje")
    from motor import construir
    resumen = construir(proyecto)
    if render:
        print("5/5 render con HyperFrames…")
        subprocess.run(["npx", "--yes", "hyperframes@0.9.25", "render"], cwd=proyecto, check=True, shell=(sys.platform == "win32"))
        mp4 = sorted((proyecto / "renders").glob("*.mp4"), key=lambda f: f.stat().st_mtime)[-1]
        import volumen
        antes, despues = volumen.normalizar(mp4)
        print(f"Volumen normalizado: {antes:.1f} → {despues:.1f} LUFS")
        import portada
        print("Portada (primer fotograma = gancho):", portada.poner_portada(mp4))
        print("VÍDEO:", mp4)
    return resumen


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0], render="--sin-render" not in sys.argv, forzar="--forzar" in sys.argv)
