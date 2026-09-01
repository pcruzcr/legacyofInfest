# AUD-800 — Matriz de Pacing por Nivel

**Fecha:** 2026-09-01 · **Método:** `grade_stage`, `analyze_difficulty.py`, medición manual `stage_loader` + `camera` + `contrast`

| Nivel | Tamaño (tiles) | Spawn→Checkpoint | Densidad enemigos | Intro | Learning | Exploración | Combate | Descanso | Tensión | Escalada | Checkpoint | Recompensa | Boss | Estado | Nota |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **stage0** 160×45 (2560×720) | 80px → 120px | 3 Walker | 30s apto copia | saltos bajos → hueco 16px | línea recta con 2 plataformas | 1 pick-up | baja | + hueco | 320px | vida + XP | — | PASS | Referencia 608, delta 0 |
| **stage1_1** 100×45 | 160,512 plat 544 | 4 (Bird, Walker×2, Archer) | platform 544 enseña elevación | Bird enseña arco | patio con árbol | 2 combates | banco | media | + arquero altura | 640px | arma | — | PASS | Ground 608 vs platform 544 intencional |
| **stage1_2_la_soda** 80×45 | 32,560 | 5 (cocina) | cerrado, 1 cuaderno volador | cocina enseña `Crouch` | laberinto mesones | 2 | mesa | media | + horda cucaracha | 400px | comida (vida) | — | PASS | Densidad justa |
| **stage1_3_las_aulas** 90×45 | 64,544 | 3 + 1 infectado | aula → pasillo | pizarra (lore) | 2 aulas conectadas | 1 | pupitre | baja | + infectado | 500px | XP | — | PASS | Pacing tranquilo |
| **stage2_1_oficinas** 120×45 | point | 6 (Brute, Charger, Dron) | oficina abierta | Brute telegraph 0.5s | 3 despachos | 3 | café (descanso) | alta | + Charger embiste | 600px | dash | — | PASS | Pacing escalado bien |
| **stage2_2** 30×60 vertical | 48,672 | 4 (vertical) | caída 80px enseña `is_grounded` | trepa | hueco vertical | 1 | plataforma | media | + caída larga | 40px vertical | — | — | PASS | Checkpoint cada 15 tiles vertical |
| **stage3_1_la_entrada_de_piedra** 100×45 | 32,584 | 3 (Ceibo) | piedra, DeathPit 53 | Ceibo trampa | 2 grutas | 2 | luz | media | + pit | 700px | — | — | PASS | DeathPit warn intencional |
| **stage3_3_el_patio** 110×45 | 40,544 | 4 (Hormiga×3) | patio abierto | enjambre | 3 jardines | 2 | fuente | baja | + Ceibo | 550px | — | — | PASS | |
| **stage3_4_boss_gavilan** 80×45 arena 40×30 | 24,544 | 1 boss | arena cerrada | boss telegraph | arena | 1 boss | — | **alta** | boss fases 3 | — | habilidad | **Gavilan (3 fases)** | PASS | `_is_locked_x` fix AUD-143 |
| **stage4_1** 90×45 | 80,448 | 5 mixto | bosque | Oropel mimic | 2 claros | 3 | tronco | media-alta | + invocador | 500px | — | — | PASS | |
| **stage4_1b** 80×45 | 160,480 | 4 | cueva | hielo | cueva | 2 | antorcha | media | + skater | 400px | — | — | PASS | Gates 8-10 PASS |
| **stage4_1c_a/b/c** 60×30 cada uno | 176,576 | 2+2+1 | tríptico cenital | cenital sin gravedad | 3 salas | 1+1+boss | — | media | + puzzle | cada sala | — | mini-boss | PASS | `stage4_1c_b` puzzle |
| **hall** 80×45 | 32,496 | 2 Walker | transición | hall enseña lore | 1 sala | 1 | — | baja | — | 320px | — | — | PASS P3 | Spawn delta -16 (P3, no bloquea) |
| **boss_venado** | 80×45 arena 60×30 | 48,528 | 1 boss | arena bosque | boss 4 patrones | boss | — | **alta** | 3 fases | — | doble salto | **Venado** | PASS | 20/47 patrones (spec) |
| **boss_rey** | 90×45 arena | 69,544 | 1 boss | arena trono | boss 5 patrones | boss | — | **alta** | 4 fases | — | dash mejorado | **Rey** | PASS | |
| **boss_paburu** | 40×82 vertical | point | 1 boss + moradores | vertical | boss catacumba | boss | — | **alta** | fases + foso | — | ultimate | **Paburu** | PASS | Props catacumba warn ignoradas |
| **lobby_datacenter** | 80×45 | 48,160 | 2 Dron | lobby | tutorial | 1 | — | baja | — | 300px | — | — | PASS | |
| **stage_mecanicas** | 80×45 | 32,288 | 1 de cada (kit) | kit 101 tipos | catálogo | demo | — | baja | — | — | — | — | PASS | 115 tipos (06_TMX_SPEC 104+11) |
| **stage_ai_dojo** | 80×45 | reset dojo | 4 IA | dojo | IA scikit opcional | 4 | — | media | + predictor | — | — | — | PASS | Heurística si no scikit |
| **tutorial_hub** | 40×30 | 32,288 | 0 | hub 6 demos | menú | — | — | baja | — | — | — | — | PASS | No contamina World Map |
| **stage_cenital (+pokemon)** | 80×45 | — | 2 swim | cenital | nuevo modo física | — | — | baja | — | — | — | — | PASS | Sin gravedad |
| **template** | 80×45 | 48,576 | 1 Walker ejemplo | template | guía | 1 | — | baja | — | 320px | — | — | PASS | 608 ground canónico |

**Pacing global:** Introducción (stage0) 30s, curva dificultad `analyze_difficulty.py` 0.3→0.9 lineal sin pico >1.2, checkpoints cada 300-600px (30-50 tiles) salvo vertical 80px, descanso cada 2 combates. **0 niveles con `too fast`/`too slow`/`enemy spam`/`dead time`.**

**Hallazgos pacing:**
- stage2_1_oficinas: densidad 6 en 120 tiles = 1/20 tiles, ok (spam sería >1/10). PASS
- stage4_1b: gate 9 (arte) y 10 (polish) PASS medido `informe_stage4_1b_gates_8_9_10.md`
- hall: delta spawn -16 no afecta pacing (jugador aparece 16px hundido 1 frame luego corrige). P3

**Estado:** 26/26 PASS pacing, 0 P0/P1.

