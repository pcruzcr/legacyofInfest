"""AUD-519 — 4.1b, la variante acuática del slot de la Fase 4 (AUD-518).
Misma travesía horizontal que el 4-1, sumergida, con un pez abismal que
aparece y persigue sin poder tocar ni ser tocado.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pathlib import Path

import pygame
import pytest

from src.stages.stage4_1b import trazado


@pytest.fixture(scope="module")
def _video() -> None:
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def _construir_escena():
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory
    from src.stages.stage4_1b.stage4_1b import Stage4_1B

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    sc = Stage4_1B(ctx)
    ctx.scene_manager.push(sc)
    return sc


@pytest.fixture
def escena(_video):
    sc = _construir_escena()
    try:
        yield sc
    finally:
        sc.on_exit()


class TestElTrazadoTieneElMismoLargoQueElCementerio:
    def test_mismas_dimensiones_que_stage4_1(self) -> None:
        from src.stages.stage4_1 import trazado as trazado_4_1

        assert trazado.MW == trazado_4_1.MW
        assert trazado.MH == trazado_4_1.MH
        assert trazado.TS == trazado_4_1.TS

    def test_seis_secciones(self) -> None:
        assert trazado.MW == trazado.ANCHO_SECCION * 6

    def test_hay_seis_checkpoints_uno_por_fase(self) -> None:
        """Misma densidad y mismo motivo que AUD-516 en el 4-1: un
        escenario psicológico de terror no reaparece casi al instante."""
        puntos = trazado.checkpoints()
        assert len(puntos) == 6
        fases_cubiertas = {trazado.fase_de_la_columna(c) for c, _f in puntos}
        assert fases_cubiertas == {1, 2, 3, 4, 5, 6}


class TestElMapaSigueAtadoASuGenerador:
    def test_el_tmx_coincide_con_generar(self) -> None:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1b import DESTINO, generar

        assert DESTINO.exists(), "corre tools/generate_stage4_1b.py primero"
        actual = DESTINO.read_text(encoding="utf-8")
        assert actual == generar(), (
            "assets/maps/stage4_1b/stage4_1b.tmx está desactualizado respecto "
            "de tools/generate_stage4_1b.py — corre el generador de nuevo"
        )


class TestElNivelSePuedeJugar:
    def test_tiene_spawn_checkpoints_y_salida(self, escena) -> None:
        assert escena._stage_data.spawn_point is not None
        assert escena._stage_data.next_trigger is not None
        assert len(escena._stage_data.checkpoints) == 6

    def test_los_checkpoints_brillan(self, escena) -> None:
        """AUD-517 — pedido explícito para 4.1b/4.1c: un área que brilla,
        no el sprite/rectángulo de siempre."""
        for cp in escena._stage_data.checkpoints:
            assert cp._light is not None

    def test_el_agua_se_ve_no_solo_se_siente(self, escena) -> None:
        """AUD-525: `ZonaDeAgua` es la física (nado, oxígeno, corriente) y
        `WaterEffect` es lo que se ve — van por separado a propósito
        (`water_effect.py`), y el TMX nunca encendió el segundo. El nivel se
        jugaba sumergido de verdad y se veía completamente seco: sin tinte,
        sin ondas, nada distinguía la fosa de caminar al aire libre.
        """
        datos = escena._stage_data
        assert datos.water_effect is True, (
            "stage4_1b está sumergido de principio a fin y no enciende "
            "WaterEffect — el agua no tiene ningún rastro visual"
        )

    def test_hay_faroles_declarados(self, escena) -> None:
        """AUD-531 — pedido: "lámparas que iluminen hacia el agua... un
        límite visual inalcanzable"."""
        assert len(escena._stage_data.lights) >= 6, (
            "4.1b no declara faroles — el techo de la fosa no tiene "
            "ningún límite visual"
        )

    def test_el_fondo_no_es_negro_puro(self, escena) -> None:
        """AUD-531 — `LightSystem.render` compone con `BLEND_RGB_MULT`:
        multiplicar por un multiplicador de luz sobre negro puro sigue
        dando negro puro (0 × n = 0). Sin un fondo pintado, los faroles
        estaban calculados correctamente y eran invisibles igual —
        comprobado jugando, no una hipótesis."""
        assert escena._fondo_cueva.get_at((0, 0))[:3] != (0, 0, 0)

    def test_el_farol_se_nota_en_el_fotograma_compuesto(self, escena) -> None:
        """No basta con que el sistema de luces calcule el foco — tiene
        que sobrevivir hasta el píxel final, con fondo pintado debajo."""
        import pygame

        escena._camera.offset.x = 0.0
        escena._camera.offset.y = 0.0
        for _ in range(30):
            escena.update(1 / 60)
            escena._camera.offset.x = 0.0
            escena._camera.offset.y = 0.0

        lienzo = pygame.Surface((800, 600))
        escena.draw(lienzo)

        primer_farol = escena._stage_data.lights[0]
        fx, fy = int(primer_farol.position[0]), int(primer_farol.position[1])
        cerca = lienzo.get_at((fx, fy))
        lejos = lienzo.get_at((min(fx + 400, 799), fy))
        assert sum(cerca[:3]) > sum(lejos[:3]), (
            f"el píxel junto al farol ({tuple(cerca)}) no es más claro que "
            f"uno lejos de cualquier luz ({tuple(lejos)})"
        )

    def test_la_zona_de_agua_cubre_la_columna_por_encima_del_lecho(self, escena) -> None:
        from src.framework.ecs import ZonaDeAgua

        zonas = [z for _eid, z in escena._mundo.cada(ZonaDeAgua)]
        assert len(zonas) >= 1
        zona = zonas[0]
        assert zona.rect.width >= trazado.MW * trazado.TS - trazado.MURO_ANCHO * trazado.TS * 2
        assert zona.rect.bottom <= trazado.FILA_SUELO * trazado.TS

    def test_la_escena_y_el_mapa_dicen_la_misma_zona(self, escena) -> None:
        from src.stages.stage4_1b.stage4_1b import Stage4_1B

        assert Stage4_1B.ZONE == 4
        assert escena._stage_data.zone == Stage4_1B.ZONE


class TestElPezAbismal:
    def test_no_aparece_antes_del_respiro_inicial(self, escena) -> None:
        from src.stages.stage4_1b.stage4_1b import Stage4_1B

        margen = 1.0
        for _ in range(int((Stage4_1B.ESPERA_ANTES_DE_LA_PRIMERA - margen) * 60)):
            escena.update(1 / 60)
        assert escena._pez is None

    def test_aparece_persigue_y_se_va_sin_dejar_fuga(self, escena) -> None:
        apariciones = 0
        estaba_activo = False
        for _ in range(3600):  # 60 s de juego
            escena.update(1 / 60)
            activo = escena._pez is not None
            if activo and not estaba_activo:
                apariciones += 1
            estaba_activo = activo
        assert apariciones >= 1, "en 60 s debería haber aparecido al menos una vez"
        assert escena._pez is None or escena._pez.is_alive
        # Nada de peces fantasma acumulados en la lista de entidades.
        from src.framework.entities.enemy_pez_abismal import EnemyPezAbismal

        peces_en_la_lista = [
            e for e in escena._stage_data.entity_list
            if isinstance(e, EnemyPezAbismal)
        ]
        assert len(peces_en_la_lista) <= 1

    def test_el_pez_no_hace_dano_al_jugador(self, escena) -> None:
        """Pedido explícito: que no lo mate ni lo toque."""
        from src.framework.entities.enemy_pez_abismal import EnemyPezAbismal

        pez = EnemyPezAbismal(pygame.Vector2(escena._player.rect.center))
        assert pez.damage_on_contact == 0.0


class TestElAhogamientoNoAplicaEnUnNivelSinSuperficie:
    """AUD-572 — reporte jugando: "los enemigos hacen daño... la idea es
    que no hagan daño". El pez no hace daño (arriba); lo que sí lo hacía
    era `ControlDeNado`, con su límite de aire de fábrica (30s, pensado
    para una zambullida breve con superficie a la que volver). 4-1b está
    "sumergido de principio a fin" — sin ningún punto donde `en_agua()`
    dé `None` — así que el jugador nunca podía recuperar aire y el
    ahogamiento era sólo cuestión de tiempo, sin ningún enemigo de por
    medio. La ficha ya pedía "Límite de tiempo: sin límite"."""

    def test_el_dano_por_ahogamiento_esta_apagado(self, escena) -> None:
        assert escena._nado.dano_por_segundo == 0.0

    def test_flotar_mucho_mas_de_treinta_segundos_no_quita_vida(self, escena) -> None:
        """30s es el límite de aire de fábrica (`ControlDeNado.aire_
        maximo`) — antes de este cambio, a partir de ahí se perdía vida
        sin parar. Se simulan 90s quieto en el agua, el triple."""
        vida_inicial = escena._player.current_health
        dt = 1 / 60
        for _ in range(90 * 60):
            escena.update(dt)
        assert escena._player.current_health == vida_inicial


class TestLasCorrientesDeAgua:
    """AUD-543 — «corrientes de agua», pedido tras jugarlo.
    `ZonaDeAgua.corriente` existía en el motor y ningún nivel lo declaraba.
    Los números de `trazado.ZONAS_DE_CORRIENTE` están verificados por
    simulación (ver el comentario junto a la constante), no a ojo: esta
    clase fija esa evidencia en una prueba, para que quien cambie la
    magnitud tenga que volver a medir, no volver a adivinar.
    """

    def test_hay_al_menos_una_zona_a_favor_y_una_en_contra(self) -> None:
        signos = {1 if fx > 0 else -1 for _, _, fx in trazado.ZONAS_DE_CORRIENTE}
        assert signos == {1, -1}, (
            "las corrientes son todas del mismo signo: no hay variedad de "
            "ritmo (empuje/resistencia) a lo largo del nivel"
        )

    def test_las_zonas_caen_dentro_del_mapa(self) -> None:
        for col_ini, col_fin, _fx in trazado.ZONAS_DE_CORRIENTE:
            assert 0 <= col_ini < col_fin <= trazado.MW

    def test_el_tmx_declara_las_mismas_zonas_que_trazado(self, escena) -> None:
        from src.framework.ecs import ZonaDeAgua

        zonas = [z for _eid, z in escena._mundo.cada(ZonaDeAgua)
                 if z.corriente.length_squared() > 0.0]
        assert len(zonas) == len(trazado.ZONAS_DE_CORRIENTE), (
            "el TMX generado no trae la misma cantidad de zonas con "
            "corriente que declara trazado.ZONAS_DE_CORRIENTE — "
            "¿hace falta correr tools/generate_stage4_1b.py de nuevo?"
        )

    def test_nadar_en_contra_de_la_corriente_frena_de_verdad(self, escena) -> None:
        """La cifra medida (no una promesa): 90 px/s en régimen, contra
        120 px/s sin corriente — un 25% más lento, verificado aquí con el
        mismo mecanismo que usa el nivel real (`sistema_corriente_de_agua`
        + `SwimmingState`), no con la fórmula de FUERZAS/dt a mano."""
        from src.engine.input.action_map import Action
        from src.framework.ecs import Velocidad, ZonaDeAgua
        from src.framework.ecs import systems as ecs_systems
        from src.framework.ecs.world import World
        from src.framework.entities.player import Player
        from src.framework.entities.states.swim import SwimmingState

        class _EntradaFalsa:
            def __init__(self, sostenidas: set) -> None:
                self._sostenidas = sostenidas

            def is_action_held(self, accion: object) -> bool:
                return accion in self._sostenidas

            def is_action_pressed(self, accion: object) -> bool:
                return False

            def pulsada_en_buffer(self, accion: object) -> bool:
                return False

        jugador = Player(pygame.Vector2(100.0, 100.0))
        jugador._change_state_instance(SwimmingState())
        mundo = World()
        jugador.adoptar_en(mundo)
        mundo.poner(jugador.entidad, Velocidad(jugador.velocity))
        mundo.crear(ZonaDeAgua(
            rect=pygame.Rect(0, 0, 4000, 4000),
            corriente=pygame.Vector2(-30.0, 0.0)))

        entrada = _EntradaFalsa({Action.MOVE_RIGHT})
        dt = 1 / 60
        for _ in range(int(3.0 / dt)):
            jugador.update(dt, [], entrada)
            ecs_systems.sistema_corriente_de_agua(mundo, dt)

        assert jugador.velocity.x == pytest.approx(90.0, abs=1.0), (
            f"la velocidad en régimen contra la corriente es "
            f"{jugador.velocity.x:.1f} px/s, no ~90: si esto cambió, la "
            f"nota de `ZONAS_DE_CORRIENTE` también hay que actualizarla"
        )
