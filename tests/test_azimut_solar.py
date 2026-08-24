"""AUD-399 — de qué lado viene la luz. Primer paso de GAP-051.

Qué faltaba
===========
`GAP-051` dice que el estado ambiental llega a la luz y se para ahí, y su plan
ordena los consumidores por efecto visible: **azimut solar (campo nuevo)** →
sombras dirigidas por el sol → audio → color grading. Esto es el primero, y el
propio hueco explica por qué va delante:

    `EnvironmentState` publica `altura_solar` pero **no azimut**, así que el
    dato para orientar la sombra no existe todavía. Es el único de los tres que
    necesita un campo nuevo.

Es decir: `vfx/sombras_proyectadas.py` proyecta desde un foco de luz y no desde
el sol porque **no podía**, no por descuido.

Dos decisiones que estas pruebas fijan
======================================
* El azimut sale del **mismo ángulo** que la altura —uno es el seno y el otro
  el coseno—. Con su propia fórmula habría dos modelos del sol capaces de
  desincronizarse, que es exactamente el defecto que GAP-050 documentó.
* Se publica normalizado (-1 a 1) y no en grados. El juego es 2D de perfil: lo
  único que se puede pintar de la posición del sol es hacia qué lado se alarga
  la sombra y cuánto. Un azimut en grados sería más exacto y tendría dos de sus
  tres dimensiones imposibles de dibujar aquí.
"""
from __future__ import annotations

import pytest

from src.framework.world.environment import EnvironmentState
from src.framework.world.simulation import _altura_solar, _azimut_solar


class TestElAzimut:
    def test_al_amanecer_el_sol_esta_al_este(self) -> None:
        assert _azimut_solar(6.0) == pytest.approx(-1.0)

    def test_al_atardecer_esta_al_oeste(self) -> None:
        assert _azimut_solar(18.0) == pytest.approx(1.0)

    def test_a_mediodia_esta_arriba(self) -> None:
        """Ni este ni oeste: la sombra cae a plomo."""
        assert _azimut_solar(12.0) == pytest.approx(0.0, abs=1e-9)

    def test_se_mantiene_en_el_rango(self) -> None:
        for hora in range(0, 24):
            assert -1.0 <= _azimut_solar(float(hora)) <= 1.0

    def test_sale_del_mismo_angulo_que_la_altura(self) -> None:
        """Seno y coseno del mismo ángulo: sen² + cos² = 1, a cualquier hora.

        Es la prueba que impide que alguien «mejore» uno de los dos por su
        cuenta y deje dos modelos del sol conviviendo.
        """
        for hora in (0.0, 3.5, 6.0, 9.25, 12.0, 15.0, 18.0, 21.75):
            altura, azimut = _altura_solar(hora), _azimut_solar(hora)
            assert altura ** 2 + azimut ** 2 == pytest.approx(1.0)


class TestLaDireccionDeLaSombra:
    def _estado(self, altura: float, azimut: float) -> EnvironmentState:
        return EnvironmentState(altura_solar=altura, azimut_solar=azimut)

    def test_de_noche_no_hay_sombra_solar(self) -> None:
        """El error clásico de este cálculo: pintar sombra con el sol debajo."""
        dx, largo = self._estado(-0.5, 0.5).direccion_de_sombra
        assert largo == 0.0
        assert dx == 0.0

    def test_la_sombra_va_al_lado_contrario_del_sol(self) -> None:
        """Con el sol al este (azimut negativo) la sombra se alarga al oeste."""
        dx, _ = self._estado(0.5, -1.0).direccion_de_sombra
        assert dx > 0

        dx, _ = self._estado(0.5, 1.0).direccion_de_sombra
        assert dx < 0

    def test_con_el_sol_alto_la_sombra_es_corta(self) -> None:
        _, corta = self._estado(1.0, 0.0).direccion_de_sombra
        _, larga = self._estado(0.2, -0.9).direccion_de_sombra
        assert corta < larga

    def test_el_largo_esta_acotado(self) -> None:
        """Sin tope, el largo tiende a infinito al rozar el horizonte y la
        sombra deja de leerse como sombra."""
        _, largo = self._estado(0.0001, -1.0).direccion_de_sombra
        assert largo <= 4.0

    def test_justo_en_el_horizonte_no_divide_entre_cero(self) -> None:
        assert self._estado(0.0, -1.0).direccion_de_sombra == (0.0, 0.0)


def test_la_simulacion_publica_el_azimut() -> None:
    """El cable trampa: que el campo llegue al estado que leen los consumidores.

    Sin esto, `_azimut_solar` sería una función correcta que nadie llama — el
    modo de fallo de esta casa, y justamente lo que GAP-051 registra que pasó
    con la mitad productora de `world/`.
    """
    from src.framework.world.simulation import WorldSimulation

    sim = WorldSimulation()
    estado = sim.estado()
    assert hasattr(estado, "azimut_solar")
    assert -1.0 <= estado.azimut_solar <= 1.0
