"""QA de diseño de nivel: geometría posible, alcanzabilidad, puntos de muerte.

Qué mide esto y qué no
----------------------
Estas pruebas responden preguntas con respuesta objetiva: ¿este salto cabe en la
envolvente física del jugador? ¿se puede llegar del spawn a la salida? ¿hay un
tramo donde el bot muere siempre? Todos los umbrales se derivan de `settings`,
así que cambiar la fuerza de salto recalcula las conclusiones en lugar de
dejarlas obsoletas.

Lo que **no** mide es si el nivel es divertido. Un bot no puede saberlo, y
ponerle un número a la diversión invita a optimizar la métrica en vez del juego.
Lo que sí puede hacer es quitar de la mesa las causas objetivas de frustración
—un salto imposible, un pozo sin retorno— para que el playtest humano se dedique
a juzgar ritmo y tensión en lugar de tropezar con bugs de geometría.

Los umbrales están calibrados como *regresión*, no como opinión de diseño: fallan
si un nivel se vuelve imposible, no si es difícil.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

INTERNAL_SIZE = (800, 600)


@pytest.fixture(scope="module")
def display():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode(INTERNAL_SIZE)
    yield


@pytest.fixture
def context(display):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory

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
    return ctx


@pytest.fixture(scope="module")
def stage0_data(display):
    from src.framework.entities import entity_factory
    from src.framework.stage.stage_loader import StageLoader

    entity_factory.ensure_registered()
    path = "assets/maps/stage0/stage0.tmx"
    if not os.path.exists(path):
        pytest.skip("stage0 no está presente")
    return StageLoader.load(path)


# ── la envolvente de salto sale de la física, no de suposiciones ──


class TestJumpEnvelope:
    def test_derives_from_settings(self) -> None:
        from src.framework.stage.level_metrics import JumpEnvelope

        env = JumpEnvelope.from_settings()
        # v²/2g con los valores actuales: 380²/1600 = 90,25 px
        assert env.max_height == pytest.approx(90.25, abs=0.5)
        assert env.air_time == pytest.approx(0.95, abs=0.02)
        assert env.max_gap > 0

    def test_reacts_to_a_physics_change(self, monkeypatch) -> None:
        """Si alguien duplica la fuerza de salto, la envolvente debe seguirle.

        Es la diferencia entre un umbral derivado y una constante mágica: un
        número escrito a mano se quedaría obsoleto en silencio y empezaría a
        aprobar niveles imposibles o a rechazar niveles válidos.
        """
        from src.engine.core import settings
        from src.framework.stage.level_metrics import JumpEnvelope

        baseline = JumpEnvelope.from_settings().max_height
        monkeypatch.setattr(settings, "PLAYER_JUMP_FORCE", -760.0)
        doubled = JumpEnvelope.from_settings().max_height
        # Duplicar la velocidad inicial cuadruplica la altura.
        assert doubled == pytest.approx(baseline * 4, rel=0.05)

    @pytest.mark.parametrize(("gap_tiles", "expected"), [
        (1, "trivial"),
        (3, "cómodo"),
        (6, "exigente"),
        (20, "imposible"),
    ])
    def test_gap_classification(self, gap_tiles: int, expected: str) -> None:
        from src.engine.core import settings
        from src.framework.stage.level_metrics import JumpEnvelope

        env = JumpEnvelope.from_settings()
        assert env.classify_gap(gap_tiles * settings.TILE_SIZE) == expected

    def test_impossible_gap_is_wider_than_the_player_can_cross(self) -> None:
        from src.framework.stage.level_metrics import JumpEnvelope

        env = JumpEnvelope.from_settings()
        assert env.classify_gap(env.max_gap_with_air_jump + 1.0) == "imposible"
        assert env.classify_gap(env.max_gap_with_air_jump - 1.0) != "imposible"


# ── geometría de stage0 ──────────────────────────────────────────


class TestStage0Geometry:
    def test_exit_is_reachable_from_spawn(self, stage0_data) -> None:
        """El único bloqueo duro real: no poder llegar a la salida.

        Esta afirmación reemplazó a un "no hay huecos anchos" (AUD-049). Aquella
        versión reportó tres huecos imposibles en stage0 y los tres eran falsos
        positivos: comparaba plataformas dentro de la misma fila, y un hueco de
        suelo ancho se cruza saltando a una plataforma superior. Contar anchuras
        mide la geometría; lo que importa es la topología.
        """
        from src.framework.stage.level_metrics import analyse_stage

        report = analyse_stage(stage0_data)
        assert report.exit_reachable, (
            f"no existe cadena de saltos del spawn a la salida en stage0:\n"
            f"{report.summary()}"
        )

    def test_wide_gaps_are_reported_but_not_fatal(self, stage0_data) -> None:
        """Los huecos anchos son información, no un fallo.

        Se siguen midiendo porque le sirven al diseñador para ver dónde el nivel
        exige precisión, pero no cuentan como problema bloqueante.
        """
        from src.framework.stage.level_metrics import analyse_stage

        report = analyse_stage(stage0_data)
        assert report.blocking_issues == 0, (
            f"stage0 tiene problemas bloqueantes:\n{report.summary()}"
        )

    def test_most_platforms_are_reachable(self, stage0_data) -> None:
        """Una plataforma huérfana suele ser un error de colocación en Tiled.

        Umbral laxo a propósito: alguna plataforma decorativa o de techo puede ser
        legítimamente inalcanzable. Que la mayoría no lo sea sí es un síntoma.
        """
        from src.framework.stage.level_metrics import analyse_stage

        report = analyse_stage(stage0_data)
        if report.total_platforms == 0:
            pytest.skip("stage0 no declara plataformas")
        ratio = report.reachable_platforms / report.total_platforms
        assert ratio >= 0.6, (
            f"sólo {report.reachable_platforms}/{report.total_platforms} "
            f"plataformas son alcanzables desde el spawn:\n{report.summary()}"
        )

    def test_has_no_impossible_ledges(self, stage0_data) -> None:
        from src.framework.stage.level_metrics import analyse_stage

        report = analyse_stage(stage0_data)
        assert not report.impossible_ledges, (
            f"stage0 tiene {len(report.impossible_ledges)} repecho(s) más altos "
            f"que el salto del jugador: {report.impossible_ledges[:5]}"
        )

    def test_declares_an_exit(self, stage0_data) -> None:
        """Sin NextTrigger el nivel no se puede completar."""
        assert stage0_data.next_trigger is not None, (
            "stage0 no declara NextTrigger: es imposible de terminar"
        )

    def test_declares_a_spawn(self, stage0_data) -> None:
        assert stage0_data.spawn_point is not None

    def test_has_collision_geometry(self, stage0_data) -> None:
        assert stage0_data.collision_rects, (
            "stage0 no tiene geometría de colisión: el jugador caería sin fin"
        )

    def test_report_is_printable(self, stage0_data) -> None:
        """El informe debe ser legible por un diseñador, no sólo por un test."""
        from src.framework.stage.level_metrics import analyse_stage

        text = analyse_stage(stage0_data).summary()
        assert "Nivel:" in text
        assert "huecos imposibles" in text


# ── el bot recorre el nivel de verdad ────────────────────────────


class TestPlaythroughBot:
    @staticmethod
    def _stage(context):
        from src.stages.stage0.stage0 import Stage0

        scene = Stage0(context)
        scene.awake()
        scene.start()
        # AUD-461 — sin esto, cualquier bot que muera por un peligro
        # instantáneo (no por daño de combate) revienta con
        # «SceneManager: no scenes on the stack»: HazardSystem.update()
        # empuja el GameOverScene leyendo scene_manager.current, que exige
        # que esta escena esté en la pila. En juego real siempre lo está
        # —es la única forma en que SceneManager.update() la llama—, pero
        # este arnés la actualiza a mano. test_muerte_y_game_over.py ya
        # empuja la escena por el mismo motivo; este ayudante no lo hacía.
        # Ver test_bot_no_revienta_con_un_peligro_instantaneo.
        context.scene_manager.push(scene)
        scene.on_enter()
        return scene

    def test_bot_makes_horizontal_progress(self, context, display) -> None:
        """Un bot que camina a la derecha debe avanzar.

        Si no avanza, la primera pantalla tiene un muro, un hueco imposible o el
        jugador no responde a la entrada — cualquiera de las tres es un fallo de
        arranque que un jugador notaría en cinco segundos.
        """
        from tests.playtest.bot import run_playthrough, walk_right_bot

        scene = self._stage(context)
        try:
            start_x = scene._player.position.x
            log = run_playthrough(scene, walk_right_bot(seconds=6.0))
        finally:
            scene.on_exit()
            scene.destroy()

        advanced = log.max_x - start_x
        assert advanced > 32.0, (
            f"tras 6 s el bot sólo avanzó {advanced:.0f} px desde {start_x:.0f}. "
            f"La primera pantalla bloquea el paso o la entrada no llega al jugador."
        )

    def test_bot_survives_the_opening_seconds(self, context, display) -> None:
        """Morir en los primeros segundos sin hacer nada mal es injusto."""
        from tests.playtest.bot import run_playthrough, walk_right_bot

        scene = self._stage(context)
        try:
            log = run_playthrough(scene, walk_right_bot(seconds=4.0))
        finally:
            scene.on_exit()
            scene.destroy()

        assert not log.deaths, (
            f"el bot murió en {log.deaths} durante los primeros 4 s caminando "
            f"a la derecha: el arranque del nivel castiga sin avisar"
        )

    def test_playthrough_is_deterministic(self, context, display) -> None:
        """Dos recorridos idénticos deben dar el mismo resultado.

        Sin esto las métricas no sirven: un bot no determinista hace imposible
        distinguir una regresión del nivel de la varianza del propio bot.
        """
        from tests.playtest.bot import run_playthrough, walk_right_bot

        results = []
        for _ in range(2):
            scene = self._stage(context)
            try:
                results.append(run_playthrough(scene, walk_right_bot(seconds=3.0)).max_x)
            finally:
                scene.on_exit()
                scene.destroy()

        assert results[0] == pytest.approx(results[1], abs=1.0), (
            f"dos recorridos idénticos avanzaron distinto: {results}"
        )

    def test_metrics_aggregate_across_runs(self, context, display) -> None:
        from tests.playtest.bot import (
            run_playthrough,
            traversal_stats,
            walk_right_bot,
        )

        logs = []
        for _ in range(3):
            scene = self._stage(context)
            try:
                logs.append(run_playthrough(scene, walk_right_bot(seconds=3.0)))
            finally:
                scene.on_exit()
                scene.destroy()

        stats = traversal_stats(logs)
        assert stats["intentos"] == 3
        assert 0.0 <= stats["tasa_exito"] <= 1.0
        assert stats["avance_medio"] >= 0.0

    def test_bot_no_revienta_con_un_peligro_instantaneo(self, context, display) -> None:
        """AUD-461 — morir en un DeathPit no debe reventar el arnés de bots.

        `HazardSystem.update()` empuja `GameOverScene` leyendo
        `scene_manager.current`, que exige que la escena esté en la pila del
        gestor — algo que sólo pasa si `_stage()` la empuja, igual que hace
        `test_muerte_y_game_over.py`. Antes de AUD-461, `_stage()` no la
        empujaba y esto reventaba con «SceneManager: no scenes on the stack»
        en cuanto un bot tocaba un peligro instantáneo en vez de morir por
        daño de combate (lo único que `run_playthrough` sabe detectar sin
        que la escena avise por sí misma)."""
        scene = self._stage(context)
        try:
            foso = scene._stage_data.death_pits[0].rect
            scene._player.rect.midbottom = (foso.centerx, foso.top + 4)
            for _ in range(60):
                scene.update(1 / 60)
        finally:
            scene.on_exit()
            scene.destroy()

    def test_death_heatmap_groups_by_region(self) -> None:
        """El mapa de calor debe agrupar muertes cercanas en el mismo tramo."""
        from tests.playtest.bot import PlaythroughLog, death_heatmap

        logs = [
            PlaythroughLog(deaths=[(100.0, 0.0)]),
            PlaythroughLog(deaths=[(110.0, 0.0)]),
            PlaythroughLog(deaths=[(900.0, 0.0)]),
        ]
        heat = death_heatmap(logs, bucket_px=128.0)
        assert heat[0] == 2, "dos muertes contiguas deberían caer en el mismo tramo"
        assert heat[7] == 1


# ── el arnés funciona sobre cualquier nivel, no sólo stage0 ──────


def test_metrics_handle_an_empty_level() -> None:
    """Un nivel sin geometría debe reportarse, no reventar.

    Es el caso que produce un alumno la primera vez que exporta un TMX.
    """
    from src.framework.stage.level_metrics import analyse_geometry

    report = analyse_geometry([])
    assert report.notes, "un nivel vacío debería generar una nota explicativa"
    assert report.blocking_issues == 0


def test_metrics_flag_a_deliberately_broken_level() -> None:
    """Control positivo: un hueco enorme debe detectarse.

    Sin esto, los tests de stage0 podrían estar pasando porque el analizador no
    encuentra nada nunca — el mismo error que hizo que la suite antigua
    reportase éxito sobre subsistemas que no funcionaban.
    """
    from src.framework.stage.level_metrics import JumpEnvelope, analyse_geometry

    env = JumpEnvelope.from_settings()
    far = int(env.max_gap_with_air_jump * 3)
    rects = [
        pygame.Rect(0, 320, 64, 16),
        pygame.Rect(64 + far, 320, 64, 16),
    ]
    report = analyse_geometry(rects)
    assert report.impossible_gaps, (
        "un hueco tres veces más ancho que el salto máximo no se detectó: "
        "el analizador no está midiendo nada"
    )


def test_metrics_accept_a_reachable_level() -> None:
    """Control negativo: un hueco cómodo no debe marcarse."""
    from src.framework.stage.level_metrics import JumpEnvelope, analyse_geometry

    env = JumpEnvelope.from_settings()
    reachable = int(env.max_gap * 0.5)
    rects = [
        pygame.Rect(0, 320, 64, 16),
        pygame.Rect(64 + reachable, 320, 64, 16),
    ]
    report = analyse_geometry(rects)
    assert not report.impossible_gaps
    assert not report.demanding_gaps


def test_reachability_detects_a_disconnected_level() -> None:
    """Control positivo de topología: una isla aislada debe ser inalcanzable.

    Sin este control, `test_exit_is_reachable_from_spawn` podría pasar porque el
    grafo declara todo alcanzable siempre — el mismo modo de fallo que la suite
    antigua, que informaba éxito sobre subsistemas muertos.
    """
    from src.framework.stage.level_metrics import (
        JumpEnvelope,
        exit_is_reachable,
        reachable_platforms,
    )

    env = JumpEnvelope.from_settings()
    far = int(env.max_gap_with_air_jump * 6)
    ground = pygame.Rect(0, 320, 64, 16)
    island = pygame.Rect(far, 320, 64, 16)
    spawn = pygame.Vector2(32, 300)

    reachable = reachable_platforms([ground, island], spawn, env)
    assert len(reachable) == 1, (
        f"la isla aislada se declaró alcanzable: {reachable}"
    )
    assert not exit_is_reachable(
        [ground, island], spawn, pygame.Rect(far + 16, 300, 16, 16), env,
    ), "una salida sobre una isla inalcanzable se declaró alcanzable"


def test_reachability_accepts_a_stepped_route() -> None:
    """Un hueco ancho con plataforma intermedia SÍ debe ser alcanzable.

    Es el caso exacto que la comprobación por filas suspendía en stage0.
    """
    from src.framework.stage.level_metrics import JumpEnvelope, reachable_platforms

    env = JumpEnvelope.from_settings()
    step = int(env.max_gap * 0.5)
    rects = [
        pygame.Rect(0, 320, 48, 16),
        pygame.Rect(step, 280, 48, 16),          # escalón intermedio, más alto
        pygame.Rect(step * 2, 320, 48, 16),      # al otro lado del hueco
    ]
    reachable = reachable_platforms(rects, pygame.Vector2(16, 300), env)
    assert len(reachable) == 3, (
        f"la ruta escalonada no se reconoció: sólo {len(reachable)}/3 alcanzables"
    )


# ── AUD-096: los muros de cierre no son plataformas huérfanas ──────


class _EscenarioFalso:
    """Lo mínimo que `analyse_stage` lee de un `StageData`."""

    def __init__(self, rects, spawn, alto=608, next_trigger=None):
        self.collision_rects = rects
        self.spawn_point = spawn
        self.height_px = alto
        self.next_trigger = next_trigger
        self.checkpoints = []
        self.stage_id = "prueba"


def test_los_muros_laterales_no_cuentan_como_plataformas_huerfanas() -> None:
    """El aviso era del calificador, no del escenario.

    Stage 0 recibía «2 plataforma(s) sin ruta desde el spawn». Medido, las
    dos eran `Rect(0, 0, 16, 608)` y `Rect(1584, 0, 16, 608)`: los muros que
    cierran el mapa por los lados. Nadie salta encima de ellos.

    Que el calificador castigue a quien cierra bien su mapa es peor que
    inofensivo: enseña al estudiante a no fiarse de los avisos, y entonces
    tampoco lee los que sí importan.
    """
    from src.framework.stage.level_metrics import analyse_stage

    suelo = pygame.Rect(16, 560, 800, 48)
    muro_izq = pygame.Rect(0, 0, 16, 608)
    muro_der = pygame.Rect(1584, 0, 16, 608)
    escenario = _EscenarioFalso(
        [muro_izq, suelo, muro_der], pygame.Vector2(64, 540),
    )
    informe = analyse_stage(escenario)
    assert informe.orphan_platforms == 0, (
        f"{informe.orphan_platforms} muro(s) contados como plataforma huérfana"
    )
    assert informe.total_platforms == 1, (
        f"se contaron {informe.total_platforms} plataformas; sólo hay una"
    )


def test_una_isla_de_verdad_inalcanzable_si_se_sigue_detectando() -> None:
    """La excepción de los muros no puede tapar el fallo que sí importa."""
    from src.framework.stage.level_metrics import JumpEnvelope, analyse_stage

    env = JumpEnvelope.from_settings()
    lejos = int(env.max_gap_with_air_jump * 4)
    escenario = _EscenarioFalso(
        [
            pygame.Rect(0, 0, 16, 608),            # muro: no cuenta
            pygame.Rect(16, 560, 200, 48),         # suelo del spawn
            pygame.Rect(lejos, 200, 64, 16),       # isla inalcanzable
        ],
        pygame.Vector2(64, 540),
    )
    informe = analyse_stage(escenario)
    assert informe.orphan_platforms == 1, (
        f"la isla inalcanzable no se detectó (huérfanas: {informe.orphan_platforms})"
    )


def test_un_suelo_muy_largo_no_se_confunde_con_un_muro() -> None:
    """Se exige alto > ancho para no descartar suelos en mapas bajos."""
    from src.framework.stage.level_metrics import _boundary_walls

    suelo = pygame.Rect(0, 100, 1600, 96)
    escenario = _EscenarioFalso([suelo], pygame.Vector2(32, 90), alto=128)
    assert _boundary_walls([suelo], escenario) == set()


def test_stage0_no_tiene_plataformas_huerfanas() -> None:
    """El caso real que motivó el cambio."""
    import pygame as pg

    from src.framework.stage.level_metrics import analyse_stage
    from src.framework.stage.stage_loader import StageLoader

    if pg.display.get_surface() is None:
        pg.display.set_mode((8, 8))
    datos = StageLoader().load("assets/maps/stage0/stage0.tmx")
    informe = analyse_stage(datos)
    assert informe.orphan_platforms == 0
    assert informe.exit_reachable
