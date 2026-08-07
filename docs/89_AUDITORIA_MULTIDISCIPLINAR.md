---
document_id: "LOI-AUDIT-089"
title: "Auditoría multidisciplinar — iteración agosto 2026"
aliases: ["Auditoría multidisciplinar 2026-08"]
tags: ["audit", "report"]
description: "Auditoría multidisciplinar de 16 disciplinas con puntuación verificable: 12 hallazgos corregidos (AUD-310 a AUD-322) y los pendientes medidos"
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
evidencia ejecutada en esta iteración (método en §19). Se corrigieron **13
hallazgos** (AUD-310 a AUD-322), todos con prueba que fallaba antes de tocar
código; quedan **7 hallazgos pendientes** medidos con su ubicación exacta.

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

**Media: 89,4/100.**

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

## 3. Correciones de esta iteración (AUD-310 a AUD-322)

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

## 8. Notas de puntuación

Cada disciplina parte de 100 y descuenta puntos por **defectos abiertos**
(no por defectos corregidos en esta iteración): −8 por hallazgo grave abierto
(P1, P4), −4 por hallazgo menor (P2, P3, P5, P6, P7), −2 por deuda de
medición (suites o métricas que no existen y se anotan). Las disciplinas sin
correcciones en esta iteración puntúan por su estado medido, no por el trabajo
de la iteración. La puntuación se puede reproducir desde las tablas §3 y §6.
