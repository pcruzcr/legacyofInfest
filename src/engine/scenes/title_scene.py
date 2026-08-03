from __future__ import annotations

import math
from typing import TYPE_CHECKING

import orjson
import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.core.user_settings import user_data_dir
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import BOTTOM_BAR_Y

# AUD-188: las cuatro escenas a las que lleva este menu se importan en el
# punto de uso, no aqui. `options_scene` y `demo_menu_scene` arrastran
# numpy, scipy y pygame_gui, y `App()` importa esta pantalla al arrancar:
# eran 1,1 s de importaciones con la ventana ya abierta y en negro, antes
# de que el splash pudiera dibujar su primer fotograma. Las otras seis
# opciones de este mismo menu ya se importaban asi; estas cuatro se
# quedaron arriba.
from src.engine.ui.theme import Theme
from src.engine.ui.widgets import (
    MenuItem,
    MenuList,
    draw_key_hints,
    handle_menu_navigation,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

_tutorial_seen_cache: bool | None = None


class TitleScene(BaseScene):
    """Main title screen with background, logo, music, custom font, and particles."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        assets = settings.ASSETS_DIR / "title"

        self._background = AssetLoader.load_image(
            assets / "bck1.png",
            size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )

        raw_logo = AssetLoader.load_image(assets / "logo.png")
        max_logo_w = settings.INTERNAL_WIDTH - 40
        max_logo_h = 80
        lw, lh = raw_logo.get_size()
        scale = min(max_logo_w / lw, max_logo_h / lh, 1.0)
        self._logo = AssetLoader.load_image(
            assets / "logo.png",
            size=(int(lw * scale), int(lh * scale)),
        )
        self._logo_y_offset: float = 0.0
        self._logo_timer: float = 0.0

        title_wav = assets / "title.wav"
        title_ogg = assets / "title.ogg"
        if title_wav.exists():
            self._music = title_wav
        else:
            self._music = title_ogg

        # AUD-068: navegación y foco vienen del kit compartido. Antes esta
        # pantalla **fijaba** en los extremos (`min`/`max`) mientras el resto
        # del juego da la vuelta: pulsar abajo en la última opción no hacía
        # nada aquí y saltaba a la primera en cualquier otro menú. Es
        # exactamente la incoherencia que el kit existe para eliminar.
        self._menu = MenuList(items=[
            MenuItem("START", value="START"),
            MenuItem("TUTORIAL", value="TUTORIAL"),
            MenuItem("WORLD MAP", value="WORLD MAP"),
            MenuItem("INVENTORY", value="INVENTORY"),
            MenuItem("BESTIARY", value="BESTIARY"),
            MenuItem("ACHIEVEMENTS", value="ACHIEVEMENTS"),
            MenuItem("BOSS RUSH", value="BOSS RUSH"),
            # AUD-202: `LeaderboardScene` existía, estaba registrada y no la
            # abría nadie. Los tiempos de speedrun se cronometraban partida
            # tras partida sin que hubiera una sola pantalla desde la que
            # verlos.
            MenuItem("RECORDS", value="RECORDS"),
            MenuItem("ACADEMIC DEMOS", value="ACADEMIC DEMOS"),
            MenuItem("OPTIONS", value="OPTIONS"),
            MenuItem("QUIT", value="QUIT"),
        ])
        self._scroll_offset: int = 0
        self._recalc_layout()

        self._bar_surf: pygame.Surface | None = None
        # AUD-188: el sistema de partículas se crea al primer uso. Importarlo
        # aquí arrastraba numpy y scipy —`particle_system` los pide a nivel de
        # módulo— y `App()` construye esta pantalla al arrancar, así que era
        # ~1 s de importaciones con la ventana ya abierta y en negro. Las
        # chispas del título son adorno: pueden esperar al primer fotograma.
        self._particle_system: object | None = None
        self._particle_timer: float = 0.0

    def _recalc_layout(self) -> None:
        h = settings.INTERNAL_HEIGHT
        logo_bottom = h // 3 + 20
        available = h - logo_bottom - 16
        n = len(self._menu.items)
        # AUD-187: el techo era `min(18, …)`, un número heredado de cuando la
        # superficie interna medía 320x240. A los 800x600 actuales sobraba
        # sitio —con diez opciones caben 36 px por fila— y el menú principal se
        # dibujaba a 16 px igualmente, más pequeño que el cuerpo de texto del
        # resto del juego. Ahora el techo es la escala del tema y el reparto
        # sólo encoge cuando de verdad no caben.
        deseado = Theme.FONT_BODY + Theme.SPACE_S
        line_h = max(11, min(deseado, available // max(n, 1)))
        self._font_size = max(14, line_h - Theme.SPACE_XS)
        self._font_game = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf",
            self._font_size,
        )
        self._option_spacing = line_h
        self._max_visible = max(1, available // line_h)

    def on_enter(self) -> None:
        self._menu.index = 0
        self._scroll_offset = 0
        self._recalc_layout()
        self._update_options()
        self.context.scene_manager.transition.start_fade_in(0.5)
        audio = self.audio
        if audio is not None:
            audio.play_music(self._music)

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        self._logo_timer += dt
        self._logo_y_offset = 2.0 * (1.0 + 0.5 * (1.0 + math.cos(self._logo_timer * 1.5)))

        self._particle_timer += dt
        if self._particle_timer >= 0.1:
            self._particle_timer = 0.0
            import random

            from src.framework.vfx.hit_effects import HitEffects
            from src.framework.vfx.particle_system import ParticleSystem
            if self._particle_system is None:
                self._particle_system = ParticleSystem()
            self._particle_system.get_emitter("title_spark").emit(
                random.uniform(0, settings.INTERNAL_WIDTH),
                random.uniform(60, settings.INTERNAL_HEIGHT),
                HitEffects.SPARK,
            )
        if self._particle_system is not None:
            self._particle_system.update(dt)

        self._menu.update(dt)
        previous = self._menu.index
        handle_menu_navigation(
            self._menu, im,
            on_confirm=self._on_confirm,
            on_cancel=self._on_cancel,
        )
        if self._menu.index != previous:
            self.context.event_bus.emit(Events.SFX_MENU_HOVER)

        # La lista puede ser más larga que la pantalla, así que la ventana
        # visible sigue al foco. Se recalcula tras navegar, no dentro de la
        # navegación: el kit decide el índice y esta escena decide qué parte
        # de la lista enseña.
        if self._menu.index < self._scroll_offset:
            self._scroll_offset = self._menu.index
        elif self._menu.index >= self._scroll_offset + self._max_visible:
            self._scroll_offset = self._menu.index - self._max_visible + 1

    def _on_confirm(self, item: MenuItem) -> None:
        self.context.event_bus.emit(Events.SFX_MENU_CONFIRM)
        self._activate_option(str(item.value))

    def _on_cancel(self) -> None:
        self.context.event_bus.emit(Events.SFX_MENU_CANCEL)
        self.context.quit()

    def _activate_option(self, opt: str) -> None:
        if opt == "CONTINUE":
            from src.engine.scenes.load_game_scene import LoadGameScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(LoadGameScene(self.context))
        elif opt == "START":
            from src.engine.scenes.story_scene import StoryScene
            from src.engine.scenes.tutorial_scene import TutorialScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            if not self._has_seen_tutorial():
                self._mark_tutorial_seen()
                self.context.scene_manager.replace(TutorialScene(self.context))
            else:
                self.context.scene_manager.replace(StoryScene(self.context, 1))
        elif opt == "TUTORIAL":
            from src.engine.scenes.tutorial_scene import TutorialScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(TutorialScene(self.context))
        elif opt == "WORLD MAP":
            from src.engine.scenes.world_map_scene import WorldMapScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(WorldMapScene(self.context))
        elif opt == "INVENTORY":
            from src.engine.scenes.inventory_scene import InventoryScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(InventoryScene(self.context))
        elif opt == "BESTIARY":
            from src.engine.scenes.bestiary_scene import BestiaryScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(BestiaryScene(self.context))
        elif opt == "ACHIEVEMENTS":
            from src.engine.scenes.achievement_scene import AchievementScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(AchievementScene(self.context))
        elif opt == "BOSS RUSH":
            # AUD-191: `boss_rush_mode` estaba completo y probado desde
            # AUD-022, y su cabecera avisaba de que nada del juego lo
            # construía. Esta rama es la puerta que faltaba.
            #
            # AUD-201 — el orden de estas dos líneas era el revés y dejaba la
            # pantalla en negro.
            #
            # Las otras diez opciones arrancan el fundido y **luego** cambian
            # de pantalla. Ésta entraba al jefe primero y pedía el fundido de
            # salida después, así que el fundido de **entrada** que dispara
            # `replace()` llegaba antes y lo pisaba el de salida.
            #
            # No era un parpadeo: `TransitionManager.update` deja el velo en
            # alfa 255 al terminar un fundido de salida, y `draw` lo pinta
            # siempre que el alfa sea mayor que cero, mire o no si la
            # transición sigue activa. El jefe se cargaba, corría y sonaba
            # debajo de una pantalla negra permanente.
            from src.engine.scenes.boss_rush_entry import empezar_boss_rush
            self.context.scene_manager.transition.start_fade_out(0.4)
            if empezar_boss_rush(self.context) is None:
                # Sin jefes que encadenar no se cambia de pantalla, así que
                # hay que deshacer el fundido o el menú se queda a oscuras.
                self.context.scene_manager.transition.start_fade_in(0.4)
        elif opt == "RECORDS":
            from src.engine.scenes.leaderboard_scene import LeaderboardScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(LeaderboardScene(self.context))
        elif opt == "ACADEMIC DEMOS":
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(DemoMenuScene(self.context))
        elif opt == "OPTIONS":
            from src.engine.scenes.options_scene import OptionsScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(OptionsScene(self.context))
        elif opt == "QUIT":
            self.context.quit()

    def _update_options(self) -> None:
        """Añade o quita CONTINUE según haya partidas guardadas."""
        sm = self.context.save_manager
        labels = [str(item.value) for item in self._menu.items]
        has_continue = "CONTINUE" in labels

        if sm is not None and sm.has_saves():
            if not has_continue:
                self._menu.items.insert(
                    0, MenuItem("CONTINUE", value="CONTINUE",
                                hint="Resume your most recent save"),
                )
        elif has_continue:
            self._menu.items.pop(labels.index("CONTINUE"))

        # Quitar una fila puede dejar el foco fuera de rango.
        self._menu.ensure_valid()

    def _has_seen_tutorial(self) -> bool:
        global _tutorial_seen_cache
        if _tutorial_seen_cache is not None:
            return _tutorial_seen_cache
        flag_path = user_data_dir() / "tutorial_seen.json"
        try:
            data = orjson.loads(flag_path.read_bytes())
            _tutorial_seen_cache = bool(data.get("seen", False))
            return _tutorial_seen_cache
        except (FileNotFoundError, orjson.JSONDecodeError):
            _tutorial_seen_cache = False
            return False

    def _mark_tutorial_seen(self) -> None:
        global _tutorial_seen_cache
        _tutorial_seen_cache = True
        flag_path = user_data_dir() / "tutorial_seen.json"
        flag_path.parent.mkdir(parents=True, exist_ok=True)
        flag_path.write_bytes(orjson.dumps({"seen": True}))

    def on_exit(self) -> None:
        audio = self.audio
        if audio is not None:
            audio.stop_music()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))

        logo_rect = self._logo.get_rect(
            center=(settings.INTERNAL_WIDTH // 2, int(settings.INTERNAL_HEIGHT // 3 + self._logo_y_offset)),
        )
        surface.blit(self._logo, logo_rect)

        if self._particle_system is not None:
            self._particle_system.draw(surface, pygame.Vector2(0, 0))

        self.context.scene_manager.transition.draw(surface)

        # AUD-068: los colores salen del tema. Antes el foco era (255,255,100)
        # y el resto (150,150,150), dos tonos que no aparecen en ninguna otra
        # pantalla; ahora usa el mismo ámbar de acento y el mismo gris de texto
        # que el resto del juego. El fondo NO se toca: esta pantalla tiene arte
        # propio, y migrar no es sustituir el arte por una pantalla genérica.
        start_y = logo_rect.bottom + 8
        end = self._scroll_offset + self._max_visible
        visible = self._menu.items[self._scroll_offset:end]
        for idx, item in enumerate(visible):
            i = self._scroll_offset + idx
            focused = i == self._menu.index
            color = Theme.ACCENT if focused else Theme.TEXT_MUTED
            text = self._font_game.render(item.label, True, color)
            ox = (settings.INTERNAL_WIDTH - text.get_width()) // 2
            oy = start_y + idx * self._option_spacing
            if oy + self._font_size > settings.INTERNAL_HEIGHT:
                continue
            if focused:
                pad = 4
                bw, bh = text.get_width() + pad * 2, text.get_height()
                if self._bar_surf is None or self._bar_surf.get_size() != (bw, bh):
                    self._bar_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
                bar_surf = self._bar_surf
                bar_surf.fill((*Theme.SURFACE_RAISED, 140))
                surface.blit(bar_surf, (ox - pad, oy))
            surface.blit(text, (ox, oy))

        # AUD-068: la pantalla principal del juego no decía qué teclas usar.
        draw_key_hints(surface, [
            ("↑↓", "Mover"),
            ("Enter", "Seleccionar"),
            ("Esc", "Salir"),
        ])

        if self._scroll_offset > 0:
            pygame.draw.polygon(surface, (200, 200, 200), [
                (settings.INTERNAL_WIDTH // 2, start_y - 4),
                (settings.INTERNAL_WIDTH // 2 - 6, start_y - 10),
                (settings.INTERNAL_WIDTH // 2 + 6, start_y - 10),
            ])
        if self._scroll_offset + self._max_visible < len(self._menu.items):
            bot = BOTTOM_BAR_Y - 2
            pygame.draw.polygon(surface, (200, 200, 200), [
                (settings.INTERNAL_WIDTH // 2, bot),
                (settings.INTERNAL_WIDTH // 2 - 6, bot + 6),
                (settings.INTERNAL_WIDTH // 2 + 6, bot + 6),
            ])

