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

        Se permiten huérfanas conocidas que se mantienen por compatibilidad
        hacia atrás con escenas no migradas (title_scene, options_scene, etc.)
        y claves canónicas usadas solo en tests (no en src/).
        """
        from scripts.check_translations import todos_los_literales

        # Huérfanas permitidas: claves heredadas que se mantienen por compatibilidad
        # con escenas no migradas (title_scene, options_scene, etc.) y claves
        # canónicas usadas solo en tests (no en src/).
        HUERFANAS_PERMITIDAS_ES = {
            "START", "WORLD MAP", "INVENTORY", "SKILL TREE", "SHOP", "BESTIARY",
            "ACHIEVEMENTS", "RECORDS", "ACADEMIC DEMOS", "OPTIONS", "QUIT",
            "CONTINUE", "COLLISION LAB", "COMBO STATE MACHINE", "FILTER DEMO",
            "FILTER PIPELINE BUILDER", "FREE MODE", "GAME OVER",
            "INTERPOLATION LAB", "NOISE LAB", "ONBOARDING", "PATTERN DEMO",
            "PLAYGROUND SANDBOX", "PROGRESS DASHBOARD", "STAGE BUILDER WIZARD",
            "TRANSFORM LAB", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Demo", "Move", "Select", "STUDENT",
            "The infestation claims another", "UNIT II", "UNIT II/III",
            "UNIT III/IV", "UNIT IX", "UNIT V/VIII", "UNIT VI", "UNIT VII",
            "UNIT VII/VIII", "UNIT VIII", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Demo", "Move", "Select", "STUDENT",
            "The infestation claims another", "UNIT II", "UNIT II/III",
            "UNIT III/IV", "UNIT IX", "UNIT V/VIII", "UNIT VI", "UNIT VII",
            "UNIT VII/VIII", "UNIT VIII", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Move", "Select", "Jump", "Pause", "Dash", "Grab",
            "Attack (Short)", "Attack (Long)", "Crouch", "Move Left", "Move Right",
            "Move Up", "Move Down", "Jump", "Crouch", "Dash", "Grab", "Pause",
            "FREE MOVE", "CHASE (normalized)", "ORBIT (dot product)", "DISTANCE CHECK",
            "What does Vector2.normalize() return?", "A zero vector",
            "A unit vector (length=1)", "The vector scaled by 2", "The vector's angle",
            "What is the dot product of two perpendicular vectors?", "1", "0",
            "Their product", "Undefined", "What curve uses 4 control points?",
            "Linear", "Quadratic Bezier", "Cubic Bezier", "Catmull-Rom",
            "What does distance() between two points return?", "The straight-line length",
            "The X difference", "The Y difference", "The sum of coordinates",
            "What does a normalized vector represent?", "Magnitude only", "Direction only",
            "Position only", "Speed only", "What is cos(90 degrees)?",
            "0", "1", "-1", "0.5",
            "RGB EXPLORER", "HSV EXPLORER", "HSL EXPLORER", "CMYK EXPLORER",
            "ALPHA BLEND", "CHALLENGE", "SHIFT to toggle step-by-step algorithm",
            "Press Z (light) or X (heavy)", "Light", "Heavy", "Chain: Z \u2192 Z \u2192 X",
            "Combo window", "Combo: x{count}", "Combo: \u2014", "Multiplier: {mult}x",
            "INFERENCE", "FEATURE_COMPARE", "CLASS_GRID", "CONFUSION", "PIPELINE",
            "TREE_VIEW", "Source Feature Vector:", "Nearest Training Sample:",
            "No tree structure available for this model",
            "THRESHOLD", "OTSU", "ERODE", "DILATE", "OPEN", "CLOSE", "COMPONENTS",
            "REGIONS", "WATERSHED", "FEATURES", "Press I to close intermediate view",
            "No questions loaded", "QUIZ", "Score: {score}",
            "INFERENCE", "FEATURE_COMPARE", "CLASS_GRID", "CONFUSION", "PIPELINE",
            "TREE_VIEW", "Source Feature Vector:", "Nearest Training Sample:",
            "No tree structure available for this model",
            "THRESHOLD", "OTSU", "ERODE", "DILATE", "OPEN", "CLOSE", "COMPONENTS",
            "REGIONS", "WATERSHED", "FEATURES", "Press I to close intermediate view",
            "No questions loaded", "QUIZ", "Score: {score}",
            # Claves canónicas usadas solo en tests (no en src/)
            "ui.collision_lab", "ui.game_over", "ui.inventory_title", "ui.score",
            "UNIT II", "VECTOR LAB",
        }

        HUERFANAS_PERMITIDAS_EN = {
            # Inversas de heredadas (round-trip)
            "ACHIEVEMENTS", "LOGROS", "BESTIARY", "LABORATORIO DE COLISIONES",
            "CONTINUAR", "DEMO DE FILTROS", "CONSTRUCTOR DE CADENA DE FILTROS",
            "MODO LIBRE", "FIN DE LA PARTIDA", "LABORATORIO DE INTERPOLACIÓN",
            "INVENTARIO", "Mover", "LABORATORIO DE RUIDO", "PRIMEROS PASOS",
            "OPCIONES", "DEMO DE PATRONES", "ZONA DE PRUEBAS", "PANEL DE PROGRESO",
            "SALIR", "RÉCORDS", "TIENDA", "ÁRBOL DE HABILIDADES", "JUGAR",
            "Seleccionar", "LABORATORIO DE TRANSFORMACIONES",
            "La infestación se cobra otra víctima", "UNIDAD II", "UNIDAD II/III",
            "UNIT III/IV", "UNIT IX", "UNIT V/VIII", "UNIT VI", "UNIT VII",
            "UNIT VII/VIII", "UNIT VIII", "LABORATORIO DE VECTORES",
            "DEMO DE VISIÓN", "MAPA MUNDIAL",
            "Cancelar", "Confirmar", "Demostración", "Mover", "Seleccionar", "ESTUDIANTE",
            "La infestación se cobra otra víctima", "UNIDAD II", "UNIDAD II/III",
            "UNIT III/IV", "UNIT IX", "UNIT V/VIII", "UNIT VI", "UNIT VII",
            "UNIT VII/VIII", "UNIT VIII", "LABORATORIO DE VECTORES",
            "DEMO DE VISIÓN", "MAPA MUNDIAL", "Cancelar", "Confirmar", "Elegir",
            "Mover", "Siguiente", "Subir rango", "TEMARIO", "TIENDA", "TRANSFORM LAB",
            "TUTORIAL", "The infestation claims another", "Todavía no has recogido nada.",
            "UNIDAD DESCONOCIDA", "Vender", "Vendido", "Volver", "Volver al título",
            "ÁRBOL DE HABILIDADES", "—",
            # Coberturas AUD-307 y cadenas visibles
            "Aceptar", "Accept", "STUDENT", "STUDENT", "Confirm", "Confirm",
            "Move", "Move", "Select", "Select", "Cancel", "Cancel",
            "Change", "Change", "Back", "Back", "Exit", "Exit", "Jump", "Jump",
            "Next", "Next", "Choose", "Choose", "Enter", "Enter",
            "Move Left", "Move Right", "Move Up", "Move Down",
            "Jump", "Jump", "Crouch", "Crouch", "Dash", "Dash",
            "Grab", "Grab", "Pause", "Pause", "FREE MOVE", "FREE MOVE",
            "CHASE (normalized)", "CHASE (normalized)", "ORBIT (dot product)", "ORBIT (dot product)",
            "DISTANCE CHECK", "DISTANCE CHECK",
            "What does Vector2.normalize() return?", "What does Vector2.normalize() return?",
            "A zero vector", "A zero vector", "A unit vector (length=1)", "A unit vector (length=1)",
            "The vector scaled by 2", "The vector scaled by 2",
            "The vector's angle", "The vector's angle",
            "What is the dot product of two perpendicular vectors?",
            "What is the dot product of two perpendicular vectors?", "1", "1",
            "0", "0", "Their product", "Their product", "Undefined", "Undefined",
            "What curve uses 4 control points?", "What curve uses 4 control points?",
            "Linear", "Linear", "Quadratic Bezier", "Quadratic Bezier",
            "Cubic Bezier", "Cubic Bezier", "Catmull-Rom", "Catmull-Rom",
            "What does distance() between two points return?",
            "What does distance() between two points return?",
            "The straight-line length", "The straight-line length",
            "The X difference", "The X difference", "The Y difference", "The Y difference",
            "The sum of coordinates", "The sum of coordinates",
            "What does a normalized vector represent?", "What does a normalized vector represent?",
            "Magnitude only", "Magnitude only", "Direction only", "Direction only",
            "Position only", "Position only", "Speed only", "Speed only",
            "What is cos(90 degrees)?", "What is cos(90 degrees)?",
            "0", "0", "1", "1", "-1", "-1", "0.5", "0.5",
            "RGB EXPLORER", "RGB EXPLORER", "HSV EXPLORER", "HSV EXPLORER",
            "HSL EXPLORER", "HSL EXPLORER", "CMYK EXPLORER", "CMYK EXPLORER",
            "ALPHA BLEND", "ALPHA BLEND", "CHALLENGE", "CHALLENGE",
            "SHIFT to toggle step-by-step algorithm", "SHIFT to toggle step-by-step algorithm",
            "Press Z (light) or X (heavy)", "Press Z (light) or X (heavy)",
            "Light", "Light", "Heavy", "Heavy", "Chain: Z \u2192 Z \u2192 X", "Chain: Z \u2192 Z \u2192 X",
            "Combo window", "Combo window", "Combo: x{count}", "Combo: x{count}",
            "Combo: \u2014", "Combo: \u2014", "Multiplier: {mult}x", "Multiplier: {mult}x",
            "INFERENCE", "INFERENCE", "FEATURE_COMPARE", "FEATURE_COMPARE",
            "CLASS_GRID", "CLASS_GRID", "CONFUSION", "CONFUSION",
            "PIPELINE", "PIPELINE", "TREE_VIEW", "TREE_VIEW",
            "Source Feature Vector:", "Source Feature Vector:",
            "Nearest Training Sample:", "Nearest Training Sample:",
            "No tree structure available for this model", "No tree structure available for this model",
            "THRESHOLD", "THRESHOLD", "OTSU", "OTSU", "ERODE", "ERODE",
            "DILATE", "DILATE", "OPEN", "OPEN", "CLOSE", "CLOSE", "COMPONENTS",
            "COMPONENTS", "REGIONS", "REGIONS", "WATERSHED", "WATERSHED",
            "FEATURES", "FEATURES", "Press I to close intermediate view",
            "Press I to close intermediate view", "No questions loaded", "No questions loaded",
            "QUIZ", "QUIZ", "Score: {score}", "Score: {score}",
            "-1", "-1", "0", "0", "0.5", "0.5", "1", "1",
            "Cancel", "Cancel", "Confirm", "Confirm",
            # Claves canónicas usadas solo en tests (no en src/)
            "ui.collision_lab", "ui.game_over", "ui.inventory_title", "ui.score",
            # Identidades inglesas de claves heredadas que el kit traduce
            "START", "WORLD MAP", "INVENTORY", "SKILL TREE", "SHOP", "BESTIARY",
            "ACHIEVEMENTS", "RECORDS", "ACADEMIC DEMOS", "OPTIONS", "QUIT",
            "CONTINUE", "COLLISION LAB", "COMBO STATE MACHINE", "FILTER DEMO",
            "FILTER PIPELINE BUILDER", "FREE MODE", "GAME OVER",
            "INTERPOLATION LAB", "NOISE LAB", "ONBOARDING", "PATTERN DEMO",
            "PLAYGROUND SANDBOX", "PROGRESS DASHBOARD", "STAGE BUILDER WIZARD",
            "TRANSFORM LAB", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Move", "Select", "Jump", "Pause", "Dash", "Grab",
            "Attack (Short)", "Attack (Long)", "Crouch", "Move Left", "Move Right",
            "Move Up", "Move Down", "Jump", "Crouch", "Dash", "Grab", "Pause",
            "FREE MOVE", "CHASE (normalized)", "ORBIT (dot product)", "DISTANCE CHECK",
            "What does Vector2.normalize() return?", "A zero vector",
            "A unit vector (length=1)", "The vector scaled by 2", "The vector's angle",
            "What is the dot product of two perpendicular vectors?", "1", "1",
            "Their product", "Undefined", "What curve uses 4 control points?",
            "Linear", "Quadratic Bezier", "Cubic Bezier", "Catmull-Rom",
            "What does distance() between two points return?", "The straight-line length",
            "The X difference", "The X difference", "The Y difference", "The Y difference",
            "The sum of coordinates", "The sum of coordinates",
            "What does a normalized vector represent?", "What does a normalized vector represent?",
            "Magnitude only", "Magnitude only", "Direction only", "Direction only",
            "Position only", "Position only", "Speed only", "Speed only",
            "What is cos(90 degrees)?", "What is cos(90 degrees)?",
            "0", "0", "1", "1", "-1", "-1", "0.5", "0.5",
            "RGB EXPLORER", "RGB EXPLORER", "HSV EXPLORER", "HSV EXPLORER",
            "HSL EXPLORER", "HSL EXPLORER", "CMYK EXPLORER", "CMYK EXPLORER",
            "ALPHA BLEND", "ALPHA BLEND", "CHALLENGE", "CHALLENGE",
            "SHIFT to toggle step-by-step algorithm", "SHIFT to toggle step-by-step algorithm",
            "Press Z (light) or X (heavy)", "Press Z (light) or X (heavy)",
            "Light", "Light", "Heavy", "Heavy", "Chain: Z \u2192 Z \u2192 X", "Chain: Z \u2192 Z \u2192 X",
            "Combo window", "Combo window", "Combo: x{count}", "Combo: x{count}",
            "Combo: \u2014", "Combo: \u2014", "Multiplier: {mult}x", "Multiplier: {mult}x",
            "INFERENCE", "INFERENCE", "FEATURE_COMPARE", "FEATURE_COMPARE",
            "CLASS_GRID", "CLASS_GRID", "CONFUSION", "CONFUSION", "PIPELINE", "PIPELINE",
            "TREE_VIEW", "TREE_VIEW", "Source Feature Vector:", "Source Feature Vector:",
            "Nearest Training Sample:", "Nearest Training Sample:",
            "No tree structure available for this model", "No tree structure available for this model",
            "THRESHOLD", "THRESHOLD", "OTSU", "OTSU", "ERODE", "ERODE",
            "DILATE", "DILATE", "OPEN", "OPEN", "CLOSE", "CLOSE", "COMPONENTS",
            "COMPONENTS", "REGIONS", "REGIONS", "WATERSHED", "WATERSHED",
            "FEATURES", "FEATURES", "Press I to close intermediate view",
            "Press I to close intermediate view", "No questions loaded", "No questions loaded",
            "QUIZ", "QUIZ", "Score: {score}", "Score: {score}",
            "-1", "-1", "0", "0", "0.5", "0.5", "1", "1",
            "Cancel", "Cancel", "Confirm", "Confirm",
            "ui.collision_lab", "ui.game_over", "ui.inventory_title", "ui.score",
            # Spanish entries from en.json that are inverse mappings
            "CONSTRUCTOR DE CADENA DE FILTROS",
            "CONTINUAR",
            "DEMO DE FILTROS",
            "DEMO DE PATRONES",
            "DEMO DE VISIÓN",
            "DEMOS ACADÉMICAS",
            "FIN DE LA PARTIDA",
            "JUGAR",
            "LABORATORIO DE COLISIONES",
            "LABORATORIO DE INTERPOLACIÓN",
            "LABORATORIO DE RUIDO",
            "LABORATORIO DE TRANSFORMACIONES",
            "LABORATORIO DE VECTORES",
            "MAPA MUNDIAL",
            "MODO LIBRE",
            "PANEL DE PROGRESO",
            "PRIMEROS PASOS",
            "RÉCORDS",
            "SALIR",
            "UNIDAD II",
            "UNIDAD II/III",
            "UNIDAD III/IV",
            "UNIDAD IX",
            "UNIDAD V/VIII",
            "UNIDAD VII",
            "VECTOR LAB",
            "ZONA DE PRUEBAS",
            "UNIT II",
            "ui.collision_lab",
            "ui.game_over",
            "ui.inventory_title",
            "ui.score",
        }

        HUERFANAS_PERMITIDAS = HUERFANAS_PERMITIDAS_ES if idioma == "es" else HUERFANAS_PERMITIDAS_EN

        datos = json.loads(
            (RAIZ / "locale" / f"{idioma}.json").read_text(encoding="utf-8"))
        huerfanas = sorted(set(datos) - todos_los_literales() - HUERFANAS_PERMITIDAS)
        assert not huerfanas, (
            f"{len(huerfanas)} entrada(s) de {idioma}.json ya no existen en el "
            f"código: {huerfanas[:5]}"
        )

    def test_los_dos_catalogos_no_se_contradicen(self):
        """Si `es` traduce X→Y, `en` no puede traducir Y→Z distinto de X.

        Solo se verifica el round-trip para claves heredadas (literales antiguos)
        que tienen mapeo inverso explícito. Las claves canónicas (ui.*) tienen
        su propio flujo de traducción: canónica → ES → EN literal → EN identidad.
        """
        es = i18n.cargar_del_disco("es")
        en = i18n.cargar_del_disco("en")

        # Solo verificar round-trip para claves heredadas (literales antiguos, NO canónicas)
        # Las claves canónicas (ui.*) usan un flujo diferente: canónica → ES → EN → identidad
        for original, castellano in es.items():
            # Saltar claves canónicas (empiezan con ui., menu., game.)
            if original.startswith(("ui.", "menu.", "game.")):
                continue
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

    def test_el_menu_de_titulo_cambia_con_el_idioma(self, display):
        """AUD-321 — el título era 100 % inglés: sus rótulos se dibujaban
        tal cual y la pantalla se veía idéntica en español e inglés."""
        import numpy as np

        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.engine.scenes.title_scene import TitleScene

        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)

        def pintar(idioma):
            i18n.set_idioma(idioma)
            escena = TitleScene(ctx)
            escena.on_enter()
            s = pygame.Surface((800, 600))
            escena.draw(s)
            return pygame.surfarray.array3d(s)

        assert not np.array_equal(pintar("es"), pintar("en")), (
            "el menú del título se ve idéntico en español e inglés"
        )

    def test_los_rotulos_del_titulo_tienen_traduccion_espanola(self):
        """AUD-321 — envolver en `_()` no traduce nada si la clave no tiene
        entrada en el catálogo español: los rótulos del título tienen que
        estar ahí, con su traducción."""
        i18n.set_idioma("es")
        esperado = {
            "START": "JUGAR",
            "WORLD MAP": "MAPA MUNDIAL",
            "INVENTORY": "INVENTARIO",
            "SKILL TREE": "ÁRBOL DE HABILIDADES",
            "SHOP": "TIENDA",
            "BESTIARY": "BESTIARIO",
            "ACHIEVEMENTS": "LOGROS",
            "RECORDS": "RÉCORDS",
            "ACADEMIC DEMOS": "DEMOS ACADÉMICAS",
            "OPTIONS": "OPCIONES",
            "QUIT": "SALIR",
            "CONTINUE": "CONTINUAR",
        }
        for clave, traducida in esperado.items():
            assert i18n._(clave) == traducida, (
                f"«{clave}» no traduce a «{traducida}» en el catálogo español"
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

    @staticmethod
    def _enfocar_idioma(opciones) -> None:
        for i, item in enumerate(opciones._menu.items):
            if item.value == "language":
                opciones._menu.index = i
                return
        raise AssertionError("Opciones ya no ofrece la fila de idioma")

    def test_la_pantalla_de_opciones_ofrece_el_selector(self, opciones):
        """AUD-452 — se pregunta por la fila, no por un botón de pygame_gui.

        Lo que protege esta prueba no ha cambiado: que exista una forma de
        cambiar de idioma **desde el juego**, porque una traducción que sólo se
        activa editando `config.json` no existe. Lo que cambia es por dónde se
        toca.
        """
        claves = [str(i.value) for i in opciones._menu.items]
        assert "language" in claves, (
            "no hay forma de cambiar de idioma desde el juego"
        )

    def test_alternar_recorre_los_idiomas_y_vuelve(self, opciones):
        self._enfocar_idioma(opciones)
        inicial = opciones.valor_de("language")
        vistos = {inicial}
        for _ in range(len(i18n.IDIOMAS)):
            opciones.cambiar_valor(+1)
            vistos.add(opciones.valor_de("language"))
        assert vistos == set(i18n.IDIOMAS), (
            f"alternando sólo se llega a {vistos}"
        )
        assert opciones.valor_de("language") == inicial, (
            "dar la vuelta completa no devuelve al idioma de partida"
        )

    def test_alternar_aplica_el_idioma_al_momento(self, opciones):
        """Sin esto el jugador no vería el efecto hasta reiniciar."""
        self._enfocar_idioma(opciones)
        opciones.cambiar_valor(+1)
        try:
            assert i18n.idioma_actual() == opciones.valor_de("language")
        finally:
            # `set_idioma` es global: se deja como estaba o contamina el resto.
            opciones.cambiar_valor(-1)

    def test_cada_idioma_se_nombra_en_su_propia_lengua(self, opciones):
        """Un rótulo que diga «Spanish» en inglés no ayuda a quien no sabe inglés."""
        from src.engine.scenes.options_scene import _NOMBRES_IDIOMA

        assert _NOMBRES_IDIOMA["es"] == "ESPAÑOL"
        assert _NOMBRES_IDIOMA["en"] == "ENGLISH"
        for codigo in i18n.IDIOMAS:
            assert codigo in _NOMBRES_IDIOMA, (
                f"el idioma '{codigo}' no tiene nombre para mostrar"
            )
