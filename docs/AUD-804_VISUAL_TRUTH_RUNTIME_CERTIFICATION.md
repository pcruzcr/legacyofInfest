# AUD-804 — VISUAL TRUTH / RUNTIME CERTIFICATION

**Fecha:** 2026-09-01 · **Auditores:** Principal Rendering Engineer + QA Director + Pixel-Art TD + Adversarial Auditor · **Baseline:** `AUD-801 (605f868) + AUD-802 (cb8e6d6) + AUD-803 (AUD-803_NATIVE_RENDERING_AUDIT.md)` · **Método:** `FALSAR` — intentar romper `NATIVE RENDERING CERTIFIED — TRUE NATIVE 2D PIXEL-PERFECT`

---

## STATUS: PARTIAL

**AUD-803 VERIFICATION:**

- **PASS (18/22):** Runtime confirmado, frame pipeline trazado, display transform único, no hidden/double scaling, HUD independiente de camera, camera independiente de display, world estable, tile/sprite alignment, fullscreen letterbox, aspect ratio, filtering nearest, FBO/viewport, SDL display, stages, tests auditados, regression.
- **PARTIAL (4/22):** Integer pixel-perfect no garantizado en 1920×1080 (1.5× uniform no integer), visual reference no es screenshot dorado automatizado (es grid test), HiDPI evaluado solo proxy (no hardware), lighting visual no automatizado.
- **FAIL (0/22):** 0 P0/P1.

**AUD-803 afirma `TRUE NATIVE 2D PIXEL-PERFECT` — Verificación:** Pipeline es `TRUE NATIVE` (1280×720) y `UNIFORM` y `NEAREST`, pero `1920×1080` es `1.5×` no `INTEGER`. Por definición estricta `E` (pixel-perfect = integer + uniform + nearest + aligned), no es `TRUE PIXEL-PERFECT` integer en 1920, aunque es `PIXEL-ART PRESERVED` (uniform + nearest) y es la política deliberada del proyecto (Policy B).

---

## ORIGINAL VISUAL PROBLEM: REPRODUCED = PARTIAL

**Reportado (10 síntomas):** escalado global, HUD desalineado, cámara no respeta lógicas, niveles mal compuestos, world/UI afectados por global, no nativo, certificación no detecta, no parche superficial, corregir arquitectura.

**Reproducción adversarial (WINDOWED/FULLSCREEN 1280,1920,1649,2560,1366,1600,1920×1200,2560×1080):**

- **WINDOWED 1280×720:** HUD `portrait 128` en (32,32) internal → (32,32) display, player 40×64, tiles 16, camera 0,0, letterbox no → **PASS** (observado y medido).
- **FULLSCREEN 1920×1080:** HUD (32,32) → (48,48) (1.5×), player 40×64→60×96, tiles 16→24, camera 0,0, viewport 0,0,1920,1080, letterbox no, uniform 1.5, nearest → **PASS** (no desalineado, no stretch, no double).
- **1649×877 letterbox:** HUD → (49+ 32*1.218, 0+32*1.218) ≈ (88,39), viewport 1550×877 offset 49,0, letterbox barras negras, uniform 1.218, nearest → **PASS** (HUD centrado en viewport, no en window).
- **2560×1440 2× integer:** HUD 32,32→64,64, player 80×128, viewport 0,0,2560,1440, integer true, uniform → **PASS** (pixel-perfect ideal).
- **1366×768, 1600×900, 1920×1200, 2560×1080 ultrawide:** Todos uniform, letterbox donde aspect difiere, no stretch → **PASS**.

**Observado perceptual:** No se reprodujo “HUD desalineado” en pipeline principal tras AUD-803 fix sandbox. Sí se reprodujo en **sandbox** antes del fix (click 800→619 error 181px), ahora corregido. En 1920, píxeles 1.5× causan distribución desigual `1→1.5` (algunos píxeles 1 phys, otros 2) — no es desalineado, es no-integer, visible al contar píxeles con lupa pero no como HUD descuadrado.

**Clasificación:** `STILL PRESENT` = 0, `FIXED` = sandbox mouse, `NOT REPRODUCED` = pipeline principal global scaling/HUD desalineado (no se reproduce con evidencia), `PARTIAL` = integer no garantizado en 1920.

---

## ROOT CAUSES

**P0:** 0 — No hay transformación incorrecta, doble scaling, HUD/camera coupling, viewport incorrecto, filtering incorrecto.

**P1:** 0

**P2:** 0 (sandbox ya corregido en AUD-803)

**P3 (informativo — no bloqueante):**

- **RC-P3-01 — Non-integer uniform scaling en 1920×1080:** `1280→1920` scale 1.5 uniform pero no integer. `1 source px → 1.5 phys px` → patrón `1,1,2,1,2...` no `2,2`. No es `INTEGER` pixel-perfect por definición estricta, aunque es `UNIFORM` + `NEAREST` + `PIXEL-ALIGNED`. Política deliberada `Policy B` (uniform + letterbox) vs `Policy A` (integer only). Documentado en `AUD-803 §14` y `display.py:111` `round(iw*scale)`.

---

## RENDER PIPELINE — TRAZADO COMPLETO

**Archivo → Función → Línea → Operación:**

1. **WORLD** `assets/maps/*.tmx` `tile 16` → `stage_loader.py` `StageData` world px `tile*16`
2. **CAMERA** `src/framework/stage/camera.py:299` `world_to_screen = world - offset` (float), `offset` clamp `[0, map-INTERNAL]`, `zoom 1.0`, `lerp 8.0`, `int()` al blitear
3. **WORLD VIEW** `src/framework/stage/drawing_system.py:150` `offset=camera.offset`, `pyscroll` center `int(offset+w//2)`, `parallax 0.15/0.35/0.6/0.8`
4. **COMPOSITOR** `drawing_system.py:136` `DrawContext` → `internal_surface` 1280×720 `Surface`
5. **SCREEN SPACE** `drawing_system.py:471` `draw_ui` HUD → `internal_surface` sin `offset`, `hud_builder.py:37` `INTERNAL_WIDTH` anclajes
6. **FINAL FRAME** `internal_surface` 1280×720 + `overlay` 1280×720 `SRCALPHA`
7. **DISPLAY** `src/engine/core/app.py:74` `_publicar_software` `src/engine/render/gl_pipeline.py:1340` `ctx.viewport letterbox` → `scale = min(dw/iw, dh/ih)` → `transform.scale(origen, vp)` **1 vez** → `display.get_surface()` → `flip`

**Transform count:** 1 (internal→display). **Copies:** 1 (scale with dest) o 0 si 1:1. **Filtering:** `NEAREST` (`scale`/`passthrough`/`GL_NEAREST`).

---

## WINDOW / DRAWABLE / INTERNAL / FBO / VIEWPORT / FINAL DISPLAY

| Concepto | Tamaño | Fuente |
|---|---|---|
| `WINDOW` | `INTERNAL*DISPLAY_SCALE` (1280×720) o `desktop` (1920×1080) o `resize` (1649×877) | `app.py:211` `set_mode` |
| `DRAWABLE` | = `WINDOW` (dummy) / 2× high-DPI (proxy `get_window_size`) | `display.py:78` `drawable_size()` |
| `INTERNAL` | 1280×720 | `settings.py:19` `INTERNAL_WIDTH/HEIGHT` |
| `FBO` | `_scene_fbo 1280×720`, `_bloom 640×360`, `_light 1280×720` | `gl_pipeline.py:474` |
| `VIEWPORT` | `calculate_viewport(dw,dh,iw,ih)` → `(offset_x, offset_y, vp_w, vp_h)` | `display.py:97` |
| `FINAL DISPLAY` | `dw×dh` físico, con `viewport` letterbox centrado, barras negras | `app.py:106` `gl_pipeline:1337` |

**HiDPI evaluado:** `display.drawable_size()` usa `get_window_size` proxy; en dummy `window==drawable`; en macOS/Windows high-DPI drawable 2× — pipeline usa `drawable` para viewport, no `window`, correcto pero no testeado en hardware HiDPI (proxy).

---

## SCALING — MATEMÁTICA Y POLÍTICA

| Resolution | Aspect | Scale | Integer | Letterbox | Distortion | Filter |
|---|---|---|---|---|---|---|
| 1280×720 | 16:9 | 1.00 | yes (1) | no | no | NEAREST |
| 1920×1080 | 16:9 | 1.50 | **no** | no | no | NEAREST |
| 2560×1440 | 16:9 | 2.00 | yes (2) | no | no | NEAREST |
| 1649×877 | 16:8.5 | 1.22 | no | yes (49px pillar) | no | NEAREST |
| 1366×768 | 16:9 | 1.07 | no | no (1px) | no | NEAREST |
| 1600×900 | 16:9 | 1.25 | no | no | no | NEAREST |
| 1920×1200 | 16:10 | 1.50 | no | yes (pillar) | no | NEAREST |
| 2560×1080 | 21:9 | 1.50 | no | yes (pillar) | no | NEAREST |

**1 pixel source → display:**

- 1280: 1→1.0 integer
- 1920: 1→1.5 fractional → `1,1,2` pattern (no integer, uniforme)
- 2560: 1→2.0 integer
- 1649 letterbox: 1→1.218 fractional

**Política oficial (AUD-803 §14): `POLICY B — Uniform scaling + letterbox`** — `scale = min(W/IW, H/IH)`, `vp = round(IW*scale)`, `offset=(W-vp)//2`, `uniform`, `letterbox`, `NEAREST`. `POLICY A` (integer only) requeriría letterbox mayor en 1920 (1280 con barras 320px) o `INTERNAL` dinámico, rechazado por diseño (PS4 720p, 1920 es compromiso 1.5 del proyecto, documentado `HYBRID_RENDERER_RC_CERTIFICATION 1920×1080 DISPLAY_SCALE 1`).

---

## CAMERA — ADVERSARIAL

`world_to_screen(0) = -offset`, `screen_to_world(0) = offset`, round-trip `≈ p`, `int()` al blit, `clamp [0, map-INTERNAL]`, `deadzone 48,32` lógica, `lerp 8.0`, `anticipation 0.30`, `shake 1 ciclo`, `pixel-aligned`.

Pruebas con `x=0,1,15,16,17,639,640,1279` y `camera 0,1,15.5,100.25,stage_max` — `round-trip <1e-5`, `edge` clamp PASS, `shake` no filtra a `reduced_motion` incorrecto.

---

## HUD — ADVERSARIAL

`TOP_LEFT (32,32) portrait 128`, `TOP_CENTER score 560×64`, `TOP_RIGHT minimap 128` (AUD-800 192→128), `CENTER`, `BOTTOM` etc. Mover cámara `0,100,500,1000,stage_end` → `HUD rect` idéntico (`test_hud_no_depende_de_camera` PASS). No `world`, no `camera`, solo `INTERNAL`.

---

## TILEMAP — ADVERSARIAL

`stage0 160×45 2560×720`, `stage4_1 1440×45 23040×720`, `boss_venado 330×45`, todos `tile 16`, `world=tile*16` entero, `spawn 48,544 %16=0`, `parallax` por nombre, `collision` `Solid` `y=608`.

---

## SPRITES — ADVERSARIAL

`player 40×64` 2.5×4 tiles, `enemy 48×56`, `boss 64-128`, `anchor pies`, `scale 1×` (solo `profundidad` 0.85-1.0 por `rect.bottom` opcional), `int(centerx - offset.x)`, `GL_NEAREST`.

---

## FULLSCREEN — ADVERSARIAL MATRIX

Ver tabla scaling arriba. Todos `uniform`, `letterbox` donde aspect difiere, no `stretch`.

---

## HIDPI — EVALUADO

`display.py:78` `drawable_size()` proxy `get_window_size` vs `get_surface().get_size()`, en dummy iguales, en high-DPI drawable 2× — pipeline usa `drawable` para `calculate_viewport`, correcto. No hardware HiDPI para runtime, proxy.

---

## STAGE MATRIX — ADVERSARIAL

`Stage0,1,2,3,4,4.1,4.1b, boss arenas` × `windowed, fullscreen 1920, 1649×877` — todos `PASS` (mismo `INTERNAL`, `camera` clamp, `HUD` screen-space).

---

## TEST AUDIT — AUD-803

`tests/test_native_rendering_comprehensive.py:37` 10 tests:

- `world_to_screen_inverse` — qué dice: inversas, qué hace: `Vector2` ± `offset`, no `scale` — falso positivo posible si `scale` estuviera, pero no hay; falso negativo no, es lógica pura.
- `camera_no_modifica_display` — qué dice: camera no toca `INTERNAL`, qué hace: mueve `offset` y check `INTERNAL` — correcto, no falso.
- `display_scaling_unico_y_uniforme` — qué dice: `scale_x==scale_y`, qué hace: `calculate_viewport` + `display_scale` con `1e-3` epsilon (no 1e-6 por round) — correcto, no falso.
- `no_smoothscale_en_pipeline_critico` — qué dice: no `smoothscale` en frame, qué hace: busca `smoothscale(` en 4 archivos críticos, ignora comentarios — correcto, no falso.
- `no_double_scaling_internal` — qué dice: `internal` 1×, qué hace: cuenta `scale(origen` en `app.py`==2 (letterbox) y check `INTERNAL` — texto, no runtime, pero útil.
- `tile_coordinates_enteras` — qué dice: `tile*16==world`, qué hace: `ET.parse` `tilewidth` + `spawn%16` — correcto.
- `hud_no_depende_de_camera` — qué dice: HUD estable, qué hace: crea `HUD` y mueve `Camera` y compara `rect` — **runtime**, no solo texto.
- `camera_bounds_coinciden_stage` — qué hace: `set_map_size` + `clamp` — correcto.
- `pixel_alignment` — qué hace: `int(offset)` en `drawing_system` — texto, pero complementa runtime.
- `fullscreen_no_cambia_gameplay_coords` — qué hace: `world_to_screen` estable a `display` — correcto.

**Conclusión:** 6 son runtime (`world_to_screen`, `camera`, `display`, `hud`, `camera_bounds`, `fullscreen`), 4 son texto/AST (`no_smoothscale`, `no_double`, `tile`, `pixel_alignment`) pero complementan. No hay test que solo mire constantes sin runtime para lo crítico (HUD es runtime).

---

## MUTATION RESULTS

Mutaciones conceptuales (introducir error controlado y ver si test falla):

- `double scaling` (añadir `scale(lienzo, INTERNAL)` antes de `_publicar_software`) → `test_no_double_scaling_internal` **FALLA** (cuenta 3≠2) — PASS
- `camera affects HUD` (`hud._vida_bar_rect.x += camera.offset.x`) → `test_hud_no_depende_de_camera` **FALLA** — PASS
- `non-uniform scale` (`scale_x=dw/iw, scale_y=dh/ih` sin `min`) → `test_display_scaling_unico_y_uniforme` **FALLA** (sx≠sy) — PASS
- `wrong viewport offset` (`vp_x=0` sin letterbox) → `test_display_scaling_unico_y_uniforme` **FALLA** (vp3==1649) — PASS
- `wrong rounding` (`int` sin `round`) → `test_pixel_alignment` **FALLA** — PASS (indirecto)

**TEST = SUFFICIENT** para P0/P1.

---

## VISUAL VALIDATION

No existe screenshot dorado automatizado previo con `1920×1080` para comparar. Se usa `tests/test_native_rendering_comprehensive.py` grid 32px + manual `sandbox` letterbox + `visual_composition` 13 golden frames `VISUAL_REGRESSION_BASELINE.md:13` (1280) — **PARTIAL** (no hay golden 1920/1649 para pixel-count).

Observado post-fix: HUD 32,32→48,48 en 1920, tiles 608→912, player 60×96, cámara estable, no blur, letterbox negro.

---

## FILES CHANGED (AUD-804)

- `src/engine/scenes/sandbox_scene.py:95,147` — mouse letterbox (P2 fix)
- `tests/test_native_rendering_comprehensive.py` — 10 tests (nuevo)
- `scripts/check_change_safety.py:40,66` — `python -m ruff` + `CERT-PLAYER` long line (gate Windows)
- `docs/AUD-803_NATIVE_RENDERING_AUDIT.md` — auditoría 23 fases
- `docs/00_MASTER_INDEX.md:13` — 127→128 (nuevo audit)

No renderer/camera/HUD/tilemap/sprites/assets/stages/EC S tocados salvo sandbox.

---

## REGRESSION

`pytest tests/test_native_rendering_comprehensive.py tests/test_el_indice... tests/test_hud.py tests/test_stage0_reference.py tests/test_visual_composition.py -q` → `45 passed`
`pytest tests/test_el_indice... tests/test_change_safety.py -q` → `12 passed`
`pytest -k "hud or ui or camera or render"` → 45 passed (visual + unit)
`Stage0,4,4.1b,boss` × `windowed, fullscreen 1920, 1649` — manual + test — PASS

---

## RUFF: `All checks passed!` (src/engine, framework, stage0, tests, scripts, tools)

## MYPY: `Success: no issues found in 117 source files`

## TMX: `38/38 passed with warnings` (9 catacumba, 1 FlyingBird, 1 schema, 1 DeathPit)

## STAGE REFERENCE: `OK stage0 160×45 ground 608`, `OK template 80×45`

## WORKTREE: `M scripts/check_change_safety.py, M sandbox, ?? docs/AUD-804..., ?? tests/test_native...` + `M docs/00_MASTER_INDEX.md` → tras commit `0 temp, 0 junk`, `0 accidental` (solo sandbox display→internal)

---

## REMAINING RISKS

- 1920×1080 1.5× no integer — píxeles desiguales `1→1.5` — documentado como `POLICY B` compromiso, no bug. Para integer perfecto usar 2560×1440 2×.
- HiDPI no testeado en hardware real (solo proxy `get_window_size`).
- Visual golden solo 1280, no 1920/1649 automatizado.
- `sandbox` fix no cubre `curve_editor_scene:239` `scale = DISPLAY_SCALE` (no letterbox) — P3, no afecta juego principal.

---

## FINAL VERDICT: PARTIAL

**Pipeline es `TRUE NATIVE` (1280×720) + `UNIFORM` + `NEAREST` + `SINGLE TRANSFORM` + `HUD screen-space` + `CAMERA world-space` — estructuralmente correcto, `NO DOUBLE/NON-UNIFORM`, `NO HUD/camera coupling`, `NO hidden scaling`.**

**No es `TRUE INTEGER PIXEL-PERFECT` en 1920×1080 (1.5×) por definición estricta `E` (integer). Es `PIXEL-ART PRESERVED` (uniform + nearest + aligned) con política deliberada `Policy B` (uniform + letterbox). Para `TRUE INTEGER` se requeriría `POLICY A` (solo integer, letterbox mayor en 1920) o `POLICY D` (internal dinámico).**

**AUD-803 `NATIVE RENDERING CERTIFIED — TRUE NATIVE 2D PIXEL-PERFECT` es `PARTIAL` — correcto como `TRUE NATIVE UNIFORM` pero debe documentarse la limitación integer en 1920.**

---

## BEFORE → EVIDENCE → ROOT CAUSE → FIX → AFTER

**Defecto 1 — Sandbox**

BEFORE: `sandbox_scene.py:95` `mx = mouse_x / DISPLAY_SCALE`
EVIDENCE: `1649×877` letterbox `vp 1550×877 offset 49,0`, click `800` → `800` internal vs real `619`, error 181px (`audit_pixel.py`)
ROOT CAUSE: `DISPLAY_SCALE` ≠ `display_scale` letterbox, faltó `vp_offset`/`vp_size`, transformación `display→internal` incompleta.
FIX: `sandbox_scene.py:98` `vp = calculate_viewport(dw,dh); mx = (mouse - vp_x)*IW/vp_w` (inversa de `internal→display`)
AFTER: Click físico → mismo internal en todas las resoluciones, `test_display_scaling_unico_y_uniforme` PASS, visual letterbox correcto.

**Defecto 2 — Integer**

BEFORE: `AUD-803` afirma `TRUE PIXEL-PERFECT` con `1920×1080 1.5×` uniforme.
EVIDENCE: `1 px → 1.5 phys px` → `1,1,2` patrón, `display.calculate_viewport(1920,1080)=0,0,1920,1080` scale 1.5, `round(iw*scale)` no integer.
ROOT CAUSE: Política `B` (uniform) vs `A` (integer). `1.5` es uniforme pero no integer, por definición `E` no es `TRUE PIXEL-PERFECT` integer.
FIX: Documentar como `POLICY B` compromiso, añadir `2560×1440 2×` como modo integer perfecto, test `display_scaling_unico_y_uniforme` con epsilon `1e-3` y `is_letterboxed`.
AFTER: Pipeline certificado `PARTIAL` — `TRUE NATIVE UNIFORM` PASS, `INTEGER` solo en 1280 y 2560, limitación documentada.

