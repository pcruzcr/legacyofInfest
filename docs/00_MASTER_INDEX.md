---
document_id: "LOI-INDEX-000"
title: "Legacy of InFest — Índice maestro de documentación"
aliases: ["Master Index", "Índice maestro"]
tags: ["index", "entry-point"]
description: "Lista autoritativa de la documentación, agrupada por para qué sirve"
source: "docs/00_MASTER_INDEX.md"
date_processed: "2026-08-06"
---

# Índice maestro de documentación

**Fecha:** 9 de agosto de 2026 · **Documentos:** 71 en `docs/` (70 indexados abajo + este índice), más 5 ficheros de la raíz
(`README`, `CLAUDE`, `CONTRIBUTING`, `CHANGELOG` y `KNOWN_GAPS`), que también tienen fila.

> **AUD-365.** Este encabezado decía 69 y la tabla tenía 75 filas: el hallazgo P3 de `docs/89`. No era una fila de más ni un documento de menos — eran **dos formas distintas de contar** sin decir cuál se usaba. Ahora el número se comprueba: `tests/test_el_indice_maestro_cuenta_bien.py` lo recuenta contra el sistema de ficheros en cada suite, que es lo que la invariante 6 de `CLAUDE.md` exige de cualquier cifra escrita en un documento.

Ésta es la **lista autoritativa**: si un documento no aparece aquí, está mal
puesto. Está agrupada por *para qué sirve*, no por el orden en que se
escribieron, porque la pregunta que trae a alguien aquí es «dónde miro para
hacer X».

> **¿Primera vez?** Empieza por
> [`88_QUE_PUEDE_HACER_CADA_ROL.md`](88_QUE_PUEDE_HACER_CADA_ROL.md): dice qué
> es el proyecto y qué puede hacer con él un profesor, un estudiante, un
> programador, un diseñador de juego y un diseñador de niveles, con los
> comandos de cada uno.

**Qué pasó con los documentos que no están.** Esta documentación tenía 102
ficheros y hoy son 71 (el encabezado de arriba los cuenta). Se retiraron 35:
auditorías cerradas, informes
de fase, hojas de ruta cumplidas y registros de decisiones ya tomadas. No eran
documentación técnica y ninguno describía el motor de hoy — varios citaban
pruebas y símbolos que hace tiempo que no existen. Siguen en el historial de
git si hace falta consultarlos.

---

## Empieza aquí

| Documento | Qué contiene |
|---|---|
| [`88_QUE_PUEDE_HACER_CADA_ROL.md`](88_QUE_PUEDE_HACER_CADA_ROL.md) | Qué es este proyecto y qué puede hacer cada quien con él |
| [`82_ENVIRONMENT_SETUP_GUIDE.md`](82_ENVIRONMENT_SETUP_GUIDE.md) | Environment Setup Guide |
| [`10_LIBRARIES_AND_DEPENDENCIES.md`](10_LIBRARIES_AND_DEPENDENCIES.md) | Libraries and Dependencies |

## Referencia del motor

| Documento | Qué contiene |
|---|---|
| [`03_ARCHITECTURE.md`](03_ARCHITECTURE.md) | Architecture |
| [`22_API_CONTRACTS.md`](22_API_CONTRACTS.md) | API Contracts |
| [`23_DATA_SCHEMAS.md`](23_DATA_SCHEMAS.md) | Data Schemas |
| [`52_EVENT_MAP.md`](52_EVENT_MAP.md) | EventBus Event Map |
| [`74_TUBERIA_DE_GPU.md`](74_TUBERIA_DE_GPU.md) | La tubería de GPU |
| [`75_BIBLIA_TECNICA.md`](75_BIBLIA_TECNICA.md) | Biblia Técnica de Legacy of InFest |

## Especificaciones de dominio

| Documento | Qué contiene |
|---|---|
| [`04_PLAYER_SPEC.md`](04_PLAYER_SPEC.md) | Player Specification |
| [`05_ENEMY_SPEC.md`](05_ENEMY_SPEC.md) | Enemy Specification |
| [`17_BOSS_SPEC.md`](17_BOSS_SPEC.md) | Catálogo de diseño de los 4 jefes — 20 de 47 patrones implementados; **no es un contrato** (AUD-369) |
| [`09_HUD_SPEC.md`](09_HUD_SPEC.md) | HUD Specification |
| [`18_ENEMY_ROSTER.md`](18_ENEMY_ROSTER.md) | Enemy Roster |
| [`06_TMX_SPEC.md`](06_TMX_SPEC.md) | TMX Specification |

## Sistemas del juego

| Documento | Qué contiene |
|---|---|
| [`40_DIALOGUE_SYSTEM.md`](40_DIALOGUE_SYSTEM.md) | Dialogue System Specification |
| [`41_BESTIARY_CODEX.md`](41_BESTIARY_CODEX.md) | Bestiary / Codex Specification |
| [`42_CUTSCENE_SYSTEM.md`](42_CUTSCENE_SYSTEM.md) | Cutscene System Specification |
| [`43_SPEEDRUN_MODE.md`](43_SPEEDRUN_MODE.md) | Speedrun Mode Specification |
| [`44_BOSS_RUSH_MODE.md`](44_BOSS_RUSH_MODE.md) | Boss Rush Mode Specification |
| [`45_SWIMMING_SPEC.md`](45_SWIMMING_SPEC.md) | Swimming Mechanics Specification |
| [`46_FOG_OF_WAR.md`](46_FOG_OF_WAR.md) | Fog of War Specification |
| [`47_WATER_EFFECT.md`](47_WATER_EFFECT.md) | Water Effect Specification |
| [`48_SCREEN_TRANSITIONS.md`](48_SCREEN_TRANSITIONS.md) | Screen Transitions Specification |
| [`49_AMBIENT_AUDIO.md`](49_AMBIENT_AUDIO.md) | Ambient Audio Specification |

## Guías de creación

| Documento | Qué contiene |
|---|---|
| [`60_GUIA_COMPLETA_DEL_MOTOR.md`](60_GUIA_COMPLETA_DEL_MOTOR.md) | Guía completa del motor — todo lo que se puede poner en un nivel |
| [`STAGE_CREATION.md`](STAGE_CREATION.md) | Stage Creation Guide |
| [`ENEMY_CREATION.md`](ENEMY_CREATION.md) | Enemy Creation Guide |
| [`BOSS_CREATION.md`](BOSS_CREATION.md) | Boss Creation Guide |
| [`SCENE_CREATION.md`](SCENE_CREATION.md) | Scene Creation Guide |
| [`66_GUIA_DE_LEVEL_DESIGN.md`](66_GUIA_DE_LEVEL_DESIGN.md) | Guía de Level Design |
| [`90_INVENTARIO_DE_LEVEL_DESIGN.md`](90_INVENTARIO_DE_LEVEL_DESIGN.md) | Inventario de Level Design — todo lo que el motor ofrece, por categoría, y qué usar en cada nivel |
| [`73_CATALOGO_DE_RECURSOS_PARA_ESTUDIANTES.md`](73_CATALOGO_DE_RECURSOS_PARA_ESTUDIANTES.md) | Catálogo de recursos para construir niveles y juegos |
| [`26_STUDENT_TEMPLATE_SPEC.md`](26_STUDENT_TEMPLATE_SPEC.md) | Student Template Specification |
| [`20_ASSET_BIBLE.md`](20_ASSET_BIBLE.md) | Asset Bible |

## Framework de procesamiento (Unidades VII–IX)

| Documento | Qué contiene |
|---|---|
| [`11_FILTER_TOOLS_SPEC.md`](11_FILTER_TOOLS_SPEC.md) | Filter Tools Specification |
| [`12_VISION_TOOLS_SPEC.md`](12_VISION_TOOLS_SPEC.md) | Vision Tools Specification |
| [`13_PATTERN_RECOGNITION_SPEC.md`](13_PATTERN_RECOGNITION_SPEC.md) | Pattern Recognition Specification |
| [`15_ACADEMIC_DEMO_SCENES.md`](15_ACADEMIC_DEMO_SCENES.md) | Academic Demo Scenes |

## Curso: profesor y ayudante

| Documento | Qué contiene |
|---|---|
| [`78_SAMPLE_SYLLABUS.md`](78_SAMPLE_SYLLABUS.md) | Sample Syllabus — Legacy of InFest: Game Development Practicum |
| [`08_SYLLABUS_MAPPING.md`](08_SYLLABUS_MAPPING.md) | Syllabus Mapping |
| [`21_COURSE_SCHEDULE.md`](21_COURSE_SCHEDULE.md) | Course Schedule |
| [`27_ACADEMIC_RUBRICS.md`](27_ACADEMIC_RUBRICS.md) | Academic Rubrics |
| [`14_PROFESSOR_DELIVERABLE_MATRIX.md`](14_PROFESSOR_DELIVERABLE_MATRIX.md) | Professor Deliverable Matrix |
| [`79_TA_GUIDE.md`](79_TA_GUIDE.md) | TA Guide — Legacy of InFest |
| [`34_CLASS_MATERIALS.md`](34_CLASS_MATERIALS.md) | Class Materials — Lecture Slides & Live Coding Scripts |

## Curso: estudiante

| Documento | Qué contiene |
|---|---|
| [`36_STUDENT_MANUAL.md`](36_STUDENT_MANUAL.md) | Manual de Estudiante |
| [`35_USER_MANUAL.md`](35_USER_MANUAL.md) | Manual de Usuario |
| [`37_DEMO_QUICK_GUIDE.md`](37_DEMO_QUICK_GUIDE.md) | Guía Rápida de Demos Académicas |
| [`38_STAGE_BOSS_GUIDE.md`](38_STAGE_BOSS_GUIDE.md) | Guía Rápida de Creación de Stages y Bosses |
| [`30_ASSIGNMENT_01_STAGE_DESIGN.md`](30_ASSIGNMENT_01_STAGE_DESIGN.md) | Assignment 1: Stage Design (TMX) |
| [`31_ASSIGNMENT_02_BOSS_DESIGN.md`](31_ASSIGNMENT_02_BOSS_DESIGN.md) | Assignment 2: Boss Design (Python) |
| [`32_ASSIGNMENT_03_LAB_EXERCISES.md`](32_ASSIGNMENT_03_LAB_EXERCISES.md) | Assignment 3: Lab Exercise Completion |
| [`33_ASSIGNMENT_04_FINAL_PROJECT.md`](33_ASSIGNMENT_04_FINAL_PROJECT.md) | Assignment 4: Final Project — Complete Zone |

## Diseño, mundo y lore

| Documento | Qué contiene |
|---|---|
| [`64_GAME_DESIGN_DOCUMENT.md`](64_GAME_DESIGN_DOCUMENT.md) | Game Design Document |
| [`16_WORLD_DESIGN.md`](16_WORLD_DESIGN.md) | World Design Document |
| [`07_STAGE0_DESIGN.md`](07_STAGE0_DESIGN.md) | Diseño del Escenario 0 |
| [`86_ESPECIFICACION_DE_NIVELES_Y_JEFES.md`](86_ESPECIFICACION_DE_NIVELES_Y_JEFES.md) | Especificación de Niveles y Jefes |
| [`19_NARRATIVE_AND_LORE.md`](19_NARRATIVE_AND_LORE.md) | Narrative and Lore |
| [`65_EL_LORE_EXTENSO.md`](65_EL_LORE_EXTENSO.md) | El Lore Extenso |

## Estado del proyecto y auditoría

| Documento | Qué contiene |
|---|---|
| [`62_ESTADO_DEL_PROYECTO.md`](62_ESTADO_DEL_PROYECTO.md) | Estado del proyecto — qué hay, qué mejorar, qué falta |
| [`63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md`](63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md) | Registro de lo prometido y no implementado |
| [`87_REPORTE_DE_LO_QUE_FALTA.md`](87_REPORTE_DE_LO_QUE_FALTA.md) | Reporte de lo que falta por completar |
| [`69_PROMPT_AUDITORIA_MAESTRO.md`](69_PROMPT_AUDITORIA_MAESTRO.md) | Prompt maestro de auditoría |
| [`70_INFORME_DE_AUDITORIA_VIVO.md`](70_INFORME_DE_AUDITORIA_VIVO.md) | Informe de auditoría vivo — datos medidos por iteración (AUD-305: restaurado; el §7 del prompt 69 lo exige) |
| [`AUDIT_2026-07.es.md`](AUDIT_2026-07.es.md) | Auditoría Multidisciplinaria de Producción |
| [`AUDIT_2026-07.en.md`](AUDIT_2026-07.en.md) | Multidisciplinary Production Audit |
| [`89_AUDITORIA_MULTIDISCIPLINAR.md`](89_AUDITORIA_MULTIDISCIPLINAR.md) | Auditoría multidisciplinar agosto 2026 — 16 disciplinas, AUD-310 a AUD-322 |
| [`91_PLAN_DE_CIERRE.md`](91_PLAN_DE_CIERRE.md) | Plan de cierre — inventario medido de todo lo abierto (gaps, avisos, huecos) y los ocho lotes que lo cierran; `WorldSimulation` es el último rasgo |
| [`92_CATALOGO_DE_FENOMENOS.md`](92_CATALOGO_DE_FENOMENOS.md) | Catálogo de fenómenos ambientales — los ~90 de la taxonomía contra lo que cuesta cada uno de verdad, y los cinco que no valen la pena |

---

## Fuera de `docs/`

| Fichero | Qué contiene |
|---|---|
| [`../README.md`](../README.md) / [`../README.en.md`](../README.en.md) | La puerta de entrada del repositorio, en los dos idiomas |
| [`../CLAUDE.md`](../CLAUDE.md) | Las reglas permanentes del repositorio: invariantes, comandos reales y convenciones |
| [`../KNOWN_GAPS.md`](../KNOWN_GAPS.md) | Huecos conocidos y su resolución. No se borra nunca una entrada: se tacha |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Cómo contribuir: ramas, mensajes de commit, qué pasa CI |
| [`../CHANGELOG.md`](../CHANGELOG.md) | Historial de versiones |
| `labs/`, `quizzes/`, `rubricas/`, `exam_bank/`, `eval_practica/` | Material de clase: 3 laboratorios, 4 cuestionarios, rúbricas y banco de exámenes |
| `niveles/`, `entregables/`, `lore/` | Diseños de nivel, entregables del curso y material de trasfondo |
