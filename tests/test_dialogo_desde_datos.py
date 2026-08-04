"""AUD-244 — un mapa podía pedir una conversación y no pasaba nada.

`StageLoader` lee `dialogue_tree_id` de los `MessageTrigger` desde AUD-127.
Hasta ahora el único sitio que consumía esos disparadores —`HazardSystem`—
emitía siempre `SHOW_MESSAGE` con el texto plano y **no miraba ese campo**. De
los diecisiete mapas, sólo `stage0` tenía conversaciones, y porque se las
construye a mano en Python dentro de su propia clase.

Es la misma forma de fallo que AUD-127, un nivel más arriba: el campo se lee, se
guarda, y quien tenía que actuar sobre él no existe. Declarar un árbol en Tiled
no producía ni diálogo ni aviso.

Y arrastraba a un segundo huérfano: `DialogueTree.desde_datos`, escrita en
AUD-127 para que un diseñador que no programa pudiera escribir un diálogo como
fichero de datos. Nadie la llamaba, así que la única forma de tener conversación
seguía siendo escribirla en el código — justo lo que aquella corrección quería
evitar.
"""
from __future__ import annotations

import json

import pytest

from src.engine.core.events import Events


@pytest.fixture
def bus():
    from src.engine.core.event_bus import EventBus
    return EventBus()


class TestElDisparadorPideLaConversacion:
    def test_el_evento_existe_en_el_catalogo(self) -> None:
        """Sin esto, `Events.SHOW_DIALOGUE` sería un AttributeError en runtime."""
        assert Events.SHOW_DIALOGUE == "SHOW_DIALOGUE"

    def test_el_sistema_de_riesgos_mira_el_arbol_antes_que_el_texto(self) -> None:
        """El cableado, por AST: ignorar el campo era exactamente el defecto."""
        import ast
        import pathlib

        ruta = (pathlib.Path(__file__).resolve().parent.parent
                / "src" / "framework" / "stage" / "hazard_system.py")
        fuente = ruta.read_text(encoding="utf-8")
        ast.parse(fuente)
        assert "dialogue_tree_id" in fuente, (
            "hazard_system vuelve a ignorar `dialogue_tree_id`: un mapa que "
            "declare una conversación no obtendrá nada, y tampoco un aviso"
        )
        assert "SHOW_DIALOGUE" in fuente


class TestElArbolSaleDeUnFicheroDeDatos:
    def test_desde_datos_construye_el_arbol_que_describe_el_json(self) -> None:
        from src.framework.ui.dialogue_system import DialogueTree

        arbol = DialogueTree.desde_datos({
            "id": "aviso_del_pozo",
            "start": "inicio",
            "nodes": {"inicio": {"speaker": "Cegua", "text": "No bajes."}},
        })
        assert arbol.tree_id == "aviso_del_pozo"
        assert arbol.start_node == "inicio"
        assert "inicio" in arbol.nodes

    def test_la_escena_carga_los_arboles_del_escenario(
        self, tmp_path, monkeypatch,
    ) -> None:
        """El cargador que faltaba, medido de punta a punta."""
        from src.engine.core import settings
        from src.framework.scenes.stage_scene import StageScene

        destino = tmp_path / "data" / "dialogues"
        destino.mkdir(parents=True)
        (destino / "stage_de_prueba.json").write_text(json.dumps({
            "id": "aviso", "start": "a",
            "nodes": {"a": {"speaker": "X", "text": "hola"}},
        }), encoding="utf-8")
        monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)

        escena = StageScene.__new__(StageScene)
        escena._stage_data = type("D", (), {"stage_id": "stage_de_prueba"})()
        escena._arboles_de_dialogo = {}
        escena._cargar_los_arboles_de_dialogo()

        assert "aviso" in escena._arboles_de_dialogo

    def test_un_escenario_sin_fichero_no_es_un_error(
        self, tmp_path, monkeypatch,
    ) -> None:
        """La inmensa mayoría de los escenarios no habla."""
        from src.engine.core import settings
        from src.framework.scenes.stage_scene import StageScene

        monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)
        escena = StageScene.__new__(StageScene)
        escena._stage_data = type("D", (), {"stage_id": "mudo"})()
        escena._arboles_de_dialogo = {}
        escena._cargar_los_arboles_de_dialogo()
        assert escena._arboles_de_dialogo == {}

    def test_un_json_roto_no_deja_al_estudiante_sin_nivel(
        self, tmp_path, monkeypatch,
    ) -> None:
        from src.engine.core import settings
        from src.framework.scenes.stage_scene import StageScene

        destino = tmp_path / "data" / "dialogues"
        destino.mkdir(parents=True)
        (destino / "roto.json").write_text("{esto no es JSON", encoding="utf-8")
        monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)

        escena = StageScene.__new__(StageScene)
        escena._stage_data = type("D", (), {"stage_id": "roto"})()
        escena._arboles_de_dialogo = {}
        escena._cargar_los_arboles_de_dialogo()   # no lanza
        assert escena._arboles_de_dialogo == {}

    def test_un_fichero_puede_traer_varias_conversaciones(
        self, tmp_path, monkeypatch,
    ) -> None:
        """Un escenario con tres avisos no debería necesitar tres ficheros."""
        from src.engine.core import settings
        from src.framework.scenes.stage_scene import StageScene

        destino = tmp_path / "data" / "dialogues"
        destino.mkdir(parents=True)
        (destino / "varios.json").write_text(json.dumps([
            {"id": "uno", "start": "a", "nodes": {"a": {"text": "1"}}},
            {"id": "dos", "start": "a", "nodes": {"a": {"text": "2"}}},
        ]), encoding="utf-8")
        monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)

        escena = StageScene.__new__(StageScene)
        escena._stage_data = type("D", (), {"stage_id": "varios"})()
        escena._arboles_de_dialogo = {}
        escena._cargar_los_arboles_de_dialogo()
        assert set(escena._arboles_de_dialogo) == {"uno", "dos"}
