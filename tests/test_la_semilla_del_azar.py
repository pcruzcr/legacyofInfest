"""AUD-375 — el motor no podía repetir una partida. Primer trozo de GAP-042.

El defecto
==========
No había **una sola** llamada a `random.seed()` en `src/engine` ni en
`src/framework`. Las 46 llamadas a `random.*` del motor —partículas, sacudida
de cámara, dispersión de disparos, clima, comportamiento de enemigos— tiraban
del generador global sin sembrar, así que dos ejecuciones del mismo escenario
nunca coinciden.

Lo que eso cuesta, con nombres:

* **AUD-359** — «la prueba de presupuesto del 4-1 fallaba por el azar de una
  sola muestra». Una prueba que no puede fijar el azar se escribe tolerante, y
  una prueba tolerante deja pasar regresiones pequeñas.
* **Los informes de fallo no se pueden reproducir.** «Se me cayó en el acto
  IV» no basta si la disposición de las partículas, el momento del rayo y la
  decisión del enemigo eran distintos esa vez.
* **El fantasma del speedrun** no se puede validar contra una repetición.

Qué entrega este lote
=====================
La semilla del proceso: quién la fija, cómo se repite y —lo que la hace útil
desde el primer día— que **quede escrita en el registro**, para que un informe
de fallo la lleve encima sin que el jugador tenga que saber qué es.

Lo que NO entrega, y está anotado en GAP-042: convertir las 46 llamadas para
que cada sistema reciba su generador. Eso es auditar uso por uso y va por
lotes; sembrar el global es lo que hace que el trabajo de después sea
verificable.
"""
from __future__ import annotations

import random

import pytest

from src.engine.core import azar


@pytest.fixture(autouse=True)
def _restaurar():
    """El azar es estado global del proceso: se deja como estaba."""
    previo = azar.semilla_actual()
    estado = random.getstate()
    yield
    random.setstate(estado)
    azar._semilla = previo


class TestSembrar:
    def test_sembrar_fija_la_secuencia(self):
        azar.sembrar(1234)
        primera = [random.random() for _ in range(5)]
        azar.sembrar(1234)
        assert [random.random() for _ in range(5)] == primera

    def test_dos_semillas_distintas_dan_secuencias_distintas(self):
        azar.sembrar(1)
        una = [random.random() for _ in range(5)]
        azar.sembrar(2)
        assert [random.random() for _ in range(5)] != una

    def test_sin_semilla_se_inventa_una_y_la_recuerda(self):
        """Sin semilla explícita hay azar de verdad, pero **anotado**.

        Es la diferencia entre no ser determinista y no saber qué pasó: la
        partida de un jugador no debe salir siempre igual, y aun así el
        informe de su fallo tiene que poder repetirse.
        """
        elegida = azar.sembrar(None)
        assert isinstance(elegida, int)
        assert azar.semilla_actual() == elegida

        primera = [random.random() for _ in range(5)]
        azar.sembrar(elegida)
        assert [random.random() for _ in range(5)] == primera

    def test_la_semilla_inventada_no_es_siempre_la_misma(self):
        semillas = {azar.sembrar(None) for _ in range(8)}
        assert len(semillas) > 1, (
            f"ocho arranques dieron la misma semilla: {semillas}"
        )

    def test_generador_propio_no_toca_el_global(self):
        """Para un sistema que quiera el suyo sin arrastrar al resto.

        Es el camino por el que van a ir las 46 conversiones de GAP-042:
        `WorldSimulation` ya lo usa (AUD-374).
        """
        azar.sembrar(7)
        esperado = [random.random() for _ in range(3)]

        azar.sembrar(7)
        propio = azar.generador(99)
        [propio.random() for _ in range(10)]
        assert [random.random() for _ in range(3)] == esperado, (
            "usar un generador propio movió el generador global"
        )

    def test_el_generador_propio_es_reproducible(self):
        assert [azar.generador(5).random() for _ in range(3)] == [
            azar.generador(5).random() for _ in range(3)
        ]


class TestLaSemillaLlegaAlRegistro:
    """Lo que convierte esto en herramienta y no en apunte.

    Un informe de fallo sirve si trae la semilla. El jugador no sabe qué es
    una semilla, así que la escribe el motor.
    """

    def test_sembrar_escribe_la_semilla(self, caplog):
        import logging

        with caplog.at_level(logging.INFO, logger=azar.__name__):
            azar.sembrar(4242)
        assert "4242" in caplog.text, (
            f"la semilla no aparece en el registro: {caplog.text!r}"
        )

    def test_el_arranque_del_motor_siembra(self):
        """El cable trampa: si `App` deja de sembrar, esto se pone rojo."""
        import inspect

        from src.engine.core.app import App

        fuente = inspect.getsource(App._init_subsystems)
        assert "sembrar" in fuente, (
            "`App._init_subsystems` ya no siembra el azar: el motor vuelve a "
            "no poder repetir una partida"
        )

    def test_se_siembra_despues_de_configurar_el_registro(self):
        """El orden importa, y por un motivo concreto.

        La semilla se escribe **en** el registro. Sembrar antes de
        configurarlo tira la única línea que hace reproducible un informe, y
        el defecto sería invisible: todo funciona, sólo que el fichero no
        tiene el número.
        """
        import inspect

        from src.engine.core.app import App

        fuente = inspect.getsource(App._init_subsystems)
        assert fuente.index("configurar_registro") < fuente.index("sembrar")


class TestLaOtraMitad:
    """Una semilla que no se puede devolver no sirve de nada."""

    def test_la_bandera_existe(self):
        import inspect

        import main

        fuente = inspect.getsource(main._parse_args)
        assert "--semilla" in fuente, (
            "el motor anota la semilla y no hay forma de volver a pasarla"
        )

    def test_todas_las_rutas_de_arranque_la_pasan(self):
        """Tres formas de arrancar: normal, `--stage` y `--boss`.

        Si una se olvida, repetir un fallo funciona en unos modos y en otros
        no, que es peor que no tenerlo — se diagnostica como «no se
        reproduce».
        """
        import pathlib

        fuente = pathlib.Path("main.py").read_text(encoding="utf-8")
        assert fuente.count("semilla=args.semilla") == 3, (
            "alguna ruta de arranque construye `App` sin pasarle la semilla"
        )
