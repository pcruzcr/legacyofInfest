"""AUD-257 — la escala de fase y el teletransporte no los usaba nadie.

El defecto
==========
`BossPhase.escala` y `BossBase.teletransportar` están en `GAP-032` desde que se
midió: la primera **se definía y nunca se aplicaba** —`escala_de_fase` devolvía
un número que ningún dibujado ni ninguna caja leía— y el segundo tenía cero
llamantes en todo el repositorio.

Es el mismo defecto que AUD-053 arregló para `speed_multiplier`, que se leía y
se tiraba con un `pass`. Un campo de fase que no cambia nada es decorativo, y
un estudiante que lo declare en su jefe concluye, con razón, que el motor está
roto.

Lo que hace este cambio
-----------------------
1. `escala_de_fase` **se aplica de verdad**: al terminar la transición, la caja
   del jefe crece o mengua, anclada por los pies para que no se hunda en el
   suelo ni flote, y el sprite se dibuja a esa misma escala.
2. `boss_venado` —el jefe de referencia del profesor, el que los estudiantes
   copian— declara las dos: crece en su segunda fase y se teletransporta al
   cambiar. Así el patrón queda escrito en el material que se copia, no sólo
   en la clase base.

`boss_rey`, `boss_paburu` y `boss_gavilan` son entregas de estudiantes y no se
tocan (invariante 1 de `CLAUDE.md`).
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.entities.boss_base import BossBase, BossPhase


class _JefeDePrueba(BossBase):
    def _get_animation_key(self) -> str:
        return "idle"

    def _patrol_behavior(self, dt: float) -> None:
        pass

    def _alert_behavior(self, dt: float) -> None:
        pass

    def _build_hitbox(self) -> pygame.Rect:
        return self.rect.copy()

    def _build_hurtbox(self) -> pygame.Rect:
        return self.rect.copy()


@pytest.fixture
def jefe(event_bus):
    j = _JefeDePrueba(pygame.Vector2(100, 100), max_health=10.0)
    j.set_event_bus(event_bus)
    j.set_phases([
        BossPhase(phase_index=0, health_threshold=1.0, attack_patterns=[]),
        BossPhase(phase_index=1, health_threshold=0.5, attack_patterns=[], escala=2.0),
    ])
    return j


class TestLaEscalaDeFaseSeAplica:
    def test_la_caja_crece_al_entrar_en_la_fase_escalada(self, jefe) -> None:
        ancho_antes = jefe.rect.width
        alto_antes = jefe.rect.height

        jefe._finish_phase_transition()

        assert jefe.rect.width == ancho_antes * 2
        assert jefe.rect.height == alto_antes * 2

    def test_los_pies_no_se_mueven_al_crecer(self, jefe) -> None:
        """Un jefe que crece desde la esquina se hunde medio cuerpo en el suelo.

        Se ancla por abajo: crece hacia arriba y hacia los lados, que es lo
        que hace cualquier transformación de personaje.
        """
        pies_antes = jefe.rect.bottom
        centro_antes = jefe.rect.centerx

        jefe._finish_phase_transition()

        assert jefe.rect.bottom == pies_antes
        assert jefe.rect.centerx == centro_antes

    def test_una_fase_sin_escala_no_toca_nada(self, event_bus) -> None:
        j = _JefeDePrueba(pygame.Vector2(100, 100), max_health=10.0)
        j.set_event_bus(event_bus)
        j.set_phases([
            BossPhase(phase_index=0, health_threshold=1.0, attack_patterns=[]),
            BossPhase(phase_index=1, health_threshold=0.5, attack_patterns=[]),
        ])
        ancho_antes, alto_antes = j.rect.width, j.rect.height

        j._finish_phase_transition()

        assert (j.rect.width, j.rect.height) == (ancho_antes, alto_antes)

    def test_la_posicion_sigue_a_la_caja(self, jefe) -> None:
        """`position` es la fuente de verdad del motor; si sólo creciera el
        rect, el primer `clamp_to_arena` deshacía el crecimiento."""
        jefe._finish_phase_transition()

        assert int(jefe.position.x) == jefe.rect.x
        assert int(jefe.position.y) == jefe.rect.y


class TestElJefeDeReferenciaLasUsa:
    """El patrón tiene que estar en el material que los estudiantes copian."""

    def test_boss_venado_declara_una_fase_con_escala(self) -> None:
        from src.stages.boss_venado.boss_venado import BossVenado

        venado = BossVenado(pygame.Vector2(0, 0))
        escalas = [float(getattr(f, "escala", 1.0)) for f in venado.phases]

        assert any(e != 1.0 for e in escalas), (
            "ninguna fase del jefe de referencia declara escala: el campo "
            "sigue sin aparecer en el material que se copia"
        )

    def test_boss_venado_se_teletransporta_al_cambiar_de_fase(self) -> None:
        from pathlib import Path

        fuente = (Path(__file__).resolve().parents[1] / "src" / "stages"
                  / "boss_venado" / "boss_venado.py").read_text(encoding="utf-8")

        assert "teletransportar(" in fuente, (
            "teletransportar sigue con cero llamantes: el método existe para "
            "que un jefe lo use en su transición de fase"
        )
