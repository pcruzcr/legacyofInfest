"""
BossPhaseGraph — grafo dirigido para jefes no lineales.

P1 para motor genérico: BossBase solo soporta lista lineal health_threshold.
Un Metroidvania necesita bifurcaciones (Paburu 3A/3B, Gavilán).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.framework.entities.boss_base import BossPhase


@dataclass
class Nodo:
    phase: BossPhase
    salidas: list[str] = field(default_factory=list)  # ids de nodos destino


class BossPhaseGraph:
    """Grafo de fases. Uso: graph.add(Nodo(phase)); graph.conectar('A','B')."""

    def __init__(self) -> None:
        self._nodos: dict[str, Nodo] = {}
        self._actual: str | None = None

    def add(self, nodo_id: str, nodo: Nodo) -> None:
        self._nodos[nodo_id] = nodo
        if self._actual is None:
            self._actual = nodo_id

    def conectar(self, origen: str, destino: str) -> None:
        if origen in self._nodos and destino in self._nodos:
            self._nodos[origen].salidas.append(destino)

    def actual(self) -> BossPhase | None:
        if self._actual is None:
            return None
        n = self._nodos.get(self._actual)
        return n.phase if n else None

    def avanzar(self, health: float) -> BossPhase | None:
        """Avanza si health <= threshold del nodo actual y hay salida."""
        if self._actual is None:
            return None
        nodo = self._nodos[self._actual]
        if health <= nodo.phase.health_threshold and nodo.salidas:
            # Por defecto, toma la primera salida; lógica custom puede sobreescribir
            # Ej: Paburu elige 3A/3B con random en el jefe, no aquí.
            self._actual = nodo.salidas[0]
            return self.actual()
        return nodo.phase

    def elegir(self, destino: str) -> bool:
        """Fuerza salto a `destino` si es salida del actual. Para decisiones como Paburu."""
        if self._actual is None:
            return False
        if destino in self._nodos[self._actual].salidas:
            self._actual = destino
            return True
        return False
