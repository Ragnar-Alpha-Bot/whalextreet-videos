# Radar de formatos

Aprende de shorts que **ya han funcionado** (en español o en inglés) y los vuelve a hacer en español, con nuestra marca, nuestra voz y **datos reales**.

## Qué copiamos y qué no
| Sí (lo que hizo funcionar al vídeo) | No (lo que sería copiar) |
|---|---|
| **El tema** exacto del que se habla | Su guion traducido frase a frase |
| **La fórmula del gancho**: el mismo tipo y la misma idea (el mismo contraste, la misma pregunta, la misma lista cerrada) | Sus cifras, nombres propios o afirmaciones sin comprobar |
| **La estructura**: qué pasa y cuándo (gancho → giro → explicación → cierre) | Sus imágenes, su voz o su música |
| El tipo de cierre y la duración | Una afirmación que no podemos sostener (consejos de compra, «lo único que necesitas»…) |

El gancho en español sigue **la misma idea**, pero se escribe con otras palabras y con **nuestras cifras reales y fechadas**. Así aprovechamos lo que ya se sabe que funciona sin plagiar a nadie y sin repetir datos que no hemos comprobado (la regla de la marca es datos reales siempre). Las plataformas penalizan el contenido «reutilizado»: reescribir y aportar datos propios nos protege.

## Cómo se usa
1. **Buscar** vídeos que funcionan en el nicho. Con las herramientas de datos conectadas (búsqueda de YouTube Shorts y de TikTok por palabra clave; transcripción de YouTube; cifras de TikTok):
   - YouTube Shorts: buscar por palabra clave con `type: shorts` y **sin filtros** (con `sortBy` o `uploadDate` a veces devuelve vacío). Ordenar luego por visualizaciones.
   - TikTok: `search-videos` con `sort_by: most-liked` (ordenar después por `play_count`: el orden de la herramienta no es fiable).
   - Cada consulta cuesta unos 2 créditos. **No se descarga ningún vídeo** sin permiso.
2. **Evidencia.** La mejor es la **transcripción** (YouTube suele tenerla). En TikTok la transcripción suele venir vacía: entonces la ficha dice `evidencia: "descripcion"` (solo se conoce el texto del post) o `"visto_a_mano"` (nos pasas el vídeo o el gancho). Una ficha con `descripcion` guarda una hipótesis, no un hecho.
3. **Escribir la ficha** en `radar/fichas/<id>.json` (copia una existente). Campos: `plataforma`, `url`, `idioma`, `metricas.vistas`, `gancho_original` (**cita de máx. 25 palabras**, no el guion), `formula` (`tipo_gancho`, `tema`, `estructura` con pasos `{seg, beat}`, `cierre`), `por_que_funciona` y `adaptar` (`tema_es`, `idea_gancho_es`, `datos_reales_necesarios`, `cuidado`). **El texto de la ficha no puede llevar cifras del original** (el validador lo rechaza).
4. **Reunir los datos reales** del tema en `radar/datos/<id>.json` (frases con su cifra, fuente y fecha). Solo estas cifras pueden salir en el vídeo.
5. `python caja/radar.py validar` comprueba las fichas. `python caja/radar.py encargo <id>` muestra el encargo.
6. **Convertir el encargo en un guion de escenas**: con Gemini (`storyboard_ia.crear(radar.encargo(ficha, datos, oferta=...))`, que ya entiende el campo `radar`) o a mano, y seguir el pipeline de siempre (`python caja/pipeline.py proyectos/<nombre>`). Antes de publicar: `python caja/qa.py proyectos/<nombre> --hoja`.

## Comprobaciones automáticas (tests/test_radar.py)
- La ficha es válida y sin cifras ajenas.
- Si la fuente está **en español**, el gancho adaptado no puede compartir frases con el original (`parecido()`).
- El guion pasa `fidelidad.py` contra el encargo (solo datos reales), el aviso temprano de la oferta, la duración (~45 s) y la retención (sin saludos).

## Primeras fichas (consultadas el 12-nov-2026)
`python caja/radar.py lista` las ordena por visualizaciones: el short «What Is an Index Fund?» (17 M), «4 Index Funds You Need For Life» (2,8 M), «Index funds vs ETFs» (943 K), «ETFs vs. Stocks» (468 K) y dos de TikTok (730 K y 370 K visualizaciones). Ya hay dos adaptaciones hechas (`proyectos/radar-100-euros`, `proyectos/radar-comisiones`) y quedan tres fichas nuevas por adaptar.

## Límites que conviene saber
- Las visualizaciones de un vídeo no garantizan que su fórmula funcione para nosotros: es una apuesta informada, no una promesa.
- Algunos vídeos virales traen afirmaciones falsas o que no valen en España (p. ej. «los fondos indexados son difíciles de encontrar en Europa»). La ficha lo anota en `por_que_funciona` y en `cuidado`.
- Nunca se adapta un consejo personalizado («los únicos que necesitas de por vida»): se convierte en datos y en lo que ha pasado.
