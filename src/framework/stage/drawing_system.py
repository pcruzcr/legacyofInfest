from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.ui.hud import HUD
    from src.engine.ui.message_box import MessageBox
    from src.engine.ui.screen_banner import ScreenBanner
    from src.framework.entities.player import Player
    from src.framework.stage.camera import Camera
    from src.framework.stage.stage_loader import StageData
    from src.framework.ui.dialogue_system import DialogueSystem
    from src.framework.ui.learning_overlay import LearningOverlay
    from src.framework.ui.tutorial_overlay import TutorialOverlay
    from src.framework.vfx.ambient_particles import AmbientParticleSystem
    from src.framework.vfx.damage_numbers import DamageNumberManager
    from src.framework.vfx.particle_system import ParticleSystem
    from src.framework.vfx.trail_system import TrailSystem
    from src.framework.vfx.weather_system import WeatherSystem


@dataclass
class DrawContext:
    surface: pygame.Surface
    stage: StageData | None = None
    player: Player | None = None
    checkpoints: list[Any] | None = None
    camera: Camera | None = None
    hud: HUD | None = None
    msg_box: MessageBox | None = None
    banner: ScreenBanner | None = None
    paused: bool = False
    pause_selected: int = 0
    pause_options: list[str] | None = None
    particle_system: ParticleSystem | None = None
    damage_numbers: DamageNumberManager | None = None
    ambient_particles: AmbientParticleSystem | None = None
    weather_system: WeatherSystem | None = None
    trail_system: TrailSystem | None = None
    tutorial_overlay: TutorialOverlay | None = None
    learning_overlay: LearningOverlay | None = None
    dialogue_system: DialogueSystem | None = None
    debug: bool = False


class DrawingSystem:
    def __init__(self) -> None:
        self._bg_tiles: dict[tuple[int, int, int], pygame.Surface] = {}
        self._pause_overlay: pygame.Surface | None = None
        self._pause_font = pygame.font.Font(None, 20)
        self._debug_font = pygame.font.Font(None, 14)

    def draw(self, ctx: DrawContext) -> None:
        surface = ctx.surface
        stage = ctx.stage
        player = ctx.player
        checkpoints = ctx.checkpoints or []
        camera = ctx.camera
        hud = ctx.hud
        msg_box = ctx.msg_box
        banner = ctx.banner

        surface.fill(settings.BG_COLOR)

        if stage is None:
            return

        if camera is None:
            return

        offset = camera.offset

        # Draw order, back to front. Parallax backdrops first, then the tile
        # map, then world-space effects, then entities, then screen-space UI.
        self._draw_background(surface, stage, camera)
        self._draw_stage_layers(surface, stage, camera)

        if ctx.particle_system:
            ctx.particle_system.draw(surface, offset)
        if ctx.weather_system:
            ctx.weather_system.draw(surface, offset)
        if ctx.ambient_particles:
            ctx.ambient_particles.draw(surface, offset)

        if ctx.learning_overlay:
            ctx.learning_overlay.draw(surface)
        if ctx.tutorial_overlay:
            ctx.tutorial_overlay.draw(surface)

        self._draw_entities(surface, stage, offset)

        if ctx.trail_system:
            ctx.trail_system.draw(surface, offset)
        if ctx.damage_numbers:
            ctx.damage_numbers.draw(surface, offset)
        if ctx.dialogue_system:
            # Screen-space, not world-space: the dialogue box is anchored to the
            # viewport, so it takes no camera offset (AUD-039).
            ctx.dialogue_system.draw(surface)

        if checkpoints:
            self._draw_checkpoints(surface, checkpoints, offset)

        if hud:
            hud.draw(surface)
        if msg_box:
            msg_box.draw(surface)
        if banner:
            banner.draw(surface)

        if ctx.paused:
            self._draw_pause_menu(surface, ctx.pause_selected, ctx.pause_options or [])

        if ctx.debug:
            self._draw_debug(surface, stage, player, camera, offset)

    # Parallax speed per backdrop layer, far to near. Index 0 is the most
    # distant layer and therefore moves least.
    _PARALLAX_FACTORS: tuple[float, ...] = (0.15, 0.35, 0.6, 0.8)

    def _draw_background(
        self, surface: pygame.Surface, stage: StageData, camera: Camera,
    ) -> None:
        """Blit the parallax backdrop layers behind the tile map.

        Rewritten (AUD-039). The previous implementation called
        ``stage.draw_background(...)`` guarded by ``hasattr`` — and ``StageData``
        has no such method, so the guard was permanently False and no backdrop
        was ever drawn. A second helper iterated ``stage.background_objects``,
        an attribute that does not exist either, which is what raised
        ``AttributeError`` on the first gameplay frame.

        What the loader actually produces is ``stage.background_layers``: a list
        of ``pygame.Surface`` ordered far to near. That is what we draw.
        """
        layers = getattr(stage, "background_layers", None)
        if not layers:
            return

        view_w = surface.get_width()
        view_h = surface.get_height()
        for index, layer in enumerate(layers):
            if not isinstance(layer, pygame.Surface):
                continue
            factor = self._PARALLAX_FACTORS[min(index, len(self._PARALLAX_FACTORS) - 1)]
            layer_w = layer.get_width()
            if layer_w <= 0:
                continue
            # Wrap horizontally so a layer narrower than the map still tiles
            # across the whole viewport instead of leaving a gap.
            shift = int(camera.offset.x * factor) % layer_w
            y = int(-camera.offset.y * factor * 0.5)
            x = -shift
            while x < view_w:
                surface.blit(layer, (x, y))
                x += layer_w
            if layer.get_height() < view_h:
                # Extend the last row of the layer down to the bottom edge so a
                # short backdrop does not expose the clear colour.
                surface.blit(layer, (x - layer_w, y + layer.get_height()))

    def _draw_stage_layers(
        self, surface: pygame.Surface, stage: StageData, camera: Camera,
    ) -> None:
        """Render the tile map.

        AUD-039: this used to look for ``stage.tile_layer`` and
        ``stage.top_layer``, neither of which exists. ``StageLoader`` builds a
        ``pyscroll.PyscrollGroup`` and stores it as ``stage.map_layer``; nothing
        in the codebase ever drew it, so **the tile map has never appeared on
        screen**. Both lookups used ``getattr(..., None)`` and silently did
        nothing, which is why this went unnoticed for so long — a missing
        attribute raises, a defaulted one just quietly renders an empty world.
        """
        map_layer = getattr(stage, "map_layer", None)
        if map_layer is None:
            return

        # pyscroll centres on a world point; the camera stores a top-left
        # offset, so convert.
        centre = (
            int(camera.offset.x + surface.get_width() // 2),
            int(camera.offset.y + surface.get_height() // 2),
        )
        try:
            map_layer.center(centre)
            # PyscrollGroup.draw takes only the target surface.
            map_layer.draw(surface)
        except (AttributeError, TypeError, pygame.error):
            # A stage built without a real pyscroll group (tests, student
            # templates in progress) must not take the whole frame down. Logged
            # at warning, not debug: if the map stops rendering in a real build
            # that is a headline failure, and burying it at debug is how the
            # previous silent-getattr version hid the same problem (AUD-039).
            logger.warning(
                "DrawingSystem: tile map could not be drawn — the world will "
                "render empty", exc_info=True,
            )

    def _draw_entities(
        self, surface: pygame.Surface, stage: StageData, offset: pygame.Vector2,
    ) -> None:
        for entity in stage.entity_list:
            if entity is None or not entity.is_visible or not entity.is_alive:
                continue
            entity.draw(surface, offset)

    def _draw_checkpoints(
        self, surface: pygame.Surface, checkpoints: list[Any], offset: pygame.Vector2,
    ) -> None:
        for cp in checkpoints:
            if hasattr(cp, 'draw'):
                cp.draw(surface, offset)

    def _draw_pause_menu(
        self, surface: pygame.Surface, selected: int, options: list[str],
    ) -> None:
        if self._pause_overlay is None:
            self._pause_overlay = pygame.Surface(
                (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
            )
        self._pause_overlay.set_alpha(160)
        self._pause_overlay.fill((0, 0, 0))
        surface.blit(self._pause_overlay, (0, 0))

        cx = settings.INTERNAL_WIDTH // 2
        cy = settings.INTERNAL_HEIGHT // 2 - (len(options) * 30) // 2
        for i, opt in enumerate(options):
            color = (255, 255, 100) if i == selected else (200, 200, 200)
            label = f"> {opt}" if i == selected else f"  {opt}"
            text = self._pause_font.render(label, True, color)
            surface.blit(text, (cx - text.get_width() // 2, cy + i * 30))

    def _draw_debug(
        self, surface: pygame.Surface, stage: StageData | None,
        player: Player | None, camera: Camera, offset: pygame.Vector2,
    ) -> None:
        if stage is None:
            return
        for entity in stage.entity_list:
            if entity is None:
                continue
            screen_x = int(entity.position.x - offset.x)
            screen_y = int(entity.position.y - offset.y)
            rect = getattr(entity, 'rect', None)
            if rect is not None:
                pygame.draw.rect(surface, (0, 255, 0), (screen_x, screen_y, rect.width, rect.height), 1)
            hurtbox = getattr(entity, 'hurtbox', None)
            if hurtbox is not None:
                hx = int(hurtbox.x - offset.x)
                hy = int(hurtbox.y - offset.y)
                pygame.draw.rect(surface, (255, 0, 0), (hx, hy, hurtbox.width, hurtbox.height), 1)
            hitbox = getattr(entity, 'hitbox', None)
            if hitbox is not None:
                hx2 = int(hitbox.x - offset.x)
                hy2 = int(hitbox.y - offset.y)
                pygame.draw.rect(surface, (0, 0, 255), (hx2, hy2, hitbox.width, hitbox.height), 1)
        if player is not None and hasattr(player, 'rect') and player.rect is not None:
            px = int(player.position.x - offset.x)
            py = int(player.position.y - offset.y)
            pygame.draw.rect(surface, (0, 255, 255), (px, py, player.rect.width, player.rect.height), 2)

        fps = self._debug_font.render(f"Entities: {len(stage.entity_list)}", True, (255, 255, 255))
        surface.blit(fps, (5, settings.INTERNAL_HEIGHT - 60))
        cam_pos = self._debug_font.render(f"Cam: {int(offset.x)},{int(offset.y)}", True, (255, 255, 255))
        surface.blit(cam_pos, (5, settings.INTERNAL_HEIGHT - 40))
