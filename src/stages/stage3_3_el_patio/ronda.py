"""
Module: ronda
System: stage (student assignment)
Academic Unit: Unidad II (vectores) + V (color) + VI (animacion con easing).

La ronda del vigilante: el tramo de sigilo que hay antes del refugio.

Un foco barre de un lado a otro el ultimo tramo de la meseta. Quedarse a la
vista cuesta salud; la unica forma de pasar es meterse en uno de los arbustos
y esperar a que el haz se aleje. Mientras el jugador esta escondido, la
pantalla le dice cuantos segundos faltan para poder salir, que es lo que
convierte la espera en una decision y no en una pausa a ciegas.

Por que el foco no es un enemigo del motor
===========================================
Se planteo como un `Shooter` con un cono, pero un enemigo del registro trae
vida, estados de dano, muerte y una IA que lo acerca al jugador
(`SquadBrain` le asigna tactica). Aqui hace falta lo contrario: algo que NO se
puede matar, que NO persigue y que solo importa por donde mira. Un enemigo
seria mas codigo y ademas mentiria al jugador, que intentaria dispararle.

Por que el barrido usa una funcion suavizada y no un vaiven lineal
===================================================================
Con interpolacion lineal el foco llega al extremo y cambia de sentido de
golpe, y eso se lee como un error de programacion. `ease_in_out_quad` sobre el
tramo de ida y otra vez sobre el de vuelta hace que frene al acercarse a cada
extremo y arranque despacio al volver, que es como gira una persona que
vigila.
"""
from __future__ import annotations

import math

import pygame

from src.engine.utils.math_utils import ease_in_out_quad

# Tramo que vigila el foco, en coordenadas de mundo.
X_INI, X_FIN = 2000.0, 2270.0
Y_SUELO = 336.0

PERIODO = 7.0          # s que tarda en ir y volver
RADIO_HAZ = 46.0       # medio ancho del haz a la altura del suelo
ALTURA_HAZ = 150.0     # de donde baja la luz
DANO = 0.25            # por segundo a la vista, como una HazardZone
CADENCIA_DANO = 1.0    # s entre golpes

# Arbustos: (x_centro, ancho). El jugador esta a salvo si su centro cae dentro.
ARBUSTOS = ((2050, 46), (2145, 46), (2240, 46))
ALTO_ARBUSTO = 26

LUZ = (255, 240, 190)
ALERTA = (255, 110, 90)
SEGURO = (150, 230, 160)
VERDE_OSC = (26, 54, 34)
VERDE_MED = (38, 78, 46)
VERDE_CLA = (54, 104, 60)


class Ronda:
    """Foco que barre, arbustos donde esconderse y aviso en pantalla."""

    def __init__(self) -> None:
        self._t = 0.0
        self._cd = 0.0
        self.escondido = False
        self.visto = False
        self.en_haz = False           # el foco cubre ahora mismo al jugador
        self._arbusto_activo = -1     # en cual esta metido el jugador
        self._fuente = pygame.font.Font(None, 26)
        self._pequena = pygame.font.Font(None, 18)
        self._arbustos = [
            pygame.Rect(int(cx - w / 2), int(Y_SUELO - ALTO_ARBUSTO), w, ALTO_ARBUSTO)
            for cx, w in ARBUSTOS
        ]

    # -- posicion del foco --------------------------------------
    def _avance(self) -> float:
        """0..1 ida, 1..0 vuelta, suavizado en los dos extremos."""
        fase = (self._t % PERIODO) / PERIODO
        if fase < 0.5:
            return ease_in_out_quad(fase * 2)
        return 1.0 - ease_in_out_quad((fase - 0.5) * 2)

    @property
    def foco_x(self) -> float:
        return X_INI + (X_FIN - X_INI) * self._avance()

    def _segundos_para_salir(self, x_jugador: float) -> float:
        """Cuanto falta para que el haz deje de cubrir ese punto.

        Se resuelve avanzando el reloj en pasos cortos en vez de despejar la
        ecuacion: el barrido esta suavizado con `ease_in_out_quad`, asi que
        invertirlo a mano seria mas codigo y mas fragil que mirar el futuro
        inmediato, que ademas es exacto.
        """
        paso = 0.1
        for i in range(1, int(PERIODO / paso) + 1):
            t = self._t + i * paso
            fase = (t % PERIODO) / PERIODO
            a = ease_in_out_quad(fase * 2) if fase < 0.5 else 1.0 - ease_in_out_quad((fase - 0.5) * 2)
            fx = X_INI + (X_FIN - X_INI) * a
            if abs(fx - x_jugador) > RADIO_HAZ:
                return i * paso
        return 0.0

    # -- ciclo de vida ------------------------------------------
    def update(self, dt: float, jugador) -> None:
        self._t += dt
        self._cd = max(0.0, self._cd - dt)
        self.escondido = False
        self.visto = False
        self.en_haz = False
        self._arbusto_activo = -1
        if jugador is None:
            return

        px, py = jugador.position.x, jugador.position.y
        if not (X_INI - 90 <= px <= X_FIN + 90):
            return      # fuera del tramo vigilado: la ronda no le afecta

        # Unidad II: dentro del haz es una distancia en el eje x contra el
        # radio del cono; el arbusto, una pertenencia a rectangulo.
        self._arbusto_activo = next(
            (i for i, a in enumerate(self._arbustos)
             if a.collidepoint(int(px), int(py - 8))), -1)
        self.escondido = self._arbusto_activo >= 0
        self.en_haz = abs(px - self.foco_x) <= RADIO_HAZ and py >= Y_SUELO - 90
        en_haz = self.en_haz

        if en_haz and not self.escondido:
            self.visto = True
            if self._cd <= 0.0:
                self._cd = CADENCIA_DANO
                jugador.apply_damage(DANO, (self.foco_x, Y_SUELO - ALTURA_HAZ), 60.0)

    # -- dibujo -------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        self._dibujar_arbustos(surface, offset)
        self._dibujar_haz(surface, offset)

    def _dibujar_arbustos(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        for i, a in enumerate(self._arbustos):
            sx = int(a.centerx - offset.x)
            sy = int(a.bottom - offset.y)
            if sx < -60 or sx > surface.get_width() + 60:
                continue
            # Cuando el jugador esta dentro, el arbusto tiembla un poco: es el
            # unico aviso de que el escondite esta funcionando.
            meneo = int(math.sin(self._t * 18) * 1.5) if i == self._arbusto_activo else 0
            for dx, dy, r, col in ((-13, -6, 11, VERDE_OSC), (12, -6, 11, VERDE_OSC),
                                   (0, -12, 14, VERDE_MED), (-7, -4, 10, VERDE_MED),
                                   (7, -4, 10, VERDE_MED), (-3, -15, 7, VERDE_CLA),
                                   (6, -13, 6, VERDE_CLA)):
                pygame.draw.circle(surface, col, (sx + dx + meneo, sy + dy), r)

    def _dibujar_haz(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        fx = self.foco_x - offset.x
        base_y = Y_SUELO - offset.y
        alto_y = base_y - ALTURA_HAZ
        if fx < -120 or fx > surface.get_width() + 120:
            return
        # Unidad V: el cono se pinta por franjas, con el alfa cayendo hacia
        # abajo; en aditivo, para que aclare lo que hay debajo en vez de
        # taparlo con una capa opaca.
        cono = pygame.Surface((int(RADIO_HAZ * 2 + 40), int(ALTURA_HAZ) + 8),
                              pygame.SRCALPHA)
        cx = cono.get_width() // 2
        pasos = 26
        for i in range(pasos):
            t = i / (pasos - 1)
            y = int(t * ALTURA_HAZ)
            medio = int(8 + (RADIO_HAZ - 8) * t)
            a = int(70 * (1 - t) + 18)
            pygame.draw.line(cono, (*LUZ, a), (cx - medio, y), (cx + medio, y))
        surface.blit(cono, (int(fx) - cx, int(alto_y)),
                     special_flags=pygame.BLEND_RGBA_ADD)
        # Charco de luz en el suelo: es la linea que marca donde acaba el
        # peligro, asi que se dibuja aparte del cono y bien definida.
        pygame.draw.ellipse(surface, LUZ,
                            (int(fx - RADIO_HAZ), int(base_y - 5),
                             int(RADIO_HAZ * 2), 10), 1)

    def draw_hud(self, surface: pygame.Surface, jugador) -> None:
        if jugador is None:
            return
        px = jugador.position.x
        if not (X_INI - 90 <= px <= X_FIN + 90):
            return
        cx = surface.get_width() // 2
        if self.visto:
            t = self._fuente.render("¡TE VEN!", True, ALERTA)
            surface.blit(t, (cx - t.get_width() // 2, 70))
            return
        if self.escondido:
            # La cuenta atras solo tiene sentido si el foco esta encima AHORA.
            # Antes se mostraba siempre, y como el haz casi nunca cubre el
            # arbusto salia un "SAL EN 0" permanente que no informaba de nada.
            if self.en_haz:
                faltan = self._segundos_para_salir(px)
                t = self._fuente.render("SAL EN %d" % max(1, math.ceil(faltan)),
                                        True, (255, 226, 150))
            else:
                t = self._fuente.render("¡AHORA!", True, SEGURO)
            surface.blit(t, (cx - t.get_width() // 2, 70))
            return
        aviso = self._pequena.render("LA RONDA VIGILA — ESCONDETE EN LOS ARBUSTOS",
                                     True, (220, 220, 190))
        surface.blit(aviso, (cx - aviso.get_width() // 2, 74))
