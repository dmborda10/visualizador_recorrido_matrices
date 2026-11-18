import io

from matplotlib.figure import Figure
from matplotlib.patches import Rectangle


def dibujar_matriz(matriz: list, visitadas: list) -> Figure:
    """
    Dibuja la matriz y colorea las posiciones visitadas.

    Usa la API orientada a objetos de matplotlib (Figure) y NO pyplot:
    pyplot guarda estado global compartido entre todos los usuarios y no es
    seguro cuando varios usuarios dibujan a la vez.
    """

    filas = len(matriz)
    columnas = len(matriz[0])

    fig = Figure(figsize = (3.5, 3.5))
    ax = fig.subplots()

    for i in range(filas):
        for j in range(columnas):
            cuadrado = Rectangle(
                (j - 0.5, filas - 1 - i - 0.5),
                width = 1,
                height = 1,
                fill = False
                )
            ax.add_patch(cuadrado)

            ax.text(
                j,
                filas - 1 - i,
                str(matriz[i][j]),
                ha = "center",
                va = "center"
            )

    for i, j in visitadas:
        cuadrado = Rectangle(
                (j - 0.5, filas - 1 - i - 0.5),
                width = 1,
                height = 1,
                alpha = 0.2,
                fill = True,
                facecolor = "#ff00ff"
                )

        ax.add_patch(cuadrado)

    ax.set_xlim(-0.5, columnas - 0.5)
    ax.set_ylim(-0.5, filas - 0.5)
    ax.set_aspect("equal")
    ax.axis("off")

    return fig


def matriz_a_png(matriz: list, visitadas: list) -> bytes:
    """Dibuja la matriz y la devuelve como imagen PNG (bytes)."""

    fig = dibujar_matriz(matriz, visitadas)
    buffer = io.BytesIO()
    fig.savefig(buffer, format = "png", dpi = 100)
    return buffer.getvalue()
