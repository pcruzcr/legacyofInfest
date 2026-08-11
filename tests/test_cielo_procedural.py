"""AUD-426 — el cielo era un PNG, así que la hora no podía cambiarlo.

Por qué estaba en el Nivel 1 del catálogo
=========================================
`docs/92` §4 lo pone entre lo imprescindible, y el motivo es concreto: con tres
PNG por zona sólo hay tres cielos. El ciclo día/noche existe desde AUD-111 y lo
único que podía hacer era **oscurecer una imagen fija de mediodía**; el
crepúsculo de verdad —horizonte naranja con el cénit todavía azul— no se puede
pintar en un PNG que también tiene que servir para el mediodía.

Un degradado calculado desde `EnvironmentState` sí puede, porque el color sale
de la altura del sol.

Lo que estas pruebas fijan
==========================
Sobre todo dos cosas que son fáciles de romper sin darse cuenta:

* **Que no se dibuje donde nadie lo pidió.** Los mapas con PNG de cielo ya
  traen el suyo pintado dentro; un degradado debajo no se vería, costaría, y un
  mapa sin fondo pasaría de `BG_COLOR` a un degradado sin haberlo pedido.
* **Que el caché acierte.** Un degradado de pantalla completa son 180 `line` a
  60 Hz. Si la clave del caché incluyera la hora sin redondear, no acertaría
  nunca y esto costaría un fotograma entero.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.vfx.cielo import CieloProcedural


class _Ambiente:
    """Lo único que el cielo consulta del estado del mundo."""

    def __init__(self, altura_solar: float = 1.0, cobertura_nubes: float = 0.0):
        self.altura_solar = altura_solar
        self.cobertura_nubes = cobertura_nubes


@pytest.fixture(autouse=True)
def _video():
    if not pygame.display.get_init():
        pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 180))


def _color_medio(sup: pygame.Surface, y: int) -> tuple[int, int, int]:
    return sup.get_at((sup.get_width() // 2, y))[:3]


class TestElDegradado:
    def test_el_cielo_cambia_con_la_hora(self) -> None:
        """Lo que un PNG no puede hacer, y el motivo del lote."""
        cielo = CieloProcedural()
        dia = cielo.superficie((64, 64), _Ambiente(altura_solar=1.0)).copy()
        noche = cielo.superficie((64, 64), _Ambiente(altura_solar=-1.0)).copy()
        assert _color_medio(dia, 32) != _color_medio(noche, 32)

    def test_de_noche_es_mas_oscuro_que_de_dia(self) -> None:
        cielo = CieloProcedural()
        dia = sum(_color_medio(cielo.superficie((64, 64), _Ambiente(1.0)).copy(), 32))
        noche = sum(_color_medio(cielo.superficie((64, 64), _Ambiente(-1.0)).copy(), 32))
        assert noche < dia

    def test_el_crepusculo_calienta_el_horizonte(self) -> None:
        """La prueba que justifica el lote entero.

        Con el sol en el horizonte, la parte de abajo tira a naranja mientras
        la de arriba sigue azul. Ésa es la diferencia **dentro de la misma
        imagen** que un PNG de mediodía no puede dar.
        """
        sup = CieloProcedural().superficie((64, 64), _Ambiente(altura_solar=0.0))
        arriba = _color_medio(sup, 2)
        abajo = _color_medio(sup, 61)
        assert abajo[0] > arriba[0], "el horizonte no se calienta al amanecer"
        assert arriba[2] > abajo[2], "el cénit no se mantiene más azul"

    def test_es_un_degradado_y_no_un_color_plano(self) -> None:
        sup = CieloProcedural().superficie((64, 64), _Ambiente(altura_solar=0.5))
        assert _color_medio(sup, 2) != _color_medio(sup, 61)

    def test_las_nubes_lo_apagan_sin_borrar_la_hora(self) -> None:
        """Cubierto no es gris plano: a mediodía y de madrugada se vería igual."""
        cielo = CieloProcedural()
        despejado = _color_medio(cielo.superficie((64, 64), _Ambiente(1.0, 0.0)).copy(), 32)
        cubierto = _color_medio(cielo.superficie((64, 64), _Ambiente(1.0, 1.0)).copy(), 32)
        assert cubierto != despejado
        noche_cubierta = _color_medio(
            cielo.superficie((64, 64), _Ambiente(-1.0, 1.0)).copy(), 32)
        assert noche_cubierta != cubierto, (
            "con el cielo cubierto la hora del día deja de notarse"
        )


class TestElCache:
    def test_el_mismo_estado_devuelve_la_misma_superficie(self) -> None:
        cielo = CieloProcedural()
        a = cielo.superficie((64, 64), _Ambiente(0.5, 0.2))
        b = cielo.superficie((64, 64), _Ambiente(0.5, 0.2))
        assert a is b, "el caché no acierta: se redibuja el degradado cada vez"

    def test_un_cambio_imperceptible_no_lo_invalida(self) -> None:
        """La clave se redondea, y eso **es** el caché.

        `altura_solar` cambia cada fotograma con el reloj corriendo. Sin
        redondear, esto redibujaría 180 líneas sesenta veces por segundo.
        """
        cielo = CieloProcedural()
        a = cielo.superficie((64, 64), _Ambiente(0.500, 0.0))
        b = cielo.superficie((64, 64), _Ambiente(0.5001, 0.0))
        assert a is b

    def test_un_cambio_real_si_lo_invalida(self) -> None:
        cielo = CieloProcedural()
        a = cielo.superficie((64, 64), _Ambiente(0.5, 0.0))
        b = cielo.superficie((64, 64), _Ambiente(0.9, 0.0))
        assert a is not b

    def test_cambiar_de_tamano_lo_invalida(self) -> None:
        cielo = CieloProcedural()
        a = cielo.superficie((64, 64), _Ambiente(0.5))
        b = cielo.superficie((128, 64), _Ambiente(0.5))
        assert a is not b
        assert b.get_width() == 128


class TestSoloDondeSePide:
    def test_la_propiedad_esta_apagada_por_defecto(self) -> None:
        from src.framework.stage.stage_data import StageData

        assert StageData(map_layer=None).cielo is False

    def test_el_laboratorio_lo_declara(self) -> None:
        """Se demuestra en `stage_mecanicas` y no en un mapa de historia.

        Es el laboratorio: quien quiera ver el degradado moverse con la hora
        abre ese mapa y cambia `start_hour`.
        """
        import xml.etree.ElementTree as ET
        from pathlib import Path

        raiz = Path(__file__).resolve().parent.parent
        tmx = raiz / "assets" / "maps" / "stage_mecanicas" / "stage_mecanicas.tmx"
        props = ET.parse(tmx).getroot().find("properties")
        assert props is not None
        valores = {p.get("name"): p.get("value") for p in props.findall("property")}
        assert valores.get("cielo") == "true"

    def test_el_cargador_lo_lee(self) -> None:
        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader

        entity_factory.ensure_registered()
        datos = StageLoader.load("assets/maps/stage_mecanicas/stage_mecanicas.tmx")
        assert datos.cielo is True

    def test_un_mapa_normal_no_lo_enciende(self) -> None:
        """Los mapas de siempre se ven exactamente igual."""
        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader

        entity_factory.ensure_registered()
        assert StageLoader.load("assets/maps/stage0/stage0.tmx").cielo is False
