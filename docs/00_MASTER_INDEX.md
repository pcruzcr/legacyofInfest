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

**Fecha:** 13 de agosto de 2026 · **Documentos:** 70 en `docs/` (69 indexados abajo + este índice), más 5 ficheros de la raíz
(`README`, `CLAUDE`, `CONTRIBUTING`, `CHANGELOG` y `KNOWN_GAPS`), que también tienen fila.

> **AUD-455 (2026-08-13).** Decía «4 ficheros» y nombraba cinco — la tabla
> «Fuera de `docs/`» de abajo también tiene cinco filas. Recontado por lectura
> directa de esta misma tabla.

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
ficheros y hoy son 70 (el encabezado de arriba los cuenta). Se retiraron 35:
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
| [`82_ENVIRONMENT_SETUP_GUIDE.md`](82_ENVIRONMENT_SETUP_GUIDE.md) | Guía de instalación del entorno |
| [`10_LIBRARIES_AND_DEPENDENCIES.md`](10_LIBRARIES_AND_DEPENDENCIES.md) | Librerías y dependencias |

## Referencia del motor

| Documento | Qué contiene |
|---|---|
| [`03_ARCHITECTURE.md`](03_ARCHITECTURE.md) | Arquitectura del motor |
| [`22_API_CONTRACTS.md`](22_API_CONTRACTS.md) | Contratos de API |
| [`23_DATA_SCHEMAS.md`](23_DATA_SCHEMAS.md) | Esquemas de datos |
| [`52_EVENT_MAP.md`](52_EVENT_MAP.md) | Mapa de eventos del EventBus |
| [`74_TUBERIA_DE_GPU.md`](74_TUBERIA_DE_GPU.md) | La tubería de GPU |
| [`75_BIBLIA_TECNICA.md`](75_BIBLIA_TECNICA.md) | Biblia Técnica de Legacy of InFest |

## Especificaciones de dominio

| Documento | Qué contiene |
|---|---|
| [`04_PLAYER_SPEC.md`](04_PLAYER_SPEC.md) | Especificación del jugador |
| [`05_ENEMY_SPEC.md`](05_ENEMY_SPEC.md) | Especificación de enemigos |
| [`17_BOSS_SPEC.md`](17_BOSS_SPEC.md) | Catálogo de diseño de los 4 jefes — 20 de 47 patrones implementados; **no es un contrato** (AUD-369) |
| [`09_HUD_SPEC.md`](09_HUD_SPEC.md) | Especificación del HUD |
| [`18_ENEMY_ROSTER.md`](18_ENEMY_ROSTER.md) | Elenco de enemigos |
| [`06_TMX_SPEC.md`](06_TMX_SPEC.md) | Especificación TMX |

## Sistemas del juego

| Documento | Qué contiene |
|---|---|
| [`40_DIALOGUE_SYSTEM.md`](40_DIALOGUE_SYSTEM.md) | Especificación del sistema de diálogo |
| [`41_BESTIARY_CODEX.md`](41_BESTIARY_CODEX.md) | Especificación del bestiario / códice |
| [`42_CUTSCENE_SYSTEM.md`](42_CUTSCENE_SYSTEM.md) | Especificación del sistema de escenas cinemáticas |
| [`43_SPEEDRUN_MODE.md`](43_SPEEDRUN_MODE.md) | Especificación del modo speedrun |
| [`44_BOSS_RUSH_MODE.md`](44_BOSS_RUSH_MODE.md) | Especificación del modo boss rush |
| [`45_SWIMMING_SPEC.md`](45_SWIMMING_SPEC.md) | Especificación de la mecánica de natación |
| [`46_FOG_OF_WAR.md`](46_FOG_OF_WAR.md) | Especificación de la niebla de guerra |
| [`47_WATER_EFFECT.md`](47_WATER_EFFECT.md) | Especificación del efecto de agua |
| [`48_SCREEN_TRANSITIONS.md`](48_SCREEN_TRANSITIONS.md) | Especificación de transiciones de pantalla |
| [`49_AMBIENT_AUDIO.md`](49_AMBIENT_AUDIO.md) | Especificación de audio ambiental |

## Guías de creación

| Documento | Qué contiene |
|---|---|
| [`60_GUIA_COMPLETA_DEL_MOTOR.md`](60_GUIA_COMPLETA_DEL_MOTOR.md) | Guía completa del motor — todo lo que se puede poner en un nivel |
| [`STAGE_CREATION.md`](STAGE_CREATION.md) | Guía de creación de escenarios |
| [`ENEMY_CREATION.md`](ENEMY_CREATION.md) | Guía de creación de enemigos |
| [`BOSS_CREATION.md`](BOSS_CREATION.md) | Guía de creación de jefes |
| [`SCENE_CREATION.md`](SCENE_CREATION.md) | Guía de creación de escenas |
| [`66_GUIA_DE_LEVEL_DESIGN.md`](66_GUIA_DE_LEVEL_DESIGN.md) | Guía de diseño de niveles |
| [`90_INVENTARIO_DE_LEVEL_DESIGN.md`](90_INVENTARIO_DE_LEVEL_DESIGN.md) | Inventario de diseño de niveles — todo lo que el motor ofrece, por categoría, y qué usar en cada nivel |
| [`73_CATALOGO_DE_RECURSOS_PARA_ESTUDIANTES.md`](73_CATALOGO_DE_RECURSOS_PARA_ESTUDIANTES.md) | Catálogo de recursos para construir niveles y juegos |
| [`26_STUDENT_TEMPLATE_SPEC.md`](26_STUDENT_TEMPLATE_SPEC.md) | Especificación de la plantilla de estudiante |
| [`20_ASSET_BIBLE.md`](20_ASSET_BIBLE.md) | Biblia de recursos gráficos |

## Framework de procesamiento (Unidades VII–IX)

| Documento | Qué contiene |
|---|---|
| [`11_FILTER_TOOLS_SPEC.md`](11_FILTER_TOOLS_SPEC.md) | Especificación de herramientas de filtrado |
| [`12_VISION_TOOLS_SPEC.md`](12_VISION_TOOLS_SPEC.md) | Especificación de herramientas de visión |
| [`13_PATTERN_RECOGNITION_SPEC.md`](13_PATTERN_RECOGNITION_SPEC.md) | Especificación de reconocimiento de patrones |
| [`15_ACADEMIC_DEMO_SCENES.md`](15_ACADEMIC_DEMO_SCENES.md) | Escenas de demostración académica |

## Curso: profesor y ayudante

| Documento | Qué contiene |
|---|---|
| [`78_SAMPLE_SYLLABUS.md`](78_SAMPLE_SYLLABUS.md) | Programa de muestra — Legacy of InFest: Prácticas de Desarrollo de Videojuegos |
| [`08_SYLLABUS_MAPPING.md`](08_SYLLABUS_MAPPING.md) | Correspondencia del programa con el curso |
| [`21_COURSE_SCHEDULE.md`](21_COURSE_SCHEDULE.md) | Calendario del curso |
| [`27_ACADEMIC_RUBRICS.md`](27_ACADEMIC_RUBRICS.md) | Rúbricas académicas |
| [`14_PROFESSOR_DELIVERABLE_MATRIX.md`](14_PROFESSOR_DELIVERABLE_MATRIX.md) | Matriz de entregables del profesor |
| [`79_TA_GUIDE.md`](79_TA_GUIDE.md) | Guía del ayudante — Legacy of InFest |
| [`34_CLASS_MATERIALS.md`](34_CLASS_MATERIALS.md) | Material de clase — diapositivas y guiones de programación en vivo |

## Curso: estudiante

| Documento | Qué contiene |
|---|---|
| [`36_STUDENT_MANUAL.md`](36_STUDENT_MANUAL.md) | Manual de Estudiante |
| [`35_USER_MANUAL.md`](35_USER_MANUAL.md) | Manual de Usuario |
| [`37_DEMO_QUICK_GUIDE.md`](37_DEMO_QUICK_GUIDE.md) | Guía Rápida de Demos Académicas |
| [`38_STAGE_BOSS_GUIDE.md`](38_STAGE_BOSS_GUIDE.md) | Guía Rápida de Creación de Stages y Bosses |
| [`30_ASSIGNMENT_01_STAGE_DESIGN.md`](30_ASSIGNMENT_01_STAGE_DESIGN.md) | Tarea 1: diseño de escenario (TMX) |
| [`31_ASSIGNMENT_02_BOSS_DESIGN.md`](31_ASSIGNMENT_02_BOSS_DESIGN.md) | Tarea 2: diseño de jefe (Python) |
| [`32_ASSIGNMENT_03_LAB_EXERCISES.md`](32_ASSIGNMENT_03_LAB_EXERCISES.md) | Tarea 3: finalización de ejercicios de laboratorio |
| [`33_ASSIGNMENT_04_FINAL_PROJECT.md`](33_ASSIGNMENT_04_FINAL_PROJECT.md) | Tarea 4: proyecto final — zona completa |

## Diseño, mundo y lore

| Documento | Qué contiene |
|---|---|
| [`64_GAME_DESIGN_DOCUMENT.md`](64_GAME_DESIGN_DOCUMENT.md) | Documento de diseño del juego |
| [`16_WORLD_DESIGN.md`](16_WORLD_DESIGN.md) | Documento de diseño del mundo |
| [`07_STAGE0_DESIGN.md`](07_STAGE0_DESIGN.md) | Diseño del Escenario 0 |
| [`86_ESPECIFICACION_DE_NIVELES_Y_JEFES.md`](86_ESPECIFICACION_DE_NIVELES_Y_JEFES.md) | Especificación de Niveles y Jefes |
| [`19_NARRATIVE_AND_LORE.md`](19_NARRATIVE_AND_LORE.md) | Narrativa y trasfondo |
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
| [`89_AUDITORIA_MULTIDISCIPLINAR.md`](89_AUDITORIA_MULTIDISCIPLINAR.md) | Auditoría multidisciplinar agosto 2026 — 16 disciplinas, AUD-310 a AUD-322 |
| [`91_PLAN_DE_CIERRE.md`](91_PLAN_DE_CIERRE.md) | Plan de cierre — inventario medido de todo lo abierto (gaps, avisos, huecos) y los ocho lotes que lo cierran; `WorldSimulation` es el último rasgo |
| [`92_CATALOGO_DE_FENOMENOS.md`](92_CATALOGO_DE_FENOMENOS.md) | Catálogo de fenómenos ambientales — los ~90 de la taxonomía contra lo que cuesta cada uno de verdad, y los cinco que no valen la pena |

---

## Fuera de `docs/`

| Fichero | Qué contiene |
|---|---|
| [`../README.md`](../README.md) | La puerta de entrada del repositorio |
| [`../CLAUDE.md`](../CLAUDE.md) | Las reglas permanentes del repositorio: invariantes, comandos reales y convenciones |
| [`../KNOWN_GAPS.md`](../KNOWN_GAPS.md) | Huecos conocidos y su resolución. No se borra nunca una entrada: se tacha |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Cómo contribuir: ramas, mensajes de commit, qué pasa CI |
| [`../CHANGELOG.md`](../CHANGELOG.md) | Historial de versiones |
| `labs/`, `quizzes/`, `rubricas/`, `exam_bank/`, `eval_practica/` | Material de clase: 3 laboratorios, 4 cuestionarios, rúbricas y banco de exámenes |
| `niveles/`, `entregables/`, `lore/` | Diseños de nivel, entregables del curso y material de trasfondo |
