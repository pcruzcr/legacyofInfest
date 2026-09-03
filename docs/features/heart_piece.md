# Heart Piece — Implementación & Certificación B4.2

**ID:** LOI-FEAT-B4.2 · **Versión:** 1.0.0 · **Estado:** CERTIFIED (Modelo A — 0 cambios de lógica)
**Baseline:** `df16c614` + B2 + B3 + B4.1 — renderer `FROZEN`
**Fecha:** 2026-09-02

---

## 1. Modelo funcional

Heart Piece es `1/4` de corazón. Cada pieza es `collectible` (B3 `1 ITEM`),
recurso de inventario (`heart_piece` count) y fragmento de vida (`+0.25 max HP`)
y a la vez ingrediente de crafteo (`4 → heart_vessel`). Modelo A verificado:
no se creó arquitectura paralela, se reutiliza `Pickup` + `Inventory` + `crafting`.

## 2. TMX representation

```xml
<object id="42" type="Pickup" x="..." y="...">
  <property name="item_id" value="heart_piece"/>
</object>
```

`type=Pickup` (alias `Key`), `item_id=heart_piece`, `tmx_object_id=42`
automático de Tiled. No se creó `type=HeartPiece`. Cada objeto TMX = `1 ITEM`
(B3 `item_total` cuenta objetos, no `cantidad`). Recomendado `cantidad=1`.

## 3. B3 semantics

- `Recogible(item_id=heart_piece, tmx_object_id=N)` → `es_item_coleccionable_recogible`
  (`interactables.py:385`) → entra en `StageData.item_total()`
  (`stage_data.py:575`).
- 4 HeartPieces físicos = `4 ITEMS` (no 1, no 5 con vessel). `heart_vessel`
  no es collectible de mapa, no entra en `item_total`.

## 4. inventory representation

- `Inventory._items["heart_piece"] = count` entero (`inventory.py:192`,
  `collect()` + `count()`).
- `ItemDef heart_piece max_hp_bonus=0.25` (`inventory.py:195`).
- `get_total_hp_bonus()` suma `0.25*count + heart_vessel*1.0`
  (`inventory.py:292`).

## 5. max health formula

`Player.max_health` `player.py:458` = `PLAYER_MAX_HEALTH + bonus`,
`bonus = get_total_hp_bonus()` (`player.py:540`).

```
0 piezas → +0.00 → 5.00
1 → +0.25 → 5.25
2 → +0.50 → 5.50
3 → +0.75 → 5.75
4 → +1.00 → 6.00
5 → +1.25 → 6.25
8 → +2.00 → 7.00
```

## 6. current health behavior

Al aumentar `max_health`:

```python
gained = new_max - prev_max
health = min(new_max, health + gained)  # player.py:556-558
```

Ejemplo `3/5 → recoger → 3.25/5.25`, `5/5 → 5.25/5.25`. No full heal, no
unchanged, no overheal.

## 7. 4→1 crafting

Receta `heart_vessel: {heart_piece:4}` (`crafting.py:19`), manual
`puede_craftear`/`craftear` consumen 4 y `collect("heart_vessel",1)`.

```
5 piezas → consume 4 → queda 1 + 1 vessel
6 → 2 +1, 7→3+1, 8→0+2 si se ejecuta dos veces
```

Craft no produce aumento neto de `max HP` (antes `4*0.25=1.0`, después
`0*0.25+1*1.0=1.0` → delta 0). No se craftea automático.

## 8. persistence

- **Runtime:** `Inventory._items` sobrevive a `death/respawn` (stage no
  recarga inventario).
- **Save/Load:** `SaveData.inventory_items` (`save_data.py:71` v3) +
  `map_item_collected` (`save_data.py:160` v6) ambos guardan piezas. `SaveManager`
  `volcar_estado_en` / `aplicar_estado_de` vuelcan/restauran.
- **Hydration:** `StageScene.on_enter` hidrata `Recogible.recogido = (key in set)`
  (`stage_scene.py:440`), **sin** llamar `Inventory.collect()` de nuevo
  (anti-duplicación).

No se creó `heart_piece_state` ni `SAVE_VERSION 7`.

## 9. slot isolation

`SaveManager` per-slot `slot_{n}.json` (`save_manager.py:258`), `map_item_collected`
y `inventory_items` dentro de cada slot. Slot A `2` piezas no aparece en B
(`test_heart_piece_slot_isolation`).

## 10. NG+

`NG+` (`SaveData.ng_plus`) no resetea `inventory_items` ni `map_item_collected`
(B3 regla). `test_heart_piece_ng_plus` PASS.

## 11. anti-duplication

- B3 `set` + `recogido` flag: segunda recogida del mismo `tmx_object_id`
  → `marcar_item_recogido` devuelve `False`, `inventory` no aumenta.
- Hydration: `recogido=True` pero **no** `Inventory.collect()` (test
  `test_heart_piece_hydration_only_marks_collectible`).

## 12. B3 percentage

4 HeartPieces → `item_total 4`, `1/4 25%`, `2/4 50%`, `3/4 75%`, `4/4 100%`
(`test_heart_piece_b3_percentage`). `heart_vessel` excluido de `item_total`.

## 13. edge cases

0→5, 8→7, duplicate, reload, death/respawn, save/load, NG+ todos definidos en
`heart_piece_contract.md` §23 y verificados en tests.

## 14. tests

`tests/test_heart_piece.py` — 21 tests (ver docs/B4_2_HEART_PIECE_CONTRACT_REVIEW.md §11
y contrato). Todos PASS con infraestructura existente, 0 cambios de lógica.

## 15. known limitations

- `cantidad>1` en TMX da `N` unidades pero `TOTAL` sigue `1` (usar `N` objetos).
- Tiled `id` churn si se borra/recrea objeto → nuevo `item_key` (documentado).
- Craft manual: jugador debe recordar convertir 4 piezas; no hay UI automática.

---

## Evidencia

- `inventory.py:192` `heart_piece 0.25` + `crafting.py:19` `4→1`
- `player.py:540,556` max/current health
- `interactables.py:52 Recogible` + `stage_objetos.py:594`
- `stage_data.py:575 item_total`
- `save_data.py:6 SAVE_VERSION 6` + `save_manager.py:562 marcar_item_recogido`
- Tests `test_heart_piece.py` 21/21 PASS, `test_item_completion` 21/21, `test_bonfire` 14/14

## Estado

**COMPLETE — certification-first, 0 cambios de lógica, renderer UNCHANGED,
SAVE_VERSION UNCHANGED (6).**
