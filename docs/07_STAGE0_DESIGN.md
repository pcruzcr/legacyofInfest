---
document_id: "LOI-STAGE0-007"
title: "Legacy of InFest — Diseño del Escenario 0"
aliases: ["Stage 0 Design", "Reference Stage", "Escenario de referencia"]
tags: ["stage0", "reference", "design"]
description: "Escenario de referencia del equipo docente"
source: "docs/07_STAGE0_DESIGN.md"
date_processed: "2026-07-31"
---

# Legacy of InFest — Diseño del Escenario 0

**ID del documento:** LOI-STAGE0-007
**Versión:** 2.0.0
**Estado:** Oficial
**Público:** profesorado, asistentes, estudiantes, asistentes de código

> **AUD-114 — este documento describía un escenario que no existe.**
> La versión 1.0.0 especificaba un mapa de **240 × 14 baldosas (3840 × 224 px)**
> con 27 mensajes, 12 enemigos y 5 checkpoints, todos en coordenadas concretas.
> El mapa que el juego carga mide **100 × 38 (1600 × 608 px)** y no coincidía en
> una sola cifra. De aquí salió el 240 × 14 de `tools/generate_stage0_tmx.py`,
> que llevaba meses listo para borrar el escenario bueno si alguien lo ejecutaba.
>
> Un documento de diseño que nadie comprueba se convierte en ficción, y esta era
> la ficción más cara del repositorio: es lo primero que lee un estudiante que
> quiere entender el motor. Todas las cifras de aquí abajo se **derivan del
> `.tmx`** y `tests/test_stage0_platform_solidity.py` las vuelve a comprobar en
> cada ejecución de la suite.
>
> **AUD-455 (2026-08-13).** §7 citaba cuatro veces `56_FASE_5_ECS_Y_MECANICAS.md`,
> un documento que no existe en `docs/` (verificado por glob). Redirigido a
> `STAGE_CREATION.md`, cuyo bloque generado documenta `Vine`, `Zipline`,
> `RhythmBlock` y `WindZone` con sus propiedades reales.

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
- **Dos soluciones donde se pueda.** El foso se salta *o* se cruza por arriba.
  Un obstáculo con una sola solución es un pasillo con un examen en medio.
- **Modo depuración.** `F1` dibuja cajas de golpe, de daño, conos de visión y
  rectángulos de colisión. Es material didáctico, no un truco.

---

## 2. Trazado

Mapa horizontal de **100 × 38 baldosas** de 16 px = **1600 × 608 px**. El suelo
está en la fila 30 (**y = 480 px**) y el avance es de izquierda a derecha.

```
  x=48      160      288       528      736      992      1184     1472  1552
   │         │        │         │        │        │         │        │     │
 SPAWN ──A──[▮]──B──[walker]──C──[liana]──D──[▮]──E──[foso]──F──[viento]──G──[tirolesa]──SALIDA
                                             llave/puerta   bloques         cofre
```

| Zona | Rango x (px) | Qué enseña |
|---|---|---|
| A | 48 – 220 | moverse, saltar, y el primer obstáculo sólido |
| B | 224 – 390 | el primer enemigo, inevitable |
| C | 400 – 700 | plataformas de un sentido, liana, primer salto exigente |
| D | 720 – 975 | combate variado, llave y puerta cerrada |
| E | 976 – 1150 | foso con dos rutas, bloques rítmicos, zona de daño |
| F | 1152 – 1350 | enemigos a distancia y zona de viento |
| G | 1360 – 1552 | todo junto, tirolesa y cofre |

### 2.1 Tema visual

Corredor de piedra neutro, legible, sin ruido atmosférico que tape lo que se
está demostrando. Tileset `tileset_stage0.png`.

### 2.2 Geometría vertical

- **Suelo:** filas 30–37 (y 480–608), sólido.
- **Muros de cierre:** x = −16 y x = 1600, de 608 px de alto. Quedan fuera del
  área jugable y `level_metrics` los descarta antes de medir repisas (AUD-112).
- **Obstáculos sólidos interiores:** dos, y son lo único contra lo que se choca
  de lado en todo el escenario.

  | x | Alto | Dónde | Para qué |
  |---|---|---|---|
  | 160 | 2 baldosas (32 px) | zona A | se salta desde parado |
  | 736 | 3 baldosas (48 px) | zona D | obliga a aprovechar el impulso; guarda la llave |

  El salto del jugador alcanza **72 px** medidos. Una prueba parametrizada
  conduce al jugador por encima de cada uno: poner cajas sólidas en el camino
  sin comprobar que se superan es como se deja un callejón sin salida en el
  escenario que sirve de ejemplo.

- **Plataformas atravesables** (`Platform`, un solo sentido):

  | x | y | Ancho | Zona |
  |---|---|---|---|
  | 416 | 416 | 96 px | C |
  | 576 | 368 | 96 px | C |
  | 976 | 352 | 144 px | E — la pasarela sobre el foso |
  | 1376 | 336 | 128 px | G |

- **Foso:** x 992 – 1088 (96 px), con `DeathPit` al fondo.

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

### Zona C — plataformas, liana y el primer salto exigente (x 400 – 700)

**Sistemas:** plataformas de un solo sentido, `Vine` con `TrepandoState`,
`Pickup`, enemigo volador con trayectoria senoidal.

- `MessageTrigger_Once` en x = 400: *«Sube. Con X te agarras a la liana.»*
- Plataformas atravesables en (416, 416) y (576, 368).
- `Flying` en x = 480: `flight_mode=sine`, amplitud 32, frecuencia 2,0
  (Unidad III).
- `Vine` en x = 528, 176 px de largo, `ancho_de_agarre=12`.
- `Pickup` «fragmento_1» en (608, 336), sobre la segunda plataforma.

Aquí está el **salto exigente** que el calificador exigía y que el escenario del
profesor no tenía: el desnivel entre las dos plataformas no se supera andando.

**Checkpoint 1:** x = 688.

---

### Zona D — combate variado, llave y puerta (x 720 – 975)

**Sistemas:** cuatro arquetipos de enemigo distintos, `Key`, `LockedDoor`,
obstáculo alto.

- `MessageTrigger_Once` en x = 720: *«La llave abre la puerta del fondo.»*
- Obstáculo sólido de 3 baldosas en x = 736.
- `Key` «llave_prologo» en x = 752, detrás del obstáculo.
- `Charger` en x = 800 (`charge_speed=250`).
- `Archer` en x = 864 (`fire_rate=2`, proyectil a 100 px/s, 2 de daño).
- `Brute` en x = 912, 6 de vida, caja de 100 × 60.
- `LockedDoor` en x = 960, `key_id=llave_prologo`, con mensaje de bloqueo.

La llave está **antes** de la puerta pero detrás del muro: el estudiante ve que
un objeto de inventario y un obstáculo de geometría resuelven cosas distintas.

**Checkpoint 2:** x = 976.

---

### Zona E — el foso, con dos rutas (x 976 – 1150)

**Sistemas:** `DeathPit`, `RhythmBlock`, plataforma de un sentido como pasarela,
`HazardZone`.

- `MessageTrigger_Once` en x = 944: *«Salta el foso, o cruza por encima.»*
- Foso en x 992 – 1088 con `DeathPit` al fondo (y = 576).
- Tres `RhythmBlock` en x 1008, 1040 y 1072, a y = 400:
  `visible_seg=1.8`, `oculto_seg=1.0`, `desfase` 0, 0,6 y 1,2. Aparecen en
  cascada, así que la ruta de arriba **existe pero hay que cronometrarla**.
- Pasarela `Platform` en (976, 352), atravesable desde abajo.
- `HazardZone` en x = 1120, daño 0,25 por tic — el nivel de daño «leve».

Tres formas de pasar: saltar el foso, cronometrar los bloques, o cruzar por la
pasarela. Es el sitio del escenario donde más se nota la diferencia entre
diseñar y poner obstáculos.

---

### Zona F — a distancia, y viento (x 1152 – 1350)

**Sistemas:** `Shooter`, `Caster`, `WindZone` (fase 5), `Pickup`.

- `MessageTrigger_Once` en x = 1152: *«El viento empuja. Espera a que amaine.»*
- `WindZone` en x 1184 – 1344, 160 × 160 px: `fuerza_x=210`, `periodo=3.4`. La
  fuerza es periódica, así que la solución es **esperar**, no insistir.
- `Pickup` «fragmento_2» en x = 1216.
- `Shooter` en x = 1248 y `Caster` en x = 1296, ambos a distancia: el viento
  cambia el problema de puntería.

**Checkpoint 3:** x = 1344.

---

### Zona G — todo junto, tirolesa y cofre (x 1360 – 1552)

**Sistemas:** `Assassin`, `Zipline` con `TirolesaState`, `Chest`, `CameraLock`,
`NextTrigger`, ataque definitivo.

- `MessageTrigger_Once` en x = 1360: *«Combina todo. U es el ataque
  definitivo.»*
- `CameraLock` en x = 1376, 224 px de ancho, `lock_y=true`.
- `Assassin` en x = 1408 y `Walker` en x = 1456.
- Plataforma alta en (1376, 336).
- `Pickup` «fragmento_3» en (1440, 320).
- `Zipline` en (1472, 320): `destino_dx=80`, `destino_dy=128`, 200 px/s.
- `Chest` «reliquia_prologo» en (1488, 320) — la recompensa por subir.
- `NextTrigger` en x = 1552.

---

## 4. Inventario del mapa

Cifras derivadas del `.tmx`; si dejan de cuadrar, la suite avisa.

| | |
|---|---|
| Tamaño | 100 × 38 baldosas (1600 × 608 px) |
| Capas | 8 |
| Objetos en `Objects` | 44 |
| Objetos en `Collision` | 10 |
| Propiedades de mapa | 17 |
| Enemigos | 9, de 8 tipos |
| Mensajes de tutorial | 7 |
| Checkpoints | 4 (ids 0–3) |
| Coleccionables | 5 (3 `Pickup`, 1 `Key`, 1 `Chest`) |
| Focos `Light` | 7 |
| Obstáculos sólidos interiores | 2 |
| Plataformas de un sentido | 4 |

### 4.1 Enemigos

| Tipo | x | Nota |
|---|---|---|
| `Walker` | 288 | 2 de vida, patrulla 80 px |
| `Flying` | 480 | senoidal, amplitud 32, frecuencia 2,0 |
| `Charger` | 800 | embestida a 250 px/s |
| `Archer` | 864 | proyectil a 100 px/s |
| `Brute` | 912 | 6 de vida |
| `Shooter` | 1248 | disparo cada 2 s |
| `Caster` | 1296 | ataque a distancia |
| `Assassin` | 1408 | acercamiento rápido |
| `Walker` | 1456 | 2 de vida |

### 4.2 Checkpoints

| id | x | Contexto |
|---|---|---|
| 0 | 352 | tras el primer enemigo |
| 1 | 688 | tras las plataformas y la liana |
| 2 | 976 | tras el combate y la puerta |
| 3 | 1344 | tras el viento, antes del tramo final |

### 4.3 Propiedades de mapa

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
3. La pantalla funde a negro y **se queda en negro** hasta el corte (AUD-109:
   `FadeAction` retornaba antes de dibujar el velo al completarse, y el fundido
   terminaba con un fotograma de destello justo antes del cambio de escena).
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

El `DeathPit` de la zona E pone la vida a cero directamente, sin pasar por los
niveles de daño ni por la invulnerabilidad. Es instantáneo a propósito: un foso
que quita media vida enseña a caerse dentro.

---

## 7. Lista de sistemas demostrados

| Sistema | Zona | Documento |
|---|---|---|
| Andar, saltar, tiempo del coyote, corte de salto | A | `04_PLAYER_SPEC.md` §4 |
| Colisión horizontal contra sólido | A, D | `06_TMX_SPEC.md` §9 |
| Ataque corto y largo, hitstop | B | `04_PLAYER_SPEC.md` §7 |
| Caja de daño y de golpe | B, C | `04_PLAYER_SPEC.md` §10–11 |
| `Walker`: patrulla, borde, alerta, contacto | B, G | `05_ENEMY_SPEC.md` §3 |
| Invulnerabilidad tras recibir daño | B | `04_PLAYER_SPEC.md` §5.3 |
| Plataforma de un solo sentido | C, E, G | `06_TMX_SPEC.md` §9.2 |
| Vuelo senoidal (Unidad III) | C | `05_ENEMY_SPEC.md` §4 |
| Liana / `TrepandoState` | C | `STAGE_CREATION.md` |
| `Pickup` e inventario | C, F, G | `06_TMX_SPEC.md` §6 |
| `Charger`, `Archer`, `Brute` | D | `05_ENEMY_SPEC.md` §5–7 |
| `Key` y `LockedDoor` | D | `06_TMX_SPEC.md` §6 |
| `DeathPit` | E | `06_TMX_SPEC.md` §9.3 |
| `RhythmBlock` | E | `STAGE_CREATION.md` |
| `HazardZone` y daño leve | E | `04_PLAYER_SPEC.md` §6.1 |
| `Shooter`, `Caster`, proyectiles, `atan2` | F | `05_ENEMY_SPEC.md` §5 |
| `WindZone` | F | `STAGE_CREATION.md` |
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
cuatro (liana, tirolesa, bloques rítmicos, zona de viento). Las otras siete
—agua y nado, plataformas móviles, plataformas hundibles, zonas de fricción,
tiempo bala, scroll forzado, sigilo con cono de visión— viven en
`assets/maps/stage_mecanicas/`, que es su escenario de referencia. Meterlas
todas aquí convertiría el prólogo en un catálogo y dejaría de ser jugable.

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
