---
document_id: "LOI-AUDIT-093"
title: "Auditoría estratégica y FODA — 19 de agosto de 2026"
aliases: ["Auditoría estratégica", "FODA 2026-08", "Comparativas de referencia"]
tags: ["audit", "strategy", "foda", "comparativas"]
description: "Auditoría estratégica derivada de cinco análisis comparativos (Mario, Castlevania SotN, Zelda OoT, Super Metroid, Dark Souls) contra el estado validado del motor: evidencia ejecutada, hallazgos, FODA extenso y dirección estratégica"
source: "docs/93_AUDITORIA_ESTRATEGICA_Y_FODA.md"
date_processed: "2026-08-19"
---

# Auditoría estratégica y FODA — 19 de agosto de 2026

**Fecha:** 19 de agosto de 2026 · **Rama:** `feature/stage4_1-cementerio-sagrado` ·
**Base:** `f8d11a3` (AUD-572)
**Informes hermanos:** [`70_INFORME_DE_AUDITORIA_VIVO.md`](70_INFORME_DE_AUDITORIA_VIVO.md)
(por hallazgo AUD-NNN) · [`89_AUDITORIA_MULTIDISCIPLINAR.md`](89_AUDITORIA_MULTIDISCIPLINAR.md)
(16 disciplinas) · [`91_PLAN_DE_CIERRE.md`](91_PLAN_DE_CIERRE.md)

## 1. Resumen ejecutivo

Esta auditoría no mide disciplinas técnicas (eso es el 89): mide **la dirección
del proyecto**. Se comparó Legacy of InFest contra cinco referencias de diseño
(Super Mario Bros., Castlevania: SotN, Zelda: OoT, Super Metroid y Dark Souls),
se validó el estado real del repositorio con los ocho validadores de CI, y el
resultado se consolida en un FODA extenso (§7), un catálogo de mejoras
priorizadas (§9) y una dirección estratégica (§8).

**El veredicto de la validación:** verde en los ocho validadores — ruff,
dependencias (13 en acuerdo), traducciones, cobertura TMX (propiedades y Light
al 100 %), referencia TMX al día, assets (0 errores / 0 avisos), TMX 22/22,
`grade_boss` Venado 100.0, mypy sin hallazgos en 51 archivos. `grade_stage`
califica 22 mapas (media 73,6/100 incluyendo arenas de jefe y laboratorios;
93,9/100 sin ellos; el escenario de referencia stage0 al 100).

**El veredicto de las comparativas:** la fórmula que define al proyecto —
linealidad docente por zona, tres escenarios + jefe, estética SNES — es la
correcta para su naturaleza. Lo que falta no es otra fórmula: es **riqueza
dentro de la fórmula existente**. Las mejoras de mayor retorno son las baratas y
compatibles (§9): NG+, porcentaje de ítems por escenario, piezas de corazón,
atajos de una vía, fogatas reutilizables, minijuegos, subarmas, finales
condicionales y día/noche jugable.

**Hallazgos nuevos:** 8, todos de severidad P2/P3, ninguno bloqueante (§6).
Los más relevantes: brechas de checkpoint de 2400–2688 px en `stage4_1` y sus
variantes (el máximo recomendado es 500), un falso positivo de `grade_stage`
en arenas de jefe y 689 archivos sin seguimiento en la raíz del repo.

## 2. Alcance y método

- **Qué se auditó:** motor (`src/engine`, `src/framework`), escenarios
  (`src/stages`), mapas (`assets/maps`), documentación viva (`docs/`,
  `KNOWN_GAPS.md`), herramientas de validación (`scripts/`).
- **Cómo:** ejecución real de los validadores de CI (§3) + cinco análisis
  comparativos nivel por nivel contra los juegos de referencia (§4) + lectura
  de los documentos de diseño (64, 16, 66, 17, 86, 90).
- **Criterio de aceptación:** nada se declara arreglado sin evidencia
  ejecutada; una mejora que rompe una entrega o una demo de clase está mal,
  aunque la ingeniería sea buena.
- **Contexto normativo vigente:** la anulación parcial (2026-08-07) de las
  invariantes 1–2 de `CLAUDE.md` — el motor evoluciona libre y el contenido de
  referencia se reconstruirá después (plan en `docs/87_REPORTE_DE_LO_QUE_FALTA.md`
  §27, fila AUD-333). Este documento asume esa anulación vigente y la regla de
  `revisar/` intacta.

## 3. Estado validado — evidencia ejecutada

| Validador | Resultado real | Notas |
|---|---|---|
| `ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/` | **All checks passed!** | — |
| `check_dependency_sync.py` | **OK: 13 dependencies agree** | — |
| `check_translations.py --ci` | **Catálogos en orden** | 71 cadenas de kit, 2937 literales; es: 44, en: 87 |
| `check_tmx_coverage.py --ci` | **Cobertura correcta** | propiedades 100 %, Light 100 %; `BossSpawn` (1 de 71 tipos) sin uso directo, cubierto indirectamente por los 4 tipos de jefe |
| `generate_tmx_reference.py --check` | **al día** | `docs/STAGE_CREATION.md` |
| `validate_assets.py` | **All assets validated successfully. 0 errors, 0 warning(s)** | avisos de libpng por perfil iCCP (hallazgo F1) y nota de `professor_sample.pkl` (F2) |
| `validate_tmx.py --ci` | **22/22 passed with warnings** | advertencia oficial: `stage1_1` registra tipos de enemigo dentro de una función (F7) |
| `grade_boss.py boss_venado` | **100.0 %** | estructura de clase 5/5 (38 métodos); errores 0 |
| `mypy` (trinquete) | **Success: no issues found in 51 source files** | alcance de `mypy_scope.txt` |
| `pytest -q` (suite completa) | **5907 passed, 8 failed, 18 skipped** en 1021 s | detalle en §11 |
| `grade_stage.py assets/maps/ --json` | 22 mapas, media 73,6/100 (93,9/100 sin arenas ni laboratorio) | tabla en §3.1 |

### 3.1 `grade_stage` — 22 mapas calificados

| Mapa | % | Errores | Avisos relevantes |
|---|---|---|---|
| stage0 | 100.0 | — | — |
| stage1_1 | 95.4 | — | 1 plataforma sin ruta |
| stage2_2 | 95.4 | — | 1 plataforma sin ruta |
| stage2_1_oficinas | 90.0 | — | — |
| stage1_2_la_soda | 86.2 | — | — |
| stage1_3_las_aulas | 86.9 | — | repecho 544 px; 640 px entre checkpoints |
| stage_mecanicas | 84.6 | — | resortes/tirolesas (no modeladas); 944 px entre checkpoints; 3 plataformas sin ruta |
| lobby_datacenter | 82.3 | — | — |
| stage3_3_el_patio | 81.5 | — | 2 plataformas sin ruta |
| stage3_1_la_entrada_de_piedra | 80.0 | — | 785 px entre checkpoints |
| stage4_1 | 72.3 | — | **2688 px entre checkpoints** |
| stage4_1b | 72.3 | — | **2400 px entre checkpoints** |
| stage4_1c (×3) | 64.6 | — | resortes/tirolesas; **2451–2528 px entre checkpoints**; 6 plataformas sin ruta por mapa; repechos de 160–208 px |
| hall | 70.0 | sin ruta al NextTrigger | arena: la métrica no aplica (aviso explícito de la herramienta); 747 px entre checkpoints |
| stage3_4_boss_gavilan | 70.8 | sin ruta al NextTrigger | arena: no aplica; 600 px entre checkpoints; 10 plataformas sin ruta |
| boss_venado | 69.2 | sin ruta al NextTrigger | arena: no aplica |
| boss_paburu | 68.5 | sin ruta al NextTrigger | arena: no aplica |
| boss_rey | 61.5 | sin ruta al NextTrigger | arena: no aplica; sin checkpoint |
| stage_cenital | 57.7 | sin ruta al NextTrigger | laboratorio: no aplica; sin checkpoint |

**Lectura:** el contenido transitable nuevo (zona 4) es el más débil en
pacing — la brecha de checkpoints triplica el máximo recomendado —, y las
arenas de jefe generan un falso positivo sistemático de la herramienta (F3).
El resto del catálogo está sano; «ningún salto pone a prueba al jugador» en
varios niveles es un rasgo deliberado de material docente (fórmula 1-1 de
Mario, ver §4.1).

## 4. Comparativas con juegos de referencia

### 4.1 Super Mario Bros. — la fórmula adoptada

Adoptado: estructura 3+1 por zona (tres escenarios + jefe, `STAGE_ORDER` de 16
ranuras en `src/engine/core/stage_registry.py`), escenario 1-1 como lección
docente (stage0), checkpoints más generosos que los de Mario. Descarte
deliberado: vidas, zonas de teletransporte, transformación por power-up. La
linealidad de la fórmula original no es una deuda: es el andamiaje de la
docencia — un estudiante debe poder recorrer el nivel sin explorar.

### 4.2 Castlevania: SotN — lo RPG-lite

Adoptado: inventario equipable con ranuras, bestiario/códice (9 fichas),
niebla de guerra (`46_FOG_OF_WAR.md`), bloques rompibles, guardado por
objeto/HMAC. Descarte incompatible: hub y backtracking entre zonas (chocaría
con la linealidad docente). Oportunidades baratas: subarmas (el arco ya
existe como base), familiares del lore como acompañantes, finales
condicionales (los flags del guardado ya existen), drops de ítems en enemigos.

### 4.3 Zelda: Ocarina of Time — el vocabulario de puzzles

Adoptado: vocabulario local de puzzles (llavero, cerradura, interruptores,
cofres), mundo con nodos en zigzag (`world_map_scene`). No adoptado: día/noche
con consecuencias de juego (el `WorldSimulation` ya emite `EnvironmentState`
con día/noche, fase lunar y clima — falta *usarlo*), piezas de corazón,
acompañante con pistas, minijuegos, atajos de una vía. Oportunidad estrella:
la **Canción del Sol** — un toggle de día/noche como mecánica de nivel, el
caso de uso que el propio `WorldSimulation` espera (los GAP-059…065 del 4-1
piden eventos atados a la oscuridad).

### 4.4 Super Metroid — el candado por habilidad

Adoptado a escala local: candado por habilidad dentro de un escenario (niveles
del 2-1, natación en 4-1b), silencio como técnica (GAP-065), memoria espacial
(GAP-059). Descarte incompatible: exploración global y backtracking
inter-zonas. Oportunidades baratas: **porcentaje de ítems por escenario**
(el candidato perfecto para las tablas de speedrun/boss rush existentes) y
estaciones de recarga reutilizables como objeto TMX (prototipo: la fuente
sanadora del 3-3).

### 4.5 Dark Souls — la profundidad sin castigo

Adoptado: NG+ (base existente en `difficulty.py` y `boss_rush_mode.py`),
atajos de una vía (ya en 2-2), fogata/bonfire como objeto TMX reutilizable,
storytelling ambiental (GAP-065). Descarte explícito y documentado: stamina,
mundo sin mapa, NPCs crípticos y castigo por muerte en la partida estándar —
ninguno sirve a un material docente donde el fracaso debe enseñar, no
entorpecer.

## 5. Inventario de inspiraciones

**23 juegos citados a lo largo de los análisis:** Super Mario Bros. (+3 y
Wonder), Sonic 1/2, Mega Man 2, Zelda clásico y OoT, Metroid, Super Metroid y
Metroid Dread, Castlevania clásicos, Super Castlevania IV y SotN, Donkey Kong
Country, Celeste, Hollow Knight, Ori, Cuphead, Shovel Knight, DuckTales,
Rayman, Dead Cells, Spelunky, Inside, Terraria, Hotline Miami, Metal Gear
Solid, Resident Evil 3, Sekiro, Katana ZERO y Metal Gear Rising.

**Anclas estéticas (no artistas individuales — el crédito es de los
estudiantes):** estética SNES (paletas de ≤16 colores, píxel 1:1, resolución
histórica 320×224 trasladada a 800×600), Studio Ghibli (Espíritu del Bosque de
*La princesa Mononoke*) para el Venado, *Demon's Crest* para el gótico de
huesos, la Medusa de Super Castlevania IV para el Gavilán, y lo precolombino +
cultura Tilawa + ecología costarricense real para Paburu y la zona 4.
Autores: José Jahel Morales Briceño (Venado), Alejandro Josué Rodríguez Zamora
(Paburu), Isaac Felipe Morún Moreira (Gavilán); generadores procedimentales
(`art_lib.py`, `gen_tileset_residencias`, `gen_paburu_art.py`) como autores
técnicos del resto.

## 6. Hallazgos de esta auditoría

Ninguno bloqueante (no hay P0 ni P1). Al implementarse, cada uno tomará su
`AUD-NNN` (el último usado es AUD-572) con su prueba de antes/después.

| ID | Severidad | Hallazgo | Evidencia |
|---|---|---|---|
| F1 | P3 | PNGs con perfil de color sRGB incorrecto (iCCP) | avisos de libpng en `validate_assets` y `grade_stage` |
| F2 | P3 | `assets/models/professor_sample.pkl` se deserializa con `pickle` (el propio script lo advierte: *unpickling executes arbitrary code*) | aviso de `validate_assets` |
| F3 | P2 | `grade_stage` reporta «no hay ruta al NextTrigger» como **error** en las 4 arenas de jefe + hall + `stage_cenital`, que por diseño no llevan NextTrigger; la herramienta avisa que la métrica no aplica pero la cuenta igual | §3.1 |
| F4 | P2 | Brechas de checkpoint de 2400–2688 px en `stage4_1`, `stage4_1b` y las tres variantes de `stage4_1c` (máximo recomendado: 500 px); además 6 plataformas sin ruta por mapa en 4-1c | §3.1 |
| F5 | P2 | `computer-vision-course/` (689 archivos) sin seguimiento en la raíz del repo | `git status` |
| F6 | P3 | Asimetría de catálogos de traducción: es: 44, en: 87 entradas (herencia de la política bilingüe; la decisión del dueño 2026-08-11 deja el español como única lengua y no se sincroniza el catálogo en) | `check_translations --ci` |
| F7 | P3 | `stage1_1` registra tipos de enemigo dentro de una función; el juego funciona, pero el previsualizador y las herramientas muestran enemigos genéricos | aviso oficial de `validate_tmx` |
| F8 | P3 | `BossSpawn` (1 de 71 tipos de objeto) sin uso directo en ningún mapa; cubierto indirectamente por los tipos de jefe | `check_tmx_coverage --ci` |

## 7. FODA extenso

### Fortalezas

1. **Motor educativo completo y probado:** 16 ranuras de `STAGE_ORDER`, 22
   mapas calificados, 4 jefes (Venado 100/100 en rúbrica; Rey y Gavilán con
   fases implementadas; Paburu con sus 4 formas), suite defendida por
   mutación.
2. **Doble naturaleza respetada:** la docencia manda; las invariantes y las
   rúbricas blindan las entregas de estudiantes, y el `grade_stage`/`grade_boss`
   dan nota objetiva a cada nivel.
3. **Validación automatizada real:** ocho validadores en CI, todos verdes en
   esta auditoría; mypy con trinquete explícito; contadores de documentación
   verificados por pruebas (`test_el_indice_maestro_cuenta_bien.py`).
4. **Documentación viva y en español:** 70 documentos de nivel superior
   indexados en `00_MASTER_INDEX.md`, con cifras verificables; `KNOWN_GAPS.md`
   como bitácora honesta de lo pendiente.
5. **Sistemas por delante de su uso:** `WorldSimulation` (día/noche, fase
   lunar sinódica, clima), inventario equipable (`heart_vessel`, consumibles),
   guardado con HMAC, niebla de guerra, bestiario, escenas y diálogos — un
   banco de mecánicas que espera contenido.
6. **Identidad propia:** estética SNES + lore costarricense (Venado, Paburu,
   Tilawa) + 23 referencias de diseño digeridas con criterio; el proyecto no
   imita, adapta.
7. **Rendimiento verificado en la Quadro M2200** con avisos explícitos de
   renderer; la medición GPU es reproducible.

### Debilidades

1. **El contenido más nuevo es el más débil:** la zona 4 (cementerio sagrado)
   tiene el pacing peor medido — checkpoints a 2400–2688 px y plataformas
   aisladas; `grade_stage` la puntúa en la cola (64.6–72.3).
2. **El cierre del juego está abierto:** falta pulir el tramo final
   (4-2 Paburu y el orden de la zona 4); el juego «se termina» pero no
   «se cierra».
3. **Ruido de herramienta:** el falso positivo de `grade_stage` en arenas
   (F3) ensucia los reportes y puede malorientar a un estudiante que califique
   su jefe con la herramienta equivocada.
4. **Higiene del repo:** 689 archivos sin seguimiento en la raíz (F5),
   perfiles iCCP incorrectos (F1), catálogo `en` asimétrico (F6).
5. **Suite lenta:** `pytest -q` completo excede los 10 minutos; CI paga el
   costo en cada push.
6. **Decisiones pendientes de un solo dueño:** los GAP-059…065 (contenido
   del 4-1) y la reversión de la anulación de invariantes 1–2 esperan
   decisión humana; el avance se ralentiza donde no hay delegación posible.

### Oportunidades

1. **Riqueza barata validada:** NG+ (base: `difficulty.py` + boss rush),
   porcentaje de ítems por escenario, piezas de corazón ¼, atajos de una vía,
   fogatas TMX, minijuego de tiro al arco, subarmas, finales condicionales y
   día/noche jugable — todas compatibles con la linealidad docente (§9).
2. **`WorldSimulation` esperando contenido:** la Canción del Sol (toggle
   día/noche) convierte el sistema ambiental en mecánica de nivel; es el caso
   de uso que los GAP-059…065 ya describen.
3. **Contenido de autoría estudiantil:** 26 entregas históricas y los tres
   jefes con crédito son la cantera del contenido de referencia que se
   reconstruirá (plan 87 §27 / AUD-333).
4. **Material de clase empaquetable:** laboratorios, cuestionarios, banco de
   exámenes y rúbricas ya existen; el curso puede publicarse como unidad
   completa.
5. **scikit-learn opcional:** demos de IA (heurística determinista sin
   dependencia dura) — un diferenciador docente que no compromete el runtime.

### Amenazas

1. **Romper entregas o demos:** la anulación de invariantes 1–2 da libertad
   hoy, pero la reconstrucción del contenido de referencia es deuda que
   vence; si la anulación se revierte, la libertad se acaba sin aviso.
2. **La docencia como límite:** mecánicas con castigo (stamina, sin-mapa,
   muerte con penalización) están descartadas por diseño; cualquier propuesta
   que las incluya muere en revisión y no debe planificarse.
3. **CI lento:** una suite de ~20 minutos desanima la iteración y puede
   empujar a «no correr las pruebas», que es exactamente donde este
   repositorio no quiere estar.
4. **Desincronización doc↔código:** el índice y los contadores están
   protegidos por pruebas, pero cada documento nuevo sin fila o cada cifra sin
   verificación reintroduce la deuda que AUD-365 y AUD-455 ya pagaron.
5. **Dependencia del dueño:** decisiones de diseño abiertas (GAPs) y la
   reversión de la anulación concentran el riesgo en una persona; la
   documentación de decisiones en `KNOWN_GAPS.md` es el único amortiguador.

## 8. Dirección estratégica — hacia dónde va el proyecto

**De «motor completo» a «juego terminado y rico por dentro».** La fórmula
lineal docente no cambia — es el contrato con el curso. Lo que cambia es la
profundidad dentro de ella, en este orden:

1. **Cerrar la zona 4** (trabajo activo de la rama actual): terminar el
   cementerio sagrado del 4-1 resolviendo los GAP-059…065, sanear el pacing de
   `4-1b`/`4-1c` (checkpoints ≤ 500 px, plataformas con ruta) y cerrar el juego
   con 4-2 Paburu.
2. **Pagar la deuda de higiene:** F3 (falso positivo del grader en arenas),
   F5 (artefactos sin seguimiento), F1 (iCCP), F4 (checkpoints) — lotes
   pequeños, uno por AUD.
3. **El lote de riqueza barata** (§9, ítems B1–B11): cada mejora con su
   prueba de antes/después y su fila en `KNOWN_GAPS.md` cuando aplique.
4. **Reconstrucción del contenido de referencia** bajo las invariantes
   anuladas (plan 87 §27), aprovechando la autoría estudiantil existente.
5. **Empaquetar el curso:** el motor, los niveles, los validadores y el
   material de clase forman una unidad publicable; el índice 00 y las guías
   (60, 66, 88) son la puerta de entrada.

La brújula de cada paso es la misma: **si rompe una entrega o una demo de
clase, la mejora está mal, por buena que sea la ingeniería** — y todo cambio
se declara arreglado sólo con evidencia ejecutada.

## 9. Mejoras priorizadas

| ID | Mejora | Origen | Costo | Base existente | Compatibilidad docente |
|---|---|---|---|---|---|
| B1 | NG+ con dificultad creciente | DS | Bajo | `difficulty.py`, `boss_rush_mode.py` | Alta |
| B2 | Porcentaje de ítems por escenario (cofres/llaves) | Super Metroid | Bajo | leaderboards + inventario | Alta |
| B3 | Atajo de una vía (ya en 2-2, generalizarlo) | DS | Bajo | warp/door TMX | Alta |
| B4 | Fogata/bonfire como objeto TMX reutilizable | DS | Bajo | fuente sanadora del 3-3 | Alta |
| B5 | Piezas de corazón ¼ (4 piezas = corazón) | Zelda | Medio | `heart_vessel` en inventario | Alta |
| B6 | Minijuego de tiro al arco | Zelda | Medio | arco + escenas | Alta |
| B7 | Canción del Sol (toggle día/noche como mecánica) | Zelda | Medio | `WorldSimulation` → `EnvironmentState` | Alta |
| B8 | Finales condicionales (flags de guardado) | SotN | Medio | `save_manager` | Alta |
| B9 | Subarmas (base: el arco) | SotN | Medio-alto | inventario equipable | Alta |
| B10 | Acompañante con pistas | Zelda | Medio | sistema de diálogo | Media |
| B11 | Drops de ítems en enemigos | SotN | Medio | bestiario | Media |
| B12 | Estación de recarga reutilizable por mapa | Super Metroid | Bajo-medio | objeto TMX | Alta |

**Descartes explícitos** (documentados en §4): hub/backtracking global,
sequence breaking, vidas y warp zones, stamina, mundo sin mapa, NPCs
crípticos, castigo por muerte en partida estándar.

## 10. Próximos pasos

1. Sancar el pacing de la zona 4 (F4) — rama actual, lotes pequeños.
2. Corregir el falso positivo de `grade_stage` en arenas (F3).
3. Decidir el destino de `computer-vision-course/` (F5): `.gitignore` o repo
   aparte.
4. Asignar `AUD-573+` a cada hallazgo implementado, con su prueba.
5. El lote B1–B4 como primer paquete de riqueza barata (todo bajo costo).

## 11. Registro de la suite completa

**Resultado: 5907 passed, 8 failed, 18 skipped en 1021 s (17 min).**
Re-ejecución individual de los 8 fallos: **6 fallan de forma estable, 2 son
intermitentes** (pasaron al re-ejecutar: `test_cajas_de_colision` —
hurtbox — y `test_la_lluvia_no_se_queda_pegada` — canal libre). Ninguno
toca los cambios de esta auditoría (sólo documentación nueva).

Fallos estables (deuda preexistente, ajenos a esta auditoría):

| Prueba | Causa raíz | Naturaleza |
|---|---|---|
| `test_el_mirador_de_la_fase_6.py` | el guion del mirador no cumple el contrato de 2 movimientos de cámara, 1 espera y 2 fundidos | trabajo en curso de la rama (zona 4) |
| `test_particion_de_stage_scene.py[senales]` | la partición de `stage_scene` creció más allá del tamaño acordado | refactor en curso |
| `test_rutas_de_los_documentos.py[22_API_CONTRACTS.md]` | una cita rota en `22_API_CONTRACTS.md` | deuda de documentación |
| `test_salida_de_consola.py[generate_all_assets.py]` | `tools/generate_all_assets.py` imprime `→` y no reconfigura `stdout` a UTF-8: muere con `UnicodeEncodeError` en consola Windows | deuda de tooling |
| `test_sistemas_huerfanos.py` | `src/framework/stage/level_mechanics.py` (`avisando`) lo declara completo `45_SWIMMING_SPEC.md` y el juego no lo invoca | clasificación pendiente (VERIFICADO/PENDIENTE) |
| `test_student_guidance.py` | la sección generada de tipos de partícula de `STAGE_CREATION.md` no incluye `vida_abisal` | sección generada desactualizada |

Estos 6 pasan a la cola de `91_PLAN_DE_CIERRE.md` como candidatos de
`AUD-573+` (el último usado es AUD-572).

### 11.1 Cierre de la actualización de documentación (misma sesión)

Los tres fallos estables que eran **de documentación** se corrigieron al día
siguiente de esta auditoría, cada uno con su evidencia:

| Prueba | Corrección |
|---|---|
| `test_rutas_de_los_documentos.py[22_API_CONTRACTS.md]` | `src/engine/utils/spritesheet.py` es un módulo retirado citado como historia (AUD-168): se declaró en `MODULOS_RETIRADOS` del test, que es el mecanismo oficial para esa clase de cita |
| `test_sistemas_huerfanos.py` | `avisando` resultó ser un huérfano real (el aviso de oxígeno bajo no lo lee nadie): se clasificó en `PENDIENTES` del guardián y se abrió **GAP-071** en `KNOWN_GAPS.md` con su plan de resolución |
| `test_student_guidance.py` | la fila `ambient_fx` de `STAGE_CREATION.md` no listaba `niebla` ni `vida_abisal`: se añadieron los dos tipos al rango documentado |

Además, la cifra viva de la suite (5.933 pruebas recogidas) quedó sincronizada
en `README.md` (decía 4.788) y en `docs/62_ESTADO_DEL_PROYECTO.md` (decía
4.751). Los tres fallos estables restantes (mirador de la fase 6, partición de
`stage_scene`, `generate_all_assets.py`) son de código o tooling y siguen en
la cola de `AUD-573+`.
### 11.2 Cierre de los hallazgos del FODA (lotes AUD-586…594, 2026-08-21)

Los ocho hallazgos de la §6 quedaron atendidos; cada uno con su evidencia
ejecutada, los tres que no pedían código disueltos por lectura:

| Hallazgo | Resolución |
|---|---|
| F1 (P2) — perfiles iCCP en PNG | **AUD-589** — chunk eliminado a nivel binario de los 15 tilesets del 4-1 y guardián nuevo (	ests/test_los_png_no_llevan_perfiles_de_color.py) que impide que vuelvan a entrar |
| F2 (P2) — pickle distribuido | **AUD-587** — professor_sample.pkl retirado del repo (git rm); alidate_assets.py exige el dataset .npz con llow_pickle=False; guardián anti-pickle en 	ests/test_pattern_demo.py; cinco documentos actualizados |
| F3 (P2) — grader y salidas | **AUD-586** — hall.tmx deja de declarar un NextTrigger fantasma; el aviso del grader ya no cuenta la métrica de ruta donde no aplica; fila hall corregida en NIVELES; env del subprocess del grader arreglado (os.environ completo, no PATH vacío) |
| F4 (P2) — checkpoints Zona 4 | Disuelto por lectura (**AUD-590**, doc-only): las brechas son diseño deliberado — AUD-516 (4-1, terror psicológico), AUD-576 (4-1b, siete por evento), test propio en 4-1c (seis por sección); las «plataformas sin ruta» de 4-1c son falso positivo del análisis estático sobre bloques rítmicos. Excepción documentada en \docs/66_GUIA_DE_LEVEL_DESIGN.md\ §1.3 |
| F5 (P2) — computer-vision-course/ | Decisión del dueño (2026-08-21): no tocar nada todavía. Queda como hallazgo abierto, sin seguimiento git, 689 archivos |
| F6 (P3) — catálogos de traducción | Disuelto por lectura: la regla AUD-307 obliga a que todo literal visible en español tenga entrada en \n.json\ (\check_translations --ci\ en verde); la asimetría 44/87 es estructural (herencia bilingüe), no pudrición |
| F7 (P3) — registro diferido | **AUD-591** — stage1_1 registra \ShooterFrog\/\FlyingBird\ a nivel de módulo (como ordena el propio aviso y practican boss_paburu/stage1_3); dos registros huérfanos ("Skitter"/"Bat") retirados de sus pruebas; trinquete nuevo: ningún mapa del motor registra dentro de una función |
| F8 (P3) — BossSpawn sin uso directo | Disuelto por lectura: \ALTERNATIVAS\ de \check_tmx_coverage.py\ (AUD-366) ya lo documenta con medición; el informe dice «cubierto indirectamente por los 4 tipos de jefe» |

Además, en la misma sesión se cerró el último hueco técnico abierto del
audio del 4-1 (**GAP-070** puntos 4/5/7, lotes **AUD-592/593/594**):
tormenta paneada estéreo para la Fase 3, lluvia pasa-banda «de radio vieja»
para la Fase 4, y bus de reverberación de la Fase 6 con variantes
\_con_eco\ horneadas y preferencia en \AudioManager.play_sfx\. GAP-067,
GAP-068 (material de autor pendiente) y GAP-072 (cuatro capacidades de
motor aún sin construir) siguen abiertos con su plan.

Las tres pruebas que §11 registraba como fallos estables de deuda
(\	est_salida_de_consola\, \	est_el_mirador_de_la_fase_6\,
\	est_particion_de_stage_scene\) pasan hoy en verde: se fueron cerrando en
los lotes intermedios de la rama. La cifra viva de la suite quedó
sincronizada en \README.md\ y \docs/62_ESTADO_DEL_PROYECTO.md\
(6.059 pruebas recogidas).
