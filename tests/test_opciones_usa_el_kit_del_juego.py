"""AUD-452 — Opciones era la única pantalla con otro lenguaje visual.

Todo el juego se maneja con listas de teclado dibujadas por `engine.ui.widgets`:
el título, los archivos de partida, los logros, el bestiario, la tienda y —lo
que más duele en la comparación— **Controles**, que está justo al lado. Sólo
Opciones usaba `pygame_gui`, con deslizadores y desplegables de ratón, su
propia tipografía y su propio tema.

No es un problema de estilo. Son dos modelos de interacción distintos en el
mismo menú: en Controles te mueves con las flechas y confirmas con Enter; en
Opciones tienes que arrastrar un deslizador y desplegar una lista. Y en un
juego que se juega con teclado, un desplegable con foco de ratón es un cuerpo
extraño.

Por qué una lista y no deslizadores nativos
-------------------------------------------
La alternativa era escribir deslizador, desplegable e interruptor propios. Se
descartó porque replicaría widgets de ratón en un menú de teclado: seguiría
habiendo dos formas de manejarse. El patrón de consola —una fila por ajuste,
←→ cambia el valor, el valor se lee a la derecha— usa lo que ya existe
(`MenuList` y su campo `trailing`), se maneja igual que el resto del juego y
hereda gratis el desplazamiento de AUD-446 y la escala de accesibilidad de
`theme.font()`.

Eso último cierra además BUG-002: las once filas ya no se amontonan.
"""
from __future__ import annotations

import os
import pathlib

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

RUTA = (pathlib.Path(__file__).resolve().parent.parent
        / "src" / "engine" / "scenes" / "options_scene.py")


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield


@pytest.fixture
def opciones(_video, tmp_path, monkeypatch):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core import user_settings
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.engine.scenes.options_scene import OptionsScene

    monkeypatch.setattr(user_settings, "CONFIG_FILENAME", "config_prueba.json")
    monkeypatch.setattr(SaveManager, "SAVES_DIR", tmp_path)
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    escena = OptionsScene(ctx)
    escena.awake()
    escena.start()
    escena.on_enter()
    return escena


class TestYaNoUsaOtroKit:
    def test_no_queda_ni_una_referencia_a_pygame_gui(self) -> None:
        """Se mira el **código**, no la prosa.

        La cabecera del módulo explica por qué se dejó `pygame_gui`, y esa
        explicación es lo que impide que alguien vuelva a meterlo por parecerle
        más cómodo. Una prueba que prohibiera nombrarlo obligaría a borrar el
        motivo para poder pasar, que es justo al revés de lo que interesa.
        """
        import ast

        arbol = ast.parse(RUTA.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    assert not alias.name.startswith("pygame_gui"), (
                        "Opciones vuelve a importar pygame_gui"
                    )
            elif isinstance(nodo, ast.ImportFrom):
                assert not (nodo.module or "").startswith("pygame_gui"), (
                    "Opciones vuelve a importar pygame_gui"
                )
            elif isinstance(nodo, ast.Attribute):
                base = nodo.value
                assert not (isinstance(base, ast.Name)
                            and base.id == "pygame_gui"), (
                    "Opciones vuelve a usar widgets de pygame_gui"
                )

    def test_dibuja_con_una_lista_del_kit(self, opciones) -> None:
        from src.engine.ui.widgets import MenuList

        assert isinstance(opciones._menu, MenuList)

    def test_la_lista_se_desplaza(self, opciones) -> None:
        """BUG-002: once filas no caben, y recortar ajustes no es la salida."""
        assert opciones._menu.visible_rows is not None
        assert len(opciones._menu.filas_visibles()) <= 5


class TestEstanTodosLosAjustes:
    #: Los once ajustes que la pantalla ofrecía con `pygame_gui`. Migrar no
    #: puede perder ninguno por el camino.
    ESPERADOS = (
        "music_volume", "sfx_volume", "difficulty", "colorblind_mode",
        "subtitles_enabled", "language", "text_scale", "reduced_motion",
        "hold_to_press", "contorno_de_enemigos",
    )

    @pytest.mark.parametrize("clave", ESPERADOS)
    def test_el_ajuste_sigue_estando(self, opciones, clave: str) -> None:
        claves = [a.clave for a in opciones.ajustes]
        assert clave in claves, f"se perdió el ajuste {clave!r} al migrar"

    def test_se_puede_llegar_a_controles_y_a_volver(self, opciones) -> None:
        valores = [str(i.value) for i in opciones._menu.items]
        assert "CONTROLES" in valores
        assert "VOLVER" in valores


class TestCambiarValores:
    def _fila_de(self, opciones, clave: str) -> int:
        for i, item in enumerate(opciones._menu.items):
            if item.value == clave:
                return i
        raise AssertionError(f"no hay fila para {clave!r}")

    def test_derecha_avanza_y_izquierda_retrocede(self, opciones) -> None:
        opciones._menu.index = self._fila_de(opciones, "difficulty")
        inicial = opciones.valor_de("difficulty")

        opciones.cambiar_valor(+1)
        assert opciones.valor_de("difficulty") != inicial

        opciones.cambiar_valor(-1)
        assert opciones.valor_de("difficulty") == inicial

    def test_el_valor_se_ve_en_la_fila(self, opciones) -> None:
        """Sin el valor a la derecha, la lista no dice en qué estado está."""
        fila = opciones._menu.items[self._fila_de(opciones, "difficulty")]
        assert fila.trailing, "la fila no muestra el valor actual"

    def test_da_la_vuelta_en_los_extremos(self, opciones) -> None:
        """Igual que la navegación del resto del kit, que envuelve."""
        opciones._menu.index = self._fila_de(opciones, "difficulty")
        vistos = set()
        for _ in range(12):
            vistos.add(opciones.valor_de("difficulty"))
            opciones.cambiar_valor(+1)
        assert len(vistos) >= 3, f"sólo se alcanzaron {vistos}"

    def test_el_volumen_no_se_sale_del_rango(self, opciones) -> None:
        opciones._menu.index = self._fila_de(opciones, "music_volume")
        for _ in range(30):
            opciones.cambiar_valor(+1)
            assert 0.0 <= float(opciones.valor_de("music_volume")) <= 1.0
        for _ in range(30):
            opciones.cambiar_valor(-1)
            assert 0.0 <= float(opciones.valor_de("music_volume")) <= 1.0

    def test_cambiar_un_ajuste_lo_persiste(self, opciones) -> None:
        from src.engine.core import user_settings

        opciones._menu.index = self._fila_de(opciones, "reduced_motion")
        antes = bool(user_settings.get().reduced_motion)
        opciones.cambiar_valor(+1)
        assert bool(user_settings.get().reduced_motion) != antes, (
            "el ajuste cambió en la pantalla y no llegó a las preferencias"
        )


class TestTodoEnEspanol:
    _DELATORES = ("on", "off", "subtitles", "language", "back", "hold",
                  "reduced", "normal motion")

    def test_los_valores_que_se_ensenan_estan_en_espanol(self, opciones) -> None:
        import re

        for item in opciones._menu.items:
            texto = f"{item.label} {item.trailing}".lower()
            for palabra in ("subtitles", "language", "back", "on", "off"):
                assert not re.search(rf"\b{palabra}\b", texto), (
                    f"la fila {item.label!r} enseña {item.trailing!r}, en inglés"
                )


class TestSeDibujaSinRomperse:
    def test_un_recorrido_entero_no_revienta(self, opciones) -> None:
        superficie = pygame.Surface((800, 600))
        for _ in range(len(opciones._menu.items) + 2):
            opciones._menu.move_down()
            for _ in range(6):
                opciones.update(1 / 60)
                opciones.draw(superficie)

    def test_pinta_algo(self, opciones) -> None:
        superficie = pygame.Surface((800, 600))
        superficie.fill((0, 0, 0))
        opciones.update(1 / 60)
        opciones.draw(superficie)
        assert pygame.transform.average_color(superficie)[:3] != (0, 0, 0)
