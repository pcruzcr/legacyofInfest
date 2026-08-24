"""AUD-389 — A* sobre tiles. Cierra GAP-045.

El hueco, y su consumidor
=========================
`sistema_acosador` perseguía al jugador con `hacia.normalize()`: **línea recta,
atravesando muros**. Un perseguidor que se mete en una pared y se queda
temblando contra ella no da la tensión de Nemesis que su propio docstring
describe; da lástima.

No es un sistema nuevo buscando quién lo use: es el arreglo de un
comportamiento que ya estaba mal, con la infraestructura que faltaba.

El diseño, decidido por el dueño
================================
A* sobre la rejilla de tiles, con los `Waypoint` que ya existen en el TMX como
ruta declarada cuando el diseñador quiere control, y **recálculo por cadencia
escalonada**: cada navegante recalcula unas cuatro veces por segundo, repartido
entre fotogramas para que no coincidan todos. Es el mismo patrón que
`SquadBrain` usa con su predicción por lote, y por el mismo motivo: el coste
por fotograma queda acotado y medible en vez de depender de cuántos enemigos
hayan decidido pensar a la vez.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.ai import navegacion


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    yield


TILE = 16


def _malla_con_muro() -> navegacion.MallaDeNavegacion:
    """Un pasillo de 10x5 tiles con un muro vertical en la columna 5.

    El muro deja un hueco abajo, así que hay camino: pero sólo rodeando.
    """
    muro = [pygame.Rect(5 * TILE, y * TILE, TILE, TILE) for y in range(0, 4)]
    return navegacion.MallaDeNavegacion.desde_rects(
        muro, ancho_px=10 * TILE, alto_px=5 * TILE, tile=TILE)


class TestLaMalla:
    def test_marca_lo_solido_como_intransitable(self):
        m = _malla_con_muro()
        assert not m.transitable(5, 0)
        assert m.transitable(0, 0)

    def test_fuera_del_mapa_no_es_transitable(self):
        m = _malla_con_muro()
        assert not m.transitable(-1, 0)
        assert not m.transitable(999, 0)

    def test_convierte_pixeles_a_celda(self):
        m = _malla_con_muro()
        assert m.celda_de(pygame.Vector2(3 * TILE + 5, 2 * TILE + 1)) == (3, 2)


class TestElCamino:
    def test_encuentra_la_ruta_rodeando_el_muro(self):
        m = _malla_con_muro()
        ruta = navegacion.a_estrella(m, (0, 0), (9, 0))
        assert ruta, "no encontró camino habiendo hueco por abajo"
        assert ruta[-1] == (9, 0)
        # La recta pasaría por la columna 5 en la fila 0, que es muro.
        assert (5, 0) not in ruta

    def test_sin_camino_devuelve_vacio(self):
        """Un muro completo: mejor una lista vacía que una ruta inventada.

        El llamante distingue «no hay camino» de «ya estoy» por la longitud, y
        devolver una ruta imposible haría que el acosador se empotrara igual
        que antes, sólo que con más código.
        """
        muro = [pygame.Rect(5 * TILE, y * TILE, TILE, TILE) for y in range(0, 5)]
        m = navegacion.MallaDeNavegacion.desde_rects(
            muro, ancho_px=10 * TILE, alto_px=5 * TILE, tile=TILE)
        assert navegacion.a_estrella(m, (0, 0), (9, 0)) == []

    def test_el_mismo_sitio_es_ruta_vacia(self):
        m = _malla_con_muro()
        assert navegacion.a_estrella(m, (2, 2), (2, 2)) == []

    def test_una_meta_dentro_de_un_muro_no_cuelga(self):
        """Un jugador dentro de la geometría es un caso real, no teórico.

        Pasa con un tile de colisión mal puesto o con el jugador empotrado un
        fotograma. Tiene que devolver algo, no explorar el mapa entero.
        """
        m = _malla_con_muro()
        assert navegacion.a_estrella(m, (0, 0), (5, 0)) == []

    def test_el_tope_de_nodos_acota_el_coste(self):
        """La red de seguridad: un mapa grande no puede costar un fotograma."""
        m = _malla_con_muro()
        assert navegacion.a_estrella(m, (0, 0), (9, 4), tope=3) == []


class TestLaCadenciaEscalonada:
    def test_los_navegantes_no_recalculan_todos_a_la_vez(self):
        """Lo que hace acotado el coste.

        Sin escalonar, treinta enemigos que aparecen en el mismo fotograma
        recalculan en el mismo fotograma para siempre: el coste no es «cuatro
        veces por segundo», es «treinta A* de golpe, cuatro veces por segundo».
        """
        from src.framework.ecs.components import Navegante

        esperas = {Navegante().proximo for _ in range(12)}
        assert len(esperas) > 1, (
            f"los doce navegantes recalculan en el mismo instante: {esperas}"
        )

    def test_la_espera_cabe_en_la_cadencia(self):
        from src.framework.ecs.components import Navegante

        for _ in range(20):
            assert 0.0 <= Navegante().proximo <= navegacion.CADENCIA


class TestElAcosadorRodea:
    """El cable trampa, y la razón de ser del lote.

    Sin esto el A* sería correcto y el acosador seguiría empotrándose, que es
    exactamente la especie de defecto que esta fase lleva doce lotes cazando.
    """

    def test_el_sistema_usa_la_navegacion(self):
        import inspect

        from src.framework.ecs import systems as S

        fuente = inspect.getsource(S.sistema_acosador)
        assert "ruta" in fuente or "navegacion" in fuente, (
            "`sistema_acosador` sigue persiguiendo en línea recta: se empotra "
            "en el primer muro que haya entre él y el jugador"
        )

    def test_sin_geometria_sigue_yendo_recto(self):
        """Compatibilidad: un mundo sin malla publicada se comporta como antes.

        Igual que la oclusión de AUD-381 — sin geometría no se puede deducir
        que haya un muro, y quedarse quieto sería peor que ir recto.
        """
        import pygame as pg

        from src.framework.ecs import systems as S
        from src.framework.ecs.components import (
            Acosador,
            EsJugador,
            Transform,
        )
        from src.framework.ecs.world import World

        m = World()
        a = m.crear(
            Transform(pg.Vector2(0, 0), pg.Rect(0, 0, 16, 16)),
            Acosador(velocidad=100.0),
        )
        m.crear(Transform(pg.Vector2(200, 0), pg.Rect(200, 0, 16, 16)), EsJugador())

        S.sistema_acosador(m, 1 / 60)
        assert m.obtener(a, Transform).posicion.x > 0.0
