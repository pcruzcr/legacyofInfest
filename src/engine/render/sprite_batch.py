"""
Module: sprite_batch
System: engine.render
Academic Unit: N/A
Description: AUD-302 — dibujar muchos sprites con una sola llamada.

Qué es esto, medido antes de escribirlo
=======================================
`SpriteBatch` llevaba desde AUD-148 en la lista de pendientes con la nota
«medir primero en la máquina destino». `scripts/bench_sprite_batch.py` es esa
medición, y en esta máquina —Intel HD Graphics 530, que es la tarjeta que el
juego coge de verdad— dio esto, en milisegundos:

=========  =======  =========  ======  ===========
 sprites    blits    blits()     GPU    GPU+bajar
=========  =======  =========  ======  ===========
      500    0,735      0,533   0,982        3,325
    2.000    3,110      2,334   1,907        5,392
    8.000   12,943     11,005   5,286        8,430
=========  =======  =========  ======  ===========

Tres conclusiones, y las tres mandan sobre lo que hay aquí:

1. **`blits()` gana siempre.** Es el mismo trabajo con el bucle en C: 1,38× con
   500 sprites y 1,18× con 8.000. Gratis y sin riesgo. Es lo que hace esta
   clase.
2. **La GPU gana a partir de unos 2.000 sprites** y llega a 2,08× con 8.000.
3. **Y la pierde entera si hay que bajar los píxeles.** `GPU+bajar` es peor que
   la CPU en todos los casos salvo el de 8.000. Mientras el fotograma se
   componga en una `Surface` —que es lo que hace este motor—, mover los sprites
   a la tarjeta significa subirlos y volver a bajarlos, y eso cuesta más de lo
   que ahorra dibujarlos.

**Por eso aquí no hay ruta de GPU.** No es que falte: es que la medición dice
que hoy perdería. La ruta de GPU tiene sentido el día que el fotograma entero se
componga en la tarjeta, y ese día el umbral son 2.000 sprites. El banco de
pruebas se queda en el repositorio para poder rehacer el número en otra máquina
—en ésta hay una Quadro M2200 que ni SDL ni ModernGL eligen por su cuenta— sin
volver a escribirlo.

Dónde paga en este juego, también medido
========================================
En los escenarios que hay, el fotograma tiene unos setenta y siete `blit`, y la
mayoría son de pantalla completa: fondo, iluminación y post-procesado. Ésos son
uno cada uno y no se pueden agrupar con nada.

Los que **sí** crecen con el contenido son dos, y son los que usan esto: los
degradados de los focos —uno por luz— y las sombras bajo los pies —una por
entidad—. Ahí el lote convierte N llamadas de Python en una.
"""
from __future__ import annotations

import pygame

#: Lo que acepta `Surface.blits`: (origen, destino) o (origen, destino, área) o
#: (origen, destino, área, banderas).
_Orden = tuple


class SpriteBatch:
    """Acumula órdenes de dibujado y las suelta todas juntas.

    Uso::

        lote = SpriteBatch()
        for cosa in muchas_cosas:
            lote.dibujar(cosa.sprite, cosa.posicion)
        lote.volcar(pantalla)

    **Se puede mezclar el origen.** `Surface.blits` acepta una superficie
    distinta por orden, así que un lote puede llevar catorce degradados
    distintos: lo que se ahorra no es el cambio de textura —eso es cosa de una
    GPU— sino las catorce vueltas del intérprete.

    Lo que este lote **no** hace es ordenar. El orden de dibujado es el orden en
    que se añade, igual que si se llamara a `blit` una vez tras otra. Ordenar
    por profundidad sigue siendo responsabilidad de quien dibuja, que es quien
    sabe qué significa «detrás».
    """

    __slots__ = ("_ordenes",)

    def __init__(self) -> None:
        self._ordenes: list[_Orden] = []

    def __len__(self) -> int:
        return len(self._ordenes)

    def dibujar(self, origen: pygame.Surface,
                destino: tuple[int, int] | pygame.Rect,
                area: pygame.Rect | None = None,
                banderas: int = 0) -> None:
        """Encola un sprite. No dibuja nada hasta `volcar`."""
        if banderas:
            self._ordenes.append((origen, destino, area, banderas))
        elif area is not None:
            self._ordenes.append((origen, destino, area))
        else:
            self._ordenes.append((origen, destino))

    def volcar(self, destino: pygame.Surface) -> int:
        """Dibuja todo lo encolado y vacía el lote. Devuelve cuántos.

        Vacía **siempre**, incluso si el volcado falla: un lote que conserva sus
        órdenes tras un error las repetiría en el fotograma siguiente, y un
        sprite duplicado que aparece una vez cada mil fotogramas es de los que
        no se reproducen nunca.
        """
        if not self._ordenes:
            return 0
        cuantos = len(self._ordenes)
        try:
            destino.blits(self._ordenes, doreturn=False)
        finally:
            self._ordenes.clear()
        return cuantos

    def limpiar(self) -> None:
        """Tira lo encolado sin dibujarlo."""
        self._ordenes.clear()
