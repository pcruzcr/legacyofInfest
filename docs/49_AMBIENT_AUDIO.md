# Legacy of InFest — Ambient Audio Specification

**Document ID:** LOI-AUDIO-049
**Version:** 1.0.0
**Status:** Official
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

Ambient Audio is managed by `AudioManager` in `src/engine/audio/audio_manager.py`, which provides layered sound support including background music, dynamic music crossfade, sound effects, and ambient audio layers (wind, rain, machinery, etc.). The system gracefully degrades on missing assets — logs a warning and continues silently.

---

## 2. Audio Layers

### 2.1 Background Music
- `play_music(path)` — plays a single track (infinite loop by default)
- `stop_music()`, `pause_music()`, `resume_music()` — lifecycle
- Volume: `set_music_volume(0.0–1.0)`

### 2.2 Dynamic Music (Crossfade)
- `play_dynamic_music(calm_path, combat_path)` — loads two layers
- `set_music_intensity(target, speed)` — crossfade between calm (0.0) and combat (1.0)
- `update_dynamic_music(dt)` — drives interpolation per frame

### 2.3 Sound Effects (SFX)
- `play_sfx(name, volume)` — one-shot from SoundBank
- `play_stinger(name, volume)` — short music overlay
- `play_sfx_at(name, x, center_x, volume)` — stereo pan based on world X position

### 2.4 Ambient Layer
- `play_ambient(path, volume)` — looped ambient sound
- `crossfade_ambient(path, duration, volume)` — smooth transition between ambients
- `stop_ambient()`, `set_ambient_volume(vol)` — lifecycle

---

## 3. SoundBank

`src/engine/audio/sound_bank.py` — loads and manages sound effect assets. Called by AudioManager for all SFX playback.

---

## 4. Mute / Volume Control

- `toggle_mute()` — global mute toggle
- Individual volume controls for music, SFX, and ambient layers
- Muted state overrides all volume levels to 0

---

## 5. Implementation Status

**File:** `src/engine/audio/audio_manager.py` (231 lines) — all audio functionality in one class
**Status:** ✅ Complete — music, dynamic crossfade, SFX with panning, ambient layers, mute, volume control
**Note:** Visual `ambient_particles.py` is a separate VFX system; see `docs/20_ASSET_BIBLE.md` for audio asset conventions.
