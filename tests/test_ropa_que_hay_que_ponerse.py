"""La ropa sólo cuenta si te la pones — AUD-207.

El hueco
========
El catálogo de `engine.core.inventory` ya distinguía dos familias de objetos:

* **mejoras permanentes** (`heart_vessel`, `swift_feather`…), con `slot=None`.
  Se recogen en el mapa y son acumulativas por diseño: dos vasijas son +2 de
  vida. Eso está bien y no se toca.
* **ropa** (`hood_leaf`, `cloak_reed`, `boots_swift`…), con `slot` y `price`.
  Se compra, se equipa en su hueco y se vende.

Pero `get_total_hp_bonus()` y sus dos hermanas sumaban **todo lo que hubiera en
`_items`, multiplicado por la cantidad**, sin mirar `_equipped` ni una vez.
Consecuencias medidas antes de tocar nada:

1. Comprar una prenda daba su bonus sin ponérsela. `equip()` era decorativo:
   escribía en `_equipped` y nadie leía ese diccionario.
2. Las dos capuchas apilaban a la vez, aunque `slot="head"` dice que sólo cabe
   una. Lo mismo con las capas y las botas.
3. Comprar la misma prenda dos veces duplicaba el bonus.
4. Vender una prenda equipada te dejaba el bonus puesto: `sell()` borraba el
   objeto de `_items` y no tocaba `_equipped`.

O sea: la tienda vendía números, no ropa, y la única estrategia era comprar de
todo. Un hueco de equipamiento que no obliga a elegir no es un hueco.
"""
from __future__ import annotations

import pytest

from src.engine.core import inventory as inv_mod
from src.engine.core.inventory import get_inventory


@pytest.fixture(autouse=True)
def _inventario_aislado(tmp_path, monkeypatch):
    """El inventario es un singleton que persiste en disco: cada prueba
    empieza de cero y escribe en su propio fichero, no en el del repositorio."""
    monkeypatch.setattr(inv_mod, "_INVENTORY_PATH", tmp_path / "inventory.json")
    inventario = get_inventory()
    inventario._items.clear()
    inventario._equipped.clear()
    yield inventario
    inventario._items.clear()
    inventario._equipped.clear()


class TestLaRopaHayQuePonersela:
    def test_tener_la_prenda_no_basta(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(100)

        assert inv.buy("hood_ember"), "no se pudo comprar con saldo de sobra"

        assert inv.get_total_hp_bonus() == pytest.approx(0.0), (
            "la capucha daba +0,5 de vida guardada en la mochila; `equip()` "
            "escribía en `_equipped` y los totales no miraban ese diccionario"
        )

    def test_ponersela_es_lo_que_la_activa(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(100)
        inv.buy("hood_ember")

        assert inv.equip("hood_ember")

        assert inv.get_total_hp_bonus() == pytest.approx(0.5)

    def test_quitarsela_la_apaga(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(100)
        inv.buy("boots_swift")
        inv.equip("boots_swift")
        assert inv.get_total_speed_bonus() == pytest.approx(8.0)

        assert inv.unequip("feet")

        assert inv.get_total_speed_bonus() == pytest.approx(0.0)

    def test_dos_prendas_del_mismo_hueco_no_apilan(self, _inventario_aislado) -> None:
        """Sólo se lleva una capucha. Equipar la segunda sustituye a la primera."""
        inv = _inventario_aislado
        inv.add_coins(200)
        inv.buy("hood_leaf")    # +0,2 de daño
        inv.buy("hood_ember")   # +0,5 de vida
        inv.equip("hood_leaf")
        inv.equip("hood_ember")

        assert inv.get_equipped()["head"] == "hood_ember"
        assert inv.get_total_hp_bonus() == pytest.approx(0.5)
        assert inv.get_total_damage_bonus() == pytest.approx(0.0), (
            "las dos capuchas contaban a la vez pese a compartir `slot='head'`"
        )

    def test_comprar_la_misma_prenda_dos_veces_no_duplica(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(200)
        inv.buy("cloak_serpent")
        inv.buy("cloak_serpent")
        inv.equip("cloak_serpent")

        assert inv.count("cloak_serpent") == 2
        assert inv.get_total_damage_bonus() == pytest.approx(0.4), (
            "el bonus se multiplicaba por la cantidad: dos capas iguales daban "
            "el doble aunque sólo se pueda llevar una puesta"
        )

    def test_prendas_de_huecos_distintos_si_suman(self, _inventario_aislado) -> None:
        """Elegir bien el conjunto es la mecánica; que no sume sería inútil."""
        inv = _inventario_aislado
        inv.add_coins(200)
        inv.buy("hood_ember")   # +0,5 vida
        inv.buy("boots_stone")  # +1,0 vida
        inv.equip("hood_ember")
        inv.equip("boots_stone")

        assert inv.get_total_hp_bonus() == pytest.approx(1.5)


class TestVenderQuitaLoQueSeLleva:
    def test_vender_la_ultima_copia_desequipa(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(100)
        inv.buy("boots_swift")
        inv.equip("boots_swift")

        assert inv.sell("boots_swift")

        assert "feet" not in inv.get_equipped(), (
            "se vendieron las botas y seguían puestas"
        )
        assert inv.get_total_speed_bonus() == pytest.approx(0.0), (
            "vender la prenda equipada te dejaba el bonus: `sell()` borraba de "
            "`_items` y no tocaba `_equipped`"
        )

    def test_vender_una_copia_de_dos_no_desequipa(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.add_coins(200)
        inv.buy("boots_swift")
        inv.buy("boots_swift")
        inv.equip("boots_swift")

        inv.sell("boots_swift")

        assert inv.get_equipped().get("feet") == "boots_swift"
        assert inv.get_total_speed_bonus() == pytest.approx(8.0)


class TestLoQueSeCargaDeDisco:
    def test_no_se_equipa_lo_que_no_se_tiene(self, _inventario_aislado, tmp_path) -> None:
        """Un fichero editado a mano no debe regalar bonus."""
        import orjson

        (tmp_path / "inventory.json").write_bytes(orjson.dumps({
            "items": {},                      # no tiene nada
            "equipped": {"head": "hood_ember"},  # pero dice llevarlo puesto
        }))

        inv = _inventario_aislado
        inv.load()

        assert inv.get_equipped() == {}
        assert inv.get_total_hp_bonus() == pytest.approx(0.0)

    def test_un_fichero_corrupto_tambien_te_desnuda(
        self, _inventario_aislado, tmp_path,
    ) -> None:
        """«Empezar de cero» incluye lo que se lleva puesto."""
        inv = _inventario_aislado
        inv.add_coins(100)
        inv.buy("hood_ember")
        inv.equip("hood_ember")
        (tmp_path / "inventory.json").write_bytes(b"{esto no es json")

        inv.load()

        assert inv.get_equipped() == {}
        assert inv.get_total_hp_bonus() == pytest.approx(0.0)

    def test_una_prenda_que_si_se_tiene_sobrevive_al_guardado(
        self, _inventario_aislado,
    ) -> None:
        inv = _inventario_aislado
        inv.add_coins(100)
        inv.buy("cloak_reed")
        inv.equip("cloak_reed")

        inv.load()  # relee lo que `equip()` acaba de guardar

        assert inv.get_equipped() == {"body": "cloak_reed"}
        assert inv.get_total_speed_bonus() == pytest.approx(5.0)


class TestLasMejorasDelMapaSiguenIgual:
    """El control. Las mejoras permanentes no son ropa: no tienen hueco, se
    recogen en el nivel y apilan por cantidad. Cambiar eso rompería
    `test_inventario_recoleccion.py` y el diseño de los niveles."""

    def test_dos_vasijas_siguen_dando_dos_de_vida(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.collect("heart_vessel")
        inv.collect("heart_vessel")

        assert inv.get_total_hp_bonus() == pytest.approx(2.0)

    def test_una_mejora_no_necesita_equiparse(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        inv.collect("swift_feather")

        assert inv.get_equipped() == {}
        assert inv.get_total_speed_bonus() == pytest.approx(10.0)

    def test_una_mejora_no_se_puede_equipar(self, _inventario_aislado) -> None:
        """No tiene hueco: `equip()` debe rechazarla, no inventarle uno."""
        inv = _inventario_aislado
        inv.collect("heart_vessel")

        assert not inv.equip("heart_vessel")
