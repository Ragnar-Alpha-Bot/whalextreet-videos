"""Pautas de gancho de la marca: máx. 15 palabras, sin aperturas genéricas, uno de los 5 ángulos."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "caja"))
import guion  # noqa: E402
import storyboard_ia  # noqa: E402

BASE = {"tema": "alerta", "escenas": [
    {"tipo": "gancho", "angulo": "error", "voz": "El error que arruina tu cartera sin que lo notes.", "texto": "EL ERROR QUE ARRUINA TU CARTERA", "resalte": "ERROR"},
    {"tipo": "titulo", "titulo": "Comprar por impulso", "voz": "Compras cuando todo sube y vendes cuando todo cae."},
    {"tipo": "cta"}]}


def con_gancho(**cambios):
    sb = copy.deepcopy(BASE)
    sb["escenas"][0].update(cambios)
    return sb


def rechaza(sb, trozo):
    try:
        guion.validar(sb)
    except ValueError as e:
        assert trozo in str(e), str(e)
        return
    raise AssertionError("debía rechazarse: " + trozo)


def test_gancho_valido_pasa():
    guion.validar(copy.deepcopy(BASE))


def test_mas_de_15_palabras_se_rechaza():
    rechaza(con_gancho(voz="Casi nadie sabe esto pero cambia por completo la forma de ver tus ahorros hoy mismo"), "palabras")


def test_aperturas_prohibidas_se_rechazan():
    for mal in ("¿Sabías que el mercado miente?", "Hola, hoy hablamos de bolsa", "En este vídeo te enseño a ahorrar", "Hoy vamos a hablar de ETFs"):
        rechaza(con_gancho(voz=mal), "no puede empezar")


def test_angulo_desconocido_se_rechaza():
    rechaza(con_gancho(angulo="clickbait"), "angulo")


def test_el_prompt_de_gemini_lleva_las_pautas():
    for t in ("MÁXIMO 15 palabras", "«error»", "«verdad»", "«secreto»", "«urgencia»", "«pregunta»", "TRANSICIÓN", "CLICKBAIT CON FUNDAMENTO", "¿Sabías que…?"):
        assert t in storyboard_ia.SISTEMA, t




def test_la_biblioteca_de_ganchos_va_en_el_prompt_sin_palabras_prohibidas():
    from ganchos import BIBLIOTECA
    assert BIBLIOTECA in storyboard_ia.SISTEMA and "OBLIGATORIO y BRUTAL" in storyboard_ia.SISTEMA
    assert len([l for l in BIBLIOTECA.splitlines() if l[:3].strip().rstrip(".").isdigit()]) == 55
    for w in guion.PROHIBIDAS:
        assert w not in guion.norm_espacios(storyboard_ia.SISTEMA), w


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
