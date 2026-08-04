"""
Module: test_subida_de_la_escena
System: tests
Academic Unit: VII

AUD-229 — subir el fotograma a la GPU costaba más que dibujarlo.

Cada fotograma se hacía ``pygame.image.tostring(superficie, "RGBA", True)``:
una pasada por los 480.000 píxeles en Python para reordenar canales y voltear
la imagen, y un `bytes` que moderngl vuelve a copiar. Medido en la máquina de
auditoría, a 800x600:

    pygame.image.tostring(RGBA, flip=True)    3,458 ms
    texture.write(bytes)                      7,517 ms
    texture.write(memoryview de la surface)   0,200 ms

Escribiendo el búfer de la superficie no hay conversión ni copia, pero los
píxeles llegan como los guarda pygame: sin voltear, con los canales en el orden
de la máquina y —esto es lo que costó encontrar— **con el alfa a cero**.

El alfa es el detalle que rompe todo en silencio. Una `Surface` creada sin
`SRCALPHA` (la superficie interna del juego lo es) tiene la máscara de alfa a
cero, así que su cuarto byte vale 0. `tostring` lo repone a 255 al convertir;
el búfer crudo no. Con `GL_BLEND` activo y `SRC_ALPHA, ONE_MINUS_SRC_ALPHA`, un
fragmento con alfa 0 **no escribe nada**: la pantalla salía entera del color de
limpieza, sin un solo error.

Aquí no hay GPU, así que no se comprueba el píxel: se comprueban las tres
propiedades que lo provocaban —el orden de canales detectado, el volteo y el
alfa forzado— más el camino de reserva, que es el que salva a las máquinas
cuyo formato no reconocemos.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.render.gl_pipeline import GLRenderer
from src.engine.render.shaders import upload_frag


@pytest.fixture(autouse=True)
def _pygame():
    if not pygame.get_init():
        pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((64, 64))
    yield


class TestDeteccionDelFormato:
    """El orden de canales se mide, no se supone: pygame lo elige según la
    plataforma y la profundidad de pantalla, y acertar por casualidad en una
    máquina no dice nada de la siguiente."""

    def test_una_superficie_normal_se_reconoce(self) -> None:
        s = pygame.Surface((8, 8))
        assert GLRenderer._swizzle_de(s) is not None, (
            "no se reconoce el formato de la superficie que usa el juego; "
            "se subiría siempre por el camino lento"
        )

    def test_bgra_pide_intercambiar_rojo_y_azul(self) -> None:
        assert GLRenderer._FORMATOS_DIRECTOS[(0x00FF0000, 0x0000FF00, 0x000000FF)] is True

    def test_rgba_no_lo_pide(self) -> None:
        assert GLRenderer._FORMATOS_DIRECTOS[(0x000000FF, 0x0000FF00, 0x00FF0000)] is False

    def test_un_formato_desconocido_cae_al_camino_de_reserva(self) -> None:
        """16 bits, o cualquier máscara rara: se convierte con `tostring`.

        Preferir correcto a rápido. Equivocarse en el orden de canales no da
        un error, da los colores cambiados — y eso llega al jugador.
        """
        s = pygame.Surface((8, 8), depth=16)
        assert GLRenderer._swizzle_de(s) is None

    def test_el_renderizador_sin_formato_no_usa_el_camino_rapido(self) -> None:
        r = GLRenderer()
        r._swizzle = None
        assert not r._subida_directa(pygame.Surface((8, 8)))

    def test_una_superficie_de_otro_formato_tampoco(self) -> None:
        """El sombreador se compiló para UN orden. Si llega otro, se convierte."""
        r = GLRenderer()
        r._swizzle = False               # compilado para RGBA
        s = pygame.Surface((8, 8))       # BGRA en Windows
        assert r._subida_directa(s) == (GLRenderer._swizzle_de(s) is False)


class TestElSombreadorDeSubida:
    def test_voltea_la_imagen(self) -> None:
        """Lo que hacía el tercer argumento de `tostring`."""
        assert "1.0 - uv.y" in upload_frag(True)
        assert "1.0 - uv.y" in upload_frag(False)

    def test_fuerza_el_alfa_a_uno(self) -> None:
        """El defecto: sin esto la mezcla alfa descarta el fotograma entero."""
        for swap in (True, False):
            fuente = upload_frag(swap)
            assert "vec4(texture(scene" in fuente and ", 1.0)" in fuente, (
                "el alfa no se fuerza: una superficie sin SRCALPHA trae alfa 0 "
                "y con GL_BLEND activo la pasada no escribiría nada"
            )

    def test_no_arrastra_el_alfa_de_la_superficie(self) -> None:
        assert ".bgra" not in upload_frag(True)
        assert ".rgba" not in upload_frag(False)

    def test_intercambia_los_canales_solo_cuando_toca(self) -> None:
        assert ".bgr" in upload_frag(True)
        assert ".rgb" in upload_frag(False)


# ── Píxeles que NO deben cruzar el bus ───────────────────────────────────


class TestElDesenfoqueNoBajaPixelesALaCpu:
    """AUD-236 — el desenfoque de movimiento costaba 5,45 ms de 16,67.

    Guardaba el fotograma para el siguiente así:

        prev_data = write_fbo.color_attachments[0].read()
        self._prev_fbo.color_attachments[0].write(prev_data)

    Eso baja 1,9 MB de la tarjeta a la CPU y los vuelve a subir en cada
    fotograma. Y un `read()` además **sincroniza**: obliga a la CPU a esperar a
    que la GPU termine todo lo pendiente, así que no sólo cuesta la copia,
    también tira por tierra el trabajo en paralelo de los dos procesadores.

    Medido en una Intel HD 530: encender el efecto costaba **5,45 ms** cuando
    ninguna otra pasada de la tubería pasa de 0,13 ms. Con `copy_framebuffer`,
    que hace la misma copia dentro de la tarjeta, son **0,12 ms** (45×).

    La prueba mira la causa, no el reloj: que nadie lea la textura de vuelta
    durante un fotograma. Un umbral en milisegundos no sobreviviría a un
    runner compartido; «no se baja un solo píxel» sí.
    """

    def _renderer_espia(self):
        import tests.test_cada_pasada_ejecuta_su_shader as base
        from src.engine.render.gl_pipeline import GLRenderConfig

        lecturas: list[str] = []

        class _TexturaQueDelata(base._Textura):
            def read(self) -> bytes:
                lecturas.append("read")
                return super().read()

        class _CtxQueDelata(base._Contexto):
            def texture(self, size, _c, **_kw):
                return _TexturaQueDelata(size)

        pygame.display.set_mode((64, 64))
        r = GLRenderer(GLRenderConfig(motion_blur_enabled=True))
        ctx = _CtxQueDelata()
        r.ctx = ctx  # type: ignore[assignment]
        from src.engine.core import settings
        r._create_fbos(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
        r._create_shaders()
        r._create_quad(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
        r._initialized = True
        return r, lecturas

    def _superficie(self):
        from src.engine.core import settings
        s = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        s.fill((40, 40, 60))
        return s

    def test_un_fotograma_no_lee_ninguna_textura(self) -> None:
        r, lecturas = self._renderer_espia()
        r.render(self._superficie(), None)
        assert not lecturas, (
            f"{len(lecturas)} lectura(s) de textura en un fotograma: los "
            "píxeles vuelven a bajar a la CPU, que es lo que costaba 5,45 ms"
        )

    def test_el_fotograma_anterior_se_copia_en_la_tarjeta(self) -> None:
        r, _ = self._renderer_espia()
        copias: list[tuple] = []
        r.ctx.copy_framebuffer = lambda d, s: copias.append((d, s))  # type: ignore[attr-defined]
        r.render(self._superficie(), None)
        assert copias, "nadie guarda el fotograma: no habría estela"
        destino, _origen = copias[0]
        assert destino is r._prev_fbo
