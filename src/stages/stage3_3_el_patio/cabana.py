"""
Module: cabana
System: stage (student assignment)
Academic Unit: Unidad V (color) + Unidad VI (easing y animacion).

El refugio del final del patio. Dos cosas a la vez:

  1) LAS LUCES. La cabana del TMX esta dibujada apagada —ventanas negras—
     porque encenderlas es cosa del juego, no del mapa. Cuando el jugador
     entra en su radio, los cristales y el farol de la puerta se encienden
     progresivamente con `ease_out_cubic`, y el suelo delante recibe un halo
     calido. Si el jugador se aleja, se apagan igual de suave.

  2) EL RETO "AGUANTA". Llegar no basta: al entrar arranca una cuenta atras
     de `SEGUNDOS` y hay que seguir ahi hasta que acabe, con el dron encima.
     La luz de la cabana ES la barra de progreso —al 50% del reto las
     ventanas estan al 50%—, asi que el jugador ve cuanto le falta sin leer
     ningun numero. Si se sale del radio, el reto se pausa y el nivel no se
     bloquea: `NextTrigger` sigue funcionando pase lo que pase, porque dejar
     la salida dependiendo de un script es la forma facil de que alguien se
     quede encerrado por un fallo.

Por que las luces no usan el sistema de iluminacion del motor
==============================================================
`src/engine/render/lighting.py` ilumina la ESCENA entera con focos que se
componen en un mapa de luz global. Aqui hace falta lo contrario: pintar unos
cristales concretos encima de unos tiles concretos, sin tocar la iluminacion
del resto del patio. Un foco del motor habria aclarado tambien la meseta, el
dron y la mitad del cielo.
"""
from __future__ import annotations

import math

import pygame

from src.engine.utils.math_utils import ease_out_cubic, vec2_distance

SEGUNDOS = 18.0       # lo que dura el reto
RADIO = 190.0         # a que distancia arranca y se mantiene
ENCENDIDO = 1.6       # s que tarda la luz en subir o bajar del todo

# Posiciones RELATIVAS a la esquina superior izquierda de la cabana (64x64).
VENTANAS = ((14, 30, 12, 12), (38, 30, 12, 12))
FAROL = (35, 52, 3, 4)

CRISTAL = (255, 206, 120)
HALO = (255, 190, 110)


class Cabana:
    """Luces graduales del refugio y cuenta atras del reto final."""

    def __init__(self, x: int, y: int) -> None:
        self.rect = pygame.Rect(x, y, 64, 64)
        self._luz = 0.0            # 0 apagada, 1 encendida del todo
        self._restante = SEGUNDOS
        self.superado = False
        self._dentro = False
        self._t = 0.0
        self._fuente = pygame.font.Font(None, 26)
        self._pequena = pygame.font.Font(None, 18)

    # -- ciclo de vida ------------------------------------------
    def update(self, dt: float, jugador) -> None:
        self._t += dt
        if jugador is None:
            return
        centro = pygame.Vector2(self.rect.centerx, self.rect.centery)
        self._dentro = vec2_distance(centro, pygame.Vector2(jugador.position)) <= RADIO

        if self._dentro and not self.superado:
            self._restante = max(0.0, self._restante - dt)
            if self._restante <= 0.0:
                self.superado = True

        # La luz persigue a su objetivo en vez de saltar: encender de golpe al
        # cruzar el radio se lee como un fallo de dibujado, no como una luz.
        if self.superado:
            objetivo = 1.0
        elif self._dentro:
            # Mientras dura el reto, la luz ES el progreso.
            objetivo = 1.0 - (self._restante / SEGUNDOS)
        else:
            objetivo = 0.0
        paso = dt / ENCENDIDO
        if self._luz < objetivo:
            self._luz = min(objetivo, self._luz + paso)
        else:
            self._luz = max(objetivo, self._luz - paso)

    # -- dibujo -------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if self._luz <= 0.01:
            return
        sx = int(self.rect.x - offset.x)
        sy = int(self.rect.y - offset.y)
        if sx > surface.get_width() or sx + 64 < 0:
            return

        # Unidad VI: la intensidad no sube lineal — arranca rapido y frena,
        # que es como se comporta una bombilla incandescente al encenderse.
        k = ease_out_cubic(self._luz)
        # Un parpadeo muy leve para que la luz no parezca una calcomania.
        k *= 0.94 + 0.06 * math.sin(self._t * 7.0)

        capa = pygame.Surface((64, 64), pygame.SRCALPHA)
        for vx, vy, vw, vh in VENTANAS:
            pygame.draw.rect(capa, (*CRISTAL, int(235 * k)), (vx, vy, vw, vh))
            pygame.draw.line(capa, (*CRISTAL, int(120 * k)),
                             (vx + vw // 2, vy), (vx + vw // 2, vy + vh))
        pygame.draw.rect(capa, (*CRISTAL, int(255 * k)), FAROL)
        surface.blit(capa, (sx, sy), special_flags=pygame.BLEND_RGBA_ADD)

        # Halo sobre el suelo delante de la puerta. Unidad V: el alfa cae con
        # el radio, asi que el borde no se corta en seco.
        radio = int(52 * k)
        if radio > 2:
            halo = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
            for r in range(radio, 0, -3):
                a = int(46 * k * (1 - r / radio))
                pygame.draw.circle(halo, (*HALO, a), (radio, radio), r)
            surface.blit(halo, (sx + 32 - radio, sy + 62 - radio),
                         special_flags=pygame.BLEND_RGBA_ADD)

    def draw_hud(self, surface: pygame.Surface) -> None:
        """Cuenta atras centrada arriba, como el resto de avisos del motor."""
        if self.superado:
            if self._luz > 0.99 and self._dentro:
                t = self._pequena.render("REFUGIO ABIERTO", True, (180, 240, 190))
                surface.blit(t, (surface.get_width() // 2 - t.get_width() // 2, 74))
            return
        if not self._dentro:
            return
        texto = self._fuente.render("AGUANTA %d" % math.ceil(self._restante),
                                    True, (255, 226, 150))
        surface.blit(texto, (surface.get_width() // 2 - texto.get_width() // 2, 70))
