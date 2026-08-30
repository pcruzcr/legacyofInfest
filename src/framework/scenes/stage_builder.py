"""
StageBuilder — Builder creacional para StageScene.

Extrae la construcción de 30+ subsistemas de StageScene.__init__ y on_enter,
que hoy mezclan instanciación, cableado y validación en 300+ líneas.
El Builder permite construir por pasos y testear cada paso aislado,
y deja StageScene como Director que orquesta, no que construye.

Patrón: Builder + Facade (ver stage_facade.py)
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.ui.hud import HUD
from src.engine.ui.message_box import MessageBox
from src.engine.ui.minimap import Minimap
from src.engine.ui.screen_banner import ScreenBanner
from src.framework.entities.bestiary import Bestiary
from src.framework.entities.player import Player
from src.framework.physics.capas import MASCARA_POR_DEFECTO, Capa
from src.framework.stage.camera import Camera

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class StageBuilder:
    """Construye un StageScene por pasos (Builder).

    Uso:
        builder = StageBuilder(context, tmx_path)
        builder.build_core()          # player, camera, world
        builder.build_systems()       # collision, hazards, etc.
        builder.build_vfx()           # particles, lighting
        scene = builder.scene
    """

    def __init__(self, context: GameContext, tmx_path: Path) -> None:
        self.context = context
        self.tmx_path = tmx_path
        # El Director (StageScene) se inyecta después para evitar ciclo
        self.scene: Any = None

    def attach_scene(self, scene: Any) -> None:
        self.scene = scene

    def build_player(self, stage_data) -> Player:
        spawn = stage_data.spawn_point
        assert spawn is not None
        player = Player(spawn, event_bus=self.context.event_bus)
        player.vista_cenital = stage_data.vista == "cenital"
        player.activar_estamina(getattr(stage_data, "estamina", 0.0))
        return player

    def build_camera(self, stage_data, player: Player) -> Camera:
        cam = Camera()
        cam.follow(player)
        cam.set_map_size(*stage_data.map_pixel_size)
        cam.modo = getattr(stage_data, "camara", "seguir")
        return cam

    def build_enemies(self, stage_data, player: Player) -> None:
        from src.framework.entities.boss_base import BossBase
        from src.framework.entities.enemy_base import EnemyBase

        def _arena_del_jefe(stage_data, cuerpo: pygame.Rect) -> pygame.Rect:
            for zona in stage_data.zonas_arena:
                if zona.collidepoint(cuerpo.center):
                    return zona
            return pygame.Rect(0, 0, *stage_data.map_pixel_size)

        for enemy in stage_data.entity_list:
            if hasattr(enemy, "set_event_bus"):
                enemy.set_event_bus(self.context.event_bus)
            elif not getattr(enemy, "_event_bus", None):
                enemy._event_bus = self.context.event_bus
            if hasattr(enemy, "set_player_ref"):
                enemy.set_player_ref(player.rect)
            if hasattr(enemy, "set_collision_rects"):
                mascara = getattr(enemy, "mascara_de_colision", MASCARA_POR_DEFECTO)
                enemy.set_collision_rects(
                    stage_data.capas.solidos_para(mascara & Capa.SOLIDO),
                    one_way=stage_data.capas.solidos_para(mascara & Capa.PLATAFORMA),
                )
            if hasattr(enemy, "set_pendientes"):
                enemy.set_pendientes(stage_data.pendientes)
            if isinstance(enemy, BossBase):
                enemy.set_arena_bounds(_arena_del_jefe(stage_data, enemy.rect))
            elif isinstance(enemy, EnemyBase):
                if enemy.arena_bounds is None:
                    enemy.set_arena_bounds(pygame.Rect(0, 0, *stage_data.map_pixel_size))
            Bestiary.get_instance().record_encounter(Bestiary.id_de(enemy))

    def build_hud(self) -> tuple[HUD, MessageBox, ScreenBanner, Minimap]:
        hud = HUD(self.context.event_bus)
        msg = MessageBox(self.context.event_bus)
        banner = ScreenBanner()
        minimap = Minimap()
        return hud, msg, banner, minimap
