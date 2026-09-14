# B4.2 — Heart Piece — Contrato de Diseño

**ID:** LOI-FEAT-B4.2 · **Versión:** 1.0.0 · **Estado:** CONTRACT READY — NO IMPLEMENTAR
**Baseline:** `df16c614` + B2 COMPLETE + B3 COMPLETE + B4.1 COMPLETE
**Fecha:** 2026-09-02

---

## 1. PURPOSE

Heart Piece es el fragmento coleccionable `1/4` que, acumulado, aumenta la vida
máxima del jugador. Enseña el flujo `TMX → Recogible → Inventory → Player.max_health`
y su persistencia per-map vía B3 (`map_item_collected`) + por-slot vía
`inventory_items`. No es un nuevo sistema, es reconciliación de infraestructura
existente (`inventory.heart_piece` + `crafting heart_vessel`).

---

## 2. ITEM MODEL

**E — Combinación A+B+D:** Heart Piece es simultáneamente:

- **A. collectible fragment** — `Pickup` en TMX con `item_id=heart_piece`,
  `tmx_object_id` estable, `1 ITEM` en B3 (`stage_data.item_total`).
- **B. inventory resource** — `Inventory._items["heart_piece"] = count`
  (`inventory.py:192`, `collect()` + `count()`), slot `None` (no equipable),
  `price 0`.
- **D. crafting ingredient** — `crafting.RECETAS heart_vessel: {"heart_piece":4}` (`crafting.py:19`)

**No es** C puro (direct max-health sin pasar por inventario): el bono
pasa por `Inventory.get_total_hp_bonus()` → `Player._bonus_max_health`.

---

## 3. COLLECTION MODEL

- **B3 ITEM:** `Recogible(item_id="heart_piece", tmx_object_id=N)` → `1 ITEM`
  (B3 contrato `Pickup/Key` con `tmx_object_id!=0`).
- **Recogido:** `Recogible.recogido==True` tras `InteractableSystem._recoger`
  (`interactable_system.py:318`), emite `INTERACT_ITEM_PICKED` y
  `llavero.coger("heart_piece")` → `Inventory.collect("heart_piece")`.
- **Anti-duplicado:** `map_item_collected[map_id]` guarda `item_key`
  `"MAP:TMX_ID:heart_piece"` (B3). Segunda colección del mismo `tmx_object_id`
  → set ya contiene → no suma, `Inventory.collect` no se vuelve a llamar
  porque `recogido` ya es `True` y el objeto no reaparece tras hidratar.

---

## 4. TMX MODEL

**Reutilizar `Pickup`, no crear `HeartPiece` type nuevo.**

```xml
<object id="42" type="Pickup" x="..." y="...">
  <properties>
    <property name="item_id" value="heart_piece"/>
    <property name="automatico" type="bool" value="true"/>
    <property name="mensaje" value="Fragmento de corazón 1/4"/>
  </properties>
</object>
```

- `type = Pickup` (o `Key`), `item_id = heart_piece` es suficiente.
- `tmx_object_id = 42` es la identidad estable para B3.
- No crear `type = HeartPiece` sin razón de dominio (no hay comportamiento
  distinto de otros `Pickup` salvo el `ItemDef`).

Si un diseñador quiere dar `N` piezas en un cofre:
`Chest contenido="heart_piece"` + `cantidad` no existe en `Cofre`; usar
`Pickup` con `cantidad=N` (`Recogible.cantidad` `interactables.py:73`,
`AUD-218`) o `N` objetos separados. Recomendado `N` objetos para B3 (cada
`TMX_ID` distinto = `1 ITEM` cada uno, no `1 Pickup` con `cantidad=4` que
contaría como `1 ITEM` en `item_total`).

---

## 5. ITEM ID

`heart_piece` (el `ItemDef.id` en `inventory.py:192`). Estable, único.

MAP+TMX+ITEM: `stage0:42:heart_piece` (B3 `item_key`).

No usar IDs ambiguos (`heart`, `piece`).

---

## 6. QUANTITY

- **TMX:** `Recogible.cantidad` default `1` (`interactables.py:73`). Si
  `cantidad>1`, el `InteractableSystem` entrega `cantidad` unidades al
  inventario en una sola recogida (`llavero.coger` + `Inventory.collect` con
  `cantidad`), pero B3 `item_total` cuenta el **objeto** como `1 ITEM`, no las
  unidades. Por eso **no** usar `cantidad>1` para Heart Piece si se quiere
  `4 piezas = 4 ITEMS` en B3 (usar 4 objetos).
- **Recomendado:** `cantidad = 1` por Heart Piece, `1 Pickup = 1 fragmento`.
  Si se necesita bolsa multi-pieza, documentar que `TOTAL` no escala con
  `cantidad`.

---

## 7. INVENTORY MODEL

- `inventory._items["heart_piece"] = count` fragmentos (entero).
- `get_def("heart_piece").max_hp_bonus = 0.25` (`inventory.py:195`) → cada
  fragmento suma `0.25` vía `_sumar_bonus` (`inventory.py:280`).
- `get_total_hp_bonus()` suma `0.25 * count` + `heart_vessel 1.0` si existe.
- `count("heart_piece")` es el número de fragmentos sin convertir.
- `has("heart_piece")` true si `count>0`.

No es `fractional heart value` ni `already converted`; es conteo crudo.

---

## 8. 4→1 RULE

**Regla actual (crafting manual):**

```
4 heart_piece (en inventario)
→ crafting.craftear(inv, "heart_vessel")  # consume 4, collect 1 heart_vessel
→ Inventory._items["heart_piece"] -=4, _items["heart_vessel"] +=1
→ get_total_hp_bonus: 4*0.25=1.0 se va, +1.0 vessel entra → neto 0 cambio tras craft
```

`crafting.py:31-41` — gasta `inventario._items[k]` en bucle, luego
`inventario.collect(resultado,1)`.

**Qué significa `heart` / `heart_vessel` / `max_health`:**

- `heart_piece` `0.25` y `heart_vessel` `1.0` son ambos `max_hp_bonus`.
- `Player.max_health` `player.py:458` = `settings.PLAYER_MAX_HEALTH + bonus_max_health`
  con `bonus_max_health = get_total_hp_bonus()` (`player.py:540`).
- `max_health` aumenta **inmediatamente** al recoger la pieza (0.25), antes de
  cualquier craft (ver `Player._bonus_max_health` refresh).

**Implicación:** craftear 4→1 no aumenta `max_health` más allá de lo que las
4 piezas ya dieron (net 0). Es canje cosmético / de inventario (liberar
material), no ganancia adicional.

---

## 9. CRAFTING

- **Cuándo:** manual, cuando `puede_craftear(inv,"heart_vessel")` (`count>=4`).
  No automático al llegar a 4 (no hay `update` que lo dispare).
- **Dónde:** donde el juego llama `craftear` (futuro UI de crafting / tienda /
  menú). Hoy sólo `crafting.py` y tests lo invocan; no hay pantalla dedicada.
- **Consume:** `heart_piece ×4` (`crafting.py:38`).
- **Recibe:** `heart_vessel ×1` (`collect`).
- **Repetible:** sí, mientras `count>=4`.
- **Sobrantes:** `count %4` permanecen (ej. 5→1 vessel +1 restante, 6→1+2, 8→2).
- **Registro:** no queda registro del craft salvo el cambio en `inventory_items`
  (`heart_piece` baja, `heart_vessel` sube) que viaja en `SaveData.inventory_items`.

---

## 10. DOUBLE COUNTING RISK

**¿Existe hoy?** **NO**, si se respeta el flujo craft.

- Sin craft, 4 piezas → `4*0.25=1.0` → `max_health +1` correcto.
- Con craft, 4 piezas → `1.0` → craft consume 4 (→0) + vessel `1.0` → `max_health +1` sigue igual, no `+2`.

**Riesgo si se modifica:** si alguien cambia `heart_piece` a `0` y mantiene
vessel `1.0` (Modelo B puro) o si añade `heart_piece 0.25` **más** vessel
adicional por cada 4 sin consumir piezas, habría `+2` (doble). Por eso el
contrato debe fijar **Modelo A** (piezas dan 0.25) y craft como canje neto 0
o **Modelo B** (piezas no dan, sólo vessel) — no ambos acumulativos.

**Decisión contrato:** **Modelo A** (actual): piezas dan `0.25` inmediato;
craft es opcional y neto 0. No double counting porque craft consume.

---

## 11. MAX HEALTH

**¿Cuándo aumenta?**

- **Modelo A (actual / contrato):** al **recoger** cada pieza (`+0.25`), vía
  `Inventory.collect` → `Player._bonus_max_health` refresh en próximo
  `player.update` o `apply_relic_bonuses` (`player.py:540`). Inmediato.
- No sólo al craftear vessel.

---

## 12. CURRENT HEALTH

Cuando `max_health` aumenta `+0.25` (o `+1` tras vessel, pero neto 0):

```python
gained = max_health - previous_max
if gained>0: _health = min(max_health, _health + gained)  # player.py:556-558
```

- **B. +same delta to current** — cura parcial igual al aumento de máximo.
- No `full heal`, no `unchanged`. Si el jugador está herido, gana vida
  proporcional; si está lleno, se mantiene lleno en el nuevo máximo.

---

## 13. PERSISTENCE

- **Runtime (muerte/respawn):** `Inventory._items["heart_piece"]` vive en
  memoria, sobrevive a `death → respawn` (stage no recarga inventario).
  `Recogible.recogido` persiste en `StageData` del stage actual hasta
  salir; muerte no lo resetea.
- **Save/Load:** `SaveData.inventory_items` (`save_data.py:71`) guarda
  `{"heart_piece": N, "heart_vessel": M}`; `SaveManager.volcar_estado_en`
  (`save_manager.py:145`) vuelca inventory actual al slot, `aplicar_estado_de`
  (`:178`) restaura. Además `SaveData.map_item_collected` (B3) guarda qué
  `tmx_object_id` ya se recogió, para que el objeto no reaparezca al volver
  al mapa.
- **No crear** `heart_piece_state` separado; reutiliza `inventory_items` +
  `map_item_collected`.

---

## 14. SAVE VERSION

- `SAVE_VERSION = 6` hoy (B3). Heart Piece **no** requiere `v7`: usa
  `inventory_items` existente (desde v3) y `map_item_collected` (v6). No hay
  nuevo campo. Si se añadiera `heart_piece` como campo propio, sí bump.

---

## 15. SLOT ISOLATION

- `SaveManager` es per-slot (`SAVES_DIR/slot_{n}.json`), `map_item_collected`
  y `inventory_items` viven dentro de cada slot.
- Slot A recoge `heart_piece` en `stage0:42` → `slot1.json` lo tiene;
  Slot B mismo mapa no lo tiene hasta que lo recoja allí.
- `restaurar()` filtra `id in _ITEM_DEFS`, pero `heart_piece` está en defs,
  por lo que sobrevive.

---

## 16. NG+

- **Remain collected** — por defecto `same save progression` (B3 regla).
  NG+ (`SaveData.ng_plus` `save_data.py:160`) no resetea `inventory_items`
  ni `map_item_collected`. Si diseño quiere reiniciar Heart Pieces en NG+
  (volver a coleccionar), debe ser decisión explícita documentada y con
  migración; contrato actual: **no reinicia**.

---

## 17. HUD

- Heart Pieces ya visibles vía `Inventory` UI (inventario) y `HUD` indirecto:
  `HUD` muestra `max_health`/`ranuras_de_corazon` (corazones) y `VIDA bar`,
  no un contador `2/4` dedicado.
- B4.2 **no** añade nueva HUD element. `B3` ya muestra porcentaje por mapa
  (`42% (3/4)`) que incluye Heart Pieces como `1 ITEM` cada uno; eso es el
  indicador principal.
- Si se quiere `HeartPieces: 2/4` explícito, es futura mejora, no B4.2.
  Contrato: **no modificar HUD en B4.2**.

---

## 18. INVENTORY UI

- `Inventory` UI (tienda/inventario) muestra `heart_piece` si `count>0`:
  nombre “Fragmento de corazón” + descripción “1/4… Junta 4…”.
- `heart_vessel` (“Vasija de corazón”) aparece si se craftea.
- Piezas restantes `count %4` visibles en inventario; vessels también.
- Visible sólo si `>0` (no mostrar 0).

---

## 19. FEEDBACK

Al recoger Heart Piece: sistema actual de `InteractableSystem._recoger`
→ `llavero.coger` → `Inventory.collect` → `_collect_notifications` (3 s) +
`EVENTO_RECOGIDO` con `pos` → partículas (`AUD-281`) / sonido panoramizado +
`HUD pulso` vía `get_inventory` y `show_message`. No crear nuevo sistema;
reutilizar `SHOW_MESSAGE`/`SFX`/`POPUP`.

---

## 20. B3 COMPATIBILITY

- `Heart Piece → 1 ITEM` en `stage_data.item_total()` (Pickup con
  `tmx_object_id!=0` cuenta). No contar `4 pieces → 4 extra + vessel` como
  5. Cada instancia TMX es exactamente `1 ITEM`; `cantidad>1` no escala `TOTAL`
  (ver §6 contract B3).
- `Fogata` no es ITEM, no interfiere.

---

## 21. ANTI-EXPLOIT

```
collect heart_piece  → inventory+1, map_item_collected add, save
→ reload → InteractableSystem hidrata recogido=True → no reaparece → no duplicate
```

B3 `set` es protección primaria; `Inventory.collect` secundario (no se llama
si ya está `recogido`).

---

## 22. TMX DESIGN

Mínimo para declarar Heart Piece:

```
type=Pickup, item_id=heart_piece, tmx_object_id=auto, automatico=true
```

Reutiliza `Pickup`. No crear `type=HeartPiece` sin comportamiento distinto.
Estudiante aprende `TMX → collectible → inventory → progression → persistence`.

---

## 23. EDGE CASES

| Piezas | Efecto | Max HP (base 5) |
|---|---|---|
| 0 | 0 | 5 |
| 1 | +0.25 | 5.25 |
| 2 | +0.5 | 5.5 |
| 3 | +0.75 | 5.75 |
| 4 | +1.0 (o 0 craft +1 vessel neto 1.0) | 6 |
| 5 | +1.25 (4→vessel +1 suelta) | 6.25 |
| 8 | +2.0 (2 vessels o 8 piezas) | 7 |

`duplicate collect` (mismo `tmx_id`) → set ignora. `reload` tras coleccionar
→ hidrata. `death/respawn` → conserva. `save/load` → conserva via both
stores. `NG+` → conserva.

---

## 24. TEST PLAN

```
test_heart_piece_registered (ItemDef existe, bonus 0.25)
test_heart_piece_loaded_from_tmx (Pickup heart_piece → item_total 1)
test_heart_piece_is_item (B3)
test_heart_piece_collects (recogido + inventory +1)
test_heart_piece_persists (map_item_collected + inventory_items)
test_heart_piece_does_not_duplicate (set)
test_four_pieces_conversion (craft 4→1 vessel, bonus neto)
test_partial_pieces_remain (5→1 vessel+1, 6→1+2)
test_heart_vessel_reward (vessel max_hp 1.0)
test_max_health_change (0.25 per piece immediate)
test_current_health_behavior (+delta)
test_death_respawn (conserva)
test_slot_isolation (A vs B)
test_ng_plus_behavior (remain)
test_b3_percentage_counts_piece (1/4 25% etc)
```

---

## 25. ACCEPTANCE CONTRACT

B4.2 no puede implementarse hasta cerrar:
`ITEM, COLLECTION, QUANTITY, INVENTORY, 4→1 RULE, MAX HEALTH, CURRENT HEALTH,
CRAFTING, PERSISTENCE, NG+, UI, TMX` — todos cerrados arriba.

---

## 26. NO IMPLEMENTAR (esta fase)

No modificar `inventory.py` `player.py` `save_data.py` `hud.py` `crafting.py`
hasta contrato aprobado.

