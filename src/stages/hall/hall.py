"""
Module: hall
System: stage (student assignment — Jose Pablo Monestel Cruz)
Academic Unit: Stage 3-2 "El Hall", Zona 3 - Sede Heredia (Unit VIII/IX track)

Do NOT modify StageScene or any engine/framework code.
Test with:
   python main.py --stage hall
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
from src.stages.hall.decor_lamp import SwingingLamp

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

# Ceiling anchor points for the two decorative lamps. Spawned from Python
# (on_stage_start) rather than as TMX objects — see the comment in
# tools/generate_hall_tmx.py for why: scripts/grade_stage.py analyzes TMX
# files without importing the stage module, so it can never learn a
# stage-local entity type, and an unknown object type in the Objects layer
# would zero out several grading categories for the whole file.
# Hang from the ceiling row (CEILING_ROW=5, y=80 in generate_hall_tmx.py),
# offset from the three skylight columns (16, 36, 53).
_LAMP_POSITIONS = ((420, 96), (700, 96))


class Hall(StageScene):
    """Stage 3-2 — El Hall (Zona 3, Sede Heredia).

    An enormous university hall: wide floor, a balcony reached by two
    staircases, an indestructible ceiling, and three skylights. El Gavilán
    Camionero Mascarero hunts the Heredia campus, so the hall is patrolled by
    aerial (FlyingHalcon) and ground (WalkerPalom, ShooterBuitre) enemies.

    Academic concepts demonstrated:
      - Vectors/interpolation (Unit II): `SwingingLamp` uses
        `math_utils.lerp`/`vec2_*` for its pendulum motion.
      - Curves (Unit III): each `FlyingHalcon` follows a closed Bezier loop
        built from TMX `Waypoint` objects via `CurveTools.build_bezier_path`
        (flight_mode="bezier"), the same mechanism the engine already uses
        for Bezier-flight enemies elsewhere in the game.
      - TMX layer stack (Unit IV): 6 tile layers (3 parallax backgrounds,
        Terrain, Terrain_Detail, FG_Overlay) plus Objects/Collision.
    """

    STAGE_ID: str = "hall"
    STAGE_NAME: str = "3-2  EL HALL"
    ZONE: int = 3
    TMX_PATH = settings.ASSETS_DIR / "maps/hall/hall.tmx"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._lamps: list[SwingingLamp] = []

    # ── Optional lifecycle hooks ────────────────────────────────────

    def on_stage_start(self) -> None:
        if self._stage_data is None:
            return
        self._lamps = []
        for x, y in _LAMP_POSITIONS:
            lamp = SwingingLamp(pygame.Vector2(x, y))
            lamp.set_event_bus(self.context.event_bus)
            self._stage_data.entity_list.append(lamp)
            self._lamps.append(lamp)

    def update(self, dt: float) -> None:
        super().update(dt)
        # BUG FIX: StageScene's own update loop only calls .update(dt) on
        # entities that are EnemyBase instances (it builds its per-frame
        # `enemies` list by filtering entity_list with
        # `isinstance(entity, EnemyBase)` before touching anything — see
        # stage_scene.py's gameplay update). SwingingLamp is a plain
        # BaseEntity (correctly — it has no health, isn't an enemy), so it
        # was silently never advanced: it rendered, just frozen at its
        # spawn position forever, never actually swinging. Confirmed by
        # direct test: position was still exactly the spawn value after 30
        # frames of scene.update(). Drawing isn't affected by this same
        # filter (DrawingSystem._draw_entities iterates the raw
        # entity_list), which is exactly why it was visible but static.
        for lamp in self._lamps:
            lamp.update(dt)

    def on_player_landed(self) -> None:
        pass

    def on_enemy_died(self, enemy) -> None:
        pass

    def on_next_trigger_entered(self) -> None:
        pass

    def on_debug_toggle(self, enabled: bool) -> None:
        pass
