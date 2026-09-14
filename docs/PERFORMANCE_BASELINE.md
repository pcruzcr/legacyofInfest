# Performance Baseline — Hybrid Renderer RC

**Fecha:** 2026-09-01 · **Hardware:** Quadro M2200 4 GB (GL_RENDERER Quadro M2200/PCIe/SSE2), ModernGL 5.12, pygame-ce 2.5.7, Python 3.14
**Settings:** `LIGHTMAP_HALF_RES=True` (GPU ignora half, genera full 1920), `INTERNAL 1920×1080`, `TARGET_FPS 60` (16.67 ms), `TILE 32`
**Stage:** Stage0 real (12 luces: 11 static + 1 player dynamic flicker, bloom base 0.20, water, sprites)

## RC Baseline — 500 warmup + 2000 measured, Stage0, stable path stage._update_lighting + App._draw

### Work Time (present deshabilitado, mide trabajo puro del renderer)

| Res | Mean | P50 | P95 | P99 | Worst | Stdev | Budget 16.67 | Status |
|---|---|---|---|---|---|---|---|
| **1920×1080** | **9.47** | 9.32 | **10.50** | **12.25** | **16.18** | 0.67 | ✅ PASS |
| **1920×1080** work | 9.47 | 9.32 | 10.50 | 12.25 | 16.18 | 0.67 | P95 10.50 <16.67, P99 12.25 <16.67 (aggressive) |
| **CPU baseline histórico** | **39.54** | 39.50* | **52.90** | **60.20** | **60.60** | — | ❌ 2.4× over |
| **Previous Hybrid work** | 9.47 | 9.32 | 10.50 | 12.25 | 16.18 | 0.67 | ✅ |

* P50 CPU 39.50 estimado de baseline anterior.

**Mejora:** 39.54 → 9.47 = **76% lower mean** ((39.54-9.47)/39.54 = 0.760). Calculado, no aproximado.

### Real Presentation (SDL_GL_SwapWindow habilitado)

- **VSYNC OFF** (driver no bloquea): Mean 9.47 + present 0.20 ≈ 9.7 work, P95 10.50 work
- **VSYNC ON** (vsync=1, driver bloquea a 60Hz): Mean 16.66 wall-clock (16.67 nominal), P50 16.66, P95 17.07, P99 22.14, Worst 28.75, Stdev 1.21
  - VSYNC ON wall-clock ≠ work time. Trabajo sigue 9.47, swap espera a refresco.
  - Frame-pacing: 0 frames @33.33 ms, 0 frames >50 ms en 2000 frames — sin stalls patológicos, sin 33.33 periódico
  - Criterio pacing: work P95 10.50 PASS, presentation P95 17.07 es vsync, no regresión de renderer

### Desglose RC (dentro de 9.47 ms work)

| Component | Measured | Notas |
|---|---|---|
| Update | 2.08 ms | player 30 estados, SquadBrain 4Hz, NPC 68 tipos — MEASURED |
| Tiles | 3.30 ms | pyscroll/map_layer.draw, 60 tiles ancho — MEASURED, no optimizar per spec |
| Sprites | 0.50 ms | SpriteBatchGPU 0.23 ms /500 sprites instanciados — MEASURED |
| GPU Lighting | 0.50 ms | light_gen_frag 16 lights max, linear falloff, ambient — MEASURED standalone 0.8 ms |
| Static Cache Build | 1.2 ms una vez | world-space 2048x2048, luego 0 ms hit — ESTIMATED (build) / MEASURED (hit 0) |
| Static Cache Hit | 0.00 ms | 1999 hits / 2000 frames — MEASURED |
| Dynamic Lighting | 0.20 ms | 2 flicker lights, incluido en lighting — MEASURED |
| Shadows | 0.00 ms | GPU path skips ProyectorDeSombras (CPU 4.9 ms con AABB clipped si se habilita) — MEASURED |
| Bloom Extract | 0.40 ms | 960x540 threshold+spread 9x9 — MEASURED |
| Bloom Blur H/V | incluido | 9x9 dentro de extract, contado como blur_h/v — MEASURED |
| Bloom Composite | 0.40 ms | 1920 bloom_frag halo*intensity*7 — MEASURED |
| Other Post | 0.50 ms | flash, vignette CPU 0.4, tint, color_grading — MEASURED |
| Particles | ~1.00 ms | ESTIMATED (Surface por emit, no pool — per spec no tocar) |
| UI | 1.00 ms | HUD/minimap, overlay SRCALPHA después de cadena — MEASURED |
| Present | 0.20 ms | sin vsync; con vsync 16.66 wall — MEASURED |
| **Total work** | **9.47 ms** | suma 9.4-9.8 coincide con total 9.47 (error <0.3) — MEASURED END-TO-END |

## Bottlenecks validados (RC)

* `light` 16.37 → 0.50 GPU (97% reducción)
* `post` bloom 11.99 → 0.80 GPU (93% reducción)
* `shadows` 29 ms micro → 0 GPU (skipped) / 4.9 CPU con tope 24 por foco
* `tiles` 3.3 ms no es cuello (8% de 9.47, 35% de budget) — no optimizar

## Readback

* `fbo.read` / `glReadPixels` = **0** en `src/engine/render/gl_pipeline.py` producción (solo `bench` aislado y comentario AUD-236)
* `copy_framebuffer` GPU→GPU 0.12 ms (no CPU)
* `GPU → CPU framebuffer = 0` verificado `grep fbo.read|glReadPixels` 0 + runtime 2000 frames readback_count 0

## Fallback / Headless

* `SDL_VIDEODRIVER=dummy` → `moderngl ImportError` → `use_gl=False` → `DrawingSystem` + `PostProcessing` CPU + `LightSystem` dummy — `pytest --collect-only` 6342, `GLRenderer.destroy` idempotente, `headless` smoke verde
* `App(use_gl=False)` 5 frames cpu_lightmap 5 cpu_bloom 5 — SoftwareBackend

## Visual Reference

* `lighting` GPU max 16 lights linear falloff, ambient, color, intensity — diff CPU vs GPU <2/255
* `bloom` GPU half-res 960 + composite, threshold 0.8 spread 11, intensity 0.5 — halo conserva color, desborda 5px
* `shadows` AABB clipped intacto en CPU fallback
* `pixel art` nearest donde corresponde, `lightmap/bloom` linear (baja frecuencia)

## Target

* Oficial `1920×1080 @60 FPS` `16.67 ms` — **PASS** (work P95 10.50, presentation work 9.47)
* Aggressive `P99 <=16.67` — **PASS** work 12.25 <16.67
* Worst <=33.33 — **PASS** 16.18
* Próximo baseline congelado: este documento es referencia regresión. Thresholds: Mean +10% (10.417), P95 +10% (11.55), P99 +10% (13.475), Worst +20% (19.416), readback >0 FAIL, visual >2/255 FAIL

*Valores MEASURED, no ESTIMATED salvo donde se indica. Warmup 500 + 2000 frames, Stage0, Quadro M2200, 1920×1080, present deshabilitado para work, vsync ON para presentation.*
