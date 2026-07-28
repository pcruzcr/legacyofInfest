"""
Paquete académico: el plan de estudios y el progreso de cada estudiante.

Vive en `framework` y no en `engine` a propósito. El motor no sabe que hay
una asignatura detrás; podría usarse para un juego sin nada de esto. Lo que
convierte a este proyecto en material de clase —qué unidad va antes de cuál,
qué fórmula se explica en cada una, cuántas preguntas hay que acertar para
avanzar— es contenido, y el contenido vive en el framework.
"""
from __future__ import annotations

from src.framework.academic.curriculum import (
    PLAN,
    Unidad,
    ids_de_unidades,
    siguiente_unidad,
    unidad,
    unidad_de_escena,
)
from src.framework.academic.progress import (
    ACIERTOS_PARA_APROBAR,
    PREGUNTAS_POR_UNIDAD,
    ProgresoAcademico,
    ResultadoIntento,
)

__all__ = [
    "ACIERTOS_PARA_APROBAR",
    "PLAN",
    "PREGUNTAS_POR_UNIDAD",
    "ProgresoAcademico",
    "ResultadoIntento",
    "Unidad",
    "ids_de_unidades",
    "siguiente_unidad",
    "unidad",
    "unidad_de_escena",
]
