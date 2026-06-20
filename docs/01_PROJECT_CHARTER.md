# Legacy of InFest — Project Charter

**Document ID:** LOI-CHARTER-001  
**Version:** 1.0.0  
**Status:** Official  
**Audience:** Professor, Teaching Assistants, Students

---

## 1. Executive Summary

Legacy of InFest is an academic game framework built on Python 3.14+ and Pygame CE, designed for use in a university-level Computer Graphics, Digital Image Processing, and Pattern Recognition course. The framework provides a fully operational, SNES-era 2D action platformer environment in which students apply theoretical course concepts through structured, hands-on implementation tasks.

The framework is not a commercial game. It is not a student-built engine. It is a pedagogical instrument — a controlled laboratory environment where every system has been designed to teach a specific concept, and where every student deliverable maps directly to a course learning objective.

The professor owns and maintains the engine, the base stages, all shared assets, all core systems, and all documentation. Students contribute three dedicated stages — Stage 1, Stage 2, and Stage 3 — each of which exercises a defined subset of the academic syllabus.

---

## 2. Purpose

The purpose of Legacy of InFest is threefold:

**2.1 Academic Integration**  
To provide a unified, semester-long context in which all course topics — from coordinate transformations and Bézier curves to image segmentation and pattern recognition — are applied in a coherent, meaningful environment rather than as disconnected exercises.

**2.2 Technical Scaffolding**  
To eliminate the engineering overhead that would otherwise prevent students from engaging deeply with academic content. Students should not spend time building collision systems, asset loaders, scene managers, or input handlers. Those systems exist and are documented. Students use them.

**2.3 Executable Documentation**  
Stage 0, built by the professor, serves as a living reference implementation. Every system the student will use is demonstrated in Stage 0. Students are expected to study it in the same way they would study a textbook — by reading, running, and modifying it to understand behavior.

---

## 3. Vision

The vision of Legacy of InFest is to make the abstract visible. Computer graphics theory is often taught with isolated exercises that students quickly forget. By embedding the same theory into a running game — one with animation, collisions, enemies, lighting effects, and player feedback — students develop intuition for why these concepts matter and how they behave under real-time constraints.

By the end of the course, a student should be able to:

- Implement a stage using the framework's scene and layer system
- Apply color space transformations and demonstrate their visual effect in-game
- Generate and animate a sprite path using interpolation or spline mathematics
- Apply convolution filters to texture or sprite data in real time
- Implement a basic pattern recognition routine that reacts to in-game visual state
- Articulate the relationship between every system they used and the academic topic it demonstrates

---

## 4. Scope

### 4.1 In Scope

| Area | Description |
|---|---|
| Framework Core | Engine loop, scene manager, input system, audio system, asset pipeline |
| Academic Systems | Color processing, filter pipeline, sprite mathematics, collision detection |
| Stage 0 | Complete professor-built demonstration stage |
| Student Stages | Stage 1, Stage 2, Stage 3 (one per student group or individual, per course design) |
| Player System | Hooded protagonist with full movement, attack, and damage model |
| Enemy Templates | Walker, Flying, Shooter base classes |
| HUD | Hearts, timer, portrait, banner, tutorial messages |
| Documentation | All 10 official documents in this package |
| TMX Integration | Tiled map format for stage design |

### 4.2 Out of Scope

| Area | Reason |
|---|---|
| Multiplayer networking | Not an academic objective; adds unmanageable complexity |
| Procedural level generation | Contradicts pedagogical clarity and reproducibility |
| Dialogue systems | Outside course scope |
| Inventory or RPG systems | Outside course scope |
| 3D rendering | The framework is strictly 2D |
| Commercial publishing | This framework is not intended for release |
| Online leaderboards | No server infrastructure |
| Save file persistence | Not required for academic assessment |
| Mobile platforms | Desktop-only (Windows, macOS, Linux) |
| Custom shaders (GLSL) | Pygame CE does not expose shader pipelines in the academic scope |
| Multiple stages/bosses per student | **Corrected per syllabus:** each student is individually assigned exactly one Stage or Boss for the trimester (see `21_COURSE_SCHEDULE.md` Class 1) |

---

## 5. Stakeholders

| Role | Responsibility |
|---|---|
| **Professor** | Framework author, documentation owner, Stage 0 developer, grader |
| **Teaching Assistant** | Student support, grading assistance, bug reporting |
| **Student** | Stage 1, 2, and 3 developer, framework consumer |
| **University** | Institutional context, academic calendar, evaluation standards |

---

## 6. Technology Stack

### 6.1 Runtime

| Component | Technology | Version |
|---|---|---|
| Language | Python | 3.14+ |
| Game Framework | Pygame CE | Latest stable |
| Numerical Computation | NumPy | Latest stable |
| Scientific Computation | SciPy | Latest stable |
| Computer Vision | OpenCV (opencv-python) | Latest stable |
| Image Processing | scikit-image | Latest stable |
| Machine Learning | scikit-learn | Latest stable |
| Image I/O | Pillow | Latest stable |
| Tiled Map Loading | pytmx | Latest stable |
| Scrolling Maps | pyscroll | Latest stable |
| Easing / Tweening | pytweening | Latest stable |

### 6.2 Tools

| Tool | Purpose |
|---|---|
| VS Code | Primary IDE |
| Git | Version control |
| GitHub | Repository hosting and collaboration |
| Tiled | Tile map editor for stage design |
| Aseprite | Pixel art and sprite animation |

### 6.3 Target Platform

| Property | Specification |
|---|---|
| OS | Windows 10+, macOS 12+, Ubuntu 22.04+ |
| Internal Resolution | 320×224 |
| Display Scaling | Integer scale to nearest monitor resolution |
| Input | Keyboard, Xbox controller, generic USB/Bluetooth controllers |

---

## 7. Repository Structure

**Corrected per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §2.A.6 and §7.** This tree reflects the actual private GitHub repository structure. The `engine/`, `framework/`, and `stages/` subtrees from the original design are preserved entirely as documented below — they are relocated under `src/` rather than at repo root, and `student_templates/` is added as the canonical starter scaffold location.

```
legacy-of-infest/                      # Actual GitHub private repo root
│
├── docs/                              # All official documentation (this package)
│   ├── 00_SYLLABUS_ALIGNMENT_AUDIT.md
│   ├── 01_PROJECT_CHARTER.md
│   ├── 02_CODEX_CONTEXT.md
│   ├── 03_ARCHITECTURE.md
│   ├── 04_PLAYER_SPEC.md
│   ├── 05_ENEMY_SPEC.md
│   ├── 06_TMX_SPEC.md
│   ├── 07_STAGE0_DESIGN.md
│   ├── 08_SYLLABUS_MAPPING.md
│   ├── 09_HUD_SPEC.md
│   ├── 10_LIBRARIES_AND_DEPENDENCIES.md
│   ├── 11_FILTER_TOOLS_SPEC.md
│   ├── 12_VISION_TOOLS_SPEC.md
│   ├── 13_PATTERN_RECOGNITION_SPEC.md
│   ├── 14_PROFESSOR_DELIVERABLE_MATRIX.md
│   ├── 15_ACADEMIC_DEMO_SCENES.md
│   ├── 16_WORLD_DESIGN.md
│   ├── 17_BOSS_SPEC.md
│   ├── 18_ENEMY_ROSTER.md
│   ├── 19_NARRATIVE_AND_LORE.md
│   ├── 20_ASSET_BIBLE.md
│   └── 21_COURSE_SCHEDULE.md
│
├── assets/                            # Professor-owned shared asset library
│   ├── sprites/
│   ├── tilesets/
│   ├── backgrounds/
│   ├── music/
│   ├── sfx/
│   ├── fonts/
│   └── ui/
│
├── src/                               # All Python source code
│   ├── engine/                        # Professor-owned. Students do not modify.
│   │   ├── core/
│   │   ├── scene/
│   │   ├── input/
│   │   ├── audio/
│   │   ├── ui/
│   │   └── utils/
│   ├── framework/                     # Professor-owned. Students do not modify.
│   │   ├── entities/
│   │   ├── stage/
│   │   └── processing/
│   │       ├── filter_tools.py
│   │       ├── vision_tools.py
│   │       └── pattern_recognition_tools.py
│   └── stages/                        # Stage and boss implementations
│       ├── stage0/                    # Professor-owned. Executable documentation.
│       └── <student_assignments>/     # One folder per assigned Stage/Boss, populated as students commit
│
├── student_templates/                 # Canonical starter scaffold for student assignments
│   ├── stage_template/
│   │   ├── stage_template.py
│   │   ├── stage_template.tmx
│   │   └── README_template.md
│   └── boss_template/
│       ├── boss_template.py
│       └── README_template.md
│
├── tests/                             # Unit and integration tests
│
├── main.py                            # Application entry point
├── requirements.txt                   # Python dependency manifest
├── README.md
└── LICENSE
```

**No class, module, dependency rule, or responsibility defined elsewhere in this documentation package changes as a result of this relocation.** All import paths used in code generation must be prefixed accordingly (e.g., `src.engine.core.app`, `src.framework.processing.filter_tools`).

---

## 8. Development Workflow

### 8.1 Environment Setup

Students must follow the environment setup guide in `README.md`. The setup process:

1. Clone the repository from GitHub.
2. Create a Python virtual environment: `python -m venv .venv`
3. Activate the virtual environment.
4. Install dependencies: `pip install -r requirements.txt`
5. Run `main.py` to verify the framework launches and Stage 0 runs.

### 8.2 Branching Strategy

| Branch | Owner | Purpose |
|---|---|---|
| `main` | Professor | Stable, reviewed code only |
| `stage0` | Professor | Stage 0 development |
| `stage1` | Student(s) | Stage 1 development |
| `stage2` | Student(s) | Stage 2 development |
| `stage3` | Student(s) | Stage 3 development |

Students **never** push to `main` or `stage0`. Pull requests from student branches to `main` are reviewed by the professor before merging.

### 8.3 Commit Standards

All commits must follow the format:

```
[STAGE1] feat: add Bézier curve enemy patrol path
[STAGE2] fix: correct HSV conversion producing negative saturation
[STAGE3] docs: update README with Watershed segmentation notes
```

### 8.4 Assessment Cadence

**Corrected per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §2.A.3.** The course runs as **11 effective classes of 4 hours** (2h theory + 2h practice) within a trimestral period, plus a 12th session reserved for Invenio Fest. There is no 16-week schedule. The complete class-by-class calendar, including which class each evaluation instrument falls in, is defined in `21_COURSE_SCHEDULE.md`. Summary:

| Class | Milestone |
|---|---|
| 1 | Framework orientation; each student individually selects **one** Stage or Boss |
| 5 | Evaluación Práctica I — Prototipo Funcional |
| 8 | Evaluación Práctica II — Vertical Slice |
| 11 | Evaluación Práctica III — Integración Final |
| 12 | Invenio Fest (interdisciplinary group presentation) |

**Official evaluation weighting** (verbatim from the course syllabus, replacing any prior invented weighting):

| Instrumento | Porcentaje |
|---|---|
| Quices | 15% |
| Prácticas de laboratorio | 20% |
| Evaluación Práctica I – Prototipo Funcional | 15% |
| Evaluación Práctica II – Vertical Slice | 15% |
| Evaluación Práctica III – Integración Final | 15% |
| Proyecto Integrador Invenio Fest | 20% |
| **Total** | **100%** |

**Individual work model (corrected):** Legacy of InFest is an **individual** project. Each student selects exactly **one** Stage or Boss in Class 1 and develops it through all three Evaluación Práctica checkpoints. References elsewhere in this documentation to "Stage 1 / Stage 2 / Stage 3" describe the three cumulative milestone states (prototype → vertical slice → final integration) of that **same single assignment** — not three different stages built by one student, and not a team deliverable.

### 8.5 Code Review Policy

The professor performs code review on all student pull requests. The review checks:

- Correct use of the framework API (no bypassing engine systems)
- Academic concept implementation (the feature must actually use the concept)
- Code quality and documentation
- TMX file correctness
- No modifications to `engine/` or `framework/` directories
