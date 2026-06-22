"""
Module: animation_controller
System: framework
Academic Unit: Player character
Description: Sprite-sheet animation controller for the player.
Implements the exact state table and timing rules from 04_PLAYER_SPEC.md §9.3.
"""

from __future__ import annotations

import pygame


class AnimationController:
    """Per-entity sprite-sheet animation player.

    Tracks the current animation, frame index, and frame timer.
    Advances frames based on elapsed time and FPS.
    Accounts for looping vs. hold-last-frame behavior.
    """

    def __init__(self) -> None:
        """Start with no animation selected."""
        self.current_animation: str = ""
        self.current_frame: int = 0
        self.frame_timer: float = 0.0
        self._facing_left: bool = False
        self._flashing: bool = False

    def set_facing(self, facing_left: bool) -> None:
        """Set horizontal flip for rendering."""
        self._facing_left = facing_left

    def set_flash(self, flashing: bool) -> None:
        """Toggle invincibility flash visibility."""
        self._flashing = flashing

    def play(
        self, animation_name: str, frame_count: int, fps: int, loop: bool
    ) -> None:
        """Switch to a new animation, resetting frame progress.

        Args:
            animation_name: Key identifying the animation (e.g. ``"idle"``).
            frame_count: Total frames in the sprite sheet row.
            fps: Playback speed in frames per second.
            loop: If ``True``, the animation repeats; if ``False``, it holds
                on the last frame until the state exits.
        """
        if self.current_animation != animation_name:
            self.current_animation = animation_name
            self.current_frame = 0
            self.frame_timer = 0.0
        self._frame_count = frame_count
        self._fps = fps
        self._loop = loop

    def update(self, dt: float) -> None:
        """Advance the animation timer by *dt* seconds."""
        if self._fps <= 0 or self._frame_count <= 0:
            return
        self.frame_timer += dt
        if self.frame_timer >= 1.0 / self._fps:
            self.frame_timer = 0.0
            at_last_frame = self.current_frame >= self._frame_count - 1
            if self._loop or not at_last_frame:
                self.current_frame = (
                    (self.current_frame + 1) % self._frame_count
                )

    def get_surface(self, spritesheet: pygame.Surface) -> pygame.Surface:
        """Extract and return the current frame surface from *spritesheet*.

        The spritesheet is assumed to be a horizontal strip of equal-sized
        frames.  The frame width is computed as ``spritesheet.width /
        frame_count``.
        """
        if self._frame_count <= 0:
            return pygame.Surface((0, 0))
        frame_w = spritesheet.get_width() // self._frame_count
        frame_h = spritesheet.get_height()
        rect = pygame.Rect(
            self.current_frame * frame_w,
            0,
            frame_w,
            frame_h,
        )
        subsurface = spritesheet.subsurface(rect).copy()
        if self._facing_left:
            subsurface = pygame.transform.flip(subsurface, True, False)
        if self._flashing:
            subsurface.set_alpha(0)
        return subsurface
