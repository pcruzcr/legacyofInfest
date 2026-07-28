---
document_id: "LOI-GUIDE-STAGE"
title: "Stage Creation Guide"
aliases: ["Stage Creation Guide"]
tags: ["stage", "creation", "guide", "tutorial"]
description: "Stage creation tutorial"
source: "docs/STAGE_CREATION.md"
date_processed: "2026-07-14"
---

# Stage Creation Guide

## 1. TMX Map Requirements

Create your map in **Tiled** with the following settings:

| Property | Value |
|---|---|
| Orientation | Orthogonal |
| Tile width | 16 px |
| Tile height | 16 px |
| Render order | Right-down |
| Infinite | No |

### Required Layers (bottom-to-top)

| Order | Name | Type | Purpose |
|---|---|---|---|
| 1 | `BG_Far` | Tile | Distant background (slowest parallax) |
| 2 | `BG_Mid` | Tile | Mid-distance background |
| 3 | `BG_Near` | Tile | Near background (fast parallax) |
| 4 | `Terrain` | Tile | Primary solid terrain |
| 5 | `Terrain_Detail` | Tile | Decorative non-solid overlays |
| 6 | `Objects` | Object | Entity spawns, triggers, checkpoints |
| 7 | `Collision` | Object | Collision rectangles |
| 8 | `FG_Overlay` | Tile | Foreground (renders above entities) |

### Required Map-Level Custom Properties

| Property | Type | Example |
|---|---|---|
| `stage_id` | string | `"stage1"` |
| `stage_name` | string | `"The Descent"` |
| `time_limit` | int | `180` (0 = no limit) |
| `bgm_track` | string | `"bgm_stage1"` |
| `background_zone` | string (optional) | `"cave"` — loads `assets/backgrounds/bg_cave_{far,mid,near}.png` |
| `gravity_multiplier` | float (optional) | `1.0` |

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
| `ambient_fx` | string | `dust` `leaves` `embers` `spores` `ash` `none` | Partículas flotantes constantes. `none` lo apaga de forma explícita. |
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

---

## 2. Object Layer Conventions

Place all objects in the `Objects` layer as rectangles or points with the correct **type** field.

### PlayerSpawn (Point)

Exactly one point object. **The Y coordinate is the player's feet position** — the engine subtracts 32 px automatically.

```
type: PlayerSpawn
```

### Enemy Spawns (Point)

| Type | Required Properties | Optional Properties |
|---|---|---|
| `Walker` | — | `patrol_length`, `facing`, `patrol_speed`, `alert_speed`, `damage_on_contact` |
| `Flying` | — | `flight_mode`, `flight_speed`, `sine_amplitude`, `sine_frequency` |
| `Shooter` | — | `fire_rate`, `projectile_speed`, `projectile_damage`, `patrol_length` |
| `Charger` | — | `charge_speed`, `patrol_speed`, `alert_speed` |
| `Archer` | — | `fire_rate`, `projectile_speed` |
| `Brute` | — | `patrol_speed`, `alert_speed`, `max_health` |
| `Caster` | — | `fire_rate`, `projectile_damage` |
| `Assassin` | — | `patrol_speed`, `alert_speed` |

Numeric properties in TMX (`patrol_length`, `max_health`, etc.) are automatically cast to `float` by `StageLoader`.

### Checkpoint (Rectangle)

```
type: Checkpoint
properties:
  - checkpoint_id (int, 0-based)
```

### NextTrigger (Rectangle)

```
type: NextTrigger
```
No properties required. Player touches it → stage complete.

### MessageTrigger (Rectangle)

```
type: MessageTrigger
properties:
  - text (string)
```

Alternatively, use `type: MessageTrigger_Once` for one-time triggers.

### HazardZone (Rectangle)

```
type: HazardZone
properties:
  - damage (float, default: 0.25)
```

### DeathPit (Rectangle)

```
type: DeathPit
```

### CameraLock (Rectangle)

```
type: CameraLock
properties:
  - lock_x (bool, default: false)
  - lock_y (bool, default: false)
```

### Waypoint (Point) — for Flying enemies

```
type: Waypoint
properties:
  - owner_id (string) — must match the Flying entity's **name**
  - waypoint_index (int) — 0-based sort order
```

### Collision Layer Objects

In the `Collision` layer, each rectangle object's `type` determines behavior:

| Type | Behavior |
|---|---|
| *(none or `Solid`)* | Full AABB collision |
| `Platform` | One-way platform (passable from below) |

---

## 3. Stage Registration

### 3.1 Create a Stage Class

Create a file like `src/stages/<your_stage>/<your_stage>.py`:

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

Place the TMX file at `assets/maps/<your_stage>/<your_stage>.tmx`.

### 3.2 Wire Up Navigation

The `ProgressionSystem` emits `Events.STAGE_COMPLETE` when the stage ends. A `WorldMapScene` or story scene should listen for this and transition to the next stage.

---

## 4. Testing Your Stage

1. **Validate the TMX** — ensure all 8 required layers exist and properties are set.
2. **Check for `PlayerSpawn`** — exactly one must exist.
3. **Place at least one `Checkpoint`** — otherwise death sends you to the start.
4. **Verify collision** — draw `Collision` layer rectangles so the player can't fall through.
5. **Run the game** — navigate to your stage and observe:
   - Sprites render correctly
   - Enemies move and detect the player
   - Checkpoints activate and persist on death
   - `NextTrigger` ends the stage

For reference, see `src/stages/stage0/stage0.py` and `assets/maps/stage0/`.


--- Traducción al Español ---

## Guía de Creación de Escenarios

### Requisitos del Mapa TMX
- Orientación: Ortogonal
- Tiles: 16×16 px
- 8 capas requeridas (BG_Far a FG_Overlay)
- Propiedades personalizadas: stage_id, stage_name, time_limit, bgm_track

### Convenciones de la Capa de Objetos
- PlayerSpawn: Un punto, Y = posición de pies
- Enemigos: Puntos con propiedades
- Checkpoints: Rectángulos con checkpoint_id
- NextTrigger: Rectángulo para finalizar escenario

Para instrucciones detalladas de registro y pruebas, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[SCENE_CREATION.md|Scene Creation Guide]]
- [[06_TMX_SPEC.md|TMX Specification]]
- [[07_STAGE0_DESIGN.md|Stage 0 Design]]

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
| `HazardZone` | Rectángulo | `damage` (float, 0.25 por defecto) |
| `DeathPit` | Rectángulo | — (caer aquí mata) |
| `CameraLock` | Rectángulo | `lock_x`, `lock_y` (bool) |
| `Waypoint` | Punto | `owner_id` — ruta para la entidad con ese nombre |
| `Light` | — | — |

### Arquetipos de enemigo (capa `Objects`, objetos punto)

| Type | Ajustable con propiedades |
|---|---|
| `Walker` | `patrol_length`, `facing`, `patrol_speed`, `alert_speed`, `damage_on_contact` |
| `Flying` | `flight_mode`, `flight_speed`, `sine_amplitude`, `sine_frequency` |
| `Shooter` | `fire_rate`, `projectile_speed`, `projectile_damage`, `patrol_length` |
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

Total aceptado en `Objects`: **40** tipos.

<!-- END GENERATED: tipos de objeto -->
