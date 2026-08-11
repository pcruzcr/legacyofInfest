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
`76_PLAN_DE_CIERRE`, que es el plan; esto es **el estado**.

**Método.** Nada de esto sale de leer documentación. Cada fila se comprobó
ejecutando el código o midiendo el árbol el 4 de agosto de 2026. Donde el
documento y el código no coincidían, se corrigió el documento.

**§15 (5 de agosto de 2026)** responde al backlog de diseño completo —las nueve
categorías, cuarenta y seis propuestas— con el mismo método. Si vienes de esa
lista, empieza por [§15.0](#150-seis-cifras-de-la-lista-que-la-medición-no-confirma):
seis de sus cifras no coinciden con lo medido, y tres de ellas cambian la
conclusión de su propia propuesta.

**§16 y §17 (5 de agosto de 2026)** son lo que se implementó después: los once
puntos baratos y medianos de §15.10 (AUD-279 a AUD-289) y luego los grandes
(AUD-291 a AUD-299), incluido el árbol de habilidades. Incluye
[§16.1](#161-las-tres-veces-que-la-medición-contradijo-a-este-documento), las
tres veces que la medición contradijo a este mismo documento — que es la parte
que conviene leer antes de fiarse de una recomendación de aquí.

**§19 (6 de agosto de 2026)** contrasta la lista con el repositorio una vez más,
porque volvió a llegar encabezada por cinco pendientes que ya no existen. Si
vienes de esa versión, la tabla de [§19](#19-la-lista-contrastada-con-el-repositorio-de-hoy-2026-08-06-quinta-pasada)
es lo único que hace falta leer: cuatro de los cinco se cerraron entre el 5 y el
6 de agosto, y el quinto —«24 pares de ciclos de importación»— nunca fue cierto.
Lo que de verdad queda abierto son **cuatro filas**, en
[§19.2](#192-lo-que-sigue-abierto-de-las-nueve-categorías).

**§20 (6 de agosto de 2026)** cierra esas cuatro: tres implementadas (AUD-304 a
AUD-306) y una que **no se entrega y explica por qué** — componer el fotograma
entero en GPU choca con las invariantes 1 y 2, y la medición que lo demuestra
está en [§20.3](#203-componer-el-fotograma-entero-en-gpu-lo-que-impide-hacerlo-hoy).

**§21 (6 de agosto de 2026)** audita la documentación entera buscando
duplicados, parecidos y reportes inservibles. **No hay nada que borrar**: cero
duplicados sobre los 110 documentos que había entonces, cero pruebas muertas. Lo que sí
apareció son seis cadenas que se veían en español jugando en inglés
([§21.5](#215-los-dos-idiomas-dentro-del-juego-seis-cadenas-rotas-aud-307),
AUD-307) y tres documentos de la raíz sin fila en el índice.

---

## 0. Resumen para quien tiene prisa

| Sistema | Estado | Lo que falta |
|---|---|---|
| Boss Rush | ✅ **Completo** | Pantallas intermedias entre combates (decoración) |
| Speedrun | ✅ **Completo** | — |
| Rendimiento / GPU | ✅ **Completo** | ~~`SpriteBatch`~~ hecho (AUD-302); la ruta de GPU, medida y descartada por ahora (AUD-301, §18) |
| Monedas al matar | ✅ **Completo** | — |
| Experiencia al matar | ✅ **Completo desde hoy** (AUD-267) | — |
| ~~Árbol de habilidades~~ | ✅ **HECHO (AUD-293)** | — |
| Tienda | ✅ **Completo** | — |
| Inventario | ✅ **Completo** | — |
| Transiciones entre escenas | ✅ **Completo** | — |
| **Mapa del mundo** | ✅ **Reparado hoy** (AUD-266) | — |
| Guardado (JSON) | ✅ **Unificado (AUD-292)** y firmado (AUD-295) | — |
| Jefe Gavilán | ⚠️ **45 % de la rúbrica** | Asignación abierta **para estudiantes** |
| Pendientes (*slopes*) | ✅ **Completas (AUD-323 a AUD-328)** | Subir, bajar, saltar, aterrizar con proyección, deslizamiento sostenido y vista cenital (§26) |

~~**Lo único que no existe en absoluto es el árbol de habilidades.**~~ Ya
existe: AUD-293. ~~A 5 de agosto de 2026 **lo único abierto que depende del motor
es medir la ruta de sprites en GPU**~~; esa medición se hizo (§18). A **6 de
agosto de 2026 no queda ningún punto abierto que dependa del motor**: lo que
sigue son tres piezas aditivas que esperan una decisión de diseño, una decisión
de rúbrica, asignaciones de estudiante y decisiones de curso. La lista corta
está en [§19.2](#192-lo-que-sigue-abierto-de-las-nueve-categorías), y la
anterior en [§17.3](#173-lo-que-sigue-abierto-y-ya-es-corto).

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

> Esta lista es la de los sistemas base. La lista **completa y ordenada por
> coste**, que incluye lo de aquí más todo el backlog de diseño, está en
> [§15.10](#1510-lo-que-queda-ordenado-por-lo-que-cuesta).

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

---

## 15. El backlog de diseño, medido (2026-08-05)

Esta sección responde a la lista de mejoras en formato GDD —nueve categorías,
cuarenta y seis propuestas— comprobando **una por una contra el código que hay
hoy**. Ninguna fila sale de leer documentación: cada veredicto trae el fichero,
la constante o el número que lo sostiene.

El resultado corto: **veinticuatro de las cuarenta y seis ya están hechas**,
casi siempre con su `AUD-NNN`. Lo que la lista propone como novedad es, en más
de la mitad de los casos, algo que el motor lleva meses haciendo. Eso no es un
defecto de la lista: es la consecuencia de que nadie tenía un sitio donde mirar
el estado real, que es justamente lo que este documento intenta ser.

### 15.0 Seis cifras de la lista que la medición no confirma

Se comprueban primero porque tres de ellas cambian la conclusión de su propia
propuesta.

| La lista dice | Medido hoy | Cómo se midió |
|---|---|---|
| El salto es «muy vertical, 1,05:1» | **0,95:1** el salto sencillo; **1,90:1** usando el salto aéreo, que ya está dentro del 1,5–2 que la lista recomienda | `JumpEnvelope.from_settings()`: altura 90,25 px, alcance 85,50 px, alcance con salto aéreo 171,00 px |
| El post-procesado «consume el 63 % del fotograma» en CPU | El 63 % es de **otra tabla**: el coste de **8.100 partículas** (`docs/74` §12). El post-procesado **ya está en GPU** desde AUD-229/230 | `docs/74_TUBERIA_DE_GPU.md`: camino GL completo 7,96 → 3,76 ms; todas las pasadas 25,80 → 15,32 ms |
| «24 pares» de ciclos de importación | **17 pares**, y **11 son `title_scene ↔ pantalla que vuelve al título`** — el patrón del menú, no una maraña | Barrido AST de los 202 módulos de `src/`, aristas mutuas |
| «15 especies inalcanzables para el jugador» | **Cero.** Las **21** especies del roster están colocadas en algún `.tmx`, y el bestiario tiene **30 fichas** (21 especies + 9 arquetipos) | `bestiary_registry.SPECIES` cruzado con los `type=` de `assets/maps/**/*.tmx`; `Bestiary.get_all_entries()` |
| Arranque de «3,4 s», a bajar con importación perezosa | Import en frío: **mediana 1,61 s** (mín 1,52, máx 3,22). Y al arrancar **no entra ninguna librería pesada**: `sklearn`, `scipy`, `cv2`, `skimage`, `matplotlib`, `joblib` y `pandas` están todas fuera de `sys.modules` | `pytest tests/benchmarks/test_startup_benchmark.py`; `python -X importtime` sobre `scene_registry` |
| `StageScene` «con más de 1.800 líneas» | **1.923**, y ya hay cinco módulos extraídos en `stage_parts/` | `wc -l src/framework/scenes/stage_scene.py` |

La de la importación perezosa merece una frase más, porque la propuesta se cae
sola: el registro de escenas **ya** construye por cadena y no importa nada
hasta que alguien entra en la pantalla, y `filter_tools` y
`pattern_recognition_tools` importan `scipy` y `sklearn` **dentro de la
función**. El trabajo está hecho; lo que quedaba —medirlo— es esta fila.

### 15.1 Gameplay y *game feel*

| Propuesta | Veredicto | Evidencia |
|---|---|---|
| *Coyote time* | **HECHO** | `PLAYER_COYOTE_FRAMES = 6`, y el contador avanza con `dt * 60.0` para que la ventana dure 100 ms en cualquier equipo y no seis fotogramas de duración variable (`player.py:894-911`) |
| *Jump buffering* | **HECHO** | `player_state.py:63` y `player.py:698-704`: la pulsación se guarda ~5 fotogramas y se dispara al aterrizar |
| Ajustar el arco de salto | **No tocar sin decidirlo antes** | `GRAVITY` y `PLAYER_JUMP_FORCE` recalibran **los 16 mapas ya calificados**. `tests/test_calibracion_del_salto.py` existe como trinquete precisamente para que nadie los cambie sin enterarse. Y con el salto aéreo el arco ya es 1,90:1 |
| *Hit-stop* | **HECHO** | `FUENTE_HITSTOP` en `clock.py`, con los tres relojes de AUD-118/119 para que congelar el golpe no congele la música ni los bloques rítmicos |
| *Knockback* | **HECHO** | `states/damage.py`, `player.py` |
| ~~*Screen shake* **direccional**~~ | **HECHO (AUD-282)** | `apply_shake(..., direccion=)`: onda de un ciclo sobre el eje del golpe, con 25 % de temblor cruzado. Sin el parámetro se comporta como antes. Lo usan el daño al jugador y el pisotón |
| Telegrafiar el ataque enemigo | **HECHO en jefes, parcial en enemigos** | `BossBase` tiene fase de aviso con `0-1` publicado para el HUD (`boss_base.py:429-546`). Los enemigos comunes no tienen ventana de aviso declarada |
| *Spacing* y cajas de ataque | **La maquinaria está; el ajuste es diseño** | Hay `hitbox`/`hurtbox` separadas por entidad y `_attack_timer` por estado. Cambiar los alcances es una decisión de diseño que afecta a las entregas |
| *Pogo* | **HECHO (AUD-134)** | `POGO_IMPULSO = -300.0`, menor que el salto a propósito: no debe ser una forma más rápida de subir |
| *Bash* sobre proyectiles | **NO EXISTE** | Sin coincidencias en `src/`. Es aditivo y de riesgo bajo, pero necesita decidir qué proyectiles admiten impulso |
| Habilidades atadas a jefes | **HECHO (AUD-238)** | El jefe suelta el recogible (aditivo) y `PLAYER_SKILLS_REQUIRE_UNLOCK = False` deja el candado apagado, porque exigir el doble salto rompería niveles ya entregados (invariante 2) |
| ~~Micro-recompensas al recoger~~ | **HECHO (AUD-281)** | Chispas doradas que suben, sonido panoramizado y rebote del contador de monedas. El evento no llevaba ni posición: ahora sí |

### 15.2 Diseño de niveles

| Propuesta | Veredicto | Evidencia |
|---|---|---|
| Iluminación como guía | **Motor listo, mapas no** | El tipo `Light` está en el TMX con sus seis propiedades y `stage0` lo cubre al 100 %. Usarla para marcar la ruta crítica es trabajo de diseño de mapas |
| Métricas de salto estandarizadas | **HECHO como herramienta, incumplido en los mapas** | `JumpEnvelope` + `grade_stage.py` califican los 16 mapas. Hoy hay **13 huecos imposibles en `stage1_2_la_soda`**, 5 en `stage3_4_boss_gavilan`, 3 en `stage3_3_el_patio` y 2 en `hall` y `stage_mecanicas` |
| Válvulas de seguridad (*pacing*) | **NO MEDIDO** | El calificador no tiene métrica de tensión. Añadirla es viable: ya cuenta enemigos, huecos y checkpoints por mapa |
| Densidad y checkpoints | **Confirmado, y es el peor dato de la tanda** | `worst_checkpoint_gap` de `stage2_1_oficinas.tmx` = **3.048,17 px**. El segundo peor es 944,0. No es una tendencia: es un mapa |
| ~~Zonas de *warp*~~ | **HECHO (AUD-287)** | Tipo `WarpZone` con destino obligatorio, enfriamiento y llave opcional. Dos colocadas en el laboratorio |
| ~~Sigilo de tres estados~~ | **HECHO, y ahora con cuatro (AUD-286)** | `tranquilo → sospecha → alerta → búsqueda`. La búsqueda dura 3 s en el último punto visto y sólo se entra desde alerta: desde sospecha haría el sigilo ilegible |
| Fricción variable | **HECHO** | Tipo TMX `FrictionZone` (hielo, miel), con la salvedad medida en AUD-236: actúa como escala de velocidad, no como coeficiente |

### 15.3 Interfaz y dirección de arte

| Propuesta | Veredicto | Evidencia |
|---|---|---|
| HUD minimalista | **Decisión de arte, no de motor** | El HUD dibuja trece elementos (corazones, retrato, estamina, especial, combo, puntuación, tiempo bala, temporizador, jefe, Boss Rush…). Hay pruebas de legibilidad (`test_legibilidad_de_menus`, `test_ui_consistency`) pero ninguna de densidad |
| *Feedback* diegético | **PARCIAL** | Está el parpadeo de invencibilidad. No hay daño visible en el sprite del jugador ni color de arma al cargar |

### 15.4 VFX, partículas y GPU

| Propuesta | Veredicto | Evidencia |
|---|---|---|
| `SpriteBatch` | **PENDIENTE (medir primero)** | AUD-148. Ver la fila siguiente antes de escribirlo |
| Atlas de texturas | **EXISTE Y NO LO USA NADIE — a propósito** | `sprite_atlas.py` está medido: **2.000 blits sueltos 2,06 ms; desde el atlas 2,35 ms**. En el camino de CPU de pygame el atlas sale *peor*. Lo que sí gana es la carga: 200 PNG 12,9 ms → atlas 4,3 ms, y `blits()` 2,06 → 1,74 ms. El atlas es el cimiento de la ruta de GPU, no una optimización de hoy |
| ~~*Culling* agresivo~~ | **HECHO (AUD-279), y la justificación de esta fila era falsa** | En los mapas que hay no gana nada (5,007 ms con / 4,931 sin). Lo que compra es que el coste no crezca con el mapa: 200 enemigos en 10.000 px, **1,52×**. Ver §16.1 |
| *GPU instancing* | **NO APLICABLE HOY** | La tubería GL (`gl_pipeline.py`) es post-proceso a pantalla completa: los sprites siguen yendo por CPU. Sin ruta de sprites en GPU no hay nada que instanciar — es la misma decisión que `SpriteBatch`, no una aparte |
| *Object pooling* de VFX | **HECHO (AUD-275)** | 0,658 → 0,453 ms/fotograma, 1,45×. Más `SurfacePool`, usado por jugador, enemigos y tutorial. Queda el pooling de **proyectiles**, que es pequeño |
| Post-procesado nativo | **HECHO (AUD-229/230)** | Subir el fotograma 10,98 → 0,20 ms; bloom 3,39 → 1,70 ms; todas las pasadas 25,80 → 15,32 ms |
| Sombra elíptica bajo los pies | **HECHO (AUD-273)** | |
| Sombras proyectadas | **HECHO (AUD-278)**, apagadas por defecto | Medido: hasta 4-5 focos cabe (+6,8 ms con 3.000 obstáculos); con 8 no |

### 15.5 Audio

| Propuesta | Veredicto | Evidencia |
|---|---|---|
| ~~*Ducking*~~ | **HECHO del todo (AUD-144 + AUD-284)** | Un efecto crítico baja la música un 30 % durante un segundo —no al 35 % como una voz: bajo un jefe que cae la música es parte del momento—. Cuatro eventos en la lista, y corta a propósito |
| Panoramización 2D | **HECHO** | `AudioManager.play_sfx_at()` calcula el *pan* por la posición en X respecto al centro de la pantalla |
| ~~Gestión de voces (polifonía)~~ | **HECHO (AUD-280)** | Dentro de 40 ms una repetición sube la voz que ya suena en vez de abrir otra; pasada la ventana, tope de tres. Cinco muertes simultáneas = una voz y cuatro refuerzos |
| Reloj musical (F6) | **HECHO (AUD-137)** | `music_clock.py` lee la posición del mezclador; `bpm`/`compas`/`desfase_audio` se declaran en el mapa |

### 15.6 Arquitectura y seguridad

| Propuesta | Veredicto | Evidencia |
|---|---|---|
| Patrón Observer (*event bus*) | **HECHO, y está en todas partes** | `EventBus` con **referencias débiles** (AUD-028) y sin *singleton* de módulo (AUD-019), usado por **38 módulos**. `PLAYER_DIED` ya funciona exactamente como describe la lista |
| Partir `StageScene` | **Empezado y aplazado por acuerdo** | 1.923 líneas, con `ambiente.py`, `dibujo_mecanicas.py`, `fantasma.py`, `rush.py` y `senales.py` ya fuera |
| Contenedor de servicios (DI) | **HECHO en su forma útil** | `GameContext` **es** el contenedor de inyección: entra por el constructor de toda escena. Y **no hay Service Locator que eliminar** — cero coincidencias en `src/`. Un `ServiceContainer` con registro dinámico sería cambiar una inyección explícita por una implícita, que es peor para leer |
| Sistema de plugins | **NO EXISTE** | `lua_script.py` se conserva como cimiento y lo dice en su cabecera. Ojo: un gestor de plugins que deje a los estudiantes extender el motor **es** una decisión de curso, no de ingeniería |
| Hash de integridad en los JSON | **NO EXISTE, y conviene pensarlo antes** | `save_manager.py` escribe con `orjson`, sin firma. Pero el *salt* viviría en el código, y el código lo leen las 26 personas de las que se querría defender: sería ofuscación, no integridad. Sirve para detectar corrupción accidental; no para un tiempo de *speedrun* alterado a conciencia |
| Eliminar `pickle` | **HECHO donde importaba (AUD-035)** | La persistencia usa `orjson`, y `tests/test_seguridad_del_motor.py` lo fija para que nadie lo deshaga. Queda **acotado y documentado** en el modelo de referencia de la Unidad IX (`joblib`), con aviso explícito de que deserializar ejecuta código |
| Carga perezosa | **HECHO** | Ver §15.0 |
| ~~Carga asíncrona en hilo~~ | **HECHO (AUD-288)** | Abrir el laboratorio de la Unidad IX pasa de **2.461 ms de congelación a 2 ms**. No se enganchó a la transición de escenario: medido, ahí no procede (§16.1) |

### 15.7 Herramientas internas

| Propuesta | Veredicto | Evidencia |
|---|---|---|
| ~~Gizmos de depuración~~ | **HECHO (AUD-285)** | F1 añade el vector de velocidad —una predicción a 0,25 s, no la velocidad a escala— y el cono de visión con el barrido aplicado, amarillo o rojo según vea al jugador |
| ~~Monitor de rendimiento~~ | **HECHO (AUD-283), y la consola no la abría nadie** | Es **F11**, no F3 —F3 es `LEARN_PHYSICS`—, y hasta AUD-283 no tenía un solo llamante. Ahora da ms de fotograma, objetos vivos, enemigos simulados de vivos, partículas y las decisiones del escuadrón. La RAM del proceso sigue fuera: medirla en Windows y Linux sin dependencias nuevas obliga a `ctypes` por plataforma |

### 15.8 Arquitectura para enseñar

| Propuesta | Veredicto | Evidencia |
|---|---|---|
| ~~Aislamiento de errores~~ | **HECHO entero (AUD-055 + AUD-289)** | Al cargar, `StageErrorScene` con recarga por `R`. Al ejecutar, la entidad que lanza se retira del nivel con su traza en el registro y su aviso en la consola de F11; el dibujado también. `AISLAR_FALLOS_DE_ENTIDAD = False` vuelve a propagar |
| API estricta para entidades | **HECHO** | `EnemyBase` es plantilla con cinco `@abstractmethod` y ganchos opcionales antes y después del update; `BossBase` hereda de ella. Un estudiante no puede olvidarse de implementar lo obligatorio: falla al instanciar |
| Rúbrica que modele la movilidad | **PARCIAL** | AUD-192 exime de `design_completable` a los mapas con objetos de movilidad; `classify_gap` sigue fuera de la exención (GAP-024) |
| Filtros «hechos a mano» | **HECHO** | `sobel_edge_propio` y `canny_edge_propio` en `filter_tools.py`, con los cinco pasos de Canny escritos, y `cv2` conservado al lado como referencia de rendimiento — que es exactamente lo que la lista pide |
| ~~Visualización de la IA~~ | **HECHO (AUD-283)** | `SquadBrain.stats` ya tiene llamante: la consola de F11 enseña qué fracción de las decisiones sale del modelo y cuántas de las reglas |
| Traducir los 12 manuales | **PENDIENTE** | Compatible con la invariante 5 y sin hacer. Ver §12 |

### 15.9 Accesibilidad y contenido

| Propuesta | Veredicto | Evidencia |
|---|---|---|
| Reasignación de controles | **HECHO** | `KeybindingScene` sobre las 14 acciones de `Action`, con persistencia en el `config.json` del usuario |
| *Hold* en vez de *mash* | **HECHO (AUD-126)** | `hold_to_press` convierte las acciones sostenidas en conmutador, y se activa desde la pantalla de opciones |
| Alto contraste | **PARCIAL** | Modos daltónicos completos, y también en la ruta de GPU (AUD-252, 0,07 ms). Contorno de silueta **sólo para el jugador** (AUD-190). Faltan el contorno de enemigos y los iconos que no dependan del color |
| Interfaz escalable | **HECHO** | `ESCALAS_DE_TEXTO` hasta 2,0, comprobado a 800 × 600 sin recortar diálogos. Más «movimiento reducido» (factor 0,25, no cero, para no borrar la única señal de que el dash ocurrió) y cuatro velocidades de texto (AUD-128) |
| Completar el bestiario | **HECHO** | 21/21 especies colocadas, 30 fichas. Ver §15.0 |

### 15.10 Lo que queda, ordenado por lo que cuesta

> **Los once primeros están hechos** (AUD-279 … AUD-289, 5 de agosto de 2026).
> Lo que se midió al hacerlos —incluidas las dos veces que la medición
> contradijo a esta misma lista— está en [§16](#16-los-once-implementados-2026-08-05).

**Barato y con efecto medible** (un `AUD-NNN` cada uno, sin tocar contratos):

1. ~~***Culling* de actualización y dibujado.**~~ **HECHO (AUD-279).** Y la
   justificación de esta fila era falsa: no era «lo más rentable que queda».
2. ~~**Polifonía en `SoundBank`.**~~ **HECHO (AUD-280).**
3. ~~**Micro-recompensas al recoger.**~~ **HECHO (AUD-281).**
4. ~~**Sacudida direccional.**~~ **HECHO (AUD-282).**
5. ~~**`stats()` del escuadrón en el overlay**, junto a RAM y sprites.~~
   **HECHO (AUD-283)** — y de paso salió que la consola **no la abría nadie**.
6. ~~***Ducking* disparado por SFX crítico.**~~ **HECHO (AUD-284).**

**Medio, y decidible sin romper nada:**

7. ~~**Vectores de velocidad y conos de visión en F1.**~~ **HECHO (AUD-285).**
8. ~~**Estado de evasión en el sigilo.**~~ **HECHO (AUD-286).**
9. ~~**Zonas de *warp*.**~~ **HECHO (AUD-287).**
10. ~~**Enganchar `LoadingScene`.**~~ **HECHO (AUD-288)** — pero **no** en la
    transición de escenario, que era lo que esta fila pedía: medido, ahí no
    procede.
11. ~~**Aislar el fallo de una entidad de estudiante.**~~ **HECHO (AUD-289).**
    Era, como decía esta fila, la de más valor docente de toda la lista.

**Grande, o pendiente de una decisión que no es técnica:**

12. **Pendientes (*slopes*)** — cambia la resolución de colisión (§11).
13. **`SpriteBatch` y la ruta de sprites en GPU** — con ella entran el atlas y
    el *instancing*; sin ella, ninguno de los tres tiene sentido. Medir antes
    (AUD-148), y el monitor del punto 5 es lo que permitiría medirlo.
14. **Reducir los 17 pares de importación mutua** — once son el patrón del
    menú y se resuelven con una importación diferida en `title_scene`.
15. **Partir `stage_scene.py`** — aplazado por acuerdo. AUD-290 le quitó tres
    partes más (1.923 → **1.900** líneas) porque los presupuestos de
    `senales.py` lo obligaron; el presupuesto de 1.500 sigue sin cumplirse y
    su prueba sigue en rojo, igual que antes de esta tanda (§16.2).
16. **Árbol de habilidades** — sigue siendo lo único que no existe en absoluto
    (§0), y necesita decisión de diseño antes que código.
17. **Traducir los 12 manuales del estudiante.**
18. **Sistema de plugins y hash de integridad** — los dos son decisiones de
    curso, y el segundo, tal como se propone, no daría la garantía que promete.

**Y lo que este documento recomienda no hacer:** cambiar `GRAVITY` o
`PLAYER_JUMP_FORCE` para «arreglar» el arco del salto, y sustituir `GameContext`
por un `ServiceContainer`. El primero recalibra dieciséis mapas ya calificados;
el segundo cambia una dependencia visible por una escondida.

---

## 16. Los once, implementados (2026-08-05)

Los puntos 1 a 11 de §15.10, uno por commit, con prueba que falla antes y pasa
después. Lo que sigue es **lo que se aprendió al hacerlos**, que es la parte que
no se puede escribir por adelantado.

| AUD | Qué era | Medida |
|---|---|---|
| **279** | El motor simulaba y dibujaba todo el mapa, mirase donde mirase la cámara | Stage 0: 5,007 ms con culling / 4,931 sin. 200 enemigos en 10.000 px: **10,292 → 6,753 ms, 1,52×** |
| **280** | Cinco muertes a la vez eran cinco copias en fase del mismo fichero | Una voz y cuatro refuerzos, tope de 3 voces por sonido |
| **281** | Recoger una moneda no producía **nada** | Partículas, sonido y rebote del contador; el evento ahora lleva `pos` |
| **282** | La sacudida decía «pasó algo», no «de dónde» | Onda de un ciclo por golpe sobre el eje del impacto |
| **283** | La consola de depuración **no la abría nadie** | F11 (F3 estaba ocupada por `LEARN_PHYSICS`), con ms, objetos vivos y las cuentas de la escena |
| **284** | El *ducking* sólo lo pedía la voz | Efecto crítico: −30 % de música durante 1 s |
| **285** | F1 dibujaba cajas y nada más | Vector de velocidad (predicción a 0,25 s) y cono de visión con su color de alerta |
| **286** | Romper la línea de visión un segundo reiniciaba el mundo | Cuarto estado: búsqueda de 3 s en el último punto visto |
| **287** | No había forma de teletransportar dentro de un mapa | Tipo `WarpZone`, con dos colocados en el laboratorio |
| **288** | La pantalla de carga estaba escrita y sin llamante | Abrir la Unidad IX pasa de **2.461 ms de congelación a 2 ms** |
| **289** | Una entidad de estudiante que fallaba tumbaba la clase | Se retira ella sola, con traza en el registro y aviso en la consola |
| **290** | `senales.py` reventó su presupuesto de 400 líneas al recibir lo de arriba | Tres partes nuevas: `sonido`, `diagnostico`, `cinematicas`. `stage_scene` 1.923 → 1.900 |

### 16.1 Las tres veces que la medición contradijo a este documento

Esto es lo que justifica el método, así que va con nombre y apellidos.

**El culling no era «lo más rentable que queda» (§15.4).** Esa frase salía de que
no existiera, no de haberlo medido. Medido, en los mapas que hay **no gana
nada**: stage 0 da 5,007 ms con culling y 4,931 sin él. Lo que compra es que el
coste deje de crecer con el tamaño del mapa —200 enemigos en 10.000 px, 1,52×—,
y eso importa por el escenario que un estudiante construye, no por los
dieciséis que hay. Se quedó por esa razón, escrita en su módulo.

**Y casi rompe stage 0.** El primer margen fue de 400 px, el doble del alcance de
cualquier proyectil. Cuatro de los nueve enemigos de stage 0 quedaban fuera de
la zona con la cámara en el arranque, y `test_every_enemy_in_stage0_moves` los
encontró convertidos en estatuas. La prueba que existía desde AUD-116 hizo
exactamente su trabajo. El margen es 800 porque el mapa de referencia —el que
copian los estudiantes— tiene que comportarse igual que antes.

**«Enganchar `LoadingScene` en la transición de escenario» (§15.10, punto 10) era
la recomendación equivocada.** Entrar en un escenario cuesta entre 41 ms
(`lobby_datacenter`) y 134 ms (`stage1_3_las_aulas`), 163 en frío: una pantalla
de carga ahí aparece y se va antes de que el ojo la resuelva, y eso no se lee
como «estaba cargando» sino como un parpadeo. Donde sí hacía falta era en el
laboratorio de la Unidad IX, que **congelaba 2.461 ms** importando scikit-learn
en el hilo del dibujado. El umbral de 0,25 s de `LoadingScene` es lo que permite
enchufarla en cualquier sitio sin medir antes: si la carga acaba antes, no se
dibuja ni un fotograma.

### 16.2 Lo que los presupuestos de líneas obligaron a hacer (AUD-290)

`senales.py` estaba **exactamente** en su presupuesto de 400 líneas, así que
AUD-281, AUD-284 y AUD-287 lo pasaron a 503 y pusieron en rojo una prueba que
llevaba verde desde AUD-152. No se subió el número: se partió, y por el eje que
el propio docstring del módulo llevaba años anunciando —«son **dos** familias,
efectos visuales y sonido»—. La mitad sonora entera vive ahora en
`stage_parts/sonido.py`.

De paso salieron dos partes más, y las dos por cohesión y no por tamaño:
`diagnostico.py` (lo que enseña F11 y qué pasa cuando una entidad revienta —
AUD-283 y AUD-289 nacieron el mismo día por el mismo motivo) y `cinematicas.py`
(montar el director de escenas y correrlo).

Efecto en `stage_scene.py`: **1.923 → 1.900 líneas**. Sigue sobre el presupuesto
de 1.500 y su prueba sigue en rojo, que es el estado que ya tenía antes de esta
tanda y que §15.10 punto 15 mantiene aplazado por acuerdo. Lo que no se ha hecho
es empeorarlo.

### 16.3 Y una cosa que apareció por el camino

**La consola de depuración no la abría nadie, y §15.7 la describía funcionando.**
El módulo estaba entero y sin un solo llamante en `src/engine`; la tecla con la
que decía abrirse, F3, es `LEARN_PHYSICS` en el mapa de acciones. El barrido de
huérfanos no lo vio porque busca símbolos que **las pruebas ejercitan y el juego
no invoca**, y lo que no prueba nadie y no usa nadie le resulta invisible. Es un
hueco del barrido que conviene recordar: hay una prueba nueva justamente para
que ese caso ya no sea ciego.

---

## 17. Lo que quedaba, cerrado (2026-08-05, cuarta pasada)

Los puntos 12 a 18 de §15.10 —los «grandes, o pendientes de una decisión que no
es técnica»— más lo que salió al preguntar por ellos. Nueve `AUD-NNN`, del 291
al 299.

| AUD | Qué era | Lo que se hizo |
|---|---|---|
| **291** | El juego sabía tu correo y no cómo llamarte | Apodo propio, `{apodo}` en los guiones y dueño en la tabla de récords |
| **292** | La partida guardaba dónde estabas y no lo que tenías | Versión 3 del esquema: inventario, marcador y experiencia viajan con el slot |
| **293** | **El árbol de habilidades no existía** | Tres ramas de estadística con tope, pantalla y persistencia |
| **294** | La mecánica de un jefe estaba disponible antes de derrotarlo | Candado encendido, con los dieciséis mapas entregados exentos uno por uno |
| **295** | Los JSON del jugador se escribían sin firma | HMAC-SHA256 en partidas y récords |
| **296** | No había forma de extender el motor sin tocarlo | `plugins/`, cuatro ganchos, fallos aislados |
| **297** | Las cuestas había que fingirlas apilando bloques | Tipo `Slope`, integrado en la resolución de colisión |
| **298** | «17 pares de ciclos de importación» | **Cero**. Ver abajo |
| **299** | `stage_scene.py` sobre su presupuesto desde AUD-152 | 1.950 → **1.457** líneas, cuatro grupos cohesivos fuera |

### 17.1 Las tres cifras que volvió a corregir la medición

**Los ciclos de importación no existían (AUD-298).** §15.0 contó 17 pares y
§15.10 recomendó reducirlos. Ese barrido contaba **todos** los `import`,
incluidos los de dentro de una función, y un import diferido no es un ciclo: se
resuelve al llamar, con el árbol ya cargado. Contando sólo los del cuerpo del
módulo —los únicos que producen un `ImportError` circular— salen **cero**. No
había nada que arreglar; había que medir mejor. La recomendación de §15.10 era
trabajo con forma de progreso y sin efecto.

**Encender el candado de habilidades rompe seis mapas de dieciséis, y dos dejan
de poder terminarse (AUD-294).** Medido con `grade_stage`, con y sin salto
aéreo: `stage0` —el mapa de referencia— y `stage3_4_boss_gavilan` se quedan sin
salida alcanzable; `stage1_1`, `stage2_2`, `stage3_3_el_patio` y `stage4_1`
ganan huecos imposibles. Por eso el candado va con una lista de exentos y no
solo. La media de calificación sigue en 79,9 %.

**`exp_total` no bastaba para restaurar la experiencia (AUD-292).** Lo decía el
propio `ExperienceSystem` y nadie lo había leído: los puntos **gastados** no se
deducen de la experiencia. Con sólo el total, cargar una partida devolvía todos
los puntos ya gastados y el árbol se podía comprar dos veces. El slot guarda los
tres números.

### 17.2 Decisiones tomadas, y quién las tomó

* **Traducir los doce manuales: no.** Se mantiene la política de la invariante 5,
  «bilingüe donde hay lector». Queda cerrado, no pendiente.
* **Pendientes integradas en la resolución de colisión, no aditivas.** §11
  recomendaba lo contrario por el riesgo sobre las veintiséis entregas; se pidió
  integrado y así está, con la calificación de los dieciséis mapas como control
  antes y después. Lo que lo hace seguro no es el cuidado: es que ningún mapa
  entregado tiene una sola pendiente, así que el paso nuevo no se ejecuta en
  ninguno de ellos.
* **Hash de integridad: sí, con su alcance escrito.** El *salt* vive en el
  código que leen las veintiséis personas de las que defendería, así que detecta
  corrupción y edición casual, y no a quien quiera alterar su tiempo a
  conciencia. Está dicho en la primera línea del módulo y en la primera de su
  prueba, para que nadie lo cite como lo que no es.

### 17.3 Lo que sigue abierto, y ya es corto

1. **El jefe Gavilán** — 45 % de la rúbrica, y es **asignación de estudiante**
   (§7). No es deuda del motor.
2. ~~**`SpriteBatch` y la ruta de sprites en GPU**~~ — **HECHO (AUD-301,
   AUD-302).** Medido con las dos tarjetas del equipo; el lote de CPU está
   puesto y la ruta de GPU está medida y justificadamente sin poner. Ver §18.
3. **Los cinco sonidos de jefe sin emisor** — pertenecen a ataques de jefes que
   los estudiantes aún no han escrito.
4. **`LuaScriptEnemy`** — completo y probado, sin conectar. Depende de si el
   guion en Lua entra en el curso.
5. **Ampliar las pruebas doc↔código** — sigue habiendo un solo documento de 95
   con pruebas de contenido.

Nada de esa lista es un defecto del motor esperando arreglo: son decisiones de
curso y asignaciones de estudiante. **La medición que quedaba pendiente ya está
hecha** (§18), y con ella no queda ningún punto abierto que dependa del motor.

---

## 18. La GPU, medida con las dos tarjetas (2026-08-06)

El último punto que dependía del motor. §17.3 lo dejó como «medir la ruta de
sprites en GPU antes de escribir nada (AUD-148)», y al medirlo apareció algo que
no estaba en la pregunta: **este equipo tiene dos tarjetas y el juego usaba la
peor**.

### 18.1 El equipo tiene dos, y ninguna herramienta elige la buena

Una Intel HD Graphics 530 integrada y una **Quadro M2200** dedicada. Comprobado:
ni el contexto standalone de ModernGL, ni una ventana OpenGL real de SDL, ni
pasar `device_index`, ni el backend EGL —que esta instalación de `glcontext` no
trae— seleccionan la dedicada. En Windows eso lo decide una preferencia por
aplicación que hay que dar de alta para `python.exe`.

Dada de alta, todo cambia:

| Medida | Intel HD 530 | Quadro M2200 |
|---|---|---|
| Camino GL completo (`docs/74` §4) | 3,76 ms | **1,46 ms** (2,6×) |
| Dibujar 8.000 sprites en GPU | 5,177 ms | **0,898 ms** (5,8×) |
| Bajarlos a una `Surface` | 8,305 ms | **2,020 ms** (4,1×) |

### 18.2 SpriteBatch: qué se hizo y por qué no hay ruta de GPU

Lo que se implementó (AUD-302) es el lote de CPU, `Surface.blits()`, y va donde
el perfil dice que paga: los degradados de los focos y las sombras bajo los
pies, que son los dos sitios donde el número de llamadas **crece con el
contenido**. Las sombras además no cacheaban nada — creaban una superficie y
rasterizaban una elipse por sombra y por fotograma para pintar las mismas ocho
del fotograma anterior. Medido en nuestros dos mapas: `stage4_1` de 6,42 a
5,93 ms, `stage0` dentro del ruido.

AUD-329 intentó añadir el tercer sitio donde las llamadas podrían crecer con
el contenido: el **wrap del parallax** envolvía cada capa con un `blit` por
copia — una capa de 40 px sobre una vista de 800 son veinte llamadas — y se
midió en el mapa real antes de decidir. Con las tres capas de `stage4_1` y
seis copias por fotograma, el lote costaba **2,4-3,0 ms y el `blit` a blit
0,8-1,4 ms**: `Surface.blits()` gana al `blit` suelto a partir de cientos de
llamadas — el banco lo mide a 500-8.000 — y el wrap nunca llega ahí, porque
su tope es ancho de vista entre ancho de capa. Revertido y documentado junto
al código; es el mismo caso que las partículas, al revés.

Y se comprobó lo que no se puede agrupar, con evidencia en lugar de silencio:

* **Estelas** — los residuos comparten la superficie cacheada y piden su alfa
  por punto con `set_alpha`; un lote lee un solo alfa para todas las órdenes
  (verificado: `blit` suelto pinta 77 y 38, `blits` agrupado 77 y 77).
  Agruparlas exigiría copiar la superficie por residuo y por fotograma, que es
  justo lo que F1.4a eliminó.
* **Números de daño** — cada número devuelve su superficie al pool antes de
  poder volcar el lote; agrupar es comprar una copia por número.
* **Partículas** — ya estaba medido (comentario del propio sistema): `blits`
  con cuadrados cacheados mejora un 4 % con 508 partículas, empeora con 2.008,
  y rompe el alfa de `SRCALPHA` porque `blits` mezcla donde `fill` escribe.

El lote se queda donde es transparente, y cada sitio que lo rechaza tiene su
razón escrita junto al código.

**La ruta de GPU está medida y no está puesta.** Con la Quadro gana siempre
dibujando —4,2× con 500 sprites, 10,4× con 8.000— pero el juego dibuja unas
veinte entidades por fotograma, y a esa escala lo que costaría subirlas y
bajarlas es más que dibujarlas en CPU. El día que el fotograma entero se componga
en la tarjeta, la ruta gana desde el primer sprite y el banco de pruebas está
escrito para volver a comprobarlo.

### 18.3 Y una predicción mía que salió al revés

Antes de medir la Quadro escribí que bajar los píxeles de una tarjeta discreta
sería **peor** que de una integrada, porque cruza el bus PCIe mientras que la
integrada comparte la memoria del sistema. Es la clase de razonamiento que suena
bien y hay que comprobar igual: medido, la lectura de vuelta en la Quadro es
**tres veces más rápida** —1,45–2,02 ms contra 5,69–8,31—.

La conclusión que había sacado de esa predicción —«con lectura de vuelta la GPU
no compensa nunca»— era falsa. La buena es que con la dedicada compensa a partir
de unos 1.500 sprites. Es la tercera vez en este reporte que una frase escrita
antes de la medición resulta estar mal; las otras dos están en §16.1.

### 18.4 De paso, dos cosas que la documentación decía mal

* **`docs/74` daba sus milisegundos sin decir de qué tarjeta eran.** Ahora lleva
  el aviso y los dos números.
* **`bench_gpu_postproc.py` explicaba el mal resultado de `PresentadorGPU` con
  «SDL está cayendo a software».** Es falso: sus seis drivers de render
  —direct3d, direct3d11, direct3d12, opengl, opengles2— salen todos como
  acelerados. Lo caro es subir el fotograma entero a una textura nueva en cada
  pasada, y eso no lo arregla una tarjeta mejor. El veredicto de AUD-148 se
  mantiene; su explicación, no.

---

## 19. La lista, contrastada con el repositorio de hoy (2026-08-06, quinta pasada)

La misma lista de §15 volvió a llegar, reordenada y con las erratas de pegado
corregidas, encabezada por un apartado nuevo —«Cosas que faltan por hacer»— de
cinco puntos. Es esa cabecera la que justifica esta sección: **ninguno de sus
cinco puntos describe ya el repositorio**. Cuatro se hicieron entre el 5 y el 6
de agosto, y el quinto nunca fue cierto.

No es reproche a quien la escribió: la lista se redactó contra el estado del 4
de agosto y el trabajo de §16, §17 y §18 ocurrió después. Se anota aquí porque
una lista de pendientes que sobrevive a su propio cierre es la forma más fácil
de repetir trabajo ya hecho.

| Punto de la cabecera | Como llegó | Estado medido hoy |
|---|---|---|
| Sombras 2D proyectadas desde focos | «Medio; medir antes de encenderlas» | **HECHO (AUD-278)** — y medido *antes*, que era la condición. `sombras_proyectadas.py`, proyección de silueta por cuña. Apagada por defecto y encendida por la propiedad de mapa `sombras_proyectadas`, porque cuesta: con 4 focos, +1,0 ms sobre 50 obstáculos y +14,8 ms sobre 1.000 (+4,9 ms con el tope) |
| Pendientes (*slopes*) | «Grande; cambiar la resolución de colisión» | **HECHO (AUD-297)**, e integrado en la resolución de colisión —no aditivo—, que fue decisión suya contra la recomendación de §11 (§17.2) |
| `SpriteBatch` | «Medio; medir antes (AUD-148)» | **HECHO (AUD-302)** el lote de CPU, donde el perfil dice que paga. La ruta de GPU se midió (AUD-301) y está justificadamente sin poner. Ver §18 |
| Reducir ciclos de importación | «Grande; 24 pares» | **No hay ninguno.** Medido: cero (AUD-298). Ver §19.1 |
| Partir `stage_scene.py` | «Aplazado por ustedes» | **HECHO (AUD-299)**: 1.457 líneas, por debajo del presupuesto de 1.500, y `tests/test_particion_de_stage_scene.py` en verde — 57 pruebas. Dejó de estar aplazado |

Verificado hoy, no leído:

```
$ python -m pytest tests/test_particion_de_stage_scene.py -q
57 passed in 4.77s

$ python -m pytest tests/test_no_hay_ciclos_de_importacion.py tests/test_sombras_proyectadas.py -q
13 passed in 3.10s

$ wc -l src/framework/scenes/stage_scene.py
1457
```

### 19.1 La cifra que creció sin que nadie volviera a medirla

Los ciclos de importación entraron en §15.0 como «17 pares», y esta versión de
la lista los da como **24**. Entre una cifra y otra no hay ninguna medición
nueva: el número subió solo, por el camino, como suele pasarles a los números
que se copian de un documento a otro.

Lo que dice la medición es que **las dos están mal, y por el mismo motivo**. El
barrido que las produjo contaba todos los `import` del fichero, incluidos los
que viven dentro de una función; y un import diferido no es un ciclo, porque se
resuelve al llamar, con el árbol ya cargado. Contando sólo los del cuerpo del
módulo —los únicos capaces de producir un `ImportError` circular— salen
**cero**, y así lo fija hoy `tests/test_no_hay_ciclos_de_importacion.py`.

Es la cuarta vez en este reporte que una frase escrita antes de medir resulta
falsa; las otras tres están en §16.1 y §18.3. Todas comparten forma: una cifra
plausible, repetida hasta parecer un dato. Por eso la regla de este documento no
es «desconfía de la documentación», sino la más barata de aplicar — **el número
que no se puede reproducir con un comando no se escribe**.

### 19.2 Lo que sigue abierto de las nueve categorías

Barridas hoy las cuarenta y seis propuestas contra el código, quedan **cuatro
filas** sin cerrar, y ninguna es un defecto: son tres piezas aditivas y una
decisión de rúbrica.

| Qué | Estado | Evidencia de hoy |
|---|---|---|
| ***Bash*** (impulso sobre proyectiles) | **NO EXISTE** | Sin coincidencias en `src/`. Su pareja en la lista, el pogo, sí está: `POGO_IMPULSO = -300.0` en `airborne.py:236` (AUD-134), deliberadamente menor que el salto para que no sea una forma de volar. El *Bash* sigue necesitando la decisión que §15.1 pedía: **qué proyectiles admiten impulso**. Sin esa lista no es trabajo de ingeniería |
| *Feedback* diegético | **PARCIAL** | Sigue estando sólo el parpadeo de invencibilidad. Sin daño visible en el sprite del jugador y sin color de arma al cargar: no hay un solo símbolo de tinte por daño ni de color por carga en `entities/` |
| Alto contraste | **PARCIAL** | `_CONTORNO` y `_COLOR_CONTORNO` viven en `player.py:50-54` y los usa `player.py:809`: el contorno de silueta es **sólo del jugador** (AUD-190). Faltan el de enemigos y los iconos que no dependan del color. Los modos daltónicos sí están completos, también en la ruta de GPU (AUD-252, 0,07 ms) |
| `classify_gap` y la movilidad | **PARCIAL, por decisión** | AUD-192 exime de `design_completable` a los mapas con objetos de movilidad; `classify_gap` sigue fuera de esa exención. GAP-024 se cerró **por decisión**, no por arreglo: el calificador es más permisivo que el motor, y el daño cae del lado que no rompe entregas ya calificadas |

De las tres primeras, la única con valor claro por delante del coste es el
**contorno de enemigos**: es la misma función de `player.py` aplicada a otro
grupo, y es accesibilidad, no adorno. Las otras dos son decisiones de diseño
—qué proyectiles, qué lenguaje visual para el daño— y este documento no las
toma.

Lo que ya estaba abierto y no depende del motor sigue igual, en §17.3: el jefe
Gavilán (asignación de estudiante), los cinco sonidos de jefe sin emisor,
`LuaScriptEnemy`, y ampliar las pruebas doc↔código. Y tres huecos conocidos
siguen abiertos a propósito con su razón escrita: GAP-002 (la heurística de
salto en X, sin ningún caso que la rompa), GAP-031 (`play_voz` no necesita
llamador, necesita ficheros de voz) y GAP-032.

### 19.3 Un hueco que ya se podía cerrar y seguía abierto

**GAP-015 —«StageScene sin descomposición, monolito de 1200+ líneas»— se cierra
hoy.** Su nota de agosto lo dejaba abierto a propósito con un argumento
correcto: la descomposición había ocurrido —los subsistemas viven en
`src/framework/stage/` y `StageScene` los compone por mixins— pero el fichero
medía 1.490 líneas y el presupuesto era 1.500, así que «marcarlo resuelto sería
falsear la medición».

AUD-299 lo bajó a **1.457** y puso su prueba en verde. La condición que la
propia entrada se puso está cumplida y verificada arriba, así que se cierra por
la vía normal: tachado y con `**Resolution:**`, según la invariante 4.

Merece la pena quedarse con por qué estuvo abierto tanto tiempo. No fue por
falta de trabajo: la descomposición llevaba hecha desde AUD-184. Fue porque la
entrada estaba escrita contra un **número medible** en vez de contra una
sensación de arquitectura, y el número no se cumplía. Un hueco redactado así no
se puede cerrar por optimismo — que es justo lo que se le pide a este registro.

---

## 20. Las cuatro filas que quedaban, decididas (2026-08-06, sexta pasada)

§19.2 dejó cuatro filas abiertas y dijo que tres eran decisiones de diseño que
este documento no toma. Se tomaron. Lo que sigue es qué se decidió, qué se
implementó y las dos veces que la medición volvió a corregir el trabajo mientras
se hacía.

| AUD | Qué era | Qué se hizo |
|---|---|---|
| **304** | El contorno de silueta lo tenía sólo el jugador | `framework/vfx/contorno.py`, sin dueño. Los enemigos lo llevan con `contorno_de_enemigos`, **apagada por defecto** |
| **305** | El *bash* no existía | Impulso al golpear un proyectil con `admite_bash`. **Opt-in por proyectil**, declarable desde Tiled |
| **306** | Las pendientes no estaban en ningún TMX que se copie | Dos en la plantilla del estudiante, una tercera tendida en la vitrina, y `validate_tmx` mirando `student_templates/` |

Las tres comparten la misma forma, que es la que este repositorio lleva pidiendo
desde AUD-297: **la mecánica entra entera y no se ejecuta en ningún mapa ya
entregado**. Ninguna de las veintiséis entregas cambia de aspecto, de dificultad
ni de nota.

### 20.1 Por qué las dos primeras van apagadas por defecto

No es prudencia genérica; cada una tiene su motivo medido.

**El contorno de enemigos (AUD-304).** El del jugador existe para decir «este
eres tú» — AUD-190 lo puso porque el personaje tenía un contraste de 1,01 a 1,18
contra el fondo en quince de los dieciséis mapas. Si todo lo que se mueve lleva
borde, esa señal desaparece. Encenderlo por defecto, además, cambiaría el
aspecto de dieciséis mapas ya calificados, y «funcionar sin tocar una línea»
(invariante 2) incluye verse como se veían el día que se calificaron. El color
del enemigo es ámbar y se separa del blanco roto del jugador **por luminancia**
(0,79 contra 0,19), no por tono: los tres modos daltónicos colapsan tonos y
dejarían los dos bordes iguales.

**El *bash* (AUD-305).** La alternativa —que valiera cualquier proyectil
enemigo— es más fácil de aprender y convierte a cada tirador en una plataforma.
Con ella, huecos que hoy no son franqueables pasan a serlo en los dieciséis
mapas, y habría que recalificarlos todos. Marcado por proyectil, no hay ni uno
en los mapas que existen: el método recorre la lista y no hace nada, igual que
las pendientes de AUD-297.

Y una trampa que apareció al declararlo desde Tiled: **Tiled entrega `"false"`
como cadena** si el autor no marca el tipo `bool`, y una cadena no vacía es
cierta en Python. Sin conversión explícita, escribir «false» *encendía* la
propiedad — el peor de los dos fallos posibles, porque el estudiante concluye
que la opción no funciona cuando lo que pasa es que no se puede apagar. Hay
`_BOOL_PROPS` en el cargador y dos pruebas para eso.

### 20.2 Las dos veces que la medición corrigió el trabajo de hoy

Van con nombre, como las siete anteriores (§16.1, §18.3, §19.1).

**Un import de tres palabras dejó a los dieciséis mapas con 0 de 12 en la
rúbrica.** La primera versión de AUD-304 importaba `user_settings` en el cuerpo
de `enemy_base.py`. Parece inocuo: `user_settings` importa `orjson`, y
`enemy_base` está en la cadena `stage_loader → entities → enemy_base`.
`scripts/grade_stage.py` carga los escenarios en un entorno pelado —sin `PATH`,
que en Windows deja inalcanzables las extensiones compiladas—, atrapa la
excepción y la convierte en un cero. Resultado: `design_completable` a 0 en los
dieciséis, **stage0 incluido**, que tenía nota perfecta.

Lo cazaron cuatro pruebas de `test_rubrica_de_movilidad.py`, que no podían decir
por qué. El arreglo es el patrón que `stage/camera.py` ya usaba y que ahora se
entiende: el import va dentro del método. Y hay una prueba nueva que importa el
cargador en ese mismo entorno pelado y falla con el traceback delante, para que
la próxima vez no haya que deducirlo.

**La vitrina no se edita: se genera.** `stage_mecanicas.tmx` sale de
`tools/generate_stage_mecanicas.py`, y la pendiente tendida se añadió primero a
mano en el TMX. `test_el_tmx_es_el_que_produce_el_script` lo cazó en la misma
tanda. La pendiente vive ahora en el generador, que es la fuente de verdad, y el
TMX se regeneró.

Las dos comparten forma con las anteriores: **el fallo no estaba en lo que se
quería hacer, sino en una suposición lateral que nadie había comprobado**. Y las
dos las encontró una prueba que ya existía, escrita por otra tanda, para otra
cosa.

### 20.3 Componer el fotograma entero en GPU: lo que impide hacerlo hoy

Es la cuarta decisión, y es la única que no se entrega. Va aquí con la medición
delante porque la conclusión no es «cuesta mucho»: es que **choca con las
invariantes 1 y 2**, y relajarlas es una decisión de curso, no de ingeniería.

§18.2 dejó dicho que la ruta de sprites en GPU gana siempre dibujando —4,2× con
500 sprites, 10,4× con 8.000 en la Quadro— y que a las ~20 entidades por
fotograma que dibuja el juego lo que cuesta subirlas y bajarlas se come la
ganancia. También dejó dicho cuándo cambia eso: **el día que el fotograma entero
se componga en la tarjeta**, porque entonces desaparece la bajada de píxeles.

Lo que hace falta para eso es que **nadie dibuje en una `Surface` de CPU**. Y
medido hoy: **17 de los 89 ficheros de `src/stages/` llaman a `blit` directo**,
varios con superficies intermedias y `BLEND_ADD` —los halos de `boss_paburu`,
por ejemplo—. Eso deja dos caminos y ninguno sirve:

* **Mantener una `Surface` de compatibilidad** para lo que no se convierta.
  Entonces el fotograma vuelve a subirse entero cada vez, que es exactamente el
  coste que esta reescritura venía a eliminar. La ganancia desaparece y queda el
  trabajo.
* **Convertir esos 17 ficheros.** La invariante 1 dice que `src/stages/` no se
  refactoriza, y la 2 que las veintiséis clases siguen funcionando sin tocar una
  línea.

O sea: la ruta de GPU completa y las entregas de estudiantes que dibujan con
`blit` **no pueden coexistir en el mismo fotograma**. Es la misma forma de
conflicto que `gpu_present.py` documentó en su día para el renderizador de SDL2
—«un `_sdl2.Window` y el `pygame.display` clásico no pueden convivir en la misma
ventana: hay que elegir»—, sólo que ahora el precio está medido y tiene nombre.

**Lo que sí se puede decidir sin tocar nada:** si el curso acepta que las
entregas futuras dibujen a través de una API del motor en vez de con `blit`
directo, la ruta de GPU deja de estar bloqueada **para los mapas nuevos**, y las
veintiséis actuales siguen en el camino de CPU sin enterarse. Eso es una línea
en la plantilla y en `BOSS_CREATION.md`, no una reescritura — pero es una
decisión de curso, y este documento no la toma.

---

## 21. La documentación, auditada y medida (2026-08-06, séptima pasada)

El encargo pedía tres cosas: buscar documentos duplicados o parecidos y reportes
de prueba inservibles, **borrarlos**, y unificar la documentación en dos
idiomas. Lo que sigue es lo que salió al medirlo, y la parte importante es que
**no hay nada que borrar**.

### 21.1 Duplicados: ninguno

Medido sobre los **110 documentos** de `docs/*.md` y la raíz que había al hacer
el barrido — hoy son **105**, porque §21.2 se llevó cinco por delante:

| Comprobación | Resultado |
|---|---|
| Ficheros byte-idénticos | **0** |
| Pares por encima del 75 % de similitud | **0** |
| Par más parecido que existe | `35_USER_MANUAL` ↔ `37_DEMO_QUICK_GUIDE`, **0,349** |

0,349 entre un manual de usuario y una guía rápida es la estructura que
comparten dos documentos del mismo tipo, no una copia. Para comparar: los cinco
duplicados que AUD-205 encontró y arregló estaban entre **0,886 y 0,962**, y los
bilingües legítimos entre 0 y 0,248. No hay nada en la franja de en medio, que
es exactamente lo que `test_documentos_sin_duplicar.py` predijo al fijar su
umbral en 0,5.

**La limpieza de AUD-205 se sostiene y su gate funciona.** No hay un segundo
episodio esperando.

### 21.2 «Reportes de prueba que ya no sirven»: son cinco, y están etiquetados

Los candidatos por nombre —`FASES_1_2_3_COMPLETADAS`, `VERIFICACION_FINAL`,
`AUDIT_VERIFICATION_2026-07-27`, `AUDITORIA_2026-07-27_MEDICION`,
`ESTRATEGIA_2026-07-27`— existen, y el índice maestro **ya los marca
`Historical`**, uno por uno, frente a los `Current` del resto.

Eso los convierte en lo contrario de un descuido: son el registro de qué se
midió y cuándo. Este repositorio no borra ese rastro —la invariante 4 dice
exactamente eso de `KNOWN_GAPS.md`, y por el mismo motivo—. Un documento
histórico correctamente etiquetado no estorba: se sabe leyendo el índice que no
describe el estado de hoy.

**Recomendación de este documento: no se borraban.** Se decidió lo contrario, y
así consta: los cinco están **eliminados** (AUD-308), con sus filas fuera del
índice. La recomendación se deja escrita, y no tachada, porque una recomendación
desoída sigue siendo el registro de qué se sopesó — que es exactamente la
función que cumplían los ficheros borrados.

Lo que se pierde es acotado y conviene tenerlo dicho: 1.385 líneas de mediciones
de julio de 2026, cada una con su commit citado —`8c476c8`, `272160c`,
`f6c005f`—. Nada de código dependía de ellos: las únicas referencias eran el
índice y este reporte. Y siguen en el historial, así que recuperar uno es
`git show <commit>:docs/VERIFICACION_FINAL.md`, no un trabajo de arqueología.

**Y de pruebas obsoletas tampoco hay ninguna.** La suite entera da **4.052
pasadas, 4 saltadas, 0 fallos**, y las cuatro que se saltan lo hacen por una
condición del entorno, no por estar muertas: tres piden `pydub`, que es
dependencia opcional, y la cuarta se salta sola con el motivo escrito —«pygame
sigue disponible en este entorno; nada que simular»—, porque existe para
comprobar qué pasa cuando *no* está. Una prueba que se salta diciendo por qué es
una prueba viva.

### 21.3 Lo único que sí está mal puesto: tres documentos sin fila

`PHASE_FIX_REPORT.md`, `REMEDIATION_PLAN.md` y `AUDIT_CHECKLIST.md` viven en la
raíz y **no tienen fila en `00_MASTER_INDEX.md`**. La convención del
`CLAUDE.md` es clara: un documento sin fila en el índice está mal puesto.

No es motivo para borrarlos —hay que leerlos y decidir si describen algo
vigente—, pero sí para que dejen de estar fuera del inventario. Es el trabajo de
limpieza real que esta auditoría encontró, y es de indexar, no de borrar.

**Hecho (AUD-308):** los tres tienen ya su fila, y las tres dicen `Historical`,
porque leídos lo son: `PHASE_FIX_REPORT.md` cita «307 passed» y la suite va por
**4.052**; `REMEDIATION_PLAN.md` es un plan con su lista terminada, y
`AUDIT_CHECKLIST.md` se subtitula «RESULTADO FINAL» con todo marcado.

Son, por tanto, **de la misma naturaleza que los cinco que se borraron**, y no
se han borrado: la decisión que se tomó nombraba a aquellos cinco, y extenderla
por analogía a unos ficheros que nadie miró al decidir habría sido inventarse un
permiso. Si el trato debe ser el mismo, es una frase, y estos tres ya están
localizados.

### 21.4 Y mi primera medición dio tres falsos positivos

Va aquí porque es la cuarta vez que pasa en este documento y la primera en que
el error es de la propia auditoría que lo escribe.

El primer barrido acusó a tres documentos: `61_AUDITORIA_AAA_2026-08.md` sin fila
en el índice, y dos filas del índice —`15_DISENO_4_1_EL_CEMENTERIO.md` y
`27_MEDICION.md`— apuntando a ficheros que no existen. Los tres eran falsos:

* el 61 **sí** está indexado, y mi expresión regular no lo cazó porque su nombre
  lleva un guion (`2026-08`) que no estaba en la clase de caracteres;
* el 15 vive en `docs/niveles/`, y el índice lo cita con su ruta;
* `27_MEDICION.md` no existe ni ha existido: era el final de
  `AUDITORIA_2026-07-27_MEDICION.md`, partido por mi propio patrón.

Tres acusaciones, cero defectos, y la herramienta que las produjo era mía y
recién escrita. Es el mismo modo de fallo que §19.1 documenta para los «24 pares
de ciclos de importación»: **una medición mal hecha no da menos confianza que
una bien hecha, da la misma**. Por eso se comprueba cada hallazgo contra el
fichero antes de escribirlo, incluso —sobre todo— cuando el hallazgo es tuyo.

### 21.5 Los dos idiomas dentro del juego: seis cadenas rotas (AUD-307)

Ésta es la parte del encargo que sí produjo un arreglo, y es la que pedía
«validar a nivel técnico que ambos idiomas se puedan utilizar dentro del juego».

Seis cadenas estaban **en castellano sin traducción en `en.json`**, así que un
jugador con el idioma en inglés las veía en español:

    'ESTUDIANTE'  'EXPERIENCIA'  'Elegir'
    'IDENTIFICACIÓN'  'Subir rango'  'ÁRBOL DE HABILIDADES'

Dos de ellas son de AUD-293 y AUD-267. Eso dice cuál es el modo de fallo real, y
no es el que `check_translations.py` vigilaba: el script buscaba entradas
huérfanas —traducciones de cadenas renombradas— y aquí no había ninguna. Lo que
pasa es que **una función nueva llega con sus textos y nadie se acuerda del
catálogo**.

El gate no lo veía porque «cadena sin entrada» estaba archivado como nota y no
como error, con un argumento correcto: el código fuente es bilingüe y un literal
ya castellano no necesita entrada en `es.json`. De ahí se había concluido que no
se podía comprobar nada, y sí se puede, sin heurísticas de idioma:

> `es.json` traduce del inglés al castellano. Una cadena visible que **no** está
> en `es.json` es que ya estaba en castellano — lo dice el catálogo, no una
> suposición. Y toda cadena castellana necesita su entrada en `en.json`.

Esa regla está ahora en el validador y en
`tests/test_los_dos_idiomas_en_el_juego.py`, con una prueba que le quita una
traducción a una copia temporal del catálogo y comprueba que el gate falla —
porque un validador que nunca dice que no, no valida.

### 21.6 Traducir toda la documentación: sigue chocando con la invariante 5

La tercera parte del encargo —«documentación final unificada en dos idiomas»—
es la que este documento no ejecuta por su cuenta, y conviene tener delante por
qué antes de decidir.

La política vigente es **bilingüe donde hay lector**, y no es una preferencia:
está razonada en `tests/test_documentacion_bilingue.py` a partir de una
medición. Los 95 documentos traducidos son 190 ficheros que mantener
sincronizados, y el modo de fallo dominante de este repositorio —medido tres
veces en un mes— es justamente que un documento se separe de la realidad. La
pareja del README ya se había separado: decía 1.333 pruebas en español y 640 en
inglés cuando la cifra real era 2.020. **Los dos estaban mal, cada uno a su
manera.**

Además, §17.2 ya registró esta decisión tomada, y en sentido contrario:
«Traducir los doce manuales: **no**. Se mantiene la política de la invariante 5.
Queda cerrado, no pendiente».

Cambiarla es legítimo —es una decisión de curso, no de ingeniería— pero es un
cambio de política, no una tarea de limpieza, y multiplica por dos la superficie
del modo de fallo que más veces ha mordido a este proyecto. Si se cambia, lo que
la haría sostenible no es traducir: es que cada pareja tenga una prueba de
contenido como la del README, y hoy **hay una sola** de 95 documentos (§17.3).

**Decidido: se mantiene la política actual** (6 de agosto de 2026). Es la
segunda vez que se ratifica —la primera está en §17.2— y con esto la parte
bilingüe del encargo queda cubierta por donde tenía arreglo de verdad: **dentro
del juego**, con las seis cadenas de §21.5 y el gate que impide que vuelvan.
Traducir los 95 documentos queda cerrado, no pendiente.

---

## 22. ¿Está la documentación al día? Medido cifra a cifra (2026-08-06, octava pasada)

§21 comprobó que no hubiera documentos *sobrantes*. Esto comprueba lo contrario:
que lo que dicen los que hay siga siendo verdad. El método es el de siempre —
sacar cada número del código y contrastarlo, no leerlo y asentir.

### 22.1 Lo que está bien

| Afirmación, y dónde se repite | Medido | |
|---|---|---|
| Enlaces entre documentos | **0 rotos** sobre 133 ficheros | ✅ |
| «21 especies» (20 veces, 8 documentos) | `len(SPECIES)` = **21** | ✅ |
| «16 escenarios» (11 veces, 6 documentos) | 16 `.tmx` en `assets/maps` | ✅ |
| Referencia TMX ↔ registro | `generate_tmx_reference.py --check`: al día | ✅ |
| Árbol de `03_ARCHITECTURE.md` ↔ `src/` | prueba en verde | ✅ |

Los 12 «enlaces rotos» que dio el primer barrido eran matrices `[[0, 0, 0]]` de
los documentos de filtros y notación de tipos `[[World, float]]`, no enlaces.
Ninguno de los cinco documentos borrados en §21.2 dejó una referencia colgando.

### 22.2 Lo que estaba desfasado, y ya no

**El recuento de pruebas del README (AUD-309).** Decía **4.007** en las dos
versiones y la suite recolecta **4.051**. No lo cazó nadie porque el gate tolera
un 5 % de desvío y esto era un 1,09 % — un margen razonable, puesto a propósito
para que el README no cambie por añadir tres pruebas. Pero la invariante 6 dice
que si cambias la suite actualizas el número, y esta sesión añadió 32 pruebas y
quitó 5. Corregido en `README.md` y `README.en.md`.

**`admite_bash` no llegó a la guía que leen los estudiantes (AUD-309).** Y aquí
está lo interesante: sí llegó a la tabla generada, y
`generate_tmx_reference.py --check` decía «al día» con razón. Lo que pasa es que
`STAGE_CREATION.md` **lista los arquetipos de enemigo dos veces**: la tabla
generada dentro del bloque `GENERATED`, y doscientas líneas antes un resumen
escrito a mano, en la sección donde uno está mientras coloca enemigos. Esa
segunda no la compara nadie.

Es exactamente el defecto que AUD-182 describió sobre este mismo generador —«un
gate que verifica que el doc coincida con una tabla incompleta»—, con la vuelta
de tuerca de que ahora la tabla estaba completa y era el documento el que tenía
dos. Corregido, y con `tests/test_las_dos_tablas_de_enemigos.py` comparándolas
para que no vuelvan a separarse.

**Y esta sección arregla una cifra de la sección anterior.** §21 midió «110
documentos» y era cierto al medirlo; §21.2 borró cinco, así que dejó de serlo
en el mismo documento y en la misma tarde. Ya dice 105.

**Corregir el README lo rompió, y lo cazó la prueba escrita para eso.** El
`README.en.md` decía 4.007 en **dos** sitios y sólo se cambió uno, así que la
pareja quedó afirmando 4.051 en español y 4.007 en inglés — que es, letra por
letra, el defecto que creó `test_documentacion_bilingue.py`: «antes decía 1.333
en español y 640 en inglés cuando había 2.020». La prueba de AUD-122 salió en
rojo con las dos cifras delante.

Vale la pena quedarse con la forma: el error no fue no saber el número, era el
correcto; fue **arreglar una pareja tocando un solo lado**. Es el mismo modo de
fallo que hace cara la política bilingüe (§21.6), reproducido por accidente
mientras se escribía la sección que lo explica. Cinco documentos que se
mantienen en dos idiomas producen esto de vez en cuando; noventa y seis lo
producirían a diario.

### 22.3 Dos cifras que la medición no confirma, y que no se han tocado

**«95 documentos»** aparece 10 veces en 6 documentos, siempre dentro del
argumento de por qué no se traduce todo. Hoy `docs/*.md` son **96** (eran 101
antes de §21.2, y ninguna combinación de subcarpetas y raíz da 95). O sea: la
cifra fue verdad cuando se escribió y el conjunto creció después.

No se corrige porque el argumento no depende del número exacto —95, 96 o 101 dan
todos «el doble de ficheros que sincronizar»— y porque tocar diez frases de seis
documentos para mover un dígito introduce más riesgo de errata que el que
elimina. Queda dicho aquí, que es donde se busca.

**«Las 26 clases de escenario»** es más serio, porque está en la **invariante 2
del `CLAUDE.md`** y se repite 31 veces en 12 documentos. Medido en el árbol de
hoy:

| Qué se cuenta | Cuántas |
|---|---|
| Clases de `src/stages/` que heredan de una `*Scene` | **16** |
| Clases totales en `src/stages/` | 58 |
| Directorios de `src/stages/` con clases | 21 |
| Ficheros `.py` en `src/stages/` | 89 |
| Directorios en `revisar/` | **0** (está vacío) |

Ninguna da 26. La explicación más probable es que 26 sea el número de
**entregas del curso** —personas— y no de clases en el repositorio, y que la
frase haya arrastrado la cifra de un sitio al otro. Desde el repositorio **no se
puede verificar**, porque `revisar/` está vacío y esa información vive fuera.

Y ahí está el problema de fondo, que no es aritmético: la invariante 6 dice que
los números de la documentación son verificables o no se escriben, y éste no lo
es. La invariante 2 sigue siendo válida y sigue mandando —no romper las entregas
existentes— pero su cifra no se puede comprobar con un comando, que es
justamente lo que este proyecto exige de cualquier otro número.

**No se cambia aquí.** El `CLAUDE.md` son las reglas del repositorio, y una
regla no se reescribe desde un informe: se corrige a sabiendas, sabiendo si 26
son personas, entregas o clases. Es la única cifra de esta pasada que necesita
que alguien de fuera del repositorio diga qué contaba.

### 22.4 «21 especies sobre 8 clases base»: son 3, y las otras cinco están libres

Apareció al escribir [`88_QUE_PUEDE_HACER_CADA_ROL.md`](88_QUE_PUEDE_HACER_CADA_ROL.md),
y apareció **por copiarla**: la frase estaba en `69_PROMPT_AUDITORIA_MAESTRO.md`
§39 y se trasladó sin comprobar. Medido:

```
>>> collections.Counter(s.base for s in SPECIES.values())
{'EnemyWalker': 8, 'EnemyFlying': 6, 'EnemyShooter': 7}
```

**Tres**, no ocho. El ocho es real pero cuenta otra cosa: los arquetipos que el
motor ofrece —`enemy_archer`, `enemy_assassin`, `enemy_brute`, `enemy_caster`,
`enemy_charger`, `enemy_flying`, `enemy_shooter`, `enemy_walker`—, y **cinco de
ellos no los usa ninguna especie del bestiario**. Existen, funcionan y se
colocan desde Tiled; simplemente el roster creció sólo sobre tres.

Que la cifra estuviera mal es lo de menos: lo que estaba escondido es que hay
**cinco arquetipos sin una sola especie encima**. Eso no es deuda, es diseño
disponible — una especie nueva sobre `Brute` o `Caster` es una fila en la tabla
y cero código, que es justo lo que se le puede pedir a un estudiante.

Y la lección de método, otra vez la misma: la cifra no venía del código, venía
de otro documento. Es la quinta vez en este reporte (§16.1, §18.3, §19.1, §21.4)
y las cinco tienen la misma forma — **un número que se copia deja de estar
medido en cuanto se copia**.

---

## 23. La documentación, recortada y contrastada (2026-08-06, novena pasada)

El encargo: dejar sólo la documentación técnica necesaria, verificarla contra el
código y dejarla usable por un estudiante. Se hizo en ese orden, y el orden
importaba — actualizar noventa y seis documentos para luego borrar treinta y uno
habría sido tirar el trabajo.

### 23.1 Qué se fue y qué se quedó

De **96 documentos a 65**. Se retiraron 31: auditorías cerradas, informes de
fase, hojas de ruta cumplidas y registros de decisiones ya tomadas.

Tres decisiones que conviene tener escritas:

* **`AUDIT_2026-07.es` y `.en` no se borraron**, aunque son informes de
  auditoría. Son la pareja bilingüe que la invariante 5 declara obligatoria y
  que vigila `test_documentacion_bilingue.py`: borrarlas es cambiar una
  invariante, no limpiar.
* **Se conservaron las cuatro fuentes que cita el `CLAUDE.md`** —`62`, `63`,
  `69` y este mismo `87`—, para que sus reglas sigan siendo ciertas.
* **`PHASE_FIX_REPORT`, `REMEDIATION_PLAN` y `AUDIT_CHECKLIST`** siguen en la
  raíz, ahora indexados y marcados `Historical`.

El índice maestro se reescribió entero. El anterior hablaba de «65 documentos»,
de siete paquetes ZIP (`v1` … `v7`) que ya no existen, y mandaba al lector a
`25_IMPLEMENTATION_ROADMAP.md` como primer destino. El nuevo se generó desde lo
que hay, agrupado por *para qué sirve*, y **no quedó un solo enlace muerto** en
toda la documentación: de 45 a 0.

### 23.2 Lo que el contraste con el código encontró

**Cinco propiedades de TMX que no existen (AUD-310).** `06_TMX_SPEC.md` es lo
que lee un estudiante mientras monta su mapa, y documentaba `background_color`,
`debug_mode`, `use_tile_collision`, `damage_type` y `trigger_once` como si
funcionaran. **Ningún módulo de `src/` lee ninguna de las cinco.**

Y no era teórico: **`stage1_2_la_soda.tmx` usa `trigger_once`**. Alguien la
escribió creyendo que su mensaje saldría una sola vez, y nunca ha hecho nada. Lo
que sí lo hace es el **tipo** `MessageTrigger_Once` — no una propiedad, otro
`type`. Ese matiz está ahora escrito donde se busca.

De paso, el ejemplo XML de mensajes usaba `type="Message"`, que el cargador no
conoce: copiarlo y pegarlo producía un objeto rechazado.

**La consola de depuración lleva desde AUD-283 en F11, y seis documentos decían
F3 (AUD-310).** Los dos README, el manual de usuario, la arquitectura, los
contratos de API y las escenas académicas. F3 es `LEARN_PHYSICS` en el mapa de
acciones, así que quien seguía la documentación pulsaba una tecla con otro
dueño.

Lo interesante es que **el propio reporte 87 ya lo decía bien** —«es F11, no
F3»— desde §15.7. Saberlo en un documento no arregla los otros seis. Por eso
las dos correcciones llevan prueba: `test_la_spec_tmx_no_promete_de_mas.py` y
`test_las_teclas_que_la_doc_promete.py`, que lee la tecla **del código** y
señala por nombre y línea cualquier documento que prometa otra.

### 23.3 Las dos veces que las pruebas nuevas no medían nada

Se comprobaron mutando, y las dos primeras versiones fallaron:

**La prueba de las teclas no cazaba el titular.** Buscaba «debug console» y
«consola de depuración», y el manual de usuario decía sólo `### 4.2 Debug (F3)`.
Devolví esa línea a mano al manual y la prueba siguió en verde. Ahora mira
cualquier línea con «debug» o «depurac», y con la mutación puesta señala
`docs/35_USER_MANUAL.md:65`.

**La prueba de la spec creía que `Walker` no existía.** Los arquetipos se
registran al llamar a `entity_factory.ensure_registered()`, no al importar el
módulo, así que el registro salía vacío y los tipos legítimos de los ejemplos
parecían inventados. Es el mismo tropiezo que ya está documentado en el
generador de la referencia TMX.

### 23.4 Y una que corrí sin mirar

Ejecuté `scripts/obsidianize.py` para ver si se rompía con los documentos
borrados. Se rompió al revés: **escribe**. Recreó `Obsidian_Home.md` —que
acababa de borrar— y añadió una sección «Documentos Relacionados» duplicada a
`07_STAGE0_DESIGN.md`, que ya tenía la suya. Revertido con `git checkout`.

Queda anotado porque el script no lo advierte en su `--help` y tiene `--dry-run`
justamente para esto. La regla que se me olvidó es del propio repositorio: antes
de ejecutar algo sobre el árbol, mirar si escribe.

### 23.5 Lo que sigue sin contrastar

Honestidad sobre el alcance: `scripts/audit_docs_vs_code.py` cuenta **524
símbolos citados que no existen** repartidos por los 65 documentos, y esta
pasada resolvió los que tocan a un estudiante que sigue instrucciones. El resto
está sin revisar uno por uno.

Y hay que saber leer esa cifra antes de perseguirla: **buena parte son falsos
positivos**. La herramienta busca símbolos de Python, y `Checkpoint_01`,
`Solid_Floor`, `Walker_01` o `BG_` son nombres y prefijos de objetos y capas
de Tiled, no código. El peor documento —`75_BIBLIA_TECNICA.md`, con 159 sobre
717 citados— hay que mirarlo con ese filtro puesto.

Los que sí conviene revisar por orden, porque son instrucciones que alguien
sigue: `66_GUIA_DE_LEVEL_DESIGN` (26), `17_BOSS_SPEC` (23),
`60_GUIA_COMPLETA_DEL_MOTOR` (18) y `26_STUDENT_TEMPLATE_SPEC` (12, y de ésos
ocho son nombres de pruebas que ya no existen).

---

## 24. Los cuatro documentos que quedaban, contrastados (2026-08-06, décima pasada)

§23.5 dejó una lista por orden de a quién engañan: `66_GUIA_DE_LEVEL_DESIGN`,
`17_BOSS_SPEC`, `60_GUIA_COMPLETA_DEL_MOTOR` y `26_STUDENT_TEMPLATE_SPEC`. Van
los cuatro, y con ellos AUD-311.

### 24.1 Lo que resultó no ser un error

Merece ir primero, porque es la mitad del recuento y explica por qué la cifra de
524 símbolos «inexistentes» no se persigue a ciegas.

**`60_GUIA_COMPLETA_DEL_MOTOR` estaba limpio.** De sus 18 supuestos fantasmas,
`Alt`, `Shift`, `Tab` y `Espacio` son teclas; `design_completable`,
`file_parses`, `required_layers` y compañía son categorías de `grade_stage.py`
—existen, pero en `scripts/`, donde el barrido no mira—; `_Once` es un trozo de
`MessageTrigger_Once`; y `esperar_evento` existe en `cutscene_guion.py`. Ni una
corrección que hacer salvo la de la música (§24.3).

**Las descripciones de jefes no implementados tampoco son errores.**
`BODY_SLAM`, `SERPENT_WAVE`, `GOLD_RUSH`… son diseño por construir, y una
especificación debe contenerlo. El problema nunca fue que estuvieran; era que
nada dijera cuáles existen.

### 24.2 Lo que sí estaba mal

**El aviso de estado de `17_BOSS_SPEC` había envejecido (AUD-311).** Su sección
0 —puesta por AUD-150 justamente para que nadie confundiera diseño con código—
decía «tres clases de jefe y nueve patrones». Medido con AST sobre
`src/stages/`: **cuatro clases y 17 patrones**. La tabla daba además al Gavilán
por inexistente (existe `BossGavilan`, con una fase y **cero** ataques, 45 % de
`grade_boss`) y a Paburu por tener una sola forma (tiene **cuatro**).

Es el fallo más instructivo de esta tanda: **un aviso de estado que no se
comprueba envejece igual que el documento al que precede, y encima con más
autoridad**, porque lleva su `AUD-NNN` y su tono de medición. Ahora lo ata
`tests/test_el_estado_de_los_jefes_es_real.py`, que cuenta las clases y los
patrones en el código y falla señalando la línea.

**Tres nombres de objeto que `66_GUIA_DE_LEVEL_DESIGN` publicaba y no existen.**
Su §1.5 se titula «vocabulario de objetos disponible», que es lo que un
diseñador copia:

| Publicado | Realidad |
|---|---|
| `EnemySpawn` con `enemy_type` | No existe. Cada enemigo se coloca con su propio `type`: `Walker`, `FlyingBird`, `WalkerGuardia`… |
| `Portal` | No existe. Es `NextTrigger` para cambiar de escenario y `WarpZone` para saltar dentro del mismo mapa |
| `OneWay` | No existe. Es `Platform` |

Y dos especies inventadas en la ficha de un nivel: `FlyingAntena` y
`ShooterSerpiente`, que no están en el bestiario. Las reales más cercanas son
`FlyingHalcon` y `ShooterSerpienteArbol`.

**Las fichas de jefes de esa guía tampoco avisaban.** Llevan «Fase 2 — La
División» y «Fase 3 — El Frenesí» del Rey Terciopelo con todo su detalle, y
ninguna de las dos existe. Ahora la sección 4 abre con el estado medido y remite
a `17_BOSS_SPEC` §0.

**Los nombres de prueba de `26_STUDENT_TEMPLATE_SPEC` eran de otra época.** Sus
nueve `test_stage_template_*` y `test_boss_template_*` no existen: las pruebas
sí, dentro de `TestStageTemplate` y `TestBossTemplate` y con nombres cortos. La
cobertura era correcta; los nombres, de antes de que se agruparan en clases.
Actualizados y comprobados contra lo que `pytest --collect-only` recolecta.

### 24.3 La música que no suena (AUD-311)

Tres documentos —`06_TMX_SPEC`, `60_GUIA_COMPLETA_DEL_MOTOR` y
`STAGE_CREATION`— daban `bgm_stage1` como ejemplo de `bgm_track`. En
`assets/music/` hay dieciséis pistas y **ninguna se llama así**.

Lo que le pasa a quien copia el ejemplo:

```
AudioManager: no se pudo cargar música bgm_stage1: No file 'bgm_stage1' found
play_music con pista inexistente: no lanza (silencio)
```

**No falla.** Anota una línea en el registro y sigue. El estudiante juega su
nivel en silencio, no mira el registro, y concluye que la música no funciona o
que su mapa está mal. Es el mismo patrón que las cinco propiedades TMX de
AUD-310: el documento promete, el motor calla, y el coste lo paga quien siguió
las instrucciones.

Corregidos a `bgm_zone1`, y `tests/test_los_ejemplos_de_la_doc_existen.py`
comprueba que todo `bgm_*` citado en la documentación exista en el disco — con
la lista sacada de `assets/music/`, no escrita a mano, para que añadir una pista
no rompa nada.

### 24.4 Balance de las tres pasadas de documentación

| | |
|---|---|
| Documentos | 96 → **65** |
| Enlaces muertos | 45 → **0** |
| Propiedades TMX documentadas que no existen | 5 → **0** (marcadas) |
| Tipos de objeto publicados que no existen | 3 → **0** |
| Ejemplos de música que no suenan | 3 → **0** |
| Documentos que anunciaban la tecla equivocada | 6 → **0** |
| Nombres de prueba obsoletos | 9 → **0** |
| Pruebas nuevas que atan documentación y código | **6 ficheros** |

Lo que **no** se ha hecho, para que conste: los 65 documentos no se han revisado
uno por uno de arriba abajo. Se persiguió una cosa concreta —lo que un
estudiante escribe porque la documentación se lo dijo y no funciona— y ésa está
cubierta y con pruebas. El resto del recuento de `audit_docs_vs_code.py` sigue
dominado por falsos positivos, y perseguirlo sin filtrar es trabajo con forma de
progreso, que es exactamente lo que §19.1 avisó de no hacer.

---

## 25. La revisión exhaustiva: el barrido, arreglado primero (2026-08-06, undécima pasada)

§24.4 dejó dicho que quedaban «524 símbolos citados que no existen» y que el
recuento estaba dominado por falsos positivos. El encargo siguiente fue
asegurarse de que **todo** concuerda. Para eso había que empezar por otro sitio:
**un contador con 400 falsos positivos no se puede vaciar leyéndolo**, así que
lo primero fue arreglar el contador.

### 25.1 Cinco huecos del barrido, y lo que tapaban (AUD-312)

`scripts/audit_docs_vs_code.py` leía cuatro carpetas pero **sólo apuntaba en su
inventario lo definido en `src/`**. Todo lo demás salía como inventado por la
documentación:

| Lo que no miraba | Qué acusaba en falso |
|---|---|
| Clases y funciones de `tests/`, `scripts/`, `tools/` | `test_stage_template_import`, `design_completable`, `generar` |
| Nombres de módulo (el fichero, sin extensión) | Los ~100 `test_*` que enumera `75_BIBLIA_TECNICA.md` |
| Cadenas literales fuera de `src/` | `file_parses`, `required_layers` y el resto de la rúbrica |
| Nombres dentro de los `.tmx` | `Checkpoint_01`, `Solid_Floor`, `BG_Far` |
| Ficheros de `assets/` | `banner_medium`, `mask_frag` |

Más dos filtros que faltaban: un token que **acaba** en `_` es un prefijo
(`BG_`, `Solid_`, `Death_`), no un identificador; y las teclas (`Shift`, `Tab`,
`Espacio`) no son símbolos por venir en mayúscula entre acentos graves.

**Resultado: de 524 a 156**, sin tocar todavía un solo documento. Los 368 que
desaparecieron nunca fueron desviaciones — eran carpetas que el inventario no
miraba.

### 25.2 La marca que faltaba: `diseno-pendiente`

Quedaba un grupo grande y legítimo: **las fichas de diseño de jefes**. Los
ataques del Gavilán, las fases 2 y 3 del Rey, la forma 3 del Paburu. Son unos
130 nombres que no existen **y deben estar escritos**: una especificación sin el
diseño por construir no es una especificación.

El proyecto ya tenía `cita-historica` para «cito este nombre para desmentirlo».
Hacía falta la otra: `<!-- diseno-pendiente -->`, para «esto es lo que hay que
construir». Son cosas distintas y confundirlas cuesta caro — mezcladas en un
solo contador, obligan a leerse los quinientos nombres para saber cuáles
importan, que es tanto como no tener contador.

### 25.3 Lo que quedó al descubierto al limpiar el ruido

Con el contador ya fiable, los documentos técnicos se vaciaron uno a uno.
**Once quedaron a cero**, entre ellos los cuatro que más se consultan:

**`22_API_CONTRACTS` se contradecía a sí mismo.** Su §4.2 listaba
`play_dynamic_music` entre los métodos de `AudioManager`, y doscientas líneas
más arriba el mismo documento explica que AUD-022 lo retiró —era una segunda
implementación de música por capas que no llamaba nadie— y que la viva es
`framework.audio.DynamicMusicSystem`. Quien lee el índice se fía y no baja a
leer el aviso.

**`73_CATALOGO` publicaba cuatro nombres que no cargan:** `BossReyTerciopelo`
(es `BossRey`), `Laser`/`Shockwave` (son `LaserZone`/`ShockwaveZone`),
`cierta_vez` (es `una_vez`) y los efectos de post-proceso sin su prefijo `set_`.

**`52_EVENT_MAP` apuntaba a un fichero de diez líneas.** Citaba
`player_states.py:358`, `:1025`, `:1609`… y ese fichero es hoy un re-export de
**10 líneas**: los estados viven en el paquete `states/`. Además nombraba
`WallJumpState`, que es `WallSlideState`, y la acción de diálogo
`collect_item`, que es `give_item:`. Diecinueve referencias corregidas.

**`75_BIBLIA_TECNICA` daba seis nombres cambiados:** `Application` por `App`
—en la misma línea que dice `App().run()`—, `Experience` por
`ExperienceSystem`, `MixerBus` por `Mezclador`, `PLAYER_FALL_SPEED` por
`PLAYER_MAX_FALL_SPEED`, y dos módulos citados como si fueran clases.

### 25.4 Una promesa muerta en el código, no en el documento

`75_BIBLIA_TECNICA` documentaba dos variables de entorno,
`LOI_TOP_BAR_H` y `LOI_PANEL_W`, para ajustar el kit de demos. Al ir a
comprobarlas apareció que el defecto **no estaba en el documento**:

* `demo_layout.py` tenía un `_env_int()` **sin un solo llamante**;
* las constantes que supuestamente ajustaban —`TOP_BAR_H`, `BOTTOM_BAR_H`— se
  calculan de `settings` y no consultan el entorno;
* lo único que mencionaba las variables era un comentario prometiéndolas.

O sea: una función muerta, un comentario que prometía, y la promesa había
llegado hasta la biblia técnica. Retirados los dos y corregido el documento. Es
el caso que mejor explica por qué esta revisión valía la pena: **el documento
decía la verdad sobre lo que el código pretendía hacer, y el código no lo
hacía**.

### 25.5 Qué queda, y por qué no es un pendiente

**156 nombres**, y su reparto dice todo:

| Documentos | Cuántos | Qué son |
|---|---|---|
| `87`, `AUDIT_2026-07.es`, `AUDIT_2026-07.en` | **74** | Son informes de auditoría: enumerar lo que no existe **es su contenido** |
| `75`, `63` | 20 | Tablas de correcciones — mismo caso, ya parcialmente marcadas |
| `13_PATTERN_RECOGNITION_SPEC` | 6 | Parámetros de scikit-learn (`n_estimators`, `train_test_split`): existen, en la librería |
| El resto | 1–4 cada uno | Cola larga: fichas de nivel con diseño por construir |

Los técnicos —contratos, mapa de eventos, catálogo, TMX, arquitectura, guías—
están **a cero o casi**. Lo que queda no es documentación desviada: es
documentación que habla de lo que falta, que es exactamente lo que se le pidió
que hiciera.

---

## 26. Las pendientes, completas (2026-08-07, duodécima pasada)

AUD-297 dejó las pendientes integradas en la resolución de colisión: subir,
bajar, saltar y aterrizar sobre la hipotenusa. Lo que faltaba eran los
**extremos** — las direcciones en las que la rampa aún se comportaba como una
caja o como un hueco. Esta pasada los cerró todos, con la misma regla que hizo
segura la integración original: **ningún mapa entregado tiene una sola
pendiente**, así que ninguno de los veintiséis escenarios ejecuta ni una línea
de esto, y la calificación de los dieciséis mapas se mantiene como control.

| AUD | Qué era | Qué se hizo |
|---|---|---|
| **323** | La rampa se atravesaba por los lados | `resolver_lateral` frena la cara empinada del extremo alto y la hipotenusa a media altura de una rampa estrecha; el centro sobre la rampa sigue siendo territorio del eje Y |
| **324** | Caer sobre una cuesta paraba en seco | Proyección de velocidad al aterrizar: el impulso de la caída se descompone sobre la hipotenusa (`seno · coseno`) y empuja cuesta abajo en vez de frenar |
| **325** | Los enemigos atravesaban la rampa | Los enemigos resuelven pendientes con la misma geometría, dentro de su propio bucle de resolución |
| **326** | Quieto en la cuesta, el jugador quedaba clavado | Deslizamiento sostenido: sin entrada horizontal, la gravedad lo desliza cuesta abajo a `PLAYER_SLOPE_SLIDE_SPEED` por el factor de la pendiente — velocidad constante y acotada, sin aceleración en fuga; andar manda |
| **328** | En vista cenital la rampa pegaba y frenaba | Sin gravedad no hay cuesta que resolver: en planta la rampa es terreno pintado — ni glue a la hipotenusa ni pared en la cara; lo que frena es la capa Collision, como siempre |
| **329** | ¿Se bachea el wrap del parallax? Medido en 4-1 antes de decidir | **No**, aunque la medición original se corrigió en AUD-330: el 2-3× contra el `blit` suelto no se reproduce re-medido (empate 0,97-1,03×; con sprites pequeños `blits()` gana desde dos llamadas). Se mantiene el blit suelto por el motivo correcto —no hay nada que ganar— y quedan documentados, con evidencia, por qué no se agrupan estelas (alfa por punto sobre superficie compartida) y números de daño (pool) |

La física queda servida para cualquier contexto sin cambiar el contrato: la
gravedad por escenario ya existía (`gravity_multiplier` en el TMX, con prueba
propia), el viento por zonas vive en el ECS (`sistema_viento`), y el
deslizamiento es una constante de `settings` que cualquier escenario puede
declarar — el mismo motor sirve tierra, espacio, hielo y cualquier vista.

AUD-334 (decimotercera pasada) llevó la resolución a `framework/physics/
resolucion.py`: ahora el contrato de AUD-297 se puede heredar sin copiarlo —
una entidad nueva llama a `resolver_movimiento` con su perfil y recibe los
hechos. El jugador pasó a ser consumidor (adaptadores delgados), y la
suite completa verificó que el port no cambió ni un comportamiento.

## 27. El motor libre: decisión del dueño y plan (2026-08-07, decimotercera pasada)

**Decisión del dueño (reversible, registrada en `CLAUDE.md` §3):** las
invariantes 1 y 2 quedan suspendidas. El motor y el framework evolucionan
**libres** para servir contextos y modos de juego distintos —colisiones por
contexto, física ampliada, SpriteBatch, GPU, 2.5D— aunque una entrega
existente se rompa por el camino, y el contenido de referencia (niveles,
jefes y demos de clase) se reconstruirá **después** de la fase de motor para
lucir las características nuevas. La regla de `revisar/` no se toca.

El programa, por fases, con lo hecho y lo pendiente:

| Fase | Qué entrega | Estado |
|---|---|---|
| **1. Perfil de física por contexto** | `framework/physics/perfil.py`: `PhysicsProfile` declara todo el modo (gravedad, caída, salto, coyote, muro, pendientes); presets `plataformas()` (el juego actual, valores de `settings`), `cenital()` (AUD-328 como perfil, no como bandera) y `vuelo()` (AUD-335); el jugador y su máquina de estados lo consumen; `pendientes.py` parametriza el margen de pegado y la velocidad de deslizamiento | **HECHO (AUD-333)**, 15 pruebas nuevas, suite 4.158 verdes |
| **2. Resolutor de mundo compartido** | Sacar la resolución AABB + pendientes + plataformas de un sentido de `Player.update`/`EnemyBase.update` a un solucionador único `framework/physics/resolucion.py` que ambos (y cualquier entidad nueva) usen con su perfil | **HECHO (AUD-334)**: `EstadoDeMovimiento` + `Contacto` (hechos, no reglas) y cinco pasos puros —eje X, pared lateral de cuestas, eje Y, cuestas, repisas— compuestos por `resolver_movimiento` (con perfil, sin perfil asume plataformas; los modos sin gravedad —cenital y vuelo— saltan cuestas y repisas). El jugador conserva `_resolve_collision`/`_resolver_pendientes`/`_resolve_one_way_collision` como adaptadores delgados con los mismos nombres y firmas —los llaman pruebas y material copiado—; sonidos y recargas de salto quedaron fuera del resolutor (los decide la entidad con los hechos). 25 pruebas puras nuevas; suite 4.158 verdes; `test_rect_fusionado_suelo_y_pared` ahora fija el umbral `v_overlap <= 2` en `resolver_eje_x`, donde vive |
| **3. Física ampliada** | Fricción por superficie desde el TMX (materiales: hielo, arena…), aceleración/fricción por perfil, modo `vuelo` integrado (8 direcciones sin gravedad) | **HECHO (AUD-335 + AUD-336)**: vuelo como preset e integración (AUD-335, 10 pruebas). Aceleración/fricción por perfil (AUD-336): `PhysicsProfile.aceleracion` y `friccion` (px/s²) declaran cómo la velocidad real se acerca a la que fija la máquina de estados (`_aplicar_friccion_y_aceleracion`, con `acercarse_a` en el resolutor); con 0 —los tres presets— el comportamiento es exactamente el de siempre, y la suite lo verifica; 12 pruebas nuevas. La **fricción por superficie desde el TMX ya vivía en el ECS** (`ZonaDeFriccion` + `sistema_friccion`, AUD-236): recorta la velocidad ya producida, así que compone con la aceleración del perfil sin tocarse |
| **4. SpriteBatch** | Umbral automático + docstrings corregidos con la medición re-hecha (blits() gana o empata en todo el rango, 0,73-1,03×) | **HECHO (AUD-330)** |
| **5. GPU** | La ruta de sprites en tarjeta (quads instanciados, composición en GPU según `docs/74`), aislada y medible con `scripts/bench_sprite_batch.py`; activable por contexto. Incluye **normal mapping** (pedido 2026-08-07): normales por sprite y luz direccional/puntual en los shaders | **HECHO (AUD-340 + AUD-342)**: `SpriteBatchGPU` (`src/engine/render/gpu_sprite_batch.py`), instanciado, con atlas de color + atlas de normales opcional, tinte, cámara por uniforme y luz ambiental + direccional + hasta 4 focos puntuales con altura; las normales se **generan del alfa** del sprite (`normales.py`, numpy puro) porque no hay pipeline de assets; la rama plana dibuja el sprite tal cual, así que la ruta sin luz es indistinguible de un blit; 22 pruebas nuevas y el bench ahora mide el componente real (0,059 ms con 500 sprites en la Quadro, mejor que la ruta de referencia). **Lote 2 (AUD-342)**: la pasada de composición en `GLRenderer` (pasada 1.5, entre la subida de la escena y la refracción —los sprites se mezclan con su alfa como un blit y el bloom, la luz y la viñeta operan sobre lo ya compuesto) y el canal por `gpu_effects` (`publish_lote_de_sprites`/`published_lote_de_sprites`, activable por contexto): `GameContext.lote_de_sprites` expone el lote a las escenas sin que importen ModernGL, `App` lo cablea cada fotograma y un lote vacío no cuesta nada (0 llamadas de render). `volcar` enlaza el atlas a las unidades del sombreador y se niega a mezclar atlas en una sola llamada (un sampler: el mezclado daría sprites con texturas ajenas); 19 pruebas nuevas; suite 4.244 |
| **6. 2.5D** | Modo de orden por Y (pintor) opcional + mejora de `profundidad.py` | **HECHO (AUD-339)**: `orden_por_y` (propiedad de mapa) reordena las entidades por la misma ancla que escala —los pies, o `depth_y` si la entidad la declara (una voladora se ordena por su proyección en el suelo)— en vez de por `rect.centery`; sin la propiedad, el orden de AUD-067 queda intacto. `profundidad_curva` (float, `1` = la lineal de AUD-277) comprime el fondo con perspectiva de verdad. `stage0.tmx` declara las dos propiedades en su generador. 10 pruebas nuevas |
| **7. Reconstrucción de contenido** | Niveles y jefes de referencia rehechos para lucir las fases 1-6 | **Suspendida (2026-08-07, dueño)**: el contenido lo reconstruyen los estudiantes con el motor ya actualizado; el motor se da por servido |

## 27.1 Características pedidas por el dueño (2026-08-07)

Seis pedidos, con el estado real (sondeo, no suposición):

| Pedido | Estado |
|---|---|
| **Unificar el guardado** | **HECHO (AUD-337)**: `score.json` e `inventory.json` vivían en `data/`, dentro del árbol del proyecto — el defecto que AUD-157 arregló para las partidas. Ahora viven en el directorio del usuario y el fichero viejo se migra una vez (copia, sin borrar, sin sobreescribir); los catálogos de sólo lectura (`data/achievements.json`, `data/bestiary.json`) se quedan donde están. Las partidas (AUD-157), los logros y el bestiario ya estaban en el usuario: el estado del jugador queda entero en un sitio |
| **Árbol de habilidades** | **Ya existe (AUD-293)**: `skill_tree.py` con catálogo (Vitalidad, Fuerza, Ímpetu), costes crecientes, requisitos, escena (`SkillTreeScene`), guardado en el slot y puntos de habilidad desde la experiencia (AUD-267/292). Sin trabajo pendiente; ampliar el catálogo es decisión de diseño del contenido |
| **Niebla de guerra animado** | **HECHO (AUD-338)**: el velo estático de `fog_of_war.py` (AUD-111/213) respira — la opacidad de la mascara pulsa con `pulso`/`pulso_del_velo` (en fase cero del ciclo dibuja exactamente el estático de v1.0.0) y el radio crece con `velocidad`; `animado=false` devuelve el velo de siempre. 7 pruebas nuevas |
| **Normal mapping** | Pendiente — vive en la fase 5 (GPU), donde está el pipeline de shaders |
| **ambient_light** | **Ya existe**: propiedad de mapa (`StageData.ambient_light`), ciclo día/noche (`day_night.py`) y tinte de hora (`MezclaDeAmbiente`), con suelo de ambiente por zona en `stage_parts/ambiente.py` |
| **Sombras 2D proyectadas** | **Ya existe (AUD-278)**: `sombras_proyectadas.py` (proyección de silueta, rejilla de AUD-276, tope medido por foco), encendida por la propiedad de mapa `sombras_proyectadas` |

Dos notas de la fase 1 que conviene no perder:

* **El trinquete de calibración sigue vivo.** El preset `plataformas()` lee
  `settings` al construir el perfil, así que `test_calibracion_del_salto`
  sigue midiendo lo mismo y sigue fallando en voz alta si `GRAVITY` o
  `PLAYER_JUMP_FORCE` cambian.
* **La medición corrigió a AUD-329.** El «cruce en cientos de llamadas» que
  justificaba no bachear el parallax no se reproduce re-medido: es empate
  (0,97-1,03×) y con sprites pequeños `blits()` gana desde dos llamadas. La
  decisión de AUD-329 —no bachear el wrap— se mantiene, pero por el motivo
  correcto: no hay nada que ganar (AUD-330).

---

## 28. La lista de mejoras del dueño, contrastada fila a fila (2026-08-10, AUD-376)

El dueño trajo una tabla de ~250 filas de mejoras con prioridad (🔴🟠🟡🟢) y una
columna «situación actual», y preguntó si se puede implementar todo.

**La respuesta corta: técnicamente sí —es Python y el motor tiene los anclajes—
pero la tabla no sirve como plan tal cual, y el motivo no es el alcance.** Es
que su columna «situación actual» está desfasada respecto al árbol de hoy, y
como la prioridad se derivó de esa columna, la prioridad tampoco es utilizable.
Ejecutar la tabla al pie de la letra reescribiría trabajo hecho y probado.

Se sondearon ~45 de las filas más pesadas contra el código, no las 250.

### 28.1 Filas marcadas 🔴 que ya están hechas y probadas

Una muestra, con el sitio donde vive cada una:

| Fila de la lista | Qué hay realmente |
|---|---|
| Event Bus 🔴 | `engine/core/event_bus.py`, por inyección, sin global |
| Lifecycle global 🔴, estados globales 🟠 | `App._init_subsystems`/`_shutdown`; `SceneManager` + `TransitionManager` + `SceneRegistry` perezoso |
| Consolidar ECS 🔴, scheduling 🔴, prioridades 🔴 | `ecs/world.py`, `ecs/scheduler.py` con `Fase` explícita, borrado diferido, `censo()` |
| Frame budget 🔴, time scale 🟠, pause 🟠 | `DeltaClock`: tres relojes, composición de escalas por nombre, `MAX_FRAME_TIME`; `test_frame_budget` |
| Input mapping 🔴, rebinding 🟠, gamepad 🟠 | `Action` + `InputManager.rebind()`, ejes y hat de mando, `KeybindingScene` |
| Separar locomoción / combate / interacción 🔴 | Ya partido: `entities/states/{grounded,airborne,attack,ability,damage,rope,swim,wall}.py`, 27 clases (medido hoy con AST) |
| Triggers 🔴, debug renderer de física 🔴 | `hazard_system`, `interactable_system`, `gizmos.py`, `CollisionSystem.draw_debug` |
| **Raycasts 🔴** | `RejillaEspacial.rayo()` (AUD-276) — existe, pero ver GAP-037 |
| Slopes 🔴, one-way 🟠, moving platforms 🟠, ice/mud 🟠 | `pendientes.py`, `_resolve_one_way_collision`, `PlataformaMovil`, `ZonaDeFriccion` |
| Movement profiles data-driven 🔴 | `PhysicsProfile` con `plataformas()`/`cenital()`/`vuelo()` (AUD-333/335/336) |
| Render passes 🔴, batching 🔴, culling 🔴, render targets 🔴 | `gl_pipeline.py` (FBOs, `_run_shader_pass`), `gpu_sprite_batch.py` instanciado, `culling.py` |
| Shader fallback 🔴 | `GLRenderer._software_fallback` |
| Normal maps 🟢 | `render/normales.py` (AUD-340) |
| Light manager 🔴, shadows 🔴 | `LightSystem`, `sombras.py`, `sombras_proyectadas.py`, `day_night.py` |
| Camera bounds 🔴, dead zone 🟠, look-ahead 🟠, shake 🟠 | `_CameraLock`, `_fuera_de_la_zona`, `anticipacion`, `apply_shake` con dirección |
| 2.5D depth sorting 🔴, depth_y 🟢, curva 🟢 | AUD-339: `orden_por_y`, `profundidad_curva` |
| **World Simulation «Nuevo» 🔴** | Ya es módulo: `world/simulation.py` + `environment.py` |
| Audio buses 🔴, music state machine 🔴 | `mixer_buses.py`, `dynamic_music.py`, `music_clock.py` |
| **Dialogue «existente conceptualmente» 🔴** | `ui/dialogue_system.py`, 533 líneas: `DialogueTree.desde_datos()`, ramificación, retratos, acciones, paginado, i18n |
| **Boss «existente conceptualmente» 🔴** | `boss_base.py` + `boss_kit.py`: fases, `TELEGRAPHING`, puntos débiles, parry, arena; `grade_boss.py` en CI |
| Level validation 🔴, metadata 🔴 | `validate_tmx.py --ci`, `check_tmx_coverage.py --ci`, `generate_tmx_reference.py --check` — los tres bloquean merge |
| Asset cache 🔴, fallback 🔴, atlas 🔴 | `AssetLoader` con caché, desalojo y *scopes*; placeholder por categoría; `sprite_atlas.py` |
| Save slots 🔴, serialization 🔴, migration 🟠 | `SaveManager` con escritura atómica y migración; `integridad.py`; `test_corrupt_saves_are_loud` |
| Structured logging 🔴, crash context 🔴 | `core/registro.py` (AUD-268) |
| Central error handling 🔴, TMX errors con contexto 🔴 | `App.run` con `FrameworkUsageError` → `StageErrorScene`, corte a los N fallos seguidos |
| Build reproducible 🔴, packaging 🔴 | `scripts/build_executable.py`, pyinstaller+nuitka en `[dev]`, `test_version_coherence` |
| Architecture docs 🔴 | `03_ARCHITECTURE.md` + `test_architecture_doc_matches_tree` (la doc falla si el árbol cambia) |

Cuatro filas de la columna «situación actual» son directamente incorrectas y
conviene dejarlas por escrito, porque son las que más trabajo harían repetir:
**World Simulation** no es «nuevo» (es un módulo con pruebas), **Dialogue** y
**Boss** no son «existentes conceptualmente» (están implementados y calificados
por CI), y **«Enemies: 10 tipos»** son 30 registrados sobre ocho arquetipos.

### 28.2 Lo que sí falta — catorce huecos, en `KNOWN_GAPS.md`

Registrados como **GAP-036 … GAP-049**. Resumen:

| GAP | Hueco | Coste |
|---|---|---|
| 036 | Bucle sin paso fijo ni interpolación | Alto — ver §28.3 |
| 037 | La rejilla espacial existe y las colisiones no la usan | **Bajo** |
| 038 | Sin capas ni máscaras de colisión (= R-03, abierto desde julio) | Medio |
| 039 | Sin materiales de superficie (hay fricción, falta restitución) | Bajo |
| 040 | Buffer de entrada sólo para el salto, y dentro de `Player` | **Bajo** |
| 041 | ECS sin reciclado de ids, sin pools, sin serialización | Bajo |
| 042 | Sin determinismo reproducible (ningún `random.seed()` en `src/`) | Medio |
| 043 | Sin tipos de daño, armadura ni resistencias | Diseño |
| 044 | Sin buff/debuff | Diseño |
| 045 | Sin pathfinding ni árbol de comportamiento | Medio |
| 046 | La percepción de enemigos vive en código de escenario | Bajo |
| 047 | Sin sistema de misiones ni objetivos | Diseño |
| 048 | Sin streaming de niveles ni versionado de mapas | Bajo (versionado) |
| 049 | Sin contadores de recursos: llamadas de dibujo, memoria, fugas | Bajo (llamadas) |

Catorce sobre ~250 filas. Ahí está todo el valor de la lista.

### 28.3 Cinco filas que chocan con decisiones ya medidas de este repositorio

No son imposibles; son cosas que ya se decidieron **con medición**, y volver a
abrirlas exige volver a medir, no volver a opinar.

* **«Batching 🔴» y «GPU particles»** — AUD-330 re-midió: `blits()` gana o
  empata en todo el rango (0,73-1,03×). §10.3 de este documento lo tiene como
  *«viable, y medido en contra»*. La ruta de GPU existe (AUD-340/342) y está
  activable por contexto; lo que no procede es rehacer el batching de CPU.
* **«Utility AI»** — invariante 7: sklearn es opcional y no se mete ML donde
  una FSM determinista rinde igual. Cabe, con el fallback intacto.
* **«Dialogue localization» y «Text externalization»** — el juego ya es
  bilingüe (`i18n.py` + `check_translations.py --ci`). Traducir los 67
  documentos sigue chocando con la invariante 5, razonada en §21.6.
* **«Reducir estados redundantes 🔴»** — las clases de estado ya están
  separadas por responsabilidad en ocho ficheros. Sin señalar una redundancia
  concreta, esto es refactor por refactor. De paso, la cifra: son **27 clases**
  en `entities/states/`, y `AirborneState` es base de `JumpingState` y
  `FallingState` en vez de un estado en el que se pueda estar — de ahí los
  **26 estados** que cuenta §A de `62_ESTADO_DEL_PROYECTO.md`. Los dos números
  son correctos y cuentan cosas distintas; la lista del dueño dice 29, que no
  sale de ninguna de las dos cuentas.
* **«Definir arquitectura definitiva, límites entre módulos»** — definir
  contratos sí. Partir el paquete en `loi-math`/`loi-physics`/`loi-render` está
  declarado **inviable** en §10.2 y no ha cambiado nada que lo reabra.

**Y el paso fijo (GAP-036) merece párrafo propio**, porque es el único cambio
estructural de la lista y el único que puede romper contenido. La calibración
entera está atada al `dt` variable: `test_calibracion_del_salto` fija el salto
en **72 px**, que es la unidad con la que están medidos los 16 mapas de
`assets/` y las guías de `66_GUIA_DE_LEVEL_DESIGN.md`. Escribir el acumulador
es media tarde;
re-calibrar el salto y revisar si cada obstáculo sigue cabiendo, no. Es
decisión del dueño, no de ingeniería, porque lo que se decide es si se rompe la
métrica de 72 px.

### 28.4 Las dos veces que la medición corrigió a mi primera pasada

Mismo patrón que §16.1 y §17.1, y por eso se deja escrito:

1. **Dije que no había buffer de entrada. Sí lo hay.** `Player.update` lleva
   salto con buffer (`_pending_jump`, ~5 fotogramas) desde antes de esta
   auditoría. El hueco real es más estrecho y más barato de lo que escribí:
   existe para *una* acción y vive en la entidad, no en `InputManager`
   (GAP-040).
2. **Dije que las capas de colisión eran un hueco nuevo. Estaban registradas
   desde julio.** Son el punto de refactor **R-03** de `AUDIT_2026-07.es.md`,
   abierto, con su motivo y con un aviso que yo no tenía: AUD-004 quitó una
   fachada de pymunk cuyas categorías `_CAT_*` iban a `shape.collision_type`
   en vez de a `shape.filter`, y `add_static_collision` creaba un cuerpo por
   tile sin fusionar. Si vuelve una tubería de cuerpo rígido, no puede volver
   sin fusión de rectángulos (GAP-038).

En los dos casos el error iba en la misma dirección: **dar por ausente lo que
no encontré con la primera consulta**. La primera búsqueda de buffer usó
alternancia ERE mal escrita (`\|` dentro de `-E`) y no encontró nada en ningún
sitio; la segunda, ya correcta, encontró el salto con buffer. Un `grep` que
devuelve cero no es una medición hasta que se comprueba que el `grep` era
capaz de devolver algo.

---

## 29. El primer cable de la integración: el clima y el viento (2026-08-10, AUD-374)

Primer lote de la fase de *integration hardening* que fijó el dueño: hacer que
lo ya construido se comunique, sea observable, determinista y medible. El
orden acordado empieza por **comunicación**, y dentro de ella por el defecto
más barato de demostrar: un campo del ambiente que se calculaba y nadie leía.

### 29.1 Qué estaba mal

`EnvironmentState.viento` se computaba cada fotograma desde AUD-358 y tenía
**cero consumidores**. En paralelo, `WeatherSystem._set_climate_params`
sorteaba su propio viento con `random.uniform` y una segunda tabla de valores.
Que los números coincidieran —75 en `CLIMAS` frente al centro del
`uniform(50, 100)` del otro, 15 frente a `uniform(-15, 15)`, 12 frente a
`uniform(-12, 12)`— delata el origen: una decisión copiada, no dos decisiones.

Es la especie dominante de esta etapa, y aparece en el mismo fichero cuyo
docstring documenta F1.3 —*un viento calculado y asignado a nada*—. Se arregló
el síntoma en su día y quedó la causa. La familia completa: AUD-343 (la tubería
GL era código muerto), AUD-355 (la verja de datos hostiles estaba en la puerta
que nadie usa), AUD-366 (los tres huérfanos de logros).

### 29.2 Lo que la medición añadió, y era peor

El diagnóstico de GAP-050 decía que la divergencia «hoy no se nota porque los
dieciséis mapas declaran su `climate`». Se notaba, y en jugabilidad. Con la
secuencia real de `stage4_1` —mapa `fog`, acto `storm` pedido al VFX—:

    humedad 0,50 → suelo_mojado False

**Los actos de tormenta de `stage4_1` nunca resbalaron.** AUD-362 construyó el
hilo entero `lluvia → humedad → suelo mojado → frenado → control`, la escena lo
consume y hay pruebas que lo cubren; lo que fallaba es que el escenario cambiaba
el clima llamando al sistema de VFX, así que la simulación se quedaba con el
clima del TMX para siempre. El dato no faltaba: **llegaba caducado**, que es
bastante más difícil de ver que si no llegara.

Segundo defecto que el primero tapaba: el campo declara signo —«negativo =
hacia la izquierda»— y `CLIMAS` sólo tenía magnitudes positivas. El viento del
ambiente **nunca soplaba hacia la izquierda**. El contrato prometía un rango
que el productor no emitía.

### 29.3 Qué se hizo

* `viento_de(clima, rng)` en `world/simulation.py` es la única tabla de viento,
  y devuelve el valor **con signo**. `WeatherSystem` borró la suya.
* `WeatherSystem.aplicar_viento()` — la entrada que no existía.
* `SimulacionDeEscenario._cambiar_clima(nombre)` es ahora **la puerta** para
  cambiar el clima en marcha: se le pide al mundo, no al que dibuja la lluvia.
  `stage0.py:173` y `stage4_1.py:241` migrados.
* `_aplicar_clima(estado)` reparte clima y viento al VFX desde el mismo sitio
  donde `_aplicar_hora` reparte luz, bloom, tinte y agarre.
* `WorldSimulation` acepta un `rng: random.Random` propio — primer ladrillo de
  GAP-042, y lo que hace la prueba de la dirección reproducible.

13 pruebas nuevas en `tests/test_el_viento_es_uno_solo.py`, las 13 rojas antes.
Incluyen un cable trampa (`test_el_campo_viento_tiene_consumidor`) para que el
campo no vuelva a quedarse huérfano en silencio.

### 29.4 La dirección se probó al revés primero, y la suite la rechazó

El primer intento reconciliaba al contrario: la simulación siguiendo al
`WeatherSystem`, con la ventaja de no tocar ningún escenario. Pasaban las 13
pruebas nuevas y las 100 del lote dirigido. La suite completa devolvió **seis
en rojo**: las cinco de `TestElClimaCambiaLasReglas` y una de
`TestElMapaConfiguraYLaSimulacionCalcula` hacen `_simulacion.set_clima(...)` y
después `_aplicar_hora()` — o sea que el contrato «la simulación es la
autoridad» estaba escrito en las pruebas desde AUD-362, y el atajo lo violaba.

Se anota por dos motivos. El primero es que el atajo era tentador: costaba cero
cambios en escenarios y arreglaba el defecto visible. El segundo es que **un
lote dirigido en verde no es la suite en verde**, y aquí la diferencia fue
justamente la arquitectura.

Se registró también, y luego se retiró, un GAP nuevo para la flecha invertida:
otra sesión ya lo había escrito como GAP-050 mientras este trabajo estaba en
curso, con el número AUD-374 ya reservado para él. Coordinación por fichero, no
por conversación.

### 29.5 Y la suite volvió a corregir el trabajo, una segunda vez

Ya con la dirección buena, `_aplicar_clima` llamaba a `set_climate` en cada
fotograma y se apoyaba en la guarda interna de esa función —que se ignora a sí
misma cuando el clima no cambia— para no vaciar el emisor de la tormenta.
Funcionalmente inocuo, y sin embargo rojo:
`test_el_acto_se_aplica_una_vez_y_no_en_cada_fotograma` vigila que la **llamada
no ocurra**, no que sea inofensiva, y esa prueba salió de una comprobación de
mutación donde reaplicar el clima sin parar dejaba toda la suite en verde.

La comparación pasó al llamante. La lección es más general que el arreglo:
apoyarse en la guarda de otro módulo convierte un detalle de implementación
ajeno en algo de lo que dependes sin declararlo, y el día que esa guarda se
optimice, el emisor se vacía sesenta veces por segundo y nadie sabe por qué.

---

## 30. La semilla del azar (2026-08-10, AUD-375)

Segundo lote de *integration hardening*. Ataca la más débil de las cuatro
propiedades de la fase: **el motor no podía repetir una partida.**

### 30.1 Por qué antes que las sombras dirigidas por el sol

El orden que se había anunciado ponía Sol → Sombras en segundo lugar, por
`GAP-051` y por `docs/92` §4, que lo marca 🟡 «alto valor visual, el sistema de
proyección ya existe». Una comprobación previa lo desaconsejó:

    $ grep -rl "sombras_proyectadas" assets/
    (nada)

**Ningún mapa enciende las sombras proyectadas.** El sistema está construido,
cableado, medido y probado desde AUD-278, y no lo usa ningún contenido —es
opt-in por una propiedad de mapa, y nadie la ha puesto—. Añadirle una fuente
solar sería ampliar una característica que **nunca ha corrido en un mapa
real**, que es literalmente lo que la lista de «no hacer» del dueño prohíbe.

Se anota, además, porque el sistema es un caso más de la especie que domina
esta fase: construido, correcto, sin consumidor. La diferencia con el viento
huérfano (AUD-374) es que aquí la ausencia de consumidor es **una decisión de
contenido**, no un cable suelto — pero el efecto sobre el valor entregado es el
mismo, y merece decidirse en vez de heredarse.

### 30.2 El defecto

Cero llamadas a `random.seed()` en `src/engine` y `src/framework`. Las 46
llamadas a `random.*` del motor —repartidas en 15 módulos, con las partículas
de ambiente (12), el clima (9) y el sistema de partículas (6) a la cabeza—
tiraban del generador global sin sembrarlo nunca.

Lo que costaba, con nombres:

* **AUD-359** — «la prueba de presupuesto del 4-1 fallaba por el azar de una
  sola muestra». Sin poder fijar el azar, una prueba se escribe tolerante, y
  una prueba tolerante deja pasar las regresiones pequeñas.
* **Un informe de fallo no se puede reproducir.** «Se me cayó en el acto IV» no
  basta cuando la disposición de las partículas, el instante del rayo y la
  decisión del enemigo eran otras esa vez.
* **El fantasma del speedrun** no se puede validar contra una repetición.

### 30.3 Qué se hizo

`engine/core/azar.py`: `sembrar()`, `semilla_actual()` y `generador()`. `App`
siembra **inmediatamente después de configurar el registro**, y `main.py`
acepta `--semilla N` en las tres rutas de arranque (normal, `--stage`,
`--boss`).

La decisión que hace esto útil el primer día: **la semilla se escribe en el
registro** con nivel `INFO`. El registro va a un fichero junto a las partidas
(AUD-268), así que viaja dentro de cualquier informe sin que el jugador sepa
qué es una semilla. Sin eso, sembrar sólo sirve a quien ya sabe reproducir el
fallo — o sea, a quien no lo necesita.

Y por eso el orden importa y hay una prueba que lo fija: sembrar antes de
configurar el registro tira esa línea, y el defecto sería invisible —todo
funciona, sólo que el fichero no trae el número—.

**No se siembra con una constante.** Una partida que reparte siempre el mismo
rayo en el mismo segundo se lee como rota. Sin `--semilla` se inventa una y se
anota: azar de verdad, reproducible a posteriori. No ser determinista y no
saber qué pasó son cosas distintas.

11 pruebas nuevas en `tests/test_la_semilla_del_azar.py`, incluidas dos de
cable trampa: que `App` siga sembrando, y que las tres rutas de arranque pasen
la semilla —si una se olvida, repetir un fallo funciona en unos modos y no en
otros, que se diagnostica como «no se reproduce»—.

### 30.4 Lo que este lote NO cierra

`GAP-042` sigue abierto, con el alcance ya medido:

* **Aislamiento** — los 46 usos siguen compartiendo el generador global, así
  que añadir una tirada en las partículas desplaza la dispersión de los
  disparos. El camino es `azar.generador()`, y `WorldSimulation` ya lo recorrió
  (AUD-374). Van por lotes: son 15 módulos.

  *(AUD-385: y eran 46 de **66**. Faltaban los 20 de `np.random`, que es otro
  global distinto — ver §39.)*
* **Trayectoria** — el mismo replay bit a bit necesita el paso fijo de
  `GAP-036`. Con `dt` variable, dos ejecuciones divergen aunque el azar
  coincida. Sembrar da decisiones repetibles, no trayectorias repetibles, y
  conviene no confundir las dos al leer este lote.

---

## 31. La primera cifra de recurso: llamadas de dibujo (2026-08-10, AUD-377)

Tercer lote de *integration hardening*, sobre la tercera propiedad de la fase:
**observable**.

### 31.1 El desequilibrio que había

Este motor mide el tiempo por todas partes —`DeltaClock.historial_ms`, los
cuantiles P50/P95/P99 (AUD-346), `Planificador.tiempos()` por sistema del ECS
(AUD-347), `test_frame_budget`, `bench_sprite_batch.py`,
`bench_gpu_postproc.py`— y no medía **ni un solo recurso**.

La diferencia importa cuando algo va lento. «El fotograma cuesta 22 ms» no
distingue entre sobran pasadas de post-procesado y va lenta la CPU; el número
de llamadas separa las dos. Y es una cifra que esta tubería puede disparar sin
que se note, porque las pasadas se encienden por configuración —`gpu_effects`,
propiedades de mapa, opciones del jugador— y no por código nuevo que alguien
revise.

### 31.2 Las dos decisiones que hacen que el número no mienta

**Se suma después de las salidas tempranas.** `_run_shader_pass` se sale sin
dibujar en tres casos: sin contexto, sin VAO de quad y sin VAO del programa.
Un contador que sume al entrar mentiría exactamente cuando más falta hace,
porque el síntoma que se diagnostica con él es «esto no se está dibujando», y
la cifra tiene que **bajar** cuando algo deja de pintarse.

**El lote de sprites cuenta como una llamada, no como N sprites.**
`SpriteBatchGPU.volcar` manda 500 sprites en un `render` instanciado
(AUD-340), y ya devolvía cuántas órdenes dibujó sin que nadie mirase el valor.
Contar por sprite diría lo contrario de lo que la instanciación consiguió, que
es justo el número que alguien miraría para decidir si vale la pena.

### 31.3 Y quién publica la fila

La pone `App`, no la escena. `medidas_de_depuracion` es de la escena y sirve
para lo que la escena sabe —sus enemigos, sus partículas, su escuadrón—; la
tubería es del motor, y una escena no sabe cuántas pasadas de post-procesado
están encendidas, que es precisamente lo que hace subir el número.

7 pruebas nuevas, las 7 rojas antes. Dos son cable trampa contra la especie de
defecto que este repositorio lleva un mes cazando —una medición sin lector—:
que `App` publique la cifra y que la reinicie. El precedente está en AUD-050
(`SquadBrain.stats()` se calculaba desde siempre «para el overlay de debug» sin
un solo llamante) y en AUD-347 (los tiempos del ECS, medidos y nunca
mostrados).

Queda abierto el resto de `GAP-049`: memoria de textura, VRAM/RAM y detección
de fugas, que exigen instrumentar la subida de texturas, más el reparto
CPU/GPU del tiempo.

---

## 32. El guardián que no se miraba a sí mismo (2026-08-10, AUD-378)

Cuarto lote de *integration hardening*. Éste no salió de la lista de mejoras
sino del propio trabajo: al descartar las sombras dirigidas por el sol porque
**ningún mapa enciende las sombras proyectadas** (§30.1), quedaba una pregunta
incómoda. El repositorio tiene un guion escrito exactamente para detectar eso.
¿Por qué no lo había dicho?

### 32.1 Porque no estaba mirando

`check_tmx_coverage.py` vigilaba **18** propiedades de mapa. `StageLoader` lee
**38**. El informe cerraba con «Todas las propiedades de mapa están demostradas
en algún mapa» sin haber mirado veinte de ellas.

La causa es una comprobación de un solo sentido. `test_student_guidance.py`
verificaba que cada propiedad **declarada** existiera en `StageData`; nunca lo
contrario. Un guardián así no puede enterarse jamás de una propiedad que el
motor gane después — y el motor ganó veinte.

Es el patrón de esta fase con una vuelta de tuerca: lo construido-y-no-leído
era **el propio detector de cosas construidas-y-no-leídas**.

### 32.2 Dos preguntas que el guion confundía en una

Arreglarlo no era añadir veinte nombres a la lista: `--ci` falla si el mapa de
referencia cubre menos del 85%, y pasar de 18/18 a 18/38 lo habría puesto rojo
por un cambio de definición. Las salidas fáciles —bajar el mínimo, o llenar
`stage0.tmx` de `estamina`, `tiempo_bala` y `desfase_audio`— son apagar el gate
y arruinar el mapa que los estudiantes copian.

Lo que había debajo eran **dos preguntas distintas**, y ahora se responden por
separado:

| Pregunta | Métrica |
|---|---|
| ¿lo **enseña** el mapa de referencia? | `PROPIEDADES_MAPA`, la lista pedagógica, con su 85% |
| ¿lo ejercita **algún** mapa? | `PROPIEDADES_DEL_MOTOR`, todo lo que el cargador lee |

La segunda no existía. Es la que habría cazado `sombras_proyectadas`.

### 32.3 Las tres veces que la medición corrigió este mismo lote

Merece la pena por lo seguido que fue:

1. **El barrido por `props.get` se dejaba cuatro fuera.** `water_alpha`,
   `water_amplitude`, `water_frequency` y `water_speed` se leen con
   `_parse_unit_prop`. El punto ciego era de 21, no de 17. Lo cazó la prueba
   nueva en cuanto se escribió la lista a mano.
2. **El informe dio 20 «sin demostrar» y dos eran falsas.** Una sustitución que
   falló por su ancla abortó la del acumulador, así que el guion restaba la
   lista completa de una cobertura acumulada sólo sobre la pedagógica: todo lo
   de fuera de las 18 salía como no usado, incluido `bpm`, que declara
   `stage4_1.tmx:20`.
3. **`owner_id` no es propiedad de mapa.** AUD-350 se llevó los 19
   manejadores `_handle_*` a `stage_objetos.py`, lo que hacía razonable suponer
   que lo que queda en `stage_loader.py` es nivel de mapa. No del todo:
   `_build_waypoints` lee el `owner_id` de los objetos `Waypoint` con la misma
   forma. Cinco mapas lo declaran —en objetos— y el informe lo daba por no
   demostrado.

Las tres eran falsos positivos, y las tres habrían mandado a alguien a
perseguir un hueco inexistente. Por eso las 17 finales se verificaron **una a
una** con `grep` contra los `.tmx` antes de escribir el número en ninguna parte.

### 32.4 Lo que ahora se ve

17 características del TMX que no ejercita ningún mapa, registradas en
`KNOWN_GAPS.md` como **GAP-052**. No es una lista de tareas —varias son
deliberadamente opcionales, y `sombras_proyectadas` está apagada por defecto
porque cuesta y su módulo lo mide— pero sí es una decisión de contenido que
antes estaba escondida y ahora está a la vista.

El paso que convertiría el informe en guardián —triaje al estilo de
`check_orphan_systems.py`, con `--ci` fallando por lo que aparece **nuevo**— se
deja para cuando exista esa decisión: hoy nacería en rojo por las diecisiete, y
un gate que nace en rojo se desactiva.

---

## 33. La rejilla en las colisiones: medida en contra (2026-08-10, AUD-379)

`GAP-037` era, según lo escribí yo mismo en §28, «el candidato con mejor
relación coste/ganancia de toda la lista». Medido, no lo es. Y el motivo por el
que parecía serlo es un número que nadie había verificado.

### 33.1 La premisa

`rejilla.py` (AUD-276) justificaba su existencia diciendo que «`stage4_1` trae
miles de rectángulos y la inmensa mayoría están a pantallas de distancia de la
pregunta». `GAP-037` lo repitió, porque venía del docstring del módulo.

Contado sobre los dieciséis mapas del repositorio:

    51  stage4_1
    27  stage1_2_la_soda
    22  stage3_4_boss_gavilan
    14  stage2_2
    12  stage1_1
     …

**Cincuenta y uno**, no miles. Y no es que haya fusión de rectángulos en el
cargador —no la hay—: los mapas sencillamente no son tan densos.

### 33.2 La medición

Sobre `stage4_1`, cuerpo del tamaño del jugador, 4 rectángulos dentro de la
zona activa, 3.000 repeticiones de `resolver_eje_x` + `resolver_eje_y`:

| | ms/fotograma |
|---|---|
| lista completa (lo de hoy) | 0,0419 |
| con `cercanos()` (rejilla construida una vez) | 0,0310 |

1,35× más rápido, y **0,011 ms** de ahorro sobre un presupuesto de 16,67: un
**0,07%**. A cambio de eso habría que mantener un índice que se desincroniza
con lo que la escena ya recompone cada fotograma —plataformas móviles, bloques
rítmicos, interactivos que abren y cierran— y una ruta más que probar.

No se hace. Es la tercera vez en este repositorio que una optimización
estructuralmente correcta se cae al medirla: AUD-329/330 con el bacheo del
parallax, la propia rejilla en las sombras, y ahora ésta.

### 33.3 Lo que la medición explica hacia atrás

`sombras_proyectadas.py` dice, medido: «El cuello de botella es el relleno de
polígonos, no la búsqueda. La rejilla de AUD-276 se usa para no recorrer los
miles de rectángulos del mapa, y es la estructura correcta, pero medida no
cambia el resultado.»

Ahora se sabe por qué: **no había nada que acelerar**. Ese módulo recibe
exactamente la misma lista de 51 rectángulos.

### 33.4 Lo que NO se cae

La rejilla se queda, y su valor no era la fase amplia. `rayo()` y
`hay_vision()` contestan «¿qué hay **entre** este punto y aquel otro?», que
ninguna lista de rectángulos contesta por barrido, y son la base sobre la que
se apoya `GAP-046` —subir la percepción de enemigos al framework—. El docstring
del módulo queda corregido: dice lo que resuelve y dice lo que creía resolver y
no resolvía.

La decisión se vigila sola.
`tests/test_los_mapas_no_traen_miles_de_rectangulos.py` se pone rojo si algún
mapa supera 500 rectángulos, que es donde esta medición dejaría de valer, con
el mensaje explicando que hay que rehacerla. Es la misma especie que
`test_calibracion_del_salto`: no arregla nada, vigila la premisa de una
decisión.

### 33.5 Y una nota sobre el método

El primer intento de medir esto tardó más de diez minutos y hubo que tirarlo:
reconstruía la rejilla 300 veces por mapa, que no es lo que haría el motor
—se construiría una vez por escenario—. Medir mal es fácil y da números que
parecen respuestas. El que vale aquí es el de la rejilla construida una vez,
porque es el único que se parece a lo que costaría de verdad.

---

## 34. Siete de las diecisiete, demostradas (2026-08-10, AUD-380)

Primer lote sobre `GAP-052`, y el primero de esta sesión que sale de una
**decisión del dueño** en vez de de una medición: *«la idea es que todo este
cableado [sea] para que los estudiantes lo usen»*.

Eso resuelve la ambigüedad con la que se había redactado el hueco. Yo lo
escribí como «no es una lista de tareas, varias son opcionales a propósito», y
con ese criterio está mal: una característica que ningún mapa declara no la
descubre nadie —no se ve al jugar y no aparece abriendo un mapa en Tiled—, así
que las diecisiete son hueco de contenido de verdad. Apagada por coste y no
demostrada en ningún sitio son cosas distintas.

### 34.1 El bloque sin riesgo

Siete propiedades, todas sobre `stage_mecanicas`:

* **Las seis del agua.** Es el **único** mapa del repositorio con `WaterZone`,
  o sea el único sitio donde se pueden demostrar. El efecto existía desde
  `docs/47_WATER_EFFECT.md` y un estudiante sólo podía enterarse leyendo ese
  documento.
* **`desfase_audio`.** El mapa ya declaraba `bpm` y `compas`; ésta era la
  única de las tres que no declaraba ningún mapa, así que los bloques rítmicos
  seguían a la música con la latencia de la tarjeta y sin forma de corregirla.

Los valores son los del motor salvo dos, subidos para que la diferencia **se
vea** al abrir el mapa —que es de lo que va demostrar algo—: amplitud 4→6 px y
alfa 100→120. El tinte es el azul por defecto escrito explícito, para que se
lea el formato: `#2850a0` carga como `(40, 80, 160)`, comprobado.

**Se editó `tools/generate_stage_mecanicas.py`, no el `.tmx`.** El mapa es
generado, y tocar la salida se habría perdido en la siguiente regeneración —
todo el lote, sin que ninguna prueba lo notara hasta meses después.

**No se tocó `stage0`.** Es el mapa que copian los estudiantes y su lección es
el prólogo; llenarlo de propiedades lo convierte en muestrario y le quita
justo lo que lo hace útil.

    Propiedades que ningún mapa usa: 17 → 10

### 34.2 Las diez que quedan, y por qué no van igual

No es pereza; cada una tiene un motivo distinto y conviene que estén separados:

* **`camara` y `vista`** son modos de juego enteros. `vista=cenital` no es una
  propiedad que se añada a un mapa: es un mapa que se diseña. Desde el criterio
  del dueño éste es **el hueco más grande que queda** — el motor sabe hacer
  cenital, tiene sus pruebas, y ningún estudiante puede descubrirlo.
* **`sombras_proyectadas` y `god_rays`** cuestan, y la primera tiene medición
  detrás: el envolvente utilizable son cuatro o cinco focos. Encenderlas exige
  elegir el mapa mirando sus focos, no a bulto.
* **`estamina`, `tiempo_bala`, `habilidades_libres`** cambian cómo se juega el
  mapa donde se pongan. Es decisión de diseño, no de cableado.
* **`fog_of_war`, `profundidad_min`, `profundidad_max`** esperan a un mapa que
  las pida.

### 34.3 Lo que este lote enseña sobre el anterior

`AUD-378` abrió el guardián para que dijera la verdad, y la verdad resultó ser
accionable en una hora para siete de las diecisiete. Merece la pena anotarlo
porque el orden importó: **primero se arregló el instrumento, después se leyó
lo que medía**. Con el guardián ciego, estas siete llevaban desde AUD-216 y
AUD-137 sin que nadie supiera que faltaban.

---

## 35. Los guardias veían a través de las paredes (2026-08-10, AUD-381)

`GAP-046` decía que la percepción de enemigos vivía en código de escenario y
había que subirla al framework. **Era falso**, y debajo había un defecto
distinto y peor.

### 35.1 La premisa, corregida

`ConoDeVision` es un componente del ECS desde hace tiempo: vive en
`framework/ecs/components.py`, lo mueve `sistema_conos_de_vision`, tiene su
`Alerta` de cuatro estados y su gizmo de depuración en `stage/gizmos.py`. Su
docstring dice, literalmente, que existe «para no reescribirlo cada estudiante
que quiera un guardia» — justo lo contrario de lo que el hueco afirmaba.

El error vino de asociar `stages/stage1_1/combat/guard_system.py` con un
guardia enemigo. Es la mecánica de **defensa del jugador** —bloquear— y
coincidió en una búsqueda por texto que no verifiqué.

Es la **segunda** premisa falsa de las catorce que escribí en §28, después de
la de `GAP-037` («stage4_1 trae miles de rectángulos»: son 51). Las dos
salieron de dar por bueno el resultado de una búsqueda sin abrir el fichero.

### 35.2 El defecto que sí había

`sistema_conos_de_vision` decidía con dos cosas: distancia y ángulo. Nada más.
Un vigilante al otro lado de un muro **veía al jugador igual que si el muro no
existiera** — el mismo defecto que AUD-278 arregló para la luz, abierto
todavía para la vista.

Y pesa más que en la luz, porque cambia una regla en vez de un píxel: el sigilo
con muros no funcionaba, así que un nivel diseñado alrededor de esconderse
detrás de algo no se podía hacer.

### 35.3 La pieza estaba escrita para esto

`RejillaEspacial` (AUD-276) justificaba su existencia así: «no había forma de
preguntar "¿qué hay **entre** este punto y aquel otro?". Sin eso no se puede
hacer la línea de visión de un guardia».

Se construyó `hay_vision()`, se probó — y el guardia se escribió después sin
llamarla. Es la especie que domina esta fase, con una vuelta de tuerca nueva:
aquí el consumidor previsto llegó **más tarde** que la pieza y aun así no la
usó.

Cierra además el arco de AUD-379, que midió que la fase amplia de la rejilla no
aportaba nada y dejó dicho que su valor real eran `rayo()` y `hay_vision()`.
Éste es ese valor, cobrado: la rejilla pasa de un consumidor a dos.

### 35.4 Cómo llega la geometría

Por recurso del mundo (`poner_recurso("geometria", ...)`), que es el canal que
el ECS ya usa para `reloj_musical`. Dos decisiones que conviene no perder:

* **Sin recurso publicado, el sistema se comporta como antes.** No es una
  concesión a la compatibilidad: un mundo que no ha publicado geometría no
  permite deducir que hay un muro, e inventárselo dejaría ciegos a los
  vigilantes de cualquier prueba o entrega que monte un mundo desnudo. Las tres
  pruebas de sigilo de `test_ecs.py` siguen en verde sin tocarlas.
* **Se publican los sólidos del mapa, no los de la escena compuesta.** Las
  plataformas móviles, los bloques rítmicos y las puertas cambian cada
  fotograma, y reindexarlos por cada cambio devolvería exactamente el coste que
  AUD-379 descartó. Una plataforma móvil no tapa la vista de un vigilante; un
  muro sí, y los muros no se mueven.

6 pruebas nuevas, incluido el cable trampa de que el escenario publique el
recurso — sin él la lógica sería correcta y no se ejecutaría nunca, que es el
modo de fallo de AUD-050 y AUD-347.

### 35.5 Lo que esto obliga a hacer con las otras doce

Dos premisas falsas de catorce no es mala suerte: es que §28 se escribió
sondeando ~45 filas en una pasada y varias conclusiones se apoyaron en
búsquedas por texto sin abrir el fichero. Las doce entradas abiertas que quedan
de aquella pasada **no están verificadas al mismo nivel** que las cuatro que se
han trabajado desde entonces, y conviene decirlo antes de que alguien planifique
sobre ellas.

*(Resuelto en §36, AUD-382: se verificaron las doce y las doce se sostienen.
Esta advertencia se conserva porque explica por qué se hizo esa pasada.)*

---

## 36. Las doce premisas restantes, verificadas (2026-08-10, AUD-382)

§35.5 dejó dicho que las doce entradas abiertas de §28 no estaban verificadas
al mismo nivel que las trabajadas, después de que dos de catorce resultaran
falsas. Esta pasada las verifica una a una, **abriendo el código** y no
buscando texto. No implementa nada.

### 36.1 Resultado: las doce se sostienen

| GAP | Premisa | Comprobación |
|---|---|---|
| 036 | El bucle no tiene paso fijo | AST de `App.run`: sin acumulador, sin `fixed_update`, `dt` del reloj ✅ |
| 038 | Sin capas ni máscaras de colisión | AST de `collision_system`, `resolucion` y `components`: ni una definición ni un campo con `layer`/`mask`/`filter` ✅ |
| 039 | Materiales sin restitución | `PhysicsProfile` tiene 15 campos y ninguno es restitución ni rebote ✅ |
| 040 | Buffer sólo para el salto | `_pending_jump` en `Player`, y `InputManager` sin la primitiva ✅ |
| 041 | El ECS no recicla identificadores | AST de `crear` y `aplicar_bajas`: sin lista de libres ✅ |
| 042 | Sin determinismo | Cero `random.seed()`; parcialmente cerrado por AUD-375 ✅ |
| 043 | Sin tipos de daño | `_calculate_damage(self, player, enemy) -> float`, escalar; sin campos de tipo o resistencia ✅ |
| 044 | Sin buff/debuff | Sin campos de efecto temporal en componentes ni en `PlayerStateData` ✅ |
| 045 | Sin pathfinding ni árbol de comportamiento | Ninguna definición; ver §36.2 ✅ |
| 047 | Sin misiones ni objetivos | `ProgressionSystem` son puntos de control, disparadores y fin de escenario; ver §36.2 ✅ |
| 048 | Sin versionado de mapas | `schema_version` no aparece en el cargador ni en ningún `.tmx` ✅ |
| 049 | Sin contadores de recurso | Llamadas de dibujo ya sí (AUD-377); memoria de textura, VRAM y fugas, no ✅ |

### 36.2 Y tres falsos positivos más, de la misma familia

La verificación por AST destapó que las búsquedas por texto que había usado
originalmente estaban contaminadas por **coincidencias de subcadena**:

* `gastar_estamina` y `gastar` contienen **`astar`**. Ésa era la mitad del ruido
  de la búsqueda de pathfinding.
* `_on_save_requested`, `request_chromatic_aberration` y `_current_question`
  contienen **`quest`**. Ésa era toda la señal aparente de un sistema de
  misiones.

Ninguno es una definición real. Buscar por nombre de definición —clases y
funciones, con AST— los elimina de un golpe, y es lo que había que haber hecho
desde el principio.

### 36.3 El patrón que separa las dos falsas de las doce buenas

Merece la pena porque es predictivo, no anecdótico. Las dos premisas que
fallaron eran **afirmaciones positivas**:

* `GAP-037`: «`stage4_1` trae **miles** de rectángulos» — una cantidad. Son 51.
* `GAP-046`: «la percepción **vive en** `stages/stage1_1`» — una ubicación. Vive
  en el ECS desde hace tiempo.

Las doce que se sostienen son todas **afirmaciones negativas**: «no existe X».

Tiene sentido y conviene explotarlo: una ausencia se establece bien con una
búsqueda exhaustiva —si no aparece en ningún sitio, no está—, mientras que una
cantidad o una ubicación exigen **abrir el fichero y mirar**. Una búsqueda que
devuelve resultados dice dónde mirar; no dice qué hay allí.

La regla operativa para las próximas auditorías de este repositorio: *un «no
hay X» se puede sostener con una búsqueda bien hecha; un «X está en tal sitio»
o «X vale N» no se escribe sin haber abierto el fichero.*

### 36.4 Por qué esta pasada no trae prueba

No cambia comportamiento: confirma premisas. Escribir una prueba por cada una
—«sigue sin haber tipos de daño»— convertiría doce decisiones pendientes en
doce cables trampa que se pondrían rojos justamente el día que alguien las
implemente, que es el día que queremos. Los cables trampa se ponen sobre
decisiones *tomadas* (`test_los_mapas_no_traen_miles_de_rectangulos`, AUD-379),
no sobre huecos abiertos.

---

## 37. El laboratorio de la vista cenital (2026-08-10, AUD-383)

Segundo lote sobre `GAP-052`, y el que cierra el hueco más grande de los
diecisiete: **un modo de juego entero que ningún estudiante podía descubrir**.

### 37.1 Lo que faltaba

`vista=cenital` existe desde AUD-129. Apaga la gravedad, da movimiento en dos
ejes, ignora las plataformas de un solo sentido —desde arriba son muros
invisibles— y trae los tres modos de cámara. Tiene su preset de física
(`PhysicsProfile.cenital()`), sus pruebas unitarias (`test_vista_cenital.py`) y
su fila en la guía del motor.

Ningún mapa lo declaraba. Así que la vista cenital era, en la práctica, una
característica que no existía: no se ve jugando, no aparece abriendo un mapa en
Tiled, y sólo se podía encontrar leyendo la especificación — que es justo lo que
no se hace.

Es la misma forma de fallo que `stage_mecanicas` cerró para las once mecánicas
de la fase 5, un escalón más arriba: allí faltaban mecánicas, aquí faltaba una
**vista**.

### 37.2 El mapa

Tres salas de 18×14 comunicadas por puertas, 58×16 baldosas en total. Cabe en
pantalla y media, que es lo que se puede leer de un vistazo en Tiled.

Tres y no una porque `camara` tiene tres modos y el mapa existe para
enseñarlos: `seguir` va pegada, `zona_muerta` no reacciona hasta salir de un
margen central, y `sala` encuadra el recinto entero. El TMX declara `sala` —el
que da sentido a una planta con habitaciones— y lleva los otros dos comentados
al lado, a un cambio de palabra de probarse.

Cuatro propiedades que ningún otro mapa declaraba: `vista`, `camara`,
`profundidad_min` y `profundidad_max`. Las dos últimas van a 1,0 las dos, o sea
escala plana, que es lo que quiere una vista en planta pura; el comentario del
TMX dice cómo devolver la perspectiva.

**Sin enemigos, a propósito.** Los arquetipos actuales asumen plataformas, y
mezclar esa conversación aquí convertiría «así se declara una vista cenital» en
«así se hace un nivel cenital». Lo que faltaba era lo primero.

**Sin lógica en la clase**, igual que `stage_mecanicas` y por el mismo motivo:
todo vive en el TMX, así que un estudiante lo reproduce sin escribir una línea
de Python. Si hiciera falta código, no demostraría lo que pretende.

### 37.3 La prueba que importaba

`test_vista_cenital.py` ya comprobaba la física en aislamiento: un jugador con
`vista_cenital = True` no cae. Eso seguiría en verde con el mapa borrado.

Lo que faltaba era el camino entero —TMX → cargador → escena → jugador—, que es
donde estaba el hueco. La prueba nueva monta el escenario real, lo juega un
segundo y comprueba que el jugador **no se ha movido en Y**: en lateral, un
segundo de caída libre son cientos de píxeles. Mismo razonamiento que
`TestLaAtmosferaLlegaAlJuego` en `test_ambience.py`.

    Propiedades que ningún mapa usa: 17 → 10 → 6

### 37.4 Las seis que quedan

Ninguna es cableado; las seis son decisión:

* `estamina`, `tiempo_bala`, `habilidades_libres` cambian cómo se juega el mapa
  donde se pongan. Es diseño.
* `sombras_proyectadas` y `god_rays` cuestan, y la primera tiene medición detrás
  —el envolvente son cuatro o cinco focos—, así que encenderlas exige elegir el
  mapa mirando sus focos y no a bulto.
* `fog_of_war` espera a un mapa que la pida.

---

## 38. Cero propiedades sin demostrar (2026-08-10, AUD-384)

Tercer y último lote de `GAP-052`. El informe de cobertura cierra con **«todas
las propiedades de mapa están demostradas en algún mapa»**, que es la primera
vez que puede decirlo de verdad: hasta AUD-378 lo decía sin haber mirado veinte
de las treinta y ocho.

    17 (AUD-378, medido) → 10 (AUD-380) → 6 (AUD-383) → 0 (AUD-384)

### 38.1 Las seis últimas, y por qué cada una donde está

* **`estamina`, `tiempo_bala`, `habilidades_libres`** → `stage_mecanicas`. Sus
  propios docstrings explican por qué estaban apagadas: «encenderla para todos
  cambiaría cómo se juegan sin que sus autores lo pidan», «los dieciséis
  escenarios entregados están calificados». El laboratorio es exactamente donde
  eso no aplica, porque cambiar la jugabilidad **es su función**.
* **`sombras_proyectadas` y `god_rays`** → `stage_mecanicas`, con **dos** focos
  nuevos y no más. El módulo de sombras mide su propio coste y deja escrito que
  el envolvente utilizable son cuatro o cinco focos; con ocho, incluso con
  tope, se come el fotograma. Medido en este mapa antes de encenderlas:

      2 focos, 6 obstáculos
      sin sombras : 0,499 ms
      con sombras : 0,657 ms   (+0,158 ms = 1,0% del presupuesto)

  Los focos van en la sala del viento, que tiene techo, porque **una sombra
  proyectada se lee cuando hay una pared donde caer**. En campo abierto el
  efecto existe y no se ve, que es la peor forma de demostrar algo.
* **`fog_of_war`** → `stage_cenital`, y no al laboratorio lateral. Una vista en
  planta con niebla es la mazmorra clásica y se entiende sola; oscurecer el
  laboratorio de mecánicas taparía las once mecánicas que ese mapa existe para
  enseñar. 220 px deja ver la sala en la que estás y esconde las otras dos.

### 38.2 Tres cables trampa que saltaron, y qué se hizo con ellos

`test_profundidad_25d`, `test_sombras_proyectadas` y `test_tiempo_bala_enchufado`
tenían cada uno una prueba de la forma «ningún mapa entregado declara esta
propiedad». Se escribieron para demostrar que cada característica era
**aditiva**: que añadirla no cambiaba el juego de los dieciséis escenarios ya
calificados. Al encenderlas en los laboratorios, los tres se pusieron rojos —
correctamente.

La reacción fácil era borrarlos o relajarlos. En los tres se hizo lo mismo:

1. **Exceptuar el laboratorio por nombre**, no relajar la aserción: lo que
   vigilan sigue importando, y es que el contenido **entregado** no cambie.
2. **Añadir la prueba del sentido contrario.** Sin ella, si alguien borra la
   propiedad del laboratorio, la primera seguiría en verde —no habría mapas
   inesperados— y la característica volvería a no estar demostrada en ninguna
   parte. Que es el estado del que `GAP-052` la sacó.

Un cable trampa que salta cuando debe no es un estorbo: es la única señal de
que el cambio hizo algo. Relajarlo habría convertido tres guardianes en tres
comentarios.

### 38.3 Y el guardián que impide reabrirlo

`test_todas_las_propiedades_las_demuestra_algun_mapa` es estricto y no un
porcentaje. Con el criterio del dueño —el cableado existe *para que los
estudiantes lo usen*— «casi todas» no significa nada. Desde ahora, añadir una
propiedad al motor obliga a decidir, **en el mismo lote**, en qué mapa se
enseña, o a escribir por qué no.

Es la respuesta durable a cómo se abrió este hueco: no por una decisión, sino
por diecisiete veces que nadie tuvo que tomarla.

---

## 39. La semilla no sembraba el otro generador (2026-08-10, AUD-385)

AUD-375 tituló «el motor no podía repetir una partida, y ahora anota con qué
azar arrancó». La segunda mitad era cierta. La primera, no del todo.

### 39.1 El defecto

`azar.sembrar()` llamaba a `random.seed()`. **NumPy mantiene su propio
generador global**, ajeno a ése. Y el motor tiene **20 usos de `np.random`**:

    12  src/framework/vfx/particle_system.py
     6  src/engine/scenes/noise_lab_scene.py
     2  src/engine/scenes/pattern_demo_scene.py

Los doce primeros son los que importan: `ParticleEmitter` dibuja **todas** las
partículas del juego —chispas, sangre, polvo, lluvia—, y saca sus ángulos,
velocidades y tamaños de `np.random.uniform`. Así que la partida seguía sin
poder repetirse justo en lo más visible, mientras el lote anterior daba el
asunto por cerrado.

Demostrado sobre el sistema real, no sobre el generador: dos ráfagas de
`emit_directed` con la misma semilla daban velocidades de **-39,565 y 23,154**.

### 39.2 Cómo apareció

No lo encontró una prueba: apareció al empezar el aislamiento de `GAP-042b` y
mirar, módulo por módulo, **de qué generador tira cada uno**. El recuento de
`random.*` con el que se dimensionó AUD-375 —46 usos, 15 módulos— era correcto
y contaba sólo la mitad de la historia, porque la pregunta que hacía era «¿usa
`random`?» y no «¿de dónde saca el azar?».

Es primo del patrón de §36.3: la afirmación era **positiva** —«los 46 usos ya
son reproducibles»— y las positivas hay que verificarlas abriendo el fichero.
Aquí la trampa fue más fina: el número era verdad, pero el conjunto que contaba
no era el conjunto que importaba.

### 39.3 El arreglo, y lo que deliberadamente no hace

`sembrar()` siembra los dos globales. Se usa `np.random.seed` y no un
`Generator` nuevo a propósito: el código existente llama a `np.random.uniform`
directamente, y cambiar eso es el trabajo de aislamiento de `GAP-042b`. Esto
hace reproducible **lo que ya hay**, que es lo que AUD-375 prometía.

La prueba que lo fija no comprueba el generador —eso pasaría con un
`np.random.seed` puesto y nadie usándolo— sino `ParticleEmitter` de verdad, que
es quien tira de NumPy doce veces.

Las tres afirmaciones que quedaron mal en lo ya publicado —el docstring de
`azar.py`, la entrada de `GAP-042` y §30.4— están corregidas en vez de
reescritas: dicen lo que decían y a continuación lo que faltaba. Un documento
que borra su error pierde la única señal de que ahí hay algo fácil de volver a
equivocar.

---

## 40. El paso fijo, y la re-calibración que no hizo falta (2026-08-10, AUD-390)

`GAP-036` llevaba toda la sesión etiquetado como el lote peligroso: «el único
cambio estructural que queda», «el que puede mover el diseño de los dieciséis
mapas», «necesita decisión del dueño sobre romper la métrica de 72 px». Resultó
costar horas y no mover un solo mapa, y el motivo merece escribirse porque es
generalizable.

### 40.1 El defecto no era «falta el paso fijo»

Era que **la física dependía de los fotogramas por segundo de la máquina**.
Simulado sobre la integración real del salto (`GRAVITY = 800`,
`PLAYER_JUMP_FORCE = -380`, gravedad y luego integrar, que es el orden del
resolutor):

    120 fps        -> 88,67 px de ápice
     60 fps        -> 87,11 px
     30 fps        -> 84,00 px
    tope 0,05 s    -> 81,00 px   (MAX_FRAME_TIME, o sea 20 fps)
    casi continuo  -> 90,06 px

Un jugador con equipo lento salta **un 7 % menos alto**. Los dieciséis mapas
están medidos contra los 72 px que se alcanzan a 60 fps, así que un obstáculo
ajustado al límite era franqueable o no **según el hardware**. Eso llevaba ahí
desde el primer día y nadie lo había escrito como defecto: el `GAP-036`
original hablaba de reproducibilidad y de replays, no de que el juego se
jugara distinto en cada máquina.

### 40.2 Por qué la re-calibración fue una comprobación

La clave está en elegir `FIXED_DT = 1/TARGET_FPS`, o sea `1/60`:

* **A 60 fps la integración es idéntica a la de antes.** Un paso por fotograma,
  del mismo tamaño. Los mapas no cambian porque no cambia nada de lo que ya
  funcionaba.
* **El fotograma lento converge al valor bueno.** Antes, un tirón se integraba
  de una vez con un `dt` grande y el salto perdía hasta 6 px —más de un tercio
  de baldosa—. Ahora se reparte en varios pasos de `1/60` y el resultado se
  acerca al que los mapas suponen.

Cualquier otro valor —`1/120`, `1/50`, un paso «más preciso»— habría obligado a
re-calibrar de verdad y a revisar los dieciséis mapas. Elegir **el que los mapas
ya suponían** convierte semanas en horas.

Verificado, no supuesto: **111 pruebas de calibración, física del jugador,
perfiles y pendientes, todas en verde sin tocar un número.**

### 40.3 Tres decisiones del acumulador

* **El sobrante se guarda.** A 120 fps, un fotograma de cada dos no simula; si
  se tirara el resto, el juego iría a la mitad de velocidad.
* **Las transiciones siguen con `dt` variable.** Son presentación, no
  simulación: trocearlas no las hace más correctas y las dejaría a cero en un
  fotograma rápido, que es un parpadeo visible.
* **El tope de 5 pasos corta la espiral de la muerte**, y al alcanzarlo **tira**
  el tiempo sobrante. Conservarlo dejaría una deuda que el fotograma siguiente
  tampoco puede pagar, y el juego se quedaría clavado intentando alcanzarse a sí
  mismo. Se prefiere ir a cámara lenta antes que dejar de responder.

Y una que no es del acumulador: se consume el `dt` **escalado**, para que la
cámara lenta y el hit-stop sigan funcionando. Ralentizar el mundo es dar
**menos pasos por segundo real**, no pasos más cortos — pasos más cortos
volverían a hacer la física dependiente del reloj, que es justo lo que este
lote quita.

### 40.4 Lo que este lote NO cierra

La reproducibilidad de **trayectoria** —el mismo replay bit a bit— necesita
además que el azar esté sembrado, y lo está desde AUD-375/385. Con las dos
piezas, dos ejecuciones con la misma semilla y las mismas entradas deberían
coincidir; comprobarlo de punta a punta es un lote propio y no se ha hecho aquí.

Y sigue faltando la **interpolación** al pintar: con el paso fijo, si el
fotograma no cae justo sobre un paso, la posición dibujada es la del último
paso y no la interpolada. A 60 fps con paso de 1/60 eso casi nunca ocurre, así
que se deja fuera hasta que se note.

---

## 41. Dónde se retoma: las nueve que quedan, ordenadas por dependencia (2026-08-10)

La sesión de hoy cerró ocho huecos —`036`, `037`, `043`, `044`, `045`, `046`,
`050`, `052`— en veinte lotes, `AUD-374` a `AUD-390`. Esta sección existe para
que retomar no dependa de acordarse de nada.

### 41.1 El orden, y por qué es ése

No es por tamaño ni por prioridad: es por **qué desbloquea a qué**. El criterio
que lo generó fue una pregunta del dueño —«ordénalos de forma que se pueda
trabajar en paralelo y que lo grande salga primero»— y produjo una corrección
al plan anterior.

**Corrección registrada:** `GAP-036` estaba planificado *el último*, «para no
rehacer trabajo». Era al revés. Toca la integración física, y `038` (capas),
`039` (materiales) y `040` (buffer, que cuenta en fotogramas) **son física**:
construidos antes, habría habido que re-calibrarlos después. Se hizo primero
(AUD-390) y por eso la ola siguiente ya puede escribirse una sola vez.

### 41.2 Las tres olas que quedan

**Ola 2 — tres frentes que no comparten ficheros. Pueden ir en paralelo.**

| Frente | Huecos | Ficheros que toca |
|---|---|---|
| Física *(desbloqueado por AUD-390)* | `038` capas, `039` materiales, `040` buffer | `resolucion.py`, `collision_system.py`, `perfil.py`, `input_manager.py` |
| Observabilidad | `049` memoria de textura y fugas | `gl_pipeline.py`, `debug_overlay.py` |
| Datos e infraestructura | `048` `schema_version`, `041` pools e ids del ECS | `stage_loader.py`, `validate_tmx.py`, `world.py` |

**Ola 3 — espera a que la ola 2 suelte sus ficheros.**

* `042b` — aislar el azar en `ambient_particles`, `weather_system` y `camera`.
  Va **antes** que `051`, porque `051` toca esos mismos módulos.
* `051` — ambiente → sombras, audio y color grading. **No puede ir a la vez que
  `049`**: los dos escriben en `gl_pipeline.py`, que son 1.081 líneas y donde
  ya hubo un choque con otra sesión.

**Ola 4 — contenido.** `047`, objetivos declarados en TMX. No depende de nada
técnico.

### 41.3 Lo que exige una máquina despejada

`049` es medición de recursos y `038`/`039` cambian el camino de colisión, que
es lo que miden las dos pruebas de presupuesto de fotograma. Con la máquina
cargada esos números no valen.

La comprobación previa, que ya está en la memoria del proyecto y merece estar
aquí:

    python -c "import time;t=time.perf_counter();x=0
    for i in range(3_000_000): x+=i
    print(f'{(time.perf_counter()-t)*1000:.0f} ms')"

Máquina ociosa: **150-250 ms**. Al cerrar esta sesión marcaba **1.081**, o sea
cinco veces más lenta, y con eso la suite completa pasó de 5:39 a 12:17 y las
dos pruebas de milisegundos fallaron. **No se mide nada por encima de ~300 ms**,
y por encima de ~500 conviene ni lanzar la suite completa: no cabe en el tope de
diez minutos del entorno y hay que partirla en dos mitades.

### 41.4 Lo que esta sesión enseñó sobre los propios huecos

Tres de los cerrados hoy demostraron que **la entrada describía mal el
problema**, y en los tres el problema real era peor y más barato de arreglar:

* `GAP-037` decía «cablear la rejilla al camino de colisión». Medido, ahorraba
  0,011 ms de 16,67 — y su premisa era falsa: `stage4_1` no trae «miles de
  rectángulos», trae **51**.
* `GAP-046` decía «la percepción vive en código de escenario». Falso: es un
  componente del ECS desde hace tiempo. Debajo había guardias que **veían a
  través de las paredes**.
* `GAP-036` decía «falta el paso fijo, y re-calibrar los 72 px es caro». Debajo
  había que **la física dependía de los FPS de la máquina**, y la re-calibración
  no hizo falta.

El patrón: los huecos se escribieron **desde fuera**, mirando qué falta. Los
defectos aparecen **al entrar**, mirando qué hace el código. Por eso los lotes
que empiezan midiendo salen mejor que los que empiezan construyendo, y por eso
§36.3 —«un "no existe X" se sostiene con una búsqueda; un "X vale N" o "X está
en tal sitio", no»— es la regla más rentable de las que salieron hoy.
