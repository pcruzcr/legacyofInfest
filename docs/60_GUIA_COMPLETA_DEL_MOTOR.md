---
document_id: "LOI-GUIDE-ENGINE"
title: "Guía completa del motor — todo lo que se puede poner en un nivel"
aliases: ["Guía del motor", "Manual del diseñador"]
tags: ["guia", "motor", "framework", "tmx", "nivel"]
source: "docs/60_GUIA_COMPLETA_DEL_MOTOR.md"
date_processed: "2026-07-31"
---

# Guía completa del motor — todo lo que se puede poner en un nivel

**Versión:** 1.0.0 · **Fecha:** 31 de julio de 2026
**Público:** cualquiera que vaya a diseñar un escenario, sepa o no programar.

> **Cómo se escribió esta guía, y por qué importa.**
> Todas las cifras, listas y nombres de propiedad de este documento están
> **leídos del código**, no copiados de otra documentación. Hoy mismo,
> `07_STAGE0_DESIGN.md` resultó describir un escenario de 240 × 14 baldosas
> con 27 mensajes y 12 enemigos que **no existe** —el mapa real mide 100 × 38—
> y de esa ficción salió un generador que habría borrado el escenario bueno.
> Cuando esta guía y el motor discrepen, el motor tiene razón; avísame y la
> corrijo. Los comandos de verificación están en la §16.

---

## Índice

1. [El bucle: qué pasa en un fotograma](#1)
2. [Anatomía de un escenario TMX](#2)
3. [Propiedades del mapa — las 17](#3)
4. [Los 63 tipos de objeto, uno por uno](#4)
5. [El jugador: 26 estados y qué los provoca](#5)
6. [Enemigos: 30 tipos y 13 estados](#6)
7. [Jefes](#7)
8. [Iluminación, post-procesado y VFX](#8)
9. [Clima, ciclo día/noche y estaciones](#9)
10. [Audio](#10)
11. [Inventario, coleccionables y llaves](#11)
12. [Bestiario y logros](#12)
13. [Diálogo, cutscenes y narrativa](#13)
14. [Escenas, progresión y guardado](#14)
15. [Registrar tu escenario en el juego](#15)
16. [Herramientas: previsualizar, validar, calificar](#16)
17. [Recetas: cómo se construye cada cosa](#17)
18. [Errores frecuentes, y qué dice el motor cuando ocurren](#18)

---

<a id="1"></a>
## 1. El bucle: qué pasa en un fotograma

Resolución interna fija de **800 × 600** a **60 FPS**, escalada a la ventana.
Gravedad **800 px/s²**. El orden de cada fotograma es:

```
entrada  →  escena.update(dt)  →  escena.draw(pantalla)  →  bus de eventos
                 │
                 ├── cinemática (si hay una, retorna aquí: el juego no corre)
                 ├── reloj de mundo (hora, estación)
                 ├── sistemas ECS (zonas, plataformas, agarres, sigilo)
                 ├── jugador: estado → física → colisión
                 ├── enemigos: IA → física → colisión
                 ├── disparadores: mensajes, checkpoints, cofres, puertas
                 └── VFX: partículas, estelas, clima, luz
```

Dos detalles que se notan al diseñar:

* **`MAX_FRAME_TIME = 0.05`.** Si un fotograma tarda más de 50 ms, `dt` se
  recorta. Sin ese tope, un tirón puede teletransportar al jugador a través de
  una pared. Significa que en un ordenador lento el juego va **lento**, no
  **roto**.
* **`Clock.time_scale`.** Un solo número escala el tiempo de todo el juego. De
  ahí salen el *hit-stop* al golpear y el tiempo bala.

---

<a id="2"></a>
## 2. Anatomía de un escenario TMX

Se dibuja en **Tiled**. Ajustes obligatorios:

| Ajuste | Valor |
|---|---|
| Orientación | Ortogonal |
| Tamaño de baldosa | 16 × 16 px |
| Orden de dibujo | Right-down |
| Infinito | **No** |

### Las ocho capas, de abajo arriba

| # | Nombre | Tipo | Para qué |
|---|---|---|---|
| 1 | `BG_Far` | baldosas | fondo lejano, parallax lento |
| 2 | `BG_Mid` | baldosas | fondo medio |
| 3 | `BG_Near` | baldosas | fondo cercano, parallax rápido |
| 4 | `Terrain` | baldosas | el terreno que se ve |
| 5 | `Terrain_Detail` | baldosas | decoración sin colisión |
| 6 | `Objects` | objetos | entidades, disparadores, luces |
| 7 | `Collision` | objetos | **la colisión de verdad** |
| 8 | `FG_Overlay` | baldosas | primer plano, se dibuja sobre todo |

**El error número uno.** `Terrain` es lo que se **ve**; `Collision` es lo que
se **toca**. Son independientes. Un suelo dibujado sin su rectángulo en
`Collision` deja caer al jugador al vacío, y un rectángulo sin baldosas es un
muro invisible. Píntalos siempre a la vez.

En `Collision` sólo hay dos tipos:

| `type` | Comportamiento |
|---|---|
| vacío o `Solid` | sólido por los cuatro lados |
| `Platform` | atravesable desde abajo; sólo se aterriza encima |

### El tileset

Declara la hoja con **su tamaño real**. Si dices que tu PNG de 1024 × 1024
mide 128 × 128, los índices de baldosa apuntan a otra casilla y tu nivel se
dibuja con las baldosas equivocadas —normalmente casi negras—. Pasó en este
repositorio esta semana y ni el calificador ni el validador lo vieron; ahora
`tests/test_tmx_validator.py` lo comprueba en los 16 mapas.

Tiled acepta la hoja incrustada en el `.tmx` o en un `.tsx` aparte. **Las dos
son válidas** y el calificador entiende ambas.

---

<a id="3"></a>
## 3. Propiedades del mapa — las 17

Se ponen en *Map → Map properties*. Sólo las tres primeras son obligatorias;
sin ellas el nivel no valida y pierde 10 puntos de rúbrica.

### Obligatorias

| Propiedad | Tipo | Ejemplo |
|---|---|---|
| `stage_id` | string | `stage1` |
| `stage_name` | string | `LAS AULAS` |
| `bgm_track` | string | `bgm_stage1` |

### Del escenario

| Propiedad | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `author` | string | — | tu nombre; el calificador lo pide |
| `time_limit` | int | `0` | segundos; `0` = sin límite |
| `gravity_multiplier` | float | `1.0` | `0.5` = lunar, `1.5` = pesado |
| `zone` | int | `0` | zona del mundo; decide paleta y bestiario por defecto |
| `vista` | string | `lateral` | `lateral` o `cenital`. Cenital apaga la gravedad, da movimiento en dos ejes y **ignora las plataformas de un solo sentido** — desde arriba son muros invisibles |
| `background_zone` | string | — | carga `assets/backgrounds/bg_<zona>_{far,mid,near}.png` |

### De atmósfera

| Propiedad | Tipo | Rango | Qué hace |
|---|---|---|---|
| `ambient_light` | float | 0 – 1 | luz de fondo. **1 = pleno día y los focos no se notan**; 0 = negro |
| `bloom` | float | 0 – 1 | halo alrededor de lo brillante |
| `vignette` | float | 0 – 0.6 | oscurece las esquinas |
| `climate` | string | `clear` `rain` `snow` `fog` `storm` | precipitación y tinte |
| `ambient_fx` | string | `dust` `leaves` `embers` `spores` `ash` `none` | partículas flotantes |
| `ambient_fx_rate` | float | 0 – 120 | partículas por segundo; 10–20 se nota sin saturar |
| `start_hour` | string o float | 0 – 24 | `dawn` `morning` `noon` `afternoon` `dusk` `night` `midnight`, `18.5` o `18:30` |
| `day_length` | float | 0 – 36000 | segundos reales de un ciclo completo. **`0` congela la hora** |
| `season` | string | `spring` `summer` `autumn` `winter` | tiñe la paleta y sugiere clima |

### Efectos opcionales

| Propiedad | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `fog_of_war` | float | `0` | radio de visión en píxeles. `0` = apagado. Con `220` el jugador sólo ve su entorno |
| `water_effect` | bool | `false` | ondulación y refracción sobre las `WaterZone` |

Los valores fuera de rango se **recortan**, no se rechazan: `bloom = 5`
significa «mucho». Un valor mal escrito —`leafs` en vez de `leaves`— avisa por
consola con la lista de valores válidos y usa el de la zona. Si no ves un
efecto, mira la consola antes que el código.

---

<a id="4"></a>
## 4. Los 63 tipos de objeto, uno por uno

El motor acepta **63 tipos** en la capa `Objects`: 31 integrados del framework
y 30 enemigos del registro, más `Solid` y `Platform` en `Collision`. Todos los
números se convierten a `float` automáticamente.

> Un objeto **punto** (ancho y alto 0) recibe el tamaño de una baldosa, porque
> un rectángulo de área cero sería imposible de tocar.

### 4.1 Obligatorios y de recorrido

#### `PlayerSpawn` — exactamente uno

Sin propiedades. **La Y es la posición de los pies**: el motor resta 32 px.
Dos `PlayerSpawn` es un error de carga, no un aviso.

#### `NextTrigger` — la salida

Sin propiedades. Al tocarlo estando en el suelo se completa el escenario.

#### `Checkpoint`

| Propiedad | Tipo | Qué hace |
|---|---|---|
| `checkpoint_id` | int | orden, empezando en 0 |

La rúbrica pide checkpoints **repartidos**. Más de 600 px entre uno y otro en
un tramo con peligro se penaliza, y con razón: morir ahí cuesta demasiado
camino rehecho.

#### `CameraLock`

| Propiedad | Tipo | Por defecto |
|---|---|---|
| `lock_x` | bool | `false` |
| `lock_y` | bool | `false` |

Fija un eje de la cámara mientras el jugador está dentro. Con `lock_y` la
cámara deja de seguir los saltos, que es lo que quieres en un tramo de
plataformas verticales.

### 4.2 Mensajes y eventos

#### `MessageTrigger` / `MessageTrigger_Once`

| Propiedad | Tipo | Qué hace |
|---|---|---|
| `text` | string | el texto; `\n` parte la línea |

`_Once` aparece una sola vez por partida. Úsalo para tutoriales; el otro, para
avisos que conviene repetir.

#### `EventTrigger`

| Propiedad | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `evento` | string | el nombre del objeto | qué se emite al bus |
| `automatico` | bool | `true` | `false` = hay que pulsar el botón |
| `una_vez` | bool | `true` | se desactiva tras dispararse |
| `key_id` | string | — | exige tener ese objeto en el inventario |

Sin `evento` ni nombre, se ignora con un aviso: emitir la cadena vacía no
serviría de nada.

### 4.3 Peligros

| Tipo | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `HazardZone` | `damage` | `0.25` | daño por tic mientras estés dentro |
| `DeathPit` | — | — | muerte instantánea, sin pasar por niveles de daño ni invulnerabilidad |
| `LaserZone` | `dano` | `99` | letal, intermitente |
| | `encendido` | `1.0` | segundos activo |
| | `apagado` | `1.0` | segundos apagado |
| | `desfase` | `0.0` | desplaza el ciclo; con tres láseres a 0, 0.5 y 1.0 se hace una cortina |
| `ShockwaveZone` | igual que `LaserZone` | | mismo componente, otro nombre para que el mapa se lea |

Un `DeathPit` mata del todo **a propósito**. Un foso que quita media vida
enseña a caerse dentro.

### 4.4 Zonas con efecto físico

| Tipo | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `WindZone` | `fuerza_x` | `0` | empuje horizontal en px/s² |
| | `fuerza_y` | `0` | empuje vertical |
| | `periodo` | `0` | segundos de ciclo. **`0` = constante**; con `3.4` amaina y vuelve, y la solución pasa a ser esperar |
| `FrictionZone` | `multiplicador` | `1.0` | `0.2` = hielo, `2.0` = barro |
| | `arrastre` | `0` | px/s que te lleva |
| `Conveyor` | igual que `FrictionZone` | `arrastre = 60` | alias con arrastre por defecto: una cinta sin arrastre no es una cinta |
| `WaterZone` | `corriente_x` | `0` | corriente horizontal |
| | `corriente_y` | `0` | corriente vertical |

Dentro de una `WaterZone` el jugador entra en `SWIMMING`: la gravedad baja, se
nada, y hay oxígeno. Combínalo con `water_effect = true` en el mapa para que
además se vea.

### 4.5 Plataformas

| Tipo | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `MovingPlatform` | `destino_dx` | `0` | desplazamiento, **no** coordenada absoluta |
| | `destino_dy` | `0` | |
| | `velocidad` | `40` | px/s |
| | `espera` | `0.5` | segundos parada en cada extremo |
| | `atravesable` | `false` | `true` = se puede subir desde abajo |
| `SinkingPlatform` | `retraso` | `0.4` | segundos antes de ceder |
| | `velocidad_caida` | `90` | px/s |
| | `reaparece_en` | `3.0` | segundos hasta volver |
| `RhythmBlock` | `visible_seg` | `1.0` | segundos presente |
| | `oculto_seg` | `1.0` | segundos ausente |
| | `desfase` | `0.0` | desplaza el ciclo |

El destino va en **desplazamiento** para que mover la plataforma en Tiled no
te obligue a recalcular su destino a mano.

> **Trampa de Tiled:** las propiedades del bloque rítmico se llaman
> `visible_seg` y `oculto_seg`, no `visible` y `oculto`. **`visible` es un
> nombre reservado en Tiled** y pytmx rechaza el mapa entero con «Reserved
> names and duplicate names are not allowed». Lo descubrimos cargando el
> escenario de mecánicas por primera vez.

### 4.5 bis  Resortes e interruptores (AUD-131 / AUD-132)

| Tipo | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `Spring` | `impulso` | `-520` | velocidad vertical impuesta al rebotar. **Se impone, no se suma**: la altura del rebote es una constante del nivel, no depende de desde dónde caigas |
| | `rearme` | `0.15` | segundos hasta poder volver a dispararse; evita el doble rebote |

Sólo rebota quien **viene cayendo**. Tocarlo de lado o desde abajo no hace nada,
que es lo que el jugador espera al verlo.

**El interruptor que abre una puerta** ya no necesita Python. En la puerta:

| Propiedad | Qué hace |
|---|---|
| `abre_con` | nombre del evento que la abre, sin llave |
| `cierra_en` | segundos hasta cerrarse sola. `0` = para siempre |

Y en el `EventTrigger`, `evento` con ese mismo nombre. Con eso queda el circuito
completo: interruptor → bus → puerta.

`Disparador` llevaba desde F4.1 emitiendo su evento **sin que nadie
escuchara**: se podía poner un interruptor en Tiled, verlo funcionar en el
registro, y no conseguir que abriera nada. Faltaba el receptor.

Una puerta cronometrada **nunca se cierra sobre el jugador**: si está dentro,
el temporizador se prorroga hasta que salga.

### 4.6 Agarres: liana y tirolesa

| Tipo | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `Vine` | `velocidad` | `70` | px/s al trepar |
| | `ancho_de_agarre` | `10` | margen lateral para engancharse |
| `Zipline` | `destino_dx` | `96` | a dónde llega el cable |
| | `destino_dy` | `64` | |
| | `velocidad` | `190` | px/s |
| | `radio_de_enganche` | `14` | margen para agarrarse |
| | `solo_de_bajada` | `true` | `false` permite subir por ella |

La liana se dibuja **alta y estrecha**; la tirolesa es un punto de enganche y
el cable se deduce del desplazamiento. El jugador se agarra con la acción
`GRAB` y entra en `CLIMBING` o `ZIPLINE`.

### 4.7 Objetos e inventario

| Tipo | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `Pickup` | `item_id` | el nombre del objeto | qué entra al inventario |
| | `automatico` | `true` | `false` = hay que pulsar el botón |
| | `mensaje` | — | texto al cogerlo |
| `Key` | igual que `Pickup` | | alias: se lee mejor en Tiled |
| `Chest` | `contenido` | — | qué entrega |
| | `key_id` | — | llave necesaria para abrirlo |
| | `mensaje` | — | |
| | `evento` | — | evento al abrirse |
| `LockedDoor` | `key_id` | — | llave que abre |
| | `consume_llave` | `false` | `true` = la gasta |
| | `mensaje` | — | qué se dice si está cerrada |
| | `evento` | — | |
| `Door` / `Cage` | igual que `LockedDoor` | | `Cage` se presenta como jaula |

Un `Pickup` sin `item_id` **y** sin nombre se ignora con un aviso. Una puerta
dibujada como punto también: una puerta sin área no bloquea nada.

### 4.8 Sigilo

| Tipo | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `Guard` | `mira_x` | `1.0` | dirección del cono |
| | `mira_y` | `0.0` | |
| | `alcance` | `160` | px |
| | `semiangulo` | `30` | grados a cada lado |
| | `barrido` | `0` | grados de vaivén. `0` = cono fijo |
| | `velocidad_barrido` | `45` | grados por segundo |
| `Stalker` | `velocidad` | `55` | px/s; persigue sin descanso |
| | `distancia_retirada` | `480` | px a los que abandona |
| | `reaparicion` | `6.0` | segundos hasta volver |

El `Stalker` es **invulnerable a propósito**: no se resuelve peleando. Si tu
nivel no ofrece una salida —un escondite, una puerta, un tramo de carrera—, no
es tensión, es un callejón.

### 4.9 Auxiliares

| Tipo | Propiedad | Qué hace |
|---|---|---|
| `Waypoint` | `owner_id` | el **nombre** de la entidad voladora que lo usa |
| | `waypoint_index` | orden, desde 0 |

Para trayectorias Bézier de enemigos voladores.

### 4.10 `Light`

El punto de luz es el **centro** del rectángulo, así que puedes encuadrar una
antorcha y la luz sale de ella.

| Propiedad | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `radius` | float | `80` | alcance en px |
| `color` | string | `warm` | `warm` `cold` `fire` `toxic` `blood` `white` o `#rrggbb` |
| `intensity` | float | `0.8` | 0 a 1 |
| `flicker` | bool | `false` | parpadeo de antorcha |
| `flicker_speed` | float | `4.0` | oscilaciones por segundo |
| `flicker_amount` | float | `0.15` | amplitud, 0 a 1 |

**Los focos no son decoración si tu mapa tiene `day_length`.** Al hacerse de
noche el ambiente cae a un suelo de 0,45 y lo único que se ve es lo que tú
hayas iluminado. Stage 0 llegó a tener sólo el **24 %** de la pantalla por
encima del umbral de legibilidad a medianoche antes de que lo corrigiéramos.
Prueba tu nivel con `--hora 23`.

---

<a id="5"></a>
## 5. El jugador: 26 estados y qué los provoca

### Controles por defecto

| Acción | Teclas |
|---|---|
| Moverse | flechas / `WASD` |
| Saltar | `Espacio`, `↑`, `W` |
| Agacharse | `↓`, `S` |
| Ataque corto | `Z`, `J` |
| Ataque largo | `X`, `K` |
| Ataque a distancia | `F`, `V` |
| Dash | `Shift`, `Alt` |
| Agarrar / liana / tirolesa | `G`, `C` |
| Bestiario | `Tab` |
| Silenciar | `M` |
| Pausa | `Esc`, `P` |
| Depuración | `F1` |
| Teoría por unidad | `F2`–`F10` |

Se pueden reasignar desde la escena de controles. Hay mando: A salta, B ataque
corto, X ataque largo, Y agacharse, LB agarrar.

### Números del jugador

| Constante | Valor |
|---|---|
| Vida máxima | 5,0 corazones |
| Velocidad al andar | 90 px/s |
| Fuerza de salto | −380 px/s |
| Caída máxima | 500 px/s |
| Tiempo del coyote | 6 fotogramas |
| Velocidad de dash | 200 px/s |
| Dash en el aire | 1 por salto |
| Saltos en el aire | 1 |
| Ataque corto | 0,15 s |
| Ataque largo | 0,40 s |
| Ventana de combo | 0,5 s |
| Multiplicador de combo | ×1,0 → ×1,5 → ×2,0 |
| **Altura de salto medida** | **72 px** |

Ese último número es el que necesitas al diseñar: **un obstáculo de más de 4
baldosas no se supera saltando**. La rúbrica marca los repechos imposibles, y
es la penalización más frecuente en las entregas.

### Los 26 estados

| Grupo | Estados |
|---|---|
| Suelo | `IDLE` `WALKING` `CROUCHING` `SLIDE` |
| Aire | `JUMPING` `FALLING` `DASHING` `WALL_SLIDE` `LEDGE_GRAB` `AIR_CHASE` |
| Ataque | `SHORT_ATTACK` `LONG_ATTACK` `CHARGE_ATTACK` `CHARGE_RELEASE` `DASH_ATTACK` `AERIAL_ATTACK` `AERIAL_SLAM` `ULTIMATE` |
| Defensa | `PARRY` |
| Agarre | `GRAB` `THROW` `CLIMBING` `ZIPLINE` |
| Medio | `SWIMMING` |
| Daño | `HURT` `DYING` |

Como diseñador no invocas estados: colocas el objeto y el estado ocurre.
`CLIMBING` necesita una `Vine`, `ZIPLINE` una `Zipline`, `SWIMMING` una
`WaterZone`, `WALL_SLIDE` un muro vertical de al menos dos baldosas.

**`ULTIMATE`** se carga golpeando y se lanza con `U`. Si tu nivel no da
enemigos suficientes antes del tramo final, el jugador nunca lo verá.

---

<a id="6"></a>
## 6. Enemigos: 30 tipos y 13 estados

### Los ocho arquetipos

Son la base; los 22 restantes son variantes temáticas con otro aspecto y otros
números.

| Tipo | Cómo se comporta | Propiedades |
|---|---|---|
| `Walker` | patrulla y detecta bordes | `patrol_length` `patrol_speed` `alert_speed` `facing` `damage_on_contact` `max_health` |
| `Flying` | vuela por una curva | `flight_mode` (`sine`/`bezier`) `flight_speed` `sine_amplitude` `sine_frequency` |
| `Shooter` | dispara a distancia | `fire_rate` `projectile_speed` `projectile_damage` `patrol_length` |
| `Archer` | dispara en arco | `fire_rate` `projectile_speed` `projectile_damage` |
| `Charger` | embiste en línea recta | `charge_speed` `patrol_speed` `alert_speed` |
| `Brute` | lento, mucha vida | `max_health` `patrol_speed` `alert_speed` |
| `Caster` | ataque a distancia con conjuro | `fire_rate` `projectile_damage` |
| `Assassin` | se acerca rápido | `patrol_speed` `alert_speed` |

### Las 22 variantes del bestiario

```
Walker:   WalkerGuardia  WalkerEstudiante  WalkerGarza  WalkerPalom
          WalkerInsect   WalkerRaton       WalkerTerciopelo
          WalkerSerpientePequena
Flying:   FlyingBird     FlyingBoa         FlyingHalcon  FlyingCucaracha
          FlyingNotebook FlyingTerciovolador
Shooter:  ShooterFrog    ShooterBuitre     ShooterQuetzal  ShooterCocinero
          ShooterTiza    ShooterSerpienteArbol  ShooterVenomoLargo
Jefe:     BossVenado
```

**Quince de estos tipos no aparecen en ningún mapa del curso.** Si buscas
enemigos con personalidad para tu zona, empieza por ahí.

### Los 13 estados de enemigo

`IDLE` → `PATROL` → `SEARCH` → `ALERT` → `CHASE` → `TELEGRAPHING` → `FIRING`
→ `RECOVER`, más `RETREAT`, `STUNNED`, `HURT`, `LAUNCHED`, `DYING`.

El que importa al diseñar es **`TELEGRAPHING`**: el aviso antes del golpe. Un
enemigo sin telegrafiado no es difícil, es injusto, y el jugador culpa al
mando. Los arquetipos ya lo traen; si escribes uno propio, respétalo.

### Dos avisos con cicatriz

* **Ponles `patrol_length`.** Sin él, varios arquetipos —el `Shooter` entre
  ellos— se quedan clavados. Un enemigo a distancia inmóvil se resuelve andando
  dos pasos a un lado.
* **`enemigo.velocity` es siempre (0, 0).** Todas las entidades tienen ese
  atributo desde la fase 5, pero los enemigos mueven `position` directamente y
  nunca lo actualizan. Si necesitas su velocidad, dedúcela del desplazamiento
  entre fotogramas. Antes esto lanzaba `AttributeError` y te enterabas; ahora
  devuelve un cero silencioso, que es peor.

---

<a id="7"></a>
## 7. Jefes

Un jefe hereda de `BossBase` y trae de fábrica:

* **Fases** con umbrales de vida, transición animada y evento
  `BOSS_PHASE_CHANGED`. Cada fase puede cambiar el tinte de la arena.
* **Telegrafiado** con `attack_timing` y `telegraph_progress` (0 → 1), para
  dibujar la barra de aviso.
* **Puntos débiles**: `weak_point_at(rect)` y `apply_hit_at()`, para que
  golpear la cabeza valga más que golpear la pata.
* **Parry**: `recibir_parry()` devuelve el aturdimiento y emite
  `BOSS_ATTACK` con patrón `PARRIED`.
* **Invulnerabilidad de fase** (`fase_invulnerable`) y **escala** por fase.
* **Invocaciones**: `on_summon(especie, cantidad)` y `take_summons()`.
* **Teletransporte** con `teletransportar(x, y)`, ya corregido para que la
  posición y el rectángulo no se contradigan.
* **Límites de arena**: `set_arena_bounds()` y `clamp_to_arena()`.

### La arena

Una arena de jefe **no se califica con la rúbrica de niveles**. Esa rúbrica
mide si se llega andando a la salida, y en una arena la salida se abre al
derrotar al jefe: pasarla por ahí da 61,5 % a la arena de referencia del propio
juego, que está bien hecha. El calificador lo avisa por escrito.

### Bullet hell

Para patrones densos hay un enjambre en NumPy en vez de un objeto por bala.
Medido: **2000 balas, 12,94 ms con objetos frente a 0,072 ms con el enjambre**
—180 veces—. A partir de unos cientos de proyectiles es la única opción que
cabe en el presupuesto de fotograma.

---

<a id="8"></a>
## 8. Iluminación, post-procesado y VFX

| Sistema | Cómo se enciende |
|---|---|
| Iluminación | `ambient_light` + objetos `Light` |
| Bloom | `bloom` |
| Viñeta | `vignette` |
| Clima | `climate` |
| Partículas de aire | `ambient_fx` + `ambient_fx_rate` |
| Niebla de guerra | `fog_of_war` (radio en px) |
| Efecto de agua | `water_effect = true` + una `WaterZone` |
| Estelas | automáticas: dash del jugador y ataques rápidos |
| Números de daño | automáticos |
| Efectos de impacto | automáticos |

**Las estelas de enemigo tienen umbral de velocidad.** Sólo aparecen por
encima de él, para que la estela signifique «ataque rápido» y no «hay alguien
ahí». Un enemigo en patrulla normal no deja ninguna, y eso es deliberado.

---

<a id="9"></a>
## 9. Clima, ciclo día/noche y estaciones

Los tres se apilan, en este orden:

```
ambient_light  ×  hora del día  ×  estación  +  clima  =  lo que se ve
```

* **`climate`** pone precipitación y tinte. `storm` añade viento lateral.
* **`start_hour` + `day_length`** mueven la hora. `day_length = 0` **congela**
  el reloj, que es lo que quiere un combate: la luz no debe cambiar a mitad de
  una pelea. Stage 0 usa 420 (siete minutos).
* **`season`** tiñe la paleta y **sugiere** clima y partículas si no los
  declaraste. Nunca sobrescribe lo que escribas: `climate = fog` en un mapa de
  otoño sigue siendo niebla.

Hay un **suelo de luz** (`StageScene.MIN_AMBIENTE`, 0,45) por debajo del cual
la noche no baja, porque una noche en la que no se ven los enemigos es un
defecto y no una decisión artística. Aun así, el suelo solo no basta: hace
falta que ilumines. Compruébalo con `preview_tmx.py --hora 23`.

---

<a id="10"></a>
## 10. Audio

| Qué | Cómo |
|---|---|
| Música del nivel | `bgm_track` en el mapa |
| Efectos | `play_sfx(nombre)` desde el banco |
| Efectos con panorámica | `play_sfx_at(nombre, x_mundo)` — suena a la izquierda o a la derecha según dónde ocurra |
| Ambiente en bucle | `play_ambient(ruta)` |
| Cambio de ambiente | `crossfade_ambient(ruta, duracion)` |
| Golpe musical | `play_stinger(nombre)` |

Volúmenes de música y efectos separados, silencio con `M`. **Si falta un
fichero de audio, el juego sigue**: se registra el aviso y se calla ese sonido.
Un nivel no se cae por un `.ogg` que no subiste, pero mira la consola.

---

<a id="11"></a>
## 11. Inventario, coleccionables y llaves

Seis objetos definidos, con efecto real sobre el jugador:

| `item_id` | Nombre | Efecto |
|---|---|---|
| `heart_vessel` | Heart Vessel | +1 vida máxima |
| `hollow_eye` | Hollow Eye | +0,3 de daño |
| `ancients_rib` | Ancient's Rib | +2 vida máxima |
| `swift_feather` | Swift Feather | +10 % de velocidad |
| `thorn_ring` | Thorn Ring | +0,5 de daño |
| `sunken_crown` | Sunken Crown | +3 vida máxima, +0,8 de daño |

Puedes inventar tus propios `item_id` para llaves y coleccionables narrativos:
si no está en la tabla, entra al inventario sin bonificación, que es
exactamente lo que quieres para una llave.

El circuito de puerta y llave es: `Key` con `key_id` → `LockedDoor` con el
mismo `key_id`. Con `consume_llave = true` la puerta se la queda.

**El calificador cuenta `Pickup`, `Key` y `Chest` como coleccionables**, y pide
tres para la casilla completa.

---

<a id="12"></a>
## 12. Bestiario y logros

El **bestiario** (`Tab`) se rellena solo: registra encuentros, muertes y veces
que te ha golpeado cada especie. Cada entrada admite nombre, descripción,
*lore*, botín, vida y daño. Es el sitio donde poner la ficción de tu zona.

Los **diez logros**:

| id | Qué pide |
|---|---|
| `first_blood` | derrotar al primer enemigo |
| `exterminator` | 50 enemigos |
| `untouchable` | terminar un escenario sin recibir daño |
| `parry_master` | 10 parries |
| `air_assault` | combo aéreo de 3 golpes |
| `speed_demon` | terminar un escenario en menos de 60 s |
| `collector` | 5 checkpoints en una partida |
| `survivor` | sobrevivir con 0,5 de vida o menos |
| `combo_king` | combo de 10 |
| `explorer` | completar los 15 escenarios |

Dos son tuyos como diseñador: `speed_demon` exige que tu nivel se pueda
terminar en un minuto por una ruta rápida, y `collector` que tenga cinco
checkpoints.

---

<a id="13"></a>
## 13. Diálogo, cutscenes y narrativa

El **sistema de diálogo** dibuja un cuadro con retrato, nombre y texto por
letras, y encadena intervenciones. Se lanza desde un `EventTrigger` o desde el
código del escenario.

El **sistema de cutscenes** encadena acciones: mover la cámara, esperar,
fundir, mostrar texto, emitir un evento. Mientras hay una cutscene,
`StageScene.update` **retorna**: el juego no se sigue jugando por debajo.

> Un fundido a negro termina **opaco**. Hasta esta semana `FadeAction`
> retornaba antes de dibujar el velo al completarse, y el fundido acababa
> desfundido: un fotograma de destello justo antes del corte, exactamente
> donde no se quiere.

---

<a id="14"></a>
## 14. Escenas, progresión y guardado

Hay **34 escenas** más los escenarios jugables, todas con prueba de humo
—se arrancan, se actualizan y se dibujan de verdad, no sólo se importan—.
Las que te tocan:

| Escena | Para qué |
|---|---|
| `StageScene` | de la que hereda tu nivel |
| `WorldMapScene` | mapa del mundo, decide a dónde se va |
| `GameOverScene` | continuar desde checkpoint o salir |
| `StageErrorScene` | tu mapa no cargó, y aquí se dice **por qué** |
| `InventoryScene` `BestiaryScene` `AchievementScene` | menús del jugador |
| `TutorialScene` `StoryScene` `UnitTheoryScene` | material didáctico |
| Laboratorios y demos | una por unidad del temario |

La **progresión** emite `STAGE_COMPLETE` al final del nivel; el mapa del mundo
lo escucha y desbloquea. El **guardado** conserva progreso, inventario,
bestiario, logros y ajustes. Un guardado corrupto **falla de forma ruidosa**:
antes se cargaba a medias y el jugador perdía la partida sin enterarse.

---

<a id="15"></a>
## 15. Registrar tu escenario en el juego

**1.** El mapa en `assets/maps/mi_nivel/mi_nivel.tmx`.

**2.** La clase en `src/stages/mi_nivel/mi_nivel.py`:

```python
from pathlib import Path
from typing import TYPE_CHECKING

from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class MiNivel(StageScene):
    STAGE_ID = "mi_nivel"
    STAGE_NAME = "EL NOMBRE QUE SALE EN PANTALLA"
    ZONE = 1                      # tiene que coincidir con `zone` del TMX

    def __init__(self, context: "GameContext") -> None:
        super().__init__(context, Path("assets/maps/mi_nivel/mi_nivel.tmx"))
```

**3.** Si registras enemigos propios, hazlo **al nivel del módulo**, no dentro
de una función. Dentro de una función funciona al jugar, pero el
previsualizador y las herramientas que abren el mapa suelto no pueden
construir esos objetos, y tu nivel se ve incompleto en la revisión.

**4.** `ZONE` en el código y `zone` en el TMX tienen que decir lo mismo. Una
entrega de este curso decía `ZONE = 3` en el código y estaba instalada en la
ranura 2-2; se descubrió al jugarla.

---

<a id="16"></a>
## 16. Herramientas: previsualizar, validar, calificar

```bash
# Ver el mapa entero con la luz aplicada, sin lanzar el juego
python scripts/preview_tmx.py assets/maps/mi_nivel/mi_nivel.tmx
python scripts/preview_tmx.py mi_nivel.tmx --hora 23        # ¿se ve de noche?
python scripts/preview_tmx.py mi_nivel.tmx --sin-luz        # sólo geometría
python scripts/preview_tmx.py mi_nivel.tmx --con-etiquetas --salida vista.png

# ¿Carga? ¿Le falta algo obligatorio?
python scripts/validate_tmx.py

# ¿Qué nota saca?
python scripts/grade_stage.py assets/maps/mi_nivel/mi_nivel.tmx

# ¿Qué tipos de objeto existen y ninguno usa?
python scripts/check_tmx_coverage.py
```

El previsualizador imprime al final un resumen: focos, entidades, checkpoints,
clima, estación. **Si algo sale en cero y no debería, ahí lo ves** — es la
forma más barata de cazar la capa que se te olvidó.

### La rúbrica, sobre 130

| Casilla | Puntos | Qué mide |
|---|---|---|
| `design_completable` | 12 | se llega andando del spawn a la salida |
| `collectibles` | 10 | ≥ 3 `Pickup`/`Key`/`Chest` |
| `design_geometry` | 10 | sin saltos imposibles ni zonas aisladas |
| `enemies_placed` | 10 | hay enemigos |
| `enemies_valid_types` | 10 | y son de tipos que existen |
| `player_spawn` | 10 | exactamente uno |
| `required_layers` | 10 | están las capas |
| `metadata` | 10 | `stage_id`, `stage_name`, `bgm_track` |
| `design_pacing` | 8 | checkpoints repartidos y **al menos un salto exigente** |
| `file_parses` | 5 | el TMX es válido |
| `map_bounds_reasonable` | 5 | tamaño sensato |
| `tileset_valid` | 5 | el tileset existe |
| `time_limit_reasonable` | 5 | el límite tiene sentido |

Stage 0 saca **130/130** y su TMX está en el repositorio: es el ejemplo
resuelto de todas estas casillas.

---

<a id="17"></a>
## 17. Recetas

**Un obstáculo que se salta.** Rectángulo `Solid` en `Collision` de 1 baldosa
de ancho y 2–3 de alto, y las baldosas correspondientes en `Terrain`. Más de 4
baldosas es un muro, no un obstáculo.

**Un foso con dos soluciones.** Hueco en el terreno + `DeathPit` al fondo +
una `Platform` por encima que lo cruce. Se salta o se rodea. Dos soluciones
para el mismo obstáculo es lo que separa un nivel de un pasillo.

**Un tramo cronometrado.** Tres `RhythmBlock` con `desfase` 0, 0.6 y 1.2 sobre
el foso. La ruta de arriba existe, pero hay que leerla.

**Una habitación de sigilo.** Dos `Guard` con conos cruzados (`barrido = 60`)
+ un `Stalker` + una `LockedDoor` con su `Key` detrás de uno de los conos.
Deja **siempre** una salida que no sea pelear.

**Una zona de nado.** `WaterZone` con `corriente_x` + `water_effect = true` en
el mapa. La corriente convierte el nado en una decisión de ruta.

**Un salto exigente** (lo que pide `design_pacing`): dos plataformas
separadas de forma que el desnivel no se supere andando, y con un checkpoint
justo antes.

**Una noche legible.** `day_length = 420`, `ambient_light = 0.7`, un `Light` de
`radius 140`, `intensity 0.85` cada 8–10 baldosas, y comprueba con
`--hora 23`. Doce focos en 100 baldosas dan un 45 % de pantalla legible a
medianoche; siete daban un 24 % y el nivel era injugable.

**Un jefe.** Hereda de `BossBase`, define fases con `set_phases()`, telegrafía
cada ataque, y pon la arena en su propio TMX con `day_length = 0` para que la
luz no cambie a mitad de la pelea.

---

<a id="18"></a>
## 18. Errores frecuentes, y qué dice el motor

| Síntoma | Causa casi segura |
|---|---|
| El jugador cae al vacío por el suelo | falta el rectángulo en `Collision` |
| Todo se ve negro o con baldosas raras | el tileset declara un tamaño que no es el de la imagen |
| «Reserved names and duplicate names are not allowed» | usaste `visible` como nombre de propiedad; es reservado en Tiled |
| «More than one PlayerSpawn» | dos spawns |
| El nivel no valida | faltan `stage_id`, `stage_name` o `bgm_track` |
| No se ven las partículas | valor mal escrito en `ambient_fx`; la consola dice cuáles valen |
| No se notan los focos | `ambient_light` demasiado alto — con 1 no se ve ninguno |
| De noche no se ve nada | te faltan focos; el suelo de luz no basta |
| Un enemigo no se mueve | le falta `patrol_length` |
| Un `Pickup` no aparece | sin `item_id` y sin nombre: se ignora con aviso |
| Una puerta no bloquea | la dibujaste como punto; necesita área |
| El previsualizador no construye tus enemigos | los registraste dentro de una función |
| Un `EventTrigger` no hace nada | sin `evento` ni nombre |

El motor **avisa por consola** de casi todo esto. Antes fallaba en silencio y
se perdían tardes enteras; ahora, si algo no aparece, la primera parada es la
consola y no el foro.

---

## Documentos relacionados

- [[06_TMX_SPEC.md|Especificación TMX completa]]
- [[07_STAGE0_DESIGN.md|Diseño del Escenario 0 — el ejemplo resuelto]]
- [[STAGE_CREATION.md|Guía breve de creación]]
- [[05_ENEMY_SPEC.md|Especificación de enemigos]]
- [[17_BOSS_SPEC.md|Especificación de jefes]]
- [[56_FASE_5_ECS_Y_MECANICAS.md|Las once mecánicas de la fase 5]]
