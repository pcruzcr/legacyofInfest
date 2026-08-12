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
4. [Los 77 tipos de objeto, uno por uno](#4)
5. [El jugador: 26 estados y qué los provoca](#5)
6. [Enemigos: 37 tipos y 13 estados](#6)
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

### 1.1 La cámara y la sensación de control

Tres modos, con la propiedad `camara` del mapa:

| Modo | Qué hace | De dónde viene |
|---|---|---|
| `seguir` | persigue al jugador con suavizado | el de siempre; sirve para casi todo |
| `zona_muerta` | **no se mueve** mientras el jugador esté en el centro | Celeste, Hollow Knight. Saltar en el sitio deja de mover el mundo entero, y eso cansa mucho menos la vista |
| `sala` | salta de pantalla en pantalla, sin suavizar | Zelda, Metroid, Castlevania. Cada sala se compone entera y se lee de un vistazo |

El corte de `sala` es instantáneo **a propósito**: suavizarlo lo convierte en
un barrido y se pierde justo lo que aporta.

La cámara además **se adelanta** en la dirección en la que corres
(`anticipacion`, 0,3 s por defecto) y **mira hacia abajo al caer**
(`anticipacion_caida`), que es lo que evita el salto de fe. Hacia arriba no
mira: ya sabes de dónde vienes, y mirar arriba al saltar marea.

Un `CameraLock` congela el eje que declare **sólo mientras estés dentro de su
rectángulo**. Hasta AUD-143 congelaba el nivel entero desde el primer
fotograma, y `boss_rey` llevaba un parche escrito para rodearlo.

Del lado del jugador hay dos perdones que no se ven y se notan:

* **Coyote time** (`PLAYER_COYOTE_FRAMES`, 100 ms): saltar justo después de
  dejar la plataforma sigue valiendo. Se cuenta en tiempo real, así que dura
  lo mismo a 30 que a 144 fps.
* **Buffer de salto** (130 ms): pulsar saltar un poco antes de aterrizar
  también vale, y el salto sale al tocar el suelo.

Los dos existen para lo mismo: el jugador cree que pulsó a tiempo, y casi
siempre tiene razón.

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
| `bgm_track` | string | `bgm_zone1` (AUD-311: tiene que ser un fichero real de `assets/music/`; si no existe, el nivel se juega en silencio y sólo lo dice el registro) |

### Del escenario

| Propiedad | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `author` | string | — | tu nombre; el calificador lo pide |
| `time_limit` | int | `0` | segundos; `0` = sin límite |
| `gravity_multiplier` | float | `1.0` | `0.5` = lunar, `1.5` = pesado |
| `zone` | int | `0` | zona del mundo; decide paleta y bestiario por defecto |
| `vista` | string | `lateral` | `lateral` o `cenital`. Cenital apaga la gravedad, da movimiento en dos ejes y **ignora las plataformas de un solo sentido** — desde arriba son muros invisibles. Hay un mapa que lo demuestra: `stage_cenital`, tres salas y una por modo de cámara (AUD-383) |
| `background_zone` | string | — | carga `assets/backgrounds/bg_<zona>_{far,mid,near}.png` |
| `camara` | string | `seguir` | `seguir`, `zona_muerta` o `sala` (§1.1) |
| `estamina` | float | `0` | máximo del medidor. **`0` = apagado.** Con `100`, cuatro dashes seguidos y una pausa de 0,6 s antes de recuperar |
| `tiempo_bala` | float | `0` | segundos de reserva de cámara lenta. **`0` = apagado.** Se mantiene pulsada `Q`/`R`: gasta reserva mientras dura y se recarga despacio al soltar (AUD-260) |
| `profundidad_min` | float | `1` | **2.5D (AUD-277).** Escala de las entidades arriba del todo del mapa —lo más lejano—. Igual a `profundidad_max` = apagado |
| `profundidad_max` | float | `1` | Escala abajo del todo —lo más cercano—. Un `0.75`/`1.0` da profundidad clara sin deformar. **No toca la física**: sólo el dibujado |
| `profundidad_curva` | float | `1` | **2.5D fase 6 (AUD-339).** Curva de la escala por profundidad: `1` es lineal (AUD-277); con más de `1` las filas del fondo se encogen más rápido, como una perspectiva de verdad. `2.0` en un mapa de 38 baldosas de alto comprime ya el tercio superior |
| `orden_por_y` | bool | `false` | **2.5D fase 6 (AUD-339).** Orden del pintor opcional: con `true`, las entidades se ordenan por la misma ancla que escala —los pies, o `depth_y` si la entidad la declara (una voladora se ordena por su proyección en el suelo)— en vez de por `rect.centery`. Sin la propiedad, el orden de AUD-067 queda intacto |
| `sombras_proyectadas` | bool | `false` | **AUD-278.** Los focos dejan de atravesar las paredes: cada obstáculo proyecta su cuña de sombra. Cuesta una proyección por foco y por obstáculo — enciéndelo en escenarios de noche, donde se nota |
| `bpm` | float | `0` | pulsos por minuto; enciende el reloj musical (§10.1) |

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
| `god_rays` | float | `0` | rayos de luz que bajan desde arriba, de `0` a `1`. Se nota con `ambient_light` baja |
| `cielo` | bool | `false` | **cielo procedural** (AUD-426): el degradado sale de la altura del sol en vez de un PNG. Enciéndelo si tu mapa **no** trae fondo con cielo pintado; si lo trae, el degradado queda debajo y no se ve |
| `habilidades_libres` | bool | `false` | exime a este escenario del candado de habilidades: el jugador entra con todo desbloqueado. Para laboratorios y pruebas |
| `water_effect` | bool | `false` | ondulación y refracción sobre las `WaterZone` |

#### Los cinco mandos del agua

Sólo hacen algo con `water_effect = true`. Los rangos se recortan a propósito
(AUD-240): una amplitud de 40 px convierte la lámina en ruido y un alfa de 255
tapa el escenario, así que un mapa mal escrito se ve raro pero **jugable**, que
es la regla del resto del cargador.

| Propiedad | Tipo | Rango | Qué hace |
|---|---|---|---|
| `water_speed` | float | 0 – 8 | a qué velocidad se mueve la ondulación |
| `water_amplitude` | float | 0 – 16 | cuánto sube y baja la onda, en píxeles |
| `water_frequency` | float | 0 – 1 | cuántas ondas caben a lo ancho |
| `water_alpha` | float | 0 – 255 | opacidad de la lámina |
| `water_tint` | color | `#rrggbb` | color del agua. Por defecto un azul verdoso |

> **Añadidas el 2026-08-11 (AUD-430).** Estas ocho propiedades las lee el motor
> y **ningún documento de referencia las mencionaba** — ni éste, ni
> `06_TMX_SPEC.md`, ni `STAGE_CREATION.md`. Ocho características construidas,
> probadas y que ningún estudiante podía descubrir. Ahora lo impide
> `test_toda_propiedad_del_motor_esta_documentada`.

Los valores fuera de rango se **recortan**, no se rechazan: `bloom = 5`
significa «mucho». Un valor mal escrito —`leafs` en vez de `leaves`— avisa por
consola con la lista de valores válidos y usa el de la zona. Si no ves un
efecto, mira la consola antes que el código.

---

<a id="4"></a>
## 4. Los 77 tipos de objeto, uno por uno

El motor acepta **78 tipos** en la capa `Objects`: 39 integrados del framework
y 37 enemigos del registro, más `Solid` y `Platform` en `Collision`. Todos los
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

#### `Objective`

Un objetivo del nivel, declarado en el mapa (AUD-400). Es un **punto**: un
objetivo no ocurre en un sitio, ocurre cuando pasa algo.

| Propiedad | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `objective_id` | string | — | **obligatoria**. Con este nombre lo cierra `complete_objective:` desde un guion de diálogo |
| `text` | string | — | **obligatoria**. Lo que lee el jugador |
| `kind` | string | `bandera` | `derrotar`, `recoger`, `bandera`, `hablar` o `llegar` |
| `target` | string | - | contra qué se compara: la especie que muere, el objeto recogido, la bandera puesta. **Vacío = cualquiera**, que es lo que permite «derrota a cinco enemigos» sin enumerar especies |
| `count` | int | `1` | cuántas veces hay que hacerlo |
| `optional` | bool | `false` | `true` = no impide terminar el nivel. Es la diferencia entre la misión y el coleccionable |

Los cinco tipos existen porque hay cinco eventos del motor que los pueden
completar; uno que ningún evento cierre sería un objetivo imposible. Un
escenario que **no declara ninguno** no tiene nada pendiente, que es lo que
mantiene intactos los mapas anteriores. Sin `objective_id` o sin `text` se
ignora con un aviso. `stage0` declara dos como ejemplo, uno obligatorio y uno
opcional.

#### `Cutscene`

| Propiedad | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `guion` | string | - | guion de la escena: acciones en orden (mover cámara, esperar, fundir, texto, evento) |
| `bloquea` | bool | `true` | `false` = el jugador puede moverse mientras suena |
| `saltable` | bool | `true` | `false` = no se puede saltar la escena |
| `una_vez` | bool | `true` | se repite en cada visita si es `false` |
| `arranca_con` | string | - | nombre del `evento` que la dispara; vacío = al entrar en el rectángulo |

Con rectángulo se dispara al entrar el jugador; como punto, al empezar el
escenario. Sin `guion` se ignora con un aviso. Mientras dura, el escenario no
se sigue jugando por debajo; el sistema completo está en el §13.

### 4.3 Peligros

| Tipo | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `HazardZone` | `damage` | `0.25` | daño por tic mientras estés dentro |
| | `sube` | `0` | px/s que sube el borde superior. **`0` = zona fija**; con `>0` es una inundación |
| | `sube_hasta` | — | la `y` del mapa donde el agua se para. Vacío = sin tope |
| | `arranca_con` | — | nombre del `evento` de un `EventTrigger`. Vacío = sube desde el principio |
| `DeathPit` | — | — | muerte instantánea, sin pasar por niveles de daño ni invulnerabilidad |
| `LaserZone` | `dano` | `99` | letal, intermitente |
| | `encendido` | `1.0` | segundos activo |
| | `apagado` | `1.0` | segundos apagado |
| | `desfase` | `0.0` | desplaza el ciclo; con tres láseres a 0, 0.5 y 1.0 se hace una cortina |
| `ShockwaveZone` | igual que `LaserZone` | | mismo componente, otro nombre para que el mapa se lea |

Un `DeathPit` mata del todo **a propósito**. Un foso que quita media vida
enseña a caerse dentro.

#### La inundación

Una `HazardZone` con `sube` es agua que crece. Es la mecánica más barata que
cambia el ritmo de una sala entera: sin añadir un enemigo, un tramo de
plataformas se convierte en una persecución.

```xml
<object type="HazardZone" x="0" y="900" width="1600" height="120">
  <properties>
    <property name="damage" type="float" value="0.5"/>
    <property name="sube" type="float" value="18"/>
    <property name="sube_hasta" type="float" value="240"/>
    <property name="arranca_con" value="ROMPER_LA_PRESA"/>
  </properties>
</object>
```

Con `arranca_con`, el agua espera a que un `EventTrigger` con ese mismo
`evento` se dispare. Es la combinación que hace el nivel: se recorre tranquilo
hacia dentro, se rompe la presa, y la vuelta es otra cosa.

Tres cosas que conviene saber al colocarla:

* **Crece hacia arriba; el fondo no se mueve.** Si se desplazara dejaría el
  suelo limpio detrás y se podría volver a bajar.
* **El motor la dibuja.** Las zonas fijas se pintan con tiles —pinchos, lava—,
  pero los tiles no suben. El agua es translúcida a propósito: hay que ver las
  plataformas sumergidas para decidir la ruta.
* **Al morir vuelve a su altura.** El reintento empieza igual que el primer
  intento.

Elegir `sube`: a 18 px/s el agua tarda unos 37 segundos en subir un mapa de
altura 672. Como referencia, con menos de 10 px/s la persecución no se siente
y por encima de 40 px/s casi ninguna ruta da tiempo.

### 4.4 Zonas con efecto físico

| Tipo | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `WindZone` | `fuerza_x` | `0` | empuje horizontal en px/s² |
| | `fuerza_y` | `0` | empuje vertical |
| |fx `periodo` | `0` | segundos de ciclo. **`0` = constante**; con `3.4` amaina y vuelve, y la solución pasa a ser esperar |
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
| `PushBlock` | `velocidad` | `45` | px/s mientras se empuja. Lento a propósito: empujar tiene que costar |
| | `con_gravedad` | `true` | `false` = se queda flotando (para vista cenital) |
| `BreakableBlock` | `golpes` | `1` | golpes que aguanta. Uno es un secreto; tres, un obstáculo |
| | `evento_al_romper` | — | evento del bus al ceder: abre puertas, arranca inundaciones, lanza escenas |
| `RhythmBlock` | `visible_seg` | `1.0` | segundos presente |
| | `oculto_seg` | `1.0` | segundos ausente |
| | `desfase` | `0.0` | desplaza el ciclo |
| | `patron` | — | patrón de compás, p. ej. `x.x.`. **Manda sobre los segundos** y exige que el mapa declare `bpm` |

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

**`ScrollZone` — la persecución (AUD-249).** SMB3 Airship, Cuphead, Ori, la
Wall of Flesh. Su rectángulo es el **disparador, no la zona de muerte**: el
jugador lo pisa una vez y a partir de ahí manda la cámara. Quien mata es el
borde izquierdo de la pantalla.

| Type | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `ScrollZone` | `velocidad_x` | `40` | px/s. Negativo = hacia la izquierda |
| | `velocidad_y` | `0` | px/s vertical, para una subida tipo Ori |
| | `margen_de_gracia` | `24` | px que se puede rebasar el borde antes de morir |
| | `parar_en_x` | — | la cámara se detiene ahí; sin ella, hasta el final |

El borde **mata** en vez de empujar, y es deliberado: empujar deja al jugador
aplastado contra la geometría o atascado en un saliente mientras la cámara
sigue. Matar es honesto —el nivel dijo «sígueme» y no lo seguiste— y el
reintento es inmediato si has puesto checkpoints. Ponlos.

**`Slope` — suelo inclinado de verdad (AUD-297).** Sonic, DKC, Celeste. Hasta
AUD-297 una cuesta había que fingirla apilando bloques escalonados, y eso no es
una cuesta: es una escalera que frena al jugador en cada peldaño.

| Type | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `Slope` | `sube` | `derecha` | Dónde está el lado alto: `derecha` o `izquierda` |

El rectángulo que dibujes es el **triángulo entero**, no la línea de la
superficie: se dibuja como se dibujaría la roca, y la hipotenusa va de esquina a
esquina. No la metas en la capa `Collision`: una pendiente que además fuera caja
pararía al jugador en seco al pie de la rampa.

Bajarla funciona igual de bien que subirla, y eso no es gratis — el motor pega
al jugador a la superficie con ocho píxeles de margen. Sin eso, descender una
cuesta se hace a saltitos.

**`WarpZone` — cruzar el mapa de una punta a otra (AUD-287).** Las cuevas de
Zelda, los ascensores de Metroid, los Stagways de Hollow Knight. Hasta AUD-287
esto no se podía declarar: `NextTrigger` cambia de escenario y `Door` abre un
paso, y no había nada entre medias, así que un mapa grande obligaba a
recorrerlo entero para volver.

| Type | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `WarpZone` | `destino_x` | **obligatoria** | px de mundo; ahí van los **pies** del jugador |
| | `destino_y` | **obligatoria** | idem |
| | `automatico` | `true` | `false` pide el botón de usar |
| | `una_vez` | `false` | para un pasadizo de ida sin vuelta |
| | `key_id` | — | hace falta esa llave |
| | `enfriamiento` | `0.5` | segundos antes de poder repetirlo |
| | `mensaje` | — | texto al cruzar |

Sin destino **no se carga**, y el cargador te lo dice: un warp que manda a la
esquina del mapa parece un fallo del motor, no un mapa a medio configurar. El
enfriamiento tampoco es decorativo — un destino que cae dentro de otra zona de
warp, o dentro de sí misma, produce un bucle a 60 fps.

Piénsalo dos veces antes de ponerlo automático. En un corredor por el que se
pasa andando se dispara sin querer, y si el tramo tiene scroll forzado, eso es
una trampa.

**`BossSpawn` — dónde entra el jefe (AUD-259).** `17_BOSS_SPEC.md` §8.2 lo
pide en todo mapa de jefe desde que se escribió, y hasta AUD-259 **el motor no
lo aceptaba**: quien seguía la especificación al pie de la letra recibía un
aviso de tipo desconocido y su jefe no aparecía.

| Type | Propiedad | Por defecto | Qué hace |
|---|---|---|---|
| `BossSpawn` | `boss` | — | **Obligatoria.** El nombre registrado del jefe, p. ej. `BossVenado` |

Produce exactamente la misma entidad que escribir ese nombre como `type`,
porque se resuelve por el mismo registro. Sin `boss`, o con un nombre que no
esté registrado, el cargador **avisa** en vez de callarse: quedarse mudo es lo
que hizo que este hueco durara meses.

El `margen_de_gracia` existe porque sin él la muerte ocurre cuando el sprite
aún se ve, y eso se lee como injusticia aunque sea correcto.

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

#### El hueco horizontal, y por qué el calificador es más generoso (GAP-024)

Con el alcance **horizontal** hay que saber una cosa antes de diseñar un salto
largo, y está medida:

| Cómo se salta | Baldosas que se cruzan |
|---|---|
| Entrada natural — mantener la dirección y saltar | **3** |
| Técnica experta — encadenar el salto aéreo en el punto justo | **5** |
| Repecho vertical | 5 |

`grade_stage` mide con una envolvente que **asume la técnica experta**, así que
puede etiquetar «cómodo» un hueco de 4 baldosas que con entrada natural no se
cruza. Es una decisión tomada y no un descuido (AUD-264): apretar la envolvente
habría rebajado la nota de geometría de entregas ya calificadas, y conectar el
salto aéreo a los estados de suelo habría cambiado la física de los diecisiete
mapas a la vez.

**Lo que significa para ti:** si tu nivel es para alguien que juega por primera
vez, diseña con **3 baldosas**. Los huecos de 4 y 5 son contenido para quien ya
domina el salto aéreo — colócalos donde fallar cueste poco, no en el camino
principal. `python -m tests.playtest.jump_bench` imprime la tabla completa.

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
## 6. Enemigos: 37 tipos y 13 estados

### Los ocho arquetipos

Son la base; los 29 restantes son variantes temáticas con otro aspecto y otros
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

### Los enemigos de las entregas

Siete tipos más viven en los escenarios de las entregas, no en el bestiario:
los registra el propio paquete del escenario al importarse, y por eso sólo
existen en los mapas de su zona.

| Tipo | De dónde viene | Cómo se comporta |
|---|---|---|
| `LaSodaWalkerRaton` | `stage1_2_la_soda` | una rata que patrulla, como `WalkerRaton` |
| `LaSodaFlyingCucaracha` | `stage1_2_la_soda` | una cucaracha que vuela, como `FlyingCucaracha` |
| `EstudianteInfectado` | `stage1_3_las_aulas` | un estudiante que ataca de cerca |
| `CuadernoVolador` | `stage1_3_las_aulas` | un cuaderno que vuela por una curva |
| `BossGavilan` | `stage3_4_boss_gavilan` | el jefe del gavilán, con fases |
| `BossRey` | `boss_rey` | el Rey Terciopelo, jefe de la Práctica I, con fases |
| `BossPaburu` | `boss_paburu` | el Gran Chamán Paburu, jefe de la Zona 4, con fases |

El cargador importa el paquete del escenario al abrir su mapa y así encuentra
estos tipos. Si registras los tuyos **al nivel del módulo** (fuera de funciones
y de métodos de clase), pasan a existir para todo el que abra tu mapa, incluido
el validador.

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
| Voz, con la música apartada | `play_voz(nombre)` — agacha la música al 35 % mientras suena |

Volúmenes de música y efectos separados, silencio con `M`. **Si falta un
fichero de audio, el juego sigue**: se registra el aviso y se calla ese sonido.
Un nivel no se cae por un `.ogg` que no subiste, pero mira la consola.

### 10.0 Los cuatro buses

`musica`, `efectos`, `voz` y `ambiente`. El volumen de un sonido es
**maestro × bus × el que pida quien lo reproduce**, y se calcula en un solo
sitio para que el silencio y el *ducking* no se olviden en ninguna llamada.

Abrir un diálogo **aparta la música** al 35 %: baja en 0,15 s —si tardara, se
comería la primera palabra— y vuelve en 0,5 s —subir de golpe suena a fallo—.
No hay que pedirlo: lo hace el sistema de diálogo.

**Reverberación por zona no hay, y no la va a haber sobre este mezclador.** El
de SDL no tiene efectos: reproduce muestras y las suma. Haría falta
convolucionar cada sonido con la respuesta de la sala al cargarlo, o una
biblioteca de DSP externa.

### 10.1 Niveles rítmicos: el reloj musical

Declara el compás en el mapa y el escenario pasa a tener pulso:

| Propiedad del mapa | Por defecto | Qué hace |
|---|---|---|
| `bpm` | `0` | pulsos por minuto. **`0` = el escenario no es rítmico** y el reloj ni se construye |
| `compas` | `4` | pulsos por compás. `3` da un vals |
| `desfase_audio` | `0` | segundos de latencia que compensar en esta máquina |

Con `bpm` puesto, un `RhythmBlock` con `patron` deja de contar segundos y sigue
a la música: `"x.x."` es sí, no, sí, no, un carácter por pulso. Dos bloques con
`"x.x."` y `".x.x"` se turnan, y eso ya es un tramo rítmico.

Por qué no basta con `visible_seg`: un bloque que suma su propio tiempo y una
canción que suena llevan **relojes distintos**. Al minuto van cien milisegundos
desfasados —más de lo que el oído tolera— y a los cinco minutos, medio compás.
El reloj musical no cuenta: le pregunta al mezclador por dónde va la pista.

Y va con tiempo **real**: el tiempo bala ralentiza el mundo y la música sigue
sonando igual, así que una ralentización no desincroniza el nivel.

Desde código hay más de lo que cabe en una propiedad: `reloj.en_ventana()` dice
si ahora mismo se está a compás —para premiar un salto a tiempo—,
`reloj.cuantizar(t)` redondea un instante al pulso más cercano y
`reloj.pulsos_cruzados` cuenta cuántos pulsos empezaron en este fotograma (es un
contador y no un sí/no: un fotograma largo puede cruzar dos).

El laboratorio de mecánicas (`stage_mecanicas`) tiene los cuatro bloques de la
sala 4 puestos así: dos a la manera de siempre y dos siguiendo la música.

---

<a id="11"></a>
## 11. Inventario, coleccionables y llaves

Dieciséis objetos definidos, en tres familias que **cuentan distinto**.

### Mejoras permanentes — se recogen en el mapa y apilan

No tienen hueco (`slot = None`): basta con tenerlas, y dos copias valen el
doble. Son las que colocas en el nivel con un `Pickup`.

| `item_id` | Nombre | Efecto |
|---|---|---|
| `heart_vessel` | Heart Vessel | +1 vida máxima |
| `hollow_eye` | Hollow Eye | +0,3 de daño |
| `ancients_rib` | Ancient's Rib | +2 vida máxima |
| `swift_feather` | Swift Feather | +10 % de velocidad |
| `thorn_ring` | Thorn Ring | +0,5 de daño |
| `sunken_crown` | Sunken Crown | +3 vida máxima, +0,8 de daño |

### Ropa — se compra, se pone y sólo cuenta puesta

Cada prenda ocupa un `slot` (`head`, `body`, `feet`) y **su bonificación sólo
se aplica si está equipada** (AUD-207). Llevar dos capuchas en la mochila no
suma las dos: sólo cuenta la que esté en el hueco `head`, y una copia de más
tampoco duplica nada. Ese límite es lo que convierte el equipo en una
decisión. `price` es lo que cuesta en monedas; se vende por la mitad.

| `item_id` | Nombre | Hueco | Efecto | Precio |
|---|---|---|---|---|
| `hood_leaf` | Leaf Hood | `head` | +0,2 de daño | 30 |
| `hood_ember` | Ember Hood | `head` | +0,5 vida máxima | 40 |
| `cloak_reed` | Reed Cloak | `body` | +5 % de velocidad | 35 |
| `cloak_serpent` | Serpent Cloak | `body` | +0,4 de daño | 50 |
| `boots_swift` | Swift Boots | `feet` | +8 % de velocidad | 45 |
| `boots_stone` | Stone Boots | `feet` | +1 vida máxima | 40 |

La moneda del juego es un objeto más: `coin`. El saldo se consulta con
`Inventory.coins` y se mueve con `add_coins()` / `spend_coins()`.

| `item_id` | Nombre | Efecto |
|---|---|---|
| `coin` | Coin | moneda de la tienda; sin bonificación |

### Habilidades — sueltas de jefe

Ocupan `slot = "skill"`, no dan estadísticas y no se equipan: se tienen o no,
y se consultan con `Inventory.has_skill()`.

| `item_id` | Nombre | Concede | La suelta |
|---|---|---|---|
| `skill_double_jump` | Double Jump | saltar otra vez en el aire | `BossRey` |
| `skill_dash` | Dash | impulso rápido hacia delante | `BossVenado` |
| `skill_parry` | Parry | desviar ataques | — (nadie todavía) |

**Tu jefe puede conceder una con una línea.** En su clase:

```python
class MiJefe(BossBase):
    skill_drop = "skill_dash"
```

Al morir deja la reliquia en el suelo junto a las monedas. Si el `item_id` no
está en el catálogo no se deja nada, para no poner un objeto que al cogerlo no
haría nada.

### El candado: `PLAYER_SKILLS_REQUIRE_UNLOCK`

Por defecto está en **`False`**, y eso importa: el doble salto y el dash están
disponibles desde el primer fotograma del primer nivel, igual que siempre. Los
niveles que ya existen se juegan exactamente igual.

Ponlo en `True` si quieres que **derrotar al jefe signifique algo**: entonces
`_can_jump` y `_can_dash` preguntan al inventario y sin la habilidad no hay
doble salto ni dash. Dos cosas que no cambian ni con el candado puesto:

* el **salto desde el suelo** y los fotogramas de coyote nunca se bloquean —
  sin ellos no se sube un escalón;
* la habilidad tiene que soltarla algún jefe **antes** del punto donde el nivel
  la exija, o el nivel no se puede terminar. Si diseñas con el candado puesto,
  comprueba ese orden.

> **Estado real:** el ciclo entero funciona.
>
> * **Monedas:** los enemigos las sueltan al morir (`Recogible` de `coin`, con
>   la cantidad según el tipo). Se recogen al pasar por encima.
> * **Tienda:** entrada `SHOP` del menú del título. Izquierda y derecha
>   alternan comprar y vender; se vende por la mitad del precio.
> * **Equipar:** entrada `INVENTORY`, con Enter sobre la prenda.
> * **Puntos y saldo:** se ven en el HUD durante la partida.
> * **Habilidades:** los jefes las sueltan; ver el candado más abajo.
>
> La única pieza sin dueño es `skill_parry`: está en el catálogo y ningún jefe
> la suelta todavía, porque parar **no** está condicionado —lo aprende el
> jugador, no se compra—. Si quieres usarla, dásela a tu jefe con `skill_drop`.

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

El **sistema de cutscenes** encadena acciones: mover la cámara, mover un
personaje, esperar, fundir, temblar, sonar, mostrar texto, abrir un árbol de
diálogo o emitir un evento. Y se escribe desde Tiled.

> Un fundido a negro termina **opaco**. Hasta esta semana `FadeAction`
> retornaba antes de dibujar el velo al completarse, y el fundido acababa
> desfundido: un fotograma de destello justo antes del corte, exactamente
> donde no se quiere.

### 13.1 Una escena desde el mapa

Se pone un objeto `Cutscene` en la capa `Objects`. Como **rectángulo**, se
dispara cuando el jugador entra; como **punto**, al empezar el escenario.

| Propiedad | Por defecto | Qué hace |
|---|---|---|
| `guion` | — | el guion, una orden por línea. **Obligatoria** |
| `bloquea` | `true` | `false` = el juego sigue corriendo por debajo |
| `saltable` | `true` | `false` = CANCEL no la salta |
| `una_vez` | `true` | `false` = se repite cada vez que se entra |
| `arranca_con` | — | evento de un `EventTrigger` que la lanza, en vez de la posición |

El guion:

```text
# la llegada al puente
camara 640 200 1.2
+ mover jugador 610 . 1.2      # «+» = a la vez que la línea anterior
temblor 0.5 8
texto Eco: El puente no aguanta.
dialogo aviso_del_puente
evento ROMPER_EL_PUENTE
esperar 0.4
```

| Orden | Forma | Qué hace |
|---|---|---|
| `esperar` | `esperar 0.5` | pausa |
| `camara` | `camara <x> <y> <dur>` | lleva la cámara |
| `mover` | `mover <quién> <x> <y> <dur>` | lleva a alguien. `jugador` o el nombre del objeto en Tiled. Un `.` en una coordenada = no la toques |
| `texto` | `texto Eco: Hola` | un cuadro; avanza con ENTER |
| `dialogo` | `dialogo <árbol>` | abre el sistema de diálogo bueno y espera a que se cierre |
| `evento` | `evento ABRIR` | emite al bus: abre puertas, arranca inundaciones |
| `sonido` | `sonido SFX_X` | pide un sonido y sigue |
| `temblor` | `temblor <dur> <fuerza>` | sacude la cámara |
| `fundido` | `fundido entra\|sale <dur>` | funde |
| `esperar_evento` | `esperar_evento X [tope]` | espera a que alguien emita `X`, con tope de segundos |

Tres cosas que conviene saber:

* **Saltar ejecuta el final, no lo cancela.** Si el guion llevaba al jugador
  hasta la puerta y abría la puerta, saltarlo lo deja en la puerta y la puerta
  abierta. Un botón de saltar que rompe la partida es peor que no tenerlo.
* **`bloquea = false` es la opción interesante.** Un compañero que grita desde
  una cornisa mientras se sigue corriendo cuenta lo mismo sin interrumpir. A la
  tercera interrupción el jugador se las salta todas sin leerlas.
* **Una línea que no se entiende no rompe la escena.** Se ignora, se avisa en
  el registro y el resto del guion sigue. Un guion es contenido, no código.

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
