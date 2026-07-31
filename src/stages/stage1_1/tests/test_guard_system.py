"""
Module: test_guard_system
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: N/A
Description: Pruebas de la guardia mantenida.

El motor solo trae un parry con ventana de 0,2 s que exige atinar el
momento (player_states.py:113). Aquí se añade una defensa sencilla de
mantener pulsado, sin tocar ningún archivo del profesor.

Ejecutar toda la suite con:
   python -m pytest src/stages/stage1_1/tests/ -v
"""
from __future__ import annotations

import pygame
import pytest

from src.stages.stage1_1.combat.guard_system import GuardSystem


class _JugadorFalso:
    def __init__(self, en_suelo: bool = True, x: float = 100.0) -> None:
        self.is_grounded = en_suelo
        self.dano_recibido = 0.0
        self.golpes = 0
        self.position = pygame.Vector2(x, 200.0)
        self.velocity = pygame.Vector2(0.0, 0.0)
        self.rect = pygame.Rect(int(x), 200, 20, 32)

    def apply_damage(self, amount, source_position, knockback_force=150.0):
        self.dano_recibido += amount
        self.golpes += 1


def _teclado(*pulsadas: int):
    """Devuelve un callable(tecla)->bool con las teclas indicadas pulsadas."""
    return lambda k: k in pulsadas


# ── Lectura del teclado ─────────────────────────────────────────────

def test_detecta_cualquiera_de_las_teclas_de_guardia() -> None:
    for tecla in GuardSystem.TECLAS:
        assert GuardSystem.hay_tecla_de_guardia(_teclado(tecla))


def test_sin_tecla_pulsada_no_hay_guardia() -> None:
    assert not GuardSystem.hay_tecla_de_guardia(_teclado())


def test_otra_tecla_no_activa_la_guardia() -> None:
    assert not GuardSystem.hay_tecla_de_guardia(_teclado(pygame.K_p))


# ── Bloqueo del daño ────────────────────────────────────────────────

def test_sin_guardia_el_dano_entra_normal() -> None:
    guardia = GuardSystem()
    jugador = _JugadorFalso()
    guardia.enganchar(jugador)

    guardia.actualizar(jugador, tecla_pulsada=False)
    jugador.apply_damage(1.0, (0, 0))

    assert jugador.dano_recibido == pytest.approx(1.0)


def test_con_la_guardia_puesta_el_dano_se_bloquea() -> None:
    """Es lo que se pidió: mantener pulsado y no recibir daño, sin timing."""
    guardia = GuardSystem()
    jugador = _JugadorFalso()
    guardia.enganchar(jugador)

    guardia.actualizar(jugador, tecla_pulsada=True)
    jugador.apply_damage(1.0, (0, 0))
    jugador.apply_damage(0.5, (0, 0))

    assert jugador.dano_recibido == pytest.approx(0.0)
    assert guardia.bloqueos == 2


def test_al_soltar_la_tecla_el_dano_vuelve_a_entrar() -> None:
    guardia = GuardSystem()
    jugador = _JugadorFalso()
    guardia.enganchar(jugador)

    guardia.actualizar(jugador, tecla_pulsada=True)
    jugador.apply_damage(1.0, (0, 0))
    guardia.actualizar(jugador, tecla_pulsada=False)
    jugador.apply_damage(1.0, (0, 0))

    assert jugador.dano_recibido == pytest.approx(1.0)


def test_en_el_aire_no_se_puede_defender() -> None:
    """Bloquear cayendo trivializaría el nivel: hay que pisar suelo."""
    guardia = GuardSystem()
    jugador = _JugadorFalso(en_suelo=False)
    guardia.enganchar(jugador)

    guardia.actualizar(jugador, tecla_pulsada=True)
    jugador.apply_damage(1.0, (0, 0))

    assert guardia.activo is False
    assert jugador.dano_recibido == pytest.approx(1.0)


# ── Enganche y desenganche ──────────────────────────────────────────

def test_desenganchar_restaura_el_apply_damage_original() -> None:
    """No debe quedar el envoltorio puesto al salir del escenario.

    Se comprueba sobre `vars(jugador)` y no con `is`: `apply_damage` es un
    método enlazado, y cada acceso crea un objeto distinto, así que `is`
    daría False incluso estando bien restaurado. Lo que importa es que no
    quede un atributo de instancia tapando el método de la clase.
    """
    guardia = GuardSystem()
    jugador = _JugadorFalso()
    assert "apply_damage" not in vars(jugador)

    guardia.enganchar(jugador)
    assert "apply_damage" in vars(jugador)          # el envoltorio está puesto

    guardia.desenganchar()
    assert "apply_damage" not in vars(jugador)      # y se quitó


def test_tras_desenganchar_el_dano_vuelve_a_entrar() -> None:
    guardia = GuardSystem()
    jugador = _JugadorFalso()
    guardia.enganchar(jugador)
    guardia.actualizar(jugador, tecla_pulsada=True)
    guardia.desenganchar()

    jugador.apply_damage(1.0, (0, 0))

    assert jugador.dano_recibido == pytest.approx(1.0)


def test_enganchar_dos_veces_no_apila_envoltorios() -> None:
    guardia = GuardSystem()
    jugador = _JugadorFalso()

    guardia.enganchar(jugador)
    guardia.enganchar(jugador)
    guardia.desenganchar()

    assert "apply_damage" not in vars(jugador)


def test_desenganchar_sin_haber_enganchado_no_revienta() -> None:
    GuardSystem().desenganchar()


# ── Inmovilidad: con la guardia puesta no se puede caminar ──────────

def test_con_la_guardia_puesta_el_jugador_no_avanza() -> None:
    """Defenderse cuesta movilidad: quedás anclado en el sitio."""
    guardia = GuardSystem()
    jugador = _JugadorFalso(x=100.0)
    guardia.actualizar(jugador, tecla_pulsada=True)

    x_antes = jugador.position.x
    jugador.position.x += 30.0          # el motor lo movió por el input
    jugador.velocity.x = 90.0

    guardia.congelar(jugador, x_antes)

    assert jugador.position.x == pytest.approx(100.0)
    assert jugador.velocity.x == pytest.approx(0.0)
    assert jugador.rect.x == 100


def test_sin_guardia_el_jugador_se_mueve_normal() -> None:
    guardia = GuardSystem()
    jugador = _JugadorFalso(x=100.0)
    guardia.actualizar(jugador, tecla_pulsada=False)

    x_antes = jugador.position.x
    jugador.position.x += 30.0
    jugador.velocity.x = 90.0

    guardia.congelar(jugador, x_antes)

    assert jugador.position.x == pytest.approx(130.0)
    assert jugador.velocity.x == pytest.approx(90.0)


def test_congelar_no_afecta_la_caida() -> None:
    """Solo se ancla la horizontal: la gravedad debe seguir funcionando,
    o el jugador se quedaría flotando al defenderse en un borde."""
    guardia = GuardSystem()
    jugador = _JugadorFalso(x=100.0)
    guardia.actualizar(jugador, tecla_pulsada=True)

    x_antes = jugador.position.x
    jugador.position.y += 12.0
    jugador.velocity.y = 240.0

    guardia.congelar(jugador, x_antes)

    assert jugador.position.y == pytest.approx(212.0)
    assert jugador.velocity.y == pytest.approx(240.0)


def test_congelar_sin_jugador_no_revienta() -> None:
    GuardSystem().congelar(None, 0.0)
