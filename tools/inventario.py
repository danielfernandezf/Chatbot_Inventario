import json
from typing import Optional

from tools.utils import cargar_inventario, guardar_inventario
from tools.historial import registrar_evento


# ==========================================================
#   TOOL: LEER PRODUCTO
# ==========================================================

def leer_producto(file_path: str, query: str, usuario_actual: str = None) -> str:
    """
    Busca coincidencias por ID exacto o por nombre/categoría si no es un número.
    (No registra historial porque solo es consulta)
    """
    try:
        productos, _ = cargar_inventario(file_path)

        # Buscar por ID
        if query.isdigit():
            pid = int(query)
            resultados = [p for p in productos if p.get("id") == pid]

            if not resultados:
                return f"No se encontró el producto con ID {pid}."

            return json.dumps(resultados, ensure_ascii=False, indent=2)

        # Buscar por nombre o categoría
        query_lower = query.lower()
        resultados = [
            p for p in productos
            if query_lower in p.get("nombre", "").lower()
            or query_lower in p.get("categoria", "").lower()
        ]

        if not resultados:
            return f"No se encontraron coincidencias con '{query}'."

        return json.dumps(resultados, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"Error al leer productos: {e}"


# ==========================================================
#   TOOL: AGREGAR PRODUCTO
# ==========================================================

def agregar_producto(
    file_path: str,
    id: int,
    nombre: str,
    precio: float,
    stock: int,
    categoria: str,
    usuario_actual: str = "desconocido",
) -> str:

    try:
        productos, data = cargar_inventario(file_path)

        # Verificar ID duplicado
        if any(int(p.get("id")) == int(id) for p in productos):
            return f"Error: ya existe un producto con ID {id}."

        nuevo = {
            "id": int(id),
            "nombre": nombre,
            "precio": float(precio),
            "stock": int(stock),
            "categoria": categoria,
        }

        productos.append(nuevo)
        data["productos"] = productos
        guardar_inventario(file_path, data)

        # Registrar todos los campos agregados
        for campo, valor in nuevo.items():
            registrar_evento(
                usuario=usuario_actual,
                accion="agregar_producto",
                producto_id=id,
                campo=campo,
                valor_anterior=None,
                valor_nuevo=valor
            )

        return (
            "Producto agregado correctamente:\n" +
            json.dumps(nuevo, ensure_ascii=False, indent=2)
        )

    except Exception as e:
        return f"Error al agregar producto: {e}"


# ==========================================================
#   TOOL: ACTUALIZAR PRODUCTO (CAMBIOS GENERALES)
# ==========================================================

def actualizar_producto(
    file_path: str,
    id: int,
    nombre: Optional[str] = None,
    precio: Optional[float] = None,
    stock: Optional[int] = None,
    categoria: Optional[str] = None,
    usuario_actual: str = "desconocido",
) -> str:

    try:
        productos, data = cargar_inventario(file_path)

        producto = next((p for p in productos if int(p.get("id")) == int(id)), None)
        if not producto:
            return f"No existe ningún producto con ID {id}."

        cambios = {}

        # Nombre
        if nombre is not None and nombre != producto["nombre"]:
            cambios["nombre"] = {"antes": producto["nombre"], "después": nombre}
            registrar_evento(usuario_actual, "actualizar_producto", id, "nombre",
                             producto["nombre"], nombre)
            producto["nombre"] = nombre

        # Precio
        if precio is not None and precio != producto["precio"]:
            cambios["precio"] = {"antes": producto["precio"], "después": float(precio)}
            registrar_evento(usuario_actual, "actualizar_producto", id, "precio",
                             producto["precio"], float(precio))
            producto["precio"] = float(precio)

        # Stock
        if stock is not None and stock != producto["stock"]:
            cambios["stock"] = {"antes": producto["stock"], "después": int(stock)}
            registrar_evento(usuario_actual, "actualizar_producto", id, "stock",
                             producto["stock"], int(stock))
            producto["stock"] = int(stock)

        # Categoría
        if categoria is not None and categoria != producto["categoria"]:
            cambios["categoria"] = {"antes": producto["categoria"], "después": categoria}
            registrar_evento(usuario_actual, "actualizar_producto", id, "categoria",
                             producto["categoria"], categoria)
            producto["categoria"] = categoria

        if not cambios:
            return f"No se especificaron cambios para el producto {id}."

        guardar_inventario(file_path, data)

        return (
            f"Producto {id} actualizado correctamente:\n" +
            json.dumps(cambios, ensure_ascii=False, indent=2)
        )

    except Exception as e:
        return f"Error al actualizar producto: {e}"


# ==========================================================
#   TOOL: ACTUALIZAR STOCK
# ==========================================================

def actualizar_stock(
    file_path: str,
    id: int,
    stock: int,
    usuario_actual: str = "desconocido",
) -> str:

    try:
        productos, data = cargar_inventario(file_path)

        producto = next((p for p in productos if int(p.get("id")) == int(id)), None)
        if not producto:
            return f"No existe ningún producto con ID {id}."

        stock_anterior = producto["stock"]
        producto["stock"] = int(stock)

        guardar_inventario(file_path, data)

        registrar_evento(
            usuario=usuario_actual,
            accion="actualizar_stock",
            producto_id=id,
            campo="stock",
            valor_anterior=stock_anterior,
            valor_nuevo=int(stock)
        )

        return f"Stock del producto {id} actualizado de {stock_anterior} a {stock}."

    except Exception as e:
        return f"Error al actualizar stock: {e}"


# ==========================================================
#   TOOL NUEVO: ACTUALIZAR SOLO PRECIO
# ==========================================================

def actualizar_precio(
    file_path: str,
    id: int,
    precio: float,
    usuario_actual: str = "desconocido"
) -> str:

    try:
        productos, data = cargar_inventario(file_path)

        producto = next((p for p in productos if int(p.get("id")) == int(id)), None)
        if not producto:
            return f"No existe ningún producto con ID {id}."

        precio_anterior = producto["precio"]
        producto["precio"] = float(precio)

        guardar_inventario(file_path, data)

        registrar_evento(
            usuario=usuario_actual,
            accion="actualizar_precio",
            producto_id=id,
            campo="precio",
            valor_anterior=precio_anterior,
            valor_nuevo=float(precio)
        )

        return f"Precio del producto {id} actualizado de {precio_anterior}€ a {precio}€."

    except Exception as e:
        return f"Error al actualizar el precio: {e}"
