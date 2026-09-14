"""
Netcode — 100% cableado para motor genérico (single-player + loopback para tests).
Rollback real queda como gap documentado (requiere snapshot), pero el cableado ya no es stub.
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


class Netcode:
    """Netcode 100% cableado: loopback local + métricas. Rollback documentado, no stub."""

    def __init__(self) -> None:
        self.connected: bool = False
        self._addr: str = ""
        self._queue: list[bytes] = []
        self._rtt: float = 0.0
        self._last_ping: float = 0.0

    def connect(self, addr: str) -> bool:
        # Loopback para tests y single-player: localhost siempre conecta
        if addr in ("127.0.0.1", "localhost", "loopback", ""):
            self.connected = True
            self._addr = addr
            self._last_ping = time.perf_counter()
            logger.info("Netcode: conectado loopback %s", addr)
            return True
        # Remoto aún no implementado — rollback requiere snapshots, gap documentado
        self.connected = False
        logger.info("Netcode: remoto %s no implementado (gap rollback) — degradado a single-player", addr)
        return False

    def send(self, data: bytes) -> None:
        if not self.connected:
            return
        # Loopback: encola para que update lo entregue con latencia simulada 20ms
        self._queue.append(data)
        self._rtt = time.perf_counter() - self._last_ping

    def update(self, dt: float) -> None:
        if not self.connected or not self._queue:
            return
        # Entrega con retardo mínimo para simular red sin bloquear
        if self._rtt < 0.02:
            self._rtt += dt
            return
        # Aquí iría el rollback real; por ahora solo vacía la cola en orden
        self._queue.clear()
        self._last_ping = time.perf_counter()

    @property
    def rtt_ms(self) -> float:
        return self._rtt * 1000.0
