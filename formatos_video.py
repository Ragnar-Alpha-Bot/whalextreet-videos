"""Elige cuándo sale el profesor según el tipo de post. La regla vive en formatos_video.json.

    from formatos_video import formato_para, profesor_en
    formato_para("mito")            -> "presentador"
    profesor_en("post_numeros", "gancho")   -> True   (cameo: solo gancho y cierre)

Uso desde la terminal:  python formatos_video.py hilo_top
"""
import json
import sys
from pathlib import Path

RUTA = Path(__file__).with_name("formatos_video.json")
MOMENTOS = {"gancho", "cuerpo", "cierre"}


def cargar(ruta: Path = RUTA) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


def formato_para(formato_post: str, config: dict | None = None) -> str:
    """Formato de vídeo para un tipo de post; los desconocidos usan el valor por defecto."""
    cfg = config or cargar()
    f = cfg["por_formato_de_post"].get(formato_post, cfg["por_defecto"])
    if f not in cfg["formatos"]:
        raise ValueError(f"formato de vídeo desconocido: {f!r}")
    return f


def profesor_en(formato_post: str, momento: str, config: dict | None = None) -> bool:
    """¿Sale el profesor en este momento del vídeo? momento: 'gancho', 'cuerpo' o 'cierre'."""
    if momento not in MOMENTOS:
        raise ValueError(f"momento desconocido: {momento!r}")
    cfg = config or cargar()
    regla = cfg["formatos"][formato_para(formato_post, cfg)]["profesor"]
    if regla == "todo":
        return True
    if regla == "nunca":
        return False
    return momento in regla


if __name__ == "__main__":
    for tipo in sys.argv[1:] or ["mito"]:
        f = formato_para(tipo)
        momentos = [m for m in ("gancho", "cuerpo", "cierre") if profesor_en(tipo, m)]
        print(f"{tipo}: {f} (el profesor sale en: {', '.join(momentos) or 'ningún momento'})")
