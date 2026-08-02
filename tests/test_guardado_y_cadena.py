"""
El guardado y la cadena de los quince niveles — AUD-156.

Dos preguntas: ¿se puede guardar y volver en todos los niveles, y están todos
encadenados en orden? Las dos se respondieron ejecutándolas, no leyendo.

Lo que se encontró
-------------------
1. **Cargar una partida devolvía al jugador al principio del nivel, en los
   quince.** `on_enter` aplicaba el checkpoint guardado y treinta y ocho
   líneas más abajo, en el mismo método, hacía
   `self._checkpoint_position = None`. Lo puesto se borraba solo. Morir después
   tampoco devolvía al checkpoint, por lo mismo.

2. **Dos escenarios no se podían marcar como completados.** El juego tenía dos
   identidades por nivel —el `STAGE_ID` de la clase y el `stage_id` del TMX— y
   usaba una para guardar y otra para el mapa del mundo. `lobby_datacenter`
   dejó en su mapa el `stage_id` de la plantilla (`stage_template`) y
   `stage2_1_oficinas` no declaraba `STAGE_ID` en su clase. Con la progresión
   en cadena, un nodo que no se marca bloquea todo lo que viene detrás.

Lo que estas pruebas defienden
-------------------------------
* Que guardar y volver funcione **en cada uno de los quince**, no sólo en el
  primero: es exactamente el fallo que se acaba de arreglar.
* Que cada nivel se pueda terminar, por puerta o por jefe.
* Que la cadena llegue de stage 0 a los créditos sin saltarse ni repetir.
* Que las dos identidades no vuelvan a divergir.
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


@pytest.fixture(scope="module")
def escenarios(_video):
    from src.engine.core.stage_registry import discover_stages
    from src.framework.entities import entity_factory

    entity_factory.ensure_registered()
    etapas = discover_stages()
    assert etapas, "no se descubrió ningún escenario"
    return etapas


def _contexto():
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager

    ctx = GameContext(
        input_manager=InputManager(),
        audio_manager=AudioManager(),
        scene_manager=None,
        event_bus=EventBus(),
        clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


@pytest.fixture
def contexto(_video):
    return _contexto()


def _ids(etapas) -> list[str]:
    return [getattr(c, "STAGE_ID", "") or c.__name__ for c in etapas]


def _indices(etapas):
    return list(enumerate(etapas))


def pytest_generate_tests(metafunc):
    """Un caso por escenario, con su nombre en el informe.

    Parametrizar aquí y no con una lista fija es lo que hace que un escenario
    nuevo entre solo en estas pruebas. Una lista escrita a mano se queda corta
    el día que alguien entrega el suyo, que es justo cuando hace falta.
    """
    if "indice_escenario" not in metafunc.fixturenames:
        return
    import os

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    from src.engine.core.stage_registry import discover_stages
    from src.framework.entities import entity_factory

    entity_factory.ensure_registered()
    etapas = discover_stages()
    metafunc.parametrize(
        "indice_escenario", range(len(etapas)),
        ids=[getattr(c, "STAGE_ID", "") or c.__name__ for c in etapas],
    )


class TestGuardarYVolverEnCadaNivel:
    """El fallo estaba en `StageScene`, así que afectaba a los quince a la vez.

    Se prueban todos igualmente: la mitad son entregas de estudiantes que
    sobreescriben `on_enter`, y una de ellas podría volver a borrar el
    checkpoint sin que nadie se enterara.
    """

    def test_cargar_devuelve_al_checkpoint_y_no_al_principio(
            self, contexto, escenarios, indice_escenario) -> None:
        from src.engine.core.inventory import get_inventory
        from src.engine.core.save_data import SaveData

        get_inventory()._items.clear()
        cls = escenarios[indice_escenario]
        contexto.scene_manager.set_stage_queue(escenarios)
        escena = cls(contexto)
        clave = getattr(cls, "STAGE_ID", "") or cls.__name__

        contexto.pending_load = SaveData(
            slot_id=1, stage_id=clave, stage_index=indice_escenario,
            checkpoint_x=777.0, checkpoint_y=333.0,
            health=2.5, max_health=5.0,
        )
        escena.awake()
        escena.start()
        escena.on_enter()
        try:
            assert escena._checkpoint_position is not None, (
                f"«{clave}» ignoró el checkpoint guardado: el jugador "
                f"reaparece al principio del nivel"
            )
            assert escena._player.current_health == pytest.approx(2.5), (
                f"«{clave}» no restauró la salud guardada"
            )
            assert contexto.pending_load is None, (
                "la partida pendiente no se consumió: se aplicaría otra vez "
                "en el siguiente nivel que coincida"
            )
        finally:
            escena.on_exit()

    def test_una_partida_de_otro_nivel_no_se_aplica(
            self, contexto, escenarios) -> None:
        """Si se aplicara, el jugador aparecería en las coordenadas de otro
        mapa: dentro de una pared, o en el vacío."""
        from src.engine.core.save_data import SaveData

        escena = escenarios[0](contexto)
        contexto.pending_load = SaveData(
            slot_id=1, stage_id="un_nivel_que_no_es_este", stage_index=0,
            checkpoint_x=777.0, checkpoint_y=333.0, health=1.0, max_health=5.0,
        )
        escena.awake()
        escena.start()
        escena.on_enter()
        try:
            assert escena._checkpoint_position is None
            assert contexto.pending_load is not None, (
                "se consumió una partida que no era de este nivel"
            )
        finally:
            escena.on_exit()
            contexto.pending_load = None


class TestCadaNivelSePuedeTerminar:
    def test_tiene_salida_o_jefe(self, contexto, escenarios,
                                 indice_escenario) -> None:
        """Sin `NextTrigger` ni jefe, el nivel es un callejón sin salida."""
        from src.framework.entities.boss_base import BossBase
        from src.framework.stage.stage_loader import StageLoader

        cls = escenarios[indice_escenario]
        escena = cls(contexto)
        datos = StageLoader.load(escena._tmx_path)
        tiene_salida = datos.next_trigger is not None
        tiene_jefe = any(isinstance(e, BossBase) for e in datos.entity_list)
        assert tiene_salida or tiene_jefe, (
            f"«{escena.stage_key}» no tiene ni NextTrigger ni jefe: se entra "
            f"y no se sale"
        )

    def test_tiene_punto_de_aparicion(self, contexto, escenarios,
                                      indice_escenario) -> None:
        from src.framework.stage.stage_loader import StageLoader

        escena = escenarios[indice_escenario](contexto)
        assert StageLoader.load(escena._tmx_path).spawn_point is not None


class TestLaCadenaLlegaHastaElFinal:
    def test_los_quince_en_orden_y_luego_los_creditos(
            self, contexto, escenarios) -> None:
        sm = contexto.scene_manager
        sm.set_stage_queue(escenarios)
        sm.push(escenarios[0](contexto))

        recorrido = []
        for _ in range(len(escenarios) + 5):
            actual = sm.current
            recorrido.append(type(actual).__name__)
            if type(actual).__name__ == "EndCreditsScene":
                break
            sm._on_stage_complete(stage_id=getattr(actual, "stage_key", ""))

        assert recorrido[:-1] == [c.__name__ for c in escenarios], (
            f"la cadena no recorre los escenarios en orden: {recorrido}"
        )
        assert recorrido[-1] == "EndCreditsScene", (
            f"terminar el último nivel no lleva a los créditos: "
            f"acabó en {recorrido[-1]}"
        )

    def test_ningun_escenario_se_repite(self, contexto, escenarios) -> None:
        nombres = [c.__name__ for c in escenarios]
        assert len(set(nombres)) == len(nombres)

    def test_el_indice_guardado_apunta_al_siguiente(
            self, contexto, escenarios) -> None:
        """Al terminar un nivel, la partida tiene que reanudarse en el que
        viene, no en el que se acaba de jugar."""
        sm = contexto.scene_manager
        sm.set_stage_queue(escenarios)
        sm.push(escenarios[0](contexto))
        assert sm._next_stage_index() == 1

    def test_el_indice_no_se_sale_de_la_cola(self, contexto, escenarios) -> None:
        sm = contexto.scene_manager
        sm.set_stage_queue(escenarios)
        sm._stage_index = len(escenarios) + 10
        assert sm._next_stage_index() == len(escenarios) - 1


class TestUnaSolaIdentidadPorEscenario:
    """AUD-156 — había dos y no coincidían en dos escenarios.

    Guardar con un identificador y buscar con otro es lo que dejaba nodos
    imposibles de completar. Y con la progresión en cadena, un nodo que no se
    completa bloquea todo lo que viene detrás.
    """

    def test_todo_escenario_tiene_clave(self, contexto, escenarios,
                                        indice_escenario) -> None:
        escena = escenarios[indice_escenario](contexto)
        assert escena.stage_key, (
            f"{type(escena).__name__} no tiene identidad: ni `STAGE_ID` en la "
            f"clase ni `stage_id` en su TMX"
        )

    def test_la_clave_no_es_el_nombre_de_la_clase(self, contexto, escenarios,
                                                  indice_escenario) -> None:
        """Caer al nombre de la clase es lo que le pasaba a
        `stage2_1_oficinas`, y su nodo no se marcaba nunca."""
        cls = escenarios[indice_escenario]
        assert cls(contexto).stage_key != cls.__name__

    def test_las_claves_son_unicas(self, contexto, escenarios) -> None:
        claves = [c(contexto).stage_key for c in escenarios]
        repetidas = {k for k in claves if claves.count(k) > 1}
        assert repetidas == set(), (
            f"dos escenarios comparten identidad {sorted(repetidas)}: "
            f"completar uno marcaría el otro"
        )

    def test_el_mapa_del_mundo_usa_las_mismas(self, contexto, escenarios) -> None:
        from src.engine.scenes.world_map_scene import construir_nodos

        nodos = {n["id"] for n in construir_nodos()}
        claves = {c(contexto).stage_key for c in escenarios}
        assert nodos == claves, (
            f"el mapa del mundo y el juego no se refieren a lo mismo; nodos "
            f"que nadie puede completar: {sorted(nodos - claves)}; escenarios "
            f"sin nodo: {sorted(claves - nodos)}"
        )

    def test_completar_marca_el_nodo_correcto(self, contexto, escenarios) -> None:
        """La cadena entera: terminar el nivel 8 —el que traía el `stage_id`
        de la plantilla— tiene que marcar su nodo y abrir el 9."""
        from src.engine.scenes.world_map_scene import WorldMapScene

        octavo = escenarios[8](contexto)
        completados = [c(contexto).stage_key for c in escenarios[:9]]
        assert octavo.stage_key in completados

        mapa = WorldMapScene(contexto)
        mapa._save_data = _PartidaCon(completados)
        mapa._build_nodes()
        assert mapa._nodes[8]["completed"] is True, (
            f"«{octavo.stage_key}» no se marca aunque esté en la partida"
        )
        assert mapa._nodes[9]["unlocked"] is True


class _PartidaCon:
    def __init__(self, completados: list[str]) -> None:
        self.completed_stages = completados
