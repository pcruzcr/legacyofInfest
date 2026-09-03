# B4.3 — Recharge Station — Especificación

**ID:** LOI-FEAT-B4.3 · **Versión:** 1.0.0 · **Estado:** CERTIFIED
**Baseline:** `df16c614` + B4.1 + B4.2 — renderer `FROZEN`
**Fecha:** 2026-09-02

---

## 1. PURPOSE

Estación de recarga reutilizable que restaura recursos de combate
(estamina, medidor especial) sin curar vida ni fijar checkpoint. Complementa a
`Fogata` (cura+checkpoint) y `Heart Piece` (vida máxima): el jugador que
agota su `dash` o su `ultimate` vuelve a la estación para recuperarlos.
No es ítem coleccionable, no entra en `map_item_collected` (B3).

## 2. OBJECT TYPE

| Tipo TMX | Clase runtime | Archivo | Registro |
|---|---|---|---|
| `RechargeStation` | `EstacionDeRecarga` | `interactables.py` | `@register("RechargeStation")` |
| `EstacionRecarga` | `EstacionDeRecarga` (alias) | mismo | `@register("EstacionRecarga")` |
| `EstacionDeRecarga` | `EstacionDeRecarga` (alias) | mismo | `@register("EstacionDeRecarga")` |

Tres alias por legibilidad (inglés/español). Misma clase, mismo handler.

## 3. TMX CONTRACT

Objeto en capa `Objects`:

```
type = RechargeStation (o EstacionRecarga)
x,y,w,h → rect (mínimo TILE_SIZE)
properties: mensaje="Estación — pulsa para recargar" (opcional)
```

Ejemplo:

```
Object id=77 type=RechargeStation x=320 y=400 w=32 h=32
  properties: mensaje="Fuente de energía"
```

Sin `heal_amount`/`checkpoint_id` configurables: restaura a máximo
(estamina → max, especial → max). Si diseño pide cantidad parcial,
añadir prop `amount` en futuro lote.

## 4. PROPERTIES

| Prop | Tipo | Default | Nota |
|---|---|---|---|
| `mensaje` | string | `"Estación — pulsa para recargar"` | Hint + mensaje al usar |

Rect se toma vía `_rect_de` (mínimo `TILE_SIZE` si es punto).

## 5. HEAL / RECHARGE

- **Recarga:** `estamina = estamina_max`, `_espera_estamina_restante = 0`,
  `special_meter = special_meter_max` (si existen en `Player`).
- **Vía:** `InteractableSystem._usar_estacion` con `player_ref` directo;
  también emite `RECHARGE_STATION_USED` + `SFX_CHECKPOINT` para feedback.
- **No cura vida:** no emite `PLAYER_HEALED`. Vida sólo la cura `Fogata`.
- **Cap:** `min(recharge, max)` — si ya está al máximo, se mantiene al máximo
  (no overheal). `estamina 90/100 → 100`, `90/100 special →100`.

## 6. CHECKPOINT

No. `RechargeStation` **no** emite `CHECKPOINT_REACHED`. Es sólo recarga.
Si el diseñador quiere checkpoint + recarga, coloca `Fogata` y
`RechargeStation` adyacentes o usa `Fogata` sola (que ya cura).

## 7. REUSE

Reutilizable infinito, como `Fogata`:

```
activate → recharge → usada=True → activate again → recharge → ...
```

`usada` se pone a `True` pero no bloquea reuse (no se comprueba antes de
permitir). 3× seguidas las 3 recargan.

## 8. PERSISTENCE

- **Estación no persiste `used`:** al recargar mapa se crea nueva
  `EstacionDeRecarga` con `usada=False`. No hay campo en `SaveData`.
- **Recursos del jugador no persisten vía estación:** la recarga es en memoria
  (player). El guardado de `estamina` es vía `SaveData`? No, `estamina` es
  runtime, no se guarda; al cargar vuelve a `max`. Por eso estación no necesita
  save duplicado (test `does_not_create_save_state`).

## 9. AUDIO & FEEDBACK

- **Evento:** `RECHARGE_STATION_USED` con `pos=rect.center`
- **SFX:** `SFX_CHECKPOINT` (reuso, mismo que Fogata) para no crear nuevo asset
- **Mensaje:** `"Recargado — recursos restaurados!"` al usar, hint
  `estacion.mensaje` 1s si cerca sin pulsar (vía `_avisar` → `SHOW_MESSAGE`).

## 10. EDGE CASES

| Caso | Comportamiento |
|---|---|
| `far (>24) + usar` | no activa |
| `near + no usar` | sólo hint, no recarga |
| `already full` | recarga a max (no overheal) |
| `multiple stations` | break tras primera que alcanza |
| `map reload` | nueva estación `usada=False` |
| `death/respawn` | estación sigue usable |
| `save/load` | no crea `map_item_collected` |

## 11. B3 COMPATIBILITY

- `EstacionDeRecarga` no es `ITEM` → excluida de `StageData.item_total()`
  (filtra sólo `Recogible`/`Cofre`/`SecretRoom`). Con sólo estaciones,
  `item_total 0 → None` → HUD porcentaje oculto.
- Regresión: `test_recharge_station_not_counted_as_item`.

## 12. TESTS

`tests/test_recharge_station.py` — 11 tests:

```
test_is_registered, is_loaded_from_tmx, alias,
can_be_used, is_reusable, restores_stamina, does_not_overheal,
not_counted_as_item, does_not_create_save_state,
interaction_conditions, tmx_integration_via_stage_data
```

## 13. PLAYTEST

- **GAMEPLAY:** `ENTER → FIND STATION (100,100) → NEAR+usar → estamina 20→100, special 10→100, RECHARGE event → MOVE AWAY far no recharge → RETURN reusable → DIE→RESPAWN still usable` — PASS headless
- **VISUAL:** 1280/1920 — rect invisible, mensaje no rompe HUD, no renderer touch

## 14. ACCEPTANCE

```
REGISTRATION PASS, TMX LOAD PASS, RUNTIME PASS, HEAL/RECHARGE PASS,
HEALTH CAP PASS (no overheal), REUSABLE PASS, B3 EXCLUSION PASS,
SAVE/LOAD N/A (no duplicate), TESTS 11/11 PASS, PLAYTEST PASS, REGRESSION PASS
```

---

## Implementación

- `interactables.py` `EstacionDeRecarga` dataclass
- `stage_data.py` `estaciones_recarga: list[EstacionDeRecarga]`
- `stage_objetos.py` `_handle_estacion_recarga` (3 alias)
- `interactable_system.py` `estaciones_recarga` + `_usar_estacion` + `set_player_ref`
- `stage_scene.py` `InteracTableSystem(estaciones_recarga=...)` + `set_player_ref`
- `events.py` `RECHARGE_STATION_USED`
- No se tocó `SaveData`, `NG+`, `Zone4`, `renderer`, `B3`

Si diseño pide `heal_amount` parcial o checkpoint, añadir prop y
documentar en §4 sin romper default `max`.
