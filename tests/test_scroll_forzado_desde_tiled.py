"""Un alumno puede hacer un nivel de persecución desde Tiled — AUD-249.

El hueco (GAP-032, la primera de las cinco)
===========================================
`ScrollForzado` estaba escrita entera y probada: velocidad, margen de gracia,
parada opcional, y un `se_quedo_atras()` con su docstring explicando por qué el
borde **mata** en vez de empujar. `StageScene.__init__` la construía en la
línea 167 y **ese era su único uso en todo el repositorio**: ni `arrancar()`,
ni `update()`, ni `se_quedo_atras()`.

Es decir: la cámara nunca se movía sola y ese borde no mataba a nadie.

Por qué importa aquí más que en otro repositorio
------------------------------------------------
Los niveles los hacen los alumnos, desde Tiled, y cada uno trae su propia
idea. Una mecánica a la que sólo se llega escribiendo Python **no está
disponible** para quien diseña un nivel: da igual que el código exista. La
persecución es un arquetipo entero —SMB3 Airship, Cuphead, Ori, la Wall of
Flesh— y estaba fuera de su alcance.

Lo que estas pruebas fijan es el circuito completo, no las piezas:

    objeto `ScrollZone` en el TMX  →  StageLoader._handle_scroll_forzado
    →  StageData.scroll_forzados  →  HazardSystem.update(..., camara)
    →  arrancar()  →  update() mueve la cámara  →  se_quedo_atras() mata

`ScrollZone` es un tipo **nuevo**: ningún mapa existente lo declara, así que
ninguna de las 26 entregas cambia. Eso es el control de la última clase.
"""
from __future__ import annotations

import types
from unittest.mock import MagicMock

import pygame
import pytest

from src.framework.stage.level_mechanics import ScrollForzado


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class _Camara:
    """Lo mínimo que `ScrollForzado` toca de una cámara: su `offset`."""

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.offset = pygame.Vector2(x, y)


def _sistema():
    """`HazardSystem` con un contexto simulado que registra la muerte."""
    from src.framework.stage.hazard_system import HazardSystem

    bus = MagicMock()
    bus.subscribe = MagicMock()
    contexto = types.SimpleNamespace(
        event_bus=bus,
        scene_manager=types.SimpleNamespace(push=MagicMock(), current=None),
    )
    return HazardSystem(contexto)


def _escenario(scroll: ScrollForzado | None = None):
    """`StageData` vacío salvo por lo que esta prueba usa."""
    stage = types.SimpleNamespace(
        message_triggers=[], hazard_zones=[], death_pits=[],
        scroll_forzados=[scroll] if scroll is not None else [],
    )
    return stage


def _jugador(x: float, ancho: int = 20):
    return types.SimpleNamespace(rect=pygame.Rect(int(x), 100, ancho, 32))


class TestSeDeclaraDesdeTiled:
    def test_scroll_zone_es_un_tipo_valido(self) -> None:
        from src.framework.stage.tmx_diagnostics import BUILTIN_OBJECT_TYPES

        assert "ScrollZone" in BUILTIN_OBJECT_TYPES, (
            "sin estar en el catálogo, el validador de TMX marcaría el objeto "
            "como desconocido y el alumno no sabría que existe"
        )

    def test_el_cargador_lo_construye(self) -> None:
        from src.framework.stage.stage_loader import StageLoader

        # `StageData` real pide un `map_layer`; el manejador sólo toca la
        # lista, y montar un mapa entero no probaría nada más.
        stage = types.SimpleNamespace(scroll_forzados=[])
        obj = types.SimpleNamespace(x=100, y=50, width=32, height=64, name="")

        StageLoader._handle_scroll_forzado(stage, obj, {})

        assert len(stage.scroll_forzados) == 1
        scroll = stage.scroll_forzados[0]
        assert scroll.disparador == pygame.Rect(100, 50, 32, 64)
        assert scroll.velocidad.x == pytest.approx(40.0)

    def test_las_propiedades_del_mapa_mandan(self) -> None:
        from src.framework.stage.stage_loader import StageLoader

        # `StageData` real pide un `map_layer`; el manejador sólo toca la
        # lista, y montar un mapa entero no probaría nada más.
        stage = types.SimpleNamespace(scroll_forzados=[])
        obj = types.SimpleNamespace(x=0, y=0, width=16, height=16, name="")

        StageLoader._handle_scroll_forzado(stage, obj, {
            "velocidad_x": 90.0, "velocidad_y": -10.0,
            "margen_de_gracia": 8.0, "parar_en_x": 640.0,
        })

        scroll = stage.scroll_forzados[0]
        assert scroll.velocidad.x == pytest.approx(90.0)
        assert scroll.velocidad.y == pytest.approx(-10.0)
        assert scroll.margen_de_gracia == pytest.approx(8.0)
        assert scroll.parar_en_x == pytest.approx(640.0)

    def test_sin_parar_en_x_corre_hasta_el_final(self) -> None:
        from src.framework.stage.stage_loader import StageLoader

        # `StageData` real pide un `map_layer`; el manejador sólo toca la
        # lista, y montar un mapa entero no probaría nada más.
        stage = types.SimpleNamespace(scroll_forzados=[])
        obj = types.SimpleNamespace(x=0, y=0, width=16, height=16, name="")

        StageLoader._handle_scroll_forzado(stage, obj, {})

        assert stage.scroll_forzados[0].parar_en_x is None


class TestElCircuitoCompleto:
    def test_pisar_el_disparador_lo_enciende(self) -> None:
        scroll = ScrollForzado(disparador=pygame.Rect(200, 90, 32, 64))
        sistema, stage, camara = _sistema(), _escenario(scroll), _Camara()

        sistema.update(1 / 60, _jugador(x=205), stage, camara)

        assert scroll.activo is True, (
            "la cámara nunca arrancaba: `arrancar()` no tenía llamante"
        )

    def test_lejos_del_disparador_no_pasa_nada(self) -> None:
        scroll = ScrollForzado(disparador=pygame.Rect(200, 90, 32, 64))
        sistema, stage, camara = _sistema(), _escenario(scroll), _Camara()

        sistema.update(1 / 60, _jugador(x=0), stage, camara)

        assert scroll.activo is False
        assert camara.offset.x == pytest.approx(0.0)

    def test_una_vez_activo_la_camara_avanza_sola(self) -> None:
        scroll = ScrollForzado(
            velocidad=pygame.Vector2(60.0, 0.0),
            disparador=pygame.Rect(0, 90, 32, 64),
        )
        sistema, stage, camara = _sistema(), _escenario(scroll), _Camara()

        for _ in range(60):
            sistema.update(1 / 60, _jugador(x=10), stage, camara)

        assert camara.offset.x > 50.0, (
            f"la cámara avanzó {camara.offset.x:.0f} px en un segundo a 60 px/s"
        )

    def test_quedarse_atras_mata(self) -> None:
        """La promesa del docstring: «el nivel dijo sígueme y no lo seguiste»."""
        scroll = ScrollForzado(
            velocidad=pygame.Vector2(300.0, 0.0), margen_de_gracia=24.0,
            disparador=pygame.Rect(0, 90, 32, 64),
        )
        sistema, stage, camara = _sistema(), _escenario(scroll), _Camara()

        sistema.update(1 / 60, _jugador(x=10), stage, camara)  # arranca
        for _ in range(60):
            sistema.update(1 / 60, _jugador(x=10), stage, camara)  # no se mueve

        assert sistema._pending_death is True, (
            "el borde alcanzó al jugador y no pasó nada: `se_quedo_atras()` "
            "seguía sin llamante"
        )

    def test_seguir_el_ritmo_no_mata(self) -> None:
        """El control de la anterior: quien sigue a la cámara vive."""
        scroll = ScrollForzado(
            velocidad=pygame.Vector2(60.0, 0.0),
            disparador=pygame.Rect(0, 90, 32, 64),
        )
        sistema, stage, camara = _sistema(), _escenario(scroll), _Camara()

        for paso in range(120):
            # El jugador va justo por delante del borde.
            sistema.update(1 / 60, _jugador(x=camara.offset.x + 80), stage, camara)
            assert sistema._pending_death is False, f"murió en el paso {paso}"

    def test_parar_en_x_detiene_la_camara(self) -> None:
        scroll = ScrollForzado(
            velocidad=pygame.Vector2(300.0, 0.0), parar_en_x=100.0,
            disparador=pygame.Rect(0, 90, 32, 64),
        )
        sistema, stage, camara = _sistema(), _escenario(scroll), _Camara()

        sistema.update(1 / 60, _jugador(x=10), stage, camara)  # pisa y arranca
        for _ in range(120):
            sistema.update(1 / 60, _jugador(x=camara.offset.x + 80), stage, camara)

        assert camara.offset.x == pytest.approx(100.0)
        assert scroll.activo is False


class TestLoQueNoCambia:
    """Los controles. `ScrollZone` es aditivo: nada existente se entera."""

    def test_un_escenario_sin_scroll_zone_no_cambia(self) -> None:
        sistema, stage, camara = _sistema(), _escenario(), _Camara()

        sistema.update(1 / 60, _jugador(x=10), stage, camara)

        assert camara.offset.x == pytest.approx(0.0)
        assert sistema._pending_death is False

    def test_la_firma_antigua_sigue_funcionando(self) -> None:
        """Una entrega que llame a `update()` sin cámara no puede romperse.

        Se queda sin la mecánica que no estaba usando, y nada más.
        """
        scroll = ScrollForzado(disparador=pygame.Rect(0, 90, 32, 64))
        sistema, stage = _sistema(), _escenario(scroll)

        sistema.update(1 / 60, _jugador(x=10), stage)

        assert scroll.activo is False

    #: El laboratorio del profesor no es una entrega: es el mapa donde se
    #: coloca a propósito todo lo que el motor sabe hacer (AUD-153). Que
    #: `ScrollZone` esté ahí es lo contrario de un problema — mientras no
    #: estuvo, la mecánica era inalcanzable jugando y AUD-258 lo cerró.
    _DEL_PROFESOR = {"stage_mecanicas.tmx"}

    def test_ningun_mapa_entregado_lo_declara(self) -> None:
        """Si algún TMX de estudiante usara el nombre, esto no sería aditivo.

        La garantía que importa es sobre las **entregas**: un tipo que ninguna
        de ellas declara no puede cambiar ningún nivel ya calificado, que es
        lo que exige la invariante 2 de `CLAUDE.md`.
        """
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent
        con_scroll = [
            p.name for p in (raiz / "assets" / "maps").rglob("*.tmx")
            if p.name not in self._DEL_PROFESOR
            and "ScrollZone" in p.read_text(encoding="utf-8", errors="replace")
        ]
        assert not con_scroll, f"ya lo usaban: {con_scroll}"
