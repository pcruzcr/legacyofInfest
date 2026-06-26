"""
Module: scene_manager
System: engine
Academic Unit: N/A
Description: SceneManager maintains a LIFO stack of BaseScene
instances and coordinates the lifecycle call-backs defined in
BaseScene (on_enter / on_exit / on_pause / on_resume).

Call order guarantees (see 22_API_CONTRACTS.md §6.2):

  push(B) while A is current:
      A.on_pause()
      B.on_enter()
      # current is now B

  pop() while B is current (A below it):
      B.on_exit()
      A.on_resume()
      # current is now A

  replace(C) while A is current:
      A.on_exit()
      C.on_enter()
      # current is now C, A is discarded
"""

from __future__ import annotations

from typing import Optional

from src.engine.scene.base_scene import BaseScene


class SceneManager:
    """Manages a stack of scenes and their lifecycle callbacks."""

    def __init__(self) -> None:
        """Create an empty scene manager."""
        self._stack: list[BaseScene] = []

    def push(self, scene: BaseScene) -> None:
        """Push scene onto the stack.

        If a scene is already active its on_pause is called first,
        then scene.on_enter is called.
        """
        if self._stack:
            self._stack[-1].on_pause()
        scene.on_enter()
        self._stack.append(scene)

    def pop(self) -> None:
        """Pop the top scene from the stack.

        The popped scene's on_exit is called, then the new top
        scene's on_resume is called. If the stack is empty after
        popping this is a no-op.
        """
        if not self._stack:
            return
        top = self._stack.pop()
        top.on_exit()
        if self._stack:
            self._stack[-1].on_resume()

    def replace(self, scene: BaseScene) -> None:
        """Replace the top scene with scene.

        The replaced scene's on_exit is called, then scene.on_enter
        is called. No on_pause / on_resume is invoked.
        """
        if self._stack:
            top = self._stack.pop()
            top.on_exit()
        scene.on_enter()
        self._stack.append(scene)

    @property
    def current(self) -> Optional[BaseScene]:
        """The scene at the top of the stack, or None if empty."""
        if self._stack:
            return self._stack[-1]
        return None