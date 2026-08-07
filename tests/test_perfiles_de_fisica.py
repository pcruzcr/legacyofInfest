"""La física declarada por contexto: AUD-333 — `PhysicsProfile`.

Antes, la física de locomoción vivía dentro de cada integrador con
constantes de `settings` repartidas (la gravedad en `Player._apply_physics`,
el salto en la máquina de estados, las pendientes en `pendientes.py`), y el
modo cenital era una bandera booleana. Un motor que sirve **contextos y
modos de juego** necesita que el contexto sea un dato: éste es el perfil que
lo hace, y estas pruebas fijan que el integrador de verdad lo consume.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import settings
from src.framework.entities.player import Player
from src.framework.physics.perfil import (
    CENITAL,
    PLATAFORMAS,
    Muro,
    PhysicsProfile,
)


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


class TestLosPresets:
    def test_plataformas_reproduce_las_constantes_del_juego(self) -> None:
        perfil = PhysicsProfile.plataformas()
        assert perfil.modo == PLATAFORMAS
        assert perfil.gravedad == settings.GRAVITY
        assert perfil.max_caida == settings.PLAYER_MAX_FALL_SPEED
        assert perfil.velocidad_suelo == settings.PLAYER_WALK_SPEED
        assert perfil.salto_impulso == settings.PLAYER_JUMP_FORCE
        assert perfil.coyote_frames == settings.PLAYER_COYOTE_FRAMES
        assert perfil.saltos_aereos == settings.PLAYER_AIR_JUMPS

    def test_cenital_es_sin_gravedad_y_sin_salto(self) -> None:
        perfil = PhysicsProfile.cenital()
        assert perfil.modo == CENITAL
        assert perfil.gravedad == 0.0
        assert perfil.max_caida == 0.0
        assert perfil.salto_impulso == 0.0
        assert perfil.coyote_frames == 0
        assert perfil.saltos_aereos == 0

    def test_los_parametros_de_pendientes_tienen_los_valores_del_juego(self) -> None:
        perfil = PhysicsProfile.plataformas()
        assert perfil.cuestas.margen_pegado == 8.0
        assert perfil.cuestas.velocidad_deslizamiento == settings.PLAYER_SLOPE_SLIDE_SPEED
        assert perfil.muro.factor_gravedad == 0.3
        assert perfil.muro.factor_max_caida == 0.5


class TestElPerfilMandaEnLaFisica:
    def _en_el_aire(self) -> Player:
        player = Player(pygame.Vector2(0, 0))
        player.is_grounded = False
        player.velocity.update(0.0, 0.0)
        return player

    def test_la_gravedad_del_perfil_se_integra(self) -> None:
        """RED de AUD-333: el jugador lee su perfil y no `settings`."""
        player = self._en_el_aire()
        player.perfil.gravedad = 200.0
        player.update(0.1)
        assert player.velocity.y == pytest.approx(20.0)

    def test_la_caida_maxima_del_perfil_se_respeta(self) -> None:
        player = self._en_el_aire()
        player.perfil.gravedad = settings.GRAVITY * 100.0
        player.perfil.max_caida = 90.0
        player.update(1.0)
        assert player.velocity.y == pytest.approx(90.0)

    def test_los_factores_de_muro_vienen_del_perfil(self) -> None:
        player = self._en_el_aire()
        player.velocity.y = 10.0  # la rama de muro sólo actúa cayendo
        player.perfil.muro = Muro(factor_gravedad=0.1, factor_max_caida=0.25)
        # `_apply_physics` directo: la máquina de estados rellena `_wall_side`
        # en una `update` completa, y aquí se está aislando el bloque de
        # física, no el estado.
        player._wall_side = 1
        player._apply_physics(0.1)
        assert player.velocity.y == pytest.approx(
            10.0 + settings.GRAVITY * 0.1 * 0.1)

    def test_la_velocidad_de_suelo_viene_del_perfil(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        player.perfil.velocidad_suelo = 123.0
        assert player.walk_speed == pytest.approx(123.0)

    def test_el_salto_sale_del_perfil(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        player.perfil.salto_impulso = -200.0
        from src.framework.entities.states.helpers import _do_jump

        _do_jump(player)
        assert player.velocity.y == pytest.approx(-200.0)

    def test_el_coyote_sale_del_perfil(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        player.perfil.coyote_frames = 12
        from src.framework.entities.states.helpers import _can_jump

        player.is_grounded = False
        player._coyote_counter = 10
        assert _can_jump(player)

    def test_los_saltos_aereos_salen_del_perfil(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        player.perfil.saltos_aereos = 3
        player._air_jumps_used = 2
        player.is_grounded = False
        player._coyote_counter = 99
        from src.framework.entities.states.helpers import _can_jump

        assert _can_jump(player)


class TestElModoCenitalEsUnPerfil:
    def test_el_preset_cenital_enciende_la_vista(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        player.perfil = PhysicsProfile.cenital()
        assert player.vista_cenital is True

    def test_el_modo_es_la_fuente_de_la_vista(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        player.perfil.modo = CENITAL
        assert player.vista_cenital is True

    def test_apagar_la_vista_devuelve_el_modo(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        player.vista_cenital = True
        assert player.perfil.modo == CENITAL
        player.vista_cenital = False
        assert player.perfil.modo == PLATAFORMAS

    def test_con_perfil_cenital_no_se_acumula_gravedad(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        player.perfil = PhysicsProfile.cenital()
        player.update(0.1, input_manager=None)
        assert player.velocity.y == 0.0


class TestLasPendientesSeParametrizan:
    def test_el_margen_de_pegado_del_perfil_llega_a_la_resolucion(self) -> None:
        """Con margen, unos píxeles por debajo de la superficie son suelo y se
        pega; sin margen, son aire y no hay nada que resolver."""
        from src.framework.stage.pendientes import (
            Pendiente,
            resolver_con_ganadora,
        )

        rampa = Pendiente(pygame.Rect(0, 0, 64, 32), sube_a_la_derecha=True)
        # Pies en y=10, superficie en y=13 (centro en x=38): el margen de 8
        # alcanza a pegar; el de 0 deja el pie volando un pelo y se salta.
        rect = pygame.Rect(28, -6, 20, 16)

        con_margen, _ = resolver_con_ganadora(
            rect, 0.0, True, [rampa], margen=8.0)
        sin_margen, _ = resolver_con_ganadora(
            rect, 0.0, True, [rampa], margen=0.0)
        assert con_margen == 13.0
        assert sin_margen is None
