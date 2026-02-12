import json
from typing import Tuple, Dict, Any, List

def cargar_inventario(file_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Carga el archivo JSON que contiene el inventario y devuelve:
    - una lista de productos
    - el JSON completo original

    El archivo debe tener esta estructura:

    {
        "productos": [
            {...},
            {...}
        ]
    }
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        productos = data.get("productos", [])
        return productos, data
    except FileNotFoundError:
        raise FileNotFoundError(f"El archivo '{file_path}' no existe.")
    except json.JSONDecodeError:
        raise ValueError(f"El archivo '{file_path}' no contiene JSON válido.")


def guardar_inventario(file_path: str, data: Dict[str, Any]) -> None:
    """
    Guarda el inventario modificado en el archivo JSON.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
