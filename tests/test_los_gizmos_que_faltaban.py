"""AUD-285 — F1 decía dónde estaba todo y nada más.

El hueco
--------
Los gizmos de F1 dibujaban `rect`, `hurtbox` y `hitbox`: tres cajas que dicen
**dónde** está algo. Ninguna decía hacia dónde va ni qué está mirando, y los dos
datos existían ya en memoria:

* `velocity` — sin verla no se distingue un enemigo pegado a una pared de uno
  parado, ni se ve que un knockback sale hacia el lado contrario.
* `ConoDeVision` — sin verlo, «¿por qué me ha detectado desde allí?» sólo se
  contesta leyendo el código.

El cono es además el único que no se podía dibujar sin tocar el cableado: no es
una entidad, es un componente del ECS, y `DrawContext` no tenía el mundo.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.drawing_system import DrawContext, DrawingSystem


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


class _StageFalso:
    def __init__(self, entidades) -> None:
        self.entity_list = list(entidades)
        self.collision_rects: list = []


class _Cuerpo:
    def __init__(self, x, y, vx=0.0, vy=0.0) -> None:
        self.rect = pygame.Rect(x, y, 16, 16)
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(vx, vy)
        self.is_alive = True
        self.is_visible = True


def _pixeles_encendidos(dibujar) -> set[int]:
    """Los colores que este dibujado deja sobre negro.

    Se cuentan píxeles y no se mira el color medio: una línea de un píxel sobre
    800 × 600 no mueve la media ni un entero, así que `average_color` daría
    negro tanto si se dibujó como si no.
    """
    import numpy as np

    superficie = pygame.Surface((800, 600))
    superficie.fill((0, 0, 0))
    dibujar(superficie)
    pixeles = pygame.surfarray.array2d(superficie)
    return set(np.unique(pixeles).tolist()) - {0}


def _pinta_algo(dibujar) -> bool:
    return bool(_pixeles_encendidos(dibujar))


class TestElVectorDeVelocidad:
    def test_una_entidad_en_movimiento_pinta_su_flecha(self) -> None:
        sistema = DrawingSystem()
        stage = _StageFalso([_Cuerpo(100, 100, vx=200.0)])
        assert _pinta_algo(lambda s: sistema._dibujar_velocidades(
            s, stage, None, pygame.Vector2(0, 0)))

    def test_una_entidad_quieta_no(self) -> None:
        """Un punto por cada entidad parada llena la pantalla de basura y
        esconde justo las que sí se mueven."""
        sistema = DrawingSystem()
        stage = _StageFalso([_Cuerpo(100, 100)])
        assert not _pinta_algo(lambda s: sistema._dibujar_velocidades(
            s, stage, None, pygame.Vector2(0, 0)))

    def test_la_flecha_predice_un_cuarto_de_segundo(self) -> None:
        """La longitud significa algo: dónde estará si nada lo para. A escala 1
        una caída normal daría una flecha de 500 px que taparía el nivel."""
        assert DrawingSystem._GIZMO_SEGUNDOS == pytest.approx(0.25)

    def test_una_entidad_sin_velocidad_no_revienta(self) -> None:
        """Los checkpoints y los recogibles no tienen `velocity`."""
        sistema = DrawingSystem()

        class _SinVelocidad:
            rect = pygame.Rect(0, 0, 8, 8)

        stage = _StageFalso([_SinVelocidad(), None])
        sistema._dibujar_velocidades(pygame.Surface((800, 600)), stage, None,
                                     pygame.Vector2(0, 0))


class TestElConoDeVision:
    @staticmethod
    def _mundo_con_cono(ve: bool):
        from src.framework.ecs.components import ConoDeVision, Transform
        from src.framework.ecs.world import World

        mundo = World()
        cono = ConoDeVision(mira=pygame.Vector2(1.0, 0.0), alcance=120.0,
                            semiangulo=30.0)
        cono.ve_al_jugador = ve
        mundo.crear(Transform(rect=pygame.Rect(200, 200, 16, 16)), cono)
        return mundo

    def test_se_dibuja(self) -> None:
        sistema = DrawingSystem()
        mundo = self._mundo_con_cono(False)
        assert _pinta_algo(lambda s: sistema._dibujar_conos(
            s, mundo, pygame.Vector2(0, 0)))

    def test_cambia_de_color_cuando_te_ve(self) -> None:
        """Es la respuesta visual a «¿por qué me ha detectado?»."""
        sistema = DrawingSystem()

        def colores_con(ve: bool):
            return _pixeles_encendidos(lambda s: sistema._dibujar_conos(
                s, self._mundo_con_cono(ve), pygame.Vector2(0, 0)))

        assert colores_con(True) != colores_con(False)

    def test_sin_mundo_no_revienta(self) -> None:
        """Una escena que no monte ECS —o un doble en una prueba— pasa `None`."""
        DrawingSystem()._dibujar_conos(pygame.Surface((800, 600)), None,
                                       pygame.Vector2(0, 0))


class TestElCableado:
    def test_el_contexto_de_dibujado_lleva_el_mundo(self) -> None:
        """Sin esto el cono no tiene de dónde salir: no es una entidad."""
        assert "mundo" in DrawContext.__dataclass_fields__

    def test_la_escena_lo_pasa(self) -> None:
        import inspect

        from src.framework.scenes import stage_scene

        assert "mundo=self._mundo" in inspect.getsource(stage_scene)
