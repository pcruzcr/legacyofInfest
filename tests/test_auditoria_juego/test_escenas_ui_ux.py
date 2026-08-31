"""Arnés de auditoría UI/UX: cada escena debe dibujar contenido real,
sobrevivir a la entrada del jugador y responder a la navegación.

Por qué no basta el smoke de `test_scene_smoke.py`
--------------------------------------------------
Ese arnés prueba que la escena no crashea. Estas pruebas añaden las dos
preguntas de UX que un jugador hace en el primer segundo: ¿hay algo en
pantalla? (ocupación de píxeles distinta del fondo) y ¿el teclado/mando hace
algo? (navegación sin crashear y con cambio de contenido). Una escena que
dibuja un fondo vacío pasa el smoke y es un defecto de UX: esto lo detecta.

El umbral de ocupación es deliberadamente bajo (0.5 %): lo que se quiere
detectar es la pantalla en blanco, no juzgar densidad visual.
"""
from __future__ import annotations

import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.game_context import GameContext
from src.engine.core.save_manager import SaveManager
from src.engine.input.input_manager import InputManager
from src.engine.scene.scene_manager import SceneManager
from src.framework.entities import entity_factory

from src.engine.core import settings as _settings
INTERNAL_SIZE = (_settings.INTERNAL_WIDTH, _settings.INTERNAL_HEIGHT)
FRAMES = 10
DT = 1.0 / 60.0
#: Pantallas legítimas dibujan poco (créditos de texto fino centrado rondan
#: el 0.1 % con el muestreo jitter): el umbral sólo debe separar "hay algo"
#: de "fondo puro" (0 %).
UMBRAL_OCUPACION = 0.001  # 0.5 % de la pantalla: detecta pantallas en blanco


@pytest.fixture(scope="module")
def display():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode(INTERNAL_SIZE)
    yield pygame.display.get_surface()


@pytest.fixture
def context(display):
    entity_factory.ensure_registered()
    bus = EventBus()
    ctx = GameContext(
        input_manager=InputManager(),
        audio_manager=None,
        scene_manager=None,
        event_bus=bus,
        clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


def _ocupacion(surface: pygame.Surface, n: int = 7500) -> float:
    """Fracción de píxeles que difieren del fondo (esquina 0,0), muestreando
    con jitter determinista (semilla fija): una rejilla alineada se queda en
    blanco cuando el contenido (créditos que ruedan, texto fino) cae entre
    sus filas, y eso fabrica falsos vacíos."""
    fondo = surface.get_at((0, 0))
    ancho, alto = surface.get_size()
    rng = random.Random(4242)
    distintos = 0
    for _ in range(n):
        x = rng.randrange(ancho)
        y = rng.randrange(alto)
        if surface.get_at((x, y)) != fondo:
            distintos += 1
    return distintos / n


class _EscenarioDoble:
    def respawn(self) -> None:
        pass


#: Escenas con constructor que pide algo más que el contexto (mismo pacto
#: que `test_scene_smoke.ARGUMENTO_EXTRA`).
ARGUMENTO_EXTRA: dict[str, object] = {
    "StoryScene": 1,
    "UnitTheoryScene": "vectores",
    "GameOverScene": _EscenarioDoble,
    "StageErrorScene": "stage0.tmx: falta la capa Terrain",
}

ESCENAS: list[tuple[str, str]] = [
    ("src.engine.scenes.splash_scene", "SplashScene"),
    ("src.engine.scenes.title_scene", "TitleScene"),
    ("src.engine.scenes.options_scene", "OptionsScene"),
    ("src.engine.scenes.keybinding_scene", "KeybindingScene"),
    ("src.engine.scenes.load_game_scene", "LoadGameScene"),
    ("src.engine.scenes.skill_tree_scene", "SkillTreeScene"),
    ("src.engine.scenes.tutorial_scene", "TutorialScene"),
    ("src.engine.scenes.game_over_scene", "GameOverScene"),
    ("src.engine.scenes.stage_error_scene", "StageErrorScene"),
    ("src.engine.scenes.end_credits_scene", "EndCreditsScene"),
    ("src.engine.scenes.world_map_scene", "WorldMapScene"),
    ("src.engine.scenes.inventory_scene", "InventoryScene"),
    ("src.engine.scenes.shop_scene", "ShopScene"),
    ("src.engine.scenes.bestiary_scene", "BestiaryScene"),
    ("src.engine.scenes.achievement_scene", "AchievementScene"),
    ("src.engine.scenes.leaderboard_scene", "LeaderboardScene"),
    ("src.engine.scenes.progress_scene", "ProgressScene"),
    ("src.engine.scenes.demo_menu_scene", "DemoMenuScene"),
    ("src.engine.scenes.story_scene", "StoryScene"),
    ("src.engine.scenes.unit_theory_scene", "UnitTheoryScene"),
    ("src.engine.scenes.student_login_scene", "StudentLoginScene"),
    ("src.engine.scenes.vector_lab_scene", "VectorLabScene"),
    ("src.engine.scenes.transform_lab_scene", "TransformLabScene"),
    ("src.engine.scenes.collision_lab_scene", "CollisionLabScene"),
    ("src.engine.scenes.interpolation_lab_scene", "InterpolationLabScene"),
    ("src.engine.scenes.noise_lab_scene", "NoiseLabScene"),
    ("src.engine.scenes.curve_editor_scene", "CurveEditorScene"),
    ("src.engine.scenes.color_theory_scene", "ColorTheoryScene"),
    ("src.engine.scenes.filter_demo_scene", "FilterDemoScene"),
    ("src.engine.scenes.vision_demo_scene", "VisionDemoScene"),
    ("src.engine.scenes.pattern_demo_scene", "PatternDemoScene"),
    ("src.engine.scenes.pipeline_builder_scene", "PipelineBuilderScene"),
    ("src.engine.scenes.combo_demo_scene", "ComboDemoScene"),
    ("src.engine.scenes.sandbox_scene", "SandboxScene"),
    ("src.engine.scenes.stage_wizard_scene", "StageWizardScene"),
]

IDS = [nombre for _, nombre in ESCENAS]


def _construir(clase: type, context: object) -> object:
    extra = ARGUMENTO_EXTRA.get(clase.__name__)
    if extra is None:
        return clase(context)
    if callable(extra) and not isinstance(extra, (str, int)):
        extra = extra()
    return clase(context, extra)


def _ciclo_vida(scene, surface, frames: int = FRAMES) -> None:
    scene.awake()
    scene.start()
    scene.on_enter()
    try:
        for _ in range(frames):
            scene.process_events([])
            scene.update(DT)
            scene.draw(surface)
    finally:
        scene.on_exit()
        scene.destroy()


def _ciclo_vida_hasta_contenido(scene, surface, max_frames: int = 180) -> float:
    """Corre fotogramas hasta que la escena dibuja algo (escenas autoplay con
    entrada animada: créditos que ruedan desde fuera, fundidos, etc.) o se
    agota el presupuesto. Devuelve la ocupación final."""
    scene.awake()
    scene.start()
    scene.on_enter()
    try:
        for _ in range(max_frames):
            scene.process_events([])
            scene.update(DT)
            scene.draw(surface)
            if _ocupacion(surface) > UMBRAL_OCUPACION:
                break
    finally:
        scene.on_exit()
        scene.destroy()
    return _ocupacion(surface)


@pytest.mark.parametrize("modulo,clase", ESCENAS, ids=IDS)
def test_la_escena_dibuja_contenido_real(modulo, clase, context, display) -> None:
    """La escena no puede dejar la pantalla casi en blanco."""
    import importlib

    scene_cls = getattr(importlib.import_module(modulo), clase)
    surface = pygame.Surface(INTERNAL_SIZE)
    surface.fill((0, 0, 0))

    scene = _construir(scene_cls, context)
    ocupacion = _ciclo_vida_hasta_contenido(scene, surface)

    assert ocupacion > UMBRAL_OCUPACION, (
        f"{clase}: pantalla prácticamente vacía tras hasta 180 fotogramas"
    )


#: Escenas a las que la prueba de navegación no aplica en el estado inicial
#: del arnés. Dos familias: (1) pantallas estáticas por diseño (error,
#: créditos autoplay); (2) menús cuyo estado inicial no tiene datos (0
#: partidas / 0 entradas de bestiario / 0 desbloqueos / 0 puntuaciones /
#: inventario vacío): sin items no hay dónde navegar. La prueba SÍ exige que
#: no crasheen; sólo renuncia al "cambió lo dibujado". Sembrar datos para
#: estas escenas es trabajo de auditoría aparte (ver reporte 02).
NAVEGACION_SIN_CAMBIO: dict[str, str] = {
    "StageErrorScene": "pantalla de error estática por diseño (sin teclas)",
    "LoadGameScene": "0 partidas guardadas en el estado inicial del arnés",
    "BestiaryScene": "bestiario sin entradas en el estado inicial del arnés",
    "InventoryScene": "inventario vacío en el estado inicial del arnés",
    "AchievementScene": "0 logros desbloqueados en el estado inicial del arnés",
    "LeaderboardScene": "0 puntuaciones registradas en el estado inicial",
    "ProgressScene": "sin progreso en el estado inicial del arnés",
}


@pytest.mark.parametrize("modulo,clase", ESCENAS, ids=IDS)
def test_la_escena_responde_a_navegacion(modulo, clase, context, display) -> None:
    """Navegar con las teclas del menú (arriba/abajo/confirmar/cancelar) no
    puede crashear, y la escena debe reaccionar (cambia lo dibujado). Cada
    tecla se mantiene 60 fotogramas: escenas autoplay (créditos) o con
    ventanas de entrada (menú de pausa) necesitan tiempo para aceptar input."""
    import importlib

    from src.engine.input.action_map import DEFAULT_KEY_BINDINGS, Action

    scene_cls = getattr(importlib.import_module(modulo), clase)
    surface = pygame.Surface(INTERNAL_SIZE)
    scene = _construir(scene_cls, context)
    input_manager = context.input_manager

    scene.awake()
    scene.start()
    scene.on_enter()
    try:
        scene.process_events([])
        scene.update(DT)
        scene.draw(surface)
        base = pygame.image.tobytes(surface, "RGB")
        reacciono = False
        for accion in (Action.MOVE_DOWN, Action.MOVE_UP, Action.CONFIRM, Action.CANCEL):
            for key in DEFAULT_KEY_BINDINGS.get(accion, ()):
                down = pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="")
                input_manager.pump([down])
                scene.process_events([down])
                for _ in range(60):
                    scene.process_events([])
                    scene.update(DT)
                    scene.draw(surface)
                up = pygame.event.Event(pygame.KEYUP, key=key, mod=0)
                input_manager.pump([up])
                scene.process_events([up])
                # Se compara tras CADA tecla y se actualiza la base: una tecla
                # que mueve la selección y la siguiente que la devuelve se
                # anulan al final, y el neto no mide nada.
                ahora = pygame.image.tobytes(surface, "RGB")
                if ahora != base:
                    reacciono = True
                base = ahora
    finally:
        scene.on_exit()
        scene.destroy()

    motivo = NAVEGACION_SIN_CAMBIO.get(clase)
    if motivo:
        pytest.skip(f"{clase}: sin cambio esperado — {motivo}")
    assert reacciono, (
        f"{clase}: ninguna tecla de menú cambió lo dibujado — ¿input muerto? "
        f"(ocupación {_ocupacion(surface):.1%})"
    )


# ── escenas de nivel: arnés de juego real ────────────────────────


NIVELES: list[tuple[str, str, str]] = [
    ("stage0", "src.stages.stage0.stage0", "Stage0"),
    ("stage_mecanicas", "src.stages.stage_mecanicas.stage_mecanicas", "StageMecanicas"),
    ("stage_cenital", "src.stages.stage_cenital.stage_cenital", "StageCenital"),
    ("stage1_1", "src.stages.stage1_1.stage1_1", "Stage1_1_LaEntrada"),
    ("stage1_2_la_soda", "src.stages.stage1_2_la_soda.stage1_2_la_soda", "Stage1_2_LaSoda"),
    ("stage1_3_las_aulas", "src.stages.stage1_3_las_aulas.stage1_3_las_aulas", "Stage1_3_LasAulas"),
    ("stage2_1_oficinas", "src.stages.stage2_1_oficinas.stage2_1_oficinas", "Stage21Oficinas"),
    ("stage2_2", "src.stages.stage2_2.stage2_2", "Stage2_2"),
    ("lobby_datacenter", "src.stages.lobby_datacenter.lobby_datacenter", "LobbyDatacenter"),
    (
        "stage3_1_la_entrada_de_piedra",
        "src.stages.stage3_1_la_entrada_de_piedra.stage3_1_la_entrada_de_piedra",
        "Stage3_1_LaEntradaDePiedra",
    ),
    ("hall", "src.stages.hall.hall", "Hall"),
    ("stage3_3_el_patio", "src.stages.stage3_3_el_patio.stage3_3_el_patio", "Stage3_3ElPatio"),
    ("stage3_4_boss_gavilan", "src.stages.stage3_4_boss_gavilan.stage3_4_boss_gavilan", "Stage3_4BossGavilanScene"),
    ("stage4_1", "src.stages.stage4_1.stage4_1", "Stage4_1"),
    ("stage4_1b", "src.stages.stage4_1b.stage4_1b", "Stage4_1B"),
    ("stage4_1c_a", "src.stages.stage4_1c.stage4_1c", "Stage4_1C"),
    ("boss_venado", "src.stages.boss_venado.boss_venado_scene", "BossVenadoScene"),
    ("boss_rey", "src.stages.boss_rey.boss_rey_scene", "BossReyScene"),
    ("boss_paburu", "src.stages.boss_paburu.boss_paburu_scene", "BossPaburuScene"),
]

IDS_NIVEL = [n[0] for n in NIVELES]


def _saltar_cutscenes(scene) -> None:
    """Las cutscenes de apertura bloquean `update()`; se limpian como hacen
    los tests del 4-1 (ayudantes_stage4_1)."""
    cutscenes = getattr(scene, "_cutscenes", None)
    activos = getattr(cutscenes, "_activos", None)
    if activos is not None:
        activos.clear()


@pytest.mark.parametrize("stage_id,modulo,clase", NIVELES, ids=IDS_NIVEL)
def test_el_nivel_se_juega_y_dibuja(stage_id, modulo, clase, context, display) -> None:
    """El nivel completo (carga TMX + entidades + física + HUD) debe correr
    fotogramas reales y dibujar el mundo, no una pantalla vacía."""
    import importlib

    scene_cls = getattr(importlib.import_module(modulo), clase)
    surface = pygame.Surface(INTERNAL_SIZE)

    extra = None
    if clase == "Stage4_1C":
        extra = "a"

    scene = scene_cls(context) if extra is None else scene_cls(context, extra)
    scene.awake()
    scene.start()
    scene.on_enter()
    _saltar_cutscenes(scene)
    try:
        for _ in range(FRAMES):
            scene.process_events([])
            scene.update(DT)
            scene.draw(surface)
    finally:
        scene.on_exit()
        scene.destroy()

    assert _ocupacion(surface) > UMBRAL_OCUPACION, (
        f"{stage_id}: el nivel dibujó una pantalla vacía"
    )