"""Fase RED — campaña de fairness (Cambio 2): anuncio visual del enjambre de
esporas de la transición de fase.

Hoy (dictamen doc-guardian AMARILLO vigente, token registrado)
``_finish_phase_transition`` suelta el anillo de 12 esporas
(``_soltar_abanico_de_esporas``) en el instante exacto en que se cierra la
ventana de 2.5 s de quietud, sin ningún anuncio visual previo -- incumple doc
86 §2.4 regla 5 ("si algo se activa, se anuncia"). El jugador ve al venado
inmóvil y brillando (``_draw_transition_pulse``, VFX de color genérico de la
propia transición) y, sin ningún aviso adicional, un anillo de proyectiles
aparece ya en movimiento.

Este módulo describe el comportamiento DESEADO (fase GREEN todavía sin
implementar): mientras ``self.is_transitioning`` es True, el boss dibuja un
anuncio propio del enjambre que va a soltar -- un método nuevo
``_draw_anuncio_del_enjambre(surface, offset)``, invocado desde ``draw()`` --
anclado a ``self.rect`` (la posición YA es la nueva: el teletransporte ocurre
al ABRIR la ventana, en ``_start_phase_transition``, no al cerrarla).

Restricción dura (riesgo 1 del dictamen, candado M-1,
``test_el_teletransporte_no_deja_hitboxes_huerfanas`` en
``test_adopcion_v3.py``): el anuncio NO puede usar
``self._telegraph``/``self._telegraph_timer`` -- esos dos campos deben seguir
valiendo ``""``/``0.0`` durante TODA la ventana de transición. El progreso
visual del anuncio debe salir de ``self.transition_timer`` (el reloj que ya
mantiene ``BossBase``, arranca en 2.5 y decrece) o de un campo propio nuevo,
nunca del sistema de telegraph de ataques.

Todos los asserts están escritos para fallar limpio (AssertionError) contra el
código de HOY, nunca por AttributeError: el método nuevo se lee con
``getattr(boss, "_draw_anuncio_del_enjambre", None)`` porque todavía no
existe, y el color de aviso se resuelve con el mismo patrón
(``getattr(boss, "_COLOR_ANUNCIO_ENJAMBRE", boss._TELEGRAPH_WARN_COLOR)``) para
no atarse a un nombre de constante que la fase GREEN todavía no decidió.

Nota de estado (Cambio 2 y Cambio 3 ya llegaron a GREEN: ``_draw_anuncio_
del_enjambre`` existe y ``boss_venado_scene.py`` ya lo pinta post-luz -- el
resto de este docstring describe fielmente el diseño original, sólo el
estado "todavía sin implementar" quedó desactualizado).

Lección H-28/B-032 (fix 2026-08-20): "ya lo pinta post-luz" describe el
CÓDIGO, no lo que el juego real mostraba -- ``BossVenadoScene`` pintaba ese
bloque desde un override de ``draw()``, y ``App._draw()`` (AUD-343) nunca
llama a ``escena.draw()`` para una ``StageScene``, así que hasta el fix de
H-28 el anuncio era código MUERTO en ``main.py --boss boss_venado`` pese a
que las pruebas de ``test_telegraphs_sobre_la_luz.py`` (que llaman
``scene.draw(surface)`` directo) ya estaban en verde. Este archivo no se
vio afectado porque ejercita ``_draw_anuncio_del_enjambre`` directo sobre el
propio jefe, sin pasar por la escena -- prueba el MÉTODO, que siempre
estuvo correcto; el candado que distingue eso del despacho real de la
escena vive en ``test_despacho_real_overlays.py``.

Adaptación Cambio 5 (fairness, dictamen doc-guardian AMARILLO vigente, orden
del usuario 2026-08-18): el teletransporte de fase deja de ser instantáneo
-- el venado se desvanece ``FADE_TELETRANSPORTE`` (~0.55s) en su posición
VIEJA antes de saltar (ver ``test_teletransporte_ux.py``). El anuncio del
enjambre está anclado a ``self.rect.center``, que YA NO es la posición final
desde el primer fotograma de la ventana: por eso pasa a dibujarse SÓLO
DESPUÉS del salto (durante el desvanecimiento, cero píxeles). Los tests 2, 4
y 6 se adaptan para reflejarlo; 1, 3 y 5 se revisaron y no cruzan el corte
del desvanecimiento (ver nota en cada uno).
"""
import pygame

from src.stages.boss_venado.boss_venado import BossVenado


def make_boss(with_bus: bool = False):
    """Mismo constructor que el resto de la suite: spawn dentro de la arena."""
    boss = BossVenado(pygame.Vector2(3168, 240))
    bus = None
    if with_bus:
        from src.engine.core.event_bus import EventBus
        bus = EventBus()
        boss.set_event_bus(bus)
    return boss, bus


def _arrancar_transicion_real(boss) -> None:
    """Lleva al jefe a una transición de fase REAL por el camino real (daño),
    igual que hace el candado M-1 (``test_el_teletransporte_no_deja_hitboxes_huerfanas``
    en ``test_adopcion_v3.py``): 12 -> 5.5, por debajo del umbral 6.0 de la
    fase 2, arranca ``_check_phase_transition`` -> ``_start_phase_transition``
    de forma síncrona dentro de ``apply_hit`` (``boss_base.py`` L246-263). No
    hace falta llamar a ``update()``: al volver de ``apply_hit`` el jefe ya
    tiene ``is_transitioning=True`` y ``transition_timer==2.5``, ya
    teletransportado al centro de la arena (nuestro override de
    ``_start_phase_transition``)."""
    boss.apply_hit(6.5, (0, 0))
    assert boss.is_transitioning, "el candado de daño no arrancó la transición -- helper roto, no el jefe"


def _superficie_de_prueba() -> pygame.Surface:
    surface = pygame.Surface((200, 200))
    surface.fill((10, 10, 10))
    return surface


def _offset_centrado(boss) -> pygame.Vector2:
    return pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100)


DT = 1.0 / 60.0


def _fade_teletransporte(boss) -> float:
    """Duración del desvanecimiento del Cambio 5 (``FADE_TELETRANSPORTE``),
    misma receta que ``test_adopcion_v3.py::_fade_teletransporte`` --
    duplicada aquí porque este módulo no importa el paquete como ``bv``.
    ``getattr`` con caída a 0.55 porque el dictamen no fija todavía si será
    una constante de módulo o un atributo de clase."""
    valor = getattr(boss, "FADE_TELETRANSPORTE", None)
    if valor is None:
        valor = getattr(type(boss), "FADE_TELETRANSPORTE", None)
    return float(valor) if valor is not None else 0.55


def _avanzar_tras_el_salto(boss) -> None:
    """Corre ``update(DT)`` lo suficiente para cubrir ``FADE_TELETRANSPORTE``
    (con margen) sin acercarse a los 2.5s de la ventana completa -- deja al
    jefe justo después del salto real, todavía en plena transición, con
    ``self.rect.center`` ya en la posición final."""
    frames = int((_fade_teletransporte(boss) + 0.05) / DT)
    for _ in range(frames):
        boss.update(DT)


# ──────────────────────────────────────────────
# 1 — el método nuevo existe
# ──────────────────────────────────────────────

def test_existe_el_metodo_de_anuncio():
    """``draw()`` (boss_venado.py ~L1212-1221) hoy no invoca ningún método de
    anuncio de enjambre -- ni el método existe todavía en la clase.

    Revisado para Cambio 5: no cruza el corte del desvanecimiento (no monta
    ninguna transición ni compara superficies) -- sin cambios."""
    boss, _ = make_boss()
    metodo = getattr(boss, "_draw_anuncio_del_enjambre", None)
    assert callable(metodo), (
        "falta el método _draw_anuncio_del_enjambre (anuncio visual del "
        "enjambre de esporas que se suelta al cerrar la transición de fase)")


# ──────────────────────────────────────────────
# 2 — se dibuja algo distinguible durante la transición
# ──────────────────────────────────────────────

def test_el_anuncio_se_dibuja_durante_la_transicion():
    """No se compara transición vs no-transición (``_draw_transition_pulse``
    ya dibuja su propio VFX de color durante toda la ventana y enmascararía la
    comparación): se compara la salida PROPIA del método nuevo contra la
    superficie base sin tocar.

    Adaptación Cambio 5 (dictamen doc-guardian AMARILLO, orden del usuario
    2026-08-18): el anuncio está anclado a ``self.rect.center``, y esa
    posición ya NO es la final desde el primer fotograma -- el venado se
    desvanece en su sitio VIEJO durante ``FADE_TELETRANSPORTE`` (~0.55s)
    antes de saltar. Este test se parte en dos comprobaciones: (a) recién
    abierta la ventana, todavía desvaneciéndose, NO debe dibujarse nada
    (el enjambre ni siquiera nació en su posición final); (b) tras el
    salto real, sí se dibuja algo distinguible, igual que antes. HOY (a)
    falla en rojo limpio: el código actual dibuja el anuncio desde el
    fotograma 0 de la ventana, sin noción de desvanecimiento."""
    boss, _ = make_boss()
    _arrancar_transicion_real(boss)

    metodo = getattr(boss, "_draw_anuncio_del_enjambre", None)
    assert callable(metodo), "falta _draw_anuncio_del_enjambre"

    # (a) recién abierta la ventana -- todavía desvaneciéndose.
    offset = _offset_centrado(boss)
    base = _superficie_de_prueba()
    recien_abierta = base.copy()
    metodo(recien_abierta, offset)
    assert pygame.image.tobytes(recien_abierta, "RGB") == pygame.image.tobytes(base, "RGB"), (
        "_draw_anuncio_del_enjambre dibujó durante el desvanecimiento -- "
        "Cambio 5 exige que sólo se dibuje después del salto")

    # (b) tras el salto real -- ya en la posición final.
    _avanzar_tras_el_salto(boss)
    offset_final = _offset_centrado(boss)      # el centro pudo desplazarse con el salto
    base2 = _superficie_de_prueba()
    con_anuncio = base2.copy()
    metodo(con_anuncio, offset_final)
    assert pygame.image.tobytes(con_anuncio, "RGB") != pygame.image.tobytes(base2, "RGB"), (
        "_draw_anuncio_del_enjambre no pinta nada distinguible tras el salto")


# ──────────────────────────────────────────────
# 3 — jamás reutiliza el sistema de telegraph de ataques (candado M-1)
# ──────────────────────────────────────────────

def test_el_anuncio_no_usa_el_sistema_de_telegraph():
    """Compatibilidad literal con el candado M-1: durante TODA la ventana de
    transición, ``self._telegraph``/``self._telegraph_timer`` deben seguir
    valiendo ``""``/``0.0`` -- también después de invocar el anuncio nuevo.
    Se hace fallar primero por el método ausente (no por la parte M-1) para
    que el mensaje de fallo de HOY sea inequívoco.

    Revisado para Cambio 5: se invoca en el fotograma 0 de la ventana
    (durante el desvanecimiento), a propósito -- el candado M-1 debe valer
    tanto si el anuncio decide no dibujar nada en ese instante como después
    del salto, así que no hace falta avanzar el reloj aquí."""
    boss, _ = make_boss()
    _arrancar_transicion_real(boss)

    metodo = getattr(boss, "_draw_anuncio_del_enjambre", None)
    assert callable(metodo), (
        "falta _draw_anuncio_del_enjambre -- el candado M-1 exige que el "
        "anuncio nunca reutilice self._telegraph/self._telegraph_timer, pero "
        "sin el método nuevo no hay nada todavía que pueda violarlo")

    metodo(_superficie_de_prueba(), _offset_centrado(boss))

    assert boss._telegraph == "", (
        "_draw_anuncio_del_enjambre no debe tocar self._telegraph (candado M-1)")
    assert boss._telegraph_timer == 0.0, (
        "_draw_anuncio_del_enjambre no debe tocar self._telegraph_timer (candado M-1)")


# ──────────────────────────────────────────────
# 4 — progresa con self.transition_timer (crece/intensifica hacia el estallido)
# ──────────────────────────────────────────────

def test_el_anuncio_progresa_con_el_reloj_de_transicion():
    """Comparando dos puntos POST-salto contra a punto de cerrarse
    (``transition_timer`` bajo, cerca de 0) el anuncio debe leerse distinto
    -- crece o se intensifica según se acerca el estallido del enjambre, no
    un dibujo estático.

    Adaptación Cambio 5 (dictamen doc-guardian AMARILLO, orden del usuario
    2026-08-18): los dos puntos de comparación ya NO pueden ser 2.4 (recién
    abierta, todavía desvaneciéndose -- ver test 2) y 0.1, porque esa pareja
    ahora mediría "no se dibuja nada" vs "se dibuja algo", que es presencia,
    no progresión. Se avanza primero el reloj de verdad más allá del
    desvanecimiento (``_avanzar_tras_el_salto``, salto REAL, no fingido) y
    LUEGO se comparan dos ``transition_timer`` -- ambos ya dentro del tramo
    post-salto -- 1.5 (recién saltado) contra 0.1 (a punto de soltar el
    enjambre)."""
    boss, _ = make_boss()
    _arrancar_transicion_real(boss)
    _avanzar_tras_el_salto(boss)                 # salto real: ya en la posición final

    metodo = getattr(boss, "_draw_anuncio_del_enjambre", None)
    assert callable(metodo), "falta _draw_anuncio_del_enjambre"

    offset = _offset_centrado(boss)

    boss.transition_timer = 1.5                  # recién saltado, bien dentro del tramo post-salto
    recien_saltado = _superficie_de_prueba()
    metodo(recien_saltado, offset)

    boss.transition_timer = 0.1                  # a punto de cerrarse / soltar el enjambre
    a_punto_de_cerrar = _superficie_de_prueba()
    metodo(a_punto_de_cerrar, offset)

    assert pygame.image.tobytes(recien_saltado, "RGB") != pygame.image.tobytes(a_punto_de_cerrar, "RGB"), (
        "el anuncio no cambia con self.transition_timer -- debe crecer o "
        "intensificarse según se acerca el momento en que se suelta el enjambre")


# ──────────────────────────────────────────────
# 5 — nunca se dibuja fuera de transición
# ──────────────────────────────────────────────

def test_el_anuncio_no_se_dibuja_fuera_de_transicion():
    """Fuera de la ventana de quietud no hay ningún enjambre por anunciar:
    invocar el método nuevo sin ``is_transitioning`` no debe cambiar ni un
    píxel.

    Revisado para Cambio 5: no monta ninguna transición, así que no hay
    desvanecimiento que cruzar -- sin cambios."""
    boss, _ = make_boss()
    assert not boss.is_transitioning

    metodo = getattr(boss, "_draw_anuncio_del_enjambre", None)
    assert callable(metodo), "falta _draw_anuncio_del_enjambre"

    offset = _offset_centrado(boss)
    base = _superficie_de_prueba()
    tras_llamada = base.copy()
    metodo(tras_llamada, offset)

    assert pygame.image.tobytes(tras_llamada, "RGB") == pygame.image.tobytes(base, "RGB"), (
        "_draw_anuncio_del_enjambre pintó algo sin estar en transición de fase")


# ──────────────────────────────────────────────
# 6 — usa el color de aviso reconocible, no uno inventado
# ──────────────────────────────────────────────

def test_el_anuncio_usa_el_color_de_aviso():
    """Doc 86 §2.4 regla 5: el anuncio debe leerse como AVISO, no como
    decoración. Se acepta cualquiera de las dos decisiones de diseño
    razonables para la fase GREEN: una constante propia nueva
    (``_COLOR_ANUNCIO_ENJAMBRE``) o reutilizar directamente
    ``_TELEGRAPH_WARN_COLOR`` (el mismo tinte que ya comparten
    STOMP/CHARGE/VINE_SWEEP/VINE_TOSS/MUSHROOM_SPORE) -- por eso se lee con
    ``getattr`` en vez de fijar un solo nombre de constante.

    Adaptación Cambio 5 (dictamen doc-guardian AMARILLO, orden del usuario
    2026-08-18): se invoca DESPUÉS del salto real (``_avanzar_tras_el_salto``)
    en vez de en el fotograma 0 de apertura -- durante el desvanecimiento el
    método no debe pintar ningún píxel (ver test 2), así que buscar el color
    de aviso ahí sería un montaje roto, no una prueba del color."""
    boss, _ = make_boss()
    _arrancar_transicion_real(boss)
    _avanzar_tras_el_salto(boss)

    metodo = getattr(boss, "_draw_anuncio_del_enjambre", None)
    assert callable(metodo), "falta _draw_anuncio_del_enjambre"

    color_esperado = tuple(getattr(boss, "_COLOR_ANUNCIO_ENJAMBRE", boss._TELEGRAPH_WARN_COLOR))

    surface = _superficie_de_prueba()
    metodo(surface, _offset_centrado(boss))

    ancho, alto = surface.get_size()
    # tuple(...) primero y luego slice: pygame.Color admite indexado/slicing
    # propio y no vale la pena depender de qué tipo exacto devuelve -- un
    # tuple de 4 elementos (r, g, b, a) recortado a 3 es inequívoco en
    # cualquier versión de pygame-ce.
    contiene_color_de_aviso = any(
        tuple(surface.get_at((x, y)))[:3] == color_esperado
        for x in range(ancho) for y in range(alto)
    )
    assert contiene_color_de_aviso, (
        f"ningún píxel de la superficie es exactamente {color_esperado!r} "
        "(color de aviso) tras invocar _draw_anuncio_del_enjambre")
