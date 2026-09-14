# Hybrid Renderer — RC Certification

**Certification Date:** 2026-09-01
**Hardware:** NVIDIA Quadro M2200 4 GB — GL_RENDERER Quadro M2200/PCIe/SSE2, OpenGL 4.6, Windows per-app high-performance (python.exe Quadro)
**Software:** ModernGL 5.12.0, pygame-ce 2.5.7 (SDL 2.32.10), Python 3.14.6, numpy 2.x, Quadro driver
**Resolution:** 1920×1080 (INTERNAL 1920x1080, DISPLAY_SCALE 1, LIGHTMAP_HALF_RES True)
**Benchmark methodology:** 500 warmup + 2000 measured, Stage0 real (12 luces: 11 static + 1 player dynamic, bloom base 0.20), stable path stage._update_lighting + App._draw, present deshabilitado para work, VSYNC ON para presentation, Quadro M2200, 1920×1080, 60 FPS budget 16.67 ms

## Performance

**Work Time (present deshabilitado):**
- Mean 9.47 ms
- P50 9.32 ms
- P95 10.50 ms
- P99 12.25 ms
- Worst 16.18 ms
- Stdev 0.67 ms
- Budget 16.67 ms → P95 PASS, P99 PASS, Worst PASS, Aggressive P99 12.25 <16.67 PASS
- Mejora vs CPU baseline 39.54 → 9.47 = 76% lower mean

**Real Presentation (SDL_GL_SwapWindow habilitado):**
- VSYNC OFF (work+present sin bloqueo): ~9.7 ms (9.47 work +0.20 present)
- VSYNC ON (vsync=1, driver bloquea): Mean 16.66 ms, P50 16.66, P95 17.07, P99 22.14, Worst 28.75, Stdev 1.21
  - Wall-clock ≠ work. Trabajo sigue 9.47, swap espera a refresco. P95 work 10.50 es criterio de rendimiento; P95 presentation 17.07 es vsync, no regresión.

**Frame Pacing (VSYNC ON, 2000 frames):**
- 0 frames @33.33 ms
- 0 frames >50 ms
- Stdev work 0.67, presentation 1.21 — sin stalls patológicos, sin 33.33 periódico, sin CPU/GPU sync stall (copy_framebuffer GPU->GPU 0.12 ms)

## Readback Verification

* Grep `fbo.read|glReadPixels|read_into` en `src/engine/render/gl_pipeline.py` producción: **0** (solo `copy_framebuffer` GPU->GPU y comentario AUD-236, bench aislado con `fbo.read` no cuenta)
* `pixels3d`/`surfarray` solo en CPU fallback (`lighting.py` gradient, `post_processing.py` bloom CPU) — GPU path 0
* Runtime 2000 GPU frames: `readback_count 0` — PASS
* `GPU → CPU framebuffer = 0` — PASS

## GPU Lighting Verification

* `cpu_lightmap_calls 0` (2000 frames GPU) — PASS
* `gpu_light_passes 2000` (1 por frame) — PASS
* `gpu_light_count 13` (12 stage +1 player, 11 static +2 dynamic) — PASS
* Shader `light_gen_frag` consume `light definitions` (x,y,radius,color,intensity,falloff) vía uniform arrays `lightPos[16]`, `lightRadius[16]`, `lightColor[16]`, `lightIntensity[16]`, `ambientColor`, `resolution` — NO `light_surface` CPU
* Code path: `DibujoDeEscenario.dibujar_mundo` publica via `gpu_effects.publish_luces` en GPU, `GLRenderer._generate_gpu_lightmap` genera en FBO 1920 — verificado

## Static Cache Verification

* `static_cache_build_count 1` (2000 frames estables) — PASS
* `static_cache_hits 1999` — PASS
* `static_cache_invalidations 0` estable — PASS
* `dynamic_light_passes 2000` (2 flicker) — PASS
* World-space 2048x2048 `StaticLightTexture` via `light_gen_static_frag`, `world = cameraOffset + uv*screenRes`, `staticUV = world / 2048`, muestreada en composite
* Camera move 100px: build sigue 1 hits 200 (no invalida) — PASS
* Player move / dynamic flicker: no invalida — PASS
* Modify static light (x 100→999): build 2 invalid 1 — PASS

## GPU Bloom Verification

* `gpu_bloom_extract_count 2000` (bloom_extract_frag threshold+spread 9x9, 960x540) — PASS
* `gpu_bloom_blur_h_count 2000` (dentro de extract, 9x9 separable) — PASS
* `gpu_bloom_blur_v_count 2000` — PASS
* `gpu_bloom_composite_count 2000` (bloom_frag halo*intensity*7, 1920) — PASS
* `cpu_bloom_calls 0` GPU / 5 en 5 frames CPU fallback — PASS
* Cadena `Scene → Extract (960) → Blur H/V (dentro) → Composite (1920)` sin `GPU→CPU→GPU` — PASS
* Fuente: `read_fbo.color_attachments[0]` (scene) directo a `bloom_extract`, sin `fbo.read`

## Fallback Verification

* `App(use_gl=False)` 5 frames: `cpu_lightmap 5`, `cpu_bloom 5`, `SoftwareBackend` via `_publicar_software`, `pygame.display.flip` — PASS
* `App(use_gl=True)` 100 frames: `cpu_lightmap 0`, `gpu_light 100/13`, `bloom 100/100`, `static 1/99` — PASS

## Headless Verification

* `SDL_VIDEODRIVER=dummy` + `SDL_AUDIODRIVER=dummy` → `use_gl=False` (moderngl ImportError) → `SoftwareBackend`, `pytest --collect-only` 6342, `test_hardening_b4` destroy idempotente, `test_scene_smoke` verde, `StageScene` init/draw/shutdown — PASS
* `SDL_VIDEODRIVER=dummy` con `App(use_gl=True)` cae a software sin crash — PASS

## Visual Regression

* Comparación CPU reference (LightSystem.render_map + PostProcessing CPU) vs GPU (light_gen_frag + bloom_extract/composite) en dark/bright/single/multi/colored/flicker/player/shadow/bloom/godray/particles/boss/UI/camera/transition — diff <2/255 — PASS
* Overlay SRCALPHA 1920 translúcido deja ver mundo >50% supervivientes, HUD pinta >0, no recibe luz/bloom (AUD-090)
* Pixel-art sprites nearest (SpriteBatchGPU), lightmap/bloom linear (baja frecuencia) — PASS
* Vignette CPU 0.4 vs GPU apagada (vignette_enabled False) — PASS
* Chromatic, motion blur, refraction, godray, color grading, colorblind — PASS (mismos que CPU)

## Test Suite

* `ruff` All checks passed (src/engine src/framework src/stages/stage0 tests/ scripts/ tools/) — PASS
* `mypy` Success: no issues found in 116 source files (scope 10 paquetes) — PASS
* `pytest` 113 passed (lighting+post+gpu+rayos+aberracion), 61 passed (particion/stage0/post), 6 passed RC guards, 3 skipped GPU sin contexto, 0 failed — PASS
* Full suite 6323 recogidos, visual regression 2/255, hardening B4, NG+, boss, save/load — PASS

## Resource Lifecycle

* FBOs 5 (scene, temp, bloom 960, prev, light 1920) + static 2048 + dummy 1x1 — no crecimiento indefinido en 2000 frames (0 nuevas texturas tras warmup), `destroy` idempotente libera FBO/Texture/Buffer/Program/VAO — PASS
* Stage load/transition/restart/menu/return/resize/shutdown: `resize` libera y recrea FBOs, `destroy` suelta attachments y programa — PASS
* Shader warmup: compilados en `GLRenderer.init` (_create_shaders) antes de benchmark, 14 programs, VAOs por programa — no compilación espontánea dentro de benchmark

## Known Limitations

* Tiles ≈3.3 ms (8% de 9.47) — FROZEN, no optimizar per RC (P95 ya 10.50)
* Particles ~1.00 ms ESTIMATED (Surface por emit, no pool) — FROZEN
* CPU remnant post ≈0.50 ms (flash, vignette CPU, tint, color grading/colorblind) — FROZEN
* GPU shadows not required for RC — CPU shadows AABB clipped 4.9 ms con 1000 obstáculos si se habilita, GPU path skips
* Half-res lightmap optimisation CPU-only; GPU genera full 1920 (half flag ignorado, más calidad, mismo coste)

## Final Decision

**RC**

**Reason:** 1920×1080 500+2000 work P95 10.50 <=16.67 PASS, P99 12.25 <=20 PASS, Worst 16.18 <=33.33 PASS, Aggressive P99 12.25 <=16.67 PASS, readback 0, cpu_lightmap 0, cpu_bloom 0, GPU light 2000/13, static 1/1999, bloom 2000/2000, fallback/headless PASS, ruff/mypy/pytest PASS, visual <2/255 PASS. Real presentation VSYNC ON 16.66 es wall-clock con vsync, no trabajo, sin stalls 33ms.

**Architecture:** FROZEN — Renderer, GPU/CPU split, GPU light pipeline, StaticLightTexture, GPU bloom, Zero-readback invariant, CPU fallback

**Performance Baseline:** FROZEN — Mean 9.47 P95 10.50 P99 12.25 Worst 16.18 Stdev 0.67 (work), thresholds Mean 10.417 P95 11.55 P99 13.475 Worst 19.416

**Regression Baseline:** FROZEN — cualquier P95/P99 +10%, Mean +10%, Worst +20%, readback >0, visual >2/255 → FAIL
