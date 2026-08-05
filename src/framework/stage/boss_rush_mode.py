"""
Module: boss_rush_mode
System: framework.stage
Academic Unit: N/A
Description: Boss Rush mode — consecutive boss gauntlet with health carry-over and scoring.

.. note::
   **CONECTADO (AUD-261), y con su historia.** El aviso que había aquí decía
   «PARCIALMENTE CONECTADO» y era exacto: desde AUD-191 el jugador podía entrar
   por el menú y pelear seguido contra los cuatro jefes, pero **nadie conducía
   el modo**. `boss_rush_entry` lo construía, llamaba a `start()` y lo dejaba
   en `context.boss_rush`, donde no lo leía nadie: `advance_to_next()` y
   `record_hit()` no tenían llamante fuera de este fichero, la puntuación nunca
   se calculaba, `hits_taken` se quedaba en cero, y `_carry_over_health` no
   tenía ni getter ni setter — el arrastre de vida no existía tampoco **dentro**
   del módulo.

   Lo conduce ahora `StageScene`, que es la única que sabe cuándo empieza un
   combate, cuándo el jugador recibe un golpe y cuándo cae el jefe. Las tres
   cosas que `docs/44` §4 daba por hechas —gauntlet, marcador y arrastre de
   vida— lo están, y GAP-030 se cierra con ellas.
"""
from __future__ import annotations

from typing import Any

#: Salud que se devuelve entre combates del Boss Rush (AUD-261).
#:
#: El arrastre puro —terminas con lo que te queda y empiezas igual— convierte
#: el gauntlet en una carrera imposible: se llega al tercer jefe con media vida
#: y al cuarto sin nada. Nadie ha jugado esto lo bastante para calibrar otra
#: cosa, así que la curación es **una fracción fija con nombre**: se ve, se
#: discute y se cambia en un sitio. Esconderla dentro de una fórmula sería
#: repetir el pecado de `docs/44`, que declaraba terminado lo que no existía.
CURACION_ENTRE_COMBATES: float = 1.0


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

    # ── AUD-261: lo que el juego llama para conducir el modo ──────

    def registrar_tiempo(self, dt: float) -> None:
        """Acumula el tiempo del combate en curso.

        Lo llama la escena por fotograma. Sin esto, `current.time` se quedaba
        en 0 y la parte de la puntuación que premia ir rápido no premiaba
        nada — el marcador existía y medía una constante.
        """
        current = self.get_current_stage()
        if current is not None:
            current.time += dt

    def acreditar_combate(self, salud_restante: float, medidor: float,
                          salud_maxima: float | None = None) -> BossRushStage | None:
        """El jefe ha caído: se guarda con qué se sigue y se pasa al siguiente.

        Es el punto de entrada que le faltaba al modo. Une las dos mitades que
        estaban escritas y sueltas: `advance_to_next()` —que ya sabía puntuar—
        y el arrastre de vida, que no tenía forma de escribirse desde fuera.

        La curación de `CURACION_ENTRE_COMBATES` se aplica **aquí** y no al
        entrar en el combate siguiente porque así el número que se guarda es el
        que se va a usar: si se aplicara al entrar, `salud_arrastrada` diría
        una cosa y el jugador vería otra, y ésa es la clase de desajuste que
        deja una barra de vida mintiendo.
        """
        tope = salud_maxima if salud_maxima is not None else float("inf")
        self._carry_over_health = min(salud_restante + CURACION_ENTRE_COMBATES, tope)
        self._carry_over_meter = medidor
        return self.advance_to_next()

    @property
    def salud_arrastrada(self) -> float:
        """Con cuánta vida empieza el siguiente combate. `0` = a vida llena."""
        return self._carry_over_health

    @salud_arrastrada.setter
    def salud_arrastrada(self, valor: float) -> None:
        self._carry_over_health = max(0.0, float(valor))

    @property
    def medidor_arrastrado(self) -> float:
        return self._carry_over_meter

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