---
document_id: "LOI-BOSSRUSH-044"
title: "Legacy of InFest — Boss Rush Mode Specification"
aliases: ["Boss Rush Mode"]
tags: ["boss", "rush", "mode", "gameplay"]
description: "Boss gauntlet mode"
source: "docs/44_BOSS_RUSH_MODE.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Boss Rush Mode Specification

**Document ID:** LOI-BOSSRUSH-044
**Version:** 1.0.0
**Status:** Official
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

Boss Rush Mode (`src/framework/stage/boss_rush_mode.py`) is a consecutive boss gauntlet with health carry-over and scoring. Players fight a sequence of bosses; health and special meter persist between encounters. Score is calculated from clear time and hits taken.

---

## 2. Architecture

### 2.1 BossRushStage
Represents a single boss encounter:
- `boss_id`, `boss_name` — identification
- `scene_builder` — callable that creates the boss scene
- `phase_count` — boss phase complexity
- `defeated`, `time`, `hits_taken` — runtime state

### 2.2 BossRushMode
- `add_stage(stage)` — append to gauntlet
- `start()` — reset all stages, activate mode
- `get_current_stage()` — current encounter
- `advance_to_next()` — mark current defeated, apply score, move to next
- `record_hit()` — penalty tracking
- `is_complete()` — all bosses defeated

---

## 3. Scoring

Per boss: `max(0, 1000 − int(time * 10)) − hits_taken * 50`
- Faster clears = higher score
- Each hit taken deducts 50 points

---

## 4. Implementation Status

**File:** `src/framework/stage/boss_rush_mode.py` (92 lines)
**Status:** ✅ Complete — gauntlet logic, scoring, health carry-over
**Missing:** No UI overlay (boss name cards, score display, intermission screens)


--- Traducción al Español ---

## Modo Boss Rush

### Descripción
Modo de juego de jefes consecutivos donde el jugador enfrenta a todos los jefes en secuencia.

### Características
- Jefes consecutivos sin descanso
- Salud persistente entre combates
- Tabla de clasificación por tiempo
- Dificultad progresiva

Para la especificación completa, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[43_SPEEDRUN_MODE.md|Speedrun Mode]]
- [[17_BOSS_SPEC.md|Boss Specification]]
