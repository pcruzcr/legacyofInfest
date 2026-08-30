"""
Module: enfoque_bordes
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: VII (Convolución, desenfoque y detección de bordes)
Description: Entrecerrar los ojos — Sobel revela lo que la selva esconde.

QUÉ DEMUESTRA
=============
La rúbrica pide `apply_kernel` / `gaussian_blur` / `sobel_edge` / `canny_edge`.
Aquí se usan tres de las cuatro, y no como adorno: mantener **`E`** revela
los contornos de lo que hay en pantalla.

Y resuelve un problema real del nivel. La rana y el ave son verdes sobre una
pared de vegetación verde: a la luz del atardecer, con el tinte ámbar de la
Unidad V encima, cuesta distinguirlas del fondo. Entrecerrar los ojos —que es
lo que hace un gradiente de Sobel— saca las siluetas.

LA CONVOLUCIÓN, PASO A PASO
===========================
Un filtro de convolución recorre la imagen con una ventana de 3x3 y, en cada
píxel, multiplica los nueve vecinos por los nueve pesos del kernel y los suma::

    salida(x,y) = suma_{i,j}  kernel[i,j] * entrada(x+i, y+j)

Sobel usa DOS kernels, uno por dirección. Salen de `get_standard_kernel()`,
no se escriben aquí::

    sobel_x = [[-1, 0, 1],        sobel_y = [[-1, -2, -1],
               [-2, 0, 2],                   [ 0,  0,  0],
               [-1, 0, 1]]                   [ 1,  2,  1]]

`sobel_x` responde a los cambios HORIZONTALES de intensidad: es cero si los
vecinos de la izquierda y los de la derecha valen lo mismo, y grande si hay un
salto. `sobel_y` hace lo propio en vertical. Nótese que cada uno suma cero:
sobre una zona de color plano la respuesta es nula, que es justo lo que se
quiere de un detector de bordes.

El 2 del centro pesa más que los 1 de las esquinas porque el vecino que está
en la misma fila o columna es más informativo que el diagonal; ese suavizado
transversal es lo que separa a Sobel de un gradiente crudo.

La magnitud del borde combina las dos::

    |G| = raiz(Gx^2 + Gy^2)

POR QUÉ HAY DOS VÍAS
====================
Medido en esta máquina (presupuesto: 16,7 ms por fotograma a 60 fps):

    apply_kernel sobre 800x600 ........... 32,9 ms   NO cabe
    sobel_edge  sobre 800x600 ............ 18,4 ms   NO cabe
    sobel_edge  sobre 200x150 ............  0,47 ms
    gaussian_blur(1.2) sobre 200x150 .....  1,40 ms
    ampliar 200x150 -> 800x600 ...........  0,80 ms

`apply_reference()` es la definición didáctica: aplica `sobel_x` y `sobel_y`
por separado con `apply_kernel` y combina las magnitudes. Es la que enseña
las matrices y la que documenta el README — y la que **no** se llama en el
juego, porque cuesta 33 ms.

`apply()` es la vía rápida: mide sobre una copia reducida, difumina el
resultado y lo amplía. Reducir antes de derivar no es hacer trampa — es lo
correcto: un gradiente sobre píxeles vecinos amplifica el ruido, y trabajar a
menor resolución actúa como paso bajo previo. Es la misma razón por la que
Canny difumina antes de derivar.

EL DESENFOQUE, Y POR QUÉ VA DESPUÉS
===================================
`gaussian_blur(sigma=1.2)` se aplica al MAPA DE BORDES, no a la escena. Un
Sobel crudo da líneas de un píxel que, al ampliarse a 800x600, parpadean y se
ven como ruido. Difuminarlas las convierte en un halo que se lee como una
silueta iluminada.
"""
from __future__ import annotations

import numpy as np
import pygame

from src.framework.processing.filter_tools import FilterTools

#: Mantener esta tecla enfoca. `E` de «enfocar»; verificado que el motor no
#: la usa (`src/engine/input/action_map.py`).
TECLA_ENFOQUE = pygame.K_e


class EnfoqueBordes:
    """Realce de contornos por convolución de Sobel, bajo demanda."""

    #: Tamaño al que se reduce para medir. Ver la cabecera para el porqué.
    TAM_MUESTRA: tuple[int, int] = (200, 150)
    #: Sigma del desenfoque que se aplica al mapa de bordes.
    SIGMA: float = 1.2
    #: Cuánto se suma el mapa de bordes sobre la escena, en 0..255.
    #: Con 190 los contornos salían perfectos pero la escena entera se
    #: lavaba: al sumar luz por todas partes, el juego dejaba de verse
    #: debajo. 120 revela las siluetas y deja la escena legible.
    INTENSIDAD: int = 120

    def __init__(self) -> None:
        self._activo = False

    # ── Estado ──────────────────────────────────────────────────────
    @property
    def activo(self) -> bool:
        return self._activo

    @staticmethod
    def hay_tecla(teclas) -> bool:
        """Si la tecla de enfoque está pulsada en este fotograma."""
        return bool(teclas[TECLA_ENFOQUE])

    @classmethod
    def leer_teclado(cls) -> bool:
        return cls.hay_tecla(pygame.key.get_pressed())

    def actualizar(self, pulsada: bool) -> None:
        self._activo = pulsada

    # ── Los kernels, para quien quiera verlos ───────────────────────
    @staticmethod
    def kernels() -> tuple[np.ndarray, np.ndarray]:
        """Las dos matrices de Sobel, tal como las da el framework.

        No se escriben aquí a propósito: la regla del curso es usar lo que el
        motor ya trae. `get_standard_kernel` es la fuente.
        """
        return (FilterTools.get_standard_kernel("sobel_x"),
                FilterTools.get_standard_kernel("sobel_y"))

    # ── Vía de referencia ───────────────────────────────────────────
    @classmethod
    def _componente(cls, surface: pygame.Surface, kernel: np.ndarray) -> np.ndarray:
        """|G| en una dirección, usando SÓLO `apply_kernel`.

        DOS COSAS QUE HAY QUE SABER DE `apply_kernel`, y que se descubrieron
        escribiendo esto:

        **1. Recorta a [0, 255].** Su última línea es
        `result.clip(0, 255).astype(np.uint8)`, así que **la mitad negativa
        del gradiente se pierde**. Medido sobre un borde de oscuro a claro:
        la convolución cruda da `min=-940, max=0`, y tras el recorte queda
        todo a cero. Un operador con signo como Sobel no sobrevive entero a
        una función que devuelve una imagen sin signo — por eso el framework
        trae `sobel_edge` aparte, que hace la magnitud por dentro.

        La vuelta es aplicar el kernel **y su negado**: donde uno recorta a
        cero, el otro conserva el valor. Sumarlos reconstruye |G| sin salirse
        de la API del framework::

            |G| = apply_kernel(k) + apply_kernel(-k)

        **2. Los ejes están transpuestos.** `pygame.surfarray.array3d`
        entrega la imagen como `[x][y]`, pero un kernel se escribe como
        `[fila][columna]` = `[y][x]`. Por eso `sobel_x` responde aquí a los
        bordes horizontales y `sobel_y` a los verticales. Da igual para el
        resultado —la magnitud combina los dos— pero conviene saberlo antes
        de pasar media hora preguntándose por qué un borde vertical no
        aparece.
        """
        mas = pygame.surfarray.array3d(
            FilterTools.apply_kernel(surface, kernel)).astype(np.float32)
        menos = pygame.surfarray.array3d(
            FilterTools.apply_kernel(surface, -kernel)).astype(np.float32)
        return mas + menos

    @classmethod
    def apply_reference(cls, surface: pygame.Surface) -> pygame.Surface:
        """Sobel hecho a mano con `apply_kernel`, kernel a kernel.

        Es la definición didáctica y la que documenta el README. Cuesta unos
        66 ms sobre 800x600 —cuatro convoluciones— así que **no se llama en
        el juego**.
        """
        kx, ky = cls.kernels()
        gx = cls._componente(surface, kx)
        gy = cls._componente(surface, ky)
        magnitud = np.clip(np.sqrt(gx * gx + gy * gy), 0, 255).astype(np.uint8)
        salida = pygame.Surface(surface.get_size())
        pygame.surfarray.blit_array(salida, magnitud)
        return salida

    # ── Vía rápida ──────────────────────────────────────────────────
    def mapa_de_bordes(self, surface: pygame.Surface) -> pygame.Surface:
        """Bordes de la escena, ya difuminados y al tamaño original."""
        muestra = pygame.transform.scale(surface, self.TAM_MUESTRA)
        bordes = FilterTools.sobel_edge(muestra)
        bordes = FilterTools.gaussian_blur(bordes, self.SIGMA)
        return pygame.transform.scale(bordes, surface.get_size())

    def apply(self, surface: pygame.Surface) -> None:
        """Suma los contornos sobre la escena mientras la tecla esté pulsada.

        Se mezcla en `BLEND_ADD` porque un borde es LUZ que se añade: en las
        zonas planas el mapa vale cero y no cambia nada, y en los contornos
        aclara. Con una mezcla normal se taparía la escena con una imagen en
        blanco y negro y dejaría de verse el juego.
        """
        if not self._activo:
            return
        bordes = self.mapa_de_bordes(surface)
        bordes.set_alpha(self.INTENSIDAD)
        surface.blit(bordes, (0, 0), special_flags=pygame.BLEND_ADD)
