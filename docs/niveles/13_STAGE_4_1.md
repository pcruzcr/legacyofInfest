---
document_id: "LOI-LVL-4-1"
title: "Nivel 4-1 — El Cementerio Sagrado"
aliases: ["Stage 4-1", "El Cementerio Sagrado", "La Entrada al Cementerio"]
tags: ["level", "zona-final", "atmospheric"]
description: "Ficha de nivel: dificultad, tamaño, secciones, día/noche y reglas obligatorias"
source: "docs/niveles/13_STAGE_4_1.md"
---

# NIVEL 4-1 — EL CEMENTERIO SAGRADO

**Entregable:** profesorado (no se asigna a estudiantes) · **Zona:** Final —
El Cementerio Sagrado · **Tipo:** Travesía atmosférica (sin enemigos)

> **AUD-518 (2026-08-17).** Ésta —el cementerio— es una de tres caras que
> puede tomar el slot `stage4_1`, sorteada una sola vez por partida
> (`src/stages/stage4_1/selector.py`): [[13b_STAGE_4_1B.md|4-1b, la fosa
> abisal]] (acuática) y [[13c_STAGE_4_1C.md|4-1c, lo que flota en la
> niebla]] (aérea, musical) son las otras dos. Todo lo que describe esta
> ficha —seis fases, cero enemigos, la reconstrucción de AUD-467— sigue
> siendo exclusivo de esta variante; las otras dos tienen la suya propia.

## 0. Estado real — segunda reconstrucción (AUD-467)

> **DECISIÓN DEL DUEÑO (2026-08-14, misma fecha que AUD-462, jugada de por
> medio).** El primer rediseño (AUD-462…466) mantenía el pozo vertical del
> diseño de La Cegua —repisas en zigzag heredadas— con una gradación de
> color encima. Jugado, el dueño lo rechazó explícitamente: *«no es en nada
> lo solicitado, mantuviste el 4.1 que existía y no lo hiciste desde cero...
> el nuevo nivel es horizontal completamente»* — cada repisa ocupa casi todo
> el ancho de pantalla, así que en pantalla se lee como una pila de
> plataformas horizontales genéricas, no como un descenso por un pozo
> sagrado.
>
> Esta versión **descarta esa geometría entera**. Es una reconstrucción
> desde cero: seis secciones horizontales con terreno y arte propios (un
> tileset nuevo por familia de sección, no sólo una matriz de color sobre el
> mismo suelo), la cutscene de introducción, el diálogo real de los tres
> espíritus, y las dos piezas de terror ambiental que el primer intento
> había dejado fuera (la sombra del Gavilán, el movimiento de la Serpiente
> de fondo). Lo único que se conserva del intento anterior es lo que nunca
> fue lo criticado: la tabla de datos `Fase`, la gradación de color
> interpolada, el shake único, el ciclo de luna, las grietas por pisada y
> los cuatro sonidos generados (AUD-465).

Esta ficha describe el **contrato**. La sección «Estado real — construido»
con cifras medidas se añade según cada pieza vaya aterrizando.

## 1. Qué es

`stage4_1` es la travesía que conduce a Jhon y Jill hasta el despertar de
Paburu. No es un nivel de combate: es exploración, atmósfera, memoria y
percepción. Una cutscene de introducción los guía hacia el cementerio con
voces en lengua indígena que hablan de Paburu. Dentro, los protagonistas son
guiados por los espíritus de los jefes vencidos —Venado, Rey Terciopelo
(la serpiente del canon), Gavilán— a través de un cementerio inspirado
visualmente en el cementerio de Tilarán. Cada espíritu tiene su propia
sección, su propio terreno y su propio diálogo, y asciende al final de su
tramo.

## 2. Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★☆☆☆ (2/5) — **atmosférica**: el miedo es el desafío |
| Forma | Horizontal, un único TMX, seis secciones de ~150 baldosas cada una |
| Tipos de enemigo | **0 — regla de oro: prohibido añadir** |
| Objetos mínimos | 1 `PlayerSpawn`, 2 `Cutscene` (introducción y mirador de la Fase 6, AUD-515), 6 checkpoints —uno por fase, a propósito muy por encima de los 500 px (AUD-516: el terror psicológico exige que morir cueste, no que sea gratis)—, 1 `NextTrigger` |
| Día/noche | Empieza al atardecer, termina de noche — la Fase 5 es la más oscura del nivel |
| Clima | Varía por sección; nunca tapa una superficie que cambie el movimiento |
| Concepto académico | Unidad V (color y gradación) + Unidad VII (clima y partículas) |
| Límite de tiempo | Sin límite (pacing atmosférico) |

## 3. Reglas obligatorias

1. **Sin enemigos.** Los ecos de los vencidos testifican, no atacan.
   *(AUD-562: la fauna decorativa que patrulla en el fondo —
   `presencias.PRESENCIAS`— no es una excepción: no es `EnemyBase`, no
   tiene colisión y no se puede tocar. La regla sigue siendo cero
   entidades de combate, no cero movimiento en el fondo.)*
2. **Ninguna trampa mortal.** Cero `DeathPit`, cero `HazardZone` fija sin
   representación visual.
3. **Toda superficie que cambie el movimiento se ve por qué** (musgo,
   lodo, viento).
4. **El lenguaje de color y el terreno son la barra de progreso
   narrativa.** Cada sección tiene su propia gradación, su propio clima y
   su propio suelo — no el mismo suelo con un filtro encima.
5. **Ningún peligro revelado tarde.**
6. **Lo personal se trata con dignidad.** El easter egg de la Fase 1 (§7)
   no lleva ningún dato que no haya dado el dueño del proyecto.

## 4. Las seis secciones

| Sección | Nombre | Columnas | Color | Clima | Terreno |
|---|---|---|---|---|---|
| 1 | El Cementerio de Tilarán | 0–149 | Color pleno | Calma | Cripta de piedra |
| 2 | El Venado | 150–299 | Color → B/N alto contraste | Lluvia → niebla | Bosque, musgo y lodo |
| 3 | El Rey Terciopelo | 300–449 | Escala de grises | Tormenta, rayos, viento | Camino de huesos, con una loma real |
| 4 | El Gavilán | 450–599 | Vintage naranja | Lluvia, silencio súbito | Bosque cortado y muerto |
| 5 | La Planicie de los Muertos | 600–749 | Noche, luz lunar intermitente | Calma | Tierra desnuda, tumbas de conquistadores |
| 6 | El Camino hacia Paburu | 750–899 | Color pleno + energía verde | Niebla sobrenatural | Piedra sagrada |

Detalle completo — terreno, diálogo, decoración y justificación de cada
número — en [[15_DISENO_4_1_EL_CEMENTERIO.md|Diseño 4-1]].

## 5. Checklist de cierre

- [ ] Seis secciones con terreno, clima y gradación propios (tileset
      nuevo, no sólo color)
- [ ] Cutscene de introducción con voces indígenas
- [ ] Diálogo real de Venado, Rey Terciopelo y Gavilán
- [ ] Loma real transitable en la Fase 3 (slope de verdad)
- [ ] Sombra del Gavilán cruzando el fondo en la Fase 4
- [ ] Serpiente de fondo moviéndose en la Fase 3
- [ ] Camera shake único tras el silencio de la Fase 4
- [ ] Ciclo de luna en la Fase 5
- [ ] Grietas por pisada en la Fase 6
- [ ] Easter egg de la Fase 1: lápidas de Teresa Murillo y Hugo Salazar
      Castillo, con un fantasma sobrio rondando la primera
- [ ] Cero enemigos, cero `DeathPit`, cero `HazardZone` fija
- [ ] `validate_tmx.py --ci` en verde
- [ ] Capturas reales del nivel corriendo, revisadas a ojo — no sólo
      pruebas en verde (la lección de AUD-462…466)

*(Se marcan al construirse cada pieza, no antes.)*
