"""Parar un ataque debe aturdir al que lo lanzó — AUD-206.

El hueco, medido antes de tocar nada
====================================
Las dos mitades existían y no se hablaban:

* `EnemyBase.stun()` y la rama `STUNNED` de la máquina de estados estaban
  completas desde AUD-051, con su salida a `RECOVER` y todo. Pero `stun()`
  **no tenía ni una sola llamada en producción**: sólo lo invocaban las
  pruebas de `test_enemy_state_machine.py`. El único sitio del motor que
  miraba `STUNNED` era `boss_base`, y sólo para leerlo.
* El parry del jugador (`ParryState` + los bloques de `_check_player_contact`)
  desviaba el golpe y ponía al enemigo en `HURT` durante 0,3 s. `HURT` no es
  una ventana de castigo: es el mismo estado en el que cae el enemigo cuando
  le pegas de forma normal, y sale de él directo a `ALERT`.

Consecuencia jugable: parar era, mecánicamente, una esquiva cara. Costaba una
ventana de 0,2 s de precisión y devolvía lo mismo que apartarse. El combate
premiaba esquivar y nunca leer.

Lo que estas pruebas fijan
--------------------------
Un parry acertado mete al enemigo en `STUNNED` durante
`EnemyBase.PARRY_STUN_DURATION`, y de ahí sale a `RECOVER` — o sea, a la
ventana de castigo que ya existía. Se comprueba por **el camino del motor**
(`_check_player_contact`, que es lo que llama `StageScene`), no llamando a
`stun()` a mano: llamar a `stun()` a mano es justamente lo que hacían las
pruebas que dejaron pasar este hueco durante toda la vida del estado.
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


class _Bus:
    def __init__(self) -> None:
        self.emitidos: list[str] = []

    def emit(self, evento: str, **_datos) -> None:
        self.emitidos.append(evento)

    def subscribe(self, *_a, **_k) -> None:
        pass


def _jugador(x: float = 200.0, y: float = 300.0):
    from src.framework.entities.player import Player

    jugador = Player(pygame.Vector2(x, y))
    jugador._invincibility_timer = 0.0
    return jugador


def _walker_encima_del_jugador(jugador):
    """Un walker pegado al jugador, con el bus falso y sin enfriamientos."""
    from src.framework.entities.enemy_walker import EnemyWalker

    walker = EnemyWalker(pygame.Vector2(jugador.position.x, jugador.position.y))
    walker._event_bus = _Bus()
    walker._contact_cooldown = 0.0
    walker._charge_cooldown = 99.0  # aísla el parry de la carga
    walker.position.update(jugador.position)
    walker.rect.center = jugador.rect.center
    walker._update_rects()
    return walker


def _parando(jugador):
    """Deja al jugador dentro de la ventana activa de parry."""
    jugador._parry_active = True
    jugador._parry_window = 0.2
    jugador._parry_success = False


class TestUnParryAcertadoAturde:
    def test_el_enemigo_parado_queda_aturdido_no_solo_dolorido(self) -> None:
        from src.framework.entities.enemy_base import EnemyState

        jugador = _jugador()
        walker = _walker_encima_del_jugador(jugador)
        assert walker.hurtbox.colliderect(jugador.hurtbox), (
            "el montaje no llega a solaparse; la prueba no probaría nada"
        )
        _parando(jugador)

        walker._check_player_contact(jugador)  # el camino del motor

        assert jugador._parry_success is True, "el parry ni siquiera se registró"
        assert walker.state == EnemyState.STUNNED, (
            "el parry dejó al enemigo en HURT: eso es lo mismo que un golpe "
            "normal, y sale directo a ALERT. Parar no abre ventana de castigo."
        )

    def test_el_aturdimiento_dura_lo_que_declara_la_clase(self) -> None:
        jugador = _jugador()
        walker = _walker_encima_del_jugador(jugador)
        _parando(jugador)

        walker._check_player_contact(jugador)

        assert walker._stun_timer == pytest.approx(walker.PARRY_STUN_DURATION)
        assert walker.PARRY_STUN_DURATION > 0.3, (
            "un aturdimiento igual o menor que el HURT de 0,3 s que había "
            "antes no cambia nada para quien juega"
        )

    def test_del_aturdimiento_se_sale_a_la_ventana_de_castigo(self) -> None:
        """STUNNED → RECOVER. Es lo que convierte parar en una oportunidad."""
        from src.framework.entities.enemy_base import EnemyState

        jugador = _jugador()
        walker = _walker_encima_del_jugador(jugador)
        walker.set_player_ref(jugador.rect)
        _parando(jugador)

        walker._check_player_contact(jugador)
        for _ in range(int(walker.PARRY_STUN_DURATION * 60) + 3):
            walker._run_state_machine(DT)

        assert walker.state == EnemyState.RECOVER, (
            "tras el aturdimiento el enemigo volvió a perseguir sin pausa"
        )

    def test_sin_parry_el_contacto_sigue_haciendo_dano(self) -> None:
        """El control: aturdir no puede ser el camino por defecto."""
        from src.framework.entities.enemy_base import EnemyState

        jugador = _jugador()
        walker = _walker_encima_del_jugador(jugador)
        vida = jugador.current_health

        walker._check_player_contact(jugador)

        assert jugador.current_health < vida, "el contacto dejó de doler"
        assert walker.state != EnemyState.STUNNED, (
            "el enemigo se aturde solo con tocar al jugador"
        )

    def test_un_cadaver_no_se_aturde(self) -> None:
        from src.framework.entities.enemy_base import EnemyState

        jugador = _jugador()
        walker = _walker_encima_del_jugador(jugador)
        walker.state = EnemyState.DYING
        _parando(jugador)

        walker._check_player_contact(jugador)

        assert walker.state == EnemyState.DYING

    def test_un_enemigo_por_los_aires_no_se_queda_colgado(self) -> None:
        """LAUNCHED tiene su propia rama con gravedad; STUNNED lo congelaría."""
        from src.framework.entities.enemy_base import EnemyState

        jugador = _jugador()
        walker = _walker_encima_del_jugador(jugador)
        walker.state = EnemyState.LAUNCHED
        _parando(jugador)

        walker._check_player_contact(jugador)

        assert walker.state == EnemyState.LAUNCHED


class TestParryDeProyectil:
    """Desviar una flecha también interrumpe a quien la disparó.

    Un arquero aturdido no vuelve a disparar durante la ventana, que es lo
    único que hace útil parar a distancia: da el hueco para acercarse.
    """

    def _arquero_con_flecha_encima(self, jugador):
        from src.framework.entities.enemy_archer import EnemyArcher

        arquero = EnemyArcher(pygame.Vector2(100.0, 300.0))
        arquero._event_bus = _Bus()
        arquero._active_projectiles.clear()
        arquero._shoot_cooldown = 0.0
        arquero._player_ref = jugador.rect
        arquero._fire_arc()
        for proyectil in arquero._active_projectiles:
            proyectil.rect.center = jugador.rect.center
            proyectil.position.update(jugador.position)
        return arquero

    def test_desviar_la_flecha_aturde_al_arquero(self) -> None:
        from src.framework.entities.enemy_base import EnemyState

        jugador = _jugador()
        arquero = self._arquero_con_flecha_encima(jugador)
        if not arquero._active_projectiles:
            pytest.skip("el arquero no llegó a disparar en este montaje")
        _parando(jugador)

        arquero._check_player_contact(jugador)

        assert jugador._parry_success is True
        assert arquero.state == EnemyState.STUNNED, (
            "parar una flecha la borraba y ya: el arquero seguía su rutina y "
            "volvía a disparar como si nada"
        )
