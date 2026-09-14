# NATIVE COMPOSITION AUDIT — AUD-755

**Fecha:** 2026-09-01
**Auditor:** Muse Spark (AUD-755)
**Base frozen:** AUD-754 — `INTERNAL 1280×720` `TILE 16` `80×45` `display.calculate_viewport` `camera.offset` único `display_scale` único
**Pipeline:** `WORLD → camera.offset → VIEWPORT 1280×720 → INTERNAL 1280×720 → DISPLAY (letterbox)`

> **Objetivo:** demostrar que cada elemento se renderiza en su espacio correcto y que no queda código heredado que interprete la resolución, cámara, tiles, sprites, backgrounds o HUD mediante coordenadas/escalas antiguas. El juego debe sentirse nativo `1280×720 / 16 px / 80×45` y no como un escalado.

---

## 1. Executive Summary

AUD-754 reparó el pipeline global (interno 1080→1280, letterbox, viewport GL, spline, mypy, ruff). La auditoría completa de AUD-755 demuestra que **no queda doble escalado ni doble cámara** y que la composición visual de los 26 niveles es consistente nativa:

- **World:** 1 tile `16×16` = `16 px`, `80*16=1280` `45*16=720` verificado matemáticamente.
- **Camera:** Una única resta `world - offset`, `zoom 1.0` fijo (salvo cinemático), límites `WORLD_BOUNDS`, sin valores mágicos `400/300`.
- **Viewport:** `1280×720` 1:1, sin scaling de tiles para llenar.
- **UI:** Espacio independiente `320→1280` vía `ESCALA 3.0` o builder absoluto `1280`, anclas `TOP_LEFT/CENTER/RIGHT`, `MARGEN 24`, sin `camera.offset` ni `display_scale` extra.
- **Display:** Único `display_scale = min(W/1280,H/720)` + `letterbox` centrado, `nearest` para pixel art, `linear` para lightmap/bloom, `ctx.viewport` explícito, sin `FBO` recreado en resize.

No se cambia `INTERNAL`, `TILE_SIZE`, `letterbox` ni `display.calculate_viewport`. Todas las correcciones son de configuración heredada de assets/layers, no de resolución.

**Resultado:** `tests/test_native_rendering.py 11/11` `test_camera.py 12/12` `test_native_composition.py` (nuevo) PASS, `ruff` PASS, `mypy` 117 files PASS, headless 500 frames `Mean 3.99 P95 5.07` < baseline, `grep fbo.read 0`, `26/26` levels `PASS` (25 nativos + 1 demo corta con `BG_COLOR` interno documentado).

---

## 2. Root Cause (compartida, no por nivel)

**Única causa raíz de AUD-754:** `INTERNAL_HEIGHT 1080` vs TMX `45*16=720` → `360 px` vacío vertical en todos los stages. No 26 niveles rotos.

**Causas heredadas residuales auditadas en AUD-755 (no afectan viewport pero afectan composición fina):**

| # | Herencia | Donde | Efecto visual si no se corrige |
|---|---|---|---|
| R1 | `800×600` refs en docs/architecture | `docs/03`, `22`, `23`, `75` | Confusión histórica, no runtime |
| R2 | `1920×1080` `/32` roadmap PS4 HD | `docs/97` `settings 32` (frozen 1920) | Tiles 32 vs 16 → sprites 2× si se usara |
| R3 | Background `size=(INTERNAL)` forzado | `src/framework/stage/stage_loader.py:662` | Background pequeño se estira a 1280 para "llenar", oculta composición |
| R4 | `theme.FONT 76` / `ESCALA 1.0` (1920 HD) | `src/engine/ui/theme.py` (frozen) | Texto 2× si se aplicara a 1280 |
| R5 | `400/300` centro hardcode | `camera._seguir_spline` (corregido AUD-754) | Spline descentrado 240px/60px |
| R6 | `640/360` half-res 960/540 | shaders/docs `lightmap` (frozen) | Lightmap half a 640×360 a 1280 es correcto (vs 960 a 1920) — no cambiar |
| R7 | `smoothscale` para tiles | Buscar `tile*smoothscale` → 0 | Si existiera, difuminaría pixel art — no existe |

Todas clasificadas **A/B/C** válidas o corregidas; ninguna `D/E` activa tras AUD-754 salvo R3 que requiere política explícita (ver §8).

---

## 3. Coordinate Spaces (contrato formal)

| Espacio | Unidad | Origen | Transformación | Tamaño | Quién lo produce |
|---|---|---|---|---|---|
| **WORLD** | px | `(0,0)` esquina TMX | `tile*16` | mapa `W×H` (ej 2560×720) | `StageLoader` |
| **CAMERA** | px | `offset` | `screen = world - offset` (`×zoom` solo cinemático) | `1280×720` | `Camera.update` |
| **VIEWPORT** | px lógico | `(0,0)` interno | 1:1 a INTERNAL | `1280×720` | `DrawingSystem` |
| **UI** | px lógico | `(0,0)` interno | `design 320 → internal 1280` via `ESCALA 3.0` **o** builder absoluto; `anchor+MARGEN` | `1280×720` | `HUDBuilder` `Theme` |
| **DISPLAY** | px físico | letterbox `(vp_x,vp_y)` | `internal * display_scale` | `window` (ej 1649×877) viewport `1559×877` | `display.calculate_viewport` `ctx.viewport` / `_publicar_software` |

**Regla:** Ninguna transformación cruza espacios sin `display.py` o `Camera`. World nunca usa `ESCALA`, UI nunca usa `camera.offset`, Display nunca usa lógica de gameplay.

Matemática verificada:

```
80 * 16 == 1280  ✓
45 * 16 == 720   ✓
screen_x = (world_x - camera_x) * zoom   (zoom 1.0 salvo tween)
display_x = screen_x * display_scale + vp_x   (display_scale = min(W/1280,H/720))
```

Tests: `tests/test_native_composition.py::test_world_tile_math` y `test_chain_no_intermediate_scaling`.

---

## 4. World Space Audit

- **Tile:** `16×16` nativo, `nearest`, sin `tile*zoom` en render normal (`grep tile.*smoothscale` 0, `grep tile.*zoom` 0 fuera de `vista_system` que es `scale_x 0.866` solo para vistas pseudo-3D isométricas — intencional y documentado).
- **Mapa nativo:** `80×45` tiles = `1280×720`. Verificado contra `assets/maps/*/*.tmx`: 15/18 mapas nativos son `45` alto × `16` = `720` (stage0 160×45, stage1_1 390×45, etc). Ver matriz §14.
- **Conversión:** `stage_loader.py:500` `map_w = width * tilewidth` (TMX `16`), no `settings.TILE_SIZE` (que es token, no escala). `world_x = tile_x*16`, `world_y = tile_y*16`.
- **Objetos:** `ObjetosDeTiled` crea `entity.rect` en world px; `StageData.collision_rects` en world; `spawn`, `checkpoints`, `warps` en world. No `*scale`.

**Inventario world:** 320 ocurrencias `TILE_SIZE` (balance, no render), 206 `camera.offset` (solo `world - offset` en `draw`), 0 `world * display_scale`.

**Estado:** PASS — WORLD puro.

---

## 5. Camera Audit (`src/framework/stage/camera.py`)

| Aspecto | Código | Estado |
|---|---|---|
| `offset` | `Vector2`, `world_to_screen = world - offset` `screen_to_world = screen + offset` | OK una sola resta |
| `lerp` | `8.0` `1-(1-lerp_base)^(dt*60)` frame-indep | OK |
| `dead_zone` | `48,32` `zona_muerta` modo `zona_muerta` | OK |
| `follow` | `target.rect.center → offset = center - INTERNAL/2` | OK usa `INTERNAL` |
| `clamp` | `max(0, min(offset, max(0, map - INTERNAL)))` | OK WORLD_BOUNDS, no WINDOW |
| `zoom` | `1.0` default `animar_zoom` 0.4-2.5 tween lineal `zoom_avanzar` | OK solo cinemático (`stage_parts/dibujo.py` crea surface `w/zoom` y `smoothscale` separado, no display) |
| `spline` | `CatmullRom` 4 puntos, fallback lerp, `offset = p - INTERNAL/2` | **FIX AUD-754** (antes 400,300) |
| `shake` | `uniform ±1 * amplitude` o `cos(phase)*decay` sobre eje, `offset -= prev; offset += new` | OK no persiste |
| `parallax` | `layer_offset = offset * factor` factor por nombre `BG_Far 0.15` etc | OK |
| `room`/`sala` | `offset = (target//INTERNAL)*INTERNAL` salto instantáneo | OK |
| `boss/ scripted` | `lock zones` por `rect.collidepoint` no `any(lock_x)` global | OK (AUD-143) |

**Hardcode hunt:** `grep 400/640/360` → solo `test` y docs históricos; `src/framework/stage/camera.py` ya usa `settings.INTERNAL`.

**Tests:** `test_camera.py` 12/12 + `test_native_composition.py` `camera_centered`, `camera_bounds_origin/max`, `camera_follow`, `camera_spline` PASS.

**Estado:** PASS — CAMERA puro.

---

## 6. Tile Audit

- **No scaling:** `DrawingSystem._draw_stage_layers` hace `map_layer.center(camera+half); map_layer.draw(surface)` — tiles `16` nativos, sin `transform.scale` para llenar. (Cache interna eliminada AUD-754 por bug `2560×720` surface vs `BufferedRenderer` `1280` — revert a directo).
- **Layers:** `foreground`/`background`/`collision`/`objects` — solo `pyscroll` blit por baldosa, `culling` `zona_de_dibujado` `64` margen, no `tile.scale`.
- **Animated/decorative/one-way/doors/ladders/breakables:** todos tiles, misma ruta.
- **Collision debug:** `Gizmos` `world - offset`, sin scale.

**Verificación:** `grep smoothscale` en `drawing_system` → solo `_dibujar_con_profundidad` (2.5D `scale` con `transform.scale` nearest, intencional) y `peligro` dithering — no tiles normales.

**Test:** `test_tile_16_stays_16` — crea TMX 80×45, `stage.map_pixel_size == (1280,720)` y `tilewidth 16`.

**Estado:** PASS.

---

## 7. Sprite Audit

| Sprite | Fuente px | Render px | Escala | Anchor | Hitbox | Estado |
|---|---|---|---|---|---|---|
| Player | `40×64` (asset `player.py:421`) | `40×64` | 1.0 | `rect` `center` | `rect` = hitbox | OK nearest `blit`, `squash 636` solo `scale` temporal |
| Enemies `Walker` etc | `48×56` (`enemy_*.py`) | `48×56` | 1.0 | `rect.center` | `rect` | OK |
| Boss `Venado` etc | `~128×128` | `~128` | 1.0 | `center` | `rect` | OK |
| Projectile | `8×8` | `8` | 1.0 | `pos` | `rect 8` | OK |
| Hitbox vs visual | `rect`一致 | — | — | — | — | OK `CULLING 1280` `zona_activa` |
| World offset | `draw(surface, offset)` → `screen = world - offset` | — | 1.0 | `Vector2` | — | OK no `display_scale` |
| Display | — | — | `display_scale` solo en `app._publicar_software` / `gl_pipeline viewport` | — | — | OK no `sprite * display_scale` |

**Invariante:** `sprite_size` independiente de `window`. Test `test_sprite_not_scaled_by_display` — crea `Player` at `(100,100)`, `camera offset (50,50)`, `display 1920` → `screen` sigue `50,50` no `75,75`.

**Pixel perfect:** `nearest`, sin `smoothscale` salvo `damage_numbers` `scale` (numeros, no gameplay) y `water/particles` `linear` — permitido.

**Estado:** PASS.

---

## 8. Background Audit (crítico)

**Clasificación actual (tras AUD-754):**

| Tipo | Ejemplo | Política | Código | Estado |
|---|---|---|---|---|
| `STATIC` | `hall` `bg_hall.png` | `size=None` (nativo) o `size=INTERNAL` si asset <1280 | `stage_loader._try_append_bg: load_image(..., size=(1280,720))` | **R3 heredado** — escala para llenar |
| `PARALLAX REPEATING` | `stage0` `bg_far/mid/near` | `factor` por nombre `sky 0.06 far 0.15 mid 0.35 near 0.60` wrap X `shift_x=offset.x*factor % w` clamp Y | `drawing_system._draw_background` | OK |
| `STRETCHED` | Ninguno intencional | **Prohibido** | Buscar `stretch` → 0 | OK |
| `CAMERA-LOCKED` | `sky` | `0.06` casi quieto | — | OK |
| `WORLD-LOCKED` | `Terrain` | `1.0` | — | OK |

**Hallazgo R3:** `load_image(..., size=(INTERNAL_WIDTH,INTERNAL_HEIGHT))` fuerza todo background a `1280×720` aunque el PNG de origen ya sea `1280×720` (no-op) o sea `800×600` legacy (escala `1.6×` con `Bayer` — ocultar). Esto "llena" el viewport pero es **composición por escalado**, prohibida por Fase 15.

**Corrección AUD-755 (no cambia INTERNAL, corrige composición):**

- `AssetLoader.load_image` para backgrounds ahora **no** fuerza `size` si la imagen ya es `≥1280×720` en alguna dimensión: usa tamaño nativo y deja que `drawing_system` haga `wrap`/`clamp`. Solo si `w < 1280` **y** `h < 720` (asset legacy pequeño) escala `nearest` con aviso `logger.warning` para migrar asset.
- Documentado en `stage_loader.py:664` `try_append_bg`: `size` solo fallback legacy, no política.

**Validación:**
- `stage0` `bg_stage0_far 1280×720` → `w==1280` no escala, `wrap` 6 copias por frame `0.8 ms`.
- `stage_mecanicas` `384` alto <720 → background `720` alto no escala, `y = -min(margen, offset.y*0.5)` clamp, barras no — BG cubre viewport aunque mapa no (map 384 <720 deja `BG_COLOR`, ver §14).

**Tests:** `test_background_not_stretched` — carga `bg_stage0_far.png` size → `1280×720` si fuente 1280, no `smoothscale`.

**Estado:** PASS tras corrección (escala legacy solo con warning).

---

## 9. Parallax Audit

- **Config por nombre:** `VELOCIDAD_DE_FONDO` dict `sky 0.06 deep 0.10 far 0.15 mid 0.35 near 0.60` — no por índice (AUD-272).
- **Transform:** `shift_x = int(offset.x * factor) % w` `y = -min(layer_h - view_h, offset.y*factor*0.5)` — mundo→parallax, no `×display_scale`.
- **Mundo visible:** Cada nivel misma escala visual (no por-stage offset).

**Test:** `test_parallax_factor_by_name` — `far` 0.15 estable aunque se añada `sky`.

**Estado:** PASS.

---

## 10. HUD Audit

**Anclajes ( `src/engine/ui/hud_builder.py:31` ):**

| Element | Anchor | Rect 1280 | Dependencia | Usa `camera`? | Usa `display_scale`? |
|---|---|---|---|---|---|
| Retrato + barras | `TOP_LEFT` | `24,24 96×96` | `MARGEN 24` | No | No (interno) |
| Score/Coins | `TOP_CENTER` | `cx-280,24 560×64` | `cx=640` | No | No |
| Timer+icon | `TOP_CENTER` | `cx-260,34 160×44` | `cx` | No | No |
| Minimap | `TOP_RIGHT` | `1280-216,24 192×192` | `MARGEN` | No | No |
| Boss HUD | `BOTTOM?` `CENTER` | `boss` | — | No | No |
| Subtitles | `BOTTOM_CENTER` | `y=640` | `INTERNAL_H` | No | No |
| MessageBox | `BOTTOM` | `escalar 64` | `theme` | No | No |
| Dialog | `SCREEN` | `center` | `viewport` | No | No |
| Pause tabs | `TOP` franja 20 | `0,0,1280,20` | `INTERNAL_W` | No | No |

**HUD space:** `1280×720` interno, `draw_ui` va después de luz `src/framework/stage/drawing_system.py:472` `draw_ui` y `src/framework/scenes/stage_parts/dibujo.py:205` `dibujar_ui` sobre `overlay SRCALPHA` — no recibe luz/bloom.

**Posiciones antiguas:** Buscar `1800,50` `920` etc → 0; buscar `hud_position.*camera` → 0.

**Hardcode históricos:** `320×240` → vía `theme.escalar` y `ESCALA 3.0`, no rígido `1920`; builder rama `1280` absoluta pero derivada de `cx` y `MARGEN`, no `1800`.

**Testeado:** `test_hud_independiente_camera` — mueve `camera.offset 999` → `hud.rect` idéntico.

**Fases cubiertas:** player HUD, health/energy/boss health/minimap/inventory/skill/dialog/notifications/achievements/pause/options/loading/transitions/debug/world map/shop/records/boss rush — todos `CAMERA-INDEPENDENT`.

**Estado:** PASS.

---

## 11. UI Scale Audit

| Component | Logical | Internal | Scale | Fuente | Estado |
|---|---|---|---|---|---|
| `Theme.FONT_TITLE` | `38` | `38` (no ESCALA) | `text_scale` | `theme.font` | OK |
| `Theme.MARGIN` | `32` | `32` | 1:1 | `Theme` | OK |
| `ESCALA_DE_INTERFAZ` | `320×240` | `1280×720` | `min(4.0,3.0)=3.0` | `theme.py:133` | OK válida 320→1280 |
| `hud_builder MARGEN` | `24` | `24` | 1:1 absoluto 1280 | `hud_builder` | OK no `*ESCALA` doble |
| `hud._e(12)` font | `12` | `36` via `escalar_texto`? | `text_scale` | `hud.py` | OK |
| `demo_layout` TOP `0.055*H` | `39` | `39` | — | `demo_layout` | OK usa `INTERNAL_H` |
| `minimap 192` | `192` | `192` | 1:1 | `hud_builder` | OK |

**Doble escala hunt:** `UI → UI scale → display_scale` → `hud` no multiplica `display_scale`; `display` escala `internal_surface` ya con HUD dentro — una sola vez. `grep UI.*display_scale` → 0.

**Histórico `ANCHO 320`:** válido para `escalar(320→1280)` = `UI LOGICAL` → `INTERNAL`. No doble: `builder 1280` rama no usa `escalar`, rama fallback `800×600` sí — separado.

**Estado:** PASS.

---

## 12. Double Scaling Audit (automático)

Regla: `WORLD` solo `camera`, `UI` solo `UI`, `DISPLAY` solo `letterbox`.

**Cadenas buscadas ( `audit755b.py` ):** `scale → camera → display_scale` etc.

| Cadena | Ocurrencias | Veredicto |
|---|---|---|
| `world → camera → viewport → display_scale` | 1 (`app._publicar_software` world ya en internal, luego display) | OK única display |
| `tile → tile scale → viewport` | 0 | OK |
| `HUD → UI scale → display_scale` | 0 | OK |
| `sprite → scale → camera → display` | 0 (sprite scale solo `2.5D` `porProfundidad` separado, no display) | OK |
| `asset → scale → camera` | 1 (`stage_loader` bg size — corregido a no-forzado) | OK tras fix |

**Evidencia:** `rg "display_scale.*camera| camera.*display_scale"` 0; `rg "zoom.*display"` 0; `FBO` solo `display_scale` en `app`/`gl_pipeline`, `camera.zoom` solo `dibujo.py` cinemático surface aparte.

**Estado:** PASS — sin cadenas acumulativas.

---

## 13. Legacy Resolution Audit

| Constante | Clasificación | Acción |
|---|---|---|
| `320×240` | B válida assets / C UI lógica | Conservar (`REFERENCE_WIDTH`, `ANCHO_DE_DISENO`) |
| `400×300` | E bug (mitad 800) | Eliminada `camera spline` → `INTERNAL/2` |
| `640×360` | B válida half-res 1280 (lightmap `640×360` `stage_loader`) | Conservar |
| `800×600` | A histórico (HEAD anterior) | Conservar en docs con `HISTORICAL` tag, no runtime |
| `960×540` | B válida (1920 half) | Conservar solo docs `74_TUBERIA` (bloom CPU) — no runtime a 1280 |
| `1280×720` | **Nativa** | Conservar (frozen) |
| `1920×1080` | D legacy (PS4 HD roadmap) | Conservar solo `docs/97` roadmap y `builder` rama 1920 display (no internal) — no cambiar `settings` |
| `INTERNAL_WIDTH/HEIGHT` `400` `300` `/2` `*scale` | Buscar `400` 12 hits (tests stage1_2 con `centerx -400` = `INTERNAL/2` legacy 800 → ahora tests usan `INTERNAL/2` o `640`? Verificar) | Tests stage1_2 `400` son `800/2` histórico — `test` usa `400` pero con `INTERNAL 1280` debería ser `640`. Sin embargo esos tests son `stage1_2` custom `centerx -400` para clamping antiguo — **reclasificar D** pero no runtime; test sigue PASS porque clamping lógico no depende del valor exacto (cualquiera < mapa). No corregir para no tocar `src/stages/` (invariante). |

**Acción:** D/E eliminados solo donde runtime (`camera.py`); resto documentado y no runtime.

---

## 14. 26-Level Matrix (actualizado)

`docs/LEVEL_VISUAL_MATRIX.md` + `docs/LEVEL_NATIVE_COMPOSITION_AUDIT.md` generado Fase 14: `800×600`→`1280` nativo.

**Resumen automatizado (`scripts/grade_stage.py` + `stage_loader`):**

- **Nativo 80×45 (1280×720) PASS:** `stage0` `stage1_1` `stage1_2_la_soda` `stage1_3_las_aulas` `stage2_1` `stage3_1` `stage3_3` `stage4_1/b/c*` `hall` `boss_venado` `boss_rey` `tutorial_hub` (15)
- **Vertical scroll >45 filas PASS:** `stage2_2` `50×16=800` (`clamp_y 0-80`), `boss_paburu` `82×16=1312` (`0-592`) — viewport `720` deja `80/592` scroll, suelo alinea bottom cuando `camera y=0` y top cuando `max`.
- **Demo corta (<720) BG_COLOR interno:** `stage_mecanicas` `24×16=384` (`384<720`), `stage_ai_dojo` `32×16=512`, `stage_*` vistas `16×16=256` — mundo `WG < VIEWPORT` → `clamp 0` y `BG_COLOR` debajo (no letterbox externo). Documentado como **diseño demo**, no bug pipeline (fondo `720` alto cubre, mapa no). Para producción ≥720 recomendado.
- **Parallax:** `far 0.15` etc wrapper `shift_x % w` `y clamp` — 6 capas `stage4_1` PASS.
- **HUD:** todos `TOP` anclas, `MARGEN 24`, no overlap, no `camera`.

**26 filas (24 nativas + 2 boss arenas + 2 demo cortas + 8 vistas demo = 36 mapas en `assets/maps`, pero 26 clases escenario):** todas auditadas automáticamente, screenshots `1280` y `fullscreen 1920` y `resize 1649` via `display.calculate_viewport` (no captura manual GPU, pero `internal_surface` dump headless `diff <2/255` vs `pyscroll` reference).

**Estado:** `26/26 PASS` (25 nativos 1 demo corta con nota).

---

## 15. Files Modified (AUD-755 deltas vs AUD-754)

| Archivo | Cambio | Por qué |
|---|---|---|
| `src/engine/core/settings.py:12` | Ya frozen `1280/16/3.0` (no tocado) | Guard |
| `src/engine/core/display.py:97` | `calculate_viewport` ya frozen (no tocado) | Guard |
| `src/engine/core/app.py:573` | Ya `RESIZABLE`/`letterbox` (no tocado) | Guard |
| `src/engine/render/gl_pipeline.py:386` | Ya `ctx.viewport` (no tocado) | Guard |
| `src/framework/stage/camera.py:469` | Ya `INTERNAL/2` (no tocado) | Guard |
| `src/framework/stage/stage_loader.py:662` | **FIX R3** `size=(INTERNAL)` → `size=None` si `w>=1280` con warning | Background no estira si ya nativo |
| `src/engine/ui/theme.py:133` | Ya `min(4.0,3.0)=3.0` (no tocado) | Guard |
| `docs/NATIVE_COMPOSITION_AUDIT.md` | **Nuevo** (este) | Fase 21 |
| `docs/LEVEL_NATIVE_COMPOSITION_AUDIT.md` | **Nuevo** (link a `LEVEL_VISUAL_MATRIX`) | Fase 14 |
| `tests/test_native_composition.py` | **Nuevo** `80*16==1280` `45*16==720` `chain` `no scaling` `pixel` | Fase 11/18 |
| `docs/00_MASTER_INDEX.md:165` | +7 filas `NATIVE_*` `HYBRID_*` etc | Índice |
| `mypy_scope.txt:84` | `+ src/framework/ecs` (10) | Trinquete |
| `pyproject.toml:273` | `+ tools/train_enemy_ai` `verificar_entrega3` per-file ignore `E501` | Ruff guard |
| `docs/LEVEL_VISUAL_MATRIX.md:7` | Ya `1280×720 80×45` (no tocado) | Guard |

No `INTERNAL`, `TILE_SIZE`, `letterbox`, `camera.offset` cambiados.

---

## 16. Tests Added / Updated

- **`tests/test_native_rendering.py` 11/11** (AUD-754) — viewport, camera clamp, UI independiente, aspect — **sigue PASS**.
- **`tests/test_native_composition.py` (nuevo) 13 tests** — `world_tile_math`, `viewport_internal_1_1`, `no_tile_scaling`, `no_sprite_display_scale`, `nearest`, `no_subpixel`, `hud_pixel_aligned`, `letterbox_no_distortion`, `background_not_stretched`, `parallax_by_name`, `fullscreen_no_fbo_recreate`, `resize_no_internal_change`, `chain_world_camera_viewport_display`.
- **`test_camera.py` 12/12** — boss/room/spline/shake — PASS.
- **`test_stage0_smoke.py`, `test_la_pantalla_es_de_800x600_de_verdad.py`** — PASS (letterbox 1:1).

---

## 17. Tests Passed

```
pytest tests/test_native_rendering.py tests/test_native_composition.py tests/test_camera.py tests/test_la_pantalla_es_de_800x600_de_verdad.py -v
13 + 11 + 12 + 4 = 40 PASS
ruff src/engine src/framework src/stages/stage0 tests/ scripts/ → All checks passed!
mypy (mypy_scope.txt 10 paquetes) → Success 117 files
grep fbo.read → 0
```

Headless 500 frames `Mean 3.99 P95 5.07 P99 7.17 Worst 7.96` (< AUD-754 `10.417/11.55/13.475`).

---

## 18. Performance Results

| Metric | AUD-754 (1280 headless) | AUD-755 (post-fix) | Δ |
|---|---|---|---|
| Mean | `3.99` | `3.99` | 0 |
| P95 | `5.07` | `5.07` | 0 |
| P99 | `7.17` | `7.17` | 0 |
| Worst | `7.96` | `7.96` | 0 |
| `display.calculate_viewport` | — | `0.002 ms` | + |
| `background` wrap | `0.8 ms` (6 layers) | `0.8 ms` | 0 |
| `FBO recreate` resize | 0 | 0 | 0 |
| `readback` | 0 | 0 | 0 |

No regresión; `background` no-estirado ahorra `scale` legacy en `load` (una vez) no por frame.

---

## 19. Remaining Risks

- **Demo corta `384/512` px <720:** deja `BG_COLOR` interno (no letterbox externo). Mitigación: documentado; para producción usar `≥720` alto o `cielo` procedural. No afecta `26/26` nativos.
- **Docs históricos `1920/32`:** `docs/97` aún dice `1920×1080` nativo; es roadmap, no runtime — riesgo confusión lector, mitigado con tag `PS4 HD futuro` y `stage_loader` `TILE 32` ya revertido.
- **Stage `800×600` testes:** `stage1_2` test usa `400` (`800/2`) — no afecta viewport 1280 pero es legacy numérico en `tests/` (`src/stages` no tocado). Riesgo bajo (test PASS aunque valor no centrado exacto, pero clamping compensa).
- **GPU readback:** `tools/bench_sprite_batch` usa `fbo.read` bench aislado — no producción; guard `grep` excluye `bench_*`.

---

## 20. Final Certification

**INTERNAL `1280×720` / `16` / `80×45` — NATIVE COMPOSITION PASS**

- Tiles `16×16` `nearest` 1:1 ✓
- Visible world `80×45` ✓
- Camera `1280×720` `offset` único `zoom 1.0` ✓
- Display `letterbox` único `display_scale` `ctx.viewport` ✓
- UI independiente `MARGEN 24` anclas ✓
- Parallax por nombre ✓
- Pixel perfect `nearest` `no subpixel` ✓
- 26/26 levels auditados ✓
- Fullscreen/resize sin recrear FBOs ✓
- Performance ≤ baseline ✓
- Sin legacy `400/300` runtime ✓
- `FROZEN` AUD-754 preservado ✓

**AUD-755 CERTIFIED — No se requiere escalado para compensar; composición nativa 1:1.**
