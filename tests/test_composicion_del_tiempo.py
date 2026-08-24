"""
El tiempo del juego se compone; no tiene dueño.

AUD-118 y AUD-119 — el hallazgo
================================
`time_scale` era un `float` público que **dos** sistemas escribían sin saber
el uno del otro:

* el hit-stop de `CollisionSystem`, que lo pone a 0,0 al golpear;
* la cámara lenta de `TiempoBala`, que lo pone a 0,35 mientras el jugador
  mantiene el botón.

Cada uno restauraba «1,0» al terminar. Ese 1,0 es la afirmación de que nadie
más había tocado el reloj, y era falsa. Medido antes del arreglo::

    cámara lenta activa      -> time_scale = 0.35
    durante el hit-stop      -> time_scale = 0.0
    tras expirar el hit-stop -> time_scale = 1.0   <-- la cámara lenta seguía pedida

Un fotograma a velocidad completa en mitad de la cámara lenta, justo en el
instante del impacto.

En el código había **dos comentarios largos** explicando quién era el dueño de
`time_scale`, uno en cada sistema. Un problema que necesita que dos módulos se
pongan de acuerdo por comentario es un problema de diseño, no de disciplina.

El segundo defecto (AUD-119) es del mismo origen: el planificador ECS recibía
el `dt` escalado, así que el hit-stop congelaba también los bloques rítmicos,
los láseres y las plataformas móviles. Golpear a un enemigo junto a un láser
lo detenía.

Qué se prueba aquí
------------------
Que componer funciona, que nadie pisa a nadie, y que la maquinaria del nivel
distingue entre «el mundo va lento» y «hay un golpe en pantalla».
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.clock import FUENTE_HITSTOP, FUENTE_MANUAL, DeltaClock
from src.framework.stage.collision_system import CollisionSystem
from src.framework.stage.level_mechanics import FUENTE_TIEMPO_BALA, TiempoBala

DT = 1.0 / 60.0

RAIZ_DEL_PROYECTO = __import__("pathlib").Path(__file__).resolve().parent.parent


@pytest.fixture
def reloj() -> DeltaClock:
    pygame.init()
    return DeltaClock()


@pytest.fixture
def colisiones() -> CollisionSystem:
    """Sólo el temporizador de hit-stop, sin construir el sistema entero."""
    sistema = CollisionSystem.__new__(CollisionSystem)
    sistema._hitstop_timer = 0.0
    return sistema


class TestElRelojCompone:
    def test_sin_efectos_el_tiempo_corre_normal(self, reloj) -> None:
        assert reloj.time_scale == pytest.approx(1.0)
        assert reloj.escalas_activas() == {}

    def test_dos_efectos_se_multiplican(self, reloj) -> None:
        reloj.escalar("a", 0.5)
        reloj.escalar("b", 0.5)
        assert reloj.time_scale == pytest.approx(0.25)

    def test_retirar_uno_deja_el_otro(self, reloj) -> None:
        reloj.escalar("a", 0.5)
        reloj.escalar("b", 0.0)
        assert reloj.time_scale == pytest.approx(0.0)
        reloj.restaurar("b")
        assert reloj.time_scale == pytest.approx(0.5), (
            "al retirar el congelado se volvió a 1.0 en vez de a lo que "
            "quedaba pedido: es exactamente el defecto AUD-118"
        )

    def test_retirar_lo_que_no_esta_no_falla(self, reloj) -> None:
        """Un sistema que se apaga dos veces no debe reventar el reloj."""
        reloj.restaurar("no_existe")
        assert reloj.time_scale == pytest.approx(1.0)

    def test_una_escala_negativa_se_recorta_a_cero(self, reloj) -> None:
        """El tiempo hacia atrás rompe todos los integradores del juego."""
        reloj.escalar("raro", -3.0)
        assert reloj.time_scale == pytest.approx(0.0)

    def test_asignar_uno_retira_la_fuente_manual(self, reloj) -> None:
        reloj.time_scale = 0.5
        assert FUENTE_MANUAL in reloj.escalas_activas()
        reloj.time_scale = 1.0
        assert FUENTE_MANUAL not in reloj.escalas_activas(), (
            "el diccionario acumula factores neutros y el depurador miente"
        )


class TestElHitStopNoPisaALaCamaraLenta:
    """La regresión concreta, reproducida paso a paso."""

    def test_la_camara_lenta_sobrevive_a_un_golpe(self, reloj, colisiones) -> None:
        bala = TiempoBala(escala=0.35)

        for _ in range(10):
            bala.update(DT, True, reloj)
        assert reloj.time_scale == pytest.approx(0.35)

        colisiones.trigger_hitstop(0.05)
        colisiones.update_hitstop(DT, reloj)
        assert reloj.time_scale == pytest.approx(0.0), "el golpe no congela"

        for _ in range(6):                      # el hit-stop expira
            colisiones.update_hitstop(DT, reloj)
        assert reloj.time_scale == pytest.approx(0.35), (
            f"tras el hit-stop el reloj quedó en {reloj.time_scale} con la "
            f"cámara lenta todavía pedida: un fotograma a velocidad completa "
            f"en mitad de la cámara lenta, y justo en el impacto"
        )

    def test_soltar_la_camara_lenta_devuelve_el_tiempo(self, reloj) -> None:
        """El otro lado: componer no debe impedir apagar."""
        bala = TiempoBala(escala=0.35)
        for _ in range(10):
            bala.update(DT, True, reloj)
        bala.update(DT, False, reloj)
        assert reloj.time_scale == pytest.approx(1.0)
        assert FUENTE_TIEMPO_BALA not in reloj.escalas_activas()

    def test_el_hitstop_se_registra_con_su_nombre(self, reloj, colisiones) -> None:
        """Sin nombre no hay forma de excluirlo de `dt_mundo`."""
        colisiones.trigger_hitstop(0.05)
        colisiones.update_hitstop(DT, reloj)
        assert FUENTE_HITSTOP in reloj.escalas_activas()

    def test_un_reloj_de_estudiante_sin_los_metodos_sigue_funcionando(
        self, colisiones,
    ) -> None:
        """Las 26 entregas traen dobles de reloj con sólo `time_scale`.

        Romper esos dobles significaría romper las pruebas de los estudiantes
        con un cambio interno del motor, que es justo lo que este proyecto ha
        pasado el mes evitando.
        """
        class RelojDeEstudiante:
            time_scale = 1.0

        doble = RelojDeEstudiante()
        colisiones.trigger_hitstop(0.05)
        colisiones.update_hitstop(DT, doble)
        assert doble.time_scale == pytest.approx(0.0)
        for _ in range(6):
            colisiones.update_hitstop(DT, doble)
        assert doble.time_scale == pytest.approx(1.0)


class TestLaMaquinariaDelNivelIgnoraElHitStop:
    """AUD-119 — `dt_mundo`."""

    def test_el_hitstop_no_para_el_mundo(self, reloj) -> None:
        reloj.escalar(FUENTE_HITSTOP, 0.0)
        reloj._clock.tick()                     # sembrar un delta real
        reloj.tick()
        assert reloj.dt == pytest.approx(0.0), "el hit-stop debe congelar el juego"
        assert reloj.dt_mundo > 0.0, (
            "el hit-stop también paró los bloques rítmicos y los láseres: "
            "golpear a un enemigo junto a un láser lo detiene"
        )

    def test_la_camara_lenta_si_ralentiza_el_mundo(self, reloj) -> None:
        """Ralentizar el mundo es lo que la cámara lenta *es*."""
        reloj.escalar(FUENTE_TIEMPO_BALA, 0.5)
        reloj._clock.tick()
        reloj.tick()
        assert reloj.dt_mundo == pytest.approx(reloj.unscaled_dt * 0.5, rel=1e-6)

    def test_las_dos_juntas(self, reloj) -> None:
        reloj.escalar(FUENTE_TIEMPO_BALA, 0.5)
        reloj.escalar(FUENTE_HITSTOP, 0.0)
        reloj._clock.tick()
        reloj.tick()
        assert reloj.dt == pytest.approx(0.0)
        assert reloj.dt_mundo == pytest.approx(reloj.unscaled_dt * 0.5, rel=1e-6)


class TestElTopeDeFotograma:
    """`MAX_FRAME_TIME` protege de atravesar geometría tras un tirón."""

    def test_un_paron_largo_no_produce_un_delta_enorme(self, reloj) -> None:
        import time

        from src.engine.core.clock import MAX_FRAME_TIME
        reloj._clock.tick()
        time.sleep(0.12)                        # simular un tirón de 120 ms
        reloj.tick()
        assert reloj.unscaled_dt <= MAX_FRAME_TIME + 1e-9, (
            f"un parón devolvió {reloj.unscaled_dt:.3f} s de golpe: el jugador "
            f"se teletransporta a través de las paredes"
        )
        assert reloj.dt_mundo <= MAX_FRAME_TIME + 1e-9


class TestLaSuiteNoDependeDelOrden:
    """AUD-120 — `pytest tests/test_clock.py` a secas daba cuatro errores.

    `conftest._reset_global_state` corre antes de **cada** prueba y llamaba a
    `pygame.event.clear()` sin comprobar que el subsistema de vídeo estuviera
    inicializado. Con cualquier otro fichero delante pasaba, porque ese otro
    fichero inicializaba pygame de camino.

    Una suite cuyo resultado depende de qué fichero corrió antes no es una
    suite. Y lo sufre quien ejecuta una sola prueba para depurar, que es
    justo cuando menos falta hace un misterio.
    """

    def test_un_fichero_sin_video_corre_solo(self) -> None:
        """Se ejecuta `pytest` de verdad, en un proceso limpio.

        Se probó primero con `__wrapped__` sobre la fixture; si pytest dejara
        de exponer ese atributo, la expresión evaluaría a `None` y la prueba
        pasaría **sin haber comprobado nada**. Es el patrón de la prueba vacía
        que este proyecto lleva un mes retirando de otros sitios, así que aquí
        se paga el segundo de coste y se ejecuta el caso real.
        """
        import os
        import subprocess
        import sys

        entorno = dict(os.environ)
        entorno.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        resultado = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_clock.py",
             "-q", "-p", "no:cacheprovider", "--no-header", "--tb=line"],
            capture_output=True, text=True, timeout=120,
            cwd=str(RAIZ_DEL_PROYECTO), env=entorno, check=False,
        )
        assert resultado.returncode == 0, (
            "`pytest tests/test_clock.py` a secas falla; sólo pasa si otro "
            "fichero lo precede e inicializa pygame de camino:\n"
            + resultado.stdout[-1500:]
        )
