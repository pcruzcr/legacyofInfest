"""AUD-369: un efecto declarado crítico no puede atenuarse hasta el silencio.

El hallazgo
===========

`play_sfx_critico` (AUD-284) existe para los momentos que no se pueden perder:
la muerte de un jefe, un logro, el final de un escenario, un cambio de fase.
Hace dos cosas: **agacha la música** un 30 % durante un segundo, y reproduce el
efecto.

AUD-348 añadió después el desvanecimiento por distancia a `play_sfx_at`, que es
la ruta por la que `play_sfx_critico` reproduce cuando el evento trae posición.
Las dos son correctas por separado y juntas producen esto:

    un cambio de fase de jefe a más de RADIO_AUDIBLE_EFECTOS
      → la música se agacha
      → el efecto se atenúa a CERO
      → un segundo de música baja y ningún sonido que lo justifique

El jugador no oye «algo lejos»: oye que la música se hunde sin motivo. Es peor
que no haber hecho nada, porque el ducking anuncia un sonido que no llega.

La decisión, y por qué es un suelo y no una exención
====================================================

Lo evidente sería saltarse la atenuación para los críticos. No: entonces la
muerte de un jefe al otro extremo del mapa sonaría como si ocurriera al lado, y
el desvanecimiento de AUD-348 existe justamente porque eso molesta.

Lo correcto es un **suelo**: el crítico se aleja como cualquier otro sonido,
pero nunca por debajo de `SUELO_CRITICO`. Se sigue notando que está lejos y se
sigue oyendo que pasó. Un sonido declarado crítico que puede valer cero es una
declaración que el código no cumple.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from unittest.mock import MagicMock

import pytest

from src.engine.audio.audio_manager import (
    RADIO_AUDIBLE_EFECTOS,
    SUELO_CRITICO,
    AudioManager,
)


@pytest.fixture
def gestor():
    g = AudioManager()
    g.sound_bank = MagicMock()
    return g


def _volumen(gestor) -> float:
    """El volumen con el que se pidió el último sonido."""
    assert gestor.sound_bank.play.called, "no se reprodujo nada"
    return gestor.sound_bank.play.call_args.kwargs["volume"]


class TestElEfectoNormalSigueDesvaneciendose:
    """AUD-348 no se toca: es lo que hace que un combate lejano no aturda."""

    def test_lejos_del_todo_se_calla(self, gestor) -> None:
        gestor.play_sfx_at("x", RADIO_AUDIBLE_EFECTOS * 2.0, 0.0)
        assert _volumen(gestor) == 0.0

    def test_al_lado_suena_entero(self, gestor) -> None:
        gestor.play_sfx_at("x", 0.0, 0.0)
        assert _volumen(gestor) > 0.0


class TestElCriticoNuncaLlegaACero:

    def test_un_jefe_que_cae_lejos_se_sigue_oyendo(self, gestor) -> None:
        gestor.play_sfx_critico(
            "boss_die", world_x=RADIO_AUDIBLE_EFECTOS * 5.0, screen_center_x=0.0)
        assert _volumen(gestor) > 0.0, (
            "el efecto crítico se atenuó a cero: la música se agacha para "
            "hacerle sitio a un sonido que no llega"
        )

    def test_el_suelo_es_el_declarado(self, gestor) -> None:
        gestor.play_sfx_critico(
            "boss_die", world_x=RADIO_AUDIBLE_EFECTOS * 5.0, screen_center_x=0.0)
        assert _volumen(gestor) == pytest.approx(SUELO_CRITICO, abs=1e-6)

    def test_sigue_notandose_que_esta_lejos(self, gestor) -> None:
        """Suelo, no exención: la distancia se sigue oyendo."""
        gestor.play_sfx_critico("boss_die", world_x=0.0, screen_center_x=0.0)
        cerca = _volumen(gestor)
        gestor.sound_bank.play.reset_mock()
        gestor.play_sfx_critico(
            "boss_die", world_x=RADIO_AUDIBLE_EFECTOS * 5.0, screen_center_x=0.0)
        lejos = _volumen(gestor)
        assert lejos < cerca, (
            "con el suelo puesto, un crítico lejano suena igual que uno "
            "al lado: eso es una exención, no un suelo"
        )

    def test_un_critico_sin_posicion_no_se_atenua(self, gestor) -> None:
        """Un logro no ocurre en ningún sitio del mapa: suena entero."""
        gestor.play_sfx_critico("achievement")
        assert _volumen(gestor) > SUELO_CRITICO


class TestElSueloEsRazonable:
    def test_ni_inaudible_ni_a_todo_volumen(self) -> None:
        """0,35 es «se oye que pasó algo», no «pasó aquí».

        Por debajo de ~0,2 el efecto queda tapado por la música agachada al
        70 %, que es lo que este arreglo viene a evitar. Por encima de ~0,5
        deja de leerse como lejano.
        """
        assert 0.2 <= SUELO_CRITICO <= 0.5
