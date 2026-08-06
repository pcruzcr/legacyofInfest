"""
Module: sprite_batch
System: engine.render
Academic Unit: N/A
Description: AUD-302 — dibujar muchos sprites con una sola llamada.

Qué es esto, medido antes de escribirlo
=======================================
`SpriteBatch` llevaba desde AUD-148 en la lista de pendientes con la nota
«medir primero en la máquina destino». `scripts/bench_sprite_batch.py` es esa
medición, y AUD-301 la hizo con **las dos tarjetas del equipo**, que resultó
ser la mitad del asunto.

Milisegundos, mediana de treinta pasadas:

===========  ==========  ==========  ==========  ============
   sprites   Intel: CPU   Intel: GPU  Quadro: GPU  Quadro: +bajar
===========  ==========  ==========  ==========  ============
        500       0,651       1,145        0,202          1,906
      2.000       4,014       2,109        0,330          1,454
      8.000      16,882       5,177        0,898          2,020
===========  ==========  ==========  ==========  ============

(«CPU» es `Surface.blits()`, que es lo que hace esta clase; la columna de CPU no
depende de la tarjeta y se da una sola vez.)

Lo que dice, y lo que corrige
=============================
1. **`blits()` gana siempre a los blits sueltos.** 1,25× con 500 y 1,23× con
   8.000, medido en la misma pasada. Gratis y sin riesgo: es esta clase.
2. **La tarjeta importa muchísimo más de lo que parecía.** La Quadro dibuja
   8.000 sprites en 0,898 ms; la Intel tarda 5,177. Y ojo con esto: el juego
   coge la Intel salvo que se dé de alta `python.exe` como «alto rendimiento»
   en Windows, cosa que ni SDL ni ModernGL hacen por su cuenta.
3. **Y aquí me equivoqué al predecir.** Escribí que bajar los píxeles de una
   tarjeta discreta sería *peor* por tener que cruzar el bus PCIe. Medido, es
   **tres veces mejor**: 1,45–2,02 ms en la Quadro contra 5,69–8,31 en la
   Intel. La conclusión que saqué de aquella predicción —«nunca compensa»— era
   falsa, y ésta es la buena: con la Quadro, la GPU gana **también con lectura
   de vuelta** a partir de unos 1.500 sprites.

**Por eso aquí sigue sin haber ruta de GPU, pero por otro motivo.** No es que
pierda: es que el juego no llega a esos números. Un escenario real dibuja unas
veinte entidades, y a 500 sprites la CPU todavía gana (0,651 contra 1,906 con
lectura). La ruta de GPU es correcta y está medida; el día que el fotograma
entero se componga en la tarjeta —sin lectura de vuelta— gana desde el primer
sprite, 4,2× con 500 y 10,4× con 8.000.

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
