"""
Module: contorno
System: framework.vfx
Academic Unit: IV (dibujado)

AUD-304 — el contorno de silueta, reutilizable, y disponible para los enemigos.

De dónde sale
=============
AUD-190 midió que el jugador se fundía con el decorado —contraste de luminancia
de 1,01 a 1,18 sobre quince de los dieciséis escenarios, donde 1,0 es
literalmente indistinguible— y lo arregló con un contorno de un píxel: la misma
imagen teñida de claro, dibujada en cuatro desplazamientos, detrás.

Esa solución vivía entera dentro de `player.py`, así que **sólo el jugador la
tenía**. El reporte 87 §19.2 lo dejó anotado como la única fila de accesibilidad
que valía la pena cerrar de inmediato, porque no es diseño nuevo: es la misma
función aplicada a otro grupo de entidades.

Aquí está la función, sin dueño. `player.py` la usa siempre; `enemy_base.py` la
usa cuando el jugador enciende la opción.

Por qué los enemigos NO lo llevan por defecto
==============================================
Dos razones medidas, y ninguna es de rendimiento:

1. **El contorno del jugador existe para decir «este eres tú».** Si todo lo que
   se mueve lleva borde, esa señal se pierde — que es exactamente lo que
   AUD-190 vino a crear.
2. **Cambiaría el aspecto por defecto de los dieciséis mapas entregados**, y la
   invariante 2 dice que las veintiséis clases de escenario siguen funcionando
   sin tocar una línea. «Funcionar» incluye verse como se veían el día que se
   calificaron.

Así que es una preferencia apagada por defecto, `contorno_de_enemigos`, junto al
resto de accesibilidad. Quien la necesita la enciende y paga sus cuatro blits
por enemigo; quien no, no paga nada.

Por qué el enemigo lleva otro color
------------------------------------
Ámbar y no el blanco roto del jugador, y la diferencia **no es de tono sino de
luminancia** (0,79 contra 0,19 en la escala WCAG). Un contorno que sólo se
distinguiera por el matiz sería inútil precisamente para quien enciende esta
opción: los tres modos daltónicos del juego colapsan tonos, no brillos.
"""
from __future__ import annotations

import pygame

#: Los cuatro desplazamientos de un píxel. En cruz y no en estrella de ocho: el
#: diagonal añade cuatro blits más por entidad y a esta escala de pixel art no
#: se distingue del de cuatro.
COMPENSACIONES: tuple[tuple[int, int], ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))

#: Un blanco roto, no blanco puro: el blanco puro sobre pixel art oscuro se lee
#: como un brillo y no como un borde.
COLOR_JUGADOR: tuple[int, int, int] = (236, 232, 220)

#: Ámbar para el enemigo. Ver el encabezado: se separa del color del jugador por
#: luminancia, que es lo único que sobrevive a un filtro daltónico.
COLOR_ENEMIGO: tuple[int, int, int] = (240, 168, 64)

#: Cacheadas por `id(frame)` y por color: se dibujan cuatro por entidad y por
#: fotograma, así que recalcularlas sería tirar trabajo. La clave lleva el color
#: porque el mismo fotograma puede pedirse teñido de dos maneras — un sprite
#: compartido entre el jugador y un enemigo, que es el caso de los maniquíes de
#: prueba.
_siluetas: dict[tuple[int, tuple[int, int, int]], pygame.Surface] = {}


def silueta_de(
    frame: pygame.Surface,
    color: tuple[int, int, int] = COLOR_JUGADOR,
) -> pygame.Surface:
    """El mismo fotograma, teñido de un color plano, conservando su alfa."""
    clave = (id(frame), color)
    cacheada = _siluetas.get(clave)
    if cacheada is not None:
        return cacheada
    silueta = frame.copy()
    # BLEND_RGB_MAX y no MIN: los sprites de este juego son oscuros, y
    # `min(oscuro, claro)` devuelve el oscuro — la primera versión de esto
    # (AUD-190) dibujaba cuatro copias de la misma sombra y el contraste medido
    # no se movía ni una centésima. `max` lleva cada canal al color del borde
    # allí donde el sprite es más oscuro, y las variantes RGB no tocan el alfa,
    # así que la forma recortada se conserva.
    silueta.fill(color, special_flags=pygame.BLEND_RGB_MAX)
    _siluetas[clave] = silueta
    return silueta


def dibujar_con_contorno(
    surface: pygame.Surface,
    frame: pygame.Surface,
    destino: tuple[int, int],
    color: tuple[int, int, int] = COLOR_JUGADOR,
) -> None:
    """Dibuja `frame` en `destino` con su contorno de un píxel detrás."""
    silueta = silueta_de(frame, color)
    x, y = destino
    for dx, dy in COMPENSACIONES:
        surface.blit(silueta, (x + dx, y + dy))
    surface.blit(frame, destino)
