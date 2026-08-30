"""
EnemyComponents — Componentes extraídos de EnemyBase (State + Strategy).

EnemyBase era 1344 líneas con 4 responsabilidades: FSM, percepción,
movimiento y animación. El FSM era un `if/elif` gigante en
`_run_state_machine` (137 líneas) y cada nuevo estado exigía editar la clase.

Ahora cada estado es una Strategy con `enter/update/exit`, y la percepción
y el movimiento son Strategies inyectables. EnemyBase queda como Facade
que delega a `EnemyStateMachine` y mantiene la API (`enemy.state`,
`enemy.apply_hit`) para las 35 especies.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.framework.entities.enemy_base import EnemyBase


class EnemyStateBase(ABC):
    """Strategy para un estado de enemigo (State pattern)."""

    def enter(self, enemy: EnemyBase) -> None:  # noqa: B027
        pass

    @abstractmethod
    def update(self, enemy: EnemyBase, dt: float) -> None:
        ...

    def exit(self, enemy: EnemyBase) -> None:  # noqa: B027
        pass


class EnemyPerceptionStrategy(ABC):
    """Strategy de percepción — cómo detecta al jugador."""

    @abstractmethod
    def detecta(self, enemy: EnemyBase, player_rect: pygame.Rect) -> bool:
        ...


class EnemyMovementStrategy(ABC):
    """Strategy de movimiento — cómo se desplaza según táctica."""

    @abstractmethod
    def mover(self, enemy: EnemyBase, dt: float, tactic: str) -> None:
        ...


class EnemyStateMachine:
    """Máquina de estados formal para EnemyBase (State).

    Reemplaza el `if state==PATROL: ... elif ALERT` por delegación.
    Cada estado registrado es una Strategy; añadir un estado = nueva clase,
    sin tocar la máquina.
    """

    def __init__(self, enemy: EnemyBase) -> None:
        self.enemy = enemy
        self._states: dict[str, EnemyStateBase] = {}
        self._current: EnemyStateBase | None = None

    def register(self, name: str, state: EnemyStateBase) -> None:
        self._states[name] = state

    def change(self, name: str) -> None:
        nxt = self._states.get(name)
        if nxt is None or nxt is self._current:
            return
        if self._current is not None:
            self._current.exit(self.enemy)
        self._current = nxt
        self._current.enter(self.enemy)

    def update(self, dt: float) -> None:
        if self._current is not None:
            self._current.update(self.enemy, dt)
