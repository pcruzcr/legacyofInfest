---
document_id: "LOI-LVL-4-1"
title: "Nivel 4-1 — La Entrada al Cementerio"
aliases: ["Stage 4-1", "La Entrada al Cementerio"]
tags: ["level", "zona-final", "atmospheric"]
description: "Ficha de nivel: dificultad, tamaño, enemigos, objetos, día/noche y mapa sugerido"
source: "docs/niveles/13_STAGE_4_1.md"
---

# NIVEL 4-1 — LA ENTRADA AL CEMENTERIO

**Entregable:** profesorado (no se asigna a estudiantes) · **Zona:** Final — El Cementerio Sagrado · **Tipo:** Travesía atmosférica (sin enemigos)

## 0. Estado real — construido (AUD-163)

El nivel **existe y se juega**. Esta sección dice qué se construyó de verdad,
qué se cambió respecto a la ficha y por qué, para que nadie tenga que
adivinarlo leyendo el código.

| Pieza | Dónde vive |
|---|---|
| Mapa (100 × 38, generado) | `tools/generate_stage4_1.py` → `assets/maps/stage4_1/stage4_1.tmx` |
| Escena, actos, luna, rayos | `src/stages/stage4_1/stage4_1.py` |
| Tabla de los cinco actos | `src/stages/stage4_1/actos.py` |
| Contornos de venado, serpiente, gavilán y la Cegua | `src/stages/stage4_1/siluetas.py` |
| Pruebas (36) | `tests/test_stage4_1.py` |

**Lo que se cambió respecto a esta ficha, y por qué:**

1. **`Portal` no existe en el motor.** La ficha lo pide en «Objetos mínimos».
   La salida de un escenario es `NextTrigger`, que es lo que hay en el mapa.
   Es la misma cosa con otro nombre; lo que no se puede es escribir un tipo
   que el cargador rechaza. (La auditoría de documentación ya lo tenía
   señalado como inexistente.)
2. **`start_hour` va como número (19), no como la cadena `dusk`.** El motor
   lee la hora como `float`; `dusk` no es un valor que entienda.
3. **Las siluetas no están en la capa `BG_Mid` del TMX** sino dibujadas por el
   escenario, detrás del mapa, con el gancho `dibujar_fondo` que AUD-162 tuvo
   que añadir a `StageScene`. La capa `BG_Mid` de un TMX es de baldosas, y no
   hay arte de venado ni de gavilán en vista de fondo: un contorno dibujado es
   honesto —se lee como «una forma en la niebla», que es lo que el diseño
   pide— y no finge ser una ilustración terminada.
4. **Partículas verdes: `spores`.** Es el único efecto del motor que sale en
   verde —(150, 255, 130)— y es exactamente la «luz espectral verde» que el
   lore le pone al cementerio (§3.4). El ritmo sube con los actos.
5. **El acto V no tiene «silencio súbito» de audio**, sólo `climate = clear` y
   menos partículas. Silenciar la música por acto exigiría tocar el gestor de
   audio y no se hizo.
6. **Los nombres de las lápidas son `[NOMBRE]`.** El diseño (§7) exige que los
   cargue el profesor, que estén todos sin distinción de nota y que ninguna
   inscripción se burle de nadie. Inventar una lista sería lo contrario.

**Medido, no supuesto:**

- Dibujar el nivel cuesta **4,6 ms** por fotograma; con la visión espectral
  puesta, **6,6 ms** de los 16,6 que hay a 60 fps. El umbral se aplica a 1/4 de
  resolución justamente por esto: a 1/2 costaba 4,6 ms de más y se salía del
  presupuesto.
- En la curva de dificultad sale con **36,8**, entre `stage3_3_el_patio` (36,4)
  y `boss_paburu` (13,4). No introduce ningún escalón brusco. Todo su índice
  viene de peligros —6 por pantalla— y **cero** de combate, que es exactamente
  lo que un nivel sin enemigos debe puntuar.

## Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★☆☆☆ (2/5) — **atmosférica**: el miedo es el desafío |
| Tamaño mínimo | **1600 × 608 px** (100 × 38 tiles) |
| Tamaño de referencia | ~400 px de recorrido en el diseño canónico |
| Tipos de enemigo | **0 — regla de oro: prohibido añadir** |
| Enemigos mínimos | 0 |
| Objetos mínimos | 1 `PlayerSpawn`, 1 `Checkpoint`, 1 `Portal`, 1 `HazardZone`, 1 visión especial |
| Día/noche | `dusk` 19:00 → 23:00, `day_length` 900 s *(sugerido)* |
| Clima | Libre (sugerencia: niebla baja que nunca tapa los peligros del suelo) |
| Concepto académico | Unidad V (tinte espectral) + Unidad VIII (visión de umbral) |
| Límite de tiempo | Sin límite (pacing atmosférico) |

## Reglas obligatorias

1. **Sin enemigos.** Si el nivel aburre, se arregla con más marcas ocultas, no
   con serpientes. La tensión ya está: es el silencio antes del juez.
2. **Visión espectral obligatoria** (Unidad VIII): con el botón de ataque largo
   se filtra la pantalla en umbral y se revelan marcas ocultas en las losas
   (3 s). Es la mecánica protagonista.
3. **Los cuencos de fuego son plataformas y luz**: cerca = más brillo; lejos =
   oscuridad. El brillo por proximidad es la mecánica de la Unidad V.
4. **Las grietas pulsantes** (HazardZone 0.25 periódico) son los únicos peligros
   y deben leerse con anticipación (pulso visible).
5. **Los ecos de los espíritus vencidos** (venado, Rey, Gavilán) aparecen como
   siluetas en BG_Mid: storytelling ambiental, no entidades.

## Día/noche (sugerido)

- `start_hour`: `dusk` (19:00) — el cementerio se ve por última vez de día agonizante.
- `day_length`: 900 s → termina a las **23:00** (noche) — prepara el clímax.
- *(Sugerido por la guía; el canon no lo fija: si el profesor decide otra hora,
  debe mantener la regla del reloj continuo con el 4-2.)*

## Enemigos

Ninguno. El único "contenido" son:

| Elemento | Cantidad | Nota |
|---|---|---|
| Cuencos de fuego | 3+ | Plataformas OneWay + luz por proximidad |
| Grietas pulsantes | 2+ | HazardZone 0.25 periódico |
| Marcas ocultas | 5+ | Solo visibles con la visión espectral |
| Ecos de espíritus | 3 | Siluetas BG_Mid (venado, Rey, Gavilán) |
| Coleccionables | 0 (o 3 discretos) | Mejor sin coleccionables: el silencio es el premio |

## Mapa sugerido

```
 19:00 ── OCASO → NOCHE ─────► 23:00
 SPAWN ─[fuego]──[fuego]──[grieta]──[fuego]──[grieta]──[fuego]── PORTAL
   │  ecos en BG_Mid: venado · serpiente · halcón
   │  las losas ocultan marcas: visión espectral (ataque largo)
   └── sin enemigos: la atmósfera ES el desafío
```

## Checklist de cierre

- [x] Sin enemigos (regla de oro) — comprobado contando `entity_list`, no el XML
- [x] Visión espectral funcionando con marcas ocultas — comprobada píxel a píxel
- [x] Cuencos con luz por proximidad; grietas pulsantes legibles
- [x] `start_hour = 19` y `day_length = 900` — como número, ver §0
- [x] `validate_tmx.py --ci` en verde (17/17)

## Diseño propuesto

Una propuesta completa de cómo llenar este nivel — progresión ambiental estilo
Magus (Chrono Trigger), luna descendente, 12 braseros en secuencia, tormenta
con relámpagos que revelan peligros, La Cegua como presencia (nunca enemigo),
lápidas con los nombres de los estudiantes y tramos de salto — está en:

- [[15_DISENO_4_1_EL_CEMENTERIO.md|Diseño 4-1 — El Cementerio y La Cegua]]

*(Cumple todas las reglas obligatorias de esta ficha; no modifica ninguna.)*
