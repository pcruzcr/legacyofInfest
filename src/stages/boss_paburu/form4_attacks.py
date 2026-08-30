# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
"""
Module: form4_attacks
System: stages.boss_paburu
Academic Unit: II (vectores), VI (interpolación y movimiento paramétrico)
Description: Forma 4 — EL ESPÍRITU DEL SHAMÁN, y el cierre EL OFRECIMIENTO
             (DISENO_NIVEL_Y_JEFE.md §3.6-3.7, GDD §4 Forma 4).

EL ACTO FINAL CITA A LOS TRES ANTERIORES
La Forma 4 no inventa peligros nuevos: convoca los que el jugador ya
aprendió. Las reliquias vuelven como satélites (RELIC_SURGE — y la variante
que NO salió en la Forma 3 debuta aquí: nadie ve todo en una partida, todos
lo ven todo en dos). El gemelo espejo repite la ola de la Forma 2 desde el
otro lado (SPIRIT_FORM). Los guardianes cruzan en procesión (ANCIENT_CALL,
lo coreografía la escena). Y los cuatro círculos del camposanto disparan sus
haces A TRAVÉS de la tierra (CONVERGENCE): el nivel entero era el arma,
visto desde abajo.

EL OFRECIMIENTO no está aquí como ataque de rotación: es la ceremonia de
muerte (el `JuicioFinal` de este módulo es su único proyectil) y la orquesta
el jefe al llegar a cero — ver `boss_paburu.py`.
"""
from __future__ import annotations

import math
from typing import Any

import pygame

# La paleta del Espíritu: el verde espectral de Paburu, más blanco — es el
# shamán sin la piedra, sin la máscara y sin la reliquia: solo el alma.
ALMA = (150, 255, 210)
ALMA_CLARA = (220, 255, 240)
ALMA_OSC = (30, 120, 80)
ORO = (232, 177, 44)
PERLA = (120, 92, 176)
AVISO = (255, 210, 90)


def suave(t: float) -> float:
    """Smoothstep 3t² − 2t³ (Unidad VI)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


class SateliteReliquia:
    """Una reliquia orbita al Espíritu un rato y se disuelve (RELIC_SURGE).

    Las DOS vuelven a la vez —la Pepita y la Perla—, en órbitas de radio y
    sentido distintos: quien peleó contra una en la Forma 3 reconoce a la
    otra al instante. El peligro es el contacto del cuerpo, como era en la
    Forma 3: la lección ya estaba aprendida.
    """

    RADIO_CUERPO = 9
    DANIO = 0.75
    VIDA = 6.5

    def __init__(self, duenio_pos: pygame.Vector2, variante: str,
                 radio: float, omega: float, fase: float) -> None:
        self.duenio = pygame.Vector2(duenio_pos)   # lo re-ancla el jefe
        self.variante = variante                   # "gold" | "black"
        self.radio = radio
        self.omega = omega
        self._ang = fase
        self._t = 0.0
        self.alive = True
        self.ya_golpeo = False
        self.pos = pygame.Vector2(duenio_pos)

    @property
    def is_telegraphing(self) -> bool:
        return self._t < 0.45      # nace tenue: medio segundo de cortesía

    def reanclar(self, duenio_pos: pygame.Vector2) -> None:
        self.duenio = pygame.Vector2(duenio_pos)

    def update(self, dt: float) -> None:
        self._t += dt
        self._ang += self.omega * dt
        # El radio respira: crece al nacer, se contrae al morir.
        r = self.radio * suave(min(1.0, self._t / 0.8))
        if self._t > self.VIDA - 0.8:
            r *= suave(max(0.0, (self.VIDA - self._t) / 0.8))
        self.pos = self.duenio + pygame.Vector2(
            math.cos(self._ang), math.sin(self._ang)) * r
        if self._t > self.VIDA:
            self.alive = False

    @property
    def rect(self) -> pygame.Rect | None:
        if self.is_telegraphing or not self.alive:
            return None
        r = self.RADIO_CUERPO
        return pygame.Rect(int(self.pos.x - r), int(self.pos.y - r), r * 2, r * 2)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        color = ORO if self.variante == "gold" else PERLA
        sx, sy = int(self.pos.x - offset.x), int(self.pos.y - offset.y)
        a = 0.5 if self.is_telegraphing else 1.0
        pygame.draw.circle(surface, tuple(int(c * a) for c in color),
                           (sx, sy), self.RADIO_CUERPO)
        pygame.draw.circle(surface, ALMA_CLARA, (sx, sy), 3)


class EspejoEspectral:
    """El gemelo del SPIRIT_FORM: aparece reflejado y repite la ola.

    No es un segundo jefe: es un eco visual que existe lo justo para lanzar
    la ola espectral DESDE EL OTRO LADO. Dos olas convergentes obligan al
    salto sincronizado — la lección de la Forma 2, con el doble de lectura.
    La ola la construye el jefe (reusa `SpiritWave`); esta clase es la
    figura: telegrafía, dispara y se disuelve.
    """

    TELEGRAFIADO = 0.7
    VIDA = 1.6

    def __init__(self, pos: pygame.Vector2, tam: tuple[int, int]) -> None:
        self.pos = pygame.Vector2(pos)
        self.tam = tam
        self._t = -self.TELEGRAFIADO
        self.alive = True
        self.disparo = False       # lo enciende el jefe al soltar la ola

    @property
    def is_telegraphing(self) -> bool:
        return self._t < 0.0

    def update(self, dt: float) -> None:
        self._t += dt
        if self._t > self.VIDA:
            self.alive = False

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        w, h = self.tam
        r = pygame.Rect(int(self.pos.x - w / 2 - offset.x),
                        int(self.pos.y - h - offset.y), w, h)
        if self.is_telegraphing:
            p = suave(1.0 + self._t / self.TELEGRAFIADO)
            pygame.draw.rect(surface, AVISO, r, 1)
            pygame.draw.line(surface, AVISO, (r.centerx, r.top),
                             (r.centerx, r.top - int(8 * p)), 1)
            return
        a = max(0.15, 1.0 - self._t / self.VIDA)
        cuerpo = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(cuerpo, (*ALMA, int(120 * a)),
                            pygame.Rect(4, 0, w - 8, h))
        pygame.draw.ellipse(cuerpo, (*ALMA_CLARA, int(160 * a)),
                            pygame.Rect(w // 2 - 6, 6, 12, 16))
        surface.blit(cuerpo, r.topleft)


class HazDelCirculo:
    """CONVERGENCE: un haz cae del techo — un círculo del camposanto
    disparando a través de la tierra.

    El aviso es una GRIETA de luz en la bóveda que gotea polvo: el jugador
    mira el techo porque el suelo se lo dice (la sombra del haz se marca en
    el piso, como la picada del gavilán). Después cae la columna de luz,
    ancha y breve. Cuatro haces secuenciales barren la sala dejando SIEMPRE
    un pasillo — castiga quedarse quieto, no estar en el lugar equivocado.
    """

    TELEGRAFIADO = 0.9
    DURACION = 0.55
    ANCHO = 56
    DANIO = 1.0

    def __init__(self, x: float, techo_y: float, suelo_y: float,
                 retraso: float = 0.0) -> None:
        self.x = x
        self.techo = techo_y
        self.suelo = suelo_y
        self._t = -self.TELEGRAFIADO - retraso
        self.alive = True
        self.ya_golpeo = False

    @property
    def is_telegraphing(self) -> bool:
        return self._t < 0.0

    def update(self, dt: float) -> None:
        self._t += dt
        if self._t > self.DURACION:
            self.alive = False

    @property
    def rect(self) -> pygame.Rect | None:
        if self.is_telegraphing or not self.alive:
            return None
        return pygame.Rect(int(self.x - self.ANCHO / 2), int(self.techo),
                           self.ANCHO, int(self.suelo - self.techo))

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        sx = int(self.x - offset.x)
        if self.is_telegraphing:
            p = suave(1.0 + self._t / self.TELEGRAFIADO)
            # La grieta en la bóveda y la sombra en el suelo.
            ty = int(self.techo - offset.y)
            pygame.draw.line(surface, AVISO, (sx - int(10 * p), ty),
                             (sx + int(10 * p), ty), 2)
            w = int(self.ANCHO * p)
            sy = int(self.suelo - offset.y)
            pygame.draw.ellipse(surface, AVISO, pygame.Rect(
                sx - w // 2, sy - 3, w, 6), 1)
            return
        r = self.rect
        if r is None:
            return
        vida = 1.0 - self._t / self.DURACION
        w = int(self.ANCHO * (0.6 + 0.4 * vida))
        columna = pygame.Surface((w, r.height), pygame.SRCALPHA)
        columna.fill((*ALMA, int(90 * vida)))
        nucleo = pygame.Surface((max(2, w // 3), r.height), pygame.SRCALPHA)
        nucleo.fill((*ALMA_CLARA, int(170 * vida)))
        surface.blit(columna, (sx - w // 2, int(r.top - offset.y)))
        surface.blit(nucleo, (sx - w // 6, int(r.top - offset.y)))


class JuicioFinal:
    """EL OFRECIMIENTO: el único ataque de la ceremonia de cierre.

    Una onda de juicio que crece desde el Espíritu hasta llenar la sala,
    con el telegraph MÁS LARGO de toda la pelea (2.2 s): es la última
    pregunta y se pregunta despacio. Es PARABLE, y esa parada es la firma
    de la pelea entera:

      · parry en la ventana → el juicio se vuelve contra el juez
        (`devuelto`): absolución.
      · sin parry → golpea UNA vez (1.0, los i-frames del jugador
        mandan) y se disipa: el jefe cae igual, pero quedás marcado.

    Se gana siempre; CÓMO se gana es lo que este ataque decide.
    """

    TELEGRAFIADO = 2.2
    VELOCIDAD_RADIO = 300.0
    GROSOR = 22
    DANIO = 1.0

    def __init__(self, centro: pygame.Vector2, radio_max: float) -> None:
        self.centro = pygame.Vector2(centro)
        self.radio_max = radio_max
        self.radio = 0.0
        self._t = -self.TELEGRAFIADO
        self.alive = True
        self.devuelto = False
        self.ya_golpeo = False

    @property
    def is_telegraphing(self) -> bool:
        return self._t < 0.0

    #: AUD-484 — EL JUICIO NO PUEDE MATAR. El diseño lo dice con todas las
    #: letras («se gana siempre; CÓMO se gana es la firma») y el código no lo
    #: respetaba: con 1,0 de vida el jugador moría en t=4,33 s del
    #: OFRECIMIENTO, con la pelea ya ganada y sin poder responder nada.
    #:
    #: Perder ahí no enseña la lección del ataque, la borra: el jugador no ve
    #: la absolución ni la marca, ve una pantalla de game over en la
    #: ceremonia de cierre y vuelve al checkpoint a repetir cuatro formas.
    #:
    #: Medio corazón es el suelo y no cero porque el ataque tiene que SEGUIR
    #: doliendo — no parar el juicio con un corazón deja al jugador al borde,
    #: que es exactamente la marca que el diseño quiere dejarle.
    VIDA_MINIMA = 0.5

    def danio_contra(self, player: Any) -> float:
        """El daño real de este juicio contra `player`, ya acotado.

        Vive aquí y no en el llamador porque la regla es del ATAQUE: quien
        conecte el golpe en el futuro —otro modo, un boss rush, una prueba—
        hereda el tope sin tener que acordarse de copiarlo.

        Se descuenta `incoming_damage_mult` porque `Player.apply_damage`
        MULTIPLICA lo que recibe por la dificultad (×1,5 en la difícil): un
        tope calculado sobre el valor de entrada dejaría de ser un tope justo
        en el modo donde más falta hace.
        """
        vida = float(getattr(player, "current_health", 0.0))
        margen = max(0.0, vida - self.VIDA_MINIMA)
        try:
            from src.engine.core.difficulty import get_config
            mult = float(get_config().incoming_damage_mult)
        except Exception:       # sin configuración: el ataque vale lo que dice
            mult = 1.0
        if mult > 0.0:
            margen /= mult
        return min(self.DANIO, margen)

    def devolver(self, _hacia: pygame.Vector2) -> None:
        """La parada de la absolución. El anillo se invierte hacia el juez."""
        if not self.devuelto:
            self.devuelto = True

    def update(self, dt: float) -> None:
        self._t += dt
        if self.is_telegraphing:
            return
        if self.devuelto:
            # El anillo colapsa de vuelta al centro, el doble de rápido.
            self.radio -= self.VELOCIDAD_RADIO * 2.0 * dt
            if self.radio <= 0:
                self.alive = False
            return
        self.radio += self.VELOCIDAD_RADIO * dt
        if self.radio > self.radio_max + 60:
            self.alive = False

    def toca(self, caja: pygame.Rect) -> bool:
        """Como el MaskPulse: solo el BORDE del anillo daña."""
        if self.is_telegraphing or not self.alive or self.devuelto:
            return False
        cx, cy = self.centro
        px = max(caja.left, min(cx, caja.right))
        py = max(caja.top, min(cy, caja.bottom))
        d = math.hypot(px - cx, py - cy)
        return abs(d - self.radio) <= self.GROSOR

    @property
    def rect(self) -> pygame.Rect | None:
        """Para el parry de la escena: la zona del frente del anillo."""
        if self.is_telegraphing or not self.alive or self.devuelto:
            return None
        r = int(self.radio + self.GROSOR)
        return pygame.Rect(int(self.centro.x - r), int(self.centro.y - r),
                           r * 2, r * 2)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        cx = int(self.centro.x - offset.x)
        cy = int(self.centro.y - offset.y)
        if self.is_telegraphing:
            # La acumulación: anillos que caen HACIA el centro, cada vez más
            # rápidos — el juicio se carga, y el compás lo marca la propia
            # animación aunque no suene la música.
            p = 1.0 + self._t / self.TELEGRAFIADO
            for k in range(3):
                f = (p * 1.6 + k / 3.0) % 1.0
                pygame.draw.circle(surface, AVISO, (cx, cy),
                                   int(150 * (1.0 - f)) + 8, 1)
            pygame.draw.circle(surface, ALMA_CLARA, (cx, cy),
                               6 + int(4 * suave(p)), 0)
            return
        color = ALMA_CLARA if self.devuelto else ALMA
        if self.radio > 4:
            pygame.draw.circle(surface, ALMA_OSC, (cx, cy),
                               int(self.radio) + 3, self.GROSOR // 3 + 2)
            pygame.draw.circle(surface, color, (cx, cy),
                               int(self.radio), self.GROSOR // 4 + 1)
