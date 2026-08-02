"""
Module: test_tmx_validator
System: tests
Academic Unit: N/A

`scripts/validate_tmx.py` es lo que el estudiante ejecuta antes de jugar.
Estas pruebas comprueban que **rechace lo que el motor rechaza**.

Por qué existe (AUD-058)
------------------------
El validador y el cargador no se hablaban, y el validador era el optimista:

* Declaraba ``REQUIRED_LAYERS = ["Terrain"]``; el cargador exige ocho. Un mapa
  con sólo Terrain pasaba la validación y el juego lo rechazaba al abrirlo.
* Buscaba el PlayerSpawn por `type` **o por `name`**. El cargador lee sólo
  `type`, así que un objeto *llamado* PlayerSpawn y sin tipo pasaba, y luego
  fallaba con «No PlayerSpawn found».
* No miraba los tipos de objeto en absoluto: la errata que hacía desaparecer un
  enemigo no la detectaba nadie.
* Avisaba —no fallaba— cuando la longitud del CSV de una capa no coincidía con
  el tamaño del mapa. Ese aviso llevaba tiempo desatendido en
  `boss_venado.tmx`, donde cinco capas tenían entre 613 y 815 tiles en lugar de
  800; pytmx acepta el CSV torcido y desplaza toda la capa.

Un validador que aprueba lo que el motor rechaza es peor que no tener
validador: enseña a no fiarse de él, y a partir de ahí nadie lo ejecuta.

La prueba clave de este módulo es la última: coge un mapa que el validador
aprueba y comprueba que el cargador **también** lo acepta. Es la afirmación que
el estudiante necesita que sea cierta.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STAGE0 = ROOT / "assets" / "maps" / "stage0" / "stage0.tmx"


@pytest.fixture
def map_factory():
    """Crea variantes de stage0 junto al original y las borra al terminar.

    Tienen que vivir en la misma carpeta: el TMX referencia sus tilesets por
    ruta relativa, y una copia en /tmp no encontraría las imágenes.
    """
    created: list[Path] = []

    def _make(transform) -> Path:
        text = STAGE0.read_text(encoding="utf-8")
        target = STAGE0.parent / f"_test_{len(created)}.tmx"
        target.write_text(transform(text), encoding="utf-8")
        created.append(target)
        return target

    yield _make

    for path in created:
        if path.exists():
            path.unlink()


def _validate(path: Path) -> tuple[bool, str]:
    """Ejecuta el validador y devuelve (pasa, texto de los problemas)."""
    import importlib

    module = importlib.import_module("scripts.validate_tmx")
    importlib.reload(module)
    ok = module.validate_tmx(path)
    return ok, "\n".join(module._errors + module._warnings)


class TestItRejectsWhatTheLoaderRejects:
    def test_a_healthy_map_passes(self) -> None:
        """Punto de partida: si stage0 no pasara, todo lo demás daría igual."""
        ok, problems = _validate(STAGE0)
        assert ok, f"stage0 no pasa su propio validador:\n{problems}"

    def test_a_missing_required_layer_is_an_error(self, map_factory) -> None:
        """Declaraba exigir sólo `Terrain`; el cargador exige ocho capas."""
        broken = map_factory(
            lambda t: t.replace('name="BG_Far"', 'name="Fondo_Lejano"', 1),
        )
        ok, problems = _validate(broken)
        assert not ok
        assert "BG_Far" in problems

    def test_an_unknown_object_type_is_an_error(self, map_factory) -> None:
        broken = map_factory(lambda t: t.replace('type="Walker"', 'type="Waker"', 1))
        ok, problems = _validate(broken)
        assert not ok
        assert "Waker" in problems

    def test_it_suggests_the_intended_type(self, map_factory) -> None:
        """Detectar la errata es la mitad; decir cuál era es la otra mitad."""
        broken = map_factory(lambda t: t.replace('type="Walker"', 'type="walker"', 1))
        _, problems = _validate(broken)
        assert "Walker" in problems
        assert "uisiste decir" in problems

    def test_an_object_with_no_type_is_an_error(self, map_factory) -> None:
        """El cargador lo ignoraría entero, que es el fallo silencioso original."""
        broken = map_factory(lambda t: t.replace('type="Walker"', "", 1))
        ok, problems = _validate(broken)
        assert not ok
        assert "sin type" in problems

    def test_a_player_spawn_named_but_not_typed_does_not_count(
        self, map_factory,
    ) -> None:
        """El validador lo aceptaba por `name`; el cargador sólo lee `type`.

        Es el caso más engañoso de todos: el validador decía que el mapa estaba
        bien y el juego decía «No PlayerSpawn found» sobre el mismo archivo.
        """
        # El objeto ya se llama PlayerSpawn en stage0, así que basta con
        # quitarle el `type`: queda exactamente el caso engañoso — nombre
        # correcto, tipo ausente.
        broken = map_factory(
            lambda t: t.replace(' type="PlayerSpawn"', "", 1),
        )
        ok, problems = _validate(broken)
        assert not ok
        assert "PlayerSpawn" in problems

    def test_two_player_spawns_are_an_error(self, map_factory) -> None:
        """El cargador lanza «More than one PlayerSpawn»."""
        def _duplicate(text: str) -> str:
            # Tiled escribe la etiqueta auto-cerrada cuando el objeto no
            # tiene propiedades y con cuerpo cuando las tiene. Buscar sólo la
            # primera forma hacía que esta prueba se rompiera al regenerar el
            # mapa, sin que el validador hubiera cambiado nada.
            match = re.search(
                r'<object[^>]*type="PlayerSpawn"[^>]*(?:/>|>.*?</object>)',
                text, re.S,
            )
            assert match, "stage0 ya no declara el PlayerSpawn como se esperaba"
            return text.replace(match.group(0), match.group(0) * 2, 1)

        ok, problems = _validate(map_factory(_duplicate))
        assert not ok
        assert "PlayerSpawn" in problems

    def test_a_checkpoint_without_its_id_is_an_error(self, map_factory) -> None:
        """`_handle_checkpoint` lanza FrameworkUsageError sin `checkpoint_id`."""
        broken = map_factory(
            lambda t: t.replace('name="checkpoint_id"', 'name="id_del_checkpoint"'),
        )
        ok, problems = _validate(broken)
        assert not ok
        assert "checkpoint_id" in problems

    def test_a_layer_with_the_wrong_tile_count_is_an_error(
        self, map_factory,
    ) -> None:
        """Era un aviso, y por eso cinco capas de boss_venado llevaban tiempo rotas.

        pytmx acepta el CSV torcido y construye una matriz de la altura
        equivocada: la capa entera queda desplazada, sin ningún mensaje.
        """
        def _truncate(text: str) -> str:
            root = ET.fromstring(text)
            data = root.find("layer/data")
            raw = (data.text or "").strip()
            ids = [x.strip() for x in raw.replace("\n", "").split(",") if x.strip()]
            return text.replace(raw, ",".join(ids[:-40]), 1)

        ok, problems = _validate(map_factory(_truncate))
        assert not ok
        assert "desplazan" in problems or "tiles" in problems


class TestTheValidatorAgreesWithTheLoader:
    """La afirmación que el estudiante necesita que sea verdad."""

    def test_what_the_validator_approves_the_loader_loads(self, _pygame_init) -> None:
        """Lo que el validador aprueba **sin reservas**, el cargador lo carga.

        AUD-106 — la excepción, y por qué está declarada
        ------------------------------------------------
        Dos entregas registran sus jefes dentro de un método de su escena, no
        a nivel de módulo. Al jugar funciona —la escena se construye antes de
        cargar el mapa—, pero abrir el TMX suelto no ejecuta ese método, y el
        cargador no sabe construir el jefe.

        El validador ya lo dice con todas las letras: «*el previsualizador y
        las herramientas que abren el mapa suelto no podrán construir esos
        objetos*». Esta prueba es una de esas herramientas, así que respeta el
        aviso en lugar de contradecirlo.

        Lo que **no** se hace es degradar el aviso a silencio: el estudiante
        tiene que saberlo, y la línea de abajo falla en cuanto un mapa sin ese
        aviso deje de cargar.
        """
        import pygame
        pygame.display.set_mode((320, 224))

        from src.framework.stage.stage_loader import StageLoader

        for tmx in sorted((ROOT / "assets" / "maps").rglob("*.tmx")):
            ok, problems = _validate(tmx)
            if not ok:
                continue  # el validador ya lo rechazó; no promete nada
            if "registro dentro de una función" in problems:
                continue  # el propio validador avisó de que esto no cargaría
            StageLoader.clear_tmx_cache()
            StageLoader.load(tmx)  # no debe lanzar

    def test_the_validator_uses_the_loaders_layer_list(self) -> None:
        """Duplicar la lista es cómo llegó a decir «sólo Terrain».

        Se comprueba el valor en tiempo de ejecución, no el texto del archivo:
        la primera versión de esta prueba buscaba la cadena
        ``REQUIRED_LAYERS = ["Terrain"]`` en el fuente y fallaba porque aparece
        en el docstring que explica el error. Una prueba que lee prosa acaba
        prohibiendo hablar del problema.
        """
        import importlib

        from src.framework.stage.stage_loader import REQUIRED_LAYERS

        module = importlib.import_module("scripts.validate_tmx")
        assert module._loader_required_layers() == list(REQUIRED_LAYERS)

    def test_the_validator_uses_the_real_entity_registry(self, _pygame_init) -> None:
        """Una lista de tipos copiada a mano se queda vieja al añadir uno.

        Se compara contra el registro vivo: si alguien añade una especie al
        bestiario, el validador tiene que aceptarla sin que nadie lo edite.
        """
        import importlib

        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader

        entity_factory.ensure_registered()
        module = importlib.import_module("scripts.validate_tmx")
        valid = set(module._valid_object_types())

        for registered in StageLoader._entity_registry:
            assert registered in valid, (
                f"el validador rechazaría '{registered}', que el cargador acepta"
            )


class TestItReadsBothTiledDialects:
    """Tiled 1.9 renombró el atributo `type` de los objetos a `class`."""

    def test_a_class_attribute_is_understood(self, map_factory) -> None:
        """Un mapa guardado con Tiled reciente no puede parecer vacío de tipos."""
        converted = map_factory(lambda t: t.replace('type="Walker"', 'class="Walker"'))
        ok, problems = _validate(converted)
        assert ok, f"un TMX con `class=` debería validar igual:\n{problems}"


class TestElTilesetDeclaradoEsElTilesetReal:
    """AUD-115 — un mapa puede dibujar las baldosas equivocadas y validar.

    `generate_stage0_tmx.py` y `generate_stage_mecanicas.py` declaraban el
    tileset como `tilecount="64" columns="8"` con una imagen de 128 × 128 px.
    `tileset_stage0.png` mide **1024 × 1024** y tiene 4096 baldosas en 64
    columnas. Con la cabecera equivocada, el índice de baldosa que el mapa
    guarda apunta a otra casilla de la hoja: los dos escenarios pintaban las
    tres primeras baldosas —casi negras— en vez del corredor de piedra.

    Ni `grade_stage.py` ni `validate_tmx.py` lo vieron. Los dos comprueban que
    el fichero del tileset **exista**; ninguno comprueba que la hoja declarada
    tenga el tamaño de la hoja real. Un mapa ilegible sacaba 130/130.

    Lo cazó, de rebote, una prueba de legibilidad nocturna que mide píxeles en
    pantalla. Ésta lo comprueba de frente, y para todos los mapas del curso:
    también para los de los estudiantes, donde el mismo error saldría como
    «mi nivel se ve negro» sin más pista.
    """

    @staticmethod
    def _mapas():
        import pathlib
        raiz = pathlib.Path(__file__).resolve().parent.parent
        return sorted((raiz / "assets" / "maps").glob("*/*.tmx"))

    def test_hay_mapas_que_revisar(self) -> None:
        """Sin esto, la prueba de abajo pasaría con una carpeta vacía."""
        assert len(self._mapas()) >= 10

    def test_cada_hoja_incrustada_declara_su_tamano_real(self) -> None:
        import xml.etree.ElementTree as ET

        from PIL import Image

        desajustes: list[str] = []
        for tmx in self._mapas():
            raiz = ET.parse(tmx).getroot()
            for tileset in raiz.findall("tileset"):
                imagen = tileset.find("image")
                if imagen is None:      # tileset externo `.tsx`: es válido
                    continue
                ruta = (tmx.parent / imagen.get("source", "")).resolve()
                if not ruta.exists():   # lo cubre el validador de recursos
                    continue
                with Image.open(ruta) as _imagen:
                    real = _imagen.size
                declarado = (int(imagen.get("width", 0)), int(imagen.get("height", 0)))
                if declarado != real:
                    desajustes.append(
                        f"{tmx.name}: declara {declarado[0]}×{declarado[1]}, "
                        f"la imagen mide {real[0]}×{real[1]}"
                    )
                columnas = int(tileset.get("columns", 0))
                esperadas = real[0] // int(tileset.get("tilewidth", 16))
                if columnas != esperadas:
                    desajustes.append(
                        f"{tmx.name}: declara {columnas} columnas, la hoja tiene "
                        f"{esperadas}"
                    )
        assert not desajustes, (
            "estos mapas dibujarían baldosas distintas de las que guardaron:\n  "
            + "\n  ".join(desajustes)
        )
