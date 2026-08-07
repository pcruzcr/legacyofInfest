"""
Module: test_pendientes_en_plantillas
System: tests
Academic Unit: N/A

AUD-306 — las pendientes existían en el motor y en ningún TMX que se copie.

El estado que corrige
=====================
AUD-297 metió `Slope` en la resolución de colisión, y §17.2 del reporte 87 dejó
escrito por qué fue seguro hacerlo integrado y no aditivo: **ningún mapa
entregado tiene una sola pendiente**, así que el paso nuevo no se ejecuta en
ninguno de los dieciséis.

Eso que hacía segura la integración era, a la vez, el problema: la mecánica
estaba escrita, probada y documentada, y el estudiante que abría la plantilla
para empezar su escenario no la veía por ninguna parte. Una mecánica que no
aparece en el fichero que se copia no existe para quien copia.

Lo que se fija aquí
===================
1. Que la **plantilla del estudiante** trae pendientes, en los dos sentidos, y
   que llegan hasta `StageData` al cargarla.
2. Que la **vitrina** (`stage_mecanicas`) enseña además que la inclinación sale
   del rectángulo y no es siempre de 45°.
3. Que `validate_tmx` mira `student_templates/`. No lo hacía: el barrido por
   defecto recorría los dieciséis mapas del motor, y el TMX del que salen las
   veintiséis entregas no lo comprobaba ningún gate.
"""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

PLANTILLA = Path("student_templates/stage_template/stage_template.tmx")
VITRINA = Path("assets/maps/stage_mecanicas/stage_mecanicas.tmx")


@pytest.fixture(scope="module", autouse=True)
def _pantalla():
    """`pytmx` convierte las imágenes al formato de la pantalla, y sin display
    inicializado revienta al cargar el tileset."""
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


def _pendientes_de(tmx: Path):
    from src.framework.stage.stage_loader import StageLoader

    return StageLoader.load(tmx).pendientes


class TestLaPlantillaDelEstudiante:
    def test_trae_pendientes(self) -> None:
        assert _pendientes_de(PLANTILLA), (
            "la plantilla que copia el estudiante no tiene ni una pendiente: "
            "la mecánica de AUD-297 es invisible para quien empieza un mapa"
        )

    def test_ensena_los_dos_sentidos(self) -> None:
        """Una sola pendiente enseña la mitad. Con `sube` sólo en un valor, el
        estudiante no tiene de dónde deducir que existe el otro."""
        sentidos = {p.sube_a_la_derecha for p in _pendientes_de(PLANTILLA)}

        assert sentidos == {True, False}, (
            f"la plantilla sólo enseña `sube` en {sentidos}: hacen falta las "
            f"dos para que se vea que la propiedad tiene dos valores"
        )

    def test_las_pendientes_se_apoyan_en_el_suelo(self) -> None:
        """Una pendiente flotando sobre el vacío se copia igual, y produce un
        mapa donde la cuesta no lleva a ninguna parte."""
        from src.framework.stage.stage_loader import StageLoader

        datos = StageLoader.load(PLANTILLA)
        assert datos.pendientes, "sin pendientes no hay nada que comprobar"

        for pendiente in datos.pendientes:
            apoyada = any(
                solido.top == pendiente.rect.bottom
                and solido.left <= pendiente.rect.left
                and solido.right >= pendiente.rect.right
                for solido in datos.collision_rects
            )
            assert apoyada, (
                f"la pendiente {pendiente.rect} no descansa sobre ningún "
                f"sólido: en la plantilla quedaría colgada"
            )


class TestLaVitrina:
    def test_ensena_una_inclinacion_que_no_es_de_45_grados(self) -> None:
        """Las dos que había medían 48×48. Con sólo cuadrados, la propiedad que
        de verdad manda —que la hipotenusa va de esquina a esquina del
        rectángulo que dibujas— no se puede deducir mirando el mapa."""
        formas = {
            (p.rect.width, p.rect.height) for p in _pendientes_de(VITRINA)
        }

        assert any(w != h for w, h in formas), (
            f"todas las pendientes de la vitrina son cuadradas ({formas}): no "
            f"enseñan que la inclinación sale del rectángulo"
        )


class TestElGateMiraLaPlantilla:
    def test_validate_tmx_recorre_student_templates(self) -> None:
        """La regresión que hizo falta arreglar para que lo de arriba importe:
        de nada sirve poner una mecánica en la plantilla si el validador que
        vigila los dieciséis mapas no mira ese fichero."""
        import scripts.validate_tmx as v

        encontrados = v.find_tmx_files(v.PLANTILLAS_DIR)

        assert any(f.name == "stage_template.tmx" for f in encontrados), (
            "validate_tmx no encuentra la plantilla del estudiante: el TMX "
            "del que salen las 26 entregas no lo comprueba ningún gate"
        )
