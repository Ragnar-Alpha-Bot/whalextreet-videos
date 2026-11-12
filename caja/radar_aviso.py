"""Aviso por Telegram del radar semanal: lista los vídeos con 1 millón de visualizaciones o más que se han encontrado esta semana.

    python caja/radar_aviso.py [radar/candidatos/AAAA-MM-DD.json]      # sin argumento, el más reciente
    DRY_RUN=1 python caja/radar_aviso.py                              # lo muestra en pantalla sin enviar nada

Claves solo por variables de entorno (TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID); nunca se imprimen.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "caja"))
import radar_buscar as rb  # noqa: E402
import telegram_envio  # noqa: E402

PIE = "Dime cuáles quieres que adapte (ficha, datos reales y guion con nuestra marca). Recuerda: las visualizaciones no garantizan que funcione para nosotros."


def _texto(datos, maximo):
    c = datos["candidatos"]
    lineas = [f"📡 Radar semanal ({datos['fecha']}): {len(c)} vídeos nuevos con {rb.formato_vistas(datos['umbral'])} de visualizaciones o más (de {datos['revisados']} revisados).", ""]
    for i, v in enumerate(c[:maximo], 1):
        lineas += [f"{i}) {rb.formato_vistas(v['vistas'])} · {v['plataforma'].replace('_', ' ')} · {v['idioma'].upper()} · {v['tema']}", f"{v['titulo'][:110]}", v["url"], ""]
    if len(c) > maximo:
        lineas += [f"…y {len(c) - maximo} más en radar/candidatos/{datos['fecha']}.md", ""]
    return "\n".join(lineas + [PIE])


def mensaje(datos, maximo=10):
    c = datos["candidatos"]
    if not c:
        return f"📡 Radar semanal ({datos['fecha']}): esta semana no hay vídeos nuevos con {rb.formato_vistas(datos['umbral'])} de visualizaciones o más (se revisaron {datos['revisados']})."
    for n in range(min(maximo, len(c)), 0, -1):          # Telegram admite 4096 caracteres por mensaje: se recorta la lista si hace falta
        texto = _texto(datos, n)
        if len(texto) <= 3900:
            return texto
    return _texto(datos, 1)[:3900]


def main(argv):
    if argv:
        ruta = Path(argv[0])
    else:
        archivos = sorted((RAIZ / "radar" / "candidatos").glob("*.json"))
        if not archivos:
            print("No hay informes del radar todavía.")
            return 2
        ruta = archivos[-1]
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    telegram_envio.aviso(mensaje(datos))
    print(f"Aviso del radar enviado ({ruta.name}).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
