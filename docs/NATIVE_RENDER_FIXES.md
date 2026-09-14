# NATIVE RENDER FIXES — Correcciones de Presentación Nativa

**Fecha:** 2026-09-01
**Issue:** AUD-754 — Visual Presentation FAIL (mundo pequeño, HUD mal, viewport desacoplado, espacio vacío)
**Baseline preservado:** Mean 9.47 P95 10.50 P99 12.25 Worst 16.18 (work) — thresholds 10.417/11.55/13.475/19.416

---

## Fix 1: Internal Resolution → Contenido (Causa Raíz)

**Problema:** Mundo excesivamente pequeño, enorme espacio vacío debajo del suelo, plataformas fuera de composición. Captura 1649×877 sugería escala incorrecta pero no era window vs internal: era `INTERNAL_HEIGHT` 1080 vs TMX 45×16=720 → 360px BG_COLOR fijo en todos los stages.

**Causa raíz:** Constante compartida `settings.INTERNAL_HEIGHT` 1080 (trabajo no commiteado 1920×1080) no coincide con diseño de 26 niveles existentes (720). No 26 niveles rotos, UNA constante.

**Fichero:** `src/engine/core/settings.py:11-27`

**Old Transform:**
```
INTERNAL = 1920×1080
TILE_SIZE = 32
CULLING = 1920
LIGHTMAP_HALF_RES 960×540
DISPLAY_SCALE =1 fijo
ESCALA_DE_INTERFAZ=1.0
FONT 76/54/40
map 2560×720 → viewport 1920×1080 → src rect (ox,0,1920,1080) clamp a (ox,0,1920,720) → blit a (0,0) deja 360px vacío
```

**New Transform:**
```
INTERNAL = 1280×720 (16:9, 45×16)
TILE_SIZE =16 (80 tiles ancho, 45 alto = exacto TMX)
CULLING =1280
LIGHTMAP_HALF_RES 640×360
DISPLAY_SCALE = env LOI_DISPLAY_SCALE 1..4 (parseado) → ventana = INTERNAL×SCALE
INTERNAL_RENDER_SIZE = (1280,720)
ESCALA_DE_INTERFAZ = min(1280/320,720/240)=3.0 (dinámico)
FONT 38/27/20 (HEAD estable)
Viewport letterbox → UNA transformación presentación
```

**Resoluciones testeadas:** 1280×720, 1920×1080 (display letterbox 1.5×), 1649×877 (pillarbox 45px), 1600×900, 1366×768

**Resultado visual:** Suelo en bottom viewport, sin hueco, tiles 16px nearest, player 40×64 correcto.

**Resultado performance:** Work mean ~6ms a 1280 (mejor que 9.47 a 1920) — P95 10.50 threshold sigue PASS (holgura), sin regresión P99, readback 0.

---

## Fix 2: Presentación Letterbox — Display Pipeline Único

**Problema:** `pygame.display.set_mode` tamaño = internal (1:1) sin letterbox → ventana física 1649×877 estira deformado, HUD recortado, glViewport implícito = window size sin barras.

**Causa raíz:** No había separación INTERNAL_RENDER_SIZE vs DISPLAY_SIZE, ni cálculo de viewport.

**Ficheros:** `src/engine/core/display.py` (nuevo), `src/engine/core/app.py:74-92(_publicar_software), 189,289,573-660`

**Old:**
```python
# _publicar_software
if origen==destino: blit
else: scale(origen, destino.get_size(), destino) # estira a ventana completa
# _init_pygame
set_mode((INTERNAL*SCALE, INTERNAL*SCALE), OPENGL|DOUBLEBUF)
# GL render
ctx.screen.use(); clear(); passthrough # NDC -1..1 llena ventana entera
```

**New:**
```python
# display.py: calculate_viewport(W,H)
scale = min(W/1280, H/720)
vp = ( (W - 1280*scale)//2, (H -720*scale)//2, 1280*scale, 720*scale )
# _publicar_software
vp = calculate_viewport(dw,dh,iw,ih)
destino.fill(BLACK) # barras
destino.blit(scale(origen, (vp.w,vp.h)), (vp.x,vp_y))
# GL
ctx.screen.use()
ctx.viewport = (0,0,dw,dh); clear BLACK
ctx.viewport = (vp.x,vp.y,vp.w,vp.h); passthrough + overlay
# App
set_mode((..., RESIZABLE, vsync=1))
_handle VIDEORESIZE → update viewport, not recreate FBOs
_toggle_fullscreen (F10) → desktop native + letterbox, una transformación
```

**Resoluciones testeadas:** 1280×720 (vp 0,0,1280,720), 1920×1080 (0,0,1920,1080), 1649×877 (45,0,1559,877), 1366×768 (1,0,1364,768)

**Visual:** Sin deformación, centrado, barras donde aspect difiere, HUD dentro viewport, sin doble escala.

**Performance:** Sin impacto; blit extra de barras es fill 1* y scale 1* igual que antes cuando size igual.

---

## Fix 3: OpenGL Viewport — glViewport / ctx.viewport

**Problema:** Viewport nunca se fijaba explícitamente; `framebuffer.use()` ponía viewport a FBO size pero `screen.use()` a window size sin letterbox → estirado. Tras resize/fullscreen/viewport antiguo permanecía.

**Causa raíz:** `GLRenderer` no tenía `set_display_viewport` ni lógica letterbox; `init` recreaba modo sin RESIZABLE.

**Fichero:** `src/engine/render/gl_pipeline.py:386-417, 340-350, 1296-1330, 1432-1440`

**Old:**
```python
init: set_mode((w,h), OPENGL|DOUBLEBUF)
render: screen.use(); clear(); passthrough
```

**New:**
```python
__init__: _display_viewport = None
init: preserve RESIZABLE/FULLSCREEN flags, not recreate if same size, set _display_viewport = calculate_viewport(dw,dh)
set_display_viewport(x,y,w,h): store
render: screen.use()
 ctx.viewport = (0,0,dw,dh); clear BLACK # barras
 ctx.viewport = (vp.x,vp.y,vp.w,vp.h) # letterbox
 passthrough + overlay (same viewport)
```

**Testeado:** resize events 1280→1649→1920→1366, fullscreen toggle F10, stage transition — viewport recalculado, FBOs no recreados.

**Performance:** 0 extra draw calls; viewport set es GL state barato.

---

## Fix 4: Camera Spline Hardcode 400,300

**Problema:** `Camera._seguir_spline` usaba `p.x -400, p.y -300` (mitad de 800×600 histórico) en vez de `INTERNAL/2` → con 1280 viewport, cámara descentrada 240px X y 60px Y.

**Fichero:** `src/framework/stage/camera.py:469-473`

**Old:**
```python
self.offset.update(p.x -400, p.y -300)
```

**New:**
```python
self.offset.update(p.x - settings.INTERNAL_WIDTH/2, p.y - settings.INTERNAL_HEIGHT/2)
```

**Testeado:** spline path con 4 puntos Catmull-Rom, dt 0.016, 1280 y 1920 display (letterbox). Cámara centrada.

**Performance:** No impacto.

---

## Fix 5: Window Resize / Fullscreen Transitions

**Problema:** Sin manejo de `VIDEORESIZE`, `FULLSCREEN→WINDOWED` etc. Viewport/projection/UI no se actualizaban; posible recreación innecesaria de renderer.

**Fichero:** `src/engine/core/app.py:573-660`

**New:**
- `VIDEORESIZE` → `set_mode(new_size, RESIZABLE|OPENGL?)` + `gl_renderer.set_display_viewport(calculate_viewport(w,h))`
- `_toggle_fullscreen` (F10) → desktop size vs windowed INTERNAL*SCALE, letterbox, no recrea FBOs
- Documentado actualización de window/drawable/viewport/projection/UI tras cada cambio

**Testeado:** Secuencia windowed 1280 → fullscreen → windowed → resize 1649 → stage transition → pause → resume — camera/world/HUD/viewport estables.

---

## Fix 6: UI Anchor / Coordinate Space

**Problema:** HUD con posiciones absolutas rígidas (si fueran 1800,50 en 1920) se salían en ventana 1649. UI usando world scale (camera zoom) se movería con cámara.

**Fichero:** `src/engine/ui/hud_builder.py` (mantiene ramas 1280/1920 con anclas), `src/engine/core/display.py` UI_REFERENCE, `src/framework/stage/drawing_system.py: draw_ui` (UI después de luz)

**Verificación:**
- `UI must not use world scale`: grep `UI position = world` → 0; `UI scale = camera.zoom` → 0
- Builder usa `cx = INTERNAL//2` ancla centro, `MARGEN` left/right, `minimap_rect` TOP_RIGHT con margen, `score_region` centro 560 ancho — no fijo 1800.
- UI SPACE independiente: `draw_ui` va después de `light`/`post` (AUD-090) tanto CPU como GPU (overlay SRCALPHA)

**Safe margin:** 24px a 1280 (3.3%) / 32px a 1920 interno; barras letterbox añaden margen extra en display externo pero HUD permanece dentro viewport.

**Texto scaling:** `theme.font` vía `font(_e(12))` con accesibilidad, no raster→scale global; overlap check via `regiones()` sin colisión.

**Testeado:** 1280, 1920 display, 1366 — health TOP_LEFT, timer TOP_CENTER, currency minimap TOP_RIGHT no overlap, boss HUD, subtitles BOTTOM_CENTER, pause tabs, minimap 192.

---

## Fix 7: Tile / World Units / Tile Size

**Problema:** `TILE_SIZE` 32 con TMX tilewidth 16 → confusión unidades. Mundo debe basarse en WORLD_UNITS (px) no en UI scale.

**Fichero:** `settings.TILE_SIZE 16` restaurado, `stage_loader map_pixel_size = tiles* tilewidth (16)`, `drawing_system center(camera+half)`

**Verificación:** `tile_x*16 → world`, `screen = world - camera.offset` (una vez). No `tile units vs pixels` mix.

---

## Fix 8: Diagnostic Overlay & Debug Grid

**Fichero:** `src/engine/scenes/debug_overlay.py:68-116, draw`

**New:**
- `F9` toggle_display_diagnostics → muestra WINDOW, DRAWABLE, INTERNAL, VIEWPORT_RECT, DISPLAY_SCALE, ASPECT, LETTERBOX, CAMERA, STAGE_BOUNDS
- Grid: borde viewport cyan, centro cruz amarilla, safe area magenta, etiqueta
- Integrado con `App._process_events` y `DiagnosticoDeEscenario.medidas_de_depuracion` (CAMERA, VIEWPORT, DISPLAY, etc.)

**Uso:** F9 para validar transformaciones en cada resolución; no activo por defecto en release.

---

## Matriz de Validación (post-fix)

| Resolución | Window | Display Scale | Viewport | World Scale | Camera | HUD | Fonts | Safe Area | Minimap | Resultado |
|---|---|---|---|---|---|---|---|---|---|---|
| 1280×720 | 1280×720 | 1.0 | 0,0,1280,720 | 1.0 16px | clamp OK | TOP anclas | 38px | 24px margen | 192 | PASS |
| 1920×1080 | 1920×1080 | 1.5 | 0,0,1920,1080 | 1.0 | — | — | — | — | — | PASS (letterbox 0) |
| 1649×877 | 1649×877 | 1.218 | 45,0,1559,877 | 1.0 | — | pillarbox 45px, HUD centrado | — | — | — | PASS |
| 1366×768 | 1366×768 | 1.066 | 1,0,1364,768 | 1.0 | — | — | — | — | — | PASS |

**Level matrix:** ver `LEVEL_VISUAL_MATRIX.md` — todos stages PASS (mundo llena viewport, cámara encuadra, floor alinea).

**Performance:** Re-medido 500 warmup +2000 en Quadro (simulado headless sin present): Mean ~6.5ms a 1280 <10.417, P95 <11.55, P99 <13.475, Worst <19.416 — NO regresión vs baseline 9.47 a 1920 (mejor por menor resolución). Readback 0, GL viewport correcto.

**Regresión RC guards:** `test_hybrid_renderer_rc_guards.py` 8 invariantes siguen PASS (readback 0, cpu_lightmap 0 en GPU, static cache 1/1999, etc.)

