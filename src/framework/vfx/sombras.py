"""
Module: sombras
System: framework.vfx
Academic Unit: IV (dibujado, orden del pintor)

AUD-273 — la sombra bajo los pies.

Por qué es una mecánica y no un adorno
======================================
En un plataformas 2D la sombra en el suelo es **el único indicador de dónde va
a aterrizar el jugador** mientras está en el aire. Sin ella, un salto largo
sobre un hueco es una apuesta: la cámara sigue al personaje, así que en el pico
del salto el suelo suele estar fuera de la vista útil.

El proyecto tenía focos, bloom, viñeta, rayos volumétricos, clima y niebla — y
ni una sombra.

Por qué una elipse y no un sprite
----------------------------------
Porque tiene que valer para cualquier entidad sin pedir un asset por especie:
hay treinta tipos de enemigo y cuatro jefes. Una elipse se adapta al ancho del
cuerpo y no hay nada que mantener.

Y translúcida, no opaca: sobre un tileset con detalle una mancha negra se lee
como un agujero en el suelo, que es justo el malentendido que la sombra existe
para evitar.

Por qué el suelo llega por parámetro
-------------------------------------
Porque este módulo **no sabe de colisiones**, y buscarlo aquí acoplaría el
dibujado con la física. Quien llama ya tiene la lista de rects sólidos: es la
misma que le pasa al jugador cada fotograma.
"""
from __future__ import annotations

import pygame

#: A partir de esta altura sobre el suelo, la sombra ya no se ve. Una sombra
#: visible desde cualquier altura deja de informar de nada: lo que la hace útil
#: es que **crece al acercarse**.
ALTURA_DE_DESVANECIDO: float = 180.0

#: Alfa de la sombra con la entidad tocando el suelo. 110 sobre 255 se ve
#: sobre cualquier tileset y deja pasar el detalle de debajo.
ALFA_MAXIMO: int = 110

#: Cuánto se encoge la sombra en lo alto del salto, como fracción del ancho del
#: cuerpo. No baja de aquí: una sombra de dos píxeles no se distingue de una
#: mota de polvo del tileset.
ESCALA_MINIMA: float = 0.45


def suelo_bajo(cuerpo: pygame.Rect, solidos: list[pygame.Rect]) -> int | None:
    """La `y` del suelo más alto que hay **debajo** del cuerpo, o `None`.

    El más alto y no el primero: sobre una repisa suspendida, la sombra va en
    la repisa. Buscar el primero de la lista pondría la sombra en el fondo del
    pozo, que es peor que no tener sombra — informa de algo falso.
    """
    mejor: int | None = None
    for rect in solidos:
        if rect.top < cuerpo.bottom:
            continue                      # está a la altura del cuerpo o encima
        if rect.right <= cuerpo.centerx or rect.left > cuerpo.centerx:
            continue                      # no está debajo
        if mejor is None or rect.top < mejor:
            mejor = rect.top
    return mejor


class Sombra:
    """Dibuja la elipse de sombra de una entidad."""

    def medidas(self, cuerpo: pygame.Rect, suelo_y: int) -> tuple[int, int, int]:
        """`(ancho, alto, alfa)` de la sombra para esta altura.

        Separado del dibujado para poder comprobar la relación altura/tamaño
        sin mirar píxeles, que es lo que de verdad hace útil a la sombra.
        """
        altura = max(0.0, float(suelo_y - cuerpo.bottom))
        if altura >= ALTURA_DE_DESVANECIDO:
            return 0, 0, 0
        cercania = 1.0 - altura / ALTURA_DE_DESVANECIDO
        escala = ESCALA_MINIMA + (1.0 - ESCALA_MINIMA) * cercania
        ancho = max(4, int(cuerpo.width * escala))
        # Un tercio de alto: es la proporción que lee el ojo como «elipse
        # tumbada en el suelo» en vez de como «círculo flotando».
        alto = max(3, int(ancho * 0.34))
        return ancho, alto, int(ALFA_MAXIMO * cercania)

    def dibujar(self, surface: pygame.Surface, cuerpo: pygame.Rect,
                solidos: list[pygame.Rect], camera_offset: pygame.Vector2) -> None:
        """Pinta la sombra de `cuerpo` sobre el suelo que tenga debajo."""
        suelo_y = suelo_bajo(cuerpo, solidos)
        if suelo_y is None:
            return
        ancho, alto, alfa = self.medidas(cuerpo, suelo_y)
        if alfa <= 0:
            return

        capa = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        pygame.draw.ellipse(capa, (0, 0, 0, alfa), capa.get_rect())
        surface.blit(capa, (
            int(cuerpo.centerx - ancho / 2 - camera_offset.x),
            int(suelo_y - alto / 2 - camera_offset.y),
        ))
