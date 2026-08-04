"""Un recogible del mapa llega al inventario de mejoras permanentes.

GAP-025
=======
`InteractableSystem._recoger()` guardaba el objeto en el llavero y emitía
`EVENTO_RECOGIDO`, pero nadie escuchaba ese evento. Un `Recogible` con
`item_id="heart_vessel"` —un objeto que la clase documenta como «si coincide
con un objeto de `engine.core.inventory` se aplica su efecto»— se recogía,
mostraba el aviso, y la mejora permanente se perdía en silencio: el
`Inventory` nunca recibía `collect()`.

    La corrección conectó el bus con el inventario desde
    `SenalesDeEscenario._subscribe_event_handlers()`. Aquí se comprueba el
    circuito completo contra el código real:

    Recogible → InteractableSystem._recoger() → EVENTO_RECOGIDO
    → (EventBus.dispatch) → SenalesDeEscenario._on_item_picked
    → Inventory.collect() → get_total_hp_bonus() refleja la mejora

    El `EventBus` del proyecto **encola** los eventos con `emit()` y los
    despacha con `dispatch()` al inicio del siguiente fotograma
    (`22_API_CONTRACTS.md` §2.3). El test llama a `dispatch()` después de cada
    `update()`, igual que hace `App` en el bucle real.

    Se usan `Mock` para los subsistemas de dibujo y sonido del mixin porque lo
    que se está probando es la conexión de recolección, no el acabado visual.
"""
from __future__ import annotations

import types
from unittest.mock import MagicMock

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.inventory import get_inventory
from src.framework.scenes.stage_parts.senales import SenalesDeEscenario
from src.framework.stage.interactable_system import InteractableSystem
from src.framework.stage.interactables import Recogible

DT = 1.0 / 60.0


@pytest.fixture(autouse=True)
def _inventario_limpio():
    """El inventario es singleton: cada prueba empieza de cero."""
    get_inventory()._items.clear()


def _escena_con_recogible(item_id: str, automatico: bool = True):
    """Monta la escena mínima —lo justo para que el mixin se suscriba— con un
    recogible en el suelo en (0, 0)."""
    bus = EventBus()
    inventario = get_inventory()

    # El sistema de interactuables que el StageScene construye de verdad.
    recogible = Recogible(
        rect=pygame.Rect(0, 0, 16, 16),
        item_id=item_id,
        automatico=automatico,
    )
    interactables = InteractableSystem(recogibles=[recogible], bus=bus)

    # La escena mínima que `SenalesDeEscenario` espera. Nada de esto participa
    # en la recolección, pero el mixin los toca al suscribirse.
    contexto = types.SimpleNamespace(event_bus=bus, save_manager=None)
    escena = MagicMock()
    escena.context = contexto
    escena.audio = None
    escena._interactables = interactables
    escena._vfx_handlers = {}
    escena._sfx_handlers = {}
    escena._particle_system.get_emitter.return_value.emit = MagicMock()
    escena._damage_numbers.add = MagicMock()
    escena._camera.offset = MagicMock()
    escena._camera.apply_shake = MagicMock()
    escena._post_processing.flash = MagicMock()
    escena._post_processing.set_damage_vignette = MagicMock()
    escena._post_processing.set_bloom = MagicMock()
    # `_make_sfx_handler` y `_play_sfx_*` son métodos reales del mixin; al
    # enlazarlos a la escena simulada funcionan con `audio=None`.
    escena._make_sfx_handler = SenalesDeEscenario._make_sfx_handler.__get__(escena)
    escena._play_sfx_named = SenalesDeEscenario._play_sfx_named.__get__(escena)
    escena._play_sfx_spatial = SenalesDeEscenario._play_sfx_spatial.__get__(escena)

    # Suscribir los manejadores reales del mixin, incluido `_on_item_picked`.
    SenalesDeEscenario._subscribe_event_handlers(escena)

    return escena, interactables, recogible, inventario


class TestLaRecoleccionLlegaAlInventario:
    def test_heart_vessel_se_convierte_en_mejora_permanente(self) -> None:
        escena, interactables, recogible, inventario = _escena_con_recogible(
            "heart_vessel",
        )

        # El jugador pasa por encima del recogible automático.
        interactables.update(DT, pygame.Rect(0, 0, 20, 32))
        escena.context.event_bus.dispatch()  # App.dispatch() en el bucle real

        assert recogible.recogido, "el recogible no se marcó como cogido"
        assert inventario.has("heart_vessel"), (
            "heart_vessel se recogió pero el Inventory no lo registró (GAP-025)"
        )
        assert inventario.get_total_hp_bonus() == pytest.approx(1.0)

    def test_el_bonus_doble_acumula(self) -> None:
        """Dos vasijas de corazón suman +2 de vida máxima."""
        escena, interactables, _recogible, inventario = _escena_con_recogible(
            "heart_vessel",
        )
        interactables.recogibles.append(
            Recogible(rect=pygame.Rect(40, 0, 16, 16), item_id="heart_vessel"),
        )

        interactables.update(DT, pygame.Rect(0, 0, 20, 32))
        escena.context.event_bus.dispatch()
        interactables.update(DT, pygame.Rect(44, 0, 20, 32))
        escena.context.event_bus.dispatch()

        assert inventario.count("heart_vessel") == 2
        assert inventario.get_total_hp_bonus() == pytest.approx(2.0)

    def test_una_llave_no_entra_en_el_inventario_de_mejoras(self) -> None:
        """`llave_roja` no es una mejora: sigue siendo solo llave del llavero."""
        escena, interactables, recogible, inventario = _escena_con_recogible(
            "llave_roja",
        )

        interactables.update(DT, pygame.Rect(0, 0, 20, 32))
        escena.context.event_bus.dispatch()

        assert recogible.recogido
        assert interactables.llavero.tiene("llave_roja")
        assert not inventario.has("llave_roja")

    def test_el_bono_rapido_aplica_velocidad(self) -> None:
        """`swift_feather` declara +10 % de velocidad y así llega al total."""
        escena, interactables, _recogible, inventario = _escena_con_recogible(
            "swift_feather",
        )

        interactables.update(DT, pygame.Rect(0, 0, 20, 32))
        escena.context.event_bus.dispatch()

        assert inventario.get_total_speed_bonus() == pytest.approx(10.0)
