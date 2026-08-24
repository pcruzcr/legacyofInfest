---
document_id: "LOI-EVENTMAP-052"
title: "Mapa de eventos del EventBus — auditoría del patrón observador"
aliases: ["Mapa de eventos", "EventMap", "Event Audit"]
tags: ["event-bus", "observador", "auditoria", "arquitectura"]
description: "Mapa completo de los eventos del EventBus: emisores, suscriptores, payloads y orden de despacho."
source: "src/engine/core/events.py, src/engine/core/event_bus.py"
date_processed: "2026-08-12"
---

# Mapa de eventos del EventBus

**ID del documento:** LOI-EVENTMAP-052
**Versión:** 1.1.0
**Estado:** ⚠️ Medido contra el árbol del **2026-07-16**, con correcciones del **2026-08-04** (§0) y del **2026-08-12** (esta versión). Ver §0.

> **AUD-455.** Traduce el documento y corrige el §1: decía 36 eventos
> definidos, 83 sitios de `emit` y 23 de `subscribe`. Recontado hoy por
> `grep` sobre `src/`: **65 eventos definidos, 103 sitios de `emit`, 36 de
> `subscribe`.** Ya eran erróneos antes de esta corrección — ninguno de los
> tres números cambió por el trabajo de esta sesión. Aplica además al §2 y al
> §3 las correcciones que el propio §0 (AUD-254) ya había documentado en
> prosa pero nunca se llevaron a las tablas — un lector que fuera directo a
> la tabla de un evento seguía leyendo el dato viejo.
>
> Lo que **no** se ha vuelto a verificar entrada por entrada en esta pasada:
> los ~40 eventos que el §0 no menciona (`VFX_CHARGE`, `SFX_PLAYER_JUMP`,
> etc.) — no hay evidencia de que hayan cambiado, pero tampoco se han vuelto
> a medir aquí; sus números de línea pueden haber corrido.

---

## 0. Qué de este documento ha caducado (AUD-254, medido 2026-08-04)

Este mapa se levantó el 16 de julio y no se ha vuelto a medir. Su §3 —«18
eventos huérfanos, ni emitidos ni suscritos»— **ya no es cierta**, y una lista
de huérfanos equivocada es peor que ninguna: manda a alguien a borrar cableado
que sí existe. Recuento de hoy, `grep` sobre `src/`:

**Dejaron de ser huérfanos** (tienen emisor desde que se escribió §3):
`MUSIC_STINGER` (`boss_base.py:336`), `SFX_PLAYER_PARRY` (`enemy_base.py`),
`SFX_UI_GAME_OVER` (`stage_scene.py`), `SFX_ENVIRONMENT_SCREEN_SHAKE` y
`SFX_BOSSES_PABURU_EYE_BEAM` (`boss_paburu.py`), `SFX_BOSS_HIT`
(`enemy_base.py`), `SFX_BOSS_PHASE_CHANGE` (`boss_base.py`).

**Se conectaron en AUD-255:** `SFX_PLAYER_HEAL`, `SFX_PLAYER_CROUCH`,
`SFX_ENVIRONMENT_ONE_WAY_PLATFORM`, `SFX_ENEMIES_PROJECTILE_HIT_WALL`. Los
cuatro tenían fichero, tabla y subtítulo, y les faltaba sólo el `emit`.

**Se conectaron en AUD-251 y AUD-256:** `ITEM_COLLECTED` y `FLAG_SET` (un
diálogo que regalaba un objeto no se lo daba a nadie) y `ACHIEVEMENT_UNLOCKED`
(el logro se veía y no se oía).

**Siguen sin emisor, y es una decisión, no un defecto (5):**
`SFX_BOSSES_GAVILAN_DIVE`, `SFX_BOSSES_GAVILAN_MASK_BEAM`,
`SFX_BOSSES_PABURU_WAVE`, `SFX_BOSSES_RELIC_APPEAR`, `SFX_BOSSES_REY_SPIT`,
`SFX_BOSSES_REY_SPLIT` — pertenecen a ataques de jefes de estudiantes.
`ACHIEVEMENT_PROGRESS` sigue reservado, como dice el propio código.

La recomendación de §6 que **sí sigue viva**: los SFX se suscriben sólo dentro
de `StageScene`, así que un sonido emitido desde un menú no suena.

---

## 1. Arquitectura del EventBus

La clase `EventBus` (`src/engine/core/event_bus.py`) implementa un patrón publicación/suscripción basado en cola:

1. **`emit(event_name, **data)`** — encola el evento (despacho diferido)
2. **`dispatch()`** — la llama `App` una vez por fotograma, antes del update de la escena; vacía la cola e invoca a todos los suscriptores
3. **`subscribe(event_name, callback)`** — registra un callback para un evento
4. **`unsubscribe(event_name, callback)`** — quita un callback

Eventos definidos en total: **65** (en `src/engine/core/events.py`)
Sitios de `emit` en total: **103**
Sitios de `subscribe` en total: **36**

---

## 2. Mapa de eventos (alfabético por nombre de evento)

### ACHIEVEMENT_PROGRESS
| Campo | Valor |
|-------|-------|
| **Emisor** | `Achievements._unlock()` (`src/engine/core/achievements.py:150`) |
| **Payload** | `achievement_id: str`, `progress: int`, `target: int` |
| **Suscriptores** | *(ninguno — reservado para UI futura)* |
| **Se dispara** | Cuando cambia el valor de progreso de un logro |

### ACHIEVEMENT_UNLOCKED
| Campo | Valor |
|-------|-------|
| **Emisor** | `Achievements._unlock()` (`src/engine/core/achievements.py:169`) |
| **Payload** | `achievement_id: str`, `name: str` |
| **Suscriptores** | AUD-256: conectado — `sonido.py` lo mapea a `"sfx_ui_stage_complete"`. Antes se veía y no se oía. |
| **Se dispara** | Cuando se desbloquea un logro por primera vez |

### BOSS_ATTACK
| Campo | Valor |
|-------|-------|
| **Emisor** | `BossVenado._do_stomp()` (`boss_venado.py:225,230,237,294`), `EnemyCaster` (`enemy_caster.py:147`), `EnemyBrute._do_attack()` (`enemy_brute.py:66`), `EnemyAssassin` (`enemy_assassin.py:100`) |
| **Payload** | `pattern: str`, `rect: pygame.Rect` |
| **Suscriptores** | StageScene — manejador `_play_sfx_named` (mapeado a `sfx_bosses_venado_*` vía `sfx_map`, en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando un jefe/minijefe hace un ataque telegrafiado |

### BOSS_PHASE_CHANGED
| Campo | Valor |
|-------|-------|
| **Emisor** | `BossBase._finish_phase_transition()` (`boss_base.py:164-179`) |
| **Payload** | `boss_name: str`, `phase: int`, `phase_name: str` |
| **Suscriptores** | `HUD._on_boss_phase_changed` (`hud.py:186`) |
| **Se dispara** | Cuando un jefe pasa a una nueva fase |

### CHECKPOINT_REACHED
| Campo | Valor |
|-------|-------|
| **Emisor** | `Checkpoint.activate()` (`checkpoint.py:68-70`) |
| **Payload** | `checkpoint_id: int` |
| **Suscriptores** | `HUD._on_checkpoint_reached` (`hud.py:187`) |
| **Se dispara** | Cuando el jugador toca un checkpoint por primera vez |

### ENEMY_DIED
| Campo | Valor |
|-------|-------|
| **Emisor** | `EnemyBase._die()` (`enemy_base.py:412`) |
| **Payload** | `entity_id: int`, `position: tuple[float, float]` |
| **Suscriptores** | StageScene `_on_enemy_died` (estallido de partículas), Achievements `_on_enemy_died` (`achievements.py:125`) |
| **Se dispara** | Cuando la vida de cualquier enemigo llega a 0 |

### FLAG_SET
| Campo | Valor |
|-------|-------|
| **Emisor** | Manejador de acción de `DialogueSystem` (`dialogue_system.py:315`) |
| **Payload** | `flag: str` |
| **Suscriptores** | AUD-251: conectado en `stage_parts/senales.py` (`_on_flag_set`) |
| **Se dispara** | Cuando un nodo de diálogo ejecuta una acción `set_flag` |

### HIDE_MESSAGE
| Campo | Valor |
|-------|-------|
| **Emisor** | `MessageBox.hide()` (`message_box.py:96`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | `MessageBox._on_hide_message` (`message_box.py:57`) |
| **Se dispara** | Cuando debe ocultarse la caja de mensajes |

### ITEM_COLLECTED
| Campo | Valor |
|-------|-------|
| **Emisor** | Manejador de acción de `DialogueSystem` (`dialogue_system.py:313`) |
| **Payload** | `item_id: str` |
| **Suscriptores** | AUD-251: conectado en `stage_parts/senales.py` — un diálogo que regalaba un objeto no se lo daba a nadie hasta esta corrección |
| **Se dispara** | Cuando un nodo de diálogo ejecuta una acción `give_item:` |

### MUSIC_STINGER
| Campo | Valor |
|-------|-------|
| **Emisor** | AUD-254: `BossBase._finish_phase_transition()` (`boss_base.py:415`) |
| **Payload** | `name: str`, `volume: float` |
| **Suscriptores** | `stage_parts/senales.py` `_on_music_stinger` (reproducción del sonido de acento musical), `subtitle_overlay.py` |
| **Se dispara** | Al terminar una transición de fase de jefe |

### PLAYER_DAMAGED
| Campo | Valor |
|-------|-------|
| **Emisor** | `Player.apply_damage()` (`player.py:334`) |
| **Payload** | `amount: float`, `source: tuple[float, float]` |
| **Suscriptores** | StageScene `_on_player_damaged` (partículas de sangre, sacudida de cámara, destello, viñeta, `stage_scene.py:357`), HUD `_on_player_damaged` (`hud.py:183`) |
| **Se dispara** | Cuando el jugador recibe daño de cualquier fuente |
| **Orden de despacho** | primero el manejador de StageScene (VFX), luego el de HUD (actualiza la barra de vida) |

### PLAYER_DIED
| Campo | Valor |
|-------|-------|
| **Emisor** | `Player.apply_damage()` (`player.py:343`), `HUD` (`hud.py:312`), `StageScene._kill_player()` (`stage_scene.py:788`), `HazardSystem` (`hazard_system.py:26`) |
| **Payload** | `pos: tuple[float, float]` (desde StageScene), o vacío (desde HUD) |
| **Suscriptores** | StageScene `_on_player_died` (partículas de muerte, `stage_scene.py:358`), SceneManager `_on_player_died` (temporizador de muerte, `scene_manager.py:43`), HUD `_on_player_died` (`hud.py:185`) |
| **Se dispara** | Cuando la vida del jugador llega a 0 o cae en un pozo de muerte |

### PLAYER_HEALED
| Campo | Valor |
|-------|-------|
| **Emisor** | `ProgressionSystem.process_checkpoints()` (`progression_system.py:39`), `Player.heal()` — indirect |
| **Payload** | `amount: int` |
| **Suscriptores** | HUD `_on_player_healed` (`hud.py:184`) |
| **Se dispara** | Cuando el jugador recibe curación (de un checkpoint o un objeto) |

### SAVE_REQUESTED
| Campo | Valor |
|-------|-------|
| **Emisor** | `ProgressionSystem.process_checkpoints()` (`progression_system.py:42`) |
| **Payload** | `stage_id: str`, `stage_index: int`, `checkpoint_x: float`, `checkpoint_y: float`, `health: float`, `max_health: float` |
| **Suscriptores** | StageScene `_on_save_requested` (auto-save, `stage_scene.py:454`) |
| **Se dispara** | Cuando el jugador llega a un checkpoint nuevo |

### SFX_BOSS_HIT
| Campo | Valor |
|-------|-------|
| **Emisor** | AUD-254: `EnemyBase._die()`/manejo de golpe (`enemy_base.py:521`), condicionado a `isinstance(self, BossBase)` |
| **Payload** | *(igual que SFX_ENEMY_HIT)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) a `"sfx_boss_hit"` |

### SFX_BOSS_PHASE_CHANGE
| Campo | Valor |
|-------|-------|
| **Emisor** | AUD-254: `BossBase._finish_phase_transition()`, indirectamente vía `boss_base.py:370` |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado en `stage_parts/sonido.py` a `"sfx_bosses_phase_change"` |

### SFX_BOSSES_* (7 eventos: GAVILAN_DIVE, GAVILAN_MASK_BEAM, PABURU_EYE_BEAM, PABURU_WAVE, RELIC_APPEAR, REY_SPIT, REY_SPLIT)
AUD-254: `PABURU_EYE_BEAM` dejó de estar huérfano — lo emite `src/stages/boss_paburu/boss_paburu.py:438`, mapeado en `sonido.py`. Los otros seis siguen sin emisor a propósito: pertenecen a ataques de jefes de estudiantes todavía no implementados.

### SFX_BOSSES_VENADO_CHARGE / STOMP / VINE
| Campo | Valor |
|-------|-------|
| **Emisor** | `BossVenado` emite `Events.BOSS_ATTACK`, mapeado vía `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Payload** | *(derivado del payload de BOSS_ATTACK)* |
| **Suscriptores** | Manejador SFX de StageScene (`stage_scene.py:424-439`) |
| **Se dispara** | Cuando el Venado Sagrado hace ataques de embestida / pisotón / enredadera |

### SFX_CHECKPOINT
| Campo | Valor |
|-------|-------|
| **Emisor** | `ProgressionSystem.process_checkpoints()` (`progression_system.py:35`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) a `"sfx_checkpoint"` |
| **Se dispara** | Cuando el jugador toca un checkpoint |

### SFX_ENEMIES_PROJECTILE_HIT_WALL
| Campo | Valor |
|-------|-------|
| **Emisor** | AUD-255: `EnemyShooter` (`enemy_shooter.py:143`) |
| **Payload** | `pos: tuple[float, float]` |
| **Suscriptores** | Mapeado en `stage_parts/sonido.py` a `"sfx_enemies_projectile_hit_wall"` |

### SFX_ENEMY_DIE_LARGE / SFX_ENEMY_DIE_SMALL
| Campo | Valor |
|-------|-------|
| **Emisor** | `EnemyBase._die()` (`enemy_base.py:418`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando muere un enemigo (LARGE para jefes/brutos, SMALL para caminantes/voladores) |

### SFX_ENEMY_HIT
| Campo | Valor |
|-------|-------|
| **Emisor** | `CollisionSystem.check_attack_hits()` (`collision_system.py:106`) |
| **Payload** | `pos: list[float]`, `damage: float` |
| **Suscriptores** | StageScene `_on_enemy_hit` (partículas de sangre, sacudida de cámara, `stage_scene.py:340`) |
| **Se dispara** | Cuando el ataque del jugador conecta con un enemigo |

### SFX_ENVIRONMENT_ONE_WAY_PLATFORM
| Campo | Valor |
|-------|-------|
| **Emisor** | AUD-255: `Player` (`player.py:1188`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado en `stage_parts/sonido.py` a `"sfx_environment_one_way_platform"` |

### SFX_ENVIRONMENT_SCREEN_SHAKE
| Campo | Valor |
|-------|-------|
| **Emisor** | AUD-254: `src/stages/boss_paburu/boss_paburu.py:451` |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado en `stage_parts/sonido.py` a `"sfx_environment_screen_shake"` |

### SFX_HAZARD_ZONE
| Campo | Valor |
|-------|-------|
| **Emisor** | `HazardSystem.update()` (`hazard_system.py:48`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando el jugador recibe daño de una zona de peligro |

### SFX_HIT_CONNECT
| Campo | Valor |
|-------|-------|
| **Emisor** | `CollisionSystem.check_attack_hits()` (`collision_system.py:121`) |
| **Payload** | `pos: list[float]`, `damage: float` |
| **Suscriptores** | StageScene `_on_hit_connect` (hit particles, damage numbers, `stage_scene.py:339`) |
| **Se dispara** | Cuando cualquier hitbox de ataque del jugador conecta (tras procesar los golpes por enemigo) |

### SFX_MENU_HOVER
| Campo | Valor |
|-------|-------|
| **Emisor** | `DemoMenuScene` (`demo_menu_scene.py:115`), `OptionsScene` (`options_scene.py:116`), `TitleScene` (`title_scene.py:121`), `WorldMapScene` (`world_map_scene.py:89`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando el usuario navega sobre un elemento del menú |

### SFX_MENU_CONFIRM
| Campo | Valor |
|-------|-------|
| **Emisor** | `DemoMenuScene` (`demo_menu_scene.py:118`), `OptionsScene` (`options_scene.py:130`), `TitleScene` (`title_scene.py:128`), `WorldMapScene` (`world_map_scene.py:93`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando el usuario confirma una selección de menú |

### SFX_MENU_CANCEL
| Campo | Valor |
|-------|-------|
| **Emisor** | `DemoMenuScene` (`demo_menu_scene.py:134`), `OptionsScene` (`options_scene.py:118`), `TitleScene` (`title_scene.py:132`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando el usuario cancela o descarta un menú |

### SFX_PLAYER_CROUCH
| Campo | Valor |
|-------|-------|
| **Emisor** | AUD-255: `states/grounded.py:178` |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado en `stage_parts/sonido.py` a `"sfx_player_crouch"` |

### SFX_PLAYER_DIE
| Campo | Valor |
|-------|-------|
| **Emisor** | `Player.apply_damage()` (`player.py:344`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando el jugador muere |

### SFX_PLAYER_FOOTSTEP
| Campo | Valor |
|-------|-------|
| **Emisor** | `WalkingState` (`states/grounded.py:83`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | En cada paso de la animación de caminar del jugador |

### SFX_PLAYER_HEAL
| Campo | Valor |
|-------|-------|
| **Emisor** | AUD-255: `Player.heal()` (`player.py:559`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado en `stage_parts/sonido.py` a `"sfx_ui_heart_restore"` |

### SFX_PLAYER_HURT
| Campo | Valor |
|-------|-------|
| **Emisor** | `Player.apply_damage()` (`player.py:348`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando el jugador recibe daño (pero no muere) |

### SFX_PLAYER_JUMP
| Campo | Valor |
|-------|-------|
| **Emisor** | `JumpingState` (`states/airborne.py:79`), `WallSlideState` (`states/wall.py:13`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando el jugador salta |

### SFX_PLAYER_LAND
| Campo | Valor |
|-------|-------|
| **Emisor** | `Player` physics update (`player.py:654`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando el jugador aterriza tras estar en el aire |

### SFX_PLAYER_LONG_ATTACK
| Campo | Valor |
|-------|-------|
| **Emisor** | los estados de ataque de `states/attack.py` |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando el jugador hace un ataque largo/pesado |

### SFX_PLAYER_PARRY
| Campo | Valor |
|-------|-------|
| **Emisor** | AUD-254: `EnemyBase` cuando un ataque de enemigo es parado (`enemy_base.py:783`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado en `stage_parts/sonido.py` a `"sfx_parry"` |

### SFX_PLAYER_SHORT_ATTACK
| Campo | Valor |
|-------|-------|
| **Emisor** | los estados de ataque de `states/attack.py` |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando el jugador hace un ataque corto/rápido |

### SFX_PROJECTILE_FIRE
| Campo | Valor |
|-------|-------|
| **Emisor** | `EnemyCaster` (`enemy_caster.py:180`), `EnemyArcher` (`enemy_archer.py:119`), `EnemyShooter` (`enemy_shooter.py:315`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando un enemigo dispara un proyectil |

### SFX_STAGE_BANNER
| Campo | Valor |
|-------|-------|
| **Emisor** | `StageScene` (`stage_scene.py:194`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando se muestra el rótulo con el nombre del escenario |

### SFX_STAGE_COMPLETE
| Campo | Valor |
|-------|-------|
| **Emisor** | `StageScene.check_stage_complete()` (`stage_scene.py:622,625`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado vía `sfx_map` de StageScene (en `stage_parts/sonido.py` desde AUD-290) |
| **Se dispara** | Cuando el jugador completa un escenario |

### SFX_UI_GAME_OVER
| Campo | Valor |
|-------|-------|
| **Emisor** | AUD-254: `StageScene` (`stage_scene.py:1255`) |
| **Payload** | *(ninguno)* |
| **Suscriptores** | Mapeado en `stage_parts/sonido.py` a `"sfx_ui_game_over"` |

### SHOW_MESSAGE
| Campo | Valor |
|-------|-------|
| **Emisor** | `HazardSystem.update()` — message triggers (`hazard_system.py:38`) |
| **Payload** | `text: str`, `duration: float` |
| **Suscriptores** | `MessageBox._on_show_message` (`message_box.py:56`) |
| **Se dispara** | Cuando el jugador entra en una zona de disparo de mensaje |

### STAGE_COMPLETE
| Campo | Valor |
|-------|-------|
| **Emisor** | `StageScene.check_stage_complete()` (`stage_scene.py:635`), `BossVenado.on_defeated()` — indirect |
| **Payload** | `stage_id: str` |
| **Suscriptores** | `SceneManager._on_stage_complete` (advance to next stage, `scene_manager.py:42`), `HUD._on_stage_complete` (`hud.py:188`) |
| **Se dispara** | Cuando se alcanza la salida del escenario o se derrota al jefe final |

### VFX_CHARGE
| Campo | Valor |
|-------|-------|
| **Emisor** | `ChargingState` (`states/ability.py:279`), `WallSlideState` (`states/wall.py:13`) |
| **Payload** | `pos: tuple[float, float]`, `level: int` |
| **Suscriptores** | StageScene `_on_vfx_charge` (partículas de carga, `stage_scene.py:360`) |
| **Se dispara** | Cuando el jugador carga un ataque |

### VFX_PARRY
| Campo | Valor |
|-------|-------|
| **Emisor** | `ParryState` (`states/ability.py:93`), `EnemyBase._on_parried()` (`enemy_base.py:526`), `EnemyCaster` (`enemy_caster.py:208`), `EnemyArcher` (`enemy_archer.py:147`), `EnemyShooter` (`enemy_shooter.py:204`) |
| **Payload** | `pos: tuple[float, float]` |
| **Suscriptores** | StageScene `_on_vfx_parry` (partículas de parry, sacudida de cámara, destello, bloom, `stage_scene.py:359`), Achievements `_on_parry` (`achievements.py:126`) |
| **Se dispara** | Cuando un parry del jugador conecta con un ataque enemigo |

### VFX_SLAM
| Campo | Valor |
|-------|-------|
| **Emisor** | `PlayerStates.SlamState` (`player_states.py:1268`) |
| **Payload** | `pos: tuple[float, float]` |
| **Suscriptores** | StageScene `_on_vfx_slam` (partículas de golpe de tierra, sacudida de cámara, `stage_scene.py:361`) |
| **Se dispara** | Cuando el jugador hace un golpe de tierra |

### VFX_ULTIMATE
| Campo | Valor |
|-------|-------|
| **Emisor** | `PlayerStates.UltimateState` (`player_states.py:798`) |
| **Payload** | `pos: tuple[float, float]` |
| **Suscriptores** | StageScene `_on_vfx_ultimate` (partículas de ataque especial, bloom, destello, sacudida, `stage_scene.py:362`) |
| **Se dispara** | Cuando el jugador usa el ataque especial/definitivo |

---

## 3. Eventos huérfanos (definidos pero nunca emitidos ni suscritos)

**AUD-455 — esta tabla decía 18 huérfanos; el §0 (AUD-254, 2026-08-04) ya
documentaba en prosa que 13 de esos 18 habían dejado de serlo, pero nunca se
actualizó esta tabla.** Quedan realmente **6** eventos sin emisor, y es una
decisión de diseño (ataques de jefes de estudiantes aún no implementados),
no un defecto:

| Evento | Notas |
|-------|-------|
| `SFX_BOSSES_GAVILAN_DIVE` | Jefe futuro |
| `SFX_BOSSES_GAVILAN_MASK_BEAM` | Jefe futuro |
| `SFX_BOSSES_PABURU_WAVE` | Jefe futuro |
| `SFX_BOSSES_RELIC_APPEAR` | Mecánica de jefe futura |
| `SFX_BOSSES_REY_SPIT` | Jefe futuro |
| `SFX_BOSSES_REY_SPLIT` | Jefe futuro |
| `ACHIEVEMENT_PROGRESS` | Reservado a propósito — el propio código lo dice (ver §0) |

Los siguientes **ya no son huérfanos** y sus entradas en §2 están corregidas
en esta versión: `PLAYER_HEALED` (unidireccional: HUD lo escucha pero sólo
lo emite la curación por checkpoint, no `Player.heal()` directamente — esto
sigue siendo cierto, no es un error, es la regla de negocio), `MUSIC_STINGER`,
`SFX_BOSS_HIT`, `SFX_BOSS_PHASE_CHANGE`, `SFX_BOSSES_PABURU_EYE_BEAM`,
`SFX_ENEMIES_PROJECTILE_HIT_WALL`, `SFX_ENVIRONMENT_ONE_WAY_PLATFORM`,
`SFX_ENVIRONMENT_SCREEN_SHAKE`, `SFX_PLAYER_CROUCH`, `SFX_PLAYER_HEAL`,
`SFX_PLAYER_PARRY`, `SFX_UI_GAME_OVER`, `ITEM_COLLECTED`, `FLAG_SET`,
`ACHIEVEMENT_UNLOCKED`.

---

## 4. Eventos sin definir (emitidos pero ausentes de la clase Events)

Esto documenta un problema histórico, ya cerrado: literales de cadena o referencias de atributo que existían en llamadas `emit`/`subscribe` pero no estaban definidas en `Events`.

| Literal de evento | Fichero | Línea | Acción tomada |
|---------------|------|------|-------------|
| `Events.ITEM_COLLECTED` | `dialogue_system.py` | 313 | ✅ Añadido a la clase `Events` (2026-07-16) |
| `Events.FLAG_SET` | `dialogue_system.py` | 315 | ✅ Añadido a la clase `Events` (2026-07-16) |

---

## 5. Mapa del orden de despacho a los suscriptores

Esta sección documenta el **orden** en que varios suscriptores reciben el mismo evento.

### PLAYER_DAMAGED
1. **StageScene._on_player_damaged** — genera partículas de sangre, sacude la cámara, destello, viñeta
2. **HUD._on_player_damaged** — actualiza la barra de vida

### PLAYER_DIED
1. **StageScene._on_player_died** — partículas de muerte, sacudida de cámara, destello
2. **HUD._on_player_died** — oculta el HUD
3. **SceneManager._on_player_died** — arranca el temporizador de muerte → escena de fin de partida
*(Nota: depende del orden de suscripción entre `StageScene.on_enter()`, `SceneManager.__init__` y `HUD.__init__`)*

### ENEMY_DIED
1. **StageScene._on_enemy_died** — genera partículas de muerte
2. **Achievements._on_enemy_died** — cuenta las bajas de enemigos

### STAGE_COMPLETE
1. **HUD._on_stage_complete** — reproduce la animación de fin de escenario
2. **SceneManager._on_stage_complete** — avanza al siguiente escenario o al menú

### VFX_PARRY
1. **StageScene._on_vfx_parry** — partículas de parry, sacudida, destello, bloom
2. **Achievements._on_parry** — cuenta los parries

---

## 6. Hallazgos y recomendaciones

### 6.1 Hallazgos

1. **Sin suscriptor para eventos SFX fuera de `StageScene`** — todos los eventos SFX se cablean sólo dentro de `StageScene`. Los eventos SFX de menú (`SFX_MENU_HOVER`, `SFX_MENU_CONFIRM`, `SFX_MENU_CANCEL`) funcionan porque usan la misma instancia de EventBus, pero dependen de que `StageScene` sea la escena activa.

2. **(Histórico, resuelto 2026-07-16) `ITEM_COLLECTED` y `FLAG_SET` no tenían constante de evento** — `DialogueSystem` los emitía vía `Events.ITEM_COLLECTED` y `Events.FLAG_SET` pero faltaban en la clase `Events`. Arreglado en esa auditoría; conectados a suscriptor real en AUD-251 (ver §0 y §2).

3. **(Histórico, parcialmente resuelto) Eventos huérfanos** — el §3 documentaba 18; hoy quedan 6, ver §3.

4. **(Histórico, resuelto en AUD-254) `MUSIC_STINGER` tenía suscriptor pero no emisor** — ahora lo emite `BossBase._finish_phase_transition()`.

5. **`PLAYER_HEALED` se emite con nombre de evento en crudo** — `ProgressionSystem.process_checkpoints()` usa `Events.PLAYER_HEALED`, pero `Player.heal()` **no** emite este evento directamente. Sólo lo dispara la curación por checkpoint. Esto sigue siendo así hoy — no es una regresión, es la regla de negocio actual, y su corrección (si se decide) es una decisión de diseño, no una limpieza de documentación.

### 6.2 Recomendaciones

1. 🔴 **Quitar los eventos huérfanos que quedan** (§3) o añadir una comprobación de lint que avise de eventos sin sitio de `emit`
2. ~~🟡 Conectar `MUSIC_STINGER` a las transiciones de fase de jefe~~ — hecho en AUD-254 (`BossBase._finish_phase_transition`)
3. 🟢 **Añadir pruebas de integración del lado del suscriptor** para todos los eventos que tienen emisor y suscriptor
4. 🟢 **Considerar un `unsubscribe_all(events, callback)`** en el EventBus para una limpieza más ordenada — ya existe (ver §1); revisar si cubre el caso que motivó esta recomendación
