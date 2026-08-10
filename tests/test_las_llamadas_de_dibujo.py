"""AUD-377 — cuántas llamadas de dibujo cuesta el fotograma. Parte de GAP-049.

El defecto
==========
Este motor mide el **tiempo** por todas partes: `DeltaClock.historial_ms`, los
cuantiles P50/P95/P99 (AUD-346), `Planificador.tiempos()` por sistema del ECS
(AUD-347), `test_frame_budget`, y dos bancos de pruebas de GPU. No medía ni un
solo **recurso**: nadie contaba cuántas llamadas de dibujo salen por fotograma.

La diferencia importa cuando algo va lento. «El fotograma cuesta 22 ms» no dice
si sobran pasadas de post-procesado o si el problema es la CPU; el número de
llamadas sí separa las dos cosas, y es la cifra que la tubería GL puede
disparar sin que se note —cada efecto encendido añade la suya— porque las
pasadas se activan por configuración, no por código nuevo.

Qué fija esta prueba
====================
Que se cuentan las pasadas que **de verdad** llegan a la tarjeta. La trampa
está en que `_run_shader_pass` se sale sin dibujar en tres casos —sin contexto,
sin VAO del programa, y sin VAO de quad—, y un contador que sume al entrar
mentiría justo cuando más importa: cuando algo no se está dibujando.
"""
from __future__ import annotations

import pytest

from src.engine.render.gl_pipeline import GLRenderer


@pytest.fixture
def renderer():
    """Un renderizador sin contexto GL: sirve para el contador, no para pintar.

    No hace falta tarjeta para comprobar la contabilidad, y no tenerla es
    justamente lo que ejercita las salidas tempranas.
    """
    return GLRenderer()


class TestElContador:
    def test_empieza_a_cero(self, renderer):
        assert renderer.llamadas_de_dibujo == 0

    def test_una_pasada_sin_contexto_no_cuenta(self, renderer):
        """Sin contexto no hay dibujo, y el contador no puede decir que sí.

        Es el caso que hace útil la cifra: si un efecto deja de pintarse, la
        consola tiene que enseñar **menos** llamadas, no las mismas.
        """
        renderer.ctx = None
        renderer._run_shader_pass(program=object(), source_tex=object())
        assert renderer.llamadas_de_dibujo == 0

    def test_el_reinicio_es_por_fotograma(self, renderer):
        """Si no se reinicia, la cifra crece sin parar y deja de significar nada."""
        renderer.llamadas_de_dibujo = 7
        renderer.reiniciar_llamadas()
        assert renderer.llamadas_de_dibujo == 0

    def test_el_lote_de_sprites_suma_una(self, renderer):
        """Un `volcar` con contenido es **una** llamada instanciada, no N.

        Ésa es la propiedad que compró AUD-340: 500 sprites en una orden. Si el
        contador sumara por sprite, el número diría lo contrario de lo que la
        instanciación consiguió.
        """
        renderer.anotar_volcado(cuantos_sprites=500)
        assert renderer.llamadas_de_dibujo == 1

    def test_un_volcado_vacio_no_suma(self, renderer):
        """`volcar` devuelve 0 y evita la llamada; el contador tiene que saberlo."""
        renderer.anotar_volcado(cuantos_sprites=0)
        assert renderer.llamadas_de_dibujo == 0


class TestLlegaALaConsola:
    """El cable trampa. El contador solo no vale de nada si nadie lo enseña.

    Es la lección de AUD-050 (`SquadBrain.stats()` se calculaba desde siempre
    «para el overlay de debug» sin un solo llamante) y de AUD-347 (los tiempos
    del ECS, medidos y nunca mostrados). Una medición sin lector es la misma
    especie de defecto que un campo sin consumidor.
    """

    def test_app_publica_las_llamadas(self):
        import inspect

        from src.engine.core.app import App

        fuente = inspect.getsource(App._draw)
        assert "llamadas_de_dibujo" in fuente, (
            "`App._draw` no publica las llamadas de dibujo: el contador existe "
            "y no lo lee nadie"
        )

    def test_app_reinicia_cada_fotograma(self):
        import inspect

        from src.engine.core.app import App

        fuente = inspect.getsource(App._draw)
        assert "reiniciar_llamadas" in fuente, (
            "nadie reinicia el contador: la cifra crece hasta el infinito"
        )
