"""GAP-002 — el caso que la heurística de X-skip no sabía manejar.

Lo que temía el hueco
=====================
La resolución en X saltaba las colisiones con `tile.top >= player_rect.centery`:
«si el borde de arriba del rect está por debajo de mi centro, es suelo, no
pared». Funciona con plataformas de 16 px, y su propia nota avisaba de que
podría no funcionar con un rect **fusionado que mezcle suelo y pared vertical**
en un solo objeto, porque entonces `tile.top` es el del muro y no el del piso.

Lo que hay ahora
----------------
Esa comparación ya no existe. La regla es el **solape vertical** con la posición
previa:

    v_overlap = min(pre.bottom, tile.bottom) - max(pre.top, tile.top)
    if v_overlap <= 2: continue

De pie sobre un rect, los pies coinciden con `tile.top` y el solape es ~0: se
salta. Andando contra un muro, el solape es la altura del cuerpo: se resuelve.
Y **no mira la altura del rect en ningún momento**, que era exactamente el
refinamiento que la nota del hueco pedía.

Estas pruebas construyen el caso temido —una L de 200 px que es piso y muro a la
vez— y comprueban las dos mitades: que se puede caminar por encima y que el muro
sigue frenando. Sin ellas, cerrar el hueco sería fiarse de una lectura.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.input.action_map import Action
from src.framework.entities.player import Player
from tests.playtest.bot import _StubInput

DT = 1.0 / 60.0
ALTO_JUGADOR = 32
ANCHO_JUGADOR = 20


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def _rect_fusionado() -> pygame.Rect:
    """Un solo rect que es piso y muro: alto de 200 px, cima en y=300.

    Es lo que produce la fusión de rects (FIX-1) cuando un mapa tiene una
    columna de bloques pegada al suelo. El hueco avisaba de este caso por su
    nombre: «merged que abarca piso + pared».
    """
    return pygame.Rect(0, 300, 400, 200)


def _andar_derecha(jugador: Player, rects: list[pygame.Rect], fotogramas: int) -> None:
    """Camina a la derecha durante N fotogramas, por el mando.

    Fijar `velocity.x` a mano no sirve: `update()` pasa por la máquina de
    estados, y el estado de suelo reescribe la velocidad desde la entrada. Sin
    `input_manager` el jugador se queda quieto y la prueba mide el vacío. Es el
    mismo tropiezo que costó una tanda en el banco de saltos.
    """
    mando = _StubInput()
    for _ in range(fotogramas):
        mando.set_actions({Action.MOVE_RIGHT})
        jugador.update(DT, rects, mando)


def _jugador_sobre(rect: pygame.Rect, x: float) -> Player:
    jugador = Player(pygame.Vector2(x, float(rect.top - ALTO_JUGADOR)))
    jugador.is_grounded = True
    return jugador


class TestSePuedeAndarSobreUnRectFusionado:
    def test_el_jugador_avanza_sobre_la_cima(self) -> None:
        """Si el X-skip fallara, el muro del propio suelo lo frenaría en seco."""
        suelo = _rect_fusionado()
        jugador = _jugador_sobre(suelo, 50.0)
        partida = jugador.position.x

        _andar_derecha(jugador, [suelo], 60)

        assert jugador.position.x > partida + 40, (
            f"el jugador sólo avanzó {jugador.position.x - partida:.1f} px sobre "
            f"un rect de {suelo.height} px de alto: el X-skip lo está tratando "
            f"como pared"
        )

    def test_y_no_se_hunde_en_el(self) -> None:
        suelo = _rect_fusionado()
        jugador = _jugador_sobre(suelo, 50.0)
        _andar_derecha(jugador, [suelo], 60)
        assert jugador.position.y + ALTO_JUGADOR == pytest.approx(suelo.top, abs=2)

    @pytest.mark.parametrize("alto", [16, 64, 200, 600])
    def test_la_altura_del_rect_da_igual(self, alto: int) -> None:
        """El nudo del hueco: la decisión no puede depender de lo alto que sea.

        La heurística vieja comparaba `tile.top` con el centro del jugador, así
        que un rect más alto movía el veredicto. La de ahora mira el solape con
        la posición previa, que sólo depende de dónde estaba el cuerpo.
        """
        suelo = pygame.Rect(0, 300, 400, alto)
        jugador = _jugador_sobre(suelo, 50.0)
        partida = jugador.position.x
        _andar_derecha(jugador, [suelo], 60)
        assert jugador.position.x > partida + 40, f"frenado sobre un rect de {alto} px"


class TestElMuroSigueFrenando:
    def test_andar_contra_una_pared_no_la_atraviesa(self) -> None:
        """La otra mitad: saltar de más convertiría los muros en aire."""
        suelo = pygame.Rect(0, 300, 400, 200)
        muro = pygame.Rect(200, 100, 32, 200)   # de y=100 a y=300, sobre el suelo
        jugador = _jugador_sobre(suelo, 100.0)

        _andar_derecha(jugador, [suelo, muro], 120)

        assert jugador.position.x + ANCHO_JUGADOR <= muro.left + 1, (
            f"el jugador llegó a x={jugador.position.x:.1f} y el muro empieza "
            f"en {muro.left}: lo atravesó"
        )

    def test_el_solape_de_dos_pixeles_es_la_frontera(self) -> None:
        """El umbral es `<= 2`, y conviene que esté fijado por una prueba.

        Dos píxeles es la tolerancia para el redondeo a entero del rect; subirla
        haría atravesable un escalón bajo, y bajarla a cero haría que el jugador
        se enganchara con el suelo sobre el que está de pie.
        """
        import inspect

        from src.framework.physics.resolucion import resolver_eje_x

        # AUD-334 — el umbral vive en el resolutor compartido, que es donde
        # corre el eje X del jugador desde el port.
        fuente = inspect.getsource(resolver_eje_x)
        assert "v_overlap <= 2" in fuente, (
            "cambió el umbral de solape vertical del X-skip; era `<= 2` y es lo "
            "que separa «estoy de pie encima» de «me estoy dando contra ello»"
        )
