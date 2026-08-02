"""
Module: scene_manager
System: engine.scene
Academic Unit: N/A

Owns the scene stack (push / pop / replace) and advances the stage queue in
response to STAGE_COMPLETE and PLAYER_DIED.

Dependency direction (AUD-018)
------------------------------
This module deliberately imports **no concrete scene**. It previously did::

    scene_manager.py     ->  title_scene.py
      title_scene.py     ->  options_scene.py
        options_scene.py ->  pygame_gui

…so importing the scene *manager* — a piece of infrastructure — dragged in the
entire scene graph plus a third-party GUI toolkit. That is not a hypothetical
cost: it is exactly why ``tests/test_scene_manager.py`` and
``tests/test_menu_navigation.py`` both failed to even collect with
``ModuleNotFoundError: pygame_gui`` on a clean install.

The concrete scenes are now supplied as factories by whoever composes the
application (``App``), so the dependency points inward: infrastructure depends
on a ``Callable`` abstraction, and the composition root knows the concrete
types. Defaults are resolved lazily on first use so existing callers that
construct ``SceneManager(context)`` keep working.

On EventBus cleanup: this class unsubscribes *its own* handlers in
:meth:`cleanup`. It does **not** unsubscribe on behalf of scenes — an earlier
docstring claimed it did, which was untrue and encouraged scenes to skip their
own teardown. Scenes are responsible for their own subscriptions; the bus holds
weak references so forgetting is no longer a leak.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from src.engine.core.events import Events
from src.engine.scenes.transition_manager import TransitionManager

logger = logging.getLogger(__name__)

@runtime_checkable
class _SceneWithRespawn(Protocol):
    """A scene that handles player death internally rather than via the manager.

    Note the limits of ``runtime_checkable``: ``isinstance`` verifies only that
    a ``respawn`` attribute exists, never its signature. A scene declaring
    ``respawn(self, checkpoint)`` satisfies this check and then raises
    ``TypeError`` when called. The manager therefore calls ``respawn()`` with no
    arguments and treats that as the contract.
    """

    def respawn(self) -> None:
        ...


if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.engine.scene.base_scene import BaseScene

SceneFactory = Callable[["GameContext"], "BaseScene"]


def _default_title_factory(context: GameContext) -> BaseScene:
    from src.engine.scenes.title_scene import TitleScene
    return TitleScene(context)


def _default_credits_factory(context: GameContext) -> BaseScene:
    from src.engine.scenes.end_credits_scene import EndCreditsScene
    return EndCreditsScene(context)


class SceneManager:
    """Manages a stack of scenes with push/pop/replace semantics."""

    def __init__(
        self,
        context: GameContext,
        *,
        title_factory: SceneFactory | None = None,
        credits_factory: SceneFactory | None = None,
    ) -> None:
        self._context = context
        self._stack: list[BaseScene] = []
        self._stage_queue: list[type[BaseScene]] = []
        self._stage_index: int = 0
        self._transition = TransitionManager()
        self._title_factory = title_factory or _default_title_factory
        self._credits_factory = credits_factory or _default_credits_factory
        # Bound method refs kept in one place so unsubscribe cannot drift out of
        # sync with subscribe.
        self._event_refs: dict[str, Callable[..., None]] = {
            Events.STAGE_COMPLETE: self._on_stage_complete,
            Events.PLAYER_DIED: self._on_player_died,
        }
        for event, cb in self._event_refs.items():
            self._context.event_bus.subscribe(event, cb)

    def update(self, dt: float) -> None:
        """Update the current active scene (top of stack)."""
        if self._stack:
            self._stack[-1].update(dt)

    def cleanup(self) -> None:
        """Unsubscribe all event listeners. Call when SceneManager is discarded."""
        for event, cb in self._event_refs.items():
            self._context.event_bus.unsubscribe(event, cb)

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

    # ── stage completion ───────────────────────────────────────
    #
    # AUD-020: this was one 22-line method doing five unrelated jobs — reading
    # the player's health through a private attribute on the current scene,
    # computing a next-stage index, loading a save, mutating it, saving it,
    # autosaving again, mutating _stage_index, and swapping the scene. Split
    # into named steps so each can be read, reasoned about and tested alone.

    def _on_stage_complete(self, **data: object) -> None:
        """Record the completion, then advance to whatever comes next."""
        stage_id = str(data.get("stage_id", ""))
        if stage_id:
            self._record_stage_completion(stage_id)
        self._stage_index += 1
        self._enter_next_stage()

    def _player_vitals(self) -> tuple[float, float]:
        """Current and maximum health of the active scene's player.

        Returns ``(0.0, 0.0)`` when there is no player to read. Scenes expose
        their player via a ``player`` property where available; the private
        ``_player`` fallback remains for scenes that have not adopted it, but the
        manager should not be reaching into scene internals at all — see R-04.
        """
        scene = self._stack[-1] if self._stack else None
        player = getattr(scene, "player", None) or getattr(scene, "_player", None)
        if player is None:
            return 0.0, 0.0
        return (
            float(getattr(player, "current_health", 0.0)),
            float(getattr(player, "max_health", 0.0)),
        )

    def _record_stage_completion(self, stage_id: str) -> None:
        """Append ``stage_id`` to the save's history and refresh the autosave."""
        save_manager = self._context.save_manager
        if save_manager is None:
            return

        slot = save_manager.newest_slot()
        if slot is not None:
            save_data = save_manager.load(slot)
            if save_data is not None and stage_id not in save_data.completed_stages:
                save_data.completed_stages.append(stage_id)
                save_manager.save(slot, save_data)

        health, max_health = self._player_vitals()
        save_manager.auto_save(
            stage_id=stage_id,
            stage_index=self._next_stage_index(),
            checkpoint_x=0.0, checkpoint_y=0.0,
            health=health, max_health=max_health,
        )

    def _next_stage_index(self) -> int:
        """The index the player should resume at, clamped to the queue.

        Kept separate from ``_stage_index`` because the two legitimately differ:
        the in-memory index may run one past the end of the queue (that is how
        ``_enter_next_stage`` detects "finished"), whereas the value written to
        the save file must always address a real stage.
        """
        if not self._stage_queue:
            return 0
        return min(self._stage_index + 1, len(self._stage_queue) - 1)

    def _enter_next_stage(self) -> None:
        """Replace the current scene with the next stage, or the credits."""
        if self._stage_index < len(self._stage_queue):
            next_stage_class = self._stage_queue[self._stage_index]
            logger.info("SceneManager: advancing to stage %s", next_stage_class.__name__)
            self.replace(next_stage_class(self._context))
            return
        logger.info("SceneManager: no more stages — end credits")
        self.replace(self._credits_factory(self._context))

    def _on_player_died(self, **data: object) -> None:
        """Handle player death.

        A scene that implements ``respawn()`` — every ``StageScene`` does —
        owns its own death handling, including checkpoints and the death
        animation. Anything else falls back to the title screen.

        AUD-186: esto miraba **sólo la cima** de la pila, y caer en un foso
        mandaba al título en vez de a la pantalla de game over.

        La secuencia que lo rompía está en `HazardSystem` y en
        `StageScene._kill_player`, y las dos hacen lo mismo::

            event_bus.emit(Events.PLAYER_DIED)      # ENCOLA
            scene_manager.push(GameOverScene(...))  # inmediato

        `emit` no invoca a nadie: encola para el `dispatch()` siguiente. Para
        cuando este manejador corría, el game over ya estaba encima, y
        `GameOverScene` no tiene `respawn()`. De ahí que diera por hecho que
        nadie sabía gestionar la muerte y se llevara por delante el game over
        que acababan de empujar.

        Se busca en toda la pila: que alguien haya empujado algo encima no
        cambia que el escenario siga vivo debajo y sepa reaparecer.
        """
        if any(isinstance(scene, _SceneWithRespawn) for scene in self._stack):
            logger.info("SceneManager: player died — scene handles respawn")
            return
        logger.info("SceneManager: player died — returning to title")
        self.replace(self._title_factory(self._context))

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
        """Set the stage queue index, e.g. when restoring a save.

        Out-of-range values are rejected with a warning rather than silently
        ignored: a save pointing past the end of the queue means the save and
        the build disagree about how many stages exist, which the player would
        otherwise experience as being dropped back at stage one for no reason.
        """
        limit = max(len(self._stage_queue), 1)
        if 0 <= index < limit:
            self._stage_index = index
        else:
            logger.warning(
                "SceneManager: ignoring out-of-range stage index %d "
                "(queue holds %d stage(s)); staying at %d",
                index, len(self._stage_queue), self._stage_index,
            )
