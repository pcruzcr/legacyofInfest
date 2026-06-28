# MASTER MODULES (v2 - Scope Adjusted)

## Modulo 1: Engine Core
Archivos: app.py, settings.py, clock.py, event_bus.py.
Dependencias: Ninguna.

## Modulo 2: Engine Input & Audio
Archivos: input_manager.py, action_map.py, audio_manager.py, sound_bank.py.
Dependencias: Module 1.

## Modulo 3: Engine Scene System
Archivos: scene_manager.py, base_scene.py, transitions.py.
Ademas: splash_scene.py, title_scene.py, story_scene.py (integrated in Phase 3).
Dependencias: Modules 1,2.

## Modulo 4: Engine UI
Archivos: hud.py, message_box.py, screen_banner.py.
Dependencias: Modules 1,3.

## Modulo 5: Framework Entities (Base & Player)
Archivos: base_entity.py, player.py.
Dependencias: Modules 1,2,4.

## Modulo 6: Enemy Templates
Archivos: enemy_base.py, enemy_walker.py, enemy_flying.py, enemy_shooter.py, projectile.py.
Dependencias: Module 5, Module 8 (CurveTools).

## Modulo 7: Stage System + StageRegistry
Archivos: stage_loader.py, stage_data.py, camera.py, checkpoint.py.
**NUEVO:** src/engine/core/stage_registry.py
StageRegistry: auto-descubre stages en src/stages/.
STAGE_ORDER fijo. Stages faltantes = skip.
14 slots: stage0, stage1_1..stage4_2_boss_paburu.
Dependencias: Modules 1,3,5,6.

## Modulo 8: Processing Core (ColorTools & CurveTools)
Archivos: color_tools.py, curve_tools.py.
Dependencias: Module 1 (math_utils).

## Modulo 9: Stage 0 (PEQUENO)
NO es 7 zonas. Es UNA stage corta (~80 tiles).
Propósito: probar que el motor funciona. NO demostracion academica avanzada.
Contenido: spawn, 1 walker, 1 checkpoint, 1 next_trigger, mensajes tutoriales.
Assets: profesor construye SOLO assets de Stage 0
Archivos: src/stages/stage0/stage0.py, stage0.tmx.
Dependencias: Todos los modulos 1-8.

## Modulo 10: FilterTools
Archivos: filter_tools.py.
Dependencias: Module 8.

## Modulo 11: VisionTools
Archivos: vision_tools.py.
Dependencias: Module 10.

## Modulo 12: PatternRecognitionTools
Archivos: pattern_recognition_tools.py.
Dependencias: Module 11.

## Modulo 13: Demo Scenes
Archivos: demo_menu_scene.py, filter_demo_scene.py, vision_demo_scene.py, pattern_demo_scene.py.
Dependencias: Modules 10,11,12.

## Modulo 14: Boss System
Archivos: boss_base.py + boss_venado.py (referencia).
Dependencias: Module 6, Module 10.

## Modulo 15: Student Templates
Archivos: stage_template/*, boss_template/*.
Dependencias: Todos (copia del estudiante).

## Modulo 16: Tooling
Archivos: validate_assets.py, build_dataset.py.
Dependencias: Modules 10,11,12.

## CAMBIOS vs v1
1. Modulo 7: StageRegistry NUEVO con auto-descubrimiento
2. Modulo 9: Stage 0 reducido (1 zona, no 7)
3. Splash/Title/Story integrados en Modulo 3
4. Profesor construye solo assets de Stage 0
5. 14 stage slots definidos
