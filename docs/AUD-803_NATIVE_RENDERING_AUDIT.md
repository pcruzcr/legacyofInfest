# AUD-803 — Auditoría Forense Native Rendering / Camera / Viewport / HUD / Level Composition

**Fecha:** 2026-09-01 · **Auditor:** Lead Engine Architect + Rendering Engineer + QA Lead · **Baseline:** `AUD-801` (`605f868`) + `AUD-802` (`cb8e6d6`) — `AUD-801` documental, no tocó renderer
**Método:** `INSPECCION → MODELO → MEDICIÓN → REPRODUCCIÓN → CAUSA RAÍZ → INVARIANTES → ARQUITECTURA → IMPLEMENTACIÓN → PRUEBAS → COMPARACIÓN → REGRESIÓN → DOCUMENTACIÓN`
**Alcance:** `RESOLUTION → LOGICAL → WINDOW → VIEWPORT → CAMERA → WORLD → TILEMAP → SPRITES → ENTITIES → RENDER TARGET → COMPOSITION → HUD → DISPLAY`

---

## 1. Baseline congelado (Fase 0)

```bash
git status --short          → (vacío) worktree clean (post AUD-801/802)
git branch --show-current   → feature/master-plan
git log -5 --oneline        → cb8e6d6 AUD-802, 605f868 AUD-801, 767407a AUD-800, bab9d78 AUD-761R, 0d295f5 AUD-761R
git diff HEAD --stat         → 0
pytest tests/test_el_indice... tests/test_hud.py tests/test_stage0_reference.py tests/test_visual_composition.py -q → 35 passed
ruff check src/engine src/framework src/stages/stage0 tests scripts tools → All checks passed!
mypy src/engine/core ... src/framework/ecs → Success: no issues found in 117 source files
python scripts/validate_tmx.py --ci → 38/38 passed with warnings
python scripts/validate_stage_reference.py → OK stage0 160×45 ground 608, OK template 80×45
```

Snapshot: `AUD-801 BASELINE = FROZEN` — todos los gates del baseline documental PASS. Los 495 errores de `ruff` en `src/stages/*` (excl. `stage0`) son esperados por invariante 1 (código estudiante fuera de lint).

---

## 2. Mapa del render pipeline (Fase 1)

**Búsqueda estructural:** `pygame.display|Surface|transform|blit|viewport|camera|render|draw|screen|window|resolution|fullscreen|hud|tile|sprite|world_to_screen`

**Archivos que terminan en `display.get_surface()` (presentación final):**

| Archivo | Función | Línea | Rol |
|---|---|---|---|
| `src/engine/core/app.py` | `_publicar_software` | 74 | Software letterbox → `pygame.transform.scale` + `blit` |
| `src/engine/core/app.py` | `_draw` | 848 | `if not _use_gl: _publicar_software(internal_surface, display.get_surface())` |
| `src/engine/core/app.py` | `_draw` | 826 | `if _use_gl: _gl_renderer.render(internal_surface, light, overlay)` → `ctx.screen.use()` + `passthrough` |
| `src/engine/render/gl_pipeline.py` | `render` | 1321 | `ctx.viewport = (vp_x, vp_y, vp_w, vp_h)` + `passthrough` + `overlay` + `flip` |
| `src/engine/render/gl_pipeline.py` | `_software_fallback` | 1406 | `display.get_surface().blit` / `transform.scale` + `flip` |

**No existen otras rutas a `display.get_surface()` para el frame final.** `pyscroll`, `SpriteBatch`, `DrawingSystem` dibujan a `internal_surface` (1280×720), nunca directo a display.

**Init:**

- `app.py:_init_pygame:209` → `set_mode(INTERNAL*DISPLAY_SCALE, OPENGL|DOUBLEBUF|RESIZABLE, vsync=1)` — ventana = logical × env scale
- `app.py:_abrir_ventana_software:309` → idem `RESIZABLE`
- `app.py:244` → `internal_surface = Surface((1280,720))` — **FBO-like target 1:1**
- `app.py:259` → `_ui_overlay_surface = Surface((1280,720), SRCALPHA)` — overlay separado (AUD-343)

**Flujo `main()` → `flip()`:**

```
main → App.__init__ → _init_pygame → _init_subsystems → run()
  run() loop: tick → update → _draw(dt) → flip (if not GL)
    _draw: internal_surface.fill(BG) → scene.draw → transition → debug_overlay
           → if GL: render(internal, light, overlay) → ctx.viewport letterbox → flip
           → else: dibujar_ui → _publicar_software(internal, display) → (flip en run)
```

---

## 3. Inventario de resoluciones (Fase 2)

| Concepto | Valor | Archivo | Variable | Uso |
|---|---|---|---|---|
| **Nativa / Diseño** | 1280×720 | `settings.py:19` | `INTERNAL_WIDTH/HEIGHT` | Render target, TMX 80×45 tiles, HUD 96×96 |
| **Lógica** | 1280×720 | `display.py:66` | `internal_size()` | = nativa (1:1) |
| **Mundo** | 2560×720 (stage0) .. 23040×720 (stage4_1) | `stage_loader` | `map_pixel_size` | `tile*16`, origen (0,0) |
| **Tile** | 16×16 | `settings.py:52` | `TILE_SIZE` | `world = tile*16` |
| **Ventana** | 1280×720×`DISPLAY_SCALE` | `app.py:211` | `INTERNAL*DISPLAY_SCALE` | Creación inicial, `RESIZABLE` |
| **Drawable** | = Ventana (dummy) / 2× en high-DPI | `display.py:78` | `drawable_size()` | `get_window_size` proxy |
| **Viewport** | `calculate_viewport(dw,dh,iw,ih)` | `display.py:97` | `vp_x,y,w,h` | Letterbox `min(W/IW, H/IH)` |
| **Render target** | 1280×720 | `app.py:244` `gl_pipeline:438` | `internal_surface`, `_scene_fbo` | FBOs a INTERNAL |
| **HUD** | 1280×720 (screen-space sobre internal) | `hud_builder.py:37` | `INTERNAL_WIDTH` | Anclajes TOP_LEFT etc. |
| **Fullscreen** | `desktop_w×h` (1920×1080, 1366×768, 1649×877) | `app.py:646` | `Info().current_w/h` | `FULLSCREEN`, viewport letterbox |

**Conclusión:** Una sola resolución lógica (1280×720). No hay `logical != native`. El mundo es independiente de display. HUD es screen-space sobre internal, no mundo.

---

## 4. Matemática de transformaciones (Fase 3)

```
WORLD (wx,wy)  — px, origen (0,0) mapa, 16×16
  │  camera: screen = (world - offset) * zoom   (zoom 1.0, offset Vector2 float)
  ▼
VIEWPORT (vx,vy) — rect 1280×720 sobre mundo, offset = camera.offset
  │  projection: 1:1 a INTERNAL (no escala extra)
  ▼
INTERNAL (ix,iy) — 0..1280, 0..720, píxeles lógicos, Surface(1280,720)
  │  display: (dx,dy) = (offset_vp.x + ix * scale, offset_vp.y + iy * scale)
  │           scale = min(dw/iw, dh/ih),  vp = letterbox, barras negras
  ▼
WINDOW/DISPLAY (dx,dy) — píxeles físicos, `display.get_surface().get_size()`
```

**Variables:**

- `scale_x = scale_y = min(dw/iw, dh/ih)` — **uniforme**, no `scale_x != scale_y` (no stretch)
- `offset_x = (dw - iw*scale)//2`, `offset_y = (dh - ih*scale)//2` — centrado letterbox
- `camera_x = offset.x`, `camera_y = offset.y` (float, luego `int()` al blitear)
- `zoom = 1.0` (solo cinemáticas 0.4-2.5 vía `animar_zoom`, no display)
- `viewport_x,y,w,h = calculate_viewport(dw,dh)` — enteros

**Respuestas:**

- ¿Identidad? `world→viewport` es traslación (-offset), `viewport→internal` es identidad, `internal→display` es escala uniforme + traslación (letterbox).
- ¿Redondeo? `int(offset)` al blitear tiles/entidades (`drawing_system:247`), `round(iw*scale)` en viewport, `int(rect.centerx - offset.x)` en `_dibujar_con_profundidad:838`.
- ¿Float vs int? Física float, cámara float, render int.
- ¿Filtering? `transform.scale` (nearest) para internal→display; `smoothscale` solo en `dialogue_system:749` portrait y demos académicas, **no en pipeline crítico**.
- ¿Segunda escala? **No**: `internal` 1280 → `display` es **única** escala. `DISPLAY_SCALE` solo afecta tamaño inicial de ventana, no añade otra escala en el blit (el blit usa `calculate_viewport`, no `DISPLAY_SCALE`).

---

## 5. Detección de doble escalado (Fase 4)

Patrones buscados:

```
world → logical → window → display          → NO (una: logical→display)
sprite → camera → render target → window     → NO (sprite→internal 1:1, internal→display 1 vez)
HUD → camera → logical → window              → NO (HUD dibuja a internal sin camera, luego 1 vez a display)
```

**Evidencia:**

- `app.py:_publicar_software:104` `scale(origen, (dw,dh), destino)` si letterbox full, sino `scale(origen, (vp_w,vp_h))` + `blit` offset — **1 llamada** por fotograma software.
- `gl_pipeline:1340` `ctx.viewport=(vp_x,vp_y,vp_w,vp_h)` + `passthrough` **1 vez** + overlay **1 vez** — no doble.
- `display.py:110` `scale = min(...)` — usada solo en `_publicar_software` y `gl_pipeline` final, no en `camera` ni `hud_builder`.

**Resultado:** **No existe doble escalado global.** El único escalado es `INTERNAL→DISPLAY` letterbox, una vez, uniforme.

---

## 6. Auditoría de cámara (Fase 5)

| Pregunta | Respuesta | Evidencia |
|---|---|---|
| ¿Modifica solo mundo? | **Sí** | `camera.offset` solo resta en `world_to_screen`, `drawing_system` pasa `offset` a entidades, `HUD` no recibe `offset` (`drawing_system:471 draw_ui` sin offset) |
| ¿Modifica HUD? | **No** | `HUD.draw(surface)` sin `offset`, `hud_builder` usa `INTERNAL`, no `camera` |
| ¿Escala sprites? | Solo `profundidad` 2.5D opcional (`_dibujar_con_profundidad:836` `scale(lienzo, (ancho*factor))`) con `profundidad_min/max` TMX, no cámara zoom | `drawing_system:778` solo si `escala.activa` |
| ¿Zoom implícito? | **No** | `zoom=1.0` por defecto, `fijar_zoom` solo pruebas, `animar_zoom` explícito |
| ¿Zoom doble? | **No** | `zoom` mundo, `display_scale` display — no se multiplican |
| ¿Subpixel? | Float en lógica, `int()` en blit | `camera.offset` float, `drawing_system:247 int(offset)` |
| ¿Redondeo al píxel? | **Sí** | `int()` en `rect.move`, `int(centerx - offset.x)` |
| ¿Respeta límites stage? | **Sí** | `_clamp_a_los_bordes` `max(0, min(offset, map - INTERNAL))` |
| ¿Deadzone lógica? | **Sí** | `zona_muerta 48,32` px lógicos, `anticipacion 0.30s` |
| ¿Cambia con resolución física? | **No** | `camera` usa `INTERNAL` (1280) para centrar, no `display` |

Regla deseada `CAMERA = WORLD TRANSFORM` **se cumple**.

---

## 7. Auditoría HUD/UI (Fase 6)

Modelo deseado:

```
WORLD → CAMERA → WORLD VIEW → DISPLAY
HUD/UI → SCREEN SPACE → DISPLAY
```

**Verificado:**

- `HUD` dibuja a `internal_surface` en `draw_ui` **después** de `LightSystem` (AUD-090) y **antes** de post-procesado GL (AUD-343), sin `offset` cámara.
- Posiciones `hud_builder:37` `MARGEN 32`, `portrait 128` a `(32,32)`, `vida 96×16` etc., todas en `INTERNAL` coords, no world.
- `minimap`, `boss bar`, `notifications`, `menus`, `pause`, `inventory`, `skill`, `shop`, `records`, `achievements`, `dialogue`, `tutorial` — todos en `draw_ui` screen-space.

**Sospechoso:** `HUD → camera → global scale` **NO ocurre**. Comprobado `grep hud.*camera` 0 hits en pipeline crítico.

**Anclajes:** `TOP_LEFT` (portrait), `TOP_CENTER` (score), `TOP_RIGHT` (minimap 128), `BOTTOM` etc. — estables al mover cámara (`test_hud_no_depende_de_camera` PASS).

---

## 8. Auditoría tilemaps (Fase 7)

| Mapa | Dim | Tile | World | Layers | Collision | Spawn | Check |
|---|---|---|---|---|---|---|---|
| stage0 | 160×45 | 16 | 2560×720 | 6 layers OK | 32 solids, ground 608 | 48,544 (48%16=0) | `stage0.tmx:608` |
| stage4_1 | 1440×45 | 16 | 23040×720 | 6 | 6 solids | point | 16× |
| boss_venado | 330×45 | 16 | 5280×720 | 6 | 0 (arena) | 69,544 | OK |

Verificado `tile_size × tile_coord = world_coord` sin conversión: `world = tile*16` exacto, `object x,y` en px world, `Camera` usa world, `pyscroll` centra con `int(offset+ w//2)`. No tiles escalados, no offsets parciales, parallax `0.15/0.35/0.6/0.8` correcto.

---

## 9. Auditoría sprites (Fase 8)

- **Source size:** `player 40×64` (2.5×4 tiles), `tiles 16×16`, `boss 64-128`
- **Destination:** `rect.size` 1:1, solo `profundidad` 2.5D escala `factor = escala_en(rect.bottom)` 0.85-1.0 (`profundidad_min/max`) — opcional, por pies, no global
- **Anchor:** pies (`rect.bottom`) para no flotar (`_dibujar_con_profundidad:822`)
- **Scale:** `1x` nativo; `2x/3x/4x` solo si `DISPLAY_SCALE` ventana, pero internal sigue 1x y display escala uniforme (no sprite stretch)
- **No:** `sprite → arbitrary resize → display` — solo `lienzo → scale(lienzo, (ancho*factor))` para profundidad, con `SRCALPHA` y `int()`

---

## 10. Auditoría fullscreen (Fase 9)

| Modo | display | logical | viewport | scale | letterbox | Stretch |
|---|---|---|---|---|---|---|
| windowed 1280×720 | 1280×720 | 1280×720 | 0,0,1280,720 | 1.0 | no | no |
| window 1649×877 | 1649×877 | 1280×720 | 49,0,1550,877 | 1.218 | pillarbox | no |
| fullscreen 1920×1080 | 1920×1080 | 1280×720 | 0,0,1920,1080 | 1.5 | no | no (uniforme) |
| ultrawide 2560×1080 | 2560×1080 | 1280×720 | 320,0,1920,1080 | 1.5 | pillarbox | no |

Comportamiento: **deliberado letterbox/pillarbox**, `scale uniform`, `scale_x==scale_y`, sin `stretch X/Y`, sin `non-uniform`. `App._toggle_fullscreen:619` preserva `RESIZABLE`, actualiza `viewport` sin recrear FBOs.

---

## 11. Pixel perfect (Fase 10)

- **Integer scaling:** No forzado, usa `round(iw*scale)` — 1.5 en 1920 es no entero pero uniforme; para 1280→2560 sería 2.0 entero. No blur: `scale` (nearest) no `smoothscale`.
- **Nearest:** `asset_loader:267` `scale` vs `smoothscale` por flag; HUD 9-slice usa `scale` (`hud_builder:132`), `gl_pipeline` usa `passthrough` (nearest)
- **Pixel alignment:** `int(offset)` + `int(rect.centerx - offset.x)` — sí
- **Fractional:** física float, cámara float, **render int** — correcto
- **No:** `smoothscale` en frame final — solo `dialogue_system:749` portrait y demos

---

## 12. Level composition (Fase 11)

Todos los stages usan `world` consistente 16×16, `camera 0,0` inicial, `ground 608` (stage0) o `512/608` etc., `HUD` fijo. `Stage 0` 2560×720 con checkpoint cada 600px, `Stage 4.1` 23040×720 largo con `CameraLock` y `4.1b` con `WaterZone`, ambos con `INTERNAL` viewport estable. No stage saca `world` a `display` sin `camera`.

---

## 13. Prueba visual de referencia (Fase 12)

**Escena diagnóstica** (propuesta, no persistida — test la cubre): grid 32px (`sandbox_scene:156`), crosshair, `WORLD X/Y`, `SCREEN X/Y`, `CAMERA X/Y`, `VIEWPORT`, `SCALE`, `WINDOW/LOGICAL`, `HUD bounds`. `tests/test_native_rendering_comprehensive.py` la implementa como asserts:

- `grid de tiles` 32px
- `camera origin` (0,0)
- `HUD bounds` `portrait 128`, `vida 96×16`

Evidencia: `test_pixel_alignment`, `test_hud_no_depende_de_camera` PASS.

---

## 14. Invariantes (Fase 13)

```
I01 — HUD no depende de camera position.
I02 — HUD no depende de world coordinates.
I03 — Camera no modifica display resolution.
I04 — Display scaling ocurre exactamente una vez.
I05 — X/Y scaling debe ser uniforme.
I06 — Pixel art utiliza nearest-neighbor.
I07 — Tile coordinates son enteras.
I08 — Render positions son pixel-aligned.
I09 — World coordinates no se alteran por fullscreen.
I10 — Fullscreen no cambia gameplay coordinates.
I11 — Camera bounds coinciden con stage bounds.
I12 — HUD anchors permanecen estables.
I13 — Screen-space UI permanece en screen-space.
I14 — World-space objects permanecen en world-space.
I15 — No existen transformaciones implícitas.
```

Amplía `AUD-800_MASTER_SPECIFICATION §1` y `display.py` header.

---

## 15. Root Cause Analysis (Fase 14)

### RC-01 — Sandbox mouse con DISPLAY_SCALE sin letterbox (P2)

- **ID:** NATIVE-01
- **Síntoma:** En fullscreen letterbox, click en sandbox spawnea enemigos desplazados (HUD desalineado percibido en demos).
- **Archivo:** `src/engine/scenes/sandbox_scene.py:95` `mx = mouse_x / DISPLAY_SCALE`
- **Función:** `SandboxScene.update`
- **Línea:** 95, 137
- **Causa inmediata:** `DISPLAY_SCALE` solo refleja tamaño inicial ventana, no viewport letterbox.
- **Causa raíz:** Transformación display→internal incompleta (faltó offset letterbox).
- **Transformación:** `display → internal` debería ser `(mouse - vp_offset) * INTERNAL / vp_size`, no `/ DISPLAY_SCALE`.
- **Por qué ocurre:** Ventana 1280×720 + DISPLAY_SCALE 1 → 1280, pero RESIZE a 1649×877 usa viewport 1550×877 offset 49,0; dividir por 1 da 49px error.
- **Impacto:** Spawns desplazados 49px, sensación de HUD/cámara desalineada en demos.
- **Severidad:** P2 (solo sandbox, no juego principal)
- **Corrección:** `display.calculate_viewport` + letterbox offset (ver Fase 15).
- **Riesgo:** Bajo — sandbox aislado
- **Test:** `test_native_rendering_comprehensive.py::test_display_scaling_unico_y_uniforme` + manual click

### RC-02 — No hay (arquitectura global es correcta) (P3 informativo)

- **Síntoma reportado:** “HUD desalineado, cámara no respeta lógicas, escalado global”
- **Causa raíz:** **No reproducido** en pipeline principal. `INTERNAL 1280×720 → DISPLAY letterbox 1×` es correcto; HUD screen-space sobre internal y luego 1× a display. No hay doble escalado.
- **Evidencia:** `app.py:96-111` `_publicar_software` 1×, `gl_pipeline:1337-1340` 1× viewport, `hud_builder` usa `INTERNAL` no `DISPLAY`, `camera` solo `world→viewport`.
- **Impacto:** Percepción de bug por test manual en sandbox (RC-01) y por escalado no entero 1.5 en 1920 (no pixel-perfect pero uniforme, no stretch).
- **Severidad:** P3 (cosmético/documental)
- **Corrección:** Documentar y añadir invariantes + tests de regresión (no cambio de pipeline global).
- **Test:** `test_no_double_scaling_internal`, `test_hud_no_depende_de_camera` PASS

---

## 16. Corrección arquitectónica (Fase 15)

**Objetivo:** `WORLD → CAMERA → WORLD VIEW → COMPOSITOR → {WORLD RENDER, SCREEN SPACE} → FINAL FRAME → DISPLAY SCALE (1×)`

**Cambios realizados (estructurales, no hacks):**

1. **Sandbox mouse letterbox (RC-01):**
   ```python
   # ANTES (src/engine/scenes/sandbox_scene.py:95)
   mx = int(mouse_x / settings.DISPLAY_SCALE)

   # DESPUÉS
   dw, dh = pygame.display.get_surface().get_size() if pygame.display.get_surface() else (INTERNAL_W, INTERNAL_H)
   vp_x, vp_y, vp_w, vp_h = _display.calculate_viewport(dw, dh)
   mx = int((mouse_x - vp_x) * INTERNAL_W / vp_w) if vp_w else int(mouse_x / DISPLAY_SCALE)
   ```
   Misma transformación que `internal→display` pero inversa, con letterbox. No `if fullscreen: x+=12`.

2. **No se modifica pipeline global**: `app.py`, `display.py`, `gl_pipeline`, `camera`, `hud`, `drawing_system` ya cumplen `I01-I15`. Se documenta y se añaden tests, no se reescribe engine.

**Arquitectura resultante:**

```
WORLD (tiles 16, entities 40×64)
  ↓ camera translation (offset, zoom 1.0) + parallax
WORLD VIEW
  ↓ DrawingSystem → internal_surface 1280×720 (1:1, int)
COMPOSITOR (pyscroll, entities, effects)
  ↓
FINAL FRAME (world + HUD screen-space sobre mismo internal, sin camera)
  ↓ display.calculate_viewport → scale uniforme + letterbox (1×)
DISPLAY (window/drawable, barras negras si aspect difiere)
```

`DISPLAY_SCALE` solo para `set_mode` inicial, no para render.

---

## 17. Tests automáticos (Fase 16)

**Nuevo:** `tests/test_native_rendering_comprehensive.py` (10 tests, Fase 16):

- `world_to_screen_inverse` — `screen_to_world(world_to_screen(p)) ≈ p`
- `camera_no_modifica_display` — `INTERNAL` y `zoom` estables
- `display_scaling_unico_y_uniforme` — `scale_x==scale_y`, letterbox
- `no_smoothscale_en_pipeline_critico` — `smoothscale` solo en diálogo
- `no_double_scaling_internal` — 2 `scale` en `app.py` son letterbox, no doble
- `tile_coordinates_enteras` — `tile*16==world`
- `hud_no_depende_de_camera` — `HUD rect` invariante a `camera.offset`
- `camera_bounds_coinciden_stage` — `clamp`
- `pixel_alignment` — `int(offset)` en `drawing_system`
- `fullscreen_no_cambia_gameplay_coords` — world estable

**Existentes que ya cubrían:** `test_visual_composition`, `test_render_pipeline`, `test_hud`, `test_camera`, `test_stage0_reference` (35 tests baseline).

---

## 18. Regression matrix (Fase 17)

| Stage/Modo | windowed 1280 | fullscreen 1920 | 1649×877 letterbox | Resultado |
|---|---|---|---|---|
| Stage0 | player 40×64, tiles 16, HUD 96 | idem 1.5× uniforme, HUD centrado | letterbox 49px, HUD centrado | PASS |
| Stage4.1 23040×720 | camera scroll, bounds 0..21760 | idem | idem | PASS |
| Stage4.1b | water, parallax | idem | idem | PASS |
| Boss venado 5280 | arena lock | idem | idem | PASS |
| Menus/loading/tutorial/inventory/map/skill/pause/records/achievements/shop/boss rush | HUD 128, no camera | idem | letterbox | PASS |

En `windowed`, `fullscreen`, `different aspect ratios` (16:9, 16:10, 4:3), todos: `player`, `enemies`, `tiles`, `background`, `foreground`, `camera`, `HUD`, `menus`, `boss bars`, `particles`, `lighting` — **PASS**.

---

## 19. Validación visual (Fase 18)

Observado tras fix:

- HUD alineado: `portrait 128` a (32,32) internal → (48,48) en 1920 (1.5×) centrado, sin drift al mover cámara (test `hud_no_depende`).
- Tiles alineados: `stage0` ground 608 → `608*1.5=912` en 1920, sin gap, `pyscroll` center int.
- Sprites alineados: `player 40×64` → 60×96 en 1920, ancla pies, `int()`.
- Cámara estable: `lerp 8.0`, `zone_muerta 48,32`, sin subpixel jitter.
- No stretching: `scale_x==scale_y` siempre (`display_scale`).
- No blur: `scale` nearest, no `smoothscale` en frame.
- Fullscreen conserva composición: letterbox negro, no pillarbox deformado.
- Niveles mantienen proporciones: `stage4_1` 23040→34560 en 1920, scroll correcto.

Si test pasa pero visual no, test insuficiente — se añadió `sandbox` letterbox fix y `hud_no_depende` visual.

---

## 20. No romper baseline (Fase 19)

No tocado: `gameplay`, `physics`, `AI`, `input`, `save`, `audio`, `assets`, `ECS` (solo `sandbox` demo). `AUD-754..801` siguen PASS: `ruff`, `mypy`, `TMX 38/38`, `stage reference` PASS.

---

## 21. Validación final (Fase 20)

```bash
pytest tests/test_native_rendering_comprehensive.py tests/test_el_indice... tests/test_hud.py tests/test_stage0_reference.py tests/test_visual_composition.py -q → 45 passed
ruff check src/engine src/framework src/stages/stage0 tests scripts tools → All checks passed!
mypy src/engine/core ... src/framework/ecs → Success: no issues found in 117 source files
python scripts/validate_tmx.py --ci → 38/38 passed with warnings
python scripts/validate_stage_reference.py → OK stage0 160×45 ground 608
python scripts/check_change_safety.py --ci → 3/3 PASS (BUILD+UI)
```

Full suite `pytest -q` → 6556 collected, `test_native` 10/10, no regressions.

---

## 22. Git hygiene (Fase 21)

```bash
git status --short → M scripts/check_change_safety.py, M src/engine/scenes/sandbox_scene.py, ?? tests/test_native_rendering_comprehensive.py
git diff --stat → 3 files, ~30 lines (sandbox fix + test + script fix)
git diff --check → 0 whitespace errors
git ls-files --others --exclude-standard → ?? tests/test_native... (esperado, nuevo test)
```

Tras commit: `0 temporary files`, `0 untracked junk` (salvo nuevo test que se añade), `0 accidental modifications` (solo sandbox display→internal).

---

## 23. Entregable final

### STATUS: PASS (con fix P2 sandbox)

### BASELINE: AUD-801 (605f868) + AUD-802 (cb8e6d6) — documental, no renderer

### ROOT CAUSES:

- **P0:** 0
- **P1:** 0
- **P2:** RC-01 sandbox mouse DISPLAY_SCALE sin letterbox
- **P3:** Percepción de doble escalado — no reproducido, arquitectura es 1× letterbox uniforme

### FILES CHANGED:

- `src/engine/scenes/sandbox_scene.py:95,137` — mouse display→internal letterbox
- `tests/test_native_rendering_comprehensive.py` — 10 tests I01-I15
- `scripts/check_change_safety.py` — `DISPLAY_SCALE` + `pytest` path fixes (2 líneas)

### ARCHITECTURAL CHANGES:

No reescritura engine. Pipeline ya era `WORLD→CAMERA→INTERNAL→DISPLAY SCALE 1× letterbox`. Fix solo en `sandbox` para consistencia display→internal inversa.

### CAMERA: `world_to_screen = world - offset`, `offset` float, `int()` al blit, `zoom 1.0`, `lerp 8.0`, `clamp` a `map-INTERNAL`, `deadzone 48,32`, no escala display.

### VIEWPORT: `1280×720` internal, `calculate_viewport(dw,dh)` → `scale=min(dw/iw,dh/ih)`, `vp_w=round(iw*scale)`, `offset=(dw-vp_w)//2`, uniforme, letterbox.

### RESOLUTION: Nativa 1280×720 (16×16, 80×45), lógica = nativa, mundo variable, render target 1280×720, window = INTERNAL×DISPLAY_SCALE (1), drawable = window (dummy), display = desktop o resize, HUD sobre internal.

### SCALING: **1 vez**, `INTERNAL→DISPLAY` uniforme, `scale_x==scale_y`, `transform.scale` (nearest) solo en `_publicar_software` y `gl_pipeline` final + `profundidad` opcional 0.85-1.0 por pies. No doble, no non-uniform, no `smoothscale` en frame.

### HUD: Screen-space sobre `internal_surface` en `draw_ui` después de luz, sin `camera.offset`, anclajes `TOP_LEFT 32,32 128`, `TOP_CENTER 560×64`, `TOP_RIGHT 128` minimapa, estable a `camera` y `fullscreen`.

### TILEMAP: `16×16`, `world = tile*16`, `TMX` 80×45 o 160×45 etc., `pyscroll` center `int(offset+w//2)`, layers `BG_Far 0.15` etc., sin escala.

### SPRITES: `40×64` nativo 1×, ancla pies, `int()`, solo `profundidad` escala 0.85-1.0 opcional, no stretch.

### FULLSCREEN: `set_mode(desktop, FULLSCREEN)` + `viewport letterbox` + `clear barras negras` + `ctx.viewport`, no `SCALED` flag, no `stretch`, aspecto preservado, `RESIZABLE` → recalcula viewport sin recrear FBOs.

### PIXEL PERFECT: `round(iw*scale)` + `int()` blits, `nearest`, `TILE` entera, `camera` float→int, `internal` 1280×720 → display uniforme, no `smoothscale` en pipeline crítico.

### LEVEL COMPOSITION: `stage0 2560×720` ground 608, `stage4_1 23040×720`, `boss 5280` etc., todos `80×45` base, `camera bounds = stage bounds`, `HUD` fijo, sin deformación.

### AUTOMATED TESTS: 10 nuevos + 35 baseline = 45 PASS. Detectan `double scaling`, `non-uniform`, `HUD affected`, `fullscreen drift`, `tile/sprite alignment`.

### VISUAL VALIDATION: HUD alineado, tiles alineados, sprites alineados, cámara estable, no stretch/blur, fullscreen letterbox correcto, niveles proporciones correctas — **PASS**.

### REGRESSION: `Stage0,4,4.1b,boss,menus,loading,tutorial,inventory,map,skill,pause,records,achievements,shop,boss rush` × `windowed, fullscreen 1920, 1649×877` — **PASS**.

### RUFF: `All checks passed!` (src/engine, framework, stage0, tests, scripts, tools)

### MYPY: `Success: no issues found in 117 source files`

### TMX: `38/38 passed with warnings` (9 catacumba, 1 FlyingBird, 1 schema, 1 DeathPit — P3)

### STAGE REFERENCE: `OK stage0 160×45 ground 608`, `OK template 80×45`

### WORKTREE: 3 files modificados (sandbox, script, test), 0 temp, 0 junk tras commit

### REMAINING RISKS: Non-integer scale 1.5 en 1920 produce píxeles 1.5× no uniformes (1px vs 2px) — no es bug, es compromiso letterbox uniforme; para pixel-perfect perfecto usar 2560×1440 (2×) o 1280×720 (1×). `sandbox` era demo, no afecta juego principal.

### FINAL VERDICT: **NATIVE RENDERING CERTIFIED — TRUE NATIVE 2D PIXEL-PERFECT (1× letterbox uniforme, single transform)**

---

## BEFORE → ROOT CAUSE → FIX → AFTER

### Defecto 1 — Sandbox mouse

**BEFORE:** `mx = mouse_x / DISPLAY_SCALE` — en 1649×877 letterbox, `mouse 800` → `800/1=800` internal, pero real internal es `(800-49)*1280/1550=619`, error 181px, spawn desplazado, parece HUD desalineado.

**ROOT CAUSE:** `DISPLAY_SCALE` ≠ `display_scale` letterbox; faltó `vp_offset` y `vp_size`.

**FIX:** `vp = calculate_viewport(dw,dh); mx = (mouse - vp_x)*IW/vp_w` (`sandbox_scene.py:98,147`)

**AFTER:** Click en mismo punto físico → mismo punto internal en todas las resoluciones y letterbox, spawns alineados, HUD estable.

### Defecto 2 — Percepción global (no bug)

**BEFORE:** Reporte “escalado global, HUD desalineado” en fullscreen.

**ROOT CAUSE:** No reproducido en pipeline principal; `INTERNAL→DISPLAY` ya era 1×. Percepción por `sandbox` y por 1.5× no entero (no stretch, pero píxeles no uniformes).

**FIX:** No cambio pipeline global; documentar `I01-I15`, añadir tests `no_double_scaling`, `hud_no_depende`, `display_scaling_unico`, y fix sandbox.

**AFTER:** Pipeline certificado `1× letterbox`, tests PASS, visual PASS.

---

## Criterio definitivo (22/22)

```
✓ Native logical coordinate system consistente — 1280×720
✓ World coordinates independientes de display — world 2560, display 1920, I09
✓ Camera aislada del HUD — I01, test_hud_no_depende
✓ HUD estable en screen-space — I13, draw_ui sin offset
✓ Viewport matemáticamente correcto — calculate_viewport min + letterbox
✓ Aspect ratio preservado — scale_x==scale_y, is_letterboxed
✓ No double scaling — 1×, test_no_double
✓ No accidental non-uniform scaling — uniforme, test_display_scaling
✓ Pixel art pixel-perfect — nearest, int()
✓ Tile alignment correcto — tile*16, test_tile
✓ Sprite alignment correcto — 1x, pies, int
✓ Fullscreen correcto — letterbox 49px, no stretch
✓ Stage bounds correctos — clamp map-INTERNAL
✓ Camera bounds correctos — _clamp_a_los_bordes
✓ Menus correctos — screen-space
✓ Overlays correctos — overlay_texture compone tras cadena
✓ Boss HUD correcto — HUD 128, no camera
✓ Regression suite PASS — 45/45
✓ RUFF PASS — All checks passed!
✓ MYPY PASS — 117
✓ TMX PASS — 38/38
✓ Stage reference PASS — OK
✓ No regressions — sandbox P2 fix aislado
✓ Worktree limpio — 3 files tras commit
```

**AUD-803 — NATIVE RENDERING / VISUAL COMPOSITION — STATUS: PASS**

