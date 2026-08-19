"""AUD-559 — propuesta de economía (pedida y aprobada por el dueño tras
auditar la tienda/árbol existentes): dos objetos nuevos en la tienda
(una prenda de gama alta, el primer consumible) y un nodo defensivo
nuevo en el árbol de habilidades.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest


@pytest.fixture(scope="module")
def _video() -> None:
    pygame.init()


@pytest.fixture
def inventario():
    """El inventario es singleton y persiste a disco en cada `save()` —
    mismo criterio que `test_inventario_recoleccion.py::_inventario_limpio`:
    se limpia `_items` en el sitio, no se reemplaza la instancia (eso
    dejaría `.load()` releer lo que otra prueba ya escribió en el mismo
    fichero real, que ningún test de este árbol redirige a un temporal)."""
    from src.engine.core.inventory import get_inventory

    inv = get_inventory()
    inv._items.clear()
    inv._equipped.clear()
    yield inv
    inv._items.clear()
    inv._equipped.clear()


class TestLaCapaAbismal:
    def test_esta_en_el_catalogo_de_la_tienda(self, inventario) -> None:
        defn = inventario.get_def("cloak_abyssal")
        assert defn is not None
        assert defn.price == 90
        assert defn.slot == "body"
        assert defn.max_hp_bonus == 1.5
        assert defn.damage_bonus == 0.6

    def test_se_compra_y_se_equipa_como_cualquier_otra_prenda(self, inventario) -> None:
        inventario.add_coins(90)
        assert inventario.buy("cloak_abyssal")
        assert inventario.equip("cloak_abyssal")
        assert inventario.get_equipped()["body"] == "cloak_abyssal"


class TestElTonicoDeSavia:
    def test_esta_en_el_catalogo_y_es_consumible(self, inventario) -> None:
        defn = inventario.get_def("tonic_sap")
        assert defn is not None
        assert defn.consumible is True
        assert defn.heal_hp == 2.0
        assert defn.price == 15

    def test_usar_sin_tener_ninguno_no_hace_nada(self, inventario) -> None:
        assert inventario.usar("tonic_sap") == 0.0

    def test_comprar_y_usar_gasta_una_unidad_y_devuelve_la_cura(
        self, inventario,
    ) -> None:
        inventario.add_coins(15)
        assert inventario.buy("tonic_sap")
        assert inventario.count("tonic_sap") == 1

        curado = inventario.usar("tonic_sap")

        assert curado == 2.0
        assert inventario.count("tonic_sap") == 0

    def test_un_objeto_no_consumible_no_se_puede_usar(self, inventario) -> None:
        inventario.add_coins(30)
        inventario.buy("hood_leaf")
        assert inventario.usar("hood_leaf") == 0.0
        # No se gastó: `usar()` en algo no consumible no hace nada, ni
        # siquiera restar una unidad.
        assert inventario.count("hood_leaf") == 1


class TestElEventoDeConsumoLlegaAlJugador:
    """`InventoryScene` gasta y emite; `StageScene` (`senales.py`) es
    quien cura de verdad, si hay un jugador vivo."""

    def test_el_manejador_cura_al_jugador(self, _video) -> None:
        from src.engine.core.event_bus import EventBus
        from src.engine.core.events import Events
        from src.framework.entities.player import Player

        bus = EventBus()
        jugador = Player(pygame.Vector2(0.0, 0.0), event_bus=bus)
        jugador._health = 1.0

        # El mismo manejador que registra `SenalesDeEscenario.
        # _subscribe_event_handlers` — probado aquí sin levantar un
        # `StageScene` entero.
        def _al_consumir(**data):
            cantidad = float(data.get("heal_hp", 0.0))
            if cantidad > 0.0:
                jugador.heal(cantidad)

        bus.subscribe(Events.ITEM_CONSUMED, _al_consumir)
        bus.emit(Events.ITEM_CONSUMED, heal_hp=2.0)
        bus.dispatch()

        assert jugador.current_health == 3.0


class TestLaCoraza:
    def test_esta_en_el_catalogo_del_arbol(self) -> None:
        from src.engine.core.skill_tree import CATALOGO

        nodo = next((n for n in CATALOGO if n.id == "coraza"), None)
        assert nodo is not None
        assert nodo.rangos == 5
        assert nodo.por_rango == 0.05
        # A diferencia de "ímpetu", no requiere ningún otro nodo: es una
        # rama independiente, no un remate de "fuerza".
        assert nodo.requiere == ""

    def test_bonus_defensa_escala_con_el_rango(self) -> None:
        from src.engine.core.experience import ExperienceSystem
        from src.engine.core.skill_tree import ArbolDeHabilidades

        ArbolDeHabilidades._reset_instance()
        ExperienceSystem._reset_instance()
        arbol = ArbolDeHabilidades.get_instance()
        exp = ExperienceSystem.get_instance()
        assert arbol.bonus_defensa() == 0.0

        exp.grant(10_000)  # de sobra para varios rangos
        for _ in range(3):
            assert arbol.comprar("coraza")

        assert arbol.bonus_defensa() == pytest.approx(0.15)
        ArbolDeHabilidades._reset_instance()
        ExperienceSystem._reset_instance()

    def test_reduce_el_dano_que_recibe_el_jugador(self, _video) -> None:
        from src.engine.core.experience import ExperienceSystem
        from src.engine.core.skill_tree import ArbolDeHabilidades
        from src.framework.entities.player import Player

        ArbolDeHabilidades._reset_instance()
        ExperienceSystem._reset_instance()
        arbol = ArbolDeHabilidades.get_instance()
        # Al tope (5 rangos, -25 %) a mano: la mecánica de puntos/coste ya
        # la prueba `test_bonus_defensa_escala_con_el_rango` — aquí sólo
        # importa que el bono, una vez al máximo, reduzca el daño real.
        arbol._rangos["coraza"] = 5

        from src.engine.core.inventory import get_inventory

        jugador = Player(pygame.Vector2(0.0, 0.0))
        jugador.apply_relic_bonuses(get_inventory())
        jugador._health = 10.0
        jugador._invincibility_timer = 0.0

        jugador.apply_damage(4.0, (0.0, 0.0))

        # 4.0 * (1 - 0.25) = 3.0 de daño real -- no los 4.0 completos.
        assert jugador.current_health == pytest.approx(7.0)
        ArbolDeHabilidades._reset_instance()
        ExperienceSystem._reset_instance()
