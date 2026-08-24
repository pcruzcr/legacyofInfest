"""La pantalla de inventario deja ponerse la ropa — AUD-220.

El hueco (GAP-029, conexión 3 de 4)
===================================
AUD-207 hizo que equiparse importara: la bonificación de una prenda sólo
cuenta si está en su hueco. Pero `InventoryScene` —la pantalla que abre
`INVENTORY` desde el título— sólo **enseñaba** la rejilla. `Inventory.equip()`
seguía sin un solo llamante en toda la interfaz, así que la única forma de
ponerse algo era desde una consola de Python.

Dicho de otro modo: AUD-207 convirtió una bonificación automática en una que
requiere una acción, y esa acción no existía. Sin esto, comprar ropa
*empeoraba* al jugador respecto a antes.

Decisiones que estas pruebas fijan
----------------------------------
* `CONFIRM` equipa y desequipa. Antes salía de la pantalla, que era un atajo
  redundante: `CANCEL` ya hacía eso y sigue haciéndolo.
* Una mejora permanente no se equipa —no tiene hueco— y pulsarla no debe
  hacer nada raro, y desde luego no sacarte de la pantalla.
* Las monedas no ocupan casilla: son el saldo, no un objeto que mirar.
"""
from __future__ import annotations

import types

import pygame
import pytest

from src.engine.core import inventory as inv_mod
from src.engine.core.inventory import get_inventory
from src.engine.input.action_map import Action


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


@pytest.fixture(autouse=True)
def _inventario_aislado(tmp_path, monkeypatch):
    monkeypatch.setattr(inv_mod, "_INVENTORY_PATH", tmp_path / "inventory.json")
    inv = get_inventory()
    inv._items.clear()
    inv._equipped.clear()
    yield inv
    inv._items.clear()
    inv._equipped.clear()


class _Input:
    """Gestor de entrada falso: una pulsación, consumida al leerla."""

    def __init__(self) -> None:
        self._pendiente: Action | None = None

    def pulsar(self, accion: Action) -> None:
        self._pendiente = accion

    def is_action_just_pressed(self, accion: Action) -> bool:
        if self._pendiente == accion:
            self._pendiente = None
            return True
        return False


def _escena():
    from src.engine.scenes.inventory_scene import InventoryScene

    entrada = _Input()
    gestor = types.SimpleNamespace(
        transition=types.SimpleNamespace(
            start_fade_in=lambda *_a, **_k: None,
            start_fade_out=lambda *_a, **_k: None,
        ),
        replace=lambda escena: setattr(gestor, "reemplazada_por", escena),
        reemplazada_por=None,
        # AUD-533 — `InventoryScene` sale ahora con `pop()`, no `replace(...)`,
        # para poder volver a una partida en pausa y no sólo al título.
        pop=lambda: setattr(gestor, "salio_por_pop", True),
        salio_por_pop=False,
    )
    contexto = types.SimpleNamespace(
        input_manager=entrada,
        scene_manager=gestor,
        audio_manager=None,
        event_bus=None,
    )
    return InventoryScene(contexto), entrada, gestor


def _seleccionar(escena, item_id: str) -> None:
    """Deja el cursor sobre `item_id`, sea cual sea el orden de la rejilla."""
    escena._selected_slot = escena._item_ids().index(item_id)


class TestPonerseYQuitarseLaRopa:
    def test_confirmar_equipa_la_prenda(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(100)
        inv.buy("hood_ember")
        escena, entrada, _ = _escena()
        _seleccionar(escena, "hood_ember")

        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)

        assert inv.get_equipped().get("head") == "hood_ember", (
            "la única forma de ponerse ropa seguía siendo una consola de Python"
        )
        assert inv.get_total_hp_bonus() == pytest.approx(0.5)

    def test_confirmar_otra_vez_se_la_quita(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(100)
        inv.buy("boots_swift")
        escena, entrada, _ = _escena()
        _seleccionar(escena, "boots_swift")

        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)
        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)

        assert inv.get_equipped() == {}
        assert inv.get_total_speed_bonus() == pytest.approx(0.0)

    def test_equipar_no_saca_de_la_pantalla(self, _inventario_aislado) -> None:
        """Antes `CONFIRM` salía; si siguiera saliendo, equipar sería inusable."""
        inv = _inventario_aislado
        inv.add_coins(100)
        inv.buy("cloak_reed")
        escena, entrada, gestor = _escena()
        _seleccionar(escena, "cloak_reed")

        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)

        assert gestor.reemplazada_por is None

    def test_cancelar_sigue_saliendo(self, _inventario_aislado) -> None:
        escena, entrada, gestor = _escena()

        entrada.pulsar(Action.CANCEL)
        escena.update(0.016)

        assert gestor.salio_por_pop, (
            "sin salida, la pantalla es una trampa"
        )

    def test_una_mejora_permanente_no_se_equipa(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.collect("heart_vessel")
        escena, entrada, gestor = _escena()
        _seleccionar(escena, "heart_vessel")

        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)

        assert inv.get_equipped() == {}
        assert gestor.reemplazada_por is None, (
            "pulsar sobre algo que no se equipa te echaba de la pantalla"
        )

    def test_cambiar_de_prenda_libera_el_hueco(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(200)
        inv.buy("hood_leaf")
        inv.buy("hood_ember")
        escena, entrada, _ = _escena()

        _seleccionar(escena, "hood_leaf")
        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)
        _seleccionar(escena, "hood_ember")
        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)

        assert inv.get_equipped() == {"head": "hood_ember"}


class TestLaRejillaEnsenaLoQueImporta:
    def test_las_monedas_no_ocupan_casilla(self, _inventario_aislado) -> None:
        """El saldo es una cifra de cabecera, no un objeto que mirar."""
        inv = _inventario_aislado
        inv.add_coins(37)
        inv.collect("heart_vessel")
        escena, _, _ = _escena()

        assert "coin" not in escena._item_ids()
        assert "heart_vessel" in escena._item_ids()

    def test_con_solo_monedas_la_rejilla_esta_vacia(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(10)
        escena, _, _ = _escena()

        assert escena._item_ids() == []

    def test_dibujarla_no_estalla_con_algo_equipado(self, _inventario_aislado) -> None:
        """La marca de «puesto» se dibuja; que al menos no rompa el fotograma."""
        inv = _inventario_aislado
        inv.add_coins(100)
        inv.buy("hood_ember")
        inv.equip("hood_ember")
        inv.collect("heart_vessel")
        escena, _, _ = _escena()

        escena.draw(pygame.Surface((800, 600)))

    def test_dibujarla_vacia_tampoco_estalla(self, _inventario_aislado) -> None:
        escena, _, _ = _escena()
        escena.draw(pygame.Surface((800, 600)))

    def test_el_cursor_no_se_sale_al_desaparecer_un_objeto(
        self, _inventario_aislado,
    ) -> None:
        """Vender desde otra pantalla deja el cursor apuntando a un hueco."""
        inv = _inventario_aislado
        inv.add_coins(200)
        inv.buy("hood_ember")
        inv.buy("boots_swift")
        escena, entrada, _ = _escena()
        escena._selected_slot = 1

        inv.sell("boots_swift")
        escena.draw(pygame.Surface((800, 600)))
        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)
