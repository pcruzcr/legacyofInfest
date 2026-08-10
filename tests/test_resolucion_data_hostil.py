"""AUD-344 — el resolutor aguanta datos que no son números.

El hueco
--------
El resolutor era una puerta sin verja: un `dt` quebrado o una posición que ya
no era un número (NaN, infinito) viajaba hasta que `int(pos.x)` de algún paso
reventaba el fotograma. Para el jugador eso es un cierre de partida en mitad
de un nivel sin ningún mensaje; para el motor, un fallo que una entidad de un
estudiante puede provocar con un simple `pos.x = float("nan")`.

Lo que fija este test
---------------------
* `dt` inválido (<= 0 o NaN): el fotograma no se integra, sin excepción.
* Posición NaN/∞: la entidad vuelve a (0, 0), la velocidad se corta.
* Velocidad NaN/∞: se corta la velocidad y la simulación sigue con el resto.
* Un fotograma legítimo no se altera (no es un umbral que pique al sano).

AUD-355 — la verja estaba en la puerta que nadie usa
----------------------------------------------------
La comprobación de AUD-344 se escribió dentro de `resolver_movimiento`, que
es la fachada «resuelve el fotograma entero» del módulo. Pero **ninguna
entidad del juego la llama**: `git grep resolver_movimiento` sólo la
encuentra en el propio módulo, en su `__all__` y en estos tests. El jugador
—`player.py:1077, 1085, 1125, 1159`— compone los pasos a mano:
`resolver_eje_x`, `resolver_paredes_de_pendientes`, `resolver_eje_y`,
`resolver_cuestas` y `resolver_repisas`. Ninguno tenía verja, y es
`resolver_eje_x` quien hace el `pygame.Rect(int(estado.posicion.x), ...)`
que revienta.

O sea: la protección existía, estaba probada, y el fotograma del jugador
seguía siendo exactamente igual de frágil que antes de escribirla. Las
clases de abajo son las mismas comprobaciones sobre los pasos reales.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.physics.perfil import Cuestas
from src.framework.physics.resolucion import (
    Contacto,
    EstadoDeMovimiento,
    resolver_cuestas,
    resolver_eje_x,
    resolver_eje_y,
    resolver_movimiento,
    resolver_repisas,
)
from src.framework.stage.pendientes import Pendiente


def _estado(x: float = 10.0, y: float = 20.0, vx: float = 1.0, vy: float = 0.0):
    return EstadoDeMovimiento(
        posicion=pygame.Vector2(x, y),
        velocidad=pygame.Vector2(vx, vy),
        ancho=16.0,
        alto=32.0,
    )


class TestDtInvalido:
    def test_dt_cero_no_integra_ni_rompe(self) -> None:
        estado = _estado(vx=100.0)
        resolver_movimiento(estado, 0.0, [])
        assert estado.posicion.x == 10.0

    def test_dt_negativo_tratado_como_invalido(self) -> None:
        estado = _estado(vx=-5.0)
        resolver_movimiento(estado, -0.25, [])
        assert estado.posicion.x == 10.0

    def test_dt_nan_no_lanza(self) -> None:
        estado = _estado()
        resolver_movimiento(estado, float("nan"), [])
        assert estado.posicion == pygame.Vector2(10.0, 20.0)

    def test_dt_infinito_no_lanza(self) -> None:
        estado = _estado()
        resolver_movimiento(estado, float("inf"), [])
        assert estado.posicion == pygame.Vector2(10.0, 20.0)


class TestPosicionNoFinita:
    def test_posicion_nan_devuelve_al_origen(self) -> None:
        estado = _estado(x=float("nan"))
        resolver_movimiento(estado, 0.016, [])
        assert estado.posicion == pygame.Vector2(0.0, 0.0)
        assert estado.velocidad == pygame.Vector2(0.0, 0.0)

    def test_posicion_infinita_devuelve_al_origen(self) -> None:
        estado = _estado(y=float("inf"))
        resolver_movimiento(estado, 0.016, [])
        assert estado.posicion == pygame.Vector2(0.0, 0.0)

    def test_devuelve_contacto_reutilizable(self) -> None:
        estado = _estado(x=float("nan"))
        contacto = resolver_movimiento(estado, 0.016, [])
        assert isinstance(contacto, Contacto)
        assert contacto.en_el_suelo is False


class TestVelocidadNoFinita:
    def test_velocidad_nan_se_corta_y_sigue(self) -> None:
        estado = _estado(vx=float("nan"), vy=float("nan"))
        resolver_movimiento(estado, 0.016, [])
        assert estado.velocidad == pygame.Vector2(0.0, 0.0)
        assert estado.posicion == pygame.Vector2(10.0, 20.0)

    def test_velocidad_infinita_se_corta(self) -> None:
        estado = _estado(vy=float("inf"))
        resolver_movimiento(estado, 0.016, [])
        assert estado.velocidad == pygame.Vector2(0.0, 0.0)


#: Un tile de suelo cualquiera. Es indispensable: el `int(posicion.x)` que
#: revienta vive **dentro** del `if solidos:`, así que un escenario sin
#: colisiones (que es como estaban escritas las pruebas de arriba) esquiva el
#: defecto por accidente y no lo mide.
SUELO = [pygame.Rect(0, 100, 64, 16)]


class TestLosPasosQueUsaElJugador:
    """AUD-355 — las mismas garantías sobre las funciones que sí se llaman.

    `player.py` nunca llama a `resolver_movimiento`: llama a estos pasos uno
    a uno. Si la verja sólo está en la fachada, el jugador sigue sin verja.
    """

    @pytest.mark.parametrize("campo", ["x", "y"])
    def test_eje_x_con_posicion_no_finita_no_lanza(self, campo: str) -> None:
        estado = _estado(**{campo: float("nan")})
        resolver_eje_x(estado, 0.016, SUELO)
        assert estado.posicion == pygame.Vector2(0.0, 0.0)
        assert estado.velocidad == pygame.Vector2(0.0, 0.0)

    @pytest.mark.parametrize("campo", ["x", "y"])
    def test_eje_y_con_posicion_no_finita_no_lanza(self, campo: str) -> None:
        estado = _estado(**{campo: float("inf")})
        resolver_eje_y(estado, 0.016, SUELO)
        assert estado.posicion == pygame.Vector2(0.0, 0.0)

    def test_eje_x_con_velocidad_no_finita_corta_la_velocidad(self) -> None:
        """NaN en la velocidad contamina la posición en cuanto se integra."""
        estado = _estado(vx=float("nan"))
        resolver_eje_x(estado, 0.016, SUELO)
        assert estado.velocidad.x == 0.0
        assert estado.posicion.x == 10.0

    def test_eje_y_con_dt_no_finito_no_integra(self) -> None:
        estado = _estado(vy=200.0)
        resolver_eje_y(estado, float("nan"), SUELO)
        assert estado.posicion.y == 20.0

    def test_repisas_con_posicion_no_finita_no_lanza(self) -> None:
        estado = _estado(x=float("nan"), vy=10.0)
        resolver_repisas(estado, [pygame.Rect(0, 100, 64, 8)])
        assert estado.posicion == pygame.Vector2(0.0, 0.0)

    def test_cuestas_con_posicion_no_finita_no_lanza(self) -> None:
        estado = _estado(y=float("nan"), vy=10.0)
        resolver_cuestas(
            estado, 0.016,
            [Pendiente(rect=pygame.Rect(0, 80, 64, 32))], Cuestas())
        assert estado.posicion == pygame.Vector2(0.0, 0.0)


class TestElSanoNoSeAltera:
    def test_dt_legitimo_integra_normal(self) -> None:
        estado = _estado(vx=10.0)
        resolver_movimiento(estado, 0.016, [])
        assert estado.posicion.x > 10.0
        assert estado.velocidad.x == 10.0

    def test_la_gravedad_no_la_pone_aqui_sino_en_su_llamante(self) -> None:
        """El resolutor integra, no aplica fuerzas: sólo la posición cambia."""
        estado = _estado(vx=0.0, vy=0.0)
        resolver_movimiento(estado, 0.016, [])
        assert estado.posicion == pygame.Vector2(10.0, 20.0)