"""AUD-591 — stage1_1 registra sus enemigos a nivel de módulo, no en __init__.

El hallazgo F7 del FODA (docs/93 §6) era el aviso oficial de `validate_tmx`:
`ShooterFrog` y `FlyingBird` se registraban dentro de
`Stage1_1_LaEntrada.__init__`, así que el previsualizador, el calificador y
cualesquiera herramientas que abren el TMX sin construir la escena resolvían
esos tipos con la clase del bestiario — un pájaro genérico donde debía estar
el `CanopyBird` de la Unidad III, sin que nada fallara.

La cura es la que el propio aviso ordena y la que `boss_paburu` (AUD-151) y
`stage1_3_las_aulas` ya practican: registrar al importar el módulo. Así las
cuatro rutas —jugar, previsualizar, calificar, validar— ven el mismo mundo.

La prueba va por subproceso a propósito: el registro es estado global del
proceso (AUD-415/AUD-472), y en la suite caliente otros módulos de escenario
ya habrán ensuciado `_entity_registry`. Un intérprete limpio es la única forma
de medir «sólo importar el módulo».
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

_GUION = """
import src.stages.stage1_1.stage1_1 as escena
from src.framework.stage.stage_loader import StageLoader
registro = StageLoader._entity_registry
print(registro.get("ShooterFrog").__name__, registro.get("FlyingBird").__name__)
"""


def _registro_tras_importar() -> tuple[str, str]:
    entorno = dict(os.environ)
    entorno.update({
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "PYGAME_HIDE_SUPPORT_PROMPT": "1",
    })
    hecho = subprocess.run(
        [sys.executable, "-c", _GUION],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
        env=entorno, check=True,
    )
    frog, bird = hecho.stdout.strip().split()
    return frog, bird


def test_solo_importar_el_modulo_registra_shooterfrog() -> None:
    frog, _bird = _registro_tras_importar()
    assert frog == "JungleFrog", (
        f"importar stage1_1 deja ShooterFrog={frog!r}: el registro sigue "
        "dentro de una función y las herramientas ven otra clase"
    )


def test_solo_importar_el_modulo_registra_flyingbird() -> None:
    _frog, bird = _registro_tras_importar()
    assert bird == "CanopyBird", (
        f"importar stage1_1 deja FlyingBird={bird!r}: el registro sigue "
        "dentro de una función y las herramientas ven otra clase"
    )
