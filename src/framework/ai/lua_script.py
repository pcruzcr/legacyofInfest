"""
.. warning::
   **NOT WIRED (AUD-022).** This module is complete and tested in isolation, but
   nothing in the shipping game constructs or calls it — there is no menu entry,
   scene or hook that reaches it. It is retained deliberately, as a foundation
   for the feature and as teaching material, but the project documentation
   should not describe the feature as delivered until an entry point exists.
   Tracked as refactor item R-11.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from lupa import LuaRuntime

if TYPE_CHECKING:
    from src.framework.entities.enemy_base import EnemyBase
    from src.framework.entities.player import Player


_SCRIPT_CACHE: dict[str, LuaScriptEnemy] = {}


logger = logging.getLogger(__name__)


class LuaScriptEnemy:
    """Wraps a Lua AI script for a single enemy instance.

    Each script receives a table 'ctx' with:
      - ctx.enemy (table with .x, .y, .hp, .max_hp, .speed, .facing, .state)
      - ctx.player (table with .x, .y, .hp, .max_hp, .vx, .vy)
      - ctx.distance (euclidean distance to player)
      - ctx.dt (delta time)

    Expected script functions (all optional):
      - patrol(ctx) -> dx, dy  (movement vector in patrol state)
      - alert(ctx)  -> action  (string: 'approach', 'retreat', 'attack', 'wait')
      - on_hit(ctx) -> nil
      - on_death(ctx) -> nil
    """

    def __init__(self, script_source: str, name: str = "") -> None:
        self._name = name
        self._runtime = LuaRuntime(unpack_returned_tuples=True, register_eval=False)
        self._script_source = script_source
        self._runtime.execute(script_source)

    def _make_ctx(self, enemy: EnemyBase, player: Player, dt: float) -> dict[str, Any]:
        dx = enemy.position.x - player.position.x
        dy = enemy.position.y - player.position.y
        dist = (dx * dx + dy * dy) ** 0.5
        return {
            "enemy": {
                "x": enemy.position.x,
                "y": enemy.position.y,
                "hp": enemy.current_health,
                "max_hp": enemy.max_health,
                "speed": getattr(enemy, "speed", 0),
                "facing": enemy.facing_direction,
                "state": str(enemy.state),
            },
            "player": {
                "x": player.position.x,
                "y": player.position.y,
                "hp": player.current_health,
                "max_hp": player.max_health,
                "vx": player.velocity.x if player.velocity else 0.0,
                "vy": player.velocity.y if player.velocity else 0.0,
            },
            "distance": dist,
            "dt": dt,
        }

    @staticmethod
    def _to_float2(v: Any) -> tuple[float, float]:
        if isinstance(v, (tuple, list)) and len(v) == 2:
            return (float(v[0]), float(v[1]))
        return (0.0, 0.0)

    def _globals(self) -> dict[str, object]:
        g = self._runtime.globals()
        return {k: g[k] for k in g}

    def call_patrol(self, enemy: EnemyBase, player: Player, dt: float) -> tuple[float, float]:
        g = self._globals()
        func = g.get("patrol")
        if func is None:
            return (0.0, 0.0)
        try:
            return self._to_float2(func(self._make_ctx(enemy, player, dt)))
        except Exception as exc:
            logger.warning("Lua patrol script '%s' error: %s", self._name, exc)
            return (0.0, 0.0)

    def call_alert(self, enemy: EnemyBase, player: Player, dt: float) -> str:
        g = self._globals()
        func = g.get("alert")
        if func is None:
            return "approach"
        try:
            result = func(self._make_ctx(enemy, player, dt))
            return str(result) if result is not None else "approach"
        except Exception as exc:
            logger.warning("Lua alert script '%s' error: %s", self._name, exc)
            return "approach"

    def call_on_hit(self, enemy: EnemyBase, player: Player, dt: float) -> None:
        g = self._globals()
        func = g.get("on_hit")
        if func is not None:
            try:
                func(self._make_ctx(enemy, player, dt))
            except Exception as exc:
                logger.warning("Lua on_hit script '%s' error: %s", self._name, exc)

    def call_on_death(self, enemy: EnemyBase, player: Player, dt: float) -> None:
        g = self._globals()
        func = g.get("on_death")
        if func is not None:
            try:
                func(self._make_ctx(enemy, player, dt))
            except Exception as exc:
                logger.warning("Lua on_death script '%s' error: %s", self._name, exc)


def load_script(name: str) -> LuaScriptEnemy | None:
    return _SCRIPT_CACHE.get(name)


def register_script(name: str, source: str) -> LuaScriptEnemy:
    script = LuaScriptEnemy(source, name=name)
    _SCRIPT_CACHE[name] = script
    return script
