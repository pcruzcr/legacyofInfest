# Auditoría profunda del proyecto — Legacy of InFest

> Fecha: 2026-08-18 · Máquina: i7-6820HQ, Python 3.14.6, GPU de referencia
> **Quadro M2200** (verificada: el benchmark no avisó de renderer incorrecto).
> Método: lectura del árbol, ejecución de calificadores y validadores, y
> mediciones propias (benchmarks, cProfile, batería de auditoría). **No se
> modificó ningún archivo del juego.**
> Complementa a `00_indice.md`, `01_analisis_niveles.md`,
> `02_analisis_escenas_ui_ux.md` y `03_plan_de_mejora.md` (auditoría de
> gameplay/UI/UX). La evidencia ejecutable de cada número está en el
> apéndice.

## Resumen ejecutivo — semáforo por dimensión

| Dimensión | Nota | Veredicto |
|---|---|---|
| Técnico | 9/10 | Arquitectura sólida, deuda baja y declarada con su AUD; ECS híbrido documentado con mediciones |
| Gameplay | 6.5/10 | Motor jugable y rico en mecánicas; contenido incompleto (Gavilán 45 %), 2 hallazgos reales, dureza sin validar |
| Level design | 7/10 | 26 niveles jugables y completables; gaps de checkpoint duros por decisión, sin sesiones humanas |
| Audio | 7/10 | Sistema completo (buses, ducking, polifonía, subtítulos) con 116 pruebas; stinger inaudible y 38 escenas mudas |
| Funcionalidad | 8.5/10 | 5 753 pruebas pasan; **pero el gate de CI `grade_stage stage0 --minimo 100` está rojo (95.4 %)** |
| Eficiencia | 7/10 | Sin fugas, cachés acotadas; draw software en p95 por encima del presupuesto y `import numba` de 0.83 s en frío |
| Eficacia docente | 7.5/10 | Rúbricas ejecutables, 10 demos con teoría+preguntas; sin demo de audio/render/perf y referencia descalibrada |
| Seguridad | 5.5/10 | Motor sin red y TMX blindado (AUD-317); **RCE inherente al modelo docente** + joblib sin cubrir + stage_id en rutas |

---

## 1. Técnico (9/10)

**Volumen:** 745 archivos `.py` (~175 300 líneas): `src/engine` 107 ficheros,
`src/framework` 140, `src/stages` 105 (entregas), `tests` 343 (~74 000 líneas,
el paquete más grande del repo). Punto de entrada: `main.py` →
`src/engine/core/app.py` (`App`, raíz de composición, 806 líneas).

**Arquitectura destacable:**
- **ECS híbrido** (`src/framework/ecs/`): dict-of-dicts por tipo (decisión
  documentada para cientos de entidades), entidades `int` sin reutilizar,
  borrado diferido, componentes `@dataclass(slots=True)`; `Transform` y
  `Salud` son vistas que leen del dueño (66 ns vs 404 ns, medido en el
  docstring). Convive bajo la herencia de las entregas (patrón higuera
  estranguladora) para no romper 26 escenarios.
- **Timestep fijo 1/60** (AUD-390) con tope de 5 pasos y suelo de 20 FPS; el
  salto de 72 px es contrato con los 16 mapas. Tres relojes (dt, dt_mundo,
  unscaled_dt) y `time_scale` por composición de fuentes (AUD-118).
- **Escenas**: `SceneManager` con pila push/pop/replace, sin imports de
  escenas concretas (factories, AUD-018), cola de escenarios por eventos,
  búsqueda de respawn en toda la pila (AUD-186).
- **Render de doble camino**: software (siempre disponible, `Surface.blits()`
  — CPU 0.651 ms vs GPU 1.906 ms a 500 sprites, benchmark del repo) y GPU
  ModernGL (13 shaders, ping-pong de FBOs, bloom/lighting/grading/aberración/
  viñeta/daltonismo/motion blur) con fallback de pérdida de contexto (AUD-437).
- **Dependencias sin muertas**: 13 duras, todas con imports reales (el test
  `test_dependencias_que_se_usan.py` lo vigila); numba/ModernGL/lupa/pydub
  opcionales. Matriz CI 3.11/3.12/3.13.

**Deuda (toda declarada):** `stage_scene.py` 1 315 líneas (mitigado por 14
mixins), `player.py` 1 240, `gl_pipeline.py` 1 180; `destroy()` del
GLRenderer no libera todos los programas (anotado en el código); trinquete
mypy cubre 6 paquetes de ~20 (`framework/ecs` y `framework/stage` fuera, 17 y
27 errores); 13 excepciones silenciosas todas documentadas; 0 TODOs reales
en el motor.

---

## 2. Gameplay (6.5/10)

Medido por la batería `tests/test_auditoria_juego/` (245 pruebas) y el
análisis por nivel en `01_analisis_niveles.md`.

**Fortalezas:** mecánicas de movimiento variadas y con intención
(11 en stage_mecanicas: resorte, viento, fricción, plataformas móviles,
bloques rítmicos, letal temporizada, hundible, agua, sigilo con cono de
visión); jefes de referencia completos (venado 100/100 en rúbrica); sección
rítmica 4-1c con 61 bloques a compás (el reto más "nivel de juego" del
motor); física con salto envolvente documentado; daño, parry, hit-stop,
dificultad y progresión implementados.

**Hallazgos reales (xfail de la batería):**
1. `stage2_1_oficinas`: **0 checkpoints en 3200 px** (gap 3048 px ≈ 33 s de
   reintento al morir).
2. `boss_paburu`: **NextTrigger fantasma en y=-64** (fuera del mapa).

**Debilidades:** jefe Gavilán al 45 % de la rúbrica (solo Fase 1,
`attack_patterns` vacío, GAP-058..065); gaps de checkpoint de stage4_1 y
4-1c de hasta ~2 700 px (decisión AUD-516, pero nunca validada con
jugadores); sin sesiones de prueba humana registradas; curva de dificultad
nunca medida (docs/62 B9).

---

## 3. Level design (7/10)

**Lo medido (21 TMX):** 16 niveles en campaña + 5 laboratorios + 4 jefes.
Salidas alcanzables en 9/12 niveles con salida; 3 falsos negativos del
analizador (no modela one-ways ni mecánicas dinámicas: stage0, hall,
stage_mecanicas) documentados con su excusa en la batería. Densidad de
terreno del 2.8 % (4-1c, plataformas rítmicas) al 39 % (stage1_1).

**Fortalezas:** enseñanza por sala en stage0 (una mecánica por sección);
identidad por bloque (universidad → oficinas/datacenter → piedra/patio →
cementerio); el analizador `level_metrics` (AUD-049) garantiza
completabilidad estática de cada entrega (salida alcanzable, repechos,
plataformas huérfanas).

**Debilidades:** gaps de checkpoint >1200 px (≈13 s) en 6 mapas; dos
secciones de 4-1c sin enemigos (reto 100 % timing); la rúbrica de diseño
castiga arenas de jefe con 0/12 en `design_completable` (5 mapas, incluido
el boss de referencia) — la media publicada mezcla rúbricas incompatibles.

---

## 4. Audio (7/10)

**Sistema:** 7 módulos en `engine/audio` + 2 en `framework/audio`. 16
canales, 4 buses con ducking medido (0.35 en 0.15 s, AUD-144), polifonía con
tope de 3 voces (AUD-280), reloj musical rítmico (AUD-137), atenuación
espacial con suelo crítico (AUD-348/369), subtítulos de sonido con criterio
documentado, toggle de silencio (tecla M), arranque sin tarjeta de sonido
robusto (AUD-089). 40 eventos de audio definidos, 38 cableados; 21/21 TMX
con música. **116 pruebas** en 9 ficheros, incluido el guardián de regresión
`test_audio_wiring.py` (evitó 20 huérfanos, AUD-064).

**Assets:** 162 ficheros (81 wav + 81 ogg, ~69 MB; la pareja ogg son ~6 MB).

**Hallazgos:**
| # | Prioridad | Hallazgo | Evidencia |
|---|---|---|---|
| A1 | ALTA | Stinger de cambio de fase **inaudible**: `MUSIC_STINGER` emitido por `boss_base.py:421` pero no existe ningún asset `*stinger*`; el subtítulo "[Music swells]" anuncia un sonido que no llega | `boss_base.py:421-425`, `senales.py:359-364`, `sound_bank.py:82-83`, `subtitle_overlay.py:62` |
| A2 | MEDIA | `SFX_VOZ_PABURU` se emite (`load_game_scene.py:223`) sin suscriptor ni fichero; el test de huérfanos solo cubre cableado-sin-emisor, no emitido-sin-cablear | `menu_sfx.py:38-51` |
| A3 | MEDIA | Splash/Story/Title cargan `.wav` (~15.9 MB) en vez del `.ogg` disponible (~1.2 MB) que `resolver_pista_de_musica` ya prefiere (AUD-485) | `splash_scene.py:59`, `story_scene.py:95`, `title_scene.py:67-72` |
| A4 | MEDIA | Intensidad "combat" nunca suena: `dynamic_music` busca `_combat`/`_traverse`/`""` y no existe ningún `bgm_*_combat`; el combate sin jefe suena a pista de tránsito | `dynamic_music.py:93-94`, inventario de `assets/music/` |
| A5 | MEDIA | `SoundBank.load_all` carga cada SFX dos veces (wav y ogg → 124 cargas) | `sound_bank.py:43-59` |
| A6 | BAJA | Ambiente climático con rutas `.wav` hardcodeadas (los `.ogg` existen) | `weather_system.py:282-285` |
| A7 | BAJA | 38 escenas mudas: game over, créditos, tienda, inventario, bestiario, 15 laboratorios/demos | inventario `src/engine/scenes/` |

---

## 5. Funcionalidad (8.5/10)

**Lo que funciona hoy (evidencia ejecutada):**
- Suite completa: **5 753 passed, 17 skipped, 2 xfailed** en 754 s
  (medido con el árbol limpio salvo la batería; los 2 fallos flaky
  `test_cajas_de_colision` y `test_la_lluvia_no_se_queda_pegada` son
  preexistentes: pasan sin nuestros cambios, confirmado con stash).
  Ojo: el vigilante `test_la_suite_se_vigila_a_si_misma` se dispara con
  cualquier cambio sin commitear — hoy el árbol trae el rediseño AUD-535
  en curso (hud.py, minimap.py, corazones eliminados, KNOWN_GAPS.md).
- Batería de auditoría: 245 passed / 11 skipped / 2 xfailed.
- Validadores CI: ruff, check_translations, check_dependency_sync: verdes.
- `grade_boss boss_venado`: **100/100**.

**Lo que NO funciona (hallazgo crítico verificado):**
- **Gate de CI `grade_stage assets/maps/stage0 --minimo 100` está rojo**:
  stage0 saca **124/130 (95.4 %)** — pierde 3 pts por una plataforma
  aislada y 3 por "ningún salto exigente" tras el rediseño AUD-491. El
  escenario de referencia no puntúa 100 en su propia rúbrica, y
  `docs/62_ESTADO_DEL_PROYECTO.md:120` aún declara "Stage 0: 130/130".
- 4 de 21 mapas sin salida alcanzable estática (arenas y cenital) que el
  calificador descuenta en `design_completable` aunque avisa que la métrica
  no aplica.

---

## 6. Eficiencia (7/10)

Mediciones propias (Quadro M2200, SDL dummy; comandos en apéndice):

| Métrica | Valor | Presupuesto |
|---|---|---|
| Update de nivel (stage0, software) | mediana 1.21 ms, p95 2.30 ms | — |
| Draw de nivel (stage0, software) | mediana 6.88 ms, **p95 15.39 ms, peor 44.42 ms** | 16.67 ms |
| update+draw | mediana 11.43 ms, **p95 29.40 ms, peor 75.04 ms** | 16.67 ms |
| Carga fría stage0 | **1724 ms** (1175 ms en imports; **829 ms solo `import numba`**) | — |
| Carga tibia stage0 | 22.6 ms (caché) | warm < cold/3 |
| Import en frío de 5 módulos pesados | 2103 ms | — |
| Física 1000 entidades × 60 pasos | 75.7 ms (~1.26 ms/paso, lineal) | — |
| SpriteBatchGPU 8000 sprites | 0.076 ms vs 31.4 ms blits sueltos | — |
| SurfacePool 500 × 32×32 | 1.39 ms vs 0.81 ms Surface crudo (**1.7× más lento**) | — |

**Hallazgos:**
| # | Prioridad | Hallazgo | Impacto |
|---|---|---|---|
| F1 | ALTA | `import numba` de 0.83 s en la primera carga con `ambient_fx` (stage0 frío 1.7 s) | ~1 s del primer cambio de nivel; mover a la splash precalentada (AUD-082) |
| F2 | ALTA | Draw software p95 al 92 % del presupuesto: blits 3 ms + smoothscale 1 ms + bloom 2.5 ms + gradientes 1 ms | Fotogramas perdidos en máquinas sin GPU (las 26 entregas) |
| F3 | ALTA | Bloom CPU 2.5 ms/frame de media (ya a 30 Hz y 1/6 de resolución) | ~15 % del presupuesto solo en el halo |
| F4 | MEDIA | Ledge check O(R²) anidado en el resolutor (`resolucion.py:237`) | Crece con mapas densos |
| F5 | MEDIA | SurfacePool 1.7× más lento que Surface crudo a 500 superficies | Documentar que su beneficio es la presión de GC, no la velocidad |
| F6 | MEDIA | Import en frío 2.1 s (arranque) | Mitigado por el fotograma de cortesía (AUD-449) |
| F7 | BAJA | `minimap._explored_rects` sin poda; `baseline_v1.json` muerto; `font.render` en gizmos de debug | Mantenimiento |

**Lo sano:** sin fugas (cachés con tope de bytes, AUD-087 corrigió una fuga
real de 182 MB/10 s), alocaciones HUD <2 KB/frame (tracemalloc), respawn
reutiliza el mapa parseado (22 ms vs 574 ms), polifonía con tope.

---

## 7. Eficacia docente (7.5/10)

**Lo que funciona:** rúbricas ejecutables — `grade_stage.py` 130 pts en 15
categorías (95 estructurales + 30 de diseño con `level_metrics`),
`grade_boss.py` 100 pts en 10 categorías por AST (no ejecuta entregas);
media medida de los 21 TMX: **76.1 %** (rango 57.7-95.4 %); 10 demos
académicas con teoría + 50 preguntas + desbloqueo progresivo por unidad
(`curriculum.py`, 30 bloques con ruta al código real); material copiable
(stage0 + boss_venado con README académico) y plantillas de estudiante; 70
documentos docentes; 66 GAP con 57 resueltos; validadores que vigilan que la
doc no mienta (`check_doc_symbols`, `check_tmx_coverage`).

**Hallazgos:**
| # | Prioridad | Hallazgo | Evidencia |
|---|---|---|---|
| E1 | **CRÍTICA** | El gate de CI de calificación está rojo: stage0 no llega a 100/100 (95.4 %); docs/62 dice 130/130 | ejecución `--minimo 100` exit 1; `ci.yml`; `docs/62:120` |
| E2 | ALTA | 9 GAP abiertos concentrados en stage4_1 + HUD (GAP-058..066): la zona 4 está declarada incompleta | `KNOWN_GAPS.md` |
| E3 | MEDIA | Sin laboratorio docente de **audio, render/GPU y rendimiento**; Unidad I solo implícita | `scene_registry.py:57-82` |
| E4 | MEDIA | 20-22 de 47 patrones de ataque de `17_BOSS_SPEC` sin ningún jefe que los ejemplifique | `docs/63 §2` |
| E5 | MEDIA | Rúbrica de diseño mezcla arenas con niveles (5 mapas a 0/12 en `design_completable`) | `grade_stage.py:576-587` |
| E6 | BAJA | Entregas de `revisar/` (14 zips) fuera del pipeline de calificación automatizada | `revisar/` |

**Gap por materia:** Gráficas (Unidades I-VI) es fuerte salvo audio/render/
perf; Procesamiento de Imágenes (VII), Visión (VIII) y Patrones (IX) bien
respaldadas. La materia con menos respaldo jugable es **Gráficas en audio,
GPU y rendimiento**.

---

## 8. Seguridad (5.5/10)

**Lo que está excelente:** motor sin red (invariante con test: sin
socket/requests/urllib en `src/engine`+`src/framework` → no hay
exfiltración remota); cargador TMX blindado (AUD-317: rechaza entidades
XML/billion-laughs y travesía de `source=`); `AssetLoader` contiene rutas
relativas al árbol; saves con firma HMAC + validación de esquema + escritura
atómica (`mkstemp`+`fsync`+`os.replace`); saneamiento de correo/apodo/nombre
de partida; suite de seguridad (`test_seguridad_del_motor.py`,
`test_datos_hostiles.py` con 12 entradas hostiles).

**Hallazgos (todos verificados por esta auditoría):**

| # | Severidad | Hallazgo | Escenario |
|---|---|---|---|
| S1 | **CRÍTICA** (inherente al modelo) | El motor importa y ejecuta el código de cada entrega: `importlib.import_module(f"src.stages.{nombre_dir_tmx}")` + `walk_packages`, `--stage/--boss`, plugins con `exec_module` | Un estudiante malicioso entrega `src/stages/<id>/` con código que roba ficheros; el profesor o CI lo ejecutan al cargar el nivel o calificar → RCE total. Mitigación operativa (contenedor/VM al calificar) fuera del código |
| S2 | ALTA | `joblib.load` (pickle) en 2 módulos sin bloqueo, y **el test que prohíbe pickle no lista joblib** (bypass del invariante) | Un `.pkl` malicioso en `assets/models/` (flujo docente documentado) ejecuta código al cargarlo desde la demo de patrones → RCE |
| S3 | ALTA | `stage_id` del TMX (dato del estudiante) construye rutas sin validar: escritura `saves/fantasmas/{stage_id}.json` y lectura `data/dialogues/{stage_id}.json` | TMX con `stage_id` con `..` escribe/lee `.json` fuera del árbol (sobrescribir settings/saves); `test_datos_hostiles.py:19-24` afirma que stage_id "no construye rutas" — desactualizado |
| S4 | MEDIA | Sin límites de tamaño: TMX con `width=100000`, PNG gigante, entidades sin tope → OOM; `validate_tmx.py` usa `ET.parse` sin guarda de entidades → DoS del CI | Un TMX bomba tumba el validador de CI |
| S5 | MEDIA | `web/app.py`: `app.run(debug=True, port=5000)` (debugger Werkzeug → consola Python en el aula) + `render_template_string` con datos de resultados sin sanear (SSTI/XSS) | Otro estudiante en la red alcanza `:5000` → RCE; o inyecta plantilla vía el JSON de calificaciones |
| S6 | MEDIA | `bgm_track` del TMX sin validar en rutas de audio; logs con rutas absolutas del sistema | Intenta cargar `.wav/.ogg` fuera del árbol; los logs revelan estructura de disco |
| S7 | BAJA | `ET.parse` directo en `stage2_2.py:227` (solo TMX del repo); HMAC hardcodeado (anti-corrupción, no anti-trampa, aceptado); `subprocess` en `downloader.py`/`convert_audio.py` sin shell (sin inyección) | Teóricos o aceptados por diseño |

**Conclusión de seguridad:** el peor escenario (S1) es el precio del modelo
docente y está asumido; lo reparable en código es S2 (joblib), S3 (stage_id
en rutas), S4 (límites y guarda XML del validador) y S5 (web). El motor
ofrece una contención notable para ser un proyecto que ejecuta 26 códigos
ajenos.

---

## 9. Prioridades consolidadas (impacto × esfuerzo)

| # | Acción | Dimensión | Prioridad |
|---|---|---|---|
| 1 | Corregir la calibración de stage0 para que el gate CI `grade_stage --minimo 100` vuelva a verde (AUD-491 dejó la referencia descalibrada) | Funcionalidad/Eficacia | CRÍTICA |
| 2 | Cerrar los 2 hallazgos de gameplay (checkpoints de stage2_1; NextTrigger fantasma de paburu) | Gameplay | ALTA |
| 3 | Completar el jefe Gavilán (45 % → rúbrica completa; GAP-058..065) | Gameplay/Contenido | ALTA |
| 4 | Seguridad reparable: cubrir joblib en el test, validar `stage_id`/`bgm_track` antes de usarlos en rutas, límites de tamaño de TMX/imágenes, guarda de entidades en `validate_tmx.py`, `debug=False` en `web/app.py` | Seguridad | ALTA |
| 5 | Eficiencia: mover `import numba` a la splash precalentada; recortar bloom CPU y smoothscale en el camino software | Eficiencia | ALTA |
| 6 | Audio: asset stinger + cablear SFX_VOZ_PABURU (o retirar la emisión); usar `.ogg` en splash/story/title; pista `_combat` para el sistema dinámico | Audio | MEDIA |
| 7 | Mensajes de estado vacío en los 7 menús sin datos; recortar la ventana de entrada de créditos | UI/UX | MEDIA |
| 8 | Demo académica de audio/render/rendimiento (la materia con menos respaldo jugable) | Eficacia | MEDIA |
| 9 | Medir la curva de dificultad y validar los gaps de 4-1 con sesiones reales (AUD-516 pendiente de confirmación) | Gameplay | MEDIA |
| 10 | Refactor de los monolíticos (`player.py` 1240 l., `stage_scene.py` 1315 l.) y ampliar el trinquete mypy a `framework/ecs` y `framework/stage` | Técnico | BAJA |

---

## Apéndice — evidencia ejecutada

```powershell
# Batería de auditoría (niveles + escenas UI/UX)
pytest tests/test_auditoria_juego -q                 # 245 passed, 11 skipped, 2 xfailed
# Suite completa
pytest tests/ -q                                     # 5753 passed, 17 skipped, 2 xfailed (754 s)
# Gate de calificación (rojo)
python scripts/grade_stage.py assets/maps/stage0 --minimo 100   # exit 1: media 95.4 %
python scripts/grade_stage.py assets/maps/ --json    # media 76.1 %, rango 57.7-95.4 %
python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json  # 100/100
# Eficiencia (Quadro M2200, SDL dummy)
python scripts/bench_sprite_batch.py                 # 8000 sprites: blits 31.4 ms, lote GPU 0.076 ms
pytest tests/benchmarks -q --durations=10            # 18 passed (29.9 s); física 1000e: 75.7 ms
pytest tests/test_frame_budget.py tests/test_benchmarks.py -q   # 21 passed
# cProfile stage0 frío: 1724 ms (imports 1175 ms; import numba 829 ms)
# draw stage0: mediana 6.88 ms, p95 15.39 ms, peor 44.42 ms (fotograma 16.67 ms)
# Lint y validadores
ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/   # verde
python scripts/check_translations.py --ci            # verde
python scripts/check_dependency_sync.py              # verde
```