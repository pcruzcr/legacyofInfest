"""
Modulo: play_map
Sistema: stages.boss_venado.tools
Descripcion: visor JUGABLE (ventana real, input real) dentro del motor para
el mapa de la arena del boss "Residencias al Crepusculo" -- la contraparte
jugable por humanos de ``capture_map.py`` en este mismo directorio. Donde
``capture_map.py`` arranca la App real de forma headless y teletransporta al
jugador a posiciones x fijas para las capturas, esta herramienta arranca el
MISMO pipeline real de App/escena pero abre una ventana de SO real, corre un
loop de juego REAL a 60 FPS (ritmo en tiempo real con ``DeltaClock``/
``pygame.time.Clock``, no dt avanzado manualmente), y deja que el usuario
camine por el mapa con los propios controles del motor (flechas/A-D para
moverse, SPACE/UP/W para saltar -- DEFAULT_KEY_BINDINGS de
``src/engine/input/action_map.py``, sin modificar). El movimiento/fisica/
colision son manejados enteramente por la ruta de codigo real que usa
main.py (``InputManager.pump`` -> ``EventBus.dispatch`` ->
``SceneManager.update`` -> ``StageScene.update`` -> ``Player.update(dt,
collision_rects, input_manager)``) -- esta herramienta nunca lee ni escribe
la position/velocity del jugador directamente; ver ``_frame`` abajo.

PREVIEW DE FASE 2 -- esta herramienta arrastra exactamente las mismas dos
compensaciones por frame, solo-de-herramienta-de-captura, que
``capture_map.py`` documenta en detalle (leer el docstring de ese modulo
para la justificacion tecnica completa, enlaces a
``reports\\map_residencias\\CAMERALOCK.md`` y ``reports\\FINDINGS.md`` H-10,
y la aprobacion del arquitecto). Resumen, reproducido aqui porque un humano
frente al teclado necesita AMBAS para realmente verse moverse por la arena
en lugar de una vista congelada/desactualizada:

  COMPENSACION DE PREVIEW A -- interruptor global de CameraLock: el
  CameraLock_01 del TMX (ver ``ArenaZone_01``/``CameraLock_01`` en x=1600 en
  boss_venado.tmx) congela AMBOS ejes de la camara para TODO el stage desde
  el frame 0 (``Camera.set_camera_locks()`` no condiciona al rect del lock,
  un bug de motor conocido). Compensacion: vaciar
  ``scene._stage_data.camera_locks`` justo despues de que la escena se
  empuja, una vez, al arrancar.

  COMPENSACION DE PREVIEW B -- H-10: ``StageScene`` nunca llama a la
  ``BufferedRenderer.center()`` real de pyscroll, asi que el arte de FONDO de
  tiles queda pegado para siempre a la esquina de spawn mientras las
  entidades (dibujadas por separado) se mueven correctamente con
  ``camera.offset``. Compensacion: cada frame, entre
  ``scene_manager.update()`` (offset de camara definitivo para el frame) y
  ``app._draw()`` (pyscroll blitea a partir de el), llamar a la
  ``stage.map_layer.center((camera.offset.x + W/2, camera.offset.y + H/2))``
  real. NOTA (2026-08-26): ``BossVenadoScene`` (boss_venado_scene.py, la
  escena completa, no la ``StageScene`` base de arriba) tuvo su propia
  version de esta compensacion en ``update()`` desde el rewrite de fase 2
  hasta esa fecha, retirada por redundante -- ``App._draw()`` SI recorre
  ``dibujar_mundo()`` (AUD-039, ver docstring de modulo de
  ``boss_venado_scene.py``, seccion H-10) y centra el mismo fondo por su
  cuenta ANTES de dibujarlo. Esta copia de aqui (COMPENSACION B) sigue sin
  tocarse -- no forma parte de ese retiro, que fue solo de la escena --
  pero por la misma razon podria ser igual de redundante; no se verifico
  para este visor, queda como hallazgo abierto.

  COMPENSACION DE PREVIEW C -- bug de clamp de arena de la IA del boss
  (COMPENSACION 3 de capture_map): la IA de movimiento original del
  ``BossVenado`` del profesor usa una constante de arena a escala 320
  (``ARENA_W = 320``) contra coordenadas de MUNDO, asi que en su
  primerisimo ``update()`` se lanza a si mismo desde su spawn del TMX (ver
  ``BossVenado_01`` en boss_venado.tmx) hacia world x~44, fuera de la
  arena. Fuera del alcance de un visor de MAPA (registrado en
  FINDINGS.md). Esta herramienta captura la posicion de spawn real del
  boss (``boss.position``) justo despues de que la escena carga -- ANTES de
  que cualquier ``update()`` tenga oportunidad de moverlo -- y re-fija al
  boss a ESA captura cada frame, mismo patron que ``_pin_boss``/
  ``boss_home`` de capture_map.py, para que siga visible dondequiera que el
  TMX lo coloque (antes esto era una coordenada (2000, 240) hardcodeada y
  desactualizada, incorrecta desde que la ampliacion de la ronda-11/
  ronda-12 del mapa movio el spawn real -- ver FINDINGS).

Ninguna de estas tres toca src/engine, src/framework, ni el TMX -- las tres
mutan objetos de runtime ya construidos (StageData, PyscrollGroup, la
entidad del boss) desde afuera, a traves de su API/campos publicos
existentes, exactamente como hace capture_map.py. Se documentan como
"preview de fase 2" porque la correccion real (hacer que Camera/StageScene/
la IA del boss sean correctos) esta fuera del alcance de una herramienta de
visualizacion de mapa y pertenece a trabajo posterior de IA del boss/puente
del motor.

VENTANA REAL, NO DUMMY: a diferencia de capture_map.py, esta herramienta
quiere una ventana de SO real, asi que fuerza SDL_VIDEODRIVER a "windows"
-- NO ``setdefault`` -- pero SOLO cuando se lanza como el propio script
(``if __name__ == "__main__"``). Esto importa porque ``tests/conftest.py``
fija a fuego ``os.environ["SDL_VIDEODRIVER"] = "dummy"`` para toda la
sesion de pytest, y las variables de entorno de PowerShell persisten entre
comandos tecleados en la MISMA sesion de shell (a diferencia de un entorno
de subproceso fresco) -- asi que un shell que corrio pytest recientemente
podria si no filtrar silenciosamente "dummy" a esta herramienta y producir
una ejecucion sin ventana aunque se pidiera una ventana real. Proteger el
forzado detras de ``__name__ == "__main__"`` significa: ejecutar
directamente -> siempre se obtiene una ventana real sin importar que se
haya filtrado; importado como modulo (el propio smoke test de este
proyecto hace exactamente eso, fijando el mismo SDL_VIDEODRIVER=dummy ANTES
de importar este modulo) -> la importacion no tiene efecto sobre la
variable de entorno, asi que el smoke test se mantiene headless.
SDL_AUDIODRIVER se deja intacto en cualquier caso -- una sesion de juego
real deberia tener audio real como lo tiene main.py; el smoke test no
llama a App() el tiempo suficiente como para tocar nada mas que
pygame.mixer.init() (inofensivo bajo cualquier driver que ya este activo
en ese proceso).

Uso (desde el directorio ``game`` del LAB, ventana/audio real):

    path\\to\\python.exe src\\stages\\boss_venado\\tools\\play_map.py

Controles: flechas o A/D para moverse, SPACE/UP/W para saltar (valores por
defecto del motor, ver ``src/engine/input/action_map.py``). ESC o cerrar la
ventana sale de forma limpia. (Nota: ESC TAMBIEN esta ligado a
Action.PAUSE/CANCEL, que StageScene.update() usa para abrir su propio menu
de pausa dentro del juego -- eso sigue pasando, en paralelo, ya que los
mismos eventos reales se alimentan a InputManager; esta herramienta
adicionalmente observa el keydown crudo de ESC por si misma,
independientemente de la escena, para garantizar que la ventana del visor
siempre se cierre con ESC segun la propia especificacion de esta
herramienta, en lugar de solo mostrar un menu de pausa del cual el tester
tendria que salir despues.)

VERIFICACION: como esta herramienta quiere una ventana real, no puede
ejercitarse de punta a punta con un smoke test automatizado sin una. Lo que
SI puede, y esta cubierto por el propio chequeo headless de smoke de este
proyecto (SDL dummy, corrido desde el LAB, no commiteado -- ver
``reports\\FINDINGS.md`` / notas de sesion para el comando exacto), es que
la funcion de avance de frame de abajo (``_frame``), que es lo unico que
corre cada frame y es exclusivo de esta herramienta (todo lo demas es
identico a capture_map.py o es el cableado estandar del loop real de
App/SceneManager), deja correctamente que el input KEYDOWN sintetico
alcance al Player real a traves del pipeline real de InputManager/EventBus/
SceneManager y que las dos compensaciones de camara mantengan a
``camera.offset`` siguiendo al jugador -- es decir, que la logica propia de
este archivo, no el sistema de ventana/eventos de pygame, sea correcta.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Fuerza un driver de video SDL REAL, pero solo cuando este archivo se
# ejecuta como el propio script -- ver "VENTANA REAL, NO DUMMY" en el
# docstring del modulo para saber por que esto NO debe ser un ajuste global
# a nivel de proceso y NO debe ser `setdefault`.
if __name__ == "__main__":
    os.environ["SDL_VIDEODRIVER"] = "windows"

# tools/ -> boss_venado/ -> stages/ -> src/ -> game/ (raiz del juego del LAB,
# el equivalente de legacyofInfest/ en el proyecto real). Misma constante de
# layout que capture_map.py.
_GAME_ROOT = Path(__file__).resolve().parents[4]
os.chdir(_GAME_ROOT)  # StageLoader.load() resuelve la ruta del TMX relativa al cwd.
sys.path.insert(0, str(_GAME_ROOT))

import pygame  # noqa: E402

from src.engine.core import settings  # noqa: E402
from src.engine.core.app import App  # noqa: E402
from src.framework.entities.boss_base import BossBase  # noqa: E402
from src.stages.boss_venado.boss_venado_scene import BossVenadoScene  # noqa: E402


def _sync_map_render(scene: BossVenadoScene) -> None:
    """COMPENSACION DE PREVIEW B (H-10, ver docstring del modulo): llama a la
    API real ``center()`` de pyscroll para que el fondo de tiles realmente
    siga a ``camera.offset`` en lugar de quedar pegado a la ventana de
    buffer inicial. Logica identica, literal, al ``_sync_map_render`` de
    capture_map.py."""
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
    """COMPENSACION DE PREVIEW C (bug de clamp de arena de la IA del boss,
    ver docstring del modulo): mantiene al boss fijo en su spawn del TMX
    cada frame, despues de que el propio update() de la escena lo (mal)movio
    y antes de draw(). Logica identica, literal, al ``_pin_boss`` de
    capture_map.py -- ``home`` es una captura de la posicion de spawn REAL
    del boss tomada dinamicamente en ``setup()``, no una coordenada
    hardcodeada, asi que siempre coincide con donde sea que el TMX actual
    lo coloque."""
    if boss is None or home is None:
        return
    boss.position.update(home)
    boss.rect.x = int(home.x)
    boss.rect.y = int(home.y)
    if hasattr(boss, "velocity"):
        boss.velocity.update(0.0, 0.0)


def _find_boss(scene: BossVenadoScene) -> BossBase | None:
    stage = scene._stage_data
    if stage is None:
        return None
    for entity in stage.entity_list:
        if isinstance(entity, BossBase):
            return entity
    return None


def _poll_events() -> tuple[list[pygame.event.Event], bool]:
    """Sondea la cola de eventos real para este frame. Retorna (events,
    quit_requested); quit_requested es True al cerrar la ventana (QUIT) o
    con un keydown crudo de ESC -- la propia tecla de salida limpia de esta
    herramienta (ver docstring del modulo sobre que ESC tambien es
    Action.PAUSE/CANCEL, manejado por separado/normalmente por la escena
    una vez que estos eventos se alimentan a InputManager en ``_frame``)."""
    events = pygame.event.get()
    quit_requested = any(
        e.type == pygame.QUIT
        or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE)
        for e in events
    )
    return events, quit_requested


def _frame(
    app: App,
    scene: BossVenadoScene,
    boss: BossBase | None,
    boss_home: pygame.Vector2 | None,
    events: list[pygame.event.Event],
    dt: float,
) -> None:
    """Una iteracion del cuerpo real del loop de juego -- el mismo pipeline
    que conduce App.run() (input -> dispatch -> update -> draw), reproducido
    aqui (en lugar de llamar a app.run() directamente) solo porque las dos
    compensaciones por frame deben correr ENTRE scene_manager.update()
    [offset de camara definitivo para el frame] y app._draw() [pyscroll
    blitea a partir de el], un punto para el que app.run() no tiene ningun
    hook. El movimiento/fisica/colision son enteramente del propio motor:
    esta funcion alimenta eventos reales a traves de InputManager igual que
    App._process_events(), y luego deja que SceneManager/StageScene/Player
    hagan todo lo que normalmente hacen -- no lee ni escribe el estado del
    jugador."""
    app.input_manager.pump(events)
    app.event_bus.dispatch()
    app.scene_manager.update(dt)
    _pin_boss(boss, boss_home)
    app.scene_manager.transition.update(dt)
    _sync_map_render(scene)
    app._draw()


def setup() -> tuple[App, BossVenadoScene, BossBase | None, pygame.Vector2 | None]:
    """Arranca la App real, empuja BossVenadoScene (identico a la secuencia
    de arranque de capture_map.py), aplica la COMPENSACION DE PREVIEW A una
    vez, localiza al boss y captura su spawn. Separado de main() para que un
    smoke test headless pueda conducir frames directamente sin abrir una
    ventana real."""
    app = App()
    scene = BossVenadoScene(app.context)
    app.scene_manager.push(scene)  # awake() -> start() -> on_enter(), igual que main.py

    assert scene._player is not None, "on_enter() did not spawn a player"
    assert scene._stage_data is not None, "on_enter() did not load stage data"

    # COMPENSACION DE PREVIEW A (interruptor global de CameraLock, ver
    # docstring del modulo): vacia la lista de CameraLock parseada sobre el
    # StageData ya cargado para que Camera.set_camera_locks() -- releida
    # cada frame desde StageScene.update() -- nunca vea una entrada con
    # lock_x/lock_y=True.
    n_locks = len(scene._stage_data.camera_locks)
    scene._stage_data.camera_locks = []
    print(f"[play_map] cleared {n_locks} CameraLock(s) from stage_data for this session")

    boss = _find_boss(scene)
    # Captura el spawn del boss ANTES de que corra cualquier update() (su IA
    # lo reubicaria en el frame 0 -- ver COMPENSACION DE PREVIEW C /
    # _pin_boss): aqui es donde el TMX ACTUAL lo coloca, leido dinamicamente
    # en lugar de una coordenada hardcodeada que quedaria desactualizada la
    # proxima vez que se edite el mapa.
    boss_home = pygame.Vector2(boss.position) if boss is not None else None
    print(
        f"[play_map] player spawn={tuple(scene._player.position)} "
        f"boss={'found' if boss else 'MISSING'}"
        f"{' spawn=' + str(tuple(boss_home)) if boss is not None else ''}"
    )
    return app, scene, boss, boss_home


def main() -> None:
    app, scene, boss, boss_home = setup()
    print("[play_map] window open -- move: arrows/A-D, jump: SPACE/UP/W, exit: ESC or close window")

    running = True
    while running and app.context.running:
        dt = app.clock.tick()  # ritmo en tiempo real a settings.TARGET_FPS (60)
        events, quit_requested = _poll_events()
        if quit_requested:
            running = False
            break
        _frame(app, scene, boss, boss_home, events, dt)
        pygame.display.flip()

    app._shutdown()
    print("[play_map] closed.")


if __name__ == "__main__":
    main()
