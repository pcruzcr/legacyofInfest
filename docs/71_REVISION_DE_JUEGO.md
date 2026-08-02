---
document_id: "LOI-REVISION-71"
title: "Revisión de mecánicas, gameplay, funfactor y level design"
tags: ["revision", "gameplay", "level-design", "mecanicas", "medicion"]
source: "docs/71_REVISION_DE_JUEGO.md"
date_processed: "2026-08-02"
---

# Revisión de mecánicas, gameplay, funfactor y level design

**Fecha:** 2 de agosto de 2026 · **Protocolo:** `docs/69_PROMPT_AUDITORIA_MAESTRO.md`, dominios D5–D9
**Alcance:** los 17 mapas de `assets/maps/`, los 25 estados del jugador, los 13 de enemigo, las 11 mecánicas de componente y los 65 tipos que un TMX puede declarar.

Todo número de este documento sale de un comando. Donde no hay medición
posible —el *funfactor* no se mide con un script— se dice que es criterio, y se
propone en vez de afirmarse. Es la separación que exige §8-D9 del protocolo.

---

## 0. Resumen

| Revisión | Estado | Lo que hay que mirar |
|---|---|---|
| Mecánicas | **Sólida** | 65 tipos declarables, 11 mecánicas de componente, 25 estados. Nada roto; el problema era que 22 tipos no se podían usar por no estar documentados → **AUD-182, corregido** |
| Gameplay | **Sólido con una anomalía** | El salto sube más de lo que avanza (5,64 vs 5,34 baldosas). Es una decisión de diseño, pero explica los huecos imposibles de los niveles |
| Funfactor | **Dos irregularidades medidas** | Dos saltos bruscos en la curva, y un jefe más fácil que el nivel que lo precede |
| Level design | **Media 78,7 %, dos casos serios** | 3.048 px sin checkpoint en un nivel; la rúbrica penaliza usar las mecánicas del motor → **decisión pendiente** |

---

## 1. Mecánicas — qué existe de verdad

Inventario extraído del código, no de la documentación:

| Cosa | Cuántas | Dónde |
|---|---|---|
| Estados del jugador | **25** concretos (+3 clases base) | `entities/states/` — 9 módulos |
| Estados de IA de enemigo | **13** | `EnemyState` en `enemy_base.py` |
| Arquetipos de enemigo | **8** | `entity_factory._ENTITY_REGISTRY` |
| Especies con nombre | **21** (9 + 7 + 5 por zona) | `bestiary_registry.SPECIES` |
| Tipos estructurales de objeto TMX | **35** | `BUILTIN_OBJECT_TYPES` |
| Mecánicas de componente ECS | **11** | `stage_loader._handle_componente` |
| Total declarable en la capa `Objects` | **65** | suma verificada por `tests/test_referencia_tmx.py` |

Los 25 estados del jugador cubren lo que se espera de un plataformas de acción:
suelo (`Idle`, `Walking`, `Crouching`, `Slide`), aire (`Jumping`, `Falling`,
`AirChase`, `AerialAttack`, `AerialSlam`), pared (`WallSlide`, `LedgeGrab`),
cuerda (`Trepando`, `Tirolesa`), agua (`Swimming`), ataque (`ShortAttack`,
`LongAttack`, `DashAttack`), habilidades (`Dashing`, `Parry`, `Ultimate`,
`Grab`, `Throw`, `Charging`, `ChargeRelease`) y daño (`Hurt`, `Dying`).

**No se encontró ninguna mecánica rota.** El defecto real era de acceso, no de
implementación, y es el que sigue.

### AUD-182 — 22 de los 35 tipos se publicaban vacíos *(corregido)*

`docs/STAGE_CREATION.md` es la guía que un estudiante lee para construir su
nivel. Su tabla de tipos la genera `scripts/generate_tmx_reference.py`, y el CI
la vigila con `--check`. Aun así, **22 de los 35 tipos estructurales salían
publicados como `| — | — |`**: sin geometría y sin propiedades.

Entre ellos: `Spring`, `Conveyor`, `MovingPlatform`, `WaterZone`, `WindZone`,
`LaserZone`, `RhythmBlock`, `SinkingPlatform`, `Guard`, `Stalker`, `Vine`,
`Zipline`, `Pickup`, `Key`, `Door`, `LockedDoor`, `Cage`, `Chest`,
`EventTrigger`, `Light`, `FrictionZone` y `ShockwaveZone`. Es decir: **casi
todo lo que convierte un mapa en un nivel**.

El estudiante veía que el tipo existe y no tenía forma de saber qué acepta.
Peor: una fila en blanco se lee como «no acepta propiedades», cuando
`MovingPlatform` tiene cuatro, `Guard` cinco y `Zipline` cinco. La información
estaba en los docstrings del cargador, que es donde un alumno de segundo año no
va a mirar.

**Por qué el gate no lo veía.** `--check` compara el documento contra la salida
del generador. Si el generador emite `—`, un documento con `—` está «al día».
El gate comprobaba coherencia entre el doc y una tabla incompleta — una
comprobación que se cumple sola, el mismo modo de fallo que AUD-170 y GAP-023.

**Corregido:** las 22 filas se completaron con la geometría y las propiedades
reales leídas del cargador, con sus valores por defecto. `tests/test_referencia_tmx.py`
(71 casos) falla ahora si un tipo aceptado se publica sin geometría o sin
propiedades; un tipo que legítimamente no acepta ninguna debe declararse en
`SIN_PROPIEDADES` con su motivo escrito. Añadir la mecánica número doce sin
documentarla pasa a ser un fallo de CI.

---

## 2. Gameplay — la envolvente del jugador, medida

Calculado de `settings.py` con la física real del motor:

| Magnitud | Valor | En baldosas de 16 px |
|---|---|---|
| Altura máxima de salto | 90,2 px | **5,64** |
| Alcance horizontal andando | 85,5 px | **5,34** |
| Tiempo en el aire | 0,950 s | — |
| Alcance con salto aéreo | 171,0 px | 10,7 |
| *Coyote time* | 6 fotogramas | **100 ms** |
| Vida del jugador | 5,0 | 20 golpes de zona 1 |

**Lo que está bien.** Hay *coyote time* (100 ms, medido en tiempo real y no en
fotogramas — lo arregló una auditoría anterior), hay *jump buffer*, hay corte
de salto (`jump_cut`), hay salto aéreo y hay *dash*. Es el kit completo de
sensación de un plataformas moderno, y está implementado donde debe estar.

**La anomalía: el salto sube más de lo que avanza.** La relación
altura : alcance es **1,05 : 1**. En la mayoría de los plataformas de
referencia esa relación va de 1 : 1,5 a 1 : 2 — se avanza más de lo que se
sube. Aquí el arco es casi vertical, con dos consecuencias:

1. Los huecos horizontales anchos se vuelven imposibles enseguida: sin salto
   aéreo, cualquier hueco de más de 85 px (5,3 baldosas) no se cruza.
2. Con 0,95 s en el aire, el jugador pasa casi un segundo sin control fino
   sobre un salto completo. Es una sensación flotante, de gravedad baja.

**Esto no se ha tocado, y no debe tocarse a la ligera.** Cambiar `GRAVITY` o
`PLAYER_JUMP_FORCE` recalibra los 17 mapas a la vez y puede romper entregas de
estudiantes ya calificadas (invariante 2). Se documenta porque **explica** los
huecos imposibles de §4, no como defecto a corregir. Si algún día se ajusta, el
orden correcto es: cambiar la física, reejecutar `grade_stage.py` sobre los 17
mapas y comparar antes/después.

---

## 3. Funfactor — lo que sí se puede medir

El *funfactor* no se cierra con una prueba, y este documento no va a fingir lo
contrario. Lo que sí tiene el repositorio es `scripts/difficulty_curve.py`, que
mide exigencia por escenario. Salida real:

| Escenario | Pantallas | Enem./pant. | Peligros/pant. | Índice |
|---|---|---|---|---|
| stage0 | 2,0 | 4,5 | 1,0 | 48,8 |
| stage1_1 | 4,8 | 2,3 | 0,0 | 23,5 |
| stage1_2_la_soda | 1,0 | 2,0 | 0,0 | 17,5 |
| stage1_3_las_aulas | 4,0 | 3,0 | 1,0 | 36,5 |
| **boss_venado** | 4,1 | 0,2 | 0,0 | **16,8** |
| stage2_1_oficinas | 4,0 | 2,0 | 0,0 | 30,0 |
| stage2_2 | 2,4 | 2,9 | 0,4 | 32,2 |
| **boss_rey** | 1,4 | 0,7 | 0,0 | **12,4** |
| stage3_1_la_entrada_de_piedra | 2,0 | 5,0 | 0,0 | 34,9 |
| stage3_3_el_patio | 1,2 | 9,2 | 0,0 | 36,4 |
| **stage4_1** | 2,0 | **0,0** | **6,0** | 36,8 |
| **boss_paburu** | 1,0 | 1,0 | 0,0 | **13,4** |

### 3.1 Dos saltos bruscos, detectados por la herramienta

```text
· stage1_2_la_soda (17.5) → stage1_3_las_aulas (36.5)
· boss_rey (12.4) → stage3_1_la_entrada_de_piedra (34.9)
```

Más del doble de exigencia entre niveles consecutivos. El primero duplica la
carga justo después del nivel más suave del juego.

### 3.2 Los tres jefes son los momentos **más fáciles** del juego

Los tres índices más bajos de la tabla son los tres jefes: 12,4 · 13,4 · 16,8,
frente a una media de 30,2 en los niveles normales. `boss_venado` (16,8) llega
después de `stage1_3_las_aulas` (36,5): el jugador atraviesa el nivel más
exigente de la zona y su recompensa es el encuentro más tranquilo.

**Matiz honesto:** el índice pondera enemigos y peligros por pantalla, y un
jefe es *un* enemigo con muchas fases. La métrica no modela fases, telegrafiado
ni patrones, así que **subestima estructuralmente a los jefes**. `grade_boss.py`
puntúa `boss_venado` con un **100 %** en su propia rúbrica —fases, telegrafiado,
puntos débiles, 9 conexiones de evento—, que es la medición que sí le
corresponde. Lo que la tabla dice de verdad es que *la curva del recorrido* baja
en los jefes, no que los jefes estén mal hechos.

### 3.3 `stage4_1`: un nivel sin un solo enemigo

6 peligros por pantalla y **0 enemigos**. Es una decisión defendible —un nivel
de puro plataformeo entre peligros, como el cementerio que su nombre sugiere—
pero conviene que sea deliberada y no un olvido: es el único nivel del juego sin
un solo enemigo, y llega en la zona 4.

### 3.4 Propuestas (criterio, no medición)

1. Subir la exigencia de los tres jefes, o bajar la del nivel que los precede,
   para que el jefe no sea un descanso.
2. Suavizar el salto `la_soda → las_aulas` metiendo un tramo intermedio o
   repartiendo enemigos.
3. Decidir explícitamente si `stage4_1` se queda sin enemigos, y si es así,
   anotarlo en su ficha de nivel para que no se lea como un descuido.

Ninguna de las tres se ha aplicado: las tres cambian el diseño del juego, y el
protocolo (§9) manda parar y preguntar antes de eso.

---

## 4. Level design — 17 mapas calificados

`python scripts/grade_stage.py assets/maps/ --json`. **Media: 78,7 %.**

| Mapa | % | ¿Salida alcanzable? | Huérfanas | Saltos imposibles | Peor tramo sin checkpoint |
|---|---|---|---|---|---|
| boss_rey | 59,2 | no* | 3 | 0 | 0 |
| boss_paburu | 63,8 | no* | 1 | 1 | 941 px |
| boss_venado | 66,9 | no* | 0 | 0 | 0 |
| hall | 70,0 | no | 1 | 2 | 747 px |
| stage4_1 | 72,3 | sí | 0 | 0 | 688 px |
| stage2_1_oficinas | 73,8 | sí | 0 | 0 | **3.048 px** |
| stage_mecanicas | 75,4 | no* | 3 | 2 | 944 px |
| stage1_1.RESPALDO | 76,9 | — | — | — | — |
| stage3_1_la_entrada_de_piedra | 77,7 | sí | 0 | 0 | 785 px |
| stage3_4_boss_gavilan | 78,5 | sí | 2 | **5** | 600 px |
| lobby_datacenter | 80,0 | sí | 0 | 0 | 319 px |
| stage1_2_la_soda | 80,0 | sí | 0 | **13** | 393 px |
| stage3_3_el_patio | 81,5 | sí | 2 | 3 | 489 px |
| stage1_3_las_aulas | 84,6 | sí | 1 | 0 | 640 px |
| stage1_1 | 97,7 | sí | 1 | 0 | 484 px |
| **stage0** | **100,0** | sí | 0 | 0 | 368 px |
| **stage2_2** | **100,0** | sí | 0 | 0 | 455 px |

`*` falso positivo conocido; ver §4.2.

### 4.1 El caso serio: 3.048 px sin checkpoint en `stage2_1_oficinas`

Seis veces el máximo recomendado (500 px). Morir al final de ese tramo cuesta
rehacer casi la mitad del nivel. Es el defecto de ritmo más caro de los 17
mapas y el que más probablemente hace abandonar a un jugador.

`stage2_1_oficinas` es entrega de estudiante: **no se toca** (invariante 1). Se
califica con la rúbrica, que ya lo está penalizando.

### 4.2 La rúbrica penaliza usar las mecánicas del motor — *decisión pendiente*

Cuatro mapas puntúan **0 de 12** en `design_completable` con el error «no hay
ruta de plataformas desde el spawn hasta el NextTrigger». Tres son arenas de
jefe, y el propio grader ya avisa de que la métrica no les aplica.

El cuarto es **`stage_mecanicas.tmx`**, que es material del motor y el nivel
escaparate de las once mecánicas. Contiene 11 objetos de movilidad: 4
`RhythmBlock`, 2 `MovingPlatform`, 1 `Spring`, 1 `SinkingPlatform`, 1
`Conveyor`, 1 `WindZone` y 1 `WaterZone`.

El analizador de alcanzabilidad **no modela ninguno de ellos**. Su propio
docstring lo dice:

> «no modela dash, salto de pared ni plataformas móviles, así que puede
> declarar *inalcanzable* algo que un jugador experto alcanza»

Es decir: el nivel construido para enseñar las mecánicas del motor pierde 12
puntos de nota **por usarlas**. Y con él, cualquier alumno que resuelva un
tramo con un resorte o una tirolesa en lugar de con un salto.

**No se ha corregido, a propósito.** `grade_stage.py` es la herramienta de
calificación: tocarla cambia notas, y §9 del protocolo manda parar y preguntar
antes de modificar la rúbrica. Las opciones, para quien mantiene el temario:

1. **Modelar las mecánicas en el grafo de alcanzabilidad** — lo correcto de
   fondo, y lo más caro: hay que dar a `Spring`, `Zipline`, `Vine` y
   `MovingPlatform` una envolvente propia.
2. **Declarar el mapa como no juzgable por esta métrica**, igual que se hace
   con las arenas de jefe (una propiedad de mapa `sin_ruta_de_salto`).
3. **Dejarlo como está** y aceptar que un nivel con movilidad no llega al 100 %.

La 2 es la barata y honesta; la 1 es la que de verdad resuelve el problema para
los estudiantes.

### 4.3 Saltos imposibles: 13 en `stage1_2_la_soda`, 5 en `stage3_4_boss_gavilan`

Un «salto imposible» es un hueco más ancho que 171 px, el alcance con salto
aéreo incluido. Los dos mapas son entregas de estudiante y no se tocan; la
rúbrica ya los penaliza. Se anotan aquí porque §2 los explica: con una
envolvente de salto tan vertical, es fácil dibujar en Tiled un hueco que parece
razonable y no se puede cruzar.

### 4.4 Dos ficheros de respaldo versionados y calificados como niveles

```text
assets/maps/stage1_1/stage1_1.RESPALDO.tmx
assets/maps/stage1_2_la_soda/stage1_2_la_soda.tmx.bak2
```

Los dos están **rastreados en git**, y el primero lo califica `grade_stage.py`
como si fuera un nivel más (76,9 %), contaminando la media de los 17. Los dos
pertenecen a carpetas de entregas de estudiante, así que **no se han borrado**:
la invariante 1 protege ese material y borrar es irreversible. Queda como
decisión de quien mantiene el curso.

---

## 5. Qué se corrigió aquí y qué no

**Corregido:** AUD-182 — los 22 tipos de objeto sin documentar, con la prueba
que impide que vuelva a ocurrir.

**Reportado y no tocado, con su motivo:**

| Hallazgo | Por qué no se toca |
|---|---|
| Envolvente de salto casi vertical | Cambiarla recalibra los 17 mapas y afecta a entregas ya calificadas (invariante 2) |
| Rúbrica que penaliza la movilidad | Cambia notas de estudiantes; §9 manda preguntar |
| 3.048 px sin checkpoint, 13 saltos imposibles | `src/stages/` y sus mapas son entregas de estudiante (invariante 1) |
| Jefes por debajo de la curva | Cambia el diseño del juego |
| Dos `.bak` versionados | Material de estudiante; borrar es irreversible |

---

## Documentos relacionados

- `docs/STAGE_CREATION.md` — la guía que AUD-182 completó
- `docs/66_GUIA_DE_LEVEL_DESIGN.md` — criterios de diseño de nivel
- `docs/18_ENEMY_ROSTER.md` — las 21 especies, verificadas contra el código
- `docs/70_INFORME_DE_AUDITORIA_VIVO.md` — el informe por iteraciones
- `KNOWN_GAPS.md` — deuda registrada
