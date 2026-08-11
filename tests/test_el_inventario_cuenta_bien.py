"""
Las cifras del inventario (docs/62) se vuelven a medir aquí.

Invariante 6: los números de la documentación son verificables o no se
escriben. `docs/62_ESTADO_DEL_PROYECTO.md` es el «inventario medido» del
proyecto y llevaba hasta agosto de 2026 siete cifras podridas: la cuenta de
tipos de objeto decía 62 cuando el motor ya aceptaba más, la de líneas de
`gl_pipeline` decía 479 cuando eran 1.100, la de pruebas decía 1.608 cuando
eran 4.751, y citaba un documento retirado. `docs/60` tiene su guardián
(`test_guia_del_motor.py`); el inventario no tenía ninguno, que es la razón
de que sus cifras envejecieran sin que nadie se enterara.

Se guarda lo que se puede medir aquí sin ejecutar la suite entera:

* los **tipos de objeto** que acepta el cargador (78 en runtime, con el
  desglose 39 + 37 + `Solid`/`Platform`, y los 69 del registro base que
  genera la referencia de estudiantes);
* las **propiedades de mapa** que reconoce el validador (18).

La cuenta de pruebas (4.751) la vigila ya `test_el_numero_de_pruebas_es_el_real`
con su tolerancia; duplicar aquí esa medición de 19 segundos no la haría más
verdadera.
"""
from __future__ import annotations

import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
INVENTARIO = RAIZ / "docs" / "62_ESTADO_DEL_PROYECTO.md"


@pytest.fixture(scope="module")
def inventario() -> str:
    assert INVENTARIO.exists(), "falta el inventario medido"
    return INVENTARIO.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def _motor():
    """Las cuentas del cargador, medidas de la misma forma que en
    `test_guia_del_motor` (AUD-144: el catálogo completo incluye los tipos
    que registran a nivel de módulo los escenarios de las entregas).

    El registro es global y otros tests lo vacían o lo ensucian a propósito
    (`test_tmx_diagnostics` deja `_registered = True` con tres tipos a mano,
    `test_stage_loader` limpia el registro en cada `setup_method`). Por eso
    esta fixture mide el estado que dejan los demás y restaura el ajeno al
    terminar, pero **no** vacía el registro: los módulos de los escenarios ya
    importados no re-ejecutan su `register_entity` de nivel de módulo, y un
    `clear()` mediría 30 tipos donde el juego ve 37.

    El registro base de 69 tipos (el que genera la referencia de estudiantes)
    sólo existe en un intérprete limpio: ahí el registro contiene únicamente
    los 30 integrados. En la suite caliente ya se importaron los escenarios,
    así que esa cuenta sale de un subproceso, igual que la mide
    `generate_tmx_reference.py` en CI."""
    import os
    import subprocess
    import sys

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame

    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((8, 8))

    from src.engine.core.stage_registry import discover_stages
    from src.framework.entities import entity_factory
    from src.framework.stage.stage_loader import StageLoader
    from src.framework.stage.tmx_diagnostics import (
        BUILTIN_OBJECT_TYPES,
        COLLISION_OBJECT_TYPES,
    )

    anterior = dict(StageLoader._entity_registry)
    registered_previo = entity_factory._registered
    try:
        entity_factory.ensure_registered()
        base = len(StageLoader._entity_registry)
        discover_stages()
        cuenta_fresca = subprocess.check_output(
            [
                sys.executable,
                "-c",
                "import os; os.environ.setdefault('SDL_VIDEODRIVER','dummy');"
                "os.environ.setdefault('SDL_AUDIODRIVER','dummy');"
                "import pygame; pygame.init(); pygame.display.set_mode((8,8));"
                "from src.framework.entities import entity_factory;"
                "from src.framework.stage.tmx_diagnostics import "
                "BUILTIN_OBJECT_TYPES, COLLISION_OBJECT_TYPES;"
                "entity_factory.ensure_registered();"
                "from src.framework.stage.stage_loader import StageLoader;"
                "print(len(BUILTIN_OBJECT_TYPES), "
                "len(StageLoader._entity_registry), len(COLLISION_OBJECT_TYPES))",
            ],
            cwd=str(RAIZ),
            text=True,
        ).strip()
        integrados_fresco, base_fresco, colision_fresco = (
            int(x) for x in cuenta_fresca.split()
        )
        return {
            "integrados": len(BUILTIN_OBJECT_TYPES),
            "integrados_fresco": integrados_fresco,
            "colision": sorted(COLLISION_OBJECT_TYPES),
            "colision_fresco": colision_fresco,
            "registro_base": base_fresco,
            "registro_caliente": base,
            "registro_runtime": len(StageLoader._entity_registry),
        }
    finally:
        StageLoader._entity_registry.clear()
        StageLoader._entity_registry.update(anterior)
        entity_factory._registered = registered_previo


def _cifra(texto: str, patron: str) -> int:
    m = re.search(patron, texto)
    assert m, f"docs/62 ya no dice «{patron}»: hay que actualizar esta prueba"
    return int(m.group(1).replace(".", "").replace(",", ""))


class TestLosTiposDeObjeto:
    def test_el_inventario_dice_lo_que_mide_el_cargador(self, inventario, _motor) -> None:
        """La frase «78 tipos de objeto en runtime» y su desglose tienen que
        coincidir con el cargador; si el desglose cambia, el documento y esta
        prueba se actualizan juntos. Las cuatro cuentas conviven a propósito:
        69 = capa `Objects` con el registro base (lo que genera la referencia
        de estudiantes, en intérprete limpio), 71 = + `Solid`/`Platform`,
        76 = `Objects` con los escenarios descubiertos, 78 = todo."""
        integrados = _motor["integrados_fresco"]
        base = _motor["registro_base"]
        colision = _motor["colision_fresco"]
        objects_runtime = _motor["registro_runtime"] + _motor["integrados"]

        assert objects_runtime == 76, (
            f"el cargador acepta {objects_runtime} tipos en `Objects` con "
            "escenarios descubiertos, no 76: ¿cambió el registro o la prueba?"
        )
        assert integrados == 39, f"integrados: {integrados}, no 39"
        assert base == 30, f"registro base limpio: {base}, no 30"
        assert base + integrados == 69, f"{base}+{integrados}, no 69"
        assert base + integrados + colision == 71

        assert "78 tipos de objeto en runtime" in inventario
        assert f"{integrados} integrados" in inventario
        assert f"{_motor['registro_runtime']} del" in inventario
        assert "69" in inventario and "71" in inventario


class TestLasPropiedadesDeMapa:
    def test_el_inventario_dice_las_dieciocho_propiedades(self, inventario) -> None:
        from scripts.check_tmx_coverage import PROPIEDADES_MAPA

        assert len(PROPIEDADES_MAPA) == 18, (
            "check_tmx_coverage.py reconoce otra cantidad de propiedades; "
            "el inventario y esta prueba se actualizan juntos"
        )
        assert "18 propiedades de mapa" in inventario


class TestElInventarioNoPrometeDocumentosRetirados:
    def test_la_cita_a_la_auditoria_61_apunta_a_la_sucesora(self, inventario) -> None:
        """La purga de 2026-08-09 retiró `61_AUDITORIA_AAA_2026-08.md`; el
        inventario ya no debe citarla como fuente viva."""
        assert "61_AUDITORIA" not in inventario, (
            "docs/62 cita la auditoría 61, retirada en la purga; su sucesora "
            "es 89_AUDITORIA_MULTIDISCIPLINAR.md"
        )
        assert (RAIZ / "docs" / "89_AUDITORIA_MULTIDISCIPLINAR.md").exists()
