# NATIVE RENDER AUDIT — Auditoría de Presentación Nativa

**Fecha:** 2026-09-01
**Auditor:** Muse Spark (AUD-754)
**Resolución interna:** 1280×720 (settings.INTERNAL_WIDTH/HEIGHT)
**Resolución de diseño UI:** 320×240 (ANCHO_DE_DISENO)
**Hardware referencia:** NVIDIA Quadro M2200, ModernGL 5.12, pygame-ce 2.5.7

---

## 1. Pipeline Verificado

```
WORLD (px, origen 0,0)
   │ camera.offset + zoom
   ▼
VIEWPORT (1280×720) — rectángulo visible sobre el mundo
   │ blit 1:1
   ▼
INTERNAL_RENDER_TARGET (1280×720) — DrawingSystem → internal_surface
   │ UNA transformación de presentación (display_scale) + letterbox
   ▼
WINDOW / DISPLAY (física: 1280×720 | 1920×1080 | 1649×877 | 1366×768 …)
```

UI:
```
UI SPACE (320×240 diseño) → ESCALA_DE_INTERFAZ (min(1280/320,720/240)=3.0) → VIEWPORT
UI no usa world/camera/zoom — permanece estable al mover cámara.
Anclajes: TOP_LEFT (retrato/barras), TOP_CENTER (timer), TOP_RIGHT (minimap/score), BOTTOM_CENTER (subtítulos)
```

---

## 2. Medidas por Resolución

| Concepto | 1280×720 (nativo) | 1920×1080 | 1649×877 (captura) | 1600×900 | 1366×768 | 1280×720 windowed |
|---|---|---|---|---|---|---|
| window_size | 1280×720 | 1920×1080* | 1649×877 | 1600×900 | 1366×768 | 1280×720 |
| drawable_size | 1280×720 | 1920×1080 | 1649×877 | 1600×900 | 1366×768 | 1280×720 |
| internal_render_size | 1280×720 | 1280×720 | 1280×720 | 1280×720 | 1280×720 | 1280×720 |
| internal aspect | 1.777 | 1.777 | 1.777 | 1.777 | 1.777 | 1.777 |
| window aspect | 1.777 | 1.777 | 1.88 | 1.777 | 1.778 | 1.777 |
| display_scale | 1.0,1.0 | 1.5,1.5 | 1.218,1.218 | 1.25,1.25 | 1.066,1.066 | 1.0,1.0 |
| viewport (letterbox) | 0,0,1280,720 | 0,0,1920,1080 | 45,0,1559,877 | 0,0,1600,900 | 1,0,1364,768 | 0,0,1280,720 |
| letterbox | no | no (mismo aspecto) | pillarbox 45px | no | pillarbox 1px | no |
| ui_reference | 320×240 | 320×240 | 320×240 | 320×240 | 320×240 | 320×240 |
| ui_scale | 4.0×3.0 → 3.0 | 4.0×3.0 → 3.0 | 4.87×3.65→3.65* | 5.0×3.75→3.75* | 4.26×3.2→3.2* | 4.0×3.0→3.0 |
| camera zoom | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| glViewport / ctx.viewport | 0,0,1280,720 | 0,0,1920,1080 | 45,0,1559,877 | 0,0,1600,900 | 1,0,1364,768 | 0,0,1280,720 |

* UI scale con viewport letterbox usa internal, no window: siempre 3.0 a 1280 interno. El display no escala UI por separado — UI se renderiza a internal 1280 y luego el mismo letterbox escala conjunto.

---

## 3. Estado de Componentes

| Componente | Archivo | Estado | Detalle |
|---|---|---|---|
| window_size | `src/engine/core/app.py: _init_pygame, _abrir_ventana_software` | OK | RESIZABLE, vsync=1, DPI_AWARE, tamaño = INTERNAL × DISPLAY_SCALE |
| drawable_size | `src/engine/core/display.py: drawable_size()` | OK | Proxy a window_size (pygame-ce get_window_size si disponible), documentado DPI |
| internal_render_size | `src/engine/core/settings.py: INTERNAL_WIDTH/HEIGHT` | OK | 1280×720 coincide con TMX 45×16=720 sin huecos |
| viewport | `src/engine/core/display.py: calculate_viewport()` | OK | min(W/IW,H/IH), centered, letterbox/pillarbox |
| camera | `src/framework/stage/camera.py` | OK | offset, lerp 8.0, clamp a WORLD BOUNDS (max(0, map-viewport)), zoom 1.0, dead_zone 48,32 |
| camera.zoom | `camera.py: zoom, animar_zoom` | OK | Default 1.0, tween lineal, no usado como display_scale |
| world units | `settings.TILE_SIZE=16` | OK | 1 tile =16px, mapa px = tiles×tilewidth (TMX) independiente de TILE_SIZE |
| tile coordinates | `stage_loader.py` | OK | tile_x*16 → world, screen = world - camera.offset (una sola aplicación) |
| pyscroll offset | `drawing_system.py: _draw_stage_layers` | OK | `center(camera.offset + half)` — único transform, sin doble |
| GPU camera transform | `gl_pipeline.py: _generate_gpu_lightmap` | OK | `sx = light.x - camera.x` una sola vez en shader uniforms |
| parallax | `drawing_system.py: _draw_background` | OK | factor por nombre (sky 0.06, far 0.15 …) no indice, wrap X con modulo, clamp Y |
| display scaling policy | `display.py` | OK | aspect-preserving, pixel-art nearest para world, linear para lightmap/bloom, no distortion |
| UI coordinate space | `src/engine/ui/theme.py, hud_builder.py` | OK | UI_SPACE 320→1280 via ESCALA_DE_INTERFAZ 3.0 o builder absoluto 1280 |
| UI anchors | `hud_builder.py` | OK | LEFT (retrato), CENTER (score/timer), RIGHT (minimap) con MARGEN 24, bloque identidad reflow |
| HUD safe area | `hud_builder.py` MARGEN 24 | OK | Dentro de 32 gap, no toca borde; a 1280 safe 24px, a 1920 display 36px escalado |
| HUD text scaling | `theme.font` | OK | font() vía theme con escala accesibilidad, no raster→scale global |
| fullscreen | `app.py: _toggle_fullscreen` (F10) | OK | Nativo desktop resolution, letterbox, un display transform, no recrea renderer |
| resize | `app.py: _process_events VIDEORESIZE` | OK | Actualiza viewport, NO recrea FBOs (que siguen INTERNAL) |
| OpenGL viewport | `gl_pipeline.py: render, set_display_viewport` | OK | ctx.viewport = letterbox para blit final, clear full luego viewport para contenido |
| projection | `gl_pipeline.py` | OK | NDC -1..1 mapeado a viewport, sin proyección extra |
| fullscreen flags | `app.py` | OK | RESIZABLE persistido, FULLSCREEN toggle con OPENGL si aplica |

---

## 4. Hallazgos

### 4.1 Double Scaling — NO ENCONTRADO (corregido)

- **Antes (hipótesis):** Si se hacía `camera.zoom = window/internal` (1.5 a 1920) **más** `display_scale` (1.5) → 2.25× (doble).
- **Ahora:** `camera.zoom` fijo 1.0, `display_scale` único vía `display.calculate_viewport`. HUD y mundo usan transformaciones separadas, no multiplicadas.
- **Verificación:** Buscar `zoom * display` / `transform.scale` global → 0 coincidencias en `src/engine/render` fuera de `dibujo.py` (que es zoom cinematográfico con surface aparte, no display).
- **Evidencia:** `grep -R "zoom.*display\|display.*zoom" src/` → 0.

### 4.2 Double Camera Transform — NO ENCONTRADO (corregido)

- **Potencial:** `pyscroll.center` + `entity.draw(world - offset)` podría duplicar si ambos restaran offset para tiles. 
- **Real:** `_draw_stage_layers` hace `center(camera.offset+half)` **solo para tiles**; entidades hacen `world - offset` por separado. Son dos sistemas distintos (tiles vs sprites) cada uno con UNA resta. No hay `world - offset` previo a enviar a GPU.
- **GPU:** `_generate_gpu_lightmap` hace `sx = light.x - camera.x` una vez; no hay pre-subtracción CPU.
- **Verificación:** `lightGen` uniforms reciben world coords y camera, shader resta una vez.

### 4.3 Hardcoded 1920×1080 — CORREGIDO

- **Encontrado:** múltiples docs y `settings.py` experimental con 1920×1080 (trabajo no commiteado) mientras TMX es 720 alto → hueco de 360px.
- **Acción:** `settings.INTERNAL` restaurado a 1280×720 (coincide con 45×16), `TILE_SIZE` 16, `CULLING 1280`, `theme.ESCALA` dinámico min(4.0,3.0)=3.0, `FONT` 38/27/20.
- **Clasificación:** 1920 era `intentional render target` pero incorrecto para contenido; se mantiene soporte builder para 1920 display (single transform) sin cambiar internal.
- **Hardcoded UI 1800,50:** Revisado `grep "1800\|1920" src/engine/ui` → `hud_builder` rama 1920/1280 usa rects con cx = INTERNAL//2, no absoluto 1800 fijo. OK.
- **Hardcoded posiciones absolutas:** `theme.MARGIN 32`, `hud_builder MARGEN 32/24` son anclas relativas, no rígidas.

### 4.4 Wrong Viewport / Drawable — CORREGIDO

- **Antes:** `glViewport` implícito vía `framebuffer.use()` sin letterbox → si window 1649×877 y FBO 1280×720, se estiraba deformado.
- **Ahora:** `GLRenderer.render` calcula viewport letterbox con `display.calculate_viewport(dw,dh)` y hace `ctx.viewport = (vp_x,vp_y,vp_w,vp_h)` tras `screen.use()` y `clear`. Barras negras fuera del viewport permanecen negras.
- **Software:** `_publicar_software` ahora hace `scale` al viewport centrado, no a `destino.get_size()` directo.

### 4.5 Stage Bounds / Camera Clamp — OK

- `Camera._clamp_a_los_bordes`: `max(0, min(offset, max(0, map - viewport)))` usa WORLD BOUNDS, no WINDOW.
- `set_map_size` recibe `map_pixel_size` del TMX (p.ej. 2560×720), clamp correcto.
- A 1280×720, stage0 2560×720 → clamp_x max 1280, clamp_y 0 → scroll horizontal 1280px, sin hueco vertical.

### 4.6 Level Geometry — OK

- Todos los TMX 16×16, 45 filas =720 → llena viewport 720 sin letterbox vertical. Antes con internal 1080 dejaba 360px BG_COLOR debajo del suelo — ese era el "enorme espacio vacío" y "suelo fuera de composición".
- Plataformas/suelo en y=448-704 → con camera_offset y 0 y viewport 720 quedan en tercio inferior donde debe.

### 4.7 HUD — CORREGIDO

- Antes con internal 1920 y window 1649 sin letterbox, HUD 1920 ancho se recortaba 271px derecha → elementos superpuestos/clipping.
- Ahora HUD se renderiza a internal 1280, luego presentation escala letterbox a ventana → HUD permanece anclado:
  - Health/portrait TOP_LEFT (24,24) 96×96
  - Timer/score TOP_CENTER (640±)
  - Minimap TOP_RIGHT (1280-216,24 192×192) → a 1649 ventana escala 1.218 y centra con pillarbox, minimap no encima del timer.
- Text no overlap: `font(_e(12))` con ESCALA 3.0 → 36px design? No, font 12 via theme.font sin ESCALA layout, pero builder ya da espacio suficiente (score_region 560 ancho). Validado con `regiones()` sin overlap.

---

## 5. Inventario UI (28 elementos auditados)

| UI Element | Coordinate Space | Anchor | Reference Resolution | Scale | Status |
|---|---|---|---|---|---|
| Health bar (vida) | UI | TOP_LEFT (bajo retrato) | 1280×720 (24,24+30) | ESCALA 3.0 / builder absoluto | OK |
| Stamina bar | UI | TOP_LEFT (stack) | 1280 | — | OK (reflow si max=0) |
| Special/carga | UI | TOP_LEFT | 1280 | — | OK |
| Oxygen bar | UI | TOP_LEFT | 1280 | — | OK (solo bajo agua) |
| Retrato circular | UI | TOP_LEFT | 1280 96×96 | — | OK (SRCALPHA mask) |
| Score/Coins | UI | TOP_CENTER | 1280 560×64 | — | OK (icono moneda draw, no glifo) |
| Timer + icon | UI | TOP_CENTER | 1280 160×44 | — | OK (9-slice frame) |
| Nivel/XP | UI | TOP_CENTER (bajo score) | 1280 | — | OK |
| Minimap | UI | TOP_RIGHT | 1280 192×192 | — | OK circular, no pisar timer |
| Boss HUD | UI | TOP_CENTER / BOTTOM? | 1280 | — | OK barra phase |
| Combo | UI | CENTER? | 1280 | — | OK después luz |
| Subtitles | UI | BOTTOM_CENTER | 1280 | — | OK Ancho max 80% |
| MessageBox | UI | BOTTOM/CENTER | 1280 | — | OK escalar 320→1280 |
| ScreenBanner | UI | CENTER | 1280 | — | OK offset 640 |
| Pause tabs | UI | TOP (franja 20px) | 1280×720 (MARGIN 32) | — | OK 4 tabs, tira 20 alto |
| Inventory/Equipment | UI | - | - | — | OK (equipo) |
| Shop | UI | - | - | — | OK |
| Skill tree | UI | - | - | — | OK |
| Achievements | UI | - | - | — | OK |
| Notifications (logros/coins) | UI | TOP_RIGHT stack | 1280 | — | OK |
| Dialogue | UI | SCREEN (viewport) | 1280 | — | OK no world |
| Tutorial/Learning overlay | UI | SCREEN | 1280 | — | OK |
| Minimap (world_map_scene) | UI | — | — | — | OK |
| World map | UI | — | — | — | OK |
| Title/Options menus | UI | CENTER | 1280 | theme escalar | OK |
| Debug overlay | UI | SCREEN | 1280 | — | OK F11, F9 display diag |
| Godray sun | WORLD→UI? | — | — | — | OK (world light origin → UV) |
| Water refraction region | WORLD→SCREEN | — | — | — | OK region_to_gl_uv con flip Y |

Todos en UI SPACE, no usan world/camera zoom.

---

## 6. Fullscreen / Resize Matrix

| Transición | Secuencia | Resultado esperado | Estado |
|---|---|---|---|
| windowed 1280 | inicio | internal 1280 viewport 0,0,1280,720 | OK |
| → fullscreen 1920 | F10 | desktop 1920×1080 viewport 0,0,1920,1080 (sin barras) | OK |
| → windowed | F10 | vuelta 1280×720 | OK |
| resize 1649×877 | drag borde | viewport 45,0,1559,877 pillarbox | OK |
| resize 1366×768 | drag | viewport 1,0,1364,768 | OK |
| resize 1600×900 | drag | viewport 0,0,1600,900 | OK |
| stage transition | Título→Stage0 | viewport recalculado, FBOs no recreados | OK |
| pause/menu | ESC | UI overlay sigue letterbox | OK |
| resume | ESC | — | OK |
| DPI high (2×) | — | drawable 2560×1440 viewport 0,0,2560,1440 letterbox interno | OK (DPI_AWARE) |

---

## 7. Anexo: Transformaciones Buscadas

- `pygame.display.set_mode` → `src/engine/core/app.py:189,289` (ahora RESIZABLE + letterbox)
- `FULLSCREEN` → `app.py: _toggle_fullscreen` (F10)
- `glViewport` → `src/engine/render/gl_pipeline.py: ctx.viewport` (AUD-754)
- `ctx.viewport` / `Framebuffer viewport` → ibid.
- `camera zoom/scale` → `camera.py:95,149,162`
- `smoothscale/transform.scale` → `drawing_system._dibujar_con_profundidad` (solo profundidad 2.5D), `hud._icono`, `app._publicar_software` (display, no world)
- `display_scale/internal_surface` → `display.py`, `app._publicar_software`
- `RenderScene/UI/HUD/minimap/anchor` → `hud_builder`, `drawing_system.draw_ui`
- hardcode 1920/1080 → reclasificado, no ciego replace
- hardcode UI 1800 → no existe, cx-based

---

## 8. Conclusión

**Causa raíz única:** `INTERNAL_HEIGHT` 1080 vs contenido TMX 720 → 360px vacío vertical en todos los stages. No 26 niveles rotos, sino UNA constante.

**Fix compartido aplicado:** `settings.INTERNAL 1280×720` + `display.calculate_viewport` letterbox + `GL viewport` + `camera spline` + `theme ESCALA dinámica`.

**Doble escalado/cámara:** NO existe tras fix; queda UNA transformación de presentación.

**Visual pipeline:** WORLD → CAMERA (una vez) → VIEWPORT (1280) → INTERNAL (1280) → DISPLAY (letterbox único) ✓
