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

**Fecha:** 2 de septiembre de 2026 · **Documentos:** 141 en `docs/` (140 indexados abajo + este índice + 0 de informe no indexados — todos indexados), más 5 ficheros de la raíz
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
ficheros y hoy son 149 (el encabezado de arriba los cuenta). Se retiraron 35
auditorías cerradas, informes de fase, hojas de ruta cumplidas y registros de
decisiones ya tomadas, y se incorporaron 63 —incluyendo AUD-800 (8),
`CHANGE_SAFETY_GUIDE`, `AUD-803_NATIVE_RENDERING_AUDIT`, `AUD-804_VISUAL_TRUTH_RUNTIME_CERTIFICATION` y `AUD-805_LEVEL_COMPOSITION_AUDIT`—. No eran
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
| [`93_AUDITORIA_ESTRATEGICA_Y_FODA.md`](93_AUDITORIA_ESTRATEGICA_Y_FODA.md) | Auditoría estratégica — cinco comparativas (Mario, SotN, Zelda OoT, Super Metroid, Dark Souls), estado validado con los 8 validadores, 8 hallazgos, FODA extenso y dirección estratégica |
| [`94_CIERRE_DE_GAPS_Y_PLAN_POR_FASES.md`](94_CIERRE_DE_GAPS_Y_PLAN_POR_FASES.md) | Cierre de gaps y plan por fases — estado verificado del árbol: qué hallazgo ya está resuelto, qué GAP sigue abierto, qué decisión espera al dueño, y el orden de cierre |
| [`50_IMPROVEMENT_ROADMAP.md`](50_IMPROVEMENT_ROADMAP.md) | Roadmap M1-M8 — hitos verificables con criterios de aceptación medibles (comandos) |
| [`PLAN_PENDIENTE_2026_08_26.md`](PLAN_PENDIENTE_2026_08_26.md) | Plan de trabajo pendiente — 15 tareas en 5 fases (A-E): pre-commit, import-linter, perf gate, scripts verificación, assist mode, playtest bot, docs, gráficos/audio |
| [`NATIVE_RENDER_AUDIT.md`](NATIVE_RENDER_AUDIT.md) | Auditoría de presentación nativa — ventana/drawable/internal/viewport/cámara/HUD/letterbox |
| [`NATIVE_COMPOSITION_AUDIT.md`](NATIVE_COMPOSITION_AUDIT.md) | Auditoría de composición nativa — 20 secciones, invariante 1280/16/80×45 |
| [`VISUAL_COMPOSITION_AUDIT.md`](VISUAL_COMPOSITION_AUDIT.md) | Auditoría visual 25 secciones — AUD-756 composición 1280/16/80×45 |
| [`VISUAL_ASSET_INVENTORY.md`](VISUAL_ASSET_INVENTORY.md) | Inventario visual por espacio WORLD/CAMERA/VIEWPORT/UI/DISPLAY |
| [`VISUAL_SCALE_MATRIX.md`](VISUAL_SCALE_MATRIX.md) | Matriz de escala visual — Element Native px Tiles ref Expected |
| [`LEVEL_VISUAL_MATRIX.md`](LEVEL_VISUAL_MATRIX.md) | Matriz visual de niveles — validación de cada stage (cámara, escala, suelo, parallax, HUD) |
| [`LEVEL_VISUAL_COMPOSITION_MATRIX.md`](LEVEL_VISUAL_COMPOSITION_MATRIX.md) | Matriz visual por nivel 26 — Player/Platforms/Enemies/Boss/Background/Parallax/Foreground/Camera/HUD/Density |
| [`LEVEL_NATIVE_COMPOSITION_AUDIT.md`](LEVEL_NATIVE_COMPOSITION_AUDIT.md) | Auditoría nativa por nivel — 26 levels TMX/camera/tiles/sprites/background/parallax/HUD |
| [`TMX_SPATIAL_AUDIT.md`](TMX_SPATIAL_AUDIT.md) | Auditoría TMX espacial — tile 16, object top-left, 37 TMX |
| [`STAGE_SPATIAL_INTEGRITY_MATRIX.md`](STAGE_SPATIAL_INTEGRITY_MATRIX.md) | Matriz integridad espacial 26 — TMX/World/Camera/Collision/Player/Enemies/Objects/Spawns/Checkpoints/Transitions/Parallax |
| [`STAGE_SPATIAL_INTEGRITY_AUDIT.md`](STAGE_SPATIAL_INTEGRITY_AUDIT.md) | Auditoría integridad espacial 30 secciones — AUD-757 1280/80×45 |
| [`AUD-757_FINDINGS.md`](AUD-757_FINDINGS.md) | Hallazgos AUD-757 — F01-F12 1 PNG fix |
| [`VISUAL_REFERENCE_SHEET.md`](VISUAL_REFERENCE_SHEET.md) | Referencia visual — player 40×64 2.5×4 tiles, bosses, HUD |
| [`LEVEL_VISUAL_QA_MATRIX.md`](LEVEL_VISUAL_QA_MATRIX.md) | Matriz QA visual 26 — Composition/Scale/Contrast/Depth/Navigation/Pixel/Lighting/HUD/FX |
| [`AUD-758_FINDINGS.md`](AUD-758_FINDINGS.md) | Hallazgos AUD-758 — V01-V03 1 ambient_light fix |
| [`PIXEL_PERFECT_VISUAL_QA.md`](PIXEL_PERFECT_VISUAL_QA.md) | Certificación pixel-perfect 23 secciones — 1280×720 16 80×45 |
| [`VISUAL_NATIVE_AUDIT.md`](VISUAL_NATIVE_AUDIT.md) | Auditoría nativa visual — 1280×720 80×45 16 unidades |
| [`RENDER_PIPELINE_AUDIT.md`](RENDER_PIPELINE_AUDIT.md) | Auditoría pipeline render — WORLD→CAMERA→VIEWPORT→DISPLAY 7 VALID |
| [`VISUAL_LEVEL_AUDIT.md`](VISUAL_LEVEL_AUDIT.md) | Auditoría niveles visual — 26 levels composition/camera/background/lighting |
| [`LEVEL_COMPOSITION_MATRIX.md`](LEVEL_COMPOSITION_MATRIX.md) | Matriz composición niveles — Size/Tiles/Objects/Enemies/Checkpoints/Camera/Background |
| [`VISUAL_REGRESSION_BASELINE.md`](VISUAL_REGRESSION_BASELINE.md) | Baseline regresión visual — 13 golden frames 1280×720 |
| [`VISUAL_FINDINGS.md`](VISUAL_FINDINGS.md) | Hallazgos visuales — VF01-VF06 1 V04 5 V10 |
| [`DYNAMIC_VISUAL_QA.md`](DYNAMIC_VISUAL_QA.md) | QA dinámica 23 secciones — 60/120 frames camera/player/parallax/HUD |
| [`DYNAMIC_LEVEL_QA_MATRIX.md`](DYNAMIC_LEVEL_QA_MATRIX.md) | Matriz QA dinámica 26 — Camera/Animation/Parallax/HUD/Transition/FX |
| [`AUD-759_FINDINGS.md`](AUD-759_FINDINGS.md) | Hallazgos AUD-759 — D01-D05 5× D13 intentional |
| [`GAME_STATE_INVENTORY.md`](GAME_STATE_INVENTORY.md) | Inventario estados 21 — Entry/Exit/Parent/Overlay/Input/Render/Persistence |
| [`GAME_STATE_GRAPH.md`](GAME_STATE_GRAPH.md) | Grafo estados 21 transiciones — STATE→EVENT→STATE |
| [`GAME_STATE_INTEGRATION_MATRIX.md`](GAME_STATE_INTEGRATION_MATRIX.md) | Matriz integración 21 — Entry/Operation/Exit/Persistence/Re-entry |
| [`HISTORICAL_BUG_REGRESSION.md`](HISTORICAL_BUG_REGRESSION.md) | Regresión 13 bugs históricos — PASS |
| [`FULL_GAME_INTEGRATION_AUDIT.md`](FULL_GAME_INTEGRATION_AUDIT.md) | Auditoría integración 40 fases — producto completo |
| [`FINAL_VISUAL_ACCEPTANCE_REPORT.md`](FINAL_VISUAL_ACCEPTANCE_REPORT.md) | Reporte aceptación visual final — 26 levels 156 screens 0-10 |
| [`RELEASE_CANDIDATE_CERTIFICATION.md`](RELEASE_CANDIDATE_CERTIFICATION.md) | Certificación RC — 1280×720 80×45 16 26/26 PASS |
| [`RELEASE_CANDIDATE_FREEZE.md`](RELEASE_CANDIDATE_FREEZE.md) | Freeze RC — arquitectura y contenido congelado 1280×720 |
| [`FINAL_QA_STATUS.md`](FINAL_QA_STATUS.md) | Estado QA final — 7 audits PASS 115 tests PASS |
| [`AUD-760_FINDINGS.md`](AUD-760_FINDINGS.md) | Hallazgos AUD-760 — I01-I10 10× I12 |
| [`NATIVE_RENDER_FIXES.md`](NATIVE_RENDER_FIXES.md) | Correcciones de presentación nativa — cada fix con causa, transform old/new, pruebas |
| [`95_GUIA_ENTREGA_3_MADURA.md`](95_GUIA_ENTREGA_3_MADURA.md) | Guía Entrega 3 — versión 1280×720 madura, verificación y checklist |
| [`96_GUIA_IA_DOJO_2_SEMANAS.md`](96_GUIA_IA_DOJO_2_SEMANAS.md) | Dojo IA — plan de 2 semanas con scikit-learn para BehaviorPredictor |
| [`97_ROADMAP_PS4_HD_2D_2_5D.md`](97_ROADMAP_PS4_HD_2D_2_5D.md) | Roadmap PS4 HD 2D/2.5D — de 1280 a 1920 y plan PS4 |
| [`98_DECISIONES_DUENO_2K26.md`](98_DECISIONES_DUENO_2K26.md) | Decisiones del dueño A1,A7,B7,C1,D2,P4,P5 — cierre 100% |
| [`HYBRID_RENDERER_RC_CERTIFICATION.md`](HYBRID_RENDERER_RC_CERTIFICATION.md) | Certificación Hybrid Renderer — 1920 work 9.47 P95 10.50 P99 12.25 readback 0 |
| [`PERFORMANCE_BASELINE.md`](PERFORMANCE_BASELINE.md) | Baseline de rendimiento — 1280×720 work 6.5 y 1920×1080 9.47 comparativa |
| [`RELEASE_NOTES_RENDERER_RC.md`](RELEASE_NOTES_RENDERER_RC.md) | Notas de release Renderer RC — 1920@60 work 9.47 vs CPU 39.54 |
| [`AUD-800_REPOSITORY_INVENTORY.md`](AUD-800_REPOSITORY_INVENTORY.md) | Inventario forense — 8.350 ficheros relevantes, 518 src, 6.556 tests, 854 assets, 37 TMX |
| [`AUD-800_ENEMY_MATRIX.md`](AUD-800_ENEMY_MATRIX.md) | Matriz enemigos 35 — propósito, IA, daño, hitbox, niveles, fairness |
| [`AUD-800_INPUT_MATRIX.md`](AUD-800_INPUT_MATRIX.md) | Matriz entrada 31 acciones — bindings, focus, leakage, accesibilidad |
| [`AUD-800_PACING_MATRIX.md`](AUD-800_PACING_MATRIX.md) | Matriz pacing 26 niveles — introducción, densidad, checkpoint, curva |
| [`AUD-800_CLEANUP_MANIFEST.md`](AUD-800_CLEANUP_MANIFEST.md) | Manifiesto limpieza — 6 temps DELETE, 1 P3 archivable, repo CLEAN |
| [`AUD-800_REGRESSION_MATRIX.md`](AUD-800_REGRESSION_MATRIX.md) | Matriz regresión 15 subsistemas ×2 niveles — renderer→tests |
| [`AUD-800_MASTER_SPECIFICATION.md`](AUD-800_MASTER_SPECIFICATION.md) | Especificación maestra — contrato 1280×720 80×45 16 pipeline nativo |
| [`AUD-800_FINAL_CERTIFICATION.md`](AUD-800_FINAL_CERTIFICATION.md) | Certificación final 88/100 RC — 44 secciones, 0 P0 0 P1 7 P3 |
| [`CHANGE_SAFETY_GUIDE.md`](CHANGE_SAFETY_GUIDE.md) | Guía de seguridad ante cambios — invariante 9, matriz CERT, validador automático |
| [`AUD-803_NATIVE_RENDERING_AUDIT.md`](AUD-803_NATIVE_RENDERING_AUDIT.md) | Auditoría native rendering — pipeline 1280×720, camera, HUD, tilemap, pixel-perfect |
| [`AUD-804_VISUAL_TRUTH_RUNTIME_CERTIFICATION.md`](AUD-804_VISUAL_TRUTH_RUNTIME_CERTIFICATION.md) | Certificación visual truth — falsación adversarial de AUD-803, 1.5× no integer |
| [`AUD-805_LEVEL_COMPOSITION_AUDIT.md`](AUD-805_LEVEL_COMPOSITION_AUDIT.md) | Auditoría composición niveles — 37 TMX, player 40×64, ground 608, HUD 128, parallax |
| [`PROJECT_IMPROVEMENT_REGISTER.md`](PROJECT_IMPROVEMENT_REGISTER.md) | Registro de mejoras del proyecto - 12 mejoras I-001..I-012 priorizadas WHY->COST->RISK |
| [`RELEASE_READINESS.md`](RELEASE_READINESS.md) | Preparación para release - matriz RC 15 áreas, P0=0 P1=0, renderer FROZEN |
| [`B3_ITEM_COMPLETION_CONTRACT_REVIEW.md`](B3_ITEM_COMPLETION_CONTRACT_REVIEW.md) | B3 item completion - revision de contrato CODE+DATA+TEST |
| [`B4_2_HEART_PIECE_CONTRACT_REVIEW.md`](B4_2_HEART_PIECE_CONTRACT_REVIEW.md) | B4.2 heart piece - revision de contrato, modo analisis |
| [`B4_MASTER_CERTIFICATION.md`](B4_MASTER_CERTIFICATION.md) | B4 master certification - bonfire, heart piece, recharge station COMPLETE |

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