---
document_id: "LOI-LVL-4-1D"
title: "Diseño 4-1 — El Cementerio Sagrado"
aliases: ["Diseño del Cementerio Sagrado", "4-1 Design", "El Despertar de Paburu"]
tags: ["level", "zona-final", "design", "folklore", "paburu"]
description: "Diseño del 4-1 horizontal: seis secciones con terreno propio, cutscene, diálogo de los espíritus y el despertar de Paburu"
source: "docs/niveles/15_DISENO_4_1_EL_CEMENTERIO.md"
---

# DISEÑO 4-1 — EL CEMENTERIO SAGRADO

**Nivel:** 4-1 · **Tipo:** Travesía atmosférica horizontal · **Reemplaza**
al prototipo del pozo vertical (AUD-462…466 — ver `13_STAGE_4_1.md` §0)

> **Por qué horizontal.** El guion original lo dice dos veces: *«a medida
> que avanzan, atraviesan diferentes espacios»* y *«el nivel puede
> construirse como un único stage4_1.tmx, dividido internamente en seis
> secciones»*. Un pozo vertical no es «atravesar espacios», es «bajar un
> pozo» — son geometrías distintas y la primera reconstrucción se equivocó
> de una por la otra. Esta versión es horizontal, un TMX, seis secciones
> concatenadas de izquierda a derecha, cada una con su propio terreno (no
> el mismo suelo con un filtro de color).

---

## 1. Geometría base

Pozo → pasillo: 900 × 38 baldosas (14.400 × 608 px), seis secciones de 150
baldosas (2.400 px, 4 pantallas) cada una, suelo a la altura de la fila 30
salvo donde el diseño de una sección lo cambia (la loma de la Fase 3). La
misma proporción que ya usan otros escenarios horizontales del proyecto
(`stage2_1_oficinas`: 200×38; `stage3_1_la_entrada_de_piedra`: 100×14) — no
la de un pozo.

Checkpoints cada 28 columnas (448 px), por debajo del límite de 500 px que
recomienda el calificador — unos 32 en total.

## 2. Un tileset propio por sección

`tileset_stage4_1.png` (generado por código, mismo camino que
`tileset_cemetery.png`), con **seis familias de baldosa**, una por sección:

| Sección | Familia | Qué se ve |
|---|---|---|
| 1 | Cripta | Losa de piedra lisa, junta de mortero |
| 2 | Bosque | Tierra con raíces, musgo y lodo como superficies (dos frenos del mismo tipo, AUD-236/AUD-473) |
| 3 | Camino de huesos | Tierra pálida con calaveras y costillas incrustadas |
| 4 | Bosque quemado | Ceniza y tierra requemada, tocones |
| 5 | Tumbas | Tierra desnuda, losas de tumba hundidas |
| 6 | Piedra sagrada | Piedra con vetas verdes que se iluminan (grietas por pisada) |

El terreno **cambia de verdad** entre secciones — no es la misma baldosa con
una matriz de color encima, que fue exactamente lo que el dueño rechazó del
primer intento.

## 3. Las seis secciones

### 3.1 Fase 1 — El Cementerio de Tilarán (columnas 0–149)

Color pleno, clima en calma. El jugador reconoce el espacio como un
cementerio real antes de lo sobrenatural.

**El easter egg** (§4 del guion original: *«un easter egg personal
relacionado con la ubicación»*): dos lápidas, una junto a la otra, hacia la
columna 30 — **Teresa Murillo** y **Hugo Salazar Castillo**. Un fantasma
—silueta suave, blanca, sin amenaza, distinta de los tres espíritus de
jefe— ronda despacio la tumba de Teresa. Sin fechas ni texto añadido: son
los dos nombres que dio el dueño del proyecto, nada inventado encima.

### 3.2 Fase 2 — El Venado (columnas 150–299)

La lluvia marca la entrada, la imagen se desatura hasta blanco y negro de
alto contraste. El suelo de bosque introduce musgo (frena al 94 %) y lodo
(frena al 88 %) — dos frenos del mismo mecanismo (`ZonaDeFriccion`,
AUD-236), el musgo más suave que el lodo. La primera versión hacía que el
musgo *arrastrara* (cinta transportadora, AUD-473: el jugador cruzaba sin
soltar el control en ningún otro punto del nivel, y en una partida real se
veía como el juego congelado) — corregido a un freno como el lodo, sólo que
más leve. `sfx_environment_viento_de_bosque` (AUD-465) como ambiente. El
Venado testifica y asciende al final del tramo.

### 3.3 Fase 3 — El Rey Terciopelo (columnas 300–449)

Escala de grises, camino de calaveras y huesos. Tormenta con rayos y viento
(`WindZone` a lo largo de toda la sección — el *«carácter ventoso»* que
menciona el guion). **Una loma real**: el suelo sube de la fila 30 a la 20
entre las columnas 340 y 370 (`Slope`, AUD-297), se mantiene arriba hasta la
370–410, y baja de vuelta entre la 410 y la 440 — un desnivel real dentro
del camino, no un parche de 80 px en un pozo. `sfx_environment_
storm_ambient` (reusa el fichero del prototipo). Una silueta de serpiente
—no la que asciende, una presencia de fondo aparte— repta despacio entre
los huesos (§Fase 3 del guion: *«movimientos de serpientes, huesos... en el
fondo»*). El Rey Terciopelo testifica y asciende.

### 3.4 Fase 4 — El Gavilán (columnas 450–599)

Vintage naranja, bosque cortado y muerto — tocones y tierra quemada de
verdad, no color sobre cripta. A media sección, el clima calla de golpe:
partículas a cero, ambiente cortado en seco (`stop_ambient`, sin fundido —
es un silencio súbito). En ese silencio, un camera shake fuerte y breve,
una sola vez. Después: el grito aislado del Gavilán (AUD-465,
`sfx_environment_grito_de_gavilan`) **y ahora también una sombra de ave**
cruzando el cielo de vez en cuando, coordinada con el grito — la pieza que
el primer intento dejó fuera (`GAP-058`). El Gavilán asciende.

### 3.5 Fase 5 — La Planicie de los Muertos (columnas 600–749)

Nocturno azulado, la sección más oscura. Un ciclo de luna (período 6 s)
determina cuándo se ve el entorno y cuándo no. Tierra desnuda con losas de
tumba hundidas — las de los conquistadores que murieron aquí, sin dueño que
reclamar. Un coro sin palabras (`sfx_environment_canto_ancestral`, AUD-465)
como ambiente. Sin espíritu de jefe: los tres ya ascendieron.

### 3.6 Fase 6 — El Camino hacia Paburu (columnas 750–899)

Color pleno, sin gradación. Niebla sobrenatural (partículas `spores`
verdes). Grietas que se iluminan al paso, sin quedar encendidas — un
rastro, no un progreso acumulado (mecánica sin cambios del prototipo).
`sfx_environment_resonancia_solemne` (AUD-465) como ambiente. Al final,
`NextTrigger` hacia `stage4_2_boss_paburu`.

## 4. La introducción

Un objeto `Cutscene` de tipo punto (dispara sin que el jugador tenga que
entrar en una zona — `stage_objetos.py::_handle_cutscene`, AUD-136) en el
`PlayerSpawn`, con un guion en el mini-lenguaje de `cutscene_guion.py`:
fundido desde negro, un par de líneas de `dialogo` con las voces en lengua
indígena que hablan de Paburu (texto abstracto, sin fingir una lengua real
— el mismo principio ya aplicado a `canto_ancestral`), un barrido de cámara
hacia el cementerio. Ningún sistema nuevo: `CutsceneSystem` ya está
completo (`42_CUTSCENE_SYSTEM.md`) y hasta ahora este nivel no lo usaba.

## 5. El diálogo de los tres espíritus

`data/dialogues/stage4_1.json`: tres árboles (`venado`, `rey_terciopelo`,
`gavilan`), cargados automáticamente por `stage_id`
(`cinematicas.py::_cargar_los_arboles_de_dialogo`, AUD-244). Cada uno se
abre con un `MessageTrigger` (`dialogue="venado"`, etc.) colocado donde
aparece la silueta del espíritu. El texto es breve — un par de líneas en el
tono del lore existente — y lo revisa el dueño del proyecto; no pretende
ser definitivo.

## 6. Lo que se hereda sin cambios del primer intento

| Elemento | De dónde |
|---|---|
| La tabla `Fase`/`FASES` como fuente de verdad | `fases.py`, patrón sin cambios |
| Gradación de color interpolada por avance | `PostProcessing.set_color_grading`, AUD-463 |
| El shake único de la Fase 4 | AUD-463 |
| El ciclo de luna de la Fase 5 | AUD-463 |
| Las grietas por pisada de la Fase 6 | AUD-463 |
| Los cuatro sonidos de ambiente | AUD-465 |
| El patrón de silueta por contorno | `siluetas.py` |

Lo que cambia es el eje (columna, no fila), la forma del suelo (terreno
propio por sección) y todo lo que en el primer intento se aplazó a
`KNOWN_GAPS.md` GAP-058: cutscene, diálogo, sombra del Gavilán, movimiento
de la Serpiente, easter egg.

---

## 🔗 Documentos relacionados

- [[13_STAGE_4_1.md|Ficha 4-1]]
- [[14_BOSS_4_2.md|Jefe final 4-2]]
- [[86_ESPECIFICACION_DE_NIVELES_Y_JEFES.md|Especificación de Niveles]]
- [[65_EL_LORE_EXTENSO.md|El Lore Extenso]]
