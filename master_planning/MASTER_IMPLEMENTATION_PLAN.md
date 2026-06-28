# MASTER IMPLEMENTATION PLAN (v3 - Full Scope Alignment)

**Version:** 3.0.0
**Fuente:** docs/33_SCOPE_ADJUSTMENT.md v2.0

## 1. PRIORIDADES (P1-P5)

### PRIORIDAD 1: Engine que corre (Phases 0-4)
Game loop, scene system, input, audio, UI - todo lo que hace que una ventana Pygame se abra.
Sin entidades aun.

Proof: Window opens, splash screen shows, title screen works, pressing Start begins story screens, story screens advance.

### PRIORIDAD 2: Player y Stage System (Phases 5-7)
Player entity, basic enemies, TMX loading, camera, checkpoints.

Proof: Stage 0 TMX loads, player appears (placeholder rect), camera follows, player reaches NextTrigger.

### PRIORIDAD 3: Stage 0 real assets (Phase 9 first pass)
Hooded character sprites, 1 walker enemy, basic stone tileset.

Proof: Stage 0 plays visually - real sprites, player animates, enemy patrols, HUD shows.

### PRIORIDAD 4: Processing pipeline (Phases 8, 10-12)
ColorTools, CurveTools, FilterTools, VisionTools, PatternRecognitionTools.

Proof: Demo scenes work. Students can call FilterTools.gaussian_blur() from their stage.

### PRIORIDAD 5: Boss framework (Phase 14)
BossBase + El Venado Sagrado reference implementation.

Proof: Students who selected a boss assignment can start their work.

## 2. FASES DETALLADAS

| Fase | Prioridad | Descripcion |
|---|---|---|
| 0: Scaffold | P1 | Directorios, requirements.txt, main.py, KNOWN_GAPS.md |
| 1: Engine Core | P1 | settings, clock, event_bus, app, Splash/Title/Story |
| 2: Input/Audio/Utils | P1 | math_utils, asset_loader, spritesheet, input_manager, audio_manager |
| 3: Scene System | P1 | scene_manager, base_scene, transitions (integra Splash/Title/Story) |
| 4: UI System | P1 | hud, message_box, screen_banner |
| 5: Player | P2 | base_entity, player (blue rect 20x32) |
| 6: Enemy Templates | P2 | enemy_base, walker(red), flying(orange), shooter(purple) |
| 7: Stage System | P2 | camera, checkpoint, stage_loader, stage_registry, Stage 0 minimal TMX |
| 8: Color/Curve Tools | P4 | color_tools, curve_tools |
| 9: Stage 0 Real Assets | P3 | Sprite sheets, tileset real, Stage 0 jugable con assets reales |
| 10: FilterTools | P4 | Filtros de imagen (histogram, blur, sobel, canny) |
| 11: VisionTools | P4 | Segmentacion (threshold, morphology, watershed) |
| 12: PatternRecognitionTools | P4 | ML (k-NN, tree, forest, SVM, train, predict) |
| 13: Demo Scenes | P4 | FilterDemo, VisionDemo, PatternDemo |
| 14: Boss System | P5 | BossBase, BossPhase, El Venado Sagrado reference |
| 15: Student Templates | P5 | stage_template, boss_template |
| 16: Regression + Tooling | P5 | validate_assets, build_dataset, KNOWN_GAPS audit |

## 3. REGLAS CRITICAS

1. App.run() frame order (11 pasos exactos del prompt)
2. Background (15,15,40) nunca negro
3. Camera offset en todo entity draw()
4. map_layer.center() + map_layer.draw() ambos requeridos
5. internal_surface escalada y blitteada a window_surface
6. Asset loading nunca crashea (fallback obligatorio)
7. StageRegistry descubre stages, skip si no existe
8. Visual gate obligatorio por fase
9. Commit: [SCOPE] type: description - T#.#
10. Student API Contract: StageScene(BaseScene) con STAGE_ID, STAGE_NAME, ZONE, TIME_LIMIT, BGM_TRACK
