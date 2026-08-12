"""AUD-445 — el juego empezaba sin preguntar en qué partida.

El arranque era: presentación → menú principal → y sólo si elegías CONTINUAR
aparecía la lista de partidas. O sea que todo lo que el menú ofrece —mundo,
inventario, habilidades, tienda— se abría **antes** de saber de quién era el
progreso que se estaba enseñando. Con una sola partida no se nota; con cinco,
el menú muestra el inventario de la que quedara activa por casualidad.

El orden nuevo es el clásico: presentación → archivos de partida →
elegir o crear → menú principal → jugar. La partida se decide antes de que
haya nada que decidir sobre ella.

Qué cambia y qué no
-------------------
* `SplashScene` entrega a la pantalla de partidas, no al título.
* Elegir una partida lleva al **menú principal**, no directamente al
  escenario: el menú es lo que el jugador viene a ver, y saltárselo era lo
  que obligaba a volver atrás para entrar al inventario.
* `CONTINUAR` en el menú reanuda la partida activa. Sólo vuelve a la lista si
  no hay ninguna activa —un arranque de emergencia, por ejemplo tras un
  fallo—, porque ahí preguntar es mejor que adivinar.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core.save_data import SaveData
from src.engine.core.save_manager import SaveManager


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield


@pytest.fixture
def contexto(_video, tmp_path, monkeypatch):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager

    monkeypatch.setattr(SaveManager, "SAVES_DIR", tmp_path)
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


class TestElOrdenDelArranque:
    def test_la_presentacion_entrega_a_la_pantalla_de_partidas(self, contexto) -> None:
        from src.engine.scenes.load_game_scene import LoadGameScene
        from src.engine.scenes.splash_scene import SplashScene

        splash = SplashScene(contexto)
        contexto.scene_manager.push(splash)

        # Se deja correr la presentación entera y su fundido.
        for _ in range(int((SplashScene.SPLASH_TIME + 1.5) * 60)):
            contexto.scene_manager.update(1 / 60)
            contexto.scene_manager.transition.update(1 / 60)

        assert isinstance(contexto.scene_manager.current, LoadGameScene), (
            f"la presentación entregó a "
            f"{type(contexto.scene_manager.current).__name__}: el juego sigue "
            f"empezando sin preguntar en qué partida"
        )


class TestElegirPartidaLlevaAlMenu:
    def test_cargar_una_partida_abre_el_menu_principal(self, contexto) -> None:
        from src.engine.scenes.load_game_scene import LoadGameScene
        from src.engine.scenes.title_scene import TitleScene

        contexto.save_manager.save(
            1, SaveData(slot_id=1, stage_id="stage0", profile_name="Pablo"))

        pantalla = LoadGameScene(contexto)
        contexto.scene_manager.push(pantalla)
        pantalla.on_enter()
        pantalla.seleccionar(0)
        pantalla._cargar_partida(contexto.save_manager.load(1))

        assert isinstance(contexto.scene_manager.current, TitleScene), (
            "elegir partida saltaba directamente al escenario, y entrar al "
            "inventario obligaba a volver atrás"
        )

    def test_la_partida_elegida_queda_activa(self, contexto) -> None:
        from src.engine.scenes.load_game_scene import LoadGameScene

        contexto.save_manager.save(
            2, SaveData(slot_id=2, stage_id="stage0", profile_name="Ana"))
        pantalla = LoadGameScene(contexto)
        contexto.scene_manager.push(pantalla)
        pantalla.on_enter()
        pantalla._cargar_partida(contexto.save_manager.load(2))

        assert contexto.save_manager.ranura_activa == 2


class TestContinuarDesdeElMenu:
    def test_continuar_sin_partida_activa_pregunta(self, contexto) -> None:
        """El arranque de emergencia: preguntar es mejor que adivinar."""
        from src.engine.scenes.load_game_scene import LoadGameScene
        from src.engine.scenes.title_scene import TitleScene

        assert contexto.save_manager.ranura_activa is None
        titulo = TitleScene(contexto)
        contexto.scene_manager.push(titulo)
        titulo._activate_option("CONTINUE")

        assert isinstance(contexto.scene_manager.current, LoadGameScene)

    def test_continuar_con_partida_activa_entra_al_juego(self, contexto) -> None:
        """Entra a un escenario de verdad, no a otra pantalla cualquiera.

        Comprobar sólo «no es el título» dejaría pasar el propio defecto: ir a
        la lista de partidas tampoco es el título.
        """
        from src.engine.core.stage_registry import discover_stages
        from src.engine.scenes.load_game_scene import LoadGameScene
        from src.engine.scenes.title_scene import TitleScene

        escenarios = discover_stages()
        if not escenarios:
            pytest.skip("no hay escenarios instalados")

        contexto.save_manager.save(
            1, SaveData(slot_id=1, stage_id="stage0", profile_name="Pablo"))
        contexto.save_manager.ranura_activa = 1

        titulo = TitleScene(contexto)
        contexto.scene_manager.push(titulo)
        titulo._activate_option("CONTINUE")

        actual = contexto.scene_manager.current
        assert not isinstance(actual, LoadGameScene | TitleScene), (
            f"CONTINUAR con una partida ya elegida acabó en "
            f"{type(actual).__name__}: vuelve a preguntar cuál"
        )
        assert isinstance(actual, escenarios[0]), (
            f"se entró a {type(actual).__name__} y la partida decía stage0"
        )
