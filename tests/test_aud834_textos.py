"""AUD-834 — textos pegados y listas sin desplazar en menús y demos.

El reporte: letras pegadas (demos educativas con muchas opciones) en vez de
desplazante. Verificado por frentes: `demo_menu` con 1 px de aire,
`pattern_demo` con solapes de hasta 11 px, `keybinding`/`load_game`/`quiz`
con pasos y cajas fijos que no escalan, y `shop` sin ventana para un
catálogo que crece. `filter_demo` no se toca (cicla modos con TAB, no es
lista) y `unit_theory` cabe con datos acotados (4 opciones, se documenta).
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


def test_demo_menu_fila_con_aire(display) -> None:
    from src.engine.scenes import demo_menu_scene as m
    from src.engine.scenes.demo_layout import FONT_MEDIUM, FONT_SMALL
    from src.engine.ui.theme import Theme, font

    esperada = (font(FONT_MEDIUM).get_height()
                + font(FONT_SMALL).get_height() + Theme.SPACE_S)
    assert m.altura_de_fila() >= esperada, (
        f"la fila mide {m.altura_de_fila()} px para dos líneas que necesitan "
        f"{esperada}: rótulo y descripción se tocan"
    )


def test_pattern_panel_sin_solapes(display) -> None:
    """Las franjas de texto del panel no se tocan entre sí."""
    import numpy as np

    from src.engine.scenes.demo_layout import FONT_LARGE, FONT_MEDIUM, FONT_SMALL
    from src.engine.scenes.pattern_demo_scene import PatternDemoScene
    from src.engine.ui.theme import font

    escena = PatternDemoScene.__new__(PatternDemoScene)
    escena._font_large = font(FONT_LARGE)
    escena._font_medium = font(FONT_MEDIUM)
    escena._font_small = font(FONT_SMALL)
    escena._model_name = "prueba"
    surf = escena._render_inference(
        {"a": 0.7, "b": 0.2, "c": 0.1}, "a", "m",
        np.zeros(8, dtype=float),
    )
    # array3d indexa [x][y]: se mira la columna x 10..70 fila por fila.
    tinta = (pygame.surfarray.array3d(surf)[10:70, :, :].max(axis=2) > 60)
    bandas, en_tinta, inicio = [], False, 0
    for y in range(tinta.shape[1]):
        hay = bool(tinta[:, y].any())
        if hay and not en_tinta:
            en_tinta, inicio = True, y
        elif not hay and en_tinta:
            en_tinta = False
            bandas.append((inicio, y - 1))
    if en_tinta:
        bandas.append((inicio, tinta.shape[1] - 1))
    assert len(bandas) >= 6, f"sólo {len(bandas)} franjas de texto separadas"
    import itertools

    for (f0, f1), (g0, g1) in itertools.pairwise(bandas):
        assert g0 - f1 - 1 >= 2, (
            f"franjas {f0}-{f1} y {g0}-{g1} pegadas en el panel"
        )


def test_keybinding_fila_desde_metricas(display) -> None:
    from src.engine.scenes import keybinding_scene as k

    escena = k.KeybindingScene.__new__(k.KeybindingScene)
    escena._font_label = k.font(k.Theme.FONT_SMALL)
    escena._font_text = k.font(k.Theme.FONT_TINY)
    esperada = (escena._font_label.get_height() + escena._font_text.get_height()
                + k.Theme.SPACE_XS)
    assert k.altura_de_fila(escena._font_label, escena._font_text) >= esperada, (
        "la fila fija no deja aire entre etiqueta y tecla con texto grande"
    )


def test_load_game_slot_desde_metricas(display) -> None:
    from src.engine.scenes import load_game_scene as lg

    escena = lg.LoadGameScene.__new__(lg.LoadGameScene)
    escena._font_small = lg.font(17)
    esperada = escena._font_small.get_height() * 2 + lg.Theme.SPACE_XS * 2
    assert lg.altura_de_slot(escena._font_small) >= esperada, (
        "el slot fijo mete dos líneas donde no caben con texto grande"
    )


def test_quiz_cabe_en_su_caja(display) -> None:
    from src.engine.core import settings
    from src.engine.scenes.quiz_system import QuizManager

    quiz = QuizManager([{
        "question": "Una pregunta deliberadamente larga para forzar el ajuste "
                    "de línea dentro de la caja del cuestionario",
        "options": ["primera opción", "segunda opción", "tercera opción",
                    "cuarta opción"],
        "answer": 0,
    }])
    quiz.toggle()
    lienzo = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    lienzo.fill((0, 0, 0))
    quiz.draw(lienzo)
    import numpy as np

    # array3d indexa [x][y]: dim0 es x, dim1 es y.
    tinta = pygame.surfarray.array3d(lienzo).max(axis=2) > 30
    xs, ys = np.where(tinta)
    assert len(xs), "el cuestionario no dibuja nada"
    caja = quiz.caja()
    fuera_x = ((xs < caja.x) | (xs >= caja.right)).sum()
    fuera_y = ((ys < caja.y) | (ys >= caja.bottom)).sum()
    assert fuera_x == 0 and fuera_y == 0, (
        f"{fuera_x + fuera_y} px de texto fuera de la caja del cuestionario"
    )
