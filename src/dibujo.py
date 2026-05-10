import matplotlib.pyplot as plt

def dibujar_matriz(matriz: list, visitadas: list):
    
    filas = len(matriz)
    columnas = len(matriz[0])

    fig, ax = plt.subplots(figsize = (3.5, 3.5))

    for i in range(filas):
        for j in range(columnas):
            cuadrado = plt.Rectangle(
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
        cuadrado = plt.Rectangle(
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