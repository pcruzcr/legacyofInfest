---
document_id: "LOI-LVL-4-1D"
title: "Diseño 4-1 — El Cementerio Sagrado"
aliases: ["Diseño del Cementerio Sagrado", "4-1 Design", "El Despertar de Paburu"]
tags: ["level", "zona-final", "design", "folklore", "paburu"]
description: "Diseño del 4-1: seis fases con lenguaje de color propio, los tres espíritus ascendiendo, y el despertar de Paburu"
source: "docs/niveles/15_DISENO_4_1_EL_CEMENTERIO.md"
---

# DISEÑO 4-1 — EL CEMENTERIO SAGRADO

**Nivel:** 4-1 · **Tipo:** Travesía atmosférica (sin enemigos) · **Reemplaza**
al diseño anterior de La Cegua (ver §0 de `13_STAGE_4_1.md`, AUD-462)

> **La idea en una frase.** Jhon y Jin descienden por un cementerio que va
> cambiando de piel —de color pleno a blanco y negro, a grises, a un tono
> vintage, a la noche, y de vuelta al color— mientras los espíritus de los
> tres jefes vencidos (Venado, Rey Terciopelo, Gavilán) ascienden uno a uno.
> Cuando los tres se han ido, el camino se abre hacia Paburu.
>
> Este documento fija los números: la gradación de color de cada fase (una
> matriz real, no una descripción), el clima, la geometría y qué sistema del
> motor resuelve cada pieza. Todo lo de aquí usa sistemas que **ya existen**
> — `PostProcessing.set_color_grading()`, `WeatherSystem`, `lighting.py`,
> `pendientes.py` (slopes), `camera.py` (shake) — y hereda del diseño
> anterior la forma de pozo y la regla de superficies visibles (§0 de la
> ficha).

---

## 1. Por qué un pozo y no un pasillo

El diseño anterior de este mismo nivel era horizontal y falló jugado (siete
`DeathPit`, cinco `HazardZone` invisibles, 37 repechos imposibles según el
calificador — AUD-225). Se rehízo como un descenso de repisas en zigzag y
funcionó: caer es gratis, subir cuesta un salto puesto donde toca, y nadie
queda encerrado porque las repisas consecutivas siempre se solapan. Ese
problema —cómo generar tensión sin combate ni muerte— es exactamente el que
plantea este guion nuevo, así que se hereda la solución en vez de
reinventarla.

**Geometría base:** pozo de 60 × 288 baldosas (960 × 4608 px), seis tramos de
48 filas cada uno (`ALTO_FASE = 48`, la misma partición que ya usaba el
diseño anterior, con un tramo más). Repisas cada 5 filas (80 px), alternando
lado — el salto del jugador llega a 90,25 px medidos
(`level_metrics.JumpEnvelope`), así que siempre se puede volver a subir uno.

## 2. Las seis fases

Cada fase fija tres cosas a la vez: **gradación de color** (una matriz 3×3,
la de verdad que aplica `PostProcessing.apply()`), **clima** (`WeatherSystem`)
y **geometría** (qué tramo del pozo es). La transición entre fases se
interpola a lo largo del propio tramo —igual que el diseño anterior
interpolaba la luna— para que el cambio se vea progresivo, no cortado.

| Fase | Filas | Nombre | Gradación | Clima | Partículas |
|---|---|---|---|---|---|
| 1 | 0–47 | El Cementerio de Tilarán | Color pleno (sin gradación) | `clear` | `ash`, ligera |
| 2 | 48–95 | El Venado | → B/N de alto contraste | `rain` → `fog` | `ash` |
| 3 | 96–143 | El Rey Terciopelo | → Grises neutros | `storm` | `spores` |
| 4 | 144–191 | El Gavilán | → Sepia/vintage naranja | `rain`, luego calma | `ash` |
| 5 | 192–239 | La Planicie de los Muertos | → Nocturno azulado | `clear`, viento de fondo | ninguna (oscuridad) |
| 6 | 240–287 | El Camino hacia Paburu | → Color pleno + verde | `fog` sobrenatural | `spores`, alta |

### Las matrices de gradación

`PostProcessing.set_color_grading(r,g,b, rr,gg,bb, rrr,ggg,bbb)` es una
matriz 3×3 real: cada canal de salida es una combinación lineal de los tres
de entrada, dividida entre 255. No es un tinte por encima — es la misma
operación que un grading de cine.

| Fase | Matriz (r,g,b / rr,gg,bb / rrr,ggg,bbb) | Qué hace |
|---|---|---|
| 1, 6 | `None` (sin gradación) | Color de la imagen sin tocar |
| 2 | `(87,172,33, 87,172,33, 87,172,33)` | Luminancia estándar (76,150,29 = ITU-R BT.601) con +15 % de ganancia: blanco y negro marcado, no un gris suave |
| 3 | `(76,150,29, 76,150,29, 76,150,29)` | La misma luminancia sin ganancia: un gris plano y uniforme — se lee como escenario, no como fotografía de época |
| 4 | `(100,196,48, 89,175,43, 69,136,33)` | Matriz sepia clásica (0.393/0.769/0.189 …, escalada a 255) — el tono vintage se completa con `set_tint` (naranja, alfa bajo) por encima, sin mezclarlo en la matriz |
| 5 | `(71,140,26, 56,110,26, 51,89,140)` | «Day-for-night»: los canales rojo y verde de salida son luminancia atenuada, el azul de salida conserva más entrada — el clásico truco de cine para simular noche sin oscurecer del todo |

La Fase 4 combina la matriz sepia con `set_tint((200, 120, 60), 0.12)`: la
matriz hace el trabajo tonal (desaturar hacia sepia) y el tinte hace el
trabajo de color (empujar hacia naranja) — son dos sistemas ya separados en
`PostProcessing` y no hace falta fundirlos en una sola matriz para lograr el
efecto.

## 3. Fase 1 — El Cementerio de Tilarán

Color pleno, clima en calma. El objetivo es que el jugador reconozca el
espacio como un cementerio real antes de que empiece lo sobrenatural — la
misma función que cumplía «La Entrada» en el diseño anterior. Ligera ceniza
cayendo (`ash`), sin siluetas de espíritu todavía.

## 4. Fase 2 — El Venado

La lluvia marca la entrada (`climate = "rain"` al principio del tramo,
`"fog"` hacia el final) y la imagen se desatura progresivamente hasta el B/N
de alto contraste. El terreno introduce **musgo** (`FrictionZone`, arrastre
hacia el hueco de la repisa — la misma superficie y el mismo valor medido que
el diseño anterior, 62 px/s) y la silueta del Venado aparece en `BG_Mid`
(reusa `siluetas._venado`, sin arte nuevo). Al llegar al final del tramo, la
silueta se desvanece hacia arriba: el Venado asciende.

## 5. Fase 3 — El Rey Terciopelo

Escala de grises neutra, tormenta con rayos y viento (`climate = "storm"`,
`rayos_por_minuto` alto, el mismo relámpago-linterna del diseño anterior que
revela el tramo siguiente antes de tener que jugarlo). Aquí el pozo
incorpora **slopes** (`pendientes.py`) en un tramo corto de subida —la
petición del guion de «ascender por lomas»— resuelto como una loma dentro
del descenso general, no como una inversión del eje: el jugador sube una
pendiente corta entre dos repisas y vuelve a bajar, igual que ya se puede
volver a subir una repisa suelta en el diseño heredado. La silueta enroscada
del Rey Terciopelo (`siluetas._serpiente`) aparece entre las lápidas de
piedra. Al ascender, dos pruebas lo comprueban: que el slope es transitable
sin salto imposible y que la silueta se desvanece al cruzar el umbral del
tramo.

## 6. Fase 4 — El Gavilán

Vintage naranja, bosque cortado y muerto (árboles secos en `BG_Far`), lluvia
suave. A media fase, el clima **calla de golpe**: partículas a cero,
`WeatherSystem.set_climate("clear")` sin transición, silencio de audio
ambiental. En ese silencio ocurre un **camera shake fuerte y breve, una sola
vez** (`camera.py`, con dirección — el mismo sistema que ya prueba
`test_la_sacudida_tiene_direccion.py`), sin causa visible: es la sensación de
que algo acaba de pasar sin que el jugador lo haya visto. Después, el sonido
del Gavilán vuelve de forma aislada y aleatoria, con sombras cruzando el
fondo (reusa el patrón de `_dibujar_brujas`, adaptado a un solo cruce de
ave). El Gavilán asciende al final del tramo.

## 7. Fase 5 — La Planicie de los Muertos

Nocturno azulado, la fase más oscura del nivel. La luz **no es constante**:
un ciclo de luna (`lighting.py`, intensidad ambiente oscilando entre un
mínimo casi nulo y un máximo que revela el entorno, período de varios
segundos) determina cuándo se ve el tramo y cuándo no. Con la luna oculta, la
escena es casi invisible — igual que exige el guion. Voces y cánticos
indígenas se mezclan con el ambiente del bosque (bus de audio `ambiente`,
volumen bajo). No hay siluetas de espíritu aquí: los tres ya ascendieron: lo
que queda son las tumbas de los conquistadores, sin dueño que reclamar.

## 8. Fase 6 — El Camino hacia Paburu

Color pleno, sin gradación — la imagen «real» vuelve. Niebla sobrenatural
(`climate = "fog"`, pero con partículas `spores` a ritmo alto en vez de la
niebla gris habitual: la niebla de este tramo es verde-espectral, no
climática). Grietas verdes que se revelan **por pisada** — cada repisa que el
jugador cruza enciende una luz ambiental corta (`lighting.py`, punto que se
apaga tras el paso, distinto de los braseros del diseño anterior porque
**no** queda encendida: es un rastro, no un progreso acumulado) y descubre
tiles con grietas verdes ya presentes en el tileset. Sin sobresaltos: la
atmósfera es solemne, no de terror. Al fondo del pozo, el `NextTrigger` que
lleva a `stage4_2_boss_paburu`.

## 9. Lo que se hereda sin cambios del diseño anterior

| Elemento | De dónde |
|---|---|
| Pozo vertical, repisas en zigzag cada 5 filas | `trazado.py` (AUD-225) |
| Cero `DeathPit`, cero `HazardZone` fija | Regla de oro heredada |
| Cero daño por caída | El motor no lo tiene — se sigue aprovechando |
| Musgo (arrastre) / lodo (freno) como `FrictionZone` visibles | AUD-236 |
| Verde espectral `(124, 255, 160)` para energía sobrenatural | `siluetas.VERDE_ESPECTRAL` |
| Checkpoints con tramo máximo medido (≤480 px) | Criterio del calificador ya cumplido antes |

## 10. Lo que queda fuera de esta pasada (a `KNOWN_GAPS.md`)

- **Arte final.** Todo lo de esta versión se construye primero con assets de
  prueba (tileset y fondos placeholder generados por código) para validar
  ritmo y lectura visual antes de encargar arte de verdad.
- **Diálogo de los tres espíritus.** El guion pide líneas para Venado, Rey
  Terciopelo y Gavilán; el sistema de diálogo (`40_DIALOGUE_SYSTEM.md`) ya
  existe, pero el texto en sí no se escribe en esta pasada técnica.
- **Reverberación de audio real.** El mezclador SDL no tiene DSP por zona
  (límite ya documentado en `90_INVENTARIO_DE_LEVEL_DESIGN.md` §1.1); el
  «silencio súbito» de la Fase 4 se resuelve bajando el bus de `ambiente` a
  cero, no con una reverberación que se apaga.

---

## 🔗 Documentos relacionados

- [[13_STAGE_4_1.md|Ficha 4-1]] — las reglas obligatorias que este diseño cumple
- [[14_BOSS_4_2.md|Jefe final 4-2]] — la puerta al otro lado del descenso
- [[86_ESPECIFICACION_DE_NIVELES_Y_JEFES.md|Especificación de Niveles]] — reglas globales
- [[65_EL_LORE_EXTENSO.md|El Lore Extenso]] — el cementerio y Paburu en el canon
