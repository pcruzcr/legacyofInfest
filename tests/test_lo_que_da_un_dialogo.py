"""AUD-251 — lo que un diálogo entrega no llegaba a ninguna parte.

El defecto
==========
`DialogueSystem._execute_action` sabe ejecutar dos acciones de guion, y las dos
están documentadas en `docs/60_GUIA_COMPLETA_DEL_MOTOR.md` §13 como si
funcionaran:

    give_item:llave   →  emite Events.ITEM_COLLECTED
    set_flag:portal   →  emite Events.FLAG_SET

Medido con `grep -rn "subscribe(Events.ITEM_COLLECTED" src/`: **cero
suscriptores**. Un personaje podía decir «toma la llave», el evento salía al
bus, y el objeto no aparecía ni en el inventario ni en el llavero. La bandera
no la guardaba nadie, así que ninguna puerta podía abrirse por haber hablado
con alguien.

Es el mismo modo de fallo que GAP-020 (los recogibles del mundo tampoco
llegaban al inventario) y que AUD-149, AUD-206 y AUD-243: la cadena entera
escrita y desconectada **por arriba**, con pruebas de unidad verdes en las dos
mitades.

Lo que se comprueba aquí
------------------------
1. Que `give_item:` de una mejora permanente llega al `Inventory`.
2. Que `give_item:` de una llave de escenario llega al llavero, que es quien
   abre las puertas.
3. Que `set_flag:` deja la bandera en el contexto **y** que el guardado la
   persiste en `zone_flags`, el campo que `SaveData` tiene desde siempre y que
   sólo escribían las pruebas.
4. La comprobación que lo habría evitado: que los dos eventos tengan
   suscriptor en `src/`, no sólo en `tests/`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.engine.core.events import Events
from src.engine.core.inventory import get_inventory
from src.engine.core.save_data import SaveData

RAIZ = Path(__file__).resolve().parents[1]


class _EscenaMinima:
    """Lo justo que `SenalesDeEscenario` espera de la escena.

    Se monta a mano en vez de levantar una `StageScene` entera porque el
    defecto vive en el cableado del bus, no en el escenario: una escena real
    traería el TMX, el jugador y el post-procesado a una prueba que no los
    mira.
    """

    def __init__(self, context) -> None:
        self.context = context
        self._vfx_handlers: dict = {}
        self._sfx_handlers: dict = {}
        self._arboles_de_dialogo: dict = {}


@pytest.fixture
def escena(event_bus, monkeypatch):
    from src.engine.core.game_context import GameContext
    from src.framework.scenes.stage_parts.senales import SenalesDeEscenario
    from src.framework.scenes.stage_parts.sonido import SonidoDeEscenario
    from src.framework.stage.interactable_system import InteractableSystem

    class _Senales(SenalesDeEscenario, SonidoDeEscenario, _EscenaMinima):
        pass

    context = GameContext(
        input_manager=None,  # type: ignore[arg-type]
        audio_manager=None,  # type: ignore[arg-type]
        scene_manager=None,  # type: ignore[arg-type]
        event_bus=event_bus,
    )
    esc = _Senales(context)
    esc._interactables = InteractableSystem()
    esc._subscribe_event_handlers()
    return esc


class TestLoQueEntregaUnDialogo:
    def test_give_item_de_una_mejora_llega_al_inventario(self, escena) -> None:
        inv = get_inventory()
        antes = inv.count("heart_vessel")

        escena.context.event_bus.emit(Events.ITEM_COLLECTED, item_id="heart_vessel")
        escena.context.event_bus.dispatch()

        assert inv.count("heart_vessel") == antes + 1

    def test_give_item_de_una_llave_llega_al_llavero(self, escena) -> None:
        """Una llave no está en el catálogo del inventario: es del escenario.

        `Llavero.tiene("")` devuelve `True` a propósito (una puerta sin llave
        declarada se abre), así que aquí se mira el conjunto directamente.
        """
        escena.context.event_bus.emit(Events.ITEM_COLLECTED, item_id="llave_roja")
        escena.context.event_bus.dispatch()

        assert "llave_roja" in escena._interactables.llavero.llaves

    def test_set_flag_deja_la_bandera_en_el_contexto(self, escena) -> None:
        escena.context.event_bus.emit(Events.FLAG_SET, flag="portal_abierto")
        escena.context.event_bus.dispatch()

        assert escena.context.banderas.get("portal_abierto") is True

    def test_la_bandera_sobrevive_al_guardado(self, escena, tmp_path) -> None:
        """Guardar en un checkpoint tiene que llevarse las banderas.

        `SaveData.zone_flags` existe desde el principio y hasta hoy sólo lo
        escribían las pruebas: el juego nunca ponía una bandera dentro.
        """
        from src.engine.core.save_manager import SaveManager

        sm = SaveManager()
        sm.SAVES_DIR = tmp_path / "saves"
        sm.SAVES_DIR.mkdir(parents=True, exist_ok=True)
        escena.context.save_manager = sm
        escena.context.event_bus.emit(Events.FLAG_SET, flag="portal_abierto")
        escena.context.event_bus.dispatch()

        escena.context.event_bus.emit(
            Events.SAVE_REQUESTED, stage_id="stage0", stage_index=0,
            checkpoint_x=10.0, checkpoint_y=20.0, health=5.0, max_health=5.0,
        )
        escena.context.event_bus.dispatch()

        guardada = escena.context.save_manager.load(
            escena.context.save_manager.newest_slot() or 1)
        assert guardada is not None
        assert guardada.zone_flags.get("portal_abierto") is True

    def test_cargar_una_partida_devuelve_las_banderas(self) -> None:
        """Y al revés: entrar en el escenario recupera lo que se guardó."""
        from src.engine.core.game_context import GameContext

        context = GameContext(
            input_manager=None,  # type: ignore[arg-type]
            audio_manager=None,  # type: ignore[arg-type]
            scene_manager=None,  # type: ignore[arg-type]
            event_bus=None,  # type: ignore[arg-type]
        )
        context.pending_load = SaveData(zone_flags={"portal_abierto": True})

        from src.framework.scenes.stage_scene import StageScene

        StageScene._restaurar_banderas(context, context.pending_load)

        assert context.banderas.get("portal_abierto") is True


class TestLaComprobacionQueLoHabriaEvitado:
    """Los dos eventos tienen que tener suscriptor en `src/`, no en `tests/`.

    Es la lección de AUD-243: una prueba de unidad sobre las dos mitades pasa
    igual de verde cuando nadie las une.
    """

    #: Los dos ficheros que **no** cuentan como oyente: el catálogo donde el
    #: nombre se declara y el módulo que lo emite. Si sólo aparece ahí, el
    #: evento sigue hablando solo.
    _NO_CUENTAN = {"events.py", "dialogue_system.py"}

    @pytest.mark.parametrize("evento", ["ITEM_COLLECTED", "FLAG_SET"])
    def test_el_evento_tiene_lector_en_produccion(self, evento: str) -> None:
        lectores = [
            p.name for p in (RAIZ / "src").rglob("*.py")
            if p.name not in self._NO_CUENTAN
            and f"Events.{evento}" in p.read_text(encoding="utf-8")
        ]
        assert lectores, (
            f"Events.{evento} se emite y nadie lo lee en src/. "
            "Es el defecto que esta prueba existe para evitar."
        )
