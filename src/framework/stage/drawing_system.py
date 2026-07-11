from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.enemy_base import EnemyBase

if TYPE_CHECKING:
    from src.framework.entities.player import Player
    from src.framework.stage.camera import Camera
    from src.framework.stage.stage_loader import StageData
    from src.framework.vfx.particle_system import ParticleSystem
    from src.framework.vfx.damage_numbers import DamageNumberManager
    from src.framework.vfx.ambient_particles import AmbientParticleSystem
    from src.framework.vfx.trail_system import TrailSystem
    from src.framework.ui.tutorial_overlay import TutorialOverlay
    from src.engine.ui.hud import HUD
    from src.engine.ui.message_box import MessageBox
    from src.engine.ui.screen_banner import ScreenBanner


class DrawingSystem:
    def __init__(self) -> None:
        pass

    def draw(
        self, surface: pygame.Surface,
        stage: StageData | None,
        player: Player | None,
        checkpoints: list[Any],
        camera: Camera,
        hud: HUD | None,
        msg_box: MessageBox | None,
        banner: ScreenBanner | None,
        paused: bool,
        debug: bool,
        pause_selected: int = 0,
        pause_options: list[str] | None = None,
        particle_system: ParticleSystem | None = None,
        damage_numbers: DamageNumberManager | None = None,
        ambient_particles: AmbientParticleSystem | None = None,
        trail_system: TrailSystem | None = None,
        tutorial_overlay: TutorialOverlay | None = None,
    ) -> None:
        if stage is None or player is None:
            return

        surface.fill(settings.BG_COLOR)
        self._draw_background(surface, stage, camera)
        stage.map_layer.draw(surface)
        cam_offset = camera.offset

        # Ambient particles behind entities
        if ambient_particles is not None:
            ambient_particles.draw(surface, cam_offset)

        # Trails behind entities
        if trail_system is not None:
            trail_system.draw(surface, cam_offset)

        drawables: list[tuple[BaseEntity, int]] = [(player, player.rect.centery)]
        for entity in stage.entity_list:
            if getattr(entity, "is_alive", True) or not isinstance(entity, EnemyBase):
                if getattr(entity, "is_visible", True):
                    drawables.append((entity, entity.rect.centery))
        for cp in checkpoints:
            drawables.append((cp, cp.rect.centery))
        drawables.sort(key=lambda x: x[1])
        for obj, _ in drawables:
            obj.draw(surface, cam_offset)

        # VFX layer
        if particle_system is not None:
            particle_system.draw(surface, cam_offset)
        if damage_numbers is not None:
            damage_numbers.draw(surface, cam_offset)

        if msg_box:
            msg_box.draw(surface)
        if banner:
            banner.draw(surface)
        if hud:
            hud.draw(surface)

        if tutorial_overlay:
            tutorial_overlay.draw(surface)

        if paused:
            self._draw_pause_menu(surface, pause_selected, pause_options or [])

        if debug:
            self._draw_debug(surface, stage, player, camera, paused)

    def _draw_pause_menu(
        self, surface: pygame.Surface,
        selected: int, options: list[str],
    ) -> None:
        overlay = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        font = pygame.font.Font(None, 20)
        title = font.render("PAUSED", True, (255, 255, 255))
        tx = (settings.INTERNAL_WIDTH - title.get_width()) // 2
        surface.blit(title, (tx, 40))

        for i, opt in enumerate(options):
            color = (255, 255, 100) if i == selected else (180, 180, 180)
            prefix = "> " if i == selected else "  "
            text = font.render(f"{prefix}{opt}", True, color)
            ox = (settings.INTERNAL_WIDTH - text.get_width()) // 2
            oy = 80 + i * 24
            surface.blit(text, (ox, oy))

    def _draw_background(
        self, surface: pygame.Surface, stage: StageData, camera: Camera,
    ) -> None:
        bg_layers = stage.background_layers
        bg_names = ("BG_Far", "BG_Mid", "BG_Near")
        for i, bg_surf in enumerate(bg_layers):
            layer_name = bg_names[i] if i < len(bg_names) else "BG_Far"
            off = camera.layer_offset(layer_name)
            bg_w = bg_surf.get_width()
            bg_h = bg_surf.get_height()
            for bx in range(0, settings.INTERNAL_WIDTH, bg_w):
                for by in range(0, settings.INTERNAL_HEIGHT, bg_h):
                    surface.blit(
                        bg_surf,
                        (bx - int(off.x),
                         by - int(off.y)),
                    )

    def _draw_debug(
        self, surface: pygame.Surface,
        stage: StageData, player: Player, camera: Camera,
        paused: bool = False,
    ) -> None:
        cam_offset = camera.offset
        lx = -int(cam_offset.x)
        ly = -int(cam_offset.y)
        font = pygame.font.Font(None, 14)
        y = 4

        for r in stage.collision_rects:
            pygame.draw.rect(surface, (0, 255, 0), (r.x + lx, r.y + ly, r.w, r.h), 1)
        for r in stage.one_way_rects:
            pygame.draw.rect(surface, (0, 128, 255), (r.x + lx, r.y + ly, r.w, r.h), 1)
        for mt in stage.message_triggers:
            r = mt.rect
            pygame.draw.rect(surface, (255, 255, 0), (r.x + lx, r.y + ly, r.w, r.h), 1)
        for hz in stage.hazard_zones:
            r = hz.rect
            pygame.draw.rect(surface, (255, 0, 0), (r.x + lx, r.y + ly, r.w, r.h), 1)
        for dp in stage.death_pits:
            r = dp.rect
            pygame.draw.rect(surface, (255, 0, 128), (r.x + lx, r.y + ly, r.w, r.h), 1)

        for enemy in stage.entity_list:
            if not isinstance(enemy, EnemyBase) or not enemy.is_alive:
                continue
            hb = enemy.hurtbox
            pygame.draw.rect(surface, (255, 128, 0), (hb.x + lx, hb.y + ly, hb.w, hb.h), 1)
            hb2 = enemy.hitbox
            pygame.draw.rect(surface, (255, 0, 0), (hb2.x + lx, hb2.y + ly, hb2.w, hb2.h), 1)

        if hasattr(player, "active_hitbox") and player.active_hitbox is not None:
            hb3 = player.active_hitbox
            pygame.draw.rect(surface, (0, 255, 255), (hb3.x + lx, hb3.y + ly, hb3.w, hb3.h), 1)
        if hasattr(player, "hurtbox"):
            hb4 = player.hurtbox
            pygame.draw.rect(surface, (0, 200, 0), (hb4.x + lx, hb4.y + ly, hb4.w, hb4.h), 1)

        max_hp = getattr(player, "max_health", player.current_health)
        info = [
            f"Pos: ({player.position.x:.0f}, {player.position.y:.0f})",
            f"Vel: ({player.velocity.x:.1f}, {player.velocity.y:.1f})",
            f"State: {player.state}",
            f"HP: {player.current_health}/{max_hp}",
            f"Grounded: {player.is_grounded}",
            f"Paused: {paused}",
        ]
        for line in info:
            txt = font.render(line, True, (255, 255, 255))
            surface.blit(txt, (4, y))
            y += 16
