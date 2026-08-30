"""
Modulo: capture_map
Sistema: stages.boss_venado.tools
Descripcion: arnes de capturas de pantalla headless dentro del motor para el
mapa de la arena del boss "Residencias al Crepusculo" (Tarea 6, verificacion
en el juego). Arranca la App real (el mismo pipeline que usa el
``--boss boss_venado`` de main.py) bajo drivers dummy de video/audio de SDL,
empuja BossVenadoScene (todavia el stub original del profesor -- STAGE_ID/
STAGE_NAME/ZONE mas la ruta del TMX, nada mas -- asi que esto ejercita
StageScene directamente desde el framework), teletransporta al jugador a
tres posiciones x a lo largo del corredor/arena, y vuelca la superficie de
render interna real del motor (settings.INTERNAL_WIDTH x INTERNAL_HEIGHT,
limpiada cada frame con settings.BG_COLOR) a PNG. Adaptado de la base
probada ``backups\\pre-reset-2026-07-21\\src\\tools\\capture_frames.py``
(referencia de solo lectura, no modificada) -- el mismo pipeline de
arranque de App / avance manual de dt, extendido de 2 capturas fijas a 3
parametrizadas y con dos compensaciones SOLO-DE-CAPTURA documentadas abajo.

Captura cinco frames (ronda-11: el mapa ampliado a 205 columnas con una
nueva zona CARPORT; ronda-12: el boss movido al extremo derecho de la
arena y una 5ta captura "final" anadida), todas con los PIES del jugador
en world y=560 (tope del piso del TMX, ver el objeto de colision ``Floor``
en y=560 en boss_venado.tmx):
  1. spawn   -- x=48   (la propia posicion de PlayerSpawn_01 del TMX).
  2. carport -- x=1280 (la nueva bahia de estacionamiento, zona CARPORT
     columnas 65-95).
  3. arcos   -- x=2000 (corredor, antes del limite de la arena en x=2480).
  4. arena   -- x=2880 (dentro de ArenaZone_01/CameraLock_01, encuadrando
     la pieza escenica del gazebo; BossVenado_01 ya no spawnea aqui desde
     la ronda-12).
  5. final   -- x=3150 (ronda-12, feedback del usuario "pon el boss al
     final del mapa": cerca del nuevo spawn de BossVenado_01 en x=3168,
     pasado el gazebo y cerca de RightWall_Arena en x=3264, para verificar
     que el boss cae ahi).

Esta herramienta solo *conduce* la escena a traves del loop publico de
update()/draw() y toca los campos publicos position/velocity/rect del
Player ya instanciado para teletransportar, mas dos compensaciones de
alcance estrecho, solo-de-captura, para problemas conocidos del motor
(ambas documentadas en detalle en ``reports\\map_residencias\\CAMERALOCK.md``
y ``reports\\FINDINGS.md`` H-10) -- NO modifica src/engine, src/framework, ni
el TMX.

COMPENSACION SOLO-DE-CAPTURA 1 -- interruptor global de CameraLock
(aprobado por el arquitecto solo para esta herramienta de captura): el TMX
declara CameraLock_01 (lock_x=lock_y=true) cubriendo la arena.
``Camera.set_camera_locks()`` (src/framework/stage/camera.py:63-67) **no**
condiciona en absoluto al rect del lock -- hace
``self._is_locked_x = any(l.lock_x for l in locks)`` sobre la lista
COMPLETA, incondicionalmente, cada frame (llamado desde
``StageScene.update()`` linea ~612). Asi que la presencia de cualquier
objeto CameraLock en el TMX congela la camara en AMBOS ejes para todo el
stage, desde el frame 0, incluyendo el corredor -- no existe ningun
condicionamiento de "solo una vez que el jugador entra al rect" en ninguna
parte del motor (verificado contra
``tests/test_camera.py::TestCameraLockZones``, que solo verifica el
booleano, nunca el rect). Dejado tal cual, cada captura de abajo mostraria
el frame de spawn congelado en su lugar. Compensacion: inmediatamente
despues de que la escena se empuja, este script vacia
``scene._stage_data.camera_locks = []``. Como ``StageScene.update()``
relee ``stage.camera_locks`` (no una copia en cache) cada frame, una
lista vacia mantiene ambos ejes desbloqueados por el resto de la vida de
este proceso. Esto es una mutacion de datos sobre la instancia de
StageData ya cargada hecha desde el arnes, no una edicion al TMX ni al
archivo del motor que lo lee.

COMPENSACION SOLO-DE-CAPTURA 2 -- H-10 (bug de motor conocido, ver
``reports\\FINDINGS.md`` buscar "H-10"): ``StageScene`` nunca llama al
unico metodo de pyscroll que realmente reposiciona el buffer del tilemap
(``BufferedRenderer.center()`` / ``PyscrollGroup.center()``,
.venv-boss/Lib/site-packages/pyscroll/{orthographic,group}.py). En vez de
eso solo sobrescribe directamente
``stage.map_layer._map_layer.view_rect`` (un simple campo pygame.Rect que
la ruta de blit real de pyscroll, ``BufferedRenderer._render_map()``,
nunca lee -- lee ``_x_offset``/``_y_offset``/``_tile_view``/``_buffer``,
que solo se tocan dentro de ``center()``). Efecto neto: ``camera.offset``
(la clase Camera, framework) avanza correctamente frame a frame, las
entidades (dibujadas por separado via el propio ``draw(surface,
camera_offset)`` de cada entidad) se mueven correctamente en relacion a
ella, pero el *fondo* de tiles de pyscroll queda pegado a donde sea que
``_initialize_buffers()`` lo dejo cuando el mapa se cargo por primera vez
-- es decir, la esquina alrededor del spawn -- sin importar cuanto viajen
el jugador/la camara. Confirmado independientemente tambien para
``stage0`` (misma base StageScene), asi que es un bug de motor compartido,
no algo introducido por esta herramienta ni por BossVenadoScene (el stub
no toca pyscroll/map_layer en absoluto). Compensacion: el propio helper de
paso por frame de este script (``_step``, abajo) llama a la API real de
pyscroll, ``stage.map_layer.center((camera.offset.x + INTERNAL_WIDTH / 2,
camera.offset.y + INTERNAL_HEIGHT / 2))`` (``center()`` quiere el CENTRO
del viewport, no su esquina superior izquierda, de ahi el ``+ w/2, + h/2``
sobre el ``camera.offset`` de estilo esquina-superior-izquierda que las
llamadas ``draw()`` de las entidades ya restan directamente) -- justo
despues de que ``scene_manager.update()`` calcula el offset de camara
final del frame y justo antes de que ``app._draw()`` lo consuma, cada
frame. Esto refleja el mismo patron de correccion previamente verificado
(``reports\\FINDINGS.md`` H-10, "Correccion aplicada") que
``BossVenadoScene`` aplico en su propio ``update()`` (metodo
``_sync_map_render()``) desde el rewrite de fase 2 (2026-07-29) hasta su
retiro el 2026-08-26 -- retirado alla por redundante: el motor centra el
fondo por su cuenta cada frame en su propio paso de dibujo
(``DrawingSystem._draw_stage_layers``, drawing_system.py:573-579,
AUD-039, que corre dentro de ``dibujar_mundo()`` -> ``self._drawing.draw()``,
llamado desde ``App._draw()`` por despacho de pato -- ver ``app.py:584-586``
y la seccion H-28/B-032 de arriba); ver la seccion H-10 (RETIRADA) del
docstring de modulo de ``boss_venado_scene.py`` para el detalle completo
y la evidencia. Esa retirada fue solo de la ESCENA -- el codigo de la
funcion ``_sync_map_render()`` definida mas abajo en este mismo archivo
NO se toca en esta tarea, sigue llamandose desde ``_step`` tal cual. Nota honesta para quien
audite despues (fuera del alcance de esta tarea, que solo corrige
referencias documentales tras el retiro en la escena): ``_step`` SI llama
a ``app._draw()`` cada frame (linea de abajo, justo despues de esta
compensacion) y ese camino real SI atraviesa ``dibujar_mundo()`` de la
misma ``BossVenadoScene`` -- el mismo AUD-039 que volvio redundante la
compensacion de la escena tambien corre aqui, DESPUES de esta llamada
propia, con la misma formula. No se verifico con una corrida A/B propia
de esta herramienta (la sonda del 2026-08-25 solo cubrio el camino de la
escena/arnes de playtest) si retirar tambien esta copia deja el mismo
observable intacto; se deja documentado como hallazgo abierto para un
dictamen futuro, no como parte de este retiro. Ningun archivo de
src/engine o src/framework es editado por ninguna de las dos
compensaciones; ambas actuan sobre objetos de runtime ya construidos
(StageData, PyscrollGroup) desde afuera, a traves de su API publica
existente.

NOTA HISTORICA (antiguo WORKAROUND 3, ahora eliminado) -- desajuste entre
el constructor de BossVenado_01 y el TMX: antes esta herramienta
descubrio que ``gen_level_residencias.py`` emitia propiedades
``arena_origin_x``/``arena_origin_y`` (tipadas float) en ``BossVenado_01``,
copiadas de un generador reemplazado emparejado con un constructor de boss
MAS ANTIGUO que aceptaba esos kwargs. El ``boss_venado.py`` ACTUAL
(original del profesor, reseteado) tiene un simple
``__init__(self, spawn_position)``, y ``StageLoader.load()`` pasa cada
propiedad de objeto del TMX como argumento de palabra clave a la clase de
la entidad, asi que esas props hacian que lanzara ``TypeError`` y abortara
toda la carga del stage -- rompiendo tambien el ``python main.py --boss
boss_venado`` real. Esto ahora esta CORREGIDO en la fuente:
``gen_level_residencias.py`` emite BossVenado_01 como un simple objeto
punto sin propiedades, asi que el boss se instancia normalmente y aparece
en la captura de la arena -- ya no se necesita ningun workaround de
registro aqui. Un test de regresion,
``tests/test_map_residencias.py::test_entities_instantiate_from_tmx``,
carga el TMX con "BossVenado" registrado y verifica que el boss se
instancia.

Uso (desde el directorio ``game`` del LAB, drivers dummy para que no se
requiera ninguna ventana/dispositivo de audio real -- tambien forzados
mas abajo para que el script sea robusto incluso si quien lo llama olvida
las variables de entorno):

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
        path/to/python.exe src/stages/boss_venado/tools/capture_map.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Debe fijarse antes de que pygame se importe en cualquier lugar (App.__init__
# llama a pygame.init()/pygame.mixer.init()) para que no se toque ningun
# dispositivo real de pantalla/audio en este entorno headless.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# tools/ -> boss_venado/ -> stages/ -> src/ -> game/ (raiz del juego del LAB,
# el equivalente de legacyofInfest/ en el proyecto real).
_GAME_ROOT = Path(__file__).resolve().parents[4]
os.chdir(_GAME_ROOT)  # StageLoader.load() resuelve la ruta del TMX relativa al cwd.
sys.path.insert(0, str(_GAME_ROOT))

import pygame  # noqa: E402

from src.engine.core import settings  # noqa: E402
from src.engine.core.app import App  # noqa: E402
from src.framework.entities.boss_base import BossBase  # noqa: E402
from src.stages.boss_venado.boss_venado_scene import BossVenadoScene  # noqa: E402

# Raiz del LAB (un nivel arriba de game/) -- reports/ vive al lado de game/, no
# anidado dentro del arbol del motor.
OUT_DIR = _GAME_ROOT.parent / "reports" / "map_residencias"
DT: float = 1.0 / 60.0
SETTLE_FRAMES: int = 400  # asentar el tiempo suficiente (>6s) para que el HUD
#                           transitorio de intro (banner de stage ~2.9s + TIP
#                           tutorial "move" 6s) expire, para que las capturas
#                           muestren la vista real en ESTADO ESTABLE -- el arte
#                           del mapa, no overlays de intro cubriendo cielo/suelo.

# (nombre, world x, feet-y) -- feet y siempre es 560 (tope de colision Floor del TMX).
# RONDA-11: cuatro posiciones, una por cada ventana de camara de ~800px del mapa
# ampliado de 205 columnas (spawn 0-50, carport 50-100, arcos 100-150, arena 150-205).
# RONDA-12 (feedback del usuario: "pon el boss al final del mapa"): una 5ta
# posicion "final" anadida cerca del nuevo spawn del boss (x=3168) para que su
# placeholder sea visible en las capturas, pasado el gazebo y cerca de RightWall_Arena.
CAPTURES: list[tuple[str, float, float]] = [
    ("spawn", 48.0, 560.0),     # PlayerSpawn_01 del TMX
    ("carport", 1280.0, 560.0),  # zona CARPORT (columnas 65-95), la bahia de estacionamiento
    ("arcos", 2000.0, 560.0),   # corredor, antes del limite de la arena en x=2480
    ("arena", 2880.0, 560.0),   # dentro de ArenaZone_01/CameraLock_01, encuadra el gazebo
    ("final", 3150.0, 560.0),   # cerca del nuevo spawn de BossVenado_01 (x=3168), extremo final del mapa
]


def _sync_map_render(scene: BossVenadoScene) -> None:
    """COMPENSACION SOLO-DE-CAPTURA 2 (H-10, ver docstring del modulo): llama
    a la API real ``center()`` de pyscroll para que el fondo de tiles
    realmente siga a ``camera.offset`` en lugar de quedar pegado a la
    ventana de buffer inicial. No hace nada de forma defensiva si
    stage/map_layer aun no estan listos (p. ej. el primerisimo tick antes
    de que on_enter() haya corrido, o un stage sin tilemap)."""
    stage = scene._stage_data
    if stage is None:
        return
    map_layer = getattr(stage, "map_layer", None)
    if map_layer is None:
        return
    offset = scene._camera.offset
    map_layer.center((
        offset.x + settings.INTERNAL_WIDTH / 2,
        offset.y + settings.INTERNAL_HEIGHT / 2,
    ))


def _pin_boss(boss: BossBase | None, home: pygame.Vector2 | None) -> None:
    """COMPENSACION SOLO-DE-CAPTURA 3 -- mantiene al boss fijo en su spawn del TMX.

    La IA de movimiento original del ``BossVenado`` del profesor usa
    constantes de arena a escala 320x224 (``ARENA_W = 320``) pero opera sobre
    coordenadas de MUNDO, asi que en su primerisimo ``update()`` el clamp de
    deriva senoidal (``if position.x > ARENA_W - 32``) arranca al boss de su
    spawn de mundo (x=3168, dentro de la arena) hacia world x~44 -- lanzandolo
    fuera de la arena y hacia el cielo de la PRADERA, donde luego flota por
    los frames de arte de spawn/arcos y desaparece del frame de la arena. Ese
    bug de clamp de arena a escala 320 es de la IA del boss del profesor,
    fuera del alcance de esta herramienta de captura de MAPA (registrado
    como entrada de FINDINGS). Para capturar el MAPA con el boss donde el
    TMX realmente lo coloca, re-fijamos al boss a su spawn cada frame
    DESPUES del update de la escena (que lo movio) y ANTES del draw -- una
    mutacion de runtime sobre la entidad ya construida, exactamente como
    las dos compensaciones anteriores; no se edita ningun archivo de
    motor/TMX/boss."""
    if boss is None or home is None:
        return
    boss.position.update(home)
    boss.rect.x = int(home.x)
    boss.rect.y = int(home.y)
    if hasattr(boss, "velocity"):
        boss.velocity.update(0.0, 0.0)


def _step(app: App, scene: BossVenadoScene, boss: BossBase | None = None,
          boss_home: pygame.Vector2 | None = None, dt: float = DT) -> None:
    """Una iteracion de exactamente lo que hace el cuerpo del loop de
    App.run() por frame, menos el ritmo en tiempo real (app.clock.tick()) y
    el sondeo de input -- conducimos dt manualmente para que las capturas no
    cuesten segundos de reloj real por nada, y de todos modos no hay ningun
    dispositivo de input real bajo SDL dummy. La sincronizacion de H-10
    corre entre update() y draw(), es decir, despues de que el offset de
    camara es definitivo para este frame pero antes de que el buffer de
    pyscroll se blitee a partir de el. La fijacion del boss (COMPENSACION 3)
    tambien se ubica entre update() y draw()."""
    app.scene_manager.update(dt)
    _pin_boss(boss, boss_home)
    app.scene_manager.transition.update(dt)
    _sync_map_render(scene)
    app._draw()
    pygame.event.pump()


def _find_boss(scene: BossVenadoScene) -> BossBase | None:
    stage = scene._stage_data
    if stage is None:
        return None
    for entity in stage.entity_list:
        if isinstance(entity, BossBase):
            return entity
    return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    app = App()

    # (Antiguo WORKAROUND 3 eliminado.) El desajuste entre el constructor de
    # BossVenado_01 y el TMX se corrigio en la fuente: gen_level_residencias.py
    # ya no emite las propiedades sueltas arena_origin_x/y, asi que
    # ensure_registered() de App() puede mantener "BossVenado" registrado y
    # StageLoader.load() instancia al boss normalmente -- ahora aparece en la
    # captura de la arena. Protegido contra regresion por
    # tests/test_map_residencias.py::test_entities_instantiate_from_tmx.
    scene = BossVenadoScene(app.context)
    app.scene_manager.push(scene)  # awake() -> start() -> on_enter(), igual que SceneManager.push en main.py

    assert scene._player is not None, "on_enter() did not spawn a player"
    assert scene._stage_data is not None, "on_enter() did not load stage data"

    # COMPENSACION SOLO-DE-CAPTURA 1 (interruptor global de CameraLock, ver
    # docstring del modulo): vacia la lista de CameraLock parseada sobre el
    # StageData ya cargado para que Camera.set_camera_locks() -- releida cada
    # frame desde StageScene.update() -- nunca vea una entrada con
    # lock_x/lock_y=True.
    n_locks = len(scene._stage_data.camera_locks)
    scene._stage_data.camera_locks = []
    print(f"[capture] cleared {n_locks} CameraLock(s) from stage_data for this capture session")

    boss = _find_boss(scene)
    # captura el spawn del boss ANTES de que corra cualquier update() (su IA lo
    # reubicaria en el frame 0 -- ver _pin_boss / COMPENSACION 3); aqui es
    # donde el TMX lo coloca y donde la captura de la arena deberia mostrarlo.
    boss_home = pygame.Vector2(boss.position) if boss is not None else None
    print(f"[capture] scene loaded. player spawn={tuple(scene._player.position)} "
          f"boss={'found' if boss else 'MISSING'}"
          f"{' spawn=' + str(tuple(boss_home)) if boss else ''}")

    player = scene._player
    feet_offset = player.rect.height  # la Y del TMX es la posicion de los pies; rect.y es la esquina superior izquierda (ver stage_loader.py)

    for name, world_x, feet_y in CAPTURES:
        player.position = pygame.Vector2(world_x, feet_y - feet_offset)
        player.velocity = pygame.Vector2(0.0, 0.0)
        player.rect.x = int(player.position.x)
        player.rect.y = int(player.position.y)

        for _ in range(SETTLE_FRAMES):
            _step(app, scene, boss, boss_home)

        out_path = OUT_DIR / f"ingame_{name}.png"
        pygame.image.save(app.internal_surface, str(out_path))

        boss = _find_boss(scene)  # volver a obtenerlo por si la identidad de entity_list cambio
        boss_info = "N/A"
        if boss is not None:
            boss_info = (
                f"state={boss.state.name} phase={boss.current_phase} "
                f"hp={boss.current_health}/{boss.phase_max_health} "
                f"pos={tuple(boss.position)}"
            )
        camera_locked = (scene._camera._is_locked_x, scene._camera._is_locked_y)
        print(
            f"[capture] {name} saved -> {out_path} size={app.internal_surface.get_size()} "
            f"player_pos={tuple(player.position)} player_feet_y={player.position.y + feet_offset} "
            f"camera_offset={tuple(scene._camera.offset)} camera_locked={camera_locked} "
            f"boss=[{boss_info}]"
        )


if __name__ == "__main__":
    main()
