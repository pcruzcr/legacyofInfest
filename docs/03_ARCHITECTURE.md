---
document_id: "LOI-ARCH-003"
title: "Legacy of InFest — Architecture"
aliases: ["Architecture", "Engine Architecture"]
tags: ["architecture", "engine", "structure"]
description: "Full folder structure, module responsibilities, data flow"
source: "docs/03_ARCHITECTURE.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Architecture

**Document ID:** LOI-ARCH-003
**Version:** 1.1.0
**Status:** Official
**Audience:** Professor, Teaching Assistants, AI coding assistants

---

## 1. Complete Folder Structure

**Corrected per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §2.A.6 and §7.** All paths below are relative to the actual private GitHub repository root. `engine/`, `framework/`, and `stages/` are relocated under `src/`; `student_templates/` is added. Every module, responsibility, and dependency rule documented elsewhere in this file is otherwise unchanged from the original design — only the path prefix changes.

```
legacy-of-infest/                      # Actual repo root
│
├── main.py                            # Entry point. Instantiates App and calls run().
│                                     # Supports --stage and --boss CLI args for direct launch.
├── requirements.txt
├── requirements.lock
├── README.md
├── README.en.md
├── LICENSE
├── pyproject.toml                     # Build config, dependencies, ruff/pytest/mypy settings
├── build.spec                         # PyInstaller build spec
├── build_nuitka.bat                   # Nuitka build script (Windows)
├── .flake8                            # Flake8 config (legacy, superseded by ruff)
├── .gitignore
├── .gitattributes
├── CHANGELOG.md
├── CONTRIBUTING.md
├── KNOWN_GAPS.md                      # Known gaps and their resolutions
├── PHASE_FIX_REPORT.md                # Stage 0 collision/spawn fixes
├── REMEDIATION_PLAN.md                # 8-phase remediation plan
│
├── docs/                              # Official documentation package (00–52+)
│
├── assets/                            # PROFESSOR-OWNED. Read-only for students.
│   ├── sprites/
│   │   ├── player/
│   │   ├── enemies/
│   │   ├── bosses/
│   │   └── shared/
│   ├── tilesets/
│   ├── backgrounds/
│   ├── music/
│   ├── sfx/
│   ├── fonts/
│   ├── ui/
│   ├── splash/
│   ├── title/
│   ├── story/
│   ├── maps/
│   ├── models/
│   ├── datasets/
│   ├── scripts/
│   └── tileset_stage0.tsx
│
├── src/                                # All Python source code
│   │
│   ├── engine/                         # PROFESSOR-OWNED. Do not modify.
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── app.py                     # App class: display init, main loop, scene pump
│   │   │   ├── settings.py                # All global constants
│   │   │   ├── clock.py                   # DeltaClock: delta time, FPS cap, time scale
│   │   │   ├── event_bus.py               # EventBus: pub/sub event dispatch
│   │   │   ├── events.py                  # Event name constants (Events class)
│   │   │   ├── game_context.py            # GameContext: DI container for all subsystems
│   │   │   ├── gpu_effects.py             # Reparto CPU/GPU del post-procesado (AUD-222)
│   │   │   ├── achievements.py            # Achievement system
│   │   │   ├── difficulty.py              # Difficulty scaling (Difficulty enum, set_difficulty)
│   │   │   ├── i18n.py                    # Internationalization (gettext wrapper)
│   │   │   ├── inventory.py               # Item/collectible management
│   │   │   ├── save_data.py               # SaveData dataclass, SAVE_VERSION, MAX_SLOTS
│   │   │   ├── score_system.py            # Points and coin drops per enemy type
│   │   │   ├── save_manager.py            # SaveManager: JSON-based save/load/delete
│   │   │   ├── stage_registry.py          # StageRegistry: auto-discover stages
│   │   │   └── user_settings.py           # UserSettings: persisted player preferences
│   │   │
│   │   ├── scene/
│   │   │   ├── __init__.py
│   │   │   ├── scene_manager.py           # SceneManager: push/pop/replace scene stack
│   │   │   └── base_scene.py              # BaseScene: abstract interface all scenes implement
│   │   │       # AUD-111: aquí vivía un módulo de transiciones con cinco
│   │   │       # clases y CERO usos en todo el repositorio, ni siquiera en
│   │   │       # pruebas. Competía con el gestor de transiciones de `scenes/`,
│   │   │       # que es el que SceneManager instancia de verdad, así que quien
│   │   │       # buscaba «cómo hago una transición» encontraba el muerto la
│   │   │       # mitad de las veces. Retirado.
│   │   │
│   │   ├── scenes/                        # All scene implementations (42+ files)
│   │   │   ├── __init__.py
│   │   │   ├── splash_scene.py            # Professor logo, auto-advance
│   │   │   ├── title_scene.py             # Main menu: Start / Academic Demos / Quit
│   │   │   ├── story_scene.py             # Story sequence (scenes 1–3)
│   │   │   ├── loading_scene.py           # Loading screen with progress indicator
│   │   │   ├── tutorial_scene.py          # Controls tutorial overlay
│   │   │   ├── tutorial_overlay.py        # Contextual help popups (engine-level)
│   │   │   ├── options_scene.py           # Options: volume, difficulty, colorblind mode
│   │   │   ├── keybinding_scene.py        # Rebind controls
│   │   │   ├── load_game_scene.py         # Save file selector
│   │   │   ├── game_over_scene.py         # Death screen with continue/quit
│   │   │   ├── end_credits_scene.py       # Credits / completion screen
│   │   │   ├── demo_menu_scene.py         # Academic Demos selector (10+ scenes)
│   │   │   ├── scene_registry.py          # DI Container: register → build pattern
│   │   │   ├── debug_overlay.py           # F3 debug console (FPS, events, modules)
│   │   │   ├── param_panel.py             # Reusable ParamPanel widget
│   │   │   ├── demo_layout.py             # Layout constants & draw helpers
│   │   │   ├── demo_utils.py              # SourceSurfaceManager, FrameThrottle, etc.
│   │   │   ├── demo_common.py             # Legacy re-exports from demo_layout + demo_utils
│   │   │   ├── filter_demo_scene.py       # Unit VII — Filter demo (9 modes)
│   │   │   ├── vision_demo_scene.py       # Unit VIII — Vision demo (10 modes)
│   │   │   ├── pattern_demo_scene.py      # Unit IX — Pattern demo (5 modes)
│   │   │   ├── vector_lab_scene.py        # Unit II — Vector lab
│   │   │   ├── transform_lab_scene.py     # Unit II/III — Transform lab
│   │   │   ├── curve_editor_scene.py      # Unit III — Curve editor
│   │   │   ├── interpolation_lab_scene.py # Unit III/IV — Interpolation lab
│   │   │   ├── color_theory_scene.py      # Unit V — Color theory lab
│   │   │   ├── noise_lab_scene.py         # Unit V/VIII — Noise lab
│   │   │   ├── collision_lab_scene.py     # Unit VI — Collision lab
│   │   │   ├── combo_demo_scene.py        # Combo system state machine demo
│   │   │   ├── inventory_scene.py         # Inventory screen (grid; equip/unequip)
│   │   │   ├── shop_scene.py              # Shop: buy/sell clothing with coins
│   │   │   ├── boss_rush_entry.py         # Boss rush entry point (two helper functions)
│   │   │   ├── achievement_scene.py       # Achievement screen (locked/unlocked)
│   │   │   ├── bestiary_scene.py          # Bestiary: enemy catalog
│   │   │   ├── world_map_scene.py         # World map (connected nodes)
│   │   │   ├── progress_scene.py          # Student progress dashboard (% per category)
│   │   │   ├── leaderboard_scene.py       # Local speedrun / boss rush leaderboards
│   │   │   ├── pipeline_builder_scene.py  # Visual filter chain builder (Unit VII/VIII)
│   │   │   ├── quiz_system.py             # Quiz overlay for academic labs
│   │   │   ├── code_panel.py              # Code display panel for teaching
│   │   │   ├── sandbox_scene.py           # Sandbox for testing mechanics
│   │   │   ├── stage_error_scene.py       # Error screen for stage load failures
│   │   │   ├── stage_wizard_scene.py      # Stage creation wizard
│   │   │   ├── transition_manager.py      # Manages screen transitions (fade/wipe/slide/circle)
│   │   │   ├── unit_theory_scene.py       # Teoria y examen de una unidad (AUD-095)
│   │   │   └── student_login_scene.py     # Identificacion por correo (AUD-098)
│   │   │
│   │   ├── input/
│   │   │   ├── __init__.py
│   │   │   ├── input_manager.py           # InputManager: unified keyboard + controller
│   │   │   └── action_map.py              # ActionMap: abstract action → device binding
│   │   │
│   │   ├── audio/
│   │   │   ├── __init__.py
│   │   │   ├── sound_bank.py              # SoundBank: named sound registry
│   │   │   ├── audio_manager.py           # AudioManager: music + sfx + ambient + stingers
│   │   │   ├── audio_pipeline.py          # Audio processing pipeline
│   │   │   ├── music_clock.py            # RelojMusical: pulsos, compases y latencia (F6)
│   │   │   └── mixer_buses.py           # Mezclador: buses y ducking (AUD-144)
│   │   │
│   │   ├── render/
│   │   │   ├── __init__.py
│   │   │   ├── gl_pipeline.py             # GLRenderer, GLRenderConfig: ModernGL pipeline
│   │   │   ├── shaders.py                 # GLSL shader sources
│   │   │   └── gpu_present.py            # PresentadorGPU: presentar por SDL2 (AUD-148, opcional)
│   │   │
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── hud.py                     # HUD: hearts, timer, portrait, score
│   │   │   ├── message_box.py             # MessageBox: scrolling text, tutorial messages
│   │   │   ├── screen_banner.py           # ScreenBanner: stage title animation
│   │   │   ├── minimap.py                 # Minimap: fog-of-war exploration map
│   │   │   ├── subtitle_overlay.py        # SubtitleOverlay: dialogue subtitles
│   │   │   ├── theme.py                   # Theme: UI color scheme and styling
│   │   │   └── widgets.py                 # Reusable UI widgets
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── asset_loader.py            # AssetLoader: load+cache images, sounds, fonts
│   │       ├── math_utils.py              # Vector2, lerp, clamp, ease functions
│   │       ├── surface_pool.py            # SurfacePool: reuse temporary surfaces
│   │       └── sprite_atlas.py            # SpriteAtlas: muchos recortes en una hoja (G1)
│   │
│   ├── framework/                      # PROFESSOR-OWNED. Do not modify.
│   │   │
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── base_entity.py             # BaseEntity: position, rect, update, draw lifecycle
│   │   │   ├── player.py                  # Player: state machine, input response, damage
│   │   │   ├── player_state.py            # PlayerState enum (all player states)
│   │   │   ├── player_states.py           # Player state machine implementation
│   │   │   ├── states/                    # Individual state classes (subdirectory)
│   │   │   ├── enemy_base.py              # EnemyBase: abstract enemy with health + state
│   │   │   ├── enemy_walker.py            # EnemyWalker: horizontal patrol, player detection
│   │   │   ├── enemy_flying.py            # EnemyFlying: sine-wave or waypoint flight
│   │   │   ├── enemy_shooter.py           # EnemyShooter: projectile emission, range trigger
│   │   │   ├── boss_base.py               # BossBase: phase manager, boss health bar event
│   │   │   ├── boss_kit.py                # BossKit: reusable boss components
│   │   │   ├── enemy_charger.py           # EnemyCharger: wind-up + charge attack
│   │   │   ├── enemy_archer.py            # EnemyArcher: ranged with arc shot
│   │   │   ├── enemy_brute.py             # EnemyBrute: heavy melee + ground slam
│   │   │   ├── enemy_caster.py            # EnemyCaster: homing orb magic
│   │   │   ├── enemy_assassin.py          # EnemyAssassin: cloak + lunge
│   │   │   ├── entity_factory.py          # EntityFactory: registry-based enemy creation
│   │   │   ├── flight_strategies.py       # FlightStrategy: sine/bezier/random flight patterns
│   │   │   ├── ai_predictor.py            # AIPredictor: ML-based player action prediction
│   │   │   ├── bestiary.py                # Bestiary: enemy encounter/kill tracking
│   │   │   ├── bestiary_registry.py       # BestiaryRegistry: enemy data registry
│   │   │   ├── ranged_weapon.py           # ArcoDelJugador: arco del jugador, munición y flechas (F4.2)
│   │   │   └── squad_brain.py             # SquadBrain: group enemy coordination AI
│   │   │
│   │   ├── ecs/                            # F5 — entidades, componentes y sistemas
│   │   │   ├── __init__.py                 #   Va DEBAJO de la jerarquía, no en su lugar:
│   │   │   ├── world.py                    #   World: almacén de componentes y entidades
│   │   │   ├── components.py               #   Los datos, sin comportamiento
│   │   │   ├── systems.py                  #   Viento, plataformas, láseres, sigilo
│   │   │   ├── scheduler.py                #   Planificador: el orden de un fotograma
│   │   │   ├── bridge.py                   #   ComponentesDeEntidad: BaseEntity sobre componentes
│   │   │   └── bullet_swarm.py             #   EnjambreDeBalas: bullet hell con NumPy (F5.8)
│   │   │
│   │   ├── stage/
│   │   │   ├── __init__.py
│   │   │   ├── stage_loader.py            # StageLoader: parse TMX, build layer stack, spawn
│   │   │   ├── interactables.py           # Recogible/Cerradura/Cofre/Disparador/Llavero (F4.1)
│   │   │   ├── bloques.py                 # PushBlock y BreakableBlock: empujar y romper (AUD-140)
│   │   │   ├── interactable_system.py     # InteractableSystem: llaves, puertas, cofres y eventos (F4.1)
│   │   │   ├── level_mechanics.py         # ControlDeNado, TiempoBala, ScrollForzado (F5.5/F5.6)
│   │   │   ├── camera.py                  # Camera: viewport, parallax, follow target
│   │   │   ├── checkpoint.py              # Checkpoint: trigger zone, respawn anchor
│   │   │   ├── collision_system.py        # CollisionSystem: hitstop, attack processing
│   │   │   ├── hazard_system.py           # HazardSystem: damage zones, death pits
│   │   │   ├── progression_system.py      # ProgressionSystem: stage completion, triggers
│   │   │   ├── drawing_system.py          # DrawingSystem: layered rendering pipeline
│   │   │   ├── cutscene_system.py         # CutsceneSystem: scripted cutscenes
│   │   │   ├── cutscene_director.py       # CutsceneDirector: escenas declaradas en TMX (AUD-136)
│   │   │   ├── cutscene_guion.py          # analizar_guion: texto de guion a acciones (AUD-136)
│   │   │   ├── speedrun_mode.py           # SpeedrunTimer: global timer + ghost data
│   │   │   ├── boss_rush_mode.py          # BossRushMode: consecutive boss gauntlet
│   │   │   ├── day_night.py               # DayNight: day/night cycle system
│   │   │   ├── level_metrics.py           # LevelMetrics: stage analysis metrics
│   │   │   ├── seasons.py                 # Seasons: seasonal visual effects
│   │   │   └── tmx_diagnostics.py         # TmxDiagnostics: TMX validation utilities
│   │   │
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── tutorial_overlay.py        # TutorialOverlay: contextual help popups
│   │   │   ├── dialogue_system.py         # DialogueSystem: branching dialogue with portraits
│   │   │   └── learning_overlay.py        # LearningOverlay: academic context overlay
│   │   │
│   │   ├── audio/
│   │   │   ├── __init__.py
│   │   │   └── dynamic_music.py           # DynamicMusic: cross-fade calm <-> combat
│   │   │
│   │   ├── academic/
│   │   │   ├── __init__.py
│   │   │   ├── curriculum.py              # PLAN: las unidades, su teoria y su examen
│   │   │   ├── progress.py                # ProgresoAcademico: notas y desbloqueo encadenado
│   │   │   └── sesion.py                  # SesionAcademica: estudiante activo
│   │   │
│   │   ├── scenes/
│   │   │   ├── __init__.py
│   │   │   ├── stage_scene.py             # StageScene: main gameplay scene
│   │   │   └── stage_parts/               # AUD-152: mixins de lectura de StageScene
│   │   │       ├── __init__.py            #   por qué son mixins y no colaboradores
│   │   │       ├── ambiente.py            #   luz, bloom, viñeta, estación, hora
│   │   │       ├── senales.py             #   suscripciones al bus: VFX y 38 sonidos
│   │   │       └── fantasma.py            #   silueta de la mejor carrera
│   │   │
│   │   ├── vfx/
│   │   │   ├── __init__.py
│   │   │   ├── particle_system.py         # ParticleSystem: emitters, bursts
│   │   │   ├── hit_effects.py             # HitEffects: burst configs per hit type
│   │   │   ├── damage_numbers.py          # DamageNumberManager: floating damage text
│   │   │   ├── post_processing.py         # PostProcessing: bloom, vignette, motion blur
│   │   │   ├── lighting.py                # LightSystem: 2D dynamic lighting
│   │   │   ├── ambient_particles.py       # AmbientParticleSystem: dust, leaves, embers
│   │   │   ├── trail_system.py            # TrailSystem: motion trails
│   │   │   ├── fog_of_war.py              # FogOfWar: black overlay with revealed holes
│   │   │   ├── water_effect.py            # WaterEffect: animated sine wave overlay
│   │   │   └── weather_system.py          # WeatherSystem: rain, snow, fog effects
│   │   │
│   │   ├── processing/
│   │   │   ├── __init__.py
│   │   │   ├── color_tools.py             # ColorTools: RGB↔HSV↔HSL↔CMYK, alpha blend
│   │   │   ├── filter_tools.py            # FilterTools: convolution, blur, Sobel, Canny
│   │   │   ├── curve_tools.py             # CurveTools: Bézier, B-Spline, NURBS, sample
│   │   │   ├── vision_tools.py            # VisionTools: threshold, morphology, features
│   │   │   ├── edge_detection.py          # EdgeDetection: additional edge detection methods
│   │   │   ├── pattern_recognition_tools.py  # PatternRecognitionTools: training, inference
│   │   │   └── reference_model.py         # ReferenceModel: reference ML model
│   │   │
│   │   ├── academic/
│   │   │   ├── __init__.py
│   │   │   ├── curriculum.py              # Curriculum: syllabus unit definitions
│   │   │   ├── progress.py                # Progress: student progress tracking
│   │   │   └── sesion.py                  # Sesion: class session management
│   │   │
│   │   └── ai/
│   │       ├── __init__.py
│   │       └── lua_script.py              # LuaScript: Lua scripting for enemy AI
│   │
│   └── stages/
│       ├── stage0/                        # PROFESSOR-OWNED. Executable documentation.
│       │   ├── __init__.py
│       │   ├── stage0.py                  # Stage0Scene class
│       │   ├── stage0.tmx                 # Tiled map
│       │   └── README.md
│       ├── boss_venado/                   # PROFESSOR-OWNED. Boss Venado implementation.
│       │   ├── __init__.py
│       │   ├── boss_venado.py
│       │   └── boss_venado_scene.py
│       └── <student_assignment>/          # ONE folder per individually-assigned Stage/Boss
│           ├── __init__.py
│           ├── <assignment>.py
│           ├── <assignment>.tmx           # (Stages only — Bosses use a fixed arena, no TMX scroll)
│           └── README.md
│
├── scripts/                            # Tooling scripts
│   ├── _cli_paths.py                   # Shared path utilities for CLI scripts
│   ├── audit_docs_vs_code.py           # Audits doc identifiers vs actual code (regenerates docs/63)
│   ├── build_executable.py             # Build executable from source
│   ├── check_dependency_sync.py        # Verify dependency consistency
│   ├── check_tmx_coverage.py           # Check TMX map coverage
│   ├── check_translations.py           # Verify translation completeness
│   ├── collect_palettes.py             # Collect palette data from assets
│   ├── downloader.py                   # Asset downloader utility
│   ├── feedback_generator.py           # Generate student feedback reports
│   ├── generate_exam.py                # Generates practice exams from question bank
│   ├── generate_tmx_reference.py       # Generate TMX reference documentation
│   ├── grade_boss.py                   # Auto-grades student boss Python files
│   ├── grade_exporter.py               # Export grades to external format
│   ├── grade_stage.py                  # Auto-grades student stage TMX files
│   ├── obsidianize.py                  # Convert docs to Obsidian format
│   ├── plagiarism_detector.py          # Plagiarism detection for student work
│   ├── preview_tmx.py                  # Preview TMX maps in terminal
│   ├── project_stats.py                # Generate project statistics
│   ├── train_reference_model.py        # Train reference ML model
│   ├── validate_assets.py              # Validates fonts, models, maps
│   └── validate_tmx.py                 # Validates TMX map files for common errors
│
├── colab/                              # Google Colab notebooks for interactive exercises
│   ├── 01_vector_math_exercises.ipynb  # Unit II — Vector mathematics exercises
│   ├── 02_color_spaces_exercises.ipynb # Unit V — Color space conversion exercises
│   └── 03_filter_kernels_exercises.ipynb# Unit VII — Convolution kernel exercises
│
├── student_templates/                  # Canonical starter scaffold (copied into src/stages/ by each student)
│   ├── __init__.py
│   ├── stage_template/
│   │   ├── stage_template.py
│   │   ├── stage_template.tmx
│   │   └── README_template.md
│   └── boss_template/
│       ├── boss_template.py
│       └── README_template.md
│
├── locale/                             # Localization files
│   ├── en.json                         # English translations
│   └── es.json                         # Spanish translations
│
├── fonts/                              # Bundled font files
│
├── tools/                              # Developer tooling (not imported by game)
│
├── web/                                # Web dashboard (if applicable)
│
├── exams/                              # Generated exam files
│
├── PHASE_FIX_REPORT.md                 # Stage 0 collision/spawn fixes
├── KNOWN_GAPS.md                       # Known gaps and their resolutions
├── REMEDIATION_PLAN.md                 # 8-phase remediation plan
│
└── tests/                              # Unit and integration tests (41+ files, 5,251+ LOC)
    ├── __init__.py
    ├── conftest.py
    ├── strategies.py                   # Hypothesis strategies for property-based testing
    ├── test_academic_units.py
    ├── test_accessibility.py
    ├── test_ambience.py
    ├── test_asset_loader.py
    ├── test_audio_wiring.py
    ├── test_audit_regressions.py
    ├── test_benchmarks.py
    ├── test_bestiary_roster.py
    ├── test_boss_base.py
    ├── test_boss_encounter.py
    ├── test_camera.py
    ├── test_checkpoint.py
    ├── test_clock.py
    ├── test_collision_edge_detect.py
    ├── test_color_tools.py
    ├── test_combo_system.py
    ├── test_curve_tools.py
    ├── test_day_night.py
    ├── test_demo_centering.py
    ├── test_demo_scenes.py
    ├── test_edge_detection.py
    ├── test_enemy_flying.py
    ├── test_enemy_shooter.py
    ├── test_enemy_state_machine.py
    ├── test_enemy_walker.py
    ├── test_event_bus.py
    ├── test_event_integration.py
    ├── test_filter_demo_perf.py
    ├── test_filter_tools.py
    ├── test_floor_x_skip.py
    ├── test_frame_budget.py
    ├── test_gameplay_integration.py
    ├── test_hud.py
    ├── test_i18n.py
    ├── test_input_injection.py
    ├── test_input_manager.py
    ├── test_level_design_qa.py
    ├── test_lighting.py
    ├── test_math_utils.py
    ├── test_menu_navigation.py
    ├── test_message_box.py
    ├── test_new_pipeline_modules.py
    ├── test_noise_lab.py
    ├── test_orphan_systems.py
    ├── test_particle_systems.py
    ├── test_pattern_demo.py
    ├── test_pattern_recognition_tools.py
    ├── test_player_damage.py
    ├── test_player_hurtbox.py
    ├── test_player_physics.py
    ├── test_player_state_machine.py
    ├── test_player_states_extended.py
    ├── test_post_processing.py
    ├── test_reported_ui_bugs.py
    ├── test_save_manager.py
    ├── test_scene_manager.py
    ├── test_scene_registry_integrity.py
    ├── test_scene_smoke.py
    ├── test_seasons.py
    ├── test_spawn_no_pop.py
    ├── test_squad_brain.py
    ├── test_stage_loader.py
    ├── test_stage0_platform_solidity.py
    ├── test_stage0_smoke.py
    ├── test_student_guidance.py
    ├── test_student_template.py
    ├── test_teaching_tools.py
    ├── test_tmx_diagnostics.py
    ├── test_tmx_validator.py
    ├── test_toolchain_consistency.py
    ├── test_trails.py
    ├── test_ui_consistency.py
    ├── test_vision_tools.py
    ├── test_visual_regression.py
    ├── benchmarks/
    │   ├── __init__.py
    │   ├── baseline_v1.json
    │   ├── test_memory_benchmark.py
    │   ├── test_performance_budget.py
    │   ├── test_physics_benchmark.py
    │   ├── test_render_benchmark.py
    │   └── test_startup_benchmark.py
    ├── fixtures/
    │   ├── __init__.py
    │   └── minimal_stage.tmx
    ├── output/
    │   ├── demo/
    │   ├── filter/
    │   └── vision/
    └── playtest/
        ├── __init__.py
        └── bot.py
```

**Clarification on individual assignment (per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §2.A.1):** Each student is assigned exactly one Stage or Boss in Class 1 (see `21_COURSE_SCHEDULE.md`). They copy the appropriate template from `student_templates/` into a new folder under `src/stages/` named for their assignment (e.g., `src/stages/stage1_2_la_soda/` or `src/stages/boss_venado/`). They develop that single folder through all three Evaluación Práctica checkpoints. No student creates more than one assignment folder.

## 2. Module Responsibilities

### 2.1 Engine Core

#### `engine/core/app.py` — `App`

The root application class. It owns the Pygame display surface, the `DeltaClock`, the `SceneManager`, the `InputManager`, and the `AudioManager`. It runs the main loop, pumps events into the `InputManager` and `EventBus`, calls `update()` and `draw()` on the active scene, and handles display scaling from internal resolution to window resolution. The UI layout uses a responsive system based on percentage calculations rather than fixed pixel coordinates, ensuring consistent proportions across display scales.

**Public Interface:**
- `App()` — Initialize Pygame, create internal surface at settings.INTERNAL_WIDTH×settings.INTERNAL_HEIGHT, create all engine singletons
- `App.run()` — Enter the main loop. Does not return until the application exits.

**Constraints:**
- Only one `App` instance may exist.
- `App` is instantiated in `main.py` only.
- No other module calls `pygame.init()` or `pygame.display.set_mode()`.

#### `engine/core/settings.py` — Constants

A flat module of uppercase constants. No classes, no functions.

| Constant | Type | Value | Description |
|---|---|---|---|
| `INTERNAL_WIDTH` | int | 800 | Internal render width in pixels |
| `INTERNAL_HEIGHT` | int | 600 | Internal render height in pixels |
| `TARGET_FPS` | int | 60 | Target frames per second |
| `DISPLAY_SCALE` | int | 1 | Default window scale multiplier — set to 2-4 on high-DPI displays |
| `TILE_SIZE` | int | 16 | Standard tile size in pixels |
| `ASSETS_DIR` | Path | `Path("assets")` | Root asset directory |
| `STAGES_DIR` | Path | `Path("src/stages")` | Root stages directory |
| `STUDENT_TEMPLATES_DIR` | Path | `Path("student_templates")` | Student templates directory |
| `PLAYER_MAX_HEALTH` | float | 5.0 | Maximum player hearts |
| `GRAVITY` | float | 800.0 | Pixels per second squared |
| `PLAYER_WALK_SPEED` | float | 90.0 | Pixels per second |
| `PLAYER_JUMP_FORCE` | float | -380.0 | Initial vertical jump velocity |

#### `engine/core/clock.py` — `DeltaClock`

Wraps `pygame.time.Clock`. Provides delta time in seconds, accumulated time, a time scale multiplier (for slow-motion effects), and an FPS accessor.

**Public Interface:**
- `DeltaClock.tick() → float` — Tick the clock. Returns delta time in seconds, scaled by `time_scale`.
- `DeltaClock.fps → float` — Current frames per second.
- `DeltaClock.time_scale: float` — Multiplier. 1.0 is normal. 0.5 is half speed.

#### `engine/core/event_bus.py` — `EventBus`

An instance-based pub/sub event dispatcher. Entities and systems communicate through the event bus rather than holding direct references to each other. Module-level convenience functions (`emit`, `subscribe`, `unsubscribe`) delegate to a default module-level instance for ergonomic single-instance usage.

**Public Interface:**
- `EventBus.subscribe(event_name: str, callback: Callable)` — Register a listener.
- `EventBus.unsubscribe(event_name: str, callback: Callable)` — Remove a listener.
- `EventBus.emit(event_name: str, **data)` — Dispatch an event to all registered listeners.

**Standard Events:**

| Event Name | Data Keys | Emitted By | Consumed By |
|---|---|---|---|
| `PLAYER_DAMAGED` | `amount`, `source` | Player | HUD, AudioManager |
| `PLAYER_DIED` | — | Player | SceneManager |
| `PLAYER_HEALED` | `amount` | Checkpoint | Player, HUD |
| `CHECKPOINT_REACHED` | `checkpoint_id` | Checkpoint | StageLoader |
| `ENEMY_DIED` | `entity_id`, `position` | EnemyBase | Stage, AudioManager |
| `STAGE_COMPLETE` | — | NextTrigger | SceneManager |
| `BOSS_PHASE_CHANGED` | `phase` | BossBase | Stage, HUD |
| `SHOW_MESSAGE` | `text`, `duration` | Stage | MessageBox |
| `HIDE_MESSAGE` | — | Stage | MessageBox |

---

### 2.2 Engine Scene

#### `engine/scene/scene_manager.py` — `SceneManager`

Manages a stack of `BaseScene` objects. Supports push (overlay a scene), pop (return to previous), and replace (transition to new scene). Only the top scene receives `update()` and `draw()` calls.

**Public Interface:**
- `SceneManager.push(scene: BaseScene)` — Push a scene onto the stack.
- `SceneManager.pop()` — Pop the top scene. Resumes the scene below.
- `SceneManager.replace(scene: BaseScene)` — Replace the top scene with a new one.
- `SceneManager.current → BaseScene` — The currently active scene.

#### `engine/scene/base_scene.py` — `BaseScene`

Abstract base class for all scenes (splash, title, story screens, stages). Constructor receives the `GameContext` dependency injection container.

```python
class BaseScene:
    def __init__(self, context: GameContext) -> None: ...
```

**Lifecycle Methods (called by SceneManager in this order):**
- `awake()` — Called once when the scene is first instantiated (before `on_enter`).
- `start()` — Called once on the first `update()` after `on_enter`.
- `on_enter()` — Called when the scene becomes active.
- `on_exit()` — Called when the scene is deactivated or removed.
- `update(dt: float)` — Update scene state. `dt` is delta time in seconds.
- `draw(surface: pygame.Surface)` — Draw the scene to the provided surface.
- `on_pause()` — Called when another scene is pushed on top.
- `on_resume()` — Called when the scene is resumed after a pop.

---

### 2.3 Engine Input

#### `engine/input/input_manager.py` — `InputManager`

Unified input abstraction. Handles keyboard and gamepad input through the `ActionMap`. Entities query actions, not raw keys or buttons.

**Public Interface:**
- `InputManager.is_action_pressed(action: str) → bool` — True on the frame the action was activated.
- `InputManager.is_action_held(action: str) → bool` — True while the action is held.
- `InputManager.is_action_released(action: str) → bool` — True on the frame the action was released.
- `InputManager.pump(events: list)` — Called once per frame by `App` with the current event list.

**Standard Actions:**

| Action | Default Keyboard | Default Controller |
|---|---|---|
| `MOVE_LEFT` | Left Arrow / A | D-Pad Left / Left Stick Left |
| `MOVE_RIGHT` | Right Arrow / D | D-Pad Right / Left Stick Right |
| `JUMP` | Space / Up / W | A (Xbox) / Cross (PS) |
| `CROUCH` | Down / S | D-Pad Down / Left Stick Down |
| `SHORT_ATTACK` | Z / J | X (Xbox) / Square (PS) |
| `LONG_ATTACK` | X / K | Y (Xbox) / Triangle (PS) |
| `PAUSE` | Escape / P | Start |
| `CONFIRM` | Enter / Z | A (Xbox) |
| `CANCEL` | Backspace / X | B (Xbox) |

---

### 2.4 Engine Audio

#### `engine/audio/audio_manager.py` — `AudioManager`

Wraps `pygame.mixer`. Manages music playback (one track at a time) and SFX playback (multiple simultaneous channels). Volume control is applied globally.

**Public Interface:**
- `AudioManager.play_music(path: str | Path, loops: int = -1)` — Play named BGM track.
- `AudioManager.stop_music()` — Stop BGM.
- `AudioManager.play_sfx(name: str, volume: float = 1.0)` — Play named sound effect.
- `AudioManager.set_music_volume(volume: float)` — Set music volume 0.0–1.0.
- `AudioManager.set_sfx_volume(volume: float)` — Set SFX volume 0.0–1.0.

---

### 2.5 Engine UI

#### `engine/ui/hud.py` — `HUD`

Renders the player HUD: portrait, heart meter, timer, and score. The HUD is drawn on top of all stage content on every frame. It subscribes to `PLAYER_DAMAGED`, `PLAYER_HEALED`, and `PLAYER_DIED` events to update the heart display.

**Public Interface:**
- `HUD.update(dt: float)` — Animate timer, flash states.
- `HUD.draw(surface: pygame.Surface)` — Blit HUD elements onto the surface.
- `HUD.start_timer(seconds: int)` — Initialize and start the countdown timer.
- `HUD.pause_timer()` / `HUD.resume_timer()` — Pause/resume the timer.

See `09_HUD_SPEC.md` for full layout specification.

#### `engine/ui/message_box.py` — `MessageBox`

Displays tutorial messages at the bottom of the screen. Subscribes to `SHOW_MESSAGE` and `HIDE_MESSAGE` events. Supports scrolling text reveal and auto-dismiss after a configurable duration.

#### `engine/ui/screen_banner.py` — `ScreenBanner`

Animates the stage entry banner. A two-part banner slides in from both sides of the screen, displays the stage name and number, holds for a beat, then slides out. Triggered at stage start.

---

### 2.6 Engine Utils

#### `engine/utils/asset_loader.py` — `AssetLoader`

Centralizes asset loading. Maintains an in-memory cache keyed by path string. Supports images, sounds, and fonts.

**Public Interface:**
- `AssetLoader.load_image(path: str | Path) → pygame.Surface` — Load and cache a PNG image.
- `AssetLoader.load_sound(path: str | Path) → pygame.mixer.Sound` — Load and cache audio.
- `AssetLoader.load_font(path: str | Path, size: int) → pygame.font.Font` — Load and cache a TTF font.
- `AssetLoader.load_sprite_sheet(path: str | Path, frame_width: int, frame_height: int) → list[pygame.Surface]`
  — Slice a horizontal sheet into frames. This is the **only** sprite-sheet
  path in the engine: `enemy_base`, `boss_base` and `player` all go through it.

> **AUD-098 — qué decía esta sección antes.**
> Documentaba `AssetLoader.load_spritesheet` (sin guion bajo) devolviendo un
> objeto `SpriteSheet`, y una clase `engine/utils/spritesheet.py` con
> `get_frame(index)`, `get_frames(start, end)` y `frame_count`.
>
> Nada de eso existía. El método real se llama `load_sprite_sheet` y devuelve
> una lista de superficies; la clase `SpriteSheet` sí estaba en el árbol, pero
> **nadie la importaba** y su `get_frame` tomaba `(x, y, width, height)`, no un
> índice. Era una segunda implementación del mismo concepto, muerta, con una
> API distinta de la documentada y de la real a la vez.
>
> Lo mismo con `engine/ui/bitmap_font.py`: un renderizador de texto por mapa
> de bits que nadie usaba, en un proyecto donde los 115 puntos de dibujado de
> texto pasan por `AssetLoader.load_font`.
>
> Los dos módulos se han retirado. En un motor que existe para que alguien lo
> lea, una implementación paralela sin usar no es código de reserva: es una
> trampa para el estudiante que la encuentra primero.

#### `engine/utils/math_utils.py` — Math Utilities

A collection of pure functions for common mathematical operations used throughout the framework.

| Function | Signature | Description |
|---|---|---|
| `lerp` | `(a, b, t) → float` | Linear interpolation |
| `clamp` | `(value, min_v, max_v) → float` | Clamp value to range |
| `ease_in_quad` | `(t) → float` | Quadratic ease-in |
| `ease_out_quad` | `(t) → float` | Quadratic ease-out |
| `vec2_normalize` | `(v: tuple) → tuple` | Normalize a 2D vector |
| `vec2_length` | `(v: tuple) → float` | Length of a 2D vector |
| `vec2_dot` | `(a, b: tuple) → float` | Dot product of two 2D vectors |
| `vec2_distance` | `(a, b: tuple) → float` | Distance between two points |

---

### 2.7 Framework Entities

#### `framework/entities/base_entity.py` — `BaseEntity`

Root class for all game objects. Manages world position, a Pygame `Rect` for collision, visibility, active state, and the basic `update` / `draw` lifecycle.

**Properties:**
- `position: pygame.Vector2` — World-space position (top-left of bounding rect)
- `rect: pygame.Rect` — Collision and render bounding rectangle
- `is_active: bool` — Whether the entity participates in updates
- `is_visible: bool` — Whether the entity participates in drawing
- `layer: int` — Draw order layer

**Required Override:**
- `update(dt: float)` — Update entity state
- `draw(surface: pygame.Surface, camera_offset: pygame.Vector2)` — Draw the entity

#### `framework/entities/player.py` — `Player`

See `04_PLAYER_SPEC.md` for the complete specification.

#### `framework/entities/enemy_base.py` — `EnemyBase`

See `05_ENEMY_SPEC.md` for the complete specification.

---

### 2.8 Framework Stage

#### `framework/stage/stage_loader.py` — `StageLoader`

Parses a TMX file using `pytmx`, constructs the layer stack using `pyscroll`, spawns entities from object layers, registers checkpoints, and returns a fully assembled stage scene state.

**Public Interface:**
- `StageLoader.load(tmx_path: Path) → StageData` — Load a TMX file and return the stage data structure.

**`StageData` Contents (17 fields — see `src/framework/stage/stage_loader.py` for the exact `@dataclass`):**
- `map_layer` — The `pyscroll` scrolling group
- `map_pixel_size: tuple[int, int]` — Total map dimensions in pixels
- `collision_rects: list[pygame.Rect]` — All solid collision rectangles
- `one_way_rects: list[pygame.Rect]` — One-way platform collision rectangles
- `entity_list: list[BaseEntity]` — All spawned entities
- `checkpoints: list[Checkpoint]` — All checkpoint objects
- `spawn_point: pygame.Vector2` — Player start position
- `next_trigger: pygame.Rect | None` — Stage completion trigger zone
- `background_layers: list[pygame.Surface]` — Parallax background layers
- `message_triggers: list[MessageTrigger]` — Message trigger zones
- `hazard_zones: list[HazardZone]` — Hazard zones
- `death_pits: list[DeathPit]` — Death pit rects
- `camera_locks: list[CameraLock]` — Camera lock zones
- `stage_id: str` — Unique stage identifier
- `stage_name: str` — Display name
- `time_limit: int` — Countdown time in seconds (0 = no limit)
- `bgm_track: str` — Background music track name

#### `framework/stage/camera.py` — `Camera`

Manages the viewport offset. Follows the player entity smoothly using configurable lerp speed. Supports parallax factor per background layer. Clamps the viewport to the map bounds.

**Public Interface:**
- `Camera.follow(target: BaseEntity)` — Set the entity the camera follows.
- `Camera.update(dt: float)` — Smooth the camera position.
- `Camera.world_to_screen(pos: pygame.Vector2) → pygame.Vector2` — Convert world to screen coordinates.
- `Camera.screen_to_world(pos: pygame.Vector2) → pygame.Vector2` — Convert screen to world coordinates.
- `Camera.offset → pygame.Vector2` — Current pixel offset to apply to all world-space draws.

#### `framework/stage/checkpoint.py` — `Checkpoint`

A trigger zone that records the player's current position as a respawn anchor. When the player enters the checkpoint's rect, it emits `CHECKPOINT_REACHED`. If the player subsequently dies, the stage restores the player to the last checkpoint position.

---

### 2.9 Framework Processing

#### `framework/processing/color_tools.py` — `ColorTools`

Pure functions for color space conversions and per-pixel operations on Pygame surfaces.

| Function | Input | Output | Academic Unit |
|---|---|---|---|
| `rgb_to_hsv(r, g, b)` | 0–255 ints | (0–360, 0–1, 0–1) | Unit V |
| `hsv_to_rgb(h, s, v)` | floats | (0–255 ints) | Unit V |
| `rgb_to_hsl(r, g, b)` | 0–255 ints | (0–360, 0–1, 0–1) | Unit V |
| `hsl_to_rgb(h, s, l)` | floats | (0–255 ints) | Unit V |
| `rgb_to_cmyk(r, g, b)` | 0–255 ints | (0–1 floats) | Unit V |
| `cmyk_to_rgb(c, m, y, k)` | 0–1 floats | (0–255 ints) | Unit V |
| `alpha_blend(src, dst, alpha)` | surfaces, float | surface | Unit V |
| `apply_tint(surface, color)` | surface, RGB | surface | Unit V |
| `surface_to_array(surface)` | surface | numpy ndarray | Unit VI |
| `array_to_surface(array)` | numpy ndarray | surface | Unit VI |

#### `framework/processing/filter_tools.py` — `FilterTools`

Convolution and edge detection filters applied to Pygame surfaces via NumPy and SciPy.

| Function | Description | Academic Unit |
|---|---|---|
| `apply_kernel(surface, kernel)` | Apply custom convolution kernel | Unit VII |
| `gaussian_blur(surface, sigma)` | Gaussian blur by sigma | Unit VII |
| `sobel_edge(surface)` | Sobel edge detection, returns grayscale | Unit VII |
| `canny_edge(surface, low, high)` | Canny edge detection | Unit VII |
| `adjust_brightness(surface, factor)` | Multiply pixel values by factor | Unit VII |
| `adjust_contrast(surface, factor)` | Stretch histogram by factor | Unit VII |
| `compute_histogram(surface)` | Return RGB histogram as dict | Unit VII |

#### `framework/processing/curve_tools.py` — `CurveTools`

Mathematical curve computation. All functions return lists of `(x, y)` tuples representing sampled points.

| Function | Description | Academic Unit |
|---|---|---|
| `bezier(control_points, n_samples)` | Compute Bézier curve via Bernstein polynomials | Unit III |
| `b_spline(control_points, degree, n_samples)` | Compute B-Spline curve | Unit III |
| `nurbs(control_points, weights, knots, degree, n_samples)` | Compute NURBS curve | Unit III |
| `catmull_rom(control_points, n_samples)` | Compute Catmull-Rom spline | Unit III |
| `sample_path(points, t)` | Interpolate position on a sampled path at parameter t (0–1) | Unit III |

#### `framework/processing/vision_tools.py` — `VisionTools`

Image segmentation and pattern recognition utilities.

| Function | Description | Academic Unit |
|---|---|---|
| `threshold_binary(surface, thresh)` | Binary threshold | Unit VIII |
| `threshold_otsu(surface)` | Otsu automatic threshold | Unit VIII |
| `morphological_erode(surface, kernel_size)` | Morphological erosion | Unit VIII |
| `morphological_dilate(surface, kernel_size)` | Morphological dilation | Unit VIII |
| `watershed_segment(surface)` | Watershed segmentation | Unit VIII |
| `extract_features(surface)` | Extract HOG or LBP feature vector | Unit IX |
| `classify_region(features, model)` | Classify feature vector using scikit-learn model | Unit IX |

---

## 3. Dependency Rules

### 3.1 Import Hierarchy

Cuatro reglas, y sólo cuatro. Están comprobadas en cada ejecución de la suite
por `tests/test_layering.py`; si alguna deja de cumplirse, la suite se pone en
rojo antes de que la infracción llegue a nadie.

| # | Regla | Por qué |
|---|---|---|
| **L1** | El núcleo del motor —`engine/` **excepto** `engine/scenes/` y `engine/core/app.py`— no importa nada de `framework`. | Es lo que permite que el motor se pueda leer y reutilizar sin arrastrar el juego. Hoy se cumple con **cero** excepciones. |
| **L2** | `framework/processing/` no importa nada de `engine`. | Son las funciones que se explican en clase: convolución, Sobel, Otsu, HOG. Tienen que poder ejecutarse desde un cuaderno sin arrancar pygame. Hoy se cumple con **cero** excepciones. |
| **L3** | Un escenario no importa otro escenario. | Cada `stages/stageN` es entregable por separado. Hoy se cumple con **cero** excepciones. |
| **L4** | Ni `engine/` ni `framework/` importan de `stages/`, salvo el jefe de referencia. | `stages/` es contenido —y en su mayor parte, entregas de estudiantes—. Si el motor depende de una entrega, un paquete que falta o que no importa deja de romper un nivel y pasa a romper el juego entero. Hoy se cumple con **una** excepción nombrada. |

**La excepción de L4, nombrada y acotada:**

`framework/entities/entity_factory.py` importa `stages.boss_venado.boss_venado`
dentro de `ensure_registered()` para darlo de alta en el registro de entidades.
Se tolera porque el Venado es el **jefe de referencia** que mantiene el equipo
docente y del que copian los estudiantes, no una entrega. Se declara aquí y en
`tests/test_layering.py::EXCEPCION_L4` para que sea una decisión y no un
descuido: cualquier *otra* dependencia de `framework` hacia `stages` pone la
suite en rojo (AUD-172).

**Las dos excepciones, nombradas y acotadas:**

- `engine/core/app.py` es la **raíz de composición**: es el único sitio que
  conoce todas las piezas a la vez, porque su trabajo es cablearlas. Que
  importe `framework.entities.entity_factory` y `framework.academic.sesion`
  no es una fuga de capas, es el patrón.
- `engine/scenes/` es la **capa de aplicación**, no el núcleo. Los
  laboratorios académicos viven ahí y enseñan algoritmos que viven en
  `framework/processing/`; que el laboratorio de color importe
  `color_tools` es exactamente lo que tiene que hacer. Todos los imports de
  esta carpeta hacia `framework` son de esa forma.
>
> **AUD-161 — aquí decía «son 27 imports».** Eran 26 al medirlo. Un número
> contado a mano en prosa envejece a la primera escena que se añade o se
> quita, y entonces el documento miente sobre algo que nadie va a volver a
> contar. Lo que sí se comprueba en cada ejecución es la **regla**, en
> `tests/test_layering.py`; la cifra no aportaba nada que la regla no diga
> mejor.

> **AUD-101 — qué decía esta sección antes.**
> Decía: «*Cross-layer imports (going upward) are prohibited*», seguido de una
> lista de importaciones permitidas por módulo. Medido contra el código, esa
> regla estaba incumplida **27 veces** —todas legítimas— y a la vez pedía a
> `framework/processing` que no importara «engine or framework», lo que
> prohibía incluso que un módulo del paquete importara a su vecino, cosa que
> hacen tres de ellos con toda la razón.
>
> Una regla que se incumple 27 veces sin consecuencias no es una regla: es
> una frase. Lo que sí es cierto, y ahora está comprobado, es que el núcleo
> del motor y las funciones de procesamiento están limpios. Eso es lo que
> importa y es lo que se vigila.

La lista de abajo se conserva como **mapa de dependencias típicas**, no como
una prohibición: describe por dónde fluyen normalmente las importaciones.

```
main.py
  → engine.core.app

engine.core.app
  → engine.core.settings
  → engine.core.clock
  → engine.core.event_bus
  → engine.scene.scene_manager
  → engine.input.input_manager
  → engine.audio.audio_manager

engine.scene.scene_manager
  → engine.scene.base_scene
  → engine.scene.transitions

framework.entities.*
  → engine.core.settings
  → engine.core.event_bus
  → engine.utils.*

framework.stage.*
  → engine.core.settings
  → engine.utils.*
  → framework.entities.*

framework.processing.*
  → (no engine or framework imports — pure functions only)

stages.stage0.stage0
  → engine.scene.base_scene
  → framework.entities.*
  → framework.stage.*
  → framework.processing.*
  → engine.core.event_bus
```

### 3.2 Prohibited Cross-Stage Imports

Stage modules must never import from other stage modules. Each stage is isolated.

```python
# PROHIBITED:
from stages.stage1.stage1 import MyCustomEnemy  # Never in stage2 or stage3
```

---

## 4. Data Flow

### 4.1 Per-Frame Data Flow

```
pygame.event.get()
    ↓
InputManager.pump(events)        # Process raw input → action states
    ↓
EventBus (queued events)         # Events from previous frame resolved
    ↓
SceneManager.current.update(dt)  # Active scene updates all entities
    |
    ├── Player.update(dt)        # Input → velocity → position → state
    ├── EnemyX.update(dt)        # AI → velocity → position → state
    ├── Checkpoint.update(dt)    # Trigger zone detection
    └── Camera.update(dt)        # Smooth follow
    ↓
App.internal_surface.fill(BG)   # Clear internal buffer
    ↓
SceneManager.current.draw(surface)
    |
    ├── Background layers (parallax)
    ├── pyscroll map render
    ├── Entity renders (world-space, camera offset applied)
    └── HUD render (screen-space, no offset)
    ↓
pygame.transform.scale(internal, window_size)  # Responsive scaling — UI uses %-based layout
    ↓
pygame.display.flip()
```

### 4.2 Event Data Flow

Events are not processed immediately when emitted. They are queued and dispatched at the start of the next frame update. This prevents mid-frame state corruption.

```
Entity emits event              (e.g., Player dies → PLAYER_DIED)
    ↓
EventBus.queue(event)           (stored in pending list)
    ↓
Next frame: EventBus.dispatch() (called at start of update)
    ↓
All registered listeners receive the event data
```

---

## 5. Application Lifecycle

```
main.py: App()
    ├── pygame.init()
    ├── pygame.mixer.init()
    ├── Create internal surface (settings.INTERNAL_WIDTH × settings.INTERNAL_HEIGHT)
    ├── Create window surface (scaled by settings.DISPLAY_SCALE)
    ├── Instantiate DeltaClock
    ├── Instantiate EventBus (singleton)
    ├── Instantiate InputManager
    ├── Instantiate AudioManager
    ├── Instantiate SceneManager
    └── Push SplashScene

App.run()
    └── Main Loop:
        ├── for event in pygame.event.get():
        │       if event.QUIT → App.quit()
        ├── InputManager.pump(events)
        ├── EventBus.dispatch()
        ├── dt = DeltaClock.tick()
        ├── SceneManager.current.update(dt)
        ├── internal_surface.fill(BLACK)
        ├── SceneManager.current.draw(internal_surface)
        ├── Scale internal_surface → window_surface
        └── pygame.display.flip()

App.quit()
    ├── AudioManager.stop_music()
    ├── pygame.quit()
    └── sys.exit(0)
```

---

## 6. Initialization Flow

### 6.1 Engine Initialization Order

1. `pygame.init()` — Initialize all Pygame subsystems
2. `pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)` — Audio
3. `pygame.display.set_mode(window_size)` — Create OS window
4. `internal_surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))` — Create render target
5. `DeltaClock()` — Wrap `pygame.time.Clock`
6. `EventBus()` — Singleton event dispatcher
7. `AssetLoader()` — Singleton asset cache
8. `InputManager(action_map)` — Load default action bindings
9. `AudioManager()` — Initialize mixer channels
10. `SceneManager()` — Initialize empty scene stack
11. `SceneManager.push(SplashScene())` — Start the application

### 6.2 Stage Initialization Order

When a stage scene is pushed or replaced onto the scene manager:

1. `Stage.on_enter()` called
2. `AudioManager.play_music(stage_bgm)`
3. `StageLoader.load(tmx_path)` — Parse map, build layers, collect spawn data
4. Spawn `Player` at `StageData.spawn_point`
5. Spawn all entities from `StageData.entity_list`
6. Register all `StageData.checkpoints`
7. `Camera.follow(player)`
8. `HUD.start_timer(stage_time_limit)`
9. `ScreenBanner.play(stage_name)`

---

## 7. Scene Flow

```
SplashScene          (professor logo, framework logo)
    ↓ (auto-advance after 3 seconds)
TitleScene           (game title, main menu: Start / Options / Academic Demos / Quit)
    ↓ (player selects Start)
StoryScene1          (story text with background illustration)
    ↓ (player confirms)
StoryScene2
    ↓
StoryScene3
    ↓
Stage0Scene          (professor-built demonstration stage)
    ↓ (next trigger reached)
Stage1Scene          (student stage)
    ↓ (next trigger reached)
Stage2Scene
    ↓
Stage3Scene
    ↓
EndScene             (credits / completion screen)

**Academic Demos Flow (accessible from TitleScene menu):**
```
TitleScene
    ↓ (player selects "ACADEMIC DEMOS")
DemoMenuScene        (10 options: Units II–IX)
    ↓      ↓         ↓           ↓            ↓
Vector   Transform  Curve       Interpolate  Color
(II)     (II/III)   (III)       (III/IV)     (V)
    ↓      ↓         ↓           ↓            ↓
Noise    Collision  Filter      Vision       Pattern
(V/VIII) (VI)       (VII)       (VIII)       (IX)
    ↓ (ESC)
DemoMenuScene
    ↓ (ESC)
TitleScene
```
```

**Game Over Flow:**
```
Player health reaches 0
    ↓ EventBus emits PLAYER_DIED
GameOverScene pushed on top of active stage
    ↓ Player selects Continue
GameOverScene popped → Stage resumes from last checkpoint
    ↓ Player selects Quit
GameOverScene popped → TitleScene
```

---

## 8. System Integration

### 8.1 Player ↔ HUD Integration

The `Player` entity emits `PLAYER_DAMAGED` and `PLAYER_HEALED` events via the `EventBus`. The `HUD` subscribes to these events and updates the heart meter display. The `HUD` does not hold a direct reference to the `Player`.

### 8.2 Stage ↔ Camera Integration

The `Camera` holds a reference to the `Player` entity as its follow target. The `Camera.update(dt)` method smoothly moves the viewport toward the player's position. All world-space entities receive `camera.offset` as a parameter in their `draw()` call and subtract it from their world position to compute screen position.

### 8.3 TMX ↔ StageLoader ↔ Entity Spawn Integration

The TMX file defines entity spawn points as Tiled object layer entries with `type` and `properties` attributes. `StageLoader` reads these objects, looks up the entity class in a registered factory dictionary, and instantiates the entity with the properties from the TMX object. This decouples entity implementation from map design.

**Entity Factory Registration:**
```python
# In App or stage initialization — professor registers defaults:
StageLoader.register_entity("Walker", EnemyWalker)
StageLoader.register_entity("Flying", EnemyFlying)
StageLoader.register_entity("Shooter", EnemyShooter)
StageLoader.register_entity("Checkpoint", Checkpoint)

# Students register custom entities in their stage:
StageLoader.register_entity("MyCustomEnemy", MyCustomEnemy)
```

### 8.4 Processing Tools ↔ Entity Integration

Processing utilities in `framework/processing/` are used by entities and stages to transform visual data. For example, a student stage might apply a Gaussian blur to a background layer, or use `CurveTools.bezier()` to generate an enemy patrol path. The tools return data; the calling code decides how to use it.

### 8.5 EventBus Integration Diagram

```
[Player]          → emits → PLAYER_DAMAGED, PLAYER_HEALED, PLAYER_DIED
[EnemyBase]       → emits → ENEMY_DIED
[Checkpoint]      → emits → CHECKPOINT_REACHED
[NextTrigger]     → emits → STAGE_COMPLETE
[Stage]           → emits → SHOW_MESSAGE, HIDE_MESSAGE
[HUD]             → listens → PLAYER_DAMAGED, PLAYER_HEALED
[AudioManager]    → listens → PLAYER_DAMAGED, ENEMY_DIED, STAGE_COMPLETE
[SceneManager]    → listens → PLAYER_DIED, STAGE_COMPLETE
[MessageBox]      → listens → SHOW_MESSAGE, HIDE_MESSAGE
[StageLoader]     → listens → CHECKPOINT_REACHED
```



--- Traducción al Español ---

*Este documento está disponible en inglés. Para una traducción completa al español, contacte al profesor.*


---
## 🔗 Documentos Relacionados

- [[04_PLAYER_SPEC.md|Player Specification]]
- [[05_ENEMY_SPEC.md|Enemy Specification]]
- [[06_TMX_SPEC.md|TMX Specification]]
- [[10_LIBRARIES_AND_DEPENDENCIES.md|Libraries and Dependencies]]
- [[22_API_CONTRACTS.md|API Contracts]]
