from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.cutscene_system import (
    CutsceneScript, CameraMoveAction, WaitAction, FadeAction,
)
from src.framework.ui.dialogue_system import DialogueTree, DialogueNode

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage0(StageScene):
    """Stage 0 — executable documentation / tutorial stage.
    Demonstrates all framework systems across 7 zones (A–G)."""

    STAGE_ID: str = "stage0"
    STAGE_NAME: str = "STAGE 0  PROLOGUE"
    ZONE: int = 0
    TIME_LIMIT: int = 0
    BGM_TRACK: str = "bgm_stage0"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path("assets/maps/stage0/stage0.tmx"))
        self._cutscene: CutsceneScript | None = None
        self._collectibles: list[pygame.Rect] = []
        self._collected: set[int] = set()

    def on_stage_start(self) -> None:
        super().on_stage_start()
        self._start_intro_cutscene()
        self._place_collectibles()
        self._register_dialogue_trees()

    def _start_intro_cutscene(self) -> None:
        script = CutsceneScript()
        script.add_action(FadeAction(duration=0.5, fade_in=False))
        script.add_action(WaitAction(0.3))
        script.add_action(CameraMoveAction(0, 0, 1.0, self._camera))
        script.add_action(FadeAction(duration=0.5, fade_in=True))
        script.start()
        self._cutscene = script

    def _place_collectibles(self) -> None:
        positions = [
            (320, 160, "heart_vessel"),
            (640, 128, "swift_feather"),
            (960, 144, "hollow_eye"),
            (1280, 112, "ancients_rib"),
            (1600, 96, "thorn_ring"),
        ]
        for x, y, item_id in positions:
            r = pygame.Rect(x - 8, y - 8, 16, 16)
            r._item_id = item_id
            self._collectibles.append(r)

    def _register_dialogue_trees(self) -> None:
        intro_tree = DialogueTree(
            "intro_narrator",
            "start",
            {
                "start": DialogueNode(
                    "start", "Narrator",
                    "The world lies in ruin. Ancient echoes stir beneath the hollow earth. "
                    "You are the last Legacy — reborn to reclaim what was lost.",
                    choices=[("Continue...", "zone_a")],
                ),
                "zone_a": DialogueNode(
                    "zone_a", "Narrator",
                    "Zone A — The Awakening. Learn to move, jump, and strike. "
                    "The path ahead is treacherous, but the echoes will guide you.",
                    choices=[("I am ready.", "__end__")],
                ),
            },
        )
        lore_tree = DialogueTree(
            "lore_echo",
            "echo_1",
            {
                "echo_1": DialogueNode(
                    "echo_1", "Echo",
                    "I remember... a city of spires that touched the sky. "
                    "Now only dust and memory remain.",
                    choices=[("Tell me more.", "echo_2"), ("I must go.", "__end__")],
                ),
                "echo_2": DialogueNode(
                    "echo_2", "Echo",
                    "The Infestation came from below — a wound in the world's heart. "
                    "Seal it, and perhaps there is still hope.",
                    choices=[("I will.", "__end__")],
                ),
            },
        )
        self._dialogue_trees: dict[str, DialogueTree] = {
            "intro": intro_tree,
            "lore": lore_tree,
        }

    def update(self, dt: float) -> None:
        if self._cutscene and self._cutscene.active:
            self._cutscene.update(dt)
            return
        super().update(dt)
        self._check_collectibles()
        self._check_dialogue_triggers()

    def _check_collectibles(self) -> None:
        if self._player is None or self._stage_data is None:
            return
        for i, rect in enumerate(self._collectibles):
            if i in self._collected:
                continue
            if self._player.rect.colliderect(rect):
                item_id = getattr(rect, "_item_id", "heart_vessel")
                from src.engine.core.inventory import get_inventory
                inv = get_inventory()
                if inv.collect(item_id):
                    self._collected.add(i)

    def _check_dialogue_triggers(self) -> None:
        if self._player is None or self._stage_data is None:
            return
        if self._dialogue.active:
            return
        for mt in self._stage_data.message_triggers:
            if self._player.rect.colliderect(mt.rect):
                tree_id = getattr(mt, "dialogue_tree_id", "")
                if tree_id and tree_id in self._dialogue_trees:
                    self._dialogue.start_dialogue(self._dialogue_trees[tree_id])

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        if self._cutscene:
            self._cutscene.draw(surface)

    def on_debug_toggle(self, enabled: bool) -> None:
        if enabled and self._collectibles:
            for i, rect in enumerate(self._collectibles):
                color = (100, 200, 255) if i not in self._collected else (100, 255, 100)
                pygame.draw.rect(
                    pygame.display.get_surface(), color,
                    (rect.x - self._camera.offset.x, rect.y - self._camera.offset.y,
                     rect.w, rect.h),
                )
