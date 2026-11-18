"""
Proceso hijo que ejecuta el código de UN estudiante.

NO se importa desde la aplicación: lo lanza `ejecutor.py` en un proceso
separado (`python -I _runner.py`). Así, si el código del estudiante se cuelga,
consume demasiada memoria o intenta cerrar el programa, solo muere este
proceso y la aplicación (y los demás usuarios) siguen funcionando.

Protocolo: lee un JSON por stdin y escribe un JSON por stdout.
"""

import ast
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from matriz import inicializar_matriz  # noqa: E402
from visualizador import LimitePasos, MatrizVisual  # noqa: E402


BUILTINS_PERMITIDOS = (
    "range", "len", "enumerate", "zip", "reversed", "sorted",
    "min", "max", "sum", "abs", "round", "divmod", "pow",
    "int", "float", "str", "bool", "list", "tuple", "set", "dict",
    "True", "False", "None",
    "Exception", "ValueError", "TypeError", "IndexError", "ZeroDivisionError",
)


class CodigoNoPermitido(Exception):
    pass


def limitar_recursos(memoria_mb, cpu_s):
    """Límites del sistema operativo (donde existan) como segunda barrera."""
    try:
        import resource
    except ImportError:  # Windows
        return

    def fijar(tipo, valor):
        try:
            resource.setrlimit(tipo, (valor, valor))
        except (ValueError, OSError):
            pass

    fijar(resource.RLIMIT_CPU, int(cpu_s))
    fijar(resource.RLIMIT_FSIZE, 0)  # no escribir archivos
    if sys.platform.startswith("linux"):
        # En macOS RLIMIT_AS no se respeta; en Linux (producción) sí.
        fijar(resource.RLIMIT_AS, memoria_mb * 1024 * 1024)


def validar(arbol):
    """Rechaza imports y accesos a atributos/nombres 'privados' (__class__, ...)."""
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Import, ast.ImportFrom)):
            raise CodigoNoPermitido("No se permite usar 'import'.")
        if isinstance(nodo, ast.Attribute) and nodo.attr.startswith("_"):
            raise CodigoNoPermitido(
                f"No se permite acceder al atributo '{nodo.attr}'."
            )
        if isinstance(nodo, ast.Name) and nodo.id.startswith("__"):
            raise CodigoNoPermitido(f"No se permite usar el nombre '{nodo.id}'.")


class Salida:
    """Acumula lo que el estudiante imprime con print, con un tope."""

    def __init__(self, limite):
        self.limite = limite
        self.partes = []
        self.total = 0
        self.truncada = False

    def imprimir(self, *args, sep=" ", end="\n", **_ignorados):
        if self.truncada:
            return
        texto = str(sep if isinstance(sep, str) else " ").join(
            str(a) for a in args
        ) + (end if isinstance(end, str) else "\n")
        restante = self.limite - self.total
        if len(texto) > restante:
            texto = texto[:restante]
            self.truncada = True
        self.partes.append(texto)
        self.total += len(texto)

    def texto(self):
        salida = "".join(self.partes)
        if self.truncada:
            salida += "\n[salida recortada]"
        return salida


def linea_del_error(exc):
    """Línea del código del estudiante donde ocurrió el error (si se sabe)."""
    linea = None
    for marco, numero in traceback.walk_tb(exc.__traceback__):
        if marco.f_code.co_filename == "<codigo>":
            linea = numero
    return linea


def ejecutar(datos):
    salida = Salida(datos["max_salida"])
    resultado = {"ok": False, "recorrido": [], "salida": "", "error": ""}
    matriz = None

    try:
        codigo = datos["codigo"]
        try:
            arbol = ast.parse(codigo, filename="<codigo>")
        except SyntaxError as e:
            raise CodigoNoPermitido(
                f"Error de sintaxis en la línea {e.lineno}: {e.msg}"
            )
        validar(arbol)
        compilado = compile(arbol, "<codigo>", "exec")

        base = inicializar_matriz(False, datos["filas"], datos["columnas"])
        matriz = MatrizVisual(base, datos["max_pasos"])

        builtins_seguros = {
            nombre: getattr(__builtins__, nombre)
            if not isinstance(__builtins__, dict)
            else __builtins__[nombre]
            for nombre in BUILTINS_PERMITIDOS
        }
        builtins_seguros["print"] = salida.imprimir
        entorno = {"__builtins__": builtins_seguros, "matriz": matriz}

        limitar_recursos(datos["memoria_mb"], datos["cpu_s"])
        exec(compilado, entorno)
        resultado["ok"] = True

    except CodigoNoPermitido as e:
        resultado["error"] = str(e)
    except LimitePasos:
        resultado["error"] = (
            f"Tu código accedió a la matriz más de {datos['max_pasos']} veces. "
            "¿Tienes un ciclo infinito?"
        )
    except MemoryError:
        resultado["error"] = "Tu código usó demasiada memoria."
    except RecursionError:
        resultado["error"] = "Tu código tiene demasiada recursión."
    except Exception as e:  # errores normales del estudiante
        linea = linea_del_error(e)
        donde = f" (línea {linea})" if linea else ""
        resultado["error"] = f"{type(e).__name__}: {e}{donde}"

    if matriz is not None:
        resultado["recorrido"] = [list(p) for p in matriz.recorrido]
    resultado["salida"] = salida.texto()
    return resultado


def main():
    datos = json.loads(sys.stdin.read())
    resultado = ejecutar(datos)
    sys.stdout.write(json.dumps(resultado))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
