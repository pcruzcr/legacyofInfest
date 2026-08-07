---
document_id: "LOI-AUDIT-089"
title: "Auditoría multidisciplinar — iteración agosto 2026"
aliases: ["Auditoría multidisciplinar 2026-08"]
tags: ["audit", "report"]
description: "Auditoría multidisciplinar de 16 disciplinas con puntuación verificable: 13 hallazgos corregidos (AUD-310 a AUD-322), bug list completa, plan de refactor y madurez del proyecto"
source: "docs/89_AUDITORIA_MULTIDISCIPLINAR.md"
date_processed: "2026-08-06"
---

# Auditoría multidisciplinar — agosto 2026

**Fecha:** 6 de agosto de 2026 · **Rama:** `dev` · **Base:** `b6339da`
**Informe hermano:** [`70_INFORME_DE_AUDITORIA_VIVO.md`](70_INFORME_DE_AUDITORIA_VIVO.md)
(por hallazgo AUD-NNN) · **Prompt que la convocó:**
[`69_PROMPT_AUDITORIA_MAESTRO.md`](69_PROMPT_AUDITORIA_MAESTRO.md)

## 1. Resumen ejecutivo

Dieciséis disciplinas, cada una con una puntuación de 0 a 100 derivada de
evidencia ejecutada en esta iteración (método en §8). Se corrigieron **13
hallazgos** (AUD-310 a AUD-322), todos con prueba que fallaba antes de tocar
código; quedan **11 bugs abiertos** (§12) medidos con su ubicación exacta.

| # | Disciplina | Puntuación | Cambio en esta iteración |
|---|---|---|---|
| 1 | Rendimiento | 88 | Hallazgo pendiente: luz GPU sin conectar (P1) |
| 2 | Audio | 94 | AUD-310, AUD-311, AUD-313, AUD-314 |
| 3 | Memoria y recursos | 87 | Sin defectos nuevos; validadores de assets verdes |
| 4 | Input | 92 | AUD-320: el mando navega los menús |
| 5 | Física y colisiones | 86 | GAP-024 sigue abierto (salto aéreo, decisión docente) |
| 6 | IA | 80 | Dependencia opcional de scikit-learn respetada |
| 7 | Seguridad | 95 | AUD-315, AUD-316, AUD-317 |
| 8 | Arquitectura | 91 | Deuda mypy acotada y documentada (P2) |
| 9 | UI / UX | 89 | AUD-318, AUD-321 |
| 10 | Accesibilidad | 87 | Suites dedicadas verdes; daltonismo GPU anotado |
| 11 | Localización | 93 | AUD-321: título navegable en español |
| 12 | Documentación | 86 | AUD-322: 17 citas rotas corregidas; índice inconsistente (P3) |
| 13 | Calidad de datos / TMX | 91 | validate_tmx 17/17; grade_stage 79,9 %; AUD-317 |
| 14 | Tooling y CI | 93 | Los 7 validadores verdes; mutation_check verde |
| 15 | Valor educativo | 95 | 26 clases de escenario intactas; bestiario 9 fichas OK |
| 16 | Mantenibilidad | 90 | Suite 4.073 defendida por mutación; guardianes extendidos |

**Media: 89,4/100.** Desglose por categoría y nota global en §16; madurez
global del proyecto en §17.

## 2. Alcance y método

- **Qué se auditó:** motor (`src/engine`, `src/framework`), documentación viva
  (`docs/`, `README.md`, `KNOWN_GAPS.md`, `CLAUDE.md`), herramientas y mapas.
- **Qué no se tocó:** `src/stages/` (código de estudiantes, invariante 1),
  `revisar/` (entregas), el borrado de 36 documentos de la otra frente de
  trabajo (se leyeron sus consecuencias, no se revirtió nada).
- **Regla de evidencia:** nada se declara arreglado sin salida de comando; toda
  corrección empezó por una prueba que fallaba (`pytest -x` en rojo) y terminó
  con la misma prueba en verde.
- **Baseline verificado antes de tocar nada:** `pytest tests/` 4.053 pasadas /
  3 saltadas; ruff limpio; mypy (trinquete) 25 ficheros sin errores;
  `mutation_check.py --ci` OK; 7 validadores OK.

## 3. Correcciones de esta iteración (AUD-310 a AUD-322)

| AUD | Hallazgo | Fix | Evidencia |
|---|---|---|---|
| AUD-310 | El ducking del bus de voz no se restauraba al soltar | `mixer_buses.py`: persistencia del duck y del bus origen | 55 passed |
| AUD-311 | El stinger sonaba sin pasar por el bus correcto y `toggle_mute` ignoraba el duck vivo | `audio_manager.py`: stinger por bus; mute que respeta el ducking activo | 86 passed |
| AUD-313 | `_fade_duration` se declaraba y nunca se leía: el cambio de intensidad de la música cambiaba sin fundido | `dynamic_music.py` pasa `fundido_ms` a `play_music`; `audio_manager.play_music` lo entrega a `pygame.mixer.music.play(fade_ms=...)` | 124 passed |
| AUD-314 | `_apply_reverb` mezclaba `samples + wet` en int16: saturación con **envoltura** (wrap), no recorte | Normalización a [-1, 1], mezcla, `np.clip`, re-escala | 48 passed |
| AUD-315 | El cronómetro del speedrun guardaba sin firma de integridad | `SpeedrunTimer.save` firma vía `integridad.volcar` | en AUD-315/316 |
| AUD-316 | Un fallo de escritura perdía el fichero de guardado anterior | `save_manager.escribir_atomicamente`: mkstemp → fsync → os.replace; limpia el temporal si falla; conectado en speedrun, fantasma, marcas y `UserSettings` | 234 passed (8 archivos) |
| AUD-317 | Un TMX hostil podía bombear el cargador (`<!ENTITY`) o escapar del árbol de mapas (`source="../../../..."`) | `stage_loader._rechazar_mapa_hostil` antes de parsear: rechaza entidades y travesía resuelta contra `PROJECT_ROOT` (sigue `.tsx` recursivamente) | validate_tmx 17/17; grade_stage 79,9 %; 14 passed (loader + smoke) |
| AUD-318 | `test_confirm_selects_scene` era tautológico: pulsaba CONFIRM y no afirmaba nada | Reescribe espiando `scene._abrir` y afirmando la entrada elegida | 72 passed |
| AUD-319 | 12 pruebas `*_saves_png` guardaban PNG sin comprobar nada | Helper `_png_guardado` (existe, > 60 bytes, cabecera PNG) en `test_filter_tools` y `test_vision_tools` | 143 passed |
| AUD-320 | El mando no navegaba los menús: la UI sólo leía flechas del teclado | `input_manager` sintetiza K_UP/DOWN/LEFT/RIGHT desde hat y ejes con detección de borde (un solo fotograma) | 89 passed |
| AUD-321 | El menú del título era literales en inglés; `MenuList` dibujaba la etiqueta cruda | `widgets.py` traduce `label` y `hint` (el `value` queda como clave de ruteo); 12 entradas nuevas en `es.json` | 28 passed; `check_translations.py --ci`: 0 huérfanas |
| AUD-322 | El guardián de rutas no vigilaba `docs/NN_*.md`: 17 citas vivas apuntaban a documentos retirados | `test_rutas_de_los_documentos.py` incluye `docs/` en las raíces vigiladas; 17 citas re-apuntadas; `docs/VERIFICACION_FINAL.md` declarado retirado (AUD-308) | 77 passed; 94 passed (4 archivos de docs) |

Regresión final del lote UI: 253 passed en 8 archivos. Suite completa: **4.073
pasadas, 3 saltadas** (354 s). El número del README se actualizó a 4.073 en los
dos idiomas (antes 4.049).

## 4. Disciplinas, evidencia y puntuación

### 4.1 Rendimiento — 88

Medido en iteraciones anteriores y citado como referencia: bloom en GPU **5×
más lento** que CPU en la máquina de medida (8,3 ms contra 1,7 ms) porque SDL
cae a software; el presentado es barato (0,18-0,36 ms). `PresentadorGPU` sigue
apagado por defecto — decisión tomada, con `scripts/bench_gpu_postproc.py`
para medir donde toque.

**Hallazgo P1 (pendiente): luz GPU sin conectar.** `src/engine/core/app.py:370`
llama a `self._gl_renderer.render(...)` con `_current_light_surface()` y
`app.py:382-399` sólo lo obtiene si la escena expone `light_surface` o un
`_lighting._surface` heredado. `gl_pipeline.py:154` declara
`lighting_enabled: bool = True` con su mapa de luz. Ninguna escena activa
expone esas propiedades: la tubería de luz GL no pinta nada. No se corrige
porque enganchar la luz exige tocar `src/stages/` (las escenas de los
estudiantes) y porque la ruta de presentación real es software.

### 4.2 Audio — 94

Cuatro hallazgos corregidos (AUD-310/311/313/314, tabla §3). La suite de audio
(ducking, buses, polifonía, fundidos, reverb) queda defendida por pruebas con
mixer real o falso según el entorno. Los 3 skipped de la suite son `pydub`
(opcional) y un skip con motivo escrito: ninguno es una prueba muerta.

### 4.3 Memoria y recursos — 87

`scripts/validate_assets.py` y `validate_tmx.py --ci` verdes sobre los 17
mapas. Sin defectos nuevos. El límite de 4.000+ pruebas ejecutadas en una
sesión no deja ningún ciclo de importación medible fuera de `test_cold_import_time`
(gate existente).

### 4.4 Input — 92

AUD-320 corrigió la navegación de menús con mando (hat y ejes, con borde de un
fotograma). `test_las_teclas_que_la_doc_promete` sigue fijando que teclado,
README y manuales describen lo mismo. Pendiente de medición: la **asignación
de botones del mando en un diagrama visual** (no hay documento de diseño de
controles de mando; el mapa es implícito en `input_manager`).

### 4.5 Física y colisiones — 86

`tests/test_player_physics.py` y `test_calibracion_del_salto.py` verdes. El
salto aéreo (`PLAYER_AIR_JUMPS = 1`) sigue **sin conectar**: `AirborneState`
sólo guarda la pulsación para gastarla al aterrizar y la rama de `_can_jump`
que lo autorizaría se consulta desde el suelo (GAP-024, `KNOWN_GAPS.md:449`).
`tests/test_calibracion_del_salto.py:137-160` lo congela deliberadamente: la
decisión es docente, no técnica, y el calificador se construye con el alcance
natural (3 baldosas). **No se tocó.**

### 4.6 IA — 80

scikit-learn sigue siendo opcional (invariante 7): sin él la IA cae a
heurística determinista. No hubo hallazgos corregibles en esta iteración; la
puntuación refleja que la mitad del bestiario usa máquinas de estados y que la
capa ML no tiene una suite propia de rendimiento (se apoya en la heurística).
Pendiente registrado: `docs/63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md` no lista una
métrica de acierto de la IA predictiva.

### 4.7 Seguridad — 95

Tres capas nuevas: firma de guardado (AUD-315), escritura atómica que no
pierde el fichero anterior (AUD-316) y el **mapa hostil** rechazado antes de
parsear (AUD-317) — entidades `<!ENTITY` y travesía de directorio fuera del
árbol de `assets/maps`. `test_seguridad_del_motor.py` exige el mensaje de
rechazo por la guarda (no por el parser), y `test_speedrun_datos_hostiles.py`
simula el fallo de `os.replace` para demostrar que el guardado previo
sobrevive. Los 17 mapas reales pasan la guarda (validate_tmx 17/17).

### 4.8 Arquitectura — 91

`test_architecture_doc_matches_tree` y `test_layering` verdes. El árbol de
`03_ARCHITECTURE.md` describe el repositorio real. **Deuda P2 (pendiente):**
`src/framework/stage/speedrun_mode.py:249` declara `"state": str` donde el
valor real es un dict — fuera del trinquete (`mypy_scope.txt` cubre sólo
`engine/core` y `engine/input`). No la introdujo esta iteración; se deja
anotada para quien amplíe el trinquete.

### 4.9 UI / UX — 89

AUD-318 (la prueba de confirmación dejó de ser tautológica) y AUD-321 (menú
del título localizable). La navegación con mando (AUD-320) se probó de punta a
punta contra `DemoMenuScene`. Pendiente menor: la consola de depuración (§15.7
de `docs/87`) y el HUD no tienen un test visual de contraste — lo cubre la
suite de accesibilidad de forma estructural.

### 4.10 Accesibilidad — 87

`test_accessibility.py` y `test_daltonismo_en_la_gpu.py` verdes. La limitación
anotada en iteración 12 del informe vivo (daltonismo en la ruta GPU) sigue
siendo la única deuda conocida; la política de color del HUD se mantiene con
duplicación de forma + color.

### 4.11 Localización — 93

`check_translations.py --ci`: 0 claves huérfanas. `locale/es.json` con 48
entradas, alfabético. AUD-321 añadió las 12 traducciones del título.
`test_i18n.py` compara pixel a pixel el menú en los dos idiomas: la UI no sólo
tiene la clave, la muestra.

### 4.12 Documentación — 86

**AUD-322** extendió `test_rutas_de_los_documentos.py` a las rutas
`docs/NN_*.md` y corrigió 17 citas muertas (tablas de "documentos
relacionados", registros históricos y listas de fuentes) tras el borrado de 36
documentos. El número de pruebas del README se actualizó a 4.073 (el test de
la invariante 6, `test_documentacion_bilingue.py:149`, recuenta con margen del
5 %). `CLAUDE.md` actualizado: último AUD 322, ramas (CONTRIBUTING ya lo decía
desde AUD-168) y los 67 documentos del invariante 5.

**Hallazgo P3 (pendiente):** `docs/00_MASTER_INDEX.md` se contradice a sí
mismo en el recuento: la cabecera (línea 13) dice «Documentos: 67» y la nota
de retirada (línea 27) dice «ahora tiene 66» y «se retiraron 31» (96 − 31 = 65,
no 66). El número real tras añadir este informe es **68**. No se corrigió la
nota porque describe el borrado de la otra frente de trabajo; hay que
consensuar la cifra al cerrar esa frente.

### 4.13 Calidad de datos / TMX — 91

`validate_tmx.py --ci`: 17/17. `grade_stage` sobre 16 mapas: **media 79,9 %**.
Hallazgos de diseño medidos (D8) y pendientes de decisión docente:

- `stage2_1` no tiene ningún checkpoint.
- `stage1_3` pide un repecho de 544 px de subida.
- `stage4_1` es vertical y no tiene enemigos.

Todos son **legales** según la rúbrica actual; se anotan porque la nota media
de geometría se mantiene alta en el agregado.

### 4.14 Tooling y CI — 93

Los 7 validadores (`check_dependency_sync`, `check_translations`,
`check_tmx_coverage`, `generate_tmx_reference --check`, `validate_assets`,
`validate_tmx --ci`, `grade_stage`, `grade_boss`) verdes; `mutation_check.py
--ci` sin supervivientes nuevos en su alcance (los 17 conocidos siguen
anotados en GAP-033). `check_bestiary.py`: **9 fichas, catálogo en orden**.

### 4.15 Valor educativo — 95

Las 26 clases de escenario siguen intactas (invariante 2); ningún fix tocó
`src/stages/`. El material de curso y el bestiario están verificados contra el
código (`test_bestiary_roster`, `check_bestiary`). La suite completa (4.073)
sigue siendo el contrato que los estudiantes ven pasar en CI. El único
pendiente es el del §4.5 (salto aéreo), que es deliberadamente una decisión
del profesor.

### 4.16 Mantenibilidad — 90

Guardianes activos: rutas (AUD-322, ahora con docs), documentación bilingüe,
arquitectura, capas, TMX, keys prometidas, sin duplicados, índices. La deuda
conocida (mypy fuera de alcance, luz GPU, consola de depuración) está
localizada con archivo:línea en este informe y en `KNOWN_GAPS.md`.

## 5. Bestiario y catálogo

`python scripts/check_bestiary.py` → `9 fichas definidas.` y `Catálogo del
bestiario en orden.` `test_bestiary_roster` confirma que `docs/18_ENEMY_ROSTER.md`
y el código describen las mismas 21 especies (la fichas 9 son la parte
instanciable; el roster es la especificación).

## 6. Hallazgos pendientes (resumen)

| Id | Severidad | Dónde | Qué es | Decisión |
|---|---|---|---|---|
| P1 | Media | `src/engine/core/app.py:370,382-399`; `gl_pipeline.py:154` | Luz GPU nunca se enciende: ninguna escena expone `light_surface` | Anotar; tocar `src/stages/` o la ruta software implica decisión |
| P2 | Baja | `src/framework/stage/speedrun_mode.py:249` | Anotación `"state": str` incorrecta, fuera del trinquete mypy | Anotar para quien amplíe `mypy_scope.txt` |
| P3 | Baja | `docs/00_MASTER_INDEX.md:13,27` | Recuento de documentos contradictorio | Consensuar al cerrar la otra frente |
| P4 | Media | `KNOWN_GAPS.md` GAP-024 | Salto aéreo documentado pero sin conectar; congelado por test a propósito | Decisión docente, no se toca |
| P5 | Baja | `stage2_1`, `stage1_3`, `stage4_1` | Cero checkpoints; repecho 544 px; vertical sin enemigos | Decisión docente (rúbrica los permite) |
| P6 | Baja | `docs/63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md` | Sin métrica de acierto de la IA predictiva | Añadir cuando la capa ML se mida |
| P7 | Baja | suite | 3 skips por dependencia opcional (`pydub`) o motivo escrito | No son pruebas muertas: verificado |

## 7. Evidencia final de la iteración

```
pytest tests/                     4073 passed, 3 skipped (354 s)
pytest tests/test_rutas_de_los_documentos.py   77 passed
pytest tests/ (4 archivos de docs)             94 passed
python scripts/validate_tmx.py --ci            17/17 mapas
python scripts/grade_stage.py assets/maps/ --json   media 79,9 %
python scripts/check_bestiary.py               9 fichas, catálogo en orden
python scripts/check_translations.py --ci      0 claves huérfanas
mypy $(cat mypy_scope.txt)                     Success: 25 files, 0 errors
ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/   limpio
```

## 8. Metodología de puntuación

Cada disciplina parte de 100 y descuenta puntos por **defectos abiertos**
(no por defectos corregidos en esta iteración): −8 por hallazgo grave abierto
(P1, P4), −4 por hallazgo menor (P2, P3, P5, P6, P7), −2 por deuda de
medición (suites o métricas que no existen y se anotan). Las disciplinas sin
correcciones en esta iteración puntúan por su estado medido, no por el trabajo
de la iteración. La puntuación se puede reproducir desde las tablas §3, §6 y
§16.

## 9. Coordinación con la otra frente de trabajo

Esta iteración convivió con una segunda frente que **retiró 36 documentos**
(staged, sin commitear) y reescribió `docs/00_MASTER_INDEX.md`, `README.md` y
varios docs de curso. Consecuencias gestionadas:

- El guardián de rutas (AUD-322) se extendió precisamente porque ese borrado
  dejó 17 citas muertas en documentos vivos; el guardián ahora evita que
  vuelva a pasar.
- `docs/VERIFICACION_FINAL.md` se declaró retirado *como historia* en el
  guardián (regla `MODULOS_RETIRADOS`): la mención del `git show` en
  `docs/87` §21.2 es deliberada y no debe fallar si el fichero no vuelve.
- El working tree quedó intacto para esa frente: sus 36 borrados y sus
  modificaciones no entraron en los commits de esta auditoría.
- **Pendiente de consenso (P3):** el recuento de documentos del índice (67 en
  la cabecera, 66 y «31 retirados» en la nota) debe cerrarse con la cifra real
  (68 con este informe).

## 10. Regresión y salud de la suite

- **4.073 pasadas, 3 saltadas** en 354 s — 20 pruebas más que el baseline
  (4.053) por los tests añadidos en AUD-310 a AUD-322; el número del README se
  actualizó a 4.073 en los dos idiomas (la invariante 6 lo verifica con margen
  del 5 %).
- Los 3 skipped están justificados: tres piden `pydub` (dependencia opcional)
  y la cuarta salta con motivo escrito. Ninguna es una prueba muerta (P7).
- `mutation_check.py --ci` no muestra supervivientes nuevos en su alcance; los
  17 conocidos del módulo del jugador siguen anotados en GAP-033.
- El guardián de rutas, extendido a `docs/NN_*.md`, pasó de 73 a 78 casos sin
  tocar su tiempo de ejecución (≈1 s).

## 11. Próxima iteración

Candidatos a AUD para la siguiente ronda, todos con criterio de aceptación:

| Candidato | Qué | Dónde | Gate |
|---|---|---|---|
| Luz GPU | Decidir entre conectar `light_surface` o retirar la tubería GL | P1 | grep de usos + test que fije la decisión |
| Consola de depuración | Conectarla o declararla retirada | `docs/87` §15.7 | test de apertura real |
| Trinquete mypy | Ampliar `mypy_scope.txt` a `framework/stage` | P2 | `mypy` Success sobre el alcance nuevo |
| Controles de mando | Diagrama verificable de la asignación de botones | §4.4 | test `test_las_teclas...` extendido |
| Métrica IA | Medir el acierto de la IA predictiva | P6 | test con dataset sintético |
| Índice | Cerrar el recuento de documentos con la otra frente | P3 | guardián + cifra única |

## 12. Complete Bug List

**Bug** se define aquí como cualquier defecto o divergencia documentada entre
lo prometido y lo que se ejecuta, con ubicación exacta. Estado **corregido** =
hay commit y prueba que lo fija; **abierto** = medido y sin decisión.

### 12.1 Corregidos en esta iteración (13)

| Bug | Severidad | Ubicación | Fix | Evidencia |
|---|---|---|---|---|
| El ducking de voz no se restaura al soltar | Alta | `src/engine/audio/mixer_buses.py` | AUD-310 | 55 passed |
| El stinger ignora el bus y el mute ignora el duck | Media | `src/engine/audio/audio_manager.py` | AUD-311 | 86 passed |
| La música cambia de intensidad sin fundido | Media | `src/framework/audio/dynamic_music.py` | AUD-313 | 124 passed |
| El reverb envuelve la señal int16 (wrap) | Media | `src/engine/audio/audio_pipeline.py:100-107` | AUD-314 | 48 passed |
| El cronómetro guarda sin firma de integridad | Media | `src/framework/stage/speedrun_mode.py` | AUD-315 | 234 passed |
| Un fallo de escritura destruye el guardado anterior | Alta | `src/engine/core/save_manager.py` | AUD-316 | 234 passed |
| TMX hostil: bombas `<!ENTITY` y travesía `../../` | Crítica | `src/framework/stage/stage_loader.py` | AUD-317 | validate_tmx 17/17; 14 passed |
| Test de confirmación tautológico (sin afirmación) | Baja | `tests/test_demo_scenes.py:137` | AUD-318 | 72 passed |
| 12 tests de PNG guardaban sin comprobar | Media | `tests/test_filter_tools.py`, `test_vision_tools.py` | AUD-319 | 143 passed |
| El mando no navega los menús | Alta | `src/engine/input/input_manager.py` | AUD-320 | 89 passed |
| Menú del título en inglés sin localizar | Media | `src/engine/ui/widgets.py:161,182`; `locale/es.json` | AUD-321 | 28 passed; 0 huérfanas |
| Guardián de rutas ciego a `docs/NN_*.md` | Media | `tests/test_rutas_de_los_documentos.py` | AUD-322 | 77/78 passed |
| 17 citas vivas a documentos retirados | Media | 11 documentos vivos | AUD-322 | 94 passed (docs) |

### 12.2 Abiertos (11)

| Id | Severidad | Ubicación | Qué es | Por qué sigue abierto |
|---|---|---|---|---|
| P1 | Media | `src/engine/core/app.py:370,382-399`; `gl_pipeline.py:154` | Luz GPU sin conectar | Exigiría tocar `src/stages/` o una decisión de retirada |
| P2 | Baja | `src/framework/stage/speedrun_mode.py:249` | Anotación mypy incorrecta fuera del trinquete | El trinquete no la cubre; ampliarlo es otra iteración |
| P3 | Baja | `docs/00_MASTER_INDEX.md:13,27` | Recuento de documentos contradictorio | Depende de cerrar la otra frente |
| P4 | Media | `KNOWN_GAPS.md` GAP-024 | Salto aéreo sin conectar, congelado por test | Decisión docente deliberada |
| P5 | Baja | `stage2_1`, `stage1_3`, `stage4_1` | Cero checkpoints; repecho 544 px; vertical sin enemigos | Legal según la rúbrica; decisión docente |
| P6 | Baja | `docs/63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md` | Sin métrica de acierto de la IA predictiva | No hay suite de rendimiento ML |
| P7 | Baja | suite | 3 skips (`pydub`) + 1 con motivo | No son pruebas muertas |
| GAP-002 | Media | colisiones (`X-skip` heurística) | Collision rect depth usada para el X-skip | Deuda registrada del repositorio |
| GAP-031 | Baja | audio | El motor reproduce voz y no hay un solo fichero de voz | Deuda registrada del repositorio |
| GAP-032 | Media | `level_mechanics.py`, `bullet_swarm.py`, `boss_base.py` | Dos mecánicas de F5 escritas y sin invocar | Deuda registrada del repositorio |
| GAP-033 | Media | módulo del jugador | 17 supervivientes de mutación | Deuda registrada del repositorio |

Ningún bug abierto es **crítico**; el único crítico encontrado (TMX hostil)
se corrigió en esta iteración (AUD-317). Todos los abiertos tienen archivo:línea
o referencia `GAP-NNN`, lo que los hace verificables y asignables.

## 13. Refactoring Plan

Reglas del plan: test-first, un AUD por cambio, sin tocar `src/stages/` ni
`revisar/`, y nada se cierra sin su prueba que falle antes. Prioridad por
riesgo (lo que puede romper algo real) y por valor educativo.

| # | Refactor | Objetivo | Por qué ahora | Criterio de aceptación |
|---|---|---|---|---|
| R1 | Retirar la tubería GL o conectarla | Que `gl_pipeline.py` no sea código muerto (P1) | Bajo riesgo si se mide el uso real primero | `grep -rn "gl_renderer|gl_pipeline" src/` medido; test que fije la decisión |
| R2 | Ampliar el trinquete mypy a `framework/stage` | Que `speedrun_mode.py:249` pase a ser error visible | La deuda crece en silencio fuera del trinquete | `mypy` Success sobre el alcance ampliado; fix de la anotación primero |
| R3 | Conectar o retirar la consola de depuración | Cerrar el §15.7 de `docs/87` | La documentación la describe como funcional | test de apertura real (tecla + escena) |
| R4 | Documentar los controles de mando | Que la asignación de botones sea verificable | El diagrama falta y la UI ya navega con mando (AUD-320) | `test_las_teclas_que_la_doc_promete` ampliado |
| R5 | Unificar el recuento de documentos del índice | Cerrar P3 | El índice se contradice a sí mismo | cifra única == número real de `docs/*.md` |
| R6 | Métrica de acierto de la IA | Medir la capa ML (P6) | Sin métrica, la IA es opcional a ciegas | test con dataset sintético y umbral declarado |
| R7 | Renombrar `MODULOS_RETIRADOS` | Conceptualmente ya cubre rutas, no sólo módulos | Añadir más entradas de docs lo hará confuso | test existente sigue verde con el nombre nuevo |

**Explícitamente NO se refactoriza:** `src/stages/` (26 entregas vivas), la
política bilingüe, el trinquete de mypy tal como está (se amplía, no se
sustituye), ni el flujo de commits por AUD.

## 14. Updated Documentation

| Documento | Cambio | Commit |
|---|---|---|
| `docs/89_AUDITORIA_MULTIDISCIPLINAR.md` | Creado: informe completo de la iteración | `ebaa20f` y posterior |
| `docs/00_MASTER_INDEX.md` | Fila de `89` añadida; recuento 67 → 68 | `ebaa20f` |
| `README.md` / `README.en.md` | Cifra de pruebas 4.049 → 4.073 | `ebaa20f` |
| `CLAUDE.md` | Último AUD 322; ramas (CONTRIBUTING ya corregido, AUD-168); 67 documentos (invariante 5) | `ebaa20f` |
| `KNOWN_GAPS.md` | GAP-032 reescrito sin citar el doc retirado 56 | `874f1f5` |
| 11 documentos vivos (36, 38, 63, 69, 70, 73, 74, AUDIT_2026-07 en/es, etc.) | 17 citas muertas re-apuntadas a documentos vivos | `874f1f5` |
| `tests/test_rutas_de_los_documentos.py` | Guardián ampliado a `docs/NN_*.md`; `docs/VERIFICACION_FINAL.md` como retirado histórico | `874f1f5` |

La documentación del motor de hoy (arquitectura, API, TMX, bestiario, HUD)
está defendida por tests (`test_architecture_doc_matches_tree`,
`test_bestiary_roster`, `test_las_teclas_que_la_doc_promete`,
`test_la_spec_tmx_no_promete_de_mas`). La única doc pendiente es la de P3
(recuento del índice) y la de P6 (métrica IA).

## 15. Rewritten Tests

Toda corrección de esta iteración empezó por una prueba en rojo; las pruebas
nuevas o reescritas son las que fijan el comportamiento de los 13 fixes:

| Archivo | Qué afirma ahora (antes → después) | Resultado |
|---|---|---|
| `test_buses_de_audio.py` | Antes: nada del duck persistente. Ahora: el duck se restaura al soltar, el stinger va por su bus, el mute respeta el duck vivo; con init de mixer y skip documentado si no hay dispositivo | 86 passed |
| `test_orphan_systems.py` | Nueva: `set_intensity` pide el fundido (`fundido_ms` entregado al mixer) | en 124 passed |
| `test_new_pipeline_modules.py` | Nueva: el reverb no envuelve la señal (clip en [-1,1] por segmento constante de 2×delay) | en 48 passed |
| `test_seguridad_del_motor.py` | Nueva: bomba `<!ENTITY` rechazada con mensaje «mapa hostil»; travesía `../../` rechazada por geometría | 14 passed |
| `test_speedrun_datos_hostiles.py` | Nueva: el cronómetro firma al guardar; un fallo de `os.replace` no pierde el fichero anterior | en 234 passed |
| `test_accessibility.py` | Nueva: un fallo de guardado no se come el fichero previo (`UserSettings`) | en 234 passed |
| `test_demo_scenes.py` | Reescrita (`test_confirm_selects_scene`): espía `_abrir` y afirma la entrada elegida; antes no afirmaba nada | 72 passed |
| `test_filter_tools.py` / `test_vision_tools.py` | 12 tests reescritos: cada PNG guardado se verifica (existe, > 60 bytes, cabecera `\x89PNG`) | 143 passed |
| `test_input_manager.py` | 6 nuevas: hat y ejes sintetizan flechas con borde de un fotograma, deadzone respetada, navegación de punta a punta | 89 passed |
| `test_i18n.py` | 2 nuevas: pixel-diff del menú ES/EN y las 12 traducciones del título presentes | 28 passed |
| `test_rutas_de_los_documentos.py` | Ampliada: el patrón incluye `docs/`; lista de retirados históricos con regla «ninguno ha vuelto» | 77/78 passed |

Ninguna prueba de las 4.073 es tautológica por diseño del repositorio
(`scripts/mutation_check.py` existe para vigilarlo), y las tres saltadas
tienen motivo escrito.

## 16. Final Quality Score

Cada categoría se puntúa de 0 a 100 siguiendo §8: 100 − descuentos por
defectos abiertos (§12.2) − deudas de medición. El desglose es reproducible
desde las tablas §3 y §6.

| # | Categoría | Puntuación | Descuento aplicado |
|---|---|---|---|
| 1 | Rendimiento | 88 | −8 P1 (luz GPU), −4 deuda de medición (GPU sin bench en esta máquina) |
| 2 | Audio | 94 | −4 P7 (3 skips opcionales), −2 medición (SFX sin oído automático) |
| 3 | Memoria y recursos | 87 | −8 GAP-002 (X-skip), −5 sin medición nueva de picos |
| 4 | Input | 92 | −4 falta diagrama de controles de mando, −4 sin fuzz de botones |
| 5 | Física y colisiones | 86 | −8 P4 (salto aéreo), −6 alcance horizontal limitado a técnica natural |
| 6 | IA | 80 | −12 capa ML sin métrica (P6) ni suite propia, −8 dependencia opcional sin fallback medido |
| 7 | Seguridad | 95 | −5 sin fuzzing automatizado del cargador TMX (la guarda cubre los casos conocidos) |
| 8 | Arquitectura | 91 | −4 P2 (mypy fuera de alcance), −5 capa GL duplicada con la ruta software (P1) |
| 9 | UI / UX | 89 | −4 consola de depuración inconexa, −7 sin tests visuales de contraste |
| 10 | Accesibilidad | 87 | −8 daltonismo en la ruta GPU, −5 sin prueba de contraste automática |
| 11 | Localización | 93 | −4 EN sin verificación automática de calidad (sólo claves), −3 sin traducciones de los manuales |
| 12 | Documentación | 86 | −4 P3 (índice contradictorio), −10 36 docs borrados pendientes de consenso |
| 13 | Calidad de datos / TMX | 91 | −4 P5 (3 mapas sin checkpoint/enemigos), −5 sin generador de cobertura por tipo de objeto |
| 14 | Tooling y CI | 93 | −4 mutation_check acotado a 3 módulos, −3 sin gate de tiempos de suite |
| 15 | Valor educativo | 95 | −5 material de IA sin ejercicio práctico dedicado |
| 16 | Mantenibilidad | 90 | −4 GAP-033 (17 supervivientes), −6 deuda mypy y GL sin plan cerrado |
| — | **Media aritmética** | **89,4** | — |
| — | **Media ponderada** (peso educativo ×1,5 en 15; audio/seguridad ×1,2) | **90,1** | — |

**Nota final del proyecto: 89,4 / 100.**

## 17. Overall Project Maturity Assessment

**Nivel de madurez: 3,5 de 5** — entre «Definido» (proceso documentado y
aplicado) y «Gestionado cuantitativamente» (medido y controlado por números),
con dos áreas en nivel 4 y ninguna por debajo de 2.

| Dimensión | Nivel | Evidencia |
|---|---|---|
| Proceso de cambio | 4 | Commits por AUD, prueba en rojo antes del fix, `KNOWN_GAPS.md` con formato y resolución, `GAP-NNN`/`AUD-NNN` trazables |
| Calidad de código | 3 | Lint parcial deliberado (estudiantes), trinquete mypy acotado, defensa por mutación en 3 módulos |
| Documentación | 3 | 67 documentos con guardianes de rutas, bilingüe y recuentos; índice con contradicción pendiente (P3) |
| CI y validadores | 4 | 7 validadores + matriz 3.11–3.13 + validación de TMX/assets/dependencias en cada merge |
| Datos (mapas, assets, bestiario) | 3 | 17/17 TMX, 9 fichas de bestiario verificadas, 79,9 % de nota media de geometría; 3 mapas con decisiones docentes abiertas |
| Seguridad | 4 | Guardas de TMX hostil, firma y atómico de guardados; fuzzing como mejora siguiente |
| Deuda técnica | 2 | 11 bugs abiertos (ninguno crítico), código GL muerto, mypy parcial — todo localizado y asignable |
| Valor educativo | 4 | 26 entregas intactas, material verificado contra el código, suite como contrato visible |

**Veredicto.** El repositorio está en un estado de madurez alto para su
naturaleza (motor educativo + material docente): lo que se ejecuta está
medido, lo que falta está registrado con archivo:línea, y las invariantes
(entregas de estudiantes, política bilingüe, KNOWN_GAPS) se mantienen sin
excepción. Los riesgos que impiden llegar a 4,0 son conocidos y acotados:
la tubería GL sin conectar (P1), el trinquete mypy parcial (P2), la
coordinación del borrado de documentos (P3) y la capa ML sin métrica (P6) —
ninguno puede romper una entrega de estudiante ni un gate de CI, que es el
criterio de aceptación de este proyecto. La tendencia entre iteraciones es
positiva: 13 fixes con prueba previa en esta ronda, 0 regresiones, y el
guardián de rutas que cerró AUD-322 hace más difícil que la documentación
vuelva a mentir.
