"""
Module: camara_seguridad
System: stage (student assignment — entrada_antenas)
Academic Unit: Unidad II — Vectores, magnitud, dirección y producto punto

Cámara de vigilancia giratoria de la caseta de seguridad del Stage 2-2.

Barre un arco horizontal y detecta al jugador cuando entra en su cono de
visión. La detección se resuelve **enteramente con álgebra vectorial** usando
`src/engine/utils/math_utils`, sin una sola llamada trigonométrica por
fotograma.

Matemática de la detección
--------------------------
Sean ``C`` la posición de la cámara, ``P`` el centro del jugador y ``m`` el
vector unitario en la dirección de mira. El vector cámara→jugador es
``v = P - C``.

1. **Alcance** — ``vec2_distance(C, P)`` calcula la norma euclidiana

       d = sqrt((Pₓ-Cₓ)² + (P_y-C_y)²)

   Es un escalar: mide *cuánto*, no *hacia dónde*. Si ``d > alcance`` se
   descarta sin más cálculo.

2. **Dirección** — ``vec2_normalize(v)`` divide el vector por su magnitud

       v̂ = v / |v|,    con |v̂| = 1

   El resultado conserva **solo la dirección** y descarta la longitud, que ya
   se midió en el paso 1. Normalizar es obligatorio para el paso 3: sin ello
   el producto punto mezclaría distancia con ángulo.

3. **Ángulo** — ``vec2_dot(v̂, m)`` calcula

       v̂ · m = v̂ₓmₓ + v̂_y m_y = |v̂||m| cos θ = cos θ

   Como ambos vectores son unitarios, sus magnitudes valen 1 y **el producto
   punto es directamente el coseno del ángulo** entre la mira y el jugador.

   El jugador está dentro de un cono de apertura ``fov`` si

       cos θ ≥ cos(fov / 2)

   Se compara el coseno y no el ángulo a propósito. En [0°, 180°] el coseno es
   monótono decreciente, así que comparar cosenos es equivalente a comparar
   ángulos — pero cuesta dos multiplicaciones y una suma, en lugar de un
   ``atan2`` con su análisis de cuadrantes. ``cos(fov/2)`` se calcula **una vez**
   en el constructor y nunca más.

Por qué el eje Y apunta hacia abajo
-----------------------------------
El sistema de coordenadas del motor tiene el origen arriba-izquierda y el eje
Y creciendo hacia abajo (convención de pantalla). Un ángulo de 0° apunta a la
derecha y los ángulos **positivos giran en sentido horario** visualmente, al
revés que en la convención matemática. Por eso la componente Y de la mira se
construye con ``+sin`` y no con ``-sin``: es el mismo círculo unitario, sobre
un eje reflejado.
"""
from __future__ import annotations

import math

import pygame

from src.engine.utils.math_utils import (
    ease_in_out_quad,
    vec2_distance,
    vec2_dot,
    vec2_normalize,
)

#: Segmentos con los que se aproxima el arco del cono al dibujarlo. Doce da un
#: borde liso a esta escala y mantiene el polígono en catorce vértices.
_SEGMENTOS_ARCO = 12

#: Evento que emite la cámara en el flanco de subida de la detección.
EVENTO_DETECCION: str = "stage2_2.camara_detecta"


class CamaraSeguridad:
    """Cámara de vigilancia con cono de visión resuelto por producto punto."""

    def __init__(
        self,
        x: float,
        y: float,
        angulo_base: float = 180.0,
        amplitud_barrido: float = 38.0,
        periodo: float = 4.2,
        fov: float = 70.0,
        alcance: float = 170.0,
        event_bus=None,
    ) -> None:
        """
        Args:
            x, y: posición de la cámara en coordenadas de mundo (píxeles).
            angulo_base: centro del barrido en grados. 0° = derecha,
                180° = izquierda.
            amplitud_barrido: cuántos grados se desvía a cada lado del centro.
            periodo: segundos de un barrido completo ida y vuelta.
            fov: apertura total del cono de visión, en grados.
            alcance: radio de detección en píxeles.
        """
        self.posicion = pygame.Vector2(x, y)
        self.angulo_base = angulo_base
        self.amplitud_barrido = amplitud_barrido
        self.periodo = max(periodo, 1e-3)
        self.fov = fov
        self.alcance = alcance

        # Umbral de detección precalculado. Es el único coseno que se evalúa
        # en toda la vida del objeto: comparar contra él sustituye a calcular
        # el ángulo en cada fotograma.
        self._cos_umbral = math.cos(math.radians(fov / 2.0))

        self._t = 0.0
        self.angulo_actual = angulo_base
        self._bus = event_bus

        # Estado observable, para el dibujado y para el README.
        self.detectando = False
        self.detectando_antes = False
        self.coseno_al_objetivo = -1.0
        self.distancia_al_objetivo = float("inf")

        #: Multiplicador del alcance, entre 0 y 1. Lo fija la escena a partir
        #: del histograma de la zona donde está el jugador (Unidad VII): en el
        #: asfalto soleado la cámara ve lejos; a la sombra, mucho menos.
        self.factor_visibilidad: float = 1.0

    # ── Dirección de mira ───────────────────────────────────────────

    @property
    def direccion_mira(self) -> pygame.Vector2:
        """Vector **unitario** en la dirección a la que apunta la cámara.

        Se construye desde el círculo unitario: ``(cos α, sin α)`` tiene norma
        1 por la identidad pitagórica ``cos²α + sin²α = 1``, así que no hace
        falta normalizarlo.
        """
        rad = math.radians(self.angulo_actual)
        return pygame.Vector2(math.cos(rad), math.sin(rad))

    # ── Ciclo de vida ───────────────────────────────────────────────

    def update(self, dt: float, objetivo_centro: pygame.Vector2) -> bool:
        """Avanza el barrido y evalúa la detección.

        Returns:
            ``True`` si el objetivo está dentro del cono y del alcance.
        """
        # Barrido con easing (Unidad VI). Se construye una onda triangular
        # ``u`` que va 0→1→0 en cada periodo y se pasa por `ease_in_out_quad`.
        #
        # Antes esto era `sin(2πt/T)`. La sinusoide también desacelera en los
        # extremos, pero su aceleración es sinusoidal: nunca es constante. Un
        # servo real bajo par constante tiene **aceleración constante** en cada
        # mitad del recorrido, que es exactamente lo que describe una función
        # cuadrática por tramos. `ease_in_out_quad` es 2t² en la primera mitad
        # y −1+(4−2t)t en la segunda, así que el barrido acelera de forma
        # uniforme al salir del extremo y frena de forma uniforme al llegar al
        # otro.
        self._t = (self._t + dt) % self.periodo
        ciclo = self._t / self.periodo
        u = 2.0 * ciclo if ciclo < 0.5 else 2.0 * (1.0 - ciclo)
        recorrido = ease_in_out_quad(u)
        self.angulo_actual = (
            self.angulo_base - self.amplitud_barrido
            + 2.0 * self.amplitud_barrido * recorrido
        )

        self.detectando_antes = self.detectando

        # ── Paso 1: magnitud ───────────────────────────────────────
        # El alcance efectivo lo modula el histograma de la zona (Unidad VII).
        alcance_efectivo = self.alcance * self.factor_visibilidad
        self.distancia_al_objetivo = vec2_distance(self.posicion, objetivo_centro)
        if self.distancia_al_objetivo > alcance_efectivo:
            self.detectando = False
            self.coseno_al_objetivo = -1.0
            return False

        # ── Paso 2: dirección ─────────────────────────────────────
        hacia_objetivo = objetivo_centro - self.posicion
        direccion_objetivo = vec2_normalize(hacia_objetivo)

        # ── Paso 3: ángulo, vía producto punto de dos unitarios ───
        self.coseno_al_objetivo = vec2_dot(direccion_objetivo, self.direccion_mira)
        self.detectando = self.coseno_al_objetivo >= self._cos_umbral

        # Emisión en el **flanco de subida**: solo cuando la detección pasa de
        # falsa a verdadera. Emitir cada fotograma inundaría el bus con 60
        # eventos por segundo y los suscriptores tendrían que deduplicar.
        if self.detectando and not self.detectando_antes and self._bus is not None:
            self._bus.emit(
                EVENTO_DETECCION,
                x=float(objetivo_centro.x),
                y=float(objetivo_centro.y),
                distancia=self.distancia_al_objetivo,
                coseno=self.coseno_al_objetivo,
            )

        return self.detectando

    # ── Dibujado ────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Dibuja el cono y el cuerpo de la cámara.

        Args:
            surface: superficie de destino.
            offset: desplazamiento de la cámara del juego (``camera.offset``).
                Restarlo convierte mundo → pantalla.
        """
        centro = self.posicion - offset

        # Descarte por pantalla: si el cono no puede tocar el viewport, no se
        # construye el polígono.
        w, h = surface.get_size()
        if (centro.x < -self.alcance or centro.x > w + self.alcance
                or centro.y < -self.alcance or centro.y > h + self.alcance):
            return

        mitad = self.fov / 2.0
        vertices = [(centro.x, centro.y)]
        for i in range(_SEGMENTOS_ARCO + 1):
            a = math.radians(
                self.angulo_actual - mitad
                + (self.fov * i / _SEGMENTOS_ARCO)
            )
            vertices.append((
                centro.x + math.cos(a) * self.alcance,
                centro.y + math.sin(a) * self.alcance,
            ))

        # El cono se pinta en una superficie propia con canal alfa y se compone
        # después. Dibujar un polígono translúcido directamente sobre la
        # pantalla no es posible: `draw.polygon` ignora el alfa del color.
        capa = pygame.Surface((w, h), pygame.SRCALPHA)
        relleno = (255, 64, 48, 90) if self.detectando else (120, 220, 255, 52)
        borde = (255, 96, 72, 200) if self.detectando else (150, 230, 255, 130)
        pygame.draw.polygon(capa, relleno, vertices)
        pygame.draw.polygon(capa, borde, vertices, 1)
        surface.blit(capa, (0, 0))

        # Cuerpo de la cámara: una caja de 8×6 px y un cañón de 7 px en la
        # dirección de mira, para que se lea a qué está apuntando.
        cuerpo = pygame.Rect(0, 0, 8, 6)
        cuerpo.center = (int(centro.x), int(centro.y))
        pygame.draw.rect(surface, (196, 200, 208), cuerpo)
        pygame.draw.rect(surface, (40, 44, 52), cuerpo, 1)

        punta = centro + self.direccion_mira * 7.0
        pygame.draw.line(
            surface,
            (255, 72, 56) if self.detectando else (90, 96, 104),
            (int(centro.x), int(centro.y)),
            (int(punta.x), int(punta.y)),
            2,
        )
