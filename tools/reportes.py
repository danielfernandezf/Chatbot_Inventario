import os
import json
from datetime import datetime, timedelta
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

from tools.utils import cargar_inventario
from tools.historial import cargar_historial

# ==========================================================
# RUTA CORRECTA DEL PDF (SE GUARDA EN LA RAÍZ DEL PROYECTO)
# ==========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Guardamos SIEMPRE el reporte en la carpeta principal del proyecto:
REPORTE_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "reporte_inventario.pdf"))


def generar_reporte(file_path: str, dias: int = 7) -> str:
    """
    Genera un PDF con:
    - productos con bajo stock
    - productos nuevos
    - movimientos de stock
    - cambios de precio
    """

    productos, _ = cargar_inventario(file_path)
    historial = cargar_historial()

    cutoff = datetime.now() - timedelta(days=dias)

    # --- Bajo stock ---
    bajo_stock = [p for p in productos if p["stock"] <= 5]

    # --- Productos nuevos ---
    nuevos = [
        h for h in historial
        if h["accion"] == "agregar_producto"
        and datetime.strptime(h["fecha"], "%Y-%m-%d %H:%M:%S") >= cutoff
    ]

    # --- Movimientos de stock ---
    movimientos_stock = [
        h for h in historial
        if h["accion"] == "actualizar_stock"
        and datetime.strptime(h["fecha"], "%Y-%m-%d %H:%M:%S") >= cutoff
    ]

    # --- Cambios de precio ---
    cambios_precio = [
        h for h in historial
        if h.get("campo") == "precio"
        and datetime.strptime(h["fecha"], "%Y-%m-%d %H:%M:%S") >= cutoff
    ]

    # =====================================================
    #   GENERAR PDF
    # =====================================================
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(REPORTE_FILE, pagesize=A4)
    elementos = []

    def titulo(t):
        elementos.append(Paragraph(f"<b>{t}</b>", styles["Heading2"]))
        elementos.append(Spacer(1, 12))

    def linea(txt):
        elementos.append(Paragraph(txt, styles["Normal"]))
        elementos.append(Spacer(1, 6))

    # Título principal
    elementos.append(Paragraph("<b>Reporte de Inventario</b>", styles["Title"]))
    elementos.append(Spacer(1, 24))

    titulo("Productos con bajo stock")
    if bajo_stock:
        for p in bajo_stock:
            linea(f"{p['id']} - {p['nombre']} → Stock: {p['stock']}")
    else:
        linea("Ninguno.")

    titulo(f"Productos nuevos (últimos {dias} días)")
    if nuevos:
        for n in nuevos:
            linea(f"{n['fecha']} - ID {n['producto_id']} agregado por {n['usuario']}")
    else:
        linea("No se agregaron productos.")

    titulo("Movimientos de stock")
    if movimientos_stock:
        for m in movimientos_stock:
            linea(f"{m['fecha']} - {m['usuario']} cambió ID {m['producto_id']} "
                  f"{m['valor_anterior']} → {m['valor_nuevo']}")
    else:
        linea("No hubo movimientos.")

    titulo("Cambios de precio")
    if cambios_precio:
        for c in cambios_precio:
            linea(f"{c['fecha']} - {c['usuario']} cambió precio de ID {c['producto_id']} "
                  f"{c['valor_anterior']} → {c['valor_nuevo']}")
    else:
        linea("No hubo cambios de precio.")

    doc.build(elementos)

    return f"Reporte generado correctamente.\nArchivo: {REPORTE_FILE}"
