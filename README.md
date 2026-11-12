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
- `marca/motivos.js` + `caja/escenas_meta.py` — **50 metáforas visuales** animadas (toro, oso, ciudad de velas, hucha, caja fuerte, cohete, ballena, blockchain, burbuja…), dibujadas con código propio (gratis, sin cifras ni datos inventados).
  Se usan como escena `metafora` y como `motivo` del gancho. Para ver todas: abre una galería con un servidor local sobre `marca/` (ver `tests/test_metaforas.py`).

- `caja/escenas_recursos.py` — **recursos de uso puntual** (no van en todos los vídeos; la IA solo los elige cuando el tema lo pide): escena `terminal` (comandos que se escriben solos; deben salir literales del post), escena `ranking` (cifra grande + título, con las cifras del post), escena `captura` (imagen real con recuadro y zoom; manual), `sello` en la metáfora (p. ej. GRATIS), `*palabra*` en cursiva serif (fuente Instrument Serif, licencia OFL, en `marca/`) y `"subs": "recuadro"` para subtítulos con la palabra activa en un cuadro de color. Prueba: `tests/test_recursos.py`; muestra: `proyectos/prueba-recursos`.
- `marca/personajes.js` + `caja/escenas_versus.py` — **formato «novato contra pro»** (salió de un vídeo de referencia): dos muñecos 2D animados con código propio (novato gris con gorra, pro del color del tema) que corren, teclean, miran un gráfico, saltan una valla o celebran; escena `versus` (dos paneles apilados con ronda numerada), `movil` (chat que se escribe solo, con sello), `calendario` (semana que se marca), `panel` (cifras que cuentan) y cierre `compartir` («Envíaselo a ese amigo que…», campo extra de la escena `cta`). Solo se usan cuando el tema lo pide. Prueba: `tests/test_versus.py`; muestra: `proyectos/pro-vs-amateur`.
- `caja/escenas_grafico.py` — **gráfico profesional con datos reales** (`grafico_pro`): línea, área o velas japonesas con TradingView Lightweight Charts (Apache 2.0, v4.2.0 en `marca/`; la escena muestra siempre su atribución). Se dibuja poco a poco, con zoom y anotaciones. Solo con una serie real del post: las cifras pasan la comprobación de `fidelidad.py`.
- `caja/radar.py` + `radar/` — **radar de formatos**: fichas de shorts que ya han funcionado (tema, fórmula del gancho, estructura) que se adaptan al español con la marca y datos reales (ver `radar/README.md`).
- `caja/qa.py` — **revisión automática de calidad**: `python caja/qa.py proyectos/<nombre> --hoja` mide con el navegador de HyperFrames textos cortados o solapados, contraste y errores de la página, y crea una hoja de fotogramas del MP4. Escribe `qa.txt` en el proyecto.
- **Retención** (pauta de la skill `yt-script`): el gancho promete, abre una pregunta y deja ver la recompensa; la escena 2 no abre con saludos ni peticiones; bucle abierto y un solo cierre. `storyboard_ia.py` lo pide y `problemas_retencion()` lo comprueba.
- `caja/escenas3d_nicho.py` — **más escenas 3D del nicho** (Three.js): `animal3d` (toro = mercado alcista, oso = bajista), `lingotes3d` (ahorro/oro), `linea3d` (gráfico de líneas 3D con los datos reales del post), `escudo3d` (proteger el capital) y `ciudad3d` (economía y crecimiento). Se reparten entre vídeos con `sugerencia_3d` (como máximo una por vídeo) y usan todo el ancho. Prueba: `tests/test_escenas3d_nicho.py`; muestra: `proyectos/toro-oso-3d`.
- **Duración según el vídeo:** los explicativos pueden durar 60-70 s; los que llevan oferta se mantienen en ~45 s (máx. 125 palabras de voz) y, en las 3 primeras escenas, avisan «al final te dejo… gratis» para que la gente llegue al cierre (en TikTok solo el 0,94 % vio entero un vídeo de 71 s). El código lo comprueba y la IA reintenta si falta.
- **Cierre con oferta** (campo `oferta` del `cta`): «COMENTA «PALABRA» y sígueme · te envío <recurso> por privado» (gancho + recurso + comentar y seguir, la mecánica que más hace crecer). La palabra y el recurso salen del post (`oferta` que manda la agencia), nunca de la IA; sin oferta, cierre normal. Prueba: `tests/test_oferta_cta.py`; muestra: `proyectos/oferta-skills`.
- `caja/sfx.py` — sonidos propios con variantes (whoosh, pop, card, ding, riser, blip…): un sonido en cada transición y aparición.
- `caja/paletas.py` — marca fija (ballena, fondo azul marino, tipografías, cierre) + color de acento por tema: cripto, bolsa, alerta, macro, educativo.
- `formatos_video.json` — cuándo sale el profesor: presentador (todo), cameo (gancho y cierre), solo_datos (nunca).
- `perfiles/voz_D.pt`, `profesor/`, `marca/` — voz clonada, personaje y recursos de marca.
- `tests/test_caja.py`, `test_formatos.py` — pruebas con datos sintéticos.

No hay claves en este repositorio y no deben añadirse nunca. Las claves van en los secretos de GitHub.
