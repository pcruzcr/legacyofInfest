"""AUD-390 — el paso fijo. Cierra GAP-036.

El defecto, que no es «falta una característica»
================================================
`App.run` integraba con `dt` variable. Eso significa que **la física del juego
depende de los fotogramas por segundo de la máquina**, y no de forma
despreciable. Simulado sobre la integración real del salto (`GRAVITY = 800`,
`PLAYER_JUMP_FORCE = -380`):

    120 fps       -> 88,67 px de ápice
     60 fps       -> 87,11 px
     30 fps       -> 84,00 px
    tope 0,05 s   -> 81,00 px   (MAX_FRAME_TIME, o sea 20 fps)
    casi continuo -> 90,06 px

Un jugador con una máquina lenta salta **un 7 % menos alto**. Los dieciséis
mapas están medidos contra los 72 px que se alcanzan a 60 fps, así que un
obstáculo ajustado al límite es franqueable o no **según el equipo**. Eso no es
una consecuencia de introducir el paso fijo: es el defecto que el paso fijo
arregla, y llevaba ahí desde el primer día.

Por qué `1/60` y no otro
========================
Porque es el valor con el que se midieron los 72 px y se diseñaron los mapas.
Con `FIXED_DT = 1/60`, a 60 fps la integración es **idéntica** a la de hoy —un
paso por fotograma, del mismo tamaño— y ningún mapa cambia. Lo que cambia es el
fotograma lento: en vez de un salto de 0,05 s se dan tres de 1/60, y el
resultado **converge** al que los mapas suponen.

Elegir cualquier otro valor obligaría a re-calibrar de verdad. Elegir éste
convierte la re-calibración en una comprobación, y esta prueba es esa
comprobación.
"""
from __future__ import annotations

import pytest

from src.engine.core import settings

GRAVEDAD = settings.GRAVITY
IMPULSO = settings.PLAYER_JUMP_FORCE


def _apice(dt: float) -> float:
    """Altura del salto con pasos de `dt`, con el orden del resolutor real.

    El resolutor aplica la gravedad y **después** integra, así que se replica
    ese orden: hacerlo al revés da otro número y la comparación no valdría.
    """
    v = IMPULSO
    h = 0.0
    while v < 0.0:
        v += GRAVEDAD * dt
        if v < 0.0:
            h += -v * dt
    return h


class TestElProblemaQueResuelve:
    def test_hoy_la_altura_depende_del_dt(self):
        """El defecto, escrito como prueba para que no se olvide por qué.

        Si algún día esto empieza a fallar es que alguien hizo la integración
        independiente del paso, y entonces sobra medio lote.
        """
        assert _apice(1 / 30) < _apice(1 / 60) < _apice(1 / 120)

    def test_la_perdida_a_20_fps_es_de_seis_pixeles(self):
        """Seis píxeles sobre 87 son más de un tercio de baldosa (16 px).

        Es el margen que separa «llegas» de «no llegas» en un salto ajustado.
        """
        perdida = _apice(1 / 60) - _apice(0.05)
        assert 5.0 < perdida < 7.0, f"la pérdida medida es {perdida:.2f} px"


class TestElReloj:
    def test_declara_el_paso_fijo(self):
        from src.engine.core import clock

        assert clock.FIXED_DT == pytest.approx(1.0 / settings.TARGET_FPS)

    def test_el_paso_fijo_conserva_la_altura_de_hoy(self):
        """**La** prueba del lote: los mapas no cambian.

        A 60 fps el paso fijo da exactamente lo mismo que el `dt` variable de
        hoy, porque es el mismo número. Por eso este cambio no re-calibra
        nada: elige el paso que los mapas ya suponían.
        """
        from src.engine.core import clock

        assert _apice(clock.FIXED_DT) == pytest.approx(_apice(1 / 60))


class TestElAcumulador:
    """Cuántos pasos da el bucle para un tiempo real dado."""

    def _pasos(self, restos: list[float]) -> list[int]:
        from src.engine.core.clock import DeltaClock

        reloj = DeltaClock()
        return [len(list(reloj.pasos_fijos(r))) for r in restos]

    def test_un_fotograma_normal_da_un_paso(self):
        assert self._pasos([1 / 60]) == [1]

    def test_un_fotograma_lento_da_varios(self):
        """Es la mitad del arreglo: el tirón se reparte en vez de integrarse
        de una vez con un `dt` enorme."""
        assert self._pasos([3 / 60])[0] == 3

    def test_un_fotograma_rapido_no_da_ninguno_y_no_pierde_tiempo(self):
        """Con 120 fps, un fotograma de cada dos no simula — y el sobrante se
        guarda. Si se tirara, el juego iría a la mitad de velocidad."""
        from src.engine.core.clock import DeltaClock

        reloj = DeltaClock()
        primero = len(list(reloj.pasos_fijos(1 / 120)))
        segundo = len(list(reloj.pasos_fijos(1 / 120)))
        assert (primero, segundo) == (0, 1), (
            "dos medios fotogramas tienen que sumar un paso: el acumulador no "
            "está guardando el sobrante"
        )

    def test_el_acumulador_no_deja_deuda_infinita(self):
        """La espiral de la muerte: si simular cuesta más que el tiempo
        simulado, el acumulador crece sin fin y el juego se congela intentando
        alcanzarse a sí mismo. El tope lo corta."""
        from src.engine.core.clock import MAX_PASOS_POR_FOTOGRAMA, DeltaClock

        reloj = DeltaClock()
        assert len(list(reloj.pasos_fijos(10.0))) <= MAX_PASOS_POR_FOTOGRAMA


class TestElBucleLoUsa:
    """El cable trampa. Sin esto el reloj es correcto y nadie lo llama."""

    def test_app_da_pasos_fijos(self):
        import inspect

        from src.engine.core.app import App

        assert "pasos_fijos" in inspect.getsource(App.run), (
            "`App.run` sigue integrando con el `dt` variable: la física del "
            "juego sigue dependiendo de los FPS de la máquina"
        )
