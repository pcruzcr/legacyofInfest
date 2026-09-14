"""
El fantasma de tu mejor carrera — AUD-142.

`GhostData` estaba escrita entera —`record`, `get_frame`, `save`, `load`,
`clear`, `frame_count`, todo correcto— y **no la llamaba nadie**: ni se
grababa ni se reproducía. El registro de huérfanos la tenía en la fila
«decidir: o se enchufa o se va».

Se enchufa, porque un fantasma es la forma más barata que existe de hacer que
repetir un nivel tenga sentido: no hace falta un adversario ni una tabla de
récords, basta con quien fuiste.

Las tres decisiones que estas pruebas defienden
------------------------------------------------
1. **Se graba a intervalo fijo, no cada fotograma.** A 60 fps un nivel de tres
   minutos serían 10.800 puntos para dibujar un muñeco, y la diferencia no se
   ve.
2. **Sólo se guarda si la carrera fue mejor.** Guardar siempre convierte el
   fantasma en «tu última partida», que es peor compañía: se persigue la mejor
   marca, no la de hace un rato.
3. **Cuando el fantasma acaba, desaparece.** Que no haya nada que dibujar es
   la información: significa que vas por detrás de tu récord.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.speedrun_mode import GhostData


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class TestGrabar:
    def test_graba_a_su_intervalo_y_no_cada_fotograma(self) -> None:
        fantasma = GhostData()
        for i in range(60):                     # un segundo a 60 fps
            fantasma.grabar_si_toca(1 / 60, i, 0)
        assert fantasma.frame_count == pytest.approx(30, abs=1), (
            f"grabó {fantasma.frame_count} muestras en un segundo; a 30 por "
            f"segundo el fantasma se ve igual y el fichero pesa la mitad"
        )

    def test_devuelve_si_grabo(self) -> None:
        fantasma = GhostData()
        assert fantasma.grabar_si_toca(1 / 60, 0, 0) is False
        assert fantasma.grabar_si_toca(1 / 30, 0, 0) is True

    def test_guarda_la_posicion_que_se_le_da(self) -> None:
        fantasma = GhostData()
        fantasma.grabar_si_toca(1.0, 123.0, 456.0)
        marco = fantasma.get_frame(0)
        assert marco["x"] == 123.0 and marco["y"] == 456.0

    def test_limpiar_borra_tambien_el_tiempo(self) -> None:
        fantasma = GhostData()
        fantasma.grabar_si_toca(1.0, 10, 10)
        fantasma.clear()
        assert fantasma.frame_count == 0
        assert fantasma.grabar_si_toca(1 / 60, 0, 0) is False


class TestReproducir:
    def _carrera(self, muestras: int = 30) -> GhostData:
        fantasma = GhostData()
        for i in range(muestras):
            fantasma.record(i * 10.0, 100.0, "")
        return fantasma

    def test_la_posicion_sigue_al_reloj(self) -> None:
        fantasma = self._carrera()
        assert fantasma.posicion_en(0.0) == (0.0, 100.0)
        assert fantasma.posicion_en(10 * GhostData.INTERVALO) == (100.0, 100.0)

    def test_cuando_la_carrera_acaba_no_hay_nada_que_dibujar(self) -> None:
        """Y eso es la información: vas por detrás de tu récord."""
        fantasma = self._carrera(muestras=10)
        assert fantasma.posicion_en(100.0) is None

    def test_una_carrera_vacia_no_dibuja_nada(self) -> None:
        assert GhostData().posicion_en(0.0) is None

    def test_la_duracion_es_la_de_la_carrera(self) -> None:
        fantasma = self._carrera(muestras=60)
        assert fantasma.duracion == pytest.approx(2.0, abs=0.05)


class TestGuardarYCargar:
    def test_va_y_vuelve(self, tmp_path) -> None:
        fantasma = GhostData()
        for i in range(10):
            fantasma.record(float(i), float(i * 2), "")
        fantasma.save(tmp_path / "g.json")

        vuelto = GhostData()
        vuelto.load(tmp_path / "g.json")
        assert vuelto.frame_count == 10
        assert vuelto.posicion_en(0.0) == (0.0, 0.0)

    def test_cargar_un_fichero_que_no_existe_no_lanza(self) -> None:
        fantasma = GhostData()
        fantasma.load("/tmp/no_existe_este_fantasma.json")
        assert fantasma.frame_count == 0

    def test_cargar_basura_no_lanza(self, tmp_path) -> None:
        """Un fichero de guardado corrupto no puede tumbar el escenario."""
        ruta = tmp_path / "roto.json"
        ruta.write_text("{{{ esto no es json", encoding="utf-8")
        fantasma = GhostData()
        fantasma.load(ruta)
        assert fantasma.frame_count == 0


class TestLaEscenaLoUsaDeVerdad:
    """La comprobación que faltaba cuando esto era un huérfano.

    Que la clase funcione no significa que la escena grabe, guarde y dibuje.
    """

    def _escena(self):
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
        from src.stages.stage_mecanicas.stage_mecanicas import StageMecanicas

        entity_factory.ensure_registered()
        ctx = GameContext(
            input_manager=InputManager(),
            audio_manager=AudioManager(),
            scene_manager=None,
            event_bus=EventBus(),
            clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        escena = StageMecanicas(ctx)
        escena.awake()
        escena.start()
        escena.on_enter()
        return escena

    def test_la_escena_graba_mientras_se_juega(self) -> None:
        escena = self._escena()
        try:
            # AUD-FANTASMA: el fantasma solo graba en Boss Rush
            from src.framework.stage.boss_rush_mode import BossRushMode, BossRushStage
            modo = BossRushMode()
            modo.add_stage(BossRushStage("test_boss", "TestBoss", lambda ctx: escena))
            modo.start()
            escena.context.boss_rush = modo
            escena._preparar_fantasma()
            assert escena._fantasma is not None, "la escena no graba nada"
            for _ in range(60):
                escena.update(1 / 60)
            assert escena._fantasma.frame_count > 0, (
                "el fantasma existe y no se graba: es lo que llevaba pasando "
                "desde que se escribió la clase"
            )
        finally:
            escena.on_exit()

    def test_dibujar_sin_carrera_previa_no_lanza(self) -> None:
        escena = self._escena()
        pantalla = pygame.display.get_surface()
        try:
            escena._fantasma_previo = None
            escena.update(1 / 60)
            escena.draw(pantalla)
        finally:
            escena.on_exit()

    def test_con_carrera_previa_se_dibuja_algo(self) -> None:
        """El lienzo es del tamaño interno del juego (800×600) y no el de la
        ventana de la prueba: con uno más pequeño el fantasma cae fuera y la
        prueba pasaría a medir el recorte, no el dibujado."""
        escena = self._escena()
        lienzo = pygame.Surface((800, 600))
        lienzo.fill((0, 0, 0))
        try:
            # AUD-FANTASMA: solo se dibuja en Boss Rush y como player transparente
            from src.framework.stage.boss_rush_mode import BossRushMode, BossRushStage
            modo = BossRushMode()
            modo.add_stage(BossRushStage("test_boss", "TestBoss", lambda ctx: escena))
            modo.start()
            escena.context.boss_rush = modo
            previo = GhostData()
            jugador = escena._player
            for _ in range(120):
                previo.record(jugador.position.x, jugador.position.y, "")
            escena._fantasma_previo = previo
            escena._dibujar_fantasma(lienzo)
            pintados = sum(
                1 for x in range(0, 800, 4) for y in range(0, 600, 4)
                if lienzo.get_at((x, y))[:3] != (0, 0, 0)
            )
            assert pintados > 0, "el fantasma no pinta nada"
        finally:
            escena.on_exit()

    def test_solo_guarda_si_la_carrera_fue_mejor(self, tmp_path) -> None:
        escena = self._escena()
        try:
            # AUD-FANTASMA: guardado solo en Boss Rush
            from src.framework.stage.boss_rush_mode import BossRushMode, BossRushStage
            modo = BossRushMode()
            modo.add_stage(BossRushStage("test_boss", "TestBoss", lambda ctx: escena))
            modo.start()
            escena.context.boss_rush = modo
            escena._ruta_del_fantasma = lambda: tmp_path / "g.json"
            mejor = GhostData()
            for i in range(5):
                mejor.record(float(i), 0.0, "")
            escena._fantasma_previo = mejor

            peor = GhostData()
            for i in range(50):
                peor.record(float(i), 0.0, "")
            escena._fantasma = peor
            escena._guardar_fantasma_si_es_mejor()
            assert not (tmp_path / "g.json").exists(), (
                "guardó una carrera peor: el fantasma pasaría a ser «tu "
                "última partida» en vez de tu mejor marca"
            )

            escena._fantasma = GhostData()
            for i in range(3):
                escena._fantasma.record(float(i), 0.0, "")
            escena._guardar_fantasma_si_es_mejor()
            assert (tmp_path / "g.json").exists()
        finally:
            escena.on_exit()
