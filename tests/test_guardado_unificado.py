"""AUD-337 — el estado del jugador, en el directorio del usuario.

`score.json` e `inventory.json` nacieron dentro de `data/`, en el árbol
del proyecto — el mismo defecto que AUD-157 arregló para las partidas:
una instalación empaquetada puede tener el árbol en un sitio de sólo
lectura. Ahora viven en el directorio del usuario y el fichero viejo se
migra una vez (copia, sin borrar, sin sobreescribir).

Lo que estas pruebas fijan, en hechos:
- las rutas por defecto están fuera del árbol del proyecto;
- el fichero viejo se migra una vez al cargar/guardar con la ruta real;
- un destino que ya existe no se pisa;
- una ruta parcheada (una prueba) no dispara la migración del fichero
  viejo del repositorio.
"""
from __future__ import annotations

import orjson

from src.engine.core import inventory as inv
from src.engine.core import score_system as score_mod
from src.engine.core.save_manager import migrar_desde_el_arbol
from src.engine.core.user_settings import user_data_dir


def _fichas_vieja(nueva, antigua, contenido: bytes) -> None:
    antigua.parent.mkdir(parents=True, exist_ok=True)
    antigua.write_bytes(contenido)
    if nueva.exists():
        nueva.unlink()


class TestLasRutasPorDefecto:
    def test_score_vive_fuera_del_arbol_del_proyecto(self) -> None:
        assert score_mod._SCORE_PATH == user_data_dir() / "score.json"

    def test_inventario_vive_fuera_del_arbol_del_proyecto(self) -> None:
        assert inv._INVENTORY_PATH == user_data_dir() / "inventory.json"


class TestLaMigracion:
    def test_el_fichero_viejo_se_copia_una_vez(self, tmp_path) -> None:
        viejo = tmp_path / "score.json"
        viejo.write_bytes(orjson.dumps({"score": 42}))
        nuevo = tmp_path / "nuevo" / "score.json"
        migrar_desde_el_arbol(nuevo, viejo)
        assert nuevo.exists()
        assert int(orjson.loads(nuevo.read_bytes())["score"]) == 42
        # el origen no se borra: volver a una versión anterior no pierde nada
        assert viejo.exists()

    def test_el_destino_existente_manda(self, tmp_path) -> None:
        viejo = tmp_path / "score.json"
        viejo.write_bytes(orjson.dumps({"score": 42}))
        nuevo = tmp_path / "score.json"
        nuevo.write_bytes(orjson.dumps({"score": 7}))
        migrar_desde_el_arbol(nuevo, viejo)
        assert int(orjson.loads(nuevo.read_bytes())["score"]) == 7

    def test_score_carga_migrando_desde_el_arbol(self, tmp_path, monkeypatch) -> None:
        viejo = tmp_path / "score.json"
        nuevo = tmp_path / "nuevo" / "score.json"
        _fichas_vieja(nuevo, viejo, orjson.dumps({"score": 9}))
        monkeypatch.setattr(score_mod, "_SCORE_PATH", nuevo)
        monkeypatch.setattr(score_mod, "_RUTA_POR_DEFECTO", nuevo)
        monkeypatch.setattr(score_mod, "_RUTA_ANTIGUA", viejo)
        sistema = score_mod.ScoreSystem()
        sistema.load()
        assert sistema.score == 9
        assert nuevo.exists()

    def test_inventario_carga_migrando_desde_el_arbol(self, tmp_path, monkeypatch) -> None:
        viejo = tmp_path / "inventory.json"
        nuevo = tmp_path / "nuevo" / "inventory.json"
        _fichas_vieja(
            nuevo, viejo,
            orjson.dumps({"items": {"coin": 5}, "equipped": {}}),
        )
        monkeypatch.setattr(inv, "_INVENTORY_PATH", nuevo)
        monkeypatch.setattr(inv, "_RUTA_POR_DEFECTO", nuevo)
        monkeypatch.setattr(inv, "_RUTA_ANTIGUA", viejo)
        inventario = inv.get_inventory()
        # El inventario es singleton (AUD-221): una prueba anterior de la suite
        # ya lo inicializó con otra ruta, y `__init__` no recarga. `load()` sí.
        inventario.load()
        assert inventario.count("coin") == 5
        assert nuevo.exists()

    def test_la_ruta_parcheada_no_migra_nada(self, tmp_path, monkeypatch) -> None:
        """Una prueba redirige la ruta: el fichero viejo no se cuela.

        La prueba parchea `_SCORE_PATH` y deja `_RUTA_POR_DEFECTO` como
        estaba: las dos ya no coinciden, y la migración se salta.
        """
        viejo = tmp_path / "score.json"
        viejo.write_bytes(orjson.dumps({"score": 99}))
        parcheada = tmp_path / "otra" / "score.json"
        monkeypatch.setattr(score_mod, "_SCORE_PATH", parcheada)
        sistema = score_mod.ScoreSystem()
        sistema.load()
        assert sistema.score == 0
        assert not parcheada.exists()
