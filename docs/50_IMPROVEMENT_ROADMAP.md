# Legacy of InFest — Improvement Roadmap

**Document ID:** LOI-ROADMAP-050  
**Version:** 2.0.0  
**Status:** Official — Current Implementation Baseline + Future Improvements  
**Audience:** Professor, Teaching Assistants, AI coding assistants

---

## 0. Current Implementation Status

### 0.1 Fully Implemented Systems ✅

| System | Status | Evidence |
|--------|--------|----------|
| **Core Engine** | ✅ Complete | Audio, Input, Scene Manager, Transitions, Save, Achievements, Inventory, Settings, Event Bus |
| **Player** | ✅ Complete | 19 states, full physics, state machine |
| **Enemies** | ✅ Complete | 9 types: Walker, Flying, Shooter, Charger, Archer, Brute, Caster, Assassin, Boss |
| **VFX** | ✅ Complete | Particles, trails, damage numbers, lighting, post-processing, fog of war, water, hit effects |
| **UI** | ✅ Complete | HUD, MessageBox, Minimap, Tutorial, Inventory, Achievements, World Map, Options |
| **Processing Tools** | ✅ Complete | FilterTools, VisionTools, PatternRecognition, ColorTools, CurveTools |
| **Stage Systems** | ✅ Complete | StageLoader, Camera, Collision, Hazards, Checkpoints, Progression, Speedrun, Boss Rush, Cutscene |
| **Dialogue System** | ✅ Complete | Branching dialogue with portraits |
| **Bestiary** | ✅ Complete | Enemy tracking system |
| **Demo Scenes** | ✅ Complete | 13 interactive labs (Filter, Vision, Pattern, Color, Vector, Transform, Interpolation, Curve, Noise, Collision, Combo, etc.) |
| **Stages** | ⚠️ Partial | 2 stages complete (Stage0, Boss Venado) |

### 0.2 Project Metrics

| Metric | Value |
|--------|-------|
| **Total Files (.py)** | 207 files |
| **Lines of Code (Python)** | ~28,959 LOC |
| **Tests** | 464 tests |
| **Test Files** | 40 files |
| **Scene Classes** | 32 scenes |
| **Enemy Types** | 8 types + Boss |
| **Player States** | 25 concrete states |
| **Implemented Stages** | 2 (Stage0, Boss Venado) |
| **Documentation** | 65 .md documents |
| **Demo Scenes** | 13 interactive labs |

### 0.3 Implementation Evidence by Category

#### Engine Layer (`src/engine/` — 52 files)
- `audio/audio_manager.py` — Audio playback with fallback
- `audio/dynamic_music.py` — Crossfade combat/traverse/boss music
- `input/input_manager.py` — Keyboard + controller support
- `scene/scene_manager.py` — Stack-based push/pop/replace
- `core/achievements.py` — Achievement system
- `core/inventory.py` — Item management
- `core/save_manager.py` — JSON-based saves

#### Framework Layer (`src/framework/` — 43 files)
- `entities/player.py` — 19 states
- `entities/enemy_*.py` — 9 enemy types
- `vfx/particle_system.py` — Particle effects
- `vfx/lighting.py` — 2D lights
- `vfx/fog_of_war.py` — Fog of war
- `stage/camera.py` — Camera follow, shake
- `stage/collision_system.py` — Collision detection
- `ui/dialogue_system.py` — Branching dialogue

---

## 1. Methodology

This document consolidates improvement opportunities from nine evaluations:

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

---

## 2. Executive Summary

| Category | Items | P0 | P1 | P2 | P3 | Effort |
|----------|-------|----|----|----|----|--------|
| Pedagogy & Math | 22 | 1 | 8 | 10 | 3 | 18-28 weeks |
| Methodology | 12 | 0 | 1 | 8 | 3 | 12-18 weeks |
| Teacher Support | 23 | 0 | 5 | 12 | 6 | 20-30 weeks |
| Student Companion | 23 | 0 | 4 | 13 | 6 | 18-26 weeks |
| AI Lab & XAI | 22 | 0 | 3 | 12 | 7 | 16-24 weeks |
| Game Progression | 12 | 0 | 2 | 6 | 4 | 10-14 weeks |
| Engine Architecture | 18 | 0 | 4 | 8 | 6 | 16-28 weeks |
| Documentation Strategy | 10 | 0 | 0 | 5 | 5 | 8-12 weeks |
| AI & Enemies | 4 | 0 | 2 | 1 | 1 | 3-4 weeks |
| Tools & Editors | 8 | 0 | 2 | 4 | 2 | 10-18 weeks |
| Performance | 3 | 0 | 1 | 1 | 1 | 2-3 weeks |
| Content | 3 | 0 | 1 | 1 | 1 | 2-4 weeks |
| Documentation | 2 | 1 | 1 | 0 | 0 | 1 week |
| **Total** | **160** | **3** | **34** | **81** | **46** | **137-198 weeks** |

**Note:** This roadmap documents FUTURE improvements. See Section 0 for currently implemented systems.

---

## 3. Improvement Items

### 3.1 P0 — Blockers (Must fix before class)

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

---

### 3.2 P1 — High Priority

[P1 items continue...]

#### P1-07: Scripting enemigos (AI)

| Field | Value |
|-------|-------|
| **Category** | AI |
| **Status** | ✅ **IMPLEMENTED** |
| **Effort** | 1-2 weeks |
| **Current State** | 9 tipos de enemigo implementados con comportamientos únicos via código. |
| **Implementation Evidence** | ✅ `src/framework/entities/enemy_base.py` (base class), `enemy_walker.py`, `enemy_flying.py`, `enemy_shooter.py`, `enemy_charger.py`, `enemy_archer.py`, `enemy_brute.py`, `enemy_caster.py`, `enemy_assassin.py`, `boss_base.py` |
| **Action** | Ya implementado via código. Considerar agregar soporte JSON/YAML para data-driven enemies. |
| **Verification** | 9 tipos de enemigo funcionales con comportamientos únicos. |

[Other P1 items remain unchanged...]

---

### 3.3 P2 — Medium Priority

[P2 Pedagogy & Math items 00-43 remain unchanged...]

#### P2-04: Bestiario UI (CONTENT)

| Field | Value |
|-------|-------|
| **Category** | Content |
| **Status** | ✅ **IMPLEMENTED** |
| **Effort** | 1 week |
| **Current State** | Sistema completo de bestiario con UI. |
| **Implementation Evidence** | ✅ `src/framework/entities/bestiary.py` (tracking system), `src/engine/scenes/bestiary_scene.py` (UI scene) |
| **Action** | Ya implementado. Considerar mejoras: filtros, búsqueda, estadísticas avanzadas. |
| **Verification** | Estudiante ve enemigos encontrados con stats y lore. |

#### P2-05: Speedrun UI (CONTENT)

| Field | Value |
|-------|-------|
| **Category** | Content |
| **Status** | ✅ **IMPLEMENTED** |
| **Effort** | 3-5 days |
| **Current State** | Sistema completo de speedrun con timer, splits y ghost replay. |
| **Implementation Evidence** | ✅ `src/framework/stage/speedrun_mode.py` (timer + splits + ghost data) |
| **Action** | Ya implementado. Considerar mejoras: leaderboards, share replays. |
| **Verification** | Jugador ve tiempo, splits, ghost replay. |

[Other P2 items remain unchanged...]

---

### 3.4 P2 — Teacher Support System

[P2-53 through P2-72 remain unchanged...]

---

### 3.5 P2 — Student Companion System

#### P2-79: Achievement System (NEW)

| Field | Value |
|-------|-------|
| **Category** | Student Support |
| **Status** | ✅ **IMPLEMENTED** |
| **Effort** | 1 week |
| **Current State** | Sistema completo de logros con UI. |
| **Implementation Evidence** | ✅ `src/engine/core/achievements.py` (system), `src/engine/scenes/achievement_scene.py` (UI) |
| **Action** | Ya implementado. Considerar mejoras: más logros, progresión, rarity. |
| **Verification** | Estudiante desbloquea logros académicos que motivan continuidad. |

[P2-80 through P2-88 remain unchanged...]

---

### 3.6 P2 — AI Lab & Explainable AI

[P2-90 through P2-109 remain unchanged...]

---

### 3.7 P2 — Game Progression System

[P2-110 through P2-114 remain unchanged...]

#### P2-115: No Monetization (CONSISTENCY)

| Field | Value |
|-------|-------|
| **Category** | Game Progression |
| **Status** | ✅ **FOLLOWED** |
| **Effort** | — |
| **Current State** | Decisión de diseño documentada y seguida. No hay features de monetización. |
| **Implementation Evidence** | ✅ No existen sistemas de monedas, tienda, loot boxes, microtransacciones en el código |
| **Action** | Mantener decisión. No implementar features de monetización. |
| **Verification** | Documento oficial declara estas features como out-of-scope. |

---

## 4. Vision — Legacy Academic Framework v4 (FINAL)

[Section 4 remains unchanged...]

---

## 5. Implementation Phases (Final)

[Phase sections remain unchanged...]

---

## 6. Verification Checklist

[Checklist remains unchanged...]

---

## 7. References

[References remain unchanged...]

---

## Appendix A: Implementation Status Summary

### A.1 By Category

| Category | Total Items | Implemented | Partial | Not Implemented | % Done |
|----------|-------------|-------------|---------|----------------|--------|
| **Already Done** | 10 systems | 10 | 0 | 0 | 100% |
| **P0 — Blockers** | 3 | 3 | 0 | 0 | 100% |
| **P1 — High Priority** | 34 | 1 | 0 | 33 | 3% |
| **P2 — Medium Priority** | 81 | 4 | 0 | 77 | 5% |
| **P3 — Low Priority** | 46 | 0 | 0 | 46 | 0% |
| **TOTAL** | **174** | **18** | **0** | **156** | **10%** |

**Note:** 10 systems (100%) represent work already complete. The 160 roadmap items are future improvements (~10% complete). P0 blockers are fully resolved — V1 infrastructure is ready.

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

### A.3 Items Partially Implemented (0 items)

All previously partial items are resolved.

### A.4 Items Not Implemented (152 items)

All other roadmap items represent future work.

---

**Document Version:** 2.0.0  
**Last Updated:** 2026-07-11  
**Next Review:** After P0 items completion