"""AUD-577 — GAP-059, «capas de sonido natural»: el silencio de la Fase 1
deja de ser literal.

El diseño pide que la Fase 1 sea un *ancla de realidad* cuyo silencio esté
**poblado**, no vacío: *«pájaros, viento, pasos e insectos»*. La Fase 1 no
declara ningún `sonido_ambiente` a propósito (es la única de las seis), y
hasta ahora tampoco declaraba `sonidos_aislados`, así que su único canal
sonoro era la música — el silencio entre notas era silencio de verdad.

El mecanismo ya existía desde AUD-546 (`Fase.sonidos_aislados`,
`Stage4_1._actualizar_sonidos_aislados`: temporizador aleatorio + paneo
espacial); aquí sólo se usa con dos sonidos naturales que ya tiene el
proyecto: el grillo (insectos) y la ráfaga de viento (Tilarán es ventosa,
lo dice el propio nivel). Los pasos ya los pone el material «grava»
(AUD-554). Los pájaros quedan para el lote de recetas de audio
([[GAP-070]]): no existe ningún SFX de ave y generar uno nuevo es trabajo
de ese documento, no de éste.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

from tests.ayudantes_stage4_1 import construir_escena, preparar_video
from tests.test_stage4_1 import _dentro_de_la_fase, _posicionar_sin_fisica


@pytest.fixture(scope="module")
def _video():
    preparar_video()


@pytest.fixture
def escena(_video):
    sc = construir_escena()
    yield sc
    sc.on_exit()


class TestLaFase1DeclaraSonidoNatural:
    def test_la_fase_1_declara_grillos_y_viento(self) -> None:
        from src.stages.stage4_1.fases import FASES

        fase1 = FASES[0]
        assert fase1.numero == 1
        assert "sfx_environment_grillo" in fase1.sonidos_aislados, (
            "la Fase 1 sigue sin insectos: su silencio es literal, no poblado"
        )
        assert "sfx_environment_rafaga_viento" in fase1.sonidos_aislados, (
            "la Fase 1 sigue sin viento: Tilarán es ventosa, el guion lo dice"
        )

    def test_el_sonido_natural_suena_en_la_fase_1(
        self, escena, monkeypatch,
    ) -> None:
        from tests.test_gap_070_audio_del_4_1 import _espiar

        espia = _espiar(escena, monkeypatch)
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(1))
        escena._proximo_sonido_aislado = 0.0
        escena._actualizar_sonidos_aislados(0.016)

        nombres = [n for n, _v in espia.sfx]
        assert nombres, "la Fase 1 no sonó nada de sonido natural"
        assert set(nombres) <= {"sfx_environment_grillo",
                                "sfx_environment_rafaga_viento"}, (
            f"sonaron sonidos que la Fase 1 no declara: {nombres}"
        )
