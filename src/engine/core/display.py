"""
Module: display
System: engine.core
Academic Unit: N/A
Description: Pipeline de presentación — coordenadas WORLD → VIEWPORT → INTERNAL → DISPLAY.

AUD-754 — NATIVE RESOLUTION / FULLSCREEN / CAMERA / HUD / LEVEL GEOMETRY RESTORATION

Este módulo es la fuente de verdad para la cadena de transformación visual.

Coordenadas
-----------
 WORLD (x,y) — sistema del mapa, origen (0,0) esquina superior izquierda, unidades px.
   │ Camera Transform: screen = (world - camera.offset) * zoom
   ▼
 VIEWPORT (x,y) — rectángulo visible sobre el mundo, tamaño INTERNAL_WIDTH×INTERNAL_HEIGHT.
   │ Projection: ninguna extra, es 1:1 a INTERNAL_RENDER_TARGET
   ▼
 INTERNAL_RENDER_TARGET (x,y) — superficie donde dibuja DrawingSystem (1280×720).
   │ Display Transform: UNA única escala aspect-preserving + letterbox
   ▼
 WINDOW / DISPLAY (x,y) — ventana física/drawable (1920×1080, 1649×877, 1366×768 …)

 UI SPACE
 --------
 UI usa espacio independiente, anclado al viewport/display, no al mundo.
   UI_REFERENCE 320×240 (diseño) → escalado por ESCALA_DE_INTERFAZ → viewport.
 Anclajes: TOP_LEFT, TOP_CENTER, TOP_RIGHT, CENTER, BOTTOM etc.
 La UI nunca usa world position ni camera zoom — permanece estable al mover cámara.

Política de escalado
--------------------
 Aspect-preserving + pixel-art correctness + sin deformación.
 Para cualquier ventana W×H:
   scale = min(W / INTERNAL_W, H / INTERNAL_H)
   scaled = (INTERNAL_W*scale, INTERNAL_H*scale)
   offset = ((W - scaled.w)//2, (H - scaled.h)//2)
   viewport = (offset.x, offset.y, scaled.w, scaled.h)
 Si aspect ratios difieren → letterbox (barras horizontales) o pillarbox (verticales).
 El área de juego queda centrada, sin estirar.

No permitir doble escalado:
  NO hacer camera zoom = window/internal si ya hay display scaling.
  NO escalar superficie de texto ya rasterizada si puede evitarse.

Viewport OpenGL
--------------
 glViewport / ctx.viewport debe corresponder al drawable target correcto.
 Tras resize/fullscreen/stage_transition, actualizar viewport/projection/UI layout.
 No recrear renderer innecesariamente.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings

# Referencia de diseño para UI (maqueta original 320×240)
UI_REFERENCE_WIDTH: int = 320
UI_REFERENCE_HEIGHT: int = 240
# Safe margin para HUD (4–8% del viewport, 32px a 1280 =2.5% pero builder usa MARGEN)
SAFE_MARGIN: int = 32


def internal_size() -> tuple[int, int]:
    """Tamaño del render target interno (INTERNAL_RENDER_SIZE)."""
    return (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)


def window_size() -> tuple[int, int]:
    """Tamaño de la ventana del sistema (pygame.display.get_surface)."""
    surf = pygame.display.get_surface()
    if surf is not None:
        return surf.get_size()
    return internal_size()


def drawable_size() -> tuple[int, int]:
    """Tamaño drawable real (OpenGL framebuffer). En SDL puede diferir por DPI.

    Con SDL_VIDEODRIVER=dummy y DPI_AWARE, window==drawable. Para macOS/Windows
    con high-DPI, drawable puede ser 2×. Pygame no expone drawable directamente;
    usamos window_size como proxy y documentamos la diferencia.
    """
    # pygame-ce expone get_window_size (ventana en screen coords) vs get_surface size (drawable).
    # Si no está disponible, cae a window_size.
    try:
        # pygame.display.get_window_size existe en pygame-ce >=2.4
        ws = pygame.display.get_window_size()  # type: ignore[attr-defined]
        if isinstance(ws, tuple) and len(ws) == 2:
            return (int(ws[0]), int(ws[1]))
    except Exception:
        pass
    return window_size()


def calculate_viewport(
    display_w: int, display_h: int,
    internal_w: int | None = None, internal_h: int | None = None,
) -> tuple[int, int, int, int]:
    """Calcula el viewport letterbox aspect-preserving.

    Devuelve (x, y, w, h) en coordenadas de display donde debe dibujarse
    el contenido interno centrado y escalado uniformemente.
    """
    iw = internal_w if internal_w is not None else settings.INTERNAL_WIDTH
    ih = internal_h if internal_h is not None else settings.INTERNAL_HEIGHT
    if iw <= 0 or ih <= 0 or display_w <= 0 or display_h <= 0:
        return (0, 0, iw, ih)
    scale = min(display_w / iw, display_h / ih)
    # Para PS4 estilo nativo usamos float->int sin forzar integer scaling
    # para no dejar bordes grandes en resoluciones no múltiplo.
    scaled_w = round(iw * scale)
    scaled_h = round(ih * scale)
    offset_x = (display_w - scaled_w) // 2
    offset_y = (display_h - scaled_h) // 2
    return (offset_x, offset_y, scaled_w, scaled_h)


def display_scale(display_w: int, display_h: int) -> tuple[float, float]:
    """Factores de escala display/internal (sx, sy). Con letterbox son iguales."""
    iw, ih = internal_size()
    _, _, vp_w, vp_h = calculate_viewport(display_w, display_h, iw, ih)
    if iw == 0 or ih == 0:
        return (1.0, 1.0)
    return (vp_w / iw, vp_h / ih)


def ui_scale(viewport_w: int, viewport_h: int) -> tuple[float, float]:
    """Escala de UI: viewport / UI_REFERENCE. Preserva aspecto donde se requiere."""
    if UI_REFERENCE_WIDTH == 0 or UI_REFERENCE_HEIGHT == 0:
        return (1.0, 1.0)
    sx = viewport_w / UI_REFERENCE_WIDTH
    sy = viewport_h / UI_REFERENCE_HEIGHT
    return (sx, sy)


def aspect_ratio(w: int, h: int) -> float:
    """Relación de aspecto w/h."""
    if h == 0:
        return 0.0
    return w / h


def is_letterboxed(display_w: int, display_h: int) -> bool:
    """¿Hay barras (letterbox o pillarbox) con este display?"""
    iw, ih = internal_size()
    # Si aspect ratios difieren más allá de epsilon, hay barras
    display_ar = aspect_ratio(display_w, display_h)
    internal_ar = aspect_ratio(iw, ih)
    return abs(display_ar - internal_ar) > 0.01


def describe_pipeline() -> dict[str, str]:
    """Descripción textual del pipeline para auditoría/diagnóstico."""
    iw, ih = internal_size()
    dw, dh = drawable_size()
    ww, wh = window_size()
    vp = calculate_viewport(dw, dh, iw, ih)
    sx, sy = display_scale(dw, dh)
    return {
        "WORLD": f"origen (0,0) world px, TILE_SIZE={settings.TILE_SIZE}",
        "VIEWPORT": f"{iw}×{ih} (offset cámara)",
        "INTERNAL": f"{iw}×{ih} (render target)",
        "WINDOW": f"{ww}×{wh}",
        "DRAWABLE": f"{dw}×{dh}",
        "VIEWPORT_RECT": f"x={vp[0]} y={vp[1]} w={vp[2]} h={vp[3]}",
        "DISPLAY_SCALE": f"sx={sx:.3f} sy={sy:.3f}",
        "ASPECT_INTERNAL": f"{aspect_ratio(iw, ih):.3f}",
        "ASPECT_WINDOW": f"{aspect_ratio(ww, wh):.3f}",
        "ASPECT_DRAWABLE": f"{aspect_ratio(dw, dh):.3f}",
        "LETTERBOX": "sí" if is_letterboxed(dw, dh) else "no",
    }
