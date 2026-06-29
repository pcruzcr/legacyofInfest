"""
Module: scene_manager
System: engine.scene
Academic Unit: N/A
Description: Manages the scene stack with push/pop/replace semantics.
Also listens for STAGE_COMPLETE and PLAYER_DIED events to advance
or trigger game-over flow via StageRegistry.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.engine.core.event_bus import EventBus

if TYPE_CHECKING:
    from src.engine.scene.base_scene import BaseScene


class SceneManager:
    """Manages a stack of scenes with push/pop/replace semantics."""

    def __init__(self) -> None:
        self._stack: list[BaseScene] = []
        self._stage_queue: list[type[BaseScene]] = []
        self._stage_index: int = 0
        # Subscribe to global events
        EventBus.subscribe("STAGE_COMPLETE", self._on_stage_complete)
        EventBus.subscribe("PLAYER_DIED", self._on_player_died)

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
        scene.on_enter()

    def pop(self) -> None:
        """Pop the top scene. Resumes the scene below if any."""
        if not self._stack:
            return
        top = self._stack.pop()
        top.on_exit()
        if self._stack:
            self._stack[-1].on_resume()

    def replace(self, scene: BaseScene) -> None:
        """Replace the top scene without pausing/resuming."""
        if self._stack:
            top = self._stack.pop()
            top.on_exit()
        self._stack.append(scene)
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
            self.replace(next_stage_class())
        else:
            # No more stages — push End Credits (placeholder for now)
            logging.info("SceneManager: no more stages — returning to title")
            from src.engine.scenes.title_scene import TitleScene
            self.replace(TitleScene())

    def _on_player_died(self, **data: object) -> None:
        """Handle player death — for now log and replace with title."""
        logging.info("SceneManager: player died")
        from src.engine.scenes.title_scene import TitleScene
        self.replace(TitleScene())

    @property
    def stack_size(self) -> int:
        return len(self._stack)
