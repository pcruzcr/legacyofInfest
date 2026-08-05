"""AUD-281 — recoger algo no producía nada.

El defecto
----------
`INTERACT_ITEM_PICKED` llegaba a `senales.py` y su manejador **sólo sumaba al
inventario**. Ni partículas, ni sonido, ni un parpadeo en la interfaz. Todo lo
demás del juego responde —el golpe tiene chispas, sacudida y hit-stop; el daño
tiene números flotantes; el parry tiene destello— y la acción que más veces se
repite en una partida no tenía nada.

Y encima el evento viajaba **sin posición**, así que ni siquiera se podía
poner: quien lo escuchaba no sabía dónde había pasado.

Qué se fija
-----------
1. Que el evento lleve `pos` — sin eso no hay nada que hacer.
2. Que el manejador emita partículas y sonido donde ocurrió.
3. Que el contador de monedas rebote, y que «movimiento reducido» lo apague.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.framework.stage.interactable_system import EVENTO_RECOGIDO, InteractableSystem
from src.framework.stage.interactables import Recogible


class TestElEventoLlevaDonde:
    def test_recoger_emite_la_posicion(self) -> None:
        bus = EventBus()
        recibido: list[dict] = []
        handler = recibido.append

        def anotar(**data):
            handler(data)

        bus.subscribe(EVENTO_RECOGIDO, anotar)

        sistema = InteractableSystem(bus=bus)
        sistema.recogibles.append(
            Recogible(rect=pygame.Rect(100, 200, 16, 16), item_id="coin",
                      automatico=True),
        )
        sistema.update(0.016, pygame.Rect(100, 200, 16, 16), usar=False)
        bus.dispatch()

        assert recibido, "recoger no emitió el evento"
        assert recibido[0].get("pos") == (108, 208), (
            "el evento de recogida viaja sin posición: sin ella no hay ni "
            "partículas ni sonido panoramizado"
        )


class TestElRebotdeDelContador:
    @pytest.fixture(autouse=True)
    def _video(self):
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))

    @pytest.fixture
    def hud(self):
        from src.engine.ui.hud import HUD

        return HUD(event_bus=EventBus())

    def test_el_pulso_arranca_y_se_agota(self, hud) -> None:
        hud.pulso_de_recogida()
        assert hud._pulso_timer > 0.0
        hud.update(1.0)
        assert hud._pulso_timer == 0.0, "el rebote se quedó encendido"

    def test_movimiento_reducido_lo_apaga(self, hud, monkeypatch) -> None:
        """Es adorno, y la opción existe para quitar el adorno que se mueve.

        Aquí sí se puede anular del todo, al contrario que la estela del dash:
        el número ya dice lo que pasó.
        """
        from src.engine.core import user_settings

        monkeypatch.setattr(
            user_settings, "preferencia",
            lambda clave, defecto=None: True if clave == "reduced_motion" else defecto,
        )
        hud.pulso_de_recogida()
        assert hud._pulso_timer == 0.0

    def test_dibujar_con_el_pulso_activo_no_rompe(self, hud) -> None:
        """El escalado va sobre una superficie de texto recién renderizada; un
        cero en el ancho reventaría `smoothscale`."""
        superficie = pygame.Surface((800, 600))
        hud.set_score(0, 0)
        hud.pulso_de_recogida()
        hud._draw_score(superficie)


class TestElCableadoDeLaEscena:
    """Que el manejador exista no basta: hay que ver que emite."""

    @pytest.fixture(autouse=True)
    def _video(self):
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))

    @pytest.fixture
    def escena(self):
        from src.engine.audio.audio_manager import AudioManager
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
        yield escena
        escena.on_exit()

    def test_recoger_emite_particulas(self, escena) -> None:
        emisor = escena._particle_system.get_emitter("pickup")
        antes = emisor.count
        escena.context.event_bus.emit(
            EVENTO_RECOGIDO, item_id="coin", cantidad=1, pos=(120, 300),
        )
        escena.context.event_bus.dispatch()
        assert emisor.count > antes, (
            "recoger no emitió una sola partícula: el manejador sigue siendo "
            "sólo contabilidad de inventario"
        )

    def test_recoger_sin_posicion_no_revienta(self, escena) -> None:
        """Un emisor antiguo puede no mandar `pos`; sumar al inventario tiene
        que seguir funcionando igual."""
        escena.context.event_bus.emit(EVENTO_RECOGIDO, item_id="coin", cantidad=1)
        escena.context.event_bus.dispatch()

    def test_recoger_rebota_el_contador(self, escena) -> None:
        escena._hud._pulso_timer = 0.0
        escena.context.event_bus.emit(
            EVENTO_RECOGIDO, item_id="coin", cantidad=1, pos=(120, 300),
        )
        escena.context.event_bus.dispatch()
        assert escena._hud._pulso_timer > 0.0
