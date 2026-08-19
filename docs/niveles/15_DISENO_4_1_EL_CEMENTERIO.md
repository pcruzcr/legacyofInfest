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

**La anomalía ambigua** (AUD-478, GAP-059 — punto 7 de la revisión de
diseño por fases del dueño, 2026-08-14): hacia la columna 95, lejos de las
lápidas para no confundirse con el fantasma de Teresa, una figura sin
nombre aparece menos de medio segundo y se desvanece. Sin sonido, sin
`MessageTrigger`, sin ningún efecto en el estado del nivel — el mismo
principio que ya usa la Bruja de la Fase 3 (AUD-475): si el jugador no la
vio, no pasa nada; si la vio, el juego nunca confirma qué era. Aparece en
una ventana aleatoria de 20 a 40 s dentro de la Fase 1, así que un
recorrido rápido puede no encontrarla nunca — eso es a propósito.

### 3.2 Fase 2 — El Venado (columnas 150–299)

La lluvia marca la entrada, la imagen se desatura hasta blanco y negro de
alto contraste. El suelo de bosque introduce musgo (frena al 94 %) y lodo
(frena al 88 %) — dos frenos del mismo mecanismo (`ZonaDeFriccion`,
AUD-236), el musgo más suave que el lodo. La primera versión hacía que el
musgo *arrastrara* (cinta transportadora, AUD-473: el jugador cruzaba sin
soltar el control en ningún otro punto del nivel, y en una partida real se
veía como el juego congelado) — corregido a un freno como el lodo, sólo que
más leve. `sfx_environment_viento_de_bosque` (AUD-465) como ambiente. El
Venado testifica; asciende si el jugador lo libera (AUD-474, ver §5.1).

**Las apariciones previas** (AUD-479, GAP-060 — puntos 6 y 9-12 de la
revisión de diseño por fases del dueño, 2026-08-14): antes de su diálogo
(columna `desde_columna + DESVIO_COLUMNA_DIALOGO`), el Venado no queda
encendido todo el tramo — se deja ver a destellos de 1,5 a 3 s, cada 4 a
9 s, y desaparece entre uno y otro. Pasado ese punto vuelve al fundido
continuo normal, el mismo que ya usan el Rey Terciopelo y el Gavilán:
tiene sentido dejar de ocultarlo una vez que ya habló.

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
fondo»*). El Rey Terciopelo testifica; asciende si se libera (§5.1). **Dos
de los relámpagos** traen a la Bruja un instante, «en la rama de un
árbol» — sin sonido, sin diálogo, sin ningún efecto en el nivel: una
percepción que nunca se confirma (AUD-475, punto 3 de la crítica de
diseño 2026-08-14).

**La pausa del diálogo** (AUD-480, GAP-061 — punto 19 del documento de la
Fase 3): alrededor de donde habla el Rey Terciopelo, el viento baja al 10 %
de su fuerza —no a cero, sigue siendo el mismo bosque ventoso— y vuelve en
cuanto el jugador se aleja. No es el silencio total de la Fase 4: es un
respiro más pequeño, repetible tantas veces como el jugador vaya y venga.

### 3.4 Fase 4 — El Gavilán (columnas 450–599)

Vintage naranja, bosque cortado y muerto — tocones y tierra quemada de
verdad, no color sobre cripta. A media sección, el clima calla de golpe:
partículas a cero, ambiente cortado en seco (`stop_ambient`, sin fundido —
es un silencio súbito). En ese silencio, un camera shake fuerte y breve,
una sola vez. Después: el grito aislado del Gavilán (AUD-465,
`sfx_environment_grito_de_gavilan`) **y ahora también una sombra de ave**
cruzando el cielo de vez en cuando, coordinada con el grito — la pieza que
el primer intento dejó fuera (`GAP-058`). El Gavilán testifica; asciende si
se libera (§5.1).

**El grito tiene dirección** (AUD-481, GAP-062 — puntos 4-5 y 23 del
documento de la Fase 4: *«pájaro → izquierda... ahora desde otra
dirección»*): suena con paneo estéreo real (`_play_sfx_spatial`,
`AudioManager.play_sfx_at`, que ya existía en el motor) desde un punto al
azar a la izquierda o la derecha del jugador — antes salía por el canal
ciego, sin dirección.

**Una luna nueva, y la sombra sincronizada de verdad con el grito**
(AUD-563 — pedido del dueño: *«que aparezca el Gavilán por la luna
cuando suena»*): antes «coordinada con el grito» era aspiracional —el
grito y la sombra corrían en temporizadores independientes, sin
relación real entre sí. Ahora la Fase 4 tiene una luna pálida fija en
el cielo (`_dibujar_luna_de_fase4`; el nivel ya va de atardecer a
noche cerrada, así que no desentona) y `_actualizar_grito_del_gavilan`
dispara el cruce de la sombra en el mismo instante en que suena el
grito, siempre que no haya ya un cruce en marcha. El temporizador
propio de la sombra se queda para la actividad ambiental *entre*
gritos — el guion también pide sombras «de vez en cuando», no sólo
junto al grito.

### 3.5 Fase 5 — La Planicie de los Muertos (columnas 600–749)

Nocturno azulado, la sección más oscura. Un ciclo de luna (período 6 s)
determina cuándo se ve el entorno mejor y cuándo peor — **nunca cuándo no
se ve nada** (AUD-476, puntos 9-10 de la crítica de diseño 2026-08-14: *«no
puedo ver bien» ≠ «no puedo jugar»*). El mínimo del ciclo (0,20) no baja de
la referencia que el propio proyecto ya usa para «casi negro» en un
instante dramático — la introducción de Paburu, que baja hasta 0,18 y lo
sostiene un segundo — y aquí se sostiene medio ciclo cada 6 s, no un
instante, así que va por encima, no igual. Tierra desnuda con losas de
tumba hundidas — las de los conquistadores que murieron aquí, sin dueño que
reclamar. Un coro sin palabras (`sfx_environment_canto_ancestral`, AUD-465)
como ambiente. Sin espíritu de jefe: los tres ya ascendieron.

**Las grietas adelantadas** (AUD-482, GAP-063 — puntos 29-30 del documento
de la Fase 5: *«pequeñas luces verdes que empiezan a sustituir a la luna
como guía»*): las tres primeras grietas de `GRIETAS_FASE6` (columnas 700,
720 y 740) caen ya en el tramo final de esta sección — el mismo mecanismo
de encendido por proximidad de la Fase 6, sin ningún código nuevo, sólo
adelantando dónde empieza el rango.

### 3.6 Fase 6 — El Camino hacia Paburu (columnas 750–899)

Color pleno, sin gradación — **y ahora tampoco sin tinte** (AUD-483,
GAP-065 §11): un verde sutil (`TINTE_DESPERTAR`, alfa 0,10) se intensifica
con el avance, el mismo mecanismo que ya usa el tinte vintage de la Fase 4,
para que «verde = algo está despertando» tenga una señal visual y no sólo
la de las grietas. Niebla sobrenatural (partículas `spores` verdes).
Grietas que se iluminan al paso, sin quedar encendidas — un rastro, no un
progreso acumulado (mecánica sin cambios del prototipo), que ahora empieza
a asomar unas columnas antes de que arranque la sección (ver nota de la
Fase 5). `sfx_environment_resonancia_solemne` (AUD-465) como ambiente. Al
final, `NextTrigger` hacia `stage4_2_boss_paburu`.

**La viñeta respira (AUD-566, propuesta "nivel cine" aprobada por el
dueño):** cada una de las seis fases pide su propia intensidad de viñeta
(`Stage4_1.VIGNETTE_POR_FASE`), interpolada por avance con el mismo
mecanismo que ya usa la gradación de color. Más cerrada en la tormenta
(Fase 3) y la noche (Fase 5) — las dos de mayor amenaza sensorial—, casi
abierta en la Fase 1 (estableciendo el espacio real) y en ésta, la Fase
6 (la llegada, ya sin terror). `PostProcessing.set_vignette` existía en
el motor desde siempre —base fija de 0,4— pero ningún escenario lo
tocaba por fase hasta ahora.

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

**El acorde de liberación** (AUD-568, propuesta "nivel cine" aprobada
por el dueño): en el mismo instante en que `_espiritu_liberado` pasa a
`True`, junto a la línea de voz de siempre (AUD-551), suena
`sfx_environment_liberacion_espiritu` — un acorde propio, generado con
la misma tríada de Re menor que ya ancla "algo despierta" en las
grietas de la Fase 6 (`paso_de_luz_*`), pero una octava más grave y con
una envolvente mucho más lenta (250ms de ataque, no 15) para que se
sienta como un alivio sostenido y no como una campanilla. La única
consecuencia narrativa medible de todo el recorrido (ver más abajo)
tenía, hasta ahora, el mismo tratamiento sonoro que cualquier otro
evento ambiental del nivel.

## 5.1 Liberar a los espíritus (AUD-474)

La crítica de diseño que revisó el dueño del proyecto (2026-08-14, puntos
15-16) señaló el defecto central de la primera pasada: la ascensión de
Venado, Rey Terciopelo y Gavilán se calculaba sólo con cuánto del tramo
llevaba andado el jugador — cruzar corriendo sin detenerse liberaba al
espíritu exactamente igual que pararse a escucharlo. El jugador nunca
*hacía* nada; sólo observaba.

Unos pasos después del `MessageTrigger` del diálogo, cada fase con
espíritu deja un `EventTrigger` con `automatico=False`: exige el botón de
usar, no basta con caminar cerca. Sin esa acción, el espíritu se queda a
la vista hasta el borde de la sección — no asciende nadie a quien nadie
liberó. El umbral final ("Paburu despierta.") cuenta cuántos de los tres
se liberaron de verdad y varía su texto en consecuencia — la única
consecuencia narrativa medible de la interacción. Ninguno de los dos
estados bloquea el avance: sigue sin haber ningún fallo posible, como pide
la regla de oro del nivel.

**El resplandor antes del diálogo** (AUD-567, propuesta "nivel cine"
aprobada por el dueño): en las tres fases con espíritu, un resplandor
suave crece justo antes del punto donde habla —`_intensidad_resplandor_
dialogo`, la misma ventana de avance que ya usa `AVANCE_ANTES_DEL_
DIALOGO`— y se apaga más rápido una vez que ya habló. Separa
visualmente «está de fondo» de «está hablándome ahora», sin tocar la
lógica de aparición ni de liberación que ya existía.

**El plano de cámara por espíritu** (AUD-569, propuesta "nivel cine"
aprobada por el dueño): en la misma ventana en que crece el
resplandor, la cámara sube un barrido pequeño (20px en el pico) hacia
donde flota el espíritu — un desplazamiento aditivo y temporal, mismo
patrón que ya usa `Camera._aplicar_sacudida` con el temblor, para que
no se acumule ni deje la cámara torcida al alejarse. El espíritu ya
vive cerca del centro de la pantalla, así que no hace falta un giro
grande para enmarcarlo — sólo levantar la mirada.

**El horizonte medio, BG_Mid** (AUD-570, propuesta "nivel cine"
aprobada por el dueño): `BG_Mid` seguía enteramente vacía en las seis
fases (GAP-058/059/065 ya lo señalaban). En vez de un sistema nuevo,
`_dibujar_horizonte_medio` reusa el mismo generador de cresta que ya
pinta `BG_Far` (`siluetas.dibujar_horizonte`), a una segunda
profundidad: más cerca del suelo, más quebrada, más opaca, con una
fase de onda distinta para que no coincida pico con pico con la
lejana, y con el factor de paralaje real que ya declara `Camera.
_parallax_factors["BG_Mid"]` (0,40) — no un número inventado para esta
pieza sola.

## 6. Lo que se hereda sin cambios del primer intento

| Elemento | De dónde |
|---|---|
| La tabla `Fase`/`FASES` como fuente de verdad | `fases.py`, patrón sin cambios |
| Gradación de color interpolada por avance | `PostProcessing.set_color_grading`, AUD-463 |
| El shake único de la Fase 4 | AUD-463 |
| El ciclo de luna de la Fase 5 | AUD-463 |
| Las grietas por pisada de la Fase 6 | AUD-463 |
| Los cuatro sonidos de ambiente | AUD-465 |
| El patrón de silueta por contorno, para la decoración de fase (árboles, cruces, la Cegua, la Bruja) | `siluetas.py` |

Lo que cambia es el eje (columna, no fila), la forma del suelo (terreno
propio por sección) y todo lo que en el primer intento se aplazó a
`KNOWN_GAPS.md` GAP-058: cutscene, diálogo, sombra del Gavilán, movimiento
de la Serpiente, easter egg.

> **AUD-561 — los tres espíritus dejan el contorno por su arte real.**
> Jugado, las siluetas de polígono del Venado, el Rey Terciopelo y el
> Gavilán «se veían raras»: no se leían como lo que eran. A diferencia de
> la decoración de fase (§ arriba), el proyecto sí tiene arte real de los
> tres —fueron jefes de una zona anterior—, así que `_dibujar_espiritu`
> ahora recorta el primer fotograma de `boss_venado_drift.png` /
> `boss_rey_walk.png` / `boss_gavilan_glide.png` y lo aplana a una
> silueta plana del mismo verde espectral de siempre (no a todo color:
> sigue siendo un recuerdo, no el jefe en persona). El contorno de
> polígono se queda como red de seguridad si el sprite faltara.

> **AUD-562 — presencias errantes: más fantasmas, y fauna sin daño para
> el estrés.** Jugado el nivel completo, dos pedidos más del dueño:
> *«más fantasmas o figuras que se muevan como fantasma en el fondo»* y
> *«sería bueno agregar enemigos que no hagan daño... para llenar algo
> de estrés»*. La segunda petición choca de frente con la regla de oro
> del nivel (regla 1, `13_STAGE_4_1.md`) — la resolución que aprobó el
> dueño: fauna decorativa sin `EnemyBase`, misma arquitectura que ya usa
> la sombra del Gavilán o la serpiente de fondo de la Fase 3. Tres
> presencias nuevas (`presencias.py`), una por fase de las que no tenían
> ninguna: un infestado errante en la Fase 2 (el sprite real de
> `WalkerEstudiante`, no un monstruo inventado — encaja con el lore de
> la infestación, y refuerza literalmente *«la sensación de que algo
> observa o sigue al jugador»* que ya pedía el guion de esa fase), un
> fantasma menor en el camino de huesos de la Fase 3, y otro
> conquistador errante en la Planicie de los Muertos de la Fase 5 —
> dándole cuerpo a la línea del propio diseño que ya menciona a los
> conquistadores sin mostrarlos. Cada una patrulla un tramo corto y
> aparece/desaparece en ventanas aleatorias, igual que la anomalía de la
> Fase 1: nunca se confirma qué es.

---

## 🔗 Documentos relacionados

- [[13_STAGE_4_1.md|Ficha 4-1]]
- [[14_BOSS_4_2.md|Jefe final 4-2]]
- [[86_ESPECIFICACION_DE_NIVELES_Y_JEFES.md|Especificación de Niveles]]
- [[65_EL_LORE_EXTENSO.md|El Lore Extenso]]
