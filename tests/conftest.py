"""
Shared test fixtures for the Legacy of InFest test suite.
"""
from __future__ import annotations

import os
import sys

# Set dummy video driver BEFORE any pygame import so display.set_mode
# never triggers the "no fast renderer available" warning.
os.environ["SDL_VIDEODRIVER"] = "dummy"
# Also hide pygame support prompt
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import warnings

import pygame
import pytest

# Suppress harmless pygame-ce SCALED warning under dummy driver
warnings.filterwarnings("ignore", message="no fast renderer available", category=Warning)


@pytest.fixture(scope="session")
def _pygame_init():
    """Initialize pygame once per test session for surface-dependent tests."""
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def event_bus():
    """Provide a fresh EventBus instance for each test."""
    from src.engine.core.event_bus import EventBus
    return EventBus()


@pytest.fixture(autouse=True)
def _reset_global_state():
    """Reset global singletons before each test to prevent cross-test contamination.

    AUD-019: there is no longer a module-level default EventBus to clear —
    every consumer receives its bus by injection, so a test's bus cannot leak
    into another test. Only genuinely process-wide caches are reset here.

    AUD-220 — las preferencias del jugador también son estado global
    ----------------------------------------------------------------
    `user_settings.get()` **carga del disco** en la primera lectura, así que sin
    esto la suite corría con el `config.json` de quien la ejecutara. En la
    máquina donde se detectó, `text_scale` estaba en 2.0 —la ayuda de
    accesibilidad al máximo—, de modo que `theme.font(20)` devolvía 40 px
    durante toda la suite y en CI devolvía 20. Dos máquinas, dos resultados, el
    mismo commit.

    Lo destapó una prueba de tipografía que pasaba sin comprobar nada: comparaba
    `font(N)` contra `Font(None, N)` sin saber que la primera venía multiplicada.

    Se instalan las preferencias **de fábrica**, no las del disco. Una prueba
    que necesite otra cosa lo declara con `set_settings()`, que para eso está.

    AUD-545 — `Inventory` también es singleton de proceso, y se coló sin
    reseteo aquí igual que `AchievementSystem` lo tenía.
    ------------------------------------------------------------------------
    `collect()` deja en cola una notificación («ITEM: …») que sólo se
    consume dibujándola unos fotogramas. Sin resetear el singleton, cualquier
    prueba que recogiera un objeto dejaba esa notificación pendiente para la
    siguiente prueba del proceso que construyera una escena — visible o no
    según cuántos fotogramas corriera esa otra prueba.

    Encontrado así: `test_reported_ui_bugs.py::test_el_hud_conserva_su_brillo`
    fallaba sólo en la suite completa, con la misma razón de brillo exacta
    en ejecuciones separadas — bit a bit igual, no un número distinto cada
    vez, que es la firma de estado compartido y no de una máquina cargada.
    Comparando pixel a pixel el HUD aislado contra el compuesto completo, la
    diferencia no estaba en la luz del mundo (que es lo que esa prueba existe
    para vigilar, AUD-090) sino en un aviso de recogida ajeno dibujado sobre
    el reloj del HUD, propiedad de una prueba anterior sin relación.
    """
    from src.engine.core import user_settings
    from src.engine.core.achievements import AchievementSystem
    from src.engine.core.inventory import Inventory
    from src.engine.scenes.demo_layout import clear_demo_font_cache
    from src.engine.ui.theme import clear_font_cache
    from src.engine.utils.asset_loader import AssetLoader
    from src.framework.stage.stage_loader import StageLoader
    AssetLoader.clear_cache()
    AssetLoader._get_instance()._scopes = 0
    StageLoader.clear_tmx_cache()
    clear_demo_font_cache()
    AchievementSystem._reset_instance()
    Inventory._reset_instance()
    user_settings.set_settings(user_settings.UserSettings())
    # La caché de fuentes indexa por (ruta, tamaño ya escalado): si sobrevive a
    # un cambio de escala, la prueba siguiente recibe la fuente de la anterior.
    clear_font_cache()
    # Drain the pygame event queue so key presses posted by a previous test
    # (e.g. menu-navigation tests that post synthetic KEYDOWN events) cannot
    # leak into the next test's fresh App and be misinterpreted as input.
    #
    # AUD-120 — la guarda no es decorativa. `pygame.event.clear()` lanza
    # «video system not initialized» si nadie ha llamado a `pygame.init()`
    # todavía, y esta función corre **antes de cada prueba**, incluidas las
    # que no necesitan vídeo. El síntoma era que `pytest tests/test_clock.py`
    # a secas daba cuatro errores y la misma orden con cualquier otro fichero
    # delante pasaba: el otro fichero inicializaba pygame de camino.
    #
    # Una suite en la que el resultado depende de qué otro fichero corrió
    # antes no es una suite, es una lotería. Y el que la sufre es quien
    # ejecuta una sola prueba para depurar, que es justo cuando menos falta
    # hace un misterio.
    if pygame.display.get_init():
        pygame.event.clear()

    # AUD-616 — mixer global: canales ocupados por ambientes en bucle
    # (loops=-1) de tests anteriores. Sin reset, find_channel() devuelve None
    # y _ambient_active miente. Se para todo y se liberan los canales.
    if pygame.mixer.get_init():
        pygame.mixer.stop()
        # Fuerza liberación real de canales bajo dummy driver
        for ch in range(pygame.mixer.get_num_channels()):
            pygame.mixer.Channel(ch).stop()

    # AUD-616 — azar global: random y np.random. GAP-042 aisla con
    # azar.generador() pero código legado aún usa random.* directo.
    # Se resiembra ambos para que cada test empiece determinista.
    import random

    import numpy as np

    from src.engine.core import azar
    semilla = azar.semilla_actual()
    if semilla is not None:
        random.seed(semilla)
        np.random.seed(semilla % (2**32 - 1))


@pytest.fixture
def sample_surface_32x32(_pygame_init) -> pygame.Surface:
    """A 32×32 solid gray surface — canonical input for processing tools."""
    surf = pygame.Surface((32, 32))
    surf.fill((128, 128, 128))
    return surf


@pytest.fixture
def sample_surface_64x64(_pygame_init) -> pygame.Surface:
    """A 64×64 surface with a gradient pattern for filter/vision tests."""
    surf = pygame.Surface((64, 64))
    for x in range(64):
        for y in range(64):
            r = (x * 4) % 256
            g = (y * 4) % 256
            b = ((x + y) * 2) % 256
            surf.set_at((x, y), (r, g, b))
    return surf


@pytest.fixture
def sample_surface_bw_32x32(_pygame_init) -> pygame.Surface:
    """A 32×32 black-and-white checkerboard surface for threshold/morph tests."""
    surf = pygame.Surface((32, 32))
    for x in range(32):
        for y in range(32):
            v = 255 if (x // 4 + y // 4) % 2 == 0 else 0
            surf.set_at((x, y), (v, v, v))
    return surf


# ── AUD-363: el presupuesto de tiempo de la suite ───────────────────────────
#
# Una suite que se hace lenta poco a poco deja de ejecutarse antes de cada
# commit, y entonces protege lo mismo que una que no existe. Esto es lo único
# que puede medirla: una prueba no puede cronometrar la sesión que la
# contiene.
#
# Sólo se aplica a la ejecución **completa**. Un lote dirigido —lo que se corre
# noventa veces al día mientras se programa— no tiene nada que ver con el
# presupuesto de la suite, y hacerlo saltar ahí sería ruido.
_INICIO_DE_SESION: float = 0.0

#: Debajo de esto se asume lote dirigido, no suite completa. La suite ronda
#: las 4.400 pruebas; 3.000 deja margen para que alguien añada o quite
#: ficheros sin desactivar el guardia por accidente.
_PRUEBAS_MINIMAS_PARA_MEDIR: int = 3_000


def pytest_sessionstart(session):
    global _INICIO_DE_SESION
    import time

    _INICIO_DE_SESION = time.perf_counter()


def pytest_sessionfinish(session, exitstatus):
    """Falla la sesión completa si la suite se pasa de su presupuesto.

    Se avisa por stderr **y** se cambia el estado de salida: un aviso que sólo
    se imprime se pierde entre las cien líneas del resumen de pytest, que es
    exactamente cómo los veinte avisos de obsolescencia de AUD-357 sobrevivieron
    tanto tiempo.
    """
    import time

    recogidas = getattr(session, "testscollected", 0) or 0
    if recogidas < _PRUEBAS_MINIMAS_PARA_MEDIR or _INICIO_DE_SESION == 0.0:
        return
    from tests.test_la_suite_se_vigila_a_si_misma import PRESUPUESTO_DE_SUITE_S

    duracion = time.perf_counter() - _INICIO_DE_SESION
    if duracion <= PRESUPUESTO_DE_SUITE_S:
        return
    print(
        f"\n[AUD-363] la suite tardó {duracion:.0f} s y el presupuesto son "
        f"{PRESUPUESTO_DE_SUITE_S:.0f} s. Si la máquina no estaba cargada, "
        f"esto es una regresión de tiempo: mira `pytest --durations=20`.",
        file=sys.stderr,
    )
    session.exitstatus = 1
