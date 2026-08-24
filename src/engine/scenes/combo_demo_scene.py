"""
ComboDemoScene — Educational visualization of the Player combo state machine.

Shows:
  - Z → Z → X chain (light → light → heavy)
  - Combo window timer (0.5s)
  - Damage scaling: 1.0x → 1.5x → 2.0x
  - Reset on type change or timeout

Controls:
  Z   — light attack
  X   — heavy attack
  ESC — back to demo menu
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_LARGE,
    FONT_MEDIUM,
    FONT_SMALL,
    draw_bottom_bar,
    draw_top_bar,
    save_png,
)
from src.engine.scenes.demo_layout import area_de_contenido
from src.engine.ui.theme import font

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class ComboDemoScene(BaseScene):
    PANEL_W = 260
    PANEL_H = 160
    #: Radio y grosor heredados del diseño de 320x224. Se conservan como
    #: valores públicos porque hay pruebas que los leen; el dibujado usa las
    #: medidas derivadas del área útil que hay debajo.
    NODE_R = 14
    WINDOW_BAR_H = 8

    # -- medidas derivadas del área útil (AUD-094) ------------------
    _MARGEN_SUPERIOR = 24
    _MARGEN_INFERIOR = 16
    _SALTO = 26
    _ANCHO_BARRA = 460
    _RADIO_NODO = 34
    _SEPARACION_NODOS = 260

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._combo_count: int = 0
        self._combo_timer: float = 0.0
        self._last_type: str = ""
        self._hit_log: list[str] = []
        self._font_large = font(FONT_LARGE)
        self._font_medium = font(FONT_MEDIUM)
        self._font_small = font(FONT_SMALL)

    def on_enter(self) -> None:
        self._combo_count = 0
        self._combo_timer = 0.0
        self._last_type = ""
        self._hit_log = ["Press Z (light) or X (heavy)"]

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        # Decay combo timer
        if self._combo_timer > 0:
            self._combo_timer -= dt
            if self._combo_timer <= 0:
                self._reset_combo("timeout")

        # Inputs
        if im.is_action_pressed(Action.SHORT_ATTACK):
            self._register_hit("SHORT")
        if im.is_action_pressed(Action.LONG_ATTACK):
            self._register_hit("LONG")

        # S — save screenshot
        if im.is_raw_key_pressed(pygame.K_s):
            ss = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
            self.draw(ss)
            save_png("combo", "main", ss)

        if im.is_action_just_pressed(Action.CANCEL):
            self.context.scene_manager.pop()

    def _register_hit(self, atk_type: str) -> None:
        import src.engine.core.settings as settings
        if (self._combo_count > 0
                and self._combo_timer > 0
                and self._last_type == atk_type
                and self._combo_count < settings.COMBO_MAX):
            self._combo_count += 1
        else:
            self._combo_count = 1
        self._combo_timer = settings.COMBO_WINDOW
        self._last_type = atk_type
        idx = min(self._combo_count - 1, len(settings.COMBO_DAMAGE_MULT) - 1)
        mult = settings.COMBO_DAMAGE_MULT[idx]
        label = "Light" if atk_type == "SHORT" else "Heavy"
        self._hit_log.append(f"{label} hit → COMBO x{self._combo_count} ({mult}x)")
        if len(self._hit_log) > 6:
            self._hit_log.pop(0)

    def _reset_combo(self, reason: str) -> None:
        self._combo_count = 0
        self._combo_timer = 0.0
        self._last_type = ""
        if reason:
            self._hit_log.append(f"[{reason}] — reset")

    def _centrado(self, surface: pygame.Surface, texto: pygame.Surface, y: int) -> None:
        """Escribe centrado horizontalmente en el área útil."""
        area = area_de_contenido()
        surface.blit(texto, (area.centerx - texto.get_width() // 2, y))

    def draw(self, surface: pygame.Surface) -> None:
        """Diagrama de la máquina de estados, centrado.

        AUD-094 — la máquina de estados vivía en la esquina
        ---------------------------------------------------
        Esto empezaba en ``x = 20; y = 40`` y bajaba en saltos de 16 a 30 px:
        una columna estrecha pegada al borde izquierdo, escrita para 320x224.
        Medido sobre los 800x600 reales, el contenido ocupaba x[20,273]
        y[43,238] —dos de las nueve celdas de una rejilla 3x3 sobre el área
        útil— y el resto de la pantalla estaba en negro.

        Ahora todo se mide desde el centro del área útil y los nodos se
        dimensionan con ella, que es lo que hace legible el diagrama desde el
        fondo de un aula.
        """
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "COMBO STATE MACHINE", "Demo")

        area = area_de_contenido()
        cx = area.centerx
        y = area.y + self._MARGEN_SUPERIOR

        title = self._font_medium.render("Chain: Z → Z → X", True, COLOR_HIGHLIGHT)
        self._centrado(surface, title, y)
        y += title.get_height() + self._SALTO

        # Barra de la ventana de combo, centrada y del ancho del diagrama
        ancho_barra = self._ANCHO_BARRA
        bx = cx - ancho_barra // 2
        alto_barra = self.WINDOW_BAR_H
        pygame.draw.rect(surface, (60, 60, 80), (bx, y, ancho_barra, alto_barra))
        if self._combo_timer > 0:
            ratio = max(0.0, min(1.0, self._combo_timer / settings.COMBO_WINDOW))
            pygame.draw.rect(surface, COLOR_ACCENT,
                             (bx, y, int(ancho_barra * ratio), alto_barra))
        label = self._font_small.render("Combo window", True, COLOR_TEXT)
        self._centrado(surface, label, y + alto_barra + 6)
        y += alto_barra + label.get_height() + self._SALTO + 6

        # Nodos del diagrama, repartidos alrededor del centro
        radio = self._RADIO_NODO
        separacion = self._SEPARACION_NODOS
        nodes = [("Z", self._last_type == "SHORT"), ("X", self._last_type == "LONG")]
        ny = y + radio
        posiciones = [
            cx - separacion // 2 + i * separacion for i in range(len(nodes))
        ]

        if self._last_type:
            pygame.draw.line(surface, COLOR_ACCENT,
                             (posiciones[0] + radio, ny),
                             (posiciones[1] - radio, ny), 4)

        for (sym, active), nx in zip(nodes, posiciones, strict=True):
            color = COLOR_HIGHLIGHT if active else (80, 80, 100)
            pygame.draw.circle(surface, color, (nx, ny), radio)
            txt = self._font_large.render(sym, True, (20, 20, 20))
            surface.blit(txt, (nx - txt.get_width() // 2, ny - txt.get_height() // 2))

        y = ny + radio + self._SALTO

        count_txt = self._font_large.render(
            f"Combo: x{self._combo_count}" if self._combo_count > 0 else "Combo: —",
            True, COLOR_HIGHLIGHT if self._combo_count > 0 else COLOR_TEXT,
        )
        self._centrado(surface, count_txt, y)
        y += count_txt.get_height() + 6

        idx = min(max(0, self._combo_count - 1), len(settings.COMBO_DAMAGE_MULT) - 1)
        mult = settings.COMBO_DAMAGE_MULT[idx] if self._combo_count > 0 else 1.0
        mult_txt = self._font_medium.render(f"Multiplier: {mult}x", True, COLOR_ACCENT)
        self._centrado(surface, mult_txt, y)
        y += mult_txt.get_height() + self._SALTO

        # El registro se ancla abajo: así no salta cada vez que crece.
        salto_log = self._font_small.get_height() + 4
        registro = self._hit_log[-4:]
        y_log = max(y, area.bottom - self._MARGEN_INFERIOR - salto_log * len(registro))
        for line in registro:
            self._centrado(surface, self._font_small.render(line, True, COLOR_TEXT), y_log)
            y_log += salto_log

        draw_bottom_bar(surface, "Z: Light | X: Heavy | ESC: Back")
