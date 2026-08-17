"""
Module: stage4_1c
System: src.stages.stage4_1c
Academic Unit: N/A

NIVEL 4-1c — LO QUE FLOTA EN LA NIEBLA

La tercera variante del slot de la Fase 4 (AUD-518,
`src/stages/stage4_1/selector.py`): la misma travesía horizontal, en el
aire. Sin suelo salvo un colchón de contención muy por debajo —caer
cuesta tiempo, no la partida, la misma filosofía "cero muerte instantánea"
del 4-1 aplicada al vacío— y cruzada con plataformas `RhythmBlock` que
aparecen y desaparecen con la música de verdad (AUD-137,
`src/framework/ecs/systems.py::sistema_bloques_ritmicos`): el nivel
entero respira con el compás, no con un temporizador propio.

Por qué el TMX cambia en cada entrada, no una vez por partida
================================================================
El sorteo de AUD-518 (cuál de las tres variantes le toca a esta partida)
es una vez por partida. Éste es distinto y vive un nivel más adentro:
una vez que a la partida le tocó 4.1c, **el propio nivel** cambia de
cara cada vez que se entra —`tools/generate_stage4_1c.py` congeló tres
semillas verificadas (`tests/test_stage4_1c.py`) en tres TMX reales; no
generación procedural en tiempo real (decisión del dueño, 2026-08-17:
sin precedente en este motor y con riesgo real de romper la garantía de
nivel completable).
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.engine.core import azar
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage4_1C(StageScene):
    """4-1c — Lo que flota en la niebla."""

    STAGE_ID: str = "stage4_1c"
    STAGE_NAME: str = "4-1c  LO QUE FLOTA EN LA NIEBLA"
    ZONE: int = 4
    BGM_TRACK: str = "bgm_zone1_traverse"

    #: Las tres plantillas congeladas — mismas claves que
    #: `tools/generate_stage4_1c.py::PLANTILLAS`.
    PLANTILLAS: tuple[str, ...] = ("a", "b", "c")
    DIRECTORIO_TMX = "assets/maps/stage4_1c"

    @classmethod
    def elegir_plantilla(cls) -> str:
        """Sortea una plantilla — con `azar.generador()`, el generador
        aislado del proceso (AUD-374), no el global."""
        return azar.generador().choice(cls.PLANTILLAS)

    def __init__(self, context: GameContext, plantilla: str | None = None) -> None:
        # `plantilla` es un parámetro y no siempre un sorteo interno para
        # que una prueba pueda pedir una plantilla concreta sin depender
        # del azar (`tests/test_stage4_1c.py`).
        self.plantilla_activa = plantilla or self.elegir_plantilla()
        tmx_path = Path(self.DIRECTORIO_TMX) / f"stage4_1c_{self.plantilla_activa}.tmx"
        super().__init__(context, tmx_path)
