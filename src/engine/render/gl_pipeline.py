from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import moderngl
import numpy as np
import pygame

from src.engine.core import settings
from src.engine.render.shaders import (
    bloom_frag,
    color_grading_frag,
    colorblind_frag,
    default_vert,
    lighting_frag,
    motion_blur_frag,
    passthrough_frag,
    vignette_frag,
)


@dataclass
class GLRenderConfig:
    bloom_enabled: bool = True
    bloom_threshold: float = 0.8
    bloom_intensity: float = 0.5

    vignette_enabled: bool = True
    vignette_strength: float = 0.5
    vignette_radius: float = 0.7

    color_grading_enabled: bool = False
    color_matrix: tuple[float, ...] = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)

    motion_blur_enabled: bool = False
    motion_blur_factor: float = 0.1

    colorblind_mode: int = 0

    lighting_enabled: bool = True

    vsync: bool = True
    display_scale: int = 1


class GLRenderer:
    def __init__(self, config: GLRenderConfig | None = None) -> None:
        self.config = config or GLRenderConfig()
        self.ctx: moderngl.Context | None = None
        self._initialized = False

        self._scene_fbo: moderngl.Framebuffer | None = None
        self._bloom_fbo: moderngl.Framebuffer | None = None
        self._temp_fbo: moderngl.Framebuffer | None = None
        self._prev_fbo: moderngl.Framebuffer | None = None
        self._light_fbo: moderngl.Framebuffer | None = None

        self._passthrough_prog: moderngl.Program | None = None
        self._bloom_prog: moderngl.Program | None = None
        self._color_grading_prog: moderngl.Program | None = None
        self._vignette_prog: moderngl.Program | None = None
        self._motion_blur_prog: moderngl.Program | None = None
        self._lighting_prog: moderngl.Program | None = None
        self._colorblind_prog: moderngl.Program | None = None

        self._quad_vao: moderngl.VertexArray | None = None
        self._screen_texture: moderngl.Texture | None = None

    def init(self, window_surface: pygame.Surface) -> None:
        display_w, display_h = window_surface.get_size()
        import os as _os
        _os.environ["SDL_WINDOW_OPENGL"] = "1"
        pygame.display.set_mode(
            (display_w, display_h),
            pygame.OPENGL | pygame.DOUBLEBUF,
        )
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        self._create_fbos(w, h)
        self._create_shaders()
        self._create_quad(w, h)
        self._initialized = True

    def _create_fbos(self, w: int, h: int) -> None:
        ctx = self.ctx
        if ctx is None:
            return

        self._scene_fbo = ctx.framebuffer(
            color_attachments=[ctx.texture((w, h), 4, dtype="f1")],
            depth_attachment=ctx.depth_texture((w, h)),
        )

        self._temp_fbo = ctx.framebuffer(
            color_attachments=[ctx.texture((w, h), 4, dtype="f1")],
        )

        self._bloom_fbo = ctx.framebuffer(
            color_attachments=[ctx.texture((w // 2, h // 2), 4, dtype="f1")],
        )

        self._prev_fbo = ctx.framebuffer(
            color_attachments=[ctx.texture((w, h), 4, dtype="f1")],
        )

        self._light_fbo = ctx.framebuffer(
            color_attachments=[ctx.texture((w, h), 4, dtype="f1")],
        )

    def _create_shaders(self) -> None:
        ctx = self.ctx
        if ctx is None:
            return
        self._passthrough_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=passthrough_frag,
        )
        self._bloom_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=bloom_frag,
        )
        self._color_grading_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=color_grading_frag,
        )
        self._vignette_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=vignette_frag,
        )
        self._motion_blur_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=motion_blur_frag,
        )
        self._lighting_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=lighting_frag,
        )
        self._colorblind_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=colorblind_frag,
        )

    def _create_quad(self, w: int, h: int) -> None:
        ctx = self.ctx
        if ctx is None:
            return
        vertices = np.array([
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 1.0,
        ], dtype=np.float32)
        indices = np.array([0, 1, 2, 1, 3, 2], dtype=np.int32)
        vbo = ctx.buffer(vertices.tobytes())
        ibo = ctx.buffer(indices.tobytes())
        self._quad_vao = ctx.vertex_array(
            self._passthrough_prog,
            [(vbo, "2f 2f", "in_position", "in_texcoord")],
            index_buffer=ibo,
        )

    def _run_shader_pass(
        self, program: moderngl.Program,
        source_tex: moderngl.Texture,
        uniforms: dict[str, Any] | None = None,
        target_fbo: moderngl.Framebuffer | None = None,
    ) -> None:
        ctx = self.ctx
        if ctx is None or self._quad_vao is None:
            return

        if target_fbo is not None:
            target_fbo.use()
        elif ctx.screen is not None:
            ctx.screen.use()

        source_tex.use(0)
        if "scene" in program:
            program["scene"].value = 0

        if uniforms:
            for key, value in uniforms.items():
                if key in program:
                    v = program[key]
                    if isinstance(value, bytes):
                        v.write(value)
                    else:
                        v.value = value

        self._quad_vao.render(moderngl.TRIANGLES)

    def render(
        self,
        scene_surface: pygame.Surface,
        light_surface: pygame.Surface | None = None,
    ) -> None:
        if not self._initialized or self.ctx is None:
            self._software_fallback(scene_surface)
            return

        ctx = self.ctx
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT

        scene_data = pygame.image.tostring(scene_surface, "RGBA", True)
        if self._screen_texture is None or self._screen_texture.size != (w, h):
            self._screen_texture = ctx.texture((w, h), 4, data=scene_data, dtype="f1")
        else:
            self._screen_texture.write(scene_data)

        read_fbo = self._scene_fbo
        write_fbo = self._temp_fbo

        # 1. Copy scene to read_fbo via passthrough
        read_fbo.use()
        ctx.clear(0.06, 0.06, 0.16, 1.0)
        self._run_shader_pass(
            self._passthrough_prog, self._screen_texture,
            target_fbo=read_fbo,
        )

        # 2. Bloom
        if self.config.bloom_enabled and self._bloom_prog:
            self._run_shader_pass(
                self._bloom_prog, read_fbo.color_attachments[0],
                uniforms={
                    "threshold": self.config.bloom_threshold,
                    "intensity": self.config.bloom_intensity,
                },
                target_fbo=write_fbo,
            )
            read_fbo, write_fbo = write_fbo, read_fbo

        # 3. Lighting
        if self.config.lighting_enabled and light_surface is not None and self._lighting_prog:
            light_data = pygame.image.tostring(light_surface, "RGBA", True)
            light_tex = ctx.texture((w, h), 4, data=light_data, dtype="f1")
            self._light_fbo.use()
            ctx.clear(0.0, 0.0, 0.0, 0.0)
            light_tex.use(1)
            self._lighting_prog["scene"].value = 0
            self._lighting_prog["lightMap"].value = 1
            self._run_shader_pass(
                self._lighting_prog, read_fbo.color_attachments[0],
                target_fbo=write_fbo,
            )
            light_tex.release()
            read_fbo, write_fbo = write_fbo, read_fbo

        # 4. Color grading
        if self.config.color_grading_enabled and self._color_grading_prog:
            mat = np.array(self.config.color_matrix, dtype=np.float32).reshape(3, 3)
            self._run_shader_pass(
                self._color_grading_prog, read_fbo.color_attachments[0],
                uniforms={"colorMatrix": mat.tobytes()},
                target_fbo=write_fbo,
            )
            read_fbo, write_fbo = write_fbo, read_fbo

        # 5. Vignette
        if self.config.vignette_enabled and self._vignette_prog:
            self._run_shader_pass(
                self._vignette_prog, read_fbo.color_attachments[0],
                uniforms={
                    "strength": self.config.vignette_strength,
                    "radius": self.config.vignette_radius,
                },
                target_fbo=write_fbo,
            )
            read_fbo, write_fbo = write_fbo, read_fbo

        # 6. Colorblind correction
        if self.config.colorblind_mode > 0 and self._colorblind_prog:
            self._run_shader_pass(
                self._colorblind_prog, read_fbo.color_attachments[0],
                uniforms={"mode": self.config.colorblind_mode},
                target_fbo=write_fbo,
            )
            read_fbo, write_fbo = write_fbo, read_fbo

        # 7. Motion blur
        if self.config.motion_blur_enabled and self._motion_blur_prog:
            self._prev_fbo.color_attachments[0].use(1)
            self._motion_blur_prog["prevFrame"].value = 1
            self._run_shader_pass(
                self._motion_blur_prog, read_fbo.color_attachments[0],
                uniforms={"blendFactor": self.config.motion_blur_factor},
                target_fbo=write_fbo,
            )
            prev_data = write_fbo.color_attachments[0].read()
            self._prev_fbo.color_attachments[0].write(prev_data)
            read_fbo, write_fbo = write_fbo, read_fbo

        # 8. Blit to screen
        ctx.screen.use()
        ctx.clear(0.0, 0.0, 0.0, 1.0)
        self._run_shader_pass(
            self._passthrough_prog, read_fbo.color_attachments[0],
        )
        pygame.display.flip()

    def _software_fallback(self, surface: pygame.Surface) -> None:
        display_surf = pygame.display.get_surface()
        if display_surf:
            pygame.transform.scale_by(
                surface, self.config.display_scale, display_surf,
            )

    def resize(self, width: int, height: int) -> None:
        self._create_fbos(width, height)

    def destroy(self) -> None:
        for fbo_name in ("_scene_fbo", "_temp_fbo", "_bloom_fbo", "_prev_fbo", "_light_fbo"):
            fbo = getattr(self, fbo_name, None)
            if fbo is not None:
                fbo.release()
        if self._screen_texture:
            self._screen_texture.release()
        if self._quad_vao:
            self._quad_vao.release()
        self._initialized = False
