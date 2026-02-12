import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORIAL_FILE = os.path.join(BASE_DIR, "../historial.json")


def cargar_historial():
    if not os.path.exists(HISTORIAL_FILE):
        return []

    with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data.get("historial", [])
        except:
            return []


def guardar_historial(historial):
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump({"historial": historial}, f, indent=2, ensure_ascii=False)


def registrar_evento(usuario, accion, producto_id, campo, valor_anterior, valor_nuevo):
    historial = cargar_historial()

    evento = {
        "usuario": usuario,
        "accion": accion,
        "producto_id": producto_id,
        "campo": campo,
        "valor_anterior": valor_anterior,
        "valor_nuevo": valor_nuevo,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    historial.append(evento)
    guardar_historial(historial)

    return True
