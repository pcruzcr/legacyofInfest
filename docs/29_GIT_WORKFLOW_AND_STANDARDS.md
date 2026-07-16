---
document_id: "LOI-GIT-029"
title: "Legacy of InFest — Git Workflow and Development Standards"
aliases: ["Git Workflow", "Git Standards"]
tags: ["git", "workflow", "standards"]
description: "Branching, commits, PRs, code review"
source: "docs/29_GIT_WORKFLOW_AND_STANDARDS.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Git Workflow and Development Standards

**Document ID:** LOI-GITFLOW-029  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires `02_CODEX_CONTEXT.md`, `00_SYLLABUS_ALIGNMENT_AUDIT.md`, `25_IMPLEMENTATION_ROADMAP.md`  
**Audience:** Professor, Students, AI coding assistants

---

## 1. Scope and Relationship to Other Documents

`02_CODEX_CONTEXT.md` §5–6 already defines **code-level** standards: naming conventions, type hints, docstrings, error handling. This document does not repeat those — it covers everything `02_CODEX_CONTEXT.md` does not: **Git branching strategy, commit message format, pull request process, and code review checklist** for the private GitHub repository described in `00_SYLLABUS_ALIGNMENT_AUDIT.md` §7.

**Precedence:** For code style, `02_CODEX_CONTEXT.md` governs. For repository workflow (branches, commits, PRs, reviews), this document governs.

---

## 2. Branch Strategy

| Branch | Owner | Purpose |
|---|---|---|
| `main` | Professor | Stable, reviewed code only. Always runnable. |
| `develop` | Professor | Integration branch for professor's own framework work, merged to `main` at phase boundaries (see `25_IMPLEMENTATION_ROADMAP.md`) |
| `student/<assignment_id>` | Individual student | One branch per student, named after their assignment folder (e.g., `student/stage1_2_la_soda`, `student/boss_venado`) |

### 2.1 Rules

- Students **never** push directly to `main` or `develop`.
- Students work exclusively on their own `student/<assignment_id>` branch.
- A student's branch only ever touches files under `src/stages/<assignment_id>/` (and, if applicable, their own model/dataset files per `23_DATA_SCHEMAS.md` §6.2). Any change outside that path in a student PR is an automatic review rejection (see §5).
- The professor merges `student/<assignment_id>` branches into `main` after review, at or after each Evaluación Práctica checkpoint (Classes 5, 8, 11 per `21_COURSE_SCHEDULE.md`).
- AI coding assistants working on **framework/engine code** (Phases 1–14 of `25_IMPLEMENTATION_ROADMAP.md`) work on `develop` or short-lived `feature/<phase-name>` branches off `develop`, never directly on `main`.

### 2.2 Branch Naming Convention

```
student/<assignment_id>          # e.g., student/stage2_3_oficinas
feature/<phase-name>             # e.g., feature/phase10-filter-tools
fix/<short-description>          # e.g., fix/checkpoint-double-trigger
docs/<short-description>         # e.g., docs/api-contracts-update
```

---

## 3. Commit Message Format

Every commit message follows this exact pattern, already introduced in `01_PROJECT_CHARTER.md` §8.3 and restated here as the authoritative full specification:

```
[SCOPE] type: short description

<optional body, wrapped at 72 chars, explaining WHY not just WHAT>
```

### 3.1 SCOPE Tags

| Scope | Used For |
|---|---|
| `[ENGINE]` | Changes to `src/engine/` |
| `[FRAMEWORK]` | Changes to `src/framework/` |
| `[STAGE0]` | Changes to `src/stages/stage0/` |
| `[<ASSIGNMENT_ID>]` | Student work, e.g. `[STAGE1_2_LA_SODA]`, `[BOSS_VENADO]` |
| `[DOCS]` | Documentation-only changes |
| `[TESTS]` | Test-only changes |
| `[TOOLS]` | Changes to `tools/` scripts |

### 3.2 Type Tags (Conventional Commits subset)

| Type | Meaning |
|---|---|
| `feat` | New functionality |
| `fix` | Bug fix |
| `docs` | Documentation change |
| `test` | Adding or correcting tests |
| `refactor` | Code restructuring, no behavior change |
| `perf` | Performance improvement |
| `chore` | Tooling, dependency, or config change |

### 3.3 Examples

```
[FRAMEWORK] feat: implement FilterTools.gaussian_blur per 11_FILTER_TOOLS_SPEC.md §8.5

[STAGE1_2_LA_SODA] feat: add Bézier-path FlyingCucaracha patrol

[ENGINE] fix: correct coyote-time frame count off-by-one in Player

[TESTS] test: add test_filter_tools.py per 24_TEST_PLAN.md §12.1

[DOCS] docs: correct repository structure in 03_ARCHITECTURE.md per audit §2.A.6
```

### 3.4 Rules

- One logical change per commit. Do not bundle unrelated fixes into a single commit.
- Never commit directly with a message that omits the `[SCOPE]` tag.
- AI coding assistants generating commits on behalf of a session must follow this format exactly — it is parseable tooling input, not just a style preference (a future grading/audit script may grep commit history by scope and type).

---

## 4. Pull Request Process

### 4.1 PR Title Format

Matches the commit message scope convention: `[SCOPE] Short summary of the PR's purpose`

### 4.2 Required PR Template

Every PR (student or professor/AI-assistant-authored) must include this filled-out template in its description:

```markdown
## Scope
<Which assignment_id, engine phase, or framework module does this PR touch?>

## What Changed
<2-4 sentences>

## Academic Units Demonstrated (student PRs only)
<List the syllabus units this PR's content demonstrates, per 08_SYLLABUS_MAPPING.md>

## Testing Performed
<Which tests in 24_TEST_PLAN.md were run? Manual playthrough done? Results?>

## Checklist
- [ ] Code follows 02_CODEX_CONTEXT.md naming and structure rules
- [ ] No changes outside my assignment_id folder (student PRs) or designated phase scope (framework PRs)
- [ ] README updated with current front-matter (23_DATA_SCHEMAS.md §7) if applicable
- [ ] All relevant tests from 24_TEST_PLAN.md pass locally
- [ ] No TODO/NotImplementedError left unresolved without a KNOWN_GAPS.md entry (23_DATA_SCHEMAS.md §8)
```

### 4.3 Student PR Timing

Student PRs are opened against their own `student/<assignment_id>` branch continuously, but are **reviewed by the professor at the three Evaluación Práctica checkpoints** (Classes 5, 8, 11), not necessarily on every push. Students may request informal early feedback via a draft PR at any time.

---

## 5. Code Review Checklist

This expands `01_PROJECT_CHARTER.md` §8.5 into the full checklist a reviewer (professor or TA) applies to every PR before merging.

### 5.1 Scope and Boundary Checks

- [ ] Student PR touches **only** their assignment folder (`src/stages/<assignment_id>/` and, if applicable, their `models/`/`datasets/` subfolder)
- [ ] No modifications to `src/engine/`, `src/framework/`, `assets/`, or another student's folder
- [ ] No direct imports of `scipy`, `cv2`, `skimage`, `sklearn`, `joblib`, or `numpy` in student-authored files (per `02_CODEX_CONTEXT.md` §11.1 and `00_SYLLABUS_ALIGNMENT_AUDIT.md` §4 library table) — only via `FilterTools`/`VisionTools`/`PatternRecognitionTools`

### 5.2 Functional Correctness

- [ ] Code runs without exceptions (manual run or automated test, per `24_TEST_PLAN.md`)
- [ ] No bypass of the framework API (no direct `pygame.key.get_pressed()`, no direct `pygame.mixer.Sound.play()`, no direct `pygame.image.load()` — per `02_CODEX_CONTEXT.md` §6.1)
- [ ] If a Stage assignment: TMX loads cleanly via `StageLoader`, all required layers present (`06_TMX_SPEC.md` §3.1)
- [ ] If a Boss assignment: phase transitions function per `BossBase` contract (`22_API_CONTRACTS.md` §17)

### 5.3 Academic Concept Verification

- [ ] The PR's claimed academic units (from the PR template) are actually demonstrated in the code, not just mentioned in the README
- [ ] At least one concrete formula, algorithm name, or framework API call is traceable to each claimed unit
- [ ] README documents the *why*, not just the *what* (per `27_ACADEMIC_RUBRICS.md` Level 3 criteria)

### 5.4 Code Quality

- [ ] Naming conventions match `02_CODEX_CONTEXT.md` §5.2
- [ ] No hardcoded magic numbers that exist in `settings.py` (per `02_CODEX_CONTEXT.md` §5.5)
- [ ] No bare `except:` clauses
- [ ] Docstrings present on custom classes and public methods

### 5.5 Documentation Completeness

- [ ] README front-matter is valid and complete per `23_DATA_SCHEMAS.md` §7
- [ ] `units_demonstrated` field in front-matter matches the actual milestone reached
- [ ] Any deferred work is logged in `KNOWN_GAPS.md` per `23_DATA_SCHEMAS.md` §8, not silently absent

### 5.6 Reviewer Outcome

After completing the checklist, the reviewer leaves one of three outcomes:

| Outcome | Meaning |
|---|---|
| **Approve** | All checklist items pass; merge to `main` |
| **Request Changes** | One or more checklist items fail; specific, actionable feedback required per failed item |
| **Comment Only** | Non-blocking suggestions; PR may be merged at author's discretion |

---

## 6. .gitignore Requirements

The repository's `.gitignore` must exclude, at minimum:

```
.venv/
__pycache__/
*.pyc
tests/output/
*.pkl          # student-trained models — large binary, regeneratable, NOT excluded from student submission folders themselves (see note below)
.pytest_cache/
.vscode/settings.json   # personal editor config, not shared project config
```

**Important exception:** `*.pkl` model files **inside a student's own assignment folder** (`src/stages/<assignment_id>/models/*.pkl`) are explicitly **tracked**, not ignored — they are required Evaluación Práctica III deliverables per `23_DATA_SCHEMAS.md` §6.2 and `27_ACADEMIC_RUBRICS.md` §4. The blanket `*.pkl` ignore pattern above must be scoped (e.g., `/tests/**/*.pkl` only) or the student model files must be explicitly re-included with a `!src/stages/**/models/*.pkl` negation pattern. AI assistants configuring `.gitignore` in Phase 0 of `25_IMPLEMENTATION_ROADMAP.md` must implement this scoping correctly.

---

## 7. Repository Hygiene for AI-Assisted Sessions

Since multiple AI tools (Claude Code, Cline, OpenCode, Codex) may work on this repository across different sessions per the original project brief, the following hygiene rules prevent cross-session conflicts:

- [ ] Before starting work, run `git status` and `git log --oneline -10` to understand the current state.
- [ ] Before starting a new phase (per `25_IMPLEMENTATION_ROADMAP.md`), confirm via `git log` that the previous phase's commits are present.
- [ ] Never force-push (`git push --force`) to `main` or `develop` under any circumstance.
- [ ] Never force-push to a student branch unless explicitly requested by that student/the professor.
- [ ] If a merge conflict arises between two AI-assisted sessions' work, stop and surface the conflict for human resolution rather than auto-resolving silently — silent auto-resolution risks discarding intentional design decisions recorded in `28_DECISION_LOG.md`.

---

## 8. Summary Quick Reference Card

```
BRANCH:    student/<assignment_id>  |  feature/<phase-name>  |  fix/<desc>  |  docs/<desc>
COMMIT:    [SCOPE] type: description
PR TITLE:  [SCOPE] Short summary
MERGE TO:  main (via PR review only, never direct push)
REVIEW AT: Class 5, 8, 11 (Evaluación Práctica checkpoints) for student PRs
NEVER:     bypass framework API · import banned libraries directly · touch files outside your scope · force-push shared branches
```


---
## 🔗 Documentos Relacionados

- [[28_DECISION_LOG.md|Decision Log]]
