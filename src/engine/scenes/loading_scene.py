"""
Module: loading_scene
System: engine.scenes
Academic Unit: N/A
Description: Pantalla de carga con barra de progreso y trabajo en un hilo.

Dónde estaba esto (AUD-288)
===========================
Escrita, probada y **sin un solo llamante**. No estaba ni en el registro de
escenas: la única referencia en todo el repositorio era `test_scene_smoke.py`.
`docs/63` la daba por «falso positivo del barrido: el registro las construye por
cadena», y era mentira — se corrigió al medirlo.

Y el sitio obvio para engancharla —la transición entre escenarios— resultó ser
**el equivocado**, cosa que sólo se supo midiendo. Entrar en un escenario cuesta
entre 41 ms (`lobby_datacenter`) y 134 ms (`stage1_3_las_aulas`); el peor caso en
frío ronda los 163 ms. Una pantalla de carga que aparece y desaparece en una
décima de segundo no informa: parpadea, y un parpadeo se lee como un fallo de
vídeo. Ahí no hace falta.

Donde sí hacía falta era en el laboratorio de la Unidad IX: abrir
`PatternDemoScene` **congelaba el juego 2,8 s** —3,5 s la primera vez— porque
`reference_model.obtener_modelo()` importa scikit-learn y carga o entrena el
modelo, todo en el hilo del dibujado. Tres segundos de pantalla negra sin nada
que mirar, en la demo que el profesor abre delante de la clase.

Ese trabajo además es el ideal para un hilo: CPU pura, sin una sola llamada a
SDL. Las superficies de pygame no se tocan desde el trabajador.

El umbral, y por qué existe
===========================
`umbral_para_mostrarse` es lo que hace que esta pantalla sirva para las dos
cosas: si la carga termina antes, la escena **no se dibuja nunca** y se pasa de
largo. Así se puede enchufar sin medir antes cada caso, sin miedo a meter un
parpadeo donde no hacía falta.
"""
from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.theme import Theme, font
from src.engine.ui.widgets import draw_progress_bar

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class LoadTask:
    def __init__(self, name: str, fn: Callable[[], None], weight: float = 1.0) -> None:
        self.name = name
        self.fn = fn
        self.weight = weight
        self.done = False


#: Segundos que tiene que durar una carga para que la pantalla llegue a verse.
#:
#: Un cuarto de segundo. Por debajo, una pantalla de carga aparece y se va antes
#: de que el ojo la resuelva, y eso no se lee como «estaba cargando»: se lee
#: como un parpadeo, o sea como un fallo. Por encima, el jugador ya está
#: preguntándose si el juego se ha colgado y agradece la barra.
UMBRAL_PARA_MOSTRARSE: float = 0.25


class LoadingScene(BaseScene):
    """Loading screen with progress bar for async asset loading."""

    def __init__(
        self,
        context: GameContext,
        next_scene: BaseScene | None = None,
        tasks: list[LoadTask] | None = None,
        umbral_para_mostrarse: float = UMBRAL_PARA_MOSTRARSE,
    ) -> None:
        super().__init__(context)
        self._umbral = max(0.0, float(umbral_para_mostrarse))
        self._esperado: float = 0.0
        self._next_scene = next_scene
        self._tasks = tasks or []
        self._lock = threading.Lock()
        self._progress: float = 0.0
        self._total_weight: float = max(sum(t.weight for t in self._tasks), 0.01)
        self._current_task_name: str = ""
        self._loading_done: bool = False
        self._thread: threading.Thread | None = None
        self._is_loading: bool = False
        self._startup_alpha: float = 0.0
        self._startup_done: bool = False
        self._fade_out: float = 0.0
        self._fading_out: bool = False
        self._fade_surf: pygame.Surface | None = None
        # AUD-069: escala del tema y caché compartida.
        self._font_info = font(Theme.FONT_TINY)
        self._font_title = font(Theme.FONT_SMALL)

    def set_next_scene(self, scene: BaseScene) -> None:
        self._next_scene = scene

    def add_task(self, task: LoadTask) -> None:
        with self._lock:
            self._tasks.append(task)
            self._total_weight = max(sum(t.weight for t in self._tasks), 0.01)

    def _load_worker(self) -> None:
        completed = 0.0
        for task in self._tasks:
            with self._lock:
                self._current_task_name = task.name
            try:
                task.fn()
            except Exception as e:
                logger.warning("loading_scene: task '%s' failed: %s", task.name, e)
                with self._lock:
                    self._current_task_name = f"Error: {e}"
            task.done = True
            completed += task.weight
            with self._lock:
                self._progress = completed / self._total_weight
        with self._lock:
            self._loading_done = True

    def on_enter(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        with self._lock:
            self._progress = 0.0
            self._loading_done = False
            self._current_task_name = ""
        self._startup_alpha = 0.0
        self._startup_done = False
        self._fade_out = 1.0
        self._fading_out = False
        self._esperado = 0.0
        if self._tasks:
            self._is_loading = True
            self._thread = threading.Thread(target=self._load_worker, daemon=True)
            self._thread.start()
        else:
            with self._lock:
                self._loading_done = True

    def on_exit(self) -> None:
        """Wait for the loader thread before the scene goes away.

        AUD-042: ``BaseScene.on_exit`` is abstract and ``LoadingScene`` never
        implemented it, which made the class **impossible to instantiate** —
        ``TypeError: Can't instantiate abstract class LoadingScene``. The
        loading screen has therefore never been usable, which is also why
        ``set_next_scene`` and ``add_task`` showed up as unreferenced in the
        dead-code scan (AUD-022).

        Joining matters beyond satisfying the ABC: the worker is a daemon
        thread that writes to ``self._progress`` and ``self._current_task_name``
        under a lock. Letting the scene be collected while it still runs means
        a background thread mutating a dead object, and asset loads continuing
        to compete for I/O with whatever scene comes next.
        """
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=5.0)
            if thread.is_alive():
                logger.warning(
                    "LoadingScene: loader thread did not finish within 5 s; "
                    "continuing without it",
                )
        self._thread = None
        self._is_loading = False

    @property
    def visible_todavia(self) -> bool:
        """¿Ha pasado ya el umbral, o seguimos esperando en silencio?

        Lo consulta `draw`. Público porque es lo que una prueba tiene que poder
        preguntar sin hurgar en atributos privados.
        """
        return self._esperado >= self._umbral

    def update(self, dt: float) -> None:
        # AUD-288 — el silencio de los primeros milisegundos.
        #
        # Mientras no se cumpla el umbral no se dibuja nada y no se cuenta el
        # fundido de entrada: si la carga acaba dentro de esa ventana, la
        # escena se sustituye sin haber pintado un solo fotograma y el jugador
        # no ve un parpadeo.
        self._esperado += dt
        if not self.visible_todavia:
            with self._lock:
                if self._loading_done:
                    if self._next_scene is not None:
                        self.context.scene_manager.replace(self._next_scene)
                    return
            return

        if not self._startup_done:
            self._startup_alpha = min(1.0, self._startup_alpha + dt * 2.0)
            if self._startup_alpha >= 1.0:
                self._startup_done = True
            return

        with self._lock:
            loading_done = self._loading_done

        if loading_done and not self._fading_out:
            self._fading_out = True

        if self._fading_out:
            self._fade_out = max(0.0, self._fade_out - dt * 1.5)
            if self._fade_out <= 0.0 and self._next_scene is not None:
                self.context.scene_manager.replace(self._next_scene)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible_todavia:
            return
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        # Fondo del kit: antes `(10,10,20)`, uno de los seis grises oscuros
        # distintos que el juego usaba para decir «pantalla».
        surface.fill(Theme.BG)
        with self._lock:
            progress = self._progress
            task_name = self._current_task_name

        # Loading bar
        bar_w = 200
        bar_h = 16
        bx = (w - bar_w) // 2
        by = h // 2

        # La barra la dibuja el kit: era un degradado hecho a mano línea por
        # línea, dieciséis `draw.line` por fotograma para un efecto que ninguna
        # otra pantalla comparte.
        draw_progress_bar(surface, pygame.Rect(bx, by, bar_w, bar_h), progress)

        text = f"Cargando {task_name}…" if task_name else "Cargando…"
        label = self._font_info.render(text, True, Theme.TEXT_MUTED)
        surface.blit(label, (bx, by - 18))

        pct = self._font_info.render(f"{int(progress * 100)}%", True, Theme.TEXT)
        px = bx + bar_w + 8
        surface.blit(pct, (px, by + 1))

        # Title
        title = self._font_title.render("LEGACY OF INFEST", True, Theme.ACCENT)
        surface.blit(title, ((w - title.get_width()) // 2, by - 50))

        # Fade overlay
        if self._fade_surf is None or self._fade_surf.get_size() != (w, h):
            self._fade_surf = pygame.Surface((w, h))
        if not self._startup_done:
            self._fade_surf.set_alpha(int((1.0 - self._startup_alpha) * 255))
            self._fade_surf.fill((0, 0, 0))
            surface.blit(self._fade_surf, (0, 0))
        elif self._fading_out:
            self._fade_surf.set_alpha(int(self._fade_out * 255))
            self._fade_surf.fill((0, 0, 0))
            surface.blit(self._fade_surf, (0, 0))
