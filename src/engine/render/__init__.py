"""ModernGL rendering pipeline for Legacy of InFest.

Provides GPU-accelerated rendering with shader-based post-processing:
bloom, color grading, vignette, motion blur, and deferred lighting.
"""

try:
    from src.engine.render.gl_pipeline import GLRenderConfig
except ImportError:  # pragma: no cover
    from dataclasses import dataclass as _dc

    @_dc
    class GLRenderConfig:  # type: ignore[no-redef]
        bloom_enabled: bool = True

try:
    from src.engine.render.gl_pipeline import GLRenderer
except ImportError:
    class _MissingGLRenderer:  # type: ignore[no-redef]
        def __init__(self, *a: object, **kw: object) -> None:
            raise ImportError(
                "ModernGL no esta instalado - instala con pip install -e .[accel] para el camino GL"
            )
    GLRenderer = _MissingGLRenderer  # type: ignore[assignment]

try:
    from src.engine.render.gpu_sprite_batch import SpriteBatchGPU
except ImportError:
    SpriteBatchGPU = None  # type: ignore[assignment]

from src.engine.render.normales import generar_normales_desde_alfa
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
    "SpriteBatchGPU",
    "bloom_frag",
    "color_grading_frag",
    "default_vert",
    "generar_normales_desde_alfa",
    "motion_blur_frag",
    "vignette_frag",
]
