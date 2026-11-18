import streamlit as st
import time
from streamlit_ace import st_ace

from src.ejecutor import ejecutar_codigo
from src.dibujo import matriz_a_png
from src.matriz import inicializar_matriz
from src.interfaz import (
    mostrar_titulo,
    mostrar_procedimiento
)

st.set_page_config(
    page_title = "Visualizador de recorridos",
    layout = "wide"
)

@st.cache_data(max_entries = 512, show_spinner = False)
def imagen_matriz(matriz, visitadas):
    """Imagen PNG de la matriz. Se comparte (caché) entre todos los usuarios."""
    return matriz_a_png(matriz, visitadas)


mostrar_titulo()

mostrar_procedimiento()

st.sidebar.header("Configuración de la matriz")

es_cuadrada = st.sidebar.checkbox(
    "Matriz cuadrada",
    value = True
    )

filas = st.sidebar.number_input(
    "Número de filas",
    min_value = 1,
    max_value = 10,
    value = 4
    )

if es_cuadrada:

    columnas = filas
    st.sidebar.write(f"Columnas: {columnas}")

else:

    columnas = st.sidebar.number_input(
        "Número de columnas",
        min_value=1,
        max_value=15,
        value=4
    )


tiempo_espera = st.sidebar.number_input(
    "Tiempo de espera animación (s)",
    min_value = 0.1,
    max_value = 1.0,
    value = 0.3, 
    step = 0.1
)

matriz_base = inicializar_matriz(
    es_cuadrada,
    filas,
    columnas
)

col_codigo, col_grafica = st.columns([1.2, 1])

with col_codigo:

    st.subheader("Código del estudiante")

    # El formulario evita que cada tecla vuelva a ejecutar toda la aplicación:
    # el código solo se envía al servidor al presionar "Ejecutar recorrido".
    with st.form("form_codigo", border = False):

        codigo = st_ace(
            value="""for i in range(len(matriz)):
    for j in range(len(matriz[i])):
        matriz[i][j]""",
            language = "python",
            theme = "monokai",
            height = 300,
            tab_size = 4,
            keybinding = "vscode",
            font_size = 15,
            auto_update = True
        )

        ejecutar = st.form_submit_button("Ejecutar recorrido")

with col_grafica:

    st.subheader("Visualización")

    espacio = st.empty()

    espacio.image(
        imagen_matriz(matriz_base, []),
        width = "content",
        alt = "Matriz sin posiciones visitadas"
    )

if ejecutar:

    with col_grafica:

        with st.spinner("Ejecutando..."):
            resultado = ejecutar_codigo(codigo, filas, columnas)

        if resultado.salida:
            st.code(resultado.salida, language = None)

        if not resultado.ok:

            st.error(f"Error en el código: {resultado.error}")

        else:

            mensaje = st.empty()

            visitadas = []

            for posicion in resultado.recorrido:

                visitadas.append(posicion)
                espacio.image(
                    imagen_matriz(matriz_base, visitadas),
                    width = "content",
                    alt = f"Matriz con {len(visitadas)} posiciones visitadas"
                )

                time.sleep(tiempo_espera)

            mensaje.success("Recorrido finalizado")

            time.sleep(2)

            mensaje.empty()
