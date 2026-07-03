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

## [GAP-003] SoundBank no conectado — sin llamadas a `play_sfx()`

- **File:** Todo el codebase
- **Phase:** 3
- **Reason:** `SoundBank` fue implementado en `src/engine/audio/sound_bank.py` pero
  nunca se invoca `sound_bank.load()` ni `play_sfx()` en ningún Scene o Entity.
  Los nombres de SFX en `ASSET_BIBLE.md` §12 fueron limpiados contra disco pero
  no hay código que los reproduzca.
- **Resolution:** Pendiente — requiere integración con EventBus (escuchar
  `PLAYER_DAMAGED`, `ENEMY_DIED`, etc.) o llamadas manuales en stages/bosses.
  Marcar como baja prioridad hasta Fase 14+.

## [GAP-004] `background_zone` implementado en StageLoader pero ausente en Stage 0 TMX

- **File:** `src/framework/stage/stage_loader.py` (línea 112)
- **Phase:** 4
- **Reason:** `StageLoader.load()` lee `background_zone` del TMX y carga fondos
  parallax desde `assets/backgrounds/{zone}/`. El Stage 0 TMX no tiene esta
  propiedad, por lo que corre sin fondos parallax (usa solo capas de tiles).
- **Resolution:** Agregar `background_zone` al TMX de Stage 0 cuando los assets
  de fondo definitivos estén listos. El soporte en StageLoader ya existe.


