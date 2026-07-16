---
document_id: "LOI-SPEEDRUN-043"
title: "Legacy of InFest — Speedrun Mode Specification"
aliases: ["Speedrun Mode"]
tags: ["speedrun", "mode", "gameplay"]
description: "Speedrun timer + ghost data"
source: "docs/43_SPEEDRUN_MODE.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Speedrun Mode Specification

**Document ID:** LOI-SPEEDRUN-043
**Version:** 1.0.0
**Status:** Official
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

Speedrun Mode (`src/framework/stage/speedrun_mode.py`) provides a global timer with per-stage splits and ghost data recording. The core class is `SpeedrunTimer` (not `SpeedrunMode` — note for documentation accuracy). A companion `GhostData` class records player position frames for ghost replay.

---

## 2. Architecture

### 2.1 SpeedrunTimer
- `start()` — resets timer and splits
- `stop()` / `reset()` — pause or full reset
- `update(dt)` — accumulates time when running
- `start_stage(stage_id)` — signals stage entry
- `split(stage_id)` — records a time split
- `get_formatted_time()` — `HH:MM:SS` string format
- `save(path)` / `load(path)` — JSON persistence

### 2.2 GhostData
- `record(x, y, state)` — captures a frame of player position + state
- `get_frame(index)` — retrieve frame for replay
- `clear()` / `save()` / `load()` — lifecycle management

---

## 3. Persistence

Timer splits and ghost data are saved to `saves/speedrun.json` as JSON arrays. Format:
```json
{
  "global_time": 123.45,
  "splits": [{"stage_id": "stage0", "time": 45.2}, ...]
}
```

---

## 4. Implementation Status

**File:** `src/framework/stage/speedrun_mode.py` (118 lines)
**Class Name:** `SpeedrunTimer` (⚠️ documented as `SpeedrunMode` in Doc 51)
**Status:** ✅ Complete — timer with splits, ghost data recording, JSON save/load


--- Traducción al Español ---

## Modo Speedrun

### Descripción
Modo de juego contrarreloj con seguimiento de mejores tiempos y datos fantasma.

### Características
- Temporizador global
- Datos fantasma del mejor tiempo
- Tabla de clasificación local
- División por zonas/checkpoints

Para la especificación completa, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[44_BOSS_RUSH_MODE.md|Boss Rush Mode]]
- [[09_HUD_SPEC.md|HUD Specification]]
