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

**What ships today (AUD-261), measured:** choosing BOSS RUSH from the title screen chains the four bosses back to back, health carries over between encounters with a declared partial heal (`CURACION_ENTRE_COMBATES`), hits are counted, and the score is computed per fight from time and damage taken — see §4.

**History, kept on purpose.** Between AUD-232 and AUD-261 this paragraph read: «That is the whole of it. Health does *not* persist between encounters, no score is computed, and hits are not counted.» Before AUD-232 it read «✅ Complete — gauntlet logic, scoring, health carry-over», and all three were false. The middle version was the honest one, and it is what made the fix possible: it named what was missing instead of claiming it was there.

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
| Arrastre de vida y de medidor | ✅ | AUD-261. `salud_arrastrada` y `medidor_arrastrado` son API pública; `StageScene` los escribe al caer el jefe y los aplica al entrar en el siguiente |
| Curación entre combates | ✅ | `CURACION_ENTRE_COMBATES`, una constante con nombre. El arrastre puro deja al jugador sin vida en el tercer jefe, y nadie ha jugado esto lo bastante para calibrar otra cosa |
| Puntuación | ✅ | AUD-261. `acreditar_combate()` la aplica: premia ir rápido y castiga cada golpe recibido |
| Recuento de golpes | ✅ | AUD-261. `record_hit()` la llama el manejador de `PLAYER_DAMAGED`, sólo con el modo activo |
| Superposición de interfaz | ❌ | rótulos de jefe, marcador en pantalla, pantallas intermedias. Es lo único que queda |

`context.boss_rush` lo **lee** `StageScene`, que es la única que sabe cuándo
empieza un combate, cuándo el jugador recibe un golpe y cuándo cae el jefe.

**GAP-030 queda cerrado.** La tabla anterior marcaba en ❌ las tres filas que la
versión de antes daba por «✅ Complete», y `tests/test_modos_que_no_se_veian.py`
estaba escrito para **fallar el día que alguien las conectara**. Falló, y por
eso esta tabla está actualizada: la prueba hizo imposible cerrar el hueco sin
tocar el documento.


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
