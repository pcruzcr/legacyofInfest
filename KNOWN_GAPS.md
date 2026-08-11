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



## ~~[GAP-024] El calificador mide el salto con una fórmula que el motor no cumple~~ *(Resuelto por decisión)*

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

## [GAP-048] Sin streaming de niveles ni versionado de mapas

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
