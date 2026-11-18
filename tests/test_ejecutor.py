import os
import sys
import threading
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import ejecutor  # noqa: E402
from src.ejecutor import ejecutar_codigo  # noqa: E402

RECORRIDO_NORMAL = """for i in range(len(matriz)):
    for j in range(len(matriz[i])):
        matriz[i][j]"""


@pytest.fixture(autouse=True)
def limites_rapidos(monkeypatch):
    monkeypatch.setattr(ejecutor, "TIEMPO_MAX_S", 1.0)


# ---------- Funcionamiento normal ----------

def test_recorrido_normal():
    r = ejecutar_codigo(RECORRIDO_NORMAL, 4, 4)
    assert r.ok, r.error
    assert len(r.recorrido) == 16
    assert r.recorrido[0] == (0, 0) and r.recorrido[-1] == (3, 3)


def test_matriz_no_cuadrada():
    r = ejecutar_codigo(RECORRIDO_NORMAL, 3, 5)
    assert r.ok and len(r.recorrido) == 15


def test_while_y_variables_funcionan():
    codigo = "i = 0\nwhile i < len(matriz):\n    matriz[i][i]\n    i += 1"
    r = ejecutar_codigo(codigo, 4, 4)
    assert r.ok and r.recorrido == [(0, 0), (1, 1), (2, 2), (3, 3)]


def test_indices_negativos():
    r = ejecutar_codigo("matriz[-1][-1]", 4, 4)
    assert r.ok and r.recorrido == [(3, 3)]


def test_print_se_captura():
    r = ejecutar_codigo("print(matriz[1][2])", 4, 4)
    assert r.ok and r.salida.strip() == "7"


def test_try_except_del_estudiante_funciona():
    r = ejecutar_codigo("try:\n    matriz[9][9]\nexcept IndexError:\n    matriz[0][0]", 4, 4)
    assert r.ok and r.recorrido == [(0, 0)]


# ---------- Errores del estudiante (mensajes claros, sin romper nada) ----------

def test_error_de_sintaxis():
    r = ejecutar_codigo("for i in range(3)\n    pass", 4, 4)
    assert not r.ok and "sintaxis" in r.error.lower() and "línea 1" in r.error


def test_indice_fuera_de_rango():
    r = ejecutar_codigo("matriz[0][4]", 4, 4)
    assert not r.ok and "IndexError" in r.error and "línea 1" in r.error


def test_error_reporta_linea():
    r = ejecutar_codigo("x = 1\ny = 2\nz = 1 / 0", 4, 4)
    assert not r.ok and "ZeroDivisionError" in r.error and "línea 3" in r.error


def test_no_se_puede_modificar_la_matriz():
    r = ejecutar_codigo("matriz[0][0] = 5", 4, 4)
    assert not r.ok


def test_codigo_vacio():
    assert not ejecutar_codigo("   ", 4, 4).ok


def test_codigo_demasiado_largo():
    r = ejecutar_codigo("x = 1\n" * 5000, 4, 4)
    assert not r.ok and "largo" in r.error


# ---------- Protecciones: lo que antes podía tumbar el servidor ----------

def test_ciclo_infinito_se_corta_por_tiempo():
    t0 = time.time()
    r = ejecutar_codigo("while True:\n    pass", 4, 4)
    assert not r.ok and "segundos" in r.error
    assert time.time() - t0 < 5


def test_ciclo_infinito_accediendo_a_la_matriz_se_corta_por_pasos():
    t0 = time.time()
    r = ejecutar_codigo("while True:\n    matriz[0][0]", 4, 4)
    assert not r.ok and "más de" in r.error
    assert len(r.recorrido) == ejecutor.MAX_PASOS
    assert time.time() - t0 < 5


def test_except_exception_no_oculta_el_limite_de_pasos():
    codigo = "while True:\n    try:\n        matriz[0][0]\n    except Exception:\n        pass"
    r = ejecutar_codigo(codigo, 4, 4)
    assert not r.ok


@pytest.mark.parametrize("codigo", [
    "import os",
    "from os import system",
    "__import__('os').system('echo hola')",
    "open('/etc/passwd').read()",
    "exit()",
    "quit()",
    "eval('1+1')",
    "exec('x=1')",
    "getattr(matriz, 'datos')",
    "matriz.__class__",
    "matriz.__init__.__globals__",
    "().__class__.__bases__[0].__subclasses__()",
    "f'{matriz.__class__}'",
    "x = __builtins__",
    "globals()",
    "compile('1', 'a', 'eval')",
])
def test_codigo_peligroso_es_rechazado(codigo):
    r = ejecutar_codigo(codigo, 4, 4)
    assert not r.ok, f"Se ejecutó código peligroso: {codigo}"
    # El servidor (este proceso) sigue vivo, por supuesto.


def test_el_estudiante_no_ve_variables_de_entorno(monkeypatch):
    monkeypatch.setenv("SECRETO_DEL_SERVIDOR", "abc123")
    r = ejecutar_codigo("print(len(matriz))", 4, 4)
    assert r.ok and "abc123" not in r.salida


def test_salida_enorme_se_recorta():
    r = ejecutar_codigo("for i in range(100000):\n    print('x' * 100)", 4, 4)
    assert r.ok and len(r.salida) < ejecutor.MAX_SALIDA_CHARS + 100


def test_recursion_infinita():
    codigo = "def f():\n    return f()\nf()"
    # 'def' funciona; la recursión debe terminar con error, no con un crash.
    r = ejecutar_codigo(codigo, 4, 4)
    assert not r.ok


@pytest.mark.skipif(not sys.platform.startswith("linux"),
                    reason="El límite de memoria solo se aplica en Linux")
def test_bomba_de_memoria():
    r = ejecutar_codigo("x = [0] * (10 ** 10)", 4, 4)
    assert not r.ok


def test_no_quedan_procesos_huerfanos():
    import subprocess
    ejecutar_codigo("while True:\n    pass", 4, 4)
    time.sleep(0.3)
    salida = subprocess.run(["ps", "-A", "-o", "command"], capture_output=True, text=True).stdout
    assert "_runner.py" not in salida


# ---------- Uso masivo ----------

def _lanzar(n, codigo):
    resultados = [None] * n

    def trabajo(k):
        resultados[k] = ejecutar_codigo(codigo, 4, 4)

    hilos = [threading.Thread(target=trabajo, args=(k,)) for k in range(n)]
    t0 = time.time()
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    return resultados, time.time() - t0


def test_muchos_usuarios_a_la_vez_codigo_normal():
    resultados, _ = _lanzar(60, RECORRIDO_NORMAL)
    assert all(r.ok and len(r.recorrido) == 16 for r in resultados)


def test_usuarios_buenos_no_se_ven_afectados_por_ciclos_infinitos():
    """Mezcla: hilos con ciclos infinitos y hilos normales, todos a la vez."""
    codigos = ["while True:\n    pass", RECORRIDO_NORMAL] * 10
    resultados = [None] * len(codigos)

    def trabajo(k):
        resultados[k] = ejecutar_codigo(codigos[k], 4, 4)

    hilos = [threading.Thread(target=trabajo, args=(k,)) for k in range(len(codigos))]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    for codigo, r in zip(codigos, resultados):
        if codigo == RECORRIDO_NORMAL:
            assert r.ok and len(r.recorrido) == 16, r.error
        else:
            assert not r.ok


def test_servidor_ocupado_responde_amablemente(monkeypatch):
    """Si se agota la espera por un turno, se avisa en vez de colgarse."""
    monkeypatch.setattr(ejecutor, "MAX_SIMULTANEOS", 1)
    monkeypatch.setattr(ejecutor, "_cupos", threading.BoundedSemaphore(1))
    monkeypatch.setattr(ejecutor, "ESPERA_MAX_S", 0.2)
    resultados, _ = _lanzar(4, "while True:\n    pass")
    mensajes = [r.error for r in resultados]
    assert any("ocupado" in m for m in mensajes)
    assert all(not r.ok for r in resultados)
