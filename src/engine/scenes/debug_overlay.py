"""
Module: debug_overlay
System: engine.scenes
Description: Debug overlay toggled with F3. Shows FPS, event queue
snapshot, and a tree-view of registered modules (F4/F5/F6).
"""
from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import _get_bus


TREE_LEVELS = [
    "Engine / Core",
    "Engine / IO",
    "Framework / Scenes",
    "Framework / Entities",
    "Framework / Processing",
]


class DebugOverlay:
    def __init__(self) -> None:
        self._visible: bool = False
        self._tree_level: int = 0
        self._key_cooldown: dict[int, float] = {}
        self._font = None

    def _ensure_font(self) -> None:
        if self._font is not None:
            return
        from src.engine.utils.asset_loader import AssetLoader
        self._font = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", 7)

    @property
    def visible(self) -> bool:
        return self._visible

    def handle_input(self, held: tuple[bool, ...], dt: float) -> None:
        # Cool-downs to avoid repeat fire
        for k in list(self._key_cooldown.keys()):
            self._key_cooldown[k] -= dt
            if self._key_cooldown[k] <= 0:
                del self._key_cooldown[k]

        def consume(key: int) -> bool:
            if not held[key]:
                return False
            if key in self._key_cooldown:
                return False
            self._key_cooldown[key] = 0.3
            return True

        if consume(pygame.K_F3):
            self._visible = not self._visible
        if self._visible:
            if consume(pygame.K_F4):
                self._tree_level = 0
            if consume(pygame.K_F5):
                self._tree_level = 1
            if consume(pygame.K_F6):
                self._tree_level = 2

    def draw(self, surface: pygame.Surface, fps: float) -> None:
        if not self._visible:
            return
        self._ensure_font()

        # Semi-transparent overlay
        overlay = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((5, 5, 15))
        surface.blit(overlay, (0, 0))

        y = 4
        lines: list[str] = []
        lines.append(f"FPS: {fps:.0f}")
        lines.append(f"Tree: {TREE_LEVELS[self._tree_level]}  |  [F3] hide  [F4/F5/F6] tree level")
        lines.append("")

        # Event queue snapshot
        try:
            bus = _get_bus()
            snap = bus.queue_snapshot
            lines.append(f"Event Queue: {len(snap)} pending")
            for evt_name, evt_data in snap[:5]:
                lines.append(f"  {evt_name}: {evt_data}")
        except Exception:
            lines.append("Event Bus: N/A")

        lines.append("")
        lines.append("Module Tree:")

        # Module tree based on level
        tree_items: list[str] = []
        if self._tree_level == 0:
            tree_items = [
                "engine/",
                "  core/",
                "    app.py",
                "    clock.py",
                "    event_bus.py",
                "    settings.py",
                "    game_context.py",
                "  input/",
                "    input_manager.py",
                "    action_map.py",
                "  scenes/",
                "    base_scene.py",
                "    scene_manager.py",
                "  utils/",
                "    asset_loader.py",
                "    math_utils.py",
            ]
        elif self._tree_level == 1:
            tree_items = [
                "framework/",
                "  entities/",
                "    entity_factory.py",
                "    entity.py",
                "    boss_base.py",
                "  processing/",
                "    filter_tools.py",
                "    vision_tools.py",
                "    pattern_recognition_tools.py",
                "    curve_tools.py",
                "  scenes/",
                "    stage_scene.py",
                "  stage/",
                "    camera.py",
            ]
        elif self._tree_level == 2:
            tree_items = [
                "student_templates/",
                "  stage_template/",
                "    stage_template.py",
                "  boss_template/",
                "    boss_template.py",
                "tests/",
                "  test_engine_core.py",
                "  test_demo_scenes.py",
                "  test_filter_tools.py",
                "  test_vision_tools.py",
                "  test_pattern_recognition_tools.py",
            ]

        lines.extend(tree_items)

        for line in lines:
            txt = self._font.render(line, True, (80, 200, 255))
            surface.blit(txt, (4, y))
            y += 10

        if y < settings.INTERNAL_HEIGHT - 20:
            hint = self._font.render(
                "  Debug Console  |  [F3] toggle  |  [F4] engine  |  [F5] framework  |  [F6] tests",
                True, (80, 200, 255))
            surface.blit(hint, (4, settings.INTERNAL_HEIGHT - 14))
