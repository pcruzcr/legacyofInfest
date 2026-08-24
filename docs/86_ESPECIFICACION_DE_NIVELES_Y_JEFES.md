---
document_id: "LOI-LEVELRULES-067"
title: "Legacy of InFest — Especificación de Niveles y Jefes"
aliases: ["Especificación de Niveles", "Reglas de Niveles", "Level Rules"]
tags: ["rules", "level-design", "deliverables", "evaluation", "day-night"]
description: "Reglas obligatorias de tamaño, enemigos, objetos, día/noche y dificultad para cada nivel y jefe, por entregable"
source: "docs/86_ESPECIFICACION_DE_NIVELES_Y_JEFES.md"
date_processed: "2026-08-01"
---

# Legacy of InFest — Especificación de Niveles y Jefes

**ID del documento:** LOI-LEVELRULES-067
**Versión:** 1.0.0
**Estado:** Oficial
**Compatibilidad:** Requiere `66_GUIA_DE_LEVEL_DESIGN.md`, `16_WORLD_DESIGN.md`, `17_BOSS_SPEC.md`, `06_TMX_SPEC.md`, `30_ASSIGNMENT_01_STAGE_DESIGN.md`, `31_ASSIGNMENT_02_BOSS_DESIGN.md`
**Público:** estudiantes, profesorado

> **AUD-455 (2026-08-13).** Cuatro correcciones verificadas contra el código
> real: §2.2 y §2.3 inventaban objetos `EnemySpawn` y una capa `Collectibles`
> que no existen — los enemigos se colocan con su `type` real en `Objects` y
> los coleccionables son objetos `Pickup`, también en `Objects` (ver
> `06_TMX_SPEC.md`). §3 daba `afternoon`(16:00)=1.00 y `dusk`(19:00)=0.66;
> recalculado con la interpolación lineal real de `luz_a_las()` en
> `src/framework/stage/day_night.py` entre las paradas (14.0→1.00, 18.0→0.80)
> y (18.0→0.80, 20.0→0.66): son **0.90** y **0.73**.

> **Qué es esto.** La especificación que **obliga** a cada nivel y cada jefe del
> proyecto: tamaño mínimo, cantidad mínima de enemigos, tipos de enemigo,
> objetos mínimos, control de día/noche, dificultad objetivo y mapa sugerido.
> El estudiante **puede usar libremente sus niveles** —tema, arte, clima,
> disposición— pero **debe** cumplir las reglas de esta especificación en las
> **tres evaluaciones del proyecto** (Entregable 1, Entregable 2, Entregable 3).
>
> Los documentos por nivel están en `docs/niveles/` (uno por stage y uno por
> jefe), con su mapa sugerido construido sobre el diseño canónico de
> `16_WORLD_DESIGN.md` —el mismo que se presentó en el Entregable 1—. El mapa
> sugerido es **reemplazable** por el del propio estudiante siempre que cumpla
> las reglas de aquí abajo.

---

## 1. Las tres evaluaciones del proyecto

| Entregable | Evaluación | Valor | Contenido | Niveles disponibles |
|---|---|---|---|---|
| **Entregable 1** | Evaluación Práctica I — Prototipo Funcional (Clase 5) | 15% | Escenario completo en TMX | Zona 1: **1-1**, **1-2**, **1-3** |
| **Entregable 2** | Evaluación Práctica II — Vertical Slice (Clase 8) | 15% | Jefe con fases O nivel de la Zona 2 | Jefes **1-4**, **2-4**, **3-4** o niveles **2-1**, **2-2**, **2-3** |
| **Entregable 3** | Evaluación Práctica III — Proyecto Final (Clase ~14) | 20% | Zona completa o nivel de la Zona 3 | Niveles **3-1**, **3-2**, **3-3** |

**Regla transversal:** las reglas mínimas de tamaño, enemigos, objetos y
día/noche de esta especificación se aplican **en todas las evaluaciones**,
esté el nivel en el entregable que esté. Un nivel de la Zona 2 presentado en el
Entregable 3 debe cumplir las reglas del Entregable 2 **y** las generales.

---

## 2. Reglas obligatorias globales

### 2.1 Tamaño mínimo y máximo

| Tipo de nivel | Mínimo | Máximo | Equivalencia |
|---|---|---|---|
| Nivel de travesía corto | **1600 × 608 px** (100×38 tiles) | 3200 × 608 px | 2–4 pantallas |
| Nivel de travesía largo | **2400 × 608 px** (150×38 tiles) | 3840 × 640 px | 3–5 pantallas |
| Nivel vertical (2-2) | **1600 × 800 px** (100×50 tiles) | 2400 × 800 px | ascenso real |
| Nivel bajo y expuesto (3-1) | **1600 × 224 px** (100×14 tiles) | 2400 × 224 px | pasillo al aire libre |
| Arena de jefe | **800 × 608 px** (50×38 tiles) | 1600 × 608 px | 1–2 pantallas, sin scroll obligatorio |

- Baldosa base **16×16 px** (la del framework; no usar 32 px salvo aprobación).
- El suelo de los niveles horizontales va en la fila 30 (**y = 480 px**).
- Se mide el **mapa completo** (`mapwidth`×`mapheight` en el TMX), no el área
  jugable. `validate_tmx.py --ci` comprueba las propiedades y
  `grade_stage.py` mide la nota del calificador.

### 2.2 Enemigos: tipos y cantidades mínimas

| Tipo de nivel | Tipos mínimos | Tipos máximos | Cantidad mínima total | En pantalla |
|---|---|---|---|---|
| Nivel de travesía | **2** | **3** (regla de `05_ENEMY_SPEC.md`) | **6** (corto) / **10** (largo) | ≤ 8 simultáneos |
| Nivel de jefe | — | — | los patrones del jefe | los del jefe + ≤ 6 invocados |
| 4-1 Cementerio | **0** | 0 | 0 (regla de oro: la atmósfera es el desafío) | 0 |
| 4-1b (variante acuática) | **1** | 1 | 1 (el pez abismal — `damage_on_contact=0`, no participa del combate) | 1 |

- La regla de oro de cero enemigos es del **cementerio**, no del slot
  `stage4_1` entero: 4-1b (AUD-518/519) la rompe a propósito con una sola
  criatura que no daña ni se puede dañar — sigue siendo "la atmósfera es
  el desafío", con una presencia que persigue en vez de testificar. Ver
  [[niveles/13b_STAGE_4_1B.md]].
- Todos los enemigos heredan de `EnemyBase` y se colocan como objetos punto en
  la capa `Objects` con su `type` real (`Walker`, `Flying`, `Shooter`, o una
  especie con nombre del bestiario — no existe un tipo genérico `EnemySpawn`).
  Los voladores en modo `bezier`/`patrol` enlazan sus `Waypoint` por
  `owner_id` (ver `06_TMX_SPEC.md` §6.3).
- Los 3 tipos máx. deben incluir **al menos un caminante y un volador o un
  tirador**: la composición suelo/aire/fondo es obligatoria en niveles de 3
  tipos.
- El primer encuentro con cada tipo se presenta **sin otras amenazas** (regla
  1.4 de la `66_GUIA_DE_LEVEL_DESIGN.md`).

### 2.3 Objetos mínimos (capas de objeto del TMX)

| Objeto | Mínimo | Regla |
|---|---|---|
| `PlayerSpawn` | 1 (exactamente 1) | Obligatorio, capa `Objects` |
| `Checkpoint` | 1 por cada pantalla y media (~1200 px) | Nunca bloqueado por enemigos; visible |
| `Portal`/`NextTrigger` | 1 (final) | Niveles de jefe: **prohibido** (sale por `STAGE_COMPLETE`) |
| `HazardZone` | 1 desde el nivel 2 de cada zona | Daño 0.25; nunca en el tramo de presentación |
| Coleccionables | 5 como mínimo | Objetos `Pickup` en la capa `Objects`, con `item_id` fijado (no existe una capa `Collectibles` — ver `06_TMX_SPEC.md`) |
| `MessageTrigger` | 1 en el nivel inicial de cada zona | Didáctico: presenta el concepto de la zona |
| `CameraLock` | 1 (solo donde hace falta) | Obligatorio en jefes (lock_x+lock_y) y en el ascenso vertical |
| `BossSpawn` | 1 (jefes) | Punto de entrada del jefe |

### 2.4 Reglas de gameplay y factor de juego (obligatorias)

1. **Un concepto académico por zona del nivel** (Unidades II–IX): el nivel
   enseña una cosa y la dificultad la hace visible.
2. **Dos soluciones donde se pueda**: un obstáculo con una sola solución es un
   pasillo con examen en medio.
3. **El castigo es el daño, no la caída infinita**: en niveles de la Zona 1 no
   hay fosos; el foso aparece desde la Zona 2 y siempre con una ruta segura.
4. **Límite de tiempo ≈ 2× la limpieza estimada.** Niveles de jefe: sin reloj.
5. **Ningún sistema oculto**: si algo dispara, se ve disparar; si algo se
   activa, se anuncia (mensaje o animación).
6. **La dificultad sube por decisión, no por daño**: los jefes suben la
   complejidad de lectura, no solo los números.
7. **Paletas de sprites ≤ 16 colores** y colores de zona respetados (campus
   ámbar, datacenter azul acero, Heredia piedra beige, cementerio verde
   espectral).

---

## 3. Control de día/noche (obligatorio en todos los niveles)

Todos los niveles del juego **llevan control del día**. No es decoración: es
una propiedad del TMX y el motor la aplica. Así se declara:

```text
Propiedades del mapa (Tiled):
  start_hour : "dusk" | "night" | "morning" | "noon" | "afternoon" | "dawn" | "midnight"
               o número (14.5) o "HH:MM" (22:30)
  day_length : segundos reales que tarda el ciclo completo de 24 h
               0 = reloj congelado en start_hour
```

Nombres válidos de `start_hour` (definidos en `src/framework/stage/day_night.py`):

| Nombre | Hora | Luz |
|---|---|---|
| `dawn` | 07:00 | Amanecer cálido (factor 0.72) |
| `morning` | 10:00 | Mañana (factor 1.00) |
| `noon` | 12:00 | Mediodía (factor 1.00) |
| `afternoon` | 16:00 | Tarde (factor 0.90) |
| `dusk` | 19:00 | Ocaso (factor 0.73) |
| `night` | 22:00 | Noche (factor 0.55) |
| `midnight` | 00:00 | Madrugada cerrada (factor 0.52) |

### 3.1 La regla del reloj continuo

**El reloj del mundo no salta entre niveles.** Cada nivel empieza a la hora en
que el nivel anterior terminó, y termina a la hora en que el siguiente empieza.
Para lograrlo se calcula `day_length` con la fórmula:

```text
day_length = duración_estimada_del_nivel_seg × 24 / horas_que_avanza
```

Ejemplo: el 1-1 dura ~150 s y avanza de 10:00 a 14:00 (4 h):
`day_length = 150 × 24 / 4 = 900 s`.

### 3.2 El arco de día por zona (obligatorio)

| Zona | Nivel inicial (dónde empieza) | Niveles intermedios | Jefe (dónde termina) |
|---|---|---|---|
| **Zona 1 — Campus** | **1-1: DÍA** (10:00, `morning`) | 1-2 tarde (→18:00), 1-3 ocaso (→22:00) | **1-4: NOCHE** (22:00, congelado) |
| **Zona 2 — Datacenter** | **2-1: ATARDECER** (17:00) | 2-2 ocaso→noche (→23:30), 2-3 noche cerrada (→02:30) | **2-4: NOCHE** (02:30, congelado) |
| **Zona 3 — Heredia** | **3-1: NOCHE** (22:00) | 3-2 madrugada→amanecer (→08:00), 3-3 mañana (→11:00) | **3-4: DÍA** (11:00, congelado en `noon`) |
| **Cementerio** *(sugerido)* | 4-1: ocaso (19:00) | — | **4-2: termina en AMANECER** (07:00) — el nuevo día tras la prueba |

Reglas de aplicación:

1. **El nivel inicial de cada zona declara obligatoriamente el `start_hour`
   indicado** (dónde empieza la luz de la zona).
2. **El nivel de jefe declara obligatoriamente cómo termina la zona**:
   `start_hour` = hora de final del arco y `day_length = 0` (congelado), o bien
   `day_length` calculado para que el reloj **llegue a esa hora justo al
   terminar la pelea** (un jefe que empieza a las 21:30 y dura ~3 min con
   `day_length = 240 × 24 / 1 = 5760 s` — no recomendado: congelar es más
   robusto).
3. **Los niveles intermedios** eligen su `start_hour` (continuo) y calculan su
   `day_length` con la fórmula 3.1. No pueden saltarse el arco (un 1-2 de
   noche rompe la Zona 1).
4. **La noche juega igual**: el motor garantiza ambiente aplicado ≥ 25 (el
   calibrado de `day_night.py`). No se compensa la noche subiendo daños.

### 3.3 Día/noche por nivel (resumen ejecutivo)

| Nivel | `start_hour` | `day_length` sugerido | Termina |
|---|---|---|---|
| 1-1 | `morning` (10:00) | 900 s | 14:00 |
| 1-2 | 14:00 | 900 s | 18:00 |
| 1-3 | 18:00 | 900 s | 22:00 |
| 1-4 (jefe) | `night` (22:00) | 0 (congelado) | **noche** |
| 2-1 | 17:00 | 1000 s | 20:30 |
| 2-2 | 20:30 | 1000 s | 23:30 |
| 2-3 | 23:30 | 1000 s | 02:30 |
| 2-4 (jefe) | 02:30 | 0 (congelado) | **noche** |
| 3-1 | `night` (22:00) | 500 s | 05:00 |
| 3-2 | 05:00 | 1200 s | 08:00 |
| 3-3 | 08:00 | 1200 s | 11:00 |
| 3-4 (jefe) | 11:00 | 0 (congelado) | **día** |
| 4-1 | `dusk` (19:00) | 900 s | 23:00 |
| 4-2 (jefe) | 23:00 | 720 s | **amanecer 07:00** |

---

## 4. Clima y ambiente (decisión creativa, con sugerencias)

El clima **no está reglamentado**: es la parte libre de la creatividad de cada
estudiante. El framework lo soporta desde Tiled (sistema de clima, partículas
de ambiente, focos, bloom, viñeta, estaciones). Sugerencias por zona:

| Zona | Climas que funcionan | Aviso |
|---|---|---|
| Zona 1 (campus selvático) | Lluvia fina, niebla de montaña, hojas cayendo | No ocultar a los enemigos: la noche ya baja la luz |
| Zona 2 (datacenter) | Calima térmica, chispas, partículas de calor, aire con polvo | El calor es el idioma: las partículas deben subir |
| Zona 3 (Heredia) | Viento, nubes que tapan el sol (bajan agresividad aérea), plumas al viento | El brillo del cielo controla la dificultad: es mecánica viva |
| Cementerio | Niebla baja, cenizas, fuego de los cuencos | La niebla nunca puede tapar los peligros del suelo |

Regla creativa única: **el clima no puede romper la jugabilidad** — si la
lluvia tapa los proyectiles o la niebla oculta los fosos, se corrige o se
retira (el calibrador de noche ya marcó el precedente: una noche que impide
jugar es un defecto, no una decisión).

---

## 5. Dificultad en estrellas

| Estrellas | Significado | Niveles |
|---|---|---|
| ★☆☆☆☆ | Llegada. Un solo peligro a la vez | 1-1 |
| ★★☆☆☆ | Aprendizaje. Combinación de dos amenazas al final | 1-2, 1-3 |
| ★★★☆☆ | Dominio. El examen de la zona; jefe inicial | 2-1, 2-2, 3-1, 1-4 (jefe) |
| ★★★★☆ | Exigencia. Combina los tres carriles y el tiempo aprieta | 2-3, 3-2, 3-3, 2-4, 3-4 (jefes) |
| ★★★★★ | La prueba final: memoria, adaptación y estilo | 4-2 (jefe) |

La estrella de cada nivel está en la ficha del nivel (`docs/niveles/`) y **no
se negocia**: si el playtest medio muere más de 3 veces en el mismo tramo, el
tramo se baja (regla de la `66`), no se sube la estrella.

---

## 6. Mapa sugerido

Cada documento de `docs/niveles/` incluye un **mapa sugerido** en ASCII,
construido sobre el diseño canónico de `16_WORLD_DESIGN.md` — el mismo que los
estudiantes presentaron en el **Entregable 1**. Uso:

- Se puede **usar tal cual** (cumple las reglas), o
- se puede **sustituir por el mapa propio del Entregable 1**, siempre que
  cumpla: tamaño mínimo (§2.1), enemigos mínimos (§2.2), objetos mínimos
  (§2.3), día/noche (§3) y gameplay (§2.4).

El mapa sugerido declara: zonas del nivel, dónde van los spawns de enemigos,
checkpoints, peligros y la disposición del terreno. Las coordenadas son
**guía**, no medida: lo que mide es el TMX final.

---

## 7. Checklist de validación (todas las evaluaciones)

- [ ] `mapwidth × mapheight` dentro del mínimo del tipo de nivel (§2.1)
- [ ] 2–3 tipos de enemigo (travesía) con cantidad mínima (§2.2)
- [ ] Primer encuentro de cada tipo sin otras amenazas
- [ ] 1 `PlayerSpawn`, checkpoints por pantalla y media, 1 `Portal` (travesía)
- [ ] Jefes: `BossSpawn` + `CameraLock` total + sin `NextTrigger` + sin reloj
- [ ] `start_hour` declarado y `day_length` conforme al arco de la zona (§3.2)
- [ ] Clima presente o ausente por decisión (nunca rompe jugabilidad)
- [ ] `python scripts/validate_tmx.py --ci` → 16/16 (o el conteo vigente)
- [ ] `python scripts/grade_stage.py` con nota ≥ la del calificador
- [ ] README del nivel con: concepto, estrellas, día/noche, clima, enemigos
  (tipos, conteos, unidades del curso que demuestran)

---

## 8. Documentos por nivel

Todos en `docs/niveles/`, uno por stage y uno por jefe:

| Doc | Nivel | Tipo | Entregable |
|---|---|---|---|
| `docs/niveles/01_STAGE_1_1.md` | 1-1 La Entrada | Travesía | 1 |
| `docs/niveles/02_STAGE_1_2.md` | 1-2 La Soda | Travesía | 1 |
| `docs/niveles/03_STAGE_1_3.md` | 1-3 Las Aulas | Travesía | 1 |
| `docs/niveles/04_BOSS_1_4.md` | 1-4 El Venado Sagrado | Jefe | 2 |
| `docs/niveles/05_STAGE_2_1.md` | 2-1 Oficinas / Planicie | Travesía | 2 |
| `docs/niveles/06_STAGE_2_2.md` | 2-2 Entrada y Antenas | Travesía vertical | 2 |
| `docs/niveles/07_STAGE_2_3.md` | 2-3 Las Oficinas | Travesía | 2 |
| `docs/niveles/08_BOSS_2_4.md` | 2-4 El Rey Terciopelo | Jefe | 2 |
| `docs/niveles/09_STAGE_3_1.md` | 3-1 La Entrada de Piedra | Travesía expuesta | 3 |
| `docs/niveles/10_STAGE_3_2.md` | 3-2 El Hall | Travesía | 3 |
| `docs/niveles/11_STAGE_3_3.md` | 3-3 El Patio | Travesía | 3 |
| `docs/niveles/12_BOSS_3_4.md` | 3-4 El Gavilán Camionero Mascarero | Jefe | 2 |
| `docs/niveles/13_STAGE_4_1.md` | 4-1 La Entrada al Cementerio | Atmosférico (profesor) | — |
| `docs/niveles/13b_STAGE_4_1B.md` | 4-1b La Fosa Abisal (variante del slot 4-1, AUD-518/519) | Atmosférico, sumergido (profesor) | 1 (el pez abismal, sin daño) |
| `docs/niveles/13c_STAGE_4_1C.md` | 4-1c Lo Que Flota en la Niebla (variante del slot 4-1, AUD-518/520) | Aéreo, musical (profesor) | — |
| `docs/niveles/14_BOSS_4_2.md` | 4-2 El Gran Shaman Paburu | Jefe final (profesor) | — |

---

## 🔗 Documentos Relacionados

- [[66_GUIA_DE_LEVEL_DESIGN.md|Guía de Level Design]] — el porqué de cada regla
- [[16_WORLD_DESIGN.md|World Design]] — la geografía canónica
- [[17_BOSS_SPEC.md|Boss Specification]] — el diseño fase a fase de los jefes
- [[06_TMX_SPEC.md|TMX Specification]] — cómo declarar todo en Tiled
- [[30_ASSIGNMENT_01_STAGE_DESIGN.md|Asignación 01]]
- [[31_ASSIGNMENT_02_BOSS_DESIGN.md|Asignación 02]]
