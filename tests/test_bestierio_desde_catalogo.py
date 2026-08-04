"""
El bestiario clásico vive en `data/bestiary.json` y el motor lo lee de ahí.

AUD-199 — los textos (nombre, descripción, lore) estaban escritos a mano en
`bestiary.py`. Al pasarlos a un catálogo, hay que garantizar que el motor y
el fichero sigan diciendo lo mismo y que un fichero descuidado no tumbe el
juego.
"""
from __future__ import annotations

from pathlib import Path

import orjson

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "data" / "bestiary.json"

#: Los nueve arquetipos clásicos que el motor espera encontrar.
CLASICOS = {
    "walker", "flying", "shooter", "charger", "archer",
    "brute", "caster", "assassin", "boss_venado",
}


def _fichas() -> list[dict]:
    datos = orjson.loads(CATALOGO.read_bytes())
    return datos["species"]


class TestElCatalogo:
    def test_existe_y_es_json_valido(self) -> None:
        assert CATALOGO.exists()
        orjson.loads(CATALOGO.read_bytes())

    def test_los_ids_son_unicos(self) -> None:
        ids = [e["id"] for e in _fichas()]
        assert len(ids) == len(set(ids))

    def test_los_arquetipos_clasicos_estan(self) -> None:
        ids = {e["id"] for e in _fichas()}
        assert CLASICOS - ids == set(), f"faltan del catálogo: {sorted(CLASICOS - ids)}"


class TestElMotorLeeElCatalogo:
    def test_las_fichas_del_json_son_las_del_motor(self) -> None:
        from src.framework.entities.bestiary import Bestiary

        bestiario = Bestiary()
        for ficha in _fichas():
            entrada = bestiario.get_entry(ficha["id"])
            assert entrada is not None, f"«{ficha['id']}» no llegó al bestiario"
            assert entrada.name == ficha["name"]
            assert entrada.description == ficha["description"]
            assert entrada.lore == ficha["lore"]
            assert entrada.hp == ficha["hp"]
            assert entrada.damage == ficha["damage"]

    def test_las_especies_del_registro_siguen_dentro(self) -> None:
        from src.framework.entities import bestiary_registry
        from src.framework.entities.bestiary import Bestiary

        bestiario = Bestiary()
        ids = {e.enemy_id for e in bestiario.get_all_entries()}
        assert bestiary_registry.SPECIES.keys() <= ids, (
            "las especies de bestiary_registry dejaron de entrar al bestiario"
        )

    def test_sin_catalogo_no_tumba_el_juego(self, tmp_path, monkeypatch) -> None:
        import src.framework.entities.bestiary as modulo
        from src.framework.entities import bestiary_registry

        monkeypatch.setattr(modulo, "_DATOS_BESTIARIO", tmp_path / "no_existe.json")
        bestiario = modulo.Bestiary()
        ids = {e.enemy_id for e in bestiario.get_all_entries()}
        assert bestiary_registry.SPECIES.keys() <= ids, (
            "sin catálogo, las especies del registro siguen teniendo que existir"
        )

    def test_una_ficha_con_estadisticas_raras_se_omite(self, tmp_path, monkeypatch) -> None:
        import src.framework.entities.bestiary as modulo

        cuidado = {
            "species": [
                {"id": "sana", "name": "Sana", "description": "ok",
                 "lore": "", "hp": 2, "damage": 0.5},
                {"id": "rota", "name": "Rota", "description": "ok",
                 "hp": "muchisima", "damage": "tambien"},
            ],
        }
        fichero = tmp_path / "bestiary.json"
        fichero.write_bytes(orjson.dumps(cuidado))
        monkeypatch.setattr(modulo, "_DATOS_BESTIARIO", fichero)

        bestiario = modulo.Bestiary()
        assert bestiario.get_entry("sana") is not None
        assert bestiario.get_entry("rota") is None