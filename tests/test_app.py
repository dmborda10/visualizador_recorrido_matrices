import os
import sys
import threading

import streamlit as st
import streamlit_ace
from streamlit.testing.v1 import AppTest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

APP = os.path.join(RAIZ, "inicio.py")

CODIGO_NORMAL = """for i in range(len(matriz)):
    for j in range(len(matriz[i])):
        matriz[i][j]"""

# AppTest no puede manejar el editor (componente personalizado); se reemplaza
# por una función que devuelve el código del "estudiante" de cada sesión
# (guardado en el session_state de esa sesión, no en una variable global).
def _falso_st_ace(*args, **kwargs):
    return st.session_state.get("_codigo_test", kwargs.get("value"))


def _nueva_sesion(codigo, timeout=60):
    streamlit_ace.st_ace = _falso_st_ace
    at = AppTest.from_file(APP, default_timeout=timeout)
    at.session_state["_codigo_test"] = codigo
    return at


def _abrir(codigo):
    return _nueva_sesion(codigo).run()


def _ejecutar(at):
    # Velocidad máxima de animación en las pruebas.
    at.sidebar.number_input[1].set_value(0.1)
    at.run()
    at.button[0].click().run()
    return at


def test_la_app_carga_sin_errores():
    at = _abrir(CODIGO_NORMAL)
    assert not at.exception
    assert len(at.get("image")) == 1


def test_ejecucion_normal_termina_bien():
    at = _ejecutar(_abrir(CODIGO_NORMAL))
    assert not at.exception
    assert not at.error


def test_error_del_estudiante_se_muestra_sin_romper_la_app():
    at = _ejecutar(_abrir("matriz[0][50]"))
    assert not at.exception
    assert len(at.error) == 1
    assert "IndexError" in at.error[0].value


def test_ciclo_infinito_no_cuelga_la_app():
    at = _ejecutar(_abrir("while True:\n    pass"))
    assert not at.exception
    assert len(at.error) == 1 and "segundos" in at.error[0].value


def test_codigo_malicioso_no_cierra_la_app():
    for codigo in ("import os\nos._exit(1)", "exit()", "__import__('os')._exit(1)"):
        at = _ejecutar(_abrir(codigo))
        assert not at.exception
        assert len(at.error) == 1


def test_muchos_usuarios_a_la_vez_en_la_app():
    """30 sesiones simultáneas: 10 con ciclo infinito, 10 con errores, 10 normales."""
    casos = (["while True:\n    pass"] * 10
             + ["matriz[0][50]"] * 10
             + [CODIGO_NORMAL] * 10)
    resultados = {}

    def sesion(k, codigo):
        try:
            at = _nueva_sesion(codigo, timeout=120).run()
            at.sidebar.number_input[1].set_value(0.1)
            at.run()
            at.button[0].click().run()
            resultados[k] = (codigo, at)
        except Exception as e:  # pragma: no cover
            resultados[k] = (codigo, e)

    streamlit_ace.st_ace = _falso_st_ace
    hilos = [threading.Thread(target=sesion, args=(k, c)) for k, c in enumerate(casos)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    assert len(resultados) == len(casos)
    for codigo, at in resultados.values():
        assert not isinstance(at, Exception), at
        assert not at.exception, at.exception
        if codigo == CODIGO_NORMAL:
            assert not at.error
        else:
            assert len(at.error) == 1
