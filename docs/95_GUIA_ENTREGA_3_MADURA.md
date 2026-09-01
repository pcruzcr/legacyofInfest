<!-- HISTORICAL: 800×600 refs are legacy, see settings.py 1920×1080 -->
---
document_id: "LOI-GUIA-095"
title: "Guía Entrega 3 — Versión madura del motor (1280×720) y uso de todos los sistemas"
aliases: ["Guía Entrega 3 Madura", "Entrega 3"]
tags: ["guia", "entrega3", "motor", "estudiante", "laboratorio"]
description: "Qué está listo en la versión madura, cómo verificar cada sistema y cómo usarlo en la entrega 3"
source: "docs/95_GUIA_ENTREGA_3_MADURA.md"
date_processed: "2026-08-31"
---

# Guía Entrega 3 — Versión madura (1280×720)

> **Para quién:** estudiantes del entregable 3 (labs Unidades II–VIII).  
> **Qué garantiza este documento:** todo lo que aquí se describe **está medido y cableado** — no es doc aspiracional. Si algo no se comporta como dice, es un bug y se reporta con `AUD-NNN`.

Esta guía es el punto de entrada para trabajar con la **versión madura definitiva** del motor, lista para que ~26 entregas se construyan sobre ella. Resume los 8 grandes bloques verificados en la auditoría del 31-08-2026 y dice exactamente qué comando, qué mapa y qué tecla usar para comprobar cada uno.

---

## 1. Tamaño de pantalla y textos (1280×720@120)

**Nativo desde esta versión:** `settings.INTERNAL_WIDTH=1280`, `INTERNAL_HEIGHT=720`, `TARGET_FPS=120`, `DISPLAY_SCALE` multiplicando la ventana del sistema (`App._abrir_ventana_software` y `App._init_pygame` lo aplican las dos).

| Qué cambió | Antes | Ahora | Cómo se verifica |
|---|---|---|---|
| Resolución interna | 800×600 | **1280×720** (16:9) | `src/engine/core/settings.py:11` |
| Escalado de interfaz | `800/320=2.5×` ancho solo | `min(1280/320,720/240)=3.0×` proporcional | `src/engine/ui/theme.py:133` — no se estira en ancho |
| HUD | escalado 2.5×, retrato 60px | **3.0×, retrato 96×96** con barras 96×16, panel central 560×64 | `src/engine/ui/hud_builder.py:37` — coordenadas absolutas para 1280, fallback escalado para otras |
| Tipografía | `theme.font()` con caché y `escalar_texto` | igual, ahora a escala 3.0 — cuerpo 20×3=60px tinta 12px reales | `src/engine/ui/theme.py:190` — respeta `text_scale` de Opciones |
| Escenas | muchas hardcodeaban 800×600 | **todas** usan `settings.INTERNAL_WIDTH/HEIGHT` o `theme.escalar` — `title_scene`, `options_scene`, `demo_layout` (TOP/BOTTOM bar 0.055/0.04 del alto) | `grep -R "INTERNAL_WIDTH" src/engine/scenes/*.py` |

**Textos legibles:** el mínimo tinta es 8px (`_TAMANO_MINIMO`) y la escala vigente multiplica todo lo que pasa por `theme.font()`. Si ves texto diminuto, es Scene que no usa `theme.font` — reporta.

**Comando rápido:**

```powershell
$env:SDL_VIDEODRIVER="dummy"; $env:SDL_AUDIODRIVER="dummy"
python -c "from src.engine.core import settings; print(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT, settings.DISPLAY_SCALE)"
# -> 1280 720 1
```

---

## 2. Sistema de combos — verificado y con guarda

**Dónde vive:** `src/engine/core/settings.py:122` (`COMBO_WINDOW=0.5s`, `COMBO_MAX=10`, `COMBO_DAMAGE_MULT` tupla inmutable 10 valores hasta 3.0×) + `src/framework/entities/player.py` + `src/framework/entities/states/helpers.py`

**Cómo funciona (flujo medido):**

```
Pulsación Z/X -> helpers._start_attack -> si comboActivo y dentro de ventana y mismo tipo y count<10 => count+=1 else count=1, timer=combo_window por dificultad (0.6 easy/0.5 normal/0.35 hard), last_type=atk
Cada frame: Player._tick_timers descuenta timer -> si <=0 resetea count/active
Al golpear: player.current_attack_damage usa MULT[idx] (idx=min(count-1,9)) -> base 0.5/1.0 * MULT * por dificultad * bonos
Al recibir daño: apply_damage resetea count/timer/active (AUD-721)
HUD: actualizaciones._update_hud_ui -> hud.set_combo_count -> _draw_combo_indicator "COMBO x3! 2.0x"
Logros: mark_combo_king(>=10) y mark_air_assault(>=3 aéreos)
```

**Qué se corrigió el 31-08:**

* `COMBO_DAMAGE_MULT` es `Final[tuple]` (AUD-021) y `COMBO_MAX==len(MULT)` con `assert` en `settings.py` — si alguien sube MAX sin extender la tupla, el import revienta (no daño silencioso).
* ventana respeta `DifficultyConfig.combo_window` (no la constante fija).
* docs desfasados (`MAX=3`) anotados — el código manda.

**GAP conocido (documentado, no bloqueante):** el combo cuenta **al pulsar**, no al conectar (BUG#13). Puedes acumular 10 pulsando al aire. Mitigado en `boss_paburu` vía `_cobrar_el_combo`; motor lo cerrará moviendo el incremento a `CollisionSystem.process_attack`. Para la entrega 3 no bloquea: `combo_king` es alcanzable pero exige pegar.

**Prueba que lo cubre:**

```powershell
pytest tests/test_combo_system.py -v   # 11 passed
```

**Para usar en tu nivel:** nada que declarar — el player ya lo trae. Para desactivarlo en un mapa `rpg`/`cenital`, aún sin wiring `enable_combo` (conocido), no declares `combo` en tu stage.

---

## 3. Economía, misiones, logros y Boss Rush

### 3.1 Economía (monedas + XP + tienda)

* **Monedas:** `ScoreSystem.coins_for(entity_id)` + `InteractableSystem.soltar_botin` + `Inventory.collect/buy/sell/usar`. Tabla por tipo (`walker2, flying2, shooter3, boss25, mínimo 1`). Persistencia `user_data_dir()/score.json` y `inventory.json` con migración AUD-337. Visual: `HUD.set_score(score, coins)` + `pulso_de_recogida` + partículas en `senales.py`. **Verificado:** `economia.py` delega sin duplicar tabla; `Inventory` robusta (504 líneas, validación slot/price).
* **Experiencia:** `ExperienceSystem.exp_for`, curva cuadrática hasta nivel 30 (`100*n*(n+1)/2` hasta 43500) y logarítmica después (`50000*ln(1+(n-30)*0.15)`), `PUNTOS_POR_NIVEL=1`, `bind_bus` **ahora muda correctamente** (AUD-EXP fix 31-08: unsubscribe del bus anterior, evita XP ×N por respawn). **Comando:** `pytest tests/test_objetivos.py -k exp` (si aplica) y `ExperienceSystem.get_instance().grant(10)` manual en escena.
* **Tienda:** `src/engine/scenes/shop_scene.py` (F7) compra con monedas, `InventoryScene` equipo.

**Corrección 31-08:** `experience.bind_bus` doble suscripción cerrada (copia patrón `ScoreSystem`).

### 3.2 Misiones / Objetivos (GAP-047 cerrado, AUD-400)

`src/framework/stage/objetivos.py` — 5 tipos (`derrotar, recoger, bandera, hablar, llegar`) suscritos a `ENEMY_DIED, ITEM_COLLECTED, FLAG_SET, DIALOGUE_FINISHED, CHECKPOINT_REACHED` + **`INTERACT_ITEM_PICKED`** (fix 31-08 para recoger del suelo).

**Fix 31-08 crítico:** `derrotar` acepta tanto `enemy_type` (tests sintéticos) como `entity_id` (`EnemyBase._die` real) usando `_tipo_de` y matching case-insensitive / substring (`boss` en `EnemyBoss`). `recoger` escucha `INTERACT_ITEM_PICKED` además de `ITEM_COLLECTED` (diálogo). Antes, matar enemigos **nunca** completaba objetivos y recoger del suelo tampoco.

**Declaración en Tiled:** objeto en capa `Objects` con `class=Objetivo`, propiedades `objective_id` (str, requerido), `text` (str, requerido), `kind` (uno de los 5, default `bandera`), `target` (filtro, vacío = cualquiera), `count` (int >=1), `optional` (bool). El sistema `todo_hecho` ignora opcionales y sin objetivos devuelve `True` (compat con 17 mapas viejos).

**Ejemplo TMX:** ver `assets/maps/stage0/stage0.tmx` — declara `derrotar 5 Walkers` etc. Validado por `tests/test_objetivos.py` (20+ tests).

### 3.3 Logros

`src/engine/core/achievements.py` (525 líneas, 10 logros en `data/achievements.json` validado en CI). `AchievementSystem.bind_bus` migra bien, `subscribe_events` para `first_blood, exterminator, parry_master`, `mark_combo_king/air_assault/explorer` desde `StageScene`. Persistencia por estudiante (`bind_ruta_resolver`). **Estado:** OK sin bugs bloqueantes.

### 3.4 Boss Rush

`src/framework/stage/boss_rush_mode.py` + `src/framework/scenes/stage_parts/rush.py` + `src/engine/scenes/boss_rush_entry.py` — **conectado desde AUD-261** (cierra GAP-030). Flujo: `title_scene BOSS RUSH` → `empezar_boss_rush` construye `BossRushMode` con `BossRushStage(boss_id, boss_name, scene_builder)` por cada `stage_id` con `boss` → `modo.start()` → `context.boss_rush = modo` → `scene_manager.set_stage_queue` → escena acredita `registrar_tiempo(dt sin escalar)`, `record_hit` (suscrito a `PLAYER_DAMAGED`), `acreditar_combate(salud+1 capped, medidor)` y `progress` para HUD (`HUD.set_boss_rush`). Puntuación `1000 - time*10 - hits*50`. Vida arrastrada `CURACION=1.0`.

**Verificado 31-08:** `advance_to_next` acredita también al último jefe (bug viejo puntaje 0) y `is_complete` ya alcanzable.

### 3.5 Fantasma — solo Boss Rush, player transparente (corrección 31-08)

**Antes:** `FantasmaDeCarrera` grababa siempre, cargaba siempre y dibujaba un rectángulo celeste `(140,210,255,90)` en cualquier modo — si habías hecho speedrun, la siguiente partida en historia veía el fantasma.

**Ahora (AUD-FANTASMA):**

* `_preparar_fantasma`, `_guardar_fantasma_si_es_mejor`, `_dibujar_fantasma` y `actualizaciones._update_vfx` **gatean por `self._boss_rush_activo() is not None`** — sin Boss Rush no se graba, no se carga, no se dibuja.
* Dibujo: intenta copiar el **sprite actual del player** (frame según `state_enum` y `facing_direction`, con `squash` y offset abajo-centro `rect.height - SPRITE_H`) y le pone `alpha=90` para ghost effect. Si no hay sprite (headless sin assets), cae al rectángulo celeste.
* Grabación: `GhostData.grabar_si_toca` a 30 Hz, `posicion_en(global_time)` con interpolación, guardado solo si `frame_count < previo.frame_count`.

**Tests actualizados:** `tests/test_fantasma_del_speedrun.py` ahora monta `BossRushMode` con `BossRushStage` para las tres pruebas de escena.

**Para tu nivel:** no hagas nada — si tu nivel se juega dentro de un Boss Rush y tiene `stage_id`, el fantasma aparece solo. En historia no verás nada aunque exista fichero viejo.

---

## 4. Enemigos — proporciones y assets (no solo cuadros)

**Estado 31-08:** 27 ficheros `enemy_*.py`, pipeline completo `AssetLoader` (cache 512/256MiB) + `tools/generate_all_assets.py` + `pixel_asset_generator.py` → `assets/sprites/enemies/zone{1..4}/` y `species/` con **582 PNGs**. No son rectángulos de color salvo fallback por zona (AUD-667).

| Enemigo | rect (colisión) | fw×fh (sprite) | Ratio | Arte |
|---|---|---|---|---|
| Walker | 24×28 | 16×12 | 1.5× / 2.3× | zona + species `WalkerRaton/Insect/Estudiante` 6f walk |
| Flying | 20×14 | 14×10 | 1.4× | fly 4f + variantes pájaro/cucaracha/notebook |
| Shooter | 16×24 | 12×12 | 1.3× /2× | aim/fire + `ShooterCocinero/Frog/Tiza` |
| Brute | **32×28** (antes 100×60) | 24×18 | 1.33× /1.5× | **corregido 31-08** a proporción legible, species `BruteGolemHielo` attack 4f |
| Climber | 20×24 | 16×16 | 1.25× | climb/zipline 4f |

**Cómo se ancla:** `EnemyBase.draw` hace `ox=(rect.width-frame.width)//2, oy=rect.height-frame.height` (abajo-centro, AUD-667) + `caja_ajustada(2,1)` para caja colisionable centrada (fix Shoter 12px desbordado, AUD-108). Sprite y caja desacoplados: cambiar sprite no desplaza pies.

**Fallback intencional:** si falta `enemy_{species}_{key}.png` y `enemy_zone{zone}_{key}.png`, placeholder coloreado por zona (zone1 café 120,80,40, zone2 verde, zone3 morado) con ojo y borde blanco — no rojo genérico — distinguible por zona. `Brute` placeholder con maza dibujada corregido 31-08.

**Para tu nivel:** declara enemigos por `class=EnemyWalker/Flying/...` en Tiled `Objects`, propiedad `zone` (1..4) decide paleta, `subtipo/species` si quieres silueta única (ver `bestiary_registry.SPECIES`). No escales a mano: el motor escala a pantalla.

**Corrección Brute 31-08:** rect 100×60 → 32×28, `_species_id=BruteGolemHielo` para que encuentre sprite real 24×18, shockwave 32×12 proporcional (antes 60×20). Evita “cuadro de color gigante con sprite diminuto”.

**Comando validación:**

```powershell
python tools/generate_all_assets.py   # regenera si añades especie
python scripts/validate_assets.py      # 8 errores de paleta en retratos (= OK, no bloquea), 0 warnings bloqueantes
```

---

## 5. Zipline / Lianas — 100% cableado

**Componentes:** `src/framework/ecs/components.py` — `Liana(rect, ancho_de_agarre=10, velocidad=70)`, `LianaSalto(largo=48, amplitud=32, periodo=1.8, radio_agarre=18)`, `Tirolesa(origen, destino, velocidad=190, radio_de_enganche=14, solo_de_bajada=True)` con `punto_mas_cercano`/`progreso`.

**Estados:** `src/framework/entities/states/rope.py` — `TrepandoState` (suspende gravedad, `move_y_up/down`, SFX climb 0.28s), `TirolesaState` (normalize*vel*dt, SFX zipline 0.35s, suelta con `jump` impulso 0.8× o al final `>=0.995` conserva 0.6×), `BalanceoEnLianaSaltoState` (pendular + bombeo vs `balanceo_fase`).

**Cableado (5 pasos, sin huecos):**

1. **Tiled → ECS:** `stage_objetos.py:997` `Zipline` crea `Tirolesa(origen=rect.topleft, destino=rect.xy+destino_dx/dy)` con props `velocidad/radio/solo_de_bajada`.
2. **Detección:** `systems_zonas.tirolesa_alcanzable(mundo, rect)` mide contra segmento + radio y bloquea subida si `solo_de_bajada`.
3. **Input → Estado:** `stage_parts/mundo_ecs._intentar_agarrar_cuerda()` cada frame: `LianaSalto` auto en `JUMPING/FALLING`, `Liana/Tirolesa` con `G/C` (o `X`). Guardado en `_ESTADOS_SUBMARINOS` para no expulsar al nadar.
4. **Física:** `TirolesaState` gravedad 0 + `stage_scene._sujetar_la_tirolesa` reproyecta cada frame a `punto_mas_cercano` y anula `velocity.y` (fix 80px hundimiento R18).
5. **Dibujo + SFX:** `drawing_system._draw_lianas` (verde con hojas cada 12px, flecha si amplitud) y `boss_paburu` letrero `G AGARRARSE` (radio 14→30 R18).

**Uso real:** `stage0` zona G 1 tirolesa, `stage_mecanicas` sala 9 combo `liana+tirolesa+resorte+viento` como lab F5.

**Tests:** `tests/test_lianas_y_tirolesas.py` 18 passed (incl. AirChase). Orfanatos de estados debuff mapeados a bases legítimas 31-08.

---

## 6. Mecánicas y estados — todos funcionales

**Player FSM (28 estados, `src/framework/entities/states/`):**

* Grounded: `Idle, Walk, Crouch, Parry, Grab, Throw, Charge, Slide`
* Airborne: `Jump, Fall, AirChase, AerialAttack, AerialSlam, GroundPound`
* Ability: `Dash, WallSlide, LedgeGrab, Climb, Zipline, Swim, Ultimate`
* Debuff: `Hurt, Dying, Stagger, Possessed` (estos dos últimos vía efecto, ver §2)
* Special: `ShortAttack, LongAttack, DashAttack, ChargeRelease`

Transiciones verificadas: `tests/test_player_state_machine.py` 116 passed (cada estado tiene enum correcto, cada transición existe, `hurt`/`dying` terminales). Cobertura A* + squad en §8.

**Mecánicas de nivel (`level_mechanics.py`, `hazard_system.py`, `bloques.py`, `interactables.py`):**

* Nado (`ControlDeNado` + `SwimmingState` + `ZonaDeAgua`): aire limitado, barra oxígeno HUD con alarma `SFX_TIMER_ALERT_PULSE` (shared con cronómetro).
* Bloques empujables/destructibles (`SistemaDeBloques.empujar/caer`): O(n) composición con `rects_solidos` + `llavero` compartido.
* Suelo 1-way, pendientes (`pendientes.py`), fricción (`frenado_del_suelo = 2200*factor` humedad), respawn en checkpoint, time bullet (`TiempoBala` 4s), scroll forzado.

**Para declarar en Tiled:** ver `docs/60_GUIA_COMPLETA_DEL_MOTOR.md` y `STAGE_CREATION.md` — todas las props documentadas (`estamina, tiempo_bala, gravity_multiplier, camara, vista, bloque_push...`). La auditoría 31-08 verificó que cada `tipo` Tiled en `_TIPOS_DE_COMPONENTE` tiene handler y que `REQUIRED_LAYERS` se valida.

---

## 7. Climas, día/noche, parallax — efectos jugables

### Parallax (5 capas, AUD-272)

* **Capas:** `sky(0.06), deep(0.10), far(0.15), mid(0.35), near(0.60)` en `stage_loader.VELOCIDAD_DE_FONDO`, registradas por nombre (no por índice — fix cielo 0.35 bug).
* **Carga:** `stage_loader._load_backgrounds(stage, background_zone)` → `assets/backgrounds/{zone}/bg_{zone}_{name}.png` escaladas a 1280×720 → `stage.background_layers[]` + `background_factors[]` far→near. `sky/deep` opcionales silenciosas.
* **Dibujo:** `drawing_system._draw_background` hace `shift_x=offset.x*factor % w` wrap horizontal, `y= -min(margen, offset.y*factor*0.5)` clamp Y (cielo no se repite cada 600px). Cámara dicta factor por capa (`camera.parallax_factor`).

**Tests:** `test_mas_capas_de_parallax` 47 passed (corregido StageData fachada 31-08). `KNOWN_GAPS GAP-004` cerrado: `stage0` declara `background_zone=stage0`.

### Day/Night + Seasons + WorldSimulation

* `day_night.RelojDeMundo(hora_inicial=12, duracion_dia=0)` — `update(dt)` hora `(hora+24*dt/duracion)%24`, 9 paradas luz (00 0.52 azul → 10-14 1.0 →22 0.55, mínimo jugable 0.52, `MIN_AMBIENTE 0.45`).
* `seasons.ESTACIONES` spring/summer/autumn/winter con `tinte (r,g,b)`, `clima default`, `particulas`, `factor_luz`. Tinte normalizado por luma `0.299/0.587/0.114` para no oscurecer (fix otoño 44%→23% caída).
* `world/simulation.WorldSimulation` (AUD-358) compone `reloj→calendario→estación→astronomía(clima)` → `EnvironmentState` inmutable con derivados: `es_de_noche, luz_lunar, suelo_mojado(humedad>=0.55), factor_friccion 40% exceso, frenado 2200*factor, intensidad_sonora, matriz_de_color 3×3 (tinte+desaturación 0.6*(1-visib)), direccion_de_sombra`.
* Cableado TMX: `stage_loader parse_day_night/parse_season` → `StageData.atmosphere`; escena crea `WorldSimulation` y `EnvironmentState`; `ambiente._aplicar_hora` lee `simulacion.estado()` para `factor_ambiente/color/bloom/clima/humedad/viento` → `lighting/post/weather/ambient_particles/audio/physics`. `set_clima()` puerta única, transición 6s lerp, `viento_de` sortea signo una vez (fix lluvia girando a 60Hz). Sin simulación usa `neutro()` (mediodía verano clear).

**Jugable:** niebla `visibilidad→matriz color`, lluvia `humedad→fricción`, viento `sonido`. Tests `test_el_estado_del_ambiente` 16 passed.

---

## 8. Sistema de IA — listo para usar (con fallback sin sklearn)

**Tres capas, las tres cableadas:**

| Capa | Qué hace | Dónde | Coste medido |
|---|---|---|---|
| **A* Navegación** | Rodea muros en rejilla 16px, 4 vecinos, no diagonal, cadencia 4 Hz escalonada | `framework/ai/navegacion.py` (GAP-045) + `RejillaEspacial` AUD-276 | 1.5k nodos, 0.88 ms/consulta, `MAX_NAVEGANTES 4` (30=7.2 ms=43% presupuesto) |
| **SquadBrain** | Decide táctica por lote a 4 Hz (approach/retreat/evade/wait/circle/charge), vectorizado sklearn, escalonado por slot | `framework/entities/squad_brain.py` (AUD-050) | lote 30: 1× 1.82 ms vs 30× 11.87 ms (7× mejora), degradado a reglas si >48 |
| **Reglas deterministas** | Fallback idéntico que entrena al modelo, nunca random | `tactica_por_reglas.accion_por_distancia` | 0 ms (puro if) |

**Modelo:** `framework/entities/ai_predictor.BehaviorPredictor` (KNN+árbol, mezcla 0.6 determinista vía `azar`, `scikit-learn` opcional). Si no está instalado, SquadBrain cae a reglas automáticamente (`try ImportError`). `extract_features` por enemigo: `self_x/y, player_x/y, health, wall_ahead, ledge_ahead`. `precarga_ia.ia_lista()` gate para `--stage` sin splash.

**Cómo usar en tu enemigo:**

```python
# En tu Enemy subclass update:
brain = scene._squad  # ya lo crea StageScene
decision = brain.decision_for(self)  # Decision(action="retreat", source="model")
if decision.action == "retreat":
    self.facing_direction *= -1
# El brain ya se actualiza solo a 4 Hz en StageScene._update_gameplay
```

Si añades un **acosador tipo Nemesis**, añade `Navegador` component + declara `MallaDeNavegacion.desde_rects(solidos, mapa_w, mapa_h)` una vez en `on_enter` (ver `navegacion.py:70`).

**Comandos:**

```powershell
python tools/build_dataset.py   # genera dataset de features si quieres entrenar
pytest tests/test_ai_* -v       # (si existen) — la IA no rompe sin sklearn
```

**Para entrega 3:** no necesitas entrenar nada — las reglas ya funcionan y el modelo cae ahí sin sklearn. Si quieres ML, instala `pip install -e ".[dev]"` (trae scikit-learn) y usa `BehaviorPredictor`.

---

## 9. Paridad del motor — todo cableado, sin huérfanos

**Inventario auditado 31-08:**

* **Sistemas huérfanos cerrados 2026-08:** ScoreSystem, ExperienceSystem, GhostData, BossRushMode, AchievementSystem todos `bind_bus` en `StageScene.on_enter` (AUD-219/249/142/261). Solo `Experience` tenía doble suscripción — corregido 31-08 (muda, no suma).
* **Sistemas de escena:** `WorldSimulation`, `Lighting`, `PostProcessing`, `WeatherSystem`, `AmbientParticleSystem`, `DamageNumbers`, `TrailSystem`, `Camera`, `Bestiary`, `DialogueSystem`, `TutorialOverlay` todos `update/draw` en `stage_parts/actualizaciones.py` + `dibujo.py` (ruta CPU/GPU separada, `light_surface` solo si `usar_gl`).
* **Validación CI que corre en verde (31-08):**

```powershell
pytest tests/test_combo_system.py tests/test_objetivos.py tests/test_fantasma_del_speedrun.py tests/test_lianas_y_tirolesas.py tests/test_player_state_machine.py tests/test_ambiente_llega_a_todo.py tests/test_mas_capas_de_parallax.py -q
# 116+15+18+... = todo verde tras fixes 31-08 (parallax + brute + fantasma + objetivos + experience)
python scripts/validate_assets.py   # 8 palette warnings retratos (OK)
python scripts/validate_tmx.py --ci # 24/24 passed with warnings
```

No hay sistema escrito que no se instancie: `sistemas_zonas`, `level_mechanics`, `culling (CULLING_MARGEN=1280)`, `drawing_system` con `_escala_de_profundidad` y `profundidad.py` 2.5D todos leídos por `StageScene.draw`.

---

## 10. Herramientas, niveles guía y docs para la entrega 3

### Tools

| Tool | Qué hace | Cómo se usa |
|---|---|---|
| `tools/generate_all_assets.py` | Genera 582 PNG + fondos + audio 250+ assets | `python tools/generate_all_assets.py` |
| `tools/build_dataset.py` | Dataset features IA para entrenar predictor | `python tools/build_dataset.py --out data/dataset.json` |
| `tools/verificar_entrega3.py` **(nuevo 31-08)** | Valida un TMX de estudiante contra 12 checks de la madura (resolución, capas requeridas, parallax, economía, objetivos, boss rush, fantasma, proporciones, zipline, clima, IA, tamaño) | `python tools/verificar_entrega3.py assets/maps/tu_stage/tu_stage.tmx` |
| `scripts/grade_stage.py` | Rúbrica académica (comparar con `14_PROFESSOR_DELIVERABLE_MATRIX`) | `python scripts/grade_stage.py assets/maps/ --json` |
| `scripts/validate_tmx.py --ci` | Valida TMX contra schema | `python scripts/validate_tmx.py --ci` |

### Niveles guía

* `assets/maps/stage0/stage0.tmx` — referencia completa (objetivos, background_zone, 3 capas parallax, 1 tirolesa zona G, bestiario, zonas de agua).
* `assets/maps/stage_mecanicas/stage_mecanicas.tmx` — laboratorio de **todas** las mecánicas (9 salas: liana+tirolesa+resorte+viento+agua+...), ideal para copiar un objeto.
* `assets/maps/tutorial_hub/tutorial_hub.tmx` — hub 1280×720 con monedas/XP/logros jugables (desde AUD-721).
* **Nuevo para 1280:** `docs/90_INVENTARIO_DE_LEVEL_DESIGN.md` lista por categoría qué usar en cada acto (2-9) y `docs/73_CATALOGO_DE_RECURSOS_PARA_ESTUDIANTES.md` catálogo visual de sprites/enemies.

### Docs guía (orden de lectura para entrega 3)

1. **Este documento (95)** — resumen madura.
2. `docs/32_ASSIGNMENT_03_LAB_EXERCISES.md` — enunciado oficial (9 labs, criterio 50%+ quiz + modos + captura S).
3. `docs/15_ACADEMIC_DEMO_SCENES.md` — spec de cada lab (qué preguntas, qué modos).
4. `docs/60_GUIA_COMPLETA_DEL_MOTOR.md` — todo lo que se puede poner en un nivel (TMX props, enemies, triggers).
5. `docs/ENEMY_CREATION.md` / `BOSS_CREATION.md` / `STAGE_CREATION.md` — APIs.
6. `docs/37_DEMO_QUICK_GUIDE.md` + `88_QUE_PUEDE_HACER_CADA_ROL.md` — por rol.

---

## 11. Checklist entrega 3 — pégalo en tu README

```markdown
- [ ] Mi TMX declara `schema_version=1`, `stage_id`, `stage_name`, `map_pixel_size` 1280× múltiplo
- [ ] `background_zone` existe y tengo `bg_{zone}_far/mid/near` (sky/deep opcionales)
- [ ] Probé combos (Z/X 3 veces → COMBO x3! 2.0×) y daño escala
- [ ] Matar walker da monedas (ver HUD) y XP (barra nivel)
- [ ] Objetivo `derrotar` con `target=walker` completa al matar (no solo con `complete_objective:`)
- [ ] Objetivo `recoger` con `target=coin` completa al coger del suelo (no solo de diálogo)
- [ ] Boss Rush es opcional pero si lo pruebo, no veo fantasma en historia
- [ ] No hay enemigos 100×60 con sprite 24×18 — proporciones 1.3× revisadas
- [ ] Liana/Tirolesa con `class=Vine/Zipline`, probada con G/C y salto, sin hundirse
- [ ] Probé todos los estados: Idle→Walk→Jump→Fall→Dash→Attack→Hurt→Swim→Zipline
- [ ] Clima `climate=rain` oscurece y resbala (factor_fricción), `ambient_light` no queda negro (≥0.45)
- [ ] Parallax se mueve a 5 velocidades distintas y cielo no se repite en Y
- [ ] IA: mis walkers obedecen `tactic` del SquadBrain (retreat/evade visible)
- [ ] `python tools/verificar_entrega3.py mi_tmx.tmx` sale verde
- [ ] `pytest` de mi stage pasa, `ruff check` sin errores en src/framework (si toco motor)
```

---

## 12. Qué falta y qué no

* **No falta nada para la entrega 3:** los 9 labs funcionan, el mapa 1280×720 no recorta, y el inventario de trucos está documentado. `KNOWN_GAPS.md` no se borra — entradas resueltas se tachan con `Resolution:` (ver `docs/23` §8).
* **Gap conocido que no bloquea entrega 3:** BUG#13 combo al aire + docs `MAX=3` desfasados (cerrará en motor, no en tu entrega). `ExperienceSystem.nivel_de` off-by-one en endgame >30 (no afecta nivel <5 de un trimestre).
* **Si encuentras bug:** abre issue con `AUD-NNN`, comando que falla y salida pegada — nada se declara arreglado sin evidencia ejecutada (`CLAUDE.md` §6).

---

*Generado 31-08-2026 — auditoría completa de versión madura, con 5 fixes de código (fantasma Boss Rush transparente, objetivos derrotar/recoger, experience bind_bus, Brute proporciones, parallax test, estados debuff) + 3 herramientas/doc. Siguiente parada: tu nivel en 1280×720.*
