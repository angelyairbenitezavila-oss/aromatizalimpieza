import streamlit as st
import pymongo
import pandas as pd
import plotly.express as px

# conexion con los datos de las tiendas aromatiza
URI = "mongodb+srv://angelbenitez:12345@cluster01.olaysrr.mongodb.net/?appName=Cluster01"
cliente = pymongo.MongoClient(URI)

db = cliente["aromatiza"]
col_empleados = db["empleados"]
col_productos = db["productos"]
col_proveedores = db["proveedores"]

# configuracion de la pagina y variables para guardar el estado del pedido
st.set_page_config(page_title="Aromatiza - Sistema de Gestión", layout="wide")

if "flujo_pedido" not in st.session_state:
    st.session_state.flujo_pedido = "inicio"
if "proveedor_seleccionado" not in st.session_state:
    st.session_state.proveedor_seleccionado = None
if "carrito_pedido" not in st.session_state:
    st.session_state.carrito_pedido = {}

# menu de la izquierda con las tres barritas
st.sidebar.title("Navegación")
opcion_principal = st.sidebar.radio(
    "Selecciona una categoría:",
    ["🏠 Inicio / Bienvenida", "🛒 Gestión de Productos", "👥 Gestión de Empleados", "🚚 Gestión de Proveedores"]
)

# pantalla de inicio con datos del negocio
if opcion_principal == "🏠 Inicio / Bienvenida":
    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>AROMATIZA 🌿✨</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #757575;'>Productos de Limpieza de Alta Calidad</h3>", unsafe_allow_html=True)
    st.write("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📖 Nuestra Historia")
        st.write(
            "Aromatiza nació con el firme propósito de ofrecer a los hogares y negocios "
            "soluciones de limpieza accesibles y de la más alta calidad, distribuyendo una amplia "
            "variedad de productos a granel y jarcería desde la ciudad de Chilpancingo, Guerrero."
        )
    with col2:
        st.subheader("🎯 Misión y Visión")
        st.info("**Misión:** Proveer frescura, higiene y bienestar a nuestra comunidad a través de fórmulas efectivas y un servicio confiable de atención al cliente.")
        st.success("**Visión:** Consolidarnos como la distribuidora de productos de limpieza líder en la región, expandiendo nuestro catálogo de la mano de soluciones ecológicas y eficientes.")

# control de inventario de productos
elif opcion_principal == "🛒 Gestión de Productos":
    st.title("🛒 Centro de Control de Productos")
    tab_lista, tab_stock_bajo, tab_entrada = st.tabs(["📋 Lista General", "⚠️ Stock Bajo", "📥 Entrada de Mercancía"])

    productos = list(col_productos.find())
    df_prod = pd.DataFrame(productos) if productos else pd.DataFrame()
    if not df_prod.empty and '_id' in df_prod.columns:
        df_prod = df_prod.drop(columns=['_id'])

    with tab_lista:
        st.subheader("Inventario Completo")
        if not df_prod.empty:
            st.dataframe(df_prod, use_container_width=True)
        else:
            st.warning("No hay productos en la base de datos.")

    with tab_stock_bajo:
        st.subheader("Alerta de Inventario Crítico (< 30 Litros)")
        if not df_prod.empty:
            df_bajo = df_prod[df_prod['stock_litros'] < 30]
            if not df_bajo.empty:
                st.error(f"¡Atención! Hay {len(df_bajo)} productos que requieren reabastecimiento inmediato.")
                prod_elegido = st.selectbox("Selecciona un producto con stock bajo para ver su proveedor:", df_bajo['nombre'].unique())

                if prod_elegido:
                    info_prod = df_bajo[df_bajo['nombre'] == prod_elegido].iloc[0]
                    nom_proveedor = info_prod.get('proveedor', '')
                    datos_prov = col_proveedores.find_one({"empresa": nom_proveedor.lower().strip()}) or col_proveedores.find_one({"nombre": nom_proveedor})

                    st.markdown("### 🚚 Datos del Proveedor Ligado:")
                    if datos_prov:
                        st.info(
                            f"**Empresa/Distribuidor:** {datos_prov.get('nombre', 'No registrado')}\n\n"
                            f"**Contacto Directo:** {datos_prov.get('telefono', 'S/N')}\n\n"
                            f"**Correo Electrónico:** {datos_prov.get('correo', 'S/N')}\n\n"
                            f"**Ubicación:** {datos_prov.get('ciudad', 'S/N')}"
                        )
                    else:
                        st.warning(f"El producto está ligado a '{nom_proveedor}', pero no se encontraron sus datos en la colección de Proveedores.")
            else:
                st.success("¡Todo en orden! Todos los productos tienen suficiente stock.")

    with tab_entrada:
        st.subheader("Registrar Entrada de Litros")
        if not df_prod.empty:
            prod_update = st.selectbox("Selecciona el producto que llegó:", df_prod['nombre'].unique())
            litros_nuevos = st.number_input("Cantidad de litros recibidos:", min_value=1, step=1)

            if st.button("Actualizar Inventario en Base de Datos"):
                col_productos.update_one({"nombre": prod_update}, {"$inc": {"stock_litros": litros_nuevos}})
                st.success(f"¡Base de datos actualizada! Se sumaron {litros_nuevos}L a {prod_update}.")
                # st.rerun()

# datos de empleados y graficas de gastos/puestos
elif opcion_principal == "👥 Gestión de Empleados":
    st.title("👥 Panel de Gestión de Personal")
    tab_emp_lista, tab_graficas = st.tabs(["📋 Lista de Personal", "📊 Gráficas e Indicadores"])

    empleados = list(col_empleados.find())
    df_emp = pd.DataFrame(empleados) if empleados else pd.DataFrame()
    if not df_emp.empty and '_id' in df_emp.columns:
        df_emp = df_emp.drop(columns=['_id'])

    with tab_emp_lista:
        st.subheader("Empleados Registrados")
        if not df_emp.empty:
            st.dataframe(df_emp, use_container_width=True)
        else:
            st.warning("No hay empleados registrados.")

    with tab_graficas:
        st.subheader("Análisis Estadístico de la Nómina y Puestos")
        if not df_emp.empty:
            df_puestos = df_emp['puesto'].value_counts().reset_index()
            df_puestos.columns = ['Puesto', 'Cantidad']

            st.markdown("#### Enfoque de Personal por Puesto")
            fig_puestos = px.pie(df_puestos, values='Cantidad', names='Puesto', hole=0.4, title="Distribución de Empleados")
            st.plotly_chart(fig_puestos, use_container_width=True)

            st.markdown("**Desglose Numérico de Personal:**")
            for idx, row in df_puestos.iterrows():
                st.write(f"• **{row['Puesto']}:** {row['Cantidad']} empleado(s)")

            st.write("---")

            df_salarios = df_emp.groupby('puesto')['salario'].sum().reset_index()
            df_salarios.columns = ['Puesto', 'Gasto Total ($)']

            st.markdown("#### Inversión de Salarios por Categoría de Puesto")
            fig_salarios = px.bar(df_salarios, x='Puesto', y='Gasto Total ($)', color='Puesto', text_auto=True, title="Presupuesto Asignado por Puesto")
            st.plotly_chart(fig_salarios, use_container_width=True)

            total_nomina = df_salarios['Gasto Total ($)'].sum()
            st.markdown(f"### 💰 Gasto Total de Nómina Combinada: ${total_nomina:,.2f} MXN")
        else:
            st.warning("No hay datos suficientes para generar estadísticas.")

# directorio de proveedores y el creador de pedidos dinamico
elif opcion_principal == "🚚 Gestión de Proveedores":
    st.title("🚚 Módulo de Proveedores y Pedidos")
    tab_prov_lista, tab_pedido = st.tabs(["📋 Directorio de Proveedores", "📑 Generar Pedido Electrónico"])

    proveedores = list(col_proveedores.find())
    df_prov = pd.DataFrame(proveedores) if proveedores else pd.DataFrame()
    if not df_prov.empty and '_id' in df_prov.columns:
        df_prov = df_prov.drop(columns=['_id'])

    with tab_prov_lista:
        st.subheader("Lista de Contactos de Proveedores")
        if not df_prov.empty:
            st.dataframe(df_prov, use_container_width=True)
        else:
            st.warning("No hay proveedores registrados.")

    with tab_pedido:
        st.subheader("Generador de Hojas de Pedido")

        if st.session_state.flujo_pedido == "inicio":
            if st.button("✨ Hacer Pedido", key="btn_hacer_pedido", use_container_width=True):
                st.session_state.flujo_pedido = "seleccion_proveedor"
                st.rerun()

        elif st.session_state.flujo_pedido == "seleccion_proveedor":
            if not df_prov.empty:
                prov_opciones = df_prov['nombre'].unique()
                prov_elegido = st.selectbox("Selecciona el proveedor al que le harás el pedido:", prov_opciones)

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("Confirmar Proveedor"):
                        st.session_state.proveedor_seleccionado = prov_elegido
                        st.session_state.carrito_pedido = {}
                        st.session_state.flujo_pedido = "armando_pedido"
                        st.rerun()
                with col_b2:
                    if st.button("Cancelar"):
                        st.session_state.flujo_pedido = "inicio"
                        st.rerun()
            else:
                st.error("No tienes proveedores registrados.")

        elif st.session_state.flujo_pedido == "armando_pedido":
            st.markdown(f"### Requisición para: **{st.session_state.proveedor_seleccionado}**")

            col_t1, col_t2 = st.columns([3, 2])
            col_t1.markdown("**Nombre del Producto**")
            col_t2.markdown("**Cantidad**")
            st.write("---")

            for prod_name, cant in list(st.session_state.carrito_pedido.items()):
                col_p, col_c1, col_c2, col_c3 = st.columns([3, 0.5, 1, 0.5])
                col_p.write(f"🔹 {prod_name}")

                if col_c1.button("➖", key=f"sub_{prod_name}"):
                    if st.session_state.carrito_pedido[prod_name] > 1:
                        st.session_state.carrito_pedido[prod_name] -= 1
                    else:
                        del st.session_state.carrito_pedido[prod_name]
                    st.rerun()

                col_c2.markdown(f"<h4 style='text-align: center; margin:0;'>{cant} L</h4>", unsafe_allow_html=True)

                if col_c3.button("➕", key=f"add_{prod_name}"):
                    st.session_state.carrito_pedido[prod_name] += 1
                    st.rerun()

            prov_data = col_proveedores.find_one({"nombre": st.session_state.proveedor_seleccionado})
            empresa_tag = prov_data.get('empresa', '').lower().strip() if prov_data else ""

            productos_filtrados = list(col_productos.find({"proveedor": {"$regex": empresa_tag, "$options": "i"}}))
            if not productos_filtrados:
                productos_filtrados = list(col_productos.find())

            lista_nombres_filtrados = [p['nombre'] for p in productos_filtrados if p['nombre'] not in st.session_state.carrito_pedido]

            st.write("")
            if lista_nombres_filtrados:
                prod_a_agregar = st.selectbox("Elige un producto para añadir a la lista:", lista_nombres_filtrados)
                if st.button("➕ Agregar Producto", use_container_width=True):
                    st.session_state.carrito_pedido[prod_a_agregar] = 1
                    st.rerun()

            st.write("---")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                if st.button("📄 Generar Pedido", use_container_width=True):
                    if st.session_state.carrito_pedido:
                        st.session_state.flujo_pedido = "pedido_listo"
                        st.rerun()
                    else:
                        st.warning("Debes agregar al menos un producto.")
            with col_f2:
                if st.button("❌ Cancelar Pedido", use_container_width=True):
                    st.session_state.flujo_pedido = "inicio"
                    st.rerun()

        elif st.session_state.flujo_pedido == "pedido_listo":
            prov_info = col_proveedores.find_one({"nombre": st.session_state.proveedor_seleccionado})

            st.markdown("""
            <div style="border: 2px solid #4CAF50; padding: 20px; border-radius: 10px; background-color: #f9f9f9;">
                <h2 style="text-align: center; color: #4CAF50; margin-bottom: 0;">AROMATIZA 🌿</h2>
                <p style="text-align: center; color: #757575; font-size: 14px;">ORDEN DE COMPRA OFICIAL</p>
                <hr style="border: 1px solid #4CAF50;">
            """, unsafe_allow_html=True)

            st.markdown("### 🏢 Datos de Envío y Proveedor")
            if prov_info:
                st.write(f"**Empresa Proveedora:** {prov_info.get('nombre')}")
                st.write(f"**Contacto Comercial:** {prov_info.get('telefono')} | {prov_info.get('correo')}")
                st.write(f"**Ciudad Origen:** {prov_info.get('ciudad')}")

            st.markdown("<br>### 📋 Lista de Suministros Solicitados", unsafe_allow_html=True)

            items_pedido = []
            for item, cantidad in st.session_state.carrito_pedido.items():
                items_pedido.append({"Descripción de Producto": item, "Cantidad Requerida": f"{cantidad} Litros"})

            st.table(pd.DataFrame(items_pedido))

            st.markdown("""
                <br><br>
                <p style="text-align: center; font-size: 12px; color: #aaa;">Generado automáticamente por el Sistema Aromatiza.</p>
            </div>
            """, unsafe_allow_html=True)

            st.write("")
            if st.button("🔄 Crear una nueva orden"):
                st.session_state.flujo_pedido = "inicio"
                st.session_state.carrito_pedido = {}
                st.rerun()
