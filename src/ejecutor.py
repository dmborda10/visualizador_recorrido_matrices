"""
Ejecución aislada del código de los estudiantes.

El código del estudiante NUNCA se ejecuta dentro del proceso de Streamlit.
Se lanza en un proceso hijo (`_runner.py`) con:

- Tiempo máximo (se mata el proceso si se pasa, p. ej. un `while True`).
- Límites de CPU / memoria / escritura de archivos del sistema operativo.
- Máximo de accesos a la matriz.
- Funciones permitidas reducidas (sin `import`, `open`, `exit`, `eval`...).
- Entorno vacío (sin variables de entorno ni secretos del servidor).
- Un máximo de ejecuciones simultáneas en todo el servidor, para que muchos
  estudiantes a la vez no saturen la máquina: los demás esperan su turno.

Nota de seguridad: esto protege la disponibilidad de la aplicación frente a
errores y ciclos infinitos, y bloquea los trucos habituales. No es un sandbox
a prueba de atacantes decididos; si la aplicación se expone a Internet abierto,
conviene además ejecutarla dentro de un contenedor sin credenciales.
"""

import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass, field

RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_runner.py")

MAX_PASOS = 400            # accesos a la matriz permitidos por ejecución
MAX_CODIGO_CHARS = 5000    # tamaño máximo del código
MAX_SALIDA_CHARS = 2000    # tamaño máximo de lo impreso con print
TIEMPO_MAX_S = 3.0         # tiempo máximo de ejecución del código
MEMORIA_MAX_MB = 256       # memoria máxima (se aplica en Linux)
MAX_SIMULTANEOS = max(1, min(4, os.cpu_count() or 1))
ESPERA_MAX_S = 20.0        # cuánto espera un turno antes de pedir reintentar

_cupos = threading.BoundedSemaphore(MAX_SIMULTANEOS)


@dataclass
class Resultado:
    ok: bool
    recorrido: list = field(default_factory=list)
    salida: str = ""
    error: str = ""


def _matar(proceso):
    """Mata el proceso hijo y todo lo que haya lanzado."""
    try:
        if hasattr(os, "killpg"):
            os.killpg(proceso.pid, signal.SIGKILL)
        else:
            proceso.kill()
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _ejecutar_en_proceso(codigo, filas, columnas):
    datos = json.dumps({
        "codigo": codigo,
        "filas": filas,
        "columnas": columnas,
        "max_pasos": MAX_PASOS,
        "max_salida": MAX_SALIDA_CHARS,
        "memoria_mb": MEMORIA_MAX_MB,
        "cpu_s": int(TIEMPO_MAX_S) + 3,  # respaldo: el tiempo real se corta antes
    })

    with tempfile.TemporaryDirectory() as carpeta:
        proceso = subprocess.Popen(
            [sys.executable, "-I", RUNNER],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=carpeta,
            env={},
            start_new_session=True,
        )
        try:
            # El margen cubre el arranque del intérprete.
            salida, _ = proceso.communicate(datos.encode(), timeout=TIEMPO_MAX_S + 2)
        except subprocess.TimeoutExpired:
            _matar(proceso)
            proceso.communicate()
            return Resultado(
                False,
                error=(
                    f"Tu código tardó más de {TIEMPO_MAX_S:g} segundos y se detuvo. "
                    "¿Tienes un ciclo infinito?"
                ),
            )
        finally:
            _matar(proceso)  # por si quedó algún proceso nieto

    if proceso.returncode == -signal.SIGXCPU:
        return Resultado(
            False,
            error=(
                f"Tu código tardó más de {TIEMPO_MAX_S:g} segundos y se detuvo. "
                "¿Tienes un ciclo infinito?"
            ),
        )

    try:
        resp = json.loads(salida.decode())
        return Resultado(
            ok=bool(resp["ok"]),
            recorrido=[(int(i), int(j)) for i, j in resp["recorrido"]],
            salida=str(resp["salida"]),
            error=str(resp["error"]),
        )
    except (ValueError, KeyError, TypeError):
        return Resultado(
            False,
            error=(
                "Tu código se detuvo de forma inesperada "
                "(por ejemplo, por usar demasiada memoria o tiempo)."
            ),
        )


def ejecutar_codigo(codigo, filas, columnas):
    """
    Ejecuta el código del estudiante de forma aislada y devuelve un `Resultado`.
    Nunca lanza excepciones por culpa del código del estudiante.
    """
    if not isinstance(codigo, str) or not codigo.strip():
        return Resultado(False, error="Escribe algún código para ejecutar.")

    if len(codigo) > MAX_CODIGO_CHARS:
        return Resultado(
            False,
            error=f"El código es demasiado largo (máximo {MAX_CODIGO_CHARS} caracteres).",
        )

    filas = max(1, min(int(filas), 10))
    columnas = max(1, min(int(columnas), 15))

    if not _cupos.acquire(timeout=ESPERA_MAX_S):
        return Resultado(
            False,
            error="El servidor está muy ocupado en este momento. Intenta de nuevo en unos segundos.",
        )
    try:
        return _ejecutar_en_proceso(codigo, filas, columnas)
    except OSError:
        return Resultado(
            False,
            error="No se pudo iniciar la ejecución. Intenta de nuevo en unos segundos.",
        )
    finally:
        _cupos.release()
