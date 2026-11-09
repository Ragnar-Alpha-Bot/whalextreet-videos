# whalextreet-videos

Fábrica de vídeos animados de WhaleXtreet: voz en español (Qwen3-TTS, Apache 2.0) + animación con HyperFrames (Apache 2.0)
+ el profesor de la marca. Repositorio público a propósito: así las ejecuciones de GitHub Actions no gastan cuota.

- `perfiles/voz_D.pt` — perfil de la voz clonada.
- `profesor/` — personaje en SVG (animado por el montaje).
- `formatos_video.json` — regla de cuándo sale el profesor (presentador / cameo / solo_datos).
- `plantillas/<nombre>/` — `guion.json` (texto por frases) + `construir.py` (escenas) + `assets/`.
- `.github/workflows/video.yml` — genera la voz, monta y renderiza; el MP4 queda como artefacto.

No hay claves en este repositorio y no deben añadirse nunca. Las claves van en los secretos de GitHub.
