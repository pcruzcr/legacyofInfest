"""AUD-288 — la pantalla de carga estaba escrita y no la usaba nadie.

Los dos hallazgos
-----------------
1. **Era huérfana de verdad.** `docs/63` la daba por «falso positivo: el
   registro las construye por cadena». No: no está en `scene_registry` y su
   única referencia en todo el repositorio era `test_scene_smoke.py`. Se
   corrigió el documento al medirlo.

2. **El sitio obvio para engancharla era el equivocado.** Entrar en un escenario
   cuesta entre 41 y 134 ms; en frío, unos 163. Una pantalla de carga de una
   décima de segundo no informa, parpadea. Donde sí hacía falta era en el
   laboratorio de la Unidad IX: **2.461 ms** de congelación al abrirlo, porque
   importar scikit-learn y cargar el modelo ocurría en el hilo del dibujado.
   Precalentado, ese mismo `on_enter` tarda **2 ms**.

De ahí las dos cosas que se fijan aquí: el umbral que evita el parpadeo, y que
la demo de patrones se abra con precarga.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.engine.scenes.loading_scene import (
    UMBRAL_PARA_MOSTRARSE,
    LoadingScene,
    LoadTask,
)


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


@pytest.fixture
def contexto():
    from src.engine.audio.audio_manager import AudioManager
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


class TestElUmbralQueEvitaElParpadeo:
    def test_una_carga_corta_no_llega_a_dibujarse(self, contexto) -> None:
        """Aparecer y desaparecer en una décima de segundo no se lee como
        «estaba cargando»: se lee como un fallo de vídeo."""
        escena = LoadingScene(contexto, tasks=[LoadTask("nada", lambda: None)])
        escena.on_enter()
        escena.update(0.016)
        assert escena.visible_todavia is False

        superficie = pygame.Surface((800, 600))
        superficie.fill((0, 0, 0))
        escena.draw(superficie)
        assert superficie.get_at((10, 10))[:3] == (0, 0, 0), (
            "la pantalla de carga pintó algo antes del umbral"
        )
        escena.on_exit()

    def test_una_carga_larga_si(self, contexto) -> None:
        import threading

        puerta = threading.Event()
        escena = LoadingScene(contexto, tasks=[LoadTask("lenta", puerta.wait)])
        escena.on_enter()
        try:
            escena.update(UMBRAL_PARA_MOSTRARSE + 0.01)
            assert escena.visible_todavia is True
            superficie = pygame.Surface((800, 600))
            superficie.fill((0, 0, 0))
            escena.update(1.0)
            escena.draw(superficie)
            assert superficie.get_at((10, 10))[:3] != (0, 0, 0)
        finally:
            puerta.set()
            escena.on_exit()

    def test_sin_tareas_pasa_de_largo_sin_pintar(self, contexto) -> None:
        siguiente = _EscenaBoba(contexto)
        escena = LoadingScene(contexto, next_scene=siguiente)
        contexto.scene_manager.push(escena)
        escena.update(0.016)
        assert contexto.scene_manager.current is siguiente


class _EscenaBoba:
    """Escena mínima: `SceneManager` sólo le pide el ciclo de vida."""

    def __init__(self, context) -> None:
        self.context = context

    def awake(self) -> None: ...
    def start(self) -> None: ...
    def on_enter(self) -> None: ...
    def on_exit(self) -> None: ...
    def on_pause(self) -> None: ...
    def on_resume(self) -> None: ...
    def destroy(self) -> None: ...
    def process_events(self, events) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface) -> None: ...


class TestElTrabajoVaEnUnHilo:
    def test_la_tarea_se_ejecuta(self, contexto) -> None:
        hecho: list[str] = []
        escena = LoadingScene(contexto, tasks=[LoadTask("x", lambda: hecho.append("sí"))])
        escena.on_enter()
        escena.on_exit()   # hace join
        assert hecho == ["sí"]

    def test_una_tarea_que_falla_no_tumba_la_carga(self, contexto) -> None:
        """Es de estudiantes de quien se carga el código."""
        def _revienta():
            raise RuntimeError("dataset corrupto")

        escena = LoadingScene(contexto, tasks=[LoadTask("mala", _revienta)])
        escena.on_enter()
        escena.on_exit()
        assert escena._loading_done is True


class TestElLlamanteQueFaltaba:
    def test_el_menu_de_demos_precarga_la_de_patrones(self) -> None:
        """El caso medido: 2.461 ms de congelación al abrir la Unidad IX."""
        from src.engine.scenes.demo_menu_scene import DemoMenuScene

        assert "pattern" in DemoMenuScene._PRECARGAS

    def test_y_no_envuelve_las_que_abren_rápido(self, contexto) -> None:
        """Las demás abren en menos de 10 ms: envolverlas todas sería ruido."""
        from src.engine.scenes.demo_menu_scene import DemoMenuScene

        menu = object.__new__(DemoMenuScene)
        menu.context = contexto
        boba = _EscenaBoba(contexto)
        assert menu._con_precarga("vision", boba) is boba

    def test_la_de_patrones_sí(self, contexto) -> None:
        from src.engine.scenes.demo_menu_scene import DemoMenuScene

        menu = object.__new__(DemoMenuScene)
        menu.context = contexto
        envuelta = menu._con_precarga("pattern", _EscenaBoba(contexto))
        assert isinstance(envuelta, LoadingScene)

    def test_la_precarga_no_toca_pygame(self) -> None:
        """El trabajador corre fuera del hilo del dibujado: una llamada a SDL
        desde ahí es un fallo intermitente imposible de reproducir."""
        import inspect

        from src.engine.scenes import demo_menu_scene

        fuente = inspect.getsource(demo_menu_scene.DemoMenuScene._con_precarga)
        # Sin los comentarios: ahí la palabra aparece justamente para explicar
        # por qué no se usa.
        codigo = "\n".join(
            linea for linea in fuente.splitlines()
            if not linea.lstrip().startswith("#")
        )
        assert "pygame" not in codigo
        assert "obtener_modelo" in codigo
