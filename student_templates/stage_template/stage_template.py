"""
Module: stage_template
System: stage (student assignment)
Academic Unit: See README.md front-matter for units_demonstrated.

STUDENT INSTRUCTIONS:
1. Copy this entire folder to src/stages/<your_assignment_id>/
2. Rename this file to <your_assignment_id>.py
3. Rename stage_template.tmx to <your_assignment_id>.tmx
4. Update TMX_PATH and class attributes (STAGE_ID, STAGE_NAME, ZONE)
5. Fill in every # TODO(student) marker.
6. Do NOT modify StageScene or any engine/framework code.

Test with:
   python main.py --stage <your_assignment_id>
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


# TODO(student): Rename this class to match your assignment
# (e.g., class Stage1_2_LaSoda(StageScene):)
class StageTemplate(StageScene):
    """TODO(student): Describe your stage's zone, narrative context,
    and the academic concepts it demonstrates."""

    # TODO(student): Change these to match your assignment
    STAGE_ID: str = "stage_template"
    STAGE_NAME: str = "UNTITLED STAGE"
    ZONE: int = 1

    # TODO(student): Update this path after moving your .tmx to assets/maps/<id>/
    TMX_PATH = "student_templates/stage_template/stage_template.tmx"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))

    # ── Optional lifecycle hooks ────────────────────────────────────
    # Override any of these to add custom behavior:

    def on_stage_start(self) -> None:
        """Called after the stage loads and setup completes.
        TODO(student): e.g., register custom entities, set initial state."""
        pass

    def on_player_landed(self) -> None:
        """Called when the player first touches ground after being airborne.
        TODO(student): e.g., trigger a message, activate a hazard."""
        pass

    def on_enemy_died(self, enemy) -> None:
        """Called when an enemy dies.
        TODO(student): e.g., unlock a door, spawn a pickup."""
        pass

    def on_next_trigger_entered(self) -> None:
        """Called when the player touches NextTrigger.
        TODO(student): e.g., play a custom cutscene before stage ends."""
        pass

    def on_debug_toggle(self, enabled: bool) -> None:
        """Called when F1 is pressed to toggle debug overlay.
        TODO(student): e.g., show/hide additional debug info."""
        pass
