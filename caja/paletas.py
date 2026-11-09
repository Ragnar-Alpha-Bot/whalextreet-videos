"""Paletas por tema. La marca (ballena, fondo azul marino, tipografías, cierre) es fija; solo cambia el color de acento."""

BASE = {"bg": "#0B1020", "surface": "#121A2B", "raised": "#1B263B", "text": "#F4F7FC", "muted": "#B2BED1", "border": "#35435B",
        "up": "#6EE7A8", "down": "#FF7A7A", "warn": "#F2C879"}

TEMAS = {
    "cripto":    {"acc": "#67D4E8", "acc2": "#A5B4FC", "resalte": "#F2C879", "etiqueta": "CRIPTO"},
    "bolsa":     {"acc": "#6EE7A8", "acc2": "#67D4E8", "resalte": "#F2C879", "etiqueta": "BOLSA"},
    "alerta":    {"acc": "#FF7A7A", "acc2": "#F2C879", "resalte": "#67D4E8", "etiqueta": "ALERTA"},
    "macro":     {"acc": "#F2C879", "acc2": "#A5B4FC", "resalte": "#67D4E8", "etiqueta": "MACRO"},
    "educativo": {"acc": "#A5B4FC", "acc2": "#67D4E8", "resalte": "#F2C879", "etiqueta": "APRENDE"},
}


def paleta(tema):
    if tema not in TEMAS:
        raise ValueError(f"tema desconocido: {tema!r}. Disponibles: {sorted(TEMAS)}")
    return {**BASE, **TEMAS[tema]}


def rgb(hexa, alpha):
    h = hexa.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"
