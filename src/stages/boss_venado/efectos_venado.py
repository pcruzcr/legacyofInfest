"""Módulo: efectos_venado
Sistema: efectos visuales puros del boss Venado -- pulido AAA de fase 2 (spec 2026-08-21)
    + nivel "Peregrinación al Venado" (spec 2026-08-24)
Descripción: puerto EfectosDelEscenario (partículas/cámara/estela sin conocer el motor) +
    dos implementaciones de prueba (EfectosNulos/EfectosRegistrados) + las configs
    BurstConfig propias de este boss + unidades visuales puras (OleadaDeLianas del ataque
    VINE_SWEEP, CrestaDePisoton/AnilloDeCaida/CoronaDeEsporas/EstrellasDeAturdimiento/
    SenalDeCastigo/EstelaDeFantasmas del pulido AAA parte 2, y alfa_de_niebla -- Tarea 8
    del nivel, B-046 en REGISTRO-DE-BUGS.md -- el perfil espacial puro del velo de niebla
    del corredor). Ninguna clase de aquí importa el motor ni la escena: todo lo que toca
    partículas/cámara/estela real pasa por el puerto, implementado en
    boss_venado_scene.EfectosDeLaEscena. La única excepción de import es
    ``tramos_venado`` (no es motor -- es la misma tabla de datos pura del propio nivel,
    ver ``alfa_de_niebla`` más abajo).
"""
from __future__ import annotations

import math
from typing import Protocol

import numpy as np
import pygame

from src.framework.vfx.particle_system import BurstConfig
from src.stages.boss_venado.tramos_venado import TABLA


class EfectosDelEscenario(Protocol):
    """Puerto que el boss usa para pedir partículas/cámara/estela sin conocer el motor.

    Los ángulos de `particulas_dirigidas` están en grados, eje Y hacia abajo (convención
    de pantalla): 0.0 = derecha, 90.0 = abajo, -90.0 = arriba, 180.0 = izquierda.
    """

    def particulas(self, x: float, y: float, config: BurstConfig) -> None:
        """Ráfaga omnidireccional -- el cono de ParticleEmitter.emit SIEMPRE arranca en 0°."""
        ...

    def particulas_dirigidas(self, x: float, y: float, angulo: float, config: BurstConfig) -> None:
        """Ráfaga centrada en `angulo` (grados) -- para abanicos CON dirección
        (polvo hacia arriba, escombros alejándose de una pared...)."""
        ...

    def sacudir(self, amplitud: float, duracion: float,
                direccion: tuple[float, float] | None) -> None:
        """Sacudida de cámara. `direccion=None` = sacudida isótropa (sin eje)."""
        ...

    def estela(self, x: float, y: float, size: tuple[int, int],
               color: tuple[int, int, int, int]) -> None:
        """Residuo de imagen (TrailSystem.capture_at) en la posición dada.

        Contrato conservado por compatibilidad -- desde la corrección
        visual del coordinador (Task 14-B, 2026-08-22) BossVenado ya NO
        llama a este método: TrailSystem dibuja un RECTÁNGULO de color
        plano (no una copia del sprite), y durante el aviso de STOMP ese
        rectángulo se quedaba encima del ciervo casi entero. El boss usa
        ahora ``EstelaDeFantasmas`` (más abajo en este mismo módulo), que
        pinta copias reales del sprite. ``EfectosDeLaEscena`` (la escena)
        sigue implementando este método -- sencillamente nadie lo invoca."""
        ...


class EfectosNulos:
    """Implementación no-op del puerto -- valor por defecto de BossVenado.efectos.

    Existe para que un boss construido sin escena (tests unitarios, grade_boss.py,
    el arnés de playtest headless, entity_factory al cargar el TMX) siga funcionando
    exactamente igual que antes de este pulido: sin escena, ningún VFX se pide de
    verdad, pero tampoco truena por AttributeError."""

    def particulas(self, x: float, y: float, config: BurstConfig) -> None:
        pass

    def particulas_dirigidas(self, x: float, y: float, angulo: float, config: BurstConfig) -> None:
        pass

    def sacudir(self, amplitud: float, duracion: float,
                direccion: tuple[float, float] | None) -> None:
        pass

    def estela(self, x: float, y: float, size: tuple[int, int],
               color: tuple[int, int, int, int]) -> None:
        pass


class EfectosRegistrados:
    """Implementación de prueba: registra cada llamada en una lista propia, para que
    los tests del boss verifiquen QUÉ efecto se pidió (y con qué argumentos) sin
    arrancar ParticleSystem/Camera/TrailSystem reales."""

    def __init__(self) -> None:
        self.particulas_emitidas: list[tuple[float, float, BurstConfig]] = []
        self.particulas_dirigidas_emitidas: list[tuple[float, float, float, BurstConfig]] = []
        self.sacudidas: list[tuple[float, float, tuple[float, float] | None]] = []
        self.estelas: list[tuple[float, float, tuple[int, int], tuple[int, int, int, int]]] = []

    def particulas(self, x: float, y: float, config: BurstConfig) -> None:
        self.particulas_emitidas.append((x, y, config))

    def particulas_dirigidas(self, x: float, y: float, angulo: float, config: BurstConfig) -> None:
        self.particulas_dirigidas_emitidas.append((x, y, angulo, config))

    def sacudir(self, amplitud: float, duracion: float,
                direccion: tuple[float, float] | None) -> None:
        self.sacudidas.append((amplitud, duracion, direccion))

    def estela(self, x: float, y: float, size: tuple[int, int],
               color: tuple[int, int, int, int]) -> None:
        self.estelas.append((x, y, size, color))


def cada_n_frames(contador: int, n: int) -> bool:
    """True exactamente cada n fotogramas (n<=0 nunca dispara).

    Las cadencias de este módulo se expresan en fotogramas de update(), NUNCA en
    tiempo real acumulado: el arnés de playtest corre a paso fijo y es determinista,
    pero el copiloto (juego humano) no -- expresar la cadencia en frames mantiene las
    dos rutas reproducibles con la misma fórmula."""
    return n > 0 and contador % n == 0


# ──────────────────────────────────────────────
# Configs BurstConfig propias del boss.
#
# Este bloque solo trae las de la oleada de lianas (VINE_SWEEP, spec §2.1). Las del
# resto del pulido AAA -- POLVO_PISOTON, HOJAS, POLVO_ASENTANDOSE (STOMP §2.2),
# MOTAS, POLEN, NUBE_ESPORA (MUSHROOM_SPORE §2.3), POLVO_RASPADO, POLVO_PEZUNAS,
# ESCOMBROS (CHARGE §2.4) -- las añade el plan parte 2 aquí mismo, no en un archivo
# nuevo.
# ──────────────────────────────────────────────
POLVO_ATERRIZAJE = BurstConfig(count=8, speed=90.0, lifetime=0.4, size=(2, 4),
                               color=(180, 150, 110), spread=160.0,
                               gravity=300.0, friction=0.85)
TIERRA_OLEADA = BurstConfig(count=3, speed=70.0, lifetime=0.35, size=(2, 3),
                            color=(120, 95, 70), spread=140.0,
                            gravity=300.0, friction=0.9)


# ──────────────────────────────────────────────
# Oleada de lianas (VINE_SWEEP, spec 2026-08-21 §2.1)
# ──────────────────────────────────────────────
OLEADA_VEL = 380.0        # px/s -- cruza media arena (~392px) en ~1.03s
OLEADA_ANCHO = 40
OLEADA_ALTO = 24
OLEADA_SEPARACION = 24    # separación inicial desde el centro del jefe, en direcciones opuestas


class OleadaDeLianas:
    """Una de las dos crestas viajeras que dispara VINE_SWEEP en fase 2.

    Nace en `x` (normalmente `boss.rect.centerx ± OLEADA_SEPARACION`), viaja en línea
    recta a `velocidad` px/s en la dirección `direccion` (+1 derecha, -1 izquierda),
    a ras del suelo (`rect.bottom == y_suelo`), y muere sola al salir de
    `[x_min, x_max]` (choca con una pared de la arena, `murio_en_pared=True`) o cuando
    algo externo llama a `golpeada()` (conectó con el jugador, `consumida=True`). No
    conoce al boss ni al motor: es geometría + un par de banderas, actualizada por
    quien la posea (`BossVenado._oleadas`)."""

    def __init__(self, x: float, direccion: int, y_suelo: float,
                 x_min: float, x_max: float, velocidad: float = OLEADA_VEL) -> None:
        self.x = x
        self.direccion = direccion
        self.y_suelo = y_suelo
        self.x_min = x_min
        self.x_max = x_max
        self.velocidad = velocidad
        self.viva = True
        self.consumida = False
        self.murio_en_pared = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - OLEADA_ANCHO / 2), int(self.y_suelo - OLEADA_ALTO),
            OLEADA_ANCHO, OLEADA_ALTO)

    def update(self, dt: float) -> None:
        """Task 9 (revisión final 2026-08-21): la oleada muere al TOCAR la
        pared, nunca sobresale de la arena.

        La condición vieja (``r.right < x_min or r.left > x_max``) exigía
        que el rect saliera POR COMPLETO de ``[x_min, x_max]`` antes de
        morir -- con ``OLEADA_ANCHO=40``, eso dejaba hasta 40px de la cresta
        sobresaliendo de la pared en su último fotograma vivo (evidencia:
        candado ``no_damage_outside_arena``/``boss_in_arena`` de la revisión
        final). Ahora muere en el PRIMER fotograma en que su borde
        DELANTERO toca la pared (``r.right >= x_max`` yendo a la derecha,
        ``r.left <= x_min`` yendo a la izquierda) y, si ese fotograma ya
        sobresalía, recoloca ``self.x`` para quedar EXACTAMENTE tangente a
        la pared antes de morir -- así el último dibujo/ráfaga de tierra cae
        sobre la pared, no más allá de ella."""
        if not self.viva:
            return
        self.x += self.direccion * self.velocidad * dt
        r = self.rect
        if self.direccion < 0 and r.left <= self.x_min:
            self.x = self.x_min + OLEADA_ANCHO / 2.0
            self.viva = False
            self.murio_en_pared = True
        elif self.direccion > 0 and r.right >= self.x_max:
            self.x = self.x_max - OLEADA_ANCHO / 2.0
            self.viva = False
            self.murio_en_pared = True

    def golpeada(self) -> None:
        """La oleada conectó con el jugador -- se consume, no cuenta como muerte de pared."""
        self.viva = False
        self.consumida = True

    def dibujar_mundo(self, surface: pygame.Surface, camera_offset: pygame.Vector2,
                      t: float) -> None:
        """Cresta dentada de 5 picos (painter's order, pase de mundo -- bajo la luz).

        La base oscila verticalmente ±2px a 12Hz (`t` es el reloj de VFX acumulado del
        boss, `self._t_vfx`, NO tiempo de pared): un temblor sutil que lee como
        vegetación viva, no como un rectángulo estático viajando."""
        if not self.viva:
            return
        ox, oy = camera_offset.x, camera_offset.y
        r = self.rect
        oscilacion = 2.0 * math.sin(2.0 * math.pi * 12.0 * t)
        base_y = int(self.y_suelo - oy + oscilacion)
        left = int(r.left - ox)
        n_dientes = 5
        paso = r.width / n_dientes
        puntos = [(left, base_y)]
        for i in range(n_dientes):
            centro_x = int(left + paso * (i + 0.5))
            puntos.append((centro_x, base_y - OLEADA_ALTO))
            puntos.append((int(left + paso * (i + 1)), base_y))
        pygame.draw.polygon(surface, (140, 200, 110), puntos)
        pygame.draw.polygon(surface, (40, 70, 40), puntos, 1)

    def dibujar_overlay(self, surface: pygame.Surface, camera_offset: pygame.Vector2,
                        color: tuple[int, int, int]) -> None:
        """Filo de 2px sobre la línea de los picos + grieta de 32px por delante de la
        cresta (post-luz -- legible de noche, mismo criterio que el resto de avisos
        del boss desde la campaña de fairness, Cambio 3)."""
        if not self.viva:
            return
        ox, oy = camera_offset.x, camera_offset.y
        r = self.rect
        cresta_y = int(r.top - oy)
        pygame.draw.line(surface, color, (int(r.left - ox), cresta_y),
                         (int(r.right - ox), cresta_y), 2)
        borde_delantero = r.right if self.direccion > 0 else r.left
        extremo_grieta = borde_delantero + self.direccion * 32
        # B-036 (revisor #2, addenda Task 1 punto 1): recortar ambos extremos
        # de la grieta a [x_min, x_max] -- sin esto, una oleada cerca de la
        # pared proyecta la grieta hasta 32px más allá del límite de la
        # arena (cosmético, pero visible; detectado en la revisión final de
        # la Parte 1).
        borde_delantero = max(self.x_min, min(self.x_max, borde_delantero))
        extremo_grieta = max(self.x_min, min(self.x_max, extremo_grieta))
        grieta_y = int(self.y_suelo - 2 - oy)
        x0 = int(borde_delantero - ox)
        x1 = int(extremo_grieta - ox)
        pygame.draw.line(surface, color, (x0, grieta_y), (x1, grieta_y), 1)


# ──────────────────────────────────────────────
# Pulido AAA fase 2 (diseño 2026-08-21) — §2.2-2.5, §3.1
# ──────────────────────────────────────────────

# Nueve ráfagas nuevas, una por gesto físico del diseño: pisotón (POLVO_
# PISOTON/HOJAS/POLVO_ASENTANDOSE), esporas (MOTAS/POLEN/NUBE_ESPORA) y
# embestida de fase 2 (POLVO_RASPADO/POLVO_PEZUNAS/ESCOMBROS). Valores
# fijados por el diseño, no ajustados a mano aquí.
POLVO_PISOTON = BurstConfig(18, 140.0, 0.45, (2, 5), (180, 150, 110), 160.0, 320.0, 0.85)
HOJAS = BurstConfig(6, 30.0, 1.2, (2, 3), (110, 160, 90), 120.0, 60.0, 0.95)
POLVO_ASENTANDOSE = BurstConfig(4, 25.0, 0.5, (1, 3), (170, 145, 110), 360.0, 40.0, 0.9)
MOTAS = BurstConfig(2, 20.0, 0.6, (1, 2), (200, 230, 160), 60.0, -40.0, 0.95)
POLEN = BurstConfig(1, 10.0, 0.35, (1, 2), (200, 230, 160), 360.0, 0.0, 0.9)
NUBE_ESPORA = BurstConfig(6, 40.0, 0.3, (2, 3), (190, 220, 150), 360.0, 0.0, 0.85)
POLVO_RASPADO = BurstConfig(3, 60.0, 0.3, (2, 3), (170, 145, 110), 50.0, 200.0, 0.9)
POLVO_PEZUNAS = BurstConfig(2, 40.0, 0.3, (2, 3), (170, 145, 110), 60.0, 250.0, 0.9)
ESCOMBROS = BurstConfig(10, 110.0, 0.5, (2, 4), (150, 140, 130), 120.0, 400.0, 0.85)

# Duración visual de la onda del pisotón -- mismo valor que boss_venado.
# STOMP_WINDOW, pero declarado aquí como constante propia porque esta
# unidad es pura y no debe importar del boss (dependencia en un solo
# sentido: boss_venado.py importa de aquí, nunca al revés).
STOMP_WINDOW_VISUAL = 0.35


def _ease_out(u: float) -> float:
    """1 - (1-u)^2, clampado a [0,1] -- arranca rápido y frena suave."""
    u = max(0.0, min(1.0, u))
    return 1.0 - (1.0 - u) ** 2


def _ease_in(u: float) -> float:
    """u^2, clampado a [0,1] -- arranca lento y acelera."""
    u = max(0.0, min(1.0, u))
    return u * u


class CrestaDePisoton:
    """Dos montículos de tierra que nacen bajo el pisotón y se separan del
    centro con ease-out durante STOMP_WINDOW_VISUAL segundos -- puramente
    visual, no representa el rect de daño (que sigue siendo el Rect(96x8)
    estático que arma boss_venado._do_stomp)."""

    ANCHO = 14.0
    ALTO = 10.0
    DESPLAZAMIENTO_MAXIMO = 48.0

    def __init__(self, centro_x: float, y_suelo: float,
                 duracion: float = STOMP_WINDOW_VISUAL) -> None:
        self.centro_x = centro_x
        self.y_suelo = y_suelo
        self.duracion = duracion
        self._t = 0.0

    @property
    def viva(self) -> bool:
        return self._t < self.duracion

    @property
    def desplazamiento(self) -> float:
        if self.duracion <= 0:
            return self.DESPLAZAMIENTO_MAXIMO
        progreso = min(1.0, self._t / self.duracion)
        return self.DESPLAZAMIENTO_MAXIMO * _ease_out(progreso)

    def update(self, dt: float) -> None:
        self._t += dt

    def _puntos_monticulo(self, cx: float) -> list[tuple[float, float]]:
        mitad = self.ANCHO / 2.0
        return [(cx - mitad, self.y_suelo), (cx + mitad, self.y_suelo),
                (cx, self.y_suelo - self.ALTO)]

    def dibujar_mundo(self, surface: "pygame.Surface", camera_offset: "pygame.Vector2") -> None:
        # Guard por tiempo, NO por `viva`: `viva` es estrictamente t<duracion
        # (así el dueño sabe cuándo retirar la cresta de su lista), pero el
        # último fotograma exacto (t==duracion, desplazamiento ya en su
        # máximo) todavía debe pintarse -- si guardáramos por `viva` la
        # cresta desaparecería un fotograma antes de llegar a su extensión
        # máxima, un "pop" visible.
        if self._t > self.duracion:
            return
        ox, oy = camera_offset.x, camera_offset.y
        despl = self.desplazamiento
        for signo in (-1.0, 1.0):
            cx = self.centro_x + signo * despl
            puntos = [(x - ox, y - oy) for x, y in self._puntos_monticulo(cx)]
            pygame.draw.polygon(surface, (120, 95, 70), puntos)
            pygame.draw.polygon(surface, (60, 45, 35), puntos, 1)

    def dibujar_overlay(self, surface: "pygame.Surface", camera_offset: "pygame.Vector2",
                         color: tuple[int, int, int]) -> None:
        """Filo de 2px en la cima de cada montículo -- versión post-luz de la
        cresta, legible de noche (mismo criterio que el resto de los
        overlays del boss)."""
        if self._t > self.duracion:  # ver comentario de dibujar_mundo
            return
        ox, oy = camera_offset.x, camera_offset.y
        despl = self.desplazamiento
        cima_y = self.y_suelo - self.ALTO - oy
        for signo in (-1.0, 1.0):
            cx = self.centro_x + signo * despl - ox
            pygame.draw.line(surface, color, (cx - 4.0, cima_y), (cx + 4.0, cima_y), 2)


class AnilloDeCaida:
    """Anillo de 12 puntos que se contrae de 48px a 8px de radio según se
    acerca el impacto del pisotón (progreso 0->1 sobre STOMP_TELEGRAPH,
    calculado por el llamante). Estático y puro: no guarda estado propio."""

    NUM_PUNTOS = 12
    RADIO_INICIAL = 48.0
    RADIO_FINAL = 8.0

    @staticmethod
    def dibujar_overlay(surface: "pygame.Surface", centro: tuple[int, int],
                         progreso: float, color: tuple[int, int, int]) -> None:
        progreso = max(0.0, min(1.0, progreso))
        radio = (AnilloDeCaida.RADIO_INICIAL
                 - (AnilloDeCaida.RADIO_INICIAL - AnilloDeCaida.RADIO_FINAL) * _ease_in(progreso))
        cx, cy = centro
        for i in range(AnilloDeCaida.NUM_PUNTOS):
            angulo = (2.0 * math.pi * i) / AnilloDeCaida.NUM_PUNTOS
            px = int(cx + math.cos(angulo) * radio)
            py = int(cy + math.sin(angulo) * radio)
            pygame.draw.circle(surface, color, (px, py), 2)


class CoronaDeEsporas:
    """Círculo sobre la corona del venado que se hincha de 6px a 14px de
    radio durante el aviso de MUSHROOM_SPORE (ease-out)."""

    RADIO_BASE = 6.0
    RADIO_EXTRA = 8.0

    @staticmethod
    def dibujar_overlay(surface: "pygame.Surface", centro_corona: tuple[int, int],
                         progreso: float, color: tuple[int, int, int]) -> None:
        progreso = max(0.0, min(1.0, progreso))
        radio = CoronaDeEsporas.RADIO_BASE + CoronaDeEsporas.RADIO_EXTRA * _ease_out(progreso)
        # +1: pygame.draw.circle con ancho de trazo pinta el borde 2px hacia
        # ADENTRO del radio pedido (el píxel más externo cae en radio-1, no
        # en radio) -- verificado empíricamente con width=2. Sin el +1 el
        # radio "visible" queda sistemáticamente 1px por debajo del calculado.
        pygame.draw.circle(surface, color, centro_corona, int(round(radio)) + 1, 2)


class EstrellasDeAturdimiento:
    """Tres puntos en órbita sobre la cabeza del venado durante la pausa de
    pared de CHARGE -- el clásico "aturdido" de videojuego, puramente
    temporal (t = boss._t_vfx, no depende del contador de fotogramas)."""

    NUM_ESTRELLAS = 3
    RADIO_ORBITA = 10.0
    VUELTAS_POR_SEGUNDO = 1.5
    ALTURA_SOBRE_CABEZA = 10.0

    @staticmethod
    def dibujar_overlay(surface: "pygame.Surface", centro_cabeza: tuple[int, int],
                         t: float, color: tuple[int, int, int]) -> None:
        cx = centro_cabeza[0]
        cy = centro_cabeza[1] - EstrellasDeAturdimiento.ALTURA_SOBRE_CABEZA
        for k in range(EstrellasDeAturdimiento.NUM_ESTRELLAS):
            angulo = (2.0 * math.pi * EstrellasDeAturdimiento.VUELTAS_POR_SEGUNDO * t
                      + k * (2.0 * math.pi / EstrellasDeAturdimiento.NUM_ESTRELLAS))
            px = int(cx + math.cos(angulo) * EstrellasDeAturdimiento.RADIO_ORBITA)
            py = int(cy + math.sin(angulo) * EstrellasDeAturdimiento.RADIO_ORBITA)
            pygame.draw.circle(surface, color, (px, py), 2)


NIVELES_BRILLO_CACHE = 16
"""Cuantización de self._cache_brillo de SenalDeCastigo (addenda del
revisor #2, punto 2, ampliada por la corrección visual del coordinador --
Task 14-A, 2026-08-22). ``round(b, 2)`` crudo daría hasta ~81 valores de
brillo distintos por clave (b vive en [0.2, 1.0]) -- demasiado alto para
una técnica que solo necesita verse fluida a 3Hz; 16 niveles ya son
imperceptibles al ojo y acotan la caché en 16x por clave, no 81x."""


def _dilatar_8_vecinos(mascara: "np.ndarray") -> "np.ndarray":
    """Dilatación booleana de `mascara` (2D) a sus 8 vecinos (radio 1px),
    por slicing -- NUNCA ``np.roll``: con ``roll`` el contenido que sale
    por un borde se enrollaría sobre el borde OPUESTO del array,
    contaminando la dilatación con datos que no existen ahí. `mascara` debe
    traer, como mínimo, 1px de borde a cero en cada lado (ver
    SenalDeCastigo._construir_anillo) para que la dilatación pueda crecer
    hacia afuera sin salirse del array."""
    ancho, alto = mascara.shape
    salida = np.zeros_like(mascara)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            sx0, sx1 = max(0, -dx), ancho - max(0, dx)
            dx0, dx1 = max(0, dx), ancho - max(0, -dx)
            sy0, sy1 = max(0, -dy), alto - max(0, dy)
            dy0, dy1 = max(0, dy), alto - max(0, -dy)
            salida[dx0:dx1, dy0:dy1] |= mascara[sx0:sx1, sy0:sy1]
    return salida


class SenalDeCastigo:
    """Señal universal de ventana de castigo (§2.5) -- REDISEÑADA por la
    corrección visual del coordinador (Task 14-A, 2026-08-22): un ANILLO de
    contorno de 1px, nunca la silueta completa.

    La primera versión (silueta completa dorada, en las 4 compensaciones de
    1px, aditiva) copiaba la técnica de ``dibujar_con_contorno`` del motor
    SIN la pieza que la hace funcionar: el motor dibuja las 4 siluetas
    DETRÁS del frame real y el frame ENCIMA, así que de cada una solo asoma
    1px en el borde -- aquí, en el overlay post-luz, no hay frame real que
    tapar esas 4 siluetas por encima, así que quedaban las 4 ENTERAS sobre
    el sprite ya dibujado: dorado x4 en modo aditivo saturaba el cuerpo
    completo a blanco sólido (zoom_stomp.png f1790/f1840, zoom_sweep.png
    f5874/f5904/f5928). Y como el pulso viejo
    (``0.35 + 0.35·sin(2π·5·t)``) tocaba 0 en el valle, la señal se apagaba
    un instante de cada ciclo (f1856/f5889: "vuelve a verde").

    Técnica nueva: ``mascara = alfa del frame > 0``; ``anillo =
    dilatar(mascara, 8 vecinos, 1px) AND NOT mascara`` -- estrictamente
    FUERA de la silueta, nunca sobre ella. Un solo blit aditivo del anillo
    (no 4 de la silueta entera) con un pulso que vive en [0.2, 1.0] --
    NUNCA toca 0 -- a 3Hz.

    Dos cachés, mismo criterio de acotación de siempre (§9 del diseño):
    - self._cache: el anillo RGBA crudo (color fijo, alfa 255 en el
      contorno, 0 en el resto -- RGB también 0 fuera del contorno, así que
      BLEND_RGBA_ADD es un no-op exacto ahí, sin fantasmas que compensar),
      indexado por (anim_key, frame_idx, facing_direction, escala) --
      acotada por combinatoria, NUNCA por id(frame). Expone tamano_cache().
    - self._cache_brillo: copias del anillo con el brillo del instante YA
      multiplicado, indexadas por (clave, nivel_de_brillo_cuantizado a
      NIVELES_BRILLO_CACHE niveles). Expone tamano_cache_brillo().
    """

    def __init__(self, color: tuple[int, int, int] = (250, 220, 120)) -> None:
        self.color = color
        self._cache: dict[tuple[str, int, int, float], "pygame.Surface"] = {}
        self._cache_brillo: dict[tuple[tuple[str, int, int, float], int], "pygame.Surface"] = {}

    @staticmethod
    def brillo(t: float) -> float:
        """Pulso de brillo en [0.2, 1.0] a 3Hz -- NUNCA toca 0 (a
        diferencia del pulso viejo de 5Hz, que sí tocaba 0 y apagaba la
        señal un instante de cada ciclo)."""
        return 0.6 + 0.4 * math.sin(2.0 * math.pi * 3.0 * t)

    def anillo(self, frame: "pygame.Surface",
               clave: tuple[str, int, int, float]) -> "pygame.Surface":
        """Construye (o recupera de caché) el anillo de contorno de 1px de
        `frame`, indexado por `clave`. Superficie SRCALPHA de tamaño
        frame+2 (1px de margen por cada lado: el contorno puede caer justo
        fuera del rect original cuando el sprite toca su propio borde)."""
        cacheado = self._cache.get(clave)
        if cacheado is not None:
            return cacheado
        anillo = self._construir_anillo(frame)
        self._cache[clave] = anillo
        return anillo

    def _construir_anillo(self, frame: "pygame.Surface") -> "pygame.Surface":
        ancho, alto = frame.get_size()
        vista_alfa = pygame.surfarray.pixels_alpha(frame)
        mascara = vista_alfa > 0
        del vista_alfa  # soltar el lock de la superficie cuanto antes

        # 1px de borde de ceros por cada lado -- deja que el anillo se
        # extienda fuera del rect original cuando la silueta toca su borde,
        # y evita que _dilatar_8_vecinos necesite wrap-around.
        con_borde = np.zeros((ancho + 2, alto + 2), dtype=bool)
        con_borde[1:-1, 1:-1] = mascara
        dilatado = _dilatar_8_vecinos(con_borde)
        anillo_mascara = dilatado & ~con_borde

        superficie = pygame.Surface((ancho + 2, alto + 2), pygame.SRCALPHA)
        rgb = pygame.surfarray.pixels3d(superficie)
        alfa_out = pygame.surfarray.pixels_alpha(superficie)
        try:
            for canal, valor in enumerate(self.color):
                rgb[:, :, canal] = np.where(anillo_mascara, valor, 0)
            alfa_out[:, :] = np.where(anillo_mascara, 255, 0)
        finally:
            del rgb
            del alfa_out
        return superficie

    def dibujar_overlay(self, surface: "pygame.Surface", frame: "pygame.Surface",
                         clave: tuple[str, int, int, float],
                         destino: tuple[int, int], t: float) -> None:
        b = self.brillo(t)
        # Cuantiza b (que vive en [0.2, 1.0]) a NIVELES_BRILLO_CACHE niveles
        # enteros -- ver NIVELES_BRILLO_CACHE arriba.
        nivel = int(round((b - 0.2) / 0.8 * (NIVELES_BRILLO_CACHE - 1)))
        nivel = max(0, min(NIVELES_BRILLO_CACHE - 1, nivel))
        clave_brillo = (clave, nivel)
        anillo_con_brillo = self._cache_brillo.get(clave_brillo)
        if anillo_con_brillo is None:
            base = self.anillo(frame, clave)
            anillo_con_brillo = base.copy()
            b_cuantizado = 0.2 + nivel / (NIVELES_BRILLO_CACHE - 1) * 0.8
            canal = max(0, min(255, int(255 * b_cuantizado)))
            # BLEND_RGB_MULT (no RGBA): el brillo se cocina SOLO en RGB. El
            # canal alfa se deja como está (255 en el contorno) -- el
            # contorno queda oscuro pero presente en el valle del pulso,
            # nunca transparente y perdido (y el valle ya no es 0, ver
            # brillo() arriba).
            anillo_con_brillo.fill((canal, canal, canal), special_flags=pygame.BLEND_RGB_MULT)
            self._cache_brillo[clave_brillo] = anillo_con_brillo
        x, y = destino
        # UN solo blit (Task 14-A: ya no son 4 compensaciones de la silueta
        # completa) -- el anillo crudo trae alfa 0 fuera de su contorno, así
        # que BLEND_RGBA_ADD es un no-op exacto ahí, sin fantasmas que
        # compensar. Offset (-1,-1): la superficie del anillo es frame+2 con
        # 1px de margen por lado (ver _construir_anillo), hay que retroceder
        # 1px para que el anillo quede centrado sobre el frame real.
        surface.blit(anillo_con_brillo, (x - 1, y - 1), special_flags=pygame.BLEND_RGBA_ADD)

    def tamano_cache(self) -> int:
        """Tamaño de la caché de ANILLOS crudos -- la que el diseño exige
        acotar por combinatoria (§9)."""
        return len(self._cache)

    def tamano_cache_brillo(self) -> int:
        """Tamaño de la caché de brillo -- acotada por
        combinaciones_de_clave * NIVELES_BRILLO_CACHE."""
        return len(self._cache_brillo)


class EstelaDeFantasmas:
    """(B) del coordinador, Task 14 (2026-08-22): fantasmas del SPRITE del
    jefe, nunca los rectángulos de color plano de
    ``TrailSystem.capture_at`` del motor -- ese sistema dibuja un
    RECTÁNGULO sólido/translúcido del tamaño del rect, y durante el aviso
    de STOMP (el jefe apenas se desplaza) ese rectángulo se quedaba ENCIMA
    del ciervo, tapándolo casi entero (zoom_stomp.png f1800-f1826: "bloque
    verde con el venado apenas visible dentro").

    Cada fantasma es una COPIA del frame vivo del jefe (no un rect), con un
    tinte verde liana ya cocinado en el momento de agregarse (más barato
    que teñir en cada dibujar_mundo) y un ``ttl`` que decrece con
    ``update(dt)`` -- se purga en cuanto llega a 0. ``dibujar_mundo()``
    modula el alfa de cada Surface guardada según el ``ttl`` restante: a
    diferencia de SenalDeCastigo (overlay post-luz, GPU, BLEND_RGBA_ADD --
    ver H-28), esta clase pinta en el PASE DE MUNDO (``draw()``, compuesto
    por software contra ``internal_surface`` ANTES de subir la textura
    GL), donde la composición por alfa estándar de pygame no tiene el
    problema de H-28 y ``set_alpha`` funciona sin trampas."""

    TINTE = (120, 200, 140)
    ALFA_PICO = 110

    def __init__(self, capacidad: int = 6, vida: float = 0.22) -> None:
        self.capacidad = capacidad
        self.vida = vida
        self._fantasmas: list[dict] = []   # cada uno: {"surface", "pos", "ttl"}

    def agregar(self, frame: "pygame.Surface", destino_mundo: tuple[float, float]) -> None:
        """Copia `frame` (tal cual lo ve el jugador -- el llamante lo saca
        de ``_frame_vivo()``, sin filtro de fase ni tinte de transición),
        lo tiñe verde liana UNA sola vez, y lo agrega con ttl=vida. Si
        supera `capacidad`, descarta el fantasma MÁS VIEJO (FIFO)."""
        teñido = frame.copy()
        teñido.fill(self.TINTE, special_flags=pygame.BLEND_RGB_MULT)
        self._fantasmas.append({"surface": teñido, "pos": destino_mundo, "ttl": self.vida})
        if len(self._fantasmas) > self.capacidad:
            self._fantasmas.pop(0)

    def update(self, dt: float) -> None:
        for fantasma in self._fantasmas:
            fantasma["ttl"] -= dt
        self._fantasmas = [f for f in self._fantasmas if f["ttl"] > 0]

    def dibujar_mundo(self, surface: "pygame.Surface", camera_offset: "pygame.Vector2") -> None:
        """Pase de MUNDO (bajo la luz, como el resto de entidades) --
        composición por software normal, sin BLEND_RGBA_ADD: set_alpha SÍ
        funciona aquí (ver el docstring de la clase)."""
        ox, oy = camera_offset.x, camera_offset.y
        for fantasma in self._fantasmas:
            proporcion = max(0.0, min(1.0, fantasma["ttl"] / self.vida))
            fantasma["surface"].set_alpha(int(self.ALFA_PICO * proporcion))
            x, y = fantasma["pos"]
            surface.blit(fantasma["surface"], (int(x - ox), int(y - oy)))

    def limpiar(self) -> None:
        self._fantasmas.clear()

    def cantidad(self) -> int:
        return len(self._fantasmas)


# ──────────────────────────────────────────────
# Velo de niebla del corredor (Tarea 8 del nivel "Peregrinación al Venado",
# REDISEÑO tras B-046 -- REGISTRO-DE-BUGS.md, revisión de spec 2026-08-25)
# ──────────────────────────────────────────────
#
# La Tarea 8 intentó primero cablear el clima del corredor al mecanismo real
# del motor (``WorldSimulation``/``WeatherSystem`` vía la puerta
# ``_cambiar_clima``, ``simulacion.py:264``). Se retiró por completo tras
# encontrar dos bugs de MOTOR que invalidaban la premisa: (1) esta escena
# declara ``day_length=0`` (exigido por el doc 86 §3.2 para jefes de Zona 1),
# lo que dejaba a ``self._reloj.congelado`` permanentemente en ``True`` y por
# tanto el gate de ``stage_parts/actualizaciones.py:148-150`` nunca dejaba
# correr ``WorldSimulation.update()`` -- ninguna transición del clima habría
# avanzado JAMÁS, ni una sola vez, en toda la pelea; (2) incluso sin ese gate,
# ``WeatherSystem._set_climate_params`` (``weather_system.py:56-86``) fija su
# ``_overlay_alpha`` de forma síncrona e instantánea desde una tabla -- no
# existe ninguna interpolación en el propio ``WeatherSystem`` para ese campo,
# así que la capa visual de niebla que el jugador REALMENTE ve en pantalla
# siempre habría aparecido de golpe en un único cuadro, sin importar qué tan
# "suave" se pidiera la transición del lado de ``WorldSimulation``.
#
# ``alfa_de_niebla`` reemplaza esa idea por completo: es un perfil puramente
# ESPACIAL (función pura de la columna de mundo del jugador, nunca de tiempo
# transcurrido ni de ningún sistema del motor), así que la suavidad de la
# transición es una propiedad GEOMÉTRICA de la función -- sube y baja suave
# en ambas direcciones por construcción, sin depender de que nada avance
# cuadro a cuadro ni de ningún reloj. Quien dibuja el velo (ver
# ``_dibujar_velo_de_niebla`` en ``boss_venado_scene.py``, wireado desde
# ``dibujar_ui``) solo necesita volver a evaluar esta función con la x
# actual del jugador cada cuadro -- no hay estado que mantener aquí.

#: Alfa máximo del velo (0-255) -- mismo valor que
#: ``WeatherSystem.CLIMATE_PARAMS["fog"]["overlay_alpha"]``
#: (``weather_system.py:21``), para que quien conozca el clima del motor
#: reconozca el número (aunque el mecanismo real ya no pase por ahí).
VELO_ALFA_MAX = 80

#: Color del velo -- mismo ``overlay_color`` que declara
#: ``WeatherSystem.CLIMATE_PARAMS["fog"]`` (``weather_system.py:21``): un
#: gris azulado neutro, no un color propio de este nivel.
VELO_COLOR: tuple[int, int, int] = (180, 180, 190)

#: Ancho de la rampa de entrada (0 -> VELO_ALFA_MAX), en píxeles de mundo.
#: 200px a la velocidad de paseo del jugador (``settings.PLAYER_WALK_SPEED``
#: = 90 px/s) son poco más de 2s -- suficiente para que la niebla se sienta
#: como que "llega", no como un parpadeo.
VELO_RAMPA_ENTRADA = 200.0

#: Ancho de la rampa de salida (VELO_ALFA_MAX -> 0), en píxeles de mundo.
#: Más corta que la de entrada (100 contra 200) a propósito -- la niebla se
#: "aparta" al acercarse a lo sagrado con más urgencia de la que tardó en
#: llegar, reforzando la lectura narrativa (ver el docstring de
#: ``alfa_de_niebla``).
VELO_RAMPA_SALIDA = 100.0

#: Dónde empieza el velo -- x_inicio del Acto 3 "El umbral", el único tramo
#: con ``clima == "fog"`` en toda la tabla (derivado de TABLA, no un número
#: mágico repetido: si algún día el diseño narrativo mueve el Acto 3, este
#: velo se mueve solo con él).
VELO_X_INICIO = TABLA[2].x_inicio

#: Dónde termina el velo -- x_inicio del Acto 4 "Lo sagrado", que coincide
#: con el borde de la arena (`boss_venado.ARENA_X0`, la constante canónica
#: del boss -- verificado literalmente contra ella, no solo contra TABLA, por
#: test_velo_x_fin_coincide_con_el_inicio_de_la_arena en
#: tests/test_efectos_venado.py). Derivado de TABLA por el mismo motivo que
#: VELO_X_INICIO.
VELO_X_FIN = TABLA[3].x_inicio


def alfa_de_niebla(x: float) -> int:
    """Alfa (0-``VELO_ALFA_MAX``) del velo de niebla del corredor en la
    columna de mundo ``x`` -- Tarea 8, B-046 (ver la nota larga arriba de
    este bloque para el porqué del rediseño).

    Perfil por tramos, todos derivados de ``tramos_venado.TABLA`` +
    constantes nombradas (nada mágico):

    - 0 para ``x <= VELO_X_INICIO`` (Actos 1-2, "El hogar"/"El abandono" --
      la niebla del Acto 3 todavía no se ve).
    - Rampa lineal 0 -> ``VELO_ALFA_MAX`` en
      ``[VELO_X_INICIO, VELO_X_INICIO + VELO_RAMPA_ENTRADA)`` -- la niebla
      se espesa según el jugador entra al Acto 3.
    - Sostenido en ``VELO_ALFA_MAX`` en
      ``[VELO_X_INICIO + VELO_RAMPA_ENTRADA, VELO_X_FIN - VELO_RAMPA_SALIDA]``
      -- el grueso del Acto 3, niebla llena.
    - Rampa lineal ``VELO_ALFA_MAX`` -> 0 en
      ``(VELO_X_FIN - VELO_RAMPA_SALIDA, VELO_X_FIN)`` -- la niebla se
      disipa al acercarse al suelo sagrado.
    - 0 para ``x >= VELO_X_FIN`` (Acto 4, la arena -- niebla completamente
      despejada; el beat dramático del cruce ("corte en seco") lo llevan el
      silencio + shake de la Tarea 6, ``_actualizar_silencio_y_shake_de_
      arena`` en boss_venado_scene.py, no este velo -- ver su docstring
      para cómo las dos piezas coinciden en el mismo umbral sin llamarse
      entre sí).

    Redondea con ``round()`` (no trunca): con los anchos elegidos (200/100,
    ambos múltiplos de 4 sobre ``VELO_ALFA_MAX=80``) el punto medio exacto de
    cada rampa cae en un entero exacto, sin ningún ``.5`` a mitad de camino
    que ``round()`` tuviera que desempatar -- la corrección de estilo aquí
    (revisión de calidad, 2026-08-25) es que la simetría subir/bajar NO la
    da ``round()``: la da que ``alfa_de_niebla`` sea una función PURA de
    ``x`` (misma fórmula evaluada en el punto simétrico da el mismo
    resultado, sea cual sea la regla de redondeo); ``round()`` solo evita la
    ambigüedad de ese ``.5`` en los anchos elegidos, nada más."""
    if x <= VELO_X_INICIO or x >= VELO_X_FIN:
        return 0
    if x < VELO_X_INICIO + VELO_RAMPA_ENTRADA:
        t = (x - VELO_X_INICIO) / VELO_RAMPA_ENTRADA
        return round(VELO_ALFA_MAX * t)
    if x > VELO_X_FIN - VELO_RAMPA_SALIDA:
        t = (VELO_X_FIN - x) / VELO_RAMPA_SALIDA
        return round(VELO_ALFA_MAX * t)
    return VELO_ALFA_MAX
