"""AUD-492 — el eslabón que no existía: «el escenario observa al jugador».

GAP-065 §13 mapea seis eslabones de la relación jugador↔escenario contra el
código real del 4-1 y concluye que cinco están construidos en algún grado y
uno **no existe en absoluto**: F4, *«el escenario parece observar al
jugador»*. Sus palabras: *«No existe ningún código en `stage4_1.py` que lea
la posición, la dirección o el tiempo de quietud del jugador para decidir un
evento: los gritos y la sombra del Gavilán corren en temporizadores
aleatorios, ciegos a lo que hace el jugador. El escenario no observa a
nadie — sólo parece que lo hace por casualidad temporal.»*

Su plan de resolución pone esto en el puesto (2) de prioridad, por encima
del resto, con un motivo explícito: es el único de los seis *«que hoy no
existe en absoluto, no sólo que esté incompleto»*.

Lo que se comprueba aquí
========================
Que la medida existe y es correcta (`framework.stage.atencion.Atencion`) y
—lo que de verdad importa— que el 4-1 la **usa** para decidir dos cosas que
antes decidía un dado: de qué lado suena el grito del Gavilán y cuándo
cruza su sombra.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.framework.stage.atencion import TOLERANCIA_DE_QUIETUD_PX, Atencion

# El montaje del escenario vive en un solo sitio; ver el docstring de
# `tests/ayudantes_stage4_1.py` para por qué no se comparte el fixture.
from tests.ayudantes_stage4_1 import construir_escena, preparar_video
from tests.test_stage4_1 import (
    _dentro_de_la_fase,
    _llevar_a,
    _posicionar_sin_fisica,
)


@pytest.fixture(scope="module")
def _video():
    preparar_video()


@pytest.fixture
def escena(_video):
    sc = construir_escena()
    yield sc
    sc.on_exit()


class _JugadorFalso:
    """Lo mínimo que `Atencion.observar` mira de un jugador."""

    def __init__(self, x: float = 0.0, y: float = 0.0, direccion: int = 1) -> None:
        # `x` es el **centro**, que es lo que `Atencion` mira: construir el
        # Rect con `x` de esquina desplazaba al doble medio ancho y hacía
        # fallar las cuentas de `a_su_espalda` por 8 px.
        self.rect = pygame.Rect(0, 0, 16, 32)
        self.rect.center = (int(x), int(y))
        self.facing_direction = direccion

    def mover_a(self, x: float) -> None:
        self.rect.center = (int(x), self.rect.centery)


class TestLaQuietudSeMide:
    def test_quieto_acumula_segundos(self) -> None:
        a, j = Atencion(), _JugadorFalso()
        for _ in range(60):
            a.observar(j, 1 / 60)
        assert a.quietud == pytest.approx(59 / 60, abs=1e-6), (
            "el primer fotograma es la referencia, no cuenta como quietud"
        )

    def test_moverse_rompe_la_racha(self) -> None:
        a, j = Atencion(), _JugadorFalso()
        for _ in range(60):
            a.observar(j, 1 / 60)
        assert a.quietud > 0.5
        j.mover_a(200.0)
        a.observar(j, 1 / 60)
        assert a.quietud == 0.0, "la racha no se reinició al moverse"

    def test_un_temblor_minimo_sigue_siendo_estar_quieto(self) -> None:
        """El defecto silencioso de medir la quietud con `== 0`.

        La física deja velocidad residual y una `ZonaDeViento` empuja de
        verdad: exigir un delta nulo haría que «quieto» no ocurriera nunca
        sobre terreno con viento.
        """
        a, j = Atencion(), _JugadorFalso()
        a.observar(j, 1 / 60)
        for i in range(60):
            j.mover_a(i * (TOLERANCIA_DE_QUIETUD_PX * 0.5))
            a.observar(j, 1 / 60)
        assert a.quietud > 0.5

    def test_una_pausa_corta_no_cuenta_como_detenerse(self) -> None:
        """`QUIETUD_MINIMA_S`: por debajo de eso es el tiempo entre dos
        pasos, no una decisión del jugador."""
        a, j = Atencion(), _JugadorFalso()
        for _ in range(20):  # 0,33 s
            a.observar(j, 1 / 60)
        assert not a.esta_quieto(0.1), (
            "un umbral corto no debe poder saltarse el mínimo"
        )

    def test_sin_jugador_no_acumula_quietud_falsa(self) -> None:
        a = Atencion()
        for _ in range(60):
            a.observar(None, 1 / 60)
        assert a.quietud == 0.0


class TestLaDireccionSeMide:
    def test_a_su_espalda_queda_detras(self) -> None:
        a, j = Atencion(), _JugadorFalso(x=500.0, direccion=1)
        a.observar(j, 1 / 60)
        assert a.a_su_espalda(100.0) == pytest.approx(400.0)
        j.facing_direction = -1
        a.observar(j, 1 / 60)
        assert a.a_su_espalda(100.0) == pytest.approx(600.0)

    def test_mira_hacia_responde_al_lado(self) -> None:
        a, j = Atencion(), _JugadorFalso(x=500.0, direccion=1)
        a.observar(j, 1 / 60)
        assert a.mira_hacia(900.0)
        assert not a.mira_hacia(100.0)

    def test_lo_que_queda_a_la_espalda_no_se_mira(self) -> None:
        """La propiedad que hace útil a las dos juntas: si se coloca un
        sonido con `a_su_espalda`, `mira_hacia` tiene que decir que no."""
        for direccion in (-1, 1):
            a = Atencion()
            j = _JugadorFalso(x=500.0, direccion=direccion)
            a.observar(j, 1 / 60)
            assert not a.mira_hacia(a.a_su_espalda(240.0))

    def test_girarse_reinicia_el_tiempo_mirando(self) -> None:
        a, j = Atencion(), _JugadorFalso(direccion=1)
        for _ in range(30):
            a.observar(j, 1 / 60)
        assert a.tiempo_mirando > 0.0
        j.facing_direction = -1
        a.observar(j, 1 / 60)
        assert a.tiempo_mirando == 0.0
        assert a.direccion == -1


# ── Y ahora lo que de verdad importa: que el 4-1 la use ──────────

def _fase4_tras_el_silencio(escena):
    """Deja al jugador dentro de la Fase 4, pasado ya el silencio súbito
    —antes de él, ni el grito ni la sombra tienen a qué responder."""
    from src.stages.stage4_1 import trazado
    from src.stages.stage4_1.fases import FASES

    fase4 = FASES[3]
    _llevar_a(escena, fase4.desde_columna + int(0.6 * trazado.ANCHO_SECCION))
    assert escena._shake_disparado is True
    return escena


class TestElGritoEvitaTuCampoDeVision:
    """GAP-062 puntos 17 y 19. Un grito al azar y uno que evita la mirada
    del jugador producen el mismo histograma de posiciones; sólo el
    segundo hace que el jugador se gire."""

    def test_la_mayoria_de_los_gritos_suenan_a_la_espalda(self, escena) -> None:
        _fase4_tras_el_silencio(escena)
        escena._player.facing_direction = 1
        escena._atencion.observar(escena._player, 1 / 60)
        detras = sum(
            1 for _ in range(200)
            if not escena._atencion.mira_hacia(escena._posicion_del_grito())
        )
        assert detras > 120, (
            f"sólo {detras} de 200 gritos sonaron fuera del campo de visión: "
            f"el lado sigue siendo una moneda al aire, ciega al jugador"
        )

    def test_pero_no_siempre_a_la_espalda(self, escena) -> None:
        """Una regla sin excepción se aprende y deja de inquietar."""
        _fase4_tras_el_silencio(escena)
        escena._player.facing_direction = 1
        escena._atencion.observar(escena._player, 1 / 60)
        de_frente = sum(
            1 for _ in range(200)
            if escena._atencion.mira_hacia(escena._posicion_del_grito())
        )
        assert de_frente > 10, (
            "el grito viene *siempre* por detrás: es un mecanismo que se "
            "aprende, no una presencia"
        )

    def test_girarse_cambia_de_donde_viene(self, escena) -> None:
        """La comprobación que separa «depende del jugador» de «al azar»:
        el mismo sitio del mapa, mirando al otro lado, y el grito cambia
        de lado."""
        _fase4_tras_el_silencio(escena)
        centro = escena._player.rect.centerx

        def _lado_tipico(direccion: int) -> float:
            escena._player.facing_direction = direccion
            escena._atencion.observar(escena._player, 1 / 60)
            muestras = [escena._posicion_del_grito() for _ in range(200)]
            return sum(muestras) / len(muestras) - centro

        assert _lado_tipico(1) < 0.0, "mirando a la derecha, el grito debe caer a la izquierda"
        assert _lado_tipico(-1) > 0.0, "mirando a la izquierda, el grito debe caer a la derecha"


class TestDetenerseTambienEsJugar:
    """GAP-062 puntos 24-25. `_actualizar_gradacion` dejó escrito *«el
    cambio se ve al caminar, no al esperar quieto»* — cierto en todo el
    nivel, y justo lo contrario de lo que pide la fase del bosque que
    observa."""

    def test_quedarse_quieto_adelanta_la_sombra(self, escena) -> None:
        _fase4_tras_el_silencio(escena)
        escena._sombra_progreso = -1.0
        escena._proxima_sombra = 999.0  # el temporizador ciego, muy lejos
        escena._proxima_revelacion = 0.0
        escena._atencion.reiniciar()
        for _ in range(int(escena.QUIETUD_QUE_REVELA * 60) + 30):
            escena._atencion.observar(escena._player, 1 / 60)
            escena._actualizar_quietud_del_gavilan(1 / 60)
        assert escena._sombra_progreso >= 0.0, (
            "el jugador se detuvo a mirar y el bosque no respondió"
        )

    def test_caminando_no_se_consigue(self, escena) -> None:
        """Si la revelación llegara igual andando, no sería una respuesta
        a la quietud: sería el temporizador de siempre con otro nombre."""
        _fase4_tras_el_silencio(escena)
        escena._sombra_progreso = -1.0
        escena._proxima_sombra = 999.0
        escena._proxima_revelacion = 0.0
        escena._atencion.reiniciar()
        for _ in range(int(escena.QUIETUD_QUE_REVELA * 60) + 30):
            escena._player.rect.centerx += 4
            escena._atencion.observar(escena._player, 1 / 60)
            escena._actualizar_quietud_del_gavilan(1 / 60)
        assert escena._sombra_progreso < 0.0, (
            "la sombra se adelantó sin que el jugador se detuviera"
        )

    def test_no_se_puede_ordenar_una_sombra_tras_otra(self, escena) -> None:
        """`ESPERA_TRAS_REVELAR`: sin ella, quedarse parado sería una
        fuente continua de sombras — se aprende a explotar, no a mirar."""
        _fase4_tras_el_silencio(escena)
        escena._proxima_sombra = 999.0
        escena._proxima_revelacion = 0.0
        escena._atencion.reiniciar()
        cruces = 0
        for _ in range(60 * 20):  # 20 s parado
            escena._atencion.observar(escena._player, 1 / 60)
            antes = escena._sombra_progreso
            escena._actualizar_quietud_del_gavilan(1 / 60)
            if antes < 0.0 <= escena._sombra_progreso:
                cruces += 1
            escena._actualizar_sombra_del_gavilan(1 / 60)
        assert cruces <= 2, (
            f"{cruces} sombras en 20 s parado: la quietud se volvió un grifo"
        )

    def test_antes_del_silencio_no_hay_a_que_responder(self, escena) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase4 = FASES[3]
        _llevar_a(escena, fase4.desde_columna + int(0.1 * trazado.ANCHO_SECCION))
        assert escena._shake_disparado is False
        escena._sombra_progreso = -1.0
        escena._proxima_revelacion = 0.0
        escena._atencion.reiniciar()
        for _ in range(int(escena.QUIETUD_QUE_REVELA * 60) + 30):
            escena._atencion.observar(escena._player, 1 / 60)
            escena._actualizar_quietud_del_gavilan(1 / 60)
        assert escena._sombra_progreso < 0.0


class TestLaRachaNoCruzaDeFase:
    def test_cambiar_de_fase_olvida_la_quietud(self, escena) -> None:
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(4))
        for _ in range(60 * 6):
            escena._atencion.observar(escena._player, 1 / 60)
        assert escena._atencion.quietud > 5.0
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(5))
        assert escena._atencion.quietud == 0.0, (
            "quien llegó parado al borde de la sección no ha estado "
            "observando ésta"
        )
