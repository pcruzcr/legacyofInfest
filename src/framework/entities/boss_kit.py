"""
Module: boss_kit
System: framework.entities
Academic Unit: N/A

Piezas de encuentro de jefe: ataques telegrafiados, puntos débiles, invocaciones.

Por qué existe (AUD-053)
------------------------
`BossBase` gestionaba fases y transiciones, y nada más. Lo que
`docs/17_BOSS_SPEC.md` describe —telegrafiado, variedad de ataques, puntos
débiles, invocaciones, interacción con la arena— no tenía representación en
código. Concretamente:

* `BossPhase.attack_patterns` es una lista de cadenas que **nadie consumía**.
  Un jefe podía declarar cinco patrones de ataque y ejecutar siempre el mismo.
* `BossPhase.speed_multiplier` estaba leído por::

      if phase.speed_multiplier != 1.0:
          pass

  Es decir, se comprobaba y se descartaba. Un jefe que declara acelerar en la
  fase 2 no aceleraba.
* No había puntos débiles ni invocaciones de ningún tipo.

Este módulo aporta las piezas; `BossBase` las orquesta. La separación importa
porque un jefe concreto debería *declarar* su encuentro, no reimplementar la
maquinaria.

Principio de diseño: telegrafiar es lo que hace justo a un jefe
---------------------------------------------------------------
Cada `BossAttack` tiene tres tramos con propósitos distintos:

``windup``  el jefe anuncia. Debe ser lo bastante largo para *leerse* y
            reposicionarse — por debajo de ~0,4 s el jugador reacciona por
            memoria, no por lectura, y el combate se vuelve de ensayo y error.
``active``  el golpe. Corto: el peligro debe ser un instante identificable, no
            un estado prolongado en el que uno no sabe cuándo empezó.
``recover`` el jefe es vulnerable. Es la ventana de castigo, y sin ella el
            jugador no tiene forma de responder, sólo de esperar.

Un ataque sin windup es injusto; uno sin recover es tedioso. Los dos números
son decisiones de diseño y por eso están explícitos en cada ataque en lugar de
enterrados en la implementación.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.framework.entities.enemy_base import EnemyBase


class AttackTiming(str, Enum):
    """Tramo en el que está un ataque telegrafiado."""

    IDLE = "IDLE"
    WINDUP = "WINDUP"
    ACTIVE = "ACTIVE"
    RECOVER = "RECOVER"


#: Por debajo de esto el aviso no se puede leer y el ataque se vuelve injusto.
MIN_READABLE_WINDUP: float = 0.35


@dataclass
class BossAttack:
    """Un ataque con aviso, golpe y ventana de castigo."""

    name: str
    windup: float = 0.6
    active: float = 0.2
    recover: float = 0.8
    damage: float = 1.0
    #: Alcance en px; los ataques a distancia lo usan como rango de disparo.
    reach: float = 48.0
    #: Distancia mínima y máxima a la que este ataque es una elección sensata.
    min_range: float = 0.0
    max_range: float = 9999.0
    #: Segundos antes de poder repetirlo. Evita que el jefe encadene su mejor
    #: opción indefinidamente, que es lo que convierte un patrón en un muro.
    cooldown: float = 1.5
    #: Fases en las que está disponible. Vacío = todas.
    phases: tuple[int, ...] = ()
    #: F5.7 — ¿se puede desviar con el parry del jugador?
    #:
    #: `ParryState` existía desde hace meses y **no tenía con qué practicar**:
    #: desviar no cambiaba nada en ningún jefe, así que la mecánica estaba en el
    #: juego y no estaba en el juego. Doce análisis del dossier de jefes giran
    #: sobre esto —Sekiro, Katana ZERO, Metal Gear Rising, Cuphead— y es lo que
    #: convierte un saco de golpes en un duelo.
    #:
    #: No todos los ataques deben serlo. Un ataque imparable obliga a moverse en
    #: vez de a esperar el desvío, y sin al menos uno el combate se resuelve
    #: quieto en el sitio pulsando un botón.
    parriable: bool = False
    #: Segundos de aturdimiento del jefe al ser desviado. Es la recompensa: sin
    #: ella el parry sólo evita daño y no invita a arriesgarse.
    aturde_al_parry: float = 1.2

    def __post_init__(self) -> None:
        # 1. Telegrafía obligatoria — windup <0.35 es ilegible y vuelve el combate ensayo/error
        if self.windup < MIN_READABLE_WINDUP:
            import logging
            logging.getLogger(__name__).warning(
                "BossAttack %r windup %.2fs < %.2fs — clamp a mínimo legible",
                self.name, self.windup, MIN_READABLE_WINDUP,
            )
            object.__setattr__(self, "windup", MIN_READABLE_WINDUP)

    def available_in(self, phase: int) -> bool:
        return not self.phases or phase in self.phases

    def in_range(self, distance: float) -> bool:
        return self.min_range <= distance <= self.max_range

    @property
    def total_duration(self) -> float:
        return self.windup + self.active + self.recover

    def is_readable(self) -> bool:
        """¿El aviso da tiempo real a reaccionar?"""
        return self.windup >= MIN_READABLE_WINDUP


@dataclass
class WeakPoint:
    """Zona que recibe daño aumentado, opcionalmente sólo en ciertas fases.

    Un punto débil convierte "golpea al jefe" en "colócate y golpea aquí", que
    es la diferencia entre una barra de vida y un encuentro. Se expone en
    coordenadas locales para que siga al jefe al moverse.
    """

    #: Desplazamiento respecto a la esquina superior izquierda del jefe.
    offset: tuple[int, int]
    size: tuple[int, int]
    #: Multiplicador de daño al acertar aquí.
    multiplier: float = 2.5
    #: Fases en las que está expuesto. Vacío = todas.
    phases: tuple[int, ...] = ()
    #: Etiqueta para el overlay de depuración y el bestiario.
    label: str = "núcleo"

    def rect_for(
        self, boss_rect: pygame.Rect,
        escala: float = 1.0, facing: int = 1,
    ) -> pygame.Rect:
        """El rect del punto débil sobre el cuerpo vivo (AUD-606, fix B-050).

        `escala` multiplica offset y tamaño para seguir al jefe escalado por
        fase; `facing` espeja el offset X cuando el jefe mira a la izquierda,
        con la misma fórmula que implica el flip del sprite
        (`ancho − offset_x − ancho_caja`). Los valores por defecto conservan
        el comportamiento histórico —offsets crudos sin espejar— para quien
        llame con la firma vieja.

        B-050: con escala !=1 el espejado debe hacerse sobre el ancho sin
        escalar y luego escalar (escala·(ancho−offset−w)), no sobre el ancho ya
        agrandado. Antes se hacía (boss_rect.width−offset−w)*escala con
        boss_rect.width ya escalado → doble escala y ~15 px de desplazamiento
        en fase 2 del Venado (1.25×) mirando a la izquierda.
        """
        ox_f, oy_f = float(self.offset[0]), float(self.offset[1])
        w_f, h_f = float(self.size[0]), float(self.size[1])
        ox, oy = ox_f, oy_f
        w, h = int(w_f), int(h_f)
        if facing < 0:
            # B-050 fix: espejar sobre ancho base, luego escalar
            if escala not in (0, 1.0):
                base_w = boss_rect.width / escala
                ox = base_w - ox_f - w_f
            else:
                ox = boss_rect.width - ox_f - w_f
        return pygame.Rect(
            int(boss_rect.x + ox * escala),
            int(boss_rect.y + oy * escala),
            max(1, int(w * escala)),
            max(1, int(h * escala)),
        )

    def exposed_in(self, phase: int) -> bool:
        return not self.phases or phase in self.phases


@dataclass
class SummonWave:
    """Invocación de esbirros con tope de población.

    El tope no es una optimización, es diseño: sin él un jefe que invoca cada N
    segundos acaba llenando la pantalla y el encuentro deja de ser sobre el jefe.
    """

    species_id: str
    count: int = 2
    #: Máximo de invocados vivos a la vez, contando oleadas previas.
    max_alive: int = 4
    cooldown: float = 8.0
    #: Fases en las que invoca. Vacío = todas.
    phases: tuple[int, ...] = ()
    #: Desplazamientos respecto al jefe donde aparecen.
    spawn_offsets: tuple[tuple[int, int], ...] = ((-64, -16), (64, -16))

    def available_in(self, phase: int) -> bool:
        return not self.phases or phase in self.phases


class AttackScheduler:
    """Elige qué ataque lanza el jefe y lleva sus tiempos.

    AUD-053: `BossPhase.attack_patterns` era una lista de cadenas que nadie
    consumía, así que un jefe con cinco patrones declarados ejecutaba siempre el
    mismo. Esto los consume de verdad.

    La selección evita repetir el último ataque cuando hay alternativa. No es
    aleatoriedad por variedad decorativa: repetir el mismo ataque dos veces
    seguidas hace que el jugador no pueda distinguir "el jefe está en bucle" de
    "he leído mal el aviso", y eso rompe la confianza en el telegrafiado.
    """

    def __init__(self, attacks: list[BossAttack] | None = None) -> None:
        self._attacks: list[BossAttack] = list(attacks or [])
        self._cooldowns: dict[str, float] = {}
        self._current: BossAttack | None = None
        self._timing: AttackTiming = AttackTiming.IDLE
        self._timer: float = 0.0
        self._last_name: str = ""

    # ── consulta ───────────────────────────────────────────────

    @property
    def current(self) -> BossAttack | None:
        return self._current

    @property
    def timing(self) -> AttackTiming:
        return self._timing

    @property
    def is_active(self) -> bool:
        """¿Está el golpe conectando ahora mismo?"""
        return self._timing == AttackTiming.ACTIVE

    @property
    def is_vulnerable(self) -> bool:
        """¿Está el jefe en su ventana de castigo?"""
        return self._timing == AttackTiming.RECOVER

    @property
    def telegraph_progress(self) -> float:
        """0-1 durante el aviso; alimenta el indicador visual."""
        if self._timing != AttackTiming.WINDUP or self._current is None:
            return 0.0
        windup = max(self._current.windup, 1e-6)
        return max(0.0, min(1.0, 1.0 - self._timer / windup))

    # ── actualización ──────────────────────────────────────────

    def update(self, dt: float, distance: float, phase: int) -> str | None:
        """Avanza los tiempos. Devuelve el nombre del ataque al entrar en ACTIVE."""
        for name in list(self._cooldowns):
            self._cooldowns[name] = max(0.0, self._cooldowns[name] - dt)

        if self._current is None:
            self._try_start(distance, phase)
            return None

        self._timer -= dt
        if self._timer > 0.0:
            return None

        if self._timing == AttackTiming.WINDUP:
            self._timing = AttackTiming.ACTIVE
            self._timer = self._current.active
            return self._current.name

        if self._timing == AttackTiming.ACTIVE:
            self._timing = AttackTiming.RECOVER
            self._timer = self._current.recover
            return None

        # Fin de la recuperación.
        self._cooldowns[self._current.name] = self._current.cooldown
        self._last_name = self._current.name
        self._current = None
        self._timing = AttackTiming.IDLE
        return None

    def _try_start(self, distance: float, phase: int) -> None:
        options = [
            a for a in self._attacks
            if a.available_in(phase)
            and a.in_range(distance)
            and self._cooldowns.get(a.name, 0.0) <= 0.0
        ]
        if not options:
            return
        # Prefiere no repetir el último si hay con qué.
        fresh = [a for a in options if a.name != self._last_name]
        chosen = random.choice(fresh or options)
        self._current = chosen
        self._timing = AttackTiming.WINDUP
        self._timer = chosen.windup

    def interrupt(self) -> None:
        """Cancela el ataque en curso (por aturdimiento o cambio de fase)."""
        if self._current is not None:
            self._cooldowns[self._current.name] = self._current.cooldown * 0.5
        self._current = None
        self._timing = AttackTiming.IDLE
        self._timer = 0.0

    # ── F5.7 — desvío ──────────────────────────────────────────
    @property
    def se_puede_desviar(self) -> bool:
        """¿El ataque en curso admite parry, y estamos a tiempo?

        Sólo durante `WINDUP` y `ACTIVE`. Permitirlo en `RECOVER` haría que el
        desvío funcionara **después** del golpe, y con eso el jugador aprendería
        a pulsar tarde, que es justo el hábito contrario al que la mecánica
        quiere enseñar.
        """
        return (
            self._current is not None
            and self._current.parriable
            and self._timing in (AttackTiming.WINDUP, AttackTiming.ACTIVE)
        )

    def desviar(self) -> float:
        """El jugador desvía. Devuelve los segundos de aturdimiento (0 si no cuela).

        Al desviar, el ataque entra en **enfriamiento completo** y no a la mitad
        como en una interrupción normal. Un jefe al que desvías y que repite el
        mismo ataque al instante convierte el acierto en castigo.
        """
        if not self.se_puede_desviar or self._current is None:
            return 0.0
        aturde = self._current.aturde_al_parry
        self._cooldowns[self._current.name] = self._current.cooldown
        self._last_name = self._current.name
        self._current = None
        self._timing = AttackTiming.IDLE
        self._timer = 0.0
        return aturde

    def reset(self) -> None:
        self._cooldowns.clear()
        self.interrupt()
        self._last_name = ""


@dataclass
class SummonTracker:
    """Lleva la cuenta de esbirros invocados y respeta el tope."""

    waves: list[SummonWave] = field(default_factory=list)
    _cooldowns: dict[str, float] = field(default_factory=dict)
    _spawned: list[EnemyBase] = field(default_factory=list)

    def update(self, dt: float) -> None:
        for key in list(self._cooldowns):
            self._cooldowns[key] = max(0.0, self._cooldowns[key] - dt)
        # Purga los muertos para que el tope refleje la población real.
        self._spawned = [e for e in self._spawned if getattr(e, "is_alive", False)]

    @property
    def alive_count(self) -> int:
        return len(self._spawned)

    def ready_wave(self, phase: int) -> SummonWave | None:
        for wave in self.waves:
            if not wave.available_in(phase):
                continue
            if self._cooldowns.get(wave.species_id, 0.0) > 0.0:
                continue
            if self.alive_count >= wave.max_alive:
                continue
            return wave
        return None

    def spawn(
        self, wave: SummonWave, origin: pygame.Vector2,
    ) -> list[EnemyBase]:
        """Crea la oleada, recortada al tope de población."""
        from src.framework.entities import bestiary_registry

        spec = bestiary_registry.get(wave.species_id)
        if spec is None:
            return []

        room = max(0, wave.max_alive - self.alive_count)
        to_spawn = min(wave.count, room)
        created: list[EnemyBase] = []
        for i in range(to_spawn):
            offset = wave.spawn_offsets[i % len(wave.spawn_offsets)]
            position = pygame.Vector2(origin.x + offset[0], origin.y + offset[1])
            created.append(spec.build(position))

        self._spawned.extend(created)
        self._cooldowns[wave.species_id] = wave.cooldown
        return created

    def reset(self) -> None:
        self._cooldowns.clear()
        self._spawned.clear()


def resolve_weak_point_damage(
    boss: EnemyBase,
    hit_rect: pygame.Rect,
    base_damage: float,
    weak_points: list[WeakPoint],
    phase: int,
) -> tuple[float, WeakPoint | None]:
    """Daño tras aplicar puntos débiles, y cuál se acertó.

    Devuelve el multiplicador del punto más alto acertado, no la suma: si dos
    puntos débiles se solapan, acertar ambos no debería multiplicar dos veces —
    eso premiaría la geometría del solape en lugar de la puntería.
    """
    best: WeakPoint | None = None
    # AUD-606 — sólo los jefes que declaran `cajas_siguen_al_cuerpo` reciben
    # escala y espejado en sus puntos débiles: los que ya compensan a mano
    # (el venado antes de AUD-606) recibirían un doble espejo, que devuelve
    # el punto al lado equivocado otra vez.
    sigue = bool(getattr(boss, "cajas_siguen_al_cuerpo", False))
    for point in weak_points:
        if not point.exposed_in(phase):
            continue
        rect_punto = (
            point.rect_for(
                boss.rect,
                escala=getattr(boss, "_escala_viva", lambda: 1.0)(),
                facing=getattr(boss, "facing_direction", 1),
            )
            if sigue
            else point.rect_for(boss.rect)
        )
        if hit_rect.colliderect(rect_punto) and (
            best is None or point.multiplier > best.multiplier
        ):
            best = point
    if best is None:
        return base_damage, None
    return base_damage * best.multiplier, best
