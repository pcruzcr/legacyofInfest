# KNOWN GAPS - Legacy of InFest

Formato: docs/23_DATA_SCHEMAS.md sec 8

Nunca borrar entradas - marcar como resueltas.

## ~~[GAP-001] EnemyFlying modos Bézier y patrol~~ *(Resuelto)*

- **File:** `src/framework/entities/enemy_flying.py`
- **Phase:** 6 (deferred to Phase 8)
- **Reason:** Requiere CurveTools que se implementa en Fase 8
- **Resolution:** Implementado en `src/framework/processing/curve_tools.py` con
  Catmull-Rom spline + waypoint patrol. Activado vía `flight_mode="bezier"` o
  `flight_mode="patrol"`.

## ~~[GAP-020] La suite no se pudo ejecutar durante la auditoría AUD-168/165~~ *(Resuelto)*

- **File:** N/A (entorno)
- **Phase:** auditoría 2026-08-02, iteración 1
- **Reason:** El entorno donde se hizo la iteración 1 no tenía acceso a PyPI ni
  un intérprete ≥ 3.11, así que `pytest`, `ruff`, `mypy` y los validadores de
  `scripts/` no se ejecutaron. Los hallazgos AUD-168 y AUD-169 son estáticos
  —parseo AST y comprobación de existencia de ficheros— y las correcciones sólo
  tocan documentación más un fichero de prueba nuevo, pero **nadie ha visto la
  suite en verde después**.
- **Resolution:** Ejecutado el 2026-08-02 en la máquina con el `.venv`
  (Python 3.14.6, iteración 4). Los doce gates corrieron de verdad. Resultado:
  `pytest` 2.872 recogidas / 2.870 pasan / 1 omitida, `ruff` «All checks
  passed», `mypy` «Success: no issues found in 18 source files», los seis
  validadores de `scripts/` en verde, `grade_stage` 78,7 % de media sobre 17
  mapas y `grade_boss` 100 %. Ejecutarlos destapó tres defectos que ningún
  análisis estático podía ver —AUD-174, AUD-175 y AUD-176—, corregidos en esa
  misma iteración. Detalle en `docs/70_INFORME_DE_AUDITORIA_VIVO.md`.

## ~~[GAP-022] `requirements.lock` no se puede instalar en Python 3.13~~ *(Resuelto)*

- **File:** `requirements.lock`
- **Phase:** auditoría 2026-08-02, iteración 3
- **Reason:** El fichero fija `numpy==1.26.4`, la última 1.x, cuyas ruedas
  llegan hasta Python 3.12. El CI declara la matriz 3.11/3.12/3.13. No se
  retocaron los pines a mano porque el propio fichero dice que se regenera con
  `pip-compile` y hand-editarlo es lo que produjo el lock imposible de AUD-008.
  El CI no usa este fichero —instala con `pip install -e ".[dev]"`—, así que
  no bloquea, pero cualquiera que lo siga en 3.13 se estrella.
- **Resolution:** Con el `pyproject.toml` ya corregido (AUD-173), regenerar en
  la máquina destino:
  `pip install pip-tools && pip-compile --output-file=requirements.lock pyproject.toml`
- **Ampliación (2026-08-02, iteración 4):** el fichero también fija
  `Pillow==12.2.0`, que AUD-176 acaba de dejar fuera del rango soportado por
  acumular diez vulnerabilidades publicadas. Son ya dos pines caducos, así que
  regenerar es más urgente que antes. **No se regeneró aquí a propósito:** el
  único intérprete disponible en esta máquina es 3.14, que está fuera de la
  matriz declarada (3.11/3.12/3.13), y `pip-compile` produce un lock atado al
  intérprete que lo genera. Regenerarlo desde 3.14 cambiaría un lock imposible
  en 3.13 por otro imposible en 3.11. Hay que hacerlo desde 3.11.

- **Resolution (AUD-262, 2026-08-04):** no hacía falta el intérprete 3.11.
  `uv pip compile --python-version 3.11 --universal` resuelve **para** una
  versión objetivo sin ejecutarla, y emite marcadores de entorno en vez de un
  pin único, así que un solo fichero sirve para las tres de la matriz. El
  bloqueo de la ampliación de arriba era real —`pip-compile` sí ata el lock al
  intérprete que lo corre— pero era una limitación de la herramienta, no del
  problema.

  Los dos pines caducos desaparecen: `numpy==1.26.4` pasa a 2.4.6 en `<3.12` y
  2.5.1 en `>=3.12`, y `Pillow==12.2.0` a 12.3.0, el mínimo que fijó AUD-176.

  Comprobado ejecutando la resolución del propio lock contra las tres versiones
  del CI:

  ```
  uv pip compile requirements.lock --python-version 3.11  → exit 0
  uv pip compile requirements.lock --python-version 3.12  → exit 0
  uv pip compile requirements.lock --python-version 3.13  → exit 0
  ```

  Sigue sin editarse a mano, que es la regla que AUD-008 dejó escrita con
  sangre: la cabecera del fichero lleva la orden exacta que lo regenera.

## ~~[GAP-023] 22 mutantes vivos en `mixer_buses.py` y `bloques.py`~~ *(Resuelto)*

- **File:** `src/engine/audio/mixer_buses.py`, `src/framework/stage/bloques.py`
- **Phase:** auditoría 2026-08-02, iteración 4
- **Reason:** `scripts/mutation_check.py --ci` pudo ejecutarse por primera vez
  —lo impedían AUD-170 y AUD-177— y dio 56,0 % en los dos módulos (el tercero,
  `music_clock.py`, sale 72,0 % y pasa). Son 22 cambios en el código que la
  suite **no detecta**. Los dos patrones dominantes:
  - constantes sin comprobar: `0.5 → 0`, `0.35 → 0`, `0.15 → 0` en
    `mixer_buses.py:71,75,77` — se puede poner a cero el volumen de tres buses
    de audio sin que falle nada;
  - fronteras `<` frente a `<=`: ocho mutantes de comparación repartidos entre
    los dos módulos, el error clásico de un píxel o un fotograma de más.
  No se corrigió en esta iteración porque son 22 pruebas por escribir y el
  protocolo (`docs/69_PROMPT_AUDITORIA_MAESTRO.md` §5) prohíbe abrir dos
  frentes a la vez. La lista completa está en
  `docs/70_INFORME_DE_AUDITORIA_VIVO.md`, iteración 4.
- **Resolution:** AUD-181. 26 pruebas nuevas en `tests/test_bloques.py` y
  `tests/test_buses_de_audio.py`. `mixer_buses.py` sube de 56,0 % a **88,0 %**
  y `bloques.py` de 56,0 % a **96,0 %**.

  Los **4 mutantes que siguen vivos son equivalentes** —cambian el código sin
  cambiar lo que hace— y se dejan documentados, no tapados: `mixer_buses.py`
  144, 164 y 177, y `bloques.py` 204. Cada uno se comprobó ejecutando el
  original y el mutante sobre miles de secuencias aleatorias de llamadas y
  comparando la salida: 0 diferencias en los cuatro. El razonamiento completo
  está en los docstrings de `TestLoQueLaMutacionDestapo` de los dos ficheros.

  El hallazgo de fondo no fueron las constantes sino **dos pruebas que pasaban
  por la razón equivocada**: `test_no_se_empuja_a_traves_de_una_pared` y
  `test_un_bloque_no_empuja_a_otro_a_traves` dejaban al jugador quieto
  mientras el bloque se alejaba, así que el contacto se perdía y el bloque se
  paraba solo antes de tocar nada. La rama de colisión que decían cubrir no
  se ejecutaba nunca y se podía invertir entera sin que fallaran.

## ~~[GAP-021] Números de documento duplicados en `docs/`~~ *(Resuelto)*

- **File:** `docs/00_MASTER_INDEX.md`
- **Phase:** auditoría 2026-08-02, iteración 1
- **Reason:** Los prefijos 28, 29, 30, 31, 32, 33, 34, 52 y 67 los usan dos
  ficheros distintos cada uno (`28_DECISION_LOG.md` y `78_SAMPLE_SYLLABUS.md`,
  `67_CURVA_DE_DIFICULTAD.md` y `86_ESPECIFICACION_DE_NIVELES_Y_JEFES.md`…).
  El índice se refiere a los documentos por número, así que «el 67» es
  ambiguo.
- **Resolution (AUD-265, 2026-08-04):** decisión tomada —renumerar— y hecha de
  golpe, que es la única forma en que no rompe nada: renombrar y arreglar las
  referencias en el mismo cambio.

  **Qué se movió y qué no.** De cada par se queda el que pertenece a una serie
  coherente y se mueve el otro, a números libres a partir del 77:

  | Antes | Ahora | Se queda con el número |
  |---|---|---|
  | `00_SYLLABUS_ALIGNMENT_AUDIT` | `77_…` | `00_MASTER_INDEX` |
  | `28_SAMPLE_SYLLABUS` | `78_…` | `28_DECISION_LOG` |
  | `29_TA_GUIDE` | `79_…` | `29_GIT_WORKFLOW_AND_STANDARDS` |
  | `30_TICKET_BACKLOG` | `80_…` | `30_ASSIGNMENT_01_STAGE_DESIGN` |
  | `31_RISK_REGISTER` | `81_…` | `31_ASSIGNMENT_02_BOSS_DESIGN` |
  | `32_ENVIRONMENT_SETUP_GUIDE` | `82_…` | `32_ASSIGNMENT_03_LAB_EXERCISES` |
  | `33_SCOPE_ADJUSTMENT` | `83_…` | `33_ASSIGNMENT_04_FINAL_PROJECT` |
  | `34_EDUCATIONAL_ROADMAP` | `84_…` | `34_CLASS_MATERIALS` |
  | `52_MULTIDISCIPLINARY_AUDIT` | `85_…` | `52_EVENT_MAP` |
  | `67_ESPECIFICACION_DE_NIVELES_Y_JEFES` | `86_…` | `67_CURVA_DE_DIFICULTAD` |

  El criterio: `30`–`33` son la serie `ASSIGNMENT_01`…`04` y partirla dejaría
  cuatro entregas con numeración salteada, que es peor que el problema. `00` es
  el índice por definición. En los demás pares se movió el documento con menos
  referencias cruzadas, para minimizar el texto tocado.

  Se renombró con `git mv` —el historial de cada fichero sigue completo— y se
  reescribieron **todas** las referencias del repositorio en la misma pasada.
  Verificado con `tests/test_rutas_de_los_documentos.py`, que exige que cada
  ruta citada en un documento exista y que cada `docs/*.md` esté en el índice:
  110 pasan.

  **Lo que este cambio no arregla:** material impreso o enlaces externos que
  citen «el 30» seguirán apuntando al documento equivocado. No hay forma de
  evitarlo renumerando; es el coste que la entrada anterior describía y que la
  decisión acepta.

## ~~[GAP-002] Collision rect depth usada para X-skip heurística~~ *(Resuelto)*

- **File:** `src/framework/entities/player.py` (línea 582)
- **Phase:** FIX-2
- **Reason:** La heurística `tile.top >= player_rect.centery` asume que rectos
  con top debajo del centro del jugador son "pisos". Con rectos de colisión
  fusionados (FIX-1), un recto de plataforma de 16px de alto se salta
  correctamente en X cuando el jugador está parado encima. Sin embargo, si un
  recto de colisión es anormalmente alto (ej. merged que abarca piso + pared),
  el skip podría fallar. Hasta ahora no hay casos que rompan esta heurística.
- **Nota:** Si en el futuro se crean stage TMX con rectos de colisión que
  mezclen piso y pared vertical en un solo objeto, esta heurística podría
  necesitar refinamiento (ej. dividir rectos por pendiente o etiqueta).
- **Resolution:** La heurística `centery` desapareció con AUD-334: el resolutor
  de mundo compartido (`src/framework/physics/resolucion.py:140-141`) la
  sustituyó por el umbral de solape vertical `v_overlap <= 2`, que distingue
  «estoy de pie encima» de «me estoy dando contra ello» sin mirar la altura
  del recto. El caso temido —un rect fusionado piso+pared— tiene prueba propia
  (`tests/test_rect_fusionado_suelo_y_pared.py`). El código del jugador ya no
  contiene `centery` ni la heurística X-skip.

## ~~[GAP-003] SoundBank no conectado — sin llamadas a `play_sfx()`~~ *(Resuelto)*

- **File:** Todo el codebase
- **Phase:** 3
- **Reason:** `SoundBank` fue implementado en `src/engine/audio/sound_bank.py` pero
  nunca se invoca `sound_bank.load()` ni `play_sfx()` en ningún Scene o Entity.
  Los nombres de SFX en `ASSET_BIBLE.md` §12 fueron limpiados contra disco pero
  no hay código que los reproduzca.
- **Resolution:** Integrado vía EventBus: `SoundBank.load_all()` escanea `assets/sfx/`
  recursivamente en `AudioManager.__init__()`. 15 eventos SFX definidos en
  `Events` class, emitidos desde entidades y escuchados por `StageScene.on_enter()`
  que mapea evento → filename y llama `self.audio.play_sfx()`. Ver
  `src/engine/core/events.py`, `src/engine/audio/sound_bank.py`,
  `src/framework/scenes/stage_scene.py`.

## ~~[GAP-004] `background_zone` implementado en StageLoader pero ausente en Stage 0 TMX~~ *(Resuelto)*

- **File:** `src/framework/stage/stage_loader.py` (línea 112)
- **Phase:** 4
- **Reason:** `StageLoader.load()` lee `background_zone` del TMX y carga fondos
  parallax desde `assets/backgrounds/{zone}/`. El Stage 0 TMX no tiene esta
  propiedad, por lo que corre sin fondos parallax (usa solo capas de tiles).
- **Resolution:** Agregar `background_zone` al TMX de Stage 0 cuando los assets
  de fondo definitivos estén listos. El soporte en StageLoader ya existe.
- **Verificado:** 2026-08-02, auditoría AUD-184 — ejecutado contra el código actual. `assets/maps/stage0/stage0.tmx` **sí declara** `background_zone`; los fondos parallax cargan.

## ~~[GAP-005] Colisión Y-primero causa wall-climb/teleport~~ *(Resuelto)*

- **File:** `src/framework/entities/player.py` (resuelto con axis-separado)
- **Phase:** FIX-3
- **Reason:** La resolución de colisión procesaba Y primero (merged en FIX-1),
  tratando cualquier recto solapado como piso. Al caminar contra una pared, la
  pared elevaba al jugador tile por tile hasta que atravesaba el muro.
- **Resolution:** Se cambió a resolución axis-separada: X → resolver X → Y →
  resolver Y. `_apply_physics` solo aplica gravedad (sin movimiento). La Y usa
  `prev_bottom <= tile.top + 1` para determinar landing. Las plataformas one-way
  usan `prev_bottom = player_rect.bottom - velocity.y * dt` para reconstruir la
  posición pre-integración.
- **Verificado:** 2026-08-02, auditoría AUD-184 — ejecutado contra el código actual. `player.py::_resolve_collision` documenta y aplica «True axis-separated AABB resolution»: integra X, resuelve X, integra Y, resuelve Y con `prev_bottom`.

## ~~[GAP-006] PlayerStates referencia `_pending_jump` sin atributo en Player~~ *(Resuelto)*

- **File:** `src/framework/entities/player_states.py`, `player.py`
- **Phase:** FIX-4
- **Reason:** `_airborne_update` asigna `player._pending_jump = True` y
  `player._pending_jump_timer`, pero estos atributos no existían en `Player.__init__`.
  Funcionaba por Python dinámico, pero violaba la explícitud del contrato.
- **Resolution:** Se agregaron `_pending_jump: bool = False` y
  `_pending_jump_timer: float = 0.0` a `Player.__init__`. El timer de 8 frames
  (≈133ms) evita bounce-off en plataformas one-way al amortiguar el input de salto.
- **Verificado:** 2026-08-02, auditoría AUD-184 — ejecutado contra el código actual. `Player(...)` recién construido expone `_pending_jump = False` y `_pending_jump_timer = 0.0`.

## ~~[GAP-007] StageLoader spawn point: TMX Y=feet convertido como top-left~~ *(Resuelto)*

- **File:** `src/framework/stage/stage_loader.py`
- **Phase:** FIX-5
- **Reason:** TMX §6.1 especifica que Y del PlayerSpawn = posición de los PIES,
  pero `StageLoader` leía `pygame.Vector2(obj.x, obj.y)` tratándolo como top-left.
  El bug de colisión Y-primero (GAP-005) enmascaraba esto al teleportear al
  jugador hacia arriba. Con la colisión axis-separada, el jugador nacía 32px
  dentro del piso y caía al vacío.
- **Resolution:** Se cambió a `pygame.Vector2(obj.x, obj.y - 32)`. El test
  `test_spawn_point_matches_tmx` se actualizó de `y=176` a `y=144`.
- **Verificado:** 2026-08-02, auditoría AUD-184 — ejecutado contra el código actual. `stage_loader.py:907` → `pygame.Vector2(obj.x, obj.y - 32)`.

## ~~[GAP-008] Timer HUD usa TTF font, no spritesheet de píxeles~~ *(Resuelto)*

- **File:** `docs/09_HUD_SPEC.md`, `src/engine/ui/hud.py`
- **Phase:** Documentación
- **Reason:** El HUD renderiza el timer con `pygame.font.Font("PixeloidSans.ttf")`,
  pero la especificación §5.4 documentaba un spritesheet `fonts/hud_digits.png`.
  El TTF produce mejor calidad a costa de no usar el sprite pipeline.
- **Resolution:** Se actualizó `09_HUD_SPEC.md` §5.2 y §5.4 para reflejar el uso
  de TTF font, posición ajustada a X=264, Y=24, ancho 54px.
- **Verificado:** 2026-08-02, auditoría AUD-184 — ejecutado contra el código actual. `docs/09_HUD_SPEC.md` documenta «TTF — `assets/fonts/game.ttf`»; no queda rastro de `hud_digits.png`.

## ~~[GAP-009] MessageBox reposicionado de Y=196 (abajo) a Y=0 (arriba)~~ *(Resuelto)*

- **File:** `docs/09_HUD_SPEC.md`, `src/engine/ui/message_box.py`
- **Phase:** UI Fix
- **Reason:** El mensaje tutorial se movió de la parte inferior de la pantalla
  (Y=196) a la superior (Y=0) para evitar solapamiento con el HUD de salud/timer.
- **Resolution:** Se actualizó `09_HUD_SPEC.md` §2, §2.1, §7.2 con la nueva
  posición y layout. Los elementos del HUD (portrait, hearts, timer) se
  desplazaron 14px hacia abajo (Y=16 base).
- **Verificado:** 2026-08-02, auditoría AUD-184 — ejecutado contra el código actual. Ni `message_box.py` ni `09_HUD_SPEC.md` mencionan ya la Y=196.

## ~~[GAP-010] Action enum documentado como str, Enum pero implementado como Enum simple~~ *(Resuelto)*

- **File:** `docs/22_API_CONTRACTS.md`, `src/engine/input/action_map.py`
- **Phase:** Documentación
- **Reason:** El contrato API declaraba `class Action(str, Enum)` con miembros
  string, pero la implementación usa `class Action(Enum)` con `auto()`. Además
  el contrato omitía los miembros MOVE_UP, MOVE_DOWN, DASH, y nombraba
  `DEFAULT_KEYBOARD_BINDINGS` en vez de `DEFAULT_KEY_BINDINGS`.
- **Resolution:** Se actualizó `22_API_CONTRACTS.md` §3.1 para reflejar la firma
  real.
- **Verificado:** 2026-08-02, auditoría AUD-184 — ejecutado contra el código actual. `action_map.py:14` y `22_API_CONTRACTS.md:266` declaran los dos `class Action(Enum)`.

## ~~[GAP-011] SoundBank API incompleta en contrato~~ *(Resuelto)*

- **File:** `docs/22_API_CONTRACTS.md`, `src/engine/audio/sound_bank.py`
- **Phase:** Documentación
- **Reason:** El contrato API sólo documentaba `__init__(asset_loader)` y
  `get(name) -> Sound`. La implementación tiene `load_all()`, `load(name, path)`,
  `play(name, loops, volume)`, y `get` retorna `Sound | None`.
- **Resolution:** Se actualizó `22_API_CONTRACTS.md` §4.1 con todos los métodos
  y tipos correctos.
- **Verificado:** 2026-08-02, auditoría AUD-184 — ejecutado contra el código actual. `22_API_CONTRACTS.md` documenta `load_all`, `load`, `play` y `get`.

## ~~[GAP-012] AssetLoader.load_image parámetros faltantes en contrato~~ *(Resuelto)*

- **File:** `docs/22_API_CONTRACTS.md`, `src/engine/utils/asset_loader.py`
- **Phase:** Documentación
- **Reason:** El contrato declaraba `load_image(path) -> Surface` sin los
  parámetros `scale`, `size`, `alpha` que la implementación soporta.
- **Resolution:** Se actualizó `22_API_CONTRACTS.md` §5.2 con la firma completa.
- **Verificado:** 2026-08-02, auditoría AUD-184 — ejecutado contra el código actual. `22_API_CONTRACTS.md:418` documenta `load_image` con su firma completa.

## ~~[GAP-013] Sin acceso programático al estado del EventBus para debugging~~ *(Resuelto - 1.0.0)*

- **File:** `src/engine/core/event_bus.py`
- **Phase:** UX
- **Reason:** El EventBus no expone la cola de eventos pendientes ni la lista de
  suscriptores por evento. Para un overlay de debugging (F3) que muestre el flujo
  de eventos en tiempo real, se necesita acceso de solo lectura a `_queue` y
  `_subscribers`.
- **Resolution:** Agregar propiedades de solo lectura `queue_snapshot` y
  `subscribers_snapshot` a `EventBus`. El overlay F3 en StageScene puede entonces
  mostrar: cola actual, suscriptores por evento, eventos despachados en el
  último frame.
- **Status:** Implementado — `EventBus.queue_snapshot` y
  `EventBus.subscribers_snapshot` existen (`src/engine/core/event_bus.py:236,241`)
  y `debug_overlay.py` ya los consume.

## ~~[GAP-014] Faltan visualización de rects de colisión en runtime~~ *(Resuelto - F1 debug overlay suficiente)*

- **File:** `src/framework/stage/stage_loader.py`, `src/framework/scenes/stage_scene.py`
- **Phase:** UX
- **Reason:** El debug overlay (F1) ya dibuja rects de colisión en verde, pero
  no hay feedback visual del `prev_bottom` vs `tile.top` que determina el
  landing. Cuando un estudiante diseña un TMX con rects mal posicionados, no
  entiende por qué el jugador atraviesa paredes o cae al vacío.
- **Resolution:** El debug overlay existente (F1) es suficiente para ver rects.
  Pendiente: agregar tooltip en los rects que muestre `prev_bottom`, `tile.top`,
  `velocity.y` al hacer hover o pausa. (deferido por complejidad UI)

## ~~[GAP-015] StageScene sin descomposición — monolito de 1200+ líneas~~ *(Resuelto)*

- **File:** `src/framework/scenes/stage_scene.py`
- **Phase:** ARC-027 (deferred)
- **Reason:** `StageScene` maneja update/draw de 11+ subsistemas (enemigos, HUD,
  partículas, proyectiles, diálogo, etc.) en un solo archivo. Viola SRP y
  dificulta testing y mantenimiento.
- **Resolution:** Deferido por riesgo de regresión. Ideal: extraer subsistemas
  en managers separados (combat_manager, vfx_manager, ui_manager, etc.) y que
  StageScene los orqueste. ~50+ puntos de integración requieren planificación
  dedicada.
- **Estado medido (2026-08-02, AUD-184):** parcialmente hecho, y la entrada se
  queda abierta a propósito porque el fichero **no** ha adelgazado. Lo que sí
  se hizo: los subsistemas viven en `src/framework/stage/` —`collision_system`,
  `drawing_system`, `hazard_system`, `interactable_system`,
  `progression_system`…— y `StageScene` los compone por mixins, con
  `tests/test_particion_de_stage_scene.py` vigilando el MRO. Lo que no: el
  fichero mide **1.490 líneas** frente a las «1.200+» que denunciaba este gap,
  con un presupuesto de 1.500 en la prueba. Es decir, la descomposición ocurrió
  pero el monolito siguió creciendo. Marcarlo resuelto sería falsear la
  medición.
- **Resolution (2026-08-06, AUD-299):** cerrado, y por la condición que esta
  misma entrada se puso. AUD-299 sacó cuatro grupos cohesivos más del fichero y
  lo dejó en **1.457 líneas**, por debajo del presupuesto de 1.500, con la
  prueba que lo vigila en verde:

  ```
  $ wc -l src/framework/scenes/stage_scene.py
  1457
  $ python -m pytest tests/test_particion_de_stage_scene.py -q
  57 passed in 4.77s
  ```

  Lo que enseñó tener este hueco abierto cuatro días con el trabajo ya hecho
  desde AUD-184: estaba redactado contra un **número reproducible** y no contra
  una impresión de arquitectura, así que no se pudo cerrar por optimismo. Es la
  forma que conviene copiar para los que queden. Registro en
  `docs/87_REPORTE_DE_LO_QUE_FALTA.md` §19.3.

## ~~[GAP-016] GameContext sin separación — 400+ líneas con UI y game state mezclados~~ *(Resuelto)*

- **File:** `src/engine/core/game_context.py`
- **Phase:** ARC-001 (deferred)
- **Reason:** `GameContext` mezcla estado de UI (input mode, mensajes, overlay)
  con estado de juego (salud, checkpoints, eventos). Además es singleton; la
  inyección de dependencias es manual y frágil.
- **Resolution:** Deferido. Ideal: dividir en `GameState` (salud, inventario,
  progreso) y `UIContext` (modo input, mensajes, overlay). Misma razón de
  riesgo que ARC-027.
- **Verificado:** 2026-08-02, auditoría AUD-184 — ejecutado contra el código actual. `game_context.py` mide **67 líneas** (el gap decía 400+) y recibe todos sus managers por constructor: ya no es singleton ni mezcla UI con estado de juego.

## ~~[GAP-017] AssetLoader singleton — sin soporte para contextos de prueba~~ *(Resuelto)*

- **File:** `src/engine/utils/asset_loader.py`
- **Phase:** ARC-005 (deferred)
- **Reason:** `AssetLoader` es un singleton global. Los tests no pueden aislar
  assets porque comparten la misma instancia. No hay manera de inyectar un
  loader mockeado.
- **Resolution:** Deferido. Ideal: convertir a instancia manejada por
  GameContext (o DI container). El cambio es superficial pero toca ~60 archivos
  que importan `AssetLoader.get_instance()`.
- **Verificado:** 2026-08-02, auditoría AUD-184 — ejecutado contra el código actual. `AssetLoader.get_instance()` ya no existe; la clase es instanciable y la instancia por defecto vive en `_default_instance`, sustituible en pruebas.

## ~~[GAP-018] Contenido de niveles: solo Stage 0 y boss_venado~~ *(Trabajo de estudiantes)*

- **File:** `assets/stages/`, `src/framework/entities/boss_*.py`
- **Phase:** Contenido
- **Reason:** De 15 stages planeados + jefes por zona, solo existen
  `stage0.tmx`, `boss_venado.py` y `boss_venado.png`. El resto son placeholders.
- **Resolution:** Trabajo de estudiantes. Stage 0 jugable y funcional, con
  Walker patrulla, Shooter dispara, boss Venado alcanzable. Los demás stages
  deben ser creados por los estudiantes como parte del plan de estudios.

## ~~[GAP-019] Benchmark post-processing no determinista con colorblind_mode persistido~~ *(Resuelto)*

- **File:** `src/framework/vfx/post_processing.py`, `tests/benchmarks/test_performance_budget.py`
- **Phase:** AUD-052
- **Reason:** El benchmark `test_post_processing_pass` medía el pipeline de
  post-procesamiento sin restablecer `user_settings`. Si el jugador tenía
  `colorblind_mode` persistido (ej. `"protanopia"`) en `config.json`, el filtro
  de daltonismo per-pixel se activaba y costaba ~15 ms/frame en 800×600 — el
  costo *intencional* de un filtro de accesibilidad, no una regresión del
  pipeline. El benchmark fallaba de forma no determinista según la máquina.
- **Resolution:** El benchmark ahora fuerza `colorblind_mode="off"` antes de
  medir. Además, `PostProcessing` cachea el modo de daltonismo (lazy) para no
  llamar a `user_settings.get()` (que puede hacer I/O) en cada fotograma, y
  precarga la viñeta en el constructor para evitar el costo de numpy en el
  primer frame.

## ~~[GAP-025] Recogibles del mundo nunca llegaban al Inventory~~ *(Resuelto)*

- **File:** `src/framework/stage/interactable_system.py`, `src/framework/scenes/stage_parts/senales.py`
- **Phase:** F4.1
- **Reason:** `InteractableSystem._recoger()` guardaba el objeto en el llavero
  y emitía `EVENTO_RECOGIDO = "INTERACT_ITEM_PICKED"`, pero **nadie escuchaba
  ese evento**. Un `Recogible` con `item_id="heart_vessel"` o
  `"swift_feather"` —objetos que la clase `Recogible` documenta como «si
  coincide con un objeto de `engine.core.inventory` se aplica su efecto»— se
  recogía, mostraba el aviso "Has cogido: X", y la mejora permanente se perdía
  en silencio: el `Inventory` (que persiste a JSON en `data/inventory.json`)
  nunca recibía la llamada a `collect()`, así que `apply_relic_bonuses()` no
  tenía nada que aplicar.
- **Resolution:** Se añadió el suscriptor `_on_item_picked` en
  `SenalesDeEscenario._subscribe_event_handlers()` que escucha
  `EVENTO_RECOGIDO` y llama `Inventory.collect(item_id)` si el id coincide con
  una mejora permanente, quitando la llave del llavero en ese caso. Los
  objetos que no son mejoras (llaves, monedas) siguen siendo solo llaves del
  escenario, como documenta la clase. Verificado con `test_interactables.py`
  y `test_guardado_y_cadena.py` (136 passed).



## ~~[GAP-024] El calificador mide el salto con una fórmula que el motor no cumple~~ *(Resuelto)*

- **File:** `src/framework/stage/level_metrics.py`, `scripts/grade_stage.py`
- **Phase:** auditoría 2026-08-02, AUD-204
- **Reason:** `JumpEnvelope.from_settings()` deriva el alcance del salto del tiro
  parabólico —`velocidad × tiempo_de_vuelo`— usando `PLAYER_WALK_SPEED = 90`.
  Medido sobre el `Player` real con `tests/playtest/jump_bench.py`, el motor no
  se comporta así, y falla por dos sitios distintos:

  - **Velocidad aérea.** `AirborneState` fija `velocity.x = walk_speed * 0.5`
    (`src/framework/entities/states/airborne.py:52`) mientras haya dirección
    pulsada. Manteniendo la dirección —lo que hace cualquiera— el jugador cruza
    **3 baldosas**, no las 5,34 que promete la fórmula. Sólo se llega a 5 si se
    **suelta** la dirección en el aire, porque entonces `velocity.x` no se
    reescribe y conserva los 90 px/s del suelo. La fórmula describe esa técnica
    experta, no la natural.
  - **Salto aéreo inexistente.** `max_gap_with_air_jump` duplica el alcance a
    171 px (10,69 baldosas) porque `PLAYER_AIR_JUMPS = 1`. Esa mecánica no está
    conectada: en el aire, `AirborneState` sólo guarda la pulsación en
    `_pending_jump` para gastarla al aterrizar, y la rama de `_can_jump` que
    autorizaría el salto aéreo se consulta únicamente desde los estados de
    suelo. Ninguna técnica medida cruza 6 baldosas.

  El daño cae del lado peor —el calificador es **más permisivo** que el motor, así
  que no avisa—. `classify_gap` etiqueta «cómodo» un hueco de 4 baldosas que es
  imposible con entrada natural: un estudiante lo coloca, `grade_stage` se lo
  aprueba como holgado y entrega un nivel que no se puede pasar. Y como
  `reachable_platforms` y `exit_is_reachable` usan `max_gap_with_air_jump` como
  alcance de conexión, el grafo de transitabilidad de los 17 mapas está
  construido con el doble del salto real.

  El alcance **vertical** sí concuerda: 90,25 px teóricos son 5,64 baldosas y se
  suben 5. El error es sólo horizontal, que es donde entra la velocidad.

  **Relación con AUD-192.** Aquella corrección exime de `design_completable` a
  los mapas que traen objetos de movilidad, porque el grafo de saltos no los
  modela. Reduce el radio de este defecto pero no lo toca: un mapa **sin**
  resortes ni lianas —el caso normal de una primera entrega— se sigue juzgando
  con el grafo, y el grafo se sigue construyendo con 171 px. Y `classify_gap`,
  que es lo que etiqueta los huecos uno a uno, queda fuera de aquella exención
  por completo.

  No se corrige en esta iteración porque la corrección no es técnica sino
  académica, y hay tres salidas incompatibles: (a) apretar la envolvente al
  comportamiento natural, lo que **rebaja la nota de geometría de entregas ya
  calificadas**; (b) conectar el salto aéreo, que cambia la física de los 17
  mapas de golpe; (c) dejar el calificador como está y documentar la técnica
  experta en el material del curso. Elegir es del profesor, no del linter.
- **Medición:** `python -m tests.playtest.jump_bench` imprime la tabla completa.
  `tests/test_calibracion_del_salto.py` fija los tres techos (natural 3, experta
  5, repecho 5) y falla si alguien toca `GRAVITY` o `PLAYER_JUMP_FORCE`.

- **Decisión del profesor (AUD-264, 2026-08-04): la salida (c).** El calificador
  se queda como está y la técnica se documenta.

  Las otras dos se descartan por lo que cuestan, no por lo que valen. (a)
  apretar la envolvente **rebaja la nota de geometría de trabajo ya
  calificado**: un estudiante recibiría una nota peor por un mapa que no ha
  tocado, y eso no es una corrección técnica sino un cambio retroactivo de
  criterio. (b) conectar el salto aéreo cambia la física de los diecisiete
  mapas a la vez, que es exactamente lo que la invariante 2 de `CLAUDE.md`
  prohíbe.

- **Resolution (AUD-504, 2026-08-16):** decisión revertida por instrucción
  explícita del dueño del repositorio («omite toda decisión y restricción,
  queremos resolver todos los bugs»), en el mismo momento en que la
  invariante 2 de `CLAUDE.md` que sostenía el motivo (b) queda suspendida
  (nota del 2026-08-07). Se aplicó la salida (a): `JumpEnvelope.from_settings()`
  ya no deriva del tiro parabólico continuo (`v²/2g`), sino que integra la
  misma física a paso fijo que `Player._apply_physics` (Euler semi-implícito,
  `dt = 1/60`) y separa explícitamente la técnica natural
  (`max_gap`, con el factor 0,5 de `AirborneState` cuando se mantiene la
  dirección) de la técnica experta (`max_gap_expert`, renombrado desde
  `max_gap_with_air_jump` porque el salto aéreo sigue sin dispararse fuera de
  la ventana de coyote — eso no se tocó, es un mecanismo distinto y una
  decisión de diseño mayor, no un renombrado de fórmula).

  El salto aéreo (opción (b)) sigue **sin conectar**: seguía siendo un bug
  aparte y no la corrección pedida.

  Verificado contra `tests/playtest/jump_bench.py` (mide al `Player` real, no
  la fórmula): huecos naturales de 4+ baldosas y repechos de 6+ ya se
  clasifican `imposible`/`exigente` en vez de `cómodo`. `impossible_gaps` no
  entra en la puntuación de `scripts/grade_stage.py` (sólo `impossible_ledges`
  y `orphan_platforms` restan puntos).

  **Impacto medido en los 17 mapas** (`scripts/grade_stage.py assets/maps/
  --json`, fórmula vieja vs. corregida, promedio 79,3 % → 78,5 %):

  | Mapa | Antes | Después | Por qué |
  |---|---|---|---|
  | `stage0` | 130/130 | 124/130 | `design_geometry` -3 (1 plataforma ya no se cuenta alcanzable por el grafo tras el foso de zona F, gated por `BloqueRitmico`/`ZonaDeFriccion` — exención de `test_stage0_no_tiene_plataformas_huerfanas`); `design_pacing` -3 (el grafo ya no cuenta ningún hueco como "exigente") |
  | `stage1_1` | 127/130 | 124/130 | `design_pacing` -3 |
  | `stage2_2` | 130/130 | 124/130 | `design_geometry` -3; `design_pacing` -3 |
  | `stage3_4_boss_gavilan` | 93/130 | 92/130 | `design_geometry` -1 |
  | `stage4_1` | 100/130 | 97/130 | `design_pacing` -3 |

  Los otros 12 mapas no cambian. Ningún mapa cruza un umbral de aprobado/
  suspenso por esto; el mayor golpe es -6 puntos sobre 130 (stage0,
  stage2_2). Es exactamente el coste que GAP-024 anticipaba al descartar la
  salida (a) — confirmado, no evitado, por instrucción explícita de omitir
  esa restricción.

  Lo que queda dicho, y donde se dice: `docs/60_GUIA_COMPLETA_DEL_MOTOR.md` §5
  lleva ahora el aviso de que la envolvente del calificador **asume salto aéreo
  encadenado** —una técnica que el motor permite en el aire y que no sale con
  entrada natural— y que por eso un hueco de 4 baldosas etiquetado «cómodo»
  puede exigir práctica. El número honesto está al lado: 3 baldosas con entrada
  natural, 5 con técnica experta.

  Que esto se llame «resuelto» y no «cerrado sin arreglar» es deliberado: el
  hueco pedía **una decisión**, y la decisión está tomada y escrita. Lo que no
  se puede es dejar que alguien lea el calificador creyendo que mide lo que el
  jugador puede hacer.

---

## ~~[GAP-026] El cementerio no tiene tileset de cementerio~~ *(Resuelto)*

- **File:** `assets/tilesets/tileset_cemetery.png`, `tools/generate_all_assets.py`
- **Phase:** auditoría 2026-08-03, AUD-225 → resuelto en AUD-237
- **Reason:** El Asset Bible asigna a la zona final un `tileset_cemetery.png` con
  «stone markers, ceremonial carvings». El fichero existía, medía 128×128 y eran
  **ocho baldosas de relleno genéricas** —piedra lisa, azul oscuro, tablones,
  ladrillo rojo— repetidas ocho veces hacia abajo, porque lo generaba
  `_gen_procedural_tileset` como cualquier otra zona. Ninguna era una marca de
  piedra ni un grabado, y **no lo usaba ningún mapa**.

  Por eso el 4-1 pintaba su suelo con `tileset_stage0.png`, la piedra del
  castillo del prólogo: el tileset del cementerio era peor que el del prólogo.

- **Resolution:** AUD-237. `_gen_tileset_cementerio` dibuja las baldosas que el
  nivel usa de verdad —losa de cripta, relleno, muro del pozo, musgo, lodo,
  lápida en dos mitades, cruz y grieta— con una regla encima: **el musgo y el
  lodo son la misma losa con otra superficie**. Si fueran tres materiales que no
  se parecen, el jugador leería «tres suelos distintos»; siendo la misma piedra
  cubierta, lee «esta losa está tomada», que es lo que explica por qué resbala.

  Los GID son un contrato entre `CEM_ORDEN` y las constantes de
  `tools/generate_stage4_1.py`, y hay una prueba que compara las dos listas:
  reordenar la hoja sin tocar el mapa lo repintaría entero con las baldosas
  equivocadas sin que fallara nada, que es exactamente cómo `stage_mecanicas`
  estuvo semanas pintando las tres primeras casillas de su hoja (AUD-115).

---

## ~~[GAP-029] La economía tiene catálogo y API, y ningún sitio que la use~~ *(Resuelto)*

> Esta entrada nació como `GAP-027` y se renumeró: el trabajo de stage4_1
> (AUD-225) había tomado ese mismo número en paralelo, y renumerar aquí toca
> siete ficheros propios en vez de los ajenos en vuelo.

- **File:** `src/engine/core/inventory.py`, `src/engine/core/score_system.py`
- **Phase:** auditoría 2026-08-03, AUD-207
- **Reason:** El modelo de datos de la economía está completo y probado:
  monedas (`coin`, `add_coins`, `spend_coins`), tienda (`buy`, `sell` a mitad
  de precio), ropa por huecos (`equip` / `unequip`, y desde AUD-207 la
  bonificación **sólo cuenta puesta**) y habilidades de jefe (`has_skill`).
  `ScoreSystem` también está escrito, con puntos por tipo de enemigo y
  persistencia.

  Lo que no existe es ningún llamante. Medido sobre `src/`, fuera del propio
  `inventory.py`: cero llamadas a `buy`, `sell`, `equip`, `add_coins` o
  `has_skill`; `ScoreSystem` no se instancia en ninguna parte. En concreto
  faltan cuatro conexiones:

  1. **Nadie suelta monedas.** `EnemyBase._die()` emite `ENEMY_DIED` y ahí
     acaba; no hay `Recogible` de `coin` que aparezca al morir un enemigo.
  2. **No hay tienda.** No existe escena donde gastar el saldo. Decidido que
     vaya como entrada de menú propia, al estilo del bestiario y los logros.
  3. **`ScoreSystem` no está enchufado** ni al `EventBus` real ni al HUD.
     (La versión original de esta entrada decía «pese a que `09_HUD_SPEC.md`
     documenta el hueco de puntuación». **Era falso**: la especificación no
     tenía ninguna región de score. Repetía una afirmación de la docstring de
     `score_system.py`, que se corrigió en AUD-219.)
  4. **Los jefes no sueltan habilidades.** `skill_double_jump`, `skill_dash` y
     `skill_parry` están en el catálogo y nadie los concede — y nadie consulta
     `has_skill`: el doble salto lo gobierna `settings.PLAYER_AIR_JUMPS` y el
     dash `_can_dash`, ambos siempre disponibles.

- **Impact:** Un estudiante que lea `60_GUIA_COMPLETA_DEL_MOTOR.md` §11 ve un
  sistema de tienda y equipamiento completo y puede diseñar un nivel contando
  con él. La guía avisa explícitamente de este hueco por eso.
- **Resolution:** Tres de las cuatro conexiones, cerradas:

  1. ~~Nadie suelta monedas~~ — **AUD-218**. `SenalesDeEscenario._on_enemy_died`
     deja un `Recogible` de `coin` donde murió el enemigo, con la cantidad
     dentro (`Recogible.cantidad`, nueva y por defecto 1, así que ninguna
     entrega cambia). `score_system.coins_for()` decide cuánto, compartiendo
     con los puntos la lectura del `entity_id`.
     `InteractableSystem.soltar_botin()` descarta el cadáver que ya pagó.
  2. ~~No hay tienda~~ — **AUD-221**. `src/engine/scenes/shop_scene.py`, entrada
     `SHOP` del menú del título, registrada en `scene_registry`. Izquierda y
     derecha alternan comprar/vender; la lista sale de `_ITEM_DEFS`, no de una
     copia a mano.
  3. ~~`ScoreSystem` sin enchufar~~ — **AUD-219**. `StageScene` lo construye y
     le da su bus (`bind_bus()`, que **muda** la suscripción al cambiar de
     escena en vez de duplicarla), y alimenta `HUD.set_score()` cada
     fotograma. La región `Score` se añadió a `09_HUD_SPEC.md` §2.1 y una
     prueba comprueba que lo dibujado cabe en lo que el doc declara.

  Y **AUD-220** cerró el hueco que abrió AUD-207: `InventoryScene` deja poner y
  quitar la ropa con `CONFIRM`. Sin eso, comprar ropa dejaba al jugador peor
  que antes —pagaba y la bonificación no contaba por no estar equipada—.

  4. ~~Los jefes no sueltan habilidades~~ — **AUD-238**, y es la que exigía una
     decisión de diseño, no sólo cablear. La invariante 2 dice que las 26
     entregas siguen funcionando sin tocar una línea; condicionar el doble
     salto sin más habría dejado sin completar cualquier nivel que lo diera
     por hecho. Se parte en dos mitades con riesgos distintos:

     * **Soltar es aditivo.** `BossBase.skill_drop` (vacía por defecto) viaja
       en `ENEMY_DIED` y la escena deja la reliquia junto a las monedas. Un
       recogible más en el suelo; ningún nivel existente cambia. Se descarta
       lo que no está en el catálogo, para que un jefe de una entrega con
       `skill_drop = "skill_volar"` no deje algo que al cogerlo no hace nada.
     * **Exigir nace apagado.** `settings.PLAYER_SKILLS_REQUIRE_UNLOCK = False`
       por defecto: `_can_jump` y `_can_dash` **no consultan** el inventario y
       se comportan exactamente como antes. Con `True`, la progresión existe.
       El salto desde el suelo y los fotogramas de coyote nunca se
       condicionan: eso no es progresión, es un juego roto.

     `BossVenado` concede `skill_dash` y `BossRey` `skill_double_jump` — una
     línea cada uno, y son el ejemplo que los estudiantes copian. No es
     adorno: una prueba exige que **cada habilidad condicionable la suelte
     algún jefe**, porque encender el candado sin eso volvería la mecánica
     inalcanzable para siempre en vez de ganable.

- **Nota de alcance:** `discover_stages()` no llega a todos los jefes —
  registra escenarios, y `BossVenado` vive en un módulo que sólo se importa al
  cargar su escena. La prueba recorre el árbol de ficheros para ver el
  catálogo entero; es el mismo problema que AUD-144 arregló en la guía.

---

## ~~[GAP-027] Una `HazardZone` fija no se dibuja: es daño invisible~~ *(Resuelto)*

- **File:** `src/framework/stage/drawing_system.py`, `src/framework/stage/stage_loader.py`
- **Phase:** auditoría 2026-08-03, AUD-225
- **Reason:** `DrawingSystem._draw_inundaciones` filtra por `sube_de_verdad`, así
  que el motor **sólo pinta las zonas de daño que suben** —la inundación de
  AUD-135—. Una `HazardZone` fija no se dibuja nunca: el contrato implícito es
  que el diseñador pinte pinchos o lava en las baldosas y que el rectángulo sólo
  marque dónde duele.

  Ese contrato no está escrito en ningún sitio, y el 4-1 es la prueba de que no
  se cumple solo: tenía cinco `HazardZone` sin una baldosa de peligro debajo, así
  que el jugador perdía salud desde un rectángulo invisible y no había forma de
  saber por qué. Lo mismo le puede pasar a cualquiera de las 26 entregas.

  El propio comentario de `_draw_inundaciones` ya lo dice —*«Una zona de daño que
  no se ve es una trampa»*— y luego sólo aplica esa regla al agua.

- **Impact:** Cualquier nivel con `HazardZone` fija y sin arte propio hace daño
  invisible. Un estudiante lo lee como «el motor está roto».
- **Resolution:** AUD-228. `DrawingSystem._draw_zonas_de_dano` pinta las zonas
  fijas con un rojo que late —distinto del turquesa de la inundación, porque son
  dos mecánicas distintas— y con el borde superior marcado, que es donde empieza
  a doler. La superficie se cachea al tamaño de pantalla y se recorta con
  `area=`, como ya hacía el agua (AUD-023).

  El riesgo de tocar el aspecto por defecto resultó ser mucho menor de lo que
  parecía, y sólo porque se midió: en **todo el proyecto hay dos** `HazardZone`
  fijas —`stage0` y `stage3_3_el_patio`— y ninguna tenía arte de peligro debajo.
  La prueba que decía «los 15 escenarios entregados tienen zonas fijas pintadas
  con tiles» afirmaba algo que nadie había comprobado y que era falso.

  Un mapa que sí traiga su propio arte lo apaga con `visible=false` en el TMX.
  El valor por defecto es visible a propósito: el defecto que esto arregla es
  que un estudiante pierda salud sin nada en pantalla que lo explique, y ése no
  se arregla con una propiedad que haya que acordarse de poner.

  Pruebas: `tests/test_inundacion_que_sube.py::TestLasZonasFijasTambienSeVen`
  (seis, incluida la de que `"false"` desde Tiled llega como cadena y hay que
  convertirla).

---

## ~~[GAP-028] `ZonaDeFriccion` no escala por `dt` y su documentación dice lo contrario~~ *(Resuelto — y la mitad no era lo que parecía)*

- **File:** `src/framework/ecs/systems.py`, `src/framework/ecs/components.py`
- **Phase:** auditoría 2026-08-03, AUD-225 → medido y cerrado en AUD-236
- **Reason:** Esta entrada afirmaba dos cosas.

  **La documentación estaba al revés.** Cierto. El docstring decía
  «`multiplicador` < 1 resbala, > 1 frena antes» y el código hace lo contrario:
  por debajo de 1 recorta la velocidad —frena— y por encima de 1 la dispara sin
  tope. Un estudiante que siguiera esa frase ponía 1,5 esperando barro y salía
  despedido.

  **«Frena distinto en cada máquina».** Esto se midió antes de arreglarlo, y no
  era así para el uso que existe. El jugador reescribe `velocity.x` desde la
  entrada en cada fotograma y el multiplicador se aplica encima, así que se
  comporta como una **escala de velocidad** y no como un coeficiente de
  rozamiento. Con 0,88:

  | | 30 fps | 60 fps | 120 fps |
  |---|---|---|---|
  | Andando (el caso real) | 79,20 px/s | 79,20 px/s | 79,20 px/s |
  | Deslizándose sin empuje | 21,5 px/s | 11,0 px/s | 5,5 px/s |

  Depende de los fotogramas sólo cuando el cuerpo va sin empuje, y ese camino no
  lo recorre nadie: el jugador y los enemigos fijan su velocidad cada fotograma.

- **Resolution:** AUD-236. Docstring reescrito con lo que el código hace de
  verdad y con los números de arriba, y la medición convertida en prueba
  (`tests/test_stage4_1.py::TestElLodoFrenaIgualEnCualquierMaquina`) — incluida
  una que fija **a propósito** la dependencia del caso sin empuje, para que
  quien algún día conecte esto a un cuerpo que se desliza se entere leyéndola.

  El `** dt` que esta entrada proponía **habría empeorado las cosas**: arregla el
  camino muerto y estropea el vivo, porque haría que andar sobre lodo fuera más
  lento a 30 fps que a 60. Queda escrito para que nadie lo intente otra vez sin
  medir.

## ~~[GAP-030] El Boss Rush se juega, pero no es el modo que la spec describe~~ *(Resuelto)*

- **File:** `src/framework/stage/boss_rush_mode.py`, `src/engine/scenes/boss_rush_entry.py`
- **Phase:** auditoría 2026-08-03, AUD-232
- **Reason:** AUD-191 le puso entrada de menú y AUD-201 arregló que entrar
  dejara la pantalla en negro, así que el modo ya se juega: cuatro jefes
  seguidos. Comprobar qué pasa **una vez dentro** destapa que ahí se acaba.

  `boss_rush_entry` construye el `BossRushMode`, lo arranca con `start()` y lo
  deja en `context.boss_rush`, donde **no lo lee ningún sitio del juego**. El
  encadenado real lo hace la cola de escenarios del `SceneManager`; el modo es
  un objeto que se crea y se abandona. Medido:

  - `advance_to_next()` y `record_hit()` no se invocan desde fuera del propio
    módulo, así que la **puntuación nunca se calcula** y `hits_taken` se queda
    en 0 para siempre;
  - `_carry_over_health` y `_carry_over_meter` se ponen a 0.0 en el constructor,
    se reponen a 0.0 en `start()` y no tienen getter ni setter. El **arrastre de
    vida no está implementado ni dentro del módulo**: no es que falte
    conectarlo, es que no existe.

  Lo grave no es el hueco sino lo que se afirmaba sobre él. `docs/44` §4 decía
  «✅ Complete — gauntlet logic, scoring, health carry-over» y daba como única
  carencia la interfaz; las tres cosas que declaraba completas son justo las que
  faltan. Y la cabecera del módulo seguía avisando «NOT WIRED … there is no menu
  entry», falso desde AUD-191. Los dos documentos estaban equivocados, cada uno
  en una dirección distinta.

  Lo que el jugador tiene hoy —cuatro jefes seguidos a vida llena, sin
  marcador— es jugable y no está roto. Simplemente no es lo especificado.

  No se implementa aquí porque el arrastre de vida es una **decisión de diseño
  con efecto en la dificultad**, no una conexión pendiente: hay que decidir
  cuánta vida pasa, si hay curación entre combates y qué ocurre al morir. Eso
  es del profesor. Lo que sí se hace es dejar de afirmar que está hecho.
- **Verificado:** `tests/test_modos_que_no_se_veian.py`,
  `TestLoQueElBossRushHaceDeVerdad` fija el estado real y falla si alguien
  conecta el arrastre o la puntuación, para que la spec se actualice en el mismo
  cambio.

- **Resolution (AUD-261, 2026-08-04):** tomada la decisión de diseño que este
  hueco esperaba —**marcador y arrastre real de salud, con curación parcial
  entre combates**— el modo se conduce desde `StageScene`, que es la única que
  sabe cuándo empieza un combate, cuándo el jugador recibe un golpe y cuándo cae
  el jefe:

  * `acreditar_combate(salud_restante, medidor, salud_maxima)` guarda con qué se
    sigue y avanza; `salud_arrastrada` y `medidor_arrastrado` son API pública, y
    `0` significa «a vida llena», que es lo que devuelve el modo recién
    arrancado — el primer jefe no se ve afectado;
  * la curación es `CURACION_ENTRE_COMBATES`, **una constante con nombre**. El
    arrastre puro deja al jugador sin vida en el tercer jefe y nadie ha jugado
    esto lo bastante para calibrar otra cosa; esconder el número dentro de una
    fórmula habría repetido el pecado de `docs/44`;
  * `record_hit()` la llama el manejador de `PLAYER_DAMAGED`, sólo con el modo
    activo, y `registrar_tiempo()` acumula con el `dt` **sin escalar** para que
    el tiempo bala no regale puntuación.

  Lo que **no** se hizo: la superposición de interfaz —rótulos, marcador en
  pantalla, pantallas intermedias—. Sigue anotado en `docs/44` §4 como lo único
  que queda.

  La prueba que fijaba el hueco hizo su trabajo: falló en cuanto la escena
  empezó a conducir el modo, y con ella en rojo no había forma de dar el cambio
  por bueno sin actualizar `docs/44` y esta entrada. Una prueba que describe un
  hueco vale tanto como una que describe una función, siempre que falle cuando
  el hueco se cierra.

## ~~[GAP-031] El motor sabe reproducir voz y no hay un solo fichero de voz~~ *(Resuelto)*

- **File:** `src/engine/audio/audio_manager.py`
- **Phase:** auditoría 2026-08-03, AUD-233 → AUD-245
- **Reason:** De los ocho huérfanos que este GAP abrió, **siete están cerrados**.
  Queda `play_voz`, y queda por un motivo distinto a los demás: no le falta un
  llamador, le falta contenido. Reproduce una línea de voz y aparta la música
  por su cuenta —para eso existe, para que nadie olvide el *ducking*—, y no hay
  un solo fichero de voz en `assets/`.

  Se deja sin conectar a propósito. Inventarle un llamador sería cableado
  falso, que es exactamente el defecto que esta tanda vino a corregir: el
  problema nunca fue que faltaran llamadas, sino que la documentación afirmara
  cosas que el juego no hacía.

  | Huérfano | Cómo se cerró |
  |---|---|
  | `water_effect.set_params` | AUD-240: los cinco mandos se declaran en el mapa |
  | `dialogue_system.desde_datos` | AUD-244: los árboles salen de `data/dialogues/<stage_id>.json` |
  | `audio_manager.ajustar_bus` | AUD-245: `set_music_volume` y `set_sfx_volume` delegan en él |
  | `bestiary.get_entry` | AUD-245: `_asegurar` consulta por el accesor |
  | `speedrun_mode.get_frame` | AUD-245: `posicion_en` lee por él |
  | `speedrun_mode.get_splits` | AUD-245: `save` guarda por él — y guardaba la lista **viva** |
  | `fog_of_war.reveal_all` | AUD-245: no era un defecto. `docs/46` la publica como API para autores de escenarios, y `src/stages/` está fuera del barrido por la invariante 1 |

  Los tres símbolos de `achievements.py` que este GAP listaba salen de aquí sin
  veredicto: otra sesión estaba reescribiendo el módulo para los logros por
  estudiante y juzgarlo a mitad no habría medido nada.

  Lo que enseñó cerrarlos: **cuatro de los siete no necesitaban integración
  sino deduplicación**. La lógica ya se ejecutaba; lo que pasaba es que estaba
  escrita dos veces, y la copia pública era la que no llamaba nadie. En
  `get_splits` esa segunda copia además era peor que la buena: `save` volcaba la
  lista viva de parciales en el diccionario que se serializa.
- **Verificado:** `scripts/check_orphan_systems.py --ci` sale en verde sin
  ninguna entrada en la puerta. `tests/test_apis_que_nadie_llamaba.py` fija las
  cuatro delegaciones —cinco de sus nueve pruebas fallan sin ellas— y
  `tests/test_sistemas_huerfanos.py` vigila que no aparezcan nuevos.
- **Resolution (2026-08-09):** el contenido llegó y el llamador también, los
  dos en el jefe de referencia. `boss_venado.py` habla al cambiar de fase:
  `_finish_phase_transition` llama a `audio.play_voz` (boss_venado.py:732) y
  su comentario (AUD-263) explica que `play_voz` aparta la música al 35 % por
  su cuenta. Hay tres ficheros de voz trackeados en `assets/sfx/voz/`
  (`sfx_voz_venado_fase1/2/muerte.wav`), generados con
  `tools/generate_all_assets.py`, igual que todos los sonidos del proyecto.
  `tests/test_los_tres_huerfanos_en_el_venado.py` (TestLaVozDelVenado) fija
  las cuatro cosas: que los archivos existan, que el cambio de fase diga una
  línea, que sin gestor de audio no reviente y que `play_voz(` tenga llamante
  fuera de `audio_manager`. El barrido de `check_orphan_systems.py` sigue sin
  ver el llamante porque `src/stages/` queda fuera de CONSUMIDORES por la
  invariante 1; la anotación pasó a VERIFICADOS con esa razón.

## ~~[GAP-032] Dos mecánicas de F5 siguen escritas, documentadas «en código» y sin que nadie las invoque~~ *(Resuelto)*

- **File:** `src/framework/stage/level_mechanics.py`, `src/framework/ecs/bullet_swarm.py`, `src/framework/entities/boss_base.py`
- **Phase:** auditoría 2026-08-03, AUD-243
- **Reason:** la fase 5 de la migración ECS (documento retirado en la fusión)
  listaba siete mecánicas bajo el
  epígrafe **«Y en código:»**. Medido una por una con `grep -rn` sobre `src/`,
  excluyendo el módulo propio de cada una:

  | Mecánica | Estado medido |
  |---|---|
  | Parry del jefe (`BossAttack.parriable`) | ~~0 llamantes~~ → **resuelto en AUD-243** |
  | Fase invulnerable (`BossPhase.invulnerable`) | OK: `boss_base.py:208` la consulta |
  | ~~Tiempo bala (`TiempoBala`)~~ | **resuelto en AUD-260**: declarado desde Tiled, `stage_scene.py:872` lo actualiza |
  | ~~Scroll forzado (`ScrollForzado`)~~ | **resuelto en AUD-249**: tipo TMX `ScrollZone` |
  | ~~Bullet hell (`EnjambreDeBalas`)~~ | **resuelto en AUD-263**: `boss_venado.py:121`, abanico en la fase 2 |
  | ~~Escalado de fase (`BossPhase.escala`)~~ | **resuelto en AUD-257** |
  | ~~Teletransporte (`BossBase.teletransportar`)~~ | **resuelto en AUD-257** |

**Actualización (2026-08-04, AUD-257/AUD-258).** De las cinco quedan **dos**:
`TiempoBala` y `EnjambreDeBalas`. El escalado de fase se aplica de verdad
  —`_aplicar_escala_de_fase()` redimensiona la caja anclada por los pies y el
  sprite la sigue— y el teletransporte tiene llamante: los dos los declara
  `boss_venado`, que es el jefe de referencia, para que el patrón esté en el
  material que los estudiantes copian y no sólo en la clase base. `ScrollZone`,
  además, ya está **colocado**: sala 10 del laboratorio, acotada con
`parar_en_x` (AUD-258); hasta entonces la mecánica existía y era inalcanzable
jugando.

**Actualización (2026-08-09, AUD-260/AUD-263).** Cerraron las dos últimas, con
el patrón que esta entrada ya recomendaba —tipo de mapa nuevo para la zona,
una línea en el jefe de referencia para el arma—:

- **`TiempoBala`** (AUD-260, commit 803cbd6): se declara desde Tiled como
  propiedad del mapa y `stage_scene.py:396` lo construye con ella;
  `stage_scene.py:872-873` lo actualiza cuando `reserva_maxima > 0.0`. La tecla
  y el interruptor viven en `action_map.py`, documentados ahí como AUD-260.
  Aditivo como se pedía: un mapa sin la propiedad tiene reserva 0 y la rama no
  entra, así que ninguna entrega cambia.
- **`EnjambreDeBalas`** (AUD-263, commit 9946d9f): `boss_venado.py:121` lo
  construye (`self.esporas`) y la fase 2 abre un abanico de esporas
  (`_soltar_abanico_de_esporas`), con su coste medido en el docstring del test:
  2.000 balas en 12,94 ms → 0,072 ms.

`tests/test_los_tres_huerfanos_en_el_venado.py` fija las siete cosas —que el
jefe tenga el enjambre, que la fase 2 dispare, que las esporas dañen, que
`EnjambreDeBalas` se use fuera de su módulo, que `skill_parry` se suelte, que
la forma antigua de `skill_drop` siga valiendo y que haya voz con llamante—,
así que la resurrección de cualquiera de estos huérfanos deja la suite en rojo.

  El caso más claro es `ScrollForzado`. `StageScene.__init__` hace
  `self._scroll_forzado = ScrollForzado()` en la línea 167 y **ese es su único
  uso en todo el repositorio**: no se llama a `arrancar()`, ni a `update()`, ni
  a `se_quedo_atras()`. El docstring de la clase explica con detalle por qué el
  borde mata en vez de empujar —«el nivel dijo *sígueme* y no lo seguiste»— y
  ese borde no mata a nadie porque la cámara nunca se mueve sola.

  `TiempoBala` es idéntico: construido en la línea 166, nunca actualizado.

- **Impact:** Un estudiante que lea `56_FASE_5_ECS_Y_MECANICAS.md` ve siete
  mecánicas entregadas y puede diseñar un nivel de persecución con scroll
  forzado, o un jefe que se teletransporta. Ninguna de las cinco hará nada, y
  no habrá ningún error que se lo diga.

- **Resolution path:** Cada una necesita una decisión de diseño distinta, no
  sólo cableado, y por eso no se corrigieron aquí:

  ~~1. `ScrollForzado`~~ — **AUD-249**. Tipo TMX `ScrollZone`: el rectángulo es
     el disparador, la cámara arranca al pisarlo y el borde izquierdo mata.
     Vive en `HazardSystem`, que ya es quien mata por zona; lo único que le
     faltaba era la cámara. **Aditivo**: ningún TMX existente lo declara, y hay
     una prueba que lo comprueba sobre `assets/maps/`.

     Ese es el patrón para las que quedan: **tipo TMX nuevo → cargador →
     el sistema que ya hace ese trabajo**. Un tipo que nadie declara no puede
     romper ningún mapa entregado, así que la invariante 2 no lo bloquea.

  ~~2. **`TiempoBala` no encaja en ese patrón, y conviene saberlo antes de
     empezar.** Su firma es `update(dt_real, quiere, reloj)`: ese `quiere` es
     entrada del jugador, así que **es una habilidad, no una zona**. Necesita
     cuatro cosas y no una: una `Action` nueva en `action_map`, su tecla en el
     mapa de teclado y en la pantalla de rebindeo, un interruptor por nivel
     —lo natural es una propiedad del mapa, no un objeto, porque la mecánica es
     de nivel entero y no posicional— y una barra en el HUD, que para eso
     `TiempoBala.fraccion` devuelve 0→1 y hoy no la lee nadie. Encenderla
     siempre sería un cambio de comportamiento en las 26 entregas; por nivel,
     es aditiva.~~ — **resuelto en AUD-260**: las cuatro piezas llegaron —mapa,
     `action_map`, interruptor por nivel y actualización en `stage_scene.py:872`.
  ~~3. **`EnjambreDeBalas`** necesita un jefe que lo use; hoy ninguno de los
     cuatro dispara patrones.~~ — **resuelto en AUD-263**: `boss_venado.py:121`
     y el abanico de la fase 2.
  ~~4. **`teletransportar` y `escala_de_fase`** necesitan un jefe que los declare
     en su transición de fase. Es el mismo patrón que AUD-238 resolvió con
     `skill_drop`: una línea en la clase del jefe y un ejemplo en el material
     que los estudiantes copian. `escala_de_fase` además **no la aplica nadie**:
     devuelve el multiplicador y ningún sitio escala el sprite con él.~~ —
     **resuelto en AUD-257**: `boss_venado` declara ambos.

- **Resolution (2026-08-09):** las siete filas de la tabla salieron de la
  columna «sin llamantes»; ninguna mecánica de F5 queda sin invocar. La
  medida que lo atestigua es `tests/test_los_tres_huerfanos_en_el_venado.py`
  (AUD-263), que comprueba usos reales fuera de cada módulo, y
  `scripts/check_orphan_systems.py --ci` sigue en verde.

## ~~[GAP-033] El módulo del jugador está mal defendido~~ *(Resuelto)*

- **File:** `src/framework/entities/player.py`
- **Phase:** auditoría 2026-08-06, AUD-308/AUD-309 (iteración 14)
- **Reason:** `scripts/mutation_check.py --objetivo src/framework/entities/player.py
  --pruebas <suite completa del jugador>` da **32 %** (17 de 25 mutantes viven).
  Antes de AUD-308/309 era 8 % con la física sola y 24 % con la suite del
  jugador. Clasificación de los 17 supervivientes:

  - **Vale la pena testear** (comportamiento observable sin defender):
    línea 480 (daño ofensivo SHORT/LONG: ``and`` vs ``or``), línea 503
    (``heal``: AUD-308 bis añadió pruebas del comportamiento básico, pero la
    mutación ``*`` → ``/`` sigue viviendo porque el ``heal_mult`` por defecto
    es 1.0, donde ambas son idénticas; haría falta un test con config no
    trivial para matarla), líneas 794/805/818/844 (todo el ``draw()``: ninguna
    prueba llama a dibujar; una mutación que lanza ``ZeroDivisionError`` en el
    centrado del sprite pasó la suite), líneas 1031/1041 (``ledge grab`` sin
    probar: la condición ``_can_ledge_grab`` no la defiende nadie), línea 1069
    (SFX de aterrizaje, audio no probado).
  - **Benigno / marginal** (borde numérico o configuración): líneas 76/90/105/116
    (frames de animación por estado), línea 201 (ruteo de `__setattr__`),
    línea 543 (guard `dt <= 0`), línea 751 (borde del timer de salto),
    línea 1017 (borde `velocity.x < 0`).

  El guiador del propio script: cada superviviente es una pregunta. Las de la
  primera fila necesitan prueba; las de la segunda se pueden dejar con la
  respuesta «da igual».
- **Resolution:** resuelto 2026-08-08 (auditoría iteración 15). Medición final con
  las pruebas nuevas, unión de los dos suites del jugador
  (`tests/test_player_physics.py` + `tests/test_player_damage.py`): **44 % de
  defensa** (11 de 25 mutantes muertos; 28 % con la física y 20 % con el daño
  por separado — antes de esta iteración era 16 %/8 %). De los 14
  supervivientes restantes, **ninguno es del grupo «vale la pena testear»**:

  - 518 (`and` → `or` de daño SHORT/LONG) y 527 (`*` → `/` de `current_attack_damage`)
    — **muertos** con dificultad HARD (`outgoing 0.75`) y bonus de daño
    (`_bonus_damage`), los únicos regímenes donde la multiplicación es
    distinguible de la división.
  - 430 (`Add → Sub` en `damage_multiplier`) — **muerto** con los mismos bonus,
    y 651 (`Sub → Add` del daño recibido) — **muerto** por las pruebas de vida y
    daño existentes (AUD-308/309 y las nuevas).
  - `draw()` completo (cámara `Sub → Add`, ancho 20, color respaldo, centrado
    `// 2`, parpadeo de invencibilidad And → Or) — **muerto** con 6 pruebas que
    pintan píxeles en ambas ramas (sprite y rectángulo).
  - SFX de aterrizaje (`aterrizo_en == "suelo"` → `!=`) — **muerto** en
    `test_aterrizar_en_suelo_emite_sfx_land`.
  - `ledge grab` — ya no vive en `player.py`: AUD-334 lo movió a
    `resolucion.py` (`_can_ledge_grab = eje_x.repisa_libre` es una asignación,
    no un operador mutadalizable).
- Supervivientes restantes, todos benignos por la clasificación de arriba:
    líneas 84/93/105/118/127 (frames y duraciones de animación), 203 (ruteo de
    `__setattr__`/`__getattr__`), 283 (`combo_active` inicial), 575 (guard de
    estamina), 609 (bit `_hitbox_consumed` redundante: `consume_hitbox()`
    también vacía `_active_hitbox` en la misma línea, la mutación no es
    observable), 670 (`force=True` del DYING), 869 (periodo de parpadeo),
    892 (fps de animación por defecto) y 966 (multiplicador de velocidad
    cenital). La 483 (hurtbox agachado 20×18) ya la defiende aparte
    `tests/test_player_hurtbox.py`, que no entraba en la unión medida.
  Prueba: `mutation_check` con cada suite; unión de muertes documentada arriba.

## ~~[GAP-034] La definición de «verde» del CI depende de una versión que nadie fija~~ *(Resuelto)*

- **File:** `pyproject.toml` (`[project.optional-dependencies] dev`, línea del
  linter), `.github/workflows/ci.yml` (paso *Lint with ruff*)
- **Phase:** auditoría 2026-08-09, AUD-353
- **Reason:** el proyecto declara `ruff>=0.6` sin tope y el CI instala con
  `pip install -e ".[dev]"`, así que el linter que decide si una rama entra es
  **el que hubiera publicado río arriba esa mañana**. No es teórico: ya pasó.
  `AUD-304` añadió un `# noqa: LOG004` legítimo; ruff movió LOG004 a *preview*
  en una versión posterior; con la regla apagada esa directiva pasó a ser un
  `RUF100` («noqa inútil») y **el gate de lint quedó en rojo en `dev` sin que
  cambiara una sola línea del fichero afectado**. Medido con ruff 0.15.20 sobre
  el árbol en el commit 3902137, cuyo mensaje afirma «ruff limpio» — y lo era,
  con la versión de aquel día.

  Las tres pruebas que decían proteger el gate (`test_ruff_sigue_en_el_ci`,
  `test_ruff_no_se_aplica_a_las_entregas`, `test_los_validadores_siguen_en_el_ci`)
  sólo comprobaban que la **orden siguiera escrita** en `ci.yml`. Ninguna la
  ejecutaba, que es la misma familia de defecto que AUD-124 encontró con mypy:
  una herramienta declarada y no ejecutada es documentación, no verificación.

  **Mitigado, no cerrado.** AUD-353 quita la directiva caducada y añade
  `test_ruff_esta_limpio_en_el_alcance_del_ci`, que **ejecuta** ruff sobre el
  alcance leído de `ci.yml` (leído, no copiado: una lista propia se
  desincroniza). Con eso la deriva se detecta en la máquina de quien programa
  y en la primera pasada de CI, en vez de a las semanas. Lo que queda abierto
  es la causa: la versión sigue sin fijar, así que la deriva se **detecta**
  pronto pero se sigue **importando** sin avisar.

  No se pone un tope (`ruff<0.16`) por decisión: congelaría también las reglas
  nuevas que este proyecto ha usado para encontrar defectos reales (B023, DTZ,
  LOG), y un tope que nadie sube envejece hasta ser un pin. La salida limpia es
  fijar la versión exacta en un fichero de herramientas y subirla a mano, con
  su commit, para que actualizar el linter sea un cambio revisable como
  cualquier otro. Eso toca `pyproject.toml`, `requirements.txt` y
  `scripts/check_dependency_sync.py`, que compara los dos: es una decisión de
  política de dependencias del dueño del repositorio, no un arreglo de paso.
- **Coste de no cerrarlo:** una versión de ruff con reglas nuevas o reglas
  movidas puede poner el CI en rojo en cualquier rama, en cualquier momento,
  sin relación con el cambio que se esté revisando. El riesgo real no es el
  rojo: es que un equipo que ve rojos que no ha causado deja de mirar el CI
  (el razonamiento de AUD-106, aplicado a la versión en vez de al alcance).
- **Resolution (AUD-408, 2026-08-11):** la salida limpia que el propio hueco
  describía —fijar la versión exacta con su commit— se tomó en AUD-408:
  `pyproject.toml` pasa de `ruff>=0.6` (sin tope) a `ruff==0.16.1`, la misma
  versión que ya ejecutaba el `.venv` de desarrollo. Con la versión fijada,
  LOG004 vuelve a estar estable (se estabilizó en 0.16.0) y el `# noqa` de
  `diagnostico.py` restaurado en AUD-408 deja de poder caducar por una deriva
  río arriba. `test_ruff_esta_limpio_en_el_alcance_del_ci` sigue ejecutando
  el linter de verdad, y ahora lo ejecuta **contra la versión fijada**:
  detectar la deriva y no importarla quedan cubiertos por la misma línea de
  `pyproject.toml`. `requirements.lock` sólo cubre runtime, así que no hubo
  segundo fichero que sincronizar; si el dueño añade un lockfile de
  herramientas, el pin vive ahí y este hueco se cierra del todo.

## ~~[GAP-035] El detector de huérfanos no ve una función a la que sólo llama su propio `__init__.py`~~ *(Resuelto)*

- **File:** `scripts/check_orphan_systems.py` (`huerfanos()`, `referencias()`)
- **Phase:** auditoría 2026-08-09, AUD-355
- **Reason:** el detector exonera un símbolo en cuanto lo referencia **un
  fichero de producción distinto del que lo define**. Un `from .resolucion
  import resolver_movimiento` en el `__init__.py` del paquete es un fichero
  distinto, así que **toda la superficie pública re-exportada por un paquete
  queda automáticamente exonerada**, la llame el juego o no.

  Es lo que dejó pasar AUD-355: la verja de datos hostiles de AUD-344 se
  escribió dentro de `resolver_movimiento`, que ninguna entidad llama —el
  jugador compone los pasos a mano—, y el detector la dio por conectada
  porque `src/framework/physics/__init__.py` la re-exporta. Una protección
  con pruebas en verde que no protegía nada, y el guardián que existe
  precisamente para eso no dijo ni una palabra.

- **Por qué no se corrige aquí, medido:** el arreglo evidente —no contar los
  `__init__.py` como consumidores— se probó antes de escribir esta entrada.
  Resultado: **212 huérfanos → 224**, doce nuevos, y once son **falsos
  positivos**: `WalkingState`, `LedgeGrabState`, `AerialSlamState` y compañía
  son estados vivos que sus módulos hermanos instancian con un import diferido
  dentro del propio fichero (`grounded.py:68`, `wall.py:30`,
  `airborne.py:211`), y `Contacto` es el tipo de retorno de medio módulo. La
  única captura real de las doce es `resolver_movimiento`.

  Once falsos por uno verdadero convierte el informe en ruido, y un guardián
  ruidoso se desactiva —el mismo razonamiento de AUD-106 con el lint de las
  entregas—. La regla correcta no es «ignorar `__init__.py`» sino «un import
  o un `__all__` no es una llamada»: distinguir referencia de invocación
  exige mirar `ast.Call` y la cadena de atributos, no el nombre suelto, y eso
  es reescribir el analizador, no parchear una condición.
- **Coste de no cerrarlo:** cualquier función pública re-exportada por un
  paquete puede quedarse sin llamantes —o nacer sin ellos, como pasó aquí— sin
  que ningún gate lo note. Afecta a los `__init__.py` de `framework/physics`,
  `framework/entities/states`, `engine/render` y `framework/academic`.

- **Resolution (2026-08-09, AUD-364):** cerrado con una regla **estrecha**, no
  con la reescritura. Las dos alternativas anchas se midieron antes de
  descartarlas y las dos salen peor que no hacer nada: ignorar los
  `__init__.py` da 212 → 224 huérfanos con **11 falsos de 12**, y «un import no
  es un uso» da 212 → 268 con **56 falsos de 56** (`Events`, `Action`,
  `PhysicsProfile` y `VisionTools` se usan por *atributo*, no por llamada).
  Lo que entra es una sección **informativa y nunca bloqueante** —«sólo los
  re-exporta su paquete»— con los símbolos cuyo único consumidor de producción
  es un `__init__.py`: doce entradas, que es lo que un humano tría una vez.
  Triadas las doce en `VERIFICADOS` con su motivo; la sección queda en
  «(ninguno)», que es lo que debe ser un cable trampa. La regla correcta de
  verdad —distinguir uso de mención resolviendo ámbitos— sigue siendo
  reescribir el analizador, y sigue sin merecer la pena.

- **Resolution (2026-08-09, AUD-369):** los dos linters van **fijados**:
  `ruff==0.15.20` y `mypy==2.2.0` en el extra `dev` de `pyproject.toml`, con la
  política escrita al lado. Fijar no congela: convierte subir el linter en un
  cambio revisable —su commit, su `AUD-NNN`— y las reglas nuevas se adoptan
  mirando lo que encuentran, en vez de descubriéndolas en rojo un lunes.
  `mypy` entra por la misma exposición: un comprobador de tipos que cambia de
  opinión solo tumba el trinquete de AUD-124.
  Lo vigila `test_los_linters_van_fijados_y_no_con_mayor_o_igual`, que se
  comprobó en rojo volviendo a `ruff>=0.6` antes de darlo por bueno. La
  mitigación de AUD-353 —ejecutar ruff dentro de la suite— se queda: fijar
  evita la deriva, ejecutarlo la detecta si aun así ocurre.

---

# Huecos abiertos por la lista del dueño (2026-08-10, AUD-371)

Los catorce de abajo salen de contrastar la lista de mejoras de 2026-08-10
contra el árbol. **No son todo lo que la lista pedía**: la mayor parte de sus
filas ya existe y está probada, y eso se detalla en
`docs/87_REPORTE_DE_LO_QUE_FALTA.md` §28. Aquí sólo queda lo que de verdad no
está.

## ~~[GAP-036] El bucle no tiene paso fijo ni interpolación~~ *(Resuelto — el paso fijo; la interpolación se deja fuera con motivo)*

- **File:** `src/engine/core/app.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** `App.run` integra con `dt` variable y punto. No hay acumulador,
  no hay `fixed_update` y no hay interpolación al pintar. Lo que sí hay es el
  tope `MAX_FRAME_TIME = 0.05`, que evita atravesar paredes por un tirón
  convirtiéndolo en cámara lenta — mitiga el síntoma peor sin dar
  reproducibilidad. Es el único cambio *estructural* que pide la lista.
- **Resolution plan:** No planificado, y no por pereza: toda la calibración de
  física está atada al `dt` variable. `test_calibracion_del_salto` fija el
  salto en 72 px, que es la unidad con la que están medidos los 16 mapas de
  `assets/` y las guías de diseño de nivel. Un paso fijo cambia la
  integración y por tanto la altura, así que el trabajo real no es el acumulador —es media tarde— sino
  re-calibrar el salto y revisar los mapas. Hacerlo exige decisión del dueño
  sobre romper la métrica de 72 px. Ver §28.3 de `docs/87`.

- **Resolution (2026-08-10, AUD-390): la re-calibración no hizo falta, y el
  defecto era peor de lo que decía este hueco.**

  Esta entrada hablaba de reproducibilidad y de replays. Lo que había debajo es
  que **la física dependía de los fotogramas por segundo de la máquina**.
  Simulado sobre la integración real del salto::

      120 fps -> 88,67 px | 60 -> 87,11 | 30 -> 84,00 | 20 fps -> 81,00

  Un jugador con equipo lento salta **un 7 % menos alto**, o sea más de un
  tercio de baldosa, y los dieciséis mapas están medidos contra los 72 px de 60
  fps: un obstáculo ajustado al límite era franqueable o no **según el
  hardware**.

  **La clave del lote es `FIXED_DT = 1/TARGET_FPS`.** A 60 fps eso da un paso
  por fotograma del mismo tamaño que el `dt` variable de antes, así que la
  integración es idéntica y ningún mapa cambia; el fotograma lento, que antes
  se integraba de una vez, ahora se reparte y **converge** al valor que los
  mapas suponen. Cualquier otro valor habría obligado a re-calibrar de verdad.

  Verificado, no supuesto: **111 pruebas de calibración, física del jugador,
  perfiles y pendientes, verdes sin tocar un número.**

  Tres decisiones del acumulador: el sobrante se guarda (a 120 fps, tirarlo
  dejaría el juego a media velocidad); las transiciones siguen con `dt`
  variable porque son presentación y trocearlas produce parpadeo; y el tope de
  5 pasos corta la espiral de la muerte **tirando** el tiempo sobrante, porque
  conservarlo deja una deuda impagable.

  **La interpolación se deja fuera a propósito**, y por eso este hueco no se
  marca resuelto del todo: con paso de 1/60 a 60 fps el fotograma casi siempre
  cae sobre un paso, así que no hay nada visible que interpolar. Se hará el día
  que se note.

## ~~[GAP-037] La rejilla espacial existe y las colisiones no la usan~~ *(Resuelto)*

- **File:** `src/framework/stage/rejilla.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** `RejillaEspacial` (AUD-276) ya da las tres operaciones que pide
  la lista —`cercanos()` (fase amplia), `rayo()` (trazado) y `hay_vision()`
  (línea de visión)— y está probada en
  `tests/test_rejilla_espacial_y_raycast.py`. Su **único consumidor de
  producción es `vfx/sombras_proyectadas.py`**. Ni `framework/physics/resolucion.py`
  ni `stage/collision_system.py` la construyen: el camino de colisión sigue
  recorriendo `stage.collision_rects` entero, que es exactamente lo que la
  rejilla se escribió para evitar. `stage4_1` trae miles de rectángulos y la
  inmensa mayoría están a pantallas de distancia de la pregunta.
- **Resolution plan:** Viable y barato — la pieza está hecha y probada; falta
  construirla una vez por escenario y llamar a `cercanos()` desde el resolutor.
  Reservado **AUD-372**. Es el candidato con mejor relación coste/ganancia de
  toda la lista.

- **Resolution (2026-08-10, AUD-379): medido en contra, y la premisa era
  falsa.** Este hueco decía que «`stage4_1` trae miles de rectángulos», copiando
  el docstring de `rejilla.py`. **Son 51**, y el resto de mapas están por
  debajo: el segundo es `stage1_2_la_soda` con 27. No hay fusión de
  rectángulos en el cargador; sencillamente los mapas no son tan densos.

  Medido sobre `stage4_1`, con el cuerpo en el centro y 4 rectángulos cerca::

      lista completa : 0,0419 ms/fotograma
      con rejilla    : 0,0310 ms/fotograma   (1,35x)

  Son **0,011 ms** de un presupuesto de 16,67 — un 0,07%. A cambio habría que
  mantener un índice que se desincroniza con lo que ya recompone la escena cada
  fotograma (plataformas móviles, bloques, interactivos), y una ruta nueva que
  probar. No se hace.

  **No invalida la rejilla.** `rayo()` y `hay_vision()` contestan «¿qué hay
  entre estos dos puntos?», que ninguna lista contesta por barrido, y siguen
  siendo la base de GAP-046 (la percepción de enemigos). Lo que se cae es sólo
  el argumento de la fase amplia — y de paso explica por qué
  `sombras_proyectadas` dice, medido, que la rejilla «no cambia el resultado».

  La decisión se vigila sola:
  `tests/test_los_mapas_no_traen_miles_de_rectangulos.py` se pone rojo si algún
  mapa supera 500 rectángulos, que es donde la medición dejaría de valer.
  **AUD-372**, que estaba reservado para el cableado, queda libre.

## ~~[GAP-038] No hay capas ni máscaras de colisión~~ *(Resuelto — capas propias sobre el AABB, sin pymunk)*

- **File:** `src/framework/stage/collision_system.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376) — ya registrado
  como refactor **R-03** en `docs/AUDIT_2026-07.es.md`
- **Reason:** El filtrado de hoy es por tipo de entidad, escrito a mano en cada
  llamada. No es un descuido nuevo: AUD-004 retiró una fachada de pymunk que
  *aparentaba* tener categorías de colisión y no las tenía —las constantes
  `_CAT_*` se asignaban a `shape.collision_type` (clave de despacho) en vez de
  a `shape.filter` (el bitmask real), y nunca se registró un manejador, así que
  no filtraban nada—. La fachada se quitó en vez de dejarla mintiendo.
- **Resolution plan:** Es la decisión R-03, todavía abierta: o se conecta una
  tubería de cuerpo rígido de verdad (cuerpos, `shape.filter`, manejadores,
  rectángulos estáticos **fusionados**, plataformas unidireccionales reales) o
  se implementan capas propias sobre el resolutor AABB actual. La segunda es
  mucho más barata y encaja con lo que ya hay. Aviso heredado de la auditoría
  de julio: si vuelve pymunk, no puede volver sin fusión de rectángulos —
  `add_static_collision` creaba un cuerpo+forma por tile, miles de cajas.

- **Resolution (2026-08-11, AUD-395): capas propias, segunda opción de R-03.**
  Decisión del dueño: no vuelve pymunk. `src/framework/physics/capas.py` es lo
  que aquella fachada aparentaba ser, en ~60 líneas y sin dependencia nueva:
  `Capa` es un `IntFlag` —`SOLIDO`, `PLATAFORMA`, `DESTRUCTIBLE`, `PUERTA`—
  porque la pregunta que se hace no es «¿de qué clase eres?» sino «¿estás entre
  las que me frenan?», y eso es una intersección de bits.
  `MapaDeCapas.solidos_para(mascara)` responde la pregunta que antes no tenía
  dónde vivir. `BaseEntity.mascara_de_colision` la declara por especie, en una
  línea, como atributo de clase.
  Lo que se descubrió al entrar: **la capa ya existía, cableada**.
  `_load_collision` decidía `Platform` o no-`Platform` y guardaba esa decisión
  en *qué lista* iba a parar. Era una capa binaria imposible de consultar o
  ampliar, y por eso cada consumidor la recomponía a mano —`bloques.py` suma
  tres listas, una entrega de estudiante suma dos, `StageScene` pasaba las dos
  a todos los enemigos por igual—.
  Compatibilidad: `collision_rects` y `one_way_rects` **no cambian de tipo** —
  las leen las 26 entregas, el arco del jefe, la cámara y el calificador—; el
  mapa de capas se publica al lado y el cargador llena las dos vistas juntas
  para que no puedan discrepar. `MASCARA_POR_DEFECTO` es `SOLIDO | PLATAFORMA`
  y no `TODO`, a propósito: con `TODO`, una entidad que nunca había visto un
  destructible empezaría a chocar con él y eso cambiaría los mapas entregados
  sin que nadie lo pidiera.
  Fuera de alcance, y dicho: el filtrado **por tipo de entidad** del combate
  sigue escrito a mano —`process_attack` recorre `entity_list` con
  `isinstance(EnemyBase)` y `_procesar_bash` la recorre otra vez con
  `isinstance(Projectile)`—. Son capas de *daño*, no de colisión geométrica,
  y unificarlas cambia el orden de resolución de los golpes; se deja como
  trabajo aparte en vez de colarlo aquí.
  Cable trampa: `tests/test_capas_de_colision.py` (12 pruebas), con una que
  comprueba que la máscara por defecto sigue viendo exactamente lo que se veía
  antes en `stage0`.

## ~~[GAP-039] Sin materiales de superficie: hay fricción, no hay restitución~~ *(Resuelto)*

- **File:** `src/framework/physics/perfil.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** La fricción por superficie desde el TMX existe (`ZonaDeFriccion`
  + `sistema_friccion`, AUD-236) y el perfil declara `aceleracion`/`friccion`
  (AUD-336). Lo que no existe es un **material** como cosa nombrada que agrupe
  fricción y restitución y se declare en el tileset en vez de por zona. Sin
  restitución no hay rebote: hielo y musgo se pueden expresar hoy, goma no.
- **Resolution plan:** Viable sin tocar el bucle: un `Material` con
  `friccion`/`restitucion` leído del tileset, consumido por `resolver_eje_y`.
  Sin fecha; no lo pide ningún nivel existente.

- **Resolution (2026-08-11, AUD-396):** hecho, y sin tocar el bucle como decía
  el plan. `Material` es un dataclass **congelado** en `physics/perfil.py` —un
  material es una constante del mundo, no un estado: dos plataformas de goma
  comparten instancia y nadie debe poder ablandar una desde otro sitio—, con
  catálogo `ROCA`/`HIELO`/`MUSGO`/`GOMA` y un índice `MATERIALES` por nombre,
  que es lo que permitirá declararlos desde datos.
  `PhysicsProfile.material` por defecto `ROCA` (restitución 0): los dieciséis
  mapas entregados se juegan exactamente igual. `EstadoDeMovimiento.restitucion`
  la lleva al resolutor, y el jugador la pone desde su perfil — el resolutor no
  sabe de materiales, sólo del número, que es la misma división que ya hace
  `Contacto` al dar hechos en vez de reglas.
  Lo que costó de verdad no fue el rebote sino **terminarlo**: sin umbral, un
  cuerpo sobre goma nunca acaba de posarse —botes cada vez más pequeños que no
  llegan a cero, `en_el_suelo` parpadeando cada fotograma y la máquina de
  estados entrando y saliendo de «en el aire» para siempre—. `_UMBRAL_DE_REBOTE`
  corta por debajo de lo que la gravedad acumula en dos fotogramas, y hay dos
  pruebas sobre eso, una de ellas dejando caer el cuerpo diez segundos para
  comprobar que acaba quieto.
  La restitución de `GOMA` es 0,6 y no más: por encima de ~0,8 el rebote tarda
  tanto en amortiguarse que el jugador pierde el control varios segundos, y eso
  se lee como un fallo, no como una mecánica.
  Fuera de alcance, y dicho: **no se lee del tileset todavía**. El plan lo
  proponía y el catálogo ya está preparado para ello (`MATERIALES` indexa por
  nombre justo para eso), pero ningún mapa pide hoy una superficie que rebote y
  cablear el TMX sin un mapa que lo use sería otro sistema sin consumidor. El
  consumidor que sí existe es el perfil de física, que ya se aplica por
  escenario.
  Cable trampa: `tests/test_materiales_de_superficie.py` (14 pruebas).

## ~~[GAP-040] El buffer de entrada existe sólo para el salto, y vive en el jugador~~ *(Resuelto)*

- **File:** `src/framework/entities/player.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** Hay salto con buffer (`_pending_jump`, ~5 fotogramas) y hay
  *coyote time* (`PhysicsProfile.coyote_frames`), o sea que las dos concesiones
  clásicas de *game feel* están. Pero el buffer está cableado a mano dentro de
  `Player.update` para una sola acción: ninguna otra —ataque, dash, parry— lo
  tiene, y `InputManager` no ofrece la primitiva. Tampoco hay prioridad entre
  acciones cuando dos caen en el mismo fotograma.
- **Resolution plan:** Subir el buffer a `InputManager` como ventana por
  acción, dejando el salto llamando a la primitiva nueva. Reservado
  **AUD-373**. Barato y sin riesgo para la calibración: no toca la integración.

- **Resolution (2026-08-11, AUD-373):** hecho tal como decía el plan, y sin
  mover la calibración: las siete pruebas de `test_calibracion_del_salto.py`
  —las que miden cuántas baldosas se cruzan— pasan sin tocarlas.
  `InputManager.pulsada_en_buffer(accion, ventana)` y `consumir_buffer(accion)`
  cuentan en **fotogramas** de `pump()` y no en segundos: el buffer es una
  concesión al tiempo de reacción humano, y desde AUD-390 la simulación avanza
  a paso fijo, así que contar fotogramas es determinista. La ventana por
  defecto son los 8 fotogramas (~133 ms) que ya usaba el salto, conservados
  para no re-calibrar de paso algo que estaba ajustado.
  Consumidores: el salto —que deja de tener mecanismo propio; `pending_jump` y
  `pending_jump_timer` salen de `PlayerStateData`, y `AirborneState` ya no
  arma nada a mano— y el dash, que es lo que el hueco pedía. El dash usa un
  campo aparte del snapshot (`dash_en_buffer`) y sólo en los estados de suelo:
  meterlo en `dash_pressed` habría cambiado también el dash en el aire, y lo
  que se describe es el que se pierde **al aterrizar**.
  Sin cerrar, y dicho aquí en vez de fingir que estaba en el alcance: **la
  prioridad entre acciones que caen en el mismo fotograma** sigue sin existir.
  No apareció ningún caso real al medir —el orden de los `if` de cada estado ya
  la impone de hecho— y sin un caso que la pida sería un mecanismo sin
  consumidor.
  Efecto colateral que merece constar: al migrar, dos pruebas de
  `test_sensacion_y_camara.py` que comprobaban el buffer buscando subcadenas en
  el fuente (`"_pending_jump = True"`, `"8.0 / 60.0"`) **siguieron en verde**
  con el mecanismo ya retirado, porque el código viejo quedó citado en el
  comentario que explica adónde se fue. Las dos se reescribieron para ejercitar
  comportamiento.

## ~~[GAP-041] El ECS no recicla identificadores, no agrupa componentes y no serializa~~ *(Resuelto — la premisa era falsa; se mide y se cierra sin tocar el ECS)*

- **File:** `src/framework/ecs/world.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** `crear()` incrementa un contador monótono y `aplicar_bajas()` no
  devuelve el id al saco, así que un escenario que cree y destruya mucho
  —balas, partículas— hace crecer el espacio de ids sin techo. No hay *pools*
  de componentes (cada uno es un objeto suelto) ni forma de volcar el mundo a
  disco. Las consultas `cada()`/`con()` son recorrido lineal sobre el índice
  por tipo, no arquetipos.
- **Resolution plan:** Ninguno de los tres duele hoy: el enjambre de balas ya
  esquiva el ECS entero por NumPy (`bullet_swarm.py`, 180×), que era el caso
  que lo habría dolido. Reciclar ids es media hora y no rompe nada; los pools y
  los arquetipos son optimización sin medición que la respalde, y este repo no
  optimiza sin medir antes (AUD-329, AUD-330).

- **Resolution (2026-08-11, AUD-394): la premisa no se sostiene, y el ECS no
  se toca.** El plan decía «reciclar ids es media hora y no rompe nada».
  `world.py:70` dice lo contrario y como decisión deliberada: *«un
  identificador nunca se reutiliza […] reciclarlos produce el peor error de
  esta arquitectura»* —el id colgante—. Uno de los dos estaba mal. Medido, el
  hueco, por tres motivos independientes de los que basta uno:
  1. **Las balas no entran al mundo de la escena.** `adoptar_en` es la única
     puerta a ese mundo y se llama desde exactamente dos sitios, los dos
     dentro de `_poblar_mundo_ecs`, al montar. Ninguno en runtime. Un
     `Projectile` vive en el mundo **privado** que cada `BaseEntity` construye
     para sí (`bridge.py:66`), donde su id es siempre 1.
  2. **El contador se reinicia en cada montaje**: `_poblar_mundo_ecs` hace
     `self._mundo = World()`, así que no acumula ni entre respawns.
  3. **El consumo por montaje es diminuto**: medido sobre los 17 mapas, 37 ids
     en el peor (`stage_mecanicas`) y 1 en el más vacío.

  A 37 por montaje, agotar los enteros pequeños de CPython pediría del orden de
  29 millones de cargas de escenario. Los pools y los arquetipos siguen siendo
  optimización sin medición que la respalde, que es lo que el propio plan ya
  decía; la serialización del mundo no la pide nada hoy y, si se pide, es un
  hueco nuevo y con otro nombre.

  No se cambia una línea de `world.py`: lo que faltaba no era código, era la
  medición que respalda la decisión que ya estaba tomada. Lo que sí se añade es
  `tests/test_los_ids_del_ecs_no_crecen.py` (20 pruebas), que fija las **tres
  condiciones** de arriba — sobre todo la primera, porque el día que alguien
  quiera que el viento empuje a los proyectiles, `adoptar_en` en runtime es la
  forma obvia de conseguirlo y ahí sí empezaría el crecimiento que el hueco
  describía.

## ~~[GAP-042] No hay determinismo reproducible~~ *(Resuelto)*

- **File:** `src/engine/core/app.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** No hay una sola llamada a `random.seed()` en `src/engine` ni en
  `src/framework`. Todo lo aleatorio —partículas, sacudida de cámara,
  dispersión de disparos, comportamiento de enemigos— tira del `random` global
  sin semilla, así que dos ejecuciones del mismo escenario no coinciden. Afecta
  a tres cosas concretas: el fantasma del speedrun no se puede validar contra
  una repetición, un fallo de física no se puede reproducir desde un informe, y
  las pruebas que tocan azar se escriben tolerantes en vez de exactas.
- **Resolution plan:** Sembrar en `App.__init__` desde una semilla guardada en
  la partida, y pasar un `random.Random` propio a los sistemas que lo pidan en
  vez del global. Lo segundo es lo caro: hay que auditar cada uso. Sin fecha.

- **Resolution (2026-08-11, AUD-398): los tres que quedaban, aislados.**
  `ambient_particles`, `weather_system` y `camera` aceptan `rng` y, sin él,
  nacen de `azar.generador()` — que deriva del global ya sembrado, así que la
  partida es tan reproducible como antes y ni un mapa cambia.
  Por qué importaba si ya estaban sembrados, que es la parte no obvia: **ya
  eran reproducibles y no eran independientes**. Compartiendo un generador, el
  orden de las llamadas entre módulos forma parte del resultado, así que añadir
  una partícula de ambiente desplazaba la secuencia que después leían el clima
  y la cámara y la misma semilla daba otra sacudida. Un determinismo que se
  rompe al tocar un módulo vecino no sirve para lo que se pidió —reproducir un
  fallo desde un informe, validar el fantasma del speedrun contra una
  repetición—, porque cualquier cambio en cualquier sitio lo invalida. Hay una
  prueba justamente de eso: gastar azar en las partículas ya no mueve la cámara.
  Efecto secundario obligado: `WeatherSystem._espera_hasta_el_proximo_rayo`
  deja de ser `@staticmethod`. La espera sale del generador de **esa** tormenta,
  y un método estático no tiene de dónde sacarlo.
  Dos falsos verdes propios, cazados escribiendo las pruebas y anotados porque
  son el mismo error dos veces: la primera versión leía `cam.offset.x` —que sin
  objetivo al que seguir vale 0,0— y además no le daba objetivo a la cámara, así
  que `update()` salía temprano. Las dos pruebas comparaban listas de ceros y
  pasaban con el azar completamente roto.
  Cable trampa: `tests/test_azar_aislado.py` (8 pruebas), con una comprobación
  por AST de que ninguno de los tres vuelve a llamar a `random.*` de módulo —
  por AST y no por texto, porque `import random` y el tipo `random.Random |
  None` de la firma son legítimos y un `grep` los daría por infracciones.

- **Avance (2026-08-10, AUD-374):** el primer consumidor ya lo tiene.
  `WorldSimulation` acepta un `rng: random.Random` propio y lo usa para la
  dirección del viento, así que una tormenta se repite en una prueba fijando la
  semilla. Es un ladrillo, no el cierre: el resto del motor sigue tirando del
  `random` global. El hueco sigue abierto.

- **Avance (2026-08-10, AUD-375):** la semilla del proceso ya existe.
  `engine/core/azar.py` la fija (`sembrar`), la recuerda (`semilla_actual`) y
  **la escribe en el registro** con `INFO`; `App` la siembra justo después de
  configurar el registro —el orden importa: al revés se pierde la única línea
  que hace reproducible un informe— y `main.py` la acepta por `--semilla` en
  las tres rutas de arranque.

  Lo que esto cambia: con el generador global sembrado, los 46 usos de
  `random.*` del motor **ya son reproducibles** sin tocarlos. Un informe de
  fallo lleva su semilla dentro sin que el jugador sepa qué es una semilla.

- **Corrección (2026-08-10, AUD-385): eran 46 de 66.** Lo de arriba es cierto y
  estaba incompleto: NumPy mantiene **su propio** generador global y
  `random.seed()` no lo toca. Hay **20 usos de `np.random`**, y doce están en
  `vfx/particle_system.py`, que dibuja todas las partículas del juego. O sea
  que la partida seguía sin poder repetirse justo en lo más visible mientras
  AUD-375 daba el asunto por cerrado. Demostrado sobre el sistema real: dos
  ráfagas con la misma semilla daban velocidades de -39,565 y 23,154.

  `sembrar()` siembra ahora los dos. Se descubrió al empezar el aislamiento y
  mirar **de qué generador tira cada módulo**, en vez de fiarse del recuento de
  `random.*` — que sólo contaba la mitad de la historia.

  Lo que falta, y por qué el hueco sigue abierto: darle a cada sistema su
  propio `random.Random` (`azar.generador`), que es aislamiento, no
  reproducibilidad — hoy catorce módulos compiten por el estado global, así que
  añadir una tirada en las partículas desplaza la dispersión de los disparos.
  Y la reproducibilidad de **trayectoria** —el mismo replay bit a bit— sigue
  necesitando el paso fijo de GAP-036: con `dt` variable dos ejecuciones
  divergen aunque el azar coincida.

## ~~[GAP-043] No hay tipos de daño, armadura ni resistencias~~ *(Resuelto)*

- **File:** `src/framework/stage/collision_system.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** `_calculate_damage` produce un escalar. No hay canal —físico,
  fuego, veneno— ni mitigación por tipo, así que un enemigo no puede ser débil
  a una cosa y resistente a otra. Es una carencia de **diseño de juego**, no un
  defecto: nada de lo que hay hoy lo pide.
- **Resolution plan:** No hacerlo hasta que un jefe o un enemigo lo necesite.
  Meterlo antes es superficie que mantener sin lector, que es el mismo
  razonamiento con el que la invariante 5 decide qué se traduce.

- **Resolution (2026-08-10, AUD-387):** hecho por decisión del dueño, que
  eligió el modelo de datos: catálogo en `data/damage_types.json` y
  resistencias declaradas en Tiled.

  Tres canales de salida —`fisico`, `veneno`, `fuego`— y no una lista genérica:
  son los que el lore sostiene (`veneno` aparece ocho veces en
  `65_EL_LORE_EXTENSO.md`, `fuego` tres; hielo y electricidad, ninguna). Un
  canal sin contenido detrás es una característica que nadie usa, que es lo que
  GAP-052 vino a cerrar.

  **La restricción que mandó sobre el diseño:** `apply_hit` tiene 32 llamantes
  y **26 están en `src/stages/`**. Por eso `canal` va al final y opcional, y
  `EnemyBase.resistencias` nace vacío: un enemigo que nadie toque se comporta
  exactamente igual que antes, y ésa es la primera prueba del fichero.

  El factor es multiplicador y no porcentaje restado, porque el mismo número
  dice las tres cosas: `0.5` resiste, `2.0` es débil, `0.0` es inmune. Un
  bestiario se vuelve interesante por las debilidades.

  **Y cerró de paso una promesa rota del spec.** `06_TMX_SPEC.md` documentaba
  `damage_type` en `HazardZone` como «no está implementada» desde AUD-310, con
  una prueba vigilando que siguiera sin estarlo. No era descuido: sin canales,
  prometer un *tipo* cuando el motor sólo sabe restar un número es prometer
  nada. Ahora existe, con el nombre que el documento prometía —para que un mapa
  que la escribiera confiando en él funcione sin cambios—.

  21 pruebas nuevas. Falta la armadura como estadística aparte, que va con los
  efectos temporales de GAP-044.

## ~~[GAP-044] No hay sistema de buff/debuff~~ *(Resuelto)*

- **File:** `src/framework/entities/player_state.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** Cero coincidencias en `src/`. Hay efectos temporales sueltos
  —`damage_mult`, `invincibility_timer`— cada uno con su temporizador a mano
  dentro de `PlayerStateData`. Lo que falta es la abstracción que los agrupe:
  efecto con duración, acumulación y caducidad, aplicable también a enemigos.
- **Resolution plan:** Encaja limpio como componente ECS. Sin fecha; mismo
  razonamiento que GAP-043 — el árbol de habilidades (AUD-293) da mejoras
  permanentes, no temporales, y nadie ha pedido temporales.

- **Resolution (2026-08-10, AUD-388):** hecho por decisión del dueño, que
  eligió el componente ECS con efectos declarados en datos y las cuatro
  estadísticas modificables: daño infligido, daño recibido, velocidad y daño
  por segundo.

  **Nace con consumidor**, que es la lección de los diez lotes anteriores de
  esta fase: una `HazardZone` con `damage_type="veneno"` (AUD-387) ya no sólo
  pica, envenena, y el efecto sigue restando cuando el jugador ha salido de la
  charca. Ésa es la única diferencia observable entre *un tipo de daño* y *una
  cantidad*; sin ella el canal veneno era daño físico con otro nombre.

  Cuatro decisiones: reaplicar **refresca** y no acumula (dos charcas no
  envenenan el doble); los factores **multiplican** y no suman (`0,65 × 0,8` es
  lento, `−0,35 − 0,2` acabaría andando hacia atrás); la correspondencia
  canal→efecto es **por nombre** y no una tabla aparte (un tercer sitio que
  sincronizar es un sitio donde olvidarse); y el sistema corre en `ZONAS + 5`,
  después de las zonas letales, para que el primer tick no se cobre en el mismo
  fotograma y se lea como daño doble.

  El componente es el mismo para jugador y enemigos, que era justo lo imposible
  con los temporizadores sueltos de `PlayerStateData`.

  21 pruebas nuevas. Falta absorber los temporizadores que ya existían
  (`damage_mult`, `invincibility_timer`): el catálogo ya trae `fuerza` y
  `escudo` para hacerlo, pero migrarlos cambia el comportamiento del jugador y
  va en su propio lote.

## ~~[GAP-045] No hay pathfinding ni árbol de comportamiento~~ *(Resuelto — el A*; el BT sigue descartado)*

- **File:** `src/framework/entities/enemy_base.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** Los enemigos usan máquina de estados (13 estados, incluido
  `TELEGRAPHING`) y `squad_brain.py` para coordinación con scikit-learn. No hay
  A*, ni malla de navegación, ni árbol de comportamiento. En la práctica los
  enemigos persiguen en línea recta y caen por los huecos.
- **Resolution plan:** El A* sobre la rejilla de tiles es viable y la rejilla
  espacial de GAP-037 le sirve de base. El árbol de comportamiento es otra
  historia: la invariante 7 pide no meter maquinaria donde una FSM determinista
  rinde igual, y con 13 estados por enemigo nadie ha enseñado que rinda peor.
  Hacer A* sí; BT sólo con un caso que la FSM no pueda expresar.

- **Resolution (2026-08-10, AUD-389):** A* sobre tiles, hecho, con el diseño
  que eligió el dueño —waypoints como pista y recálculo por cadencia
  escalonada—. `framework/ai/navegacion.py`.

  **No es un sistema buscando quién lo use.** `sistema_acosador` perseguía con
  `hacia.normalize()`: línea recta, atravesando muros. Un perseguidor que se
  empotra y tiembla contra una pared no da la tensión de Nemesis que su propio
  docstring describe. El A* es el arreglo de ese comportamiento.

  **Lo que cuesta, medido** sobre `stage4_1` (malla de 60×240 celdas, 3.230
  bloqueadas) a la distancia real de persecución (480 px = 30 celdas):

  | Tope de nodos | ms/consulta | Rutas halladas |
  |---|---|---|
  | 1.500 | 3,616 | 192/200 |
  | 400 | 1,830 | 80/200 |
  | 150 | 0,877 | 39/200 |

  Bajar el tope abarata y **rompe la característica**, así que lo que se acota
  no es el coste de cada A* sino cuántos se hacen por fotograma. Con la
  cadencia de 4 Hz escalonada: 1 navegante 0,241 ms (1,4 % del presupuesto), 4
  navegantes 0,964 ms, **30 navegantes 7,232 ms (43 %)**. El envolvente
  utilizable son unos pocos, que es el caso para el que existe.

  Sin diagonales a propósito: un paso diagonal atraviesa la esquina entre dos
  muros y produce rutas que el cuerpo no puede recorrer.

  **El árbol de comportamiento sigue descartado**, por la invariante 7 y porque
  nadie ha enseñado que la FSM de 13 estados rinda peor.

## ~~[GAP-046] La percepción de enemigos vive en código de escenario~~ *(Resuelto — la premisa era falsa)*

- **File:** `src/stages/stage1_1/combat/guard_system.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** El cono de visión y el perseguidor —el sigilo de la fase 5— están
  implementados dentro de un escenario, no en el framework. Cualquier otro
  escenario que quiera un guardia lo copia. Y la pieza que lo haría bien ya
  existe fuera: `RejillaEspacial.hay_vision()` (ver GAP-037).
- **Resolution plan:** Subir la percepción —visión con cono y oclusión por
  `hay_vision()`, más oído por radio— a `framework/entities/` como componente,
  dejando el guardia del escenario como primer consumidor. Nota de alcance:
  `revisar/` no se toca (invariante 3), pero `src/stages/stage1_1` sí es
  material del repo.

- **Resolution (2026-08-10, AUD-381): la premisa era falsa, y debajo había un
  defecto distinto y peor.**

  La percepción **no** vive en código de escenario. `ConoDeVision` es un
  componente del ECS (`framework/ecs/components.py`), con su sistema
  (`sistema_conos_de_vision`), su `Alerta` de cuatro estados y su gizmo de
  depuración (`stage/gizmos.py`). Su propio docstring dice que existe «para no
  reescribirlo cada estudiante que quiera un guardia» — justo lo contrario de
  lo que este hueco afirmaba. El error vino de asociar
  `stages/stage1_1/combat/guard_system.py` con un guardia enemigo: es la
  mecánica de **defensa del jugador** (bloquear), y coincidió en una búsqueda
  por texto.

  Lo que sí era cierto, y no lo decía este hueco: **el cono no comprobaba
  oclusión**. Decidía con distancia y ángulo, así que un vigilante al otro lado
  de un muro veía igual que si el muro no existiera. Es el mismo defecto que
  AUD-278 arregló para la luz, abierto todavía para la vista, y cambia una
  regla del juego en vez de un píxel: el sigilo con muros no funcionaba y un
  nivel diseñado alrededor de esconderse no se podía hacer.

  Y la pieza que lo resuelve estaba escrita **para esto**: `RejillaEspacial`
  (AUD-276) se justificaba diciendo «sin esto no se puede hacer la línea de
  visión de un guardia». Se construyó `hay_vision()`, se probó, y el guardia se
  escribió después sin llamarla — la misma especie que domina esta fase, con la
  vuelta de tuerca de que el consumidor previsto llegó más tarde y no la usó.

  Arreglado en `sistema_conos_de_vision`, con la geometría llegando por recurso
  del mundo (`poner_recurso("geometria", ...)`, el canal que el ECS ya usa para
  `reloj_musical`). Sin recurso publicado el sistema se comporta exactamente
  como antes, que es lo correcto: un mundo desnudo no permite deducir que hay un
  muro. Se publican los sólidos del mapa y no los de la escena compuesta —las
  plataformas móviles cambian cada fotograma y reindexarlas devolvería el coste
  que AUD-379 descartó; un muro no se mueve—. 6 pruebas nuevas.

## ~~[GAP-047] No hay sistema de misiones ni objetivos~~ *(Resuelto)*

- **File:** `src/framework/stage/progression_system.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** Cero coincidencias de `mision`/`objective`/`quest` en `src/`.
  `progression_system.py` lleva el avance entre escenarios y `zone_flags` en la
  partida, que es otra cosa: no hay objetivos declarados, ni seguimiento, ni
  estado de completado por objetivo. El diálogo (`DialogueSystem._execute_action`)
  ya ejecuta acciones, así que el enganche existe.
- **Resolution plan:** Sin fecha. Es contenido narrativo, y la fase 7 del plan
  del motor —reconstrucción de contenido— está suspendida por decisión del
  dueño (`docs/87` §27).

- **Resolution (2026-08-11, AUD-400):** el dueño **levantó la suspensión** de la
  fase 7 ese día y pidió cerrarlo. Se hace constar porque el plan de arriba
  decía lo contrario y sigue escrito.
  `src/framework/stage/objetivos.py`: `Objetivo` (id, texto, tipo, objetivo,
  cantidad, opcional) y `SistemaDeObjetivos`, que **no inventa ninguna fuente de
  verdad**: se suscribe a los eventos que el juego ya emitía —`ENEMY_DIED`,
  `ITEM_COLLECTED`, `FLAG_SET`, `DIALOGUE_FINISHED`, `CHECKPOINT_REACHED`— y
  lleva la cuenta. Los cinco tipos existen porque hay cinco eventos que los
  pueden completar: un tipo que ningún evento cierra sería un objetivo
  imposible, y eso es peor que no tener objetivos.
  Se declara en el TMX con el tipo `Objective`, que es un **punto**: un objetivo
  no ocurre en un sitio, ocurre cuando pasa algo. `stage0` declara dos —uno
  obligatorio y uno opcional— porque un tipo de objeto que sólo existe en la
  documentación no lo usa nadie, y stage0 es el que se copia.
  Compatibilidad: un escenario sin objetivos declarados da `todo_hecho == True`.
  Es lo que mantiene intactos los diecisiete mapas anteriores, y hay una prueba
  sólo de eso.
  Consumidores, para que no sea un sistema que nadie llama: `StageScene` lo
  construye y le da de alta los del mapa; `complete_objective:` desde un árbol
  de diálogo lo cierra por id vía `OBJECTIVE_REQUESTED` —el enganche que el
  propio hueco daba por existente—; y la consola de F11 enseña el estado, porque
  un objetivo que el jugador no puede ver no sirve de nada.
  Lo que enseñó el bus, y que casi cuesta una prueba falsa: `EventBus.emit`
  **encola**, reparte `dispatch()`, y hay guardia de reentrada —lo que un
  suscriptor emite mientras se le atiende se encola para la vuelta siguiente—.
  Las primeras diez pruebas fallaron por emitir sin despachar, que es el
  contrato real y no un detalle.
  Cable trampa: `tests/test_objetivos.py` (25 pruebas), tres de ellas cargando
  `stage0` de verdad para comprobar que lo declarado en el TMX llega al sistema.
  Fuera de alcance, y dicho: **el HUD no los pinta**. Se ven en la consola de
  depuración, no en pantalla durante la partida. Es trabajo de interfaz y va
  aparte.

## ~~[GAP-048] Sin streaming de niveles ni versionado de mapas~~ *(Resuelto — el versionado hecho, el streaming descartado por medición)*

- **File:** `src/framework/stage/stage_loader.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** El TMX se carga entero y de una vez. No molesta —los mapas
  actuales caben— pero no hay corte por salas ni carga por proximidad, y el
  encuadre por sala de la cámara (`Camera._encuadrar_sala`) es visual, no de
  carga. Aparte: ningún mapa declara versión de esquema, así que un TMX viejo
  con una propiedad renombrada falla como dato malo en vez de como versión
  antigua.
- **Resolution plan:** El versionado sí conviene y es barato: una propiedad de
  mapa `schema_version` validada por `scripts/validate_tmx.py`, que ya corre en
  CI. El streaming no, hasta que un mapa no quepa.

- **Avance (2026-08-11, AUD-393): el versionado está hecho.** La entrada queda
  abierta por el *streaming*, que sigue sin hacer falta: ningún mapa se acerca
  a no caber. Lo que hay ahora:
  `StageLoader.SCHEMA_VERSION` es el contrato, los 17 mapas del motor y la
  plantilla de estudiantes declaran `schema_version=1`, y las reglas son
  asimétricas a propósito (decisión del dueño, 2026-08-11): **falta** → aviso
  del validador con el texto que hay que escribir, nunca error, porque ninguna
  entrega anterior a este lote la lleva y suspenderlas a todas por una
  propiedad inventada después sería AUD-106 otra vez; **versión mayor que la
  del motor** → error en el validador y `FrameworkUsageError` al cargar, porque
  abrir a medias un mapa que usa lo que este código no entiende da
  comportamiento incorrecto en silencio; **valor no numérico** → error en el
  validador (hay alguien delante que puede arreglarlo) y sólo aviso en el
  cargador (a mitad de partida no interesa negarse a abrir un nivel por un dato
  mal escrito). La comprobación de versión corre **antes** que la de capas:
  si el mapa es de otra época, «falta la capa Collision» es un diagnóstico
  engañoso.
  Se destaparon dos defectos por el camino, los dos en el validador que iba a
  hacer cumplir esto: `AUD-391` —`--ci` leía una lista que se vaciaba por
  fichero, así que imprimía «FAILED» y devolvía 0— y `AUD-392` —la lista de
  propiedades conocidas estaba escrita, sin usar, y desincronizada 6×, de modo
  que `gravty_multiplier` pasaba en verde—. Ese segundo era, literalmente, el
  fallo que esta entrada quería detectar con el versionado.
  Cable trampa: `tests/test_version_de_esquema_del_mapa.py`, verificado por
  mutación —desconectar la llamada en `load()` pone dos pruebas en rojo—.

- **Resolution (2026-08-11, AUD-423): la otra mitad se cierra sin construirla,
  y con la medición delante.** El propio plan de arriba ya lo decía —«el
  streaming no, hasta que un mapa no quepa»—; lo que faltaba era comprobar que
  ninguno se acerca. Medido sobre los diecisiete:

  | | |
  |---|---|
  | Mapa mayor (`stage4_1`) | **191 KiB**, 60×240 tiles |
  | Segundo (`stage1_1`) | 146 KiB |
  | Los diecisiete juntos | **1.183 KiB** |

  Todos los mapas del juego caben a la vez en poco más de un megabyte, así que
  cortar por salas y cargar por proximidad no ahorraría memoria que a nadie le
  falte y a cambio metería un sistema de carga asíncrona en el camino que hoy
  es un `load()` y ya está. Es optimización sin medición que la respalde, que
  es justo lo que este repositorio no hace (AUD-329, AUD-330).

  **Cuándo reabrirlo:** el día que un mapa no quepa o que cargar uno se note al
  entrar. Hoy entrar en un escenario cuesta 41–134 ms medidos (AUD-288), que es
  por debajo de lo que una pantalla de carga tarda en dejar de parpadear.

- **El streaming sigue sin hacerse, y ahora con la medición delante
  (2026-08-11).** El plan decía «hasta que un mapa no quepa». Medido: el mapa
  más grande es `stage4_1` con 60×240 y 6 capas —86.400 tiles, 191 KiB— y los
  diecisiete TMX juntos ocupan **1,2 MiB** en disco. No hay ninguno que no
  quepa, ni de lejos.
  Construirlo hoy sería exactamente lo que esta fase entera ha estado
  desmontando: un sistema correcto que nadie necesita, con su coste de
  mantenimiento y sin un caso que lo pida. Esta entrada se queda abierta **sólo
  por eso**, y el día que se abra por necesidad la medición de arriba es contra
  lo que hay que comparar.

## ~~[GAP-049] No se cuentan los recursos: llamadas de dibujo, memoria de textura, fugas~~ *(Resuelto)*

- **File:** `src/engine/render/gl_pipeline.py`
- **Phase:** auditoría 2026-08-10, lista del dueño (AUD-376)
- **Reason:** Hay medición de **tiempo** por todas partes —`DeltaClock.historial_ms`,
  `Planificador.tiempos()` por sistema, `test_frame_budget`,
  `bench_sprite_batch.py`, `bench_gpu_postproc.py`— y ninguna de **recursos**:
  nadie cuenta llamadas de dibujo por fotograma, ni cuánta memoria de textura
  hay viva, ni detecta que una superficie no se libera. La caché del
  `AssetLoader` tiene desalojo acotado, así que la fuga clásica está tapada,
  pero nadie lo comprueba.
- **Resolution plan:** Las llamadas de dibujo son fáciles —un contador en
  `GLRenderer` y una línea en `DebugOverlay`— y son la cifra que la lista pide
  con 🔴. Memoria de textura y detección de fugas exigen instrumentar la subida
  de texturas; sin fecha.

- **Avance (2026-08-10, AUD-377):** las llamadas de dibujo ya se cuentan y se
  ven. `GLRenderer.llamadas_de_dibujo` suma **después** de las tres salidas
  tempranas de `_run_shader_pass` —sumar al entrar mentiría justo cuando se
  diagnostica «esto no se dibuja»— y `anotar_volcado` cuenta el lote de sprites
  como **una** llamada instanciada, no como N sprites, que es lo que enseña en
  la consola lo que compró AUD-340. `App` lo reinicia por fotograma junto al
  resto de lo que caduca y publica la fila; la pone `App` y no la escena porque
  una escena no sabe cuántas pasadas de post-procesado hay encendidas, que es
  justo lo que hace subir el número.

  Sigue abierto lo demás del hueco: memoria de textura, VRAM/RAM y detección de
  fugas, que exigen instrumentar la subida de texturas. Y el reparto CPU/GPU
  del tiempo, que la lista del dueño pide aparte.

- **Resolution (2026-08-11, AUD-397): memoria de textura y fugas, hechas.**
  `src/engine/render/memoria_de_textura.py`. Vive **fuera** de `gl_pipeline.py`
  por un motivo que es la mitad del valor del lote: `gl_pipeline` necesita un
  contexto ModernGL para casi todo y en CI no hay ninguno, así que una medición
  escrita dentro de esa clase sería código que no se ejecuta hasta que alguien
  abra el juego en una máquina con tarjeta. Instrumentación que sólo corre
  donde nadie mira es exactamente lo que este hueco existía para evitar. El
  registro no toca OpenGL: pesa objetos que declaran `size` y `components`, y
  eso lo cumple `moderngl.Texture` igual que un doble de tres líneas.
  Se instrumentan los dos sitios donde nacen texturas: `_subir` —la baja va
  pegada al `release()`, porque separarlos es como se desincroniza un contador
  de recursos— y `_create_fbos`, que son los cinco adjuntos de color y con
  diferencia la mayor parte de la memoria del juego. `App` publica la fila
  junto a la de llamadas de dibujo, por lo mismo que aquélla.
  La detección de fugas **no tiene umbral de bytes**, a propósito: cuánta
  memoria es «mucha» depende del nivel y de la resolución, y cualquier número
  ahí sería inventado. Lo que delata la fuga es la forma de la serie —sube y no
  baja ni una vez en diez segundos— y los primeros 120 fotogramas no cuentan,
  porque cargar un nivel siempre sube y llamar fuga a eso sería un aviso que se
  aprende a ignorar.
  Defecto propio, cazado por la prueba en su primera ejecución: el registro
  indexaba por `id()`, y CPython **reutiliza** los identificadores de los
  objetos que recolecta, así que cinco texturas creadas y soltadas en un bucle
  se contaban como tres. En producción habría dado un contador que subestima
  justo cuando más rotación hay, que es cuando se mira.
  Cable trampa: `tests/test_memoria_de_textura.py` (15 pruebas), incluida una
  que comprueba que el historial del propio detector está acotado — un detector
  de fugas que se fuga sería un buen chiste y un mal detector.
  Sigue abierto y no se toca aquí: el **reparto CPU/GPU** del tiempo, que la
  lista del dueño pide aparte y que no es una cifra de recurso sino de tiempo.

## ~~[GAP-050] El clima tiene dos autoridades: la simulación lo calcula y el VFX lo ignora~~ *(Resuelto)*

- **File:** `src/framework/scenes/stage_parts/ambiente.py`
- **Phase:** auditoría 2026-08-10, segunda pasada sobre la lista del dueño
  (AUD-371)
- **Reason:** AUD-362 hizo que la escena **consumiera** `EnvironmentState` en
  vez de componer el ambiente por su cuenta, y lo hizo para la luz: en
  `_aplicar_hora` salen `ambient_brightness` (con el suelo que sube por
  `luz_lunar`), `ambient_color`, el bloom y el agarre del suelo. **El clima se
  quedó fuera de esa mudanza.** `WorldSimulation` calcula `clima`,
  `precipitacion`, `viento`, `visibilidad` y `cobertura_nubes`, y el sistema
  que de verdad dibuja la lluvia, la nieve y la niebla —`WeatherSystem`— no
  lee ninguno: se alimenta de `_clima_efectivo()` (`ambiente.py:175`), que
  devuelve la cadena `climate` del TMX o, si falta, el clima por defecto de la
  estación, y llega por `set_climate(str)`.

  Son dos autoridades sobre el mismo hecho, que es exactamente el defecto que
  `WorldSimulation` vino a cerrar y que §1 de `docs/92` enuncia como la regla
  que lo sostiene («un fenómeno **lee** el estado y nunca lo escribe»). Hoy no
  se nota porque los dieciséis mapas declaran su `climate` y la simulación
  arranca del mismo dato, así que las dos autoridades coinciden por
  construcción; se notará el día que el clima cambie durante la partida —que
  es justamente lo que la simulación sabe hacer y el TMX no—. `stage4_1` ya
  llama a `set_climate` por acto (`stage4_1.py:241`) sin pasar por el estado.

  Alcance de lo que sí está garantizado, para no re-medirlo: `test_el_ambiente
  _llega_al_juego.py` cubre hora, estación, visibilidad y agarre. Ninguna
  prueba ata el VFX de clima al estado, y por eso la divergencia no la ve
  nadie.
- **Resolution plan:** Barato y sin riesgo de calibración: que
  `_clima_efectivo()` lea `self.ambiente.clima` y que el TMX pase a ser el
  **valor inicial** de la simulación en vez de la fuente permanente —que es la
  separación de responsabilidades que la propia lista del dueño pide en sus
  filas de TMX («TMX como configuración del mundo, no simulador»)—. La prueba
  que falta es de una línea: mover la simulación a `storm` y comprobar que el
  `WeatherSystem` lo sigue. Reservado **AUD-374**.


- **Resolution (2026-08-10, AUD-374):** el mundo manda y el VFX consume.

  * **Una puerta.** `SimulacionDeEscenario._cambiar_clima(nombre)` se lo pide a
    `WorldSimulation` y recompone el ambiente. Es la única forma de cambiar el
    clima en marcha; `stage0.py:173` (el clímax) y `stage4_1.py:241` (por acto)
    están migrados.
  * **Un consumidor.** `_aplicar_clima(estado)` pasa `estado.clima` y
    `estado.viento` al `WeatherSystem` desde el mismo sitio donde `_aplicar_hora`
    reparte luz, bloom, tinte y agarre. `set_climate` ya se ignoraba a sí misma
    cuando el clima no cambia, así que llamarla por fotograma no vacía el
    emisor. El TMX queda como **valor inicial** de la simulación, que es la
    separación que pedía el plan.
  * **Un viento.** Era el caso extremo de las dos autoridades:
    `EnvironmentState.viento` se calculaba cada fotograma y **nadie lo leía**,
    mientras `WeatherSystem._set_climate_params` sorteaba el suyo con
    `random.uniform` y una segunda tabla. Que los números coincidieran —75
    frente al centro del `uniform(50, 100)`, 15 frente a `uniform(-15, 15)`, 12
    frente a `uniform(-12, 12)`— delataba que era una decisión copiada. Ahora
    `viento_de(clima, rng)` en `world/simulation.py` es la única tabla, y el
    sistema de clima la consume o cae a ella; `aplicar_viento` es la entrada que
    no existía.

  **Lo que la medición añadió al diagnóstico de este GAP.** Decía «hoy no se
  nota porque los dieciséis mapas declaran su `climate`». Sí se notaba, y en
  jugabilidad: con la secuencia real de `stage4_1` —mapa `fog`, acto `storm`—
  la humedad se quedaba en 0,50 y `suelo_mojado` en falso. **Los actos de
  tormenta de ese escenario nunca resbalaron**, con AUD-362 entero construido y
  la escena consumiéndolo. El dato no faltaba: llegaba caducado, que es más
  difícil de ver.

  Y un segundo defecto que el primero tapaba: el campo declara signo
  («negativo = hacia la izquierda») y `CLIMAS` sólo tenía magnitudes positivas,
  así que el viento del ambiente **nunca soplaba hacia la izquierda**.
  `test_declarar_tormenta_produce_un_mundo_de_tormenta_entero` pasó a comprobar
  la magnitud (`abs(e.viento) > 50`), porque su `> 50` fijaba justo el defecto.

  **La dirección se probó al revés primero, y la suite la rechazó.** El primer
  intento reconciliaba al contrario —la simulación siguiendo al `WeatherSystem`,
  para no tocar ningún escenario— y dejó seis pruebas en rojo: las cinco de
  `TestElClimaCambiaLasReglas` y una de `TestElMapaConfiguraYLaSimulacionCalcula`
  hacen `_simulacion.set_clima(...)` y luego `_aplicar_hora()`, o sea que el
  contrato «la simulación es la autoridad» ya estaba escrito en las pruebas
  desde AUD-362. Queda anotado porque el atajo era tentador y costaba cero
  cambios en escenarios.

  13 pruebas nuevas en `tests/test_el_viento_es_uno_solo.py`, las 13 rojas
  antes.

## ~~[GAP-051] El estado ambiental llega a la luz y se para ahí: sombras, audio y color grading tienen sus propias fuentes~~ *(Resuelto — los tres consumidores cableados)*

- **File:** `src/framework/world/environment.py`
- **Phase:** auditoría 2026-08-10, segunda pasada sobre la lista del dueño
  (AUD-371)
- **Reason:** Es el hermano mayor de GAP-050 y conviene separarlo, porque
  aquél es un **defecto** (dos autoridades sobre un dato) y éste es
  **integración que no se ha escrito**. Fuera de `world/`, el único fichero de
  producción que importa `EnvironmentState` es
  `scenes/stage_parts/simulacion.py`. Tres consumidores que la lista del dueño
  marca 🔴 siguen sin enterarse:

  * **Sombras proyectadas.** `vfx/sombras_proyectadas.py` proyecta desde un
    `foco` de luz, no desde el sol. Y no puede: `EnvironmentState` publica
    `altura_solar` pero **no azimut**, así que el dato para orientar la sombra
    no existe todavía. Es el único de los tres que necesita un campo nuevo.
  * **Audio ambiental.** `stage_parts/sonido.py` es despacho de SFX por
    eventos; nada lee `viento`, `precipitacion` ni `fase_del_dia`. El
    mezclador y el audio espacial ya existen (AUD-144, `play_sfx_at`), o sea
    que lo que falta es quién los llama, no con qué.
  * **Color grading.** La pasada existe en `gl_pipeline.py` y se controla por
    `gpu_effects`; el estado no la alimenta.

  No es un descuido: AUD-357/358 entregaron el productor y AUD-362 cableó el
  primer consumidor a propósito, para que el cableado se hiciera de uno en uno
  y con pruebas. Se registra para que no se lea el módulo como «hecho» cuando
  lo hecho es la mitad productora.
- **Resolution plan:** Un consumidor por commit, en el orden de §4 de
  `docs/92`, que ya los tiene priorizados por efecto visible: azimut solar
  (campo nuevo, 🟢) → sombras dirigidas por el sol (🟡, «alto valor visual por
  poco coste») → audio → color grading. **No se abre una fila por fenómeno
  aquí**: el catálogo de arcoíris, halos, meteoros y demás vive en `docs/92`
  §3 con su coste medido, y duplicarlo en este fichero produciría dos listas
  que se desincronizan. Este GAP cubre la *tubería*; `docs/92` cubre la cola
  larga que la recorre.

- **Avance (2026-08-11, AUD-399): el campo que faltaba, hecho. 1 de 4.**
  `EnvironmentState.azimut_solar` existe y la simulación lo publica, así que el
  dato para orientar una sombra ya está — era el bloqueo que el propio hueco
  señalaba («es el único de los tres que necesita un campo nuevo»).
  Sale del **mismo ángulo** que `altura_solar`: uno es el seno y el otro el
  coseno de `2π(hora−6)/24`. Con su propia fórmula habría dos modelos del sol
  capaces de desincronizarse, que es exactamente el defecto que GAP-050
  documentó, y hay una prueba de `sen² + cos² = 1` para impedirlo.
  Se publica normalizado (−1 este, 1 oeste) y no en grados porque el juego es
  2D de perfil: lo único pintable de la posición del sol es hacia qué lado se
  alarga la sombra y cuánto. `EnvironmentState.direccion_de_sombra` es el
  derivado que lo hace usable —y vive ahí, como `luz_lunar`, para que las
  sombras de las paredes y las de los personajes no acaben apuntando a sitios
  distintos—; de noche devuelve largo 0, que es el error clásico de este
  cálculo, y el largo está acotado a 4× porque va como 1/altura y al amanecer
  tiende a infinito.
  **El hueco sigue abierto**, y esto no es un cierre disfrazado: faltan los tres
  consumidores que la lista del dueño marca 🔴 —sombras dirigidas por el sol,
  audio ambiental y color grading—, que es donde está el efecto visible. El plan
  pide un consumidor por commit y éste entrega el paso previo que los tres
  necesitaban.
  Cable trampa: `tests/test_azimut_solar.py` (11 pruebas), incluida una que
  comprueba que el campo llega al estado que leen los consumidores — sin ella
  `_azimut_solar` sería una función correcta que nadie llama, que es
  precisamente lo que este GAP registra que pasó con la mitad productora.

- **Resolution (2026-08-11, AUD-401/402/403): los tres consumidores, cableados.**
  El plan pedía uno por commit y así se hizo, en el orden que marcaba.

  * **Color grading (AUD-401).** Era el más barato porque no necesitaba dato
    nuevo. La pasada llevaba compilada desde hace tiempo con
    `color_matrix = (1,0,0, 0,1,0, 0,0,1)` **fija en el config**: un efecto
    construido, ejecutándose y multiplicando por la identidad.
    `EnvironmentState.matriz_de_color` sale de `color_ambiente` —el tinte que
    la hora y la estación ya calculaban— y de `visibilidad`. Se normaliza al
    canal más alto porque el brillo ya lo lleva `factor_ambiente` y aplicarlo
    dos veces oscurecería el doble al atardecer; y desatura con niebla usando
    pesos de luminancia Rec. 601, tope 0,6, porque en blanco y negro no se
    distingue un enemigo venenoso de uno normal.
  * **Audio ambiental (AUD-402).** `EnvironmentState.intensidad_sonora`, con la
    lluvia pesando más que el viento —una tormenta sin lluvia suena a poco— y
    el viento en valor absoluto. Se **modula** el volumen del bus, no se fija:
    fijarlo pisaría la preferencia del jugador, que es lo que ese bus existe
    para respetar (AUD-149). Suelo de 0,35, porque un silencio absoluto se oye
    como un fallo de audio y no como calma.
  * **Sombras dirigidas por el sol (AUD-403).** `sombra_direccional()`, que es
    proyección **paralela** y no radial. Ésa era la razón de fondo de que el
    módulo proyectara desde un foco: una sombra radial con el foco muy lejos no
    es una paralela, es una paralela *en el límite*, y para acercarse habría que
    poner el foco a millones de píxeles con lo que la coma flotante se rompe
    mucho antes. `LightSystem.set_sombra_solar` la recibe ya derivada, por lo
    mismo que `set_obstaculos` recibe la lista hecha.

  Un intento fallido que merece constar: la primera versión del grading buscaba
  el renderer con `getattr(self.context, "gl_renderer", None)`. Ese atributo
  **no existe**, y por diseño — el comentario de `GameContext` lo dice: «una
  escena con la ruta de GPU no se pregunta "¿hay renderer?" (no puede importarlo
  sin arrastrar ModernGL)». Habría sido una función que no hace nada nunca. El
  canal correcto es `gpu_effects.publish_*`, el mismo del bloom.
  Y una decisión de prueba: cuando `_LuzFalsa` de `test_el_viento_es_uno_solo.py`
  se quedó sin el método nuevo, se le **enseñó al doble** en vez de poner un
  `hasattr` en `simulacion.py`. Un `hasattr` ahí dejaría que el cableado se
  rompiera sin que nada se entere, que es el patrón que AUD-039 anotó:
  «`getattr` contra un campo que no existe no falla, calla».
  Cables trampa: `tests/test_grading_desde_el_ambiente.py` (10) y
  `tests/test_ambiente_llega_a_todo.py` (16), incluidas tres que comprueban por
  AST que `_aplicar_hora` llama de verdad a los tres consumidores.
  Lo que queda fuera y no es de este hueco: el catálogo de fenómenos —arcoíris,
  halos, meteoros— sigue en `docs/92` §3 con su coste medido. Este GAP cubría la
  tubería, y la tubería está entera.

## ~~[GAP-052] Diecisiete características del TMX que no ejercita ningún mapa~~ *(Resuelto)*

- **File:** `assets/maps/`
- **Phase:** AUD-378 (2026-08-10)
- **Reason:** Con el punto ciego del guardián cerrado, `check_tmx_coverage.py`
  puede por fin responder la pregunta para la que se escribió. La respuesta:
  de las 38 propiedades de mapa que lee el motor, **17 no las declara ningún
  mapa del repositorio**:

      camara / vista            (modo de cámara y proyección)
      fog_of_war  god_rays      sombras_proyectadas
      water_effect  water_tint  water_alpha
      water_amplitude  water_frequency  water_speed
      tiempo_bala  estamina  habilidades_libres
      desfase_audio
      profundidad_min  profundidad_max

  Verificadas una a una contra los `.tmx` — cero falsos positivos, después de
  que el primer barrido diera dos (`bpm` y `owner_id`).

  No es un defecto del motor: las diecisiete están implementadas, probadas y
  documentadas. Es que **el contenido no las usa**, y el propio guion enuncia
  por qué eso importa: «una característica que el motor lee del TMX pero que
  ningún mapa declara es, en la práctica, una característica que no existe» —
  el estudiante no la ve al jugar, no la encuentra abriendo un mapa en Tiled, y
  sólo puede enterarse leyendo la documentación, que es justo lo que no se
  hace. `sombras_proyectadas` es el caso que destapó todo esto: construida y
  medida en AUD-278, encendida por nadie desde entonces.

  Conviene no leerlo como una lista de tareas. Varias son deliberadamente
  opcionales (`sombras_proyectadas` está apagada por defecto porque cuesta, y
  su módulo lo mide), y `camara`/`vista` tienen valor por defecto sensato, así
  que no declararlas no es lo mismo que no usarlas. Lo que sí es cierto de las
  diecisiete es que **ningún mapa las demuestra**, y ésa es una decisión de
  contenido que ahora está a la vista en vez de escondida.
- **Decisión del dueño (2026-08-10):** *«la idea es que todo este cableado
  [sea] para que los estudiantes lo usen»*. Eso resuelve la ambigüedad con la
  que se redactó este hueco: **no son opcionales aceptables**. Una
  característica que ningún mapa demuestra no la descubre el estudiante —no la
  ve al jugar y no la encuentra abriendo un mapa en Tiled—, así que el estado
  de las diecisiete es un hueco de contenido de verdad, no un límite de la
  métrica. La frase de arriba sobre «no leerlo como una lista de tareas» queda
  matizada por esto: sigue siendo cierto que `sombras_proyectadas` está apagada
  por defecto **por coste**, pero apagada por coste y no demostrada en ningún
  sitio son cosas distintas, y lo segundo hay que arreglarlo.

- **Avance (2026-08-10, AUD-380):** siete demostradas, de 17 a 10. El bloque
  sin riesgo, y sin tocar `stage0` —el mapa que copian los estudiantes, cuya
  lección es el prólogo y no ser un muestrario—:

  * **Las seis del agua** en `stage_mecanicas`, que es el **único** mapa del
    repositorio con `WaterZone`, o sea el único sitio donde se pueden
    demostrar. Los valores son los del motor salvo dos subidos para que la
    diferencia se vea al abrir el mapa (amplitud 4→6 px, alfa 100→120); el
    tinte es el azul por defecto escrito explícito, para que se lea el formato.
  * **`desfase_audio`** en el mismo mapa, que ya declaraba `bpm` y `compas` y
    era la única de las tres sin declarar en ningún sitio.

  Se editó `tools/generate_stage_mecanicas.py`, no el `.tmx`: el mapa es
  generado y tocar la salida se pierde en la siguiente regeneración.

  **Las diez que quedan, por qué no se cierran igual:** `camara` y `vista` son
  modos de juego enteros —`vista=cenital` no es una propiedad que se añada,
  es un mapa que se diseña— y son el hueco más grande que queda desde el
  criterio del dueño, porque el motor sabe hacer cenital y ningún mapa lo
  muestra. `sombras_proyectadas` y `god_rays` cuestan, y la primera tiene
  medición detrás (≤4-5 focos): encenderlas exige elegir el mapa mirando sus
  focos. `estamina`, `tiempo_bala` y `habilidades_libres` cambian cómo se juega
  y son decisión de diseño. `fog_of_war`, `profundidad_min` y
  `profundidad_max` esperan a un mapa que las pida.

- **Avance (2026-08-10, AUD-383):** cuatro más, de 10 a 6. `stage_cenital` —el
  laboratorio de la vista de arriba— declara `vista`, `camara`,
  `profundidad_min` y `profundidad_max`, que no declaraba ningún mapa.

  Era el hueco más grande de los diecisiete: un **modo de juego entero** que el
  motor sabía hacer desde AUD-129 —sin gravedad, dos ejes, tres modos de
  cámara, con su preset de física y sus pruebas— y que ningún estudiante podía
  descubrir. Tres salas, una por modo de cámara, sin enemigos y sin lógica en
  la clase: todo vive en el TMX, así que se copia sin escribir Python. Lo
  genera `tools/generate_stage_cenital.py`.

  Quedan **seis**, y las seis son decisión de diseño o de coste, no de
  cableado: `estamina`, `tiempo_bala` y `habilidades_libres` cambian cómo se
  juega el mapa donde se pongan; `sombras_proyectadas` y `god_rays` cuestan, y
  la primera tiene medición detrás (≤4-5 focos), así que encenderlas exige
  elegir el mapa mirando sus focos; `fog_of_war` espera a un mapa que la pida.

- **Resolution (2026-08-10, AUD-384): cero.** El informe cierra con «todas las
  propiedades de mapa están demostradas en algún mapa», y lo vigila
  `test_todas_las_propiedades_las_demuestra_algun_mapa`, que es estricto y no
  un porcentaje: con el criterio del dueño —el cableado existe *para que los
  estudiantes lo usen*— «casi todas» no significa nada. Añadir una propiedad al
  motor obliga desde ahora a decidir, en el mismo lote, en qué mapa se enseña.

  Las seis últimas, y dónde:

  * **`estamina`, `tiempo_bala`, `habilidades_libres`** → `stage_mecanicas`.
    Están apagadas en los dieciséis escenarios entregados a propósito —sus
    docstrings lo dicen: encenderlas allí cambiaría el juego que sus autores
    diseñaron, y están calificados—, y el laboratorio es justo donde cambiar la
    jugabilidad **es su función**.
  * **`sombras_proyectadas` y `god_rays`** → `stage_mecanicas`, con **dos**
    focos nuevos y no más: el módulo mide que el envolvente utilizable son
    cuatro o cinco. Medido antes de encenderlo: **+0,158 ms sobre 0,499, un
    1,0% del presupuesto de fotograma**. Los focos van en la sala del viento,
    que tiene techo, porque una sombra proyectada se lee cuando hay una pared
    donde caer; en campo abierto el efecto existe y no se ve.
  * **`fog_of_war`** → `stage_cenital`, y no al laboratorio lateral. Una vista
    en planta con niebla es la mazmorra clásica y se entiende sola; oscurecer
    el laboratorio de mecánicas taparía las once mecánicas que ese mapa existe
    para enseñar. 220 px deja ver la sala en la que estás y esconde las otras
    dos.

  Los tres lotes: AUD-380 (siete), AUD-383 (cuatro, con el mapa cenital nuevo)
  y AUD-384 (seis).

- **Resolution plan:** Es del dueño, no de ingeniería: decidir cuáles merecen
  aparecer en un mapa —empezando por el de referencia, que es el que los
  estudiantes copian— y cuáles se quedan como opcionales documentadas. Cuando
  esa decisión exista, el paso siguiente para el guion es la triaje al estilo
  de `check_orphan_systems.py` (listas `VERIFICADOS`/`PENDIENTES` y `--ci` que
  falla por lo que **aparece nuevo**), que es lo que convierte el informe en
  guardián. Hoy no se hace porque fallaría de entrada por las diecisiete, y un
  gate que nace en rojo se desactiva.

## ~~[GAP-053] Cuatro módulos de `src/engine/ui/` sin ninguna entrada en `22_API_CONTRACTS.md`~~ *(Resuelto)*

- **File:** `src/engine/ui/minimap.py`, `subtitle_overlay.py`, `theme.py`, `widgets.py`
- **Phase:** AUD-455 (2026-08-13), revisión manual de código línea a línea
- **Reason:** `22_API_CONTRACTS.md` §7 documenta `HUD`, `MessageBox` y
  `ScreenBanner`, pero los otros cuatro módulos de `src/engine/ui/` —el
  minimapa, los subtítulos, el sistema de tema (`Theme`/`escalar`/`font`, del
  que dependen `MessageBox` y `ScreenBanner` para la escala de accesibilidad
  de AUD-451) y los widgets compartidos— no tienen ninguna sección. Se citan
  por nombre en `03_ARCHITECTURE.md`, `52_EVENT_MAP.md` y otros documentos,
  pero nunca se documenta su API pública.
- **Resolution:** Añadidas `### 7.4`–`7.7` a `22_API_CONTRACTS.md` con la API
  pública real de las cuatro clases (`Theme`, `MenuItem`/`MenuList` y el
  mobiliario de pantalla de `widgets.py`, `Minimap`, `SubtitleOverlay`),
  verificada contra los cuatro ficheros fuente.

## ~~[GAP-054] `src/framework/ecs/components.py` — 20 componentes sin documentar en `23_DATA_SCHEMAS.md`~~ *(Resuelto)*

- **File:** `src/framework/ecs/components.py`, `docs/23_DATA_SCHEMAS.md`
- **Phase:** AUD-455 (2026-08-13), revisión manual de código línea a línea
- **Reason:** El módulo define 20 clases de componente (confirmado por
  `grep -n "^class "`); `23_DATA_SCHEMAS.md` no menciona ninguna por nombre.
  Es el mismo patrón de deuda que motivó el resto de las correcciones AUD-455
  en `22_API_CONTRACTS.md` (código que evolucionó sin que el contrato lo
  siguiera).
- **Resolution:** Añadida la sección §11 a `23_DATA_SCHEMAS.md` con los 20
  componentes, sus campos y para qué sirve cada uno (incluidos los 3
  retirados por AUD-123: `Gravedad`, `Renderizable`, `Etiqueta`, marcados como
  inexistentes en vez de omitidos en silencio). De paso se corrigió la tabla
  de espacios de coordenadas de la misma §10, que documentaba «espacio de
  pantalla» como 320×224 cuando la resolución interna real es 800×600.

## ~~[GAP-055] 28 escenas de `src/engine/scenes/` sin ninguna entrada en `22_API_CONTRACTS.md`~~ *(Resuelto)*

- **File:** `src/engine/scenes/` — `achievement_scene.py`, `bestiary_scene.py`,
  `boss_rush_entry.py`, `code_panel.py`, `combo_demo_scene.py`,
  `end_credits_scene.py`, `game_over_scene.py`, `inventory_scene.py`,
  `keybinding_scene.py`, `leaderboard_scene.py`, `load_game_scene.py`,
  `loading_scene.py`, `pipeline_builder_scene.py`, `progress_scene.py`,
  `quiz_system.py`, `sandbox_scene.py`, `shop_scene.py`, `skill_tree_scene.py`,
  `splash_scene.py`, `stage_error_scene.py`, `stage_wizard_scene.py`,
  `story_scene.py`, `student_login_scene.py`, `title_scene.py`,
  `transition_manager.py` (parcialmente documentada en §6.3/6.4),
  `tutorial_overlay.py`, `tutorial_scene.py`, `unit_theory_scene.py`,
  `world_map_scene.py`
- **Phase:** AUD-455 (2026-08-13), revisión manual de código línea a línea
- **Reason:** De las 48 escenas de `src/engine/scenes/`, `22_API_CONTRACTS.md`
  §16-17 sólo documenta las 4 demo/laboratorio con API pública propia
  (`DemoMenuScene`, `FilterDemoScene`, `VisionDemoScene`, `PatternDemoScene`),
  las 7 escenas de laboratorio teórico (§16.5, verificadas en esta misma
  pasada — sus listas de modos coinciden con el código real) y la
  infraestructura compartida (`scene_registry`, `debug_overlay`,
  `param_panel`, `demo_layout`, `demo_utils`, `options_scene`,
  `demo_common`). Las 28 escenas de contenido/menú listadas arriba —
  inventario, tienda, bestiario, créditos, game over, mapa del mundo, login
  de estudiante, etc.— no aparecen en el documento ni una sola vez (grep de
  sus 15 nombres de clase principales: **un** acierto, y era una mención de
  paso en la sección de `SceneManager`). No se abrieron los 28 ficheros en
  esta pasada por volumen: se deja como hueco explícito en vez de una
  cobertura desigual.
- **Resolution:** Añadida `### 17.8` a `22_API_CONTRACTS.md`. De los 28
  ficheros: 16 escenas sólo implementan los 4 métodos abstractos de
  `BaseScene` sin API propia —se dice explícitamente en vez de dejarlo en
  silencio—; 7 escenas tienen `__init__` u otros métodos propios
  (`GameOverScene`, `UnitTheoryScene`, `StageErrorScene`, `LoadGameScene`,
  `StudentLoginScene`, `TitleScene`, `SplashScene`); 4 ficheros no son
  `BaseScene` en absoluto y documentan sus propias clases auxiliares
  (`code_panel.py`, `loading_scene.py` con `LoadTask`+`LoadingScene`,
  `quiz_system.py`, `tutorial_overlay.py`); y `boss_rush_entry.py` resultó no
  ser una escena en absoluto sino un módulo de funciones (AUD-191) — también
  documentado. 16+7+4+1 = 28. Verificado contra los 28 ficheros fuente.

## ~~[GAP-056] `StageScene`, física, mundo, combate, IA y academic sin API en `22_API_CONTRACTS.md`~~ *(Resuelto)*

- **File:** `src/framework/scenes/stage_scene.py`, `src/framework/physics/`,
  `src/framework/world/`, `src/framework/combate/`, `src/framework/ai/`,
  `src/framework/academic/`
- **Phase:** AUD-455 (2026-08-13), revisión manual de código línea a línea
- **Reason:** `StageScene` es la clase que orquesta cada nivel jugable y se
  citaba narrativamente en 8 documentos sin tener nunca una sección de API en
  `22_API_CONTRACTS.md`. Los directorios de física, combate, IA, mundo y
  material académico estaban en la misma situación.
- **Resolution:** Añadida `### 11.8` con la API pública real de `StageScene`
  (ganchos sobreescribibles, `stage_key`, métodos heredados de los mixins de
  `stage_parts/`) y `## 20` completa (12 subsecciones, `20.1`–`20.12`) con
  `physics/` (capas de colisión, perfiles de física, el resolutor de
  movimiento), `combate/` (canales de daño, efectos temporales), `ai/`
  (A* de navegación, y el script Lua marcado explícitamente como no
  conectado — AUD-022/R-11) y `academic/` (el temario de 10 unidades, el
  progreso del estudiante, la sesión): 12 ficheros con API pública
  documentada (`physics/` 3, `combate/` 2, `ai/` 2, `world/` 2, `academic/`
  3), más `stage_scene.py` y los 12 mixins de `stage_parts/` leídos para
  extraer la superficie pública de `StageScene` — 25 ficheros en total
  abiertos en esta pasada. No documentada la API interna de los mixins de
  `stage_parts/` (casi enteramente privada) — ver [[GAP-057]] para lo que
  queda de `vfx/`.
- **Nota:** al resolverse, este hueco se dividió: lo que quedaba de `vfx/`
  (13 módulos) pasó a [[GAP-057]] por ser una superficie distinta (efectos
  visuales, no lógica de juego) con su propio criterio de prioridad.

## ~~[GAP-057] 13 módulos de `src/framework/vfx/` sin API en `22_API_CONTRACTS.md`~~ *(Resuelto)*

- **File:** `src/framework/vfx/ambient_particles.py`, `cielo.py`, `contorno.py`,
  `damage_numbers.py`, `hit_effects.py`, `lighting.py`, `particle_system.py`,
  `post_processing.py`, `pulso.py`, `sombras.py`, `sombras_proyectadas.py`,
  `trail_system.py`, `weather_system.py`
- **Phase:** AUD-455 (2026-08-13), revisión manual de código línea a línea
- **Reason:** Desprendido de [[GAP-056]] al resolverse: `fog_of_war.py` y
  `water_effect.py` ya tienen descripción de comportamiento (no firmas) en
  `46_FOG_OF_WAR.md`/`47_WATER_EFFECT.md`, pero los otros 13 módulos de
  efectos visuales de `src/framework/vfx/` no tenían ninguna sección de API
  ni documento dedicado.
- **Resolution:** Añadidas `### 20.13`–`20.25` a `22_API_CONTRACTS.md` con
  la API pública real de los 13 módulos — partículas (`ParticleEmitter`/
  `ParticleSystem`, con el kernel numba opcional), iluminación (`LightSource`/
  `LightSystem`), sombras proyectadas por vector (Unidad II), el cielo
  procedural derivado de `EnvironmentState`, el contorno de silueta de
  accesibilidad, la sombra bajo los pies, números de daño, el catálogo de
  `HitEffects`, post-procesado de pantalla completa (bloom, viñeta, filtro de
  daltonismo — con la optimización de AUD-138 documentada), el pulso visual
  al compás, estelas de movimiento, partículas de ambiente y el sistema de
  clima. Verificado contra los 13 ficheros fuente. `src/framework/vfx/`
  queda completo en `22_API_CONTRACTS.md`.
- **Nota:** con esto se cierra la cadena GAP-053→057; `22_API_CONTRACTS.md`
  cubre ahora la totalidad de `src/framework/` y `src/engine/` con secciones
  de API verificadas, salvo los métodos internos (`_`-prefijados, casi
  siempre privados) de los mixins de `src/framework/scenes/stage_parts/`,
  que se dejaron fuera deliberadamente por bajo valor de contrato público.

## [GAP-058] `stage4_1` (El Cementerio Sagrado) — arte final por fase, diálogo de los espíritus y reverberación real

- **File:** `assets/backgrounds/final/`, `assets/tilesets/tileset_cemetery.png`, `src/stages/stage4_1/stage4_1.py`
- **Phase:** AUD-462/463/464 (2026-08-14), rediseño de `stage4_1` a seis fases
- **Reason:** El rediseño (ver `docs/niveles/13_STAGE_4_1.md` §0 y
  `15_DISENO_4_1_EL_CEMENTERIO.md`) se construyó a propósito reusando el
  fondo y el tileset del diseño anterior (`bg_final_*.png`,
  `tileset_cemetery.png`) para probar primero la mecánica —gradación de
  color por fase, clima, la loma, el shake, el ciclo de luna— antes de
  encargar arte nuevo. Eso demuestra la transición de color de verdad, pero
  **no** da a cada fase su identidad de contenido: la Fase 4 («bosque
  cortado y muerto») y la Fase 5 («la Planicie de los Muertos», tumbas de
  conquistadores) siguen mostrando el mismo cementerio de piedra que la Fase
  1, sólo con la matriz de color distinta. Tampoco se escribió el diálogo de
  los tres espíritus (el sistema de `40_DIALOGUE_SYSTEM.md` ya lo soporta,
  el texto no) ni existe reverberación de audio real para el silencio
  súbito de la Fase 4 — el mezclador SDL no tiene DSP por zona
  (`90_INVENTARIO_DE_LEVEL_DESIGN.md` §1.1), así que el silencio se resuelve
  bajando el clima y las partículas a cero, no con una reverberación que se
  apaga.
- **Resolution plan:** Encargar (o generar por código, siguiendo
  `tools/generate_all_assets.py`) un fondo bespoke por fase una vez que el
  playtest del prototipo confirme el ritmo de las seis fases — cambiar el
  arte antes de validar la mecánica sería el orden caro. El diálogo de los
  espíritus y una reverberación real (si el proyecto añade algún día un
  mezclador con DSP) quedan igual de pendientes, sin fecha.
- **Nota (AUD-465, 2026-08-14):** parcialmente resuelto. Se generaron cuatro
  ambientes propios por código (`viento_de_bosque`, `grito_de_gavilan`,
  `canto_ancestral`, `resonancia_solemne` — sin fingir ninguna lengua, el
  mismo principio que ya aplica `venado_fase1`) y se cableó
  `sonido_ambiente` por fase con `crossfade_ambient`, corrigiendo de paso
  que la tormenta de la Fase 3 nunca sonaba (`get_ambient_audio_key()` sólo
  se consultaba una vez, al entrar al escenario). Se añadió decoración de
  fondo propia —árboles cortados (Fase 4) y cruces de conquistador (Fase
  5)— como contornos dibujados por código, igual que las siluetas de los
  espíritus, sin PNG nuevo. **Sigue pendiente:** un fondo TMX bespoke por
  fase con arte final (el tileset y los tres `bg_final_*` siguen siendo los
  del diseño anterior), sombras de ave cruzando el fondo en la Fase 4, el
  diálogo de los tres espíritus, y la reverberación real.
- **Nota (AUD-467…471, 2026-08-14):** el dueño jugó el prototipo del pozo
  (arriba) y lo rechazó — *«no es en nada lo solicitado... el nuevo nivel
  es horizontal completamente»*. Se reconstruyó desde cero como un
  pasillo horizontal de seis secciones, lo que resuelve la mayoría de lo
  que quedaba pendiente aquí: **terreno propio por sección**
  (`tileset_stage4_1.png`, seis familias — ya no es el mismo suelo con la
  matriz de color encima), **el diálogo de los tres espíritus**
  (`data/dialogues/stage4_1.json`), **la cutscene de introducción**, **la
  sombra del Gavilán** y **una serpiente de fondo** en la Fase 3, y el
  easter egg personal de la Fase 1. **Sigue pendiente:** un fondo de
  parallax (`BG_Far`/`BG_Mid`/`BG_Near`) propio por sección — las seis
  siguen compartiendo `bg_final_*.png` — y la reverberación real. De paso
  se encontró que `scripts/grade_stage.py` no modela objetos `Slope` en su
  analizador de rutas (marca la loma como «repecho imposible» y la salida
  como inalcanzable; verificado falso con un recorrido físico real):
  queda como sugerencia aparte, no se arregla en este lote.
- **Nota (AUD-513, 2026-08-16):** el hueco de `BG_Far`/`BG_Mid`/`BG_Near`
  se cierra con **parallax dibujado por código**, no con arte de tileset:
  `assets/maps/stage4_1/stage4_1.tmx` ya tiene `BG_Far`/`BG_Mid` con
  baldosas pintadas a mano (comprobado leyendo el XML — rangos de gid
  contiguos, no ceros) y `tools/generate_stage4_1.py` se niega a
  regenerar el mapa sin `--forzar` en cuanto lo detecta
  (`tiene_arte_pintado()`); forzarlo para añadir una silueta habría
  borrado ese trabajo. `siluetas.dibujar_horizonte` (nueva, procedural,
  un perfil de cresta distinto por fase) se pinta detrás del mapa por el
  mismo gancho `dibujar_fondo` que ya usan los espíritus — una capa más,
  no una sustituta de la que ya existe. Pruebas en
  `tests/test_el_horizonte_y_la_despedida.py`. El diálogo de los tres
  espíritus ya se había cerrado en AUD-467…471 (`data/dialogues/
  stage4_1.json`, ver la nota de esa fecha arriba). **Sigue pendiente:**
  la reverberación real, que sigue sin mezclador DSP.
- **Nota (AUD-515, 2026-08-16):** la reverberación se cierra sin mezclador
  DSP. El mezclador de este motor no tiene DSP en tiempo real, pero
  **todo** el audio del proyecto ya se genera por código
  (`tools/generate_all_assets.py::_gen_sfx`), así que se hornea en el
  propio `.wav`: `_aplicar_reverberacion` suma varias copias retrasadas y
  cada vez más flojas del sonido por encima del original —el mismo
  principio que un comb filter, calculado una vez al generar en vez de en
  tiempo real— y alarga el clip con la cola que hace falta para que el
  último eco no se corte. Se aplica al silencio súbito de la Fase 4
  (`cemetery_silence`, que ya decaía y ahora además resuena) y a un sonido
  nuevo, `despertar_profundo`, que sustituye al `sfx_bosses_phase_change`
  prestado que usaba la secuencia de despertar de la Fase 6 ([[GAP-064]]
  punto 25) — un cue de combate sin relación, cambiado por un retumbar
  propio con la misma reverberación. Pruebas en
  `tests/test_la_reverberacion_esta_horneada.py`.

## [GAP-059] `stage4_1` Fase 1 — sin anomalía ambigua de fondo, sin memoria espacial, sin capas de sonido natural

- **File:** `src/stages/stage4_1/fases.py`, `src/stages/stage4_1/trazado.py`, `src/stages/stage4_1/stage4_1.py`, `tools/generate_stage4_1.py`
- **Phase:** Revisión de diseño por fases del dueño del proyecto (2026-08-14) —
  documento «Fase 1 — El Cementerio que Recuerda», comparado contra el
  estado real por Claude Code el mismo día.
- **Reason:** El dueño pidió que la Fase 1 funcione como «ancla de
  realidad»: el jugador debe aprender —sin tutorial— que explorar
  recompensa, que el fondo puede esconder algo y que el sonido llama la
  atención, antes de que la Fase 2 empiece a romper esas reglas. Lo que
  hoy existe cumple la mitad negativa (nada de enemigos, nada de trampas,
  nada de música intensa: la Fase 1 es la única de las seis sin
  `sonido_ambiente`) pero no la mitad positiva:
  - **Cero anomalías ambiguas de fondo.** El único elemento sobrenatural es
    el fantasma de `_dibujar_fantasma_personal`, y no es ambiguo: tiene un
    `MessageTrigger` con el nombre escrito encima, sobre el camino
    principal. No existe el evento que pide el dueño —una silueta que
    cruza detrás de una tumba menos de un segundo, sin música ni shake,
    que el jugador puede simplemente no ver.
  - **Una sola «historia pequeña», no varias.** El diseño pide tumbas con
    reacciones distintas (una con sonido al acercarse, una que cambia si
    el jugador vuelve). Hoy sólo hay las dos lápidas del easter egg
    (Teresa Murillo, Hugo Salazar Castillo), sin variación entre ellas.
  - **Sin memoria espacial.** Nada en la Fase 1 depende de que el jugador
    regrese a una zona ya visitada — el punto 10 del dueño («el jugador
    piensa: estoy seguro de que antes estaba diferente») no tiene ningún
    gancho en el código.
  - **El fondo está vacío.** El TMX ya trae `BG_Far`/`BG_Mid`/`BG_Near`
    como capas separadas (la estructura de tres planos que pide el punto
    11 existe), pero `tools/generate_stage4_1.py::generar()` las rellena
    con ceros para las seis fases — ninguna silueta de fondo, ninguna
    señal a lo lejos.
  - **Sin capas de sonido natural.** El silencio de la Fase 1 es literal
    (sin `sonido_ambiente`), no el silencio *poblado* de pájaros, viento,
    pasos e insectos que describe el dueño — no hay ningún sistema de
    sonido ambiental en capas, sólo el canal único de `_actualizar_sonido_de_fase`.
  - **Terreno completamente plano.** `FILA_SUELO` es constante en toda la
    Fase 1 (la única loma real del nivel es la de la Fase 3) — no hay
    nada que saltar, ni desniveles pequeños, ni espacios que explorar
    verticalmente.
  - **Choque estructural, sin resolver:** el dueño propone un hub pequeño
    con ramificaciones (Sector A / Sector B / tumba secreta) para la Fase
    1. Eso contradice la decisión ya tomada en AUD-467
    (`docs/niveles/13_STAGE_4_1.md` §0): el 4-1 entero es un pasillo
    horizontal sin bifurcaciones, después de que el dueño rechazara
    jugada la geometría no lineal del pozo. No se puede cerrar este punto
    sin que el dueño confirme si quiere reabrir esa decisión o adaptar la
    idea a bolsillos laterales cortos dentro del pasillo.
  - **La música no modula por fase.** `BGM_TRACK = "bgm_final_approach"`
    (`stage4_1.py`) es una sola pista para las seis fases — no hay
    mecanismo para que la Fase 1 suene distinta de la aproximación final
    a Paburu, lo que compite con el punto 5 del dueño («guardar el sonido
    como recurso»).
- **Resolution plan:** Sin fecha. Depende primero de que el dueño resuelva
  el choque de estructura (hub vs. pasillo). El resto —anomalía de fondo,
  historias de tumba adicionales, sonido ambiental en capas, memoria
  espacial al volver, decoración en `BG_Far`/`BG_Mid`/`BG_Near`— se puede
  construir dentro del pasillo actual sin reabrir esa geometría. Ver
  [[GAP-058]] para el fondo de parallax pendiente, que es el mismo hueco
  visto desde el lado del arte.
- **Nota (AUD-478, 2026-08-14):** parcialmente resuelto. Se añadió la
  anomalía ambigua de fondo que pedía el punto 7: una figura sin nombre
  (`siluetas._figura_lejana`) que aparece hacia la columna 95 —lejos de
  las lápidas del easter egg, para no confundirse con el fantasma de
  Teresa— menos de medio segundo, en una ventana aleatoria de 20-40 s, sin
  tocar sonido, disparadores ni diálogo (mismo principio que la Bruja de
  la Fase 3, AUD-475; pruebas en `TestLaAnomaliaAmbiguaDeLaFase1`,
  `tests/test_stage4_1.py`). **Sigue pendiente:** el choque de estructura
  (sin resolver, no se tocó), varias historias de tumba en vez de una,
  memoria espacial al volver, decoración en `BG_Far`/`BG_Mid`/`BG_Near`,
  capas de sonido natural y la música por fase.
- **Nota (AUD-513, 2026-08-16):** tres puntos más, cerrados. La música por
  fase ya se había resuelto en AUD-493 ([[GAP-065]] §12) desde el lado del
  sistema, no de esta fase en concreto. **Historias de tumba distintas:**
  `Stage4_1._actualizar_tumba_susurrante` añade una segunda reacción, por
  sonido y no por nombre ni silueta —`trazado.COLUMNA_TUMBA_SUSURRO`, lejos
  del easter egg y de la anomalía—, para no confundirse con las otras dos
  lecturas de la Fase 1. **Memoria espacial:** `_actualizar_memoria_espacial`
  recuerda cuánto avanzó el jugador dentro de la fase y, si vuelve tras
  alejarse lo bastante (`UMBRAL_MEMORIA_ESPACIAL`), el fantasma de Teresa se
  ve más presente que la primera vez (`ALFA_EXTRA_AL_REGRESAR`) — el mismo
  fantasma, no uno nuevo, que es justo lo que pide el punto 10 («estoy
  seguro de que antes estaba diferente»). El fondo de parallax se cerró
  aparte, ver la nota de [[GAP-058]]. Pruebas en
  `tests/test_la_tumba_susurra_y_el_fantasma_recuerda.py`. **Sigue
  pendiente, y no se toca desde aquí:** el choque de estructura (hub vs.
  pasillo) — sigue siendo una decisión del dueño, no un defecto de código.
- **Decisión confirmada (2026-08-16):** consultado directamente, el dueño
  mantiene AUD-467: el pasillo horizontal sigue siendo la forma final del
  nivel. El hub de la Fase 1 que pedía la crítica de diseño **no se
  construye** — no por costo, sino porque contradice una geometría que ya
  se jugó, se rechazó una vez (el pozo vertical) y se confirmó de nuevo
  ahora. Este punto queda cerrado por decisión, igual que se cerraba GAP-024
  antes de que otra decisión posterior lo reabriera — la diferencia es que
  aquí la decisión se sostiene.

## [GAP-060] `stage4_1` Fase 2 — la fricción no es sistémica, el Venado no enseña por comportamiento y no hay progresión de dificultad

- **File:** `src/stages/stage4_1/fases.py`, `src/stages/stage4_1/trazado.py` (`SEGMENTOS_FASE2`, `FRENO_DEL_MUSGO`, `FRENO_DEL_LODO`), `src/stages/stage4_1/stage4_1.py`
- **Phase:** Revisión de diseño por fases del dueño del proyecto (2026-08-14) —
  documento «Fase 2 — El Sendero del Venado», comparado contra el estado
  real por Claude Code el mismo día.
- **Reason:** El dueño pide que la Fase 2 enseñe «mi movimiento depende
  del mundo» mediante una progresión jugable real (superficie simple →
  superficies combinadas → superficie + pendiente → superficie + lluvia →
  dominio) y que el Venado funcione como presencia narrativa que se ve
  fuera de alcance antes de hablar, no como un NPC que aparece una vez a
  dar su diálogo. Lo construido hoy es la versión mínima de la mecánica,
  no la progresión:
  - **La fricción es estática, no sistémica.** `SEGMENTOS_FASE2` alterna
    cinco tramos fijos de musgo (0.94) y lodo (0.88) — dos valores
    constantes durante toda la sección. El punto 14 del dueño pide que la
    lluvia intensifique el resbalón progresivamente («al principio,
    musgo = ligeramente resbaladizo; después de lluvia intensa, mucho
    más»); hoy `FrictionZone.multiplicador` no depende de nada del clima.
  - **Sin pendientes en la Fase 2.** Las únicas pendientes del nivel
    (`LOMAS_FASE3`, `trazado.py`) están en la Fase 3. El punto 13 pide
    que la propia Fase 2 combine «superficies + pendientes» antes de
    llegar a la Fase 3 — hoy ese paso de la progresión no existe.
  - **El Venado sólo aparece una vez, al hablar.** `_dibujar_espiritu` lo
    dibuja únicamente durante el 15 %-85 % del tramo, centrado en el
    `MessageTrigger` de columna fija (`desde_columna + 60`). No hay
    apariciones previas parciales «fuera de alcance» —entre árboles, tras
    una colina, cruzando un claro— que el dueño pide en los puntos 9-12
    para que el jugador aprenda a seguirlo antes de que hable.
  - **Sin mecánica de huellas.** El punto 28 propone huellas del Venado
    como herramienta de navegación (que a veces desaparecen o terminan
    abruptamente). No existe ningún objeto ni decoración de ese tipo.
  - **Sin el pequeño desafío de control que pide el punto 8** (una
    pendiente corta que termina en zona resbaladiza, para que el jugador
    aprenda a frenar antes de entrar). No hay geometría de ese tipo en la
    Fase 2.
  - **Sin zona secundaria opcional** (punto 15: un bosque secundario con
    una historia, una aparición o una tumba antigua, no obligatorio).
  - **Sin señales de «el bosque observa»** (punto 16: ramas sin viento,
    ojos entre árboles, huellas, una figura, hojas desplazándose) más
    allá de la aparición fija del Venado.
  - **Sin el momento de «la física vuelve a la normalidad»** tras liberar
    al espíritu (punto 21) ni un cambio perceptible del entorno en los
    segundos siguientes antes de que empiece la Fase 3 (punto 22) — la
    liberación de AUD-474 cambia si el espíritu asciende o no, pero no
    toca fricción, clima ni iluminación de forma diferenciada.
  - Lo que sí coincide: cero enemigos, sin combate, sin plataformas de
    precisión extrema, sin jumpscare, diálogo breve durante la
    exploración sin pantalla de carga (`Cutscene`/`MessageTrigger`, no
    una cinemática larga) — el punto 18 y el punto 26 del dueño ya se
    cumplen.
- **Resolution plan:** Sin fecha. La fricción escalable por intensidad de
  lluvia y el paso de «superficie + pendiente» necesitan que `fases.py`
  deje de tratar cada fase como estática por tramo y empiece a leer del
  estado de clima actual — un cambio de forma, no sólo de datos. Las
  apariciones previas del Venado y las huellas de navegación son
  contenido nuevo en `siluetas.py`/`trazado.py`, sin bloqueo de diseño
  pendiente (a diferencia de [[GAP-059]], aquí no hay ningún choque con
  una decisión ya tomada del dueño).
- **Nota (AUD-479, 2026-08-14):** parcialmente resuelto. El Venado ya no
  queda encendido todo el tramo antes de hablar: `_venado_visible`
  (`Stage4_1._actualizar_apariciones_previas_del_venado`) lo hace asomar a
  destellos de 1,5-3 s cada 4-9 s hasta `AVANCE_ANTES_DEL_DIALOGO`
  (la misma columna que usa el `MessageTrigger` de diálogo,
  `trazado.DESVIO_COLUMNA_DIALOGO` — un solo sitio para las dos, para que
  no puedan desincronizarse); pasado ese punto vuelve al fundido continuo
  normal, igual que el Rey Terciopelo y el Gavilán (pruebas en
  `TestLasAparicionesPreviasDelVenado`, `tests/test_stage4_1.py`).
  **Sigue pendiente:** la fricción no escala con la lluvia, no hay
  pendientes en la Fase 2, sin mecánica de huellas, sin desafío de
  control, sin zona secundaria opcional, sin señales de «el bosque
  observa», y sin el momento de «la física vuelve a la normalidad» tras
  liberar al espíritu.
- **Nota (AUD-513, 2026-08-16):** tres puntos más, cerrados —la fricción
  sistémica, las huellas, y el retorno a la normalidad. **Fricción con la
  lluvia:** `_actualizar_friccion_de_la_lluvia` escala `multiplicador` con
  una intensidad que crece con el avance dentro de la sección; no se
  identifica la `ZonaDeFriccion` por `material` (el TMX comprometido no lo
  declara y regenerarlo habría borrado el arte pintado a mano de
  `BG_Far`/`BG_Mid` — ver la nota de [[GAP-058]]), sino por el valor de
  fábrica de su propio `multiplicador` (`FRENO_DEL_MUSGO`/`FRENO_DEL_LODO`),
  recordado por id de entidad la primera vez que se ve. **Huellas:**
  `trazado.HUELLAS_FASE2` y `_dibujar_huellas_del_venado`, en dos grupos con
  un corte entre ellos — «terminan abruptamente», no un rastro continuo — y
  sólo antes de que el Venado hable. **La física vuelve a la normalidad:**
  liberar al Venado (AUD-474) hace caer la intensidad de la lluvia a un
  valor bajo y fijo en vez de seguir subiendo con el avance. Pruebas en
  `tests/test_stage4_1.py::TestLaFriccionEscalaConLaLluvia`. **Sigue
  pendiente:** las pendientes dentro de la Fase 2 (choca con el mismo eje
  horizontal/vertical de [[GAP-061]]), el desafío de control, la zona
  secundaria opcional, y las señales de «el bosque observa» más allá de
  las apariciones ya existentes del Venado.
- **Nota (AUD-522, 2026-08-17):** jugado, el musgo y el lodo de AUD-513 no
  se distinguían de nada — 0,94 contra 0,88 de `multiplicador` es un 6 %
  de diferencia, imperceptible contra un viento que sí desplaza al
  jugador de verdad. Petición directa del dueño: *«el musgo resbala como
  la nieve, el lodo es el que frena»* — dos mecánicas, no dos
  intensidades del mismo freno.

  El musgo pasa de `multiplicador` a un campo nuevo, `ZonaDeFriccion.inercia`
  (`components.py`): amortigua la velocidad hacia el objetivo en vez de
  recortarla —el mismo patrón de `ChaseFlight.DRAG` (AUD-046)— así que
  soltar la tecla sobre musgo desliza un momento en vez de parar en seco,
  y sigue acotado por construcción (nunca "se dispara sin tope", el
  riesgo que AUD-236 ya había descartado para `multiplicador > 1`). El
  lodo se queda exactamente como estaba: frena con `multiplicador`, sin
  cambios.

  También ganó lo que le faltaba para notarse: pisada propia
  (`sfx_player_footstep_musgo`, un chapoteo corto y sordo, distinto del
  paso normal) y una partícula (`HitEffects.MUSGO`, motas verdosas al
  pisar) — las dos disparadas por `material="musgo"` en la
  `FrictionZone`, que hasta ahora tampoco se declaraba. TMX parcheado
  quirúrgicamente, mismo patrón que el mirador y los checkpoints (sólo la
  capa `Objects`, ninguna baldosa pintada a mano se toca). Pruebas en
  `tests/test_el_musgo_resbala.py` y `TestLaFriccionEscalaConLaLluvia`
  (`tests/test_stage4_1.py`, reescrita para separar musgo de lodo — antes
  esperaba que las dos escalaran igual). **Sigue pendiente:** todo lo que
  ya quedaba de la nota de AUD-513, arriba.

## [GAP-061] `stage4_1` Fase 3 — el viento no escala, el rayo no informa y las osamentas son decoración, no arquitectura

- **File:** `src/stages/stage4_1/fases.py`, `src/stages/stage4_1/trazado.py` (`LOMAS_FASE3`, `HUESOS_FASE3`), `src/stages/stage4_1/stage4_1.py` (`_actualizar_rayos`), `tools/generate_stage4_1.py` (`WindZone`)
- **Phase:** Revisión de diseño por fases del dueño del proyecto (2026-08-14) —
  documento «Fase 3 — El Ascenso de la Serpiente», comparado contra el
  estado real por Claude Code el mismo día.
- **Reason:** El dueño pide que la Fase 3 sea el salto jugable de la
  trilogía inicial: el viento como herramienta que se aprende a leer y
  usar, el rayo como sistema de información («flashlight natural») y las
  osamentas como arquitectura que construye el nivel, todo dentro de una
  sección con «dirección dominante hacia arriba». Lo construido hoy
  demuestra la mecánica en su forma mínima (viento real, rayo real, loma
  real, AUD-297/477) pero no la profundidad que pide el diseño:
  - **No es vertical.** El eje dominante de la Fase 3, como el del resto
    del 4-1, es horizontal — decisión explícita del dueño en AUD-467.
    `LOMAS_FASE3` sube de `FILA_SUELO` (30) a `FILA_CIMA` (20): 160 px de
    desnivel real dentro de un pasillo por lo demás plano, no la
    ascensión vertical dedicada («slopes, plataformas, paredes, rutas
    superiores e inferiores») que compara con *Shadow of the Colossus*.
    Mismo choque estructural que [[GAP-059]] documentó para el hub de la
    Fase 1: hay que decidir si se reabre el eje vertical o si el diseño
    se adapta al pasillo.
  - **El viento no escala ni tiene componente vertical.** `ZonaDeViento`
    (`components.py`) sí sopla en pulsos (`periodo`, mitad del ciclo
    encendida) — coincide parcialmente con el punto 8 del dueño— pero el
    generador coloca un único `WindZone` con `fuerza_x=-60.0`,
    `fuerza_y=0.0` y `periodo=3.2` para toda la zona de las lomas: una
    sola intensidad, no la progresión «leve → fuerte → intermitente →
    combinado con pendientes → combinado con salto» del punto 5. Sin
    `fuerza_y`, el viento no puede llevar al jugador por un vacío (punto
    7, «viento = herramienta») — y de hecho no hay ningún vacío que
    cruzar: el suelo es sólido en toda la Fase 3, así que «usar el
    viento» no tiene ningún contexto de plataformas donde aplicarse.
  - **El rayo sube el brillo, no revela nada.** `_actualizar_rayos` sólo
    escala `ambient_brightness` un instante y dispara un SFX
    simultáneo — no hay «trueno lejano» antes ni silencio momentáneo
    (punto 13), y como el ambiente base de la fase ya es 0.44 (visible)
    todo el tiempo, el rayo no oculta ni revela ninguna plataforma, ruta
    o criatura (puntos 11-12): sólo satura el brillo que ya había. La
    Bruja de AUD-475 es la única cosa que aparece sólo durante el rayo,
    y su función es sembrar duda, no informar sobre una ruta —cumple un
    mecanismo parecido al que pide el dueño, pero no la función.
  - **Los huesos son una baldosa de decoración, no arquitectura.**
    `HUESOS_FASE3` coloca una `CALAVERA` cada 12 columnas sobre el suelo
    — no hay costillas formando arcos, puentes ni plataformas (punto 4),
    ni la progresión «una vértebra, luego una columna, luego una
    estructura gigantesca» (punto 15) que el dueño pide como
    environmental storytelling de que el camino está construido
    alrededor de la Serpiente.
  - **Sin ruta alta/baja con riesgo-recompensa.** El pasillo tiene un
    único trazado; las dos lomas están sobre ese mismo camino, sin
    bifurcación entre una ruta segura y una expuesta al viento (puntos
    10, 17), y los checkpoints se reparten uniformemente cada 28 columnas
    en todo el mapa (`CADA_CUANTAS_COLUMNAS_CHECKPOINT`,
    `trazado.checkpoints()`) — no hay un tramo final sin puntos de
    reaparición que funcione como «demostración de dominio» (punto 22).
  - **Sin silencio específico antes de la ascensión.** La liberación del
    Rey Terciopelo usa el mismo mecanismo genérico de las tres fases con
    espíritu (AUD-474: `EventTrigger` + fundido/ascenso). No hay ningún
    momento en que la tormenta, el viento y la serpiente de fondo se
    detengan antes de que aparezca a hablar (puntos 19, 22-24) — el
    patrón ya existe en el motor (`shake_de_silencio` de la Fase 4 hace
    algo parecido, cortar el clima de golpe) pero no está aplicado aquí.
  - **Sin apertura ni consecuencia tras la ascensión.** Punto 25: «queda
    una apertura» que antes bloqueaba la tormenta. El pasillo siempre
    estuvo abierto — no hay ningún obstáculo que la partida de la
    Serpiente elimine.
  - **La serpiente de fondo es una sola presencia continua**
    (`_dibujar_serpiente_de_fondo`, vaivén sinusoidal), no la pluralidad
    ambigua que pide el punto 14 (huesos que parecen moverse, ojos,
    sombras, restos animados por el viento).
  - Lo que sí coincide: cero enemigos y ningún combate contra la
    Serpiente (punto 27); el diálogo se dispara durante la exploración
    sin cinemática larga (`MessageTrigger_Once` a mitad de sección); la
    escala de grises y la tormenta con rayos ya transmiten el tono de
    «tormenta y huesos» del punto 26; y el viento sí tiene una
    consecuencia física real sobre el jugador (`ZonaDeViento` empuja de
    verdad, no son sólo partículas), que es la base sobre la que
    construir la progresión que falta.
- **Resolution plan:** Sin fecha. Depende primero de la misma decisión de
  [[GAP-059]] sobre el eje del nivel (si se acepta que la Fase 3 siga
  siendo mayormente horizontal con desniveles reales, o si se reabre la
  verticalidad). El resto —escalar `WindZone` en intensidad a lo largo de
  la sección, dar al rayo una función de revelar en vez de sólo iluminar,
  convertir algunas calaveras en arquitectura navegable, y aplicar el
  patrón de silencio de la Fase 4 antes de la ascensión de la Fase 3— no
  choca con ninguna decisión tomada y se puede construir dentro del
  pasillo actual.
- **Nota (AUD-480, 2026-08-14):** parcialmente resuelto. Se aplicó el
  patrón de silencio de la Fase 4 antes del diálogo del Rey Terciopelo —
  no idéntico (no es un silencio total ni un shake único): la
  `ZonaDeViento` real del mapa baja al 10 % de su fuerza en una ventana
  alrededor de `AVANCE_ANTES_DEL_DIALOGO` y sube de vuelta en cuanto el
  jugador se aleja, repetible (`Stage4_1._actualizar_pausa_de_la_serpiente`;
  pruebas en `TestLaPausaDelDialogoDeLaSerpiente`). **Sigue pendiente:** el
  eje vertical (sin resolver, no se tocó), el rayo como revelador de rutas,
  las osamentas como arquitectura, y la escalada de intensidad del viento
  a lo largo de la sección.
- **Nota (AUD-513, 2026-08-16):** los tres puntos restantes, cerrados —
  salvo el eje vertical, que sigue sin tocarse a propósito.
  **Viento escalado:** `_factor_de_viento` multiplica la fuerza declarada
  en el TMX por una curva que sube de «leve» a «fuerte» en el primer 60 %
  del tramo y se queda ahí — la misma `_actualizar_pausa_de_la_serpiente`
  la aplica antes de la reducción por diálogo, así que las dos conviven.
  **El rayo revela:** `_dibujar_columna_de_huesos` sube el alfa de las
  osamentas gigantes de 60 a 190 mientras dura el relámpago —
  prácticamente invisibles en penumbra normal, a plena vista durante el
  flash— en vez de sólo escalar `ambient_brightness` como antes.
  **Osamentas como arquitectura, la mitad visual:** `siluetas._vertebra_gigante`
  se alza sobre el paisaje en tres puntos de la sección
  (`COLUMNAS_DE_HUESOS_FASE3`) — la mitad **navegable** (una plataforma
  sólida de verdad) sigue sin construirse: exige geometría nueva en el
  generador, y regenerar `stage4_1.tmx` borraría el arte pintado a mano de
  `BG_Far`/`BG_Mid` (ver la nota de [[GAP-058]]). Pruebas en
  `tests/test_el_horizonte_y_la_despedida.py`. **Sigue pendiente:** el eje
  vertical (decisión del dueño, no se reabre desde aquí) y la mitad
  navegable de las osamentas.
- **Decisión confirmada (2026-08-16):** consultado directamente, el dueño
  mantiene AUD-467 — el pasillo horizontal, no una ascensión vertical
  dedicada. Misma decisión que [[GAP-059]], la misma pregunta (1) de
  [[GAP-065]] §14, confirmada una sola vez para el nivel entero. La
  verticalidad de la Fase 3 **no se construye**.
- **Nota (AUD-516, 2026-08-17):** resuelto el punto de «los checkpoints se
  reparten uniformemente cada 28 columnas en todo el mapa... no hay un
  tramo final sin puntos de reaparición». Petición directa del dueño: el
  4-1 es un escenario *psicológico de terror* y 32 checkpoints (cada 448
  px) anulaban la tensión — reaparecer costaba casi nada. Bajado a 6, uno
  por fase, elegidos a mano en terreno llano antes de cada set piece
  (`COLUMNAS_CHECKPOINT`, `trazado.py`). El efecto secundario cubre
  exactamente lo que este punto pedía: desde el último checkpoint (columna
  760, Fase 6) hasta el final del nivel no hay ningún punto de
  reaparición — el tramo final, con el mirador y la secuencia de
  despertar, se recorre sin red. Pruebas actualizadas en
  `TestElNivelSePuedeJugar::test_hay_seis_checkpoints_uno_por_fase`
  (`tests/test_stage4_1.py`), que reemplaza la antigua que exigía ≤500 px
  entre checkpoints — esa regla general de `66_GUIA_DE_LEVEL_DESIGN.md` es
  justo la que aquí se rompe a propósito. **Sigue pendiente** el resto de
  este GAP: la progresión de intensidad del viento, el rayo que revela en
  vez de sólo iluminar, y la mitad navegable de las osamentas.

## [GAP-062] `stage4_1` Fase 4 — el sonido no tiene dirección, nada cambia tras el silencio y no hay mecánica de quietud

- **File:** `src/stages/stage4_1/fases.py`, `src/stages/stage4_1/stage4_1.py` (`_actualizar_silencio_y_shake`, `_actualizar_grito_del_gavilan`, `_actualizar_sombra_del_gavilan`, `_dibujar_sombra_de_ave`), `src/framework/scenes/stage_parts/sonido.py`
- **Phase:** Revisión de diseño por fases del dueño del proyecto (2026-08-14) —
  documento «Fase 4 — El Bosque que Observa», comparado contra el estado
  real por Claude Code el mismo día.
- **Reason:** El dueño pide que la Fase 4 cambie el tipo de desafío de
  físico a perceptual: sonido direccional que no siempre dice la verdad,
  sombras de fondo con eventos propios, cambios de escenario tras el
  silencio que el jugador debe reconstruir, y una mecánica de quietud
  donde detenerse revela información. La pieza mejor lograda de las
  cuatro fases revisadas hasta ahora vive aquí — el silencio súbito y el
  shake sin causa visible (`_actualizar_silencio_y_shake`) coinciden casi
  al pixel con el punto 12 del dueño: sin transición musical, sin aviso,
  `stop_ambient()` sin fundido, un shake único y breve. Pero alrededor de
  esa pieza faltan las que le dan sentido:
  - **El grito aislado no tiene dirección, aunque el motor ya sabe
    hacerlo.** `_actualizar_grito_del_gavilan` llama a
    `self._play_sfx_named(...)` — sin posición. `AudioManager.play_sfx_at`
    y el propio helper `_play_sfx_spatial` de `sonido.py` (línea 151) ya
    hacen paneo estéreo por posición X en el mundo, y otro sistema del
    motor (`play_sfx_critico`) ya lo usa — el Gavilán simplemente no lo
    invoca. Es el gap más barato de cerrar de los cuatro: cambiar una
    llamada, no construir un sistema nuevo. Sin esto, el punto 4 del
    dueño («pájaro → izquierda, rama → derecha») no tiene ninguna base
    técnica que lo sostenga hoy, aunque el motor ya la tiene.
  - **La sombra del Gavilán es siempre el mismo sprite identificable.**
    `_dibujar_sombra_de_ave` cruza siempre de izquierda a derecha, a la
    misma altura (`y=80`), con la silueta de `_gavilan` reconocible — el
    punto 10 pide explícitamente lo contrario: «no debería aparecer como
    un sprite claramente identificable cada vez... queremos presencia,
    no exposición» (aparecer detrás, cruzar lateralmente, confundirse con
    una sombra). Hoy sólo hay una variante de cruce.
  - **Grito y sombra no están realmente coordinados**, pese a que el
    comentario de `fases.py` dice que sí («una sombra de ave... cruzando
    el cielo... coordinada con el grito»): `_proximo_grito` y
    `_proxima_sombra` son dos temporizadores aleatorios independientes
    (`ESPERA_ENTRE_GRITOS`, `ESPERA_ENTRE_SOMBRAS`), sin ninguna relación
    entre sí. Vale la pena corregir el comentario o la implementación,
    lo que sea cierto.
  - **Nada del escenario cambia tras el silencio.** El punto 13 es central
    en el diseño del dueño: un árbol que antes estaba en pie ahora está
    caído, un camino que antes estaba cerrado ahora está abierto — el
    jugador reconstruye que «algo ocurrió» sin que se le muestre qué. Hoy
    el silencio sólo dispara el shake y, más tarde, gritos y una sombra;
    ninguna decoración ni geometría cambia de estado.
  - **Sin memoria espacial al volver** (punto 14) — mismo hueco que
    [[GAP-059]] y [[GAP-060]] documentaron para las Fases 1 y 2: no hay
    ningún mecanismo en todo `stage4_1` que condicione algo a que el
    jugador regrese a una zona ya visitada.
  - **Ninguna anomalía ambigua antes del punto medio de la sección.**
    Los puntos 6-9 piden que el Halcón empiece a insinuarse mucho antes
    del silencio (alas que se oyen sin pájaro visible, una figura de
    fondo que desaparece si el jugador se da la vuelta). Hoy la primera
    mitad de la Fase 4 es sólo lluvia, partículas de ceniza y los árboles
    cortados estáticos de `ARBOLES_FASE4` — sin ningún evento.
  - **El diálogo se dispara por posición fija, no por acumulación de
    percepción.** El `MessageTrigger_Once` de `dialogo_id="gavilan"` está
    en `desde_columna + 60`, igual que el de las otras dos fases —no
    depende de cuánto investigó el jugador (punto 15: «después de varias
    interacciones perceptuales»).
  - **Sin sistema de «el Halcón responde a la atención del jugador»**
    (puntos 17, 19): nada en el código consulta hacia dónde mira o se
    detiene el jugador para decidir si dispara un evento.
  - **Sin mecánica de quietud.** El comentario de
    `_actualizar_gradacion` dice, casi como declaración de principios
    contraria a lo que pide el dueño: «el cambio se ve al caminar, no al
    esperar quieto» — y es cierto en todo `stage4_1`: no existe ninguna
    detección de cuánto tiempo lleva el jugador inmóvil, así que el punto
    24-25 («detenerse también es jugar») no tiene ningún gancho técnico
    hoy.
  - **La lluvia no tiene función perceptual.** Es un canal de clima y un
    canal de audio ambiente independientes (`_actualizar_sonido_de_fase`)
    — no hay ningún acoplamiento entre intensidad de lluvia y audibilidad
    de otro sonido (punto 21-22: un sonido tenue que la lluvia esconde y
    luego deja oír).
  - **La ascensión del Gavilán usa la misma fórmula genérica que Venado y
    Rey Terciopelo** (`_fundido_del_espiritu`, avance 0.85-1.0) — no hay
    una «ascensión aérea» distinta con aves regresando gradualmente
    (punto 27); los gritos y sombras siguen su propio temporizador
    aleatorio sin picar en el momento de la ascensión.
  - **Sin anomalía final ambigua antes de pasar a la Fase 5** (punto 28):
    `_actualizar_sombra_del_gavilan` simplemente deja de disparar en
    cuanto `fase.sombra_de_ave` es falso al cruzar a la Fase 5 — corte
    limpio, no un último cruce sin confirmar qué era.
  - **La gradación no tiene picos en momentos sobrenaturales** (punto 3:
    «naranja envejecido → naranja intenso en los momentos
    sobrenaturales»): `SEPIA_VINTAGE`/`TINTE_VINTAGE` son constantes
    durante toda la fase, sin subir de intensidad junto con el grito o
    la sombra.
- **Resolution plan:** Sin fecha. El más barato de cerrar es el paneo
  espacial del grito (`_play_sfx_spatial` ya existe, sólo hay que
  invocarlo con la posición del Gavilán en vez de `_play_sfx_named`). El
  resto —variedad en la silueta de la sombra, cambios de escenario tras
  el silencio, una detección de quietud reutilizable (útil también para
  otras fases del terror psicológico del proyecto, no sólo ésta), y el
  acoplamiento lluvia↔audibilidad— son sistemas nuevos, no bloqueados
  por ninguna decisión de geometría como en [[GAP-059]] y [[GAP-061]].
- **Nota (AUD-481, 2026-08-14):** parcialmente resuelto — exactamente el
  ítem más barato del plan de arriba. `_actualizar_grito_del_gavilan` ya
  llama a `_play_sfx_spatial` con una posición al azar a la izquierda o
  la derecha del jugador (`_posicion_del_grito`), no al canal ciego
  `_play_sfx_named` (pruebas en `TestElGritoDelGavilanTieneDireccion`).
  **Sigue pendiente:** variedad en la silueta de la sombra, cambios de
  escenario tras el silencio, la detección de quietud, y el acoplamiento
  lluvia↔audibilidad.

- **Nota (AUD-492, 2026-08-15):** cerrados los dos itemes de percepcion del
  plan de arriba. Existe la **deteccion de quietud reutilizable** que el plan
  pedia -- `src/framework/stage/atencion.py`, en el framework y no en el
  escenario, justo para que la puedan usar otras fases del terror psicologico
  del proyecto-- y la Fase 4 la usa para dos cosas: el grito del Gavilan suena
  tres de cada cuatro veces **a la espalda** del jugador, hacia donde no mira
  (puntos 17 y 19), y **detenerse cuatro segundos adelanta el cruce de la
  sombra** (puntos 24-25, *«detenerse tambien es jugar»*), con una espera de
  12 s para que la quietud no se vuelva un grifo. El grito conserva una de
  cada cuatro apariciones de frente: una regla sin excepcion se aprende y deja
  de inquietar. Pruebas en `tests/test_el_escenario_observa.py`.
  **Sigue pendiente:** variedad en la silueta de la sombra, cambios de
  escenario tras el silencio, y el acoplamiento lluvia<->audibilidad.

- **Nota (AUD-513, 2026-08-16):** los tres últimos puntos, cerrados.
  **Variedad de sombra:** `_iniciar_cruce_de_sombra` elige, cada cruce, si
  se ve la silueta reconocible (`_gavilan`, minoría de las veces) o una
  mancha difusa nueva (`siluetas._sombra_difusa`), a qué altura
  (`ALTURAS_DE_CRUCE`) y en qué dirección — antes era siempre la misma
  silueta, a la misma altura, siempre izquierda→derecha. **Cambios tras el
  silencio:** el último árbol de `ARBOLES_FASE4` pasa a
  `siluetas._arbol_caido` (tronco en el suelo, no de pie) en cuanto
  `_shake_disparado` se activa — un cambio real de escenario, no un efecto
  encima del de siempre. **Lluvia↔audibilidad:** `_intensidad_de_lluvia_fase4`
  es una marea lenta que sube y baja el volumen del grito
  (`VOLUMEN_GRITO`) — cuando «llueve fuerte» tapa el sonido, cuando escampa
  se oye más claro. Pruebas en
  `tests/test_la_sombra_varia_y_el_bosque_cambia.py`.

## [GAP-063] `stage4_1` Fase 5 — la luna es sólo brillo ambiente, sin eventos atados a la oscuridad ni sonido de navegación

- **File:** `src/stages/stage4_1/fases.py`, `src/stages/stage4_1/trazado.py` (`TUMBAS_FASE5`), `src/stages/stage4_1/stage4_1.py` (`_actualizar_ambiente_de_fase`, `_dibujar_decoracion`)
- **Phase:** Revisión de diseño por fases del dueño del proyecto (2026-08-14) —
  documento «Fase 5 — La Planicie de los Muertos», comparado contra el
  estado real por Claude Code el mismo día.
- **Reason:** El dueño pide que la luna sea «un sistema de información»,
  no sólo iluminación: eventos que ocurren mientras está oculta y se
  descubren al volver, sonido que sustituye a la vista como orientación,
  landmarks distintos entre sí, y un tramo final donde luces verdes
  reemplazan progresivamente a la luna como guía hacia la Fase 6. Lo
  construido hoy resuelve bien la mitad ya corregida por AUD-476 (el
  ciclo nunca llega a negro real: `AMBIENTE_MIN_LUNA=0.20` se eligió a
  propósito por encima de la referencia de «casi negro» del proyecto,
  ver el comentario junto a `PERIODO_DE_LA_LUNA` en `stage4_1.py`) pero
  la luna sigue siendo únicamente una curva de brillo, no un sistema:
  - **Nada depende de si la luna está arriba o abajo.** `_actualizar_ambiente_de_fase`
    sólo escribe `_ambiente_base` con una senoidal continua
    (`PERIODO_DE_LA_LUNA=6.0`s) — ninguna otra función del escenario lee
    ese valor para decidir si aparece o desaparece algo. El punto 7 del
    dueño («cuando la luna está oculta pueden ocurrir cosas: una figura
    aparece, una tumba se abre, una sombra cruza») no tiene ningún gancho
    técnico: la decoración de la Fase 5 es estática en todo momento.
  - **Las cruces de conquistador son idénticas y regulares.**
    `TUMBAS_FASE5 = range(610, 749, 30)` coloca la misma silueta
    (`_cruz_conquistador`) cada 30 columnas, sin variación — no hay
    landmarks distintos entre sí (punto 21: árbol muerto, torre, capilla,
    roca, grupo de tumbas) que permitan al jugador decir «estoy cerca de
    aquella estructura» en vez de ver la misma cruz repetida.
  - **Sin figuras, procesiones ni cambios que aparezcan sólo con luz.**
    Los puntos 5, 16 y 20 (una figura junto a una tumba que sólo se ve
    iluminada; una procesión lejana que está más cerca la próxima vez que
    vuelve la luna; una multitud de figuras que desaparece sin
    explicación) no tienen ningún elemento equivalente — la única
    decoración de fondo son las cruces estáticas.
  - **El sonido no es navegación, es un solo bucle ambiental.**
    `sonido_ambiente = canto_ancestral.wav` es un único canal en volumen
    constante (`_actualizar_sonido_de_fase`, igual que las demás fases) —
    no depende de si la luna está arriba, no tiene dirección (mismo hueco
    que [[GAP-062]] documentó para el grito del Gavilán:
    `_play_sfx_spatial` existe y sigue sin usarse aquí), y no hay ninguna
    voz o campana que el jugador pueda seguir para orientarse (puntos
    12-14) — mucho menos la mezcla deliberada de «información confiable +
    información ambigua» que pide el punto 14.
  - **Sin camino que se revele sólo con la luna** (punto 27: un objetivo
    intermedio — «encontrar el camino iluminado» — antes de seguir hacia
    Paburu). El pasillo de la Fase 5 es único y siempre transitable
    igual, con o sin luna.
  - **Sin la transición de luces verdes al final de la fase** (puntos
    29-30): el mecanismo que el dueño describe —pequeñas luces verdes que
    empiezan a sustituir a la luna como guía— ya existe en el motor,
    pero vive enteramente dentro de la Fase 6 (`GRIETAS_FASE6`,
    `_actualizar_grietas`, encendido por proximidad). Hoy el corte entre
    Fase 5 y Fase 6 es seco en la columna 750 — no hay ninguna grieta
    adelantada asomando en el tramo final de la Fase 5 que anticipe la
    transición como pide el dueño.
  - **El ciclo de la luna no evoluciona.** El punto 4 pide un patrón
    aprendible al principio y «más irregular» después; `PERIODO_DE_LA_LUNA`
    es una sola constante durante toda la fase, sin ninguna variación de
    ritmo entre el principio y el final del tramo.
  - Lo que sí coincide: nunca hay negro absoluto (AUD-476, ver arriba);
    sin enemigos ni combate; el ciclo es regular y por tanto aprendible
    (aunque no evolucione, sí cumple la base del punto 4); ninguna
    plataforma difícil ni laberinto (la Fase 5 es el mismo pasillo llano
    que el resto del nivel, lo que de hecho ya cumple el punto 25 —
    «no haría laberintos»); y el uso de cánticos ancestrales sin fingir
    una lengua real (mismo principio que `canto_ancestral` en AUD-465) ya
    responde al cuidado que pide el punto 18 sobre no tratar la voz
    indígena como «sonido tribal = terror».
- **Resolution plan:** Sin fecha. Lo más aprovechable a corto plazo es
  extender `GRIETAS_FASE6` unas columnas hacia atrás para que el tramo
  final de la Fase 5 ya muestre alguna grieta adelantada (la mecánica ya
  existe, sólo falta que cruce la frontera de sección) y reutilizar
  `_play_sfx_spatial` (ver [[GAP-062]]) para el canto ancestral. Los
  eventos atados al estado de la luna (figuras, procesión, cambios de
  decoración) y la variedad de landmarks son contenido nuevo, sin ningún
  bloqueo de geometría — a diferencia de [[GAP-059]] y [[GAP-061]], la
  Fase 5 ya es exactamente el tipo de espacio abierto y legible que pide
  el dueño; sólo le falta lo que ocurre dentro de él.
- **Nota (AUD-482, 2026-08-14):** parcialmente resuelto. `GRIETAS_FASE6`
  empieza ahora en la columna 700, no 760 — las tres primeras (700, 720,
  740) caen dentro del tramo final de la Fase 5, encendidas por el mismo
  mecanismo de proximidad de siempre, sin código nuevo (pruebas en
  `TestLasGrietasAdelantadasDeLaFase5`; TMX regenerado con
  `tools/generate_stage4_1.py`). **Sigue pendiente:** el canto ancestral
  sigue sin paneo espacial, y los eventos atados al estado de la luna
  (figuras, procesión, cambios de decoración) siguen sin construirse.

- **Nota (AUD-488, 2026-08-15):** cerrados los dos primeros puntos. El canto
  ancestral ya no es solo un bucle de volumen constante: ademas de la cama de
  ambiente, **llama desde una columna fija** (`trazado.COLUMNA_DEL_CANTO`,
  745 -- al final de la seccion, de modo que seguirlo lleva hacia la salida y
  no hacia atras) por `_play_sfx_spatial`, y **sube de volumen cuando la luna
  se esconde** (`Stage4_1.luna_oculta`, derivada de `_ambiente_base` para que
  no haya dos senoidales que puedan desincronizarse). Eso cierra a la vez el
  «el sonido no es navegacion» de los puntos 12-14 y el «nada depende de si la
  luna esta arriba o abajo» del punto 7, y completa la mezcla de «informacion
  confiable + informacion ambigua» del punto 14: el canto es la mitad fiable,
  y el grito del Gavilan --que desde AUD-492 rehuye la mirada del jugador-- la
  ambigua. Pruebas en `tests/test_el_canto_orienta_en_la_planicie.py`.
  **Sigue pendiente:** los eventos atados al estado de la luna (figuras,
  procesion, cambios de decoracion) y la variedad de landmarks.

- **Nota (AUD-513, 2026-08-16):** los dos puntos restantes, cerrados —a un
  nivel modesto, no la lista completa del punto 5/16/20 (procesión que se
  acerca, multitud que desaparece). **Figura atada a la luna:**
  `_dibujar_figura_de_la_luna` sólo se pinta cuando `luna_oculta` supera
  `UMBRAL_LUNA_OCULTA`, junto a una de las cruces, no en el camino — el
  primer gancho real de «cuando la luna está oculta pueden ocurrir cosas».
  **Variedad de landmarks:** `siluetas.LANDMARKS_DE_LA_PLANICIE` cicla tres
  siluetas (`_cruz_conquistador`, `_cruz_caida`, `_grupo_de_tumbas`) en vez
  de repetir la misma cruz cada 30 columnas. Pruebas en
  `tests/test_la_luna_esconde_cosas.py`. **Sigue pendiente:** la variedad
  de eventos más rica que pide el diseño (procesión que se acerca cada
  ciclo, multitud que desaparece sin explicación) — lo que hay hoy es un
  gancho, no el catálogo completo.

## [GAP-064] `stage4_1` Fase 6 — sin silueta de Paburu, sin despedida de los espíritus y sin secuencia de despertar antes del corte

- **File:** `src/stages/stage4_1/fases.py`, `src/stages/stage4_1/trazado.py` (`GRIETAS_FASE6`, `TEXTO_FINAL_BASE`), `src/stages/stage4_1/stage4_1.py` (`_actualizar_grietas`, `_actualizar_mensaje_final`), `tools/generate_stage4_1.py`
- **Phase:** Revisión de diseño por fases del dueño del proyecto (2026-08-14) —
  documento «Fase 6 — El Camino hacia Paburu», comparado contra el estado
  real por Claude Code el mismo día. Cierra la serie de revisión por fases
  ([[GAP-059]]…[[GAP-063]] cubren las cinco anteriores).
- **Reason:** El dueño pide que la Fase 6 sea la resolución emocional del
  nivel: cada paso «despierta» el mundo, los tres espíritus liberados
  regresan brevemente como despedida, la escala crece hasta insinuar a
  Paburu sin mostrarlo completo, y el final es una secuencia sugerida
  —vibración, shake, silencio, un sonido profundo— no un corte seco. Lo
  construido hoy tiene ya la pieza central (las grietas que se iluminan
  al paso, un mecanismo real de «el mundo responde a tu presencia») y el
  mejor gancho de consecuencia narrativa de las seis fases —el mensaje
  final varía según cuántos espíritus se liberaron de verdad (AUD-474)—
  pero le falta casi todo lo que rodea a esa pieza:
  - **Ninguna silueta de Paburu en el fondo.** Los puntos 7-8 y 22-23
    piden que la escala crezca hasta «revelar parcialmente el lugar
    donde está Paburu» — una búsqueda en `src/stages/stage4_1/` confirma
    que «Paburu» sólo aparece en un comentario comparativo
    (`stage4_1.py`) y en el texto final (`TEXTO_FINAL_BASE`), nunca como
    elemento visual. Mismo hueco que [[GAP-059]] documentó para
    `BG_Far`/`BG_Mid`/`BG_Near`: siguen vacías también en la Fase 6.
  - **Los espíritus liberados no vuelven a aparecer.** `Fase(6, ...)`
    tiene `espiritu=None` y ningún código dibuja Venado, Rey Terciopelo
    ni Gavilán durante esta fase — los puntos 15-16 («Venado en la
    distancia, Serpiente como energía, Halcón en el cielo... una vez
    cada uno, como despedida») no tienen ningún gancho: `siluetas.ESPIRITUS`
    sólo se consulta cuando `fase.espiritu is not None`.
  - **Sin mirador.** El punto 17 («el jugador mira atrás y ve el camino
    que recorrió») no tiene ningún mecanismo de cámara — no hay ningún
    momento en que la cámara se aleje o cambie de encuadre en todo
    `stage4_1`.
  - **Las grietas no escalan.** `GRIETAS_FASE6 = range(760, 899, 20)`
    coloca siete luces a intervalo fijo, la misma densidad del principio
    al final del tramo, siempre a nivel de suelo — el punto 6 pide que
    empiecen pocas y aumenten («después suben por las paredes... el
    entorno completo parece estar conectado por ellas»). Hoy no hay
    ninguna progresión de densidad ni de altura.
  - **El final es un corte, no una secuencia.** El punto 25 describe una
    secuencia de despertar completa antes del corte a `stage4_2_boss_paburu`
    (vibración del suelo, shake pequeño, parpadeo de las grietas, aves
    alzando vuelo, la música se detiene, silencio, un sonido profundo).
    Hoy `_actualizar_mensaje_final` sólo reescribe el texto del
    `MessageTrigger_Once` según cuántos espíritus se liberaron, y el
    `NextTrigger` está a un par de baldosas — no hay ningún camera shake,
    ninguna pausa ni ninguna señal sonora específica del despertar.
  - **Sin pausa contemplativa antes del final** (puntos 23-24: «uno de
    los pocos momentos donde sí permitiría una pequeña pausa... deja que
    la imagen hable») — no existe ningún tramo sin gameplay ni cámara
    lenta en la Fase 6.
  - **Sin secreto opcional con los tres espíritus juntos** (punto 32) —
    no existe ningún objeto ni disparador de ese tipo.
  - **La música no se construye progresivamente.** Los puntos 13-14
    piden que el tema musical «nazca del mundo» —una nota, luego otra,
    luego una textura, luego el tema completo—, pero `BGM_TRACK` es una
    sola pista para las seis fases (mismo hueco que ya señaló [[GAP-059]]
    desde el lado de la Fase 1). El motor sí tiene un sistema de capas
    dinámicas (`framework.audio.DynamicMusicSystem`, calm/combat,
    referenciado en `stage_scene.py`), pero está diseñado para intensidad
    de combate, no para revelar instrumentos con el avance narrativo —
    y `stage4_1` no tiene combate, así que ese eje nunca se mueve aquí.
  - **El sonido no se «limpia» progresivamente.** Los puntos 12-13
    (agua, luego aves, luego viento, luego insectos, cada uno asociado a
    una luz nueva) no tienen equivalente: `sonido_ambiente =
    resonancia_solemne.wav` es un solo bucle constante, igual que en las
    otras cinco fases.
  - **Sin mecánica de revelación de geometría** (punto 10: un hueco que
    se convierte en camino al activar la energía) — el suelo de la Fase
    6 es sólido y uniforme (baldosa `SAGRADA`/`SAGRADA_RELLENO`) en todo
    el tramo, sin ninguna sección oculta que aparezca.
  - Lo que sí coincide, y es lo mejor logrado de la fase: las grietas
    verdes por pisada son un mecanismo real de «el mundo responde a tu
    presencia» (puntos 2-3, aunque por proximidad continua y no por
    conteo de pasos); la gradación interpola de verdad desde
    `NOCTURNO_AZULADO` hacia `COLOR_PLENO` a lo largo del tramo (punto 4,
    aunque como una curva continua, no las etapas narrativas discretas
    que describe el dueño); cero enemigos y cero trampas en toda la fase
    cumplen directamente el punto 31; y el mensaje final variable según
    cuántos espíritus se liberaron de verdad (AUD-474) ya es la
    consecuencia narrativa medible que pide el punto 26 — de hecho es el
    ejemplo más fuerte de «agencia del jugador» de las seis fases hasta
    ahora.
- **Resolution plan:** Sin fecha. Cierra la revisión de diseño por fases
  iniciada en [[GAP-059]]. Antes de construir nada de esto conviene que
  el dueño revise el conjunto de los seis GAP (059-064) de una vez: hay
  patrones que se repiten en las seis fases —música de una sola pista
  para todo el nivel, `BG_Far`/`BG_Mid`/`BG_Near` vacíos en las seis, sin
  memoria espacial en ninguna, sin audio direccional en ninguna pese a
  que `_play_sfx_spatial` ya existe (ver [[GAP-062]])— y probablemente
  conviene resolverlos una vez para las seis fases a la vez, no fase por
  fase, antes de encarar lo específico de cada una (la secuencia de
  despertar de esta fase, el mirador, la despedida de los espíritus).
- **Nota (AUD-513, 2026-08-16):** cuatro puntos cerrados de un lote.
  **Silueta de Paburu:** `_dibujar_paburu` crece con el avance de la fase
  y nunca revela el todo (alfa y ancho topados). **Despedida de los
  espíritus:** `_dibujar_despedida_de_los_espiritus` deja ver un instante,
  repartidos a lo largo del tramo, a los que el jugador liberó de verdad
  (AUD-474) — a quien no liberó nada no le queda nada que despedirse.
  **Las grietas escalan:** más lejos se encienden y más tardan en
  apagarse cerca del final (`DISTANCIA_DE_GRIETA_FINAL`,
  `BAJADA_DE_GRIETA_FINAL`) — no hay luces nuevas que colocar sin
  regenerar el mapa (ver la nota de [[GAP-058]]), así que el «cada vez
  más conectado» se consigue con las mismas grietas de siempre.
  **Secuencia de despertar, la mitad que no bloquea:**
  `_actualizar_secuencia_de_despertar` da el shake y el corte de música,
  una sola vez cerca del final. Pruebas en
  `tests/test_el_horizonte_y_la_despedida.py` y
  `tests/test_el_despertar_de_la_fase_6.py`. **Sigue pendiente entonces:**
  el mirador, la pausa contemplativa, y un sonido propio en vez de
  prestado — los tres, resueltos abajo.
- **Nota (AUD-515, 2026-08-16):** el mirador y la pausa contemplativa
  (punto 17 y 23-24) se daban por bloqueados —*«necesitan un sistema de
  cámara/pausa que el motor no tiene»*— y era un diagnóstico equivocado:
  `CutsceneSystem` ya sabe mover la cámara (`camara x y duración`,
  `cutscene_guion.py`) y ya se usa en este mismo mapa para la cutscene de
  introducción, con `bloquea=True` congelando al jugador mientras dura —
  la pausa contemplativa, literalmente gratis. El mirador es un guión de
  cutscene nuevo: la cámara se aleja 280 px hacia el camino recorrido, se
  queda 2,5 s, y vuelve. Se añadió un objeto `Cutscene` nuevo
  (`COLUMNA_MIRADOR_FASE6`, `trazado.py`) al TMX comprometido con un
  parche quirúrgico del XML —sólo la capa `Objects`, con el bloque exacto
  que produce `tools/generate_stage4_1.py::_objetos()`, para que
  `TestElMapaSigueAtadoASuGenerador` no distinga el mapa del que
  generaría el código— en vez de regenerar el mapa completo, que habría
  borrado el arte de `BG_Far`/`BG_Mid` (ver la nota de [[GAP-058]]).
  De paso, la secuencia de despertar deja de tomar prestado
  `sfx_bosses_phase_change` (un cue de combate) y usa `despertar_profundo`,
  un sonido propio con la misma reverberación horneada que el silencio de
  la Fase 4 (ver la nota de [[GAP-058]]). Pruebas en
  `tests/test_el_mirador_de_la_fase_6.py`. **Sigue pendiente, sin fecha:**
  el secreto opcional con los tres espíritus juntos, la música que se
  construye progresivamente, y el sonido que se «limpia» por capas — los
  tres son sistemas más grandes que una cutscene, no huecos de una llamada.

## [GAP-065] `stage4_1` como sistema — la progresión de color ya cuenta la historia, la relación jugador↔escenario no siempre

- **File:** `src/stages/stage4_1/fases.py`, `src/stages/stage4_1/stage4_1.py`, `src/stages/stage4_1/trazado.py`, `tools/generate_stage4_1.py`
- **Phase:** Revisión de diseño por fases del dueño del proyecto (2026-08-14) —
  documento de síntesis «Legacy of InFest — Stage 4.1: La Entrada al
  Cementerio Sagrado», que mira las seis fases como un sistema único.
  Comparado contra el estado real por Claude Code el mismo día, después
  de cerrar la revisión fase por fase en [[GAP-059]]…[[GAP-064]].
- **Reason:** El documento de síntesis pide algo distinto de los seis
  anteriores: que el color, el sonido y la relación
  jugador-escenario funcionen como **un solo lenguaje narrativo continuo**
  a lo largo de las seis fases, no como seis piezas independientes. Visto
  así, algunos sistemas del `stage4_1` real ya cumplen ese estándar y
  otros no:
  - **La progresión de color es el sistema mejor logrado de todo el
    nivel — coincide casi exactamente con el documento.** El punto 11
    pide `Color natural → Blanco y negro → Escala de grises → Vintage
    naranja → Noche/luz lunar → Full color/verde sobrenatural`; las seis
    entradas de `FASES` en `fases.py` son, en el mismo orden,
    `COLOR_PLENO → BLANCO_Y_NEGRO → GRISES_NEUTROS → SEPIA_VINTAGE →
    NOCTURNO_AZULADO → COLOR_PLENO`, interpoladas de verdad por avance
    dentro de cada tramo (`_actualizar_gradacion`, AUD-463). Sólo le
    falta la coda final: el punto 11 pide que la Fase 6 termine en
    «verde sobrenatural», y hoy `Fase(6, ...)` tiene `tinte=None` — vuelve
    al color pleno sin ningún tinte verde que marque el despertar (mismo
    detalle que señaló [[GAP-064]] desde el lado de esa fase).
  - **La progresión de sonido existe en el orden correcto, pero es una
    sola capa por fase, nunca una mezcla que evoluciona.** `sonido_ambiente`
    por fase (`None → viento_de_bosque → storm_ambient → rain_ambient →
    canto_ancestral → resonancia_solemne`) sigue temáticamente la
    secuencia del punto 12, pero cada fase es un único bucle de volumen
    constante (`_actualizar_sonido_de_fase`) — no hay ninguna mezcla que
    se construya o se limpie con el tiempo. Es el mismo hueco que
    [[GAP-059]] a [[GAP-064]] repitieron fase por fase, visto ahora como
    lo que es: no son seis huecos de sonido distintos, es una sola
    limitación de arquitectura (un canal de ambiente, sin capas).
  - **De los seis eslabones de la relación jugador↔escenario (§13 del
    documento), tres están sólidamente construidos y uno prácticamente no
    existe.** Mapeando cada eslabón contra el código real:
    - F1 «el jugador observa el escenario» — sólido: cero elementos
      sobrenaturales que actúen sobre el jugador en la Fase 1.
    - F2 «el escenario afecta al jugador» — sólido:
      `ZonaDeFriccion` (musgo/lodo) cambia de verdad la física del
      jugador.
    - F3 «el jugador aprende a utilizar el escenario» — a medias:
      `ZonaDeViento` empuja de verdad, pero sin `fuerza_y` y sin ningún
      vacío que cruzar (ver [[GAP-061]]), el jugador nunca llega a
      *usar* el viento como herramienta — sólo lo sufre, igual que en la
      Fase 2.
    - **F4 «el escenario parece observar al jugador» — es el eslabón más
      débil de los seis.** No existe ningún código en `stage4_1.py` que
      lea la posición, la dirección o el tiempo de quietud del jugador
      para decidir un evento (ver [[GAP-062]]): los gritos y la sombra
      del Gavilán corren en temporizadores aleatorios, ciegos a lo que
      hace el jugador. El escenario no observa a nadie — sólo parece que
      lo hace por casualidad temporal.
    - F5 «el escenario oculta información al jugador» — a medias: el
      ciclo de la luna sí modula cuánto se ve de la pantalla entera
      (`_actualizar_ambiente_de_fase`), pero como la decoración es
      estática (ver [[GAP-063]]), no hay ningún contenido específico que
      esté realmente oculto y se revele — se oculta *brillo*, no
      *información*.
    - F6 «el jugador activa y revela el escenario» — sólido: las
      grietas por pisada son una activación real ligada a la posición
      del jugador.
  - **El verdadero clímax mecánico (§20) sí está construido, aunque de
    forma discreta.** El documento insiste en que liberar a los
    espíritus, no llegar a Paburu, es el clímax real — y
    `_actualizar_mensaje_final` (AUD-474) hace de esto algo medible: el
    texto final de la Fase 6 cambia según cuántos de los tres espíritus
    se liberaron de verdad. Es el mecanismo más fiel a la síntesis de
    todo el nivel, y vale la pena no tocarlo al resolver el resto de
    estos GAP.
  - **La lista de «lo que evitaría» (§18) se cumple en su totalidad**:
    cero enemigos, cero coleccionables (no hay un solo objeto
    `Recogible`/`Collectible` en `tools/generate_stage4_1.py`), cero
    plataformas de precisión, la Fase 5 nunca llega a negro real
    (AUD-476), y los tres espíritus se liberan con una sola interacción
    de botón, no con una lista de misiones.
  - **El choque estructural ya documentado en [[GAP-059]] y [[GAP-061]]
    es, visto en conjunto, el mismo choque repetido dos veces**: la Fase
    1 quiere un hub y la Fase 3 quiere verticalidad, y las dos chocan con
    la misma decisión de AUD-467 (pasillo horizontal sin bifurcaciones).
    No son dos preguntas distintas para el dueño — es una sola pregunta
    sobre el eje del nivel completo.
- **Resolution plan:** Sin fecha. Esta entrada no añade trabajo nuevo:
  es la lectura de conjunto de [[GAP-059]]…[[GAP-064]]. Si el dueño
  quiere priorizar, el orden que se desprende de mirar el sistema
  completo es: (1) resolver la pregunta del eje horizontal/vertical una
  sola vez, no fase por fase; (2) construir el eslabón F4 («el escenario
  observa») como sistema reutilizable de atención del jugador (posición +
  quietud + dirección), porque es el único de los seis que hoy no existe
  en absoluto, no sólo que esté incompleto; (3) los tres huecos de
  infraestructura que se repiten en las seis fases —una sola pista de
  música, `BG_Far`/`BG_Mid`/`BG_Near` vacíos, y `_play_sfx_spatial` sin
  usar pese a existir— porque resolverlos una vez sirve a las seis fases
  a la vez, no a una sola.
- **Nota (AUD-478…483, 2026-08-14):** parcialmente resuelto. De los tres
  huecos de infraestructura del punto (3), uno ya se cerró para una fase:
  `_play_sfx_spatial` ahora sí se usa (el grito del Gavilán, AUD-481 —
  ver [[GAP-062]]). Se cerró también el detalle señalado del punto de
  color: la Fase 6 ya declara `tinte=(TINTE_DESPERTAR, ALFA_TINTE_DESPERTAR)`
  en vez de `None` (AUD-483), así que la progresión de color queda
  todavía más cerca de lo que pide el punto 11 (pruebas en
  `TestElTinteDeLaFase6`). También se sumaron piezas de las fases
  individuales: la anomalía ambigua de la Fase 1 (AUD-478, [[GAP-059]]),
  las apariciones previas del Venado (AUD-479, [[GAP-060]]), la pausa del
  diálogo de la Fase 3 (AUD-480, [[GAP-061]]) y las grietas adelantadas
  de la Fase 5 (AUD-482, [[GAP-063]]). **Sigue pendiente, sin tocar:** el
  eslabón F4 («el escenario observa») completo, la música de una sola
  pista para las seis fases, y `BG_Far`/`BG_Mid`/`BG_Near` vacíos.
- **Nota (AUD-492…488, 2026-08-15):** aplicados los puestos (2) y (3) del
  plan de resolucion de arriba, que es el orden que el propio documento de
  sintesis fija.
  - **(2) El eslabon F4 ya existe.** Era el unico de los seis que no existia
    en absoluto. `src/framework/stage/atencion.py` (AUD-492) mide quietud,
    direccion y posicion del jugador, y la Fase 4 decide con eso de que lado
    suena el grito del Gavilan y cuando cruza su sombra. El escenario ya no
    corre en temporizadores ciegos: responde.
  - **(3) Dos de los tres huecos de infraestructura, cerrados.**
    `_play_sfx_spatial` ya se usa tambien en la Fase 5 (AUD-488, ver
    [[GAP-063]]), asi que deja de ser «existe y no lo usa nadie»; y la musica
    dejo de ser una sola pista para las seis fases (AUD-493): `Fase.musica`
    manda, cinco fases piden silencio y `bgm_final_approach` **entra** en la
    Fase 6 con un fundido de 2,5 s en vez de sonar desde el primer paso del
    cementerio. Pruebas en `tests/test_la_musica_del_4_1_entra_tarde.py`.
  - **Sigue pendiente, sin tocar:** el tercer hueco de infraestructura
    --`BG_Far`/`BG_Mid`/`BG_Near` vacios en las seis fases-- y la pregunta (1),
    el eje horizontal/vertical, que es una decision del dueno y no se reabre
    desde aqui: el pasillo horizontal se decidio en AUD-467 despues de que el
    dueno jugara y rechazara la geometria no lineal.
- **Nota (AUD-513, 2026-08-16):** cierra el tercer hueco de infraestructura
  y, con él, prácticamente todo lo que quedaba abierto de [[GAP-059]] a
  [[GAP-064]] salvo la pregunta (1). `BG_Far`/`BG_Mid`/`BG_Near` no se
  llenan con tiles del tileset —el mapa comprometido ya trae `BG_Far`/
  `BG_Mid` con arte pintado a mano, y regenerarlo lo habría borrado— sino
  con una cresta lejana **dibujada por código**, un perfil distinto por
  fase (`siluetas.dibujar_horizonte`), el mismo principio que ya usan los
  espíritus y la decoración: contornos honestos, no arte fingido. De paso
  se cerraron, uno por uno, casi todos los puntos que [[GAP-059]]…[[GAP-064]]
  dejaron pendientes tras sus notas anteriores — ver la nota de AUD-513 en
  cada uno. Lo único que sigue **sin tocar, a propósito**: la pregunta (1)
  del eje horizontal/vertical, que sigue siendo una decisión del dueño y
  no una omisión de código; la reverberación real (sin mezclador DSP); la
  mitad navegable de las osamentas de la Fase 3 (geometría sólida nueva,
  fuera de este lote); el mirador de la Fase 6 (necesita un sistema de
  cámara que este motor no tiene); y la pausa contemplativa / el secreto
  opcional de la Fase 6 (necesitan un sistema de pausa-por-escena que
  tampoco existe). Pruebas repartidas por fase, ver cada nota; también
  `tests/test_el_horizonte_y_la_despedida.py` para la pieza sistémica.
- **Nota (AUD-515, 2026-08-16):** dos de los tres «sin tocar» de la nota
  anterior resultaron estar mal diagnosticados, no bloqueados de verdad.
  **La reverberación real no necesitaba mezclador DSP:** todo el audio del
  proyecto ya se genera por código, así que se hornea en el propio `.wav`
  (`_aplicar_reverberacion`, ver la nota de [[GAP-058]]). **El mirador y la
  pausa contemplativa no necesitaban un sistema de cámara/pausa nuevo:**
  `CutsceneSystem` ya lo tenía, y ya se usaba en este mismo mapa para la
  introducción — sólo hacía falta un guión más (ver la nota de
  [[GAP-064]]). La pregunta (1), el eje horizontal/vertical, se confirmó
  directamente con el dueño (2026-08-16, ver las notas de [[GAP-059]] y
  [[GAP-061]]): AUD-467 se mantiene, no se reabre. Lo que de verdad sigue
  sin construirse, y por qué cada uno es un sistema aparte y no una
  llamada más: la mitad navegable de las osamentas de la Fase 3 (geometría
  sólida nueva — regenerar el mapa borraría el arte de `BG_Far`/`BG_Mid`);
  el secreto opcional de la Fase 6 (un objeto y un disparador nuevos, la
  misma limitación de regenerar el mapa); y la música/el sonido que se
  construyen progresivamente por capas (`DynamicMusicSystem` está pensado
  para intensidad de combate, no para revelar instrumentos con el avance
  narrativo, y este nivel no tiene combate).
- **Nota (AUD-518…523, 2026-08-17):** el sorteo entre tres variantes del
  slot de la Fase 4 —cementerio (AUD-518), fosa abisal acuática (AUD-519)
  y niebla aérea musical (AUD-520)— quedó completo y documentado
  (`docs/niveles/13b_STAGE_4_1B.md`, `13c_STAGE_4_1C.md`, AUD-521). Dos
  correcciones jugadas después de construir las tres: **(AUD-522)** el
  musgo/lodo de la Fase 2 (ver la nota de [[GAP-060]]) pasó de "una sola
  mecánica, dos intensidades imperceptibles" a dos mecánicas de verdad —
  el musgo resbala (`ZonaDeFriccion.inercia`, nueva), el lodo frena
  (`multiplicador`, sin cambios) — con pisada y partícula propias.
  **(AUD-523)** el checkpoint que brillaba opt-in sólo en 4.1b/4.1c
  (AUD-517) pasó a ser el checkpoint de los 26 escenarios: se retiró
  `assets/sprites/shared/checkpoint.png` y el rectángulo de respaldo —
  ya no hay dos caminos de dibujo para un solo resultado final. **(AUD-525,
  jugado tras un reporte de "no se ve el agua ni que nade el personaje" en
  4.1b)** dos huecos separados, no uno: el TMX nunca encendía
  `water_effect` — `ZonaDeAgua` (física: nado, oxígeno, corriente) y
  `WaterEffect` (lo que se ve) son componentes aparte a propósito
  (`water_effect.py`, AUD-111), y nadie había prendido el segundo, así que
  el nivel se jugaba sumergido y se veía seco. Y `SWIMMING` reutilizaba
  `player_jump.png` — cuatro copias del mismo fotograma quieto, cero
  brazada — ahora tiene `player_swim.png` propio, alternando una patada
  abierta con la silueta cerrada del salto. El pez abismal no tenía ningún
  defecto de código encontrado; queda por comprobar si el tinte de agua ya
  lo hace más visible por contraste.
