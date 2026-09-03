# B4.2 — Heart Piece — Contract Review (Análisis)

**Fecha:** 2026-09-02 · **Baseline:** `df16c614` + B2+B3+B4.1 COMPLETE
**Modo:** ANALYZE / RECONCILE — no implementar

---

## 1. CURRENT INFRASTRUCTURE

- **ItemDef:** `inventory.py:192 heart_piece` `max_hp_bonus=0.25`, `heart_vessel:193` `1.0`,
  `hollow_eye`, etc. `get_total_hp_bonus()` `inventory.py:292` suma `max_hp_bonus*count`.
- **Collectible:** `Pickup` `stage_objetos.py:594` con `item_id` → `Recogible`
  `interactables.py:52` `tmx_object_id` (B3).
- **Crafting:** `crafting.py:19 heart_vessel: {heart_piece:4}` `puede_craftear`/`craftear` consumen 4 y `collect(resultado,1)`.
- **Player:** `player.py:540 _bonus_max_health = get_total_hp_bonus()`, `max_health` `458`,
  `gained` cura `556-558` `min(max_health, _health+gained)`.
- **Save:** `SaveData.inventory_items` `71` + `map_item_collected` v6 (B3) ambos guardan piezas.
- **B3:** `Pickup heart_piece` es `1 ITEM` (`stage_data.item_total`), `item_key` `MAP:TMX:heart_piece`.

---

## 2. ITEM MODEL DECISION — E (A+B+D)

Heart Piece es fragmento coleccionable **y** recurso de inventario **y**
ingrediente de crafteo — las tres a la vez. No es sólo A ni sólo D: la pieza
se recoge (A), cuenta en `inventory.count` (B), suma `0.25` a vida (C) vía
`max_hp_bonus`, y se gasta en `crafting` para `heart_vessel` (D). La
combinación está ya implementada; crear un sistema paralelo sería duplicar.

---

## 3. 4→1 RULE

```
4 × heart_piece (0.25 cada una = 1.0)
→ crafting.heart_vessel consume 4 → heart_vessel (+1.0)
→ neto tras craft = 0 (1.0 se va, 1.0 entra) — canje, no ganancia extra
```

`heart` = `max_health` +1 corazón (5→6). `heart_vessel` es el ítem resultado
del craft; `max_hp_bonus` es el campo que ambos usan.

---

## 4. DOUBLE COUNTING ANALYSIS

**¿4 piezas → +1 por acumulación +1 por vessel = +2?** **NO** con código actual.

- 4 piezas sin craft: `4*0.25=1.0` → `max 6` — PASS.
- 4 piezas + craft: piezas `4*0.25=1.0` → craft consume 4 piezas (→0) + vessel `1.0` → `max 6` igual, no `7`.
- Código `crafting.py:38-41` borra `heart_piece` antes de añadir vessel, por lo
  que `_sumar_bonus` no los cuenta doble en el mismo fotograma. Si craft no
  consumiera, sí habría `+2` (riesgo si se cambia receta).

**Conclusión:** riesgo NO presente hoy, pero existe si alguien modifica receta
sin consumo o cambia `heart_piece` bonus a 0 sin ajustar.

---

## 5. QUANTITY, INVENTORY, CRAFTING

- **Cantidad:** `Recogible.cantidad` default `1`; cada TMX `Pickup` es `1` pieza.
  Usar 4 objetos para 4 piezas (B3 `TOTAL` cuenta objetos, no unidades).
- **Inventory:** `count("heart_piece")` = fragmentos sueltos; `has_vessel` es
  `count("heart_vessel")`.
- **Crafting:** manual `craftear(inv,"heart_vessel")`, no automático; `puede_craftear`
  true si `count>=4`; consume exacto 4, deja resto `count%4`.

---

## 6. MAX / CURRENT HEALTH

- **Max:** +0.25 inmediato al recoger (Modelo A). Confirmado `player.py:540` refresh.
- **Current:** `+gained` `min(max, _health+gained)` `556-558` — cura parcial,
  no full heal ni unchanged. Si el jugador está en 3/5 y recoge pieza
  (max 5→5.25), `gained 0.25` → health 3.25; no salta a 5.25.

---

## 7. PERSISTENCE, SLOT, NG+

- `inventory_items["heart_piece"]` + `map_item_collected[map_id]` ambos viajan
  en `SaveData` (v6). `death/respawn` conserva memoria (no recarga inventario);
  `save/load` conserva ambos stores; `slot A` no contamina `B` (SaveManager per-slot).
- NG+ **remain collected** (no reset), como B3.

---

## 8. HUD / INVENTORY UI / FEEDBACK

- Piezas visibles en `Inventory` UI si `count>0` (“1/4…”). `heart_vessel` si existe.
- HUD no tiene `2/4` dedicado; `B3` `% (3/4)` ya incluye Heart Pieces como `1 ITEM`
  cada una. Feedback al recoger: `SHOW_MESSAGE` + `SFX` + `HUD pulso` existente.

---

## 9. B3 COMPATIBILITY, ANTI-EXPLOIT, EDGE

- B3: `heart_piece` = `1 ITEM`, `4 pieces + vessel` no cuenta como 5.
- Anti-exploit: `set` + `recogido` flag → `collect` duplicado no suma.
- Edge 0-8 piezas tabla contrato, `duplicate collect`, `reload`, `death`, `NG+`
  todos definidos.

---

## 10. TMX DESIGN

`Pickup` `item_id=heart_piece` (no nuevo type). Mínimo 1 objeto por pieza,
`tmx_object_id` auto. Estudiante aprende TMX→collectible→inventory→progression.

---

## 11. TEST PLAN

15 tests listados en contrato (`test_heart_piece_*` + `test_max_health_change`
etc.), todos diseñados pero no escritos (fase contrato).

---

## 12. IMPLEMENTATION FILES (cuando se apruebe)

No tocar en esta fase contrato: si se aprueba Modelo A, **ningún** archivo
necesita cambio de lógica (todo ya existe). Si se quiere Modelo B (piezas no
dan bonus, sólo vessel), sí habría que editar `inventory.py` (`heart_piece`
`max_hp_bonus 0`), pero contrato recomienda **mantener Modelo A** (0 cambio).

Si se mantiene Modelo A, implementación B4.2 es sólo **tests + docs** para
certificar, no nueva persistencia.

---

## 13. DESIGN RISKS

- **Churn Tiled id:** borrar/recrear Heart Piece cambia `tmx_object_id` → se
  considera nuevo ITEM (B3). Mitigar documentando “no borrar, mover”.
- **Cantidad>1 en TMX:** `Recolectable.cantidad` con `heart_piece` daría `N`
  unidades pero `TOTAL` seguiría `1`; usar `N` objetos en vez de
  `cantidad=N` para Heart Piece.
- **Craft manual olvidado:** jugador con 8 piezas sin craftear tiene `+2` de
  piezas, no de vessels — pero `max` igual, sólo inventario distinto; no es
  bug, es UX.

---

## 14. DOUBLE COUNTING RISK

**NO** — con código actual (`heart_piece 0.25` + `craft consume 4 → vessel 1.0`
neto 0). Riesgo sólo si se cambia receta/bonus sin análisis.

