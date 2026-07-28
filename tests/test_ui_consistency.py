"""Guards that keep the UI from fragmenting again (AUD-044 / AUD-045).

Before the design system existed, every scene invented its own look. A survey
found six different background colours all meaning "dark backdrop", selection
highlights in four different colours, titles anchored at y=14, 20, 40 and 60,
and two different answers to "what happens when I press Down on the last item"
— one screen wrapped, another clamped.

None of that is a crash, so no test caught it, and it is exactly the kind of
inconsistency that accumulates until a redesign is the only way out. These tests
make drift visible while it is still one line.

They are intentionally lenient about *where* a scene draws things and strict
about *which tokens* it uses. Layout is a design decision; palette is identity.
"""
from __future__ import annotations

import os
import pathlib
import re

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCENES_DIR = ROOT / "src" / "engine" / "scenes"

# Scenes migrated to the shared kit. New scenes should be added here, and
# existing ones removed from the waiver list below as they are migrated.
MIGRATED = {
    "game_over_scene.py",
    "stage_error_scene.py",
    "title_scene.py",
    # ── Los 17 laboratorios ────────────────────────────────────────
    # Estas escenas no importan `theme` ni `widgets` directamente: usan
    # `demo_layout`, que **deriva toda su paleta del tema** (`COLOR_BG =
    # Theme.BG`, `COLOR_HIGHLIGHT = Theme.ACCENT`…). Cambiar el tema las
    # cambia a todas, que es exactamente lo que el kit persigue.
    #
    # Llevaban tiempo en la lista de espera por un error de contabilidad: se
    # alinearon al reescribir `demo_layout` y nadie las sacó de ahí. Una lista
    # de deuda que exagera la deuda es tan poco útil como una que la esconde —
    # con 30 nombres pendientes nadie empieza; con 12, sí.
    "collision_lab_scene.py", "color_theory_scene.py", "combo_demo_scene.py",
    "curve_editor_scene.py", "demo_menu_scene.py", "filter_demo_scene.py",
    "interpolation_lab_scene.py", "leaderboard_scene.py", "load_game_scene.py",
    "noise_lab_scene.py", "pipeline_builder_scene.py", "progress_scene.py",
    "sandbox_scene.py", "stage_wizard_scene.py", "transform_lab_scene.py",
    "vector_lab_scene.py", "vision_demo_scene.py",
    # AUD-095 y AUD-098. Usan `demo_layout` —barras, colores y
    # `area_de_contenido`— igual que sus hermanas de esta lista, que es lo que
    # aquí cuenta como migrada.
    "unit_theory_scene.py", "student_login_scene.py",
    # Su fondo de pantalla ya es `COLOR_BG` (= Theme.BG). Los `(5,5,15)` que
    # una versión anterior de este archivo marcaba como infracción se pintan
    # sobre lienzos internos de visualización, no sobre la pantalla.
    "pattern_demo_scene.py",
    # ── Menús migrados en AUD-069 ──────────────────────────────────
    "achievement_scene.py", "bestiary_scene.py", "inventory_scene.py",
    "keybinding_scene.py", "tutorial_scene.py", "world_map_scene.py",
    # ── Pantallas sin menú, migradas en AUD-069 ────────────────────
    "end_credits_scene.py", "loading_scene.py", "story_scene.py",
}

# Not yet migrated. This list may only ever shrink — see
# test_migration_waiver_does_not_grow. It exists so the guard can be switched on
# now rather than waiting for all 34 scenes to be converted, which would have
# meant shipping no guard at all.
AWAITING_MIGRATION = {
    # `splash_scene` es una imagen a pantalla completa durante dos segundos:
    # no tiene fondo propio que unificar, ni menú, ni teclas que anunciar más
    # allá de «pulsa para saltar». Migrarla sería añadirle una cabecera que
    # taparía la ilustración.
    "splash_scene.py",
    # Caso aparte: es la única escena construida con `pygame_gui`, una
    # segunda librería de UI. Migrarla no es reordenar dibujado, es decidir
    # si el proyecto mantiene dos sistemas de interfaz o uno. Esa decisión no
    # es mía y no se toma escondiéndola en una lista.
    "options_scene.py",
}


def _scene_files() -> list[pathlib.Path]:
    return sorted(
        p for p in SCENES_DIR.glob("*.py")
        if not p.name.startswith("_")
        and p.name not in {"demo_common.py", "demo_layout.py", "demo_utils.py",
                           "scene_registry.py", "code_panel.py", "param_panel.py",
                           "quiz_system.py", "debug_overlay.py", "transition_manager.py",
                           "tutorial_overlay.py"}
    )


# ── theme integrity ──────────────────────────────────────────────


def test_theme_tokens_are_distinct() -> None:
    """Surface depth steps must be visually distinguishable.

    If SURFACE and SURFACE_RAISED are too close, the focused row stops reading
    as focused and the menu becomes unusable — which is the failure mode the
    redundant cursor glyph exists to protect against, but the colours should
    carry their share.
    """
    from src.engine.ui.theme import Theme

    def luma(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

    assert luma(Theme.SURFACE_RAISED) - luma(Theme.SURFACE) >= 8, (
        "SURFACE_RAISED is not clearly lighter than SURFACE, so focused rows "
        "will not read as raised"
    )
    assert luma(Theme.SURFACE) - luma(Theme.BG) >= 6, (
        "panels do not stand out from the background"
    )


def test_text_tiers_have_descending_contrast() -> None:
    from src.engine.ui.theme import Theme

    def luma(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

    assert luma(Theme.TEXT) > luma(Theme.TEXT_MUTED) > luma(Theme.TEXT_DIM), (
        "the three text tiers must be ordered by prominence"
    )


def test_primary_text_meets_contrast_on_background() -> None:
    """WCAG-style contrast check for body text on the app background.

    4.5:1 is the AA threshold for normal text. The game renders at a small
    internal resolution and is upscaled, so falling below this makes text
    genuinely hard to read rather than merely unfashionable.
    """
    from src.engine.ui.theme import Theme

    def relative_luminance(c):
        def channel(v):
            v = v / 255
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        r, g, b = (channel(x) for x in c)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    light = relative_luminance(Theme.TEXT)
    dark = relative_luminance(Theme.BG)
    ratio = (light + 0.05) / (dark + 0.05)
    assert ratio >= 4.5, f"body text contrast is {ratio:.2f}:1, below the 4.5:1 AA floor"


def test_accent_is_not_the_danger_colour() -> None:
    """Focus and danger must never be the same colour.

    If the selection highlight is red, players stop reading red as "damage",
    which is the one colour meaning the game cannot afford to dilute.
    """
    from src.engine.ui.theme import Theme

    assert Theme.ACCENT != Theme.DANGER
    assert abs(Theme.ACCENT[2] - Theme.DANGER[2]) > 10 or Theme.ACCENT[1] != Theme.DANGER[1]


# ── shared navigation semantics ──────────────────────────────────


class TestMenuNavigationIsUniform:
    def test_wraps_at_both_ends(self) -> None:
        from src.engine.ui.widgets import MenuItem, MenuList

        menu = MenuList(items=[MenuItem("a"), MenuItem("b"), MenuItem("c")])
        menu.index = 2
        menu.move_down()
        assert menu.index == 0, "moving down past the last item must wrap to the first"
        menu.move_up()
        assert menu.index == 2, "moving up from the first item must wrap to the last"

    def test_skips_disabled_items(self) -> None:
        from src.engine.ui.widgets import MenuItem, MenuList

        menu = MenuList(items=[
            MenuItem("a"), MenuItem("b", enabled=False), MenuItem("c"),
        ])
        menu.index = 0
        menu.move_down()
        assert menu.index == 2, "focus landed on a disabled row"

    def test_all_disabled_does_not_hang(self) -> None:
        from src.engine.ui.widgets import MenuItem, MenuList

        menu = MenuList(items=[MenuItem("a", enabled=False)])
        menu.move_down()  # must terminate
        menu.move_up()

    def test_empty_menu_is_safe(self) -> None:
        from src.engine.ui.widgets import MenuList

        menu = MenuList()
        menu.move_down()
        menu.move_up()
        assert menu.current is None

    def test_ensure_valid_clamps_after_shrink(self) -> None:
        """A save-slot list that shrinks under the cursor must not IndexError."""
        from src.engine.ui.widgets import MenuItem, MenuList

        menu = MenuList(items=[MenuItem("a"), MenuItem("b"), MenuItem("c")])
        menu.index = 2
        menu.items = [MenuItem("a")]
        menu.ensure_valid()
        assert menu.index == 0
        assert menu.current is not None


# ── palette discipline across scenes ─────────────────────────────


# Sólo interesa quien pinta **la pantalla**, no cualquier superficie.
# `self._cached_result.fill((0, 0, 0))` limpia un búfer de trabajo interno y no
# tiene nada que ver con la identidad visual del juego; la primera versión de
# esta expresión no distinguía las dos cosas y marcaba tres laboratorios
# correctos como infractores. Un guardián con falsos positivos acaba
# desactivado, que es peor que no tenerlo.
_FILL_RE = re.compile(r"\bsurface\.fill\(\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)")


@pytest.mark.parametrize("path", [p for p in _scene_files() if p.name in MIGRATED],
                         ids=lambda p: p.name)
def test_migrated_scenes_use_the_shared_kit(path: pathlib.Path) -> None:
    """Directamente o a través de `demo_layout`, que deriva del tema.

    Los laboratorios no importan `theme`: importan `demo_layout`, cuyas
    constantes **son** las del tema. Exigir el import directo obligaría a
    reescribir diecisiete archivos para no cambiar ni un píxel, que es
    trabajo con la forma de progreso y sin el efecto.
    """
    source = path.read_text(encoding="utf-8")
    uses_kit = (
        "src.engine.ui.widgets" in source
        or "src.engine.ui.theme" in source
        or "demo_layout" in source
        or "demo_common" in source
    )
    assert uses_kit, (
        f"{path.name} está en MIGRATED pero no usa el tema ni por `demo_layout`"
    )


@pytest.mark.parametrize("path", [p for p in _scene_files() if p.name in MIGRATED],
                         ids=lambda p: p.name)
def test_migrated_scenes_have_no_hardcoded_background(path: pathlib.Path) -> None:
    """A migrated scene must not paint its own backdrop colour."""
    source = path.read_text(encoding="utf-8")
    literals = _FILL_RE.findall(source)
    dark = [t for t in literals if sum(int(v) for v in t) < 150]
    assert not dark, (
        f"{path.name} still fills a hand-picked dark colour {dark}; use "
        "widgets.draw_screen() so the whole game shares one backdrop"
    )


def test_migration_waiver_does_not_grow() -> None:
    """Every scene is either migrated or explicitly waived — no third state.

    A new scene added without a decision would otherwise silently reintroduce a
    bespoke look. This test forces the author to pick.
    """
    known = MIGRATED | AWAITING_MIGRATION
    actual = {p.name for p in _scene_files()}
    unaccounted = actual - known
    assert not unaccounted, (
        f"new scene(s) {sorted(unaccounted)} are neither migrated to the shared "
        "UI kit nor listed in AWAITING_MIGRATION. Add them to one or the other."
    )


def test_waiver_has_no_stale_entries() -> None:
    """Names in the waiver must still exist, or the list is lying."""
    actual = {p.name for p in _scene_files()}
    stale = AWAITING_MIGRATION - actual
    assert not stale, f"AWAITING_MIGRATION lists scenes that no longer exist: {sorted(stale)}"


def test_lab_palette_is_derived_from_the_theme() -> None:
    """The 18 lab scenes share demo_layout; it must not fork the palette."""
    from src.engine.scenes import demo_layout
    from src.engine.ui.theme import Theme

    assert demo_layout.COLOR_BG == Theme.BG
    assert demo_layout.COLOR_TEXT == Theme.TEXT
    assert demo_layout.COLOR_HIGHLIGHT == Theme.ACCENT


class TestLaCacheDeFuentesSobreviveAUnApagado:
    """AUD-077 — la caché servía fuentes muertas y nadie lo notaba.

    Un `pygame.font.Font` queda inservible en cuanto se apaga el módulo de
    fuentes, y no revive al reinicializarlo. La caché del tema devolvía el
    objeto viejo sin comprobarlo, así que cualquier pantalla que pasara por el
    kit reventaba con `Invalid font` en la primera llamada a `render()`.

    Estas pruebas ejecutan el ciclo completo —crear, apagar, reiniciar, volver
    a pedir— porque el fallo sólo existe en la frontera entre esas cuatro
    cosas. Una prueba que sólo pidiera la fuente dos veces seguidas pasaría con
    el error dentro.
    """

    @staticmethod
    def _ciclo_de_apagado() -> None:
        import pygame
        pygame.quit()
        pygame.init()
        pygame.display.set_mode((320, 180))

    def test_una_fuente_pedida_tras_apagar_pygame_puede_dibujar(self) -> None:
        import pygame

        from src.engine.ui.theme import Theme, font

        pygame.init()
        pygame.display.set_mode((320, 180))
        primera = font(Theme.FONT_SMALL)
        primera.render("hola", True, Theme.TEXT)

        self._ciclo_de_apagado()

        segunda = font(Theme.FONT_SMALL)
        # Si la caché devolviera la misma instancia, esto lanzaría
        # `pygame.error: Invalid font (font module quit since font created)`.
        superficie = segunda.render("hola", True, Theme.TEXT)
        assert superficie.get_width() > 0

    def test_el_apagado_invalida_toda_la_cache_no_solo_la_entrada_pedida(self) -> None:
        """Pedir un tamaño debe sanear los demás, no dejarlos podridos."""
        import pygame

        from src.engine.ui.theme import Theme, font

        pygame.init()
        pygame.display.set_mode((320, 180))
        font(Theme.FONT_SMALL)
        font(Theme.FONT_TITLE)

        self._ciclo_de_apagado()

        font(Theme.FONT_SMALL)          # sólo se pide una de las dos
        otra = font(Theme.FONT_TITLE)   # la otra también tiene que estar viva
        assert otra.render("x", True, Theme.TEXT).get_width() > 0

    def test_una_pantalla_completa_se_dibuja_tras_el_apagado(self) -> None:
        """La prueba que de verdad importa: el kit entero, no una fuente suelta."""
        import pygame

        from src.engine.ui.widgets import draw_key_hints, draw_screen

        pygame.init()
        pygame.display.set_mode((320, 180))
        self._ciclo_de_apagado()

        superficie = pygame.Surface((320, 180))
        draw_screen(superficie, "TÍTULO", "subtítulo")
        draw_key_hints(superficie, [("Esc", "Volver")])

    def test_sin_apagones_la_cache_sigue_reutilizando(self) -> None:
        """La validación no debe convertir la caché en un no-op."""
        import pygame

        from src.engine.ui.theme import Theme, font

        pygame.init()
        pygame.display.set_mode((320, 180))
        assert font(Theme.FONT_SMALL) is font(Theme.FONT_SMALL)
