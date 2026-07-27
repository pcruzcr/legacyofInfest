"""
Module: level_metrics
System: framework.stage
Academic Unit: N/A

Métricas objetivas de diseño de nivel, derivadas de la física real del juego.

Qué mide y qué NO (AUD-049)
---------------------------
Este módulo responde preguntas que tienen una respuesta correcta comprobable:

* ¿Este salto es **físicamente posible** con la altura y el alcance que el
  jugador tiene realmente?
* ¿Se puede **llegar** desde el spawn hasta la salida?
* ¿Hay checkpoints tan separados que morir cueste más de N segundos de
  reintento?
* ¿Alguna zona concentra la mayoría de las muertes?

No mide si el nivel es **divertido**. Un bot no puede saberlo. Lo que sí puede
hacer es eliminar las causas objetivas de frustración —un salto imposible, un
pozo sin retorno, un tramo de reintento de 90 segundos— para que el playtest
humano se dedique a juzgar el ritmo y la tensión en lugar de tropezar con bugs
de geometría.

Esa separación importa: llamar "fun factor" a un número que un script calcula
invita a optimizar la métrica en vez del juego. Aquí las métricas se llaman por
lo que son.

Todos los umbrales salen de `settings`, así que si alguien cambia la fuerza de
salto las conclusiones se recalculan solas en lugar de quedar obsoletas.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import pairwise

import pygame

from src.engine.core import settings


@dataclass(frozen=True)
class JumpEnvelope:
    """La envolvente de salto del jugador, calculada de la física, no adivinada."""

    max_height: float
    air_time: float
    max_gap: float
    max_gap_with_air_jump: float
    tile: int

    @classmethod
    def from_settings(cls) -> JumpEnvelope:
        gravity = float(settings.GRAVITY)
        jump = abs(float(settings.PLAYER_JUMP_FORCE))
        speed = float(settings.PLAYER_WALK_SPEED)

        height = (jump * jump) / (2.0 * gravity)
        air_time = 2.0 * jump / gravity
        gap = speed * air_time

        # Un salto aéreo extra reinicia la velocidad vertical a mitad de vuelo,
        # así que añade aproximadamente otro arco completo de alcance.
        air_jumps = int(getattr(settings, "PLAYER_AIR_JUMPS", 0))
        gap_extended = gap * (1.0 + air_jumps)

        return cls(
            max_height=height,
            air_time=air_time,
            max_gap=gap,
            max_gap_with_air_jump=gap_extended,
            tile=int(settings.TILE_SIZE),
        )

    # Margen de seguridad: un salto que requiere el 100% de la envolvente sólo
    # se logra con entrada perfecta. Por encima de este porcentaje el salto es
    # técnicamente posible pero exige precisión de speedrun, lo cual es una
    # decisión de diseño consciente y no algo que deba aparecer por accidente.
    COMFORT = 0.80

    def classify_gap(self, width: float) -> str:
        """'trivial' | 'cómodo' | 'exigente' | 'imposible'."""
        if width <= self.max_gap * 0.4:
            return "trivial"
        if width <= self.max_gap * self.COMFORT:
            return "cómodo"
        if width <= self.max_gap_with_air_jump:
            return "exigente"
        return "imposible"

    def classify_ledge(self, height: float) -> str:
        if height <= self.max_height * 0.4:
            return "trivial"
        if height <= self.max_height * self.COMFORT:
            return "cómodo"
        if height <= self.max_height:
            return "exigente"
        return "imposible"


@dataclass
class LevelReport:
    """Resultado del análisis de un nivel."""

    stage_id: str = ""
    impossible_gaps: list[tuple[int, int, float]] = field(default_factory=list)
    demanding_gaps: list[tuple[int, int, float]] = field(default_factory=list)
    impossible_ledges: list[tuple[int, int, float]] = field(default_factory=list)
    checkpoint_gaps: list[float] = field(default_factory=list)
    unreachable_pickups: list[tuple[float, float]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    total_platforms: int = 0
    reachable_platforms: int = 0
    exit_reachable: bool = True

    @property
    def orphan_platforms(self) -> int:
        """Plataformas a las que no se puede llegar desde el spawn."""
        return max(0, self.total_platforms - self.reachable_platforms)

    @property
    def blocking_issues(self) -> int:
        """Problemas que hacen el nivel imposible de completar.

        AUD-049: sólo cuenta la alcanzabilidad de la salida y los repechos
        imposibles. Los "huecos anchos" se dejaron fuera a propósito: la primera
        versión los contaba y producía tres falsos positivos en stage0, porque un
        hueco de suelo ancho se cruza por una plataforma superior. Un hueco ancho
        es información para el diseñador, no un fallo.
        """
        blocking = 0 if self.exit_reachable else 1
        return blocking + len(self.impossible_ledges)

    def summary(self) -> str:
        lines = [f"Nivel: {self.stage_id or '(sin id)'}"]
        lines.append(f"  huecos imposibles      : {len(self.impossible_gaps)}")
        lines.append(f"  huecos exigentes       : {len(self.demanding_gaps)}")
        lines.append(f"  repechos imposibles    : {len(self.impossible_ledges)}")
        lines.append(f"  plataformas alcanzables: {self.reachable_platforms}/{self.total_platforms}")
        lines.append(f"  salida alcanzable      : {'sí' if self.exit_reachable else 'NO'}")
        if self.checkpoint_gaps:
            worst = max(self.checkpoint_gaps)
            lines.append(f"  mayor tramo sin checkpoint: {worst:.0f} px")
        for note in self.notes:
            lines.append(f"  nota: {note}")
        return "\n".join(lines)


def _ground_spans(collision_rects: list[pygame.Rect]) -> list[pygame.Rect]:
    """Superficies sobre las que el jugador puede estar de pie.

    Aproximación deliberada: toma cada rect de colisión como plataforma y usa su
    borde superior. Es suficiente para detectar huecos, y no pretende ser un
    modelo de navegación completo — prometer eso sería exagerar lo que un
    análisis estático puede afirmar.
    """
    return sorted(collision_rects, key=lambda r: (r.top, r.left))


def analyse_geometry(
    collision_rects: list[pygame.Rect],
    envelope: JumpEnvelope | None = None,
) -> LevelReport:
    """Busca huecos y repechos que la física del jugador no puede superar."""
    env = envelope or JumpEnvelope.from_settings()
    report = LevelReport()

    if not collision_rects:
        report.notes.append("el nivel no declara geometría de colisión")
        return report

    # Agrupar plataformas por altura para comparar sólo las contiguas: dos
    # plataformas a alturas muy distintas no forman un "hueco" que cruzar.
    by_row: dict[int, list[pygame.Rect]] = {}
    for rect in _ground_spans(collision_rects):
        row = rect.top // max(env.tile, 1)
        by_row.setdefault(row, []).append(rect)

    for row, rects in by_row.items():
        rects.sort(key=lambda r: r.left)
        for left, right in pairwise(rects):
            gap = right.left - left.right
            if gap <= 0:
                continue
            verdict = env.classify_gap(gap)
            entry = (left.right, row * env.tile, float(gap))
            if verdict == "imposible":
                report.impossible_gaps.append(entry)
            elif verdict == "exigente":
                report.demanding_gaps.append(entry)

    # Repechos: una plataforma directamente encima de otra y demasiado alta.
    rows = sorted(by_row)
    for upper_row, lower_row in pairwise(rows):
        rise = (lower_row - upper_row) * env.tile
        if rise <= 0:
            continue
        for upper in by_row[upper_row]:
            for lower in by_row[lower_row]:
                # Sólo cuenta si se solapan horizontalmente: si no, no es un
                # repecho, es otra parte del mapa.
                if upper.right < lower.left or upper.left > lower.right:
                    continue
                if env.classify_ledge(rise) == "imposible":
                    report.impossible_ledges.append(
                        (lower.left, lower.top, float(rise)),
                    )
                break

    return report


def analyse_checkpoints(
    checkpoints: list[object],
    spawn: pygame.Vector2,
    exit_rect: pygame.Rect | None,
    max_retry_distance: float = 1200.0,
) -> list[float]:
    """Distancias entre puntos de reaparición consecutivos.

    Un tramo largo entre checkpoints no es un bug, pero sí una decisión que el
    diseñador debería tomar a propósito. `max_retry_distance` corresponde a
    aproximadamente 13 s de recorrido a velocidad de caminar — el punto a partir
    del cual repetir deja de enseñar y empieza a castigar.
    """
    points: list[tuple[float, float]] = [(spawn.x, spawn.y)]
    for cp in checkpoints:
        pos = getattr(cp, "position", None)
        if pos is not None:
            points.append((float(pos.x), float(pos.y)))
    if exit_rect is not None:
        points.append((float(exit_rect.centerx), float(exit_rect.centery)))

    points.sort()
    return [
        math.dist(a, b)
        for a, b in pairwise(points)
    ]


def reachable_platforms(
    collision_rects: list[pygame.Rect],
    spawn: pygame.Vector2,
    envelope: JumpEnvelope | None = None,
) -> set[int]:
    """Índices de plataformas alcanzables desde el spawn, por búsqueda en grafo.

    Por qué esto sustituye a la comprobación de huecos por filas (AUD-049)
    ---------------------------------------------------------------------
    La primera versión de `analyse_geometry` comparaba plataformas contiguas
    *dentro de la misma fila* y marcaba como imposible cualquier hueco más ancho
    que el salto. Sobre stage0 reportó tres huecos imposibles, y los tres eran
    falsos positivos: un jugador cruza un hueco de suelo saltando a una
    plataforma **superior**, no atravesándolo en línea recta. Un mapa con
    plataformas escalonadas es perfectamente transitable y aquel análisis lo
    declaraba roto.

    La pregunta correcta no es "¿hay huecos anchos?" sino "¿se puede llegar?".
    Esto construye el grafo de saltos —A conecta con B si B cae dentro de la
    envolvente física desde A— y recorre desde el spawn. Es la métrica que un
    diseñador realmente quiere: le da igual que un hueco sea ancho si hay ruta.

    Sigue siendo una aproximación: no modela dash, salto de pared ni plataformas
    móviles, así que puede declarar *inalcanzable* algo que un jugador experto
    alcanza. Por eso los tests la usan para detectar niveles **desconectados**,
    no para juzgar dificultad.
    """
    env = envelope or JumpEnvelope.from_settings()
    if not collision_rects:
        return set()

    # Alcance vertical hacia arriba y horizontal, con el salto aéreo incluido.
    up = env.max_height
    span = env.max_gap_with_air_jump
    # Caer es gratis: cualquier altura hacia abajo es alcanzable.
    DOWN = 10_000.0

    def connected(a: pygame.Rect, b: pygame.Rect) -> bool:
        # Separación horizontal entre bordes (0 si se solapan).
        if b.left > a.right:
            dx = b.left - a.right
        elif a.left > b.right:
            dx = a.left - b.right
        else:
            dx = 0.0
        if dx > span:
            return False
        rise = a.top - b.top          # positivo si b está por encima
        if rise > up:
            return False
        return -rise <= DOWN

    # Plataforma de partida: la más cercana por debajo del spawn.
    start = None
    best = float("inf")
    for i, rect in enumerate(collision_rects):
        if rect.top >= spawn.y - env.tile and rect.left - span <= spawn.x <= rect.right + span:
            d = abs(rect.top - spawn.y)
            if d < best:
                best, start = d, i
    if start is None:
        # Sin suelo bajo el spawn: se toma la plataforma más cercana en general.
        start = min(
            range(len(collision_rects)),
            key=lambda i: math.dist(
                (collision_rects[i].centerx, collision_rects[i].top),
                (spawn.x, spawn.y),
            ),
        )

    seen = {start}
    frontier = [start]
    while frontier:
        current = frontier.pop()
        for j, candidate in enumerate(collision_rects):
            if j in seen:
                continue
            if connected(collision_rects[current], candidate):
                seen.add(j)
                frontier.append(j)
    return seen


def exit_is_reachable(
    collision_rects: list[pygame.Rect],
    spawn: pygame.Vector2,
    exit_rect: pygame.Rect | None,
    envelope: JumpEnvelope | None = None,
) -> bool:
    """¿Existe una cadena de saltos del spawn a la salida?"""
    if exit_rect is None:
        return False
    env = envelope or JumpEnvelope.from_settings()
    reachable = reachable_platforms(collision_rects, spawn, env)
    if not reachable:
        return False
    span = env.max_gap_with_air_jump
    for i in reachable:
        rect = collision_rects[i]
        # La salida se considera alcanzada si una plataforma alcanzable queda
        # bajo ella o a un salto de distancia.
        if (rect.left - span <= exit_rect.centerx <= rect.right + span
                and abs(rect.top - exit_rect.bottom) <= env.max_height + env.tile * 2):
            return True
    return False


def analyse_stage(stage_data: object) -> LevelReport:
    """Análisis completo de un `StageData` ya cargado."""
    rects = list(getattr(stage_data, "collision_rects", []) or [])
    report = analyse_geometry(rects)
    report.stage_id = str(getattr(stage_data, "stage_id", "") or "")

    exit_rect = getattr(stage_data, "next_trigger", None)
    spawn = getattr(stage_data, "spawn_point", None)
    report.total_platforms = len(rects)

    if spawn is not None and rects:
        report.reachable_platforms = len(reachable_platforms(rects, spawn))
        report.exit_reachable = exit_is_reachable(rects, spawn, exit_rect)
        report.checkpoint_gaps = analyse_checkpoints(
            list(getattr(stage_data, "checkpoints", []) or []),
            spawn,
            exit_rect,
        )
        if report.orphan_platforms:
            report.notes.append(
                f"{report.orphan_platforms} plataforma(s) sin ruta desde el spawn"
            )

    if not getattr(stage_data, "next_trigger", None):
        report.notes.append(
            "el nivel no declara NextTrigger: no se puede completar",
        )
    return report
