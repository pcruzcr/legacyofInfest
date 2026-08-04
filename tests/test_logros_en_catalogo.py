"""
Los logros viven en `data/achievements.json` y el motor los lee de ahí.

AUD-197 — las definiciones (nombre, descripción, objetivo, si es secreto)
estaban escritas a mano en `achievements.py`. Un texto que vive en el código
no se puede validar en CI ni editar sin tocar el motor. Ahora es un catálogo,
y estas pruebas fijan que el motor diga lo mismo que el fichero.
"""
from __future__ import annotations

from pathlib import Path

import orjson

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "data" / "achievements.json"

#: Logros que src/engine/core/achievements.py referencia por id. Si uno falta
#: en el catálogo, existe para el jugador pero nunca se puede desbloquear.
REQUERIDOS = {
    "first_blood", "exterminator", "untouchable", "parry_master",
    "air_assault", "speed_demon", "collector", "survivor",
    "combo_king", "explorer",
}


def _entradas() -> list[dict]:
    datos = orjson.loads(CATALOGO.read_bytes())
    return datos["achievements"]


class TestElCatalogo:
    def test_existe_y_es_json_valido(self) -> None:
        assert CATALOGO.exists()
        orjson.loads(CATALOGO.read_bytes())

    def test_los_ids_son_unicos(self) -> None:
        ids = [e["id"] for e in _entradas()]
        assert len(ids) == len(set(ids))

    def test_cubre_los_logros_que_el_motor_referencia(self) -> None:
        ids = {e["id"] for e in _entradas()}
        assert REQUERIDOS - ids == set(), (
            f"faltan del catálogo: {sorted(REQUERIDOS - ids)}"
        )

    def test_hay_medallas_secretas_y_visibles(self) -> None:
        ocultas = [e for e in _entradas() if e.get("hidden")]
        visibles = [e for e in _entradas() if not e.get("hidden")]
        assert ocultas, "el catálogo no define ninguna medalla secreta"
        assert visibles, "el catálogo no define ninguna medalla visible"


class TestElMotorLeeElCatalogo:
    def test_lo_que_lista_el_motor_es_lo_que_dice_el_catalogo(self) -> None:
        from src.engine.core.achievements import AchievementSystem

        sistema = AchievementSystem()
        ids = {definicion.id for definicion, _ in sistema.achievements}
        assert ids == {e["id"] for e in _entradas()}

    def test_un_catalogo_invalido_no_tumba_el_juego(self, tmp_path, monkeypatch) -> None:
        import src.engine.core.achievements as modulo

        roto = tmp_path / "achievements.json"
        roto.write_text("{no es json", encoding="utf-8")
        monkeypatch.setattr(modulo, "DEFINICIONES_PATH", roto)

        sistema = modulo.AchievementSystem()
        assert sistema.get_all_achievements() == []

    def test_una_entrada_invalida_no_hunde_a_las_demas(self, tmp_path, monkeypatch) -> None:
        import src.engine.core.achievements as modulo

        catalogo = {
            "achievements": [
                {"id": "bueno", "name": "Bueno", "description": "va bien", "target": 1},
                {"id": 7},  # id con tipo incorrecto: pydantic la rechaza
            ],
        }
        fichero = tmp_path / "achievements.json"
        fichero.write_bytes(orjson.dumps(catalogo))
        monkeypatch.setattr(modulo, "DEFINICIONES_PATH", fichero)

        sistema = modulo.AchievementSystem()
        assert {d.id for d, _ in sistema.get_all_achievements()} == {"bueno"}

    def test_el_target_del_explorador_sale_del_catalogo(self) -> None:
        """El umbral de «explorer» no puede divergir de lo que muestra la UI."""
        from src.engine.core.achievements import AchievementSystem

        sistema = AchievementSystem()
        objetivo = {
            d.id: d.target
            for d, _ in sistema.get_all_achievements()
        }
        datos = {e["id"]: e["target"] for e in _entradas()}
        assert objetivo == datos


class TestMedallasSecretas:
    def test_una_secreta_bloqueada_no_se_muestra(self) -> None:
        from src.engine.core.achievements import (
            AchievementDef,
            AchievementProgress,
            esta_oculta,
        )

        secreta = AchievementDef(id="s", name="S", description="", hidden=True)
        normal = AchievementDef(id="n", name="N", description="")
        assert esta_oculta(secreta, AchievementProgress())
        assert not esta_oculta(normal, AchievementProgress())

    def test_desbloqueada_deja_de_ser_secreta(self) -> None:
        from src.engine.core.achievements import (
            AchievementDef,
            AchievementProgress,
            esta_oculta,
        )

        secreta = AchievementDef(id="s", name="S", description="", hidden=True)
        progreso = AchievementProgress()
        progreso.unlocked = True
        assert not esta_oculta(secreta, progreso)