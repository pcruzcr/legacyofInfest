"""AUD-437 — la imagen se congelaba con el juego corriendo por debajo.

El síntoma que lo destapó
------------------------
«La pantalla se pega, el ratón mueve el arco para disparar, el sonido sigue,
pero lo visual no funciona.» Eso **no es un cuelgue**: si la entrada llega y
el audio avanza, el bucle de juego está vivo. Lo único que dejó de pasar es
que el fotograma se presente.

Y hay exactamente un sitio donde puede dejar de pasar. En el árbol sólo
existen dos `pygame.display.flip()`:

* `App.run` — pero **sólo** `if not self._use_gl`. Con tarjeta, `App` no
  presenta nunca; delega.
* `GLRenderer.render` — al final del camino completo, después de toda la
  cadena de pasadas.

`render()` empieza con una salida temprana: si el contexto no está listo
(`not self._initialized or self.ctx is None`) llama a `_software_fallback` y
**retorna sin presentar**. `_software_fallback` escala la superficie sobre la
del sistema y tampoco presenta. Resultado: con `_use_gl` puesto y esa rama
activa, nadie hace flip en ningún fotograma. La ventana se queda en la última
imagen presentada mientras el mundo, el sonido y el ratón siguen su curso —
que es justo lo que se ve.

La forma del defecto
--------------------
El fotograma se dibujaba en dos sitios y se presentaba en uno solo de los dos
caminos posibles. Presentar es parte de dibujar: una función que se llama
«dibuja este fotograma sin GL» y deja la imagen sin publicar no ha terminado
su trabajo. Por eso el arreglo va dentro de `_software_fallback` y no en un
`if` más arriba: así **toda** salida de `render()` presenta exactamente una vez.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.render.gl_pipeline import GLRenderConfig, GLRenderer


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))
    yield


@pytest.fixture
def contador_de_flips(monkeypatch):
    """Cuenta las presentaciones sin dejar que SDL las haga de verdad."""
    caja = {"n": 0}

    def falso_flip() -> None:
        caja["n"] += 1

    monkeypatch.setattr(pygame.display, "flip", falso_flip)
    return caja


def test_sin_contexto_gl_el_fotograma_se_sigue_presentando(
    _video, contador_de_flips,
) -> None:
    """El defecto exacto: la rama de reserva dibujaba y no publicaba.

    Un `GLRenderer` recién construido tiene `_initialized = False`, que es la
    misma condición que dispara la salida temprana en producción cuando el
    contexto se pierde o no llegó a montarse.
    """
    renderer = GLRenderer(GLRenderConfig())
    assert not renderer._initialized, (
        "la premisa de esta prueba es que el renderizador NO está inicializado"
    )

    escena = pygame.Surface((320, 240))
    escena.fill((40, 80, 120))
    renderer.render(escena)

    assert contador_de_flips["n"] == 1, (
        f"render() salió por la rama de reserva y presentó "
        f"{contador_de_flips['n']} veces. Con `_use_gl` puesto, `App.run` no "
        f"hace flip: si éste tampoco, la ventana se congela en el fotograma "
        f"anterior mientras el juego sigue corriendo por debajo."
    )


def test_varios_fotogramas_seguidos_presentan_uno_cada_uno(
    _video, contador_de_flips,
) -> None:
    """Un fotograma, una presentación: ni de más ni de menos.

    Presentar dos veces por vuelta no congela nada pero tira medio fotograma
    de trabajo y puede partir la imagen, así que el número exacto importa.
    """
    renderer = GLRenderer(GLRenderConfig())
    escena = pygame.Surface((320, 240))
    for _ in range(5):
        renderer.render(escena)
    assert contador_de_flips["n"] == 5


@pytest.mark.parametrize("tam_escena", [(320, 240), (800, 600), (640, 360)])
def test_la_reserva_aguanta_cualquier_tamano_de_escena(
    _video, contador_de_flips, tam_escena: tuple[int, int],
) -> None:
    """La ruta de emergencia no puede ser la que rompa el fotograma.

    `scale_by(origen, factor, destino)` exige que el destino mida exactamente
    origen × factor y lanza `ValueError: Destination surface not the given
    width or height` si no. No tiene por qué medirlo: `App` abre la ventana a
    la resolución interna y deja que SDL la reescale (AUD-013), así que el
    factor del config no describe esa relación. Se descubrió porque estas
    mismas pruebas pasaban solas y reventaban en lote, cuando otro fichero
    había dejado la ventana de otro tamaño.
    """
    renderer = GLRenderer(GLRenderConfig())
    escena = pygame.Surface(tam_escena)
    escena.fill((10, 200, 90))
    renderer.render(escena)          # no debe lanzar
    assert contador_de_flips["n"] == 1


def test_la_reserva_deja_la_imagen_en_la_superficie_del_sistema(
    _video, contador_de_flips,
) -> None:
    """Presentar una superficie en blanco no arreglaría nada.

    Sin esto, la prueba de arriba pasaría con un `flip()` suelto que publica
    un fotograma vacío: el jugador cambiaría una imagen congelada por una
    negra, que es peor.
    """
    renderer = GLRenderer(GLRenderConfig())
    escena = pygame.Surface((320, 240))
    escena.fill((200, 30, 60))
    pygame.display.get_surface().fill((0, 0, 0))

    renderer.render(escena)

    destino = pygame.display.get_surface()
    assert destino.get_at((destino.get_width() // 2, destino.get_height() // 2))[:3] != (0, 0, 0), (
        "la superficie del sistema quedó negra: se presentó un fotograma vacío"
    )
