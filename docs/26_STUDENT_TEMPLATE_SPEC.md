---
document_id: "LOI-TEMPLATE-026"
title: "Legacy of InFest — Student Template Specification"
aliases: ["Student Template Spec"]
tags: ["template", "student", "starter"]
description: "Exact starter files every student copies"
source: "docs/26_STUDENT_TEMPLATE_SPEC.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Student Template Specification

**Document ID:** LOI-TEMPLATE-026  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires `77_SYLLABUS_ALIGNMENT_AUDIT.md`, `22_API_CONTRACTS.md`, `23_DATA_SCHEMAS.md`, `21_COURSE_SCHEDULE.md`  
**Audience:** Professor, AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Purpose

`77_SYLLABUS_ALIGNMENT_AUDIT.md` §7 and `03_ARCHITECTURE.md` §1 both reference `student_templates/stage_template/` and `student_templates/boss_template/` as the canonical starting point every student copies in Class 1 (per `21_COURSE_SCHEDULE.md`). No prior document defines what those template files actually contain. This document is that definition — exact file contents, placeholders, and the README a student fills in.

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
> **Actualizado 2026-08-11 (AUD-417). La plantilla ya no es «mínima»: es un
> catálogo.** Medida con la rúbrica del propio curso (`scripts/grade_stage.py`),
> la versión mínima que este documento describía sacaba **84/130 = 64,6 %**, y
> `validate_tmx.py` la daba por `[OK]` sin decir nada — el estudiante empezaba
> cuesta arriba y sin saberlo. Ahora saca **92,3 %** y trae **un ejemplar de
> cada tipo** que un nivel puede llevar.
>
> Y no más de uno: con tres coleccionables y tres puntos de control llegaba a
> 100/130 y `test_teaching_tools` saltó con razón —«stage0 saca 100 % y la
> plantilla vacía 100 %: la rúbrica no distingue trabajo hecho de trabajo sin
> hacer»—. Demostrar cada tipo, no llenar la rúbrica.
>
> **El fichero se genera**, no se edita: `tools/generate_stage_template.py`,
> con `tests/test_la_plantilla_del_estudiante.py` comprobando que el TMX del
> repositorio y su generador siguen de acuerdo. Es el mismo trato que
> `stage_mecanicas` desde AUD-153, y por el mismo motivo: un defecto aquí se
> multiplica por veintiséis antes de que nadie lo ejecute.

| Element | Content |
|---|---|
| Map dimensions | 60 tiles wide × 16 tiles tall (960×256 px) — cabe un hueco exigente y sigue entrando entera en Tiled |
| Tileset reference | `assets/tilesets/tileset_stage0.png` (neutral, always available, swappable later) |
| Layers (all 8 required, per `06_TMX_SPEC.md` §3.1) | `BG_Far`, `BG_Mid`, `BG_Near` y `Terrain_Detail` vacías; `Terrain` — suelo de dos filas **con un hueco de 5 baldosas**; `Objects` — see §4.2; `Collision` — dos `Solid` (el suelo partido por el hueco) y un `Platform` sobre él; `FG_Overlay` — empty |
| Map custom properties | `schema_version=1`, `stage_id="stage_template"`, `stage_name="Untitled Stage"`, **`author="TU NOMBRE AQUI"`**, `time_limit=120`, `bgm_track="bgm_stage0"`, `climate="clear"`, `zone=1`, `ambient_light=1.0` |

**Sobre `author`:** la puntúa la rúbrica (`grade_stage.REQUIRED_GRADE_PROPS`) y
hasta AUD-416 ninguna herramienta se lo decía al estudiante. Lleva un valor que
pide ser cambiado y no una cadena vacía, porque un campo en blanco se entrega
en blanco.

**Sobre el hueco:** 5 baldosas son 80 px. Medido con
`JumpEnvelope.from_settings()`, el salto normal cruza hasta **85,5 px** y lo
«cómodo» acaba en **68,4**, así que 80 cae en *exigente* y se cruza sin salto
aéreo. Con tres baldosas el calificador respondía «el recorrido no tiene ningún
salto exigente»; con siete haría falta una técnica que aún no está
desbloqueada.

### 4.2 Required `Objects` Layer Content

| Object | Por qué está |
|---|---|
| `PlayerSpawn_01` | Sobre el suelo, cerca del borde izquierdo |
| `Checkpoint_01`, `Checkpoint_02` | `checkpoint_id` 0 y 1 — enseñan que va correlativo. Dos, no tres: colocar el resto según dónde duela morir es la decisión que el estudiante tiene que aprender |
| `NextTrigger_01` | Borde derecho, altura completa |
| `Slope_sube`, `Slope_baja` | Suelo inclinado, con `sube="derecha"` / `"izquierda"` |
| `Walker_ejemplo_01`, `Flying_ejemplo_01`, `Shooter_ejemplo_01` | Un arquetipo de cada uno. Los tres básicos y no especies del bestiario: son los que la guía explica primero y los que se sustituyen por los propios sin tocar nada más |
| `Pickup_ejemplo_01` | Con `item_id="moneda"` — sin `item_id` el cargador lo ignora con un aviso |
| `Light_ejemplo_01` | `radius`, `color`, `intensity`. Es el objeto que más se beneficia de `preview_tmx.py`: en Tiled es un cuadrado de 16×16 idéntico a cualquier otro |
| `Mensaje_bienvenida` | Un `MessageTrigger` con texto que pide ser editado |
| `Pinchos_ejemplo` | Un `HazardZone` **en `Objects`, no en `Collision`** — ver abajo |
| `Objetivo_principal` | Un `Objective` (AUD-400) con `objective_id`, `text` y `kind="llegar"` |

**Por qué `HazardZone` va en `Objects` y no en `Collision`.** Es el error que
comete todo el mundo y que un mapa del motor todavía tiene
(`stage3_3_el_patio`, objeto id=130): la capa `Collision` sólo acepta `Solid` y
`Platform`, así que cualquier otra cosa puesta ahí **se trata como suelo
sólido**. La trampa deja de hacer daño y encima se convierte en plataforma. La
plantilla enseña dónde va cada cosa, y
`tests/test_la_plantilla_del_estudiante.py` lo fija.

**Ya no es «el escenario válido mínimo».** Lo era, y sacaba 64,6 %. Ahora es un
catálogo con un ejemplar de cada cosa: se aprende más borrando un enemigo que
sobra que buscando en la documentación cómo se coloca el primero. Lo que el
estudiante añade sigue siendo lo suyo —más enemigos, su terreno, su zona— según
`16_WORLD_DESIGN.md` y `18_ENEMY_ROSTER.md`.

### 4.3 Cómo se genera

`python tools/generate_stage_template.py` lo escribe;
`python tools/generate_stage_template.py --check` falla si el fichero del
repositorio se ha editado a mano y se ha desviado del generador. **No se edita
el TMX directamente**: el porqué de cada objeto vive en el generador, y editar
a mano deja el generador viejo hasta que la siguiente ejecución borra los
cambios sin avisar.

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
| `TestStageTemplate::test_import` | `StageTemplate` can be imported |
| `TestStageTemplate::test_can_instantiate` | `StageTemplate(context)` constructs without exception |
| `TestStageTemplate::test_tmx_exists` | The default TMX file exists at `TMX_PATH` |
| `TestStageTemplate::test_default_tmx_has_required_layers` | The TMX contains all 8 required layer names |
| `TestStageTemplate::test_has_stage_scene_attributes` | Instance has `_stage_data`, `_player`, `_camera` (inherited from StageScene) |
| `TestBossTemplate::test_import` | `BossTemplate` can be imported |
| `TestBossTemplate::test_constructs` | `BossTemplate(pygame.Vector2(0, 0))` does not raise |
| `TestBossTemplate::test_has_required_methods` | Instance has `_patrol_behavior`, `_alert_behavior`, `_get_animation_key`, `_build_hitbox`, `_build_hurtbox` |
| `TestBossTemplate::test_has_one_phase` | `len(BossTemplate(...).phases) == 1` (the placeholder phase) |

---

## 9. Relationship to Student Assignment Folders

Once a student completes the 15-minute onboarding copy-and-rename, their working folder lives at `src/stages/<assignment_id>/` (per `77_SYLLABUS_ALIGNMENT_AUDIT.md` §7 and `03_ARCHITECTURE.md` §1) and is **no longer** part of `student_templates/`. The template directory itself is never modified after initial professor setup — it is read-only scaffolding that every student copies from independently, so one student's in-progress work never collides with another's, consistent with the individual-assignment model confirmed in `77_SYLLABUS_ALIGNMENT_AUDIT.md` §2 A.1.


--- Traducción al Español ---

## Especificación de Plantillas para Estudiantes

Este documento especifica los archivos de plantilla que los estudiantes copian para comenzar sus asignaciones.

### Plantilla de Escenario
- `stage_template.py` — Clase base de escenario
- `stage_template.tmx` — Mapa Tiled con estructura de capas
- `README_template.md` — Documentación requerida

### Plantilla de Jefe
- `boss_template.py` — Clase base de jefe
- `README_template.md` — Documentación requerida

Para instrucciones detalladas de uso y verificación, consultar el documento original en inglés.
