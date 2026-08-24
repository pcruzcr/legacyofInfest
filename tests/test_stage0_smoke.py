"""
Module: test_stage0_smoke
System: tests
Description: Automatable smoke tests for Stage 0 integration.
These verify that Stage 0 loads without exceptions and matches the
design document (07_STAGE0_DESIGN.md) in key structural properties.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pygame

from src.framework.entities import entity_factory
from src.framework.stage.stage_loader import StageData, StageLoader

STAGE0_TMX = Path("assets/maps/stage0/stage0.tmx")


class TestStage0Smoke:
    def setup_method(self) -> None:
        """Registra el bestiario completo, como hace el juego.

        Antes esto vaciaba el registro y daba de alta tres tipos a mano
        (Walker, Flying, Shooter). El efecto era que stage0 se cargaba **sin
        cinco de sus enemigos** —Charger, Archer, Brute, Caster y Assassin, que
        el mapa sí coloca— y a continuación se afirmaba `len(entity_list) >= 1`,
        que se cumplía con los que sobrevivían. La prueba pasaba describiendo
        un escenario que el juego nunca carga, y habría seguido pasando si
        stage0 perdiera esos cinco enemigos de verdad (AUD-056).
        """
        _init_pygame_display()
        entity_factory.ensure_registered()

    def test_stage0_loads_without_exception(self) -> None:
        data = StageLoader.load(STAGE0_TMX)
        assert isinstance(data, StageData)

    def test_stage0_has_checkpoints(self) -> None:
        data = StageLoader.load(STAGE0_TMX)
        assert len(data.checkpoints) >= 1

    def test_stage0_has_next_trigger(self) -> None:
        data = StageLoader.load(STAGE0_TMX)
        assert data.next_trigger is not None

    def test_stage0_has_enemies(self) -> None:
        """Los ocho tipos que el mapa coloca, no «al menos uno».

        `>= 1` es una tautología: se cumple mientras quede un solo enemigo, así
        que no distingue «el escenario está bien» de «se cargaron 3 de 9».
        Nombrar la población esperada es lo que hace que la prueba falle
        cuando alguien rompe el registro de entidades o edita el mapa sin
        querer.
        """
        data = StageLoader.load(STAGE0_TMX)
        by_type = Counter(type(e).__name__ for e in data.entity_list)

        assert by_type == {
            "EnemyWalker": 2,
            "EnemyFlying": 1,
            "EnemyShooter": 1,
            "EnemyCharger": 1,
            "EnemyArcher": 1,
            "EnemyBrute": 1,
            "EnemyCaster": 1,
            "EnemyAssassin": 1,
        }, f"la población de stage0 cambió: {dict(by_type)}"

    def test_stage0_uses_more_than_the_three_basic_archetypes(self) -> None:
        """stage0 es la referencia que copian los estudiantes.

        Si sólo mostrara Walker/Flying/Shooter, nadie descubriría que existen
        Charger, Archer, Brute, Caster o Assassin: el mapa de ejemplo es la
        documentación que la gente lee de verdad.
        """
        data = StageLoader.load(STAGE0_TMX)
        kinds = {type(e).__name__ for e in data.entity_list}
        assert len(kinds) >= 8, f"stage0 sólo demuestra {sorted(kinds)}"


def _init_pygame_display() -> None:
    if not pygame.display.get_init():
        pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
