"""AUD-551 — GAP-070: lo que quedaba documentado y no construido del
documento de audio del 4-1. Ocho piezas independientes; éstas son las
seis que se pudieron construir sin necesitar una decisión de diseño
nueva ni tocar el sistema de diálogo compartido por los 26 escenarios:

1. Pasos en lodo (Fase 2) — existía la zona, no el sonido distinto.
2. Trueno sincronizado con el rayo, no instantáneo.
3. Grillos esporádicos (Fase 5).
4. Voz del Venado/Rey Terciopelo/Gavilán al liberar cada espíritu.
5. Campanilla de "paso de luz" al terminar de encender una grieta (Fase 6),
   con reverberación horneada.
6. Volumen del canto ancestral atado al ciclo lunar (Fase 5) — también en
   el bucle de ambiente, no sólo en la voz espacial que ya lo hacía.

Lo que sigue sin construir (filtro lo-fi de la lluvia en Fase 4, paneo
LFO de la tormenta en Fase 3) queda documentado en `KNOWN_GAPS.md`
GAP-070 — necesitan generar variantes de audio nuevas por fase sobre un
mismo bucle base, no un evento puntual como los seis de arriba.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
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


class _AudioEspia:
    def __init__(self) -> None:
        self.sfx: list[tuple[str, float]] = []
        self.voces: list[str] = []
        self.volumenes_de_ambiente: list[float] = []
        self.ecos: list[bool] = []
        self._ambient_active = True

    def activar_eco(self, activo: bool) -> None:
        # AUD-594 — el bus de reverberación de la Fase 6 pasa por aquí.
        self.ecos.append(bool(activo))

    def play_sfx(self, name, volume=1.0, **_k) -> None:
        self.sfx.append((name, volume))

    def play_sfx_at(self, name, world_x, screen_center_x=None, volume=1.0, **_k) -> None:
        self.sfx.append((name, volume))

    def play_voz(self, name, *_a, **_k) -> None:
        self.voces.append(name)

    def set_ambient_volume(self, volume: float) -> None:
        self.volumenes_de_ambiente.append(volume)

    def play_ambient(self, *_a, **_k) -> None:
        pass

    def crossfade_ambient(self, *_a, **_k) -> None:
        pass

    def stop_ambient(self) -> None:
        pass

    def play_music(self, *_a, **_k) -> None:
        pass

    def stop_music(self) -> None:
        pass


def _espiar(escena, monkeypatch) -> _AudioEspia:
    espia = _AudioEspia()
    monkeypatch.setattr(
        type(escena), "audio", property(lambda _self: espia), raising=False,
    )
    return espia


class TestLosPasosDeLodoSuenanDistinto:
    def test_el_evento_de_lodo_existe(self) -> None:
        from src.engine.core.events import Events

        assert hasattr(Events, "SFX_PLAYER_FOOTSTEP_LODO")

    def test_caminar_sobre_lodo_emite_el_evento_de_lodo(self, _video) -> None:
        from src.engine.core.event_bus import EventBus
        from src.engine.core.events import Events
        from src.engine.input.input_manager import InputManager
        from src.framework.entities.player import Player
        from src.framework.entities.states import WalkingState
        from src.framework.physics.perfil import MATERIALES

        bus = EventBus()
        recibidos: list[str] = []
        # El bus guarda referencias débiles a sus suscriptores — sin una
        # variable con nombre que las retenga, el recolector de basura
        # se las lleva antes de `dispatch()` (AUD-152).
        def _al_lodo(**_k):
            recibidos.append("lodo")

        def _al_generico(**_k):
            recibidos.append("generico")

        bus.subscribe(Events.SFX_PLAYER_FOOTSTEP_LODO, _al_lodo)
        bus.subscribe(Events.SFX_PLAYER_FOOTSTEP, _al_generico)

        jugador = Player(pygame.Vector2(0.0, 0.0), event_bus=bus)
        jugador._material_de_zona = MATERIALES.get("lodo")
        estado = WalkingState()
        estado._footstep_timer = 1.0  # ya vencido, el próximo update dispara

        # `InputManager` real, sin ninguna tecla pulsada — mismo criterio
        # que el resto de pruebas de estados de bajo nivel de este
        # proyecto: es más barato que replicar su interfaz entera a mano.
        estado.update(jugador, 0.016, InputManager())
        bus.dispatch()

        assert "lodo" in recibidos, "caminar en lodo no disparó el evento de lodo"
        assert "generico" not in recibidos, (
            "caminar en lodo también disparó el paso genérico — sonarán los dos a la vez"
        )


class TestElTruenoLlegaDespuesDelFlash:
    def test_el_flash_no_dispara_el_trueno_en_el_mismo_fotograma(
        self, escena, monkeypatch,
    ) -> None:
        espia = _espiar(escena, monkeypatch)
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(3))
        escena._proximo_rayo = 0.0
        escena.fase.rayos_por_minuto  # noqa: B018 — sólo confirma que hay rayos en esta fase
        escena._actualizar_rayos(0.016)

        nombres = [n for n, _v in espia.sfx]
        assert "sfx_environment_thunder" not in nombres, (
            "el trueno sonó en el mismo fotograma que el flash — debería "
            "esperar (ESPERA_DEL_TRUENO)"
        )
        assert escena._trueno_pendiente > 0.0, (
            "el flash no dejó ningún trueno pendiente"
        )

    def test_el_trueno_suena_tras_la_espera(self, escena, monkeypatch) -> None:
        espia = _espiar(escena, monkeypatch)
        escena._trueno_pendiente = 0.05
        escena._actualizar_rayos(0.1)

        nombres = [n for n, _v in espia.sfx]
        assert "sfx_environment_thunder" in nombres
        assert escena._trueno_pendiente == 0.0


class TestLosGrillosSuenanEnLaFase5:
    def test_la_fase_5_declara_el_grillo(self) -> None:
        from src.stages.stage4_1.fases import FASES

        fase5 = FASES[4]
        assert fase5.numero == 5
        assert "sfx_environment_grillo" in fase5.sonidos_aislados


class TestLaVozDeLosEspiritus:
    def test_liberar_al_venado_reproduce_su_voz_una_vez(
        self, escena, monkeypatch,
    ) -> None:
        espia = _espiar(escena, monkeypatch)
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(2))
        monkeypatch.setattr(escena, "_espiritu_liberado", lambda _fase: True)

        escena._actualizar_voz_del_espiritu()
        escena._actualizar_voz_del_espiritu()
        escena._actualizar_voz_del_espiritu()

        # AUD-554 — el Venado dejó de reusar la voz de marcador de
        # posición de AUD-263 y ganó su propia receta ("La Voz del
        # Bosque").
        assert espia.voces.count("sfx_voz_venado_ancestral") == 1, (
            f"la voz del Venado debía sonar una sola vez: {espia.voces}"
        )

    def test_cada_espiritu_tiene_una_linea_distinta(self) -> None:
        from src.stages.stage4_1.stage4_1 import Stage4_1

        voces = set(Stage4_1._VOZ_POR_ESPIRITU.values())
        assert len(voces) == 3, "dos espíritus comparten la misma línea de voz"


class TestLaCampanillaDePasoDeLuz:
    def test_una_grieta_a_maxima_intensidad_suena_una_vez(
        self, escena, monkeypatch,
    ) -> None:
        espia = _espiar(escena, monkeypatch)
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(6))
        escena._intensidad_grieta[0] = 1.0

        escena._actualizar_pasos_de_luz()
        escena._actualizar_pasos_de_luz()

        campanillas = [n for n, _v in espia.sfx if "paso_de_luz" in n]
        assert len(campanillas) == 1, (
            f"la campanilla debía sonar una sola vez mientras la grieta "
            f"siga encendida: {campanillas}"
        )

    def test_apagarse_y_reencenderse_vuelve_a_sonar(self, escena, monkeypatch) -> None:
        espia = _espiar(escena, monkeypatch)
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(6))
        escena._intensidad_grieta[0] = 1.0
        escena._actualizar_pasos_de_luz()

        escena._intensidad_grieta[0] = 0.0
        escena._actualizar_pasos_de_luz()
        escena._intensidad_grieta[0] = 1.0
        escena._actualizar_pasos_de_luz()

        campanillas = [n for n, _v in espia.sfx if "paso_de_luz" in n]
        assert len(campanillas) == 2

    def test_las_tres_notas_estan_en_re_menor(self) -> None:
        from src.stages.stage4_1.stage4_1 import Stage4_1

        assert set(Stage4_1.NOTAS_DEL_PASO_DE_LUZ) == {
            "sfx_environment_paso_de_luz_re",
            "sfx_environment_paso_de_luz_fa",
            "sfx_environment_paso_de_luz_la",
        }


class TestElCantoDeLaLunaModulaElBucleDeAmbiente:
    """GAP-070 punto 8 — antes sólo la voz espacial (`_actualizar_canto_
    ancestral`) escalaba con la luna; el bucle de fondo sonaba a volumen
    fijo todo el tramo."""

    def test_actualizar_ambiente_de_fase_llama_a_set_ambient_volume(
        self, escena, monkeypatch,
    ) -> None:
        espia = _espiar(escena, monkeypatch)
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(5))

        escena._actualizar_ambiente_de_fase()

        assert espia.volumenes_de_ambiente, (
            "la Fase 5 no ajustó el volumen del ambiente con la luna"
        )
        vol = espia.volumenes_de_ambiente[-1]
        flojo, fuerte = escena.VOLUMEN_DEL_CANTO
        assert flojo <= vol <= fuerte

    def test_fuera_de_la_fase_5_no_toca_el_volumen(self, escena, monkeypatch) -> None:
        espia = _espiar(escena, monkeypatch)
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(1))

        escena._actualizar_ambiente_de_fase()

        assert espia.volumenes_de_ambiente == []
