"""AUD-354: dibujar un fotograma con la pila de escenas vacía, por la GPU.

El hallazgo
===========

`App._draw` liga el nombre `escena` **dentro** del `if` que comprueba que hay
algo en la pila::

    if self.scene_manager.stack_size > 0:
        escena = self.scene_manager.current
        ...

y lo vuelve a leer ciento cincuenta líneas más abajo, ya **fuera** de ese
`if`, en la rama de GPU que compone la interfaz de AUD-343::

    if self._use_gl and self._gl_renderer:
        ...
        if callable(getattr(escena, "dibujar_ui", None)):   # <-- sin ligar

Con la pila vacía y la tarjeta activa, ese acceso es un `UnboundLocalError`.

Por qué importa, y por qué no salió en la suite
-----------------------------------------------

La pila se vacía cuando la escena de más arriba es la única y se saca
(`SceneManager.pop` no tiene suelo: `game_over_scene.py:70` y
`combo_demo_scene.py:106` sacan la suya sin comprobar quién queda debajo).
El bucle de `run()` no vuelve a mirar la pila entre `update` y `_draw`, así
que el fotograma que sigue a ese `pop` dibuja con la pila a cero.

No falló en CI porque **en CI no hay GPU**: `_use_gl` es `False` en las 4.335
pruebas y el camino roto es exactamente el que allí no se ejecuta. Es el modo
de fallo que este repositorio ya conoce con otro nombre (AUD-343: la tubería
GL entera fue código muerto durante meses porque el único camino que la
activaba reventaba en silencio) — código que sólo corre en la máquina del
jugador es código que ninguna prueba mira, salvo que se le monte el contexto
a mano. Eso es lo que hace este fichero.

El daño no es un cierre: `run()` atrapa la excepción de `_draw`, la registra y
llama a `_fallback_to_title()`. El jugador ve la pantalla de título aparecer
sola. Diez fotogramas así seguidos y `MAX_CONSECUTIVE_FRAME_ERRORS` aborta el
juego.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from unittest.mock import MagicMock

import pygame

from src.engine.core import settings
from src.engine.core.app import App


def _app_con_gpu(stack_size: int) -> tuple[App, MagicMock]:
    """Una `App` sin arrancar, con lo mínimo que `_draw` toca.

    No se llama a `App()`: abrir ventana, mezclador y subsistemas para
    comprobar una ligadura de nombre sería medir otra cosa. `__new__` deja el
    objeto con la clase real —el método bajo prueba es el de producción— y se
    le cuelgan las colaboraciones que `_draw` usa.
    """
    app = App.__new__(App)
    tam = (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
    app.internal_surface = pygame.Surface(tam)
    app._ui_overlay_surface = pygame.Surface(tam, pygame.SRCALPHA)

    gestor = MagicMock()
    gestor.stack_size = stack_size
    if stack_size == 0:
        # `SceneManager.current` levanta RuntimeError con la pila vacía; el
        # doble tiene que ser igual de estricto o la prueba pasaría por un
        # motivo falso.
        type(gestor).current = property(
            lambda _self: (_ for _ in ()).throw(
                RuntimeError("SceneManager: no scenes on the stack")))
    app.scene_manager = gestor

    app.debug_overlay = MagicMock()
    app.debug_overlay.visible = False
    app.clock = MagicMock()
    app.clock.fps = 60.0
    app._use_gl = True
    renderer = MagicMock()
    app._gl_renderer = renderer
    return app, renderer


class TestLaPilaVaciaConLaTarjetaActiva:

    def test_dibujar_sin_escenas_no_revienta(self) -> None:
        """El fotograma que sigue al `pop` de la última escena."""
        app, renderer = _app_con_gpu(stack_size=0)

        app._draw(0.016)

        # Y llega a la tarjeta: sin escena no hay overlay que componer, pero
        # el fotograma (fondo + transición) sí se presenta. Saltarse el
        # `render` dejaría la pantalla congelada en el fotograma anterior.
        assert renderer.render.call_count == 1
        assert renderer.render.call_args.kwargs["overlay"] is None

    def test_con_escena_de_gpu_el_overlay_sigue_llegando(self) -> None:
        """La ruta de AUD-343 no se toca: quien parte el dibujo, compone."""
        app, renderer = _app_con_gpu(stack_size=1)
        escena = MagicMock(spec=["dibujar_mundo", "dibujar_ui", "light_surface"])
        escena.light_surface = None
        app.scene_manager.current = escena

        app._draw(0.016)

        escena.dibujar_mundo.assert_called_once_with(app.internal_surface)
        escena.dibujar_ui.assert_called_once_with(app._ui_overlay_surface)
        assert renderer.render.call_args.kwargs["overlay"] is app._ui_overlay_surface

    def test_una_escena_de_cpu_no_aporta_overlay(self) -> None:
        """Un menú dibuja de una vez y su fotograma entero pasa por la cadena."""
        app, renderer = _app_con_gpu(stack_size=1)
        escena = MagicMock(spec=["draw"])
        app.scene_manager.current = escena

        app._draw(0.016)

        escena.draw.assert_called_once_with(app.internal_surface)
        assert renderer.render.call_args.kwargs["overlay"] is None
