---
document_id: "LOI-DIALOGUE-040"
title: "Legacy of InFest — Dialogue System Specification"
aliases: ["Dialogue System"]
tags: ["dialogue", "system", "ui"]
description: "Branching dialogue with portraits"
source: "docs/40_DIALOGUE_SYSTEM.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Dialogue System Specification

**Document ID:** LOI-DIALOGUE-040
**Version:** 1.0.0
**Status:** Official
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

The Dialogue System provides branching dialogue trees with speaker portraits, name labels, and choice-based progression. It supports multiple NPCs, scriptable actions (item grants, flag setting), and is professor-owned (`src/framework/ui/dialogue_system.py`). Students do not modify the dialogue system but may trigger dialogue trees through the EventBus.

---

## 2. Architecture

### 2.1 DialogueNode
Each node contains:
- `node_id` — unique identifier
- `speaker` — display name
- `text` — dialogue text (revealed character-by-character)
- `portrait` — optional 48×48 portrait filename from `assets/sprites/portraits/`
- `choices` — optional list of `(display_text, next_node_id)` tuples
- `on_enter` / `on_exit` — script action strings

### 2.2 DialogueTree
A collection of nodes with a `start_node` entry point. Multiple trees can coexist; the system loads one at a time.

### 2.3 DialogueSystem
Manages active state, text progress animation (30 chars/sec default), choice selection with MOVE_UP/MOVE_DOWN, and CONFIRM/CANCEL advancement.

### 2.4 Script Actions
Format: `action:argument`
- `give_item:item_id` — emits `ITEM_COLLECTED`
- `set_flag:flag_name` — emits `FLAG_SET`

---

## 3. Visual Layout

Dialogue box: 20px inset from screen edges, 100px tall, anchored at bottom (screen height − 110). Black background at 200 alpha. Portrait rendered at (30, box_y + 10) at 48×48; speaker name at X+56 in gold (#FFDC96); text in light gray (#DCDCDC) below name. Choices rendered at box_y + 60 with yellow highlight on selection. Continue hint "[ENTER]" shown on leaf nodes.

---

## 4. Controls

| Action | Effect |
|--------|--------|
| MOVE_DOWN | Next choice |
| MOVE_UP | Previous choice |
| CONFIRM | Select choice / advance non-branching node |
| CANCEL | End dialogue on non-branching node |

---

## 5. Implementation Status

**File:** `src/framework/ui/dialogue_system.py` (175 lines)
**Status:** ✅ Complete — functional branching dialogue with portraits
**Missing:** No dedicated scene/renderer outside the system class; dialogue is drawn inline by the hosting scene.


--- Traducción al Español ---

## Sistema de Diálogo

### Descripción
Sistema de diálogo ramificado con retratos para conversaciones dentro del juego.

### Características
- Diálogo con ramificaciones (opciones múltiples)
- Retratos de personajes
- Texto con efecto máquina de escribir
- Avance automático o manual

Para la especificación completa de la API con ejemplos de código, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[42_CUTSCENE_SYSTEM.md|Cutscene System]]
- [[09_HUD_SPEC.md|HUD Specification]]
