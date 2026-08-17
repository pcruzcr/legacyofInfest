"""AUD-520 — 4.1c, la variante aérea del slot de la Fase 4 (AUD-518):
sin suelo salvo un colchón de contención, cruzada con plataformas
`RhythmBlock` que siguen la música de verdad. A diferencia de las otras
dos variantes, el propio nivel cambia de plantilla en cada entrada.
"""
from __future__ import annotations

import os
import sys
from itertools import pairwise
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.framework.stage.level_metrics import JumpEnvelope
from src.stages.stage4_1c import trazado
from src.stages.stage4_1c.stage4_1c import Stage4_1C


@pytest.fixture(scope="module")
def _video() -> None:
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def _construir_escena(plantilla: str):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    sc = Stage4_1C(ctx, plantilla=plantilla)
    ctx.scene_manager.push(sc)
    return sc


class TestLaRutaEsSiempreCruzable:
    """`generar_ruta` sortea con `random.Random`, pero cada hueco tiene
    que caer dentro de lo que el jugador puede saltar de verdad — no un
    número inventado, la envolvente física real (AUD-504)."""

    @pytest.mark.parametrize("semilla", [1, 2, 3, 4, 5, 42, 100, 999, 7777])
    def test_ningun_hueco_supera_la_envolvente_de_salto(self, semilla: int) -> None:
        envolvente = JumpEnvelope.from_settings()
        ruta = trazado.generar_ruta(semilla)
        for a, b in pairwise(ruta):
            hueco_h = (b.columna - (a.columna + a.ancho)) * trazado.TS
            hueco_v = abs(b.fila - a.fila) * trazado.TS
            assert hueco_h <= envolvente.max_gap_expert + 1, (
                f"semilla {semilla}: hueco horizontal {hueco_h}px entre "
                f"columna {a.columna} y {b.columna} supera el máximo "
                f"experto ({envolvente.max_gap_expert:.0f}px)"
            )
            assert hueco_v <= envolvente.max_height + 1, (
                f"semilla {semilla}: hueco vertical {hueco_v}px entre "
                f"columna {a.columna} y {b.columna} supera la altura "
                f"máxima de salto ({envolvente.max_height:.0f}px)"
            )

    @pytest.mark.parametrize("semilla", [1, 2, 3])
    def test_hay_seis_checkpoints_uno_por_seccion(self, semilla: int) -> None:
        ruta = trazado.generar_ruta(semilla)
        cps = trazado.checkpoints_de(ruta)
        assert len(cps) == 6
        secciones = {p.columna // trazado.ANCHO_SECCION for p in cps}
        assert len(secciones) == 6, "cada checkpoint debe caer en una sección distinta"

    def test_es_reproducible_con_la_misma_semilla(self) -> None:
        a = trazado.generar_ruta(123)
        b = trazado.generar_ruta(123)
        assert a == b


class TestLasTresPlantillasSiguenAtadasAlGenerador:
    @pytest.mark.parametrize("nombre", ["a", "b", "c"])
    def test_el_tmx_coincide_con_generar(self, nombre: str) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1c import PLANTILLAS, generar

        destino = (Path(__file__).resolve().parent.parent
                   / "assets" / "maps" / "stage4_1c" / f"stage4_1c_{nombre}.tmx")
        assert destino.exists(), "corre tools/generate_stage4_1c.py primero"
        actual = destino.read_text(encoding="utf-8")
        assert actual == generar(PLANTILLAS[nombre]), (
            f"{destino} está desactualizado respecto de generate_stage4_1c.py"
        )


class TestElNivelSePuedeJugar:
    @pytest.mark.parametrize("plantilla", ["a", "b", "c"])
    def test_tiene_spawn_checkpoints_y_salida(self, _video, plantilla: str) -> None:
        sc = _construir_escena(plantilla)
        try:
            assert sc._stage_data.spawn_point is not None
            assert sc._stage_data.next_trigger is not None
            assert len(sc._stage_data.checkpoints) == 6
        finally:
            sc.on_exit()

    @pytest.mark.parametrize("plantilla", ["a", "b", "c"])
    def test_los_checkpoints_brillan(self, _video, plantilla: str) -> None:
        sc = _construir_escena(plantilla)
        try:
            for cp in sc._stage_data.checkpoints:
                assert cp._light is not None
        finally:
            sc.on_exit()

    def test_tiene_reloj_musical_real(self, _video) -> None:
        """AUD-137 — sin `bpm` > 0 el reloj musical ni se monta, y sin él
        `RhythmBlock` cae al modo por segundos: dejaría de ser un nivel
        musical de verdad."""
        sc = _construir_escena("a")
        try:
            assert sc._stage_data.bpm > 0.0
            assert sc._reloj_musical is not None
        finally:
            sc.on_exit()

    def test_hay_bloques_ritmicos_que_siguen_la_musica(self, _video) -> None:
        from src.framework.ecs import BloqueRitmico

        sc = _construir_escena("a")
        try:
            bloques = [b for _eid, b in sc._mundo.cada(BloqueRitmico)]
            assert len(bloques) > 0
            assert all(b.sigue_la_musica for b in bloques)
        finally:
            sc.on_exit()

    def test_la_escena_y_el_mapa_dicen_la_misma_zona(self, _video) -> None:
        sc = _construir_escena("a")
        try:
            assert Stage4_1C.ZONE == 4
            assert sc._stage_data.zone == Stage4_1C.ZONE
        finally:
            sc.on_exit()

    def test_actualizar_no_revienta(self, _video) -> None:
        sc = _construir_escena("a")
        try:
            for _ in range(180):
                sc.update(1 / 60)
        finally:
            sc.on_exit()


class TestElegirPlantilla:
    def test_siempre_devuelve_una_plantilla_valida(self) -> None:
        for _ in range(30):
            assert Stage4_1C.elegir_plantilla() in Stage4_1C.PLANTILLAS

    def test_sin_plantilla_explicita_el_constructor_sortea_una(self, _video) -> None:
        sc = _construir_escena(plantilla=None)  # type: ignore[arg-type]
        try:
            assert sc.plantilla_activa in Stage4_1C.PLANTILLAS
        finally:
            sc.on_exit()
