# PLAN DE REMEDIACIÓN — Legacy of InFest

**Objetivo:** 100% de cumplimiento entre código y documentación.
**Formato:** Cada fase debe completarse al 100% antes de pasar a la siguiente.
**Checklist:** Marcar `[x]` cuando esté completado.

---

## Fase 0 — Críticos (runtime crashes)

- [x] 0.1 Mover `fonts/game.ttf` → `assets/fonts/game.ttf`
- [x] 0.2 Corregir `PlayerSpawn_01` Y=160 → Y=192 en `stage0.tmx`
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

**Progreso:** Fase 0: 5/5 ✅ | Fase 1: 9/9 ✅ | Fase 2: 11/11 ✅ | Fase 3: 9/9 ✅ | Fase 4: 9/9 ✅ | Fase 5: 8/8 ✅ | Fase 6: 7/7 ✅ | Fase 7: 7/7 ✅
