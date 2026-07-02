from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.stage_registry import discover_stages
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


STORY_TEXTS: dict[int, tuple[str, str]] = {
    1: (
        "CAPITULO I: EL LEGADO",
        "En las tierras de Tilawa, un antiguo mal despierta.\n"
        "Los espiritus de la naturaleza claman justicia.\n"
        "Un guerrero surge para enfrentar la oscuridad.",
    ),
    2: (
        "CAPITULO II: EL CAMINO",
        "A traves de bosques ancestrales y ruinas olvidadas,\n"
        "el viajero debe recolectar los fragmentos del poder\n"
        "que yacen dispersos por las cuatro zonas.",
    ),
    3: (
        "CAPITULO III: EL DESTINO",
        "El gran colibri vigila desde las alturas.\n"
        "La serpiente custodia los secretos de la tierra.\n"
        "El venado guia a los valientes hacia su destino.",
    ),
}

STORY_BG: dict[int, str] = {1: "h01.png", 2: "h02.png", 3: "h03.png"}


class EmptyFallbackStage(BaseScene):
    """Shown when no stages are discovered in src/stages/."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(settings.BG_COLOR)
        f = pygame.font.Font(None, 16)
        t = f.render("No stages found. Add a stage in src/stages/", True, (255, 255, 200))
        surface.blit(t, (10, 100))


class StoryScene(BaseScene):
    """Narrative story screen with chapter background and music."""

    def __init__(self, context: GameContext, chapter: int) -> None:
        super().__init__(context)
        self._chapter: int = chapter
        self._assets = settings.ASSETS_DIR / "story"

        self._background = AssetLoader.load_image(
            self._assets / STORY_BG[chapter],
            size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )

        self._music = self._assets / "story.wav"

        self._font_title = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", 20)
        self._font_text = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", 14)
        self._font_hint = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", 11)

    def on_enter(self) -> None:
        if self._chapter == 1:
            audio = self.audio
            if audio is not None:
                audio.play_music(self._music)

    def on_exit(self) -> None:
        if self._chapter == 3:
            audio = self.audio
            if audio is not None:
                audio.stop_music()

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if im.is_action_pressed(Action.CONFIRM):
            if self._chapter < 3:
                self.context.scene_manager.replace(StoryScene(self.context, self._chapter + 1))
            else:
                stages = discover_stages()
                if stages:
                    self.context.scene_manager.set_stage_queue(stages)
                    self.context.scene_manager.replace(stages[0](self.context))
                else:
                    self.context.scene_manager.replace(EmptyFallbackStage(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))

        title, text = STORY_TEXTS.get(self._chapter, ("DESCONOCIDO", ""))
        title_surf = self._font_title.render(title, True, (255, 255, 240))
        tx = (settings.INTERNAL_WIDTH - title_surf.get_width()) // 2
        surface.blit(title_surf, (tx, 30))

        lines = text.split("\n")
        y = 70
        for line in lines:
            text_surf = self._font_text.render(line, True, (240, 240, 230))
            text_x = (settings.INTERNAL_WIDTH - text_surf.get_width()) // 2
            surface.blit(text_surf, (text_x, y))
            y += 22

        hint = self._font_hint.render("Presiona CONFIRM para continuar", True, (180, 180, 160))
        hx = (settings.INTERNAL_WIDTH - hint.get_width()) // 2
        surface.blit(hint, (hx, settings.INTERNAL_HEIGHT - 25))
