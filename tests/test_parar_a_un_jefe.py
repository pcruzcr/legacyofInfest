"""Parar el ataque de un jefe hace algo — AUD-243.

El hueco, medido
================
La cadena del parry de jefe estaba **entera y desconectada por arriba**:

    BossAttack(parriable=True)  →  AttackScheduler.se_puede_desviar
    →  AttackScheduler.desviar()  →  BossBase.recibir_parry()  →  ???

`recibir_parry()` se describe a sí misma como «**el punto de entrada de la
mecánica**», y no tenía **un solo llamante en todo el repositorio** — ni en
producción ni en pruebas. Medido con `grep -rn "recibir_parry"`: una línea, su
propia definición.

Consecuencia: `BossAttack.parriable`, `aturde_al_parry` y `se_puede_desviar`
existían, se probaban por unidad y no cambiaban nada en ningún jefe. El campo
`parriable` era decorativo.

Es exactamente el mismo defecto que AUD-206 arregló para los enemigos
normales, en la mitad de los jefes. `docs/56_FASE_5_ECS_Y_MECANICAS.md` lista
«Parry del jefe (`BossAttack.parriable`) — Sekiro, Katana ZERO, MGR» bajo el
epígrafe «Y en código:».

Lo que fija esta prueba
-----------------------
El parry que ya funciona contra cualquier enemigo (AUD-206, por contacto)
consulta ahora al jefe: si tiene un ataque parable en curso, manda su
`aturde_al_parry` y el ataque entra en enfriamiento completo. Si no lo tiene,
se aplica el aturdimiento genérico de siempre, así que un jefe sin ataques
parables se comporta igual que antes.
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


def _jefe_con_ataque(parriable: bool = True, aturde: float = 2.5):
    """Un jefe mínimo con un ataque en curso, parable o no."""
    from src.framework.entities.boss_base import BossBase
    from src.framework.entities.boss_kit import AttackScheduler, BossAttack
    from src.framework.entities.enemy_walker import EnemyWalker

    # Se usa una subclase concreta mínima: `BossBase` es abstracta.
    class _Jefe(BossBase):
        def _patrol_behavior(self, dt: float) -> None: ...
        def _alert_behavior(self, dt: float) -> None: ...
        def _get_animation_key(self) -> str: return "walk"
        def _build_hitbox(self) -> pygame.Rect: return self.caja_ajustada()
        def _build_hurtbox(self) -> pygame.Rect: return self.caja_ajustada()

    jefe = _Jefe(pygame.Vector2(200.0, 300.0))
    jefe._event_bus = _Bus()
    jefe._contact_cooldown = 0.0
    ataque = BossAttack(
        name="EMBESTIDA", windup=1.0, active=0.5, recover=1.0,
        parriable=parriable, aturde_al_parry=aturde, cooldown=3.0,
    )
    jefe.attacks = AttackScheduler([ataque])
    # Se arranca el ataque y se deja en WINDUP, que es cuando se puede parar.
    jefe.attacks.update(DT, distance=10.0, phase=0)
    assert jefe.attacks.current is not None, "el montaje no llegó a atacar"
    _ = EnemyWalker  # el import documenta que el jefe también es un EnemyBase
    return jefe


def _pegados(jefe, jugador) -> None:
    jefe.position.update(jugador.position)
    jefe.rect.center = jugador.rect.center
    jefe._update_rects()


def _parando(jugador) -> None:
    jugador._parry_active = True
    jugador._parry_window = 0.2
    jugador._parry_success = False


class TestElPuntoDeEntradaSeLlama:
    def test_recibir_parry_tiene_llamante_en_produccion(self) -> None:
        """La comprobación que habría evitado todo esto.

        Se busca en `src/`, no en las pruebas: una función que sólo llaman las
        pruebas es justamente el defecto, no la solución.
        """
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent
        llamantes = [
            p for p in (raiz / "src").rglob("*.py")
            if "recibir_parry" in p.read_text(encoding="utf-8", errors="replace")
            and p.name != "boss_base.py"
        ]
        assert llamantes, (
            "`recibir_parry` sigue sin llamante: la cadena del parry de jefe "
            "está escrita entera y desconectada por arriba"
        )


class TestPararUnAtaqueParable:
    def test_manda_el_aturdimiento_que_declara_el_ataque(self) -> None:
        jugador = _jugador()
        jefe = _jefe_con_ataque(parriable=True, aturde=2.5)
        _pegados(jefe, jugador)
        _parando(jugador)

        jefe._check_player_contact(jugador)

        assert jugador._parry_success is True
        assert jefe._stun_timer == pytest.approx(2.5), (
            f"se aplicó {jefe._stun_timer}: el aturdimiento genérico de "
            "`PARRY_STUN_DURATION` en vez del que declara el ataque"
        )

    def test_el_jefe_queda_aturdido(self) -> None:
        from src.framework.entities.enemy_base import EnemyState

        jugador = _jugador()
        jefe = _jefe_con_ataque()
        _pegados(jefe, jugador)
        _parando(jugador)

        jefe._check_player_contact(jugador)

        assert jefe.state == EnemyState.STUNNED

    def test_el_ataque_entra_en_enfriamiento_completo(self) -> None:
        """Un jefe al que desvías y que repite al instante castiga el acierto."""
        jugador = _jugador()
        jefe = _jefe_con_ataque()
        _pegados(jefe, jugador)
        _parando(jugador)

        jefe._check_player_contact(jugador)

        assert jefe.attacks.current is None, "el ataque siguió en curso"

    def test_se_avisa_por_el_bus(self) -> None:
        """El aviso es lo que permite al escenario reaccionar al desvío."""
        from src.engine.core.events import Events

        jugador = _jugador()
        jefe = _jefe_con_ataque()
        _pegados(jefe, jugador)
        _parando(jugador)

        jefe._check_player_contact(jugador)

        assert Events.BOSS_ATTACK in jefe._event_bus.emitidos


class TestLoQueNoCambia:
    """Los controles. Un jefe sin ataques parables se comporta como antes."""

    def test_un_ataque_no_parable_cae_al_aturdimiento_generico(self) -> None:
        jugador = _jugador()
        jefe = _jefe_con_ataque(parriable=False)
        _pegados(jefe, jugador)
        _parando(jugador)

        jefe._check_player_contact(jugador)

        assert jefe._stun_timer == pytest.approx(jefe.PARRY_STUN_DURATION), (
            "un ataque marcado como no parable no puede dar la recompensa "
            "grande; el parry sigue valiendo, pero lo genérico"
        )

    def test_un_enemigo_normal_no_cambia(self) -> None:
        """AUD-206 no puede haberse movido."""
        from src.framework.entities.enemy_walker import EnemyWalker

        jugador = _jugador()
        walker = EnemyWalker(pygame.Vector2(200.0, 300.0))
        walker._event_bus = _Bus()
        walker._contact_cooldown = 0.0
        walker._charge_cooldown = 99.0
        _pegados(walker, jugador)
        _parando(jugador)

        walker._check_player_contact(jugador)

        assert walker._stun_timer == pytest.approx(walker.PARRY_STUN_DURATION)

    def test_sin_parry_el_jefe_sigue_haciendo_dano(self) -> None:
        jugador = _jugador()
        jefe = _jefe_con_ataque()
        _pegados(jefe, jugador)
        vida = jugador.current_health

        jefe._check_player_contact(jugador)

        assert jugador.current_health < vida
