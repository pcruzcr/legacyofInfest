"""
Module: patrulla_bspline
System: stage (student assignment — entrada_antenas)
Academic Unit: Unidad III — Curvas paramétricas (B-Spline)

Trayectoria de patrulla B-Spline que se enrolla alrededor de los postes de
antena de la azotea del Stage 2-2.

`docs/16_WORLD_DESIGN.md` §4.3 exige para este escenario: *"Enemy patrol along
B-Spline paths wrapping around antenna poles"*.

Por qué B-Spline y no Bézier
----------------------------
Una Bézier de grado ``n`` se evalúa sobre la base de Bernstein::

    B(t) = Σ  C(n,i) · t^i · (1-t)^(n-i) · P_i
          i=0..n

Cada polinomio de Bernstein es distinto de cero en **todo** el intervalo
(0, 1). Eso implica dos cosas incómodas para una ruta de patrulla:

1. **Soporte global.** Mover un solo punto de control deforma la curva
   completa. Ajustar cómo el enemigo rodea el tercer poste cambiaría su vuelta
   alrededor del primero.
2. **Grado atado al número de puntos.** Con 8 puntos de control la Bézier es de
   grado 7, un polinomio que oscila y se aleja del polígono de control.

Una B-Spline separa ambas cosas mediante un **vector de nodos**::

    C(t) = Σ  N_{i,p}(t) · P_i
          i=0..n-1

donde las bases ``N_{i,p}`` salen de la recursión de Cox–de Boor::

    N_{i,0}(t) = 1  si  t_i ≤ t < t_{i+1},  0 en otro caso

                  t - t_i                     t_{i+p+1} - t
    N_{i,p}(t) = ─────────── N_{i,p-1}(t) + ───────────────── N_{i+1,p-1}(t)
                 t_{i+p} - t_i               t_{i+p+1} - t_{i+1}

La propiedad decisiva es el **soporte local**: ``N_{i,p}(t) = 0`` fuera del
intervalo ``[t_i, t_{i+p+1})``. Cada punto de control influye únicamente sobre
``p+1`` tramos, así que cada poste se ajusta por separado. Y el grado se
mantiene en 3 sin importar cuántos waypoints se agreguen.

La relación entre las tres cantidades es::

    m = n + p + 1

con ``m`` nodos, ``n`` puntos de control y grado ``p``. Con los 8 waypoints de
este escenario y grado 3: ``m = 8 + 3 + 1 = 12`` nodos. Es la restricción que
obliga a ``n ≥ p + 1``: con menos de 4 puntos de control no existe una cúbica,
y `CurveTools.b_spline` devuelve los puntos sin tocar.

Parametrización por longitud de arco
------------------------------------
`CurveTools.b_spline` devuelve muestras uniformes **en el parámetro t**, no en
la distancia. Una curva no tiene rapidez constante respecto de su parámetro:
donde se curva mucho, muestras consecutivas quedan juntas; en los tramos
rectos, separadas. Avanzar de muestra en muestra a ritmo fijo produciría un
enemigo que acelera en las rectas y frena en las vueltas.

Para evitarlo se tabula la longitud acumulada de la poligonal y se avanza sobre
**esa** magnitud, en píxeles por segundo. Es una reparametrización discreta por
longitud de arco:

    s(k) = Σ |Q_j - Q_{j-1}|   para j = 1..k

y dado ``s`` se busca el tramo que lo contiene y se interpola linealmente. Con
160 muestras el error frente a la curva real es de décimas de píxel.
"""
from __future__ import annotations

import bisect

import pygame

from src.framework.processing.curve_tools import CurveTools


class PatrullaBSpline:
    """Recorre una B-Spline a rapidez constante, en vaivén."""

    #: Grado de la B-Spline. Cúbica: el mínimo que da continuidad C² —
    #: posición, tangente y curvatura continuas — que es lo que hace que el
    #: movimiento no muestre esquinas ni tirones.
    GRADO: int = 3

    #: Muestras con las que se discretiza la curva. Suficientes para que la
    #: poligonal sea indistinguible de la curva a 16 px por tile.
    MUESTRAS: int = 160

    def __init__(
        self,
        puntos_control: list[tuple[float, float]],
        velocidad: float = 45.0,
        grado: int = GRADO,
        muestras: int = MUESTRAS,
    ) -> None:
        """
        Args:
            puntos_control: waypoints en coordenadas de mundo, ya ordenados
                por `waypoint_index`.
            velocidad: rapidez de recorrido en píxeles por segundo.
            grado: grado ``p`` de la B-Spline.
            muestras: número de puntos de la poligonal resultante.

        Raises:
            ValueError: si hay menos de ``grado + 1`` puntos de control. La
                condición viene de ``m = n + p + 1``: sin ``n ≥ p + 1`` no
                existe ninguna B-Spline de ese grado. Se falla aquí en vez de
                dejar que `CurveTools` devuelva los puntos sin curvar, que
                produciría un enemigo moviéndose en línea recta sin ningún
                aviso de que la curva nunca se calculó.
        """
        if len(puntos_control) < grado + 1:
            raise ValueError(
                f"PatrullaBSpline necesita al menos {grado + 1} puntos de "
                f"control para grado {grado} (m = n + p + 1); "
                f"recibió {len(puntos_control)}"
            )

        self.puntos_control = [tuple(p) for p in puntos_control]
        self.grado = grado
        self.velocidad = velocidad

        # Evaluación de la curva. Una sola vez, al construir: los puntos de
        # control no cambian, así que recalcularla por fotograma sería gastar
        # 160 evaluaciones de Cox–de Boor para obtener siempre lo mismo.
        muestreo = CurveTools.b_spline(self.puntos_control, grado, muestras)
        self.trayectoria: list[pygame.Vector2] = [
            pygame.Vector2(p) for p in muestreo
        ]

        # Tabla de longitud acumulada.
        self._acumulada: list[float] = [0.0]
        for anterior, actual in zip(self.trayectoria, self.trayectoria[1:]):
            self._acumulada.append(self._acumulada[-1] + anterior.distance_to(actual))
        self.longitud: float = self._acumulada[-1]

        # Estado del recorrido: distancia recorrida y sentido.
        self._s: float = 0.0
        self._sentido: int = 1

    # ── Recorrido ───────────────────────────────────────────────────

    def update(self, dt: float) -> pygame.Vector2:
        """Avanza ``velocidad * dt`` píxeles y devuelve la posición.

        El recorrido es de **vaivén** y no cíclico. La B-Spline que genera
        `CurveTools._uniform_knots` es abierta: su primer y último punto no
        coinciden, así que cerrar el ciclo teletransportaría al enemigo del
        final al principio. Invertir el sentido en los extremos mantiene la
        trayectoria continua y además se lee como una patrulla real.
        """
        if self.longitud <= 0.0:
            return pygame.Vector2(self.trayectoria[0])

        self._s += self.velocidad * dt * self._sentido
        if self._s >= self.longitud:
            self._s = self.longitud - (self._s - self.longitud)
            self._sentido = -1
        elif self._s <= 0.0:
            self._s = -self._s
            self._sentido = 1

        return self.punto_en_arco(self._s)

    def punto_en_arco(self, s: float) -> pygame.Vector2:
        """Punto de la curva a distancia ``s`` medida sobre la propia curva."""
        s = max(0.0, min(self.longitud, s))

        # Búsqueda binaria del tramo. La tabla acumulada es creciente, así que
        # `bisect` la resuelve en O(log n) en vez del O(n) de un barrido.
        i = bisect.bisect_right(self._acumulada, s) - 1
        i = max(0, min(i, len(self.trayectoria) - 2))

        tramo = self._acumulada[i + 1] - self._acumulada[i]
        if tramo <= 1e-9:
            return pygame.Vector2(self.trayectoria[i])

        # Interpolación lineal dentro del tramo.
        u = (s - self._acumulada[i]) / tramo
        return self.trayectoria[i].lerp(self.trayectoria[i + 1], u)

    # ── Dibujado ────────────────────────────────────────────────────

    def draw(
        self,
        surface: pygame.Surface,
        offset: pygame.Vector2,
        mostrar_control: bool = False,
    ) -> None:
        """Dibuja la trayectoria muestreada.

        Args:
            surface: superficie de destino.
            offset: ``camera.offset``; restarlo convierte mundo → pantalla.
            mostrar_control: además, el polígono de control y sus vértices.
                Se activa con la tecla de depuración (F1).
        """
        puntos = [(p.x - offset.x, p.y - offset.y) for p in self.trayectoria]
        if len(puntos) < 2:
            return

        w, h = surface.get_size()
        if all(x < -32 or x > w + 32 or y < -32 or y > h + 32 for x, y in puntos):
            return

        capa = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.lines(capa, (120, 220, 255, 70), False, puntos, 1)

        if mostrar_control:
            ctrl = [(x - offset.x, y - offset.y) for x, y in self.puntos_control]
            # El polígono de control: la B-Spline queda contenida en su
            # envolvente convexa, y verlos juntos hace evidente esa propiedad.
            pygame.draw.lines(capa, (255, 200, 90, 90), False, ctrl, 1)
            for i, (cx, cy) in enumerate(ctrl):
                color = (255, 120, 60, 220) if i in (0, len(ctrl) - 1) else (255, 200, 90, 200)
                pygame.draw.rect(capa, color, pygame.Rect(int(cx) - 2, int(cy) - 2, 5, 5))

        surface.blit(capa, (0, 0))
