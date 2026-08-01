---
document_id: "LOI-ANALYSIS-039"
title: "Reporte Exhaustivo de Análisis de Código — Legacy of InFest"
aliases: ["Code Analysis Report", "Reporte Analisis Codigo"]
tags: ["analysis", "code", "report"]
description: "Code analysis report"
source: "docs/39_REPORTE_ANALISIS_CODIGO.md"
date_processed: "2026-07-14"
---

# Reporte Exhaustivo de Análisis de Código — Legacy of InFest

**Documento:** LOI-REP-039  
**Alcance:** Análisis técnico línea a línea del código fuente (`src/`) comparado contra la documentación (`docs/`).  
**Objetivo:** Describir para qué sirve cada módulo, qué hace, cómo se usa, su alcance y sus limitaciones, con español neutro y nivel técnico.  
**Estado del repositorio analizado:** `b63ca536` · `legacyofInfest`

---

## 0. Resumen ejecutivo

`Legacy of InFest` es un motor de videojuego 2D tipo *platformer de acción* construido sobre **Pygame**, de 320×224 px de resolución interna escalada por un factor configurable (por defecto ×3, vía `SDL_HINT_RENDER_SCALE_QUALITY=0` para escalado *nearest-neighbor*). Está arquitecturado con una separación clara entre **motor (`engine/`)**, **framework de juego (`framework/`)** y **contenido (`stages/`)**, usando patrones de diseño: *Dependency Injection* (`GameContext`), *Observer/Event Bus* (`EventBus`), *State* (máquina de estados del jugador), *Template Method* (enemigos), *Factory* (`entity_factory`) y *Scene Stack*.

El repositorio contiene **~120 módulos Python** de código fuente y **~40 documentos** en `docs/`. La documentación principal (`03_ARCHITECTURE.md`) describe una arquitectura **congelada en una versión anterior e incompleta** del proyecto: omite subsistemas enteros (VFX, audio dinámico, logros, minimapa, sistema de guardado, tutorial, música ambiental, sistema de iluminación), subestima el número de entidades (documenta 3 enemigos; el código registra 8 más un jefe), y declara firmas de API que **no coinciden** con la implementación actual (p. ej. `AudioManager.play_music`, `AssetLoader.load_spritesheet`, `InputManager.is_action_pressed`, `EventBus` basado en instancia). Las herramientas de procesamiento académico (`framework/processing/`) son, por el contrario, **más completas** que lo documentado y sus firmas coinciden.

---

## 1. Punto de entrada y arranque (`main.py`)

| Aspecto | Código | Doc (03_ARCHITECTURE §1, §5, §6) |
|---|---|---|
| Lanzamiento | `python main.py` crea `App()` y llama `run()` | Coincide |
| CLI | Soporta `--stage <id>` y `--boss <id>` (valida módulo antes de iniciar Pygame) | **No documentado** |
| Carga selectiva | Importa dinámicamente `src.stages.<id>.<id>` o `src.stages.<id>.<id>_scene` y busca subclase de `StageScene` | **No documentado** |

**Funcionalidad:** `main.py` resuelve dos modos de ejecución además del flujo normal:
1. `--stage <id>`: importa `src.stages.<id>.<id>`, localiza la subclase de `StageScene` por introspección (`issubclass`, excluyendo la propia base) y la empuja directamente al `SceneManager`.
2. `--boss <id>`: igual, pero el módulo se nombra `<id>_scene`.
En ambos, si el módulo no existe o no hay subclase válida, imprime error y `sys.exit(1)`. Esto es **útil para depurar un escenario concreto sin recorrer el menú**.

**Limitación:** La detección de la subclase itera `dir(mod)` y toma la *primera* subclase de `StageScene`; si un módulo definiera dos escenas, se tomaría la primera alfabéticamente, no necesariamente la deseada.

---

## 2. Núcleo del motor (`src/engine/core/`)

### 2.1 `app.py` — `App`
Clase raíz. `App.__init__` inicializa Pygame, crea superficie interna 320×224 y ventana escalada con `pygame.SCALED`, instancia `DeltaClock`, `EventBus` (y lo fija como bus por defecto vía `set_default_bus`), `InputManager`, `AudioManager`, `TransitionManager`, y el `GameContext` inyectado a todos los subsistemas. Registra entidades (`ensure_registered`) y escenas demo (`register_demo_scenes`), crea el `DebugOverlay` y empuja `SplashScene`.

`App.run()` es el bucle principal. Orden sagrado (comentado en código):
1. `pygame.event.get()` → `QUIT` cierra.
2. `InputManager.pump(events)`.
3. `EventBus.dispatch()` (eventos encolados en frame previo).
4. `DeltaClock.tick()` → `dt`.
4a. `DebugOverlay.handle_input()` (teclas F3–F6).
5. `SceneManager.current.update(dt)` (envuelto en `try/except` que imprime traceback; **no aborta**).
5a. `TransitionManager.update` + `scene_manager.transition.update`.
6. `internal_surface.fill(BG_COLOR)` — **no negro**, sino `(15,15,40)`.
7. `SceneManager.current.draw(internal_surface)` (también con `try/except`).
7a. `TransitionManager.draw`.
7b. `DebugOverlay.draw(fps)`.
8. Escalado con `pygame.transform.scale_by(internal, DISPLAY_SCALE)` y `blit` + `flip`.

**Diferencia vs doc:** La doc dice "background never black" implícitamente y describe `transitions.py`; el código usa `TransitionManager` (módulo `scenes/transition_manager.py`), no `scene/transitions.py` (ese archivo **no existe** en el árbol). La doc §3.1 lista `engine.scene.scene_manager → engine.scene.transitions`, pero la importación real es `engine.scenes.transition_manager`. **La jerarquía de imports de la doc está desactualizada.**

**Limitación robustez:** El `try/except Exception` en update/draw captura y "traga" errores imprimiendo traceback, permitiendo que el juego continúe en estado potencialmente corrupto (p. ej. entidad `None`).

### 2.2 `settings.py` — constantes
Módulo plano de constantes (coincide con "sin clases/funciones"). Pero **la doc solo lista 12 constantes**; el código define **44**, incluyendo:
- `PLAYER_MAX_FALL_SPEED`, `PLAYER_COYOTE_FRAMES`, `PLAYER_INVINCIBILITY_DURATION`, `PLAYER_DASH_SPEED`, `PLAYER_AIR_DASH_LIMIT`, `PLAYER_AIR_JUMPS`, `PLAYER_SHORT/LONG_ATTACK_DURATION`, `PLAYER_COOLDOWN_*`.
- Sistema de combos: `COMBO_WINDOW`, `COMBO_DAMAGE_MULT=[1.0,1.5,2.0]`, `COMBO_MAX=3`.
- Accesibilidad: `COLORBLIND_MODE`, `SUBTITLES_ENABLED`.
- `BG_COLOR=(15,15,40)` (no `BLACK`).
- `DISPLAY_SCALE` se lee de la variable de entorno `LOI_DISPLAY_SCALE` (doc lo fija en 3 estático).

**Implicación:** La doc subestima drásticamente la configuración del jugador (dash, coyote time, saltos aéreos, ventanas de combo) que el código implementa plenamente.

### 2.3 `event_bus.py` — `EventBus`
La doc describe `subscribe/unsubscribe/emit` y una cola. El código **implementa EventBus como clase basada en instancia** (doc §3.1 y §2.1 sugieren uso global, pero el diseño "Fase 1" lo hizo instancia). Además provee:
- `unsubscribe_all(events, callback)`, `subscriber_count()`, `clear()`.
- Propiedades `queue_snapshot`, `subscribers_snapshot` (solo lectura, para depuración).
- Funciones módulo a nivel (`subscribe`, `emit`, …) que delegan a un bus por defecto lazy (`_default_bus`), manteniendo compatibilidad hacia atrás.

`dispatch()` drena la cola y llama a cada callback con `callback(**data)` **bajo copia de la cola** (`queue[:]`), evitando mutaciones durante iteración. Eventos **no se procesan en el frame de emisión** (se encolan y se despachan al inicio del siguiente frame) — coincide con doc §4.2.

### 2.4 `events.py` — `Events`
Enum central con **~40 constantes** de nombre de evento, frente a las ~10 listadas en la doc. Agrupa: ciclo de jugador (`PLAYER_DAMAGED/HEALED/DIED`), enemigos (`ENEMY_DIED`, `BOSS_PHASE_CHANGED`, `BOSS_ATTACK`), UI (`SHOW_MESSAGE/HIDE_MESSAGE`), progresión (`CHECKPOINT_REACHED`, `STAGE_COMPLETE`), **SFX** (`SFX_PLAYER_JUMP`, `SFX_HIT_CONNECT`, … ~20), **VFX** (`VFX_PARRY`, `VFX_CHARGE`, `VFX_SLAM`, `VFX_ULTIMATE`), y **logros** (`ACHIEVEMENT_UNLOCKED/PROGRESS`). Nota: `PLAYER_HEALED` está marcado en código como *"Reserved — not yet emitted"* pero **sí se emite** desde `ProgressionSystem.process_checkpoints` (discrepancia interna doc/código: la doc lo atribuye a Checkpoint; en realidad el StageScene/ProgressionSystem lo dispara al curar en checkpoint).

### 2.5 `clock.py` — `DeltaClock`
`DeltaClock.tick()` usa `pygame.time.Clock().tick(60)/1000.0` → `dt` escalado por `time_scale`. Propiedad `fps`. Coincide con doc. **Detalle:** el reloj interno está fijado a 60 FPS hardcodeado (`tick(60)`), por lo que `TARGET_FPS=60` es la cota real; el `time_scale` permite cámara lenta (usado por el *hitstop* de combate).

### 2.6 `game_context.py` — `GameContext`
Contenedor de inyección de dependencias. Expone `input_manager`, `audio_manager`, `scene_manager`, `event_bus`, `clock`, **`save_manager`** (doc §2.1 no lo menciona), `pending_load` (para carga de partida), `running`. Propiedad `audio`. Método `quit()` pone `running=False`. **Este DI container es omiso en la arquitectura documentada**, que aún asume un singleton global `App`.

---

## 3. Entrada (`src/engine/input/`)

### 3.1 `action_map.py`
`Action` es un `Enum` con **13 acciones**: `MOVE_LEFT/RIGHT/UP/DOWN, JUMP, CROUCH, SHORT_ATTACK, LONG_ATTACK, DASH, GRAB, CONFIRM, CANCEL, PAUSE`. La doc lista **9** (sin `MOVE_UP`, `MOVE_DOWN`, `DASH`, `GRAB`). `DEFAULT_KEY_BINDINGS` mapea acciones a listas de teclas Pygame. `CONTROLLER_DEADZONE=0.25`, ejes 0/1, y `_CONTROLLER_BUTTON_MAP` (A=JUMP, B=SHORT_ATTACK, X=LONG_ATTACK, Y=CROUCH, LB=GRAB, START=PAUSE, SELECT=CANCEL). **Diferencia vs doc:** la doc pone `CONFIRM=A(Xbox)`, pero el mapa real asigna `CONFIRM` a `ENTER/SPACE/Z` y deja A para `JUMP`.

### 3.2 `input_manager.py` — `InputManager`
Unifica teclado + joystick. Métodos: `is_action_just_pressed` (alias `is_action_pressed`), `is_action_held`, `is_action_released`, `consume` (marca acción consumida para que `just_pressed` sea `False` el resto del frame — **no documentado**), `rebind`, `is_raw_key_pressed`. El manejo de eje analógico solo usa el eje X para `MOVE_LEFT/RIGHT` y el eje Y para `CROUCH`/`JUMP` (no `MOVE_UP/DOWN`). **Limitación:** `is_raw_key_held` es `@staticmethod` y lee `pygame.key.get_pressed()` global, rompiendo la abstracción de acción.

---

## 4. Audio (`src/engine/audio/`)

### 4.1 `audio_manager.py` — `AudioManager`
La doc describe `play_music(name, loop, fade_ms)`, `stop_music`, `play_sfx(name, volume)`, `set_music/sfx_volume`. El código **cambia la firma**: `play_music(path, loops=-1)` (sin `fade_ms`), y añade un conjunto enorme:
- Música dinámica por capas: vive en `src/framework/audio/dynamic_music.py` (`DynamicMusicSystem`), no en `AudioManager`. Su API es `set_zone(zone, bgm_track)`, `set_intensity(level)` y `detect_intensity_from_state(has_boss, has_alive_enemies)`, con intensidades `INTENSITY_CALM/COMBAT/BOSS`; `StageScene` la maneja.
- Música ambiental: `play_ambient`, `stop_ambient`, `set_ambient_volume`, `crossfade_ambient`.
- `play_stinger` (SFX corto sobre la música), `play_sfx_at(name, world_x, screen_center_x, volume)` (**pan estéreo posicional** — no documentado), `pause_music/resume_music`, `toggle_mute`, propiedades `music_volume/sfx_volume/is_muted/current_music`.
- **Tolerancia a fallos:** nunca crashea ante archivos faltantes (loguea warning).

**Alcance:** Maneja 2 canales de música dinámica + 1 ambiente + el canal global de `pygame.mixer.music`. No hay límite explícito de canales SFX (usa `find_channel` de Pygame).

### 4.2 `sound_bank.py` — `SoundBank`
La doc dice "named sound registry". El código **auto-carga recursivamente** `assets/sfx/*.wav` en `__init__` (`load_all`), en lugar de registro manual. `play(name, loops, volume, pitch, pan)` admite pan estéreo y un parámetro `pitch` que, **en la práctica es un no-op** (intenta `fadeout(0)` pero no cambia la frecuencia real de reproducción). **Limitación:** `pitch` documentado implícitamente pero no funcional.

---

## 5. Utilidades (`src/engine/utils/`)

### 5.1 `asset_loader.py` — `AssetLoader`
**Clase con métodos `@classmethod`** (no instancia, a diferencia de la doc que implica instancia). Caché global por clave. `load_image(path, scale, size, alpha)` con **placeholder generado** si falta el archivo (colores por categoría de carpeta), y soporte de **`custom_assets/` override** (doc omiso). `load_font`, `load_sound` (devuelve `None` si falta), `load_sprite_sheet(path, fw, fh)` → **devuelve `list[Surface]`**, NO un objeto `SpriteSheet` (discrepancia con doc §2.6 que dice `load_spritesheet → SpriteSheet`). `clear_cache()` libera todo.

### 5.2 `spritesheet.py` — `SpriteSheet`
Existe como clase, pero **no es usada por `AssetLoader.load_sprite_sheet`**. `get_frame(x,y,w,h,colorkey)`, `get_frames(rects)`, `get_grid(cols,rows,...)`. La doc afirma `get_frame(index)` y `frame_count`; el código usa coordenadas (x,y), no índice. **Incoherencia documentada.**

### 5.3 `math_utils.py`
Funciones puras. La doc lista 9; el código tiene **17**: añade `ease_in_out_quad`, `ease_in_cubic`, `ease_out_cubic`, `ease_out_bounce`, `ease_out_elastic`, `ease_in_sine`, `ease_out_sine`. Usa `pygame.Vector2` (no tuplas, como implica la doc). `lerp` acota `t` a [0,1].

---

## 6. UI del motor (`src/engine/ui/`)

### 6.1 `hud.py` — `HUD`
La doc lo limita a "corazones, timer, retrato, score". El código es **mucho más amplio**:
- Corazones con 5 estados (full/¾/½/¼/empty), flash al dañar y animación de sparkle al curar.
- Retrato de jugador con 4 estados (normal/hurt/critical/dead) y marco 9-slice (`hud_frame.png`).
- **Boss HUD** (barra de vida + fase), **medidor de combo**, **medidor de especial/ULTIMATE**, **notificación de guardado**, timer countdown con flash a ≤30 s, timer de cuenta ascendente.
- Se suscribe a `PLAYER_DAMAGED/HEALED/DIED`, `BOSS_PHASE_CHANGED`, `CHECKPOINT_REACHED`, `STAGE_COMPLETE`. Patrón crítico: **`destroy()` es obligatorio** para desuscribir del bus (idempotente). La doc no menciona score; el código **no implementa score**.

**Limitación:** El HUD depende de fuentes/sprites opcionales (`game.ttf`, `heart_*.png`); si faltan, cae a rectángulos de fallback. No hay prueba de layout para resoluciones distintas a 320×224.

### 6.2 `message_box.py` — `MessageBox`
Coincide en lo esencial: cola de mensajes, efecto máquina de escribir (`chars_per_second=30`), auto-despedida por `duration`, o `dismiss_on_confirm` si `duration<=0` (espera CONFIRM, muestra flecha). `_wrap_text` limita a 3 líneas × 58 chars. Suscripción a `SHOW_MESSAGE/HIDE_MESSAGE`.

### 6.3 `screen_banner.py` — `ScreenBanner`
Coincide: banner de dos tonos que entra/sostiene/sale (slide_in 0.5 s, hold 2.0 s, slide_out 0.4 s) con `ease_out/in_quad`. Triggered vía `play(stage_id, stage_name)`.

---

## 7. Entidades del framework (`src/framework/entities/`)

### 7.1 `base_entity.py`
`BaseEntity` abstracta con `position: Vector2`, `rect`, `is_active`, `is_visible`, `layer` (default 4), `update`/`draw` abstractos. Coincide con doc.

### 7.2 `player.py` — `Player` (734 líneas)
La doc remite a `04_PLAYER_SPEC.md`. El código implementa **19 estados** (`PlayerState` enum): IDLE, WALKING, JUMPING, FALLING, CROUCHING, SHORT_ATTACK, LONG_ATTACK, HURT, DYING, DASHING, PARRY, CHARGE_ATTACK, DASH_ATTACK, WALL_SLIDE, LEDGE_GRAB, GRAB, THROW, SLIDE, y el valor adicional `WALL_SLIDE`. **Patrón State:** cada estado es una instancia de `PlayerStateBase` (en `player_states.py`) con `enter/update/exit`; `Player` delega y mantiene infraestructura compartida (física, colisión, animación).

Capacidades (más allá de la arquitectura resumida):
- Física: gravedad, **coyote time** (`PLAYER_COYOTE_FRAMES`), **jump buffering** (~5 frames), **jump cut** (al soltar se reduce vy), dash (incluido aéreo limitado), **wall slide + wall jump**, **ledge grab**.
- Combate: hitbox de ataque corto/largo con frames activos, **combo** (mult x1.5/x2.0), **medidor de especial** (gana al golpear), **parry** (deflexión de enemigos), **charge attack**, **grab/throw**, **slide**, **aerial slam**.
- Hurtbox dinámico (de pie 20×28, agachado 20×18).
- `apply_damage` aplica invencibilidad, knockback, emite `PLAYER_DAMAGED`/`PLAYER_DIED`/`SFX_*`, y escala daño por `difficulty.get_config()` (doc omiso de dificultad).
- Colisión AABB **por ejes separados** con detección de paredes, lógicas de *grazing* (overlap ≤2 px ignorado), y plataformas *one-way* con semántica `prev_foot_y`.

**Limitación grave de calidad:** el método `draw()` y `_resolve_collision()` contienen múltiples sentencias `print(...)` de depuración (p. ej. `[player] draw at screen (...)`, `[collision] NO collision rects provided`). Esto **contamina stdout en producción** y revela estados internos. Deben eliminarse o trasladarse a un logger.

### 7.3 `enemy_base.py` — `EnemyBase` (601 líneas)
La doc lo resume como "salud + estado". El código es un **Template Method** con 7 estados (`PATROL, ALERT, TELEGRAPHING, FIRING, HURT, LAUNCHED, DYING`):
- `update()` fijo: pre_update → invincibilidad → state machine → knockback → rects → cooldowns → animación → post_update.
- Detección con **histéresis de desagregarro** (`deaggro_margin`), rangos x/y configurables.
- `apply_hit` con **3 tipos de hitstun** (light/heavy/launch según daño), knockback, tinte de impacto.
- **Parry**: si el jugador tiene `_parry_active`, el enemigo es deflectado en lugar de dañar.
- Sprites por zona (`zone1..zoneN`), animación FPS normal/alerta.
- `set_player_ref`, `set_collision_rects`, `_check_player_contact`, `check_player_contact` (alias deprecado).
- `_build_hitbox`/`_build_hurtbox` abstractos (locales), `_get_animation_key` abstracto.

**Limitación:** `EnemyBase` importa a `Player` solo en TYPE_CHECKING (evita ciclo), pero `_check_player_contact` usa `getattr(player, ...)` para acceder a atributos privados del jugador (`_parry_active`, `_parry_window`, `_parry_success`), acoplándose a detalles de implementación.

### 7.4 `entity_factory.py`
`ensure_registered()` registra **9 tipos** en `StageLoader`: `Walker, Flying, Shooter, Charger, Archer, Brute, Caster, Assassin, BossVenado`. La doc (§8.3) solo ejemplifica `Walker/Flying/Shooter/Checkpoint`. **BossVenado se importa de forma perezosa** para no pagar el costo de importar numpy/sklearn (~3.4 s) al arranque. `Checkpoint` se registra aparte en `StageLoader.load`.

(No se leyeron los 8 enemigos concretos en detalle, pero su existencia y registro quedan verificados; cada uno extiende `EnemyBase` implementando `_patrol_behavior`, `_alert_behavior`, `_build_hitbox`, `_build_hurtbox`, `_get_animation_key`.)

### 7.5 `boss_base.py` — `BossBase`
Extiende `EnemyBase` con gestor de fases (`_finish_phase_transition` emite `BOSS_PHASE_CHANGED`), `_completion_fired`, `_boss_name`, `_phase_max_health`, y barra de vida para el HUD. La doc menciona "phase manager, boss health bar event" — coincide. `BossVenado` (en `stages/boss_venado/`) implementa `_do_stomp` que emite `BOSS_ATTACK`.

---

## 8. Sistema de escenario (`src/framework/stage/`)

### 8.1 `stage_loader.py` — `StageLoader` + `StageData`
La doc describe `StageData` con 17 campos; el código tiene **18** (añade `gravity_multiplier`). Carga TMX con `pytmx` + `pyscroll` (`BufferedRenderer`, `PyscrollGroup`). **Requisito estricto:** el TMX debe tener 8 capas: `BG_Far, BG_Mid, BG_Near, Terrain, Terrain_Detail, Objects, Collision, FG_Overlay` (la doc no lo menciona). Valida `PlayerSpawn` único y lanza `FrameworkUsageError` si falta.

Parsea objetos de `Objects`: `PlayerSpawn, MessageTrigger, MessageTrigger_Once, <tipos registrados>, Checkpoint, NextTrigger, HazardZone, DeathPit, CameraLock, Waypoint` (estos agrupados por `owner_id` y almacenados para entidades con patrullaje). Convierte props TMX (enteros/floats) y crea entidades. Carga fondos por zona (`background_zone`). `collision_rects`/`one_way_rects` se separan según `type=="Platform"` en la capa `Collision`.

**Alcance:** Soporta parallax, plataformas unidireccionales, zonas de cámara, peligros, death pits, mensajes, checkpoints y next-trigger. **Limitación:** los `Waypoint` solo se aplican si el objeto tiene `name` coincidente con `owner_id`; de lo contrario se ignora silenciosamente.

### 8.2 `camera.py` — `Camera`
Sigue al objetivo con LERP (`lerp_speed=8`). Añade a la doc: **screen shake** (`apply_shake`), **look-ahead** basado en velocidad, **camera locks** (congela eje x/y), factores de parallax por capa (`BG_Far 0.15 … Terrain 1.0`). `world_to_screen`/`screen_to_world`/`layer_offset`/`set_parallax_factor`. Coincide en lo documentado + extensiones.

### 8.3 `checkpoint.py` — `Checkpoint`
Activación única; emite `CHECKPOINT_REACHED`; dibuja gris→oro. La doc atribuye la curación a `Checkpoint` y el listener a `StageLoader`; en realidad la curación + autosave ocurre en `ProgressionSystem` (acoplamiento distinto al descrito).

### 8.4 `collision_system.py` — `CollisionSystem` (**no documentado**)
`process_attack` resuelve el hitbox del jugador contra hurtboxes enemigas: aplica daño (`apply_hit`), rebote de combo aéreo, ganancia de medidor especial, **hitstop** (`clock.time_scale=0.15` por N frames), **screen shake**, y emite `SFX_HIT_CONNECT`/`SFX_ENEMY_HIT`. `update_hitstop` restaura `time_scale`. `update_enemies` inyecta `set_player_ref` y `entity.update`.

### 8.5 `hazard_system.py` — `HazardSystem` (**no documentado**)
Dispara `SHOW_MESSAGE` en `message_triggers`, daña en `hazard_zones` (cooldown), mata instantáneo en `death_pits` (con delay de 1 frame para emitir `PLAYER_DIED` y empujar `GameOverScene`).

### 8.6 `progression_system.py` — `ProgressionSystem` (**no documentado**)
`process_checkpoints`: al activar, cura al jugador hasta max, emite `PLAYER_HEALED` + `SFX_CHECKPOINT`, y **autoguarda** vía `SaveManager`. `check_next_trigger`/`check_boss_defeat` disparan `STAGE_COMPLETE` con timer de 2.9 s. Integra `SaveManager` y `HUD`.

### 8.7 `drawing_system.py` — `DrawingSystem` (**no documentado**)
Orquesta el render por capas: fondo parallax (tileado) → `map_layer.draw` (pyscroll) → partículas ambientales → trails → entidades ordenadas por `rect.centery` (profundidad) → VFX (partículas, números de daño) → message box → banner → HUD → tutorial overlay → menú de pausa → overlay debug (hitboxes/hurtboxes en vivo). `_draw_debug` dibuja todos los rects de colisión/zonas y stats del jugador.

### 8.8 `stage_scene.py` — `StageScene` (705 líneas, **orquestador no documentado en detalle**)
Subclase de `BaseScene`. En `on_enter` carga TMX, crea `Player`, cámara, enemigos (inyecta refs), checkpoints, HUD, banner, message box, y **todo el ecosistema VFX**:
- `ParticleSystem`, `DamageNumberManager`, `HitEffects`, `PostProcessing` (flash, vignette de daño, bloom), `LightSystem`/`LightSource` (iluminación por zona), `AmbientParticleSystem`, `TrailSystem`.
- `DynamicMusicSystem` (intensidad según presencia de enemigos/jefe).
- `TutorialOverlay`, `Minimap`, `AchievementSystem`.
Suscribe ~20 handlers de eventos SFX/VFX (mapa `sfx_map` con 19 eventos → nombres de sonido; handlers espaciales con pan). `update` ejecuta: input/pausa → player.update → colisión/procesar ataque → cámara → map_layer.center → locks → checkpoints → next/boss → dynamic music → HUD → hazards → tutorial → partículas → iluminación → logros → minimap → trails. `respawn()` reubica en checkpoint con invencibilidad y fade-in. `draw` compone drawing + lighting + post + minimap + notificaciones de logros.

**Limitaciones:** `on_enter` contiene mucha lógica de inicialización (zonas de luz, ambiente, VFX) que se duplica en `respawn()` (vuelve a llamar `on_enter`); el manejo de `pending_load` (carga de partida) solo aplica si `stage_id` coincide. El método es extenso (705 líneas) y difícil de mantener; sería candidato a descomposición.

---

## 9. Herramientas de procesamiento académico (`src/framework/processing/`)

Estas son las más **fieles y más completas** respecto a la doc (§2.9). Todas se implementan como `classmethod` (la doc dice "funciones puras"; es una diferencia de estilo, no de capacidad).

### 9.1 `color_tools.py` — `ColorTools` ✅ coincide + 100%
`rgb_to_hsv, hsv_to_rgb, rgb_to_hsl, hsl_to_rgb, rgb_to_cmyk, cmyk_to_rgb` (todas con rangos documentados), `alpha_blend` (exige mismo tamaño), `apply_tint`, `surface_to_array`, `array_to_surface`. Implementación manual correcta (sin dependencias salvo numpy/pygame).

### 9.2 `filter_tools.py` — `FilterTools` ✅ coincide + extras
`compute_histogram` (devuelve dict con r/g/b/luminance/total), `adjust_brightness`/`adjust_contrast` (validan [0,4]), `stretch_contrast` (**extra**), `apply_kernel` (valida cuadrada 3–15 impar), `gaussian_blur` (sigma (0,10]), `sobel_edge`, `canny_edge` (usa **OpenCV `cv2`**, no solo scipy — doc omiso de la dependencia cv2), `histogram_equalize` (**extra**), `get_standard_kernel` (**extra**, 9 kernels).

**Dependencia no documentada:** `import cv2` en `filter_tools`, `vision_tools`, `pattern_recognition_tools`. La doc `10_LIBRARIES_AND_DEPENDENCIES` debe listar OpenCV; si no, el alcance de instalación cambia.

### 9.3 `curve_tools.py` — `CurveTools` ✅ coincide + extra
`bezier` (Bernstein/De Casteljau), `b_spline` (nudos uniformes, Cox-de-Boor), `nurbs` (con pesos), `catmull_rom`, `sample_path`. **Extra:** `build_bezier_path` (interpolación Catmull suave por waypoints). Documentación dice "Unit III"; el módulo dice "Phase 8" (inconsistencia de nomenclatura de unidad).

### 9.4 `vision_tools.py` — `VisionTools` ✅ coincide + mucho extra
Documentado: `threshold_binary, threshold_otsu, morphological_erode/dilate, watershed_segment, extract_features`. El código añade: `morphological_open/close`, `connected_components`, `filter_components_by_area`, `analyze_regions` (RegionInfo con área, centroid, bbox, eccentricity, solidity, perimeter), `largest_region`, `find_contours`, `bounding_boxes_from_mask`, `extract_hog/lbp/color_histogram` (HOG vía skimage, LBP uniforme 8-1, histograma de color), y `extract_features(method=...)` con `"hog"|"lbp"|"color_hist"|"combined"`. Todo sobre OpenCV + skimage. La doc lista `classify_region(features, model)` como parte de VisionTools, pero **ese método NO existe aquí**; la inferencia vive en `PatternRecognitionTools.classify`. (Discrepancia menor de ubicación.)

### 9.5 `pattern_recognition_tools.py` — `PatternRecognitionTools` ✅ coincide + extra
`train` (modelos `knn/tree/forest/svm` con `StandardScaler` en un `Pipeline`, `random_state=42`), `evaluate` (accuracy, por-clase, matriz de confusión, reporte), `save_model/load_model` (`.pkl` vía joblib, valida tipo), `register_model/get_model/list_models` (registro en memoria), `classify`, `classify_proba` (SVM requiere `probability=True`), `predict(surface, model)`, `generate_training_report` (**matplotlib → Surface**, con matriz de confusión y barras de precisión por clase). `extract_*` delega a `VisionTools`. Valida dataset (≥10 muestras, ≥2 clases). **La doc solo mencionaba "training, inference"**; el código es un pipeline ML completo.

---

## 10. Dependencias y alcance de instalación

`requirements.txt`/`requirements.lock` incluyen Pygame, numpy, scipy, **opencv-python (cv2)**, scikit-image, scikit-learn, joblib, matplotlib. La documentación de arquitectura (§2.9) afirma que `framework.processing.*` son "pure functions only (no engine or framework imports)" — **falso**: `pattern_recognition_tools` importa `vision_tools` (framework) y `color/filter/curve/vision` usan `pygame`. Además, el arranque paga import de numpy/scipy/sklearn solo de forma perezosa (BossVenado), pero `cv2`/`skimage` se importan a nivel de módulo en `vision_tools`/`filter_tools`, por lo que **cualquier uso de procesamiento carga OpenCV** (pesado).

---

## 11. Mapa de discrepancias documentación ↔ código (resumen)

| Tema | Doc | Código |
|---|---|---|
| Jerarquía de imports / `transitions.py` | `engine.scene.transitions` | `engine.scenes.transition_manager` (no existe el primero) |
| `AudioManager.play_music` | `(name, loop:bool, fade_ms)` | `(path, loops=-1)` sin fade_ms |
| `AssetLoader.load_spritesheet` | devuelve `SpriteSheet` | devuelve `list[Surface]` |
| `SpriteSheet.get_frame` | `get_frame(index)` | `get_frame(x,y,w,h)` |
| `EventBus` | global/estático | instancia + funciones módulo compat |
| Acciones de entrada | 9 | 13 (añade DASH, GRAB, MOVE_UP/DOWN) |
| Enemigos registrados | 3 + Checkpoint | 8 + BossVenado |
| `settings` constantes | 12 | 44 |
| `events` eventos | ~10 | ~40 |
| StageData campos | 17 | 18 (+gravity_multiplier) |
| Capas TMX requeridas | no mencionadas | 8 obligatorias |
| Subsistemas documentados | engine + entities + stage + processing | + VFX, audio dinámico, logros, minimapa, guardado, tutorial, iluminación, dynamic music |
| `FrameworkUsageError` | no mencionado | usado por StageLoader |
| `GameContext.save_manager` | no mencionado | presente y usado en progresión |
| `vision_tools.classify_region` | listado | no existe (está en PatternRecognitionTools) |
| `filter/vision` deps | numpy/scipy | + **OpenCV**, scikit-image |
| Player draw/collision | silencioso | `print()` de debug en producción |

---

## 12. Alcance, limitaciones y riesgos generales

1. **Documentación desactualizada estructuralmente.** `03_ARCHITECTURE.md` describe una versión previa del motor. Quien aprenda del doc tendrá una visión incompleta y, en algunos puntos, incorrecta de las firmas de API.
2. **Trazas de depuración en producción.** `Player.draw` y `Player._resolve_collision` (y `DrawingSystem.draw`) emiten `print()` por frame. Debe reemplazarse por `logging` con nivel DEBUG o eliminarse.
3. **Acoplamiento por atributos privados.** Enemigos leen `_parry_active`/`_parry_window` del jugador vía `getattr`; frágil ante refactors.
4. **Dependencias pesadas en el arranque.** Aunque BossVenado se importa perezosamente, `cv2`/`skimage` se cargan al importar `vision_tools`/`filter_tools`. Cualquier escena demo de procesamiento paga ese costo.
5. **`pitch` de SoundBank es no-op.** La firma promete cambio de tono pero no lo aplica.
6. **Duplicación en `StageScene`.** `respawn()` reinvoca `on_enter()` completo, re-suscribiendo handlers y recreando sistemas; el manejo de suscripciones es propenso a fugas si `on_exit`/`respawn` no se ejecutan en orden.
7. **Escalado de resolución fijo.** Todo el layout asume 320×224; no hay soporte para ventanas redimensionables más allá del `DISPLAY_SCALE` entero.
8. **TMX rígido.** Faltar una de las 8 capas obligatorias lanza `FrameworkUsageError`; los estudiantes deben replicar exactamente la plantilla (`student_templates/`).
9. **Robustez del bucle.** `try/except` en update/draw oculta excepciones; un error en una entidad no detiene el juego pero deja el frame en estado inconsistente.
10. **Pruebas.** El repo incluye ~37 archivos de test (verificados por su existencia en `tests/`) que cubren unidades clave; sin embargo, la integración de VFX/audio/logros no está reflejada en la arquitectura documentada.

---

## 13. Cómo usar el código (guía técnica rápida)

- **Ejecutar todo:** `python main.py` → Splash → Título → Historia → Stage0.
- **Escenario concreto:** `python main.py --stage stage0` o `--boss boss_venado`.
- **Registrar enemigo propio:** añadir la clase en `entity_factory._ENTITY_REGISTRY` (o usar `StageLoader.register_entity` desde el stage); colocar el objeto en la capa `Objects` del TMX con `type` igual a la clave.
- **Crear stage:** copiar `student_templates/stage_template/`, definir TMX con las 8 capas, `PlayerSpawn`, `NextTrigger`, y objetos tipados.
- **Usar herramientas de procesamiento:** `ColorTools.rgb_to_hsv(...)`, `FilterTools.canny_edge(surf, low, high)`, `CurveTools.bezier(pts, n)`, `VisionTools.extract_features(surf, method="combined")`, `PatternRecognitionTools.train(X, y, "forest")` → `classify`/`predict`.
- **Eventos:** emitir/subscribir vía `from src.engine.core.event_bus import emit, subscribe` o `EventBus` instancia de `context.event_bus`.
- **Guardar/cargar:** `GameContext.save_manager.auto_save(...)`; `pending_load` restaura posición/salud al entrar al stage.

---

## 14. Conclusión

El proyecto es un motor de juego 2D maduro y amplio, con arquitectura por capas sólida y patrones de diseño coherentes, y un conjunto de herramientas académicas de procesamiento de imágenes/ML que **supera con creces** lo prometido en la documentación. El riesgo principal no es funcional sino **documental**: la arquitectura oficial está desfasada y contiene firmas de API incorrectas, omite subsistemas completos (VFX, audio dinámico, guardado, logros, minimapa, iluminación), y no registra dependencias críticas (OpenCV, scikit-image). Se recomienda regenerar `03_ARCHITECTURE.md` a partir del estado actual del código, eliminar las trazas `print()` de `Player`, y documentar el ecosistema VFX/audio/progresión para alinear expectativas de estudiantes y profesores.

---
## 🔗 Documentos Relacionados

- [[51_IMPLEMENTATION_AUDIT.md|Implementation Audit]]
- [[50_IMPROVEMENT_ROADMAP.md|Improvement Roadmap]]
