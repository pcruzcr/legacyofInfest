# RELEASE CANDIDATE FREEZE — Arquitectura y contenido congelado

**Fecha:** 2026-09-01
**Estado:** `RELEASE CANDIDATE FREEZE`

## Congelado

```
Internal Resolution = 1280×720 (80×45 tiles)
Viewport = 80×45
TILE = 16×16
FBO = 1280
Zoom = 1.0
Nearest
Integer positioning
Letterbox display.calculate_viewport
Camera architecture src/framework/stage/camera.py:299 world - offset
HUD architecture src/engine/ui/hud_builder.py:37 anchor TOP_LEFT 24,24 MARGEN 24
World coordinates src/framework/stage/stage_loader.py:688 Rect(obj.x, ...)
SceneManager src/engine/scene/scene_manager.py
StateManager src/engine/scene/scene_manager.py
SaveManager src/engine/core/save_manager.py
Rendering pipeline src/engine/core/app.py:74 letterbox + src/engine/render/gl_pipeline.py:1321 ctx.viewport
Parallax src/framework/stage/stage_loader.py VELOCIDAD_DE_FONDO 0.06/0.15/0.35/0.60
Collision geometry src/framework/stage/stage_data.py Rect(x,y,w,h) top-left
```

## Prohibido sin evidencia CRITICAL BUG

`global scaling` `structural scaling` `global zoom` `TILE` `alternative coordinate` `renderer replacement` `FBO replacement` `HUD rewrite` `camera rewrite`

## Level design congelado 26/26 VISUAL PASS

`DO NOT REBALANCE` `DO NOT RESPACE` `DO NOT REDESIGN` `DO NOT ADD/REMOVE DECORATION` `DO NOT MOVE LANDMARKS/CHECKPOINTS/BOSSES` salvo `CRITICAL BUG` verificable.

## Art direction congelado

`stage0 fog 31.8` `stage1_1 bright/open 122.9 ambient_light 0.55 KEEP` `stage2_2 vertical 800` `boss arenas 1280-5280` `hall sparse 2.3% V10` `background hierarchy` `lighting` `parallax` `pixel-art`

Especial `stage1_1 ambient_light =0.55` `INTENTIONAL ART DIRECTION` — no revertir.

## Demos

`384×512 1024×512 928×256` `DEBUG TEST PROTOTYPE SHOWCASE` `no forzar 1280×720` `no scaling`

## World map

`26 nodes 32×32 camera 0 scale 1.0 native` `no histórico 128`

## Performance freeze

`Mean 3.99 P95 5.07 P99 7.17 Worst 7.96` `FBO recreation 0` `fbo.read 0` — no regresión significativa.

## Cambio futuro

`WHY CHANGE? WHAT BUG? WHAT EVIDENCE? WHAT REGRESSION TEST?` Si no, `DO NOT MODIFY` `POST-RC BACKLOG` rama separada, no destruir baseline.
