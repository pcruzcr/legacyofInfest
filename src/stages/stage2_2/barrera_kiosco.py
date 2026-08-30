"""
Module: barrera_kiosco
System: stage (student assignment — entrada_antenas)
Academic Unit: Unidad VI — Animación e interpolación con funciones de easing

Barrera de control de acceso del kiosco de seguridad del Stage 2-2.

El brazo gira entre la posición cerrada (horizontal, apuntando al parqueo) y la
abierta (casi vertical). La animación **no es lineal**: usa dos funciones de
easing distintas de `src/engine/utils/math_utils.py`, una para cada sentido,
porque subir y bajar son movimientos físicamente distintos.

Por qué easing y no interpolación lineal
----------------------------------------
Una interpolación lineal ``ángulo = a + (b - a) · t`` recorre el arco a
velocidad angular **constante**, lo que implica aceleración infinita en el
instante de arranque y frenado instantáneo al llegar. Nada mecánico se mueve
así, y el ojo lo lee como un salto: el brazo aparece en su destino en vez de
llegar a él.

Una función de easing reemplaza ``t`` por ``f(t)`` con ``f(0)=0`` y ``f(1)=1``,
deformando el reparto del recorrido en el tiempo sin cambiar los extremos.

**Al abrir — `ease_out_bounce`.** El brazo sube empujado por el motor, choca
contra el tope superior y rebota dos o tres veces antes de asentarse. Es lo que
hace una barrera real, cuyo brazo es una palanca larga con inercia. La función
es una parábola por tramos::

    f(t) = 7.5625·t²                          si t < 1/2.75
    f(t) = 7.5625·(t−1.5/2.75)² + 0.75        si t < 2/2.75
    f(t) = 7.5625·(t−2.25/2.75)² + 0.9375     si t < 2.5/2.75
    f(t) = 7.5625·(t−2.625/2.75)² + 0.984375  en otro caso

Cada tramo es un rebote con la altura reducida: 1, 0.75, 0.9375 y 0.984375
convergen a 1, que es la pérdida de energía en cada impacto.

**Al cerrar — `ease_in_out_quad`.** El brazo baja frenado por su propio
mecanismo, sin rebote: acelera al soltarse y desacelera al acercarse al
cierre. Es simétrica y de aceleración constante por tramo::

    f(t) = 2t²                    si t < 0.5
    f(t) = −1 + (4 − 2t)·t        si t ≥ 0.5

Sistema de coordenadas
----------------------
El ángulo sigue la convención del motor: 0° apunta a la derecha y el eje Y
crece hacia abajo, así que la dirección es ``(cos α, sin α)`` y los ángulos
crecientes giran en sentido horario en pantalla. Cerrada = 180° (horizontal,
hacia el parqueo); abierta = 252° (casi vertical, levemente inclinada).

Nota de diseño: la barrera **no genera colisión**. Es un elemento animado, no
un obstáculo. Añadirle un rectángulo sólido cambiaría la geometría del nivel y
`level_metrics.analyse_stage` volvería a evaluar la ruta desde cero.
"""
from __future__ import annotations

import math

import pygame

from src.engine.utils.math_utils import ease_in_out_quad, ease_out_bounce

#: Evento que emite la barrera al terminar de abrirse.
EVENTO_ABIERTA: str = "stage2_2.barrera_abierta"

_ANGULO_CERRADA: float = 180.0
_ANGULO_ABIERTA: float = 252.0
_LARGO_BRAZO: float = 46.0

#: Duraciones en segundos. Abrir es más rápido que cerrar: el motor empuja
#: contra la gravedad al subir y la acompaña al bajar.
_DUR_ABRIR: float = 0.85
_DUR_CERRAR: float = 1.30

#: Segundos que la barrera permanece abierta antes de volver a bajar.
_ESPERA_ABIERTA: float = 5.0


class BarreraKiosco:
    """Brazo de barrera animado con dos funciones de easing."""

    def __init__(self, x: float, y: float, event_bus=None) -> None:
        """
        Args:
            x, y: pivote del brazo en coordenadas de mundo.
            event_bus: bus opcional. Si se entrega, la barrera emite
                `EVENTO_ABIERTA` al completar la apertura.
        """
        self.pivote = pygame.Vector2(x, y)
        self._bus = event_bus

        self._estado = "cerrada"      # cerrada | abriendo | abierta | cerrando
        self._t = 0.0                 # tiempo dentro de la transición actual
        self._espera = 0.0

        # Estado observable, para depuración y para el README.
        self.angulo = _ANGULO_CERRADA
        self.progreso = 0.0           # f(t) de la función de easing

    # ── Interacción ─────────────────────────────────────────────────

    def abrir(self) -> None:
        """Pide la apertura. Reinicia la espera si ya estaba abierta."""
        if self._estado in ("cerrada", "cerrando"):
            self._estado = "abriendo"
            self._t = 0.0
        elif self._estado == "abierta":
            self._espera = 0.0

    # ── Ciclo de vida ───────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._estado == "abriendo":
            self._t += dt
            u = min(1.0, self._t / _DUR_ABRIR)
            # Medido: la función nunca supera 1.0. Sube a 0.840, **cae** a
            # 0.773, vuelve a 0.939 y se asienta en 1.0. Los rebotes son
            # caídas por debajo del destino, no sobrepasos: el brazo llega
            # arriba, se vence un poco por su peso, y se recompone.
            self.progreso = ease_out_bounce(u)
            if u >= 1.0:
                self._estado = "abierta"
                self._espera = 0.0
                self.progreso = 1.0
                if self._bus is not None:
                    self._bus.emit(EVENTO_ABIERTA, x=self.pivote.x, y=self.pivote.y)

        elif self._estado == "abierta":
            self._espera += dt
            self.progreso = 1.0
            if self._espera >= _ESPERA_ABIERTA:
                self._estado = "cerrando"
                self._t = 0.0

        elif self._estado == "cerrando":
            self._t += dt
            u = min(1.0, self._t / _DUR_CERRAR)
            self.progreso = 1.0 - ease_in_out_quad(u)
            if u >= 1.0:
                self._estado = "cerrada"
                self.progreso = 0.0
        else:
            self.progreso = 0.0

        self.angulo = _ANGULO_CERRADA + (_ANGULO_ABIERTA - _ANGULO_CERRADA) * self.progreso

    # ── Dibujado ────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        base = self.pivote - offset
        w, h = surface.get_size()
        if base.x < -_LARGO_BRAZO or base.x > w + _LARGO_BRAZO:
            return

        rad = math.radians(self.angulo)
        direccion = pygame.Vector2(math.cos(rad), math.sin(rad))
        punta = base + direccion * _LARGO_BRAZO

        # Poste del pivote
        pygame.draw.rect(surface, (196, 192, 184),
                         pygame.Rect(int(base.x) - 3, int(base.y) - 2, 6, 16))
        pygame.draw.rect(surface, (150, 146, 140),
                         pygame.Rect(int(base.x) - 3, int(base.y) - 2, 2, 16))

        # Brazo a franjas rojas y blancas: cuatro tramos alternos sobre el
        # segmento pivote→punta.
        for i in range(4):
            t0, t1 = i / 4.0, (i + 1) / 4.0
            p0 = base + direccion * (_LARGO_BRAZO * t0)
            p1 = base + direccion * (_LARGO_BRAZO * t1)
            color = (220, 80, 60) if i % 2 == 0 else (240, 240, 240)
            pygame.draw.line(surface, color,
                             (int(p0.x), int(p0.y)), (int(p1.x), int(p1.y)), 4)

        # Contrapeso en el pivote y remate en la punta
        pygame.draw.circle(surface, (58, 58, 66), (int(base.x), int(base.y)), 4)
        pygame.draw.circle(surface, (58, 58, 66), (int(punta.x), int(punta.y)), 2)
