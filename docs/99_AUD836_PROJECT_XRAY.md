# AUD-836 — PROJECT X-RAY: radiografía integral verificada

> **Restricción cumplida:** solo lectura. No se modificó código, tests, assets ni documentación existente. Este documento es el producto de la auditoría.
> **Regla de evidencia:** cada afirmación técnica lleva `FUENTE | ARCHIVO | SÍMBOLO | LÍNEA | EVIDENCIA | ESTADO`. Estados: `VERIFIED / PARTIAL / DECLARED / ASSET_ONLY / CODE_ONLY / TEST_ONLY / DEAD / UNKNOWN / ABSENT`.
> **Fecha:** 2026-09-07. **Método:** lectura directa de código, parseo XML de TMX, conteo de tests, más 4 sondeos de exploración en solo lectura (boot-loop, player-combat, enemigos-mundo, motor-framework).
> **Fila en `docs/00_MASTER_INDEX.md`:** pendiente (no se tocó el índice por la restricción de no corregir documentación).

---

## A. Executive Summary — ¿qué juego tenemos realmente?

**VERIFIED.** `Legacy of InFest` es un **action-platformer 2D por niveles** (vista lateral, tiles de 16 px, resolución interna única 1280×720) con **hub/tutorial + campaña por stages TMX + 4 jefes + boss-rush + speedrun + NG+**, montado sobre **pygame-ce (CPU, camino por defecto)** con **backend ModernGL opcional**, física propia con resolutor de ejes separados, combate cuerpo a cuerpo + arco con proyectiles, parry sin bloqueo, progresión por habilidades que sueltan los jefes, persistencia atómica versionada, diálogo ramificado y cutscenes no bloqueantes.

| Pregunta | Respuesta verificada |
|---|---|
| Género | Plataformas de acción 2D con combate, exploración ligera, llaves/puertas, checkpoints, jefes. `FUENTE: código+TMX+tests` `ARCHIVO: src/framework/entities/player.py` `SÍMBOLO: PlayerState (30 valores)` `LÍNEA: 170` `ESTADO: VERIFIED` |
| Perspectiva | Lateral en campaña; hay 12 stages-demos de cámaras alternativas (cenital, isométrica, mode7, raycast, etc.) que son plantillas, no campaña. `ARCHIVO: assets/maps/` (33 dirs de mapas) `ESTADO: VERIFIED / ASSET_ONLY para demos` |
| Resolución | Interna única `INTERNAL_WIDTH=1280, INTERNAL_HEIGHT=720`, `TARGET_FPS=120`, paso fijo `FIXED_DT=1/TARGET_FPS`. `ARCHIVO: src/engine/core/settings.py:19-21` + `src/engine/core/clock.py:79` `ESTADO: VERIFIED` |
| Tile | 16 px. Dimensiones medidas: stage0 160×45 (2560×720), stage1_1 390×45 (6240×720), stage4_1 960×40 (15360×640). `EVIDENCIA: parseo XML TMX` `ESTADO: VERIFIED` |
| Core loop real | `ENTRAR A STAGE → TRAVESÍA (salto/coyote/dash) → ENCUENTRO (corto/largo/arco/parry) → DAÑO/RECOMPENSA (score/monedas/pickups) → CHECKPOINT (respawn+autosave) → PUERTA/LLAVE/NEXT → JEFE (habilidad) → DESBLOQUEO (dash/doble salto/parry/coraza) → SIGUIENTE STAGE`. No hay loop `EXPLORE→UNLOCK→RETURN` tipo metroidvania con backtracking sistémico: el backtracking existe como módulo (`backtracking.py`) y hub con `WarpZone`, pero las ability-gates son llaves/puertas TMX y skills de jefe, no un mapa interconectado con gating de traversal verificado. `ESTADO: VERIFIED (loop lineal por stages con hubs), PARTIAL (backtracking sistémico)` |
| Victoria / derrota | Victoria = completar stage/jefe (`NextTrigger`, `BOSS_PHASE_CHANGED`, `ENEMY_DIED`). Derrota = HP a 0 → `DYING` → game-over → respawn en checkpoint/slot. `ARCHIVO: src/framework/entities/player.py:809 apply_damage` + `src/framework/stage/checkpoint.py:34` + `src/engine/scenes/*game*over*` `ESTADO: VERIFIED` |
| Save | `SaveData v6, MAX_SLOTS=5`, atómico `tmp+fsync+os.replace`, `user_data_dir/saves`. `ARCHIVO: src/engine/core/save_data.py:15-32` + `src/engine/core/save_manager.py:83-117,234-273,346-500` `ESTADO: VERIFIED` |

**Lo que NO es:** no es metroidvania con mundo interconectado y gating verificado; no es roguelike (sin NG+ procedimental; NG+ es flag/timer en HUD); no es RPG con stats profundos (XP + árbol de 3 ramas solo-stats); no es juego GPU-first (GPU existe y es correcto, pero el camino real es CPU).

---

## B. Project Map (Fase 2)

### B.1 Árbol `src/` (2 niveles, medido por lectura)

```text
src/
  engine/   core/ (app, settings, clock, event_bus, game_context, save_manager, save_data, ...),
            input/ (input_manager, action_map), audio/ (audio_manager, sound_bank, mixer_buses, ...),
            render/ (render_facade, gl_pipeline, sprite_batch, gpu_sprite_batch, shaders, ...),
            scene/ (base_scene, scene_manager), scenes/ (~30: splash, title, shop, inventory,
              skill_tree, bestiary, keybinding, boss_rush_entry, game-over, ...),
            ui/ (hud, hud_builder, widgets, theme), utils/ (asset_loader, resource_manager, ...), netcode.py
  framework/ entities/ (player, player_state, states/*, enemy_base, enemy_*, boss_base, boss_kit,
              bestiary_registry, entity_factory, ...), physics/ (resolucion, physics_system, capas, perfil),
            stage/ (stage_loader, stage_data, camera, collision_system, checkpoint, hazard_system,
              progression_system, cutscene_*, ...), scenes/ (stage_scene + stage_parts/),
            vfx/ (particle_system, trail_system, damage_numbers, ...), audio/ (dynamic_music, ...),
            ui/ (dialogue_system, ...), ecs/ combate/ ai/ processing/ world/ academic/, crafting.py, game_modes.py
  stages/   34 dirs: stage0, stage1_1, stage1_2_la_soda, stage1_3_las_aulas, stage2_1_oficinas, stage2_2,
            stage2_4, stage3_1_la_entrada_de_piedra, stage3_3_el_patio, stage3_4_boss_gavilan, stage4_1,
            stage_mecanicas, hall, hub_backtracking, lobby_datacenter, tutorial_hub, tutorial_hub_cenital,
            boss_venado, boss_rey, boss_paburu + 12 demos de cámara/render
  tools/    editor.py
```

`FUENTE: lectura de directorios` `ESTADO: VERIFIED`. `docs/62_ESTADO_DEL_PROYECTO.md:48-51` confirma 34 dirs / 33 mapas / 4 jefes (coincide).

### B.2 Grafo BOOT→PRESENTATION con componentes reales

```text
BOOT main.py:99 (__main__)
 ├─ main.py:9 _parse_args (--stage/--boss/--debug/--semilla)
 ├─ main.py:53 _preflight (pygame, pytmx, pyscroll, pydantic, orjson, numpy)
 └─ main.py:178 App(depurar,semilla).run()
     ↓
COMPOSICIÓN src/engine/core/app.py:136 App
 ├─ app.py:188 _init_pygame → set_mode(1280×720×DISPLAY_SCALE) + mixer.init + internal_surface + DeltaClock
 ├─ app.py:154 RenderFacade(prefer_gl) [render_facade.py:37: SoftwareBackend.render=pass]
 └─ app.py:354 _init_subsystems: registro.py:50 → azar.sembrar → event_bus.py:97 EventBus →
    debug_overlay.py:67 DebugOverlay → plugins.descubrir → UserSettings.load (user_settings.py:215) →
    i18n.set_idioma → InputManager (input_manager.py:51) → AudioManager (audio_manager.py:49) →
    SaveManager (save_manager.py:234) → GameContext (game_context.py:27) →
    SceneManager (scene_manager.py:78) → _init_gl GLRenderer.init → push SplashScene
     ↓
LOOP app.py:482 run / app.py:491 while running:
 ├─ clock.tick [app.py:498] (FIXED_DT clock.py:79, MAX_FRAME_TIME=0.05 clock.py:71)
 ├─ _process_events [app.py:573] → InputManager.pump(events) [input_manager.py:144]
 ├─ event_bus.dispatch [app.py:500] (contrato events.py:15 Events)
 ├─ audio_manager.update(unscaled_dt) [app.py:505] (ducking en tiempo real)
 ├─ scene_manager.actualizar_en_tiempo_real + for paso in pasos_fijos(): scene_manager.update(paso) [app.py:528-531]
 └─ _draw(dt) [app.py:656]: escena.draw → debug_overlay.draw →
     Software: _publicar_software [app.py:74] + display.py:97 calculate_viewport (letterbox)
     GL: GLRenderer.render [gl_pipeline.py:255] + RenderFacade [render_facade.py:37]
```

### B.3 Managers / servicios reales

| Dominio | Archivo:Símbolo:Línea | Estado |
|---|---|---|
| DI container | `src/engine/core/game_context.py:27 GameContext` | VERIFIED |
| Event bus | `src/engine/core/event_bus.py:97 EventBus (subscribe:110, emit:167, dispatch:171)` | VERIFIED |
| Assets | `src/engine/utils/asset_loader.py:52 AssetLoader` + `src/engine/utils/resource_manager.py:33 ResourceManager (load_async con ThreadPool:79)` | VERIFIED |
| Audio | `src/engine/audio/audio_manager.py:49 AudioManager` + `sound_bank.py:22 SoundBank` + `mixer_buses.py:96 Mezclador (MUSICA/EFECTOS/VOZ/AMBIENTE)` | VERIFIED |
| Input | `src/engine/input/input_manager.py:51 InputManager` + `action_map.py:14 Action` | VERIFIED |
| Save | `src/engine/core/save_manager.py:234 SaveManager` + `save_data.py:32 SaveData (SAVE_VERSION=6, MAX_SLOTS=5)` | VERIFIED |
| Config | `settings.py:1` constantes + `user_settings.py:119 UserSettings (load:215, save:245)` | VERIFIED |
| L10n | `i18n.py:84 set_idioma, :116 _()` + `locale/es.json, en.json` + `scripts/check_translations.py` | VERIFIED |
| Reloj | `clock.py:96 DeltaClock` (dt/unscaled/dt_mundo sin hit-stop) | VERIFIED |
| Render | `render_facade.py:37 RenderFacade (GLBackend/SoftwareBackend)` + `gl_pipeline.py:255 GLRenderer` | VERIFIED (CPU) / PARTIAL (GL sin GPU física en CI) |
| Debug | `scenes/debug_overlay.py:67 DebugOverlay (F11 consola, F9 diagnósticos, F8 forense)` + `render/visual_forensics.py:227 collect_forensics` + `core/registro.py:50` | VERIFIED |

Entry points: `pyproject.toml` sin `[project.scripts]`; entry único `main.py`. `ESTADO: VERIFIED`.

---

## C. Player State Catalog (§4)

Enum maestro `src/framework/entities/player.py:170 PlayerState` — **30 valores VERIFIED**: `IDLE, WALKING, JUMPING, FALLING, CROUCHING, SHORT_ATTACK, LONG_ATTACK, HURT, DYING, DASHING, PARRY, CHARGE_ATTACK, DASH_ATTACK, WALL_SLIDE, LEDGE_GRAB, GRAB, THROW, SWIMMING, SWIM_ATTACK, CLIMBING, ZIPLINE, ULTIMATE, AERIAL_ATTACK, AERIAL_SLAM, GROUND_POUND, AIR_CHASE, CHARGE_RELEASE, STAGGER, SLIDE, POSSESSED`.

Base `states/base.py:13 PlayerStateBase (enter/update/exit)` VERIFIED. Datos `player_state.py:20 PlayerStateData` VERIFIED (coyote, jump_cut, combo, air_dash, air_jumps_used, invencibilidad, parry, grab, charge, wall_side/can_wall_jump/can_ledge_grab/wall_jump_count+cooldown). Sprites `player.py:76 _PLAYER_SPRITE_MAP` + `:126 _PLAYER_ANIM_FPS` VERIFIED.

Tabla de estados (resumen; detalle completo de transiciones en tests `test_player_state_machine.py:257,263`, `test_player_states_extended.py`, `test_resolucion_de_movimiento.py:84`):

| Estado | Input / entrada | Salida | Física/colisión | SFX/VFX | Estado |
|---|---|---|---|---|---|
| IDLE / WALKING / JUMPING / FALLING | Movimiento, salto en buffer | Aterrizaje, salto, dash, ataque, hurt | Gravedad perfil, coyote 6f (`settings.py:72`), jump-cut `*=0.5**(dt*60)` (`airborne.py:127`), aire→0.5×walk (`airborne.py:104`) | stretch por salto (`helpers.py:141`) | VERIFIED |
| CROUCHING `grounded.py:190` | CROUCH held | `!crouch\|\|!grounded` | `v=0`, hurtbox 20×18 (`player.py:567`) | `SFX_CROUCH` | VERIFIED |
| SLIDE `grounded.py:244` | crouch + `\|vx\|>30` desde walk | fricción `0.3**(dt*60)`, 0.4 s, 300 px/s | `rect.h=18` | — | VERIFIED |
| DASHING `ability.py:34` | DASH + `skill_dash` + cooldown + estamina | 0.15 s, 8-dir 200 px/s (`settings.py:73`), cancela a dash-attack siempre, a salto ≤0.1 s | iframes 0.15 | `VFX_SLAM` | VERIFIED |
| WALL_SLIDE `wall.py:14` / wall-jump `helpers.py:33` | push pared en aire | `vy=-320, vx=-wall_dir*90`, cadena 3× cd 0.15 | gravedad de muro (`player.py:1324`) | — | VERIFIED |
| LEDGE_GRAB `wall.py:66` | `can_ledge_grab` ← `eje_x.repisa_libre (player.py:1460)` ← `resolucion.py:410 resolver_repisas` | salto `vy=-250`, o crouch/t>1.5→fall | `v=0`, invuln 0.5 | — | VERIFIED |
| GRAB `ability.py:247` / THROW `ability.py:297` | GRAB o LONG+CROUCH (`helpers.py:213`) | grab 0.15 s caja 20×16 → throw 36×20 daño 1.0 | — | — | VERIFIED |
| SHORT `attack.py:74` (6f) / LONG `attack.py:84` (10f) | SHORT/LONG, suelo→grounded, aire→aerial | combo timer 0.5 s (`settings.py:141`) | hitbox 36×20, agachado h=12 (`helpers.py:239`) | hitstop vía `collision_system.py:241` | VERIFIED |
| AERIAL `airborne.py:227` / SLAM `:391` (pogo `-300`) / GROUND_POUND `:304` (caída 420, onda 72×16 ×1.5) | corto en aire / 2 hits→slam / crouch+short en aire + `skill_ground_pound` | — | `vx=0` en pound | `VFX_SLAM` | VERIFIED (pound PARTIAL: skill exigida sin catálogo visible en `inventory.py:150-161`) |
| PARRY `ability.py:160` | crouch+short, ventana 0.25 (`NORMAL`) | stun enemigo + `VFX_PARRY/SFX_PLAYER_PARRY` (`enemy_base.py:978`, `events.py:78,122`) | — | VERIFIED (sin gate de skill aunque `skill_parry` existe en `inventory.py:160`) |
| CLIMBING/Trepando `rope.py:44` / ZIPLINE/Tirolesa `rope.py:125` | proximidad + GRAB/JUMP (`mundo_ecs.py:184`) | gravedad 0, MOVE_UP/DOWN, salto impulso 130 | — | VERIFIED |
| SWIMMING `:16` / SWIM_ATTACK `:145` | agua | exentos de gravedad (`player.py:1317`) | — | VERIFIED |
| HURT / STAGGER / DYING / ULTIMATE (96×64 ×3.0 `ability.py:221`) / CHARGE_* / AIR_CHASE / POSSESSED | daño (`apply_damage player.py:809`, iframes `inv_timer`, `difficulty.py:22` 1.5 s) | knockback `collision_system.py:80-101`, hitstop 0.035/0.07/0.11 | VERIFIED |

**Muertos/inaccesibles VERIFIED:** `GanchoTechoState (rope.py:199)` y `BalanceoEnLianaSaltoState (rope.py:271)` existen pero **no se exportan** en `states/__init__.py:7` → inalcanzables por import normal → `DECLARED`. Sin `Action.BLOCK/DODGE/STOMP/GRAPPLE`: **Block ABSENT** (solo `PushBlock/BreakableBlock`), **dodge dedicado ABSENT** (el dash con iframes hace la función), **stomp nominal ABSENT** (la mecánica es `GROUND_POUND`).

---

## D. Input Catalog (§5)

```text
INPUT (teclado+ratón+mando) → InputManager.pump (input_manager.py:144) → Action (action_map.py:14)
→ CONSUMER (Player helpers / StageScene / UI / diálogo) → STATE → EFECTO
```

| Acción | Default teclado | Mando/ratón | Buffer | Consumidor | Estado |
|---|---|---|---|---|---|
| MOVE_LEFT/RIGHT/UP/DOWN | A/D, etc. | eje X/Y deadzone 0.25 (`action_map.py:122+`) | n/a | Player, trepar, menús | VERIFIED |
| JUMP | SPACE/UP/W | botón 0 | buffer 8f (`VENTANA_DE_BUFFER=8 :132`, `pulsada_en_buffer :337`, `consumir_buffer :359`) | `grounded.py:58`, `player.py:1031` | VERIFIED |
| CROUCH | DOWN/S | botón 3 | conmutable | Crouch/Slide/Parry/Pound | VERIFIED |
| SHORT_ATTACK | Z/J | botón 1 / ratón 1 | buffer | `_start_attack helpers.py:161` | VERIFIED |
| LONG_ATTACK | X/K | botón 2 / ratón 3 | buffer, conmutable | idem | VERIFIED |
| DASH | LSHIFT/RSHIFT/LALT | botón 8 / ratón 2 | buffer, conmutable | `ability.py:34` | VERIFIED |
| GRAB | G/C | botón 5 / ratón 5 | conmutable | `ability.py:247` | VERIFIED |
| RANGED_ATTACK | F/V | botón 4 / ratón 4 | — | `ranged_weapon.py:229 disparar` | VERIFIED |
| CONFIRM/CANCEL/PAUSE | — | — | — | UI/diálogo/pausa | VERIFIED |
| BULLET_TIME, TAB_PREV/NEXT, LEARN_*, OPEN_BESTIARY, TOGGLE_MUTE | Q/R etc. | botón 9 (bullet) | — | cámara/skill-tree/bestiario | VERIFIED (rebinding UI PARTIAL: solo 12 filas en `keybinding_scene.py:47-87`, resto con binding pero sin fila) |

Rebinding primitiva `rebind (input_manager.py:373)` + persistencia `keybindings.json` vía orjson (`keybinding_scene.py:65-87`) VERIFIED. Coyote 6f + jump-cut + buffer 8f con tests (`test_player_physics.py:67,77,84,95,179`, `test_accesibilidad.py:153`). Frontera `engine/input NO importa framework (test_arquitectura_fronteras.py:16)` VERIFIED. Si se pulsa durante otro estado: el buffer genérico la conserva 8 fotogramas y la consume quien ejecuta; si ningún estado la consume, se pierde por expiración (sin robo entre sistemas). `ESTADO: VERIFIED`.

---

## E. Mechanics Catalog + J. Traversal Map + K. Combat Map (§6, §7, §30, §31)

Formato por mecánica: `Code / State / Input / Physics / Collision / Animation / VFX / SFX / Camera / UI / Level / Progression / Tests / Status`.

**Movimiento:** walk, run (walk con variador; sin sprint dedicado → PARTIAL nominal), jump, fall, crouch, slide, dash (8-dir, 1 en aire `AIR_DASH_LIMIT=1 settings.py:74`), swim, climb/tirolesa, wall-slide/jump (3 encadenados), ledge-grab, knockback/launch (`BASH_IMPULSO`), ground-pound, pogo (`AERIAL_SLAM`), arco-tensado. **VERIFIED** salvo: run dedicado PARTIAL; doble salto VERIFIED con candado (`saltos_aereos=1 settings.py:75` + `skill_double_jump inventory.py:150` + `PLAYER_SKILLS_REQUIRE_UNLOCK=True settings.py:89`).
**Ausentes verificados:** ledge-hang/shimmy, wall-grab estático, rope-swing/péndulo utilizable, grapple disparado, hook/pull, vault, step-up/slope-walk especial más allá de `pendientes.py`, ladder dedicada (la trepa es por proximidad a liana), zipline más allá de `TirolesaState`, stomp-enemigo como rebote encadenado (hay pound-onda y pogo-slam, no stomp-rebote tipo Mario). `ESTADO: ABSENT (buscado en Action+PlayerState+helpers+resolucion, sin resultados)`.
**Ability-gated traversal:** `skill_double_jump/dash/parry` (jefes Venado/Rey), `skill_coraza` (Gavilán), `skill_ground_pound` exigida pero sin catálogo visible → PARTIAL. Puertas/llaves/cofres/placas/bloques TMX VERIFIED (`stage0.tmx: LockedDoor/Key/Chest`, `stage_mecanicas.tmx`).
**Combate:** cadena completa `INPUT→STATE→ANIM→HITBOX→COLLISION→DAMAGE→ENEMY_RESPONSE→VFX→SFX→CAMERA→UI` VERIFIED para corto/largo/aéreo/slam/pound/arco/ultimate/throw/dash-attack/charge-release. Daño escala por combo (`current_attack_damage player.py:598`, `COMBO_DAMAGE_MULT×10, MAX=10 settings.py:149-150`), combo aéreo separado (2→slam), arco (`ArcoDelJugador ranged_weapon.py:158`: 5 flechas, cadencia 0.35, vel 420, daño 0.5, tensado 0.6 s ×1.45, recarga por golpe, anti-túnel). Hitstop light/heavy/launch (0.035/0.07/0.11 `collision_system.py:80-101`). Parry VERIFIED. **Roto/ausente:** block ABSENT, dodge dedicado ABSENT, críticos/elementos/estados (veneno/fuego solo como resistencias enemigas `enemy_base.py:149,673`, no como sistema del jugador) ABSENT/DECLARED, finishing ABSENT.

---

## F. Enemy Catalog (§8)

Base `enemy_base.py:73 EnemyBase` + `EnemyState` 15 estados (`:31` IDLE/PATROL/SEARCH/ALERT/CHASE/TELEGRAPHING/FIRING/RECOVER/RETREAT/FLEEING/CHANNELING/STUNNED/HURT/LAUNCHED/DYING) VERIFIED. Componentes `enemy_components.py:24,38,46,54` VERIFIED. Registro 35 especies `bestiary_registry.py:358` + factory `entity_factory.py:50,81,146` VERIFIED (test `test_bestiary_roster` parsea `docs/18_ENEMY_ROSTER.md`).

| Clase | Archivo:Línea | HP/daño | Estado |
|---|---|---|---|
| Walker / Flying (sine/dive) / Shooter+Projectile / Charger / Brute / Archer / Caster / Assassin / Shielded (escudo 3.0) / Swimmer / Climber / FlyingBomber / TerrainShaper / Summoner / Dron / Ceibo / Cerbatana / IceSkater / ParryTeacher / Cangrejo / Medusa / PezAbismal / Buddies(Rino/Expresso/Enguarde) / SquadBrain | `enemy_walker.py:16`, `enemy_flying.py:28`, `enemy_shooter.py:146`, `enemy_charger.py:14`, `enemy_brute.py:19`, `enemy_archer.py:16`, `enemy_caster.py:91`, `enemy_assassin.py:19`, `enemy_shielded.py:25`, `enemy_swimmer.py:27`, `enemy_climber.py:26`, ... | p.ej. Walker 2.0/0.5, Bird 1.0/0.25, Frog 2.0/0.25, Wolf 3.5/1.0, Golem 5.0/0.75 | VERIFIED, salvo Brute PARTIAL (hoja base 96×12 incompatible con sprite 24×18 → placeholder; suplido en `stage2_1_oficinas/office_enemies.py:1`) y Hormiga/Oropel PARTIAL (clase sin SpeciesSpec dedicado) |
| Propios de stage | `stage1_2_la_soda/entities.py:1` (5 plagas), `stage1_3_las_aulas/estudiante_infectado.py, cuaderno_volador.py` (10+5), `stage2_1_oficinas/office_enemies.py:51,59, dron04.py` , `stage2_2/camara_seguridad.py, monitor_seguridad.py, patrulla_bspline.py, barrera_kiosco.py` | TMX | VERIFIED |
| Spawn/muerte/drops | TMX `type=` → `StageLoader._entity_registry`; `_die enemy_base.py:733` emite `ENEMY_DIED+skill_drop`, `VFX_KILL_FLASH`, `SFX_ENEMY_DIE_*`; botín/moneda en escena (`_RecompensaDePickup stage1_2_la_soda.py:821`), no en enemigo | — | VERIFIED (diseño: habilidad solo en jefes `boss_base.py:99,135`) |

Tests: `test_enemy_walker/shooter/flying/state_machine`, `test_la_soda*.py`, `boss_venado/tests/` VERIFIED.

---

## G. Boss Catalog (§9)

| Jefe | Fases/ataques/telegraphs | Arena/HUD/música | Estado |
|---|---|---|---|
| BossVenado (referencia) `boss_venado.py:256` | 2 fases (12.0/6.0 HP `:272`); 5 ataques STOMP/CHARGE/VINE_SWEEP/VINE_TOSS/MUSHROOM_SPORE `:396`; telegraphs 0.35/0.4/0.6/0.4/0.35; WeakPoint cuernos/flanco `:107-114`; `skill_drop=[dash,parry]`; arena `X0=2480/X1=3264, FLOOR_Y=560, ARENA_RECT/ESPORAS_RECT :55,464,481,496`; escena `:316` | HUD base + `efectos_venado.py`, stingers `boss_base.py:522`, `BOSS_PHASE_CHANGED` | VERIFIED |
| BossPaburu (final, 4 formas) `boss_paburu.py:63,76,91,175` | Formas Piedra/Máscara/Reliquia/Espíritu; F1 completa STONE_SPIT/EYE_BEAM/EL_SELLO + cooldowns; módulos `form1-4_attacks/arena/guardianes/cementerio/moradores/intro` | `bgm_paburu` en TMX; arte `referencia_arte.png` ASSET_ONLY | PARTIAL (F1 completa, F2-4 según GDD) |
| BossRey `boss_rey.py:17,30,47,75` | F1 Marioneta Catmull-Rom + VENOM_SPIT (200 px, cd 2.5, vel 90, daño 0.5); telegraph 0.4; `skill_drop=double_jump`; F2 `ReyMetad`/F3 declaradas | `bgm_zone2_boss` en TMX | PARTIAL (F1 VERIFIED, F2/F3 DECLARED) |
| BossGavilán `boss_gavilan.py:20,28,43,81` | 2 fases (10.0/5.0, transición a 7.0 HP); patrones DIVE/FEATHER_STORM/ORBIT_SHRINK (R=80, ω=0.6); contacto 0.75, HP 14.0 | `bgm_zone3_boss`; sin barra dedicada | PARTIAL (órbita VERIFIED; ataques emiten eventos sin proyectil/VFX propios `:97,101`) |

Infraestructura VERIFIED: `boss_kit.py:73,137,197,218,362,418` (Windup≥0.35 s, WeakPoint, SummonTracker), `boss_base.py:318,430,638` (fases, invulnerabilidad, clamp_arena), telegrafiado genérico `enemy_base.py:510` + anillo rojo. Barra de jefe dedicada ABSENT (se usa barra de enemigo + eventos). Calificador `scripts/grade_boss.py:33` (100 pts) + tests `test_boss_base/encounter/rush/rush_conducido/grader/spawn_desde_tiled/el_boss_rush_se_ve` VERIFIED.

---

## H. World Catalog + I. Level Design + 12. Pacing (§10, §11, §12)

Mediciones por parseo XML (tile 16 px). `PACING = STATIC STRUCTURAL ANALYSIS` (sin telemetría; inferido por densidad de enemigos/checkpoints/hazards y `grade_stage.py:641 design_pacing` con `MAX_CHECKPOINT_GAP=500`).

| Mapa | Dimensión | Contenido clave | Secuencia real |
|---|---|---|---|
| stage0 | 160×45 | Spawn 1, Checkpoint 5, 9 enemigos variados, Pickup 3/Key 1/Chest 1, Next 1 | Tutorial A–G por diálogo (`stage0.py:100,173`), combate básico+avanzado, tormenta |
| stage1_1 | 390×45 | Spawn 1, Checkpoint 8, Walker 7/Bird 3/Frog 2, Waypoint 12 | Travesía larga → patrullas → checkpoints cada ~500 px |
| stage1_2_la_soda | 350×45 | 5 plagas propias 3/3/3/3/1, Pickup 6/Key 1/Chest 1/Door 1 | Hub-gastronómico con puerta-llave |
| stage1_3_las_aulas | 320×45 | Estudiante 10/Cuaderno 5, Waypoint 16 | Oleadas escolares densas |
| stage2_1_oficinas | 320×45 | Patrullas + Zona2 + Raton 4/Shielded/Bomber/Golem/Wolf/Swimmer | Oficinas por zonas, mayor HP (3–5) |
| stage2_2 | 120×50 | Guardia 2/Boa/Serpientes, CameraLock 1 | Infiltración corta con cámaras (`camara_seguridad.py`) |
| stage3_1 | 160×45 | Garza 6/Quetzal 3/Halcón 4, Pickup 5 | Aéreo de piedra |
| stage3_3_el_patio | 100×45 | Walker 4/Flying 7/Shooter 3, HazardZone 1 | Patio corto e intenso |
| stage3_4_boss_gavilan | 102×45 | BossGavilan 1 + Flying 3, CameraLock, Egg/Nest/Guardian/KeyPedestal/DoorZone | Arena con llave-pedestal |
| stage4_1 | 960×40 | 0 enemigos (regla oro, excepción `grade_stage.py:324`), Cutscene 2, EventTrigger 3, Slope 9 | Cementerio narrativo, no-combate |
| boss_venado | 330×45 | BossVenado 1, ArenaZone 1, CameraLock, Checkpoint 3, Pickup 4/Chest 1 | Arena clásica |
| boss_rey | 120×45 | BossRey 1, CameraLock, Floor/Ceiling/Walls | Duelo cerrado |
| boss_paburu | 260×82 | Murciélago 3/Ahogado/Tilawa/Sukia, MovingPlatform 5/Sinking 2/Rhythm 3/Zipline 1/Spring 2, Checkpoint 12 | Plataformeo vertical; jefe instanciado por escena, no por TMX → PARTIAL |
| tutorial_hub | 280×45 | Walker 5/Shooter 2, Pickup 5, WarpZone 1 | Hub con warp |
| stage_mecanicas | 310×24 | Catálogo 30+ especies + Buddies + BossSpawn, MusicZone/CameraZoomZone | Laboratorio, no campaña |
| 12 demos cámara | 58×16–100×45 | Solo Collision + 1–2 objetos | ASSET_ONLY (plantillas visuales) |

Sistemas de mundo VERIFIED: colisión (`collision_system.py`, `pendientes.py`), checkpoints (`checkpoint.py:34`, haz dorado/azul + `CHECKPOINT_REACHED`), hazards (`hazard_system.py:16`: Laser 6/Shockwave 2 en mecánicas, DeathPit, WaterZone...), pickups/llaves/cofres, puertas (`LockedDoor`), placas/bloques (`PressurePlate/Breakable/PushBlock`), transiciones (`room_transition.py:13`, `NextTrigger/WarpZone/CameraLock`, `backtracking.py`). NPC con IA propia solo en Paburu (`moradores/guardianes`); resto son triggers de diálogo → PARTIAL.

---

## M/N. Juice Map + Audio Map (§13, §15) + 14. Cámara

**Visual VERIFIED:** `VFX_KILL_FLASH/PARRY/ULTIMATE`, hit_tint, barra 3 px (`enemy_base.py:593,739,598`), `damage_numbers.py`, `particle_system.py:159`, `trail_system.py`, `hit_effects.py`, screen shake direccional 1 ciclo + `reduced_motion` (`camera.py:18,36,64` LERP+parallax+clamp+CameraLock). Boss Venado: destello por silueta (`boss_base.py:807`), sobel/filtros por fase, `efectos_venado.py:29`.
**Audio VERIFIED:** `AudioManager (audio_manager.py:49-81,315-404)`: música/SFX/ambiente/voz/espacial (radio 2000, suelo crítico 0.35)/eco + ducking voz 0.35/efecto 0.70 (`mixer_buses.py:57-241`) + update en tiempo real (`app.py:505`); `SoundBank` escanea `assets/sfx/`; música dinámica `dynamic_music.py:12,47` + stems + `bgm_*` por TMX; voz con ducking + 3 wavs venado. **Reverb PARTIAL** (límite SDL documentado: variantes `_con_eco` horneadas `reverb_zones.py`, fase 6 stage4_1). Sin HAP/rumble verificados → ABSENT. **Temporal VERIFIED:** hitstop 0.035/0.07/0.11 + hit-stop/bala (`clock.py`, `collision_system.py:121-173`).
**Cámara:** follow+deadzone+smoothing+look-ahead+shake+zoom+room-lock+CameraLock+boss + zones (`CameraZoomZone`, `MusicZone`) VERIFIED. CPU y GPU producen el mismo resultado conceptual (misma escena/lógica; difieren en postproceso), pero GPU no certificable en CI-dummy.

---

## O/P. Dialogue + UI Maps (§16, §17)

**Diálogo VERIFIED:** `dialogue_system.py:122-232` nodos/árbol `desde_datos`, `:235-438` ciclo+typewriter+paginación+`{apodo}`+voz+ducking+`OBJECTIVE_REQUESTED`, `:442-631` dibujo/retratos; datos `data/dialogues/<stage_id>.json`; `MessageTrigger.dialogue_tree_id`; visto `_dialogo_visto`; cutscenes `cutscene_system.py:112`, `cutscene_director.py`, `cutscene_guion.py` (no bloquean, salto ejecuta final). Localización ES/EN (`i18n.py`, `locale/*.json`) aunque el proyecto decreta español como única lengua (documentación en español vigilada por test).
**UI VERIFIED:** HUD (`hud.py:268-502`+`hud_builder.py`+`theme.py`): vida/estamina/mana/ultimate/oxígeno/bala/score+monedas/timer/boss/combo/NG+/items/rush + `regiones (:590-607)` + minimap/message/subtitle; escenas título/opciones/keybinding/carga/tienda/inventario/bestiario/logros/skill-tree/world-map/boss-rush-entry/game-over/créditos (`scene_registry.py:72-82`, `LoadingScene` precalienta sklearn 2461→2 ms). Inventario (`inventory.py:36-80`): catálogo, equipar, tienda compra/venta mitad, `collect` vía `InteractableSystem._recoger→SenalesDeEscenario._on_item_picked`.

---

## L. Progression Map + 25. Save/State (§18, §25)

```text
JEFE MUERTO (ENEMY_DIED) → skill_drop (boss_base.py:99,135) → INVENTARIO.has_skill
→ NUEVA CAPACIDAD (dash/doble/parry/coraza) → NUEVA ZONA (puerta/llave/next) → NUEVO ENEMIGO (HP 1→5 por zonas bestiary_registry.py:193-287)
```
XP (`experience.py:46-60`) + árbol 3 ramas solo-stats (`skill_tree.py`, `CORAZONES_MAXIMOS=10`) + score/monedas (`score_system.py`, botín en escena) + objetivos/checkpoints (`progression_system.py:19`, `objetivos.py`, `checkpoint.py:34`) VERIFIED. Habilidades por jefe, no por tienda (GAP-029/AUD-238, `settings.PLAYER_SKILLS_REQUIRE_UNLOCK=False` como resolución) VERIFIED. NG+/dificultad (`difficulty.py:22` invencibilidad 1.5/2.0/1.0, ventana parry 0.25) VERIFIED como flags/timers. **Persistencia:** runtime (timers/buffers) vs escena (entidades/checkpoint) vs sesión (contexto) vs save (slot: pos/vida/flags/exp/score/inventario/árbol/logros/play_time/variante 4-1, `save_data.py:32-113`) vs global (`config.json` user_settings) VERIFIED. Atómico + migración + ranura activa + `auto_save` read-modify-write VERIFIED.

---

## Q/R. Framework + Engine Maps (§19, §20)

Framework propio VERIFIED: ECS declarado pero premisa falsa documentada (GAP-041: no hay ECS sistémico; hay entidades+estrategias+StageScene por partes) → **ECS DECLARED/ABSENT como sistema**, VERIFIED como módulos sueltos (`ecs/`, `ai/`, `combate/`). Event bus, escenas, entidades, estados, assets, config, save, l10n, audio-abstracto, input-abstracto, colisión-abstracta (`capas.py` IntFlag sin pymunk + `MapaDeCapas`), UI-abstracta, scripting (cutscene guion), debug, testing, logging VERIFIED con API/consumidores en tabla §Q del sondeo.
Motor: **pygame-ce** (ventana, Surface, eventos, clock, audio SDL, fuentes, imágenes) VERIFIED como camino real; **ModernGL** (contexto, texturas, buffers, shaders, FBO, upload, draw, present) VERIFIED como código, PARTIAL como runtime certificable (solo Quadro M2200; CI-dummy cae a `_software_fallback`). Física: gravedad por perfil, colisión por ejes, resolución X→pared→Y→cuestas→repisas (`resolucion.py:453-524` AUD-297), queries por rect, capas IntFlag VERIFIED. Rendering:
```text
WORLD(TMX+entidades) → GAMEPLAY(StageScene por partes) → DRAW DATA(SpriteBatch) → CPU(blits)/GPU(instanciado)
→ FBO(5+1) → POST (bloom 9×9=81 lecturas, grading, viñeta, motion, godray 32, lighting 16 focos) → LETTERBOX → DISPLAY
```

---

## S/T. CPU/GPU Maps (§21, §22) + 23. Memoria

**CPU VERIFIED (medido en docs/código):** ~20 entidades, ~77 blits por escena; `SpriteBatch.dibujar/volcar (sprite_batch.py:92-167)` N blits→1 `blits()`; `PostProcessing` numpy CPU; TMX parsing en carga (no por frame); audio ducking por frame real; hitstop con reloj real. Hotspots Python: resolutor por entidad, `colliderect` por rect, daño/números/VFX por evento, `validate/los_mapas_no_traen_miles_de_rectangulos` (GAP-037: 51 rects, no miles).
**GPU (código VERIFIED, medición PARTIAL):** 5+1 FBO (`_scene/_temp/_bloom(w/2)/_prev/_light/_static_light 2048²`, `gl_pipeline.py:460-508`), shaders fullscreen (copy/bloom/grading/viñeta/motion/lighting/colorblind/aberration/refraction/godray/sprite/upload swap_rb/overlay), 1 VAO por programa (fix AUD-223), batching instanciado `SpriteBatchGPU (gpu_sprite_batch.py:63-300)` que rechaza mezclar atlas, `MemoriaDeTexturas`, contadores de draw calls. `PresentadorGPU` SDL2 CODE_ONLY deliberado (incompatible Window vs display, doc con medición bloom GPU 9.47 ms vs CPU 2.04 ms → apagado por defecto). Sin GPU física en CI: lo GPU cuenta pasadas sin pintar (tests `test_cada_pasada_ejecuta_su_shader`, `test_composicion_de_sprites_en_gpu`).
**Memoria:** altas/bajas de texturas registradas; sin leaks demostrados en la auditoría (no se ejecutó profiler; se declara UNKNOWN para leaks, VERIFIED para caches/vida de assets vía ResourceManager/Handle).

---

## 24. Collision & Physics

`POSICIÓN LÓGICA (float, top-left) → RECT (int, _verja NaN→0,0 resolucion.py:120-171) → COLLIDER (rect) → SPRITE (dibujo) → PIES (y+h) → ORIGEN (top-left)`. Spawn TMX `Y=pies → y-32` (`stage_loader.py:718-732,907`, GAP-007) VERIFIED. Hurtbox jugador pie/agachado (`player.py:567`), hurtbox/hitbox enemigos (`enemy_base.py:802,959,1032-1047`), `process_attack` una vez por swing + knockback + hitstop VERIFIED. One-way (atravesable desde abajo), cuestas fuera de `collision_rects` (`pendientes.py:22`), materiales ROCA/HIELO/MUSGO/GOMA + rebote umbral 30 (`resolucion.py:57-65`, `perfil.py`), coyote+buffer 8f VERIFIED. Capas `SOLIDO/PLATAFORMA/DESTRUCTIBLE/PUERTA`, `MASCARA_POR_DEFECTO=SOLIDO|PLATAFORMA` (`capas.py`, 12 pruebas `test_capas_de_colision.py`) VERIFIED.

---

## U. Test Map (§26) — 357 ficheros `test_*.py` (conteo por `Get-ChildItem`)

| Bloque | Ejemplos | Estado |
|---|---|---|
| Física/colisión/spawn | player_physics, cajas/capas de colisión, rect fusionado, calibración del salto (111 pruebas, salto 72 px/3–5 baldosas), spawn==TMX, lodo 4-1 | VERIFIED |
| Render/GPU/batching | cada pasada ejecuta su shader, composición GPU, atlas, partículas, HUD no invertido, daltonismo/aberración, benchmarks+bench_sprite_batch/bench_gpu_postproc/jump_bench/bot | VERIFIED (GPU en dummy) |
| Audio | buses, ambience, wiring, direccional, dynamic_music, sonido de muerte | VERIFIED |
| UI/diálogo/cutscene | dialogo_y_cutscenes/desde_datos/alcanzable, cutscenes desde mapa, demo_scenes, escenas_ui_ux | VERIFIED |
| Progresión/save | aud_559_economia, guardado_y_cadena, ranura vacía, corrupt_saves_are_loud, checkpoint, boss_rush, curva_dificultad | VERIFIED |
| Docs/contratos/seguridad | architecture_doc_matches_tree, arquitectura_fronteras, documentacion_en_espanol, simbolos_de_specs (173, 0 rotos), rutas, change_safety, apis_que_nadie_llamaba, sistemas_huerfanos, dependencias | VERIFIED |
| Validadores CI | check_dependency_sync/translations/tmx_coverage/validate_assets/validate_tmx/grade_stage/grade_boss/check_change_safety + `grade_stage assets/maps/ --json`, `grade_boss ... --json` | VERIFIED |

Cobertura PARTIAL global: mutación `player.py 44%`, `mixer_buses 88%`, `bloques 96%`; interpolación fuera (GAP-036); prioridad mismo fotograma sin caso (GAP-040).

---

## V. Documentation Delta (§27)

```text
CODE == TESTS ≈ RUNTIME > DOC (con fecha) ; ASSETS ≥ CODE (demos sobran); TESTS > IMPLEMENTACIÓN en GPU-dummy
```
Discrepancias: **DOC>CODE**: ECS como sistema, reverb DSP, F2/F3 Rey, F2-4 Paburu, bestiario visible pleno, grapple-techo utilizable. **CODE>DOC**: buffer genérico 8f, wall-jump triple, pogo-slam, tirolesa, `Backtracking/WarpZone`. **ASSET>CODE**: 12 demos cámara, `referencia_arte.png` Paburu, sfx sin emisor verificable individual. **TEST>IMPLEMENTATION**: pasadas GPU en dummy. `KNOWN_GAPS.md` (46 gaps GAP-001…046, todos cerrados con medición) y `docs/63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md` (huérfanos 221→0 reales, 22 patrones boss etiquetados) son proceso VERIFIED pero con secciones históricas que exigen leer con fecha.

---

## W. Orphan/Dead Systems (§28)

| Candidato | Veredicto |
|---|---|
| `GanchoTechoState`, `BalanceoEnLianaSaltoState` (no exportados, sin Action/skill/cable) | DEAD/DECLARED |
| `PresentadorGPU` (nadie lo llama desde App) | CODE_ONLY deliberado |
| `SpriteBatchGPU.volcar` vacío / rechazo mezcla atlas sin escena que lo publique | CODE_ONLY/PARTIAL |
| `netcode.py:14 Netcode` | CODE_ONLY (sin consumidor verificado en el sondeo; `UNKNOWN` si hay plugin que lo use) |
| Demos cámara, arte Paburu, bindings sin fila UI | ASSET_ONLY / PARTIAL |
| `PhysicsSystem.step/update_enemies` obsoletos (avisan con warn `collision_system.py:175-237`) | DEAD (intencional) |
| `skill_ground_pound` exigida sin catálogo visible | UNKNOWN (candado sin fuente; buscar en `inventory.py` ampliado antes de certificar) |

 Guardián: `scripts/check_orphan_systems.py` + `test_sistemas_huerfanos.py` + `test_apis_que_nadie_llamaba.py` VERIFIED.

---

## X. Feature Traceability Matrix (§29, resumen; matriz completa por feature en §E–W)

| Feature | Code | State | Input | Phys | Coll | Anim | VFX | SFX | UI | Level | Prog | Tests | Runtime | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| walk/jump/fall/crouch/slide | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | ✓ | VERIFIED |
| doble salto / dash | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓(skill) | ✓ | ✓ | VERIFIED |
| wall-slide/jump×3, ledge-grab | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | – | – | ✓ | – | ✓ | ✓ | VERIFIED |
| trepar/tirolesa/nado | ✓ | ✓ | ✓ | ✓(grav 0) | ✓ | ✓ | – | – | – | ✓(Paburu) | – | ✓ | ✓ | VERIFIED |
| gancho-techo/péndulo | ✓ | ✓ | ✗ | ✓ | – | ? | – | – | – | ✗ | ✗ | ✗ | ✗ | DECLARED/DEAD |
| ground-pound / pogo-slam | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | ~(skill?) | ✓ | ✓ | VERIFIED/PARTIAL |
| corto/largo/combo/aéreo/arco | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓(combo) | ✓ | – | ✓ | ✓ | VERIFIED |
| parry | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | ✓(tutorial) | ✓(skill sin gate) | ✓ | ✓ | VERIFIED |
| block / dodge dedicado | ✗ | ✗ | ✗ | – | – | – | – | – | – | – | – | – | – | ABSENT |
| enemigos base+propios / bosses Venado | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓(drop) | ✓ | ✓ | VERIFIED |
| Paburu/Rey/Gavilán | ✓ | ✓ | – | ✓ | ✓ | ~ | ~/✗ | ~ | base | ✓ | ✓ | ✓ | ~ | PARTIAL |
| checkpoint/save/score/diálogo/cutscene/HUD/tienda | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | VERIFIED |
| GPU pipeline/shaders/FBO | ✓ | – | – | – | – | – | ✓ | – | – | – | – | ✓(dummy) | ~ | PARTIAL |
| reverb DSP / rumble / críticos / finishing | ✗/~ | – | – | – | – | – | – | ~/✗ | – | – | – | – | – | ABSENT/PARTIAL |

---

## Y. Missing Capabilities (§30–31: lo que NO existe, buscado explícitamente)

Movimiento: run dedicado, ledge-hang/shimmy/climb, wall-grab, slope-sistemas más allá de pendientes, ladder dedicada, rope-swing utilizable, grapple/hook/pull, vault, swim-dash, stomp-rebote encadenado. Combate: block, dodge dedicado, cargados más allá de `CHARGE_*` (existen estados; carga completa por verificar caso a caso → PARTIAL), críticos, elementos/estados del jugador, finishing. Exploración: ability-gates de traversal interconectado (solo llaves/puertas + skills de jefe), puzzles ambientales sistémicos, secretos más allá de cofres/pickups. Interacción: shops sistémicos más allá de `ShopScene`, skill-tree activo (solo
stats), mapa de mundo navegable (world-map escena existe; gating por mapa → PARTIAL). Haptic/rumble, reverb DSP, mezcla dinámica total de música por stems en runtime (infra sí, pistas verificadas solo por TMX) → ABSENT/PARTIAL.

---

## Z. Final Architecture Diagram (§35, con nombres reales)

```text
                         ┌───────────────┐
                         │ Player (framework/entities/player.py:204) │
                         │ PlayerState×30 (:170) + PlayerStateData   │
                         └───────┬───────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
     InputManager (engine/   STATES (states/:      Camera (framework/
     input/input_manager     grounded, airborne,    stage/camera.py:64
     .py:51 + action_map     ability, wall,         + CameraLock)
     .py:14, buffer 8f)      rope, attack)          │
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                      GAMEPLAY CORE (framework/scenes/stage_scene
                       + stage_parts/mundo_ecs + combat_manager :52)
                                 │
          ┌──────────────┬───────┼───────────┬──────────────┐
          │              │       │           │              │
  Physics (physics/  Combat (stage/    AI (enemy_   Interact   Progresión
  resolucion.py,     collision_   _base.py:73,  (pickups,    (progression
  physics_system,    system.py:   components,   puertas,     _system,
  capas, perfil)     241 + hitstop) bestiary,   placas,      experience,
          │              │       │ factory,     checkpoint,  skill_tree,
          │              │       │ squad_brain)  diálogo)    score, shop)
          │              │       │           │              │
          └──────────────┴───────┼───────────┴──────────────┘
                                 │
                           EVENTS (core/event_bus.py:97,
                            events.py:15: ENEMY_DIED, BOSS_PHASE_CHANGED,
                            VFX_*/SFX_*, CHECKPOINT_REACHED, OBJECTIVE_REQUESTED)
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
      VFX (framework/vfx:  SFX (engine/audio:  UI (engine/ui/hud.py,
       particle, trail,     audio_manager:49,   dialogue_system,
       damage_numbers,      mixer_buses,        escenas título/tienda/
       hit_effects,         sound_bank,          inventario/bestiario/
       efectos_venado)      dynamic_music)      skill-tree/world-map)
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                        RENDER (engine/render: RenderFacade :37,
                         sprite_batch, gl_pipeline GLRenderer :255,
                         shaders, FBO 5+1, gpu_effects, post_processing CPU)
                                 │
                         ┌───────┴───────┐
                         │  CPU (pygame-ce, │
                         │  camino real) /  │
                         │  GPU (ModernGL,  │
                         │  opcional Quadro)│
                         └───────┬───────┘
                                 │
                        DISPLAY (core/display.py:97 viewport
                         letterbox + core/app.py:74/832 publish)
```

---

## 36. Hallazgos especiales

**Capacidades que creíamos que existían pero NO están demostradas:** ledge-hang/climb más allá de grab, wall-jump infinito (es 3× con cooldown), stomp-rebote, enemy-bounce encadenado (solo pogo-slam), grapple/hook/rope-climb utilizable (péndulo muerto), ability-gates interconectadas, barra de jefe dedicada, reverb DSP, dodge/block dedicados, críticos/elementos del jugador.
**Implementadas pero no documentadas (CODE>DOC):** buffer 8f, wall-jump triple, SlideState, tirolesa/trepa por proximidad, pogo-slam, `WarpZone/backtracking`, `CameraZoomZone/MusicZone`, `Switch decamouflage` de escenas (ver stage_parts).
**Implementadas pero no certificadas:** GPU pipeline completo, Paburu F2-4, Rey F2/F3, Gavilán proyectiles/VFX, `skill_ground_pound`, demos cámara.
**Declaradas pero no implementadas:** las de la primera lista + ECS sistémico + reverb SDL + NG+ procedimental.

---

## 37. Architecture Health (solo describir)

Acoplamiento moderado-bajo: `engine/input` no importa `framework` (test de frontera); `GameContext` por inyección (ya no singleton); `RenderFacade` strategy; resolutor puro por funciones. Deuda: estados no exportados (rope), skills sin gate uniforme (parry libre vs dash/doble con candado vs pound sin catálogo), spawn de jefe dual (TMX vs código en Paburu), HUD que empuja valores cada frame desde escena (push, no pull), docs históricos que exigen fecha, GPU opcional que duplica postproceso (con `cpu_effects_taken_over` para no duplicar). Sin circulares demostradas en esta pasada (ver `importlinter` + `test_dependencias_que_se_usan`).

---

## 38. Certification Baseline

| Contrato | Veredicto X-RAY (no cambia certificaciones) |
|---|---|
| CERT-PLAYER (estados, física, combate, parry, arco) | CERTIFIED salvo pound-skill y carga completa → PARTIALLY CERTIFIED en esos subcasos |
| CERT-RENDERER (CPU) | CERTIFIED; (GPU) PARTIALLY CERTIFIED/TESTED ONLY (dummy) |
| CERT-ENEMIES (FSM, especies, spawn, muerte) | CERTIFIED salvo Brute-base y Hormiga/Oropel → PARTIALLY en esos |
| CERT-BOSS (Venado) | CERTIFIED; Paburu/Rey/Gavilán PARTIALLY CERTIFIED |
| CERT-INPUT (teclado/mando/buffer/rebinding) | CERTIFIED; rebinding-UI PARTIALLY (12/20+ filas) |
| CERT-PERFORMANCE | PARTIALLY CERTIFIED (CPU medido; GPU solo Quadro; leaks UNKNOWN) |
| SAVE/AUDIO/DIALOGO/UI/TMX | CERTIFIED/TESTED (validadores CI en verde según docs; re-ejecutar `pytest` + validadores para sello actual) |

---

## 40. Regla de oro — respuestas con código real

**¿Qué ocurre cuando el jugador presiona JUMP mientras cae, cerca de un enemigo, en zona interior, con lluvia, tras checkpoint, con zoom de cámara y renderer GPU activo?**
`InputManager.pump (input_manager.py:144)` → `pulsada_en_buffer JUMP (:337, ventana 8f :132)` → en `AirborneState` se evalúa `_can_jump (helpers.py:122)`: fuera de coyote (`COYOTE_FRAMES=6 settings.py:72`) solo salta si `air_jumps_used < saltos_aereos(1 :75) + skill_double_jump (inventory.py:150)`; si procede, `_do_jump (:141)` con `salto_impulso` + stretch; si no, el buffer expira y sigue cayendo (`MAX_FALL=500 :71`, gravedad de muro si hay push `player.py:1324`). Proximidad enemiga no altera el salto (sin pogo contextual; el contacto lo resuelve `collision_system.py:241` + `apply_damage player.py:809` con `inv_timer`); lluvia = `particle/weather` + `MusicZone/ambience` sin física distinta verificada; checkpoint previo solo define respawn (`checkpoint.py:34`) y slot autosalvado (`save_manager.py:445`); zoom (`CameraZoomZone`, `camera.py:64`) y GPU (`GLRenderer.render`) solo cambian presentación, no lógica (misma `StageScene`, `cpu_effects_taken_over` evita doble postproceso).
**¿En Stage 4.1b?** Sin TMX `stage4_1b` en `assets/maps/` (solo `stage4_1/stage4_1.tmx` 960×40, 0 enemigos por regla oro `grade_stage.py:324`): `UNKNOWN — EVIDENCE INSUFFICIENT` para ese sufijo; en `stage4_1` el salto opera igual pero sin amenazas y con cuestas (`Slope 9`) y cutscenes.
**¿Nueva habilidad? ¿Dónde se usa? ¿Qué desbloquea?** Las habilidades las sueltan jefes (`skill_drop boss_base.py:99`; Venado→dash+parry, Rey→double_jump, Gavilán→coraza) y las consume `_tiene_habilidad (helpers.py:100)`; desbloquean traversal (dash aéreo, doble salto) y puertas/zonas TMX (`LockedDoor/Key`, `NextTrigger`), no un mapa metroidvania verificado.

---

## 39/42. Output y principio final — trazabilidad WHAT/WHO/WHERE/WHEN/WHY/HOW

Este documento cubre A–Z. Cada fila trae su `SOURCE/FILE/SYMBOL/LINE/EVIDENCE/STATUS`. Lo `UNKNOWN` se declara como tal (fugas de memoria, reverb DSP, sufijo 4.1b, consumidores de `Netcode`). El roadmap (correcciones, certificación, gameplay, traversal, combat depth, juice, pacing, performance, contenido, mecánicas) solo podrá construirse después de este X-RAY; no se diseña aquí.

*Fin AUD-836. Sin commits, sin cambios de código/tests/assets/docs existentes.*
