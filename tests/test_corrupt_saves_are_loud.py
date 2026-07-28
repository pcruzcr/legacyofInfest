"""
Un fichero de datos corrupto no tumba el juego, pero tampoco desaparece en silencio.

AUD-100
=======
Tres cargas del proyecto —bestiario, logros e inventario— tenían la misma
forma::

    except (FileNotFoundError, orjson.JSONEncodeError, ValueError):
        pass

Dos problemas distintos escondidos en dos líneas:

1. **La tupla mentía.** `orjson.JSONEncodeError` *es* `TypeError`, y codificar
   no puede fallar dentro de un `loads`. Lo que de verdad atrapaba un fichero
   corrupto era `ValueError`, del que `orjson.JSONDecodeError` hereda. El
   bloque funcionaba, pero por una razón distinta de la que aparentaba: quien
   viniera a «simplificar» esa tupla tenía todas las papeletas de quitar lo
   que hacía el trabajo y dejar lo que no hacía nada.

2. **El `pass`.** Las bajas de un semestre, los logros o los objetos
   recogidos desaparecían sin una línea en el registro. El estudiante veía un
   bestiario vacío y no tenía forma de saber si había perdido los datos o si
   nunca los había tenido.

`ProgresoAcademico.cargar` ya avisaba ante exactamente el mismo problema. Que
el mismo proyecto tratara la misma situación de dos maneras opuestas es lo
que convierte esto en un defecto y no en una preferencia.

Qué se exige aquí
-----------------
Las dos mitades: que **no se caiga** (perder unas notas es malo; que treinta
portátiles no arranquen el día de la entrega, peor) y que **deje rastro**.
"""
from __future__ import annotations

import logging

import pytest

#: Basura que no es JSON válido por ninguna vía.
BASURA = "{esto no es json, ni pretende serlo"


@pytest.fixture(autouse=True)
def _pygame():
    import pygame

    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((64, 64))


class TestElBestiario:
    def test_un_fichero_corrupto_avisa_y_no_lanza(self, tmp_path, caplog):
        from src.framework.entities.bestiary import Bestiary

        roto = tmp_path / "bestiary.json"
        roto.write_text(BASURA, encoding="utf-8")

        with caplog.at_level(logging.WARNING):
            Bestiary.get_instance().load(roto)

        assert any("ilegible" in r.message for r in caplog.records), (
            "el bestiario se comió un fichero corrupto sin decir nada"
        )

    def test_el_aviso_nombra_la_ruta_que_fallo(self, tmp_path, caplog):
        """No la ruta por defecto, que es la que se nombraba antes."""
        from src.framework.entities.bestiary import Bestiary

        roto = tmp_path / "otro_sitio.json"
        roto.write_text(BASURA, encoding="utf-8")

        with caplog.at_level(logging.WARNING):
            Bestiary.get_instance().load(roto)

        assert any("otro_sitio.json" in str(r.args) or "otro_sitio.json" in r.getMessage()
                   for r in caplog.records), (
            "el aviso no dice cuál de los ficheros falló"
        )

    def test_sin_fichero_no_hay_aviso_de_alarma(self, tmp_path, caplog):
        """Que no exista todavía es normal, no un problema."""
        from src.framework.entities.bestiary import Bestiary

        with caplog.at_level(logging.WARNING):
            Bestiary.get_instance().load(tmp_path / "no_existe.json")

        assert not [r for r in caplog.records if r.levelno >= logging.WARNING], (
            "un arranque limpio no puede parecer un error"
        )


class TestLosLogros:
    def test_un_fichero_corrupto_avisa_y_no_lanza(self, tmp_path, caplog, monkeypatch):
        from src.engine.core import achievements

        roto = tmp_path / "achievements.json"
        roto.write_text(BASURA, encoding="utf-8")
        monkeypatch.setattr(achievements, "ACHIEVEMENTS_PATH", roto)

        sistema = achievements.AchievementSystem.get_instance()
        with caplog.at_level(logging.WARNING):
            sistema.load()

        assert any("ilegible" in r.message for r in caplog.records)
        # Y sigue utilizable: las definiciones no dependen del fichero.
        assert sistema.get_all_achievements()


class TestElInventario:
    def test_un_fichero_corrupto_avisa_y_deja_el_inventario_vacio(
        self, tmp_path, caplog, monkeypatch,
    ):
        from src.engine.core import inventory

        roto = tmp_path / "inventory.json"
        roto.write_text(BASURA, encoding="utf-8")
        monkeypatch.setattr(inventory, "_INVENTORY_PATH", roto)

        inv = inventory.Inventory()
        with caplog.at_level(logging.WARNING):
            inv.load()

        assert any("ilegible" in r.message for r in caplog.records)
        assert inv._items == {}


class TestLaTuplaDeExcepcionesYaNoMiente:
    def test_ningun_cargador_captura_un_error_de_codificacion(self):
        """`orjson.JSONEncodeError` en un `loads` no puede saltar nunca.

        Se comprueba sobre el texto de los tres módulos porque lo que importa
        es que nadie vuelva a escribirlo: es la clase de línea que se copia de
        un fichero a otro sin releerla.
        """
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent
        sospechosos = [
            "src/framework/entities/bestiary.py",
            "src/engine/core/achievements.py",
            "src/engine/core/inventory.py",
        ]
        for relativo in sospechosos:
            texto = (raiz / relativo).read_text(encoding="utf-8")
            for numero, linea in enumerate(texto.splitlines(), 1):
                if linea.lstrip().startswith(("#", "*")):
                    continue
                assert not (linea.lstrip().startswith("except")
                            and "JSONEncodeError" in linea), (
                    f"{relativo}:{numero} vuelve a capturar un error de "
                    f"codificación en una ruta de lectura"
                )

    def test_orjson_decodifica_lanzando_un_valueerror(self):
        """La premisa del arreglo, comprobada y no supuesta."""
        import orjson

        assert issubclass(orjson.JSONDecodeError, ValueError)
        assert orjson.JSONEncodeError is TypeError
        with pytest.raises(ValueError):
            orjson.loads(BASURA.encode("utf-8"))
