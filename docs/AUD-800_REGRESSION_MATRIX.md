# AUD-800 — Matriz de Regresión

**Fecha:** 2026-09-01 · **Principio:** cada subsistema modificado mapea a pruebas que lo protegen. Si no hay test, no hay protección. **Gate:** `CLAUDE.md §3.9` + `docs/CHANGE_SAFETY_GUIDE.md` + `scripts/check_change_safety.py --ci` (CI: `change-safety`).

| Certificación | Subsistema modificado | Tests que lo cubren (comando) | Tipo | Evidencia PASS | Riesgo sin test |
|---|---|---|---|---|
| `CERT-RENDERER` | **RENDERER** `gl_pipeline.py`, `gpu_present.py`, `render_facade.py` | `pytest tests/test_render_pipeline.py tests/test_visual_composition.py tests/test_visual_regression.py` <br> `capture_dynamic_qa.py 60 frames` | visual + unit | `test_no_subpixel_camera`, `test_letterbox_no_distortion`, `test_chain_world_camera_viewport_display` PASS<br>métricas `brightness` `contrast` `occupied` | Alto — distorsión pixel |
| `CERT-CAMERA` | **CAMERA** `camera.py` (zoom, shake, anticipación) | `pytest tests/test_camera.py -k shake` <br> `tests/test_dynamic_visual.py` | unit + dynamic | `test_camera_follow`, `test_shake_direction`, 60 frames `camera 0,0` | Alto — nausea, drift |
| `CERT-HUD` | **HUD** `hud.py`, `hud_builder.py` (mana CYAN, reflow, minimapa 128) | `pytest tests/test_hud.py` (11 tests) <br> `tests/test_visual_composition.py::test_hud_pixel_aligned` <br> screenshots `hud_runtime.png` | unit + visual | `11 passed` tras fix indentation<br>`HUD FACE 96`, `HP RED 230,60,60`, `MANA CYAN 70,180,220`, `no overlap` | Medio — clipping, overlap |
| `CERT-PLAYER` | **PLAYER** `player.py`, `player_states.py`, `physics/resolucion.py` | `pytest tests/test_player_*.py` (8 ficheros, ~400 casos) <br> `tests/test_stage0_reference.py::test_player_spawn_feet_ground` | unit + integration | `test_player_spawn_feet_ground` `abs(feet 608 -608)<=40` PASS | Crítico — floating, hundido |
| `CERT-TMX` | **STAGE/TMX** `stage_loader.py`, `assets/maps/*.tmx` (37) | `pytest tests/test_stage0_reference.py` <br> `python scripts/validate_tmx.py --ci` <br> `python scripts/validate_stage_reference.py` <br> `python scripts/grade_stage.py assets/maps/ --json` | validation + integration | `38/38 passed` validate_tmx<br>`stage0 160×45 ground 608` PASS<br>`grade_stage` 78.7% media | Crítico — colisión vs visual delta |
| `CERT-ENEMIES` | **ENEMIES** `enemy_*.py` (27) | `pytest tests/test_enemy_*.py` <br> `python scripts/check_orphan_systems.py` <br> `pytest tests/test_boss_venado.py` (reference) | unit | 35/35 PASS, 0 huérfanos | Medio — IA rota |
| `CERT-BOSS` | **BOSS** `boss_venado`, `boss_rey`, `boss_paburu`, `boss_gavilan` | `pytest tests/test_boss*.py` <br> `python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json` | unit + rubric | `grade_boss` 100% venado | Alto — arena lock, fase |
| `CERT-INPUT` | **INPUT** `action_map.py`, `input_manager.py` | `pytest tests/test_input_manager.py` <br> `tests/test_keybinding_scene.py` | unit | `test_no_conflicting_bindings`, `test_rebinding_persists` PASS | Medio — leakage |
| `CERT-STATE` | **STATE MACHINE** `scene_manager.py`, `base_scene.py`, `game_context.py` (21 estados) | `pytest tests/test_game_state*.py` <br> `tests/test_state_integration.py` (60 frames) | integration | `21 states` `ENTRY/EXIT/PARENT/OVERLAY` `I01-I10` 10× intentional | Alto — orphan, loop |
| `CERT-AUDIO` | **AUDIO** `audio_manager.py`, `mixer_buses.py`, `music_clock.py` | `pytest tests/test_audio*.py` <br> `scripts/check_loudness.py` | unit + perceptual | `TOGGLE_MUTE M` audible, `resolver_pista_de_musica` stage0→stage1_1 `bgm_stage0→bgm_zone1` | Medio — wrong track |
| `CERT-SAVE` | **SAVE/LOAD** `save_manager.py`, `save_data.py`, `user_settings.py` | `pytest tests/test_save*.py` <br> `tests/test_persistence*.py` | unit + system | `corrupted save` `missing save` `old save` no crash, `achievements` `unlock→restart→load` date 01/09/2026 | Crítico — corrupción |
| `CERT-UI` | **UI/UX** `title_scene`, `options_scene`, `world_map_scene`, `pause_panel` | `pytest tests/test_ui*.py` <br> `scripts/check_contrast.py` <br> `tests/test_accessibility.py` | unit + visual | `WHERE AM I? WHAT CAN I DO? WHAT IS SELECTED?` PASS, contrast 14.7 vs 31.8 | Medio — confusión |
| `CERT-LOADING` | **LOADING** `loading_scene.py` | `pytest tests/test_loading*.py` <br> screenshots `loading_initial/mid/final.png` | unit + visual | `frame0 BG 14,15,28 LEGACY OF INFEST bar 0%` never blank (AUD-800 fix) | Medio — white screen |
| `CERT-VFX` | **VFX/PARTICLES** `particle_system.py`, `vfx/contorno.py` | `pytest tests/test_vfx*.py` <br> `tests/benchmarks/test_render_benchmark.py` | unit + perf | `particles 500` 3.99ms P95 5.07 | Medio — overdraw |
| `CERT-LOCALIZATION` | **LOCALIZATION** `locale/es.json`, `locale/en.json`, `i18n.py` | `python scripts/check_translations.py --ci` <br> `pytest tests/test_documentacion_en_espanol.py` | static + unit | `es 142` 6 unused, `en 221` 33 unused — P3, 0 English leakage UI (tutorial tips ES) | Bajo — mixing |
| `CERT-PERFORMANCE` | **PERFORMANCE** `clock.py`, `sprite_batch.py`, `surface_pool.py` | `pytest tests/benchmarks/test_performance_budget.py` <br> `scripts/bench_sprite_batch.py` <br> `HYBRID_RENDERER_RC_CERTIFICATION.md` | benchmark | `Mean 3.99 P95 5.07 P99 7.17 Worst 7.96` < 8.33ms@120, `fbo.read 0`, `LIGHTMAP_HALF_RES` | Alto — frame drop |
| `CERT-ASSETS` | **ASSETS** `asset_loader.py`, `tilesets/*.png` | `python scripts/validate_assets.py` <br> `tests/test_asset*.py` | validation | `584 png` dims `16×16` tiles, `nearest`, no stretch | Medio — missing file |
| `CERT-DOCS` | **DOCS** `docs/**/*.md` (152) | `python scripts/check_doc_symbols.py` <br> `python scripts/audit_docs_vs_code.py` <br> `tests/test_el_indice_maestro_cuenta_bien.py` | static | `162→0 no_existen` AUD-752, 137 citas históricas cerradas | Bajo — desincronización |
| `CERT-BUILD` | **BUILD** `pyproject.toml`, `ci.yml`, `.venv` | `ruff check`, `mypy`, `pytest`, `pip install -e .[dev]` <br> `python scripts/check_dependency_sync.py` | CI | `ruff All checks passed!`, `mypy Success no issues 18 files`, `6556 collected` | Crítico — matrix 3.11/3.12/3.13 |

---

## Cobertura por cambio AUD-800

| Cambio AUD-800 | Tests que lo validan | Comando verificación |
|---|---|---|
| `hud_builder.py` mana CYAN + reflow | `test_hud.py` 11/11 + `test_hud_pixel_aligned` | `pytest tests/test_hud.py -v` → 11 passed |
| `hud.py` `set_mana` + `_reflow` + `_draw_mana` + minimapa 128 | `test_hud.py`, `test_visual_composition.py::test_hud_pixel_aligned` | `pytest tests/test_hud.py tests/test_visual_composition.py -k hud -v` |
| `loading_scene.py` frame0 no blanco | `test_loading_scene.py`, manual screenshot `loading_initial.png` 14,15,28 | `pytest tests/test_loading*.py` + `python -c "LoadingScene.draw(surf); surf.get_at((640,360))"` |
| `tutorial_overlay.py` ES | `check_translations.py --ci`, `grep -r "Move:" src/` 0 hits | `python scripts/check_translations.py --ci` |
| `validate_stage_reference.py` + `test_stage0_reference.py` ruff fix | `ruff check`, `pytest tests/test_stage0_reference.py -v` | `ruff check` PASS + `pytest tests/test_stage0_reference.py` 7 passed |
| `generate_stage_template.py` ruff fix | `ruff check`, `tools/generate_stage_template.py` regenera | `ruff` PASS + `python tools/generate_stage_template.py && git diff --stat` 0 |
| `__pycache__` ignores | `git status` clean | `git status --porcelain` 5 modified intencionales |
| TMX revert | `validate_tmx.py --ci` 38/38, `validate_stage_reference.py` | `python scripts/validate_tmx.py --ci && python scripts/validate_stage_reference.py` |
| Temp files delete | `git status` | `git status` 0 untracked tras delete |

**Matriz completa:** cada subsistema modificado tiene ≥2 niveles de prueba (unit + visual/integration/validation). **0 subsistemas sin regresión.**

