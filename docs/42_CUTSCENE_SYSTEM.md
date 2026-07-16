---
document_id: "LOI-CUTSCENE-042"
title: "Legacy of InFest — Cutscene System Specification"
aliases: ["Cutscene System"]
tags: ["cutscene", "system", "cinematic"]
description: "Scripted cutscene system"
source: "docs/42_CUTSCENE_SYSTEM.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Cutscene System Specification

**Document ID:** LOI-CUTSCENE-042
**Version:** 1.0.0
**Status:** Official
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

The Cutscene System (`src/framework/stage/cutscene_system.py`) provides scripted, sequential action playback for in-engine cutscenes. Actions run in order; each reports completion before the next begins. Cutscenes are professor-owned — students trigger them via the script API but do not modify the system.

---

## 2. Action Types

### 2.1 CutsceneAction (Base)
Abstract interface: `start()`, `update(dt) → bool`, `draw(surface)`.

### 2.2 WaitAction
Pauses for a fixed duration in seconds. Used for timing between actions.

### 2.3 FadeAction
Fades the screen to/from black over duration. Uses per-pixel alpha overlay.

### 2.4 CameraMoveAction
Lerps the camera offset to a target `(x, y)` over duration. Uses linear interpolation.

### 2.5 DialogueAction
Displays a text box with optional speaker name, waits for ENTER/SPACE press or duration expiry. Box anchored at bottom of screen, 60px tall, 20px inset.

---

## 3. CutsceneScript

A sequential list of `CutsceneAction` objects:
- `add_action(action)` — append to script
- `start(callback)` — begin execution with optional completion callback
- `update(dt)` — advance current action; move to next when complete
- `draw(surface)` — render all active actions from current index forward

---

## 4. Execution Flow

```
start() → action[0].start()
  ↓
update() loop:
  → action[N].update(dt)
  → if complete: action[N+1].start()
  → if no more actions: callback() called, active=false
```

---

## 5. Implementation Status

**File:** `src/framework/stage/cutscene_system.py` (178 lines)
**Status:** ✅ Complete — 5 action types, sequential playback, callback on finish
**Missing:** No visual scripting editor; actions must be coded manually


--- Traducción al Español ---

## Sistema de Cinemáticas

### Descripción
Sistema de cinemáticas guionizadas para secuencias narrativas.

### Características
- Cinemáticas guionizadas con temporización
- Transiciones entre escenas
- Efectos visuales (fundidos, barras)
- Soporte de audio sincronizado

Para la especificación completa de la API, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[40_DIALOGUE_SYSTEM.md|Dialogue System]]
- [[48_SCREEN_TRANSITIONS.md|Screen Transitions]]
