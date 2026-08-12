"""AUD-436 — «Presiona CONFIRM para continuar» no se veía al acabar el tutorial.

Qué fallaba
-----------
El tutorial termina entrando en `StoryScene`, y su aviso se pintaba con
`AssetLoader.load_font(game.ttf, 11)`. Medido, eso son **7 px de tinta real**
—`game.ttf` entrega bastante menos alto del que se le pide, ver AUD-203— y,
lo que importa más, esa ruta **no pasa por `theme.font()`**, así que
`escalar_texto` no la toca: el aviso mide 7 px con la accesibilidad al 100 %
y sigue midiendo 7 px con el texto al 200 %.

No es contraste: medido contra `story/h01.png` da 4,83:1, por encima del 4,5:1
que pide WCAG para texto pequeño. Es tamaño.

AUD-126 predijo esto por escrito al centralizar la escala en `theme.font()`:
«bastaría que una escena se olvidara para que el jugador que necesita el texto
grande se encontrara una pantalla ilegible sin saber por qué». Se olvidaron
36 ficheros con 75 construcciones de fuente; éste es el que se reportó.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import settings, user_settings
from src.engine.ui.theme import clear_font_cache


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    yield


def _con_escala(escala: float):
    ajustes = user_settings.UserSettings()
    ajustes.text_scale = escala
    user_settings.set_settings(ajustes)
    clear_font_cache()


def _tinta(superficie: pygame.Surface) -> int:
    """Alto de los píxeles realmente pintados, no el que declara la fuente."""
    return superficie.get_bounding_rect().height


def _aviso(contexto) -> pygame.Surface:
    from src.engine.scenes.story_scene import StoryScene

    escena = StoryScene(contexto, 1)
    return escena._font_hint.render(
        "Presiona CONFIRM para continuar", True, (180, 180, 160),
    )


@pytest.fixture
def contexto(_video):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager

    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


def test_el_aviso_crece_con_la_accesibilidad(contexto) -> None:
    """Lo que el defecto rompía: subir el texto no hacía nada aquí."""
    _con_escala(1.0)
    normal = _tinta(_aviso(contexto))
    _con_escala(2.0)
    doble = _tinta(_aviso(contexto))

    assert doble > normal * 1.5, (
        f"con el texto al 200 % el aviso pasa de {normal} px de tinta a "
        f"{doble} px. La preferencia de accesibilidad no le llega: es la "
        f"pantalla que ve todo el mundo al terminar el tutorial."
    )


def test_el_aviso_es_legible_ya_al_100_por_ciento(contexto) -> None:
    """7 px de tinta no se leen ni con buena vista, y ése era el tamaño."""
    _con_escala(1.0)
    assert _tinta(_aviso(contexto)) >= 9, (
        "el aviso del final del tutorial tiene menos tinta de la que se puede "
        "leer a tamaño normal"
    )


def test_el_aviso_sigue_cabiendo_a_doble_tamano(contexto) -> None:
    """Agrandar sin comprobar el ancho sólo cambia un defecto por otro.

    Es exactamente lo que se midió en la pantalla de error del escenario, que
    recorta por número de caracteres y a 2.0x se sale 266 px del marco.
    """
    _con_escala(2.0)
    assert _aviso(contexto).get_width() <= settings.INTERNAL_WIDTH, (
        "el aviso agrandado no cabe en los 800 px de la superficie interna"
    )


def test_las_lineas_no_se_solapan_con_el_texto_grande(contexto) -> None:
    """El fallo que introduce arreglar esto a medias.

    El cuerpo se pinta con `y += 22` escrito a mano. Si la tipografía escala y
    el interlineado no, a 2.0x cada línea invade la siguiente y el resultado es
    menos legible que el defecto que se venía a corregir. El paso tiene que
    salir de la métrica de la fuente, no de un número.
    """
    from src.engine.scenes.story_scene import StoryScene

    _con_escala(2.0)
    escena = StoryScene(contexto, 1)
    assert escena._alto_de_linea() > escena._font_text.get_height(), (
        f"el interlineado ({escena._alto_de_linea()} px) no deja hueco para "
        f"una línea de {escena._font_text.get_height()} px: el texto se pisa"
    )


def test_el_titulo_y_el_cuerpo_tambien_escalan(contexto) -> None:
    """El aviso no viajaba solo: las tres tipografías de la escena se saltaban
    la escala, y arreglar sólo una dejaría la pantalla descompensada."""
    from src.engine.scenes.story_scene import StoryScene

    def altos():
        e = StoryScene(contexto, 1)
        return (
            _tinta(e._font_title.render("TITULO", True, (255, 255, 240))),
            _tinta(e._font_text.render("cuerpo del texto", True, (240, 240, 230))),
        )

    _con_escala(1.0)
    t1, c1 = altos()
    _con_escala(2.0)
    t2, c2 = altos()
    assert t2 > t1 and c2 > c1, (
        f"título {t1}->{t2}, cuerpo {c1}->{c2}: alguna de las dos no escala"
    )
