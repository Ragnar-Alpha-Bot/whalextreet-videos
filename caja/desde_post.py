"""De un post aprobado a un vídeo en Telegram, todo seguido.

    python caja/desde_post.py post.json            # post.json = {"id", "format", "parts": [...], "platforms": [...], "chart": {...} (opcional)}
    python caja/desde_post.py post.json --sin-render   # solo el guion de escenas (no gasta voz ni render)

Pasos: guion de escenas con Gemini (validado y con cifras trazables) → voz D → tiempos de palabra → montaje → render → Telegram.
Si algo falla, avisa por Telegram («no pude hacer el vídeo de este post») y termina con error; nunca manda un vídeo a medias.
"""
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))
import telegram_envio  # noqa: E402
from storyboard_ia import StoryboardError, crear  # noqa: E402


def nombre_proyecto(post):
    pid = re.sub(r"[^A-Za-z0-9_-]", "", str(post.get("id") or "sin-id"))[:40] or "sin-id"
    return f"post-{pid}"


def main(post, render=True, cliente=None):
    proyecto = RAIZ / "proyectos" / nombre_proyecto(post)
    try:
        sb = crear(post, cliente)
        proyecto.mkdir(parents=True, exist_ok=True)
        (proyecto / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Guion de escenas listo: {len(sb['escenas'])} escenas, tema {sb['tema']}")
        from informe_metaforas import resumen_escenas
        print("Escenas:", resumen_escenas(sb))
        if not render:
            return proyecto, None
        import pipeline
        pipeline.main(proyecto, render=True)
        mp4 = sorted((proyecto / "renders").glob("*.mp4"), key=lambda f: f.stat().st_mtime)[-1]
        primera = (post.get("parts") or [""])[0].strip().replace("\n", " ")
        pie = f"🎬 Vídeo listo del post aprobado · 9:16 · para subir a TikTok, Instagram y Shorts.\n\n«{primera[:160]}»"
        telegram_envio.enviar_video(mp4, pie)
        print("Vídeo enviado a Telegram.")
        return proyecto, mp4
    except StoryboardError as e:
        telegram_envio.aviso(f"⚠️ No pude hacer el vídeo del post aprobado ({post.get('format')}): {e}")
        raise
    except Exception as e:  # noqa: BLE001
        telegram_envio.aviso(f"⚠️ Falló la creación del vídeo del post aprobado ({post.get('format')}): {e.__class__.__name__}")
        raise


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    post = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    main(post, render="--sin-render" not in sys.argv)
