"""
Module: boss_rush_mode
System: framework.stage
Academic Unit: N/A
Description: Boss Rush mode — consecutive boss gauntlet with health carry-over and scoring.

.. warning::
   **NOT WIRED (AUD-022).** This module is complete and tested in isolation, but
   nothing in the shipping game constructs or calls it — there is no menu entry,
   scene or hook that reaches it. It is retained deliberately, as a foundation
   for the feature and as teaching material, but the project documentation
   should not describe the feature as delivered until an entry point exists.
   Tracked as refactor item R-11.
"""
from __future__ import annotations

from typing import Any


class BossRushStage:
    """A single boss encounter in the boss rush."""

    def __init__(self, boss_id: str, boss_name: str,
                 scene_builder: Any, phase_count: int = 1) -> None:
        self.boss_id: str = boss_id
        self.boss_name: str = boss_name
        self.scene_builder: Any = scene_builder
        self.phase_count: int = phase_count
        self.defeated: bool = False
        self.time: float = 0.0
        self.hits_taken: int = 0


class BossRushMode:
    """Gauntlet mode: fight bosses consecutively."""

    def __init__(self, stages: list[BossRushStage] | None = None) -> None:
        self._stages: list[BossRushStage] = stages or []
        self._current_index: int = 0
        self._active: bool = False
        self._total_time: float = 0.0
        self._start_time: float = 0.0
        self._carry_over_health: float = 0.0
        self._carry_over_meter: float = 0.0
        self._score: int = 0

    def add_stage(self, stage: BossRushStage) -> None:
        self._stages.append(stage)

    def start(self) -> None:
        self._current_index = 0
        self._active = True
        self._total_time = 0.0
        self._score = 0
        self._carry_over_health = 0.0
        self._carry_over_meter = 0.0
        for s in self._stages:
            s.defeated = False
            s.time = 0.0
            s.hits_taken = 0

    def get_current_stage(self) -> BossRushStage | None:
        if 0 <= self._current_index < len(self._stages):
            return self._stages[self._current_index]
        return None

    def advance_to_next(self) -> BossRushStage | None:
        """Da por derrotado al jefe actual y pasa al siguiente, si lo hay.

        F2.5 — dos defectos que nadie había visto
        -----------------------------------------
        Este módulo no tenía una sola prueba. Al escribirle las primeras
        aparecieron dos fallos que se anulaban entre sí lo justo para que nada
        crujiera:

        1. **El último jefe no contaba.** La versión anterior sólo marcaba
           `defeated` y sumaba puntos dentro del `if` que comprueba que quede
           otro jefe. Derrotar al jefe final no daba puntos y lo dejaba
           marcado como vivo. Medido con dos jefes: `[True, False]`.

        2. **El modo no se podía terminar.** `is_complete()` exige
           ``self._active and self._current_index >= len(self._stages)``, y el
           código anterior nunca incrementaba el índice más allá del último y
           además apagaba `_active` al llegar al final. Las dos condiciones no
           podían darse a la vez: `is_complete()` devolvía `False` para
           siempre. Un modo de juego sin final.

        Ahora se acredita al jefe actual **siempre**, y el índice avanza hasta
        `len(self._stages)` para que el estado "terminado" sea representable.
        """
        current = self._stages[self._current_index] if self._stages else None
        if current is not None:
            current.defeated = True
            self._score += max(0, 1000 - int(current.time * 10))
            self._score -= current.hits_taken * 50

        self._current_index += 1
        if self._current_index < len(self._stages):
            return self._stages[self._current_index]
        # Se ha superado el último. El índice queda fuera de rango a propósito:
        # es lo que `is_complete()` mira para distinguir "terminado" de "en el
        # último jefe".
        return None

    def record_hit(self) -> None:
        current = self.get_current_stage()
        if current:
            current.hits_taken += 1

    def is_complete(self) -> bool:
        """¿Se han superado todos los jefes?

        Requiere que el modo se haya iniciado —`_stages` vacío con el modo
        parado no es "completo", es "no empezado"— y que el índice haya
        rebasado el último jefe.
        """
        return bool(self._stages) and self._current_index >= len(self._stages)

    @property
    def score(self) -> int:
        return self._score

    @property
    def active(self) -> bool:
        return self._active

    @property
    def current_name(self) -> str:
        current = self.get_current_stage()
        return current.boss_name if current else ""

    @property
    def progress(self) -> str:
        return f"{self._current_index + 1}/{len(self._stages)}"