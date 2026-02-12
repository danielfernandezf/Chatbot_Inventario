import pandas as pd
import json
from tools.utils import cargar_inventario, guardar_inventario
from tools.historial import registrar_evento


def validar_csv(df):
    errores = []

    columnas_obligatorias = ["id", "nombre", "precio", "stock", "categoria"]

    # Validar columnas faltantes
    faltan = [c for c in columnas_obligatorias if c not in df.columns]
    if faltan:
        errores.append(f"Faltan columnas obligatorias: {', '.join(faltan)}")

    # Validar filas
    for idx, row in df.iterrows():
        if row["id"] <= 0:
            errores.append(f"Fila {idx}: ID inválido ({row['id']})")

        if not isinstance(row["nombre"], str) or row["nombre"].strip() == "":
            errores.append(f"Fila {idx}: nombre vacío")

        if row["precio"] <= 0:
            errores.append(f"Fila {idx}: precio no válido ({row['precio']})")

        if row["stock"] < 0:
            errores.append(f"Fila {idx}: stock negativo ({row['stock']})")

        if not isinstance(row["categoria"], str) or row["categoria"].strip() == "":
            errores.append(f"Fila {idx}: categoría vacía")

    # IDs duplicados dentro del archivo
    duplicados = df[df["id"].duplicated()]
    if not duplicados.empty:
        errores.append(f"IDs duplicados en el archivo: {duplicados['id'].tolist()}")

    return errores


def aplicar_importacion(file_path_json, df, usuario="desconocido"):
    productos, data = cargar_inventario(file_path_json)

    nuevos = 0
    actualizados = 0

    for _, row in df.iterrows():

        existente = next((p for p in productos if p["id"] == int(row["id"])), None)

        if existente:
            # Actualizar valores
            for campo in ["nombre", "precio", "stock", "categoria"]:
                antes = existente[campo]
                despues = row[campo]

                if antes != despues:
                    registrar_evento(
                        usuario=usuario,
                        accion="importar_masivo",
                        producto_id=row["id"],
                        campo=campo,
                        valor_anterior=antes,
                        valor_nuevo=despues
                    )

                    existente[campo] = despues

            actualizados += 1

        else:
            # Crear producto nuevo
            nuevo = row.to_dict()
            productos.append(nuevo)

            for campo, valor in nuevo.items():
                registrar_evento(
                    usuario=usuario,
                    accion="importar_nuevo_producto",
                    producto_id=row["id"],
                    campo=campo,
                    valor_anterior=None,
                    valor_nuevo=valor
                )

            nuevos += 1

    data["productos"] = productos
    guardar_inventario(file_path_json, data)

    return f"Importación completada: {nuevos} nuevos, {actualizados} actualizados."
