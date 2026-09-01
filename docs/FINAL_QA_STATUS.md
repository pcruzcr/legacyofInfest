# FINAL QA STATUS — Release Candidate

**Fecha:** 2026-09-01
**Commit:** `78bee36` + `AUD-754..760` `1280×720`
**Python** `3.14.6` `pygame-ce 2.5.7` `ModernGL 5.12` `Quadro M2200`

## Tests

`pytest` `test_visual_composition 13` `native_composition 13` `native_rendering 11` `stage_spatial 43` `dynamic_visual 58` `game_state_integration 14` `camera 12` `historical 13` `el_indice 4` `ruff` PASS `mypy` 117 PASS

```
AUD-754 PASS 1280×720
AUD-755 PASS 80×45
AUD-756 PASS 40×64 2.5×4
AUD-757 PASS 26/26 0Δ
AUD-758 PASS pixel-perfect 34 screenshots
AUD-759 PASS dynamic 60/120
AUD-760 PASS 21 states 13 historical
FINAL VISUAL ACCEPTANCE PASS 156/156
```

## Audits

`AUD-754..760` `FINAL VISUAL ACCEPTANCE` `PASS` `FROZEN` `render pipeline` `camera` `pixel integrity` `TMX` `sprites` `background` `parallax` `lighting` `HUD` `collision` `NATIVE COMPOSITION` `PERFORMANCE` `REGRESSION` `PASS`

## Performance

`Mean 3.99 P95 5.07 P99 7.17 Worst 7.96` `headless 500` `stage0 1280` `Δ0` `fbo.read 0` `FBO recreation 0`

## Visual baseline

`13` `GOLDEN` `TITLE` `WORLD_MAP` `STAGE0 SPAWN` `STAGE1_1 MID` `BOSS_VENADO` `BOSS_PABURU` `PAUSE` `INVENTORY 3×3` `SKILL` `SHOP` `DEATH` `COMPLETE` `VISUAL_REGRESSION_BASELINE.md`

## Known warnings (non-blocking)

`demo levels below 720` `384×512 1024×512 928×256` `BG_COLOR` `V10` `hall intentionally sparse 2.3%` `70 Composition` `V10` `stage1_1 ambient_light 0.55 KEEP` `V10`

## Post-RC backlog

`none` `critical` — `hall` `2.3%` `stage1_1` `0.55` `demo <720` `no scaling` `migrar asset` si `≥720` `backlog`.

## Reproducibility

`Python 3.14.6` `pip install -e ".[dev]"` `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` `pytest` `ruff check src/engine src/framework src/stages/stage0 tests/ scripts/` `mypy $(grep -v '^\s*#' mypy_scope.txt | grep -v '^\s*$')` `renderer 1280×720` `assets baseline` `commit 78bee36` — reproducible `checkout` limpio.

## Git status (release baseline)

`MODIFIED` `src/engine/core/display.py` `app.py` `gl_pipeline.py` `camera.py` `stage_loader.py` `theme.py` `debug_overlay.py` `diagnostico.py` `settings.py` — `AUD-754..760` `FROZEN` `intentional` `baseline`
`ADDED` `docs/NATIVE_*` `VISUAL_*` `LEVEL_*` `STAGE_SPATIAL*` `DYNAMIC_*` `GAME_STATE_*` `HISTORICAL*` `FULL_GAME*` `RELEASE_CANDIDATE*` `FINAL_QA*` `tests/test_*` `scripts/capture_dynamic_qa.py` `assets/backgrounds/paburu/bg_paburu_far.png` `1280→` — `RC baseline`
`UNTRACKED` `qa_screenshots/*` `34` `NORMAL+DIAGNOSTIC` `1280×720` — `evidence` `baseline` `optional` `post-RC`
`CLEAN` `no accidental` `assets/src/tests/scripts/docs` `reviewed` `docs/00_MASTER_INDEX.md` `115` `114+1`

## Final clean build

`BOOT` `SPLASH 2s` `TITLE` `OPTIONS` `WORLD_MAP` `NEW GAME` `STAGE` `CHECKPOINT` `PAUSE` `INVENTORY 3×3` `SKILL` `SHOP 4 cat 8` `BOSS` `DEATH` `RESPAWN` `DEFEAT` `COMPLETE` `SAVE` `RESTART` `LOAD` `FULLSCREEN F10` `RESIZE VIDEORESIZE` — `CRITICAL JOURNEY PASS`.

## Visual smoke test

`TITLE` `WORLD_MAP 26 nodes 32×32` `STAGE0 31.8` `STAGE1_1 122.9` `STAGE2_2 163` `STAGE3 63.7` `STAGE4 35.5` `BOSS VENADO 81` `REY 106` `PABURU 47` `PAUSE overlay 180` `INVENTORY 480×360` `SKILL 48×48` `SHOP` `DEATH fade 0.5` `COMPLETE banner` — `no corruption` `no black` `no missing` `HUD` `camera` `transitions` `PASS`.

## Final status

`RELEASE CANDIDATE — PASS`
