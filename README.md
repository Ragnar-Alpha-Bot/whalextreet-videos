# whalextreet-videos

Fábrica de vídeos animados de WhaleXtreet: voz en español (Qwen3-TTS, Apache 2.0), subtítulos palabra a palabra (Whisper, MIT),
animación con HyperFrames (Apache 2.0), sonidos propios generados con código y el profesor de la marca.
Repositorio público a propósito: así las ejecuciones de GitHub Actions no gastan cuota.

## Cómo se hace un vídeo
1. Un **guion de escenas** (`proyectos/<nombre>/storyboard.json`): tema, tipo de post y una lista de escenas, cada una con su texto de voz.
   Formato y límites: `caja/guion.py`. Si el guion no es válido, se rechaza con un mensaje claro.
2. `python caja/pipeline.py proyectos/<nombre>` → valida, genera la voz D, calcula el tiempo de cada palabra, monta y renderiza el MP4.
3. En GitHub: Actions → «Generar vídeo» → nombre del proyecto → descarga el MP4 como artefacto.

## Piezas
- `caja/escenas.py` — escenas: titulo, numero, grafico, barras, donut, lista, tarjetas, pregunta. Cada una engancha sus apariciones a palabras de la voz.
- `caja/sfx.py` — sonidos propios con variantes (whoosh, pop, card, ding, riser, blip…): un sonido en cada transición y aparición.
- `caja/paletas.py` — marca fija (ballena, fondo azul marino, tipografías, cierre) + color de acento por tema: cripto, bolsa, alerta, macro, educativo.
- `formatos_video.json` — cuándo sale el profesor: presentador (todo), cameo (gancho y cierre), solo_datos (nunca).
- `perfiles/voz_D.pt`, `profesor/`, `marca/` — voz clonada, personaje y recursos de marca.
- `tests/test_caja.py`, `test_formatos.py` — pruebas con datos sintéticos.

No hay claves en este repositorio y no deben añadirse nunca. Las claves van en los secretos de GitHub.
