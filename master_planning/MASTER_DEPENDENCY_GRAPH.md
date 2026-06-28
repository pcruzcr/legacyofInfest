# MASTER DEPENDENCY GRAPH (v2 - Scope Adjusted)

## 1. GRAFO COMPLETO
Layer 0: src/engine/core/ (app, clock, settings, event_bus, stage_registry)
Layer 1: src/engine/utils/ (math_utils, asset_loader, spritesheet)
Layer 2: src/engine/input/ + src/engine/audio/
Layer 3: src/engine/scene/ + src/engine/scenes/
Layer 4: src/engine/ui/
Layer 5: src/framework/entities/ (base_entity, player)
Layer 6: src/framework/entities/ (enemy_base, walker, flying, shooter)
Layer 7: src/framework/stage/ (stage_loader, camera, checkpoint)
Layer 8: src/framework/processing/ (color_tools, curve_tools)
Layer 9: src/framework/processing/ (filter_tools, vision_tools, pattern_recognition_tools)
Layer 10: src/stages/stage0/
Layer 11: src/engine/scenes/ (demo scenes)
Layer 12: src/framework/entities/ (boss_base)

StageRegistry esta en Layer 0 (engine/core/)
Es usado por SceneManager (Layer 3) para avanzar stages.

## 2. REGLAS
R1: Engine NO depende de Framework
R2: Framework depende de Engine
R3: Stages dependen de Engine + Framework
R4: Processing Tools NO dependen de Engine ni Stages
R5: StageRegistry descubre stages - usa STAGE_ORDER fijo
R6: Stages faltantes = skip silencioso
R7: Ningun ciclo

## 3. STAGE ORDER (14 stages)
stage0 -> stage1_1 -> stage1_2 -> stage1_3 -> stage1_4_boss_venado
-> stage2_1 -> stage2_2 -> stage2_3 -> stage2_4_boss_rey
-> stage3_1 -> stage3_2 -> stage3_3 -> stage3_4_boss_gavilan
-> stage4_1 -> stage4_2_boss_paburu

## 4. VERIFICACION AUSENCIA CICLOS
Engine -> Framework -> Stages: No
Engine -> StageRegistry -> SceneManager: No
StageRegistry -> os.listdir(src/stages/): No
Todos los caminos son DAG.
