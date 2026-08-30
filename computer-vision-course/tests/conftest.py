"""
Configuración de las pruebas del curso.

Las variables de SDL se fijan **antes** de importar pygame porque el
controlador de vídeo se elige al inicializar y luego no cambia. Puesto
después, el `dummy` no hace nada y la suite intenta abrir ventanas.

`sys.path` incluye la raíz del repositorio y la del curso: las pruebas
importan tanto `cvcourse` como `src.framework` del motor.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

RAIZ_DEL_CURSO = Path(__file__).resolve().parent.parent
RAIZ_DEL_REPO = RAIZ_DEL_CURSO.parent

for ruta in (RAIZ_DEL_CURSO, RAIZ_DEL_REPO):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))

import pytest


@pytest.fixture(scope="session")
def hay_motor() -> bool:
    from cvcourse.engine_bridge import hay_motor as _hay

    return _hay()


@pytest.fixture
def perfil_temporal(tmp_path: Path) -> Path:
    """Directorio de progreso desechable para las pruebas del modo taller.

    Nunca se usa el directorio real: una prueba que escriba en el perfil del
    curso dejaría notas sembradas en la máquina de quien la ejecute.
    """
    destino = tmp_path / "profiles"
    destino.mkdir()
    return destino
