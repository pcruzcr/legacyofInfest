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
    """El azar es estado global del proceso: se deja como estaba.

    AUD-544 — «como estaba» era sólo la mitad de la historia. Esta prueba
    existe justamente porque `random.seed()` y `np.random.seed()` son dos
    globales distintos (AUD-385, documentado en `azar.sembrar`), y este
    fixture sólo restauraba el primero. Cada `azar.sembrar(N)` de este
    fichero deja el generador de NumPy sembrado con el último `N` usado
    (4242, de `test_sembrar_escribe_la_semilla`, al ser el último en orden de
    ejecución) y **sin restaurar**, así que se filtraba al resto de la suite:
    cualquier prueba posterior que construyera un `ParticleEmitter()` sin
    generador propio heredaba ese estado, y con él una cantidad de sorteos ya
    consumidos que depende de qué otras pruebas corrieron antes en el mismo
    proceso.

    Encontrado reproduciendo `test_reported_ui_bugs.py::
    test_el_hud_conserva_su_brillo`, que fallaba sólo dentro de la suite
    completa con una razón de brillo idéntica en ejecuciones separadas
    (0,7463648122122662): esa repetibilidad exacta —no un número distinto
    cada vez, que es la firma de la carga de máquina— apuntaba a estado
    compartido, no a inestabilidad de hardware. Aislado con `pytest.main()`
    arrancando justo después de `test_sembrar_escribe_la_semilla` y
    sembrando `np.random` con 4242 a mano, las mismas 1701 pruebas
    siguientes reproducen la misma razón exacta sin tocar `random` del todo:
    la prueba nunca sembraba antes de construir su escena y heredaba
    silenciosamente cualquier estado que dejara NumPy.
    """
    import numpy as np

    previo = azar.semilla_actual()
    estado = random.getstate()
    estado_numpy = np.random.get_state()
    yield
    random.setstate(estado)
    np.random.set_state(estado_numpy)
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


class TestElOtroGeneradorGlobal:
    """AUD-385 — NumPy tiene el suyo, y `sembrar` no lo tocaba.

    AUD-375 sembró `random` y dio por reproducible el motor. No lo era: hay
    **20 usos de `np.random`**, y doce están en `vfx/particle_system.py`, que
    es quien dibuja **todas** las partículas del juego —chispas, sangre, polvo,
    lluvia—. NumPy mantiene su propio estado global, ajeno a `random.seed()`.

    O sea que la disposición de las partículas seguía siendo distinta en cada
    ejecución con la misma semilla, que es justo lo que la semilla venía a
    arreglar. Un informe de fallo con «se me cayó aquí» seguía sin poder
    repetirse si lo que fallaba dependía de dónde cayó una chispa.

    Se descubrió al ir a aislar el azar por sistema (GAP-042b) y mirar de qué
    generador tira cada módulo, en vez de fiarse del recuento de `random.*`.
    """

    def test_sembrar_fija_tambien_el_de_numpy(self):
        import numpy as np

        azar.sembrar(31415)
        primera = np.random.uniform(0, 1, 5).tolist()
        azar.sembrar(31415)
        assert np.random.uniform(0, 1, 5).tolist() == primera

    def test_dos_semillas_distintas_separan_tambien_numpy(self):
        import numpy as np

        azar.sembrar(1)
        una = np.random.uniform(0, 1, 5).tolist()
        azar.sembrar(2)
        assert np.random.uniform(0, 1, 5).tolist() != una

    def test_las_particulas_se_repiten_con_la_misma_semilla(self):
        """La consecuencia observable, sobre el sistema real.

        Es la prueba que importa: las dos de arriba pasarían con un
        `np.random.seed` puesto y nadie usándolo. Ésta ejercita
        `ParticleEmitter`, que es quien tira de NumPy doce veces.
        """
        import pygame

        from src.framework.vfx.particle_system import ParticleEmitter

        pygame.init()

        def disparo() -> list[float]:
            azar.sembrar(777)
            em = ParticleEmitter()
            em.emit_directed(
                100.0, 100.0, angle=90, speed=120, count=24, lifetime=1.0,
                size=(2, 4), color=(255, 255, 255),
            )
            n = em.count
            return [round(float(v), 6) for v in em.vx[:n]]

        assert disparo() == disparo(), (
            "dos ráfagas con la misma semilla dan partículas distintas: el "
            "azar de NumPy no está sembrado"
        )


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


class TestElFixtureNoFugaNumpy:
    """AUD-544 — cable trampa para el propio `_restaurar` de este fichero.

    Sin esto, nada impide que alguien vuelva a "simplificar" `_restaurar`
    a sólo `random.getstate()`/`setstate()` —que es exactamente el estado en
    que estaba antes de AUD-544— y la fuga a `np.random` reaparece sin que
    ninguna prueba de este fichero se entere, porque todas pasan igual: la
    fuga sólo se nota en la prueba de *otro* fichero que construya algo con
    azar de NumPy sin generador propio.
    """

    def test_restaurar_repone_tambien_el_estado_de_numpy(self):
        import numpy as np

        estado_original = np.random.get_state()

        # `__wrapped__` es la función sin envolver por `@pytest.fixture`
        # (pytest se la deja accesible ahí); se dirige a mano para probar el
        # propio fixture, no lo que otra prueba haga con él.
        gen = _restaurar.__wrapped__()
        next(gen)  # arranca el fixture: guarda el estado de numpy tal cual está aquí

        # Lo mismo que hace cualquier prueba de esta clase: resembrar y
        # gastar sorteos del generador global de NumPy.
        azar.sembrar(999999)
        np.random.uniform(0, 1, 10)

        with pytest.raises(StopIteration):
            next(gen)  # dispara el teardown del fixture

        estado_repuesto = np.random.get_state()
        assert estado_repuesto[0] == estado_original[0]
        assert np.array_equal(estado_repuesto[1], estado_original[1]), (
            "el teardown de _restaurar no repuso el vector de estado de "
            "NumPy: la semilla de esta prueba se filtra al resto de la suite"
        )
        assert estado_repuesto[2:] == estado_original[2:]

        # Deja todo como estaba antes de esta prueba; el `random` de stdlib
        # ya lo repone el `_restaurar` que pytest aplica alrededor de ésta.
        np.random.set_state(estado_original)
