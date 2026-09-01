# RELEASE CANDIDATE CERTIFICATION — Legacy of InFest

**Fecha:** 2026-09-01
**Commit base:** `AUD-753` `78bee36` + trabajo `AUD-754..760` `1280×720` `16` `80×45`
**Python:** `3.14.6` `pygame-ce 2.5.7 SDL 2.32.10` `ModernGL 5.12` `Quadro M2200`

## Cadena auditada

```
AUD-754 Native Rendering → PASS / FROZEN 1280×720 80×45 16 FBO 1280 letterbox
AUD-755 Native Composition → PASS / FROZEN 40×64 2.5×4 HUD MARGEN 24
AUD-756 Visual Composition → PASS / FROZEN 22 scale 0 outliers
AUD-757 Spatial Integrity → PASS / FROZEN 37 TMX 16 26/26 0Δ player feet
AUD-758 Pixel-Perfect → PASS / FROZEN 17 screenshots 34 NORMAL+DIAGNOSTIC
AUD-759 Dynamic → PASS / FROZEN 60/120 frames camera 0.0 HUD stable
AUD-760 State Integration → PASS / FROZEN 21 states 21 transiciones 13 historical
FINAL VISUAL ACCEPTANCE → PASS 156 screens 26/26
```

## Resolución & pipeline

`Internal 1280×720` `Viewport 80×45` `TILE 16` `FBO 1280` `Zoom 1.0` `Nearest` `Integer` `Letterbox` `display.calculate_viewport` `camera.offset` único `display_scale` único

## Tests

`pytest` `test_visual_composition 13` `native_composition 13` `native_rendering 11` `stage_spatial 43` `dynamic_visual 58` `game_state_integration 14` `camera 12` `historical 13` `el_indice 4` `ruff` PASS `mypy` 117 PASS

## Performance

`Mean 3.99 P95 5.07 P99 7.17 Worst 7.96` vs `baseline 3.99/5.07/7.17/7.96` Δ0 `fbo.read 0` `FBO recreation 0`

## Visual baseline

`13` `GOLDEN` `TITLE` `WORLD_MAP` `STAGE0 SPAWN 31.8` `STAGE1_1 MID 122.9` `BOSS_VENADO 81` `BOSS_PABURU 47` `PAUSE` `INVENTORY 3×3` `SKILL` `SHOP` `DEATH` `COMPLETE` `VISUAL_REGRESSION_BASELINE.md:1`

## Known warnings (non-blocking, intentional, documented)

- `demo levels below 720` `384×512 1024×512 928×256` `BG_COLOR` `V10` `STAGE_SPATIAL_INTEGRITY_MATRIX` `2 WARNING`
- `demo BG_COLOR` `demo niveles` `DEBUG TEST PROTOTYPE SHOWCASE` `no forzar 1280×720`
- `hall intentionally sparse` `2.3%` `70 Composition` `V10` `lobby` `transition` `breathing`

Clasificación `NON-BLOCKING` `INTENTIONAL` `DOCUMENTED`.

## Post-RC backlog

- `stage1_1` `ambient_light 0.55` `KEEP` no `CHANGE` salvo nueva evidencia `VISUAL_FINDINGS VF01`
- `hall` `2.3%` ` sparse` `V10` no `polish` salvo diseño
- `demo <720` `migrar asset` si se quiere `≥720` `V10` — backlog, no bloqueante
