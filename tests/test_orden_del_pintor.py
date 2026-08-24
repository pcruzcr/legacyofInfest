"""AUD-339 — 2.5D fase 6: orden por Y del pintor (opcional) y curva.

AUD-067 ordenó las entidades por `rect.centery` y eso nunca cambió, pero el
2.5D de AUD-277 **escala** por los pies (`rect.bottom`): dos anclas distintas
para la misma profundidad. Con la propiedad de mapa `orden_por_y = true`, la
ordenación usa la misma ancla que la escala — `depth_y` si la entidad la
declara (un volador se ordena por su proyección en el suelo), si no sus pies.

La otra mitad es `profundidad_curva`: la escala era lineal, y una perspectiva
de verdad comprime el horizonte. Con 1.0 (por defecto) la fórmula es la de
AUD-277 exactamente.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.profundidad import EscalaPorProfundidad


@pytest.fixture(scope="module", autouse=True)
def _pygame_listo(_pygame_init):
    # Sin `pygame.quit()` al terminar: la suite comparte sesión de pygame, y
    # apagar el módulo de fuentes invalida las fuentes cacheadas de otras
    # pruebas (los números de daño guardan `pygame.font.Font` en una caché).
    yield


class _Dibujable:
    """Entidad falsa que registra el orden en que la pintan."""

    def __init__(self, rect, etiqueta: str, orden: list[str],
                 depth_y: int | None = None) -> None:
        self.rect = pygame.Rect(rect)
        self._orden = orden
        self._etiqueta = etiqueta
        self.depth_y = depth_y
        self.is_visible = True
        self.is_alive = True

    def draw(self, surface, offset) -> None:
        self._orden.append(self._etiqueta)


def _pintar(entidades, *, orden_por_y: bool = False) -> list[str]:
    from src.framework.stage.drawing_system import DrawingSystem

    orden: list[str] = []
    for e in entidades:
        e._orden = orden
    escenario = type("E", (), {
        "entity_list": list(entidades),
        "orden_por_y": orden_por_y,
        "collision_rects": [],
        "map_pixel_size": (3200, 600),
        "profundidad_min": 1.0,
        "profundidad_max": 1.0,
    })()
    sistema = DrawingSystem()
    sistema._draw_entities(
        pygame.Surface((320, 240)), escenario,
        None, [], pygame.Vector2(0, 0),
    )
    return orden


class TestElOrdenDelPintor:
    def test_por_defecto_se_ordena_por_el_centro(self) -> None:
        """AUD-067 intacto: sin la propiedad, la clave es `rect.centery`."""
        alto = _Dibujable((0, 0, 32, 200), "alto", [])      # centro 100
        bajo = _Dibujable((0, 150, 32, 20), "bajo", [])     # centro 160
        assert _pintar([alto, bajo]) == ["alto", "bajo"], (
            "sin la propiedad no se conserva el orden por centro de AUD-067"
        )

    def test_con_la_propiedad_se_ordena_por_los_pies(self) -> None:
        """Con `orden_por_y` manda la misma ancla que escala: los pies.

        El alto (centro 100) tiene los pies en 200; el bajo (centro 160) los
        tiene en 170. Por centro, el alto va primero; por pies, el bajo va
        primero — el de pies más abajo se pinta encima.
        """
        alto = _Dibujable((0, 0, 32, 200), "alto", [])      # pies 200
        bajo = _Dibujable((0, 150, 32, 20), "bajo", [])     # pies 170
        assert _pintar([alto, bajo], orden_por_y=True) == ["bajo", "alto"]

    def test_depth_y_ancla_a_un_volador(self) -> None:
        """Un volador se ordena por su proyección en el suelo, no por su centro.

        El volador cuelga arriba del todo (centro 16, pies 32) pero declara
        que su posición para el pintor está en 220: por debajo del caminante
        (pies 212), así que se pinta encima de él.
        """
        caminante = _Dibujable((0, 180, 32, 32), "caminante", [])
        volador = _Dibujable((0, 0, 32, 32), "volador", [], depth_y=220)
        assert _pintar([caminante, volador], orden_por_y=True) == [
            "caminante", "volador",
        ], "el volador debería tapar al que está bajo su proyección"

    def test_una_entidad_sin_rect_no_rompe_el_orden(self) -> None:
        from src.framework.stage.drawing_system import _ancla_de_profundidad

        sin_rect = type("X", (), {"depth_y": None})()
        assert _ancla_de_profundidad(sin_rect) == 0


class TestLaCurva:
    def test_por_defecto_es_la_lineal_de_aud_277(self) -> None:
        e = EscalaPorProfundidad(mapa_alto=1000, minimo=0.5, maximo=1.0)
        assert e.escala_en(0) == pytest.approx(0.5)
        assert e.escala_en(250) == pytest.approx(0.625)
        assert e.escala_en(500) == pytest.approx(0.75)
        assert e.escala_en(1000) == pytest.approx(1.0)

    def test_con_curva_el_fondo_se_comprime(self) -> None:
        """Curva 2: la mitad del mapa ya recorrió las 3/4 partes de la escala."""
        e = EscalaPorProfundidad(mapa_alto=1000, minimo=0.5, maximo=1.0,
                                 curva=2.0)
        assert e.escala_en(0) == pytest.approx(0.5)
        assert e.escala_en(500) == pytest.approx(0.625)      # 0.5 + 0.5·0.25
        assert e.escala_en(1000) == pytest.approx(1.0)

    def test_la_curva_no_invierte_el_degradado(self) -> None:
        """Curva negativa o cero se sujetan: invertiría el degradado."""
        e = EscalaPorProfundidad(mapa_alto=1000, minimo=0.5, maximo=1.0,
                                 curva=-3.0)
        assert e.escala_en(500) >= e.escala_en(0)
        assert e.escala_en(500) <= e.escala_en(1000)

    def test_con_curva_sigue_creciendo_hacia_abajo(self) -> None:
        e = EscalaPorProfundidad(mapa_alto=1000, minimo=0.5, maximo=1.0,
                                 curva=2.0)
        valores = [e.escala_en(y) for y in range(0, 1001, 100)]
        assert valores == sorted(valores)


class TestElMapaLasDeclara:
    def test_el_mapa_de_referencia_las_demuestra(self) -> None:
        """stage0 declara las dos, para que el estudiante las vea en Tiled."""
        import xml.etree.ElementTree as ET
        from pathlib import Path

        raiz = ET.parse(
            Path("assets/maps/stage0/stage0.tmx")).getroot()
        props = {p.get("name"): p.get("value")
                 for p in raiz.findall("./properties/property")}
        assert "orden_por_y" in props, "stage0 no demuestra orden_por_y"
        assert "profundidad_curva" in props, "stage0 no demuestra la curva"

    def test_el_cargador_las_pasa_a_stage_data(self, _pygame_init) -> None:
        import pygame

        pygame.display.set_mode((320, 224))

        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader

        entity_factory.ensure_registered()
        StageLoader.clear_tmx_cache()
        stage = StageLoader.load("assets/maps/stage0/stage0.tmx")
        assert stage.orden_por_y is False
        assert stage.profundidad_curva == pytest.approx(1.0)
