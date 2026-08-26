"""
Module: moneda_fx
System: stage (student assignment - stage3_3_el_patio)
Academic Unit: VI (Animacion con easing + interaccion propia de EventBus)

Cuando se recoge una moneda, el motor emite el evento del framework
EVENTO_RECOGIDO (interactable_system.py) con item_id/cantidad/pos. Esta
clase se suscribe a ese evento (interaccion propia, no generica) y anima un
destello en el punto de recogida usando una funcion de easing de
math_utils.py -- no es un movimiento lineal, la escala sigue la curva de
ease_out_elastic (sube de golpe y "rebota" antes de asentarse).
"""
from __future__ import annotations

import pygame

from src.engine.utils.math_utils import ease_out_elastic


class MonedaSparkle:
    """Un destello animado de una sola moneda, en (x, y)."""

    DURACION = 0.5
    RADIO_MAX = 14

    def __init__(self, pos: tuple[float, float]) -> None:
        self.pos = pygame.Vector2(pos)
        self._t = 0.0
        self.terminado = False

    def update(self, dt: float) -> None:
        self._t += dt
        if self._t >= self.DURACION:
            self.terminado = True

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        if self.terminado:
            return
        t = min(1.0, self._t / self.DURACION)
        # ease_out_elastic va de 0 a 1 pero se pasa de 1 y vuelve (rebote):
        # eso es lo que hace que el destello "salte" en vez de solo crecer.
        escala = ease_out_elastic(t)
        radio = max(1, int(self.RADIO_MAX * escala))
        alpha = max(0, int(255 * (1.0 - t)))
        if radio <= 0 or alpha <= 0:
            return
        glow = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 221, 90, alpha), (radio, radio), radio)
        pygame.draw.circle(glow, (255, 255, 220, alpha), (radio, radio), max(1, radio // 2))
        sx = int(self.pos.x - camera_offset.x - radio)
        sy = int(self.pos.y - camera_offset.y - radio)
        surface.blit(glow, (sx, sy))


class MonedaFxController:
    """Se suscribe a EVENTO_RECOGIDO y mantiene la lista de destellos vivos."""

    def __init__(self, event_bus) -> None:
        from src.framework.stage.interactable_system import EVENTO_RECOGIDO
        self._sparkles: list[MonedaSparkle] = []
        event_bus.subscribe(EVENTO_RECOGIDO, self._on_recogido)

    def _on_recogido(self, **data) -> None:
        if str(data.get("item_id", "")) != "coin":
            return
        pos = data.get("pos")
        if pos is None:
            return
        self._sparkles.append(MonedaSparkle((pos[0], pos[1])))

    def update(self, dt: float) -> None:
        for s in self._sparkles:
            s.update(dt)
        self._sparkles = [s for s in self._sparkles if not s.terminado]

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        for s in self._sparkles:
            s.draw(surface, camera_offset)
