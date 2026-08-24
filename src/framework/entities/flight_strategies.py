"""
Module: flight_strategies
System: framework.entities
Academic Unit: Unit III (Curve Mathematics, Sine-wave Motion)
Description: Strategy Pattern for EnemyFlying flight modes.
Each strategy encapsulates one movement algorithm (sine wave, Bézier
spline, or linear waypoint patrol), making EnemyFlying extensible
without modifying its class — adhering to the Open/Closed Principle.

STRATEGY PATTERN: EnemyFlying holds a reference to an IFlightStrategy
and delegates both _patrol_behavior and _alert_behavior to it.
Adding a new flight mode requires only a new strategy class,
not changes to EnemyFlying.
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.framework.processing.curve_tools import CurveTools

if TYPE_CHECKING:
    from src.framework.entities.enemy_flying import EnemyFlying


class IFlightStrategy(ABC):
    """
    Strategy interface for EnemyFlying movement algorithms.
    Each concrete strategy implements execute() which updates
    the enemy's position for one frame.
    """

    @abstractmethod
    def execute(
        self,
        enemy: EnemyFlying,
        dt: float,
        speed_mult: float = 1.0,
    ) -> None:
        """Update enemy position using this strategy's movement algorithm."""
        ...


class SineFlight(IFlightStrategy):
    """
    Sine-wave movement: horizontal movement with sinusoidal vertical oscillation.
    """

    def execute(
        self,
        enemy: EnemyFlying,
        dt: float,
        speed_mult: float = 1.0,
    ) -> None:
        enemy._t += dt

        # Horizontal movement
        enemy.position.x += (
            enemy.facing_direction * enemy.flight_speed * speed_mult * dt
        )

        # Vertical sine oscillation
        enemy.position.y = (
            enemy._origin.y
            + enemy.sine_amplitude
            * math.sin(2.0 * math.pi * enemy.sine_frequency * enemy._t)
        )

        # Reverse at boundaries (simple bounce)
        dx = enemy.position.x - enemy._origin.x
        if abs(dx) > 96.0:
            enemy.facing_direction *= -1

        enemy.rect.x = int(enemy.position.x)
        enemy.rect.y = int(enemy.position.y)


class BezierFlight(IFlightStrategy):
    """
    Bézier path traversal: follow a smooth closed curve through all
    waypoints using Catmull-Rom spline segments via CurveTools.
    """

    def execute(
        self,
        enemy: EnemyFlying,
        dt: float,
        speed_mult: float = 1.0,
    ) -> None:
        if not enemy._path_waypoints:
            return

        arc_length = enemy.flight_speed * speed_mult * dt
        total_path = 64.0 * max(len(enemy._path_waypoints), 1)
        enemy._path_progress += arc_length / total_path

        # Loop when done
        if enemy._path_progress > 1.0:
            enemy._path_progress -= 1.0

        pos = CurveTools.build_bezier_path(
            enemy._path_waypoints, enemy._path_progress,
        )
        enemy.position.x = pos.x
        enemy.position.y = pos.y
        enemy.rect.x = int(enemy.position.x)
        enemy.rect.y = int(enemy.position.y)


class WaypointPatrol(IFlightStrategy):
    """
    Linear waypoint patrol: move from waypoint to waypoint in order.
    """

    def execute(
        self,
        enemy: EnemyFlying,
        dt: float,
        speed_mult: float = 1.0,
    ) -> None:
        if len(enemy._path_waypoints) < 2:
            return

        target = enemy._path_waypoints[enemy._waypoint_index]
        dx = target.x - enemy.position.x
        dy = target.y - enemy.position.y
        dist = math.sqrt(dx * dx + dy * dy)

        step = enemy.flight_speed * speed_mult * dt

        if dist <= step:
            # Reached waypoint — advance to next
            enemy.position.x = target.x
            enemy.position.y = target.y
            enemy._waypoint_index += 1
            if enemy._waypoint_index >= len(enemy._path_waypoints):
                enemy._waypoint_index = 0
            # Face direction of travel
            next_target = enemy._path_waypoints[enemy._waypoint_index]
            if next_target.x != enemy.position.x:
                enemy.facing_direction = (
                    1 if next_target.x > enemy.position.x else -1
                )
        else:
            # Move toward target
            enemy.position.x += (dx / dist) * step
            enemy.position.y += (dy / dist) * step
            enemy.facing_direction = 1 if dx > 0 else -1

        enemy.rect.x = int(enemy.position.x)
        enemy.rect.y = int(enemy.position.y)


class ChaseFlight(IFlightStrategy):
    """Persecución directa con inercia — el enemigo *acelera* hacia el jugador.

    AUD-046: las tres estrategias anteriores son todas trayectorias
    predeterminadas: seno, spline y waypoints. Ninguna reacciona al jugador, así
    que un enemigo volador nunca supone una amenaza distinta de un obstáculo
    móvil. `docs/18_ENEMY_ROSTER.md` describe especies (Halcón, Terciovolador,
    Cuaderno poseído) cuyo texto habla de perseguir, y no había forma de
    expresarlo.

    Detalle de diseño: acelera hacia el objetivo en lugar de fijar la velocidad
    directamente. Un perseguidor de velocidad fija es trivial — basta con
    correr. Uno con inercia sobrepasa al girar, lo que da al jugador una ventana
    real para esquivar y convierte el enfrentamiento en una lectura de ritmo en
    vez de una carrera.
    """

    # Cuánta velocidad puede ganar por segundo, como múltiplo de flight_speed.
    ACCELERATION = 3.0
    # Fracción de velocidad conservada por segundo; por debajo de 1 el
    # perseguidor no orbita indefinidamente alrededor del jugador.
    DRAG = 0.85

    def execute(
        self,
        enemy: EnemyFlying,
        dt: float,
        speed_mult: float = 1.0,
    ) -> None:
        target = getattr(enemy, "_player_ref", None)
        if target is None:
            # Sin objetivo, mantiene la altura de origen y deriva: no se queda
            # inmóvil, que se leería como un bug.
            SineFlight().execute(enemy, dt, speed_mult * 0.4)
            return

        vel = getattr(enemy, "_chase_velocity", None)
        if vel is None:
            import pygame

            vel = pygame.Vector2(0.0, 0.0)
            enemy._chase_velocity = vel

        dx = target.centerx - enemy.position.x
        dy = target.centery - enemy.position.y
        dist = math.hypot(dx, dy)
        if dist > 1e-6:
            accel = enemy.flight_speed * self.ACCELERATION * speed_mult * dt
            vel.x += (dx / dist) * accel
            vel.y += (dy / dist) * accel

        # Amortiguación exponencial independiente del framerate.
        damping = self.DRAG ** dt
        vel.x *= damping
        vel.y *= damping

        # Techo de velocidad para que la aceleración no se dispare.
        max_speed = enemy.flight_speed * speed_mult * 1.6
        speed = math.hypot(vel.x, vel.y)
        if speed > max_speed:
            vel.x = vel.x / speed * max_speed
            vel.y = vel.y / speed * max_speed

        enemy.position.x += vel.x * dt
        enemy.position.y += vel.y * dt
        if abs(vel.x) > 1.0:
            enemy.facing_direction = 1 if vel.x > 0 else -1

        enemy.rect.x = int(enemy.position.x)
        enemy.rect.y = int(enemy.position.y)


class DiveFlight(IFlightStrategy):
    """Picado en tres fases, tal y como lo especifica el roster.

    AUD-047: `docs/18_ENEMY_ROSTER.md` §5.3 describe el comportamiento de alerta
    del Halcón con precisión::

        Al entrar el jugador en rango, el halcón pasa a picado: se desplaza
        horizontalmente hasta la X del jugador (50 px/s), luego pica a 200 px/s.
        Tras alcanzar Y=200 o golpear una plataforma, reasciende a la altitud
        de patrulla. Esto sustituye el comportamiento de alerta estándar.

    No existía nada que lo expresara: `make_strategy` sólo conocía seno, Bézier
    y waypoints, y ante un modo desconocido **cae silenciosamente en SineFlight**
    — así que el Halcón habría volado en sinusoide sin que nada avisara de que
    su comportamiento documentado no estaba implementado.

    Por qué el picado en fases funciona como diseño: telegrafía. La fase de
    alineación es lenta y legible, y da al jugador ~1 s para leer la amenaza y
    reposicionarse. La fase de picado es cuatro veces más rápida y ya no se
    puede corregir. La amenaza es justa porque se anuncia.
    """

    ALIGN_SPEED = 50.0     # px/s, fase de alineación horizontal
    DIVE_SPEED = 200.0     # px/s, fase de picado
    ASCEND_SPEED = 90.0    # px/s, regreso a la altitud de patrulla
    DIVE_FLOOR_Y = 200.0   # profundidad máxima antes de reascender
    ALIGN_TOLERANCE = 6.0  # px; por debajo de esto se considera alineado

    def execute(
        self,
        enemy: EnemyFlying,
        dt: float,
        speed_mult: float = 1.0,
    ) -> None:
        target = getattr(enemy, "_player_ref", None)
        if target is None:
            SineFlight().execute(enemy, dt, speed_mult)
            return

        phase = getattr(enemy, "_dive_phase", "align")

        if phase == "align":
            dx = target.centerx - enemy.position.x
            if abs(dx) <= self.ALIGN_TOLERANCE:
                enemy._dive_phase = "dive"
            else:
                step = self.ALIGN_SPEED * speed_mult * dt
                enemy.position.x += math.copysign(min(step, abs(dx)), dx)
                enemy.facing_direction = 1 if dx > 0 else -1

        elif phase == "dive":
            enemy.position.y += self.DIVE_SPEED * speed_mult * dt
            if enemy.position.y >= self.DIVE_FLOOR_Y:
                enemy._dive_phase = "ascend"

        else:  # ascend
            origin_y = getattr(enemy, "_origin", None)
            ceiling = origin_y.y if origin_y is not None else 0.0
            enemy.position.y -= self.ASCEND_SPEED * speed_mult * dt
            if enemy.position.y <= ceiling:
                enemy.position.y = ceiling
                # Vuelve a alinear: el ciclo se repite mientras siga alerta.
                enemy._dive_phase = "align"

        enemy.rect.x = int(enemy.position.x)
        enemy.rect.y = int(enemy.position.y)


# ── Strategy factory ──────────────────────────────────────────────

def make_strategy(flight_mode: str) -> IFlightStrategy:
    """Devuelve la estrategia de vuelo para el modo indicado.

    AUD-047: ante un modo desconocido esto cae en ``SineFlight``. Es una reserva
    razonable — un modo mal escrito en un TMX de alumno no debe tumbar el nivel —
    pero es *silenciosa*, y así fue como el picado documentado del Halcón pudo
    no existir sin que nada lo señalara. ``tests/test_bestiary_roster.py``
    comprueba ahora que cada modo que el roster nombra resuelve a su clase.
    """
    strategy_map: dict[str, type[IFlightStrategy]] = {
        "sine": SineFlight,
        "bezier": BezierFlight,
        "patrol": WaypointPatrol,
        "chase": ChaseFlight,
        "dive": DiveFlight,
    }
    cls = strategy_map.get(flight_mode, SineFlight)
    return cls()
