"""
Module: scene_manager
System: engine.scene
Academic Unit: N/A
Description: Manages the scene stack with push/pop/replace semantics.
Also listens for STAGE_COMPLETE and PLAYER_DIED events to advance
or trigger game-over flow via StageRegistry.
Automatically cleans up EventBus subscriptions when scenes exit.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.scenes.title_scene import TitleScene

if TYPE_CHECKING:
    from src.engine.scene.base_scene import BaseScene
    from src.engine.core.game_context import GameContext


class SceneManager:
    """Manages a stack of scenes with push/pop/replace semantics."""

    _subscribed_events: list[str] = [Events.STAGE_COMPLETE, Events.PLAYER_DIED]

    def __init__(self, context: GameContext) -> None:
        self._context = context
        self._stack: list[BaseScene] = []
        self._stage_queue: list[type[BaseScene]] = []
        self._stage_index: int = 0
        self._context.event_bus.subscribe(Events.STAGE_COMPLETE, self._on_stage_complete)
        self._context.event_bus.subscribe(Events.PLAYER_DIED, self._on_player_died)

    def cleanup(self) -> None:
        """Unsubscribe all event listeners. Call when SceneManager is discarded."""
        for event in self._subscribed_events:
            self._context.event_bus.unsubscribe(event, getattr(self, f"_on_{event.lower()}"))

    @property
    def current(self) -> BaseScene:
        """The top-most scene on the stack."""
        if not self._stack:
            raise RuntimeError("SceneManager: no scenes on the stack")
        return self._stack[-1]

    def push(self, scene: BaseScene) -> None:
        """Push a new scene on top. Pauses the current scene if any."""
        if self._stack:
            self._stack[-1].on_pause()
        self._stack.append(scene)
        scene.awake()
        scene.start()
        scene.on_enter()

    def pop(self) -> None:
        """Pop the top scene. Resumes the scene below if any."""
        if not self._stack:
            return
        top = self._stack.pop()
        top.on_exit()
        top.destroy()
        if self._stack:
            self._stack[-1].on_resume()

    def replace(self, scene: BaseScene) -> None:
        """Replace the top scene without pausing/resuming."""
        if self._stack:
            top = self._stack.pop()
            top.on_exit()
            top.destroy()
        self._stack.append(scene)
        scene.awake()
        scene.start()
        scene.on_enter()

    def set_stage_queue(self, stages: list[type[BaseScene]]) -> None:
        """Set the ordered list of stage classes to advance through."""
        self._stage_queue = list(stages)
        self._stage_index = 0

    def _on_stage_complete(self, **data: object) -> None:
        """Advance to the next stage in the queue."""
        self._stage_index += 1
        if self._stage_index < len(self._stage_queue):
            next_stage_class = self._stage_queue[self._stage_index]
            logging.info(f"SceneManager: advancing to stage {next_stage_class.__name__}")
            self.replace(next_stage_class(self._context))
        else:
            # No more stages — push End Credits (placeholder for now)
            from src.engine.scenes.end_credits_scene import EndCreditsScene
            logging.info("SceneManager: no more stages — end credits")
            self.replace(EndCreditsScene(self._context))

    def _on_player_died(self, **data: object) -> None:
        """Handle player death. If the current scene has a _respawn
        method (e.g. StageScene), let it handle death internally."""
        current = self._stack[-1] if self._stack else None
        if current is not None and hasattr(current, "respawn"):
            logging.info("SceneManager: player died — scene handles respawn")
            return
        logging.info("SceneManager: player died — returning to title")
        self.replace(TitleScene(self._context))

    @property
    def stack_size(self) -> int:
        return len(self._stack)
