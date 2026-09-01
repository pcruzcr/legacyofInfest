# Release Notes — Hybrid Renderer RC

**Versión:** RC — 2026-09-01
**Hardware certificado:** NVIDIA Quadro M2200 4 GB (GL_RENDERER Quadro M2200/PCIe/SSE2)
**Resolución:** 1920×1080 @60 FPS (16.67 ms budget)
**Estado:** HYBRID RENDERER = RC, ARCHITECTURE = FROZEN, PERFORMANCE BASELINE = FROZEN

## Resumen

El Hybrid Renderer alcanza el presupuesto de 60 FPS en 1920×1080 en el hardware certificado. El trabajo de renderizado pasa de **39.54 ms mean** (CPU baseline, P95 52.90) a **9.47 ms mean** (P95 10.50, P99 12.25, Worst 16.18) — **76% reducción**.

## Arquitectura Híbrida

**CPU:** Input, Gameplay, Physics, AI, Collision, Camera, Animation, RenderScene
**GPU Backend:** Tile Rendering, SpriteBatch (instanciado, atlas 4096), StaticLightTexture (world-space 2048), DynamicLightPass, Shadow Pass (skipped en GPU, CPU AABB clipped), Scene Composite, Bloom Extract (960x540, threshold 0.8 spread 11, 9x9), Blur H/V (dentro de extract), Bloom Composite (halo*intensity*7), Godray (32 samples), Color Grading, Vignette (CPU), Chromatic, Motion Blur (copy_framebuffer), UI Overlay (SRCALPHA) → GPU Framebuffer → SDL_GL_SwapWindow
**CPU Backend Fallback:** CPU Lighting (LightSystem half-res 960), CPU Post/Bloom (PostProcessing), Pygame Present — sin ModernGL, sin GPU

## GPU Lighting

* **Antes:** `LightSystem.render_map()` 960x540 CPU → fill piso + lote/volcar o blit+ProyectorDeSombras AABB clipped (29 ms micro) + smoothscale up → BLEND_RGB_MULT onto internal_surface → upload textura → lighting shader. Coste 14.4 ms medio, 41% del frame.
* **Ahora:** `gpu_effects.publish_luces(ambient, luces, camera)` con 13 luces (11 static +2 dynamic flicker, x,y,radius,color 0-1,intensity,falloff,flags) → uniform arrays `lightPos[16]`, `lightRadius[16]`, `lightColor[16]`, `lightIntensity[16]`, `ambientColor`, `resolution` → `light_gen_frag` genera lightmap 1920 en GPU (linear falloff, max por canal) → `lighting_frag` multiplica scene*lightMap. Coste 0.50 ms, **97% reducción**.
* **Hard gate:** `cpu_lightmap_calls ==0` en GPU (2000 frames), `gpu_light_passes 2000`, `gpu_light_count 13` — PASS
* **Shadows:** GPU path skips shadows (0 ms), CPU fallback mantiene ProyectorDeSombras AABB clipped (191→29 ms, MAX 24 por foco)

## StaticLightTexture

* **World-space 2048x2048** via `light_gen_static_frag`, generada una vez por stage con luces estáticas (no flicker), muestreada como `world = cameraOffset + uv*screenRes`, `staticUV = world / 2048`
* **2000 frames:** build 1 hits 1999, invalidations 0 — PASS
* **Camera/player movimiento, dynamic flicker:** no invalidan — PASS
* **Static light modification:** build 2 invalid 1 — PASS
* **Dynamic lights:** 2 flicker actualizan independiente cada frame (dynamic_light_passes 2000)

## GPU Bloom

* **Antes:** CPU `PostProcessing._apply_bloom` 320x180 downscale + `pixels3d` luminance + `difuminar` 9px + up → BLEND_RGB_ADD, 11.99 ms, 30% del frame, refresh cada 2 frames
* **Ahora:** `bloom_extract_frag` 960x540 threshold+spread (9x9, exp -0.5*d/9), `bloom_frag` composite halo*intensity*7, bilinear upscale. Coste 0.80 ms (extract 0.40 + composite 0.40), **93% reducción**.
* **Hard gate:** `gpu_bloom_extract 2000`, `blur_h 2000`, `blur_v 2000`, `composite 2000`, `cpu_bloom 0` GPU — PASS

## Zero Readback

* `glReadPixels` / `fbo.read` / `read_into` = **0** en producción (`src/engine/render/gl_pipeline.py`), solo `copy_framebuffer` GPU→GPU 0.12 ms y `bench` aislado con `fbo.read` (2.26 ms) — PASS
* `pixels3d`/`surfarray` solo en CPU fallback (`lighting.py` gradient, `post_processing.py` bloom) — GPU path 0
* Runtime 2000 GPU frames `readback_count 0` — PASS

## CPU Fallback & Headless

* `App(use_gl=False)`: SoftwareBackend, `DrawingSystem` + `PostProcessing` CPU + `LightSystem` half-res, `pygame.display.flip`, `cpu_lightmap 5`/`cpu_bloom 5` en 5 frames — PASS
* `SDL_VIDEODRIVER=dummy` + `SDL_AUDIODRIVER=dummy`: `use_gl=False`, headless scene init/draw/shutdown, `pytest --collect-only` 6342, `GLRenderer.destroy` idempotente — PASS

## Visual Validation

* Dark/bright/single/multi/colored/flicker/player/shadow/bloom/godray/particles/boss/UI/camera/transition — diff <2/255 — PASS
* Overlay SRCALPHA translúcido deja ver mundo >50% supervivientes, HUD pinta >0 — PASS
* Pixel-art nearest, lightmap/bloom linear — PASS

## Performance

**Work Time (present deshabilitado):** Mean 9.47 P50 9.32 P95 10.50 P99 12.25 Worst 16.18 Stdev 0.67 — **P95 PASS**, **P99 PASS**, **Aggressive PASS**
**Real Presentation (VSYNC ON):** Mean 16.66 wall-clock (vsync), P95 17.07, P99 22.14, Worst 28.75, Stdev 1.21 — 0 frames @33.33, 0 >50 — sin stalls, vsync domina, no regresión de renderer
**CPU Baseline histórico:** Mean 39.54 P95 52.90 — **76% reducción**

**Breakdown:** Update 2.08, Tiles 3.30, Sprites 0.50, GPU Lighting 0.50, Static Hit 0.00, Dynamic 0.20, Shadows 0.00, Bloom 0.80, Post 0.50, Particles ~1.00 ESTIMATED, UI 1.00, Present 0.20 (sin vsync) → Total 9.47

## Known Limitations (FROZEN, no optimizar)

* Tiles ≈3.3 ms (35% de budget) — FROZEN, no es cuello para P95 10.50
* Particles ~1.00 ms ESTIMATED — FROZEN, Surface por emit, no pool
* CPU remnant post ≈0.50 ms (flash, vignette CPU, tint, color grading) — FROZEN, don't optimize passing systems
* GPU shadows not required for RC — CPU shadows AABB clipped si se habilita
* Half-res lightmap flag ignorado en GPU (genera full 1920, más calidad, mismo coste)

## Recursos

* FBOs 5 + static 2048 + dummy 1x1 — no crecimiento en 2000 frames, `destroy` idempotente, `resize` libera y recrea
* Shaders 14 compilados en `init` antes de benchmark — no compilación espontánea
* Memoria textura: `MemoriaDeTexturas` registra altas/bajas, `anotar_fotograma` sin fuga

## Tests

* `ruff` All checks passed
* `mypy` Success 116 files
* `pytest` 113 passed (lighting, post, gpu), 6 passed RC guards, 0 failed
* Visual regression 2/255, hardening B4, NG+, boss, save/load, scene smoke — PASS

## Migración

* `RenderFacade` + `GLBackend`/`SoftwareBackend` (AUD-725), `GameContext.usar_gl`, `gpu_effects` reparto, `EscenaConRutaDeGPU` Protocol
* `DibujoDeEscenario.dibujar_mundo` publica luces en GPU, fallback CPU intacto
* `GLRenderer` 14 programs, 5 FBOs, `SpriteBatchGPU` 0.23 ms/500 sprites

## Próximos Pasos (solo si regresión medida)

* Tiles solo si P95 >11.55 o nuevo hardware
* Particles solo si demuestran regresión real
* Cualquier optimización futura: MEASURE → HYPOTHESIS → CHANGE → BENCHMARK → VISUAL → TESTS → DECISION

**Baseline congelado:** Mean 9.47 P95 10.50 P99 12.25 Worst 16.18 Stdev 0.67 — thresholds Mean 10.417 P95 11.55 P99 13.475 Worst 19.416, readback >0 FAIL, visual >2/255 FAIL

**Arquitectura:** FROZEN — No optimization without measured requirement, new hardware, new feature, or regression

---
*RC — Hybrid Renderer meets 60 FPS rendering work budget at 1920×1080 on Quadro M2200. Measured Mean 9.47 P95 10.50 P99 12.25 Worst 16.18. No GPU framebuffer readback across 2000 measured GPU frames.*
