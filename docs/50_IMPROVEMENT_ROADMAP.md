---
document_id: "LOI-ROADMAP-050"
title: "Legacy of InFest — Improvement Roadmap & V2 Architecture"
aliases: ["Improvement Roadmap", "50 Improvement Roadmap", "V2 Architecture"]
tags: ["improvement", "roadmap", "architecture", "v2", "planning"]
description: "Complete architecture transformation: from V1 monolithic prototype to V2 modular multi-engine platform"
source: "docs/50_IMPROVEMENT_ROADMAP.md"
date_processed: "2026-07-16"
---

# Legacy of InFest — Improvement Roadmap & V2 Architecture

**Document ID:** LOI-ROADMAP-050  
**Version:** 4.0.0  
**Status:** Official — V1 Baseline + V2 Multi-Engine Architecture  
**Audience:** Professor, Teaching Assistants, AI coding assistants, Architects

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [V1 Current Implementation Status](#2-v1-current-implementation-status)
3. [V1 Code Quality Assessment](#3-v1-code-quality-assessment)
4. [V1 Architectural Problems Detected](#4-v1-architectural-problems-detected)
5. [V2 Proposed Architecture: Multi-Engine Design](#5-v2-proposed-architecture-multi-engine-design)
6. [Module Specifications](#6-module-specifications)
7. [Design Patterns Applied](#7-design-patterns-applied)
8. [Implementation Phases](#8-implementation-phases)
9. [V1 vs V2 Comparison](#9-v1-vs-v2-comparison)
10. [Game Types Possible After V2](#10-game-types-possible-after-v2)
11. [V2 Verification Checklist](#11-v2-verification-checklist)
12. [Complete Improvement Item List](#12-complete-improvement-item-list)
13. [References](#13-references)

---

## 1. Executive Summary

### 1.1 Current State (V1)

**Legacy of InFest V1** es un prototipo funcional de ~29,000 LOC con 464+ tests, 32 escenas, 25 estados de jugador, 9 tipos de enemigos, sistema de partículas, iluminación, post-procesamiento, y más. **Funciona, pero NO escala.**

| Métrica | Valor |
|---------|-------|
| Archivos Python | ~210 |
| LOC | ~29,000 |
| Tests | 464+ |
| Player States | 25 |
| Enemy Types | 9 |
| Scenes | 32 |
| Score General | **5.6/10** |

### 1.2 Roadmap Summary

| Category | Items | P0 | P1 | P2 | P3 | Effort |
|----------|-------|----|----|----|----|--------|
| **loi-core** | 12 | 4 | 4 | 3 | 1 | 12-20 weeks |
| **loi-math** | 4 | 0 | 1 | 2 | 1 | 4-8 weeks |
| **loi-physics** | 5 | 1 | 2 | 1 | 1 | 6-10 weeks |
| **loi-render** | 10 | 3 | 3 | 2 | 2 | 14-22 weeks |
| **loi-audio** | 4 | 0 | 2 | 1 | 1 | 4-8 weeks |
| **loi-vfx** | 6 | 0 | 2 | 3 | 1 | 8-14 weeks |
| **loi-framework** | 14 | 0 | 4 | 6 | 4 | 16-28 weeks |
| **loi-tools** | 5 | 0 | 1 | 2 | 2 | 8-14 weeks |
| **Code Quality** | 12 | 2 | 4 | 4 | 2 | 10-18 weeks |
| **Content** | 3 | 0 | 1 | 1 | 1 | 2-4 weeks |
| **Documentation** | 2 | 1 | 1 | 0 | 0 | 1 week |
| **TOTAL** | **77** | **11** | **25** | **25** | **16** | **85-148 weeks** |

**Note:** Items reducidos de 203 a 77 porque ahora están agrupados por módulo en lugar de prioridad. Cada módulo es un paquete pip-installable independiente.

### 1.3 Key Architectural Decision

**SÍ, es mejor tener motores independientes para cada área.**

| Motor | Propósito | Dependencias | Tamaño estimado |
|-------|-----------|--------------|-----------------|
| `loi-math` | Matemáticas puras (vectores, matrices, curvas, ruido) | Ninguna | ~2,000 LOC |
| `loi-physics` | Física (gravedad, colisiones AABB, spatial grid) | loi-math | ~3,000 LOC |
| `loi-audio` | Audio (backends: pygame, null, sdl2) | Ninguna | ~1,500 LOC |
| `loi-render` | Renderizado (SpriteBatch, SurfacePool, PostFX, Camera) | loi-math | ~5,000 LOC |
| `loi-vfx` | Efectos visuales (partículas, luz, clima, fog) | loi-render | ~4,000 LOC |
| `loi-core` | Core engine (EventBus, SceneManager, DI, Input, Plugin) | Ninguna | ~4,000 LOC |
| `loi-framework` | Framework Metroidvania (Player, Enemies, Stage, HUD, ECS) | Todos los anteriores | ~8,000 LOC |
| `loi-tools` | Herramientas (Editor, Benchmarks, WebExport) | loi-framework | ~3,000 LOC |
| `legacy-game` | El juego (stages, contenido específico) | loi-framework | ~2,000 LOC |
| **Total** | | | **~32,500 LOC** |

---

## 2. V1 Current Implementation Status

### 2.1 Fully Implemented Systems ✅

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

### 2.2 V1 Architecture (Current)

```
src/
  engine/     (52 files)  ← Core + Scenes + Audio + Input + UI
  framework/  (43 files)  ← Entities + Stage + VFX + UI + Processing
  stages/     (2 stages)  ← Stage0, Boss Venado

⚠️ ACoplamiento CRÍTICO:
  engine/scenes/ ←importa→ framework/entities/
  framework/entities/ ←importa→ engine/core/
  → GRAFO CÍCLICO DE DEPENDENCIAS
```

---

## 3. V1 Code Quality Assessment

Evaluación basada en auditoría de código de 22+ archivos clave (Julio 2026).

| Aspecto | Score | Evidencia | Problema |
|---------|-------|-----------|----------|
| **Architecture** | ⚠️ 6/10 | OOP jerárquico, sin ECS, sin plugin system, engine↔framework acoplados | 🔴 Acoplamiento cíclico |
| **Rendering** | ⚠️ 4/10 | CPU-bound blitting, ~800 sprite limit, sin GPU batch | 🔴 Cuello de botella #1 |
| **Memory** | ⚠️ 5/10 | Sin object pooling, GC pressure 15-30 MB/s, micro-stutters | 🔴 GC pauses |
| **Startup** | ⚠️ 5/10 | ~3.4s por imports pesados (scipy, sklearn, numpy) | 🟡 Lento |
| **Modularity** | ✅ 7/10 | DI con GameContext, pero globales ocultos (_emit, _get_bus) | 🔴 Service Locator anti-pattern |
| **Type Safety** | ⚠️ 5/10 | Type hints parciales, `Any` en muchos lados, `TYPE_CHECKING` | 🟡 Bugs silenciosos |
| **Test Coverage** | ✅ 7/10 | 464+ tests, pero faltan benchmarks de rendimiento | 🟡 Sin métricas |
| **Extensibility** | ❌ 3/10 | Sin plugin system, sin hooks API, sin data-driven config | 🔴 No extensible |
| **StageScene** | ❌ 2/10 | God Object de 812 líneas, 30+ subsistemas, 42 imports | 🔴 Mantenible |
| **GameContext** | ⚠️ 5/10 | Crecimiento sin control, mezcla SceneContext con StageContext | 🟡 DI débil |
| **Overall V1** | ⚠️ **5.6/10** | **Funcional pero necesita re-arquitectura total para escalar** | |

### 3.1 Code Smells Detectados

| # | Code Smell | Archivo | Línea | Impacto |
|---|------------|---------|-------|---------|
| 1 | Lambda global `_emit` atada a `_get_bus()` | `player.py` | 23 | Dependencia oculta, no testeable |
| 2 | Lambda global `_emit` atada a `_get_bus()` | `enemy_base.py` | 20 | Dependencia oculta, no testeable |
| 3 | Singleton `Inventory` con `__new__` | `inventory.py` | 73-77 | Estado global, no testeable |
| 4 | God Object `StageScene` (812 LOC) | `stage_scene.py` | 50-812 | Mantenibilidad, viola SRP |
| 5 | Player con ~40 atributos sueltos | `player.py` | 138-220 | Sin cohesión, difícil de serializar |
| 6 | `set_default_bus()` global | `event_bus.py` | 116-119 | Service Locator anti-pattern |
| 7 | `_default_bus` module-level | `event_bus.py` | 113 | Estado global mutable |
| 8 | Import de scipy/sklearn en startup | `entity_factory.py` | 42 | ~3.4s de arranque extra |
| 9 | `app._draw()` hace blit directo | `app.py` | 107-118 | CPU-bound total, sin batching |
| 10 | AudioManager acoplado a pygame.mixer | `audio_manager.py` | 21-28 | No portable, no testeable sin display |

---

## 4. V1 Architectural Problems Detected

### Problem #1: 🔴 Acoplamiento Cíclico Engine ↔ Framework

```python
# DIRECCIÓN ACTUAL (CÍCLICA):
engine/scenes/  ──importa──→  framework/entities/  (stage_wizard_scene.py)
framework/entities/  ──importa──→  engine/core/     (player.py: _get_bus)

# DIRECCIÓN CORRECTA (ACÍCLICA):
core  →  render + audio + input  →  framework  →  game
```

**Impacto:** No se puede usar `engine/` sin `framework/`. No se puede testear Player sin inicializar EventBus global.

### Problem #2: 🔴 God Object StageScene (812 LOC)

`StageScene` en `src/framework/scenes/stage_scene.py` sabe de TODO:

```python
class StageScene(BaseScene):
    def __init__(self, ...):
        self._collision = CollisionSystem()
        self._hazards = HazardSystem()
        self._progression = ProgressionSystem()
        self._drawing = DrawingSystem()
        self._particle_system = ParticleSystem()
        self._damage_numbers = DamageNumberManager()
        self._post_processing = PostProcessing()
        self._ambient_particles = AmbientParticleSystem()
        self._weather = WeatherSystem()
        self._trail_system = TrailSystem()
        self._lighting = LightSystem()
        self._dynamic_music = DynamicMusicSystem()
        self._tutorial = TutorialOverlay()
        self._learning = LearningOverlay()
        self._minimap = Minimap()
        self._achievements = AchievementSystem.get_instance()
        self._bestiary = Bestiary.get_instance()
        self._speedrun = SpeedrunTimer()
        self._dialogue = DialogueSystem()
        self._sfx_handlers = {...}
        self._vfx_handlers = {...}
        # 30+ subsistemas en una sola clase
```

**Impacto:** Violación del **Single Responsibility Principle**. Cualquier cambio en cualquier subsistema requiere modificar StageScene.

### Problem #3: 🟡 Player State Fragmentado (40 atributos sueltos)

```python
class Player:
    def __init__(self, spawn_position):
        self.velocity = Vector2(0, 0)
        self.is_grounded = False
        self._coyote_counter = 6
        self._jump_cut_applied = False  
        self._state_instance = IdleState()
        self._attack_timer = 0.0
        self._attack_active_frames = []
        self._attack_current_frame = 0
        self._active_hitbox = None
        self._hitbox_consumed = False
        self._cooldown_timer = 0.0
        self.combo_count = 0
        self.combo_timer = 0.0
        self.last_attack_type = ""
        self.special_meter = 0.0
        self._slide_speed = 300.0
        self._air_dash_count = 0
        self._dash_timer = 0.0
        self._invincibility_timer = 0.0
        self._knockback_timer = 0.0
        # ... ~40 atributos total
```

**Impacto:** No se puede serializar, no se puede resetear al morir sin recrear el objeto, difícil de testear.

### Problem #4: 🔴 Service Locator Anti-Pattern

```python
# player.py
from src.engine.core.event_bus import _get_bus as _bus
_emit = lambda *a, **kw: _bus().emit(*a, **kw)
```

**Impacto:** Dependencia oculta, no testeable, no se puede tener múltiples instancias de EventBus.

### Problem #5: 🟡 GameContext sin Control de Crecimiento

```python
class GameContext:
    def __init__(self, input_manager, audio_manager, scene_manager, 
                 event_bus, clock, save_manager):
        # Cada nuevo feature agrega un parámetro aquí
```

**Solución:** Contextos especializados:
- `SceneContext`: Solo input, audio, events (para menús, demos)
- `StageContext`: SceneContext + physics, collision, stage_data (para gameplay)

---

## 5. V2 Proposed Architecture: Multi-Engine Design

### 5.1 Philosophy: Unix Philosophy for Game Engines

> **"Do one thing and do it well."**

Cada motor es un paquete Python independiente con:
- **API pública clara** (interfaces abstractas)
- **Cero dependencias circulares**
- **Versionado semántico** (semver)
- **pip-installable** individualmente
- **Testeable de forma aislada**

### 5.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          LEGACY OF INFEST V2                              │
│                                                                           │
│  DEPENDENCY DIRECTION:  →  (siempre hacia la derecha)                    │
│                                                                           │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │ loi-math │  │loi-physics│  │loi-render│  │ loi-vfx  │  │loi-fwk  │  │
│  │          │  │           │  │          │  │          │  │         │  │
│  │ Vector2  │→ │ Gravity   │  │ Sprite   │  │ Particle │  │ Player  │  │
│  │ Matrix3  │  │ Collision │  │ Batch    │  │ Lighting │  │ Enemy   │  │
│  │ Curve    │  │ Spatial   │  │SurfaceP  │  │ Weather  │  │ Stage   │  │
│  │ Noise    │  │ Grid      │  │PostFX    │  │ FogOfWar │  │ HUD     │  │
│  │ ColorSp  │  │ Raycast   │  │Camera2D  │  │ Trail    │  │ ECS     │  │
│  └────┬─────┘  └─────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘  │
│       │              │             │             │             │        │
│       └──────────────┴─────────────┴─────────────┴─────────────┘        │
│                                  ▲                                      │
│  ┌──────────┐  ┌──────────┐      │      ┌──────────┐  ┌───────────┐    │
│  │ loi-core │  │loi-audio │      │      │loi-tools │  │legacy-game│    │
│  │          │  │          │      │      │          │  │           │    │
│  │EventBus  │  │ IAudio   │      │      │ Editor   │  │ Stage0    │    │
│  │SceneMgr  │  │ Pygame   │──────┘      │ Bench    │  │ BossVenado│    │
│  │DI Cont.  │  │ Null     │             │ WebExp   │  │ Students  │    │
│  │ Input    │  │ SDL2     │             │ Profiler │  │           │    │
│  │ Plugin   │  └──────────┘             └──────────┘  └───────────┘    │
│  │ Clock    │                                                           │
│  └──────────┘                                                           │
│                                                                           │
│  DEPENDENCIAS (siempre acíclicas):                                       │
│    loi-math  → (ninguna)                                                  │
│    loi-core  → (ninguna)                                                  │
│    loi-audio → (ninguna)                                                  │
│    loi-physics → loi-math                                                 │
│    loi-render → loi-math                                                  │
│    loi-vfx → loi-render, loi-math                                         │
│    loi-framework → loi-core, loi-math, loi-physics, loi-render, loi-vfx  │
│    loi-tools → loi-framework                                              │
│    legacy-game → loi-framework                                            │
│                                                                           │
│  ✅ NO HAY DEPENDENCIAS CIRCULARES                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Module Descriptions

| # | Module | Name | Purpose | Dependencies | LOC Est. |
|---|--------|------|---------|-------------|----------|
| 1 | `loi-math` | Mathematics Engine | Vectores, matrices, curvas, ruido, colores, estadísticas | Ninguna | ~2,000 |
| 2 | `loi-core` | Core Engine | EventBus, SceneManager, DI Container, Input, Clock, Plugin | Ninguna | ~4,000 |
| 3 | `loi-audio` | Audio Engine | IAudio interface, backends (Pygame, Null, SDL2), SoundBank | Ninguna | ~1,500 |
| 4 | `loi-physics` | Physics Engine | Gravedad, colisiones AABB, spatial grid, raycast, dinámica | loi-math | ~3,000 |
| 5 | `loi-render` | Render Engine | SpriteBatch, SurfacePool, PostFX, Camera2D, TextureAtlas | loi-math | ~5,000 |
| 6 | `loi-vfx` | Visual Effects Engine | Partículas, iluminación, clima, fog of war, trails, water | loi-render, loi-math | ~4,000 |
| 7 | `loi-framework` | Metroidvania Framework | Player, Enemies, Stage, HUD, Dialogue, ECS, AI | Todos ↑ | ~8,000 |
| 8 | `loi-tools` | Tools Suite | StageWizard editor, Benchmarks, WebExport, Profiler | loi-framework | ~3,000 |
| 9 | `legacy-game` | The Game | Stage0, BossVenado, student stages | loi-framework | ~2,000 |
| | **Total** | | | | **~32,500** |

---

## 6. Module Specifications

### 6.1 `loi-math` — Mathematics Engine

**Purpose:** Pure math operations. Zero dependencies. Reusable in ANY Python project.

```
loi-math/
  ├── __init__.py
  ├── vector2.py          # Vector2 class (x, y) with all operations
  ├── matrix3.py          # 3x3 transformation matrix
  ├── curves.py           # Bezier, B-Spline, Catmull-Rom, NURBS
  ├── noise.py            # Perlin noise, simplex noise
  ├── color_spaces.py     # RGB↔HSV↔HSL↔CMYK↔LAB conversions
  ├── interpolation.py    # lerp, ease_in/out, smoothstep, cubic
  ├── statistics.py       # mean, std, histogram, correlation
  └── random.py           # Seeded RNG, distributions

Key classes:
  Vector2(x, y)            # .normalize(), .dot(), .cross(), .length()
  Matrix3()                 # .rotate(), .scale(), .translate()
  BezierCurve(points)       # .sample(t) → Vector2
  PerlinNoise(seed)         # .noise2d(x, y) → float
  ColorRGB(r, g, b)         # .to_hsv() → ColorHSV

pip install loi-math
```

**Migration from V1:**
- `src/engine/utils/math_utils.py` → `loi-math/vector2.py`
- `src/framework/processing/curve_tools.py` → `loi-math/curves.py`
- `src/framework/processing/color_tools.py` → `loi-math/color_spaces.py`

### 6.2 `loi-core` — Core Engine

**Purpose:** Framework-agnostic core. No game logic. Reusable in ANY game type.

```
loi-core/
  ├── __init__.py
  ├── api/                    # Abstract interfaces
  │   ├── irenderer.py        # IRenderer (implementado por loi-render)
  │   ├── iaudio.py           # IAudio (implementado por loi-audio)
  │   ├── iinput.py           # IInput
  │   ├── iscene.py           # IScene
  │   ├── iscenemanager.py    # ISceneManager
  │   └── ieventbus.py        # IEventBus
  ├── event/
  │   ├── event_bus.py        # EventBus con prioridades y tipado
  │   └── events.py           # Event name constants
  ├── scene/
  │   ├── base_scene.py       # BaseScene (implementa IScene)
  │   ├── scene_manager.py    # SceneManager (push/pop/replace)
  │   └── transitions.py      # Fade, Wipe, Slide transitions
  ├── di/
  │   └── service_container.py # ServiceContainer (DI)
  ├── input/
  │   ├── input_manager.py    # InputManager
  │   ├── action_map.py       # Action bindings
  │   └── input_stack.py      # Layered input (UI > Gameplay > Debug)
  ├── plugin/
  │   ├── plugin_manager.py   # Discover, load, hook system
  │   └── plugin_api.py       # Safe API exposed to plugins
  ├── clock.py                # DeltaClock
  └── settings.py             # Global constants

Key classes:
  EventBus                    # subscribe(priority), emit(Event), dispatch()
  SceneManager                # push(), pop(), replace(), stage queue
  ServiceContainer            # register_singleton(), resolve()
  InputStack                  # push_layer(), pop_layer(), layers
  PluginManager               # discover(), load(), trigger_hook()
  DeltaClock                  # tick(), time_scale, fps
  BaseScene(context)          # on_enter(), update(dt), draw(renderer)

pip install loi-core
```

**Migration from V1:**
- `src/engine/core/event_bus.py` → `loi-core/event/event_bus.py` (con tipado fuerte)
- `src/engine/scene/scene_manager.py` → `loi-core/scene/scene_manager.py`
- `src/engine/scene/base_scene.py` → `loi-core/scene/base_scene.py`
- `src/engine/input/input_manager.py` → `loi-core/input/input_manager.py`
- `src/engine/core/clock.py` → `loi-core/clock.py`
- `src/engine/core/settings.py` → `loi-core/settings.py`

### 6.3 `loi-audio` — Audio Engine

**Purpose:** Audio abstraction with swappable backends.

```
loi-audio/
  ├── __init__.py
  ├── iaudio.py               # IAudio interface
  ├── backends/
  │   ├── pygame_backend.py   # Actual: pygame.mixer
  │   ├── null_backend.py     # Silent, for CI/headless
  │   └── sdl2_backend.py     # Future: SDL2_mixer
  ├── sound_bank.py           # Named sound registry
  └── audio_manager.py        # High-level: music, sfx, ambient, dynamic

Key classes:
  AudioManager(backend)        # play_music(), play_sfx(), set_volume()
  PygameAudioBackend()         # Implementación con pygame.mixer
  NullAudioBackend()           # Implementación silenciosa
  SoundBank()                  # load_all(), play(name), cache

pip install loi-audio
```

### 6.4 `loi-physics` — Physics Engine

**Purpose:** 2D physics for platformers. Independent of rendering.

```
loi-physics/
  ├── __init__.py
  ├── vector2.py               # Re-export from loi-math (or standalone)
  ├── gravity.py               # GravitySystem
  ├── collision.py             # AABB collision detection + resolution
  ├── spatial_grid.py          # Spatial hash grid for broad-phase
  ├── raycast.py               # Raycasting
  ├── dynamics.py              # Velocity, acceleration, friction
  └── one_way_platform.py      # One-way platform collision

Key classes:
  GravitySystem(strength)      # apply(dt, velocity)
  CollisionSystem()            # resolve_x(), resolve_y(), collide()
  SpatialGrid(cell_size)       # insert(), get_nearby(), clear()
  RaycastResult(hit, point, normal)  # cast(from, to, collision_rects)
  OneWayPlatform(rect)         # pasable desde abajo

pip install loi-physics
```

**Migration from V1:**
- `src/framework/stage/collision_system.py` → `loi-physics/collision.py`
- `src/framework/entities/player.py` (physics parts) → `loi-physics/gravity.py`

### 6.5 `loi-render` — Render Engine

**Purpose:** High-performance 2D rendering pipeline.

```
loi-render/
  ├── __init__.py
  ├── api/
  │   └── irenderer.py         # IRenderer interface
  ├── backends/
  │   ├── pygame_renderer.py   # Actual: pygame-ce SDL2
  │   ├── null_renderer.py     # Headless
  │   └── opengl_renderer.py   # Future: ModernGL
  ├── pipeline/
  │   ├── render_pipeline.py   # Layers, ordering, composition
  │   └── render_command.py    # RenderCommand dataclass
  ├── batch/
  │   └── sprite_batch.py      # SpriteBatch (group by texture)
  ├── pool/
  │   └── surface_pool.py      # SurfacePool (reuse surfaces)
  ├── camera/
  │   └── camera2d.py          # Camera2D (follow, parallax, shake)
  ├── postfx/
  │   ├── post_process_stack.py # Chain of effects
  │   ├── bloom.py             # Bloom effect
  │   ├── color_grading.py     # Color grading / colorblind
  │   └── vignette.py          # Vignette effect
  └── atlas/
      └── texture_atlas.py     # TextureAtlas builder

Key classes:
  RenderPipeline(renderer)     # submit(cmd), render()
  SpriteBatch()                # add(cmd), flush(renderer)
  SurfacePool(max_size)        # acquire(w, h), release(surface)
  Camera2D()                   # follow(target), apply(cmd), shake()
  PostProcessStack()           # add_effect(), apply(layer)
  TextureAtlas()               # pack(images), get(id)

pip install loi-render
```

**Migration from V1:**
- `src/engine/core/app.py` (draw parts) → `loi-render/pipeline/render_pipeline.py`
- `src/framework/stage/camera.py` → `loi-render/camera/camera2d.py`
- `src/framework/vfx/post_processing.py` → `loi-render/postfx/`

### 6.6 `loi-vfx` — Visual Effects Engine

**Purpose:** Reusable visual effects for 2D games.

```
loi-vfx/
  ├── __init__.py
  ├── particle/
  │   ├── particle_system.py   # ParticleSystem (emitters, bursts)
  │   ├── emitter.py           # Emitter (position, rate, lifetime)
  │   └── particle.py          # Particle dataclass
  ├── lighting/
  │   ├── light_system.py      # LightSystem (ambient, lights)
  │   └── light_source.py      # LightSource (position, radius, color)
  ├── weather/
  │   └── weather_system.py    # Rain, Snow, Fog, Dust, Embers
  ├── fog_of_war.py            # FogOfWar (revealed areas)
  ├── trail_system.py          # TrailSystem (motion trails)
  ├── water_effect.py          # WaterEffect (sine wave overlay)
  ├── hit_effects.py           # HitEffects (burst on hit)
  └── damage_numbers.py        # DamageNumberManager

Key classes:
  ParticleSystem(pool)         # emit(), update(dt), draw(renderer)
  LightSystem(ambient)         # add_light(), remove_light(), render()
  WeatherSystem(climate)       # rain(), snow(), fog(), update(dt)
  FogOfWar()                   # reveal(rect), is_visible(pos), draw()
  TrailSystem(max_length)      # add_point(pos), draw()
  DamageNumberManager()        # spawn(text, pos), update(dt), draw()

pip install loi-vfx
```

### 6.7 `loi-framework` — Metroidvania Framework

**Purpose:** Complete game framework for Metroidvania/2D platformers.

```
loi-framework/
  ├── __init__.py
  ├── ecs/                     # Entity Component System
  │   ├── world.py             # World (entities, components, systems)
  │   ├── entity.py            # Entity (ID)
  │   ├── component.py         # Position, Velocity, Health, Sprite, AI, Collider
  │   └── system.py            # System (abstract), MovementSystem, AISystem
  ├── entities/
  │   ├── player.py            # Player (wraps PlayerState + ECS)
  │   ├── player_state.py      # PlayerState dataclass (datos puros)
  │   ├── player_states.py     # State Machine (Idle, Walk, Jump, etc.)
  │   ├── enemy_base.py        # EnemyBase + AI Strategy
  │   ├── enemy_walker.py      # WalkerStrategy
  │   ├── enemy_flying.py      # FlyingStrategy
  │   ├── enemy_shooter.py     # ShooterStrategy
  │   ├── boss_base.py         # BossBase (phase manager)
  │   └── blueprint_loader.py  # EnemyBlueprint (YAML → Entity)
  ├── stage/
  │   ├── stage_controller.py  # StageController (orquesta subsistemas)
  │   ├── stage_loader.py      # TMX → StageData
  │   ├── stage_data.py        # StageData dataclass
  │   ├── checkpoint.py        # Checkpoint system
  │   ├── hazard_system.py     # Hazard zones
  │   ├── progression.py       # Progression triggers
  │   ├── drawing_system.py    # Layer-based drawing
  │   └── cutscene_system.py   # Scripted cutscenes
  ├── ui/
  │   ├── hud.py               # HUD (hearts, timer, score)
  │   ├── message_box.py       # Tutorial messages
  │   ├── screen_banner.py     # Stage name intro
  │   ├── minimap.py           # Exploration map
  │   ├── dialogue_system.py   # Branching dialogue
  │   ├── tutorial_overlay.py  # Contextual help
  │   └── learning_overlay.py  # F2-F10 debug toggles
  ├── audio/
  │   └── dynamic_music.py     # DynamicMusicSystem (crossfade)
  ├── ai/
  │   ├── ai_strategy.py       # AIStrategy (abstract)
  │   ├── patrol.py            # PatrolStrategy
  │   ├── chase.py             # ChaseStrategy
  │   ├── shooter.py           # ShooterStrategy
  │   └── predictor.py         # AIPredictor (ML-based)
  └── data/
      ├── achievements.py      # Achievement system
      ├── inventory.py         # Item management
      ├── bestiary.py          # Enemy tracking
      ├── save_manager.py      # Save/load
      └── speedrun_mode.py     # Speedrun timer + ghost

Key classes:
  StageController(world, pipeline, bus)  # load_stage(), update(), draw()
  Player(spawn, bus)                     # update(dt, input, physics)
  PlayerState()                          # Datos puros del jugador
  EnemyBlueprint(data)                   # Crea enemigos desde YAML
  ECS World                              # create_entity(), add_component(), update()
  AIStrategy                             # update(entity, world, dt)

pip install loi-framework
```

### 6.8 `loi-tools` — Tools Suite

**Purpose:** Development tools for the framework.

```
loi-tools/
  ├── __init__.py
  ├── editor/
  │   ├── stage_wizard.py      # In-game level editor
  │   ├── tile_palette.py      # Tile selection UI
  │   └── entity_placer.py     # Entity placement tool
  ├── benchmark/
  │   ├── render_bench.py      # 500/1000/2000 sprites
  │   ├── physics_bench.py     # 100/500/1000 entities
  │   ├── startup_bench.py     # Cold/warm startup
  │   └── memory_bench.py      # Heap allocations
  ├── export/
  │   └── web_exporter.py      # pyodide/pyscript export
  └── profiler/
      ├── frame_profiler.py    # Per-frame timing
      └── memory_profiler.py   # Memory tracking

pip install loi-tools
```

### 6.9 `legacy-game` — The Game

```python
# legacy-game/src/stages/stage0.py
from loi_framework import StageController, StageLoader
from loi_core import SceneContext

class Stage0Scene(BaseScene):
    def __init__(self, context: SceneContext):
        self.controller = StageController(
            world=context.resolve(World),
            pipeline=context.resolve(RenderPipeline),
            event_bus=context.resolve(EventBus),
        )
    
    def on_enter(self):
        self.controller.load_stage(Path("assets/maps/stage0/stage0.tmx"))
    
    def update(self, dt: float):
        self.controller.update(dt)
    
    def draw(self, renderer: IRenderer):
        self.controller.draw()
```

---

## 7. Design Patterns Applied

| Patrón | Dónde | Problema que Resuelve | Estado V1 | Estado V2 |
|--------|-------|-----------------------|-----------|-----------|
| **Strategy** | AI de enemigos | Cambiar comportamiento sin modificar clases | ❌ Hardcodeado | ✅ `AIStrategy` + Blueprints |
| **State** | Player states | Máquina de estados | ✅ Ya existe | ✅ Mejorado con dataclass |
| **Observer** | EventBus | Comunicación desacoplada | ✅ Ya existe | ✅ Tipado + Prioridades |
| **Command** | Input + Replay | Grabar/Reproducir inputs | ❌ No existe | ✅ `InputCommand` |
| **Composite** | Render layers | Jerarquía de render | ❌ app._draw() plano | ✅ `RenderPipeline` capas |
| **Abstract Factory** | Entity creation | Crear sin acoplamiento | ✅ EntityFactory | ✅ + ServiceContainer |
| **Service Locator → DI** | GameContext | Inyección de dependencias | ⚠️ Globales | ✅ `ServiceContainer` |
| **Prototype** | Enemies | Clonar configs | ❌ No existe | ✅ `EnemyBlueprint.spawn()` |
| **Adapter** | Audio backends | Soportar backends | ❌ Acoplado | ✅ `IAudio` + Adapters |
| **Facade** | StageController | Simplificar interfaz compleja | ❌ God Object | ✅ Facade + ECS |
| **Null Object** | Audio, Render | Evitar None checks | ❌ `if audio:` | ✅ `NullAudioBackend` |
| **Pool** | Surfaces, Particles | Reducir allocaciones | ❌ 15-30 MB/s | ✅ `SurfacePool` |
| **Plugin** | Extensions | Extender sin modificar core | ❌ No existe | ✅ `PluginManager` |
| **ECS** | Entidades | Data-Oriented Design | ❌ OOP jerárquico | ✅ `World` + `System` |
| **Value Object** | PlayerState | Datos inmutables | ❌ 40 atributos sueltos | ✅ `PlayerState` dataclass |
| **Layered Architecture** | Toda la app | Separación de concerns | ❌ Acoplamiento cíclico | ✅ 9 módulos independientes |

---

## 8. Implementation Phases

### Phase 1: Foundation (8-12 weeks)
**Objective:** Establish base modules with zero external dependencies.

| Item | Module | Effort | Description |
|------|--------|--------|-------------|
| P0-001 | `loi-math` | 2-3 weeks | Vector2, Matrix3, Curves, Noise, ColorSpaces |
| P0-002 | `loi-core` | 4-6 weeks | EventBus tipado, ServiceContainer, BaseScene, SceneManager, InputStack, PluginManager |
| P0-003 | `loi-audio` | 2-3 weeks | IAudio, PygameBackend, NullBackend, SoundBank |
| P0-004 | Benchmarks | 1-2 weeks | Render, Physics, Startup, Memory benchmarks |
| P0-005 | Type hints | 2-3 weeks | mypy strict en loi-math, loi-core, loi-audio |
| **Total** | | **11-17 weeks** | |

### Phase 2: Performance (6-10 weeks)
**Objective:** GPU-accelerated rendering, memory optimization.

| Item | Module | Effort | Description |
|------|--------|--------|-------------|
| P0-006 | `loi-render` | 3-4 weeks | SpriteBatch, RenderPipeline, Camera2D, SurfacePool |
| P0-007 | `loi-render` | 2-3 weeks | PostProcessStack (Bloom, ColorGrading, Vignette, Multi-Res) |
| P0-008 | `loi-physics` | 2-3 weeks | GravitySystem, CollisionSystem, SpatialGrid, Raycast |
| P1-001 | `loi-core` | 1-2 weeks | Lazy imports (scipy, sklearn, numpy under demand) |
| **Total** | | **8-12 weeks** | |

### Phase 3: Visual Effects (4-6 weeks)
**Objective:** Beautiful effects that don't kill performance.

| Item | Module | Effort | Description |
|------|--------|--------|-------------|
| P1-002 | `loi-vfx` | 2-3 weeks | ParticleSystem, TrailSystem, DamageNumbers |
| P1-003 | `loi-vfx` | 2-3 weeks | LightSystem, WeatherSystem, FogOfWar, WaterEffect |
| P2-001 | `loi-vfx` | 1-2 weeks | HitEffects, AmbientParticles |
| **Total** | | **5-8 weeks** | |

### Phase 4: Framework (8-12 weeks)
**Objective:** Complete Metroidvania framework.

| Item | Module | Effort | Description |
|------|--------|--------|-------------|
| P1-004 | `loi-framework` | 3-4 weeks | PlayerState dataclass, Player refactor, State Machine |
| P1-005 | `loi-framework` | 2-3 weeks | EnemyBase, AIStrategy, BlueprintLoader, 9 enemy types |
| P1-006 | `loi-framework` | 3-4 weeks | ECS World, Component, System, MovementSystem, AISystem |
| P2-002 | `loi-framework` | 2-3 weeks | StageController, StageLoader, Checkpoint, Hazards |
| P2-003 | `loi-framework` | 2-3 weeks | HUD, Dialogue, Tutorial, Minimap, LearningOverlay |
| P2-004 | `loi-framework` | 2-3 weeks | SaveManager, Achievements, Inventory, Bestiary, Speedrun |
| **Total** | | **14-20 weeks** | |

### Phase 5: Tools (4-6 weeks)
**Objective:** Developer tools.

| Item | Module | Effort | Description |
|------|--------|--------|-------------|
| P1-007 | `loi-tools` | 2-3 weeks | StageWizard editor (tile painter, entity placer) |
| P2-005 | `loi-tools` | 2-3 weeks | Benchmark suite automation, CI integration |
| P3-001 | `loi-tools` | 4-6 weeks | WebAssembly export (pyodide) |
| **Total** | | **8-12 weeks** | |

### Phase 6: Migration (4-6 weeks)
**Objective:** Migrate existing V1 game to V2.

| Item | Module | Effort | Description |
|------|--------|--------|-------------|
| P2-006 | `legacy-game` | 2-3 weeks | Stage0 migration (uses loi-framework StageController) |
| P2-007 | `legacy-game` | 1-2 weeks | Boss Venado migration |
| P2-008 | `legacy-game` | 1-2 weeks | Demo scenes migration (13 labs) |
| **Total** | | **4-7 weeks** | |

### Total V2 Effort: **50-75 weeks** (~1-1.5 years)

---

## 9. V1 vs V2 Comparison

### 9.1 Architecture Comparison

| Aspect | V1 (Monolith) | V2 (Multi-Engine) | Gap |
|--------|---------------|-------------------|-----|
| **Modules** | 3 (engine, framework, stages) | 9 (math, core, audio, physics, render, vfx, framework, tools, game) | 🔴 Grande |
| **Dependencies** | Circular (engine↔framework) | Acíclica (siempre hacia la derecha) | 🔴 Crítico |
| **Rendering** | CPU blit (~800 sprites) | GPU batch (2000+ sprites) | 🔴 Grande |
| **Memory** | 15-30 MB/s alloc | <5 MB/s (SurfacePool) | 🔴 Grande |
| **Post-Processing** | Full-res, <35 FPS | Multi-res, ≥55 FPS | 🔴 Grande |
| **Architecture** | OOP jerárquico | ECS opcional + OOP wrappers | 🟡 Medio |
| **StageScene** | God Object 812 LOC | StageController (facade) + ECS Systems | 🔴 Crítico |
| **Player State** | 40 atributos sueltos | PlayerState dataclass (20 fields) | 🟡 Medio |
| **Player Init** | 80 líneas | 20 líneas | 🟡 Medio |
| **Input** | Plano, sin capas | InputStack con prioridades | 🟡 Medio |
| **Audio** | Acoplado a pygame.mixer | IAudio + 3 backends | 🟡 Medio |
| **Startup** | ~3.4s (imports pesados) | <1.5s (lazy loading) | 🟡 Medio |
| **Type Safety** | Parcial, no pasa mypy | mypy strict en todos los módulos | 🟡 Medio |
| **Global State** | Singleton Inventory, _emit lambda | DI completa (ServiceContainer) | 🟡 Medio |
| **Plugins** | No existe | PluginManager + 5 hooks | 🔴 Grande |
| **Data-Driven** | Solo código Python | YAML blueprints + editor visual | 🟡 Medio |
| **Multiplayer** | Solo single-player | Couch co-op (P2) + Netcode (P3) | 🟢 Lejano |
| **Tools** | Tiled externo obligatorio | StageWizard in-game | 🟡 Medio |
| **Web Export** | No | pyodide (P3) | 🟢 Lejano |
| **Reusabilidad** | Solo para este juego | Cualquier Metroidvania | 🔴 Grande |
| **pip install** | No | Sí, cada módulo individualmente | 🔴 Grande |

### 9.2 Compared to Commercial Engines

| Aspect | Godot 4 | Unity 2D | Legacy V1 | Legacy V2 (Target) |
|--------|---------|----------|-----------|-------------------|
| **Render** | GPU (Vulkan/GL) | GPU (DX/GL) | CPU blit | **GPU batch** |
| **ECS** | ✅ Built-in | ✅ DOTS | ❌ OOP | **✅ Optional** |
| **Plugins** | ✅ GDScript/C# | ✅ C# | ❌ None | **✅ Hook system** |
| **Pooling** | ✅ Built-in | ✅ Built-in | ❌ None | **✅ SurfacePool** |
| **Profiling** | ✅ Built-in | ✅ Profiler | ❌ None | **✅ Benchmark suite** |
| **Multiplayer** | ✅ Built-in | ✅ Mirror/Photon | ❌ None | **✅ Couch + UDP (P3)** |
| **Startup** | <2s | <5s | ~3.4s | **<1.5s** |
| **Sprites 60fps** | 5000+ | 10000+ | ~800 | **2000+** |
| **LOC** | ~1.5M | ~3M | ~29K | **~32.5K** |
| **Modular** | Monolítico | Monolítico | Monolítico | **9 módulos independientes** |
| **pip install** | No | No | No | **✅ Sí** |
| **Target** | General 2D/3D | General 2D/3D | Metroidvania | **🏆 Best Metroidvania Framework** |

### 9.3 Key Improvements Summary

| De (V1) | A (V2) | Beneficio |
|---------|--------|-----------|
| Monolito acoplado | 9 módulos independientes | Mantenibilidad, reuso, testing |
| God Object StageScene (812 LOC) | StageController + ECS Systems | SRP, extensibilidad |
| 40 atributos sueltos en Player | PlayerState dataclass | Serialización, testing |
| Lambdas globales (_emit) | EventBus inyectado vía DI | Testeabilidad |
| Singleton Inventory | ServiceContainer | Sin estado global |
| CPU blit (800 sprites) | GPU batch (2000+ sprites) | Rendimiento 2.5x |
| Sin plugins | PluginManager con hooks | Extensibilidad infinita |
| Sin ECS | ECS opcional | Data-Oriented Design |
| Acoplado a pygame.mixer | IAudio + 3 backends | Portabilidad |
| Sin benchmarks | Benchmark suite | Medición objetiva |
| Sin editor de niveles | StageWizard in-game | Productividad estudiantes |

---

## 10. Game Types Possible After V2

### 🟢 DOMINADOS (Scroll Lateral 2D)

| Game Type | Why V2 Excels | Examples |
|-----------|---------------|----------|
| **Metroidvania** 🏆 | ECS + StageController + AIStrategy + Data-Driven Enemies | Hollow Knight, Axiom Verge, Ori |
| **Action Platformer** 🏆 | GPU batch (2000+ sprites), ParticleSystem, PostFX | Mega Man, Cuphead |
| **Precision Platformer** 🏆 | Physics engine, benchmarks, DeltaClock preciso | Celeste, Super Meat Boy |
| **Bullet Hell / Shmup** 🏆 | ECS para 500+ proyectiles, SpriteBatch | Touhou, Enter the Gungeon |
| **Castlevania-like** 🏆 | Inventory + ECS + AIStrategy + Stage progression | Castlevania SOTN |
| **Speedrun Platformer** 🏆 | SpeedrunSystem, ghost data, benchmarks integrados | Dustforce |

### 🟡 POSIBLES con Adaptación (Top-Down)

| Game Type | What's Needed | Effort | Examples |
|-----------|---------------|--------|----------|
| **Top-Down Adventure** | New MovementSystem (8-dir), Camera centrada, AI 360° | 4-6 weeks | Zelda: Link to the Past |
| **Beat 'em Up** | Couch co-op P2, camera multijugador, combo system | 6-8 weeks | Streets of Rage |
| **Dual-Stick Shooter** | ECS proyectiles, input analógico, right stick | 4-6 weeks | Hotline Miami |
| **RPG de Acción (Diablo-like)** | Loot system, procedimental generation, ECS stats | 8-12 weeks | Diablo, Path of Exile |
| **Party Game** | Couch co-op, minijuegos via Plugin system | 6-8 weeks | TowerFall, Duck Game |
| **Souls-like 2D** | Stamina system, AI agresiva, animaciones largas | 4-6 weeks | Salt & Sanctuary |

### 🔴 NO POSIBLES (Requieren reescritura)

| Game Type | Limitation | Examples |
|-----------|------------|----------|
| **Pokémon (RPG por turnos)** ❌ | Sin sistema de batalla por turnos, captura, evolución, movimientos, party management, overworld grid | Pokémon, Persona |
| **JRPG por turnos** ❌ | Sin sistema de turnos, ATB, menú de comandos | Final Fantasy |
| **Estrategia por turnos** ❌ | Sin grid-based movement, pathfinding, sistema de unidades/turnos | Fire Emblem |
| **Estrategia en tiempo real** ❌ | Sin selección de unidades, multi-agent pathfinding, recursos | StarCraft |
| **Juego de Cartas** ❌ | Sin tablero, sistema de reglas, efectos encadenados | Slay the Spire |
| **Novela Visual** ❌ | Sin branching narrativo complejo, galería CG, guardado por capítulos | Doki Doki |
| **Racing** ❌ | Sin física vehicular, sistema de turbos, derrape | Mario Kart |
| **Fighting Game** ❌ | Sin 1v1 mechanics, frame data, motion inputs | Street Fighter |

---

## 11. V2 Verification Checklist

### 11.1 Architecture

- [ ] 9 módulos independientes con dependencias acíclicas
- [ ] `pip install loi-core` funciona sin pygame
- [ ] `pip install loi-render` funciona con pygame
- [ ] `pip install loi-framework` funciona con todas las dependencias
- [ ] ServiceContainer registra todas las dependencias sin circularidad
- [ ] Cero lambdas globales `_emit` en todo el código
- [ ] Cero singletons en todo el código
- [ ] Cero `_get_bus()` o `set_default_bus()` en loi-framework

### 11.2 StageScene

- [ ] StageScene < 200 líneas (delegado a StageController)
- [ ] StageController no < 400 líneas (orquesta subsistemas)
- [ ] Cada subsistema es testeable de forma aislada
- [ ] ECS opcional funcional (World + Component + System)

### 11.3 Performance Benchmarks

- [ ] 2000+ sprites animados a 60 FPS estables (Sprite Batch)
- [ ] <5 MB/s de alloc sostenido (Surface Pool)
- [ ] 3+ filtros post-process simultáneos ≥55 FPS (Multi-Res)
- [ ] Startup time <1.5s cold (Lazy Loading)
- [ ] Zero micro-stutters por GC en gameplay normal
- [ ] Benchmarks en CI con línea base documentada

### 11.4 Player

- [ ] PlayerState dataclass con ~20 fields
- [ ] Player.__init__ < 20 líneas
- [ ] Serialización a JSON en < 10 líneas
- [ ] Reset al checkpoint en < 5 líneas

### 11.5 Code Quality

- [ ] `mypy --strict` pasa en los 9 módulos
- [ ] Cobertura de tests >80%
- [ ] Benchmarks en CI
- [ ] Docstrings en todas las clases públicas

### 11.6 Features V2

- [ ] Plugin funcional de ejemplo (nuevo filtro de imagen)
- [ ] Data-driven enemy via YAML blueprint
- [ ] Editor de niveles in-game funcional (StageWizard)
- [ ] Couch co-op 2 jugadores (opcional Phase 5)
- [ ] Audio NullBackend para CI

---

## 12. Complete Improvement Item List

### 12.1 Items Already Implemented (8 items from V1)

| ID | Name | Module | Evidence |
|----|------|--------|----------|
| ✅ | P0-01 | Documentation | Docs actualizados, 05_ENEMY_SPEC.md, 03_ARCHITECTURE.md |
| ✅ | P0-02 | WeatherSystem | `loi-vfx/weather_system.py` (155 LOC) |
| ✅ | P0-03 | LearningOverlay | `loi-framework/ui/learning_overlay.py` (209 LOC) |
| ✅ | P1-07 | 9 Enemy Types | `loi-framework/entities/enemy_*.py` (8 + Boss) |
| ✅ | P2-04 | Bestiary UI | `loi-framework/data/bestiary.py` + scene |
| ✅ | P2-05 | Speedrun UI | `loi-framework/data/speedrun_mode.py` |
| ✅ | P2-79 | Achievement System | `loi-framework/data/achievements.py` + scene |
| ✅ | P2-115 | No Monetization | Design decision followed |

### 12.2 P0 — Critical (Must fix before V2 launch)

| ID | Name | Module | Effort | Description |
|----|------|--------|--------|-------------|
| **P0-001** | **Vector2, Matrix3, Curves** | `loi-math` | 2-3 weeks | Extraer matemáticas puras a módulo independiente |
| **P0-002** | **EventBus tipado + DI** | `loi-core` | 4-6 weeks | EventBus con prioridades, ServiceContainer, SceneManager, InputStack, PluginManager |
| **P0-003** | **IAudio + NullBackend** | `loi-audio` | 2-3 weeks | Desacoplar audio de pygame.mixer, NullBackend para CI |
| **P0-004** | **Benchmark Suite** | `loi-tools` | 1-2 weeks | Render, Physics, Startup, Memory benchmarks |
| **P0-005** | **mypy strict** | All | 2-3 weeks | Type hints completos en todos los módulos |
| **P0-006** | **SpriteBatch + RenderPipeline** | `loi-render` | 3-4 weeks | GPU batch rendering, capas, composición |
| **P0-007** | **PostProcessStack (Multi-Res)** | `loi-render` | 2-3 weeks | Bloom, ColorGrading, Vignette, adaptive resolution |
| **P0-008** | **SurfacePool** | `loi-render` | 2-3 weeks | Object pooling para superficies, eliminar GC pressure |
| **P0-009** | **PlayerState dataclass** | `loi-framework` | 1-2 weeks | Datos puros del jugador, serializable |
| **P0-010** | **Eliminar globales (_emit)** | `loi-framework` | 1-2 weeks | Inyectar EventBus via DI en Player, EnemyBase |
| **P0-011** | **Refactor StageScene** | `loi-framework` | 3-4 weeks | Dividir God Object en StageController + ECS Systems |

### 12.3 P1 — High Priority

| ID | Name | Module | Effort | Description |
|----|------|--------|--------|-------------|
| P1-001 | Lazy Loading (scipy, sklearn) | `loi-core` | 1-2 weeks | Import bajo demanda de dependencias pesadas |
| P1-002 | ParticleSystem V2 | `loi-vfx` | 2-3 weeks | Sistema de partículas con pool, GPU batch |
| P1-003 | LightSystem V2 + Weather | `loi-vfx` | 2-3 weeks | Iluminación 2D con SurfacePool, clima multi-res |
| P1-004 | AIStrategy + BlueprintLoader | `loi-framework` | 2-3 weeks | Strategy Pattern para AI, enemigos desde YAML |
| P1-005 | ECS Core (World + Component + System) | `loi-framework` | 3-4 weeks | Entity Component System opcional |
| P1-006 | StageWizard Editor | `loi-tools` | 2-3 weeks | Editor de niveles in-game (tile painter, entity placer) |
| P1-007 | CollisionSystem + SpatialGrid | `loi-physics` | 2-3 weeks | Sistema de colisiones independiente del render |
| P1-008 | GravitySystem + Physics | `loi-physics` | 2-3 weeks | Física de plataformas independiente del framework |
| P1-009 | InputStack (capas) | `loi-core` | 2-3 weeks | Input con prioridades: UI > Gameplay > Debug |
| P1-010 | SaveManager V2 | `loi-framework` | 1-2 weeks | Save/load con PlayerState serializable |
| P1-011 | Singleton Removal (Inventory) | `loi-framework` | 1-2 weeks | Inventory via ServiceContainer, no singleton |

### 12.4 P2 — Medium Priority

| ID | Name | Module | Effort | Description |
|----|------|--------|--------|-------------|
| P2-001 | HitEffects + DamageNumbers | `loi-vfx` | 1-2 weeks | Efectos de impacto y números de daño |
| P2-002 | StageController + StageLoader | `loi-framework` | 2-3 weeks | Orquestador de stage, carga TMX |
| P2-003 | HUD + Dialogue + Tutorial | `loi-framework` | 2-3 weeks | UI del framework Metroidvania |
| P2-004 | Achievements + Inventory + Bestiary | `loi-framework` | 2-3 weeks | Sistemas de datos del framework |
| P2-005 | Benchmark Automation | `loi-tools` | 2-3 weeks | Benchmarks en CI con reportes |
| P2-006 | Stage0 Migration | `legacy-game` | 2-3 weeks | Migrar Stage0 a V2 |
| P2-007 | Boss Venado Migration | `legacy-game` | 1-2 weeks | Migrar Boss Venado a V2 |
| P2-008 | Demo Scenes Migration | `legacy-game` | 1-2 weeks | Migrar 13 labs académicos a V2 |
| P2-009 | Couch Co-op (2P local) | `loi-framework` | 4-6 weeks | Segundo jugador local, split-screen |
| P2-010 | Data-Driven Enemies (YAML) | `loi-framework` | 2-3 weeks | BlueprintLoader con ejemplos YAML |
| P2-011 | DynamicMusicSystem V2 | `loi-framework` | 1-2 weeks | Música dinámica con crossfade y transiciones |
| P2-012 | FogOfWar V2 | `loi-vfx` | 1-2 weeks | Fog of war con SurfacePool |
| P2-013 | Minimap V2 | `loi-framework` | 1-2 weeks | Minimapa con exploración y markers |
| P2-014 | Tutorial System V2 | `loi-framework` | 1-2 weeks | Tutoriales contextuales con triggers |
| P2-015 | LearningOverlay V2 | `loi-framework` | 1-2 weeks | F2-F10 toggles con más modos |
| P2-016 | EventBus EventMap | `loi-core` | 1-2 weeks | Documentación de eventos y suscriptores |

### 12.5 P3 — Low Priority

| ID | Name | Module | Effort | Description |
|----|------|--------|--------|-------------|
| P3-001 | WebAssembly Export | `loi-tools` | 4-6 weeks | pyodide/pyscript export |
| P3-002 | Netcode UDP | `loi-core` | 6-10 weeks | Multiplayer online básico |
| P3-003 | Replay System | `loi-framework` | 3-5 weeks | Input replay, ghost split comparación |
| P3-004 | Code Obfuscation | `loi-tools` | 2-3 weeks | Nuitka/PyInstaller empaquetado |
| P3-005 | 3D Audio (positional) | `loi-audio` | 2-3 weeks | Audio 3D posicional con HRTF |
| P3-006 | OpenGL Renderer Backend | `loi-render` | 4-6 weeks | ModernGL backend para GPU nativa |
| P3-007 | Visual Stage Scripting | `loi-tools` | 4-6 weeks | Editor visual de lógica de stage |
| P3-008 | Mobile Export (Android) | `loi-tools` | 6-10 weeks | pyjnius/pygame-android export |

---

## 13. References

- [[03_ARCHITECTURE.md|V1 Architecture]]
- [[04_PLAYER_SPEC.md|Player Specification]]
- [[05_ENEMY_SPEC.md|Enemy Specification]]
- [[51_IMPLEMENTATION_AUDIT.md|Implementation Audit]]
- [[85_MULTIDISCIPLINARY_AUDIT.md|Multidisciplinary Audit]]

---

**Document Version:** 4.0.0  
**Last Updated:** 2026-07-16  
**Next Review:** After Phase 1 V2 completion (loi-math + loi-core + loi-audio)

---

## Appendix: V1 → V2 Migration Mapping

| V1 Path | V2 Module | Notes |
|---------|-----------|-------|
| `src/engine/utils/math_utils.py` | `loi-math/vector2.py` | Pure math, zero deps |
| `src/framework/processing/curve_tools.py` | `loi-math/curves.py` | Bezier, B-Spline, NURBS |
| `src/framework/processing/color_tools.py` | `loi-math/color_spaces.py` | RGB↔HSV↔HSL↔CMYK |
| `src/engine/core/event_bus.py` | `loi-core/event/event_bus.py` | Tipado fuerte + prioridades |
| `src/engine/core/events.py` | `loi-core/event/events.py` | Event constants |
| `src/engine/core/clock.py` | `loi-core/clock.py` | DeltaClock |
| `src/engine/core/settings.py` | `loi-core/settings.py` | Global constants |
| `src/engine/scene/scene_manager.py` | `loi-core/scene/scene_manager.py` | SceneManager |
| `src/engine/scene/base_scene.py` | `loi-core/scene/base_scene.py` | BaseScene |
| `src/engine/scenes/transition_manager.py` | `loi-core/scene/transitions.py` | Fade, Wipe, Slide, Circle (AUD-168: el origen no era `scene/transitions.py`, retirado en AUD-111) |
| `src/engine/input/input_manager.py` | `loi-core/input/input_manager.py` | + InputStack |
| `src/engine/input/action_map.py` | `loi-core/input/action_map.py` | Action bindings |
| `src/engine/core/game_context.py` | `loi-core/di/service_container.py` | ServiceContainer |
| `NUEVO` | `loi-core/plugin/plugin_manager.py` | Plugin system |
| `NUEVO` | `loi-core/plugin/plugin_api.py` | Plugin API |
| `src/engine/audio/audio_manager.py` | `loi-audio/audio_manager.py` | IAudio interface |
| `src/engine/audio/sound_bank.py` | `loi-audio/sound_bank.py` | SoundBank |
| `NUEVO` | `loi-audio/backends/null_backend.py` | For CI |
| `NUEVO` | `loi-audio/backends/sdl2_backend.py` | Future |
| `src/framework/stage/collision_system.py` | `loi-physics/collision.py` | + SpatialGrid |
| `src/framework/entities/player.py` (physics) | `loi-physics/gravity.py` | Gravity system |
| `src/engine/core/app.py` (draw) | `loi-render/pipeline/render_pipeline.py` | RenderPipeline |
| `NUEVO` | `loi-render/batch/sprite_batch.py` | GPU batch |
| `NUEVO` | `loi-render/pool/surface_pool.py` | Object pool |
| `src/framework/stage/camera.py` | `loi-render/camera/camera2d.py` | Camera2D |
| `src/framework/vfx/post_processing.py` | `loi-render/postfx/post_process_stack.py` | Multi-res |
| `NUEVO` | `loi-render/atlas/texture_atlas.py` | Atlas builder |
| `src/framework/vfx/particle_system.py` | `loi-vfx/particle/particle_system.py` | + Pool |
| `src/framework/vfx/lighting.py` | `loi-vfx/lighting/light_system.py` | LightSystem |
| `src/framework/vfx/weather_system.py` | `loi-vfx/weather/weather_system.py` | Climate |
| `src/framework/vfx/fog_of_war.py` | `loi-vfx/fog_of_war.py` | FogOfWar |
| `src/framework/vfx/trail_system.py` | `loi-vfx/trail_system.py` | Trails |
| `src/framework/vfx/water_effect.py` | `loi-vfx/water_effect.py` | Water |
| `src/framework/vfx/hit_effects.py` | `loi-vfx/hit_effects.py` | Hit VFX |
| `src/framework/vfx/damage_numbers.py` | `loi-vfx/damage_numbers.py` | Damage text |
| `src/framework/entities/player.py` | `loi-framework/entities/player.py` | Use PlayerState |
| `src/framework/entities/player_states.py` | `loi-framework/entities/player_states.py` | State Machine |
| `NUEVO` | `loi-framework/entities/player_state.py` | Data class |
| `src/framework/entities/enemy_*.py` | `loi-framework/entities/` | Use AIStrategy |
| `NUEVO` | `loi-framework/entities/blueprint_loader.py` | YAML→Entity |
| `NUEVO` | `loi-framework/ecs/world.py` | ECS |
| `NUEVO` | `loi-framework/ecs/component.py` | Position, Velocity, etc |
| `NUEVO` | `loi-framework/ecs/system.py` | Movement, Render, AI |
| `src/framework/scenes/stage_scene.py` | `loi-framework/stage/stage_controller.py` | Facade |
| `src/framework/stage/stage_loader.py` | `loi-framework/stage/stage_loader.py` | TMX→StageData |
| `src/framework/stage/checkpoint.py` | `loi-framework/stage/checkpoint.py` | Checkpoint |
| `src/framework/stage/hazard_system.py` | `loi-framework/stage/hazard_system.py` | Hazards |
| `src/framework/stage/progression_system.py` | `loi-framework/stage/progression_system.py` | Progression |
| `src/engine/ui/hud.py` | `loi-framework/ui/hud.py` | HUD |
| `src/engine/ui/message_box.py` | `loi-framework/ui/message_box.py` | Messages |
| `src/engine/ui/minimap.py` | `loi-framework/ui/minimap.py` | Minimap |
| `src/engine/ui/screen_banner.py` | `loi-framework/ui/screen_banner.py` | Banner |
| `src/framework/stage/speedrun_mode.py` | `loi-framework/data/speedrun_mode.py` | Speedrun |
| `src/engine/core/inventory.py` | `loi-framework/data/inventory.py` | No singleton |
| `src/engine/core/achievements.py` | `loi-framework/data/achievements.py` | Achievements |
| `src/framework/entities/bestiary.py` | `loi-framework/data/bestiary.py` | Bestiary |
| `src/engine/core/save_manager.py` | `loi-framework/data/save_manager.py` | Save |
| `src/framework/ui/dialogue_system.py` | `loi-framework/ui/dialogue_system.py` | Dialogue |
| `src/framework/ui/tutorial_overlay.py` | `loi-framework/ui/tutorial_overlay.py` | Tutorial |
| `src/framework/ui/learning_overlay.py` | `loi-framework/ui/learning_overlay.py` | Learning |
| `src/framework/audio/dynamic_music.py` | `loi-framework/audio/dynamic_music.py` | Dynamic music |
| `NUEVO` | `loi-tools/editor/stage_wizard.py` | Level editor |
| `NUEVO` | `loi-tools/benchmark/render_bench.py` | Benchmarks |
| `NUEVO` | `loi-tools/export/web_exporter.py` | Web export |
| `src/stages/stage0/` | `legacy-game/stages/stage0/` | Uses V2 API |
| `src/stages/boss_venado/` | `legacy-game/stages/boss_venado/` | Uses V2 API |