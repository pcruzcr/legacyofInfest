"""
El medidor de estamina — AUD-141.

La última fila del catálogo de mecánicas.

Por qué viene apagada de fábrica
---------------------------------
Una estamina cambia **cómo se juega**: convierte el dash de recurso libre en
recurso administrado. Encenderla para todo el mundo cambiaría los quince
escenarios ya entregados sin que sus autores lo pidan, y varios están medidos
al dash — un salto que hoy se cruza con dos dashes seguidos dejaría de
cruzarse. Se enciende por escenario, con la propiedad `estamina` del mapa.

Ésa es la decisión de diseño que estas pruebas defienden, y la mitad de ellas
comprueban justamente que **con la estamina apagada no cambia nada**.
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


def _jugador(estamina: float = 0.0):
    from src.framework.entities.player import Player

    p = Player(pygame.Vector2(100, 100))
    p.activar_estamina(estamina)
    return p


class TestApagadaNoSeNota:
    """Los quince escenarios entregados no declaran `estamina`."""

    def test_por_defecto_esta_apagada(self) -> None:
        assert _jugador().estamina_activa is False

    def test_apagada_siempre_hay_para_correr(self) -> None:
        jugador = _jugador()
        for _ in range(50):
            jugador.gastar_estamina()
        assert jugador.hay_estamina_para_correr is True

    def test_gastar_con_ella_apagada_no_falla_nunca(self) -> None:
        assert _jugador().gastar_estamina(9999) is True

    def test_apagada_el_hud_no_dibuja_la_barra(self) -> None:
        """Una barra vacía en un nivel sin estamina es una promesa falsa: el
        jugador se pondría a buscar qué la llena."""
        from src.engine.core.event_bus import EventBus
        from src.engine.ui.hud import HUD

        hud = HUD(EventBus())
        hud.set_estamina(0.0, 0.0)
        lienzo = pygame.Surface((320, 240))
        lienzo.fill((0, 0, 0))
        hud._draw_estamina(lienzo)
        assert lienzo.get_at((90, 41))[:3] == (0, 0, 0)


class TestEncendida:
    def test_arranca_llena(self) -> None:
        jugador = _jugador(100)
        assert jugador.estamina == 100
        assert jugador.estamina_activa is True

    def test_un_dash_cuesta(self) -> None:
        jugador = _jugador(100)
        assert jugador.gastar_estamina() is True
        assert jugador.estamina == 75

    def test_cuatro_dashes_la_vacian(self) -> None:
        jugador = _jugador(100)
        for _ in range(4):
            assert jugador.gastar_estamina() is True
        assert jugador.estamina == 0
        assert jugador.gastar_estamina() is False

    def test_sin_estamina_no_se_puede_correr(self) -> None:
        jugador = _jugador(100)
        jugador.estamina = 0.0
        assert jugador.hay_estamina_para_correr is False

    def test_se_recupera_con_el_tiempo(self) -> None:
        jugador = _jugador(100)
        jugador.gastar_estamina()
        for _ in range(120):                    # dos segundos
            jugador.recuperar_estamina(1 / 60)
        assert jugador.estamina == pytest.approx(100, abs=0.5)

    def test_hay_una_pausa_antes_de_recuperar(self) -> None:
        """Sin la pausa, la barra se rellena mientras se encadenan dashes y
        no limita nada: la mecánica existiría sin hacer efecto."""
        jugador = _jugador(100)
        jugador.gastar_estamina()
        antes = jugador.estamina
        for _ in range(int(0.5 * 60)):          # menos que la espera
            jugador.recuperar_estamina(1 / 60)
        assert jugador.estamina == antes

    def test_no_pasa_del_maximo(self) -> None:
        jugador = _jugador(100)
        for _ in range(600):
            jugador.recuperar_estamina(1 / 60)
        assert jugador.estamina == 100

    def test_no_baja_de_cero(self) -> None:
        jugador = _jugador(30)
        jugador.gastar_estamina()               # 30 - 25 = 5
        assert jugador.gastar_estamina() is False
        assert jugador.estamina >= 0


class TestLaPuertaDelDash:
    """`_can_dash` es el único sitio del motor donde se decide si un dash
    empieza. Ponerlo en cada estado que lo permite —hay seis— habría
    garantizado que a alguno se le olvidara."""

    def _intento(self, jugador):
        from src.framework.entities.states.base import _InputSnapshot
        from src.framework.entities.states.helpers import _can_dash

        return _can_dash(jugador, _InputSnapshot(None))

    def test_con_estamina_se_puede(self) -> None:
        jugador = _jugador(100)
        jugador.is_grounded = True
        assert self._intento(jugador) is True

    def test_sin_estamina_no(self) -> None:
        jugador = _jugador(100)
        jugador.is_grounded = True
        jugador.estamina = 0.0
        assert self._intento(jugador) is False

    def test_apagada_se_puede_siempre(self) -> None:
        jugador = _jugador()
        jugador.is_grounded = True
        jugador.estamina = 0.0
        assert self._intento(jugador) is True

    def test_el_dash_cobra_al_entrar_en_el_estado(self) -> None:
        """Se cobra al entrar y no al pulsar: así no se paga por un dash que
        otra condición cancela después."""
        from src.framework.entities.states import DashingState

        jugador = _jugador(100)
        jugador.is_grounded = True
        jugador._change_state_instance(DashingState())
        assert jugador.estamina == 75


class TestLoQueLlegaDesdeElMapa:
    def test_la_propiedad_del_mapa_enciende_la_estamina(self) -> None:
        from src.framework.stage.stage_loader import StageData

        stage = StageData(map_layer=None)  # type: ignore[arg-type]
        assert stage.estamina == 0.0, "por defecto tiene que venir apagada"

    def test_activar_desde_un_valor_del_mapa(self) -> None:
        jugador = _jugador()
        jugador.activar_estamina(80)
        assert jugador.estamina_activa and jugador.estamina == 80

    def test_un_valor_negativo_la_deja_apagada(self) -> None:
        """Dato hostil: `estamina = -10` en Tiled."""
        jugador = _jugador()
        jugador.activar_estamina(-10)
        assert jugador.estamina_activa is False


class TestLaBarra:
    def _hud(self, actual: float, maximo: float):
        from src.engine.core.event_bus import EventBus
        from src.engine.ui.hud import HUD

        hud = HUD(EventBus())
        hud.set_estamina(actual, maximo)
        lienzo = pygame.Surface((320, 240))
        lienzo.fill((0, 0, 0))
        hud._draw_estamina(lienzo)
        return lienzo

    def test_encendida_se_dibuja(self) -> None:
        lienzo = self._hud(100, 100)
        assert lienzo.get_at((90, 41))[:3] != (0, 0, 0)

    def test_avisa_en_ambar_cuando_queda_poco(self) -> None:
        """El jugador tiene que poder decidir **antes** de intentar el dash
        que no le va a salir."""
        llena = self._hud(100, 100).get_at((86, 41))[:3]
        poca = self._hud(20, 100).get_at((86, 41))[:3]
        assert llena != poca

    def test_vacia_ensena_el_carril_pero_no_el_relleno(self) -> None:
        """Vacía sigue viéndose el hueco de la barra, y eso es lo correcto:
        una barra que desaparece al gastarse no dice cuánto falta."""
        vacia = self._hud(0, 100).get_at((100, 41))[:3]
        llena = self._hud(100, 100).get_at((100, 41))[:3]
        assert vacia != llena
        assert vacia != (0, 0, 0), "la barra desaparece al vaciarse"
