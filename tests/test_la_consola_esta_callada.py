"""AUD-268 — jugar escupía avisos de depuración por la consola.

El defecto
==========
El proyecto **no configuraba el logging en ninguna parte**: ni `basicConfig`,
ni un nivel, ni un manejador. Medido con
`grep -rn "basicConfig\\|setLevel\\|StreamHandler" src/ main.py`: cero
resultados.

Sin configuración, Python instala su manejador de último recurso, que escribe
todo lo de nivel `WARNING` o superior **a la consola**. Y este repositorio tiene
**134 llamadas a `logger.warning`**, muchas en rutas normales de juego: un
fondo que no está, un árbol de diálogo que el mapa pide y no existe, el
renderizador que cae a software. El jugador ve una pared de mensajes técnicos
mientras juega.

Por qué no se borran los avisos
-------------------------------
Porque son correctos. Este repositorio lleva un mes cazando cosas que fallaban
**en silencio** —AUD-055, AUD-127, AUD-149— y la lección fue justamente la
contraria: callarse es lo que hace que un defecto dure meses. Los avisos se
quedan; lo que cambia es **a dónde van**.

La consola queda limpia y el registro completo va a un fichero en el directorio
del usuario, junto a las partidas. `--debug` lo devuelve a la consola para quien
esté diagnosticando, que es la única persona que quiere verlo.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest

from src.engine.core.registro import _MARCA, configurar_registro, ruta_del_registro

RAIZ = Path(__file__).resolve().parents[1]


def _nuestros() -> list[logging.Handler]:
    """Sólo los manejadores del motor.

    pytest instala los suyos en el logger raíz —captura de `caplog`, salida en
    vivo— y contarlos aquí haría fallar la prueba por algo que el juego no
    controla. `configurar_registro` marca los suyos justamente para esto.
    """
    return [h for h in logging.getLogger().handlers if getattr(h, _MARCA, False)]


def _consolas() -> list[logging.Handler]:
    return [h for h in _nuestros()
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)]


@pytest.fixture(autouse=True)
def _raiz_limpia():
    """Deja el logger raíz como estaba: es estado global del proceso."""
    raiz = logging.getLogger()
    previos = list(raiz.handlers)
    nivel = raiz.level
    yield
    raiz.handlers = previos
    raiz.setLevel(nivel)


class TestLaConsolaSeQuedaCallada:
    def test_por_defecto_no_hay_manejador_de_consola(self, tmp_path) -> None:
        configurar_registro(depurar=False, directorio=tmp_path)

        assert _consolas() == [], (
            "sigue habiendo un manejador de consola: el jugador ve los avisos"
        )

    def test_un_aviso_no_llega_a_la_consola(self, tmp_path, capsys) -> None:
        configurar_registro(depurar=False, directorio=tmp_path)

        logging.getLogger("prueba").warning("esto no lo puede ver el jugador")

        capturado = capsys.readouterr()
        assert "no lo puede ver" not in capturado.err
        assert "no lo puede ver" not in capturado.out


class TestElRegistroNoSePierde:
    def test_el_aviso_acaba_en_el_fichero(self, tmp_path) -> None:
        """Callar la consola no puede significar perder el diagnóstico."""
        configurar_registro(depurar=False, directorio=tmp_path)

        logging.getLogger("prueba").warning("un fondo que falta")
        for h in logging.getLogger().handlers:
            h.flush()

        assert "un fondo que falta" in ruta_del_registro(tmp_path).read_text(
            encoding="utf-8")

    def test_con_depurar_vuelve_a_la_consola(self, tmp_path) -> None:
        configurar_registro(depurar=True, directorio=tmp_path)

        assert _consolas(), "--debug tiene que devolver los avisos a la consola"

    def test_llamarlo_dos_veces_no_duplica_manejadores(self, tmp_path) -> None:
        """`App` puede construirse dos veces en la misma sesión (pruebas)."""
        configurar_registro(depurar=False, directorio=tmp_path)
        configurar_registro(depurar=False, directorio=tmp_path)

        ficheros = [h for h in _nuestros() if isinstance(h, logging.FileHandler)]
        assert len(ficheros) == 1

    def test_un_directorio_no_escribible_no_impide_jugar(self, tmp_path) -> None:
        """Si no se puede abrir el fichero, se juega igual y sin ruido."""
        configurar_registro(depurar=False, directorio=tmp_path / "no" / "existe" / "\0")

        logging.getLogger("prueba").warning("da igual")   # no debe lanzar


class TestElJuegoLoLlama:
    """La comprobación que lo habría evitado: alguien tiene que configurarlo."""

    def test_app_configura_el_registro(self) -> None:
        fuente = (RAIZ / "src" / "engine" / "core" / "app.py").read_text(
            encoding="utf-8")

        assert "configurar_registro" in fuente, (
            "nadie configura el registro: vuelve el manejador de último "
            "recurso de Python y con él los 134 avisos por consola"
        )

    def test_main_ofrece_la_bandera(self) -> None:
        fuente = (RAIZ / "main.py").read_text(encoding="utf-8")

        assert "--debug" in fuente
