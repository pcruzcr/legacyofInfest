"""
Module: user_settings
System: engine.core
Academic Unit: N/A

Player-controlled preferences: accessibility, volumes, difficulty.

Why this module exists (AUD-021 / AUD-036)
------------------------------------------
``settings.py`` mixes two very different things: engine constants that must
never change at runtime (tile size, gravity, internal resolution) and player
preferences that must. The preferences were declared as bare module-level
globals — ``COLORBLIND_MODE``, ``SUBTITLES_ENABLED`` — which meant:

* any module could mutate them from anywhere, with no audit trail;
* they were never persisted, so a preference was lost on quit;
* they leaked between tests, because a test that set one left it set;
* and most importantly, **nothing ever wrote to them**. The options screen
  saved ``colorblind_mode`` into ``config.json`` and the post-processing pass
  read ``settings.COLORBLIND_MODE``, but no code connected the two. A player
  could select "deuteranopia", see it persist across restarts in the UI, and
  never have a single frame actually filtered. ``SUBTITLES_ENABLED`` had no UI
  and no reader at all.

Preferences now live in one owned, persisted, injectable object. Reads go
through :func:`get`; writes go through :meth:`UserSettings.save`.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Final

import orjson

logger = logging.getLogger(__name__)

CONFIG_FILENAME: Final = "config.json"

COLORBLIND_MODES: Final[tuple[str, ...]] = (
    "off", "protanopia", "deuteranopia", "tritanopia",
)


def user_data_dir() -> Path:
    """The per-user directory this game stores its state in.

    Deliberately *not* inside the project directory: a packaged build may be
    installed somewhere read-only (Program Files, /Applications), and writing
    player state into the install tree is what put ``saves/slot_1.json`` into
    version control in the first place.

    AUD-032: four modules — ``achievements``, ``keybinding_scene``,
    ``title_scene`` and this one — each open-coded
    ``Path(os.environ.get("APPDATA", "~/.config")) / "legacyofinfest" / ...``.
    Besides being duplicated four ways, that spelling ignores
    ``XDG_CONFIG_HOME`` on Linux and mis-locates data on macOS. One helper, one
    place to fix.
    """
    import os

    if os.name == "nt":
        base = os.environ.get("APPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Roaming"
    else:
        base = os.environ.get("XDG_CONFIG_HOME")
        root = Path(base) if base else Path.home() / ".config"
    return root / "legacyofinfest"


def _default_config_path() -> Path:
    """Full path to the preferences file."""
    return user_data_dir() / CONFIG_FILENAME


@dataclass
class UserSettings:
    """Persisted player preferences.

    Field names match the keys written by the options screen, so an existing
    ``config.json`` is read without migration.
    """

    music_volume: float = 0.7
    sfx_volume: float = 0.8
    difficulty: str = "normal"
    colorblind_mode: str = "off"
    subtitles_enabled: bool = False

    # Not persisted: resolved at load time so callers need not handle None.
    _path: Path | None = field(default=None, repr=False, compare=False)

    # ── validation ─────────────────────────────────────────────

    def __post_init__(self) -> None:
        self.music_volume = _clamp01(self.music_volume)
        self.sfx_volume = _clamp01(self.sfx_volume)
        if self.colorblind_mode not in COLORBLIND_MODES:
            logger.warning(
                "UserSettings: unknown colorblind_mode %r — falling back to 'off'",
                self.colorblind_mode,
            )
            self.colorblind_mode = "off"
        self.subtitles_enabled = bool(self.subtitles_enabled)

    # ── persistence ────────────────────────────────────────────

    @classmethod
    def load(cls, path: Path | None = None) -> UserSettings:
        """Read preferences from disk, falling back to defaults."""
        resolved = path or _default_config_path()
        try:
            raw = orjson.loads(resolved.read_bytes())
        except FileNotFoundError:
            return cls(_path=resolved)
        except (OSError, ValueError, TypeError) as exc:
            logger.warning(
                "UserSettings: could not read %s (%s) — using defaults",
                resolved, exc,
            )
            return cls(_path=resolved)

        if not isinstance(raw, dict):
            logger.warning("UserSettings: %s is not an object — using defaults", resolved)
            return cls(_path=resolved)

        # pylint: disable=no-member  # `__dataclass_fields__` lo genera @dataclass
        known = {f for f in cls.__dataclass_fields__ if not f.startswith("_")}
        kwargs: dict[str, Any] = {k: v for k, v in raw.items() if k in known}
        try:
            return cls(**kwargs, _path=resolved)
        except (TypeError, ValueError) as exc:
            logger.warning(
                "UserSettings: %s has invalid values (%s) — using defaults",
                resolved, exc,
            )
            return cls(_path=resolved)

    def save(self, path: Path | None = None) -> bool:
        """Write preferences to disk. Returns True on success.

        Never raises: failing to persist a volume slider must not crash a game.
        """
        target = path or self._path or _default_config_path()
        payload = {
            k: v for k, v in asdict(self).items() if not k.startswith("_")
        }
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
        except OSError as exc:
            logger.warning("UserSettings: could not write %s (%s)", target, exc)
            return False
        self._path = target
        return True


def _clamp01(value: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


# ── process-wide accessor ──────────────────────────────────────
#
# Preferences are genuinely global to a running game, so a single instance is
# the right model — but unlike the previous bare module globals it is loaded
# once, validated, persisted, and replaceable in tests via set_settings().

_current: UserSettings | None = None


def get() -> UserSettings:
    """The active preferences, loading them from disk on first access."""
    global _current
    if _current is None:
        _current = UserSettings.load()
    return _current


def set_settings(settings_obj: UserSettings) -> None:
    """Replace the active preferences (used by App at startup, and by tests)."""
    global _current
    _current = settings_obj


def reset() -> None:
    """Forget the loaded preferences so the next get() re-reads them."""
    global _current
    _current = None
