import streamlit as st
import time
from streamlit_ace import st_ace

from src.visualizador import MatrizVisual
from src.dibujo import dibujar_matriz
from src.matriz import inicializar_matriz
from src.interfaz import (
    mostrar_titulo,
    mostrar_procedimiento
)

st.set_page_config(
    page_title = "Visualizador de recorridos",
    layout = "wide"
)

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

    ejecutar = st.button("Ejecutar recorrido")

with col_grafica:

    st.subheader("Visualización")

    espacio = st.empty()

    fig_inicial = dibujar_matriz(matriz_base, [])
    espacio.pyplot(fig_inicial, use_container_width = False)

if ejecutar:

    matriz = MatrizVisual(matriz_base)

    entorno = {
        "matriz": matriz,
        "range": range,
        "len": len,
        "print": print
    }

    try:

        exec(codigo, entorno)

        recorrido = matriz.recorrido

        with col_grafica:

            mensaje = st.empty()

            visitadas = []

            for posicion in recorrido:

                visitadas.append(posicion)
                fig = dibujar_matriz(matriz_base, visitadas)
                espacio.pyplot(fig, use_container_width = False)
                time.sleep(tiempo_espera)

            mensaje.success("Recorrido finalizado")

            time.sleep(2)

            mensaje.empty()

    except Exception as e:

        st.error(f"Error en el código: {e}")