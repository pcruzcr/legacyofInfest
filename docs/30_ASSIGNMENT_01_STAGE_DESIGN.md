---
document_id: "LOI-ASGN01-030B"
title: "Entrega 1: diseño de escenario (TMX)"
aliases: ["Entrega 1: diseño de escenario", "Assignment 1: Stage Design"]
tags: ["entrega", "escenario", "diseno", "academico"]
description: "Entrega de diseño de escenario"
source: "docs/30_ASSIGNMENT_01_STAGE_DESIGN.md"
date_processed: "2026-08-13"
---

# Entrega 1: diseño de escenario (TMX)

**Entrega:** Clase 5 | **Instrumento:** Evaluación Práctica I — Prototipo Funcional | **Valor:** 15% de la nota final

> **AUD-455.** Traduce y unifica el documento: tenía un cuerpo en inglés
> con un formato de entrega genérico (semana 4, 100 puntos, capas
> `Terrain`/`Collectibles`/`Checkpoint`, baldosas de 32×32) que
> contradecía al resumen en español del final (Clase 5, Evaluación
> Práctica I, 15%) — y ambos contradecían el estándar real de 8 capas de
> `06_TMX_SPEC.md` y el tamaño de baldosa de 16×16 de `settings.py`. Gana
> el estándar verificado contra el código: las 8 capas reales, baldosa de
> 16×16, y checkpoints como objetos `Checkpoint` en la capa `Objects` (no
> una capa de baldosas propia).

## Objetivo

Diseñar e implementar un escenario de juego jugable usando Tiled y el framework de Legacy of InFest. Se crea un mapa `.tmx` que incluye terreno, enemigos, coleccionables, punto de aparición del jugador, y checkpoints — como Evaluación Práctica I del único Escenario o Jefe asignado (ver `21_COURSE_SCHEDULE.md`, `08_SYLLABUS_MAPPING.md` §12).

## Requisitos del mapa TMX

- Tamaño de baldosa: 16×16 px (`settings.TILE_SIZE`)
- Las **8 capas obligatorias** (ver `06_TMX_SPEC.md` §3): `BG_Far`, `BG_Mid`, `BG_Near`, `Terrain`, `Terrain_Detail`, `Objects`, `Collision`, `FG_Overlay`
- La capa `Objects` debe contener exactamente un objeto `PlayerSpawn`
- La capa `Objects` debe contener 1 o más objetos `Checkpoint` (con `checkpoint_id` correlativo)
- La capa `Collision` lleva los rectángulos `Solid`/`Platform` — nunca peligros ni coleccionables (ver `06_TMX_SPEC.md` sobre por qué `HazardZone` va en `Objects`, no en `Collision`)

### Propiedades personalizadas (en el mapa)

| Propiedad | Tipo | Descripción |
|---|---|---|
| `author` | cadena | Nombre completo del estudiante |
| `zone` | entero | Número de zona |
| `stage_id` | cadena | p. ej. `"1-1"` |
| `stage_name` | cadena | Nombre de presentación del escenario |
| `climate` | cadena | Según la lista válida de `06_TMX_SPEC.md` |
| `schema_version`, `time_limit`, `bgm_track`, `ambient_light` | — | Ver `06_TMX_SPEC.md` §4 para la lista completa de propiedades obligatorias |

### Enemigos

- Colocar enemigos en la capa `Objects`, con el tipo correcto (`Walker`, `Shooter`, `Flying`, `Charger`, o una especie con nombre del bestiario — ver `18_ENEMY_ROSTER.md`)
- Cada objeto de enemigo debe tener la propiedad `type` correspondiente a la clase real

### Coleccionables

- Al menos un objeto coleccionable en la capa `Objects`, con `item_id` fijado (sin `item_id` el cargador lo ignora con un aviso)

## Rúbrica de calificación

Este entregable corresponde al criterio **"Representación de escena/objeto (Unidad IV)"** de la rúbrica completa de la Evaluación Práctica I — ver `27_ACADEMIC_RUBRICS.md` §4 para los 100 puntos completos (coordenadas y vectores, curvas, escena, color, completitud funcional, y calidad de documentación). No se repite aquí para no desincronizarse: la rúbrica autoritativa vive en un solo sitio.

`scripts/grade_stage.py assets/maps/tu_escenario.tmx --json` da la calificación automática de las categorías estructurales y de diseño de nivel (ver `27_ACADEMIC_RUBRICS.md`, Apéndice).

## Entrega

Suba su escenario completo a su repositorio de GitHub Classroom. El script de calificación corre automáticamente vía CI.

```bash
git add assets/maps/tu_escenario.tmx src/stages/tu_escenario/
git commit -m "feat: diseño de escenario completo"
git push
```

Revise su nota en la pestaña de Actions de CI.

---
## 🔗 Documentos relacionados

- [[07_STAGE0_DESIGN.md|Diseño de Stage 0]]
- [[06_TMX_SPEC.md|Especificación de TMX]]
- [[27_ACADEMIC_RUBRICS.md|Rúbricas académicas]]
