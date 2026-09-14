# AUD-758 FINDINGS — Inspección visual real

**Fecha:** 2026-09-01 · **Screenshots:** `qa_screenshots/*_normal.png` `1280×720` + `diagnostic` `qa_gen.log` `metrics.log` · **Metodología:** observación pantalla completa 17 niveles + métricas `occupancy` `brightness` `contrast`

| ID | LEVEL | SCREEN `x,y 1280×720` | OBJECT | OBSERVED | EXPECTED | ROOT CAUSE | EVIDENCE `qa_screenshots` `metrics` | FIX | RISK |
|---|---|---|---|---|---|---|---|---|---|
| V01 | stage1_1 | `~640,200` `midground` | `bg_stage1_1_mid 2560×720` | `brightness 122.9` `contrast 67.2` `occupied 100%` `bg` domina, `player 40×64` pierde `14.7` vs `bg` pero `HUD 182` `high` — `mid` 2560 muy brillante vs `far` | `V04 Contrast` | `metrics.log: stage1_1 122.9 67.2 100%` `stage0 31.8` comparación | Ajustar `tint` `bg_mid` `0.85` o `light ambient 0.65→0.55` en `stage1_1.tmx` `ambient_light 0.60` (no scaling) | Bajo (solo `stage1_1` `TMX` `ambient_light` property) |
| V02 | hall | `0-1280` `0-720` | `hall` `71` objetos `2.3%` `occupied` `24.6` `brightness` | `hall` `2.3%` extremadamente sparse, `1760×720` `0-480` camera `wall` vacío `70 Composition` | `V02 Layout` `V10 Intentional` | `metrics hall 2.3%` `STAGE_SPATIAL_INTEGRITY_MATRIX hall 1760` `71 objs` pero `occupied 2%` — decor `16×32` pequeña | `V10` no corregir — `hall` es lobby vacío intencional (transición) | Nulo |
| V03 | stage2_2 | `1920×800` `vertical 50` | `Camera 0-640×0-80` `80 px` `Y` scroll | `Y` scroll `80` correcto pero `player` `40×64` `8.9% H` en `800` deja `9%` `80` para anticipar vertical — `Navigation 88` | `V02 Layout` | `TMX 120×50 1920×800` `metrics 163 53 100%` `occupied 100%` por `bg` 1920×800 brillante | `V10` `800>720` vertical intencional — no corregir | Nulo |

**Clasificación V01-V10:** `V01 Asset` `V04` `stage1_1` `V02` `hall` `V10` `V03` `V10` — solo `V01` candidato `V04` contraste, `V02/V03` `V10` intencionales.

**Propuesta:** Solo `V01` con `evidence` `122.9` vs `31.8` → `TMX` `ambient_light` `0.60→0.55` `stage1_1` (1 línea `TMX` `properties`) — no `scaling`, no `renderer`.

**Riesgo:** Bajo — `ambient_light` es `float 0-1` `world` `light` no `display`.

**Total FINDINGS:** `3` (`1` `V04` `2` `V10`) — `0` `V01-V09` confirmados para corrección automática (solo `V01` manual `ambient_light` opcional).
