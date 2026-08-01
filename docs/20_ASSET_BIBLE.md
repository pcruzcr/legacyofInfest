---
document_id: "LOI-ASSET-020"
title: "Legacy of InFest — Asset Bible"
aliases: ["Asset Bible"]
tags: ["asset", "bible", "art", "audio"]
description: "Every visual/audio asset, path, dimensions, palette"
source: "docs/20_ASSET_BIBLE.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Asset Bible

**Document ID:** LOI-ASSET-020  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires LOI-CODEX-002, LOI-WORLD-016, LOI-BOSS-017, LOI-ROSTER-018  
**Audience:** Professor, Students, Artists, AI coding assistants

---

## 1. Overview

This document defines every visual and audio asset required by Legacy of InFest. It is the authoritative reference for artists, students creating custom assets, and AI coding assistants generating asset loading code.

Every asset listed here has a defined path, format, dimensions, palette constraints, and usage context. Assets not listed here are either student-created (placed in `student_assets/`) or are generated at runtime by the processing pipeline.

---

## 2. Global Asset Standards

### 2.1 Visual Standards

| Property | Standard |
|---|---|
| Pixel format | PNG with alpha channel (RGBA) |
| Color depth | 8 bits per channel |
| Palette constraint | Maximum 16 colors per sprite sheet |
| Global palette | Maximum 256 colors across the entire game |
| Pixel size | 1:1 — no sub-pixel rendering |
| Anti-aliasing | Never |
| Transparency | Binary (fully transparent or opaque) OR smooth alpha (for effects only) |
| Internal resolution | All assets designed for the 800×600 internal render |

### 2.2 Sprite Sheet Format

All animated sprites are **horizontal sprite sheets**: frames arranged left to right, equal width, top-left origin.

```
[Frame 0][Frame 1][Frame 2][Frame 3]...
```

Sheet width = frame_width × frame_count  
Sheet height = frame_height (single row only — no multi-row sheets)

### 2.3 Tile Format

| Property | Standard |
|---|---|
| Tile size | 16×16 pixels |
| Sheet arrangement | Row-major grid |
| Maximum tiles per set | 256 |
| Sheet dimensions | 128×128 px (8×8 tile grid) |

### 2.4 Audio Standards

| Property | Music | SFX |
|---|---|---|
| Format | OGG Vorbis | WAV or OGG |
| Sample rate | 44100 Hz | 22050 Hz |
| Bit depth | 16-bit | 16-bit |
| Channels | Stereo | Mono |
| Loop point | Must be defined for BGM | N/A |
| Volume normalization | -12 dBFS peak | -6 dBFS peak |

---

## 3. Directory Structure

```
assets/
├── sprites/
│   ├── player/
│   ├── enemies/
│   │   ├── zone1/
│   │   ├── zone2/
│   │   └── zone3/
│   ├── bosses/
│   └── shared/
│       ├── checkpoint.png
│       ├── torch_anim.png
│       ├── fountain_anim.png
│       └── spirit_echo_overlay.png
├── tilesets/
│   ├── tileset_stage0.png
│   ├── tileset_jungle_stone.png
│   ├── tileset_cafeteria.png
│   ├── tileset_aulas.png
│   ├── tileset_datacenter.png
│   ├── tileset_heredia_stone.png
│   ├── tileset_heredia_interior.png
│   └── tileset_cemetery.png
├── backgrounds/
│   ├── stage0/
│   ├── zone1/
│   ├── zone2/
│   ├── zone3/
│   └── final/
├── ui/
│   ├── portrait_normal.png
│   ├── portrait_hurt.png
│   ├── portrait_critical.png
│   ├── portrait_dead.png
│   ├── banner_top.png
│   ├── banner_bottom.png
│   ├── hud_frame.png
│   ├── message_arrow.png
│   ├── menu_arrow.png
│   ├── heart_sparkle.png
│   └── relics/
│       ├── relic_pepita.png
│       ├── relic_perla.png
│       ├── relic_fragment1.png
│       ├── relic_fragment2.png
│       └── relic_fragment3.png
├── fonts/
│   ├── hud_digits.png
│   ├── message_font.png
│   ├── banner_large.png
│   ├── banner_medium.png
│   ├── gameover_font.png
│   └── menu_font.png
├── music/
│   ├── bgm_splash.ogg
│   ├── bgm_title.ogg
│   ├── bgm_story.ogg
│   ├── bgm_stage0.ogg
│   ├── bgm_zone1_traverse.ogg
│   ├── bgm_zone1_boss.ogg
│   ├── bgm_zone2_traverse.ogg
│   ├── bgm_zone2_boss.ogg
│   ├── bgm_zone3_traverse.ogg
│   ├── bgm_zone3_boss.ogg
│   ├── bgm_final_approach.ogg
│   └── bgm_paburu.ogg
└── sfx/
    ├── player/
    ├── enemies/
    ├── bosses/
    ├── ui/
    └── environment/
```

---

## 4. Player Sprites

All player sprites are located in `assets/sprites/player/`.  
Frame size: **32×32 pixels** for all animations.

| File | Frames | FPS | Loop | State |
|---|---|---|---|---|
| `player_idle.png` | 4 | 8 | Yes | IDLE |
| `player_walk.png` | 8 | 12 | Yes | WALKING |
| `player_jump.png` | 4 | 12 | No (hold last) | JUMPING |
| `player_fall.png` | 3 | 8 | Yes | FALLING |
| `player_crouch.png` | 3 | 8 | No (hold last) | CROUCHING |
| `player_short_attack.png` | 6 | 18 | No | SHORT_ATTACK |
| `player_long_attack.png` | 10 | 16 | No | LONG_ATTACK |
| `player_hurt.png` | 4 | 12 | No | HURT |
| `player_die.png` | 8 | 10 | No | DYING |

**Palette:**  
The player (hooded protagonist) uses a restricted palette of exactly 12 colors:
- 3 hood shadow tones (deep gray-blue, mid gray-blue, light gray)
- 2 skin tones (warm tan, shadow)
- 2 cloth tones (dark navy, mid navy)
- 2 rope/belt tones (brown, dark brown)
- 1 eye glow (pale gold — visible in very dark scenes only)
- 1 pure black (outline)
- 1 pure transparent

---

## 5. Enemy Sprites

Enemy sprites use generic zone-based naming. Zone-specific thematic variants
are aspirational; the sprites on disk are shared across all enemy types within
a zone and use the concrete type prefix (`walker`, `fly`, `shoot`).

### 5.1 Walker (universal)

Location: `assets/sprites/enemies/`

| File | Enemy | Frame Size | Frames | FPS | Loop |
|---|---|---|---|---|---|
| `enemy_walker_walk.png` | Walker | 20×16 | 6 | 10 | Yes |

### 5.2 Zone-sprited Enemies

Location: `assets/sprites/enemies/zoneN/`

| File | Enemy | Frames | FPS |
|---|---|---|---|
| `enemy_zoneN_walk.png` | Zone walker | 6 | 10 |
| `enemy_zoneN_hurt.png` | Any (damage) | 3 | 12 |
| `enemy_zoneN_die.png` | Any (death) | 5 | 8 |
| `enemy_fly_zoneN.png` | Zone flyer | 4 | 12 |
| `enemy_shoot_zoneN.png` | Zone shooter | 4 | 6 |

Where `N` is the zone number (1–3). All sprites use 16×16 frame size
(placeholder; actual frame sizes depend on the thematic replacement).

---

## 6. Boss Sprites

Location: `assets/sprites/bosses/`

### 6.1 El Venado Sagrado

Frame size: 48×48 px

| File | Frames | FPS | Loop | Status |
|---|---|---|---|---|
| `boss_venado_drift.png` | 6 | 8 | Yes | ✅ |
| `boss_venado_stomp.png` | 8 | 12 | No | ✅ |
| `boss_venado_charge.png` | 6 | 14 | No | ✅ |
| `boss_venado_frenzy_drift.png` | 6 | 14 | Yes | ✅ |
| `boss_venado_vine.png` | 10 | 12 | No | ✅ |
| `boss_venado_hurt.png` | 4 | 12 | No | ✅ |
| `boss_venado_death.png` | 12 | 8 | No | ✅ |
| `boss_venado_skull.png` | 1 | — | — | ⚠️ Placeholder |
| `boss_venado_proyectil_vine.png` | 4 | 10 | Yes | ⚠️ Placeholder |

**Palette Notes:** Bone white (`#E8DCC8`), moss dark (`#2D4A1E`), moss mid (`#4A7832`), earth brown (`#6B4423`), fungus cream (`#C8B896`), beetle black (`#0A0A0A`), root tan (`#8C6E3C`), shadow (`#1A1A2E`) + transparent.

### 6.2 El Rey Terciopelo

Phase 1 frame size: 40×56 px. Sub-boss (Phase 2) frame size: 24×28 px.

| File | Frames | FPS | Loop | Status |
|---|---|---|---|---|
| `boss_rey_walk.png` | 8 | 10 | Yes | ✅ |
| `boss_rey_spit.png` | 6 | 12 | No | ✅ |
| `boss_rey_split.png` | 8 | 10 | Yes | ✅ |
| `boss_rey_metad_walk.png` | 6 | 12 | Yes | ⚠️ Placeholder |
| `boss_rey_merge.png` | 6 | 8 | No | ✅ |
| `boss_rey_rampage.png` | 8 | 16 | Yes | ✅ |
| `boss_rey_hurt.png` | 4 | 12 | No | ✅ |
| `boss_rey_death.png` | 14 | 8 | No | ✅ |
| `boss_rey_venom_glob.png` | 3 | 8 | Yes | ⚠️ Placeholder |

**Palette Notes:** Terciopelo tan (`#C8A264`), terciopelo dark (`#4A3218`), terciopelo mid (`#8C6432`), decay gray (`#7D7D7D`), decay dark (`#3C3C3C`), venom green (`#32A050`), venom bright (`#50C878`), shadow (`#0A0A14`).

### 6.3 El Gavilán Camionero Mascarero

Frame size: 56×40 px (wide — wingspan)

| File | Frames | FPS | Loop | Status |
|---|---|---|---|---|
| `boss_gavilan_glide.png` | 8 | 10 | Yes | ✅ |
| `boss_gavilan_dive.png` | 6 | 16 | No | ✅ |
| `boss_gavilan_hover.png` | 4 | 8 | Yes | ✅ |
| `boss_gavilan_storm.png` | 8 | 12 | No | ✅ |
| `boss_gavilan_masked.png` | 6 | 14 | Yes | ✅ |
| `boss_gavilan_hurt.png` | 4 | 12 | No | ✅ |
| `boss_gavilan_death.png` | 16 | 8 | No | ✅ |
| `boss_gavilan_mask_frag.png` | 4 | 12 | No | ⚠️ Placeholder |
| `boss_gavilan_feather.png` | 3 | 10 | Yes | ⚠️ Placeholder |

**Palette Notes:** Hawk brown (`#8C5A28`), hawk tan (`#C88C3C`), hawk white (`#E8DCC8`), mask gold (`#D4A017`), mask dark gold (`#8C6800`), mask teal (`#1E6B6B`), mask red-orange (`#D45A00`), eye glow (`#50FF50`), shadow black (`#0A0A0A`).

### 6.4 El Gran Shaman Paburu

Multiple frame sizes per form.

| File | Form | Frame Size | Frames | FPS | Loop | Status |
|---|---|---|---|---|---|---|
| `boss_paburu_stone.png` | 1 | 64×64 | 4 | 6 | Yes | ✅ |
| `boss_paburu_stone_slam.png` | 1 | 64×64 | 8 | 12 | No | ✅ |
| `boss_paburu_stone_crack.png` | 1→2 | 64×64 | 8 | 8 | No | ⚠️ Placeholder |
| `boss_paburu_mask.png` | 2 | 56×72 | 6 | 10 | Yes | ✅ |
| `boss_paburu_mask_wave.png` | 2 | 56×72 | 8 | 12 | No | ⚠️ Placeholder |
| `boss_paburu_gold.png` | 3A | 32×32 | 6 | 14 | Yes | ✅ |
| `boss_paburu_black.png` | 3B | 32×32 | 6 | 14 | Yes | ✅ |
| `boss_paburu_relic_atk.png` | 3A/B | 32×32 | 10 | 14 | No | ⚠️ Placeholder |
| `boss_paburu_spirit.png` | 4 | 64×80 | 8 | 10 | Yes | ✅ |
| `boss_paburu_spirit_surge.png` | 4 | 64×80 | 12 | 14 | No | ⚠️ Placeholder |
| `boss_paburu_hurt.png` | All | 64×64 | 4 | 12 | No | ✅ |
| `boss_paburu_transcend.png` | Death | 64×64 | 20 | 8 | No | ⚠️ Placeholder |
| `boss_paburu_stone_proyectil.png` | Form 1 | 8×8 | 3 | 8 | Yes | ⚠️ Placeholder |
| `boss_paburu_gold_orb.png` | Form 3A | 6×6 | 3 | 12 | Yes | ⚠️ Placeholder |
| `boss_paburu_black_orb.png` | Form 3B | 6×6 | 3 | 12 | Yes | ⚠️ Placeholder |

**Palette Notes — Form 1 (Stone):** Stone green (`#3C6432`), stone mid (`#5A8C50`), stone light (`#8CB496`), carving shadow (`#1E3C1E`), eye glow green (`#50FF50`), moss accent (`#2D5A28`), outline (`#0A0A0A`).

**Palette Notes — Form 2 (Spectral):** Spectral green bright (`#50FF78`), spectral green mid (`#28C850`), spectral green dark (`#0A6428`), mask teal (`#1E8C8C`), mask gold (`#D4A017`), spirit white (`#E8FFE8`), void black (`#000000`), glow white (`#FFFFFF`).

**Palette Notes — Form 3A (Gold):** Gold bright (`#FFD700`), gold mid (`#C8A800`), gold dark (`#8C7000`), gold shadow (`#3C3200`), energy white (`#FFFFF0`), outline black (`#1A1000`).

**Palette Notes — Form 3B (Pearl):** Pearl black (`#0A0A14`), pearl dark sheen (`#1E1E3C`), pearl mid (`#3C3C64`), pearl highlight (`#7878A0`), void center (`#000000`), outline (`#5A5A8C`).

---

## 7. Tilesets

Location: `assets/tilesets/`

| File | Used In | Theme | Size |
|---|---|---|---|
| `tileset_stage0.png` | Stage 0 | Neutral stone corridor | 1024×1024 |
| `tileset_jungle_stone.png` | Zone 1 Stage 1-1, 1-4 | Mountain jungle with stone | 128×128 |
| `tileset_cafeteria.png` | Zone 1 Stage 1-2 | Interior cafeteria, checkered floor | 128×128 |
| `tileset_aulas.png` | Zone 1 Stage 1-3 | Classroom interior, wood and plaster | 128×128 |
| `tileset_planicie.png` | Zone 2 Stage 2-1 | Open agricultural flatlands | 128×128 |
| `tileset_datacenter_ext.png` | Zone 2 Stage 2-2 | Concrete exterior, antennas | 128×128 |
| `tileset_datacenter.png` | Zone 2 Stages 2-3, 2-4 | Steel floor, glass partitions, servers | 128×128 |
| `tileset_heredia_stone.png` | Zone 3 Stages 3-1, 3-4 | Stone path and bungaló architecture | 128×128 |
| `tileset_heredia_interior.png` | Zone 3 Stages 3-2, 3-3 | Interior hall, courtyard | 128×128 |
| `tileset_cemetery.png` | Zone Final | Stone markers, ceremonial carvings | 128×128 |

### 7.1 Tileset Tile Categories

Each tileset must contain tiles organized in the following categories (columns):

| Column | Category | Description |
|---|---|---|
| 0–1 | Solid floor | Main walkable surface |
| 2–3 | Solid wall | Left and right walls |
| 4–5 | Platform edge | Left/right edge of platforms |
| 6 | Platform top | One-way platform surface |
| 7 | Solid corner | Interior corners |
| 8–9 | Decorative overlay | Non-solid decorative tiles |
| 10–11 | Background fill | Used in BG layers |
| 12–15 | Special/Environment | Zone-specific (vines, servers, antennas, graves) |

---

## 8. Background Layers

Location: `assets/backgrounds/`

Each stage requires three background layers: `_far`, `_mid`, `_near`. Dimensions must match or exceed the stage map width × 224px. Stage 0's set is the exception at 800×600 (the game's internal resolution).

### 8.1 Stage 0

| File | Layer | Size | Parallax |
|---|---|---|---|
| `stage0/bg_stage0_far.png` | BG_Far | 800×600 | 0.15× |
| `stage0/bg_stage0_mid.png` | BG_Mid | 800×600 | 0.40× |
| `stage0/bg_stage0_near.png` | BG_Near | 800×600 | 0.70× |

Each zone uses a single generic background set loaded by `StageLoader` using
the pattern `bg_{zone}_{layer}.png` (e.g. `bg_zone1_far.png`). Thematic
background variants (cafeteria, aulas, planicie, etc.) are aspirational;
all stages within a zone currently share the same generic background.

### 8.2 Zone 1

| File | Layer | Size |
|---|---|---|
| `zone1/bg_zone1_far.png` | BG_Far | 320×224 |
| `zone1/bg_zone1_mid.png` | BG_Mid | 640×224 |
| `zone1/bg_zone1_near.png` | BG_Near | 960×224 |

### 8.3 Zone 2

| File | Layer | Size |
|---|---|---|
| `zone2/bg_zone2_far.png` | BG_Far | 320×224 |
| `zone2/bg_zone2_mid.png` | BG_Mid | 640×224 |
| `zone2/bg_zone2_near.png` | BG_Near | 960×224 |

### 8.4 Zone 3

| File | Layer | Size |
|---|---|---|
| `zone3/bg_zone3_far.png` | BG_Far | 320×224 |
| `zone3/bg_zone3_mid.png` | BG_Mid | 640×224 |
| `zone3/bg_zone3_near.png` | BG_Near | 960×224 |

### 8.5 Zone Final

| File | Layer | Size |
|---|---|---|
| `final/bg_final_far.png` | BG_Far | 320×224 |
| `final/bg_final_mid.png` | BG_Mid | 640×224 |
| `final/bg_final_near.png` | BG_Near | 960×224 |

**Cemetery background palette:** Deep purple-black (`#0A0014`), cemetery stone (`#4A4A5A`), spirit green glow (`#28C850`), pale moonlight (`#C8D4C8`), dark soil (`#1E1410`).

---

## 9. UI Sprites

Location: `assets/ui/`

| File | Size | Description |
|---|---|---|
| `portrait_normal.png` | 32×32 | Player portrait — neutral |
| `portrait_hurt.png` | 32×32 | Player portrait — hurt expression |
| `portrait_critical.png` | 32×32 | Player portrait — critical health |
| `portrait_dead.png` | 32×32 | Player portrait — deceased |
| `banner_top.png` | 320×24 | Top half of stage entry banner |
| `banner_bottom.png` | 320×24 | Bottom half of stage entry banner |
| `hud_frame.png` | 36×36 | Portrait frame (9-slice) |
| `message_arrow.png` | 5×7 | Animated confirm arrow (2 frames) |
| `menu_arrow.png` | 5×8 | Menu selection arrow |
| `heart_sparkle.png` | 8×8 | Heart restore sparkle (4 frames, 12 FPS) |
| `heart_full.png` | 14×8 | Full heart |
| `heart_three_quarter.png` | 14×8 | Three-quarter heart |
| `heart_half.png` | 14×8 | Half heart |
| `heart_quarter.png` | 14×8 | Quarter heart |
| `heart_empty.png` | 14×8 | Empty heart outline |
| `relic_pepita.png` | 8×6 | Gold nugget HUD icon (animated, 3 frames) |
| `relic_perla.png` | 7×7 | Black pearl HUD icon (animated, 3 frames) |
| `relic_fragment1.png` | 12×12 | Relic fragment 1 (antler) — Zone 1 cleared |
| `relic_fragment2.png` | 12×12 | Relic fragment 2 (coil) — Zone 2 cleared |
| `relic_fragment3.png` | 12×12 | Relic fragment 3 (mask) — Zone 3 cleared |

---

## 10. Fonts

Location: `assets/fonts/`

All fonts are bitmap pixel sprite sheets (horizontal, one row per character set).

| File | Char Size | Character Set | Used For |
|---|---|---|---|
| `hud_digits.png` | 6×8 | `0-9 : ` (12 chars) | HUD timer display |
| `message_font.png` | 5×7 | ASCII printable (96 chars) | Tutorial messages |
| `banner_large.png` | 10×14 | A-Z 0-9 space (37 chars) | Stage number on banner |
| `banner_medium.png` | 6×9 | A-Z a-z 0-9 space .:- (66 chars) | Stage name on banner |
| `gameover_font.png` | 12×16 | A-Z space (27 chars) | GAME OVER text |
| `menu_font.png` | 6×9 | ASCII printable (96 chars) | Menu options |

---

## 11. Music Tracks

Location: `assets/music/`

| File | Used In | Mood | Loop |
|---|---|---|---|
All tracks are stored as **WAV** (not OGG). The engine's `stage_scene.py`
loads music via `assets/music/{bgm_track}.wav`. Conversion to OGG is deferred
until the final asset pipeline (Phase 3.6 in the remediation plan).

| File | Used In | Mood | Loop |
|---|---|---|---|
| `bgm_splash.wav` | Splash screen | Ambient, brief | No |
| `bgm_title.wav` | Title screen | Heroic, inviting | Yes |
| `bgm_story.wav` | Story screens 1-3 | Atmospheric, mysterious | Yes |
| `bgm_stage0.wav` | Stage 0 | Tense, instructional | Yes |
| `bgm_zone1_traverse.wav` | Zone 1 stages | Jungle percussion, humid tension | Yes |
| `bgm_zone1_boss.wav` | Stage 1-4 (Venado) | Forest spirit, ancient rhythm | Yes |
| `bgm_zone2_traverse.wav` | Zone 2 stages | Electronic drone, industrial | Yes |
| `bgm_zone2_boss.wav` | Stage 2-4 (Rey) | Collective whisper, metallic | Yes |
| `bgm_zone3_traverse.wav` | Zone 3 stages | Aerial, hunting tension | Yes |
| `bgm_zone3_boss.wav` | Stage 3-4 (Gavilán) | Wing beats, ceremonial | Yes |
| `bgm_final_approach.wav` | Stage 4-1 | Silence punctuated by ritual drums | Yes |
| `bgm_paburu.wav` | Stage 4-2 | Four-part adaptive track (one section per form) | Yes |

**`bgm_paburu.wav` — Adaptive Note:** This track is structured with a loop point that the `AudioManager` advances manually at each `BOSS_PHASE_CHANGED` event for Paburu. The track has four internally consistent sections that each loop independently. The `AudioManager.advance_music_section()` method (Paburu-specific) skips to the next section's loop point.

---

## 12. Sound Effects

Location: `assets/sfx/`

### 12.1 Player SFX

| File | Trigger |
|---|---|
| `player/sfx_player_jump.wav` | Jump action |
| `player/sfx_player_land.wav` | Landing after fall |
| `player/sfx_player_short_attack.wav` | Short attack swing |
| `player/sfx_player_long_attack.wav` | Long attack swing |
| `player/sfx_player_hit_connect.wav` | Player attack hits enemy |
| `player/sfx_player_hurt.wav` | Player receives damage |
| `player/sfx_player_die.wav` | Player death |
| `player/sfx_player_crouch.wav` | Crouch start |

### 12.2 Enemy SFX

All paths relative to `assets/sfx/enemies/`.

| File | Trigger |
|---|---|
| `sfx_enemies_hit.wav` | Any enemy receives damage |
| `sfx_enemies_die_small.wav` | Small enemies (health ≤ 1.0) |
| `sfx_enemies_die_large.wav` | Larger enemies (health ≥ 2.0) |
| `sfx_enemies_projectile_fire.wav` | Any projectile fired |
| `sfx_enemies_projectile_hit_wall.wav` | Projectile hits terrain |

### 12.3 Boss SFX

All paths relative to `assets/sfx/bosses/`.

| File | Trigger |
|---|---|
| `sfx_bosses_venado_stomp.wav` | Venado stomp attack |
| `sfx_bosses_venado_charge.wav` | Venado charge |
| `sfx_bosses_venado_vine.wav` | Venado vine toss |
| `sfx_bosses_rey_spit.wav` | Rey venom spit |
| `sfx_bosses_rey_split.wav` | Rey Phase 2 split |
| `sfx_bosses_gavilan_dive.wav` | Gavilán dive bomb |
| `sfx_bosses_gavilan_mask_beam.wav` | Gavilán mask beam |
| `sfx_bosses_paburu_eye_beam.wav` | Paburu eye beam (Form 1) |
| `sfx_bosses_paburu_wave.wav` | Paburu spirit wave (Form 2) |
| `sfx_bosses_phase_change.wav` | Any boss phase transition |
| `sfx_bosses_relic_appear.wav` | Relic fragment appears post-boss |

Missing aspirational boss SFX (not yet on disk): `sfx_venado_die`, `sfx_rey_die`, `sfx_gavilan_die`, `sfx_paburu_gold_rush`, `sfx_paburu_pull`, `sfx_paburu_convergence`, `sfx_paburu_transcend`.

### 12.4 UI SFX

All paths relative to `assets/sfx/ui/`.

| File | Trigger |
|---|---|
| `sfx_ui_menu_move.wav` | Menu cursor navigation |
| `sfx_ui_menu_confirm.wav` | Menu selection confirm |
| `sfx_ui_menu_cancel.wav` | Menu back |
| `sfx_ui_checkpoint.wav` | Checkpoint activated |
| `sfx_ui_stage_banner.wav` | Stage banner slide-in |
| `sfx_ui_game_over.wav` | Game Over screen |
| `sfx_ui_heart_restore.wav` | Heart refill animation |
| `sfx_ui_stage_complete.wav` | Stage completion |

### 12.5 Environment SFX

All paths relative to `assets/sfx/environment/`.

| File | Trigger |
|---|---|
| `sfx_environment_jungle_ambient.wav` | Zone 1 ambient loop |
| `sfx_environment_datacenter_hum.wav` | Zone 2 ambient loop |
| `sfx_environment_wind_indoor.wav` | Zone 3 ambient loop |
| `sfx_environment_cemetery_silence.wav` | Zone Final ambient (minimal) |
| `sfx_environment_screen_shake.wav` | Screen shake events |
| `sfx_environment_hazard_zone.wav` | Hazard zone damage tick |
| `sfx_environment_one_way_platform.wav` | Landing on one-way platform |

---

## 13. Shared Sprites

Location: `assets/sprites/shared/`

| File | Size | Frames | FPS | Description |
|---|---|---|---|---|
| `checkpoint.png` | 16×32 | 6 (animated), 1 (inactive) | 8 | Checkpoint post — glows when active |
| `torch_anim.png` | 8×16 | 4 | 8 | Torch flame animation |
| `fountain_anim.png` | 24×24 | 6 | 10 | Fountain water animation (Zone 3-3) — ⚠️ Placeholder |
| `spirit_echo_overlay.png` | 1×1 | 1 | — | Alpha overlay tint for spirit echoes — ⚠️ Placeholder |

---

## 14. Student Asset Guidelines

Students adding assets to `student_assets/` must comply with all standards in Section 2. Additionally:

| Rule | Requirement |
|---|---|
| Palette validation | Run `tools/validate_assets.py` on all new sprites before committing |
| Naming convention | Follow the same naming pattern as the asset type (see Section 2.5 of Codex) |
| No modification of `assets/` | Students only add to `student_assets/` |
| File format | PNG only for visuals; WAV or OGG for audio |
| Maximum new assets per stage | 20 sprite sheets, 5 music tracks, 15 SFX files |
| Color palette | Maximum 16 colors per sprite sheet; must be compatible with the zone's visual palette |

---

## 15. Asset Loading Reference

All assets are loaded through `AssetLoader`. The following shows the canonical loading pattern for each asset type:

```python
# Image loading:
surface = AssetLoader.load_image(ASSETS_DIR / "sprites" / "player" / "player_idle.png")

# Spritesheet loading:
sheet = AssetLoader.load_spritesheet(
    ASSETS_DIR / "sprites" / "player" / "player_walk.png",
    frame_w=32,
    frame_h=32
)

# Sound loading:
sound = AssetLoader.load_sound(ASSETS_DIR / "sfx" / "player" / "sfx_player_jump.wav")

# Background loading (direct image):
bg_far = AssetLoader.load_image(ASSETS_DIR / "backgrounds" / "zone1" / "bg_zone1_far.png")

# UI image loading:
heart = AssetLoader.load_image(ASSETS_DIR / "ui" / "heart_full.png")
```

Students use the same `AssetLoader` API for their student assets:
```python
# Student asset loading:
custom_sprite = AssetLoader.load_image(STUDENT_ASSETS_DIR / "sprites" / "my_enemy.png")
```


---
## 🔗 Documentos Relacionados

- [[06_TMX_SPEC.md|TMX Specification]]
- [[07_STAGE0_DESIGN.md|Stage 0 Design]]
- [[16_WORLD_DESIGN.md|World Design]]

---
--- Traducción al Español ---

*This document is also available in English above.*

# Legacy of InFest — Biblia de Recursos

**ID del Documento:** LOI-ASSET-020
**Versión:** 1.0.0
**Estado:** Oficial
**Compatibilidad:** Requiere LOI-CODEX-002, LOI-WORLD-016, LOI-BOSS-017, LOI-ROSTER-018
**Audiencia:** Profesor, Estudiantes, Artistas, asistentes de codificación IA

---

## 1. Descripción General

Este documento define cada recurso visual y de audio requerido por Legacy of InFest. Es la referencia autoritativa para artistas, estudiantes que crean recursos personalizados y asistentes de codificación IA que generan código de carga de recursos.

Cada recurso listado aquí tiene una ruta, formato, dimensiones, restricciones de paleta y contexto de uso definidos. Los recursos no listados aquí son creados por estudiantes (ubicados en student_assets/) o son generados en tiempo de ejecución por el pipeline de procesamiento.

---

## 2. Estándares Globales de Recursos

### 2.1 Estándares Visuales

| Propiedad | Estándar |
|---|---|
| Formato de píxel | PNG con canal alfa (RGBA) |
| Profundidad de color | 8 bits por canal |
| Restricción de paleta | Máximo 16 colores por hoja de sprites |
| Paleta global | Máximo 256 colores en todo el juego |
| Tamaño de píxel | 1:1 — sin renderizado de subpíxeles |
| Anti-aliasing | Nunca |
| Transparencia | Binaria (totalmente transparente u opaca) O alfa suave (solo para efectos) |
| Resolución interna | Todos los recursos diseñados para visualización 320x224 |

### 2.2 Formato de Hoja de Sprites

Todos los sprites animados son hojas de sprites horizontales: fotogramas dispuestos de izquierda a derecha, ancho igual, origen en la esquina superior izquierda.

### 2.3 Formato de Tiles

| Propiedad | Estándar |
|---|---|
| Tamaño de tile | 16x16 píxeles |
| Disposición de hoja | Cuadrícula de orden mayor de fila |
| Máximo de tiles por conjunto | 256 |
| Dimensiones de hoja | 128x128 px |

### 2.4 Estándares de Audio

| Propiedad | Música | SFX |
|---|---|---|
| Formato | OGG Vorbis | WAV u OGG |
| Tasa de muestreo | 44100 Hz | 22050 Hz |
| Profundidad de bits | 16 bits | 16 bits |
| Canales | Estéreo | Mono |
| Punto de bucle | Debe definirse para BGM | N/A |
| Normalización de volumen | Pico -12 dBFS | Pico -6 dBFS |

---

## 3. Estructura de Directorios

assets/sprites/player/, assets/sprites/enemies/, assets/sprites/bosses/, assets/tilesets/, assets/backgrounds/, assets/ui/, assets/fonts/, assets/music/, assets/sfx/

---

## 4. Sprites del Jugador

Todos los sprites del jugador están ubicados en assets/sprites/player/. Tamaño de fotograma: 32x32 píxeles para todas las animaciones.

| Archivo | Fotogramas | FPS | Bucle | Estado |
|---|---|---|---|---|
| player_idle.png | 4 | 8 | Sí | IDLE |
| player_walk.png | 8 | 12 | Sí | WALKING |
| player_jump.png | 3 | 12 | No | JUMPING |
| player_fall.png | 2 | 8 | Sí | FALLING |
| player_crouch.png | 2 | 8 | No | CROUCHING |
| player_short_attack.png | 6 | 18 | No | SHORT_ATTACK |
| player_long_attack.png | 10 | 16 | No | LONG_ATTACK |
| player_hurt.png | 4 | 12 | No | HURT |
| player_die.png | 8 | 10 | No | DYING |

---

## 5. Sprites de Enemigos

Los sprites de enemigos usan nombres genéricos basados en zonas.

### 5.1 Walker (universal)

Ubicación: assets/sprites/enemies/

| Archivo | Enemigo | Tamaño | Fotogramas | FPS |
|---|---|---|---|---|
| enemy_walker_walk.png | Walker | 20x16 | 6 | 10 |

### 5.2 Enemigos con Sprites por Zona

Ubicación: assets/sprites/enemies/zoneN/

| Archivo | Enemigo | Fotogramas | FPS |
|---|---|---|---|
| enemy_zoneN_walk.png | Walker de zona | 6 | 10 |
| enemy_zoneN_hurt.png | Cualquiera | 3 | 12 |
| enemy_zoneN_die.png | Cualquiera | 6 | 8 |
| enemy_fly_zoneN.png | Volador | 4 | 12 |
| enemy_shoot_zoneN.png | Disparador | 4 | 6 |

---

## 6. Sprites de Jefes

Ubicación: assets/sprites/bosses/

### 6.1 El Venado Sagrado — Tamaño: 48x48 px

| Archivo | Fotogramas | FPS |
|---|---|---|
| boss_venado_drift.png | 6 | 8 |
| boss_venado_stomp.png | 8 | 12 |
| boss_venado_charge.png | 6 | 14 |
| boss_venado_frenzy_drift.png | 6 | 14 |
| boss_venado_vine.png | 10 | 12 |
| boss_venado_hurt.png | 4 | 12 |
| boss_venado_death.png | 12 | 8 |

### 6.2 El Rey Terciopelo — Fase 1: 40x56 px, Subjefe: 24x28 px

### 6.3 El Gavilán Camionero Mascarero — 56x40 px

### 6.4 El Gran Shaman Paburu — Múltiples tamaños por forma

---

## 7. Tilesets

Ubicación: assets/tilesets/. 10 tilesets para los diferentes niveles y zonas. Cada tileset usa formato de cuadrícula 8x8 con categorías que incluyen suelo sólido, pared sólida, borde de plataforma, etc.

---

## 8. Capas de Fondo

Ubicación: assets/backgrounds/. Cada nivel requiere tres capas: _far, _mid, _near con tamaños 320x224, 640x224, y 960x224 respectivamente.

---

## 9. Sprites de UI

Ubicación: assets/ui/. Incluye retratos del jugador (32x32), banners (320x24), marco de HUD (36x36), flechas animadas, iconos de corazón (14x8) y fragmentos de reliquia.

---

## 10. Fuentes

Ubicación: assets/fonts/. Fuentes de mapa de bits para HUD, mensajes, banners, texto GAME OVER y menús.

---

## 11. Pistas de Música

Ubicación: assets/music/. 12 pistas en formato WAV para pantalla de presentación, título, historia, niveles de zona y jefes. bgm_paburu.wav tiene 4 secciones adaptativas.

---

## 12. Efectos de Sonido

Ubicación: assets/sfx/. Efectos categorizados por jugador, enemigos, jefes, UI y entorno.

---

## 13. Sprites Compartidos

Ubicación: assets/sprites/shared/. Incluye checkpoint, antorcha, fuente y superposición de eco espiritual.

---

## 14. Directrices para Estudiantes

Los estudiantes añaden recursos a student_assets/ cumpliendo reglas de validación de paleta, convención de nombres, formato PNG/WAV/OGG, máximo 20 hojas de sprites por nivel y 16 colores por hoja.

---

## 15. Referencia de Carga de Recursos

Todos los recursos se cargan a través de AssetLoader con métodos load_image, load_sound y load_spritesheet. Los estudiantes usan la misma API con STUDENT_ASSETS_DIR.