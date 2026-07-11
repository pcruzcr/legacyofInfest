from __future__ import annotations

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
        mode = settings.COLORBLIND_MODE
        if mode == "off":
            return
        w, h = surface.get_size()
        for x in range(0, w, 2):
            for y in range(0, h, 2):
                try:
                    r, g, b, *a = surface.get_at((x, y))
                    alpha_val = a[0] if a else 255
                    if mode == "protanopia":
                        surface.set_at((x, y), (int(r * 0.57 + g * 0.43), int(g * 0.86), int(b * 0.86), alpha_val))
                    elif mode == "deuteranopia":
                        surface.set_at((x, y), (int(r * 0.63), int(g * 0.78 + r * 0.22), int(b * 0.86), alpha_val))
                    elif mode == "tritanopia":
                        surface.set_at((x, y), (int(r * 0.95), int(g * 0.43 + b * 0.57), int(b * 0.43), alpha_val))
                except Exception:
                    pass

    def apply(self, surface: pygame.Surface) -> None:
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT

        # Flash overlay
        if self._flash_alpha > 0:
            alpha = int(self._flash_alpha * (self._flash_timer / max(self._flash_duration, 0.01)))
            flash = pygame.Surface((w, h), pygame.SRCALPHA)
            flash.fill((*self._flash_color, min(255, alpha)))
            surface.blit(flash, (0, 0))

        # Damage + base vignette
        if self._damage_vignette > 0 or self._vignette_strength > 0:
            total_v = min(0.6, self._vignette_strength + self._damage_vignette)
            if self._vignette_surf is None or self._vignette_surf.get_size() != (w, h):
                self._vignette_surf = self._build_vignette(w, h)
            vig = self._vignette_surf.copy()
            vig.set_alpha(int(total_v * 255))
            surface.blit(vig, (0, 0))

        # Bloom — downsample bright areas for a glow
        if self._bloom_intensity > 0.01:
            small_w = max(1, w // 4)
            small_h = max(1, h // 4)
            glow = pygame.transform.smoothscale(surface, (small_w, small_h))
            for _ in range(2):
                glow = pygame.transform.smoothscale(
                    pygame.transform.smoothscale(glow, (max(1, small_w // 2), max(1, small_h // 2))),
                    (small_w, small_h),
                )
            glow = pygame.transform.smoothscale(glow, (w, h))
            # Add glow with intensity
            glow.set_alpha(int(self._bloom_intensity * 128))
            surface.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

            # Add spectral highlight layer on top
            highlight = pygame.Surface((w, h), pygame.SRCALPHA)
            for x in range(0, w, 1):
                for y in range(0, h, 1):
                    try:
                        r, g, b, *a = surface.get_at((x, y))
                        lum = 0.299 * r + 0.587 * g + 0.114 * b
                        if lum > self._bloom_threshold:
                            extra = min(1.0, (lum - self._bloom_threshold) / 175.0)
                            val = int(extra * self._bloom_intensity * 200)
                            highlight.set_at((x, y), (255, 255, 255, val))
                    except Exception:
                        pass
            surface.blit(highlight, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # Tint overlay
        if self._tint_alpha > 0:
            tint = pygame.Surface((w, h), pygame.SRCALPHA)
            tint.fill((*self._tint_color, int(self._tint_alpha * 255)))
            surface.blit(tint, (0, 0))

        # Motion blur — blend current frame with previous frame
        if self._motion_blur_strength > 0.01:
            if self._prev_frame is None:
                self._prev_frame = surface.copy()
            else:
                blur = pygame.Surface((w, h), pygame.SRCALPHA)
                blur.blit(self._prev_frame, (0, 0))
                blur.set_alpha(int(self._motion_blur_strength * 128))
                surface.blit(blur, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                self._prev_frame = surface.copy()

        # Color grading — 3x3 color matrix applied per pixel
        if self._color_grading is not None:
            r, g, b, rr, gg, bb, rrr, ggg, bbb = self._color_grading
            for x in range(0, w, 2):
                for y in range(0, h, 2):
                    try:
                        pr, pg, pb, *pa = surface.get_at((x, y))
                        nr = min(255, max(0, pr * r // 255 + pg * g // 255 + pb * b // 255))
                        ng = min(255, max(0, pr * rr // 255 + pg * gg // 255 + pb * bb // 255))
                        nb = min(255, max(0, pr * rrr // 255 + pg * ggg // 255 + pb * bbb // 255))
                        surface.set_at((x, y), (nr, ng, nb, pa[0] if pa else 255))
                    except Exception:
                        pass

        # Colorblind filter (last, on top of everything)
        self._apply_colorblind_filter(surface)

    def _build_vignette(self, w: int, h: int) -> pygame.Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        max_dist = ((cx) ** 2 + (cy) ** 2) ** 0.5
        for x in range(w):
            for y in range(h):
                dx, dy = x - cx, y - cy
                dist = ((dx * dx + dy * dy) ** 0.5) / max_dist
                alpha = int(max(0, dist - 0.3) / 0.7 * 200)
                surf.set_at((x, y), (0, 0, 0, min(200, alpha)))
        return surf
