"""
VectorLabScene — Interactive Vector Mathematics Laboratory

Teaches Unit II concepts:
  - Vector arithmetic (addition, subtraction, scaling)
  - Vector normalization (unit vectors)
  - Dot product and angle between vectors
  - Distance calculation
  - Pursuit movement using normalized vectors

Controls:
  arrows      — move Player
  WASD        — move Enemy target
  TAB         — cycle visualization mode
  N           — toggle normalized vector display
  R           — reset positions
  ESC         — back to demo menu
"""
from __future__ import annotations

import math
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
from src.engine.scenes.demo_layout import (
    AUTHORED_H,
    AUTHORED_W,
    Lienzo,
    area_con_columna,
)
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.math_utils import vec2_dot

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

from src.engine.scenes.code_panel import CodePanel
from src.engine.scenes.quiz_system import QuizManager
from src.engine.scenes.tutorial_overlay import TutorialOverlay

# Responsive layout offsets (resolvable to demo_layout constants)
_MARGIN = 8
#: Ancho de la columna de lecturas numéricas (AUD-094).
_ANCHO_COLUMNA = 290
_CONTENT_TOP = TOP_BAR_H + 4
_PANEL_TOP = TOP_BAR_H

MODE_NAMES = ["FREE MOVE", "CHASE (normalized)", "ORBIT (dot product)", "DISTANCE CHECK"]

VECTOR_QUIZZES = [
    {"question": "What does Vector2.normalize() return?", "options": ["A zero vector", "A unit vector (length=1)", "The vector scaled by 2", "The vector's angle"], "answer": 1},
    {"question": "What is the dot product of two perpendicular vectors?", "options": ["1", "0", "Their product", "Undefined"], "answer": 1},
    {"question": "What curve uses 4 control points?", "options": ["Linear", "Quadratic Bezier", "Cubic Bezier", "Catmull-Rom"], "answer": 2},
    {"question": "What does distance() between two points return?", "options": ["The straight-line length", "The X difference", "The Y difference", "The sum of coordinates"], "answer": 0},
    {"question": "What does a normalized vector represent?", "options": ["Magnitude only", "Direction only", "Position only", "Speed only"], "answer": 1},
    {"question": "What is cos(90 degrees)?", "options": ["0", "1", "-1", "0.5"], "answer": 0},
]

#: Margen que se deja a los puntos para que su círculo y su etiqueta no
#: queden cortados contra el borde del lienzo.
_MARGEN_LIENZO = 10


def _dentro_del_lienzo(v: pygame.Vector2) -> pygame.Vector2:
    """Recorta un punto a las unidades de autoría del escenario."""
    m = _MARGEN_LIENZO
    return pygame.Vector2(
        max(m, min(AUTHORED_W - m, v.x)),
        max(m, min(AUTHORED_H - m, v.y)),
    )


DOT_COLORS = {
    "player": (80, 200, 120),
    "enemy": (200, 80, 80),
    "vector": (255, 220, 80),
    "normalized": (100, 180, 255),
    "projection": (200, 120, 255),
}


class VectorLabScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._player: pygame.Vector2 = pygame.Vector2(80.0, 120.0)
        self._enemy: pygame.Vector2 = pygame.Vector2(220.0, 100.0)
        self._speed: float = 100.0
        self._show_normalized: bool = False

        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)

        self._status_msg: str = ""
        self._status_timer: float = 0.0

        self._ANCHO_COLUMNA = _ANCHO_COLUMNA
        self._quiz = QuizManager(VECTOR_QUIZZES)
        self._code_panel = CodePanel("normalize")
        self._tutorial = TutorialOverlay("vector_lab")

    def on_enter(self) -> None:
        self._mode = 0
        self._show_normalized = False

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._status_timer > 0:
            self._status_timer -= dt
            if self._status_timer <= 0:
                self._status_msg = ""

        # Quiz, Code Panel, Tutorial handlers (non-blocking)
        if im and im.is_raw_key_pressed(pygame.K_q):
            self._quiz.toggle()

        if im and im.is_raw_key_pressed(pygame.K_c):
            self._code_panel.toggle()

        if im and im.is_raw_key_pressed(pygame.K_t):
            self._tutorial.toggle()

        if self._tutorial.active:
            if im and im.is_raw_key_pressed(pygame.K_RIGHT):
                self._tutorial.next_step()
            if im and im.is_raw_key_pressed(pygame.K_LEFT):
                self._tutorial.prev_step()

        if self._quiz.active:
            self._quiz.handle_input(im)
            self._quiz.update(dt)
            return  # freeze game while quiz is open

        if self._code_panel.active:
            return  # freeze game while code panel is open

        if self._tutorial.active:
            return  # freeze game while tutorial is open

        # Update code panel content based on mode
        mode_code_keys = ["distance", "normalize", "dot_product", "distance"]
        self._code_panel.set_code(mode_code_keys[self._mode])

        # TAB — cycle modes
        if im.is_raw_key_pressed(pygame.K_TAB):
            self._mode = (self._mode + 1) % len(MODE_NAMES)
            self._status_msg = f"Mode: {MODE_NAMES[self._mode]}"
            self._status_timer = 1.5

        # N — toggle normalized vector
        if im.is_raw_key_pressed(pygame.K_n):
            self._show_normalized = not self._show_normalized

        # R — reset
        if im.is_raw_key_pressed(pygame.K_r):
            self._player = pygame.Vector2(80.0, 120.0)
            self._enemy = pygame.Vector2(220.0, 100.0)

        # ESC — back
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        # Player movement (arrows)
        move_dir = pygame.Vector2(0.0, 0.0)
        if im.is_action_held(Action.MOVE_LEFT):
            move_dir.x -= 1.0
        if im.is_action_held(Action.MOVE_RIGHT):
            move_dir.x += 1.0
        if im.is_action_held(Action.JUMP):
            move_dir.y -= 1.0
        if im.is_action_held(Action.CROUCH):
            move_dir.y += 1.0

        self._player += move_dir * self._speed * dt
        # AUD-094: los límites van en unidades de autoría, que es donde viven
        # las posiciones. Antes se recortaban contra la pantalla (800x600), así
        # que el punto podía llegar a x=790 en un lienzo de 320 de ancho y
        # dibujarse fuera del escenario.
        self._player = _dentro_del_lienzo(self._player)

        # Enemy movement (WASD via raw keys)
        enemy_dir = pygame.Vector2(0.0, 0.0)
        if im.is_raw_key_pressed(pygame.K_w):
            enemy_dir.y -= 1.0
        if im.is_raw_key_pressed(pygame.K_s):
            enemy_dir.y += 1.0
        if im.is_raw_key_pressed(pygame.K_a):
            enemy_dir.x -= 1.0
        if im.is_raw_key_pressed(pygame.K_d):
            enemy_dir.x += 1.0

        # Mode-specific behavior
        if self._mode == 1:
            # CHASE: enemy moves toward player using normalized vector
            to_player = self._player - self._enemy
            dist = to_player.length()
            if dist > 5.0:
                to_player.normalize_ip()
                self._enemy += to_player * self._speed * 0.6 * dt
            else:
                self._enemy += enemy_dir * self._speed * dt
        elif self._mode == 2:
            # ORBIT: enemy orbits around player (manually controlled)
            self._enemy += enemy_dir * self._speed * dt
        else:
            self._enemy += enemy_dir * self._speed * dt

        self._enemy = _dentro_del_lienzo(self._enemy)

    def draw(self, surface: pygame.Surface) -> None:
        """Vectores en el escenario centrado, lecturas en su columna.

        AUD-094 — el vector cabía en un octavo de la pantalla
        -----------------------------------------------------
        El jugador arrancaba en (80, 120) y el enemigo en (220, 100): puntos
        de un lienzo de 320x224 dibujados como píxeles de pantalla sobre
        800x600. Medido, todo el contenido cabía en x[8,379] y[40,159] —dos
        de nueve celdas— y el vector, que es lo que la escena enseña, medía
        141 px sobre una pantalla de 800.

        La aritmética vectorial —longitud, producto escalar, ángulo— **sigue
        en unidades de autoría**. Escalarla cambiaría los números que el
        estudiante compara con los que calcula a mano. Lo único que pasa por
        el lienzo es el trazo.
        """
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "VECTOR LAB", "UNIT II")

        _, escenario = area_con_columna(self._ANCHO_COLUMNA)
        lienzo = Lienzo(AUTHORED_W, AUTHORED_H, area=escenario)

        # Rejilla dentro del escenario, con el paso de autoría escalado
        paso = lienzo.l(32)
        for x in range(escenario.left, escenario.right, paso):
            pygame.draw.line(surface, (20, 20, 40), (x, escenario.top), (x, escenario.bottom), 1)
        for y in range(escenario.top, escenario.bottom, paso):
            pygame.draw.line(surface, (20, 20, 40), (escenario.left, y), (escenario.right, y), 1)

        pi = lienzo.p(self._player.x, self._player.y)
        ei = lienzo.p(self._enemy.x, self._enemy.y)

        # Vector AB (del enemigo al jugador), en unidades de autoría
        vec_ab = self._player - self._enemy
        vec_len = vec_ab.length()
        vx, vy = vec_ab.x, vec_ab.y

        radio = lienzo.l(8)
        grosor = max(2, lienzo.l(1))

        if vec_len > 1.0:
            pygame.draw.line(surface, DOT_COLORS["vector"], ei, pi, grosor)
            # Punta de la flecha
            if vec_len > 10.0:
                punta = lienzo.l(8)
                angle_rad = math.radians(-30)
                cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
                n = vec_ab.copy().normalize()
                ax1 = pi[0] + int((-n.x * cos_a - n.y * sin_a) * punta)
                ay1 = pi[1] + int((-n.y * cos_a + n.x * sin_a) * punta)
                rad2 = math.radians(30)
                cos_b, sin_b = math.cos(rad2), math.sin(rad2)
                ax2 = pi[0] + int((-n.x * cos_b - n.y * sin_b) * punta)
                ay2 = pi[1] + int((-n.y * cos_b + n.x * sin_b) * punta)
                pygame.draw.line(surface, DOT_COLORS["vector"], pi, (ax1, ay1), grosor)
                pygame.draw.line(surface, DOT_COLORS["vector"], pi, (ax2, ay2), grosor)

            # Vector normalizado (si está activado)
            if self._show_normalized and vec_len > 5.0:
                nn = vec_ab.copy().normalize()
                n_end = lienzo.p(self._enemy.x + nn.x * 40, self._enemy.y + nn.y * 40)
                pygame.draw.line(surface, DOT_COLORS["normalized"], ei, n_end, grosor + 1)
                nlabel = self._font_small.render("normalized", True, DOT_COLORS["normalized"])
                surface.blit(nlabel, (n_end[0] + 4, n_end[1] - 8))

        # Jugador y enemigo
        pygame.draw.circle(surface, DOT_COLORS["player"], pi, radio)
        pygame.draw.circle(surface, (255, 255, 255), pi, radio, 1)
        label_p = self._font_small.render("Player", True, DOT_COLORS["player"])
        surface.blit(label_p, (pi[0] + radio + 4, pi[1] - 6))

        pygame.draw.circle(surface, DOT_COLORS["enemy"], ei, radio)
        pygame.draw.circle(surface, (255, 255, 255), ei, radio, 1)
        label_e = self._font_small.render("Enemy", True, DOT_COLORS["enemy"])
        surface.blit(label_e, (ei[0] + 12, ei[1] - 6))

        # Mode label
        mode_color = COLOR_HIGHLIGHT if self._mode >= 1 else COLOR_ACCENT
        mode_label = self._font_medium.render(
            f"  Mode: {MODE_NAMES[self._mode]}  ", True, mode_color)
        surface.blit(mode_label, (_MARGIN, _CONTENT_TOP))

        # Math info panel
        info_y = _PANEL_TOP + 52
        dot_x = vec2_dot(vec_ab, pygame.Vector2(1, 0))
        angle = math.degrees(math.atan2(vec_ab.y, vec_ab.x)) if vec_len > 0.01 else 0.0
        info_lines = [
            f"Vector AB: ({vx:.0f}, {vy:.0f})",
            f"Length |AB|: {vec_len:.1f}",
        ]
        if self._show_normalized and vec_len > 1.0:
            nn = vec_ab.copy().normalize()
            info_lines.append(f"Normalized: ({nn.x:.3f}, {nn.y:.3f}) [length={nn.length():.1f}]")
        info_lines += [
            f"Dot(AB, X): {dot_x:.1f}",
            f"Angle from X: {angle:.0f}°",
            f"Distance: {vec_len:.1f} px",
        ]

        for i, line in enumerate(info_lines):
            txt = self._font_small.render(line, True, COLOR_TEXT)
            surface.blit(txt, (_MARGIN, info_y + i * 16))

        # Controls hint
        hint = self._font_small.render(
            "  Arrows: Player  |  WASD: Enemy  |  TAB: mode  |  N: toggle norm  |"
            "  R: reset  |  ESC: exit", True, COLOR_TEXT)
        surface.blit(hint, (_MARGIN, _CONTENT_TOP + 24))

        # Status
        if self._status_msg:
            st = self._font_small.render(self._status_msg, True, COLOR_HIGHLIGHT)
            surface.blit(st, (_MARGIN, BOTTOM_BAR_Y - 16))

        # Quiz, Code Panel, Tutorial overlays
        self._quiz.draw(surface)
        self._code_panel.draw(surface)
        self._tutorial.draw(surface)

        draw_bottom_bar(surface, (
            f"  MODE: {MODE_NAMES[self._mode]} | [Q] Quiz [C] Code [T] Tutorial"
        ))
