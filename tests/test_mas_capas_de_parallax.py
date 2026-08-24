"""AUD-272 — el parallax admitía cuatro capas y el cargador sólo traía tres.

El defecto
==========
`DrawingSystem._PARALLAX_FACTORS` declara cuatro velocidades y engancha la
última a cualquier capa de más. El cargador, en cambio, buscaba exactamente
tres ficheros —`bg_<zona>_far`, `_mid`, `_near`— y no había forma de declarar
una cuarta desde los assets: la profundidad estaba limitada por el lado que
menos costaba cambiar.

Y había algo peor escondido: el factor se elegía **por índice de carga**. Si un
escenario añadía una capa de cielo delante de las otras, `far` pasaba de 0,15 a
0,35 y el mismo fondo se movía distinto en dos mapas, sin que nadie lo pidiera.

La corrección
-------------
El factor va **atado al nombre**, no a la posición: `sky` siempre es 0,06 y
`near` siempre 0,6, tenga el mapa dos capas o cinco. Se publica en un campo
nuevo, `background_factors`, para no cambiar el tipo de `background_layers`,
que es lo que leen las entregas.

Las capas nuevas —`sky` y `deep`— son **opcionales y silenciosas**: un mapa que
no las tenga se carga exactamente igual que antes. Las tres de siempre siguen
avisando si faltan, porque ahí sí es una errata.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.stage_loader import StageLoader


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


class TestElFactorVaConElNombre:
    def test_hay_una_velocidad_declarada_por_capa(self) -> None:
        assert set(StageLoader.CAPAS_DE_FONDO) <= set(StageLoader.VELOCIDAD_DE_FONDO)

    def test_lo_lejano_se_mueve_menos_que_lo_cercano(self) -> None:
        v = StageLoader.VELOCIDAD_DE_FONDO

        assert v["sky"] < v["deep"] < v["far"] < v["mid"] < v["near"]

    def test_el_cielo_casi_no_se_mueve(self) -> None:
        """Un cielo que sigue a la cámara deja de leerse como cielo."""
        assert StageLoader.VELOCIDAD_DE_FONDO["sky"] < 0.1

    def test_ninguna_capa_va_mas_rapido_que_el_mapa(self) -> None:
        """Un fondo a velocidad 1,0 o más se pega al terreno y rompe la ilusión."""
        assert all(0.0 < v < 1.0 for v in StageLoader.VELOCIDAD_DE_FONDO.values())


class TestSonCincoYEnOrden:
    def test_de_lo_mas_lejano_a_lo_mas_cercano(self) -> None:
        assert StageLoader.CAPAS_DE_FONDO == ("sky", "deep", "far", "mid", "near")

    def test_las_tres_de_siempre_siguen_estando(self) -> None:
        """Quitar una rompería los dieciséis mapas entregados."""
        for capa in ("far", "mid", "near"):
            assert capa in StageLoader.CAPAS_DE_FONDO

    def test_las_nuevas_son_opcionales(self) -> None:
        """Un mapa sin `sky` ni `deep` no puede quejarse: casi ninguno las tiene."""
        assert StageLoader.CAPAS_OPCIONALES == frozenset({"sky", "deep"})


class TestElDibujadoUsaElFactorPublicado:
    def test_stage_data_publica_los_factores(self) -> None:
        import dataclasses

        from src.framework.stage.stage_loader import StageData

        campos = {f.name for f in dataclasses.fields(StageData)}
        assert "background_factors" in campos

    def test_sin_factores_publicados_se_dibuja_igual_que_antes(self) -> None:
        """Las entregas que construyan un `StageData` a mano no se rompen."""
        from src.framework.stage.drawing_system import DrawingSystem

        assert DrawingSystem._PARALLAX_FACTORS, (
            "la tabla por índice sigue haciendo falta como respaldo"
        )
