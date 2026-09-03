# B4.1 — Bonfire / Fogata — Especificación

**ID:** LOI-FEAT-B4.1 · **Versión:** 1.0.0 · **Estado:** CERTIFIED
**Baseline:** `df16c614 AUD-805` + B2 COMPLETE + B3 COMPLETE — renderer `FROZEN`, Zone4 HOLD
**Fecha:** 2026-09-02

---

## 1. PURPOSE

Fogata es un interactuable **reutilizable** que el diseñador coloca en TMX
para ofrecer curación y checkpoint sin escribir Python. Inspirado en
Dark Souls / Hollow Knight: el jugador se acerca, pulsa usar, recupera vida
y fija su punto de reaparición. No es un ítem coleccionable y no entra en
`map_item_collected` (B3).

---

## 2. OBJECT TYPE

| Tipo TMX | Clase runtime | Archivo | Registro |
|---|---|---|---|
| `Fogata` | `Fogata` | `src/framework/stage/interactables.py:162` | `@register("Fogata")` `stage_objetos.py:762` |
| `Bonfire` | `Fogata` (alias) | mismo | `@register("Bonfire")` |

Ambos nombres resuelven al mismo handler `_handle_fogata` — no hay dos
nomenclaturas distintas, es alias por legibilidad (Fogata en español,
Bonfire para quien sigue tutoriales en inglés).

---

## 3. TMX CONTRACT

Un objeto en la capa `Objects` con:

```
type = Fogata  (o Bonfire)
x, y, width, height  → Fogata.rect (mínimo TILE_SIZE si es punto)
```

Propiedades (todas opcionales):

| Propiedad | Tipo | Default | Significado |
|---|---|---|---|
| `mensaje` | string | `"Fogata — pulsa para descansar (cura y guarda)"` | Texto hint cuando el jugador está cerca sin pulsar, y mensaje al usar |
| — | — | — | No hay `heal_amount`, `checkpoint_id`, `sound` configurables: son regla global |

Ejemplo Tiled:

```
Object type=Fogata  x=640 y=480 w=32 h=32
  properties: mensaje="Descanso del bosque"
```

Si no se declara `mensaje`, usa el default de `Fogata.mensaje`.

---

## 4. PROPERTIES — Mapping TMX → Loader → Runtime

```
TMX Fogata (x,y,w,h, mensaje)
  → stage_objetos._handle_fogata (stage_objetos.py:762)
      rect = _rect_de(obj)  # mínimo TILE_SIZE
      mensaje = props.get("mensaje", "Fogata — pulsa para descansar")
      stage.fogatas.append(Fogata(rect, mensaje))
  → StageData.fogatas: list[Fogata] (stage_data.py:474)
  → StageScene.on_enter: InteractableSystem(fogatas=stage_data.fogatas, bus=...) + set_persistencia(stage_id, save_manager)
```

No hay `tmx_object_id` para Bonfire (no es ITEM, no necesita persistencia
per-map). `Fogata.usada` es estado de sesión, no se guarda en `SaveData`.

---

## 5. HEAL

- **Evento:** `PLAYER_HEALED` con `amount = 5.0` (`interactable_system.py:512`)
- **Regla global:** `5.0` es default fijo, no propiedad TMX. No introducir
  configuración global innecesaria.
- **Health cap:** la curación respeta `player.max_health` — `min(requested, missing)`
  (`Player`/`HUD` clamp). Fogata siempre emite `5.0`; el receptor recorta.
- **Casos:**
  - `health < max` → `healed = min(5.0, max - health)`
  - `health == max` → `healed = 0` pero igual emite checkpoint/mensaje (no se
    bloquea por estar lleno)

---

## 6. CHECKPOINT

- **Evento:** `CHECKPOINT_REACHED` con `checkpoint_id = "fogata"` (`interactable_system.py:513`)
- **Semántica:** establece respawn en esa fogata. `StageScene`/`Progression`
  escuchan `CHECKPOINT_REACHED` y actualizan `checkpoint_position`. No es un
  `Checkpoint` entidad con `checkpoint_id:int` (haz de luz) — es un checkpoint
  lógico reutilizable.
- **Tipo:** `checkpoint_id` es `str` `"fogata"`, no `int`. El sistema de
  checkpoints acepta ambos (StageScene lo trata como evento, no como id
  numérico de TMX). No convertir a `int` ni introducir strings arbitrarios
  fuera de este contrato.
- **No implica save automático:** `checkpoint ≠ save`. La fogata emite
  checkpoint pero no llama a `SaveManager.save()` automáticamente. El guardado
  ocurre vía `auto_save` en `SceneManager` o explícito `SaveManager.save()`.
  Separar checkpoint y save evita guardados silenciosos.

---

## 7. REUSE

- **Reutilizable infinito:** `Fogata.usada` se pone a `True` al usar, pero
  `_usar_fogata` **no** comprueba `usada` para bloquear — sólo para hint.
  Secuencia:
  ```
  activate → heal 5.0 + checkpoint fogata + SFX → usada=True
  → activate again → heal + checkpoint → ...
  ```
- **Prueba:** `test_bonfire_is_reusable` activa 3 veces seguidas, las 3 emiten
  `PLAYER_HEALED` y `CHECKPOINT_REACHED`.

---

## 8. PERSISTENCE

- **Fogata no persiste `used`:** al recargar el mapa (`StageLoader.load` →
  `StageScene.on_enter`) se crea `Fogata` nueva con `usada=False`. No hay
  campo en `SaveData` para `fogatas`.
- **Checkpoint sí puede persistir vía SaveData si el sistema de checkpoints
  guarda `checkpoint_x/y` en `auto_save` — pero eso es responsabilidad de
  `SaveManager`, no de la fogata. La fogata no crea estado de save duplicado
  (ver `test_bonfire_does_not_create_duplicate_save_state`).

---

## 9. AUDIO & FEEDBACK

- **Sonido:** `SFX_CHECKPOINT` con `pos = fogata.rect.center` (`interactable_system.py:516`)
  — mismo bus que los checkpoints de haz de luz.
- **Mensaje:** al usar → `"Descansando en la fogata... ¡Vida restaurada!"` (`:511`);
  al estar cerca sin pulsar → `fogata.mensaje` durante 1 s (`:523`);
  también emite `SHOW_MESSAGE` vía `InteractableSystem._avisar` → `MessageBox`.
- **Visual:** la fogata no tiene sprite propio en esta fase; es rect invisible
  con mensaje. No añade UI nueva.

---

## 10. EDGE CASES

| Caso | Comportamiento |
|---|---|
| `player far` (> ALCANCE 24) + usar | no activa, no emite |
| `player near` + no usar | sólo hint `fogata.mensaje` 1 s, no heal/checkpoint |
| `dead` / `menu open` / `cutscene` | `InteractableSystem.update` no se llama (pausado), no activa |
| `already full health` | igual emite heal 5.0 + checkpoint (no bloquea) → receptor recorta a max |
| `multiple fogatas` | `break` tras la primera que alcanza → sólo una por pulsación |
| `map reload` (salir y volver) | nueva `Fogata` con `usada=False`, checkpoint previo sigue en `SaveData` si se guardó |
| `death → respawn` | respawn en última fogata si checkpoint fue `fogata`; fogata sigue usable |
| `save/load` | no añade `map_item_collected`, total B3 no incrementa |

---

## 11. B3 COMPATIBILITY

- `Fogata` **no** es `ITEM` → excluida de `StageData.item_total()` y
  `item_percentage()` (`stage_data.py:item_keys` filtra sólo
  `Recogible`/`Cofre`/`SecretRoom` con `tmx_object_id!=0`).
- `stage_data.item_total()` con sólo fogatas → `0` → `None` → HUD oculta
  porcentaje (no muestra `0%` falso).
- Regresión explícita: `test_bonfire_not_counted_as_item` y colateral
  `test_bonfire_does_not_create_duplicate_save_state`.

---

## 12. TESTS

`tests/test_bonfire.py` — 14 tests:

```
test_bonfire_is_registered
test_bonfire_is_loaded_from_tmx
test_bonfire_is_loaded_from_tmx_via_bonfire_type
test_bonfire_can_be_used
test_bonfire_is_reusable
test_bonfire_heals_player (5.0)
test_bonfire_does_not_overheal (cap max)
test_bonfire_sets_checkpoint (id fogata)
test_bonfire_not_counted_as_item (B3 exclusion)
test_bonfire_does_not_create_duplicate_save_state
test_bonfire_checkpoint_survives_save_load
test_bonfire_respawn
test_bonfire_interaction_conditions (far/near, usar true/false)
test_bonfire_tmx_integration_via_stage_data
```

---

## 13. PLAYTEST

- **GAMEPLAY:** `ENTER MAP → FIND BONFIRE (Rect 100,100 32x32) → NEAR + usar → heal 5.0 + checkpoint fogata + SFX → move away → damage → return → usar again → reusable → DIE → RESPAWN at fogata` — PASS headless dummy
- **VISUAL:** 1280×720 y 1920×1080 — fogata rect invisible, mensaje no rompe HUD, cámara/viewport/scaling intactos (no toca renderer)
- **MAP RELOAD:** salir y volver recrea fogata con `usada=False` pero checkpoint previo persiste en save si se guardó

---

## 14. ACCEPTANCE

```
FOGATA CLASS PASS (interactables.py:162)
TMX REGISTRATION PASS (stage_objetos.py:762 Fogata/Bonfire)
TMX LOAD PASS (_handle_fogata → StageData.fogatas)
RUNTIME PASS (_usar_fogata alcanza+usar → heal+checkpoint)
HEAL PASS (5.0, test_bonfire_heals_player)
HEALTH CAP PASS (min heal, test_does_not_overheal)
CHECKPOINT PASS (id fogata, test_sets_checkpoint)
REUSABLE PASS (3×, test_is_reusable)
DEATH/RESPAWN PASS (respawn usable)
SAVE/LOAD N/A (fogata no persiste, checkpoint via SaveManager — test_checkpoint_survives)
B3 ITEM EXCLUSION PASS (item_total 0)
TESTS 14/14 PASS
PLAYTEST PASS
REGRESSION PASS
```

---

## 15. IMPLEMENTATION

No se modificó lógica de curación/checkpoint — infraestructura ya completa.
Cambios B4.1 sólo para certificar y documentar:

- `tests/test_bonfire.py` (nuevo, 14 tests)
- `docs/features/bonfire.md` (este fichero)
- No se tocó: `difficulty`, `save_data NG+`, `player`, `enemy`, `render`, `Zone4`, `B3`

Si diseño pide `heal_amount` configurable por TMX, añadir prop
`heal_amount` en `Fogata` y `stage_objetos._handle_fogata` en futuro lote
(mínimo cambio, sin romper default 5.0).

