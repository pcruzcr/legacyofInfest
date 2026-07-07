# Legacy of InFest — Master Documentation Index

**Document ID:** LOI-INDEX-000  
**Version:** 1.0.0  
**Status:** Official — Single Entry Point  
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Purpose

The complete Legacy of InFest documentation set spans **33 documents** issued across **6 packages** (v1 through v6) at different points in the project's development. Each package shipped with its own local README, but none of them indexes the *entire* set, and 6 documents were superseded by corrected versions issued in the v4 (realignment) package. This document is the **single, authoritative, unified index** — read this first, regardless of which package's ZIP file you happen to have open.

**If you are an AI coding assistant about to start work, read this document, then go directly to `25_IMPLEMENTATION_ROADMAP.md`.**

---

## 2. The Authoritative Document List (Use This, Not Any Package's Local README)

Documents marked **[SUPERSEDED]** below exist in their originating package (v1, v2, or v3) but have been replaced by a corrected version issued in the v4 realignment package. **Always use the v4 version of these six documents.** All other documents are used from their original issuing package — there is only one valid copy.

| # | Document | Authoritative Source Package | Status |
|---|---|---|---|
| 00 | `00_SYLLABUS_ALIGNMENT_AUDIT.md` | v4 (`legacy_of_infest_docs_corrected/`) | Current |
| 01 | `01_PROJECT_CHARTER.md` | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v1 original |
| 02 | `02_CODEX_CONTEXT.md` | v1 (`legacy_of_infest_docs/`) | Current — unchanged since v1 |
| 03 | `03_ARCHITECTURE.md` | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v1 original |
| 04 | `04_PLAYER_SPEC.md` | v1 (`legacy_of_infest_docs/`) | Current — unchanged since v1 |
| 05 | `05_ENEMY_SPEC.md` | v1 (`legacy_of_infest_docs/`) | Current — unchanged since v1 |
| 06 | `06_TMX_SPEC.md` | v1 (`legacy_of_infest_docs/`) | Current — unchanged since v1 |
| 07 | `07_STAGE0_DESIGN.md` | v1 (`legacy_of_infest_docs/`) | Current — unchanged since v1 |
| 08 | `08_SYLLABUS_MAPPING.md` | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v1 original |
| 09 | `09_HUD_SPEC.md` | v1 (`legacy_of_infest_docs/`) | Current — unchanged since v1 |
| 10 | `10_LIBRARIES_AND_DEPENDENCIES.md` | v1 (`legacy_of_infest_docs/`) | Current — unchanged since v1 |
| 11 | `11_FILTER_TOOLS_SPEC.md` | v2 (`legacy_of_infest_docs_v2/`) | Current — unchanged since v2 |
| 12 | `12_VISION_TOOLS_SPEC.md` | v2 (`legacy_of_infest_docs_v2/`) | Current — unchanged since v2 |
| 13 | `13_PATTERN_RECOGNITION_SPEC.md` | v2 (`legacy_of_infest_docs_v2/`) | Current — unchanged since v2 |
| 14 | `14_PROFESSOR_DELIVERABLE_MATRIX.md` | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v2 original |
| 15 | `15_ACADEMIC_DEMO_SCENES.md` | v2 (`legacy_of_infest_docs_v2/`) | Updated — v1.1 adds 4 theory lab scenes (Units II, III, V, VI) |
| 16 | `16_WORLD_DESIGN.md` | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v3 original (terminology only) |
| 17 | `17_BOSS_SPEC.md` | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v3 original |
| 18 | `18_ENEMY_ROSTER.md` | v3 (`legacy_of_infest_docs_v3/`) | Current — unchanged since v3 |
| 19 | `19_NARRATIVE_AND_LORE.md` | v4 (`legacy_of_infest_docs_corrected/`) | Current — supersedes v3 original |
| 20 | `20_ASSET_BIBLE.md` | v3 (`legacy_of_infest_docs_v3/`) | Current — unchanged since v3 |
| 21 | `21_COURSE_SCHEDULE.md` | v4 (`legacy_of_infest_docs_corrected/`) | Current — new in v4 |
| 22 | `22_API_CONTRACTS.md` | v5 (`legacy_of_infest_docs_v5/`) | Current |
| 23 | `23_DATA_SCHEMAS.md` | v5 (`legacy_of_infest_docs_v5/`) | Current |
| 24 | `24_TEST_PLAN.md` | v5 (`legacy_of_infest_docs_v5/`) | Current |
| 25 | `25_IMPLEMENTATION_ROADMAP.md` | v5 (`legacy_of_infest_docs_v5/`) | Current |
| 26 | `26_STUDENT_TEMPLATE_SPEC.md` | v5 (`legacy_of_infest_docs_v5/`) | Current |
| 27 | `27_ACADEMIC_RUBRICS.md` | v6 (`legacy_of_infest_docs_v6/`) | Current |
| 28 | `28_DECISION_LOG.md` | v6 (`legacy_of_infest_docs_v6/`) | Current |
| 29 | `29_GIT_WORKFLOW_AND_STANDARDS.md` | v6 (`legacy_of_infest_docs_v6/`) | Current |
| 30 | `30_TICKET_BACKLOG.md` | v6 (`legacy_of_infest_docs_v6/`) | Current |
| 31 | `31_RISK_REGISTER.md` | v6 (`legacy_of_infest_docs_v6/`) | Current |
| 32 | `32_ENVIRONMENT_SETUP_GUIDE.md` | v6 (`legacy_of_infest_docs_v6/`) | Current |

**Recommended action before implementation begins:** Consolidate all 33 current-status documents into a single flat `docs/` folder in the actual repository (per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §7's structure), discarding the superseded v1/v2/v3 originals of the six documents listed as "supersedes" above. This index becomes redundant once that consolidation happens — at that point, a simple numbered `docs/` folder listing is self-explanatory.

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
| `04_PLAYER_SPEC.md` | Player physics, states, combat — complete behavioral spec |
| `05_ENEMY_SPEC.md` | Enemy base class and the 3 templates |
| `06_TMX_SPEC.md` | Map file format, layers, object types |
| `07_STAGE0_DESIGN.md` | The professor's reference-implementation stage, zone by zone |
| `09_HUD_SPEC.md` | HUD layout, hearts, timer, messages, Game Over |
| `10_LIBRARIES_AND_DEPENDENCIES.md` | Every third-party library, purpose, integration rules |
| `11_FILTER_TOOLS_SPEC.md` | Unit VII image processing subsystem |
| `12_VISION_TOOLS_SPEC.md` | Unit VIII segmentation subsystem |
| `13_PATTERN_RECOGNITION_SPEC.md` | Unit IX machine learning subsystem |
| `15_ACADEMIC_DEMO_SCENES.md` | 10 interactive demo/lab scenes (7 theory labs + 3 academic demos) |

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
6. 15_ACADEMIC_DEMO_SCENES.md        — explore the 10 interactive theory labs (Units II–IX)
7. 27_ACADEMIC_RUBRICS.md §2-4      — understand exactly how you'll be scored
8. 29_GIT_WORKFLOW_AND_STANDARDS.md — understand the branch/commit/PR process
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
| v6 (`legacy_of_infest_docs_v6/`) | 27–32 | 6 | — |
| **Total unique, current documents** | **34** (00–33) | | |
| v7 (in-repo updates) | 15, 25, 03, 28, 24, 21, 08, 22, 30 | 9 updated | — |
| v8 (current session) | 10 lab scenes, scene_registry, param_panel, demo_layout, demo_utils, debug_overlay, validate_assets.py, generate_exam.py | all docs re-audited | — |

---

## 7. What Comes After Document 32

At this point, the documentation set covers all four layers — Academic, Analysis/Design, Implementation/Architecture, and Code/Build — completely enough to begin Phase 0 of `25_IMPLEMENTATION_ROADMAP.md` with no remaining undefined decisions blocking a coding assistant.

Any further documents should be **generated only in response to a concrete gap discovered during actual implementation** (logged first in `KNOWN_GAPS.md` per `23_DATA_SCHEMAS.md` §8, and in `31_RISK_REGISTER.md` if it represents an ongoing risk rather than a one-time gap) — not speculatively.

The two items previously tracked as open/deferred have both been resolved by professor confirmation:

1. **Matplotlib's role** — confirmed as classroom/lab-instructional use only (per `21_COURSE_SCHEDULE.md`'s Quices/Labs), not a Legacy of InFest framework integration point. No `src/` call site is required. (`31_RISK_REGISTER.md` RISK-A03, closed.)
2. **El Gavilán Camionero Mascarero** — confirmed as the official, permanent Zone 3 boss, no longer pending or subject to reassignment. (`31_RISK_REGISTER.md` RISK-A04, closed; `28_DECISION_LOG.md` ADR-008, accepted final.)

With both items closed, the documentation set has **no remaining open design decisions** blocking implementation.
