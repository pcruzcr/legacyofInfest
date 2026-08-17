---
document_id: "LOI-STAGE0-007"
title: "Legacy of InFest — Diseño del Escenario 0"
aliases: ["Stage 0 Design", "Reference Stage", "Escenario de referencia"]
tags: ["stage0", "reference", "design"]
description: "Escenario de referencia del equipo docente"
source: "docs/07_STAGE0_DESIGN.md"
date_processed: "2026-08-15"
---

# Legacy of InFest — Diseño del Escenario 0

**ID del documento:** LOI-STAGE0-007
**Versión:** 3.0.0
**Estado:** Oficial
**Público:** profesorado, asistentes, estudiantes, asistentes de código

> **AUD-491 (2026-08-15) — rediseño completo del trazado.**
> La versión 2.0.0 de este documento (AUD-114) ya describía con precisión el
> `.tmx` de esa fecha. Lo que cambia aquí no es una corrección de cifras: es
> el propio nivel. Dos sistemas construidos después de esa versión —material
> por zona (AUD-490, `GAP-039`) y el impulso al golpear un proyectil
> (AUD-305, *bash*)— llevaban desde entonces sin aparecer en ningún nivel
> real, incluido el que se supone que enseña todo el motor. `stage0.py`
> tampoco coincidía: su docstring describía seis zonas con otros nombres y
> sus coleccionables apuntaban a coordenadas que ningún `.tmx` había tenido
> nunca — la misma clase de mentira que AUD-114 ya había cazado una vez en
> este mismo documento.
>
> Todas las cifras de aquí abajo se **derivan del `.tmx`** —generado por
> `tools/generate_stage0_tmx.py`, no editado a mano— y
> `tests/test_stage0_platform_solidity.py` las vuelve a comprobar en cada
> ejecución de la suite.

---

## 1. Para qué existe el Escenario 0

El Escenario 0 no es un tutorial en el sentido comercial. Es la **documentación
ejecutable** del framework: cada sistema que un estudiante va a usar para
construir su escenario aparece aquí, funcionando, con un mensaje que explica qué
está pasando.

Quien lo haya jugado y leído su fuente debería poder:

1. Entender la API del framework sin leer el motor.
2. Saber cómo se comporta cada sistema dentro de un escenario en marcha.
3. Usarlo como implementación de referencia para su propia entrega.

También es la **calibración del calificador**: `scripts/grade_stage.py` le pone
130/130, que es la nota que un estudiante puede aspirar a igualar.

### 1.1 Principios

- **Ningún sistema oculto.** Todo lo que se activa se anuncia con un mensaje.
- **Complejidad creciente.** El orden de las zonas es el orden del temario.
- **Zonas reintentables.** Hay un checkpoint antes de cada bloque difícil.
- **Dos soluciones donde se pueda, tres donde el sistema lo permita.** El foso
  se salta, se cruza cronometrando los bloques, *o* se cruza rebotando en una
  zona de goma. Un obstáculo con una sola solución es un pasillo con un
  examen en medio.
- **Nada se enseña dos veces si ya se enseñó una.** El rediseño movió el
  combate a distancia antes que la variedad cuerpo a cuerpo: esquivar un solo
  proyectil es más simple que gestionar tres enemigos a la vez, y el orden
  del temario debe seguir esa dificultad, no la cronología de cuándo se
  implementó cada arquetipo.
- **Modo depuración.** `F1` dibuja cajas de golpe, de daño, conos de visión y
  rectángulos de colisión. Es material didáctico, no un truco.

---

## 2. Trazado

Mapa horizontal de **100 × 38 baldosas** de 16 px = **1600 × 608 px**. El suelo
está en la fila 30 (**y = 480 px**) y el avance es de izquierda a derecha.

```
  x=48    224      400        720        912         1024  1600
   │       │        │          │           │            │    │
 SPAWN ──A──[▮]──B──[Walker]──C──[hielo]──D──[bash]──E──[llave]──F──[goma]──G──[viento]──SALIDA
                    liana                 Caster       puerta      bloques  tirolesa/cofre
```

| Zona | Rango x (px) | Qué enseña |
|---|---|---|
| A | 48 – 220 | moverse, saltar, y el primer obstáculo sólido |
| B | 224 – 390 | el primer enemigo, inevitable |
| C | 384 – 720 | la colina escalonada, liana, **hielo**, primer salto exigente |
| D | 720 – 895 | combate a distancia, **el *bash*** |
| E | 912 – 1040 | combate variado cuerpo a cuerpo, llave y puerta cerrada |
| F | 1024 – 1200 | el foso: salto, bloques rítmicos, o **goma** |
| G | 1312 – 1600 | todo junto, viento, tirolesa y cofre |

### 2.1 Tema visual

Corredor de piedra neutro, legible, sin ruido atmosférico que tape lo que se
está demostrando. Tileset `tileset_stage0.png`.

### 2.2 Geometría vertical

- **Suelo:** filas 30–37 (y 480–608), sólido.
- **Muros de cierre:** x = −16 y x = 1600, de 608 px de alto. Quedan fuera del
  área jugable y `level_metrics` los descarta antes de medir repisas.
- **Obstáculos sólidos interiores:** dos, y son lo único contra lo que se choca
  de lado en todo el escenario.

  | x | Alto | Dónde | Para qué |
  |---|---|---|---|
  | 160 | 2 baldosas (32 px) | zona A | se salta desde parado |
  | 288 | 3 baldosas (48 px) | zona B/C | obliga a aprovechar el impulso |

  AUD-506 movió el segundo de la columna 50 a la 18: la colina de la zona C
  ocupa las columnas 24–50, y un obstáculo ahí quedaba enterrado dentro del
  propio sólido de la colina — mismo tramo, misma altura, cero efecto.

  El salto del jugador alcanza **72 px** medidos
  (`tests/playtest/jump_bench.py`). Este número **no cambió** con el
  rediseño — es una constante física, no una decisión de contenido, y
  tocarla exige recalibrar `grade_stage.py` y los 16 mapas que comparten su
  vara de medir (ver `KNOWN_GAPS.md`, GAP-036).

- **Plataformas atravesables** (`Platform`, un solo sentido — no confundir
  con la colina de la zona C, que es `Solid`: se pisa desde cualquier lado
  porque es terreno, no una repisa):

  | x | y | Ancho | Zona |
  |---|---|---|---|
  | 928 | 336 | 160 px | E — la ruta alta bypass |
  | 1408 | 336 | 128 px | G |

- **Foso:** x 1056 – 1152 (96 px), con `DeathPit` al fondo.

---

## 3. Zona por zona

### Zona A — moverse, saltar y chocar (x 48 – 220)

**Sistemas:** andar, saltar, tiempo del coyote, corte de salto, colisión
horizontal contra un sólido.

- Aparición del jugador en x = 48.
- `MessageTrigger_Once` en x = 80: *«Flechas para moverte. Espacio para
  saltar.»*
- Obstáculo sólido de 2 baldosas en x = 160. Sin enemigos: el primer choque del
  jugador es contra geometría, no contra algo que le quite vida.

**Checkpoints:** ninguno todavía.

---

### Zona B — el primer enemigo (x 224 – 390)

**Sistemas:** `Walker`, patrulla, detección de borde, estado de alerta, daño por
contacto, fotogramas de invulnerabilidad.

- `MessageTrigger_Once` en x = 224: *«Z ataca. También puedes saltar por
  encima.»* Va **después** del mensaje de salto, para que el jugador ya sepa
  saltar cuando se le ofrece esa salida.
- `Walker` en x = 288, `patrol_length=80`, `patrol_speed=60`, `alert_speed=90`,
  2 de vida.

Está **en el camino**, no a un lado. Es la lección de Mario 1-1 del dossier del
Top 200: el castigo por contacto se enseña sin una línea de texto, y las dos
soluciones —pelear o saltar— se ofrecen a la vez.

**Checkpoint 0:** x = 352.

---

### Zona C — la colina, liana y hielo (x 384 – 816)

**Sistemas:** terreno sólido escalonado (`_altura_colina`, AUD-506), `Vine`
con `TrepandoState`, `Pickup`, enemigo volador con trayectoria senoidal,
**material por zona** (`ZonaDeFriccion`, AUD-490).

AUD-506 sustituyó las dos repisas flotantes del primer rediseño (AUD-491) por
una colina de verdad: una escalera sólida de un escalón (16 px) por columna
entre x = 384 y x = 816, sube seis escalones (x 384–464), se aplana en una
meseta de seis baldosas de alto (x 464–704) y baja los mismos seis escalones
(x 704–816). Cada escalón es un `Solid` independiente —no una `Slope`
diagonal— porque 16 px se sube de un salto corto y no hace falta rampa.

- `MessageTrigger_Once` en x = 400: *«Sube. Con X te agarras a la liana.»*
- `Pickup` «fragmento_1» en (464, 400), sobre el último escalón de la subida.
- `Flying` en x = 480: `flight_mode=sine`, amplitud 32, frecuencia 2,0
  (Unidad III), sobrevolando la meseta.
- `Vine` en x = 528, desde la fila 19 hasta la superficie de la meseta (fila
  24) — 80 px de largo, `ancho_de_agarre=12`. Antes de AUD-506 bajaba hasta
  el suelo llano (176 px) y su tramo final quedaba enterrado dentro del
  sólido de la meseta.
- `MessageTrigger_Once` en x = 576: *«Hielo. Sueltas menos el salto, no
  más.»*
- **Hielo sobre la meseta** en (576, 384), 112 px: una `FrictionZone` con
  `material="hielo"` sobre la superficie real de la meseta,
  `multiplicador=0.55` — primer uso real de AUD-490 en un nivel jugado. No es
  una baldosa distinta a propósito: el jugador tiene que leer «esta repisa
  está tomada» por cómo resbala, no por su color.

El **salto exigente** que el calificador exige lo pone ahora la propia colina:
subir sus seis escalones seguidos, con hielo esperando en la cima.

**Checkpoint 1:** x = 688, y = 352 (sobre la meseta, no sobre el suelo llano).

---

### Zona D — fuego de respuesta, y el *bash* (x 720 – 895)

**Sistemas:** `Archer`, `Caster`, proyectiles, **el impulso al golpear un
proyectil** (`admite_bash`, AUD-305).

- `MessageTrigger_Once` en x = 720: *«Esa flecha se puede golpear para
  impulsarte.»*
- `Archer` en x = 784: `fire_rate=1.6`, proyectil a 90 px/s, 1,5 de daño,
  **`admite_bash=True`** — primer uso real de AUD-305 en un nivel jugado. La
  flecha se puede esquivar, como siempre, o golpear para ganar impulso.
- `Caster` en x = 832 (Unidad de reconocimiento de patrones — orbe
  homing).
- `Pickup` «fragmento_2» en (864, 464).

El combate a distancia va **antes** que la variedad cuerpo a cuerpo de la zona
E a propósito: esquivar o interceptar un solo proyectil es más simple que
gestionar tres arquetipos a la vez, y el orden del temario sigue esa
dificultad.

**Checkpoint 2:** x = 880.

---

### Zona E — combate variado, llave y puerta (x 912 – 1040)

**Sistemas:** `Charger`, `Brute`, `Key`, `LockedDoor`, obstáculo alto.

- `MessageTrigger_Once` en x = 912: *«La llave abre la puerta del fondo.»*
- `Key` «llave_prologo» en x = 944.
- `Charger` en x = 992 (`charge_speed=250`).
- Obstáculo sólido de 3 baldosas en x = 800 (ver §2.2 — está antes de esta
  zona a propósito, para que el impulso que exige ya esté aprendido cuando
  llega el combate).
- `Brute` en x = 1040, 6 de vida, caja de 100 × 60.
- `LockedDoor` en x = 1040, `key_id=llave_prologo`, con mensaje de bloqueo.

La llave está **antes** de la puerta: el estudiante ve que un objeto de
inventario y un obstáculo de geometría resuelven cosas distintas.

**Checkpoint 3:** x = 1040.

---

### Zona F — el foso, tres formas de cruzarlo (x 1024 – 1200)

**Sistemas:** `DeathPit`, `RhythmBlock`, **material por zona** (`goma`,
AUD-490), `HazardZone`.

- `MessageTrigger_Once` en x = 1024: *«Salta, cronometra los bloques, o
  prueba la goma.»*
- Foso en x 1056 – 1152 con `DeathPit` al fondo.
- Tres `RhythmBlock` en x 1072, 1088 y 1104, a y = 400:
  `visible_seg=1.8`, `oculto_seg=1.0`, `desfase` 0, 0,6 y 1,2 — cascada, así
  que la ruta de arriba existe pero hay que cronometrarla.
- **Zona de goma** en (1040, 576), justo al borde del foso: una
  `FrictionZone` con `material="goma"` — aterrizar ahí devuelve el 60 % de
  la velocidad vertical de impacto (`Material.GOMA.restitucion=0.6`) en vez
  de frenar en seco, así que cruza el foso rebotando en dos tiempos. Es la
  **tercera** ruta, no una alternativa decorativa a las otras dos.
- `HazardZone` en x = 1184, daño 0,25 por tic — el nivel de daño «leve».

Tres formas de pasar: saltar el foso, cronometrar los bloques, o rebotar en la
goma. Es el sitio del escenario donde más se nota la diferencia entre diseñar
y poner obstáculos — y ahora demuestra dos mecánicas de movilidad en vez de
una.

---

### Zona G — todo junto, tirolesa y cofre (x 1312 – 1600)

**Sistemas:** `Shooter`, `Assassin`, `Zipline` con `TirolesaState`, `Chest`,
`CameraLock`, `WindZone` (fase 5), `NextTrigger`, ataque definitivo.

- `MessageTrigger_Once` en x = 1312: *«El viento empuja. Espera a que amaine.
  U es el ataque definitivo.»*
- `WindZone` en x 1344 – 1504, 160 × 160 px: `fuerza_x=210`, `periodo=3.4`. La
  fuerza es periódica, así que la solución es **esperar**, no insistir.
- `Shooter` en x = 1392: a distancia, con patrulla — un enemigo a distancia
  inmóvil se resuelve andando dos pasos a un lado.
- `Assassin` en x = 1440, acercamiento rápido.
- `Walker` en x = 1488, 2 de vida — segunda aparición del arquetipo más
  simple, ahora en un tramo con más presión alrededor.
- `Pickup` «fragmento_3» en (1472, 320).
- `Chest` «reliquia_prologo» en (1504, 320) — la recompensa por subir.
- `Zipline` en (1488, 320): `destino_dx=80`, `destino_dy=128`, 200 px/s.
- `CameraLock` en x = 1376, 224 px de ancho, `lock_y=true`.
- `Checkpoint 4` en x = 1424 — el único de las siete zonas que no marca el
  final de un bloque difícil sino el principio del clímax, para que morir en
  la combinación final no obligue a rehacer el viento.
- `NextTrigger` en x = 1552.

---

## 4. Inventario del mapa

Cifras derivadas del `.tmx`; si dejan de cuadrar, la suite avisa.

| | |
|---|---|
| Tamaño | 100 × 38 baldosas (1600 × 608 px) |
| Capas | 8 |
| Enemigos | 9, de **8** tipos (los ocho arquetipos del bestiario) |
| Mensajes de tutorial | 8 |
| Checkpoints | 5 (ids 0–4) |
| Coleccionables | 5 (3 `Pickup`, 1 `Key`, 1 `Chest`) |
| Relics adicionales (Python, fuera del `.tmx`) | 4 — ver §4.2 |
| Focos `Light` | 12 |
| Obstáculos sólidos interiores | 2 |
| Plataformas de un sentido | 2 |
| Zonas de material (`FrictionZone`) | 2 — hielo (zona C) y goma (zona F) |

### 4.1 Enemigos

| Tipo | x | Nota |
|---|---|---|
| `Walker` | 288 | 2 de vida, patrulla 80 px |
| `Flying` | 480 | senoidal, amplitud 32, frecuencia 2,0 |
| `Archer` | 784 | proyectil a 90 px/s, **`admite_bash=True`** |
| `Caster` | 832 | ataque a distancia (orbe homing) |
| `Charger` | 992 | embestida a 250 px/s |
| `Brute` | 1040 | 6 de vida |
| `Shooter` | 1392 | disparo cada 2 s |
| `Assassin` | 1440 | acercamiento rápido |
| `Walker` | 1488 | 2 de vida |

### 4.2 Coleccionables permanentes (fuera del `.tmx`)

Cuatro reliquias que `Stage0._place_collectibles` coloca por código, no desde
Tiled — bonifican estadísticas vía `Inventory`/`apply_relic_bonuses` y no
tienen equivalente TMX porque no son objetos de escenario, son progresión de
cuenta. Repuestas en el rediseño (AUD-491) en posiciones dentro de las siete
zonas nuevas — las anteriores no correspondían a ningún trazado real, ni el
viejo ni el actual.

| item_id | Columna, fila | Zona |
|---|---|---|
| `swift_feather` | 20, 25 | B — sobre el Walker |
| `heart_vessel` | 40, 19 | C — junto a la repisa de hielo |
| `ancients_rib` | 63, 23 | E — junto al combate variado |
| `sunken_crown` | 95, 19 | G — junto al cofre final |

### 4.3 Checkpoints

| id | x | Contexto |
|---|---|---|
| 0 | 352 | tras el primer enemigo |
| 1 | 688 | tras las plataformas, la liana y el hielo |
| 2 | 880 | tras el arquero con *bash* y el hechicero |
| 3 | 1040 | tras el combate variado y la puerta |
| 4 | 1424 | al entrar al tramo final, antes del viento |

### 4.4 Propiedades de mapa

`stage_id`, `stage_name`, `author`, `bgm_track`, `background_zone`, `climate`,
`time_limit`, `gravity_multiplier`, `ambient_light`, `start_hour`, `day_length`,
`season`, `zone`, `bloom`, `vignette`, `ambient_fx`, `ambient_fx_rate`.

Las tres primeras son las que exige el calificador. Las demás encienden clima,
ciclo día/noche, estaciones, iluminación y post-procesado: si un estudiante
quiere saber qué se puede pedir desde Tiled, esta lista es la respuesta.

---

## 5. Fin del escenario

### 5.1 Final normal

El jugador entra en el rectángulo `NextTrigger` de x = 1552 estando en el suelo.

1. Se emite `STAGE_COMPLETE`.
2. El audio se atenúa.
3. La pantalla funde a negro y se queda en negro hasta el corte.
4. `SceneManager` reemplaza la escena por la siguiente.

### 5.2 Temporizador

`time_limit = 0`: el Escenario 0 no tiene límite. El reloj del HUD se muestra
como demostración y cuenta hacia arriba.

---

## 6. Fallos

### 6.1 Muerte del jugador

Con `Salud` a cero: se emite `PLAYER_DIED`, se reproduce la animación, se apila
`GameOverScene`. **Continuar** reaparece en el último checkpoint con la vida
llena; **Salir** vuelve al título.

### 6.2 Foso

El `DeathPit` de la zona F pone la vida a cero directamente, sin pasar por los
niveles de daño ni por la invulnerabilidad. Es instantáneo a propósito: un foso
que quita media vida enseña a caerse dentro. La zona de goma amortigua la
caída del jugador, no la quita: sigue siendo posible fallar el rebote y caer.

---

## 7. Lista de sistemas demostrados

| Sistema | Zona | Documento |
|---|---|---|
| Andar, saltar, tiempo del coyote, corte de salto | A | `04_PLAYER_SPEC.md` §4 |
| Colisión horizontal contra sólido | A, E | `06_TMX_SPEC.md` §9 |
| Ataque corto y largo, hitstop | B | `04_PLAYER_SPEC.md` §7 |
| Caja de daño y de golpe | B, D | `04_PLAYER_SPEC.md` §10–11 |
| `Walker`: patrulla, borde, alerta, contacto | B, G | `05_ENEMY_SPEC.md` §3 |
| Invulnerabilidad tras recibir daño | B | `04_PLAYER_SPEC.md` §5.3 |
| Plataforma de un solo sentido | C, G | `06_TMX_SPEC.md` §9.2 |
| Vuelo senoidal (Unidad III) | C | `05_ENEMY_SPEC.md` §4 |
| Liana / `TrepandoState` | C | `STAGE_CREATION.md` |
| **Material por zona — hielo, goma** (AUD-490) | C, F | `KNOWN_GAPS.md` GAP-039 |
| `Pickup` e inventario | C, D, G | `06_TMX_SPEC.md` §6 |
| `Archer`, `Caster` a distancia | D | `05_ENEMY_SPEC.md` §5–6 |
| **El *bash*** (AUD-305) | D | `collision_system.py` |
| `Charger`, `Brute` | E | `05_ENEMY_SPEC.md` §7 |
| `Key` y `LockedDoor` | E | `06_TMX_SPEC.md` §6 |
| `DeathPit` | F | `06_TMX_SPEC.md` §9.3 |
| `RhythmBlock` | F | `STAGE_CREATION.md` |
| `HazardZone` y daño leve | F | `04_PLAYER_SPEC.md` §6.1 |
| `Shooter` a distancia, proyectiles, `atan2` | G | `05_ENEMY_SPEC.md` §5 |
| `WindZone` | G | `STAGE_CREATION.md` |
| `Assassin` | G | `05_ENEMY_SPEC.md` §8 |
| Tirolesa / `TirolesaState` | G | `STAGE_CREATION.md` |
| `Chest` | G | `06_TMX_SPEC.md` §6 |
| `CameraLock` | G | `06_TMX_SPEC.md` §8 |
| `NextTrigger` y fin de escenario | G | `06_TMX_SPEC.md` §8 |
| Checkpoints | B–G | `06_TMX_SPEC.md` §7 |
| Mensajes de tutorial | A–G | `09_HUD_SPEC.md` §5 |
| HUD: corazones y reloj | todas | `09_HUD_SPEC.md` §3–4 |
| Iluminación por focos | todas | `06_TMX_SPEC.md` §5 |
| Clima, ciclo día/noche, estaciones | todas | `06_TMX_SPEC.md` §4 |
| Bloom y viñeta | todas | `03_ARCHITECTURE.md` §2.6 |
| Cámara, parallax, capas TMX | todas | `06_TMX_SPEC.md` §3 |
| `EventBus`, audio | todas | `03_ARCHITECTURE.md` §8.5 |
| Superposición de depuración (`F1`) | todas | `03_ARCHITECTURE.md` §2 |

### 7.1 Lo que el Escenario 0 **no** demuestra

Honestidad por delante: de las once mecánicas de la fase 5, el prólogo usa
**cinco** tras el rediseño (liana, tirolesa, bloques rítmicos, zona de viento,
y ahora material por zona). Las otras seis —agua y nado, plataformas móviles,
plataformas hundibles, tiempo bala, scroll forzado, sigilo con cono de
visión— viven en `assets/maps/stage_mecanicas/`, que es su escenario de
referencia. Meterlas todas aquí convertiría el prólogo en un catálogo y
dejaría de ser jugable.

---

## 8. Cómo se regenera

```bash
python tools/generate_stage0_tmx.py
```

El `.tmx` del repositorio **es** la salida de ese script, y una prueba lo
comprueba. Si hay que cambiar el trazado, se cambia el generador; editar el
`.tmx` a mano funciona hasta que alguien ejecute el script.

---

## 🔗 Documentos relacionados

- [[06_TMX_SPEC.md|Especificación TMX]]
- [[30_ASSIGNMENT_01_STAGE_DESIGN.md|Práctica 1: diseño de escenario]]
