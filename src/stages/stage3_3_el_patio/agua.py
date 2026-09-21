"""
Module: agua
System: stage (student assignment)
Academic Unit: Unidad V (color y transparencia) + Unidad VI (animacion).

Dibuja la lamina del estanque: agua translucida con la superficie ondulando.

Por que hace falta, si el motor ya trae `WaterEffect`
=====================================================
No lo sustituye: lo completa, y solo en la parte que en este escenario no
funciona. `WaterZone` (el objeto del TMX) sigue siendo quien crea la
`ZonaDeAgua`, dispara `SwimmingState` y hace que el jugador nade — toda la
fisica es del motor y no se toca.

Lo que no sirve aqui es el DIBUJO. `WaterEffect.draw()`
(`src/framework/vfx/water_effect.py`) pinta lineas tenues repartidas por
**toda la pantalla** con `BLEND_RGB_ADD`: un brillo ambiental, no un estanque.
La version que si localiza el agua es la de GPU, que publica la region al
sombreador (`stage_scene._publicar_o_dibujar_el_agua`), y solo entra cuando el
efecto corre en la tarjeta. En el camino por software el estanque quedaba
invisible: se veia el hueco en el suelo y nada de agua dentro.

Esto pinta la lamina donde de verdad esta, leyendo el rectangulo de la propia
`ZonaDeAgua`, asi que no hay dos fuentes de verdad sobre donde hay agua.
"""
from __future__ import annotations

import math

import pygame

# Tres bandas, de la superficie al fondo: el agua se oscurece con la
# profundidad en vez de ser un tinte plano.
COLOR_SUP = (120, 200, 210)
COLOR_MEDIO = (60, 130, 150)
COLOR_FONDO = (28, 74, 96)
ALFA_SUP = 120
ALFA_FONDO = 190

AMPLITUD = 3.0        # px que sube y baja la superficie
LONGITUD = 34.0       # px de una cresta a la siguiente
VELOCIDAD = 1.6       # rad/s
BRILLOS = 5           # reflejos que recorren la superficie


class Agua:
    """Lamina de agua de un `ZonaDeAgua`, dibujada en coordenadas de mundo."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = pygame.Rect(rect)
        self._t = 0.0
        # El degradado no depende del tiempo, asi que se pinta una vez y se
        # reutiliza; solo la superficie ondulada se redibuja por fotograma.
        self._cuerpo = self._pintar_cuerpo()

    def _pintar_cuerpo(self) -> pygame.Surface:
        alto = max(1, self.rect.height)
        cuerpo = pygame.Surface((self.rect.width, alto), pygame.SRCALPHA)
        for y in range(alto):
            t = y / max(1, alto - 1)
            # Unidad V: interpolacion lineal de color y de alfa por franja.
            if t < 0.5:
                u = t * 2
                a, b = COLOR_SUP, COLOR_MEDIO
            else:
                u = (t - 0.5) * 2
                a, b = COLOR_MEDIO, COLOR_FONDO
            color = tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))
            alfa = int(ALFA_SUP + (ALFA_FONDO - ALFA_SUP) * t)
            pygame.draw.line(cuerpo, (*color, alfa), (0, y), (self.rect.width, y))
        return cuerpo

    def update(self, dt: float) -> None:
        self._t += dt * VELOCIDAD

    def _altura_de_ola(self, x_mundo: float) -> float:
        """Desplazamiento vertical de la superficie en ese x (Unidad VI).

        Dos senos de periodo distinto sumados: con uno solo la superficie se
        mueve toda a la vez y parece una tira que sube y baja, no agua.
        """
        k = 2 * math.pi / LONGITUD
        return (math.sin(x_mundo * k + self._t) * AMPLITUD
                + math.sin(x_mundo * k * 0.47 - self._t * 0.8) * AMPLITUD * 0.4)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        sx = int(self.rect.x - offset.x)
        sy = int(self.rect.y - offset.y)
        if sx > surface.get_width() or sx + self.rect.width < 0:
            return      # fuera de pantalla: ni se dibuja

        surface.blit(self._cuerpo, (sx, sy))

        # Superficie: una franja clara que ondula sobre el borde de arriba.
        for i in range(self.rect.width):
            dy = self._altura_de_ola(self.rect.x + i)
            y = sy + int(dy)
            pygame.draw.line(surface, COLOR_SUP, (sx + i, y), (sx + i, y + 2))

        # Reflejos: tramos cortos y claros que se desplazan por la superficie,
        # para que el agua no parezca quieta cuando el jugador tampoco se mueve.
        for n in range(BRILLOS):
            avance = (self._t * 12 + n * self.rect.width / BRILLOS) % self.rect.width
            dy = self._altura_de_ola(self.rect.x + avance)
            x = sx + int(avance)
            pygame.draw.line(surface, (200, 240, 245),
                             (x, sy + int(dy) - 1), (x + 7, sy + int(dy) - 1))
