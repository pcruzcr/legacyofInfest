"""AUD-446 — el menú de título era una lista de la compra.

Las catorce opciones se dibujaban a la vez. A 24 px por fila son 336 px de
los 600 que hay, y el logo quedaba encajonado en 80 px de alto peleando por
el sitio con las opciones. La jerarquía que pedía el encargo —logo, luego
contexto, luego menú— no se leía: todo tenía el mismo peso.

Lo que cambia:

* el logo puede ocupar el doble de alto y tiene aire alrededor;
* se ven **cuatro** opciones a la vez y la lista se desliza para mantener la
  seleccionada dentro;
* el deslizamiento es suave, no un salto de página.

Ninguna opción desaparece. Quitar funciones para que quepan sería resolver el
problema equivocado, y el encargo lo decía expresamente.

El aspecto se queda
-------------------
Esta pantalla dibuja sus filas con la tipografía del juego, centradas y con
brillo en la seleccionada. No pasa a usar el dibujo genérico de `MenuList`:
lo que toma prestado del widget es la **lógica** —qué filas se ven y cuánto
se ha deslizado—, no el aspecto. Cambiar el aspecto sería sustituir el arte
de la portada por una pantalla de sistema.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import settings


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    yield


@pytest.fixture
def titulo(_video, tmp_path, monkeypatch):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.engine.scenes.title_scene import TitleScene

    monkeypatch.setattr(SaveManager, "SAVES_DIR", tmp_path)
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    escena = TitleScene(ctx)
    escena.awake()
    escena.start()
    escena.on_enter()
    return escena


def _asentar(escena, segundos: float = 2.0) -> None:
    for _ in range(int(segundos * 60)):
        escena.update(1 / 60)


class TestElMenuNoLoEnseñaTodo:
    def test_se_ven_como_mucho_cuatro_opciones(self, titulo) -> None:
        assert len(titulo._menu.items) > 4, (
            "el menú se ha quedado corto y esta prueba ya no mide nada"
        )
        assert len(titulo._menu.filas_visibles()) <= 4, (
            f"se dibujan {len(titulo._menu.filas_visibles())} opciones a la "
            f"vez: la portada vuelve a ser una lista de la compra"
        )

    def test_no_se_ha_quitado_ninguna_opcion(self, titulo) -> None:
        """El encargo lo pedía expresamente: no recortar para que quepa."""
        etiquetas = [str(i.value) for i in titulo._menu.items]
        for esperada in ("START", "WORLD MAP", "INVENTORY", "SKILL TREE",
                         "SHOP", "BESTIARY", "ACHIEVEMENTS", "RECORDS",
                         "OPTIONS", "QUIT"):
            assert esperada in etiquetas, f"desapareció {esperada!r}"

    def test_la_seleccionada_siempre_se_ve(self, titulo) -> None:
        for _ in range(len(titulo._menu.items) + 3):
            titulo._menu.move_down()
            _asentar(titulo, 0.5)
            assert titulo._menu.index in titulo._menu.filas_visibles()


class TestElLogoTieneSitio:
    def test_es_mas_grande_que_antes(self, titulo) -> None:
        """80 px era el techo anterior; el encargo pedía más presencia."""
        assert titulo._logo.get_height() > 80, (
            f"el logo mide {titulo._logo.get_height()} px de alto"
        )

    def test_no_invade_las_opciones(self, titulo) -> None:
        """Más grande no puede significar encima del menú."""
        assert titulo.primera_fila_y() > titulo.logo_rect().bottom, (
            "la primera opción empieza dentro del logo"
        )

    def test_las_opciones_caben_en_la_pantalla(self, titulo) -> None:
        ultima = (titulo.primera_fila_y()
                  + len(titulo._menu.filas_visibles()) * titulo._option_spacing)
        assert ultima <= settings.INTERNAL_HEIGHT, (
            f"la última opción visible acaba en {ultima}, fuera de los "
            f"{settings.INTERNAL_HEIGHT} px de alto"
        )


class TestSeDibujaSinRomperse:
    def test_un_recorrido_entero_no_revienta(self, titulo) -> None:
        superficie = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        for _ in range(len(titulo._menu.items) + 2):
            titulo._menu.move_down()
            for _ in range(20):
                titulo.update(1 / 60)
                titulo.draw(superficie)

    def test_la_portada_pinta_algo(self, titulo) -> None:
        superficie = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        superficie.fill((0, 0, 0))
        _asentar(titulo, 0.5)
        titulo.draw(superficie)
        assert pygame.transform.average_color(superficie)[:3] != (0, 0, 0)
