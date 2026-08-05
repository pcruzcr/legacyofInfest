"""AUD-287 — no había forma de teletransportar dentro de un mapa.

El hueco
--------
De los 68 tipos de objeto TMX, ninguno movía al jugador dentro del mismo mapa.
`NextTrigger` cambia de escenario y `Door` abre un paso; conectar dos extremos
de un nivel grande no se podía declarar de ninguna manera, así que un mapa de
5.000 px obligaba a recorrerlo entero cada vez.

Las tres decisiones que hay que defender
----------------------------------------
1. **El sistema no mueve al jugador: emite adónde debería ir.** Mover un
   rectángulo que `InteractableSystem` no posee es el atajo que deja al jugador
   dentro de una pared sin que nadie sepa quién lo puso ahí.
2. **Sin destino no se carga.** Un warp con destino implícito manda a la esquina
   del mapa, y eso se lee como un fallo del motor, no como un mapa a medio
   configurar.
3. **Enfriamiento.** Un destino que cae dentro de otra zona de warp —o dentro de
   sí misma, el error de colocación más fácil en Tiled— produce un bucle a 60
   fps, que no es un fallo visible sino una pantalla epiléptica.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.framework.stage.interactable_system import EVENTO_WARP, InteractableSystem
from src.framework.stage.interactables import ZonaDeWarp


def _sistema(bus, **kwargs):
    warp = ZonaDeWarp(
        rect=pygame.Rect(100, 100, 32, 32),
        destino=pygame.Vector2(900, 400),
        **kwargs,
    )
    return InteractableSystem(bus=bus, warps=[warp]), warp


def _escuchar(bus):
    recibido: list[dict] = []

    def anotar(**data):
        recibido.append(data)

    bus.subscribe(EVENTO_WARP, anotar)
    # El bus guarda referencias débiles: sin devolver el manejador, el
    # recolector se lo lleva y la prueba pasa por la razón equivocada.
    return recibido, anotar


class TestCruzar:
    def test_pisar_la_zona_emite_el_destino(self) -> None:
        bus = EventBus()
        recibido, _h = _escuchar(bus)
        sistema, _ = _sistema(bus)

        sistema.update(0.016, pygame.Rect(100, 100, 16, 16))
        bus.dispatch()

        assert recibido, "pisar la zona de warp no emitió nada"
        assert recibido[0]["destino"] == (900.0, 400.0)

    def test_estar_fuera_no_hace_nada(self) -> None:
        bus = EventBus()
        recibido, _h = _escuchar(bus)
        sistema, _ = _sistema(bus)

        sistema.update(0.016, pygame.Rect(500, 500, 16, 16))
        bus.dispatch()
        assert not recibido

    def test_el_manual_pide_el_boton(self) -> None:
        bus = EventBus()
        recibido, _h = _escuchar(bus)
        sistema, _ = _sistema(bus, automatico=False)

        sistema.update(0.016, pygame.Rect(100, 100, 16, 16), usar=False)
        bus.dispatch()
        assert not recibido

        sistema.update(0.016, pygame.Rect(100, 100, 16, 16), usar=True)
        bus.dispatch()
        assert recibido

    def test_una_llave_que_no_se_tiene_lo_bloquea(self) -> None:
        bus = EventBus()
        recibido, _h = _escuchar(bus)
        sistema, _ = _sistema(bus, key_id="llave_azul")

        sistema.update(0.016, pygame.Rect(100, 100, 16, 16))
        bus.dispatch()
        assert not recibido

        sistema.llavero.coger("llave_azul")
        sistema.update(0.016, pygame.Rect(100, 100, 16, 16))
        bus.dispatch()
        assert recibido


class TestElEnfriamiento:
    def test_no_se_dispara_dos_veces_seguidas(self) -> None:
        """El bucle: el jugador aparece dentro del disparador, salta, aparece.
        A 60 fps eso es una pantalla epiléptica, no un fallo visible."""
        bus = EventBus()
        recibido, _h = _escuchar(bus)
        sistema, _ = _sistema(bus)

        for _ in range(10):
            sistema.update(0.016, pygame.Rect(100, 100, 16, 16))
        bus.dispatch()
        assert len(recibido) == 1, f"se disparó {len(recibido)} veces en 10 fotogramas"

    def test_pasado_el_enfriamiento_vuelve_a_valer(self) -> None:
        bus = EventBus()
        recibido, _h = _escuchar(bus)
        sistema, _ = _sistema(bus, enfriamiento=0.1)

        sistema.update(0.016, pygame.Rect(100, 100, 16, 16))
        for _ in range(10):
            sistema.update(0.016, pygame.Rect(100, 100, 16, 16))
        bus.dispatch()
        assert len(recibido) == 2

    def test_una_vez_es_una_vez(self) -> None:
        bus = EventBus()
        recibido, _h = _escuchar(bus)
        sistema, _ = _sistema(bus, una_vez=True, enfriamiento=0.01)

        for _ in range(30):
            sistema.update(0.016, pygame.Rect(100, 100, 16, 16))
        bus.dispatch()
        assert len(recibido) == 1


class TestDesdeElMapa:
    """El tipo tiene que existir para Tiled y para el validador."""

    def test_warpzone_es_un_tipo_conocido(self) -> None:
        from src.framework.stage.tmx_diagnostics import known_object_types

        assert "WarpZone" in known_object_types([])

    def test_el_cargador_lo_lee(self, tmp_path) -> None:
        from src.framework.stage.stage_loader import StageData, StageLoader

        class _Obj:
            id, name, x, y, width, height = 1, "salida", 64.0, 96.0, 32.0, 32.0

        stage = StageData(map_layer=None)
        StageLoader._handle_warp(stage, _Obj(), {
            "destino_x": 900, "destino_y": 400, "mensaje": "Al patio",
        })
        assert len(stage.warps) == 1
        assert stage.warps[0].destino == pygame.Vector2(900, 400)
        assert stage.warps[0].mensaje == "Al patio"

    def test_sin_destino_no_se_carga(self, caplog) -> None:
        """Un destino implícito manda a la esquina del mapa y se lee como un
        fallo del motor."""
        from src.framework.stage.stage_loader import StageData, StageLoader

        class _Obj:
            id, name, x, y, width, height = 1, "roto", 64.0, 96.0, 32.0, 32.0

        stage = StageData(map_layer=None)
        StageLoader._handle_warp(stage, _Obj(), {})
        assert stage.warps == []


class TestLoQueHaceLaEscena:
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

    def test_mueve_al_jugador_a_los_pies_del_destino(self, escena) -> None:
        escena.context.event_bus.emit(EVENTO_WARP, destino=(700.0, 400.0),
                                      origen=(100, 100))
        escena.context.event_bus.dispatch()
        assert escena._player.rect.midbottom == (700, 400)

    def test_le_corta_la_velocidad(self, escena) -> None:
        """Llegar cayendo a 500 px/s atraviesa el suelo antes de que la
        colisión pueda resolverlo."""
        escena._player.velocity.update(0.0, 500.0)
        escena.context.event_bus.emit(EVENTO_WARP, destino=(700.0, 400.0),
                                      origen=(100, 100))
        escena.context.event_bus.dispatch()
        assert escena._player.velocity.length() == 0.0

    def test_la_camara_salta_en_vez_de_barrer(self, escena) -> None:
        """Con el LERP normal, un warp largo produce medio segundo de barrido a
        toda velocidad por el nivel."""
        escena._camera.offset.update(0.0, 0.0)
        escena.context.event_bus.emit(EVENTO_WARP, destino=(1400.0, 400.0),
                                      origen=(100, 100))
        escena.context.event_bus.dispatch()
        assert escena._camera.offset.x > 0.0
