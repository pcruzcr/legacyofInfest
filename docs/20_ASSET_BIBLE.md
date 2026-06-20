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
| Internal resolution | All assets designed for 320×224 display |

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
│       ├── heart_full.png
│       ├── heart_three_quarter.png
│       ├── heart_half.png
│       ├── heart_quarter.png
│       └── heart_empty.png
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
| `player_jump.png` | 3 | 12 | No (hold last) | JUMPING |
| `player_fall.png` | 2 | 8 | Yes | FALLING |
| `player_crouch.png` | 2 | 8 | No (hold last) | CROUCHING |
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

### 5.1 Zone 1 Enemy Sprites

Location: `assets/sprites/enemies/zone1/`

| File | Enemy | Frame Size | Frames | FPS | Loop |
|---|---|---|---|---|---|
| `enemy_insecto_walk.png` | WalkerInsect | 16×12 | 6 | 10 | Yes |
| `enemy_insecto_hurt.png` | WalkerInsect | 16×12 | 3 | 12 | No |
| `enemy_insecto_die.png` | WalkerInsect | 16×12 | 5 | 10 | No |
| `enemy_pajaro_fly.png` | FlyingBird | 14×10 | 4 | 12 | Yes |
| `enemy_pajaro_hurt.png` | FlyingBird | 14×10 | 3 | 12 | No |
| `enemy_pajaro_die.png` | FlyingBird | 14×10 | 6 | 10 | No |
| `enemy_rana_idle.png` | ShooterFrog | 12×12 | 4 | 6 | Yes |
| `enemy_rana_aim.png` | ShooterFrog | 12×12 | 3 | 8 | No |
| `enemy_rana_fire.png` | ShooterFrog | 12×12 | 4 | 14 | No |
| `enemy_rana_hurt.png` | ShooterFrog | 12×12 | 3 | 12 | No |
| `enemy_rana_die.png` | ShooterFrog | 12×12 | 6 | 10 | No |
| `enemy_rana_proyectil.png` | Frog projectile | 4×4 | 2 | 8 | Yes |
| `enemy_raton_walk.png` | WalkerRaton | 14×10 | 6 | 14 | Yes |
| `enemy_raton_hurt.png` | WalkerRaton | 14×10 | 3 | 12 | No |
| `enemy_raton_die.png` | WalkerRaton | 14×10 | 5 | 10 | No |
| `enemy_cucaracha_fly.png` | FlyingCucaracha | 12×8 | 4 | 16 | Yes |
| `enemy_cucaracha_hurt.png` | FlyingCucaracha | 12×8 | 3 | 12 | No |
| `enemy_cucaracha_die.png` | FlyingCucaracha | 12×8 | 5 | 10 | No |
| `enemy_cocinero_idle.png` | ShooterCocinero | 16×24 | 4 | 6 | Yes |
| `enemy_cocinero_throw.png` | ShooterCocinero | 16×24 | 6 | 14 | No |
| `enemy_cocinero_hurt.png` | ShooterCocinero | 16×24 | 3 | 12 | No |
| `enemy_cocinero_die.png` | ShooterCocinero | 16×24 | 8 | 8 | No |
| `enemy_cocinero_tray.png` | Cook projectile | 12×6 | 2 | 8 | Yes |
| `enemy_estudiante_walk.png` | WalkerEstudiante | 16×24 | 8 | 10 | Yes |
| `enemy_estudiante_hurt.png` | WalkerEstudiante | 16×24 | 3 | 12 | No |
| `enemy_estudiante_die.png` | WalkerEstudiante | 16×24 | 7 | 8 | No |
| `enemy_hoja_fly.png` | FlyingNotebook | 10×14 | 4 | 8 | Yes |
| `enemy_hoja_hurt.png` | FlyingNotebook | 10×14 | 2 | 12 | No |
| `enemy_hoja_die.png` | FlyingNotebook | 10×14 | 4 | 10 | No |
| `enemy_tiza_idle.png` | ShooterTiza | 14×14 | 4 | 6 | Yes |
| `enemy_tiza_fire.png` | ShooterTiza | 14×14 | 5 | 14 | No |
| `enemy_tiza_hurt.png` | ShooterTiza | 14×14 | 3 | 12 | No |
| `enemy_tiza_die.png` | ShooterTiza | 14×14 | 6 | 10 | No |
| `enemy_tiza_proyectil.png` | Chalk projectile | 4×4 | 1 | — | — |

### 5.2 Zone 2 Enemy Sprites

Location: `assets/sprites/enemies/zone2/`

| File | Enemy | Frame Size | Frames | FPS | Loop |
|---|---|---|---|---|---|
| `enemy_terciopelo_small_walk.png` | WalkerSerpientePequena | 20×8 | 6 | 12 | Yes |
| `enemy_terciopelo_small_hurt.png` | WalkerSerpientePequena | 20×8 | 3 | 12 | No |
| `enemy_terciopelo_small_die.png` | WalkerSerpientePequena | 20×8 | 6 | 10 | No |
| `enemy_boa_fly.png` | FlyingBoa | 32×12 | 6 | 10 | Yes |
| `enemy_boa_hurt.png` | FlyingBoa | 32×12 | 3 | 12 | No |
| `enemy_boa_die.png` | FlyingBoa | 32×12 | 7 | 8 | No |
| `enemy_serpiente_arbol_idle.png` | ShooterSerpienteArbol | 14×16 | 4 | 6 | Yes |
| `enemy_serpiente_arbol_fire.png` | ShooterSerpienteArbol | 14×16 | 5 | 12 | No |
| `enemy_serpiente_arbol_hurt.png` | ShooterSerpienteArbol | 14×16 | 3 | 12 | No |
| `enemy_serpiente_arbol_die.png` | ShooterSerpienteArbol | 14×16 | 6 | 10 | No |
| `enemy_venom_proyectil.png` | Venom projectile | 5×5 | 2 | 8 | Yes |
| `enemy_terciopelo_large_walk.png` | WalkerTerciopelo | 28×12 | 6 | 8 | Yes |
| `enemy_terciopelo_large_hurt.png` | WalkerTerciopelo | 28×12 | 3 | 12 | No |
| `enemy_terciopelo_large_die.png` | WalkerTerciopelo | 28×12 | 7 | 8 | No |
| `enemy_cobra_idle.png` | ShooterVenomoLargo | 16×20 | 4 | 5 | Yes |
| `enemy_cobra_fire.png` | ShooterVenomoLargo | 16×20 | 6 | 12 | No |
| `enemy_cobra_hurt.png` | ShooterVenomoLargo | 16×20 | 3 | 12 | No |
| `enemy_cobra_die.png` | ShooterVenomoLargo | 16×20 | 7 | 8 | No |
| `enemy_venom_stream.png` | Long venom projectile | 8×4 | 4 | 12 | Yes |
| `enemy_terciovolador_fly.png` | FlyingTerciovolador | 18×14 | 6 | 12 | Yes |
| `enemy_terciovolador_hurt.png` | FlyingTerciovolador | 18×14 | 3 | 12 | No |
| `enemy_terciovolador_die.png` | FlyingTerciovolador | 18×14 | 6 | 8 | No |
| `enemy_guardia_walk.png` | WalkerGuardia | 16×24 | 8 | 10 | Yes |
| `enemy_guardia_hurt.png` | WalkerGuardia | 16×24 | 3 | 12 | No |
| `enemy_guardia_die.png` | WalkerGuardia | 16×24 | 7 | 8 | No |

### 5.3 Zone 3 Enemy Sprites

Location: `assets/sprites/enemies/zone3/`

| File | Enemy | Frame Size | Frames | FPS | Loop |
|---|---|---|---|---|---|
| `enemy_garza_walk.png` | WalkerGarza | 18×28 | 6 | 7 | Yes |
| `enemy_garza_hurt.png` | WalkerGarza | 18×28 | 3 | 12 | No |
| `enemy_garza_die.png` | WalkerGarza | 18×28 | 7 | 8 | No |
| `enemy_halcon_fly.png` | FlyingHalcon (glide) | 20×14 | 6 | 12 | Yes |
| `enemy_halcon_dive.png` | FlyingHalcon (dive) | 14×20 | 4 | 18 | No |
| `enemy_halcon_hurt.png` | FlyingHalcon | 20×14 | 3 | 12 | No |
| `enemy_halcon_die.png` | FlyingHalcon | 20×14 | 7 | 8 | No |
| `enemy_quetzal_idle.png` | ShooterQuetzal | 12×20 | 4 | 6 | Yes |
| `enemy_quetzal_aim.png` | ShooterQuetzal | 12×20 | 3 | 8 | No |
| `enemy_quetzal_fire.png` | ShooterQuetzal | 12×20 | 4 | 14 | No |
| `enemy_quetzal_hurt.png` | ShooterQuetzal | 12×20 | 3 | 12 | No |
| `enemy_quetzal_die.png` | ShooterQuetzal | 12×20 | 6 | 8 | No |
| `enemy_quetzal_feather.png` | Quetzal feather projectile | 3×10 | 2 | 12 | Yes |
| `enemy_palom_walk.png` | WalkerPalom | 16×16 | 6 | 8 | Yes |
| `enemy_palom_hurt.png` | WalkerPalom | 16×16 | 3 | 12 | No |
| `enemy_palom_die.png` | WalkerPalom | 16×16 | 6 | 8 | No |
| `enemy_buitre_idle.png` | ShooterBuitre | 18×22 | 4 | 5 | Yes |
| `enemy_buitre_fire.png` | ShooterBuitre | 18×22 | 5 | 12 | No |
| `enemy_buitre_hurt.png` | ShooterBuitre | 18×22 | 3 | 12 | No |
| `enemy_buitre_die.png` | ShooterBuitre | 18×22 | 7 | 8 | No |
| `enemy_buitre_proyectil.png` | Bone projectile | 8×6 | 2 | 8 | Yes |

---

## 6. Boss Sprites

Location: `assets/sprites/bosses/`

### 6.1 El Venado Sagrado

Frame size: 48×48 px

| File | Frames | FPS | Loop |
|---|---|---|---|
| `boss_venado_drift.png` | 6 | 8 | Yes |
| `boss_venado_stomp.png` | 8 | 12 | No |
| `boss_venado_charge.png` | 6 | 14 | No |
| `boss_venado_frenzy_drift.png` | 6 | 14 | Yes |
| `boss_venado_vine.png` | 10 | 12 | No |
| `boss_venado_hurt.png` | 4 | 12 | No |
| `boss_venado_death.png` | 12 | 8 | No |
| `boss_venado_skull.png` | 1 | — | — |
| `boss_venado_proyectil_vine.png` | 4 | 10 | Yes |

**Palette Notes:** Bone white (`#E8DCC8`), moss dark (`#2D4A1E`), moss mid (`#4A7832`), earth brown (`#6B4423`), fungus cream (`#C8B896`), beetle black (`#0A0A0A`), root tan (`#8C6E3C`), shadow (`#1A1A2E`) + transparent.

### 6.2 El Rey Terciopelo

Phase 1 frame size: 40×56 px. Sub-boss (Phase 2) frame size: 24×28 px.

| File | Frames | FPS | Loop |
|---|---|---|---|
| `boss_rey_walk.png` | 8 | 10 | Yes |
| `boss_rey_spit.png` | 6 | 12 | No |
| `boss_rey_split.png` | 8 | 10 | Yes |
| `boss_rey_metad_walk.png` | 6 | 12 | Yes |
| `boss_rey_merge.png` | 6 | 8 | No |
| `boss_rey_rampage.png` | 8 | 16 | Yes |
| `boss_rey_hurt.png` | 4 | 12 | No |
| `boss_rey_death.png` | 14 | 8 | No |
| `boss_rey_venom_glob.png` | 3 | 8 | Yes |

**Palette Notes:** Terciopelo tan (`#C8A264`), terciopelo dark (`#4A3218`), terciopelo mid (`#8C6432`), decay gray (`#7D7D7D`), decay dark (`#3C3C3C`), venom green (`#32A050`), venom bright (`#50C878`), shadow (`#0A0A14`).

### 6.3 El Gavilán Camionero Mascarero

Frame size: 56×40 px (wide — wingspan)

| File | Frames | FPS | Loop |
|---|---|---|---|
| `boss_gavilan_glide.png` | 8 | 10 | Yes |
| `boss_gavilan_dive.png` | 6 | 16 | No |
| `boss_gavilan_hover.png` | 4 | 8 | Yes |
| `boss_gavilan_storm.png` | 8 | 12 | No |
| `boss_gavilan_masked.png` | 6 | 14 | Yes |
| `boss_gavilan_hurt.png` | 4 | 12 | No |
| `boss_gavilan_death.png` | 16 | 8 | No |
| `boss_gavilan_mask_frag.png` | 4 | 12 | No |
| `boss_gavilan_feather.png` | 3 | 10 | Yes |

**Palette Notes:** Hawk brown (`#8C5A28`), hawk tan (`#C88C3C`), hawk white (`#E8DCC8`), mask gold (`#D4A017`), mask dark gold (`#8C6800`), mask teal (`#1E6B6B`), mask red-orange (`#D45A00`), eye glow (`#50FF50`), shadow black (`#0A0A0A`).

### 6.4 El Gran Shaman Paburu

Multiple frame sizes per form.

| File | Form | Frame Size | Frames | FPS | Loop |
|---|---|---|---|---|---|
| `boss_paburu_stone.png` | 1 | 64×64 | 4 | 6 | Yes |
| `boss_paburu_stone_slam.png` | 1 | 64×64 | 8 | 12 | No |
| `boss_paburu_stone_crack.png` | 1→2 | 64×64 | 8 | 8 | No |
| `boss_paburu_mask.png` | 2 | 56×72 | 6 | 10 | Yes |
| `boss_paburu_mask_wave.png` | 2 | 56×72 | 8 | 12 | No |
| `boss_paburu_gold.png` | 3A | 32×32 | 6 | 14 | Yes |
| `boss_paburu_black.png` | 3B | 32×32 | 6 | 14 | Yes |
| `boss_paburu_relic_atk.png` | 3A/B | 32×32 | 10 | 14 | No |
| `boss_paburu_spirit.png` | 4 | 64×80 | 8 | 10 | Yes |
| `boss_paburu_spirit_surge.png` | 4 | 64×80 | 12 | 14 | No |
| `boss_paburu_hurt.png` | All | 64×64 | 4 | 12 | No |
| `boss_paburu_transcend.png` | Death | 64×80 | 20 | 8 | No |
| `boss_paburu_stone_proyectil.png` | Form 1 | 8×8 | 3 | 8 | Yes |
| `boss_paburu_gold_orb.png` | Form 3A | 6×6 | 3 | 12 | Yes |
| `boss_paburu_black_orb.png` | Form 3B | 6×6 | 3 | 12 | Yes |

**Palette Notes — Form 1 (Stone):** Stone green (`#3C6432`), stone mid (`#5A8C50`), stone light (`#8CB496`), carving shadow (`#1E3C1E`), eye glow green (`#50FF50`), moss accent (`#2D5A28`), outline (`#0A0A0A`).

**Palette Notes — Form 2 (Spectral):** Spectral green bright (`#50FF78`), spectral green mid (`#28C850`), spectral green dark (`#0A6428`), mask teal (`#1E8C8C`), mask gold (`#D4A017`), spirit white (`#E8FFE8`), void black (`#000000`), glow white (`#FFFFFF`).

**Palette Notes — Form 3A (Gold):** Gold bright (`#FFD700`), gold mid (`#C8A800`), gold dark (`#8C7000`), gold shadow (`#3C3200`), energy white (`#FFFFF0`), outline black (`#1A1000`).

**Palette Notes — Form 3B (Pearl):** Pearl black (`#0A0A14`), pearl dark sheen (`#1E1E3C`), pearl mid (`#3C3C64`), pearl highlight (`#7878A0`), void center (`#000000`), outline (`#5A5A8C`).

---

## 7. Tilesets

Location: `assets/tilesets/`

| File | Used In | Theme | Size |
|---|---|---|---|
| `tileset_stage0.png` | Stage 0 | Neutral stone corridor | 128×128 |
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

Each stage requires three background layers: `_far`, `_mid`, `_near`. Dimensions must match or exceed the stage map width × 224px.

### 8.1 Stage 0

| File | Layer | Size | Parallax |
|---|---|---|---|
| `stage0/bg_stage0_far.png` | BG_Far | 320×224 | 0.15× |
| `stage0/bg_stage0_mid.png` | BG_Mid | 640×224 | 0.40× |
| `stage0/bg_stage0_near.png` | BG_Near | 960×224 | 0.70× |

### 8.2 Zone 1

| File | Layer | Used In |
|---|---|---|
| `zone1/bg_jungle_far.png` | BG_Far | Stages 1-1, 1-4 |
| `zone1/bg_jungle_mid.png` | BG_Mid | Stages 1-1, 1-4 |
| `zone1/bg_jungle_near.png` | BG_Near | Stages 1-1, 1-4 |
| `zone1/bg_cafeteria_far.png` | BG_Far | Stage 1-2 |
| `zone1/bg_cafeteria_mid.png` | BG_Mid | Stage 1-2 |
| `zone1/bg_cafeteria_near.png` | BG_Near | Stage 1-2 |
| `zone1/bg_aulas_far.png` | BG_Far | Stage 1-3 |
| `zone1/bg_aulas_mid.png` | BG_Mid | Stage 1-3 |
| `zone1/bg_aulas_near.png` | BG_Near | Stage 1-3 |

### 8.3 Zone 2

| File | Layer | Used In |
|---|---|---|
| `zone2/bg_planicie_far.png` | BG_Far | Stage 2-1 |
| `zone2/bg_planicie_mid.png` | BG_Mid | Stage 2-1 |
| `zone2/bg_planicie_near.png` | BG_Near | Stage 2-1 |
| `zone2/bg_datacenter_far.png` | BG_Far | Stages 2-2, 2-3, 2-4 |
| `zone2/bg_datacenter_mid.png` | BG_Mid | Stages 2-2, 2-3, 2-4 |
| `zone2/bg_datacenter_near.png` | BG_Near | Stages 2-2, 2-3, 2-4 |

### 8.4 Zone 3

| File | Layer | Used In |
|---|---|---|
| `zone3/bg_heredia_far.png` | BG_Far | All Zone 3 stages |
| `zone3/bg_heredia_mid.png` | BG_Mid | All Zone 3 stages |
| `zone3/bg_heredia_near.png` | BG_Near | All Zone 3 stages |
| `zone3/bg_patio_sky.png` | BG_Far | Stage 3-3 only (open sky) |

### 8.5 Zone Final

| File | Layer | Used In |
|---|---|---|
| `final/bg_cemetery_far.png` | BG_Far | Stages 4-1, 4-2 |
| `final/bg_cemetery_mid.png` | BG_Mid | Stages 4-1, 4-2 |
| `final/bg_cemetery_near.png` | BG_Near | Stages 4-1, 4-2 |

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
| `bgm_splash.ogg` | Splash screen | Ambient, brief | No |
| `bgm_title.ogg` | Title screen | Heroic, inviting | Yes |
| `bgm_story.ogg` | Story screens 1-3 | Atmospheric, mysterious | Yes |
| `bgm_stage0.ogg` | Stage 0 | Tense, instructional | Yes |
| `bgm_zone1_traverse.ogg` | Stages 1-1, 1-2, 1-3 | Jungle percussion, humid tension | Yes |
| `bgm_zone1_boss.ogg` | Stage 1-4 (Venado) | Forest spirit, ancient rhythm | Yes |
| `bgm_zone2_traverse.ogg` | Stages 2-1, 2-2, 2-3 | Electronic drone, industrial | Yes |
| `bgm_zone2_boss.ogg` | Stage 2-4 (Rey) | Collective whisper, metallic | Yes |
| `bgm_zone3_traverse.ogg` | Stages 3-1, 3-2, 3-3 | Aerial, hunting tension | Yes |
| `bgm_zone3_boss.ogg` | Stage 3-4 (Gavilán) | Wing beats, ceremonial | Yes |
| `bgm_final_approach.ogg` | Stage 4-1 | Silence punctuated by ritual drums | Yes |
| `bgm_paburu.ogg` | Stage 4-2 | Four-part adaptive track (one section per form) | Yes |

**`bgm_paburu.ogg` — Adaptive Note:** This track is structured with a loop point that the `AudioManager` advances manually at each `BOSS_PHASE_CHANGED` event for Paburu. The track has four internally consistent sections that each loop independently. The `AudioManager.advance_music_section()` method (Paburu-specific) skips to the next section's loop point.

---

## 12. Sound Effects

Location: `assets/sfx/`

### 12.1 Player SFX

| File | Trigger |
|---|---|
| `sfx/player/sfx_player_jump.wav` | Jump action |
| `sfx/player/sfx_player_land.wav` | Landing after fall |
| `sfx/player/sfx_player_short_attack.wav` | Short attack swing |
| `sfx/player/sfx_player_long_attack.wav` | Long attack swing |
| `sfx/player/sfx_player_hit_connect.wav` | Player attack hits enemy |
| `sfx/player/sfx_player_hurt.wav` | Player receives damage |
| `sfx/player/sfx_player_die.wav` | Player death |
| `sfx/player/sfx_player_crouch.wav` | Crouch start |

### 12.2 Enemy SFX

| File | Trigger |
|---|---|
| `sfx/enemies/sfx_enemy_hit.wav` | Any enemy receives damage |
| `sfx/enemies/sfx_enemy_die_small.wav` | Small enemies (health ≤ 1.0) |
| `sfx/enemies/sfx_enemy_die_large.wav` | Larger enemies (health ≥ 2.0) |
| `sfx/enemies/sfx_projectile_fire.wav` | Any projectile fired |
| `sfx/enemies/sfx_projectile_hit_wall.wav` | Projectile hits terrain |
| `sfx/enemies/sfx_serpent_hiss.wav` | Zone 2 serpent alert |
| `sfx/enemies/sfx_bird_cry.wav` | Zone 3 bird alert |

### 12.3 Boss SFX

| File | Trigger |
|---|---|
| `sfx/bosses/sfx_venado_stomp.wav` | Venado stomp attack |
| `sfx/bosses/sfx_venado_charge.wav` | Venado charge |
| `sfx/bosses/sfx_venado_vine.wav` | Venado vine toss |
| `sfx/bosses/sfx_venado_die.wav` | Venado death |
| `sfx/bosses/sfx_rey_spit.wav` | Rey venom spit |
| `sfx/bosses/sfx_rey_split.wav` | Rey Phase 2 split |
| `sfx/bosses/sfx_rey_die.wav` | Rey death |
| `sfx/bosses/sfx_gavilan_dive.wav` | Gavilán dive bomb |
| `sfx/bosses/sfx_gavilan_mask_beam.wav` | Gavilán mask beam |
| `sfx/bosses/sfx_gavilan_die.wav` | Gavilán death |
| `sfx/bosses/sfx_paburu_eye_beam.wav` | Paburu eye beam (Form 1) |
| `sfx/bosses/sfx_paburu_wave.wav` | Paburu spirit wave (Form 2) |
| `sfx/bosses/sfx_paburu_gold_rush.wav` | Gold sphere rush (Form 3A) |
| `sfx/bosses/sfx_paburu_pull.wav` | Pearl pull (Form 3B) |
| `sfx/bosses/sfx_paburu_convergence.wav` | Convergence attack (Form 4) |
| `sfx/bosses/sfx_paburu_transcend.wav` | Paburu defeat / ascension |
| `sfx/bosses/sfx_phase_change.wav` | Any boss phase transition |
| `sfx/bosses/sfx_relic_appear.wav` | Relic fragment appears post-boss |

### 12.4 UI SFX

| File | Trigger |
|---|---|
| `sfx/ui/sfx_menu_move.wav` | Menu cursor navigation |
| `sfx/ui/sfx_menu_confirm.wav` | Menu selection confirm |
| `sfx/ui/sfx_menu_cancel.wav` | Menu back |
| `sfx/ui/sfx_checkpoint.wav` | Checkpoint activated |
| `sfx/ui/sfx_checkpoint_restore.wav` | Respawn at checkpoint |
| `sfx/ui/sfx_stage_banner.wav` | Stage banner slide-in |
| `sfx/ui/sfx_game_over.wav` | Game Over screen |
| `sfx/ui/sfx_heart_restore.wav` | Heart refill animation |
| `sfx/ui/sfx_stage_complete.wav` | Stage completion |

### 12.5 Environment SFX

| File | Trigger |
|---|---|
| `sfx/environment/sfx_jungle_ambient.wav` | Zone 1 ambient loop |
| `sfx/environment/sfx_datacenter_hum.wav` | Zone 2 ambient loop |
| `sfx/environment/sfx_wind_indoor.wav` | Zone 3 ambient loop |
| `sfx/environment/sfx_cemetery_silence.wav` | Zone Final ambient (minimal) |
| `sfx/environment/sfx_screen_shake.wav` | Screen shake events |
| `sfx/environment/sfx_hazard_zone.wav` | Hazard zone damage tick |
| `sfx/environment/sfx_one_way_platform.wav` | Landing on one-way platform |

---

## 13. Shared Sprites

Location: `assets/sprites/shared/`

| File | Size | Frames | FPS | Description |
|---|---|---|---|---|
| `checkpoint.png` | 16×32 | 6 (animated), 1 (inactive) | 8 | Checkpoint post — glows when active |
| `torch_anim.png` | 8×16 | 4 | 8 | Torch flame animation |
| `fountain_anim.png` | 24×24 | 6 | 10 | Fountain water animation (Zone 3-3) |
| `spirit_echo_overlay.png` | 1×1 | 1 | — | Alpha overlay tint for spirit echoes |

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
bg_far = AssetLoader.load_image(ASSETS_DIR / "backgrounds" / "zone1" / "bg_jungle_far.png")
```

Students use the same `AssetLoader` API for their student assets:
```python
# Student asset loading:
custom_sprite = AssetLoader.load_image(STUDENT_ASSETS_DIR / "sprites" / "my_enemy.png")
```
