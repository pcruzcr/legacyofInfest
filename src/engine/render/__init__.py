"""ModernGL rendering pipeline for Legacy of InFest.

Provides GPU-accelerated rendering with shader-based post-processing:
bloom, color grading, vignette, motion blur, and deferred lighting.
"""

from src.engine.render.gl_pipeline import GLRenderConfig, GLRenderer
from src.engine.render.shaders import (
    bloom_frag,
    color_grading_frag,
    default_vert,
    motion_blur_frag,
    vignette_frag,
)

__all__ = [
    "GLRenderConfig",
    "GLRenderer",
    "bloom_frag",
    "color_grading_frag",
    "default_vert",
    "motion_blur_frag",
    "vignette_frag",
]
