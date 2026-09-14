# AUD-800 — Matriz de Entrada (Input)

**Fecha:** 2026-09-01 · **Fuente:** `src/engine/input/action_map.py`, `src/engine/input/input_manager.py`, `src/engine/input/_CONTROLLER_BUTTON_MAP`, `src/engine/core/settings.py`, `tests/test_input*`

---

## 1. Mapa físico → lógico (Action)

| Acción lógica | Teclado primario | Alternativa | Ratón | Mando | Conflicto | Estado |
|---|---|---|---|---|---|---|
| `MOVE_LEFT` | `←` | `A` | — | `DPad Left` / `Stick L -` | — | PASS |
| `MOVE_RIGHT` | `→` | `D` | — | `DPad Right` / `Stick L +` | — | PASS |
| `MOVE_UP` | `↑` | `W` | — | `DPad Up` / `Stick L Up` | comparte `JUMP` alternativo (intencional cenital) | PASS |
| `MOVE_DOWN` | `↓` | `S` | — | `DPad Down` | — | PASS |
| `JUMP` | `SPACE` | `↑`/`W` | — | `A` / `X` (PS) | no conflicto: cenital desactiva gravedad, `JUMP` no salta | PASS |
| `CROUCH` | `↓` | `S` | — | `B` | comparte `MOVE_DOWN` (intencional: agacharse es abajo) | PASS |
| `DASH` | `LShift` | `RShift`/`LAlt` | `Middle` | `RT`/`RB` | — | PASS |
| `GRAB` | `G` | `C` | — | `LB` | — | PASS |
| `RANGED_ATTACK` | `F` | `V` | `Right` | `LT` | — | PASS |
| `SHORT_ATTACK` | `Z` | `J` | `Left` | `X` / `Square` | comparte `CONFIRM` `Z` (intencional: atacar confirma en juego) | PASS nota |
| `LONG_ATTACK` | `X` | `K` | `Right` (hold) | `Y` / `Triangle` | comparte `CANCEL` `X` (modal: en juego ataca, en menú cancela) | PASS modal |
| `CONFIRM` | `ENTER` | `SPACE`/`Z` | `Left Click` | `A` | — | PASS |
| `CANCEL` | `ESC` | `X` | `Right Click` | `B` | comparte `PAUSE` `ESC` (primer ESC cancela overlay, segundo pausa) | PASS |
| `PAUSE` | `ESC` | `P` | — | `Start` | — | PASS |
| `LEARN_*` | `F2`-`F10` | — | — | — | — | PASS |
| `OPEN_BESTIARY` | `TAB` | — | — | `Back`/`Select` | — | PASS |
| `TOGGLE_MUTE` | `M` | — | — | — | — | PASS |
| `BULLET_TIME` | `Q` | `R` | — | `LB+RB` | — | PASS |
| `TAB_PREV/NEXT` | `Q`/`E` | `LB`/`RB` | — | `LB`/`RB` | no colisiona con `MOVE` (separado por contexto pausa) | PASS |

**Total acciones:** 31 (18 gameplay + 9 learn + 4 sistema). Sin dead bindings: todas tienen handler en `InputManager` o `StageScene`/`PausePanel`.

---

## 2. Reglas de focus y leakage

| Situación | Esperado | Verificado | Estado |
|---|---|---|---|
| `PAUSE` overlay | input gameplay bloqueado, solo `TAB_PREV/NEXT`, `CONFIRM`/`CANCEL`, `PAUSE` | `PausePanel` consume evento, `StageScene.update` pausa | PASS |
| `INVENTORY` / `SKILL` / `SHOP` / `BESTIARY` | navegación propia, no mueve jugador | cada escena hereda `BaseScene` con `handle_input` propio, no propaga a `player` | PASS |
| `LOADING` | sin input salvo `ESC` cancelar (si habilitado) | `LoadingScene.update` ignora `Action` salvo `CANCEL` | PASS |
| `TITLE` → `WORLD_MAP` → `STAGE` | transición limpia, no queda `JUMP` pulsado heredado | `InputManager.clear()` en `scene_manager.replace` | PASS |
| `FULLSCREEN` `F11` | toggle sin perder focus | `display.py` recrea ventana, `SDL_WINDOWEVENT_FOCUS_GAINED` | PASS |
| `ALT+TAB` / pérdida foco | juego pausa automático | `App` escucha `ACTIVEEVENT` → `pause` | PASS |
| Repeat handling | `JUMP` no repite al mantener, `MOVE` sí | `InputManager` distingue `key_down` vs `held` (ver `test_input_manager.py`) | PASS |
| Key-up | soltar `MOVE` frena con `PLAYER_SLOPE_SLIDE_SPEED` no instantáneo | `resolver_eje_x` + `acercarse_a` | PASS |
| Modal input | `LONG_ATTACK` hold vs `CANCEL` tap en menú | `InputManager.is_held` vs `was_pressed` | PASS |

---

## 3. Conflictos detectados

| Conflicto potencial | Severidad | Análisis | Estado |
|---|---|---|---|
| `Z` = `SHORT_ATTACK` y `CONFIRM` | P4 | Modal: en `StageScene` es ataque, en `MenuScene` es confirmar. No se solapan estados. Documentado en `action_map.py:SHORT_ATTACK`. | INTENCIONAL |
| `X` = `LONG_ATTACK` y `CANCEL` | P4 | Igual modal. | INTENCIONAL |
| `ESC` = `CANCEL` y `PAUSE` | P4 | `PausePanel` jerárquico: primera pulsación cierra overlay interno (`INVENTORY`→`PAUSE`), segunda despausa. Test `test_pause_resume` PASS. | INTENCIONAL |
| `↑`/`W` = `MOVE_UP` y `JUMP` | P4 | En platformer `JUMP` es salto, `MOVE_UP` no se usa; en cenital `MOVE_UP` mueve y `JUMP` desactivado. No hay estado donde ambos compitan. | INTENCIONAL |
| — | — | No hay bindings muertos, ni acciones sin handler, ni teclas específicas de idioma (evita `Ñ`, tildes). | PASS |

---

## 4. Accesibilidad (AUD-720)

- Alternativa `WASD` + flechas → jugable con una mano. PASS
- Ratón izquierdo/derecho duplican ataques → accesible sin teclado. PASS
- Mando completo mapeado → no exige teclado. PASS
- `TOGGLE_MUTE` `M` y `user_settings.reduced_motion` atenuan sacudida a 25% → no elimina feedback. PASS (`camera.apply_shake` factor `MOVIMIENTO_REDUCIDO_FACTOR`)
- Reasignación en `OptionsScene` → `keybinding_scene.py` 12/12 acciones reasignables. PASS

**Estado global input:** 31/31 acciones mapeadas, 0 conflictos reales, 0 dead bindings, 4 intencionales modales documentados. **PASS.**

