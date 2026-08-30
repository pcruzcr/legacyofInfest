"""Fase RED — campaña de fairness (Cambio 3): telegraphs y anuncio del
enjambre dibujados POR ENCIMA de la capa de iluminación.

Hoy (dictamen doc-guardian AMARILLO vigente, token registrado)
``BossVenado.draw()`` pinta ``_draw_telegraphs``/``_draw_anuncio_del_enjambre``
dentro del pase de entidades de ``dibujar_mundo`` (ver
``src/framework/scenes/stage_parts/dibujo.py``) -- ANTES de que
``LightSystem.render()`` multiplique TODA la superficie por el mapa de luz
(``pygame.BLEND_RGB_MULT``). De noche (``boss_venado.tmx`` declara
``start_hour=night``, hora 22 -> ``factor_ambiente=0.55``, ver
``src/framework/stage/day_night.py`` PARADAS) eso deja el piso ambiente en
torno a 0.55 por canal: el tinte de aviso ``_TELEGRAPH_WARN_COLOR=(230, 90,
60)`` llega al jugador atenuado a ~40 % de su brillo. Doc 86 §2.4 regla 5
exige que "se vea disparar" -- un aviso que se ve como un tercio de su color
real no cumple esa regla igual de bien que uno pintado a pantalla completa.

Este módulo describe el comportamiento DESEADO (fase GREEN todavía sin
implementar): ``BossVenado.draw()`` deja de pintar esos dos métodos en el
pase de entidades, y ``BossVenadoScene.draw()`` los pinta DESPUÉS de
``super().draw(surface)`` (que ya compone mundo+luz+post+UI), con el mismo
mecanismo que ya usa para el halo de luna del jugador (ver el docstring de
``boss_venado_scene.py``, sección "Halo del jugador"). Los métodos de
dibujo en sí (``_draw_telegraphs``/``_draw_anuncio_del_enjambre``) NO
cambian por dentro -- sólo se retiran sus DOS llamadas del pase de
entidades -- así que las pruebas ya existentes que los invocan de forma
DIRECTA (``test_avisos_de_ataque.py``, ``test_anuncio_del_enjambre.py``)
deben seguir en verde, y la prueba 4 de este archivo es justo el candado que
lo garantiza.

Todos los asserts de las pruebas 1-3 están escritos para fallar limpio
(AssertionError) contra el código de HOY. La prueba 4 es la única que YA
PASA hoy -- es un candado anti-regresión para la fase GREEN, no una
afirmación sobre el bug; su propio docstring lo repite para que no se cuente
como "verde inesperado" al medir el rojo de esta fase.
"""
import numpy as np
import pygame
import pytest

from src.engine.core import settings
from src.engine.core.app import App
from src.stages.boss_venado import boss_venado as bv
from src.stages.boss_venado.boss_venado import BossVenado
from src.stages.boss_venado.boss_venado_scene import ARENA_X0, BossVenadoScene


def make_boss(with_bus: bool = False):
    """Mismo constructor que el resto de la suite: spawn dentro de la arena."""
    boss = BossVenado(pygame.Vector2(3168, 240))
    bus = None
    if with_bus:
        from src.engine.core.event_bus import EventBus
        bus = EventBus()
        boss.set_event_bus(bus)
    return boss, bus


def _superficie_de_prueba() -> pygame.Surface:
    surface = pygame.Surface((200, 200))
    surface.fill((10, 10, 10))
    return surface


def _offset_centrado(boss) -> pygame.Vector2:
    return pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100)


def _contiene_color_exacto(surface: pygame.Surface, color: tuple[int, int, int]) -> bool:
    """Busca un píxel con el color EXACTO dado en TODA la superficie.

    Las pruebas 1/4 de este archivo reutilizan el barrido con
    ``surface.get_at()`` de ``test_anuncio_del_enjambre.py`` (superficies de
    sondeo de 200x200 = 40 000 píxeles, barato en Python puro). Las pruebas
    2/3 escanean el fotograma INTERNO real del motor (800x600 = 480 000
    píxeles, ver ``settings.INTERNAL_WIDTH/HEIGHT``) y ese mismo barrido en
    Python puro sí se nota -- de ahí numpy (ya usado en esta misma carpeta,
    ver ``test_art_lib.py``) en vez de repetir el bucle. ``array3d`` copia
    (no expone un buffer bloqueado que haya que soltar a mano) y vectoriza
    la comparación exacta canal a canal.
    """
    arr = pygame.surfarray.array3d(surface)
    objetivo = np.array(color, dtype=arr.dtype)
    return bool(np.all(arr == objetivo, axis=-1).any())


# ──────────────────────────────────────────────
# 1 — el pase de entidades (BossVenado.draw) ya NO debe pintar los avisos
# ──────────────────────────────────────────────

def test_el_pase_de_entidades_ya_no_pinta_los_avisos():
    """HOY ``BossVenado.draw()`` llama ``_draw_telegraphs`` y
    ``_draw_anuncio_del_enjambre`` sin blending -- ambos pintan
    ``_TELEGRAPH_WARN_COLOR``/``_COLOR_ANUNCIO_ENJAMBRE`` directo con
    ``pygame.draw.*``, así que un ``draw()`` completo sobre una superficie
    limpia SIEMPRE deja al menos un píxel en ese tono exacto -- este assert
    lo comprueba y HOY lo encuentra (falla).

    ``_COLOR_ANUNCIO_ENJAMBRE = _TELEGRAPH_WARN_COLOR`` en el código actual
    (mismo tuple, ver boss_venado.py) -- un solo valor de color cubriría los
    dos estados, pero se ejercitan por separado de todos modos porque cada
    uno pinta desde un método distinto (``_draw_telegraphs`` vs
    ``_draw_anuncio_del_enjambre``) dentro de dos ramas distintas de
    ``draw()``, y la fase GREEN debe retirar las DOS llamadas, no una."""
    # Estado A: telegraph de ataque armado (STOMP).
    boss_telegraph, _ = make_boss()
    boss_telegraph._telegraph = "STOMP"
    boss_telegraph._telegraph_timer = bv.STOMP_TELEGRAPH
    superficie_telegraph = _superficie_de_prueba()
    boss_telegraph.draw(superficie_telegraph, _offset_centrado(boss_telegraph))

    color = boss_telegraph._TELEGRAPH_WARN_COLOR
    assert not _contiene_color_exacto(superficie_telegraph, color), (
        f"draw() con telegraph=STOMP armado dejó un píxel {color!r} puro en "
        "el pase de entidades -- _draw_telegraphs ya no debe llamarse desde "
        "ahí (fase GREEN: la escena lo pinta después de la luz)")

    # Estado B: transición de fase activa (anuncio del enjambre, Cambio 2).
    boss_transicion, _ = make_boss()
    boss_transicion.apply_hit(6.5, (0, 0))          # 12 -> 5.5, cruza el umbral de fase 1 (6.0)
    assert boss_transicion.is_transitioning, (
        "el daño no arrancó la transición -- helper roto, no el jefe")
    superficie_transicion = _superficie_de_prueba()
    boss_transicion.draw(superficie_transicion, _offset_centrado(boss_transicion))

    color_anuncio = tuple(getattr(
        boss_transicion, "_COLOR_ANUNCIO_ENJAMBRE", boss_transicion._TELEGRAPH_WARN_COLOR))
    assert not _contiene_color_exacto(superficie_transicion, color_anuncio), (
        f"draw() en plena transición de fase dejó un píxel {color_anuncio!r} "
        "puro en el pase de entidades -- _draw_anuncio_del_enjambre ya no "
        "debe llamarse desde ahí (fase GREEN: la escena lo pinta después de "
        "la luz)")


# ──────────────────────────────────────────────
# 2-3 — la escena SÍ debe pintarlos, después de la luz nocturna
# ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def app_headless():
    """``App`` real bajo software forzado (``use_gl=False``).

    Ninguna prueba de este archivo necesita GL, y forzarlo evita depender de
    la caída silenciosa a software que ``App._init_pygame`` hace de todos
    modos bajo el driver dummy (moderngl no puede abrir un contexto real
    ahí) -- con eso explícito, ``dibujar_mundo`` (ver
    ``src/framework/scenes/stage_parts/dibujo.py``) toma SIEMPRE la rama
    ``self._lighting.render(surface, offset)``: la multiplicación de luz
    aplicada de una vez sobre la MISMA superficie que ``scene.draw(surface)``
    recibe, no la ruta de GPU (``render_map`` + una tarjeta que esta prueba
    nunca compone).

    Lección H-28/B-032 (posterior a este archivo, fix 2026-08-20): llamar
    ``scene.draw(surface)`` directo aquí prueba el MÉTODO, no el despacho
    real de ``App._draw()`` -- que, para cualquier escena que exponga
    ``dibujar_mundo``/``dibujar_ui`` (toda ``StageScene``, AUD-343, ver
    app.py 556-723), JAMÁS invoca ``escena.draw()``. Mientras
    ``BossVenadoScene`` sólo sobrescribía ``draw()`` (antes del fix de
    H-28), las pruebas de este archivo seguían en verde mientras el bloque
    de overlays era código MUERTO en el juego real -- un falso verde
    silencioso, la trampa exacta que da nombre a la lección. Tras la
    migración a un override de ``dibujar_ui()``, ``scene.draw(surface)``
    sigue siendo una llamada válida por herencia del mixin
    (``DibujoDeEscenario.draw`` = ``dibujar_mundo`` + ``dibujar_ui``,
    precedente H-27), así que estas pruebas no necesitaron reescribirse --
    pero el candado que sí vigila el despacho real vive aparte, en
    ``test_despacho_real_overlays.py`` (llama ``App._draw()``, nunca
    ``scene.draw()``).

    Receta de escena real -- ADVERTENCIA sobre la premisa: ``test_boss_
    scene.py`` NO construye una escena real en ningún punto (ver el
    docstring de su ``_bare_scene_with_boss``: "Construir la escena real
    requiere arrancar un GameContext/App (costoso...)" -- ese archivo evita
    a propósito lo que aquí SÍ hace falta, el pipeline completo mundo+luz+
    post+UI de ``StageScene.draw()``). Esta receta está adaptada en su
    lugar de ``tools/capture_map.py``/``tools/play_map.py`` (los dos
    visores de esta misma zona editable que ya prueban ``App()`` +
    ``BossVenadoScene(app.context)`` bajo drivers dummy).

    Alcance de módulo: una sola ``App`` (arranca pygame/plugins/registro de
    entidades/calentamiento JIT) para las dos pruebas de escena real de este
    archivo; cada una empuja su propia ``BossVenadoScene`` nueva vía
    ``scene_manager.replace()`` (ver ``_push_real_scene``) -- más barato que
    repetir el arranque completo de ``App`` por prueba, y ``replace()``
    (a diferencia de ``push()``) destruye la escena anterior en vez de
    apilarla, así que la 2ª prueba no hereda estado de la 1ª.

    Teardown: ``App()`` deja el modo de vídeo en la resolución interna real
    (800x600, ver ``settings.INTERNAL_WIDTH/HEIGHT``) -- se restaura
    explícitamente a ``(320, 224)`` (el modo que ``conftest.py`` deja listo
    para el resto de la suite) para que un archivo de pruebas hermano que
    corra DESPUÉS de éste en la misma sesión no herede un modo de vídeo
    distinto al de su propio arranque de sesión."""
    app = App(use_gl=False)
    try:
        yield app
    finally:
        pygame.display.set_mode((320, 224))


def _push_real_scene(app: App) -> BossVenadoScene:
    scene = BossVenadoScene(app.context)
    app.scene_manager.replace(scene)  # awake() -> start() -> on_enter(), igual que main.py
    assert scene._player is not None, "on_enter() no generó al jugador"
    assert scene._stage_data is not None, "on_enter() no cargó el stage"
    return scene


def _find_boss_en_escena(scene: BossVenadoScene) -> BossVenado:
    jefe = scene._get_boss()
    assert isinstance(jefe, BossVenado), (
        "BossVenado_01 no apareció en entity_list -- revisar boss_venado.tmx")
    return jefe


def _encuadrar_arena_sin_actualizar(scene: BossVenadoScene) -> None:
    """Encuadra la cámara sobre la arena entera SIN llamar a ``scene.update()``.

    Deliberado, no un atajo de conveniencia: ``update()`` dispararía
    ``_update_lighting`` (``actualizaciones.py``), que crea la luz dinámica
    del jugador y hace avanzar ``LightSystem.update(dt, ...) ->
    LightSource.update(dt)`` -- el reloj de parpadeo ``_elapsed`` de cada
    foco ``Light_*`` del TMX. Ninguna de las dos pruebas de este archivo
    necesita eso, y evitarlo deja la luz de la arena determinista para el
    cálculo de "el aviso queda lejos de cualquier foco" que documenta cada
    prueba (ver sus propios docstrings). Llega al mismo offset exacto que
    ``BossVenadoScene._arena_target_offset()`` asienta tras H-17, pero
    escribiéndolo directo en vez de correr el bucle de asentamiento (ese
    bucle ya tiene su propia suite de candados en ``test_boss_scene.py``;
    no hace falta repetirla aquí)."""
    map_h = scene._stage_data.map_pixel_size[1]
    target_y = max(0.0, float(map_h) - settings.INTERNAL_HEIGHT)
    scene._camera.offset.update(ARENA_X0, target_y)


def test_la_escena_pinta_los_avisos_tras_la_luz(app_headless):
    """Comportamiento DESEADO (fase GREEN todavía sin implementar): un
    telegraph de ataque armado debe sobrevivir a pantalla completa
    (``BossVenadoScene.draw`` ya compuso mundo+luz+post+UI vía
    ``super().draw(surface)``) DESPUÉS de la luz, no antes.

    El STOMP se arma en el spawn del boss (x=3168; y=192, porque la Y del
    TMX -- 240 -- es la de los PIES y ``__init__`` resta la altura del
    sprite, 48px), deliberadamente lejos de los 5 focos ``Light_*`` del TMX:
    todos viven a nivel de piso (y entre 496 y 528, radio máximo declarado
    140px), mientras que el boss flota a y~192-216 -- más de 280px por
    encima del alcance de cualquiera. Sin ``scene.update()`` de por medio
    (ver ``_encuadrar_arena_sin_actualizar``) el único multiplicador que
    toca esos píxeles es el piso ambiente nocturno (TMX ``ambient_light=1.0``
    x ``factor_ambiente`` de la hora "night"/22h = 0.55, ver
    ``src/framework/stage/day_night.py`` PARADAS -- nunca 1.0 exacto), así
    que HOY ningún píxel final puede sobrevivir en el tinte exacto de aviso:
    este assert busca justo ese superviviente y hoy no lo encuentra."""
    scene = _push_real_scene(app_headless)
    jefe = _find_boss_en_escena(scene)
    _encuadrar_arena_sin_actualizar(scene)

    jefe._telegraph = "STOMP"
    jefe._telegraph_timer = bv.STOMP_TELEGRAPH

    surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    scene.draw(surface)

    color = jefe._TELEGRAPH_WARN_COLOR
    assert _contiene_color_exacto(surface, color), (
        f"ningún píxel de la escena final es exactamente {color!r} -- el "
        "aviso de STOMP se pintó ANTES de la luz nocturna y llegó atenuado; "
        "la fase GREEN debe pintarlo DESPUÉS de super().draw() (ver el "
        "halo del jugador en boss_venado_scene.py como referencia del "
        "mismo mecanismo)")


DT = 1.0 / 60.0


def _fade_mas_materializacion() -> float:
    """Cuánto avanzar el reloj del jefe para dejar el teletransporte del
    Cambio 5 completamente resuelto -- el desvanecimiento (``FADE_
    TELETRANSPORTE``) Y el destello de materialización posterior
    (``MATERIALIZACION_TELETRANSPORTE``) YA consumidos -- antes de sondear
    el color. Mismo patrón ``getattr`` con reserva que el resto de la suite
    de esta campaña (ver ``test_teletransporte_ux.py``), aunque en esta
    fase GREEN las dos constantes ya existen en producción."""
    fade = getattr(bv, "FADE_TELETRANSPORTE", 0.55)
    flash = getattr(bv, "MATERIALIZACION_TELETRANSPORTE", 0.25)
    return float(fade) + float(flash)


def _avanzar_boss(jefe: BossVenado, segundos: float) -> None:
    """Avanza SÓLO al jefe (``jefe.update(DT)`` en bucle), nunca
    ``scene.update()`` -- mismo motivo que ``_encuadrar_arena_sin_actualizar``:
    no disparar ``_update_lighting`` y mantener la luz de la arena
    determinista, condición de la que depende el razonamiento de "sólo el
    piso ambiente toca estos píxeles" de todo este archivo."""
    for _ in range(int(segundos / DT)):
        jefe.update(DT)


def test_la_escena_pinta_el_anuncio_del_enjambre_tras_la_luz(app_headless):
    """Gemelo de la prueba anterior para la transición de fase real (Cambio
    2: ``_draw_anuncio_del_enjambre``, mismo ``_COLOR_ANUNCIO_ENJAMBRE ==
    _TELEGRAPH_WARN_COLOR`` -- ver boss_venado.py).

    Adaptación Cambio 5 de la campaña de fairness (dictamen doc-guardian
    AMARILLO, feedback UX del usuario 2026-08-18) -- POR QUÉ CAMBIÓ este
    test: la premisa original de este docstring ("no hace falta llamar a
    ``scene.update()``: ``_start_phase_transition`` ya teletransporta al
    jefe de forma síncrona dentro de ``apply_hit``") dejó de ser cierta. El
    Cambio 5 retrasa el salto real detrás de un desvanecimiento
    (``FADE_TELETRANSPORTE``, 0.55s) y le añade un destello de
    materialización posterior (``MATERIALIZACION_TELETRANSPORTE``, 0.25s) --
    ver ``boss_venado.py::_update_teletransporte``/``_draw_teletransporte``.
    Mientras tanto, ``_draw_anuncio_del_enjambre`` tiene ahora un gate propio
    (``if self._desvanecimiento_restante > 0: return``) que lo mantiene
    MUDO hasta que el salto real ocurre -- así que, sin avanzar el reloj,
    este test ya NO ejercita el método que dice probar.

    Peor todavía: el escaneo de fotograma COMPLETO original seguía
    devolviendo VERDE de todos modos, pero por la razón EQUIVOCADA (hallazgo
    reportado en el handoff de la fase GREEN del Cambio 5): el anillo/
    marcador de ``_draw_teletransporte`` -- que la escena pinta post-luz en
    el MISMO bloque, ver ``BossVenadoScene.draw()`` -- comparte exactamente
    ``_TELEGRAPH_WARN_COLOR`` con el anuncio del enjambre, y se pinta desde
    el primer fotograma de la ventana (justo cuando ``_draw_anuncio_del_
    enjambre`` todavía calla). Un escaneo global no puede distinguir "el
    anuncio se pintó" de "otro método comparte su tinte en otro punto de la
    pantalla" -- coincidencia de color, no evidencia del método bajo prueba.

    Arreglo, con las dos técnicas que sugiere el handoff:
    (a) se avanza el jefe (NUNCA la escena, ver ``_avanzar_boss``) más allá
    de ``FADE_TELETRANSPORTE + MATERIALIZACION_TELETRANSPORTE`` para que el
    salto real YA ocurriera y ``_draw_teletransporte`` quede totalmente
    inerte (sus dos relojes en 0) -- sólo entonces ``_draw_anuncio_del_
    enjambre`` es la única fuente posible de ese tinte en pantalla; y
    (b) el sondeo se acota, además, a una ventana local de 100x100 centrada
    en la posición FINAL del jefe en pantalla (donde vive el anuncio,
    ``self.rect.center`` ya saltado) en vez de la superficie de 800x600
    completa -- mismo patrón de ``test_teletransporte_ux.py``. Con (a) ya
    basta para eliminar la coincidencia, pero (b) deja el test blindado
    aunque algún método futuro vuelva a compartir tinte en otra parte de la
    pantalla.

    El resto de la premisa física NO cambió: el salto real sigue yendo al
    centro de la arena en X (``ARENA_CX = (2480 + 3264) / 2 = 2872``)
    conservando la Y del spawn (~216, la mitad superior del sprite -- el
    jefe "flota, no se planta"), más de 280px por encima de los 5 focos del
    TMX (todos a nivel de piso, entre 496 y 528) -- el mismo razonamiento de
    "sólo el piso ambiente puede tocar estos píxeles" de la prueba anterior
    sigue aplicando sin cambios, incluida la advertencia de la trampa física
    del overlap entre ``Light_ArenaLampWest_01``/``Light_ArenaLampEast_01``
    (x=2816/x=2944, radio 100): sigue sin aplicar porque la Y se queda
    arriba, el override nunca la toca."""
    scene = _push_real_scene(app_headless)
    jefe = _find_boss_en_escena(scene)
    _encuadrar_arena_sin_actualizar(scene)

    jefe.apply_hit(6.5, (0, 0))
    assert jefe.is_transitioning, (
        "el daño no arrancó la transición -- helper roto, no la escena")

    _avanzar_boss(jefe, _fade_mas_materializacion() + 0.05)   # (a) salto real + destello ya resueltos
    assert jefe.is_transitioning, "el avance no debe cerrar la ventana por sí solo"

    centro_final_mundo = pygame.Vector2(jefe.rect.center)     # posición YA saltada

    surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    scene.draw(surface)

    offset = scene._camera.offset
    lado = 100
    centro_pantalla = (int(centro_final_mundo.x - offset.x), int(centro_final_mundo.y - offset.y))
    ventana_rect = pygame.Rect(centro_pantalla[0] - lado // 2, centro_pantalla[1] - lado // 2,
                               lado, lado).clip(surface.get_rect())
    ventana = surface.subsurface(ventana_rect)                # (b) sondeo acotado a la posición final

    color = tuple(getattr(jefe, "_COLOR_ANUNCIO_ENJAMBRE", jefe._TELEGRAPH_WARN_COLOR))
    assert _contiene_color_exacto(ventana, color), (
        f"ningún píxel cerca de la posición FINAL del jefe es exactamente "
        f"{color!r} tras componer mundo+luz+post+UI -- el anuncio del "
        "enjambre se pintó ANTES de la luz nocturna y llegó atenuado (o no "
        "se pintó en absoluto); la fase GREEN debe pintarlo DESPUÉS de "
        "super().draw()")


# ──────────────────────────────────────────────
# 4 — candado anti-sobre-borrado: los métodos de dibujo directo siguen vivos
# ──────────────────────────────────────────────

def test_los_metodos_de_dibujo_directo_siguen_vivos():
    """Candado para la fase GREEN futura de este Cambio 3:
    ``_draw_telegraphs``/``_draw_anuncio_del_enjambre`` en sí NO cambian --
    sólo se retiran sus DOS llamadas del pase de entidades de
    ``BossVenado.draw()`` (ver el docstring del módulo). Si esa fase
    borrara los métodos enteros en vez de sólo sus dos líneas de llamada,
    este candado debe notarlo -- y las pruebas existentes que los invocan
    directo (``test_avisos_de_ataque.py``, ``test_anuncio_del_enjambre.py``)
    dejarían de poder ejercitarlos en absoluto.

    NOTA para quien cuente rojos/verdes de esta fase RED: esta prueba YA
    PASA hoy contra el código actual -- no es una afirmación sobre el bug de
    este Cambio 3, es la guardia que la fase GREEN no debe romper al mover
    las dos llamadas fuera de ``draw()``.

    Usa MUSHROOM_SPORE y no STOMP -- corrección tras la primera corrida real
    de esta suite (el candado SÍ se armó con STOMP en el primer intento y
    salió rojo por error de geometría, no por el bug de este Cambio 3): la
    rama STOMP de ``_draw_telegraphs`` (boss_venado.py ~L1240-1242) ancla su
    marca al SUELO en coordenadas de MUNDO (``FLOOR_Y - 6``, y≈554-558),
    totalmente independiente de ``self.rect`` -- el boss flota en su spawn a
    ``rect.centery≈216``, así que con ``_offset_centrado(boss)`` (ventana
    centrada en el CUERPO del boss) la marca de STOMP cae ~140px por debajo
    del borde inferior de la superficie de sondeo de 200x200 y nunca se
    pinta: ambas superficies quedaban bit a bit idénticas y el candado
    fallaba por una trampa de geometría, no porque ``_draw_telegraphs``
    estuviera roto. MUSHROOM_SPORE (boss_venado.py ~L1254-1262) ancla sus
    tres marcas a ``self.rect.top``/``self.rect.centerx`` -- siempre a
    ~28px del centro del boss -- así que cualquier ventana centrada en
    ``rect.center`` la contiene por construcción; es la misma geometría que
    ya prueba en verde ``test_avisos_de_ataque.py`` (Cambio 1)."""
    boss, _ = make_boss()
    boss._telegraph = "MUSHROOM_SPORE"
    boss._telegraph_timer = bv.SPORE_TELEGRAPH
    offset = _offset_centrado(boss)
    base = _superficie_de_prueba()
    con_telegraph = base.copy()

    boss._draw_telegraphs(con_telegraph, offset)

    assert pygame.image.tobytes(con_telegraph, "RGB") != pygame.image.tobytes(base, "RGB"), (
        "_draw_telegraphs (llamado DIRECTO, no vía draw()) dejó de pintar -- "
        "la fase GREEN debe mover sus DOS llamadas fuera del pase de "
        "entidades, no borrar los métodos")
