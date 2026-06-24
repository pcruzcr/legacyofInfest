# ASSET_PRODUCTION_MASTER_PLAN

Generated: Master asset production plan for full game delivery

## 1. PLAYER ASSETS

Location: `assets/sprites/player/`

Frame size: **32×32** per docs/20_ASSET_BIBLE.md §4

| Asset ID | Animation | Frames | Loop | Priority | Phase Dependency |
|---|---|---|---|---|---|
| PLR_IDLE | Idle | 4 | Yes | P0 | Core runtime |
| PLR_WALK | Walk | 8 | Yes | P0 | Core runtime |
| PLR_JUMP | Jump | 3 | No (hold last) | P0 | Core runtime |
| PLR_FALL | Fall | 2 | Yes | P0 | Core runtime |
| PLR_CROUCH | Crouch | 2 | No (hold last) | P0 | Core runtime |
| PLR_SHORT_ATK | Short Attack | 6 | No | P0 | Core runtime |
| PLR_LONG_ATK | Long Attack | 10 | No | P0 | Core runtime |
| PLR_HURT | Hurt | 4 | No | P1 | Core runtime |
| PLR_DIE | Death | 8 | No | P1 | Core runtime |

**Quantity:** 9 sprite sheets  
**Total frames:** 47

---

## 2. ENEMY ASSETS

Location: `assets/sprites/enemies/`

### 2.1 Zone 1 Enemies (docs/20_ASSET_BIBLE.md §5.1)

| Asset ID | Enemy | Frame Size | Frames | Loop | Priority | Phase Dependency |
|---|---|---|---|---|---|---|
| ENM_INSECTO_WALK | WalkerInsect | 16×12 | 6 | Yes | P0 | Core runtime |
| ENM_INSECTO_HURT | WalkerInsect | 16×12 | 3 | No | P1 | Core runtime |
| ENM_INSECTO_DIE | WalkerInsect | 16×12 | 5 | No | P1 | Core runtime |
| ENM_PAJARO_FLY | FlyingBird | 14×10 | 4 | Yes | P0 | Core runtime |
| ENM_PAJARO_HURT | FlyingBird | 14×10 | 3 | No | P1 | Core runtime |
| ENM_PAJARO_DIE | FlyingBird | 14×10 | 6 | No | P1 | Core runtime |
| ENM_RANA_IDLE | ShooterFrog | 12×12 | 4 | Yes | P0 | Core runtime |
| ENM_RANA_AIM | ShooterFrog | 12×12 | 3 | No | P1 | Core runtime |
| ENM_RANA_FIRE | ShooterFrog | 12×12 | 4 | No | P1 | Core runtime |
| ENM_RANA_HURT | ShooterFrog | 12×12 | 3 | No | P1 | Core runtime |
| ENM_RANA_DIE | ShooterFrog | 12×12 | 6 | No | P1 | Core runtime |
| ENM_RANA_PROYECTIL | Frog projectile | 4×4 | 2 | Yes | P1 | Core runtime |
| ENM_RATON_WALK | WalkerRaton | 14×10 | 6 | Yes | P1 | Zone 1 student stage |
| ENM_RATON_HURT | WalkerRaton | 14×10 | 3 | No | P2 | Zone 1 student stage |
| ENM_RATON_DIE | WalkerRaton | 14×10 | 5 | No | P2 | Zone 1 student stage |
| ENM_CUCARACHA_FLY | FlyingCucaracha | 12×8 | 4 | Yes | P1 | Zone 1 student stage |
| ENM_CUCARACHA_HURT | FlyingCucaracha | 12×8 | 3 | No | P2 | Zone 1 student stage |
| ENM_CUCARACHA_DIE | FlyingCucaracha | 12×8 | 5 | No | P2 | Zone 1 student stage |
| ENM_COCINERO_IDLE | ShooterCocinero | 16×24 | 4 | Yes | P1 | Zone 1 student stage |
| ENM_COCINERO_THROW | ShooterCocinero | 16×24 | 6 | No | P2 | Zone 1 student stage |
| ENM_COCINERO_HURT | ShooterCocinero | 16×24 | 3 | No | P2 | Zone 1 student stage |
| ENM_COCINERO_DIE | ShooterCocinero | 16×24 | 8 | No | P2 | Zone 1 student stage |
| ENM_COCINERO_TRAY | Cook projectile | 12×6 | 2 | Yes | P2 | Zone 1 student stage |
| ENM_ESTUDIANTE_WALK | WalkerEstudiante | 16×24 | 8 | Yes | P1 | Zone 1 student stage |
| ENM_ESTUDIANTE_HURT | WalkerEstudiante | 16×24 | 3 | No | P2 | Zone 1 student stage |
| ENM_ESTUDIANTE_DIE | WalkerEstudiante | 16×24 | 7 | No | P2 | Zone 1 student stage |
| ENM_HOJA_FLY | FlyingNotebook | 10×14 | 4 | Yes | P1 | Zone 1 student stage |
| ENM_HOJA_HURT | FlyingNotebook | 10×14 | 2 | No | P2 | Zone 1 student stage |
| ENM_HOJA_DIE | FlyingNotebook | 10×14 | 4 | No | P2 | Zone 1 student stage |
| ENM_TIZA_IDLE | ShooterTiza | 14×14 | 4 | Yes | P1 | Zone 1 student stage |
| ENM_TIZA_FIRE | ShooterTiza | 14×14 | 5 | No | P2 | Zone 1 student stage |
| ENM_TIZA_HURT | ShooterTiza | 14×14 | 3 | No | P2 | Zone 1 student stage |
| ENM_TIZA_DIE | ShooterTiza | 14×14 | 6 | No | P2 | Zone 1 student stage |
| ENM_TIZA_PROYECTIL | Chalk projectile | 4×4 | 1 | — | P2 | Zone 1 student stage |

**Zone 1 enemy sheets:** 37

### 2.2 Zone 2 Enemies (docs/20_ASSET_BIBLE.md §5.2)

| Asset ID | Enemy | Frame Size | Frames | Loop | Priority | Phase Dependency |
|---|---|---|---|---|---|---|
| ENM_TERCIO_SMALL_WALK | WalkerSerpientePequena | 20×8 | 6 | Yes | P2 | Zone 2 student stage |
| ENM_TERCIO_SMALL_HURT | WalkerSerpientePequena | 20×8 | 3 | No | P3 | Zone 2 student stage |
| ENM_TERCIO_SMALL_DIE | WalkerSerpientePequena | 20×8 | 6 | No | P3 | Zone 2 student stage |
| ENM_BOA_FLY | FlyingBoa | 32×12 | 6 | Yes | P2 | Zone 2 student stage |
| ENM_BOA_HURT | FlyingBoa | 32×12 | 3 | No | P3 | Zone 2 student stage |
| ENM_BOA_DIE | FlyingBoa | 32×12 | 7 | No | P3 | Zone 2 student stage |
| ENM_SERP_ARBOL_IDLE | ShooterSerpienteArbol | 14×16 | 4 | Yes | P2 | Zone 2 student stage |
| ENM_SERP_ARBOL_FIRE | ShooterSerpienteArbol | 14×16 | 5 | No | P3 | Zone 2 student stage |
| ENM_SERP_ARBOL_HURT | ShooterSerpienteArbol | 14×16 | 3 | No | P3 | Zone 2 student stage |
| ENM_SERP_ARBOL_DIE | ShooterSerpienteArbol | 14×16 | 6 | No | P3 | Zone 2 student stage |
| ENM_VENOM_PROYECTIL | Venom projectile | 5×5 | 2 | Yes | P3 | Zone 2 student stage |
| ENM_TERCIO_LARGE_WALK | WalkerTerciopelo | 28×12 | 6 | Yes | P3 | Zone 2 boss |
| ENM_TERCIO_LARGE_HURT | WalkerTerciopelo | 28×12 | 3 | No | P3 | Zone 2 boss |
| ENM_TERCIO_LARGE_DIE | WalkerTerciopelo | 28×12 | 7 | No | P3 | Zone 2 boss |
| ENM_COBRA_IDLE | ShooterVenomoLargo | 16×20 | 4 | Yes | P3 | Zone 2 boss |
| ENM_COBRA_FIRE | ShooterVenomoLargo | 16×20 | 6 | No | P3 | Zone 2 boss |
| ENM_COBRA_HURT | ShooterVenomoLargo | 16×20 | 3 | No | P3 | Zone 2 boss |
| ENM_COBRA_DIE | ShooterVenomoLargo | 16×20 | 7 | No | P3 | Zone 2 boss |
| ENM_VENOM_STREAM | Long venom projectile | 8×4 | 4 | Yes | P3 | Zone 2 boss |
| ENM_TERCIOVOLADOR_FLY | FlyingTerciovolador | 18×14 | 6 | Yes | P3 | Zone 2 boss |
| ENM_TERCIOVOLADOR_HURT | FlyingTerciovolador | 18×14 | 3 | No | P3 | Zone 2 boss |
| ENM_TERCIOVOLADOR_DIE | FlyingTerciovolador | 18×14 | 6 | No | P3 | Zone 2 boss |
| ENM_GUARDIA_WALK | WalkerGuardia | 16×24 | 8 | Yes | P2 | Zone 2 student stage |
| ENM_GUARDIA_HURT | WalkerGuardia | 16×24 | 3 | No | P3 | Zone 2 student stage |
| ENM_GUARDIA_DIE | WalkerGuardia | 16×24 | 7 | No | P3 | Zone 2 student stage |

**Zone 2 enemy sheets:** 24

### 2.3 Zone 3 Enemies (docs/20_ASSET_BIBLE.md §5.3)

| Asset ID | Enemy | Frame Size | Frames | Loop | Priority | Phase Dependency |
|---|---|---|---|---|---|---|
| ENM_GARZA_WALK | WalkerGarza | 18×28 | 6 | Yes | P3 | Zone 3 student stage |
| ENM_GARZA_HURT | WalkerGarza | 18×28 | 3 | No | P4 | Zone 3 student stage |
| ENM_GARZA_DIE | WalkerGarza | 18×28 | 7 | No | P4 | Zone 3 student stage |
| ENM_HALCON_GLIDE | FlyingHalcon (glide) | 20×14 | 6 | Yes | P3 | Zone 3 student stage |
| ENM_HALCON_DIVE | FlyingHalcon (dive) | 14×20 | 4 | No | P3 | Zone 3 student stage |
| ENM_HALCON_HURT | FlyingHalcon | 20×14 | 3 | No | P4 | Zone 3 student stage |
| ENM_HALCON_DIE | FlyingHalcon | 20×14 | 7 | No | P4 | Zone 3 student stage |
| ENM_QUETZAL_IDLE | ShooterQuetzal | 12×20 | 4 | Yes | P3 | Zone 3 student stage |
| ENM_QUETZAL_AIM | ShooterQuetzal | 12×20 | 3 | No | P4 | Zone 3 student stage |
| ENM_QUETZAL_FIRE | ShooterQuetzal | 12×20 | 4 | No | P4 | Zone 3 student stage |
| ENM_QUETZAL_HURT | ShooterQuetzal | 12×20 | 3 | No | P4 | Zone 3 student stage |
| ENM_QUETZAL_DIE | ShooterQuetzal | 12×20 | 6 | No | P4 | Zone 3 student stage |
| ENM_QUETZAL_FEATHER | Quetzal feather | 3×10 | 2 | Yes | P4 | Zone 3 student stage |
| ENM_PALOM_WALK | WalkerPalom | 16×16 | 6 | Yes | P3 | Zone 3 student stage |
| ENM_PALOM_HURT | WalkerPalom | 16×16 | 3 | No | P4 | Zone 3 student stage |
| ENM_PALOM_DIE | WalkerPalom | 16×16 | 6 | No | P4 | Zone 3 student stage |
| ENM_BUITRE_IDLE | ShooterBuitre | 18×22 | 4 | Yes | P3 | Zone 3 student stage |
| ENM_BUITRE_FIRE | ShooterBuitre | 18×22 | 5 | No | P4 | Zone 3 student stage |
| ENM_BUITRE_HURT | ShooterBuitre | 18×22 | 3 | No | P4 | Zone 3 student stage |
| ENM_BUITRE_DIE | ShooterBuitre | 18×22 | 7 | No | P4 | Zone 3 student stage |
| ENM_BUITRE_PROYECTIL | Bone projectile | 8×6 | 2 | Yes | P4 | Zone 3 student stage |

**Zone 3 enemy sheets:** 20

**TOTAL ENEMY SPRITE SHEETS:** 81

---

## 3. BOSS ASSETS

Location: `assets/sprites/bosses/`

### 3.1 El Venado Sagrado (docs/20_ASSET_BIBLE.md §6.1)

Frame size varies per animation

| Asset ID | Animation | Frame Size | Frames | Loop | Priority | Phase Dependency |
|---|---|---|---|---|---|---|
| BOSS_VENADO_DRIFT | Drift | 48×48 | 6 | Yes | P1 | Zone 1 boss |
| BOSS_VENADO_STOMP | Stomp | 48×48 | 8 | No | P1 | Zone 1 boss |
| BOSS_VENADO_CHARGE | Charge | 48×48 | 6 | No | P1 | Zone 1 boss |
| BOSS_VENADO_FRENZY | Frenzy drift | 48×48 | 6 | Yes | P2 | Zone 1 boss |
| BOSS_VENADO_VINE | Vine toss | 48×48 | 10 | No | P2 | Zone 1 boss |
| BOSS_VENADO_HURT | Hurt | 48×48 | 4 | No | P2 | Zone 1 boss |
| BOSS_VENADO_DEATH | Death | 48×48 | 12 | No | P2 | Zone 1 boss |
| BOSS_VENADO_SKULL | Skull (static) | 48×48 | 1 | — | P2 | Zone 1 boss |
| BOSS_VENADO_VINE_PROJ | Vine projectile | varies | 4 | Yes | P2 | Zone 1 boss |

**Sheets:** 9

### 3.2 El Rey Terciopelo (docs/20_ASSET_BIBLE.md §6.2)

| Asset ID | Animation | Frame Size | Frames | Loop | Priority | Phase Dependency |
|---|---|---|---|---|---|---|
| BOSS_REY_WALK | Walk | 40×56 | 8 | Yes | P2 | Zone 2 boss |
| BOSS_REY_SPIT | Venom spit | 40×56 | 6 | No | P2 | Zone 2 boss |
| BOSS_REY_SPLIT | Split | 40×56 | 8 | Yes | P2 | Zone 2 boss |
| BOSS_REY_META_WALK | Sub-boss walk | 24×28 | 6 | Yes | P3 | Zone 2 boss |
| BOSS_REY_MERGE | Merge | 24×28 | 6 | No | P3 | Zone 2 boss |
| BOSS_REY_RAMPAGE | Rampage | 40×56 | 8 | Yes | P3 | Zone 2 boss |
| BOSS_REY_HURT | Hurt | 40×56 | 4 | No | P3 | Zone 2 boss |
| BOSS_REY_DEATH | Death | 40×56 | 14 | No | P3 | Zone 2 boss |
| BOSS_REY_VENOM_GLOB | Venom glob | varies | 3 | Yes | P3 | Zone 2 boss |

**Sheets:** 9

### 3.3 El Gavilán Camionero Mascarero (docs/20_ASSET_BIBLE.md §6.3)

| Asset ID | Animation | Frame Size | Frames | Loop | Priority | Phase Dependency |
|---|---|---|---|---|---|---|
| BOSS_GAVILAN_GLIDE | Glide | 56×40 | 8 | Yes | P3 | Zone 3 boss |
| BOSS_GAVILAN_DIVE | Dive | 56×40 | 6 | No | P3 | Zone 3 boss |
| BOSS_GAVILAN_HOVER | Hover | 56×40 | 4 | Yes | P3 | Zone 3 boss |
| BOSS_GAVILAN_STORM | Storm | 56×40 | 8 | No | P3 | Zone 3 boss |
| BOSS_GAVILAN_MASKED | Masked form | 56×40 | 6 | Yes | P4 | Zone 3 boss |
| BOSS_GAVILAN_HURT | Hurt | 56×40 | 4 | No | P4 | Zone 3 boss |
| BOSS_GAVILAN_DEATH | Death | 56×40 | 16 | No | P4 | Zone 3 boss |
| BOSS_GAVILAN_MASK_FRAG | Mask fragment | varies | 4 | No | P4 | Zone 3 boss |
| BOSS_GAVILAN_FEATHER | Feather | varies | 3 | Yes | P4 | Zone 3 boss |

**Sheets:** 9

### 3.4 El Gran Shaman Paburu (docs/20_ASSET_BIBLE.md §6.4)

| Asset ID | Form/Animation | Frame Size | Frames | Loop | Priority | Phase Dependency |
|---|---|---|---|---|---|---|
| BOSS_PABURU_STONE | Form 1 idle | 64×64 | 4 | Yes | P4 | Final boss |
| BOSS_PABURU_STONE_SLAM | Form 1 slam | 64×64 | 8 | No | P4 | Final boss |
| BOSS_PABURU_STONE_CRACK | Form 1→2 transition | 64×64 | 8 | No | P4 | Final boss |
| BOSS_PABURU_MASK | Form 2 idle | 56×72 | 6 | Yes | P4 | Final boss |
| BOSS_PABURU_MASK_WAVE | Form 2 wave | 56×72 | 8 | No | P4 | Final boss |
| BOSS_PABURU_GOLD | Form 3A idle | 32×32 | 6 | Yes | P4 | Final boss |
| BOSS_PABURU_BLACK | Form 3B idle | 32×32 | 6 | Yes | P4 | Final boss |
| BOSS_PABURU_RELIC_ATK | Form 3A/B attack | 32×32 | 10 | No | P4 | Final boss |
| BOSS_PABURU_SPIRIT | Form 4 idle | 64×80 | 8 | Yes | P4 | Final boss |
| BOSS_PABURU_SPIRIT_SURGE | Form 4 surge | 64×80 | 12 | No | P4 | Final boss |
| BOSS_PABURU_HURT | All forms hurt | 64×64 | 4 | No | P4 | Final boss |
| BOSS_PABURU_TRANSCEND | Death/transcend | 64×80 | 20 | No | P4 | Final boss |
| BOSS_PABURU_STONE_PROJ | Form 1 projectile | 8×8 | 3 | Yes | P4 | Final boss |
| BOSS_PABURU_GOLD_ORB | Form 3A projectile | 6×6 | 3 | Yes | P4 | Final boss |
| BOSS_PABURU_BLACK_ORB | Form 3B projectile | 6×6 | 3 | Yes | P4 | Final boss |

**Sheets:** 15

**TOTAL BOSS SPRITE SHEETS:** 42

---

## 4. TILESETS

Location: `assets/tilesets/`

Format: PNG (128×128 px, 8×8 tile grid, 16×16 tiles)

| Asset ID | Used In | Priority | Phase Dependency |
|---|---|---|---|
| TILESET_STAGE0 | Stage 0 | P0 | Core runtime |
| TILESET_JUNGLE_STONE | Stages 1-1, 1-4 | P1 | Zone 1 |
| TILESET_CAFETERIA | Stage 1-2 | P1 | Zone 1 |
| TILESET_AULAS | Stage 1-3 | P1 | Zone 1 |
| TILESET_PLANICIE | Stage 2-1 | P2 | Zone 2 |
| TILESET_DATACENTER_EXT | Stage 2-2 | P2 | Zone 2 |
| TILESET_DATACENTER | Stages 2-3, 2-4 | P2 | Zone 2 |
| TILESET_HEREDIA_STONE | Stages 3-1, 3-4 | P3 | Zone 3 |
| TILESET_HEREDIA_INTERIOR | Stages 3-2, 3-3 | P3 | Zone 3 |
| TILESET_CEMETERY | Stages 4-1, 4-2 | P4 | Final zone |

Each tileset requires matching `.tsx` definition.

**Quantity:** 10 tilesets + 10 TSX files = 20 files  
**Tile capacity:** 256 tiles per tileset = 2,560 tile slots

---

## 5. BACKGROUNDS

Location: `assets/backgrounds/`

Per docs/20_ASSET_BIBLE.md §8, each stage requires BG_Far, BG_Mid, BG_Near.

| Asset ID | Stage | Layer | Dimensions | Parallax | Priority | Phase Dependency |
|---|---|---|---|---|---|---|
| BG_STAGE0_FAR | Stage 0 | Far | 320×224 | 0.15× | P0 | Core runtime |
| BG_STAGE0_MID | Stage 0 | Mid | 640×224 | 0.40× | P0 | Core runtime |
| BG_STAGE0_NEAR | Stage 0 | Near | 960×224 | 0.70× | P0 | Core runtime |
| BG_JUNGLE_FAR | Stages 1-1, 1-4 | Far | varies | 0.15× | P1 | Zone 1 |
| BG_JUNGLE_MID | Stages 1-1, 1-4 | Mid | varies | 0.40× | P1 | Zone 1 |
| BG_JUNGLE_NEAR | Stages 1-1, 1-4 | Near | varies | 0.70× | P1 | Zone 1 |
| BG_CAFETERIA_FAR | Stage 1-2 | Far | varies | 0.15× | P1 | Zone 1 |
| BG_CAFETERIA_MID | Stage 1-2 | Mid | varies | 0.40× | P1 | Zone 1 |
| BG_CAFETERIA_NEAR | Stage 1-2 | Near | varies | 0.70× | P1 | Zone 1 |
| BG_AULAS_FAR | Stage 1-3 | Far | varies | 0.15× | P1 | Zone 1 |
| BG_AULAS_MID | Stage 1-3 | Mid | varies | 0.40× | P1 | Zone 1 |
| BG_AULAS_NEAR | Stage 1-3 | Near | varies | 0.70× | P1 | Zone 1 |
| BG_PLANICIE_FAR | Stage 2-1 | Far | varies | 0.15× | P2 | Zone 2 |
| BG_PLANICIE_MID | Stage 2-1 | Mid | varies | 0.40× | P2 | Zone 2 |
| BG_PLANICIE_NEAR | Stage 2-1 | Near | varies | 0.70× | P2 | Zone 2 |
| BG_DATACENTER_FAR | Stages 2-2, 2-3, 2-4 | Far | varies | 0.15× | P2 | Zone 2 |
| BG_DATACENTER_MID | Stages 2-2, 2-3, 2-4 | Mid | varies | 0.40× | P2 | Zone 2 |
| BG_DATACENTER_NEAR | Stages 2-2, 2-3, 2-4 | Near | varies | 0.70× | P2 | Zone 2 |
| BG_HEREDIA_FAR | All Zone 3 | Far | varies | 0.15× | P3 | Zone 3 |
| BG_HEREDIA_MID | All Zone 3 | Mid | varies | 0.40× | P3 | Zone 3 |
| BG_HEREDIA_NEAR | All Zone 3 | Near | varies | 0.70× | P3 | Zone 3 |
| BG_PATIO_SKY | Stage 3-3 only | Far | varies | 0.10× | P3 | Zone 3 |
| BG_CEMETERY_FAR | Stages 4-1, 4-2 | Far | varies | 0.15× | P4 | Final zone |
| BG_CEMETERY_MID | Stages 4-1, 4-2 | Mid | varies | 0.40× | P4 | Final zone |
| BG_CEMETERY_NEAR | Stages 4-1, 4-2 | Near | varies | 0.70× | P4 | Final zone |

**Total background layers:** **27**

---

## 6. HUD ASSETS

Location: `assets/ui/`

| Asset ID | File | Size | Priority | Phase Dependency |
|---|---|---|---|---|
| HUD_HEART_FULL | heart_full.png | 14×8 | P0 | Core runtime |
| HUD_HEART_3Q | heart_three_quarter.png | 14×8 | P0 | Core runtime |
| HUD_HEART_HALF | heart_half.png | 14×8 | P0 | Core runtime |
| HUD_HEART_Q | heart_quarter.png | 14×8 | P0 | Core runtime |
| HUD_HEART_EMPTY | heart_empty.png | 14×8 | P0 | Core runtime |
| HUD_PORTRAIT_NORM | portrait_normal.png | 32×32 | P1 | Core runtime |
| HUD_PORTRAIT_HURT | portrait_hurt.png | 32×32 | P1 | Core runtime |
| HUD_PORTRAIT_CRIT | portrait_critical.png | 32×32 | P1 | Core runtime |
| HUD_PORTRAIT_DEAD | portrait_dead.png | 32×32 | P1 | Core runtime |
| HUD_BANNER_TOP | banner_top.png | 320×24 | P1 | Core runtime |
| HUD_BANNER_BOTTOM | banner_bottom.png | 320×24 | P1 | Core runtime |
| HUD_FRAME | hud_frame.png | 36×36 | P1 | Core runtime |
| HUD_MSG_ARROW | message_arrow.png | 5×7 | P1 | Core runtime |
| HUD_MENU_ARROW | menu_arrow.png | 5×8 | P2 | UI system |
| HUD_HEART_SPARKLE | heart_sparkle.png | 8×8 | P2 | Core runtime |
| HUD_RELIC_PEPITA | relic_pepita.png | 8×6 | P2 | HUD |
| HUD_RELIC_PERLA | relic_perla.png | 7×7 | P2 | HUD |
| HUD_RELIC_FRAG1 | relic_fragment1.png | 12×12 | P2 | HUD |
| HUD_RELIC_FRAG2 | relic_fragment2.png | 12×12 | P2 | HUD |
| HUD_RELIC_FRAG3 | relic_fragment3.png | 12×12 | P2 | HUD |

**Quantity:** 20 sprites

---

## 7. SHARED SPRITES

Location: `assets/sprites/shared/`

| Asset ID | File | Size | Frames | FPS | Loop | Priority | Phase Dependency |
|---|---|---|---|---|---|---|---|
| SPR_CHECKPOINT | checkpoint.png | 16×32 | 6 (active) + 1 (inactive) | 8 | Yes | P0 | Core runtime |
| SPR_TORCH | torch_anim.png | 8×16 | 4 | 8 | Yes | P0 | Core runtime |
| SPR_FOUNTAIN | fountain_anim.png | 24×24 | 6 | 10 | Yes | P1 | Zone 3 |
| SPR_SPIRIT_ECHO | spirit_echo_overlay.png | 1×1 | 1 | — | — | P1 | Final zone |

**Quantity:** 4 sprite sheets

---

## 8. FONTS

Location: `assets/fonts/`

Format: Bitmap sprite sheet (horizontal, 1 row)

| Asset ID | File | Char Size | Charset | Priority | Phase Dependency |
|---|---|---|---|---|---|
| FONT_HUD_DIGITS | hud_digits.png | 6×8 | 0-9, space (12) | P0 | Core runtime |
| FONT_MSG | message_font.png | 5×7 | ASCII printable (96) | P0 | Core runtime |
| FONT_BANNER_LG | banner_large.png | 10×14 | A-Z0-9 space (37) | P1 | Core runtime |
| FONT_BANNER_MD | banner_medium.png | 6×9 | A-Za-z0-9 .:- (66) | P1 | Core runtime |
| FONT_GAMEOVER | gameover_font.png | 12×16 | A-Z space (27) | P1 | Core runtime |
| FONT_MENU | menu_font.png | 6×9 | ASCII printable (96) | P2 | UI system |

**Quantity:** 6 font sprite sheets

---

## 9. AUDIO ASSETS

### 9.1 Music (location: `assets/music/`)

Format: OGG Vorbis, 44100 Hz, stereo, with loop points

| Asset ID | File | Used In | Priority | Phase Dependency |
|---|---|---|---|---|
| MUS_SPLASH | bgm_splash.ogg | Splash screen | P0 | Core runtime |
| MUS_TITLE | bgm_title.ogg | Title screen | P1 | UI system |
| MUS_STORY | bgm_story.ogg | Story screens | P1 | UI system |
| MUS_STAGE0 | bgm_stage0.ogg | Stage 0 | P0 | Core runtime |
| MUS_ZONE1_TRAVERSE | bgm_zone1_traverse.ogg | Stages 1-1, 1-2, 1-3 | P1 | Zone 1 |
| MUS_ZONE1_BOSS | bgm_zone1_boss.ogg | Stage 1-4 | P2 | Zone 1 boss |
| MUS_ZONE2_TRAVERSE | bgm_zone2_traverse.ogg | Stages 2-1, 2-2, 2-3 | P2 | Zone 2 |
| MUS_ZONE2_BOSS | bgm_zone2_boss.ogg | Stage 2-4 | P3 | Zone 2 boss |
| MUS_ZONE3_TRAVERSE | bgm_zone3_traverse.ogg | Stages 3-1, 3-2, 3-3 | P3 | Zone 3 |
| MUS_ZONE3_BOSS | bgm_zone3_boss.ogg | Stage 3-4 | P4 | Zone 3 boss |
| MUS_FINAL_APPROACH | bgm_final_approach.ogg | Stage 4-1 | P4 | Final zone |
| MUS_PABURU | bgm_paburu.ogg | Stage 4-2 (adaptive 4-phase) | P4 | Final boss |

**Quantity:** 12 music tracks

### 9.2 Sound Effects

#### 9.2.1 Player SFX (location: `assets/sfx/player/`)

| Asset ID | File | Trigger | Priority | Phase Dependency |
|---|---|---|---|---|
| SFX_PLR_JUMP | sfx_player_jump.wav | Jump | P0 | Core runtime |
| SFX_PLR_LAND | sfx_player_land.wav | Landing | P0 | Core runtime |
| SFX_PLR_SHORT_ATK | sfx_player_short_attack.wav | Short attack | P0 | Core runtime |
| SFX_PLR_LONG_ATK | sfx_player_long_attack.wav | Long attack | P0 | Core runtime |
| SFX_PLR_HIT_CONN | sfx_player_hit_connect.wav | Attack hits enemy | P0 | Core runtime |
| SFX_PLR_HURT | sfx_player_hurt.wav | Player damaged | P0 | Core runtime |
| SFX_PLR_DIE | sfx_player_die.wav | Player death | P1 | Core runtime |
| SFX_PLR_CROUCH | sfx_player_crouch.wav | Crouch start | P2 | Core runtime |

**Quantity:** 8 player SFX

#### 9.2.2 Enemy SFX (location: `assets/sfx/enemies/`)

| Asset ID | File | Trigger | Priority | Phase Dependency |
|---|---|---|---|---|
| SFX_ENM_HIT | sfx_enemy_hit.wav | Any enemy hit | P0 | Core runtime |
| SFX_ENM_DIE_SMALL | sfx_enemy_die_small.wav | Small enemy death | P0 | Core runtime |
| SFX_ENM_DIE_LARGE | sfx_enemy_die_large.wav | Large enemy death | P1 | Core runtime |
| SFX_ENM_PROJ_FIRE | sfx_projectile_fire.wav | Projectile fired | P1 | Core runtime |
| SFX_ENM_PROJ_WALL | sfx_projectile_hit_wall.wav | Projectile hits wall | P2 | Core runtime |
| SFX_ENM_SERPENT_HISS | sfx_serpent_hiss.wav | Zone 2 serpent alert | P2 | Zone 2 |
| SFX_ENM_BIRD_CRY | sfx_bird_cry.wav | Zone 3 bird alert | P3 | Zone 3 |

**Quantity:** 7 enemy SFX

#### 9.2.3 Boss SFX (location: `assets/sfx/bosses/`)

| Asset ID | File | Trigger | Priority | Phase Dependency |
|---|---|---|---|---|
| SFX_BOSS_VENADO_STOMP | sfx_venado_stomp.wav | Venado stomp | P2 | Zone 1 boss |
| SFX_BOSS_VENADO_CHARGE | sfx_venado_charge.wav | Venado charge | P2 | Zone 1 boss |
| SFX_BOSS_VENADO_VINE | sfx_venado_vine.wav | Venado vine toss | P2 | Zone 1 boss |
| SFX_BOSS_VENADO_DIE | sfx_venado_die.wav | Venado death | P2 | Zone 1 boss |
| SFX_BOSS_REY_SPIT | sfx_rey_spit.wav | Rey venom spit | P3 | Zone 2 boss |
| SFX_BOSS_REY_SPLIT | sfx_rey_split.wav | Rey split | P3 | Zone 2 boss |
| SFX_BOSS_REY_DIE | sfx_rey_die.wav | Rey death | P3 | Zone 2 boss |
| SFX_BOSS_GAVILAN_DIVE | sfx_gavilan_dive.wav | Gavilán dive | P4 | Zone 3 boss |
| SFX_BOSS_GAVILAN_BEAM | sfx_gavilan_mask_beam.wav | Gavilán mask beam | P4 | Zone 3 boss |
| SFX_BOSS_GAVILAN_DIE | sfx_gavilan_die.wav | Gavilán death | P4 | Zone 3 boss |
| SFX_BOSS_PABURU_BEAM | sfx_paburu_eye_beam.wav | Paburu eye beam | P4 | Final boss |
| SFX_BOSS_PABURU_WAVE | sfx_paburu_wave.wav | Paburu spirit wave | P4 | Final boss |
| SFX_BOSS_PABURU_GOLD | sfx_paburu_gold_rush.wav | Gold sphere rush | P4 | Final boss |
| SFX_BOSS_PABURU_PEARL | sfx_paburu_pull.wav | Pearl pull | P4 | Final boss |
| SFX_BOSS_PABURU_CONV | sfx_paburu_convergence.wav | Convergence attack | P4 | Final boss |
| SFX_BOSS_PABURU_TRANS | sfx_paburu_transcend.wav | Paburu defeat | P4 | Final boss |
| SFX_BOSS_PHASE_CHG | sfx_phase_change.wav | Any boss phase change | P3 | Bosses |
| SFX_BOSS_RELIC_APPEAR | sfx_relic_appear.wav | Relic fragment appears | P3 | Boss reward |

**Quantity:** 18 boss SFX

#### 9.2.4 UI SFX (location: `assets/sfx/ui/`)

| Asset ID | File | Trigger | Priority | Phase Dependency |
|---|---|---|---|---|
| SFX_UI_MENU_MOVE | sfx_menu_move.wav | Cursor nav | P1 | UI system |
| SFX_UI_MENU_CONFIRM | sfx_menu_confirm.wav | Selection | P1 | UI system |
| SFX_UI_MENU_CANCEL | sfx_menu_cancel.wav | Back | P1 | UI system |
| SFX_UI_CHECKPOINT | sfx_checkpoint.wav | CP activated | P0 | Core runtime |
| SFX_UI_CP_RESTORE | sfx_checkpoint_restore.wav | Respawn at CP | P1 | Core runtime |
| SFX_UI_STAGE_BANNER | sfx_stage_banner.wav | Banner slide-in | P1 | Core runtime |
| SFX_UI_GAMEOVER | sfx_game_over.wav | Game Over | P1 | Core runtime |
| SFX_UI_HEART_RESTORE | sfx_heart_restore.wav | Heart refill | P2 | Core runtime |
| SFX_UI_STAGE_COMPLETE | sfx_stage_complete.wav | Stage clear | P1 | Core runtime |

**Quantity:** 9 UI SFX

#### 9.2.5 Environment SFX (location: `assets/sfx/environment/`)

| Asset ID | File | Trigger | Priority | Phase Dependency |
|---|---|---|---|---|
| SFX_ENV_JUNGLE | sfx_jungle_ambient.wav | Zone 1 ambient | P1 | Zone 1 |
| SFX_ENV_DATACENTER | sfx_datacenter_hum.wav | Zone 2 ambient | P2 | Zone 2 |
| SFX_ENV_WIND | sfx_wind_indoor.wav | Zone 3 ambient | P3 | Zone 3 |
| SFX_ENV_CEMETERY | sfx_cemetery_silence.wav | Final zone ambient | P4 | Final zone |
| SFX_ENV_SCREEN_SHAKE | sfx_screen_shake.wav | Screen shake | P1 | Core runtime |
| SFX_ENV_HAZARD | sfx_hazard_zone.wav | Damage tick | P1 | Core runtime |
| SFX_ENV_ONEWAY | sfx_one_way_platform.wav | Land on platform | P2 | Core runtime |

**Quantity:** 7 environment SFX

**TOTAL AUDIO FILES:** 12 + 8 + 7 + 18 + 9 + 7 = **61 audio files**

---

## 10. TMX MAPS

Location: `src/stages/` (source) → `assets/maps/` (built)

Required by docs/07_STAGE0_DESIGN.md, docs/16_WORLD_DESIGN.md:

| Map ID | Stage | Type | Width (px) | Priority | Phase Dependency |
|---|---|---|---|---|---|
| MAP_STAGE0 | Stage 0 | Tutorial | 3840 | P0 | Core runtime |
| MAP_1_1 | Stage 1-1 | Traversal | ~10000 | P1 | Zone 1 |
| MAP_1_2 | Stage 1-2 | Traversal+Combat | ~7680 | P1 | Zone 1 |
| MAP_1_3 | Stage 1-3 | Traversal+Combat | ~8960 | P1 | Zone 1 |
| MAP_1_4 | Stage 1-4 | Boss | 320 (fixed) | P2 | Zone 1 boss |
| MAP_2_1 | Stage 2-1 | Traversal | ~7680 | P2 | Zone 2 |
| MAP_2_2 | Stage 2-2 | Traversal+Combat | varies | P2 | Zone 2 |
| MAP_2_3 | Stage 2-3 | Traversal+Combat | ~7680 | P2 | Zone 2 |
| MAP_2_4 | Stage 2-4 | Boss | 320 (fixed) | P3 | Zone 2 boss |
| MAP_3_1 | Stage 3-1 | Traversal | ~8960 | P3 | Zone 3 |
| MAP_3_2 | Stage 3-2 | Traversal+Combat | ~10240 | P3 | Zone 3 |
| MAP_3_3 | Stage 3-3 | Traversal+Combat | ~6400 | P3 | Zone 3 |
| MAP_3_4 | Stage 3-4 | Boss | 320 (fixed) | P4 | Zone 3 boss |
| MAP_4_1 | Stage 4-1 | Traversal+Atmospheric | ~6400 | P4 | Final zone |
| MAP_4_2 | Stage 4-2 | Final Boss | 320 (fixed) | P4 | Final boss |

**Quantity:** 15 TMX files

---

## 11. CUTSCENE ASSETS

| Asset ID | Type | Description | Priority | Phase Dependency |
|---|---|---|---|---|
| CUT_INTRO | Image sequence | Prologue: John and Jin arrival | P1 | Story system |
| CUT_ZONE1_BOSS | Image sequence | Zone 1 boss intro | P2 | Zone 1 |
| CUT_ZONE2_BOSS | Image sequence | Zone 2 boss intro | P2 | Zone 2 |
| CUT_ZONE3_BOSS | Image sequence | Zone 3 boss intro | P3 | Zone 3 |
| CUT_FINAL_BOSS | Image sequence | Final boss intro | P4 | Final zone |
| CUT_ZONE1_WIN | Image sequence | Zone 1 cleared | P2 | Zone 1 |
| CUT_ZONE2_WIN | Image sequence | Zone 2 cleared | P2 | Zone 2 |
| CUT_ZONE3_WIN | Image sequence | Zone 3 cleared | P3 | Zone 3 |
| CUT_ENDING | Image sequence | Full ending | P4 | Final zone |

**Quantity:** 9 cutscene/image assets

---

## 12. GRAND TOTALS

| Category | Count | Notes |
|---|---|---|
| Player sprite sheets | 9 | 32×32 frames |
| Enemy sprite sheets | 81 | Various sizes |
| Boss sprite sheets | 42 | Various sizes |
| **Total sprite sheets** | **132** | |
| Tileset PNG + TSX pairs | 10 pairs (20 files) | 128×128 each |
| Background layers | 27 | Per stage × 3 layers |
| HUD sprites | 20 | |
| Shared sprites | 4 | |
| Font sprite sheets | 6 | |
| **Total image assets** | **189** | |
| Music tracks | 12 | OGG |
| Sound effects | 49 | WAV/OGG |
| **Total audio files** | **61** | |
| TMX maps | 15 | |
| Cutscene assets | 9 | |
| **Total map/cutscene** | **24** | |

### Asset file count summary

| Type | Files |
|------|-------|
| Sprite sheets (player + enemies + bosses) | 132 |
| Tilesets (PNG + TSX) | 20 |
| Backgrounds | 27 |
| HUD sprites | 20 |
| Shared sprites | 4 |
| Fonts | 6 |
| Audio (music + SFX) | 61 |
| TMX maps | 15 |
| Cutscene assets | 9 |
| **TOTAL** | **294 files** |

---

## 13. PRIORITY MATRIX

| Priority | Scope | Assets | Purpose |
|---|---|---|---|
| **P0** | Core runtime | Player (9), Stage0 tileset+bg (4), shared (1), fonts (2), SFX core (10), MAP 0 (1) | `python main.py` produces meaningful visual + audio |
| **P1** | Zone 1 | Enemy Zone1 (29), Zone1 boss (9), Zone1 tilesets (3), Zone1 BGs (9), HUD (10), UI SFX (5), maps 1-1..1-4 (4) | Full Zone 1 playable |
| **P2** | Zone 2 | Enemy Zone2 (24), Zone2 boss (9), Zone2 tilesets (3), Zone2 BGs (6), maps 2-1..2-4 (4) | Full Zone 2 playable |
| **P3** | Zone 3 | Enemy Zone3 (20), Zone3 boss (9), Zone3 tilesets (2), Zone3 BGs (7), maps 3-1..3-4 (4) | Full Zone 3 playable |
| **P4** | Final zone | Final boss (15), final tilesets (1), final BGs (3), maps 4-1, 4-2 (2) | Game complete |

---

## 14. PHASE DEPENDENCY SUMMARY

| Phase | Assets Delivered | Sprite Sheets | Audio | Maps |
|---|---|---|---|---|
| 0 (current) | Stub tileset, minimal TMX | 0 (stub only) | 0 | 1 (minimal fixture) |
| P0 — Core Runtime | Player, Stage0 full, shared, core SFX, core fonts | 13 | 10 music + SFX | 2 (Stage0 + full map) |
| P1 — Zone 1 | Zone1 enemies, boss, tilesets, BGs, HUD | 49 | 19 | 5 |
| P2 — Zone 2 | Zone2 enemies, boss, tilesets, BGs | 48 | 12 | 5 |
| P3 — Zone 3 | Zone3 enemies, boss, tilesets, BGs | 49 | 12 | 5 |
| P4 — Final Zone | Paburu, cemetery, final audio | 32 | 9 | 3 |
| **TOTAL** | | **220 sprite sheets** + **20 tilesets** + **27 BGs** + **30 HUD/shared/fonts** = **297 image files** | 62 | 20 |

---

## 15. RECOMMENDATIONS

1. **P0 minimum viable set** should be produced first: full Stage0 tileset (with 128×128 PNG + TSX), 3 Stage0 backgrounds, 9 player sheets, 3 Zone1 enemy sheets (Walker/Flying/Shooter), checkpoint and torch shared sprites, core fonts, core SFX, and the full `stage0.tmx` map. This unblocks `python main.py` to display a complete Stage 0 experience.

2. **Tileset stubs** at `assets/tileset_stage0.*` must be replaced with real graphics before the full TMX loads, because pytmx validates tile GIDs against the tileset image.

3. **Background layers** can be simple gradient fills at first — even solid-colour images prove parallax.

4. **Player sprites** should match the 32×32 frame size spec; the current 16×24 placeholder is too small.

5. **Boss sprites** can be deferred to P1–P4 as boss stages are completed; they are not required for the initial runtime demonstration.

6. **Audio** can be silent stubs (valid OGG/WAV headers, no content) to satisfy the loader while real tracks are composed.

7. **Fonts** can be placeholder 1-colour sheets; readability matters more than style.

8. **Cutscene assets** are lowest priority — text-only fallbacks work until images exist.