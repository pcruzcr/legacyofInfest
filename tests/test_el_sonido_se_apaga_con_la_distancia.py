"""AUD-348 — el sonido espacial se apaga con la distancia.

El hueco
--------
`play_sfx_at` movía el sonido en el estéreo (pan por X) pero no lo alejaba:
un enemigo dos pantallas a la izquierda sonaba a la misma potencia que uno a
tu lado. El pan da dirección; la mezcla no daba lejanía, y un combate con
emisores fuera de cámara se oía como una pared de ruido por encima de lo que
de verdad estaba en pantalla.

Qué fija
--------
* La atenuación es lineal con la distancia al centro de cámara y cero a
  partir del radio audible (dos pantallas y media por defecto).
* El pan no cambia: se sigue oyendo de dónde viene, más bajo.
* El volumen pedido por el emisor y el del bus siguen multiplicando igual.
"""
from __future__ import annotations

import pytest

from src.engine.audio.audio_manager import (
    RADIO_AUDIBLE_EFECTOS,
    AudioManager,
)
from src.engine.core import settings


class _BancoQueGraba:
    def __init__(self) -> None:
        self.llamadas: list[tuple[str, float, tuple[float, float]]] = []

    def play(self, name: str, volume: float = 1.0,
             pan: tuple[float, float] | None = None) -> None:
        self.llamadas.append((name, volume, pan or (1.0, 1.0)))


@pytest.fixture
def audio():
    gestor = AudioManager()
    banco = _BancoQueGraba()
    gestor.sound_bank = banco
    return gestor, banco


class TestLaAtenuacion:
    def test_centro_de_camara_suena_entero(self, audio) -> None:
        gestor, banco = audio
        centro = settings.INTERNAL_WIDTH / 2.0
        gestor.play_sfx_at("x", centro, centro)
        _, volumen, _ = banco.llamadas[0]
        assert volumen == pytest.approx(1.0)

    def test_a_media_distancia_la_mitad(self, audio) -> None:
        gestor, banco = audio
        centro = settings.INTERNAL_WIDTH / 2.0
        gestor.play_sfx_at("x", centro + RADIO_AUDIBLE_EFECTOS / 2.0, centro)
        _, volumen, _ = banco.llamadas[0]
        assert volumen == pytest.approx(0.5)

    def test_fuera_del_radio_no_se_oye(self, audio) -> None:
        gestor, banco = audio
        centro = settings.INTERNAL_WIDTH / 2.0
        gestor.play_sfx_at("x", centro + RADIO_AUDIBLE_EFECTOS * 2.0, centro)
        _, volumen, _ = banco.llamadas[0]
        assert volumen == pytest.approx(0.0)

    def test_el_volumen_pedido_se_multiplica(self, audio) -> None:
        gestor, banco = audio
        centro = settings.INTERNAL_WIDTH / 2.0
        gestor.play_sfx_at("x", centro, centro, volume=0.5)
        _, volumen, _ = banco.llamadas[0]
        assert volumen == pytest.approx(0.5)


class TestElPanNoSeToca:
    def test_lejos_y_el_pan_sigue(self, audio) -> None:
        gestor, banco = audio
        gestor.play_sfx_at("x", -2000.0, 0.0)
        _nombre, volumen, pan = banco.llamadas[0]
        assert pan[0] > pan[1]
        assert volumen < 1.0

    def test_el_radio_tiene_ensenanza_util(self) -> None:
        assert RADIO_AUDIBLE_EFECTOS > settings.INTERNAL_WIDTH
        assert RADIO_AUDIBLE_EFECTOS <= settings.INTERNAL_WIDTH * 3