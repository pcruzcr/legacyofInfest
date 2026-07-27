"""Accessibility and user-preference tests (AUD-021 / AUD-036).

Before the audit, ``settings.COLORBLIND_MODE`` and ``settings.SUBTITLES_ENABLED``
were module-level globals with no writer and, for subtitles, no reader either.
The options screen persisted the player's colourblind choice to a JSON file that
nothing loaded back, and the post-processing pass read a variable that was
permanently ``"off"`` — so selecting a colourblind mode never altered a single
rendered pixel. These tests assert the two ends are actually connected.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import user_settings


@pytest.fixture(autouse=True)
def _isolated_prefs():
    """Never touch the developer's real config file during tests."""
    user_settings.reset()
    yield
    user_settings.reset()


@pytest.fixture
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))
    return pygame.display.get_surface()


# ── the settings object itself ───────────────────────────────────


class TestUserSettings:
    def test_defaults_are_sane(self) -> None:
        prefs = user_settings.UserSettings()
        assert prefs.colorblind_mode == "off"
        assert prefs.subtitles_enabled is False
        assert 0.0 <= prefs.music_volume <= 1.0

    def test_round_trips_through_disk(self, tmp_path) -> None:
        target = tmp_path / "config.json"
        written = user_settings.UserSettings(
            colorblind_mode="tritanopia",
            subtitles_enabled=True,
            music_volume=0.33,
            difficulty="hard",
        )
        assert written.save(target) is True

        read_back = user_settings.UserSettings.load(target)
        assert read_back.colorblind_mode == "tritanopia"
        assert read_back.subtitles_enabled is True
        assert read_back.music_volume == pytest.approx(0.33)
        assert read_back.difficulty == "hard"

    def test_unknown_colorblind_mode_falls_back(self) -> None:
        assert user_settings.UserSettings(colorblind_mode="banana").colorblind_mode == "off"

    @pytest.mark.parametrize(("given", "expected"), [
        (99.0, 1.0), (-5.0, 0.0), ("nonsense", 0.0), (None, 0.0), (0.5, 0.5),
    ])
    def test_volume_is_clamped(self, given, expected) -> None:
        assert user_settings.UserSettings(music_volume=given).music_volume == pytest.approx(expected)

    def test_missing_file_yields_defaults(self, tmp_path) -> None:
        prefs = user_settings.UserSettings.load(tmp_path / "does_not_exist.json")
        assert prefs.colorblind_mode == "off"

    def test_corrupt_file_yields_defaults_without_raising(self, tmp_path) -> None:
        target = tmp_path / "config.json"
        target.write_bytes(b"{ this is not json")
        assert user_settings.UserSettings.load(target).colorblind_mode == "off"

    def test_non_object_json_yields_defaults(self, tmp_path) -> None:
        target = tmp_path / "config.json"
        target.write_bytes(b"[1, 2, 3]")
        assert user_settings.UserSettings.load(target).subtitles_enabled is False

    def test_unknown_keys_are_ignored(self, tmp_path) -> None:
        target = tmp_path / "config.json"
        target.write_bytes(b'{"colorblind_mode": "protanopia", "from_the_future": 7}')
        assert user_settings.UserSettings.load(target).colorblind_mode == "protanopia"

    def test_save_failure_is_reported_not_raised(self, tmp_path) -> None:
        # A directory where the file should be: writing must fail gracefully.
        blocked = tmp_path / "config.json"
        blocked.mkdir()
        assert user_settings.UserSettings().save(blocked) is False


# ── the colourblind filter actually filters ──────────────────────


class TestColorblindFilterIsConnected:
    @staticmethod
    def _filtered(mode: str) -> tuple[int, int, int]:
        from src.framework.vfx.post_processing import PostProcessing

        user_settings.set_settings(user_settings.UserSettings(colorblind_mode=mode))
        surface = pygame.Surface((16, 16))
        surface.fill((200, 40, 40))  # strongly red: worst case for red-green CVD
        PostProcessing()._apply_colorblind_filter(surface)
        return tuple(surface.get_at((4, 4))[:3])

    def test_off_leaves_pixels_untouched(self, display) -> None:
        assert self._filtered("off") == (200, 40, 40)

    @pytest.mark.parametrize("mode", ["protanopia", "deuteranopia", "tritanopia"])
    def test_each_mode_changes_the_image(self, display, mode: str) -> None:
        """The core regression: the preference must reach the renderer."""
        assert self._filtered(mode) != (200, 40, 40), (
            f"colorblind_mode={mode!r} left the image identical — the setting is "
            "not reaching the post-processing pass"
        )

    def test_modes_differ_from_each_other(self, display) -> None:
        results = {m: self._filtered(m) for m in ("protanopia", "deuteranopia", "tritanopia")}
        assert len(set(results.values())) == 3, f"modes are not distinct: {results}"


# ── subtitles have a reader ──────────────────────────────────────


class TestSubtitlesAreImplemented:
    @staticmethod
    def _overlay(enabled: bool):
        from src.engine.core.event_bus import EventBus
        from src.engine.ui.subtitle_overlay import SubtitleOverlay

        user_settings.set_settings(
            user_settings.UserSettings(subtitles_enabled=enabled),
        )
        bus = EventBus()
        return SubtitleOverlay(bus), bus

    def test_audio_event_produces_a_caption(self, display) -> None:
        from src.engine.core.events import Events

        overlay, bus = self._overlay(enabled=True)
        bus.emit(Events.SFX_BOSS_PHASE_CHANGE)
        bus.dispatch()

        captions = [entry[0] for entry in overlay._active]
        assert captions, "an informative audio event produced no caption"

    def test_nothing_is_captioned_when_disabled(self, display) -> None:
        from src.engine.core.events import Events

        overlay, bus = self._overlay(enabled=False)
        bus.emit(Events.SFX_BOSS_PHASE_CHANGE)
        bus.dispatch()
        assert overlay._active == []

    def test_repeated_sound_refreshes_rather_than_stacking(self, display) -> None:
        from src.engine.core.events import Events

        overlay, bus = self._overlay(enabled=True)
        for _ in range(6):
            bus.emit(Events.SFX_BOSS_PHASE_CHANGE)
            bus.dispatch()
        assert len(overlay._active) == 1, (
            "a repeating sound flooded the caption band, which makes captions "
            "unreadable — worse for accessibility than showing nothing"
        )

    def test_captions_expire(self, display) -> None:
        from src.engine.core.events import Events

        overlay, bus = self._overlay(enabled=True)
        bus.emit(Events.SFX_PLAYER_PARRY)
        bus.dispatch()
        assert overlay._active

        overlay.update(10.0)
        assert overlay._active == [], "captions never disappear"

    def test_destroy_unsubscribes(self, display) -> None:
        from src.engine.core.events import Events

        overlay, bus = self._overlay(enabled=True)
        overlay.destroy()
        bus.emit(Events.SFX_PLAYER_PARRY)
        bus.dispatch()
        assert overlay._active == []

    def test_rearm_restores_subscriptions(self, display) -> None:
        from src.engine.core.events import Events

        overlay, bus = self._overlay(enabled=True)
        overlay.destroy()
        overlay.rearm()
        bus.emit(Events.SFX_PLAYER_PARRY)
        bus.dispatch()
        assert overlay._active, "a re-entered scene lost its captions permanently"

    def test_draw_is_safe_with_no_captions(self, display) -> None:
        overlay, _ = self._overlay(enabled=True)
        overlay.draw(pygame.Surface((320, 240)))  # must not raise

    def test_only_informative_events_are_captioned(self) -> None:
        """Footsteps and jumps must not be captioned.

        Captioning every sound produces a wall of text that hides the
        meaningful captions — a common accessibility anti-pattern.
        """
        from src.engine.core.events import Events
        from src.engine.ui.subtitle_overlay import CAPTIONS

        for noisy in (Events.SFX_PLAYER_JUMP, Events.SFX_PLAYER_LAND):
            assert noisy not in CAPTIONS


# ── constants are immutable ──────────────────────────────────────


class TestBalanceTableIsImmutable:
    def test_combo_multipliers_cannot_be_mutated(self) -> None:
        """AUD-021: as a list, any module could silently rebalance combat."""
        from src.engine.core import settings

        assert isinstance(settings.COMBO_DAMAGE_MULT, tuple)
        with pytest.raises((AttributeError, TypeError)):
            settings.COMBO_DAMAGE_MULT.append(99.0)  # type: ignore[attr-defined]

    def test_runtime_preferences_are_no_longer_module_globals(self) -> None:
        from src.engine.core import settings

        for leaked in ("COLORBLIND_MODE", "SUBTITLES_ENABLED"):
            assert not hasattr(settings, leaked), (
                f"settings.{leaked} is back — player preferences belong in "
                "user_settings, where they are persisted and validated"
            )
