---
document_id: "LOI-CIERRE-76"
title: "Plan de cierre: todo lo que falta, medido"
tags: ["pendiente", "huerfanos", "deuda", "auditoria", "plan"]
source: "docs/76_PLAN_DE_CIERRE.md"
date_processed: "2026-08-04"
---

# Plan de cierre — inventario de lo que falta

**Fecha:** 4 de agosto de 2026
**Qué es:** la lista única de trabajo pendiente, ordenada para empezar a
implementar. Cruza `75_BIBLIA_TECNICA.md` (§21–§22), `70_INFORME_DE_AUDITORIA_VIVO.md`
(13 iteraciones), `63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md` y `KNOWN_GAPS.md` con un
inventario externo de la API completa de `src/framework/`, `src/engine/`, los 16
escenarios y los 95 documentos.

**Método.** Cada fila de las secciones 1 a 4 se volvió a comprobar contra el
código el 4 de agosto de 2026, con `grep` sobre el árbol y los gates ejecutados.
Donde el documento y el código no coinciden, **gana el código** y la fila lo
dice. Lo que no se pudo comprobar aparece marcado como tal.

**Numeración.** El último `AUD-` usado es **AUD-262**; el siguiente libre es
X

> **Estado (4 de agosto, cierre).** Los lotes A, B y C de §8 están **hechos**
> (AUD-251 a AUD-258), y con las decisiones tomadas también el lote D en lo que
> se decidió: `TiempoBala` (AUD-260), Boss Rush (AUD-261), `BossSpawn`
> (AUD-259) y `requirements.lock` (AUD-262). **GAP-030 y GAP-022 quedan
> cerrados**; GAP-032 baja de cinco mecánicas a una.
>
> **Tercera ronda (AUD-263 a AUD-265).** Los tres huérfanos que quedaban se
> **conservan y se demuestran** en `boss_venado` —la decisión fue que los
> estudiantes los van a usar en la segunda entrega, así que lo que faltaba no
> era menos API sino un sitio donde verlos funcionar—: `EnjambreDeBalas` es la
> nube de esporas de la fase 2, `skill_parry` lo suelta el jefe junto al dash, y
> el venado **habla** en cada cambio de fase y al morir. **GAP-031 y GAP-021
> quedan cerrados**, y GAP-024 se cierra por decisión documentada.
>
> Lo único que sigue vivo es **D7** (aplazado por acuerdo mientras el frente
> paralelo edite `stage_scene.py`) y el Gavilán, que **no se puede completar
> desde aquí**: `src/stages/` es código de estudiantes (invariante 1). Cada
> fila lleva su marca **HECHO (AUD-NNN)**.

---

## 0. Lo que se ejecutó hoy

```
ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/
    → All checks passed!

python scripts/check_dependency_sync.py        → exit 0 (14 dependencias de acuerdo)
python scripts/check_translations.py --ci      → exit 0 (catálogos en orden)
python scripts/check_tmx_coverage.py --ci      → exit 0, con 1 aviso: ScrollZone no lo usa ningún mapa
python scripts/generate_tmx_reference.py --check → exit 0 (STAGE_CREATION.md al día)
python scripts/validate_assets.py              → exit 0 (0 errores, 0 avisos)
python scripts/validate_tmx.py --ci            → exit 0 (16/16 mapas)

pytest (suite completa)  → 5 failed, 3514 passed, 4 skipped en 377,71 s

── después de los arreglos (AUD-251 … AUD-265) ──────────────────────
ruff, los 6 validadores, mypy (21 ficheros)  → todo en verde
grade_stage assets/maps/  → 16 mapas, media 79,9 %   grade_boss → 100 %
pytest (suite completa)   → 2 failed, 3598 passed, 4 skipped
```

De esos dos fallos finales, **uno solo es real**: `test_particion_de_stage_scene`
(D7, aplazado por acuerdo). El otro,
`test_atlas_y_filtro_rapido::test_cabe_en_el_presupuesto_de_60_fps`, es un
presupuesto de milisegundos que **pasa 3 de 3 veces en aislado** y cae cuando la
máquina está ocupada — ver el aviso de entorno de abajo.

De esos tres fallos finales, **ninguno es un defecto nuevo**: `stage_scene.py`
sigue por encima del presupuesto (D7, aplazado por acuerdo);
`test_scroll_forzado_desde_tiled::test_ningun_mapa_entregado_lo_declara`
saltó porque la sala nueva del laboratorio declara `ScrollZone` —se acotó la
prueba a las **entregas**, que es la garantía que importa, y quedó en verde—; y
`test_stage4_1::test_con_la_vision_puesta_tambien` es un presupuesto de
fotograma que **pasa en aislado** y cayó por la carga de la máquina (fichero
del frente paralelo, sin commitear).

Los seis validadores de CI y `ruff` están en verde. Los **cinco fallos de la
suite**, uno por uno:

| Prueba en rojo (medida inicial) | Qué dice | Aquí | Estado |
|---|---|---|---|
| `test_todos_los_tipos_se_usan` | «1 tipos que el cargador reconoce y ningún mapa coloca: `['ScrollZone']`» | **D6** | Verde |
| `test_particion_de_stage_scene` | `stage_scene.py` por encima de 1.500 líneas | **D7** | Aplazado |
| `test_architecture_doc_matches_tree` | «`src/engine/core/experience.py` existe y el árbol de `03_ARCHITECTURE.md` no lo menciona» | **D8** | Verde |
| `test_teaching_tools::test_informa_de_lo_que_encontro` | `preview_tmx.py` no menciona «estación» en su resumen | **D9** | Verde |
| `test_salida_de_consola[check_orphan_systems.py]` | El guardián de AUD-233 no fija su salida de consola fuera de cp1252 | **D10** | Verde |

Ninguno era una regresión de esta revisión: los cinco estaban ya anotados o
venían de trabajo reciente. Lo que faltaba **no era sobre todo una puerta
rota**: era funcionalidad construida y no conectada, y decisiones sin tomar.

> **Aviso de entorno.** Este `.venv` corre Python 3.14, fuera de la matriz de CI
> (3.11/3.12/3.13), y hay otra sesión escribiendo en el repositorio: hay cambios
> sin commitear de un frente paralelo (`docs/46`, `docs/70`,
> `leaderboard_scene.py`, `tests/test_rect_fusionado_suelo_y_pared.py`). Los
> fallos de suite no son atribuibles a un solo frente.
>
> **Y hay dos pruebas sensibles a la carga de la máquina**, las dos de
> presupuesto de fotograma: `test_stage4_1::test_con_la_vision_puesta_tambien` y
> `test_atlas_y_filtro_rapido::test_cabe_en_el_presupuesto_de_60_fps`. Las dos
> **pasan en aislado** y caen si la suite compite con `mypy`, los validadores o
> el otro frente. No es un defecto del código que miden; es que un presupuesto
> de milisegundos medido en una máquina ocupada mide la máquina. Conviene
> saberlo antes de perseguir un fantasma.

---

## 1. Corrección de partida: cuatro afirmaciones de los documentos que hoy son falsas

Antes de la lista de trabajo, lo que hay que dejar de creer. Estas cuatro se
midieron hoy y contradicen a los documentos de referencia:

| Lo que dice el documento | Lo que mide el código hoy |
|---|---|
| `63` §2: «el Gavilán no tiene clase, ni sprites, ni escena: sólo un hueco reservado» | **Falso.** `class BossGavilan(BossBase)` existe en `src/stages/stage3_4_boss_gavilan/boss_gavilan.py:19`, con escena `Stage3_4BossGavilanScene` y mapa `stage3_4_boss_gavilan.tmx` (58,7 KB). `75` §21.3 ya lo llama «clase **parcial** (fase orbital)», que es lo correcto. **Los jefes son cuatro, no tres** |
| `52` §3: «18 eventos huérfanos, ni emitidos ni suscritos»; «`MUSIC_STINGER` sin emisor» | **Desfasado.** `MUSIC_STINGER` se emite desde `boss_base.py:336`; también se emiten ya `SFX_PLAYER_PARRY`, `SFX_UI_GAME_OVER`, `SFX_ENVIRONMENT_SCREEN_SHAKE`, `SFX_BOSS_HIT`, `SFX_BOSS_PHASE_CHANGE` y `SFX_BOSSES_PABURU_EYE_BEAM`. Hoy quedan **9 sin emisor** y **4 emitidos sin oyente** (§2 y §3) |
| `75` §22 y `GAP-032`: «cinco mecánicas de F5 sin invocar» | **Cuatro.** `ScrollForzado` se conectó en AUD-249 como tipo TMX `ScrollZone` (`stage_loader.py:943`, `hazard_system.py:54`). Quedan `TiempoBala`, `EnjambreDeBalas`, `escala_de_fase`, `teletransportar` |
| `75` §21.3 y `GAP-015`: «`stage_scene.py`, 1.405–1.490 líneas» | **1.844 líneas** medidas hoy, contra un presupuesto de 1.500 en `tests/test_particion_de_stage_scene.py:182`. La prueba está en rojo |

---

## 2. Defectos funcionales — algo que existe y no hace lo que promete

Ordenados por lo que un jugador o un estudiante nota primero.

| # | Qué falla | Evidencia | Qué falta exactamente | Estado |
|---|---|---|---|---|
| **D1** | Un diálogo con `give_item:llave` **no entrega el objeto**: emite `ITEM_COLLECTED` y no hay ni un suscriptor en `src/`. Igual `set_flag:x` → `FLAG_SET`: ninguna bandera de mundo se guarda en ninguna parte. `60` §13 documenta las dos acciones como si funcionaran | `dialogue_system.py:282` y `:284` emiten; `grep -rn "subscribe(Events.ITEM_COLLECTED\|subscribe(Events.FLAG_SET" src/` → **cero** | Un manejador atiende a las dos formas de recibir un objeto (recogible del suelo y regalo de diálogo): si está en el catálogo va al inventario, si no al llavero. `GameContext.banderas` guarda las banderas y el checkpoint las baja a `SaveData.zone_flags`, campo que existía y sólo escribían las pruebas | **HECHO (AUD-251)** |
| **D2** | ~~Desbloquear un logro no se ve ni se oye~~ — **la mitad era falsa**: `AchievementSystem._unlock` encola un aviso y `stage_scene.py:1856` lo dibuja. Lo que sí faltaba: el desbloqueo era **mudo**, con `ACHIEVEMENT_UNLOCKED` emitido sin un solo suscriptor | `achievements.py:258-275` | Entrada en la tabla de sonidos de `senales.py`, reutilizando `sfx_ui_stage_complete`. Queda vivo el límite de `docs/52` §6: los SFX sólo suenan dentro de un escenario | **HECHO (AUD-256)** |
| **D3** | El **modo daltonismo se pierde en la ruta GPU**. `GLRenderConfig.colorblind_mode` vale 0 siempre y `App` nunca lo escribe desde `user_settings`; el sombreador `colorblind_frag` está escrito y jamás se ejecuta | `gl_pipeline.py:138` (`colorblind_mode: int = 0`), `:785` (sólo actúa si `> 0`); doc `70` §Iteración 12 lo dejó «anotado» | `app.modo_daltonico_gl()` traduce la preferencia al entero del sombreador y se sincroniza **cada fotograma**, porque Opciones la cambia en caliente | **HECHO (AUD-252)** |
| **D4** | `CONTRIBUTING.md` sigue diciendo **«Crear rama desde `main`»** en el proceso de PR, tres párrafos después de explicar que `main` no existe | `CONTRIBUTING.md:192` contra `CONTRIBUTING.md:74`. AUD-168 corrigió una y no la otra. `CLAUDE.md` §4 lo marca como defecto pendiente | Cambiar `main` por `dev` en la línea 192 | **HECHO (AUD-253)** |
| **D5** | Jugar **ensucia el árbol de git**: `data/score.json` se escribe en runtime y no está en `.gitignore`, aunque `data/inventory.json` sí lo está | `git status` lo lista como `??`; `.gitignore:42` sólo cubre `inventory.json` | Añadir `data/score.json` a `.gitignore` | **HECHO (AUD-253)** |
| **D6** | `ScrollZone`, el tipo TMX nuevo de AUD-249, **no está colocado en ningún mapa**: la mecánica es inalcanzable jugando, y la prueba que AUD-153 dejó puesta está en rojo | `test_todos_los_tipos_se_usan.py:83`; `check_tmx_coverage.py --ci`: «Tipos de objeto que ningún mapa usa (1 de 67): ScrollZone» | Sala 10 nueva en el laboratorio (mapa 280 → 310 baldosas), **acotada**: `parar_en_x` detiene la cámara antes de la salida y el checkpoint va antes del disparador, así el tramo con presión dura lo que dura la sala | **HECHO (AUD-258)** |
| **D7** | `stage_scene.py` a **1.857 líneas** contra 1.500 de presupuesto: `test_particion_de_stage_scene` en rojo | `wc -l`; `tests/test_particion_de_stage_scene.py:182` | Extraer un grupo cohesivo más a `scenes/stage_parts/` (el patrón de AUD-152) | **APLAZADO por acuerdo** — el frente paralelo está editando el mismo fichero; partirlo ahora garantiza conflictos sobre la clase de la que heredan las 26 entregas |
| **D8** | El sistema de experiencia (`src/engine/core/experience.py`, AUD-249) **no aparece en el árbol de `03_ARCHITECTURE.md`**: se añadió código y no se tocó el documento de arquitectura | `test_architecture_doc_matches_tree.py:104` | Añadir la línea al árbol de `03_ARCHITECTURE.md` | **HECHO (AUD-254)** |
| **D9** | `preview_tmx.py` no menciona «estación» en su resumen | `test_teaching_tools.py::test_informa_de_lo_que_encontro` | **Sí lo mencionaba**: lo escribía en cp1252 y quien lo leía esperaba UTF-8, así que llegaba `estaciÃ³n`. Se reconfigura la salida del script y el ayudante de la prueba fija la descodificación. En Linux no se veía porque allí las dos codificaciones coinciden | **HECHO (AUD-254)** |
| **D10** | `scripts/check_orphan_systems.py` —el guardián de huérfanos de AUD-233— **muere en una consola cp1252**: imprime `✅` y no fija su salida. Es el mismo modo de fallo que AUD-177 | `test_salida_de_consola.py[check_orphan_systems.py]` | Fijar la salida a UTF-8 como hacen las demás herramientas | **HECHO (AUD-254)** |

---

## 3. Construido y sin invocar — los huérfanos, con lo que le falta a cada uno

Nada de esto está roto: está escrito, probado por unidad y **desconectado**. La
columna de la derecha es el trabajo real, no «llamar a la función».

| Símbolo | Dónde | Estado medido hoy | Qué falta para conectarlo |
|---|---|---|---|
| ~~`TiempoBala`~~ | `stage/level_mechanics.py` | **HECHO (AUD-260).** Las cuatro piezas: `Action.BULLET_TIME` en `Q`/`R` (mantenida, no conmutada), propiedad de mapa `tiempo_bala` **apagada por defecto** —la decisión de AUD-141 con la estamina, por la misma razón: los dieciséis mapas entregados están calificados—, la llamada por fotograma con el `dt` sin escalar, y una barra de HUD que sólo aparece si el escenario la pide | — |
| ~~`EnjambreDeBalas`~~ | `ecs/bullet_swarm.py` | **HECHO (AUD-263).** La nube de esporas de la fase 2 de `boss_venado`: doce proyectiles en abanico, con sus ángulos calculados de una vez en NumPy. **GAP-032 cerrado** | — |
| ~~`BossPhase.escala` / `escala_de_fase`~~ | `boss_base.py` | **HECHO (AUD-257).** `_aplicar_escala_de_fase()` redimensiona la caja anclada por los pies y el centro —crecer desde la esquina hundía medio jefe en el suelo— y el sprite se escala con ella. `boss_venado` declara `escala=1.25` en su segunda fase: si el patrón no está en el jefe de referencia, no está en el material que se copia | — |
| ~~`BossBase.teletransportar`~~ | `boss_base.py` | **HECHO (AUD-257).** `boss_venado` lo llama en su transición de fase: reaparece en el centro de la arena, lo que hace legible el cambio e impide acorralarlo contra una pared toda la pelea. Sin arena declarada no se mueve | — |
| `LuaScriptEnemy` | `framework/ai/lua_script.py` | Completo y probado **sólo en aislamiento**; ningún enemigo lo usa | Decidir si el guion en Lua entra en el curso. Depende del extra opcional `lupa`. **AUD-022**. Sin decidir |
| ~~`play_voz`~~ | `audio_manager.py` | **HECHO (AUD-263).** El venado habla en cada cambio de fase y al morir. Las tres líneas se sintetizan con el mismo generador que produce **todos** los sonidos del proyecto (`tools/generate_all_assets.py`): no es cableado de mentira, es cómo existe cada sonido de este juego. **GAP-031 cerrado** | — |
| ~~`skill_parry`~~ | `inventory.py` | **HECHO (AUD-263).** Lo suelta `boss_venado`, **junto al dash**: `skill_drop` era un solo `str` —por eso no tenía dueño posible— y ahora acepta también una lista, sin romper la forma antigua que usan las 26 entregas | — |
| ~~`BossSpawn`~~ | `stage/stage_loader.py` | **HECHO (AUD-259).** Declara dónde entra el jefe que nombra su propiedad `boss`, resuelto por el mismo registro de entidades: `BossSpawn` con `boss="BossVenado"` produce la misma entidad que escribir `BossVenado`. Sin `boss`, o con un nombre no registrado, **avisa**. Exento de la regla de AUD-153 con su motivo escrito: sólo tiene sentido en un mapa de jefe, y los tres que hay ya colocan el suyo | — |

### Eventos huérfanos (recuento de hoy, sustituye al de `52` §3)

~~**Los cuatro de juego base**~~ — **HECHO (AUD-255)**: `SFX_PLAYER_HEAL` (sólo
si la salud sube de verdad), `SFX_PLAYER_CROUCH` (en `enter`, que agacharse es
un gesto y no un estado que zumbe), `SFX_ENVIRONMENT_ONE_WAY_PLATFORM` (posarse
en una repisa atravesable era **mudo**: `SFX_PLAYER_LAND` sale por la ruta del
suelo sólido, que es la otra) y `SFX_ENEMIES_PROJECTILE_HIT_WALL`. Ninguno
esperaba una funcionalidad: los cuatro tenían fichero, tabla y subtítulo, y les
faltaba el `emit`. La lista `AWAITING_THEIR_FEATURE` de
`tests/test_audio_wiring.py` quedó vacía.

**Siguen sin emisor, y es una decisión de diseño (5):**
`SFX_BOSSES_GAVILAN_DIVE`, `SFX_BOSSES_GAVILAN_MASK_BEAM`,
`SFX_BOSSES_PABURU_WAVE`, `SFX_BOSSES_RELIC_APPEAR`, `SFX_BOSSES_REY_SPIT`,
`SFX_BOSSES_REY_SPLIT`. Pertenecen a ataques concretos de jefes de estudiantes
(invariante 1): decidir en qué fotograma suena el picado del Gavilán es trabajo
de su autor, no de una auditoría.

**Emitidos y sin oyente:** ~~`ITEM_COLLECTED`, `FLAG_SET`~~ (**HECHO**, D1);
~~`ACHIEVEMENT_UNLOCKED`~~ (**HECHO**, D2). Queda `ACHIEVEMENT_PROGRESS`, que el
propio código declara reservado.

---

## 4. A medias — existe, y no cumple lo que el documento promete

| Elemento | Qué falta | Referencia |
|---|---|---|
| ~~**Boss Rush**~~ | **HECHO (AUD-261), GAP-030 cerrado.** `StageScene` conduce el modo: acredita el combate al caer el jefe, cuenta los golpes desde `PLAYER_DAMAGED` y acumula el tiempo con `dt` sin escalar —para que el tiempo bala no regale puntuación—. La salud se arrastra con `CURACION_ENTRE_COMBATES`, **una constante con nombre**: el arrastre puro deja sin vida en el tercer jefe y nadie ha jugado esto lo bastante para calibrar otra cosa. Queda sólo la superposición de interfaz. La prueba que fijaba el hueco falló al conectarlo, que es para lo que estaba escrita | — |
| **BossGavilan** | Clase **parcial** (fase orbital). Los 22 patrones de ataque de `17_BOSS_SPEC.md` (`BODY_SLAM`, `DIVE_BOMB`, `MASK_BEAM`, `ORBIT_SHRINK`…) no los implementa ningún jefe — la spec describe un diseño anterior que nadie siguió, y `§0` ya lo etiqueta | `63` §2, `75` §21.3 |
| **Stage 0** | Usa 4 de las 11 mecánicas de F5 (liana, tirolesa, bloques rítmicos, viento). Las otras 7 viven en `stage_mecanicas`, que es un laboratorio, no un nivel | `62` B7, `75` §21.3 |
| **`49_AMBIENT_AUDIO`** | «El sistema existe, faltan assets». `rain` y `storm` **declaran** que les falta el fichero en vez de callarse (AUD-145), que es lo correcto — pero el fichero sigue faltando | `51`, `75` §21.3 |
| **Tubería GL** | Completa (doc 74) y **apagada por defecto**: en máquina sin tarjeta el bloom en GPU sale 5× más lento (8,3 ms contra 1,7). No es deuda, es una medición — pero deja `PresentadorGPU` y el sombreador de daltonismo sin ruta viva (→ **D3**) | AUD-148, doc 74 |
| **Trinquete de mypy** | 2 paquetes de ~15 (`src/engine/core`, `src/engine/input`) | `62` B3 |
| **Cobertura** | ~48 %, sin medición por módulo | `62` B4 |
| **Documentación atada al código** | 1 documento de 95 tiene pruebas doc↔código (`docs/60`, 22 pruebas) | `62` B5 |

---

## 5. Decisiones que bloquean — nadie puede implementar esto sin una respuesta

Estas **no son trabajo de programación**: son preguntas abiertas. Implementarlas
sin decidir es lo que produjo `docs/44` diciendo «✅ Complete».

| GAP | Pregunta que hay que responder | Quién decide |
|---|---|---|
| ~~**GAP-024**~~ | **Decidido (AUD-264): la salida (c).** El calificador se queda y `docs/60` §5 documenta la tabla honesta —3 baldosas con entrada natural, 5 con técnica experta— y avisa de que la envolvente asume salto aéreo encadenado. Las otras dos salidas se descartan por lo que cuestan: (a) rebaja notas de trabajo ya calificado, (b) cambia la física de 17 mapas | — |
| ~~**GAP-030**~~ | **Decidido y hecho (AUD-261):** marcador + arrastre real, con curación parcial declarada | — |
| ~~**GAP-031**~~ | **Decidido (AUD-263): se generan.** El repositorio sintetiza todos sus sonidos, así que tres líneas del venado por el mismo camino no son un placeholder falso — son la misma clase de recurso que el resto del audio | — |
| ~~**GAP-021**~~ | **HECHO (AUD-265).** Diez documentos movidos a números libres (77–86) con `git mv`, y **todas** las referencias del repositorio reescritas en la misma pasada. Se conserva el número quien pertenece a una serie: `30`–`33` son `ASSIGNMENT_01`…`04` y partirla habría sido peor que el problema | — |
| ~~**GAP-022**~~ | **Hecho (AUD-262).** El bloqueo era de la herramienta, no del problema: `uv pip compile --python-version 3.11 --universal` resuelve **para** una versión objetivo sin necesitar ese intérprete, y emite marcadores de entorno en vez de un pin único. `numpy` pasa a 2.4.6/2.5.1 según versión y `Pillow` a 12.3.0. Comprobado resolviendo en 3.11, 3.12 y 3.13 | — |
| — | ~~¿Se completa `BossGavilan`?~~ | **Resuelto por invariante, no por decisión:** `src/stages/` es código de estudiantes (invariante 1 de `CLAUDE.md`). Completarlo no es nuestro; que la spec diga la verdad sobre lo que hay, sí — `17_BOSS_SPEC.md` §0 lleva la corrección (AUD-265) |
| — | ~~`skill_parry`~~ | **Decidido (AUD-263): se le da al venado**, junto al dash |
| — | ~~`TiempoBala` y `ScrollZone`: quién los enciende~~ | **Decidido:** propiedad TMX apagada por defecto (AUD-260) y sala acotada del laboratorio (AUD-258) |
| — | ~~`EnjambreDeBalas`: qué jefe lo usa~~ | **Decidido (AUD-263): `boss_venado`**, fase 2 |

**GAP-002** (heurística de X-skip en la colisión) aparece como abierto en
`KNOWN_GAPS.md`, pero el frente paralelo tiene sin commitear
`tests/test_rect_fusionado_suelo_y_pared.py`, que construye el caso temido —una
L de 200 px que es piso y muro a la vez— y documenta que la comparación
`tile.top >= player_rect.centery` **ya no existe**. Verificar y cerrar el hueco
cuando ese trabajo entre.

---

## 6. Documentación desincronizada — el código gana

Ninguna rompe nada hoy; todas engañan a quien programe contra ellas.

* `63` §2 — el Gavilán (ver §1 de este documento).
* `52` — los eventos huérfanos (ver §3 de este documento).
* `75` §21.3 / `KNOWN_GAPS` GAP-032 — cinco mecánicas, son cuatro.
* `75` §22 / GAP-015 — 1.490 líneas, son 1.844.
* `17_BOSS_SPEC.md` — 22 patrones que ningún jefe implementa (**etiquetado**, no
  reescrito: un diseño sin implementar es lo que una spec *debe* contener).
* **Corregido (AUD-254): la §4 del propio doc `63` era en su mayoría falsos
  positivos.** Comprobados uno por uno hoy, **ocho de los doce identificadores
  que declaraba inexistentes sí existen**: `KERNEL_X`, `KERNEL_Y`,
  `umbral_alto` y `umbral_bajo` en `edge_detection.py`; `label_array`,
  `component_sizes`, `bounding_rect` y `local_binary_pattern` en
  `vision_tools.py`; y `_health` (`player.py:345`) y `facing_direction`
  (`player.py:308`) son atributos vivos de `Player`. Siguen siendo ciertas las
  filas de `09_HUD_SPEC.md` (`hurt_display_timer`, `reveal_count`, `Message`
  —la clase es `MessageBox`—), `14_PROFESSOR_DELIVERABLE_MATRIX.md`
  (`AnimationController`, `SpriteSheet`, `OneWay_`) y `damage_amount` de
  `04_PLAYER_SPEC.md`. `23_DATA_SCHEMAS.md` sigue sin volver a medirse.
* `07_STAGE0_DESIGN.md` — mapa 240×14; el real es 100×38.
* `22_API_CONTRACTS.md` / `03_ARCHITECTURE.md` (histórico) — módulos eliminados
  (`utils/spritesheet.py`, `scene/transitions.py`).
* `CONTRIBUTING.md:192` — rama desde `main` (→ **D4**).
* **Conteos que no concuerdan entre sí:** tipos declarables 62 (doc `62`) / 65
  (docs `73`, `75`) / 67 (`check_tmx_coverage` hoy) / 74 (doc `60`); estados del
  jugador 19/25/26 según edición (**el código tiene 26**); `EnemyState` 4
  miembros en `22_API` contra **13** en código; HP del Bruto 6.0 en el GDD contra
  **5.0** en código.

---

## 7. No implementado **por decisión** — no lo «arregles»

Esto está en la lista para que nadie lo tome por deuda:

* **Reverberación por zona:** imposible sobre el mezclador de SDL. Documentado
  en `mixer_buses.py`.
* **Post-procesado en GPU por defecto:** medido 5× más lento sin tarjeta
  (AUD-148).
* **3D:** no. La tubería GL de 479 líneas no es un scene graph; 2.5D sí es
  viable.
* **Traducir los 95 documentos:** no. Bilingüe sólo donde hay lector.
* **Lintear `src/stages/`:** no. Es trabajo de estudiantes (invariante 1 de
  `CLAUDE.md`).
* **gettext:** no. Catálogos JSON propios, razonado en `i18n.py` §F3.1.
* **`sincronizar_salud` (ECS):** hueco vacío a propósito desde F5.12; borrarlo
  rompería entregas.
* **`on_stage_start`, `on_player_landed`, `on_enemy_died`,
  `on_next_trigger_entered`:** ganchos que el estudiante rellena. Correcto que
  estén sin usar.
* **`fog_of_war.reveal_all`:** API pública para autores de escena (docs/46).

---

## 8. Orden de ataque propuesto

Un `AUD-NNN` por lote, verificable por separado, empezando en **AUD-251**.

| Lote | Contenido | Estado |
|---|---|---|
| **A — lo que el jugador nota** | D1 (`give_item`/`set_flag` sin destino), D2 (el logro era mudo), D3 (daltonismo en GPU) | **HECHO** — AUD-251, AUD-256, AUD-252 |
| **B — huérfanos baratos** | `escala_de_fase` y `teletransportar` en el jefe de referencia; los 4 eventos SFX de juego base; `ScrollZone` colocado en el laboratorio (D6) | **HECHO** — AUD-257, AUD-255, AUD-258 |
| **C — higiene y la suite en verde** | D4 (`CONTRIBUTING.md`), D5 (`.gitignore`), D8 (árbol de `03_ARCHITECTURE.md`), D9 (`preview_tmx.py`), D10 (`check_orphan_systems.py`), recuento del README, y las correcciones de §1 | **HECHO** — AUD-253, AUD-254 |
| **D — con decisión previa** | `TiempoBala` (AUD-260), Boss Rush (AUD-261), `BossSpawn` (AUD-259), `requirements.lock` (AUD-262) | **HECHO** — las cuatro decisiones se tomaron y se implementaron. **GAP-030 y GAP-022 cerrados** |
| **D′ — sin decidir todavía** | `EnjambreDeBalas` en un jefe, `skill_parry`, voces (GAP-031), completar o cerrar el Gavilán, GAP-021, GAP-024 | **PENDIENTE** — cada uno espera una respuesta de §5. Implementar antes de decidir es cómo se escribió «✅ Complete» sobre algo que no existía |
| **E — deuda estructural** | D7 (`stage_scene.py`), trinquete de mypy, cobertura por módulo, `requirements.lock` | **PENDIENTE** — D7 aplazado por acuerdo mientras el frente paralelo edite el mismo fichero |

---

## Documentos relacionados

- [[75_BIBLIA_TECNICA.md|La referencia técnica completa]]
- [[70_INFORME_DE_AUDITORIA_VIVO.md|Informe vivo, iteración por iteración]]
- [[63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md|Registro de lo prometido y no implementado]]
- [[62_ESTADO_DEL_PROYECTO.md|Qué hay, qué mejorar, qué falta]]
- `KNOWN_GAPS.md` — el registro de huecos abiertos
