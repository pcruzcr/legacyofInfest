"""
Module: adaptacion_visual
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: VII (Histograma, brillo y contraste)
Description: El ojo que se adapta — el histograma decide la exposición.

QUÉ DEMUESTRA
=============
La rúbrica pide que «`FilterTools.compute_histogram()` **dirija la lógica**».
Aquí el histograma no se dibuja ni se enseña: se **mide** el fotograma, se
saca de él la luminancia media, y de esa medida sale una decisión que cambia
lo que el jugador ve.

Es una auto-exposición, como la de una cámara. El sendero pasa por el túnel
de roca —oscuro— y sale al atardecer —lavado—, y en los dos casos la imagen
se corrige sola. Igual que el ojo tarda un momento en acostumbrarse al entrar
en un sitio oscuro.

LA CADENA DE DECISIÓN
=====================
1. Se reduce el fotograma a 200x150 y se le pide el histograma.
2. De los 256 cajones de luminancia sale la media::

       media = suma(i * cuenta[i]) / total_pixeles          i = 0..255

3. Esa media se compara con una BANDA. Dentro, no se toca nada; fuera, se
   corrige hasta el borde más cercano::

       si  62 <= media <= 108   ->  factor = 1.0   (bien expuesta)
       si  media <  62          ->  factor = 62  / media
       si  media > 108          ->  factor = 108 / media

   La banda no es un adorno: medido con el bot del profesor, este nivel vive
   entre 79 y 88 de luminancia. Con un objetivo único de 118 —la primera
   versión— la corrección se quedaba clavada en el tope y lavaba el cielo y
   las colinas. Una auto-exposición que se come el arte que viene a proteger
   está mal calibrada.

4. El factor **no salta**: se acerca al objetivo poco a poco. Un ojo no se
   adapta de golpe, y una exposición que salta de un fotograma al siguiente
   se ve como un parpadeo.

POR QUÉ SE MIDE EN 200x150 Y CADA SEIS FOTOGRAMAS
=================================================
Medido en esta máquina, con un presupuesto de 16,7 ms por fotograma a 60 fps:

    compute_histogram sobre 800x600 ...... 59,3 ms   imposible
    compute_histogram sobre 200x150 ......  3,1 ms   viable a ratos
    reducir 800x600 -> 200x150 ...........  0,04 ms

Reducir es prácticamente gratis, y la media de luminancia **no cambia** al
reducir: es un promedio, y promediar una muestra representativa da lo mismo.
Midiendo uno de cada seis fotogramas el coste se reparte en 0,52 ms, y como
la corrección se acerca despacio al objetivo, medir a 10 Hz en vez de a 60 no
se nota.

POR QUÉ HAY DOS VÍAS PARA APLICARLA
===================================
Es el mismo problema que ya resolvió `sunset_light.py` con la Unidad V:

    adjust_brightness sobre 800x600 ...... 14,5 ms   NO cabe
    blit BLEND_MULT / BLEND_ADD ..........  0,07 ms  gratis

`apply_reference()` usa `FilterTools.adjust_brightness` y es **la definición
correcta**: es la que documenta el README y contra la que se comparan las
pruebas. `apply()` es la vía rápida que corre en el juego, y consigue el
MISMO producto con mezclas de superficie:

    oscurecer (f < 1) -> BLEND_MULT con gris de f*255
    aclarar   (f > 1) -> s + s*(f-1), o sea una copia atenuada y sumada

Lo segundo tiene truco y se explica en `apply()`. El primer intento sumaba
una constante con BLEND_ADD y estaba MAL: medido sobre el tunel, la media
pasaba de 33 a 148 cuando el objetivo eran 118. Sumar no es multiplicar.
"""
from __future__ import annotations

import pygame

from src.engine.utils.math_utils import clamp
from src.framework.processing.filter_tools import FilterTools


class AdaptacionVisual:
    """Auto-exposición dirigida por el histograma de luminancia."""

    #: Tamaño de la copia que se mide. Ver la cabecera para el porqué.
    TAM_MUESTRA: tuple[int, int] = (200, 150)
    #: Uno de cada cuántos fotogramas se mide.
    CADA_N: int = 6
    #: BANDA MUERTA — dentro de estos límites no se corrige nada.
    #:
    #: Es lo que hace una cámara de verdad, y aquí no es un detalle: la
    #: primera versión sólo tenía un objetivo (118) y corregía SIEMPRE hacia
    #: él. Medido jugando el nivel con el bot del profesor, la luminancia
    #: natural va de 79 a 88 — o sea que la corrección vivía clavada en el
    #: tope de 1,45 y lavaba la escena entera. El cielo azul y las colinas
    #: con contraste salían en gris verdoso: la auto-exposición se estaba
    #: comiendo el arte que venía a proteger.
    #:
    #: Con la banda, un nivel bien pintado no se toca. Sólo se corrige lo que
    #: de verdad se sale: el túnel de roca, que no tiene cielo.
    BANDA_BAJA: float = 62.0
    BANDA_ALTA: float = 108.0
    #: Topes de la corrección. Sin ellos, una pantalla casi negra pediría un
    #: factor enorme y el túnel se vería como un negativo velado.
    FACTOR_MIN: float = 0.82
    FACTOR_MAX: float = 1.45
    #: Fracción del camino al objetivo que se recorre en cada medición. Con
    #: 0.18 y una medición cada 6 fotogramas, adaptarse cuesta ~0,8 s.
    VELOCIDAD: float = 0.18
    #: Por debajo de esta media, la escena se considera oscura. El escenario
    #: lo usa para sugerir la tecla de enfoque.
    UMBRAL_OSCURO: float = 70.0

    def __init__(self) -> None:
        self._factor: float = 1.0
        self._media: float = (self.BANDA_BAJA + self.BANDA_ALTA) / 2
        self._contador: int = 0
        self._cache: dict[int, pygame.Surface] = {}

    # ── Medición ────────────────────────────────────────────────────
    @classmethod
    def luminancia_media(cls, histograma: dict) -> float:
        """Media de luminancia a partir de los 256 cajones.

        `compute_histogram` devuelve las cuentas por cajón, no la media, así
        que hay que hacer la suma ponderada: el cajón `i` vale `i` de
        luminancia y aparece `cuenta[i]` veces.
        """
        cajones = histograma["luminance"]
        total = int(histograma["total_pixels"]) or 1
        acumulado = sum(i * int(c) for i, c in enumerate(cajones))
        return acumulado / total

    def medir(self, surface: pygame.Surface) -> float:
        """Reduce el fotograma, le saca el histograma y devuelve la media."""
        muestra = pygame.transform.scale(surface, self.TAM_MUESTRA)
        self._media = self.luminancia_media(FilterTools.compute_histogram(muestra))
        return self._media

    def factor_objetivo(self, media: float) -> float:
        """El factor de brillo que hace falta, o 1.0 si no hace falta.

        Dentro de la banda muerta se devuelve 1.0: la escena está bien
        expuesta y tocarla sólo puede empeorarla. Fuera, se corrige hasta el
        borde de la banda más cercano — no hasta el centro, porque llevar
        todo al mismo punto medio aplanaría las diferencias de luz entre
        secciones, que son justo lo que da carácter al recorrido.
        """
        if self.BANDA_BAJA <= media <= self.BANDA_ALTA:
            return 1.0
        objetivo = self.BANDA_BAJA if media < self.BANDA_BAJA else self.BANDA_ALTA
        return clamp(objetivo / max(media, 1.0), self.FACTOR_MIN, self.FACTOR_MAX)

    # ── Estado ──────────────────────────────────────────────────────
    @property
    def factor(self) -> float:
        return self._factor

    @property
    def media(self) -> float:
        return self._media

    @property
    def escena_oscura(self) -> bool:
        """La decisión que el histograma dirige, aparte de la exposición."""
        return self._media < self.UMBRAL_OSCURO

    def reiniciar(self) -> None:
        self._factor = 1.0
        self._media = (self.BANDA_BAJA + self.BANDA_ALTA) / 2
        self._contador = 0

    def actualizar(self, surface: pygame.Surface) -> bool:
        """Mide si toca y acerca el factor al objetivo. Devuelve si midió."""
        self._contador += 1
        if self._contador % self.CADA_N:
            return False
        objetivo = self.factor_objetivo(self.medir(surface))
        self._factor += (objetivo - self._factor) * self.VELOCIDAD
        return True

    # ── Aplicación ──────────────────────────────────────────────────
    def apply_reference(self, surface: pygame.Surface) -> pygame.Surface:
        """La definición correcta: `FilterTools.adjust_brightness`.

        Cuesta 14,5 ms sobre 800x600, así que **no se llama en el juego**.
        Existe para el README, para las pruebas y para poder decir contra qué
        se compara la vía rápida.
        """
        return FilterTools.adjust_brightness(surface, self._factor)

    def _gris(self, valor: int, tam: tuple[int, int]) -> pygame.Surface:
        clave = valor * 1000 + tam[0]
        capa = self._cache.get(clave)
        if capa is None or capa.get_size() != tam:
            capa = pygame.Surface(tam)
            capa.fill((valor, valor, valor))
            self._cache[clave] = capa
        return capa

    def apply(self, surface: pygame.Surface) -> None:
        """Vía rápida: multiplicar por `f` con mezclas, sin tocar píxeles.

        OSCURECER (`f < 1`) es directo: `BLEND_MULT` con un gris de `f·255`
        multiplica cada canal por `f`. Es exactamente `adjust_brightness`.

        ACLARAR (`f > 1`) no cabe en una sola mezcla: `BLEND_MULT` no puede
        pasar de 1 y `BLEND_ADD` **suma una constante**, que no es lo mismo.

            El primer intento hacía `BLEND_ADD` con `(f-1)·255`. Medido sobre
            el túnel: la luminancia media pasaba de 33 a **148**, cuando el
            objetivo eran 118. Sumar 115 a un píxel de 33 no es multiplicarlo
            por 1,45 — es aplastar el contraste y lavar las sombras.

        La vuelta es descomponer el producto::

            s · f  =  s + s·(f - 1)

        O sea: una copia de la escena atenuada por `(f-1)` con `BLEND_MULT`,
        sumada encima con `BLEND_ADD`. Dos mezclas, ~0,14 ms, y el resultado
        **es** la multiplicación, no una aproximación.
        """
        f = self._factor
        if abs(f - 1.0) < 0.01:
            return
        tam = surface.get_size()
        if f < 1.0:
            gris = round(clamp(f, 0.0, 1.0) * 255)
            surface.blit(self._gris(gris, tam), (0, 0),
                         special_flags=pygame.BLEND_MULT)
            return
        copia = surface.copy()
        gris = round(clamp(f - 1.0, 0.0, 1.0) * 255)
        copia.blit(self._gris(gris, tam), (0, 0), special_flags=pygame.BLEND_MULT)
        surface.blit(copia, (0, 0), special_flags=pygame.BLEND_ADD)
