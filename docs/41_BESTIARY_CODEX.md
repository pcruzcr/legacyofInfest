---
document_id: "LOI-BESTIARY-041"
title: "Legacy of InFest — Bestiary / Codex Specification"
aliases: ["Bestiary Codex"]
tags: ["bestiary", "codex", "enemy"]
description: "Enemy tracking system"
source: "docs/41_BESTIARY_CODEX.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Bestiary / Codex Specification

**Document ID:** LOI-BESTIARY-041
**Version:** 1.0.0
**Status:** Official
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

The Bestiary (Codex) tracks enemy encounters, kills, and lore. It is a singleton data store (`src/framework/entities/bestiary.py`) holding static definitions and runtime state for all 9 enemy types (8 concrete + 1 boss). Students can read bestiary data to display in their stages but must not modify the singleton.

---

## 2. Architecture

### 2.1 BestiaryEntry
Per-enemy data:
- `enemy_id`, `name`, `description`, `lore` — static spec
- `hp`, `damage`, `drops` — gameplay stats
- `encountered`, `kills`, `times_hit_by_player` — runtime tracking

### 2.2 Bestiary (Singleton)
- `get_instance()` — global accessor
- `record_encounter(enemy_id)` — marks as seen
- `record_kill(enemy_id)` — increments kills, marks as seen
- `record_hit(enemy_id)` — tracks damage dealt
- `save(path)` / `load(path)` — JSON persistence to `saves/bestiary.json`

---

## 3. Default Entries

| ID | Name | HP | Damage |
|----|------|----|--------|
| walker | Walker | 2 | 0.5 |
| flying | Flying Eye | 1 | 0.5 |
| shooter | Shooter | 2 | 1.0 |
| charger | Charger | 3 | 1.5 |
| archer | Archer | 2 | 1.0 |
| brute | Brute | 5 | 2.0 |
| caster | Caster | 3 | 1.5 |
| assassin | Assassin | 2 | 2.0 |
| boss_venado | Venado | 12 | 2.0 |

---

## 4. UI Display

No dedicated bestiary scene exists yet. The singleton stores data; a future `BestiaryScene` should display entries as a scrollable catalog with encounter/kill counters and lore text.

---

## 5. Implementation Status

**File:** `src/framework/entities/bestiary.py` (123 lines)
**Status:** ✅ Complete — data model, singleton, JSON persistence
**Missing:** No `bestiary_scene.py` — UI viewer class not implemented


--- Traducción al Español ---

## Bestiario / Códex

### Descripción
Sistema de seguimiento de enemigos que registra encuentros y derrotas.

### Características
- Catálogo de enemigos encontrados
- Estadísticas de derrotas
- Información de cada tipo de enemigo
- Desbloqueo progresivo

Para la especificación completa, consultar el documento original en inglés.
