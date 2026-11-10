"""Metáforas visuales: el catálogo de Python y el de marca/motivos.js coinciden, la escena valida y el gancho admite «motivo»."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import escenas_meta  # noqa: E402
import storyboard_ia  # noqa: E402
from escenas import ESCENAS, Ctx  # noqa: E402
from guion import validar  # noqa: E402
from paletas import paleta  # noqa: E402

js = escenas_meta.motivos_js()
assert js == set(escenas_meta.CATALOGO), (js ^ set(escenas_meta.CATALOGO))
assert len(js) >= 50, len(js)
texto_js = (RAIZ / "marca" / "motivos.js").read_text(encoding="utf-8")
assert "fillText(\"1" not in texto_js and "Math.random" not in texto_js, "los motivos no llevan cifras sueltas ni azar (deben salir igual en cada render)"
assert "metafora" in ESCENAS

e = []
ESCENAS["metafora"][1]({"motivo": "no_existe"}, e.append)
assert e, "debe rechazar un motivo desconocido"
e = []
ESCENAS["metafora"][1]({"motivo": "hucha", "titulo": "x" * 50}, e.append)
assert e, "título demasiado largo"
e = []
ESCENAS["metafora"][1]({"motivo": "hucha", "titulo": "AHORRO", "subtitulo": "Poco a poco"}, e.append)
assert not e, e

base = {"tema": "bolsa", "escenas": [
    {"tipo": "gancho", "voz": "Tu dinero parado pierde valor ahora mismo.", "texto": "TU DINERO SE DESHACE", "motivo": "billete_se_va"},
    {"tipo": "metafora", "voz": "Cada año cuesta más comprar lo mismo.", "motivo": "grafico_sube", "titulo": "LA INFLACIÓN"},
    {"tipo": "metafora", "voz": "Por eso conviene invertir.", "motivo": "arbol_monedas"},
    {"tipo": "cta"}]}
validar(base)
dup = {"tema": "bolsa", "escenas": [dict(base["escenas"][0], motivo="hucha"), dict(base["escenas"][1], motivo="hucha"), {"tipo": "cta"}]}
try:
    validar(dup)
    raise SystemExit("debía rechazar el mismo motivo dos veces")
except ValueError as ex:
    assert "hucha" in str(ex)
mal = {"tema": "bolsa", "escenas": [dict(base["escenas"][0], motivo="nada"), {"tipo": "cta"}, {"tipo": "cta"}]}
try:
    validar(mal)
    raise SystemExit("debía rechazar un motivo desconocido en el gancho")
except ValueError:
    pass

# el HTML del gancho y de la metáfora lleva el canvas y el módulo
p = paleta("bolsa")
c = Ctx(1, 3.0, 8.0, 3.1, 7.8, [], 984, 1010, p)
html, js_ = ESCENAS["metafora"][0](c, base["escenas"][1])
assert "<canvas" in html and "./assets/motivos.js" in html and 'dibujar("grafico_sube"' in html and "LA INFLACIÓN" in html
c0 = Ctx(0, 0.0, 4.0, 0.05, 3.5, [], 984, 1010, p)
html0, _ = ESCENAS["gancho"][0](c0, base["escenas"][0])
assert "<canvas" in html0 and 'dibujar("billete_se_va"' in html0
c0 = Ctx(0, 0.0, 4.0, 0.05, 3.5, [], 984, 1010, p)
html1, _ = ESCENAS["gancho"][0](c0, dict(base["escenas"][0], grafico="cifra", cifra={"valor": 5, "decimales": 0, "sufijo": "%"}))
assert "<canvas" not in html1, "con cifra gigante manda la cifra"

# Gemini conoce las metáforas y recibe sugerencias repartidas por todo el catálogo
assert "METÁFORAS DISPONIBLES" in storyboard_ia.SISTEMA and "hucha" in storyboard_ia.SISTEMA and "metafora:" in storyboard_ia.SISTEMA
assert storyboard_ia.SISTEMA.index("METÁFORAS DISPONIBLES") < storyboard_ia.SISTEMA.index("SALIDA")
assert "METÁFORAS SUGERIDAS" in storyboard_ia._prompt({"format": "x", "parts": ["un post"]})
vistos = set()
for i in range(200):
    vistos.update(escenas_meta.sugeridos(f"post {i}"))
assert len(vistos) >= len(escenas_meta.CATALOGO) - 3, len(vistos)
assert escenas_meta.sugeridos("igual") == escenas_meta.sugeridos("igual")
print("OK: test_metaforas")

# --- el gancho cabe en su zona (no pisa subtítulos ni pie), aun con kicker, subtexto largo y 3 líneas de texto ---
import escenas  # noqa: E402
peor = [("TU DINERO SE DESHACE", {"kicker": "ERROR COMÚN", "subtexto": "Y casi nadie lo nota cuando mira su cuenta"}),
        ("¿COMPRASTE PORQUE SUBÍA O PORQUE LO ENTIENDES?", {"kicker": "NADIE LO MIRA", "subtexto": "Lo que decide todo y casi nadie lee antes de comprar"}),
        ("PERDER 50 % EXIGE GANAR 100 %", {"kicker": "ERROR COMÚN", "subtexto": "Las matemáticas de las pérdidas"}),
        ("AHORRA", {})]
for texto, extra in peor:
    d0 = dict(texto=texto, **extra)
    ws = texto.split()
    n = len(texto)
    fs = 200 if n <= 14 else 160 if n <= 24 else 128 if n <= 34 else 106
    fs = min(fs, int(0.92 * 984 / (0.70 * max(len(w) for w in ws))))
    for graf, motivo in (("pulso", None), ("caida", None), ("ninguno", "billete_se_va")):
        f2 = escenas._ajustar_fs_gancho(ws, fs, d0, graf, motivo, 984)
        gr = escenas.altura_motivo_gancho(ws, f2, d0) if motivo else {"pulso": 260, "caida": 300}[graf]
        total = escenas._alto_fijo_gancho(ws, f2, d0) + gr
        assert total <= escenas.AREA_UTIL + 40, (texto, graf, f2, total)
print("OK: el gancho cabe en su zona")
