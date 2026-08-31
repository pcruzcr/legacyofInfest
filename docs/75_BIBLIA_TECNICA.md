---
document_id: "LOI-BIBLIA-075"
title: "Biblia Técnica de Legacy of InFest — Referencia Exhaustiva para Usuarios"
tags: ["reference", "api", "user-guide", "cli", "tests"]
description: "Referencia única que cruza la documentación contra el código: mecánicas, estados del jugador, enemigos, jefes, diseño de niveles, efectos, API completa del framework y del motor, CLI, scripts y pruebas. Incluye auditoría implementado/huérfano/a medias."
source: "docs/75_BIBLIA_TECNICA.md"
date_processed: "2026-08-04"
---

# Biblia Técnica de Legacy of InFest

**Documento:** 75 · **Versión:** 1.0.0 · **Estado:** Referencia viva
**Audiencia:** Estudiantes, asistentes de enseñanza, profesor y cualquier usuario del motor.
**Garantía:** Todo lo que dice este documento fue verificado contra el código en `src/` o contra
pruebas que se ejecutan en CI. Cuando una fuente documental dice otra cosa, este documento lo
señala y gana el código (regla de precedencia de `CLAUDE.md` §5).

---

## 0. Cómo usar este documento

| Sección | Responde |
|---|---|
| §1 | ¿Cómo instalo, corro y pruebo el juego? |
| §2 | ¿Qué comandos CLI tiene el motor? |
| §3 | ¿Cuáles son los controles? |
| §4 | ¿Qué hace el jugador? (30 estados, física, combate, habilidades) |
| §5 | ¿Qué enemigos existen y cómo se programan? |
| §6 | ¿Qué jefes hay y qué API usan? |
| §7 | ¿Cómo diseño un nivel? (TMX: capas, objetos, propiedades) |
| §8 | ¿Qué interactivos y mecánicas de nivel hay? |
| §9 | ¿Qué efectos visuales puedo usar? |
| §10 | ¿Qué hace la tubería de post-procesado? |
| §11 | ¿Qué es el ECS y cómo se usa? |
| §12 | API completa del **framework** (todas las funciones) |
| §13 | API completa del **engine** (todas las funciones) |
| §14 | ¿Qué escenas existen? |
| §15 | Sistemas transversales (eventos, guardado, economía, logros…) |
| §16 | Herramientas de procesamiento académico (filtros, visión, ML) |
| §17 | Todos los **scripts** de línea de comandos |
| §18 | Todas las **tools** de generación de assets |
| §19 | La **suite de pruebas** y cómo correrla |
| §20 | CI y validadores |
| §21 | Auditoría: **implementado / huérfano / a medias** |
| §22 | Brechas abiertas (GAPs) y advertencias |
| §23 | Glosario |

**Fuentes de verdad (orden):** código y pruebas que pasan → `62_ESTADO_DEL_PROYECTO.md` →
`63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md` y `KNOWN_GAPS.md` → `03_ARCHITECTURE.md`,
`22_API_CONTRACTS.md`, `23_DATA_SCHEMAS.md` → specs de dominio → diseño.

---

## 1. Arranque rápido

```powershell
# 1. Instalar (la única vía recomendada)
pip install -e ".[dev]"

# 2. Correr el juego
python main.py

# 3. Probar
pytest                      # suite completa (~2.872 casos, CI)
pytest tests/test_player_physics.py -v
pytest tests/ -k "collision"
```

**Requisitos:** Python >= 3.11 (CI corre 3.11/3.12/3.13). En entornos sin pantalla:

```powershell
$env:SDL_VIDEODRIVER="dummy"; $env:SDL_AUDIODRIVER="dummy"; $env:PYGAME_HIDE_SUPPORT_PROMPT="1"
```

**Extras opcionales** (el motor degrada con elegancia sin ellos): `[accel]` (numba + ModernGL),
`[scripting]` (lupa, IA en Lua), `[audiotools]` (pydub), `[build]` (pyinstaller/nuitka).

> **AUD-455/AUD-457 — el estado de esta afirmación cambió mientras se auditaba.**
> Esta sección decía "scikit-learn es dependencia dura de `[dev]` pero la IA del juego
> funciona sin él cayendo a heurística determinista (invariante 7)". A principios de esta
> auditoría eso era falso —verificado contra el código—: `SquadBrain._decide_batch`
> importaba `ai_predictor` sin `try`/`except`, y como `ai_predictor.py` importa sklearn a
> nivel de módulo, un sklearn ausente habría lanzado `ImportError` en el primer lote de
> decisiones, no degradado con elegancia.
>
> Con el trabajo AUD-456/AUD-457 (`src/framework/entities/tactica_por_reglas.py`,
> `precarga_ia.py`, y el `try: from ...ai_predictor import get_predictor / except
> ImportError` que ahora tiene `squad_brain._decide_batch`), la reserva **sí es real y
> alcanzable**: la heurística vive en un módulo sin ninguna dependencia de sklearn, y
> `SquadBrain` cae a ella tanto si `ia_lista()` dice que la carga aún no terminó como si
> la importación de `ai_predictor` falla. `scikit-learn` sigue en
> `[project.dependencies]` de `pyproject.toml` —es decir, sigue siendo obligatoria para
> instalar el proyecto— pero la invariante 7 habla de comportamiento en **runtime**, no de
> instalación: hoy, si el intérprete no tuviera sklearn disponible, la IA de enemigos
> seguiría funcionando por reglas en vez de fallar. La invariante describe correctamente
> el comportamiento actual.

---

## 2. CLI del juego (`main.py`)

| Comando | Efecto |
|---|---|
| `python main.py` | Arranque normal: App → Splash → Title → Tutorial → Story → Stage0… |
| `python main.py --stage <id>` | Lanza un nivel directo (`--stage stage1_2_la_soda`) |
| `python main.py --boss <id>` | Lanza un jefe directo (`--boss boss_rey`, módulo `..._scene`) |

Los 16 niveles por id: `stage0`, `stage_mecanicas`, `stage1_1`, `stage1_2_la_soda`,
`stage1_3_las_aulas`, `stage1_4_boss_venado` (carpeta `boss_venado`), `stage2_1` (carpeta
`stage2_1_oficinas`), `stage2_2`, `stage2_3` (carpeta `lobby_datacenter`), `stage2_4_boss_rey`
(carpeta `boss_rey`), `stage3_1_la_entrada_de_piedra`, `stage3_2` (carpeta `hall`),
`stage3_3_el_patio`, `stage3_4_boss_gavilan`, `stage4_1`, `stage4_2_boss_paburu` (carpeta
`boss_paburu`).

> **AUD-455.** Esta lista decía `stage3_1` a secas; la carpeta real es
> `stage3_1_la_entrada_de_piedra` (así lo dice también su propio
> `assignment_id` en el README) — `python main.py --stage stage3_1` fallaría
> con `ModuleNotFoundError`, porque `main.py` construye la ruta de import
> literalmente con el valor de `--stage`. También existe
> `src/stages/stage_cenital/` (sin `README.md`, aparentemente un laboratorio
> de vista cenital, no un escenario numerado de la progresión) que no
> aparece en esta lista de 16; no está claro si falta aquí a propósito o por
> descuido — se deja anotado en vez de adivinar.

**Variables de entorno útiles:**

| Variable | Efecto |
|---|---|
| `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy` | Headless (CI, servidores) |
| `PYGAME_HIDE_SUPPORT_PROMPT=1` | Silencia el banner de pygame |
| `LOI_DISPLAY_SCALE` | Escala de ventana |
| `SIN_BICHOS` (stage1_1), `LOI_SIN_ENEMIGOS` (stage2_2) | Quita enemigos para depurar |
| `APPDATA` / `XDG_CONFIG_HOME` / `XDG_CACHE_HOME` | Ubicación de preferencias y cachés |
| ~~`LOI_TOP_BAR_H`, `LOI_PANEL_W`~~ | **Retiradas (AUD-312).** Nunca funcionaron: la función que las habría leído no tenía llamante y las constantes se calculan de `settings`. El kit de demos no se ajusta desde el entorno |

---

## 3. Controles (por defecto, re-mapeables en KeybindingScene)

| Acción (`Action`, `src/engine/input/action_map.py`) | Teclas |
|---|---|
| `MOVE_LEFT` / `MOVE_RIGHT` | ←/A · →/D |
| `MOVE_UP` / `MOVE_DOWN` | ↑/W · ↓/S |
| `JUMP` | Espacio · ↑ · W |
| `CROUCH` | ↓ · S |
| `DASH` | Shift izq · Shift der · Alt izq |
| `GRAB` | G · C |
| `RANGED_ATTACK` (arco) | F · V |
| `SHORT_ATTACK` | Z · J |
| `LONG_ATTACK` | X · K |
| `CONFIRM` | Enter · Espacio · Z |
| `CANCEL` | Escape · X |
| `PAUSE` | Escape · P |
| `LEARN_MATH` … `LEARN_HELP` | F2 … F10 (paneles de teoría) |
| `OPEN_BESTIARY` | Tab |
| `TOGGLE_MUTE` | M |

**Mando (gamepad):** stick izquierdo = mover; A=salto, B=ataque corto, X=ataque largo, Y=agachar,
LB=agarrar, RB=arco, START=pausa, SELECT/BACK=cancelar. `CONTROLLER_DEADZONE = 0.25`.

**Controles en escenas académicas:** Q = quiz, C = panel de código fuente, T = tutorial de la demo,
F4 = overlay de colisiones, I = overlay de máscaras/kernels (vision_demo).

---

## 4. El jugador — mecánicas y estados

### 4.1 Estados (26, `PlayerState` en `src/framework/entities/player.py`)

| Grupo | Estados |
|---|---|
| Suelo | `IDLE` `WALKING` `CROUCHING` `SLIDE` |
| Aire | `JUMPING` `FALLING` `AIR_CHASE` `AERIAL_ATTACK` `AERIAL_SLAM` |
| Pared/borde | `WALL_SLIDE` `LEDGE_GRAB` |
| Cuerda | `CLIMBING` (liana) `ZIPLINE` (tirolesa) |
| Agua | `SWIMMING` |
| Habilidades | `DASHING` `PARRY` `CHARGE_ATTACK` `CHARGE_RELEASE` `ULTIMATE` `GRAB` `THROW` |
| Ataque | `SHORT_ATTACK` `LONG_ATTACK` `DASH_ATTACK` |
| Daño | `HURT` `DYING` |

Cada estado es una clase en `src/framework/entities/states/` (`IdleState`, `SwimmingState`, …)
con `enter(player)`, `update(player, dt, input_manager)`, `exit(player)`. La máquina vive en
`Player._change_state_instance()`; todo el estado transitorio está en el dataclass
`PlayerStateData` (`player_state.py`), accesible con prefijo `_` sobre el Player.

### 4.2 Física y constantes (`src/engine/core/settings.py`)

| Constante | Valor | Nota |
|---|---|---|
| `GRAVITY` | 800 px/s² | |
| `PLAYER_WALK_SPEED` | 90 px/s | |
| `PLAYER_JUMP_FORCE` | −380 px/s | |
| `PLAYER_MAX_FALL_SPEED` | 500 px/s | velocidad terminal |
| `PLAYER_COYOTE_FRAMES` | 6 (~100 ms) | coyote time |
| Buffer de salto | 8 frames (~130 ms) | |
| `PLAYER_AIR_JUMPS` | 1 | salto doble EXISTE en el código |
| `PLAYER_DASH_SPEED` | 200 px/s · 0.15 s | 1 dash aéreo |
| `PLAYER_MAX_HEALTH` | 5.0 corazones | |
| Altura de salto medida | ~72–90 px (5.64 tiles) | avance 5.34 tiles |

> **Advertencia medida (GAP-024):** el salto del motor sube más de lo que avanza
> (5.64 vs 5.34 tiles). Un hueco de 4 tiles etiquetado "cómodo" por el calificador es
> imposible con input natural. Véase §22.

### 4.3 Combate

| Acción | Daño | Hitbox | Notas |
|---|---|---|---|
| `SHORT_ATTACK` | 0.50 | 20×16 | 0.15 s |
| `LONG_ATTACK` | 1.00 | 36×20 | 0.40 s |
| Combo | ×1.0 → ×1.5 → ×2.0 | | ventana 0.5 s |
| `DASH_ATTACK` / `AERIAL_SLAM` | | | variantes aéreas |
| `PARRY` | — | | ventana 0.2 s; aturde al enemigo 0.9 s; desvía proyectiles; contra jefes parriables aturde 1.2 s |
| `CHARGE_ATTACK` | | | 3 niveles de carga (1.0 s máx.): `[(0.5,1.0),(1.0,1.5),(1.5,2.0)]` |
| `GRAB`/`THROW` | | | agarre de enemigo |
| `ULTIMATE` | | | medidor especial (solo sube al consumir un hit con la hitbox) |
| `RANGED_ATTACK` (arco) | | | munición, cadencia, potencia 0–1 al tensar, trayectoria punteada, recarga por golpe |

**API pública del Player** (`player.py`): `current_health`, `max_health`, `walk_speed`,
`damage_multiplier`, `hurtbox`, `state`, `active_hitbox`, `current_attack_damage`,
`apply_damage(amount, source_position, knockback_force=150)`, `heal`, `set_health`,
`gain_special`, `ultimate_listo`, `set_spawn(position)` (única vía sancionada de reposicionar),
`update(dt, collision_rects, input_manager, one_way_rects)`, `draw(surface, camera_offset)`.

**Estamina (opt-in):** activada por la propiedad de mapa `estamina` (0 = off; 100 = 4 dashes +
0.6 s de pausa). `estamina_activa()`, `hay_estamina_para_correr()`, `gastar_estamina(cantidad)`,
`recuperar_estamina(dt)`, `activar_estamina(maximo)`.

**Habilidades como ítems** (caen de jefes, slot `skill`): `skill_double_jump` (cae de `BossRey`),
`skill_dash` (de `BossVenado`), `skill_parry` (**nadie lo suelta todavía**). El bloqueo de
habilidades está apagado por defecto (`PLAYER_SKILLS_REQUIRE_UNLOCK = False`).

---

## 5. Enemigos

### 5.1 Estados de IA (13, `EnemyState` en `enemy_base.py`)

`IDLE` `PATROL` `SEARCH` `ALERT` `CHASE` `TELEGRAPHING` `FIRING` `RECOVER` `RETREAT`
`STUNNED` `HURT` `LAUNCHED` `DYING`
(prioridad: DYING > LAUNCHED > HURT > TELEGRAPHING > FIRING > ALERT > PATROL, con histéresis de
des-aggro por `deaggro_margin`.)

### 5.2 Los 8 arquetipos (`src/framework/entities/`)

| Clase | Constructor (parámetros clave) | Comportamiento |
|---|---|---|
| `EnemyWalker` | `spawn_position, patrol_length=96, facing='right', patrol_speed=45, alert_speed=75, damage_on_contact=0.5, max_health=2, zone=0` | Patrulla horizontal con detección de borde; embiste en alerta |
| `EnemyFlying` | `flight_mode='sine', flight_speed=60, sine_amplitude=28, sine_frequency=1.5, waypoints=None, alert_flight_mode=None` | Estrategias: `SineFlight`, `BezierFlight` (Catmull-Rom), `WaypointPatrol`, `ChaseFlight`, `DiveFlight` |
| `EnemyShooter` | `fire_rate=0.5, projectile_speed=120, projectile_damage=0.5, patrol_length=0, max_health=3` | Apunta, telegrafía y dispara ráfagas; estacionario si `patrol_length=0`; proyectiles parriables |
| `EnemyCharger` | `max_health=4, damage_on_contact=1.5, charge_speed=250` | Ciclo WIND-UP (telegrafía) → CHARGE → STUN; parry cancela la carga |
| `EnemyArcher` | `fire_rate=0.4, projectile_speed=90, projectile_damage=0.75` | Flechas en arco con puntería predictiva |
| `EnemyBrute` | `max_health=5, damage_on_contact=0.5` | Onda de choque telegrafiada (¡el GDD dice 6.0 de HP, el código 5.0!) |
| `EnemyCaster` | `max_health=2, damage_on_contact=0.25` | Orbes guiados (`HomingOrb`) |
| `EnemyAssassin` | `max_health=1.5, damage_on_contact=0.25` | Invisibilidad, estocada 200 px/s (1.0 de daño), retirada 2 s |

**Proyectiles:** `Projectile(spawn_position, velocity, damage, lifetime=3.0, gravity=0.0)` y
`HomingOrb(spawn_position, velocity, damage, lifetime=3.0)` (método `set_player_ref(rect)`).

### 5.3 API de `EnemyBase` (lo que el usuario puede llamar)

```python
EnemyBase(spawn_position, max_health, damage_on_contact=0.5, contact_knockback=120.0,
          detection_range_x=160.0, detection_range_y=64.0, hurt_duration=0.25,
          invincibility_duration=0.5, deaggro_margin=32.0, event_bus=None)
```

Público: `update(dt)`, `draw(surface, offset)`, `apply_hit(damage, source_position)`,
`caja_ajustada(margen_x=0, margen_y=0)`, `set_collision_rects(rects, one_way=None)`,
`set_player_ref(player_rect)`, `stun(duration=0.8)`, `begin_recovery(duration=None)`,
`death_timer()`. Ganchos de extensión (los estudiantes NO sobreescriben `update`/`draw`):
`_patrol_behavior(dt)`, `_alert_behavior(dt)`, `_firing_behavior(dt)`, `_idle_behavior`,
`_search_behavior`, `_recover_behavior`, `_retreat_behavior`, `_pre_update`, `_post_update`,
`_get_animation_key`, `_build_hitbox`, `_build_hurtbox`, `_check_player_contact(player)`,
`_cancelar_ataque_en_curso`, `_should_retreat`, `_aturdimiento_por_parry`.
Consulta: `_player_in_range(player_rect, margin=0.0)`.

### 5.4 Las 21 especies con nombre (`bestiary_registry.py`, `SPECIES`)

| Zona | Especies |
|---|---|
| 1 | `WalkerInsect` `FlyingBird` `ShooterFrog` `WalkerRaton` `FlyingCucaracha` `ShooterCocinero` `WalkerEstudiante` `FlyingNotebook` `ShooterTiza` |
| 2 | `WalkerSerpientePequena` `FlyingBoa` `ShooterSerpienteArbol` `WalkerTerciopelo` `ShooterVenomoLargo` `FlyingTerciovolador` `WalkerGuardia` |
| 3 | `WalkerGarza` `FlyingHalcon` (`alert_flight_mode="dive"`) `ShooterQuetzal` `WalkerPalom` `ShooterBuitre` |

Cada especie es un `SpeciesSpec(species_id, base, zone, display_name, params)` con `build(spawn, **overrides)`
(los overrides del TMX ganan a la tabla). `get(id)`, `by_zone(zone)`, `species_ids()`. En el TMX se
spawnean por nombre de tipo en la capa Objects. `entity_factory.ensure_registered()` debe correr una
vez (lo hace `App.__init__`) para registrarlas en el `StageLoader`.

---

## 6. Jefes

### 6.1 Los 4 jefes reales

| Jefe | Escenario | Notas |
|---|---|---|
| `BossVenado` | `boss_venado` (1-4, **referencia**) | 2 fases: pisada, carga, lianas Bézier, esporas |
| `BossRey` (Rey Terciopelo) | `boss_rey` (2-4) | fase única `VENOM_SPIT` |
| `BossGavilan` (El Gavilán Camionero Mascarero) | `stage3_4_boss_gavilan` (3-4) | **clase parcial** (fase orbital); el spec 17 lo describe con 22 patrones que ningún jefe implementa |
| `BossPaburu` (Gran Shamán) | `boss_paburu` (4-2) | 4 formas; `STONE_SPIT` / `EYE_BEAM` / `EL_SELLO`; braseros por fase; intro con cutscene |

### 6.2 API de `BossBase` (heredada gratis por los jefes)

```python
BossBase(spawn_position, max_health=20.0, damage_on_contact=1.0)   # atributo de clase: skill_drop
```

`set_phases(phases: list[BossPhase])`, `set_boss_name(name)`, `boss_name()`, `phase_count()`,
`phase_max_health()`, `completion_fired`, `apply_hit(damage, source_position)`,
`fase_invulnerable()`, `escala_de_fase()`, `aturdido()`, `recibir_parry()` (devuelve segundos de
aturdimiento), `teletransportar(x, y)` (esquina superior-izquierda), `on_attack_fired(attack_name)`,
`on_summon(species_id, count)`, `take_summons()`, `set_arena_bounds(rect)`, `clamp_to_arena(margin=16)`,
`attack_timing()`, `is_vulnerable()`, `telegraph_progress()` (0–1), `weak_point_at(hit_rect)`,
`apply_hit_at(damage, source_position, hit_rect=None)` (daño por punto débil). Emite
`BOSS_PHASE_CHANGED`.

### 6.3 Kit de jefe (`boss_kit.py`)

- `BossAttack(name, windup=0.6, active=0.2, recover=0.8, damage=1.0, reach=48, min_range=0,
  max_range=9999, cooldown=1.5, phases=(), parriable=False, aturde_al_parry=1.2)` +
  `available_in(phase)`, `in_range(distance)`, `total_duration()`, `is_readable()`.
- `WeakPoint(offset, size, multiplier=2.5, phases=(), label='núcleo')` + `rect_for(boss_rect)`,
  `exposed_in(phase)`.
- `SummonWave(species_id, count=2, max_alive=4, cooldown=8, phases=(), spawn_offsets=...)`.
- `AttackScheduler(attacks=None)`: `current()`, `timing()`, `is_active()`, `is_vulnerable()`,
  `telegraph_progress()`, `update(dt, distance, phase)` (devuelve el ataque al entrar en ACTIVE),
  `interrupt()`, `se_puede_desviar()`, `desviar()` (éxito → cooldown completo + aturdimiento),
  `reset()`.
- `SummonTracker(waves)`: `update(dt)`, `alive_count()`, `ready_wave(phase)`, `spawn(wave, origin)`,
  `reset()`.
- `resolve_weak_point_damage(boss, hit_rect, base_damage, weak_points, phase) → (daño, acertó_punto)`.

**Regla para crear un jefe:** heredar `BossBase`, declarar fases con umbrales de salud, usar
`BossAttack`/`WeakPoint`/`SummonWave` y ganchos `on_attack_fired`/`on_summon`. La arena se limita con
`set_arena_bounds` (AUD-061). El drop de habilidad se declara con `skill_drop`.

---

## 7. Diseño de niveles (TMX)

### 7.1 Reglas del formato

- Tile 16×16, ortogonal, orden derecha-abajo, infinito **No**. Resolución interna 800×600.
- **8 capas** (en orden): `BG_Far`, `BG_Mid`, `BG_Near`, `Terrain`, `Terrain_Detail`, `Objects`,
  `Collision`, `FG_Overlay`.
- Capa `Collision`: rectángulos con tipo `Solid` (sólido total) o `Platform` (un solo sentido,
  atraviesa desde abajo). Nada más.
- Todo lo demás vive en `Objects` como rectángulos tipados (ver §7.3).

### 7.2 Propiedades de mapa (17+; en el nodo map del TMX)

| Propiedad | Valores / significado |
|---|---|
| `stage_id`, `stage_name`, `bgm_track` | **Obligatorias** |
| `author`, `time_limit`, `gravity_multiplier`, `zone`, `background_zone` | Metadatos y física |
| `vista` | `lateral` (defecto) o `cenital` |
| `camara` | `seguir` (defecto), `zona_muerta`, `sala` |
| `estamina` | 0 = off; 100 = 4 dashes + 0.6 s pausa |
| `tiempo_bala` | 0 = off; segundos de reserva de cámara lenta (`Q`/`R` mantenida, AUD-260) |
| `bpm`, `compas`, `desfase_audio` | Reloj musical (0 bpm = sin ritmo) |
| `ambient_light` (0–1), `bloom`, `vignette` | Atmósfera base |
| `climate` | `clear` `rain` `snow` `fog` `storm` |
| `ambient_fx`, `ambient_fx_rate` | `dust` `leaves` `embers` `spores` `ash` `none` |
| `start_hour`, `day_length` | Día/noche; `day_length=0` congela |
| `season` | `spring` `summer` `autumn` `winter` |
| `fog_of_war` | radio en px (0 = off) |
| `water_effect`, `water_speed/amplitude/frequency/alpha/tint` | Efecto de agua (AUD-240) |
| `god_rays` | Rayos volumétricos (AUD-226) |

### 7.3 Tipos de objeto (39 del framework + 21 especies + 8 arquetipos + `BossVenado` en `Objects`, + `Solid`/`Platform` en `Collision` = **71 tipos siempre declarables**)

> **AUD-455 (2026-08-13), corregido tras leer `docs/70` §Iteración 15-16.**
> Decía «34 del framework... = 65». `BUILTIN_OBJECT_TYPES` en
> `src/framework/stage/tmx_diagnostics.py` tiene **39** entradas exactas. Con
> las 21 especies, los 8 arquetipos y `BossVenado` (registrados por
> `entity_factory.ensure_registered()` al arrancar, igual que cuenta la fila
> «Enemigos» de la §21.1) más `Solid`/`Platform` de `Collision`, el total
> siempre disponible es **71** — la misma cifra que ya usaba
> `tests/test_el_inventario_cuenta_bien.py` para este alcance antes de que
> AUD-415 corrigiera un bug de orden de ejecución (véase `docs/70`). Una
> primera versión de esta nota decía 69 por no sumar `Solid`/`Platform`;
> AUD-412/413 fijan que sí cuentan en el total del motor.
> `60_GUIA_COMPLETA_DEL_MOTOR.md` §4 da **78**: cuenta además 7 tipos de
> enemigo que sólo existen cuando se importa el paquete de su propio
> escenario (`LaSodaWalkerRaton`, `BossRey`…) — un alcance más amplio, no una
> contradicción.

| Categoría | Tipos |
|---|---|
| Progresión | `PlayerSpawn` (obligatorio, 1 solo) `Checkpoint` `NextTrigger` |
| Mensajes/diálogo | `MessageTrigger` `MessageTrigger_Once` (`Message` solo NO es válido) `Cutscene` |
| Peligro | `HazardZone` (daño, `sube`/`sube_hasta`/`arranca_con` = inundación) `DeathPit` `LaserZone` `ShockwaveZone` |
| Cámara | `CameraLock` (congela ejes solo dentro de su rect) `ScrollZone` (scroll forzado, AUD-249) |
| Luz | `Light` (pos, radio, color `#aarrggbb`, intensidad, parpadeo) |
| Interactivos | `PushBlock` `BreakableBlock` `Pickup`/`Key` `Door`/`LockedDoor` `Cage` `Chest` `EventTrigger` |
| Mecánicas F5 | `WindZone` `FrictionZone` `Conveyor` `WaterZone` `MovingPlatform` `RhythmBlock` `SinkingPlatform` `Spring` |
| Sigilo | `Guard` (cono de visión) `Stalker` (perseguidor inmortal) |
| Movilidad | `Vine` (liana) `Zipline` (tirolesa) `Waypoint` |
| Enemigos | Las 21 especies por nombre + los 8 arquetipos (tipos registrados vía `register_entity`) |

> **AUD-455 — `BossSpawn` sí existe (AUD-259), esta nota estaba desactualizada.**
> `StageObjetos._handle_boss_spawn()` lo reconoce: con propiedad `boss="BossVenado"` produce la
> misma entidad que declarar `type="BossVenado"` directamente. Sólo avisa si falta `boss` o si
> nombra una clave no registrada. Confirmado leyendo `src/framework/stage/stage_objetos.py`.

### 7.4 El flujo de carga

`StageLoader.load(tmx_path) → StageData` (caché de parseo; `FrameworkUsageError` si falta la
capa, un objeto es inválido o no hay `PlayerSpawn`). `StageData` contiene `map_layer`,
`collision_rects`, `one_way_rects`, `entity_list`, `checkpoints`, `spawn_point`, `next_trigger`,
`hazard_zones`, `death_pits`, `escenas`, `empujables`, `destructibles`, `camera_locks`, `lights`,
`recogibles`, `cerraduras`, `cofres`, `disparadores`, `scroll_forzados`, `componentes` + las
propiedades del mapa. Registro de entidades nuevas: `StageLoader.register_entity(nombre, clase)`.

**Herramientas de nivel:** `scripts/preview_tmx.py` (vista previa), `scripts/validate_tmx.py`
(validación), `scripts/grade_stage.py` (rúbrica de 130 puntos), `scripts/check_tmx_coverage.py`
(exige que el mapa de ejemplo demuestre cada propiedad), `scripts/grade_boss.py`.

---

## 8. Interactivos y mecánicas de nivel

| Sistema | Archivo | API |
|---|---|---|
| Interactivos | `stage/interactables.py` + `interactable_system.py` | `Recogible` (item, `automatico`, `cantidad`), `Cerradura` (`key_id`, `clase`, `abre_con_evento`, `cierra_en`), `Cofre` (`contenido`, `key_id`), `Disparador` (`evento`, `automatico`, `una_vez`), `Llavero` (`tiene/coger/gastar`). `InteractableSystem(recogibles, cerraduras, cofres, disparadores, bus)` con `rects_solidos()`, `hay_algo_que_hacer()`, `update(dt, jugador, usar)`, `soltar_botin(entity_id, recogible)`, `abrir_por_evento(evento)` |
| Bloques | `stage/bloques.py` | `BloqueEmpujable` (reinicia al respawn), `BloqueDestructible` (`golpear()`), `SistemaDeBloques` (`rects_solidos`, `empujar`, `caer`, `golpear`, `reiniciar`) |
| Peligros | `stage/hazard_system.py` | `HazardSystem(context)` → `arrancar_por_evento(evento)`, `update(dt, player, stage, camara)`, `reset()`; gestiona inundaciones y scroll forzado |
| Checkpoints | `stage/checkpoint.py` | `Checkpoint(pos, rect, checkpoint_id, bus)` → `check_collision(player_rect)`, `activate()`, `is_activated()` |
| Cámara | `stage/camera.py` | `Camera` → `follow(target)`, `set_map_size`, `set_camera_locks`, `apply_shake(amp=2, dur=0.1)`, `parallax_factor(nombre)`, `set_parallax_factor`, `layer_offset`, `world_to_screen`, `screen_to_world`, `update(dt)` |
| Colisiones | `stage/collision_system.py` | `CollisionSystem(context)` → `reset()`, `trigger_hitstop(dur=0.05)`, `is_hitstopped()`, `update_hitstop(unscaled_dt, clock)`, `apply_knockback(entity, ix, iy)`, `process_attack(dt, player, stage, camera=None, clock=None)`, `remove_entity`, `draw_debug` |
| Día/noche | `stage/day_night.py` | `RelojDeMundo(hora_inicial=12, duracion_dia=0)` → `hora()`, `luz()`, `etiqueta()`, `update(dt)`; `luz_a_las(hora)`; `MOMENTOS = {dawn:7, morning:10, noon:12, afternoon:16, dusk:19, …}` |
| Estaciones | `stage/seasons.py` | `estacion(nombre)` (nunca lanza), `es_valida(nombre)`, `aplicar_tinte(color, est)`; `ESTACIONES = {spring, summer, autumn, winter}` |
| Corte de nivel | `stage/level_mechanics.py` | `ControlDeNado(aire_maximo=30, dano_por_segundo=1, umbral_aviso=10)` → `sin_aire()`, `avisando()`, `update(dt, jugador, mundo, bus)`; `TiempoBala(escala=0.35, reserva_maxima=3)` → `activo()`, `fraccion()`, `update(dt_real, quiere, reloj)` (**conectado en AUD-260**: propiedad de mapa `tiempo_bala`, `Action.BULLET_TIME`); `ScrollForzado(velocidad=(40,0))` → `arrancar(camara)`, `update(dt, camara)`, `se_quedo_atras(rect, camara)` |
| Métricas de nivel | `stage/level_metrics.py` | `JumpEnvelope.from_settings()` (COMFORT 0.8), `classify_gap(w)`, `classify_ledge(h)`, `analyse_geometry`, `analyse_checkpoints`, `reachable_platforms`, `exit_is_reachable`, `analyse_stage` |
| Progresión | `stage/progression_system.py` | `ProgressionSystem(context)` → `process_checkpoints(player, stage, checkpoints, hud, stage_key)`, `check_next_trigger`, `check_boss_defeat`, `update_complete_timer`, `stage_complete` |
| Speedrun | `stage/speedrun_mode.py` | `SpeedrunTimer` → `start/stop/reset/update/start_stage/split/get_splits/save/load/global_time/running`; `GhostData` → `grabar_si_toca(dt,x,y,state)`, `posicion_en(t)`, `record`, `get_frame`, `save/load`; `registrar_marca(stage_id, tiempo)` |
| Boss rush | `stage/boss_rush_mode.py` | `BossRushStage(boss_id, boss_name, scene_builder, phase_count)`; `BossRushMode` → `add_stage`, `start`, `get_current_stage`, `advance_to_next`, `record_hit`, `registrar_tiempo`, `acreditar_combate`, `salud_arrastrada`, `medidor_arrastrado`, `is_complete`, `score`, `active`, `current_name`, `progress` (**conectado en AUD-261**; GAP-030 cerrado) |
| Cutscenes | `stage/cutscene_system.py` + `cutscene_guion.py` + `cutscene_director.py` | Acciones: `WaitAction`, `FadeAction`, `CameraMoveAction`, `DialogueAction`, `MoverEntidadAction`, `EventoAction`, `SonidoAction`, `TemblorAction`, `EsperarEventoAction` (tope 10 s), `DialogoArbolAction`, `AccionParalela`. `CutsceneScript(acciones, bloquea, saltable, bandas)` → `add_action`, `start(cb)`, `saltar()` (ejecuta los finales, NO cancela), `update`, `draw`, `active`, `terminada`. **Mini-lenguaje** (una orden por línea, `#` comentario, `+` paralela, `.` deja la coordenada): `esperar` `camara` `mover` `dialogo` `evento` `sonido` `temblor` `fundido` `esperar_evento`. `CutsceneDirector(contexto, escenas, bus, vistas)` → `reproducir_texto(guion)`, `bloquea()`, `update(dt, jugador_rect, saltar)`, `saltar()`, `draw`, `reset()` |
| Dibujo | `stage/drawing_system.py` | `DrawContext(surface, stage, player, …, debug)`; `DrawingSystem.draw(ctx)`, `draw_ui(ctx)` |
| Diálogo TMX→árboles | `ui/dialogue_system.py` | `DialogueNode(node_id, speaker, text, portrait, choices, on_enter, on_exit)`, `DialogueTree.desde_datos(datos)`, `DialogueSystem(context)` → `start_dialogue(tree)`, `end_dialogue()`, `update`, `draw`, `active()`; árboles desde `data/dialogues/<stage_id>.json` (AUD-244) |

---

## 9. Efectos visuales (VFX) — `src/framework/vfx/`

| Sistema | API |
|---|---|
| Partículas | `ParticleEmitter` → `emit(x,y,config)`, `emit_directed(...)`, `update(dt)`, `draw(surface, offset)`, `clear()`, `count()`; `BurstConfig(count, speed, lifetime, size, color, spread=360, gravity=0, friction=1)`; `ParticleSystem` (emisores con nombre) → `get_emitter(name)`. `warmup()` precompila el kernel JIT |
| Luz | `LightSource(pos, radius=80, color, intensity=0.8, flicker, flicker_speed, flicker_amount)` → `update`, `get_current_radius/intensity`, `build_gradient`, `get_cached_gradient`; `LightSystem(ambient_brightness=0.3)` → `add_light`, `remove_light`, `clear`, `update(dt, offset)`, `render(target, offset)`, `get_player_light(pos, is_combat)` |
| Impactos | `HitEffects.get_for_damage(damage)` / `get_blood_for_damage(damage)` → BurstConfig |
| Números de daño | `DamageNumber(x,y,texto,critical)`; `DamageNumberManager` → `add`, `clear`, `update`, `draw` |
| Clima | `WeatherSystem(climate='clear')` → `set_climate`, `climate()`, `update(dt, offset)`, `draw(surface, offset)`, `clear()`, `get_ambient_audio_key()`, `falta_su_ambiente()`; climas `clear/rain/snow/fog/storm` (storm = viento lateral) |
| Partículas ambientales | `AmbientParticleSystem` → `set_effect(tipo, rate=10)`, `count()`, `rate()`, `update`, `draw`, `clear()`; tipos `dust/leaves/embers/spores/ash` |
| Estelas | `TrailSystem` → `capture(player)` (dash azul), `capture_at(x,y,size,color)`, `update`, `draw`, `clear()` |
| Niebla de guerra | `FogOfWar(w, h, radius=80, hardness=0.6)` → `clear()`, `reveal(x,y)`, `reveal_all(puntos)`, `update`, `draw` |
| Agua | `WaterEffect(w, h)` → `set_params(speed=1.5, amplitude=4, frequency=0.04, alpha=100, tint=(40,80,160))`, `update`, `draw` |
| Post-procesado | ver §10 |

**Cómo se activan desde un nivel:** por propiedades del mapa (`climate`, `ambient_fx`,
`fog_of_war`, `water_effect`, `ambient_light`, `bloom`, `vignette`, `god_rays`) y por objetos
`Light`. Fórmula de apilado: `luz = ambient_light × hora × estación + clima` con suelo
`MIN_AMBIENTE = 0.45` (la noche nunca baja de ahí).

---

## 10. Post-procesado y tubería GPU

### 10.1 `PostProcessing` (CPU, por defecto)

`set_motion_blur(strength)`, `clear_motion_blur()`, `set_color_grading(9 canales)`,
`clear_color_grading()`, `set_bloom(intensity, duration)`, `flash(color, alpha, duration)`,
`set_damage_vignette(strength)`, `set_tint(color, alpha)`, `clear_tint()`,
`set_base_bloom(intensity)`, `set_vignette(strength)`, `update(dt)`, `apply(surface)`. Incluye
**filtros de daltonismo** (protanopia/deuteranopia) activables por accesibilidad.

### 10.2 Tubería OpenGL (`src/engine/render/`, doc 74)

`gl_pipeline.py` + `shaders.py` + `gpu_present.py` (`PresentadorGPU`). **Medido (AUD-148):** el
bloom en GPU es **5× más lento** que en CPU (8.3 vs 1.7 ms) en máquinas sin GPU real porque SDL cae
a software; presentar es barato (0.18–0.36 ms). Por eso la tubería GL está **apagada por defecto**.
Medir con `scripts/bench_gpu_postproc.py`. No usar `ModernGL` convierte el arranque en software puro.

---

## 11. ECS — `src/framework/ecs/`

**Principio (invariante 2):** el ECS vive **debajo** de la jerarquía clásica (las 26 clases de
escenario siguen funcionando sin tocarlas). El puente: `ComponentesDeEntidad` (mixin de
`BaseEntity`) → `mundo()`, `entidad()`, `adoptar_en(destino)`, `componente(tipo)`,
`poner_componente(c)`, `facing`, `velocity`.

- **`World`** (store): `poner_recurso/recurso`, `crear(*componentes) → EntityId` (no se reutilizan
  ids), `adoptar`, `existe`, `marcar_baja`, `aplicar_bajas`, `poner`, `quitar`, `obtener`, `tiene`,
  `cada(tipo)`, `con(*tipos)` (query all-of), `total_entidades()`, `censo()`, `censo_tipos()`.
- **20 componentes** (`components.py`, datos puros — AUD-455: esta lista decía 18 y le faltaban
  `Navegante` y `Efectos`, dos clases reales): `Transform` (`posicion`, `rect`, `facing`,
  vista sobre el dueño), `Velocidad`, `Solido` (`atravesable_desde_abajo`), `Salud` (vista),
  `EsJugador` (marcador), `Resorte` (`impulso=-520`, `rearme=0.15`),
  `Navegante` (AUD-389: `ruta`, `proximo` con espera inicial aleatoria para escalonar el A* entre
  enemigos), `Efectos` (AUD-388: `activos`, la lista de efectos temporales — veneno, etc. —
  compartida entre jugador y enemigos; catálogo en `framework/combate/efectos.py`),
  `ZonaDeViento` (`fuerza`,
  `periodo`), `ZonaDeFriccion` (`multiplicador`, `arrastre`; **ojo:** <1 frena, >1 acelera),
  `ZonaLetalTemporizada` (`dano=99`, `encendido/apagado/desfase`, `activa()`, `aviso()`),
  `ZonaDeAgua` (`corriente`), `PlataformaMovil` (`origen/destino/velocidad/espera/delta`),
  `BloqueRitmico` (`visible_seg`, `oculto_seg`, `desfase`, `patron` "x.x."),
  `PlataformaHundible` (`retraso=0.4`, `velocidad_caida=90`, `reaparece_en=3`), `Liana`
  (`ancho_de_agarre=10`, `velocidad=70`), `Tirolesa` (`origen/destino/velocidad=190`,
  `radio_de_enganche=14`, `solo_de_bajada`, `punto_mas_cercano(p)`, `progreso(p)`),
  `ConoDeVision` (`alcance=160`, `semiangulo=30`, `barrido`, `ve_al_jugador`), `Alerta`
  (`nivel`, `subida=2/s`, `bajada=0.35/s`, `umbral_sospecha=0.4`, `umbral_alerta=1`, `estado()`),
  `Acosador` (`velocidad=55`, `distancia_retirada=480`, `reaparicion=6`).
- **Sistemas** (`systems.py`, funciones `(mundo, dt)`): `sistema_resortes`, `sistema_viento`,
  `sistema_friccion`, `sistema_corriente_de_agua`, `sistema_plataformas_moviles`,
  `sistema_bloques_ritmicos`, `sistema_plataformas_hundibles`, `marcar_pisada`,
  `sistema_arrastre_de_plataformas`, `sistema_zonas_letales`, `liana_alcanzable`,
  `tirolesa_alcanzable`, `en_agua`, `rect_del_jugador`, `sistema_conos_de_vision`,
  `sistema_alerta`, `sistema_acosador`, `rects_solidos`.
- **`Planificador`** (scheduler): `registrar(fase, nombre, fn)`, `activar(nombre, bool)`,
  `ejecutar(mundo, dt)`, `tiempos()`, `nombres()`, `total_ms()`. **Fases** (números espaciados):
  `ENTRADA=100, IA=200, FUERZAS=300, MOVIMIENTO=400, ESCENARIO=450, ARRASTRE=460, COLISION=500,
  ZONAS=600, COMBATE=700, ANIMACION=800, CAMARA=850, BAJAS=900`. El orden del fotograma del
  jugador está declarado una sola vez en `StageScene._construir_planificador()`.
- **`EnjambreDeBalas`** (lluvia de balas, SoA numpy, capacidad 4096): `disparar(x,y,vx,vy,vida,dano,radio)`,
  `abanico(x,y,cuantas,velocidad,angulo_inicial,apertura)`, `retirar(indices)`, `limpiar()`,
  `update(dt, limites)`, `impactos_contra(rect)`, `dano_total_contra(rect, consumir=True)`,
  `draw(surface, offset, color)`, `contador()`, `lleno()`. (Medido: 2000 balas 12.94 ms → 0.072 ms.)
- `sincronizar_salud(*args)` es un **no-op deliberado** desde F5.12 (compatibilidad de estudiante).

---

## 12. API completa del framework (`src/framework/`)

> Convención: `Player` y las 8 clases de enemigos + `BossBase` + `Projectile`/`HomingOrb` están en
> §4–§6. El ECS en §11. Los VFX en §9. Aquí van los módulos restantes.

### 12.1 `framework/__init__.py`
`FrameworkUsageError(Exception)` — se lanza cuando el código de usuario malusa el framework
(p. ej. falta una capa TMX).

### 12.2 `framework/entities/`
- `BaseEntity(ComponentesDeEntidad, ABC)`: `set_event_bus(bus)`, `update(dt)` (abstracto),
  `draw(surface, camera_offset)` (abstracto). Posición `pygame.Vector2`, `Rect` de colisión,
  visibilidad, activo.
- `PlayerState(str, Enum)`: los 30 estados (ver §4.1). `PlayerStateData`: 44 campos transitorios.
- `entity_factory.ensure_registered()`: registra tipos en el StageLoader (idempotente).
- `bestiary.py`: `BestiaryEntry(enemy_id, name, description, lore, drops, hp, damage)`,
  `Bestiary.get_instance()` → `id_de(enemigo)`, `get_entry(id)`, `get_all_entries()`,
  `record_encounter(id)`, `record_kill(id)`, `record_hit(id)`, `save(path)`, `load(path)`.
  Fichero por defecto `user_data_dir()/saves/bestiary.json`; base en `data/bestiary.json`.
- `squad_brain.py`: `SquadBrain` (IA táctica por lotes a 4 Hz) → `reset()`, `forget(enemy)`,
  `decision_for(enemy)`, `update(dt, player, enemies)`, `stats()`; `Decision(action, source, age)`.
- `ai_predictor.py`: `BehaviorPredictor` (KNN + árbol; sklearn es dependencia obligatoria y se
  importa sin repliegue — ver la corrección de §1) → `add_example`,
  `is_trained()`, `action_names()`, `action_index(nombre)`, `extract_features(**kw)`,
  `predict_batch(rows)`, `predict(features)`, `predict_action_name(**kw)`,
  `get_rule_based_action(dist, health_pct, player_health_pct, has_ranged)`; `get_predictor()`.
- `ranged_weapon.py` (arco del jugador): `velocidad_inicial(direccion, potencia)`,
  `trayectoria(origen, direccion, pasos, potencia)`, `ArcoDelJugador(municion_maxima, cadencia,
  dano)` → `listo()`, `tensando()`, `potencia()`, `tensar(dt)`, `soltar_tension()`, `vacio()`,
  `update(dt)`, `disparar(origen, direccion)`, `recargar(cantidad)`, `llenar()`, `limpiar()`,
  `impactos_contra(objetivos, dt)`, `choca_con_muros(muros, dt)`.
- `flight_strategies.py`: `SineFlight`, `BezierFlight`, `WaypointPatrol`, `ChaseFlight`,
  `DiveFlight`, `make_strategy(flight_mode)` (modo desconocido → SineFlight, no crashea).

### 12.3 `framework/processing/` — ver §16.

### 12.4 `framework/scenes/`
- `StageScene` (la escena jugable): subclases declaran `TMX_PATH` y `STAGE_ID`. **Ganchos
  públicos de escena:** `on_stage_start()`, `on_player_landed()`, `on_enemy_died(enemy)`,
  `on_next_trigger_entered()`, `on_debug_toggle(enabled)`, `dibujar_fondo(surface, offset)`
  (pintar DETRÁS del mapa, AUD-162), `stage_key()` (identidad única para guardado, AUD-156),
  `on_enter()`, `on_exit()`, `respawn()`, `update(dt)`, `draw(surface)`.
- `stage_parts/`: mixins de lectura (AUD-152) — `MezclaDeAmbiente`, `SenalesDeEscenario`
  (`_soltar_botin`, `_play_sfx_named`, `_play_sfx_spatial`), `FantasmaDeCarrera`
  (`_ruta_del_fantasma`, `_preparar_fantasma`, `_guardar_fantasma_si_es_mejor`, `_dibujar_fantasma`),
  y `dibujar_mecanicas_ecs(surface, mundo, offset)`.

### 12.5 `framework/ui/`
- `dialogue_system.py`: ver §8.
- `tutorial_overlay.py`: `TutorialOverlay.show(tip_key, duration=5)`, `update`, `draw`.
- `learning_overlay.py`: `LearningOverlay.toggle(action)`, `hide()`, `active()`, `update`, `draw`
  (paneles F2–F10).

### 12.6 `framework/audio/`
`DynamicMusicSystem(audio_manager)` → `set_zone(zone, bgm_track)`, `set_intensity(nivel)`
(crossfade), `detect_intensity_from_state(has_boss, has_alive_enemies)`.

### 12.7 `framework/ai/`
`LuaScriptEnemy(script_source, name)` → `call_patrol/alert/on_hit/on_death`; `load_script(name)`,
`register_script(name, source)`. **OJO: NO está conectado al juego (AUD-022).** Solo pruebas.

### 12.8 `framework/academic/`
`curriculum.py`: `PLAN` (unidades), `ids_de_unidades()`, `unidad(id)`, `unidad_de_escena(clave)`,
`siguiente_unidad(id)`, dataclasses `BloqueTeorico`, `Pregunta`, `Unidad`. `progress.py`:
`ProgresoAcademico(correo)` → `aciertos(id)`, `intentos(id)`, `esta_aprobada`,
`esta_desbloqueada`, `unidades_desbloqueadas/aprobadas`, `porcentaje()`, `unidad_actual()`,
`registrar_intento(id, aciertos)`, `a_dict/desde_dict`, `guardar(dir)`, `cargar(dir, correo)`;
constantes `PREGUNTAS_POR_UNIDAD=5`, `ACIERTOS_PARA_APROBAR=4`. `sesion.py`:
`SesionAcademica.instancia()`, `entrar(correo)`, `reanudar()`, `salir()`, `registrar_examen(id,
aciertos)`, `guardar()`, `progreso()`, `correo()`, `identificado()`.

---

## 13. API completa del engine (`src/engine/`)

### 13.1 `core/`
| Módulo | API |
|---|---|
| `app.py` | `App` — raíz de composición (cablea todo; `App().run()`) |
| `clock.py` | `DeltaClock` — 3 relojes: `dt` (escalado), `dt_mundo` (sin hit-stop), `unscaled_dt` (real); `time_scale` compone factores con nombre; `MAX_FRAME_TIME=0.05` |
| `events.py` | `Events` — catálogo central (ver §15.1) |
| `event_bus.py` | `EventBus` — cola + suscriptores weak-ref: `subscribe`, `unsubscribe`, `emit`, `queue_snapshot()`, `subscribers_snapshot()` (debug) |
| `game_context.py` | `GameContext` — contenedor DI (67 líneas): `input_manager`, `audio_manager`, `scene_manager`, `event_bus`, `clock`, `save_manager`, `pending_load`, `running`, `inventory` |
| `difficulty.py` | `Difficulty` (enum) + `set_difficulty()` |
| `settings.py` | `INTERNAL_WIDTH=800`, `INTERNAL_HEIGHT=600`, `ASSETS_DIR`, `PLAYER_MAX_HEALTH=5.0`, `COMBO_DAMAGE_MULT`, constantes de física |
| `user_settings.py` | `UserSettings` (JSON en `user_data_dir()`), `preferencia("text_scale", …)`, `subtitles_enabled`, volúmenes |
| `i18n.py` | `_()` — traducciones es/en desde `locale/` (gettext rechazado en escrito, ver doc 60 §F3.1) |
| `save_data.py` / `save_manager.py` | `SaveData` (dataclass, `MAX_SLOTS`), `SaveManager.list_slots()`, `load(slot)`, `newest_slot()`; guardado atómico con `fsync` + `os.replace` |
| `achievements.py` | `AchievementSystem.get_instance()` → `get_all_achievements()`; carga por estudiante |
| `inventory.py` | `Inventory` — monedas/ítems; economía de tienda |
| `experience.py` | `ExperienceSystem` — XP/niveles |
| `score_system.py` | `ScoreSystem` — puntos + mejores marcas (verdad de leaderboard) |
| `stage_registry.py` | `STAGE_ORDER` (16 ids) + `discover_stages()` + `_STAGE_MODULE_MAP` (rutas no convencionales) |
| `gpu_effects.py` | Gestor de efectos GL |

### 13.2 `scene/`
- `BaseScene` (ABC): `on_enter()`, `on_exit()`, `update(dt)`, `draw(surface)`, `process_events()`,
  `respawn()`; propiedades `context`, `input`, `audio`.
- `SceneManager`: pila `push/pop/replace`, avanza cola de niveles con `STAGE_COMPLETE`/
  `PLAYER_DIED`, `set_stage_queue`, `set_stage_index`, transición fade (fabrica escenas; sin
  importaciones concretas, AUD-018).

### 13.3 `input/`
`InputManager`: `is_action_held(action)`, `just_pressed(action)`, `is_raw_key_pressed(key)`,
`rebind(action, keys)`. `Action` enum: ver §3 (26 acciones). Bindings en
`keybindings.json` (user_data_dir).

### 13.4 `audio/`
- `AudioManager`: `play_music`, `stop_music`, `play_sfx(nombre, volumen)`,
  `play_sfx_at(nombre, world_x, volumen)` (pan), `play_ambient`, `crossfade_ambient`,
  `play_stinger`, `play_voz` (baja la música a 35 %), `toggle_mute`, `is_muted`, `ajustar_bus`.
  **4 buses:** `musica`, `efectos`, `voz`, `ambiente`; volumen = master × bus × petición.
- `mixer_buses.py`: `Mezclador`; el diálogo duce la música (baja 0.15 s, sube 0.5 s).
- `sound_bank.py`: `SoundBank` (carga perezosa + caché; `load_all()` en `AudioManager.__init__`).
- `music_clock.py`: `RelojMusical(bpm, compas, …)` — reloj sincronizado a la posición de la pista
  (AUD-137); API `en_ventana()`, `cuantizar(t)`, `pulsos_cruzados`; bloques rítmicos con `patron`.
- `audio_pipeline.py`: cadena de post-proceso de salida (ducking/filtros).

### 13.5 `render/`
`gl_pipeline.py` (batching de sprites + programas GL), `shaders.py` (GLSL + compilación),
`gpu_present.py` (`PresentadorGPU`, off por defecto). Ver §10.

### 13.6 `utils/`
- `asset_loader.py`: `AssetLoader.load_image`, `load_font`, `load_sprite_sheet` (caché + fallback).
- `math_utils.py`: `vec2_dot`, `lerp`, suite de easing (`ease_in_quad`, `ease_out_bounce`,
  `ease_out_elastic`, …).
- `sprite_atlas.py`: `SpriteAtlas` (empacado/load, blit por clave).
- `surface_pool.py`: `SurfacePool` (`get_pool()`, `borrow`/`return`).

### 13.7 `ui/` (kit en-stage)
- `hud.py`: `HUD` — corazones (cuartos de slot), flash de daño, retrato 9-slice, temporizador,
  barra de jefe + fase, combo, medidor especial, estamina (oculta si max=0), región de
  puntuación+monedas; se suscribe a 6 eventos; requiere `destroy()`.
- `message_box.py`: `MessageBox` — máquina de escribir, 3 líneas/58 chars, cola,
  auto-descarte o CONFIRM.
- `minimap.py`: `Minimap` — rects explorados, flecha del jugador, enemigos, jefes, checkpoints.
- `screen_banner.py`: `ScreenBanner` — banner animado de título de nivel.
- `subtitle_overlay.py`: `SubtitleOverlay` — subtítulos de eventos con info; depende de
  `subtitles_enabled`.
- `theme.py`: tokens de diseño (`Theme.BG/SURFACE/ACCENT/…`, escala tipográfica, `font()`,
  `escalar_texto()` (respeta text_scale), `pulse()`, `with_alpha()`, `clear_font_cache()`).
- `widgets.py`: `MenuItem`, `MenuList`, `draw_screen()` (traduce títulos), `draw_panel()`,
  `draw_key_hints()`, `draw_modal_scrim()`, `draw_progress_bar()`, `draw_toast()`,
  `handle_menu_navigation()`.

---

## 14. Escenas del juego (34+; `src/engine/scenes/`)

| Grupo | Escenas |
|---|---|
| Flujo | `SplashScene` (3 s, warmup JIT + sklearn), `TitleScene` (menú principal), `TutorialScene`, `StoryScene` (3 capítulos), `GameOverScene`, `EndCreditsScene`, `LoadingScene`, `StageErrorScene` (fallo de carga en pantalla, `R` reintenta), `TransitionManager` |
| Menús | `OptionsScene`, `KeybindingScene`, `LoadGameScene`, `WorldMapScene`, `ProgressScene` (panel del estudiante), `LeaderboardScene`, `AchievementScene`, `BestiaryScene`, `InventoryScene`, `ShopScene`, `StudentLoginScene`, `StageWizardScene` (plantillas de nivel) |
| Académicas | `VectorLabScene` (4 modos), `TransformLabScene` (5 modos), `InterpolationLabScene`, `NoiseLabScene` (Perlin), `ColorTheoryScene` (RGB/HSV/HSL/CMYK + reto), `CollisionLabScene`, `ComboDemoScene`, `CurveEditorScene`, `FilterDemoScene` (10 modos), `PipelineBuilderScene` (11 filtros, 6 presets), `VisionDemoScene` (10 modos), `PatternDemoScene` (6 modos), `UnitTheoryScene` (teoría + examen), `DemoMenuScene` (hub), `SandboxScene` |
| Infra | `DebugOverlay`, `CodePanel` (C), `ParamPanel`, `QuizManager` (Q), `TutorialOverlay` (T), `SceneRegistry`, `demo_layout` (módulo de funciones: lienzo autorado 320×224 en ventana 800×600) |

Kit de demos (`demo_common.py`): `build_default_sources()`, `save_png`, `draw_top_bar`,
`draw_bottom_bar`, `draw_histogram_bars`, `FrameThrottle`, paleta y fuentes compartidas.

---

## 15. Sistemas transversales

### 15.1 Eventos (`Events`, `src/engine/core/events.py`) + interacción

**Juego:** `PLAYER_DAMAGED` `PLAYER_HEALED` `PLAYER_DIED` `ENEMY_DIED` `BOSS_PHASE_CHANGED`
`BOSS_ATTACK` `CHECKPOINT_REACHED` `STAGE_COMPLETE` `ITEM_COLLECTED` `FLAG_SET`
`SAVE_REQUESTED` `SHOW_MESSAGE` `HIDE_MESSAGE` `SHOW_DIALOGUE` `DIALOGUE_FINISHED`
`ACHIEVEMENT_UNLOCKED` `ACHIEVEMENT_PROGRESS`.

**SFX (39, más `MUSIC_STINGER` aparte):** `SFX_PLAYER_JUMP/LAND/FOOTSTEP/SHORT_ATTACK/LONG_ATTACK/HURT/DIE/PARRY/CROUCH/HEAL`,
`SFX_MENU_HOVER/CONFIRM/CANCEL`, `SFX_HIT_CONNECT`, `SFX_ENEMY_HIT`, `SFX_ENEMY_DIE_SMALL/LARGE`,
`SFX_PROJECTILE_FIRE`, `SFX_CHECKPOINT`, `SFX_STAGE_BANNER/COMPLETE`, `SFX_HAZARD_ZONE`,
`SFX_BOSS_HIT`, `SFX_BOSS_PHASE_CHANGE`, `SFX_UI_GAME_OVER`,
`SFX_ENVIRONMENT_SCREEN_SHAKE/ONE_WAY_PLATFORM`, `SFX_ENEMIES_PROJECTILE_HIT_WALL`,
`SFX_BOSSES_GAVILAN_DIVE/MASK_BEAM`, `SFX_BOSSES_PABURU_EYE_BEAM/WAVE`,
`SFX_BOSSES_RELIC_APPEAR`, `SFX_BOSSES_REY_SPIT/SPLIT`,
`SFX_BOSSES_VENADO_CHARGE/STOMP/VINE`, `SFX_VOZ_PABURU` (AUD-443: se emite ya; sin muestra en el
banco todavía, a propósito — falta el `.wav` de autor), `MUSIC_STINGER`.

> **AUD-455 (2026-08-13).** Decía «SFX (41)» y faltaba `SFX_VOZ_PABURU` en la
> lista. Recontado contra las constantes `SFX_*` de `src/engine/core/events.py`
> (39 exactas) más `MUSIC_STINGER`, que no lleva el prefijo y se cuenta aparte.

**VFX:** `VFX_PARRY` `VFX_CHARGE` `VFX_SLAM` `VFX_ULTIMATE` `VFX_BUBBLE`.

**Interacción (5):** `INTERACT_ITEM_PICKED` `INTERACT_LOCK_OPENED` `INTERACT_LOCK_BLOCKED`
`INTERACT_CHEST_OPENED` `INTERACT_TRIGGER_FIRED`.

Regla: nunca emitas/suscribas strings sueltos; usa `Events` (doc 23).

### 15.2 Persistencia
Guardado atómico (`fsync` + `os.replace`); 13 entradas hostiles probadas; partida corrupta falla
en voz alta (`test_corrupt_saves_are_loud.py`). Slots en `saves/`. Los escenarios completados
hacen avanzar la cola de niveles (`.stage_index` en `SaveData`).

### 15.3 Economía e inventario (doc 60 §11)
**16 ítems, 3 familias:** mejoras permanentes (slot `None`): `heart_vessel` (+1 HP máx),
`hollow_eye` (+0.3 daño), `ancients_rib` (+2 HP), `swift_feather` (+10 % velocidad),
`thorn_ring` (+0.5 daño), `sunken_crown` (+3 HP, +0.8 daño). Ropa (slots cabeza/cuerpo/pies; bonus
solo si está equipada; se vende a mitad): `hood_leaf`, `hood_ember`, `cloak_reed`, `cloak_serpent`,
`boots_swift`, `boots_stone`. Habilidades (slot `skill`): `skill_double_jump`, `skill_dash`,
`skill_parry`. Moneda: `coin` (los enemigos sueltan monedas; AUD-218).

### 15.4 Logros (10) y bestiario
`first_blood`, `exterminator` (50 bajas), `untouchable`, `parry_master` (10), `air_assault`
(combo aéreo de 3), `speed_demon` (<60 s), `collector` (5 checkpoints), `survivor` (≤0.5 HP),
`combo_king` (10), `explorer` (15 escenarios). Textos en `data/achievements.json` (validado en CI).
Bestiario: se llena solo (Tab); `data/bestiary.json`.

### 15.5 Accesibilidad
4 modos de daltonismo (post-procesado); escala de texto 1.0–2.0×; movimiento reducido atenúa al
25 % (no elimina); tap-not-hold; foco no cromático (fila elevada + cursor + brillo); contraste
8.9:1 medido (AA exige 4.5:1).

### 15.6 Audio dinámico
`DynamicMusicSystem` cruza pistas de travesía/combate/jefe por intensidad. Reloj musical
(AUD-137): `bpm`/`compas`/`desfase_audio` en el mapa; bloques rítmicos con `patron` (ej. `"x.x."`)
cuantizados a la pista; tiempo real (el bullet-time no desincroniza). **Reverberación por zona:
imposible en SDL** (documentado en `mixer_buses.py`).

---

## 16. Procesamiento académico (`src/framework/processing/`)

| Módulo | Funciones públicas |
|---|---|
| `filter_tools.py` (`FilterTools`) | `compute_histogram`, `histogram_equalize`, `adjust_brightness(surf, factor)`, `adjust_contrast`, `stretch_contrast`, `apply_kernel(surf, kernel)`, `get_standard_kernel(name)`, `gaussian_blur(sigma)`, `sobel_edge`, `canny_edge(lo, hi)`, `sobel_edge_propio`, `canny_edge_propio(lo, hi, sigma=1.4)` |
| `vision_tools.py` (`VisionTools`) | `threshold_binary`, `threshold_otsu`, `morphological_erode/dilate/open/close`, `connected_components`, `filter_components_by_area`, `analyze_regions`, `largest_region`, `watershed_segment`, `extract_features(surf, method='hog')`, `extract_hog`, `extract_lbp`, `extract_color_histogram(bins=256)`, `find_contours`, `bounding_boxes_from_mask` |
| `pattern_recognition_tools.py` | `train(X, y, model_type, feature_method='hog', **kw) → TrainedModel`, `evaluate`, `save_model`, `load_model` (⚠ solo ficheros de confianza, AUD-038), `register_model`, `get_model`, `list_models`, `classify`, `classify_proba`, `predict(surf, method)`, `generate_training_report(...)` |
| `color_tools.py` (`ColorTools`) | `rgb_to_hsv`, `hsv_to_rgb`, `rgb_to_hsl`, `hsl_to_rgb`, `rgb_to_cmyk`, `cmyk_to_rgb`, `alpha_blend(src, dst, alpha)`, `apply_tint(surf, color)`, `surface_to_array`, `array_to_surface` |
| `curve_tools.py` (`CurveTools`) | `bezier(puntos, n)`, `b_spline(puntos, grado, n)`, `nurbs(puntos, pesos, nudos, grado, n)`, `catmull_rom(puntos, n)`, `sample_path(puntos, t)`, `build_bezier_path(waypoints, t)` |
| `edge_detection.py` | `a_gris`, `convolucionar`, `gradiente`, `sobel`, `suavizar(gris, sigma)`, `supresion_no_maxima`, `histeresis`, `canny(rgb, bajo=50, alto=150, sigma=1.4)` |
| `reference_model.py` | `ruta_cacheada()`, `obtener_modelo(forzar=False)` (None sin sklearn/dataset), `entrenar()` |

---

## 17. Scripts de línea de comandos (`scripts/`)

### 17.1 Validadores y calidad (los que corre CI)

| Script | Uso | Args |
|---|---|---|
| `validate_assets.py` | Valida assets (rutas, formatos) | — |
| `validate_tmx.py` | Valida mapas TMX | `paths...`, `--fix` (sugiere arreglos), `--ci` (solo errores) |
| `check_dependency_sync.py` | Manifest de dependencias consistente | — |
| `check_translations.py` | Catálogos es/en | `--ci` |
| `check_tmx_coverage.py` | Cada propiedad del mapa demostrada en el ejemplo | `--ci`, `--minimo 0.85` |
| `check_achievements.py` / `check_bestiary.py` | Textos de logros/bestiario válidos | — |
| `check_orphan_systems.py` | Detecta símbolos sin invocar | `--ci`, `--todos` |
| `audit_docs_vs_code.py` | Regenera el registro de lo no implementado | `--json` |
| `generate_tmx_reference.py` | Tabla de tipos de `STAGE_CREATION.md` | `--check` |
| `mutation_check.py` | Pruebas de mutación | `--objetivo`, `--pruebas`, `--maximo 25`, `--umbral`, `--ci` |
| `difficulty_curve.py` | Curva de dificultad medida | `--md`, `--ci` |
| `grade_stage.py` | Rúbrica de nivel (130 pts) | `paths...`, `--json`, `--dir` |
| `grade_boss.py` | Rúbrica de jefe | `paths...`, `--json`, `--dir` |
| `grade_exporter.py` | Exporta calificaciones | `--input` (req), `--output`, `--format csv/json` |
| `feedback_generator.py` | Feedback markdown desde JSON | `--grade` (req), `--output` |
| `plagiarism_detector.py` | Compara entregas | `submissions`, `--threshold 0.85`, `--pattern "**/*.tmx"` |
| `downloader.py` | Baja entregas de GitHub Classroom | `--org`, `--assignment`, `--csv`, `--output submissions` |
| `generate_exam.py` | Genera exámenes | `--unit`, `--num-questions 10` |
| `train_reference_model.py` | Entrena el modelo de referencia | `--npz`/`--data`, `--out`, `--model-type`, `--feature-method` |
| `preview_tmx.py` | Vista previa de un mapa | `tmx`, `--salida PNG`, `--sin-luz`, `--con-etiquetas`, `--hora` |
| `collect_palettes.py` | Paletas de los assets | `--max-colors` |
| `project_stats.py` | Estadísticas del repo | — |
| `obsidianize.py` | Convertir docs a Obsidian | `--dry-run` |
| `bench_gpu_postproc.py` | Bench de post-procesado GPU vs CPU | — |
| `build_executable.py` | Empaqueta ejecutable | `--limpiar`, `--un-archivo` |
| `_cli_paths.py` | Utilidad interna de rutas | — |

### 17.2 Comandos maestros de desarrollo

```powershell
pip install -e ".[dev]"                                   # instalar
python main.py                                            # jugar
pytest                                                    # suite completa
pytest tests/test_player_physics.py -v                    # un archivo
pytest tests/ -k "collision"                              # patrón
ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/
mypy $(grep -v '^\s*#' mypy_scope.txt | grep -v '^\s*$')  # tipos (solo src/engine/core + src/engine/input)
python scripts/grade_stage.py assets/maps/ --json         # calificar niveles
python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json
python scripts/check_tmx_coverage.py --ci
python scripts/validate_tmx.py --ci
python scripts/validate_assets.py
python scripts/check_translations.py --ci
python scripts/check_dependency_sync.py
python scripts/generate_tmx_reference.py --check
python scripts/mutation_check.py --ci                     # semanal o manual
```

---

## 18. Tools de generación de assets (`tools/`)

| Tool | Función |
|---|---|
| `generate_all_assets.py` | Genera todo el set de assets procedurales |
| `generate_assets.py` / `pixel_asset_generator.py` | Generadores base de sprites pixel-art |
| `generate_stage0_tmx.py` / `generate_demo_stage0.py` | Regenera el TMX del stage0 (validado por test) |
| `generate_stage_mecanicas.py` | Regenera el laboratorio de mecánicas (validado por test) |
| `generate_stage4_1.py` | Regenera el TMX del 4-1 |
| `build_dataset.py` | Dataset de entrenamiento (ML) |
| `convert_audio.py` | Conversión de audio (requiere extra `audiotools`) |
| `export_individual_frames.py` | Exporta frames individuales |
| `quantize_to_palette.py` | Cuantiza sprites a paleta |
| `validate_stage.py` | Valida un escenario empaquetado |

> Nota: la documentación antigua citaba los validadores con rutas de `tools/` que ya no
> existen (corregido AUD-168): los validadores viven en `scripts/`.

---

## 19. Suite de pruebas

**Cifras medidas (2026-08-02, GAP-020):** 2.872 casos recolectados / 2.870 pass / 1 skip;
161 ficheros de test + benchmarks + playtest. Fixture global (conftest): drivers dummy, reset de
singletons (`AssetLoader`, `StageLoader`, fuentes, `AchievementSystem`, `user_settings`) y drenaje
de la cola de eventos pygame antes de cada test.

| Área | Tests representativos |
|---|---|
| Jugador | `test_player_physics`, `test_player_state_machine`, `test_player_states_extended`, `test_player_damage`, `test_player_hurtbox`, `test_estamina`, `test_calibracion_del_salto`, `test_floor_x_skip`, `test_spawn_no_pop`, `test_ranged_and_ultimate`, `test_arco_con_apuntado`, `test_flechas_y_punalada`, `test_combo_system`, `test_muerte_y_game_over` |
| Enemigos/jefes | `test_enemy_walker/flying/shooter/state_machine`, `test_boss_base`, `test_boss_encounter`, `test_boss_grader`, `test_parar_a_un_jefe`, `test_parar_una_embestida`, `test_parada_que_aturde`, `test_habilidades_que_sueltan_los_jefes`, `test_squad_brain`, `test_monedas_que_sueltan_los_enemigos` |
| Colisiones/física | `test_cajas_de_colision`, `test_collision_edge_detect`, `test_rect_fusionado_suelo_y_pared`, `test_layering`, `test_sensacion_y_camara` |
| TMX/niveles | `test_stage_loader`, `test_referencia_tmx`, `test_tmx_diagnostics`, `test_tmx_validator`, `test_todos_los_tipos_se_usan`, `test_level_design_qa`, `test_rubrica_de_movilidad`, `test_cadena_de_niveles`, `test_guardado_y_cadena`, `test_toolchain_consistency` |
| Mecánicas F5 | `test_mecanicas_f5`, `test_lianas_y_tirolesas`, `test_inundacion_que_sube`, `test_scroll_forzado_desde_tiled`, `test_vista_cenital`, `test_mecanicas_que_no_conectaban`, `test_reloj_musical`, `test_bloques`, `test_interactables` |
| VFX/post | `test_particle_systems`, `test_dibujado_de_particulas`, `test_lighting`, `test_post_processing`, `test_postprocesado_no_se_duplica`, `test_aberracion_cromatica`, `test_rayos_de_luz`, `test_refraccion_bajo_el_agua`, `test_agua_configurable`, `test_fog` (en `test_*` de niebla), `test_trails`, `test_day_night`, `test_seasons`, `test_ambience`, `test_gpu_y_panel`, `test_cada_pasada_ejecuta_su_shader` |
| UI/escenas | `test_hud`, `test_message_box`, `test_menu_navigation`, `test_legibilidad_de_menus`, `test_legibilidad_del_jugador`, `test_ui_consistency`, `test_demo_centering`, `test_demo_scenes`, `test_scene_smoke`, `test_scene_manager`, `test_scene_registry_integrity`, `test_subida_de_la_escena`, `test_modos_que_no_se_veian`, `test_menus_que_no_hacian_nada`, `test_reported_ui_bugs` |
| Persistencia/seguridad | `test_save_manager`, `test_corrupt_saves_are_loud`, `test_datos_hostiles`, `test_seguridad_del_motor`, `test_speedrun_datos_hostiles` |
| Economía | `test_inventario_recoleccion`, `test_equipar_desde_el_inventario`, `test_tienda`, `test_ropa_que_hay_que_ponerse`, `test_puntuacion_que_se_ve`, `test_los_recogibles_se_distinguen` |
| Diálogo/cutscenes | `test_dialogo_y_cutscenes`, `test_dialogo_desde_datos`, `test_dialogo_alcanzable`, `test_cutscenes_desde_el_mapa`, `test_fantasma_del_speedrun` |
| Académico | `test_academic_units`, `test_logros_en_catalogo`, `test_logros_por_estudiante`, `test_bestiary_roster`, `test_bestierio_desde_catalogo`, `test_teaching_tools`, `test_student_guidance`, `test_student_template`, `test_grade*` |
| Procesamiento | `test_filter_tools`, `test_vision_tools`, `test_edge_detection`, `test_color_tools`, `test_curve_tools`, `test_pattern_recognition_tools`, `test_pattern_demo`, `test_noise_lab`, `test_filter_demo_perf` |
| Infra/auditoría | `test_audit_regressions`, `test_auditoria_157_160`, `test_rutas_de_los_documentos`, `test_documentos_sin_duplicar`, `test_documentacion_bilingue`, `test_apis_que_nadie_llamaba`, `test_sistemas_huerfanos`, `test_orphan_systems`, `test_dependencias_que_se_usan`, `test_dependencias_coherentes`, `test_version_coherence`, `test_architecture_doc_matches_tree`, `test_guia_del_motor`, `test_gameplay_integration`, `test_event_integration`, `test_input_injection`, `test_visual_regression`, `test_mutacion` |

**Benchmarks** (`tests/benchmarks/`): `test_startup_benchmark`, `test_render_benchmark`
(1.000/2.000 sprites), `test_physics_benchmark`, `test_performance_budget`, `test_memory_benchmark`;
`tests/test_frame_budget.py`, `test_composicion_del_tiempo.py`, `test_benchmarks.py`.
**Playtest** (`tests/playtest/`): `bot.py` (robot que juega), `jump_bench.py` (tabla de saltos).

---

## 20. CI y validadores

`.github/workflows/ci.yml` — ramas `prod`/`pprod`/`dev` (¡no `main`!). 3 jobs:

1. **test** (matriz 3.11/3.12/3.13): ruff → mypy (trinquete) → `pip-audit` (no bloqueante) →
   `check_dependency_sync` → `generate_tmx_reference --check` → `check_translations --ci` →
   `check_achievements` + `check_bestiary` → `check_tmx_coverage --ci` → pytest con cobertura →
   sube reporte.xml y coverage.xml.
2. **mutation** (semanal o manual, `workflow_dispatch`): `mutation_check.py --ci`.
3. **validate**: `validate_assets.py` → `validate_tmx.py --ci` → `grade_stage.py assets/maps/ --json`
   → `grade_boss.py src/stages/boss_venado/boss_venado.py --json`.

**Trinquete de tipos (`mypy_scope.txt`):** solo `src/engine/core` y `src/engine/input`.
**Ruff:** línea 120, objetivo py311, reglas E/F/B/UP/I/RUF/LOG/G/DTZ; `src/stages/` NO se lintea
(excepto `stage0`); `revisar/` jamás.

---

## 21. Auditoría: implementado / huérfano / a medias

> Fuentes: `62_ESTADO_DEL_PROYECTO.md`, `63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md`, `KNOWN_GAPS.md`,
> `70_INFORME_DE_AUDITORIA_VIVO.md` (iteraciones 1-13; `51_IMPLEMENTATION_AUDIT.md` se retiró en la
> limpieza de docs de 2026-08-06 y vive sólo en el historial de git).
> Método: cada fila indica si existe código que lo respalde y si algo lo invoca.

### 21.1 Implementado y verificado (resumen por dominio)

| Dominio | Estado medido |
|---|---|
| Núcleo | 800×600 @60 FPS; 3 relojes; time_scale compuesto; event bus por inyección; `SceneRegistry` perezoso |
| ECS | Bajo la herencia; 20 componentes; coste medido 9.07 vs 9.42 ms por fotograma |
| Jugador | 30 estados; 5.0 HP; combate completo; arco; estamina opt-in |
| Enemigos | 65 tipos registrados (22 clases base + 35 especies + jefes ref) sobre 15 estados; squad brain con sklearn (lote 9 filas: 1.82 ms vs 11.87 ms) |
| Jefes | Fases, telegrafía, puntos débiles, parry, invocaciones, arena |
| TMX | 50 tipos del framework + 65 de entidades, más `Solid`/`Platform` en `Collision` (115 declarables; ver §7.3); 18 propiedades; 8 capas |
| Mecánicas F5 | 11/11 en el motor (stage_mecanicas las enseña) |
| VFX | Luz, bloom, viñeta, clima, partículas, día/noche, estaciones, niebla, agua, estelas, números de daño |
| Persistencia | Atómica, hostil-probada |
| Accesibilidad | Daltonismo ×4, texto ×2, movimiento reducido, foco no cromático |
| Herramientas | preview/validate/grade/check ×6 + auditoría doc↔código |
| Calidad | ~2.872 pruebas; ruff limpio; Stage0 130/130; 16 niveles integrados y calificados (media 78.7 %) |

### 21.2 Huérfanos (existen en código, nadie los invoca)

| Símbolo | Dónde | Estado |
|---|---|---|
| `LuaScriptEnemy` (IA en Lua) | `framework/ai/lua_script.py` | **No conectado** (AUD-022); completo y probado solo |
| ~~`TiempoBala`~~ | `stage/level_mechanics.py` | **Resuelto (AUD-260)**: `Action.BULLET_TIME` en `Q`/`R`, propiedad de mapa `tiempo_bala` (0 = apagado, como la estamina de AUD-141) y barra de HUD que sólo aparece si el escenario la pide |
| ~~`EnjambreDeBalas`~~ | `ecs/bullet_swarm.py` | **Resuelto (AUD-263)**: la nube de esporas de la fase 2 de `boss_venado` |
| ~~`BossPhase.escala` / `escala_de_fase`~~ | `boss_base.py` | **Resuelto (AUD-257).** `_aplicar_escala_de_fase()` redimensiona la caja anclada por los pies y escala el sprite; `boss_venado` declara `escala=1.25` en su fase 2 |
| ~~`BossBase.teletransportar`~~ | `boss_base.py` | **Resuelto (AUD-257).** `boss_venado` lo llama en su transición de fase: reaparece en el centro de la arena |
| ~~`skill_parry`~~ | inventario | **Resuelto (AUD-263)**: lo suelta `boss_venado` junto al dash; `skill_drop` acepta ahora una lista sin romper la forma antigua |
| ~~`play_voz` (voces)~~ | `audio_manager.py` | **Resuelto (AUD-263)**: el venado habla en cada cambio de fase y al morir; las líneas se sintetizan con el mismo generador que el resto del audio |
| `reverberación por zona` | — | **Imposible en SDL**; documentado, no defecto |
| `PresentadorGPU` | `engine/render/gpu_present.py` | Apagado por defecto (GPU 5× más lenta sin tarjeta real; AUD-148) |

### 21.3 A medias (existe, pero no cumple lo que promete)

| Elemento | Qué falta |
|---|---|
| ~~`BossRushMode`~~ | **Resuelto (AUD-261)**: `StageScene` conduce el modo — acredita el combate, cuenta los golpes y acumula el tiempo con `dt` sin escalar. La salud se arrastra con `CURACION_ENTRE_COMBATES`. Queda la superposición de interfaz |
| `BossGavilan` | Clase **parcial** (fase orbital); el spec 17 describe 22 patrones de ataque que ningún jefe implementa. `63` §2 decía que no existía: caducó, y lleva su corrección desde AUD-254 |
| `stage_scene.py` | **1.857 líneas medidas el 2026-08-04** contra un presupuesto de 1.500: ya se partió en mixins (AUD-152) y el fichero volvió a crecer (GAP-015). La prueba está en rojo a propósito |
| `Tubería GL` | Existe completa (doc 74) pero es opcional y más lenta en hardware común; el motor vive en post-procesado CPU |
| `49_AMBIENT_AUDIO` | "El sistema existe, faltan assets" |
| `Stage0` | Usa 4 de 11 mecánicas F5 (liana, tirolesa, bloques rítmicos, viento); las otras 7 viven en el laboratorio `stage_mecanicas` (no es un nivel) |
| Bestiario | Completamente conectado (AUD-154/199/245); antes huérfano parcial, hoy resuelto |

### 21.4 Documentado pero desincronizado del código (los docs mienten; el código gana)

- `07_STAGE0_DESIGN.md`: especificaba mapa 240×14; el real es 100×38.
- `03_ARCHITECTURE.md` (histórico): `transitions.py` con 5 clases y **cero usos**.
- `17_BOSS_SPEC.md`: 22 patrones (`BODY_SLAM`, `DIVE_BOMB`, `MASK_BEAM`, `ORBIT_SHRINK`, …) que
  ningún jefe implementa + habla de 4 jefes cuando el Gavilán es parcial.
<!-- cita-historica -->
- `05_ENEMY_SPEC.md`: `WIND_UP` (no existe; es `TELEGRAPHING`), `detection_rect`/`patrol_origin`
<!-- /cita-historica -->
  (nombres viejos), 3 SFX por enemigo (el motor usa 2 por tamaño).
- `09_HUD_SPEC.md` / `04_PLAYER_SPEC.md` / `11_*` / `12_*` / `14_*`: nombres de API antiguos
<!-- cita-historica -->
  (`hurt_display_timer`, `_health`, `facing_direction`, `KERNEL_X`, `label_array`, …).
<!-- /cita-historica -->
- `22_API_CONTRACTS.md` (histórico): módulos eliminados (`utils/spritesheet.py`,
  `scene/transitions.py`).
- Conteos de estados: docs 19/25/26/27 según edición; **el código tiene 30**.
- `EnemyState`: 4 miembros en 22_API vs **15 en código**.
- Brute HP: 6.0 en GDD vs **5.0 en código**.
- Conteos de tipos: doc 62 dice 104/54 (2026-08-30); **el código declara 50 tipos de framework** (+ 54 entidades + 2 de
  colisión = 104 declarables; ver §7.3 y `tests/test_el_inventario_cuenta_bien.py`). *(Nota 2026-08-30: doc 60 actualizado a 104 y 54; la cifra viva es la de `test_el_inventario_cuenta_bien.py`.)*
- README (histórico): "1.333 tests ES / 640 EN"; real ~2.872.

### 21.5 No implementado por decisión (no es deuda, es diseño)

- **3D**: no (la tubería GL de 479 líneas no es un scene graph; 2.5D es viable).
- **Traducir los 95 docs**: no (bilingüe solo donde hay lector: README + informes auditables).
- **Lintear `src/stages/`**: no (164 avisos de estilo; es trabajo de estudiantes).
- **gettext**: no (herramientas GNU externas; catálogos JSON propios).
- **Pip split en paquetes / multi-engine**: no (rompería las 26 entregas; 0 ciclos reales de
  import medidos).
- **Roadmap `50_IMPROVEMENT_ROADMAP.md`**: ~10 % implementado (174 ítems; P0 3/3 resueltos;
  P1 3 %, P2 5 %, P3 0 % a la fecha del audit 51).

---

## 22. Brechas abiertas (GAPs) y advertencias

| GAP | Tema | Qué significa para el usuario |
|---|---|---|
| ~~GAP-024~~ | Calibración del salto | **Decidido (AUD-264)**: el calificador se queda como está y `docs/60` §5 documenta la tabla honesta —natural 3 baldosas, experta 5— con el aviso de que la envolvente asume salto aéreo encadenado. Apretarla habría rebajado notas ya puestas; conectar el salto aéreo habría cambiado la física de 17 mapas |
| ~~GAP-030~~ | Boss Rush | **Resuelto (AUD-261)**: marcador, recuento de golpes y arrastre real de salud con curación parcial declarada (`CURACION_ENTRE_COMBATES`). Queda sólo la superposición de interfaz |
| ~~GAP-031~~ | Voces | **Resuelto (AUD-263)**: tres líneas del venado sintetizadas por el mismo camino que todo el audio del proyecto |
| ~~GAP-032~~ | **0** mecánicas F5 sin invocar | **Cerrado (AUD-263)**. Resueltas: parry de jefe (AUD-243), scroll forzado (AUD-249 + AUD-258), `escala_de_fase` y `teletransportar` (AUD-257), tiempo bala (AUD-260, propiedad de mapa `tiempo_bala`) y bullet hell (AUD-263, esporas del venado) |
| GAP-015 | `stage_scene.py` | **1.857** líneas medido vs presupuesto 1.500; la partición en mixins está hecha y el fichero volvió a crecer |
| GAP-002 | Colisión X-skip | Heurística `tile.top >= player_rect.centery` para el salto de eje X; sin casos que fallen aún. **Puede estar ya cerrado**: hay trabajo sin commitear del frente paralelo que la sustituye por solape vertical con la posición previa |
| ~~GAP-021~~ | Números duplicados de docs | **Resuelto (AUD-265)**: diez documentos movidos a 77–86 con `git mv` y todas las referencias reescritas; las series (`ASSIGNMENT_01`…`04`) conservan su número |
| ~~GAP-022~~ | `requirements.lock` | **Resuelto (AUD-262)**: `uv pip compile --python-version 3.11 --universal` resuelve para una versión objetivo sin necesitar ese intérprete; comprobado en 3.11/3.12/3.13 |

**Trampas frecuentes (de doc 60 §18):** falta de rect de Collision → caerse del mundo; tamaño de
tileset equivocado → baldosas negras; `visible` es un nombre reservado; dos `PlayerSpawn` →
error; faltan las 3 propiedades obligatorias → error; `ambient_fx` inválido → error; luz ambiente
alta → las luces no se ven; `patrol_length` ausente en Shooter → se queda pegado; `enemigo.velocity`
siempre es (0,0) por diseño.

---

## 23. Glosario

| Término | Significado |
|---|---|
| `src/engine/` | Motor: bucle, escenas, input, audio, render, UI, persistencia (lo que no cambia por entrega) |
| `src/framework/` | Marco de juego: jugador, enemigos, jefes, ECS, VFX, TMX, cutscenes (lo que los estudiantes usan) |
| `src/stages/` | Entregas: 16 escenarios (12 niveles + 4 jefes). Código de estudiantes (excepto `stage0`, `stage_mecanicas`, `boss_venado`) |
| `StageScene` | Escena jugable que carga un TMX; base de todo escenario |
| `StageData` | Contenedor de todo lo cargado de un TMX |
| `Events` | Catálogo central de eventos del bus |
| `GameContext` | Contenedor de dependencias (DI) que recibe cada escena |
| `StageLoader` | Cargador TMX con caché y registro de tipos de entidad |
| `Planificador` / `Fase` | Scheduler ECS con fases numeradas |
| `GAP-NNN` / `AUD-NNN` | Brecha conocida / defecto auditado y corregido |
| `Trinquete (mypy)` | Lista `mypy_scope.txt`; no puede encoger |

---

## Fuentes

`docs/60_GUIA_COMPLETA_DEL_MOTOR.md` (referencia general), `62_ESTADO_DEL_PROYECTO.md`,
`63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md`, `70_INFORME_DE_AUDITORIA_VIVO.md`,
`73_CATALOGO_DE_RECURSOS_PARA_ESTUDIANTES.md`,
`74_TUBERIA_DE_GPU.md`, `KNOWN_GAPS.md`, y verificación directa de
`src/engine/` (95 ficheros), `src/framework/` (101 ficheros), `src/stages/` (16 escenarios),
`scripts/` (28), `tools/` (13), `tests/` (161), `pyproject.toml`, `.github/workflows/ci.yml`,
`main.py`.
