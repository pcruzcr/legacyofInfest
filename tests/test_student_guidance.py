"""
Module: test_student_guidance
System: tests
Academic Unit: N/A

La guía que ve el estudiante tiene que decir lo que el motor hace de verdad.

Por qué existe (AUD-057)
------------------------
`StageWizardScene` es el asistente que el proyecto ofrece para aprender a montar
un escenario en Tiled. Contradecía al motor en ocho puntos, y seguirlo al pie de
la letra producía un mapa que **no carga**:

======================================  ==========================================
El asistente decía                      El motor hace
======================================  ==========================================
«Tile size: 32x32 pixels»               ``settings.TILE_SIZE`` es 16
«Crea una capa 'Terrain'»               Exige las 8 de ``REQUIRED_LAYERS``
«Crea una capa de tiles 'Enemies'»      Los enemigos son objetos en ``Objects``
«Crea una capa 'Collectibles'»          No existe tal concepto
«Al menos 1 checkpoint»                 Y con ``checkpoint_id``, o no carga
«Tipos: Walker, Shooter, Flying,        Hay 30 tipos registrados
Charger»
«usa load_stage(tmx_path)»              No existe esa función
«assets/maps/tu_stage.tmx»              La convención es ``<id>/<id>.tmx``
======================================  ==========================================

Una guía equivocada es peor que ninguna: quien no tiene guía lee el código de
`stage0`, que sí funciona; quien la sigue pierde la tarde y concluye que el
motor está roto.

Estas pruebas no revisan la redacción. Comprueban que cada dato **verificable**
que aparece en el asistente siga coincidiendo con el código: los nombres de las
capas, los tipos de objeto, el tamaño de tile y los comandos que manda ejecutar.
La única forma de que vuelva a desincronizarse es que alguien cambie el motor y
esta prueba se lo diga.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def wizard_text(_pygame_init) -> str:
    """Todo el texto que el asistente muestra, en una sola cadena."""
    import pygame
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))

    from src.engine.scenes.stage_wizard_scene import WIZARD_STEPS

    chunks: list[str] = []
    for step in WIZARD_STEPS:
        chunks.append(str(step["title"]))
        chunks.append(str(step["instruction"]))
        chunks.extend(str(d) for d in step["details"])
    return "\n".join(chunks)


class TestTheWizardMatchesTheEngine:
    def test_the_tile_size_it_teaches_is_the_engine_tile_size(
        self, wizard_text: str,
    ) -> None:
        """Decía 32x32 cuando el motor usa 16: el doble de escala."""
        from src.engine.core import settings

        sizes = set(re.findall(r"(\d+)x\1", wizard_text))
        assert sizes, "el asistente ya no menciona ningún tamaño de tile"
        assert sizes == {str(settings.TILE_SIZE)}, (
            f"el asistente enseña tiles de {sizes} y el motor usa "
            f"{settings.TILE_SIZE}"
        )

    def test_it_names_every_required_layer(self, wizard_text: str) -> None:
        """Pedía sólo `Terrain`; faltar una capa impide cargar el mapa."""
        from src.framework.stage.stage_loader import REQUIRED_LAYERS

        missing = [name for name in REQUIRED_LAYERS if name not in wizard_text]
        assert not missing, (
            f"el asistente no menciona capas obligatorias: {missing}. "
            f"Quien lo siga verá «Missing required layer»"
        )

    def test_every_object_type_it_mentions_exists(self, wizard_text: str) -> None:
        """Enseñar un tipo que el motor no conoce es enseñar un enemigo invisible."""
        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader
        from src.framework.stage.tmx_diagnostics import known_object_types

        entity_factory.ensure_registered()
        valid = set(known_object_types(list(StageLoader._entity_registry)))

        # `type=Algo` y `Type: Algo` son las dos formas en que el asistente
        # nombra un tipo concreto.
        mentioned = set(re.findall(r"[Tt]ype[=:]\s*([A-Za-z_]+)", wizard_text))
        mentioned.discard("Class")  # es el nombre del campo en Tiled, no un tipo

        unknown = {m for m in mentioned if m not in valid}
        assert not unknown, f"el asistente enseña tipos que no existen: {unknown}"

    def test_it_mentions_the_property_that_checkpoints_require(
        self, wizard_text: str,
    ) -> None:
        """Un Checkpoint sin `checkpoint_id` lanza FrameworkUsageError.

        El asistente decía «al menos 1 checkpoint» y nada más, así que seguirlo
        llevaba directamente a un escenario que no carga.
        """
        assert "checkpoint_id" in wizard_text

    def test_it_does_not_invent_layers_the_loader_ignores(
        self, wizard_text: str,
    ) -> None:
        """Mandaba crear capas 'Enemies' y 'Collectibles' que nadie lee.

        Es la peor clase de instrucción equivocada: se ejecuta sin error y no
        produce nada, así que el estudiante busca el fallo en su mapa.
        """
        for invented in ("'Enemies'", "'Collectibles'"):
            assert invented not in wizard_text, (
                f"el asistente vuelve a mandar crear la capa {invented}, que el "
                f"cargador no lee"
            )

    def test_the_commands_it_tells_you_to_run_exist(
        self, wizard_text: str,
    ) -> None:
        """Mandaba usar `load_stage(...)`, que nunca existió."""
        scripts = re.findall(r"python (scripts/[\w./]+|main\.py)", wizard_text)
        assert scripts, "el asistente ya no dice cómo validar ni cómo jugar"
        for script in scripts:
            assert (ROOT / script).exists(), (
                f"el asistente manda ejecutar {script}, que no existe"
            )

    def test_it_points_at_a_template_that_exists(self, wizard_text: str) -> None:
        paths = re.findall(r"(student_templates/[\w/]+)", wizard_text)
        assert paths, "el asistente ya no indica de dónde partir"
        for path in paths:
            assert (ROOT / path).exists(), f"ruta inexistente en el asistente: {path}"


class TestTheWrittenGuideMatchesTheEngine:
    """`docs/STAGE_CREATION.md` es la versión larga de lo mismo."""

    @pytest.fixture(scope="class")
    def guide(self) -> str:
        return (ROOT / "docs" / "STAGE_CREATION.md").read_text(encoding="utf-8")

    def test_the_guide_lists_every_required_layer(self, guide: str) -> None:
        from src.framework.stage.stage_loader import REQUIRED_LAYERS

        missing = [name for name in REQUIRED_LAYERS if name not in guide]
        assert not missing, f"la guía no documenta las capas: {missing}"

    def test_the_guide_does_not_document_types_that_vanished(
        self, guide: str, _pygame_init,
    ) -> None:
        """Documentar un tipo eliminado envía al estudiante a un enemigo invisible.

        Se aceptan los dos vocabularios: la capa `Objects` y la capa
        `Collision`, que se procesa aparte y admite `Platform`. La primera
        versión de esta prueba sólo conocía el primero y marcó `Platform` como
        inexistente cuando el cargador sí lo trata — un falso positivo que
        habría empujado a borrar documentación correcta.
        """
        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader
        from src.framework.stage.tmx_diagnostics import (
            COLLISION_OBJECT_TYPES,
            known_object_types,
        )

        entity_factory.ensure_registered()
        valid = set(known_object_types(list(StageLoader._entity_registry)))
        valid.update(COLLISION_OBJECT_TYPES)

        # Los tipos aparecen en la guía como celdas de tabla con acentos
        # graves: | `Walker` | …
        documented = set(re.findall(r"^\| `([A-Z]\w+)`", guide, re.MULTILINE))
        unknown = documented - valid
        assert not unknown, f"la guía documenta tipos inexistentes: {unknown}"

    def test_the_guide_mentions_the_checkpoint_property(self, guide: str) -> None:
        assert "checkpoint_id" in guide


class TestTheGeneratedTypeTable:
    """La tabla de tipos del doc se genera; comprobamos que siga generada."""

    def test_the_reference_table_matches_the_registry(self) -> None:
        """Documentar 8 de 30 tipos deja 21 especies inalcanzables.

        Estaban registradas y funcionaban, pero nadie las iba a escribir en
        Tiled porque la guía no decía que existieran. Una función que existe y
        no se puede descubrir es, desde fuera, una función que no existe.
        """
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "scripts/generate_tmx_reference.py", "--check"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0, (
            f"la tabla de tipos de docs/STAGE_CREATION.md está desfasada.\n"
            f"{result.stderr}"
        )

    def test_every_named_species_appears_in_the_guide(self, _pygame_init) -> None:
        from src.framework.entities import bestiary_registry

        guide = (ROOT / "docs" / "STAGE_CREATION.md").read_text(encoding="utf-8")
        missing = [s for s in bestiary_registry.SPECIES if f"`{s}`" not in guide]
        assert not missing, f"especies registradas y no documentadas: {missing}"

    def test_the_generated_block_is_marked_as_generated(self) -> None:
        """Sin la marca, alguien lo editará a mano y perderá el cambio."""
        guide = (ROOT / "docs" / "STAGE_CREATION.md").read_text(encoding="utf-8")
        assert "BEGIN GENERATED" in guide
        assert "No la edites a mano" in guide


class TestLaGuiaDocumentaLaAtmosferaDeLaFase1:
    """Una propiedad que el motor lee y la guía no menciona no existe.

    El estudiante no tiene forma de descubrir `ambient_light` leyendo el
    código: está en `StageLoader`, a tres archivos de distancia de su
    escenario. La guía es el único sitio donde puede encontrarla, así que
    desincronizarla equivale a borrar la característica.

    Esta prueba compara la guía con las listas reales del motor, no con una
    copia escrita a mano.
    """

    GUIA = pathlib.Path(__file__).resolve().parent.parent / "docs" / "STAGE_CREATION.md"

    def _filas_de_tabla(self) -> list[str]:
        """Sólo las filas de tabla, no la prosa.

        La primera versión de esta prueba buscaba el nombre en cualquier parte
        del archivo. No detectó al mutante que borraba `ambient_light` de la
        tabla, porque la propiedad seguía mencionada de pasada en la
        descripción de la viñeta. Documentar de verdad una propiedad es darle
        una fila con su tipo, su rango y lo que hace; una mención suelta no
        sirve para configurar nada.
        """
        return [linea for linea in self.GUIA.read_text(encoding="utf-8").splitlines()
                if linea.lstrip().startswith("|")]

    @pytest.mark.parametrize(
        "propiedad",
        ["ambient_light", "bloom", "vignette", "climate",
         "ambient_fx", "ambient_fx_rate", "start_hour", "day_length",
         "season"],
    )
    def test_cada_propiedad_de_atmosfera_tiene_su_fila(self, propiedad):
        """La propiedad tiene que ser el **sujeto** de una fila, no una mención.

        Segundo intento. El primero exigía que el nombre apareciera en alguna
        fila de tabla, y tampoco detectó al mutante: `ambient_light` sale
        también en la fila de `vignette` —"conviene subirla al bajar
        `ambient_light`"—, así que la búsqueda acertaba con la fila equivocada.
        Se comprueba la primera columna, que es donde vive el sujeto de la fila.
        """
        filas = [
            f for f in self._filas_de_tabla()
            if f.strip().strip("|").split("|")[0].strip() == f"`{propiedad}`"
        ]
        assert filas, (
            f"el motor lee la propiedad de mapa '{propiedad}' y la guía no le "
            "dedica una fila propia: el estudiante no puede descubrirla"
        )
        # La fila tiene que decir algo, no sólo nombrarla.
        assert len(filas[0].strip().strip("|").split("|")) >= 3, (
            f"la fila de '{propiedad}' no documenta tipo ni comportamiento: {filas[0]}"
        )

    def test_los_tipos_de_particula_coinciden_con_el_motor(self):
        from src.framework.vfx.ambient_particles import AmbientParticleSystem

        texto = self.GUIA.read_text(encoding="utf-8")
        for tipo in AmbientParticleSystem.TIPOS:
            assert tipo in texto, f"falta el tipo de partícula '{tipo}' en la guía"

    def test_los_colores_de_foco_coinciden_con_el_motor(self):
        from src.framework.stage.stage_loader import StageLoader

        texto = self.GUIA.read_text(encoding="utf-8")
        for nombre in StageLoader.LIGHT_COLORS:
            assert nombre in texto, f"falta el color de foco '{nombre}' en la guía"

    def test_las_estaciones_coinciden_con_el_motor(self):
        from src.framework.stage.seasons import ESTACIONES

        texto = self.GUIA.read_text(encoding="utf-8")
        for nombre in ESTACIONES:
            assert nombre in texto, f"falta la estación '{nombre}' en la guía"

    def test_los_momentos_del_dia_coinciden_con_el_motor(self):
        from src.framework.stage.day_night import RelojDeMundo

        texto = self.GUIA.read_text(encoding="utf-8")
        for momento in RelojDeMundo.MOMENTOS:
            assert momento in texto, f"falta el momento '{momento}' en la guía"

    def test_los_climas_coinciden_con_el_motor(self):
        from src.framework.vfx.weather_system import WeatherSystem

        texto = self.GUIA.read_text(encoding="utf-8")
        for clima in WeatherSystem.CLIMATE_PARAMS:
            assert clima in texto, f"falta el clima '{clima}' en la guía"

    def test_las_propiedades_del_objeto_light_estan_documentadas(self):
        texto = self.GUIA.read_text(encoding="utf-8")
        for prop in ("radius", "intensity", "flicker",
                     "flicker_speed", "flicker_amount"):
            assert f"`{prop}`" in texto, (
                f"la propiedad '{prop}' del objeto Light no está en la guía"
            )
