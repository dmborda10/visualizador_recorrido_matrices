class LimitePasos(BaseException):
    """
    Se lanza cuando el código del estudiante accede a la matriz más veces
    de las permitidas (por ejemplo, por un ciclo infinito).

    Hereda de BaseException a propósito: así un `except Exception` del
    código del estudiante no puede ocultarla.
    """


class FilaVisual:

    def __init__(self, fila, indice_fila, recorrido, max_pasos):
        self.fila = fila
        self.indice_fila = indice_fila
        self.recorrido = recorrido
        self.max_pasos = max_pasos

    def __getitem__(self, j):

        if not isinstance(j, int):
            raise TypeError("El índice de la columna debe ser un número entero.")

        if j < 0:
            j = len(self.fila) + j

        if not 0 <= j < len(self.fila):
            raise IndexError(
                f"La columna {j} no existe (la matriz tiene {len(self.fila)} columnas)."
            )

        if len(self.recorrido) >= self.max_pasos:
            raise LimitePasos(
                f"Se superó el máximo de {self.max_pasos} accesos a la matriz."
            )

        self.recorrido.append((self.indice_fila, j))
        return self.fila[j]

    def __len__(self):
        return len(self.fila)


class MatrizVisual:

    def __init__(self, datos, max_pasos = 400):
        self.datos = datos
        self.max_pasos = max_pasos
        self.recorrido = []

    def __getitem__(self, i):

        if not isinstance(i, int):
            raise TypeError("El índice de la fila debe ser un número entero.")

        if i < 0:
            i = len(self.datos) + i

        if not 0 <= i < len(self.datos):
            raise IndexError(
                f"La fila {i} no existe (la matriz tiene {len(self.datos)} filas)."
            )

        return FilaVisual(
            self.datos[i],
            i,
            self.recorrido,
            self.max_pasos
        )

    def __len__(self):
        return len(self.datos)
