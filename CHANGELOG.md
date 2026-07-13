# Changelog

## [1.0.0] - 2025-07-10

### Added

- **Initial release** of Legacy of InFest — an educational game engine for Computer Graphics, Image Processing, Computer Vision, and Pattern Recognition.
- **10 interactive labs** spanning Units II–IX for visual theory learning.
- **Demo scenes** covering filters, segmentation, ML, transformations, interpolation, and procedural noise.
- **DI Container (SceneRegistry)** for lazy-loading scenes with a reusable ParamPanel widget.
- **Complete 2D stage system** with physics, collisions, camera, HUD, and boss encounters.
- **Processing framework:** `ColorTools`, `CurveTools`, `FilterTools`, `VisionTools`, `PatternRecognitionTools`.
- **Debug overlay** (F3 key) showing FPS, event queue snapshot, and module tree.
- **8 enemy types:** Walker, Shooter, Flying (Bezier/patrol), Charger, Brute, Archer, Assassin, Caster.
- **Boss system** (`BossBase`) with `boss_venado` implementation.
- **Dynamic music system** (`DynamicMusic`) with zone-based audio transitions.
- **Sound effects pipeline** via EventBus: 15 SFX events wired to `SoundBank` + `AudioManager`.
- **VFX system:** particle system, lighting, post-processing, fog of war, water effects, trail system, hit effects, damage numbers, ambient particles.
- **Stage systems:** camera with parallax, checkpoints, collision system (axis-separated), drawing system, hazard system, progression system.
- **UI components:** HUD, message box, minimap, tutorial overlay, screen banner, bitmap font.
- **Asset pipeline:** `AssetLoader`, `Spritesheet`, TMX loader via `StageLoader`, parallax backgrounds.
- **Input system:** `ActionMap` + `InputManager` with configurable keyboard bindings.
- **Save/load system:** `SaveManager` with checkpoint persistence, inventory, achievements.
- **Student template system** for lab exercises.
- **369 automated tests** with pytest.
- **Exam generation and asset validation scripts** (`scripts/generate_exam.py`, `scripts/validate_assets.py`).
- **Tooling:** `generate_stage0_tmx.py`, `pixel_asset_generator.py`, `build_dataset.py`, `convert_audio.py`, `validate_stage.py`.

### Fixed

- **Collision system** — rewired to axis-separated resolution (X → resolve X → Y → resolve Y), fixing wall-climb/teleport bug.
- **One-way platform collision** — corrected via `_prev_foot_y` + straddle detection; Stage 0 zones A/C now use Solid tiles instead of Platform tiles.
- **Player spawn point** — TMX Y coordinate now correctly treated as feet position (adjusted by 32px).
- **Player states** — `_pending_jump` / `_pending_jump_timer` attributes added to `Player.__init__` with 8-frame buffer to prevent bounce-off on one-way platforms.
- **Collision rect depth** — X-skip heuristic uses `tile.top >= player_rect.centery` for reliable platform detection with merged collision rects.
- **14 crash bugs** resolved across 3 commits, plus 3 gameplay bugs (one-way platforms, floor/health/completion of Venado boss).
- **Text rendering** — font sizes adjusted (7→12, 9→15, 11→18), anti-aliasing enabled, `SDL_HINT_RENDER_SCALE_QUALITY=0` for crisp text.

### Changed

- **HUD timer** — migrated from spritesheet (`fonts/hud_digits.png`) to TTF font (`PixeloidSans.ttf`) for higher quality.
- **Message box** — repositioned from Y=196 (bottom) to Y=0 (top) to avoid overlap with health/timer HUD.
- **SoundBank** — integrated via EventBus; `SoundBank.load_all()` scans `assets/sfx/` recursively; 15 SFX events defined and wired to stage scenes.
- **API contracts** — updated `Action` enum, `SoundBank`, and `AssetLoader` documentation to match implementation signatures.
- **EventBus** — exposed read-only `queue_snapshot` and `subscribers_snapshot` properties for debug overlay.

### Known Issues

- **GAP-002 — Collision rect depth heuristic:** `tile.top >= player_rect.centery` may fail with abnormally tall merged collision rects. No known cases currently trigger this.
- **GAP-004 — Background zone missing in Stage 0 TMX:** `background_zone` property absent; stage runs without parallax backgrounds. StageLoader support exists — requires TMX update.
- **GAP-014 — Collision rect runtime visualization:** Debug overlay (F1) draws collision rects but no tooltip shows `prev_bottom`, `tile.top`, or `velocity.y` on hover/pause.

For full gap tracking, see `KNOWN_GAPS.md`.



--- Traducción al Español ---

*Este documento está disponible en inglés. Para una traducción completa al español, contacte al profesor.*
