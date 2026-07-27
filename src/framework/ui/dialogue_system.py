"""
Module: dialogue_system
System: framework.ui
Academic Unit: N/A
Description: Branching dialogue system with speaker portraits, name labels,
and choice-based progression. Supports multiple NPCs and dialogue trees.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.input.action_map import Action
from src.engine.utils.asset_loader import AssetLoader

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class DialogueNode:
    """A single node in a branching dialogue tree."""

    def __init__(self, node_id: str, speaker: str, text: str,
                 portrait: str | None = None,
                 choices: list[tuple[str, str]] | None = None,
                 on_enter: str | None = None,
                 on_exit: str | None = None) -> None:
        self.node_id: str = node_id
        self.speaker: str = speaker
        self.text: str = text
        self.portrait: str | None = portrait
        self.choices: list[tuple[str, str]] = choices or []
        self.on_enter: str | None = on_enter
        self.on_exit: str | None = on_exit


class DialogueTree:
    """A complete dialogue tree with multiple nodes."""

    def __init__(self, tree_id: str, start_node: str,
                 nodes: dict[str, DialogueNode]) -> None:
        self.tree_id: str = tree_id
        self.start_node: str = start_node
        self.nodes: dict[str, DialogueNode] = nodes


class DialogueSystem:
    """Manages dialogue display with portraits, choices, and branching."""

    def __init__(self, context: GameContext) -> None:
        self._context = context
        self._active: bool = False
        self._current_tree: DialogueTree | None = None
        self._current_node: DialogueNode | None = None
        self._selected_choice: int = 0
        self._text_progress: float = 0.0
        self._text_speed: float = 30.0
        self._full_text_visible: bool = False
        self._portrait_cache: dict[str, pygame.Surface] = {}
        self._font_name = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", 18)
        self._font_text = pygame.font.Font(None, 16)
        self._font_choice = pygame.font.Font(None, 16)
        self._bg = pygame.Surface((settings.INTERNAL_WIDTH - 40, 100), pygame.SRCALPHA)
        self._bg.fill((0, 0, 0, 200))

    def start_dialogue(self, tree: DialogueTree) -> None:
        """Start a dialogue tree."""
        self._active = True
        self._current_tree = tree
        self._selected_choice = 0
        self._go_to_node(tree.start_node)

    def _go_to_node(self, node_id: str) -> None:
        if self._current_tree is None:
            return
        node = self._current_tree.nodes.get(node_id)
        if node is None:
            self.end_dialogue()
            return
        self._current_node = node
        self._text_progress = 0.0
        self._full_text_visible = False
        self._selected_choice = 0
        if node.on_enter:
            self._execute_action(node.on_enter)

    def _execute_action(self, action: str) -> None:
        """Execute a script action (e.g. 'give_item:key', 'set_flag:boss_defeated')."""
        parts = action.split(":")
        if len(parts) < 2:
            return
        cmd, arg = parts[0], ":".join(parts[1:])
        if cmd == "give_item":
            self._context.event_bus.emit(Events.ITEM_COLLECTED, item_id=arg)
        elif cmd == "set_flag":
            self._context.event_bus.emit(Events.FLAG_SET, flag=arg)

    def end_dialogue(self) -> None:
        """End the current dialogue."""
        if self._current_node and self._current_node.on_exit:
            self._execute_action(self._current_node.on_exit)
        self._active = False
        self._current_tree = None
        self._current_node = None

    def update(self, dt: float) -> None:
        if not self._active or self._current_node is None:
            return
        if not self._full_text_visible:
            self._text_progress += self._text_speed * dt
            if self._text_progress >= len(self._current_node.text):
                self._text_progress = float(len(self._current_node.text))
                self._full_text_visible = True
        im = self._context.input_manager
        if im is None:
            return
        if self._full_text_visible:
            if self._current_node.choices:
                if im.is_action_just_pressed(Action.MOVE_DOWN):
                    self._selected_choice = (self._selected_choice + 1) % len(self._current_node.choices)
                if im.is_action_just_pressed(Action.MOVE_UP):
                    self._selected_choice = (self._selected_choice - 1) % len(self._current_node.choices)
                if im.is_action_just_pressed(Action.CONFIRM):
                    _, next_id = self._current_node.choices[self._selected_choice]
                    self._go_to_node(next_id)
            else:
                if im.is_action_just_pressed(Action.CONFIRM) or im.is_action_just_pressed(Action.CANCEL):
                    self.end_dialogue()

    def draw(self, surface: pygame.Surface) -> None:
        if not self._active or self._current_node is None:
            return
        w = settings.INTERNAL_WIDTH
        h = settings.INTERNAL_HEIGHT
        box_y = h - 110
        surface.blit(self._bg, (20, box_y))
        pygame.draw.rect(surface, (60, 60, 80), (20, box_y, w - 40, 100), 2, border_radius=4)
        portrait = self._current_node.portrait
        px = 30
        py = box_y + 10
        if portrait:
            if portrait not in self._portrait_cache:
                try:
                    img = AssetLoader.load_image(
                        settings.ASSETS_DIR / "sprites" / "portraits" / portrait,
                        size=(48, 48),
                    )
                    self._portrait_cache[portrait] = img
                except (pygame.error, FileNotFoundError, PermissionError):
                    logger.warning("dialogue_system: failed to load portrait %s", portrait)
                    self._portrait_cache[portrait] = pygame.Surface((48, 48))
                    self._portrait_cache[portrait].fill((80, 80, 100))
            surface.blit(self._portrait_cache[portrait], (px, py))
            px += 56
        name = self._font_name.render(self._current_node.speaker, True, (255, 220, 150))
        surface.blit(name, (px, py))
        visible_chars = int(self._text_progress)
        display_text = self._current_node.text[:visible_chars]
        text_surf = self._font_text.render(display_text, True, (220, 220, 220))
        surface.blit(text_surf, (px, py + 20))
        if self._full_text_visible and self._current_node.choices:
            cy = box_y + 60
            for i, (choice_text, _) in enumerate(self._current_node.choices):
                color = (255, 255, 100) if i == self._selected_choice else (180, 180, 180)
                prefix = "> " if i == self._selected_choice else "  "
                choice_surf = self._font_choice.render(f"{prefix}{choice_text}", True, color)
                surface.blit(choice_surf, (px, cy + i * 16))
        elif self._full_text_visible and not self._current_node.choices:
            hint = self._font_text.render("[ENTER] Continue", True, (140, 140, 150))
            surface.blit(hint, (w - 120, box_y + 80))

    @property
    def active(self) -> bool:
        return self._active