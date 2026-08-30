from __future__ import annotations

import math
import random
import weakref
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
import numpy as np

from src.engine.utils.math_utils import (
    clamp,
    ease_in_quad,
    ease_out_quad,
    lerp,
    vec2_distance,
    vec2_normalize,
)
from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.enemy_base import EnemyState
from src.framework.entities.boss_kit import (
    AttackScheduler,
    AttackTiming,
    BossAttack,
    SummonTracker,
    SummonWave,
)
from src.framework.processing.color_tools import ColorTools
from src.framework.processing.curve_tools import CurveTools
from src.framework.processing.filter_tools import FilterTools
from src.stages.stage2_4.rey_metad import CoordinadorDeMitades, ReyMetad

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class BossRey(BossBase):
    """
    El Rey Terciopelo — Evaluación Práctica I: solo Fase 1 ("La Marioneta").

    Movimiento: recorrido errático por Catmull-Rom sobre 4 posiciones del
    arena (la actual + 3 aleatorias), recalculado cada 0.3s.
    Ataque: VENOM_SPIT, un glob de veneno recto apuntado al jugador con
    vectores de math_utils.

    Las Fases 2 (división en ReyMetad) y 3 (frenesí) son Práctica II — no se
    implementan aquí (docs/17_BOSS_SPEC.md §4, CLAUDE.md).
    """

    # AUD-238 — el Rey concede el doble salto. Ver `boss_venado.py`, que hace
    # lo mismo con el dash: cada habilidad condicionable necesita al menos un
    # jefe que la suelte o encender el candado la vuelve inalcanzable.
    skill_drop = "skill_double_jump"

    #: Cuántos puntos de control aleatorios se suman a la posición actual
    #: para trazar la curva (spec: "4 random arena positions").
    RANDOM_POINTS = 3
    PATH_SAMPLES = 20
    PATH_RECALC_INTERVAL = 0.3
    #: No generar puntos de control pegados a las paredes del arena.
    ARENA_MARGIN = 24
    #: Velocidad de caminata de la Fase 1 (spec §4.3: 50 px/s). El
    #: `speed_multiplier` de la fase la escala.
    WALK_SPEED = 50.0
    #: Radio en el que se sortean los puntos de control, alrededor del jefe.
    #:
    #: Antes se sorteaban en TODO el ancho del arena. Con una sala de 542 px
    #: eso ponía puntos a cientos de píxeles y, como la curva se recorría
    #: entera en 0.3 s, el Rey se movía a ~900 px/s: no parecía errático,
    #: parecía teletransportarse. Acotar el radio conserva el nervio de la
    #: marioneta y devuelve la velocidad al terreno del spec.
    WANDER_RADIUS = 110.0
    #: Temblor vertical de la marioneta al caminar — el Rey no vuela, así que
    #: la Y se mantiene pegada al suelo con un jitter pequeño en vez de
    #: vagar por todo el alto del arena.
    FLOOR_JITTER = 5.0

    VENOM_SPIT_RANGE = 200.0
    VENOM_SPIT_COOLDOWN = 2.5
    VENOM_SPIT_SPEED = 90.0
    VENOM_SPIT_DAMAGE = 0.5

    #: BODY_SLAM (spec §4.3, Fase 1): la marioneta se abalanza 80px de golpe
    #: cuando el jugador se le acerca a menos de 64px. 1.0 corazón de daño.
    BODY_SLAM_RANGE = 64.0
    BODY_SLAM_LUNGE = 80.0
    BODY_SLAM_COOLDOWN = 4.0
    BODY_SLAM_DAMAGE = 1.0

    #: VENOM_BURST (spec §4.3, Fase 3): abanico de 5 globos cada 6s en los
    #: ángulos exactos del spec. 0.25 corazones cada uno.
    VENOM_BURST_ANGLES = (-30.0, -15.0, 0.0, 15.0, 30.0)
    VENOM_BURST_COOLDOWN = 6.0
    VENOM_BURST_DAMAGE = 0.25

    #: LUNGE (spec §4.3, Fase 3): carga de 160px a 350px/s cada 8s.
    LUNGE_DISTANCE = 160.0
    LUNGE_SPEED = 350.0
    LUNGE_COOLDOWN = 8.0
    LUNGE_DAMAGE = 1.25
    #: Duración que se deduce de los dos números del spec: 160/350 ≈ 0.457 s.
    #: Coincide con la ventana `active` del ataque, así que la carga termina
    #: justo cuando deja de golpear.
    LUNGE_DURATION = LUNGE_DISTANCE / LUNGE_SPEED

    #: Unidad VI — pausa tras herir al jugador. El Rey se detiene a «saborear»
    #: el golpe y reanuda con una rampa suavizada, no de golpe.
    SAVOUR_DURATION = 0.6

    # ── Unidad VII — «la visión del Rey» ───────────────────────────────
    #
    # El Rey es un cadáver animado por serpientes, y las víboras no cazan con
    # la vista. Aquí eso deja de ser adorno narrativo: cada pocos fotogramas
    # se mide con `FilterTools.compute_histogram` el brillo REAL de la zona de
    # pantalla donde está el jugador —con la iluminación, la niebla y las
    # lámparas ya dibujadas— y ese número gobierna dos cosas del combate.
    #
    #   Zona oscura  -> el Rey no fija bien al jugador: falla la puntería y
    #                   avanza con cautela. Su sprite se difumina.
    #   Zona clara   -> lectura limpia: apunta certero y se acerca decidido.
    #
    # Consecuencia de diseño: las lámparas del mapa pasan a ser mecánica.
    #: Lado en px del cuadrado que se muestrea alrededor del jugador.
    BRILLO_MUESTRA = 96
    #: Cada cuántos fotogramas se remuestrea (~0.4 s a 60 fps). Un histograma
    #: por fotograma sería tirar NumPy a la basura 60 veces por segundo.
    BRILLO_CADA_N_FRAMES = 24
    #: Error angular máximo del escupitajo con oscuridad total.
    PUNTERIA_ERROR_MAX = 18.0
    #: Velocidad de persecución en penumbra, como fracción de la normal.
    PERSECUCION_EN_PENUMBRA = 0.6
    #: Por debajo de este brillo el Rey se considera «a ciegas» y su sprite se
    #: difumina. Es también el umbral que cuantiza la caché de filtros.
    UMBRAL_PENUMBRA = 0.35
    #: Sigma del desenfoque cuando caza a ciegas.
    BLUR_SIGMA = 1.2

    #: Gravedad con la que el Rey devuelve al suelo a sus serpientes. Es la
    #: misma que usa el motor en su estado `LAUNCHED`, para que una serpiente
    #: golpeada caiga igual sea cual sea la fuerza del golpe. Ver
    #: `_asentar_serpientes`.
    GRAVEDAD_SERPIENTES = 600.0

    # ── SERPENT_CARPET: calibrado por playtest ─────────────────────────
    #
    # DESVIACIÓN DELIBERADA DEL SPEC, con el aval de la propia guía del curso.
    # El spec §4.3 pide 6 serpientes cada 10 s en Fase 1 y 12 en Fase 3. Al
    # jugarlo, con la arena de 542 px eso es un muro: la pelea deja de ser
    # contra el Rey y pasa a ser contra la alfombra. `66_GUIA §4.2` ya lo
    # anticipa —«carpet con demasiadas serpientes en fase 1 satura el
    # rendimiento y al jugador»— y `86_ESPEC §5` manda calibrar por playtest,
    # no por el número escrito.
    #
    # Tres cambios, los tres para que el jefe siga siendo el protagonista:
    #: Cuántas salen por oleada (spec: 6 / 12).
    SERPIENTES_POR_OLEADA = 2
    #: Tope de serpientes vivas a la vez, contando oleadas anteriores.
    SERPIENTES_EN_PANTALLA = 2
    #: Espera entre oleadas: hay que poder pelear con el Rey, no solo limpiar.
    SERPIENTES_COOLDOWN = 15.0
    #: Cuánto se separan las dos mitades al partirse el cuerpo.
    SEPARACION_MITADES = 70

    #: Vida por debajo de la cual el Rey empieza a invocar (de 15 máx.). No
    #: gasta serpientes en el primer contacto: primero mide al jugador.
    SERPIENTES_DESDE = 12.0

    # ── Unidad IX — subtipos de la Fase 3 ──────────────────────────────
    #
    # Spec §4.3: «los subtipos se detectan, no se anuncian». En el frenesí el
    # Rey alterna entre tres modos cada 8–15 s y **nada en el HUD lo dice**:
    # el jugador tiene que deducirlo observando qué hace. Es el examen de
    # reconocimiento de patrones de la Unidad IX.
    #
    # Cada subtipo cambia cosas observables —cadencia, alcance, velocidad—
    # para que haya algo que leer. Si los tres se jugaran igual, no habría
    # patrón que reconocer y la mecánica sería decorativa.
    SUBTIPO_AGRESIVO = "AGGRESSIVE"
    SUBTIPO_DISPERSO = "DISPERSED"
    SUBTIPO_DEFENSIVO = "DEFENSIVE"
    SUBTIPOS = (SUBTIPO_AGRESIVO, SUBTIPO_DISPERSO, SUBTIPO_DEFENSIVO)
    #: Ventana de permanencia de cada subtipo, en segundos (spec: 8–15 s).
    SUBTIPO_MIN_SEG = 8.0
    SUBTIPO_MAX_SEG = 15.0
    #: Cómo se comporta cada subtipo. `cadencia` multiplica los enfriamientos
    #: (menor = ataca más seguido) y `avance` la velocidad de persecución.
    SUBTIPO_PERFIL: dict[str, dict[str, float]] = {
        SUBTIPO_AGRESIVO: {"cadencia": 0.6, "avance": 1.3},   # carga y acosa
        SUBTIPO_DISPERSO: {"cadencia": 1.0, "avance": 0.8},   # suelta serpientes
        SUBTIPO_DEFENSIVO: {"cadencia": 1.4, "avance": 0.5},  # aguanta a distancia
    }

    #: Persecución en línea recta de la Fase 3 (spec: 130 px/s).
    PURSUIT_SPEED = 130.0

    #: Índices de fase, para no repartir números mágicos por el código.
    PHASE_MARIONETA = 0
    PHASE_DIVISION = 1
    PHASE_FRENESI = 2

    #: Unidad V — tinte venenoso por fase (`ColorTools.apply_tint`).
    #:
    #: `apply_tint` MULTIPLICA cada canal por `color/255`, así que solo puede
    #: oscurecer: un canal en 255 se queda igual y uno en 0 desaparece.
    #:
    #: DESVIACIÓN DELIBERADA DEL SPEC, y por qué. El spec §4.3 pide
    #: literalmente `(30, 80, 0)`, que son factores 0.12 / 0.31 / 0.00. Ese
    #: valor asume un sprite claro; sobre el hueso y la carne del Rey deja un
    #: verde casi negro, y jugándolo el jefe se veía como una mancha oscura
    #: sin silueta legible. Un jefe que no se distingue del fondo no es una
    #: decisión estética, es un defecto de jugabilidad.
    #:
    #: Se conservan la intención y la progresión —verde venenoso que se
    #: enciende conforme las serpientes toman el cuerpo— con factores que
    #: dejan ver de qué está hecho. Sobre el hueso (232, 226, 205):
    #:
    #:     Fase 1 -> (100, 177,  72)   cadáver verdoso
    #:     Fase 2 -> (127, 204,  97)   las serpientes asoman
    #:     Fase 3 -> (159, 226, 117)   veneno puro
    # ── Animación ──────────────────────────────────────────────

    #: Ataques que usan la hoja `spit`. Son los dos de veneno; `BODY_SLAM` y
    #: `LUNGE` son embestidas con el cuerpo y siguen con la hoja de caminar,
    #: que es lo que de verdad hacen: lanzarse hacia el jugador.
    ATAQUES_DE_ESCUPIR: frozenset[str] = frozenset({"VENOM_SPIT", "VENOM_BURST"})

    #: `EnemyBase._ANIM_FPS` no conoce `spit` ni `death` —sus claves son las
    #: del enemigo común (`die`, no `death`)— así que ambas caían al valor por
    #: defecto de 10 fps. La muerte se baja a 8: son cuatro fotogramas de un
    #: cuerpo deshaciéndose en serpientes y a 10 fps pasaba demasiado rápido
    #: para leerse. `spit` no se lista porque no la gobierna un reloj, sino el
    #: propio aviso del ataque (ver `_advance_animation`).
    _ANIM_FPS: dict[str, float] = {
        "walk": 10.0, "fly": 12.0, "shoot": 16.0,
        "hurt": 12.0, "die": 10.0, "death": 8.0,
    }

    PHASE_TINTS: dict[int, tuple[int, int, int]] = {
        PHASE_MARIONETA: (110, 200, 90),
        PHASE_DIVISION: (140, 230, 120),
        PHASE_FRENESI: (175, 255, 145),   # el verde ya no se atenúa
    }

    @property
    def _floor_y(self) -> float:
        """Y de la cabeza del jefe para que sus pies queden sobre el suelo.

        `floor_surface_y` es la fuente preferida: la escena la toma del
        rectángulo de colisión "Floor" del TMX, que es el suelo de verdad.
        Antes esto se derivaba de `arena_bounds`, pero desde que
        `arena_bounds` es el rect del `CameraLock` (para encerrar al jefe en
        su sala) el jefe flotaba: la altura a la que camina no tiene por qué
        depender de dónde esté encuadrada la cámara, y al arrastrar el
        CameraLock en Tiled el borde inferior cayó en 592.0, que `pygame.Rect`
        trunca a 591 y desalinea los pies un píxel.

        El cálculo por `arena_bounds` queda como respaldo para cuando la
        escena no informa el suelo (por ejemplo en pruebas unitarias).
        """
        if self.floor_surface_y is not None:
            return float(self.floor_surface_y - self.rect.height)
        if self.arena_bounds is None:
            return self.position.y
        return float(self.arena_bounds.bottom - 16 - self.rect.height)

    def __init__(self, spawn_position: pygame.Vector2) -> None:
        # Las tres fases del spec §4.3. `health_threshold[i]` es la vida
        # MÁXIMA de la fase i, no el punto de corte: `BossBase` salta a la
        # fase i+1 cuando la vida baja de `threshold[i+1]` y entonces fija
        # `_phase_max_health = threshold[i+1]`. Por eso el primer umbral vale
        # lo mismo que `max_health`, igual que en el jefe de referencia
        # (`boss_venado`: max_health=12 con umbrales [12, 6]).
        #
        #   Fase 1 «La Marioneta» 15 → 10   |  Fase 2 «La División» 10 → 4
        #   Fase 3 «El Frenesí»    4 → 0
        phases = [
            BossPhase(
                phase_index=0,
                health_threshold=15.0,
                attack_patterns=["VENOM_SPIT", "BODY_SLAM"],
                movement_type="random_walk",
                speed_multiplier=1.0,
            ),
            BossPhase(
                phase_index=1,
                health_threshold=10.0,
                attack_patterns=["VENOM_SPIT", "BODY_SLAM"],
                movement_type="bezier",
                speed_multiplier=1.6,
            ),
            BossPhase(
                phase_index=2,
                health_threshold=4.0,
                attack_patterns=["VENOM_BURST", "LUNGE"],
                movement_type="pursuit",
                speed_multiplier=2.6,
            ),
        ]
        super().__init__(
            spawn_position=spawn_position,
            max_health=15.0,
            damage_on_contact=0.5,
        )
        self.set_boss_name("REY TERCIOPELO")

        # Hurtbox exacta del spec (28x48). El hitbox se deriva con la misma
        # proporción que usa boss_venado.py entre su sprite (48x48) y su
        # hitbox (36x44) aplicada al sprite de Fase 1 del Rey (40x56).
        self.rect.width = 30
        self.rect.height = 50
        self.position.y -= self.rect.height
        self.rect.y = int(self.position.y)

        # Los sprites propios viven junto al mapa, en `assets/maps/stage2_4/`,
        # y no en `assets/sprites/bosses/`: esa carpeta es común a todos los
        # jefes y no me corresponde. `_load_boss_sprites` acepta `base_dir`
        # justo para esto.
        self._load_boss_sprites(
            "boss_rey", 40, 56,
            sheets={
                "walk": (40, 56),
                "spit": (40, 56),
                "hurt": (40, 56),
                "death": (40, 56),
            },
            base_dir=str(settings.ASSETS_DIR / "maps/stage2_4"),
        )
        self.set_phases(phases)

        # Telegrafiado: lo lleva `AttackScheduler`, no temporizadores propios.
        #
        # El planificador recorre por cada ataque el ciclo WINDUP → ACTIVE →
        # RECOVER y llama a `on_attack_fired` justo al entrar en ACTIVE. Eso
        # da tres cosas gratis: el aviso que el jugador puede leer
        # (`telegraph_progress`, 0→1 durante el windup, que el HUD dibuja), la
        # ventana de castigo al terminar (`is_vulnerable`) y los enfriamientos.
        # Mantener aquí un diccionario de cooldowns en paralelo sería tener dos
        # relojes gobernando el mismo ataque, y cuál gana dependería del orden
        # de llamadas.
        #
        # `windup` nunca baja de MIN_READABLE_WINDUP (0.35 s): por debajo el
        # aviso no se alcanza a leer y el ataque se vuelve injusto. Los
        # ataques más dañinos avisan más — LUNGE (1.25 corazones) da 0.9 s.
        self.attacks = AttackScheduler([
            BossAttack(
                "VENOM_SPIT", windup=0.5, active=0.2, recover=0.6,
                damage=self.VENOM_SPIT_DAMAGE, reach=self.VENOM_SPIT_RANGE,
                max_range=self.VENOM_SPIT_RANGE, cooldown=self.VENOM_SPIT_COOLDOWN,
                phases=(self.PHASE_MARIONETA, self.PHASE_DIVISION),
            ),
            BossAttack(
                "BODY_SLAM", windup=0.45, active=0.25, recover=0.8,
                damage=self.BODY_SLAM_DAMAGE, reach=self.BODY_SLAM_RANGE,
                max_range=self.BODY_SLAM_RANGE, cooldown=self.BODY_SLAM_COOLDOWN,
                phases=(self.PHASE_MARIONETA, self.PHASE_DIVISION),
            ),
            BossAttack(
                "VENOM_BURST", windup=0.8, active=0.25, recover=0.9,
                damage=self.VENOM_BURST_DAMAGE, reach=self.VENOM_SPIT_RANGE,
                cooldown=self.VENOM_BURST_COOLDOWN,
                phases=(self.PHASE_FRENESI,),
            ),
            BossAttack(
                "LUNGE", windup=0.9, active=0.45, recover=1.1,
                damage=self.LUNGE_DAMAGE, reach=self.LUNGE_DISTANCE,
                cooldown=self.LUNGE_COOLDOWN,
                phases=(self.PHASE_FRENESI,),
            ),
        ])

        # ── Invocaciones (spec §4.3) ───────────────────────────────────
        #
        # Las lleva `SummonTracker`, que `BossBase` ya conduce: mide los
        # enfriamientos, purga a los muertos y respeta el tope de población.
        # El tope no es una optimización — es diseño: sin él un jefe que
        # invoca cada N segundos llena la pantalla y el encuentro deja de ser
        # sobre el jefe.
        #
        # `SERPENT_CARPET` (Fase 1) y `SERPENT_WAVE` (Fase 3) son la misma
        # especie con distinta intensidad: 6 serpientes cada 10 s frente a 12
        # cada 12 s. La guía de diseño avisa de que más de 6 en Fase 1 satura
        # al jugador, así que el salto a 12 llega cuando ya sabe leerlas.
        # Las oleadas NO se registran todavía: el Rey no invoca hasta que le
        # han hecho daño (ver `_armar_serpientes_si_toca`). Se guardan aparte
        # y se dan de alta cuando toca.
        self.summons = SummonTracker(waves=[])
        self._oleadas_serpiente = (
            SummonWave(
                species_id="WalkerSerpientePequena",
                count=self.SERPIENTES_POR_OLEADA,
                max_alive=self.SERPIENTES_EN_PANTALLA,
                cooldown=self.SERPIENTES_COOLDOWN,
                phases=(self.PHASE_MARIONETA, self.PHASE_DIVISION),
                # Solo importa el reparto horizontal: la Y la corrige
                # `take_summons`, que es donde se conoce el suelo real.
                spawn_offsets=((-72, 0), (72, 0)),
            ),
            SummonWave(
                species_id="WalkerSerpientePequena",
                count=self.SERPIENTES_POR_OLEADA,
                max_alive=self.SERPIENTES_EN_PANTALLA,
                # En el frenesí vuelven antes, pero nunca son más a la vez:
                # la fase sube la presión, no el número de cuerpos.
                cooldown=self.SERPIENTES_COOLDOWN * 0.7,
                phases=(self.PHASE_FRENESI,),
                spawn_offsets=((-140, 0), (140, 0)),
            ),
        )

        #: Y de la superficie transitable, que la escena fija leyendo el
        #: rect de colisión "Floor" del TMX. `None` hasta entonces: ver
        #: `_floor_y` para el respaldo.
        self.floor_surface_y: float | None = None

        self._path_points: list[tuple[float, float]] = []
        self._path_timer: float = 0.0
        #: Largo de la ruta actual y cuánto lleva recorrido, para avanzar por
        #: distancia y no por tiempo normalizado (ver `_update_movement`).
        self._path_largo: float = 0.0
        self._path_avance: float = 0.0

        #: Estado de la carga de la Fase 3. `_lunge_t` va de 0 a 1 y la curva
        #: de easing lo convierte en distancia recorrida (ver `_advance_lunge`).
        #: Los enfriamientos NO viven aquí: los lleva `self.attacks`.
        self._lunge_t: float = 1.0          # 1.0 = sin carga en curso
        self._lunge_origen_x: float = 0.0
        self._lunge_direction: float = 1.0
        #: Pausa tras herir al jugador (Unidad VI).
        self._savouring: bool = False
        self._savour_t: float = 0.0
        #: Última fase vista, para detectar el flanco en `_detect_phase_change`.
        self._last_phase: int = 0
        #: Fotogramas ya teñidos, por (superficie original, fase). Ver
        #: `_tenir_fase` para por qué la clave es la superficie y no su `id`.
        self._tint_cache: dict[tuple[pygame.Surface, int], pygame.Surface] = {}
        #: Fotogramas ya filtrados (Unidad VII), por (superficie teñida, efecto).
        self._filter_cache: dict[tuple[pygame.Surface, str], pygame.Surface] = {}
        #: Brillo leído del escenario alrededor del jugador, 0..1. Arranca en
        #: 1.0 —a plena luz— para que el Rey no empiece la pelea cegado antes
        #: de haber medido nada.
        self._brillo_leido: float = 1.0
        self._brillo_frame: int = 0
        #: Serpientes invocadas vivas, como [referencia_débil, velocidad_caída].
        #: Ver `_asentar_serpientes`: el motor las deja flotando tras un golpe.
        self._serpientes: list[list[Any]] = []
        #: Velocidad de caída del propio Rey. Ver `_asentar_rey`: los golpes
        #: lo empujan hacia arriba y el motor nunca lo baja.
        self._caida_rey: float = 0.0
        #: Las dos mitades vivas de la Fase 2. Vacío = no está partido.
        self._mitades: list[Any] = []
        #: ¿Corrió el movimiento propio del Rey este fotograma? Lo usa
        #: `_asentar_rey` para no pisar el temblor de la curva.
        self._movio_este_frame: bool = False
        #: Clave de animación del fotograma anterior. Sirve para reiniciar
        #: el contador al cambiar de hoja: ver `_advance_animation`.
        self._animacion_previa: str = "walk"
        #: Subtipo del frenesí (Unidad IX) y lo que le queda activo.
        self._subtipo: str = self.SUBTIPO_AGRESIVO
        self._subtipo_restante: float = 0.0
        #: Enfriamientos declarados de cada ataque, para que la cadencia del
        #: subtipo se calcule siempre desde el valor del spec.
        self._COOLDOWNS_BASE: dict[str, float] = {
            a.name: a.cooldown for a in self.attacks._attacks
        }
        self._projectiles: list[dict[str, Any]] = []

    def _patrol_behavior(self, dt: float) -> None:
        self._update_movement(dt)

    def _alert_behavior(self, dt: float) -> None:
        # El cambio de fase y las invocaciones se atienden en `update()`, que
        # corre en todos los estados. Aquí solo queda el comportamiento.
        self._actualizar_subtipo(dt)
        self._aplicar_cadencia_de_subtipo()
        # Durante el aviso el Rey se planta: si siguiera vagando por la curva
        # mientras telegrafía, el jugador no podría saber desde dónde le va a
        # llegar el golpe y el aviso dejaría de servir.
        #
        # El saboreo escala el `dt` del movimiento en vez de la posición: así
        # la curva no se recalcula ni salta, solo se recorre más despacio.
        if self.attack_timing != AttackTiming.WINDUP:
            self._update_movement(dt * self._factor_de_saboreo(dt))
        self._advance_lunge(dt)

    def on_attack_fired(self, attack_name: str) -> None:
        """Terminó el aviso: ejecuta el golpe.

        Gancho de `BossBase`, invocado una sola vez al pasar de WINDUP a
        ACTIVE. Aquí no se comprueban rangos ni enfriamientos: el
        planificador ya decidió que el ataque tocaba y el jugador ya vio
        venir el aviso.
        """
        if attack_name == "VENOM_SPIT":
            self._do_venom_spit()
        elif attack_name == "BODY_SLAM":
            self._do_body_slam()
        elif attack_name == "VENOM_BURST":
            self._do_venom_burst()
        elif attack_name == "LUNGE":
            self._do_lunge()

    # ── Fases (spec §4.3) ──────────────────────────────────────────────

    def _detect_phase_change(self) -> None:
        """Reacciona al primer fotograma de cada fase nueva.

        `BossBase` ya gestiona la transición (invencibilidad, temporizador,
        `speed_multiplier` y el evento `BOSS_PHASE_CHANGED`), así que aquí
        no se reimplementa nada de eso: solo se detecta el flanco para
        limpiar los enfriamientos —entrar a una fase nueva no debe heredar
        el enfriamiento a medias de la anterior— y anunciar el cambio.
        """
        if self.current_phase == self._last_phase:
            return
        self._last_phase = self.current_phase
        # `BossBase._finish_phase_transition` ya llama a `attacks.interrupt()`,
        # así que los enfriamientos del planificador no se tocan aquí. Solo se
        # cancela lo que es estado propio del Rey: la carga a medio recorrer,
        # el saboreo pendiente y el trazado de la curva, que pertenece a la
        # fase que acaba de morir.
        self._lunge_t = 1.0          # 1.0 = carga terminada
        self._savouring = False
        self._path_points = []

        # El anuncio del cambio de fase ya lo hace `BossBase`
        # (`BOSS_PHASE_CHANGED`, `SFX_BOSS_PHASE_CHANGE`, `VFX_ULTIMATE`…),
        # así que aquí no se re-emite nada genérico. Lo único que falta es el
        # sonido propio del Rey al partirse en dos.
        if self.current_phase == self.PHASE_DIVISION:
            self._event_bus.emit(Events.SFX_BOSSES_REY_SPLIT)
            self._partirse()

    def _get_animation_key(self) -> str:
        """Qué hoja toca en los estados que no son `HURT` ni `DYING`.

        Esos dos ya los resuelve `BossBase._get_animation_state` antes de
        llamar aquí, así que este método solo decide entre caminar y escupir.

        Antes devolvía `"walk"` siempre: las tres hojas restantes se cargaban
        en memoria y `spit` no se dibujaba **nunca**. El jefe escupía veneno
        con la misma pose con la que patrulla, así que el aviso del ataque
        dependía por completo del realce por convolución. Ahora la pose es la
        primera señal y el filtro la refuerza.
        """
        actual = self.attacks.current
        if (
            actual is not None
            and actual.name in self.ATAQUES_DE_ESCUPIR
            and self.attack_timing in (AttackTiming.WINDUP, AttackTiming.ACTIVE)
        ):
            return "spit"
        return "walk"

    def _advance_animation(self, dt: float) -> None:
        """Tres correcciones sobre el avance del motor.

        **1. Reiniciar al cambiar de hoja.** `_animation_frame` es un único
        contador compartido por todas las animaciones y el motor no lo pone a
        cero al cambiar de clave. Pasar de `walk` (4 fotogramas) a `spit` (3)
        entraba a mitad de la animación; `draw` lo recorta con `min(...)`, así
        que no reventaba, pero el escupitajo empezaba por el final. Una
        transición que arranca donde terminó la anterior no se lee como
        transición.

        **2. La muerte no se repite.** El motor avanza con
        `(frame + 1) % len(frames)`, que es correcto para un ciclo de caminar
        y absurdo para morirse: el Rey se deshacía en serpientes y volvía a
        recomponerse en bucle. Se congela en el último fotograma.

        **3. El escupitajo va con el ataque, no con un reloj propio.** A fps
        fijos la animación y el ataque son dos relojes independientes y la
        pose que acompaña al disparo sale distinta cada vez. Aquí el
        fotograma se deriva de `telegraph_progress`, así que los dos primeros
        cuentan el aviso y el último cae **exactamente** cuando el ataque
        entra en `ACTIVE` y sale el proyectil. Eso es lo que hace legible el
        aviso: la pose dice cuánto falta.
        """
        clave = self._get_animation_state()
        if clave != self._animacion_previa:
            self._animacion_previa = clave
            self._animation_frame = 0
            self._animation_timer = 0.0

        fotogramas = self._sprite_frames.get(clave)
        if not fotogramas:
            super()._advance_animation(dt)
            return

        if clave == "death":
            if self._animation_frame >= len(fotogramas) - 1:
                self._animation_frame = len(fotogramas) - 1
                return
            super()._advance_animation(dt)
            return

        if clave == "spit":
            self._animation_frame = self._fotograma_de_escupir(len(fotogramas))
            return

        super()._advance_animation(dt)

    def _fotograma_de_escupir(self, total: int) -> int:
        """Reparte la hoja `spit` a lo largo del ataque.

        El aviso ocupa todos los fotogramas menos el último, que queda
        reservado para el instante del disparo. Con las tres poses de la hoja:
        0 y 1 son el Rey tomando aire, y 2 es el veneno saliendo.
        """
        if self.attack_timing == AttackTiming.WINDUP:
            avance = clamp(self.telegraph_progress, 0.0, 1.0)
            return min(int(avance * (total - 1)), total - 2)
        return total - 1

    # ── Fase 2: la división en dos ReyMetad (spec §4.3) ────────────────

    def _partirse(self) -> None:
        """El cuerpo se abre y salen las dos mitades.

        El Rey no muere ni desaparece del combate: se vuelve invisible e
        invulnerable mientras las serpientes pelean por él. Es lo que dice el
        spec —«el cuerpo se parte en dos ReyMetad»— y además resuelve un
        problema práctico: si el Rey siguiera golpeable, el jugador podría
        saltarse la fase entera pegándole a él en vez de a las mitades.

        Las mitades salen por `pending_summons`, el mismo canal que las
        serpientes: la escena las recoge en `take_summons` y les cablea el
        bus, el jugador y las colisiones. El jefe nunca toca la escena.
        """
        if self._mitades:
            return                      # ya está partido
        centro = self.rect.centerx
        coordinador = CoordinadorDeMitades()
        for lado in (-1, 1):
            mitad = ReyMetad(
                pygame.Vector2(centro + lado * self.SEPARACION_MITADES,
                               self.position.y + self.rect.height),
                lado=lado,
                coordinador=coordinador,
            )
            self._mitades.append(mitad)
            self.pending_summons.append(mitad)

        self.is_visible = False
        self._invincibility_timer = float("inf")
        self._event_bus.emit(
            Events.VFX_ULTIMATE, pos=(self.position.x, self.position.y - 20),
        )

    def _vigilar_mitades(self) -> None:
        """Cuando caen las dos, el Rey se rearma y arranca «El Frenesí».

        Spec §4.3: «cuando ambos ReyMetad llegan a 0, disparan
        BOSS_PHASE_CHANGED y empieza la Fase 3». Aquí eso se traduce en bajar
        la vida del Rey al umbral de la Fase 3 y pedirle al framework que
        compruebe la transición — la misma llamada que hace `apply_hit`, para
        no inventar un camino paralelo al del motor.
        """
        if not self._mitades or self.current_phase != self.PHASE_DIVISION:
            return

        vivas = [m for m in self._mitades if m.is_alive]
        if vivas:
            # Si solo queda una, se le avisa: sin compañera con quien turnarse
            # el reparto de turnos deja de tener sentido y se enfurece.
            if len(vivas) == 1:
                vivas[0].quedarse_sola()
            return

        self._mitades.clear()
        self.is_visible = True
        self._invincibility_timer = 0.0
        # Justo por debajo del umbral de la Fase 3, para que la comprobación
        # del framework la dispare.
        umbral = self.phase_health_thresholds[self.PHASE_FRENESI]
        self.current_health = min(self.current_health, umbral - 0.1)
        self._check_phase_transition()

    def _update_encounter(self, dt: float) -> None:
        """Mientras el Rey está partido, no pelea él: pelean sus mitades.

        `is_visible = False` **solo apaga el dibujo**. `BossBase.draw` es el
        único sitio del motor que consulta esa bandera (`boss_base.py:640`),
        así que el planificador de ataques y las invocaciones seguían
        corriendo con el Rey borrado de la pantalla. Medido en 20 s de Fase 2:

            5 x VENOM_SPIT  +  4 x BODY_SLAM  disparados por un jefe invisible

        Eso rompe la regla que sostiene el resto de la pelea: todo golpe se
        telegrafía para que se pueda leer y esquivar. Un aviso que no se
        dibuja no es un aviso, y encima el jugador no puede castigarlo porque
        el Rey está invulnerable. Le llega daño de la nada.

        Se corta con el mismo gesto que usa el motor para un jefe aturdido
        —`attacks.interrupt()` y salir—, no inventando un camino nuevo.
        `summons.update(dt)` se llama antes de salir para que los
        enfriamientos de las oleadas sigan descontando: al rearmarse el Rey
        debe seguir el ritmo de la pelea, no arrancar con todo en cooldown.
        """
        if self._mitades:
            self.summons.update(dt)
            self.attacks.interrupt()
            return
        super()._update_encounter(dt)

    def _armar_serpientes_si_toca(self) -> None:
        """Da de alta las oleadas cuando el Rey ya ha recibido daño.

        El `SummonTracker` no sabe de vida, solo de fase y enfriamiento, así
        que la puerta se pone aquí: las oleadas no están registradas hasta
        que la vida baja de `SERPIENTES_DESDE`.

        Es diseño, no ahorro: el primer tramo de la pelea sirve para que el
        jugador aprenda a leer al Rey. Meterle serpientes desde el primer
        segundo tapa justo lo que tiene que aprender, y el spec no pide que
        invoque de entrada — pide que invoque «cada 10 s», sin decir desde
        cuándo.
        """
        if self.summons.waves or self.current_health > self.SERPIENTES_DESDE:
            return
        self.summons.waves = list(self._oleadas_serpiente)

    def take_summons(self) -> list[Any]:
        """Entrega las serpientes ya asentadas en el suelo y dentro del arena.

        `SummonTracker.spawn` las coloca en `boss.position + offset`, y
        `position` es la **cabeza** del jefe, no sus pies: con el Rey en
        y=526 y el suelo en 576, las serpientes nacían 58 px en el aire.
        Caían, caminaban y las que llegaban al borde acababan trepadas al
        techo sin poder bajar.

        El offset del `SummonWave` no puede arreglarlo por sí solo: es un
        valor fijo declarado en `__init__`, y ni el alto del suelo ni el de
        la serpiente se conocen entonces. Aquí sí: se apoya cada una sobre
        `floor_surface_y` y se la mete dentro del arena antes de entregarla.
        """
        invocadas = super().take_summons()
        if not invocadas:
            return invocadas

        for bicho in invocadas:
            # Las mitades heredan la arena del Rey: pelean donde él pelea.
            if isinstance(bicho, ReyMetad):
                if self.arena_bounds is not None:
                    bicho.set_arena_bounds(self.arena_bounds)
                bicho.floor_surface_y = self.floor_surface_y
            # Se guarda una referencia DÉBIL: la dueña de la serpiente es la
            # escena. Si la mata y la retira, esta lista no debe impedir que
            # el recolector se la lleve.
            self._serpientes.append([weakref.ref(bicho), 0.0])
            if self.floor_surface_y is not None:
                # `position.y` es el borde SUPERIOR: para apoyar los pies hay
                # que restar el alto del propio bicho.
                bicho.position.y = float(self.floor_surface_y - bicho.rect.height)
                bicho.rect.y = int(bicho.position.y)
            if self.arena_bounds is not None:
                izq = self.arena_bounds.left + self.ARENA_MARGIN
                der = self.arena_bounds.right - self.ARENA_MARGIN - bicho.rect.width
                if der >= izq:
                    bicho.position.x = clamp(bicho.position.x, izq, der)
                    bicho.rect.x = int(bicho.position.x)
        return invocadas

    # ── Unidad IX: subtipos que se detectan, no se anuncian ────────────

    @property
    def subtipo(self) -> str | None:
        """Subtipo activo, o `None` fuera de la Fase 3."""
        if self.current_phase != self.PHASE_FRENESI:
            return None
        return self._subtipo

    def _actualizar_subtipo(self, dt: float) -> None:
        """Rota el subtipo del frenesí cada 8–15 s (spec §4.3).

        El cambio **no se anuncia**: ni evento, ni sonido, ni aviso en el HUD.
        El jugador solo puede notarlo por cómo cambia el comportamiento, que
        es exactamente lo que la Unidad IX pide reconocer.

        La duración es aleatoria dentro de la ventana del spec a propósito: un
        periodo fijo se aprendería contando segundos en vez de leyendo al
        jefe, y eso no es reconocer un patrón, es mirar el reloj.
        """
        if self.current_phase != self.PHASE_FRENESI:
            return
        self._subtipo_restante -= dt
        if self._subtipo_restante > 0.0:
            return
        # No repetir el mismo subtipo dos veces seguidas: si se repite, el
        # jugador no puede distinguir «cambió» de «leí mal».
        opciones = [s for s in self.SUBTIPOS if s != self._subtipo]
        self._subtipo = random.choice(opciones)
        self._subtipo_restante = random.uniform(
            self.SUBTIPO_MIN_SEG, self.SUBTIPO_MAX_SEG,
        )

    def _perfil_subtipo(self, campo: str) -> float:
        """Multiplicador del subtipo activo, o 1.0 si no hay ninguno."""
        activo = self.subtipo
        if activo is None:
            return 1.0
        return self.SUBTIPO_PERFIL[activo][campo]

    def _aplicar_cadencia_de_subtipo(self) -> None:
        """Reescala los enfriamientos de los ataques del frenesí.

        El planificador es el dueño de los tiempos, así que en vez de llevar
        un reloj paralelo se ajustan sus propios `cooldown` a partir de los
        valores del spec. Se recalcula desde `_COOLDOWNS_BASE` y no sobre el
        valor actual, porque multiplicar repetidamente lo que ya está
        multiplicado los haría crecer sin tope en pocos segundos.
        """
        factor = self._perfil_subtipo("cadencia")
        for ataque in self.attacks._attacks:
            base = self._COOLDOWNS_BASE.get(ataque.name)
            if base is not None:
                ataque.cooldown = base * factor

    # ── Unidad VII: el histograma dirige la cacería ────────────────────

    @property
    def oscuridad(self) -> float:
        """Cuánto le cuesta al Rey fijar al jugador: 0 = a plena luz, 1 = ciego."""
        return 1.0 - self._brillo_leido

    def _leer_brillo(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        """Mide el brillo alrededor del jugador con `compute_histogram`.

        Se llama desde `draw()` y no desde `update()` a propósito: aquí el
        fondo, el terreno, las lámparas y la niebla YA están dibujados, así
        que lo que se mide es lo que el jugador realmente ve. Medido en
        `update()` habría que reconstruir la iluminación a mano y sería otra
        copia del motor que se queda vieja.

        El brillo sale del histograma de luminancia, no del array de píxeles:
        es la media ponderada de los 256 cubos, normalizada a 0..1.

            brillo = Σ i·luminancia[i] / (255 · total_píxeles)
        """
        self._brillo_frame += 1
        if self._brillo_frame % self.BRILLO_CADA_N_FRAMES != 0:
            return
        if self._player_ref is None:
            return

        lado = self.BRILLO_MUESTRA
        zona = pygame.Rect(0, 0, lado, lado)
        zona.center = (
            int(self._player_ref.centerx - camera_offset.x),
            int(self._player_ref.centery - camera_offset.y),
        )
        zona = zona.clip(surface.get_rect())
        if zona.width < 8 or zona.height < 8:
            return          # el jugador está fuera de cuadro: no se remuestrea

        hist = FilterTools.compute_histogram(surface.subsurface(zona))
        total = int(hist["total_pixels"])
        if total <= 0:
            return
        lum = np.asarray(hist["luminance"], dtype=np.float64)
        media = float((np.arange(256) * lum).sum() / total)
        self._brillo_leido = clamp(media / 255.0, 0.0, 1.0)

    # ── Unidad V: tinte venenoso (ColorTools) ──────────────────────────

    def _apply_filter(self, frame: pygame.Surface) -> pygame.Surface:
        """Pila de filtros del sprite, en el orden en que se leen.

        Gancho de `BossBase`, invocado desde `draw()` con el fotograma ya
        elegido y volteado.

          1. Tinte de la fase (Unidad V) — siempre.
          2. Realce por convolución si está avisando (Unidad VII): el aviso
             tiene que destacar por encima de todo lo demás.
          3. Desenfoque gaussiano si caza a ciegas (Unidad VII): el Rey se
             vuelve difícil de leer justo cuando también falla la puntería,
             así el efecto visual y el mecánico dicen lo mismo.
          4. `filter_effect` de la fase, que aporta la clase base.

        El aviso gana al desenfoque a propósito: si el Rey estuviera borroso
        mientras telegrafía, el jugador no podría leer el ataque y la pelea
        dejaría de ser justa.
        """
        frame = self._tenir_fase(frame)
        if self.attack_timing == AttackTiming.WINDUP:
            frame = self._filtrar_cacheado(frame, "realce")
        elif self._brillo_leido < self.UMBRAL_PENUMBRA:
            frame = self._filtrar_cacheado(frame, "penumbra")
        return super()._apply_filter(frame)

    #: Kernel de realce (Unidad VII). Suma 1, así que no cambia el brillo
    #: medio: solo sube el contraste local — resta a los cuatro vecinos y lo
    #: devuelve al centro, marcando los bordes del sprite.
    #:
    #:      [  0  -1   0 ]
    #:      [ -1   5  -1 ]
    #:      [  0  -1   0 ]
    KERNEL_REALCE = "sharpen"

    def _filtrar_cacheado(
        self,
        frame: pygame.Surface,
        efecto: str,
    ) -> pygame.Surface:
        """Aplica un filtro de Unidad VII, con caché por (fotograma, efecto).

        Igual que el tinte: la entrada es un sprite fijo y el resultado no
        cambia, así que convolucionar en cada `draw()` sería repetir el mismo
        cálculo 60 veces por segundo. Se cachea por la superficie ya teñida.
        """
        clave = (frame, efecto)
        salida = self._filter_cache.get(clave)
        if salida is not None:
            return salida
        if efecto == "realce":
            kernel = FilterTools.get_standard_kernel(self.KERNEL_REALCE)
            salida = self._conservando_alfa(
                frame, lambda s: FilterTools.apply_kernel(s, kernel),
            )
        else:
            salida = self._conservando_alfa(
                frame, lambda s: FilterTools.gaussian_blur(s, self.BLUR_SIGMA),
            )
        self._filter_cache[clave] = salida
        return salida

    def _tenir_fase(self, frame: pygame.Surface) -> pygame.Surface:
        """Aplica el tinte de la fase actual, con caché.

        El tinte de una fase no cambia y los fotogramas del sprite son fijos,
        así que teñir en cada `draw()` sería repetir una ida y vuelta a NumPy
        60 veces por segundo para obtener siempre lo mismo. Se calcula una vez
        por (fotograma, fase) y se reutiliza.

        La clave es la superficie misma, no su `id()`: guardar la referencia
        impide que el recolector libere el fotograma y reasigne ese `id` a
        otro objeto, que daría un acierto de caché falso.
        """
        color = self.PHASE_TINTS.get(self.current_phase)
        if color is None:
            return frame
        clave = (frame, self.current_phase)
        tenido = self._tint_cache.get(clave)
        if tenido is None:
            tenido = self._tenir_conservando_alfa(frame, color)
            self._tint_cache[clave] = tenido
        return tenido

    @staticmethod
    def _conservando_alfa(
        frame: pygame.Surface,
        operacion: Callable[[pygame.Surface], pygame.Surface],
    ) -> pygame.Surface:
        """Aplica una operación de imagen del framework sin perder el alfa.

        **Todas** las herramientas de imagen del curso reconstruyen la
        superficie con `pygame.surfarray.make_surface`, que solo copia RGB.
        Comprobado con las cuatro que usa este jefe:

            ColorTools.apply_tint      alfa perdido
            FilterTools.gaussian_blur  alfa perdido
            FilterTools.apply_kernel   alfa perdido
            FilterTools.sobel_edge     alfa perdido

        Un píxel `(0,0,0,0)` sale como `(0,0,0,255)`, así que aplicadas tal
        cual al sprite el Rey se dibujaría como un **rectángulo negro** con la
        figura dentro. Se guarda el alfa antes, se aplica la operación y se
        reinyecta después, dejando el color exactamente como lo calculó el
        framework.

        Nota sobre el desenfoque: se difumina el color pero **no** la silueta.
        Difuminar también el alfa sangraría fuera del rect del sprite, que es
        justo donde el motor recorta.
        """
        alfa = pygame.surfarray.array_alpha(frame).copy()
        salida = operacion(frame).convert_alpha()
        destino = pygame.surfarray.pixels_alpha(salida)
        destino[:] = alfa
        del destino          # libera el bloqueo de superficie que crea pixels_alpha
        return salida

    @classmethod
    def _tenir_conservando_alfa(
        cls,
        frame: pygame.Surface,
        color: tuple[int, int, int],
    ) -> pygame.Surface:
        """`ColorTools.apply_tint` (Unidad V) conservando la transparencia."""
        return cls._conservando_alfa(
            frame, lambda s: ColorTools.apply_tint(s, color),
        )

    def _build_hitbox(self) -> pygame.Rect:
        # Partido en dos no hay cuerpo que chocar: el daño por contacto de un
        # jefe invisible es indefendible, porque el jugador no puede ver
        # dónde está lo que le hace daño. Un rect vacío no colisiona con
        # nada, así que basta con devolverlo mientras dure la división.
        if self._mitades:
            return pygame.Rect(0, 0, 0, 0)
        # AUD-165 — la caja de golpe no puede salirse del cuerpo (30x50):
        # antes era `Rect(5, 3, 30, 50)`, el cuerpo entero desplazado, que
        # golpeaba desde fuera del sprite. Ahora se encoge y centra como la
        # hurtbox (28x48).
        return pygame.Rect(2, 2, 26, 46)

    def _build_hurtbox(self) -> pygame.Rect:
        ox = (self.rect.width - 28) // 2
        oy = (self.rect.height - 48) // 2
        return pygame.Rect(ox, oy, 28, 48)

    # ── Movimiento: Catmull-Rom sobre 4 posiciones, cada 0.3s ──────────

    def _update_movement(self, dt: float) -> None:
        """Despacha al movimiento de la fase activa (spec §4.3).

        Fase 1 y 2 recorren una curva recalculada cada 0.3 s; la Fase 3
        abandona las curvas y persigue al jugador en línea recta.
        """
        if self.current_phase == self.PHASE_FRENESI:
            self._update_pursuit(dt)
            return

        self._path_timer += dt
        if not self._path_points or self._path_timer >= self.PATH_RECALC_INTERVAL:
            self._path_timer = 0.0
            self._path_points = self._build_random_path()
            self._path_largo = self._longitud_de_ruta(self._path_points)
            self._path_avance = 0.0

        # Se avanza por DISTANCIA, no por tiempo normalizado.
        #
        # Antes era `t = timer / 0.3`, o sea: recorrer la curva ENTERA cada
        # 0.3 s, fuera cual fuera su largo. Con puntos repartidos por toda la
        # sala eso daba ~900 px/s — el jefe no se veía errático, se veía
        # teletransportándose, y la velocidad de 50 px/s del spec no se
        # cumplía en ningún momento.
        #
        # Ahora la curva se recalcula igual cada 0.3 s (el nervio de la
        # marioneta viene de ahí), pero el Rey solo recorre el trozo que le
        # da su velocidad. La forma la pone la curva; el ritmo, el spec.
        velocidad = self.WALK_SPEED * self.speed_multiplier
        self._path_avance += velocidad * dt
        t = 0.0 if self._path_largo <= 0.0 else clamp(
            self._path_avance / self._path_largo, 0.0, 1.0,
        )
        x, y = CurveTools.sample_path(self._path_points, t)
        self.position.x = x
        self.position.y = y
        self._movio_este_frame = True
        self.clamp_to_arena()

    @staticmethod
    def _longitud_de_ruta(puntos: list[tuple[float, float]]) -> float:
        """Largo de la polilínea que aproxima la curva ya muestreada."""
        total = 0.0
        for (x0, y0), (x1, y1) in zip(puntos, puntos[1:]):
            total += math.hypot(x1 - x0, y1 - y0)
        return total

    def _update_pursuit(self, dt: float) -> None:
        """Fase 3: persecución recta a 130 px/s (spec §4.3).

        Sin curvas a propósito: el contraste entre el vagabundeo nervioso de
        las fases anteriores y esta línea recta es lo que hace que «El
        Frenesí» se lea como un cambio de intención, no solo de velocidad.
        """
        if self._player_ref is None:
            return
        boss_pos = pygame.Vector2(self.rect.centerx, self.rect.centery)
        player_pos = pygame.Vector2(self._player_ref.centerx, self._player_ref.centery)

        # Unit II: dirección unitaria hacia el jugador, escalada por la
        # velocidad del spec. Solo en X — el Rey sigue pegado al suelo.
        #
        # Unidad VII: en penumbra el Rey avanza con cautela. No es un castigo
        # al jugador que se esconde, es lo contrario — esconderse en la
        # oscuridad le compra distancia, a cambio de que el Rey falle menos
        # cuando salga a la luz.
        direction = vec2_normalize(player_pos - boss_pos)
        cautela = lerp(self.PERSECUCION_EN_PENUMBRA, 1.0, self._brillo_leido)
        # Unidad IX: el subtipo activo también modula el avance. Es una de las
        # señales que el jugador tiene para deducir en cuál está.
        avance = self._perfil_subtipo("avance")
        self.position.x += direction.x * self.PURSUIT_SPEED * cautela * avance * dt
        self.position.y = self._floor_y
        self.clamp_to_arena()

    def _build_random_path(self) -> list[tuple[float, float]]:
        """Curva Catmull-Rom desde la posición actual hasta 3 puntos al azar.

        Unit III: `CurveTools.catmull_rom` pasa exactamente por cada punto de
        control (a diferencia de una Bézier, que solo pasa por los extremos),
        lo que produce el movimiento nervioso y errático de una marioneta
        tirada por hilos en vez de un recorrido suave.
        """
        control_points = [(self.position.x, self.position.y)]
        control_points += [self._random_arena_point() for _ in range(self.RANDOM_POINTS)]
        if self.current_phase == self.PHASE_DIVISION:
            # Fase 2 «La División»: los dos flujos de serpientes serpentean.
            # Una Bézier NO pasa por sus puntos de control intermedios, así
            # que el recorrido sale suave y ondulante — el contraste exacto
            # con el andar entrecortado de la marioneta de la Fase 1.
            return CurveTools.bezier(control_points, self.PATH_SAMPLES)
        return CurveTools.catmull_rom(control_points, self.PATH_SAMPLES)

    def _random_arena_point(self) -> tuple[float, float]:
        """Punto de control al azar, cerca del jefe y dentro del arena.

        El sorteo se hace en una ventana de `WANDER_RADIUS` alrededor de la
        posición actual, no en todo el ancho de la sala: así el recorrido
        sigue siendo impredecible pero deja de dar saltos de cientos de
        píxeles. La ventana se recorta después contra las paredes, de modo
        que junto a un muro el Rey merodea hacia dentro en vez de empujar
        contra él.
        """
        if self.arena_bounds is None:
            return (self.position.x, self.position.y)
        left = self.arena_bounds.left + self.ARENA_MARGIN
        right = self.arena_bounds.right - self.ARENA_MARGIN - self.rect.width
        if right < left:
            left = right = self.arena_bounds.centerx - self.rect.width // 2
        else:
            left = max(left, self.position.x - self.WANDER_RADIUS)
            right = min(right, self.position.x + self.WANDER_RADIUS)
            if right < left:
                left = right = clamp(
                    self.position.x,
                    self.arena_bounds.left + self.ARENA_MARGIN,
                    self.arena_bounds.right - self.ARENA_MARGIN - self.rect.width,
                )
        x = random.uniform(left, right)
        y = self._floor_y + random.uniform(-self.FLOOR_JITTER, self.FLOOR_JITTER)
        return (x, y)

    # ── Ataques (spec §4.3, Fase 1) ────────────────────────────────────
    #
    # El prefijo `_do_` es la convención del framework para los métodos de
    # ataque: el jefe de referencia usa `_do_stomp`, `_do_charge`,
    # `_do_vine_toss`. Los nombres declarativos siguen viviendo en
    # `BossPhase(attack_patterns=[...])`, que es el campo real del dataclass.

    def _do_venom_spit(self) -> None:
        """VENOM_SPIT: glob de veneno recto hacia el jugador (0.5 corazones)."""
        if self._player_ref is None:
            return

        boss_pos = pygame.Vector2(self.rect.centerx, self.rect.centery)
        player_pos = pygame.Vector2(self._player_ref.centerx, self._player_ref.centery)

        # Unit II: distancia y dirección normalizada — el glob de veneno se
        # dispara solo dentro de rango y viaja recto hacia el jugador.
        if vec2_distance(boss_pos, player_pos) > self.VENOM_SPIT_RANGE:
            return
        direction = vec2_normalize(player_pos - boss_pos)
        if direction.length_squared() == 0.0:
            return

        # Unidad VII: la puntería se degrada con la oscuridad medida por el
        # histograma. A plena luz el error es 0 y el glob va exacto; a ciegas
        # se desvía hasta PUNTERIA_ERROR_MAX grados. Es lo que convierte una
        # lámpara del mapa en una decisión táctica del jugador.
        error = self.PUNTERIA_ERROR_MAX * self.oscuridad
        if error > 0.0:
            direction = direction.rotate(random.uniform(-error, error))

        self._projectiles.append({
            "pos": pygame.Vector2(boss_pos),
            "vel": direction * self.VENOM_SPIT_SPEED,
            "damage": self.VENOM_SPIT_DAMAGE,
            "alive": True,
        })
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="VENOM_SPIT", rect=self.rect)
        # El sonido del escupitajo existe en disco y tiene subtítulo; sin esta
        # línea el Rey escupía en silencio (mismo descuido que el AUD-064 del
        # Venado).
        self._event_bus.emit(Events.SFX_BOSSES_REY_SPIT)

    def _do_body_slam(self) -> None:
        """BODY_SLAM: embestida corta cuerpo a cuerpo (1.0 corazón).

        Spec §4.3: «Player within 64px — lurches forward 80px instantly».
        La marioneta se abalanza sobre el jugador cuando lo tiene encima,
        castigando quedarse pegado al jefe para golpearlo gratis.
        """
        if self._player_ref is None:
            return

        boss_pos = pygame.Vector2(self.rect.centerx, self.rect.centery)
        player_pos = pygame.Vector2(self._player_ref.centerx, self._player_ref.centery)

        # Unit II: el mismo par distancia/dirección que VENOM_SPIT, pero a
        # quemarropa. `vec2_distance` decide si el jugador está en rango de
        # embestida y `vec2_normalize` da el vector unitario del empujón, que
        # se escala por la distancia fija del spec (80 px).
        if vec2_distance(boss_pos, player_pos) > self.BODY_SLAM_RANGE:
            return
        direction = vec2_normalize(player_pos - boss_pos)
        if direction.length_squared() == 0.0:
            return

        # Solo se desplaza en X: el Rey camina por el suelo, no vuela. La Y
        # la sigue gobernando `_floor_y` en `_update_movement`.
        self.position.x += direction.x * self.BODY_SLAM_LUNGE
        self.clamp_to_arena()

        self._event_bus.emit(Events.BOSS_ATTACK, pattern="BODY_SLAM", rect=self.rect)

    def _do_venom_burst(self) -> None:
        """VENOM_BURST: abanico de 5 globos (0.25 corazones cada uno).

        Spec §4.3, Fase 3: ángulos −30°, −15°, 0°, +15°, +30° respecto a la
        línea jefe→jugador, cada 6 segundos.
        """
        if self._player_ref is None:
            return

        boss_pos = pygame.Vector2(self.rect.centerx, self.rect.centery)
        player_pos = pygame.Vector2(self._player_ref.centerx, self._player_ref.centery)

        aim = vec2_normalize(player_pos - boss_pos)
        if aim.length_squared() == 0.0:
            return

        # Unit II: un solo vector unitario de puntería, rotado a cada ángulo
        # del abanico. `Vector2.rotate` aplica la matriz de rotación 2D, así
        # que no hay que escribirla a mano.
        for angle in self.VENOM_BURST_ANGLES:
            self._projectiles.append({
                "pos": pygame.Vector2(boss_pos),
                "vel": aim.rotate(angle) * self.VENOM_SPIT_SPEED,
                "damage": self.VENOM_BURST_DAMAGE,
                "alive": True,
            })

        self._event_bus.emit(Events.BOSS_ATTACK, pattern="VENOM_BURST", rect=self.rect)

    def _do_lunge(self) -> None:
        """LUNGE: arma la carga de 160px hacia el jugador (1.25 corazones).

        Spec §4.3, Fase 3. A diferencia de BODY_SLAM —un empujón instantáneo
        a quemarropa— esta carga recorre la distancia a 350 px/s, así que
        tiene recorrido visible y se puede esquivar. Aquí solo se fija el
        rumbo; el avance lo hace `_advance_lunge` fotograma a fotograma.
        """
        if self._player_ref is None:
            return

        boss_pos = pygame.Vector2(self.rect.centerx, self.rect.centery)
        player_pos = pygame.Vector2(self._player_ref.centerx, self._player_ref.centery)

        direction = vec2_normalize(player_pos - boss_pos)
        if direction.length_squared() == 0.0:
            return

        # Se guarda solo el signo en X: la carga es rasante, no un salto.
        self._lunge_direction = 1.0 if direction.x >= 0.0 else -1.0
        self._lunge_t = 0.0
        self._lunge_origen_x = self.position.x

        self._event_bus.emit(Events.BOSS_ATTACK, pattern="LUNGE", rect=self.rect)

    def _advance_lunge(self, dt: float) -> None:
        """Avanza la carga con aceleración (Unidad VI).

        La carga no va a velocidad constante: recorre los 160 px del spec
        siguiendo `ease_in_quad`, que arranca en cero y acelera. Se avanza la
        DISTANCIA con la curva, no la velocidad — hacerlo al revés dejaría la
        carga clavada, porque `ease_in_quad(0) = 0` y nunca despegaría.

        El efecto es de lectura, no de adorno: un arranque lento hace visible
        el compromiso del Rey (todavía se puede esquivar) y el tramo final
        rápido es el que castiga haberse quedado quieto. A velocidad constante
        los dos tramos se ven igual y la carga se vuelve ilegible.
        """
        if self._lunge_t >= 1.0:
            return
        self._lunge_t = min(1.0, self._lunge_t + dt / self.LUNGE_DURATION)
        recorrido = self.LUNGE_DISTANCE * ease_in_quad(self._lunge_t)
        self.position.x = self._lunge_origen_x + self._lunge_direction * recorrido
        self.clamp_to_arena()

    # ── Unidad VI: reacción a eventos del jugador ──────────────────────

    def set_event_bus(self, bus: Any) -> None:
        """Recibe el bus de la escena y se suscribe a lo que le interesa.

        La escena llama a este método si existe (`stage_scene.py`), y si no
        asigna `_event_bus` a pelo. Definirlo es la forma de enterarse de que
        el bus ya está disponible: en `__init__` todavía no lo está.

        El bus guarda referencias **débiles**, pero usa `WeakMethod` para los
        métodos ligados, así que la suscripción vive tanto como el jefe.
        """
        self._event_bus = bus
        bus.subscribe(Events.PLAYER_DAMAGED, self._on_player_damaged)

    def _on_player_damaged(self, **_datos: Any) -> None:
        """El Rey se detiene un instante al herir al jugador.

        No es una pausa gratuita: marca el golpe y le da al jugador un respiro
        legible para reposicionarse, en vez de encadenar ataques sin aire.
        """
        self._savouring = True
        self._savour_t = 0.0

    def _factor_de_saboreo(self, dt: float) -> float:
        """Multiplicador de movimiento mientras el Rey saborea el golpe.

        Va de 0 (quieto) a 1 (velocidad normal) siguiendo `ease_out_quad`:
        arranca deprisa y se asienta al final, que es como se reanuda un
        cuerpo pesado. Con una rampa lineal el momento del golpe no se lee.
        """
        if not self._savouring:
            return 1.0
        self._savour_t = min(1.0, self._savour_t + dt / self.SAVOUR_DURATION)
        if self._savour_t >= 1.0:
            self._savouring = False
            return 1.0
        return ease_out_quad(self._savour_t)

    def _update_projectiles(self, dt: float) -> None:
        bounds = self.arena_bounds.inflate(64, 64) if self.arena_bounds else None
        for proj in self._projectiles[:]:
            if not proj["alive"]:
                self._projectiles.remove(proj)
                continue
            proj["pos"] += proj["vel"] * dt
            if bounds is not None and not bounds.collidepoint(proj["pos"]):
                proj["alive"] = False

    def update(self, dt: float) -> None:
        """Red de seguridad de posición, en el único punto que corre siempre.

        `_post_update` NO se ejecuta en `HURT`: `EnemyBase.update` hace
        `if self._pre_update(dt): return` y corta antes. Medido: 0 de 12
        fotogramas mientras el Rey estaba aturdido. Ahí es justo cuando hace
        falta la corrección, porque el retroceso desplaza al jefe y su propio
        movimiento —que es quien llama a `clamp_to_arena`— tampoco corre.

        Sin esto, golpearlo siempre desde el mismo lado lo empujaba fuera de
        su arena y acababa saliéndose del mapa. Aquí se corrigen las dos
        derivas que deja el motor: la horizontal (acotar al arena) y la
        vertical (`_asentar_rey`).
        """
        super().update(dt)
        # Estas cuatro cosas NO pueden vivir en `_alert_behavior`: ese gancho
        # solo corre en ALERT. Medido: tras una transición de fase el Rey
        # quedaba en PATROL y la división nunca llegaba a dispararse, porque
        # el flanco de fase se detectaba desde ahí. Un cambio de fase, una
        # invocación o una corrección de posición no dependen del humor del
        # jefe: van donde se ejecutan siempre.
        self._detect_phase_change()
        self._armar_serpientes_si_toca()
        self._vigilar_mitades()
        self.clamp_to_arena()
        self._asentar_rey(dt)

    def _post_update(self, dt: float) -> None:
        self._update_projectiles(dt)
        self._asentar_serpientes(dt)

    def _asentar_rey(self, dt: float) -> None:
        """Devuelve al Rey al suelo si un golpe lo dejó flotando.

        MISMO DEFECTO DEL MOTOR que sufre `_asentar_serpientes`, pero sobre el
        propio jefe, y aquí se acumula. Cada golpe en estado `HURT` lo empuja
        ~2.4 px hacia arriba y nada lo baja: mientras está en `HURT` o
        `RETREAT`, `_run_state_machine` sale antes de llamar a
        `_alert_behavior`, así que el movimiento del Rey —que es quien fija
        `position.y` al suelo— no llega a correr. Medido golpeándolo seguido
        en Fase 3:

            golpe  1 -> flota  3 px
            golpe  6 -> flota 15 px
            golpe 12 -> flota 29 px, y ahí se queda

        Se corrige desde `_post_update`, que sí corre en todos los estados.

        Solo se corrige cuando el movimiento del Rey NO ha corrido este
        fotograma. Si corrió, él es el dueño de la Y y hay que dejarlo: en las
        fases 1 y 2 la curva lo hace temblar hasta `FLOOR_JITTER` por encima
        del suelo, y ese temblor es el nervio de la marioneta, no una deriva
        que arreglar. Distinguirlo por estado sería frágil —hay media docena
        de estados y el motor puede añadir más—; el indicador dice exactamente
        lo que importa.
        """
        movio = self._movio_este_frame
        self._movio_este_frame = False
        if self.floor_surface_y is None or movio:
            return
        if self.state in (EnemyState.LAUNCHED, EnemyState.DYING):
            self._caida_rey = 0.0       # el motor sí gobierna el arco de LAUNCHED
            return

        if self.position.y >= self._floor_y:
            self._caida_rey = 0.0
            return

        self._caida_rey += self.GRAVEDAD_SERPIENTES * dt
        self.position.y = min(self._floor_y, self.position.y + self._caida_rey * dt)
        self.rect.y = int(self.position.y)
        if self.position.y >= self._floor_y:
            self._caida_rey = 0.0
            # El motor recuerda su propio suelo para el arco de LAUNCHED; si
            # quedó apuntando al aire, el siguiente lanzamiento lo devolvería
            # a flotar.
            self._ground_y = self._floor_y

    def _asentar_serpientes(self, dt: float) -> None:
        """Devuelve al suelo a las serpientes que un golpe dejó en el aire.

        SUPLE UN DEFECTO DEL MOTOR. En `EnemyBase._run_state_machine` solo el
        estado `LAUNCHED` recibe gravedad y re-anclaje al suelo
        (`enemy_base.py:860-862`). El estado `HURT` —el de los golpes
        normales— aplica retroceso **hacia arriba** (`_knockback_velocity.y`
        vale −25 en un golpe flojo y −85 en uno fuerte) y nunca lo deshace: el
        retroceso se amortigua a cero y el enemigo se queda flotando donde
        quedó. Medido con una serpiente sobre el suelo en y=576:

            golpe 0.5 (light)   -> flota  4 px
            golpe 1.0 (heavy)   -> flota 12 px
            golpe 2.0 (launch)  -> vuelve al suelo (este sí tiene gravedad)

        Cuanto más fuerte el golpe, más alto se queda. Reportado al profesor.

        No se toca `src/framework/`, así que la corrección vive aquí: las
        serpientes son invocación del Rey y su física es asunto suyo. Se
        respeta el arco de `LAUNCHED`, que el motor sí gobierna bien.
        """
        if self.floor_surface_y is None or not self._serpientes:
            return

        vivas: list[list[Any]] = []
        for entrada in self._serpientes:
            serpiente = entrada[0]()
            if serpiente is None or not getattr(serpiente, "is_alive", False):
                continue                      # muerta o ya recolectada
            vivas.append(entrada)

            estado = getattr(serpiente, "state", None)
            if estado in (EnemyState.LAUNCHED, EnemyState.DYING):
                entrada[1] = 0.0              # el motor la está gobernando
                continue

            suelo = float(self.floor_surface_y - serpiente.rect.height)
            if serpiente.position.y >= suelo - 0.5:
                entrada[1] = 0.0
                continue

            # Caída propia, acelerada, hasta apoyarse. No se usa
            # `_knockback_velocity` porque `_apply_knockback` la amortigua un
            # 15 % por fotograma y la caída nunca llegaría a completarse.
            entrada[1] += self.GRAVEDAD_SERPIENTES * dt
            serpiente.position.y = min(suelo, serpiente.position.y + entrada[1] * dt)
            serpiente.rect.y = int(serpiente.position.y)
            if serpiente.position.y >= suelo:
                entrada[1] = 0.0
                # El motor recuerda su propio suelo para el arco de LAUNCHED;
                # si quedó apuntando al aire, el siguiente lanzamiento la
                # devolvería a flotar.
                serpiente._ground_y = suelo

        self._serpientes = vivas

    def _check_player_contact(self, player: Player) -> None:
        player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        for proj in self._projectiles:
            if not proj["alive"]:
                continue
            proj_rect = pygame.Rect(int(proj["pos"].x - 4), int(proj["pos"].y - 4), 8, 8)
            if proj_rect.colliderect(player_hurtbox):
                player.apply_damage(proj["damage"], self.rect.center)
                proj["alive"] = False
        super()._check_player_contact(player)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        # Se mide ANTES de dibujarse a sí mismo: si el Rey ya estuviera pintado
        # y quedara dentro de la zona muestreada, su propio tinte verde
        # contaminaría la lectura y el jefe acabaría midiéndose a sí mismo.
        self._leer_brillo(surface, camera_offset)
        super().draw(surface, camera_offset)
        for proj in self._projectiles:
            if not proj["alive"]:
                continue
            sx = int(proj["pos"].x - camera_offset.x)
            sy = int(proj["pos"].y - camera_offset.y)
            pygame.draw.circle(surface, (60, 140, 40), (sx, sy), 4)
            pygame.draw.circle(surface, (200, 255, 180), (sx, sy), 4, 1)
