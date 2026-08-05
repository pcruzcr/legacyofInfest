"""AUD-286 — romper la línea de visión reiniciaba el mundo.

El defecto
----------
`Alerta` tenía tres estados —tranquilo, sospecha, alerta— y el tercero se
apagaba solo. Al perder de vista al jugador, el nivel bajaba y el guardia volvía
a patrullar como si no hubiera pasado nada. Eso convierte el sigilo en un juego
de esquinas: se rompe la visión un segundo, uno se queda quieto detrás de la
caja, y el mundo se reinicia.

Falta el estado que hace que esconderse cueste algo: la **búsqueda**. El guardia
recuerda dónde te vio y se queda ahí unos segundos, así que después de romper la
visión hay que *moverse*. Es lo que hacen MGS, Dishonored y Mark of the Ninja, y
siempre por la misma razón.

La decisión que hay que defender
--------------------------------
**Sólo se busca desde alerta, nunca desde sospecha.** Un guardia que registra la
sala porque creyó ver algo un instante hace el sigilo ilegible: el jugador no
puede aprender un sistema que reacciona igual a un error suyo que a una
detección real.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.ecs import systems as S
from src.framework.ecs.components import Alerta, ConoDeVision, EsJugador, Transform
from src.framework.ecs.world import World

FRAME = 1.0 / 60.0


def _mundo_con_guardia():
    mundo = World()
    guardia = mundo.crear(
        Transform(pygame.Vector2(100, 100), pygame.Rect(100, 100, 16, 16)),
        ConoDeVision(mira=pygame.Vector2(1.0, 0.0), alcance=400.0, semiangulo=45.0),
        Alerta(),
    )
    jugador = mundo.crear(
        Transform(pygame.Vector2(200, 100), pygame.Rect(200, 100, 16, 16)),
        EsJugador(),
    )
    return mundo, guardia, jugador


def _correr(mundo, fotogramas: int) -> None:
    for _ in range(fotogramas):
        S.sistema_conos_de_vision(mundo, FRAME)
        S.sistema_alerta(mundo, FRAME)


def _esconder(mundo, jugador) -> None:
    """Detrás del guardia, fuera del cono."""
    mundo.obtener(jugador, Transform).rect.topleft = (-500, 100)


class TestElCuartoEstado:
    def test_existe(self) -> None:
        alerta = Alerta()
        alerta.busqueda_restante = 1.0
        assert alerta.estado == "busqueda"

    def test_va_por_delante_de_la_sospecha(self) -> None:
        """Quien acaba de perder de vista al jugador está más despierto que
        quien cree haber visto algo, aunque su nivel ya haya caído."""
        alerta = Alerta()
        alerta.nivel = alerta.umbral_sospecha + 0.01
        alerta.busqueda_restante = 1.0
        assert alerta.estado == "busqueda"

    def test_no_pisa_a_la_alerta(self) -> None:
        alerta = Alerta()
        alerta.nivel = alerta.umbral_alerta
        alerta.busqueda_restante = 1.0
        assert alerta.estado == "alerta"


class TestPerderDeVista:
    def test_tras_la_alerta_se_entra_en_busqueda(self) -> None:
        mundo, guardia, jugador = _mundo_con_guardia()
        _correr(mundo, 60)
        assert mundo.obtener(guardia, Alerta).estado == "alerta"

        _esconder(mundo, jugador)
        _correr(mundo, 1)
        # En el flanco sigue leyéndose «alerta» —el nivel todavía está alto— y
        # eso es correcto: lo que tiene que haber pasado es que la búsqueda
        # quede armada. Se comprueba el mecanismo, no la etiqueta.
        assert mundo.obtener(guardia, Alerta).busqueda_restante > 0.0, (
            "perder de vista al jugador no armó la búsqueda: el sigilo se "
            "resuelve rompiendo la visión un segundo"
        )

        # Y cuando el nivel cae, el estado que se lee es «busqueda» y no
        # «tranquilo», que es lo que pasaba antes de AUD-286.
        _correr(mundo, int(2.0 / FRAME))
        assert mundo.obtener(guardia, Alerta).estado == "busqueda"

    def test_y_recuerda_donde_te_vio(self) -> None:
        mundo, guardia, jugador = _mundo_con_guardia()
        _correr(mundo, 60)
        visto = mundo.obtener(guardia, Alerta).ultimo_visto
        assert visto is not None
        assert visto.x == pytest.approx(208.0)

        _esconder(mundo, jugador)
        _correr(mundo, 30)
        # Sigue apuntando a donde estaba, no a donde está.
        assert mundo.obtener(guardia, Alerta).ultimo_visto.x == pytest.approx(208.0)

    def test_la_busqueda_se_acaba(self) -> None:
        """Más de tres segundos deja al guardia clavado lejos de su ronda y
        rompe el patrullaje que el nivel había diseñado."""
        mundo, guardia, jugador = _mundo_con_guardia()
        _correr(mundo, 60)
        _esconder(mundo, jugador)
        _correr(mundo, int(3.5 / FRAME))
        assert mundo.obtener(guardia, Alerta).estado == "tranquilo"

    def test_dura_los_tres_segundos_que_dice_y_no_cuatro(self) -> None:
        """El defecto que tuvo la primera versión: sin detectar el flanco, la
        cuenta atrás se rearmaba mientras el nivel bajaba y la búsqueda duraba
        4,4 s en vez de 3."""
        mundo, guardia, jugador = _mundo_con_guardia()
        _correr(mundo, 60)
        _esconder(mundo, jugador)
        _correr(mundo, int(2.9 / FRAME))
        assert mundo.obtener(guardia, Alerta).busqueda_restante > 0.0
        _correr(mundo, int(0.3 / FRAME))
        assert mundo.obtener(guardia, Alerta).busqueda_restante == 0.0

    def test_volver_a_verlo_cancela_la_busqueda(self) -> None:
        mundo, guardia, jugador = _mundo_con_guardia()
        _correr(mundo, 60)
        _esconder(mundo, jugador)
        _correr(mundo, 10)
        assert mundo.obtener(guardia, Alerta).busqueda_restante > 0.0

        mundo.obtener(jugador, Transform).rect.topleft = (200, 100)
        _correr(mundo, 2)
        assert mundo.obtener(guardia, Alerta).busqueda_restante == 0.0


class TestDesdeSospechaNoSeBusca:
    def test_un_vistazo_no_desata_una_batida(self) -> None:
        """Si sospechar bastara, el jugador no podría distinguir un error suyo
        de una detección real, y un sistema así no se puede aprender."""
        mundo, guardia, jugador = _mundo_con_guardia()
        # Lo justo para pasar de «tranquilo» sin llegar a «alerta».
        _correr(mundo, 15)
        alerta = mundo.obtener(guardia, Alerta)
        assert alerta.estado == "sospecha", f"estado de partida: {alerta.estado}"

        _esconder(mundo, jugador)
        _correr(mundo, 2)
        assert mundo.obtener(guardia, Alerta).estado != "busqueda"


class TestLoDeAntesSigueIgual:
    """La invariante 2: los mapas con guardias ya entregados no cambian."""

    def test_la_alerta_sigue_subiendo_y_bajando(self) -> None:
        mundo, guardia, jugador = _mundo_con_guardia()
        _correr(mundo, 60)
        alto = mundo.obtener(guardia, Alerta).nivel
        _esconder(mundo, jugador)
        _correr(mundo, 30)
        assert mundo.obtener(guardia, Alerta).nivel < alto

    def test_un_guardia_recien_creado_esta_tranquilo(self) -> None:
        alerta = Alerta()
        assert alerta.estado == "tranquilo"
        assert alerta.ultimo_visto is None
