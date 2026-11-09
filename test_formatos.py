"""Pruebas de la regla de formatos con datos sintéticos, y comprobación contra los formatos reales de la agencia.
Ejecutar:  python test_formatos.py"""
import re
import sys
from pathlib import Path

from formatos_video import cargar, formato_para, profesor_en

fallos = []


def comprobar(nombre, condicion):
    print(("OK   " if condicion else "FALLA"), nombre)
    if not condicion:
        fallos.append(nombre)


# --- 1. Pruebas con configuraciones inventadas -------------------------------------------------------------
cfg = {
    "formatos": {"presentador": {"profesor": "todo"}, "cameo": {"profesor": ["gancho", "cierre"]}, "solo_datos": {"profesor": "nunca"}},
    "por_formato_de_post": {"explicado": "presentador", "cifras": "cameo", "flash": "solo_datos"},
    "por_defecto": "cameo",
}
comprobar("presentador: sale en gancho, cuerpo y cierre", all(profesor_en("explicado", m, cfg) for m in ("gancho", "cuerpo", "cierre")))
comprobar("cameo: sale en gancho y cierre", profesor_en("cifras", "gancho", cfg) and profesor_en("cifras", "cierre", cfg))
comprobar("cameo: NO sale en el cuerpo", not profesor_en("cifras", "cuerpo", cfg))
comprobar("solo_datos: no sale nunca", not any(profesor_en("flash", m, cfg) for m in ("gancho", "cuerpo", "cierre")))
comprobar("tipo desconocido usa el formato por defecto", formato_para("inventado", cfg) == "cameo")
try:
    profesor_en("cifras", "intermedio", cfg)
    comprobar("momento inválido da error", False)
except ValueError:
    comprobar("momento inválido da error", True)
cfg_mala = {**cfg, "por_defecto": "no_existe"}
try:
    formato_para("inventado", cfg_mala)
    comprobar("formato de vídeo inexistente da error", False)
except ValueError:
    comprobar("formato de vídeo inexistente da error", True)

# --- 2. Con la regla real: todos los formatos de la agencia tienen un formato válido ---------------------------
real = cargar()
comprobar("la regla real solo usa formatos definidos", set(real["por_formato_de_post"].values()) <= set(real["formatos"]))
gen = Path(__file__).parent / "agencia_whalextreet" / "agency" / "generator.py"
if gen.exists():
    texto = gen.read_text(encoding="utf-8")
    inicio = texto.index("FORMATS = {")
    tipos = re.findall(r'^    "([a-z_]+)": \{', texto[inicio:], re.M)
    sin_regla = [t for t in tipos if t not in real["por_formato_de_post"]]
    comprobar(f"los {len(tipos)} tipos de post de la agencia tienen regla propia (sin regla: {sin_regla or 'ninguno'})", not sin_regla)
    sobrantes = [t for t in real["por_formato_de_post"] if t not in tipos]
    comprobar(f"la regla no nombra tipos que la agencia no tiene (sobran: {sobrantes or 'ninguno'})", not sobrantes)
else:
    print("AVISO: no encuentro generator.py de la agencia; se omite la comprobación contra los tipos reales")

print("\nTODO CORRECTO" if not fallos else f"\nFALLOS: {fallos}")
sys.exit(1 if fallos else 0)
