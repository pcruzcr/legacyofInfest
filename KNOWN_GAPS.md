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

## [GAP-022] `requirements.lock` no se puede instalar en Python 3.13

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

## [GAP-021] Números de documento duplicados en `docs/`

- **File:** `docs/00_MASTER_INDEX.md`
- **Phase:** auditoría 2026-08-02, iteración 1
- **Reason:** Los prefijos 28, 29, 30, 31, 32, 33, 34, 52 y 67 los usan dos
  ficheros distintos cada uno (`28_DECISION_LOG.md` y `28_SAMPLE_SYLLABUS.md`,
  `67_CURVA_DE_DIFICULTAD.md` y `67_ESPECIFICACION_DE_NIVELES_Y_JEFES.md`…).
  El índice se refiere a los documentos por número, así que «el 67» es
  ambiguo.
- **Resolution:** No se renumeró a propósito: las referencias cruzadas del
  material del curso citan los números, y renumerar rompe todas a la vez. La
  decisión —renumerar de golpe o pasar a citar por nombre de fichero— es de
  quien mantiene el temario.

## [GAP-002] Collision rect depth usada para X-skip heurística

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

## [GAP-015] StageScene sin descomposición — monolito de 1200+ líneas

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


