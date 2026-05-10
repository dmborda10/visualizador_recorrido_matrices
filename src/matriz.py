def inicializar_matriz(
    es_cuadrada: bool,
    filas: int,
    columnas: int
    ) -> list:
    """
    Inicializa una matriz numérica secuencial.

    Parámetros:
        es_cuadrada (bool):
            Indica si la matriz debe ser cuadrada.
        filas (int):
            Número de filas.
        columnas (int):
            Número de columnas.

    Retorno:
        list:
            Matriz generada.
    """

    if es_cuadrada:

        columnas = filas

    valor = 1
    matriz = []

    for i in range(filas):

        fila = []
        
        for j in range(columnas):

            fila.append(valor)
            valor += 1

        matriz.append(fila)

    return matriz