import streamlit as st
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()

from AgenteInventario import ejecutar_mensaje, TOOL_FUNCTIONS
from tools.reportes import REPORTE_FILE, generar_reporte


# ---------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------
st.set_page_config(
    page_title="Control de inventario",
    page_icon="📦",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTARIO_FILE = os.path.join(BASE_DIR, "productos.json")
USERS_FILE = os.path.join(BASE_DIR, "usuarios.json")
HISTORIAL_FILE = os.path.join(BASE_DIR, "historial.json")


# ---------------------------------------------------
# FUNCIONES: LOGIN Y USUARIOS
# ---------------------------------------------------
def cargar_usuarios():
    if not os.path.exists(USERS_FILE):
        st.error("No se encontró usuarios.json")
        st.stop()

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["usuarios"]


def autenticar(username, password):
    usuarios = cargar_usuarios()
    for u in usuarios:
        if u["username"] == username and u["password"] == password:
            return u
    return None


# ---------------------------------------------------
# FUNCIONES: HISTORIAL
# ---------------------------------------------------
def cargar_historial_seguro():
    if not os.path.exists(HISTORIAL_FILE):
        return []

    try:
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "historial" in data:
            return data["historial"]

        if isinstance(data, list):
            return data

        return []
    except:
        return []


# ---------------------------------------------------
# SESIÓN
# ---------------------------------------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.title("Acceso al sistema")

    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        auth = autenticar(user, pwd)
        if auth:
            st.session_state.usuario = auth
            st.rerun()
        else:
            st.error("Credenciales incorrectas.")

    st.stop()


# ---------------------------------------------------
# CSS CHAT
# ---------------------------------------------------
st.markdown(
    """
<style>
body {
    background-color: #F5F5F5;
}
.chat-container {
    max-width: 700px;
    margin: auto;
}
.user-bubble {
    background-color: #CDE8C3;
    color: black !important;
    padding: 12px 18px;
    border-radius: 12px;
    margin-bottom: 8px;
    width: fit-content;
    max-width: 80%;
}
.bot-bubble {
    background-color: #F1F1F1;
    color: black !important;
    padding: 12px 18px;
    border-radius: 12px;
    margin-bottom: 8px;
    width: fit-content;
    max-width: 80%;
}
</style>
""",
    unsafe_allow_html=True
)


# ---------------------------------------------------
# SESIÓN MENSAJES
# ---------------------------------------------------
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

if "accion_pendiente" not in st.session_state:
    st.session_state.accion_pendiente = None


# ---------------------------------------------------
# PESTAÑAS
# ---------------------------------------------------
tab_chat, tab_inventario, tab_dashboard, tab_historial = st.tabs(
    ["Chat", "Inventario", "Dashboard", "Historial"]
)


# ======================================================
# TAB 1: CHAT
# ======================================================
with tab_chat:

    st.subheader(f"Sesión iniciada como: {st.session_state.usuario['rol'].upper()}")

    chat_container = st.container()
    chat_container.markdown("<div class='chat-container'>", unsafe_allow_html=True)

    for rol, texto in st.session_state.mensajes:
        bubble = "user-bubble" if rol == "user" else "bot-bubble"
        label = "Tú" if rol == "user" else "Asistente"

        chat_container.markdown(
            f"<div class='{bubble}'><b>{label}:</b> {texto}</div>",
            unsafe_allow_html=True
        )

    chat_container.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------
    # BOTONES RÁPIDOS
    # ------------------------------
    st.markdown("### Acciones rápidas")
    colA, colB, colC = st.columns(3)

    if colA.button("Consultar producto"):
        consulta = "Consultar producto"
        st.session_state.mensajes.append(("user", consulta))
        st.session_state.mensajes.append(("assistant",
            ejecutar_mensaje(
                consulta,
                st.session_state.mensajes,
                rol_usuario=st.session_state.usuario["rol"],
                usuario_actual=st.session_state.usuario["username"]
            )["mensaje"]
        ))
        st.rerun()

    if colB.button("Actualizar stock"):
        upd = "Actualizar stock"
        st.session_state.mensajes.append(("user", upd))
        st.session_state.mensajes.append(("assistant",
            ejecutar_mensaje(
                upd,
                st.session_state.mensajes,
                rol_usuario=st.session_state.usuario["rol"],
                usuario_actual=st.session_state.usuario["username"]
            )["mensaje"]
        ))
        st.rerun()

    if colC.button("Nuevo producto"):
        nuevo = "Nuevo producto"
        st.session_state.mensajes.append(("user", nuevo))
        st.session_state.mensajes.append(("assistant",
            ejecutar_mensaje(
                nuevo,
                st.session_state.mensajes,
                rol_usuario=st.session_state.usuario["rol"],
                usuario_actual=st.session_state.usuario["username"]
            )["mensaje"]
        ))
        st.rerun()

    # ------------------------------
    # ACCIÓN PENDIENTE
    # ------------------------------
    if st.session_state.accion_pendiente:

        acc = st.session_state.accion_pendiente
        st.warning(acc["mensaje"])

        col1, col2 = st.columns(2)

        if col1.button("Confirmar"):
            tool = acc["tool"]
            args = acc["args"]
            usuario_actual = acc["usuario_actual"]

            resultado = TOOL_FUNCTIONS[tool](
                usuario_actual=usuario_actual,
                **args
            )

            st.session_state.mensajes.append(("assistant", resultado))
            st.session_state.accion_pendiente = None
            st.rerun()

        if col2.button("Cancelar"):
            st.session_state.mensajes.append(("assistant", "Operación cancelada."))
            st.session_state.accion_pendiente = None
            st.rerun()

    # ------------------------------
    # CHAT NORMAL
    # ------------------------------
    user_input = st.chat_input("Escribe tu consulta…")

    if user_input:
        st.session_state.mensajes.append(("user", user_input))
        respuesta = ejecutar_mensaje(
            user_input,
            st.session_state.mensajes,
            rol_usuario=st.session_state.usuario["rol"],
            usuario_actual=st.session_state.usuario["username"]
        )

        st.session_state.mensajes.append(("assistant", respuesta["mensaje"]))

        if respuesta["tipo"] == "accion_pendiente":
            st.session_state.accion_pendiente = respuesta

        st.rerun()


# ======================================================
# TAB 2: INVENTARIO
# ======================================================
with tab_inventario:

    st.header("Inventario")

    with open(INVENTARIO_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    productos = raw["productos"]
    df = pd.DataFrame(productos)

    # -------------------------------
    # 📄 REPORTE PDF
    # -------------------------------
    st.subheader("Reporte en PDF")

    if st.session_state.usuario["rol"] == "admin":
        if st.button("📄 Generar reporte PDF"):
            generar_reporte(INVENTARIO_FILE)
            st.success("Reporte generado correctamente.")

        if os.path.exists(REPORTE_FILE):
            with open(REPORTE_FILE, "rb") as pdf:
                st.download_button(
                    "⬇ Descargar reporte PDF",
                    data=pdf,
                    file_name="reporte_inventario.pdf",
                    mime="application/pdf"
                )
    else:
        st.info("Solo los administradores pueden generar reportes.")

    st.divider()

    # -------------------------------
    # TABLA DE INVENTARIO
    # -------------------------------
    if df.empty:
        st.info("Inventario vacío.")
    else:
        # 🔍 BUSCADOR
        busqueda = st.text_input("Buscar por nombre, categoría o ID", key="busqueda_inv")

        if busqueda:
            df = df[df.apply(
                lambda r: r.astype(str).str.contains(busqueda, case=False).any(),
                axis=1
            )]

        # 🏷 FILTRO POR CATEGORÍA
        categorias = ["Todas"] + sorted(df["categoria"].unique())
        cat = st.selectbox("Filtrar por categoría", categorias, key="cat_inv")

        if cat != "Todas":
            df = df[df["categoria"] == cat]

        # 🔼 ORDENAR POR STOCK
        ordenar = st.checkbox("Ordenar por stock ascendente", key="ordenar_inv")
        if ordenar:
            df = df.sort_values(by="stock", ascending=True)

        # 🔥 COLOREAR STOCK BAJO
        def estilo_stock(v):
            try:
                if int(v) <= 5:
                    return "color:red; font-weight:bold;"
            except:
                pass
            return ""

        st.dataframe(df.style.map(estilo_stock, subset=["stock"]), width="stretch")

        # ---------------------------------
        # 🔼 ACTUALIZAR PRECIO (SUPERVISOR/ADMIN)
        # ---------------------------------
        st.subheader("Actualizar precio de un producto")

        rol = st.session_state.usuario["rol"]

        if rol in ["supervisor", "admin"]:

            with st.form("form_precio"):
                c1, c2 = st.columns(2)
                with c1:
                    idp = st.number_input("ID del producto", min_value=1, step=1)
                with c2:
                    pr = st.number_input("Nuevo precio (€)", min_value=0.01, step=0.01)

                enviar = st.form_submit_button("Actualizar precio")

            if enviar:
                try:
                    resultado = TOOL_FUNCTIONS["actualizar_precio"](
                        file_path=INVENTARIO_FILE,
                        id=int(idp),
                        precio=float(pr),
                        usuario_actual=st.session_state.usuario["username"]
                    )
                    st.success(resultado)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar precio: {e}")

        else:
            st.info("Solo supervisores y administradores pueden actualizar precios.")


# ======================================================
# TAB 3: DASHBOARD + BOTÓN DE DESCARGA PDF
# ======================================================
with tab_dashboard:

    st.header("Dashboard")

    # Cargar inventario
    with open(INVENTARIO_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    productos = raw["productos"] if isinstance(raw, dict) else raw
    df = pd.DataFrame(productos)

    # ============================
    # MÉTRICAS SUPERIORES
    # ============================
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Stock total", int(df["stock"].sum()))
    col2.metric("Categorías", df["categoria"].nunique())
    col3.metric("Productos", df.shape[0])
    col4.metric("Críticos (≤5)", df[df["stock"] <= 5].shape[0])

    # ============================
    # GRÁFICO: Stock por categoría
    # ============================
    st.subheader("Stock por categoría")
    st.bar_chart(df.groupby("categoria")["stock"].sum())

    # ============================
    # TABLA: Productos con menos stock
    # ============================
    st.subheader("Menos stock")
    st.dataframe(df.sort_values(by="stock").head(10))

    # ============================
    # TABLA: Productos con más stock
    # ============================
    st.subheader("Más stock")
    st.dataframe(df.sort_values(by="stock", ascending=False).head(10))

    # ============================
    # GRÁFICO: Tendencia general por nombre
    # ============================
    st.subheader("Tendencia")
    try:
        st.line_chart(df.set_index("nombre")["stock"])
    except:
        st.info("No se pudo generar la gráfica de tendencia (duplicados o datos inválidos).")

    # ============================
    # DESCARGA DE REPORTE PDF
    # ============================
    st.subheader("📄 Descargar reporte del inventario")

    if os.path.exists(REPORTE_FILE):
        with open(REPORTE_FILE, "rb") as f_pdf:
            st.download_button(
                label="⬇️ Descargar reporte PDF",
                data=f_pdf,
                file_name="reporte_inventario.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Aún no se ha generado ningún reporte.")


# ======================================================
# TAB 4: HISTORIAL
# ======================================================
with tab_historial:

    st.header("Historial de Cambios")

    historial = cargar_historial_seguro()

    if not historial:
        st.info("Aún no hay eventos registrados.")
    else:
        hist_df = pd.DataFrame(historial)

        columnas_necesarias = {
            "usuario", "accion", "producto_id", "campo",
            "valor_anterior", "valor_nuevo", "fecha"
        }

        faltan = columnas_necesarias - set(hist_df.columns)

        if faltan:
            st.error(f"Faltan columnas: {faltan}")
            st.write(hist_df)
        else:
            st.subheader("Filtros del historial")

            col1, col2, col3 = st.columns(3)

            # ------------------------
            # FILTRO POR USUARIO
            # ------------------------
            with col1:
                usuario_sel = st.selectbox(
                    "Usuario",
                    ["Todos"] + sorted(hist_df["usuario"].unique())
                )

            # ------------------------
            # FILTRO POR ACCIÓN
            # ------------------------
            with col2:
                accion_sel = st.selectbox(
                    "Acción",
                    ["Todas"] + sorted(hist_df["accion"].unique())
                )

            # ------------------------
            # FILTRO POR CAMPO
            # ------------------------
            with col3:
                campo_sel = st.selectbox(
                    "Campo modificado",
                    ["Todos"] + sorted(hist_df["campo"].unique())
                )

            col4, col5 = st.columns(2)

            # ------------------------
            # FILTRO POR ID PRODUCTO
            # ------------------------
            with col4:
                ids = ["Todos"] + sorted(map(str, hist_df["producto_id"].unique()))
                id_sel = st.selectbox("ID Producto", ids)

            # ------------------------
            # BÚSQUEDA DE TEXTO
            # ------------------------
            with col5:
                texto_busqueda = st.text_input("Buscar texto en cualquier campo")

            # ------------------------
            # APLICAR FILTROS
            # ------------------------
            df_filtrado = hist_df.copy()

            if usuario_sel != "Todos":
                df_filtrado = df_filtrado[df_filtrado["usuario"] == usuario_sel]

            if accion_sel != "Todas":
                df_filtrado = df_filtrado[df_filtrado["accion"] == accion_sel]

            if campo_sel != "Todos":
                df_filtrado = df_filtrado[df_filtrado["campo"] == campo_sel]

            if id_sel != "Todos":
                df_filtrado = df_filtrado[df_filtrado["producto_id"] == int(id_sel)]

            if texto_busqueda:
                df_filtrado = df_filtrado[
                    df_filtrado.apply(
                        lambda r: texto_busqueda.lower() in r.astype(str).str.lower().to_string(),
                        axis=1
                    )
                ]

            # ------------------------
            # MOSTRAR RESULTADO
            # ------------------------
            st.subheader("Resultados del historial")
            st.dataframe(
                df_filtrado.sort_values(by="fecha", ascending=False),
                use_container_width=True
            )


#python -m streamlit run interfaz.py