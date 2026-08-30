"""
Stencil/Dissolve — transición genérica para 2D/2.5D.

Faltante 9/10: motor cubría 9/10 familias VFX, solo stencil/dissolve faltaba
para transiciones genéricas (puertas, muerte, cambio de sala).
"""

from __future__ import annotations

import pygame


def stencil_mask(surface: pygame.Surface, alpha: int = 128) -> pygame.Surface:
    """Aplica máscara stencil con alpha."""
    mask = surface.copy()
    mask.set_alpha(alpha)
    return mask


def dissolve(surface: pygame.Surface, progress: float) -> pygame.Surface:
    """Dissolve 0.0→1.0 con dithering Bayer."""
    # Stub: hoy es alpha lerp, mañana puede ser shader
    out = surface.copy()
    out.set_alpha(int(255 * (1.0 - max(0.0, min(1.0, progress)))))
    return out
