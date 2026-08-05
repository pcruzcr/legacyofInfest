---
document_id: "LOI-FALTA-87"
title: "Reporte de lo que falta por completar"
tags: ["pendiente", "qa", "estado", "auditoria"]
source: "docs/87_REPORTE_DE_LO_QUE_FALTA.md"
date_processed: "2026-08-04"
---

# Reporte de lo que falta por completar

**Fecha:** 4 de agosto de 2026
**Qué es:** la respuesta a la lista de verificación de sistemas, sistema por
sistema, con lo que se ejecutó para comprobarlo. Complementa a
[[76_PLAN_DE_CIERRE.md]], que es el plan; esto es **el estado**.

**Método.** Nada de esto sale de leer documentación. Cada fila se comprobó
ejecutando el código o midiendo el árbol el 4 de agosto de 2026. Donde el
documento y el código no coincidían, se corrigió el documento.

---

## 0. Resumen para quien tiene prisa

| Sistema | Estado | Lo que falta |
|---|---|---|
| Boss Rush | ✅ **Completo** | Superposición de interfaz (rótulos, marcador en pantalla) |
| Speedrun | ✅ **Completo** | — |
| Rendimiento / GPU | ✅ **Completo salvo una pieza** | `SpriteBatch` (no existe) |
| Monedas al matar | ✅ **Completo** | — |
| Experiencia al matar | ✅ **Completo desde hoy** (AUD-267) | — |
| **Árbol de habilidades** | ❌ **NO EXISTE** | Todo: nodos, coste, efectos y pantalla |
| Tienda | ✅ **Completo** | — |
| Inventario | ✅ **Completo** | — |
| Transiciones entre escenas | ✅ **Completo** | — |
| **Mapa del mundo** | ✅ **Reparado hoy** (AUD-266) | — |
| Guardado (JSON) | ⚠️ **Funciona, y está repartido** | Unificar: la partida no incluye inventario ni logros |
| Jefe Gavilán | ⚠️ **45 % de la rúbrica** | Asignación abierta **para estudiantes** |

**Lo único que no existe en absoluto es el árbol de habilidades.** Todo lo
demás está construido; lo que faltaba era cableado, y hoy está puesto.

---

## 1. Modos de juego

### Boss Rush — completo (AUD-261, GAP-030 cerrado)

Lo que se midió: `advance_to_next()` y `record_hit()` **no tenían llamante**
fuera de su módulo, así que la puntuación nunca se calculaba y `hits_taken` se
quedaba en 0. `_carry_over_health` se ponía a 0.0 en el constructor y otra vez
en `start()`, sin getter ni setter: el arrastre de vida no existía **ni dentro
del módulo**.

Hoy lo conduce `StageScene`, que es la única que sabe cuándo empieza un
combate, cuándo el jugador recibe un golpe y cuándo cae el jefe:

* `acreditar_combate()` guarda con qué se sigue y avanza;
* la salud se arrastra con `CURACION_ENTRE_COMBATES`, **una constante con
  nombre** — el arrastre puro deja sin vida en el tercer jefe;
* `registrar_tiempo()` acumula con el `dt` **sin escalar**, para que el tiempo
  bala no regale puntuación.

**Falta:** la superposición de interfaz — rótulos de jefe, marcador en pantalla
y pantallas intermedias. Es lo único que `docs/44` §4 sigue marcando en ❌.

### Speedrun — completo

`SpeedrunTimer` tiene `start`, `stop`, `split`, `save`, `get_splits` y
`get_formatted_time`, y los usa el juego: `stage_scene.py` registra la marca al
completar (`registrar_marca`, AUD-231) y `leaderboard_scene.py` la lee. El
fantasma de la mejor carrera se graba y se dibuja (AUD-142). Nada pendiente.

---

## 2. Rendimiento y GPU

Está todo lo que se puede aprovechar **en esta máquina**, y conviene decir por
qué esa frase importa:

| Pieza | Estado |
|---|---|
| Tubería GL completa (doc 74) | ✅ bloom, viñeta, aberración cromática, refracción, rayos volumétricos |
| Daltonismo en GPU | ✅ **desde hoy** (AUD-252): el sombreador estaba escrito y **jamás se ejecutaba** |
| `PresentadorGPU` | ✅ existe, **apagado por defecto** |
| Atlas de sprites | ✅ (AUD-138) |
| `SurfacePool` | ✅ y en uso |
| Enjambre de balas en NumPy | ✅ y **ya se usa** (AUD-263): 2.000 balas de 12,94 ms a 0,072 ms |
| `SpriteBatch` | ❌ **no existe** |

**La medición que manda (AUD-148):** en una máquina sin tarjeta real, el bloom
en GPU sale **5× más lento** que en CPU (8,3 ms contra 1,7), porque SDL cae a
software. Por eso `PresentadorGPU` está apagado por defecto y no es un
descuido. Para medirlo donde toque: `python scripts/bench_gpu_postproc.py`.

---

## 3. Progresión y economía

### Monedas al derrotar enemigos — completo

`ENEMY_DIED` → `_soltar_botin()` → un recogible con la cantidad que decide
`coins_for()`, la misma lectura de `entity_id` que usa la puntuación. Se recoge
al pasar por encima y entra en el `Inventory`, que persiste a JSON.

### Experiencia al derrotar enemigos — completo **desde hoy** (AUD-267)

Aquí había un hueco real, y grande. `ExperienceSystem` estaba construido entero
desde AUD-249 —tabla por tipo derivada de `_tipo_de()`, curva cuadrática de
nivel, puntos de habilidad— y **nadie lo instanciaba**. Medido con
`grep -rn "ExperienceSystem" src/` fuera de su módulo: **cero resultados**.
Consecuencia: sin instancia no hay suscripción a `ENEMY_DIED`, así que matar
enemigos **no daba un solo punto de experiencia**, y `SaveData` ni siquiera
tenía dónde guardarla.

Hoy la escena lo enlaza junto a los logros y la puntuación, y el autoguardado
se lleva `exp_total`. Las partidas anteriores se cargan sin tocar nada.

### Árbol de habilidades — **NO EXISTE**

Esto es lo que la lista de QA pedía validar, y la respuesta honesta es que **no
hay nada que validar**:

* no hay clase de árbol, ni nodos, ni pantalla;
* `ExperienceSystem` reparte `puntos` y **no hay forma de gastarlos** — no
  existe un método `gastar`;
* `PLAYER_SKILLS_REQUIRE_UNLOCK` existe y está en `False`; las tres habilidades
  del catálogo (`skill_dash`, `skill_double_jump`, `skill_parry`) las sueltan
  los jefes, que es un mecanismo **distinto** del árbol.

Lo que sí está decidido, y consta en el mensaje de AUD-249: **el árbol no se
paga con monedas**. Las monedas compran lo que se consume o se equipa; la
experiencia compra lo permanente. Si las monedas pagaran las dos cosas, quien
farmee para consumibles se encuentra el árbol regalado y quien gaste en la
tienda se queda sin habilidades sin saber por qué.

**Lo que falta, en orden:** decidir los nodos y su coste en puntos → decidir
qué hace cada uno (y si toca la física, cómo no rompe las 26 entregas) →
`gastar(nodo)` en `ExperienceSystem` → persistir qué nodos están comprados →
la pantalla. Es una funcionalidad, no un cableado: **necesita una decisión de
diseño del curso antes de escribir código.**

---

## 4. Interfaz y menús

**Tienda:** `buy()`/`sell()` con desequipado al vender la última copia,
`ShopScene` con su entrada de menú. Verificado por `tests/test_tienda.py`.

**Inventario:** `collect`, `equip`, `unequip`, tres ranuras (cabeza, cuerpo,
pies), bonificaciones que sólo cuentan si el objeto está equipado (AUD-207),
`InventoryScene`. Verificado por `tests/test_equipar_desde_el_inventario.py` y
`tests/test_inventario_recoleccion.py`.

Los dos completos. 274 pruebas verdes entre escenas, tienda, inventario y
guardado.

---

## 5. Navegación

### Mapa del mundo — **reparado hoy** (AUD-266)

Era el punto urgente de la lista, y el defecto era éste: el mapa abría el
escenario con `scene_manager.replace(cls(...))` y **nunca declaraba la cola de
escenarios**. Al terminar el nivel, `SceneManager._on_stage_complete` incrementa
el índice y llama a `_enter_next_stage()`, que compara contra una cola **vacía**
y cae por la rama de «no quedan escenarios».

**Lo que el jugador veía:** entra al mapa del mundo, elige *2-2 Entrada y
Antenas*, lo completa, y el juego le pone **los créditos finales**. Si la cola
venía de una partida cargada, peor: le mandaba a un nivel sin relación con el
que acababa de jugar.

Arreglado declarando la cola entera —la misma lista que el mapa dibuja y la
misma que pone `story_scene`— con el índice en el nodo elegido. De paso, la
navegación: arriba y abajo saltaban **±2** en una rejilla de **3** por fila,
resto de cuando la lista tenía cinco nodos escritos a mano; ahora las dos
constantes son la misma (`NODOS_POR_FILA`), así que no pueden volver a
divergir.

### Transiciones entre escenas — completo

`TransitionManager` con fundidos, `SceneManager` con pila push/pop/replace y
cola de escenarios. Las 16 escenas de escenario se construyen y entran sin
excepción (comprobado una por una), y las de menú tienen sus pruebas de humo.

---

## 6. Sistema de guardado

**Funciona, y hay que saber cómo está repartido.** No es un solo fichero:

| Qué | Dónde | Por slot |
|---|---|---|
| Escenario, checkpoint, salud, escenarios completados, banderas de mundo, experiencia | `user_data_dir()/saves/slot_N.json` | **Sí** (5 ranuras) |
| Monedas y objetos | `data/inventory.json` | **No — global** |
| Puntuación | `data/score.json` | **No — global** |
| Logros | `user_data_dir()`, por estudiante | **No** |
| Bestiario | `user_data_dir()/saves/bestiary.json` | **No** |

La escritura es **atómica**: fichero temporal, `flush`, `fsync` y `os.replace`,
para que un corte de luz no instale atómicamente una partida corrupta. Una
partida ilegible **avisa** en vez de callarse, y las de versiones anteriores se
migran una vez desde el sitio viejo sin borrarlas.

**Lo que falta, y es una decisión de diseño:** empezar una partida nueva
**conserva** el inventario, las monedas y la puntuación de la anterior, porque
esos tres viven fuera del slot. Para un juego de un jugador con cinco ranuras,
lo esperable es que el saldo y los objetos vayan **dentro** de la partida. No
se cambió aquí porque mover `data/inventory.json` dentro del slot afecta a
cómo se juega y a las entregas que lo leen: es una decisión, no un arreglo.

---

## 7. El jefe Gavilán — asignación abierta

**Sin asignar hoy. El desarrollo completo queda a cargo de los estudiantes.**

`BossGavilan` existe con la fase 1 —la órbita paramétrica de §5.3— y saca
**45 %** de la rúbrica de jefes; el venado de referencia saca 100 %. Esos 55
puntos son la tarea: fases 2 y 3, los ocho patrones de ataque de §5, puntos
débiles, telegrafía y los dos sonidos que ya tienen fichero y esperan emisor.

El detalle completo, con la tabla de lo hecho y lo que falta, está en
[[17_BOSS_SPEC.md]] §0. **No lo completa el motor**: `src/stages/` es código de
estudiantes (invariante 1 de `CLAUDE.md`).

---

## 8. Lo que sigue abierto, en una lista

Por orden de lo que más se nota jugando:

1. **Árbol de habilidades** — no existe. Necesita decisión de diseño primero.
2. **Interfaz del Boss Rush** — rótulos y marcador en pantalla.
3. **Unificar el guardado** — inventario y puntuación dentro del slot.
4. **`stage_scene.py`** — 1.900 líneas contra un presupuesto de 1.500
   (GAP-015). Aplazado mientras otra sesión edite el mismo fichero.
5. **`SpriteBatch`** — no existe; el atlas sí.
6. **`LuaScriptEnemy`** — completo y probado en aislamiento, sin conectar
   (AUD-022). Depende de si el guion en Lua entra en el curso.
7. **Jefe Gavilán** — asignación de estudiante (§7).
8. **Los cinco sonidos de jefe sin emisor** — `SFX_BOSSES_GAVILAN_DIVE`,
   `_MASK_BEAM`, `PABURU_WAVE`, `RELIC_APPEAR`, `REY_SPIT`, `REY_SPLIT`.
   Pertenecen a ataques de jefes de estudiantes.

---

## Documentos relacionados

- [[76_PLAN_DE_CIERRE.md|El plan del que sale este estado]]
- [[75_BIBLIA_TECNICA.md|La referencia técnica completa]]
- [[17_BOSS_SPEC.md|Especificación de jefes — §0, el aviso del Gavilán]]
- [[44_BOSS_RUSH_MODE.md|Boss Rush]]
- `KNOWN_GAPS.md` — los huecos abiertos
