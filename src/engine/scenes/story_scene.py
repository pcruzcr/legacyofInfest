from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import BOTTOM_BAR_Y
from src.engine.ui.theme import Theme, font
from src.engine.ui.widgets import draw_screen
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
        self._font = font(Theme.FONT_SMALL)

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        # AUD-069: esto es un mensaje de error para quien monta el juego, así
        # que usa la pantalla estándar y dice **qué hacer**, no sólo qué falta.
        y = draw_screen(
            surface, "NO HAY ESCENARIOS",
            "El registro no encontró ninguno que cargar",
        )
        for line in (
            "Añade tu escenario en src/stages/<tu_id>/<tu_id>.py",
            "y regístralo en STAGE_ORDER (engine/core/stage_registry.py).",
            "Puedes partir de student_templates/stage_template.",
        ):
            text = self._font.render(line, True, Theme.TEXT_MUTED)
            surface.blit(text, (Theme.MARGIN, y + Theme.SPACE_L))
            y += 20


class StoryScene(BaseScene):
    """Narrative story screen with chapter background and music."""

    def __init__(self, context: GameContext, chapter: int) -> None:
        super().__init__(context)
        self._chapter: int = chapter
        self._assets = settings.ASSETS_DIR / "story"
        self._typewriter_timer: float = 0.0
        self._typewriter_speed: float = 0.04
        self._pending_transition: bool = False

        bg_filename = STORY_BG.get(chapter)
        if bg_filename is None:
            bg_filename = "h01.png"
        self._background = AssetLoader.load_image(
            self._assets / bg_filename,
            size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )

        self._music = self._assets / "story.wav"

        # AUD-436 — por `theme.font()`, no por `AssetLoader.load_font()`.
        #
        # Las dos cargan el mismo `game.ttf`; la diferencia es que sólo la
        # primera pasa por `escalar_texto`. Con la carga directa, el aviso
        # «Presiona CONFIRM para continuar» medía 7 px de tinta real y seguía
        # midiendo 7 px con la accesibilidad al 200 %: es la pantalla en la
        # que desemboca el tutorial, y era ilegible sin forma de arreglarlo
        # desde Opciones.
        #
        # Los tamaños suben a los tokens del tema en vez de quedarse en
        # 20/14/11. `game.ttf` entrega bastante menos alto del que se le pide
        # (AUD-203), así que 11 px no eran 11 px de letra sino 7; el token
        # `FONT_TINY` es el mínimo que este proyecto ya considera legible.
        self._font_title = font(Theme.FONT_HEADING)
        self._font_text = font(Theme.FONT_SMALL)
        self._font_hint = font(Theme.FONT_TINY)

    def on_enter(self) -> None:
        if self._chapter == 1:
            audio = self.audio
            if audio is not None:
                audio.play_music(self._music)
        self.context.scene_manager.transition.start_fade_in(0.5)

    def on_exit(self) -> None:
        if self._chapter == 3:
            audio = self.audio
            if audio is not None:
                audio.stop_music()

    def _advance(self) -> None:
        if self._chapter < 3:
            self.context.scene_manager.replace(StoryScene(self.context, self._chapter + 1))
        else:
            from src.engine.core.stage_registry import discover_stages
            stages = discover_stages()
            if stages:
                self.context.scene_manager.set_stage_queue(stages)
                self.context.scene_manager.replace(stages[0](self.context))
            else:
                self.context.scene_manager.replace(EmptyFallbackStage(self.context))

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._pending_transition:
            if self.context.scene_manager.transition.finished:
                self._advance()
            return

        self._typewriter_timer -= dt

        if im.is_action_just_pressed(Action.CONFIRM):
            duration = 0.6 if self._chapter == 3 else 0.5
            self.context.scene_manager.transition.start_fade_out(duration)
            self._pending_transition = True
            if self._chapter == 3:
                if self.audio is not None:
                    self.audio.stop_music()

    def _alto_de_linea(self) -> int:
        """Separación entre renglones del cuerpo, sacada de la fuente.

        AUD-436 — era `y += 22`, una constante escrita cuando el cuerpo medía
        14 px y nunca crecía. Al pasar la tipografía por `theme.font()` sí
        crece, y con el texto al 200 % cada renglón invadía el siguiente: se
        habría cambiado un texto ilegible por pequeño por otro ilegible por
        solaparse.

        El holgor es proporcional y no fijo por el mismo motivo: 4 px de aire
        entre líneas de 34 px se leen apretados aunque entre líneas de 14 px
        sobraran.
        """
        alto = self._font_text.get_height()
        return alto + max(4, alto // 4)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))

        title, text = STORY_TEXTS.get(self._chapter, ("DESCONOCIDO", ""))

        if not hasattr(self, "_typewriter_full"):
            self._typewriter_full = False
            self._typewriter_buffer = ""
        if not self._typewriter_full:
            if self._typewriter_timer <= 0:
                self._typewriter_timer = self._typewriter_speed
                if len(self._typewriter_buffer) < len(text):
                    self._typewriter_buffer = text[: len(self._typewriter_buffer) + 1]
                else:
                    self._typewriter_full = True
        display_text = self._typewriter_buffer

        title_surf = self._font_title.render(title, True, (255, 255, 240))
        tx = (settings.INTERNAL_WIDTH - title_surf.get_width()) // 2
        surface.blit(title_surf, (tx, 30))

        lines = display_text.split("\n")
        y = 70
        paso = self._alto_de_linea()
        for line in lines:
            text_surf = self._font_text.render(line, True, (240, 240, 230))
            text_x = (settings.INTERNAL_WIDTH - text_surf.get_width()) // 2
            surface.blit(text_surf, (text_x, y))
            y += paso

        if self._typewriter_full:
            hint = self._font_hint.render("Presiona CONFIRM para continuar", True, (180, 180, 160))
            hx = (settings.INTERNAL_WIDTH - hint.get_width()) // 2
            surface.blit(hint, (hx, BOTTOM_BAR_Y - 21))

        self.context.scene_manager.transition.draw(surface)

