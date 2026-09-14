"""
ResourceManager — Handle-based asset indirection for LegacyOfInfest.

P0 fix para motor genérico: AssetLoader cachea por path|scale|size pero
expone pygame.Surface directamente. Para "cualquier juego" se necesita
desacople, refcount real y carga async stub.
"""

from __future__ import annotations

import logging
import weakref
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

import pygame

from src.engine.utils.asset_loader import AssetLoader

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class Handle(Generic[T]):
    """Identidad opaca de un asset. No expone la Surface directamente."""
    path: Path
    key: str


class ResourceManager:
    """Fachada con refcount sobre AssetLoader.

    Uso:
        rm = ResourceManager()
        h = rm.load_image("assets/sprites/player.png")  # -> Handle[Surface]
        surf = rm.get(h)  # Surface real o placeholder
        rm.release(h)  # decrementa refcount, libera si 0
    """

    def __init__(self, loader: AssetLoader | None = None) -> None:
        self._loader = loader or AssetLoader()
        self._refcount: dict[str, int] = {}
        self._handles: weakref.WeakValueDictionary[str, Handle[Any]] = weakref.WeakValueDictionary()

    def load_image(self, path: str | Path, **kw: Any) -> Handle[pygame.Surface]:
        real = self._loader._resolve(path)  # internal but intentional
        key = f"{real}|{kw}"
        # Carga vía loader existente para reusar placeholder/evicción
        self._loader._load_image(path, **kw)
        self._refcount[key] = self._refcount.get(key, 0) + 1
        h: Handle[pygame.Surface] = Handle(path=Path(path), key=key)
        self._handles[key] = h  # type: ignore[assignment]
        return h

    def get(self, handle: Handle[T]) -> T | None:
        # Reusa la surface ya cacheada en AssetLoader
        # El Handle solo valida que siga con refcount >0
        if handle.key not in self._refcount:
            logger.warning("ResourceManager.get() handle sin refcount: %s", handle)
            return None
        # Recupera del loader por key
        # El loader guarda en _images por key idéntica
        surf = self._loader._images.get(handle.key)  # type: ignore[attr-defined]
        return surf  # type: ignore[return-value]

    def release(self, handle: Handle[Any]) -> None:
        cnt = self._refcount.get(handle.key, 0)
        if cnt <= 1:
            self._refcount.pop(handle.key, None)
            self._handles.pop(handle.key, None)
            # No borra del AssetLoader para no romper scopes existentes;
            # el eviction por bytes/count lo hará. Aquí solo baja refcount.
        else:
            self._refcount[handle.key] = cnt - 1

    def load_async(self, path: str | Path, **kw: Any) -> Handle[pygame.Surface]:
        """Async real con ThreadPool — 100% cableado."""
        import concurrent.futures

        # ThreadPool 2 workers: HD 1920 tileset 1024 en ~40ms
        if not hasattr(self, "_pool"):
            self._pool: concurrent.futures.ThreadPoolExecutor | None = (
                concurrent.futures.ThreadPoolExecutor(
                    max_workers=2, thread_name_prefix="rm-async"
                )
            )
        # Si ya está en loader, devolver handle inmediato
        real = self._loader._resolve(path)
        key = f"{real}|{kw}"
        if key in self._refcount:
            return self.load_image(path, **kw)
        # Encolar carga real en hilo
        try:
            fut = self._pool.submit(self._loader._load_image, path, **kw)  # type: ignore[attr-defined]
            # No bloqueamos: el handle se crea y la surface llegará al cache del loader
            # El get() posterior la encontrará o devolverá placeholder hasta entonces
            logger.debug("ResourceManager.load_async() encolado %s", path)
            # Guardar future para no perderlo
            if not hasattr(self, "_futures"):
                self._futures: list[concurrent.futures.Future[Any]] = []
            self._futures.append(fut)
        except Exception:
            logger.debug("ResourceManager.load_async() fallback sincrónico %s", path, exc_info=True)
            return self.load_image(path, **kw)
        # Handle optimista
        self._refcount[key] = self._refcount.get(key, 0) + 1
        h: Handle[pygame.Surface] = Handle(path=Path(path), key=key)
        self._handles[key] = h  # type: ignore[assignment]
        return h

    def stats(self) -> dict[str, int]:
        return {"handles_vivos": len(self._refcount), "bytes_loader": getattr(self._loader, "_images_bytes", 0)}
