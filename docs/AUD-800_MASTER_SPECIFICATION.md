# AUD-800 — Especificación Maestra (Contrato Técnico Autoritativo)

**Fecha:** 2026-09-01 · **Versión:** 1.1.0 (`pyproject.toml`) · **Rama certificada:** `feature/master-plan` basada en `bab9d78 AUD-761R`
**Precedencia:** este documento es **#1** tras el código que pasa tests. Cualquier otro documento que lo contradiga debe corregirse.

> **Principios certificados e inmutables (AUD-754..761R verificados):**
> `INTERNAL 1280×720` `VIEWPORT 80×45` `TILE 16×16` `NEAREST` `FBO 1280` `LETTERBOX` `CAMERA ZOOM 1.0` `WORLD→CAMERA→VIEWPORT→DISPLAY` `PLAYER 40×64` `HUD SCREEN SPACE` `PIXEL INTEGRITY` `NATIVE COMPOSITION`
> Cambiar cualquiera requiere evidencia concluyente `EVIDENCE → CONTRADICTION → ROOT CAUSE → IMPACT → RECOMMENDATION` y nuevo AUD.

---

## 1. Resolución y espacio

| Constante | Valor | Definición | Fichero |
|---|---|---|---|
| `INTERNAL_WIDTH` | 1280 | Resolución de diseño, coincide con TMX 80×16 | `settings.py:19` |
| `INTERNAL_HEIGHT` | 720 | 45×16, llena 16:9 sin huecos | `settings.py:20` |
| `TILE_SIZE` | 16 | 1280/16=80, 720/16=45 | `settings.py:52` |
| `VIEWPORT` | 80×45 tiles | `INTERNAL / TILE` | derivado |
| `DISPLAY` | ventana física (e.g. 1920×1080, 1649×877) | `display.py` letterbox | `display.py` |
| `DISPLAY_SCALE` | env `LOI_DISPLAY_SCALE` 1..4 clamp | ventana = internal × scale + letterbox | `settings.py:36` |
| `TARGET_FPS` | 120 (recomendado 60) | `clock.py FIXED_DT` | `settings.py:21` |
| `FRAME_BUDGET_120/60` | 8.33 / 16.67 ms | `PERFORMANCE_BASELINE.md` | `settings.py:24` |
| `CULLING_MARGEN` | 1280 | 1 pantalla extra simulada | `settings.py:127` |

**Pipeline:** `WORLD (px TMX)` → `CAMERA (offset + zoom 1.0 + shake)` → `VIEWPORT (80×45)` → `DISPLAY (letterbox escalado NEAREST)` → `FBO 1280` (si ModernGL) else `software blit` + `fbo.read 0` (prohibido readback por frame).

**Pixel integrity:** no `smoothscale`, no `zoom !=1.0` en gameplay (solo cinemáticas `animar_zoom`), no `subpixel camera` (`int(offset)`), `HUD` alineado a píxel, `background` no estirado, `parallax` por nombre (`BG_Far 0.15, Mid 0.40, Near 0.70, Terrain 1.0`).

---

## 2. Cámara

- `lerp_speed 8.0`, `snap_to_target()` para warp/respawn, `_clamp_a_los_bordes()` a `map_w - INTERNAL_WIDTH`.
- Modos: `seguir` (defecto), `zona_muerta` (48×32, Celeste), `sala` (Zelda, salto instantáneo por pantalla), `fija`, `cinematica` (Catmull-Rom).
- Shake: `apply_shake(amplitude, duration, direccion)` direccional coherente (1 ciclo, 25% cruzado, atenúa con `reduced_motion` a 25%, no elimina).
- Zoom: `zoom 1.0` vivo, `zoom_deseado`, `zoom_segundos`, `zoom_avanzar(dt)` lineal; `fijar_zoom` instantáneo para tests.

---

## 3. Jugador

- `rect 40×64` (2.5×4 tiles), `position` top-left, `feet = rect.bottom`, `prev_foot_y = spawn.y+32`.
- Física: `GRAVITY 800`, `WALK 90`, `JUMP -380`, `MAX_FALL 500`, `COYOTE 6 frames`, `DASH 200`, `AIR_DASH 1`, `AIR_JUMPS 1`, `SLOPE_SLIDE 90` (deslizamiento `sin·cos`), `COMBO 10` (1.0→3.0).
- Estados: 27 (`IDLE`, `WALKING`, `JUMPING`, `FALLING`, `CROUCHING`, `SHORT_ATTACK` 0.15s, `LONG_ATTACK` 0.4s, `HURT`, `DYING`, `DASHING`, `PARRY`, `CHARGE_ATTACK`, `WALL_SLIDE`, `LEDGE_GRAB`, `GRAB/THROW`, `SLIDE`, `SWIMMING`, `CLIMBING`, `ZIPLINE`, `ULTIMATE`, `AERIAL_*`, `GROUND_POUND`, etc.) — `player_spec.md §8.1`.
- Hitbox/hurtbox: `BaseEntity` `mascara_de_colision`, `PhysicsProfile` `plataformas`/`cenital`/`vuelo`/`natación`.
- Regla contacto: `PLAYER_FEET == CONTACT_SURFACE ±2` (`Solid` o `Platform`), validado `test_stage0_reference`.

---

## 4. HUD (screen space)

**Semántica colores:** `RED 230,60,60 = HP` · `YELLOW 240,210,60 = STAMINA` · `CYAN 70,180,220 = MANA` · `BLUE 90,140,255 = ULTIMATE` — `09_HUD_SPEC.md`.

**Layout 1280×720:** retrato `96×96` esq. sup. izq. `MARGEN 24`, barras `96×16 paso 24` debajo retrato (vida, estamina si `>0`, mana si `>0`, carga ultimate, oxígeno si `ratio>=0`), centro `score 560×64`, timer `160×44`. Minimapa `128×128` esq. sup. der. `152,24` (10% pantalla), no 192. `HUD SCREEN SPACE` sin `camera_offset`.

**Regla reflow:** cada barra activa ocupa slot; inactivas colapsan sin hueco; rects preservan ancho para tests.

---

## 5. TMX

**Cabecera:** `version 1.10`, `tiledversion 1.10.2`, `orientation orthogonal`, `renderorder right-down`, `tilewidth 16 tileheight 16`, `infinite 0`, `width = MW`, `height = MH`, `nextlayerid`, `nextobjectid`.

**Capas obligatorias:** `BG_Far`, `BG_Mid`, `BG_Near`, `Terrain`, `Terrain_Detail` (opcional), `Collision` (objectgroup), `Objects` (objectgroup), `FG_Overlay` (opcional). Validado `validate_tmx.py --ci` 38/38.

**Propiedades mapa (18):** `schema_version 1`, `stage_id`, `stage_name`, `author`, `bgm_track`, `background_zone`, `climate`, `time_limit`, `gravity_multiplier`, `ambient_light`, `start_hour`, `day_length`, `season`, `zone`, `bloom`, `vignette`, `profundidad_*`, `orden_por_y`, `sombras_proyectadas`, `ambient_fx`, `ambient_fx_rate`. Cobertura 100% en `stage0`.

**Objetos `Objects`:** `PlayerSpawn` 1× (16×32, `y+64==ground`), `Checkpoint` ≥1, `NextTrigger` ≥1, enemigos por `type` (Walker, FlyingBird, etc.), `Light` (radius,color,intensity), `Door`, `BossSpawn`, `Platform`, `Solid` en `Collision`.

**Regla suelo:** `Collision` `Solid` `width>500` `y==ground` `height 112` (608→720). Visual `Terrain` fila 38→44 mismo `y`. Delta 0.

---

## 6. Input, estados, audio, localización, persistencia

- **Input:** 31 acciones `Action` enum, `DEFAULT_KEY_BINDINGS` WASD+flechas, `InputManager` clear en `scene_manager.replace`, no leakage entre estados, modal `Z`/`X`/`ESC` documentado. `AUD-800_INPUT_MATRIX.md`.
- **Estados:** 21 (`SPLASH`, `TITLE`, `OPTIONS`, `WORLD_MAP`, `STAGE`, `PAUSE`, `INVENTORY`, `SKILL`, `SHOP`, `RECORDS`, `ACHIEVEMENTS`, `BESTIARY`, `BOSS`, `CHECKPOINT`, `DEATH`, `COMPLETE`, `LOADING`, `BOSS_RUSH`, `SAVE/LOAD`, `TUTORIAL`, `DEBUG`) — `GAME_STATE_INVENTORY.md`. Transiciones `STATE→EVENT→STATE` en `GAME_STATE_GRAPH.md`. No orphan, no dead, no loop inválido (AUD-760 I01-I10 10 intentional).
- **Audio:** `AudioManager` + `MixerBuses` (music, sfx, ui), `MusicClock`, `resolver_pista_de_musica` por `zone`/`stage_id`, `TOGGLE_MUTE M`, `reverb_zones`, `polifonia`. Cada nivel `bgm_track` declarado, transición `stage0 bgm_stage0 → stage1_1 bgm_zone1`.
- **Localización:** `locale/es.json` 142, `locale/en.json` 221, `i18n.py` fallback ES, `check_translations.py --ci` 0 English leakage UI (tutorial tips ES). Todo visible `ES`, docs `ES` único (inv. 5).
- **Persistencia:** `SaveManager` + `save_data.py` `orjson` + `user_settings` (`colorblind_mode`, `reduced_motion`, `locale`), `grade_stage`/`grade_boss` progresión, `ESCENARIOS_CON_HABILIDADES_LIBRES` para retrocompatibilidad.

---

## 7. Reglas de creación

- **Stage:** copiar `student_templates/stage_template` 80×45 16 608, editar en Tiled, validar `validate_tmx.py --ci` + `grade_stage.py`. Guía `STAGE_CREATION.md` 101 tipos (50 base + 51 props).
- **Enemy:** heredar `EnemyBase`, registrar `mascara_de_colision`, implementar `update`/`draw`, declarar en TMX `type`. Guía `ENEMY_CREATION.md`.
- **Boss:** heredar `BossBase`, 3-5 fases con telegraph, arena lock, música. Guía `BOSS_CREATION.md` + `17_BOSS_SPEC.md` (20/47 patrones, no contrato).
- **Tests:** cada fix trae test que falla antes y pasa después; no manipular código para pasar test; `mutation_check.py` ≥72% (`mixer_buses`, `bloques`).
- **Release:** `RELEASE READY` solo si `P0=0`, `P1=0`, `pytest` verde, `ruff` verde, `mypy` verde, 6 validadores verdes, runtime journey completo, screenshots capturados.

---

## 8. Validaciones futuras (no overengineer)

Obligatorias en CI: `validate_tmx --ci`, `validate_assets`, `check_translations --ci`, `check_tmx_coverage --ci`, `generate_tmx_reference --check`, `grade_stage --json`, `grade_boss --json`, `check_dependency_sync`, `check_doc_symbols`, `ruff`, `mypy` (ratchet `mypy_scope.txt`).

Recomendadas locales: `bench_sprite_batch`, `bench_gpu_postproc`, `check_orphan_systems`, `check_contrast`, `check_loudness`, `capture_dynamic_qa` 60 frames.

Este contrato es la **única fuente de verdad** tras el código. Cualquier PR que lo viole debe corregirse o documentar `EVIDENCE/CONTRADICTION/ROOT CAUSE/IMPACT/RECOMMENDATION` y recertificar.

