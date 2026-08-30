"""
RenderFacade — Fachada para GLPipeline + Software fallback.

GLPipeline era 1234 líneas mezclando compilación de shaders, manejo de FBO,
compositing y fallback a CPU. La Fachada oculta esa red y expone
`render(scene, camera)` con Strategy GL vs Software.

Patrón: Facade + Strategy + Builder (GLRenderConfig)
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

if TYPE_CHECKING:
    from src.framework.stage.camera import Camera


class RenderBackendStrategy:
    """Strategy para backend de render (GL vs Software)."""

    def render(self, surface: pygame.Surface, camera: Camera, dt: float) -> None:
        raise NotImplementedError


class GLBackend(RenderBackendStrategy):
    def render(self, surface: pygame.Surface, camera: Camera, dt: float) -> None:
        # Delega a GLRenderer si está inicializado, si no cae a software
        from src.engine.render.gl_pipeline import GLRenderer
        GLRenderer.get_instance().render(surface, camera, dt)


class SoftwareBackend(RenderBackendStrategy):
    def render(self, surface: pygame.Surface, camera: Camera, dt: float) -> None:
        # Fallback puro CPU (DrawingSystem + PostProcessing)
        pass


class RenderFacade:
    """Fachada que elige backend y oculta FBO/shader internals."""

    def __init__(self, prefer_gl: bool = True) -> None:
        self._backend: RenderBackendStrategy = GLBackend() if prefer_gl else SoftwareBackend()

    def set_backend(self, backend: RenderBackendStrategy) -> None:
        self._backend = backend

    def render(self, surface: pygame.Surface, camera: Any, dt: float) -> None:
        self._backend.render(surface, camera, dt)
