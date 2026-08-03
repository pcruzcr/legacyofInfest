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

Boss Rush Mode (`src/framework/stage/boss_rush_mode.py`) is the design for a consecutive boss gauntlet with health carry-over and scoring.

**What ships today (AUD-232), measured:** choosing BOSS RUSH from the title screen chains the four bosses back to back. That is the whole of it. Health does *not* persist between encounters, no score is computed, and hits are not counted — see §4. This section used to state the carry-over as fact; it was describing the intent.

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

**File:** `src/framework/stage/boss_rush_mode.py`

**Status (AUD-232, medido):** ⚠️ **Parcial.** La lógica del módulo está escrita y
probada en aislamiento, pero el juego no la conduce.

| Pieza | Estado real | Por qué |
|---|---|---|
| Entrada desde el menú | ✅ | AUD-191 la añadió; AUD-201 arregló que dejara la pantalla en negro |
| Los cuatro jefes seguidos | ✅ | lo encadena la cola de escenarios del `SceneManager` |
| Arrastre de vida y de medidor | ❌ | `_carry_over_health` y `_carry_over_meter` se ponen a 0.0 y no tienen getter ni setter: **no está implementado dentro del módulo** |
| Puntuación | ❌ | la aplica `advance_to_next()`, a la que no llama nadie fuera del módulo |
| Recuento de golpes | ❌ | lo incrementa `record_hit()`, ídem |
| Superposición de interfaz | ❌ | rótulos de jefe, marcador, pantallas intermedias |

`context.boss_rush` se escribe en `boss_rush_entry` y **no lo lee ningún sitio**.

La versión anterior de esta sección decía «✅ Complete — gauntlet logic, scoring,
health carry-over» y daba como única carencia la interfaz. Las tres cosas que
declaraba completas son las que faltan. Registrado como **GAP-030**; el estado
real lo fija `tests/test_modos_que_no_se_veian.py`, que falla si alguien conecta
el arrastre o la puntuación sin actualizar esta tabla.


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
