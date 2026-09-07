"""
Module: test_el_interior_se_declara
System: tests
Description: AUD-822 (P19) — `interior` y `cielo` son independientes. El
interior se DECLARA (`interior=true`); la ausencia de `cielo` ya no
convierte al mapa en interior ni apaga su día, su clima y su luna.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pygame

from src.framework.scenes.stage_parts.simulacion import SimulacionDeEscenario
from src.framework.stage.stage_data import StageData
from src.framework.stage.stage_loader import StageLoader

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "minimal_stage.tmx"


def _escena(interior: bool, cielo: bool, zonas=()) -> SimulacionDeEscenario:
    escena = SimulacionDeEscenario()
    datos = StageData(map_layer=None)  # type: ignore[arg-type]
    datos.interior = interior
    datos.cielo = cielo
    datos.indoor_zones = list(zonas)
    escena._stage_data = datos  # type: ignore[attr-defined]
    escena._player = SimpleNamespace(rect=pygame.Rect(100, 100, 20, 32))  # type: ignore[attr-defined]
    return escena


class TestElInteriorSeDeclara:
    def test_sin_cielo_y_sin_interior_es_exterior(self) -> None:
        """P19 — el caso de los 30 mapas: sin `cielo` y sin `interior`,
        a cielo abierto. Antes daba interior global."""
        assert _escena(interior=False, cielo=False)._es_indoor() is False

    def test_exterior_con_cielo_sigue_exterior(self) -> None:
        assert _escena(interior=False, cielo=True)._es_indoor() is False

    def test_interior_declarado_sin_zonas_es_interior(self) -> None:
        assert _escena(interior=True, cielo=False)._es_indoor() is True

    def test_interior_declarado_con_cielo_es_interior(self) -> None:
        """`cielo` dibuja; no vota sobre el techo."""
        assert _escena(interior=True, cielo=True)._es_indoor() is True

    def test_con_zonas_manda_el_rect(self) -> None:
        zona = pygame.Rect(0, 0, 50, 50)
        dentro = _escena(interior=False, cielo=False, zonas=[zona])
        assert dentro._es_indoor() is False
        dentro._player = SimpleNamespace(rect=pygame.Rect(10, 10, 20, 32))
        assert dentro._es_indoor() is True

    def test_el_cargador_nace_exterior_por_defecto(self) -> None:
        datos = StageLoader.load(FIXTURE)
        assert datos.interior is False
        assert datos.cielo is False
