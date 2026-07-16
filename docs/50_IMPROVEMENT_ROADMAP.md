---
document_id: "LOI-ROADMAP-050"
title: "Legacy of InFest — Improvement Roadmap"
aliases: ["Improvement Roadmap", "50 Improvement Roadmap"]
tags: ["improvement", "roadmap", "planning"]
description: "Consolidated improvement opportunities from evaluations + V2 Architecture Plan"
source: "docs/50_IMPROVEMENT_ROADMAP.md"
date_processed: "2026-07-16"
---

# Legacy of InFest — Improvement Roadmap

**Document ID:** LOI-ROADMAP-050  
**Version:** 3.0.0  
**Status:** Official — Current Implementation Baseline + V2 Architecture Plan  
**Audience:** Professor, Teaching Assistants, AI coding assistants

---

## 0. Current Implementation Status

### 0.1 Fully Implemented Systems ✅

| System | Status | Evidence |
|--------|--------|----------|
| **Core Engine** | ✅ Complete | Audio, Input, Scene Manager, Transitions, Save, Achievements, Inventory, Settings, Event Bus |
| **Player** | ✅ Complete | 25 states, full physics, state machine (State Pattern) |
| **Enemies** | ✅ Complete | 9 types: Walker, Flying, Shooter, Charger, Archer, Brute, Caster, Assassin, Boss |
| **VFX** | ✅ Complete | Particles, trails, damage numbers, lighting, post-processing, fog of war, water, hit effects |
| **UI** | ✅ Complete | HUD, MessageBox, Minimap, Tutorial, Inventory, Achievements, World Map, Options |
| **Processing Tools** | ✅ Complete | FilterTools, VisionTools, PatternRecognition, ColorTools, CurveTools |
| **Stage Systems** | ✅ Complete | StageLoader, Camera, Collision, Hazards, Checkpoints, Progression, Speedrun, Boss Rush, Cutscene, WeatherSystem |
| **Dialogue System** | ✅ Complete | Branching dialogue with portraits |
| **Bestiary** | ✅ Complete | Enemy tracking system |
| **Demo Scenes** | ✅ Complete | 13 interactive labs (Filter, Vision, Pattern, Color, Vector, Transform, Interpolation, Curve, Noise, Collision, Combo, etc.) |
| **Learning Overlay** | ✅ Complete | F2-F10 debug/learning toggles |
| **Spatial Grid** | ✅ Complete | Broad-phase collision in `collision_system.py` |
| **Entity Factory** | ✅ Complete | Registry pattern in `entity_factory.py` |
| **Stages** | ⚠️ Partial | 2 stages complete (Stage0, Boss Venado) |

### 0.2 Project Metrics (Updated)

| Metric | Value |
|--------|-------|
| **Total Files (.py)** | ~210 files |
| **Lines of Code (Python)** | ~29,000 LOC |
| **Tests** | 464+ tests |
| **Test Files** | 40+ files |
| **Scene Classes** | 32 scenes |
| **Enemy Types** | 8 types + Boss |
| **Player States** | 25 concrete states |
| **Implemented Stages** | 2 (Stage0, Boss Venado) |
| **Documentation** | 65+ .md documents |
| **Demo Scenes** | 13 interactive labs |
| **Architectural Patterns Used** | DI (GameContext), State, Factory, Observer (EventBus), Singleton (Inventory) |

### 0.3 Code Quality Assessment (from 2026-07-16 Code Audit)

| Aspect | Score | Notes |
|--------|-------|-------|
| **Architecture** | ⚠️ 6/10 | OOP jerárquico, sin ECS, sin plugin system |
| **Rendering Performance** | ⚠️ 4/10 | CPU-bound blitting, sin GPU batch, ~800 sprite limit |
| **Memory Efficiency** | ⚠️ 5/10 | Sin object pooling, GC pressure 15-30 MB/s |
| **Startup Time** | ⚠️ 5/10 | ~3.4s por imports pesados (scipy, sklearn) |
| **Modularity** | ✅ 7/10 | DI con GameContext, pero globales ocultos (_emit, _get_bus) |
| **Type Safety** | ⚠️ 5/10 | Type hints parciales, no pasa mypy strict |
| **Test Coverage** | ✅ 7/10 | 464+ tests, faltan benchmarks de rendimiento |
| **Extensibility** | ❌ 3/10 | Sin plugin system, sin hooks API |
| **Code Smells** | ⚠️ | Lambda global `_emit`, Singleton Inventory, imports laterales |
| **Overall V1** | ⚠️ **5.6/10** | **Funcional pero necesita re-arquitectura para escalar** |

### 0.4 Implementation Evidence by Category

#### Engine Layer (`src/engine/` — 52 files)
- `audio/audio_manager.py` — Audio playback with dynamic crossfade, stereo pan, ambient layers
- `audio/sound_bank.py` — Named sound registry
- `input/input_manager.py` — Keyboard + controller support
- `scene/scene_manager.py` — Stack-based push/pop/replace + stage queue
- `scene/base_scene.py` — Abstract lifecycle (awake, start, on_enter, on_exit, update, draw)
- `core/achievements.py` — Achievement system
- `core/inventory.py` — Item management (⚠️ Singleton anti-pattern)
- `core/save_manager.py` — JSON-based atomic saves
- `core/game_context.py` — DI container ✅
- `core/event_bus.py` — Pub/sub event dispatch ✅
- `core/settings.py` — Global constants
- `core/events.py` — Event name constants
- `core/stage_registry.py` — Stage registration
- `scenes/*.py` — 32 scene implementations

#### Framework Layer (`src/framework/` — 43 files)
- `entities/player.py` — 25 states, State Pattern ✅ (750 LOC)
- `entities/player_states.py` — State subclasses ✅
- `entities/enemy_*.py` — 9 enemy types
- `entities/entity_factory.py` — Registry pattern ✅
- `vfx/particle_system.py` — Particle effects
- `vfx/lighting.py` — 2D lights
- `vfx/fog_of_war.py` — Fog of war
- `vfx/weather_system.py` — Climate system (rain, snow, fog, dust, embers) ✅
- `stage/camera.py` — Camera follow, shake, parallax
- `stage/collision_system.py` — SpatialGrid broad-phase ✅
- `stage/stage_loader.py` — TMX parser → StageData
- `ui/dialogue_system.py` — Branching dialogue
- `ui/learning_overlay.py` — F2-F10 learning toggles ✅

---

## 1. Methodology

This document consolidates improvement opportunities from evaluations + 2026-07-16 code audit:

1. **External evaluation v1** (game dev professor) — architecture, pedagogy, completeness
2. **External evaluation v2** (syllabus alignment) — shift from "game" to "academic platform"
3. **External evaluation v3** (architecture review) — plugin system, ECS, observability
4. **External evaluation v4** (engine review) — production engine architecture, tools
5. **External evaluation v5** (pedagogy & math visualization) — teaching engineering thinking
6. **External evaluation v6** (methodology & documentation) — learning methodologies, documentation strategy
7. **External evaluation v7** (teacher & student support) — Teaching Operating System, student companion
8. **External evaluation v8** (AI Lab & XAI) — Scikit-learn integration, explainable AI, ML applied to graphics
9. **External evaluation v9** (game progression & gamification) — progression system, mastery levels, knowledge tree
10. **Code audit** (build `b63ca53` + working tree) — 426 tests, 120+ modules, 19 player states, 9 enemy types
11. **Gap analysis** against AAA+ 2D titles, academic platforms, commercial engines, pedagogical best practices, and accreditation standards
12. **Engine architecture analysis** (v10) — rendering performance, dependency management, networking, distribution limits
13. **2026-07-16 Deep Code Audit** (22 files analyzed) — identified architecture smells, performance bottlenecks, code quality issues, and V2 roadmap

---

## 2. Executive Summary (Updated)

| Category | Items | P0 | P1 | P2 | P3 | Effort |
|----------|-------|----|----|----|----|--------|
| Pedagogy & Math | 22 | 1 | 8 | 10 | 3 | 18-28 weeks |
| Methodology | 12 | 0 | 1 | 8 | 3 | 12-18 weeks |
| Teacher Support | 23 | 0 | 5 | 12 | 6 | 20-30 weeks |
| Student Companion | 23 | 0 | 4 | 13 | 6 | 18-26 weeks |
| AI Lab & XAI | 22 | 0 | 3 | 12 | 7 | 16-24 weeks |
| Game Progression | 12 | 0 | 2 | 6 | 4 | 10-14 weeks |
| Engine Architecture | 28 | 4 | 6 | 10 | 8 | 30-45 weeks |
| Documentation Strategy | 10 | 0 | 0 | 5 | 5 | 8-12 weeks |
| AI & Enemies | 4 | 0 | 2 | 1 | 1 | 3-4 weeks |
| Tools & Editors | 8 | 0 | 2 | 4 | 2 | 10-18 weeks |
| **Performance** | **9** | **3** | **1** | **4** | **1** | **12-18 weeks** |
| Content | 3 | 0 | 1 | 1 | 1 | 2-4 weeks |
| Documentation | 2 | 1 | 1 | 0 | 0 | 1 week |
| **Code Quality** | **15** | **2** | **5** | **6** | **2** | **14-24 weeks** |
| **TOTAL** | **193** | **11** | **41** | **92** | **49** | **185-268 weeks** |

**Note:** This roadmap documents FUTURE improvements. See Section 0 for currently implemented systems. New items added in v3.0.0: Code Quality category, V2 Architecture Plan (Section 8), elevated P0 items from P2 based on criticality.

---

## 3. Improvement Items

### 3.1 P0 — Blockers (Must fix before V2 launch)

#### P0-01: Documentación desactualizada (DOC) — ✅ RESOLVED

| Field | Value |
|-------|-------|
| **Category** | Documentation |
| **Status** | ✅ **RESOLVED** |
| **Effort** | 1 week |
| **Current State** | `05_ENEMY_SPEC.md` documenta los 8 tipos de enemigo (Walker, Flying, Shooter, Charger, Archer, Brute, Caster, Assassin) en secciones 3-10. BossBase tiene spec separado (`17_BOSS_SPEC.md`). Docs 03/22 actualizados con INTERNAL_WIDTH=800, INTERNAL_HEIGHT=600. BaseScene incluye `awake()`/`start()` y `context: GameContext`. |
| **Implementation Evidence** | ✅ `src/framework/entities/enemy_walker.py`, `enemy_flying.py`, `enemy_shooter.py`, `enemy_charger.py`, `enemy_archer.py`, `enemy_brute.py`, `enemy_caster.py`, `enemy_assassin.py`, `boss_base.py` |
| **Action** | Resuelto. Mantener sincronización en futuras actualizaciones. |
| **Verification** | Cada spec documenta exactamente lo que el código implementa. |

#### P0-02: Clima/partículas desde TMX (ARC) — ✅ IMPLEMENTED

| Field | Value |
|-------|-------|
| **Category** | Architecture |
| **Status** | ✅ **IMPLEMENTED** |
| **Effort** | 2-3 days |
| **Current State** | `WeatherSystem` existe en `src/framework/vfx/weather_system.py` (155 lines). Auto-wired en `StageScene` desde propiedad `climate` del TMX. Soporta rain, snow, fog, dust, embers. |
| **Implementation Evidence** | ✅ `src/framework/vfx/weather_system.py` |
| **Action** | Resuelto. Considerar mejoras: weather transitions, thunder/lightning, wind. |
| **Verification** | TMX con `climate: rain` produce lluvia visible. |

#### P0-03: Legacy Learning Mode (PED) — ✅ IMPLEMENTED

| Field | Value |
|-------|-------|
| **Category** | Pedagogy & Visualization |
| **Status** | ✅ **IMPLEMENTED** |
| **Effort** | 2-3 weeks |
| **Current State** | `LearningOverlay` existe en `src/framework/ui/learning_overlay.py` (209 lines). F2=FPS, F3=Grid, F4=Bounding Boxes, F5=Coords, F7=Pipeline, F8=Colisiones, F9=Histograma, F10=Segmentación. Wired en `StageScene.update()`. |
| **Implementation Evidence** | ✅ `src/framework/ui/learning_overlay.py`, `src/engine/scenes/debug_overlay.py` |
| **Action** | Resuelto. Considerar F6=Matriz 3x3 como mejora futura. |
| **Verification** | F4 muestra ejes X/Y. F9 muestra histograma RGB. |

#### P0-004: Sprite Batch System (PERF) — 🔺 NEW — ELEVATED to P0

| Field | Value |
|-------|-------|
| **Category** | Performance |
| **Priority** | **P0** (elevated from P2-116 after code audit) |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 3-4 weeks |
| **Current State** | El motor usa blitting CPU-bound (pygame-ce Surface.copy/blit). No hay agrupación de geometría en GPU. `app._draw()` hace un blit por sprite directamente a la surface interna. |
| **Problem** | El renderizado 2D es puramente CPU-bound. Cada sprite se dibuja como una operación de copia de píxeles individual, sin batching. Esto limita la cantidad de sprites simultáneos (~500-800 antes de micro-stutters). Este es **el cuello de botella #1 del motor**. |
| **Suggested Solution** | Implementar un `SpriteBatch` que agrupe sprites por textura atlas y los dibuje en una sola operación de GPU usando `pygame.sdl2.video.Texture`. Crear un `Renderer2D` con capas: Background (tilemap batch), Entities (atlas), Particles (point sprites), Foreground, HUD. |
| **Acceptance Criteria** | Renderizar 2000+ sprites animados a 60 FPS estables sin micro-stutters. |
| **Dependencies** | pygame-ce 2.5+ (SDL2_GPU features), `TextureAtlas` builder |
| **Academic Value** | Concepto de **graphics pipeline**, **draw call optimization**, **GPU vs CPU rendering** — temas avanzados de CG. |
| **Why P0** | Sin esto, el motor no puede escalar a juegos con muchos sprites. Es requisito base para V2. |

#### P0-005: Surface Object Pool & GC Mitigation (PERF) — 🔺 NEW — ELEVATED to P0

| Field | Value |
|-------|-------|
| **Category** | Performance |
| **Priority** | **P0** (elevated from P2-117 after code audit) |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 2-3 weeks |
| **Current State** | Efectos como iluminación, partículas climáticas y post-processing crean superficies intermedias temporales frame a frame. La tasa de asignación alcanza 15-30 MB/s, provocando micro-stutters por GC. |
| **Problem** | El recolector de basura de Python (GC) se activa frecuentemente al descartar objetos `Surface` temporales, causando caídas de frames imperceptibles pero acumulativas. Con efectos intensivos (lluvia + luces + partículas), el GC puede causar pausas de hasta 16ms (~1 frame perdido). |
| **Suggested Solution** | Implementar un `SurfacePool` con reutilización de objetos: pre-asignar un pool de superficies de tamaños comunes (screen, quarter-screen, tile-sized) y reciclarlas en lugar de crear/destruir. Usar `__slots__` en clases de datos temporales. |
| **Acceptance Criteria** | Reducción de asignación de memoria a <5 MB/s sostenido. Eliminación de micro-stutters por GC en escenas con efectos intensivos. |
| **Dependencies** | `gc` module, profiling con `tracemalloc` |
| **Academic Value** | Enseña **memory management**, **object pooling pattern**, **GC profiling** — conceptos clave en ingeniería de software de tiempo real. |
| **Why P0** | El GC pressure afecta a TODAS las escenas con efectos. Es un problema sistémico. |

#### P0-006: Post-Processing Pipeline with Selective Resolution (PERF) — 🔺 NEW — ELEVATED to P0

| Field | Value |
|-------|-------|
| **Category** | Performance |
| **Priority** | **P0** (elevated from P2-118 after code audit) |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 2-3 weeks |
| **Current State** | Los filtros de post-procesamiento (Bloom, Color Grading, Daltonismo) se aplican sobre la resolución completa (800×600), causando caídas de ~80 FPS a <35 FPS cuando se combinan múltiples efectos. |
| **Problem** | Aplicar múltiples filtros de software sobre cada píxel de la pantalla es computacionalmente costoso. No hay un sistema de composición de efectos que permita priorizar o reducir resolución por efecto. |
| **Suggested Solution** | Implementar un `PostProcessStack` con: (1) resolución variable por efecto (half-resolution para Bloom, full para Color Grading), (2) composición por capas con blending, (3) desactivación automática de efectos cuando FPS < umbral (adaptive performance). |
| **Acceptance Criteria** | 3+ filtros simultáneos a ≥55 FPS sostenidos. Degradación graceful cuando el rendimiento cae. |
| **Dependencies** | `PostProcessStack` class, `scipy.ndimage` para filtros downsampled |
| **Academic Value** | **Signal processing**, **multi-resolution techniques**, **adaptive performance** — temas de CG avanzada. |
| **Why P0** | El post-procesamiento es usado en demos académicas (filtros). Sin rendimiento aceptable, la experiencia de usuario se degrada severamente. |

#### P0-007: State Container for Player Data (ARC) — 🔺 NEW

| Field | Value |
|-------|-------|
| **Category** | Code Quality |
| **Priority** | **P0** |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 1-2 weeks |
| **Current State** | `Player.__init__` en `player.py` tiene ~40 variables de estado dispersas entre líneas 138-220: `velocity`, `is_grounded`, `_coyote_counter`, `_attack_timer`, `combo_count`, `special_meter`, `_slide_speed`, `_air_dash_count`, etc. |
| **Problem** | El estado del jugador está fragmentado en ~40 atributos sueltos. Esto hace difícil: (1) serializar el estado para save/load, (2) resetear el estado al morir, (3) testear la lógica de física, (4) entender el flujo de datos. |
| **Suggested Solution** | Crear `PlayerState` dataclass que agrupe todo el estado puro del jugador (posición, velocidad, salud, combo, meter, etc.) y usar composición: `Player` tiene un `PlayerState` en lugar de 40 atributos. La lógica de negocio queda en `Player`, los datos en `PlayerState`. |
| **Acceptance Criteria** | `PlayerState` dataclass con ~20 fields. `Player` init reducido de 80 líneas a 20. Serialización a JSON trivial. Tests de física pueden crear `PlayerState` directamente. |
| **Dependencies** | `dataclasses` (ya importado) |
| **Academic Value** | **Separation of concerns**, **Value Objects**, **data vs behavior** — principios SOLID. |

#### P0-008: Eliminar Global EventBus Shortcuts (ARC) — 🔺 NEW

| Field | Value |
|-------|-------|
| **Category** | Code Quality |
| **Priority** | **P0** |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 1 week |
| **Current State** | En `player.py:23` y `enemy_base.py:20` existe: `_emit = lambda *a, **kw: _bus().emit(*a, **kw)`. Esto es una función lambda global que llama a `_get_bus()` cada vez, creando una dependencia oculta al EventBus global. |
| **Problem** | (1) Dificulta el testing: no se puede mockear el EventBus fácilmente. (2) Dependencia oculta: el módulo falla si no hay un bus default. (3) Code smell: patrón Service Locator encubierto. (4) Imposible tener múltiples buses (ej: test isolation). |
| **Suggested Solution** | Inyectar `EventBus` via parámetro en `__init__` de Player y EnemyBase. Mantener compatibilidad con código existente usando parámetro opcional `event_bus=None` que usa el bus default como fallback. Luego migrar progresivamente todas las instancias a usar inyección explícita. |
| **Acceptance Criteria** | Player y EnemyBase aceptan `event_bus` en constructor. Cero lambdas globales `_emit`. Tests pueden inyectar un `EventBus` mock. |
| **Dependencies** | `game_context.py` (ya tiene event_bus) |
| **Academic Value** | **Dependency Injection**, **Service Locator anti-pattern**, **testability** — ingeniería de software. |

---

### 3.2 P1 — High Priority

#### P1-01: Benchmark Suite for Performance (PERF) — 🔺 NEW

| Field | Value |
|-------|-------|
| **Category** | Performance / Code Quality |
| **Priority** | **P1** |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 2-3 weeks |
| **Current State** | No existen benchmarks automáticos. El rendimiento solo se evalúa subjetivamente ("se siente lento"). |
| **Problem** | Sin benchmarks, no podemos medir si las optimizaciones realmente funcionan. No hay línea base para comparar V1 vs V2. |
| **Suggested Solution** | Crear `tests/benchmarks/` con: `test_render_benchmark.py` (500/1000/2000 sprites), `test_physics_benchmark.py` (100/500/1000 entities), `test_startup_time.py` (cold/warm), `test_memory_benchmark.py` (heap allocations). Usar `pytest-benchmark` para integración CI. |
| **Acceptance Criteria** | 4+ benchmarks ejecutables con `pytest tests/benchmarks/`. Reporte de rendimiento en CI. Línea base documentada. |
| **Dependencies** | `pytest-benchmark` |
| **Academic Value** | **Performance engineering**, **benchmark-driven optimization**, **CI/CD pipelines**. |

#### P1-02: ECS Prototype for Data-Oriented Design (ARC)

| Field | Value |
|-------|-------|
| **Category** | Engine Architecture |
| **Priority** | **P1** (elevated from P2-120 after code audit) |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 4-6 weeks |
| **Current State** | El motor usa jerarquía de clases OOP tradicional (Player, Enemy, etc.) con herencia profunda. No hay separación datos-comportamiento. Enemigos: `EnemyBase → EnemyWalker → ...` (herencia profunda de 3 niveles). |
| **Problem** | (1) Agregar nuevo tipo de entidad requiere crear subclase y posiblemente modificar la jerarquía. (2) El rendimiento de caché de CPU es subóptimo al iterar componentes dispersos en memoria. (3) La serialización requiere lógica ad-hoc por cada clase. |
| **Suggested Solution** | Implementar un mini-ECS (Entity Component System) como capa OPCIONAL sobre la arquitectura existente: `Entity` como ID (int), `Component` como datos planos (dataclass/numpy struct), `System` como lógica pura. Mantener compatibilidad con el sistema OOP actual mediante wrappers/adapter pattern. Componentes iniciales: Position, Velocity, Sprite, Health, AI, Collision. Sistemas: Movement, Render, AI, Collision. |
| **Acceptance Criteria** | 5+ componentes funcionales (Position, Velocity, Sprite, Health, AI). 3+ sistemas (Movement, Render, AI). Rendimiento de iteración 2x vs OOP equivalente. Compatibilidad con entidades OOP existentes via adapter. |
| **Dependencies** | `numpy` para almacenamiento contiguo de componentes |
| **Academic Value** | **Data-Oriented Design (DOD)**, **CPU cache optimization**, **ECS pattern** — arquitectura de motores AAA. |
| **Why P1** | Fundamental para escalar a +100 entidades simultáneas y para la extensibilidad del framework. |

#### P1-03: Plugin System for Extensibility (ARC)

| Field | Value |
|-------|-------|
| **Category** | Engine Architecture |
| **Priority** | **P1** (elevated from P2-121) |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 3-5 weeks |
| **Current State** | No existe un sistema de plugins. Toda funcionalidad debe integrarse directamente en el código base del motor. |
| **Problem** | Los estudiantes avanzados o contribuyentes externos no pueden extender el motor sin modificar el núcleo. No hay un mecanismo estándar para empaquetar y distribuir extensiones (nuevos filtros, tipos de enemigos, efectos). |
| **Suggested Solution** | Diseñar un `PluginManager` que: (1) descubra plugins en directorios específicos (`plugins/`), (2) cargue dinámicamente módulos Python, (3) registre hooks en puntos de extensión definidos (render, update, input, tools), (4) valide versiones y dependencias. Hooks iniciales: `on_render`, `on_update`, `on_input`, `on_entity_spawn`, `on_stage_load`. |
| **Acceptance Criteria** | Plugin funcional de ejemplo (nuevo filtro de imagen) cargado sin modificar el core. Sistema de hooks con 5+ puntos de extensión. |
| **Dependencies** | `importlib.metadata`, `pluggy` (opcional) |
| **Academic Value** | **Plugin architecture**, **dependency injection**, **hook systems** — patrones de diseño de software extensible. |
| **Why P1** | Clave para el valor académico: estudiantes pueden extender sin tocar el core. |

#### P1-04: Lazy Import System for Heavy Dependencies (ARC)

| Field | Value |
|-------|-------|
| **Category** | Engine Architecture |
| **Priority** | **P1** (elevated from P2-119) |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 1-2 weeks |
| **Current State** | `scikit-learn`, `scikit-image`, `scipy` se importan al inicio de la aplicación, añadiendo >300ms de latencia de arranque incluso si no se usan en la sesión actual. BossVenado importa numpy y sklearn en startup. |
| **Problem** | Los tiempos de carga inicial son perceptibles para el usuario final (~3.4s). Las dependencias científicas pesadas se cargan aunque el estudiante solo esté explorando un nivel, no usando herramientas de ML/CV. |
| **Suggested Solution** | Implementar un `LazyLoader` que envuelva los imports pesados usando `__getattr__` a nivel de módulo. Los módulos científicos solo se importan cuando se invoca su primera función. Adicionalmente, mostrar un splash screen con barra de progreso durante la carga inicial. |
| **Acceptance Criteria** | Tiempo de arranque <1.5s en frío (vs ~3.4s actual). Los módulos científicos se cargan bajo demanda en <100ms. |
| **Dependencies** | `importlib`, refactor de `entity_factory.py` (BossVenado lazy import) |
| **Academic Value** | **Lazy loading pattern**, **module architecture**, **dependency management** — ingeniería de software. |

#### P1-05: Input System with Priority Layers (ARC) — 🔺 NEW

| Field | Value |
|-------|-------|
| **Category** | Engine Architecture |
| **Priority** | **P1** |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 1-2 weeks |
| **Current State** | `InputManager` es plano: todas las acciones compiten por el mismo espacio de input. Cuando hay UI abierta (menú, diálogo, inventario), el input de gameplay también se procesa. |
| **Problem** | No hay separación entre capas de input. Si el jugador presiona "A" mientras un mensaje de tutorial está abierto, puede activar tanto el gameplay como la UI. No hay un mecanismo de "input consume" o "priority stacking". |
| **Suggested Solution** | Implementar `InputStack` con capas jerárquicas: (1) UI Layer (menús, diálogos, popups), (2) Gameplay Layer (movimiento, ataque), (3) Debug Layer (F-keys). Cada capa puede consumir input y evitar que capas inferiores lo procesen. |
| **Acceptance Criteria** | UI abierta → gameplay inputs ignorados. Debug toggles siempre funcionan. Capas configurables por escena. |
| **Dependencies** | `input_manager.py` |
| **Academic Value** | **Input handling architecture**, **event propagation**, **layered systems** — UI/gameplay separation. |

#### P1-06: Audio Pipeline with Backend Abstraction (ARC) — 🔺 NEW

| Field | Value |
|-------|-------|
| **Category** | Engine Architecture |
| **Priority** | **P1** |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 2-3 weeks |
| **Current State** | `AudioManager` está acoplado directamente a `pygame.mixer`. No hay capa de abstracción ni fallback para entornos sin audio (headless, CI, web). |
| **Problem** | (1) No se puede ejecutar el juego en entornos sin pygame.mixer (CI, servidores). (2) Migrar a otro backend de audio (SDL2, OpenAL, WebAudio) requeriría reescribir AudioManager. (3) No hay soporte para audio 3D posicional. |
| **Suggested Solution** | Crear `AudioBackend` clase abstracta con implementaciones: `PygameMixerBackend` (actual), `NullBackend` (silent, para CI/headless), `SDL2MixerBackend` (futuro). AudioManager usa composición con un backend inyectable. |
| **Acceptance Criteria** | NullBackend funcional: cero dependencia de pygame.mixer. CI puede ejecutar tests de audio sin fallos. PygameMixerBackend mantiene 100% funcionalidad actual. |
| **Dependencies** | `audio_manager.py`, `ABC` |
| **Academic Value** | **Abstraction layer**, **Strategy pattern**, **backend isolation** — arquitectura de sistemas de audio. |

#### P1-07: Scripting enemigos (AI) — ✅ IMPLEMENTED

| Field | Value |
|-------|-------|
| **Category** | AI |
| **Status** | ✅ **IMPLEMENTED** |
| **Effort** | 1-2 weeks |
| **Current State** | 9 tipos de enemigo implementados con comportamientos únicos via código. |
| **Implementation Evidence** | ✅ `src/framework/entities/enemy_base.py` (base class), `enemy_walker.py`, `enemy_flying.py`, `enemy_shooter.py`, `enemy_charger.py`, `enemy_archer.py`, `enemy_brute.py`, `enemy_caster.py`, `enemy_assassin.py`, `boss_base.py` |
| **Action** | Ya implementado via código. Considerar agregar soporte JSON/YAML para data-driven enemies. |
| **Verification** | 9 tipos de enemigo funcionales con comportamientos únicos. |

---

### 3.3 P1 — Code Quality (NEW Category)

#### P1-08: Type Hints Completos + mypy strict (CQ) — 🔺 NEW

| Field | Value |
|-------|-------|
| **Category** | Code Quality |
| **Priority** | **P1** |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 2-3 weeks |
| **Current State** | Type hints parciales, `TYPE_CHECKING` en varios lados (`player.py:28-31`, `enemy_base.py:25-26`), `Any` usado como tipo en muchos lugares (`scene_manager.py:13`, `collision_system.py:3`). |
| **Problem** | Sin tipos estrictos, el IDE no puede detectar errores en tiempo de escritura. `mypy --strict` no pasa. Bugs como pasar argumentos en orden incorrecto solo se detectan en runtime. |
| **Suggested Solution** | Agregar type hints completos a todo el código. Configurar `mypy --strict` en `pyproject.toml`. Resolver gradualmente los errores. Priorizar: core (event_bus, app, scene_manager) → framework (player, enemy, stage) → scenes. |
| **Acceptance Criteria** | `mypy --strict` pasa en todo el código. Cero `Any` innecesarios. `TYPE_CHECKING` solo para imports circulares inevitables. |
| **Dependencies** | `mypy`, `pyproject.toml` |
| **Academic Value** | **Type safety**, **static analysis**, **defensive programming** — calidad de software. |

#### P1-09: Singleton Removal — Inventory (CQ) — 🔺 NEW

| Field | Value |
|-------|-------|
| **Category** | Code Quality |
| **Priority** | **P1** |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 1 week |
| **Current State** | `Inventory` en `inventory.py` usa patrón Singleton: `_instance: Inventory | None = None` con `__new__`. Se accede globalmente via `get_inventory()`. |
| **Problem** | (1) Dificulta testing: el estado persiste entre tests. (2) Acoplamiento global: cualquier módulo puede llamar a `get_inventory()` sin inyección. (3) Imposible tener inventarios separados (multiplayer, test scenarios). |
| **Suggested Solution** | Refactorizar Inventory a instancia normal inyectada via `GameContext`. Mantener `get_inventory()` como deprecated wrapper que emite warning. Migrar consumidores a usar `context.inventory`. |
| **Acceptance Criteria** | `Inventory` sin singleton. `GameContext` tiene `inventory` field. Tests pueden crear inventarios independientes. |
| **Dependencies** | `game_context.py`, `inventory.py` |
| **Academic Value** | **Singleton anti-pattern**, **Dependency Injection**, **test isolation**. |

#### P1-10: Asset Pipeline Moderno (ARC) — 🔺 NEW

| Field | Value |
|-------|-------|
| **Category** | Engine Architecture |
| **Priority** | **P1** |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 3-4 weeks |
| **Current State** | Assets en disco, sin compresión ni streaming. `AssetLoader` carga síncronamente con cache LRU simple. Sprites se cargan uno por uno. |
| **Problem** | (1) Carga síncrona: la primera vez que se usa un asset, hay un micro-freeze. (2) Sin empaquetado: los assets son archivos sueltos, fácil de perder/dañar. (3) Sin compresión: texturas PNG sin optimizar. |
| **Suggested Solution** | `AssetSystem V2`: (1) `AssetPack`: paquete binario comprimido (zip/7z) con índice. (2) `AsyncAssetLoader`: carga en background thread con callback. (3) `TextureAtlasBuilder`: empaqueta sprites en atlas. (4) LRU cache configurable con límite de memoria. |
| **Acceptance Criteria** | Carga asíncrona sin micro-freezes. AssetPack reduce espacio en disco 40%+. TextureAtlas builder funcional. |
| **Dependencies** | `asset_loader.py`, `threading` |
| **Academic Value** | **Asset pipeline**, **async loading**, **resource management** — ingeniería de motores. |

---

### 3.4 P2 — Medium Priority

#### P2-04: Bestiario UI (CONTENT) — ✅ IMPLEMENTED

| Field | Value |
|-------|-------|
| **Category** | Content |
| **Status** | ✅ **IMPLEMENTED** |
| **Effort** | 1 week |
| **Current State** | Sistema completo de bestiario con UI. |
| **Implementation Evidence** | ✅ `src/framework/entities/bestiary.py` (tracking system), `src/engine/scenes/bestiary_scene.py` (UI scene) |
| **Action** | Ya implementado. Considerar mejoras: filtros, búsqueda, estadísticas avanzadas. |
| **Verification** | Estudiante ve enemigos encontrados con stats y lore. |

#### P2-05: Speedrun UI (CONTENT) — ✅ IMPLEMENTED

| Field | Value |
|-------|-------|
| **Category** | Content |
| **Status** | ✅ **IMPLEMENTED** |
| **Effort** | 3-5 days |
| **Current State** | Sistema completo de speedrun con timer, splits y ghost replay. |
| **Implementation Evidence** | ✅ `src/framework/stage/speedrun_mode.py` (timer + splits + ghost data) |
| **Action** | Ya implementado. Considerar mejoras: leaderboards, share replays. |
| **Verification** | Jugador ve tiempo, splits, ghost replay. |

#### P2-79: Achievement System (NEW) — ✅ IMPLEMENTED

| Field | Value |
|-------|-------|
| **Category** | Student Support |
| **Status** | ✅ **IMPLEMENTED** |
| **Effort** | 1 week |
| **Current State** | Sistema completo de logros con UI. |
| **Implementation Evidence** | ✅ `src/engine/core/achievements.py` (system), `src/engine/scenes/achievement_scene.py` (UI) |
| **Action** | Ya implementado. Considerar mejoras: más logros, progresión, rarity. |
| **Verification** | Estudiante desbloquea logros académicos. |

#### P2-115: No Monetization (CONSISTENCY) — ✅ FOLLOWED

| Field | Value |
|-------|-------|
| **Category** | Game Progression |
| **Status** | ✅ **FOLLOWED** |
| **Effort** | — |
| **Current State** | Decisión de diseño documentada y seguida. No hay features de monetización. |
| **Implementation Evidence** | ✅ No existen sistemas de monedas, tienda, loot boxes, microtransacciones en el código |
| **Action** | Mantener decisión. No implementar features de monetización. |
| **Verification** | Documento oficial declara estas features como out-of-scope. |

#### P2-116: Observer Pattern Audit (ARC) — 🔺 NEW

| Field | Value |
|-------|-------|
| **Category** | Code Quality |
| **Priority** | P2 |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 1-2 weeks |
| **Current State** | EventBus se usa extensivamente, pero no hay documentación de todos los eventos, suscriptores, y orden de dispatch. `events.py` tiene 107 líneas de constantes. |
| **Problem** | Sin un mapa claro de eventos → suscriptores, es fácil introducir bugs por orden de dispatch incorrecto o eventos no esperados. |
| **Suggested Solution** | Crear `EventMap.md` documentando: cada evento, suscriptores, payload, orden de dispatch. Agregar tests de integración que verifiquen que eventos producen los efectos esperados. |
| **Acceptance Criteria** | `EventMap.md` documenta 30+ eventos. Tests de integración para eventos críticos (PLAYER_DAMAGED, STAGE_COMPLETE). |
| **Dependencies** | `events.py`, `event_bus.py` |
| **Academic Value** | **Observer pattern**, **event-driven architecture**, **integration testing**. |

---

### 3.5 P2-P3 — Architectural & Performance Limits

#### P2-117: Data-Driven Design for Enemies (ARC) — 🔺 NEW

| Field | Value |
|-------|-------|
| **Category** | AI / Engine Architecture |
| **Priority** | P2 |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 2-3 weeks |
| **Current State** | Enemigos definidos 100% en código Python. Cada nuevo tipo requiere crear una subclase de `EnemyBase` y registrarla en `entity_factory.py`. |
| **Problem** | No es posible definir enemigos desde data (JSON/YAML). Los estudiantes deben escribir código Python para crear variantes de enemigos. |
| **Suggested Solution** | Crear `EnemyBlueprint` sistema: (1) definición de enemigos en YAML (stats, comportamiento, sprite), (2) `DataDrivenEnemy` wrapper que interpreta blueprints, (3) editor visual básico. Mantener compatibilidad con enemigos code-based existentes. |
| **Acceptance Criteria** | 3+ blueprints YAML funcionales. `DataDrivenEnemy` puede reemplazar `EnemyWalker` y `EnemyFlying` via data. |
| **Dependencies** | `PyYAML`, `entity_factory.py` |
| **Academic Value** | **Data-Driven Design**, **declarative configuration**, **content pipeline**. |

#### P2-118: Couch Co-op Local Multiplayer (NET)

| Field | Value |
|-------|-------|
| **Category** | Engine Architecture |
| **Priority** | P2 |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 4-6 weeks |
| **Current State** | El motor es estrictamente single-player local. No hay soporte para múltiples jugadores locales. |
| **Problem** | No es posible implementar modos cooperativos locales (2 jugadores en misma máquina). |
| **Suggested Solution** | (1) Segundo jugador con joystick/gamepad. (2) Sistema de split-screen o shared-screen con cámara que abarca ambos jugadores. (3) Sistema de respawn cooperativo. (4) Segundo set de inputs en InputManager. |
| **Acceptance Criteria** | 2 jugadores locales funcionales. Split-screen o shared-screen. Respawn cooperativo. |
| **Dependencies** | `input_manager.py`, `camera.py`, `player.py` |
| **Academic Value** | **Multiplayer architecture**, **split-screen rendering**, **local coop patterns**. |

#### P2-119: Editor de Niveles Integrado (TOOLS)

| Field | Value |
|-------|-------|
| **Category** | Tools & Editors |
| **Priority** | P2 |
| **Status** | ❌ **NOT IMPLEMENTED** (existe esqueleto en `stage_wizard_scene.py`) |
| **Effort** | 4-6 weeks |
| **Current State** | `StageWizardScene` existe como esqueleto pero no es funcional. Los niveles solo se pueden crear con Tiled externo. |
| **Problem** | Los estudiantes deben aprender Tiled + formato TMX para crear niveles. No hay herramienta de edición in-game. |
| **Suggested Solution** | Completar `StageWizardScene` con: (1) tilemap painter, (2) entity placer, (3) collision zone editor, (4) export a TMX. |
| **Acceptance Criteria** | Estudiante puede crear un nivel funcional sin salir del juego. Exportar a TMX compatible con StageLoader. |
| **Dependencies** | `stage_wizard_scene.py`, `stage_loader.py` |
| **Academic Value** | **Tool development**, **level design workflows**, **editor architecture**. |

---

### 3.6 P3 — Low Priority

#### P3-122: Netcode Core — UDP Multiplayer Foundation (NET)

| Field | Value |
|-------|-------|
| **Category** | Engine Architecture |
| **Priority** | P3 |
| **Status** | ❌ **NOT IMPLEMENTED** |
| **Effort** | 6-10 weeks |

(Content unchanged from previous version.)

#### P3-123: Replay & Spectator System (NET)

| Field | Value |
|-------|-------|
| **Category** | Engine Architecture |
| **Priority** | P3 |
| **Status** | ❌ **NOT IMPLEMENTED** |

(Content unchanged from previous version.)

#### P3-124: WebAssembly Export Target (DIST)

| Field | Value |
|-------|-------|
| **Category** | Engine Architecture |
| **Priority** | P3 |
| **Status** | ❌ **NOT IMPLEMENTED** |

(Content unchanged from previous version.)

#### P3-125: Code Obfuscation & IP Protection (DIST)

| Field | Value |
|-------|-------|
| **Category** | Engine Architecture |
| **Priority** | P3 |
| **Status** | ❌ **NOT IMPLEMENTED** |

(Content unchanged from previous version.)

---

## 4. Vision — Legacy Academic Framework V2

### 4.1 V2 Purpose

Transformar Legacy of InFest de un **prototipo funcional V1** a un **motor profesional para Metroidvania/scroll lateral 2D** con:

- **Rendimiento GPU**: Sprite batching, post-processing multi-res, object pooling
- **Arquitectura moderna**: ECS opcional, plugin system, lazy loading, DI completa
- **Calidad de código**: Type hints estrictos, benchmarks, sin anti-patrones
- **Extensibilidad**: Plugins, data-driven enemies, editor de niveles integrado
- **Calidad académica**: Documentación viva, tests de integración, profiling integrado

### 4.2 V2 Core Principles

1. **GPU-first rendering** — Todo el renderizado debe ir a GPU cuando sea posible
2. **Data-Oriented Design** — Los datos y la lógica deben estar separados
3. **Zero global state** — No más singletons, no más lambdas globales
4. **Plugin architecture** — El core debe ser extensible sin modificarlo
5. **Measurable performance** — Benchmarks obligatorios para cada optimización
6. **Backward compatibility** — Todo el código V1 debe seguir funcionando

### 4.3 V2 Architecture Diagram (Propuesta)

```
src/
├── engine/
│   ├── core/           # (V1 + mejoras) GameContext, EventBus, Settings
│   ├── render/         # 🔺 NUEVO: SpriteBatch, RenderLayer, PostProcessStack, SurfacePool
│   ├── scene/          # (V1) SceneManager, BaseScene, Transitions
│   ├── scenes/         # (V1) 32 scenes
│   ├── input/          # (V1 + mejoras) InputStack con capas
│   ├── audio/          # (V1 + mejoras) AudioBackend abstraction
│   ├── ui/             # (V1) HUD, MessageBox, etc.
│   └── utils/          # (V1) AssetLoader (V2 async), SpriteSheet, MathUtils
│
├── framework/
│   ├── entities/       # (V1 + V2 ECS wrapper) Player, Enemy* + EntityECS
│   ├── stage/          # (V1) StageLoader, Camera, Collision, etc.
│   ├── vfx/            # (V1) Particles, Lighting, Fog, Weather
│   ├── ui/             # (V1) Dialogue, Tutorial, LearningOverlay
│   ├── processing/     # (V1) FilterTools, VisionTools, etc.
│   └── ecs/            # 🔺 NUEVO: ECS core (Entity, Component, System)
│
├── plugins/            # 🔺 NUEVO: Plugin discovery directory
│
└── stages/             # (V1) Stage0, Boss Venado, student stages
```

---

## 5. V2 Implementation Phases

### Phase 1 (Foundation — 8-12 weeks)
**Objetivo:** Resolver los cuellos de botella de rendimiento y arquitectura.

| Item | Effort | Dependencies |
|------|--------|-------------|
| P0-004: Sprite Batch System + Render Pipeline | 3-4 weeks | pygame-ce 2.5+ |
| P0-005: Surface Object Pool | 2-3 weeks | profiling tools |
| P0-006: Post-Processing Pipeline (Multi-Res) | 2-3 weeks | SurfacePool |
| P0-007: State Container (PlayerState) | 1-2 weeks | player.py |
| P0-008: Eliminar globales (_emit, _get_bus) | 1 week | player.py, enemy_base.py |
| P1-01: Benchmark Suite | 2-3 weeks | pytest-benchmark |
| P1-04: Lazy Loading System | 1-2 weeks | entity_factory.py |
| P1-08: Type Hints + mypy strict | 2-3 weeks | pyproject.toml |
| **Total Phase 1** | **14-21 weeks** | |

### Phase 2 (Architecture — 10-14 weeks)
**Objetivo:** ECS, Plugins, y mejoras arquitectónicas mayores.

| Item | Effort | Dependencies |
|------|--------|-------------|
| P1-02: ECS Prototype (Position, Velocity, Sprite, Health, AI) | 4-6 weeks | numpy |
| P1-03: Plugin System (hooks + manager) | 3-5 weeks | importlib |
| P1-05: Input Stack (UI vs Gameplay layers) | 1-2 weeks | input_manager.py |
| P1-06: Audio Backend Abstraction | 2-3 weeks | audio_manager.py |
| P1-09: Singleton Removal (Inventory) | 1 week | inventory.py |
| P1-10: Asset Pipeline (async + atlas) | 3-4 weeks | asset_loader.py |
| P2-116: EventBus Audit + EventMap | 1-2 weeks | events.py |
| **Total Phase 2** | **16-25 weeks** | |

### Phase 3 (Tools & Content — 6-10 weeks)
**Objetivo:** Herramientas para estudiantes y creadores de contenido.

| Item | Effort | Dependencies |
|------|--------|-------------|
| P2-117: Data-Driven Enemies (YAML blueprints) | 2-3 weeks | entity_factory.py |
| P2-119: Editor de Niveles (Wizard) | 4-6 weeks | stage_loader.py |
| P2-118: Couch Co-op (2P local) | 4-6 weeks | input, camera, player |
| P2-04/05/79: Bestiario, Speedrun, Achievements | ✅ Done | — |
| **Total Phase 3** | **10-15 weeks** | |

### Phase 4 (Advanced Features — 12-20 weeks)
**Objetivo:** Multiplayer, Replay, Web Export.

| Item | Effort | Dependencies |
|------|--------|-------------|
| P3-122: Netcode UDP | 6-10 weeks | socket, msgpack |
| P3-123: Replay System | 3-5 weeks | speedrun_mode.py |
| P3-124: WebAssembly Export | 8-12 weeks | pyodide |
| P3-125: Code Obfuscation | 2-3 weeks | Nuitka |
| **Total Phase 4** | **19-30 weeks** | |

### V2 Total Estimated Effort: **59-91 weeks** (1-2 years)

---

## 6. Verification Checklist (V2)

### 6.1 Performance Benchmarks

- [ ] 2000+ sprites animados a 60 FPS estables (Sprite Batch)
- [ ] <5 MB/s de alloc sostenido (Surface Pool)
- [ ] 3+ filtros post-process simultáneos ≥55 FPS (Multi-Res)
- [ ] Startup time <1.5s cold (Lazy Loading)
- [ ] Zero micro-stutters por GC en gameplay normal

### 6.2 Architecture

- [ ] ECS funcional: 5+ componentes, 3+ sistemas, 2x iteración vs OOP
- [ ] Plugin cargado sin modificar core (ej: nuevo filtro)
- [ ] InputStack con capas funcionales
- [ ] AudioBackend con NullBackend para CI
- [ ] Zero lambdas globales `_emit`
- [ ] Inventory sin singleton

### 6.3 Code Quality

- [ ] `mypy --strict` pasa en todo src/
- [ ] Cobertura de tests >70%
- [ ] Benchmarks en CI
- [ ] EventMap documentado

### 6.4 Features

- [ ] Data-driven enemy via YAML blueprint
- [ ] Editor de niveles in-game funcional
- [ ] Couch co-op 2 jugadores (opcional)

---

## 7. Current Status vs V2 Target

| Aspect | V1 (Current) | V2 Target | Gap |
|--------|-------------|-----------|-----|
| **Rendering** | CPU blit (~800 sprites) | GPU batch (2000+ sprites) | 🔴 Grande |
| **Memory** | 15-30 MB/s alloc, GC stutters | <5 MB/s, zero stutters | 🔴 Grande |
| **Post-Processing** | Full-res, <35 FPS con 3 filtros | Multi-res, ≥55 FPS con 3 filtros | 🔴 Grande |
| **Architecture** | OOP jerárquico | ECS opcional + OOP wrappers | 🟡 Medio |
| **Extensibility** | Sin plugins | Plugin system con 5 hooks | 🔴 Grande |
| **Input** | Plano, sin capas | InputStack con prioridades | 🟡 Medio |
| **Audio** | Acoplado a pygame.mixer | Backend abstraction | 🟡 Medio |
| **Startup** | ~3.4s | <1.5s | 🟡 Medio |
| **Type Safety** | Parcial | mypy strict | 🟡 Medio |
| **Global State** | Singleton Inventory, _emit lambda | DI completa | 🟡 Medio |
| **Assets** | Síncrono, archivos sueltos | Async, empaquetado | 🟡 Medio |
| **Data-Driven** | Solo código | YAML blueprints | 🟡 Medio |
| **Multiplayer** | Solo single-player | Couch co-op (P2) + Netcode (P3) | 🟢 Lejano |
| **Tools** | Tiled externo | Editor in-game | 🟡 Medio |
| **Web Export** | No | pyodide (P3) | 🟢 Lejano |

---

## 8. V2 Architecture Comparison

| Aspect | Godot 4 | Unity 2D | Legacy V1 | Legacy V2 (Target) |
|--------|---------|----------|-----------|-------------------|
| **Render** | GPU (Vulkan/GL) | GPU (DX/GL) | CPU blit | GPU batch |
| **ECS** | ✅ Built-in | ✅ DOTS | ❌ OOP | ✅ Optional |
| **Plugins** | ✅ GDScript/C# | ✅ C# | ❌ None | ✅ Hook system |
| **Pooling** | ✅ Built-in | ✅ Built-in | ❌ None | ✅ SurfacePool |
| **Profiling** | ✅ Built-in | ✅ Profiler | ❌ None | ✅ Benchmark suite |
| **Multiplayer** | ✅ Built-in | ✅ Mirror/Photon | ❌ None | ✅ Couch (P2) + UDP (P3) |
| **Startup** | <2s | <5s | ~3.4s | <1.5s |
| **Sprites 60fps** | 5000+ | 10000+ | ~800 | 2000+ |
| **LOC** | ~1.5M | ~3M | ~29K | ~35K |
| **Target** | General 2D/3D | General 2D/3D | Metroidvania/Scroll | **Best Metroidvania Framework** |

---

## Appendix A: Implementation Status Summary

### A.1 By Category (Updated)

| Category | Total Items | Implemented | Not Implemented | % Done |
|----------|-------------|-------------|-----------------|--------|
| **Already Done** | 10 systems | 10 | 0 | 100% |
| **P0 — Blockers** | 11 | 3 | 8 | 27% |
| **P1 — High Priority** | 41 | 1 | 40 | 2% |
| **P2 — Medium Priority** | 92 | 4 | 88 | 4% |
| **P3 — Low Priority** | 49 | 0 | 49 | 0% |
| **TOTAL** | **203** | **18** | **185** | **9%** |

### A.2 Items Already Implemented (8 items)

| Roadmap Item | System | Evidence |
|--------------|--------|----------|
| **P0-01** | Documentación actualizada | `05_ENEMY_SPEC.md` cubre 8 tipos + Boss; docs 03/22/04 corregidos |
| **P0-02** | WeatherSystem desde TMX | `src/framework/vfx/weather_system.py` |
| **P0-03** | LearningOverlay (F2-F10) | `src/framework/ui/learning_overlay.py` |
| **P1-07** | Enemy scripting (9 types) | `src/framework/entities/enemy_*.py` |
| **P2-04** | Bestiary UI | `src/framework/entities/bestiary.py`, `src/engine/scenes/bestiary_scene.py` |
| **P2-05** | Speedrun UI | `src/framework/stage/speedrun_mode.py` |
| **P2-79** | Achievement System | `src/engine/core/achievements.py`, `src/engine/scenes/achievement_scene.py` |
| **P2-115** | No Monetization | Design decision followed |

### A.3 New Items Added in v3.0.0 (from 2026-07-16 Code Audit)

| Item | Priority | Category | Description |
|------|----------|----------|-------------|
| **P0-004** | P0 | Performance | Sprite Batch System (elevated from P2-116) |
| **P0-005** | P0 | Performance | Surface Object Pool (elevated from P2-117) |
| **P0-006** | P0 | Performance | Post-Processing Multi-Res (elevated from P2-118) |
| **P0-007** | P0 | Code Quality | PlayerState dataclass |
| **P0-008** | P0 | Code Quality | Eliminar lambdas globales _emit |
| **P1-01** | P1 | Performance | Benchmark Suite |
| **P1-02** | P1 | Architecture | ECS Prototype (elevated from P2-120) |
| **P1-03** | P1 | Architecture | Plugin System (elevated from P2-121) |
| **P1-04** | P1 | Architecture | Lazy Loading (elevated from P2-119) |
| **P1-05** | P1 | Architecture | Input Stack con capas |
| **P1-06** | P1 | Architecture | Audio Backend Abstraction |
| **P1-08** | P1 | Code Quality | Type Hints + mypy strict |
| **P1-09** | P1 | Code Quality | Singleton Removal (Inventory) |
| **P1-10** | P1 | Architecture | Asset Pipeline (async + atlas) |
| **P2-116** | P2 | Code Quality | EventBus Audit + EventMap |
| **P2-117** | P2 | AI/ARC | Data-Driven Enemies (YAML blueprints) |
| **P2-118** | P2 | NET | Couch Co-op Local Multiplayer |

---

**Document Version:** 3.0.0  
**Last Updated:** 2026-07-16  
**Next Review:** After Phase 1 V2 completion  

---

## 🔗 Documentos Relacionados

- [[51_IMPLEMENTATION_AUDIT.md|Implementation Audit]]
- [[03_ARCHITECTURE.md|Architecture]]
- [[04_PLAYER_SPEC.md|Player Specification]]
- [[05_ENEMY_SPEC.md|Enemy Specification]]
- [[52_MULTIDISCIPLINARY_AUDIT.md|Multidisciplinary Audit]]