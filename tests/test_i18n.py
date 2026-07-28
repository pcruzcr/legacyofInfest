"""
Module: test_i18n
System: tests
Academic Unit: N/A

Traducción de la interfaz, español por defecto.

F3.1 — la auditoría midió 348 cadenas fijas en las escenas y 0 módulos con
soporte de idioma, para un curso que se imparte en español. La interfaz mezcla
`"INVENTARIO"` con `"COLLISION LAB"`.

Dos cosas se prueban aquí, y la segunda es la que importa:

* que el catálogo traduzca y que un idioma desconocido no rompa nada;
* que la traducción **llegue a las pantallas sin que cada escena la pida**. Se
  traduce dentro del kit de interfaz a propósito: si hubiera que envolver cada
  literal en cada escena, la primera que escribiera un estudiante saldría sin
  traducir y nadie se enteraría.
"""
from __future__ import annotations

import json
from pathlib import Path

import pygame
import pytest

from src.engine.core import i18n

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _restaurar_idioma():
    """Cada prueba deja el idioma como lo encontró."""
    anterior = i18n.idioma_actual()
    yield
    i18n.set_idioma(anterior)


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


class TestElCatalogoTraduce:
    def test_el_espanol_es_el_idioma_por_defecto(self):
        assert i18n.IDIOMA_POR_DEFECTO == "es", (
            "el curso se imparte en español; el valor por defecto tiene que serlo"
        )

    def test_traduce_al_ingles(self):
        i18n.set_idioma("en")
        assert i18n._("INVENTARIO") == "INVENTORY"
        assert i18n._("Volver") == "Back"

    def test_traduce_al_espanol_los_literales_ingleses(self):
        """El código mezcla los dos idiomas; el catálogo español lo normaliza."""
        i18n.set_idioma("es")
        assert i18n._("COLLISION LAB") == "LABORATORIO DE COLISIONES"
        assert i18n._("GAME OVER") == "FIN DE LA PARTIDA"

    def test_lo_que_ya_esta_en_el_idioma_pasa_tal_cual(self):
        i18n.set_idioma("es")
        assert i18n._("INVENTARIO") == "INVENTARIO"

    def test_una_cadena_sin_traducir_se_devuelve_entera(self):
        """Nunca un identificador ni un hueco: el original es legible."""
        i18n.set_idioma("en")
        raro = "esta cadena no está en ningún catálogo"
        assert i18n._(raro) == raro

    def test_las_cadenas_sin_traducir_se_anotan(self):
        i18n.set_idioma("en")
        i18n._("una cadena inventada para esta prueba")
        assert "una cadena inventada para esta prueba" in i18n.faltantes()

    def test_un_idioma_desconocido_cae_al_por_defecto_sin_lanzar(self):
        assert i18n.set_idioma("klingon") == i18n.IDIOMA_POR_DEFECTO
        assert i18n.set_idioma("") == i18n.IDIOMA_POR_DEFECTO
        assert i18n.set_idioma(None) == i18n.IDIOMA_POR_DEFECTO

    def test_cambiar_de_idioma_ida_y_vuelta_es_estable(self):
        i18n.set_idioma("en")
        en = i18n._("INVENTARIO")
        i18n.set_idioma("es")
        i18n.set_idioma("en")
        assert i18n._("INVENTARIO") == en


class TestLosCatalogosEstanSanos:
    @pytest.mark.parametrize("idioma", i18n.IDIOMAS)
    def test_el_archivo_existe_y_es_json_valido(self, idioma):
        ruta = RAIZ / "locale" / f"{idioma}.json"
        assert ruta.exists(), f"falta el catálogo {ruta}"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert isinstance(datos, dict)

    @pytest.mark.parametrize("idioma", i18n.IDIOMAS)
    def test_ninguna_entrada_esta_vacia(self, idioma):
        datos = json.loads(
            (RAIZ / "locale" / f"{idioma}.json").read_text(encoding="utf-8"))
        vacias = [k for k, v in datos.items()
                  if not str(k).strip() or not str(v).strip()]
        assert not vacias, f"entradas vacías en {idioma}.json: {vacias}"

    @pytest.mark.parametrize("idioma", i18n.IDIOMAS)
    def test_no_hay_entradas_huerfanas(self, idioma):
        """Una traducción de algo que ya no existe es catálogo podrido.

        Es el síntoma de que alguien renombró una cadena y el catálogo se
        quedó atrás. El juego sigue funcionando y muestra esa pantalla sin
        traducir; nadie se entera hasta que un estudiante pregunta.
        """
        from scripts.check_translations import todos_los_literales

        datos = json.loads(
            (RAIZ / "locale" / f"{idioma}.json").read_text(encoding="utf-8"))
        huerfanas = sorted(set(datos) - todos_los_literales())
        assert not huerfanas, (
            f"{len(huerfanas)} entrada(s) de {idioma}.json ya no existen en el "
            f"código: {huerfanas[:5]}"
        )

    def test_los_dos_catalogos_no_se_contradicen(self):
        """Si `es` traduce X→Y, `en` no puede traducir Y→Z distinto de X."""
        es = i18n.cargar_del_disco("es")
        en = i18n.cargar_del_disco("en")
        for original, castellano in es.items():
            vuelta = en.get(castellano)
            if vuelta is not None:
                assert vuelta == original, (
                    f"ida y vuelta inconsistente: es[{original!r}]={castellano!r} "
                    f"pero en[{castellano!r}]={vuelta!r}"
                )


class TestLaTraduccionLlegaALasPantallas:
    """La prueba de cableado: sin esto, todo lo anterior sería teoría."""

    def _titulo_pintado(self, idioma: str, titulo: str) -> pygame.Surface:
        from src.engine.ui.widgets import draw_screen

        i18n.set_idioma(idioma)
        lienzo = pygame.Surface((800, 600))
        draw_screen(lienzo, titulo, "")
        return lienzo

    def test_el_kit_traduce_el_titulo_sin_que_la_escena_lo_pida(self, display):
        import numpy as np

        a = self._titulo_pintado("es", "COLLISION LAB")
        b = self._titulo_pintado("en", "COLLISION LAB")
        assert not np.array_equal(
            pygame.surfarray.array3d(a), pygame.surfarray.array3d(b)), (
            "la pantalla se ve igual en los dos idiomas: el kit no traduce"
        )

    def test_el_kit_traduce_los_atajos_de_teclado(self, display):
        import numpy as np

        from src.engine.ui.widgets import draw_key_hints

        def pintar(idioma):
            i18n.set_idioma(idioma)
            s = pygame.Surface((800, 600))
            s.fill((0, 0, 0))
            draw_key_hints(s, [("Esc", "Volver")])
            return pygame.surfarray.array3d(s)

        assert not np.array_equal(pintar("es"), pintar("en"))

    def test_una_escena_real_cambia_con_el_idioma(self, display):
        """Se carga una pantalla del juego, no un lienzo de laboratorio."""
        import numpy as np

        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.engine.scenes.inventory_scene import InventoryScene

        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)

        def pintar(idioma):
            i18n.set_idioma(idioma)
            escena = InventoryScene(ctx)
            escena.on_enter()
            s = pygame.Surface((800, 600))
            escena.draw(s)
            return pygame.surfarray.array3d(s)

        assert not np.array_equal(pintar("es"), pintar("en")), (
            "la pantalla de inventario se ve idéntica en español e inglés"
        )


class TestElIdiomaSePersiste:
    def test_el_ajuste_existe_y_su_valor_por_defecto_es_espanol(self):
        from src.engine.core.user_settings import UserSettings

        assert UserSettings().language == "es"

    def test_un_idioma_invalido_en_el_config_no_rompe_el_arranque(self):
        from src.engine.core.user_settings import UserSettings

        ajustes = UserSettings(language="klingon")
        assert ajustes.language == i18n.IDIOMA_POR_DEFECTO

    def test_se_guarda_y_se_recupera(self, tmp_path):
        from src.engine.core.user_settings import UserSettings

        destino = tmp_path / "config.json"
        ajustes = UserSettings(language="en")
        ajustes.save(destino)
        assert UserSettings.load(destino).language == "en"

    def test_la_aplicacion_aplica_el_idioma_al_arrancar(self):
        """Si se aplicara después, las escenas ya creadas se quedarían atrás."""
        import inspect

        from src.engine.core import app

        fuente = inspect.getsource(app.App)
        assert "set_idioma" in fuente, (
            "App no aplica el idioma guardado: el ajuste no tendría efecto "
            "hasta recrear cada pantalla"
        )


class TestElJugadorPuedeCambiarDeIdioma:
    """Una traducción que sólo se activa editando config.json no existe."""

    @pytest.fixture
    def opciones(self, display):
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.engine.scenes.options_scene import OptionsScene

        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        escena = OptionsScene(ctx)
        escena.on_enter()
        return escena

    def test_la_pantalla_de_opciones_ofrece_el_selector(self, opciones):
        assert opciones._btn_language is not None, (
            "no hay forma de cambiar de idioma desde el juego"
        )

    def test_alternar_recorre_los_idiomas_y_vuelve(self, opciones):
        inicial = opciones._idioma_actual
        vistos = {inicial}
        for _ in range(len(i18n.IDIOMAS)):
            opciones._toggle_language()
            vistos.add(opciones._idioma_actual)
        assert vistos == set(i18n.IDIOMAS), (
            f"alternando sólo se llega a {vistos}"
        )
        assert opciones._idioma_actual == inicial, (
            "dar la vuelta completa no devuelve al idioma de partida"
        )

    def test_alternar_aplica_el_idioma_al_momento(self, opciones):
        """Sin esto el jugador no vería el efecto hasta reiniciar."""
        opciones._toggle_language()
        assert i18n.idioma_actual() == opciones._idioma_actual

    def test_cada_idioma_se_nombra_en_su_propia_lengua(self, opciones):
        """Un botón que diga «Spanish» en inglés no ayuda a quien no sabe inglés."""
        assert opciones._NOMBRES_IDIOMA["es"] == "ESPAÑOL"
        assert opciones._NOMBRES_IDIOMA["en"] == "ENGLISH"
        for codigo in i18n.IDIOMAS:
            assert codigo in opciones._NOMBRES_IDIOMA, (
                f"el idioma '{codigo}' no tiene nombre para mostrar"
            )
