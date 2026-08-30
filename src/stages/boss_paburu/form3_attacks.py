# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
"""
Module: form3_attacks
System: stages.boss_paburu
Academic Unit: II (vectores, distancia), VI (interpolación, movimiento
               paramétrico y circular)
Description: Forma 3 — LA RELIQUIA. Los motores 3A/3B y sus proyectiles
             (DISENO_NIVEL_Y_JEFE.md §3.5, GDD §4 Forma 3).

LA FORMA 3 ES DISTINTA A LAS OTRAS DOS
En la Piedra y en la Máscara el jefe se queda en su sitio y LANZA cosas. En
la Reliquia el peligro es EL CUERPO: 32×32 px de reliquia que persigue (3A)
u orbita (3B), y tocarla es el daño. Por eso esta forma no vive en clases de
proyectil sueltas sino en dos MOTORES —máquinas de estado que gobiernan el
movimiento del jefe— y dos proyectiles de apoyo que existen sobre todo para
que el parry siga teniendo qué decir.

EL SORTEO 3A/3B
`relic_variant` se sortea al entrar en la forma ("gold" o "black") y cada
partida ve UNA de las dos peleas. La rejugabilidad es el argumento del
sorteo entero del nivel: quien lo juega dos veces no repite ni el círculo
de la trampa ni la pelea del medio.

LA REGLA DE VULNERABILIDAD (compartida por las dos variantes)
Una reliquia en movimiento es un borrón: golpearla da daño de roce (×0.25).
Cada variante tiene su VENTANA —la Pepita se agota tras la triple embestida,
la Perla se abre cuando su órbita se detiene— y ahí el daño entra completo.
La forma entera es una pregunta de lectura: ¿sabés cuándo pegar?

Mismo contrato visual que form2: `AVISO` para telegrafiar, colores propios
por variante (oro vs nácar oscuro) para que la variante se reconozca en un
fotograma.
"""
from __future__ import annotations

import math

import pygame

# ── Paletas ────────────────────────────────────────────────────
ORO = (232, 177, 44)
ORO_CLARO = (255, 226, 130)
ORO_OSC = (140, 96, 18)
PERLA = (120, 92, 176)
PERLA_CLARA = (196, 172, 236)
PERLA_OSC = (56, 38, 92)
AVISO = (255, 210, 90)


def suave(t: float) -> float:
    """Smoothstep 3t² − 2t³ (Unidad VI)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


# ══════════════════════════════════════════════════════════════
#  Proyectiles de apoyo
# ══════════════════════════════════════════════════════════════

class EsquirlaDeOro:
    """Fragmento que la Pepita suelta en abanico. Cae con gravedad.

    Existe para que 3A no sea SOLO esquivar el cuerpo: las esquirlas se
    PARAN, y devueltas pegan el triple de lo que traían. En un combate cuyo
    peligro principal no es parable (la embestida es un cuerpo), este es el
    hueco por donde el parry sigue entrando.
    """

    RADIO = 6
    DANIO = 0.5
    DANIO_DEVUELTA = 1.5
    GRAVEDAD = 420.0
    VIDA = 3.5

    def __init__(self, origen: pygame.Vector2, vel: pygame.Vector2) -> None:
        self.pos = pygame.Vector2(origen)
        self.vel = pygame.Vector2(vel)
        self._t = 0.0
        self.alive = True
        self.devuelta = False
        self._objetivo: pygame.Vector2 | None = None

    @property
    def is_telegraphing(self) -> bool:
        return False        # nace ya en vuelo: el aviso fue el gesto de la Pepita

    def devolver(self, hacia: pygame.Vector2) -> None:
        if self.devuelta:
            return
        self.devuelta = True
        self._objetivo = pygame.Vector2(hacia)

    def update(self, dt: float) -> None:
        self._t += dt
        if self.devuelta and self._objetivo is not None:
            d = self._objetivo - self.pos
            if d.length() > 1:
                self.pos += d.normalize() * 300.0 * dt
        else:
            self.vel.y += self.GRAVEDAD * dt
            self.pos += self.vel * dt
        if self._t > self.VIDA:
            self.alive = False

    @property
    def rect(self) -> pygame.Rect | None:
        if not self.alive:
            return None
        r = self.RADIO
        return pygame.Rect(int(self.pos.x - r), int(self.pos.y - r), r * 2, r * 2)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        sx, sy = int(self.pos.x - offset.x), int(self.pos.y - offset.y)
        color = ORO_CLARO if self.devuelta else ORO
        # Rombo, no círculo: una esquirla es un fragmento con aristas.
        pygame.draw.polygon(surface, ORO_OSC, (
            (sx, sy - 7), (sx + 5, sy), (sx, sy + 7), (sx - 5, sy)))
        pygame.draw.polygon(surface, color, (
            (sx, sy - 4), (sx + 3, sy), (sx, sy + 4), (sx - 3, sy)))


class LagrimaNegra:
    """La Perla llora una gota lenta que busca al jugador.

    Es EL golpe de estado de 3B: devuelta con parry no solo daña — ABRE a la
    Perla (detiene su órbita) fuera de turno. La ventana de vulnerabilidad
    normalmente hay que esperarla; con un buen parry, se fabrica.
    """

    TELEGRAFIADO = 0.5
    VELOCIDAD = 105.0
    RADIO = 9
    DANIO = 1.0
    DANIO_DEVUELTA = 1.5
    VIDA = 7.0
    AMPLITUD = 16.0
    FRECUENCIA = 2.8

    def __init__(self, origen: pygame.Vector2, objetivo: pygame.Vector2) -> None:
        self.pos = pygame.Vector2(origen)
        d = pygame.Vector2(objetivo) - self.pos
        self.rumbo = d.normalize() if d.length() > 1 else pygame.Vector2(0, 1)
        self._t = -self.TELEGRAFIADO
        self._fase = 0.0
        self.alive = True
        self.devuelta = False
        self._objetivo: pygame.Vector2 | None = None

    @property
    def is_telegraphing(self) -> bool:
        return self._t < 0.0

    def devolver(self, hacia: pygame.Vector2) -> None:
        if self.devuelta:
            return
        self.devuelta = True
        self._objetivo = pygame.Vector2(hacia)

    def retarget(self, hacia: pygame.Vector2) -> None:
        self._objetivo = pygame.Vector2(hacia)

    def update(self, dt: float) -> None:
        self._t += dt
        if self.is_telegraphing:
            return
        # AUD-494 — LA GOTA DEVUELTA VIVÍA PARA SIEMPRE.
        #
        # El chequeo de `VIDA` estaba al final, después del `return` de la
        # rama `devuelta`: una gota parada nunca lo alcanzaba. Si su objetivo
        # ya no estaba (la Perla se movió, la fase cambió, `d.length() <= 1`)
        # se quedaba flotando y dibujándose indefinidamente — medida viva a
        # los 120 s con `VIDA` = 7. Un proyectil inmortal no es sólo basura
        # en pantalla: sigue teniendo `rect` y sigue pudiendo golpear.
        #
        # El límite de vida es del PROYECTIL, no de una de sus trayectorias,
        # así que va antes de bifurcar.
        if self._t > self.VIDA:
            self.alive = False
            return
        if self.devuelta and self._objetivo is not None:
            d = self._objetivo - self.pos
            if d.length() > 1:
                self.pos += d.normalize() * 260.0 * dt
            return
        self._fase += dt * self.FRECUENCIA
        perpendicular = pygame.Vector2(-self.rumbo.y, self.rumbo.x)
        self.pos += (self.rumbo * self.VELOCIDAD
                     + perpendicular * math.sin(self._fase) * self.AMPLITUD) * dt

    @property
    def rect(self) -> pygame.Rect | None:
        if self.is_telegraphing or not self.alive:
            return None
        r = self.RADIO
        return pygame.Rect(int(self.pos.x - r), int(self.pos.y - r), r * 2, r * 2)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        sx, sy = int(self.pos.x - offset.x), int(self.pos.y - offset.y)
        if self.is_telegraphing:
            p = suave(1.0 + self._t / self.TELEGRAFIADO)
            pygame.draw.circle(surface, AVISO, (sx, sy),
                               int(self.RADIO + 5 * (1 - p)), 1)
            return
        color = PERLA_CLARA if self.devuelta else PERLA
        # Forma de gota: círculo con punta hacia atrás del rumbo.
        pygame.draw.circle(surface, PERLA_OSC, (sx, sy), self.RADIO + 2)
        pygame.draw.circle(surface, color, (sx, sy), self.RADIO)
        cola = self.pos - self.rumbo * (self.RADIO + 6)
        pygame.draw.polygon(surface, PERLA_OSC, (
            (sx - 4, sy), (sx + 4, sy),
            (int(cola.x - offset.x), int(cola.y - offset.y))))


# ══════════════════════════════════════════════════════════════
#  3A — LA PEPITA (gold): persecución
# ══════════════════════════════════════════════════════════════

class MotorPepita:
    """La Pepita acecha, apunta, y embiste tres veces. Después se agota.

    La lección de 3A: MOVERSE SIN DEJAR DE MIRAR. La embestida fija su rumbo
    AL EMPEZAR a apuntar —no persigue en vuelo—, así que un paso lateral
    durante el apuntado la vuelve inofensiva… y deja al jugador de frente a
    la siguiente. Tras la tercera, la ventana: 1.7 s de reliquia agotada en
    el suelo, que es cuando pegar de verdad.

    AUD-486 — LA LÍNEA DE MIRA APUNTABA AL REVÉS.
    ---------------------------------------------
    El rumbo se fijaba al FINAL del apuntado, pero `draw` pinta la línea de
    mira DURANTE el apuntado leyendo `self._rumbo`: en esos 0,5 s el valor
    todavía era el de la embestida ANTERIOR. Medido sobre una pelea entera:
    error angular de mediana 129°, máximo 172,8° — o sea que la mitad de las
    veces la reliquia avisaba de ir justo por donde no fue. La primera
    embestida de cada serie era aún peor: `_rumbo` valía su valor inicial
    (1,0), un aviso hacia la derecha viniera de donde viniera. El jugador que
    hacía exactamente lo que el juego le enseña —leer el telegrafiado y
    apartarse— se metía él solo en la trayectoria.

    Fijarlo al ENTRAR en APUNTA hace que la línea diga la verdad, y de paso
    aprieta la lección: el paso lateral hay que darlo durante el apuntado,
    con la marca ya puesta, que es cuando se puede leer.
    """

    ACECHO, APUNTA, EMBISTE, PAUSA, AGOTADA = range(5)

    VEL_ACECHO = 95.0
    VEL_EMBISTE = 430.0
    APUNTADO = 0.5
    PAUSA_ENTRE = 0.22
    VENTANA = 1.7
    EMBESTIDAS = 3
    ALTURA_ACECHO = 120.0       # sobre el suelo, fuera del alcance del sable

    def __init__(self, arena: pygame.Rect, suelo_y: float) -> None:
        self.arena = arena
        self.suelo_y = suelo_y
        self.estado = self.ACECHO
        self._t = 0.0
        self._restantes = 0
        self._rumbo = pygame.Vector2(1, 0)
        self._objetivo = pygame.Vector2()
        #: AUD-486 — «este apuntado ya eligió a dónde va». Hace falta una
        #: bandera y no basta con `self._t == 0` porque `ordenar_embestida`
        #: no recibe al jugador: quien puede leer su posición es `update`, y
        #: el rumbo se fija en su PRIMER fotograma dentro de APUNTA.
        self._apuntado_fijado = False
        self._estela: list[tuple[float, float, float]] = []   # (x, y, edad)

    # ── Órdenes del planificador ───────────────────────────────
    def ordenar_embestida(self) -> bool:
        """El planificador pide la triple embestida. Solo desde el acecho."""
        if self.estado != self.ACECHO:
            return False
        self.estado = self.APUNTA
        self._t = 0.0
        self._restantes = self.EMBESTIDAS
        self._apuntado_fijado = False       # AUD-486
        return True

    def _fijar_rumbo(self, desde: pygame.Vector2,
                     jugador: pygame.Rect) -> None:
        """Elige a dónde va esta embestida. AUD-486: al EMPEZAR a apuntar.

        Se pasa 60 px del objetivo: una embestida que frena SOBRE el jugador
        no se esquiva, se sufre.
        """
        self._objetivo = pygame.Vector2(jugador.center)
        d = self._objetivo - desde
        self._rumbo = (d.normalize() if d.length() > 1
                       else pygame.Vector2(1, 0))
        self._objetivo += self._rumbo * 60.0
        self._apuntado_fijado = True

    # ── Estado que el jefe consulta ────────────────────────────
    @property
    def ventana_abierta(self) -> bool:
        return self.estado == self.AGOTADA

    @property
    def peligrosa(self) -> bool:
        """¿El cuerpo daña ahora? Solo en plena embestida: una reliquia
        acechando a 120 px del suelo no puede ser un golpe sorpresa."""
        return self.estado == self.EMBISTE

    # ── El ciclo ───────────────────────────────────────────────
    def update(self, boss, jugador: pygame.Rect | None, dt: float) -> None:
        self._t += dt
        self._estela = [(x, y, e + dt) for x, y, e in self._estela if e < 0.35]
        pos = pygame.Vector2(boss.rect.center)

        if jugador is None:
            return

        if self.estado == self.ACECHO:
            # Flota hacia un punto sobre el jugador, sin tirarse encima:
            # mantiene ~110 px de distancia horizontal, del lado en que ya
            # estaba (cruzar por encima gratis sería un dash sin telegraph).
            lado = 1.0 if pos.x >= jugador.centerx else -1.0
            meta = pygame.Vector2(
                jugador.centerx + lado * 110.0,
                self.suelo_y - self.ALTURA_ACECHO
                + math.sin(self._t * 2.1) * 14.0,
            )
            d = meta - pos
            if d.length() > 2:
                pos += d.normalize() * min(self.VEL_ACECHO * dt, d.length())

        elif self.estado == self.APUNTA:
            # AUD-486 — el rumbo se elige AQUÍ, en el primer fotograma del
            # apuntado, para que la línea de mira que `draw` pinta durante
            # estos 0,5 s sea la de ESTA embestida y no la de la anterior.
            if not self._apuntado_fijado:
                self._fijar_rumbo(pos, jugador)
            # Y vibra en el sitio: el aviso de que ya está cargada.
            pos.x += math.sin(self._t * 60.0) * 1.5
            if self._t >= self.APUNTADO:
                self.estado = self.EMBISTE
                self._t = 0.0

        elif self.estado == self.EMBISTE:
            paso = self.VEL_EMBISTE * dt
            self._estela.append((pos.x, pos.y, 0.0))
            pos += self._rumbo * paso
            llegada = (self._objetivo - pos).dot(self._rumbo) <= 0.0
            fuera = not self.arena.inflate(-24, -8).collidepoint(pos.x, pos.y)
            if llegada or fuera or self._t > 1.4:
                self._restantes -= 1
                self._t = 0.0
                self.estado = (self.PAUSA if self._restantes > 0
                               else self.AGOTADA)

        elif self.estado == self.PAUSA:
            if self._t >= self.PAUSA_ENTRE:
                self.estado = self.APUNTA
                self._t = 0.0
                self._apuntado_fijado = False       # AUD-486

        elif self.estado == self.AGOTADA:
            # Cae al suelo y se queda: LA ventana.
            caida = self.suelo_y - 16.0 - pos.y
            if caida > 1:
                pos.y += min(260.0 * dt, caida)
            if self._t >= self.VENTANA:
                self.estado = self.ACECHO
                self._t = 0.0

        # Nunca fuera de la arena: la reliquia pelea en la Sala, no en la roca.
        pos.x = max(self.arena.left + 20, min(self.arena.right - 20, pos.x))
        pos.y = max(self.arena.top + 20, min(self.suelo_y - 14, pos.y))
        boss.rect.center = (int(pos.x), int(pos.y))
        boss.position.update(float(boss.rect.x), float(boss.rect.y))

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2,
             boss_rect: pygame.Rect) -> None:
        # La estela de la embestida: el recorrido queda pintado un instante.
        for x, y, edad in self._estela:
            a = 1.0 - edad / 0.35
            r = max(2, int(8 * a))
            pygame.draw.circle(
                surface, ORO_OSC,
                (int(x - offset.x), int(y - offset.y)), r, 1)
        if self.estado == self.APUNTA:
            # La línea de mira parpadea del cuerpo hacia el jugador.
            p = suave(self._t / self.APUNTADO)
            cx = boss_rect.centerx - offset.x
            cy = boss_rect.centery - offset.y
            largo = 40 + 50 * p
            fin = pygame.Vector2(cx, cy) + self._rumbo * largo if \
                self._rumbo.length() else pygame.Vector2(cx + largo, cy)
            pygame.draw.line(surface, AVISO, (cx, cy),
                             (int(fin.x), int(fin.y)), 2)
        elif self.estado == self.AGOTADA:
            # El brillo de "pégame ahora": anillo dorado pulsante.
            p = 0.5 + 0.5 * math.sin(self._t * 9.0)
            pygame.draw.circle(
                surface, ORO_CLARO,
                (boss_rect.centerx - offset.x, boss_rect.centery - offset.y),
                int(24 + 4 * p), 2)


# ══════════════════════════════════════════════════════════════
#  3B — LA PERLA (black): órbita
# ══════════════════════════════════════════════════════════════

class MotorPerla:
    """La Perla orbita un centro que deriva hacia el jugador.

    La lección de 3B: LEER EL RITMO, entrar y salir. El peligro es el anillo
    —el cuerpo que pasa—, no el centro: pararse dentro de la órbita es más
    seguro que huir de ella, y darse cuenta de eso ES el combate. Cuando la
    órbita se cierra y se acelera, tocaba salir; cuando se detiene, la Perla
    queda ABIERTA: la ventana.
    """

    NORMAL, CERRANDO, FURIA, ABRIENDO, ABIERTA = range(5)

    RADIO_BASE = 112.0
    RADIO_CERRADO = 54.0
    OMEGA_BASE = 2.3            # rad/s
    OMEGA_FURIA = 5.2
    VEL_CENTRO = 52.0
    CIERRE = 1.1
    FURIA_DUR = 1.6
    APERTURA = 0.7
    VENTANA = 1.9

    def __init__(self, arena: pygame.Rect, suelo_y: float,
                 centro: pygame.Vector2) -> None:
        self.arena = arena
        self.suelo_y = suelo_y
        self.centro = pygame.Vector2(centro)
        self.estado = self.NORMAL
        self._t = 0.0
        self._ang = 0.0
        self._radio = self.RADIO_BASE

    # ── Órdenes ────────────────────────────────────────────────
    def ordenar_cierre(self) -> bool:
        if self.estado != self.NORMAL:
            return False
        self.estado = self.CERRANDO
        self._t = 0.0
        return True

    def abrir(self) -> None:
        """Un parry certero (la lágrima devuelta) fuerza la ventana."""
        if self.estado != self.ABIERTA:
            self.estado = self.ABIERTA
            self._t = 0.0

    # ── Estado consultable ─────────────────────────────────────
    @property
    def ventana_abierta(self) -> bool:
        return self.estado == self.ABIERTA

    @property
    def peligrosa(self) -> bool:
        return self.estado in (self.NORMAL, self.CERRANDO, self.FURIA)

    # ── El ciclo ───────────────────────────────────────────────
    def update(self, boss, jugador: pygame.Rect | None, dt: float) -> None:
        self._t += dt

        if jugador is not None and self.estado != self.ABIERTA:
            # El centro deriva hacia el jugador, despacio: la amenaza camina.
            meta = pygame.Vector2(jugador.centerx,
                                  min(jugador.centery,
                                      self.suelo_y - self.RADIO_BASE * 0.8))
            d = meta - self.centro
            if d.length() > 2:
                self.centro += d.normalize() * min(self.VEL_CENTRO * dt,
                                                   d.length())

        omega = self.OMEGA_BASE
        if self.estado == self.CERRANDO:
            p = suave(self._t / self.CIERRE)
            self._radio = self.RADIO_BASE + (self.RADIO_CERRADO
                                             - self.RADIO_BASE) * p
            if self._t >= self.CIERRE:
                self.estado = self.FURIA
                self._t = 0.0
        elif self.estado == self.FURIA:
            omega = self.OMEGA_FURIA
            self._radio = self.RADIO_CERRADO
            if self._t >= self.FURIA_DUR:
                self.estado = self.ABRIENDO
                self._t = 0.0
        elif self.estado == self.ABRIENDO:
            p = suave(self._t / self.APERTURA)
            self._radio = self.RADIO_CERRADO + (self.RADIO_BASE
                                                - self.RADIO_CERRADO) * p
            omega = self.OMEGA_BASE * (1.0 - 0.8 * p)   # se va frenando
            if self._t >= self.APERTURA:
                self.estado = self.ABIERTA
                self._t = 0.0
        elif self.estado == self.ABIERTA:
            omega = 0.0                                  # quieta: la ventana
            if self._t >= self.VENTANA:
                self.estado = self.NORMAL
                self._t = 0.0

        self._ang += omega * dt

        # El centro tampoco sale de la arena (con el radio de margen).
        m = self._radio + 24
        self.centro.x = max(self.arena.left + m,
                            min(self.arena.right - m, self.centro.x))
        self.centro.y = max(self.arena.top + 60,
                            min(self.suelo_y - 40, self.centro.y))

        pos = self.centro + pygame.Vector2(
            math.cos(self._ang), math.sin(self._ang)) * self._radio
        pos.y = min(pos.y, self.suelo_y - 14)
        boss.rect.center = (int(pos.x), int(pos.y))
        boss.position.update(float(boss.rect.x), float(boss.rect.y))

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2,
             boss_rect: pygame.Rect) -> None:
        cx = int(self.centro.x - offset.x)
        cy = int(self.centro.y - offset.y)
        if self.estado in (self.NORMAL, self.CERRANDO, self.FURIA,
                           self.ABRIENDO):
            # La órbita se dibuja tenue: el jugador debe poder leer por
            # dónde va a pasar el cuerpo. En el cierre, el anillo DESTINO
            # parpadea en aviso — el "va a achicarse hasta acá".
            pygame.draw.circle(surface, PERLA_OSC, (cx, cy),
                               int(self._radio), 1)
            if self.estado == self.CERRANDO:
                pygame.draw.circle(surface, AVISO, (cx, cy),
                                   int(self.RADIO_CERRADO), 1)
        if self.estado == self.ABIERTA:
            p = 0.5 + 0.5 * math.sin(self._t * 9.0)
            pygame.draw.circle(
                surface, PERLA_CLARA,
                (boss_rect.centerx - offset.x, boss_rect.centery - offset.y),
                int(24 + 4 * p), 2)
        # El corazón del giro: un punto donde está el centro, para que el
        # "adentro es seguro" tenga un adentro visible.
        pygame.draw.circle(surface, PERLA_OSC, (cx, cy), 3)
