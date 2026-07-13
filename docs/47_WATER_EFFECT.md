# Legacy of InFest — Water Effect Specification

**Document ID:** LOI-WATER-047
**Version:** 1.0.0
**Status:** Official
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

The Water Effect (`src/framework/vfx/water_effect.py`) is an animated visual overlay that renders sine-wave ripples with alpha blending. It provides a distortion effect appropriate for underwater scenes, pools, and rain puddles.

---

## 2. Architecture

### 2.1 WaterEffect
- **Overlay:** Per-pixel alpha `Surface` at screen resolution
- **Animation:** Each scanline (every 2px Y) computes a sine wave offset: `sin(y * frequency + time) * amplitude`
- **Blending:** `BLEND_RGBA_ADD` for luminous water appearance
- **Color Tint:** Default (40, 80, 160) blue at alpha 100

---

## 3. Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `speed` | 1.5 | Wave animation speed multiplier |
| `amplitude` | 4 | Maximum horizontal wave displacement (px) |
| `frequency` | 0.04 | Wave frequency (cycles per pixel) |
| `alpha` | 100 | Overlay transparency (0–255) |
| `tint` | (40, 80, 160) | RGB color of water overlay |

All adjustable via `set_params()`.

---

## 4. Implementation Status

**File:** `src/framework/vfx/water_effect.py` (50 lines)
**Status:** ✅ Complete — animated sine-wave water with configurable parameters
**Missing:** No refraction/distortion of underlying content; no surface reflections


--- Traducción al Español ---

## Efecto de Agua

### Descripción
Efecto visual de agua animada usando ondas sinusoidales.

### Características
- Animación de ondas en superficie de agua
- Distorsión de la imagen bajo el agua
- Configuración de amplitud y frecuencia
- Efecto de transparencia y reflejos

Para la especificación completa, consultar el documento original en inglés.
