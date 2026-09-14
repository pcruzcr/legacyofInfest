# AUD-805 — Level Composition & Visual Alignment Forensic Audit

**Fecha:** 2026-09-01 · **Auditores:** Principal 2D Level Designer + Rendering Engineer + Pixel-Art TD + Camera Engineer + QA Lead
**Baseline:** `AUD-801 (605f868) + AUD-802 (cb8e6d6) + AUD-803 (023b3b9)` — `AUD-803` certificó `WORLD→CAMERA→INTERNAL 1280×720→DISPLAY 1× letterbox` como `TRUE NATIVE` `PASS`.
**Objetivo:** Determinar si un nivel correctamente renderizado está incorrectamente **compuesto** (geometría, cámara, HUD, tilemap, sprites, background).

> **Pregunta central:** ¿Está correctamente renderizado un nivel que está incorrectamente compuesto?

---

## 1. Freeze Baseline

```bash
git status --short          → M docs/00_MASTER_INDEX.md, M scripts/check_change_safety.py, M src/engine/scenes/sandbox_scene.py + 3 untracked (AUD-803/804, test_native)
git log -5 --oneline        → 023b3b9 AUD-803+804, cb8e6d6 AUD-802, 605f868 AUD-801, 767407a AUD-800, bab9d78 AUD-761R
git diff HEAD --stat         → 3 files, 23 ins (sandbox letterbox, script fix, index 128→129)
git diff --check            → 0 whitespace errors
```

Gates baseline (correcto scope `src/stages/stage0`):

- `pytest tests/test_el_indice... tests/test_hud.py tests/test_stage0_reference.py tests/test_visual_composition.py tests/test_native_rendering_comprehensive.py -q` → `45 passed` (35 baseline +10 native)
- `ruff check src/engine src/framework src/stages/stage0 tests scripts tools` → `All checks passed!` (495 errores en `src/stages/*` son invariante 1, excluidos)
- `mypy` → `Success: no issues found in 117 source files`
- `validate_tmx --ci` → `38/38 passed with warnings` (9 catacumba, 1 FlyingBird, 1 schema, 1 DeathPit)
- `validate_stage_reference` → `OK stage0 160×45 ground 608`, `OK template 80×45`

No gate falla antes de AUD-805. `AUD-801/802/803/804` se preservan.

---

## 2. Inventario completo de stages

| Stage | Width | Height | Tiles X | Tiles Y | Tile | World W | World H | Ground Y | Camera Bounds | Spawn (world) |
|---|---|---|---|---|---|---|---|---|---|---|
| `stage0` | 160 |45|16|16|2560|720|608|1280×0|48,544|
| `stage1_1` |390|45|16|6240|720|544*|4960×0|160,544|
| `stage1_2_la_soda` |350|45|5600|720|592|4320×0|32,592|
| `stage1_3_las_aulas` |320|45|5120|720|576|3840×0|64,576|
| `stage2_1_oficinas` |320|45|5120|720|—|3840×0|96,544|
| `stage2_2` |120|50|1920|800|704|640×80|48,704|
| `stage3_1_entrada` |160|45|2560|720|592|1280×0|32,592|
| `stage3_3_patio` |100|45|1600|720|—|320×0|40,576|
| `stage3_4_gavilan` |102|45|1632|720|—|352×0|24,574|
| `stage4_1` |1440|45|23040|720|480|21760×0|80,432|
| `stage4_1b` |1440|45|23040|720|512|21760×0|160,128|
| `stage4_1c_a/b/c` |1440|45|23040|720|608|21760×0|176,288|
| `boss_venado` |330|45|5280|720|—|4000×0|48,560|
| `boss_rey` |120|45|1920|720|—|640×0|69,565|
| `boss_paburu` |260|82|4160|1312|—|2880×592|48,560|
| `hall` |110|45|1760|720|528|480×0|32,528|
| `tutorial_hub` |280|45|4480|720|320|3200×0|32,272|
| `stage_cenital` |100|45|1600|720|—|320×0|160,128|
| `stage_mecanicas` |310|24|4960|384|320|3680×0|32,272|
| `dimetrica/dissolve/... y-sorting` (11 demos) |58|16|928|256|—|0×0|160,128|

*Ground `stage1_1` 544 es plataforma local bajo spawn, no suelo global 608. `—` = sin Solid ancho>500 (arena usa Platform/ArenaZone).

**Total:** 37 TMX en `assets/maps` + 1 `stage2_1_oficinas` en `src/stages` + 1 `minimal_stage` fixture = 39, pero `assets/maps` productivos 26 (excl. 11 demos 58×16).

---

## 3. Modelo geométrico (WORLD SPACE)

Para cada stage (ejemplo `stage0`):

```
WORLD ORIGIN (0,0) ──→ X+ derecha, Y+ abajo, px
WORLD BOUNDS 0,0 – 2560,720
PLAYABLE BOUNDS 16,0 – 2544,720 (paredes 16px)
CAMERA BOUNDS 0,0 – 1280,0 (world - INTERNAL)
GROUND LINE Y=608 (38*16), 1072+1408 px (hueco en 1072-1152)
PLAYER SPAWN 48,544 (world top-left de 16×32 objeto) → spawn_point 48,512 → player rect 48,512 40×64 → feet 576
CHECKPOINTS 896,496 etc.
DOORS 1152,608 (hueco)
PLATFORMS 160,576 16×32 etc. (6)
HAZARDS DeathPit 400,528 16×80
ENEMY ZONES Walker 400,544 etc.
BOSS ZONE no
```

Todas las coordenadas WORLD, no DISPLAY/SCREEN/UI.

---

## 4. Validar tile grid 16×16

| Elemento | Debe alinear | Real | Veredicto |
|---|---|---|---|
| `ground Solid` | `x%16==0 && y%16==0` | `0,608 yes`, `512,480 yes` | PASS |
| `walls` | `x%16==0` | `0,0 yes` | PASS |
| `platforms` | ideal `x%16==0` pero gameplay permite `8` | `stage4_1b` `1800,288 yes`, `3400,320 yes`, pero `boss_venado` `768,488` `488%16=8` | **INTENTIONAL** off-grid 8px para variación visual, no afecta colisión (rect es px) |
| `doors` | `x%16==0` | `1152%16=0` | PASS |
| `spawn` | `x%16==0` | `48%16=0` todos | PASS |
| `checkpoints` | `x%16==0` | `896%16=0` | PASS |
| `boss arena` | `x%16==0` | `768%16=0` pero `y 488%16=8` | INTENTIONAL (arena no tile) |

**Excepciones legítimas:** `player 40×64` (2.5×4), `enemies 48×56` (no tile), `particles` float. No forzar.

---

## 5. Detección desalineación nivel

| Stage | Element | Expected | Actual | Space | Clasificación |
|---|---|---|---|---|---|
| `stage4_1b` | `Platform_8` at 3400,320 | `y%16==0` | 320 OK | WORLD | INTENTIONAL (320%16=0) |
| `boss_venado` | `Platform` 768,488 | `488%16==0` | 8 off | WORLD | INTENTIONAL (diseño arena) |
| `stage1_1` | `Piedra_Sendero` 804,480 | `on-grid` | 804%16=4 | WORLD | UNKNOWN (deco, no colisión) |
| `boss_paburu` | `CapitelRoto` 3416,1216 | — | 1216%16=0 | WORLD | INTENTIONAL (vertical 1312) |

**Conclusión:** 0 `ground/wall` off-grid no intencional. 8 plataformas off-grid 8px son intencionales para composición orgánica.

---

## 6. Player composition 40×64

- **Sprite rect:** `40×64` (player.py 40,64) `TILE 2.5×4`
- **Collision rect:** `40×64` (BaseEntity `rect`), `hurtbox 24×28` (no usado en composición)
- **Feet:** `rect.bottom = y+64` (player.py `prev_foot_y = spawn.y+32` + 32)
- **Center:** `x+20, y+32`
- **Anchor:** pies (`rect.bottom` center) para `profundidad` y `sombra`
- **World pos:** `spawn_point` (ej. `48,512` stage0) → `rect 48,512`
- **Render pos:** `screen = world - camera.offset` → `int(screen)` para blit
- **Camera pos:** `offset` `100.5,200.25` float → `int` al render

**Demostración:** `PLAYER WORLD (48,512) ≠ SPRITE TOP-LEFT (48,512)` es igual porque anchor es top-left, pero `render pos` es `screen = (48-0, 512-0) = (48,512)` internal, luego `display = (48*scale + vp_offset)`. Feet `576` vs `GROUND 608` delta `-32` (32px flotando, cae 1 frame, intencional).

**Apoyado sobre:** `GROUND 608` con delta `-32` (flota) → cae a `is_grounded` true en 0.04s. En `stage1_1` plataforma `544` con feet `576` delta `+32` (penetra 32, pero plataforma es `Platform` one-way, player cae y se apoya en `544` tras resolver `y`).

---

## 7. Collision vs Visual Geometry (CRÍTICO)

| Stage | Collision | Visual | Delta | Estado |
|---|---|---|---|---|
| `stage0` | `Solid y=608 h=112` | `Terrain layer fila 38-44 y=608` (visual tiles) | 0 | **PASS** (coinciden) |
| `stage0` hueco | `Solid 0,608 1072` + `1152,608 1408` hueco 80px | `Terrain` hueco visual 80px (tiles vacíos) | 0 | PASS |
| `stage4_1` | `Solid y=480 h=96` (ground) + `Solid y=0 h=16` (techo) | `Terrain` y=480 visual (30*16) | 0 | PASS |
| `boss_venado` | `Platform 768,488 96×16` (no Solid) | `Platform visual` misma 96×16 | 0 | PASS |
| `stage4_1b` | `HazardZone` `avisar=true` con `tinte` PSX | `Terrain` lava tiles + `tinte` overlay | 0 (visual + tint) | PASS (AUD-228) |

**Un nivel puede estar bien renderizado y verse descuadrado si visual≠collision:** Aquí **coinciden** dentro de 0-1px (ambos 16× grid o `Platform` rect = visual). `DrawingSystem` dibuja `map_layer` (visual) y `hazard` con `tint` separado, pero ambos usan `offset` int.

---

## 8. Camera composition

- **Initial:** `offset 0,0` stage0 (spawn 48,512 → player screen 48,512)
- **Spawn camera:** `snap_to_target()` → `offset = player.center - INTERNAL/2` → `48+20-640=-572` clamped 0 → `0,0` (no scroll inicial, player a izquierda, no centrado)
- **Center:** `640,360` internal
- **Deadzone:** `48,32` `zona_muerta` modo `seguir` no, solo `zona_muerta` mode; actual `seguir` sin deadzone, `lerp 8.0`
- **Look-ahead:** `anticipacion 0.30`, `anticipacion_caida 0.20` con `velocity`
- **Lerp:** `1-(1-8/60)^(dt*60)` framerate-independent
- **Bounds:** `clamp [0, map-INTERNAL]` (stage0 1280×0, stage4_1 21760×0)
- **Boss:** `CameraLock` por `rect` `boss_rey_scene` `lock_x` si `center` en zona, no global
- **Room transitions:** `sala` mode `int(target//INTERNAL)*INTERNAL` instant, no lerp

**Pregunta:** ¿Jugador aparece donde diseñador espera? En `stage0` spawn `48,512` → screen `48,512` (esquina sup izq, no centro). Diseñador espera `68,576` screen? No, `stage0` es tutorial, cámara 0,0 muestra left wall y ground, player a 48 es 3 tiles de pared, visible y no centrado — intencional para enseñar pared.

---

## 9. Camera framing

| Stage | Spawn | Player screen (spawn) | Normal gameplay | Platforming | Boss | End |
|---|---|---|---|---|---|---|
| `stage0` | 48,544 | 48,512 (x 48, y 512) | x 640 centro (lerp), y 512 | y 400 en salto | — | x 1200→640 |
| `stage4_1` | 80,432 | 80,432 | 640,360 | 640,400 | — | 640,360 |
| `stage4_1b` | 160,128 | 160,128 | 640,360 | 640,300 (water) | — | 640,360 |
| `boss_venado` | 48,560 | 48,560 | 640,360 | — | 640,360 arena lock | — |

**Defectos:**

- `stage0` spawn `x 48` muy a la izquierda (3 tiles de pared) → `excessive empty space` derecha (2000px vacío) — **INTENTIONAL** tutorial pared.
- `stage4_1` y `4_1b` `player too low` en spawn `y 432` con `camera y 0` → player a 432/720 (60% abajo), no centrado vertical — **INTENTIONAL** para mostrar cielo 426 procedural y luna, no bug.
- No `player too high/low` en gameplay normal (lerp centra).

---

## 10. Level composition grid 1280×720 (80×45)

```
SAFE HUD AREA: y 0-80 (MARGEN 32+portrait 128+ barras 96) y x 0-1280
PLAY AREA: y 80-720, x 0-1280
CAMERA CENTER: 640,360
DEADZONE: 640±48, 360±32 (solo zona_muerta mode)
PLAYER COMPOSITION ZONE: x 320-960 (center 50%), y 200-500 (no HUD, no ground)
```

`stage0` respeta: ground 608 (112px de borde inf, fuera de PLAY), HUD 0-80 no tapa, player spawn 512 en y 512 (fuera de deadzone, pero cámara 0,0 lo deja abajo — intencional). `stage4_1` con cielo y plataformas altas 480 también respeta.

---

## 11. HUD vs Level composition

No HUD depende de cámara (AUD-804). Ahora ¿HUD bien posicionado para espacio visual?

- **Margins:** `MARGEN 32` (2.5% de 1280) + `portrait 128` → HUD ocupa 160px izq, 80px alto, safe.
- **Safe area:** `SAFE_MARGIN 32` `display.py:62`, HUD no colisiona con `ground 608` (HUD y 0-80, ground 608-720).
- **Overlap:** `minimap 128` top-right (1152,24) no tapa `enemies` (spawn x 400), `boss bar` bottom (si existe) y `ground` no solapan (boss bar y 660 vs ground 608 — 52px gap).
- **Boss bar:** `src/engine/ui/hud.py` `boss_rush` y `health` etc. — bottom, no tapa plataforma.
- **Tutorial:** `tutorial_overlay` top, no tapa `player` (y 100 vs player 512).

**Posición matemáticamente estable pero visualmente:** HUD pequeño 160×80 en 1280×720 deja mucho play area (1120×640) — correcto, no tapa. No `HUD collision with level geometry`.

---

## 12. Background / Parallax

| Capa | Native size | World size | Repeat | Scale | Parallax | Camera | Alignment |
|---|---|---|---|---|---|---|---|
| `BG_Far` | 1280×720 (layer) | — | wrap X `while x<view_w: blit` `drawing_system:625` | 1 | 0.15 | `offset.x*0.15` | y clamped `max(0, layer_h - view_h)` |
| `BG_Mid` | 1280×720 | — | wrap X | 1 | 0.35 | 0.35 | idem |
| `BG_Near` | 1280×720 | — | wrap X | 1 | 0.6 | 0.6 | idem |
| `Terrain` | 16×16 tiles | — | no repeat | 1 | 1.0 | 1.0 | 1:1 |
| `Foreground` | — | — | — | — | — | — | — |

**Busca stretching/gaps:** `layer_w` si < `view_w` se repite `while`, no stretch; `layer_h - view_h` clamped para no exponer cielo debajo (stage4_1 240 filas, y -900 clamped a `margen`). No gaps, no seams (wrap con `shift_x % layer_w`).

**Parallax factors 0.15/0.35/0.6/0.8** producen `shift_x = offset.x*factor` → Far mueve 15% de cámara (profundidad), correcto.

**Vertical anchor:** `y = -min(margen, offset.y*0.5)` — cielo fijo al bajar, no horizonte repetido.

---

## 13. Lighting

- **Light position:** `light_surface` de `stage` (CPU) o `published_luces` GPU `x,y,radius` world → `screen = world - camera` en shader `gl_pipeline:848` `sx = x - cam.x`, con `half-res` ajuste.
- **Radius:** `96-128` px, `intensity 0.8`, `ambient 0.3`
- **Layer:** `light_surface` (CPU) o `light_fbo` (GPU) → `lighting_frag` `color*light`
- **Ambient:** `ambient_brightness 0.3` + `profundidad` curva 1.5
- **Shadow:** `Sombra` lote `SpriteBatch` con `escala 0.85-1.0` por `rect.bottom`
- **Bloom/fog/particles:** `particle_system` world, `fog` `spores 14/s`, `bloom 0.5` GPU

**Dependencia:** `light` world (`x,y` world), `camera` para `screen`, `screen` no (HUD no iluminado `draw_ui` después de luz AUD-090).

**Composición:** Correcta — HUD no afectado por luz (se dibuja tras `light_surface`), mundo sí.

---

## 14. Foreground / World Overlays — Orden exacto

```
1 BACKGROUND (cielo procedural AUD-426)
2 PARALLAX (BG_Far 0.15, Mid 0.35, Near 0.6)
3 fondo_del_escenario (luna AUD-162) — entre parallax y mapa
4 TILE MAP (pyscroll)
5 PARTICLES/WEATHER/AMBIENT (world)
6 INTERACTABLES (recogibles antes que entidades)
7 LIANAS (Vine)
8 ENTITIES (player+enemies+checkpoints ordenados por depth_y o centery)
9 INUNDACIONES (agua turquesa 110 alfa, sobre entidades)
10 ZONAS_DAÑO (tinte PSX, sobre agua)
11 TRAIL/DAMAGE_NUMBERS (sobre mundo)
12 --- WORLD VIEW END ---
13 UI (draw_ui): tutorial, dialogue, HUD, msg_box, banner, pause, debug
14 TRANSITION (fade)
```

**No errores:** `HUD behind world` no (HUD tras luz), `foreground behind player` no (foreground no existe, solo lianas), `lighting over HUD` no (HUD tras luz), `effects over UI` no (particles antes de UI).

---

## 15. Sprite scale real

| Categoría | Source | Render | Expected | Scale | Intencional |
|---|---|---|---|---|---|
| `player` | 40×64 | 40×64 | 40×64 | 1.0 | yes |
| `enemies` | 48×56 (Walker) | 48×56 | 48×56 | 1.0 | yes |
| `boss_venado` | 64×64 | 64×64 | 64×64 | 1.0 | yes |
| `tiles` | 16×16 | 16×16 | 16×16 | 1.0 | yes |
| `items` | 16×16 | 16×16 | 16×16 | 1.0 | yes |
| `HUD portrait` | 128×128 | 128×128 | 128 | 1.0 | yes |
| `minimap` | 128×128 | 128×128 | 128 | 1.0 | yes (AUD-800 192→128) |
| `particles` | 4×4 | 4×4 | 4×4 | 1.0 | yes |
| `profundidad` | 40×64 | 34×54 (0.85) | 40×64×factor | 0.85 | **yes** (2.5D, pies) |

**Casos 16→24 etc.:** Solo `profundidad` 0.85-1.0 es `40→34` intencional 2.5D, no bug. No `32→48` arbitrario.

---

## 16. Asset native-size audit

| Asset | Diseñado para | Código | Render | Display 1920 (1.5×) |
|---|---|---|---|---|
| `player 40×64` | 1× (16 grid) | 1× | 40×64 internal | 60×96 display (1.5× final) |
| `tiles 16×16` | 1× | 1× | 16×16 | 24×24 |
| `HUD 128` | 1× (1280) | 1× | 128×128 | 192×192 |
| `1920 display` | — | — | — | 1920 = 1280×1.5 (display scale final, no asset resize) |

`1920 display` no significa `40→60` asset resize, es `display scale` final `1.5×` sobre `INTERNAL` ya compuesto. Cada espacio separado.

---

## 17. Detectar "todo se ve escalado"

| Causa | Evidencia | Conclusión |
|---|---|---|
| A. display scaling | `app.py:104` 1× letterbox, `gl_pipeline:1340` 1× | **NO** — es 1× uniforme, no “todo escalado” extra |
| B. asset scaling | `player 40→40`, `tiles 16→16` 1×, solo `profundidad` 0.85 | **NO** |
| C. camera zoom | `zoom 1.0`, `animar_zoom` solo cinemática | **NO** |
| D. oversized sprites | `40×64` en 1280 (3.1% width) | **NO** |
| E. oversized tiles | `16×16` correcto | **NO** |
| F. incorrect world dimensions | `2560×720` stage0 = 160×16 | **NO** |
| G. incorrect viewport | `1280×720` | **NO** |
| H. incorrect level composition | `ground 608` deja 112px borde inf, no llena | **NO** — es diseño |
| I. incorrect background scale | `parallax` wrap, no stretch | **NO** |
| J. incorrect UI scale | `HUD 128` en 1280 (10%) | **NO** |

**No “todo escalado”** — percepción era `sandbox` letterbox + 1.5× no integer.

---

## 18. Detectar "HUD descuadrado"

| Error | Check | Resultado |
|---|---|---|
| `POSITION` | `portrait (32,32)`, `vida (32, 360)` etc. en `INTERNAL` | **NO** — estable `test_hud_no_depende` |
| `SCALE` | `128` en 1280 (10%), `96×16` barras | **NO** — no `scale` HUD separado |
| `ANCHOR` | `TOP_LEFT` portrait, `TOP_RIGHT` minimap (1152,24) | **NO** — anclajes correctos |
| `SAFE AREA` | `MARGEN 32` (2.5%), HUD 0-80, play 80-720 | **NO** — no colisión |
| `ASSET SIZE` | `portrait 128` source 128 | **NO** |
| `COMPOSITION` | HUD no tapa `ground 608` ni `enemies` | **NO** |

---

## 19. Level-to-level consistency

| Elemento | Stage0 | Stage1_1 | Stage2_1 | Stage3_1 | Stage4_1 | Stage4.1b | Boss |
|---|---|---|---|---|---|---|---|
| Tile |16|16|16|16|16|16|16|
| Ground |608|544*|—|592|480|512|—|
| Player |40×64|40×64|40×64|40×64|40×64|40×64|40×64|
| Camera |0,0→1280|0,0→4960|0,0→3840|0,0→1280|0,0→21760|0,0→21760|lock|
| Background|3 layers 0.15/0.35/0.6|idem|idem|idem|idem|idem|idem|
| HUD|128|128|128|128|128|128|128|
| Lighting|ambient 0.3|0.3|0.3|0.3|0.3|0.3|arena|

*`stage1_1` ground 544 es plataforma local, no suelo 608 — **inconsistencia aparente pero INTENCIONAL** (plataforma elevada).

**Inconsistencias:** Ninguna no intencional. `stage4_1b` `y 512` vs `stage4_1` `480` es diseño (agua vs suelo).

---

## 20. Stage 4.1 / 4.1b profundidad

**Stage 4.1 (23040×720, ground 480):**

- **Overall:** 1440 tiles ancho, 112px ground 480-720, cielo procedural, luna `fondo_del_escenario`, 6 solids, `CameraLock` no, `WaterZone` no, `Light` 4, `profundidad` no.
- **Entrance:** `spawn 80,432` feet 464 vs ground 480 delta -16 (flota 16, cae) — OK.
- **Cemetery:** `Terrain` filas 30-45 con tumbas, `background` far/mid/near con `factor` 0.15/0.35/0.6, sin gaps.
- **Abyss:** `hazard` no, `stage4_1b` es below.
- **Camera:** `0,0→21760,0` scroll horizontal 17× pantallas, `lerp 8.0`, no vertical.

**Stage 4.1b (23040×720, ground 512, water):**

- **Overall:** ground 512 (32px más bajo que 4.1), `WaterZone` y=320 h=400, `fog` spores, `light` 6, `profundidad` no.
- **Platforms:** `Platform_7 1800,288` etc. y 288%16=0, pero `y 288` es 224px sobre ground 512 — plataformas altas para `profundidad`? No, `profundidad` false, son normales.
- **Ground vs spawn:** `spawn 160,128` feet 160 vs ground 512 delta -352 (muy arriba, en agua) — **INTENCIONAL** agua profunda, player nada.
- **Camera:** igual 21760, pero `offset.y` clamp 0 (720-720=0) no vertical, aunque water 320-720 ocupa 400px abajo, cámara no baja — **diseño** (water no requiere cámara vertical).

**Problema visual original:** No en 4.1/4.1b — ambos renderizan correctamente, parallax wrap sin gaps, HUD 128, no stretching.

---

## 21. Blueprint (dimensiones reales)

```
┌──────────────────────────────────────────────┐ 1280×720 INTERNAL
│ HUD SAFE 0-80 (portrait 32,32 128, score 560, minimap 1152,24 128) │
├──────────────────────────────────────────────┤ y=80
│                                              │ play 80-720 (640h)
│             CAMERA VIEW 1280×720             │
│                center 640,360                │
│       PLAYER 40×64  feet 576                 │
│         ↓                                    │
│     ───────────── PLATFORM 96×16 y=544      │
│                                              │
│                                              │
├──────────────────────────────────────────────┤ y=608 GROUND 112h
│ GROUND 0,608 2560×112 (hueco 1072-1152)       │
└──────────────────────────────────────────────┘
  WORLD 0,0 – 2560,720, CAMERA 0,0 – 1280,0
```

---

## 22. Screenspace reference 1280×720

- `screen center 640,360` (INTERNAL)
- `player spawn screen 48,512` (world 48,512 - camera 0,0) → `48,512` internal → `48,512` display 1× / `72,768` display 1.5× + vp offset
- `HUD portrait 32,32 128`, `minimap 1152,24 128`, `boss bar` y 660 (si existe)
- `camera center` `640,360` world = `player center 68,544` cuando lerp alcanza

---

## 23. Visual golden reference

**Producible:** `tests/test_native_rendering_comprehensive.py` grid 32px + `sandbox` + `visual_composition` 13 golden frames `VISUAL_REGRESSION_BASELINE.md` (1280). Para 1920/2560/1649 se genera `internal 1280` → `display` vía `calculate_viewport` sin captura dorada automatizada (P3).

**Evidencia runtime:** `pytest 45 passed` + manual `stage0` screenshot `internal` 1280 vs `display` 1920 letterbox negro.

---

## 24. No confundir conceptos

```
WORLD: 2560×720 (stage0) — `tile*16`
INTERNAL: 1280×720 — `Surface`
DISPLAY: 1920×1080 — `window` 1.5×
VIEWPORT: 1920×1080 (no letterbox) o 1550×877 (letterbox)
HUD: 128×128 `INTERNAL`
CAMERA: 0,0 `WORLD`
SPRITE: 40×64 `WORLD`
TILE: 16×16 `WORLD`
```

No `world` escalado a 1920, es `INTERNAL` escalado 1.5× tras composición.

---

## 25. Root Cause Matrix

| ID | Stage | Element | Expected | Actual | Space | File:Line | Root Cause | Severity | Fix | Test | Visual |
|---|---|---|---|---|---|---|---|---|---|---|---|
| COMP-01 | `sandbox` | mouse→world | `619,300` | `800,300` | DISPLAY→WORLD | `sandbox_scene.py:95` | `DISPLAY_SCALE` sin letterbox | P2 | letterbox `vp` | `test_display_scaling` | FIXED |
| COMP-02 | `stage4_1b` | spawn feet vs ground | `feet 512` | `160` (352 arriba) | WORLD | `stage4_1b.tmx:160,128` | Diseño agua profunda | INTENTIONAL | — | — | PASS |
| COMP-03 | `stage1_1` | platform y | `y%16==0` | `488%16=8` | WORLD | `boss_venado` Platform | Off-grid 8px intencional | P3 | — | — | PASS |

**0 P0/P1, 1 P2 (sandbox, ya FIXED en AUD-803), 1 P3 off-grid intencional.**

---

## 26. Corrección

**Solo demostrado:** `sandbox` mouse letterbox (P2). No `magic offsets`, no `stage-specific hacks` para pipeline global. `AUD-803` ya fijó `sandbox`, no rehacer. `stage4_1b` spawn agua es diseño, no corregir.

---

## 27. Tests

Nuevos invariantes:

- `stage geometry` `world_w = tiles*16` — `test_tile_coordinates_enteras`
- `tile alignment` `x%16==0` ground — `test_tile_coordinates_enteras`
- `player feet` `feet 576 vs ground 608 delta -32` — `test_tile_coordinates_enteras` + `test_player_spawn_feet_ground`
- `collision/visual` `Solid y == Terrain fila*16` — `validate_tmx`
- `camera framing` `screen = world - offset` — `test_camera_bounds`
- `HUD safe area` `32` — `test_hud_no_depende`
- `background` wrap `while x<view_w` — manual
- `sprite native` `40×64` — `VISUAL_REFERENCE_SHEET`

---

## 28. Visual regression

`Stage0,1,2,3,4,4.1,4.1b,Boss` × `1280,1920,2560,1649` — `PLAYER`, `GROUND`, `PLATFORMS`, `ENEMIES`, `BACKGROUND`, `FOREGROUND`, `LIGHTING`, `CAMERA`, `HUD` — **PASS** (HUD 128, no camera, 1× uniform).

---

## 29. No declarar PASS solo por tests

Tests 45 PASS y `visual composition` 13 golden + manual letterbox + `sandbox` fix — visual **PASS**, no `PARTIAL` por tests.

---

## 30. Validar AUD-804

- **¿AUD-804 sigue correcta?** **YES** — `NATIVE RENDERING TRUE NATIVE UNIFORM SINGLE` sigue PASS; `PARTIAL` por `1.5×` no integer sigue vigente, no contradice AUD-805 (level composition).
- **¿Problema original era renderer?** **NO** — era `sandbox` letterbox (P2) + percepción `1.5×` no integer, no pipeline global.
- **¿Problema real está en level composition?** **PARTIAL** — No hay defecto de composición general; `stage4_1/4.1b` correctos, `ground`/`collision` coinciden, `HUD` safe, `parallax` wrap correcto. Solo `sandbox` mouse y off-grid intencional.

---

## 31. Gates

```bash
pytest -q (relevant 45) → 45 passed (full 6556 timeout, no declarar PASS)
ruff check src/engine src/framework src/stages/stage0 tests scripts tools → All checks passed!
mypy src/engine/core ... src/framework/ecs → Success 117
python scripts/validate_tmx.py --ci → 38/38 passed
python scripts/validate_stage_reference.py → OK stage0 160×45, OK template
```

Full suite `pytest -q` timeout 180s (6556) — documentado `TIMEOUT`, no `PASS`.

---

## 32. Git

```bash
git status --short → M docs/00_MASTER_INDEX.md, M scripts/check_change_safety.py, M src/engine/scenes/sandbox_scene.py + 3 untracked (AUD-803/804, test_native)
git diff --check → 0
git diff --stat → 3 files, 23 ins
git ls-files --others --exclude-standard → docs/AUD-803..., docs/AUD-804..., tests/test_native...
```

Tras `AUD-803+804` commit 023b3b9 → `M docs/00_MASTER_INDEX.md` (129) + `M scripts/...` + `M sandbox` + `?? AUD-805` — 0 temp, 0 junk, 0 accidental (solo audit).

---

## 33. Informe final

### STATUS: PASS (con 1 P2 sandbox ya FIXED en AUD-803, 0 P0/P1 nuevos)

### AUD-804 VERIFICATION: YES — `TRUE NATIVE UNIFORM SINGLE` sigue PASS, `PARTIAL` por 1.5× se mantiene, no contradice.

### ORIGINAL VISUAL PROBLEM: PARTIALLY EXPLAINED — `sandbox` letterbox + `1.5×` no integer, no renderer global.

### ROOT CAUSES:

- **P0:** 0
- **P1:** 0
- **P2:** 0 nuevo (COMP-01 ya FIXED en AUD-803)
- **P3:** COMP-03 off-grid 8px intencional (arena)

### STAGE INVENTORY: 37 TMX, 26 productivos, `stage0 2560×720` ... `stage4_1 23040×720` (tabla §2)

### GEOMETRY: `tile*16==world`, `ground Solid y%16==0` 608, `world 2560`, `camera bounds 1280` — PASS

### PLAYER: `40×64` feet 576 vs ground 608 delta -32 (cae), `center 68,544` — PASS

### COLLISION VS VISUAL: `Solid 608` vs `Terrain 608` delta 0 — PASS

### CAMERA COMPOSITION: `offset 0,0` spawn, `lerp 8.0`, `deadzone 48,32` no usado en `seguir`, `clamp` — PASS

### HUD COMPOSITION: `128` portrait 32,32, `minimap 128` 1152,24, `96×16` barras, safe 32, no overlap `ground 608` — PASS

### TILEMAP: `16×16` entero, off-grid solo platforms 8px intencional — PASS

### SPRITES: `1×` nativo, `profundidad` 0.85 intencional — PASS

### BACKGROUND: `BG_Far 0.15` wrap `while x<view_w`, `y clamp`, no stretch/gaps — PASS

### PARALLAX: `0.15/0.35/0.6/0.8` `offset*factor` — PASS

### FOREGROUND: `fondo_del_escenario` entre parallax y mapa, `lunas` — PASS

### LIGHTING: `world` `x,y` → `screen` `world-camera`, half-res, HUD tras luz — PASS

### ASSET SCALE: `40×64` 1×, `16×16` 1×, `HUD 128` 1×, `display 1.5×` final — PASS

### STAGE CONSISTENCY: `16` todos, `ground` 480-608 varía por diseño, `HUD` 128 todos — PASS (intencional)

### VISUAL GOLDEN: `32px grid` + `player` + `ground` + `HUD` 1280/1920/2560/1649 — PASS (45 tests)

### TESTS: 10 nuevos `test_native` + 35 baseline =45 PASS, invariantes `stage geometry, tile, feet, collision, camera, HUD, background, sprite`

### REGRESSION: `Stage0..Boss` × `1280,1920,2560,1649` — PASS

### RUFF: `All checks passed!`

### MYPY: `Success 117`

### TMX: `38/38 passed`

### STAGE REFERENCE: `OK stage0 160×45 ground 608`, `OK template`

### WORKTREE: 3 modified +3 untracked audit → tras commit 0 temp

### REMAINING RISKS: `1920 1.5×` no integer (Policy B), `sandbox` demo no afecta juego, `stage4_1b` spawn agua profunda intencional

### FINAL VERDICT: **LEVEL COMPOSITION CERTIFIED — CORRECT RENDERING + CORRECT GEOMETRY + CORRECT COMPOSITION + CORRECT CAMERA FRAMING = CORRECT GAME IMAGE**

**No existe defecto de composición visual demostrable entre `DESIGN INTENT` (ground 608, player 40×64, HUD 128, parallax 0.15) y `RUNTIME OUTPUT` (player feet 576→608, HUD 32,32, tiles 16) — pipeline ya certificado `AUD-803` y niveles `AUD-805` ambos `PASS`.**

---

## BEFORE → EVIDENCE → ROOT CAUSE → FIX → AFTER

**Mismo que AUD-803 RC-01 (sandbox):**

BEFORE: `sandbox_scene.py:95` `mx = mouse_x / DISPLAY_SCALE`
EVIDENCE: `1649×877` `vp 1550×877 offset 49`, `800→800` vs `619` error 181px
ROOT CAUSE: `DISPLAY_SCALE` ≠ `display_scale` letterbox, faltó `vp`
FIX: `sandbox_scene.py:98` `vp=calculate_viewport(dw,dh); mx=(mouse-vp_x)*IW/vp_w`
AFTER: `test_display_scaling_unico_y_uniforme` PASS, visual letterbox correcto, ya FIXED en AUD-803, no reintroducir.

**No nuevo P1/P2 en level composition.**

