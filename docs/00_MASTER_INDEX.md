---
document_id: "LOI-INDEX-000"
title: "Legacy of InFest — Master Documentation Index"
aliases: ["Master Index", "Documentation Index"]
tags: ["index", "entry-point"]
description: "Single authoritative entry point for all documentation"
source: "docs/00_MASTER_INDEX.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Master Documentation Index
**Document ID:** LOI-INDEX-000  
**Version:** 1.0.0  
**Status:** Official — Single Entry Point  
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Purpose

The complete Legacy of InFest documentation set spans **65 documents** (00–52, 28b–34d, creation guides) issued across **7 packages** (v1 through v7, plus v10 in-repo docs) at different points in the project's development. Each package shipped with its own local README, but none of them indexes the *entire* set, and 6 documents were superseded by corrected versions issued in the v4 (realignment) package. This document is the **single, authoritative, unified index** — read this first, regardless of which package's ZIP file you happen to have open.

**If you are an AI coding assistant about to start work, read this document, then go directly to `25_IMPLEMENTATION_ROADMAP.md`.**

---

## 2. The Authoritative Document List (Use This, Not Any Package's Local README)

Documents marked **[SUPERSEDED]** below exist in their originating package (v1, v2, or v3) but have been replaced by a corrected version issued in the v4 realignment package. **Always use the v4 version of these six documents.** All other documents are used from their original issuing package — there is only one valid copy.

| #   | Document                             | Authoritative Source Package            | Status                                                               |
| --- | ------------------------------------ | --------------------------------------- | -------------------------------------------------------------------- |
| 00  | [[`00_SYLLABUS_ALIGNMENT_AUDIT.md`]] | v4 (`legacy_of_infest_docs_corrected/`) | Current                                                              |
| 01  | `01_PROJECT_CHARTER.md`              | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v1 original                                     |
| 02  | `02_CODEX_CONTEXT.md`                | v1 (`legacy_of_infest_docs/`)           | Current — unchanged since v1                                         |
| 03  | `03_ARCHITECTURE.md`                 | v11 (in-repo, 2026-07-11)               | Current — corrected: 800×600 resolution, BaseScene context+lifecycle |
| 04  | `04_PLAYER_SPEC.md`                  | v11 (in-repo, 2026-07-11)               | Current — corrected: 25 states, ULTIMATE→CHARGE_ATTACK               |
| 05  | `05_ENEMY_SPEC.md`                   | v11 (in-repo, 2026-07-11)               | Current — verified: 8 enemy types documented                         |
| 06  | `06_TMX_SPEC.md`                     | v1 (`legacy_of_infest_docs/`)           | Current — unchanged since v1                                         |
| 07  | `07_STAGE0_DESIGN.md`                | v1 (`legacy_of_infest_docs/`)           | Current — unchanged since v1                                         |
| 08  | `08_SYLLABUS_MAPPING.md`             | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v1 original                                     |
| 09  | `09_HUD_SPEC.md`                     | v1 (`legacy_of_infest_docs/`)           | Current — unchanged since v1                                         |
| 10  | `10_LIBRARIES_AND_DEPENDENCIES.md`   | v1 (`legacy_of_infest_docs/`)           | Current — unchanged since v1                                         |
| 11  | `11_FILTER_TOOLS_SPEC.md`            | v2 (`legacy_of_infest_docs_v2/`)        | Current — unchanged since v2                                         |
| 12  | `12_VISION_TOOLS_SPEC.md`            | v2 (`legacy_of_infest_docs_v2/`)        | Current — unchanged since v2                                         |
| 13  | `13_PATTERN_RECOGNITION_SPEC.md`     | v2 (`legacy_of_infest_docs_v2/`)        | Current — unchanged since v2                                         |
| 14  | `14_PROFESSOR_DELIVERABLE_MATRIX.md` | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v2 original                                     |
| 15  | `15_ACADEMIC_DEMO_SCENES.md`         | v2 (`legacy_of_infest_docs_v2/`)        | Updated — v1.1 adds 4 theory lab scenes (Units II, III, V, VI)       |
| 16  | `16_WORLD_DESIGN.md`                 | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v3 original (terminology only)                  |
| 17  | `17_BOSS_SPEC.md`                    | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v3 original                                     |
| 18  | `18_ENEMY_ROSTER.md`                 | v3 (`legacy_of_infest_docs_v3/`)        | Current — unchanged since v3                                         |
| 19  | `19_NARRATIVE_AND_LORE.md`           | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v3 original                                     |
| 20  | `20_ASSET_BIBLE.md`                  | v3 (`legacy_of_infest_docs_v3/`)        | Current — unchanged since v3                                         |
| 21  | `21_COURSE_SCHEDULE.md`              | v4 (`legacy_of_infest_docs_corrected/`) | Current — new in v4                                                  |
| 22  | `22_API_CONTRACTS.md`                | v11 (in-repo, 2026-07-11)               | Current — corrected: 800×600, SlideTransition, play_sfx volume       |
| 23  | `23_DATA_SCHEMAS.md`                 | v5 (`legacy_of_infest_docs_v5/`)        | Current                                                              |
| 24  | `24_TEST_PLAN.md`                    | v5 (`legacy_of_infest_docs_v5/`)        | Current                                                              |
| 25  | `25_IMPLEMENTATION_ROADMAP.md`       | v5 (`legacy_of_infest_docs_v5/`)        | Current                                                              |
| 26  | `26_STUDENT_TEMPLATE_SPEC.md`        | v5 (`legacy_of_infest_docs_v5/`)        | Current                                                              |
| 27  | `27_ACADEMIC_RUBRICS.md`             | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 28  | `28_DECISION_LOG.md`                 | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 28b | `28_SAMPLE_SYLLABUS.md`              | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 29  | `29_GIT_WORKFLOW_AND_STANDARDS.md`   | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 29b | `29_TA_GUIDE.md`                     | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 30  | `30_TICKET_BACKLOG.md`               | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 30b | `30_ASSIGNMENT_01_STAGE_DESIGN.md`   | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 31  | `31_RISK_REGISTER.md`                | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 31b | `31_ASSIGNMENT_02_BOSS_DESIGN.md`    | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 32  | `32_ENVIRONMENT_SETUP_GUIDE.md`      | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 32b | `32_ASSIGNMENT_03_LAB_EXERCISES.md`  | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 33  | `33_SCOPE_ADJUSTMENT.md`             | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 33b | `33_ASSIGNMENT_04_FINAL_PROJECT.md`  | v6 (`legacy_of_infest_docs_v6/`)        | Current                                                              |
| 34  | `34_CLASS_MATERIALS.md`              | v11 (in-repo, 2026-07-11)               | Current — corrected: real file status indicators                     |
| 34b | `34_EDUCATIONAL_ROADMAP.md`          | v11 (in-repo, 2026-07-11)               | Current — educational roadmap                                        |
| 34c | `34_LIVE_CODE_u02_vector_class.py`   | v11 (in-repo)                           | Current — live coding: vector class (Unit II)                        |
| 34d | `34_LIVE_CODE_u07_convolution.py`    | v11 (in-repo)                           | Current — live coding: convolution (Unit VII)                        |
| 35  | `35_USER_MANUAL.md`                  | v7 (in-repo)                            | Current — new                                                        |
| 36  | `36_STUDENT_MANUAL.md`               | v7 (in-repo)                            | Current — new                                                        |
| 37  | `37_DEMO_QUICK_GUIDE.md`             | v7 (in-repo)                            | Current — new                                                        |
| 38  | `38_STAGE_BOSS_GUIDE.md`             | v7 (in-repo)                            | Current — new                                                        |
| 39  | `39_REPORTE_ANALISIS_CODIGO.md`      | v10 (in-repo)                           | Current — code analysis report                                       |
| 40  | `40_DIALOGUE_SYSTEM.md`              | v10 (in-repo)                           | Current — branching dialogue with portraits                          |
| 41  | `41_BESTIARY_CODEX.md`               | v10 (in-repo)                           | Current — enemy tracking system                                      |
| 42  | `42_CUTSCENE_SYSTEM.md`              | v10 (in-repo)                           | Current — scripted cutscene system                                   |
| 43  | `43_SPEEDRUN_MODE.md`                | v10 (in-repo)                           | Current — speedrun timer + ghost data                                |
| 44  | `44_BOSS_RUSH_MODE.md`               | v10 (in-repo)                           | Current — boss gauntlet mode                                         |
| 45  | `45_SWIMMING_SPEC.md`                | v10 (in-repo)                           | Current — swimming mechanics                                         |
| 46  | `46_FOG_OF_WAR.md`                   | v10 (in-repo)                           | Current — fog of war overlay                                         |
| 47  | `47_WATER_EFFECT.md`                 | v10 (in-repo)                           | Current — water VFX                                                  |
| 48  | `48_SCREEN_TRANSITIONS.md`           | v10 (in-repo)                           | Current — fade/wipe/slide/circle                                     |
| 49  | `49_AMBIENT_AUDIO.md`                | v10 (in-repo)                           | Current — ambient audio system                                       |
| 50  | [[`50_IMPROVEMENT_ROADMAP.md`]]      | v11 (in-repo, 2026-07-11)               | Current — corrected: P0 items resolved, accurate metrics             |
| 51  | `[[51_IMPLEMENTATION_AUDIT.md]]`     | v10 (in-repo)                           | Current — evidence-based gap analysis (corrected 2026-07-11)         |
| 52  | `[[52_MULTIDISCIPLINARY_AUDIT.md]]`  | v12 (in-repo, 2026-07-14)              | Current — multi-disciplinary audit with 44 category scores           |
| —   | `BOSS_CREATION.md`                   | v10 (in-repo)                           | Current — boss creation guide                                        |
| —   | `ENEMY_CREATION.md`                  | v10 (in-repo)                           | Current — enemy creation guide                                       |
| —   | `SCENE_CREATION.md`                  | v10 (in-repo)                           | Current — scene creation guide                                       |
| 53  | `53_MECANICAS_DEL_DOSSIER_VIABILIDAD.md` | v13 (in-repo)                      | Current — mechanic feasibility dossier analysis |
| 54  | `54_MECANICAS_TOP200_VIABILIDAD.md`  | v13 (in-repo)                           | Current — top-200 mechanics viability |
| 55  | `55_MECANICAS_JEFES_TOP200_VIABILIDAD.md` | v13 (in-repo)                     | Current — boss mechanics top-200 viability |
| 56  | `56_FASE_5_ECS_Y_MECANICAS.md`       | v13 (in-repo)                           | Current — phase 5 ECS and mechanics |
| 57  | `57_COLISIONES_Y_DEUDAS_SALDADAS.md` | v13 (in-repo)                           | Current — collisions and settled debts |
| 58  | `58_VALIDACION_DE_SISTEMAS.md`       | v13 (in-repo)                           | Current — systems validation |
| 59  | `59_STAGE_0_REGENERADO.md`           | v13 (in-repo)                           | Current — stage 0 regeneration |
| 60  | `60_GUIA_COMPLETA_DEL_MOTOR.md`      | v13 (in-repo)                           | Current — complete engine guide (Spanish) |
| 61  | `61_AUDITORIA_AAA_2026-08.md`        | v13 (in-repo)                           | Current — AAA audit 2026-08 |
| 62  | `62_ESTADO_DEL_PROYECTO.md`          | v13 (in-repo)                           | Current — project state |
| 63  | `63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md` | v13 (in-repo)                        | Current — registry of what is not implemented |
| 64  | `64_GAME_DESIGN_DOCUMENT.md`         | v13 (in-repo)                           | Current — complete game design reference (GDD) |
| 65  | `65_EL_LORE_EXTENSO.md`              | v1 (in-repo)                            | Current — extensive canon lore expansion (Spanish) |
| 66  | `66_GUIA_DE_LEVEL_DESIGN.md`         | v1 (in-repo)                            | Current — level design guide: difficulty, dimensions, enemy composition (Spanish) |
| 67  | `67_ESPECIFICACION_DE_NIVELES_Y_JEFES.md` | v1 (in-repo)                     | Current — mandatory level/boss rules per deliverable 1-2-3 + day/night arcs; per-level sheets in `docs/niveles/` (Spanish) |
| 67b | `67_CURVA_DE_DIFICULTAD.md`          | v1 (in-repo)                            | Current — measured difficulty curve (AUD-151) |
| 68  | `68_AUDITORIA_DE_INGENIERIA.md`      | v1 (in-repo)                            | Current — engineering audit AUD-157/160 |
| 69  | `69_PROMPT_AUDITORIA_MAESTRO.md`     | v1 (in-repo)                            | Current — master audit prompt + critique of the previous one |
| 70  | `70_INFORME_DE_AUDITORIA_VIVO.md`    | v1 (in-repo)                            | Current — living audit report, updated per iteration |
| 71  | `71_REVISION_DE_JUEGO.md`            | v1 (in-repo)                            | Current — measured review of mechanics, gameplay, funfactor and level design (D5-D9) |
| —   | `niveles/15_DISENO_4_1_EL_CEMENTERIO.md` | v1 (in-repo)                        | Current — proposed design for level 4-1: Magus-style progression, La Cegua, advancing flames, storm, student tombstones (Spanish) |
| —   | `52_EVENT_MAP.md`                    | v1 (in-repo)                            | Current — event bus map |
| —   | `AUDIT_2026-07.es.md`                | v1 (in-repo)                            | Current — July 2026 audit (Spanish side of the enforced bilingual pair) |
| —   | `AUDIT_2026-07.en.md`                | v1 (in-repo)                            | Current — July 2026 audit (English side; `test_documentacion_bilingue.py` keeps both in sync) |
| —   | `AUDITORIA_2026-07-27_MEDICION.md`   | v1 (in-repo)                            | Historical — measurement record |
| —   | `AUDIT_VERIFICATION_2026-07-27.md`   | v1 (in-repo)                            | Historical — verification record |
| —   | `ESTRATEGIA_2026-07-27.md`           | v1 (in-repo)                            | Historical — strategy note |
| —   | `FASES_1_2_3_COMPLETADAS.md`         | v1 (in-repo)                            | Historical — phases 1-3 completion record |
| —   | `VERIFICACION_FINAL.md`              | v1 (in-repo)                            | Historical — final verification record |
| —   | `STAGE_CREATION.md`                  | v10 (in-repo)                           | Current — stage creation guide                                       |

> **AUD-169.** Esta tabla se declara «la lista autoritativa» y no mencionaba
> trece documentos, entre ellos `52_EVENT_MAP.md`, `67_CURVA_DE_DIFICULTAD.md` y
> `68_AUDITORIA_DE_INGENIERIA.md`. La fila 68 apuntaba además a
> `niveles/15_DISENO_4_1_EL_CEMENTERIO.md`, que no es el documento 68. Una lista
> autoritativa incompleta es peor que ninguna: quien la consulta concluye que lo
> que falta no existe. `tests/test_rutas_de_los_documentos.py` lo comprueba
> ahora en cada ejecución.

**Recommended action before implementation begins:** Consolidate all current-status documents into a single flat `docs/` folder in the actual repository (per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §7's structure), discarding the superseded v1/v2/v3 originals of the six documents listed as "supersedes" above. This index becomes redundant once that consolidation happens — at that point, a simple numbered `docs/` folder listing is self-explanatory.

---

## 3. Documentation Coverage Map — The Four Layers

This documentation set covers four distinct layers. Every document is classified below so you can find what you need by the *kind* of question you're asking, not just by number.

### 3.1 Academic Layer — "What is this course, and how is it graded?"

| Document | Answers |
|---|---|
| `00_SYLLABUS_ALIGNMENT_AUDIT.md` | What does the official syllabus actually say, and where did earlier drafts deviate from it? |
| `08_SYLLABUS_MAPPING.md` | Which framework component maps to which syllabus unit? |
| `14_PROFESSOR_DELIVERABLE_MATRIX.md` | Full syllabus-to-framework-to-assessment traceability |
| `21_COURSE_SCHEDULE.md` | What happens in each of the 11 classes + Invenio Fest? |
| `27_ACADEMIC_RUBRICS.md` | How many points for what, on every graded instrument? |
| `31_RISK_REGISTER.md` | What academic/pedagogical risks exist and how are they mitigated? |

### 3.2 Analysis & Design Layer — "What are we building, and why?"

| Document | Answers |
|---|---|
| `01_PROJECT_CHARTER.md` | Scope, vision, stakeholders, repo structure at a glance |
| `02_CODEX_CONTEXT.md` | Project philosophy, coding rules, architecture rules |
| `16_WORLD_DESIGN.md` | The 4 zones, 14 stages, narrative-to-gameplay mapping |
| `17_BOSS_SPEC.md` | All 4 boss designs, phase-by-phase |
| `18_ENEMY_ROSTER.md` | Every standard enemy, by zone |
| `19_NARRATIVE_AND_LORE.md` | Story, characters, cultural grounding |
| `20_ASSET_BIBLE.md` | Every visual/audio asset, path, dimensions, palette |
| `28_DECISION_LOG.md` | Why each major technical/design choice was made (ADRs) |

### 3.3 Implementation/Architecture Layer — "How is the system structured?"

| Document | Answers |
|---|---|
| `03_ARCHITECTURE.md` | Full folder structure, module responsibilities, data flow |
| `04_PLAYER_SPEC.md` | Player physics, states (19 states incl. SWIMMING), combat — complete behavioral spec |
| `05_ENEMY_SPEC.md` | Enemy base class and 8 enemy types (Walker, Flying, Shooter, Charger, Archer, Brute, Caster, Assassin) |
| `06_TMX_SPEC.md` | Map file format, layers, object types |
| `07_STAGE0_DESIGN.md` | The professor's reference-implementation stage, zone by zone |
| `09_HUD_SPEC.md` | HUD layout, hearts, timer, messages, Game Over |
| `10_LIBRARIES_AND_DEPENDENCIES.md` | Every third-party library, purpose, integration rules |
| `11_FILTER_TOOLS_SPEC.md` | Unit VII image processing subsystem |
| `12_VISION_TOOLS_SPEC.md` | Unit VIII segmentation subsystem |
| `13_PATTERN_RECOGNITION_SPEC.md` | Unit IX machine learning subsystem |
| `15_ACADEMIC_DEMO_SCENES.md` | 10 interactive demo/lab scenes + 3 new UI scenes (inventory, achievements, world map) |

### 3.4 Code/Build Layer — "What do I actually write, in what order, and how do I know it's correct?"

| Document | Answers |
|---|---|
| `22_API_CONTRACTS.md` | Exact function/class signatures — the syntax authority |
| `23_DATA_SCHEMAS.md` | Exact data shapes crossing module boundaries |
| `24_TEST_PLAN.md` | Exact test cases per module |
| `25_IMPLEMENTATION_ROADMAP.md` | The 16-phase build order with Definition of Done |
| `26_STUDENT_TEMPLATE_SPEC.md` | The exact starter files every student copies |
| `29_GIT_WORKFLOW_AND_STANDARDS.md` | Branching, commits, PRs, code review |
| `30_TICKET_BACKLOG.md` | Every roadmap phase decomposed into atomic tickets |
| `32_ENVIRONMENT_SETUP_GUIDE.md` | Step-by-step machine setup, troubleshooting |

---

## 4. Reading Paths by Role

### 4.1 "I am an AI coding assistant starting implementation from zero"

```
1. This document (00_MASTER_INDEX.md)
2. 00_SYLLABUS_ALIGNMENT_AUDIT.md   — understand what's authoritative
3. 02_CODEX_CONTEXT.md              — understand the rules
4. 25_IMPLEMENTATION_ROADMAP.md     — understand the build order
5. 30_TICKET_BACKLOG.md             — pick up Phase 0, Ticket T0.1
6. 22_API_CONTRACTS.md + 23_DATA_SCHEMAS.md  — keep open as syntax/shape reference while coding
7. 24_TEST_PLAN.md                  — write tests for whatever phase you're on
8. 28_DECISION_LOG.md               — consult before proposing any architectural change
```

### 4.2 "I am the professor preparing for Class 1"

```
1. 21_COURSE_SCHEDULE.md            — confirm the calendar
2. 32_ENVIRONMENT_SETUP_GUIDE.md    — verify it works on your own machine first
3. 25_IMPLEMENTATION_ROADMAP.md Phase 0-9 — confirm these are complete before Class 1
4. 26_STUDENT_TEMPLATE_SPEC.md      — confirm templates exist and the 15-minute test passes
5. 27_ACADEMIC_RUBRICS.md           — have these ready for grading from Class 5 onward
6. 31_RISK_REGISTER.md §8           — review open risks before term start
```

### 4.3 "I am a student starting my assignment"

```
1. 32_ENVIRONMENT_SETUP_GUIDE.md    — get your machine working
2. 26_STUDENT_TEMPLATE_SPEC.md §8   — copy your template, 15-minute onboarding
3. 16_WORLD_DESIGN.md               — find your assigned zone/stage
   (or 17_BOSS_SPEC.md if assigned a boss)
4. 18_ENEMY_ROSTER.md               — find your zone's enemies (Stage assignments)
5. 08_SYLLABUS_MAPPING.md           — understand what each milestone requires
6. 36_STUDENT_MANUAL.md             — complete student manual with all references
7. 15_ACADEMIC_DEMO_SCENES.md       — explore the 10 interactive theory labs (Units II–IX)
8. 37_DEMO_QUICK_GUIDE.md           — quick reference for using the 10 demos
9. 38_STAGE_BOSS_GUIDE.md           — quick reference for building your stage/boss
10. 27_ACADEMIC_RUBRICS.md §2-4     — understand exactly how you'll be scored
11. 29_GIT_WORKFLOW_AND_STANDARDS.md — understand the branch/commit/PR process
```

### 4.4 "I am reviewing a student submission"

```
1. 27_ACADEMIC_RUBRICS.md           — the scoring criteria for this milestone
2. 29_GIT_WORKFLOW_AND_STANDARDS.md §5 — the code review checklist
3. 08_SYLLABUS_MAPPING.md           — verify claimed units are actually demonstrated
4. 23_DATA_SCHEMAS.md §7            — verify README front-matter is valid
```

---

## 5. Precedence Rules (Consolidated)

When two documents appear to disagree, resolve using this table (also stated locally in `25_IMPLEMENTATION_ROADMAP.md`'s package README — restated here as the single global authority):

| When This... | ...Conflicts With This... | This One Wins | Reason |
|---|---|---|---|
| `00_SYLLABUS_ALIGNMENT_AUDIT.md` | Any document issued before it | Audit wins | It is the authoritative reconciliation against the real syllabus |
| `22_API_CONTRACTS.md` | Any narrative spec (04, 05, 06, 09, 11, 12, 13, 17) | Contracts win | ...for **syntax** only |
| Narrative spec (04, 05, 06, 09, 11, 12, 13, 17) | `22_API_CONTRACTS.md` | Narrative spec wins | ...for **behavior** only |
| `23_DATA_SCHEMAS.md` | Any document's prose description of a data structure | Schemas win | Exact field names/types |
| `25_IMPLEMENTATION_ROADMAP.md` | Developer/AI intuition about build order | Roadmap wins | Sequencing dependencies are non-obvious by design |
| `28_DECISION_LOG.md` | A new proposal to change an already-decided architecture choice | Decision Log wins, unless a new ADR is added | Prevents re-litigating settled decisions |
| `27_ACADEMIC_RUBRICS.md` | Any informal grading intuition | Rubric wins | Ensures grading consistency and defensibility |

---

## 6. Document Count Summary

| Package | Documents | New in This Package | Superseded by Later Package |
|---|---|---|---|
| v1 (`legacy_of_infest_docs/`) | 01–10 | 10 | 01, 03, 08 (by v4) |
| v2 (`legacy_of_infest_docs_v2/`) | 11–15 | 5 | 14 (by v4) |
| v3 (`legacy_of_infest_docs_v3/`) | 16–20 | 5 | 16, 17, 19 (by v4) |
| v4 (`legacy_of_infest_docs_corrected/`) | 00, 01, 03, 08, 14, 16, 17, 19, 21 | 2 new (00, 21) + 7 corrected | — |
| v5 (`legacy_of_infest_docs_v5/`) | 22–26 | 5 | — |
| v6 (`legacy_of_infest_docs_v6/`) | 27–33, 28b–33b | 11 | — |
| **Total unique, current documents** | **65** (00–52, 28b–34d, creation guides) | | |
| v7 (in-repo updates) | 15, 03, 28, 21, 08, 22, 30 | 7 updated | — |
| v8–v10 (sessions) | 10 lab scenes, registry, panels, layouts, debug, scripts, docs 35–51, creation guides | 20 new + all re-audited | — |
| v11 (2026-07-11 alignment) | 03, 04, 05, 22, 34, 50, 00 | 7 corrected |
| v12 (2026-07-14) | 52_MULTIDISCIPLINARY_AUDIT.md | 1 new | — |

---

## 7. What Comes After Document 32

At this point, the documentation set covers all four layers — Academic, Analysis/Design, Implementation/Architecture, and Code/Build — completely enough to begin Phase 0 of `25_IMPLEMENTATION_ROADMAP.md` with no remaining undefined decisions blocking a coding assistant.

Any further documents should be **generated only in response to a concrete gap discovered during actual implementation** (logged first in `KNOWN_GAPS.md` per `23_DATA_SCHEMAS.md` §8, and in `31_RISK_REGISTER.md` if it represents an ongoing risk rather than a one-time gap) — not speculatively.

The two items previously tracked as open/deferred have both been resolved by professor confirmation:

1. **Matplotlib's role** — confirmed as classroom/lab-instructional use only (per `21_COURSE_SCHEDULE.md`'s Quices/Labs), not a Legacy of InFest framework integration point. No `src/` call site is required. (`31_RISK_REGISTER.md` RISK-A03, closed.)
2. **El Gavilán Camionero Mascarero** — confirmed as the official, permanent Zone 3 boss, no longer pending or subject to reassignment. (`31_RISK_REGISTER.md` RISK-A04, closed; `28_DECISION_LOG.md` ADR-008, accepted final.)

With both items closed, the documentation set has **no remaining open design decisions** blocking implementation.


---
## 🔗 Documentos Relacionados

- [[00_SYLLABUS_ALIGNMENT_AUDIT.md|Syllabus Alignment Audit]]
- [[01_PROJECT_CHARTER.md|Project Charter]]
- [[02_CODEX_CONTEXT.md|Codex Context]]
- [[03_ARCHITECTURE.md|Architecture]]
- [[04_PLAYER_SPEC.md|Player Specification]]
- [[05_ENEMY_SPEC.md|Enemy Specification]]
- [[06_TMX_SPEC.md|TMX Specification]]
- [[07_STAGE0_DESIGN.md|Stage 0 Design]]
- [[08_SYLLABUS_MAPPING.md|Syllabus Mapping]]
- [[09_HUD_SPEC.md|HUD Specification]]
- [[10_LIBRARIES_AND_DEPENDENCIES.md|Libraries and Dependencies]]
- [[11_FILTER_TOOLS_SPEC.md|Filter Tools Spec]]
- [[12_VISION_TOOLS_SPEC.md|Vision Tools Spec]]
- [[13_PATTERN_RECOGNITION_SPEC.md|Pattern Recognition Spec]]
- [[14_PROFESSOR_DELIVERABLE_MATRIX.md|Professor Deliverable Matrix]]
- [[15_ACADEMIC_DEMO_SCENES.md|Academic Demo Scenes]]
- [[16_WORLD_DESIGN.md|World Design]]
- [[17_BOSS_SPEC.md|Boss Specification]]
- [[18_ENEMY_ROSTER.md|Enemy Roster]]
- [[19_NARRATIVE_AND_LORE.md|Narrative and Lore]]
- [[20_ASSET_BIBLE.md|Asset Bible]]
- [[21_COURSE_SCHEDULE.md|Course Schedule]]
- [[22_API_CONTRACTS.md|API Contracts]]
- [[23_DATA_SCHEMAS.md|Data Schemas]]
- [[24_TEST_PLAN.md|Test Plan]]
- [[25_IMPLEMENTATION_ROADMAP.md|Implementation Roadmap]]
- [[26_STUDENT_TEMPLATE_SPEC.md|Student Template Spec]]
- [[27_ACADEMIC_RUBRICS.md|Academic Rubrics]]
- [[28_DECISION_LOG.md|Decision Log]]
- [[28_SAMPLE_SYLLABUS.md|Sample Syllabus]]
- [[29_GIT_WORKFLOW_AND_STANDARDS.md|Git Workflow]]
- [[29_TA_GUIDE.md|TA Guide]]
- [[30_TICKET_BACKLOG.md|Ticket Backlog]]
- [[30_ASSIGNMENT_01_STAGE_DESIGN.md|Assignment 1: Stage Design]]
- [[31_RISK_REGISTER.md|Risk Register]]
- [[31_ASSIGNMENT_02_BOSS_DESIGN.md|Assignment 2: Boss Design]]
- [[32_ENVIRONMENT_SETUP_GUIDE.md|Environment Setup Guide]]
- [[32_ASSIGNMENT_03_LAB_EXERCISES.md|Assignment 3: Lab Exercises]]
- [[33_SCOPE_ADJUSTMENT.md|Scope Adjustment]]
- [[33_ASSIGNMENT_04_FINAL_PROJECT.md|Assignment 4: Final Project]]
- [[34_CLASS_MATERIALS.md|Class Materials]]
- [[34_EDUCATIONAL_ROADMAP.md|Educational Roadmap]]
- [[35_USER_MANUAL.md|User Manual]]
- [[36_STUDENT_MANUAL.md|Student Manual]]
- [[37_DEMO_QUICK_GUIDE.md|Demo Quick Guide]]
- [[38_STAGE_BOSS_GUIDE.md|Stage Boss Guide]]
- [[39_REPORTE_ANALISIS_CODIGO.md|Code Analysis Report]]
- [[40_DIALOGUE_SYSTEM.md|Dialogue System]]
- [[41_BESTIARY_CODEX.md|Bestiary Codex]]
- [[42_CUTSCENE_SYSTEM.md|Cutscene System]]
- [[43_SPEEDRUN_MODE.md|Speedrun Mode]]
- [[44_BOSS_RUSH_MODE.md|Boss Rush Mode]]
- [[45_SWIMMING_SPEC.md|Swimming Spec]]
- [[46_FOG_OF_WAR.md|Fog of War]]
- [[47_WATER_EFFECT.md|Water Effect]]
- [[48_SCREEN_TRANSITIONS.md|Screen Transitions]]
- [[49_AMBIENT_AUDIO.md|Ambient Audio]]
- [[50_IMPROVEMENT_ROADMAP.md|Improvement Roadmap]]
- [[51_IMPLEMENTATION_AUDIT.md|Implementation Audit]]
- [[64_GAME_DESIGN_DOCUMENT.md|Game Design Document]]
- [[BOSS_CREATION.md|Boss Creation Guide]]
- [[ENEMY_CREATION.md|Enemy Creation Guide]]
- [[SCENE_CREATION.md|Scene Creation Guide]]
- [[STAGE_CREATION.md|Stage Creation Guide]]

---
--- Traducción al Español ---

*This document is also available in English above.*

# Legacy of InFest — Índice Maestro de Documentación

**ID del Documento:** LOI-INDEX-000
**Versión:** 1.0.0
**Estado:** Oficial — Punto de Entrada Único
**Audiencia:** Profesor, Asistentes de Enseñanza, Estudiantes, asistentes de codificación IA (Claude Code, Cline, OpenCode, Codex)

---

## 1. Propósito

El conjunto completo de documentación de Legacy of InFest abarca **65 documentos** (00–52, 28b–34d, guías de creación) emitidos en **7 paquetes** (v1 a v7, más v10 documentos en el repositorio) en diferentes puntos del desarrollo del proyecto. Cada paquete incluía su propio README local, pero ninguno indexa el conjunto *completo*, y 6 documentos fueron reemplazados por versiones corregidas emitidas en el paquete v4 (realineación). Este documento es el **índice único, autoritativo y unificado** — lea esto primero, independientemente de qué archivo ZIP de paquete tenga abierto.

**Si usted es un asistente de codificación IA a punto de comenzar a trabajar, lea este documento, luego vaya directamente a 25_IMPLEMENTATION_ROADMAP.md.**

---

## 2. La Lista Autoritativa de Documentos (Use Esta, No el README Local de Ningún Paquete)

Los documentos marcados como **[SUPERSEDED]** en la tabla siguiente existen en su paquete original (v1, v2 o v3) pero han sido reemplazados por una versión corregida emitida en el paquete de realineación v4. **Use siempre la versión v4 de estos seis documentos.** Todos los demás documentos se usan desde su paquete de emisión original — solo existe una copia válida.

| # | Documento | Paquete Fuente Autoritativo | Estado |
|---|---|---|---|
| 00 | [[00_SYLLABUS_ALIGNMENT_AUDIT.md]] | v4 (legacy_of_infest_docs_corrected/) | Actual |
| 01 | 01_PROJECT_CHARTER.md | v4 (legacy_of_infest_docs_corrected/) | Actual — reemplaza original v1 |
| 02 | 02_CODEX_CONTEXT.md | v1 (legacy_of_infest_docs/) | Actual — sin cambios desde v1 |
| 03 | 03_ARCHITECTURE.md | v11 (en-repo, 2026-07-11) | Actual — corregido: resolución 800x600, contexto y ciclo de vida BaseScene |
| 04 | 04_PLAYER_SPEC.md | v11 (en-repo, 2026-07-11) | Actual — corregido: 25 estados, ULTIMATE a CHARGE_ATTACK |
| 05 | 05_ENEMY_SPEC.md | v11 (en-repo, 2026-07-11) | Actual — verificado: 8 tipos de enemigos documentados |
| 06 | 06_TMX_SPEC.md | v1 (legacy_of_infest_docs/) | Actual — sin cambios desde v1 |
| 07 | 07_STAGE0_DESIGN.md | v1 (legacy_of_infest_docs/) | Actual — sin cambios desde v1 |
| 08 | 08_SYLLABUS_MAPPING.md | v4 (legacy_of_infest_docs_corrected/) | Actual — reemplaza original v1 |
| 09 | 09_HUD_SPEC.md | v1 (legacy_of_infest_docs/) | Actual — sin cambios desde v1 |
| 10 | 10_LIBRARIES_AND_DEPENDENCIES.md | v1 (legacy_of_infest_docs/) | Actual — sin cambios desde v1 |
| 11 | 11_FILTER_TOOLS_SPEC.md | v2 (legacy_of_infest_docs_v2/) | Actual — sin cambios desde v2 |
| 12 | 12_VISION_TOOLS_SPEC.md | v2 (legacy_of_infest_docs_v2/) | Actual — sin cambios desde v2 |
| 13 | 13_PATTERN_RECOGNITION_SPEC.md | v2 (legacy_of_infest_docs_v2/) | Actual — sin cambios desde v2 |
| 14 | 14_PROFESSOR_DELIVERABLE_MATRIX.md | v4 (legacy_of_infest_docs_corrected/) | Actual — reemplaza original v2 |
| 15 | 15_ACADEMIC_DEMO_SCENES.md | v2 (legacy_of_infest_docs_v2/) | Actualizado — v1.1 añade 4 escenas de laboratorio teórico (Unidades II, III, V, VI) |
| 16 | 16_WORLD_DESIGN.md | v4 (legacy_of_infest_docs_corrected/) | Actual — reemplaza original v3 (solo terminología) |
| 17 | 17_BOSS_SPEC.md | v4 (legacy_of_infest_docs_corrected/) | Actual — reemplaza original v3 |
| 18 | 18_ENEMY_ROSTER.md | v3 (legacy_of_infest_docs_v3/) | Actual — sin cambios desde v3 |
| 19 | 19_NARRATIVE_AND_LORE.md | v4 (legacy_of_infest_docs_corrected/) | Actual — reemplaza original v3 |
| 20 | 20_ASSET_BIBLE.md | v3 (legacy_of_infest_docs_v3/) | Actual — sin cambios desde v3 |
| 21 | 21_COURSE_SCHEDULE.md | v4 (legacy_of_infest_docs_corrected/) | Actual — nuevo en v4 |
| 22 | 22_API_CONTRACTS.md | v11 (en-repo, 2026-07-11) | Actual — corregido: 800x600, SlideTransition, volumen play_sfx |
| 23 | 23_DATA_SCHEMAS.md | v5 (legacy_of_infest_docs_v5/) | Actual |
| 24 | 24_TEST_PLAN.md | v5 (legacy_of_infest_docs_v5/) | Actual |
| 25 | 25_IMPLEMENTATION_ROADMAP.md | v5 (legacy_of_infest_docs_v5/) | Actual |
| 26 | 26_STUDENT_TEMPLATE_SPEC.md | v5 (legacy_of_infest_docs_v5/) | Actual |
| 27 | 27_ACADEMIC_RUBRICS.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 28 | 28_DECISION_LOG.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 28b | 28_SAMPLE_SYLLABUS.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 29 | 29_GIT_WORKFLOW_AND_STANDARDS.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 29b | 29_TA_GUIDE.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 30 | 30_TICKET_BACKLOG.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 30b | 30_ASSIGNMENT_01_STAGE_DESIGN.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 31 | 31_RISK_REGISTER.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 31b | 31_ASSIGNMENT_02_BOSS_DESIGN.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 32 | 32_ENVIRONMENT_SETUP_GUIDE.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 32b | 32_ASSIGNMENT_03_LAB_EXERCISES.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 33 | 33_SCOPE_ADJUSTMENT.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 33b | 33_ASSIGNMENT_04_FINAL_PROJECT.md | v6 (legacy_of_infest_docs_v6/) | Actual |
| 34 | 34_CLASS_MATERIALS.md | v11 (en-repo, 2026-07-11) | Actual — corregido: indicadores de estado de archivo reales |
| 34b | 34_EDUCATIONAL_ROADMAP.md | v11 (en-repo, 2026-07-11) | Actual — hoja de ruta educativa |
| 34c | 34_LIVE_CODE_u02_vector_class.py | v11 (en-repo) | Actual — codificación en vivo: clase vector (Unidad II) |
| 34d | 34_LIVE_CODE_u07_convolution.py | v11 (en-repo) | Actual — codificación en vivo: convolución (Unidad VII) |
| 35 | 35_USER_MANUAL.md | v7 (en-repo) | Actual — nuevo |
| 36 | 36_STUDENT_MANUAL.md | v7 (en-repo) | Actual — nuevo |
| 37 | 37_DEMO_QUICK_GUIDE.md | v7 (en-repo) | Actual — nuevo |
| 38 | 38_STAGE_BOSS_GUIDE.md | v7 (en-repo) | Actual — nuevo |
| 39 | 39_REPORTE_ANALISIS_CODIGO.md | v10 (en-repo) | Actual — informe de análisis de código |
| 40 | 40_DIALOGUE_SYSTEM.md | v10 (en-repo) | Actual — diálogo ramificado con retratos |
| 41 | 41_BESTIARY_CODEX.md | v10 (en-repo) | Actual — sistema de seguimiento de enemigos |
| 42 | 42_CUTSCENE_SYSTEM.md | v10 (en-repo) | Actual — sistema de escenas cinemáticas con guion |
| 43 | 43_SPEEDRUN_MODE.md | v10 (en-repo) | Actual — cronómetro de velocidad + datos fantasma |
| 44 | 44_BOSS_RUSH_MODE.md | v10 (en-repo) | Actual — modo de desafío de jefes |
| 45 | 45_SWIMMING_SPEC.md | v10 (en-repo) | Actual — mecánicas de natación |
| 46 | 46_FOG_OF_WAR.md | v10 (en-repo) | Actual — niebla de guerra |
| 47 | 47_WATER_EFFECT.md | v10 (en-repo) | Actual — efectos visuales de agua |
| 48 | 48_SCREEN_TRANSITIONS.md | v10 (en-repo) | Actual — fundido/barrido/deslizamiento/círculo |
| 49 | 49_AMBIENT_AUDIO.md | v10 (en-repo) | Actual — sistema de audio ambiental |
| 50 | [[50_IMPROVEMENT_ROADMAP.md]] | v11 (en-repo, 2026-07-11) | Actual — corregido: elementos P0 resueltos, métricas precisas |
| 51 | [[51_IMPLEMENTATION_AUDIT.md]] | v10 (en-repo) | Actual — análisis de brechas basado en evidencia (corregido 2026-07-11) |
| 52 | [[52_MULTIDISCIPLINARY_AUDIT.md]] | v12 (en-repo, 2026-07-14) | Actual — auditoría multidisciplinaria con puntuaciones de 44 categorías |
| — | BOSS_CREATION.md | v10 (en-repo) | Actual — guía de creación de jefes |
| — | ENEMY_CREATION.md | v10 (en-repo) | Actual — guía de creación de enemigos |
| — | SCENE_CREATION.md | v10 (en-repo) | Actual — guía de creación de escenas |
| — | STAGE_CREATION.md | v10 (en-repo) | Actual — guía de creación de niveles |

**Acción recomendada antes de comenzar la implementación:** Consolidar todos los documentos de estado actual en una sola carpeta docs/ en el repositorio real (según la estructura de 00_SYLLABUS_ALIGNMENT_AUDIT.md sección 7), descartando los originales reemplazados v1/v2/v3 de los seis documentos listados como "reemplaza" arriba. Este índice se vuelve redundante una vez que ocurre esa consolidación — en ese punto, una simple lista numerada de la carpeta docs/ se explica por sí misma.

---

## 3. Mapa de Cobertura de Documentación — Las Cuatro Capas

Este conjunto de documentación cubre cuatro capas distintas. Cada documento está clasificado a continuación para que pueda encontrar lo que necesita por el *tipo* de pregunta que hace, no solo por el número.

### 3.1 Capa Académica — "¿Qué es este curso y cómo se califica?"

| Documento | Responde |
|---|---|
| 00_SYLLABUS_ALIGNMENT_AUDIT.md | ¿Qué dice realmente el programa de estudios oficial, y dónde se desviaron los borradores anteriores? |
| 08_SYLLABUS_MAPPING.md | ¿Qué componente del marco se asigna a qué unidad del programa? |
| 14_PROFESSOR_DELIVERABLE_MATRIX.md | Trazabilidad completa de programa a marco a evaluación |
| 21_COURSE_SCHEDULE.md | ¿Qué sucede en cada una de las 11 clases + Invenio Fest? |
| 27_ACADEMIC_RUBRICS.md | ¿Cuántos puntos por qué, en cada instrumento calificado? |
| 31_RISK_REGISTER.md | ¿Qué riesgos académicos/pedagógicos existen y cómo se mitigan? |

### 3.2 Capa de Análisis y Diseño — "¿Qué estamos construyendo y por qué?"

| Documento | Responde |
|---|---|
| 01_PROJECT_CHARTER.md | Alcance, visión, partes interesadas, estructura del repositorio de un vistazo |
| 02_CODEX_CONTEXT.md | Filosofía del proyecto, reglas de codificación, reglas de arquitectura |
| 16_WORLD_DESIGN.md | Las 4 zonas, 14 niveles, mapeo narrativa a jugabilidad |
| 17_BOSS_SPEC.md | Los 4 diseños de jefes, fase por fase |
| 18_ENEMY_ROSTER.md | Cada enemigo estándar, por zona |
| 19_NARRATIVE_AND_LORE.md | Historia, personajes, fundamento cultural |
| 20_ASSET_BIBLE.md | Cada recurso visual/audio, ruta, dimensiones, paleta |
| 28_DECISION_LOG.md | Por qué se tomó cada decisión técnica/de diseño importante (ADR) |

### 3.3 Capa de Implementación/Arquitectura — "¿Cómo está estructurado el sistema?"

| Documento | Responde |
|---|---|
| 03_ARCHITECTURE.md | Estructura completa de carpetas, responsabilidades de módulos, flujo de datos |
| 04_PLAYER_SPEC.md | Física del jugador, estados (19 estados incl. SWIMMING), combate — especificación de comportamiento completa |
| 05_ENEMY_SPEC.md | Clase base de enemigos y 8 tipos de enemigos (Walker, Flying, Shooter, Charger, Archer, Brute, Caster, Assassin) |
| 06_TMX_SPEC.md | Formato de archivo de mapa, capas, tipos de objetos |
| 07_STAGE0_DESIGN.md | El nivel de implementación de referencia del profesor, zona por zona |
| 09_HUD_SPEC.md | Diseño del HUD, corazones, temporizador, mensajes, Game Over |
| 10_LIBRARIES_AND_DEPENDENCIES.md | Cada biblioteca de terceros, propósito, reglas de integración |
| 11_FILTER_TOOLS_SPEC.md | Subsistema de procesamiento de imágenes de la Unidad VII |
| 12_VISION_TOOLS_SPEC.md | Subsistema de segmentación de la Unidad VIII |
| 13_PATTERN_RECOGNITION_SPEC.md | Subsistema de aprendizaje automático de la Unidad IX |
| 15_ACADEMIC_DEMO_SCENES.md | 10 escenas interactivas de demostración/laboratorio + 3 nuevas escenas de UI (inventario, logros, mapa mundial) |

### 3.4 Capa de Código/Construcción — "¿Qué escribo realmente, en qué orden, y cómo sé que es correcto?"

| Documento | Responde |
|---|---|
| 22_API_CONTRACTS.md | Firmas exactas de funciones/clases — la autoridad de sintaxis |
| 23_DATA_SCHEMAS.md | Formas de datos exactas que cruzan los límites de los módulos |
| 24_TEST_PLAN.md | Casos de prueba exactos por módulo |
| 25_IMPLEMENTATION_ROADMAP.md | El orden de construcción de 16 fases con Definición de Terminado |
| 26_STUDENT_TEMPLATE_SPEC.md | Los archivos iniciales exactos que cada estudiante copia |
| 29_GIT_WORKFLOW_AND_STANDARDS.md | Ramificación, commits, PRs, revisión de código |
| 30_TICKET_BACKLOG.md | Cada fase de la hoja de ruta descompuesta en tickets atómicos |
| 32_ENVIRONMENT_SETUP_GUIDE.md | Configuración paso a paso de la máquina, solución de problemas |

---

## 4. Rutas de Lectura por Rol

### 4.1 "Soy un asistente de codificación IA que comienza la implementación desde cero"

1. Este documento (00_MASTER_INDEX.md)
2. 00_SYLLABUS_ALIGNMENT_AUDIT.md   — entender qué es autoritativo
3. 02_CODEX_CONTEXT.md              — entender las reglas
4. 25_IMPLEMENTATION_ROADMAP.md     — entender el orden de construcción
5. 30_TICKET_BACKLOG.md             — tomar la Fase 0, Ticket T0.1
6. 22_API_CONTRACTS.md + 23_DATA_SCHEMAS.md  — mantener abiertos como referencia de sintaxis/formas mientras codifica
7. 24_TEST_PLAN.md                  — escribir pruebas para la fase en la que esté
8. 28_DECISION_LOG.md               — consultar antes de proponer cualquier cambio arquitectónico

### 4.2 "Soy el profesor preparándome para la Clase 1"

1. 21_COURSE_SCHEDULE.md            — confirmar el calendario
2. 32_ENVIRONMENT_SETUP_GUIDE.md    — verificar que funcione en su propia máquina primero
3. 25_IMPLEMENTATION_ROADMAP.md Fases 0-9 — confirmar que estén completas antes de la Clase 1
4. 26_STUDENT_TEMPLATE_SPEC.md      — confirmar que las plantillas existan y la prueba de 15 minutos pase
5. 27_ACADEMIC_RUBRICS.md           — tenerlas listas para calificar desde la Clase 5 en adelante
6. 31_RISK_REGISTER.md seccion 8    — revisar riesgos abiertos antes del inicio del semestre

### 4.3 "Soy un estudiante comenzando mi asignación"

1. 32_ENVIRONMENT_SETUP_GUIDE.md    — preparar su máquina
2. 26_STUDENT_TEMPLATE_SPEC.md seccion 8   — copiar su plantilla, incorporación de 15 minutos
3. 16_WORLD_DESIGN.md               — encontrar su zona/nivel asignado (o 17_BOSS_SPEC.md si se le asignó un jefe)
4. 18_ENEMY_ROSTER.md               — encontrar los enemigos de su zona (asignaciones de nivel)
5. 08_SYLLABUS_MAPPING.md           — entender qué requiere cada hito
6. 36_STUDENT_MANUAL.md             — manual completo del estudiante con todas las referencias
7. 15_ACADEMIC_DEMO_SCENES.md       — explorar los 10 laboratorios teóricos interactivos (Unidades II a IX)
8. 37_DEMO_QUICK_GUIDE.md           — referencia rápida para usar las 10 demostraciones
9. 38_STAGE_BOSS_GUIDE.md           — referencia rápida para construir su nivel/jefe
10. 27_ACADEMIC_RUBRICS.md secciones 2-4     — entender exactamente cómo será calificado
11. 29_GIT_WORKFLOW_AND_STANDARDS.md — entender el proceso de rama/commit/PR

### 4.4 "Estoy revisando una entrega de estudiante"

1. 27_ACADEMIC_RUBRICS.md           — los criterios de calificación para este hito
2. 29_GIT_WORKFLOW_AND_STANDARDS.md seccion 5 — la lista de verificación de revisión de código
3. 08_SYLLABUS_MAPPING.md           — verificar que las unidades reclamadas estén realmente demostradas
4. 23_DATA_SCHEMAS.md seccion 7     — verificar que el front-matter del README sea válido

---

## 5. Reglas de Precedencia (Consolidadas)

Cuando dos documentos parezcan estar en desacuerdo, resuelva usando esta tabla:

| Cuando Esto... | ...Entre en Conflicto Con Esto... | Este Gana | Razón |
|---|---|---|---|
| 00_SYLLABUS_ALIGNMENT_AUDIT.md | Cualquier documento emitido antes que él | Gana la Auditoría | Es la reconciliación autoritativa contra el programa de estudios real |
| 22_API_CONTRACTS.md | Cualquier especificación narrativa (04, 05, 06, 09, 11, 12, 13, 17) | Ganan los Contratos | ...para sintaxis solamente |
| Especificación narrativa (04, 05, 06, 09, 11, 12, 13, 17) | 22_API_CONTRACTS.md | Gana la especificación narrativa | ...para comportamiento solamente |
| 23_DATA_SCHEMAS.md | La descripción en prosa de cualquier documento de una estructura de datos | Ganan los Esquemas | Nombres/tipos de campo exactos |
| 25_IMPLEMENTATION_ROADMAP.md | La intuición del desarrollador/IA sobre el orden de construcción | Gana la Hoja de Ruta | Las dependencias de secuenciación no son obvias por diseño |
| 28_DECISION_LOG.md | Una nueva propuesta para cambiar una decisión arquitectónica ya tomada | Gana el Registro de Decisiones, a menos que se añada un nuevo ADR | Previene la re-litigación de decisiones ya resueltas |
| 27_ACADEMIC_RUBRICS.md | Cualquier intuición de calificación informal | Gana la Rúbrica | Asegura consistencia y defendibilidad de la calificación |

---

## 6. Resumen de Conteo de Documentos

| Paquete | Documentos | Nuevos en Este Paquete | Reemplazados por Paquete Posterior |
|---|---|---|---|
| v1 (legacy_of_infest_docs/) | 01 a 10 | 10 | 01, 03, 08 (por v4) |
| v2 (legacy_of_infest_docs_v2/) | 11 a 15 | 5 | 14 (por v4) |
| v3 (legacy_of_infest_docs_v3/) | 16 a 20 | 5 | 16, 17, 19 (por v4) |
| v4 (legacy_of_infest_docs_corrected/) | 00, 01, 03, 08, 14, 16, 17, 19, 21 | 2 nuevos (00, 21) + 7 corregidos | - |
| v5 (legacy_of_infest_docs_v5/) | 22 a 26 | 5 | - |
| v6 (legacy_of_infest_docs_v6/) | 27 a 33, 28b a 33b | 11 | - |
| Total unicos actuales | 65 (00 a 52, 28b a 34d, guias de creacion) | | |
| v7 (actualizaciones en-repo) | 15, 03, 28, 21, 08, 22, 30 | 7 actualizados | - |
| v8 a v10 (sesiones) | 10 escenas de laboratorio, registro, paneles, disenos, depuracion, scripts, docs 35 a 51, guias de creacion | 20 nuevos + todos re-auditados | - |
| v11 (alineacion 2026-07-11) | 03, 04, 05, 22, 34, 50, 00 | 7 corregidos |
| v12 (2026-07-14) | 52_MULTIDISCIPLINARY_AUDIT.md | 1 nuevo | - |

---

## 7. Que Viene Despues del Documento 32

En este punto, el conjunto de documentacion cubre las cuatro capas — Academica, Analisis/Diseno, Implementacion/Arquitectura, y Codigo/Construccion — lo suficientemente completo para comenzar la Fase 0 de 25_IMPLEMENTATION_ROADMAP.md sin que queden decisiones indefinidas que bloqueen a un asistente de codificacion.

Cualquier documento adicional debe ser **generado solo en respuesta a una brecha concreta descubierta durante la implementacion real** (registrada primero en KNOWN_GAPS.md segun 23_DATA_SCHEMAS.md seccion 8, y en 31_RISK_REGISTER.md si representa un riesgo continuo en lugar de una brecha puntual) — no especulativamente.

Los dos elementos previamente rastreados como abiertos/diferidos han sido resueltos por confirmacion del profesor:

1. **El rol de Matplotlib** — confirmado como uso exclusivo en aula/laboratorio instruccional (segun los Quices/Labs de 21_COURSE_SCHEDULE.md), no un punto de integracion del marco Legacy of InFest. No se requiere ningun sitio de llamada en src/. (RISK-A03 de 31_RISK_REGISTER.md, cerrado.)
2. **El Gavilan Camionero Mascarero** — confirmado como el jefe oficial y permanente de la Zona 3, ya no pendiente ni sujeto a reasignacion. (RISK-A04 de 31_RISK_REGISTER.md, cerrado; ADR-008 de 28_DECISION_LOG.md, aceptado final.)

Con ambos elementos cerrados, el conjunto de documentacion **no tiene decisiones de diseno abiertas restantes** que bloqueen la implementacion.

---
## Documentos Relacionados

- [[00_SYLLABUS_ALIGNMENT_AUDIT.md|Auditoria de Alineacion del Programa]]
- [[01_PROJECT_CHARTER.md|Acta del Proyecto]]
- [[02_CODEX_CONTEXT.md|Contexto del Codice]]
- [[03_ARCHITECTURE.md|Arquitectura]]
- [[04_PLAYER_SPEC.md|Especificacion del Jugador]]
- [[05_ENEMY_SPEC.md|Especificacion de Enemigos]]
- [[06_TMX_SPEC.md|Especificacion TMX]]
- [[07_STAGE0_DESIGN.md|Diseno del Nivel 0]]
- [[08_SYLLABUS_MAPPING.md|Mapeo del Programa]]
- [[09_HUD_SPEC.md|Especificacion del HUD]]
- [[10_LIBRARIES_AND_DEPENDENCIES.md|Bibliotecas y Dependencias]]
- [[11_FILTER_TOOLS_SPEC.md|Especificacion de Herramientas de Filtro]]
- [[12_VISION_TOOLS_SPEC.md|Especificacion de Herramientas de Vision]]
- [[13_PATTERN_RECOGNITION_SPEC.md|Especificacion de Reconocimiento de Patrones]]
- [[14_PROFESSOR_DELIVERABLE_MATRIX.md|Matriz de Entregables del Profesor]]
- [[15_ACADEMIC_DEMO_SCENES.md|Escenas de Demostracion Academica]]
- [[16_WORLD_DESIGN.md|Diseno del Mundo]]
- [[17_BOSS_SPEC.md|Especificacion de Jefes]]
- [[18_ENEMY_ROSTER.md|Lista de Enemigos]]
- [[19_NARRATIVE_AND_LORE.md|Narrativa y Lore]]
- [[20_ASSET_BIBLE.md|Biblia de Recursos]]
- [[21_COURSE_SCHEDULE.md|Calendario del Curso]]
- [[22_API_CONTRACTS.md|Contratos de API]]
- [[23_DATA_SCHEMAS.md|Esquemas de Datos]]
- [[24_TEST_PLAN.md|Plan de Pruebas]]
- [[25_IMPLEMENTATION_ROADMAP.md|Hoja de Ruta de Implementacion]]
- [[26_STUDENT_TEMPLATE_SPEC.md|Especificacion de Plantilla del Estudiante]]
- [[27_ACADEMIC_RUBRICS.md|Rubricas Academicas]]
- [[28_DECISION_LOG.md|Registro de Decisiones]]
- [[28_SAMPLE_SYLLABUS.md|Programa de Estudios de Muestra]]
- [[29_GIT_WORKFLOW_AND_STANDARDS.md|Flujo de Trabajo Git]]
- [[29_TA_GUIDE.md|Guia del Asistente de Ensenanza]]
- [[30_TICKET_BACKLOG.md|Backlog de Tickets]]
- [[30_ASSIGNMENT_01_STAGE_DESIGN.md|Asignacion 1: Diseno de Nivel]]
- [[31_RISK_REGISTER.md|Registro de Riesgos]]
- [[31_ASSIGNMENT_02_BOSS_DESIGN.md|Asignacion 2: Diseno de Jefe]]
- [[32_ENVIRONMENT_SETUP_GUIDE.md|Guia de Configuracion del Entorno]]
- [[32_ASSIGNMENT_03_LAB_EXERCISES.md|Asignacion 3: Ejercicios de Laboratorio]]
- [[33_SCOPE_ADJUSTMENT.md|Ajuste de Alcance]]
- [[33_ASSIGNMENT_04_FINAL_PROJECT.md|Asignacion 4: Proyecto Final]]
- [[34_CLASS_MATERIALS.md|Materiales de Clase]]
- [[34_EDUCATIONAL_ROADMAP.md|Hoja de Ruta Educativa]]
- [[35_USER_MANUAL.md|Manual de Usuario]]
- [[36_STUDENT_MANUAL.md|Manual del Estudiante]]
- [[37_DEMO_QUICK_GUIDE.md|Guia Rapida de Demostracion]]
- [[38_STAGE_BOSS_GUIDE.md|Guia de Nivel y Jefe]]
- [[39_REPORTE_ANALISIS_CODIGO.md|Informe de Analisis de Codigo]]
- [[40_DIALOGUE_SYSTEM.md|Sistema de Dialogo]]
- [[41_BESTIARY_CODEX.md|Codice de Bestiario]]
- [[42_CUTSCENE_SYSTEM.md|Sistema de Escenas Cinematicas]]
- [[43_SPEEDRUN_MODE.md|Modo Speedrun]]
- [[44_BOSS_RUSH_MODE.md|Modo Boss Rush]]
- [[45_SWIMMING_SPEC.md|Especificacion de Natacion]]
- [[46_FOG_OF_WAR.md|Niebla de Guerra]]
- [[47_WATER_EFFECT.md|Efecto de Agua]]
- [[48_SCREEN_TRANSITIONS.md|Transiciones de Pantalla]]
- [[49_AMBIENT_AUDIO.md|Audio Ambiental]]
- [[50_IMPROVEMENT_ROADMAP.md|Hoja de Ruta de Mejoras]]
- [[51_IMPLEMENTATION_AUDIT.md|Auditoria de Implementacion]]
- [[BOSS_CREATION.md|Guia de Creacion de Jefes]]
- [[ENEMY_CREATION.md|Guia de Creacion de Enemigos]]
- [[SCENE_CREATION.md|Guia de Creacion de Escenas]]
- [[STAGE_CREATION.md|Guia de Creacion de Niveles]]