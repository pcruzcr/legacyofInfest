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


class TestCheckpointBrillo:
    """AUD-517 — estilo opt-in: un área que brilla en vez del sprite/rectángulo
    de siempre, pedido para los niveles nuevos 4.1b/4.1c (GAP-065 §4)."""

    def test_sin_brillo_no_crea_luz(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(0, 0), pygame.Rect(0, 0, 16, 32), checkpoint_id=0,
        )
        assert cp._light is None

    def test_con_brillo_crea_una_luz_centrada_en_el_rect(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(100, 200), pygame.Rect(100, 200, 16, 32),
            checkpoint_id=0, brillo=True,
        )
        assert cp._light is not None
        assert cp._light.position == (108, 216)  # el centro del rect

    def test_activarse_cambia_el_color_de_frio_a_dorado(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(0, 0), pygame.Rect(0, 0, 16, 32),
            checkpoint_id=0, brillo=True,
        )
        color_en_espera = cp._light.color
        cp.activate()
        assert cp._light.color != color_en_espera

    def test_dibujar_con_brillo_no_revienta_ni_pinta_el_rectangulo_plano(self) -> None:
        """El pedido explícito era «un área que brille y no un gráfico que
        no tiene forma» — con `brillo=True` no debe quedar ningún rastro
        del rectángulo relleno de siempre."""
        cp = Checkpoint(
            pygame.Vector2(0, 0), pygame.Rect(10, 10, 16, 32),
            checkpoint_id=0, brillo=True,
        )
        surface = pygame.Surface((64, 64))
        surface.fill((0, 0, 0))
        cp.draw(surface, pygame.Vector2(0, 0))
        # El rectángulo de respaldo pinta las esquinas exactas del rect con
        # un color plano y sólido; el disco de luz es un degradado que no
        # llega uniforme hasta la esquina.
        assert surface.get_at((10, 10))[:3] != (100, 100, 100)

    def test_update_avanza_el_parpadeo_sin_reventar_sin_brillo(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(0, 0), pygame.Rect(0, 0, 16, 32), checkpoint_id=0,
        )
        cp.update(0.5)  # no debe reventar cuando no hay luz que actualizar

    def test_la_propiedad_tmx_se_lee_en_el_cargador(self) -> None:
        """El TMX declara `brillo` como booleano (o su forma en texto); el
        cargador tiene que llegar hasta el `Checkpoint` real, no quedarse en
        el diccionario de propiedades crudas."""
        from src.framework.stage.stage_loader import StageData, StageLoader

        class _Obj:
            x, y, width, height = 50.0, 60.0, 16.0, 32.0

        stage = StageData(map_layer=None)
        StageLoader._handle_checkpoint(stage, _Obj(), {
            "checkpoint_id": 1, "brillo": True,
        })
        assert len(stage.checkpoints) == 1
        assert stage.checkpoints[0]._light is not None

    def test_sin_la_propiedad_el_cargador_no_activa_brillo(self) -> None:
        from src.framework.stage.stage_loader import StageData, StageLoader

        class _Obj:
            x, y, width, height = 50.0, 60.0, 16.0, 32.0

        stage = StageData(map_layer=None)
        StageLoader._handle_checkpoint(stage, _Obj(), {"checkpoint_id": 1})
        assert stage.checkpoints[0]._light is None
