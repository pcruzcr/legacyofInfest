"""
Module: camara_objetivo
System: stage (student assignment)
Academic Unit: Unidad III (curvas) + Unidad VI (easing / animacion).

Camara de objetivo: cuando el jugador llega a cierto punto del nivel, la
camara se despega de el, viaja hasta el siguiente obstaculo importante para
ensenarlo, se queda un instante y vuelve. Sirve de guia: el patio mide 2400 px
y el muro de bloqueo no se ve hasta que ya lo tienes encima.

Por que no uso `Camera.set_cinematica_path()` del motor
=======================================================
Existe, pero no sirve para esto: su `_seguir_spline()` es un esbozo que
interpola en linea recta (el propio comentario del motor dice "stub — real
usaria CurveTools.catmull_rom"), avanza en bucle infinito con `% 1.0` y solo
corre si la camara esta en modo `cinematica`, que secuestraria el nivel entero.
Aqui la camara vuelve sola al jugador, que es justo lo que hace falta.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.utils.math_utils import ease_in_out_quad
from src.framework.processing.curve_tools import CurveTools


class Objetivo:
    """Un punto que la camara ensena, y el x a partir del cual se dispara."""

    def __init__(self, x: float, y: float, disparo_x: float, rotulo: str) -> None:
        self.punto = pygame.Vector2(x, y)
        self.disparo_x = disparo_x
        self.rotulo = rotulo
        self.mostrado = False


class CamaraObjetivo:
    """Anima la camara hasta un objetivo y la devuelve al jugador.

    Tres fases: ida (`IDA`), espera quieta (`ESPERA`) y vuelta (`VUELTA`). La
    trayectoria no es una recta: son 24 muestras de una spline Catmull-Rom que
    pasa por un punto intermedio elevado, para que el barrido tenga una curva
    reconocible en vez de un desplazamiento plano.
    """

    IDA = 0.9
    ESPERA = 0.5
    VUELTA = 0.9
    TOTAL = IDA + ESPERA + VUELTA

    def __init__(self, objetivos: list[Objetivo], mapa_ancho: int, mapa_alto: int) -> None:
        self._objetivos = objetivos
        self._mapa = (mapa_ancho, mapa_alto)
        self._activo: Objetivo | None = None
        self._t = 0.0
        self._ruta: list[tuple[float, float]] = []
        self._origen = pygame.Vector2()
        self._fuente = pygame.font.Font(None, 20)

    # ── disparo ────────────────────────────────────────────────
    def _mira(self, objetivo: Objetivo, camara_offset: pygame.Vector2) -> None:
        """Arma la spline que va del encuadre actual al del objetivo."""
        self._activo = objetivo
        self._t = 0.0
        self._origen = pygame.Vector2(camara_offset)
        destino = self._encuadre(objetivo.punto)
        # Punto intermedio 40 px por encima de la recta: da el arco.
        medio = (self._origen + destino) * 0.5 - pygame.Vector2(0, 40)
        self._ruta = CurveTools.catmull_rom(
            [tuple(self._origen), tuple(medio), tuple(destino)], n_samples=24
        )

    def _encuadre(self, punto: pygame.Vector2) -> pygame.Vector2:
        """Offset de camara que deja `punto` en el centro, sin salirse del mapa."""
        x = punto.x - settings.INTERNAL_WIDTH / 2
        y = punto.y - settings.INTERNAL_HEIGHT / 2
        max_x = max(0, self._mapa[0] - settings.INTERNAL_WIDTH)
        max_y = max(0, self._mapa[1] - settings.INTERNAL_HEIGHT)
        return pygame.Vector2(min(max(x, 0), max_x), min(max(y, 0), max_y))

    def _en_ruta(self, avance: float) -> pygame.Vector2:
        """Punto de la spline en `avance` (0..1)."""
        if not self._ruta:
            return pygame.Vector2(self._origen)
        i = min(int(avance * (len(self._ruta) - 1)), len(self._ruta) - 1)
        return pygame.Vector2(self._ruta[i])

    # ── ciclo de vida ──────────────────────────────────────────
    def update(self, dt: float, jugador, camara) -> None:
        if self._activo is None:
            if jugador is None:
                return
            for obj in self._objetivos:
                if not obj.mostrado and jugador.position.x >= obj.disparo_x:
                    obj.mostrado = True
                    self._mira(obj, camara.offset)
                    break
            return

        self._t += dt
        if self._t >= self.TOTAL:
            self._activo = None
            self._ruta = []
            return

        if self._t < self.IDA:
            camara.offset.update(self._en_ruta(ease_in_out_quad(self._t / self.IDA)))
        elif self._t < self.IDA + self.ESPERA:
            camara.offset.update(self._en_ruta(1.0))
        else:
            avance = (self._t - self.IDA - self.ESPERA) / self.VUELTA
            # La vuelta no rebobina la spline: interpola del objetivo al
            # encuadre del jugador *ahora*, que se ha movido mientras tanto.
            destino = self._encuadre(pygame.Vector2(jugador.position)) if jugador else self._origen
            camara.offset.update(self._en_ruta(1.0).lerp(destino, ease_in_out_quad(avance)))

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Rotulo y anillo sobre el objetivo mientras dura la cinematica."""
        if self._activo is None:
            return
        centro = self._activo.punto - offset
        # El anillo se cierra segun avanza la cinematica: 30 px -> 12 px.
        radio = int(30 - 18 * min(self._t / self.TOTAL, 1.0))
        pygame.draw.circle(surface, (255, 235, 120), (int(centro.x), int(centro.y)), radio, 2)
        texto = self._fuente.render(self._activo.rotulo, True, (255, 235, 120))
        surface.blit(texto, (int(centro.x - texto.get_width() / 2), int(centro.y - radio - 18)))

    @property
    def activa(self) -> bool:
        return self._activo is not None
