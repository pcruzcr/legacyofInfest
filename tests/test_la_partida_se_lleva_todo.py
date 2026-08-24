"""AUD-292 — la partida guardaba dónde estabas y no lo que tenías.

El defecto
----------
Lo que el jugador acumula vivía en tres sitios que no se hablaban:

* la **puntuación** en `data/score.json`,
* el **inventario** —y con él las monedas— en `data/inventory.json`,
* la **experiencia** dentro del slot desde AUD-267… y nadie volvía a leerla.

Los dos primeros eran globales. Cargar la partida 2 dejaba la cartera y la ropa
de la partida 1; empezar una nueva no vaciaba nada; y dos personas turnándose en
el mismo equipo compartían dinero. La tercera era peor de otra forma: la
experiencia se escribía en el disco y al cargar la partida el jugador volvía a
nivel 1 con sus puntos a cero.

La trampa de la experiencia
---------------------------
`exp_total` sola **no basta**, y el propio `ExperienceSystem` lo dice: los
puntos ya gastados no se deducen de la experiencia. Restaurando sólo el total,
cargar una partida le devolvería al jugador todos los puntos que ya se gastó —y
con ellos podría comprar el árbol dos veces—. Por eso el slot guarda los tres
números.
"""
from __future__ import annotations

import pytest

from src.engine.core.save_data import SAVE_VERSION, SaveData
from src.engine.core.save_manager import aplicar_estado_de, volcar_estado_en


@pytest.fixture
def limpio():
    """Inventario, marcador y experiencia a cero, en un disco de usar y tirar."""
    from src.engine.core.experience import ExperienceSystem
    from src.engine.core.inventory import get_inventory
    from src.engine.core.score_system import ScoreSystem

    inv = get_inventory()
    inv.restaurar({}, {})
    ScoreSystem.get_instance().reset()
    ExperienceSystem.get_instance().reset()
    return inv


class TestElEsquema:
    def test_la_version_subio(self) -> None:
        # AUD-438 la llevó a 4 al meter los logros dentro de la partida.
        assert SAVE_VERSION == 4

    def test_una_partida_nueva_trae_los_campos(self) -> None:
        data = SaveData()
        assert data.score == 0
        assert data.inventory_items == {}
        assert data.exp_estado == {}

    def test_una_partida_de_la_v2_se_carga_sin_perder_nada(self) -> None:
        vieja = {"version": 2, "stage_id": "stage1_1", "exp_total": 400,
                 "completed_stages": ["stage0"], "health": 3.0}
        data = SaveData.from_dict(vieja)
        assert data.stage_id == "stage1_1"
        assert data.exp_total == 400
        assert data.completed_stages == ["stage0"]
        assert data.health == 3.0


class TestVolcarYAplicar:
    def test_lo_que_tienes_acaba_en_la_partida(self, limpio) -> None:
        from src.engine.core.score_system import ScoreSystem

        limpio.add_coins(37)
        ScoreSystem.get_instance().set_score(1200)

        data = SaveData()
        volcar_estado_en(data)
        assert data.inventory_items.get("coin") == 37
        assert data.score == 1200

    def test_cargar_otra_partida_sustituye_la_cartera(self, limpio) -> None:
        """El defecto exacto: cargar el slot 2 dejaba el dinero del slot 1."""
        limpio.add_coins(500)
        data = SaveData(version=3, inventory_items={"coin": 10})
        aplicar_estado_de(data)
        assert limpio.coins == 10, "la cartera se fundió en vez de sustituirse"

    def test_y_el_marcador(self, limpio) -> None:
        from src.engine.core.score_system import ScoreSystem

        ScoreSystem.get_instance().set_score(9999)
        aplicar_estado_de(SaveData(version=3, score=120))
        assert ScoreSystem.get_instance().score == 120

    def test_una_partida_vieja_no_vacia_la_cartera(self, limpio) -> None:
        """Vaciarle el inventario a quien carga una partida de la versión 2
        sería cobrarle la migración."""
        limpio.add_coins(500)
        aplicar_estado_de(SaveData.from_dict({"version": 2, "stage_id": "x"}))
        assert limpio.coins == 500

    def test_un_objeto_inventado_no_entra(self, limpio) -> None:
        """Una partida editada a mano no debe poder meter objetos que no están
        en el catálogo."""
        aplicar_estado_de(SaveData(version=3,
                                   inventory_items={"espada_laser": 1, "coin": 5}))
        assert not limpio.has("espada_laser")
        assert limpio.coins == 5

    def test_ropa_que_no_se_tiene_no_se_equipa(self, limpio) -> None:
        """AUD-207: si no, cobra el bonus gratis."""
        aplicar_estado_de(SaveData(version=3, inventory_items={"coin": 1},
                                   inventory_equipped={"body": "armadura"}))
        assert limpio.get_equipped() == {}


class TestLaExperiencia:
    def test_viaja_entera_y_no_sólo_el_total(self, limpio) -> None:
        from src.engine.core.experience import ExperienceSystem

        exp = ExperienceSystem.get_instance()
        exp.grant(1000)
        gastados = exp.puntos
        assert exp.spend(1), "hacen falta puntos para que la prueba diga algo"

        data = SaveData()
        volcar_estado_en(data)
        exp.reset()
        aplicar_estado_de(data)

        assert ExperienceSystem.get_instance().exp == 1000
        assert ExperienceSystem.get_instance().puntos == gastados - 1, (
            "cargar la partida devolvió los puntos ya gastados: con ellos el "
            "árbol se compra dos veces"
        )

    def test_una_partida_v2_restaura_el_total_que_hay(self, limpio) -> None:
        from src.engine.core.experience import ExperienceSystem

        aplicar_estado_de(SaveData.from_dict({"version": 2, "exp_total": 400}))
        assert ExperienceSystem.get_instance().exp == 400


class TestElAutoguardado:
    def test_guarda_la_cartera_junto_con_la_posición(self, limpio, tmp_path) -> None:
        from src.engine.core.save_manager import SaveManager

        gestor = SaveManager()
        gestor.SAVES_DIR = tmp_path
        limpio.add_coins(12)
        gestor.auto_save(stage_id="stage0", stage_index=0, checkpoint_x=10.0,
                         checkpoint_y=20.0, health=4.0, max_health=5.0)
        guardada = gestor.load(gestor.newest_slot() or 1)
        assert guardada is not None
        assert guardada.inventory_items.get("coin") == 12
        assert guardada.checkpoint_x == 10.0

    def test_no_se_cae_si_el_inventario_falla(self, limpio, monkeypatch) -> None:
        """Guardar corre al llegar a un checkpoint. Perder la posición por no
        poder leer el inventario sería cambiar un dato importante por uno
        accesorio."""
        import src.engine.core.inventory as inv_mod

        def _revienta():
            raise RuntimeError("disco lleno")

        monkeypatch.setattr(inv_mod, "get_inventory", _revienta)
        data = SaveData()
        volcar_estado_en(data)
        assert data.score == 0
