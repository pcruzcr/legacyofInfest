# Legacy of InFest — Syllabus Alignment Audit

**Document ID:** LOI-AUDIT-000  
**Version:** 1.0.0  
**Status:** Official  
**Source of Truth:** `syllabus_compu_grafica.docx` — TIIT3002.1 Computación Gráfica y Procesamiento de Imágenes I, Universidad Invenio  
**Audience:** Professor, Academic Committee, AI coding assistants

---

## 1. Purpose

This document is the authoritative reconciliation between the official course syllabus and the Legacy of InFest documentation package (Documents 01–20). It classifies every identified difference into one of three categories and states the corrective action taken, if any.

| Classification | Meaning | Action |
|---|---|---|
| **A — Real Contradiction** | Documentation states something the syllabus explicitly contradicts | Must be corrected |
| **B — Valid Design Decision** | Documentation makes a pedagogical or technical choice the syllabus permits but does not specify | Preserved as-is, clarified as professor's discretion |
| **C — Legitimate Framework Extension** | Documentation operationalizes something the syllabus describes only at a conceptual level | Preserved as-is, marked as extension |

No item in this audit results in deletion of framework content, Stage 0, the zone/stage structure, the Enemy Roster, the Boss Roster, the Asset Bible, World Design, or the processing tool specifications (FilterTools, VisionTools, PatternRecognitionTools). Per explicit instruction, these are pedagogical design decisions of the framework and do not contradict the syllabus.

---

## 2. Classification A — Real Contradictions (Corrected)

### A.1 Individual vs. Team Work Model

**Syllabus states (verbatim):** *"Legacy of InFest es el proyecto integrador **individual** de la asignatura"* and *"Cada estudiante selecciona un Stage o Boss durante la primera clase."*

**Prior documentation issue:** `01_PROJECT_CHARTER.md` described a workflow where students collectively build "Stage 1, Stage 2, Stage 3" as if each student produces three sequential stages, and branching/PR conventions implied team-style collaborative review across multiple stage outputs per student.

**Correction:** Each student selects **one** Stage or Boss in Class 1 and develops that single assignment through all three Evaluación Práctica checkpoints (I, II, III). "Stage 1 / Stage 2 / Stage 3" in the existing framework documents refers to the **student's three cumulative submission milestones for their one assigned Stage/Boss**, not three different stages built by the same student. This terminology distinction is clarified in `01_PROJECT_CHARTER.md` and `08_SYLLABUS_MAPPING.md`.

**Status:** Corrected in this realignment pass.

---

### A.2 Evaluation Weights and Instruments

**Syllabus states (verbatim):**

| Instrumento | Porcentaje |
|---|---|
| Quices | 15% |
| Prácticas de laboratorio | 20% |
| Evaluación Práctica I – Prototipo Funcional | 15% |
| Evaluación Práctica II – Vertical Slice | 15% |
| Evaluación Práctica III – Integración Final | 15% |
| Proyecto Integrador Invenio Fest | 20% |
| **Total** | **100%** |

**Prior documentation issue:** `01_PROJECT_CHARTER.md` §8.4 and `14_PROFESSOR_DELIVERABLE_MATRIX.md` §12 invented different assessment instruments ("Exam I — Theory", "Practical I/II/III" with different content scope, no Quices, no Invenio Fest weight, no Lab percentage) that do not match the official weighting or instrument names.

**Correction:** All evaluation references now use the exact six official instruments and percentages. See new `21_COURSE_SCHEDULE.md` §5 for the corrected evaluation table, and the corrected `01_PROJECT_CHARTER.md` §8.

**Status:** Corrected in this realignment pass.

---

### A.3 Trimester Duration and Class Count

**Syllabus context (from user-provided operational detail, consistent with "Periodo Académico: Trimestral"):** 11 effective classes of 4 hours each (2h theory + 2h practice), with Class 12 reserved for Invenio Fest.

**Prior documentation issue:** No document defined a class calendar. `01_PROJECT_CHARTER.md` §8.4 invented a 16-week academic milestone schedule ("Week 4", "Week 7", "Week 10", "Week 13", "Week 16") that contradicts the trimestral 11+1 class structure.

**Correction:** The 16-week schedule is removed from `01_PROJECT_CHARTER.md` §8.4 and replaced with a reference to the new `21_COURSE_SCHEDULE.md`, which defines the real 11-class + Invenio Fest structure.

**Status:** Corrected in this realignment pass.

---

### A.4 John and Jin — Official Origin Story

**Syllabus states (verbatim):** *"John, hijo de un empresario vinculado a la explotación minera. Jin, hija de una familia relacionada con la industria pesquera... Una pepita de oro proveniente de Crucitas. Una extraña perla nacida en un raro coral marino."*

**Prior documentation issue:** `19_NARRATIVE_AND_LORE.md` §3 stated John "found it while hiking near the university" and Jin "found it washed up on a beach during a field trip" — omitting the official family backgrounds (mining industry father / fishing industry family) and the specific named origin of each relic (Crucitas gold mining region; rare marine coral).

**Correction:** `19_NARRATIVE_AND_LORE.md` §3 and §4 are corrected to state the official family backgrounds and relic origins verbatim as defined by the syllabus. See corrected excerpt in Section 6 of this audit.

**Status:** Corrected in this realignment pass.

---

### A.5 Tilawa — Official Culture Name

**Syllabus states (verbatim):** *"Paburu, un antiguo chamán de la cultura ancestral de Tilawa."*

**Prior documentation issue:** `19_NARRATIVE_AND_LORE.md` and `17_BOSS_SPEC.md` used real-world **Maleku** cultural references (Maléku Jaíka language, real Maleku masks, Guatuso canton) as the cultural grounding for Paburu and the mask iconography.

**Correction:** This is a **partial correction**. The syllabus defines a **fictional** culture named **Tilawa** as the official in-universe culture — this is not the same as the real-world Maleku people. The documentation is corrected to use "Tilawa" as the official fictional culture name throughout. However, the real-world respectful-design principle is **preserved** as a production guideline: Tilawa, while fictional, should continue to be designed with the same care, dignity, and avoidance of caricature that was applied when Maleku references were used, since Tilawa is clearly inspired by real Costa Rican and Central American indigenous heritage in the spirit of the course's setting. Real-world tribal names, sacred objects, and ceremonial terminology (e.g. "Maleku mask," "Maléku Jaíka") are removed from official game text and replaced with the fictional Tilawa equivalents.

**Status:** Corrected in this realignment pass. See `19_NARRATIVE_AND_LORE.md` v2 and `17_BOSS_SPEC.md` v2 cultural notes.

---

### A.6 Repository Structure

**Actual repository (confirmed by professor):**

```
docs/
assets/
src/
student_templates/
main.py
requirements.txt
README.md
LICENSE
```

**Prior documentation issue:** `03_ARCHITECTURE.md` §1 defined a repository structure using `engine/` and `framework/` as top-level directories instead of `src/`, and did not include a `student_templates/` directory at all.

**Correction:** This is classified as **A (contradiction)** because the actual repository already exists with a different top-level layout than what was documented, and `03_ARCHITECTURE.md` is the document AI coding assistants will use to generate code — it must match the real repo or it will create a duplicate, conflicting structure.

**Resolution applied:** `engine/` and `framework/` are preserved as logical **subpackages inside `src/`** (i.e., `src/engine/`, `src/framework/`), which keeps every class, module, and dependency-rule design from `03_ARCHITECTURE.md` v1 completely intact — only the top-level container changes from repo-root to `src/`. The `student_templates/` directory is added as the canonical location for the per-student starter scaffold (replacing the implicit student stage folders under `stages/` for the *template* purpose only — actual student submissions still live under `stages/` once a student commits their work, consistent with the original branching model). See corrected `03_ARCHITECTURE.md` §1 in Section 7 of this audit and the full updated tree in `21_COURSE_SCHEDULE.md` Appendix A.

**Status:** Corrected in this realignment pass — structural relocation only, zero content/class loss.

---

## 3. Classification B — Valid Design Decisions (Preserved, Clarified)

### B.1 Implementation-Layer Libraries (PyTMX, PyScroll, PyTweening)

**Syllabus states (verbatim):** *"NumPy, OpenCV, Matplotlib, Scikit-Image, Scikit-Learn, Pillow... La persona docente podrá incorporar otras bibliotecas complementarias cuando los objetivos de aprendizaje así lo requieran."*

**Assessment:** The syllabus explicitly grants the professor authority to add complementary libraries. PyTMX (map parsing), PyScroll (scrolling renderer), and PyTweening (easing functions) are **engine implementation choices** that make Pygame CE function as a usable 2D framework — they carry no academic weight of their own and are never touched directly by students (per `02_CODEX_CONTEXT.md` and `10_LIBRARIES_AND_DEPENDENCIES.md`).

**Conclusion:** **Not a contradiction.** `10_LIBRARIES_AND_DEPENDENCIES.md` is preserved unchanged, but is now explicitly cross-referenced against §4 of this audit's library table to make the distinction administratively clear (see Section 4 below).

**Status:** No content change required. Clarifying cross-reference added.

---

### B.2 Pygame CE as the Rendering Framework

**Syllabus context:** The syllabus does not name Pygame, Pygame CE, or any specific game framework. It names only the 6 core libraries (NumPy, OpenCV, Matplotlib, Scikit-Image, Scikit-Learn, Pillow) plus Python, and grants discretion for "otras bibliotecas complementarias."

**Assessment:** Selecting Pygame CE as the interactive rendering and game-loop layer is squarely within the professor's documented discretion — the syllabus requires "aplicaciones visuales interactivas" and "interfaces gráficas de usuario" (Unit IX) but does not mandate a specific rendering technology. This is the central, load-bearing architectural decision of the entire framework.

**Conclusion:** **Not a contradiction. Valid design decision**, foundational to the project and explicitly preserved per instruction.

---

### B.3 Matplotlib Integration Gap

**Observation:** The syllabus lists **Matplotlib** as one of the six core required libraries, but no existing document (`10_LIBRARIES_AND_DEPENDENCIES.md`, `11_FILTER_TOOLS_SPEC.md`, `12_VISION_TOOLS_SPEC.md`, `13_PATTERN_RECOGNITION_SPEC.md`) currently specifies where or how Matplotlib is used.

**Assessment:** This is not a contradiction (nothing in the docs says Matplotlib is excluded), but it is a **gap** that should be closed in a future documentation pass, since Matplotlib is one of the six explicitly mandated libraries and currently has zero defined integration point. Likely uses: (1) histogram and confusion-matrix visualization in `tests/output/`, (2) static plots for the Evaluación Práctica III dataset/training report (`EvaluationResult` visualization), (3) `tools/build_dataset.py` and the training notebook template referenced in `13_PATTERN_RECOGNITION_SPEC.md` §20.

**Conclusion:** **Not a contradiction** — flagged as an open item for the next documentation cycle, not corrected in this pass per the restriction against expanding scope. Recorded here so it is not lost.

**Status:** Logged as a follow-up item. No new mechanics or documents created for it in this pass.

---

### B.4 Stage 0 as Professor-Owned Executable Documentation

**Assessment:** The syllabus does not mention "Stage 0" by name, but it implicitly requires that students have a working reference environment before they can build their own Stage/Boss ("el estudiante demuestra el dominio... mediante la construcción incremental de un Stage o Boss," which presupposes a functioning framework to build within). Stage 0 operationalizes this requirement.

**Conclusion:** **Valid design decision.** Preserved unchanged per explicit instruction.

---

### B.5 Internal Stage Subdivision per Zone (1-1, 1-2, 1-3, 1-4, etc.)

**Syllabus states (verbatim, Zone 1 description):** *"Inspirada en: Entrada principal. Áreas naturales. Soda. Aulas. Residencias."* — five named environmental areas, presented as inspiration for the zone, not as a mandated 1:1 list of separate playable stages.

**Assessment:** `16_WORLD_DESIGN.md` operationalized these five named areas into four discrete framework stages (1-1 La Entrada, 1-2 La Soda, 1-3 Las Aulas, 1-4 La Residencia/Boss). This is a **framework implementation decision**, not a contradiction — the syllabus names these exact locations as the zone's thematic content; `16_WORLD_DESIGN.md` simply gives them stage boundaries so they can function as buildable units in the engine.

**Important clarification required by the individual-work correction (A.1):** A single student is assigned **one** Stage or Boss (e.g., "Stage 1-2 La Soda" or "Boss El Venado Sagrado") — not all four sub-stages of a zone. The internal 1-1/1-2/1-3/1-4 subdivision exists so that **multiple different students**, each working individually, can each be assigned a different stage within the same zone, all sharing one coherent narrative environment. This is the correct reading and is now made explicit in `21_COURSE_SCHEDULE.md` §3.

**Conclusion:** **Valid design decision, clarified.** Zone/stage structure, World Design, Enemy Roster, Boss Roster, and Asset Bible remain entirely unchanged per explicit instruction. Only the assignment model (one student → one stage/boss) is clarified.

---

### B.6 FilterTools, VisionTools, PatternRecognitionTools as Encapsulation Layers

**Assessment:** The syllabus requires students to apply OpenCV, Scikit-Image, and Scikit-Learn techniques (Units VII, VIII, IX) but does not specify whether students call these libraries directly or through a wrapper. Encapsulating them behind `FilterTools`/`VisionTools`/`PatternRecognitionTools` is a pedagogical scaffolding decision — consistent with the syllabus's emphasis on "calidad de software... documentación técnica y buenas prácticas de ingeniería" (Section 11) and with the framework's general professor-builds-the-engine / student-applies-concepts philosophy already established in `02_CODEX_CONTEXT.md`.

**Conclusion:** **Valid design decision.** Preserved unchanged per explicit instruction. `11_FILTER_TOOLS_SPEC.md`, `12_VISION_TOOLS_SPEC.md`, `13_PATTERN_RECOGNITION_SPEC.md` remain fully intact.

---

## 4. Library Classification Table (Required by Realignment Instructions)

| Library | Classification | Syllabus Status | Used Directly By |
|---|---|---|---|
| **NumPy** | Syllabus-mandated | Explicitly named | FilterTools, VisionTools, PatternRecognitionTools (internal) |
| **OpenCV (opencv-python)** | Syllabus-mandated | Explicitly named | FilterTools, VisionTools (internal) |
| **Matplotlib** | Syllabus-mandated | Explicitly named | ⚠ Integration point not yet defined — see B.3 |
| **Scikit-Image** | Syllabus-mandated | Explicitly named | VisionTools, PatternRecognitionTools (internal) |
| **Scikit-Learn** | Syllabus-mandated | Explicitly named | PatternRecognitionTools (internal) |
| **Pillow** | Syllabus-mandated | Explicitly named | Asset validation tooling (`tools/validate_assets.py`), not runtime |
| Pygame CE | Framework implementation | Permitted under "bibliotecas complementarias" | Engine core (rendering, input, audio, scenes) |
| SciPy (`scipy.ndimage`) | Framework implementation | Permitted under "bibliotecas complementarias" | FilterTools (internal — convolution, Gaussian blur) |
| PyTMX | Framework implementation | Permitted under "bibliotecas complementarias" | StageLoader (internal — TMX parsing) |
| PyScroll | Framework implementation | Permitted under "bibliotecas complementarias" | StageLoader, Camera (internal — scrolling render) |
| PyTweening | Framework implementation | Permitted under "bibliotecas complementarias" | math_utils.py (internal — easing functions) |
| joblib | Framework implementation | Permitted under "bibliotecas complementarias" (scikit-learn dependency) | PatternRecognitionTools (internal — model serialization) |

**Rule confirmed:** Students never import any of the above directly except through the framework's `FilterTools` / `VisionTools` / `PatternRecognitionTools` APIs, per `02_CODEX_CONTEXT.md` §11 and §12, which remains unchanged.

---

## 5. Boss Classification Table (Required by Realignment Instructions)

| Boss | Zone | Origin Classification | Notes |
|---|---|---|---|
| **El Venado Sagrado** | 1 — Campus Guanacaste | **Syllabus-official** | Verbatim from syllabus: *"Una antigua criatura esquelética cubierta de musgo, barro, hojas y raíces que protege los dominios naturales del campus."* Fully consistent with `17_BOSS_SPEC.md` §3. |
| **El Rey Terciopelo** | 2 — Contenium Data Center | **Syllabus-official** | Verbatim from syllabus: *"Una entidad formada por miles de serpientes terciopelo que actúan como un único organismo."* Fully consistent with `17_BOSS_SPEC.md` §4. |
| **El Gavilán Camionero Mascarero** | 3 — Campus Heredia | **Project-defined (post-syllabus), now professor-confirmed as official.** *(See addendum below — originally pending at the time of this audit, since resolved.)* | **Syllabus explicitly states the Zone 3 boss is "Pendiente de definición final dentro de la narrativa general."** This boss was authored by the documentation project, not the syllabus. It is **preserved** as a legitimate framework extension per the instruction *"si un elemento fue definido posteriormente como parte oficial del framework, debe conservarse"* — it has since been adopted as the working Zone 3 boss design and is now treated as the project's official answer to the syllabus's open item. **Addendum:** the professor has since confirmed this design as final (see `28_DECISION_LOG.md` ADR-008, updated). This boss is no longer pending. |

**Addendum (post-audit confirmation):** At the time this audit was originally written, El Gavilán Camionero Mascarero's status was "pending final professor sign-off." The professor has since reviewed and confirmed this boss design as the official, permanent Zone 3 boss. This addendum is recorded here to preserve the audit's historical accuracy as a point-in-time document, while `28_DECISION_LOG.md` ADR-008 and `31_RISK_REGISTER.md` (RISK-A04, closed) hold the current authoritative status going forward.
| **Gran Shaman Paburu (Final Boss)** | Zone Final | **Syllabus-official** | Verbatim from syllabus: *"Paburu. El guardián ancestral que busca restaurar el equilibrio natural y recuperar las reliquias que provocaron su despertar."* The 4-form structure (stone head → spectral mask → relic-form A/B → spirit) in `17_BOSS_SPEC.md` §6 is a **project-defined elaboration** of the syllabus's one-paragraph description — classified as a legitimate framework extension, not a contradiction, since the syllabus gives no contrary detail to elaborate against. |

**Action taken:** `17_BOSS_SPEC.md` Section 1 (Overview) is updated with a notice clarifying that El Gavilán Camionero Mascarero is a project-defined boss filling a syllabus-acknowledged gap, and that its design remains subject to final confirmation by the professor as the authoritative course owner. No boss is removed or redesigned.

---

## 6. Corrected Narrative Excerpt (Replaces Prior Text)

The following is the corrected, syllabus-accurate version of the John/Jin/relic origin story, to replace the corresponding passage in `19_NARRATIVE_AND_LORE.md` §3:

> **John** es hijo de un empresario vinculado a la explotación minera. Llegó a Costa Rica como estudiante de intercambio en Universidad Invenio. Sin saberlo, transporta **La Pepita** — una pepita de oro proveniente de **Crucitas**, la histórica zona minera de oro en el norte de Costa Rica.
>
> **Jin** es hija de una familia relacionada con la industria pesquera. También llegó como estudiante de intercambio. Sin saberlo, transporta **La Perla** — una extraña perla nacida en un raro coral marino.
>
> La combinación de ambos objetos rompe el equilibrio natural y despierta a **Paburu**, antiguo chamán de la cultura ancestral de **Tilawa**, quien había jurado proteger a su pueblo y a la naturaleza de la región, y permanecía dormido durante siglos.

This text is the corrected baseline. The full corrected `19_NARRATIVE_AND_LORE.md` is issued as part of this realignment package (see `19_NARRATIVE_AND_LORE_v2.md`).

---

## 7. Corrected Repository Structure Excerpt (Replaces Prior Text)

The following replaces the top-level tree in `03_ARCHITECTURE.md` §1, relocating the engine/framework subtree under `src/` and adding `student_templates/`:

```
legacy-of-infest/                      ← actual GitHub private repo root
│
├── docs/                              ← This documentation package (00–21)
├── assets/                            ← Professor-owned shared asset library
├── src/                               ← All Python source (was repo-root in v1)
│   ├── engine/                        ← (unchanged from 03_ARCHITECTURE.md v1)
│   │   ├── core/
│   │   ├── scene/
│   │   ├── input/
│   │   ├── audio/
│   │   ├── ui/
│   │   └── utils/
│   ├── framework/                     ← (unchanged from 03_ARCHITECTURE.md v1)
│   │   ├── entities/
│   │   ├── stage/
│   │   └── processing/
│   └── stages/                        ← (unchanged from 03_ARCHITECTURE.md v1)
│       └── stage0/
├── student_templates/                 ← NEW — canonical per-student starter scaffold
│   ├── stage_template/
│   │   ├── stage_template.py
│   │   ├── stage_template.tmx
│   │   └── README_template.md
│   └── boss_template/
│       ├── boss_template.py
│       └── README_template.md
├── main.py                            ← Entry point (was already correct in v1)
├── requirements.txt
├── README.md
└── LICENSE
```

**No class, module, dependency rule, or responsibility defined in `03_ARCHITECTURE.md` v1 §2 through §8 changes.** Only the path prefix `src/` is added in front of `engine/`, `framework/`, and `stages/`, and `student_templates/` is added as new. All import paths in future code generation must be updated to `src.engine.*`, `src.framework.*`, `src.stages.*` accordingly.

---

## 8. Items Explicitly Confirmed Unchanged

Per the restriction in the realignment instructions, the following are confirmed **unchanged, unmodified, and unreviewed for deletion** in this audit:

- `02_CODEX_CONTEXT.md` — Framework philosophy, coding rules, architecture rules (content unchanged; only the repo path prefix from §7 above applies when this doc is read alongside `03_ARCHITECTURE.md`)
- `04_PLAYER_SPEC.md` — Player specification
- `05_ENEMY_SPEC.md` — Enemy base classes and templates
- `06_TMX_SPEC.md` — TMX specification
- `07_STAGE0_DESIGN.md` — Stage 0 design
- `09_HUD_SPEC.md` — HUD specification
- `10_LIBRARIES_AND_DEPENDENCIES.md` — Library specification (content unchanged; cross-referenced by §4 of this audit)
- `11_FILTER_TOOLS_SPEC.md` — FilterTools (Unit VII)
- `12_VISION_TOOLS_SPEC.md` — VisionTools (Unit VIII)
- `13_PATTERN_RECOGNITION_SPEC.md` — PatternRecognitionTools (Unit IX)
- `15_ACADEMIC_DEMO_SCENES.md` — Demo scenes
- `16_WORLD_DESIGN.md` — World Design / zone and stage structure
- `17_BOSS_SPEC.md` — Boss Spec (content unchanged except the Section 1 origin-classification notice described in §5 above)
- `18_ENEMY_ROSTER.md` — Enemy Roster
- `20_ASSET_BIBLE.md` — Asset Bible

---

## 9. Items Corrected in This Realignment Pass

| Document | Sections Changed | Nature of Change |
|---|---|---|
| `01_PROJECT_CHARTER.md` | §8 (Development Workflow / Evaluation) | Replaced invented evaluation instruments and 16-week schedule with official 6-instrument weighting and reference to `21_COURSE_SCHEDULE.md`; clarified individual work model |
| `03_ARCHITECTURE.md` | §1 (Repository Structure) | Relocated `engine/`, `framework/`, `stages/` under `src/`; added `student_templates/` |
| `08_SYLLABUS_MAPPING.md` | Stage-to-unit assignment language | Clarified that "Stage 1/2/3" refers to a single student's three cumulative milestone submissions for their one assigned Stage/Boss, not three separate stages |
| `14_PROFESSOR_DELIVERABLE_MATRIX.md` | §12 (Assessment Instrument Summary) | Replaced invented instrument names/weights with official six instruments and percentages |
| `17_BOSS_SPEC.md` | §1 (Overview) | Added origin-classification notice distinguishing syllabus-official bosses from the project-defined Zone 3 boss |
| `19_NARRATIVE_AND_LORE.md` | §3 (Protagonists), §4 (Relics), Tilawa references throughout | Corrected John/Jin family backgrounds, Crucitas/coral relic origins, Tilawa as official culture name replacing real-world Maleku references |

---

## 10. New Documents Issued in This Realignment Pass

| Document | Purpose |
|---|---|
| `00_SYLLABUS_ALIGNMENT_AUDIT.md` | This document |
| `21_COURSE_SCHEDULE.md` | Complete 11-class + Invenio Fest trimester calendar with theory/practice split and evaluation checkpoints |

---

## 11. Summary Verdict

The Legacy of InFest framework, as designed across Documents 01–20, is **substantially aligned** with the official syllabus. The vast majority of the documentation — the entire processing pipeline (FilterTools/VisionTools/PatternRecognitionTools), the engine architecture, the player and enemy specifications, the world design, the boss roster, and the asset bible — requires **no content change** and is confirmed as valid pedagogical and technical design work product of the professor operationalizing the syllabus.

The corrections in this pass are narrow and surgical: evaluation weighting, class calendar, narrative facts (family backgrounds, relic origins, culture name), repository path structure, and the individual-vs-shared-zone assignment model. No mechanic, system, or document was deleted. No new scope was added beyond the two documents explicitly requested.

The documentation package is now ready for the implementation phase.
