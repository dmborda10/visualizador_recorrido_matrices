class FilaVisual:

    def __init__(self, fila, indice_fila, recorrido):
        self.fila = fila
        self.indice_fila = indice_fila
        self.recorrido = recorrido

    def __getitem__(self, j):
        
        if j < 0:
            j = len(self.fila) + j
            
        self.recorrido.append((self.indice_fila, j))
        return self.fila[j]

    def __len__(self):
        return len(self.fila)


class MatrizVisual:

    def __init__(self, datos):
        self.datos = datos
        self.recorrido = []

    def __getitem__(self, i):

        if i < 0:
            i = len(self.datos) + i

        return FilaVisual(
            self.datos[i],
            i,
            self.recorrido
        )

    def __len__(self):
        return len(self.datos)