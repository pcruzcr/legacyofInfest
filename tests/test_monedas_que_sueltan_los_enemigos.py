"""Matar a un enemigo deja una moneda en el suelo — AUD-218.

El hueco (GAP-029, conexión 1 de 4)
===================================
La economía tenía catálogo y API —`coin`, `add_coins`, `buy`, `sell`— y ni una
sola moneda que ganar. `EnemyBase._die()` emitía `ENEMY_DIED`, la escena lo
escuchaba **sólo para lanzar partículas**, y ahí acababa todo. El saldo del
jugador no podía subir por jugar: la única forma de tener monedas era editar
`data/inventory.json` a mano.

Lo que se comprueba aquí es el circuito entero contra el código real, no cada
pieza por su lado — que es como este proyecto ha dejado pasar nueve veces dos
mitades que no se hablaban:

    EnemyBase._die() → ENEMY_DIED → (EventBus.dispatch)
    → SenalesDeEscenario._on_enemy_died → Recogible("coin") en el suelo
    → InteractableSystem._recoger() → EVENTO_RECOGIDO
    → SenalesDeEscenario._on_item_picked → Inventory.collect("coin", n)
    → Inventory.coins

El `EventBus` **encola** con `emit()` y reparte con `dispatch()` al principio
del fotograma siguiente (`22_API_CONTRACTS.md` §2.3), así que las pruebas
llaman a `dispatch()` donde lo hace `App`.
"""
from __future__ import annotations

import types
from unittest.mock import MagicMock

import pygame
import pytest

from src.engine.core import inventory as inv_mod
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.core.inventory import get_inventory
from src.framework.scenes.stage_parts.economia import EconomiaDeEscenario
from src.framework.scenes.stage_parts.senales import SenalesDeEscenario
from src.framework.scenes.stage_parts.sonido import SonidoDeEscenario
from src.framework.stage.interactable_system import InteractableSystem

DT = 1.0 / 60.0


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


@pytest.fixture(autouse=True)
def _inventario_aislado(tmp_path, monkeypatch):
    monkeypatch.setattr(inv_mod, "_INVENTORY_PATH", tmp_path / "inventory.json")
    inv = get_inventory()
    inv._items.clear()
    inv._equipped.clear()
    yield inv
    inv._items.clear()
    inv._equipped.clear()


def _escena():
    """La escena mínima que `SenalesDeEscenario` necesita para suscribirse.

    Se simulan los subsistemas de dibujo y sonido porque lo que se prueba es
    el circuito de la moneda, no el acabado visual.
    """
    bus = EventBus()
    interactables = InteractableSystem(bus=bus)

    escena = MagicMock()
    escena.context = types.SimpleNamespace(event_bus=bus, save_manager=None)
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
    # Los métodos reales del mixin, enlazados a la escena simulada: es el
    # código de producción el que corre, no un doble. AUD-595: el botín
    # vive en `EconomiaDeEscenario`, no en `SenalesDeEscenario`.
    escena._BOTIN_TAM = EconomiaDeEscenario._BOTIN_TAM
    escena._soltar_botin = EconomiaDeEscenario._soltar_botin.__get__(escena)
    escena._make_sfx_handler = SonidoDeEscenario._make_sfx_handler.__get__(escena)
    escena._play_sfx_named = SonidoDeEscenario._play_sfx_named.__get__(escena)
    escena._play_sfx_spatial = SonidoDeEscenario._play_sfx_spatial.__get__(escena)

    SonidoDeEscenario._subscribe_sfx_handlers(escena) or SenalesDeEscenario._subscribe_event_handlers(escena)
    return escena, interactables, bus


def _muere(bus, entity_id: str, pos=(100.0, 200.0)) -> None:
    bus.emit(Events.ENEMY_DIED, entity_id=entity_id, position=pos)
    bus.dispatch()


class TestLaMonedaApareceEnElSuelo:
    def test_matar_a_un_enemigo_deja_un_recogible(self) -> None:
        _, interactables, bus = _escena()
        assert interactables.recogibles == []

        _muere(bus, "EnemyWalker_1")

        monedas = [r for r in interactables.recogibles if r.item_id == "coin"]
        assert monedas, (
            "el enemigo murió y no soltó nada: `_on_enemy_died` sólo lanzaba "
            "partículas y el saldo del jugador no podía subir jugando"
        )

    def test_la_moneda_cae_donde_murio(self) -> None:
        _, interactables, bus = _escena()

        _muere(bus, "EnemyWalker_1", pos=(300.0, 150.0))

        moneda = interactables.recogibles[0]
        assert moneda.rect.collidepoint(300, 150), (
            f"la moneda cayó en {moneda.rect}, no donde murió el enemigo"
        )

    def test_se_coge_al_pasar_por_encima(self) -> None:
        """Automática: una moneda que hay que pulsar para coger es un estorbo."""
        _, interactables, bus = _escena()
        _muere(bus, "EnemyWalker_1")

        assert interactables.recogibles[0].automatico is True

    def test_un_cadaver_no_suelta_dos_veces(self) -> None:
        """`_die()` emite una vez, pero el evento puede repetirse por rebote."""
        _, interactables, bus = _escena()

        _muere(bus, "EnemyWalker_7")
        _muere(bus, "EnemyWalker_7")

        assert len(interactables.recogibles) == 1, (
            "el mismo enemigo soltó dos montones de monedas"
        )


class TestElSaldoSubeAlCogerla:
    def test_el_circuito_entero_llega_al_inventario(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        _, interactables, bus = _escena()
        assert inv.coins == 0

        _muere(bus, "EnemyWalker_1", pos=(100.0, 200.0))
        # El jugador pasa por encima de donde cayó.
        interactables.update(DT, pygame.Rect(90, 190, 20, 32))
        bus.dispatch()

        assert inv.coins > 0, (
            "la moneda se recogió y el saldo siguió a cero: `collect()` no "
            "llegó, o llegó sin la cantidad"
        )

    def test_un_jefe_paga_mucho_mas_que_un_peon(self, _inventario_aislado) -> None:
        """Si matar al jefe rinde como un walker, la tienda no se alcanza."""
        from src.engine.core.score_system import coins_for

        assert coins_for("BossVenado_1") > coins_for("EnemyWalker_1") * 5

    def test_un_tipo_desconocido_paga_algo_pero_poco(self) -> None:
        """Un enemigo de una entrega no está en la tabla y no debe dar cero."""
        from src.engine.core.score_system import coins_for

        valor = coins_for("CuadernoVolador_3")
        assert valor >= 1
        assert valor < coins_for("BossGavilan_1")


class TestLaCantidadViajaEnElRecogible:
    """`Recogible.cantidad` es lo que permite una bolsa de monedas sin poner
    veinte objetos en el suelo — y sirve igual para las entregas."""

    def test_el_recogible_declara_cuanto_vale(self) -> None:
        from src.engine.core.score_system import coins_for

        _, interactables, bus = _escena()
        _muere(bus, "EnemyBrute_1")

        assert interactables.recogibles[0].cantidad == coins_for("EnemyBrute_1")

    def test_una_bolsa_de_diez_da_diez(self, _inventario_aislado) -> None:
        from src.framework.stage.interactables import Recogible

        inv = _inventario_aislado
        _, interactables, bus = _escena()
        interactables.recogibles.append(
            Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="coin", cantidad=10),
        )

        interactables.update(DT, pygame.Rect(0, 0, 20, 32))
        bus.dispatch()

        assert inv.coins == 10

    def test_por_defecto_vale_una(self) -> None:
        """Las entregas existentes construyen `Recogible` sin ese campo."""
        from src.framework.stage.interactables import Recogible

        assert Recogible(rect=pygame.Rect(0, 0, 8, 8), item_id="llave").cantidad == 1

    def test_una_mejora_recogida_sigue_contando_una(self, _inventario_aislado) -> None:
        """El control: `cantidad` no puede cambiar lo que ya funcionaba."""
        from src.framework.stage.interactables import Recogible

        inv = _inventario_aislado
        _, interactables, bus = _escena()
        interactables.recogibles.append(
            Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_vessel"),
        )

        interactables.update(DT, pygame.Rect(0, 0, 20, 32))
        bus.dispatch()

        assert inv.count("heart_vessel") == 1
        assert inv.get_total_hp_bonus() == pytest.approx(1.0)
