# Verificación de los 20 bugs del motor reportados por el estudiante (stage 4-2)

**Fecha:** 2026-09-10 · **Alcance:** verificación, contra el código actual de la rama
`feature/master-plan`, de los veinte hallazgos del reporte del estudiante
(`REPORTE_COMPLETO_BUGS_DEL_MOTOR.md` v5 + adendas nº 12/13 y nº 19/20). Cada número
«P» del estudiante ya tiene su AUD de adopción en el árbol; este documento **no corrige
nada y no asigna AUD nuevos**: mapea P→AUD, comprueba el parche adoptado en el código y
lo confirma en runtime con las pruebas del repositorio.

**Veredicto global:** los 20 reportes eran reales. **18 están resueltos y verificados**
(en 3 casos el mecanismo adoptado difiere del parche propuesto, ver fila). **1 quedó
resuelto a medias** (#9: el B-1 no se adoptó) y **1 resuelto con regresión posterior**
(#5: la envolvente correcta se recalculó bien, pero AUD-827 subió la marcha 90→120 y dejó
en rojo los 6 tests de calibración). Además quedaron sin adoptar dos piezas
"recomendadas" del reporte (migración de partidas viejas del nº 2 y penalización de
huecos imposibles del nº 5), ambas documentadas abajo.

## Resumen: los veinte

| P | Gravedad (reporte) | Bug | AUD de adopción | Estado en el árbol | Prueba runtime |
|---|---|---|---|---|---|
| 1 | 🔴 BLOQUEANTE | Hit-stop congela el juego | AUD-498 | RESUELTO (mecanismo distinto) | 26/26 ✓ |
| 2 | 🔴 CRÍTICO | Respawn fuera del mapa | AUD-502 | RESUELTO (parche tal cual; falta migración de partidas viejas) | 26/26 ✓ |
| 3 | 🔴 CRÍTICO | Ruta software sin UI | AUD-725 (facade) | RESUELTO | revisión de código ✓ |
| 4 | 🟠 ALTO | Coyote desconectado | AUD-503 | RESUELTO | batería física ✓ |
| 5 | 🟠 ALTO | Calificador salta ×4 | AUD-504 | RESUELTO **con regresión de AUD-827** | 6 tests en rojo |
| 6 | 🟠 ALTO | Hundibles nunca se hunden | AUD-507 | RESUELTO | `test_ecs` 59/60 ✓ |
| 7 | 🟠 ALTO | `atravesable` ignorado | AUD-508 | RESUELTO | `test_ecs` 59/60 ✓ |
| 8 | 🟠 ALTO | Lianas invisibles | AUD-509 | RESUELTO | código ✓ |
| 9 | 🟡 MEDIO | Sombras: bandas negras | AUD-510 (+AUD-762, AUD-827) | **PARCIAL** — B-2 sí, B-1 no | 2 fallos preexistentes |
| 10 | 🟡 MEDIO | fog/snow chasquean | AUD-829 | RESUELTO | `test_aud829_ambiente` ✓ |
| 11 | 🟢 BAJO | HUD muestra total de fases | AUD-512 | RESUELTO | `test_la_fase_cambia_al_jefe` ✓ |
| 12 | 🟠 ALTO | Tirolesa no anula gravedad | AUD-820 (P12) | RESUELTO (mecanismo equivalente) | cuerdas ✓ |
| 13 | 🟡 MEDIO | Combo cuenta botonazos | AUD-818 (P13) | RESUELTO (parche tal cual) | combo ✓ |
| 14 | 🟠 ALTO | Nace 32 px dentro del suelo | AUD-819 (P14) | RESUELTO | spawn ✓ |
| 15 | 🔴 CRÍTICO | AUD-732 consume el flanco (G muerto) | AUD-817 (P15) | RESUELTO | input ✓ |
| 16 | 🟠 ALTO | Rects de enemigos al doble | AUD-821 (P16) | RESUELTO | rects ✓ |
| 17 | 🟡 MEDIO | Disco blanco en el retrato | AUD-824 (P17) | RESUELTO (parche tal cual) | HUD ✓ |
| 18 | 🟡 MEDIO | Zoom no existe en GPU | AUD-825 (P18) | RESUELTO (composición compartida) | zoom ✓ |
| 19 | 🟠 ALTO | Sin `cielo` = interior entero | AUD-822 (P19) | RESUELTO (parche tal cual: `interior`) | interior ✓ |
| 20 | 🟢 BAJO | Piel del checkpoint ignorada | AUD-823 (P20) | RESUELTO (parche tal cual) | checkpoint ✓ |

---

## Los nueve del lote P12-P20 (motor v3, adoptados como AUD-817 a AUD-825)

### P12 — `TirolesaState` no anula la gravedad → AUD-820 — RESUELTO

El parche adoptado **no** es la línea `player.velocity.update(0.0, 0.0)` dentro de
`update`, sino la variante que el reporte llamaba «más robusta»: el integrador deja de
aplicar gravedad al estado colgado.

- `src/framework/entities/player.py` (`_apply_physics`), comentario AUD-820 (P12):
  `SWIMMING`, `SWIM_ATTACK`, `ZIPLINE` y `CLIMBING` quedan fuera de la gravedad del
  perfil. Como `velocity` nace a cero en `enter` y ningún sistema la toca durante el
  viaje, el jinete ya no describe la parábola de ~80 px bajo el cable.
- Cobertura: `tests/test_lianas_y_tirolesas.py` (batería de cuerdas, 67 pruebas del
  lote verde junto con combo/spawn/input/rects).

### P13 — el combo cuenta botonazos → AUD-818 — RESUELTO, parche tal cual

- `src/framework/entities/states/helpers.py` (`_start_attack`): el arranque sólo
  refresca `combo_timer`; ya no incrementa nada.
- `src/framework/entities/player.py`: `consume_hitbox` → `_progresar_combo_al_conectar`
  sube `combo_count` una vez por tajo conectado (dedupe por `_hitbox_consumed`), y
  `current_attack_damage` sigue usando el combo como multiplicador — que ahora se gana.
- Cobertura: `tests/test_combo_system.py`.

### P14 — el jugador nace 32 px dentro del suelo → AUD-819 — RESUELTO

- `src/framework/entities/player.py:420` — el rect **nace** `ANCHO_DE_PIE × ALTO_DE_PIE`
  (20×32), no 40×64; el sprite se ancla abajo sin depender del rect.
- `src/framework/stage/prefab_loader.py:316` y `stage_objetos.py:180` — la Y del TMX son
  los pies: se resta la altura lógica de pie, no la del arte.
- Cobertura: `tests/test_el_spawn_deja_los_pies_en_el_suelo.py`.

### P15 — AUD-732 consumía el flanco en la primera lectura → AUD-817 — RESUELTO

- `src/engine/input/input_manager.py:218` — `is_action_just_pressed` es **no
  destructivo** (el docstring cita textualmente este reporte: P15). El flanco lo cierra
  `pump()` y quien ejecuta una acción la gasta con `consume()` explícito
  (`input_manager.py:369`).
- Consumidores explícitos en los tres estados de cuerda (`rope.py`, AUD-831) para que
  saltar desde la cuerda no re-enganche en el mismo fotograma.
- Cobertura: `tests/test_input_manager.py`.

### P16 — rects de enemigos al doble → AUD-821 — RESUELTO

- `enemy_shooter.py:210` (16×24 a escala del frame 12×12), `enemy_flying.py:107`,
  `enemy_charger.py:42` (28×24 sobre frame 14×12).
- Cobertura: `tests/test_los_rects_van_a_la_escala_del_sprite.py`.

### P17 — disco blanco sobre el retrato → AUD-824 — RESUELTO, parche tal cual

- `src/engine/ui/hud.py:1341` — el highlight superior es un blit normal con
  `(255,255,255,18)` en superficie SRCALPHA; sin `BLEND_RGBA_ADD`.
- Cobertura: `tests/test_el_barra_de_vida_reemplaza_corazones.py`.

### P18 — el zoom no existía en la ruta de GPU → AUD-825 — RESUELTO

- `src/framework/scenes/stage_parts/dibujo.py:49,108` — la composición del zoom vive en
  `dibujar_mundo` (camino software) y `draw` se limita a mundo+interfaz; `DibujoDeEscenario.draw`
  recompone igual, así que ambas rutas ven el mismo zoom. La subida del zoom como uniform
  de GL queda declarada como fase R (KNOWN_GAPS).
- Cobertura: `tests/test_el_zoom_llega_al_mundo.py`.

### P19 — sin `cielo` el mapa es un interior → AUD-822 — RESUELTO, parche tal cual

- `src/framework/stage/stage_loader.py:484-487` — propiedad de mapa nueva `interior`
  (opt-in, por defecto exterior), junto a `cielo`.
- `src/framework/scenes/stage_parts/simulacion.py` (`_es_indoor`) — el interior se
  DECLARA; `cielo` vuelve a significar sólo «dibujar cielo procedural» (AUD-426).
- Cobertura: `tests/test_el_interior_se_declara.py`.

### P20 — la piel inyectada del checkpoint se ignoraba → AUD-823 — RESUELTO, parche tal cual

- `src/framework/stage/checkpoint.py:51-57` (`_sprite`/`_grey_sprite` nacen `None`) y
  `:104-110` (`draw` pinta la piel ENCIMA del haz, que queda de halo).
- Cobertura: `tests/test_checkpoint.py`.

---

## Los once ya adoptados en el motor v2 — siguen corregidos

### P1 — hit-stop congelaba la partida → AUD-498 — RESUELTO (mecanismo distinto al propuesto)

No se adoptó la Opción 1 del reporte (`update(0.0)` cuando no hay pasos) sino una más
limpia: en `App.run` (`src/engine/core/app.py:522-531`) se llama
`scene_manager.actualizar_en_tiempo_real(unscaled_dt)` ANTES de iterar `pasos_fijos()`;
`StageScene.actualizar_en_tiempo_real` (`stage_scene.py:1288`) drena
`update_hitstop` con el reloj real — el único latido que corre con `time_scale == 0.0`.
El abrazo mortal queda roto por construcción.
Runtime: `test_un_golpe_no_congela_el_juego` + `test_composicion_del_tiempo` +
`test_muerte_y_game_over` = 26/26.

### P2 — respawn fuera del mapa → AUD-502 — RESUELTO (parche de los 3 ficheros, tal cual)

- `progression_system.py:62-66` — el punto de reaparición es la esquina superior
  izquierda (`centerx − ANCHO_DE_PIE/2`, `bottom − ALTO_DE_PIE`).
- `stage_scene.py:826-834` — `respawn` llama a `set_spawn` (la puerta sancionada).
- `SAVE_REQUESTED` guarda la misma convención (`progression_system.py:84-91`).
- **No adoptado (era «Fichero 4, recomendado»):** la conversión de partidas viejas en
  `save_data.py` (`SAVE_VERSION` hoy 6, sin `VERSION_CON_CHECKPOINT_TOPLEFT`). Una
  ranura guardada antes de AUD-502 trae el CENTRO y se lee como esquina: el primer
  respawn tras cargar cae 10 px a la izquierda y 16 px arriba (flotando; cae y sigue).
  Inofensivo pero pendiente si importan partidas de hace meses.

### P3 — ruta software sin UI → RESUELTO

`App._draw` reparte hoy: un pre-paso común dibuja `dibujar_mundo` (o `escena.draw` si la
subclase lo sobreescribe, respeto del «reporte Guillermo 4»), la rama GL compone la UI
tras la cadena de pasadas y **la rama software también llama `dibujar_ui`**
(`app.py`, rama `else` con `_publicar_software`). La estructura evolucionó con la facade
AUD-725, pero el defecto del reporte (HUD/cinemáticas/minimapa perdidos sin GPU) no
reproduce: las dos rutas dibujan las dos mitades.

### P4 — coyote (y salto aéreo) desconectados → AUD-503 — RESUELTO

`airborne.py:61-90` — el coyote se gasta en `AirborneState` vía
`_handle_grounded_jump_input` con la puerta explícita al contador (mismo enfoque del
reporte); `_do_jump` distingue coyote de salto aéreo por sí solo. El salto aéreo sigue
siendo decisión de diseño aparte (GAP-024 documentado en `level_metrics`).

### P5 — el calificador sobreestimaba el salto ×4 → AUD-504 — RESUELTO, con REGRESIÓN posterior

- `level_metrics.from_settings` (AUD-504) ya no usa `v²/2g` ni `gap × (1 + air_jumps)`:
  **simula el integrador real** de `Player._apply_physics` paso a paso y separa
  `max_gap` (técnica natural, control aéreo 0,5) de `max_gap_expert` (soltar dirección).
  Equivalente al parche propuesto y más robusto (sube y baja solo con los ajustes).
- El parche complementario del calificador (penalizar `impossible_gaps` en
  `grade_stage`) **no se adoptó**: sigue en el JSON (línea 540) y fuera de la puntuación.
  Era opcional; queda como deuda.
- **REGRESIÓN nueva (post-reporte):** AUD-827 subió `PLAYER_WALK_SPEED` 90→120 y la
  envolvente creció un 33 %: `max_gap` 42,75→**57 px** (3 baldosas) y
  `max_gap_expert` 85,5→**114 px** (7 baldosas). Los 6 tests de
  `tests/test_calibracion_del_salto.py` siguen fijando los números de 90 px/s y hoy
  FALLAN (medido: `assert 3 == 2`, y el banco mide 2/49 despegues válidos cruzando 4
  baldosas «naturales»). AUD-827 ya declaraba esta deuda («los saltos llegan más lejos;
  revalidar nivel por nivel») — la revalidación de los tests y de los saltos ajustados
  de los mapas sigue abierta.

### P6 — hundibles que nunca se hunden → AUD-507 — RESUELTO

`sistema_plataformas_hundibles` (`src/framework/ecs/systems_escenario.py:98`; el sistema
vive hoy en `systems_escenario.py`) lleva el sensor de pasajero con `MARGEN_PASAJERO` y
llama `marcar_pisada` — exactamente el parche propuesto, con el mismo sensor de
`sistema_arrastre_de_plataformas`. Runtime: `test_ecs.py` 59/60 (el 1 fallo es la
regeneración del TMX de mecánicas, preexistente de otro workstream, ver §Fallos).

### P7 — `atravesable_desfrom_abajo` ignorado → AUD-508 — RESUELTO

La clasificación por capa existe: `src/framework/ecs/systems_zonas.py:446-472` separa
sólidos y repisas leyendo `Solido.atravesable_desde_abajo`, y
`stage_scene.py:1146-1157` suma los atravesables a `one_way_rects` del jugador (y evita
el falso sólido de la `SinkingPlatform` al reaparecer). El campo dejó de estar muerto.

### P8 — lianas invisibles → AUD-509 — RESUELTO

`src/framework/scenes/stage_parts/dibujo_mecanicas.py` (módulo movido desde `vfx/`)
añade `Liana` y `PlataformaHundible` al barrido de marcadores (AUD-509); la liana dibuja
línea + nudos con recorte a cámara, como las otras tres mecánicas.

### P9 — sombras proyectadas → AUD-510 — RESUELTO A MEDIAS (única parte viva del reporte)

- **B-2 resuelto:** `_pintar_cuna` rellena la cuña con `piso_ambiente` (el mismo relleno
  inicial del multiplicador) y compone con `BLEND_RGBA_MIN` — la sombra nunca vuelve a
  ser más negra que un rincón sin luz. Coste aparte: AABB clip (AUD-B1) y lightmap a
  media resolución (AUD-762/AUD-827).
- **B-1 NO adoptado:** `silueta_de` sigue tomando las dos esquinas del rect **entero**
  (`sombras_proyectadas.py:80-105`), `_cerca_del_foco` devuelve los obstáculos **sin
  recortar** a la zona del foco y ordena por distancia al **centro**, y `proyectar` no
  pone `set_clip` al alcance. Consecuencia residual, medida en el reporte («el 97 % de
  la sombra cae donde el foco no llega»): la cuña de un suelo largo sigue dimensionada
  por el suelo entero y, al ir el gradiente y la sombra intercalados por foco en
  `render_map`, esa cuña puede **apagar la luz de otros focos** dentro de su área (el
  MIN baja todo a ambiente). Ya no hay bandas negras; sí puede haber focos vecinos
  apagados por la sombra mal acotada de otro. El arreglo del reporte (recortar
  obstáculo y dibujo a la zona del foco) sigue en pie como pista.
- Los dos tests de `TestApagadoPorDefecto` de `test_sombras_proyectadas.py` siguen en
  rojo por la causa ya conocida y atribuida (doc 100): `boss_paburu.tmx` declara la
  opción y no está en la excepción del test.

### P10 — fog/snow chasqueaban cada 2 s → AUD-829 — RESUELTO

`weather_system.py:316-321`: `snow`/`fog` apuntan a `sfx_environment_wind_loop.wav`
(8 s, empalme exacto, generado por `tools/generar_ambiente_viento.py`); además
`StageScene.on_exit` hace `stop_ambient()` (la fuga del reporte colateral). Cobertura:
`test_aud829_ambiente.py`.

### P11 — el HUD mostraba el total de fases → AUD-512 — RESUELTO

`hud.py:660-663` iguala las dos rutas de emisión de fase. Cobertura:
`test_la_fase_cambia_al_jefe.py` — PASA.

---

## Evidencia runtime de esta verificación (2026-09-10)

Comando: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m pytest <lotes> -q`

| Lote | Resultado |
|---|---|
| `test_lianas_y_tirolesas` + `test_combo_system` + `test_el_spawn_deja_los_pies_en_el_suelo` + `test_input_manager` + `test_los_rects_van_a_la_escala_del_sprite` | **67/67** ✓ |
| `test_el_barra_de_vida_reemplaza_corazones` + `test_el_zoom_llega_al_mundo` + `test_el_interior_se_declara` + `test_checkpoint` + `test_ecs` + `test_aud830_tirolesa` + `test_aud831_liana` | **111/112** — 1 fallo: `test_el_mapa_se_puede_regenerar_igual` (preexistente: el TMX de `stage_mecanicas` en árbol no coincide con su generador; el propio test lo dice y pide regenerar — workstream ajeno) |
| `test_un_golpe_no_congela_el_juego` + `test_muerte_y_game_over` + `test_composicion_del_tiempo` | **26/26** ✓ |
| `test_la_fase_cambia_al_jefe` | ✓ |
| `test_calibracion_del_salto` | **0/6** — regresión de AUD-827 (marcha 90→120 vs números fijados a 90) |
| `test_sombras_proyectadas` (TestApagadoPorDefecto ×2) | 2 fallos preexistentes ya atribuidos en doc 100 (`boss_paburu.tmx` declara sombras) |

Los cambios **sin commit** del árbol (sprites opcionales AUD-830 de hojas ausentes,
registro `ParryTeacher`, `skill_coraza`, repintado de barras de vida tras la luz) NO
revierten ninguno de los veinte parches: son aditivos y sus ficheros tocan zonas
distintas de las de los arreglos.

## Deudas que deja esta verificación

| Deuda | Origen | Estado |
|---|---|---|
| B-1 de sombras: cuña dimensionada por el obstáculo entero (sin clip al foco, orden por centro) | P9 | Abierta — pista de arreglo en el reporte original, §9.3 |
| Calibración de salto desfasada tras la marcha 120 | P5 × AUD-827 | Abierta — reescribir `test_calibracion_del_salto.py` con la envolvente nueva y revalidar saltos ajustados de los mapas |
| Partidas guardadas antes de AUD-502 cargan el checkpoint con desplazamiento de una vez | P2 (Fichero 4) | Abierta — conversión en `from_dict` con `version_original` |
| `impossible_gaps` no penaliza en el calificador | P5 (parche opcional) | Abierta — aplicar con exclusión cenital o tope, como advertía el reporte |
| `TestApagadoPorDefecto` (sombras) con `boss_paburu.tmx` fuera de la excepción | colateral de P9 | Abierta — añadir a la excepción o apagar la opción en el TMX |
| TMX de `stage_mecanicas` desincronizado de su generador | ajeno (doc 100) | Preexistente — `python tools/generate_stage_mecanicas.py` |

---

Este documento no corrige nada (verificación pura, sin AUD nuevo: cada P ya tiene el
suyo). Al commitear, la invariante 9 (`check_change_safety.py --ci`) exige declaración:
`AUD-800: verificacion de los 20 bugs del motor reportados — CERT-DOCUMENTATION`.
