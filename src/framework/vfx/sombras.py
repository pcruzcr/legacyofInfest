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

from typing import Any

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


#: Cuántas elipses distintas se guardan antes de tirar la caché.
#:
#: AUD-302. La sombra cambia de tamaño con la altura, así que en un salto se
#: piden decenas de tallas distintas; sin tope, la caché crecería con cada
#: entidad y cada altura hasta ocupar más que los sprites del juego. 96 cubre
#: de sobra las tallas de una escena —lo medido en stage 0 son ocho entidades
#: con menos de treinta tallas vivas— y el desalojo entero es más barato que
#: llevar una cuenta de uso.
_MAXIMO_DE_TALLAS: int = 96


class Sombra:
    """Dibuja la elipse de sombra de una entidad.

    AUD-302 — la elipse se cachea y las sombras van en lote
    =======================================================
    Antes, cada sombra creaba una `Surface` nueva y dibujaba una elipse en ella
    **cada fotograma**: con ocho entidades en pantalla son ocho reservas de
    memoria y ocho rasterizaciones por fotograma para pintar exactamente las
    mismas ocho elipses que el fotograma anterior.

    Ahora se guardan por `(ancho, alto, alfa)`, que es todo lo que las
    distingue, y quien dibuja varias puede pedir un `SpriteBatch` y soltarlas
    de una sola llamada.
    """

    def __init__(self) -> None:
        self._cache: dict[tuple[int, int, int], pygame.Surface] = {}

    def _elipse(self, ancho: int, alto: int, alfa: int) -> pygame.Surface:
        """La elipse de esta talla, reutilizada si ya se pintó."""
        clave = (ancho, alto, alfa)
        capa = self._cache.get(clave)
        if capa is None:
            if len(self._cache) >= _MAXIMO_DE_TALLAS:
                self._cache.clear()
            capa = pygame.Surface((ancho, alto), pygame.SRCALPHA)
            pygame.draw.ellipse(capa, (0, 0, 0, alfa), capa.get_rect())
            self._cache[clave] = capa
        return capa

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
                solidos: list[pygame.Rect], camera_offset: pygame.Vector2,
                lote: Any = None, escala: float = 1.0) -> None:
        """Pinta la sombra de `cuerpo` sobre el suelo que tenga debajo.

        Con `lote`, la encola en vez de dibujarla: quien pinta ocho sombras
        seguidas las suelta todas con una llamada (AUD-302). Sin él se comporta
        exactamente como antes, que es lo que necesitan las entregas que llaman
        a esto por su cuenta.
        
        Parámetro `escala` (AUD-624): factor de profundidad 2.5D para escalar
        la sombra igual que la entidad. 1.0 = sin cambio.
        """
        suelo_y = suelo_bajo(cuerpo, solidos)
        if suelo_y is None:
            return
        ancho, alto, alfa = self.medidas(cuerpo, suelo_y)
        if alfa <= 0:
            return

        # AUD-624 — escalar la sombra igual que la entidad en 2.5D
        ancho = max(4, int(ancho * escala))
        alto = max(3, int(alto * escala))
        if alfa <= 0:
            return

        capa = self._elipse(ancho, alto, alfa)
        posicion = (
            int(cuerpo.centerx - ancho / 2 - camera_offset.x),
            int(suelo_y - alto / 2 - camera_offset.y),
        )
        if lote is not None:
            lote.dibujar(capa, posicion)
            return
        surface.blit(capa, posicion)
