---
document_id: "LOI-CODEX-002"
title: "Legacy of InFest — Codex Context"
aliases: ["Codex Context", "Coding Rules"]
tags: ["codex", "rules", "architecture"]
description: "Project philosophy, coding rules, architecture rules"
source: "docs/02_CODEX_CONTEXT.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Codex Context

**Document ID:** LOI-CODEX-002  
**Version:** 1.0.0  
**Status:** Official  
**Audience:** All contributors, AI coding assistants

---

## 1. Project Identity

| Property | Value |
|---|---|
| Project Name | Legacy of InFest |
| Type | Academic Game Framework |
| Platform | Desktop (Windows, macOS, Linux) |
| Language | Python 3.14+ |
| Game Framework | Pygame CE |
| Visual Style | Authentic SNES Era (1993–1995) |
| Internal Resolution | 320×224 |
| Academic Context | Computer Graphics, Digital Image Processing, Pattern Recognition |

This document defines the philosophical and technical identity of the project. Every design decision, every piece of code, and every asset must be consistent with the principles described here. When in doubt, refer to this document before making any decision.

---

## 2. Academic Philosophy

### 2.1 The Framework is a Teaching Instrument

Legacy of InFest exists to make academic concepts tangible. It is not a game in the commercial sense. It is a controlled laboratory. Every system in it was built with a specific learning objective in mind.

The professor is the engineer. The students are the researchers. The framework gives them a running environment so they can focus entirely on applying course content — not on debugging a physics engine or writing a renderer.

### 2.2 Concepts Before Features

Every feature in a student stage must be grounded in a course concept. Students do not add features for aesthetic reasons. They add features because those features demonstrate a specific academic topic from the syllabus. A moving enemy that follows a Bézier path exists because the student is applying Unit III. A texture with real-time Sobel edge detection applied exists because the student is applying Unit VII.

If a feature cannot be mapped to a course learning objective, it does not belong in the stage.

### 2.3 Reproducibility Over Randomness

Academic work must be reproducible. Randomness in game behavior must be seeded and documented so that graders and professors can reproduce observed behavior. All random elements must be seeded with a fixed value unless the student explicitly documents the intent and the expected variance.

### 2.4 Clarity Over Performance

Students are not expected to optimize for 60 fps on minimal hardware. They are expected to write code that a professor can read and evaluate. Clarity, documentation, and correctness of concept application are prioritized over micro-optimizations.

---

## 3. Framework Philosophy

### 3.1 The Professor Owns the Engine

The `engine/` and `framework/` directories are professor territory. Students do not modify them. They do not submit pull requests against them. They do not fork them for their own use inside the project.

This constraint exists because the framework's value comes from its consistency. If each student modified the engine to suit their needs, the shared foundation would collapse, and the teaching instrument would be unusable.

### 3.2 Students Build Stages, Not Systems

A student stage is a scene file, a TMX map, a set of custom entities (if needed), and a README. It consumes the framework. It does not extend the framework's architecture.

If a student legitimately needs a new base-level capability — a new processing utility, a new entity template — they submit a documented proposal to the professor, who evaluates it and potentially integrates it into the framework for all students.

### 3.3 Stage 0 is the Ground Truth

Stage 0 is the executable documentation. When a student does not know how to implement something, they study Stage 0 before asking the professor. Stage 0 demonstrates every major system the student will use. It is designed to be read, not just played.

### 3.4 Asset Reuse is Encouraged

Students may use all assets in the `assets/` directory. They may create new assets in `student_assets/`. Asset reuse reduces the workload of asset creation and keeps the project visually coherent, which is appropriate for an academic context.

---

## 4. Design Principles

| Principle | Description |
|---|---|
| **Minimal surface** | Expose only what students need. Engine internals are hidden behind clean APIs. |
| **Predictable behavior** | Every system behaves consistently. No hidden side effects. |
| **Fail loudly** | When a student misuses the framework, it raises a descriptive exception — not a silent failure. |
| **Self-documenting code** | All engine and framework code is commented at a level appropriate for a first-reading student. |
| **Academic transparency** | Every system includes a comment block explaining which course concept it implements and why. |
| **SNES fidelity** | Visual design, animation rhythm, and gameplay feel target the 1993–1995 SNES era. No modern UI conventions. No particle engines. |

---

## 5. Programming Standards

### 5.1 Language Rules

- Python 3.14+ only. No compatibility shims for older versions.
- Type hints are required on all function signatures in the engine and framework. Type hints are encouraged but not mandatory in student stages.
- Docstrings are required on all classes and public methods in the engine and framework, following Google-style format.
- f-strings are preferred over `.format()` or `%` formatting.
- `pathlib.Path` is used for all file system operations. `os.path` is not used.

### 5.2 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Module | `snake_case` | `enemy_walker.py` |
| Class | `PascalCase` | `EnemyWalker` |
| Method | `snake_case` | `apply_damage()` |
| Property | `snake_case` | `current_health` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_HEALTH = 5` |
| Private | leading underscore | `_collision_rect` |
| Event name | `UPPER_SNAKE_CASE` string | `"PLAYER_DAMAGED"` |

### 5.3 File Structure Rules

Every module begins with:

```python
"""
Module: <module_name>
System: <engine|framework|stage>
Academic Unit: <course unit number and name>
Description: <one paragraph description>
"""
```

### 5.4 Error Handling

- Use descriptive exceptions with messages that identify the problem and the expected correct behavior.
- Do not use bare `except:` clauses.
- Engine errors are unrecoverable and should raise `RuntimeError` or a custom `EngineError`.
- Framework misuse by students should raise `FrameworkUsageError` with a message that explains the correct usage.

### 5.5 Constants and Configuration

- All numeric constants that affect gameplay or display are declared in `engine/core/settings.py`.
- Students must not hardcode values that exist in `settings.py`.
- Students may define their own stage-local constants in their stage module, but must not override global settings.

---

## 6. Coding Rules

### 6.1 Prohibited Patterns

The following patterns are prohibited in all framework and student code:

| Pattern | Reason |
|---|---|
| `import pygame` without `import pygame.locals` | Inconsistent namespace usage |
| Direct `pygame.display.set_mode()` calls outside `app.py` | Display is managed by the engine |
| Direct `pygame.time.Clock()` instantiation outside `clock.py` | Clock is managed by the engine |
| Hardcoded file paths using string literals | Use `pathlib.Path` and `settings.ASSETS_DIR` |
| Global mutable state outside the engine core | Use the event bus or scene state |
| Circular imports | Restructure into dependencies |
| `print()` for debug output | Use `logging` |
| Polling `pygame.key.get_pressed()` directly in entities | Use `InputManager.is_action_held()` |
| Direct sprite blit outside the camera/layer system | All rendering goes through the layer stack |

### 6.2 Required Patterns

| Pattern | Reason |
|---|---|
| All entities inherit from `BaseEntity` | Ensures lifecycle compatibility |
| All scenes inherit from `BaseScene` | Ensures scene manager compatibility |
| All stage maps are TMX files loaded via `StageLoader` | Ensures layer and object standardization |
| All sounds played via `AudioManager` | Ensures volume control and channel management |
| All assets loaded via `AssetLoader` | Ensures caching and path resolution |

---

## 7. Architecture Rules

### 7.1 Dependency Direction

Dependencies flow in one direction only: from higher-level components toward lower-level ones. The dependency hierarchy is:

```
Stages
  ↓
Framework (entities, stage, processing)
  ↓
Engine (core, scene, input, audio, ui, utils)
  ↓
Pygame CE / Libraries
```

Stages may depend on framework and engine. Framework may depend on engine. Engine depends only on libraries. Nothing flows upward.

### 7.2 Scene Isolation

Scenes own their state. A scene does not read or write the state of another scene directly. Cross-scene communication happens only via the event bus or via data passed through the scene manager's push/pop interface.

### 7.3 Entity Isolation

Entities do not hold direct references to other entities. They communicate via the event bus. This prevents cascading coupling and makes each entity independently testable.

### 7.4 Processing Pipeline Isolation

The processing utilities in `framework/processing/` are pure functions wherever possible. They receive data in (surfaces, numpy arrays, color values), transform it, and return data out. They do not hold state, do not call the event bus, and do not access Pygame globals.

---

## 8. Asset Rules

### 8.1 Sprite Standards

| Property | Value |
|---|---|
| Format | PNG with alpha |
| Palette | SNES-constrained (max 16 colors per sprite, 256 globally) |
| Pixel size | 1:1 pixels |
| Animation format | Horizontal sprite sheet, equal-width frames |

### 8.2 Tileset Standards

| Property | Value |
|---|---|
| Tile size | 16×16 pixels |
| Format | PNG with alpha |
| Maximum tiles per set | 256 |
| Naming | `tileset_<environment>_<variant>.png` |

### 8.3 Audio Standards

| Property | Value |
|---|---|
| Music format | OGG Vorbis |
| SFX format | WAV or OGG |
| Music sample rate | 44100 Hz |
| SFX sample rate | 22050 Hz or 44100 Hz |
| Channels | Stereo for music, mono for SFX |

### 8.4 Font Standards

- All UI text uses bitmap pixel fonts.
- No anti-aliased fonts.
- No system fonts.
- Fonts are loaded as PNG sprite sheets through the engine's font renderer.

### 8.5 Naming Conventions

| Asset Type | Convention | Example |
|---|---|---|
| Player sprite sheet | `player_<action>.png` | `player_walk.png` |
| Enemy sprite sheet | `enemy_<type>_<action>.png` | `enemy_walker_walk.png` |
| Tileset | `tileset_<env>.png` | `tileset_dungeon.png` |
| Background | `bg_<name>_<layer>.png` | `bg_castle_far.png` |
| Music | `bgm_<scene>_<mood>.ogg` | `bgm_stage0_tense.ogg` |
| SFX | `sfx_<action>.wav` | `sfx_player_jump.wav` |

---

## 9. Student Responsibilities

Students are responsible for the following, and only the following:

1. **Stage TMX File:** Design the stage layout using Tiled, following the TMX specification in `06_TMX_SPEC.md`.
2. **Stage Python Module:** Implement the stage class inheriting from the provided stage base, populating it with entities and systems defined by the framework.
3. **Academic Feature Implementation:** Implement at least one academic feature per course unit covered by the stage's assigned syllabus range. The feature must be documented in the stage README.
4. **Custom Entities (if needed):** Students may create custom entity subclasses for their stage. Custom entities must inherit from `EnemyBase` or `BaseEntity` and must not duplicate functionality that already exists in the framework.
5. **Student Assets:** New assets created by students are placed in `student_assets/`. Students do not modify assets in `assets/`.
6. **Stage README:** A markdown file documenting which academic concepts are demonstrated, which framework systems were used, and how to run and test the stage.

---

## 10. Professor Responsibilities

The professor is responsible for:

1. **Engine Maintenance:** All code in `engine/` is professor-owned. The professor keeps it functional, documented, and consistent across all student branches.
2. **Framework Maintenance:** All code in `framework/` is professor-owned.
3. **Stage 0:** The professor builds and maintains Stage 0 as the executable documentation of all framework systems.
4. **Documentation:** All 10 documents in the `docs/` directory are professor-owned and maintained.
5. **Asset Library:** The core `assets/` directory is professor-owned. The professor provides a sufficient base asset library for students to build their stages.
6. **Grading Rubric:** The professor defines the evaluation criteria mapped in `08_SYLLABUS_MAPPING.md`.
7. **Code Review:** The professor reviews all student pull requests and provides written feedback.

---

## 11. Restrictions

### 11.1 Absolute Restrictions (Never Permitted)

These actions are prohibited under any circumstances:

- Modifying any file in `engine/`
- Modifying any file in `framework/`
- Modifying Stage 0 files
- Modifying files in `assets/`
- Committing directly to `main`
- Importing libraries not listed in `requirements.txt` without professor approval
- Bypassing the `InputManager` by polling Pygame input directly
- Bypassing the `AudioManager` by calling `pygame.mixer` directly
- Bypassing the `AssetLoader` by calling `pygame.image.load()` directly
- Instantiating `pygame.time.Clock()` inside a stage or entity

### 11.2 Conditional Restrictions (Require Professor Approval)

- Adding a new library dependency
- Creating a new processing utility
- Creating a new entity template
- Adding to the shared `assets/` directory

---

## 12. AI Generation Guidelines

When an AI coding assistant (such as Claude, Copilot, or Cursor) is used to generate code for this project, the following rules apply:

### 12.1 What AI May Generate

- Stage Python modules (`stage1.py`, `stage2.py`, `stage3.py`)
- Custom entity subclasses within a student stage
- Processing routines that use `framework/processing/` utilities
- Stage README documentation
- Unit tests for student-created modules

### 12.2 What AI Must Not Generate

- Any code in `engine/` or `framework/`
- Any new base classes not already defined in the framework
- Any code that bypasses the framework API (no direct Pygame calls in stages)
- Any TMX file modifications (TMX is a visual editor output, not code)

### 12.3 Context Requirements for AI

When prompting an AI assistant to generate code for this project, always provide:

1. The complete `02_CODEX_CONTEXT.md` document (this file)
2. The `03_ARCHITECTURE.md` document for module context
3. The specific specification document for the system being used (e.g., `04_PLAYER_SPEC.md` if working with the player)
4. The current stage module if extending existing code

### 12.4 AI Output Validation

All AI-generated code must be reviewed against:

- The coding rules in Section 6 of this document
- The architecture rules in Section 7
- The student responsibility constraints in Section 9
- The absolute restrictions in Section 11.1

AI-generated code that violates any of the above must be corrected before committing.


--- Traducción al Español ---

## Contexto del Códice

### Identidad del Proyecto
Legacy of InFest es un motor de videojuegos académico construido con Python 3.14+ y Pygame CE, de estilo SNES (resolución 320×224), para el contexto académico de Gráficas por Computadora, Procesamiento de Imágenes y Reconocimiento de Patrones.

### Filosofía Académica
El framework es un instrumento de enseñanza. Cada sistema se construyó con un objetivo de aprendizaje específico. Los estudiantes construyen escenarios, no sistemas. El profesor es dueño del motor (`engine/` y `framework/`).

### Reglas de Programación
- Python 3.14+ solamente
- Type hints obligatorios en código del motor
- Docstrings estilo Google
- `snake_case` para funciones, `PascalCase` para clases

### Restricciones Absolutas
- No modificar archivos en `engine/` o `framework/`
- No consolidar directamente a `main`
- No eludir `InputManager`, `AudioManager` o `AssetLoader`

Para la especificación completa, consultar el documento original en inglés.
