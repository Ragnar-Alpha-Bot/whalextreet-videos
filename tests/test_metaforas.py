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

# --- escenas de panel: pasos y checklist ---
import fidelidad  # noqa: E402
assert "pasos" in ESCENAS and "checklist" in ESCENAS
assert "pasos:" in storyboard_ia.SISTEMA and "checklist:" in storyboard_ia.SISTEMA and "__ICONOS__" not in storyboard_ia.SISTEMA and "persona|barras" in storyboard_ia.SISTEMA
e = []
ESCENAS["pasos"][1]({"fase": "FASE 1", "items": [{"n": "TU PRESUPUESTO"}, {"n": "TU FONDO", "icono": "no_existe"}]}, e.append)
assert e, "icono desconocido"
e = []
ESCENAS["pasos"][1]({"fase": "FASE 1 · TU PLAN", "items": [{"n": "TU PRESUPUESTO", "etiqueta": "PRIMERO", "icono": "cartera"}, {"n": "TU FONDO"}, {"n": "TU INVERSIÓN"}]}, e.append)
assert not e, e
e = []
ESCENAS["pasos"][1]({"items": [{"n": "A"}]}, e.append)
assert e, "mínimo 2 pasos"
e = []
ESCENAS["checklist"][1]({"titulo": "ANTES DE INVERTIR", "items": ["Fondo de emergencia", {"t": "Sin deudas caras"}, "Plazo claro"]}, e.append)
assert not e, e
e = []
ESCENAS["checklist"][1]({"titulo": "x", "items": ["a" * 50, "b"]}, e.append)
assert e
p = paleta("cripto")
c = Ctx(2, 3.0, 9.0, 3.1, 8.8, [{"t": "fondo", "ini": .5, "fin": .9}, {"t": "deudas", "ini": 1.5, "fin": 1.9}], 648, 1010, p)
h, j = ESCENAS["pasos"][0](c, {"fase": "FASE 1 · TU PLAN", "items": [{"n": "TU PRESUPUESTO"}, {"n": "TU FONDO", "cuando": "fondo"}, {"n": "TU INVERSIÓN"}]})
assert "01" in h and "02" in h and "03" in h and "FASE 1" in h and len(j) >= 9
c = Ctx(3, 3.0, 9.0, 3.1, 8.8, [{"t": "fondo", "ini": .5, "fin": .9}], 984, 1010, p)
h, j = ESCENAS["checklist"][0](c, {"titulo": "ANTES DE INVERTIR", "items": [{"t": "Fondo de emergencia", "cuando": "fondo"}, "Sin deudas caras", "Plazo claro"]})
assert "0/3" in h and "3/3" in h and "stroke=\"var(--up)\"" in h and "var(--up)" in "".join(j)
# las cifras de estas escenas también cuentan como datos y deben salir del post
sb = {"tema": "bolsa", "escenas": [{"tipo": "metafora", "motivo": "hucha", "titulo": "AHORRA 87 € AL MES"}, {"tipo": "pasos", "items": [{"n": "GANA 34 %"}, {"n": "SIN CIFRA"}]},
                                     {"tipo": "checklist", "titulo": "CHECK", "items": ["Rendimiento 61 %", "Otro"]}]}
pr = fidelidad.comprobar(sb, "Un post sin esas cifras")
assert any("87" in x for x in pr) and any("34" in x for x in pr) and any("61" in x for x in pr), pr
validar({"tema": "bolsa", "escenas": [{"tipo": "gancho", "voz": "Tu plan empieza hoy.", "texto": "TU PLAN"}, {"tipo": "pasos", "voz": "Tres pasos.", "fase": "FASE 1", "items": [{"n": "A"}, {"n": "B"}]},
                                       {"tipo": "checklist", "voz": "Marca cada punto.", "titulo": "T", "items": ["a", "b"]}, {"tipo": "cta"}]})
print("OK: pasos y checklist")

# --- informe de uso ---
import informe_metaforas  # noqa: E402
sbs = [{"escenas": [{"tipo": "gancho", "motivo": "balanza"}, {"tipo": "metafora", "motivo": "hucha"}, {"tipo": "pasos"}, {"tipo": "cta"}]},
       {"escenas": [{"tipo": "gancho", "motivo": "balanza"}, {"tipo": "metafora", "motivo": "ya_no_existe"}, {"tipo": "cta"}]}]
assert informe_metaforas.resumen_escenas(sbs[0]) == "gancho(balanza) · metafora(hucha) · pasos · cta"
mot, tip, n = informe_metaforas.contar(sbs)
assert mot["balanza"] == 2 and mot["hucha"] == 1 and tip["cta"] == 2 and n == 2
txt = informe_metaforas.informe(sbs)
assert "balanza 2" in txt and "ya no existen" in txt and "no han salido nunca" in txt
print("OK: informe de metáforas")
