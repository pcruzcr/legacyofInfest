---
document_id: "LOI-SETUP-032"
title: "Legacy of InFest — Environment Setup Guide"
aliases: ["Environment Setup Guide"]
tags: ["setup", "environment", "guide"]
description: "Step-by-step machine setup, troubleshooting"
source: "docs/82_ENVIRONMENT_SETUP_GUIDE.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Environment Setup Guide

**Document ID:** LOI-SETUP-032  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires `10_LIBRARIES_AND_DEPENDENCIES.md`, `23_DATA_SCHEMAS.md` §9, `81_RISK_REGISTER.md`  
**Audience:** Professor, Students (Class 1 onboarding)

---

## 1. Purpose

`10_LIBRARIES_AND_DEPENDENCIES.md` §14 covers installation in 6 lines. This document is the **operational, step-by-step guide** a student actually follows during Class 1's "Framework Orientation" practice block (`21_COURSE_SCHEDULE.md` Class 1), including platform-specific instructions, non-Python tooling (Tiled, VS Code), and a troubleshooting table covering every failure mode flagged in `81_RISK_REGISTER.md` §5.

**Target:** A student following this guide reaches a running `python main.py` within 30 minutes, leaving the remaining Class 1 practice time for the 15-minute template onboarding from `26_STUDENT_TEMPLATE_SPEC.md` §8.

---

## 2. Prerequisites Checklist

Before starting, confirm:

- [ ] Access to the private GitHub repository (provided by professor)
- [ ] Git installed and configured (`git --version` succeeds; `git config user.name`/`user.email` set)
- [ ] Administrator/sudo access on your machine (required for some installs below)
- [ ] At least 2 GB free disk space

---

## 3. Step 1 — Install Python 3.14+

### 3.1 Windows

1. Download the installer from [python.org/downloads](https://python.org/downloads) — version 3.14 or later.
2. Run the installer. **Check "Add Python to PATH"** on the first screen — this is the single most common setup failure if skipped.
3. Verify: open a new terminal (PowerShell or Command Prompt) and run:
   ```
   python --version
   ```
   Expected output: `Python 3.14.x` or later.

### 3.2 macOS

1. Recommended: use [Homebrew](https://brew.sh):
   ```bash
   brew install python@3.14
   ```
2. Verify:
   ```bash
   python3 --version
   ```

### 3.3 Linux (Debian/Ubuntu-based)

```bash
sudo apt update
sudo apt install python3.14 python3.14-venv python3-pip
python3.14 --version
```

If `python3.14` is not yet in your distribution's package repository, use [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) (Ubuntu) or build from source per python.org instructions.

---

## 4. Step 2 — Clone the Repository

```bash
git clone <repository-url>
cd legacy-of-infest
```

Replace `<repository-url>` with the private GitHub repository URL provided by the professor (per `77_SYLLABUS_ALIGNMENT_AUDIT.md` §7 for the expected resulting structure).

---

## 5. Step 3 — Create and Activate a Virtual Environment

**Always work inside a virtual environment.** This isolates the project's dependencies from your system Python and from other courses' projects.

### 5.1 Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If you get an execution policy error, run PowerShell as Administrator once and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then retry activation.

### 5.2 macOS / Linux

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

### 5.3 Confirm Activation

Your terminal prompt should now show `(.venv)` at the start of the line. Confirm with:

```bash
which python    # macOS/Linux
where python    # Windows
```

The output should point **inside** your project's `.venv` folder, not a system Python location.

---

## 6. Step 4 — Install Dependencies

With the virtual environment active:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs the full pinned dependency set from `23_DATA_SCHEMAS.md` §9: `pygame-ce`, `numpy`, `scipy`, `opencv-python`, `scikit-image`, `scikit-learn`, `Pillow`, `pytmx`, `pyscroll`, `pytweening`, `joblib`, `matplotlib`.

**Expected install time:** 2–5 minutes depending on connection speed (OpenCV and scikit-learn are the largest packages).

### 6.1 Verify the Install

Run the verification sequence from `10_LIBRARIES_AND_DEPENDENCIES.md` §14.1:

```bash
python -c "import pygame; print(pygame.version.ver)"
python -c "import cv2; print(cv2.__version__)"
python -c "import numpy; print(numpy.__version__)"
python -c "import sklearn; print(sklearn.__version__)"
python -c "import skimage; print(skimage.__version__)"
python -c "import matplotlib; print(matplotlib.__version__)"
```

Every line should print a version number with no `ModuleNotFoundError` or `ImportError`. If any line fails, see §9 Troubleshooting.

---

## 7. Step 5 — Install Tiled Map Editor (Non-Python Tool)

**This is a separate application, not a pip package** — flagged explicitly in `81_RISK_REGISTER.md` RISK-T03 as a common onboarding gap. Required only if your assignment is a **Stage** (Boss assignments may not need it, per `17_BOSS_SPEC.md` §6.2).

1. Download from [mapeditor.org](https://www.mapeditor.org/) — free and open source.
2. Install for your platform (standard installer on Windows/macOS; package manager or AppImage on Linux).
3. Open `student_templates/stage_template/stage_template.tmx` (after copying it per `26_STUDENT_TEMPLATE_SPEC.md` §8) to confirm Tiled opens project files correctly.

---

## 8. Step 6 — Configure VS Code (Recommended Editor)

1. Install [VS Code](https://code.visualstudio.com/).
2. Install the **Python** extension (Microsoft) from the Extensions panel.
3. Open the cloned repository folder: `File → Open Folder...` → select `legacy-of-infest/`.
4. Select the correct Python interpreter: `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS) → `Python: Select Interpreter` → choose the one inside `.venv/`.
5. Confirm the bottom-left status bar shows the `.venv` interpreter, not a system Python.

### 8.1 Recommended (Optional) Extensions

| Extension | Purpose |
|---|---|
| Pylance | Type checking, autocomplete (pairs with the type hints throughout `22_API_CONTRACTS.md`) |
| GitLens | Git history visibility, useful for following `29_GIT_WORKFLOW_AND_STANDARDS.md` |
| Even Better TOML / YAML | Syntax highlighting for `requirements.txt`-adjacent config and README front-matter (`23_DATA_SCHEMAS.md` §7) |

---

## 9. Step 7 — Run the Application

```bash
python main.py
```

**At Phase 0 of `25_IMPLEMENTATION_ROADMAP.md`,** this prints a scaffold placeholder message and exits. **From Phase 9 onward,** this launches the full scene flow (Splash → Title → Story → Stage 0).

If a window does not appear at all (no error, no window), see §9.6 below.

---

## 10. Troubleshooting

This table directly addresses the technical risks cataloged in `81_RISK_REGISTER.md` §5, with concrete fixes.

### 10.1 `ModuleNotFoundError: No module named 'cv2'`

**Cause:** `opencv-python` failed to install, or you're not in the activated virtual environment.  
**Fix:**
```bash
# Confirm venv is active (see §5.3), then:
pip install opencv-python
```
If it still fails on Linux, you may be missing system libraries:
```bash
sudo apt install libgl1 libglib2.0-0
```

### 10.2 `pygame-ce` Conflicts with `pygame`

**Cause:** Both packages installed simultaneously cause import ambiguity (`81_RISK_REGISTER.md` RISK-T02).  
**Fix:**
```bash
pip uninstall pygame
pip install pygame-ce
```
Always verify with `python -c "import pygame; print(pygame.version.ver)"` — the version string for `pygame-ce` typically includes distinguishing metadata; if uncertain, `pip show pygame-ce` confirms the correct package is installed.

### 10.3 `pip install -r requirements.txt` Fails on scikit-learn or scipy (Compilation Error)

**Cause:** Missing a pre-built wheel for your platform/Python version combination, falling back to source compilation which requires a C compiler.  
**Fix:**
- **Windows:** Install ["Build Tools for Visual Studio"](https://visualstudio.microsoft.com/visual-cpp-build-tools/), or more simply, ensure you're using a Python version with pre-built wheels available (check [PyPI](https://pypi.org/project/scikit-learn/#files) for wheel availability matching your Python version).
- **macOS:** `xcode-select --install` to get command-line build tools.
- **Linux:** `sudo apt install build-essential python3-dev`

### 10.4 Tiled Map Editor: TMX File Won't Open / "Invalid Tileset Reference"

**Cause:** The `.tmx` file references a tileset by a relative path that doesn't match your local checkout structure.  
**Fix:** Confirm the tileset file (e.g., `tileset_stage0.png` per `20_ASSET_BIBLE.md` §7) exists at the expected relative path from the `.tmx` file's location (`assets/tilesets/`). If you moved the `.tmx` file outside its original folder, Tiled's relative path breaks — keep `.tmx` files inside their designated `src/stages/<assignment_id>/` folder.

### 10.5 PowerShell: "running scripts is disabled on this system"

**Cause:** Windows execution policy blocks the venv activation script (§5.1).  
**Fix:** See §5.1's `Set-ExecutionPolicy` instruction.

### 10.6 `python main.py` Runs With No Error But No Window Appears

**Cause (common on Linux, especially WSL or headless/remote setups):** No display server available, or SDL is defaulting to a video driver incompatible with your environment.  
**Fix:**
- Confirm you are running on a machine with an actual display (not a headless server/CI environment — those should run tests via `pytest`, per `24_TEST_PLAN.md` §2.3, not launch the windowed app).
- On WSL2, ensure WSLg is enabled (Windows 11) or an X server (e.g., VcXsrv) is running and `DISPLAY` is set correctly.

### 10.7 VS Code Shows Import Errors Despite `pip install` Succeeding

**Cause:** VS Code is pointed at the wrong Python interpreter (system Python instead of `.venv`).  
**Fix:** Re-run §8 step 4 (`Python: Select Interpreter`) and confirm the `.venv` path is selected.

### 10.8 `joblib`/Model Loading Fails with a Version Warning or Error

**Cause:** Per `81_RISK_REGISTER.md` RISK-T04, scikit-learn version mismatch between when a `.pkl` was saved and when it's being loaded.  
**Fix:** Confirm your `requirements.txt` matches exactly what the professor used to generate `assets/models/professor_sample.pkl` — re-run `pip install -r requirements.txt` to ensure no local version drift, and report persistent mismatches to the professor (this may indicate the pin table in `23_DATA_SCHEMAS.md` §9 needs updating for the current trimester).

---

## 11. Daily Workflow Quick Reference

Once setup is complete, your typical session start looks like:

```bash
cd legacy-of-infest
source .venv/bin/activate      # macOS/Linux
# OR
.venv\Scripts\Activate.ps1     # Windows PowerShell

git checkout student/<your_assignment_id>
git pull origin student/<your_assignment_id>

python main.py                 # run the game
pytest tests/ -v                # run tests (once you have any to run, per 24_TEST_PLAN.md)
```

When done for the session:

```bash
git add .
git commit -m "[<YOUR_ASSIGNMENT_ID>] feat: <description>"   # per 29_GIT_WORKFLOW_AND_STANDARDS.md §3
git push origin student/<your_assignment_id>
deactivate                      # exits the virtual environment
```

---

## 12. Verification Checklist (End of Setup)

A student has completed environment setup successfully when **all** of the following are true:

- [ ] `python --version` shows 3.14 or later
- [ ] Terminal prompt shows `(.venv)` when working in the project
- [ ] All six `import` verification lines in §6.1 succeed
- [ ] Tiled Map Editor opens (Stage assignments only)
- [ ] VS Code shows the `.venv` interpreter selected, no import errors in the editor
- [ ] `python main.py` runs without exception (placeholder message or full scene flow, depending on Phase per `25_IMPLEMENTATION_ROADMAP.md`)
- [ ] `git status` inside the repo shows you're on your own `student/<assignment_id>` branch, not `main`

Once all boxes are checked, proceed to `26_STUDENT_TEMPLATE_SPEC.md` §8's 15-minute template onboarding.


--- Traducción al Español ---

## Guía de Configuración del Entorno

### Requisitos
- Python 3.14+
- Git
- VS Code (recomendado)

### Pasos de Instalación
1. Clonar el repositorio: `git clone <repo-url>`
2. Crear entorno virtual: `python -m venv .venv`
3. Activar: `.venv\Scripts\Activate` (Windows) o `source .venv/bin/activate` (macOS/Linux)
4. Instalar dependencias: `pip install -r requirements.txt`
5. Verificar: `python main.py`

Para solución de problemas y configuración adicional, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[10_LIBRARIES_AND_DEPENDENCIES.md|Libraries and Dependencies]]
