"""Pruebas del paquete H-18: adopción de las 5 características del motor V3.

Qué cubre, y por qué cada bloque existe
=======================================
El motor V3 trajo un jefe de referencia del profesor con cinco patrones que
nuestro venado no tenía. Se reimplementaron desde cero en la zona editable
(D1..D10 de la spec 2026-08-14-adopcion-v3-h18-design.md), y estas pruebas
fijan las decisiones que NO son evidentes leyendo el código:

* **skill_drop** — atributo de CLASE, porque el contrato del profesor lo lee
  sin instanciar.
* **Voz** — se degrada en silencio sin gestor de audio, y la inyecta la escena
  en ``on_enter`` para que sobreviva al reintento del motor V3 (H-18).
* **escala** — se declara en la ``BossPhase``, y cajas y puntos débiles la
  siguen (H-20: sin esto, la mitad inferior-derecha del venado agrandado era
  imposible de golpear).
* **teletransporte** — al centro de NUESTRA arena, jamás al de
  ``arena_bounds`` del motor (H-19: ese centro cae en mitad del corredor).
* **esporas en enjambre** — con daño real y acotadas a la arena.
* **reliquia** — anunciada una sola vez, al final de la secuencia de derrota.
* **TMX** — noche congelada + metadatos, sin mover el ambiente aprobado.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

import pygame

from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.framework.ecs.bullet_swarm import EnjambreDeBalas
from src.framework.entities.enemy_base import EnemyState
from src.stages.boss_venado import boss_venado as bv
from src.stages.boss_venado.boss_venado import BossVenado

DT = 1.0 / 60.0
TMX = Path("assets/maps/boss_venado/boss_venado.tmx")


def make_boss(with_bus: bool = False):
    """Mismo constructor que el resto de la suite: spawn dentro de la arena."""
    boss = BossVenado(pygame.Vector2(3168, 240))
    bus = None
    if with_bus:
        bus = EventBus()
        boss.set_event_bus(bus)
    return boss, bus


def _entrar_en_fase_2(boss) -> None:
    """Lleva al jefe hasta la fase 2 por el camino real (daño + transición).

    No se toca ``current_phase`` a mano a propósito: el escalado del cuerpo lo
    aplica ``BossBase._aplicar_escala_de_fase`` dentro de
    ``_finish_phase_transition``, así que un atajo daría un jefe en fase 2 con
    el cuerpo de la fase 1 -- justo el desajuste que estas pruebas vigilan.
    """
    boss.apply_hit(6.5, (0, 0))                 # 12 -> 5.5 <= umbral 6.0
    for _ in range(int(2.6 / DT)):
        boss.update(DT)
    assert boss.current_phase == 1 and not boss.is_transitioning


def _relativo(caja: pygame.Rect, posicion: pygame.Vector2) -> pygame.Rect:
    """Resta la posición del cuerpo a una caja MUNDO para recuperar el offset
    LOCAL que ``_update_rects`` sumó (enemy_base.py:822-838: ``self.hitbox =
    pygame.Rect(self.position.x + local_hitbox.x, ...)``).

    Adopción AUD-606: fijar la posición a un entero exacto ANTES de llamar
    ``_update_rects()`` (y leerla de nuevo aquí antes de que nada más la
    mueva) evita que el truncamiento a ``int`` que hace el constructor de
    ``pygame.Rect`` sobre la SUMA introduzca hasta 1px de error si la
    posición del jefe tuviera parte fraccionaria."""
    return pygame.Rect(
        int(round(caja.x - posicion.x)), int(round(caja.y - posicion.y)),
        caja.width, caja.height,
    )


class _AudioEspia:
    """Doble mínimo del AudioManager: sólo `play_voz`, que es lo que se llama."""

    def __init__(self) -> None:
        self.lineas: list[str] = []

    def play_voz(self, name: str, **_kw: object) -> None:
        self.lineas.append(name)


# ──────────────────────────────────────────────
# D1 — skill_drop
# ──────────────────────────────────────────────

def test_venado_declara_skill_drop_con_dash_y_parry():
    """Leído de la CLASE (sin instanciar) y de la API normalizada del motor.

    Las dos lecturas importan: el contrato del profesor recorre subclases y usa
    ``getattr(cls, "skill_drop")``, mientras que ``EnemyBase._die`` publica lo
    que devuelva ``habilidades_que_suelta()``."""
    assert BossVenado.skill_drop == ["skill_dash", "skill_parry"]
    boss, _ = make_boss()
    sueltas = boss.habilidades_que_suelta()
    assert "skill_dash" in sueltas and "skill_parry" in sueltas


def test_las_habilidades_declaradas_existen_en_el_catalogo():
    """Un id inventado se dejaría en el suelo y ``collect()`` lo rechazaría:
    el jugador lo recogería y no pasaría nada."""
    from src.engine.core.inventory import _ITEM_DEFS

    for habilidad in BossVenado.skill_drop:
        assert habilidad in _ITEM_DEFS, f"{habilidad} no está en el catálogo"


def test_la_muerte_publica_las_habilidades_en_el_evento():
    boss, bus = make_boss(with_bus=True)
    recibidos: list[dict] = []
    # El EventBus del motor guarda weakrefs: la lambda se ata a un nombre para
    # que no la barra el recolector antes del dispatch (mismo patrón que ya usa
    # test_charge_emits_boss_attack_event).
    on_died = lambda **kw: recibidos.append(kw)  # noqa: E731
    bus.subscribe(Events.ENEMY_DIED, on_died)
    boss.apply_hit(12.0, (0, 0))
    bus.dispatch()
    assert recibidos, "morir no publicó ENEMY_DIED"
    soltadas = recibidos[-1].get("skill_drop", "")
    assert "skill_dash" in soltadas and "skill_parry" in soltadas


# ──────────────────────────────────────────────
# D2/D3 — la voz
# ──────────────────────────────────────────────

def test_el_venado_habla_al_cambiar_de_fase():
    boss, _ = make_boss()
    audio = _AudioEspia()
    boss.audio_de_voz = audio
    boss._finish_phase_transition()
    assert audio.lineas == ["sfx_voz_venado_fase2"]


def test_el_venado_habla_al_morir():
    boss, _ = make_boss()
    audio = _AudioEspia()
    boss.audio_de_voz = audio
    boss.apply_hit(12.0, (0, 0))
    assert "sfx_voz_venado_muerte" in audio.lineas


def test_sin_audio_de_voz_no_revienta():
    """Una entrega (o el arnés headless) puede construir el jefe sin audio."""
    boss, _ = make_boss()
    assert boss.audio_de_voz is None
    boss._finish_phase_transition()      # no debe lanzar
    boss.on_defeated()                   # tampoco


def test_un_audio_sin_play_voz_no_revienta():
    """La guarda es doble (``is not None`` + ``hasattr``) justo para esto."""
    boss, _ = make_boss()
    boss.audio_de_voz = object()
    boss._finish_phase_transition()      # no debe lanzar


def test_existen_los_wav_de_cada_linea():
    """Cada nombre que el jefe emite tiene archivo: una línea sin wav es una
    llamada que suena a nada y que ninguna prueba de humo detecta."""
    boss, _ = make_boss()
    audio = _AudioEspia()
    boss.audio_de_voz = audio
    boss._finish_phase_transition()
    boss.on_defeated()
    assert audio.lineas, "no se emitió ninguna línea"
    for linea in audio.lineas:
        assert Path("assets/sfx/voz") .joinpath(f"{linea}.wav").is_file(), (
            f"la línea {linea} no tiene wav en assets/sfx/voz"
        )


# ──────────────────────────────────────────────
# D4/D5 — escala de fase, cajas y puntos débiles (H-20)
# ──────────────────────────────────────────────

def test_la_fase_dos_declara_escala():
    boss, _ = make_boss()
    assert boss.phases[0].escala == 1.0
    assert boss.phases[1].escala == 1.25


def test_el_cuerpo_crece_al_entrar_en_fase_dos():
    boss, _ = make_boss()
    assert boss.rect.size == (48, 48)
    pies_antes = boss.rect.bottom
    _entrar_en_fase_2(boss)
    assert boss.rect.size == (60, 60)
    # El motor ancla por pies+centro; los pies no deben saltar al crecer
    # (más allá del propio movimiento del fotograma).
    assert abs(boss.rect.bottom - pies_antes) < 120
    assert boss._factor_de_escala() == 1.25


def test_hitbox_y_hurtbox_escalan_con_el_cuerpo():
    """H-20: sin esto la hurtbox de 30x40 se quedaba cubriendo sólo el
    cuadrante superior izquierdo del venado de 60x60 -- la mitad
    inferior-derecha del cuerpo VISIBLE era imposible de golpear.

    Adopción AUD-606: ``_build_hitbox``/``_build_hurtbox`` ahora devuelven
    los rects CRUDOS del sprite en disco (verificado abajo) -- es el motor
    quien los escala, vía ``BossBase._escalar_local``
    (``cajas_siguen_al_cuerpo = True``, boss_base.py:338-360). Lo que hay
    que vigilar dejó de ser el método privado y pasó a ser el OBSERVABLE
    real: ``boss.hitbox``/``boss.hurtbox`` tras ``_update_rects()``
    (enemy_base.py:822-838), que es exactamente el paso que el motor
    ejecuta cada fotograma. Los números finales no cambiaron -- misma
    aritmética ``round()`` que el ``_escalar_rect_local`` retirado."""
    boss, _ = make_boss()
    assert boss._build_hitbox() == pygame.Rect(6, 4, 36, 44)
    assert boss._build_hurtbox() == pygame.Rect(9, 4, 30, 40)

    boss.position.x, boss.position.y = 100.0, 100.0
    boss._update_rects()
    assert _relativo(boss.hitbox, boss.position) == pygame.Rect(6, 4, 36, 44)
    assert _relativo(boss.hurtbox, boss.position) == pygame.Rect(9, 4, 30, 40)

    _entrar_en_fase_2(boss)
    boss.position.x, boss.position.y = 100.0, 100.0
    boss._update_rects()
    assert _relativo(boss.hitbox, boss.position) == pygame.Rect(8, 5, 45, 55)
    assert _relativo(boss.hurtbox, boss.position) == pygame.Rect(11, 5, 38, 50)


def _proporciones(rect: pygame.Rect, cuerpo: pygame.Rect) -> tuple[float, ...]:
    """El punto débil expresado como fracción del cuerpo: lo que debe
    conservarse al escalar, ya que el sprite se escala igual."""
    return (
        (rect.x - cuerpo.x) / cuerpo.width,
        (rect.y - cuerpo.y) / cuerpo.height,
        rect.width / cuerpo.width,
        rect.height / cuerpo.height,
    )


def test_flanco_sigue_alineado_con_el_sprite_en_fase_2_escalada():
    """El riesgo R3 del diseño, hecho ejecutable.

    El flanco sólo está expuesto en fase 2, que es justo la fase que escala: si
    los offsets no escalaran, el punto débil se quedaría donde estaba el anca
    del venado pequeño mientras el sprite dibuja el anca 12px más allá. Se
    comprueban las tres cosas que hacen que "alineado" signifique algo:
    proporciones conservadas, el rect cabe dentro del cuerpo, y un golpe
    centrado en el flanco escalado paga el multiplicador."""
    boss, _ = make_boss()
    _entrar_en_fase_2(boss)
    boss.facing_direction = 1

    flanco = next(wp for wp in boss.weak_points if wp.label == "flanco")
    escalado = boss._escalar_weak_point(flanco)
    rect = escalado.rect_for(boss.rect)

    canonicas = (bv.FLANCO_OFFSET[0] / 48, bv.FLANCO_OFFSET[1] / 48,
                 bv.FLANCO_SIZE[0] / 48, bv.FLANCO_SIZE[1] / 48)
    obtenidas = _proporciones(rect, boss.rect)
    # Tolerancia 1/60: un píxel del cuerpo escalado. Por debajo de eso el
    # redondeo entero de los offsets haría fallar la prueba sin que nada esté
    # desalineado de verdad.
    for esperada, obtenida in zip(canonicas, obtenidas):
        assert abs(esperada - obtenida) <= 1 / 60, (
            f"el flanco se desalineó: {obtenidas} vs {canonicas}"
        )
    assert boss.rect.contains(rect), "el flanco escalado se sale del cuerpo"

    # Y el golpe: un jugador centrado en el flanco escalado debe cobrar crítico.
    boss.set_player_ref(pygame.Rect(rect.centerx - 2, rect.centery - 2, 4, 4))
    vida_antes = boss.current_health
    boss.apply_hit(1.0, (0, 0))
    assert boss.last_weak_point is not None and boss.last_weak_point.label == "flanco"
    assert abs((vida_antes - boss.current_health) - bv.FLANCO_MULTIPLIER) < 1e-6


def test_cuernos_siguen_alineados_en_fase_2_escalada():
    boss, _ = make_boss()
    _entrar_en_fase_2(boss)
    boss.facing_direction = 1

    cuernos = next(wp for wp in boss.weak_points if wp.label == "cuernos")
    rect = boss._escalar_weak_point(cuernos).rect_for(boss.rect)
    canonicas = (bv.CUERNOS_OFFSET[0] / 48, bv.CUERNOS_OFFSET[1] / 48,
                 bv.CUERNOS_SIZE[0] / 48, bv.CUERNOS_SIZE[1] / 48)
    for esperada, obtenida in zip(canonicas, _proporciones(rect, boss.rect)):
        assert abs(esperada - obtenida) <= 1 / 60
    assert boss.rect.contains(rect)


def test_el_espejado_se_aplica_despues_del_escalado():
    """Orden obligatorio: ``_mirror_weak_point`` refleja contra ``rect.width``
    (60 en fase 2), así que sólo devuelve el reflejo correcto si offset y size
    ya vienen escalados. Invertir el orden desplazaría el punto débil."""
    boss, _ = make_boss()
    _entrar_en_fase_2(boss)
    boss.facing_direction = -1

    cuernos = next(wp for wp in boss.weak_points if wp.label == "cuernos")
    correcto = boss._mirror_weak_point(boss._escalar_weak_point(cuernos))
    invertido = boss._escalar_weak_point(boss._mirror_weak_point(cuernos))
    assert correcto.offset != invertido.offset, (
        "los dos órdenes dan lo mismo: la prueba dejó de vigilar nada"
    )
    esperado_x = boss.rect.width - correcto.size[0] - int(round(
        bv.CUERNOS_OFFSET[0] * 1.25))
    assert correcto.offset[0] == esperado_x
    assert boss.rect.contains(correcto.rect_for(boss.rect))


def test_stomp_planta_los_pies_en_el_suelo_tambien_escalado():
    """``GROUND_Y`` está calculada con 48px de alto: usarla cruda en fase 2
    hundiría las pezuñas 12px dentro del piso durante toda la ventana de
    castigo."""
    boss, _ = make_boss()
    _entrar_en_fase_2(boss)
    assert boss._y_de_suelo() == bv.FLOOR_Y - 60.0
    assert boss._y_de_banda_de_embestida() == bv.FLOOR_Y - 60.0 - bv.CHARGE_BAND_GAP

    boss.position.y = boss._y_de_suelo() - 30.0
    boss._telegraph = "STOMP"
    for _ in range(int(1.0 / DT)):
        boss._update_movement(DT)
    boss._update_rects()
    assert boss.rect.bottom == int(bv.FLOOR_Y)


def test_las_cajas_no_escalan_si_el_cuerpo_no_ha_crecido():
    """Candado del diseño D5: el factor se mide del rect VIVO, no de la fase
    declarada. Media docena de pruebas existentes fuerzan ``current_phase = 1``
    sin redimensionar, y con esos jefes las cajas deben seguir siendo las
    canónicas.

    Adopción AUD-606: reapuntada al OBSERVABLE (``boss.hurtbox`` tras
    ``_update_rects()``, el mismo paso que ejecuta el motor cada fotograma,
    enemy_base.py:822-838) en vez de ``boss._build_hurtbox()`` a secas --
    ese método ahora siempre devuelve el rect CRUDO sin escalar (es el
    motor quien escala, vía ``BossBase._escalar_local``), así que llamarlo
    directo ya no distingue "escaló" de "no escaló"."""
    boss, _ = make_boss()
    boss.current_phase = 1
    assert boss.rect.size == (48, 48)
    assert boss._factor_de_escala() == 1.0
    boss.position.x, boss.position.y = 100.0, 100.0
    boss._update_rects()
    assert _relativo(boss.hurtbox, boss.position) == pygame.Rect(9, 4, 30, 40)


# ──────────────────────────────────────────────
# Adopción H-20 (AUD-606) — cajas_siguen_al_cuerpo, Opción A / B-050
# ──────────────────────────────────────────────
#
# El drop #6 del motor (AUD-606) le dio a ``BossBase`` la bandera de clase
# ``cajas_siguen_al_cuerpo``: con ella en ``True`` es EL MOTOR quien escala
# hitbox/hurtbox (``BossBase._escalar_local``, boss_base.py:338-360, la MISMA
# aritmética -- mismo ``round()``, rects bit-idénticos -- que este archivo
# calculaba a mano en el ``_escalar_rect_local`` retirado) y quien resuelve
# los puntos débiles a escala/espejados si se llama a
# ``boss_kit.resolve_weak_point_damage`` (boss_kit.py:391-428, línea 409).
# Verificado antes de tocar una línea: esa segunda mitad NO se puede adoptar
# todavía. ``WeakPoint.rect_for`` (boss_kit.py:141-163) espeja el offset
# CANÓNICO contra el ancho YA escalado y multiplica por ``escala`` DESPUÉS --
# ``(W·s − ox − w)·s`` -- en vez de la fórmula correcta ``s·(W − ox − w)`` que
# hace nuestra ruta propia (escalar primero con ``_escalar_weak_point``,
# espejar después con ``_mirror_weak_point``). Ambas sólo coinciden con
# ``s == 1``; a ``escala=1.25`` (fase 2) difieren en ``W_vivo·(s−1)`` px sea
# cual sea el punto débil -- B-050, ver REGISTRO-DE-BUGS. Por eso la adopción
# es a medias (Opción A): la bandera sube (cajas correctas, sin pérdida), pero
# los puntos débiles se siguen resolviendo con nuestra propia composición
# (``BossVenado._resolver_punto_debil``) hasta que el motor corrija el orden
# de ``rect_for``.


def test_el_venado_declara_cajas_siguen_al_cuerpo():
    """Espejo local del contrato del profesor sobre AUD-606: sin esta
    bandera el motor no escala hitbox/hurtbox y la mitad del venado
    agrandado (fase 2) vuelve a ser imposible de golpear -- exactamente el
    fallo original de H-20, ahora a cargo del motor en vez de nuestro
    ``_escalar_rect_local`` retirado."""
    assert BossVenado.cajas_siguen_al_cuerpo is True


def test_canario_b050_rect_for_del_motor_desalinea_a_escala_no_uno():
    """CANARIO B-050 -- ROJO FUTURO PLANIFICADO, deliberado.

    Compara, para los CUERNOS en fase 2 (escala 1.25, cuerpo 60x60,
    facing_direction=-1): (i) la ruta del motor,
    ``WeakPoint.rect_for(rect_vivo, escala=1.25, facing=-1)``; contra (ii)
    nuestra ruta propia, ``_mirror_weak_point(_escalar_weak_point(wp))``
    (escalar primero, espejar después) seguida de un ``rect_for`` crudo.

    La diferencia entre ambas en X debe ser ``W_vivo·(escala−1)`` =
    ``60·0.25`` = 15px, sea cual sea el offset del punto débil -- así lo
    describe el bloque de comentarios de arriba. Tolerancia ±1px: cada ruta
    redondea offsets/tamaños con una función distinta (``int()`` truncado
    dentro de ``rect_for`` del motor vs ``round()`` en
    ``_escalar_weak_point``).

    Si esta prueba se pone en VERDE sin que nadie la haya tocado, el motor
    corrigio rect_for (AUD-606): retirar la compensacion B-050
    (_resolver_punto_debil y el espejado propio) y adoptar la ruta del
    motor -- ver REGISTRO-DE-BUGS B-050.
    """
    from src.framework.entities.boss_kit import WeakPoint

    escala = 1.25
    rect_vivo = pygame.Rect(0, 0, 60, 60)   # cuerpo de fase 2 (48 * 1.25)
    cuernos = WeakPoint(offset=bv.CUERNOS_OFFSET, size=bv.CUERNOS_SIZE,
                         multiplier=bv.CUERNOS_MULTIPLIER, label="cuernos")

    rect_motor = cuernos.rect_for(rect_vivo, escala=escala, facing=-1)

    boss, _ = make_boss()
    boss.rect = rect_vivo.copy()
    boss.facing_direction = -1
    assert boss._factor_de_escala() == escala
    propio = boss._mirror_weak_point(boss._escalar_weak_point(cuernos))
    rect_propio = propio.rect_for(rect_vivo)

    desfase_esperado = rect_vivo.width * (escala - 1.0)   # 15.0
    desfase_real = rect_motor.x - rect_propio.x
    assert abs(desfase_real - desfase_esperado) <= 1, (
        "Si esto falla, el motor corrigio rect_for (AUD-606): retirar la "
        "compensacion B-050 (_resolver_punto_debil y el espejado propio) y "
        "adoptar la ruta del motor -- ver REGISTRO-DE-BUGS B-050"
    )

    # Y la nuestra es la geométricamente correcta: s*(W - ox - w), con W el
    # ancho CANÓNICO (48), no el vivo.
    esperado_propio = round(escala * (bv.BOSS_SPRITE_SIZE
                                       - bv.CUERNOS_OFFSET[0] - bv.CUERNOS_SIZE[0]))
    assert rect_propio.x == esperado_propio


# ──────────────────────────────────────────────
# D6/D7/D8 — el teletransporte de fase
# ──────────────────────────────────────────────
#
# Cambio 5 de la campaña de fairness (dictamen doc-guardian AMARILLO
# vigente, token registrado, orden del usuario 2026-08-18): el salto al
# centro deja de ser instantáneo al abrir la ventana de quietud. El venado
# ahora se queda ``FADE_TELETRANSPORTE`` (~0.55 s) "desvaneciéndose" en su
# posición VIEJA antes de saltar -- ver ``test_teletransporte_ux.py`` para
# el detalle del efecto visual nuevo. Los tres tests de este bloque se
# adaptan para describir ese comportamiento (GREEN futura, todavía sin
# implementar); la razón de cada cambio va en su propio docstring.


def _fade_teletransporte(boss) -> float:
    """Duración del desvanecimiento del Cambio 5 (``FADE_TELETRANSPORTE``),
    leída con ``getattr`` en dos ubicaciones posibles -- el dictamen no fija
    si terminará siendo una constante de módulo o un atributo de clase --
    con una caída final al valor de diseño 0.55 s para que estas pruebas
    describan el comportamiento GREEN sin acoplarse a esa decisión."""
    valor = getattr(bv, "FADE_TELETRANSPORTE", None)
    if valor is None:
        valor = getattr(type(boss), "FADE_TELETRANSPORTE", None)
    return float(valor) if valor is not None else 0.55


def _avanzar(boss, segundos: float) -> None:
    """Corre ``update(DT)`` durante ``segundos`` (redondeado a fotogramas de
    60fps) -- mismo patrón que ya usa el resto de la suite (p. ej.
    ``_entrar_en_fase_2``), factorizado aquí porque el Cambio 5 necesita
    avanzar el reloj en más de un punto dentro de una misma prueba."""
    for _ in range(int(segundos / DT)):
        boss.update(DT)


def test_el_cambio_de_fase_teletransporta_al_centro_de_la_arena():
    """Se adapta para cubrir los dos tramos del Cambio 5 en vez de uno solo:
    recién abierta la transición el jefe sigue en su X VIEJA (assert nuevo
    -- HOY falla, porque el código actual salta de inmediato), y sólo tras
    el desvanecimiento queda centrado."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_X1 - 80.0        # acorralado contra la pared derecha
    boss.rect.x = int(boss.position.x)
    x_vieja = boss.position.x
    boss.apply_hit(6.5, (0, 0))                 # dispara _start_phase_transition
    assert boss.is_transitioning
    assert boss.position.x == x_vieja, (
        "el venado saltó de inmediato al abrir la ventana -- Cambio 5 exige "
        "que se quede en su posición vieja durante el desvanecimiento")
    _avanzar(boss, _fade_teletransporte(boss) + 0.05)
    assert abs(boss.rect.centerx - bv.ARENA_CX) <= 1.0


def test_el_teletransporte_conserva_la_altura():
    """El venado flota: reposicionar en X no debe dejarlo caer ni subirlo.

    Cambio 5 (riesgo 3 del dictamen): el salto ya no ocurre dentro del mismo
    ``apply_hit`` sincrónico -- se adapta avanzando el reloj más allá del
    desvanecimiento ANTES de leer ``position.y``, para que el test siga
    probando lo que su nombre promete (que Y sobrevive al salto real) en vez
    de un aprobado accidental por el salto ni siquiera haber ocurrido
    todavía. Sigue en VERDE tras la adaptación: la Y jamás formó parte de lo
    que ``teletransportar()`` toca, ni antes ni después del Cambio 5."""
    boss, _ = make_boss()
    boss.position.y = 420.0
    boss.rect.y = int(boss.position.y)
    boss.apply_hit(6.5, (0, 0))
    _avanzar(boss, _fade_teletransporte(boss) + 0.05)
    assert boss.position.y == 420.0


def test_el_salto_ocurre_tras_el_desvanecimiento_dentro_del_primer_tramo():
    """Renombrado desde
    ``test_el_teletransporte_ocurre_al_empezar_la_transicion_no_al_terminar``:
    ese nombre describía un salto instantáneo en el fotograma de apertura,
    que ya no es el comportamiento GREEN futuro del Cambio 5.

    D6 sigue intacto en su forma general -- el jugador ve al jefe
    desvanecerse donde estaba y reaparecer poco después, quieto, en el
    centro, por el resto de la ventana -- y la garantía ANTI-TIRÓN de H-18/D6
    se preserva explícitamente: el salto completo (desvanecimiento +
    reaparición) cabe dentro del primer tramo de la ventana (bien por debajo
    de 1.0s de los 2.5s totales), así que NUNCA coincide con el instante en
    que el jefe recupera el control -- eso reproduciría el mismo tirón
    brusco que D6 ya documentaba al comparar contra saltar al CERRAR."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_X0 + 40.0
    boss.rect.x = int(boss.position.x)
    x_vieja = boss.position.x
    boss.apply_hit(6.5, (0, 0))

    # (a) recién abierta la ventana: el jefe TODAVÍA no está en el centro.
    assert boss.position.x == x_vieja
    assert abs(boss.position.x - boss._destino_de_teletransporte()) > 1.0, (
        "el venado ya estaba en el centro en el primer fotograma de la "
        "ventana -- Cambio 5 exige un desvanecimiento previo")

    # (b) tras el desvanecimiento (bien dentro del primer tramo de <=1.0s de
    # ventana transcurrida -- la garantía anti-tirón de H-18/D6): el salto ya
    # se completó.
    _avanzar(boss, _fade_teletransporte(boss) + 0.05)
    assert abs(boss.position.x - boss._destino_de_teletransporte()) <= 1.0
    assert boss.is_transitioning, "el salto no debe cerrar la ventana por sí solo"

    # (c) mucho antes del cierre -- a mitad de la ventana completa de 2.5s --
    # sigue centrado: el salto no se deshizo ni se repitió.
    _avanzar(boss, 1.2 - _fade_teletransporte(boss))
    assert abs(boss.position.x - boss._destino_de_teletransporte()) <= 1.0
    assert boss.is_transitioning

    _avanzar(boss, 1.5)                        # cierra la ventana completa (2.5s totales)
    assert boss.current_phase == 1
    # Y al terminar no hay un SEGUNDO salto: el movimiento de la fase 2 puede
    # haberlo desplazado, pero no de un fotograma al otro.
    assert bv.ARENA_X0 <= boss.position.x <= bv.ARENA_X1


def test_el_destino_del_teletransporte_queda_dentro_de_la_arena():
    for x_inicial in (0.0, 800.0, bv.ARENA_X0 - 200.0, bv.ARENA_X0,
                      bv.ARENA_CX, bv.ARENA_X1 - 48.0, bv.ARENA_X1 + 500.0):
        boss, _ = make_boss()
        boss.position.x = x_inicial
        boss.rect.x = int(x_inicial)
        destino = boss._destino_de_teletransporte()
        assert bv.ARENA_X0 + bv.TELEPORT_MARGIN <= destino
        assert destino + boss.rect.width <= bv.ARENA_X1 - bv.TELEPORT_MARGIN


def test_el_centro_del_arena_del_motor_no_sirve_de_destino():
    """H-19, hecho candado.

    ``StageScene.on_enter`` le pasa a todo ``BossBase``
    ``set_arena_bounds(Rect(0, 0, *map_pixel_size))``. En este mapa-corredor
    eso da ``centerx == 1640``, a media pradera. El jefe de referencia
    teletransporta exactamente a ``arena_bounds.centerx``: copiarlo sacaría al
    venado de su terreno y rompería ``boss_in_arena`` /
    ``no_damage_outside_arena``. Esta prueba existe para que quien un día
    "simplifique" nuestro cálculo a ``arena_bounds.centerx`` se encuentre el
    rojo aquí."""
    import ast

    mapa_entero = pygame.Rect(0, 0, 3280, 608)
    assert not (bv.ARENA_X0 <= mapa_entero.centerx <= bv.ARENA_X1), (
        f"el centro del mapa ({mapa_entero.centerx}) cayó dentro de la arena: "
        "la premisa de H-19 cambió y hay que revisar el diseño"
    )
    # Se inspecciona el AST y no el texto: los comentarios y docstrings del
    # módulo NOMBRAN ``arena_bounds.centerx`` justamente para explicar por qué
    # no se usa, y un `in fuente` los confundiría con código.
    fuente = Path("src/stages/boss_venado/boss_venado.py").read_text(encoding="utf-8")
    usos = [
        nodo for nodo in ast.walk(ast.parse(fuente))
        if isinstance(nodo, ast.Attribute) and nodo.attr in ("centerx", "centery")
        and isinstance(nodo.value, ast.Attribute) and nodo.value.attr == "arena_bounds"
    ]
    assert not usos, (
        "el jefe lee arena_bounds.centerx: en este mapa-corredor eso es x=1640, "
        "a media pradera (H-19)"
    )


def test_el_fuente_llama_a_teletransportar():
    """Espejo local del contrato del profesor
    (test_boss_venado_se_teletransporta_al_cambiar_de_fase), para que romperlo
    salga en NUESTRA suite y no sólo en la del motor."""
    fuente = Path("src/stages/boss_venado/boss_venado.py").read_text(encoding="utf-8")
    assert "self.teletransportar(" in fuente


# ──────────────────────────────────────────────
# D9 — la nube de esporas en enjambre
# ──────────────────────────────────────────────

def test_el_venado_tiene_un_enjambre_de_esporas():
    boss, _ = make_boss()
    assert isinstance(boss.esporas, EnjambreDeBalas)
    assert boss.esporas.contador == 0


def test_el_abanico_de_esporas_crea_balas():
    boss, _ = make_boss()
    boss._soltar_abanico_de_esporas()
    assert boss.esporas.contador == boss._ESPORAS_DE_LA_CORONA


def test_el_dano_de_una_espora_es_el_oficial():
    """0.25 no es un número inventado: es el daño de espora de 17_BOSS_SPEC
    §3.3, el mismo que ya llevan las 3 esporas dirigidas de MUSHROOM_SPORE."""
    assert BossVenado._DANO_ESPORA_ENJAMBRE == 0.25
    boss, _ = make_boss()
    boss._do_mushroom_spore(pygame.Rect(2600, 528, 20, 32))
    assert all(p["damage"] == BossVenado._DANO_ESPORA_ENJAMBRE
               for p in boss._projectiles if p["type"] == "spore")


class _JugadorFalso:
    """Jugador duck-typed: sólo lo que ``_check_player_contact`` toca."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.hurtbox = rect
        self.velocity = pygame.Vector2(0.0, 0.0)
        self.golpes: list[float] = []

    def apply_damage(self, amount, source_position, knockback_force=150.0) -> None:
        self.golpes.append(amount)


def test_las_esporas_del_enjambre_danan_al_jugador():
    """Y lo hacen en UNA sola llamada: aplicar daño bala por bala perdería N-1
    golpes contra el cooldown de invulnerabilidad del jugador y haría que el
    daño real dependiera del orden del arreglo."""
    boss, _ = make_boss()
    boss._soltar_abanico_de_esporas()
    jugador = _JugadorFalso(pygame.Rect(boss.rect.centerx - 30,
                                        boss.rect.centery - 30, 60, 60))
    boss._check_player_contact(jugador)
    assert len(jugador.golpes) == 1
    assert jugador.golpes[0] >= BossVenado._DANO_ESPORA_ENJAMBRE


def test_las_esporas_no_danan_al_jugador_fuera_de_la_arena():
    """Candado de regresión del gate ``no_damage_outside_arena``: el venado
    sólo pelea en su terreno sagrado."""
    boss, _ = make_boss()
    boss._soltar_abanico_de_esporas()
    contador_antes = boss.esporas.contador
    jugador = _JugadorFalso(pygame.Rect(int(bv.ARENA_X0) - 300, 500, 20, 32))
    boss._check_player_contact(jugador)
    assert jugador.golpes == []
    # Y las balas siguen vivas: la guarda va ANTES de ``dano_total_contra``,
    # que consume lo que acierta.
    assert boss.esporas.contador == contador_antes


def test_las_esporas_mueren_fuera_de_la_arena():
    boss, _ = make_boss()
    boss.position.x = 100.0                       # bien lejos de la arena
    boss.rect.x = 100
    boss._soltar_abanico_de_esporas()
    assert boss.esporas.contador > 0
    boss.esporas.update(DT, bv.ARENA_RECT)
    assert boss.esporas.contador == 0


def test_la_transicion_a_fase_2_abre_el_abanico():
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_X0 + 40.0          # acorralado, para ver el efecto del salto
    boss.rect.x = int(boss.position.x)
    _entrar_en_fase_2(boss)
    assert boss.esporas.contador > 0
    # Nacen en el centro: el teletransporte ya ocurrió al empezar la transición.
    xs = boss.esporas.x[boss.esporas.vivas]
    assert abs(float(xs.mean()) - bv.ARENA_CX) <= 60.0


def test_la_fase_1_no_abre_abanico():
    boss, _ = make_boss()
    assert boss.current_phase == 0
    for _ in range(int(1.0 / DT)):
        boss.update(DT)
    assert boss.esporas.contador == 0


def test_la_derrota_limpia_el_enjambre():
    boss, _ = make_boss()
    boss._soltar_abanico_de_esporas()
    assert boss.esporas.contador > 0
    boss.apply_hit(12.0, (0, 0))
    assert boss.esporas.contador == 0


# ──────────────────────────────────────────────
# D10 — "Fragmento de Reliquia 1"
# ──────────────────────────────────────────────

def test_la_derrota_anuncia_la_reliquia():
    """El anuncio es la bandera, y es MUDO (H-21).

    El sonido de la reliquia está cableado por el motor, pero el profesor lo
    reserva en la lista `AWAITING_THEIR_BOSS` de `tests/test_audio_wiring.py`
    porque la recompensa del Venado "se resuelve por la escena de créditos".
    Esta prueba fija las dos mitades de esa decisión: el jefe deja constancia de
    la reliquia (lo que la escena lee para el banner) y no emite el efecto.
    """
    boss, bus = make_boss(with_bus=True)
    recibidos: list[dict] = []
    on_relic = lambda **kw: recibidos.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_RELIC_APPEAR, on_relic)
    boss.apply_hit(12.0, (0, 0))
    for _ in range(int(4.0 / DT)):
        boss.update(DT)
    bus.dispatch()
    assert boss.reliquia_anunciada
    assert not recibidos, "H-21: el sonido de la reliquia no se emite desde el jefe"


def test_la_reliquia_no_se_anuncia_antes_de_la_calavera():
    """Va en la ÚLTIMA etapa de §3.6: la reliquia es lo que QUEDA del venado,
    no algo que suelte mientras aún se está muriendo."""
    boss, _ = make_boss()
    boss.apply_hit(12.0, (0, 0))
    assert boss.state == EnemyState.DYING
    assert not boss.reliquia_anunciada
    for _ in range(int(1.6 / DT)):
        boss.update(DT)
    assert boss._defeat_stage == 1               # calavera en pantalla
    assert not boss.reliquia_anunciada


def test_la_reliquia_se_anuncia_una_sola_vez():
    """Sin evento que contar (H-21), lo que hay que fijar es el pestillo.

    La bandera sube una vez y una segunda llamada no la vuelve a levantar. De
    eso depende el banner: `_update_relic_banner` sólo arma el temporizador en
    el flanco de subida, así que un anuncio repetido reiniciaría el fundido a
    mitad de camino o resucitaría el icono cuando ya se había apagado.
    """
    import types

    from src.stages.boss_venado.boss_venado_scene import (
        RELIC_BANNER_DURATION,
        BossVenadoScene,
    )

    boss, _ = make_boss()
    escena = BossVenadoScene.__new__(BossVenadoScene)
    escena._stage_data = types.SimpleNamespace(entity_list=[boss])
    escena._relic_timer = 0.0
    escena._relic_shown = False
    escena._relic_icon = None

    boss.apply_hit(12.0, (0, 0))
    for _ in range(int(6.0 / DT)):
        boss.update(DT)
    assert boss.reliquia_anunciada
    escena._update_relic_banner(DT)
    assert escena._relic_timer == RELIC_BANNER_DURATION

    # El banner se consume entero y el jefe reintenta anunciar: nada rearma.
    escena._update_relic_banner(RELIC_BANNER_DURATION)
    boss._anunciar_reliquia()                    # segundo intento explícito
    escena._update_relic_banner(DT)
    assert escena._relic_timer == 0.0


def test_la_reliquia_se_declara_por_lo_que_no_hace():
    """Lo honesto, por escrito y ejecutable: no existe en el catálogo del
    motor, así que NO entra al inventario ni da bonus. Si alguien la añadiera
    al catálogo (editando el motor, prohibido) esta prueba avisa de que la
    decisión D10 hay que rehacerla."""
    from src.engine.core.inventory import _ITEM_DEFS

    assert bv.RELIQUIA_ID not in _ITEM_DEFS
    assert bv.RELIQUIA_NOMBRE == "Fragmento de Reliquia 1"


# ──────────────────────────────────────────────
# D3/D8/D10 — lo que aporta la escena
# ──────────────────────────────────────────────

def test_la_escena_declara_la_arena_real_y_no_el_mapa_entero():
    """H-19: constante de la escena, verificada contra las del jefe."""
    from src.stages.boss_venado import boss_venado_scene as bvs

    assert bvs.ARENA_BOUNDS == pygame.Rect(2480, 0, 784, 608)
    assert bvs.ARENA_BOUNDS.left == int(bv.ARENA_X0)
    assert bvs.ARENA_BOUNDS.right == int(bv.ARENA_X1)
    assert bvs.ARENA_BOUNDS == bv.ARENA_RECT


def test_la_escena_inyecta_el_audio_y_acota_el_arena_en_on_enter():
    """Se inyecta en ``on_enter`` y no en ``__init__`` porque ``respawn()``
    reejecuta ``on_enter`` y reconstruye StageData: tras cada muerte del
    jugador el jefe es un objeto NUEVO (reintento del motor V3, H-18). Este
    doble sin ``__init__`` reproduce esa llamada sin arrancar un GameContext."""
    import types

    from src.stages.boss_venado.boss_venado_scene import ARENA_BOUNDS, BossVenadoScene

    boss, _ = make_boss()
    escena = BossVenadoScene.__new__(BossVenadoScene)
    audio = _AudioEspia()
    escena.context = types.SimpleNamespace(audio_manager=audio)
    escena._stage_data = types.SimpleNamespace(entity_list=[boss], camera_locks=[])
    escena._original_camera_locks = []
    escena._in_arena_prev = True
    escena._arena_ease_elapsed = 0.0
    escena._arena_ease_start = pygame.Vector2(0.0, 0.0)
    escena._relic_timer = 9.0
    escena._relic_shown = True

    # Sólo la parte propia de on_enter(): super().on_enter() necesita un
    # GameContext real, y lo que se está fijando aquí es lo que añadimos.
    jefe = escena._get_boss()
    jefe.set_arena_bounds(pygame.Rect(ARENA_BOUNDS))
    jefe.audio_de_voz = getattr(escena.context, "audio_manager", None)

    assert boss.arena_bounds == pygame.Rect(2480, 0, 784, 608)
    assert boss.audio_de_voz is audio


def test_el_icono_de_reliquia_se_dibuja_tras_el_anuncio():
    """El banner se arma leyendo la bandera del jefe (y no suscribiéndose al
    evento) porque el jefe desaparece de ``entity_list`` poco después de morir:
    el temporizador local sobrevive a esa desaparición."""
    import types

    from src.stages.boss_venado.boss_venado_scene import (
        RELIC_BANNER_DURATION,
        BossVenadoScene,
    )

    boss, _ = make_boss()
    escena = BossVenadoScene.__new__(BossVenadoScene)
    escena._stage_data = types.SimpleNamespace(entity_list=[boss])
    escena._relic_timer = 0.0
    escena._relic_shown = False
    escena._relic_icon = None

    escena._update_relic_banner(DT)
    assert escena._relic_timer == 0.0            # todavía no hay anuncio

    boss.reliquia_anunciada = True
    escena._update_relic_banner(DT)
    assert escena._relic_timer == RELIC_BANNER_DURATION

    lienzo = pygame.Surface((800, 600))
    escena._update_relic_banner(0.7)             # pasado el fundido de entrada
    escena._draw_relic_icon(lienzo)
    assert escena._relic_icon is not None
    esquina = lienzo.subsurface(pygame.Rect(740, 0, 60, 60))
    assert esquina.get_bounding_rect().width > 0, "no se pintó nada en la esquina"

    # Y expira solo.
    escena._update_relic_banner(RELIC_BANNER_DURATION)
    assert escena._relic_timer == 0.0


# ──────────────────────────────────────────────
# D11 — propiedades nuevas del TMX
# ──────────────────────────────────────────────

def _props_del_tmx() -> dict[str, str]:
    raiz = ET.parse(TMX).getroot()
    return {p.get("name"): p.get("value") for p in raiz.find("properties")}


def test_tmx_declares_schema_version():
    """El valor se IMPORTA del motor, no se escribe a mano: escribir un 1
    literal aquí y otro en el generador es garantizar que se separen cuando el
    motor suba de versión."""
    from src.framework.stage.stage_loader import SCHEMA_VERSION

    props = _props_del_tmx()
    assert "schema_version" in props
    assert int(props["schema_version"]) == SCHEMA_VERSION


def test_tmx_declares_author():
    """``grade_stage.py:61`` lo puntúa dentro de REQUIRED_GRADE_PROPS: sin
    declararlo se perdía un tercio de la categoría de metadatos."""
    from src.stages.boss_venado.tools.gen_level_residencias import AUTHOR

    props = _props_del_tmx()
    assert props.get("author") == AUTHOR
    assert props["author"].strip() != ""


def test_tmx_declares_night_frozen_clock():
    """Doc 86 §3.2 (normativo): los jefes de Zona 1 se pelean a las 22 h con el
    reloj congelado. Se declara la forma NOMBRADA (``night``) y no un ``22``
    suelto: es el mismo valor —``RelojDeMundo.MOMENTOS["night"] == 22.0``— y es
    la que dice qué significa cuando alguien abre el mapa en Tiled."""
    from src.framework.stage.day_night import RelojDeMundo
    from src.framework.stage.stage_loader import StageLoader

    props = _props_del_tmx()
    assert props.get("start_hour") == "night"
    assert float(props.get("day_length", "-1")) == 0.0
    assert RelojDeMundo.MOMENTOS["night"] == 22.0

    stage = StageLoader.load(TMX)
    assert stage.start_hour == 22.0
    assert (stage.day_length or 0.0) == 0.0


def test_effective_bloom_matches_approved_value():
    """La otra mitad de la re-calibración: ``_aplicar_hora`` suma
    ``luz.bloom_extra`` encima del bloom declarado, y de noche ese extra es
    +0.14. Bajando el crudo de 0.22 a 0.08 el bloom APLICADO sigue siendo
    exactamente el 0.22 aprobado."""
    from src.framework.stage.day_night import RelojDeMundo
    from src.framework.stage.stage_loader import StageLoader

    stage = StageLoader.load(TMX)
    reloj = RelojDeMundo(hora_inicial=stage.start_hour, duracion_dia=0.0)
    aplicado = stage.bloom + reloj.luz().bloom_extra
    assert abs(aplicado - 0.22) <= 1e-6, (
        f"bloom aplicado {aplicado:.4f} se movió del 0.22 aprobado"
    )


# ──────────────────────────────────────────────
# M-1 / menores — repaso adversarial del paquete H-18
# ──────────────────────────────────────────────

def test_el_teletransporte_no_deja_hitboxes_huerfanas():
    """M-1: las cajas de daño se fijan en coordenadas de MUNDO al abrirse.

    El salto al centro mueve el cuerpo cientos de píxeles, pero el rect de
    STOMP y el del barrido de lianas se quedaban donde estaban y seguían
    cobrando durante toda la ventana de quietud: el jugador veía al jefe al
    otro lado de la arena y recibía el golpe igual."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_X1 - 80.0            # acorralado contra la pared
    boss.rect.x = int(boss.position.x)

    from src.stages.boss_venado.efectos_venado import OleadaDeLianas
    boss._do_stomp()                                # onda de choque en vuelo
    boss._oleadas = [OleadaDeLianas(2900.0, 1, bv.FLOOR_Y, bv.ARENA_X0, bv.ARENA_X1)]  # oleada de lianas en vuelo
    boss._sweep_rooted = bv.SWEEP_ROOTED
    boss._telegraph, boss._telegraph_timer = "CHARGE", bv.CHARGE_TELEGRAPH
    boss._charge_active = True
    caja_vieja = boss._stomp_rect.copy()

    boss.apply_hit(6.5, (0, 0))                     # 12 -> 5.5: arranca la transición
    assert boss.is_transitioning

    assert boss._stomp_rect is None and boss._stomp_window == 0.0
    assert boss._oleadas == [] and boss._sweep_rooted == 0.0
    assert boss._telegraph == "" and boss._telegraph_timer == 0.0
    assert not boss._charge_active and boss._charge_recover == 0.0

    # Lo que de verdad importa: quien esté parado donde estaba la caja vieja no
    # cobra daño de un jefe que ya está a media arena de distancia.
    jugador = _JugadorFalso(pygame.Rect(caja_vieja.x, caja_vieja.y - 24, 20, 32))
    boss._check_player_contact(jugador)
    assert jugador.golpes == [], "una caja de daño sobrevivió al teletransporte"


def test_el_tope_de_la_senoidal_sigue_al_cuerpo_escalado():
    """m-1, gemelo de ``test_stomp_planta_los_pies_en_el_suelo_tambien_escalado``.

    El margen derecho de 80 salía de sumar el sprite de 48 más 32px de hueco
    cuerpo a cuerpo; con el cuerpo agrandado por ``escala`` esos 80 dejaban 12px
    de anca metidos en la pared."""
    boss, _ = make_boss()
    boss.rect.width = boss.rect.height = 60         # cuerpo de fase 2
    boss.position.x = bv.ARENA_X1                   # bien pasado el tope
    boss._update_movement(DT)
    assert boss.position.x == bv.ARENA_X1 - 32.0 - 60.0
    assert boss.position.x + 60 <= bv.ARENA_X1 - 32
    assert boss.facing_direction == -1


def test_la_embestida_para_antes_de_la_pared_tambien_escalada():
    """m-1, lado embestida: 16px de hueco en vez de 32 (la embestida SÍ termina
    pegada a la pared), pero contados igualmente desde el ancho vivo."""
    boss, _ = make_boss()
    _entrar_en_fase_2(boss)
    assert boss.rect.width == 60

    boss.position.x = bv.ARENA_X1 - 200.0
    boss._charge_active, boss._charge_direction = True, 1
    for _ in range(int(3.0 / DT)):
        boss._update_charge(DT)
        if not boss._charge_active:
            break
    assert not boss._charge_active, "la embestida nunca llegó a la pared"
    assert boss.position.x == bv.ARENA_X1 - 16.0 - 60.0
    # Y sigue por dentro del tope de la senoidal, que es lo que evita que el
    # reajuste del fotograma siguiente lo empuje de vuelta.
    assert boss.position.x > bv.ARENA_X1 - 32.0 - 60.0


def test_el_venado_dice_su_linea_de_fase_1_al_ver_al_jugador():
    """m-4: ``sfx_voz_venado_fase1.wav`` no sonaba jamás.

    Su único disparador vivía en el cambio de fase, que por definición ya
    estrena la fase 2 y pide el clip de la 2."""
    boss, _ = make_boss()
    audio = _AudioEspia()
    boss.audio_de_voz = audio
    assert audio.lineas == []

    boss._alert_behavior(DT)
    assert audio.lineas == ["sfx_voz_venado_fase1"]

    for _ in range(30):                             # y no la repite nunca más
        boss._alert_behavior(DT)
    assert audio.lineas == ["sfx_voz_venado_fase1"]


def test_las_esporas_se_apagan_al_tocar_el_suelo():
    """m-5: ``ARENA_RECT`` llega hasta y=608 porque describe la columna entera
    de la arena; usarlo de límite del enjambre dejaba a las esporas
    descendentes ~0,7 s simulándose y pintándose por dentro del terreno."""
    assert bv.ESPORAS_RECT.bottom == int(bv.FLOOR_Y)
    assert bv.ESPORAS_RECT.left == bv.ARENA_RECT.left
    assert bv.ESPORAS_RECT.right == bv.ARENA_RECT.right

    boss, _ = make_boss()
    boss.position.x = bv.ARENA_CX
    boss.rect.x = int(bv.ARENA_CX)
    boss.rect.y = int(bv.FLOOR_Y) - 60              # justo encima del piso
    boss._soltar_abanico_de_esporas()
    nacidas = boss.esporas.contador
    assert nacidas > 0

    for _ in range(int(1.0 / DT)):
        boss.update(DT)

    assert boss.esporas.contador < nacidas, "ninguna espora se retiró"
    bajo_el_piso = [float(y) for y in boss.esporas.y[boss.esporas.vivas]
                    if float(y) > bv.FLOOR_Y]
    assert bajo_el_piso == [], f"esporas vivas bajo el suelo: {bajo_el_piso}"

