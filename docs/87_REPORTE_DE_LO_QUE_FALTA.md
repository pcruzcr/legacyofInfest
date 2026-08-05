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
| Boss Rush | ✅ **Completo** | Pantallas intermedias entre combates (decoración) |
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

~~**Falta:** la superposición de interfaz.~~ **HECHO (AUD-274)**: franja de una
línea arriba con el combate, el jefe, los puntos y los golpes, visible **sólo**
con el modo activo. Quedan las pantallas intermedias entre combates, que son
decoración y no información.

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
2. ~~Interfaz del Boss Rush~~ — **HECHO (AUD-274)**.
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

---

## 9. Auditoría de sistemas base (2026-08-04, segunda pasada)

Medido ejecutando el motor, no leyendo documentación.

### 9.1 Jugador — completo

**26 estados en el enum, 26 con clase instanciable.** Ninguno huérfano.

> **Corrección de método.** La primera pasada de esta auditoría dio tres
> estados «sin clase» —`CHARGE_ATTACK`, `CLIMBING`, `ZIPLINE`— y era **falso**:
> los implementan `ChargingState`, `TrepandoState` y `TirolesaState`. El script
> casaba por nombre de clase en vez de por `state_enum`. Queda escrito porque
> es el mismo error que este repositorio lleva un mes corrigiendo: una lista de
> hallazgos automáticos no es una lista de defectos hasta que alguien la
> comprueba contra el código.

### 9.2 Enemigos — completo

13 estados de IA, 8 arquetipos, 21 especies con nombre. Sprites por **zona**
—`enemy_zone{N}_walk/hurt/die/fly/shoot/aim/fire`, 7 ficheros por zona × 3
zonas— que es como los carga `_load_zone_sprites`. IA de pelotón con
scikit-learn y predictor de trayectoria, los dos presentes.

> Segunda corrección del mismo tipo: buscar sprites por nombre de arquetipo
> (`*walker*`, `*flying*`…) daba ocho falsos negativos. El motor no los nombra
> así.

### 9.3 VFX y entorno

Los diez módulos de `vfx/` existen y se usan. Lo que se midió del entorno:

| Qué | Medido |
|---|---|
| Día contra noche | Factor de luz **1,00 al mediodía y 0,52 a medianoche**, con color propio: `(255, 252, 245)` contra `(165, 180, 235)`. El amanecer queda en 0,65 |
| Estaciones | Las cuatro, cada una con **tinte propio** y clima por defecto: primavera `clear`, verano `clear`, otoño `rain`, invierno `snow` |
| Lluvia, nieve, niebla | Partículas, velo de color y viento lateral |
| **Rayos y relámpagos** | **Faltaban por completo** → **HECHO (AUD-270)** |
| **Ambiente de lluvia y tormenta** | **Sin fichero de audio** → **HECHO (AUD-271)** |
| Niebla de guerra | Se nota: el centro revelado queda a alfa 0 y la esquina a 220. `update()` **es un hueco vacío a propósito** — el sistema es de revelado, no animado |

**AUD-270 — la tormenta no relampagueaba.** `storm` era lluvia con viento: cien
partículas inclinadas y un velo gris, sin una sola referencia a un rayo en todo
el módulo. Una tormenta que no relampaguea se lee como lluvia fuerte, y `storm`
es justamente el clima del clímax de `stage0`. Ahora hay fogonazo a pantalla
completa con espera aleatoria entre 4 y 11 segundos —un rayo cada N exactos
deja de dar miedo a la tercera vez, porque el jugador lo empieza a contar—,
decaimiento de 0,35 s y alfa máximo 110 sobre 255: aclara la escena sin cegar.

**AUD-271 — `rain` y `storm` sonaban en silencio.** Eran los dos climas que
`SIN_ASSET` declaraba sin fichero desde AUD-145. Declararlo en voz alta era lo
correcto mientras no existieran; ahora se generan por el mismo camino que todo
el audio del proyecto, más un trueno. `SIN_ASSET` queda vacío y **no se
retira**: el mecanismo hará falta el día que alguien añada un clima nuevo.

### 9.4 Cámara — completo

Tres modos (`seguir`, `zona_muerta`, `sala`), anticipación de mirada
(*look-ahead*), sacudida, y `CameraLock` por zona con el arreglo de AUD-143 —el
`rect` se guardaba y no se leía nunca, así que una sola zona congelaba la
cámara en todo el nivel.

### 9.5 Narrativa e interfaz

| Requisito | Estado |
|---|---|
| Cinemáticas sin errores | ✅ `CutsceneSystem` + `CutsceneDirector`, guion en texto, no bloquean |
| Caja de diálogo abajo | ✅ `h - alto - 10` |
| Imagen del personaje | ✅ `_retrato()`, con rectángulo de reserva si falta el retrato |
| Texto progresivo | ✅ máquina de escribir, con adelanto al pulsar (AUD-128) |
| **Texto largo dividido** | **Se recortaba en silencio** → **HECHO (AUD-269)** |
| **Ocultar mensajes de depuración** | **134 avisos salían por consola** → **HECHO (AUD-268)** |

**AUD-269 — un diálogo largo se recortaba.** `draw` dibujaba líneas hasta
llenar el cuadro y hacía `break`: **lo que no cabía no se mostraba nunca**. Sin
aviso ni flecha; el jugador leía media frase, pulsaba ENTER y el resto se
perdía, y un guionista que escribiera un párrafo en
`data/dialogues/<stage>.json` no tenía forma de enterarse. Ahora se **pagina**:
el texto se parte en páginas del alto del cuadro —calculado, no fijo, para que
la escala de accesibilidad al 2,0× no vuelva a recortar—, ENTER avanza de
página antes que de nodo, la máquina de escribir se reinicia en cada una, y el
indicador dice `[ENTER] 1/3`.

**AUD-268 — la consola escupía avisos mientras se jugaba.** El proyecto **no
configuraba el logging en ninguna parte**: sin `basicConfig`, Python instala su
manejador de último recurso y escribe todo lo de `WARNING` arriba en la
consola. Este árbol tiene **134 `logger.warning`**, muchos en rutas normales de
juego.

Los avisos **no se borran**: son correctos, y este repositorio lleva un mes
cazando defectos que fallaban en silencio —AUD-055, AUD-127, AUD-149—. Lo que
cambia es el destino: el registro completo va a
`user_data_dir()/legacy_of_infest.log` y la consola queda limpia.
`python main.py --debug` los devuelve a la pantalla para quien esté
diagnosticando, que es la única persona que quiere verlos.

---

## 10. Viabilidad de las mejoras de arquitectura

Cada una medida contra el árbol de hoy, no contra la intención.

### 10.1 Partir `stage_scene.py` — **viable, y ya empezado**

**Medido: 1.906 líneas** contra un presupuesto de 1.500. La partición en mixins
existe desde AUD-152 (`stage_parts/`: ambiente, señales, fantasma, dibujo de
mecánicas, y `rush` desde AUD-261) y el fichero volvió a crecer.

**Viable, y el patrón está probado.** Lo que hay que saber antes de seguir:

* los mixins mueven texto y **no cambian nada más** — `self` sigue siendo la
  misma escena y las subclases de los estudiantes siguen sobreescribiendo los
  mismos métodos. Convertirlos en colaboradores exigiría pasarles media docena
  de referencias y **rompería las 26 entregas**;
* los candidatos naturales que quedan: la carga del TMX con el montaje de
  sistemas, y el dibujado;
* **está aplazado por acuerdo** mientras otra sesión edite el mismo fichero.

### 10.2 Arquitectura multi-motor (`loi-math`, `loi-physics`, `loi-render`) — **inviable hoy**

**Medido: 147 aristas de importación entre paquetes y 24 pares con ciclo.**
Entre ellos:

```
src.engine.core        <-> src.framework.entities
src.engine.core        <-> src.engine.audio / render / input / scene / scenes
src.framework.entities <-> src.framework.stage
src.framework.entities <-> src.stages.boss_venado   <- el motor importa una entrega
```

Ese último es el que decide: para publicar paquetes independientes habría que
cortar **veinticuatro acoplamientos bidireccionales**, uno de ellos entre el
motor y código de estudiante. Y `docs/72` ya lo evaluó por el otro lado:
partirlo en paquetes pip **rompería las 26 entregas**, que importan
`src.framework...` por ruta absoluta.

**Recomendación: no ahora.** Lo que sí es viable y barato es lo que ese número
mide de verdad — **reducir los ciclos uno a uno**, empezando por
`engine.core -> framework.entities`, que no debería existir en ningún caso.

### 10.3 GPU batching de más de 2.000 sprites — **viable, y medido en contra**

La tubería GL existe entera (doc 74) y el atlas también (AUD-138). Lo que hay
que pesar antes de migrar el dibujado:

* **AUD-148, medido:** en una máquina sin tarjeta real el bloom en GPU sale
  **5× más lento** que en CPU (8,3 ms contra 1,7), porque SDL cae a software.
  Por eso `PresentadorGPU` está apagado por defecto;
* **AUD-138, medido:** el atlas **no** acelera el dibujado en la ruta software
  (2,06 -> 2,35 ms). Lo que gana es carga (3×) y `blits()` (16 %);
* `SpriteBatch` **no existe**. Es la pieza que falta.

**Recomendación: viable con una condición** — medir primero en la máquina
destino con `python scripts/bench_gpu_postproc.py`. Migrar el dibujado a GPU en
las máquinas del laboratorio, si son como la de medida, **empeoraría** el
fotograma. El 63 % de CPU en dibujado es real; que la GPU lo arregle *aquí* no
está demostrado.

### 10.4 Pooling de memoria — **la mitad ya está**

`SurfacePool` existe (`engine/utils/surface_pool.py`) y **lo usan**
`player.py`, `enemy_base.py`, `enemy_shooter.py` y `tutorial_overlay.py`. Hay
benchmarks dedicados: `test_surface_allocation_vs_pool`,
`test_gc_collections_per_frame`, `test_tracemalloc_peak_on_burst`.

**Lo que falta es el pooling de entidades.** Viable y de bajo riesgo: los
proyectiles y las partículas ya se dan de baja por índice —`EnjambreDeBalas`
mantiene una pila de ranuras libres— así que el patrón está en la casa.

---

## 11. Hoja de ruta V2 — viabilidad

| Propuesta | Veredicto | Por qué |
|---|---|---|
| Módulo `loi-physics` aparte | **No ahora** | Mismo problema que §10.2. La física **sí** se puede aislar *dentro* de `src/framework/`, sin publicarla como paquete |
| Rejilla espacial y *raycast* | **Viable** | Aditivo; no toca el contrato de colisión actual |
| Pymunk (cuerpos rígidos) | **No recomendado** | `pymunk` se **retiró** de las dependencias. Volver a meterlo cambia la física de los 16 mapas entregados y calificados — invariante 2 |
| Pendientes (*slopes*) | **Viable, con coste** | Necesita normales de superficie y proyección de velocidad, y **cambia la resolución de colisión**, que es el sistema del que dependen las 26 entregas. Hay que hacerlo aditivo (un tipo TMX nuevo) o no hacerlo |
| Capas de profundidad y escala Z (2.5D) | **Viable** | Es dibujado, no física. `docs/62` C2 ya lo evaluó: 2.5D es factible, 3D no |
| ~~Más de 3 niveles de parallax~~ | **HECHO (AUD-272)** | Cinco capas (`sky`, `deep`, `far`, `mid`, `near`), con la velocidad atada al **nombre** y no al índice de carga. `sky` y `deep` opcionales y silenciosas |
| *Normal mapping* en GPU | **Viable, sin datos** | Requiere un mapa normal por sprite: es trabajo de arte, no de motor |
| Bajar `ambient_light` a 0,35 | **Cuidado** | `docs/60` §17 lo midió: con 12 luces en 100 baldosas la noche es legible al 45 %; con 7, **24 % e injugable**. `MIN_AMBIENTE = 0.45` existe por eso. Bajarlo sin añadir focos deja niveles a oscuras |
| God rays y bloom encendidos | **Ya existen** | AUD-226 y AUD-224, activables desde el TMX |
| ~~Sombra elíptica bajo los pies~~ | **HECHO (AUD-273)** | Elipse que se encoge y aclara con la altura; el suelo llega por parámetro para no acoplar dibujado y física |
| Sombras 2D proyectadas | **Viable, con coste** | Una proyección por foco y por *collider*: hay que medirla antes de encenderla por defecto |

---

## 12. Documentación, estudiantes y huérfanos — estado

| Punto de la lista | Estado real |
|---|---|
| Deriva documental | **Corregida en esta ronda**: `63` §2 y §4, `52`, `17`, `44`, `60`, `75` y el índice, todos medidos contra el código |
| Ampliar pruebas doc↔código | **Parcial.** Hay guardianes para rutas (111 pruebas), índice, árbol de arquitectura, tipos TMX, recuento de pruebas y cifras de la guía. Sigue siendo **1 documento de 95** con pruebas de contenido (`docs/60`) |
| Traducción de 66 documentos | **Pendiente.** La política vigente es «bilingüe donde hay lector» (invariante 5): traducir los 95 duplicaría la superficie de desincronización. **Traducir los 12 manuales del estudiante es compatible con esa política** y sigue sin hacerse |
| ~~Boss Rush sin acceso desde el menú~~ | **Ya no es cierto.** Entra por menú desde AUD-191 y el modo se conduce entero desde AUD-261 |
| ~~Tiempo bala sin acceso~~ | **Ya no es cierto.** AUD-260: `Action.BULLET_TIME` y propiedad de mapa `tiempo_bala` |
| ~~Reloj musical (F6) pendiente~~ | **Ya no es cierto.** AUD-137: `bpm`/`compas`/`desfase_audio` en el mapa y `patron` en los bloques, con la posición tomada del mezclador |
| Rúbrica que castiga la movilidad | **Parcial.** AUD-192 exime de `design_completable` a los mapas con objetos de movilidad; `classify_gap` sigue fuera de esa exención. Relacionado con GAP-024, decidido en AUD-264 |

---

## 13. Mejoras ya implementadas — registro

Las tres que la lista da por hechas, confirmadas contra el código:

* **Tres relojes independientes.** `DeltaClock` separa `dt` (escalado),
  `dt_mundo` (sin hit-stop) y `unscaled_dt` (tiempo real). Es lo que impide que
  el hit-stop de un golpe congele los láseres y los bloques rítmicos, y lo que
  permite el tiempo bala sin desincronizar la música (AUD-118/119).
* **Heurística `prev_bottom`.** Las plataformas de un solo sentido sólo atrapan
  si los pies estaban al nivel o por encima el fotograma anterior. Y con el
  trabajo del frente paralelo, la resolución en X usa **solape vertical con la
  posición previa** en vez de comparar `tile.top` con el centro del jugador,
  que era justo lo que GAP-002 temía.
* **Independencia de FPS.** Gravedad, fricción y amortiguación multiplicadas
  por `dt`. Con una salvedad medida en AUD-236: `ZonaDeFriccion` actúa como
  escala de velocidad y no como coeficiente, así que andar sobre barro da
  79,20 px/s a 30, 60 y 120 fps por igual — sólo el deslizamiento sin impulso
  difiere.

---

## 14. Lo viable, implementado (2026-08-04, tercera pasada)

De la lista de §10 y §11, lo que se ha hecho y lo que queda, para que nadie
tenga que cruzar dos secciones:

| Ítem | Estado |
|---|---|
| Más de 3 capas de parallax | **HECHO (AUD-272)** |
| Sombra elíptica bajo los pies | **HECHO (AUD-273)** |
| Interfaz del Boss Rush | **HECHO (AUD-274)** |
| ~~Pooling de partículas~~ | **HECHO (AUD-275)** — 0,658 → 0,453 ms/fotograma, 1,45× |
| ~~Rejilla espacial y *raycast*~~ | **HECHO (AUD-276)** — aditiva; el raycast es lo que faltaba para línea de visión y sombras proyectadas |
| ~~Capas de profundidad / escala Z (2.5D)~~ | **HECHO (AUD-277)** — propiedades `profundidad_min`/`max`, apagadas por defecto; no toca la física |
| ~~Sombras 2D proyectadas desde los focos~~ | **HECHO (AUD-278)** — medida: hasta 4-5 focos cabe (+6,8 ms con 3.000 obstáculos); con 8 no. Apagada por defecto |
| Pendientes (*slopes*) | Pendiente (*viable con coste*: cambia la resolución de colisión, hay que hacerlo aditivo) |
| `SpriteBatch` | Pendiente (*medir primero* en la máquina destino: AUD-148) |
| Reducir ciclos de importación | Pendiente |
| Partir `stage_scene.py` | Aplazado por acuerdo |

**El pooling, resuelto y medido (AUD-275).** La sospecha era `np.concatenate`
en `emit`, y el perfil dijo otra cosa: **`update` se llevaba el 74 %**. Lo que
hacía era compactar con máscara booleana —diez arreglos nuevos por emisor y por
fotograma— más reconstruir una lista de Python de 3.840 tuplas de color
elemento a elemento. AUD-214 lo había rozado años atrás y lo dejó escrito.

Capacidad reservada, compactación en su sitio con `np.take(..., out=)` y el
color en un arreglo `(capacidad, 3)`. **0,658 → 0,453 ms/fotograma, 1,45×**, con
los píxeles idénticos comprobados contra el oráculo de AUD-214.

Queda pendiente el pooling de **proyectiles**, que es mucho menor: tres por
tirador como mucho.

**Y una corrección de método, para la próxima.** La primera versión de
`sombras_proyectadas.py` afirmaba que la rejilla de AUD-276 «es lo que lo
vuelve asumible». Al medirlo, **no era cierto**: el cuello de botella es el
relleno de polígonos. La rejilla se queda porque es la estructura correcta,
pero lo que acota el coste es un tope explícito por foco. Escribir la
justificación antes de medirla es la forma más fácil de que un documento
vuelva a mentir.
