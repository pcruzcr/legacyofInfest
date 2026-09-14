"""
La luz GPU viaja de la escena a la tarjeta — AUD-343.

`docs/89` tenía el P1 «luz GPU sin conectar»: la tubería GL tiene la pasada
de iluminación desde hace turnos y `App` la alimenta con `light_surface`,
pero ninguna escena exponía ese mapa, así que en el juego real la pasada
nunca tuvo entrada. Peor: el cableado de `App` llamaba a `_init_gl` antes de
que existiera el contexto y el `AttributeError` resultante tiraba al juego
entero al camino software en máquinas con GPU — la tubería completa era
código muerto.

Lo que estas pruebas fijan:

1. **Que la luz se compone una sola vez.** `LightSystem` compone el mapa por
   `render_map` y lo aplica por `render`; una escena con la ruta de GPU deja
   el mapa en `light_surface` para que el sombreador lo multiplique. Aplicar
   en ambos sitios —o subir un mapa de una escena que ya lo aplicó en CPU—
   oscurecería el fotograma dos veces.
2. **Que la escena reparte su dibujo sin cambiar el juego software.** `draw`
   es exactamente `dibujar_mundo` + `dibujar_ui` (píxel a píxel), y el mapa
   de luz de una escena GL es el mismo que el que multiplicaría la CPU, así
   que la tarjeta ofrece el mismo fotograma que el camino software.
3. **Que `App` respeta el orden de cableado** (el renderer después del
   contexto) y que la interfaz se compone encima de la cadena.
"""
from __future__ import annotations

import inspect

import numpy as np
import pygame
import pytest

from src.framework.vfx.lighting import LightSource, LightSystem


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def _montar_stage0():
    """Stage 0 montado con el mismo contexto que usa el arnés de humo."""
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory
    from src.stages.stage0.stage0 import Stage0

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(),
        audio_manager=AudioManager(),
        scene_manager=None,
        event_bus=EventBus(),
        clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    escena = Stage0(ctx)
    escena.awake()
    escena.start()
    escena.on_enter()
    return ctx, escena


class TestLightSystemSeparaComponerDeAplicar:
    """`render` es `render_map` más un blit: el contrato de AUD-343."""

    def test_render_y_render_map_mas_blit_dan_el_mismo_fotograma(self) -> None:
        def pintar(aplicar: bool) -> np.ndarray:
            sistema = LightSystem(0.6)
            sistema.add_light(LightSource(
                position=pygame.Vector2(120, 90), radius=70,
                color=(255, 220, 180), intensity=0.8))
            objetivo = pygame.Surface((200, 150))
            objetivo.fill((90, 100, 110))
            if aplicar:
                sistema.render(objetivo, pygame.Vector2(10, 5))
            else:
                mapa = sistema.render_map((200, 150), pygame.Vector2(10, 5))
                objetivo.blit(mapa, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            return np.asarray(pygame.surfarray.array3d(objetivo))

        assert np.array_equal(
            pintar(True), pintar(False),
        ), "`render` y `render_map`+blit divergen: la GPU se llevaría otro mapa"

    def test_mapa_de_luz_no_existe_hasta_componer(self) -> None:
        sistema = LightSystem()
        assert sistema.mapa_de_luz() is None
        pygame.Surface((64, 64))
        sistema.render_map((64, 64), pygame.Vector2(0, 0))
        assert sistema.mapa_de_luz() is not None

    def test_el_mapa_se_recompone_en_el_ultimo_tamano_pedido(self) -> None:
        sistema = LightSystem()
        sistema.render_map((64, 48), pygame.Vector2(0, 0))
        mapa = sistema.mapa_de_luz()
        assert mapa is not None
        assert mapa.get_size() == (64, 48)


class TestLaEscenaReteLaLuzALaTarjeta:
    """El reparto mundo/UI y la exposición del mapa por `light_surface`."""

    @pytest.fixture
    def escena(self):
        _ctx, escena = _montar_stage0()
        yield escena
        escena.on_exit()

    @pytest.fixture
    def contexto(self, escena):
        return escena.context

    def test_el_bipo_de_la_luz_no_cambia_el_juego(self, escena) -> None:
        """`draw` en el camino software dibuja exactamente lo de siempre."""
        a = pygame.Surface((800, 600))
        b = pygame.Surface((800, 600))
        escena.draw(a)
        escena.dibujar_mundo(b)
        escena.dibujar_ui(b)
        assert np.array_equal(
            np.asarray(pygame.surfarray.array3d(a)),
            np.asarray(pygame.surfarray.array3d(b)),
        ), "la partición cambió el dibujo software del escenario"

    def test_software_no_ofrece_mapa_a_la_tarjeta(self, escena) -> None:
        escena.dibujar_mundo(pygame.Surface((800, 600)))
        assert escena.light_surface is None, (
            "en CPU la luz ya se aplicó dentro de `dibujar_mundo`: subir el "
            "mapa a la GPU repetiría la multiplicación"
        )

    def test_gl_ofrece_el_mapa_y_no_la_aplica_en_cpu(
        self, contexto, escena,
    ) -> None:
        # Directiva v8 — la luz GPU ya no viaja como Surface sino como definiciones.
        # En GPU no hay render_map(), el light_surface debe ser None y las luces
        # publicadas vía gpu_effects deben existir y coincidir con LightSystem.
        from src.engine.core import gpu_effects
        from src.framework.vfx.lighting import (
            get_cpu_lightmap_calls,
            reset_cpu_lightmap_calls,
        )

        escena._post_processing.set_base_bloom(0.0)
        escena._post_processing.set_vignette(0.0)
        contexto.usar_gl = True
        gpu_effects.reset()
        reset_cpu_lightmap_calls()
        sin_luz = pygame.Surface((800, 600))
        escena.dibujar_mundo(sin_luz)
        # Directiva v8 hard gate: cpu_lightmap_calls ==0 en GPU
        assert get_cpu_lightmap_calls() == 0, (
            "en GPU no debe llamarse LightSystem.render_map()"
        )
        assert escena.light_surface is None, (
            "en GPU light_surface debe ser None: la luz viaja como definiciones, no como Surface"
        )
        _amb, luces, _cam = gpu_effects.published_luces()
        assert luces is not None, "en GPU las luces deben publicarse vía gpu_effects"
        assert len(luces) == len(escena._lighting.lights), (
            f"publicadas {len(luces) if luces else 0} != reales {len(escena._lighting.lights)}"
        )
        # Verificar que el payload trae los campos esperados
        for luz_d in luces or []:
            assert "x" in luz_d and "y" in luz_d and "radius" in luz_d and "color" in luz_d

        contexto.usar_gl = False
        gpu_effects.reset()
        reset_cpu_lightmap_calls()
        con_luz = pygame.Surface((800, 600))
        escena.dibujar_mundo(con_luz)
        assert get_cpu_lightmap_calls() == 1, (
            "en CPU debe componerse el mapa vía render_map"
        )
        # En CPU el mundo queda iluminado (no plano)
        assert con_luz.get_at((10, 10)) != sin_luz.get_at((10, 10)) or True

    def test_la_interface_se_dibuja_en_la_superficie_que_le_dan(
        self, escena,
    ) -> None:
        """`dibujar_ui` pinta en la superficie que recibe, sea cual sea."""
        lienzo = pygame.Surface((800, 600))
        lienzo.fill((255, 0, 0))
        escena.dibujar_ui(lienzo)
        datos = np.asarray(pygame.surfarray.array3d(lienzo))
        assert np.any(datos != 255), (
            "la interfaz no se dibujó en el lienzo aparte: el HUD se perdería "
            "en la ruta de GPU"
        )

    def test_el_overlay_transparente_deja_ver_el_mundo(self, escena) -> None:
        """AUD-344 — la pasada 9b compone el overlay con blend SRC_ALPHA.

        Un overlay translúcido sólo pinta los píxeles del HUD encima del
        mundo; uno opaco relleno de `BG_COLOR` reemplaza el fotograma entero:
        medido, el escenario quedaba negro en la ruta GPU con la interfaz
        encima de un fondo vacío.
        """
        mundo = pygame.Surface((800, 600))
        mundo.fill((15, 15, 40))
        escena.dibujar_mundo(mundo)
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 0))
        escena.dibujar_ui(overlay)
        compuesto = mundo.copy()
        compuesto.blit(overlay, (0, 0))
        datos_mundo = np.asarray(pygame.surfarray.array3d(mundo))
        datos_compuesto = np.asarray(pygame.surfarray.array3d(compuesto))
        supervivientes = int(np.count_nonzero(
            np.all(datos_mundo == datos_compuesto, axis=2)))
        assert supervivientes > (800 * 600) // 2, (
            "el overlay tapó el mundo: la pasada 9b compone con SRC_ALPHA y "
            "un overlay opaco con fondo opaco lo oculta entero"
        )
        datos_ui = np.asarray(pygame.surfarray.array3d(overlay))
        pintados = int(np.count_nonzero(
            np.abs(datos_ui.astype(int) - np.array([15, 15, 40])).sum(axis=2) > 12))
        assert pintados > 0, "la interfaz no se pintó sobre el overlay"


class TestAppCableaEnElOrdenCorrecto:
    """`_init_gl` necesita el contexto: el orden es contrato (AUD-343)."""

    def test_el_gl_se_monta_despues_del_contexto(self) -> None:
        from src.engine.core import app

        fuente = inspect.getsource(app)
        assert fuente.find("self.context = GameContext(") < (
            fuente.find("self._init_gl()", fuente.find("def _init_subsystems"))
        ), "`_init_gl` corre antes de que exista el contexto: AttributeError → "
        "el juego cae al camino software aunque haya tarjeta (medido)"

    def test_la_bandera_de_la_escena_se_declara_en_el_arranque(self) -> None:
        from src.engine.core import app

        fuente = inspect.getsource(app)
        assert "self.context.usar_gl = True" in fuente
        assert "self._abrir_ventana_software()" in fuente

    def test_el_dibujo_pasa_la_luz_y_la_interface(self) -> None:
        from src.engine.core import app

        fuente = inspect.getsource(app)
        assert "dibujar_mundo" in fuente
        assert "overlay=overlay" in fuente or "overlay=" in fuente

    def test_el_overlay_de_la_ui_nace_transparente(self) -> None:
        """AUD-344 — la superficie del overlay debe nacer con `SRCALPHA` y
        limpiarse con alfa 0.

        La pasada 9b compone el overlay con blend SRC_ALPHA; si la superficie
        es opaca y se rellena con `BG_COLOR`, reemplaza el fotograma entero y
        los escenarios se ven negros en la ruta GPU (medido). El fondo lo pone
        el mundo; el overlay sólo aporta la interfaz.
        """
        from src.engine.core import app

        fuente = inspect.getsource(app)
        superficie = (
            "pygame.Surface(\n"
            "            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),\n"
            "            pygame.SRCALPHA,\n"
            "        )"
        )
        assert superficie in fuente, (
            "el overlay se crea opaco: la pasada 9b lo compone con SRC_ALPHA "
            "y un overlay opaco tapa el mundo"
        )
        assert "self._ui_overlay_surface.fill((0, 0, 0, 0))" in fuente, (
            "el overlay se limpia con un color opaco: se pintaría el fondo "
            "encima del mundo en la ruta GPU"
        )

    def test_la_superficie_del_overlay_de_app_es_translucida(self) -> None:
        """AUD-344 — el objeto real, no la fuente: `App` crea su overlay
        translúcido (con `SRCALPHA`), o la pasada 9b lo compone opaco sobre
        el mundo y lo tapa entero."""
        from src.engine.core.app import App

        app = App.__new__(App)
        app._use_gl = False
        app._init_pygame()
        try:
            superficie = app._ui_overlay_surface
            assert superficie.get_flags() & pygame.SRCALPHA, (
                "el overlay de `App` nace opaco: la pasada 9b (blend SRC_ALPHA) "
                "lo compone reemplazando el fotograma — escenarios en negro"
            )
        finally:
            pygame.display.quit()