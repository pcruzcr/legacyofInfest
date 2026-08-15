"""
Module: asset_loader
System: engine.utils

Centralized asset manager for Legacy of InFest.

Responsibilities
----------------
- Cached image loading
- Cached sound loading
- Cached font loading
- Music playback
- Placeholder generation
- Sprite sheet loading
- Automatic scaling
"""

from __future__ import annotations

import logging
from pathlib import Path

import pygame

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


PLACEHOLDER_SIZES = {
    "player": (20, 32),
    "enemies": (24, 24),
    "bosses": (64, 64),
    "ui": (32, 32),
    "tilesets": (16, 16),
    "backgrounds": (320, 224),
    "splash": (320, 224),
}


PLACEHOLDER_COLORS = {
    "player": (40, 140, 255),
    "enemies": (220, 60, 60),
    "bosses": (180, 40, 40),
    "tilesets": (90, 90, 90),
    "ui": (220, 220, 220),
    "backgrounds": (35, 35, 35),
    "splash": (20, 20, 40),
}


class AssetLoader:
    """
    Centralized asset manager with instance-based caching.

    Instance-based design (ARC-005): Internal ``_``-prefixed methods use
    instance state for proper test isolation. Classmethod wrappers with the
    public names (``load_image``, ``load_font``, etc.) delegate to a default
    singleton instance so existing code continues to work unchanged.

    Usage (existing code, via default instance):
        img = AssetLoader.load_image('path')

    Usage (new code, explicit instance injection):
        loader = AssetLoader()
        img = loader._load_image('path')
    """

    _default_instance: AssetLoader | None = None

    # Images above this many cached entries trigger eviction of the
    # least-recently-used ones. Sized generously: a stage plus its UI is well
    # under this, so eviction only kicks in on pathological churn.
    MAX_CACHED_IMAGES = 512

    # AUD-484: MAX_CACHED_IMAGES bounds the cache by *count*, never by memory.
    # That was invisible with 16x16 pixel-art sprites — 512 of those are a few
    # MB — but the bound stops protecting anything the day an asset pipeline
    # starts shipping high-resolution art: 512 entries of multi-MB textures is
    # gigabytes, not a "pathological churn" edge case. 256 MiB is generous for
    # today's pixel-art content (eviction still only kicks in on churn) and is
    # the ceiling that keeps a future HD asset pass from growing unbounded.
    MAX_CACHED_BYTES = 256 * 1024 * 1024

    def __init__(self) -> None:
        self._images: dict[str, pygame.Surface] = {}
        # AUD-484: bytes per cached image, keyed the same as ``_images``, so
        # eviction can subtract the *exact* size freed instead of re-summing
        # every surface on every insert.
        self._image_bytes: dict[str, int] = {}
        self._images_bytes: int = 0
        self._fonts: dict[str, pygame.font.Font] = {}
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._missing: set[str] = set()
        # Number of live scopes (scenes) currently using the cache. Only the
        # last one to leave may clear it.
        self._scopes: int = 0

    # ── Internal instance methods ──────────────────────────────

    def _enter_scope(self) -> None:
        """Register a consumer (typically a scene) as using the cache."""
        self._scopes += 1

    def _leave_scope(self) -> None:
        """Release a consumer; clear the cache only when the last one leaves.

        AUD-025: ``StageScene.on_exit()`` called the *global* ``clear_cache()``.
        With a paused scene still on the stack below, that freed nothing — the
        paused scene's surfaces kept the pixel data alive — while forcing every
        subsequent lookup to re-decode from disk. The result was cache thrash
        with none of the memory benefit. Reference counting means the cache is
        only actually dropped when nothing is using it any more.
        """
        self._scopes = max(0, self._scopes - 1)
        if self._scopes == 0:
            self._clear_cache()

    def _clear_cache(self) -> None:
        """Release all cached images/fonts/sounds to free memory."""
        self._images.clear()
        self._image_bytes.clear()
        self._images_bytes = 0
        self._fonts.clear()
        self._sounds.clear()
        self._missing.clear()

    @staticmethod
    def _surface_bytes(surface: pygame.Surface) -> int:
        """Estimate a surface's footprint: width × height × bytes-per-pixel.

        AUD-484: ignores row padding/pitch, so it under-counts slightly on
        some platforms — that is fine for an eviction *budget*, the same way
        the leak detector in ``memoria_de_textura.py`` deliberately has no
        byte threshold: this number only has to be consistently comparable
        across surfaces, not byte-exact.
        """
        width, height = surface.get_size()
        return width * height * surface.get_bytesize()

    def _evict_if_needed(self) -> None:
        """Drop the oldest cached images past ``MAX_CACHED_IMAGES`` entries
        or past ``MAX_CACHED_BYTES`` of estimated memory, whichever comes
        first.

        The cache was previously unbounded by count, and its keys include
        scale, size, alpha and smoothing — so a single source file requested
        at several sizes multiplied into several entries with nothing ever
        reclaiming them. ``dict`` preserves insertion order, which gives us
        FIFO eviction for free; that is a good enough approximation of LRU
        for asset loading, where access is dominated by stage-scoped bursts.

        AUD-484: the count bound alone protected memory only by accident —
        it assumed every entry was cheap. Evicting until *both* budgets are
        satisfied means a handful of oversized textures gets reclaimed long
        before 512 entries accumulate, instead of only being caught once the
        count also happens to overflow.
        """
        # Snapshot insertion order *before* mutating the dict — deleting from
        # ``self._images`` while a live iterator over it is open raises
        # ``RuntimeError: dictionary changed size during iteration``.
        candidates = list(self._images)
        evicted = 0
        for key in candidates:
            if (
                len(self._images) <= self.MAX_CACHED_IMAGES
                and self._images_bytes <= self.MAX_CACHED_BYTES
            ):
                break
            self._images_bytes -= self._image_bytes.pop(key, 0)
            del self._images[key]
            evicted += 1
        if evicted:
            logger.debug("AssetLoader: evicted %d cached image(s)", evicted)

    def _resolve(self, path: str | Path) -> Path:
        """Resolve an asset path, refusing to escape the project directory.

        AUD-026: this used to join any caller-supplied path onto
        ``PROJECT_ROOT`` with no containment check. Stage geometry, sprite paths
        and tileset references all come from student-authored TMX files, so a
        path like ``../../../../etc/passwd`` — or, on Windows, one pointing at a
        user's documents — was reachable from data the engine is designed to
        load from untrusted authors. Absolute paths are still honoured, because
        tooling legitimately passes them, but relative paths must stay inside
        the project.
        """
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate

        for base in (PROJECT_ROOT / "custom_assets", PROJECT_ROOT):
            resolved = (base / candidate).resolve()
            try:
                resolved.relative_to(PROJECT_ROOT.resolve())
            except ValueError:
                logger.error(
                    "AssetLoader: refusing path %r — it resolves to %s, outside "
                    "the project directory", str(path), resolved,
                )
                # Return a path that cannot exist rather than raising, so a
                # malformed stage degrades to placeholder art instead of
                # crashing the game.
                return PROJECT_ROOT / "__rejected__" / candidate.name
            if base.name == "custom_assets" and not resolved.exists():
                continue
            return resolved
        return (PROJECT_ROOT / candidate).resolve()

    @staticmethod
    def _display_ready() -> bool:
        """True when a display surface exists, so ``convert_alpha()`` can work."""
        return pygame.display.get_init() and pygame.display.get_surface() is not None

    def _load_image(
        self,
        path: str | Path,
        *,
        scale: float | None = None,
        size: tuple[int, int] | None = None,
        alpha: bool = True,
        smooth: bool = False,
    ) -> pygame.Surface:
        real_path = self._resolve(path)
        key = f"{real_path}|{scale}|{size}|{alpha}|{smooth}"
        if key in self._images:
            return self._images[key]

        image: pygame.Surface | None = None
        try:
            image = pygame.image.load(real_path)
        except (pygame.error, FileNotFoundError, PermissionError):
            image = None
            if str(real_path) not in self._missing:
                logger.warning("Missing asset: %s", real_path)
                self._missing.add(str(real_path))
        else:
            # AUD-024: convert()/convert_alpha() require a display surface. When
            # called before pygame.display.set_mode(), pygame raises
            # pygame.error — which the old code caught with the file-not-found
            # handler, so the game silently served placeholder art for every
            # asset and logged "Missing asset: <path>" for files that exist. The
            # cause and the symptom were unrelated, which made it very hard to
            # diagnose. Distinguish the two cases explicitly.
            if self._display_ready():
                image = image.convert_alpha() if alpha else image.convert()
            else:
                # Keep the unconverted surface: it renders correctly, just
                # slower. Crucially it is the *real* artwork, not a placeholder,
                # and it is not cached as if the file were missing.
                logger.warning(
                    "AssetLoader: no display surface yet — %s loaded unconverted. "
                    "Blitting will be slower until a display mode is set; call "
                    "pygame.display.set_mode() before loading assets.",
                    real_path.name,
                )

        if image is None:
            category = real_path.parent.name
            placeholder_size = PLACEHOLDER_SIZES.get(category, (32, 32))
            color = PLACEHOLDER_COLORS.get(category, (120, 120, 120))
            image = pygame.Surface(placeholder_size, pygame.SRCALPHA)
            image.fill(color)
            pygame.draw.rect(image, (255, 255, 255), image.get_rect(), 1)

        if size:
            transform_fn = pygame.transform.smoothscale if smooth else pygame.transform.scale
            image = transform_fn(image, size)
        elif scale:
            transform_fn = pygame.transform.smoothscale if smooth else pygame.transform.scale
            image = transform_fn(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
        self._images[key] = image
        size_bytes = self._surface_bytes(image)
        self._image_bytes[key] = size_bytes
        self._images_bytes += size_bytes
        self._evict_if_needed()
        return image

    def _load_font(self, path: str | Path | None, size: int) -> pygame.font.Font:
        key = f"{path}:{size}"
        if key in self._fonts:
            return self._fonts[key]
        try:
            if path is None:
                font = pygame.font.Font(None, size)
            else:
                font = pygame.font.Font(self._resolve(path), size)
        except (pygame.error, FileNotFoundError, PermissionError):
            font = pygame.font.Font(None, size)
        self._fonts[key] = font
        return font

    def _load_sound(self, path: str | Path) -> pygame.mixer.Sound | None:
        real = str(self._resolve(path))
        if real in self._sounds:
            return self._sounds[real]
        try:
            sound = pygame.mixer.Sound(real)
        except (pygame.error, FileNotFoundError, PermissionError):
            sound = None
        self._sounds[real] = sound
        return sound

    def _load_sprite_sheet(
        self,
        path: str | Path,
        frame_width: int,
        frame_height: int,
    ) -> list[pygame.Surface]:
        if frame_width <= 0 or frame_height <= 0:  # BUG-081 FIX: validar antes de dividir
            raise ValueError(
                f"AssetLoader: invalid frame size ({frame_width}x{frame_height}) "
                f"for {path}"
            )
        sheet = self._load_image(path)
        frames = []
        cols = sheet.get_width() // frame_width
        rows = sheet.get_height() // frame_height
        for y in range(rows):
            for x in range(cols):
                rect = pygame.Rect(x * frame_width, y * frame_height, frame_width, frame_height)
                frames.append(sheet.subsurface(rect))
        return frames

    # ── Classmethod wrappers (backward compatible) ─────────────

    @classmethod
    def _get_instance(cls) -> AssetLoader:
        if cls._default_instance is None:
            cls._default_instance = AssetLoader()
        return cls._default_instance

    @classmethod
    def clear_cache(cls) -> None:
        """Unconditionally drop every cached asset.

        Use this in test teardown and at shutdown. Scenes should call
        :meth:`enter_scope` / :meth:`leave_scope` instead, so that a scene
        exiting while another is still paused underneath does not throw away
        assets the paused scene is still holding (AUD-025).
        """
        cls._get_instance()._clear_cache()

    @classmethod
    def enter_scope(cls) -> None:
        """Mark the start of a cache-using scope (called by scenes on enter)."""
        cls._get_instance()._enter_scope()

    @classmethod
    def leave_scope(cls) -> None:
        """End a cache-using scope; clears the cache when the last one leaves."""
        cls._get_instance()._leave_scope()

    @classmethod
    def load_image(
        cls,
        path: str | Path,
        *,
        scale: float | None = None,
        size: tuple[int, int] | None = None,
        alpha: bool = True,
        smooth: bool = False,
    ) -> pygame.Surface:
        return cls._get_instance()._load_image(path, scale=scale, size=size, alpha=alpha, smooth=smooth)

    @classmethod
    def load_font(cls, path: str | Path | None, size: int) -> pygame.font.Font:
        return cls._get_instance()._load_font(path, size)

    @classmethod
    def load_sound(cls, path: str | Path) -> pygame.mixer.Sound | None:
        return cls._get_instance()._load_sound(path)

    @classmethod
    def load_sprite_sheet(
        cls, path: str | Path, frame_width: int, frame_height: int,
    ) -> list[pygame.Surface]:
        return cls._get_instance()._load_sprite_sheet(path, frame_width, frame_height)
