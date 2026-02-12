ROLES = {
    "lector": {
        "leer_producto": True,
        "actualizar_producto": False,
        "actualizar_stock": False,
        "agregar_producto": False
    },
    "operador": {
        "leer_producto": True,
        "actualizar_producto": True,
        "actualizar_stock": True,
        "agregar_producto": False
    },
    "supervisor": {
        "leer_producto": True,
        "actualizar_producto": True,
        "actualizar_stock": True,
        "agregar_producto": True
    },
    "admin": {
        "leer_producto": True,
        "actualizar_producto": True,
        "actualizar_stock": True,
        "agregar_producto": True
    }
}
