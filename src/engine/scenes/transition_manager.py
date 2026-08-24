"""
Module: transition_manager
System: engine.scenes
Description: Handles fade, wipe, slide, and circle transitions between scenes.
SceneManager calls this before/after scene swaps so the user sees
a smooth transition instead of an abrupt cut.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings

FADE_DURATION = 0.35


class TransitionManager:
    """Transition overlay controller supporting fade, wipe, slide, and circle modes."""

    def __init__(self) -> None:
        self._fade_alpha: int = 0
        self._fade_duration: float = FADE_DURATION
        self._fade_timer: float = 0.0
        self._direction: int | str = 0
        self._active: bool = False
        self._has_been_active: bool = False
        self._mode: str = "fade"
        self._wipe_progress: float = 0.0
        self._slide_offset: float = 0.0
        self._circle_radius: float = 0.0
        self._max_radius: float = 0.0
        self._old_surface: pygame.Surface | None = None

    def start_fade_out(self, duration: float = FADE_DURATION) -> None:
        self._mode = "fade"
        self._fade_duration = duration
        self._fade_timer = duration
        self._direction = -1
        self._active = True
        self._has_been_active = True

    def start_fade_in(self, duration: float = FADE_DURATION) -> None:
        self._mode = "fade"
        self._fade_duration = duration
        self._fade_timer = duration
        self._direction = 1
        self._active = True
        self._has_been_active = True

    def start_wipe(self, direction: str = "left", duration: float = 0.4, old_surface: pygame.Surface | None = None) -> None:  # noqa: E501
        """Wipe transition: old scene slides away revealing new scene beneath.
        direction: 'left', 'right', 'up', 'down'"""
        self._mode = "wipe"
        self._fade_duration = duration
        self._fade_timer = duration
        self._wipe_progress = 0.0
        self._direction = 1
        self._active = True
        self._has_been_active = True
        self._old_surface = old_surface

    def start_slide(self, direction: str = "left", duration: float = 0.4, old_surface: pygame.Surface | None = None) -> None:  # noqa: E501
        """Slide transition: entire old scene slides out to reveal new scene.
        direction: 'left', 'right', 'up', 'down'"""
        self._mode = "slide"
        self._fade_duration = duration
        self._fade_timer = duration
        self._slide_offset = 0.0
        self._direction = direction
        self._active = True
        self._has_been_active = True
        self._old_surface = old_surface

    def start_circle(self, expanding: bool = True, duration: float = 0.4, old_surface: pygame.Surface | None = None) -> None:  # noqa: E501
        """Circle wipe: expanding or contracting circle reveal.
        expanding=True: circle grows from center. expanding=False: circle shrinks to center."""
        self._mode = "circle"
        self._fade_duration = duration
        self._fade_timer = duration
        self._circle_radius = 0.0
        self._direction = 1 if expanding else -1
        self._active = True
        self._has_been_active = True
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        self._max_radius = (w ** 2 + h ** 2) ** 0.5
        self._old_surface = old_surface

    def asegurar_fundido_de_entrada(self, duracion: float = FADE_DURATION) -> None:
        """Garantiza que el velo acabará levantándose tras un cambio de escena.

        AUD-434 — por qué esto vive aquí y no en cada escena
        ----------------------------------------------------
        El patrón del juego es: la pantalla que se va arranca un fundido de
        salida y **acto seguido** cambia de escena. Quien levanta el velo es la
        escena de destino, llamando a `start_fade_in` en su `on_enter`.

        Ese contrato no se puede cumplir: obliga a cada pantalla nueva a
        acordarse de deshacer algo que no puso ella. Trece lo hacen y dos no
        —`LeaderboardScene` y `SkillTreeScene`—, y en esas dos el fundido de
        salida llega a su fin, `update` deja el alfa en 255 y `draw` lo pinta
        mientras el alfa sea mayor que cero, mire o no si la transición sigue
        viva. La pantalla aparece, se oscurece y se queda negra con la escena
        corriendo debajo.

        Ya se había cobrado una víctima: AUD-201 lo sufrió con BOSS RUSH, dejó
        el diagnóstico escrito y lo arregló reordenando dos líneas en la
        *llamada*. Van dos de dos, así que la garantía se mueve al sitio que
        conoce el estado del velo y la invoca quien sabe que hubo cambio de
        escena (`SceneManager`).

        No se limpia el alfa a pelo: eso cortaría en seco el velo que **sí**
        tiene que cubrir el salto de `SplashScene` a la pantalla de título.
        Lo que se hace es asegurar que existe un camino de vuelta a
        transparente.
        """
        # Los otros modos no miran `_fade_alpha` —`draw` exige `_old_surface`—
        # así que un velo pendiente no es asunto suyo.
        if self._mode != "fade":
            return
        # La escena pidió su propia entrada: se respeta, duración incluida.
        # Reiniciarla cambiaría el ritmo de trece transiciones que hoy están
        # bien, que es exactamente el precio que esta red de seguridad no debe
        # cobrar.
        if self._active and self._direction == 1:
            return
        # Sin velo puesto no hay nada que levantar, y arrancar un fundido aquí
        # sería un parpadeo negro donde antes había un corte limpio.
        if not self._active and self._fade_alpha <= 0:
            return
        self.start_fade_in(duracion)

    def update(self, dt: float) -> None:
        if not self._active:
            return
        self._fade_timer -= dt
        if self._fade_timer <= 0:
            self._fade_timer = 0.0
            if self._mode == "fade":
                if self._direction == -1:
                    self._fade_alpha = 255
                elif self._direction == 1:
                    self._fade_alpha = 0
            self._active = False
            return

        ratio = self._fade_timer / self._fade_duration

        if self._mode == "fade":
            if self._direction == -1:
                self._fade_alpha = int(255 * (1.0 - ratio))
            elif self._direction == 1:
                self._fade_alpha = int(255 * ratio)
        elif self._mode == "wipe":
            self._wipe_progress = 1.0 - ratio
        elif self._mode == "slide":
            self._slide_offset = ratio * settings.INTERNAL_WIDTH
        elif self._mode == "circle":
            ratio_complete = 1.0 - ratio
            if self._direction == 1:
                self._circle_radius = self._max_radius * ratio_complete
            else:
                self._circle_radius = self._max_radius * (1.0 - ratio_complete)

    def draw(self, surface: pygame.Surface) -> None:
        if self._mode == "fade" and self._fade_alpha > 0:
            overlay = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self._fade_alpha)
            surface.blit(overlay, (0, 0))
        elif self._mode == "wipe" and self._old_surface is not None:
            w = settings.INTERNAL_WIDTH
            h = settings.INTERNAL_HEIGHT
            wipe_x = int(w * self._wipe_progress)
            if self._direction == "left":
                surface.blit(self._old_surface, (0, 0), (0, 0, w - wipe_x, h))
            elif self._direction == "right":
                surface.blit(self._old_surface, (wipe_x, 0), (wipe_x, 0, w - wipe_x, h))
            elif self._direction == "up":
                surface.blit(self._old_surface, (0, 0), (0, 0, w, h - wipe_x))
            elif self._direction == "down":
                surface.blit(self._old_surface, (0, wipe_x), (0, wipe_x, w, h - wipe_x))
        elif self._mode == "slide" and self._old_surface is not None:
            offset = int(self._slide_offset)
            if self._direction == "left":
                surface.blit(self._old_surface, (-offset, 0))
            elif self._direction == "right":
                surface.blit(self._old_surface, (offset, 0))
            elif self._direction == "up":
                surface.blit(self._old_surface, (0, -offset))
            elif self._direction == "down":
                surface.blit(self._old_surface, (0, offset))
        elif self._mode == "circle" and self._old_surface is not None:
            w = settings.INTERNAL_WIDTH
            h = settings.INTERNAL_HEIGHT
            cx, cy = w // 2, h // 2
            radius = int(self._circle_radius)
            mask = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.circle(mask, (0, 0, 0, 255), (cx, cy), radius)
            surface.blit(self._old_surface, (0, 0))
            surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    @property
    def active(self) -> bool:
        return self._active

    @property
    def finished(self) -> bool:
        return self._has_been_active and not self._active
