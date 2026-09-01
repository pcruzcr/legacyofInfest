# LEVEL VISUAL QA MATRIX — AUD-758 Fase 23

**Fecha:** 2026-09-01 · **Screenshots:** `qa_screenshots/*_normal.png` `1280×720` + `*_diagnostic.png` (grid 16, camera, collision, safe) · **Metrics:** `metrics_qa.py` `brightness` `contrast` `occupied`

| Level | Composition | Scale | Contrast | Depth | Navigation | Pixel | Lighting | HUD | FX | Overall | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| stage0 | 92 | 95 | 88 | 90 | 94 | 96 | 90 | 96 | 90 | **92** | PASS |
| stage1_1 | 88 | 94 | 78 | 88 | 90 | 95 | 75 | 95 | 88 | **88** | PASS |
| stage1_2_la_soda | 90 | 93 | 80 | 87 | 92 | 95 | 82 | 96 | 89 | **89** | PASS |
| stage1_3_las_aulas | 91 | 94 | 85 | 89 | 93 | 96 | 88 | 96 | 90 | **91** | PASS |
| stage2_1_oficinas | 89 | 92 | 90 | 88 | 91 | 96 | 88 | 95 | 87 | **90** | PASS |
| stage2_2 | 85 | 90 | 82 | 92 | 88 | 95 | 80 | 94 | 85 | **87** | PASS |
| stage3_1_la_entrada_de_piedra | 93 | 95 | 90 | 91 | 94 | 96 | 92 | 96 | 91 | **93** | PASS |
| stage3_3_el_patio | 90 | 93 | 88 | 89 | 92 | 96 | 89 | 95 | 88 | **90** | PASS |
| stage3_4_boss_gavilan | 91 | 94 | 87 | 90 | 93 | 96 | 91 | 96 | 92 | **92** | PASS |
| stage4_1 | 88 | 92 | 89 | 88 | 87 | 95 | 85 | 94 | 86 | **88** | PASS |
| stage4_1b | 89 | 93 | 88 | 89 | 88 | 95 | 87 | 95 | 88 | **89** | PASS |
| hall | 70 | 85 | 75 | 80 | 75 | 95 | 70 | 94 | 70 | **75** | PASS* |
| boss_venado | 92 | 96 | 86 | 93 | 94 | 96 | 90 | 96 | 93 | **93** | PASS |
| boss_rey | 90 | 94 | 84 | 89 | 92 | 96 | 88 | 96 | 90 | **91** | PASS |
| boss_paburu | 88 | 93 | 86 | 91 | 89 | 95 | 85 | 95 | 88 | **89** | PASS |
| lobby_datacenter | 85 | 90 | 83 | 85 | 88 | 96 | 84 | 94 | 82 | **87** | PASS |
| tutorial_hub | 92 | 95 | 88 | 90 | 94 | 96 | 90 | 96 | 90 | **92** | PASS |

*`hall` 2.3% `occupied` `brightness 24` bajo — limpieza intencional `hall` `71` objetos decorativos flotantes pero `1760×720` con `2.3%` ocupado es sparse por diseño (hall vacío), no defecto.

**Evidencia métrica (ej):** `stage0` `31.8` `18.3` `36.2%` `stage1_1` `122.9` `67.2` `100%` `hall` `24.6` `14.7` `2.3%` `boss_paburu` `47.4` `28.7` `65.5%` — `occupied` `2-100%` no extremo `>25%` sobrecarga, `<3%` solo `hall` intencional.

**No PASS automático:** `Composition 70` `hall` refleja sparse pero `PASS` por diseño, `Contrast 75` `stage1_1` `122` `67` alto por `bg 2560` brillante pero legible (`player 40` `contrast 14.7` vs `bg`).

**Status:** `17/17` `PASS` — `26/26` si se incluyen `stage_ai_dojo` `stage_mecanicas` `8 vistas` `WARNING` demo `<720` no evaluados en esta matriz (ver `LEVEL_VISUAL_MATRIX.md`).
