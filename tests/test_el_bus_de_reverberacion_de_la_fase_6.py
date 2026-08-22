"""AUD-594 — GAP-070 punto 7: el bus de reverberación de la Fase 6.

La receta del dueño pide que *todo* lo que suene en la Fase 6 lleve la
reverberación del espacio sagrado — un «bus» de reverb. Este motor no tiene
DSP en tiempo real (`_aplicar_reverberacion` lo explica desde AUD-515), así
que el bus se aproxima como manda el propio GAP-070: **horneando** variantes
`_con_eco` de los sonidos compartidos y haciendo que `AudioManager` prefiera
la variante cuando una escena enciende el bus. La Fase 6 lo enciende al
entrar y lo apaga al salir de ella (y del nivel).
"""
from __future__ import annotations

import os
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pathlib import Path

import pytest

from src.engine.core import settings
from tests.ayudantes_stage4_1 import construir_escena, preparar_video
from tests.test_stage4_1 import _dentro_de_la_fase, _llevar_a

#: Los sonidos compartidos que suenan durante el recorrido de la Fase 6 y
#: tienen variante con eco horneada.
BASES_DEL_BUS = (
    ("player", "jump"), ("player", "land"), ("player", "crouch"),
    ("player", "short_attack"), ("player", "long_attack"),
    ("player", "hit_connect"), ("player", "hurt"), ("ui", "checkpoint"),
)


def _duracion(ruta: Path) -> float:
    with wave.open(str(ruta), "rb") as wf:
        return wf.getnframes() / wf.getframerate()


@pytest.fixture(scope="module")
def _video():
    preparar_video()


class TestElBusPrefiereLaVarianteConEco:
    @pytest.fixture
    def mgr(self, _video):
        from src.engine.audio.audio_manager import AudioManager

        return AudioManager()

    def _nombres_tocados(self, mgr, monkeypatch):
        tocados: list[str] = []
        monkeypatch.setattr(
            mgr.sound_bank, "play",
            lambda name, **k: tocados.append(name),
        )
        return tocados

    def test_con_el_bus_activo_suenan_las_variantes(self, mgr, monkeypatch) -> None:
        tocados = self._nombres_tocados(mgr, monkeypatch)
        mgr.activar_eco(True)
        mgr.play_sfx("sfx_player_jump")
        assert tocados == ["sfx_player_jump_con_eco"]

    def test_sin_bus_suenan_los_originales(self, mgr, monkeypatch) -> None:
        tocados = self._nombres_tocados(mgr, monkeypatch)
        mgr.activar_eco(True)
        mgr.activar_eco(False)
        mgr.play_sfx("sfx_player_jump")
        assert tocados == ["sfx_player_jump"]

    def test_un_sonido_sin_variante_cae_al_original(self, mgr, monkeypatch) -> None:
        """El bus es una preferencia, no una exigencia: si un sonido no
        tiene `_con_eco`, suena el de siempre."""
        tocados = self._nombres_tocados(mgr, monkeypatch)
        mgr.activar_eco(True)
        mgr.play_sfx("sfx_bosses_phase_change")
        assert tocados == ["sfx_bosses_phase_change"]

    def test_el_bus_direccional_tambien_pasa_por_el_eco(self, mgr, monkeypatch) -> None:
        tocados = self._nombres_tocados(mgr, monkeypatch)
        mgr.activar_eco(True)
        mgr.play_sfx_at("sfx_player_hurt", world_x=100.0)
        assert tocados == ["sfx_player_hurt_con_eco"]


class TestLasVariantesEstanHorneadas:
    @pytest.mark.parametrize("categoria,base", list(BASES_DEL_BUS))
    def test_la_variante_dura_mas_que_el_original(
        self, categoria: str, base: str,
    ) -> None:
        """La cola de ecos añade tiempo: la variante no puede durar lo
        mismo que el seco."""
        sdir = settings.ASSETS_DIR / "sfx" / categoria
        seco = sdir / f"sfx_{categoria}_{base}.wav"
        con_eco = sdir / f"sfx_{categoria}_{base}_con_eco.wav"
        assert seco.exists(), f"falta el original {seco.name}"
        assert con_eco.exists(), f"falta hornear {con_eco.name}"
        assert _duracion(con_eco) > _duracion(seco) + 0.3, (
            f"{con_eco.name} dura lo mismo que el seco: no lleva cola de eco"
        )


class TestLaFase6ManejaElBus:
    def test_al_cruzar_a_la_fase_6_el_bus_se_enciende(self, _video) -> None:
        sc = construir_escena()
        try:
            _llevar_a(sc, _dentro_de_la_fase(6) + 2)
            assert sc.audio.eco_activo is True
        finally:
            sc.on_exit()

    def test_volver_a_una_fase_anterior_lo_apaga(self, _video) -> None:
        sc = construir_escena()
        try:
            _llevar_a(sc, _dentro_de_la_fase(6) + 2)
            _llevar_a(sc, _dentro_de_la_fase(1) + 2)
            assert sc.audio.eco_activo is False
        finally:
            sc.on_exit()

    def test_salir_del_nivel_lo_deja_apagado(self, _video) -> None:
        """El bus es global del mezclador: si el nivel muere dentro de la
        Fase 6, el eco no puede colarse en la escena siguiente."""
        sc = construir_escena()
        _llevar_a(sc, _dentro_de_la_fase(6) + 2)
        assert sc.audio.eco_activo is True
        sc.on_exit()
        assert sc.audio.eco_activo is False
