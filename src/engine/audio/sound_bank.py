"""
Module: sound_bank
System: engine
Academic Unit: N/A
Description: SoundBank wraps an AssetLoader to provide
name-based access to pygame.mixer.Sound objects. Sounds are
keyed by a human-readable name (not a raw path), and the bank
remembers every name it has loaded so that get() can produce a
useful error message when an unknown name is requested.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    pass


class SoundBank:
    """Name-based lookup for loaded pygame.mixer.Sound objects.

    All load requests are delegated to the supplied AssetLoader and
    cached by path. The name is a plain string chosen by the caller
    (typically a music or SFX identifier from a constants table); it
    does not need to match any file-system layout.
    """

    def __init__(self, asset_loader: AssetLoader) -> None:
        """Create a bank backed by asset_loader."""
        self._asset_loader: AssetLoader = asset_loader
        self._names: dict[str, str] = {}  # name -> path
        self._sounds: dict[str, object] = {}  # path -> Sound

    def get(self, name: str) -> object:
        """Return the pygame.mixer.Sound registered under name.

        Raises KeyError listing all available names if name is
        unknown. The first call for a given name loads the sound via
        AssetLoader.load_sound; subsequent calls return the cached
        object.
        """
        if name not in self._names:
            available = ", ".join(sorted(self._names)) or "(none)"
            raise KeyError(
                f"SoundBank: unknown sound name '{name}'. "
                f"Available names: {available}"
            )
        path = self._names[name]
        if path not in self._sounds:
            self._sounds[path] = self._asset_loader.load_sound(path)
        return self._sounds[path]

    def register(self, name: str, path: str) -> None:
        """Bind name to path without loading the sound yet.

        The actual pygame.mixer.Sound object is loaded lazily on
        the first get(name) call.
        """
        self._names[name] = path

    @property
    def available_names(self) -> list[str]:
        """Return all registered sound names, sorted alphabetically."""
        return sorted(self._names)