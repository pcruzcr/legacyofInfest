"""
Module: story_scene
System: engine.scenes
Academic Unit: N/A
Description: Story text screen. Displays narrative text that advances
on CONFIRM. After 3 story scenes, loads stages via StageRegistry.
"""
from __future__ import annotations
import pygame
from src.engine.scene.base_scene import BaseScene
from src.engine.core import settings
from src.engine.input.action_map import Action

# Story text for the three narrative screens
STORY_TEXTS: dict[int, tuple[str, str]] = {
    1: (
        "CAPITULO I: EL LEGADO",
        "En las tierras de Tilawa, un antiguo mal despierta.\n"
        "Los espiritus de la naturaleza claman justicia.\n"
        "Un guerrero surge para enfrentar la oscuridad."
    ),
    2: (
        "CAPITULO II: EL CAMINO",
        "A traves de bosques ancestrales y ruinas olvidadas,\n"
        "el viajero debe recolectar los fragmentos del poder\n"
        "que yacen dispersos por las cuatro zonas."
    ),
    3: (
        "CAPITULO III: EL DESTINO",
        "El gran colibri vigila desde las alturas.\n"
        "La serpiente custodia los secretos de la tierra.\n"
        "El venado guia a los valientes hacia su destino."
    ),
}


class StoryScene(BaseScene):
    """Narrative story screen."""

    def __init__(self, chapter: int) -> None:
        self._chapter: int = chapter
        self._font_title = pygame.font.Font(None, 20)
        self._font_text = pygame.font.Font(None, 14)
        self._font_hint = pygame.font.Font(None, 11)

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def _get_input(self):
        from src.engine.core.app import App
        if App._instance is not None:
            return App._instance.input_manager
        return None

    def update(self, dt: float) -> None:
        im = self._get_input()
        if im is None:
            return

        if im.is_pressed(Action.CONFIRM):
            if self._chapter < 3:
                from src.engine.core.app import App
                if App._instance is not None:
                    App._instance.scene_manager.replace(StoryScene(self._chapter + 1))
            else:
                # After chapter 3, load stages
                from src.engine.core.app import App
                from src.engine.core.stage_registry import discover_stages
                from src.engine.scene.base_scene import BaseScene
                if App._instance is not None:
                    stages = discover_stages()
                    if stages:
                        App._instance.scene_manager.set_stage_queue(stages)
                        App._instance.scene_manager.replace(stages[0]())
                    else:
                        # No stages found — fallback placeholder
                        class EmptyStage(BaseScene):
                            def on_enter(self): pass
                            def on_exit(self): pass
                            def update(self, dt): pass
                            def draw(self, surface):
                                surface.fill(settings.BG_COLOR)
                                f = pygame.font.Font(None, 16)
                                t = f.render("No stages found. Add a stage in src/stages/", True, (255,255,200))
                                surface.blit(t, (10, 100))
                        App._instance.scene_manager.replace(EmptyStage())

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((10, 10, 25))

        title, text = STORY_TEXTS.get(self._chapter, ("DESCONOCIDO", ""))
        title_surf = self._font_title.render(title, True, (200, 200, 255))
        tx = (settings.INTERNAL_WIDTH - title_surf.get_width()) // 2
        surface.blit(title_surf, (tx, 30))

        # Render text lines
        lines = text.split("\n")
        y = 70
        for line in lines:
            text_surf = self._font_text.render(line, True, (200, 200, 200))
            text_x = (settings.INTERNAL_WIDTH - text_surf.get_width()) // 2
            surface.blit(text_surf, (text_x, y))
            y += 22

        hint = self._font_hint.render("Presiona CONFIRM para continuar", True, (100, 100, 150))
        hx = (settings.INTERNAL_WIDTH - hint.get_width()) // 2
        surface.blit(hint, (hx, settings.INTERNAL_HEIGHT - 25))
