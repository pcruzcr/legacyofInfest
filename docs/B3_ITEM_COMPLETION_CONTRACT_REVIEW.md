# B3 — Item Completion — Contract Review

**Fecha:** 2026-09-02 · **Baseline:** `df16c614` + B2 COMPLETE · **Estado:** CONTRACT READY
**Autor:** Análisis CODE→DATA→TEST frente a repositorio verificado

---

## 1. CURRENT IMPLEMENTATION

**HUD existe pero no pinta:**

- `src/engine/ui/hud.py:931 set_porcentaje_items(pct: float | None)` — existe, guarda
  `self._porcentaje_items` (type ignore), llamado desde
  `src/framework/scenes/stage_parts/actualizaciones.py:180`.
- `HUD.draw()` `hud.py:793` **no invoca** ningún `_draw_porcentaje_items` — el
  valor calculado nunca llega a pantalla. `git grep _draw_porcentaje_items` → 0.

**Cálculo actual en stage:**

`src/framework/scenes/stage_parts/actualizaciones.py:180-200`

```python
total_items = len(recogibles or []) + len(cerraduras or []) + len(cofres or [])
recogidos = sum(1 for r in recogibles if r.recogido) + sum(1 for c in cofres if c.abierto)
pct = min(1.0, recogidos/total) if total>0 else None
hud.set_porcentaje_items(pct)
```

- Fuente: `StageData.recogibles` (`stage_data.py:463`), `cerraduras:464`,
  `cofres:465` — listas pobladas por `StageLoader` vía `stage_objetos.py:506/520/788`.
- Clases: `Recogible` `interactables.py:52` (rect,item_id,automatico,recogido),
  `Cerradura` `:77` (rect,key_id,abierta), `Cofre` `:144` (rect,contenido,key_id,abierto),
  `Fogata` `:157` (rect,mensaje,usada) — no es ítem.
- Persistencia: **nula** para per-map. `SaveData` `save_data.py:32` no tiene
  `map_item_collected`; sólo `inventory_items` global (mezcla compras, drops,
  y colección TMX). `SaveManager` `save_manager.py:502 fijar_variante...`
  guarda Zona4, pero no colección por mapa. `Inventory` `inventory.py:221`
  guarda `items/equipped/prestigio` globales, no por mapa.
- TMX: 46 `Pickup`, 5 `Key`, 6 `Chest`, 4 `Door`, 2 `LockedDoor`, 1 `Cage`,
  2 `PressurePlate`, etc. (medido `assets/maps/**/*.tmx` 906 `(no type)` —
  ruido de tiles, no afecta).

**Inventory defs relevantes:**

- `inventory.py:62 _ITEM_DEFS` incluye `heart_piece` `:192` (0.25 HP),
  `heart_vessel`, `relic_fragment`, `coin`, etc. — todos con `id/name/icon`.
- `Fogata` no está en `_ITEM_DEFS`, no es comprable ni coleccionable.

---

## 2. SEMANTIC PROBLEMS

| # | Problema | Evidencia | Impacto |
|---|---|---|---|
| **P1** | `total = recogibles + cerraduras + cofres` incluye puertas. `recogidos` sólo cuenta `recogibles.recogido + cofres.abierto`. Si el mapa tiene 1 Door, `TOTAL=1` extra que nunca se puede recoger → `100%` imposible. Ej. `stage0` tiene `LockedDoor` → total 5 con puertas vs 4 reales. | `actualizaciones.py:182-194` — `len(cerraduras)` en total pero no en recogidos | UX roto: el jugador hace todo y ve 80 % |
| **P2** | `Chest` vacío (`contenido==""`) cuenta como ítem pero no aporta recompensa. `boss_venado` tiene `Chest_Carport_01` sin `contenido` — contar 1 infla TOTAL sin valor. | `interactables.py:149 contenido=""` + `stage_objetos.py:788 contenido or ""` | Falso TOTAL |
| **P3** | `Key`/`Pickup` sin `item_id` se ignora con `logger.warning` (`stage_objetos.py:510`) pero no hay constancia en `TOTAL` — el diseñador no ve que su objeto no contó. | `stage_objetos.py:506` `if not item_id: logger.warning ... return` | Silencioso |
| **P4** | `TOTAL` se recalcula **cada frame** `len(...)` (actualizaciones.py:182). No es caro para 6–10 ítems, pero viola principio "derivar/cachear" y es el tipo de cómputo que a 120 FPS se vuelve debt si crece. | `actualizaciones.py:182` dentro de `_update_hud_ui` | Performance debt |
| **P5** | `HUD.set_porcentaje_items` existe pero no dibuja — el feature parece "a medias" y nadie lo ve. Un test que sólo verifica `set` pasaría sin detectar el hueco visual. | `hud.py:931` existe, `hud.py:793 draw()` no lo usa | Gap visual |
| **P6** | Persistencia inexistente per-map. `inventory_items` mezcla `coin` de tienda (`buy` `inventory.py:327`), drops de enemigo (`soltar_botin` `interactable_system.py:313`) y TMX — no se puede derivar `COLLECTED` por mapa desde inventory sin falsos positivos. | `save_data.py:71 inventory_items` + `inventory.py:252 collect` | Exploit / métrica falsa |
| **P7** | `Cerradura` exige `reach` y `Llavero`, pero `Cofre` también exige llave (`cofre.key_id`). Si el cofres se cuenta como ítem, ¿contar llave y cofre doble-contaría el mismo desafío? No, son ítems distintos, pero el contrato debe explicitarlo. | `interactables.py:77 key_id` vs `:151 key_id` | Ambigüedad |
| **P8** | `Pickup.automatico=True` vs `False` no cambia semántica de colección, pero el test debe cubrir ambos (tocar vs pulsar). Actual cálculo no distingue — correcto, pero no documentado. | `interactables.py:66 automatico=True` | No bloqueante |

---

## 3. DECISIONS

| Tema | Decisión | Por qué | Alternativa rechazada |
|---|---|---|---|
| **ITEM** | `Pickup`/`Key` + `Chest` con contenido + `SecretRoom` con recompensa | Son las únicas recompensas coleccionables declaradas en TMX; puertas/bonfires/triggers son tránsito/interactuables | Incluir `Door` — rechazado P1 |
| **COLLECTED** | `Recogible.recogido` ∨ `Cofre.abierto` (con contenido) ∨ `SecretRoom.descubierto` (con recompensa) | Flags binarios ya existentes, sin inventar estados | `visible/opened/collected` mezclados — rechazado |
| **TOTAL** | `count(ITEMS declarados en TMX, filtrado por “es ITEM”)` cacheado al load | Determinístico, no depende de runtime, no incluye drops dinámicos | `TOTAL = len dinámico actual` — rechazado (no determinístico) |
| **100%** | `COLLECTED == TOTAL ∧ TOTAL>0` | Evita falso 100 % en mapas sin ítems | `TOTAL==0 → 100%` — rechazado |
| **PERCENTAGE** | `round(collected/total*100)` con `None` si `TOTAL==0`, clamp `[0,1]` | Round UX (2/3=67 no 66), compatible con barra 0.0-1.0 | `floor` — rechazado (subestima) |
| **MAP ID** | `StageData.stage_id` | Ya es la identidad lógica estable usada por Save/WorldMap/Registry | Ruta absoluta — rechazado (frágil) |
| **ITEM ID** | `str(object.id) + ":" + item_id` (Tiled id + item_id) per mapa | Estable sin exigir al diseñador, debuggeable, único por mapa | Coordenadas — rechazado (frágil), `custom item_uid` — rechazado (coste) |
| **PERSISTENCE** | Modelo A `map_id → set(item_ids)` en `SaveData.map_item_collected` | Exactitud + debug + anti-exploit + determinismo | Modelo B count — rechazado (pierde identidad), C dict — rechazado (overkill) |
| **SAVE VERSION** | Propone `v6` sólo al implementar (aditivo `setdefault` si se hace sin bump también vale, pero bump documenta migración) | Backwards: partida v5 sin campo → `{}` → `0%` correcto | No bumpear y confiar en default — posible pero menos explícito |
| **HU** | Barra + texto `42%` sólo si `TOTAL>0`, bajo `NIVEL` | Reusa `_dibujar_barra_moderna`, no reflow, no segunda fila | World Map % en B3 — defer (HUD primero) |
| **BONFIRE** | No es ITEM | No tiene `item_id`, no emite `PICKED`, cura/guardado B4 | Contar como ITEM — rechazado |

---

## 4. REJECTED MODELS

- **B — count only:** pierde qué falta, se rompe al añadir un objeto al TMX
  (histórico 2/3 → nuevo 2/4 sin saber cuál falta), no puede re-hidratar.
- **C — full state dict:** guardar por ítem `{"recogido":bool,"abierto":bool}` es
  redundante cuando el único estado persistente es bool recogido/abierto.
- **`TOTAL = recogibles + cerraduras + cofres`:** hace 100% imposible (P1).
- **`Chest` vacío como ITEM:** infla TOTAL sin recompensa (P2).
- **Coordenadas como ID:** mover 1 px en Tiled cambia identidad.
- **`custom item_uid` obligatorio:** obliga a todo mapa a declarar uid, coste
  innecesario cuando `object.id` ya existe.

---

## 5. SELECTED MODEL

```
SaveData.map_item_collected: dict[str, set[str]] = {}
# map_id "stage0" → {"214","222","225:llave_prologo"}
# map_id "boss_paburu" → {"Chest_Cofre_Del_Mausoleo:heart_vessel"}
```

- Al load: `for r in stage.recogibles: r.recogido = (r.tmx_id in collected_set)`
- Al recoger/abrir: `collected_set.add(tmx_id); save()` (vía SaveManager)
- TOTAL cache: `stage.item_total = len(ITEMS filtrados)` (computado al load)
- HUD: `pct = len(collected_set & item_ids_del_mapa) / total` o `count flags`

---

## 6. MIGRATION PLAN

- **No modificar SaveData hoy** (fase contrato). Para implementación:
  1. Añadir campo `map_item_collected: dict[str, set[str]] = Field(default_factory=dict)` en `save_data.py:32`
  2. `SAVE_VERSION 5 → 6`, `migrate()` `if ver < 6: data.setdefault("map_item_collected", {})`
  3. `SaveManager` añade helpers `marcar_item_recogido(map_id, item_id)` y lectura
  4. `StageLoader` hidrata `recogido` desde save al construir `StageData`
  5. `InteractableSystem` al recoger/abrir llama al helper (o emite evento que `StageScene` escucha)
  6. Backwards: save v5 → `map_item_collected` ausente → `{}` → `0%` (no crash)
- `inventory_items` sigue existiendo para efectos (coin, heart_piece) pero no es fuente de porcentaje.

---

## 7. TEST PLAN

Ver `docs/features/item_completion.md` § Test Plan — 17 tests mínimos.

Prioridad de escritura (cuando se implemente):

1. `test_total_items` (excluye puertas, cofres vacíos)
2. `test_total_zero_safe`
3. `test_item_collected` + `test_chest_collected` + `test_chest_empty_not_counted`
4. `test_percentage_*`
5. `test_map_item_persistence` + `test_map_items_do_not_mix_between_maps`
6. `test_old_save_migration` + `test_new_save_without_item_state`
7. `test_duplicate_collection_ignored` + `test_collected_gt_total_clamped`
8. `test_bonfire_not_counted` + `test_heart_piece_counts_as_one`
9. HUD visibility tests

---

## 8. IMPLEMENTATION PLAN

Orden (no tocar renderer/camera/Zone4/NG+):

1. `interactables.py` — añadir `tmx_object_id: int = 0` a `Recogible`/`Cofre` (+ SecretRoom)
2. `stage_objetos.py` — en `_handle_recogible/_handle_cofre` guardar `tmx_object_id = int(obj.id)`
3. `stage_data.py` — cache `item_ids: list[str]` / `item_total` al construir
4. `save_data.py` — campo `map_item_collected` + bump v6 + migrate
5. `save_manager.py` — helpers y volcado
6. `stage_loader.py` / `StageScene` — hidratación al load y marcado al evento
7. `actualizaciones.py` — eliminar `len(recogibles)+...` por frame, usar cache + set
8. `hud.py` — implementar `HUD._draw_porcentaje_items` + llamar en `HUD.draw()` (respetando `TOTAL==0` hide)
9. `tests/test_item_completion.py` — 17 tests
10. `docs/09_HUD_SPEC.md` § nueva barra porcentaje (opcional)

No tocar: `inventory.py` (no mezclar), `world_map_scene.py` en B3 (defer), TMX (sólo leer).

---

## 9. RISKS

- **TMX id churn:** borrar y recrear objeto cambia `object.id` → progreso perdido para ese ítem. Mitigación: documentar "no borrar, mover" y considerar `item_uid` custom sólo si churn real se mide.
- **Drops vs TMX:** si `soltar_botin` suelta `Recogible` dinámico con `item_id` que coincide con `_ITEM_DEFS`, no debe contar para porcentaje de mapa. Mitigación: filtrar `tmx_object_id == 0` (dinámicos) fuera de `TOTAL`.
- **HeartPiece 4→1:** porcentaje cuenta piezas (1 ITEM = 1 pieza), no corazones completos. Un jugador con 3/4 piezas ve 75 % aunque no haya ganado el corazón — correcto, es colección, no bonus.
- **Map rename:** `stage_id` cambia → nuevo mapa → `{}` → 0 % (no intenta alias; documentar).

---

## 10. STATUS

```
CONTRACT READY — 9 decisiones cerradas, implementación desbloqueada tras aprobación
```

Siguiente acción única (cuando se apruebe implementar): añadir `tmx_object_id` a `Recogible`/`Cofre` y campo `map_item_collected` en `SaveData` (con tests `test_total_items` primero).

