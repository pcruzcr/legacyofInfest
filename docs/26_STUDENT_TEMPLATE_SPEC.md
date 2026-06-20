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

This is the exact file content an AI assistant generates at `student_templates/stage_template/stage_template.py`. Every `# TODO(student):` comment marks a required student edit. Everything else must work unmodified the first time the student runs it.

```python
"""
Module: stage_template
System: stage (student assignment)
Academic Unit: See README.md front-matter for units_demonstrated.

STUDENT INSTRUCTIONS:
1. Copy this entire folder to src/stages/<your_assignment_id>/
2. Rename this file and the .tmx file to match your assignment_id
   (e.g., stage1_2_la_soda.py, stage1_2_la_soda.tmx)
3. Rename the class below from StageTemplate to a descriptive name
   (e.g., Stage1_2_LaSoda)
4. Fill in every # TODO(student) marker.
5. Do NOT modify anything outside the marked sections — the engine
   and framework integration points below are required exactly as written.
"""

from pathlib import Path

from src.engine.scene.base_scene import BaseScene
from src.engine.core.event_bus import EventBus
from src.engine.core.settings import STAGES_DIR
from src.framework.entities.player import Player
from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import EnemyShooter
from src.framework.stage.stage_loader import StageLoader, StageData
from src.framework.stage.camera import Camera
from src.framework.stage.checkpoint import Checkpoint
from src.engine.ui.hud import HUD
from src.engine.ui.message_box import MessageBox
from src.engine.ui.screen_banner import ScreenBanner


# TODO(student): Rename this class to match your assignment
# (e.g., class Stage1_2_LaSoda(BaseScene):)
class StageTemplate(BaseScene):
    """
    TODO(student): One-paragraph description of your stage's zone,
    narrative context (see 16_WORLD_DESIGN.md for your assigned zone),
    and the academic concepts it demonstrates.
    """

    # TODO(student): Point this at your renamed .tmx file
    TMX_PATH = STAGES_DIR / "stage_template" / "stage_template.tmx"

    def __init__(self) -> None:
        self.stage_data: StageData | None = None
        self.player: Player | None = None
        self.camera = Camera()
        self.hud = HUD()
        self.message_box = MessageBox()
        self.screen_banner = ScreenBanner()
        self._register_entities()

    def _register_entities(self) -> None:
        """
        Required framework entity registration. Do not remove these three.
        TODO(student): Add StageLoader.register_entity(...) calls here for
        any CUSTOM entity subclasses you create (see 05_ENEMY_SPEC.md §11.2
        for the pattern). Do not duplicate Walker/Flying/Shooter — they are
        already registered globally by the engine.
        """
        pass  # Custom entity registrations go here, if any.

    def on_enter(self) -> None:
        self.stage_data = StageLoader.load(self.TMX_PATH)

        self.player = Player(spawn_position=self.stage_data.spawn_point)
        self.camera.follow(self.player)
        self.hud.bind_player(self.player)
        self.hud.start_timer(seconds=self.stage_data.time_limit)
        self.screen_banner.play(
            stage_id=self.stage_data.stage_id,
            stage_name=self.stage_data.stage_name,
        )

        # TODO(student): If your stage needs setup beyond what StageLoader
        # already does (e.g., spawning a custom entity not driven by TMX),
        # do it here.

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self.player.update(dt)
        for entity in self.stage_data.entity_list:
            if entity.is_active:
                entity.update(dt)
        for checkpoint in self.stage_data.checkpoints:
            checkpoint.update(dt)
        self.camera.update(dt)
        self.hud.update(dt)
        self.message_box.update(dt)
        self.screen_banner.update(dt)

        self._check_attack_collisions()
        self._check_next_trigger()

        # TODO(student): Any additional per-frame logic specific to your
        # stage's academic feature (e.g., a FilterTools/VisionTools call
        # driving a custom mechanic) goes here.

    def draw(self, surface) -> None:
        offset = self.camera.offset
        self.stage_data.map_layer.draw(surface)
        for entity in self.stage_data.entity_list:
            if entity.is_visible:
                entity.draw(surface, offset)
        self.player.draw(surface, offset)
        self.hud.draw(surface)
        self.message_box.draw(surface)
        self.screen_banner.draw(surface)

    def _check_attack_collisions(self) -> None:
        """Provided. Matches the pattern in 05_ENEMY_SPEC.md §9.3. Do not modify."""
        if self.player.active_hitbox:
            for entity in self.stage_data.entity_list:
                if (
                    entity.is_active
                    and hasattr(entity, "hurtbox")
                    and self.player.active_hitbox.colliderect(entity.hurtbox)
                ):
                    entity.apply_hit(
                        damage=self.player.current_attack_damage,
                        source_position=self.player.rect.center,
                    )
                    self.player.consume_hitbox()

    def _check_next_trigger(self) -> None:
        """Provided. Do not modify."""
        if self.stage_data.next_trigger and self.player.rect.colliderect(
            self.stage_data.next_trigger
        ):
            EventBus.emit("STAGE_COMPLETE")
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
3. Define your boss's phases following the BossPhase pattern shown.
4. Fill in every # TODO(student) marker.
5. See 17_BOSS_SPEC.md for the full design contract of your assigned boss
   (if it is a syllabus-official or project-defined boss already documented
   there) — your implementation must match that specification's attack
   patterns, health values, and phase structure exactly. If your assigned
   boss is NOT yet documented in 17_BOSS_SPEC.md, work with the professor
   to define its design before writing combat logic.
"""

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
            phases=phases,
            # TODO(student): Set your boss's display name (used in the boss HUD)
            boss_name="Untitled Boss",
        )

    def _patrol_behavior(self, dt: float) -> None:
        # TODO(student): Implement this phase's idle/patrol movement.
        pass

    def _alert_behavior(self, dt: float) -> None:
        # TODO(student): Implement this phase's active-combat movement
        # and attack-pattern triggering, per your BossPhase.attack_patterns.
        pass

    def _get_animation_state(self) -> str:
        # TODO(student): Return the animation key matching self.state
        # and self.current_phase.
        return "idle"

    def _build_hitbox(self) -> pygame.Rect:
        # TODO(student): Define your boss's attack hitbox in LOCAL space
        # (offset from self.position). See 04_PLAYER_SPEC.md §10 for the
        # local-space hitbox pattern this mirrors.
        return pygame.Rect(0, 0, 32, 32)

    def _build_hurtbox(self) -> pygame.Rect:
        # TODO(student): Define your boss's damage-receiving hurtbox in
        # LOCAL space.
        return pygame.Rect(0, 0, 32, 32)
```

---

## 6. `README_template.md` (Stage Variant)

```markdown
---
assignment_type: stage
assignment_name: "TODO: Your stage's display name, e.g. La Soda"
assignment_id: "TODO: your_folder_name, e.g. stage1_2_la_soda"
zone: 1
student_name: "TODO: Your full name"
units_demonstrated: []
evaluation_milestone: "Evaluación Práctica I"
---

# TODO: Stage Title

## Narrative Context

TODO(student): Describe how your stage fits into its zone per
`16_WORLD_DESIGN.md`. What is this place? What happened here?

## Academic Concepts Demonstrated

TODO(student): For each unit listed in `units_demonstrated` above, explain
in 2-4 sentences which framework API you used and why. Follow the format
required by `08_SYLLABUS_MAPPING.md` for each unit — state the formula or
algorithm, not just the feature name.

### Unit II — Coordinate Systems and Transformations
TODO

### Unit III — Curves and Geometric Modeling
TODO

### Unit IV — Object and Scene Representation
TODO

### Unit V — Color, Transparency, and Lighting
TODO

(Add sections for Unit VI, VII, VIII, IX as your assignment progresses
through Evaluación Práctica II and III.)

## How to Run

```bash
python main.py --stage <your_assignment_id>
```

(TODO(student): confirm this matches the actual CLI/debug-launch mechanism
your professor's `main.py` exposes — see `25_IMPLEMENTATION_ROADMAP.md`
Phase 16 for the final launch flow.)

## Screenshots

TODO(student): Add before/after screenshots for any FilterTools/VisionTools
operations once you reach Evaluación Práctica II/III.
```

---

## 7. `README_template.md` (Boss Variant)

```markdown
---
assignment_type: boss
assignment_name: "TODO: Your boss's display name"
assignment_id: "TODO: your_folder_name, e.g. boss_rey"
zone: 2
student_name: "TODO: Your full name"
units_demonstrated: []
evaluation_milestone: "Evaluación Práctica I"
---

# TODO: Boss Title

## Narrative Context

TODO(student): Per `17_BOSS_SPEC.md` (if your boss is already documented
there) or your professor-approved design — describe this boss's origin,
nature, and role in the story.

## Phase Structure

TODO(student): Document each phase: health range, attack patterns, movement
type, and which academic unit each visual/mathematical effect demonstrates.

| Phase | Health Range | Attack Patterns | Academic Concept |
|---|---|---|---|
| 1 | TODO | TODO | TODO |

## Academic Concepts Demonstrated

(Same structure as the stage template — see `08_SYLLABUS_MAPPING.md`.)

## How to Run / Debug-Fight This Boss

TODO(student): document the debug-skip mechanism for testing your boss
without playing through the full game (see `25_IMPLEMENTATION_ROADMAP.md`
Phase 16 for what this mechanism is once implemented).
```

---

## 8. Definition of Done for This Template Set

(Restated and expanded from `25_IMPLEMENTATION_ROADMAP.md` Phase 15.)

- [ ] `stage_template.py` imports cleanly with zero changes (`python -c "import src.stages.stage_template.stage_template"` succeeds once copied into `src/stages/`).
- [ ] `stage_template.tmx` opens in Tiled with no validation errors and passes `StageLoader.load()` with zero exceptions (verified by a dedicated `tests/test_student_template.py` smoke test — see §9 below).
- [ ] `boss_template.py` imports cleanly and `BossTemplate(pygame.Vector2(0, 0))` constructs without exception.
- [ ] Both `README_template.md` files contain valid YAML front-matter parseable by a basic `yaml.safe_load()` call (no syntax errors in the placeholder values).
- [ ] **15-minute onboarding test:** the professor (or a TA acting as a test student) copies `stage_template/` to a new `src/stages/test_assignment/` folder, renames the file/class/TMX, runs it, and reaches a playable (if empty) stage with working player movement and a functioning `NextTrigger` — within 15 minutes, without consulting any document beyond this one and `21_COURSE_SCHEDULE.md` Class 1 instructions.

### 8.1 `tests/test_student_template.py`

| Test | Assertion |
|---|---|
| `test_stage_template_tmx_loads` | `StageLoader.load(student_templates/stage_template/stage_template.tmx)` completes without exception |
| `test_stage_template_has_required_objects` | The loaded `StageData` has exactly one `PlayerSpawn`-derived `spawn_point`, one `next_trigger`, and `len(checkpoints) == 1` |
| `test_boss_template_constructs` | `BossTemplate(pygame.Vector2(0,0))` does not raise |
| `test_boss_template_has_one_phase` | `len(BossTemplate(...).phases) == 1` (the placeholder phase — confirms the template itself, not a partially-filled student copy) |
| `test_readme_templates_parse_as_yaml` | Both `README_template.md` front-matter blocks parse via `yaml.safe_load()` without error |

This test file is added to the Phase 15 gate in `24_TEST_PLAN.md`'s execution summary (§16) under a row for Phase 15, which was previously listed as "manual onboarding test only" — the automatable subset above now supplements that manual check.

---

## 9. Relationship to Student Assignment Folders

Once a student completes the 15-minute onboarding copy-and-rename, their working folder lives at `src/stages/<assignment_id>/` (per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §7 and `03_ARCHITECTURE.md` §1) and is **no longer** part of `student_templates/`. The template directory itself is never modified after initial professor setup — it is read-only scaffolding that every student copies from independently, so one student's in-progress work never collides with another's, consistent with the individual-assignment model confirmed in `00_SYLLABUS_ALIGNMENT_AUDIT.md` §2 A.1.
