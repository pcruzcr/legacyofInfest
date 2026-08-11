"""AUD-393 — versión de esquema en el TMX. Cierra la mitad viva de GAP-048.

Qué pedía el hueco
==================
`GAP-048` son dos cosas con un mismo título, y su propio plan de resolución las
separa: *«el versionado sí conviene y es barato […]. El streaming no, hasta que
un mapa no quepa»*. Esto es el versionado.

El problema concreto que resuelve: hoy un TMX escrito para una versión distinta
del motor —una propiedad renombrada, un tipo de objeto que cambió de
significado— **falla como dato malo**. El mensaje habla de una capa que falta o
de un tipo que no existe, y quien lo lee busca el error en su mapa en vez de en
la distancia entre su mapa y este motor.

Las reglas, y por qué son asimétricas
=====================================
Decisión del dueño (2026-08-11):

* **Falta la propiedad** → aviso del validador, con el texto exacto que hay que
  añadir. No es un error porque hay entregas de estudiantes ya hechas y ningún
  TMX anterior a este lote la declara; suspenderlas a todas por una propiedad
  inventada hoy sería AUD-106 otra vez.
* **Declara una versión mayor que la del motor** → error, y al cargar también.
  Ese mapa usa cosas que este motor no entiende, y cargarlo a medias produce
  comportamiento incorrecto en silencio, que es peor que no abrirlo.
* **No es un número** → aviso y se sigue. Es dato malo, no incompatibilidad.

La validación de versión va **antes** que la de capas en `load()`, a propósito:
si el mapa es de otra época, «falta la capa Collision» es un diagnóstico
engañoso — la capa no falta, se llama de otra manera en esa versión.
"""
from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pygame
import pytest

from src.framework import FrameworkUsageError
from src.framework.stage.stage_loader import SCHEMA_VERSION, StageLoader

_RAIZ = Path(__file__).resolve().parent.parent
STAGE0 = _RAIZ / "assets" / "maps" / "stage0" / "stage0.tmx"


def _init_pygame_display() -> None:
    """Mismo arranque que `test_stage0_smoke`: pytmx llama a `Surface.convert`
    al cargar los tilesets y eso exige un display inicializado."""
    if not pygame.display.get_init():
        pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))


@pytest.fixture
def stage0_con_esquema():
    """Deja declarar la versión de esquema de stage0 sin tocar el disco.

    `_parse_tmx` cachea por ruta, así que se muta el objeto cacheado y se
    restaura después vaciando la caché — si no, la mutación se filtra a las
    demás pruebas de la sesión, que cargan stage0 constantemente.
    """
    _init_pygame_display()
    puestas: list[str] = []

    def poner(valor: str | None) -> None:
        datos = StageLoader._parse_tmx(STAGE0)
        if valor is None:
            datos.properties.pop("schema_version", None)
        else:
            datos.properties["schema_version"] = valor
        puestas.append("x")

    yield poner

    if puestas:
        StageLoader.clear_tmx_cache()


class TestElCargador:
    def test_un_mapa_de_esquema_futuro_no_se_carga(self, stage0_con_esquema) -> None:
        """El caso que da nombre al hueco."""
        stage0_con_esquema(str(SCHEMA_VERSION + 1))
        with pytest.raises(FrameworkUsageError) as exc:
            StageLoader.load(STAGE0)
        mensaje = str(exc.value)
        assert str(SCHEMA_VERSION + 1) in mensaje and str(SCHEMA_VERSION) in mensaje, (
            "el error tiene que decir las dos versiones —la del mapa y la del "
            f"motor— para que se entienda de qué va: {mensaje!r}"
        )

    def test_el_esquema_actual_carga_con_normalidad(self, stage0_con_esquema) -> None:
        """Sin esto, «rechaza siempre» pasaría la prueba de arriba."""
        stage0_con_esquema(str(SCHEMA_VERSION))
        assert StageLoader.load(STAGE0) is not None

    def test_un_mapa_sin_la_propiedad_sigue_cargando(self, stage0_con_esquema) -> None:
        """Las entregas de estudiantes no declaran ninguna. Se asume la 1."""
        stage0_con_esquema(None)
        assert StageLoader.load(STAGE0) is not None

    def test_un_valor_que_no_es_numero_no_impide_cargar(
        self, stage0_con_esquema, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Dato malo, no incompatibilidad: avisa y sigue."""
        stage0_con_esquema("dos")
        assert StageLoader.load(STAGE0) is not None
        assert any("schema_version" in r.getMessage() for r in caplog.records), (
            "un valor no numérico tiene que dejar rastro en el log"
        )


class TestElValidador:
    def _avisos(self, ruta: Path) -> list[str]:
        from scripts import validate_tmx as v

        v.validate_tmx(ruta)
        return list(v._warnings)

    def _errores(self, ruta: Path) -> list[str]:
        from scripts import validate_tmx as v

        v.validate_tmx(ruta)
        return list(v._errors)

    def _copia_con(self, tmp_path: Path, valor: str | None) -> Path:
        destino = tmp_path / "mapa.tmx"
        shutil.copy(STAGE0, destino)
        arbol = ET.parse(destino)
        props = arbol.getroot().find("properties")
        assert props is not None
        for p in list(props.findall("property")):
            if p.get("name") == "schema_version":
                props.remove(p)
        if valor is not None:
            ET.SubElement(props, "property",
                          {"name": "schema_version", "value": valor})
        arbol.write(destino, encoding="utf-8", xml_declaration=True)
        return destino

    def test_avisa_cuando_falta(self, tmp_path: Path) -> None:
        avisos = [a for a in self._avisos(self._copia_con(tmp_path, None))
                  if "schema_version" in a]
        assert avisos, "un mapa sin schema_version tiene que avisar"

    def test_el_aviso_dice_que_hay_que_escribir(self, tmp_path: Path) -> None:
        """Un aviso que no dice cómo arreglarlo cuesta una búsqueda por el repo."""
        avisos = [a for a in self._avisos(self._copia_con(tmp_path, None))
                  if "schema_version" in a]
        assert any(str(SCHEMA_VERSION) in a for a in avisos), (
            f"el aviso no dice qué valor poner: {avisos}"
        )

    def test_falta_no_es_error(self, tmp_path: Path) -> None:
        """La decisión del dueño: no suspende a las entregas ya hechas."""
        errores = [e for e in self._errores(self._copia_con(tmp_path, None))
                   if "schema_version" in e]
        assert not errores

    def test_una_version_futura_si_es_error(self, tmp_path: Path) -> None:
        ruta = self._copia_con(tmp_path, str(SCHEMA_VERSION + 1))
        assert [e for e in self._errores(ruta) if "schema_version" in e]

    def test_un_valor_no_numerico_es_error(self, tmp_path: Path) -> None:
        """En el validador sí suspende: es el sitio donde se arreglan los mapas."""
        ruta = self._copia_con(tmp_path, "dos")
        assert [e for e in self._errores(ruta) if "schema_version" in e]

    def test_la_version_actual_pasa_limpia(self, tmp_path: Path) -> None:
        ruta = self._copia_con(tmp_path, str(SCHEMA_VERSION))
        assert not [e for e in self._errores(ruta) if "schema_version" in e]


def test_todos_los_mapas_del_motor_declaran_su_esquema() -> None:
    """El cable trampa: un mapa nuevo sin versión se cuela si nadie mira.

    Los mapas del motor son la referencia que se copia. Si el versionado sólo
    lo llevan la mitad, la propiedad se lee como opcional-y-decorativa, que es
    como muere un mecanismo de compatibilidad.
    """
    sin_declarar: list[str] = []
    for mapa in sorted((_RAIZ / "assets" / "maps").rglob("*.tmx")):
        props = ET.parse(mapa).getroot().find("properties")
        nombres = ({p.get("name") for p in props.findall("property")}
                   if props is not None else set())
        if "schema_version" not in nombres:
            sin_declarar.append(mapa.parent.name)
    assert not sin_declarar, (
        f"{len(sin_declarar)} mapas del motor no declaran schema_version: "
        f"{sin_declarar}"
    )
