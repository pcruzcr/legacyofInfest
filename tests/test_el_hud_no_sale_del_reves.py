"""AUD-435 — el HUD salía invertido y con rojo y azul cambiados en la ruta GL.

Qué fallaba
-----------
`_subir` tiene dos caminos y **sólo uno de ellos coloca los píxeles**:

* rápido   — `surface.get_view("0")`, la memoria cruda. Va en el orden de
             pygame (arriba abajo) y con los canales de la plataforma (BGRA en
             Windows). Colocarla es trabajo del sombreador `upload_frag`, que
             voltea la Y e intercambia rojo y azul.
* reserva  — `pygame.image.tobytes(s, "RGBA", True)`, que ya entrega los
             píxeles volteados y en RGBA. Ahí el sombreador correcto es
             `passthrough_frag`, que no toca nada.

La escena elige bien: `_upload_prog if _subida_directa(...) else
_passthrough_prog`. El overlay de interfaz de AUD-343 usaba
`_passthrough_prog` **siempre**, y su superficie (`SRCALPHA`, creada en
`App._init_pygame`) califica para el camino rápido igual que la escena. Así
que el HUD subía crudo y se pintaba sin colocar: del revés en vertical y con
los canales cambiados. El mundo se veía bien porque viene de un FBO, no de
`_subir`.

Por qué no basta con reutilizar `_upload_prog`
----------------------------------------------
`upload_frag` termina en `vec4(color, 1.0)`: fuerza el alfa a opaco, y lo hace
a propósito (la superficie interna del juego no tiene canal alfa y sin eso
salía todo el fotograma del color de limpieza). El overlay es justo lo
contrario: AUD-344 lo crea translúcido porque la pasada 9b lo compone con
`SRC_ALPHA`, y un overlay opaco tapa el mundo entero. Necesita el mismo
volteo y el mismo swizzle **conservando el alfa**, que es lo que hace
`overlay_frag`.

La lección de forma
-------------------
El defecto no fue elegir mal un programa: fue que la elección estaba escrita
dos veces, y la segunda copia se quedó sin la condición. Ahora hay una sola
función que empareja camino y sombreador, y es la que estas pruebas fijan.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.render.gl_pipeline import GLRenderConfig, GLRenderer
from src.engine.render.shaders import overlay_frag, passthrough_frag, upload_frag


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((64, 64))
    yield


# ── los sombreadores dicen lo que prometen ────────────────────────


def test_passthrough_no_coloca_nada() -> None:
    """Es la premisa del defecto: si esto cambia, el resto mide otra cosa."""
    assert "1.0 - uv.y" not in passthrough_frag
    assert ".bgr" not in passthrough_frag


@pytest.mark.parametrize("swap", [True, False])
def test_upload_voltea_y_deja_el_alfa_opaco(swap: bool) -> None:
    fuente = upload_frag(swap)
    assert "1.0 - uv.y" in fuente
    assert ", 1.0)" in fuente, "la escena necesita el alfa forzado a opaco"


@pytest.mark.parametrize("swap", [True, False])
def test_overlay_voltea_igual_pero_conserva_el_alfa(swap: bool) -> None:
    fuente = overlay_frag(swap)
    assert "1.0 - uv.y" in fuente, "sin volteo el HUD sigue saliendo del revés"
    canales = "bgra" if swap else "rgba"
    assert f".{canales}" in fuente, (
        "el overlay tiene que llevarse los cuatro canales: AUD-344 lo compone "
        "con SRC_ALPHA y un alfa forzado a 1.0 taparía el mundo entero"
    )
    assert ", 1.0)" not in fuente, "se está forzando el alfa a opaco"


# ── la superficie que App manda de verdad toma el camino rápido ───


def test_el_overlay_de_app_califica_para_subida_directa(_video) -> None:
    """Si no calificara, el defecto no se daría y esto sería teatro.

    Se construyen igual que en `App._init_pygame`: la escena sin banderas y el
    overlay con `SRCALPHA`.
    """
    escena = pygame.Surface((32, 32))
    overlay = pygame.Surface((32, 32), pygame.SRCALPHA)
    referencia = GLRenderer._swizzle_de(pygame.Surface((1, 1)))
    if referencia is None:
        pytest.skip("esta plataforma no usa el camino rápido de subida")
    assert GLRenderer._swizzle_de(escena) == referencia
    assert GLRenderer._swizzle_de(overlay) == referencia, (
        "el overlay ya no califica para subida directa; el emparejamiento "
        "sigue siendo obligatorio pero este fichero mide otra cosa"
    )


# ── el emparejamiento camino/sombreador, que es la corrección ─────


class _RendererFalso(GLRenderer):
    """Un renderizador con los programas sustituidos por etiquetas.

    Permite comprobar *qué* se elegiría sin necesitar tarjeta: la decisión es
    lógica pura y no debería exigir un contexto de OpenGL para probarse.
    """

    def __init__(self, directa: bool) -> None:
        super().__init__(GLRenderConfig())
        self._directa = directa
        self._passthrough_prog = "passthrough"      # type: ignore[assignment]
        self._upload_prog = "upload"                # type: ignore[assignment]
        self._overlay_prog = "overlay"              # type: ignore[assignment]

    def _subida_directa(self, surface: pygame.Surface) -> bool:
        return self._directa


@pytest.mark.parametrize(("directa", "esperado_escena", "esperado_overlay"), [
    (True, "upload", "overlay"),
    (False, "passthrough", "passthrough"),
])
def test_el_programa_acompana_al_camino(
    _video, directa: bool, esperado_escena: str, esperado_overlay: str,
) -> None:
    r = _RendererFalso(directa)
    s = pygame.Surface((8, 8))
    assert r._programa_de_subida(s, conserva_alfa=False) == esperado_escena
    assert r._programa_de_subida(s, conserva_alfa=True) == esperado_overlay


def test_el_overlay_nunca_usa_el_programa_que_borra_el_alfa(_video) -> None:
    """El fallo que sustituiría un defecto visible por uno peor."""
    for directa in (True, False):
        r = _RendererFalso(directa)
        elegido = r._programa_de_subida(pygame.Surface((8, 8)), conserva_alfa=True)
        assert elegido != "upload", (
            "el overlay se dibujaría con el sombreador que fuerza el alfa a "
            "1.0: el HUD quedaría del derecho y taparía el escenario"
        )
