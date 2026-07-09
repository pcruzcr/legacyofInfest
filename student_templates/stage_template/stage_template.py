"""
Module: stage_template
System: stage (student assignment)
Academic Unit: See README.md front-matter for units_demonstrated.

STUDENT INSTRUCTIONS:
1. Copy this entire folder to src/stages/<your_assignment_id>/
2. Rename this file and the .tmx file to match your assignment_id
   (e.g., stage1_2_la_soda.py, stage1_2_la_soda.tmx)
3. Rename the class below from StageTemplate to a descriptive name
   (e.g., Stage1_2_LaSoda)
4. Fill in every # TODO(student) marker.
5. Do NOT modify anything outside the marked sections — the engine
   and framework integration points below are required exactly as written.
"""

from pathlib import Path

from src.engine.scene.base_scene import BaseScene
from src.engine.core.event_bus import EventBus
from src.engine.core.game_context import GameContext
from src.engine.core.settings import STAGES_DIR
from src.framework.entities.player import Player
from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import EnemyShooter
from src.framework.stage.stage_loader import StageLoader, StageData
from src.framework.stage.camera import Camera
from src.framework.stage.checkpoint import Checkpoint
from src.engine.ui.hud import HUD
from src.engine.ui.message_box import MessageBox
from src.engine.ui.screen_banner import ScreenBanner


# TODO(student): Rename this class to match your assignment
# (e.g., class Stage1_2_LaSoda(BaseScene):)
class StageTemplate(BaseScene):
    """
    TODO(student): One-paragraph description of your stage's zone,
    narrative context (see 16_WORLD_DESIGN.md for your assigned zone),
    and the academic concepts it demonstrates.
    """

    # TODO(student): Point this at your renamed .tmx file
    TMX_PATH = "student_templates/stage_template/stage_template.tmx"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self.stage_data: StageData | None = None
        self.player: Player | None = None
        self.camera = Camera()
        self.hud = HUD(event_bus=context.event_bus)
        self.message_box = MessageBox(event_bus=context.event_bus)
        self.screen_banner = ScreenBanner()
        self._register_entities()

    def _register_entities(self) -> None:
        """
        Required framework entity registration. Do not remove these three.
        TODO(student): Add StageLoader.register_entity(...) calls here for
        any CUSTOM entity subclasses you create (see 05_ENEMY_SPEC.md §11.2
        for the pattern). Do not duplicate Walker/Flying/Shooter — they are
        already registered globally by the engine.
        """
        pass  # Custom entity registrations go here, if any.

    def on_enter(self) -> None:
        self.stage_data = StageLoader.load(self.TMX_PATH)
        self.player = Player(spawn_position=self.stage_data.spawn_point)
        self.camera.follow(self.player)
        self.hud.bind_player(self.player)
        self.hud.start_timer(seconds=self.stage_data.time_limit)
        self.screen_banner.play(
            stage_id=self.stage_data.stage_id,
            stage_name=self.stage_data.stage_name,
        )

        # TODO(student): If your stage needs setup beyond what StageLoader
        # already does (e.g., spawning a custom entity not driven by TMX),
        # do it here.

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self.player.update(dt)
        for entity in self.stage_data.entity_list:
            if entity.is_active:
                entity.update(dt)
        for checkpoint in self.stage_data.checkpoints:
            checkpoint.update(dt)
        self.camera.update(dt)
        self.hud.update(dt)
        self.message_box.update(dt)
        self.screen_banner.update(dt)

        self._check_attack_collisions()
        self._check_next_trigger()

        # TODO(student): Any additional per-frame logic specific to your
        # stage's academic feature (e.g., a FilterTools/VisionTools call
        # driving a custom mechanic) goes here.

    def draw(self, surface) -> None:
        offset = self.camera.offset
        self.stage_data.map_layer.draw(surface)
        for entity in self.stage_data.entity_list:
            if entity.is_visible:
                entity.draw(surface, offset)
        self.player.draw(surface, offset)
        self.hud.draw(surface)
        self.message_box.draw(surface)
        self.screen_banner.draw(surface)

    def _check_attack_collisions(self) -> None:
        """Provided. Matches the pattern in 05_ENEMY_SPEC.md §9.3. Do not modify."""
        if self.player is None or self.stage_data is None:
            return
        if self.player.active_hitbox:
            for entity in self.stage_data.entity_list:
                if (
                    entity.is_active
                    and hasattr(entity, "hurtbox")
                    and self.player.active_hitbox.colliderect(entity.hurtbox)
                ):
                    entity.apply_hit(
                        damage=self.player.current_attack_damage,
                        source_position=self.player.rect.center,
                    )
                    self.player.consume_hitbox()

    def _check_next_trigger(self) -> None:
        """Provided. Do not modify."""
        if (self.player is not None and self.stage_data is not None
                and self.stage_data.next_trigger
                and self.player.rect.colliderect(self.stage_data.next_trigger)):
            EventBus.emit("STAGE_COMPLETE")
