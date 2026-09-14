# B3 — Item Completion — Contrato Semántico

**ID:** LOI-FEAT-B3 · **Versión:** 0.1.0 (CONTRACT) · **Estado:** CONTRACT READY — NO IMPLEMENTAR SAVE TODAVÍA
**Baseline:** `df16c614 AUD-805` + B2 COMPLETE — renderer `FROZEN`, Zona4 HOLD
**Fecha:** 2026-09-02

---

## 1. PURPOSE

Dar al jugador una medida exacta y persistente de qué porcentaje del contenido
coleccionable de **cada mapa** ha obtenido, visible en el HUD, sin mezclar
progresión de inventario global, sin falsos 100 % y sin exploits de recarga.

No es un porcentaje de inventario global (`coin`/`heart_vessel` totales), es
**per-map**: cada TMX tiene su propio total y su propio recogido.

---

## 2. SCOPE

- **Dentro:** `Pickup`/`Key` (Recogible), `Chest` (Cofre) cuando entrega
  contenido, y sus variantes via `SecretRoom.recompensa` si es un ítem.
- **Fuera:** `Door`/`Cage`/`LockedDoor` (Cerradura), `Bonfire`/`Fogata`,
  `EventTrigger`/`Disparador`, `WarpZone`, `PressurePlate`, `SecretExit`
  (revela), `MessageTrigger`, enemigos, monedas de enemigo si no están en TMX
  (son dinámicas), tienda (`buy` no es colección de mapa).

La tienda y los drops de enemigo no cuentan para el porcentaje de mapa porque
no son declarados en el TMX y no tienen `TOTAL` determinístico.

---

## 3. ITEM DEFINITION

```
ITEM :=
  objeto coleccionable declarado en TMX
  cuyo tipo pertenece a { Pickup, Key, Chest }
  y que al ser obtenido incrementa progreso de colección del mapa
```

| Tipo TMX | Clase runtime | ¿Es ITEM? | ¿Por qué? | Evidencia |
|---|---|---|---|---|
| `Pickup` | `Recogible` `src/framework/stage/interactables.py:52` | **SÍ** | Es el recogible genérico; al tocarlo dispara `INTERACT_ITEM_PICKED` y entra en inventario/llavero | `stage_objetos.py:760 _handle_recogible` + `interactable_system.py:288 _recoger` |
| `Key` | `Recogible` (alias) | **SÍ** | Alias de `Pickup` por legibilidad en Tiled; mismo comportamiento | `stage_objetos.py:506 @register("Pickup","Key")` |
| `Chest` | `Cofre` `interactables.py:144` | **SÍ si contenido != ""** | El cofre es contenedor: el ítem es su `contenido` (`heart_vessel`, `relic_fragment`, etc.). Un cofre vacío no aporta colección | `interactables.py:144 contenido=""` + `stage_objetos.py:788 _handle_cofre` |
| `Door`/`Cage`/`LockedDoor` | `Cerradura` `interactables.py:77` | **NO** | Es una barrera, no una recompensa. Abrirla es superar obstáculo, no coleccionar | `stage_objetos.py:520 _handle_cerradura` — no debe contar |
| `Fogata`/`Bonfire` | `Fogata` `interactables.py:157` | **NO** | Interactuable reutilizable de curación/guardado (B4), no colección | `interactable_system.py:456 _usar_fogata` |
| `SecretRoom` | `SecretRoom` `interactables.py:301` | **SÍ si recompensa != ""** | La sala en sí no es ítem, pero su `recompensa` (ej. `relic_fragment`) sí | `interactables.py:311 recompensa=""` |
| `SecretExit`, `EventTrigger`, `WarpZone`, `PressurePlate` | — | **NO** | Triggers / tránsito / puzzles, no colección | `interactables.py:168/187/327` |

**Respuestas obligatorias:**

- ¿Un cofre cuenta? → Sí **si tiene contenido**; el contenedor cuenta como 1 ítem (no el cofre vacío + contenido separado).
- ¿La cerradura cuenta? → **No**.
- ¿La llave cuenta? → **Sí** (es un `Key`/`Pickup` con `item_id`, p.ej. `llave_del_juicio`).
- ¿La recompensa dentro de un cofre cuenta? → **Es el ítem del cofre**; no se duplica.
- ¿HeartPiece cuenta? → **Sí**, como `Pickup` con `item_id="heart_piece"` (vía `inventory.py:192`). 1 pieza = 1 ITEM.
- ¿Bonfire cuenta? → **No**.
- ¿Objeto interactivo no coleccionable cuenta? → **No**.

---

## 4. COLLECTED DEFINITION

```
ITEM = COLLECTED ⇔
  (Recogible.recogido == True)  para Pickup/Key
  ∨ (Cofre.abierto == True  ∧  Cofre.contenido != "")  para Chest con contenido
  ∨ (SecretRoom.descubierto == True  ∧  recompensa != "")  para SecretRoom con recompensa
```

**NO mezclar estados:**

- `visible` / `abierto` / `recogido` / `disparado` / `descubierto` son
  estados distintos; sólo los tres de arriba significan colección.
- `Cerradura.abierta` **no** es `COLLECTED`.
- `Disparador.disparado` **no** es `COLLECTED`.

Evidencia: `Recogible.recogido` `interactables.py:74`, `Cofre.abierto` `:153`,
`SecretRoom.descubierto` `:314`, `InteractableSystem._recoger/:288`,
`_abrir_cofres/:392`, `SecretRoom.intentar_descubrir/:316`.

**Cuándo se decide:** en el fotograma en que el sistema marca el flag
(`objeto.recogido = True` etc.) y emite el evento. No al dibujar ni al
entrar inventario (el inventario puede filtrar `item_id` desconocidos).

---

## 5. TOTAL DEFINITION

```
TOTAL(map) :=
  count { ITEMS declarados como coleccionables en el TMX de map }
```

Fuente de verdad **única:** lo que `StageLoader` construye en
`StageData.recogibles + StageData.cofres_con_contenido (+ secret_rooms_con_recompensa)`
al hacer `load()` del TMX.

- **No** depende del estado dinámico actual (cuántos quedan en el suelo).
- **No** incluye drops de enemigos (`InteracableSystem.soltar_botin`) porque
  son dinámicos y no hay TOTAL determinístico.
- **No** incluye compras de tienda.
- Se calcula **una vez** al cargar el mapa (`StageData.map_pixel_size` etc.),
  no por frame. Actual `actualizaciones.py:182` recalculaba `len(...)` cada
  frame — debe cachearse.

Si `TOTAL == 0` (mapa sin coleccionables, ej. muchos mapas de jefe), no hay
porcentaje que mostrar.

**Ejemplo medido** (grep TMX):

- `stage0` 6 objetos (3 Pickups + 1 Key + 1 LockedDoor + 1 Pickup) → **TOTAL=4**
  (3 fragmentos + llave + Pickups, cofre 0, puerta excluida)
- `boss_paburu` 5 (1 Key + 1 Door + 1 Chest + 2 Pickups) → **TOTAL=4**
  (Key + Chest + 2 Pickups, puerta excluida)
- `stage4_1b` 10 Pickups minerales → **TOTAL=10**

La regla `TOTAL` antigua (`recogibles + cerraduras + cofres`) está rechazada
(ver § Rejected).

---

## 6. 100% DEFINITION

```
PERCENTAGE = 100%  ⇔  COLLECTED == TOTAL  ∧  TOTAL > 0
```

- `TOTAL == 0` → `percentage = None` (no mostrar), no 0 % ni 100 %.
- `COLLECTED > TOTAL` es **imposible** por construcción (ver Anti-exploit);
  si ocurre por corrupción, clamp a 100 % y log warning, no crash.

---

## 7. PERCENTAGE FORMULA

```
if TOTAL == 0:   percentage = None   # no mostrar
else:            percentage = round((COLLECTED / TOTAL) * 100)
```

- `round` a entero (0–100) compatible con UX (`37 %`, `100 %`).
  `floor` subestima (2/3=66 % cuando el jugador espera 67), `ceil` infla.
- Internamente el HUD recibe `float 0.0–1.0` (`pct = collected/total`,
  clamp `[0,1]`) para la barra; la etiqueta se formatea con `round`.
- Acota: `pct = max(0.0, min(1.0, collected/total))` (defensa `COLLECTED> TOTAL`).

Actual `actualizaciones.py:196 min(1.0, recogidos/total)` ya acota, pero debe
migrar a `round`.

---

## 8. ITEM ID

Cada ítem necesita identificador **estable** dentro del mapa para persistencia.

**Problema de `Tiled object id`:** es estable si el objeto no se borra, pero
Tiled lo reasigna si se elimina y recrea; dos mapas distintos pueden
compartir el mismo id numérico, y reordenar no lo cambia, pero borrar sí.

**Decisión:** `MAP_ID + ":" + str(object.id) + ":" + item_id`

- `object.id` es el `id` del elemento `<object id="123">` del TMX (único por
  mapa, leído como `obj.id` en `stage_objetos.py`). Es el más estable que
  ofrece Tiled sin exigir al diseñador.
- Se concatena con `item_id` (`Pickup.item_id` / `Cofre.contenido`) para
  debug humano, no para identidad (el `id` numérico ya es clave).
- Si el diseñador borra y recrea el objeto, el id cambia y el progreso se
  pierde — comportamiento aceptable y visible; alternativa (`custom property
  item_uid`) obligaría a todo mapa a declarar uid manual y se rechaza por
  coste.

**No usar:** coordenadas (`x,y`) — frágiles al mover el objeto 1 px.

Ejemplo: `stage0:214:fragmento_1`, `boss_paburu:Chest_Cofre_Del_Mausoleo:heart_vessel`

**Para implementación:** al construir `Recogible`/`Cofre` en
`stage_objetos.py` guardar `tmx_object_id = int(obj.id or 0)` como campo
nuevo (aditivo, sin romper TMX antiguos — 0 = legacy sin persistencia).

---

## 9. MAP ID

```
MAP_ID := StageData.stage_id
```

- `stage_id` es el identificador lógico del mapa (ej. `stage0`,
  `stage1_2_la_soda`, `boss_paburu`), declarado en TMX propiedad `stage_id`
  o derivado del nombre de fichero (`stage_registry.py:32 STAGE_ORDER`,
  `discover_stages()`).
- Es el que ya usan `SaveData.stage_id`, `SceneManager`, `WorldMap` y
  `StageLoader`; no se introduce nuevo `MAP_ID` de filesystem.
- Estable: no es ruta absoluta (`assets/maps/stage0/stage0.tmx` no, `stage0` sí).
- Si un mapa se renombra, se considera mapa nuevo — migración no intenta
  alias.

---

## 10. SAVE MODEL

### Modelo seleccionado: **A** — `map_id → set(item_ids collected)`

```python
# en SaveData, aditivo, default {}
map_item_collected: dict[str, set[str]] = Field(default_factory=dict)
# ejemplo:
# {
#   "stage0": {"214", "222", "225"},
#   "boss_paburu": {"Chest_Cofre_Del_Mausoleo"},
#   "stage4_1b": {"122", "123"}
# }
# donde cada set contiene los ITEM_IDs (object ids) recogidos
```

**Por qué A:**

- Exactitud: sabe **qué** se recogió, no sólo cuántos (permite re-hidratar
  objetos al cargar, no sólo pintar porcentaje).
- Debugging: `save_data.map_item_collected["stage0"]` lista los ids — útil
  para reproducir bugs.
- Determinismo: re-cargar el mismo mapa + mismo set = mismo porcentaje,
  independiente del orden.
- Anti-exploit: re-colectar el mismo `item_id` ya en set no suma.
- Migración: añadir un nuevo objeto al TMX no invalida los viejos ids.

**Rechazados:**

- **B** `map_id → collected count` — pierde identidad; añadir/quitar un objeto
  del mapa rompe el porcentaje histórico y no puede saber qué falta.
- **C** `map_id → item state dict` — sobre-ingeniería (guardar `recogido`,
  `abierto`, `descubierto` por ítem) cuando el único estado que persiste es
  recogido/abierto (bool).

**Qué NO se persiste (derivable):**

- `TOTAL` — se deriva del TMX al cargar (`len(ITEMS declarados)`).
- `percentage` — `round(collected/total*100)`.
- `Inventory` global no es la fuente; la fuente es `map_item_collected`.
  El inventario (`SaveData.inventory_items`) sigue guardando efectos
  (`coin`, `heart_piece`), pero el porcentaje no se deriva de él porque el
  inventario mezcla compras y drops no-TMX.

**Dónde en StageData:** al cargar, `StageLoader` marca
`recogible.recogido = (item_id in save_data.map_item_collected[stage_id])`
antes de entregar la escena — así el objeto ya no está en el suelo al volver.

---

## 11. MIGRATION

**No bump todavía** en esta fase (CONTRACT READY). Para implementación:

- `SAVE_VERSION = 5` hoy (NG+). B3 propone `SAVE_VERSION = 6` **sólo si**
  se añade `map_item_collected`; si se hiciera aditivo con default `{}` sin
  bump, una partida vieja se leería con `{}` y daría `0 %` — correcto, pero
  `migrate()` debe asegurar `setdefault("map_item_collected", {})` y
  `version=6` para futuros cambios que sí necesiten migración.
- `version_original` conserva la versión con la que se escribió la partida
  (ya existe) para distinguir `0 % real` de `0 % por ausencia`.
- Backwards: partida sin `map_item_collected` → `{}` → `COLLECTED=0` →
  `percentage 0 %` si `TOTAL>0`, `None` si `TOTAL==0`. No rompe NG+/WorldMap/
  inventory/achievements/checkpoints (campos aditivos).

---

## 12. HUD

**Estado actual:** `HUD.set_porcentaje_items(pct: float | None)` existe
`hud.py:931`, `HUD._porcentaje_items` almacenado, **pero `_draw_*` no existe**
— el porcentaje se calcula en `actualizaciones.py:180` y se guarda, pero nunca
se pinta (gap confirmado).

**Contrato HUD B3:**

- `what`: `percentage` como barra + texto `42 %` + `COLLECTED/TOTAL` opcional
  (ej. `3/4`). Texto universal, no requiere locale nueva (`%` es universal).
- `when`: sólo si `TOTAL > 0`; si `TOTAL == 0` → `set_porcentaje_items(None)` →
  HUD oculta barra/texto (early return).
- `where`: bloque de identidad bajo `NIVEL` bar (ya existe `HUD._draw_nivel`
  bajo `carga_bar_rect`), o como nueva barra delgada `item_bar_rect` con
  mismo lenguaje `_dibujar_barra_moderna`. No crea segunda fila completa,
  respeta `MARGEN`/`reflow`/`scale`/`INTERNAL 1280`.

Ejemplo `0 %` / `25 %` / `50 %` / `75 %` / `100 %`: `pct` 0.0→0.25→0.5→0.75→1.0
con `round`, barra degradada azul → dorado al 100 % + halo si se desea.

**No tocar** en esta fase contrato: sólo definir. Implementación posterior
crea `HUD._draw_porcentaje_items` y lo llama en `HUD.draw()` sin mover
`portrait`/`vida`/`estamina`/`carga`.

---

## 13. WORLD MAP

- **No implementar UI de World Map en B3 fase contrato.** Sólo definir.
- El porcentaje es **per-map**, por lo que el World Map podría mostrar por nodo
  (`WorldMapScene.construir_nodos()` `world_map_scene.py:100`) el `map_item_collected`
  de cada `stage_id` como `42 %` junto al nombre.
- Decisión: **defer** — HUD primero (juego en curso), World Map después si
  diseño lo pide. La obligación B2 `WORLD PROGRESS PRESERVED` sigue: B3 no debe
  romper `completed_stages` ni `zone_flags`.

---

## 14. EDGE CASES

| Caso | TOTAL | COLLECTED | Comportamiento |
|---|---|---|---|
| `TOTAL=0` (mapa sin ítems) | 0 | 0 | `percentage=None`, HUD oculta, no división |
| `COLLECTED=0, TOTAL>0` | >0 | 0 | `0 %`, barra vacía |
| `COLLECTED==TOTAL>0` | >0 | ==TOTAL | `100 %`, barra llena + halo opcional |
| `COLLECTED > TOTAL` | >0 | >TOTAL | clamp a 100 %, log warning, no crash |
| `duplicate collection` (mismo `item_id` dos veces) | — | — | set ignora duplicado, no suma |
| `same item twice` (re-enter tras recoger) | — | — | objeto ya `recogido=True` al cargar, no reaparece |
| `map reload` (morir sin guardar) | — | — | `COLLECTED` en memoria vuelve a último save; no se persiste hasta `save()` |
| `death` / `respawn` | — | — | `recogido` persiste en memoria del escenario; checkpoint no resetea colección |
| `checkpoint` | — | — | colección no es checkpoint, es save (ver anti-exploit) |
| `save` | — | — | `SaveManager.save()` vuelca `map_item_collected[map_id]` |
| `load` | — | — | hidrata `recogido` desde save |
| `new game` | — | — | nuevo slot → `map_item_collected={}` → `0 %` |
| `NG+` | — | — | NG+ no resetea `map_item_collected` (colección persiste por slot, no por vuelta); si diseño quiere reset en NG+, debe decidirse y documentarse, por defecto **persiste** |

Todos deben tener test (ver § Test Plan).

---

## 15. COFRES Y CERRADURAS — semántica investigada

- `Cofre` `interactables.py:144` con `contenido` y `key_id` y `abierto`:
  - Si `contenido == ""` → cofre vacío → **no es ITEM** (decorado).
  - Si `contenido != ""` → **1 ITEM** (el contenido). `abierto==True` ⇔ `COLLECTED`.
  - No es `contenedor + ítem separados`; es una unidad.
- `Cerradura` `interactables.py:77` con `key_id`, `abierta`, `consume_llave`:
  - **Nunca es ITEM**, aunque requiera llave. La llave sí es ITEM.
  - `abierta==True` no suma a `COLLECTED`; es desbloqueo, no colección.

Conclusión: la fórmula actual `total = recogibles + cerraduras + cofres`
es **semánticamente incorrecta** y hace 100 % imposible si hay puertas.

---

## 16. HEART PIECE

- `Inventory.ItemDef id="heart_piece"` `inventory.py:192` →
  `max_hp_bonus=0.25`, `description 1/4 corazón`.
- Como `Pickup` con `item_id="heart_piece"` cuenta como **1 ITEM** por pieza.
- `4 pieces = +1 corazón` es efecto de inventario (`get_total_hp_bonus` suma
  `0.25*count`), no de porcentaje. B3 no altera esa regla; sólo lo cuenta.
- No implementar modificación de HeartPiece aquí; sólo clasificarlo como ITEM
  si aparece en TMX.

---

## 17. BONFIRE

Confirmado **no coleccionable:**

- `Fogata` `interactables.py:157` es `rect + mensaje + usada`, sin `recogido`.
- `InteractableSystem._usar_fogata` `interactable_system.py:456` cura (`PLAYER_HEALED
  5.0`), emite `CHECKPOINT_REACHED` y `SFX_CHECKPOINT`, marca `usada=True`,
  pero **no** emite `INTERACT_ITEM_PICKED` ni toca `Llavero`/`Inventory`.
- Es `INTERACTABLE` reutilizable (B4), no `ITEM`. Evidencia: no tiene
  `item_id`, no entra en `StageData.recogibles`.

---

## 18. ANTI-EXPLOIT

```
collect → save → reload → collect again → debe dar 0 duplicado
```

- Modelo set lo impide: segunda colección ve `item_id in map_item_collected[map_id]`
  y no suma; si el objeto ya está marcado `recogido=True` al hidratar, ni siquiera
  aparece interactuable.
- Drop de enemigo con `soltar_botin(entity_id)` ya usa `set _botin_soltado`
  para no pagar dos veces por el mismo cadáver (`interactable_system.py:313`).
- Guardar sin recoger no crea entrada; cargar sin haber guardado tras recoger
  revierte al último save (pérdida de progreso, no duplicación) — comportamiento
  estándar.

Determinismo: mismo `MAP + SAVE + COLLECTED SET` → mismo `PERCENTAGE`,
independiente del orden de carga (`round` no depende de orden, set es
conmutativo).

---

## 19. PERFORMANCE

- `TOTAL` se calcula **una vez** al cargar (`StageLoader`), cacheado en
  `StageData` (ej. `stage.total_item_ids` o `stage.item_total`).
- `COLLECTED` es `len(set)` o conteo de flags ya hidratados; no itera TMX por
  frame. Actual `actualizaciones.py:182 len(...)` por frame es waste y debe
  eliminarse.
- No recalcular estructuras caras por frame.

---

## 20. TEST PLAN

Mínimo antes de implementar:

```
test_total_items                    — TMX con 0/1/muchos → TOTAL correcto (excluye puertas)
test_item_collected                 — recoger Pickup marca recogido + incrementa COLLECTED
test_chest_collected                — abrir Chest con contenido marca COLLECTED
test_chest_empty_not_counted        — Chest vacío no suma TOTAL ni COLLECTED
test_door_not_counted               — Door en TMX no entra en TOTAL
test_percentage_zero                — 0/TOTAL → 0 %
test_percentage_partial  (1/3,2/3)   — round(33), round(67)
test_percentage_complete             — COLLECTED==TOTAL → 100 %
test_total_zero_safe                — TOTAL 0 → None, no ZeroDivision
test_map_item_persistence           — recoger → save → load → sigue recogido, no reaparece
test_map_items_do_not_mix_between_maps — stage0 2/3 ≠ stage4_1b 5/10, aisla por map_id
test_new_save_without_item_state    — slot nuevo sin map_item_collected → 0 %
test_old_save_migration             — save v5 sin campo → migrado a {} → 0 % sin crash
test_duplicate_collection_ignored   — recoger mismo id dos veces → count no sube
test_collected_gt_total_clamped     — corrupción → clamp 100, no crash
test_map_reload_without_save        — recoger sin save → reload → perdido (no exploit)
test_hud_shows_only_when_total_gt_0 — TOTAL 0 oculta, TOTAL>0 muestra 0 %..100 %
test_bonfire_not_counted            — Fogata no suma TOTAL
test_heart_piece_counts_as_one      — heart_piece Pickup = 1 ITEM
```

---

## 21. ACCEPTANCE CRITERIA

- Contratos cerrados para `ITEM, COLLECTED, TOTAL, 100%, PERCENTAGE, MAP_ID, ITEM_ID, COFRE, CERRADURA, HEART PIECE, BONFIRE, PERSISTENCE MODEL, SAVE VERSION, MIGRATION, ANTI-EXPLOIT, HUD, WORLD MAP, EDGE CASES`
- `docs/features/item_completion.md` existe y es verificable contra código `file:line`
- Tests diseñados (lista arriba) antes de tocar `SaveData`
- Implementación posterior debe pasar `B3 = BLOCKED_FOR_IMPLEMENTATION` → `READY` sólo tras contrato

---

## 22. ARCHIVOS PARA IMPLEMENTACIÓN (no tocar aún)

```
src/framework/stage/stage_objetos.py   (añadir tmx_object_id en Recogible/Cofre)
src/framework/stage/stage_data.py      (cache ITEM ids, total)
src/framework/stage/interactables.py   (campo tmx_object_id)
src/framework/stage/interactable_system.py (usar map_item_collected para hidratar)
src/engine/core/save_data.py           (map_item_collected: dict[str, set[str]], SAVE_VERSION bump si se decide)
src/engine/core/save_manager.py        (volcar/aplicar map_item_collected)
src/engine/ui/hud.py + hud_builder.py  (barra/texto porcentaje, no reflow)
src/framework/scenes/stage_parts/actualizaciones.py (cache total, eliminar len por frame)
tests/test_item_completion.py          (20 tests arriba)
assets/maps/*.tmx                      (no cambiar, sólo leer)
```

Riesgo: bajo (UI delta + persistencia set, sin tocar renderer/camera/Zone4/NG+)

---

## 23. CONTRATO CERRADO

Ver `docs/B3_ITEM_COMPLETION_CONTRACT_REVIEW.md` para análisis de implementación actual,
problemas semánticos, modelos rechazados y plan de migración.

