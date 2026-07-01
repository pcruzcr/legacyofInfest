"""
Module: stage_template
Academic Unit: Final Project — Stage Design
Description: Template for custom stage scenes. Students extend StageScene
and implement the placeholder methods below.
"""
from __future__ import annotations

from pathlib import Path

import pygame

from src.framework.processing.pattern_recognition_tools import (
    PatternRecognitionTools,
    TrainedModel,
)
from src.framework.scenes.stage_scene import StageScene


class CustomStageScene(StageScene):
    """A custom stage built from a TMX map.

    TODO:
    1. Replace the TMX path with your own map.
    2. Override on_enter() to set up stage-specific logic.
    3. Override update() to add custom behavior.
    4. Override draw() to add custom rendering.
    """

    def __init__(self, tmx_path: Path | None = None) -> None:
        if tmx_path is None:
            tmx_path = Path("student_templates/stage_template/stage_template.tmx")
        super().__init__(tmx_path)
        self._stage_model: TrainedModel | None = None
        self._custom_timer: float = 0.0

    def load_model(self, model_path: str | Path) -> None:
        """Load a pre-trained model for recognition tasks."""
        self._stage_model = PatternRecognitionTools.load_model(Path(model_path))

    def on_enter(self) -> None:
        """Called when the stage becomes active."""
        super().on_enter()
        self._custom_timer = 0.0

    def update(self, dt: float) -> None:
        """Called every frame with the delta time in seconds."""
        super().update(dt)
        self._custom_timer += dt

    def draw(self, surface: pygame.Surface) -> None:
        """Render all visual elements for this stage."""
        super().draw(surface)
