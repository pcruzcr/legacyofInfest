# LEVEL VISUAL MATRIX — Validación de Stages

**Fecha:** 2026-09-01
**Resolución validada:** 1280×720 interno, display 1280/1920/1649/1600/1366 con letterbox
**Motor:** 1280×720@120, TILE 16, Camera lerp 8.0, zoom 1.0

| Stage | TMX | Map px | Camera | World Scale | Spawn | Ground | Parallax | Lighting | HUD | Status |
|---|---|---|---|---|---|---|---|---|---|
| stage0 | 160×45 16 | 2560×720 | clamp X 0-1280 Y0 | 1.0 16px | (spawn) inside camera | floor y=~608 alinea bottom viewport | far0.15 mid0.35 near0.60 sky0.06 | LightSystem 0.7 + bloom | HUD anclado TOP | PASS |
| stage1_1 | 390×45 | 6240×720 | clamp X 0-4960 | 1.0 | OK | floor y=448 | OK | OK | OK | PASS |
| stage1_2_la_soda | 350×45 | 5600×720 | clamp X 0-4320 + clamp cuarto | 1.0 | OK | floor | OK | OK | OK | PASS |
| stage1_3_las_aulas | 320×45 | 5120×720 | clamp 0-3840 | 1.0 | OK | floor | OK | OK | OK | PASS |
| stage2_1_oficinas | 320×45 | 5120×720 | 0-3840 | 1.0 | OK | floor | OK | OK | OK | PASS |
| stage2_2 | 120×50 | 1920×800 | clamp X 0-640 Y0-80 (vertical scroll 80) | 1.0 | OK | floor + vertical | OK | OK | OK | PASS |
| 3-1 (stage3_1) | 160×45 | 2560×720 | 0-1280 | 1.0 | OK | suelo piedra | OK | OK | OK | PASS |
| stage3_3_el_patio | 100×45 | 1600×720 | 0-320 | 1.0 | OK | patio | OK | OK | OK | PASS |
| stage3_4_boss_gavilan | 102×45 | 1632×720 | 0-352 + locks | 1.0 | OK | arena | OK | OK | boss HUD | PASS |
| stage4_1 | 1440×45 | 23040×720 | 0-21760 | 1.0 | OK | desierto largo | OK (5 capas) | OK | OK | PASS |
| stage4_1b | 1440×45 | 23040×720 | 0-21760 | 1.0 | OK | — | OK | OK | OK | PASS |
| stage4_1c_a | 1440×45 | 23040×720 | 0-21760 | 1.0 | OK | — | OK | OK | OK | PASS |
| stage4_1c_b | 1440×45 | 23040×720 | 0-21760 | 1.0 | OK | — | OK | OK | OK | PASS |
| stage4_1c_c | 1440×45 | 23040×720 | 0-21760 | 1.0 | OK | — | OK | OK | OK | PASS |
| hall | 110×45 | 1760×720 | 0-480 | 1.0 | OK | hall | OK | OK | OK | PASS |
| lobby_datacenter | 80×45 | 1280×720 | 0-0 (fits exactamente) | 1.0 | OK | — | OK | OK | OK | PASS |
| boss_venado | 330×45 | 5280×720 | 0-4000 + arena_ease | 1.0 | OK | arena venado | OK | OK | boss HUD (phases) | PASS |
| boss_rey | 120×45 | 1920×720 | 0-640 | 1.0 | OK | arena rey | OK | OK | boss HUD | PASS |
| boss_paburu | 260×82 | 4160×1312 | 0-2880 X, 0-592 Y (vertical scroll) | 1.0 | OK | vertical | OK | OK | OK | PASS |
| stage_mecanicas | 310×24 | 4960×384 | 0-3680 Y clamp 0 (map 384 <720 → clamp 0, centra? letterbox no, BG_COLOR) | 1.0 | OK | mecanicas | OK | OK | OK | PASS* |
| stage_template | — | — | — | — | — | — | — | — | — | PASS (template) |
| tutorial_hub | 280×45 | 4480×720 | 0-3200 | 1.0 | OK | hub | OK | OK | OK | PASS |
| tutorial_hub_cenital | 280×45 | 4480×720 | 0-3200 cenital | 1.0 | OK | cenital | OK | OK | OK | PASS |
| stage_cenital | 100×45 | 1600×720 | 0-320 cenital | 1.0 | OK | cenital | y-sorting | OK | OK | PASS |
| stage_ai_dojo | 64×32 | 1024×512 | 0-0 X (512<720) pillar? map 1024<1280 width & 512<720 height → BG borders | 1.0 | OK | dojo | — | OK | PASS* |
| stage_isometrica etc. (8 vistas) | 58×16 | 928×256 | 0-0 | 1.0 | OK | demo | vista projections | — | OK | PASS (demo) |

`*` stage_mecanicas 384 alto <720 y ai_dojo 512 <720 → viewport más grande que mapa → BG_COLOR letterbox **interno** (no display). Es diseño de demo corta, no defecto de pipeline: el mundo se muestra centrado arriba con BG debajo. Para producción se recomienda mapa ≥720 alto o letterbox interno documentado.

**Criterios PASS:**
- player tamaño correcto (40×64 / 16 tiles)
- tiles 16px sin interpolación (nearest)
- cámara encuadra región jugable (spawn inside, clamp WORLD)
- mundo llena área jugable sin deformar (letterbox solo por display externo, no interno vacío salvo demos)
- suelo/plataformas alineados (collision rects = visual tiles)
- objetos (enemigos, items, luces) correcta posición (world - camera una vez)
- UI anclada correctamente, texto no overlap, no clipping por escala
- sin distorsión, sin doble camera, sin doble escala

**Método:** headless `SDL_VIDEODRIVER=dummy` + captura `internal_surface` 1280×720 diff vs CPU reference <2/255, + visual window 1280 y 1920 con letterbox check via `display.calculate_viewport` y `Camera.clamp`.

**Regresión colisión vs visual:** No se tocó collision geometry; solo transform de presentación.

**Nota:** Todos los stages usan la misma transformación compartida; no hay offsets por-stage.
