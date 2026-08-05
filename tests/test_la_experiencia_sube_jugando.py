"""AUD-267 — la experiencia existía, no subía y no se guardaba.

El defecto
==========
AUD-249 construyó `ExperienceSystem` entero: tabla de experiencia derivada de
`_tipo_de()`, curva cuadrática de nivel, puntos de habilidad al subir. Y lo
dejó **sin enlazar**: medido con `grep -rn "ExperienceSystem" src/` excluyendo
su propio módulo, **cero resultados**. Nadie lo construía, así que:

* matar enemigos no daba experiencia — el manejador de `ENEMY_DIED` que el
  sistema trae no llegaba a suscribirse nunca;
* `SaveData` no tiene campo de experiencia, así que aunque subiera, cerrar el
  juego la borraba.

Es el mismo modo de fallo del resto de la sesión —la cadena escrita y
desconectada por arriba— con un agravante: es la **moneda** con la que AUD-249
decidió que se paga el árbol de habilidades. Un árbol sobre una moneda que no
se acuña no se puede ni empezar a diseñar.

Lo que **no** entra aquí: el árbol. Qué habilidades hay, qué cuestan y qué
hacen es diseño del curso, no cableado. Lo que esto garantiza es que el día que
se decida, la moneda existe, sube sola jugando y sobrevive a cerrar el juego.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.events import Events
from src.engine.core.experience import ExperienceSystem


@pytest.fixture(autouse=True)
def _sistema_limpio():
    ExperienceSystem._reset_instance()
    yield
    ExperienceSystem._reset_instance()


class TestSubeAlMatar:
    def test_un_enemigo_muerto_da_experiencia(self, event_bus) -> None:
        sistema = ExperienceSystem.get_instance()
        sistema.bind_bus(event_bus)
        antes = sistema.exp

        event_bus.emit(Events.ENEMY_DIED, entity_id="EnemyWalker_1",
                       position=(0.0, 0.0))
        event_bus.dispatch()

        assert sistema.exp > antes

    def test_un_jefe_da_mas_que_un_bicho(self, event_bus) -> None:
        from src.engine.core.experience import exp_for

        assert exp_for("BossVenado_1") > exp_for("EnemyWalker_1")


class TestLaEscenaLoEnlaza:
    """La comprobación que lo habría evitado: alguien tiene que construirlo."""

    def test_alguien_construye_el_sistema_en_produccion(self) -> None:
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[1] / "src"
        usos = [
            p.name for p in raiz.rglob("*.py")
            if p.name != "experience.py"
            and "ExperienceSystem" in p.read_text(encoding="utf-8")
        ]
        assert usos, (
            "ExperienceSystem no lo construye nadie: la experiencia no sube "
            "jugando, que es exactamente lo que AUD-249 dejó a medias"
        )


class TestSobreviveAlGuardado:
    def test_save_data_tiene_campo_de_experiencia(self) -> None:
        from src.engine.core.save_data import SaveData

        assert "exp_total" in SaveData().model_dump()

    def test_ida_y_vuelta_por_json(self, tmp_path) -> None:
        from src.engine.core.save_data import SaveData
        from src.engine.core.save_manager import SaveManager

        sm = SaveManager()
        sm.SAVES_DIR = tmp_path / "saves"
        sm.SAVES_DIR.mkdir(parents=True, exist_ok=True)
        sm.save(1, SaveData(slot_id=1, exp_total=450))

        recuperada = sm.load(1)

        assert recuperada is not None
        assert recuperada.exp_total == 450

    def test_una_partida_vieja_sin_el_campo_se_carga(self, tmp_path) -> None:
        """Las partidas grabadas antes de AUD-267 no pueden romperse."""
        import json

        from src.engine.core.save_manager import SaveManager

        sm = SaveManager()
        sm.SAVES_DIR = tmp_path / "saves"
        sm.SAVES_DIR.mkdir(parents=True, exist_ok=True)
        (sm.SAVES_DIR / "slot_1.json").write_text(
            json.dumps({"slot_id": 1, "stage_id": "stage0", "health": 5.0}),
            encoding="utf-8")

        recuperada = sm.load(1)

        assert recuperada is not None
        assert recuperada.exp_total == 0

    def test_el_autoguardado_se_lleva_la_experiencia(self, tmp_path, event_bus) -> None:
        from src.engine.core.save_manager import SaveManager

        sm = SaveManager()
        sm.SAVES_DIR = tmp_path / "saves"
        sm.SAVES_DIR.mkdir(parents=True, exist_ok=True)
        sistema = ExperienceSystem.get_instance()
        sistema.bind_bus(event_bus)
        sistema.grant(300)

        sm.auto_save(stage_id="stage0", stage_index=0, checkpoint_x=0.0,
                     checkpoint_y=0.0, health=5.0, max_health=5.0,
                     exp_total=sistema.exp)

        assert sm.load(sm.newest_slot() or 1).exp_total == 300


class TestElArbolTodaviaNoExiste:
    """Se deja escrito, porque es lo que la lista de QA preguntaba.

    AUD-249 decidió el reparto —las monedas compran lo que se consume o se
    equipa, la experiencia compra lo permanente— y construyó la moneda. El
    árbol en sí **no existe**: no hay clase, ni escena, ni forma de gastar los
    puntos. Esta prueba lo fija para que nadie lo dé por hecho al leer que hay
    `puntos`.
    """

    def test_los_puntos_todavia_no_se_pueden_gastar(self) -> None:
        sistema = ExperienceSystem.get_instance()

        assert not hasattr(sistema, "gastar"), (
            "si esto falla, alguien construyó el árbol: actualiza docs/76 y "
            "la lista de QA en el mismo cambio"
        )
