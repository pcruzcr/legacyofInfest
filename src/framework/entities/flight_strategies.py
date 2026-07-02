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


# ── Strategy factory ──────────────────────────────────────────────

def make_strategy(flight_mode: str) -> IFlightStrategy:
    """Create the appropriate flight strategy for the given mode name."""
    strategy_map: dict[str, type[IFlightStrategy]] = {
        "sine": SineFlight,
        "bezier": BezierFlight,
        "patrol": WaypointPatrol,
    }
    cls = strategy_map.get(flight_mode, SineFlight)
    return cls()
