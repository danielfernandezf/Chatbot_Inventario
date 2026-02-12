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
from tools.historial import cargar_historial, registrar_evento
from tools.reportes import generar_reporte

load_dotenv()

# ==========================================================
#  RUTAS
# ==========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTARIO_FILE = os.path.join(BASE_DIR, "productos.json")


# ==========================================================
#  NUEVA FUNCIÓN: ACTUALIZAR SOLO PRECIO
# ==========================================================
def actualizar_precio(file_path: str, id: int, precio: float, usuario_actual: str):
    """
    Cambia solamente el precio de un producto.
    Registra correctamente el historial.
    """

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    productos = data["productos"]
    producto = next((p for p in productos if p["id"] == id), None)

    if not producto:
        return f"❌ El producto con ID {id} no existe."

    precio_anterior = producto["precio"]
    producto["precio"] = float(precio)

    # Guardar inventario actualizado
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Registrar historial
    registrar_evento(
        usuario=usuario_actual,
        accion="actualizar_precio",
        producto_id=id,
        campo="precio",
        valor_anterior=precio_anterior,
        valor_nuevo=float(precio)
    )

    return f"✔ Precio actualizado: {precio_anterior} → {precio}"


# ==========================================================
#  MAPEO DE FUNCIONES
# ==========================================================
TOOL_FUNCTIONS = {
    "leer_producto": leer_producto,
    "agregar_producto": agregar_producto,
    "actualizar_producto": actualizar_producto,
    "actualizar_stock": actualizar_stock,
    "actualizar_precio": actualizar_precio,  # NUEVO
    "generar_reporte": generar_reporte
}


# ==========================================================
#  PERMISOS POR ROL
# ==========================================================
PERMISOS = {
    "empleado": ["leer_producto"],

    "supervisor": [
        "leer_producto",
        "actualizar_stock",
        "actualizar_precio"   # PUEDE CAMBIAR PRECIOS
    ],

    "admin": [
        "leer_producto",
        "agregar_producto",
        "actualizar_producto",
        "actualizar_stock",
        "actualizar_precio",  # PUEDE CAMBIAR PRECIOS
        "generar_reporte"
    ]
}

def usuario_puede(rol, tool_name):
    return tool_name in PERMISOS.get(rol, [])


# ==========================================================
#  OPENAI CLIENT
# ==========================================================
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key=GITHUB_TOKEN,
    default_query={"api-version": "2024-08-01-preview"},
)


# ==========================================================
#  DETECTOR “producto 123”
# ==========================================================
def detectar_busqueda_producto(texto: str):
    txt = texto.lower().strip()
    patron = r"(producto|ver|mostrar|info|información|id)\s*(\d+)"
    match = re.search(patron, txt)
    if match:
        return match.group(2)
    return None


# ==========================================================
#  VALIDACIÓN DE ARGUMENTOS
# ==========================================================
def validar_argumentos(tool_name, args):
    errores = []

    # Validación general de ID
    if "id" in args:
        if not isinstance(args["id"], int) or args["id"] <= 0:
            errores.append("El ID debe ser un número mayor que cero.")

    # Validar precio
    if tool_name == "actualizar_precio":
        if args.get("precio") is None or args["precio"] <= 0:
            errores.append("El precio debe ser mayor que 0.")

    # Validar stock
    if tool_name == "actualizar_stock":
        if args.get("stock") is None or args["stock"] < 0:
            errores.append("El stock debe ser ≥ 0.")

    # Validaciones para agregar / actualizar producto
    if tool_name in ["agregar_producto", "actualizar_producto"]:
        if args.get("precio") is not None and args["precio"] <= 0:
            errores.append("El precio debe ser mayor a 0.")
        if args.get("stock") is not None and args["stock"] < 0:
            errores.append("El stock no puede ser negativo.")
        if tool_name == "agregar_producto":
            if not args.get("nombre"):
                errores.append("El nombre no puede estar vacío.")
            if not args.get("categoria"):
                errores.append("La categoría no puede estar vacía.")

    return errores


# ==========================================================
#  DEFINICIÓN DE TOOLS PARA EL MODELO
# ==========================================================
tools = [
    {
        "type": "function",
        "function": {
            "name": "leer_producto",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "agregar_producto",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "nombre": {"type": "string"},
                    "precio": {"type": "number"},
                    "stock": {"type": "integer"},
                    "categoria": {"type": "string"}
                },
                "required": ["id", "nombre", "precio", "stock", "categoria"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_producto",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "nombre": {"type": "string"},
                    "precio": {"type": "number"},
                    "stock": {"type": "integer"},
                    "categoria": {"type": "string"}
                },
                "required": ["id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_stock",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "stock": {"type": "integer"}
                },
                "required": ["id", "stock"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_precio",  # NUEVO TOOL
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "precio": {"type": "number"}
                },
                "required": ["id", "precio"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_reporte",
            "parameters": {
                "type": "object",
                "properties": {"dias": {"type": "integer"}},
                "required": []
            }
        }
    }
]


# ==========================================================
#  FUNCIÓN PRINCIPAL
# ==========================================================
def ejecutar_mensaje(mensaje_usuario: str, historial, rol_usuario="empleado", usuario_actual="desconocido"):

    # -------------------------------------------------------
    # 1️⃣ COMANDO LOCAL: VER HISTORIAL
    # -------------------------------------------------------
    if mensaje_usuario.lower().strip() in ["ver historial", "historial"]:
        eventos = cargar_historial()
        if not eventos:
            return {"tipo": "respuesta", "mensaje": "📭 El historial está vacío."}

        texto = "📘 Historial reciente:\n\n"
        for ev in eventos[-20:]:
            texto += (
                f"- {ev['fecha']} | {ev['usuario']} | {ev['accion']} | "
                f"Producto {ev['producto_id']} | {ev['campo']}: "
                f"{ev['valor_anterior']} → {ev['valor_nuevo']}\n"
            )
        return {"tipo": "respuesta", "mensaje": texto}

    # -------------------------------------------------------
    # 2️⃣ DETECTOR “producto 123”
    # -------------------------------------------------------
    producto_id = detectar_busqueda_producto(mensaje_usuario)

    if producto_id:
        resultado = leer_producto(INVENTARIO_FILE, producto_id)
        try:
            datos = json.loads(resultado)
        except:
            return {"tipo": "respuesta", "mensaje": resultado}

        if isinstance(datos, list) and len(datos) == 1:
            p = datos[0]
            msg = (
                f"📦 *Producto encontrado*\n"
                f"ID: {p['id']}\n"
                f"Nombre: {p['nombre']}\n"
                f"Precio: {p['precio']}\n"
                f"Categoría: {p['categoria']}\n"
                f"Stock: {p['stock']}"
            )
            if p["stock"] <= 5:
                msg += "\n⚠ Stock bajo."
            return {"tipo": "respuesta", "mensaje": msg}

        return {"tipo": "respuesta", "mensaje": resultado}

    # -------------------------------------------------------
    # 3️⃣ LLAMADA AL MODELO
    # -------------------------------------------------------
    messages = [{
        "role": "system",
        "content": (
            "Eres un agente de inventario.\n"
            "- Solo precio → actualizar_precio\n"
            "- Solo stock → actualizar_stock\n"
            "- Cambios múltiples → actualizar_producto\n"
            "- Nuevo → agregar_producto\n"
            "- Buscar → leer_producto\n"
            "- Reporte → generar_reporte\n"
            "Nunca inventes datos."
        )
    }]

    for rol, texto in historial[-6:]:
        messages.append({"role": rol, "content": texto})

    messages.append({"role": "user", "content": mensaje_usuario})

    response = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        tools=tools,
        response_format={"type": "text"},
        temperature=0.3,
    )

    msg = response.choices[0].message

    # -------------------------------------------------------
    # 4️⃣ TOOL CALL
    # -------------------------------------------------------
    if msg.tool_calls:
        for t in msg.tool_calls:

            nombre_tool = t.function.name
            args = json.loads(t.function.arguments or "{}")

            # --- PERMISOS ---
            if not usuario_puede(rol_usuario, nombre_tool):
                return {"tipo": "respuesta",
                        "mensaje": f"⛔ No tienes permisos para '{nombre_tool}'."}

            # --- VALIDACIONES ---
            if nombre_tool != "leer_producto":
                errores = validar_argumentos(nombre_tool, args)
                if errores:
                    return {"tipo": "respuesta",
                            "mensaje": "❌ Errores:\n- " + "\n- ".join(errores)}

            args["file_path"] = INVENTARIO_FILE

            # --- CONFIRMACIÓN ---
            if nombre_tool in [
                "agregar_producto",
                "actualizar_producto",
                "actualizar_stock",
                "actualizar_precio"
            ]:
                return {
                    "tipo": "accion_pendiente",
                    "tool": nombre_tool,
                    "args": args,
                    "usuario_actual": usuario_actual,
                    "mensaje": f"⚠ Vas a ejecutar '{nombre_tool}'. ¿Confirmar?"
                }

            # --- EJECUCIÓN DIRECTA ---
            resultado = TOOL_FUNCTIONS[nombre_tool](
                usuario_actual=usuario_actual,
                **args
            )
            return {"tipo": "respuesta", "mensaje": resultado}

    # Respuesta sin tool call
    return {"tipo": "respuesta", "mensaje": msg.content}