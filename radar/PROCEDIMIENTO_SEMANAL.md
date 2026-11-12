# Procedimiento semanal del radar (para la tarea programada de Claude)

Objetivo: cada semana, buscar vídeos virales del nicho (YouTube Shorts y TikTok, en español e inglés) con **1 millón de visualizaciones o más** y mandar la lista nueva al Telegram del usuario. Nada se publica ni se adapta sin que el usuario lo pida.

## Pasos
1. **Copia de trabajo aparte** (no tocar la copia principal del repo, que puede tener trabajo a medias):
   ```
   cd C:\Users\Lele\Desktop\CLAUDE\videos\whalextreet-videos
   git fetch origin
   git worktree add <carpeta temporal>\radar -B radar-semanal origin/radar-semanal   # si la rama aún no existe: ... -B radar-semanal origin/main
   cd <carpeta temporal>\radar && git merge origin/main --no-edit
   ```
   La rama `radar-semanal` acumula las semanas (guarda `radar/vistos.json`, así no se repiten vídeos).
2. **Leer `radar/consultas.json`** y hacer las búsquedas con las herramientas de datos (Alexandria), en lotes de hasta 10 llamadas:
   - YouTube Shorts: proveedor `scrapecreators`, capacidad `youtube/search`, opciones `{"query": <consulta>, "type": "shorts"}`. **Sin** `sortBy` ni `uploadDate` (con ellos a veces devuelve vacío).
   - TikTok: `scrapecreators` → `tiktok/search-videos`, opciones `{"query": <consulta>, "sort_by": "most-liked", "trim": true}`.
   - Las respuestas son enormes: la herramienta las guarda en un archivo y avisa de su ruta. **No las leas enteras**; las procesa el script.
3. **Filtrar**, dentro de la copia de trabajo:
   `python caja\radar_buscar.py --carpeta <carpeta tool-results de esta sesión> --desde-min 240 --min 1000000 --max 15`
   (solo usa la librería estándar de Python). Escribe `radar/candidatos/AAAA-MM-DD.json` y `.md` y actualiza `radar/vistos.json`.
4. **Subir** a la rama `radar-semanal` (sin pull request, sin tocar `main`):
   `git add radar/candidatos radar/vistos.json && git commit -m "Radar semanal AAAA-MM-DD" && git push origin radar-semanal`.
   Al subir, el workflow «Aviso del radar semanal» envía el mensaje al Telegram del usuario.
5. **Comprobar** que salió: `gh run list --repo Ragnar-Alpha-Bot/whalextreet-videos --workflow radar-aviso.yml --limit 1`.
6. **Contar al usuario** en pocas líneas: cuántos vídeos se revisaron, cuántos nuevos pasaron el umbral y los 3 con más visualizaciones. Si algo falló, decirlo claro (nunca rellenar con datos viejos).
7. Quitar la copia de trabajo: `git worktree remove <carpeta temporal>\radar --force`.

## Reglas
- No descargar ningún vídeo, no publicar nada, no escribir claves en ningún archivo.
- Las visualizaciones no garantizan que algo funcione para la marca: la lista es para elegir, no para copiar.
- Si el usuario elige uno, el siguiente paso es una **ficha** (`radar/fichas/`), los **datos reales** del tema y la adaptación (ver `radar/README.md`).
- Coste aproximado: 68 consultas × 2 créditos ≈ 136 créditos por semana.
