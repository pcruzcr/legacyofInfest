"""AUD-284 — el *ducking* estaba entero y sólo lo disparaba la voz.

El hueco
--------
`mixer_buses.py` sabe apartar la música desde AUD-144, y el único que lo pedía
era `play_voz`. O sea: en el momento más ruidoso de la partida —un jefe que cae,
un logro, el final del escenario— la música seguía a todo volumen encima del
sonido que anunciaba justo eso. El mecanismo escrito y desconectado por un
extremo, otra vez.

Las dos decisiones que hay que defender
---------------------------------------
1. **Un efecto crítico baja la música un 30 %, no al 35 % como una voz.** Bajo
   una línea de diálogo la música estorba; bajo un jefe que cae la música *es*
   el momento. Se le hace hueco, no se la apaga.
2. **Gana el duck más profundo.** Si la muerte de un jefe subiera la música por
   encima de la línea que está sonando, el diálogo se perdería.
"""
from __future__ import annotations

import pytest

from src.engine.audio.mixer_buses import (
    BUS_MUSICA,
    DUCK_NIVEL,
    DUCK_NIVEL_EFECTO,
    Mezclador,
)


@pytest.fixture
def mezcla() -> Mezclador:
    return Mezclador()


def _asentar(mezcla: Mezclador, segundos: float = 2.0) -> None:
    """Corre el duck hasta que deja de moverse."""
    for _ in range(int(segundos / 0.016)):
        mezcla.update(0.016)


class TestLaProfundidad:
    def test_una_voz_baja_al_nivel_de_voz(self, mezcla) -> None:
        mezcla.agachar_musica(1.0)
        _asentar(mezcla, 0.5)
        assert mezcla.factor_de_duck == pytest.approx(DUCK_NIVEL, abs=0.01)

    def test_un_efecto_baja_mucho_menos(self, mezcla) -> None:
        mezcla.agachar_musica(1.0, nivel=DUCK_NIVEL_EFECTO)
        _asentar(mezcla, 0.5)
        assert mezcla.factor_de_duck == pytest.approx(DUCK_NIVEL_EFECTO, abs=0.01)

    def test_el_efecto_es_un_30_por_ciento(self) -> None:
        """La cifra de la propuesta, fijada para que nadie la mueva a ojo."""
        assert DUCK_NIVEL_EFECTO == pytest.approx(0.70)

    def test_y_la_ganancia_de_la_musica_lo_refleja(self, mezcla) -> None:
        antes = mezcla.ganancia(BUS_MUSICA)
        mezcla.agachar_musica(1.0, nivel=DUCK_NIVEL_EFECTO)
        _asentar(mezcla, 0.5)
        assert mezcla.ganancia(BUS_MUSICA) < antes


class TestGanaElMasProfundo:
    def test_un_efecto_no_levanta_la_voz(self, mezcla) -> None:
        mezcla.agachar_musica(2.0)                            # voz
        mezcla.agachar_musica(1.0, nivel=DUCK_NIVEL_EFECTO)   # efecto encima
        _asentar(mezcla, 0.5)
        assert mezcla.factor_de_duck == pytest.approx(DUCK_NIVEL, abs=0.01), (
            "un efecto crítico levantó la música por encima del diálogo que "
            "estaba sonando"
        )

    def test_una_voz_sí_profundiza_un_efecto(self, mezcla) -> None:
        mezcla.agachar_musica(2.0, nivel=DUCK_NIVEL_EFECTO)
        mezcla.agachar_musica(2.0)
        _asentar(mezcla, 0.5)
        assert mezcla.factor_de_duck == pytest.approx(DUCK_NIVEL, abs=0.01)

    def test_al_soltar_se_olvida_la_profundidad(self, mezcla) -> None:
        """Un nivel que sobrevive a su duck decide el siguiente."""
        mezcla.agachar_musica(0.1, nivel=DUCK_NIVEL_EFECTO)
        _asentar(mezcla, 3.0)
        assert mezcla.factor_de_duck == pytest.approx(1.0, abs=0.01)
        mezcla.agachar_musica(1.0)
        _asentar(mezcla, 0.5)
        assert mezcla.factor_de_duck == pytest.approx(DUCK_NIVEL, abs=0.01)

    def test_la_musica_vuelve_sola(self, mezcla) -> None:
        mezcla.agachar_musica(0.2, nivel=DUCK_NIVEL_EFECTO)
        _asentar(mezcla, 3.0)
        assert mezcla.factor_de_duck == pytest.approx(1.0, abs=0.01)


class TestQuienLoDispara:
    def test_la_lista_de_criticos_es_corta(self) -> None:
        """El ducking funciona porque es raro: si lo pidiera cada golpe, el
        bombeo se oiría más que los propios efectos."""
        from src.framework.scenes.stage_parts.senales import EVENTOS_CRITICOS

        assert 0 < len(EVENTOS_CRITICOS) <= 6

    def test_la_muerte_de_un_enemigo_no_esta(self) -> None:
        """Mueren a docenas."""
        from src.engine.core.events import Events
        from src.framework.scenes.stage_parts.senales import EVENTOS_CRITICOS

        assert Events.SFX_ENEMY_DIE_SMALL not in EVENTOS_CRITICOS
        assert Events.SFX_HIT_CONNECT not in EVENTOS_CRITICOS

    def test_el_logro_y_el_fin_de_escenario_si(self) -> None:
        from src.engine.core.events import Events
        from src.framework.scenes.stage_parts.senales import EVENTOS_CRITICOS

        assert Events.ACHIEVEMENT_UNLOCKED in EVENTOS_CRITICOS
        assert Events.SFX_STAGE_COMPLETE in EVENTOS_CRITICOS


class TestElCableado:
    """El defecto era que el mecanismo no tenía quien lo pidiera."""

    def test_el_gestor_de_audio_expone_el_efecto_critico(self) -> None:
        from src.engine.audio.audio_manager import AudioManager

        assert hasattr(AudioManager, "play_sfx_critico")

    def test_y_agacha_la_musica_al_llamarlo(self) -> None:
        from src.engine.audio.audio_manager import AudioManager

        audio = AudioManager()
        assert audio.mezcla.factor_de_duck == pytest.approx(1.0)
        audio.play_sfx_critico("sfx_ui_stage_complete")
        _asentar(audio.mezcla, 0.5)
        assert audio.mezcla.musica_agachada, (
            "play_sfx_critico no agachó la música: el ducking sigue siendo "
            "sólo para la voz"
        )

    def test_la_escena_marca_los_criticos_al_suscribir(self) -> None:
        import inspect

        from src.framework.scenes.stage_parts import senales

        fuente = inspect.getsource(senales)
        assert "critico=evt in EVENTOS_CRITICOS" in fuente
