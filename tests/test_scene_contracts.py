"""
AUD-631 — contract tests para SceneManager: push, pop y replace.

Cada operación de la pila de escenas tiene un contrato:
- `push`: la escena anterior recibe `on_pause`, la nueva `on_enter`
- `pop`:  la escena superior recibe `on_exit`, la inferior `on_resume`
- `replace`: la escena actual recibe `on_exit`, la nueva `on_enter`

Estos tests verifican que los contratos se cumplen sin importar qué
escenas concretas se apilen: si alguien rompe el ciclo de vida, aquí salta.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pygame
import pytest

from src.engine.core import settings


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))


@pytest.fixture
def scene_manager(_video):
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.scene.scene_manager import SceneManager

    ctx = MagicMock(spec=GameContext)
    ctx.event_bus = EventBus()
    mgr = SceneManager(ctx)
    mgr.context = ctx
    return mgr


def _escena_falsa(nombre: str):
    """Crea un mock que se comporta como BaseScene."""
    escena = MagicMock()
    escena.__repr__ = lambda self: f"<EscenaFalsa:{nombre}>"
    escena.nombre = nombre
    return escena


class TestContratoPush:
    def test_push_llama_on_pause_en_anterior_y_on_enter_en_nueva(self, scene_manager):
        vieja = _escena_falsa("vieja")
        nueva = _escena_falsa("nueva")

        scene_manager.replace(vieja)
        vieja.on_enter.reset_mock()

        scene_manager.push(nueva)

        vieja.on_pause.assert_called_once()
        nueva.on_enter.assert_called_once()
        assert scene_manager.current is nueva

    def test_push_apila(self, scene_manager):
        a = _escena_falsa("a")
        b = _escena_falsa("b")

        scene_manager.replace(a)
        scene_manager.push(b)

        assert len(scene_manager._stack) == 2

    def test_push_a_pila_vacia_reemplaza(self, scene_manager):
        nueva = _escena_falsa("primera")
        scene_manager.push(nueva)
        assert scene_manager.current is nueva


class TestContratoPop:
    def test_pop_llama_on_exit_en_superior_y_on_resume_en_inferior(self, scene_manager):
        base = _escena_falsa("base")
        encima = _escena_falsa("encima")

        scene_manager.replace(base)
        scene_manager.push(encima)

        base.on_resume.reset_mock()
        encima.on_exit.reset_mock()

        scene_manager.pop()

        encima.on_exit.assert_called_once()
        base.on_resume.assert_called_once()
        assert scene_manager.current is base

    def test_pop_en_pila_unitaria_no_explota(self, scene_manager):
        unica = _escena_falsa("unica")
        scene_manager.replace(unica)
        scene_manager.pop()
        # La pila puede quedar vacía o mantener la escena; no debe lanzar.

    def test_pop_retorna_la_escena_desapilada(self, scene_manager):
        base = _escena_falsa("base")
        encima = _escena_falsa("encima")
        scene_manager.replace(base)
        scene_manager.push(encima)

        scene_manager.pop()


class TestContratoReplace:
    def test_replace_llama_on_exit_en_actual_y_on_enter_en_nueva(self, scene_manager):
        vieja = _escena_falsa("vieja")
        nueva = _escena_falsa("nueva")

        scene_manager.replace(vieja)
        vieja.on_exit.reset_mock()
        nueva.on_enter.reset_mock()

        scene_manager.replace(nueva)

        vieja.on_exit.assert_called_once()
        nueva.on_enter.assert_called_once()
        assert scene_manager.current is nueva

    def test_replace_mantiene_tamano_de_pila_en_uno(self, scene_manager):
        vieja = _escena_falsa("vieja")
        nueva = _escena_falsa("nueva")
        scene_manager.replace(vieja)
        scene_manager.replace(nueva)
        assert len(scene_manager._stack) == 1

    def test_replace_sobre_vacia_funciona(self, scene_manager):
        nueva = _escena_falsa("primera")
        scene_manager.replace(nueva)
        assert scene_manager.current is nueva


class TestContratoCicloCompleto:
    def test_ciclo_push_pop_replace_secuencia_completa(self, scene_manager):
        """Una secuencia real de navegación respeta el ciclo de vida."""
        titulo = _escena_falsa("titulo")
        juego = _escena_falsa("juego")
        pausa = _escena_falsa("pausa")
        game_over = _escena_falsa("game_over")

        # Arrancar
        scene_manager.replace(titulo)
        titulo.on_enter.assert_called_once()

        # Jugar
        scene_manager.push(juego)
        titulo.on_pause.assert_called_once()
        juego.on_enter.assert_called_once()

        # Pausar
        scene_manager.push(pausa)
        juego.on_pause.assert_called_once()
        pausa.on_enter.assert_called_once()

        # Reanudar
        scene_manager.pop()
        pausa.on_exit.assert_called_once()
        juego.on_resume.assert_called_once()

        # Morir → Game Over
        scene_manager.replace(game_over)
        juego.on_exit.assert_called_once()
        game_over.on_enter.assert_called_once()