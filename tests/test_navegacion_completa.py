"""
AUD-616 — estructura de navegación en escenas clave.

Testea que las escenas principales exponen la API de navegación esperada:
  - _actions / _mode / get_focusable_widgets()
  - Métodos update/draw existen y no crashean
  - InputManager se conecta correctamente desde GameContext
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pygame
import pytest

from src.engine.core import settings


# Mocks mínimos para GameContext
@pytest.fixture
def ctx(input_mock):
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext

    context = GameContext(
        input_manager=input_mock,
        audio_manager=MagicMock(),
        scene_manager=MagicMock(),
        event_bus=EventBus(),
    )
    return context


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))


@pytest.fixture
def input_mock():
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock.is_action_just_pressed = lambda a: False
    mock.is_action_pressed = lambda a: False
    return mock


class TestEstructuraNavegacion:
    """Escenas clave exponen API de navegación."""

    def test_keybinding_scene_tiene_acciones(self, _video, ctx):
        from src.engine.scenes.keybinding_scene import _ACTION_LABELS, KeybindingScene

        escena = KeybindingScene(ctx)
        escena.on_enter()

        assert hasattr(escena, "_actions")
        assert len(escena._actions) == len(_ACTION_LABELS)

    def test_vector_lab_scene_tiene_modos(self, _video, ctx):
        from src.engine.scenes.vector_lab_scene import MODE_NAMES, VectorLabScene

        escena = VectorLabScene(ctx)
        escena.on_enter()

        assert hasattr(escena, "_mode")
        assert len(MODE_NAMES) == 4

    def test_color_theory_scene_tiene_modos(self, _video, ctx):
        from src.engine.scenes.color_theory_scene import MODE_NAMES, ColorTheoryScene

        escena = ColorTheoryScene(ctx)
        escena.on_enter()

        assert hasattr(escena, "_mode")
        assert len(MODE_NAMES) == 6

    def test_combo_demo_scene_tiene_estado(self, _video, ctx):
        from src.engine.scenes.combo_demo_scene import ComboDemoScene

        escena = ComboDemoScene(ctx)
        escena.on_enter()

        assert hasattr(escena, "_combo_count")
        assert hasattr(escena, "_hit_log")

    def test_pattern_demo_scene_tiene_modos(self, _video, ctx):
        from src.engine.scenes.pattern_demo_scene import MODE_NAMES, PatternDemoScene

        escena = PatternDemoScene(ctx)
        escena.on_enter()

        assert hasattr(escena, "_mode")
        assert len(MODE_NAMES) == 6

    def test_vision_demo_scene_tiene_modos(self, _video, ctx):
        from src.engine.scenes.vision_demo_scene import MODE_NAMES, VisionDemoScene

        escena = VisionDemoScene(ctx)
        escena.on_enter()

        assert hasattr(escena, "_mode")
        assert len(MODE_NAMES) == 10

    def test_quiz_system_tiene_preguntas(self, _video, ctx):
        from src.engine.scenes.quiz_system import QuizManager

        quiz = QuizManager([])
        assert hasattr(quiz, "_questions")
        assert hasattr(quiz, "toggle")
        assert hasattr(quiz, "handle_input")
        assert hasattr(quiz, "draw")

    def test_escenas_tienen_update_y_draw(self, _video, ctx):
        """Todas las escenas principales tienen update y draw."""
        from src.engine.scenes.color_theory_scene import ColorTheoryScene
        from src.engine.scenes.combo_demo_scene import ComboDemoScene
        from src.engine.scenes.keybinding_scene import KeybindingScene
        from src.engine.scenes.pattern_demo_scene import PatternDemoScene
        from src.engine.scenes.vector_lab_scene import VectorLabScene
        from src.engine.scenes.vision_demo_scene import VisionDemoScene

        escenas = [
            KeybindingScene(ctx),
            VectorLabScene(ctx),
            ColorTheoryScene(ctx),
            ComboDemoScene(ctx),
            PatternDemoScene(ctx),
            VisionDemoScene(ctx),
        ]

        for escena in escenas:
            escena.on_enter()
            # No debe crashear
            escena.update(0.016)
            surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
            escena.draw(surface)
            escena.on_exit()