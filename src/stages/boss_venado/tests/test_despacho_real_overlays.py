"""Fase 1 (RED) del fix H-28/B-032 — candados de regresión, sin tocar el fix.

Dictamen doc-guardian AMARILLO vigente (token registrado). Este módulo NO
implementa nada: describe, con candados que hoy deben fallar en rojo limpio,
el comportamiento DESEADO que la Fase 2 (aún no escrita) tiene que producir.

El bug (FINDINGS H-28/B-032, ~líneas 4737-4843): ``App._draw()`` (app.py
556-723) despacha por duck-typing (``_soporta``, app.py 57-66) a
``dibujar_mundo()``/``dibujar_ui()`` -- JAMÁS llama a ``escena.draw()`` si la
escena implementa esas dos mitades (``StageScene`` las implementa siempre,
ver ``src/framework/scenes/stage_parts/dibujo.py``: ``DibujoDeEscenario.draw``
es sólo ``dibujar_mundo(surface); dibujar_ui(surface)``, un método de
conveniencia que ``App`` nunca invoca cuando la escena soporta la ruta
partida). ``BossVenadoScene`` sólo sobrescribe ``draw()``
(boss_venado_scene.py:448) -- el bloque de overlays de líneas 475-491
(telegraphs del jefe -> anuncio del enjambre -> teletransporte -> halo
aditivo del jugador -> icono de la Reliquia) es, por tanto, código MUERTO
bajo el despacho real del motor: nunca corre ni en ``main.py --boss
boss_venado`` ni en el arnés. El fix (Fase 2, todavía no escrita) migrará
ese bloque a un override de ``dibujar_ui()`` y eliminará ``draw()``.

Por qué las pruebas de ESTE módulo no reutilizan ``scene.draw(surface)``
directo (a diferencia de ``test_telegraphs_sobre_la_luz.py``/
``test_teletransporte_ux.py``, que sí lo hacen y por eso YA pasan hoy pese al
bug: llaman al método muerto directamente en vez de pasar por
``App._draw()``): ese es justo el punto ciego que H-28 describe. Cada
candado de aquí llama, en su lugar, a ``App._draw()`` (el despacho REAL) o a
``scene.dibujar_ui()`` bajo el contrato exacto de composición por alfa que la
ruta de GPU le exige a esa mitad (app.py 230-233/692-703) -- nunca
``scene.draw()``.

Receta de escena real: calcada (no importada) de
``test_telegraphs_sobre_la_luz.py::app_headless``/``_push_real_scene`` -- ver
el docstring de esa fixture para el razonamiento completo (``App(use_gl=
False)`` fuerza la rama de software, evita depender de la caída silenciosa a
software bajo el driver dummy, y dibuja sobre la MISMA superficie que
``App._draw()`` usa de verdad).
"""
import numpy as np
import pygame
import pytest

from src.engine.core import settings
from src.engine.core.app import App
from src.stages.boss_venado.boss_venado_scene import (
    ARENA_X0,
    PLAYER_HALO_PEAK,
    PLAYER_HALO_RADIUS,
    RELIC_ICON_COLOR,
    RELIC_ICON_MARGIN,
    RELIC_ICON_SIZE,
    BossVenadoScene,
)
from src.stages.boss_venado.luciernagas_venado import MAXIMO_LUCIERNAGAS

# ──────────────────────────────────────────────
# Receta compartida (calcada de test_telegraphs_sobre_la_luz.py, no importada)
# ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def app_headless():
    """``App`` real bajo software forzado -- ver el docstring del módulo y el
    de la fixture homónima en ``test_telegraphs_sobre_la_luz.py`` (misma
    receta, misma razón: ``use_gl=False`` deja ``App._draw()`` en la rama de
    software de app.py 704-723, la que compone ``dibujar_ui`` directo sobre
    ``internal_surface`` -- justo la ruta cuyo despacho real hoy nunca llega a
    ``BossVenadoScene.draw()``).

    Alcance de módulo, igual que el original: una sola ``App`` para las tres
    pruebas de este archivo; cada una empuja su propia escena nueva vía
    ``scene_manager.replace()`` (destruye la anterior, no apila estado).

    Teardown: restaura el modo de vídeo a ``(320, 224)`` -- el que
    ``conftest.py`` deja listo para el resto de la suite -- para no dejarle a
    un archivo de pruebas hermano que corra después un modo de vídeo
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


def _encuadrar_y_ubicar_jugador(scene: BossVenadoScene, centro_pantalla: tuple[int, int]) -> None:
    """Fija cámara y jugador en coordenadas de pantalla conocidas, SIN llamar
    a ``scene.update()`` -- mismo motivo que
    ``test_telegraphs_sobre_la_luz.py::_encuadrar_arena_sin_actualizar``: no
    disparar ``_update_lighting`` (que haría avanzar los focos ``Light_*``
    del TMX) ni el asentamiento de cámara H-17, así que la luz y el offset
    quedan deterministas entre las dos pasadas de despacho que cada candado
    de este módulo compara por diferencia. La cámara se encuadra sobre el
    borde izquierdo exacto de la arena (mismo offset que
    ``BossVenadoScene._arena_target_offset()`` asienta tras H-17) y el
    jugador se coloca para caer exactamente en ``centro_pantalla`` dentro de
    esa vista."""
    map_h = scene._stage_data.map_pixel_size[1]
    offset_y = max(0.0, float(map_h) - settings.INTERNAL_HEIGHT)
    scene._camera.offset.update(ARENA_X0, offset_y)
    scene._player.rect.center = (
        int(ARENA_X0) + centro_pantalla[0],
        int(offset_y) + centro_pantalla[1],
    )


def _halo_neutro() -> pygame.Surface:
    """Superficie del mismo tamaño que ``_build_player_halo()`` pero negra y
    opaca -- la identidad de ``pygame.BLEND_RGB_ADD`` (sumar (0,0,0) no
    cambia nada). Sustituir ``scene._player_halo`` por esto entre dos
    despachos deja el resto del fotograma bit a bit igual y anula
    exclusivamente la contribución del halo -- mide su efecto por diferencia
    en vez de comparar contra un umbral absoluto de brillo (que dependería
    del terreno/luz de fondo bajo el jugador, ajeno al halo). El ``fill``
    explícito no es cosmético: una ``Surface`` recién creada no tiene
    contenido garantizado por la API de pygame, y aquí SÍ hace falta negro
    exacto para que la identidad de ``BLEND_RGB_ADD`` se sostenga."""
    superficie = pygame.Surface((PLAYER_HALO_RADIUS * 2, PLAYER_HALO_RADIUS * 2))
    superficie.fill((0, 0, 0))
    return superficie


def _brillo_medio(surface: pygame.Surface, centro: tuple[int, int], radio: int) -> float:
    """Media de brillo (los tres canales, sin ponderar) de un recorte
    cuadrado de lado ``2*radio`` centrado en ``centro``. ``array3d`` (numpy,
    mismo patrón que ``test_telegraphs_sobre_la_luz.py::_contiene_color_
    exacto``) vectoriza la media en vez de recorrer píxel a píxel en Python
    puro -- 800x600 se nota en un bucle manual."""
    rect = pygame.Rect(centro[0] - radio, centro[1] - radio, radio * 2, radio * 2)
    rect = rect.clip(surface.get_rect())
    recorte = surface.subsurface(rect)
    arr = pygame.surfarray.array3d(recorte).astype(np.float64)
    return float(arr.mean())


def _contiene_color_exacto(surface: pygame.Surface, color: tuple[int, int, int]) -> bool:
    """Copiado (no importado) de ``test_telegraphs_sobre_la_luz.py::
    _contiene_color_exacto`` -- busca un píxel con el color EXACTO dado en
    TODA la superficie."""
    arr = pygame.surfarray.array3d(surface)
    objetivo = np.array(color, dtype=arr.dtype)
    return bool(np.all(arr == objetivo, axis=-1).any())


# Punto de la vista donde cae el jugador en las pruebas 1 y 2 -- centro exacto
# del viewport de 800x600 (ver settings.INTERNAL_WIDTH/HEIGHT), lejos de
# cualquier borde donde el recorte de sondeo pudiera recortarse.
_CENTRO_PANTALLA = (settings.INTERNAL_WIDTH // 2, settings.INTERNAL_HEIGHT // 2)

# Umbral de contraste para las pruebas 1 y 2: una fracción conservadora
# (30 %) del pico de un solo canal documentado en PLAYER_HALO_TINT (el canal
# r == PLAYER_HALO_PEAK, ver el docstring de ``_build_player_halo`` en
# boss_venado_scene.py). No es un número mágico -- el degradado lineal de
# ``_build_player_halo`` promedia bastante MÁS que esto dentro del radio
# ``PLAYER_HALO_RADIUS // 2`` que sondean las pruebas (brillo relativo entre
# 0.5 y 1.0 en ese disco interior), así que el margen tolera diferencias
# menores de implementación (redondeo, un recorte de un píxel en el borde de
# pantalla) sin dejar de exigir un contraste inequívoco, no ruido.
_UMBRAL_CONTRASTE = PLAYER_HALO_PEAK * 0.3


# ──────────────────────────────────────────────
# Candado 1 — el despacho REAL del motor debe pintar los overlays
# ──────────────────────────────────────────────

def test_overlays_se_pintan_bajo_el_despacho_real_del_motor(app_headless):
    """Candado anti-trampa central de H-28/B-032.

    HOY ``App._draw()`` (app.py 556-723) nunca llama a
    ``BossVenadoScene.draw()``: con ``escena`` soportando ``dibujar_mundo``
    (``_soporta(escena, "dibujar_mundo")`` es cierto para toda ``StageScene``,
    ver app.py 584-588), la rama ``else: escena.draw(...)`` ni se evalúa, y en
    la rama de software (``use_gl=False``, líneas 704-718) sólo se llama
    ``dibujar_ui`` -- que en ``BossVenadoScene`` no existe como override, así
    que corre la implementación heredada de ``DibujoDeEscenario`` (dibujo.py),
    que jamás pinta el halo del jugador. Este candado usa el halo (en vez de
    un telegraph del jefe) porque se pinta SIEMPRE que hay jugador y cámara
    -- no depende de armar un estado de ataque concreto -- así que es la
    señal más directa y menos frágil de que el bloque de overlays de
    ``draw()`` (líneas 475-491) por fin corre bajo despacho real.

    Método: dos pasadas de ``app._draw()`` REAL con el jugador fijo en
    ``_CENTRO_PANTALLA`` (ver ``_encuadrar_y_ubicar_jugador`` -- sin
    ``scene.update()`` de por medio, así que nada más cambia entre las dos
    pasadas) y se mide, por DIFERENCIA, la contribución exclusiva del halo
    (``_brillo_medio`` en un recorte de radio ``PLAYER_HALO_RADIUS // 2``,
    igual que documenta ``_UMBRAL_CONTRASTE``):

    1. Primera pasada tal cual -- si el fix ya migró el bloque a
       ``dibujar_ui()``, ``scene._player_halo`` sigue ``None`` y se
       construye perezosamente (mismo patrón que hoy en ``draw()``) y se
       pinta.
    2. Se sustituye ``scene._player_halo`` por ``_halo_neutro()`` (negro,
       identidad de ``BLEND_RGB_ADD``) y se repite el despacho -- el resto
       del fotograma (mundo, luz, HUD, todo lo que NO es el halo) es bit a
       bit idéntico a la primera pasada, así que cualquier diferencia de
       brillo en la región sondeada sólo puede venir del halo.

    HOY (código actual): como ``dibujar_ui`` heredado nunca toca
    ``_player_halo`` en absoluto, las dos pasadas son indistinguibles en la
    región sondeada -- ``brillo_con_halo`` y ``brillo_sin_halo`` salen
    iguales y el ``assert`` de contraste falla limpio (rojo esperado).
    Tras la Fase 2, la primera pasada queda más brillante que la segunda por
    encima de ``_UMBRAL_CONTRASTE`` y el candado pasa."""
    scene = _push_real_scene(app_headless)
    _encuadrar_y_ubicar_jugador(scene, _CENTRO_PANTALLA)
    radio = PLAYER_HALO_RADIUS // 2

    app_headless._draw()
    brillo_con_halo = _brillo_medio(app_headless.internal_surface, _CENTRO_PANTALLA, radio)

    scene._player_halo = _halo_neutro()
    app_headless._draw()
    brillo_sin_halo = _brillo_medio(app_headless.internal_surface, _CENTRO_PANTALLA, radio)

    assert brillo_con_halo > brillo_sin_halo + _UMBRAL_CONTRASTE, (
        f"el halo del jugador no aportó contraste bajo App._draw() real "
        f"(con={brillo_con_halo:.2f}, sin={brillo_sin_halo:.2f}, "
        f"umbral={_UMBRAL_CONTRASTE:.2f}) -- BossVenadoScene.draw() sigue "
        "siendo código muerto bajo el despacho por dibujar_mundo/dibujar_ui "
        "(H-28/B-032): migrar el bloque de overlays a un override de "
        "dibujar_ui() y eliminar draw()")


# ──────────────────────────────────────────────
# Candado 2 — el contrato de composición por alfa de la ruta de GPU
# ──────────────────────────────────────────────

def _componer_dibujar_ui_por_alfa(scene: BossVenadoScene) -> pygame.Surface:
    """Emula en CPU, con precisión de píxel, el contrato exacto que la ruta
    de GPU le exige a ``dibujar_ui`` -- ver app.py:

    - 230-233: ``_ui_overlay_surface`` nace ``pygame.SRCALPHA``.
    - 696: cada fotograma se limpia con ``fill((0, 0, 0, 0))`` -- alfa CERO,
      no ``BG_COLOR`` (un relleno opaco ocultaría el mundo entero bajo el
      fondo, comentario textual de AUD-344 en ese mismo bloque).
    - 697-699: la escena pinta ENCIMA de esa superficie translúcida
      (``dibujar_ui(self._ui_overlay_surface)``).
    - 700-703: el renderer compone esa superficie sobre el mundo ya
      procesado por la cadena de pasadas de la tarjeta -- una composición
      que, como cualquier blit normal de pygame contra una superficie
      ``SRCALPHA``, respeta el alfa POR PÍXEL del origen: donde el alfa es
      0, el destino no cambia, sin importar qué valores de RGB haya ahí.

    ``base.blit(overlay, (0, 0))`` (blit normal, sin flags especiales)
    reproduce exactamente esa última propiedad en CPU sin necesitar
    ``GLRenderer`` real: es la forma más simple de blit que respeta el
    contrato de alfa por píxel de una superficie ``SRCALPHA`` de origen,
    igual que la composición que ``self._gl_renderer.render(...,
    overlay=overlay)`` hace puertas adentro."""
    overlay = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 0))            # app.py:696
    scene.dibujar_ui(overlay)             # app.py:697-698, DIRECTO -- nunca scene.draw()
    base = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    base.fill((10, 10, 20))               # base opaca oscura -- el "mundo ya procesado"
    base.blit(overlay, (0, 0))            # composición que SÍ respeta el alfa por píxel
    return base


def test_overlays_sobreviven_la_composicion_por_alfa_de_la_ruta_gl(app_headless):
    """Riesgo 2 del dictamen doc-guardian: no basta con que el fix mueva el
    bloque de ``draw()`` a ``dibujar_ui()`` tal cual -- tiene que sobrevivir
    a la composición por alfa que la ruta de GPU le aplica a esa mitad (ver
    ``_componer_dibujar_ui_por_alfa``).

    La trampa que este candado bloquea: HOY (y en un fix "ingenuo" que sólo
    mueva la línea sin más) el halo se pinta con
    ``surface.blit(self._player_halo, top_left,
    special_flags=pygame.BLEND_RGB_ADD)`` -- ``BLEND_RGB_ADD`` suma sólo los
    canales RGB; el canal ALFA del overlay de destino queda intacto donde
    caiga ese blit. En el camino de software (candado 1) esto no se nota
    porque ahí ``dibujar_ui`` pinta DIRECTO sobre ``internal_surface``, una
    superficie sin alfa por píxel (app.py 704-718) -- no hay composición de
    por medio. Pero bajo el contrato de la ruta de GPU, el overlay nace con
    alfa 0 en todas partes (app.py:696) y ``BLEND_RGB_ADD`` no sube ese alfa:
    los píxeles del halo quedarían con RGB correcto pero alfa 0, y
    ``base.blit(overlay, (0, 0))`` los descartaría enteros en la
    composición -- el halo se pintaría y, acto seguido, se borraría solo. Un
    fix que sólo pase el candado 1 (software) y no éste dejaría el halo
    invisible en la ruta de GPU real del motor.

    Mismo método por diferencia que el candado 1 (``scene._player_halo`` vs.
    ``_halo_neutro()``), pero componiendo con ``_componer_dibujar_ui_por_
    alfa`` en vez de despachar por ``App._draw()`` -- esta prueba no necesita
    tarjeta real ni ``_gl_renderer``, sólo el contrato de superficies que
    ``dibujar_ui`` tiene que respetar para que, cuando SÍ haya tarjeta, la
    composición no se coma el halo.

    HOY: ``dibujar_ui`` heredado no pinta el halo en absoluto (ni siquiera
    con alfa 0) -- las dos composiciones salen idénticas y el ``assert``
    falla limpio. Si una implementación futura pintara el halo pero SIN
    escribir alfa (el riesgo descrito arriba), este candado seguiría en rojo
    aunque el candado 1 ya estuviera en verde -- es justo la señal que debe
    distinguir entre "se mueve la llamada" y "se mueve la llamada Y se
    respeta el contrato de alfa de la ruta de GPU"."""
    scene = _push_real_scene(app_headless)
    _encuadrar_y_ubicar_jugador(scene, _CENTRO_PANTALLA)
    radio = PLAYER_HALO_RADIUS // 2

    compuesto_con_halo = _componer_dibujar_ui_por_alfa(scene)
    brillo_con_halo = _brillo_medio(compuesto_con_halo, _CENTRO_PANTALLA, radio)

    scene._player_halo = _halo_neutro()
    compuesto_sin_halo = _componer_dibujar_ui_por_alfa(scene)
    brillo_sin_halo = _brillo_medio(compuesto_sin_halo, _CENTRO_PANTALLA, radio)

    assert brillo_con_halo > brillo_sin_halo + _UMBRAL_CONTRASTE, (
        f"el halo no sobrevivió a la composición por alfa de la ruta de GPU "
        f"(con={brillo_con_halo:.2f}, sin={brillo_sin_halo:.2f}, "
        f"umbral={_UMBRAL_CONTRASTE:.2f}) -- o dibujar_ui no lo pinta "
        "todavía (H-28/B-032), o lo pinta con BLEND_RGB_ADD puro dejando el "
        "canal alfa del overlay en 0 (riesgo 2 del dictamen doc-guardian): "
        "la composición por alfa de app.py:692-703 lo descartaría entero en "
        "la ruta de GPU real")


# ──────────────────────────────────────────────
# Candado 3 — un overlay NO ligado al jugador (icono de la Reliquia)
# ──────────────────────────────────────────────

def test_icono_de_reliquia_e_iconografia_bajo_despacho_real(app_headless):
    """Variante del candado 1 para un overlay anclado a la PANTALLA, no al
    jugador ni al jefe: el icono de "Fragmento de Reliquia 1" (adopción V3,
    D10; ``_draw_relic_icon``, boss_venado_scene.py:388-413), que hoy
    también vive dentro del bloque muerto de ``draw()`` (línea 491).

    Se eligió el icono de la Reliquia y no un telegraph post-luz del jefe
    (la otra opción que sugiere el encargo) porque es el overlay MENOS
    frágil de sondear por píxeles: su posición es un rincón fijo de la
    PANTALLA (``ancho - RELIC_ICON_SIZE - RELIC_ICON_MARGIN``, ``RELIC_ICON_
    MARGIN``, ver ``_draw_relic_icon``), independiente de cámara, arena o
    posición del jefe -- sondear un telegraph exige además razonar sobre
    focos ``Light_*`` cercanos y el encuadre exacto de la arena (ver los
    docstrings de ``test_telegraphs_sobre_la_luz.py``), mientras que este
    rincón es el mismo sondeado sin importar dónde estén jugador o jefe. Y a
    diferencia del halo (aditivo, sin bordes nítidos), el icono se dibuja con
    ``pygame.draw.lines``/``pygame.draw.circle`` SIN antialiasing sobre una
    superficie ``SRCALPHA`` con ``RELIC_ICON_COLOR`` exacto y luego
    ``set_alpha(255)`` cuando el fundido ya terminó -- así que, a diferencia
    del halo, aquí SÍ es seguro un sondeo de color EXACTO (mismo patrón que
    ``test_telegraphs_sobre_la_luz.py::_contiene_color_exacto``) en vez de
    una comparación diferencial de brillo.

    Se fuerza ``scene._relic_timer = 2.0`` -- fuera de las dos ventanas de
    fundido (``RELIC_FADE_DURATION = 0.6``s): ``transcurrido = RELIC_BANNER_
    DURATION(4.0) - 2.0 = 2.0`` y el propio ``_relic_timer`` (2.0) son ambos
    mayores que ``RELIC_FADE_DURATION``, así que ``fade = min(1.0, ...) ==
    1.0`` y ``alpha == 255`` (icono totalmente opaco, ver ``_draw_relic_
    icon``) sin depender de ``reliquia_anunciada``/``_update_relic_banner``
    -- mismo atajo que ya usa ``test_adopcion_v3.py::test_el_icono_de_
    reliquia_se_dibuja_tras_el_anuncio`` para ejercitar ``_draw_relic_icon``
    de forma aislada.

    HOY: ``App._draw()`` real nunca llama ``_draw_relic_icon`` (vive en el
    bloque muerto de ``draw()``), así que ningún píxel del rincón sondeado es
    exactamente ``RELIC_ICON_COLOR`` -- rojo limpio. Nota de solape conocida
    y no relevante para este candado: el rincón sondeado (rect en
    ``(ancho - RELIC_ICON_SIZE - RELIC_ICON_MARGIN, RELIC_ICON_MARGIN,
    RELIC_ICON_SIZE, RELIC_ICON_SIZE)`` = 748,12 a 788,52 en 800x600) roza en
    sus 2 px inferiores el marco del cronómetro del HUD (``HUD._timer_rect``,
    aprox. 720-800 x 5-40 en pantalla real) -- el trazo del icono (astas y
    cráneo) queda casi entero por encima de esa franja, así que el candado
    sigue teniendo de sobra dónde encontrar el color exacto aunque el HUD
    pinte debajo primero (el propio orden de ``draw()`` de hoy, que la Fase 2
    debe preservar: overlays SIEMPRE después del resto de la interfaz)."""
    scene = _push_real_scene(app_headless)
    scene._relic_icon = None
    scene._relic_shown = True
    scene._relic_timer = 2.0

    app_headless._draw()

    ancho = settings.INTERNAL_WIDTH
    x = ancho - RELIC_ICON_SIZE - RELIC_ICON_MARGIN
    rincon_rect = pygame.Rect(x, RELIC_ICON_MARGIN, RELIC_ICON_SIZE, RELIC_ICON_SIZE)
    rincon_rect = rincon_rect.clip(app_headless.internal_surface.get_rect())
    rincon = app_headless.internal_surface.subsurface(rincon_rect)

    assert _contiene_color_exacto(rincon, RELIC_ICON_COLOR), (
        f"ningún píxel del rincón superior derecho ({rincon_rect}) es "
        f"exactamente {RELIC_ICON_COLOR!r} tras App._draw() real -- "
        "_draw_relic_icon sigue viviendo en el bloque muerto de "
        "BossVenadoScene.draw() (H-28/B-032): migrarlo también al override "
        "de dibujar_ui()")


# ──────────────────────────────────────────────
# Candado 4 — el filo de la oleada de lianas (pulido AAA 2026-08-21, Task 5)
# ──────────────────────────────────────────────

def test_filo_de_oleada_bajo_despacho_real(app_headless):
    """Candado H-28 extendido (spec 2026-08-21 §7.5, riesgo 6 del dictamen
    AMARILLO): el filo de la oleada de lianas (OleadaDeLianas.dibujar_overlay,
    llamado desde BossVenado._draw_telegraphs -> dibujar_ui) debe sobrevivir el
    despacho REAL de App._draw() -- mismo patrón que el candado 1 de este
    módulo, con una oleada en vez del halo del jugador.

    Nota de ubicación (hallazgo de esta sesión vía TDD -- el snippet literal
    de la Task 5 del plan colocaba la oleada en ``_CENTRO_PANTALLA``, el
    mismo punto donde cae el jugador): ese punto queda DENTRO de
    ``PLAYER_HALO_RADIUS`` (44px, ``boss_venado_scene.py``) del halo aditivo
    del jugador -- ``dibujar_ui`` pinta el halo (``BLEND_RGBA_ADD``) justo
    DESPUÉS de ``_draw_telegraphs``, así que un filo a sólo 24px sobre el
    jugador (``OLEADA_ALTO``) sale contaminado por la suma y ningún píxel
    conserva el color EXACTO del telegraph (confirmado neutralizando el
    halo: con él en negro el mismo assert sí encuentra el color -- la
    implementación de ``dibujar_overlay`` es correcta, la colisión es sólo
    geométrica). Por eso se sondea un punto bien alejado del jugador
    (150px verticales de más sobre ``_CENTRO_PANTALLA``, fuera con margen
    del radio del halo) para que el candado mida específicamente la
    supervivencia del filo de la oleada bajo despacho real, sin ruido de un
    overlay no relacionado."""
    from src.stages.boss_venado.efectos_venado import OleadaDeLianas

    scene = _push_real_scene(app_headless)
    _encuadrar_y_ubicar_jugador(scene, _CENTRO_PANTALLA)
    jefe = scene._get_boss()
    assert jefe is not None, "BossVenado_01 no aparecio en entity_list"

    offset = scene._camera.offset
    mundo_x = offset.x + _CENTRO_PANTALLA[0]
    y_suelo = offset.y + _CENTRO_PANTALLA[1] + 150.0   # lejos del halo del jugador, ver nota arriba
    oleada = OleadaDeLianas(mundo_x, 1, y_suelo, ARENA_X0, ARENA_X0 + 2000.0)
    jefe._oleadas = [oleada]

    app_headless._draw()

    r = oleada.rect
    fila_y = int(r.top - offset.y)
    color = jefe._TELEGRAPH_WARN_COLOR
    fila_rect = pygame.Rect(0, max(0, fila_y - 2), settings.INTERNAL_WIDTH, 5)
    fila_rect = fila_rect.clip(app_headless.internal_surface.get_rect())
    ventana = app_headless.internal_surface.subsurface(fila_rect)
    assert _contiene_color_exacto(ventana, color), (
        f"ningun pixel de la fila del filo de la oleada (y={fila_y}) es "
        f"exactamente {color!r} tras App._draw() real -- "
        "OleadaDeLianas.dibujar_overlay no sobrevive el despacho real "
        "(candado H-28 extendido, spec 2026-08-21)")


# ──────────────────────────────────────────────
# Candado 5 — anillo de caída del STOMP y estrellas de aturdimiento del
# CHARGE bajo despacho real (H-28/pulido AAA fase 2, Task 8)
# ──────────────────────────────────────────────

def test_anillo_de_caida_se_pinta_bajo_despacho_real(app_headless):
    """Fuerza el telegraph de STOMP sobre el jefe REAL de la escena y
    comprueba, vía App._draw(), que aparece al menos un pixel del color de
    aviso -- el mismo patron anti-trampa que ya usan los candados 1-4 de
    este archivo (despacho real, nunca scene.draw()/jefe.draw() aislado)."""
    scene = _push_real_scene(app_headless)
    _encuadrar_y_ubicar_jugador(scene, _CENTRO_PANTALLA)
    jefe = scene._get_boss()
    assert jefe is not None
    # Solo se reubica el eje X (dentro de la arena, bajo el encuadre de la
    # cámara); el eje Y se deja como está -- _draw_telegraphs calcula la
    # altura del anillo de STOMP con la constante FLOOR_Y, no con
    # jefe.rect.centery, así que tocar ese eje aquí no tendría ningún efecto.
    jefe.rect.centerx = int(ARENA_X0) + _CENTRO_PANTALLA[0]
    jefe.position.x, jefe.position.y = float(jefe.rect.x), float(jefe.rect.y)
    jefe._telegraph = "STOMP"
    jefe._telegraph_timer = jefe._telegraph_timer or 0.4

    app_headless._draw()

    assert _contiene_color_exacto(app_headless.internal_surface, jefe._TELEGRAPH_WARN_COLOR), (
        "el anillo de caida de STOMP no se pinto bajo App._draw() real")


def test_estrellas_de_aturdimiento_se_pintan_bajo_despacho_real(app_headless):
    """Mismo patron que el anterior, pero con la ventana de castigo de
    CHARGE (pausa de pared): _charge_recover > 0 basta para que
    _draw_telegraphs pinte las estrellitas sobre la cabeza del jefe."""
    scene = _push_real_scene(app_headless)
    _encuadrar_y_ubicar_jugador(scene, _CENTRO_PANTALLA)
    jefe = scene._get_boss()
    assert jefe is not None
    jefe._charge_recover = 0.5

    app_headless._draw()

    assert _contiene_color_exacto(app_headless.internal_surface, jefe._TELEGRAPH_WARN_COLOR), (
        "las estrellitas de aturdimiento no se pintaron bajo App._draw() real")


# ──────────────────────────────────────────────
# Candado 6 — contraste de SenalDeCastigo bajo despacho real (Task 8)
# ──────────────────────────────────────────────

def _senal_neutra(jefe) -> None:
    """Sustituye la cache de SenalDeCastigo por una que devuelve una
    silueta completamente negra y opaca -- misma tecnica de "neutralizar
    por identidad" que _halo_neutro() mas arriba, aplicada a la senal en
    vez de al halo: negro sobre BLEND_RGBA_ADD no aporta brillo, asi que la
    diferencia con/sin senal mide exclusivamente su contribucion."""
    import pygame as pg

    class _SenalNegra:
        def dibujar_overlay(self, surface, frame, clave, destino, t):
            negra = pg.Surface(frame.get_size(), pg.SRCALPHA)
            negra.fill((0, 0, 0, 255))
            x, y = destino
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                surface.blit(negra, (x + dx, y + dy), special_flags=pg.BLEND_RGBA_ADD)

    jefe._senal = _SenalNegra()


def test_senal_de_castigo_dibuja_solo_el_contorno_bajo_despacho_real(app_headless):
    """Candado 6, REESCRITO por la corrección visual del coordinador
    (Task 14-A, 2026-08-22): SenalDeCastigo dejó de ser una silueta dorada
    pulsante COMPLETA -- ahora es un anillo de contorno de 1px (ver
    efectos_venado.SenalDeCastigo). Medir brillo PROMEDIO en un radio de 6px
    alrededor del centro (como hacía este candado antes del rediseño) ya no
    tiene sentido: un anillo de 1px apenas mueve un promedio sobre un disco
    de 12px de lado. El candado nuevo mide por PIXEL: el centro del cuerpo
    (interior, lejos de cualquier borde) NO debe cambiar un solo canal, y
    debe existir AL MENOS un pixel bajo el rect del jefe que sí se ilumine
    -- el contorno. Mismo método por diferencia que el candado viejo
    (con/sin señal, neutralizando con _senal_neutra), solo que ahora se
    compara pixel a pixel en vez de promediar."""
    scene = _push_real_scene(app_headless)
    _encuadrar_y_ubicar_jugador(scene, _CENTRO_PANTALLA)
    jefe = scene._get_boss()
    assert jefe is not None
    jefe._stomp_recover = 0.3
    ox, oy = scene._camera.offset.x, scene._camera.offset.y
    centro_jefe = (int(jefe.rect.centerx - ox), int(jefe.rect.centery - oy))

    app_headless._draw()
    con = pygame.surfarray.array3d(app_headless.internal_surface).astype(np.int32)

    _senal_neutra(jefe)
    app_headless._draw()
    sin = pygame.surfarray.array3d(app_headless.internal_surface).astype(np.int32)

    diff = con - sin
    cx, cy = centro_jefe
    assert tuple(diff[cx, cy]) == (0, 0, 0), (
        "un pixel interior del cuerpo del jefe cambió con la señal de castigo -- "
        "debería ser solo un anillo de contorno, no la silueta completa")

    rect_jefe = pygame.Rect(int(jefe.rect.x - ox) - 2, int(jefe.rect.y - oy) - 2,
                             jefe.rect.width + 4, jefe.rect.height + 4)
    rect_jefe = rect_jefe.clip(pygame.Rect(0, 0, *app_headless.internal_surface.get_size()))
    recorte = diff[rect_jefe.x:rect_jefe.x + rect_jefe.width,
                    rect_jefe.y:rect_jefe.y + rect_jefe.height]
    assert recorte.sum(axis=-1).max() > 0, (
        "ningún pixel del contorno se iluminó con la señal de castigo bajo App._draw() real")


# ──────────────────────────────────────────────
# Candado 7 — luciérnagas (Unidad VII, Tarea 12 del plan de peregrinación)
# sobreviven la composición por alfa de la ruta de GPU
# ──────────────────────────────────────────────

def test_luciernagas_sobreviven_la_composicion_por_alfa_de_la_ruta_gl(app_headless):
    """Candado NUEVO (no pedido literalmente por el plan, añadido en la
    verificación de calidad de esta tarea): mismo riesgo 2 del dictamen
    doc-guardian que ya cubre el candado 2 de este archivo para el halo, pero
    para ``BossVenadoScene._dibujar_luciernagas`` (Tarea 12).

    Por qué hace falta un candado propio y no basta con el candado 1
    ("_dibujar_luciernagas se llama bajo App._draw() real"): ``_dibujar_luciernagas``
    ya se ejerce estructuralmente por venir colgada de ``dibujar_ui`` (el
    candado 1 de este archivo, que despacha ``App._draw()`` real, ya prueba
    que ese método entero corre) -- lo que NINGÚN candado existente cubre
    todavía es si el DIBUJO concreto de las luciérnagas sobrevive la
    composición por alfa que la ruta de GPU le exige a ``dibujar_ui`` (ver
    ``_componer_dibujar_ui_por_alfa`` arriba). El riesgo es real: si alguien
    tocara ``_dibujar_luciernagas`` y cambiara ``BLEND_RGBA_ADD`` por
    ``BLEND_RGB_ADD`` (el mismo error que originalmente tenía el halo, ver
    ``_build_player_halo``), las luciérnagas seguirían pintándose bien en la
    ruta de software (candado 1, que usa ``App(use_gl=False)``) pero
    quedarían invisibles en la ruta de GPU real del motor -- exactamente el
    tipo de falso verde silencioso que H-28 enseñó a este proyecto a no
    volver a dejar pasar.

    Método por diferencia (mismo patrón que el candado 2): se fuerza
    ``cantidad_objetivo`` al máximo (``MAXIMO_LUCIERNAGAS``, en vez de
    esperar a que el histograma real lo calcule -- aislar el candado de la
    lógica de muestreo, que ya tiene su propia cobertura en
    test_luciernagas_venado.py/test_boss_scene.py) y ``_tiempo_luciernagas``
    a un valor fijo (para que el parpadeo sea idéntico entre las dos
    composiciones que se comparan) y se mide el brillo medio de TODA la
    superficie (las luciérnagas se reparten por ángulo dorado en toda la
    pantalla, a diferencia del halo que es puntual -- por eso aquí el sondeo
    cubre el frame entero, radio = las dimensiones completas, en vez de un
    recorte pequeño centrado)."""
    scene = _push_real_scene(app_headless)
    _encuadrar_y_ubicar_jugador(scene, _CENTRO_PANTALLA)
    scene._tiempo_luciernagas = 1.0   # fase de parpadeo fija -- misma en las dos composiciones
    centro_pantalla = (settings.INTERNAL_WIDTH // 2, settings.INTERNAL_HEIGHT // 2)
    radio_pantalla_completa = max(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)

    scene._gestor_luciernagas.cantidad_objetivo = MAXIMO_LUCIERNAGAS
    compuesto_con = _componer_dibujar_ui_por_alfa(scene)
    brillo_con = _brillo_medio(compuesto_con, centro_pantalla, radio_pantalla_completa)

    scene._gestor_luciernagas.cantidad_objetivo = 0
    compuesto_sin = _componer_dibujar_ui_por_alfa(scene)
    brillo_sin = _brillo_medio(compuesto_sin, centro_pantalla, radio_pantalla_completa)

    assert brillo_con > brillo_sin, (
        f"las luciérnagas no sobrevivieron la composición por alfa de la ruta "
        f"de GPU (con={brillo_con:.4f}, sin={brillo_sin:.4f}) -- o dibujar_ui "
        "no las pinta todavía, o las pinta con BLEND_RGB_ADD puro dejando el "
        "canal alfa del overlay en 0 (riesgo 2 del dictamen doc-guardian): la "
        "composición por alfa de app.py:692-703 las descartaría enteras en la "
        "ruta de GPU real")


# ──────────────────────────────────────────────
# Candado 8 — el velo de niebla del corredor sobrevive la composición por
# alfa de la ruta GL sin devorar el mundo (B-049)
# ──────────────────────────────────────────────

def test_velo_de_niebla_sobrevive_la_composicion_por_alfa_de_la_ruta_gl(app_headless):
    """B-049 (REGISTRO-DE-BUGS.md) -- "mundo negro" en todo el Acto 3 bajo la
    ruta de GPU, detectado en playtest humano (2026-08-25).

    La trampa (misma familia que el riesgo 2 del dictamen doc-guardian que ya
    resolvió el halo -- candado 2 de este archivo -- y las luciérnagas --
    candado 7 -- pero al REVÉS de esos dos): antes de este fix,
    ``_build_velo_de_niebla`` construía una Surface de pantalla completa SIN
    ``pygame.SRCALPHA``, y ``_dibujar_velo_de_niebla`` la pintaba con
    ``Surface.set_alpha()`` (alfa POR SUPERFICIE, no por píxel) más un
    ``surface.blit(..., (0, 0))`` normal, sin flags. Blitear un origen SIN
    canal alfa por píxel sobre un destino ``SRCALPHA`` (el overlay de
    ``dibujar_ui`` bajo la ruta GL, app.py 230-233/696) deja el ALFA DE
    DESTINO en 255 (opaco) en TODA el área cubierta por el blit -- y el velo
    cubre la pantalla ENTERA, así que ese único blit dejaba el overlay
    COMPLETO marcado opaco con el tinte ya atenuado del velo. Como el velo se
    pinta PRIMERO en ``dibujar_ui`` (ver su docstring, "B-046: PRIMERO"), la
    composición final de la ruta GL (``base.blit(overlay, (0, 0))``, mismo
    contrato que ``_componer_dibujar_ui_por_alfa`` documenta arriba)
    sustituía el MUNDO ENTERO por ese tinte -- "mundo negro" en todo el
    Acto 3, confirmado con la escena real
    (``reports\\peregrinacion_playtest_humano\\debug_negro\\repro_negro.py``:
    lum_gl~9-19 contra lum_sw~36-44 en x=1530/1550/1575; la ruta de software,
    sin overlay de por medio, no se veía afectada).

    Este candado sondea el overlay CRUDO (no compuesto sobre ningún "mundo"
    todavía -- necesita el canal alfa del propio overlay, no solo el
    resultado final) en un punto lejos de cualquier otro overlay conocido:
    esquina inferior izquierda de la pantalla, lejos del HUD/minimapa (ambos
    arriba, ver ``DibujoDeEscenario.dibujar_ui``/``HUD._draw_boss_hud``/
    ``Minimap``) y del halo del jugador (el jugador se coloca en x=2000 --
    Acto 3 sostenido, ``VELO_ALFA_MAX`` pleno -- pero la cámara queda
    encuadrada por ``_encuadrar_y_ubicar_jugador`` sobre el borde de la
    arena, así que en pantalla el jugador cae muy a la izquierda del
    viewport, lejos del punto sondeado). Las luciérnagas se fuerzan a 0
    (``cantidad_objetivo``, mismo motivo que el candado 7: su posición es
    determinista por ángulo dorado y podría, por casualidad, caer sobre el
    punto sondeado).

    HOY (antes del fix): el alfa sondeado sale ~255 (el bug) en vez de
    ``VELO_ALFA_MAX`` (80) -- el primer assert falla limpio. Tras el fix, el
    alfa del overlay en ese punto es el alfa POR PÍXEL real que
    ``alfa_de_niebla`` calculó, y componer ese overlay sobre un "mundo"
    sintético CLARO conserva la mayor parte de su luz (en vez de quedar
    sustituido casi entero por el gris apagado del velo, que es justo lo que
    el bug le hacía al mundo real)."""
    from src.stages.boss_venado.efectos_venado import VELO_ALFA_MAX

    scene = _push_real_scene(app_headless)
    _encuadrar_y_ubicar_jugador(scene, _CENTRO_PANTALLA)
    scene._player.rect.centerx = 2000   # Acto 3 sostenido -- alfa_de_niebla == VELO_ALFA_MAX
    scene._gestor_luciernagas.cantidad_objetivo = 0   # aislar el velo, ver docstring

    overlay = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 0))            # app.py:696
    scene.dibujar_ui(overlay)             # DIRECTO -- nunca scene.draw()

    punto = (20, settings.INTERNAL_HEIGHT - 20)   # esquina inferior izquierda -- ver docstring
    alfa_ahi = overlay.get_at(punto)[3]

    assert alfa_ahi < 200, (
        f"el alfa del overlay en {punto} es {alfa_ahi} (~255 esperado bajo el "
        "bug B-049) -- el velo de niebla, bliteado SIN SRCALPHA usando "
        "set_alpha() (alfa por superficie), clobbea el alfa de DESTINO a "
        "opaco en toda la pantalla bajo la ruta GL: la composición "
        "posterior sustituiría el mundo entero por el tinte del velo")
    assert abs(alfa_ahi - VELO_ALFA_MAX) <= 5, (
        f"el alfa del overlay ({alfa_ahi}) no coincide con VELO_ALFA_MAX "
        f"({VELO_ALFA_MAX}) en la zona sondeada")

    # "Mundo" sintético CLARO (no el (10,10,20) oscuro de
    # _componer_dibujar_ui_por_alfa, que no distingue "opaco con tinte oscuro"
    # de "opaco por el bug") -- debe conservar la mayor parte de la luz, no
    # sustituirla por el gris apagado del velo.
    mundo_claro = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    mundo_claro.fill((220, 220, 220))
    compuesto = mundo_claro.copy()
    compuesto.blit(overlay, (0, 0))
    brillo = _brillo_medio(compuesto, punto, 5)

    assert brillo > 150, (
        f"la composición del velo sobre un mundo claro quedó demasiado "
        f"oscura en {punto} (brillo={brillo:.1f}) -- el velo (alfa pleno "
        f"{VELO_ALFA_MAX}/255, ~31%) no debería sustituir casi todo el "
        "mundo por su propio color apagado")
