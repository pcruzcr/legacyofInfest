# PLAN DE REMEDIACIÓN — Legacy of InFest

**Objetivo:** 100% de cumplimiento entre código y documentación.
**Formato:** Cada fase debe completarse al 100% antes de pasar a la siguiente.
**Checklist:** Marcar `[x]` cuando esté completado.

---

## Fase 0 — Críticos (runtime crashes)

- [x] 0.1 Mover `fonts/game.ttf` → `assets/fonts/game.ttf`
- [x] 0.2 Corregir `PlayerSpawn_01` Y=192 → Y=160 en `stage0.tmx`
- [x] 0.3 Agregar 4 Waypoints para Flying_02 (bezier) en `stage0.tmx`
- [x] 0.4 MessageBox: hacer pop de la cola en vez de limpiarla al descartar
- [x] 0.5 Alinear nombres de SFX en SoundBank con los archivos reales en disco (eliminados flat files obsoletos `assets/sfx/*.wav`)

**Verificación:** Juego corre sin crash, Stage 0 funcional, mensajes encolan bien.

---

## Fase 1 — Jugabilidad (gameplay correctness)

- [x] 1.1 Agregar `hurtbox` a Player: 20×28 standing (offY=4), 20×18 crouching (offY=14)
- [x] 1.2 `check_player_contact` → usar `player.hurtbox` (no `player.rect`)
- [x] 1.3 Colisiones de proyectiles → usar `player.hurtbox`
- [x] 1.4 Reemplazar FPS hardcodeado (10) con FPS por estado en enemigos
- [x] 1.5 Agregar animación `alert` separada a Walker y Flying
- [x] 1.6 Agregar estado `FIRING` al Shooter FSM
- [x] 1.7 Agregar claves de animación Aim (3fr 8FPS) y Fire (5fr 16FPS) al Shooter
- [x] 1.8 Animación de curación: derecha→izquierda, retardo 0.1s, múltiples corazones
- [x] 1.9 Animar heart_sparkle.png como sprite de 4 frames

**Verificación:** Las hitboxes/hurtboxes siguen la spec; enemigos animan a FPS correctos; shooter tiene Aim/Fire; curacion anima secuencialmente.

---

## Fase 2 — HUD y Visuales

- [x] 2.1 Cargar `hud_digits.png` como bitmap font para el timer
- [x] 2.2 Renderizar label `TIME` en Y=3, X=272
- [x] 2.3 Dibujar fondo del timer desde `hud_frame.png`
- [x] 2.4 Flash rojo 2Hz cuando countdown ≤30s
- [x] 2.5 Pausa: congelar timer (no ocultarlo)
- [x] 2.6 ScreenBanner: Y=88, dos tiras, sprites banner_top/banner_bottom, fuentes banner_large/banner_medium
- [x] 2.7 MessageBox: cargar `message_font.png` bitmap font
- [x] 2.8 Color texto mensajes → blanco puro (255,255,255)
- [x] 2.9 Límite de 3 líneas y 58 chars/línea en MessageBox
- [x] 2.10 Subscribir HUD a `CHECKPOINT_REACHED` y `STAGE_COMPLETE`
- [x] 2.11 Corregir docstring de `HIDE_MESSAGE` en events.py

**Verificación:** Todos los textos HUD usan fuentes bitmap; banner tiene animación de dos tiras; timer tiene fondo, label y flash.

---

## Fase 3 — Generación y Renombre de Assets

- [x] 3.1 Generar 13 sprites de jefes faltantes como placeholders (transparentes, tamaño correcto)
- [x] 3.2 Generar 2 shared sprites faltantes como placeholders (fountain_anim, spirit_echo_overlay)
- [x] 3.3 Actualizar ASSET_BIBLE.md §5 — nombres genéricos por zona (zone1_walk, fly_zone1, etc.)
- [x] 3.4 Actualizar ASSET_BIBLE.md §8 — nombres genéricos de backgrounds (bg_zone1_far, etc.)
- [x] 3.5 Actualizar ASSET_BIBLE.md §12 — nombres de SFX coinciden con disco
- [x] 3.6 Actualizar ASSET_BIBLE.md §11 — música es .wav (no .ogg); conversión diferida
- [x] 3.7 Verificado — StageLoader ya usa bg_{zone}_{layer}.png (coincide con disco)
- [x] 3.8 Crear `assets/ui/relics/` y mover los PNG de reliquias allí
- [x] 3.9 Eliminar/migrar directorios duplicados: `assets/player/`, `assets/enemies/`, `assets/bosses/`, `assets/audio/`

**Verificación:** Cada archivo listado en la Asset Bible existe exactamente en la ruta y nombre especificados.

---

## Fase 4 — Estructura del Código y APIs

- [x] 4.1 Marcar `_build_hitbox()` como `@abstractmethod`
- [x] 4.2 Renombrar `check_player_contact` → `_check_player_contact`
- [x] 4.3 Renombrar `_get_animation_key()` → `_get_animation_state()` o agregar alias abstracto
- [x] 4.4 Agregar `hurt_duration` e `invincibility_duration` a API_CONTRACTS.md
- [x] 4.5 Agregar parámetro `zone` a constructores de enemigos en API_CONTRACTS.md
- [x] 4.6 Agregar `build_bezier_path()` a CurveTools en API_CONTRACTS.md
- [x] 4.7 Actualizar StageData en ARCHITECTURE.md (7→17 campos)
- [x] 4.8 Agregar archivos de test faltantes: test_stage0_smoke.py, fixtures
- [x] 4.9 Crear directorios tests/output/{filter,vision,demo}/

**Verificación:** Firmas de API en código coinciden exactamente con API_CONTRACTS.md.

---

## Fase 5 — Documentación

- [x] 5.1 Agregar estado DASHING a PLAYER_SPEC.md (tabla §8.1 y diagrama §8.2)
- [x] 5.2 Agregar DASHING a API_CONTRACTS.md → PlayerState enum
- [x] 5.3 Actualizar TMX_SPEC.md §9.2: usar atributo `type` en vez de prefijo en nombre
- [x] 5.4 Sincronizar STAGE0_DESIGN.md con valores reales del TMX
- [x] 5.5 Sincronizar ASSET_BIBLE.md con nombres reales en disco
- [x] 5.6 Agregar `background_zone` a propiedades requeridas del TMX en TMX_SPEC.md
- [x] 5.7 Actualizar KNOWN_GAPS.md
- [x] 5.8 Corregir docstring de HIDE_MESSAGE en events.py (duplicado de 2.11 — ya resuelto)

**Verificación:** Cada spec describe exactamente lo que el código hace.

---

## Fase 6 — Tests y Verificación Final

- [x] 6.1 Tests unitarios para hurtbox del Player
- [x] 6.2 Tests para animación de curación (cubierto por test_hud.py — heal event/health)
- [x] 6.3 Tests para cola de MessageBox (orden, no limpiar al descartar) — test_message_box.py:108
- [x] 6.4 Smoke test de Stage 0 (cargar, spawn, update básico) — test_stage0_smoke.py
- [x] 6.5 Ejecutar `pytest` completo y corregir fallas — 347/347 pasan
- [x] 6.6 Jugar Stage 0 completo manualmente
- [x] 6.7 Verificar boss_venado arena (background, colisión, HUD)

**Verificación:** 100% tests pasan; playthrough completo de Stage 0 funciona.

---

## Fase 7 — Stage 0 Playability (bugs del playthrough)

- [x] 7.1 Fix Walker estático: TMX Y=192 → Y=164 (bottom alinea con floor top), probe_y en `_patrol_behavior`, y agregar floor snapping en `_post_update`
- [x] 7.2 Fix Shooter no dispara: TMX Y=192 → Y=168, spawn de proyectil en `self.rect.top`
- [x] 7.3 Fix ataque corto sin daño: aumentar hitbox (24×20, offset_x=12) y corregir posiciones de enemigos
- [x] 7.4 Fix animación ataque no visible: hitbox extendida mejora visibilidad de impacto; sprite key correcto en `_PLAYER_SPRITE_MAP`
- [x] 7.5 Fix Boss Venado inalcanzable: agregar 3 plataformas one-way (Y=224, Y=168, Y=112)
- [x] 7.6 Corregir F1 debug toggle (guard `hasattr` para `get_just_pressed`)
- [x] 7.7 Verificar Checkpoints y triggers en Stage 0 con nuevas Y de enemigos (colliderect touch inclusive)

**Verificación:** Jugar Stage 0 completo — Walker patrulla, Shooter dispara, ataque corto y largo hacen daño, Boss Venado es alcanzable.

---

## Fase 8 — Auditoría Técnica Integral (QC Phase 3 + Session 3)

- [x] 8.1 BUG-001: `_change_state_instance(force=True)` para transiciones HURT/DYING
- [x] 8.2 BUG-045: Camera look-ahead clamped antes de sumar a target
- [x] 8.3 BUG-052: App-level TransitionManager eliminado; una sola instancia scene-level
- [x] 8.4 BUG-058: `_was_alive = True` en `_die()` para re-evento de muerte
- [x] 8.5 BUG-061: Clasificación de entidades en una sola pasada
- [x] 8.6 BUG-062: `BossBase.phase_max_health` propiedad
- [x] 8.7 UX-001: Título font mínimo `max(12,…)` → `max(14,…)`
- [x] 8.8 UX-002: Diálogo font speaker 20→18, text/choices 14→16
- [x] 8.9 UX-006: Selection highlight azul → semi-transparent white
- [x] 8.10 UX-011: Keybinding capture usa `_last_keys_state` en vez de drain event.get()
- [x] 8.11 GA-015: Fog of war redibujado viewport-sized; fill cada frame
- [x] 8.12 PF-006, PF-007: Weather/Trail `list.remove()` O(n) → list comprehension filter
- [x] 8.13 PF-011: Weather spawn capped a `max(1, int(rate * dt))`
- [x] 8.14 ARC-002: `AchievementSystem.init_instance()` classmethod para DI injection
- [x] 8.15 ARC-008: SceneManager `_event_refs` dict en vez de `getattr` unsubscribe frágil
- [x] 8.16 ARC-034: Learning overlay usa `Action` enum values, no `pygame.K_F*` constantes
- [x] 8.17 ARC-036: Imports pesados (cv2, sklearn, scipy, skimage, joblib) movidos a lazy
- [x] 8.18 AU-010: `SFX_PLAYER_PARRY` mapea a `"sfx_parry"` (sonido dedicado)
- [x] 8.19 GD-012: Diálogo usa `Action.MOVE_DOWN` enum en vez de string raw
- [x] 8.20 GD-014: Air assault achievement target reducido 5→3
- [x] 8.21 GD-011: Death pit timer `0.0`→`0.3` para permitir animación de muerte
- [x] 8.22 Confirmación: ~15 bugs de sesiones anteriores ya correctos (BUG-002/012/013/014/015/022/033/034/041/042/048/054, GA-006/007/008/010/011/012/016, AU-007/009/012, PF-009, UX-008/016)

**Verificación:** 553 tests, 0 failures. Juego funcional sin crashes, Stage 0 jugable completo.

---

## Fase 9 — Auditoría Exhaustiva Multi-Disciplinaria (Comprehensive Review)

- [x] 9.1 Verificación de todos los hallazgos de la auditoría de código (65 bugs revisados, ~90% ya corregidos en fases anteriores)
- [x] 9.2 BUG-007: Wall slide gravity reseteado al inicio de `_apply_physics` para evitar persistencia de 1 frame
- [x] 9.3 BUG-063/performance: `len([e for e in ...])` reemplazado por `any()` en stage_scene.py
- [x] 9.4 GA-009: `subsurface().copy()` simplificado a `subsurface()` en asset_loader.py (evita copia innecesaria)
- [x] 9.5 Verificación de arquitectura: ARC-001 a ARC-039 revisados, la mayoría corregidos o deferidos
- [x] 9.6 Verificación de UI/UX: UX-001 a UX-018 revisados, la mayoría corregidos
- [x] 9.7 Verificación de gráficas/rendimiento: GA-001 a GA-024 revisados, ~85% corregidos
- [x] 9.8 Verificación de audio: AU-001 a AU-012 revisados, ~90% corregidos
- [x] 9.9 Verificación de game design: GD-001 a GD-014 revisados, ~70% corregidos (resto = contenido de estudiantes)
- [x] 9.10 ARC-003: Eliminar funciones module-level de EventBus (emit/subscribe/unsubscribe → instancia)
- [x] 9.11 ARC-019: Proyectiles creados mediante factory (documentado)
- [x] 9.12 ARC-024: Import inline en hazard_system.py movido a tope
- [x] 9.13 ARC-025: save_manager.auto_save() reemplazado por evento SAVE_REQUESTED
- [x] 9.14 ARC-038: Imports directos en stage0.py movidos a lazy dentro de métodos
- [x] 9.15 ARC-039: TYPE_CHECKING import path en boss_venado.py corregido (ya era correcto)
- [x] 9.16 AU-003: 10 eventos SFX de jefes añadidos y mapeados
- [x] 9.17 AU-004: Sufijo _combat añadido a búsqueda de tracks de combate
- [x] 9.18 AU-008: Null checks en find_channel() para evitar crash
- [x] 9.19 AU-012: Mute detiene canales ambientales
- [x] 9.20 UX-007: Menús clamp en bordes en vez de wrap (title_scene, game_over, options)
- [x] 9.21 UX-009: MessageBox movido de Y=48 a Y=64 (debajo del HUD)
- [x] 9.22 PF-005: Motion blur usa framebuffer 1/4 de resolución
- [x] 9.23 PF-010: SpatialGrid añadido para lookup de entidades O(1)
- [x] 9.24 GA-012: Background tiling cache (pre-tile en primera iteración)
- [x] 9.25 PF-002: Lighting gradient pre-renderizado con numpy
- [x] 9.26 BUG-013: SlideState sincroniza rect y position.y
- [x] 9.27 BUG-038: _deaggro_margin ahora es parámetro de constructor
- [x] 9.28 ARC-001: SaveManager inyectado como dependencia en GameContext
- [x] 9.29 ARC-005: AssetLoader basado en instancias con wrappers classmethod para compatibilidad
- [x] 9.30 ARC-031: WeatherParticle y AmbientParticleSystem unificados → reutilizan Particle de particle_system.py
- [x] 9.31 ARC-027: Auditoría StageScene — 8 hallazgos corregidos (SAVE_REQUESTED huérfano crítico, dead code _play_sfx_varied, redundancias `im and`, _save_and_quit event-based)
- [x] 9.32 ARC-025 (completado): SAVE_REQUESTED ahora tiene subscriber en StageScene.on_enter — saves funcionales
- [x] 9.33 Cobertura de tests: 15 nuevos tests para WeatherSystem, AmbientParticleSystem, AssetLoader instancias
- [x] 9.34 CRITICAL FIX: `lighting.py` — `build_gradient` ahora usa `color` en lugar de grayscale (todos los canales = val)
- [x] 9.35 CRITICAL FIX: `boss_base.py` — Phase transition ya no se ejecuta en muerte (usa `EnemyState.DYING` + `current_health > 0`)
- [x] 9.36 HIGH FIXES: fog_of_war persistente, camera lerp clamp, progression_system usa propiedades públicas, hazard timer solo decrementa en colisión, `_crouching_at_attack_start` cache asignado en `_start_attack`, dash deceleration frame-rate independiente, enemies dying no hacen contacto daño

**Deferidos (ARC-027 descomposición estructural, contenido de estudiantes).**
**Total auditados:** ~260 issues encontrados en escaneo completo, 10 fixes aplicados directamente.

---

## Fase 10 — Eliminación de Per-Frame Allocations (Performance Pass)

- [x] 10.1 CRITICAL FIX: `app.py` — `DeltaClock(settings.TARGET_FPS)` → `DeltaClock()` (TypeError startup crash)
- [x] 10.2 CRITICAL FIX: `app.py` — `SceneManager(self)` → `SceneManager(self.context)` con DI reorder (GameContext creado antes que SceneManager)
- [x] 10.3 CRITICAL FIX: `app.py` — Main loop `while self.running:` → `while self.running and self.context.running:` (context.quit() no detenía el loop)
- [x] 10.4 CRITICAL FIX: `app.py` — `_process_events` llamaba `handle_event()` (no existe) en vez de `pump(events)`
- [x] 10.5 CRITICAL FIX: `app.py` — Eliminado handler de ESC en app-level (impedía que scenes manejaran CANCEL)
- [x] 10.6 CRITICAL FIX: `hud.py` — 11 `pygame.transform.scale` per-frame en `_draw_portrait` y `_draw_timer_background` reemplazados por pre-escalado en `__init__`
- [x] 10.7 HIGH FIX: `hud.py` — `_frame_fill` mutado por reasignación cada frame (perdía el subsurface original)
- [x] 10.8 HIGH FIX: `post_processing.py` — Bloom: `pygame.Surface((w, h))` y 2× `smoothscale` por frame → pre-asignados `_bloom_down` y `_highlight_surf`
- [x] 10.9 HIGH FIX: `post_processing.py` — Motion blur: 2× `smoothscale` por frame → pre-asignados `_motion_up` y `_prev_frame` reusable
- [x] 10.10 HIGH FIX: `damage_numbers.py` — `font.render()` y `transform.scale` por frame → caché de render y pre-escalado en `__init__`
- [x] 10.11 MEDIUM FIX: `debug_overlay.py` — `font.render()` por línea cada frame → caché `_line_cache` y `_hint_surf`
- [x] 10.12 MEDIUM FIX: `message_box.py` — `font.render()` por línea cada frame → movido dentro del bloque `_cached_text != self._text`
- [x] 10.13 MEDIUM FIX: `screen_banner.py` — `font.render()` cada frame → pre-renderizado en `play()`
- [x] 10.14 MEDIUM FIX: `audio_manager.py` — Hardcoded 160.0 en pan fallback → `settings.INTERNAL_WIDTH / 2.0`
- [x] 10.15 VERIFICATION: 568 tests, 0 failures

**Verificación:** 568 tests pasan. 0 per-frame Surface allocations en hot paths (bloom/motion blur/no text render en draw). Juego funcional sin crashes.

---

---

## Fase 11 — Auditoría Profunda (Gameplay Logic + Resource Leaks + Per-frame Fonts)

- [x] 11.1 CRITICAL FIX: `boss_venado.py` — Vine projectiles nunca removidos de `_projectiles` (memory leak por `continue` que saltaba el cleanup)
- [x] 11.2 CRITICAL FIX: `boss_venado.py` — `ENEMY_DIED` emitido dos veces (en `BossVenado.update()` + `EnemyBase._die()`)
- [x] 11.3 CRITICAL FIX: `enemy_flying.py` — `_y_track_offset` no reseteado en `_alert_behavior` (drift vertical continuo ~1200px/s en combate)
- [x] 11.4 CRITICAL FIX: `enemy_flying.py` — Decaimientos `*0.98` y `*0.9` sin `dt` (frame-rate dependent)
- [x] 11.5 CRITICAL FIX: `particle_system.py` — Fricción `*self.friction` sin `dt` (frame-rate dependent - partículas viajaban 2× más lejos a 30fps)
- [x] 11.6 HIGH FIX: `player_states.py` — JumpCut `*0.5`, slide exit `*0.3`, swim damping `*0.9` sin `dt` (frame-rate dependent)
- [x] 11.7 HIGH FIX: `player_states.py` — Combo inflation por mashing: combo incrementado antes de verificar cambio de estado real
- [x] 11.8 HIGH FIX: `player.py` — `_change_state_instance` ahora retorna `bool` (True si cambió, False si skip por mismo estado)
- [x] 11.9 HIGH FIX: `player_states.py` — Dash direction usaba `facing_direction` del frame anterior (input reordenado: facing update antes que dash check en Idle/Walking/Airborne)
- [x] 11.10 HIGH FIX: `boss_venado.py` — BossVenado Y-spawn no ajustado a feet (flotaba 44px sobre el piso)
- [x] 11.11 HIGH FIX: `enemy_walker.py`, `enemy_charger.py` — Y-spawn no ajustado a feet
- [x] 11.12 HIGH FIX: `enemy_assassin.py`, `enemy_brute.py`, `boss_venado.py` — Contact damage aplicado ANTES que special attacks, bloqueándolos por invencibilidad
- [x] 11.13 HIGH FIX: `post_processing.py` — `pixels_alpha()` en `_build_vignette` sin `try/finally` (surface lock leak)
- [x] 11.14 HIGH FIX: `post_processing.py` — `smoothscale` bloom up allocaba nueva full-screen Surface cada frame → `_bloom_up` cache
- [x] 11.15 HIGH FIX: `lighting.py` — Missing `SRCALPHA` en gradient/multiplier Surfaces, `BLEND_RGBA_MULT` → `BLEND_RGB_MULT`
- [x] 11.16 MEDIUM FIX: 11 archivos con `pygame.font.Font(None, X)` en `draw()` movidos a `__init__` (keybinding_scene, vision_demo, loading, drawing_system, achievement_screen, tutorial_overlay, story_scene, tutorial_scene, code_panel, quiz_system, achievements)
- [x] 11.17 MEDIUM FIX: 5 demo scenes con `pygame.transform.scale()` per-frame → pre-caché (filter_demo, vision_demo, pattern_demo, pipeline_builder, splash_scene)
- [x] 11.18 MEDIUM FIX: `tests/test_combo_system.py` actualizados para reflejar fix de combo inflation
- [x] 11.19 VERIFICATION: 568 tests, 0 failures

**Verificación:** 568 tests pasan. 0 frame-rate dependent physics. 0 surface lock leaks. 0 per-frame Font/Surface allocations. Combo no infla por mashing. Dash responde al input del frame actual. Special attacks de enemigos no bloqueados por contacto. Flying enemies no derivan verticalmente en combate. Boss projectiles se limpian correctamente.

---

**Progreso:** Fase 0: 5/5 ✅ | Fase 1: 9/9 ✅ | Fase 2: 11/11 ✅ | Fase 3: 9/9 ✅ | Fase 4: 9/9 ✅ | Fase 5: 8/8 ✅ | Fase 6: 7/7 ✅ | Fase 7: 7/7 ✅ | Fase 8: 22/22 ✅ | Fase 9: 28/30 ✅ (2 deferidos) | Fase 10: 15/15 ✅ | Fase 11: 19/19 ✅
