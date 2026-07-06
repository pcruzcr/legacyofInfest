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

## [GAP-004] `background_zone` implementado en StageLoader pero ausente en Stage 0 TMX

- **File:** `src/framework/stage/stage_loader.py` (línea 112)
- **Phase:** 4
- **Reason:** `StageLoader.load()` lee `background_zone` del TMX y carga fondos
  parallax desde `assets/backgrounds/{zone}/`. El Stage 0 TMX no tiene esta
  propiedad, por lo que corre sin fondos parallax (usa solo capas de tiles).
- **Resolution:** Agregar `background_zone` al TMX de Stage 0 cuando los assets
  de fondo definitivos estén listos. El soporte en StageLoader ya existe.

## [GAP-005] Colisión Y-primero causa wall-climb/teleport

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

## [GAP-006] PlayerStates referencia `_pending_jump` sin atributo en Player

- **File:** `src/framework/entities/player_states.py`, `player.py`
- **Phase:** FIX-4
- **Reason:** `_airborne_update` asigna `player._pending_jump = True` y
  `player._pending_jump_timer`, pero estos atributos no existían en `Player.__init__`.
  Funcionaba por Python dinámico, pero violaba la explícitud del contrato.
- **Resolution:** Se agregaron `_pending_jump: bool = False` y
  `_pending_jump_timer: float = 0.0` a `Player.__init__`. El timer de 8 frames
  (≈133ms) evita bounce-off en plataformas one-way al amortiguar el input de salto.

## [GAP-007] StageLoader spawn point: TMX Y=feet convertido como top-left

- **File:** `src/framework/stage/stage_loader.py`
- **Phase:** FIX-5
- **Reason:** TMX §6.1 especifica que Y del PlayerSpawn = posición de los PIES,
  pero `StageLoader` leía `pygame.Vector2(obj.x, obj.y)` tratándolo como top-left.
  El bug de colisión Y-primero (GAP-005) enmascaraba esto al teleportear al
  jugador hacia arriba. Con la colisión axis-separada, el jugador nacía 32px
  dentro del piso y caía al vacío.
- **Resolution:** Se cambió a `pygame.Vector2(obj.x, obj.y - 32)`. El test
  `test_spawn_point_matches_tmx` se actualizó de `y=176` a `y=144`.

## [GAP-008] Timer HUD usa TTF font, no spritesheet de píxeles

- **File:** `docs/09_HUD_SPEC.md`, `src/engine/ui/hud.py`
- **Phase:** Documentación
- **Reason:** El HUD renderiza el timer con `pygame.font.Font("PixeloidSans.ttf")`,
  pero la especificación §5.4 documentaba un spritesheet `fonts/hud_digits.png`.
  El TTF produce mejor calidad a costa de no usar el sprite pipeline.
- **Resolution:** Se actualizó `09_HUD_SPEC.md` §5.2 y §5.4 para reflejar el uso
  de TTF font, posición ajustada a X=264, Y=24, ancho 54px.

## [GAP-009] MessageBox reposicionado de Y=196 (abajo) a Y=0 (arriba)

- **File:** `docs/09_HUD_SPEC.md`, `src/engine/ui/message_box.py`
- **Phase:** UI Fix
- **Reason:** El mensaje tutorial se movió de la parte inferior de la pantalla
  (Y=196) a la superior (Y=0) para evitar solapamiento con el HUD de salud/timer.
- **Resolution:** Se actualizó `09_HUD_SPEC.md` §2, §2.1, §7.2 con la nueva
  posición y layout. Los elementos del HUD (portrait, hearts, timer) se
  desplazaron 14px hacia abajo (Y=16 base).

## [GAP-010] Action enum documentado como str, Enum pero implementado como Enum simple

- **File:** `docs/22_API_CONTRACTS.md`, `src/engine/input/action_map.py`
- **Phase:** Documentación
- **Reason:** El contrato API declaraba `class Action(str, Enum)` con miembros
  string, pero la implementación usa `class Action(Enum)` con `auto()`. Además
  el contrato omitía los miembros MOVE_UP, MOVE_DOWN, DASH, y nombraba
  `DEFAULT_KEYBOARD_BINDINGS` en vez de `DEFAULT_KEY_BINDINGS`.
- **Resolution:** Se actualizó `22_API_CONTRACTS.md` §3.1 para reflejar la firma
  real.

## [GAP-011] SoundBank API incompleta en contrato

- **File:** `docs/22_API_CONTRACTS.md`, `src/engine/audio/sound_bank.py`
- **Phase:** Documentación
- **Reason:** El contrato API sólo documentaba `__init__(asset_loader)` y
  `get(name) -> Sound`. La implementación tiene `load_all()`, `load(name, path)`,
  `play(name, loops, volume)`, y `get` retorna `Sound | None`.
- **Resolution:** Se actualizó `22_API_CONTRACTS.md` §4.1 con todos los métodos
  y tipos correctos.

## [GAP-012] AssetLoader.load_image parámetros faltantes en contrato

- **File:** `docs/22_API_CONTRACTS.md`, `src/engine/utils/asset_loader.py`
- **Phase:** Documentación
- **Reason:** El contrato declaraba `load_image(path) -> Surface` sin los
  parámetros `scale`, `size`, `alpha` que la implementación soporta.
- **Resolution:** Se actualizó `22_API_CONTRACTS.md` §5.2 con la firma completa.


