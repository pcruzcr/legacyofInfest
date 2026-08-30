"""Pruebas de la escena del boss: politica de camara por zona + contratos de engine/harness."""
import types

import pygame
import pytest

from src.engine.core import settings
from src.engine.core.app import App
from src.engine.core.event_bus import EventBus
from src.engine.ui.hud import HUD
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.atencion import Atencion
from src.framework.stage.camera import Camera
from src.stages.boss_venado.boss_venado import BossVenado
from src.stages.boss_venado.boss_venado_scene import (
    ARENA_SETTLE_DURATION,
    ARENA_SHAKE_DURATION,
    ARENA_X0,
    COOLDOWN_REVELACION,
    PLAYER_HALO_PEAK,
    PLAYER_HALO_RADIUS,
    QUIETUD_PARA_REVELAR,
    BossVenadoScene,
)
from src.stages.boss_venado.presencias_venado import SOMBRA_X0, GestorDePresencias

MAP_W, MAP_H = 3280, 608   # boss_venado.tmx (mapa Residencias promovido 2026-07-24)


class _HudStub:
    """Registra cada llamada a set_boss_hud() -- sin renderizado, sin arranque de engine."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def set_boss_hud(self, name, health, max_health, phase, phase_count) -> None:
        self.calls.append((name, health, max_health, phase, phase_count))


def _bare_scene_with_boss(boss) -> tuple[BossVenadoScene, _HudStub]:
    """Construir la escena real requiere arrancar un GameContext/App (costoso,
    la misma razon por la que el resto de pruebas de este archivo lo evitan --
    ver test_scene_overrides_dibujar_ui_for_player_halo). ``__new__`` se salta
    __init__ y cableamos a mano solo los atributos que update() realmente
    toca: _player=None hace un cortocircuito en la rama del camera-lock,
    _stage_data es un sustituto minimo con solo entity_list (todo lo que lee
    _get_boss()), y _hud es el registrador de arriba (usado hoy para
    confirmar que update() ya NO le escribe nada -- ver la seccion H-02 del
    docstring del modulo de boss_venado_scene.py)."""
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._player = None
    scene._stage_data = types.SimpleNamespace(entity_list=[boss])
    hud = _HudStub()
    scene._hud = hud
    return scene, hud


def test_locks_pure_logic():
    sentinel = [object()]
    assert BossVenadoScene._locks_for_player_x(100.0, sentinel) == []
    assert BossVenadoScene._locks_for_player_x(ARENA_X0 - 1, sentinel) == []
    assert BossVenadoScene._locks_for_player_x(ARENA_X0, sentinel) == sentinel
    assert BossVenadoScene._locks_for_player_x(3200.0, sentinel) == sentinel


def _bare_scene_with_camera(camera_offset: tuple[float, float]) -> BossVenadoScene:
    """Candado H-17 (ver el docstring de H-17 en boss_venado_scene.py +
    reports/FINDINGS.md H-17): una Camera real (pero sin display -- Camera()
    solo toca pygame.Vector2/settings, no necesita arrancar el display)
    cableada lo justo para que _pin_camera_to_arena()/_arena_target_offset()
    corran en aislamiento, el mismo patron de evitar el costoso arranque de
    App que ya usa el resto de este archivo."""
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._camera = Camera()
    scene._camera.offset = pygame.Vector2(camera_offset)
    scene._camera.set_map_size(MAP_W, MAP_H)
    scene._stage_data = types.SimpleNamespace(map_pixel_size=(MAP_W, MAP_H))
    scene._in_arena_prev = False
    scene._arena_ease_elapsed = ARENA_SETTLE_DURATION
    scene._arena_ease_start = pygame.Vector2(0.0, 0.0)
    return scene


def test_pin_camera_to_arena_settles_on_the_true_right_edge():
    """Candado de regresion H-17 -- bug de playtest humano (2026-07-30): al
    entrar caminando a la arena la camara solia congelarse con el borde
    derecho clavado alrededor de x=2900 (mitad del gazebo) en vez del borde
    real del mapa (3280). Simula el offset exacto del congelamiento que midio
    la reproduccion headless (offset.x=2105.2 en el frame en que el lock se
    activo) y confirma que _pin_camera_to_arena lo suaviza (ease) hasta
    ARENA_X0 (== MAP_W - INTERNAL_WIDTH == 2480) dentro de
    ARENA_SETTLE_DURATION, y lo mantiene ahi despues."""
    scene = _bare_scene_with_camera((2105.2, 8.0))
    dt = 1.0 / 60.0
    frames = int(ARENA_SETTLE_DURATION / dt) + 5   # ventana de asentamiento + margen
    for _ in range(frames):
        scene._pin_camera_to_arena(dt, True)
    assert scene._camera.offset.x == ARENA_X0
    assert scene._camera.offset.x + settings.INTERNAL_WIDTH == MAP_W, (
        "borde derecho visible debe ser exactamente el borde real del mapa")
    assert scene._camera.offset.y == 8.0   # MAP_H - INTERNAL_HEIGHT clamp

    # Se mantiene estable tambien en frames posteriores (no solo en el instante en que termina el ease).
    for _ in range(120):
        scene._pin_camera_to_arena(dt, True)
    assert scene._camera.offset.x == ARENA_X0


def test_pin_camera_to_arena_eases_instead_of_snapping():
    """Protege el fix del "salto de borde" documentado en la seccion H-17 de
    boss_venado_scene.py (y en backups/pre-reset-2026-07-21/src/
    boss_venado_scene.py, donde primero se probo un snap duro y se rechazo):
    el primerisimo frame tras cruzar hacia la arena todavia debe estar a
    mitad de transicion, no ya sentado en el target -- una regresion
    silenciosa de vuelta a un snap duro reproduciria el corte duro de
    ~400px de screen_x en un solo frame."""
    scene = _bare_scene_with_camera((2105.2, 8.0))
    scene._pin_camera_to_arena(1.0 / 60.0, True)
    assert 2105.2 < scene._camera.offset.x < ARENA_X0, (
        "el primer frame enganchado debe seguir en pleno ease, no ya en el target")


def test_pin_camera_to_arena_is_noop_outside_the_arena():
    """Fuera de la arena, _pin_camera_to_arena debe dejar camera.offset
    completamente intacto -- el follow-lerp heredado de StageScene (que ya
    corrio via super().update() antes en el frame) es quien debe tener el
    control ahi."""
    scene = _bare_scene_with_camera((600.0, 8.0))
    scene._pin_camera_to_arena(1.0 / 60.0, False)
    assert (scene._camera.offset.x, scene._camera.offset.y) == (600.0, 8.0)


def test_pin_camera_to_arena_settles_across_repeated_oscillation():
    """H-17 candado de vaivén (2026-07-30): las corridas largas oficiales
    (final_cam_dodger/final_cam_competent, 7200/14400f seed 1) muestran al
    bot cruzando ARENA_X0 hacia adelante y atrás varias veces cerca del
    umbral (keep-away del dodger, proximity-gate del competent) antes de
    quedarse en combate. Cada entrada debe volver a asentar EXACTO en
    ARENA_X0, sin importar cuántas veces se repita el vaivén -- guarda
    contra que el pin se vuelva frágil bajo oscilación repetida (una de las
    hipótesis descartadas al investigar el falso rojo del gate)."""
    scene = _bare_scene_with_camera((2105.2, 8.0))
    dt = 1.0 / 60.0
    ease_frames = int(ARENA_SETTLE_DURATION / dt) + 5

    for cycle in range(4):
        for _ in range(ease_frames):
            scene._pin_camera_to_arena(dt, True)
        assert scene._camera.offset.x == ARENA_X0, (
            f"ciclo {cycle}: no asentó en {ARENA_X0} (offset={scene._camera.offset.x})")
        # el player sale de la arena unos frames (follow-lerp normal, simulado
        # moviendo el offset directamente) antes de la siguiente entrada.
        scene._pin_camera_to_arena(dt, False)
        scene._camera.offset.x = 1950.0 + cycle * 10.0   # posición "de salida" distinta cada vez


def test_pin_camera_to_arena_re_eases_on_re_entry():
    """Salir de la arena (in_arena=False) reinicia el latch transitorio del
    ease, de modo que salir caminando y volver a entrar hace un re-ease
    limpio desde la nueva posicion de la follow-camera en vez de quedarse
    silenciosamente "asentado" en un target obsoleto (o, peor, saltando)."""
    scene = _bare_scene_with_camera((2105.2, 8.0))
    dt = 1.0 / 60.0
    for _ in range(int(ARENA_SETTLE_DURATION / dt) + 5):
        scene._pin_camera_to_arena(dt, True)
    assert scene._camera.offset.x == ARENA_X0

    # El jugador vuelve a salir caminando -- el follow-lerp (simulado aqui
    # con solo mover el offset directamente) lleva la camara a otro lado.
    scene._pin_camera_to_arena(dt, False)
    scene._camera.offset.x = 1900.0

    # Al volver a entrar debe hacer ease de nuevo, no re-saltar de inmediato a ARENA_X0.
    scene._pin_camera_to_arena(dt, True)
    assert 1900.0 < scene._camera.offset.x < ARENA_X0


def test_scene_declares_engine_contract():
    assert BossVenadoScene.STAGE_ID == "boss_venado"
    assert hasattr(BossVenadoScene, "_get_boss")        # contrato del Recorder de playtest


def test_player_halo_is_a_bright_center_dark_edge_gradient():
    """Hallazgo de playtest (2026-07-28): el sprite encapuchado del jugador
    se camufla contra el follaje crepuscular. _build_player_halo() es el
    constructor puro/cacheable del fix de luz de luna aditiva -- no hace
    falta ninguna escena para probarlo."""
    halo = BossVenadoScene._build_player_halo()
    assert isinstance(halo, pygame.Surface)
    assert halo.get_size() == (PLAYER_HALO_RADIUS * 2, PLAYER_HALO_RADIUS * 2)
    center_px = halo.get_at((PLAYER_HALO_RADIUS, PLAYER_HALO_RADIUS))
    edge_px = halo.get_at((0, 0))
    assert sum(center_px[:3]) > sum(edge_px[:3]), (
        "halo center should be brighter than its edge (radial gradient)")


def test_scene_overrides_dibujar_ui_for_player_halo():
    """Construir la escena real (App/TMX/display de pygame) es costoso --
    esto solo verifica que el override exista en BossVenadoScene mismo (no
    solo heredado de StageScene), que es lo que realmente hace el blit del
    halo.

    H-28/B-032 (fix 2026-08-20, ver el docstring del módulo de
    boss_venado_scene.py y el de ``dibujar_ui``): esta escena solía
    sobrescribir ``draw()`` -- y esta misma prueba, antes de este fix,
    aseguraba precisamente eso (``"draw" in BossVenadoScene.__dict__``).
    Pero ``App._draw()`` (app.py 556-723) nunca llama a ``escena.draw()``
    cuando la escena expone ``dibujar_mundo``/``dibujar_ui`` -- que
    ``StageScene`` expone siempre (AUD-343) -- así que ese override entero
    era código MUERTO bajo el despacho real del motor, y esta prueba, junto
    con el resto de la suite que llamaba ``scene.draw(surface)`` a mano,
    seguía en verde sin notarlo: la lección H-28 es que una llamada DIRECTA
    a un método en una prueba no prueba el DESPACHO real de ese método por
    el motor. El fix mueve el override a ``dibujar_ui()`` y elimina
    ``draw()`` de esta clase -- este candado ahora vigila las dos mitades de
    esa migración: que ``dibujar_ui`` sea propio (no heredado) Y que
    ``draw`` ya NO lo sea (para que una regresión futura que reintroduzca
    ``draw()`` en esta clase se note aquí antes que en cualquier otro
    lado). El candado que sí distingue "el método existe" de "el motor lo
    despacha de verdad" -- el que de verdad importa para H-28 -- vive por
    píxeles en ``test_despacho_real_overlays.py`` (llama ``App._draw()``,
    nunca ``scene.draw()``)."""
    assert "dibujar_ui" in BossVenadoScene.__dict__
    assert "draw" not in BossVenadoScene.__dict__, (
        "BossVenadoScene volvió a sobrescribir draw() -- ver H-28/B-032: "
        "App._draw() nunca lo despacha, así que cualquier overlay pintado "
        "ahí sería código muerto de nuevo")


def test_player_halo_never_silently_disabled():
    """Candado de regresion: nada debe poder anular silenciosamente el fix
    del halo (p. ej. alguien baja PLAYER_HALO_PEAK hacia 0, o encoge el
    radio hasta volverlo un no-op) sin que una prueba se ponga roja.

    Piso acordado tras el playtest del 2026-07-28 -- el sprite encapuchado
    es RGB~=(15, 20, 35) sobre una paleta crepuscular; por debajo de esto el
    heroe vuelve a camuflarse."""
    assert PLAYER_HALO_PEAK >= 30
    assert PLAYER_HALO_RADIUS >= 32

    halo = BossVenadoScene._build_player_halo()
    center_px = halo.get_at((PLAYER_HALO_RADIUS, PLAYER_HALO_RADIUS))
    assert sum(center_px[:3]) >= 3 * 25, (
        "halo center is too dim to read against the dusk palette -- "
        "the fix was silently weakened")


def test_la_escena_ya_no_pisa_el_phase_count_del_hud(monkeypatch):
    """Candado de la nueva realidad de H-02 (motor V4, AUD-512 -- ver la
    seccion H-02 del docstring del modulo): ``_compensate_boss_hud_phase``
    volvia a llamar a ``set_boss_hud()`` pasando la fase actual en AMBOS
    slots, lo que con el HUD V4 (que ya guarda ``phase`` y ``phase_count``
    en atributos separados, ver hud.py ``set_boss_hud``/``_draw_boss_hud``)
    pisaba ``phase_count`` con un valor falso. Dos candados en uno:

    1) anti-resurreccion -- el metodo ya no debe existir en absoluto, para
       que un merge descuidado desde una rama vieja se note aqui antes que
       en cualquier otro lado.
    2) el override propio de ``update()`` de esta escena ya no debe llamar a
       ``set_boss_hud()`` -- esa llamada es responsabilidad exclusiva de
       ``ActualizacionesDeEscenario._update_hud_ui`` (actualizaciones.py
       L59-71), dentro de ``super().update(dt)``, que aqui se stubea como
       no-op para aislar el override PROPIO de la escena (mismo patron que
       usaba el test viejo de esta compensacion). El HUD se deja
       pre-poblado con el ``phase_count`` REAL que ``_update_hud_ui`` ya
       habria escrito momentos antes en el mismo frame (el total constante
       de fases del boss, 2): si la compensacion resucitara, este valor
       cambiaria a la fase actual (1) y el ultimo assert fallaria."""
    assert not hasattr(BossVenadoScene, "_compensate_boss_hud_phase")

    monkeypatch.setattr(StageScene, "update", lambda self, dt: None)

    boss = BossVenado(pygame.Vector2(0, 0))
    assert boss.current_phase == 0                        # sanidad: un boss recien creado empieza en fase 0
    scene, hud = _bare_scene_with_boss(boss)
    hud._boss_phase_count = boss.phase_count               # simula que _update_hud_ui ya corrio este frame

    scene.update(1.0 / 60.0)

    assert hud.calls == [], (
        "la escena ya no debe llamar a set_boss_hud directamente -- "
        "eso corrompia phase_count con el HUD V4")
    assert hud._boss_phase_count == boss.phase_count, (
        "el slot phase_count del HUD debe sobrevivir intacto sin la compensacion")


def test_el_hud_del_motor_deja_la_fase_actual_correcta_tras_una_transicion_real():
    """La garantia que antes daba ``_compensate_boss_hud_phase`` -- que la
    etiqueta del HUD muestre la fase ACTUAL, 1-indexada, y no el conteo
    total fijo -- ahora la da el motor V4 por si solo (AUD-512):
    ``HUD.set_boss_hud`` y su handler de evento ``_on_boss_phase_changed``
    (hud.py ~L435-460) guardan ``phase``/``phase_count`` en atributos
    separados, y ``_draw_boss_hud`` (~L820-831) ya lee el slot correcto.

    Se dispara una transicion de fase REAL sobre un ``BossVenado`` de
    verdad -- mismo patron que
    ``test_phase_transition_emits_event_and_builds_figure8`` en
    test_boss_venado.py: ``set_event_bus`` (publico, de ``EnemyBase`` via
    ``BossBase``) comparte el bus del boss con un HUD externo -- y se
    confirma que el HUD del motor, sin que esta escena intervenga en
    absoluto, termina con ``_boss_phase`` en el valor 1-indexado correcto.

    No se ejercita ``_update_hud_ui`` (actualizaciones.py) directamente
    porque exige un ``_player``/inventario/tiempo-bala completos que esta
    suite evita deliberadamente montar (ver ``_bare_scene_with_boss`` y el
    resto de este archivo, que jamas arranca un StageScene real); el
    camino por evento cubre la misma garantia de almacenamiento del HUD
    sin ese costo."""
    dt = 1.0 / 60.0
    bus = EventBus()
    boss = BossVenado(pygame.Vector2(3168, 240))
    boss.set_event_bus(bus)
    hud = HUD(bus)

    assert boss.current_phase == 0
    boss.apply_hit(6.5, (0, 0))          # 12 -> 5.5, cruza el umbral de fase 1 (6.0)
    assert boss.is_transitioning
    for _ in range(int(2.6 / dt)):       # transition_timer == 2.5 (motor)
        boss.update(dt)
    assert not boss.is_transitioning and boss.current_phase == 1

    bus.dispatch()                        # EventBus es una cola
    assert hud._boss_phase == boss.current_phase + 1, (
        "el HUD del motor debe guardar la fase ACTUAL 1-indexada por si solo, "
        "sin ninguna compensacion de esta escena")
    assert hud._boss_phase_count == boss.phase_count


# ──────────────────────────────────────────────
# Task 6 (pulido AAA, oleada de lianas): EfectosDeLaEscena -- el puerto real
# EfectosDelEscenario (ver efectos_venado.py) implementado contra el motor.
# ──────────────────────────────────────────────

class _EmisorFalso:
    """Duplica la superficie minima de ParticleEmitter que EfectosDeLaEscena toca."""
    def __init__(self) -> None:
        self.emitidas = []
        self.dirigidas = []

    def emit(self, x, y, config) -> None:
        self.emitidas.append((x, y, config))

    def emit_directed(self, x, y, angle, **kwargs) -> None:
        self.dirigidas.append((x, y, angle, kwargs))


class _ParticleSystemFalso:
    def __init__(self) -> None:
        self.emisores: dict = {}

    def get_emitter(self, nombre: str) -> "_EmisorFalso":
        if nombre not in self.emisores:
            self.emisores[nombre] = _EmisorFalso()
        return self.emisores[nombre]


class _CamaraFalsa:
    def __init__(self) -> None:
        self.shakes = []

    def apply_shake(self, amplitude, duration, direccion) -> None:
        self.shakes.append((amplitude, duration, direccion))


class _TrailSystemFalso:
    def __init__(self) -> None:
        self.capturas = []

    def capture_at(self, x, y, size, color) -> None:
        self.capturas.append((x, y, size, color))


def _escena_falsa_para_efectos():
    from src.stages.boss_venado.boss_venado_scene import EfectosDeLaEscena
    escena = types.SimpleNamespace(
        _particle_system=_ParticleSystemFalso(),
        _camera=_CamaraFalsa(),
        _enemy_trail_system=_TrailSystemFalso(),
    )
    return escena, EfectosDeLaEscena(escena)


def test_efectos_de_la_escena_particulas_delega_al_emisor_venado():
    from src.framework.vfx.particle_system import BurstConfig
    escena, efectos = _escena_falsa_para_efectos()
    config = BurstConfig(count=3, speed=70.0, lifetime=0.35, size=(2, 3), color=(1, 2, 3))
    efectos.particulas(10.0, 20.0, config)
    assert escena._particle_system.emisores["venado"].emitidas == [(10.0, 20.0, config)]


def test_efectos_de_la_escena_particulas_dirigidas_usa_spread_medio_de_emit_directed():
    from src.framework.vfx.particle_system import BurstConfig
    escena, efectos = _escena_falsa_para_efectos()
    config = BurstConfig(count=8, speed=90.0, lifetime=0.4, size=(2, 4),
                         color=(1, 2, 3), spread=160.0, gravity=300.0, friction=0.85)
    efectos.particulas_dirigidas(10.0, 20.0, -90.0, config)
    x, y, angulo, kwargs = escena._particle_system.emisores["venado"].dirigidas[0]
    assert (x, y, angulo) == (10.0, 20.0, -90.0)
    assert kwargs["speed"] == 90.0 and kwargs["count"] == 8 and kwargs["lifetime"] == 0.4
    assert kwargs["size"] == (2, 4) and kwargs["color"] == (1, 2, 3)
    assert kwargs["spread"] == 80.0     # spread/2.0 -- emit_directed toma el SEMI-angulo
    assert kwargs["gravity"] == 300.0 and kwargs["friction"] == 0.85


def test_efectos_de_la_escena_sacudir_delega_a_camera_apply_shake():
    escena, efectos = _escena_falsa_para_efectos()
    efectos.sacudir(4.0, 0.2, (0.0, 1.0))
    assert escena._camera.shakes == [(4.0, 0.2, (0.0, 1.0))]


def test_efectos_de_la_escena_sacudir_es_noop_sin_camara():
    escena, efectos = _escena_falsa_para_efectos()
    escena._camera = None
    efectos.sacudir(4.0, 0.2, None)   # no debe lanzar


def test_efectos_de_la_escena_estela_delega_al_trail_system():
    escena, efectos = _escena_falsa_para_efectos()
    efectos.estela(5.0, 6.0, (8, 8), (1, 2, 3, 4))
    assert escena._enemy_trail_system.capturas == [(5.0, 6.0, (8, 8), (1, 2, 3, 4))]


# ──────────────────────────────────────────────
# Task 6, inyeccion real: el puerto EfectosDeLaEscena debe conectarse en
# on_enter() -- y volver a conectarse en cada respawn() (H-18, el motor V3
# reconstruye el jefe entero en cada reintento).
# ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def app_headless():
    """App real bajo software forzado -- misma receta que test_telegraphs_sobre_la_luz.py/
    test_despacho_real_overlays.py (calcada, no importada -- ver esos modulos para el
    razonamiento completo)."""
    app = App(use_gl=False)
    try:
        yield app
    finally:
        pygame.display.set_mode((320, 224))


def _push_real_scene(app: App) -> BossVenadoScene:
    scene = BossVenadoScene(app.context)
    app.scene_manager.replace(scene)  # awake() -> start() -> on_enter(), igual que main.py
    assert scene._player is not None, "on_enter() no genero al jugador"
    assert scene._stage_data is not None, "on_enter() no cargo el stage"
    return scene


def test_conectar_efectos_tras_on_enter_inyecta_el_puerto_real(app_headless):
    from src.stages.boss_venado.boss_venado_scene import EfectosDeLaEscena
    scene = _push_real_scene(app_headless)
    jefe = scene._get_boss()
    assert jefe is not None
    assert isinstance(jefe.efectos, EfectosDeLaEscena)


def test_conectar_efectos_sobrevive_al_respawn(app_headless):
    """H-18: respawn() reconstruye el jefe entero (objeto nuevo) -- el puerto debe
    volver a inyectarse en cada reintento, no solo en el primer on_enter()."""
    from src.stages.boss_venado.boss_venado_scene import EfectosDeLaEscena
    scene = _push_real_scene(app_headless)
    jefe_1 = scene._get_boss()
    assert jefe_1 is not None
    scene.respawn()
    jefe_2 = scene._get_boss()
    assert jefe_2 is not None
    assert jefe_2 is not jefe_1, "respawn() debe reconstruir un jefe nuevo (H-18)"
    assert isinstance(jefe_2.efectos, EfectosDeLaEscena)


# ──────────────────────────────────────────────
# Tarea 2 del plan "La Peregrinacion al Venado": grading/tinte/vineta por
# avance del jugador en el corredor (tramos_venado.py). Mismo patron de doble
# stub que _HudStub/_bare_scene_with_boss de arriba: registrar llamadas, sin
# arrancar ningun subsistema real de post-procesado.
# ──────────────────────────────────────────────

class _PostProcessingStub:
    """Registra cada llamada -- mismo patron que _HudStub de arriba."""

    def __init__(self) -> None:
        self.gradings: list[tuple] = []
        self.grading_limpiada = False
        self.tintes: list[tuple] = []
        self.tinte_limpiado = False
        self.vinetas: list[float] = []

    def set_color_grading(self, *matriz) -> None:
        self.gradings.append(matriz)

    def clear_color_grading(self) -> None:
        self.grading_limpiada = True

    def set_tint(self, color, alfa) -> None:
        self.tintes.append((color, alfa))

    def clear_tint(self) -> None:
        self.tinte_limpiado = True

    def set_vignette(self, valor) -> None:
        self.vinetas.append(valor)


def _bare_scene_with_player_x(x: float) -> tuple[BossVenadoScene, _PostProcessingStub]:
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._post_processing = _PostProcessingStub()
    rect = pygame.Rect(0, 528, 32, 32)
    rect.centerx = int(x)   # x es la columna de MUNDO que lee la produccion
                             # (rect.centerx), no el borde izquierdo del rect
    scene._player = types.SimpleNamespace(rect=rect)
    scene._tramo_actual = None
    scene._tramo_grading_previo = None
    scene._tramo_tinte_previo = None
    scene._tramo_vineta_previa = 0.0
    return scene, scene._post_processing


def test_actualizar_tramo_narrativo_en_acto_1_sin_gradacion():
    scene, pp = _bare_scene_with_player_x(0.0)
    scene._actualizar_tramo_narrativo(1 / 60)
    assert pp.grading_limpiada is True
    assert pp.tinte_limpiado is True
    assert pp.vinetas[-1] == pytest.approx(0.20)


def test_actualizar_tramo_narrativo_al_entrar_al_acto_2_parte_de_la_identidad():
    """t==0.0 al entrar a un tramo: el resultado es el tramo ANTERIOR (aqui
    None -> IDENTIDAD, ver interpolar_grading), nunca el destino de golpe."""
    from src.stages.boss_venado.tramos_venado import IDENTIDAD
    scene, pp = _bare_scene_with_player_x(1040.0)
    scene._actualizar_tramo_narrativo(1 / 60)
    assert pp.gradings[-1] == IDENTIDAD
    assert pp.tintes == []   # alfa parte de 0 y t=0 -> clear_tint(), set_tint() no se llega a invocar
    assert pp.tinte_limpiado is True


def test_actualizar_tramo_narrativo_alcanza_ambar_completo_al_cruzar_al_acto_3():
    """AMBAR es el valor del Acto 2 -- se alcanza EXACTO como el "previo" en
    el instante t=0 del Acto 3 (interpolar_grading(AMBAR, ..., 0.0) == AMBAR),
    sin depender de la precision de ease_in_out_quad a mitad de camino."""
    from src.stages.boss_venado.tramos_venado import AMBAR
    scene, pp = _bare_scene_with_player_x(1300.0)   # dentro del Acto 2
    scene._actualizar_tramo_narrativo(1 / 60)
    scene._player.rect.centerx = 1520   # cruza al Acto 3: Acto 2 (AMBAR) pasa a ser el "previo"
    scene._actualizar_tramo_narrativo(1 / 60)
    assert pp.gradings[-1] == AMBAR
    assert pp.tintes[-1][0] == (80, 110, 160)   # color del tinte del Acto 3 (AZUL_MISTERIO), fijo desde t=0


def test_actualizar_tramo_narrativo_regresion_al_acto_anterior():
    """Regresion (el jugador retrocede en vez de avanzar): al cruzar de
    vuelta del Acto 3 al Acto 2, el tramo "previo" para la interpolacion debe
    ser el Acto 3 (de donde viene), no None ni un salto directo al valor
    pleno del Acto 2 -- exactamente el mismo mecanismo de _tramo_actual/
    _tramo_*_previo que el cruce hacia adelante del test de arriba, solo que
    en sentido contrario. Protege contra una implementacion que solo
    actualizara el estado "previo" en una direccion (p. ej. comparando
    x_inicio creciente en vez de identidad de tramo con `is not`)."""
    from src.stages.boss_venado.tramos_venado import AZUL_MISTERIO
    scene, pp = _bare_scene_with_player_x(2000.0)   # dentro del Acto 3
    scene._actualizar_tramo_narrativo(1 / 60)
    scene._player.rect.centerx = 1040   # retrocede al Acto 2 (entrada exacta, t=0)
    scene._actualizar_tramo_narrativo(1 / 60)
    # t=0 al re-entrar al Acto 2: el grading parte EXACTO del "previo"
    # (Acto 3, AZUL_MISTERIO), no de golpe del AMBAR del Acto 2.
    assert pp.gradings[-1] == AZUL_MISTERIO
    # El tinte de destino ya es el del Acto 2 (AMBAR)...
    assert pp.tintes[-1][0] == (220, 160, 90)
    # ...pero el alfa en t=0 sigue siendo el del tramo del que se viene (Acto
    # 3, 0.10), no el objetivo del Acto 2 (0.08) ni cero.
    assert pp.tintes[-1][1] == pytest.approx(0.10)
    # Misma logica para la vineta: en t=0 vale lo que traia el Acto 3.
    assert pp.vinetas[-1] == pytest.approx(0.38)


def test_dibujar_velo_de_niebla_pinta_solo_en_la_zona_de_fog():
    """B-046 (REGISTRO-DE-BUGS.md) -- REDISEÑO de la Tarea 8 tras retirar el
    cableado a `WeatherSystem` (el motor no puede transicionar clima con el
    reloj congelado, `day_length=0`, y su overlay tampoco interpola jamás).
    El velo de niebla es ahora puramente de esta escena: perfil puro en
    `efectos_venado.alfa_de_niebla`, wiring en `_dibujar_velo_de_niebla`.

    Smoke de píxel (mismo patrón que
    `test_dibujar_fondo_pinta_una_presencia_visible_dentro_del_viewport`,
    más abajo en este archivo): con el jugador en x=2000 (dentro del Acto 3,
    tramo sostenido de `alfa_de_niebla`) debe pintarse algo no transparente
    en pantalla completa; en x=800 (Acto 1) y x=2500 (Acto 4/arena) no debe
    pintarse NADA -- `alfa_de_niebla` devuelve 0 y el método hace return
    temprano sin tocar la superficie, que por tanto queda exactamente como
    `pygame.Surface(..., SRCALPHA)` la inicializa: transparente."""
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._velo_de_niebla = None
    rect = pygame.Rect(0, 528, 32, 32)
    scene._player = types.SimpleNamespace(rect=rect)

    rect.centerx = 2000
    surface_fog = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)
    scene._dibujar_velo_de_niebla(surface_fog)
    assert surface_fog.get_at((10, 10)).a > 0

    rect.centerx = 800
    surface_acto1 = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)
    scene._dibujar_velo_de_niebla(surface_acto1)
    assert surface_acto1.get_at((10, 10)).a == 0

    rect.centerx = 2500
    surface_arena = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)
    scene._dibujar_velo_de_niebla(surface_arena)
    assert surface_arena.get_at((10, 10)).a == 0


def test_dibujar_velo_de_niebla_sin_jugador_no_lanza():
    """Mismo patrón defensivo que el resto de `dibujar_ui` (halo, banner de
    reliquia): un doble de prueba mínimo sin `_player` no debe reventar."""
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._velo_de_niebla = None
    scene._player = None
    surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)
    scene._dibujar_velo_de_niebla(surface)   # no debe lanzar
    assert surface.get_at((10, 10)).a == 0


def test_dibujar_velo_de_niebla_cachea_la_superficie_una_sola_vez():
    """La superficie NO se reconstruye en cada llamada -- mismo patrón de
    caché que `_player_halo`/H-28 (ver el docstring de
    `_build_velo_de_niebla`): dos llamadas con alfa>0 deben reutilizar el
    mismo objeto `pygame.Surface`."""
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._velo_de_niebla = None
    rect = pygame.Rect(0, 528, 32, 32)
    rect.centerx = 2000
    scene._player = types.SimpleNamespace(rect=rect)
    surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)

    scene._dibujar_velo_de_niebla(surface)
    primera = scene._velo_de_niebla
    assert primera is not None
    scene._dibujar_velo_de_niebla(surface)
    assert scene._velo_de_niebla is primera


def test_presencias_no_alteran_la_posicion_del_jugador_en_una_corrida_corta():
    """Candado: 120 cuadros con el gestor de presencias activo no deben
    cambiar nada de la física del jugador -- las presencias solo se dibujan,
    nunca se actualizan contra un rect de jugador."""
    g = GestorDePresencias(semilla=7)
    g.tramo_actual = 1
    for _ in range(120):
        g.actualizar(1 / 60)
    # Si esto no revienta y no exige ningún argumento de jugador, el
    # contrato arquitectónico ya está probado por la firma (ver
    # test_presencias_venado.py); aquí solo se confirma que 120 cuadros
    # reales no crashean.
    assert True


def test_scene_expone_dibujar_fondo_propio_para_las_presencias():
    """CORRECCIÓN del Paso 5/6 de la Tarea 4 frente al plan escrito: el
    borrador proponía sobrescribir ``dibujar_mundo`` -- eso no sobrevive
    (ver el docstring de ``dibujar_fondo`` en boss_venado_scene.py: pintar
    ahí se borra por el ``surface.fill`` con el que arranca
    ``DrawingSystem.draw``). El wiring real vive en ``dibujar_fondo``
    (gancho AUD-162, mismo patrón que ``Stage4_1.dibujar_fondo``), así que
    este candado -- mismo espíritu que
    test_scene_overrides_dibujar_ui_for_player_halo de arriba -- vigila que
    el override sea PROPIO de BossVenadoScene (no solo heredado) y que
    ``draw()`` siga sin reaparecer (precedente H-28)."""
    assert "dibujar_fondo" in BossVenadoScene.__dict__
    assert "draw" not in BossVenadoScene.__dict__, (
        "BossVenadoScene volvió a sobrescribir draw() -- ver H-28\\B-032: "
        "App._draw() nunca lo despacha, así que cualquier overlay pintado "
        "ahí sería código muerto de nuevo")


def test_dibujar_fondo_pinta_una_presencia_visible_dentro_del_viewport():
    """Prueba de humo por píxeles: con una presencia forzada a visible,
    dibujar_fondo() debe dejar algo no-transparente donde se espera la
    silueta -- sin esto, un candado puramente estructural (el de arriba)
    podría quedar verde con un cuerpo de método vacío o roto.

    Se muestrea el píxel CENTRAL del bounding box de la silueta, no su
    borde: el centro de una elipse rellena por ``pygame.draw.ellipse``
    siempre cae dentro de la curva, mientras que el borde exacto depende de
    cómo SDL/pygame-ce rasteriza el contorno -- muestrear ahí haría la
    prueba frágil a un detalle de implementación ajeno a este módulo."""
    from src.stages.boss_venado.presencias_venado import PRESENCIAS

    boss = types.SimpleNamespace(is_alive=False)
    scene, _ = _bare_scene_with_boss(boss)
    scene._gestor_presencias = GestorDePresencias(semilla=1)
    p = PRESENCIAS[0]
    scene._gestor_presencias._visible[p.id] = 5.0   # forzar visible sin depender del azar
    scene._gestor_presencias.tiempo_total = 0.0     # columna == columna_centro exacta

    surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)
    offset = pygame.Vector2(p.columna_centro - settings.INTERNAL_WIDTH / 2, 0.0)
    scene.dibujar_fondo(surface, offset)

    ancho = int(p.alto * 0.5)   # mismo cálculo que dibujar_fondo()
    x = int(p.columna_centro - offset.x)
    y = int((560.0 - p.alto) - offset.y)
    x_pantalla = x + ancho // 2
    y_pantalla = y + p.alto // 2
    assert surface.get_at((x_pantalla, y_pantalla)).a > 0


def test_sombra_que_cruza_se_reinicia_en_on_enter(app_headless):
    """Candado H-18: cada episodio de vida (respawn) debe poder volver a
    disparar el aviso -- la mecánica pura de disparar/reiniciar ya está
    probada en aislamiento en
    test_presencias_venado.py::test_sombra_que_cruza_se_puede_reiniciar_para_otro_episodio;
    aquí se prueba la integración REAL: que on_enter()/respawn() (H-18)
    llaman reiniciar() sobre el objeto YA conectado a la escena real, mismo
    patrón que test_conectar_efectos_sobrevive_al_respawn de arriba.

    CORRECCIÓN frente al Paso 11 tal como está escrito en el plan: el
    borrador construía un `EventoSombraQueCruza` suelto y probaba
    disparar()/reiniciar() sobre él directamente -- eso no ejercita la
    escena en absoluto (es exactamente el mismo caso ya cubierto por
    test_presencias_venado.py) y no habría detectado, por ejemplo, olvidar
    la llamada a `self._sombra_que_cruza.reiniciar()` en on_enter()."""
    scene = _push_real_scene(app_headless)
    scene._sombra_que_cruza._disparado = True   # simula un disparo del episodio anterior
    scene.respawn()   # H-18: reproduce on_enter() en cada reintento
    assert scene._sombra_que_cruza._disparado is False


# ── Tarea 6: silencio súbito + shake único + eco del gazebo ────────────────


class _AudioStub:
    """Doble mínimo del `AudioManager` real -- sólo registra llamadas a
    `activar_eco`, que es la única API de audio que toca esta tarea."""

    def __init__(self) -> None:
        self.eco_llamadas: list[bool] = []

    def activar_eco(self, activo: bool) -> None:
        self.eco_llamadas.append(activo)


class _CameraShakeStub:
    """Doble mínimo de `Camera` -- sólo registra llamadas a `apply_shake`,
    sin reproducir la física real de la sacudida (esa física ya tiene sus
    propias pruebas en test_camera.py; aquí sólo importa CUÁNTAS veces y con
    qué argumentos se llama)."""

    def __init__(self) -> None:
        self.offset = pygame.Vector2(0.0, 0.0)
        self.shakes: list[tuple] = []

    def apply_shake(self, amplitude, duration, direccion=None) -> None:
        self.shakes.append((amplitude, duration, direccion))


def test_shake_de_arena_usa_direccion_vertical_no_isotropico():
    """B-045 (REGISTRO-DE-BUGS.md, revisión de spec T6 2026-08-25): sin
    ``direccion``, ``Camera.apply_shake`` cae en la rama isotrópica de
    ``camera.py:409-411`` -- magnitud PLENA sin envolvente de decaimiento --
    y eso rompía de forma intermitente el candado H-17
    (``test_camera_settles_correctly_across_arena_boundary_oscillation``,
    ~1 de cada 2 corridas: offset final ~2474-2477 en vez de 2480.0 exacto).
    El fix es pasar una dirección VERTICAL, mismo patrón que el STOMP del
    propio jefe (``boss_venado.py:1245``: ``self.efectos.sacudir(4.0, 0.2,
    (0.0, 1.0))``), que activa la onda con decaimiento de
    ``camera.py:412-431``."""
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._camera = _CameraShakeStub()
    scene._shake_de_arena_disparado = False
    scene._eco_activo = False
    scene.context = types.SimpleNamespace(audio=_AudioStub())
    scene._actualizar_silencio_y_shake_de_arena(2600.0)
    assert scene._camera.shakes == [(6.0, ARENA_SHAKE_DURATION, (0.0, 1.0))]


def test_shake_duration_invariante_bajo_arena_settle_duration():
    """B-045: si esto deja de cumplirse, el flaky de H-17 vuelve.

    ``ARENA_SHAKE_DURATION`` DEBE quedar estrictamente por debajo de
    ``ARENA_SETTLE_DURATION`` -- si algún cambio futuro (p. ej. la Tarea 8
    tocando esta zona, ver la nota de acople del docstring de
    ``_actualizar_silencio_y_shake_de_arena``) sube la duración del shake
    de arena a acercarse o superar la ventana de ease del H-17, el shake
    vuelve a seguir activo cuando ``_pin_camera_to_arena`` deja de
    sobrescribir ``offset.x``, y el offset final de la cámara deja de
    asentar exacto en ``ARENA_X0`` de forma intermitente (ver
    REGISTRO-DE-BUGS.md B-045 para el mecanismo completo)."""
    assert ARENA_SHAKE_DURATION < ARENA_SETTLE_DURATION


def test_actualizar_arena_dispara_shake_una_sola_vez_al_entrar():
    """El temblor es un golpe ÚNICO al cruzar el umbral -- volver a llamar el
    método mientras el jugador sigue dentro (o avanza más adentro) no debe
    repetirlo, mismo patrón "una sola vez por visita" que
    `_actualizar_silencio_y_shake` de stage4_1.py:1069-1092."""
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._camera = _CameraShakeStub()
    scene._shake_de_arena_disparado = False
    scene._eco_activo = False
    scene.context = types.SimpleNamespace(audio=_AudioStub())
    scene._actualizar_silencio_y_shake_de_arena(2480.0)
    scene._actualizar_silencio_y_shake_de_arena(2500.0)
    scene._actualizar_silencio_y_shake_de_arena(2600.0)
    assert len(scene._camera.shakes) == 1
    assert scene.context.audio.eco_llamadas == [True]


def test_eco_se_apaga_al_salir_de_la_arena():
    """El eco es estado del mezclador ligado a estar DENTRO del gazebo, no un
    disparo único como el shake: entrar lo enciende, salir lo apaga, y
    reentrar debe volver a encenderlo (candado aparte más abajo)."""
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._camera = _CameraShakeStub()
    scene._shake_de_arena_disparado = False
    scene._eco_activo = False
    scene.context = types.SimpleNamespace(audio=_AudioStub())
    scene._actualizar_silencio_y_shake_de_arena(2600.0)   # entra
    scene._actualizar_silencio_y_shake_de_arena(2000.0)   # sale
    assert scene.context.audio.eco_llamadas == [True, False]


def test_eco_se_reenciende_al_reentrar_a_la_arena():
    """Complemento del candado anterior: el eco no es un latch de una sola
    vez -- salir y volver a entrar debe reencenderlo, a diferencia del shake
    (que sí es de una sola vez por episodio, ver el test de arriba)."""
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._camera = _CameraShakeStub()
    scene._shake_de_arena_disparado = False
    scene._eco_activo = False
    scene.context = types.SimpleNamespace(audio=_AudioStub())
    scene._actualizar_silencio_y_shake_de_arena(2600.0)   # entra
    scene._actualizar_silencio_y_shake_de_arena(2000.0)   # sale
    scene._actualizar_silencio_y_shake_de_arena(2700.0)   # reentra
    assert scene.context.audio.eco_llamadas == [True, False, True]
    # el shake, en cambio, sigue disparado una sola vez en todo el episodio
    assert len(scene._camera.shakes) == 1


def test_on_exit_apaga_el_eco_si_seguia_activo(monkeypatch):
    """`on_exit()` es la red de seguridad si la escena termina con el eco
    encendido a mitad de la arena (salir a mitad de la pelea, cambiar de
    escena) -- mismo contrato que Stage4_1.on_exit (stage4_1.py:453-463,
    AUD-594): el eco es estado COMPARTIDO del mezclador, no de la escena, y
    dejarlo prendido contaminaría la escena siguiente.

    `StageScene.on_exit` se reemplaza por un no-op vía monkeypatch: lo que
    se prueba aquí es sólo la parte propia de esta escena (apagar el eco
    ANTES de delegar), no todo el ciclo de vida heredado -- ese ciclo ya
    tiene sus propias pruebas, y ejercitarlo aquí exigiría un doble con
    _hud/_msg_box/_dialogue/_subtitles/_achievements/_bestiary/context.clock,
    ninguno de los cuales toca esta tarea."""
    monkeypatch.setattr(StageScene, "on_exit", lambda self: None)
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._eco_activo = True
    audio = _AudioStub()
    scene.context = types.SimpleNamespace(audio=audio)
    scene.on_exit()
    assert audio.eco_llamadas == [False]


def test_on_exit_no_llama_al_eco_si_ya_estaba_apagado(monkeypatch):
    """Sin ruido: si el jugador nunca llegó a la arena (`_eco_activo` sigue
    en su valor inicial `False`), salir de la escena no debe emitir una
    llamada de apagado de más."""
    monkeypatch.setattr(StageScene, "on_exit", lambda self: None)
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._eco_activo = False
    audio = _AudioStub()
    scene.context = types.SimpleNamespace(audio=audio)
    scene.on_exit()
    assert audio.eco_llamadas == []


def test_on_enter_reinicia_los_flags_de_shake_y_eco(app_headless):
    """Candado H-18: cada episodio de vida (respawn) debe poder volver a
    disparar el shake y a encender el eco -- si `on_enter()` no reiniciara
    estos flags, morir DENTRO de la arena y reaparecer en el `PlayerSpawn`
    (fuera de ella) dejaría `_shake_de_arena_disparado` en `True` para
    siempre y el segundo cruce de `ARENA_X0` del episodio nuevo no temblaría.
    Mismo patrón que test_sombra_que_cruza_se_reinicia_en_on_enter, arriba."""
    scene = _push_real_scene(app_headless)
    scene._shake_de_arena_disparado = True   # simula un episodio anterior ya disparado
    scene._eco_activo = True
    scene.respawn()   # H-18: reproduce on_enter() en cada reintento
    assert scene._shake_de_arena_disparado is False
    assert scene._eco_activo is False


# ── Tarea 7: sistema Atencion (quietud revela) ──────────────────────────────


def _bare_scene_with_atencion(x: float = 100.0) -> tuple[BossVenadoScene, list[int]]:
    """Construye una escena `BossVenadoScene` 'bare' (vía `__new__`, sin
    `__init__`) cableada solo con lo que `_actualizar_quietud_revela`
    necesita: una `Atencion` fresca, el cooldown en 0, un jugador quieto en
    `x`, y `_reproducir_revelacion` sustituido por un stub que registra cada
    llamada en la lista devuelta -- mismo patrón de doble mínimo que
    `_bare_scene_with_boss`/`_HudStub` arriba, factorizado (revisión de
    calidad, 2026-08-25) porque los cuatro tests de esta sección repetían
    este mismo cableado casi palabra por palabra. Los tests que necesitan
    mover al jugador cuadro a cuadro (p. ej. el del DodgerBot) simplemente
    reasignan `scene._player` después de llamar a este helper."""
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._atencion = Atencion()
    scene._cooldown_revelacion = 0.0
    scene._player = types.SimpleNamespace(rect=pygame.Rect(int(x), 528, 32, 32), facing_direction=1)
    revelaciones: list[int] = []
    scene._reproducir_revelacion = lambda: revelaciones.append(1)
    return scene, revelaciones


def test_quietud_revela_con_cooldown_anti_farmeo():
    """La 'revelación' de este boss es un SFX espacial disparado tras
    QUIETUD_PARA_REVELAR segundos quieto (ver _reproducir_revelacion) --
    no depende de presencias_venado.py, así que el test no necesita montar
    ningún GestorDePresencias."""
    scene, revelaciones = _bare_scene_with_atencion()
    dt = 1 / 60
    for _ in range(int(3.5 * 60)):   # 3.5s quieto -- por encima del umbral de 3s del spec
        scene._atencion.observar(scene._player, dt)
        scene._actualizar_quietud_revela(dt)
    assert len(revelaciones) == 1
    # sigue quieto: el cooldown evita una segunda revelacion inmediata
    for _ in range(60):
        scene._atencion.observar(scene._player, dt)
        scene._actualizar_quietud_revela(dt)
    assert len(revelaciones) == 1


def test_cooldown_expira_y_permite_revelar_de_nuevo():
    """Complemento del candado anterior: el enfriamiento no es permanente --
    tras COOLDOWN_REVELACION segundos, si el jugador SIGUE quieto, la
    quietud vuelve a revelar. Sin este candado, un cooldown que nunca
    expirase (p. ej. un bug de signo en la resta de `_actualizar_quietud_
    revela`) pasaría igual de bien la prueba de arriba, que sólo cubre 1s de
    enfriamiento -- mismo motivo por el que Tarea 6 empareja
    test_eco_se_apaga_al_salir_de_la_arena con
    test_eco_se_reenciende_al_reentrar_a_la_arena en vez de conformarse con
    uno solo."""
    scene, revelaciones = _bare_scene_with_atencion()
    dt = 1 / 60
    # margen amplio por encima de QUIETUD + COOLDOWN + QUIETUD: el jugador
    # nunca se mueve, así que en cuanto el enfriamiento llega a 0 la
    # revelación vuelve a dispararse de inmediato (la quietud ya lleva rato
    # por encima del umbral).
    total_frames = int((QUIETUD_PARA_REVELAR + COOLDOWN_REVELACION + QUIETUD_PARA_REVELAR + 0.5) * 60)
    for _ in range(total_frames):
        scene._atencion.observar(scene._player, dt)
        scene._actualizar_quietud_revela(dt)
    assert len(revelaciones) == 2


def test_quietud_no_revela_a_partir_de_sombra_x0():
    """Acote de la revisión de calidad, 2026-08-25 (ver el docstring de
    `_actualizar_quietud_revela`): esta revelación reutiliza el mismo
    bramido que `EventoSombraQueCruza`, así que dejarla sonar en
    `[SOMBRA_X0, ∞)` competiría con el aviso ÚNICO de esa clase (Tarea 5) y
    seguiría sonando dentro de la arena, con el jefe ya revelado. Por debajo
    de `SOMBRA_X0` (Actos 1-2) la revelación debe seguir funcionando -- ahí
    es donde tiene sentido premiar la quietud."""
    dt = 1 / 60
    frames = int(3.5 * 60)   # 3.5s quieto -- por encima del umbral de 3s del spec

    # x=SOMBRA_X0+100 (2300 con la SOMBRA_X0 actual, 2200): acotada, cero
    # revelaciones aunque se quede quieto -- calculado desde la constante
    # real (no hardcodeado) para no desalinearse si SOMBRA_X0 cambia.
    scene_acotada, revelaciones_acotadas = _bare_scene_with_atencion(x=SOMBRA_X0 + 100.0)
    for _ in range(frames):
        scene_acotada._atencion.observar(scene_acotada._player, dt)
        scene_acotada._actualizar_quietud_revela(dt)
    assert revelaciones_acotadas == []

    # x=SOMBRA_X0-1400 (800): por debajo del umbral, sigue revelando igual que siempre.
    scene_normal, revelaciones_normales = _bare_scene_with_atencion(x=SOMBRA_X0 - 1400.0)
    for _ in range(frames):
        scene_normal._atencion.observar(scene_normal._player, dt)
        scene_normal._actualizar_quietud_revela(dt)
    assert len(revelaciones_normales) == 1


def test_atencion_se_reinicia_en_on_enter(app_headless):
    """Candado H-18, mismo patrón que test_on_enter_reinicia_los_flags_de_
    shake_y_eco (arriba) y test_sombra_que_cruza_se_reinicia_en_on_enter:
    un episodio nuevo (muerte + respawn) empieza sin quietud acumulada y sin
    el enfriamiento del intento anterior colgado. Sin este reinicio, morir
    justo después de una revelación reaparecería con el cooldown todavía
    corriendo (bloqueando una revelación legítima del episodio nuevo), o
    morir tras 3s quieto reaparecería con la quietud ya heredada y
    revelaría de inmediato en el cuadro 1, sin que el jugador se haya
    detenido en absoluto en este episodio."""
    scene = _push_real_scene(app_headless)
    scene._atencion.quietud = 5.0   # simula quietud acumulada del episodio anterior
    scene._cooldown_revelacion = 12.0   # simula un enfriamiento a mitad de cuenta
    scene.respawn()   # H-18: reproduce on_enter() en cada reintento
    assert scene._atencion.quietud == 0.0
    assert scene._cooldown_revelacion == 0.0


def test_dodger_en_movimiento_constante_nunca_dispara_revelacion():
    """Candado de no-regresión para `fairness` (0 golpes del DodgerBot, ver
    la sección "Verificación de no-regresión" de la Tarea 7 del plan): un
    jugador que se mueve más de TOLERANCIA_DE_QUIETUD_PX cada cuadro -- el
    comportamiento constante de esquive del DodgerBot -- jamás debe
    acumular quietud, así que `_actualizar_quietud_revela` no debe llamar
    nunca a `_reproducir_revelacion`, sin importar cuánto tiempo pase."""
    scene, revelaciones = _bare_scene_with_atencion()   # x=100.0 inicial; se sobrescribe cada cuadro abajo
    dt = 1 / 60
    x = 100.0
    for i in range(10 * 60):   # 10s de esquive continuo, muy por encima del umbral
        x += 10.0 if i % 2 == 0 else -10.0   # vaivén constante, nunca queda "quieto"
        scene._player = types.SimpleNamespace(
            rect=pygame.Rect(int(x), 528, 32, 32), facing_direction=1)
        scene._atencion.observar(scene._player, dt)
        scene._actualizar_quietud_revela(dt)
    assert revelaciones == []


def test_cutscene_no_bloqueante_no_congela_al_jugador(app_headless):
    """Candado del spec Tarea 9 / S6.1 punto 2: `bloquea=false` debe
    significar que el gameplay NO se pausa mientras la cutscene corre.

    Nota de diseño de la prueba: comparar dos corridas (con/sin cutscene)
    mutando `stage_data.escenas` DESPUÉS de `on_enter()` no funciona --
    `_montar_director_de_escenas()` (cinematicas.py:47-79) ya construyó el
    `CutsceneDirector` a partir de esa lista en el momento de la
    construcción de la escena (dentro de `_push_real_scene()` ->
    `on_enter()`), así que una mutación posterior no desarma nada que ya se
    armó. En vez de esa comparación inválida, se verifica DIRECTAMENTE que
    el jugador avanza cuadro a cuadro mientras la cutscene (disparada desde
    el frame 0 -- el `PlayerSpawn` en x=48 cae dentro del rect x=0..96 de
    `Cutscene_Presentacion_01` desde el primer fotograma, verificado
    empíricamente contra el motor real) está activa.

    Guion vigente desde la corrección del 2026-08-25 (sin orden `camara`,
    ver `_cutscene_object_xml()` en el generador): `esperar 0.6` + `temblor
    0.18 3.0` (instantáneo para el guion, aunque anime la cámara aparte) +
    `esperar 1.0` ≈ 1.6 s totales -- el bucle de 60 cuadros de abajo cubre
    de sobra la ventana en la que la cutscene sigue activa.

    PORTABILIDAD (Gate 5 del puente, 2026-08-25): esta prueba se apoyaba en
    `playtest.harness.PlaytestSession`, que solo existe en el LAB -- el
    Gate 5 de `sync_back` corre la suite del boss EN EL REPO REAL SELLADO
    (sin el paquete `playtest` en `sys.path`), y ese import moría con
    `ModuleNotFoundError` (bloqueante de la promoción; ver
    REGISTRO-DE-BUGS.md). Los tests de la zona del boss deben ser
    AUTOCONTENIDOS -- corren tal cual en el real, sin el lab. El fix
    reemplaza `PlaytestSession` por el mismo patrón `app_headless`/
    `_push_real_scene` que ya usan `test_conectar_efectos_sobrevive_al_
    respawn` y los candados de las Tareas 6/7 de este archivo, reproduciendo
    a mano -- vía el `_paso()` local de abajo -- exactamente la secuencia
    que `PlaytestSession.step()` hacía por dentro (`input_manager.pump()` ->
    `event_bus.dispatch()`, el gotcha de cola del EventBus, ->
    `scene_manager.update()` -> `transition.update()`), sin depender del
    paquete `playtest` para nada."""
    from itertools import pairwise

    from src.engine.input.action_map import DEFAULT_KEY_BINDINGS, Action

    app = app_headless
    scene = _push_real_scene(app)
    dt = 1.0 / 60.0
    tecla_derecha = DEFAULT_KEY_BINDINGS[Action.MOVE_RIGHT][0]

    def _paso(events: list[pygame.event.Event]) -> None:
        app.input_manager.pump(events)
        app.event_bus.dispatch()          # EventBus es de cola -- antes de update()
        app.scene_manager.update(dt)
        app.scene_manager.transition.update(dt)

    _paso([pygame.event.Event(pygame.KEYDOWN, {"key": tecla_derecha})])
    posiciones = [scene._player.rect.centerx]
    try:
        for _ in range(60):   # 1s sosteniendo la tecla -- cubre de sobra el guion (~1.6s de esperar+temblor)
            _paso([])
            posiciones.append(scene._player.rect.centerx)
    finally:
        # soltar la tecla -- app_headless es de alcance de MODULO (compartido
        # con el resto de las pruebas de este archivo que lo usan), no hay
        # que dejarla retenida en input_manager._held para quien venga después.
        _paso([pygame.event.Event(pygame.KEYUP, {"key": tecla_derecha})])
    # el jugador debe avanzar en la GRAN mayoría de los cuadros -- unos
    # pocos iguales por fricción/colisión al arrancar son normales, una
    # racha larga congelada NO lo sería (eso es justo lo que `bloquea=true`
    # produciría).
    #
    # Umbral <= 3 (revisión de calidad 2026-08-25): de los 61 cuadros
    # muestreados (60 pasos + la posición inicial), a lo sumo 3 pueden salir
    # iguales -- margen generoso para el primer cuadro de arranque
    # (fricción/colisión al iniciar el movimiento) sin dejar pasar un
    # congelamiento real. La comparación no es contra cero: con
    # `bloquea=true` este mismo bucle produciría `congelados` cercano a
    # **60** (el jugador entero congelado durante los ~1.6s del guion,
    # bien dentro de la ventana de 1s muestreada aquí) -- <= 3 separa con
    # margen amplio "avanza con normalidad" de "está pausado".
    congelados = sum(1 for a, b in pairwise(posiciones) if a == b)
    assert congelados <= 3
    assert posiciones[-1] > posiciones[0]


def test_dibujar_mundo_alimenta_de_verdad_al_gestor_de_luciernagas(monkeypatch):
    """Fix del coordinador (revisión de calidad de la Tarea 12, punto MEDIA):
    la versión anterior de este test se llamaba "candado de wiring" pero solo
    instanciaba ``GestorDeLuciernagas`` a mano y llamaba
    ``actualizar_desde_superficie`` directamente -- eso NO ejercía el wiring
    real (``BossVenadoScene.dibujar_mundo`` -> ``gestor.actualizar_desde_superficie``,
    ver ese método en boss_venado_scene.py), solo probaba el gestor aislado --
    cobertura que YA vive, mejor, en test_luciernagas_venado.py. Este test
    reemplaza aquel: llama al método REAL ``scene.dibujar_mundo(surface)`` con
    una superficie oscura/clara controlada y confirma que
    ``scene._gestor_luciernagas`` se alimentó de verdad -- ``cantidad_objetivo``
    Y ``factor_de_halo`` cambiaron en el sentido ya medido por
    test_luciernagas_venado.py (más oscuro -> más luciérnagas y factor de
    halo más alto).

    ``monkeypatch.setattr(StageScene, "dibujar_mundo", ...)`` neutraliza el
    ``dibujar_mundo`` heredado -- mismo patrón que
    ``test_la_escena_ya_no_pisa_el_phase_count_del_hud`` usa para
    ``update()`` más arriba: el ``dibujar_mundo`` real de ``StageScene`` (vía
    el mixin ``DibujoDeEscenario``) empieza con ``surface.fill(BG_COLOR)`` y
    dibuja mapa/luz reales -- sin neutralizarlo, el color de control que este
    test pinta en ``surface`` se borraría antes de llegar a la línea que
    alimenta al gestor, y no habría forma determinista de controlar si la
    lectura es "oscura" o "clara" sin depender de la iluminación real del TMX
    en una posición de cámara arbitraria. El override PROPIO de esta escena
    (``BossVenadoScene.dibujar_mundo``) sigue corriendo tal cual -- solo su
    llamada interna a ``super().dibujar_mundo(surface)`` queda anulada.

    ``_bare_scene_with_boss`` (el helper de este archivo) usa ``__new__``, no
    ``__init__`` -- así que ``_gestor_luciernagas`` no existe en el objeto
    hasta que este test lo cablea a mano, igual que ya hace con
    ``_player``/``_stage_data``/``_hud``."""
    from src.stages.boss_venado.luciernagas_venado import FRECUENCIA_DE_MUESTREO, GestorDeLuciernagas

    monkeypatch.setattr(StageScene, "dibujar_mundo", lambda self, surface: None)
    boss = types.SimpleNamespace(is_alive=False)

    scene_oscura, _ = _bare_scene_with_boss(boss)
    scene_oscura._gestor_luciernagas = GestorDeLuciernagas()
    oscura = pygame.Surface((800, 600))
    oscura.fill((5, 5, 8))
    for _ in range(FRECUENCIA_DE_MUESTREO):   # garantiza al menos un muestreo real
        scene_oscura.dibujar_mundo(oscura)

    scene_clara, _ = _bare_scene_with_boss(boss)
    scene_clara._gestor_luciernagas = GestorDeLuciernagas()
    clara = pygame.Surface((800, 600))
    clara.fill((240, 240, 240))
    for _ in range(FRECUENCIA_DE_MUESTREO):
        scene_clara.dibujar_mundo(clara)

    assert scene_oscura._gestor_luciernagas.cantidad_objetivo > scene_clara._gestor_luciernagas.cantidad_objetivo
    assert scene_oscura._gestor_luciernagas.factor_de_halo > scene_clara._gestor_luciernagas.factor_de_halo


def test_build_player_halo_factor_por_defecto_es_identico_al_historico():
    """Fix académico del coordinador (Tarea 12, "refuerzo REAL del halo"):
    _build_player_halo(factor=FACTOR_HALO_MINIMO) -- el default -- debe
    seguir produciendo EXACTAMENTE el mismo halo que antes de este fix
    (comportamiento histórico intacto), píxel a píxel, no solo "por encima
    del piso". Compara ``_build_player_halo()`` (sin argumento, la misma
    llamada que hace test_player_halo_never_silently_disabled arriba) contra
    ``_build_player_halo(FACTOR_HALO_MINIMO)`` (el mismo factor, explícito) --
    deben ser byte-idénticos porque multiplicar por 1.0 no cambia ningún
    resultado de int()."""
    from src.stages.boss_venado.luciernagas_venado import FACTOR_HALO_MINIMO

    sin_argumento = BossVenadoScene._build_player_halo()
    con_factor_uno = BossVenadoScene._build_player_halo(FACTOR_HALO_MINIMO)
    assert pygame.image.tobytes(sin_argumento, "RGBA") == pygame.image.tobytes(con_factor_uno, "RGBA")


def test_build_player_halo_factor_mayor_sube_el_pico_por_encima_del_piso():
    """factor > FACTOR_HALO_MINIMO (oscuridad medida por el histograma) debe
    producir un pico EFECTIVO mayor que con el factor histórico, y seguir por
    encima del piso de test_player_halo_never_silently_disabled (sum(rgb) >=
    3*25 == 75) -- el factor SOLO AUMENTA desde el piso, nunca lo debilita."""
    from src.stages.boss_venado.luciernagas_venado import FACTOR_HALO_MAXIMO

    halo_base = BossVenadoScene._build_player_halo(1.0)
    halo_reforzado = BossVenadoScene._build_player_halo(FACTOR_HALO_MAXIMO)
    centro = (PLAYER_HALO_RADIUS, PLAYER_HALO_RADIUS)
    pico_base = sum(halo_base.get_at(centro)[:3])
    pico_reforzado = sum(halo_reforzado.get_at(centro)[:3])
    assert pico_reforzado > pico_base
    assert pico_reforzado >= 3 * 25   # mismo piso que test_player_halo_never_silently_disabled
