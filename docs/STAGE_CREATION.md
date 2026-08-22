---
document_id: "LOI-GUIDE-STAGE"
title: "Guía de Creación de Escenarios"
aliases: ["Stage Creation Guide", "Guía de Creación de Escenarios"]
tags: ["stage", "creation", "guide", "tutorial"]
description: "Tutorial de creación de escenarios"
source: "docs/STAGE_CREATION.md"
date_processed: "2026-07-14"
---

# Stage Creation Guide

> **Esta guía es el resumen. El manual completo es
> [`60_GUIA_COMPLETA_DEL_MOTOR.md`](60_GUIA_COMPLETA_DEL_MOTOR.md).**
>
> Lo que hay aquí abajo sigue siendo cierto, pero es **parcial**: la tabla de
> enemigos lista 8 de los 30 tipos registrados, y no aparecen ninguno de los
> objetos de las fases 4 y 5 —`Pickup`, `Key`, `LockedDoor`, `Chest`, `Vine`,
> `Zipline`, `RhythmBlock`, `MovingPlatform`, `SinkingPlatform`, `WindZone`,
> `WaterZone`, `FrictionZone`, `Conveyor`, `LaserZone`, `Guard`, `Stalker`,
> `EventTrigger`—. Si buscas algo y no está aquí, está en la guía completa
> antes que en ningún sitio.

## 1. Requisitos del mapa TMX

Crea tu mapa en **Tiled** con esta configuración:

| Propiedad | Valor |
|---|---|
| Orientación | Ortogonal |
| Ancho de baldosa | 16 px |
| Alto de baldosa | 16 px |
| Orden de dibujado | Derecha-abajo |
| Infinito | No |

### Capas obligatorias (de abajo arriba)

| Orden | Nombre | Tipo | Propósito |
|---|---|---|---|
| 1 | `BG_Far` | Baldosas | Fondo lejano (parallax más lento) |
| 2 | `BG_Mid` | Baldosas | Fondo medio |
| 3 | `BG_Near` | Baldosas | Fondo cercano (parallax rápido) |
| 4 | `Terrain` | Baldosas | Terreno sólido principal |
| 5 | `Terrain_Detail` | Baldosas | Decoración sin colisión |
| 6 | `Objects` | Objetos | Apariciones de entidad, disparadores, checkpoints |
| 7 | `Collision` | Objetos | Rectángulos de colisión |
| 8 | `FG_Overlay` | Baldosas | Primer plano (se dibuja encima de las entidades) |

### Propiedades personalizadas obligatorias a nivel de mapa

| Property | Type | Example |
|---|---|---|
| `schema_version` | int | `1` — la versión del formato TMX que lee el motor |
| `stage_id` | string | `"stage1"` |
| `stage_name` | string | `"The Descent"` |
| `time_limit` | int | `180` (0 = no limit) |
| `bgm_track` | string | `"bgm_zone1"` — un fichero real de `assets/music/` |
| `background_zone` | string (optional) | `"cave"` — loads `assets/backgrounds/bg_cave_{far,mid,near}.png` |
| `gravity_multiplier` | float (optional) | `1.0` |

> **Sobre `schema_version` (AUD-393).** La plantilla ya la trae puesta y
> normalmente no hay que tocarla. Existe para que un mapa escrito para otra
> versión del motor se pueda distinguir de un mapa mal escrito: sin ella, un
> TMX antiguo falla con «falta la capa Collision» y uno se pone a buscar el
> error dentro del mapa. Un mapa que **no** la declara carga igual —se asume la
> `1`—; uno que declare una versión mayor que la del motor se rechaza al abrir,
> porque usa cosas que este código todavía no entiende.

### Atmósfera (opcional) — propiedades de la Fase 1

Todas son opcionales. Si no las declaras, el escenario usa el valor que
corresponde a su `zone`, así que un mapa sin ninguna de estas propiedades
sigue viéndose bien. Los valores fuera de rango se recortan en vez de
rechazarse: escribir `bloom = 5` significa "mucho", no un error de carga.

| Propiedad | Tipo | Rango | Qué hace |
|---|---|---|---|
| `ambient_light` | float | 0 – 1 | Luz de fondo. 1 = a plena luz, 0 = oscuridad total. Los focos que coloques se ven **por contraste** con este valor: con 1 no se nota ninguno. Stage 0 usa `0.70`; la arena del jefe, `0.42`. |
| `bloom` | float | 0 – 1 | Halo alrededor de lo brillante. Sube el contraste percibido de los focos sin aclarar las sombras. |
| `vignette` | float | 0 – 0.6 | Oscurece las esquinas. Conviene subirla al bajar `ambient_light`: un nivel oscuro con encuadre abierto se ve incoherente. |
| `climate` | string | `clear` `rain` `snow` `fog` `storm` | Precipitación y tinte de color. `storm` añade viento lateral. |
| `ambient_fx` | string | `dust` `leaves` `embers` `spores` `ash` `niebla` `vida_abisal` `none` | Partículas flotantes constantes. `none` lo apaga de forma explícita. |
| `ambient_fx_rate` | float | 0 – 120 | Partículas por segundo. Entre 10 y 20 es un ambiente perceptible sin saturar. |
| `start_hour` | string o float | 0 – 24 | Hora a la que empieza el escenario. Acepta un nombre (`dawn` `morning` `noon` `afternoon` `dusk` `night` `midnight`), un número (`18.5`) o `HH:MM`. |
| `season` | string | `spring` `summer` `autumn` `winter` | Estación. Tiñe la paleta, y **sugiere** un clima y unas partículas de aire si no los declaraste. Nunca sobrescribe lo que escribas: `climate = fog` en un mapa de otoño sigue siendo niebla. |
| `day_length` | float | 0 – 36000 | Segundos **reales** que dura un ciclo día/noche completo. `0` congela el reloj en `start_hour`, que es lo que quiere un combate: la luz no debe cambiar a mitad de una pelea. Stage 0 usa `420` (siete minutos); la arena del jefe lo deja congelado al atardecer. |

El ciclo modula la luz que ya declaraste: `ambient_light` sigue mandando, y la
hora lo multiplica y lo tiñe. Hay un suelo (`StageScene.MIN_AMBIENTE`) por
debajo del cual la luz no baja, porque una noche en la que no se ven los
enemigos es un defecto y no una decisión artística. La hora se comunica sobre
todo por el **color**: azul frío de madrugada, dorado al atardecer.

Un tipo mal escrito en `ambient_fx` —`leafs` en vez de `leaves`— **no falla en
silencio**: se avisa por consola con la lista de valores válidos y el escenario
cae a su valor por zona. Comprueba la consola si no ves las partículas.

### El objeto `Light`

Los focos se colocan en la capa `Objects` con `type = Light`. El punto de luz
es el **centro** del rectángulo que dibujes, así que puedes encuadrar una
antorcha y la luz saldrá de ella.

| Propiedad | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `radius` | float | `80` | Alcance en píxeles. |
| `color` | string | `warm` | `warm` `cold` `fire` `toxic` `blood` `white`, o `#rrggbb`. |
| `intensity` | float | `0.8` | 0 a 1. |
| `flicker` | bool | `false` | Parpadeo tipo antorcha o fuego. |
| `flicker_speed` | float | `4.0` | Oscilaciones por segundo. |
| `flicker_amount` | float | `0.15` | Amplitud, 0 a 1. |

Ejemplo de una antorcha: rectángulo de 16×16 sobre el muro, `type = Light`,
`radius = 110`, `color = warm`, `intensity = 0.85`, `flicker = true`.

Mira `assets/maps/stage0/stage0.tmx` (9 focos a lo largo del recorrido) y
`assets/maps/boss_venado/boss_venado.tmx` (cuatro braseros y un foco frío
central) como referencia.

### Ver tu escenario sin lanzar el juego

Ajustar un foco a ciegas cuesta una partida entera por intento: en Tiled un
`Light` es un cuadrado de 16 px y no hay forma de saber si su radio llega a
donde quieres. Para eso está el previsualizador:

```
python scripts/preview_tmx.py assets/maps/stage0/stage0.tmx
python scripts/preview_tmx.py mi_mapa.tmx --salida vista.png --con-etiquetas
python scripts/preview_tmx.py mi_mapa.tmx --hora 23        # ¿se ve de noche?
python scripts/preview_tmx.py mi_mapa.tmx --sin-luz        # sólo la geometría
```

Dibuja el mapa **entero** —no una ventana— con la iluminación aplicada, el
radio real de cada foco y un calco de colores sobre los objetos. Y al final
imprime un resumen: cuántos focos, cuántas entidades, cuántos puntos de
control, qué clima y qué estación. Si algo sale en cero que no debería, ahí lo
ves.

---

## 2. Convenciones de la capa de objetos

Coloca todos los objetos en la capa `Objects` como rectángulos o puntos con el campo **type** correcto.

### PlayerSpawn (punto)

Exactamente un objeto punto. **La coordenada Y es la posición de los pies del jugador** — el motor resta 32 px automáticamente.

```
type: PlayerSpawn
```

### Apariciones de enemigo (punto)

> **La tabla autoritativa es la de «Arquetipos de enemigo»**, más abajo, dentro
> del bloque `GENERATED`: la produce `scripts/generate_tmx_reference.py` desde
> el registro real y el CI comprueba que coincida. Ésta de aquí es un resumen de
> lectura y se mantiene a mano — si las dos se contradicen, gana la generada.
> (AUD-309: se contradijeron. `admite_bash` entró en la generada y esta llevaba
> una tanda sin enterarse.)

| Type | Required Properties | Optional Properties |
|---|---|---|
| `Walker` | — | `patrol_length`, `facing`, `patrol_speed`, `alert_speed`, `damage_on_contact` |
| `Flying` | — | `flight_mode`, `flight_speed`, `sine_amplitude`, `sine_frequency` |
| `Shooter` | — | `fire_rate`, `projectile_speed`, `projectile_damage`, `patrol_length`, `admite_bash` |
| `Charger` | — | `charge_speed`, `patrol_speed`, `alert_speed` |
| `Archer` | — | `fire_rate`, `projectile_speed` |
| `Brute` | — | `patrol_speed`, `alert_speed`, `max_health` |
| `Caster` | — | `fire_rate`, `projectile_damage` |
| `Assassin` | — | `patrol_speed`, `alert_speed` |

Las propiedades numéricas en el TMX (`patrol_length`, `max_health`, etc.) las convierte `StageLoader` a `float` automáticamente.

### Checkpoint (rectángulo)

```
type: Checkpoint
properties:
  - checkpoint_id (int, base 0)
```

### NextTrigger (rectángulo)

```
type: NextTrigger
```
No necesita propiedades. El jugador lo toca → el escenario se completa.

### MessageTrigger (rectángulo)

```
type: MessageTrigger
properties:
  - text (string)
```

Alternativamente, usa `type: MessageTrigger_Once` para disparadores de una sola vez.

### HazardZone (rectángulo)

```
type: HazardZone
properties:
  - damage (float, por defecto: 0.25)
```

### DeathPit (rectángulo)

```
type: DeathPit
```

### CameraLock (rectángulo)

```
type: CameraLock
properties:
  - lock_x (bool, por defecto: false)
  - lock_y (bool, por defecto: false)
```

### Waypoint (punto) — para enemigos Flying

```
type: Waypoint
properties:
  - owner_id (string) — debe coincidir con el **nombre** de la entidad Flying
  - waypoint_index (int) — orden de clasificación, base 0
```

### Objetos de la capa Collision

En la capa `Collision`, el `type` de cada objeto rectángulo determina el comportamiento:

| Type | Comportamiento |
|---|---|
| *(ninguno o `Solid`)* | Colisión AABB completa |
| `Platform` | Plataforma de un sentido (atravesable desde abajo) |

---

## 3. Registro del escenario

### 3.1 Crear una clase de escenario

Crea un fichero como `src/stages/<tu_escenario>/<tu_escenario>.py`:

```python
from pathlib import Path
from typing import TYPE_CHECKING
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

class Stage1(StageScene):
    STAGE_ID: str = "stage1"
    STAGE_NAME: str = "The Descent"
    ZONE: int = 1

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path("assets/maps/stage1/stage1.tmx"))
```

Coloca el fichero TMX en `assets/maps/<tu_escenario>/<tu_escenario>.tmx`.

### 3.2 Conectar la navegación

`ProgressionSystem` emite `Events.STAGE_COMPLETE` al terminar el escenario. Una `WorldMapScene` o una escena de historia debe escuchar este evento y hacer la transición al siguiente escenario.

---

## 4. Probar tu escenario

1. **Valida el TMX** — comprueba que existen las 8 capas obligatorias y que las propiedades están puestas.
2. **Comprueba que hay `PlayerSpawn`** — debe existir exactamente uno.
3. **Coloca al menos un `Checkpoint`** — si no, morir te manda al principio.
4. **Verifica la colisión** — dibuja los rectángulos de la capa `Collision` para que el jugador no atraviese el suelo.
5. **Ejecuta el juego** — navega a tu escenario y observa:
   - Los sprites se dibujan correctamente
   - Los enemigos se mueven y detectan al jugador
   - Los checkpoints se activan y persisten al morir
   - `NextTrigger` termina el escenario

Como referencia, mira `src/stages/stage0/stage0.py` y `assets/maps/stage0/`.

---
## 🔗 Documentos relacionados

- [[SCENE_CREATION.md|Guía de creación de escenas]]
- [[06_TMX_SPEC.md|Especificación TMX]]
- [[07_STAGE0_DESIGN.md|Diseño del Escenario 0]]

---

## Referencia de tipos de objeto

<!-- BEGIN GENERATED: tipos de objeto -->

> Tabla generada por `scripts/generate_tmx_reference.py` desde el
> registro real de entidades. No la edites a mano: añade la especie a
> `bestiary_registry.SPECIES` y vuelve a ejecutar el script.

### Tipos estructurales (capa `Objects`)

| Type | Geometría | Propiedades |
|---|---|---|
| `PlayerSpawn` | Punto | — (la Y son los pies del jugador) |
| `Checkpoint` | Rectángulo | `checkpoint_id` (int) **obligatoria** |
| `NextTrigger` | Rectángulo | — (completa el escenario) |
| `MessageTrigger` | Rectángulo | `text`, `duration` |
| `MessageTrigger_Once` | Rectángulo | `text`, `duration` (una sola vez) |
| `HazardZone` | Rectángulo | `damage` (float, 0.25) · `sube` (px/s: la inundación) · `sube_hasta` (y del mapa donde para) · `arranca_con` (evento de un `EventTrigger`) |
| `DeathPit` | Rectángulo | — (caer aquí mata) |
| `CameraLock` | Rectángulo | `lock_x`, `lock_y` (bool) |
| `Waypoint` | Punto | `owner_id` — ruta para la entidad con ese nombre |
| `Light` | Punto o rectángulo (se usa el **centro**) | `radius` (px, 80) · `color` (nombre de la paleta o `#rrggbb`) · `intensity` (0-1, 0.8) · `flicker` (bool) · `flicker_speed` (Hz, 4.0) · `flicker_amount` (0-1, 0.15) |
| `AmbientLightZone` | Rectángulo | `valor` (brillo 0-1 dentro de la zona, 1.0 = sin cambio) · `fundido` (px de transición del borde, 64). Mientras el jugador esté dentro, la luz ambiental base vale `valor`; en la banda de `fundido` interpola hacia el brillo del mapa (AUD-598) |
| `Cutscene` | Rectángulo o punto | `guion` **obligatoria** · `bloquea` · `saltable` · `una_vez` · `arranca_con`. Punto = al empezar; rectángulo = al entrar |
| `PushBlock` | Rectángulo | `velocidad` (px/s, 45) · `con_gravedad` |
| `BreakableBlock` | Rectángulo | `golpes` (int, 1) · `evento_al_romper` |
| `Pickup` | Rectángulo o punto | `item_id` **obligatoria** (vale el nombre del objeto en Tiled, o `key_id`) · `automatico` (bool, sí: se coge al tocarlo) · `mensaje` |
| `Key` | Rectángulo o punto | Alias de `Pickup`, mismas propiedades. Nombrarlo `Key` sólo hace el mapa legible en Tiled |
| `Door` | Rectángulo **obligatorio** | `key_id` (llave que la abre) · `consume_llave` (bool, no) · `mensaje` (al intentar pasar sin llave) · `evento` (se emite al abrir) · `abre_con` (evento que la abre sola) · `cierra_en` (segundos: puerta cronometrada) |
| `LockedDoor` | Rectángulo **obligatorio** | Alias de `Door`, mismas propiedades |
| `Cage` | Rectángulo **obligatorio** | Igual que `Door` pero se dibuja como jaula |
| `Chest` | Rectángulo | `contenido` (o `item_id`: lo que entrega) · `key_id` (llave que hace falta) · `mensaje` · `evento` (al abrir). Se abre con el botón de interactuar y entrega una sola vez |
| `EventTrigger` | Rectángulo | `evento` **obligatoria** (vale el nombre del objeto) · `automatico` (bool, sí: al entrar; no: hay que pulsar) · `una_vez` (bool, sí) · `key_id` |
| `Objective` | Punto | `objective_id` **obligatoria** · `text` **obligatoria** · `kind` (derrotar/recoger/bandera/hablar/llegar, «bandera») · `target` (qué enemigo, objeto o bandera; vacío = cualquiera) · `count` (int, 1) · `optional` (bool, false). Sin geometría: un objetivo no ocurre en un sitio, ocurre cuando pasa algo |
| `WindZone` | Rectángulo | `fuerza_x`, `fuerza_y` (px/s², 0) · `periodo` (s: con valor, el viento sopla a rachas) |
| `FrictionZone` | Rectángulo | `multiplicador` (1.0; por debajo de 1 resbala) · `arrastre` (px/s, 0) |
| `Conveyor` | Rectángulo | Igual que `FrictionZone`, pero `arrastre` vale 60 px/s por defecto: una cinta sin arrastre no es una cinta |
| `LaserZone` | Rectángulo | `dano` (99: mata) · `encendido` (s, 1.0) · `apagado` (s, 1.0) · `desfase` (s, 0: desincroniza dos láseres) |
| `ShockwaveZone` | Rectángulo | Alias de `LaserZone`, mismas propiedades |
| `WaterZone` | Rectángulo | `corriente_x`, `corriente_y` (px/s, 0). Dentro del agua el jugador pasa al estado de nado |
| `MovingPlatform` | Rectángulo | `destino_dx`, `destino_dy` (px **relativos** a donde la dibujaste) · `velocidad` (px/s, 40) · `espera` (s en cada extremo, 0.5) · `atravesable` (bool, no) |
| `RhythmBlock` | Rectángulo | `visible_seg` (1.0) · `oculto_seg` (1.0) · `desfase` (s, 0) · `patron` (p. ej. `"x.x."`: con patrón manda la música y los segundos dejan de contar) |
| `SinkingPlatform` | Rectángulo | `retraso` (s antes de ceder, 0.4) · `velocidad_caida` (px/s, 90) · `reaparece_en` (s, 3.0) |
| `Spring` | Rectángulo (rebota en todo su ancho) | `impulso` (px/s, -520; negativo es hacia arriba) · `rearme` (s, 0.15) |
| `Guard` | Punto | `mira_x`, `mira_y` (dirección, 1/0) · `alcance` (px, 160) · `semiangulo` (grados, 30) · `barrido` (grados, 0: el cono oscila) · `velocidad_barrido` (grados/s, 45) |
| `Stalker` | Punto | `velocidad` (px/s, 55) · `distancia_retirada` (px, 480) · `reaparicion` (s, 6.0) |
| `ScrollZone` | Rectángulo (el **disparador**, no la zona de muerte) | `velocidad_x` (px/s, 40) · `velocidad_y` (px/s, 0) · `margen_de_gracia` (px que se puede rebasar el borde antes de morir, 24) · `parar_en_x` (la cámara se detiene ahí; sin ella, hasta el final del mapa). Al pisarlo la cámara arranca sola y **el borde izquierdo mata**: SMB3 Airship, Cuphead, Ori |
| `WarpZone` | Rectángulo (el disparador) | `destino_x` / `destino_y` (**obligatorias**: adónde van los **pies** del jugador, en píxeles de mundo) · `automatico` (al tocar, true) · `una_vez` (false) · `key_id` · `enfriamiento` (s antes de poder repetirlo, 0.5) · `mensaje`. Teletransporta **dentro del mismo mapa**, que es lo que `NextTrigger` no hace: Zelda, Metroid, Hollow Knight. Sin destino no se carga y el cargador avisa |
| `Slope` | Rectángulo (el **triángulo entero**, no la línea) | `sube` (`derecha` por defecto, o `izquierda`: dónde está el lado alto). Suelo inclinado de verdad — la hipotenusa va de esquina a esquina. **No se apila con bloques escalonados**: eso es una escalera que frena al jugador en cada peldaño. Sonic, DKC, Celeste (AUD-297) |
| `Vine` | Rectángulo (alto = lo que se trepa) | `ancho_de_agarre` (px, 10) · `velocidad` (px/s de trepada, 70) |
| `Zipline` | Rectángulo (la esquina es el enganche) | `destino_dx` (px, 96), `destino_dy` (px, 64) **relativos** · `velocidad` (px/s, 190) · `radio_de_enganche` (px, 14) · `solo_de_bajada` (bool, sí) |
| `BossSpawn` | Punto (dónde entra el jefe) | `boss` (**obligatoria**: el nombre registrado del jefe, p. ej. `BossVenado`). Produce la misma entidad que escribir ese nombre como `type`; sin `boss`, o con uno que no esté registrado, el cargador avisa. Lo pide `17_BOSS_SPEC.md` §8.2 en todo mapa de jefe |

### Arquetipos de enemigo (capa `Objects`, objetos punto)

| Type | Ajustable con propiedades |
|---|---|
| `Walker` | `patrol_length`, `facing`, `patrol_speed`, `alert_speed`, `damage_on_contact` |
| `Flying` | `flight_mode`, `flight_speed`, `sine_amplitude`, `sine_frequency` |
| `Shooter` | `fire_rate`, `projectile_speed`, `projectile_damage`, `patrol_length`, `admite_bash` (bool, no: deja que el jugador se impulse golpeando sus disparos) |
| `Charger` | `charge_speed`, `patrol_speed`, `alert_speed` |
| `Archer` | `fire_rate`, `projectile_speed` |
| `Brute` | `patrol_speed`, `alert_speed`, `max_health` |
| `Caster` | `fire_rate`, `projectile_damage` |
| `Assassin` | `patrol_speed`, `alert_speed` |

### Especies con nombre (capa `Objects`, objetos punto)

Cada una es un arquetipo con sus valores ya puestos, tomados de
`docs/18_ENEMY_ROSTER.md`. Puedes sobreescribir cualquiera con una
propiedad del objeto en Tiled.

| Type | Nombre | Zona | Vida |
|---|---|---|---|
| `FlyingBird` | Ave de selva | 1 | 1.0 |
| `FlyingBoa` | Boa arborícola | 2 | 2.0 |
| `FlyingCucaracha` | Cucaracha voladora | 1 | 1.0 |
| `FlyingHalcon` | Halcón | 3 | 2.0 |
| `FlyingNotebook` | Cuaderno poseído | 1 | 0.5 |
| `FlyingTerciovolador` | Terciovolador | 2 | 1.5 |
| `ShooterBuitre` | Buitre | 3 | 3.5 |
| `ShooterCocinero` | Cocinero de cafetería | 1 | 3.0 |
| `ShooterFrog` | Rana dardo | 1 | 2.0 |
| `ShooterQuetzal` | Quetzal | 3 | 2.5 |
| `ShooterSerpienteArbol` | Serpiente de árbol | 2 | 2.0 |
| `ShooterTiza` | Tiza voladora | 1 | 2.5 |
| `ShooterVenomoLargo` | Venomo largo | 2 | 3.0 |
| `WalkerEstudiante` | Estudiante infestado | 1 | 1.5 |
| `WalkerGarza` | Garza | 3 | 2.0 |
| `WalkerGuardia` | Guardia infestado | 2 | 3.0 |
| `WalkerInsect` | Insecto de suelo | 1 | 1.0 |
| `WalkerPalom` | Paloma infestada | 3 | 2.5 |
| `WalkerRaton` | Rata de laboratorio | 1 | 1.0 |
| `WalkerSerpientePequena` | Serpiente pequeña | 2 | 1.0 |
| `WalkerTerciopelo` | Terciopelo | 2 | 2.5 |

### Capa `Collision` (vocabulario distinto)

| Type | Comportamiento |
|---|---|
| *(ninguno)* o `Solid` | Colisión AABB completa |
| `Platform` | Plataforma atravesable desde abajo |

Total aceptado en `Objects`: **70** tipos.

<!-- END GENERATED: tipos de objeto -->
