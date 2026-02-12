"""Run this model in Python

> pip install openai
"""
import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

from tools.inventario import (
    leer_producto,
    agregar_producto,
    actualizar_producto,
    actualizar_stock
)

# Ruta absoluta del archivo de inventario
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTARIO_FILE = os.path.join(BASE_DIR, "productos.json")

# -------------------- TOKEN --------------------
load_dotenv()
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]  # Lee el token desde .env

client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key=GITHUB_TOKEN,
    default_query={"api-version": "2024-08-01-preview"},
)

# -------------------- MAPEADO DE TOOLS (TU ORIGINAL) --------------------

TOOL_FUNCTIONS = {
    "leer_producto": leer_producto,
    "agregar_producto": agregar_producto,
    "actualizar_producto": actualizar_producto,
    "actualizar_stock": actualizar_stock,
}

# ---------------------------------------------------------
# 🆕 PREPROCESADOR AVANZADO (AÑADIDO)
# ---------------------------------------------------------
def detectar_busqueda_producto(texto: str) -> str | None:
    """
    Detecta expresiones como:
    - "producto 127"
    - "informacion del producto 55"
    - "dame el producto 20"
    - "muéstrame el ID 30"
    - "info del 12"
    Devuelve el número detectado como string, o None si no hay coincidencia.
    """
    txt = texto.lower().strip()

    patron = r"(producto|informacion|información|info|ver|mostrar|muéstrame|muestrame|dato|datos|id)\s*(del|de|sobre)?\s*(producto|id)?\s*(\d+)"
    m = re.search(patron, txt)

    if m:
        return m.group(4)   # el número encontrado

    return None


# -------------------- VALIDACIÓN INTELIGENTE (TU ORIGINAL) --------------------

def validar_argumentos(tool_name, args):
    errores = []

    if "id" in args:
        if not isinstance(args["id"], int) or args["id"] <= 0:
            errores.append("El ID debe ser un número entero positivo.")

    if tool_name in ["agregar_producto", "actualizar_producto"]:

        if "precio" in args and args["precio"] is not None:
            if not isinstance(args["precio"], (int, float)) or args["precio"] <= 0:
                errores.append("El precio debe ser mayor que cero.")

        if "stock" in args and args["stock"] is not None:
            if not isinstance(args["stock"], int) or args["stock"] < 0:
                errores.append("El stock no puede ser negativo.")

        if tool_name == "agregar_producto":
            if "nombre" in args and (args["nombre"] is None or args["nombre"].strip() == ""):
                errores.append("El nombre no puede estar vacío.")

            if "categoria" in args and (args["categoria"] is None or args["categoria"].strip() == ""):
                errores.append("La categoría no puede estar vacía.")

    if tool_name == "actualizar_stock":
        if not isinstance(args.get("stock"), int) or args["stock"] < 0:
            errores.append("El stock debe ser un número entero mayor o igual a 0.")

    return errores


# -------------------- DEFINICIÓN DE TOOLS (TU ORIGINAL) --------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "leer_producto",
            "description": "Lee un archivo JSON de productos y devuelve coincidencias.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "query": {"type": "string"}
                },
                "required": ["file_path", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "agregar_producto",
            "description": "Agrega un nuevo producto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "id": {"type": "integer"},
                    "nombre": {"type": "string"},
                    "precio": {"type": "number"},
                    "stock": {"type": "integer"},
                    "categoria": {"type": "string"}
                },
                "required": ["file_path", "id", "nombre", "precio", "stock", "categoria"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_producto",
            "description": "Actualiza los detalles de un producto existente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "id": {"type": "integer"},
                    "nombre": {"type": "string"},
                    "precio": {"type": "number"},
                    "stock": {"type": "integer"},
                    "categoria": {"type": "string"}
                },
                "required": ["file_path", "id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_stock",
            "description": "Actualiza únicamente el stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "id": {"type": "integer"},
                    "stock": {"type": "integer"}
                },
                "required": ["file_path", "id", "stock"]
            }
        }
    }
]

response_format = {"type": "text"}


# -------------------- SYSTEM PROMPT (TU ORIGINAL) --------------------

messages = [
    {
        "role": "system",
        "content": (
            "Eres un agente de inventario estricto.\n"
            "Reglas:\n"
            "- Cambios de nombre, precio o categoría → actualizar_producto\n"
            "- Solo stock → actualizar_stock\n"
            "- Nuevo producto → agregar_producto\n"
            "- Búsqueda → leer_producto\n"
            "- No inventes datos ni muestres JSON\n"
            "- Pide: '¿Deseas continuar? (sí/no)' para acciones críticas"
        )
    }
]

accion_pendiente = None


# -------------------- LOOP PRINCIPAL (TU ORIGINAL + PREPROCESO) --------------------

print("Agente de Inventario iniciado.")
print("Escribe tu pregunta. Escribe 'salir' para terminar.\n")

while True:

    user_input = input("Tú: ").strip()

    if user_input.lower() in ["salir", "exit", "quit"]:
        print("Adiós!")
        break

    # ---------------------------------------------------
    # 1. ACCIÓN CRÍTICA PENDIENTE (TU LÓGICA ORIGINAL)
    # ---------------------------------------------------
    if accion_pendiente is not None:

        if user_input.lower() in ["si", "sí", "ok", "vale", "confirmo"]:
            tool_name = accion_pendiente["tool"]
            args = accion_pendiente["args"]

            result = TOOL_FUNCTIONS[tool_name](**args)

            accion_pendiente = None

            print("\n✔ Acción confirmada y ejecutada:")
            print(result)
            print()
            continue

        elif user_input.lower() in ["no", "cancelar", "n"]:
            print("❌ Operación cancelada.\n")
            accion_pendiente = None
            continue

        else:
            print("⚠️ Responde solo 'sí' o 'no'.")
            continue

    # ---------------------------------------------------
    # 2. 🆕 PREPROCESADOR LOCAL PARA CONSULTA DE PRODUCTO
    # ---------------------------------------------------

    producto_id = detectar_busqueda_producto(user_input)

    if producto_id:
        # Forzamos uso de leer_producto SIN pasar por el modelo
        resultado = leer_producto(INVENTARIO_FILE, producto_id)

        # Si leer_producto devuelve JSON en string, lo intentamos parsear
        datos = resultado
        if isinstance(resultado, str):
            try:
                datos = json.loads(resultado)
            except Exception:
                # No se puede parsear, devolvemos tal cual
                print("Respuesta:", resultado)
                continue

        # Si hay exactamente un producto, construimos respuesta + alerta
        if isinstance(datos, list) and len(datos) == 1:
            p = datos[0]

            nombre = p.get("nombre", "¿?")
            precio = p.get("precio", "¿?")
            categoria = p.get("categoria", "¿?")
            stock = p.get("stock", "¿?")
            pid = p.get("id", "¿?")

            UMBRAL = 5

            mensaje = (
                "Producto encontrado:\n"
                f"- ID: {pid}\n"
                f"- Nombre: {nombre}\n"
                f"- Precio: {precio}\n"
                f"- Categoría: {categoria}\n"
                f"- Stock: {stock}"
            )

            if isinstance(stock, int) and stock <= UMBRAL:
                mensaje += f"\n⚠ El stock está por debajo del mínimo sugerido ({UMBRAL} unidades)."

            print("Respuesta:", mensaje)
            continue

        # Si hay 0 o varios productos, devolvemos el resultado tal cual
        print("Respuesta:", resultado)
        continue

    # ---------------------------------------------------
    # 3. CONSULTA NORMAL AL MODELO (TU ORIGINAL)
    # ---------------------------------------------------

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        messages=messages[-6:],
        model="gpt-4o",
        tools=tools,
        response_format=response_format,
        temperature=1,
    )

    msg = response.choices[0].message

    # ---------------------------------------------------
    # 4. TOOL CALL (TU ORIGINAL)
    # ---------------------------------------------------

    if msg.tool_calls:
        for tool_call in msg.tool_calls:

            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            tool_args["file_path"] = INVENTARIO_FILE

            errores = validar_argumentos(tool_name, tool_args)
            if errores:
                print("\n⚠️ Error en los datos:")
                for err in errores:
                    print(" - " + err)
                print()
                continue

            # ACCIONES CRÍTICAS
            if tool_name in ["agregar_producto", "actualizar_producto", "actualizar_stock"]:
                accion_pendiente = {
                    "tool": tool_name,
                    "args": tool_args
                }
                print(f"\n⚠️ Vas a ejecutar: {tool_name}")
                print("¿Deseas continuar? (sí/no)")
                continue

            # ACCIONES NO CRÍTICAS
            result = TOOL_FUNCTIONS[tool_name](**tool_args)

            print("Respuesta:", result)
            continue

    else:
        print("Respuesta:", msg.content)
