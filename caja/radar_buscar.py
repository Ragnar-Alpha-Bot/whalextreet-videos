"""Radar semanal: de los resultados crudos de las búsquedas (YouTube Shorts y TikTok) saca los vídeos que superan el umbral de visualizaciones.

Las búsquedas las hace la tarea semanal con las herramientas de datos (ver radar/PROCEDIMIENTO_SEMANAL.md); cada respuesta puede ser enorme y se guarda en un
archivo JSON. Este script lee esos archivos, se queda con los vídeos de 1 millón de visualizaciones o más (o el umbral que se indique), los clasifica por tema,
quita los que ya se vieron en semanas anteriores (radar/vistos.json) y escribe radar/candidatos/AAAA-MM-DD.json y .md.

    python caja/radar_buscar.py --carpeta <carpeta con los JSON> [--desde-min 180] [--min 1000000] [--max 15]
    python caja/radar_buscar.py --archivos a.json b.json ...

No descarga ni toca ningún vídeo: solo lee cifras que ya vienen en las respuestas.
"""
import argparse
import datetime
import json
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RADAR = RAIZ / "radar"
UMBRAL = 1_000_000

# tema -> palabras clave (minúsculas, sin tildes) que lo identifican en el título o la descripción, en español e inglés
TEMAS = {
    "ETFs y fondos": ["etf", "index fund", "fondo indexado", "fondos indexados", "fondo de inversion", "fondos de inversion", "vanguard", "s&p 500", "sp500", "msci", "mutual fund"],
    "Narrativas (IA, chips, emergentes, metales)": ["inteligencia artificial", " ai ", "semiconductor", "chips", "emergentes", "emerging", "uranio", "uranium", "gold", " oro ", "plata", "silver", "precious metal", "metales"],
    "Acciones": ["stock", "stocks", "acciones", "accion ", "nvidia", "tesla", "apple", "amd", "microsoft", "amazon", "wall street", "nasdaq", "dow jones", "earnings", "dividend", "dividendo"],
    "Cripto": ["bitcoin", "btc", "crypto", "cripto", "ethereum", "altcoin", "solana", "blockchain", "binance"],
    "Trading y análisis técnico": ["trading", "trader", "day trad", "technical analysis", "analisis tecnico", "candlestick", "velas japonesas", "soporte y resistencia", "support and resistance", "rsi", "stop loss", "swing"],
    "Noticias y mercado hoy": ["news", "noticias", "market today", "mercado hoy", "crash", "recession", "recesion", "se desploma", "cae la bolsa", "falling", "rally", "fed ", "tipos de interes", "interest rate"],
    "Ahorro e interés compuesto": ["compound", "interes compuesto", "ahorr", "saving", "save money", "50/30/20", "50 30 20", "fondo de emergencia", "emergency fund", "budget", "presupuesto"],
    "Errores y consejos de inversión": ["mistake", "errores", "error ", "advice", "consejo", "tips", "beginner", "principiante", "invertir", "investing", "invest "],
}
_ES = re.compile(r"[áéíóúñ¿¡]|\b(el|la|los|las|de|que|para|con|por|una|un|como|cómo|es|en|tu|tus|dinero|invertir)\b", re.I)


def sin_tildes(t):
    return (str(t).lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n"))


def tema(texto):
    t = " " + sin_tildes(texto) + " "
    for nombre, claves in TEMAS.items():
        if any(c in t for c in claves):
            return nombre
    return "Otros"


def idioma(texto, declarado=None):
    if declarado:
        return str(declarado)[:2].lower()
    return "es" if len(_ES.findall(str(texto))) >= 2 else "en"


def _recorrer(x):
    """Todos los diccionarios de una estructura JSON."""
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from _recorrer(v)
    elif isinstance(x, list):
        for v in x:
            yield from _recorrer(v)


def extraer(datos):
    """Vídeos de una respuesta (YouTube: shorts/videos con viewCountInt; TikTok: search_item_list con statistics.play_count)."""
    out = []
    for d in _recorrer(datos):
        for clave in ("shorts", "videos"):
            for x in d.get(clave) or []:
                if isinstance(x, dict) and x.get("id") and isinstance(x.get("viewCountInt"), (int, float)):
                    titulo = x.get("title") or ""
                    out.append({"plataforma": "youtube_shorts" if x.get("type") == "short" or clave == "shorts" else "youtube", "id": "yt-" + str(x["id"]), "url": x.get("url") or f"https://www.youtube.com/watch?v={x['id']}",
                                "titulo": titulo, "vistas": int(x["viewCountInt"]), "duracion_s": x.get("lengthSeconds"), "publicado": x.get("publishedTimeText") or x.get("publishedTime"),
                                "idioma": idioma(titulo), "tema": tema(titulo)})
        for x in d.get("search_item_list") or []:
            if not isinstance(x, dict):
                continue
            a = x.get("aweme_info") if isinstance(x.get("aweme_info"), dict) else x
            st = a.get("statistics") or {}
            if a.get("aweme_id") and isinstance(st.get("play_count"), (int, float)):
                desc = a.get("desc") or ""
                out.append({"plataforma": "tiktok", "id": "tt-" + str(a["aweme_id"]), "url": a.get("url") or "", "titulo": desc[:140], "vistas": int(st["play_count"]), "likes": st.get("digg_count"),
                            "guardados": st.get("collect_count"), "compartidos": st.get("share_count"), "autor": (a.get("author") or {}).get("unique_id"),
                            "publicado": a.get("create_time_utc"), "idioma": idioma(desc, a.get("desc_language")), "tema": tema(desc)})
    return out


def leer(rutas):
    vistos, todos = set(), []
    for r in rutas:
        try:
            datos = json.loads(Path(r).read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        for v in extraer(datos):
            if v["id"] not in vistos:
                vistos.add(v["id"])
                todos.append(v)
    return todos


def seleccionar(videos, minimo=UMBRAL, ya_vistos=(), maximo=15):
    """Los vídeos con `minimo` o más visualizaciones que no se vieron antes, de más a menos vistos."""
    ya = set(ya_vistos)
    nuevos = [v for v in videos if v["vistas"] >= minimo and v["id"] not in ya]
    return sorted(nuevos, key=lambda v: -v["vistas"])[:maximo]


def formato_vistas(n):
    return f"{n / 1_000_000:.1f} M".replace(".", ",") if n >= 1_000_000 else f"{n // 1000} K"


def informe_md(fecha, cands, minimo, revisados):
    lineas = [f"# Radar semanal · {fecha}", "", f"{len(cands)} vídeos con **{formato_vistas(minimo)} de visualizaciones o más** (de {revisados} revisados esta semana).", ""]
    for i, v in enumerate(cands, 1):
        lineas += [f"{i}. **{formato_vistas(v['vistas'])}** · {v['plataforma'].replace('_', ' ')} · {v['idioma'].upper()} · {v['tema']}", f"   {v['titulo']}", f"   {v['url']}", ""]
    return "\n".join(lineas) + "\n"


def escribir(cands, fecha, minimo, revisados):
    (RADAR / "candidatos").mkdir(parents=True, exist_ok=True)
    js = RADAR / "candidatos" / f"{fecha}.json"
    js.write_text(json.dumps({"fecha": fecha, "umbral": minimo, "revisados": revisados, "candidatos": cands}, ensure_ascii=False, indent=2), encoding="utf-8")
    (RADAR / "candidatos" / f"{fecha}.md").write_text(informe_md(fecha, cands, minimo, revisados), encoding="utf-8")
    vp = RADAR / "vistos.json"
    antes = json.loads(vp.read_text(encoding="utf-8")) if vp.exists() else []
    vp.write_text(json.dumps(sorted(set(antes) | {c["id"] for c in cands}), indent=1), encoding="utf-8")
    return js


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carpeta")
    ap.add_argument("--archivos", nargs="*", default=[])
    ap.add_argument("--desde-min", type=int, default=180, help="con --carpeta: solo los archivos modificados en los últimos N minutos")
    ap.add_argument("--min", type=int, default=UMBRAL)
    ap.add_argument("--max", type=int, default=15)
    ap.add_argument("--fecha", default=datetime.date.today().isoformat())
    a = ap.parse_args(argv)
    rutas = list(a.archivos)
    if a.carpeta:
        corte = time.time() - a.desde_min * 60
        rutas += [str(p) for p in Path(a.carpeta).glob("*.txt") if p.stat().st_mtime >= corte] + [str(p) for p in Path(a.carpeta).glob("*.json") if p.stat().st_mtime >= corte]
    if not rutas:
        print("No hay archivos de resultados que leer.")
        return 2
    videos = leer(rutas)
    vp = RADAR / "vistos.json"
    ya = json.loads(vp.read_text(encoding="utf-8")) if vp.exists() else []
    cands = seleccionar(videos, a.min, ya, a.max)
    print(f"{len(videos)} vídeos revisados · {len(cands)} nuevos con {formato_vistas(a.min)} o más")
    print(escribir(cands, a.fecha, a.min, len(videos)))      # también sin candidatos: el aviso dice «esta semana no hay nada nuevo»
    return 0


if __name__ == "__main__":
    sys.exit(main())
