---
document_id: "LOI-BOSS-017"
title: "Legacy of InFest — Catálogo de jefes (diseño)"
aliases: ["Boss Specification", "Boss Spec", "Catálogo de jefes"]
tags: ["boss", "catalogo", "diseno", "entity"]
description: "Catálogo de diseño de los 4 jefes: 20 de 47 patrones implementados. NO es un contrato de API — ver §0.0"
source: "docs/17_BOSS_SPEC.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Catálogo de jefes (diseño)

**ID del documento:** LOI-BOSS-017
**Versión:** 2.1.0
**Estado:** Catálogo de diseño — **no es un contrato** (AUD-369)
**Requiere:** LOI-ENEMY-005, LOI-ARCH-003
**Audiencia:** Profesor, ayudantes, asistentes de código

> **AUD-455.** Traduce el documento completo y corrige: la sección §1
> citaba dos veces `77_SYLLABUS_ALIGNMENT_AUDIT.md` (y §8.1 una tercera vez)
> y una vez `28_DECISION_LOG.md`, documentos que no existen en este
> repositorio; su tabla de "estado de implementación" decía "Planned" para
> El Rey Terciopelo y para el Gran Shamán Paburu, cuando ambos ya tienen
> clase y patrones reales (`class BossRey`, `class BossPaburu`); la nota
> histórica de §6 sobre Paburu decía "Forma 1 implementada" cuando el código
> ya tiene las 4 formas; y §3.10 de `23_DATA_SCHEMAS.md` junto con §7.3 de
> `75_BIBLIA_TECNICA.md` decían que `BossSpawn` **no** existe — contradecía
> directamente a este mismo documento (§0, línea 131), que ya decía que sí
> (AUD-259). Verificado leyendo `src/framework/stage/stage_objetos.py`:
> `BossSpawn` funciona, y las dos referencias cruzadas quedaron corregidas.

---

## 0.0 Qué es este documento, y qué no — AUD-369

**Esto es un catálogo de diseño, no una especificación.** El cambio de
etiqueta no es cosmético: cambia qué significa cada línea de lo que sigue.

Medido el 2026-08-09: de los **47** patrones de ataque que este documento
nombra, el motor implementa **20**. Los otros 27 —FEATHER_STORM,
SERPENT_CARPET, MASK_BEAM, DIVE_BOMB y compañía, sin acentos graves porque
no existen— están descritos aquí y no están en ninguna parte del código.

(Que este párrafo tuviera que perder los acentos graves es la regla de
AUD-365 funcionando: `scripts/check_doc_symbols.py` lo puso en rojo en la
primera ejecución, sobre el texto que anunciaba justamente eso.)

Durante meses eso se leyó como deuda: veintisiete cosas que faltaban por
hacer. No lo es, y llamarlo así tenía un coste real. Dos de los cuatro jefes
—el Gavilán y las fases 2-3 del Rey— **son asignaciones de estudiante**: el
45 % de la rúbrica de `grade_boss` es precisamente que el alumno diseñe e
implemente sus patrones. Un documento que los da por especificados le está
quitando el trabajo y, a la vez, mintiendo sobre el estado del motor.

Y una especificación que nadie cumple envejece hasta ser mentira. El jefe de
referencia (`boss_venado`) saca **100/100** con la rúbrica actual sin
implementar ni uno de esos 27, lo que dice bastante sobre si eran requisitos.

Cómo leerlo entonces:

| Lo que ves | Cómo se lee |
|---|---|
| Un patrón con clase en el código | Contrato: existe y se llama así. `scripts/check_doc_symbols.py` lo vigila |
| Un patrón sólo descrito aquí | **Idea de diseño.** Material para el estudiante, no promesa del motor |
| §0 (abajo) | El estado real, medido, jefe por jefe |

Lo que **sí** es contrato vinculante de un jefe vive en `22_API_CONTRACTS.md`
(la API de `BossBase`) y en `scripts/grade_boss.py` (la rúbrica). Este
documento alimenta a los dos, y no manda sobre ninguno.

---

## 0. Qué de esto existe hoy (AUD-150)

> **Leer esto antes que nada.** Este documento describe **cuatro jefes** y
> unos cuarenta patrones de ataque. En el código hay **cuatro clases de jefe** y
> **17 patrones**. Lo demás es diseño: legítimo, útil y **no implementado**.
>
> *(Medido el 6 de agosto de 2026 — AUD-311. La versión anterior decía «tres
> clases y nueve patrones», y era cierta al escribirse: desde entonces apareció
> `BossGavilan` y `BossPaburu` pasó de una forma a cuatro.)*
>
> El registro de pendientes (`63`) lo llamaba «22 patrones que ningún jefe
> implementa» y sugería reescribir la especificación contra los jefes reales.
> No se reescribe: se **etiqueta**. Un diseño de jefe que aún no existe es lo
> que una especificación debe contener; lo que no puede es que nadie sepa cuál
> de las dos cosas está leyendo.

<!-- cita-historica -->

| Jefe | Clase en el código | Fases reales | Patrones que EXISTEN | Patrones sólo diseñados |
|---|---|---|---|---|
| El Venado Sagrado (§3) | `BossVenado` | 2 | `STOMP`, `CHARGE`, `VINE_TOSS`, `VINE_SWEEP`, `MUSHROOM_SPORE` | — |
| El Rey Terciopelo (§4) | `BossRey` | **1** | `VENOM_SPIT` | `SERPENT_CARPET`, `VENOM_BURST`, `SERPENT_WAVE`, y las formas ReyMetad de las fases 2-3 (nombre de diseño: no hay clase con ese nombre, y por eso va sin acentos graves — AUD-365) |
| El Gavilán Mascarero (§5) | `BossGavilan` | **1** | **ninguno** (`attack_patterns=[]`) | todo §5. Es **asignación de estudiante**: 45 % de la rúbrica de `grade_boss` |
| El Gran Shaman Paburu (§6) | `BossPaburu` | **4 formas** | Piedra: `STONE_SPIT`, `EYE_BEAM`, `EL_SELLO` · Máscara: `SPIRIT_WAVE`, `DUELO_DE_ECOS`, `MASK_PULSE` · Espíritu: `RELIC_SURGE`, `SPIRIT_FORM`, `ANCIENT_CALL`, `CONVERGENCE`, `EL_OFRECIMIENTO` | La Reliquia (forma 3) tiene `attack_patterns=[]`: se llenan al elegir 3A/3B, y esa elección no está escrita |

<!-- /cita-historica -->

**Cómo se comprobó.** Leyendo `attack_patterns` de cada `BossPhase` en las tres
clases y los métodos `_attack_*` / `_do_*` que las ejecutan. La lista de
patrones inventados del registro salía de citar nombres en este documento que
no aparecen en ningún fichero `.py`.

> **Actualización (AUD-265, 2026-08-04): el Gavilán ya tiene clase.** La fila
> de arriba dice «ninguna» y era cierta el día que se escribió; la entrega
> llegó después. Hoy existe `class BossGavilan(BossBase)` en
> `src/stages/stage3_4_boss_gavilan/boss_gavilan.py`, con su escena y su mapa.
>
> **Es parcial y lo dice ella misma**: implementa sólo la fase 1, «El Vuelo
> Circular» de §5.3, sin ataques y sin las fases 2 y 3. Los jefes son **cuatro**,
> uno de ellos a medias.
>
> Y no se completa desde aquí: `src/stages/` es **código de estudiantes**
> (invariante 1 de `CLAUDE.md`). Terminar el Gavilán es trabajo de quien lo
> tiene asignado, con esta especificación como contrato; lo que sí es trabajo
> del motor es que el documento diga la verdad sobre lo que hay.

### Aviso de asignación — el Gavilán está SIN ASIGNAR

**Estado a 4 de agosto de 2026.** Las etapas tempranas del Gavilán —lo que hay
en `boss_gavilan.py`— están **sin asignar**: nadie las mantiene hoy.

**El desarrollo completo del jefe Gavilán queda a cargo de los estudiantes.**
Es una asignación abierta, no deuda del motor. Quien la tome recibe:

<!-- cita-historica -->
| Lo que ya está hecho | Lo que falta por hacer |
|---|---|
| La clase `BossGavilan(BossBase)` con la fase 1, «El Vuelo Circular» (§5.3): órbita paramétrica con vectores explícitos (Unidad II) | Las **fases 2 y 3** completas |
| Su escena `Stage3_4BossGavilanScene` y su mapa (58,7 KB), ya en el registro y jugables | Los **patrones de ataque** de §5: `DIVE_BOMB`, `FEATHER_STORM`, `MASK_BEAM`, `ORBIT_SHRINK`, `RAPID_DIVE`, `FULL_FEATHER_STORM`, `MASK_FRAGMENT_STORM`, `FEATHER_TOSS` — hoy `attack_patterns=[]` |
| Nueve sprites en `assets/sprites/bosses/` (`dive`, `feather`, `glide`, `hover`, `masked`, `mask_frag`, `storm`, `hurt`, `death`) | Los **puntos débiles** (`WeakPoint`) y la **telegrafía** de cada ataque |
| Todo `BossBase` heredado gratis: fases, parry (AUD-243), escala de fase y teletransporte (AUD-257), arena, invocaciones | Los sonidos `SFX_BOSSES_GAVILAN_DIVE` y `_MASK_BEAM`, que **existen con fichero** y esperan su emisor |
<!-- /cita-historica -->

**Por dónde empezar, medido:** `src/stages/boss_venado/boss_venado.py` es el
jefe de referencia y hace las mismas cosas que §5 pide — telegrafía, puntos
débiles, proyectiles con curva, dos fases con escala y teletransporte, voz—.
Copiar de ahí es lo esperado, no hacer trampa.

**Cómo se califica:** `python scripts/grade_boss.py src/stages/stage3_4_boss_gavilan/boss_gavilan.py --json`
(100 puntos). Medido el 2026-08-04: el venado saca **100 %**, el Gavilán **45 %**. Esos 55 puntos son, literalmente, la tarea.

**`BossSpawn`** —el tipo de objeto de Tiled que §8 describe— **ya funciona
(AUD-259)**. Hasta entonces el motor no lo conocía y un estudiante que siguiera
esta especificación al pie de la letra recibía un aviso de tipo desconocido.

Declara **dónde entra** el jefe que nombra su propiedad `boss`:

```
type = "BossSpawn"      boss = "BossVenado"
```

y produce exactamente la misma entidad que escribir `BossVenado` como tipo,
porque se resuelve por el mismo registro. Sin `boss`, o con un nombre no
registrado, el cargador **avisa** en vez de callarse.

Los jefes existentes siguen colocándose con su tipo propio y no se tocó
ninguno: `BossSpawn` es aditivo y ningún mapa entregado lo declara.

---

## 1. Visión general

> **AUD-455 — esta sección estaba desactualizada frente a §0, que se
> escribió después y sí se remidió contra el código.** Citaba dos veces
> `77_SYLLABUS_ALIGNMENT_AUDIT.md` y una vez `28_DECISION_LOG.md`, ninguno de
> los cuales existe en este repositorio. Y la tabla de "estado de
> implementación" decía "Planned" (planeado, sin implementar) para El Rey
> Terciopelo y para el Gran Shamán Paburu — falso hoy: `class BossRey` y
> `class BossPaburu` existen y tienen clase, escena y patrones reales (ver
> la tabla medida de §0, líneas 78–84 de este documento).

Legacy of InFest tiene cuatro combates de jefe — uno por zona. Cada
asignación de jefe (salvo el Venado, de referencia) puede recaer en un
estudiante como su entrega del trimestre, igual que un Stage: el diseño de
este documento es el contrato que debe cumplir, tanto si lo implementa el
profesorado como si lo implementa el estudiante asignado.

**Origen y estado de implementación de cada jefe (ver también la tabla medida de §0):**

| Jefe | Origen | Estado de implementación |
|---|---|---|
| El Venado Sagrado (Zona 1) | Jefe de referencia del programa del curso. | **Implementado** — `BossVenado` en `src/stages/boss_venado/boss_venado.py` |
| El Rey Terciopelo (Zona 2) | Jefe oficial del programa del curso. | **Parcial** — `BossRey` existe con 1 fase real (`VENOM_SPIT`); las fases 2–3 son diseño sin implementar, entrega abierta |
| El Gavilán Camionero Mascarero (Zona 3) | Diseño confirmado como definitivo por el dueño del proyecto. | **Parcial y sin asignar** — `BossGavilan` existe con la fase 1 (órbita), sin ataques; ver el aviso de asignación más arriba |
| Gran Shamán Paburu (jefe final) | Jefe oficial del programa del curso (identidad y rol); la estructura de 4 formas es una elaboración del proyecto sobre esa base. | **Implementado** — `BossPaburu` con 4 formas y patrones reales (ver §0) |

Cada jefe es una entidad multifase que demuestra el pipeline académico completo del curso:
- Las transiciones de fase usan matemática de curvas de la **Unidad III** para el movimiento
- Los efectos visuales usan operaciones de color y filtro de las **Unidades V y VII**
- La detección de fase usa clasificación de la **Unidad IX** (en los jefes que aplica)

Todos los jefes heredan de `BossBase`, una subclase de `EnemyBase`. La clase `BossBase` añade gestión de fases, barras de vida por fase, un elemento de HUD de jefe dedicado y el evento `BOSS_PHASE_CHANGED`.

---

## 2. BossBase

### 2.1 Definición de la clase

`BossBase` extiende `EnemyBase` (ver `05_ENEMY_SPEC.md`) con lo siguiente:

| Propiedad | Tipo | Descripción |
|---|---|---|
| `phases` | `list[BossPhase]` | Lista ordenada de definiciones de fase |
| `current_phase` | `int` | Índice de la fase activa (base 0) |
| `phase_health_thresholds` | `list[float]` | Valores de vida en los que ocurren las transiciones de fase |
| `is_transitioning` | `bool` | Verdadero durante la animación de transición de fase |
| `transition_timer` | `float` | Cuenta atrás de la duración de la transición |

### 2.2 Definición de BossPhase

Cada fase es un dataclass `BossPhase`:

| Campo | Tipo | Descripción |
|---|---|---|
| `phase_index` | `int` | Número de fase (base 0) |
| `health_threshold` | `float` | El jefe pasa a la SIGUIENTE fase cuando la vida baja de este valor |
| `attack_patterns` | `list[str]` | Identificadores con nombre de los patrones de ataque de esta fase |
| `movement_type` | `str` | Estrategia de movimiento: `'stationary'`, `'bezier'`, `'sine'`, `'random_walk'` |
| `speed_multiplier` | `float` | Velocidad relativa a la base de la Fase 0 |
| `sprite_override` | `str | None` | Si está fijado, reemplaza la hoja de sprites de esta fase |
| `filter_effect` | `str | None` | Efecto de FilterTools aplicado a la superficie del jefe cada fotograma: `'sobel'`, `'canny'`, `'tint_green'`, etc. |

### 2.3 Protocolo de transición de fase

Cuando la vida del jefe baja de `phase_health_thresholds[current_phase]`:

1. `is_transitioning = True`
2. El jefe se vuelve invencible (`invincibility_timer = INF`)
3. Se reproduce la animación de transición (típicamente 2–3 segundos)
4. Se emite `BOSS_PHASE_CHANGED` con `phase = current_phase + 1`
5. La barra de vida del jefe en el HUD se vuelve a llenar al máximo de la nueva fase
6. `current_phase += 1`
7. `is_transitioning = False`
8. Expira la invencibilidad; se reanuda el combate

### 2.4 Elemento de HUD del jefe

Durante las escenas de jefe se dibuja una barra de vida de jefe dedicada al pie de la pantalla, separada de la vida del jugador:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │ Y=208
│  [BOSS NAME          ] [████████████████████████████████] [P1]  │ Y=212
│                                                                 │ Y=220
└─────────────────────────────────────────────────────────────────┘
```

| Elemento | Descripción |
|---|---|
| Nombre del jefe | Alineado a la izquierda, dorado. **AUD-365:** este documento nombraba una fuente «banner_medium» que nunca ha existido — sin acentos graves ahora, porque no es una API. `hud.py:215` lo dibuja con la fuente por defecto de pygame a 12 px. Darle una fuente de mapa de bits propia es trabajo de diseño abierto, no un defecto |
| Barra de vida | Se llena de izquierda a derecha. Color: rojo con vida llena, pasa a naranja y luego amarillo según se agota |
| Indicador de fase | `[P1]`, `[P2]`, etc. — se actualiza al cambiar de fase |

---

## 3. Boss 1 — El Venado Sagrado

### 3.1 Concepto

**Nombre:** El Venado Sagrado
**Ubicación:** Stage 1-4 — La Residencia
**Vida:** 12 corazones (repartidos en 2 fases)

El Venado Sagrado es el espíritu de un venado de cola blanca antiguo — una criatura del bosque que lleva décadas muerta, hoy reclamada por completo por la naturaleza. Su esqueleto está entrelazado con lianas, cubierto de musgo y helechos, con escarabajos y gusanos recorriéndolo. Le crecen hongos de las costillas. No camina — **flota**, como si el propio bosque lo llevara.

**Referencias de diseño:**
- El venado de cola blanca (Odocoileus virginianus) — el animal
- Estética de espíritu del bosque: el Espíritu del Bosque de Studio Ghibli, el diseño gótico de huesos de Demon's Crest
- Paleta SNES: 16 colores — blanco hueso, verde musgo profundo, marrón tierra, crema de hongo, negro sombra

### 3.2 Especificaciones de sprite

| Hoja | Fichero | Fotogramas | FPS | Bucle |
|---|---|---|---|---|
| Fase 1 — Flotar | `boss_venado_drift.png` | 6 | 8 | Sí |
| Fase 1 — Ataque pisotón | `boss_venado_stomp.png` | 8 | 12 | No |
| Fase 1 — Ataque embestida | `boss_venado_charge.png` | 6 | 14 | No |
| Fase 2 — Flotar frenético | `boss_venado_frenzy_drift.png` | 6 | 14 | Sí |
| Fase 2 — Ataque barrido de lianas | `boss_venado_vine.png` | 10 | 12 | No |
| Daño | `boss_venado_hurt.png` | 4 | 12 | No |
| Muerte | `boss_venado_death.png` | 12 | 8 | No |

**Tamaño de sprite:** 48×48 píxeles
**Hitbox:** 36×44 px (desplazada 6px desde la izquierda del sprite, 4px desde arriba)
**Hurtbox:** 30×40 px (centrada en el sprite)

### 3.3 Fases

#### Fase 1 — "El Bosque Duerme" (Vida: 12 → 6 corazones)

**Condición de entrada:** Se cargó el Stage 1-4, terminó el rótulo
**Tipo de movimiento:** Flotación senoidal por la arena (horizontal, amplitud=40px, frecuencia=0.4 Hz)
**Velocidad:** base de 60 px/s horizontal

**Patrones de ataque:**

| Nombre del patrón | Disparador | Descripción |
|---|---|---|
| `STOMP` | Jugador a menos de 96px horizontalmente | El jefe se yergue y golpea con las pezuñas delanteras. Crea un rectángulo de onda de choque de 96px de ancho a nivel del suelo. Daño: 1.0 corazón. |
| `CHARGE` | Jugador en la mitad opuesta de la arena | El jefe embiste horizontalmente a 220px/s. Daño de contacto: 0.75 corazones. Se detiene en la pared de la arena. |
| `VINE_TOSS` | Cada 8 segundos | Suelta un proyectil de liana que viaja en un arco de Bézier hasta una posición predicha del jugador. Daño: 0.5 corazones. |

**Tiempos de espera de ataque:**
- `STOMP`: 3.0 segundos
- `CHARGE`: 6.0 segundos
- `VINE_TOSS`: 8.0 segundos

**Efecto visual (Unidad VII):**
Fase 1: se aplica `FilterTools.sobel_edge()` a la superficie del jefe cada 5 fotogramas y se mezcla a alfa=80 sobre el sprite. Crea un aura sutil de brillo de bordes — como si el bosque delineara al venado.

**Ilustración académica (Unidad III):**
El proyectil de `VINE_TOSS` sigue un arco de Bézier de grado 2:
- Punto de control 0: posición del hocico del jefe
- Punto de control 1: punto medio elevado 80px
- Punto de control 2: posición predicha del jugador (posición actual + velocidad × 0.5s)

#### Fase 2 — "El Bosque Despierta" (Vida: 6 → 0 corazones)

**Transición:**
1. El jefe deja de moverse (0.5s)
2. Las lianas del esqueleto pulsan y se retuercen (animación especial)
3. Crecen dos extensiones nuevas de liana en la cornamenta (cambio de sprite)
4. Se emite `BOSS_PHASE_CHANGED`
5. Sube la velocidad, se desbloquean ataques nuevos

**Tipo de movimiento:** Camino de Bézier — figura de 8 precalculada por la arena
**Multiplicador de velocidad:** ×1.5

**Patrones de ataque nuevos:**

| Nombre del patrón | Disparador | Descripción |
|---|---|---|
| `VINE_SWEEP` | Cada 5 segundos | El jefe barre ambas astas-liana en un arco amplio. Hitbox a nivel del suelo de ancho completo (320×24px). Daño: 0.5 corazones. Se evita saltando. |
| `MUSHROOM_SPORE` | Cada 10 segundos | Suelta 3 proyectiles de esporas en abanico (izquierda, centro, derecha) desde la posición del jefe. Cada uno viaja en línea recta. Daño: 0.25 corazones cada uno. |
| `CHARGE` | Sigue disponible — más rápido | Ahora a 280 px/s. |

**Efecto visual (Unidad VII — Fase 2):**
Fase 2: `FilterTools.apply_kernel(sobel_x_kernel)` aplicado cada 3 fotogramas crea un brillo direccional que se intensifica según baja la vida. Con menos de 3 corazones, el jefe parpadea visualmente entre normal y la capa de bordes cada fotograma.

### 3.4 Elementos de la arena

| Elemento | Posición | Tipo | Descripción |
|---|---|---|---|
| Plataforma de piedra I | X=48, Y=160 | Un sentido | Plataforma elevada a la izquierda |
| Plataforma de piedra C | X=136, Y=144 | Un sentido | Plataforma alta central |
| Plataforma de piedra D | X=224, Y=160 | Un sentido | Plataforma elevada a la derecha |
| Arco de lianas | X=272–320 | Sólo visual | Punto de entrada del jefe |

### 3.5 Correspondencia académica

| Fase | Unidad académica | Implementación |
|---|---|---|
| Flotar en fase 1 | Unidad III — trayectoria senoidal | `position.y = base_y + A * sin(2πft)` |
| Lanzar liana en fase 1 | Unidad III — proyectil de Bézier | `CurveTools.bezier(control_points, 32)` |
| Aura de fase 1 | Unidad VII — bordes de Sobel | `FilterTools.sobel_edge(boss_surface)` |
| Camino de fase 2 | Unidad III — camino de Bézier en la arena | Figura de 8 precalculada con 6 puntos de control |
| Parpadeo de fase 2 | Unidad VII — convolución de núcleo | `FilterTools.apply_kernel(sobel_x)` |

### 3.6 Secuencia de derrota

1. Se reproduce la animación de muerte (12 fotogramas, 8 FPS)
2. El jefe se disuelve en partículas de hojas/lianas flotantes (sistema de partículas con sprite, 8 sprites)
3. Queda una calavera de venado brillante durante 2 segundos
4. La calavera se desvanece — aparece un icono nuevo en el HUD: **Fragmento de Reliquia 1** (icono de cornamenta)
5. Se emite `STAGE_COMPLETE`
6. Transición al Stage 2-1

---

## 4. Jefe 2 — El Rey Terciopelo

<!-- cita-historica -->
> **Estado (AUD-150): fase 1 implementada, fases 2 y 3 no.** `BossRey` existe
> con una sola `BossPhase` y un único patrón, `VENOM_SPIT`. Todo lo que este
> apartado dice de serpientes, ráfagas y mitades ReyMetad es diseño.
<!-- /cita-historica -->

### 4.1 Concepto

**Nombre:** El Rey Terciopelo
**Ubicación:** Stage 2-4 — El Datacenter
**Vida:** 15 corazones en total, repartidos en 3 fases (5 por fase)

El Rey Terciopelo no es una sola criatura — son miles de víboras terciopelo fundidas en una inteligencia colectiva, que anima un cuerpo humanoide descompuesto como su vasija. El cuerpo es su **marioneta** — fluyen dentro y fuera de él por sus articulaciones y su boca, comunicándose por señales de veneno. El cuerpo se mueve a tirones, de forma antinatural — controlado desde dentro.

**Referencias de diseño:**
- La terciopelo (Bothrops asper) — la serpiente más peligrosa de Costa Rica
- Estética de movimiento de marioneta/títere
- Descomposición e infestación — ciclos de animación tipo gusano dentro de la silueta del cuerpo

### 4.2 Especificaciones de sprite

| Hoja | Fichero | Fotogramas | FPS | Bucle |
|---|---|---|---|---|
| Fase 1 — Caminar | `boss_rey_walk.png` | 8 | 10 | Sí |
| Fase 1 — Escupir | `boss_rey_spit.png` | 6 | 12 | No |
| Fase 2 — Dividirse | `boss_rey_split.png` | 8 | 10 | Sí (dos entidades) |
| Fase 3 — Fusionarse | `boss_rey_merge.png` | 6 | 8 | No |
| Fase 3 — Frenesí | `boss_rey_rampage.png` | 8 | 16 | Sí |
| Daño | `boss_rey_hurt.png` | 4 | 12 | No |
| Muerte | `boss_rey_death.png` | 14 | 8 | No |

**Tamaño de sprite:** Fase 1: 40×56 px. Entidades divididas de fase 2: 24×28 px cada una.
**Hurtbox de fase 1:** 28×48 px

### 4.3 Fases
<!-- diseno-pendiente -->

#### Fase 1 — "La Marioneta" (Vida: 15 → 10 corazones)

**Tipo de movimiento:** Caminata aleatoria errática — la posición se actualiza con sacudidas cada 0.3s usando `CurveTools.catmull_rom()` por 4 posiciones aleatorias de la arena
**Velocidad:** 50 px/s

**Patrones de ataque:**

| Patrón | Disparador | Descripción |
|---|---|---|
| `VENOM_SPIT` | Jugador a menos de 200px | Escupe un grumo de veneno lento que viaja en línea recta. Daño: 0.5 corazones. |
| `SERPENT_CARPET` | Cada 10 segundos | Suelta 6 enemigos pequeños `WalkerSerpientePequena` desde su cuerpo. Daño al tocarlos: 0.25 corazones cada uno. |
| `BODY_SLAM` | Jugador a menos de 64px | Se lanza 80px hacia delante al instante. Daño de contacto: 1.0 corazón. |

**Efecto visual (Unidad V):**
Fase 1: `ColorTools.apply_tint(boss_surface, (30, 80, 0))` — un tinte verde enfermizo aplicado a toda la superficie del jefe cada fotograma, que da al cuerpo descompuesto un brillo venenoso.

#### Fase 2 — "La División" (Vida: 10 → 4 corazones)

**Transición:**
1. El cuerpo se estremece y colapsa
2. Dos corrientes de serpientes salen y forman dos **sub-jefes independientes**: ReyMitad (mitad izquierda) y ReyMitad (mitad derecha)
3. Cada mitad tiene 3 corazones de vida propia
4. Cuando las dos mitades llegan a 0, empieza la Fase 3

**Comportamiento del sub-jefe:**
- Cada ReyMitad se comporta como un `EnemyWalker` agrandado con el `VENOM_SPIT` de la Fase 1
- Se coordinan: uno ataca mientras el otro se reposiciona
- Daño de contacto: 0.5 corazones

**Cómo se dispara la Fase 3:**
Cuando las dos entidades ReyMitad llegan a 0 de vida, no mueren — disparan `BOSS_PHASE_CHANGED` simultáneamente. El escenario captura ese evento e inicia la Fase 3.

#### Fase 3 — "El Frenesí" (Vida: 4 → 0 corazones)

**Transición:**
1. Las dos mitades colapsan y las serpientes vuelven a fundirse
2. El cuerpo se reensambla — ahora más rápido y más grande (sprites escalados ×1.25 con la transformación de pygame)
3. El cuerpo pulsa con veneno verde

**Tipo de movimiento:** Persecución agresiva en línea recta al jugador a 130 px/s
**Multiplicador de velocidad:** ×2.6 respecto a la Fase 1

**Patrones de ataque nuevos:**

| Patrón | Disparador | Descripción |
|---|---|---|
| `VENOM_BURST` | Cada 6 segundos | Escupe 5 grumos de veneno en abanico (ángulos: -30°, -15°, 0°, +15°, +30°). Cada uno: 0.25 corazones. |
| `SERPENT_WAVE` | Cada 12 segundos | Suelta 12 serpientes a la vez por todo el suelo de la arena. Duración 3 segundos. |
| `LUNGE` | En cualquier posición del jugador | Embiste 160px en dirección al jugador a 350px/s. 1.25 corazones de daño. Tiempo de espera de 8 segundos. |

**Efecto visual (Unidad IX — punto académico destacado):**
La Fase 3 introduce una mecánica de reconocimiento de patrones. El jefe alterna entre tres subestados cada 8–15 segundos: `AGGRESSIVE` (embiste con frecuencia), `DISPERSED` (suelta serpientes) y `DEFENSIVE` (ráfaga de veneno a distancia). La transición entre estados no se anuncia explícitamente.

La idea de diseño incluye comentarios documentando que un estudiante con conocimientos de la Unidad IX podría implementar un clasificador que detecte el subestado actual analizando el historial de posición del sprite del jefe o la densidad de serpientes activas en pantalla — y usarlo para informar la estrategia del jugador. Queda documentado como ejercicio de extensión.

<!-- /diseno-pendiente -->
### 4.4 Secuencia de derrota

1. Animación de muerte: el cuerpo colapsa, las serpientes se dispersan y se retuercen
2. Todos los `WalkerSerpientePequena` se desactivan de inmediato
3. Queda una gran cabeza de terciopelo, que se disuelve en luz verde
4. Aparece el **Fragmento de Reliquia 2** (icono de serpiente enroscada)
5. Se emite `STAGE_COMPLETE` → Zona 3

---

## 5. Jefe 3 — El Gavilán Camionero Mascarero

<!-- cita-historica -->
> **Estado (AUD-150): NO EXISTE.** No hay clase, ni sprites, ni escena. El
> registro de escenarios reserva el hueco `stage3_4_boss_gavilan` y los
> créditos ya lo citan, pero el jefe está entero por hacer. Todo este apartado
> es diseño; ninguno de sus patrones —`DIVE_BOMB`, `FEATHER_STORM`,
> `MASK_BEAM` y los demás— aparece en el código.
<!-- /cita-historica -->

### 5.1 Concepto

**Nombre:** El Gavilán Camionero Mascarero
**Ubicación:** Stage 3-4 — El Bungaló
**Vida:** 14 corazones en 3 fases

El Gavilán es un gavilán caminero común (Buteo magnirostris, llamado coloquialmente "gavilán camionero" en Costa Rica porque se posa en los rótulos de la carretera). Una máscara ceremonial Tilawa se ha fundido con la cara del gavilán, dándole inteligencia y poder sobrenaturales. La máscara pulsa con energía dorada Tilawa. El gavilán es enorme — envergadura igual al ancho de la arena.

**Referencias de diseño:**
- Buteo magnirostris — gavilán real de Costa Rica
- Máscaras ceremoniales Tilawa — artefacto cultural ficticio (tratado con profundo respeto)
- Estética de Medusa de Super Castlevania IV — depredador aéreo grande y lento

**Nota cultural:** la máscara Tilawa se representa con respeto y reverencia. Se presenta como un objeto sagrado que la influencia de Paburu se apropió — la máscara en sí no es maligna, ha sido corrompida. La secuencia de derrota honra esto.

### 5.2 Especificaciones de sprite

| Hoja | Fichero | Fotogramas | FPS | Bucle |
|---|---|---|---|---|
| Fase 1 — Planear | `boss_gavilán_glide.png` | 8 | 10 | Sí |
| Fase 1 — Picado | `boss_gavilán_dive.png` | 6 | 16 | No |
| Fase 2 — Flotar | `boss_gavilán_hover.png` | 4 | 8 | Sí |
| Fase 2 — Tormenta de plumas | `boss_gavilán_storm.png` | 8 | 12 | No |
| Fase 3 — Brillo de máscara | `boss_gavilán_masked.png` | 6 | 14 | Sí |
| Daño | `boss_gavilán_hurt.png` | 4 | 12 | No |
| Muerte | `boss_gavilán_death.png` | 16 | 8 | No |
| Fragmento de máscara | `boss_gavilán_mask_frag.png` | 4 | 12 | No (proyectil) |

**Tamaño de sprite:** 56×40 px (más ancho que alto — énfasis en la envergadura)
**Hurtbox:** 40×28 px (centro del cuerpo, sin las puntas de las alas)

### 5.3 Fases
<!-- diseno-pendiente -->

#### Fase 1 — "El Vuelo Circular" (Vida: 14 → 9 corazones)

**Tipo de movimiento:** Órbita circular alrededor del centro de la arena
- Radio de órbita: 80px desde el centro
- Velocidad orbital: 0.6 radianes/segundo (una vuelta completa en ~10 segundos)
- Se calcula como: `position = center + (cos(angle) * radius, sin(angle) * radius)`
- Documentado en comentarios del código fuente como ilustración de movimiento paramétrico circular (Unidad II — vectores, Unidad III — paramétrico)

**Patrones de ataque:**

| Patrón | Disparador | Descripción |
|---|---|---|
| `DIVE_BOMB` | Cada 6 segundos | Sale de la órbita, se lanza en picado directo a la X actual del jugador, y vuelve a la órbita. Velocidad: 300px/s. Daño: 0.75 corazones. |
| `FEATHER_TOSS` | Cada 8 segundos | Suelta 4 proyectiles de plumas en direcciones cardinales (izquierda, derecha, abajo-izquierda, abajo-derecha). Cada uno: 0.25 corazones. |
| `ORBIT_SHRINK` | A 11 corazones | El radio de órbita baja a 48px — el gavilán queda más cerca y es más difícil de esquivar |

**Efecto visual (Unidad V):**
Fase 1: se aplica `ColorTools.rgb_to_hsv()` a la superficie del jefe cada fotograma, el tono rota +5° por segundo, y `ColorTools.hsv_to_rgb()` reconvierte. Crea un brillo iridiscente lento en las plumas.

#### Fase 2 — "El Ojo de la Máscara" (Vida: 9 → 4 corazones)

**Transición:**
1. El gavilán se detiene en el centro de la arena (se mantiene 1 segundo)
2. La máscara Tilawa empieza a brillar — animación de pulso en la región de la máscara
3. El gavilán sube al centro-arriba de la arena y flota ahí toda la fase
4. `BOSS_PHASE_CHANGED`

**Tipo de movimiento:** Flotación estacionaria en (160, 48)
**La Fase 2 introduce dominio aéreo — el gavilán nunca aterriza, nunca se mueve de su punto de flotación. Todos los ataques son hacia abajo.**

**Patrones de ataque nuevos:**

| Patrón | Disparador | Descripción |
|---|---|---|
| `FEATHER_STORM` | Cada 7 segundos | Suelta 8 plumas en un abanico completo hacia abajo. Velocidades variables. Duración: 3 segundos de plumas cayendo. 0.25 corazones cada una. |
| `MASK_BEAM` | Cada 10 segundos | Dispara un rayo vertical hacia abajo desde el ojo de la máscara. Rectángulo de 24px de ancho, instantáneo, altura completa de la arena. Daño: 1.0 corazón. Destello de aviso de 0.5s antes de activarse. |
| `WIND_BLAST` | Cada 12 segundos | Viento horizontal empuja al jugador 96px en la dirección a la que mira el gavilán. Sin daño — disrupción posicional. |

**Efecto visual (Unidad VII):**
Fase 2: `FilterTools.gaussian_blur(boss_surface, sigma=0.8)` aplicado cada 3 fotogramas crea un brillo suave alrededor de la máscara. El radio de desenfoque aumenta según baja la vida.

#### Fase 3 — "La Máscara Sin Control" (Vida: 4 → 0)

**Transición:**
1. La máscara Tilawa se agrieta — se animan líneas de fractura por ella
2. Estalla energía dorada de las grietas (sprites de partículas)
3. El gavilán desciende de su flotación, ahora impredecible

**Tipo de movimiento:** Errático — combina picados y flotación al azar. Usa `CurveTools.catmull_rom()` por 6 puntos aleatorios (pero acotados) de la arena.

**Patrones de ataque nuevos:**

| Patrón | Disparador | Descripción |
|---|---|---|
| `MASK_FRAGMENT_STORM` | Cada 8 segundos | Trozos rotos de la máscara vuelan hacia fuera en 6 direcciones. Cada fragmento tiene 0.5 corazones de daño y rebota una vez en las paredes de la arena. |
| `RAPID_DIVE` | Cada 4 segundos | Dos picados consecutivos en rápida sucesión (0.5s de separación). |
| `FULL_FEATHER_STORM` | Cada 15 segundos | Tormenta extendida — 16 plumas a lo largo de 5 segundos. |

**Efecto visual (Unidad VII — Fase 3):**
`FilterTools.canny_edge(boss_surface, 40, 120)` mezclado a alfa=100 sobre el sprite del jefe. La máscara fracturada crea bordes fuertes que el filtro de Canny resalta — la forma del gavilán queda rodeada de líneas de borde ásperas e irregulares, a juego con la estética de máscara rota.

**Punto académico destacado (Unidad IX):**
El patrón de movimiento de la Fase 3 — una combinación de picados y flotación errática — se podría clasificar en teoría con un clasificador entrenado sobre el historial de posición. Se documenta como ejercicio avanzado: dada la posición Y del gavilán en los últimos 10 fotogramas, clasificar si la siguiente acción será `DIVE` o `HOVER` y posicionar al jugador en consecuencia.

<!-- /diseno-pendiente -->
### 5.4 Secuencia de derrota

1. Animación de muerte: el gavilán cae al suelo de la arena
2. La máscara Tilawa se eleva lentamente de la cara del gavilán — flota hacia arriba, pulsando suavemente
3. La máscara brilla en dorado cálido y se disipa (se libera, no se destruye)
4. El gavilán vuelve a su tamaño natural — un gavilán caminero normal — y se va volando por el tragaluz
5. Aparece el **Fragmento de Reliquia 3** (icono de contorno de máscara)
6. Se emite `STAGE_COMPLETE` → Zona final

---

## 6. Jefe final — El Gran Shamán Paburu

> **AUD-455 — la nota de AUD-150 de arriba estaba desactualizada frente a §0
> (medido después, AUD-311).** Decía "Forma 1 implementada" con sólo tres
> patrones; hoy `BossPaburu` define las **4 formas** con `attack_patterns`
> reales: Piedra (`STONE_SPIT`, `EYE_BEAM`, `EL_SELLO`), Máscara
> (`SPIRIT_WAVE`, `DUELO_DE_ECOS`, `MASK_PULSE`), Espíritu (`RELIC_SURGE`,
> `SPIRIT_FORM`, `ANCIENT_CALL`, `CONVERGENCE`, `EL_OFRECIMIENTO`) — la
> Reliquia (forma 3) tiene `attack_patterns=[]` porque se rellena al elegir
> la rama 3A/3B, no porque esté sin hacer. Confirmado leyendo
> `src/stages/boss_paburu/boss_paburu.py` directamente.

### 6.1 Concepto

**Nombre:** El Gran Shamán Paburu
**Ubicación:** Stage 4-2 — El Cementerio Sagrado
**Vida:** 20 corazones en total, repartidos en 4 fases (5 por fase)

Paburu es el Gran Shamán — una figura espiritual Tilawa de poder inmenso, corrompida por un duelo antiguo. No pelea para destruir — pelea para **poner a prueba**. La Pepita de Oro y la Perla que llevan John y Jill son las últimas llaves de su ritual. Necesita ver si son dignos.

Sus cuatro formas no son entidades separadas — son capas de su poder, cada una revelando más de quién es en realidad.

### 6.2 Especificaciones de sprite

| Hoja | Fichero | Fotogramas | FPS | Bucle |
|---|---|---|---|---|
| Forma 1 — Cabeza de piedra | `boss_paburu_stone.png` | 4 | 6 | Sí |
| Forma 1 — Golpe de piedra | `boss_paburu_stone_slam.png` | 8 | 12 | No |
| Forma 2 — Máscara espectral | `boss_paburu_mask.png` | 6 | 10 | Sí |
| Forma 2 — Onda espectral | `boss_paburu_mask_wave.png` | 8 | 12 | No |
| Forma 3A — Esfera dorada | `boss_paburu_gold.png` | 6 | 14 | Sí |
| Forma 3B — Esfera negra | `boss_paburu_black.png` | 6 | 14 | Sí |
| Forma 3 — Ataque de reliquia | `boss_paburu_relic_atk.png` | 10 | 14 | No |
| Forma 4 — Espíritu | `boss_paburu_spirit.png` | 8 | 10 | Sí |
| Forma 4 — Oleada espiritual | `boss_paburu_spirit_surge.png` | 12 | 14 | No |
| Daño | `boss_paburu_hurt.png` | 4 | 12 | No |
| Muerte | `boss_paburu_transcend.png` | 20 | 8 | No |

**Tamaños de sprite:**
- Forma 1: 64×64 px
- Forma 2: 56×72 px
- Forma 3: 32×32 px (esferas)
- Forma 4: 64×80 px

---

### 6.3 Forma 1 — "La Cabeza de Piedra" (Vida: 20 → 15)

**Visual:** una cabeza de piedra enorme — piedra verde tallada, estilo precolombino. Ojos cerrados. Descansa en el suelo del cementerio, ligeramente hundida. Al empezar la batalla, los ojos se abren: brillo verde.

**Movimiento:** estacionaria. La cabeza de piedra no se mueve horizontalmente. Puede inclinarse ligeramente a izquierda y derecha (animación visual, ±8px).

**Patrones de ataque:**

| Patrón | Disparador | Descripción |
|---|---|---|
| `STONE_SPIT` | Cada 4 segundos | Escupe proyectiles de piedra en arco (3 proyectiles, separados 15°). Daño: 0.5 corazones cada uno. |
| `EYE_BEAM` | Cada 8 segundos | Dispara un rayo horizontal desde ambos ojos a la vez. El rayo mide 8px de alto, viaja a 200px/s. Daño: 1.0 corazón. |
<!-- diseno-pendiente -->
| `GROUND_SLAM` | Cada 10 segundos | Sacude la pantalla (el desplazamiento de cámara oscila ±4px durante 0.5s). Aparecen fisuras (HazardZone) en 3 posiciones X aleatorias (24px de ancho, altura completa). Daño: 0.5 corazones. Duración: 2 segundos. |
<!-- /diseno-pendiente -->

**Efecto visual (Unidad V):**
`ColorTools.apply_tint(stone_surface, (0, 120, 40))` — la cabeza de piedra tiene un tinte espectral verde permanente, que refuerza la atmósfera sobrenatural del cementerio.

**Narrativa de la transición de fase:**
Al bajar a 15 corazones: la cabeza de piedra se agrieta. Las tres siluetas espirituales del Stage 4-1 (venado, serpiente, gavilán) emergen de las grietas y fluyen hacia la forma de Paburu. El caparazón de piedra cae. Emerge la Forma 2.

---

### 6.4 Forma 2 — "La Máscara Espectral" (Vida: 15 → 10)

**Visual:** una figura espectral imponente — el contorno de un shamán, hecho enteramente de energía verde. Donde estaría la cara: una máscara Tilawa masiva y flotante, verde y translúcida. La máscara es el punto de daño — el contorno del cuerpo es invulnerable.

**Tipo de movimiento:** flotación lenta a la deriva — onda senoidal vertical (amplitud: 20px, frecuencia: 0.3 Hz) mientras se mueve horizontalmente a 40px/s.

**Punto de daño:** sólo la máscara (una hurtbox de 40×40px centrada en el sprite de la máscara) recibe daño. El contorno del cuerpo no registra golpes.

**Patrones de ataque:**

| Patrón | Disparador | Descripción |
|---|---|---|
| `SPIRIT_WAVE` | Cada 5 segundos | Envía una onda de energía espectral por el suelo (se evita agachándose) O por el techo (se evita saltando). Alterna. Daño: 0.5 corazones. |
<!-- diseno-pendiente -->
| `SUMMON_ECHOES` | Cada 12 segundos | Invoca copias espectrales de los tres jefes derrotados (eco de venado, de serpiente, de gavilán) — cada uno hace un ataque y se disipa. Daño del eco: 50% del original. |
<!-- /diseno-pendiente -->
| `MASK_PULSE` | Cada 7 segundos | La máscara suelta una onda de choque circular. Daño a menos de 80px: 0.75 corazones. |

**Efecto visual (Unidad VII):**
`FilterTools.adjust_brightness(mask_surface, factor = 0.8 + 0.4 * sin(elapsed_time * 3))` aplicado cada fotograma — la máscara pulsa con un efecto de brillo que respira.

**Ecos espirituales:**
Los tres ecos son instancias de entidad ligeras que usan los mismos sprites que los jefes derrotados, pero con:
- `set_alpha(120)` — semitransparentes
- 50% del daño de ataque original
- Un solo ataque y luego se autodestruyen

---

### 6.5 Forma 3 — "La Reliquia" (Vida: 10 → 5) — fase aleatoria
<!-- diseno-pendiente -->

**Transición visual:**
1. La forma de máscara espectral se disuelve
2. La Pepita de Oro y la Perla vuelan hasta la arena — antes en manos de John y Jill
3. La mano de Paburu las atrapa
4. Se pone la máscara
5. **En este punto, el juego elige al azar la Forma 3A o la Forma 3B**

La elección aleatoria tiene semilla por sesión (no por intento). El jugador aprende qué forma esperar por experiencia.

---

#### Forma 3A — "La Pepita" (esfera dorada) — ofensiva

**Visual:** la máscara se transforma en una esfera dorada brillante (32×32 px). Rápida, errática.

**Tipo de movimiento:** persecución agresiva. Usa `vec2_normalize()` hacia el jugador a 120px/s, con una sacudida cada 0.5 segundos (desplazamiento de dirección aleatorio ±30°).

**Características:**
- Puramente ofensiva — sin ataques estacionarios
- Se mueve constante y rápido
- Daño de contacto: 1.0 corazón

**Patrones de ataque:**

| Patrón | Descripción |
|---|---|
| `GOLD_RUSH` | Acelera a 240px/s durante 0.8 segundos cada 5 segundos |
| `GOLD_BURST` | En múltiplos de 1.0 de vida: suelta 8 proyectiles de orbe dorado en todas direcciones (abanico radial). Cada uno: 0.25 corazones |
| `RICOCHET` | El orbe dorado rebota en las paredes de la arena (refleja el vector de velocidad al tocar la pared). Sigue siendo rápido. |

**Nota académica (Unidad II):** el rebote en las paredes es una aplicación directa de la reflexión vectorial: `velocity = velocity - 2 * dot(velocity, normal) * normal`. Documentado en el código fuente como ilustración de la Unidad II.

---

#### Forma 3B — "La Perla" (esfera negra) — defensiva

**Visual:** la máscara se transforma en una esfera negra profunda (32×32 px), lenta, metódica.

**Tipo de movimiento:** orbita lentamente el centro de la arena con radio 64px. Velocidad: 0.3 radianes/segundo.

**Características:**
- Puramente defensiva — rara vez se acerca al jugador
- Genera trampas y denegación de área
- Daño de contacto: 0.5 corazones

**Patrones de ataque:**

| Patrón | Descripción |
|---|---|
| `DARK_FIELD` | Coloca una zona lenta de 48×48 en el suelo (la velocidad del jugador se reduce a la mitad dentro). Dura 8 segundos. Coloca hasta 3 a la vez. |
| `PEARL_VOLLEY` | Dispara 3 orbes negros lentos en abanico hacia el jugador. Cada uno: 0.5 corazones. Los orbes persisten 6 segundos (largo alcance). |
| `PULL` | Cada 10 segundos: atrae al jugador hacia la esfera 120px con una fuerza gravitacional (velocity += normalize(sphere_pos - player_pos) * 80 * dt durante 1 segundo). |

**Nota académica (Unidad II — implementación de atracción gravitacional):**
El ataque PULL implementa directamente una atracción gravitacional simplificada: `attraction_vector = normalize(paburu_pos - player_pos) * G_CONSTANT`. Documentado en línea como matemática vectorial de la Unidad II.

---

<!-- /diseno-pendiente -->
### 6.6 Forma 4 — "El Espíritu del Shamán" (Vida: 5 → 0)

**Narrativa de la transición:**
1. La esfera (dorada o negra) se disuelve lentamente
2. Se materializa una figura alta y antigua — la verdadera forma espiritual de Paburu
3. Mira a John y Jill durante un largo momento
4. Luego levanta la mano — y empieza la batalla final

**Visual:** una figura espectral alta y delgada. Túnicas de luz fluyente. Cara antigua — pacífica pero inmensa. Ojos que brillan en blanco. Manos que brillan alternando luz dorada y de perla.

**Tipo de movimiento:** flotación vertical lenta — sube y baja en un patrón senoidal (amplitud: 32px, frecuencia: 0.2 Hz). Se mueve horizontalmente muy despacio (20px/s), a la deriva.

**Vida:** 5 corazones. Cada golpe lo tambalea levemente (breve animación de pausa en la flotación).

**Patrones de ataque:**

| Patrón | Disparador | Descripción |
|---|---|---|
| `RELIC_SURGE` | Cada 6 segundos | Las dos reliquias (pepita y perla) orbitan a Paburu y sueltan ráfagas simultáneas hacia fuera — orbes dorados (rápidos, pocos) y orbes negros (lentos, muchos). Dorado: 0.5 corazones, negro: 0.25 corazones. |
| `SPIRIT_FORM` | Cada 10 segundos | Paburu se vuelve momentáneamente intangible — la hurtbox se desactiva 1.5 segundos. Sigue soltando ataques durante la intangibilidad. |
| `ANCIENT_CALL` | Cada 15 segundos | Los tres ecos espirituales (venado, serpiente, gavilán) aparecen a la vez durante 3 segundos y cada uno hace un ataque. Luego se disipan. |
| `CONVERGENCE` | Con 2 corazones restantes | Ataque de una sola vez: las dos reliquias convergen sobre el jugador. El jugador tiene 2 segundos de aviso (las reliquias telegrafían orbitando hacia él). Si golpea: 2.0 corazones (fuerte). Se evita moviéndose al borde extremo izquierdo o derecho. |

**Efecto visual (Unidades VII + VIII — aplicación académica combinada):**
- `FilterTools.sobel_edge(boss_surface)` mezclado a alfa=60 — refuerzo del contorno espiritual
- `VisionTools.threshold_binary(screen_region_around_boss, 180)` usado en el Stage 4-2 como ejercicio de estudiante (en el README del escenario): identificar la "zona activa" alrededor de Paburu para predecir patrones de ataque

---

### 6.7 Secuencia de derrota de Paburu

1. A 0 de vida: la forma espiritual de Paburu no cae — se eleva
2. Las reliquias (pepita y perla) vuelan hacia John y Jill respectivamente
3. Paburu extiende los brazos — se mantiene un momento largo (4 segundos de animación)
4. Los tres guardianes espirituales (venado, serpiente, gavilán) aparecen una última vez — y se inclinan ante Paburu
5. Paburu también se inclina — y se disuelve en luz dorada
6. El cementerio queda en silencio. La pantalla se funde a blanco.
7. Empieza la secuencia final / los créditos

---

## 7. Resumen académico de los jefes

| Jefe | Unidades clave | API principal del framework | Lo que se lleva el jugador |
|---|---|---|---|
| El Venado Sagrado | III, VII | `CurveTools.bezier`, `FilterTools.sobel_edge` | Proyectiles de curva, aura de Sobel |
| El Rey Terciopelo | III, V, IX | `CurveTools.catmull_rom`, `ColorTools.apply_tint` | Fase multicuerpo, efecto de tinte |
| El Gavilán Camionero | II, III, V, VII, IX | Paramétrico circular, `FilterTools.gaussian_blur`, `FilterTools.canny_edge` | Órbita circular, brillo de desenfoque, fractura de Canny |
| El Gran Shamán Paburu | II, V, VII, VIII | `ColorTools.apply_tint`, `FilterTools.adjust_brightness`, `VisionTools.threshold_binary` | Reflexión vectorial, brillo que respira, visión binaria |

---

## 8. Integración con el framework de jefes

### 8.1 Ficheros necesarios

Las rutas usan el prefijo `src/`; los ficheros de implementación de jefe viven en la carpeta de entrega asignada al estudiante bajo `src/stages/`, o junto a `src/stages/stage0/` si son del profesorado (sin reclamar).

| Fichero | Descripción | Dueño habitual |
|---|---|---|
| `src/framework/entities/boss_base.py` | Clase `BossBase` — gestor de fases, evento de barra de vida | Profesorado (siempre) |
| `src/stages/boss_venado/boss_venado.py` | Implementación de El Venado Sagrado | Jefe de referencia del profesorado |
| `src/stages/boss_rey/boss_rey.py` | Implementación de El Rey Terciopelo | Estudiante asignado, o profesorado si no está reclamado |
| `src/stages/stage3_4_boss_gavilan/boss_gavilan.py` | El Gavilán Camionero Mascarero | Estudiante asignado, o profesorado si no está reclamado |
| `src/stages/boss_paburu/boss_paburu.py` | El Gran Shamán Paburu (4 formas) | Profesorado (el jefe final no se asigna a un solo estudiante) |

### 8.2 Objetos TMX necesarios

Todo TMX de escenario de jefe debe contener:
- Un objeto `BossSpawn` en el punto de entrada del jefe
- Un `CameraLock` que cubra toda la arena del jefe (lock_x=true, lock_y=true)
- Sin `NextTrigger` — los escenarios de jefe se completan vía el evento `STAGE_COMPLETE` que emite la secuencia de muerte del jefe

### 8.3 Integración con el HUD

Al entrar a un escenario de jefe:
- Se oculta el temporizador estándar
- Aparece la barra de vida del jefe (pie de pantalla)
- El nombre del jefe se muestra en la barra
- El evento `BOSS_PHASE_CHANGED` actualiza el indicador de fase y rellena el segmento de la barra


---
## 🔗 Documentos relacionados

- [[44_BOSS_RUSH_MODE.md|Modo Boss Rush]]
- [[05_ENEMY_SPEC.md|Especificación de enemigos]]
