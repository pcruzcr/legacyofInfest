---
document_id: "LOI-RISK-031"
title: "Legacy of InFest — Risk Register"
aliases: ["Risk Register"]
tags: ["risk", "register", "management"]
description: "Academic/pedagogical risks and mitigation"
source: "docs/81_RISK_REGISTER.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Risk Register

**Document ID:** LOI-RISK-031  
**Version:** 1.0.0  
**Status:** Official — Living Document  
**Compatibility:** Requires `21_COURSE_SCHEDULE.md`, `25_IMPLEMENTATION_ROADMAP.md`, `28_DECISION_LOG.md`  
**Audience:** Professor, Teaching Assistants

---

## 1. Purpose

No prior document addresses **what happens when something goes wrong** — a student doesn't submit, a library fails to install on someone's machine, an asset pipeline bottlenecks the professor before Class 1. This document catalogs known risks across the academic, technical, and project-management dimensions of running Legacy of InFest for a full trimester, with likelihood, impact, and a concrete mitigation for each.

This is a **living document** — update it as new risks materialize during actual course delivery, following the entry format in §3.

---

## 2. Risk Severity Matrix

| Likelihood ↓ / Impact → | Low | Medium | High |
|---|---|---|---|
| **Low** | Monitor | Monitor | Mitigate |
| **Medium** | Monitor | Mitigate | Mitigate Urgently |
| **High** | Mitigate | Mitigate Urgently | Mitigate Urgently |

---

## 3. Risk Entry Format

Each risk below follows: ID · Category · Description · Likelihood · Impact · Mitigation · Owner · Status.

---

## 4. Academic / Pedagogical Risks

### RISK-A01: Student Does Not Complete Assigned Stage/Boss

**Category:** Academic  
**Description:** A student falls behind across the trimester and arrives at Class 11 (Evaluación Práctica III) with a non-functional or severely incomplete assignment.  
**Likelihood:** Medium  
**Impact:** High (student receives a failing grade on 45% of the course — the three Evaluación Práctica instruments combined, per `21_COURSE_SCHEDULE.md` §5)  
**Mitigation:**
- Early-warning checkpoint: if a student's Evaluación Práctica I (Class 5) score is in the "Insuficiente" or "No alcanza el mínimo" band (`27_ACADEMIC_RUBRICS.md` §2 score interpretation), the professor flags this student for a mid-course check-in before Class 8.
- `26_STUDENT_TEMPLATE_SPEC.md`'s 15-minute onboarding guarantee reduces Class 1 friction that could otherwise cause early-trimester delay.
- The milestone structure itself (`08_SYLLABUS_MAPPING.md` §12) is incremental by design — a student behind at Práctica I still has II and III to recover partial credit.  
**Owner:** Professor  
**Status:** Open — ongoing monitoring each trimester

---

### RISK-A02: Student Misunderstands "Individual" Scope and Collaborates Inappropriately

**Category:** Academic / Integrity  
**Description:** Given the framework's shared codebase and the natural instinct to help classmates debug, a student's submission may contain code substantially written by another student, contradicting the syllabus's individual-project requirement (`77_SYLLABUS_ALIGNMENT_AUDIT.md` §2 A.1).  
**Likelihood:** Medium  
**Impact:** Medium (academic integrity concern, requires case-by-case adjudication outside this framework's scope)  
**Mitigation:**
- The Git branching model (`29_GIT_WORKFLOW_AND_STANDARDS.md` §2.1) scopes each student to their own branch and folder, making cross-student code copying visible in PR diffs.
- The code review checklist (`29_GIT_WORKFLOW_AND_STANDARDS.md` §5.1) explicitly checks "no modifications to ... another student's folder."
- Class 1 orientation (per `21_COURSE_SCHEDULE.md` Class 1) should explicitly state the individual-work expectation verbally, not just rely on the written syllabus.  
**Owner:** Professor  
**Status:** Open — mitigated by tooling, requires verbal reinforcement each trimester

---

### RISK-A03: ~~Matplotlib (Syllabus-Mandated) Has No Defined Integration Point~~ — RESOLVED

**Category:** Academic / Compliance  
**Description:** Per `77_SYLLABUS_ALIGNMENT_AUDIT.md` §3 B.3 and `23_DATA_SCHEMAS.md` §9, Matplotlib is one of six syllabus-mandated libraries. This was flagged as having no concrete call site anywhere in the Legacy of InFest framework/codebase.  
**Resolution (Professor-confirmed):** Matplotlib's syllabus role is **classroom/lab instructional use only** — used in lecture demonstrations, lab exercises (e.g., Lab 1–3 per `21_COURSE_SCHEDULE.md` §4), and ad-hoc student exploration (e.g., plotting a histogram while learning Unit VII concepts before translating that understanding into `FilterTools` usage). It is **not** intended to be integrated into the Legacy of InFest framework, engine, or any student Stage/Boss deliverable. No call site needs to exist in `src/`.  
**Likelihood:** N/A — closed  
**Impact:** N/A — closed  
**Mitigation:** None needed. `matplotlib~=3.9` remains pinned in `requirements.txt` (`23_DATA_SCHEMAS.md` §9) solely so it is available for in-class/lab use on the same environment as the rest of the course tooling; this satisfies the syllabus's mandate without requiring framework integration.  
**Owner:** Professor  
**Status:** **Closed — confirmed by professor, no further action required**

---

### RISK-A04: ~~Zone 3 Boss Design (El Gavilán) Reassigned Mid-Trimester~~ — RESOLVED

**Category:** Academic / Design Stability  
**Description:** Per `28_DECISION_LOG.md` ADR-008 (prior version), El Gavilán Camionero Mascarero was project-defined, not syllabus-official, and pending final professor sign-off. The concern was that a student assigned this boss could have their work invalidated by a later redesign.  
**Resolution (Professor-confirmed):** El Gavilán Camionero Mascarero **is** the Zone 3 boss — confirmed final, not a placeholder. `28_DECISION_LOG.md` ADR-008 status updated to "Accepted — Final, Confirmed by Professor."  
**Likelihood:** N/A — closed  
**Impact:** N/A — closed  
**Mitigation:** None needed going forward. Students may be assigned this boss starting any future Class 1 with no reassignment risk.  
**Owner:** Professor  
**Status:** **Closed — confirmed by professor, no further action required**

---

### RISK-A05: Quiz/Lab Distribution Ambiguity Leads to Inconsistent Grading

**Category:** Academic  
**Description:** `21_COURSE_SCHEDULE.md` §4 explicitly notes the quiz/lab count and distribution within the 15%/20% pools is "at the professor's discretion," which is correct per the syllabus but could lead to inconsistent application across sections or terms if not fixed in advance.  
**Likelihood:** Low  
**Impact:** Low  
**Mitigation:** Before each trimester begins, the professor commits to a specific quiz/lab schedule (the one in `21_COURSE_SCHEDULE.md` §4 is the documented default) and does not alter it mid-term.  
**Owner:** Professor  
**Status:** Monitor

---

## 5. Technical / Environment Risks

### RISK-T01: OpenCV Installation Failure on Student Machines

**Category:** Technical  
**Description:** `opencv-python` has known platform-specific installation issues (missing system libraries on some Linux distributions, architecture mismatches on Apple Silicon, occasional conflicts with other CV packages).  
**Likelihood:** Medium  
**Impact:** High (blocks `FilterTools`/`VisionTools`, which are required from Class 8 onward)  
**Mitigation:**
- Test the full `requirements.txt` install on Windows, macOS (Intel and Apple Silicon), and at least one Linux distribution **before** Class 1.
- Document common failure modes and fixes in a dedicated environment setup guide (`82_ENVIRONMENT_SETUP_GUIDE.md`).
- Recommend `opencv-python-headless` as a fallback if the standard package conflicts with Pygame CE's own SDL-based windowing on a specific platform (verify this is not actually needed before recommending it — flag as an open verification item).  
**Owner:** Professor / TA  
**Status:** Open — requires pre-Class-1 verification pass each trimester

---

### RISK-T02: Pygame CE / Pygame Namespace Conflict

**Category:** Technical  
**Description:** `10_LIBRARIES_AND_DEPENDENCIES.md` §14.2 already flags this: if a student's machine has both `pygame` (legacy) and `pygame-ce` installed, import conflicts occur.  
**Likelihood:** Medium (especially for students who previously took a different course using legacy Pygame)  
**Impact:** Medium (confusing import errors, but documented fix exists)  
**Mitigation:** Already mitigated in `10_LIBRARIES_AND_DEPENDENCIES.md` §14.2: `pip uninstall pygame && pip install pygame-ce`. Ensure this is surfaced prominently in Class 1 setup instructions, not buried in a reference doc students may not read proactively.  
**Owner:** Professor  
**Status:** Mitigated — ensure visibility in onboarding

---

### RISK-T03: Tiled Map Editor Not Installed or Unfamiliar to Students

**Category:** Technical / Tooling  
**Description:** TMX authoring requires the Tiled application (external to the Python/pip toolchain), which is not mentioned in `requirements.txt` since it's not a Python package.  
**Likelihood:** High (every Stage-assignment student needs this from Class 1)  
**Impact:** Medium (delays TMX-based work, but Boss-assignment students are less affected per `17_BOSS_SPEC.md` §6.2's note that boss arenas may be built as static Python geometry)  
**Mitigation:**
- Tiled installation instructions must be part of Class 1 setup, separate from the Python `requirements.txt` flow.
- `student_templates/stage_template/stage_template.tmx` (per `26_STUDENT_TEMPLATE_SPEC.md`) gives students a working file to open immediately, reducing the "blank Tiled project" learning curve.  
**Owner:** Professor  
**Status:** Open — needs explicit Class 1 instruction step

---

### RISK-T04: Scikit-Learn Version Drift Breaks Model Serialization Compatibility

**Category:** Technical  
**Description:** `joblib`-serialized `TrainedModel` objects (containing a `sklearn.pipeline.Pipeline`) can fail to load if the scikit-learn version used to save differs significantly from the version used to load (a known scikit-learn limitation, not specific to this project).  
**Likelihood:** Low within a single trimester (all students use the same pinned `requirements.txt`), Medium across trimesters if the pin is updated  
**Impact:** Medium (a saved `.pkl` from a prior trimester's `assets/models/professor_sample.pkl` could break if dependencies are later upgraded)  
**Mitigation:**
- Never change the pinned scikit-learn version (`23_DATA_SCHEMAS.md` §9) mid-trimester.
- Regenerate `assets/models/professor_sample.pkl` (Phase 12, ticket T12.9 in `80_TICKET_BACKLOG.md`) at the start of any trimester where the pin is updated.  
**Owner:** Professor  
**Status:** Mitigated by version pinning discipline

---

### RISK-T05: Performance Degradation from Unthrottled Filter/Vision Calls in Student Code

**Category:** Technical  
**Description:** `11_FILTER_TOOLS_SPEC.md` §13 and `12_VISION_TOOLS_SPEC.md` §16 document per-operation time budgets, but a student applying an expensive operation (e.g., `watershed_segment`) every frame without throttling will produce a visibly stuttering stage, which is also explicitly graded against in `27_ACADEMIC_RUBRICS.md` §3.  
**Likelihood:** High (a very common first-attempt mistake for students new to real-time constraints)  
**Impact:** Low-Medium (degrades the demo experience and costs rubric points, but does not block functional correctness)  
**Mitigation:**
- `FilterDemoScene`/`VisionDemoScene` (per `15_ACADEMIC_DEMO_SCENES.md`) let students observe real per-operation costs before writing their own throttling logic, reducing first-attempt mistakes.
- The rubric (`27_ACADEMIC_RUBRICS.md` §3, "Code quality, performance awareness" row) directly incentivizes correct throttling.  
**Owner:** Professor (pedagogical), Student (execution)  
**Status:** Mitigated by design — expected as a normal part of the learning curve, not a project failure

---

### RISK-T06: AI-Assisted Coding Sessions Lose Context Between Tool Switches

**Category:** Technical / Process  
**Description:** Per the original project brief, multiple AI tools (Claude Code, Cline, OpenCode, Codex) may work on the same repository across sessions. A tool switch without proper handoff could result in duplicate work, contradicted decisions, or phase-order violations.  
**Likelihood:** Medium  
**Impact:** Medium (wasted work, potential regression)  
**Mitigation:**
- `25_IMPLEMENTATION_ROADMAP.md` §21's Session Handoff Protocol exists specifically for this.
- `28_DECISION_LOG.md` exists specifically so a new session doesn't silently re-litigate settled decisions.
- `29_GIT_WORKFLOW_AND_STANDARDS.md` §7 gives explicit repository hygiene rules for AI-assisted sessions.  
**Owner:** Professor (process enforcement)  
**Status:** Mitigated by documentation — requires actual discipline in practice, not just the existence of the rule

---

## 6. Project Management Risks

### RISK-P01: Professor's Pre-Class-1 Asset/Engine Workload Underestimated

**Category:** Project Management  
**Description:** `14_PROFESSOR_DELIVERABLE_MATRIX.md` §13 and `25_IMPLEMENTATION_ROADMAP.md` Phases 0–9 represent substantial work (full engine, Stage 0 with all assets) that must exist **before** Class 1. If this work is incomplete, the entire course's foundation is unavailable.  
**Likelihood:** Medium (large scope, single-professor authorship, AI-assisted but still requiring review/integration time)  
**Impact:** High (course cannot start without a working framework and Stage 0)  
**Mitigation:**
- `25_IMPLEMENTATION_ROADMAP.md`'s phase structure exists precisely to make this tractable — work backward from Class 1 to determine the latest safe start date for Phase 0.
- Placeholder assets are explicitly permitted for Phase 9 (Stage 0) per the roadmap's DoD — visual polish is not required to unblock Class 1, only functional correctness.
- AI-assisted development (the explicit purpose of Documents 22–26) is intended to compress this timeline significantly versus manual implementation.  
**Owner:** Professor  
**Status:** Open — track actual Phase 0–9 completion date against Class 1 date each trimester

### RISK-P02: Documentation Drift — Code Diverges from the 31 Documents Over Time

**Category:** Project Management  
**Description:** As the codebase evolves across trimesters (bug fixes, student feedback, library updates), the documentation set (Documents 00–31) can silently become inaccurate, undermining its value as an AI-assistant reference.  
**Likelihood:** Medium  
**Impact:** Medium (future AI sessions or new TAs trust stale documentation)  
**Mitigation:**
- `28_DECISION_LOG.md` is the designated location for recording any decision that changes prior documented behavior — but only if actually used consistently.
- Recommend an end-of-trimester documentation review pass: diff actual code behavior against `22_API_CONTRACTS.md` and `23_DATA_SCHEMAS.md`, correcting drift before the next trimester's Class 1.  
**Owner:** Professor  
**Status:** Open — recommend formalizing an end-of-trimester review as a recurring process (not yet a separate document; could become one if drift becomes a recurring problem)

### RISK-P03: Invenio Fest Cross-Course Coordination Failure

**Category:** Project Management  
**Description:** Invenio Fest (`21_COURSE_SCHEDULE.md` §3 Class 12) integrates work across all of a student's trimester courses. This course's rubric (`27_ACADEMIC_RUBRICS.md` §7) isolates this course's grading contribution, but logistical coordination with other courses' professors (shared rubric understanding, presentation scheduling) is outside this framework's documentation scope entirely.  
**Likelihood:** Medium  
**Impact:** Low-Medium (affects only the 20% Invenio Fest portion, and only its administration, not its content)  
**Mitigation:** Outside the scope of Legacy of InFest documentation — flagged here as a known boundary, to be coordinated through Universidad Invenio's standard interdisciplinary-festival administration process.  
**Owner:** Professor (coordinating with other course instructors)  
**Status:** Out of scope — acknowledged boundary, not a framework defect

---

## 7. Risk Register Maintenance

This document should be revisited:
- **Before each Class 1** — review all "Open" risks, confirm mitigations are still in place.
- **After each trimester** — add any newly-discovered risk using the §3 format, update Likelihood/Impact based on actual experience, close any risk whose mitigation has proven durable across 2+ trimesters (change Status to "Closed — stable").
- **Whenever a new ADR is added to `28_DECISION_LOG.md`** that touches risk surface (e.g., a new dependency, a redesigned boss) — cross-check whether a corresponding risk entry needs updating or adding.

---

## 8. Open Risk Summary (Quick Reference)

| ID | Title | Likelihood | Impact | Status |
|---|---|---|---|---|
| RISK-A01 | Student doesn't complete assignment | Medium | High | Open |
| RISK-A02 | Inappropriate collaboration | Medium | Medium | Open |
| RISK-A03 | ~~Matplotlib unintegrated~~ | — | — | **Closed — confirmed classroom-only by professor** |
| RISK-A04 | ~~Zone 3 boss reassignment mid-trimester~~ | — | — | **Closed — confirmed official by professor** |
| RISK-A05 | Quiz/lab distribution inconsistency | Low | Low | Monitor |
| RISK-T01 | OpenCV install failure | Medium | High | Open — needs pre-term verification |
| RISK-T02 | Pygame/Pygame-CE conflict | Medium | Medium | Mitigated |
| RISK-T03 | Tiled not installed | High | Medium | Open — needs Class 1 instruction |
| RISK-T04 | Scikit-learn version drift | Low/Medium | Medium | Mitigated by pinning |
| RISK-T05 | Unthrottled filter calls | High | Low-Medium | Mitigated by design |
| RISK-T06 | AI session context loss | Medium | Medium | Mitigated by documentation |
| RISK-P01 | Pre-Class-1 workload underestimated | Medium | High | Open — track each trimester |
| RISK-P02 | Documentation drift | Medium | Medium | Open — recommend formal review |
| RISK-P03 | Invenio Fest coordination | Medium | Low-Medium | Out of scope |
