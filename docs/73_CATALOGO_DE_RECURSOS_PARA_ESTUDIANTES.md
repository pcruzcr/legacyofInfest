---
document_id: "LOI-CATALOGO-73"
title: "Catálogo de recursos para construir niveles y juegos"
tags: ["estudiantes", "api", "catalogo", "tmx", "enemigos", "objetos", "gameplay"]
source: "docs/73_CATALOGO_DE_RECURSOS_PARA_ESTUDIANTES.md"
date_processed: "2026-08-02"
---

# Catálogo de recursos para construir niveles y juegos

Documento de curso. Inventario verificado contra el código en ejecución de todo
lo que un estudiante puede usar para construir su nivel o su juego: funciones,
métodos, estados, enemigos, objetos y elementos. Complementa el informe
`docs/70_INFORME_DE_AUDITORIA_VIVO.md` y la guía de mapas `docs/STAGE_CREATION.md`.

Regla del curso: **todo número de aquí sale de un comando**; donde el número no
se pudo medir, no se escribe.

---

## 0. Índice de números verificados

`30` estados de jugador · `25` acciones de entrada · `13` estados de IA ·
`8` arquetipos de enemigo · `35` especies del bestiario · `50` tipos de objeto
TMX (AUD-455: eran 34 el 2026-08-02, ver §3.1; actualizado 2026-08-30: 50) · `2` tipos de capa `Collision`
· `18` componentes ECS · `60` eventos en el enum `Events` + `5` de interacción
(`INTERACT_*`). Total `Objects` en runtime **115** (50+54), **117** con `Collision`.

---

## 1. El jugador

### 1.1. Los 30 estados (verificado en `src/framework/entities/player.py:171`)

Todas las mecánicas del personaje son estados de una máquina. El API pública es
el enum `PlayerState`:

| Grupo | Estados |
|---|---|
| Suelo | `IDLE`, `WALKING`, `CROUCHING`, `SLIDE` |
| Aire | `JUMPING`, `FALLING`, `AIR_CHASE`, `AERIAL_ATTACK`, `AERIAL_SLAM`, `GROUND_POUND` |
| Pared / bordes | `WALL_SLIDE`, `LEDGE_GRAB` |
| Cuerda / tirolesa | `CLIMBING`, `ZIPLINE` |
| Agua | `SWIMMING`, `SWIM_ATTACK` |
| Habilidades | `DASHING`, `PARRY`, `CHARGE_ATTACK`, `CHARGE_RELEASE`, `ULTIMATE`, `GRAB`, `THROW` |
| Ataque | `SHORT_ATTACK`, `LONG_ATTACK`, `DASH_ATTACK` |
| Daño | `HURT`, `DYING` |

> **Nota de coherencia:** los doc `04` y `60` mencionaban 19/25/26 según la
> edición. El código tiene **28** y es la fuente de verdad. `docs/71` decía «25
> concretos (+3 clases base)» antes de añadir `SWIM_ATTACK` y `GROUND_POUND`.

### 1.2. Física (en `src/engine/core/settings.py`)

| Magnitud | Valor |
|---|---|
| Vida máxima del jugador | `PLAYER_MAX_HEALTH = 5.0` (corazones) |
| Gravedad | `GRAVITY = 800.0` px/s² |
| Velocidad de pasos | `PLAYER_WALK_SPEED = 90.0` px/s |
| Impulso de salto | `PLAYER_JUMP_FORCE = -380.0` |
| Velocidad de caída | `PLAYER_FALL_SPEED = 500.0` |
| Dash | `PLAYER_DASH_SPEED = 200.0`, duración `_DASH_DURATION = 0.15` |
| Coyote time | `PLAYER_COYOTE_FRAMES = 6` (≈100 ms) |
| Saltos aéreos | `PLAYER_AIR_JUMPS = 1` |
| Buffer de salto | 8 fotogramas (`states/airborne.py:49`) |
| Envolvente de salto | altura 90,2 px (5,64 baldosas) × alcance 85,5 px (5,34) |

### 1.3. Entrada (25 acciones, `src/engine/input/action_map.py:14`)

`Action` enum: `MOVE_LEFT/RIGHT/UP/DOWN`, `JUMP`, `CROUCH`, `SHORT_ATTACK`,
`LONG_ATTACK`, `DASH`, `GRAB`, `RANGED_ATTACK`, `CONFIRM`, `CANCEL`, `PAUSE`,
`LEARN_MATH/PYSICS/COLLISION/FSM/RENDER/AUDIO/PERF/CONTROLS/HELP`,
`OPEN_BESTIARY`, `TOGGLE_MUTE`.

API de `InputManager` (`src/engine/input/input_manager.py`):
`is_action_just_pressed`, `is_action_pressed`, `is_action_held`,
`is_action_released`, `consume(action)`, `rebind(action, keys)`.

### 1.4. Daño y combate

`apply_damage(amount, source_position, knockback_force=150)` (`player.py:514`).
Los valores del daño van modulados por `DifficultyConfig` (iframe, knockback,
incoming/outgoing multipliers). Ataque corto/largo: 0,50/1,00 corazones, hitbox
20×16 y 36×20. Parry: 0,2 s (`states/ability.py:78`, constante `_PARRY_DURATION`).

---

## 2. Enemigos

### 2.1. Los 15 estados de IA (`src/framework/entities/enemy_base.py:53`)

`IDLE`, `PATROL`, `SEARCH`, `ALERT`, `CHASE`, `TELEGRAPHING`, `FIRING`,
`RECOVER`, `RETREAT`, `STUNNED`, `HURT`, `LAUNCHED`, `DYING`.

API base extendible (`EnemyBase`):
`set_collision_rects(rects, one_way=None)`, hooks `_patrol_behavior` /
`_alert_behavior`, `_player_in_range`, `death_timer`, `caja_ajustada()`,
`_INV_FLASH_INTERVAL`.

### 2.2. Los 8 arquetipos + constructores (`src/framework/entities/`)

Registro en `entity_factory.py:61-71` (`_ENTITY_REGISTRY`):

| Arquetipo | Constructor (firma verificada) |
|---|---|
| `EnemyWalker` | `(spawn, patrol_length=96, facing, patrol_speed=45, alert_speed=75, damage_on_contact=0.5, max_health=2.0, zone)` |
| `EnemyShooter` | `(spawn, fire_rate=0.5, projectile_speed=120, projectile_damage=0.5, patrol_length=0, max_health=3, damage_on_contact=0.25, zone)` — burst 2, aim predictivo |
| `EnemyFlying` | `(spawn, flight_mode="sine", flight_speed=60, sine_amplitude=28, sine_frequency=1.5, waypoints, max_health=1.5, zone, alert_flight_mode)` — strategy `SineFlight/Bézier/Waypoint/Chase/Dive` (`flight_strategies.py:307-311`) |
| `EnemyCharger` | `(spawn, max_health=4, damage_on_contact=1.5, charge_speed=250, zone)` — cicle WIND_UP→CHARGE→STUN |
| `EnemyArcher` | `(spawn, max_health=2.5, damage_on_contact=0.25, fire_rate=0.4, projectile_speed=90, projectile_damage=0.75, zone)` — arco parabólico |
| `EnemyBrute` | `(spawn, max_health=5, damage_on_contact=0.5, zone)` — shockwave telegrafiada |
| `EnemyCaster` | `(spawn, max_health=2, damage_on_contact=0.25, zone)` — `HomingOrb` |
| `EnemyAssassin` | `(spawn, max_health=1.5, damage_on_contact=0.25, zone)` — cloaking α, lunge 200px/s (dmg 1,0), retira 2 s |

### 2.3. Las 35 especies del bestiario (`bestiary_registry.py`)

Zona 1 (9): `WalkerInsect`, `FlyingBird`, `ShooterFrog`, `WalkerRaton`,
`FlyingCucaracha`, `ShooterCocinero`, `WalkerEstudiante`, `FlyingNotebook`,
`ShooterTiza`.

Zona 2 (13): `WalkerSerpientePequena`, `FlyingBoa`, `ShooterSerpienteArbol`,
`WalkerTerciopelo`, `ShooterVenomoLargo`, `FlyingTerciovolador`,
`WalkerGuardia`, `Cangrejo`, `Climber`, `FlyingBomber`, `Shielded`, `Swimmer`,
`TerrainShaper`.

Zona 3 (7): `WalkerGarza`, `FlyingHalcon`, `ShooterQuetzal`, `WalkerPalom`,
`ShooterBuitre`, `ArcherQuetzal`, `AssassinSombra`.

Zona 4 y buddies (6): `BruteGolemHielo`, `CasterHealer`, `ChargerWolf`,
`BuddyRino`, `BuddyExpresso`, `BuddyEnguarde` — más `Medusa`, `PezAbismal`,
`Summoner` distribuidos (ver `18_ENEMY_ROSTER.md` para asignación por zona).

Cada `SpeciesSpec` expone `build(spawn_position, **overrides)`; los overrides
del TMX ganan (`bestiary_registry.py:50-56`). El test `test_bestiary_roster.py`
comprueba doc ↔ código.

### 2.4. Jefes (`src/stages/boss_*`, `src/framework/entities/boss_base.py`)

- `BossVenado` (referencia, 2 fases): pisada, carga, lianas, esporas.
- `BossRey` (1 fase, `VENOM_SPIT`) — hitbox corregida en AUD-165.
- `BossGavilan` (clase parcial, fase orbital) — `stage3_4_boss_gavilan/`.
- `BossPaburu` (`STONE_SPIT` / `EYE_BEAM` / `EL_SELLO`).

---

## 3. Los objetos que el mapa TMX puede declarar

### 3.1. Tipos de capa «Objects» — **50 tipos** (AUD-455: eran 34 el 2026-08-02; 50 en 2026-08-30)

`PlayerSpawn`, `Checkpoint`, `NextTrigger`, `MessageTrigger`,
`MessageTrigger_Once`, `HazardZone`, `DeathPit`, `CameraLock`, `Waypoint`,
`Light`, `AmbientLightZone`, `MusicZone`, `CameraZoomZone`, `Cutscene`, `PushBlock`, `BreakableBlock`, `Pickup`, `Key`, `Door`,
`LockedDoor`, `Cage`, `Chest`, `EventTrigger`, `Objective`, `WindZone`,
`FrictionZone`, `Conveyor`, `LaserZone`, `ShockwaveZone`, `WaterZone`,
`MovingPlatform`, `RhythmBlock`, `SinkingPlatform`, `Spring`, `Guard`,
`Stalker`, `ScrollZone`, `WarpZone`, `Slope`, `Vine`, `VineSwing`, `LianaSalto`, `RopeSwing`, `Zipline`, `BossSpawn`, `ArenaZone`,
`PressurePlate`, `PlacaDePresion`, `PlacaPresion`, `Boton`, `SecretRoom`, `SecretExit`.

> **AUD-455 (2026-08-13).** Esta lista y su cuenta («34 tipos») son del
> 2026-08-02 y no incluían `Objective` (AUD-400), `ScrollZone` (AUD-249),
> `WarpZone`, `Slope` (AUD-297) ni `BossSpawn` (AUD-259) — los cinco añadidos
> después de esa fecha. La lista viva y verificada por CI es el bloque
> `GENERATED` de `STAGE_CREATION.md` §«Tipos estructurales» (50 tipos en 2026-08-30:
> `AmbientLightZone`, `MusicZone`, `CameraZoomZone`, `ArenaZone`, `VineSwing`/`LianaSalto`/`RopeSwing`,
> `PressurePlate`/`PlacaDePresion`/`PlacaPresion`/`Boton`, `SecretRoom`/`SecretExit`), que es
> de donde sale la corrección de arriba.

Propiedades por tipo (default) — ver tabla completa de `STAGE_CREATION.md`:

| Tipo | Propiedades (default) |
|---|---|
| `Pickup` | `item_id` (oblig), `automatico` (True), `mensaje` |
| `Door`/`Cage`/`LockedDoor` | `key_id`, `consume_llave` (False), `evento`, `abre_con` (AUD-132), `cierra_en` (0) |
| `EventTrigger` | `evento`, `automatico`, `una_vez` |
| `HazardZone` | `damage` (0.25), `sube`/`sube_hasta`, `arranca_con` |
| `Cutscene` | `guion` (obligatorio, AUD-136) |
| `Spring` | `impulso` (-520), `rearme` (0.15) |
| `WindZone` | `fuerza_x`, `fuerza_y`, `periodo` |
| `FrictionZone`/`Conveyor` | `multiplicador` (frena, nunca > 1), `inercia` (resbala, AUD-522), `material`, `arrastre` |
| `LaserZone`/`ShockwaveZone` | `encendido` (1), `apagado` (1), `desfase` |
| `WaterZone` | `corriente_x/y` |
| `MovingPlatform` | `destino_dx/dy`, `velocidad` (40), `espera`, `atravesable` |
| `RhythmBlock` | `visible_seg` (1), `oculto_seg` (1), `desfase`, `patron` ("x.x.") |
| `SinkingPlatform` | `retraso` (0.4), `velocidad_caida` (90), `reaparece_en` (3) |
| `Guard` | `mira_x/y`, `alcance` (160), `semiangulo` (30), `barrido`, `vel` |
| `Stalker` | `velocidad` (55), `distancia_retirada` (480), `reaparicion` (6) |
| `Vine` | `ancho_de_agarre` (10), `velocidad` (70) |
| `Zipline` | `destino_dx` (96), `destino_dy` (64), `velocidad` (190), `radio_de_enganche` (14), `solo_de_bajada` (True) |

### 3.2. Capa `Collision`

`COLLISION_OBJECT_TYPES = ("Platform", "Solid")` (`tmx_diagnostics.py:109`).
`Platform` = plataforma atravesable desde abajo; cualquier otro valor o la
ausencia = suelo sólido.

### 3.3. Componentes ECS (18, en `src/framework/ecs/components.py`)

`Transform`, `Velocidad`, `Solido`, `Salud`, `EsJugador`, `Resorte`,
`ZonaDeViento`, `ZonaDeFriccion`, `ZonaLetalTemporizada`, `ZonaDeAgua`,
`PlataformaMovil`, `BloqueRitmico`, `PlataformaHundible`, `Liana`, `Tirolesa`,
`ConoDeVision`, `Alerta`, `Acosador`.

`World` (`ecs/world.py`), `Sistema = Callable[[World, float], None]`, `Fase`,
`Planificador` (`ecs/scheduler.py`), pooling en `bullet_swarm.py`
(`EnjambreDeBalas`, 4096).

---

## 4. Sistemas que se activan solos (sin escribir código)

| Sistema | Clases / archivo | Qué hace |
|---|---|---|
| Interactuables | `interactable_system.py`, `Recogible`/`Cerradura`/`Cofre`/`Disparador` | llaves, puertas, cofres, triggers |
| Checkpoints | `checkpoint.py` | emite `Events.CHECKPOINT_REACHED` |
| Progresión | `progression_system.py` | guarda/respawn en checkpoints |
| Hazards | `hazard_system.py` | inundación (`sube`/`sube_hasta`) |
| Corte de nivel | `level_mechanics.py` | control de nado, scroll forzado |
| Bloques | `bloques.py` | `BloqueEmpujable`, `BloqueDestructible` |
| Cámara | `camera.py` | lerp 8,0, lock, parallax, shake |
| Día/noche/estaciones | `day_night.py` / `seasons.py` | `LuzDelDia`, `Estacion` |
| Cutescena | `cutscene_*.py` | mini-lenguaje de guión |
| Speedrun | `speedrun_mode.py` | cronómetro + fantasmas (`GhostData`) |
| Fast-travel | `dynamic_music.py` | música por intensidad |

---

## 5. Eventos del bus

Enum `Events` con **60 entradas** (`src/engine/core/events.py`), más **5 de
interacción** emitidos por `interactable_system.py`:

Jugador / enemigo: `PLAYER_DAMAGED`, `PLAYER_HEALED`, `PLAYER_DIED`,
`ENEMY_DIED`, `BOSS_ATTACK`, `BOSS_PHASE_CHANGED`. Nivel: `STAGE_COMPLETE`,
`CHECKPOINT_REACHED`, `ITEM_COLLECTED`, `FLAG_SET`, `SAVE_REQUESTED`. UI / narración:
`SHOW_MESSAGE`, `HIDE_MESSAGE`, `DIALOGUE_FINISHED`, `ACHIEVEMENT_UNLOCKED`,
`ACHIEVEMENT_PROGRESS`. SFX (41): `SFX_PLAYER_JUMP/LAND/FOOTSTEP`, `SFX_HIT_CONNECT`,
`SFX_PROJECTILE_FIRE`, `SFX_CHECKPOINT`, `SFX_BOSS_HIT`, `SFX_BOSSES_*`… VFX:
`VFX_PARRY`, `VFX_CHARGE`, `VFX_SLAM`, `VFX_ULTIMATE`, `VFX_BUBBLE`.

Interacción (5): `INTERACT_ITEM_PICKED`, `INTERACT_LOCK_OPENED`,
`INTERACT_LOCK_BLOCKED`, `INTERACT_CHEST_OPENED`, `INTERACT_TRIGGER_FIRED`.

Suscripción clásica: `event_bus.subscribe(Events.STAGE_COMPLETE, mi_fn)`.
El bus es con referencias débiles y sin singleton (`core/event_bus.py`, AUD-019).

---

## 6. VFX, ambiente, y post-procesado

| Sistema | API pública | Archivo |
|---|---|---|
| Partículas | `ParticleEmitter.emit/emit_directed`, `BurstConfig` | `particle_system.py` |
| Luz | `LightSource(radius, color, flicker)` + `LightSystem` | `lighting.py` |
| Impacto | `HitEffects.SPARK/DEATH/PARRY/…` + `get_for_damage` | `hit_effects.py` |
| Números | `DamageNumberManager` | `damage_numbers.py` |
| Clima | `WeatherSystem.clear/rain/snow/fog/storm` | `weather_system.py` |
| Ambiente | `AmbientParticleSystem` (dust/leaves/embers/spores/ash) | `ambient_particles.py` |
| Estela | `TrailSystem` | `trail_system.py` |
| Post | `flash`, `set_vignette`, `set_bloom`, `set_tint`, `set_motion_blur`, `set_color_grading`, daltónico | `post_processing.py` |
| Niebla de guerra | `fog_of_war.py` (prop TMX `fog_of_war`) | — |
| Efecto de agua | `water_effect.py` (prop `water_effect`) | — |
| Transiciones | `start_fade_in/out`, `start_wipe`, `start_slide`, `start_circle` | `scenes/transition_manager.py` |

---

## 8. Meta-progresión y datos

- Guardado: `SaveManager.save/load/delete/list_slots/has_saves/newest_slot`
  (`core/save_manager.py`), `SaveData` con 5 slots `SAVE_VERSION=2`.
- Preferencias: `UserSettings.load/save/reset/preferencia`.
- Inventario: `Inventory.collect/has/count/get_total_*_bonus`.
- Logros: `AchievementSystem.progress/mark`.
- Progreso académico del curso: `ProgresoAcademico`, `SesionAcademica`.
- Currículo: `curriculum.PLAN` (10 unidades).

---

## 9. Advertencias de coherencia (doc ↔ código) para el estudiante

1. **Estados del jugador**: el código tiene **28**, los docs variaban 19/25/26/28 (actualizado 2026-08-30).
2. **Doble salto**: el código lo permite (1), el doc `04 §3` lo prohíbe.
3. **`detection_range_x` por especie no se aplica** — se usa la del arquetipo.
4. **`patrol_speed`/`alert_speed`/`fire_rate`** documentados para
   Brute/Caster/Assassin `no` son aceptados por sus constructores.
5. **Boss Gavilán**: el docs «no existía», el código sí.
<!-- cita-historica -->
6. **`Message` vs `MessageTrigger`**: el TMX solo acepta
   `MessageTrigger`(_Once); usar `Message` produce un error.
<!-- /cita-historica -->
7. **Conteos de la doc inconciliables**: `60` decía 78/37, `62` decía 104/54 (2026-08-30); el código tiene **106 tipos declarables** (50 + 54 + 2 collision, ver §3.1) y
   30 estados de jugador (ver §1.1).

---

## Documentos relacionados

- `docs/70_INFORME_DE_AUDITORIA_VIVO.md` — revisión de juego y auditoría vivas
- `docs/STAGE_CREATION.md` — cómo crear un mapa (generado, al día)
- `docs/18_ENEMY_ROSTER.md` — las 21 especies, verificadas
- `docs/04_PLAYER_SPEC.md` — especificación del jugador
- `docs/60_GUIA_COMPLETA_DEL_MOTOR.md` — guía completa
- `docs/22_API_CONTRACTS.md` — contratos de API