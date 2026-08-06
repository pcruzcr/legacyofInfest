"""AUD-297 — suelo inclinado, dentro de la resolución de colisión.

La decisión, y quién la tomó
----------------------------
`docs/87` §11 recomendó hacerlo **aditivo** —un tipo nuevo con su propia
resolución— o no hacerlo, porque tocar la resolución de colisión es tocar el
sistema del que dependen las veintiséis entregas. Se pidió integrado, y así se
hizo, con la calificación de los dieciséis mapas como control.

Lo que hace que sea seguro no es el cuidado: es que **una pendiente es un tipo
de objeto nuevo y ningún mapa entregado tiene ninguno**. La lista llega vacía y
el paso entero se salta.

Lo que se fija aquí
-------------------
1. La geometría: dónde está la superficie, en cada sentido y en los bordes.
2. Que subir funcione, que **bajar** funcione —el caso que se rompe solo si
   nadie lo prueba— y que saltar despegue.
3. Que sin pendientes el jugador se comporte exactamente igual que antes.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.pendientes import MARGEN_DE_PEGADO, Pendiente, resolver


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


class TestLaGeometria:
    def test_sube_a_la_derecha(self) -> None:
        p = Pendiente(pygame.Rect(0, 0, 100, 50), sube_a_la_derecha=True)
        assert p.altura_en(0) == pytest.approx(50)      # pie, abajo
        assert p.altura_en(100) == pytest.approx(0)     # cima, arriba
        assert p.altura_en(50) == pytest.approx(25)

    def test_sube_a_la_izquierda(self) -> None:
        p = Pendiente(pygame.Rect(0, 0, 100, 50), sube_a_la_derecha=False)
        assert p.altura_en(0) == pytest.approx(0)
        assert p.altura_en(100) == pytest.approx(50)

    def test_fuera_del_rango_no_hay_superficie(self) -> None:
        p = Pendiente(pygame.Rect(0, 0, 100, 50))
        assert p.altura_en(-1) is None
        assert p.altura_en(101) is None

    def test_el_borde_derecho_entra(self) -> None:
        """Dos pendientes seguidas comparten el píxel del borde: excluirlo deja
        un hueco de un píxel por el que el jugador se cuela."""
        p = Pendiente(pygame.Rect(0, 0, 100, 50))
        assert p.altura_en(100) is not None

    def test_una_pendiente_sin_ancho_no_divide_por_cero(self) -> None:
        p = Pendiente(pygame.Rect(10, 0, 0, 50))
        assert p.altura_en(10) == pytest.approx(0)


class TestResolver:
    @staticmethod
    def _cuesta():
        # Sube a la derecha, de y=100 (pie) a y=50 (cima).
        return [Pendiente(pygame.Rect(0, 50, 100, 50), sube_a_la_derecha=True)]

    def test_los_pies_dentro_de_la_cuesta_suben(self) -> None:
        rect = pygame.Rect(40, 80, 20, 20)   # centro x=50, pies en 100
        assert resolver(rect, 0.0, True, self._cuesta()) == pytest.approx(75.0)

    def test_volando_por_encima_no_pasa_nada(self) -> None:
        rect = pygame.Rect(40, 0, 20, 20)    # pies en 20, muy por encima
        assert resolver(rect, 5.0, False, self._cuesta()) is None

    def test_por_debajo_del_triangulo_no_hay_suelo(self) -> None:
        """El jugador pasa por dentro de la roca, no sobre ella."""
        rect = pygame.Rect(40, 200, 20, 20)
        assert resolver(rect, 5.0, False, self._cuesta()) is None

    def test_subiendo_no_se_pega(self) -> None:
        """Saltar desde una cuesta tiene que despegar, no re-pegar al
        fotograma siguiente."""
        rect = pygame.Rect(40, 80, 20, 20)
        assert resolver(rect, -200.0, True, self._cuesta()) is None

    def test_al_bajar_se_pega_con_margen(self) -> None:
        """Sin esto, bajar una cuesta se hace a saltitos."""
        cuesta = self._cuesta()
        # Pies un poco por encima de la superficie, ya en el suelo.
        rect = pygame.Rect(40, 80 - int(MARGEN_DE_PEGADO / 2), 20, 20)
        assert resolver(rect, 0.0, True, cuesta) is not None

    def test_en_el_aire_el_margen_es_mucho_menor(self) -> None:
        """Volando **por encima** de la cuesta no hay que engancharse a ella.

        Los pies quedan unos píxeles por encima de la superficie: en el suelo
        eso es bajar una cuesta y hay que pegarse; en el aire es sobrevolarla.
        """
        cuesta = self._cuesta()
        superficie = 75.0                      # la cuesta en x=50
        arriba = int(superficie - MARGEN_DE_PEGADO / 2)
        rect = pygame.Rect(40, arriba - 20, 20, 20)
        assert resolver(rect, 5.0, False, cuesta) is None
        # Y en el suelo, la misma posición sí se pega: es bajar la cuesta.
        assert resolver(rect, 0.0, True, cuesta) == pytest.approx(superficie)

    def test_sin_pendientes_no_hay_nada_que_resolver(self) -> None:
        assert resolver(pygame.Rect(0, 0, 20, 20), 0.0, True, []) is None

    def test_con_dos_solapadas_gana_la_mas_alta(self) -> None:
        """Es la que el jugador está pisando de verdad."""
        baja = Pendiente(pygame.Rect(0, 100, 100, 20), sube_a_la_derecha=True)
        alta = Pendiente(pygame.Rect(0, 50, 100, 50), sube_a_la_derecha=True)
        rect = pygame.Rect(40, 80, 20, 20)
        assert resolver(rect, 0.0, True, [baja, alta]) == pytest.approx(75.0)


class TestElJugadorEnLaCuesta:
    @staticmethod
    def _jugador():
        from src.framework.entities.player import Player

        return Player(pygame.Vector2(50, 40))

    def test_subir_una_cuesta_lo_levanta(self) -> None:
        jugador = self._jugador()
        cuesta = [Pendiente(pygame.Rect(0, 50, 200, 100), sube_a_la_derecha=True)]
        # Primero se le deja caer sobre la cuesta: comparar el primer fotograma
        # con el último mediría la caída, no la subida.
        for _ in range(30):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        assert jugador.is_grounded, "no llegó a posarse en la cuesta"
        posado = jugador.rect.bottom

        # Se avanza la posición a mano en vez de dar velocidad: sin
        # `InputManager`, la máquina de estados pone `velocity.x` a cero cada
        # fotograma y el jugador no se movería. Lo que se mide es la cuesta, no
        # la entrada.
        for _ in range(20):
            jugador.position.x += 3.0
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        assert jugador.rect.bottom < posado, "la cuesta no levantó al jugador"
        assert jugador.is_grounded

    def test_bajar_no_va_a_saltitos(self) -> None:
        """El caso que se rompe solo si nadie lo prueba."""
        jugador = self._jugador()
        cuesta = [Pendiente(pygame.Rect(0, 50, 200, 100), sube_a_la_derecha=False)]
        jugador.position.update(20.0, 40.0)
        # Se le deja posarse antes de contar: la caída inicial no es traqueteo.
        for _ in range(30):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        assert jugador.is_grounded

        despegues = 0
        for _ in range(30):
            jugador.position.x += 3.0
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
            if not jugador.is_grounded:
                despegues += 1
        assert despegues == 0, (
            f"el jugador despegó {despegues} veces bajando: eso es el "
            "traqueteo que `MARGEN_DE_PEGADO` existe para evitar"
        )

    def test_sin_pendientes_todo_sigue_igual(self) -> None:
        """La condición para no romper las veintiséis entregas."""
        jugador = self._jugador()
        suelo = [pygame.Rect(0, 200, 400, 20)]
        for _ in range(40):
            jugador.update(1 / 60.0, suelo, None)
        assert jugador.is_grounded
        assert jugador.rect.bottom == 200


class TestDesdeElMapa:
    def test_slope_es_un_tipo_conocido(self) -> None:
        from src.framework.stage.tmx_diagnostics import known_object_types

        assert "Slope" in known_object_types([])

    def test_el_cargador_lo_lee(self) -> None:
        from src.framework.stage.stage_loader import StageData, StageLoader

        class _Obj:
            id, name, x, y, width, height = 1, "cuesta", 32.0, 64.0, 48.0, 48.0

        stage = StageData(map_layer=None)
        StageLoader._handle_pendiente(stage, _Obj(), {"sube": "izquierda"})
        assert len(stage.pendientes) == 1
        assert stage.pendientes[0].sube_a_la_derecha is False

    def test_un_sube_ilegible_no_revienta(self) -> None:
        from src.framework.stage.stage_loader import StageData, StageLoader

        class _Obj:
            id, name, x, y, width, height = 1, "cuesta", 32.0, 64.0, 48.0, 48.0

        stage = StageData(map_layer=None)
        StageLoader._handle_pendiente(stage, _Obj(), {"sube": "arriba"})
        assert stage.pendientes[0].sube_a_la_derecha is True

    def test_el_laboratorio_tiene_una_de_cada(self) -> None:
        """Subir y bajar, pegadas: bajar es el caso que hay que poder probar."""
        import re
        from pathlib import Path

        from src.engine.core import settings

        tmx = (Path(settings.ASSETS_DIR) / "maps" / "stage_mecanicas"
               / "stage_mecanicas.tmx").read_text(encoding="utf-8")
        assert len(re.findall(r'type="Slope"', tmx)) >= 2
        assert 'value="izquierda"' in tmx

    def test_ningun_mapa_entregado_tiene_pendientes(self) -> None:
        """Lo que hace segura una integración en la resolución de colisión: el
        paso nuevo no se ejecuta en ninguno de los mapas ya calificados."""
        from pathlib import Path

        from src.engine.core import settings

        con_pendiente = [
            tmx.parent.name
            for tmx in Path(settings.ASSETS_DIR).joinpath("maps").rglob("*.tmx")
            if 'type="Slope"' in tmx.read_text(encoding="utf-8")
        ]
        assert con_pendiente == ["stage_mecanicas"]
