"""AUD-424 — el clima cambiaba de golpe: despejado a tormenta en un fotograma.

El defecto
==========
`WorldSimulation.estado()` leía la tabla directamente::

    tiempo = CLIMAS.get(self._clima, CLIMAS["clear"])
    …
    precipitacion=tiempo["precipitacion"],

Así que `set_clima("storm")` movía la precipitación de 0,0 a 1,0, las nubes de
0,05 a 1,00 y el viento de 0 a 75 px/s **entre dos fotogramas**. `docs/92` §4 lo
tenía en el Nivel 1 del catálogo —lo imprescindible— junto al cielo procedural,
y con un motivo que el propio documento explica mejor que nadie:

    Más sistemas no son más madurez. Un motor con noventa fenómenos y sin
    transiciones de clima se siente peor que uno con doce que transicionan
    bien.

Qué cambia, y qué no
====================
El **nombre** del clima sigue cambiando al instante: es la intención del
diseñador y quien pregunte «¿está lloviendo?» debe recibir la respuesta nueva
enseguida. Lo que interpola son los **valores** —precipitación, humedad,
nubes, visibilidad y viento—, que son el efecto.

Y no interpola al arrancar: una simulación recién construida nace ya con los
valores de su clima. Sin eso, todo nivel que empiece con tormenta abriría
despejado y se ensuciaría durante los primeros segundos, que es peor que el
salto que esto viene a arreglar.
"""
from __future__ import annotations

import random

import pytest

from src.framework.world.simulation import CLIMAS, WorldSimulation

#: Los campos que deben moverse suavemente.
METEO = ("precipitacion", "humedad", "cobertura_nubes", "visibilidad")


def _sim(clima: str = "clear", **kw) -> WorldSimulation:
    return WorldSimulation(clima=clima, rng=random.Random(1), **kw)


class TestArrancaEnSuSitio:
    """Lo primero que hay que no romper."""

    @pytest.mark.parametrize("clima", sorted(CLIMAS))
    def test_nace_con_los_valores_de_su_clima(self, clima: str) -> None:
        e = _sim(clima).estado()
        esperado = CLIMAS[clima]
        assert e.precipitacion == pytest.approx(esperado["precipitacion"])
        assert e.cobertura_nubes == pytest.approx(esperado["nubes"])
        assert e.visibilidad == pytest.approx(esperado["visibilidad"])

    def test_un_nivel_de_tormenta_abre_con_tormenta(self) -> None:
        """Sin esto, todo mapa con `climate=storm` empezaría despejado."""
        assert _sim("storm").estado().precipitacion == pytest.approx(1.0)


class TestLaTransicion:
    def test_el_nombre_cambia_al_instante(self) -> None:
        """La intención es inmediata; el efecto, no."""
        sim = _sim("clear")
        sim.set_clima("storm")
        assert sim.estado().clima == "storm"

    def test_los_valores_no_saltan(self) -> None:
        """El defecto: 0,0 a 1,0 de precipitación entre dos fotogramas."""
        sim = _sim("clear")
        sim.set_clima("storm")
        e = sim.estado()
        assert e.precipitacion < 0.5, (
            f"la precipitación saltó a {e.precipitacion} en el mismo fotograma "
            "del cambio: sigue sin haber transición"
        )

    def test_avanzan_hacia_el_objetivo(self) -> None:
        sim = _sim("clear")
        sim.set_clima("storm")
        antes = sim.estado().precipitacion
        sim.update(0.5)
        assert sim.estado().precipitacion > antes

    def test_llegan_al_objetivo_y_se_quedan(self) -> None:
        """La propiedad que importa: que la transición **termine**."""
        sim = _sim("clear")
        sim.set_clima("storm")
        for _ in range(600):
            sim.update(1 / 60)
        e = sim.estado()
        assert e.precipitacion == pytest.approx(1.0)
        assert e.cobertura_nubes == pytest.approx(1.0)
        sim.update(1 / 60)
        assert sim.estado().precipitacion == pytest.approx(1.0)

    def test_tambien_a_la_inversa(self) -> None:
        """De tormenta a despejado se escampa, no se corta."""
        sim = _sim("storm")
        sim.set_clima("clear")
        e = sim.estado()
        assert e.precipitacion > 0.5
        for _ in range(600):
            sim.update(1 / 60)
        assert sim.estado().precipitacion == pytest.approx(0.0)

    def test_el_viento_tambien_transiciona(self) -> None:
        """75 px/s de golpe empujan al jugador de lado sin previo aviso."""
        sim = _sim("clear")
        sim.set_clima("storm")
        primero = abs(sim.estado().viento)
        assert primero < 75.0
        for _ in range(600):
            sim.update(1 / 60)
        assert abs(sim.estado().viento) == pytest.approx(75.0, abs=0.5)

    def test_el_viento_no_cambia_de_lado_a_mitad(self) -> None:
        """La dirección se sortea al fijar el clima y se mantiene (AUD-374).

        Interpolar la magnitud no puede reintroducir el defecto que aquel lote
        arregló: una lluvia que cambia de lado sesenta veces por segundo.
        """
        sim = _sim("clear")
        sim.set_clima("storm")
        signos = set()
        for _ in range(120):
            sim.update(1 / 60)
            v = sim.estado().viento
            if v:
                signos.add(v > 0)
        assert len(signos) == 1, "el viento cambió de dirección durante la transición"

    def test_cambiar_a_mitad_de_transicion_no_estalla(self) -> None:
        """Se sale de una tormenta hacia nieve sin haber llegado a la tormenta."""
        sim = _sim("clear")
        sim.set_clima("storm")
        for _ in range(20):
            sim.update(1 / 60)
        sim.set_clima("snow")
        for _ in range(600):
            sim.update(1 / 60)
        assert sim.estado().precipitacion == pytest.approx(
            CLIMAS["snow"]["precipitacion"])


class TestLoQueNoSeRompe:
    def test_el_clima_transiciona_aunque_no_haya_ciclo_dia_noche(self) -> None:
        """Sin `day_length`, `RelojDeMundo.congelado` es True — y eso **no**
        significa «tiempo detenido».

        `congelado` sale de `duracion_dia <= 0`, que es como se declara un mapa
        **sin ciclo de día y noche**: la mayoría. La primera versión de esta
        prueba daba por hecho lo contrario y esperaba que el clima se
        congelara con él; de haberlo implementado así, la característica no
        habría funcionado en casi ningún nivel del juego.

        El clima y el reloj son dos relojes distintos y sólo uno se puede
        parar desde el mapa.
        """
        sim = _sim("clear", duracion_dia=0.0)
        assert sim.reloj.congelado, "se esperaba un reloj sin ciclo"
        sim.set_clima("storm")
        for _ in range(600):
            sim.update(1 / 60)
        assert sim.estado().precipitacion == pytest.approx(1.0), (
            "el clima no transicionó en un mapa sin ciclo de día y noche, que "
            "son la mayoría"
        )

    def test_forzar_sigue_mandando_sobre_la_transicion(self) -> None:
        """La válvula del diseñador gana, como con todo lo demás."""
        sim = _sim("clear")
        sim.set_clima("storm")
        sim.forzar(precipitacion=0.42)
        for _ in range(60):
            sim.update(1 / 60)
        assert sim.estado().precipitacion == pytest.approx(0.42)
