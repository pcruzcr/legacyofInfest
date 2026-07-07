# Legacy of InFest — Decision Log

**Document ID:** LOI-ADR-028  
**Version:** 1.0.0  
**Status:** Official — Living Document  
**Format:** Architecture Decision Records (ADR)  
**Audience:** Professor, AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Purpose

Across 26 prior documents, dozens of decisions were made — Pygame CE over another framework, 320×224 over another resolution, SciPy included despite not being syllabus-mandated, the `src/` repository relocation, El Gavilán as a project-defined boss, and many more. None of those decisions had their **reasoning** recorded in one place. Without this record, a future AI session (or a new TA, or the professor six months from now) might "fix" something that was actually a deliberate, already-justified choice — or might repeat a debate that was already settled.

**Rule for AI assistants:** Before proposing to change any architectural, technological, or pedagogical decision already recorded here, **read this document first**. If a proposed change conflicts with an existing ADR, either justify why the ADR should be superseded (and record that as a new ADR per the format in §3) or do not make the change.

---

## 2. ADR Status Values

| Status | Meaning |
|---|---|
| **Accepted** | Currently in effect, governs the codebase |
| **Superseded** | Replaced by a later ADR (the later one is linked) |
| **Proposed** | Under consideration, not yet binding |

---

## 3. ADR Format

Each entry follows this structure: Title · Status · Context · Decision · Consequences · Alternatives Considered.

---

## ADR-001: Use Pygame CE as the Rendering and Game-Loop Framework

**Status:** Accepted

**Context:** The syllabus mandates NumPy, OpenCV, Matplotlib, Scikit-Image, Scikit-Learn, and Pillow, and permits the professor to add complementary libraries (`00_SYLLABUS_ALIGNMENT_AUDIT.md` §3 B.2). It does not specify a rendering technology. The course requires "aplicaciones visuales interactivas" (Unit IX) and a real-time environment in which Units I–IX can all be demonstrated cohesively.

**Decision:** Use Pygame CE (Community Edition) as the engine's rendering, input, audio, and game-loop layer.

**Consequences:** All engine code (`src/engine/`) depends on Pygame CE's API surface (`pygame.Surface`, `pygame.Rect`, `pygame.mixer`, `pygame.joystick`). Students never interact with Pygame CE directly except implicitly through the framework's wrapper classes.

**Alternatives Considered:**
- **Raw OpenCV window loop** — rejected: no sprite/scene/input abstraction, would require building far more engine infrastructure from scratch than Pygame CE already provides.
- **Arcade (Python library)** — rejected: smaller community, less mature controller support, no compelling advantage over Pygame CE for this use case.
- **Godot with Python via GDExtension** — rejected: adds a non-Python toolchain dependency, contradicts the syllabus's Python-centric library list, raises the onboarding barrier for an 11-class trimester.

---

## ADR-002: 320×224 Internal Resolution, SNES-Era Visual Style

**Status:** Accepted

**Context:** The framework needs a visual identity and a technical constraint that keeps asset production scope manageable for a single professor across 11 classes.

**Decision:** Internal render resolution is 320×224 pixels (the SNES's actual resolution), scaled to the display window. Visual style targets the 1993–1995 SNES era (`Super Castlevania IV`, `Blackthorne`, `Demon's Crest` as references).

**Consequences:** Every sprite, tileset, and UI element is authored at this fixed low resolution with a 16-color-per-sheet palette constraint (`02_CODEX_CONTEXT.md` §8.1). This bounds asset production time and enforces visual consistency across student-contributed content. It also makes `pygame.SCALED` integer scaling straightforward with no filtering artifacts.

**Alternatives Considered:**
- **1920×1080 native resolution, modern pixel-art style** — rejected: dramatically larger asset production burden, no natural palette/detail constraint to keep scope bounded for student work.
- **Variable/responsive resolution** — rejected: adds engine complexity (UI layout systems, asset scaling logic) with no pedagogical payoff for this course's objectives.

---

## ADR-003: Include SciPy as a Non-Syllabus-Mandated Dependency

**Status:** Accepted

**Context:** `scipy.ndimage` provides `convolve` and `gaussian_filter`, used internally by `FilterTools`. SciPy is not in the syllabus's six-library mandate.

**Decision:** Include SciPy as a framework-implementation-layer dependency, used only internally inside `filter_tools.py`. Students never import it directly.

**Consequences:** `requirements.txt` includes `scipy~=1.13` per `23_DATA_SCHEMAS.md` §9. This is explicitly classified as Classification B (Valid Design Decision) in `00_SYLLABUS_ALIGNMENT_AUDIT.md` §3 B.1, under the syllabus's "bibliotecas complementarias" discretion clause.

**Alternatives Considered:**
- **Implement convolution/Gaussian blur from scratch with pure NumPy** — rejected: reinvents well-tested, academically-standard numerical code with no pedagogical benefit (students never see this code anyway — it's hidden behind `FilterTools`), and risks subtle correctness bugs in a tool the entire course depends on.
- **Use only OpenCV for these operations, drop SciPy** — considered but rejected: OpenCV's `cv2.filter2D`/`cv2.GaussianBlur` could replace SciPy's role, but the current implementation already uses `scipy.ndimage.convolve` for `apply_kernel()`'s arbitrary-kernel case, which has a cleaner API for the academic kernel-matrix presentation in `11_FILTER_TOOLS_SPEC.md` §9. Revisiting this is low-priority — see §5 Open Questions.

---

## ADR-004: Relocate Engine/Framework Code Under `src/`

**Status:** Accepted (Supersedes the original `engine/`-at-repo-root layout from `03_ARCHITECTURE.md` v1)

**Context:** The actual private GitHub repository was created with a `src/` top-level directory before the original `03_ARCHITECTURE.md` was written, which instead placed `engine/` and `framework/` at repo root. This created a real contradiction discovered during syllabus realignment.

**Decision:** Relocate `engine/`, `framework/`, and `stages/` under `src/`. Add `student_templates/` as a new top-level directory.

**Consequences:** All import paths use the `src.engine.*` / `src.framework.*` / `src.stages.*` prefix. No class, responsibility, or dependency rule changed — only the path prefix. Documented exhaustively in `00_SYLLABUS_ALIGNMENT_AUDIT.md` §2 A.6 and §7.

**Alternatives Considered:**
- **Restructure the actual GitHub repo to match the original `engine/`-at-root design instead** — rejected: the repo already existed with real commit history ("Initial Legacy of InFest repository structure," 3 days prior per the professor's account) at the time of discovery; changing the actual repository's structure is more disruptive than updating documentation to match reality.

---

## ADR-005: Individual Assignment Model — One Student, One Stage or Boss

**Status:** Accepted (Corrects an ambiguity in pre-syllabus-audit documentation)

**Context:** Early drafts of `01_PROJECT_CHARTER.md` described a workflow that read as if a single student built three sequential stages ("Stage 1," "Stage 2," "Stage 3"). The official syllabus states Legacy of InFest is individual and that each student selects one Stage or Boss in Class 1.

**Decision:** Each student is assigned exactly one Stage or Boss for the entire trimester. "Stage 1/2/3" terminology is retained only to label the three cumulative completeness milestones (Evaluación Práctica I/II/III) of that single assignment — never three different stages.

**Consequences:** `student_templates/` provides one starting scaffold per assignment type (stage or boss), copied once per student into `src/stages/<assignment_id>/`. Grading rubrics (`27_ACADEMIC_RUBRICS.md`) score a single, evolving artifact across three checkpoints rather than three separate artifacts.

**Alternatives Considered:**
- **Reinterpret the syllabus as allowing team-based stage assignment** — rejected: the syllabus text is unambiguous ("proyecto integrador individual"); no alternative reading is defensible.

---

## ADR-006: Encapsulate OpenCV/Scikit-Image/Scikit-Learn Behind FilterTools/VisionTools/PatternRecognitionTools

**Status:** Accepted

**Context:** The syllabus requires students to apply OpenCV, Scikit-Image, and Scikit-Learn techniques but does not mandate whether students call these libraries directly.

**Decision:** Hide all three behind professor-owned wrapper classes (`FilterTools`, `VisionTools`, `PatternRecognitionTools`). Students call only the wrapper API.

**Consequences:** Students never see raw OpenCV/Scikit-Image/Scikit-Learn error messages or API quirks (e.g., BGR vs RGB channel order, axis-transposition between Pygame and OpenCV array conventions — see `23_DATA_SCHEMAS.md` §10). This trades a small amount of "real-world library fluency" for a large reduction in non-academic debugging friction during an 11-class trimester where class time is scarce (2h theory + 2h practice per class, per `21_COURSE_SCHEDULE.md`).

**Alternatives Considered:**
- **Students call OpenCV/Scikit-Image/Scikit-Learn directly** — rejected: would consume significant in-class practice time on library-specific API debugging (array shape mismatches, BGR/RGB confusion) rather than on the underlying graphics/CV concepts the syllabus actually examines.
- **Partial encapsulation (wrap only the hardest parts, e.g. BGR conversion, leave the rest direct)** — considered but rejected for consistency: a single clean boundary (`02_CODEX_CONTEXT.md` §11.1) is easier to enforce in code review than a partial one, and matches the professor-builds-the-engine / student-applies-concepts philosophy already established for the rest of the framework.

---

## ADR-007: Stage 0 as Professor-Built Executable Documentation

**Status:** Accepted

**Context:** Students need a reference implementation of every framework system before building their own assignment, but the syllabus is silent on the specific mechanism for this.

**Decision:** Build a complete, professor-owned Stage 0 that demonstrates every reusable gameplay system (movement, combat, enemies, checkpoints, HUD, etc.) with inline tutorial messages, serving simultaneously as a playable onboarding experience and a "read the source" reference for students and AI assistants alike.

**Consequences:** Stage 0 (`07_STAGE0_DESIGN.md`) is the single largest required asset+content investment for the professor before Class 1, and the Phase 9 integration milestone in `25_IMPLEMENTATION_ROADMAP.md` — every other processing module (Phases 10–14) re-runs the Stage 0 playthrough as its regression smoke test.

**Alternatives Considered:**
- **Written documentation only, no playable reference** — rejected: a static document cannot demonstrate frame-rate-dependent systems (coyote time, invincibility flashing, hitstop) as legibly as a running example.
- **A minimal "Hello World" stage instead of a full 7-zone demonstration** — rejected: would leave several framework systems (e.g., Bézier-path flying enemies, one-way platforms, HazardZones) without any reference implementation, forcing students to read engine source code cold for those cases.

---

## ADR-008: El Gavilán Camionero Mascarero as the Zone 3 Boss

**Status:** **Accepted — Final, Confirmed by Professor**

**Context:** The official syllabus originally marked the Zone 3 boss as "pendiente de definición final dentro de la narrativa general." A complete boss design (El Gavilán Camionero Mascarero — masked hawk, 3 phases) was authored by the documentation project to fill this gap and unblock framework/asset planning. The professor has since reviewed and confirmed this design as final.

**Decision:** El Gavilán Camionero Mascarero **is** the Zone 3 boss. This is no longer a placeholder pending sign-off — it is the confirmed, permanent design. `17_BOSS_SPEC.md` §1's prior "project-defined, pending sign-off" classification is updated accordingly (see `17_BOSS_SPEC.md` for the corrected boss origin table).

**Consequences:** All downstream documentation referencing El Gavilán — `17_BOSS_SPEC.md` §3, `18_ENEMY_ROSTER.md` Zone 3 enemies, `16_WORLD_DESIGN.md` Stage 3-4, `19_NARRATIVE_AND_LORE.md` §5.3, `20_ASSET_BIBLE.md` §6.3 — is now treated as stable, confirmed content, not subject to reassignment risk. A student may be safely assigned this boss starting any future Class 1 with no risk of mid-trimester invalidation. The corresponding risk entry (`31_RISK_REGISTER.md` RISK-A04) is closed.

**Alternatives Considered:**
- **Leave Zone 3 boss undefined until the professor decides** — moot: the professor has now decided.
- **Reuse one of the other three bosses' design pattern for Zone 3 (e.g., another serpent variant)** — rejected: Zone 3 (Campus Heredia, urban/aerial setting) does not thematically fit a serpent boss; an aerial predator (hawk) is a better thematic fit for the zone's described "Inspirada en: Entrada de piedra, Hall, Patio, Bungaló" environment.

---

## ADR-009: Tilawa as the Official Fictional Ancestral Culture (Replacing Real-World Maleku References)

**Status:** Accepted (Supersedes earlier drafts that used real-world Maleku cultural references)

**Context:** Early narrative drafts grounded Paburu and the ceremonial mask iconography in the real-world Maleku people of Costa Rica. The official syllabus instead names a fictional culture, "Tilawa," verbatim.

**Decision:** Use "Tilawa" as the official in-universe culture throughout all game text, while retaining the same standard of respectful, non-caricatured design that would be required if the source were a living real-world culture.

**Consequences:** All boss, narrative, and asset documentation referencing cultural elements use "Tilawa" terminology exclusively (`00_SYLLABUS_ALIGNMENT_AUDIT.md` §2 A.5, `19_NARRATIVE_AND_LORE.md` v2). No real-world tribal names, sacred object names, or ceremonial terminology belonging to actual living indigenous peoples appear in official game text.

**Alternatives Considered:**
- **Keep Maleku references since they're "more authentic"** — rejected: contradicts the syllabus's explicit naming choice, and using a real living culture's actual sacred terminology in a game context (even respectfully) carries representational risk that a fictional-but-inspired culture avoids while preserving the same real-world grounding and care in design.

---

## ADR-010: Six Official Evaluation Instruments Replace Earlier Invented Instruments

**Status:** Accepted (Supersedes the original `01_PROJECT_CHARTER.md` v1 / `14_PROFESSOR_DELIVERABLE_MATRIX.md` v1 assessment tables)

**Context:** Early documentation invented assessment instruments ("Exam I — Theory," "Practical I/II/III" with different scope, no Quices, no Invenio Fest weighting) that did not match the syllabus's six official instruments and weights.

**Decision:** Replace all invented instruments with the syllabus's exact six: Quices (15%), Prácticas de laboratorio (20%), Evaluación Práctica I/II/III (15% each), Proyecto Integrador Invenio Fest (20%).

**Consequences:** `01_PROJECT_CHARTER.md`, `14_PROFESSOR_DELIVERABLE_MATRIX.md`, `21_COURSE_SCHEDULE.md`, and `27_ACADEMIC_RUBRICS.md` all reference this exact six-instrument structure consistently. This is the highest-impact correction from `00_SYLLABUS_ALIGNMENT_AUDIT.md` (§2 A.2).

**Alternatives Considered:** None — this was a factual correction against an authoritative source document, not a design tradeoff.

---

## ADR-011: Flying Enemy Y-Tracking via Leaky-Integrator Offset

**Status:** Accepted

**Context:** The Flying enemy's alert mode must track the player's Y position, but sine and Bézier flight strategies fully reset `position.y` each frame. A direct push to `position.y` would be overwritten by the next strategy execution.

**Decision:** Use a persistent `_y_track_offset` (leaky integrator, damping 0.98). Each alert frame: strategy runs (reset position.y), Y error is computed against player center, offset is pushed toward the error at `0.4 × flight_speed`, damped by 0.98, then added to `position.y`. The offset resets to 0.0 on return to PATROL.

**Consequences:** Y-tracking survives all strategy modes. The 0.98 damping prevents windup while keeping the enemy centered near the player vertically. Simple, minimal change (3 lines in `_alert_behavior` plus field).

**Alternatives Considered:**
- **Push `velocity.y` instead of `position.y`** — rejected: flying enemies don't use velocity-based movement; strategies set position directly
- **Post-process `position.y` after every strategy** — equivalent to the chosen approach; `_y_track_offset` makes the separation explicit and traceable

---

## ADR-012: EventBus-Based SFX Wiring (SoundBank Activation)

**Status:** Accepted

**Context:** The SoundBank existed but had zero call sites — the game was completely mute. Wiring audio required deciding how entities reach the audio system.

**Decision:** Entities emit EventBus events (`Events.SFX_*`) with no knowledge of the audio system. `StageScene.on_enter()` subscribes to all 15 SFX events via a static event→filename map, calling `self.audio.play_sfx(filename)`. Stored handler references in `_sfx_handlers` dict enable clean `unsubscribe()` on exit. `SoundBank.load_all()` scans `assets/sfx/` recursively at `AudioManager` init.

**Consequences:** No audio reference passed into the entity tree. New stages that extend `StageScene` get SFX for free. Student stages with custom scenes must subscribe manually or inherit from `StageScene`. 38 `.wav` files auto-registered.

**Alternatives Considered:**
- **Audio reference in every entity** — rejected: would require threading `audio` through the entire entity constructor chain
- **Singleton AudioManager** — rejected: anti-pattern, breaks testability; EventBus approach is decoupled and testable via `emit()` assertions

---

## ADR-013: `prev_bottom` Heuristic for One-Way Platform Collision

**Status:** Accepted

**Context:** One-way platforms (passable from below) need to distinguish landing-from-above from walking-under. Prior approaches (checking `player_rect.bottom <= plat.top` or `player_rect.centery < plat.top`) failed when the player's rect was already overlapping after X-resolution.

**Decision:** Use `prev_bottom = player_rect.bottom - self.velocity.y * dt` to reconstruct the player's bottom position on the previous frame. The collision check triggers only when `prev_bottom <= plat.top` (was above or at platform top) and `velocity.y >= 0` (falling or stationary).

**Consequences:** Works for all cases: land from above (prev_bottom above), walk under (prev_bottom below), jump up through (velocity.y < 0 early return), fall through from below (prev_bottom below). Tested with headless verification.

**Alternatives Considered:**
- **`player_rect.bottom <= plat.top`** — rejected: fails when player rect overlaps platform after X-movement
- **`player_rect.centery < plat.top`** — rejected: fails when player steps onto platform from ground level (centery is below top)

---

## ADR-014: Interactive Theory Lab Scenes for Units II–VI Fill Identified Learning Gaps

**Status:** Accepted

**Context:** The syllabus alignment audit and academic deliverable matrix revealed a structural gap: the 3 original academic demo scenes (FilterDemoScene, VisionDemoScene, PatternDemoScene) cover only Units VII–IX. Units II (Vectors), III (Curves), V (Color Spaces), and VI (Collision/AABB) had no interactive visualization — students were expected to apply math_utils, curve_tools, color_tools, and collision code from static documentation alone. Professor assessment found that students "call pre-built APIs (`FilterTools.apply_kernel()`, `ColorTools.rgb_to_hsv()`) but never implement the algorithms" — the biggest learning gap across all units.

**Decision:** Create 7 interactive theory lab scenes as professor-owned extensions of the demo scene infrastructure:
- `VectorLabScene` (Unit II — Vector operations, normalization, dot product, pursuit)
- `TransformLabScene` (Unit II/III — 2D affine transformations: translate, rotate, scale, shear, composite)
- `CurveEditorScene` (Unit III — Bézier, Catmull-Rom, B-Spline, de Casteljau animation)
- `InterpolationLabScene` (Unit III/IV — linear interpolation, easing functions, keyframe animation)
- `ColorTheoryScene` (Unit V — RGB/HSV/HSL/CMYK explorers, step-by-step conversion algorithms, alpha blending, color matching challenge)
- `NoiseLabScene` (Unit V/VIII — value noise, Perlin noise, fractal noise with octaves/persistence/lacunarity)
- `CollisionLabScene` (Unit VI — Y-first vs X-first AABB resolution, prev_bottom heuristic, wall-climb bug demo)

These follow the same architecture as the original 3 demos (BaseScene subclass, keyboard-controlled, demo_layout + demo_utils infrastructure) and are also professor-owned; students do not modify them.

**Consequences:**
- Demo menu now lists 10 scenes (Units II–IX) instead of 3.
- `tests/test_demo_scenes.py` tests all 10 scenes with import/instantiate/draw tests.
- 364 tests total (original 347 + 17 new demo scene tests).
- `demo_common.py` split into `demo_layout.py` (layout/draw helpers) + `demo_utils.py` (sources, throttle, save) with backward-compatible re-exports.
- `SceneRegistry` DI container replaces the `_try_scene()` elif chain.
- `ParamPanel` widget created for reusable parameter controls.
- `DebugOverlay` (F3) with FPS, event queue snapshot, module tree browser.
- Font sizes increased (5→7, 6→9, 7→11) and layout constants adjusted for readability at 320×224.
- Documentation (`15_ACADEMIC_DEMO_SCENES.md`, `25_IMPLEMENTATION_ROADMAP.md`) updated to v1.2.

**Alternatives Considered:**
- **Expand the 3 existing demos to cover earlier units** — rejected: each demo scene has a focused pedagogical purpose; mixing vector math into FilterDemoScene would confuse both subjects.
- **No interactive labs, rely on static documentation + code comments** — rejected: the audit identified that static documentation alone does not bridge the "see the algorithm step by step" gap for students.
- **Web-based interactive tools (e.g., Observable notebook, Desmos)** — rejected: external tools break the "everything is in the game engine" pedagogical immersion; keeping labs inside Pygame CE means students practice the same input, rendering, and framework patterns they use for their assignment.

---

## 4. Decisions Explicitly Deferred (Not Yet Made)

These are flagged here rather than silently decided by whichever AI session encounters them first.

| Open Decision | Tracked In | Status |
|---|---|---|
| Whether `apply_kernel()`'s SciPy dependency should be replaced with a pure-OpenCV implementation | ADR-003 above | Open, low priority |
| Exact quiz/lab count distribution within the 15%/20% pools (syllabus permits professor discretion) | `21_COURSE_SCHEDULE.md` §4 note | Open, professor discretion |

**Resolved since last revision:** Matplotlib's role (confirmed classroom/lab-instructional use only, not a framework integration point — see `31_RISK_REGISTER.md` RISK-A03) and El Gavilán Camionero Mascarero's status as the confirmed, permanent Zone 3 boss (see ADR-008 above) have both been resolved by professor confirmation and removed from this open-items list.

---

## 5. How to Add a New ADR

When a new architectural or pedagogical decision is made during implementation (Phases 0–16 of `25_IMPLEMENTATION_ROADMAP.md`), append a new entry to this document using the format in §3, numbered sequentially (ADR-011, ADR-012, ...). Do not edit or delete prior ADRs — if a decision is reversed, add a new ADR with status **Accepted** and mark the old one **Superseded**, linking to the new one's number.
