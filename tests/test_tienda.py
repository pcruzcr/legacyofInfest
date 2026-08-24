"""La tienda: comprar y vender ropa con las monedas — AUD-221.

El hueco (GAP-029, conexión 4 de 4)
===================================
`Inventory.buy()` y `Inventory.sell()` estaban escritos, probados por unidad
desde AUD-207 y **sin un solo llamante**. No había ninguna pantalla donde
gastar el saldo que AUD-218 hizo que subiera al jugar, así que la economía
terminaba en un número del HUD que no servía para nada.

Decisiones que estas pruebas fijan
----------------------------------
* **Entrada de menú propia**, al estilo de `BESTIARY` y `RECORDS`, y no un
  mercader en el mapa. Se probó así porque una escena de menú no obliga a
  tocar el cargador de TMX ni las 26 entregas.
* **Izquierda / derecha cambian entre comprar y vender**; arriba y abajo ya
  mueven por la lista y `CONFIRM` actúa en el modo activo. No hace falta una
  tecla nueva, que sería una que rebindear en las opciones y documentar.
* **Sólo aparece lo que tiene precio.** Las mejoras permanentes se recogen en
  el nivel, las habilidades las sueltan los jefes y `coin` es el saldo: nada
  de eso se compra, y enseñarlo prometería algo que no se puede hacer.
* **Nunca se queda a deber.** Comprar sin saldo no hace nada; es la comprobación
  que evita el saldo negativo, que en un juego de clase se encuentra en
  cuanto un estudiante pulsa Enter veinte veces seguidas.
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
    from src.engine.scenes.shop_scene import ShopScene

    entrada = _Input()
    gestor = types.SimpleNamespace(
        transition=types.SimpleNamespace(
            start_fade_in=lambda *_a, **_k: None,
            start_fade_out=lambda *_a, **_k: None,
        ),
        reemplazada_por=None,
        salio_por_pop=False,
    )
    gestor.replace = lambda escena: setattr(gestor, "reemplazada_por", escena)
    # AUD-550 — `ShopScene._volver()` sale con `pop()`, no `replace()`
    # (mismo par que `InventoryScene`/`SkillTreeScene`, AUD-533).
    gestor.pop = lambda: setattr(gestor, "salio_por_pop", True)
    contexto = types.SimpleNamespace(
        input_manager=entrada,
        scene_manager=gestor,
        audio_manager=None,
        event_bus=None,
    )
    return ShopScene(contexto), entrada, gestor


def _apuntar_a(escena, item_id: str) -> None:
    escena._menu.index = [i.value for i in escena._menu.items].index(item_id)


class TestComprar:
    def test_con_saldo_se_compra(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(100)
        escena, entrada, _ = _escena()
        _apuntar_a(escena, "hood_ember")  # 40 monedas

        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)

        assert inv.has("hood_ember")
        assert inv.coins == 60

    def test_sin_saldo_no_pasa_nada(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(5)
        escena, entrada, _ = _escena()
        _apuntar_a(escena, "cloak_serpent")  # 50 monedas

        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)

        assert not inv.has("cloak_serpent")
        assert inv.coins == 5, "el saldo se movió sin haber comprado nada"

    def test_el_saldo_nunca_baja_de_cero(self, _inventario_aislado) -> None:
        """Veinte pulsaciones seguidas sin dinero: el caso del aula."""
        inv = _inventario_aislado
        inv.add_coins(30)
        escena, entrada, _ = _escena()
        _apuntar_a(escena, "hood_leaf")  # 30 monedas

        for _ in range(20):
            entrada.pulsar(Action.CONFIRM)
            escena.update(0.016)

        assert inv.coins == 0
        assert inv.count("hood_leaf") == 1


class TestVender:
    def _en_modo_vender(self, escena, entrada):
        entrada.pulsar(Action.MOVE_RIGHT)
        escena.update(0.016)
        return escena

    def test_vender_devuelve_la_mitad(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(100)
        inv.buy("boots_swift")  # 45 → quedan 55
        escena, entrada, _ = _escena()
        self._en_modo_vender(escena, entrada)
        _apuntar_a(escena, "boots_swift")

        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)

        assert not inv.has("boots_swift")
        assert inv.coins == 55 + 45 // 2

    def test_vender_lo_que_no_se_tiene_no_da_dinero(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(10)
        escena, entrada, _ = _escena()
        self._en_modo_vender(escena, entrada)
        _apuntar_a(escena, "cloak_reed")

        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)

        assert inv.coins == 10, "vender aire imprimía monedas"

    def test_vender_la_prenda_puesta_la_desequipa(self, _inventario_aislado) -> None:
        """Lo garantiza `Inventory.sell()` desde AUD-207; aquí se comprueba
        que la tienda pasa por ese camino y no por uno propio."""
        inv = _inventario_aislado
        inv.add_coins(100)
        inv.buy("hood_ember")
        inv.equip("hood_ember")
        escena, entrada, _ = _escena()
        self._en_modo_vender(escena, entrada)
        _apuntar_a(escena, "hood_ember")

        entrada.pulsar(Action.CONFIRM)
        escena.update(0.016)

        assert inv.get_equipped() == {}
        assert inv.get_total_hp_bonus() == pytest.approx(0.0)


class TestLosDosModos:
    def test_empieza_comprando(self, _inventario_aislado) -> None:
        escena, _, _ = _escena()
        assert escena.modo == "comprar"

    def test_derecha_e_izquierda_alternan(self, _inventario_aislado) -> None:
        escena, entrada, _ = _escena()

        entrada.pulsar(Action.MOVE_RIGHT)
        escena.update(0.016)
        assert escena.modo == "vender"

        entrada.pulsar(Action.MOVE_LEFT)
        escena.update(0.016)
        assert escena.modo == "comprar"

    def test_cambiar_de_modo_no_compra(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(100)
        escena, entrada, _ = _escena()

        entrada.pulsar(Action.MOVE_RIGHT)
        escena.update(0.016)

        assert inv.coins == 100


class TestLoQueSeEnsena:
    def test_solo_hay_cosas_con_precio(self, _inventario_aislado) -> None:
        escena, _, _ = _escena()
        ids = [i.value for i in escena._menu.items]

        assert "coin" not in ids, "el saldo no es un artículo"
        assert "heart_vessel" not in ids, "las mejoras se recogen en el nivel"
        assert "skill_dash" not in ids, "las habilidades las sueltan los jefes"
        assert "hood_leaf" in ids

    def test_todas_las_prendas_del_catalogo_estan(self, _inventario_aislado) -> None:
        from src.engine.core.inventory import _ITEM_DEFS

        escena, _, _ = _escena()
        ids = {i.value for i in escena._menu.items}
        con_precio = {k for k, d in _ITEM_DEFS.items() if d.price > 0}

        assert ids == con_precio, (
            "la tienda y el catálogo se desincronizaron: la lista está escrita "
            "a mano en vez de salir de `_ITEM_DEFS`"
        )

    def test_dibujar_no_estalla_en_los_dos_modos(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(100)
        inv.buy("hood_ember")
        escena, entrada, _ = _escena()
        escena.draw(pygame.Surface((800, 600)))

        entrada.pulsar(Action.MOVE_RIGHT)
        escena.update(0.016)
        escena.draw(pygame.Surface((800, 600)))

    def test_cancelar_sale(self, _inventario_aislado) -> None:
        """AUD-550 — `pop()`, no `replace()`: quien abrió la tienda
        (el título, o una partida en pausa) sigue debajo en la pila."""
        escena, entrada, gestor = _escena()

        entrada.pulsar(Action.CANCEL)
        escena.update(0.016)

        assert gestor.salio_por_pop is True
        assert gestor.reemplazada_por is None, (
            "cancelar sigue sustituyendo la escena en vez de volver a "
            "quien la abrió"
        )


class TestEstaEnchufada:
    """El paso que este proyecto ha olvidado nueve veces: que se llegue."""

    def test_esta_en_el_registro_de_escenas(self) -> None:
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent
        registro = (raiz / "src/engine/scenes/scene_registry.py").read_text(
            encoding="utf-8",
        )
        assert "ShopScene" in registro

    def test_esta_en_el_menu_del_titulo(self) -> None:
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent
        titulo = (raiz / "src/engine/scenes/title_scene.py").read_text(
            encoding="utf-8",
        )
        assert "SHOP" in titulo, (
            "la escena existiría y no habría forma de abrirla, que es "
            "exactamente lo que le pasó a LeaderboardScene hasta AUD-202"
        )
        assert "ShopScene" in titulo
