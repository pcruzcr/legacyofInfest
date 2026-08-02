"""
Module: gpu_present
System: engine.render
Academic Unit: N/A
Description: AUD-148 — presentar el fotograma con el renderizador de SDL2, y
la medición que dice cuándo conviene.

Lo primero: lo que MEDÍ, no lo que se supone
=============================================
La fila «post-procesado en GPU» del registro llevaba meses dando por hecho que
mover el post-procesado a la GPU lo aceleraría. Medido en este proyecto, a
800 × 600::

    subir la superficie como textura y presentarla   0,48 ms
    presentar una textura ya subida                  0,19 ms
    bloom con numpy (el actual)                      2,04 ms
    bloom en GPU (aditivo, tres pasadas)             9,47 ms

**El bloom en GPU salió cinco veces más lento.** No porque la idea sea mala,
sino porque la medición se hizo sin GPU: con `SDL_VIDEODRIVER=dummy` —y en
cualquier CI— el «renderizador acelerado» de SDL cae a software, y entonces
son los mismos píxeles por CPU más el coste de subirlos.

Así que la respuesta honesta a «¿movemos el post-procesado a la GPU?» es:
**depende de la máquina, y hay que medirlo en la máquina**. Por eso esto viene
con `scripts/bench_gpu_postproc.py`, que reproduce la tabla de arriba donde se
ejecute, y **apagado por defecto**.

Lo que sí es barato en cualquier caso
--------------------------------------
Presentar (0,19–0,48 ms) y las operaciones que la textura hace sola: tinte por
modulación de color, alfa y modos de mezcla. Eso es un fundido, un destello y
un tinte de daño **gratis**, que hoy cuestan una pasada de numpy cada uno.

Lo que NO se puede, y no lo va a poder este camino
---------------------------------------------------
El filtro de daltonismo. Mezcla canales entre sí —parte del verde va al
rojo— y el renderizador de SDL2 **no tiene shaders**: modula, mezcla y escala,
pero no sabe combinar canales. Para eso hace falta OpenGL de verdad, que es
otra reescritura y otra dependencia. AUD-138 lo dejó en 3,1 ms por CPU, que
cabe en el presupuesto.

Por qué no está enchufado en `App`
-----------------------------------
Un `_sdl2.Window` y el `pygame.display` clásico **no pueden convivir en la
misma ventana**: hay que elegir. Cambiar el motor entero al renderizador toca
el escalado, las transiciones, el volcado de escenas y las quince entregas de
los estudiantes. Eso no se hace a cambio de una mejora que no he podido medir.

Esto queda como pieza opcional y medible: quien tenga una GPU de verdad puede
ejecutar el banco de pruebas, ver su número y decidir con datos.
"""
from __future__ import annotations

import logging

import pygame

logger = logging.getLogger(__name__)


def hay_soporte() -> bool:
    """¿Está disponible el renderizador de SDL2 en esta instalación?"""
    try:
        from pygame._sdl2 import video  # noqa: F401
    except ImportError:
        return False
    return True


class PresentadorGPU:
    """Presenta una superficie por el renderizador de SDL2.

    Es **opcional y está apagado por defecto**. Se construye con la ventana
    que va a dibujar, y a partir de ahí `presentar(superficie)` sube el
    fotograma y lo pinta, aplicando tinte, destello y fundido con las
    operaciones que la textura hace sola.
    """

    def __init__(self, tamano: tuple[int, int], titulo: str = "Legacy of Infest") -> None:
        from pygame._sdl2 import video as sdl2

        self._ventana = sdl2.Window(titulo, size=tamano)
        self._render = sdl2.Renderer(self._ventana)
        self._sdl2 = sdl2
        self._tamano = tamano
        #: Tinte multiplicativo, de 0 a 255 por canal. Blanco = sin tinte.
        self.tinte: tuple[int, int, int] = (255, 255, 255)
        #: Opacidad del fotograma, para fundidos. 255 = opaco.
        self.opacidad: int = 255

    @property
    def tamano(self) -> tuple[int, int]:
        return self._tamano

    def presentar(self, superficie: pygame.Surface) -> None:
        """Sube el fotograma y lo pinta con el tinte y la opacidad actuales.

        El tinte y la opacidad los aplica la propia textura: son parámetros
        del dibujado, no píxeles que haya que recorrer. Ésa es la parte del
        post-procesado que la GPU regala aunque el resto no compense.
        """
        textura = self._sdl2.Texture.from_surface(self._render, superficie)
        textura.color = pygame.Color(*self.tinte)
        textura.alpha = max(0, min(255, self.opacidad))
        self._render.clear()
        textura.draw()
        self._render.present()

    def destello(self, color: tuple[int, int, int], opacidad: int = 200) -> None:
        """Un destello a pantalla completa, sin tocar un solo píxel a mano."""
        textura = self._sdl2.Texture(self._render, self._tamano)
        textura.color = pygame.Color(*color)
        textura.alpha = max(0, min(255, opacidad))
        textura.blend_mode = pygame.BLENDMODE_ADD
        textura.draw()

    def cerrar(self) -> None:
        self._ventana.destroy()
