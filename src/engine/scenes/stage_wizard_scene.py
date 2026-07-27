"""
StageWizardScene — Interactive Stage Builder Wizard.

Guides students step-by-step through creating a TMX stage.
Each step explains what to do and shows examples.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    BOTTOM_BAR_Y,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_MEDIUM,
    FONT_SMALL,
    TOP_BAR_H,
    draw_bottom_bar,
    draw_top_bar,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


def _tile_size() -> int:
    """Tamaño de tile real del motor.

    Se lee de `settings` en vez de escribirlo aquí. La versión anterior decía
    «32x32 pixels» mientras `stage0.tmx`, la plantilla del estudiante y
    `docs/06_TMX_SPEC.md` usaban 16: quien siguiera el asistente construía un
    mapa al doble de escala y no había forma de que se enterara hasta verlo
    mal en pantalla (AUD-057).
    """
    return settings.TILE_SIZE


def _required_layers() -> str:
    """Las capas que `StageLoader` exige, leídas del propio cargador.

    El asistente pedía crear sólo `Terrain`. Cargar ese mapa fallaba con
    `Missing required layer: BG_Far` — un error correcto sobre un paso que el
    asistente nunca mandó dar.
    """
    from src.framework.stage.stage_loader import REQUIRED_LAYERS

    return ", ".join(REQUIRED_LAYERS)


def _enemy_examples(count: int = 6) -> str:
    """Algunos tipos de enemigo válidos, tomados del registro real."""
    from src.framework.entities import entity_factory
    from src.framework.stage.stage_loader import StageLoader

    entity_factory.ensure_registered()
    names = sorted(StageLoader._entity_registry)
    return ", ".join(names[:count]) + f" … ({len(names)} en total)"


WIZARD_STEPS = [
    {
        "title": "Paso 1: Crear el mapa en Tiled",
        "instruction": "Archivo > Nuevo > Nuevo mapa.",
        "details": [
            "Orientación: Ortogonal · Orden de dibujo: Right-down",
            f"Tamaño de tile: {_tile_size()}x{_tile_size()} px (el del motor)",
            "Tamaño del mapa: desde 40x23 tiles; «Infinito» desactivado",
            "Guárdalo en assets/maps/<tu_id>/<tu_id>.tmx",
        ],
    },
    {
        "title": "Paso 2: Añadir el tileset",
        "instruction": "Mapa > Añadir tileset externo.",
        "details": [
            "Usa un .tsx existente o crea uno desde tu PNG",
            f"El tamaño de tile del tileset debe ser {_tile_size()}x{_tile_size()}",
            "La ruta al tileset debe ser RELATIVA al .tmx",
            "Si la ruta es absoluta, el mapa no abrirá en otro ordenador",
        ],
    },
    {
        "title": "Paso 3: Crear las 8 capas obligatorias",
        "instruction": "El cargador exige estas capas, en este orden.",
        "details": [
            "Capas de tiles: BG_Far, BG_Mid, BG_Near,",
            "  Terrain, Terrain_Detail, FG_Overlay",
            "Capas de objetos: Objects, Collision",
            "Si falta una, el escenario no carga y te lo dirá por su nombre",
        ],
    },
    {
        "title": "Paso 4: Pintar el terreno",
        "instruction": "Dibuja el suelo en la capa 'Terrain'.",
        "details": [
            "Terrain es lo que se ve; Collision es lo que frena al jugador",
            "En 'Collision' dibuja rectángulos sobre el suelo sólido",
            "Los rectángulos de Collision no necesitan type",
            "Pon paredes en los bordes o el jugador se saldrá del mapa",
        ],
    },
    {
        "title": "Paso 5: Punto de aparición",
        "instruction": "Un objeto punto con type=PlayerSpawn en 'Objects'.",
        "details": [
            "Clic derecho > Insertar punto, en la capa Objects",
            "En el panel de propiedades, campo Type (o Class): PlayerSpawn",
            "La Y es la posición de los PIES del jugador",
            "Exactamente uno: con dos, el escenario no carga",
        ],
    },
    {
        "title": "Paso 6: Puntos de control",
        "instruction": "Objetos con type=Checkpoint y su checkpoint_id.",
        "details": [
            "Añade un objeto rectángulo en 'Objects'",
            "Type: Checkpoint",
            "Propiedad int OBLIGATORIA: checkpoint_id (0, 1, 2…)",
            "Sin checkpoint_id el escenario no carga",
        ],
    },
    {
        "title": "Paso 7: Enemigos",
        "instruction": "Objetos punto en 'Objects', NO una capa de tiles.",
        "details": [
            "Inserta un punto y ponle el Type del enemigo",
            f"Tipos: {_enemy_examples()}",
            "Distingue mayúsculas: «walker» no es «Walker»",
            "Ajusta patrol_length, max_health… como propiedades del objeto",
        ],
    },
    {
        "title": "Paso 8: Salida y peligros",
        "instruction": "Rectángulos en 'Objects' con su type.",
        "details": [
            "NextTrigger: rectángulo que completa el escenario",
            "DeathPit: caer aquí mata al jugador",
            "HazardZone: daña al tocarla (propiedad float 'damage')",
            "CameraLock: fija la cámara (lock_x / lock_y)",
        ],
    },
    {
        "title": "Paso 9: Propiedades del mapa",
        "instruction": "Mapa > Propiedades del mapa, botón +.",
        "details": [
            "string stage_id — p. ej. 'stage1_2'",
            "string stage_name — el nombre que verá el jugador",
            "string bgm_track — música de fondo",
            "int zone (1-8) · int time_limit (0 = sin límite)",
        ],
    },
    {
        "title": "Paso 10: Validar y jugar",
        "instruction": "Comprueba el mapa antes de escribir código.",
        "details": [
            "python scripts/validate_tmx.py assets/maps/<tu_id>/<tu_id>.tmx",
            "Copia student_templates/stage_template a src/stages/<tu_id>/",
            "Cambia STAGE_ID, STAGE_NAME, ZONE y TMX_PATH",
            "python main.py --stage <tu_id>",
        ],
    },
]


BACK_COLOR = (30, 30, 60)
ACCENT_BRIGHT = (255, 200, 50)


class StageWizardScene(BaseScene):
    """10-step interactive wizard that guides students through creating a TMX stage in Tiled."""

    def __init__(self, context: GameContext) -> None:
        """Load fonts and initialize step counter."""
        super().__init__(context)
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)
        self._step: int = 0

    def on_enter(self) -> None:
        """Reset to step 0 when entering the wizard."""
        self._step = 0

    def on_exit(self) -> None:
        """Cleanup on exit."""

    def update(self, dt: float) -> None:
        """Handle navigation: LEFT/RIGHT/SPACE to move between steps, ESC to exit."""
        im = self.input
        if im is None:
            return

        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        if im.is_raw_key_pressed(pygame.K_RIGHT):
            self._step = min(self._step + 1, len(WIZARD_STEPS) - 1)

        if im.is_raw_key_pressed(pygame.K_LEFT):
            self._step = max(self._step - 1, 0)

        if im.is_raw_key_pressed(pygame.K_SPACE):
            self._step = min(self._step + 1, len(WIZARD_STEPS) - 1)

    def draw(self, surface: pygame.Surface) -> None:
        """Render the current wizard step: title, instruction, bullet details, progress bar."""
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "STAGE BUILDER WIZARD", "ONBOARDING")

        step = WIZARD_STEPS[self._step]

        title_y = TOP_BAR_H + 12
        title = self._font_medium.render(f"  {step['title']}", True, ACCENT_BRIGHT)
        surface.blit(title, (8, title_y))

        instr_y = title_y + 28
        instr = self._font_medium.render(f"  {step['instruction']}", True, COLOR_HIGHLIGHT)
        surface.blit(instr, (8, instr_y))

        detail_y = instr_y + 24
        for line in step["details"]:
            color = COLOR_ACCENT if any(kw in line for kw in ["Run:", "Save", "python"]) else COLOR_TEXT
            txt = self._font_small.render(f"  * {line}", True, color)
            surface.blit(txt, (16, detail_y))
            detail_y += 16

        bar_y = BOTTOM_BAR_Y - 50
        bar_w = settings.INTERNAL_WIDTH - 40
        bar_x = 20
        progress = (self._step + 1) / len(WIZARD_STEPS)

        pygame.draw.rect(surface, (40, 40, 60), (bar_x, bar_y, bar_w, 12))
        if progress > 0:
            pygame.draw.rect(surface, ACCENT_BRIGHT, (bar_x, bar_y, int(bar_w * progress), 12))

        progress_text = self._font_small.render(
            f"  Step {self._step + 1}/{len(WIZARD_STEPS)} ({int(progress * 100)}%)",
            True, COLOR_HIGHLIGHT)
        surface.blit(progress_text, (bar_x + 4, bar_y - 14))

        hint = self._font_medium.render(
            "  LEFT/RIGHT or SPACE to navigate  |  ESC to exit", True, COLOR_ACCENT)
        surface.blit(hint, (8, bar_y - 30))

        draw_bottom_bar(surface, "  LEFT/RIGHT: navigate  SPACE: next  ESC: exit")
