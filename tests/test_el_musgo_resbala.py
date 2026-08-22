"""AUD-522 — el musgo resbala (`inercia`), el lodo frena (`multiplicador`,
sin cambios). Antes las dos superficies eran el mismo freno con distinta
intensidad (0,94 contra 0,88) y en una partida real no se distinguían de
nada — jugado, el dueño lo dijo sin rodeos: *«el musgo resbala como la
nieve, el lodo es el que frena»*.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.framework.ecs.components import Transform, Velocidad, ZonaDeFriccion
from src.framework.ecs.systems import sistema_friccion
from src.framework.ecs.world import World
from src.framework.entities.player import Player
from src.framework.entities.states import WalkingState
from src.framework.physics.perfil import MATERIALES


@pytest.fixture(scope="module")
def _video() -> None:
    pygame.init()


class TestLaInerciaEsSeguraPorConstruccion:
    """AUD-236 advirtió que `multiplicador > 1` «se dispara sin tope».
    `inercia` tiene que resolver lo mismo (resbalar de verdad) sin ese
    riesgo — nunca se aleja del objetivo, sólo tarda en llegar."""

    def _mundo_con_zona(self, inercia: float) -> tuple[World, int, Velocidad]:
        m = World()
        m.crear(ZonaDeFriccion(pygame.Rect(0, 0, 500, 50), inercia=inercia))
        e = m.crear(
            Transform(pygame.Vector2(10, 10), pygame.Rect(10, 10, 8, 8)),
            Velocidad(pygame.Vector2(0, 0)),
        )
        return m, e, m.obtener(e, Velocidad)

    def test_con_tecla_sostenida_no_se_aleja_del_objetivo(self, _video) -> None:
        m, _e, v = self._mundo_con_zona(0.15)
        for _ in range(120):
            v.v.x = 90.0  # el jugador sigue pulsando
            sistema_friccion(m, 1 / 60)
        assert v.v.x == pytest.approx(90.0)

    def test_al_soltar_decae_sin_pasarse_ni_invertirse(self, _video) -> None:
        m, _e, v = self._mundo_con_zona(0.15)
        for _ in range(30):
            v.v.x = 90.0
            sistema_friccion(m, 1 / 60)
        anterior = v.v.x
        for _ in range(180):  # 3 s sueltos
            v.v.x = 0.0
            sistema_friccion(m, 1 / 60)
            actual = v.v.x
            assert 0.0 <= actual <= anterior + 1e-6, (
                "la velocidad no debe crecer ni volverse negativa al soltar "
                "la tecla en una zona resbaladiza"
            )
            anterior = actual
        assert v.v.x < 1.0, "a los 3 s debería haber frenado casi del todo"

    def test_inercia_cero_no_cambia_nada(self, _video) -> None:
        """El valor por defecto (0.0) dice «sin inercia» — ningún mapa
        entregado debe notar la diferencia."""
        m, _e, v = self._mundo_con_zona(0.0)
        v.v.x = 90.0
        sistema_friccion(m, 1 / 60)
        assert v.v.x == 90.0

    def test_entidades_que_ya_no_tocan_la_zona_dejan_de_resbalar(self, _video) -> None:
        """Sin esto, volver a entrar mucho después reanudaría desde la
        velocidad con la que se salió, no desde la de ahora."""
        m = World()
        zona = ZonaDeFriccion(pygame.Rect(0, 0, 50, 50), inercia=0.15)
        m.crear(zona)
        e = m.crear(
            Transform(pygame.Vector2(10, 10), pygame.Rect(10, 10, 8, 8)),
            Velocidad(pygame.Vector2(90, 0)),
        )
        sistema_friccion(m, 1 / 60)
        assert e in zona._vx_mezclada

        # Sale de la zona.
        t = m.obtener(e, Transform)
        t.posicion.x = 1000.0
        t.rect.x = 1000
        sistema_friccion(m, 1 / 60)
        assert e not in zona._vx_mezclada


class TestElMultiplicadorSigueIgual:
    """El lodo (y cualquier otra `FrictionZone` existente) no debe notar
    que `inercia` existe."""

    def test_multiplicador_se_aplica_igual_que_antes(self, _video) -> None:
        m = World()
        m.crear(ZonaDeFriccion(pygame.Rect(0, 0, 200, 50), multiplicador=0.88))
        e = m.crear(
            Transform(pygame.Vector2(10, 10), pygame.Rect(10, 10, 8, 8)),
            Velocidad(pygame.Vector2(90, 0)),
        )
        sistema_friccion(m, 1 / 60)
        assert m.obtener(e, Velocidad).v.x == pytest.approx(79.2)


class TestLaPisadaDelMusgo:
    """AUD-522 — el musgo resbala y hasta ahora no se oía ni se veía."""

    def test_sin_material_de_zona_suena_la_pisada_normal(self, _video) -> None:
        bus = EventBus()
        vistos: list[str] = []
        # AUD-522 — `EventBus.subscribe` guarda una referencia **débil**
        # (docstring de `event_bus.py`): una lambda pasada directamente se
        # recolecta antes del siguiente `dispatch()` y la suscripción se
        # cae en silencio. Hay que quedarse con el callback en una
        # variable, y `emit()` encola — hace falta `dispatch()` para que
        # de verdad se llame.
        def _al_normal(**_data: object) -> None:
            vistos.append("normal")

        def _al_musgo(**_data: object) -> None:
            vistos.append("musgo")

        bus.subscribe(Events.SFX_PLAYER_FOOTSTEP, _al_normal)
        bus.subscribe(Events.SFX_PLAYER_FOOTSTEP_MUSGO, _al_musgo)

        player = Player(pygame.Vector2(0, 0), event_bus=bus)
        player.is_grounded = True
        estado = WalkingState()
        player._change_state_instance(estado)
        for _ in range(30):  # más de 0,35 s a 60 fps
            estado.update(player, 1 / 60, None)
        bus.dispatch()

        assert vistos == ["normal"]

    def test_sobre_musgo_suena_y_se_ve_la_pisada_propia(self, _video) -> None:
        bus = EventBus()
        sonidos: list[str] = []
        vfx: list[dict] = []

        def _al_normal(**_data: object) -> None:
            sonidos.append("normal")

        def _al_musgo(**_data: object) -> None:
            sonidos.append("musgo")

        def _al_vfx(**data: object) -> None:
            vfx.append(data)

        bus.subscribe(Events.SFX_PLAYER_FOOTSTEP, _al_normal)
        bus.subscribe(Events.SFX_PLAYER_FOOTSTEP_MUSGO, _al_musgo)
        bus.subscribe(Events.VFX_MUSGO_STEP, _al_vfx)

        player = Player(pygame.Vector2(5, 7), event_bus=bus)
        player.is_grounded = True
        player._material_de_zona = MATERIALES["musgo"]
        estado = WalkingState()
        player._change_state_instance(estado)
        for _ in range(30):
            estado.update(player, 1 / 60, None)
        bus.dispatch()

        assert sonidos == ["musgo"]
        assert len(vfx) == 1
        assert vfx[0]["pos"] == (5, 7)


class TestElTmxDeclaraElMaterial:
    def test_las_zonas_de_musgo_declaran_material(self) -> None:
        from pathlib import Path

        xml = Path("assets/maps/stage4_1/stage4_1.tmx").read_text(encoding="utf-8")
        # Cada zona con `inercia` (musgo) tiene que traer también
        # `material="musgo"` -- si no, `Transform.material_actual` se
        # queda en "roca" y la pisada/partícula propias nunca se activan
        # de verdad, aunque la física sí resbale.
        bloques = xml.split("<object ")[1:]
        con_inercia = [b for b in bloques if 'name="inercia"' in b]
        # AUD-595 — la cuarta zona es el repiso de la Fase 2 (AUD-580): su
        # bajada aterriza directo en musgo, y trae su `material` como las
        # tres originales.
        assert len(con_inercia) == 4
        for bloque in con_inercia:
            assert 'name="material" value="musgo"' in bloque
