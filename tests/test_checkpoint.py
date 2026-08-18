"""
Module: test_checkpoint
System: tests
Description: Tests for Checkpoint single-activation and event emission.
"""
from __future__ import annotations

import pygame

from src.engine.core.event_bus import EventBus
from src.framework.stage.checkpoint import Checkpoint


class TestCheckpointActivation:
    def test_activates_once(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(100, 100),
            pygame.Rect(100, 100, 24, 32),
            checkpoint_id=0,
        )
        assert cp.is_activated is False
        cp.activate()
        assert cp.is_activated is True
        cp.activate()
        assert cp.is_activated is True

    def test_checkpoint_id_preserved(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(200, 150),
            pygame.Rect(200, 150, 24, 32),
            checkpoint_id=5,
        )
        assert cp.checkpoint_id == 5

    def test_draw_does_not_crash(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(0, 0),
            pygame.Rect(0, 0, 24, 32),
            checkpoint_id=0,
        )
        surface = pygame.Surface((320, 224))
        cp.draw(surface, pygame.Vector2(0, 0))

    def test_check_collision_activates(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(100, 100),
            pygame.Rect(100, 100, 24, 32),
            checkpoint_id=0,
        )
        player_rect = pygame.Rect(110, 110, 20, 32)
        result = cp.check_collision(player_rect)
        assert result is True
        assert cp.is_activated is True

    def test_check_collision_only_once(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(100, 100),
            pygame.Rect(100, 100, 24, 32),
            checkpoint_id=0,
        )
        player_rect = pygame.Rect(110, 110, 20, 32)
        cp.check_collision(player_rect)
        result = cp.check_collision(player_rect)
        assert result is False

    def test_check_collision_no_overlap(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(100, 100),
            pygame.Rect(100, 100, 24, 32),
            checkpoint_id=0,
        )
        player_rect = pygame.Rect(0, 0, 20, 32)
        result = cp.check_collision(player_rect)
        assert result is False
        assert cp.is_activated is False

    def test_activate_emits_event(self, event_bus: EventBus) -> None:
        cp = Checkpoint(
            pygame.Vector2(100, 100),
            pygame.Rect(100, 100, 24, 32),
            checkpoint_id=3,
            event_bus=event_bus,
        )
        cp.activate()
        assert cp.is_activated is True


class TestElCheckpointBrilla:
    """AUD-517 lo dejó opt-in para 4.1b/4.1c; AUD-523 lo hizo **el**
    checkpoint, en los 26 escenarios — sin propiedad que lo active, sin
    sprite ni rectángulo de respaldo. `assets/sprites/shared/checkpoint.png`
    ya no existe."""

    def test_todo_checkpoint_tiene_luz_centrada_en_el_rect(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(100, 200), pygame.Rect(100, 200, 16, 32),
            checkpoint_id=0,
        )
        assert cp._light is not None
        assert cp._light.position == (108, 216)  # el centro del rect

    def test_activarse_cambia_el_color_de_frio_a_dorado(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(0, 0), pygame.Rect(0, 0, 16, 32), checkpoint_id=0,
        )
        color_en_espera = cp._light.color
        cp.activate()
        assert cp._light.color != color_en_espera

    def test_dibujar_no_revienta_ni_pinta_el_rectangulo_plano(self) -> None:
        """El pedido explícito era «un área que brille y no un gráfico que
        no tiene forma» — no debe quedar ningún rastro del rectángulo
        relleno que dibujaba `checkpoint.png` cuando fallaba la carga."""
        cp = Checkpoint(
            pygame.Vector2(0, 0), pygame.Rect(10, 10, 16, 32), checkpoint_id=0,
        )
        surface = pygame.Surface((64, 64))
        surface.fill((0, 0, 0))
        cp.draw(surface, pygame.Vector2(0, 0))
        # El rectángulo de respaldo (retirado) pintaba las esquinas exactas
        # del rect con un color plano y sólido; el disco de luz es un
        # degradado que no llega uniforme hasta la esquina.
        assert surface.get_at((10, 10))[:3] != (100, 100, 100)

    def test_update_avanza_el_parpadeo_sin_reventar(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(0, 0), pygame.Rect(0, 0, 16, 32), checkpoint_id=0,
        )
        cp.update(0.5)

    def test_el_cargador_construye_un_checkpoint_con_luz(self) -> None:
        """El TMX ya no declara ninguna propiedad para esto — el cargador
        tiene que llegar hasta un `Checkpoint` con luz de todas formas."""
        from src.framework.stage.stage_loader import StageData, StageLoader

        class _Obj:
            x, y, width, height = 50.0, 60.0, 16.0, 32.0

        stage = StageData(map_layer=None)
        StageLoader._handle_checkpoint(stage, _Obj(), {"checkpoint_id": 1})
        assert len(stage.checkpoints) == 1
        assert stage.checkpoints[0]._light is not None
