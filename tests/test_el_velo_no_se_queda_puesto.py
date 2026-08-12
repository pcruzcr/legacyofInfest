"""AUD-434 — el velo de transición se quedaba puesto y dejaba la pantalla negra.

Qué fallaba
-----------
`TitleScene._activate_option` arranca un fundido de salida y **acto seguido**
cambia de escena. El velo lo levanta la escena de destino llamando a
`start_fade_in` en su `on_enter`. Trece pantallas lo hacen; dos no —
`LeaderboardScene` (RÉCORDS) y `SkillTreeScene` (HABILIDADES)—, así que el
fundido de salida llegaba a su fin, `TransitionManager.update` dejaba
`_fade_alpha` en 255, y `draw` lo pinta siempre que el alfa sea mayor que cero
mire o no si la transición sigue viva. Resultado: la pantalla aparecía, se
oscurecía y se quedaba en negro con la escena corriendo debajo.

Ya había pasado antes. AUD-201 lo sufrió con BOSS RUSH y lo arregló **en la
llamada**, reordenando dos líneas de `title_scene`, dejando escrito el
diagnóstico y sin tocar la causa. Un contrato que obliga a treinta escenas a
acordarse de levantar un velo que no pusieron ellas es un contrato que se
volverá a incumplir: van dos de dos.

Por eso la garantía se mueve a donde se sabe que hubo cambio de escena —
`SceneManager` — y se expresa en el objeto que es dueño del estado del velo.
Una escena que quiera su propio fundido lo sigue pidiendo y se respeta.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.scenes.transition_manager import TransitionManager


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield


def _agotar(tm: TransitionManager, segundos: float = 2.0) -> None:
    for _ in range(int(segundos * 60)):
        tm.update(1 / 60)


# ── la unidad: qué hace el gestor del velo ────────────────────────


def test_un_fundido_de_salida_terminado_deja_el_velo_opaco(_video) -> None:
    """El punto de partida del defecto, fijado para que no se pierda."""
    tm = TransitionManager()
    tm.start_fade_out(0.4)
    _agotar(tm)
    assert not tm.active
    assert tm._fade_alpha == 255, (
        "si esto cambia, la premisa de AUD-434 ya no se sostiene y el resto "
        "de este fichero mide otra cosa"
    )

    superficie = pygame.Surface((800, 600))
    superficie.fill((90, 120, 200))
    tm.draw(superficie)
    assert superficie.get_at((400, 300))[:3] == (0, 0, 0), (
        "el velo terminado tiene que seguir tapando: es lo que cubre el "
        "cambio de escena hasta que alguien lo levanta"
    )


def test_asegurar_entrada_levanta_un_velo_que_nadie_reclamo(_video) -> None:
    tm = TransitionManager()
    tm.start_fade_out(0.4)
    _agotar(tm)

    tm.asegurar_fundido_de_entrada(0.4)
    _agotar(tm)

    assert tm._fade_alpha == 0
    superficie = pygame.Surface((800, 600))
    superficie.fill((90, 120, 200))
    tm.draw(superficie)
    assert superficie.get_at((400, 300))[:3] == (90, 120, 200)


def test_asegurar_entrada_respeta_el_fundido_que_pidio_la_escena(_video) -> None:
    """Una escena con su propio fundido no debe ver cómo se lo reinician.

    Es la diferencia entre una red de seguridad y una imposición: trece
    pantallas ya piden su entrada con su propia duración, y pisarlas cambiaría
    el ritmo de trece transiciones que hoy están bien.
    """
    tm = TransitionManager()
    tm.start_fade_in(0.9)
    tm.update(1 / 60)
    restante = tm._fade_timer

    tm.asegurar_fundido_de_entrada(0.2)

    assert tm._fade_timer == pytest.approx(restante), (
        "se reinició el fundido que la escena ya había pedido"
    )


def test_asegurar_entrada_no_inventa_un_fundido_si_no_hay_velo(_video) -> None:
    """Sin velo puesto no hay nada que levantar, y meter uno sería un parpadeo."""
    tm = TransitionManager()
    assert tm._fade_alpha == 0
    tm.asegurar_fundido_de_entrada(0.4)
    assert not tm.active, "se arrancó un fundido donde no había nada que tapar"


def test_asegurar_entrada_no_toca_los_otros_modos(_video) -> None:
    """`wipe`, `slide` y `circle` no usan el alfa: no son asunto de esto."""
    tm = TransitionManager()
    vieja = pygame.Surface((800, 600))
    tm.start_wipe("left", 0.4, old_surface=vieja)
    tm.asegurar_fundido_de_entrada(0.4)
    assert tm._mode == "wipe"


# ── la integración: el camino que el jugador recorre de verdad ────


@pytest.fixture
def contexto(_video):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager

    ctx = GameContext(
        input_manager=InputManager(),
        audio_manager=AudioManager(),
        scene_manager=None,
        event_bus=EventBus(),
        clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


#: Las dos que no pedían su fundido, y una tercera que sí lo pide, como control.
#: Sin el control, esta prueba pasaría igual si el arreglo rompiera las trece
#: pantallas que hoy funcionan.
@pytest.mark.parametrize(("modulo", "clase"), [
    ("leaderboard_scene", "LeaderboardScene"),
    ("skill_tree_scene", "SkillTreeScene"),
    ("inventory_scene", "InventoryScene"),
])
def test_entrar_desde_el_titulo_no_deja_la_pantalla_en_negro(
    contexto, modulo: str, clase: str,
) -> None:
    import importlib

    mod = importlib.import_module(f"src.engine.scenes.{modulo}")
    escena = getattr(mod, clase)(contexto)

    gestor = contexto.scene_manager
    # Exactamente lo que hace `TitleScene._activate_option`.
    gestor.transition.start_fade_out(0.4)
    gestor.replace(escena)

    superficie = pygame.Surface((800, 600))
    for _ in range(120):                      # dos segundos
        gestor.update(1 / 60)
        gestor.transition.update(1 / 60)
        superficie.fill((0, 0, 0))
        gestor.current.draw(superficie)
        gestor.transition.draw(superficie)

    assert gestor.transition._fade_alpha == 0, (
        f"{clase}: dos segundos después de entrar, el velo sigue en alfa "
        f"{gestor.transition._fade_alpha}. La escena corre debajo de una "
        f"pantalla negra."
    )
    assert pygame.transform.average_color(superficie)[:3] != (0, 0, 0), (
        f"{clase}: el fotograma final es completamente negro"
    )
