"""AUD-295 — firma de los ficheros JSON que escribe el juego.

Lo primero, y va en la prueba para que no se olvide
---------------------------------------------------
**Esto no defiende de quien quiera alterar su tiempo de speedrun.** El *salt*
está en el código y el código lo leen las veintiséis personas de las que
teóricamente defendería. Cualquier esquema con la clave en el cliente tiene ese
techo.

Lo que sí hace, y es lo que se comprueba aquí:

* detecta un fichero **escrito a medias** —guardado interrumpido, disco malo—,
  que hoy se leía como datos válidos y cargaba una partida incompleta;
* detecta la **edición casual**, que es la que de verdad ocurre en un aula;
* **no rompe nada de lo que ya existe**: un fichero sin firma se acepta, porque
  rechazarlo sería borrarle la partida a todo el que actualice.
"""
from __future__ import annotations

import orjson
import pytest

from src.engine.core.integridad import (
    CAMPO_FIRMA,
    cargar,
    esta_firmado,
    firmar,
    verificar,
    volcar,
)


class TestFirmarYVerificar:
    def test_lo_firmado_verifica(self) -> None:
        assert verificar(firmar({"score": 100}))

    def test_cambiar_un_dato_lo_invalida(self) -> None:
        datos = firmar({"score": 100})
        datos["score"] = 999999
        assert not verificar(datos)

    def test_añadir_un_campo_lo_invalida(self) -> None:
        datos = firmar({"score": 100})
        datos["monedas"] = 9999
        assert not verificar(datos)

    def test_quitar_un_campo_lo_invalida(self) -> None:
        datos = firmar({"score": 100, "monedas": 5})
        del datos["monedas"]
        assert not verificar(datos)

    def test_una_firma_inventada_no_cuela(self) -> None:
        assert not verificar({"score": 100, CAMPO_FIRMA: "a" * 64})

    def test_el_orden_de_las_claves_no_importa(self) -> None:
        """Un verificador que falla la mitad de las veces enseña a ignorar el
        aviso, que es peor que no tenerlo."""
        uno = firmar({"a": 1, "b": 2})
        otro = firmar({"b": 2, "a": 1})
        assert uno[CAMPO_FIRMA] == otro[CAMPO_FIRMA]


class TestLoQueYaExistia:
    def test_un_fichero_sin_firma_se_acepta(self) -> None:
        """Rechazarlo sería borrarle la partida a todo el que actualice."""
        assert verificar({"score": 100})
        assert not esta_firmado({"score": 100})

    def test_y_se_distingue_del_firmado(self) -> None:
        assert esta_firmado(firmar({"score": 100}))


class TestCargar:
    def test_lee_lo_que_escribió(self) -> None:
        datos = cargar(volcar({"score": 100}))
        assert datos is not None
        assert datos["score"] == 100

    def test_un_json_roto_da_none(self) -> None:
        assert cargar(b'{"score": ') is None

    def test_un_fichero_editado_da_none(self) -> None:
        crudo = volcar({"score": 100})
        editado = crudo.replace(b'"score": 100', b'"score": 999')
        assert editado != crudo, "la prueba no llegó a editar nada"
        assert cargar(editado) is None

    def test_un_json_que_no_es_objeto_da_none(self) -> None:
        assert cargar(b"[1, 2, 3]") is None


class TestLaPartida:
    def test_se_guarda_firmada(self) -> None:
        from src.engine.core.save_data import SaveData

        crudo = SaveData(stage_id="stage0").to_json()
        assert esta_firmado(orjson.loads(crudo))

    def test_ida_y_vuelta(self) -> None:
        from src.engine.core.save_data import SaveData

        original = SaveData(stage_id="stage0", health=3.0, score=120)
        vuelta = SaveData.from_json(original.to_json())
        assert vuelta.stage_id == "stage0"
        assert vuelta.health == 3.0
        assert vuelta.score == 120

    def test_una_partida_editada_no_se_carga(self) -> None:
        from src.engine.core.save_data import SaveData

        crudo = SaveData(stage_id="stage0", score=10).to_json()
        editada = crudo.replace(b'"score":10', b'"score":99')
        with pytest.raises(ValueError, match="firma"):
            SaveData.from_json(editada)

    def test_una_partida_de_antes_de_la_firma_sí(self) -> None:
        from src.engine.core.save_data import SaveData

        vieja = orjson.dumps({"version": 2, "stage_id": "stage0", "health": 2.0})
        assert SaveData.from_json(vieja).stage_id == "stage0"

    def test_el_gestor_la_registra_y_no_revienta(self, tmp_path) -> None:
        """`load` ya sabía tratar una partida ilegible; una firma que no cuadra
        entra por el mismo camino."""
        from src.engine.core.save_data import SaveData
        from src.engine.core.save_manager import SaveManager

        gestor = SaveManager()
        gestor.SAVES_DIR = tmp_path
        gestor.save(1, SaveData(slot_id=1, stage_id="stage0", score=10))
        ruta = tmp_path / "slot_1.json"
        ruta.write_bytes(ruta.read_bytes().replace(b'"score":10', b'"score":99'))
        assert gestor.load(1) is None


class TestElLibroDeRecords:
    def test_se_escribe_firmado(self, tmp_path) -> None:
        from src.framework.stage.speedrun_mode import registrar_marca

        ruta = tmp_path / "speedrun.json"
        registrar_marca("stage0", 42.0, ruta)
        assert esta_firmado(orjson.loads(ruta.read_bytes()))

    def test_editarlo_a_mano_lo_descarta(self, tmp_path) -> None:
        """El caso real: abrir el fichero, poner 0.5 y volver a entrar."""
        from src.framework.stage.speedrun_mode import registrar_marca

        ruta = tmp_path / "speedrun.json"
        registrar_marca("stage0", 42.0, ruta)
        ruta.write_bytes(ruta.read_bytes().replace(b"42.0", b"0.5"))

        # Al volver a anotar, el libro editado se descarta y se empieza de
        # cero: la marca falsa no sobrevive.
        registrar_marca("stage1_1", 60.0, ruta)
        datos = orjson.loads(ruta.read_bytes())
        stages = {s["stage_id"] for s in datos["splits"]}
        assert stages == {"stage1_1"}

    def test_el_fantasma_sigue_cargando(self, tmp_path) -> None:
        """Se guarda como lista y una lista no tiene dónde llevar firma:
        pedírsela lo dejaría sin cargar nunca."""
        from src.framework.stage.speedrun_mode import GhostData

        ruta = tmp_path / "ghost.json"
        grabador = GhostData()
        grabador.record(10.0, 20.0, "idle")
        grabador.save(ruta)

        otro = GhostData()
        otro.load(ruta)
        assert otro.get_frame(0) is not None
