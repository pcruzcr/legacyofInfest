from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.save_data import MAX_SLOTS, SaveData
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    COLOR_ERROR,
    FONT_SMALL,
    draw_top_bar,
    draw_bottom_bar,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


def _stage_display_name(stage_id: str) -> str:
    mapping = {
        "stage0": "Stage 0: Prólogo",
        "boss_venado": "Boss: Venado Sagrado",
    }
    return mapping.get(stage_id, stage_id.replace("_", " ").title())


class LoadGameScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._selected: int = 0
        self._slots: list[SaveData | None] = [None] * MAX_SLOTS
        self._error_msg: str = ""
        self._error_timer: float = 0.0
        self._font_small = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)

    def on_enter(self) -> None:
        self._selected = 0
        self._refresh_slots()
        self._error_msg = ""
        self._error_timer = 0.0

    def _refresh_slots(self) -> None:
        sm = self.context.save_manager
        self._slots = [None] * MAX_SLOTS
        if sm is not None:
            for entry in sm.list_slots():
                slot = entry["slot"] - 1
                if 0 <= slot < MAX_SLOTS:
                    data = sm.load(entry["slot"])
                    self._slots[slot] = data

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._error_timer > 0:
            self._error_timer -= dt
            if self._error_timer <= 0:
                self._error_msg = ""

        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected = (self._selected + 1) % MAX_SLOTS
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected = (self._selected - 1) % MAX_SLOTS

        if im.is_action_pressed(Action.CONFIRM):
            data = self._slots[self._selected]
            if data is None:
                self._error_msg = "Slot vacío — elige un slot con datos"
                self._error_timer = 2.0
            else:
                self._load_save(data)

        if im.is_action_pressed(Action.CANCEL):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))

    def _load_save(self, data: SaveData) -> None:
        from src.engine.core.stage_registry import discover_stages

        stages = discover_stages()
        if not stages:
            self._error_msg = "No hay stages disponibles"
            self._error_timer = 2.0
            return

        target_index = min(data.stage_index, len(stages) - 1)
        target_class = stages[target_index]

        self.context.pending_load = data
        sm = self.context.scene_manager
        sm.set_stage_queue(stages)
        sm.set_stage_index(target_index)
        sm.replace(target_class(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "CARGAR PARTIDA", "LOAD")

        cy = 32
        for i in range(MAX_SLOTS):
            data = self._slots[i]
            selected = i == self._selected

            slot_rect = pygame.Rect(20, cy, settings.INTERNAL_WIDTH - 40, 28)
            if selected:
                pygame.draw.rect(surface, (40, 40, 80), slot_rect, border_radius=3)

            pygame.draw.rect(surface, (60, 60, 100), slot_rect, 1, border_radius=3)

            slot_num = self._font_small.render(f"  SLOT {i + 1}", True,
                                               COLOR_HIGHLIGHT if selected else COLOR_TEXT)
            surface.blit(slot_num, (26, cy + 2))

            if data is not None:
                stage_str = _stage_display_name(data.stage_id)
                ts = data.timestamp[:19] if data.timestamp else ""
                info = f"  {stage_str}  |  {ts}  |  HP: {data.health:.0f}/{data.max_health:.0f}"
                info_surf = self._font_small.render(info, True, (160, 160, 180))
                surface.blit(info_surf, (26, cy + 14))
            else:
                empty_surf = self._font_small.render("  (vacío)", True, (100, 100, 100))
                surface.blit(empty_surf, (26, cy + 14))

            cy += 34

        if self._error_msg:
            err = self._font_small.render(self._error_msg, True, COLOR_ERROR)
            ex = (settings.INTERNAL_WIDTH - err.get_width()) // 2
            surface.blit(err, (ex, 180))

        draw_bottom_bar(surface, "  UP/DOWN: Select Slot  |  ENTER: Load  |  ESC: Back")
