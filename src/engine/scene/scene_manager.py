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
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from src.engine.core.events import Events
from src.engine.scenes.transition_manager import TransitionManager
from src.engine.scenes.title_scene import TitleScene


@runtime_checkable
class _SceneWithRespawn(Protocol):
    def respawn(self) -> None: ...

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
        self._transition = TransitionManager()
        self._pending_replace_cb = None
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
        stage_id = str(data.get("stage_id", ""))
        sm = self._context.save_manager
        if sm is not None and stage_id:
            current_scene = self._stack[-1] if self._stack else None
            player_health = getattr(getattr(current_scene, '_player', None), 'current_health', 5.0)
            player_max = getattr(getattr(current_scene, '_player', None), 'max_health', 5.0)
            sm.auto_save(
                stage_id=f"{stage_id}_completed",
                stage_index=self._stage_index,
                checkpoint_x=0.0, checkpoint_y=0.0,
                health=player_health, max_health=player_max,
            )
        self._stage_index += 1
        if self._stage_index < len(self._stage_queue):
            next_stage_class = self._stage_queue[self._stage_index]
            logging.info(f"SceneManager: advancing to stage {next_stage_class.__name__}")
            self.replace(next_stage_class(self._context))
        else:
            from src.engine.scenes.end_credits_scene import EndCreditsScene
            logging.info("SceneManager: no more stages — end credits")
            self.replace(EndCreditsScene(self._context))

    def _on_player_died(self, **data: object) -> None:
        """Handle player death. If the current scene has a _respawn
        method (e.g. StageScene), let it handle death internally."""
        current = self._stack[-1] if self._stack else None
        if current is not None and isinstance(current, _SceneWithRespawn):
            logging.info("SceneManager: player died — scene handles respawn")
            return
        logging.info("SceneManager: player died — returning to title")
        self.replace(TitleScene(self._context))

    @property
    def stack_size(self) -> int:
        return len(self._stack)

    @property
    def stage_index(self) -> int:
        """Zero-based index into the stage queue (for save/load)."""
        return self._stage_index

    @property
    def transition(self) -> TransitionManager:
        return self._transition

    def set_stage_index(self, index: int) -> None:
        """Set the stage queue index (for load-game restore)."""
        if 0 <= index < max(len(self._stage_queue), 1):
            self._stage_index = index
