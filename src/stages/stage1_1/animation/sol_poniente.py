"""
Module: sol_poniente
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: VI (Animación dirigida por easing e interacción por EventBus)
Description: El sol que baja hacia el horizonte conforme se sube el sendero.

QUÉ DEMUESTRA
=============
La rúbrica de la Evaluación Práctica II pide «animación dirigida por easing;
interacción propia de `EventBus`». Este módulo es las dos cosas:

1. La posición del sol NO es lineal en el avance del jugador: pasa por
   `ease_in_out_sine`, y esa curva es la que le da el ritmo.
2. Al cruzar el horizonte, el escenario emite un evento **suyo** —no uno del
   motor— y quien quiera reaccionar se suscribe.

POR QUÉ `ease_in_out_quad` Y NO OTRA
====================================
Comparadas las que ofrece `src/engine/utils/math_utils.py` —no se escribe
ninguna aquí, esa es la regla del curso—:

* **Lineal** (sin easing) — el sol baja como un ascensor. Es lo que más se
  nota que está mal: un cuerpo celeste no cambia de altura a ritmo constante.
* **`ease_in_quad`** (lento arriba, rápido abajo) — parece que se cae.
* **`ease_out_quad`** (rápido arriba, lento abajo) — parece que frena solo.
* **`ease_in_out_quad`** — arranca despacio en lo alto, gana velocidad a media
  bajada y **se frena al tocar el horizonte**. Ese frenado final es lo que
  hace que se lea como un atardecer y no como un objeto cayendo. Y coincide
  con lo que se ve de verdad: cerca del horizonte la refracción atmosférica
  aplasta el disco y su descenso aparente se ralentiza.

`ease_in_out_quad` es una parábola partida por la mitad::

    u(t) = 2t²                      para t < 0,5
    u(t) = -1 + (4 - 2t)·t          para t ≥ 0,5

u(0) = 0, u(0,5) = 0,5 y u(1) = 1, así que respeta los extremos: el sol
empieza donde debe y acaba donde debe, pase lo que pase en medio. La derivada
es 4t en la primera mitad y 4-4t en la segunda: nula en los dos extremos y
máxima en el centro. Eso **es** el arranque y el frenado suaves.

POR QUÉ VA EN `dibujar_fondo()` Y NO EN `draw()`
================================================
`StageScene.dibujar_fondo()` (AUD-162) se llama **después del parallax y antes
del mapa de baldosas**. Dibujar ahí hace que las colinas de `BG_Far` tapen el
disco: el sol *se pone detrás del paisaje*, que es lo que tiene que pasar.
Desde `draw()` se pintaría encima de todo y el sol flotaría delante de las
montañas.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.utils.math_utils import clamp, ease_in_out_quad

#: Evento **propio** de este escenario. El prefijo con el id del escenario
#: evita chocar con los nombres del motor (`src/engine/core/events.py`), que
#: son cadenas planas en mayúsculas sin espacio de nombres.
EVENTO_SOL_EN_EL_HORIZONTE = "stage1_1:sol_en_el_horizonte"


class SolPoniente:
    """El disco solar y su recorrido por el cielo."""

    #: Fracción del ancho de pantalla donde nace y donde muere el sol. Va de
    #: derecha a izquierda: el jugador sube hacia el este y el sol queda atrás.
    X_INICIO: float = 0.78
    X_FIN: float = 0.16
    #: Altura en fracción del alto de pantalla. El final queda por debajo de
    #: la línea del horizonte pintada en el mapa (filas 6..19 de 40), para que
    #: el disco desaparezca tras las colinas en vez de posarse encima.
    Y_INICIO: float = 0.14
    Y_FIN: float = 0.46

    RADIO: int = 22
    #: A partir de aquí se considera que ya tocó el horizonte y se emite el
    #: evento. No es 1.0 porque para entonces ya está tapado y nadie lo vería.
    UMBRAL_HORIZONTE: float = 0.82

    NUCLEO = (254, 244, 206)
    MEDIO = (250, 206, 128)
    HALO = (244, 168, 96)

    def __init__(self) -> None:
        self._avisado = False

    # ── El recorrido ────────────────────────────────────────────────
    def progreso_suavizado(self, avance: float) -> float:
        """`avance` ∈ [0,1] del jugador → `u` ∈ [0,1] del sol, con easing."""
        return ease_in_out_quad(clamp(avance, 0.0, 1.0))

    def posicion(self, avance: float) -> tuple[int, int]:
        """Centro del disco en coordenadas de PANTALLA.

        No lleva el desplazamiento de la cámara a propósito: el sol está en el
        infinito. Un objeto a distancia infinita no tiene paralaje, así que
        moverlo con la cámara sería tan falso como que se moviera la Luna al
        andar.
        """
        u = self.progreso_suavizado(avance)
        x = (self.X_INICIO + (self.X_FIN - self.X_INICIO) * u) * settings.INTERNAL_WIDTH
        y = (self.Y_INICIO + (self.Y_FIN - self.Y_INICIO) * u) * settings.INTERNAL_HEIGHT
        return int(x), int(y)

    def radio_del_halo(self, avance: float) -> int:
        """El halo crece al bajar: cerca del horizonte la luz atraviesa más
        atmósfera y el disco se ve más grande y más difuso."""
        return int(self.RADIO * (1.35 + 0.65 * self.progreso_suavizado(avance)))

    # ── El evento propio ────────────────────────────────────────────
    def revisar_horizonte(self, avance: float, event_bus) -> bool:
        """Emite el evento del escenario la PRIMERA vez que cruza el umbral.

        Devuelve si lo emitió en esta llamada. `_avisado` existe para que no
        se dispare sesenta veces por segundo mientras el jugador esté pasado
        del umbral — un evento de «ya ocurrió» que se re-emite cada fotograma
        es el defecto que el propio profesor apuntó en AUD-602 con el cierre
        de nivel.
        """
        if self._avisado or event_bus is None:
            return False
        if self.progreso_suavizado(avance) < self.UMBRAL_HORIZONTE:
            return False
        self._avisado = True
        event_bus.emit(EVENTO_SOL_EN_EL_HORIZONTE, progreso=avance)
        return True

    def reiniciar(self) -> None:
        """Vuelve a armar el aviso. Al reaparecer tras morir, el sol vuelve
        atrás con el jugador y el evento tiene que poder repetirse."""
        self._avisado = False

    # ── Dibujo ──────────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, avance: float) -> None:
        cx, cy = self.posicion(avance)
        halo = self.radio_del_halo(avance)

        # El halo se dibuja aparte y se mezcla en ADD para que sume luz en vez
        # de tapar el cielo: un sol que recorta un círculo opaco sobre el
        # degradado se ve pegado encima, no dentro.
        capa = pygame.Surface((halo * 2, halo * 2), pygame.SRCALPHA)
        for r, color, alfa in ((halo, self.HALO, 40), (int(halo * 0.62), self.MEDIO, 70)):
            pygame.draw.circle(capa, (*color, alfa), (halo, halo), max(1, r))
        surface.blit(capa, (cx - halo, cy - halo), special_flags=pygame.BLEND_RGB_ADD)

        pygame.draw.circle(surface, self.MEDIO, (cx, cy), self.RADIO)
        pygame.draw.circle(surface, self.NUCLEO, (cx, cy), int(self.RADIO * 0.72))
