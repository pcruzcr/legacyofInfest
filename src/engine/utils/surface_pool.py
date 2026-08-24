"""
Module: surface_pool
System: engine.utils
Academic Unit: N/A
Description: Surface object pool to mitigate GC pressure from per-frame
Surface allocations. Pre-allocates surfaces of common sizes and recycles
them instead of creating/destroying.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import pygame

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Configuration for a pool size bucket."""
    capacity: int = 4
    flags: int = 0
    prefetch: int = 2  # number to pre-allocate on init


_DEFAULT_BUCKETS: dict[tuple[int, int, int], PoolConfig] = {
    # (width, height, flags) -> config
    (800, 600, 0): PoolConfig(capacity=2, prefetch=1),
    (800, 600, pygame.SRCALPHA): PoolConfig(capacity=2, prefetch=1),
    (280, 200, 0): PoolConfig(capacity=4, prefetch=2),
    (280, 200, pygame.SRCALPHA): PoolConfig(capacity=4, prefetch=2),
    (32, 32, 0): PoolConfig(capacity=16, prefetch=8),
    (32, 32, pygame.SRCALPHA): PoolConfig(capacity=16, prefetch=8),
    (16, 16, 0): PoolConfig(capacity=16, prefetch=8),
    (16, 16, pygame.SRCALPHA): PoolConfig(capacity=16, prefetch=8),
    (64, 64, 0): PoolConfig(capacity=8, prefetch=4),
    (64, 64, pygame.SRCALPHA): PoolConfig(capacity=8, prefetch=4),
}


class SurfacePool:
    """Reusable pool of pygame Surfaces keyed by (width, height, flags).

    Usage:
        pool = SurfacePool()
        surf = pool.borrow(32, 32, pygame.SRCALPHA)
        # ... use surf ...
        pool.return_surface(surf)

    Surfaces are pre-initialized at startup and recycled to avoid GC pressure.
    """

    __slots__ = ("_active_count", "_flip_cache", "_hits", "_leak_warning", "_misses", "_pools")

    def __init__(self, buckets: dict[tuple[int, int, int], PoolConfig] | None = None) -> None:
        self._pools: dict[tuple[int, int, int], list[pygame.Surface]] = defaultdict(list)
        self._hits: int = 0
        self._misses: int = 0
        self._active_count: int = 0
        # AUD-124 — la clave es una tupla de tres enteros, no un entero.
        # La anotación decía `dict[int, ...]` y el código guardaba
        # `(id(frames), len(frames), id(frames[0]))`, que es lo correcto: con
        # sólo `id()` una lista liberada y otra creada en la misma dirección
        # compartirían caché y el sprite saldría espejado. La anotación
        # describía una versión anterior y más frágil de este caché.
        self._flip_cache: dict[tuple[int, int, int], list[pygame.Surface]] = {}
        self._leak_warning: bool = False

        buckets = buckets or _DEFAULT_BUCKETS
        for key, cfg in buckets.items():
            w, h, flags = key
            for _ in range(cfg.prefetch):
                surf = pygame.Surface((w, h), flags)
                self._pools[key].append(surf)

    def borrow(
        self,
        width: int,
        height: int,
        flags: int = 0,
        fill_color: tuple[int, int, int, int] | None = None,
    ) -> pygame.Surface:
        """Get a Surface from the pool, or create one if pool is empty.

        If fill_color is provided, the surface is cleared to that color
        before returning (avoids explicit fill in caller).
        """
        key = (width, height, flags)
        pool = self._pools.get(key)
        if pool:
            try:
                surf = pool.pop()
                self._hits += 1
            except IndexError:
                surf = pygame.Surface((width, height), flags)
                self._misses += 1
        else:
            surf = pygame.Surface((width, height), flags)
            self._misses += 1

        self._active_count += 1
        if fill_color:
            surf.fill(fill_color)
        return surf

    def return_surface(self, surf: pygame.Surface, clear: bool = True) -> None:
        """Return a Surface to the pool.

        If clear is True, the surface is filled with (0,0,0,0) to avoid
        leaking pixel data between frames.
        """
        if surf is None:
            return
        key = (surf.get_width(), surf.get_height(), surf.get_flags())
        if clear:
            surf.fill((0, 0, 0, 0))
        self._pools[key].append(surf)
        self._active_count -= 1

    def return_all(self, surfaces: list[pygame.Surface], clear: bool = True) -> None:
        """Return multiple surfaces at once."""
        for surf in surfaces:
            self.return_surface(surf, clear=clear)

    def prewarm(self, width: int, height: int, flags: int = 0, count: int = 1) -> None:
        """Pre-allocate additional surfaces for a given size."""
        key = (width, height, flags)
        if key not in self._pools:
            self._pools[key] = []
        for _ in range(count):
            self._pools[key].append(pygame.Surface((width, height), flags))

    def stats(self) -> dict[str, Any]:
        """Return pool statistics for monitoring/profiling."""
        total_pooled = sum(len(v) for v in self._pools.values())
        return {
            "hits": self._hits,
            "misses": self._misses,
            "active": self._active_count,
            "pooled": total_pooled,
            "hit_ratio": self._hits / max(self._hits + self._misses, 1),
            "buckets": {str(k): len(v) for k, v in sorted(self._pools.items())},
        }

    # ── Flipped frame cache ─────────────────────────────────────
    # Caches horizontally-flipped sprite frames to avoid per-frame
    # pygame.transform.flip() allocations in entity draw() methods.

    def get_flipped_frames(self, frames: list[pygame.Surface]) -> list[pygame.Surface]:
        """Return cached horizontally-flipped copies of the given frames.

        Cache key combines id(frames), length, and first frame id to
        guard against id() reuse after garbage collection.
        """
        if not frames:
            return []
        key = (id(frames), len(frames), id(frames[0]))
        cached = self._flip_cache.get(key)
        if cached is not None:
            return cached
        flipped = [pygame.transform.flip(f, True, False) for f in frames]
        self._flip_cache[key] = flipped
        return flipped

    def clear_flip_cache(self) -> None:
        """Clear the flipped frame cache (call when sprite sheets are reloaded)."""
        self._flip_cache.clear()

    def clear(self) -> None:
        """Release all pooled surfaces (except active ones)."""
        self._pools.clear()
        self._hits = 0
        self._misses = 0
        self._active_count = 0
        self._flip_cache.clear()


# Module-level default instance for easy integration
_default_pool: SurfacePool | None = None


def get_pool() -> SurfacePool:
    """Get or create the default SurfacePool instance."""
    global _default_pool
    if _default_pool is None:
        _default_pool = SurfacePool()
    return _default_pool


def set_pool(pool: SurfacePool | None) -> None:
    """Set the default pool (useful for testing)."""
    global _default_pool
    _default_pool = pool
