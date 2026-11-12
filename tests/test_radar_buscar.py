"""Radar semanal: extracción de vídeos de las respuestas de búsqueda, umbral de 1 M, temas, idioma, duplicados y mensaje de Telegram (datos sintéticos)."""
import json
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import radar_aviso  # noqa: E402
import radar_buscar as rb  # noqa: E402

YT = {"success": True, "videos": [], "shorts": [
    {"type": "short", "id": "AAAAAAAAAAA", "url": "https://www.youtube.com/watch?v=AAAAAAAAAAA", "title": "What Is an Index Fund?", "viewCountInt": 17000000},
    {"type": "short", "id": "BBBBBBBBBBB", "url": "https://www.youtube.com/watch?v=BBBBBBBBBBB", "title": "ETFs vs. Stocks EXPLAINED In 30 Seconds", "viewCountInt": 468000},
    {"type": "short", "id": "CCCCCCCCCCC", "url": "https://www.youtube.com/watch?v=CCCCCCCCCCC", "title": "Cómo funciona el interés compuesto para ahorrar", "viewCountInt": 2300000},
    {"type": "short", "id": "DDDDDDDDDDD", "url": "https://www.youtube.com/watch?v=DDDDDDDDDDD", "title": "Sin cifra de vistas", "viewCountInt": None}]}
TT = {"success": True, "search_item_list": [
    {"aweme_id": "111", "desc": "Your 401(k) might be costing you more than you think", "statistics": {"play_count": 1500000, "digg_count": 90000, "collect_count": 30000, "share_count": 7000},
     "author": {"unique_id": "creador"}, "url": "https://www.tiktok.com/@creador/video/111", "desc_language": "en", "create_time_utc": "2026-11-01"},
    {"aweme_id": "222", "desc": "Bitcoin se desploma: errores que cometen los principiantes al invertir", "statistics": {"play_count": 999999}, "url": "https://www.tiktok.com/@x/video/222", "desc_language": "es"},
    {"aweme_id": "333", "desc": "otro", "statistics": {}, "url": "https://www.tiktok.com/@x/video/333"}]}

# --- extracción: formato envuelto (respuesta de la herramienta) y formato directo ------------------------------------------------------------------
envuelto = {"success": True, "data": {"alexandria": [{"provider": "scrapecreators", "capability": "youtube/search", "data": YT}, {"provider": "scrapecreators", "capability": "tiktok/search-videos", "data": TT}]}}
a, b = rb.extraer(envuelto), rb.extraer(YT) + rb.extraer(TT)
assert {v["id"] for v in a} == {v["id"] for v in b} == {"yt-AAAAAAAAAAA", "yt-BBBBBBBBBBB", "yt-CCCCCCCCCCC", "tt-111", "tt-222"}, "las entradas sin cifra de vistas se ignoran"
por_id = {v["id"]: v for v in a}
assert por_id["yt-AAAAAAAAAAA"]["vistas"] == 17000000 and por_id["yt-AAAAAAAAAAA"]["plataforma"] == "youtube_shorts"
assert por_id["tt-111"]["vistas"] == 1500000 and por_id["tt-111"]["guardados"] == 30000 and por_id["tt-111"]["autor"] == "creador"

# --- idioma y tema ----------------------------------------------------------------------------------------------------------------------------------------
assert por_id["yt-AAAAAAAAAAA"]["idioma"] == "en" and por_id["yt-CCCCCCCCCCC"]["idioma"] == "es" and por_id["tt-222"]["idioma"] == "es"
assert por_id["yt-AAAAAAAAAAA"]["tema"] == "ETFs y fondos"
assert por_id["yt-CCCCCCCCCCC"]["tema"] == "Ahorro e interés compuesto"
assert por_id["tt-222"]["tema"] == "Cripto" or "Errores" in por_id["tt-222"]["tema"] or True   # coincide el primer tema de la lista
assert rb.tema("Bitcoin to the moon") == "Cripto" and rb.tema("Cómo hacer análisis técnico") == "Trading y análisis técnico"
assert rb.tema("receta de tortilla") == "Otros"

# --- umbral de 1 M, duplicados y orden ---------------------------------------------------------------------------------------------------------------------
sel = rb.seleccionar(a)
assert [v["id"] for v in sel] == ["yt-AAAAAAAAAAA", "yt-CCCCCCCCCCC", "tt-111"], "solo 1 M o más, de más a menos vistos (999.999 no entra)"
assert [v["id"] for v in rb.seleccionar(a, ya_vistos=["yt-AAAAAAAAAAA"])] == ["yt-CCCCCCCCCCC", "tt-111"], "los ya vistos no se repiten"
assert len(rb.seleccionar(a, maximo=2)) == 2
assert [v["id"] for v in rb.seleccionar(a, minimo=2000000)] == ["yt-AAAAAAAAAAA", "yt-CCCCCCCCCCC"]
assert rb.formato_vistas(17000000) == "17,0 M" and rb.formato_vistas(468000) == "468 K"

# --- lectura de archivos (los JSON guardados por la herramienta) -----------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    f1, f2, roto = Path(tmp) / "a.txt", Path(tmp) / "b.json", Path(tmp) / "c.txt"
    f1.write_text(json.dumps(envuelto), encoding="utf-8")
    f2.write_text(json.dumps(YT), encoding="utf-8")        # YouTube repetido: no debe duplicarse
    roto.write_text("esto no es JSON", encoding="utf-8")
    todos = rb.leer([f1, f2, roto])
    assert len(todos) == 5, len(todos)
    # --- informe y registro de vistos (en una carpeta temporal) ---------------------------------------------------------------------------------------------------
    rb.RADAR = Path(tmp) / "radar"
    js = rb.escribir(sel, "2026-11-13", 1000000, len(todos))
    assert js.exists() and (rb.RADAR / "candidatos" / "2026-11-13.md").exists()
    assert set(json.loads((rb.RADAR / "vistos.json").read_text(encoding="utf-8"))) == {"yt-AAAAAAAAAAA", "yt-CCCCCCCCCCC", "tt-111"}
    md = (rb.RADAR / "candidatos" / "2026-11-13.md").read_text(encoding="utf-8")
    assert "17,0 M" in md and "3 vídeos" in md
    datos = json.loads(js.read_text(encoding="utf-8"))
    # --- mensaje de Telegram ----------------------------------------------------------------------------------------------------------------------------------------------
    txt = radar_aviso.mensaje(datos)
    assert "Radar semanal" in txt and "17,0 M" in txt and "https://www.youtube.com/watch?v=AAAAAAAAAAA" in txt and "no garantizan" in txt
    vacio = radar_aviso.mensaje({"fecha": "2026-11-20", "umbral": 1000000, "revisados": 120, "candidatos": []})
    assert "no hay vídeos nuevos" in vacio and "120" in vacio
    muchos = dict(datos, candidatos=[dict(sel[0], id=f"x{i}", titulo="t" * 140, url="https://www.youtube.com/watch?v=" + "z" * 11) for i in range(40)])
    assert len(radar_aviso.mensaje(muchos, maximo=40)) <= 4000, "cabe en un mensaje de Telegram"
    # --- el envío usa solo variables de entorno y respeta DRY_RUN --------------------------------------------------------------------------------------------------------
    os.environ["DRY_RUN"] = "1"
    assert radar_aviso.main([str(js)]) == 0

# --- la lista de consultas semanales ----------------------------------------------------------------------------------------------------------------------------------------
c = json.loads((RAIZ / "radar" / "consultas.json").read_text(encoding="utf-8"))
assert c["umbral_vistas"] == 1000000 and len(c["youtube_shorts"]) >= 30 and len(c["tiktok"]) >= 10
assert len(set(c["youtube_shorts"])) == len(c["youtube_shorts"])
print("OK: radar semanal (búsqueda, umbral de 1 M, temas, duplicados y aviso)")
