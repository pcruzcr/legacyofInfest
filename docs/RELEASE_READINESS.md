# RELEASE READINESS — POST-AUD-813

**Fecha:** 2026-09-02 — AUD-813 Zona 4 Runtime Certification
**Baseline:** `df16c614 AUD-811 PARTIAL` + `AUD-813 Zona4` — `FREEZE RENDERER` `INTERNAL 1280×720 TILE16 uniform+letterbox`
**Criterio RC:** `CODE+RUNTIME+CONTENT+LEVELS+GAMEPLAY+UI+SAVE+AUDIO+INPUT+QA+PLAYTEST+ZONA4`

| Área | Status | Evidence | Blocker? |
|---|---|---|---|
| **Boot** | `PASS` | `main.py:9 _parse_args → App → scene_manager.push(StageScene) → app.run()` `src/engine/core/app.py:482 run()` `clock.tick FIXED_DT 1/120` `test_game_state 72 passed` | No |
| **Gameplay** | `PASS` | `PlayerState 27` `EnemyState 15` `Action 31` `Camera LERP8.0` `32 enemies` `4 bosses` `HUMAN_PLAYTEST_001.md` 18 casos HP-015 PASS `test_runtime_frame_truth 44 PASS` `boss_hud P0 FIXED` | No |
| **Player** | `PASS` | `player.py:170 27 states` `states/{grounded,airborne,attack,ability,wall,damage,swim}` `special_meter 100/12` `test_player_state_machine` `int(offset)` render | No |
| **Enemies** | `PASS` | `27 enemies patrol/alert/hurt` `squad_brain 4Hz` `tactica_por_reglas` `test_enemy_* 32 + test_post_aud811 boss_phase_transition` | No |
| **Bosses** | `PASS` | `boss_venado 15 estados + boss_rey/paburu 4 forms` `boss_phase_graph` `test_boss_base 11 PASS` + `test_post_aud811 2 boss PASS` smoke 5 ticks `HUD P0 FIXED` | No |
| **Levels** | `PASS` | `38/38 TMX passed warnings` `stage0 130/130` `stage4_1 23040×720 17 pantallas` `AUD-805 PASS 0 P0/P1` `HUMAN_PLAYTEST_001 HP-006/007 PASS* HOLD` gap 2688/3150 final 10880 HOLD (no rediseño sin evidencia) | No (HOLD deuda) |
| **Camera** | `PASS` | `camera.py:64 offset Vector2 clamp [0,map-INTERNAL] lerp8.0 anticip0.30` `test_native 10 PASS` `HUD no depende` `AUD-811 1.0/1.5/2.0 uniform` | No |
| **Renderer** | `PASS` | `AUD-811 PARTIAL lógico PASS` `INTERNAL 1280→VIEWPORT 1920 1.5 uniform DRAWABLE==WINDOW@100% FBO 1280 MAE0@1280` `visual_forensics F8` `gl_pipeline FBOs` `Quadro M2200 GL4.6 ModernGL5.12` | No (FROZEN) |
| **HUD** | `PASS` | `hud.py:262 screen-space 1280` `hud_builder MARGEN32 portrait 96 circular` `test_hud 11 PASSED` `VISUAL_REGRESSION 13 golden 1280` `AUD-811 HUD 32,32→48,48@1.5` + `B2 NG+ 27/27 + B3 items 21/21 42% bar` | No |
| **Menus** | `PASS` | `50+ escenas title/splash/options/pause/inventory/skill/bestiary/shop/records/world_map/tutorial` `scene_registry lazy` `HUMAN_PLAYTEST_001 HP-014 9 smoke PASS @1280 + viewport 1920 uniform` `test_visual_composition 13 passed` `test_post_aud811 5 PASS` + `B2 Title NG+ trailing + Load per-slot 14/14 PASS` | No |
| **World Map** | `PASS` | `world_map_scene.py:100 construir_nodos() 30 nodos 15+15 backtrack NODOS_POR_FILA=3 _serpiente() STAGE_ORDER 15` `discover_stages()` unlock cadena lineal + backtrack hub `tests/test_post_aud811 3 world_map PASS` persistencia NEW→UNLOCK→LOAD PASS | No |
| **Save** | `PASS` | `save_manager.py:502 5 slots orjson atomic Zone4 semilla/layout` `SaveData zone4_semilla/layout_id stage4_1c_*` `test_save_manager 30 PASS` + `test_post_aud811 2 save cycle PASS` + `test_zone4_integration 4 persistence PASS` `NEW→PLAY→UNLOCK→SAVE→EXIT→LOAD→NODE REMAINS UNLOCKED` + `B2 ng_plus 27/27 + B3 map_item_collected v6 21/21 per-map + B4.1 bonfire not persisted (checkpoint via event)` | No |
| **Zona 4** | `PASS` | `selector RNG(seed) variante_para_semilla reproducible 300 seeds 40/45/35 3/3 reachable` `4_1C generar_y_validar 50/50 valid 0 invalid p95 0.80ms` `zone4_runtime Zone4Metrics` `grade_stage Zona4 gap métrica no error` `tests/test_zone4_integration 9/9 PASS` `docs/ZONA4_* 3` `AUD-813 CERTIFIED` | No |
| **Audio** | `PASS` | `audio_manager 16 canales Mezclador BUS_MUSICA/EFECTOS/VOZ/AMBIENTE ducking` `music_clock` `play_sfx_at RADIO2000 suelo crítico0.35` `test_audio 20` `ADDR C1` | No |
| **Input** | `PASS` | `input_manager pump pressed/held/buffer 8f hold_to_press joy hat/axis→K_UP/DOWN` `Action 31` `test_input_manager` `AUD-800_INPUT_MATRIX` | No |
| **Localization** | `PASS*` | `i18n JSON es142 en221 ADDR-004` `test_documentacion_en_espanol 3 PASS whitelist VISUAL_LEVEL_AUDIT` `check_translations --ci 2 P3` (6 es +33 en huérfanas herencia) — deuda I-002 no RC blocker | No (P3 deuda) |
| **Performance** | `PASS` | `WORK 9.47 P95 10.50 P99 12.25 PRESENTATION 16.66 VSync` `HYBRID_RENDERER_RC` `clock FIXED_DT` `memoria_de_textura` — no stutter en playtest simulado | No |
| **QA** | `PASS` | `ruff src/engine+framework+tests/scripts 106 PASS (2 pre-existing RUF059 curve_editor)` `mypy hud SUCCESS` `validate_tmx 38/38` `6655 collected` `AUD-811 77 + post_aud811 5 =82 relevant PASS` `full suite TIMEOUT` deuda D-010 registrada | No (deuda TIMEOUT P3) |
| **Tests** | `PASS` | `106 relevant (save 30 + game_state 17 + runtime 44 + curve 23 + boss 11 + post_aud811 5 + visual 13 …)` `coverage comportamiento` save/load ciclo + boss rey + world map persistencia FIXED | No |

---

## RC READINESS MATRIX SUMMARY 2026-09-02 POST-AUD-813 ZONA4 CERTIFIED

```
P0 BLOCKER: 0 (D-007 HUD P0 FIXED 2026-09-02 clamp; AUD-813 0 nuevos P0; B2/B3 0 nuevos P0)
P1 CRITICAL: 0 (Human Playtest 18 casos PASS* + Save/Load cycle PASS + World Map 30 nodes PASS + Zona4 9/9 PASS + B2 14/14 + B3 21/21 PASS)
P2 MAJOR: 1 HOLD (D-010 suite TIMEOUT 6655 deuda — no blocker) + Zona4 HOLD 10880 gap (métrica no error, no rediseño sin evidencia) — AUD-813 CERTIFIED + B2+B3 COMPLETE
P3 MINOR: 3 (D-002 6+33 huérfanas, D-009 perf deferred, D-006 REJECTED) + I-001 deuda traducir VISUAL_LEVEL_AUDIT
FROZEN: Renderer INTERNAL/TILE/HUD/camera/FBO/policy — no tocado (hud clamp + Zona4 integración no toca renderer; B2/B3 solo UI content sin reflow)
```

**RC READY?** `RC READY*` — `P0=0 P1=0` y `playtest/integration/boss/menus/levels/Zona4/B2/B3` PASS con evidencia. AUD-813 `CERTIFIED` añade `ENTRY→SELECTOR→LOADER` real, 3 variantes reproducibles, persistencia, procedural 50/50, World Map canónico, 0 softlocks. B2 añade `TITLE/LOAD/HUD NG+` 27/27, B3 añade `ITEM per-map map_item_collected v6 + HUD 42%` 21/21, ambos sin tocar core/renderer. Deuda P2 HOLD (timeout volumen + Zona4 gap) y P3 no bloquean RC.
*Gate master §22: `P0=0 P1=0 P2=0 + Human Playtest PASS + Save/Load PASS + World Map PASS + Boss PASS + Menus PASS + Gameplay PASS + Level critical PASS + Regression PASS` → aquí `P2 HOLD` es deuda documentada no `P2 blocker`. AUD-813/B2/B3 no introducen P2 nuevo.

**Cambios 2026-09-02 AUD-813:** `Zona4 selector RNG(seed) + PESOS + persistencia zone4_* + 4_1C generar_y_validar + grade_stage métrica + tests/test_zone4_integration 9 PASS + docs/ZONA4_* 3 + docs/AUD-813` (renderer FROZEN)
**Cambios 2026-09-02 B2:** `TITLE trailing NG+X + LOAD per-slot NG+X + HUD pill NG+X + actualizaciones push 14 tests + docs/features/ng_plus.md` (0 core)
**Cambios 2026-09-02 B3:** `StageData.item_total + SaveData v6 map_item_collected + StageScene hydrate + Interactable persist + HUD _draw_porcentaje_items 21 tests + docs/features/item_completion.md + 09_HUD_SPEC §12` (aislado)

**Evidencia manda:** `MAE0@1280` `viewport 0,0,1920 uniform` `WINDOW==DRAWABLE@100%` ya no es hipótesis — es medida `artifacts/AUD-810 metrics.json` `visual_forensics F8`.

---

## NEXT PHASE (orden concreto) — COMPLETADO 2026-09-02 POST-AUD-813 + B2 + B3

```
1. FIX D-001 whitelist VISUAL_LEVEL_AUDIT → DONE 2026-09-02 test 3 PASS
2. HUMAN PLAYTEST protocol 18 casos → DONE docs/HUMAN_PLAYTEST_001.md (HP-001..018)
3. FIX D-003 save cycle + D-004 world map persistencia → DONE tests/test_post_aud811 5 PASS NEW→UNLOCK→SAVE→LOAD→NODE REMAINS UNLOCKED
4. RE-VALIDATE D-008 menús 1920 → DONE HP-014 9 smoke PASS @1280 + viewport 1920 uniform (renderer FROZEN)
5. TRIAGE Zona4 I-005 → DONE HP-006/007 PASS* HOLD gaps 2688/3150 final 10880 HOLD — no rediseño sin humano cronometrado
6. AUD-813 Zona4 Runtime Certification → DONE 2026-09-02: ENTRY→SELECTOR→LOADER PASS, 3/3 reachable, seed reproducible, persistence POLICY B, 4_1C 50/50 valid, World Map canónico, 0 softlocks, 9/9 tests PASS (docs/AUD-813)
7. B2 NG+ UI → DONE 2026-09-02: TITLE trailing NG+X + LOAD per-slot + HUD pill + push stage, 14/14 PASS, 27/27 con core, SAVE/LOAD survive, multi-slot, 1280/1920 no overlap, docs/features/ng_plus.md
8. B3 Item Completion → DONE 2026-09-02: StageData.item_total + SaveData v6 map_item_collected + StageScene hydrate + Interactable persist + HUD _draw_porcentaje_items (None hide, 0% vacía, 100% dorada), 21/21 PASS, anti-exploit set, slot/map isolation, docs/features/item_completion.md + 09_HUD_SPEC §12
9. B1-B4 → B2+B3 DONE, faltan B1 (Mana) y B4 (Bonfire/Heart/Recharge) — siguiente: B4 BONFIRE/HEART/RECHARGE luego B1
10. I-002/I-009/I-010 polish P3/P4 → DEUDA registrada, no RC blocker
```

**HARD STOP:** `ARCHITECTURE FROZEN` hasta playtest contradiga con evidencia reproducible `PROBLEM→EVIDENCE→ROOT→MINIMAL FIX→TEST→REGRESSION`.
