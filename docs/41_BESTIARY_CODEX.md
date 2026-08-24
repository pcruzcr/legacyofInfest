---
document_id: "LOI-BESTIARY-041"
title: "Legacy of InFest — Especificación del bestiario / códice"
aliases: ["Especificación del bestiario", "Bestiary Codex"]
tags: ["bestiario", "codice", "enemigos"]
description: "Sistema de seguimiento de enemigos"
source: "docs/41_BESTIARY_CODEX.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación del bestiario / códice

**ID del documento:** LOI-BESTIARY-041
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, estudiantes, asistentes de código

> **AUD-455.** Traduce el documento y corrige varias afirmaciones que
> estaban desactualizadas, no sólo en inglés: decía "9 tipos de enemigo (8
> concretos + 1 jefe)" cuando el bestiario real se construye desde
> `bestiary_registry.SPECIES` — **21 especies** con nombre, repartidas en 3
> zonas (ver `18_ENEMY_ROSTER.md`), sobre 8 arquetipos base; decía que
> `src/framework/entities/bestiary.py` tenía 123 líneas, y hoy tiene 278;
> y decía dos veces que **no existe ninguna escena de bestiario** — sí
> existe, `src/engine/scenes/bestiary_scene.py` (210 líneas, migrada al kit
> de UI compartido en AUD-069), accesible desde el menú con Tab.

---

## 1. Visión general

El bestiario (códice) registra los encuentros, las bajas y el trasfondo de los enemigos. Es un almacén de datos singleton (`src/framework/entities/bestiary.py`) que guarda las definiciones estáticas y el estado en tiempo de ejecución de las 21 especies con nombre (más el jefe de referencia). Los estudiantes pueden leer los datos del bestiario para mostrarlos en sus escenarios, pero no deben modificar el singleton.

---

## 2. Arquitectura

### 2.1 `BestiaryEntry`
Datos por enemigo:
- `enemy_id`, `name`, `description`, `lore` — ficha estática
- `hp`, `damage`, `drops` — estadísticas de juego
- `encountered`, `kills`, `times_hit_by_player` — seguimiento en tiempo de ejecución

### 2.2 `Bestiary` (singleton)
- `get_instance()` — acceso global
- `record_encounter(enemy_id)` — marca como visto
- `record_kill(enemy_id)` — incrementa las bajas, marca como visto
- `record_hit(enemy_id)` — registra el daño infligido
- `save(path)` / `load(path)` — persistencia JSON en `saves/bestiary.json`

Las entradas se construyen automáticamente a partir de
`bestiary_registry.SPECIES` — el bestiario no mantiene su propia tabla de
enemigos por separado; enumerar cada especie aquí se desincronizaría en
cuanto se añadiera una nueva, así que la lista autoritativa es
`18_ENEMY_ROSTER.md` §6 y el propio `bestiary_registry.py`.

---

## 3. Pantalla del bestiario

`BestiaryScene` (`src/engine/scenes/bestiary_scene.py`) muestra las entradas como un catálogo navegable, con el kit de UI compartido (`Theme`, `MenuList`, `draw_screen`, `handle_menu_navigation`) — la misma navegación y paleta que `InventoryScene` y `WorldMapScene`. Se accede con **Tab** desde el menú.

---

## 4. Estado de implementación

**Fichero:** `src/framework/entities/bestiary.py` (278 líneas) + `src/engine/scenes/bestiary_scene.py` (210 líneas)
**Estado:** ✅ Completo — modelo de datos, singleton, persistencia JSON, pantalla de visualización

---
## 🔗 Documentos relacionados

- [[18_ENEMY_ROSTER.md|Elenco de enemigos]]
- [[05_ENEMY_SPEC.md|Especificación de enemigos]]
