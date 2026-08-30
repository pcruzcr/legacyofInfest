# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
"""
Module: form2_attacks
System: src.stages.boss_paburu
Academic Unit: II (vectores), III (curvas), V (color), VI (interpolación)

FORMA 2 — LA MÁSCARA ESPECTRAL

Paburu deja la piedra y se pone la máscara. Ya no juzga sin mirar: juzga **con
la tradición**, y por eso esta forma es la única en la que los guardianes
bajan a pelear con él. No está solo, y ésa es toda la diferencia.

LOS TRES ATAQUES, Y QUÉ PREGUNTA CADA UNO
Igual que en la Forma 1, ninguno repite la pregunta de otro; si dos la
repitieran sobraría uno.

    SPIRIT_WAVE     · ¿sabés cuándo saltar?      — ola rasante por el suelo
    MASK_PULSE      · ¿sabés cuándo alejarte?    — onda radial desde la máscara
    DUELO_DE_ECOS   · ¿sabés parar?              — ecos que hay que devolver

Y las tres respuestas son distintas: saltar, retirarse, y parar. Un jugador
que solo sepa esquivar hacia los lados no pasa de aquí.

POR QUÉ EL SUELO Y EL AIRE SE REPARTEN
`SPIRIT_WAVE` va rasante y `MASK_PULSE` se abre en círculo desde la máscara,
que flota. La ola te obliga a estar en el aire y el pulso te obliga a estar
lejos: como el círculo mide 576 px y las plataformas están a 80 y 160 del
suelo, siempre hay un sitio seguro, pero nunca es el mismo dos veces seguidas.
Ésa es la lectura que se le pide al jugador.

EL DUELO DE ECOS ES EL CORAZÓN DE LA FORMA
El GDD dice que Paburu «juzga con la tradición»: no ataca, **repite**. Los
ecos son sus propios ataques anteriores devueltos contra el jugador, y la
única respuesta limpia es pararlos — el parry que ya devuelve piedras y rayos
en la Forma 1. Aguantarlos también funciona, pero cuesta vida.

Se apoya en `resolve_weak_point_damage` y en el parry que ya están montados:
esta forma no inventa sistemas, usa los que la Forma 1 dejó probados.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    pass

# ── Paleta espectral ───────────────────────────────────────────
# El verde del más allá que usa todo el juego para lo sobrenatural. Se
# mantiene: cambiar de color en la Forma 2 obligaría al jugador a reaprender
# qué le hace daño justo cuando el jefe se vuelve más rápido.
ESPECTRO = (0, 200, 100)
ESPECTRO_CLARO = (140, 255, 200)
ESPECTRO_OSC = (24, 92, 62)
AVISO = (255, 210, 90)          # el color del telegrafiado, en toda la pelea


def suave(t: float) -> float:
    """Smoothstep 3t²−2t³ (Unidad VI). Arranca y termina sin tirón."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


# ══════════════════════════════════════════════════════════════
#  SPIRIT_WAVE — la ola rasante
# ══════════════════════════════════════════════════════════════
class SpiritWave:
    """Una ola de ánimas que corre pegada al suelo. Se salta.

    Va A RAS y no a media altura a propósito: un ataque que ocupa la franja
    del salto no se esquiva, se adivina. Pegado al suelo, el jugador tiene una
    respuesta clara —saltar— y el error es suyo, no del diseño.

    La cresta sube y baja con un seno mientras avanza (Unidad III): además de
    verse viva, hace que el momento del salto no sea siempre el mismo, así que
    la respuesta se mide en vez de memorizarse.
    """

    #: Aviso antes de salir. `MIN_READABLE_WINDUP` del BossKit es 0.35; se le
    #: da 0.45 porque la ola nace en el jefe y el jugador puede estar al otro
    #: lado del círculo, a 500 px, y necesita ver de dónde viene.
    TELEGRAFIADO = 0.45

    VELOCIDAD = 190.0           # px/s
    ALTO = 26                   # alto de la cresta, en px
    LARGO = 34                  # grosor del frente
    DANIO = 1.0
    ALCANCE = 620.0             # se apaga sola: no cruza el mapa entero

    def __init__(self, origen: pygame.Vector2, direccion: int,
                 suelo_y: float) -> None:
        self.origen = pygame.Vector2(origen)
        self.direccion = 1 if direccion >= 0 else -1
        self.suelo_y = float(suelo_y)
        self.x = float(origen.x)
        self._t = 0.0
        self._recorrido = 0.0
        self.alive = True
        #: Como los ataques de la Forma 1: una ola parada puede devolverse.
        self.devuelta = False

    @property
    def is_telegraphing(self) -> bool:
        return self._t < self.TELEGRAFIADO

    def devolver(self, hacia: pygame.Vector2) -> None:
        """El parry la manda de vuelta. Cambia de dueño y de sentido."""
        if self.devuelta:
            return
        self.devuelta = True
        self.direccion = 1 if hacia.x >= self.x else -1
        self._recorrido = 0.0

    def update(self, dt: float) -> None:
        self._t += dt
        if self.is_telegraphing:
            return
        paso = self.VELOCIDAD * dt
        self.x += paso * self.direccion
        self._recorrido += paso
        if self._recorrido > self.ALCANCE:
            self.alive = False

    @property
    def rect(self) -> pygame.Rect | None:
        if self.is_telegraphing or not self.alive:
            return None
        return pygame.Rect(
            int(self.x - self.LARGO / 2),
            int(self.suelo_y - self.ALTO),
            self.LARGO, self.ALTO,
        )

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        ox, oy = int(offset.x), int(offset.y)
        if self.is_telegraphing:
            # El aviso: una línea que se enciende a lo largo del suelo hacia
            # donde va a salir la ola. Dice DÓNDE y HACIA DÓNDE, que es lo que
            # el jugador necesita para decidir si salta o se aparta.
            k = suave(self._t / self.TELEGRAFIADO)
            largo = int(180 * k)
            y = int(self.suelo_y - 2) - oy
            x0 = int(self.x) - ox
            pygame.draw.line(surface, AVISO, (x0, y),
                             (x0 + largo * self.direccion, y), 2)
            return

        # La ola: tres crestas de seno desfasadas. Con una sola se lee como un
        # rectángulo que se desliza; con tres, como agua.
        base_x = int(self.x) - ox
        base_y = int(self.suelo_y) - oy
        for _capa, (color, amp, fase) in enumerate((
                (ESPECTRO_OSC, 1.0, 0.0),
                (ESPECTRO, 0.78, 1.1),
                (ESPECTRO_CLARO, 0.5, 2.2))):
            puntos = []
            for i in range(9):
                u = i / 8.0
                dx = int((u - 0.5) * self.LARGO)
                onda = math.sin(u * math.pi) * math.sin(self._t * 9.0 + fase)
                alto = self.ALTO * amp * (0.65 + 0.35 * onda)
                puntos.append((base_x + dx, base_y - int(alto)))
            puntos.append((base_x + self.LARGO // 2, base_y))
            puntos.append((base_x - self.LARGO // 2, base_y))
            pygame.draw.polygon(surface, color, puntos)


# ══════════════════════════════════════════════════════════════
#  MASK_PULSE — la onda radial
# ══════════════════════════════════════════════════════════════
class MaskPulse:
    """Un anillo que se abre desde la máscara. Se sale de él, no se salta.

    Es el castigo por quedarse pegado al jefe, que es exactamente lo que
    invita a hacer el punto débil de la máscara (x2.5 de daño). Sin este
    ataque, la Forma 2 se resolvería quedándose debajo y pegando: el punto
    débil sería un regalo en vez de una decisión.

    Sólo daña el BORDE del anillo, no el interior. Así el jugador que ya está
    pegado al jefe puede quedarse quieto y dejarlo pasar, y el que está a
    media distancia es el que tiene que correr. Un anillo macizo castigaría
    justo al que se acercó, que es lo que se quiere premiar.
    """

    TELEGRAFIADO = 0.55         # más largo: hay que darle tiempo a alejarse
    RADIO_MAX = 190.0
    GROSOR = 14
    DURACION = 0.85             # lo que tarda en llegar al radio máximo
    DANIO = 1.0

    def __init__(self, centro: pygame.Vector2) -> None:
        self.centro = pygame.Vector2(centro)
        self._t = 0.0
        self.alive = True

    @property
    def is_telegraphing(self) -> bool:
        return self._t < self.TELEGRAFIADO

    @property
    def radio(self) -> float:
        if self.is_telegraphing:
            return 0.0
        u = (self._t - self.TELEGRAFIADO) / self.DURACION
        # Arranca rápido y frena: así el jugador cercano tiene el instante
        # justo para reaccionar y el lejano lo ve venir.
        return self.RADIO_MAX * suave(min(1.0, u))

    def update(self, dt: float) -> None:
        self._t += dt
        if self._t > self.TELEGRAFIADO + self.DURACION:
            self.alive = False

    def toca(self, caja: pygame.Rect) -> bool:
        """¿El borde del anillo cruza esta caja?

        Se compara la distancia del centro al punto más cercano de la caja
        contra el radio, con la tolerancia del grosor. Es la prueba
        círculo-rectángulo de la Unidad II, y es lo correcto aquí: usar el
        `rect` del anillo daría un cuadrado y el jugador vería un círculo.
        """
        if self.is_telegraphing or not self.alive:
            return False
        cx = max(caja.left, min(self.centro.x, caja.right))
        cy = max(caja.top, min(self.centro.y, caja.bottom))
        d = pygame.Vector2(cx - self.centro.x, cy - self.centro.y).length()
        return abs(d - self.radio) <= self.GROSOR * 0.5 + 2.0

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        c = (int(self.centro.x - offset.x), int(self.centro.y - offset.y))
        if self.is_telegraphing:
            # Un anillo de aviso del tamaño final, punteado por sectores: se
            # ve exactamente hasta dónde va a llegar antes de que llegue.
            k = suave(self._t / self.TELEGRAFIADO)
            r = int(self.RADIO_MAX)
            pasos = 20
            for i in range(pasos):
                if (i + int(k * 8)) % 2:
                    continue
                a0 = i / pasos * math.tau
                a1 = (i + 0.7) / pasos * math.tau
                pygame.draw.arc(
                    surface, AVISO,
                    pygame.Rect(c[0] - r, c[1] - r, r * 2, r * 2),
                    a0, a1, 2)
            return

        r = int(self.radio)
        if r <= 1:
            return
        # Tres anillos concéntricos que se apagan hacia fuera: el borde se lee
        # como una onda y no como un aro de alambre.
        for _k, (color, dr, w) in enumerate((
                (ESPECTRO_OSC, 4, self.GROSOR),
                (ESPECTRO, 0, max(2, self.GROSOR - 5)),
                (ESPECTRO_CLARO, -3, 2))):
            rr = max(1, r + dr)
            pygame.draw.circle(surface, color, c, rr, w)


# ══════════════════════════════════════════════════════════════
#  DUELO_DE_ECOS — los ecos que se paran
# ══════════════════════════════════════════════════════════════
class Eco:
    """Un eco del propio Paburu. Viaja despacio y **se para**.

    Es el ataque que da nombre a la forma y el que enseña el parry. Va lento a
    propósito —110 px/s contra los 190 de la ola— porque parar tiene una
    ventana de 0,2 s y pedirla contra un proyectil rápido sería pedir
    memorizar, no reaccionar.

    Y se lanzan de a tres, escalonados. Con uno solo, fallar la parada no
    tiene consecuencia y acertarla tampoco tiene mérito; con tres seguidos el
    jugador puede parar el primero, comerse el segundo y volver a parar el
    tercero, que es una conversación y no un examen.
    """

    TELEGRAFIADO = 0.4
    VELOCIDAD = 110.0
    RADIO = 9
    DANIO = 0.75
    #: Un eco devuelto pega MÁS que el original: parar tiene que rendir más
    #: que esquivar, o nadie para.
    DANIO_DEVUELTO = 1.5
    VIDA = 4.0

    def __init__(self, origen: pygame.Vector2, destino: pygame.Vector2,
                 retraso: float = 0.0) -> None:
        self.pos = pygame.Vector2(origen)
        delta = pygame.Vector2(destino) - self.pos
        self.dir = delta.normalize() if delta.length_squared() > 1e-6 \
            else pygame.Vector2(1, 0)
        self._t = -retraso           # el escalonado: negativo = todavía no sale
        self.alive = True
        self.devuelta = False

    @property
    def is_telegraphing(self) -> bool:
        return self._t < self.TELEGRAFIADO

    def devolver(self, hacia: pygame.Vector2) -> None:
        if self.devuelta:
            return
        self.devuelta = True
        delta = pygame.Vector2(hacia) - self.pos
        if delta.length_squared() > 1e-6:
            self.dir = delta.normalize()

    def update(self, dt: float) -> None:
        self._t += dt
        if self._t < 0.0 or self.is_telegraphing:
            return
        # Devuelto va más rápido: se siente como un golpe, no como una
        # devolución de cortesía.
        v = self.VELOCIDAD * (1.9 if self.devuelta else 1.0)
        self.pos += self.dir * v * dt
        if self._t > self.VIDA:
            self.alive = False

    @property
    def rect(self) -> pygame.Rect | None:
        if self._t < 0.0 or self.is_telegraphing or not self.alive:
            return None
        r = self.RADIO
        return pygame.Rect(int(self.pos.x - r), int(self.pos.y - r), r * 2, r * 2)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive or self._t < 0.0:
            return
        c = (int(self.pos.x - offset.x), int(self.pos.y - offset.y))
        if self.is_telegraphing:
            k = suave(self._t / self.TELEGRAFIADO)
            pygame.draw.circle(surface, AVISO, c, int(self.RADIO * (0.4 + k)), 1)
            return
        color = ESPECTRO_CLARO if self.devuelta else ESPECTRO
        pygame.draw.circle(surface, ESPECTRO_OSC, c, self.RADIO + 2)
        pygame.draw.circle(surface, color, c, self.RADIO)
        pygame.draw.circle(surface, ESPECTRO_CLARO, c, max(1, self.RADIO - 4))
