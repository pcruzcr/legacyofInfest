"""
Module: test_tmx_diagnostics
System: tests
Academic Unit: N/A

Pruebas del diagnóstico de mapas TMX (AUD-055).

Estas pruebas verifican el **contenido del mensaje**, no sólo que se lance una
excepción. La diferencia importa más de lo normal aquí: quien lee este error es
un estudiante que no escribió el engine, y `FrameworkUsageError("bad object")`
es tan inútil como el silencio que vino a sustituir. Lo que hay que garantizar
es que el mensaje diga *qué* objeto, *dónde* está y *qué* debió escribirse.

Por eso hay aserciones sobre la sugerencia y sobre las coordenadas. Son las dos
cosas que convierten el error en una corrección de treinta segundos en Tiled.
"""
from __future__ import annotations

import pytest

from src.framework.stage.tmx_diagnostics import (
    BUILTIN_OBJECT_TYPES,
    TmxObjectProblem,
    TmxReport,
    known_object_types,
    suggest_types,
)

# Un subconjunto representativo del registro real, suficiente para razonar
# sobre las sugerencias sin depender de pygame ni del bestiario completo.
KNOWN = [
    "Walker", "Flying", "Shooter", "Charger", "Archer", "Brute",
    "FlyingBird", "FlyingBoa", "WalkerGarza", "PlayerSpawn", "Checkpoint",
]


class TestSuggestions:
    def test_a_lowercase_type_suggests_the_correct_casing(self) -> None:
        """El error más común: el nombre bien, la mayúscula mal."""
        assert suggest_types("walker", KNOWN) == ("Walker",)

    def test_case_only_matches_are_offered_alone(self) -> None:
        """Cuando hay coincidencia exacta salvo mayúsculas, es *la* respuesta.

        Se prueba con «flyingbird» y no con «shooter» a propósito. Con
        «shooter» la búsqueda por parecido acierta igual, así que la prueba no
        distinguiría un atajo por mayúsculas de no tenerlo — se detectó con una
        mutación que eliminaba el atajo y seguía pasando. Con «flyingbird» la
        búsqueda por parecido devuelve además «Flying», y ofrecer dos opciones
        cuando una es exacta salvo capitalización añade una duda que no existe.
        """
        assert suggest_types("flyingbird", KNOWN) == ("FlyingBird",)
        assert suggest_types("shooter", KNOWN) == ("Shooter",)

    def test_a_typo_suggests_near_matches(self) -> None:
        suggestions = suggest_types("FlyingBrid", KNOWN)
        assert "FlyingBird" in suggestions

    def test_suggestions_are_capped(self) -> None:
        """Más de tres opciones deja de ser una pista y pasa a ser una lista."""
        assert len(suggest_types("Walke", KNOWN)) <= 3

    def test_nonsense_suggests_nothing_rather_than_anything(self) -> None:
        """Una sugerencia inventada es peor que ninguna: manda a un callejón."""
        assert suggest_types("zzzzzzzzzz", KNOWN) == ()

    def test_an_empty_type_has_no_suggestions(self) -> None:
        assert suggest_types("", KNOWN) == ()


class TestKnownTypes:
    def test_builtin_types_are_included(self) -> None:
        """Un `Checkpoint` mal escrito debe sugerir `Checkpoint`.

        Si sólo se ofrecieran los tipos de entidad, los tipos estructurales
        —los que todo mapa necesita— serían justamente los que no reciben
        ayuda.
        """
        combined = known_object_types(["Walker"])
        for builtin in BUILTIN_OBJECT_TYPES:
            assert builtin in combined

    def test_the_list_is_sorted_and_deduplicated(self) -> None:
        combined = known_object_types(["Walker", "Walker", "PlayerSpawn"])
        assert combined == sorted(set(combined))


class TestProblemDescription:
    def test_the_description_locates_the_object(self) -> None:
        """Sin coordenadas, «tienes un objeto mal» obliga a revisar el mapa entero."""
        problem = TmxObjectProblem(
            object_id=7, object_name="Walker_01", object_type="walker",
            x=288.0, y=512.0, suggestions=("Walker",),
        )
        text = problem.describe()
        assert "7" in text
        assert "Walker_01" in text
        assert "288" in text and "512" in text
        assert "Walker" in text

    def test_a_single_suggestion_is_phrased_as_one(self) -> None:
        problem = TmxObjectProblem(
            object_id=1, object_name="", object_type="walker",
            x=0.0, y=0.0, suggestions=("Walker",),
        )
        assert "¿quisiste decir «Walker»?" in problem.describe()

    def test_several_suggestions_are_listed(self) -> None:
        problem = TmxObjectProblem(
            object_id=1, object_name="", object_type="Flyin",
            x=0.0, y=0.0, suggestions=("Flying", "FlyingBird"),
        )
        text = problem.describe()
        assert "Flying" in text and "FlyingBird" in text

    def test_an_untyped_object_says_so_instead_of_guessing(self) -> None:
        """«sin tipo» y «tipo desconocido» se arreglan de forma distinta."""
        problem = TmxObjectProblem(
            object_id=3, object_name="caja", object_type="",
            x=10.0, y=20.0, reason="objeto sin type",
        )
        text = problem.describe()
        assert "sin type" in text
        assert "quisiste decir" not in text


class TestReport:
    def test_an_empty_report_is_ok(self) -> None:
        assert TmxReport().ok is True

    def test_every_problem_appears_in_the_report(self) -> None:
        """Se informan todos juntos: encontrar seis erratas de una en una son
        seis ejecuciones del juego."""
        report = TmxReport(tmx_path="mapa.tmx")
        for i in range(6):
            report.add(TmxObjectProblem(
                object_id=i, object_name=f"obj{i}", object_type="mal",
                x=float(i), y=0.0,
            ))
        assert report.ok is False
        text = report.format(KNOWN)
        for i in range(6):
            assert f"obj{i}" in text

    def test_the_report_names_the_file(self) -> None:
        report = TmxReport(tmx_path="assets/maps/mi_stage/mi_stage.tmx")
        report.add(TmxObjectProblem(1, "x", "mal", 0.0, 0.0))
        assert "mi_stage.tmx" in report.format()

    def test_the_report_lists_valid_types_when_asked(self) -> None:
        report = TmxReport()
        report.add(TmxObjectProblem(1, "x", "mal", 0.0, 0.0))
        text = report.format(KNOWN)
        assert "Tipos válidos" in text
        for known in KNOWN:
            assert known in text

    def test_the_report_mentions_the_field_to_edit_in_tiled(self) -> None:
        """El mensaje tiene que decir dónde se arregla, no sólo qué está mal.

        Tiled renombró el campo «Type» a «Class» en versiones recientes, así
        que se nombran los dos: buscar un campo que en tu versión se llama
        distinto es otra media hora perdida.
        """
        report = TmxReport()
        report.add(TmxObjectProblem(1, "x", "mal", 0.0, 0.0))
        text = report.format()
        assert "Type" in text
        assert "Class" in text


class TestLoaderIntegration:
    """Extremo a extremo sobre un TMX real con los errores típicos."""

    @pytest.fixture
    def broken_map(self, tmp_path, _pygame_init):
        import shutil
        from pathlib import Path

        import pygame
        pygame.display.set_mode((320, 224))

        source = Path("assets/maps/stage0/stage0.tmx")
        # El TMX referencia sus tilesets por ruta relativa, así que la copia
        # tiene que vivir junto al original o pytmx no encuentra las imágenes.
        target = source.parent / "_test_broken.tmx"
        text = source.read_text(encoding="utf-8")
        text = text.replace('type="Walker"', 'type="walker"', 1)
        text = text.replace('type="Flying"', 'type="FlyingBrid"', 1)
        target.write_text(text, encoding="utf-8")
        yield target
        shutil.os.remove(target)

    def test_a_misspelled_type_stops_the_load_with_a_useful_message(
        self, broken_map,
    ) -> None:
        from src.framework import FrameworkUsageError
        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader

        entity_factory.ensure_registered()
        StageLoader.clear_tmx_cache()

        with pytest.raises(FrameworkUsageError) as excinfo:
            StageLoader.load(broken_map)

        message = str(excinfo.value)
        # Los dos errores, no sólo el primero.
        assert "walker" in message
        assert "FlyingBrid" in message
        # Y las dos correcciones.
        assert "«Walker»" in message
        assert "FlyingBird" in message

    def test_a_correct_map_still_loads(self, _pygame_init) -> None:
        """La red de seguridad no puede rechazar los mapas que ya funcionan."""
        from pathlib import Path

        import pygame
        pygame.display.set_mode((320, 224))

        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader

        entity_factory.ensure_registered()
        StageLoader.clear_tmx_cache()
        stage = StageLoader.load(Path("assets/maps/stage0/stage0.tmx"))
        assert stage.entity_list, "stage0 debería tener entidades"


class TestRegistrationIsSelfHealing:
    """El registro de entidades no puede depender de que alguien lo llame antes.

    AUD-056. `ensure_registered()` sólo lo invocaba `App.__init__`, así que
    cargar un mapa desde un script, una herramienta o una prueba daba un
    escenario incompleto. Y su guarda era `if _registered: return`, un
    indicador que seguía diciendo «hecho» después de que alguien vaciara el
    registro.
    """

    def test_loading_a_map_registers_the_bestiary_by_itself(
        self, _pygame_init,
    ) -> None:
        from pathlib import Path

        import pygame
        pygame.display.set_mode((320, 224))

        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader

        # Estado hostil: alguien vació el registro y el indicador miente.
        StageLoader._entity_registry.clear()
        entity_factory._registered = True

        StageLoader.clear_tmx_cache()
        stage = StageLoader.load(Path("assets/maps/stage0/stage0.tmx"))

        kinds = {type(e).__name__ for e in stage.entity_list}
        assert len(kinds) >= 8, (
            f"el escenario se cargó incompleto tras vaciar el registro: {sorted(kinds)}"
        )

    def test_a_partial_registry_is_completed_not_accepted(
        self, _pygame_init,
    ) -> None:
        """«No vacío» no es «completo».

        Una guarda que se conforme con que el registro tenga algo deja pasar
        justo el caso que hay que detectar: tres tipos dados de alta a mano.
        """
        from src.framework.entities import entity_factory
        from src.framework.entities.enemy_walker import EnemyWalker
        from src.framework.stage.stage_loader import StageLoader

        StageLoader._entity_registry.clear()
        StageLoader.register_entity("Walker", EnemyWalker)
        entity_factory._registered = True

        entity_factory.ensure_registered()

        for expected in ("Charger", "Archer", "Brute", "Caster", "Assassin"):
            assert expected in StageLoader._entity_registry


class TestTheErrorReachesTheScreen:
    """Un diagnóstico que sólo llega al log no llega a nadie.

    `App.run` capturaba la excepción, la escribía en el log y volvía al título.
    Desde el asiento del estudiante: un parpadeo y el menú principal. El
    mensaje existía y no lo veía la única persona que podía actuar sobre él.
    """

    def test_the_scene_renders_the_diagnostic_text(self, _pygame_init) -> None:
        """El texto del informe tiene que llegar a los píxeles.

        La primera versión de esta prueba comprobaba que la pantalla no fuera
        de un color uniforme, y pasaba aunque no se dibujara ni una línea del
        mensaje: `draw_screen` ya pinta título y separador. Lo descubrió una
        mutación que borraba el `blit` del cuerpo.

        Comparar un mensaje corto con uno largo mide lo que interesa —cuánto
        del informe acaba en pantalla— y no depende de a qué altura empiece el
        texto ni de qué colores use el tema.
        """
        import pygame

        from src.engine.scenes.stage_error_scene import StageErrorScene

        pygame.display.set_mode((800, 600))

        def _ink(message: str) -> int:
            scene = StageErrorScene(_minimal_context(), message)
            surface = pygame.Surface((800, 600))
            scene.on_enter()
            scene.update(1 / 60)
            scene.draw(surface)
            from src.engine.ui.theme import Theme
            return sum(
                1
                for x in range(0, 800, 3)
                for y in range(0, 600, 3)
                if surface.get_at((x, y))[:3] != Theme.BG
            )

        short = _ink("x")
        long = _ink("\n".join(f"objeto id={i}: tipo desconocido" for i in range(12)))
        assert long > short * 1.5, (
            f"el cuerpo del informe no se está dibujando "
            f"(corto={short}, largo={long})"
        )

    def test_it_accepts_an_exception_object_directly(self, _pygame_init) -> None:
        """Quien llama tiene una excepción en la mano, no una cadena."""
        from src.engine.scenes.stage_error_scene import StageErrorScene
        from src.framework import FrameworkUsageError

        scene = StageErrorScene(
            _minimal_context(), FrameworkUsageError("línea uno\nlínea dos"),
        )
        assert scene._lines == ["línea uno", "línea dos"]

    def test_the_retry_key_is_hidden_when_there_is_nothing_to_retry(
        self, _pygame_init,
    ) -> None:
        """Anunciar una tecla que no hace nada es peor que no anunciarla."""
        import pygame

        from src.engine.scenes.stage_error_scene import StageErrorScene

        scene = StageErrorScene(_minimal_context(), "error", retry=None)
        # Pulsar R no debe explotar aunque no haya reintento.
        scene.process_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)])
        assert scene._retry is None

    def test_retry_runs_the_callback(self, _pygame_init) -> None:
        import pygame

        from src.engine.scenes.stage_error_scene import StageErrorScene

        calls: list[int] = []
        scene = StageErrorScene(
            _minimal_context(), "error", retry=lambda: calls.append(1),
        )
        scene.process_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)])
        assert calls == [1]

    def test_long_reports_scroll_instead_of_being_cut(self, _pygame_init) -> None:
        """Un mapa con veinte erratas produce un informe más alto que la pantalla."""
        import pygame

        from src.engine.scenes.stage_error_scene import StageErrorScene

        pygame.display.set_mode((800, 600))
        scene = StageErrorScene(
            _minimal_context(), "\n".join(f"línea {i}" for i in range(200)),
        )
        scene.draw(pygame.Surface((800, 600)))  # fija _visible_lines
        scene.process_events(
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)],
        )
        assert scene._scroll == 1

        for _ in range(500):
            scene.process_events(
                [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)],
            )
        assert scene._scroll <= 200, "el desplazamiento se salió del informe"


def _minimal_context():
    """GameContext suficiente para construir y dibujar una escena."""
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager

    bus = EventBus()
    context = GameContext(
        input_manager=InputManager(),
        audio_manager=AudioManager(),
        scene_manager=None,
        event_bus=bus,
    )
    context.scene_manager = SceneManager(context)
    return context
