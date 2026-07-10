# Legacy of InFest — Student Template Specification

**Document ID:** LOI-TEMPLATE-026  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires `00_SYLLABUS_ALIGNMENT_AUDIT.md`, `22_API_CONTRACTS.md`, `23_DATA_SCHEMAS.md`, `21_COURSE_SCHEDULE.md`  
**Audience:** Professor, AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Purpose

`00_SYLLABUS_ALIGNMENT_AUDIT.md` §7 and `03_ARCHITECTURE.md` §1 both reference `student_templates/stage_template/` and `student_templates/boss_template/` as the canonical starting point every student copies in Class 1 (per `21_COURSE_SCHEDULE.md`). No prior document defines what those template files actually contain. This document is that definition — exact file contents, placeholders, and the README a student fills in.

**Onboarding target (per `25_IMPLEMENTATION_ROADMAP.md` §18):** A student must be able to copy a template, rename it to their assignment, and have a *running* (if empty) Stage or Boss within 15 minutes of starting Class 1.

---

## 2. Directory Contents

```
student_templates/
├── stage_template/
│   ├── stage_template.py
│   ├── stage_template.tmx
│   └── README_template.md
└── boss_template/
    ├── boss_template.py
    └── README_template.md
```

Bosses do not get a `.tmx` template — per `17_BOSS_SPEC.md` §6.2, boss arenas are fixed (320×224, no scrolling), so a boss's TMX (if the assignment is a boss with a scroll-free arena built in Tiled) is created by the student directly from a blank Tiled map rather than a pre-authored template, OR (more commonly) the arena is built directly in Python as static geometry per `17_BOSS_SPEC.md` boss arena tables — both approaches are valid and the `boss_template.py` below supports either.

---

## 3. `stage_template.py`

This is the exact file content at `student_templates/stage_template/stage_template.py`. Every `# TODO(student):` comment marks a required student edit. Everything else must work unmodified the first time the student runs it.

The template inherits from `StageScene` (not `BaseScene`), which provides all engine integration: collision system, hazard system, progression system, SFX, boss HUD, save/load, pause menu, camera locks, and time scaling — students only override lifecycle hooks.

```python
"""
Module: stage_template
System: stage (student assignment)
Academic Unit: See README.md front-matter for units_demonstrated.

STUDENT INSTRUCTIONS:
1. Copy this entire folder to src/stages/<your_assignment_id>/
2. Rename this file to <your_assignment_id>.py
3. Rename stage_template.tmx to <your_assignment_id>.tmx
4. Update TMX_PATH and class attributes (STAGE_ID, STAGE_NAME, ZONE)
5. Fill in every # TODO(student) marker.
6. Do NOT modify StageScene or any engine/framework code.

Test with:
   python main.py --stage <your_assignment_id>
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


# TODO(student): Rename this class to match your assignment
# (e.g., class Stage1_2_LaSoda(StageScene):)
class StageTemplate(StageScene):
    """TODO(student): Describe your stage's zone, narrative context,
    and the academic concepts it demonstrates."""

    # TODO(student): Change these to match your assignment
    STAGE_ID: str = "stage_template"
    STAGE_NAME: str = "UNTITLED STAGE"
    ZONE: int = 1

    # TODO(student): Update this path after moving your .tmx to assets/maps/<id>/
    TMX_PATH = "student_templates/stage_template/stage_template.tmx"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))

    # ── Optional lifecycle hooks ────────────────────────────────────
    # Override any of these to add custom behavior:

    def on_stage_start(self) -> None:
        """Called after the stage loads and setup completes.
        TODO(student): e.g., register custom entities, set initial state."""
        pass

    def on_player_landed(self) -> None:
        """Called when the player first touches ground after being airborne.
        TODO(student): e.g., trigger a message."""
        pass

    def on_enemy_died(self, enemy) -> None:
        """Called when an enemy dies.
        TODO(student): e.g., unlock a door."""
        pass

    def on_next_trigger_entered(self) -> None:
        """Called when the player touches NextTrigger.
        TODO(student): e.g., play a cutscene."""
        pass

    def on_debug_toggle(self, enabled: bool) -> None:
        """Called when F1 is pressed.
        TODO(student): e.g., show/hide debug info."""
        pass
```

---

## 4. `stage_template.tmx`

The template TMX is not reproduced as raw XML in this document (TMX is a binary-adjacent Tiled-editor format, not meant for hand-authoring in Markdown). Instead, this section specifies **exactly what the professor's `tools/` scripting (or an AI assistant with file-write access) must generate** so a student opens a valid, minimal, already-passing TMX in Tiled on day one.

### 4.1 Required Generated Content

| Element | Content |
|---|---|
| Map dimensions | 40 tiles wide × 14 tiles tall (640×224 px) — small enough to be a trivial starting point, large enough to be non-degenerate |
| Tileset reference | `assets/tilesets/tileset_stage0.png` (neutral, always available, swappable later) |
| Layers (all 8 required, per `06_TMX_SPEC.md` §3.1) | `BG_Far`, `BG_Mid`, `BG_Near` — each filled with a single repeating placeholder tile; `Terrain` — a flat floor row at the bottom; `Terrain_Detail` — empty; `Objects` — see §4.2; `Collision` — one `Solid_Floor` rect matching the `Terrain` floor row; `FG_Overlay` — empty |
| Map custom properties | `stage_id="stage_template"`, `stage_name="Untitled Stage"`, `time_limit=120`, `bgm_track="bgm_stage0"` (placeholder; student changes per their zone) |

### 4.2 Required `Objects` Layer Content

| Object | Properties |
|---|---|
| `PlayerSpawn_01` | Positioned on the flat floor, near the left edge |
| `NextTrigger_01` | Positioned at the right edge, full floor-to-ceiling height |
| `Checkpoint_01` | Positioned at the horizontal midpoint, `checkpoint_id=0` |

**This is intentionally the minimum valid stage** — it passes `StageLoader.load()` (per `tests/test_stage_loader.py` validation rules) with zero enemies and zero messages. The student adds enemies, messages, hazards, and additional terrain as their first Class 1–5 work, per their zone's design in `16_WORLD_DESIGN.md` and enemy roster in `18_ENEMY_ROSTER.md`.

### 4.3 Generation Method for AI Assistants

Since TMX is XML, an AI assistant with file-write access generates this file directly as XML following the exact structure documented in `06_TMX_SPEC.md` §11.1 ("Minimal Valid TMX Structure"), populated with the values from §4.1–4.2 above. Do not invent additional layers, objects, or properties beyond what is listed here — the template's entire purpose is minimalism.

---

## 5. `boss_template.py`

```python
"""
Module: boss_template
System: framework/entities (student boss assignment)
Academic Unit: See README.md front-matter for units_demonstrated.

STUDENT INSTRUCTIONS:
1. Copy this file to src/stages/<your_assignment_id>/<your_assignment_id>.py
2. Rename the class below from BossTemplate to your boss's name
   (e.g., class BossRey(BossBase): for El Rey Terciopelo).
3. Define your boss's phases via set_phases() with BossPhase objects.
4. Fill in every # TODO(student) marker.
5. See 17_BOSS_SPEC.md for the full design contract of your assigned boss.
6. Create a companion scene file <your_assignment_id>_scene.py that
   inherits from StageScene and points to your boss's arena TMX.

Test with:
   python main.py --boss <your_assignment_id>
"""
from __future__ import annotations

import pygame

from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.enemy_base import EnemyState


# TODO(student): Rename this class to match your assigned boss
class BossTemplate(BossBase):
    def __init__(self, spawn_position: pygame.Vector2) -> None:
        # TODO(student): Replace this single placeholder phase with the
        # full phase list from your boss's 17_BOSS_SPEC.md entry (or your
        # professor-approved design if not yet documented there).
        phases = [
            BossPhase(
                phase_index=0,
                health_threshold=0.0,
                attack_patterns=["PLACEHOLDER_ATTACK"],
                movement_type="stationary",
                speed_multiplier=1.0,
            ),
        ]
        super().__init__(
            spawn_position=spawn_position,
            # TODO(student): Set your boss's total health per its spec document
            max_health=10.0,
            damage_on_contact=0.5,
        )
        # TODO(student): Set your boss's display name (used in the boss HUD)
        self.set_boss_name("Untitled Boss")
        self.set_phases(phases)

    def _patrol_behavior(self, dt: float) -> None:
        # TODO(student): Implement this phase's idle/patrol movement.
        pass

    def _alert_behavior(self, dt: float) -> None:
        # TODO(student): Implement this phase's active-combat movement
        # and attack-pattern triggering, per your BossPhase.attack_patterns.
        pass

    def _get_animation_key(self) -> str:
        # TODO(student): Return the sprite animation key matching
        # self.state and self.current_phase (e.g., "drift", "idle").
        return "drift"

    def _build_hitbox(self) -> pygame.Rect:
        # TODO(student): Define your boss's attack hitbox in LOCAL space
        # (offset from self.position). See boss_venado.py for reference.
        return pygame.Rect(6, 4, 36, 44)

    def _build_hurtbox(self) -> pygame.Rect:
        # TODO(student): Define your boss's damage-receiving hurtbox in
        # LOCAL space.
        ox = (self.rect.width - 30) // 2
        oy = (self.rect.height - 40) // 2
        return pygame.Rect(ox, oy, 30, 40)
```

---

## 6. `README_template.md` (Stage Variant)

Located at `student_templates/stage_template/README_template.md`. This is a worksheet format — students fill in each section by hand.

```markdown
# Custom Stage Design — Student Worksheet

**Student Name:** ___________________________
**Stage ID:** ___________________________

---

## 1. Stage Concept (3–5 sentences)

Describe the theme, environment, and atmosphere of your custom stage.

___________________________

## 2. Tileset Requirements

| Tile ID | Description | Collision? |
|---------|-------------|------------|
| 0       | Empty / Air | No         |
| 1       | ____________ | ______     |
| 2       | ____________ | ______     |

## 3. Enemy / Entity Placements

| X   | Y   | Type    | Properties             |
|-----|-----|---------|------------------------|
| ___ | ___ | ________ | ______________________ |

## 4. Checkpoints

| ID | X   | Y   |
|----|-----|-----|
| 0  | ___ | ___ |

## 5. Custom Logic Notes

Describe any custom behavior (moving platforms, conditional spawns, etc.).

___________________________

## 6. Reflection (2–3 sentences)

What was the hardest part? What would you improve?

___________________________
```

---

## 7. `README_template.md` (Boss Variant)

Located at `student_templates/boss_template/README_template.md`. Worksheet format:

```markdown
# Boss Battle Design — Student Worksheet

**Student Name:** ___________________________
**Boss Name:** ___________________________

---

## 1. Boss Concept (3–5 sentences)

Describe your boss's appearance, personality, and role in the game world.

___________________________

## 2. Attack Patterns

| Attack Name | Type       | Damage | Cooldown | Description               |
|-------------|------------|--------|----------|---------------------------|
| ____________ | projectile | ____   | ________ | _________________________ |

## 3. Phase Transitions

| Phase | HP %   | New Behaviour                      |
|-------|--------|------------------------------------|
| 1     | 100–51 | __________________________________ |
| 2     | 50–26  | __________________________________ |

## 4. Visual / Audio Design

Describe sprites, animations, screen effects, and sound.

___________________________

## 5. Reflection (2–3 sentences)

What was the most challenging aspect? What would you improve?

___________________________
```

---

## 8. Definition of Done for This Template Set

(Restated and expanded from `25_IMPLEMENTATION_ROADMAP.md` Phase 15.)

- [ ] `stage_template.py` imports cleanly with zero changes (`python -c "from student_templates.stage_template.stage_template import StageTemplate"` succeeds).
- [ ] `stage_template.tmx` opens in Tiled with no validation errors and passes `StageLoader.load()` with zero exceptions (verified by `tests/test_student_template.py`).
- [ ] `boss_template.py` imports cleanly and `BossTemplate(pygame.Vector2(0, 0))` constructs without exception.
- [ ] Both README template files exist as worksheets (no YAML front-matter requirement — simple Markdown).
- [ ] **15-minute onboarding test:** the professor (or a TA acting as a test student) copies `stage_template/` to a new `src/stages/test_assignment/` folder, renames the file/class, updates `TMX_PATH`, runs `python main.py --stage test_assignment`, and reaches a playable (if empty) stage with working player movement and a functioning `NextTrigger` — within 15 minutes.

### 8.1 `tests/test_student_template.py`

| Test | Assertion |
|---|---|
| `test_stage_template_import` | `StageTemplate` can be imported |
| `test_stage_template_instantiate` | `StageTemplate(context)` constructs without exception |
| `test_stage_template_tmx_exists` | The default TMX file exists at `TMX_PATH` |
| `test_stage_template_has_required_layers` | The TMX contains all 8 required layer names |
| `test_stage_template_has_stage_scene_attrs` | Instance has `_stage_data`, `_player`, `_camera` (inherited from StageScene) |
| `test_boss_template_import` | `BossTemplate` can be imported |
| `test_boss_template_constructs` | `BossTemplate(pygame.Vector2(0, 0))` does not raise |
| `test_boss_template_has_required_methods` | Instance has `_patrol_behavior`, `_alert_behavior`, `_get_animation_key`, `_build_hitbox`, `_build_hurtbox` |
| `test_boss_template_has_one_phase` | `len(BossTemplate(...).phases) == 1` (the placeholder phase) |

---

## 9. Relationship to Student Assignment Folders

Once a student completes the 15-minute onboarding copy-and-rename, their working folder lives at `src/stages/<assignment_id>/` (per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §7 and `03_ARCHITECTURE.md` §1) and is **no longer** part of `student_templates/`. The template directory itself is never modified after initial professor setup — it is read-only scaffolding that every student copies from independently, so one student's in-progress work never collides with another's, consistent with the individual-assignment model confirmed in `00_SYLLABUS_ALIGNMENT_AUDIT.md` §2 A.1.
