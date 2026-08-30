"""
Module: light_shimmer
System: stages.hall
Academic Unit: Unit V — Color (HSL) and alpha transparency

Reflejo de luz sobre el agua inundada de El Hall. Cada tragaluz de la ficha
oficial de Zona 3 (`16_WORLD_DESIGN.md`: "columnas de luz que caen de las
claraboyas") proyecta un charco de luz sobre el piso; donde el piso se
inundó, ese mismo charco ahora se refleja en el agua y cambia de color
según qué tan cerca está de la columna de luz real (cálido, la "luz dorada
de tarde" que el documento de mundo ya asigna a la Zona 3) o de la sombra
del agua profunda (frío, azul-verde). Es el mismo patrón que ya usan
`stage3_1_la_entrada_de_piedra` (sombra de nube en HSL) y
`stage3_3_el_patio` (`ColorTools.apply_tint` en la fuente): color con una
causa visible en el mundo, no un filtro decorativo.
"""
from __future__ import annotations

import math

import pygame

from src.framework.entities.base_entity import BaseEntity
from src.framework.processing.color_tools import ColorTools


class LightPoolShimmer(BaseEntity):
    """Un charco de luz que respira sobre el agua: color HSL + alfa real.

    Puramente visual — sin colisión, sin efecto de jugabilidad. Cada
    fotograma:

    1. Calcula qué tan "cerca del centro de la columna de luz" está el
       reflejo (`ciclo`, una onda triangular en el tiempo — no depende de
       la posición del jugador porque el agua entera respira igual, como
       una superficie real).
    2. Convierte esa cercanía en un color HSL: matiz entre 45° (ámbar
       cálido, la luz directa) y 200° (azul-verde frío, el agua profunda),
       con `ColorTools.hsl_to_rgb` — la misma fórmula que ya usa
       `stage3_1` para su sombra de nube.
    3. Dibuja el óvalo en una `Surface` con `SRCALPHA` y un alfa que
       también respira (28 a 90 de 255): transparencia real, no un color
       sólido que simula transparencia.
    """

    #: Radio máximo del óvalo de luz, en px.
    RADIUS_PX = 22
    #: Segundos para un ciclo completo de "respiración" (color + alfa).
    PERIOD_SECONDS = 3.2

    def __init__(
        self, position: pygame.Vector2, phase: float = 0.0, event_bus=None, **_ignored,
    ) -> None:
        super().__init__(position, event_bus)
        self.rect = pygame.Rect(
            int(position.x) - self.RADIUS_PX, int(position.y) - self.RADIUS_PX // 2,
            self.RADIUS_PX * 2, self.RADIUS_PX,
        )
        self.layer = 4
        self.is_alive: bool = True
        self._t = phase

    def update(self, dt: float) -> None:
        self._t += dt

    def _ciclo(self) -> float:
        """Onda triangular en [0, 1]: sube y baja, nunca salta de golpe."""
        fase = (self._t % self.PERIOD_SECONDS) / self.PERIOD_SECONDS
        return 1.0 - abs(2.0 * fase - 1.0)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        ciclo = self._ciclo()

        # Unidad V — HSL: el matiz interpola entre ámbar cálido (luz
        # directa del tragaluz, 45°) y azul-verde frío (el agua profunda,
        # 200°), nunca en RGB directo. Verificado con
        # `ColorTools.hsl_to_rgb` en los tres puntos del recorrido:
        # ciclo=0.0 -> (203,172,77) ámbar; ciclo=0.5 -> (77,203,82) verde;
        # ciclo=1.0 -> (77,161,203) azul. El punto medio cae en verde, no
        # en un naranja intermedio — interpolar en HSL por el camino corto
        # (45°->200° subiendo) cruza la banda verde (90°-150°) porque está
        # entre los dos extremos en la rueda de color. Es el resultado
        # correcto de la fórmula, y se queda: un verde-turquesa a mitad de
        # camino es exactamente cómo se ve luz cálida disolviéndose en agua
        # fría, no un error de interpolación.
        hue = 45.0 + (200.0 - 45.0) * ciclo
        r, g, b = ColorTools.hsl_to_rgb(hue, 0.55, 0.55)

        # Transparencia real: alfa por superficie (SRCALPHA), no un
        # blend_mode global ni un color sólido que "parece" transparente.
        alpha = int(28 + (90 - 28) * ciclo)
        w = int(self.RADIUS_PX * 2 * (0.7 + 0.3 * ciclo))
        h = w // 2

        pool = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(pool, (r, g, b, alpha), pool.get_rect())

        screen_pos = self.position - camera_offset
        surface.blit(
            pool, (int(screen_pos.x - w / 2), int(screen_pos.y - h / 2)),
        )
