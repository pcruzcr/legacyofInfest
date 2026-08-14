---
document_id: "LOI-LVL-4-1"
title: "Nivel 4-1 — El Cementerio Sagrado"
aliases: ["Stage 4-1", "El Cementerio Sagrado", "La Entrada al Cementerio"]
tags: ["level", "zona-final", "atmospheric"]
description: "Ficha de nivel: dificultad, tamaño, fases, día/noche y reglas obligatorias"
source: "docs/niveles/13_STAGE_4_1.md"
---

# NIVEL 4-1 — EL CEMENTERIO SAGRADO

**Entregable:** profesorado (no se asigna a estudiantes) · **Zona:** Final —
El Cementerio Sagrado · **Tipo:** Travesía atmosférica (sin enemigos)

## 0. Estado real — reemplazo deliberado en construcción (AUD-462)

> **DECISIÓN DEL DUEÑO (2026-08-14).** El 4-1 existía ya como «La Entrada al
> Cementerio»: un pozo de cinco actos con La Cegua, doce braseros y 84
> pruebas (`git log` conserva ese diseño completo si hace falta consultarlo).
> Se sustituye deliberadamente por el guion de abajo — seis fases que llevan
> a Jhon y Jin hasta el despertar de Paburu — porque el dueño del proyecto lo
> pidió así tras ver el análisis de viabilidad técnica. No es una revisión
> menor: cambia la estructura de fases, el lenguaje visual (gradación de
> color por fase) y el motivo central (los espíritus de los jefes vencidos
> ascienden, en vez de La Cegua como presencia).
>
> Lo que **no** cambia, porque ya estaba resuelto y sigue siendo correcto:
> la forma de **pozo vertical** (repisas en zigzag, cero `DeathPit`, cero
> `HazardZone` fija, cero daño por caída) que dejó AUD-225 tras comprobar que
> la versión horizontal de este mismo nivel no funcionaba jugada. El guion
> nuevo no exige un pasillo horizontal, así que se hereda la forma que ya se
> demostró que funciona en este nivel concreto.

Esta ficha describe el **contrato** del nivel nuevo: lo que tiene que ser
verdad cuando esté construido. La sección «Estado real — construido» con
cifras medidas se añade aquí, igual que en cualquier otro nivel del
proyecto, según cada pieza vaya aterrizando (ver `docs/15_DISENO...` para el
plan de construcción por lotes).

## 1. Qué es

`stage4_1` es la travesía que conduce a Jhon y Jin hasta el despertar de
Paburu. No es un nivel de combate: es exploración, atmósfera, memoria y
percepción. Los protagonistas son guiados por los espíritus de los jefes
vencidos —Venado, Rey Terciopelo, Gavilán— a través de un cementerio
inspirado visualmente en el cementerio de Tilarán. La premisa: esos
espíritus necesitan ascender, y su liberación es lo que permite que Paburu
despierte.

`Rey Terciopelo` **es** la serpiente del canon (el terciopelo,
*Bothrops asper*, ya forma parte del bestiario del juego —
`siluetas.py._serpiente()` lo dibuja como *"la masa enroscada del Rey
Terciopelo"* desde antes de este rediseño). No hace falta inventar un cuarto
espíritu: los tres ecos de este nivel son los tres jefes reales de las zonas
1 a 3 (`boss_venado`, `boss_rey`, `boss_gavilan`).

## 2. Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★☆☆☆ (2/5) — **atmosférica**: el miedo es el desafío |
| Forma | Pozo vertical, seis tramos de profundidad (heredado de AUD-225) |
| Tipos de enemigo | **0 — regla de oro: prohibido añadir** |
| Objetos mínimos | 1 `PlayerSpawn`, checkpoints repartidos (≤480 px entre dos), 1 `NextTrigger` de salida |
| Día/noche | Empieza al atardecer, termina de noche — la Fase 5 es la más oscura del nivel |
| Clima | Varía por fase: niebla, tormenta, calma — nunca tapa una superficie que cambie el movimiento |
| Concepto académico | Unidad V (color y gradación) + Unidad VII (clima y partículas) + Unidad VIII (visión de umbral, heredada del diseño anterior si se conserva) |
| Límite de tiempo | Sin límite (pacing atmosférico) |

## 3. Reglas obligatorias

1. **Sin enemigos.** Si el nivel aburre, se arregla con más atmósfera, no con
   combate. Es la misma regla de oro del diseño anterior y sigue vigente:
   *«los ecos de los vencidos no atacan, testifican»*.
2. **Ninguna trampa mortal.** Cero `DeathPit`, cero `HazardZone` fija sin
   representación visual. El motor no tiene daño por caída — se aprovecha
   igual que en el diseño anterior: caer es movimiento, no castigo.
3. **Toda superficie que cambie el movimiento del jugador se ve por qué**
   (musgo que arrastra, lodo que frena, viento que empuja): la regla que
   dejó AUD-236 y que este rediseño hereda sin modificar.
4. **El lenguaje de color es la barra de progreso narrativa.** Cada fase
   tiene su propia gradación (`PostProcessing.set_color_grading`) y clima; la
   transición entre fases se interpola, nunca se corta en seco.
5. **Ningún peligro revelado tarde.** Si una fase introduce un tramo
   exigente (slopes, superficies que frenan), el jugador tiene que poder
   verlo antes de necesitarlo — el mismo principio que ya aplicaba el
   relámpago del diseño anterior.

## 4. Las seis fases

| Fase | Nombre | Color | Clima | Motivo |
|---|---|---|---|---|
| 1 | El Cementerio de Tilarán | Color pleno | Calma | Establece el espacio real antes de lo sobrenatural |
| 2 | El Venado | Color → blanco y negro | Lluvia → niebla | Musgo que arrastra; el Venado asciende |
| 3 | El Rey Terciopelo | Escala de grises | Tormenta, rayos, viento | Slopes, tramo de subida corta; el Rey asciende |
| 4 | El Gavilán | Vintage naranja | Lluvia, silencio súbito | Camera shake puntual; el Gavilán asciende |
| 5 | La Planicie de los Muertos | Noche, luz lunar intermitente | Calma, viento del bosque | Visibilidad ligada al ciclo de la luna |
| 6 | El Camino hacia Paburu | Color pleno + energía verde | Niebla sobrenatural | Luces por pisada; llegada solemne |

Detalle completo de cada fase, valores de gradación de color, geometría y
justificación de cada decisión: [[15_DISENO_4_1_EL_CEMENTERIO.md|Diseño 4-1 —
El Cementerio Sagrado]].

## 5. Lo que se hereda del diseño anterior sin cambios

- La forma de pozo y su geometría de repisas en zigzag (`trazado.py`).
- La regla de «superficie visible» para musgo/lodo/viento.
- Cero daño por caída, cero `DeathPit`.
- El verde espectral (`124, 255, 160`) como color de la energía sobrenatural
  del cementerio — se reusa para la niebla y las grietas de la Fase 6.

## 6. Checklist de cierre

- [ ] Seis fases con su gradación de color, clima y geometría propios
- [ ] Venado, Rey Terciopelo y Gavilán como siluetas de fondo — reusan
      `siluetas.py`, sin arte nuevo
- [ ] Slopes transitables en la Fase 3, con margen medido de salto
- [ ] Camera shake puntual y único en la Fase 4, tras el silencio
- [ ] Luz lunar intermitente en la Fase 5 controlando la visibilidad
- [ ] Niebla sobrenatural + grietas verdes por pisada en la Fase 6
- [ ] Cero enemigos, cero `DeathPit`, cero `HazardZone` fija — comprobado
      cargando el mapa, no leyendo el XML
- [ ] `validate_tmx.py --ci` en verde
- [ ] Checkpoints con tramo máximo medido (mismo criterio de 480 px)

*(Se marcan al construirse cada pieza, no antes — regla de la invariante 6:
un número o una casilla sin evidencia ejecutada no se escribe.)*
