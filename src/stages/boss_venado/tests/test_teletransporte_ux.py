"""Fase RED — campaña de fairness (Cambio 5): UX del teletransporte de fase.

Dictamen doc-guardian AMARILLO vigente (token registrado), orden del usuario
2026-08-18. Hoy (Cambios 1-4 ya en producción) ``_start_phase_transition``
(boss_venado.py ~L994-1024) teletransporta al venado al centro de la arena
en el MISMO instante en que se abre la ventana de quietud de 2.5s -- un
salto instantáneo, sin ningún efecto de transición. Este módulo describe el
comportamiento DESEADO (fase GREEN todavía sin implementar):

* El salto deja de ser instantáneo. Al abrir la ventana, el venado se queda
  ``FADE_TELETRANSPORTE`` (constante nueva, módulo o clase, valor de diseño
  0.55s -- >= 0.3s exigido aquí como candado de "duración perceptible")
  "desvaneciéndose" en su posición VIEJA, con un temporizador propio nuevo
  (``self._desvanecimiento_restante``) conducido desde NUESTRO ``update()``
  (boss_venado.py ~L1156-1190), que corre ENTERO antes de delegar en
  ``super().update()`` -- confirmado leyendo ``EnemyBase.update``
  (enemy_base.py ~L207-230): mientras ``is_transitioning`` es True,
  ``_pre_update`` (boss_base.py ~L430-436) hace que ``EnemyBase.update()``
  retorne SIN tocar ``position``/``rect`` en absoluto, así que el único
  código que puede mover al jefe durante la ventana es el nuestro, ANTES de
  esa llamada a ``super()``.
* Al expirar el desvanecimiento se llama ``teletransportar(
  self._destino_de_teletransporte(), self.position.y)`` -- la subcadena
  literal ``teletransportar(`` se conserva (contrato AUD-257, candado
  ``test_el_fuente_llama_a_teletransportar`` en ``test_adopcion_v3.py``) --
  más un destello breve de materialización (``_draw_teletransporte``, más
  abajo).
* Garantía ANTI-TIRÓN de H-18/D6, preservada sin cambios: el salto completo
  (desvanecimiento + reaparición) cabe dentro del primer tramo de la
  ventana (<=1.0s de los 2.5s totales), nunca al cerrarla -- ver
  ``test_adopcion_v3.py::test_el_salto_ocurre_tras_el_desvanecimiento_dentro_del_primer_tramo``.
* Dibujo nuevo: ``_draw_teletransporte(surface, offset)``. Durante el
  desvanecimiento pinta un anillo IMPLOSIVO en la posición VIEJA + un
  MARCADOR creciente en el DESTINO (color de aviso exacto, formas planas
  sin antialias), y nada fuera de esa ventana. Mismo patrón de capas que el
  Cambio 3 (``test_telegraphs_sobre_la_luz.py``): el pase de entidades
  (``BossVenado.draw()``) NO lo pinta -- la ESCENA lo pinta post-luz, junto
  a ``_draw_telegraphs``/``_draw_anuncio_del_enjambre``.
* Orden de temporizadores (riesgo 6 del dictamen): el salto debe ocurrir
  ANTES que ``_finish_phase_transition`` aunque los dos relojes venzan en
  el MISMO fotograma (posible con un ``update(dt)`` de dt grande) -- porque
  nuestro ``update()`` corre completo antes de que ``super().update()``
  llegue a decrementar ``transition_timer``.

Todos los asserts están escritos para fallar limpio (AssertionError) contra
el código de HOY, nunca por AttributeError: ``FADE_TELETRANSPORTE`` y
``_draw_teletransporte``/``_desvanecimiento_restante`` se leen con
``getattr`` y valores de reserva, porque el Cambio 5 todavía no decidió si
serán constantes de módulo o atributos de clase/instancia. El color de
aviso se resuelve con el mismo patrón que ``_COLOR_ANUNCIO_ENJAMBRE`` en
``test_anuncio_del_enjambre.py``: se acepta una constante propia nueva o la
reutilización directa de ``_TELEGRAPH_WARN_COLOR``.
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


def _offset_centrado_en(punto: tuple[float, float]) -> pygame.Vector2:
    return pygame.Vector2(int(punto[0]) - 100, int(punto[1]) - 100)


def _offset_centrado(boss) -> pygame.Vector2:
    return _offset_centrado_en(boss.rect.center)


def _contiene_color_exacto(surface: pygame.Surface, color: tuple[int, int, int]) -> bool:
    """Mismo helper (y misma razón de usar numpy) que
    ``test_telegraphs_sobre_la_luz.py::_contiene_color_exacto``: barato para
    las superficies de sondeo de 200x200 de este archivo, y necesario para
    el fotograma interno real de 800x600 de la prueba de escena."""
    arr = pygame.surfarray.array3d(surface)
    objetivo = np.array(color, dtype=arr.dtype)
    return bool(np.all(arr == objetivo, axis=-1).any())


def _color_de_aviso(boss) -> tuple[int, int, int]:
    """Igual patrón de ``getattr`` que ``_COLOR_ANUNCIO_ENJAMBRE`` en
    ``test_anuncio_del_enjambre.py`` -- no se ata a un nombre de constante
    que el Cambio 5 todavía no decidió (podría ser ``_COLOR_TELETRANSPORTE``
    propio o reutilizar directamente ``_TELEGRAPH_WARN_COLOR``)."""
    return tuple(getattr(boss, "_COLOR_TELETRANSPORTE", boss._TELEGRAPH_WARN_COLOR))


# ──────────────────────────────────────────────
# (a) el desvanecimiento arranca en la posición VIEJA
# ──────────────────────────────────────────────

def test_arranca_el_desvanecimiento_en_la_posicion_vieja():
    """HOY ``_start_phase_transition`` llama ``teletransportar()`` en el
    mismo ``apply_hit`` sincrónico -- no existe ningún temporizador de
    desvanecimiento y la posición cambia de inmediato. Este test falla en
    rojo limpio contra el código actual en las dos aserciones."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_X1 - 80.0        # acorralado contra la pared derecha
    boss.rect.x = int(boss.position.x)
    x_vieja = boss.position.x

    boss.apply_hit(6.5, (0, 0))                 # dispara _start_phase_transition
    assert boss.is_transitioning

    assert getattr(boss, "_desvanecimiento_restante", 0.0) > 0.0, (
        "falta self._desvanecimiento_restante (o no arrancó > 0) al abrir "
        "la ventana de transición -- Cambio 5 exige un temporizador propio "
        "que conduzca el desvanecimiento antes del salto")
    assert boss.position.x == x_vieja, (
        "el venado saltó de inmediato al abrir la ventana -- debía quedarse "
        "en su posición vieja durante el desvanecimiento")


# ──────────────────────────────────────────────
# (b) la duración del desvanecimiento es perceptible
# ──────────────────────────────────────────────

def test_el_desvanecimiento_dura_al_menos_0_3_segundos():
    """``FADE_TELETRANSPORTE`` debe ser lo bastante largo para leerse como un
    efecto, no un parpadeo de un fotograma -- 0.3s es el piso de diseño del
    dictamen; el valor real esperado es 0.55s (ver docstring del módulo).
    ``getattr`` con caída a 0.0 porque el Cambio 5 todavía no decidió si
    será una constante de módulo (``bv.FADE_TELETRANSPORTE``) o un atributo
    de clase (``BossVenado.FADE_TELETRANSPORTE``) -- se prueban las dos
    ubicaciones antes de caer al valor de reserva que garantiza el rojo de
    HOY."""
    valor = getattr(bv, "FADE_TELETRANSPORTE", None)
    if valor is None:
        valor = getattr(BossVenado, "FADE_TELETRANSPORTE", 0.0)
    assert valor >= 0.3, (
        f"FADE_TELETRANSPORTE={valor!r} -- debe ser >= 0.3s para leerse "
        "como un desvanecimiento real, no un parpadeo de un fotograma")


# ──────────────────────────────────────────────
# (c) _draw_teletransporte: anillo en la posición vieja + marcador en el destino
# ──────────────────────────────────────────────

def test_dibuja_anillo_en_la_posicion_vieja_y_marcador_en_el_destino():
    """Dos ventanas de sondeo independientes -- una centrada en la posición
    VIEJA (``boss.rect.center``, todavía sin mover porque el salto no ha
    ocurrido), otra centrada en el DESTINO calculado por
    ``_destino_de_teletransporte()`` -- porque un único sondeo sobre toda la
    superficie no distinguiría "sólo pinta el anillo" de "pinta las dos
    formas": el punto de esta prueba es que las DOS existen, en DOS lugares
    distintos."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_X1 - 80.0
    boss.rect.x = int(boss.position.x)
    boss.apply_hit(6.5, (0, 0))
    assert boss.is_transitioning

    metodo = getattr(boss, "_draw_teletransporte", None)
    assert callable(metodo), "falta el método _draw_teletransporte (Cambio 5)"

    color = _color_de_aviso(boss)
    centro_viejo = boss.rect.center                          # el cuerpo no se ha movido todavía
    centro_destino = (boss._destino_de_teletransporte() + boss.rect.width / 2.0,
                      boss.rect.centery)                      # Y preservada, el venado flota

    ventana_vieja = _superficie_de_prueba()
    metodo(ventana_vieja, _offset_centrado_en(centro_viejo))
    assert _contiene_color_exacto(ventana_vieja, color), (
        "_draw_teletransporte no pintó el anillo implosivo en la posición vieja")

    ventana_destino = _superficie_de_prueba()
    metodo(ventana_destino, _offset_centrado_en(centro_destino))
    assert _contiene_color_exacto(ventana_destino, color), (
        "_draw_teletransporte no pintó el marcador creciente en el destino")


def test_no_dibuja_nada_fuera_de_transicion():
    """Sin ninguna transición en curso no hay ningún salto que anunciar."""
    boss, _ = make_boss()
    assert not boss.is_transitioning

    metodo = getattr(boss, "_draw_teletransporte", None)
    assert callable(metodo), "falta el método _draw_teletransporte (Cambio 5)"

    base = _superficie_de_prueba()
    resultado = base.copy()
    metodo(resultado, _offset_centrado(boss))

    assert pygame.image.tobytes(resultado, "RGB") == pygame.image.tobytes(base, "RGB"), (
        "_draw_teletransporte pintó algo sin estar en transición de fase")


# ──────────────────────────────────────────────
# (d) el pase de entidades NO lo pinta (patrón del test 1 del Cambio 3)
# ──────────────────────────────────────────────

def test_el_pase_de_entidades_no_pinta_el_desvanecimiento():
    """Mismo patrón que
    ``test_telegraphs_sobre_la_luz.py::test_el_pase_de_entidades_ya_no_pinta_los_avisos``:
    ``BossVenado.draw()`` corre ANTES de la capa de luz de la escena, así
    que si ``_draw_teletransporte`` se llamara desde ahí el aviso llegaría
    atenuado de noche (~40% de su brillo real, factor ambiente nocturno
    0.55 del TMX). HOY este test YA PASA -- no es parte del rojo de esta
    fase (el método ni siquiera existe todavía, así que no hay nada que
    pintar desde ningún lado); es el candado que impide que la
    implementación futura repita el error que Cambio 1/2 tuvieron que
    corregir en Cambio 3: el pase de entidades jamás debe pintar el color
    de aviso puro durante el desvanecimiento del teletransporte."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_X1 - 80.0
    boss.rect.x = int(boss.position.x)
    boss.apply_hit(6.5, (0, 0))
    assert boss.is_transitioning

    superficie = _superficie_de_prueba()
    boss.draw(superficie, _offset_centrado(boss))

    color = _color_de_aviso(boss)
    assert not _contiene_color_exacto(superficie, color), (
        f"boss.draw() (pase de entidades) dejó un píxel {color!r} puro "
        "durante el desvanecimiento del teletransporte -- _draw_teletransporte "
        "no debe llamarse desde ahí (la escena lo pinta después de la luz, "
        "mismo patrón del Cambio 3)")


# ──────────────────────────────────────────────
# (e) la ESCENA sí lo pinta, post-luz
# ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def app_headless():
    """Misma receta EXACTA que
    ``test_telegraphs_sobre_la_luz.py::app_headless`` (``App(use_gl=False)``
    fuerza la rama de software de ``dibujar_mundo``, que multiplica la luz
    sobre la MISMA superficie que ``scene.draw(surface)`` recibe). Duplicada
    aquí en vez de importada porque cada archivo de esta suite arma su
    propia sesión de ``App`` (ver el docstring del original para el resto
    del razonamiento: alcance de módulo, teardown a 320x224).

    Lección H-28/B-032 (posterior a este archivo, fix 2026-08-20): las
    pruebas de abajo que llaman ``scene.draw(surface)`` directo prueban el
    MÉTODO, no el despacho real de ``App._draw()`` (que nunca invoca
    ``escena.draw()`` para una ``StageScene`` -- ver el docstring de
    ``test_telegraphs_sobre_la_luz.py::app_headless`` para el detalle
    completo). Siguen siendo válidas por herencia del mixin tras la
    migración a ``dibujar_ui()`` (precedente H-27); el candado por píxeles
    contra el despacho real vive en ``test_despacho_real_overlays.py``."""
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
    """Ver ``test_telegraphs_sobre_la_luz.py::_encuadrar_arena_sin_actualizar``
    -- misma razón exacta (evita disparar ``_update_lighting`` vía
    ``scene.update()``, deja la luz de la arena determinista)."""
    map_h = scene._stage_data.map_pixel_size[1]
    target_y = max(0.0, float(map_h) - settings.INTERNAL_HEIGHT)
    scene._camera.offset.update(ARENA_X0, target_y)


def test_la_escena_pinta_el_desvanecimiento_tras_la_luz(app_headless):
    """Gemelo de
    ``test_telegraphs_sobre_la_luz.py::test_la_escena_pinta_el_anuncio_del_enjambre_tras_la_luz``
    para ``_draw_teletransporte``. Se dispara la transición por el camino
    REAL de daño (``jefe.apply_hit(6.5, (0, 0))``) sin llamar
    ``scene.update()``: recién abierta la ventana, el jefe sigue en su
    spawn (x=3168, y~216 -- flota, más de 280px por encima de los 5 focos
    ``Light_*`` del TMX, todos a nivel de piso), en pleno desvanecimiento.

    TRAMPA descubierta al escribir esta prueba (documentada en el handoff):
    un escaneo de la superficie COMPLETA no sirve aquí, a diferencia del
    test gemelo del Cambio 3. ``_draw_anuncio_del_enjambre`` (Cambio 2) YA
    está en producción y usa exactamente el mismo tinte
    (``_COLOR_ANUNCIO_ENJAMBRE == _TELEGRAPH_WARN_COLOR``), y la escena YA
    lo pinta post-luz (Cambio 3) en cuanto ``is_transitioning`` es True --
    con o sin ``_draw_teletransporte``. Un escaneo global encontraría ESE
    color HOY por la razón equivocada (falso verde). Por eso el sondeo se
    acota a una ventana local de 80x80 centrada en la posición VIEJA en
    pantalla (leída con ``jefe.rect.center`` ANTES de ``apply_hit``): el
    anuncio del enjambre ancla en ``self.rect.center`` -- que HOY, al
    saltar de inmediato, ya es la posición NUEVA (``_destino_de_
    teletransporte()``, en torno a ARENA_CX=2872) -- separada por ~320px en
    X de la posición vieja (x=3168) del anillo implosivo que
    ``_draw_teletransporte`` debe pintar ahí. Esa separación es la que hace
    que esta ventana SÍ dé rojo limpio hoy (nada pinta ese color cerca de
    la posición vieja todavía) sin que el anuncio la contamine."""
    scene = _push_real_scene(app_headless)
    jefe = _find_boss_en_escena(scene)
    _encuadrar_arena_sin_actualizar(scene)

    centro_viejo_mundo = pygame.Vector2(jefe.rect.center)   # ANTES de apply_hit
    jefe.apply_hit(6.5, (0, 0))
    assert jefe.is_transitioning, (
        "el daño no arrancó la transición -- helper roto, no la escena")

    surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    scene.draw(surface)

    offset = scene._camera.offset
    lado = 80
    centro_pantalla = (int(centro_viejo_mundo.x - offset.x), int(centro_viejo_mundo.y - offset.y))
    ventana_rect = pygame.Rect(centro_pantalla[0] - lado // 2, centro_pantalla[1] - lado // 2,
                               lado, lado).clip(surface.get_rect())
    ventana = surface.subsurface(ventana_rect)

    color = _color_de_aviso(jefe)
    assert _contiene_color_exacto(ventana, color), (
        f"ningún píxel cerca de la posición VIEJA del venado es exactamente "
        f"{color!r} tras componer mundo+luz+post+UI -- el anillo implosivo "
        "del desvanecimiento no se pintó ahí (o _draw_teletransporte todavía "
        "no existe / la escena todavía no lo llama post-luz)")


# ──────────────────────────────────────────────
# (f) orden de temporizadores: el salto vence ANTES que _finish_phase_transition
# ──────────────────────────────────────────────

def test_el_salto_ocurre_antes_que_finish_phase_transition_en_el_mismo_frame():
    """Riesgo 6 del dictamen. Nuestro ``update()`` (boss_venado.py
    ~L1156-1190) corre ENTERO antes de delegar en ``super().update()`` --
    confirmado leyendo ``EnemyBase.update`` (enemy_base.py ~L207-230) y
    ``BossBase._pre_update`` (boss_base.py ~L430-436): con ``FADE_
    TELETRANSPORTE`` (~0.55s) << 2.5s de ventana, un ``dt`` normal (1/60s)
    nunca hace que los dos relojes crucen cero en el mismo fotograma, pero
    un ÚNICO ``update(dt)`` con dt gigante -- como el de esta prueba -- sí
    puede. Si el salto llegara a ejecutarse DESPUÉS del avance de fase,
    ``_finish_phase_transition`` abriría el anillo de esporas
    (``_soltar_abanico_de_esporas``, ancla en ``self.rect.center``) con el
    cuerpo TODAVÍA en la posición vieja, y el jugador vería esporas nacer
    lejos de donde el venado termina.

    HOY este test pasa en verde de todos modos (el salto siempre fue
    inmediato, así que por definición siempre ocurre "antes" de que
    ``_finish_phase_transition`` corra dos segundos y medio después) -- no
    es parte del rojo de esta fase, es el candado de orden que la
    implementación futura del desvanecimiento no debe romper."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_X1 - 80.0
    boss.rect.x = int(boss.position.x)
    boss.apply_hit(6.5, (0, 0))
    assert boss.is_transitioning

    boss.update(3.0)          # dt gigante: cubre el desvanecimiento Y la ventana completa de golpe

    assert boss.current_phase == 1, (
        "la fase no avanzó tras un update() que cubre de sobra la ventana")
    assert not boss.is_transitioning
    assert abs(boss.rect.centerx - bv.ARENA_CX) <= 1.0, (
        "el venado no terminó centrado -- el salto no llegó a completarse")
    assert boss.esporas.contador > 0, (
        "la fase 2 debía abrir el anillo de esporas al terminar la transición")
    xs = boss.esporas.x[boss.esporas.vivas]
    assert abs(float(xs.mean()) - bv.ARENA_CX) <= 64.0, (
        "las esporas del anillo nacieron lejos del centro -- el anillo se "
        "abrió con self.rect todavía en la posición VIEJA "
        "(_finish_phase_transition corrió ANTES que el salto del "
        "desvanecimiento, el orden que este candado prohíbe)")
