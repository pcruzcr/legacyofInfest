"""
StageWizardScene — Interactive Stage Builder Wizard.

Guides students step-by-step through creating a TMX stage.
Each step explains what to do and shows examples.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    BOTTOM_BAR_Y,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_MEDIUM,
    FONT_SMALL,
    TOP_BAR_H,
    draw_bottom_bar,
    draw_top_bar,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


WIZARD_STEPS = [
    {
        "title": "Step 1: Choose Tile Size",
        "instruction": "Open Tiled and create a new map.",
        "details": [
            "Map size: 40x23 tiles minimum, 80x60 max",
            "Tile size: 32x32 pixels",
            "Orientation: Orthogonal",
            "Save in assets/maps/your_stage.tmx",
        ],
    },
    {
        "title": "Step 2: Add Tileset",
        "instruction": "Add the template tileset.",
        "details": [
            "Use File > New Tileset or drag tileset_stage_template.tsx",
            "Set first GID to 1",
            "Tile size must match map (32x32)",
            "Check that tileset path is RELATIVE to the TMX",
        ],
    },
    {
        "title": "Step 3: Create Terrain Layer",
        "instruction": "Create a tile layer named 'Terrain'.",
        "details": [
            "Layer > Add Tile Layer, name it 'Terrain'",
            "Paint ground tiles using the tileset",
            "Ensure all tiles are connected (no gaps)",
            "Add walls/boundaries so player can't leave",
        ],
    },
    {
        "title": "Step 4: Add Player Spawn",
        "instruction": "Add an object group with PlayerSpawn.",
        "details": [
            "Layer > Add Object Group, name it 'Objects'",
            "Add a Point object (right-click > Insert Point)",
            "Set its Type property to 'PlayerSpawn'",
            "The player will appear at this position",
        ],
    },
    {
        "title": "Step 5: Add Checkpoints",
        "instruction": "Add checkpoint objects.",
        "details": [
            "In the 'Objects' layer, add more Point objects",
            "Set Type to 'Checkpoint' for each",
            "Place at strategic points in the stage",
            "At least 1 checkpoint is required",
        ],
    },
    {
        "title": "Step 6: Add Enemies",
        "instruction": "Create an 'Enemies' tile layer with enemy tiles.",
        "details": [
            "Create a new tile layer named 'Enemies'",
            "Place enemy tiles from the tileset",
            "Valid types: Walker, Shooter, Flying, Charger",
            "2-5 enemies recommended for a good stage",
        ],
    },
    {
        "title": "Step 7: Add Collectibles",
        "instruction": "Create a 'Collectibles' tile layer.",
        "details": [
            "Create a new tile layer named 'Collectibles'",
            "Use coin tiles (GID 1) and gem tiles (GID 2)",
            "Place 5+ collectibles throughout the stage",
            "Reward exploration, not just the main path",
        ],
    },
    {
        "title": "Step 8: Set Map Properties",
        "instruction": "Add custom properties to the map.",
        "details": [
            "Map > Map Properties, click + to add",
            "Add string property 'author' = your name",
            "Add int property 'zone' = zone number (1-8)",
            "Add string 'stage_id' = e.g. '1-1'",
            "Add string 'stage_name' = your stage name",
            "Add string 'climate' = desert/forest/cemetery/ice/lava/factory",
        ],
    },
    {
        "title": "Step 9: Save & Validate",
        "instruction": "Save and validate your TMX file.",
        "details": [
            "Save the TMX file to assets/maps/",
            "Run: python scripts/validate_tmx.py assets/maps/your_stage.tmx",
            "Fix any errors the validator reports",
            "Run: python scripts/grade_stage.py assets/maps/your_stage.tmx --json",
            "Aim for 90+ points",
        ],
    },
    {
        "title": "Step 10: Create Stage Scene",
        "instruction": "Create a Python stage scene to load your TMX.",
        "details": [
            "Look at src/stages/stage0/ for reference",
            "Create src/stages/your_stage/ directory",
            "Create __init__.py and stage_your_stage.py",
            "Import and use load_stage(tmx_path)",
            "Register in the stage registry",
        ],
    },
]

BACK_COLOR = (30, 30, 60)
ACCENT_BRIGHT = (255, 200, 50)


class StageWizardScene(BaseScene):
    """10-step interactive wizard that guides students through creating a TMX stage in Tiled."""

    def __init__(self, context: GameContext) -> None:
        """Load fonts and initialize step counter."""
        super().__init__(context)
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)
        self._step: int = 0

    def on_enter(self) -> None:
        """Reset to step 0 when entering the wizard."""
        self._step = 0

    def on_exit(self) -> None:
        """Cleanup on exit."""

    def update(self, dt: float) -> None:
        """Handle navigation: LEFT/RIGHT/SPACE to move between steps, ESC to exit."""
        im = self.input
        if im is None:
            return

        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        if im.is_raw_key_pressed(pygame.K_RIGHT):
            self._step = min(self._step + 1, len(WIZARD_STEPS) - 1)

        if im.is_raw_key_pressed(pygame.K_LEFT):
            self._step = max(self._step - 1, 0)

        if im.is_raw_key_pressed(pygame.K_SPACE):
            self._step = min(self._step + 1, len(WIZARD_STEPS) - 1)

    def draw(self, surface: pygame.Surface) -> None:
        """Render the current wizard step: title, instruction, bullet details, progress bar."""
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "STAGE BUILDER WIZARD", "ONBOARDING")

        step = WIZARD_STEPS[self._step]

        title_y = TOP_BAR_H + 12
        title = self._font_medium.render(f"  {step['title']}", True, ACCENT_BRIGHT)
        surface.blit(title, (8, title_y))

        instr_y = title_y + 28
        instr = self._font_medium.render(f"  {step['instruction']}", True, COLOR_HIGHLIGHT)
        surface.blit(instr, (8, instr_y))

        detail_y = instr_y + 24
        for line in step["details"]:
            color = COLOR_ACCENT if any(kw in line for kw in ["Run:", "Save", "python"]) else COLOR_TEXT
            txt = self._font_small.render(f"  * {line}", True, color)
            surface.blit(txt, (16, detail_y))
            detail_y += 16

        bar_y = BOTTOM_BAR_Y - 50
        bar_w = settings.INTERNAL_WIDTH - 40
        bar_x = 20
        progress = (self._step + 1) / len(WIZARD_STEPS)

        pygame.draw.rect(surface, (40, 40, 60), (bar_x, bar_y, bar_w, 12))
        if progress > 0:
            pygame.draw.rect(surface, ACCENT_BRIGHT, (bar_x, bar_y, int(bar_w * progress), 12))

        progress_text = self._font_small.render(
            f"  Step {self._step + 1}/{len(WIZARD_STEPS)} ({int(progress * 100)}%)",
            True, COLOR_HIGHLIGHT)
        surface.blit(progress_text, (bar_x + 4, bar_y - 14))

        hint = self._font_medium.render(
            "  LEFT/RIGHT or SPACE to navigate  |  ESC to exit", True, COLOR_ACCENT)
        surface.blit(hint, (8, bar_y - 30))

        draw_bottom_bar(surface, "  LEFT/RIGHT: navigate  SPACE: next  ESC: exit")
