# PHASE FIX REPORT — Legacy of InFest

**Date:** 2026-07-01
**Commit:** `de324f6`
**Test Status:** 307 passed, 0 failed

---

## FIX-1: Colisión de Stage 0

| Item | Detalle |
|------|---------|
| **Archivo** | `tools/generate_stage0_tmx.py` |
| **Problema** | La colisión se definía por tiles individuales (48 rectos separados), generando gaps en TMX |
| **Solución** | `_gen_collision_rects()` fusiona tiles sólidos contiguos → 33 merged rects, 0 gaps |
| **Layer** | Collision layer independiente del Objects layer |
| **Verificación** | `generate_stage0_tmx.py:51-75` — bucle de merge horizontal por fila |

---

## FIX-2: Truncamiento de posición

| Item | Detalle |
|------|---------|
| **Archivo** | `src/framework/entities/player.py` |
| **Problema** | `position.x/y` se truncaba a `int` en cada frame aunque no hubiera colisión |
| **Solución** | Flags `collided_x` / `collided_y` controlan el snap; floor tiles se saltan en X |
| **Heurística X-skip** | `tile.top >= player_rect.centery` → saltar rectos de piso durante resolución X |
| **Push direction** | Comparación de overlap (left vs right) en vez de dirección de velocidad |
| **Verificación** | `test_floor_x_skip.py:test_floor_does_not_block_x_movement` ✓ |

---

## FIX-3: Spawn point desalineado

| Item | Detalle |
|------|---------|
| **Archivo** | `tools/generate_stage0_tmx.py:81` |
| **Problema** | PlayerSpawn en y=192 → rect.bottom=224, 32px por debajo del piso |
| **Solución** | y=160 (floor_y - player_height = 192 - 32) |
| **Verificación** | `test_spawn_no_pop.py:test_feet_align_with_floor_after_landing` ✓ |

---

## FIX-4: Crash en PatternDemoScene

| Item | Detalle |
|------|---------|
| **Archivo** | `src/engine/scenes/pattern_demo_scene.py:237` |
| **Problema** | `PANEL_W` → no definido; debía ser `RIGHT_PANEL_W` |
| **Solución** | Renombrado a `RIGHT_PANEL_W` |

---

## FIX-5: Deuda de tests

| Item | Detalle |
|------|---------|
| **Archivo** | `tests/test_input_manager.py`, `tests/test_player_state_machine.py` |
| **Problema** | Usaban `is_pressed()`/`is_held()` (API antigua), no `is_action_pressed()`/`is_action_held()` |
| **Solución** | Actualizados a la nueva API; `input_manager` inyectado como 3er arg |
| **Verificación** | `test_input_injection.py` ✓ |

---

## FIX-6: Limpieza flake8 / ruff

| Item | Detalle |
|------|---------|
| **Auto-fix** | 54 correcciones (F401 imports no usados, W292 trailing newlines) |
| **Manual** | `l→lightness` en color_tools.py; `l→layer` en stage_loader.py; `__all__` en processing/__init__.py |

---

## Bug Adicional: _update_rect_size cancelaba gravedad

| Item | Detalle |
|------|---------|
| **Archivo** | `src/framework/entities/player.py:628` |
| **Problema** | `old_bottom = self.rect.bottom` usaba `self.rect.y` (truncado) en vez de `self.position.y` (precisión completa) |
| **Efecto** | La corrección de `_update_rect_size` cancelaba el avance fraccional de la gravedad cada frame |
| **Solución** | `old_bottom = self.position.y + self.rect.height` |
| **Verificación** | `test_collision_edge_detect.py:test_collided_y_only_snaps_when_collision_occurs` ✓ |

---

## Tests de Regresión Agregados

| Archivo | Propósito | Tests |
|---------|-----------|-------|
| `tests/test_floor_x_skip.py` | FIX-1/FIX-2: Floor tiles no bloquean X | 3 |
| `tests/test_spawn_no_pop.py` | FIX-3: Spawn y=160, sin pop | 3 |
| `tests/test_collision_edge_detect.py` | FIX-2: Inflated rect detecta edge overlaps | 3 |
| `tests/test_input_injection.py` | FIX-5: Input injection funciona | 3 |

**Total tests:** 295 → 307 (+12)
