from __future__ import annotations

import numpy as np
import pygame

from src.engine.core import settings


class PostProcessing:
    """Screen-space post-processing effects: vignette, flash, tint, bloom, motion blur, color grading."""

    def __init__(self) -> None:
        self._vignette_strength: float = 0.4
        self._flash_color: tuple[int, int, int] = (0, 0, 0)
        self._flash_alpha: float = 0.0
        self._flash_duration: float = 0.0
        self._flash_timer: float = 0.0
        self._tint_color: tuple[int, int, int] = (0, 0, 0)
        self._tint_alpha: float = 0.0
        self._damage_vignette: float = 0.0
        self._vignette_surf: pygame.Surface | None = None
        self._bloom_intensity: float = 0.0
        self._bloom_target: float = 0.0
        self._bloom_decay: float = 0.0
        self._bloom_threshold: int = 80
        self._motion_blur_strength: float = 0.0
        self._prev_frame: pygame.Surface | None = None
        self._color_grading: tuple[int, int, int, int, int, int, int, int, int] | None = None
        self._last_vignette_strength: float = 0.0
        self._flash_surf: pygame.Surface | None = None
        self._tint_surf: pygame.Surface | None = None
        self._blur_surf: pygame.Surface | None = None
        self._bloom_down: pygame.Surface | None = None
        self._bloom_up: pygame.Surface | None = None
        self._highlight_surf: pygame.Surface | None = None
        self._motion_up: pygame.Surface | None = None

    def set_motion_blur(self, strength: float = 0.3) -> None:
        self._motion_blur_strength = max(0.0, min(1.0, strength))

    def clear_motion_blur(self) -> None:
        self._motion_blur_strength = 0.0
        self._prev_frame = None

    def set_color_grading(
        self, r: int, g: int, b: int,
        rr: int, gg: int, bb: int,
        rrr: int, ggg: int, bbb: int
    ) -> None:
        self._color_grading = (r, g, b, rr, gg, bb, rrr, ggg, bbb)

    def clear_color_grading(self) -> None:
        self._color_grading = None

    def set_bloom(self, intensity: float, duration: float = 0.3) -> None:
        self._bloom_target = max(0.0, min(1.0, intensity))
        self._bloom_intensity = self._bloom_target
        self._bloom_decay = 1.0 / max(0.01, duration)

    def flash(self, color: tuple[int, int, int], alpha: float = 200, duration: float = 0.1) -> None:
        self._flash_color = color
        self._flash_alpha = alpha
        self._flash_duration = duration
        self._flash_timer = duration

    def set_damage_vignette(self, strength: float) -> None:
        self._damage_vignette = max(0.0, min(0.6, strength))

    def set_tint(self, color: tuple[int, int, int], alpha: float) -> None:
        self._tint_color = color
        self._tint_alpha = alpha

    def clear_tint(self) -> None:
        self._tint_alpha = 0.0

    def update(self, dt: float) -> None:
        if self._flash_timer > 0:
            self._flash_timer -= dt
            if self._flash_timer <= 0:
                self._flash_alpha = 0.0
        if self._bloom_intensity > 0.001:
            self._bloom_intensity -= self._bloom_decay * dt
        else:
            self._bloom_intensity = 0.0

    def _apply_colorblind_filter(self, surface: pygame.Surface) -> None:
        # AUD-036: this used to read settings.COLORBLIND_MODE, a module global
        # that nothing ever assigned to. The options screen persisted the
        # player's choice to config.json and this filter read a different,
        # always-"off" variable, so selecting a colourblind mode had no effect
        # on a single rendered frame. Both sides now use user_settings.
        from src.engine.core import user_settings
        mode = user_settings.get().colorblind_mode
        if mode == "off":
            return
        arr = pygame.surfarray.pixels3d(surface)
        try:
            r = arr[:,:,0].astype(np.float32)
            g = arr[:,:,1].astype(np.float32)
            b = arr[:,:,2].astype(np.float32)
            if mode == "protanopia":
                arr[:,:,0] = np.clip(r * 0.57 + g * 0.43, 0, 255).astype(np.uint8)
                arr[:,:,1] = np.clip(g * 0.86, 0, 255).astype(np.uint8)
                arr[:,:,2] = np.clip(b * 0.86, 0, 255).astype(np.uint8)
            elif mode == "deuteranopia":
                arr[:,:,0] = np.clip(r * 0.63, 0, 255).astype(np.uint8)
                arr[:,:,1] = np.clip(g * 0.78 + r * 0.22, 0, 255).astype(np.uint8)
                arr[:,:,2] = np.clip(b * 0.86, 0, 255).astype(np.uint8)
            elif mode == "tritanopia":
                arr[:,:,0] = np.clip(r * 0.95, 0, 255).astype(np.uint8)
                arr[:,:,1] = np.clip(g * 0.43 + b * 0.57, 0, 255).astype(np.uint8)
                arr[:,:,2] = np.clip(b * 0.43, 0, 255).astype(np.uint8)
        finally:
            del arr

    def apply(self, surface: pygame.Surface) -> None:
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT

        # Flash overlay
        if self._flash_alpha > 0:
            alpha = int(self._flash_alpha * (self._flash_timer / max(self._flash_duration, 0.01)))
            if self._flash_surf is None or self._flash_surf.get_size() != (w, h):
                self._flash_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            self._flash_surf.fill((*self._flash_color, min(255, alpha)))
            surface.blit(self._flash_surf, (0, 0))

        # Damage + base vignette
        if self._damage_vignette > 0 or self._vignette_strength > 0:
            total_v = min(0.6, self._vignette_strength + self._damage_vignette)
            if (self._vignette_surf is None
                or self._vignette_surf.get_size() != (w, h)
                or abs(total_v - self._last_vignette_strength) > 0.01):
                self._vignette_surf = self._build_vignette(w, h)
                self._last_vignette_strength = total_v
            self._vignette_surf.set_alpha(int(total_v * 255))
            surface.blit(self._vignette_surf, (0, 0))

        # Bloom — downsample bright areas for a glow
        if self._bloom_intensity > 0.01:
            small_w = max(1, w // 4)
            small_h = max(1, h // 4)
            down_size = (small_w, small_h)
            if self._bloom_down is None or self._bloom_down.get_size() != down_size:
                self._bloom_down = pygame.Surface(down_size)
            pygame.transform.smoothscale(surface, down_size, self._bloom_down)
            up_size = (w, h)
            if self._bloom_up is None or self._bloom_up.get_size() != up_size:
                self._bloom_up = pygame.Surface(up_size, pygame.SRCALPHA)
            self._bloom_up.fill((0, 0, 0, 0))
            alpha = int(self._bloom_intensity * 128)
            self._bloom_up.blit(self._bloom_down, (0, 0))
            self._bloom_up.set_alpha(alpha)
            glow = self._bloom_up
            surface.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

            # Add spectral highlight layer on top
            if self._highlight_surf is None or self._highlight_surf.get_size() != (w, h):
                self._highlight_surf = pygame.Surface((w, h))
            highlight = self._highlight_surf
            harr = pygame.surfarray.pixels3d(highlight)
            try:
                arr = pygame.surfarray.pixels3d(surface)
                try:
                    # ITU-R BT.601 luma coefficients.
                    lum = (
                        0.299 * arr[:, :, 0].astype(np.float32)
                        + 0.587 * arr[:, :, 1].astype(np.float32)
                        + 0.114 * arr[:, :, 2].astype(np.float32)
                    )
                finally:
                    del arr
                extra = np.clip((lum - self._bloom_threshold) / 175.0, 0, 1)
                val = (extra * self._bloom_intensity * 200).astype(np.uint8)
                harr[:,:,0] = val
                harr[:,:,1] = val
                harr[:,:,2] = val
            finally:
                del harr
            surface.blit(highlight, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # Tint overlay
        if self._tint_alpha > 0:
            if self._tint_surf is None or self._tint_surf.get_size() != (w, h):
                self._tint_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            self._tint_surf.fill((*self._tint_color, int(self._tint_alpha * 255)))
            surface.blit(self._tint_surf, (0, 0))

        # Motion blur — blend current frame with previous frame (1/4 res buffer)
        if self._motion_blur_strength > 0.01:
            sw, sh = max(1, w // 4), max(1, h // 4)
            down_size = (sw, sh)
            up_size = (w, h)
            if self._prev_frame is None:
                self._prev_frame = pygame.Surface(down_size)
                pygame.transform.smoothscale(surface, down_size, self._prev_frame)
            else:
                if self._blur_surf is None or self._blur_surf.get_size() != up_size:
                    self._blur_surf = pygame.Surface(up_size, pygame.SRCALPHA)
                if self._motion_up is None or self._motion_up.get_size() != up_size:
                    self._motion_up = pygame.Surface(up_size)
                prev_up = self._motion_up
                pygame.transform.smoothscale(self._prev_frame, up_size, prev_up)
                self._blur_surf.blit(prev_up, (0, 0))
                self._blur_surf.set_alpha(int(self._motion_blur_strength * 128))
                surface.blit(self._blur_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                pygame.transform.smoothscale(surface, down_size, self._prev_frame)

        # Color grading — 3x3 color matrix applied per pixel
        if self._color_grading is not None:
            cr, cg, cb, crr, cgg, cbb, crrr, cggg, cbbb = self._color_grading
            arr = pygame.surfarray.pixels3d(surface)
            try:
                pr = arr[:,:,0].astype(np.int32)
                pg = arr[:,:,1].astype(np.int32)
                pb = arr[:,:,2].astype(np.int32)
                arr[:,:,0] = np.clip((pr * cr + pg * cg + pb * cb) // 255, 0, 255).astype(np.uint8)
                arr[:,:,1] = np.clip((pr * crr + pg * cgg + pb * cbb) // 255, 0, 255).astype(np.uint8)
                arr[:,:,2] = np.clip((pr * crrr + pg * cggg + pb * cbbb) // 255, 0, 255).astype(np.uint8)
            finally:
                del arr

        # Colorblind filter (last, on top of everything)
        self._apply_colorblind_filter(surface)

    def _build_vignette(self, w: int, h: int) -> pygame.Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        max_dist_sq = cx * cx + cy * cy
        arr = pygame.surfarray.pixels_alpha(surf)
        try:
            xs, ys = np.ogrid[:w, :h]
            dist_sq = (xs - cx) ** 2 + (ys - cy) ** 2
            dist = np.sqrt(dist_sq / max_dist_sq)
            alpha = np.clip((dist - 0.3) / 0.7 * 200, 0, 200).astype(np.uint8)
            arr[:, :] = alpha
        finally:
            del arr
        return surf
