"""Parar una embestida la cancela — AUD-239.

El hueco, destapado por AUD-206
===============================
AUD-206 hizo que un parry acertado metiera al enemigo en `STUNNED` durante una
ventana de castigo. Con el `EnemyCharger` y el `EnemyWalker` eso no bastaba:
los dos llevan **su propia máquina de embestida** en banderas
(`_is_charging`, `_is_winding_up`), y `stun()` sólo tocaba el estado de la
base. Al salir del aturdimiento, `_alert_behavior` volvía a encontrarse
`_is_charging = True` y **reanudaba la misma embestida** — con el jugador ya
colocado para castigar y el enemigo saliendo disparado contra él.

Ya pasaba antes de AUD-206 (con `HURT` de 0,3 s el parpadeo era corto y se
confundía con un empujón), pero con 0,9 s de aturdimiento el enemigo se queda
quieto, el jugador se acerca a pegar, y entonces arranca. Es peor que no
aturdir: enseña al jugador que parar es una trampa.

El segundo defecto, más silencioso
----------------------------------
`EnemyCharger.__init__` declara `self._stun_timer`, **el mismo nombre que usa
`EnemyBase` para la rama `STUNNED`**. Dos dueños para una variable: la base la
decrementa en su rama y el charger la decrementa en `_alert_behavior`. Mientras
nadie llamaba a `stun()` en producción —hasta AUD-206— no chocaban nunca.
"""
from __future__ import annotations

import pygame
import pytest

DT = 1.0 / 60.0


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


@pytest.fixture
def charger():
    from src.framework.entities.enemy_charger import EnemyCharger

    e = EnemyCharger(pygame.Vector2(200.0, 300.0))
    e.set_player_ref(pygame.Rect(260, 300, 20, 32))
    return e


class TestElChargerNoReanudaLaEmbestida:
    def test_aturdir_a_media_embestida_la_cancela(self, charger) -> None:
        charger._is_charging = True
        charger._charge_timer = 0.5

        charger.stun(0.9)

        assert charger._is_charging is False, (
            "la embestida seguía en marcha por dentro: al salir del "
            "aturdimiento el enemigo arrancaba contra el jugador que se había "
            "acercado a castigarle"
        )

    def test_aturdir_durante_el_aviso_tambien(self, charger) -> None:
        """El telegrafiado es la parte que el jugador lee para parar."""
        charger._is_winding_up = True
        charger._wind_up_timer = 0.3

        charger.stun(0.9)

        assert charger._is_winding_up is False

    def test_tras_el_aturdimiento_no_sale_disparado(self, charger) -> None:
        """La comprobación de verdad: dónde acaba el enemigo."""
        from src.framework.entities.enemy_base import EnemyState

        charger._is_charging = True
        charger._charge_timer = 0.5
        charger.stun(0.4)
        x0 = charger.position.x

        for _ in range(int((0.4 + charger.RECOVER_DURATION) * 60) + 10):
            charger._run_state_machine(DT)

        assert charger.state != EnemyState.DYING
        assert abs(charger.position.x - x0) < 60.0, (
            f"se desplazó {abs(charger.position.x - x0):.0f} px tras el "
            "aturdimiento: la embestida se reanudó"
        )

    def test_un_cadaver_no_cambia(self, charger) -> None:
        from src.framework.entities.enemy_base import EnemyState

        charger.state = EnemyState.DYING
        charger._is_charging = True

        charger.stun(0.9)

        assert charger.state == EnemyState.DYING
        assert charger._is_charging is True, (
            "un cadáver no se aturde, así que tampoco se le toca la embestida"
        )


class TestElWalkerTampoco:
    """`EnemyWalker` lleva la misma bandera y el mismo problema."""

    def test_aturdir_cancela_su_carga(self) -> None:
        from src.framework.entities.enemy_walker import EnemyWalker

        walker = EnemyWalker(pygame.Vector2(200.0, 300.0))
        walker._is_charging = True

        walker.stun(0.9)

        assert walker._is_charging is False


class TestElTemporizadorTieneUnSoloDueno:
    """`_stun_timer` es de `EnemyBase`. El charger tenía el suyo con el mismo
    nombre y los dos lo decrementaban."""

    def test_el_charger_no_pisa_el_temporizador_de_la_base(self, charger) -> None:
        charger.stun(1.0)
        assert charger._stun_timer == pytest.approx(1.0)

        # Un fotograma de la máquina de estados: sólo la rama STUNNED de la
        # base debe descontar, y una sola vez.
        charger._run_state_machine(DT)

        assert charger._stun_timer == pytest.approx(1.0 - DT), (
            "alguien más descontó del mismo temporizador"
        )

    def test_la_recuperacion_propia_del_charger_sigue_funcionando(
        self, charger,
    ) -> None:
        """Tras embestir, el charger se queda expuesto por su cuenta. Eso es
        suyo y no debe haberse perdido al separar los temporizadores."""
        charger.state = charger.state.__class__.ALERT
        charger._is_charging = True
        charger._charge_timer = 0.0
        charger._collision_rects = []

        charger._alert_behavior(DT)

        assert charger._is_stunned is True
        assert charger._is_charging is False
