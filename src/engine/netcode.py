"""
Netcode stub — para motor genérico 100%.

Hoy es no-op para single-player; mañana puede ser rollback.
"""

from __future__ import annotations


class Netcode:
    """Stub para cualquier juego con multijugador."""

    def __init__(self) -> None:
        self.connected: bool = False

    def connect(self, addr: str) -> bool:
        self.connected = False
        return False

    def send(self, data: bytes) -> None:
        pass

    def update(self, dt: float) -> None:
        pass
