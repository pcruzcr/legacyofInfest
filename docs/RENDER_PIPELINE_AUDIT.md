# RENDER PIPELINE AUDIT — AUD Final Fase 5

**Fecha:** 2026-09-01 · **Pipeline:** `WORLD→CAMERA→VISIBLE→LAYERS→OBJECTS→SPRITES→LIGHTING→EFFECTS→HUD→FINAL`

| Etapa | Dónde se dibuja | Resolución | Transformación | Origen | Escala | Alpha | Orden | Archivo:Line |
|---|---|---|---|---|---|---|---:|---|
| World tiles | `internal_surface 1280×720` | `1280×720` | `camera.offset` `center+half` | `top-left 0,0` | `1.0` `nearest` | `255` | `0` `Terrain` | `drawing_system.py:640` |
| Background far/mid/near | `internal` | `1280×720` (1280/2560/3840) | `offset*factor%w` `clamp Y` | `0,0` | `1.0` `nearest` | `255` | `-1` `BG` | `drawing_system.py:592` |
| Objects (chests) | `internal` | `1280×720` | `world - offset` | `midbottom 32×24` | `1.0` | `255` | `1` `objects` | `drawing_system.py:355` |
| Sprites player `40×64` | `internal` | `1280×720` | `world - offset` `feet midbottom` | `top-left` `feet` | `1.0` `squash 1.1` `scale` `VALID ANIMATION` | `255` | `2` `entities` | `player.py:1041` `scale` `VALID` |
| Depth sprites `2.5D` | `internal` | `1280×720` | `world - offset` `porProfundidad` `scale 0.85-1.0` | `feet` | `0.85-1.0` `nearest` `VALID ANIMATION` | `255` | `2` | `drawing_system.py:836` `scale` |
| Lighting | `light FBO 640×360` `→ internal` | `640×360→1280` | `world - camera` `shader` | `light pos world` | `1.0` `linear` | `blend MULT` | `3` | `lighting.py:307` `gl_pipeline 0.06` |
| Particles `4×4` | `internal` | `1280×720` | `world - offset` | `center` | `1.0` | `alpha 110` | `4` | `particle_system` |
| HUD `96×16` `192×192` | `internal overlay SRCALPHA 1280×720` | `1280×720` | `anchor TOP_LEFT 24,24` `MARGEN` | `top-left` `center` | `1.0` | `255` | `5` `overlay` | `hud.py:37` `hud_builder 58` |
| Final | `display` `window 1280/1920` | `window` | `letterbox` `display.calculate_viewport` `ctx.viewport` | `vp_x,vp_y` | `1.5` `letterbox` | `255` | `6` | `app.py:74` `gl_pipeline 1321` |

**Scaling clasificación:**

| Uso | Archivo:Line | Tipo | Veredicto |
|---|---|---|---|
| `player squash` `transform.scale(frame,(ancho,alto))` | `player.py:1041` | `ANIMATION FRAME SCALING` `squash 1.1` | VALID NATIVE |
| `2.5D depth` `scale(lienzo,(ancho,alto))` | `drawing_system.py:836` | `LEGITIMATE ASSET SCALING` `porProfundidad 0.85-1.0` `nearest` | VALID NATIVE |
| `lightmap half` `smoothscale 640→1280` | `lighting.py` | `LEGITIMATE` `linear` `baja frecuencia` | VALID |
| `hud icon 16` `scale` | `hud.py` `icon` | `LEGITIMATE ASSET SCALING` `16` | VALID |
| `background size=(1280)` | `stage_loader.py:661` | `FORBIDDEN STRUCTURAL` si `<1280` → **CORREGIDO** `no-forzado ≥1280` | FIXED AUD-755 |
| `display letterbox` `scale(origen,(vp_w,vp_h))` | `app.py:74` `gl_pipeline 1321` | `VALID NATIVE` `display_scale` único | VALID |
| `boss Venado smoothscale` `halo` | `boss_venado.py:1692` | `LEGITIMATE EFFECT` `bloom` | VALID |
| `tile*scale` `sprite*scale` `world*scale` | `grep tile.*scale` 0 | — | NONE |

**Conclusión:** `0` `FORBIDDEN STRUCTURAL` tras `AUD-755` `stage_loader` fix; `7` `VALID` restantes.
