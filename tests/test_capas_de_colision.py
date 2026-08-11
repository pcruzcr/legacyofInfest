"""AUD-395 — capas de colisión sobre el resolutor AABB. Cierra GAP-038.

El defecto
==========
La pregunta «¿qué frena a esta entidad?» no tenía dónde vivir, así que se
respondía a mano en cada sitio que la necesitaba:

* `StageLoader._load_collision` decidía la clase de cada caja —`Platform` o no—
  y guardaba esa decisión en **qué lista** iba a parar. Eso ya era una capa,
  expresada de forma que no se puede ni consultar ni ampliar.
* `bloques.py` recompone: `stage.collision_rects + cerradas + bloques.rects_solidos()`.
* Una entrega de estudiante hace `self._collision_rects + self._one_way_rects`.
* `StageScene` pasaba las dos listas del escenario a todos los enemigos por
  igual; un enemigo que tuviera que ignorar algo se lo filtraba él por dentro.

Añadir una clase de sólido —cristal que sólo frena proyectiles, una verja que
el jugador cruza y los enemigos no— obligaba a tocar todos esos sitios y a
acordarse de todos.

Por qué no vuelve pymunk
========================
Decisión del dueño (2026-08-11): capas propias sobre el AABB actual. La fachada
que se retiró en AUD-004 *aparentaba* tener categorías de colisión sin
tenerlas —asignaba `_CAT_*` a `shape.collision_type`, la clave de despacho, en
vez de a `shape.filter`, el bitmask real, y nunca registró un manejador—, y
`add_static_collision` creaba un cuerpo y una forma por tile. Esto es lo que
aquella fachada aparentaba ser, sin dependencia nueva.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.physics.capas import MASCARA_POR_DEFECTO, Capa, MapaDeCapas


@pytest.fixture
def mapa() -> MapaDeCapas:
    m = MapaDeCapas()
    m.poner(Capa.SOLIDO, [pygame.Rect(0, 0, 10, 10), pygame.Rect(20, 0, 10, 10)])
    m.poner(Capa.PLATAFORMA, [pygame.Rect(40, 0, 10, 10)])
    m.poner(Capa.DESTRUCTIBLE, [pygame.Rect(60, 0, 10, 10)])
    return m


class TestElFiltrado:
    def test_la_mascara_por_defecto_da_solidos_y_plataformas(
        self, mapa: MapaDeCapas
    ) -> None:
        """El comportamiento de antes de que existieran las capas.

        Es el valor que importa de esta prueba: si la máscara por defecto
        cambiara, cambiarían los dieciséis mapas entregados sin que nadie lo
        hubiera pedido.
        """
        assert len(mapa.solidos_para(MASCARA_POR_DEFECTO)) == 3

    def test_una_mascara_sin_plataformas_las_excluye(self, mapa: MapaDeCapas) -> None:
        """El caso que el hueco pedía poder expresar."""
        solo_solidos = mapa.solidos_para(Capa.SOLIDO)
        assert len(solo_solidos) == 2
        assert pygame.Rect(40, 0, 10, 10) not in solo_solidos

    def test_se_pueden_combinar_capas(self, mapa: MapaDeCapas) -> None:
        assert len(mapa.solidos_para(Capa.SOLIDO | Capa.DESTRUCTIBLE)) == 3

    def test_la_mascara_vacia_no_frena_nada(self, mapa: MapaDeCapas) -> None:
        """Una entidad que atraviesa el escenario entero: un fantasma."""
        assert mapa.solidos_para(Capa.NADA) == []

    def test_todo_incluye_las_declaradas(self, mapa: MapaDeCapas) -> None:
        assert len(mapa.solidos_para(Capa.TODO)) == 4

    def test_devuelve_una_lista_y_no_un_generador(self, mapa: MapaDeCapas) -> None:
        """El resolutor la recorre varias veces por fotograma.

        Con un generador el segundo recorrido saldría vacío, y eso no falla:
        el jugador atravesaría el suelo un fotograma de cada dos.
        """
        salida = mapa.solidos_para(Capa.TODO)
        assert isinstance(salida, list)
        assert len(list(salida)) == len(list(salida))

    def test_una_capa_sin_declarar_no_estalla(self) -> None:
        assert MapaDeCapas().solidos_para(Capa.TODO) == []


class TestLoQueDeclaraLaEntidad:
    def test_una_entidad_normal_choca_con_lo_de_siempre(self) -> None:
        from src.framework.entities.player import Player

        jugador = Player(pygame.Vector2(0, 0))
        assert jugador.mascara_de_colision == MASCARA_POR_DEFECTO

    def test_una_subclase_puede_declarar_la_suya(self) -> None:
        """La forma en que se usa: una línea al escribir el enemigo."""
        from src.framework.entities.enemy_base import EnemyBase

        class Fantasma(EnemyBase):
            mascara_de_colision = Capa.SOLIDO

        assert Fantasma.mascara_de_colision == Capa.SOLIDO
        assert EnemyBase.mascara_de_colision == MASCARA_POR_DEFECTO, (
            "declarar la máscara en una subclase se la cambió a la base"
        )


class TestElEscenarioLasPublica:
    """Las dos vistas de la misma verdad no pueden discrepar."""

    def _stage0(self):
        import pygame as pg

        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader

        if not pg.display.get_init():
            pg.display.init()
        if pg.display.get_surface() is None:
            pg.display.set_mode((1, 1))
        entity_factory.ensure_registered()
        return StageLoader.load("assets/maps/stage0/stage0.tmx")

    def test_la_capa_solido_es_collision_rects(self) -> None:
        datos = self._stage0()
        assert datos.capas.de(Capa.SOLIDO) == datos.collision_rects

    def test_la_capa_plataforma_es_one_way_rects(self) -> None:
        datos = self._stage0()
        assert datos.capas.de(Capa.PLATAFORMA) == datos.one_way_rects

    def test_por_defecto_se_ve_todo_lo_que_se_veia_antes(self) -> None:
        """El cable trampa de la compatibilidad.

        Si esto se rompe, algún mapa dejó de frenar donde frenaba y la
        característica nueva se llevó por delante el contenido existente.
        """
        datos = self._stage0()
        esperado = len(datos.collision_rects) + len(datos.one_way_rects)
        assert len(datos.capas.solidos_para(MASCARA_POR_DEFECTO)) == esperado
