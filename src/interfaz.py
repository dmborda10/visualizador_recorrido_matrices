import streamlit as st

def mostrar_titulo():

    st.markdown(
        """
        <h1 style='text-align: center;'>
            Visualizador de recorridos en matrices
        </h1>
        """,
        unsafe_allow_html = True
    )


def mostrar_procedimiento():

    st.markdown(
    """
    ### Procedimiento

    1. La matriz se encuentra almacenada en la variable `matriz`.

    2. Puede utilizar:
        - Ciclos `for`.
        - Ciclos `while`.
        - Variables.
        - `len`.
        - `range`.
        - `print`.

    3. Para colorear una posición simplemente acceda a ella:

        `matriz[i][j]`

    4. Donde:

        - `i` representa la fila.
        - `j` representa la columna.

    5. Cada vez que se accede a una posición de la matriz, esta se colorea automáticamente.

    6. El programa únicamente permite colorear posiciones individuales de la matriz.  No es posible colorear filas o columnas completas simultáneamente.

    7. Cada vez que modifique el código debe presionar 'Ejecutar recorrido' para ejecutarlo nuevamente.
    """
    )

    st.markdown("<br><br>", unsafe_allow_html = True)

    st.markdown("### A practicar")

