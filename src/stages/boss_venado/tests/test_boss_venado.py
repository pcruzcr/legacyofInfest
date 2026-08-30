"""Tests para el boss VENADO SAGRADO reescrito (Evaluación Práctica I)."""
import math

import numpy as np
import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.framework.entities.boss_kit import WeakPoint, resolve_weak_point_damage
from src.framework.entities.enemy_base import EnemyState
from src.stages.boss_venado import boss_venado as bv
from src.stages.boss_venado.boss_venado import BossVenado
from src.stages.boss_venado.efectos_venado import (
    EfectosRegistrados, HOJAS, OleadaDeLianas, POLVO_PISOTON,
)

DT = 1.0 / 60.0


def make_boss(with_bus: bool = False):
    boss = BossVenado(pygame.Vector2(3168, 240))
    bus = None
    if with_bus:
        bus = EventBus()
        boss.set_event_bus(bus)
    return boss, bus


def test_phases_official_config():
    boss, _ = make_boss()
    assert boss.max_health == 12.0
    assert [p.health_threshold for p in boss.phases] == [12.0, 6.0]
    assert boss.phases[0].attack_patterns == ["STOMP", "CHARGE", "VINE_TOSS"]
    assert boss.phases[1].attack_patterns == ["VINE_SWEEP", "MUSHROOM_SPORE", "CHARGE"]
    assert boss.phases[0].movement_type == "sine"
    assert boss.phases[1].movement_type == "bezier"
    assert boss.phases[1].speed_multiplier == 1.5
    assert boss.boss_name == "VENADO SAGRADO"


def test_fase_2_declara_filter_effect_sobel():
    """Unidad VII (c): la fase 2 aplica el filtro Sobel al sprite del jefe.

    Candado de cambio minimo: el resto de la configuracion de fase 2 no
    se toca -- solo se agrega filter_effect al final de la llamada, tal
    como exige el plan (Tarea 14, Paso 4).
    """
    boss = BossVenado(pygame.Vector2(0, 0))
    assert boss.phases[1].filter_effect == "sobel"
    assert boss.phases[1].attack_patterns == ["VINE_SWEEP", "MUSHROOM_SPORE", "CHARGE"]
    assert boss.phases[1].movement_type == "bezier"
    assert boss.phases[1].speed_multiplier == 1.5
    assert boss.phases[1].escala == 1.25
    # la fase 1 no lleva filtro
    assert boss.phases[0].filter_effect is None


# ──────────────────────────────────────────────
# B-048 (veredicto de la parada de la Tarea 14, 2026-08-25): aura de
# bordes Sobel real, en vez del reemplazo opaco 1-de-5 del motor.
# ──────────────────────────────────────────────

def test_apply_filter_propio_nunca_reemplaza_el_sprite_ni_en_el_recomputo():
    """Candado anti-bloque-negro exacto: nuestro override de
    ``_apply_filter`` (B-048) debe devolver el frame SIN tocar, incluso en
    los fotogramas donde ``BossBase._apply_filter`` (motor) habría
    sustituido el sprite por el resultado opaco de
    ``FilterTools.sobel_edge`` (cada 5 llamadas, ``_APPLY_FILTER_EVERY_N_
    FRAMES``)."""
    boss, _ = make_boss()
    boss.current_phase = 1
    original = boss._sprite_frames[boss._get_animation_state()][0]
    for _ in range(6):  # cubre de sobra el multiplo de 5 del motor
        resultado = boss._apply_filter(original.copy())
        assert resultado is not None
        # AU-20260826-03: tostring esta deprecado desde pygame 2.3.0; tobytes es el reemplazo directo
        assert pygame.image.tobytes(resultado, "RGBA") == pygame.image.tobytes(original, "RGBA")


def test_aura_de_bordes_solo_activa_en_fase_sobel_con_hp_bajo():
    """(b): fase 1 nunca; fase 2 con HP>3 no; fase 2 con HP<=3 sí."""
    boss, _ = make_boss()
    boss.current_health = 1.0
    assert boss.current_phase == 0
    assert boss._aura_activa() is False        # fase 1, sin filtro sobel -- nunca, ni con HP bajísimo
    boss.current_phase = 1
    boss.current_health = 4.0
    assert boss._aura_activa() is False         # fase sobel, pero HP por encima de 3 corazones
    boss.current_health = 2.5
    assert boss._aura_activa() is True          # fase sobel + HP<=3 -- activa
    boss.current_health = 3.0
    assert boss._aura_activa() is True          # borde inclusivo (<=3.0)


def test_aura_de_bordes_no_pinta_fuera_de_la_silueta_original():
    """(c): cero píxeles del aura fuera del alfa original -- muestreo de
    las 4 esquinas del tile (siempre transparentes en el sprite: la
    silueta del venado no llega al borde) más un barrido completo de la
    máscara transparente."""
    boss, _ = make_boss()
    boss.current_phase = 1
    boss.current_health = 2.0
    vivo = boss._frame_vivo()
    assert vivo is not None
    frame, _destino, _clave = vivo
    aura = boss._construir_aura_de_bordes(frame)
    ancho, alto = frame.get_size()
    alfa_original = pygame.surfarray.pixels_alpha(frame)
    alfa_aura = pygame.surfarray.pixels_alpha(aura)
    esquinas = [(0, 0), (ancho - 1, 0), (0, alto - 1), (ancho - 1, alto - 1)]
    for x, y in esquinas:
        assert alfa_original[x, y] == 0, "premisa del sprite: las esquinas del tile son transparentes"
        assert alfa_aura[x, y] == 0
    mascara_transparente = alfa_original == 0
    assert np.all(alfa_aura[mascara_transparente] == 0)
    # y de verdad hay ALGO de aura donde sí hay silueta -- que la máscara
    # no esté vaciando el efecto entero por error
    assert alfa_aura.max() > 0


def test_aura_de_bordes_recomputa_sobel_cada_n_frames_no_en_los_intermedios(monkeypatch):
    """(d): ``FilterTools.sobel_edge`` se invoca DE VERDAD en el recómputo
    (contador por monkeypatch) y NO en los fotogramas intermedios
    (caché). Con ``_CADENCIA_RECOMPUTO_AURA`` + 1 dibujados sin cambiar de
    clave (misma animación/dirección/escala), debe invocarse exactamente
    2 veces: una en la activación (primer dibujado, sin caché todavía) y
    una más al tocar el siguiente tick de la cadencia."""
    from src.framework.processing.filter_tools import FilterTools
    boss, _ = make_boss()
    boss.current_phase = 1
    boss.current_health = 2.0
    llamadas = []
    original_sobel = FilterTools.sobel_edge

    def rastreado(surf):
        llamadas.append(1)
        return original_sobel(surf)

    monkeypatch.setattr(FilterTools, "sobel_edge", staticmethod(rastreado))
    surface = pygame.Surface((320, 224))
    camera_offset = pygame.Vector2(0, 0)
    n = bv.BossVenado._CADENCIA_RECOMPUTO_AURA
    for _ in range(n + 1):
        boss._dibujar_aura_de_bordes(surface, camera_offset)
    assert len(llamadas) == 2


def test_aura_de_bordes_se_apaga_del_todo_con_hp_por_encima_de_3():
    """HP>3: aura totalmente apagada -- ``_dibujar_aura_de_bordes`` no
    pinta nada (la superficie destino queda intacta) y limpia su caché."""
    boss, _ = make_boss()
    boss.current_phase = 1
    boss.current_health = 4.0
    surface = pygame.Surface((320, 224))
    # AU-20260826-03: tostring esta deprecado desde pygame 2.3.0; tobytes es el reemplazo directo
    antes = pygame.image.tobytes(surface, "RGB")
    boss._dibujar_aura_de_bordes(surface, pygame.Vector2(0, 0))
    despues = pygame.image.tobytes(surface, "RGB")
    assert antes == despues
    assert boss._aura_base is None


def test_intensidad_pulso_aura_es_determinista_nunca_toca_cero_y_alcanza_el_pico():
    """(e): pulso determinista con dt (dos jefes con la misma secuencia de
    dt producen la misma intensidad en el mismo fotograma), vive
    SIEMPRE en [0.4, 1.0] (nunca 0 -- "que el aura respire, no parpadee
    en seco") y de verdad se acerca al pico en algún punto del ciclo."""
    boss1, _ = make_boss()
    boss2, _ = make_boss()
    for b in (boss1, boss2):
        b.current_phase = 1
        b.current_health = 2.0
    assert boss1._intensidad_pulso_aura() == pytest.approx(0.7)  # t=0 -> seno=0
    muestras = []
    for _ in range(400):  # bastante mas de un ciclo completo a 3Hz
        boss1.update(DT)
        boss2.update(DT)
        muestras.append(boss1._intensidad_pulso_aura())
        assert boss1._intensidad_pulso_aura() == pytest.approx(boss2._intensidad_pulso_aura())
    assert min(muestras) >= 0.4 - 1e-9
    assert max(muestras) <= 1.0 + 1e-9
    assert max(muestras) > 0.95


def test_constructor_contract_loader():
    """El cargador de TMX llama a BossVenado(Vector2(x, y)) sin kwargs — debe funcionar tal cual."""
    boss = BossVenado(pygame.Vector2(0, 0))
    assert boss.is_alive


def test_hitbox_hurtbox_spec():
    boss, _ = make_boss()
    assert boss._build_hitbox() == pygame.Rect(6, 4, 36, 44)     # 17_BOSS_SPEC §3.2
    # Espacio LOCAL (enemy_base.py: docstrings de _build_hitbox/_build_hurtbox +
    # _update_rects desplaza por self.position) — 30x40 centrado en el sprite de 48x48.
    assert boss._build_hurtbox() == pygame.Rect(9, 4, 30, 40)


def test_boss_arranca_con_efectos_nulos_y_sin_oleadas():
    """Valor por defecto: sin conectar_efectos(), self.efectos es EfectosNulos --
    un boss levantado desde una prueba, el grader o el arnés headless sigue
    funcionando exactamente igual que antes de este pulido."""
    from src.stages.boss_venado.efectos_venado import EfectosNulos
    boss, _ = make_boss()
    assert isinstance(boss.efectos, EfectosNulos)
    assert boss._oleadas == []
    assert boss._sweep_rooted == 0.0
    assert boss.oleadas_activas() == []


def test_conectar_efectos_asigna_el_puerto():
    from src.stages.boss_venado.efectos_venado import EfectosRegistrados
    boss, _ = make_boss()
    reg = EfectosRegistrados()
    boss.conectar_efectos(reg)
    assert boss.efectos is reg


def test_sweep_rooted_reemplaza_a_sweep_window():
    """SWEEP_WINDOW ya no existe -- SWEEP_ROOTED (1.6s, B-039 opción C subió
    el valor de 1.2s a 1.6s) es la nueva constante de tiempo plantado tras el
    disparo de la oleada doble."""
    assert not hasattr(bv, "SWEEP_WINDOW")
    assert bv.SWEEP_ROOTED == 1.6


def test_detection_is_arena_gated():
    """Corrección de diseño: el venado NO debe francotirar VINE_TOSS a un jugador
    que todavía camina por el corredor -- solo se activa (aggro) una vez que se
    acerca a la boca de la arena (AGGRO_X = ARENA_X0 - 96), no en el instante en
    que player_ref existe (lo cual el loader/CollisionSystem fija desde el
    fotograma 1, mucho antes de la arena)."""
    boss, _ = make_boss()
    assert boss._check_detection_range() is False       # aún no hay player_ref
    boss.set_player_ref(pygame.Rect(500, 528, 20, 32))   # corredor, lejos de la arena
    assert boss._check_detection_range() is False
    boss.set_player_ref(pygame.Rect(2300, 528, 20, 32))  # corredor, todavía antes de AGGRO_X=2384
    assert boss._check_detection_range() is False
    boss.set_player_ref(pygame.Rect(2400, 528, 20, 32))  # pasado AGGRO_X=2384: boca de la arena
    assert boss._check_detection_range() is True
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))  # dentro de la arena
    assert boss._check_detection_range() is True
    boss.set_player_ref(pygame.Rect(3200, 528, 20, 32))  # bien adentro de la arena
    assert boss._check_detection_range() is True


def test_no_attacks_fire_outside_arena():
    """Complemento de la corrección de diseño: con la detección limitada a la
    arena, un boss que nunca entra en ALERT jamás debe llegar a _try_attack --
    ni proyectil, ni telegraph, ni charge, sin importar qué tan abiertos estén
    todos los cooldowns. Se verifica CADA fotograma (no solo el último): el
    propio ciclo de telegraph/dash/pausa-en-pared de CHARGE puede limpiar
    transitoriamente _telegraph de vuelta a "" según su propio ritmo, lo cual
    haría que una verificación de solo-el-último-fotograma pasara por
    coincidencia sin probar jamás que VINE_TOSS (el bug reportado -- sin
    límite de alcance, arco Bézier de ~2500px) nunca se disparó en el
    corredor."""
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(500, 528, 20, 32))   # corredor, lejos de la arena
    for k in boss._attack_timers:
        boss._attack_timers[k] = 0.0
    for _ in range(180):                                  # 3s: de sobra para que cualquier cooldown reintente
        boss.update(DT)
        assert boss._projectiles == [], "a projectile fired while the player was outside the arena"
        assert boss._telegraph == "", "an attack telegraph started while the player was outside the arena"
        assert not boss._charge_active, "CHARGE fired while the player was outside the arena"


def test_no_engine_v2_auto_retreat_at_low_health():
    """Regresión de ENGINE V2: EnemyBase._should_retreat (enemy_base.py) fuerza
    state=RETREAT en cuanto current_health <= 25% de max_health (con max_health=
    12.0, eso es <=3.0 -- justo dentro de la fase 2), y el _retreat_behavior
    genérico aleja al boss del jugador sin ningún límite ARENA_X0/X1, así que
    puede empujar al Venado completamente fuera de la arena. El diseño oficial
    (17_BOSS_SPEC §3) no tiene estado de retirada; boss_venado.BossVenado.
    _should_retreat sobreescribe el hook para mantener el patrón figura-8 de
    la fase 2 como autoritativo."""
    boss, _ = make_boss()
    boss.current_health = 2.0                             # bien adentro de la banda de salud baja de la fase 2
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))    # dentro de la arena, en rango de detección
    assert boss._should_retreat() is False
    for _ in range(120):                                   # 2s: de sobra para que la máquina de estados se asiente
        boss.update(DT)
        assert boss.state != EnemyState.RETREAT
    assert boss._should_retreat() is False


# ──────────────────────────────────────────────
# Task 9 (revisión final 2026-08-21, B-035) -- blindaje del boss en su arena.
#
# Hallazgo de la canónica competent (seed 1, 14400f): tras la última oleada,
# CompetentBot._decide_bait_charge retrocede al jugador por debajo de AGGRO_X
# sin conciencia de ese límite -- el venado pierde el aggro, EnemyBase enruta
# a EnemyState.SEARCH, y `EnemyBase._search_behavior` (enemy_base.py ~L1060)
# mueve `position.x` DIRECTO hacia `_last_seen` sin pasar por NINGÚN clamp de
# `_update_movement` -- el jefe cruza ARENA_X0 y se queda mudo (0 BOSS_ATTACK,
# 0 PLAYER_DAMAGED) el resto de la corrida. Dos capas de blindaje independientes:
# (1) `_search_behavior` sobreescrito -- el venado jamás abandona su arena para
#     buscar, vuelve al patrón de deriva de PATROL.
# (2) un clamp de último recurso al final de `update()` -- por si el motor
#     algún día mueve X por otra ruta que tampoco pase por `_update_movement`
#     (knockback, launch...).
# ──────────────────────────────────────────────

def test_el_venado_jamas_sale_de_la_arena_en_search():
    """(1): con el venado ya pegado a la pared izquierda y `_last_seen` 600px
    al oeste de la arena (el jugador que el jefe "recuerda" desde el corredor),
    forzar EnemyState.SEARCH cada fotograma durante 3s no debe sacarlo NUNCA
    de [ARENA_X0, ARENA_X1] -- ni un solo fotograma intermedio."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_X0 + 40.0
    boss.rect.x = int(boss.position.x)
    boss._last_seen = pygame.Vector2(bv.ARENA_X0 - 600.0, boss.position.y)
    for _ in range(180):                     # 3s -- SEARCH_DURATION completo, de sobra
        boss.state = EnemyState.SEARCH
        boss._search_timer = 10.0            # nunca decae a PATROL dentro de esta ventana -- se quiere ejercitar SEARCH todo el tiempo
        boss.update(DT)
        assert boss.rect.left >= bv.ARENA_X0, (
            f"el venado salió de la arena por la izquierda en SEARCH: rect.left={boss.rect.left}")
        assert boss.rect.right <= bv.ARENA_X1, (
            f"el venado salió de la arena por la derecha en SEARCH: rect.right={boss.rect.right}")


def test_el_clamp_de_arena_corrige_un_empuje_externo():
    """(2): un `position.x` fuera de la arena puesto a mano (simula cualquier
    ruta futura del motor que mueva X sin pasar por `_update_movement`) debe
    quedar corregido tras UN solo `update()` -- por ambos lados de la arena."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_X0 - 100.0
    boss.rect.x = int(boss.position.x)
    boss.update(DT)
    assert bv.ARENA_X0 + 32 <= boss.position.x
    assert boss.rect.x == int(boss.position.x)

    boss2, _ = make_boss()
    boss2.position.x = bv.ARENA_X1 + 100.0
    boss2.rect.x = int(boss2.position.x)
    boss2.update(DT)
    assert boss2.rect.right <= bv.ARENA_X1 - 32
    assert boss2.rect.x == int(boss2.position.x)


def test_alert_behavior_keeps_running_under_chase_state(monkeypatch):
    """Triage de recertificación V2 (2026-07-29): se investigó la hipótesis de
    que el _run_state_machine reescrito de EnemyBase de ENGINE V2 (SEARCH/CHASE/
    RECOVER/RETREAT/STUNNED) enruta a un boss dentro de rango hacia CHASE en
    lugar de ALERT y, en CHASE, se salta `_alert_behavior` por completo --
    dejando al boss perseguir genéricamente y golpear solo vía
    `damage_on_contact` en lugar de ejecutar sus patrones de ataque diseñados
    (motivado por v2_recert_dodger2: 15 golpes de damage_on_contact=0.75,
    todos correlacionados con CHARGE).

    REFUTADO al leer `_run_state_machine` directamente (enemy_base.py,
    ~líneas 763-782): `self._alert_behavior(dt)` se llama
    INCONDICIONALMENTE siempre que `player_in_range` sea True, sin importar
    si `self.state` termina en ALERT o CHASE -- la etiqueta de estado solo
    cambia para fines de animación/SFX (su propio docstring: "ALERT es el
    primer fotograma de detección; a partir de ahí es CHASE"). La causa real
    de los golpes al dodger fue un bug DIFERENTE, del lado del bot
    (el `_on_attack` de playtest/bots.py armaba también una esquiva
    reactiva genérica de 45f en CHARGE, secuestrando el salto cronometrado
    dedicado de `_decide_charge_dodge` -- corregido ahí, no aquí).

    Este test fija la refutación con un conteo directo de llamadas (no un
    invariante físico indirecto como la fórmula del seno -- un primer intento
    con eso falló en la primerísima corrida: CHARGE/STOMP legítimamente
    sobreescriben `position.y` mientras están activos, lo cual no es una
    regresión, así que afirmar la curva de seno pura produce falsos
    positivos cada vez que un ataque se dispara durante la ventana
    muestreada)."""
    calls: dict[str, int] = {}
    orig_alert_behavior = BossVenado._alert_behavior

    def counting_alert_behavior(self, dt):
        key = self.state.name
        calls[key] = calls.get(key, 0) + 1
        return orig_alert_behavior(self, dt)

    monkeypatch.setattr(BossVenado, "_alert_behavior", counting_alert_behavior)

    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))   # dentro de la arena, en rango de detección
    boss.update(DT)
    assert boss.state == EnemyState.ALERT, "primer frame en rango: debe ser ALERT (sanity)"
    for _ in range(30):
        boss.update(DT)
        assert boss.state == EnemyState.CHASE, \
            "el boss debe permanecer en CHASE con el player fijo dentro del rango"
    assert calls.get("ALERT", 0) >= 1, "sanity: _alert_behavior no corrió durante ALERT"
    assert calls.get("CHASE", 0) >= 25, (
        f"REGRESIÓN: _alert_behavior dejó de ejecutarse bajo CHASE (conteo real={calls})")


def test_dos_ataques_listos_el_mismo_frame_no_se_pisan():
    """B-030 (observación menor H-23, FINDINGS.md): `_alert_behavior` recorre
    `phase.attack_patterns` completo sin `break` -- si dos patrones están
    listos el mismo fotograma, el segundo `_try_attack` pisa el `_telegraph`
    que el primero acababa de armar Y quema el cooldown de AMBOS, así que el
    turno del primero se pierde por completo sin que nada se dispare en su
    lugar. El fix (fase 2 de este candado) corta el bucle en cuanto el
    primer patrón consigue armar telegraph."""
    boss, _ = make_boss()
    # <=96px del boss y en la MISMA mitad de la arena: el gate de STOMP se
    # cumple, el de CHARGE (mitades opuestas) no -- así que, listos los dos
    # el mismo fotograma, STOMP es el único que debería sobrevivir.
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)
    # Neutraliza la gracia del fix de aggro (interacción entre cambios
    # señalada por el dictamen doc-guardian): este candado prueba el bucle
    # de armado de _alert_behavior, no la gracia -- el atributo todavía no
    # existe pre-fix y asignarlo aquí es inofensivo (Python permite
    # atributos dinámicos sin __slots__).
    boss._voz_de_aggro_dicha = True
    boss._gracia_de_aggro = 0.0
    for k in boss._attack_timers:
        boss._attack_timers[k] = 0.0
    boss._alert_behavior(DT)
    assert boss._telegraph == "STOMP", (
        f"el primer patrón listo de la fase (STOMP) debía ganar el turno, quedó {boss._telegraph!r}")
    assert boss._attack_timers["VINE_TOSS"] <= 0.0, (
        "VINE_TOSS no debía disparar este fotograma -- su cooldown no debía consumirse")


def test_el_primer_ataque_respeta_la_gracia_de_aggro():
    """H-26/B-031: el primer VINE_TOSS de la pelea se telegrafiaba FUERA de
    cámara -- evidencia del filmstrip 20260819_155557, el boss dispara a
    561px con la cámara todavía viniendo del corredor, el ease de cámara de
    0.3s del fix H-17 recién empezando. GRACIA_DE_AGGRO=0.6s (2x ese ease)
    le da su momento a la voz de aggro (`sfx_voz_venado_fase1`, armada la
    ÚNICA vez que se pone `_voz_de_aggro_dicha`) y deja que la cámara se
    asiente antes de que el primer ataque pueda armarse."""
    boss, _ = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)
    for k in boss._attack_timers:
        boss._attack_timers[k] = 0.0
    frames_gracia = int(bv.GRACIA_DE_AGGRO / DT)   # pre-fix: AttributeError -- la constante todavía no existe
    for _ in range(frames_gracia - 2):
        boss.update(DT)
        assert boss._telegraph == "" and not boss._charge_active, (
            "ningún ataque debía armarse mientras la gracia de aggro sigue viva")
    for _ in range(60):
        boss.update(DT)
        if boss._telegraph != "":
            break
    assert boss._telegraph != "", "el ataque nunca llegó a armarse tras expirar la gracia de aggro"


def test_spawn_rect_and_feet_anchor():
    """La Y de spawn del TMX es la línea de los PIES; el patrón del motor la convierte a esquina superior izquierda."""
    boss = BossVenado(pygame.Vector2(3168, 240))
    assert boss.rect.size == (48, 48)
    assert boss.position.y == 240 - 48
    assert boss.rect.topleft == (3168, 192)


def test_sine_drift_formula():
    boss, _ = make_boss()
    for _ in range(30):
        boss._update_movement(DT)
    expected_y = bv.BASE_Y + bv.SINE_AMPLITUDE * math.sin(
        2 * math.pi * bv.SINE_FREQ * boss._elapsed)
    assert abs(boss.position.y - expected_y) < 1e-6
    assert boss._elapsed > 0


def test_sine_stays_reachable_and_in_arena():
    boss, _ = make_boss()
    min_x, max_x, max_bottom = 1e9, -1e9, -1e9
    for _ in range(int(6.0 / DT)):        # más de 2 períodos completos
        boss._update_movement(DT)
        min_x = min(min_x, boss.position.x)
        max_x = max(max_x, boss.position.x)
        max_bottom = max(max_bottom, boss.position.y + 48)
    assert min_x >= bv.ARENA_X0 + 32 - 1e-6
    assert max_x <= bv.ARENA_X1 - 80 + 1e-6
    assert 520.0 <= max_bottom <= bv.FLOOR_Y - 8   # ventana alcanzable por melee (corrección H-04/H-08)


def test_stomp_trigger_telegraph_window():
    boss, _ = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)   # dentro de 96 px
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    assert boss._telegraph == "STOMP" and boss._telegraph_timer == bv.STOMP_TELEGRAPH
    assert boss._attack_timers["STOMP"] == boss._attack_cooldowns["STOMP"]
    for _ in range(int(bv.STOMP_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    assert boss._stomp_rect is not None
    assert boss._stomp_rect.width == 96 and boss._stomp_rect.y == int(bv.FLOOR_Y) - 8
    for _ in range(int(bv.STOMP_WINDOW / DT) + 1):
        boss._update_attack_state(DT)
    assert boss._stomp_rect is None                     # ventana cerrada (corrige el bug de la base)


def test_stomp_not_triggered_far():
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(int(boss.rect.centerx) - 300, 528, 20, 32))
    boss._try_attack("STOMP")
    assert boss._telegraph == ""
    assert boss._attack_timers["STOMP"] == 0.0


def test_charge_trigger_opposite_half_and_direction():
    boss, _ = make_boss()                                   # spawn 3168 (mitad derecha)
    boss.set_player_ref(pygame.Rect(2500, 528, 20, 32))     # mitad izquierda
    boss._try_attack("CHARGE")
    assert boss._telegraph == "CHARGE"
    for _ in range(int(bv.CHARGE_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    assert boss._charge_active and boss._charge_direction == -1


def test_charge_same_half_no_trigger():
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(3000, 528, 20, 32))     # misma mitad derecha
    boss._try_attack("CHARGE")
    assert boss._telegraph == "" and not boss._charge_active


def test_charge_speed_by_phase_and_wall_stop():
    boss, _ = make_boss()
    boss._charge_active, boss._charge_direction = True, -1
    x0 = boss.position.x
    boss._update_charge(DT)
    assert abs((x0 - boss.position.x) - bv.CHARGE_SPEED_P1 * DT) < 1e-6
    boss.current_phase = 1
    x1 = boss.position.x
    boss._update_charge(DT)
    assert abs((x1 - boss.position.x) - bv.CHARGE_SPEED_P2 * DT) < 1e-6
    boss.position.x = bv.ARENA_X0 + 17
    boss._update_charge(1.0)
    assert not boss._charge_active                          # se detuvo en la pared


def test_charge_emits_boss_attack_event():
    """Paridad H-08 con STOMP: CHARGE también debe anunciarse, o nada observable
    (incluyendo bots/tests dirigidos por eventos) podrá detectar jamás que se disparó."""
    boss, bus = make_boss(with_bus=True)
    received = []
    # ENGINE V2: EventBus.subscribe() solo guarda una referencia débil (event_bus.py
    # _Subscription -- weakref.ref para callables simples). Una lambda pasada inline
    # sin ningún otro referente es recolectada antes del siguiente dispatch() y la
    # suscripción se descarta silenciosamente (registrado como "dropping collected
    # subscriber"). Mantenerla ligada a un nombre local la conserva viva durante la
    # vida del test.
    on_attack = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.BOSS_ATTACK, on_attack)
    boss.set_player_ref(pygame.Rect(2500, 528, 20, 32))     # mitad izquierda
    boss._try_attack("CHARGE")
    for _ in range(int(bv.CHARGE_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    assert boss._charge_active
    bus.dispatch()
    assert received and received[-1]["pattern"] == "CHARGE"


def test_stomp_plants_boss_to_ground_during_window():
    """Corrección de diseño H-04: STOMP debe bajar al boss hasta el piso por
    completo (spec §3.3 'a nivel de piso') durante la ventana de telegraph +
    castigo -- esa es la ventana de vulnerabilidad al melee que la spec (y los
    bots de QA) esperan. Primero deja que el drift senoidal se asiente (en
    peleas reales nunca se hace STOMP justo a la altura de spawn --
    enter_arena() en el arnés de playtest se asienta 120f antes de que
    cualquier ataque pueda dispararse) para que el boss empiece en su banda
    de oscilación normal, igual que en el juego, en vez de probar una subida
    completa 192->560 inalcanzable que el presupuesto de tiempo de la
    ventana nunca tuvo pensado cubrir."""
    boss, _ = make_boss()
    far_pr = pygame.Rect(int(boss.rect.centerx) + 1000, 528, 20, 32)  # lejos: sin auto-disparo mientras se asienta
    boss.set_player_ref(far_pr)
    for _ in range(90):             # 1.5s: dejar que el seno se asiente en su banda normal
        boss.update(DT)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)        # ahora acercar al jugador
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    reached_floor = False
    for _ in range(int((bv.STOMP_TELEGRAPH + bv.STOMP_WINDOW) / DT) + 2):
        boss.update(DT)
        if boss.rect.bottom >= int(bv.FLOOR_Y):
            reached_floor = True
            break
    assert reached_floor, (
        f"boss never planted to the ground during STOMP: rect.bottom={boss.rect.bottom}")
    assert boss.rect.bottom == int(bv.FLOOR_Y)


def test_charge_sweeps_into_melee_band():
    """Corrección de diseño H-08: CHARGE debe bajar al boss hacia la banda de
    melee del jugador mientras arremete, no solo cruzar la arena a la altura
    donde sea que lo dejó el seno -- el paro-en-pared con daño de contacto de
    la spec solo tiene sentido físico a esa altura. Arranca al boss en
    ARENA_CX (espacio a ambos lados) para que el dash no se detenga en la
    pared antes de que termine el barrido vertical (mucho más rápido) -- un
    boss que aparece justo al lado de una pared y se detiene en 2-3
    fotogramas es un artefacto de la configuración del test, no algo que la
    geometría real de disparo (CHARGE solo se dispara con dx>=ARENA_W//2 de
    distancia) produzca jamás."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_CX
    boss.position.y = bv.BASE_Y - bv.SINE_AMPLITUDE   # empezar en el punto alto del seno (lejos de la banda)
    boss._charge_active, boss._charge_direction = True, 1
    for _ in range(int(2.0 / DT)):                    # el propio charge solo dura una fracción de esto
        boss._update_charge(DT)
        if not boss._charge_active:                   # paro en pared: el barrido de banda ya se aplicó este fotograma
            break
    assert boss.position.y + 48 >= 540, (
        f"boss never swept into the melee band during CHARGE: rect.bottom={boss.position.y + 48}")


def test_y_recovery_after_attack_is_bounded_no_teleport():
    """Contrato de recuperación H-04/H-08: una vez que un ataque termina, el
    boss se reacomoda gradualmente hacia la fórmula del seno a
    VERTICAL_ATTACK_SPEED, nunca salta/teletransporta de vuelta en un solo
    fotograma.

    ACTUALIZADO para la corrección del Hallazgo C (recuperación de castigo en
    el piso, FINDINGS.md): el cierre de la ventana de onda de choque ya no
    arma _y_recovering directamente -- ahora el boss pasa primero
    STOMP_RECOVER segundos plantado e inofensivo (una ventana de castigo
    real, ver test_stomp_has_grounded_punish_recover más abajo), LUEGO se
    reacomoda gradualmente. Este test recorre esa fase de recuperación antes
    de verificar el contrato original de paso acotado, que por lo demás no
    cambia."""
    boss, _ = make_boss()
    far_pr = pygame.Rect(int(boss.rect.centerx) + 1000, 528, 20, 32)
    boss.set_player_ref(far_pr)
    for _ in range(90):
        boss.update(DT)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    for _ in range(int((bv.STOMP_TELEGRAPH + bv.STOMP_WINDOW) / DT) + 2):
        boss.update(DT)
    assert boss._stomp_rect is None                    # ventana de onda de choque cerrada
    assert boss._stomp_recover > 0, "grounded punish recover never armed"
    assert not boss._y_recovering, "recovery should wait for the punish recover, not start immediately"

    for _ in range(int(bv.STOMP_RECOVER / DT) + 3):     # recorrer la nueva recuperación de castigo
        if boss._stomp_recover <= 0:
            break
        boss.update(DT)
    assert boss._y_recovering, "recovery flag never armed once the punish recover ended"

    eps = 1e-6
    max_step = bv.VERTICAL_ATTACK_SPEED * DT + eps
    for _ in range(int(2.0 / DT)):
        y_before = boss.position.y
        boss.update(DT)
        assert abs(boss.position.y - y_before) <= max_step, (
            f"y jumped {abs(boss.position.y - y_before):.3f}px in one frame "
            f"(max allowed {max_step:.3f}) -- recovery teleported instead of easing")
        if not boss._y_recovering:
            break
    assert not boss._y_recovering, "recovery never finished re-locking to the sine formula"


def test_stomp_has_grounded_punish_recover():
    """Corrección del Hallazgo C (FINDINGS.md): el boss reescrito no tenía
    ningún remanente seguro después de la onda de choque -- el alcance de
    melee vivía por completo dentro del propio radio de la onda de choque
    todo el tiempo que _stomp_window estaba viva, así que "esperar a que sea
    seguro y luego golpear" no era una estrategia que existiera para este
    ataque. Ahora el cierre de la ventana arma una fase de castigo
    STOMP_RECOVER plantada e inofensiva: el boss se queda plantado en el
    piso, la onda de choque sigue ausente, y ningún ataque nuevo puede
    comenzar."""
    boss, _ = make_boss()
    far_pr = pygame.Rect(int(boss.rect.centerx) + 1000, 528, 20, 32)
    boss.set_player_ref(far_pr)
    for _ in range(90):
        boss.update(DT)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    for _ in range(int((bv.STOMP_TELEGRAPH + bv.STOMP_WINDOW) / DT) + 2):
        boss.update(DT)

    assert boss._stomp_rect is None, "shockwave should already be gone"
    assert boss._stomp_recover > 0, "grounded punish recover never armed"
    assert boss.rect.bottom == int(bv.FLOOR_Y), "boss should stay planted during the punish recover"
    assert not boss._y_recovering, "recovery should wait for the punish recover to end"

    # Ningún ataque nuevo debe poder comenzar mientras está plantado y
    # recuperándose -- mover al jugador a la mitad opuesta (un disparador
    # válido de CHARGE) y forzar que todos los cooldowns estén abiertos,
    # luego ejecutar el comportamiento de alerta directamente.
    boss.set_player_ref(pygame.Rect(int(bv.ARENA_X0) + 10, 528, 20, 32))
    for k in boss._attack_timers:
        boss._attack_timers[k] = 0.0
    boss._alert_behavior(DT)
    assert boss._telegraph == "" and not boss._charge_active, (
        "a new attack started during the grounded punish recover")

    recover_frames = int(bv.STOMP_RECOVER / DT) + 3
    for _ in range(recover_frames):
        if boss._stomp_recover <= 0:
            break
        assert boss.rect.bottom == int(bv.FLOOR_Y), "boss left the floor before recover expired"
        assert boss._stomp_rect is None, "shockwave should stay gone during recover"
        boss.update(DT)
    assert boss._stomp_recover <= 0
    assert boss._y_recovering, "y_recovering never armed once the punish recover expired"


def test_stomp_que_conecta_conserva_el_recover_plantado():
    """H-25/B-029 (FINDINGS.md línea 4216): cuando la onda de choque de STOMP
    SÍ conecta con el jugador, la rama correspondiente de
    _check_player_contact aplica el daño, limpia _stomp_rect Y apaga
    _stomp_window directamente a 0.0 -- ese cero directo se salta por
    completo el flip ventana->recover de _update_attack_state (líneas
    735-747, el ÚNICO punto que arma self._stomp_recover = STOMP_RECOVER),
    así que el recover plantado de 0.6s jamás se activa y el boss salta de
    golpe a la altura de vuelo de la senoidal en un solo fotograma. Este
    candado conecta la onda a mano y exige el mismo recover plantado que ya
    exige test_stomp_has_grounded_punish_recover (arriba), pero para el
    caso en que la ventana SÍ golpeó a alguien antes de cerrarse."""
    boss, _ = make_boss()
    far_pr = pygame.Rect(int(boss.rect.centerx) + 1000, 528, 20, 32)
    boss.set_player_ref(far_pr)
    for _ in range(90):
        boss.update(DT)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    # Avanza SOLO el telegraph (+2 de margen, mismo criterio que el resto
    # del archivo) -- la onda debe seguir viva, dentro de STOMP_WINDOW.
    for _ in range(int(bv.STOMP_TELEGRAPH / DT) + 2):
        boss.update(DT)
    assert boss._stomp_rect is not None, "shockwave should still be live inside the window"

    # Jugador parado sobre el BORDE IZQUIERDO de la onda (ancho 96, centrada
    # en el boss) -- no en el centro: _check_player_contact termina en
    # super()._check_player_contact(player), que cobra contacto corporal
    # aparte contra self.hurtbox (30px de ancho, centrado en el boss); un
    # falso colocado en el centro de la onda también solaparía ese hurtbox
    # y el test vería DOS golpes ([1.0, 0.75]) en vez de aislar el de la
    # onda. FakePlayer trae rect/hurtbox/velocity/apply_damage, exactamente
    # lo que _check_player_contact toca (clase definida más abajo en este
    # archivo; ya existe en el scope del módulo para cuando este test corre).
    fake = FakePlayer(pygame.Rect(
        boss._stomp_rect.left + 2, boss._stomp_rect.top - 24, 20, 32))
    # centerx sigue >= ARENA_X0 (el boss nace en x=3168) -- la rama de
    # esporas de _check_player_contact también corre, pero self.esporas
    # está vacío (nadie llamó _soltar_abanico_de_esporas), así que
    # dano_total_contra es 0.0 y no aporta un segundo golpe.
    boss._check_player_contact(fake)
    assert fake.damage_calls == [1.0], "shockwave should connect for exactly the official STOMP damage"
    assert boss._stomp_rect is None, "anti multi-hit: shockwave must be gone after connecting"

    # Deja correr el ciclo como si la ventana hubiera expirado sola.
    for _ in range(int(bv.STOMP_WINDOW / DT) + 3):
        boss.update(DT)
        if boss._stomp_recover > 0:
            break
    assert boss._stomp_recover > 0, "H-25: la onda que conecta robó el recover plantado"

    eps = 1e-6
    max_step = bv.VERTICAL_ATTACK_SPEED * DT + eps
    recover_frames = int(bv.STOMP_RECOVER / DT) + 3
    for _ in range(recover_frames):
        if boss._stomp_recover <= 0:
            break
        assert boss.rect.bottom == int(bv.FLOOR_Y), "boss left the floor before recover expired"
        y_before = boss.position.y
        boss.update(DT)
        assert abs(boss.position.y - y_before) <= max_step, (
            f"y jumped {abs(boss.position.y - y_before):.3f}px in one frame "
            f"(max allowed {max_step:.3f}) -- recovery teleported instead of easing")


def test_charge_wall_pause_is_stationary_punish_window():
    """Corrección del Hallazgo C, lado CHARGE: el dash solía pasar directo a
    _y_recovering en el instante en que golpeaba la pared, sin ninguna pausa
    observable -- ahora se mantiene quieto en la pared (altura de banda)
    durante CHARGE_WALL_PAUSE segundos, una segunda ventana de castigo
    estacionaria que refleja la recuperación en el piso de STOMP."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_X0 + 17
    boss._charge_active, boss._charge_direction = True, -1
    boss._update_charge(1.0)                       # dt grande: garantiza el paro en pared este fotograma
    assert not boss._charge_active
    assert boss._charge_recover > 0, "wall pause never armed"
    assert not boss._y_recovering, "recovery should wait for the wall pause, not start immediately"

    x_at_wall = boss.position.x
    y_at_wall = boss.position.y
    recover_frames = int(bv.CHARGE_WALL_PAUSE / DT) + 3
    saw_pause = False
    for _ in range(recover_frames):
        boss.update(DT)
        # Verificado DESPUÉS de update (no antes): el fotograma en que
        # _charge_recover decae por debajo de 0 legítimamente reanuda el
        # movimiento dentro de esa misma llamada a update() (recover se
        # actualiza en _update_attack_state, que corre antes de que
        # _update_movement lo lea) -- el mismo límite que
        # test_no_horizontal_drift_during_stomp_cycle más abajo.
        still_paused = boss._charge_recover > 0
        if still_paused:
            saw_pause = True
            assert boss.position.x == x_at_wall, "boss drifted horizontally during the CHARGE wall pause"
            assert boss.position.y == y_at_wall, "boss should stay at band height during the wall pause"
            assert not boss._charge_active, "a new CHARGE should not restart during its own wall pause"
        else:
            break
    assert saw_pause, "wall pause never observed active during the loop"
    assert boss._charge_recover <= 0
    assert boss._y_recovering, "y_recovering never armed once the CHARGE wall pause expired"


def test_no_horizontal_drift_during_stomp_cycle():
    """Corrección del Hallazgo C: el viejo drift senoidal seguía sumando a
    position.x durante todo el telegraph+window(+recover) de STOMP,
    socavando la suposición de los bots de un objetivo de castigo
    cuasi-estático -- el boss viejo congelaba X durante STOMP, este no lo
    hacía (FINDINGS.md Hallazgo C, punto 1)."""
    boss, _ = make_boss()
    far_pr = pygame.Rect(int(boss.rect.centerx) + 1000, 528, 20, 32)
    boss.set_player_ref(far_pr)
    for _ in range(90):
        boss.update(DT)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    x0 = boss.position.x
    total_frames = int((bv.STOMP_TELEGRAPH + bv.STOMP_WINDOW + bv.STOMP_RECOVER) / DT) + 4
    saw_recover = False
    for _ in range(total_frames):
        boss.update(DT)
        still_in_cycle = (boss._telegraph == "STOMP" or boss._stomp_window > 0
                           or boss._stomp_recover > 0)
        if boss._stomp_recover > 0:
            saw_recover = True
        if still_in_cycle:
            assert boss.position.x == x0, "boss drifted horizontally during the STOMP punish cycle"
        else:
            break
    assert saw_recover, "recover window never armed -- test didn't exercise the full cycle"


def test_projectile_attacks_emit_boss_attack():
    """Corrección del Hallazgo D (FINDINGS.md): VINE_TOSS/MUSHROOM_SPORE
    también deben anunciarse, igual que STOMP/CHARGE, o el bot dodger queda
    estructuralmente ciego ante ellos (medido: 0 fotogramas de aviso, 4/5
    golpes en f2_dodger_recal fueron VINE_TOSS sin anunciar)."""
    boss, bus = make_boss(with_bus=True)
    received = []
    # ENGINE V2: mantener vivo el handler -- ver test_charge_emits_boss_attack_event.
    on_attack = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.BOSS_ATTACK, on_attack)
    pr = pygame.Rect(2600, 528, 20, 32)

    boss._do_vine_toss(pr)
    bus.dispatch()
    assert received and received[-1]["pattern"] == "VINE_TOSS"
    assert received[-1]["rect"].size == (10, 10)

    boss._do_mushroom_spore(pr)
    bus.dispatch()
    assert received[-1]["pattern"] == "MUSHROOM_SPORE"
    assert received[-1]["rect"] == boss.rect


def test_stomp_emits_sfx_event():
    """Feature A (SFX): STOMP debe emitir SFX_BOSSES_VENADO_STOMP en el mismo
    punto de resolución donde ya emite BOSS_ATTACK (_do_stomp)."""
    boss, bus = make_boss(with_bus=True)
    received = []
    on_sfx = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_VENADO_STOMP, on_sfx)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)   # dentro de 96 px
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    for _ in range(int(bv.STOMP_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    bus.dispatch()
    assert received, "STOMP never emitted SFX_BOSSES_VENADO_STOMP"


def test_charge_emits_sfx_event():
    """Feature A (SFX): CHARGE debe emitir SFX_BOSSES_VENADO_CHARGE en el mismo
    punto de resolución donde ya emite BOSS_ATTACK (_do_charge)."""
    boss, bus = make_boss(with_bus=True)
    received = []
    on_sfx = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_VENADO_CHARGE, on_sfx)
    boss.set_player_ref(pygame.Rect(2500, 528, 20, 32))     # mitad izquierda
    boss._try_attack("CHARGE")
    for _ in range(int(bv.CHARGE_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    bus.dispatch()
    assert received, "CHARGE never emitted SFX_BOSSES_VENADO_CHARGE"


def test_vine_toss_emits_sfx_event():
    """Feature A (SFX): VINE_TOSS debe emitir SFX_BOSSES_VENADO_VINE al
    lanzarse (_do_vine_toss), el mismo instante en que ya emite BOSS_ATTACK."""
    boss, bus = make_boss(with_bus=True)
    received = []
    on_sfx = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_VENADO_VINE, on_sfx)
    boss._do_vine_toss(pygame.Rect(2600, 528, 20, 32))
    bus.dispatch()
    assert received, "VINE_TOSS never emitted SFX_BOSSES_VENADO_VINE"


def test_vine_sweep_emite_boss_attack_y_sfx_al_disparar():
    """Pulido AAA 2026-08-21 (spec §2.1): a diferencia del VINE_SWEEP viejo,
    la oleada doble SÍ emite Events.BOSS_ATTACK con pattern="VINE_SWEEP" al
    disparar, además del SFX ya existente -- decisión del usuario 2026-08-21
    que retira el candado del Hallazgo D (VINE_TOSS/MUSHROOM_SPORE seguían
    siendo ciegos para el dodger; VINE_SWEEP era el tercero, y este pulido lo
    cierra dándole señal real). El rect del evento es la UNIÓN de los rects
    iniciales de las dos oleadas."""
    boss, bus = make_boss(with_bus=True)
    recibido_sfx = []
    recibido_ataque = []
    # EventBus usa weakrefs (Motor V2, Hallazgo G): hay que quedarse con una
    # referencia fuerte a cada lambda o el recolector de basura se la lleva
    # antes de bus.dispatch() (mismo criterio que on_sfx en los tests SFX de arriba).
    on_sfx = lambda **kw: recibido_sfx.append(kw)  # noqa: E731
    on_ataque = lambda **kw: recibido_ataque.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_VENADO_VINE, on_sfx)
    bus.subscribe(Events.BOSS_ATTACK, on_ataque)
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))
    boss._try_attack("VINE_SWEEP")
    for _ in range(int(bv.SWEEP_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    bus.dispatch()
    assert recibido_sfx, "VINE_SWEEP never emitted SFX_BOSSES_VENADO_VINE"
    ataques_sweep = [e for e in recibido_ataque if e.get("pattern") == "VINE_SWEEP"]
    assert len(ataques_sweep) == 1, "VINE_SWEEP debe emitir BOSS_ATTACK exactamente una vez al disparar"
    rect = ataques_sweep[0]["rect"]
    assert isinstance(rect, pygame.Rect)
    # unión de los rects iniciales de las dos oleadas: ancho >= OLEADA_ANCHO + separación*2
    from src.stages.boss_venado.efectos_venado import OLEADA_ANCHO, OLEADA_SEPARACION
    assert rect.width >= OLEADA_ANCHO + 2 * OLEADA_SEPARACION - 1


def test_vine_sweep_crea_dos_oleadas_con_direcciones_opuestas():
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))
    boss._try_attack("VINE_SWEEP")
    # sin "+1": el disparo cae exactamente en la última llamada -- un tick extra
    # también movería las oleadas recién nacidas vía OleadaDeLianas.update()
    # (el bloque de decremento de _sweep_rooted, que actualiza self._oleadas,
    # se ejecuta en la MISMA llamada donde se dispara si sobra un tick).
    for _ in range(int(bv.SWEEP_TELEGRAPH / DT)):
        boss._update_attack_state(DT)
    assert len(boss._oleadas) == 2
    direcciones = sorted(o.direccion for o in boss._oleadas)
    assert direcciones == [-1, 1]
    xs = sorted(o.x for o in boss._oleadas)
    from src.stages.boss_venado.efectos_venado import OLEADA_SEPARACION
    centro = boss.rect.centerx
    assert xs[0] == pytest.approx(centro - OLEADA_SEPARACION)
    assert xs[1] == pytest.approx(centro + OLEADA_SEPARACION)


def test_vine_sweep_arma_sweep_rooted_y_planta_al_jefe():
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))
    x_antes = boss.rect.centerx
    boss._try_attack("VINE_SWEEP")
    # sin "+1" -- ver el comentario equivalente en
    # test_vine_sweep_crea_dos_oleadas_con_direcciones_opuestas: un tick extra
    # decrementaría _sweep_rooted una vez antes de esta lectura.
    for _ in range(int(bv.SWEEP_TELEGRAPH / DT)):
        boss._update_attack_state(DT)
    assert boss._sweep_rooted == pytest.approx(bv.SWEEP_ROOTED)
    # plantado: la X no debe moverse aunque pasen varios frames de _update_movement
    for _ in range(10):
        boss._update_movement(DT)
    assert boss.rect.centerx == x_antes


def test_sweep_rooted_decrementa_y_activa_y_recovering_al_expirar():
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))
    boss._try_attack("VINE_SWEEP")
    for _ in range(int(bv.SWEEP_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    assert boss._sweep_rooted > 0
    assert boss._y_recovering is False
    for _ in range(int(bv.SWEEP_ROOTED / DT) + 2):
        boss._update_attack_state(DT)
    assert boss._sweep_rooted == 0.0
    assert boss._y_recovering is True


def test_grounded_punish_congela_x_durante_telegraph_y_rooted_de_vine_sweep():
    """La X se congela DURANTE el aviso (telegraph) y durante todo el plantado
    posterior (sweep_rooted) -- mismo criterio que STOMP."""
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))
    boss._try_attack("VINE_SWEEP")
    x_en_aviso = boss.rect.centerx
    for _ in range(int(bv.SWEEP_TELEGRAPH / 2 / DT)):   # a mitad del aviso, todavía armado
        boss._update_movement(DT)
        boss._update_attack_state(DT)
    assert boss.rect.centerx == x_en_aviso, "el jefe se movió en X durante el aviso de VINE_SWEEP"


def test_aterrizaje_de_vine_sweep_emite_polvo_dirigido_hacia_arriba():
    from src.stages.boss_venado.efectos_venado import EfectosRegistrados, POLVO_ATERRIZAJE
    boss, _ = make_boss()
    reg = EfectosRegistrados()
    boss.conectar_efectos(reg)
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))
    # empezar en el punto alto del seno (mismo criterio que
    # test_charge_sweeps_into_melee_band): desde el spawn crudo (192) llegar a
    # FLOOR_Y llevaría ~96 frames a VERTICAL_ATTACK_SPEED, muy por encima del
    # presupuesto de este aviso -- en una pelea real el drift senoidal ya
    # asentó al jefe en su banda normal antes de que se dispare cualquier ataque.
    boss.position.y = bv.BASE_Y - bv.SINE_AMPLITUDE
    boss._try_attack("VINE_SWEEP")
    for _ in range(int(bv.SWEEP_TELEGRAPH / DT) + 5):
        boss._update_movement(DT)
        boss._update_attack_state(DT)
    aterrizajes = [c for c in reg.particulas_dirigidas_emitidas if c[3] is POLVO_ATERRIZAJE]
    assert len(aterrizajes) == 1, (
        f"esperada exactamente 1 ráfaga de aterrizaje, hubo {len(aterrizajes)}")
    _, _, angulo, _ = aterrizajes[0]
    assert angulo == -90.0, "el polvo de aterrizaje debe dispararse hacia arriba (-90 grados)"


def test_oleadas_vivas_emiten_tierra_cada_4_frames():
    from src.stages.boss_venado.efectos_venado import EfectosRegistrados, TIERRA_OLEADA
    boss, _ = make_boss()
    reg = EfectosRegistrados()
    boss.conectar_efectos(reg)
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))
    boss._try_attack("VINE_SWEEP")
    for _ in range(int(bv.SWEEP_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)   # dispara las 2 oleadas
    assert len(boss._oleadas) == 2
    reg.particulas_emitidas.clear()   # descarta cualquier ráfaga del propio disparo/aterrizaje
    for _ in range(8):                # 8 frames = 2 cadencias de 4
        boss._update_attack_state(DT)
    tierra = [c for c in reg.particulas_emitidas if c[2] is TIERRA_OLEADA]
    assert len(tierra) >= 2, f"esperadas >=2 ráfagas de tierra en 8 frames, hubo {len(tierra)}"


def test_oleada_muerta_en_pared_emite_dos_rafagas_de_tierra():
    from src.stages.boss_venado.efectos_venado import EfectosRegistrados, TIERRA_OLEADA
    boss, _ = make_boss()
    reg = EfectosRegistrados()
    boss.conectar_efectos(reg)
    # oleada casi pegada a la pared derecha -- muere en 1-2 frames.
    boss._oleadas = [OleadaDeLianas(bv.ARENA_X1 - 2.0, 1, bv.FLOOR_Y, bv.ARENA_X0, bv.ARENA_X1)]
    for _ in range(5):
        boss._update_attack_state(DT)
        if not boss._oleadas:
            break
    assert boss._oleadas == [], "la oleada debía morir contra la pared"
    tierra = [c for c in reg.particulas_emitidas if c[2] is TIERRA_OLEADA]
    assert len(tierra) == 2, f"esperadas exactamente 2 ráfagas al morir en pared, hubo {len(tierra)}"


def test_oleadas_activas_devuelve_solo_los_rects_de_las_vivas():
    boss, _ = make_boss()
    viva = OleadaDeLianas(2800.0, 1, bv.FLOOR_Y, bv.ARENA_X0, bv.ARENA_X1)
    muerta = OleadaDeLianas(2900.0, 1, bv.FLOOR_Y, bv.ARENA_X0, bv.ARENA_X1)
    muerta.golpeada()
    boss._oleadas = [viva, muerta]
    rects = boss.oleadas_activas()
    assert rects == [viva.rect]


def test_mushroom_spore_emits_sfx_event():
    """Feature A (SFX): MUSHROOM_SPORE reutiliza SFX_BOSSES_VENADO_VINE
    (desviación deliberada respecto al boss de referencia, que deja este
    ataque silencioso -- solo existen 3 wavs del Venado, no hay sonido
    dedicado para las esporas)."""
    boss, bus = make_boss(with_bus=True)
    received = []
    on_sfx = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_VENADO_VINE, on_sfx)
    boss._do_mushroom_spore(pygame.Rect(2600, 528, 20, 32))
    bus.dispatch()
    assert received, "MUSHROOM_SPORE never emitted SFX_BOSSES_VENADO_VINE"


def test_sfx_not_emitted_during_telegraph():
    """El SFX debe dispararse en la resolución (fin del windup, el mismo
    instante que BOSS_ATTACK), no en el instante en que empieza el telegraph
    -- una emisión anticipada desincronizaría la señal de sonido del golpe
    visible."""
    boss, bus = make_boss(with_bus=True)
    received = []
    on_sfx = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_VENADO_STOMP, on_sfx)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    bus.dispatch()
    assert boss._telegraph == "STOMP"
    assert not received, "SFX fired at telegraph start instead of resolution"


def bernstein2(p0, p1, p2, t):
    u = 1.0 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def test_vine_toss_path_is_quadratic_bezier():
    boss, _ = make_boss()
    boss._last_player_velocity = pygame.Vector2(100.0, 0.0)
    pr = pygame.Rect(2600, 528, 20, 32)
    boss._do_vine_toss(pr)
    assert len(boss._projectiles) == 1
    proj = boss._projectiles[0]
    assert proj["type"] == "vine" and proj["damage"] == 0.5
    p0 = (boss.rect.centerx + 18.0 * boss.facing_direction, boss.rect.centery - 6.0)
    px = pygame.Vector2(pr.centerx, pr.centery) + pygame.Vector2(100.0, 0.0) * bv.VINE_PREDICT
    p2 = (px.x, min(px.y, bv.FLOOR_Y - 16.0))
    p1 = ((p0[0] + p2[0]) / 2.0, min(p0[1], p2[1]) - 80.0)
    path = proj["path"]
    assert len(path) == 32
    for k in (0, 8, 16, 31):
        ex, ey = bernstein2(p0, p1, p2, k / 31.0)
        assert abs(path[k][0] - ex) < 1e-6 and abs(path[k][1] - ey) < 1e-6


def test_vine_projectile_traverses_and_expires():
    boss, _ = make_boss()
    boss._do_vine_toss(pygame.Rect(2600, 528, 20, 32))
    proj = boss._projectiles[0]
    boss._update_projectiles(0.5)
    assert proj["alive"] and proj["t"] > 0
    assert proj["pos"] != pygame.Vector2(proj["path"][0])   # avanzó a lo largo del arco
    boss._update_projectiles(2.0)                     # t >= 1.0
    assert boss._projectiles == []                    # limpiado


def test_phase_transition_emits_event_and_builds_figure8():
    boss, bus = make_boss(with_bus=True)
    received = []
    # ENGINE V2: mantener vivo el handler -- ver test_charge_emits_boss_attack_event.
    on_phase = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.BOSS_PHASE_CHANGED, on_phase)
    boss.apply_hit(6.5, (0, 0))                       # 12 -> 5.5 <= 6.0
    assert boss.is_transitioning
    hp_before = boss.current_health
    boss.apply_hit(3.0, (0, 0))                       # invulnerable mientras transiciona
    assert boss.current_health == hp_before
    for _ in range(int(2.6 / DT)):                    # transition_timer=2.5 (motor)
        boss.update(DT)
    assert not boss.is_transitioning and boss.current_phase == 1
    bus.dispatch()                                    # EventBus es una cola
    assert received and received[-1]["phase"] == 1
    assert len(boss._bezier_path) == 64               # figura-8 precalculada


def test_figure8_path_inside_arena_and_reachable():
    """Con el cuerpo canónico Y con el cuerpo agrandado de la fase 2 (m-2).

    La trayectoria en ocho es la que gobierna el vuelo justo en la fase que
    declara ``escala``, así que comprobarla sólo a 48px dejaba sin vigilar el
    caso real: con la caída nominal de 45 el extremo inferior queda en y=505 y
    los pies del venado de 60px en 565, cinco píxeles POR DENTRO del piso. La
    caída efectiva se recorta ahora según la altura viva."""
    boss, _ = make_boss()
    path = boss._build_figure8_path()
    xs = [p[0] for p in path]; ys = [p[1] for p in path]
    assert min(xs) >= bv.ARENA_X0 + 16 and max(xs) <= bv.ARENA_X1 - 48
    assert max(ys) + 48 <= bv.FLOOR_Y and max(ys) + 48 >= 500   # se sumerge en rango de melee
    assert boss._caida_de_figura8() == bv.FIGURE8_DIP           # a 48px no se recorta nada

    # Fase 2: mismo cálculo con el cuerpo ya escalado por el motor.
    boss.rect.width = boss.rect.height = 60
    path_2 = boss._build_figure8_path()
    xs_2 = [p[0] for p in path_2]; ys_2 = [p[1] for p in path_2]
    assert boss._caida_de_figura8() < bv.FIGURE8_DIP            # el suelo recorta la caída
    assert min(xs_2) >= bv.ARENA_X0 + 16 and max(xs_2) + 60 <= bv.ARENA_X1
    assert max(ys_2) + 60 <= bv.FLOOR_Y, (
        f"el venado escalado se hunde en el suelo: pies={max(ys_2) + 60}")
    assert max(ys_2) + 60 >= 500                                # y sigue bajando a rango de melee


def test_entrar_en_fase_2_reanuda_la_ruta_sin_teletransporte():
    """H-24/B-028 (FINDINGS.md ~línea 4216): `_finish_phase_transition` fija
    `self._bezier_t = 0.0` a secas al estrenar la fase 2, sin importar dónde
    quedó el cuerpo tras el salto al centro de la arena -- el primer
    fotograma en que `_update_movement` vuelve a correr (con
    `is_transitioning` ya en False) salta la posición de golpe al path[0]
    de la figura en ocho, un tirón medido de ~272px hacia la pared
    izquierda. El fix (fase 2 de este candado) elige el t de la polilínea
    de 64 muestras MÁS CERCANO a `self.position` en vez del extremo fijo,
    además de encadenar `_y_recovering = True` para que la y residual se
    suavice con `_approach_y` en lugar de saltar también."""
    boss, _ = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)
    for _ in range(90):
        boss.update(DT)
    boss.apply_hit(6.5, (0, 0))          # 12 -> 5.5: cruza el umbral de fase 2 (6.0)
    assert boss.is_transitioning

    tope = 220
    cerro_dentro_del_tope = False
    for _ in range(tope):
        boss.update(DT)
        if not boss.is_transitioning:
            cerro_dentro_del_tope = True
            break
    assert cerro_dentro_del_tope, "la ventana de transición nunca cerró dentro del tope de 220 fotogramas"

    # El propio fotograma de cierre (ya consumido por el bucle de arriba)
    # trae el desplazamiento BENIGNO de `_aplicar_escala_de_fase` (ancla
    # pies+centro, ~17.7px -- FINDINGS.md líneas 3804-3813 lo clasifica como
    # artefacto de medición, no un bug); la medición empieza en el
    # fotograma SIGUIENTE -- la cota jamás se sube para absorberlo (regla de
    # oro §3.4).
    eps = 1e-6
    # Misma derivación que el filmstrip: la velocidad legítima más alta que
    # el boss puede alcanzar en un solo fotograma es la mayor entre CHARGE en
    # fase 2 (CHARGE_SPEED_P2, escalada por el `escala`=1.25 de la propia
    # fase) y el picado diagonal de VINE_SWEEP (B-039 opción C,
    # REGISTRO-DE-BUGS.md: VEL_PICADO=1500px/s, sin escalar por `escala` --
    # es una velocidad de aproximación, no una animación del cuerpo), con un
    # margen x2 para no perseguir redondeos -- 1500 * DT * 2 ≈ 50.0 px/frame,
    # todavía muy por debajo de los ~272px del salto que este candado
    # detecta (regla de oro §3.4: la cota nunca sube para absorber el bug).
    max_step = max(bv.CHARGE_SPEED_P2 * 1.25, bv.VEL_PICADO) * DT * 2.0 + eps
    for _ in range(60):
        pos_antes = pygame.Vector2(boss.position)
        boss.update(DT)
        delta = boss.position.distance_to(pos_antes)
        assert delta <= max_step, (
            f"boss.position saltó {delta:.1f}px en un fotograma "
            f"(máximo permitido {max_step:.2f}px) -- H-24: reanudar la fase "
            f"2 no debe teletransportar el cuerpo a path[0]")


def test_spores_three_fan_aimed_at_player():
    boss, _ = make_boss()
    pr = pygame.Rect(2600, 528, 20, 32)
    boss._do_mushroom_spore(pr)
    spores = [p for p in boss._projectiles if p["type"] == "spore"]
    assert len(spores) == 3 and all(p["damage"] == 0.25 for p in spores)
    to_player = pygame.Vector2(pr.centerx - boss.rect.centerx,
                               pr.centery - boss.rect.centery).normalize()
    center = spores[1]["vel"].normalize()
    assert center.dot(to_player) > 0.9999             # la espora central apunta al jugador
    for side in (spores[0], spores[2]):
        assert abs(side["vel"].normalize().dot(center) - math.cos(math.radians(15))) < 1e-4
    assert all(abs(p["vel"].length() - bv.SPORE_SPEED) < 1e-6 for p in spores)


def test_spore_expires_by_distance_not_lifetime():
    boss, _ = make_boss()
    boss._do_mushroom_spore(pygame.Rect(2600, 528, 20, 32))
    proj = boss._projectiles[0]
    proj["vel"] = proj["vel"].normalize() * 1000.0    # acelerado para el test
    boss._update_projectiles(0.5)                     # 500 px > SPORE_RANGE, edad 0.5s
    assert proj not in boss._projectiles


def test_defeat_sequence_stages_then_progression_ready():
    boss, bus = make_boss(with_bus=True)
    boss.apply_hit(12.0, (0, 0))
    assert boss.state == EnemyState.DYING and boss.is_alive
    for _ in range(int(1.6 / DT)):
        boss.update(DT)
    assert boss._defeat_stage == 1                    # cráneo brillante (§3.6)
    for _ in range(int(2.1 / DT)):
        boss.update(DT)
    assert boss._defeat_stage == 2 and not boss.is_alive
    assert boss.death_timer <= 0 and not boss.completion_fired
    # -> ProgressionSystem.check_boss_defeat() disparará el banner (lado del motor)


def test_defeat_sequence_is_one_shot_even_if_hit_again():
    boss, _ = make_boss()
    boss.apply_hit(12.0, (0, 0))
    boss.update(DT)                                   # secuencia en curso
    timer_before = boss.death_timer
    boss.apply_hit(5.0, (0, 0))                       # machacando ataques sobre el boss agonizante
    assert boss._defeat_stage == 0 and boss.death_timer == timer_before


def test_spore_glow_uses_colortools_cache():
    boss, _ = make_boss()
    assert isinstance(boss._spore_glow, pygame.Surface)
    assert boss._spore_glow.get_size() == (16, 16)


def test_defeat_clears_combat_state():
    boss, _ = make_boss()
    boss._do_mushroom_spore(pygame.Rect(2600, 528, 20, 32))
    boss._charge_active = True
    boss._telegraph = "STOMP"
    boss._stomp_recover = 0.3          # Corrección del Hallazgo C: no debe dejar al boss varado a mitad de la recuperación
    boss._charge_recover = 0.3
    boss._oleadas = [OleadaDeLianas(2800.0, 1, bv.FLOOR_Y, bv.ARENA_X0, bv.ARENA_X1)]
    boss._sweep_rooted = 0.5
    boss.apply_hit(12.0, (0, 0))
    assert boss._projectiles == [] and not boss._charge_active and boss._telegraph == ""
    assert boss._stomp_recover == 0.0 and boss._charge_recover == 0.0
    assert boss._oleadas == [] and boss._sweep_rooted == 0.0


class FakePlayer:
    """Jugador duck-typed: solo lo que _check_player_contact toca."""
    def __init__(self, rect):
        self.rect = rect
        self.hurtbox = rect
        self.velocity = pygame.Vector2(50.0, 0.0)
        self.damage_calls = []
    def apply_damage(self, amount, source_position, knockback_force=150.0):
        self.damage_calls.append(amount)


def test_check_player_contact_applies_projectile_and_oleada_damage():
    boss, _ = make_boss()
    fake = FakePlayer(pygame.Rect(2600, 528, 20, 32))
    boss._do_mushroom_spore(fake.rect)
    boss._projectiles[1]["pos"] = pygame.Vector2(fake.rect.center)  # espora central sobre el jugador
    boss._oleadas = [OleadaDeLianas(fake.rect.centerx, 1, float(fake.rect.bottom),
                                    bv.ARENA_X0, bv.ARENA_X1)]
    boss._check_player_contact(fake)
    assert 0.25 in fake.damage_calls and 0.5 in fake.damage_calls
    assert boss._last_player_velocity == pygame.Vector2(50.0, 0.0)
    assert boss._oleadas[0].viva is False and boss._oleadas[0].consumida is True


def test_una_oleada_golpeada_no_apaga_a_la_otra():
    """Cada oleada golpea una sola vez y se consume -- la que sigue viva debe
    poder seguir haciendo daño (los i-frames del jugador, 1.5s, hacen imposible
    el doble golpe real, pero el estado de la SEGUNDA oleada no debe verse
    afectado por la resolución de la primera)."""
    boss, _ = make_boss()
    fake = FakePlayer(pygame.Rect(2600, 528, 20, 32))
    tocando = OleadaDeLianas(fake.rect.centerx, 1, float(fake.rect.bottom), bv.ARENA_X0, bv.ARENA_X1)
    lejos = OleadaDeLianas(bv.ARENA_X1 - 20.0, 1, float(fake.rect.bottom), bv.ARENA_X0, bv.ARENA_X1)
    boss._oleadas = [tocando, lejos]
    boss._check_player_contact(fake)
    assert tocando.viva is False and tocando.consumida is True
    assert lejos.viva is True and lejos.consumida is False
    assert fake.damage_calls == [0.5]


def test_oleada_no_dana_al_jugador_fuera_de_la_arena():
    """Task 9 (revisión final 2026-08-21): candado de regresión del gate
    ``no_damage_outside_arena`` -- el bucle de colisión de oleadas en
    ``_check_player_contact`` no llevaba la misma guarda de arena que ya
    lleva la rama de esporas (``player.rect.centerx >= ARENA_X0``); mismo
    criterio que ``test_las_esporas_no_danan_al_jugador_fuera_de_la_arena``
    de ``test_adopcion_v3.py``."""
    boss, _ = make_boss()
    fake = FakePlayer(pygame.Rect(int(bv.ARENA_X0) - 300, 500, 20, 32))
    boss._oleadas = [OleadaDeLianas(fake.rect.centerx, 1, float(fake.rect.bottom),
                                    bv.ARENA_X0, bv.ARENA_X1)]
    boss._check_player_contact(fake)
    assert fake.damage_calls == []
    # Y la oleada sigue viva -- la guarda va ANTES de golpeada(), que la consume.
    assert boss._oleadas[0].viva is True and boss._oleadas[0].consumida is False


def test_get_animation_key_flags():
    """Función pura de las banderas de instancia — cobertura barata, sin necesidad de ticks de update()."""
    boss, _ = make_boss()
    assert boss._get_animation_key() == "drift"
    boss._charge_active = True
    assert boss._get_animation_key() == "charge"
    boss._charge_active = False
    boss._telegraph = "CHARGE"
    assert boss._get_animation_key() == "charge"
    boss._telegraph = "STOMP"
    assert boss._get_animation_key() == "stomp"
    boss._telegraph = ""
    boss._stomp_window = 0.1
    assert boss._get_animation_key() == "stomp"
    boss._stomp_window = 0.0
    boss._telegraph = "VINE_SWEEP"
    assert boss._get_animation_key() == "vine"
    boss._telegraph = ""
    boss._sweep_rooted = 0.1
    assert boss._get_animation_key() == "vine"
    boss._sweep_rooted = 0.0
    # Corrección del Hallazgo C: las recuperaciones de castigo en piso/pared mantienen la pose correspondiente.
    boss._stomp_recover = 0.1
    assert boss._get_animation_key() == "stomp"
    boss._stomp_recover = 0.0
    boss._charge_recover = 0.1
    assert boss._get_animation_key() == "charge"
    boss._charge_recover = 0.0
    boss.current_phase = 1
    assert boss._get_animation_key() == "frenzy_drift"


# ──────────────────────────────────────────────
# Puntos débiles (Feature C, adoptado de boss_kit.WeakPoint -- spec
# 2026-07-29-adopcion-v2-sfx-luces-weakpoints-design.md §3)
# ──────────────────────────────────────────────

def _cuernos_player_ref(boss, facing: int = 1) -> pygame.Rect:
    """Un rect de jugador colocado justo dentro del rect de cuernos (consciente del facing)."""
    ox = bv.CUERNOS_OFFSET[0]
    if facing < 0:
        ox = boss.rect.width - bv.CUERNOS_OFFSET[0] - bv.CUERNOS_SIZE[0]
    return pygame.Rect(boss.rect.x + ox, boss.rect.y + bv.CUERNOS_OFFSET[1], 20, 32)


def _flanco_player_ref(boss, facing: int = 1) -> pygame.Rect:
    """Un rect de jugador colocado justo dentro del rect de flanco (consciente del facing)."""
    ox = bv.FLANCO_OFFSET[0]
    if facing < 0:
        ox = boss.rect.width - bv.FLANCO_OFFSET[0] - bv.FLANCO_SIZE[0]
    return pygame.Rect(boss.rect.x + ox, boss.rect.y + bv.FLANCO_OFFSET[1], 20, 32)


def test_weak_point_cuernos_multiplies_damage():
    """Los cuernos están expuestos en todas las fases (17_BOSS_SPEC no tiene
    requisito de rúbrica aquí -- este es un enriquecimiento del boss de
    referencia, ver README)."""
    boss, _ = make_boss()
    boss.set_player_ref(_cuernos_player_ref(boss))
    boss.apply_hit(1.0, (0, 0))
    assert boss.current_health == 12.0 - 1.0 * bv.CUERNOS_MULTIPLIER


def test_weak_point_flanco_only_in_phase_2():
    """Dos bosses frescos, no uno golpeado dos veces: EnemyBase.apply_hit fija
    un invincibility_timer de 0.5s en cualquier golpe no letal (enemy_base.py),
    lo cual haría que un segundo apply_hit inmediato no hiciera nada
    silenciosamente y confundiría la intención de este test -- aislar la fase
    0 frente a la fase 1 en instancias separadas evita esto por completo en
    vez de encadenar llamadas a update() solo para agotarlo."""
    boss0, _ = make_boss()
    boss0.set_player_ref(_flanco_player_ref(boss0))
    boss0.apply_hit(1.0, (0, 0))                   # fase 0: flanco no expuesto
    assert boss0.current_health == 12.0 - 1.0      # daño base, sin multiplicador

    boss1, _ = make_boss()
    boss1.current_phase = 1
    boss1.set_player_ref(_flanco_player_ref(boss1))
    boss1.apply_hit(1.0, (0, 0))                   # fase 1 (índice): flanco expuesto ahora
    assert boss1.current_health == 12.0 - 1.0 * bv.FLANCO_MULTIPLIER


def test_weak_point_miss_applies_base_damage():
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(boss.rect.x, boss.rect.y + 300, 20, 32))  # lejos de ambos rects
    boss.apply_hit(1.0, (0, 0))
    assert boss.current_health == 12.0 - 1.0


def test_weak_point_overlap_uses_higher_multiplier():
    """Documenta el propio contrato de boss_kit.resolve_weak_point_damage (gana
    el mejor multiplicador, no la suma) en el contexto de este boss --
    nuestros dos puntos débiles reales nunca se superponen por construcción,
    así que esto usa unos sintéticos."""
    boss, _ = make_boss()
    low = WeakPoint(offset=(0, 0), size=(20, 20), multiplier=1.5, label="low")
    high = WeakPoint(offset=(5, 5), size=(20, 20), multiplier=3.0, label="high")
    hit_rect = pygame.Rect(boss.rect.x + 10, boss.rect.y + 10, 4, 4)  # dentro de ambos
    damage, point = resolve_weak_point_damage(boss, hit_rect, 1.0, [low, high], 0)
    assert point is high and damage == 3.0


def test_last_weak_point_recorded():
    boss, _ = make_boss()
    boss.set_player_ref(_cuernos_player_ref(boss))
    boss.apply_hit(1.0, (0, 0))
    assert boss.last_weak_point is not None
    assert boss.last_weak_point.label == "cuernos"
    assert boss.last_weak_point.multiplier == bv.CUERNOS_MULTIPLIER


def test_weak_point_offsets_mirror_with_facing():
    """El sprite se voltea horizontalmente cuando facing_direction < 0
    (boss_base.py pygame.transform.flip, dentro del lienzo de 48px de ancho).
    Los puntos débiles están definidos en espacio canónico (mirando a la
    derecha), así que golpear la posición reflejada de los cuernos debe
    seguir siendo crítico -- y el offset SIN reflejar (canónico) ya NO debe
    ser crítico, probando que el reflejo realmente ocurrió en vez de que la
    verificación sea agnóstica al facing por accidente."""
    boss, _ = make_boss()
    boss.facing_direction = -1
    boss.set_player_ref(_cuernos_player_ref(boss, facing=-1))
    boss.apply_hit(1.0, (0, 0))
    assert boss.current_health == 12.0 - 1.0 * bv.CUERNOS_MULTIPLIER

    boss2, _ = make_boss()
    boss2.facing_direction = -1
    canonical_rect = pygame.Rect(boss2.rect.x + bv.CUERNOS_OFFSET[0],
                                  boss2.rect.y + bv.CUERNOS_OFFSET[1], 20, 32)
    boss2.set_player_ref(canonical_rect)
    boss2.apply_hit(1.0, (0, 0))
    assert boss2.current_health == 12.0 - 1.0     # el offset canónico falla una vez reflejado


def test_weak_point_multiplier_respects_transition_invulnerability():
    """El multiplicador se calcula y se entrega a super().apply_hit() -- no
    debe saltarse la protección existente del motor de
    invulnerable-mientras-transiciona (la misma cadena de la que ya depende
    el resto del apply_hit del boss, ver
    test_phase_transition_emits_event_and_builds_figure8)."""
    boss, _ = make_boss()
    boss.set_player_ref(_cuernos_player_ref(boss))
    boss.apply_hit(3.0, (0, 0))                   # 3*2.5=7.5 -> 12-7.5=4.5 <= umbral 6.0
    assert boss.is_transitioning
    hp_before = boss.current_health
    boss.apply_hit(1.0, (0, 0))                   # todavía en cuernos, pero a mitad de transición
    assert boss.current_health == hp_before


def test_apply_hit_still_triggers_phase_transition_and_defeat():
    """Regresión: la resolución de puntos débiles no debe interferir con el
    umbral de fase ni con la secuencia de muerte -- ambos ya ejercitados sin
    un golpe de punto débil por
    test_phase_transition_emits_event_and_builds_figure8 /
    test_defeat_sequence_stages_then_progression_ready; este repite la forma
    de ambos CON self._player_ref estacionado en cuernos."""
    boss, _ = make_boss()
    boss.set_player_ref(_cuernos_player_ref(boss))
    boss.apply_hit(3.0, (0, 0))                   # -> transición (ver test de arriba)
    for _ in range(int(2.6 / DT)):
        boss.update(DT)
    assert not boss.is_transitioning and boss.current_phase == 1
    boss.set_player_ref(_cuernos_player_ref(boss))
    boss.apply_hit(10.0, (0, 0))                  # 10*2.5=25, muy por debajo de 0
    assert boss.state == EnemyState.DYING and boss.is_alive


def test_weak_point_flash_activates_on_crit_not_on_normal_hit():
    boss, _ = make_boss()
    boss.set_player_ref(_cuernos_player_ref(boss))
    boss.apply_hit(1.0, (0, 0))
    assert boss._weak_point_flash_timer > 0.0
    assert boss._weak_point_flash_point is not None

    boss2, _ = make_boss()
    boss2.set_player_ref(pygame.Rect(boss2.rect.x, boss2.rect.y + 300, 20, 32))
    boss2.apply_hit(1.0, (0, 0))
    assert boss2._weak_point_flash_timer == 0.0
    assert boss2._weak_point_flash_point is None


def test_draw_pinta_las_oleadas_en_el_pase_de_mundo():
    """Task 5, Step 5.1 -- ``draw()`` debe iterar ``self._oleadas`` y pintar
    cada cresta viva en el pase de mundo (``OleadaDeLianas.dibujar_mundo``),
    igual que ya hace con proyectiles/esporas/skull. Se compara contra una
    superficie limpia del mismo color base: cualquier diferencia de píxeles
    confirma que algo se dibujó."""
    boss, _ = make_boss()
    boss._oleadas = [OleadaDeLianas(float(boss.rect.centerx), 1, bv.FLOOR_Y,
                                    bv.ARENA_X0, bv.ARENA_X1)]
    offset = pygame.Vector2(int(boss.rect.centerx) - 100, int(bv.FLOOR_Y) - 100)
    limpia = pygame.Surface((200, 200))
    limpia.fill((10, 10, 10))
    con_oleada = limpia.copy()
    boss.draw(con_oleada, offset)
    assert pygame.image.tobytes(con_oleada, "RGB") != pygame.image.tobytes(limpia, "RGB")


def test_grietas_de_vine_sweep_crecen_con_el_progreso_del_aviso():
    """Task 5, Step 5.1 -- las astas/grietas del aviso de VINE_SWEEP
    (reemplazo de la franja estática de ancho completo, spec §2.1) crecen
    con el progreso del telegraph: cerca del final del aviso (timer bajo)
    la grieta horizontal a la altura de las pezuñas debe ser más ancha que
    al principio (timer == SWEEP_TELEGRAPH, progreso ~0.0)."""
    boss, _ = make_boss()
    offset = pygame.Vector2(int(boss.rect.centerx) - 100, int(bv.FLOOR_Y) - 100)
    boss._telegraph = "VINE_SWEEP"
    color = boss._TELEGRAPH_WARN_COLOR
    fila_y = int(bv.FLOOR_Y - 2 - offset.y)

    def ancho_de_grieta(timer: float) -> int:
        boss._telegraph_timer = timer
        surface = pygame.Surface((200, 200))
        surface.fill((10, 10, 10))
        boss._draw_telegraphs(surface, offset)
        return sum(1 for x in range(surface.get_width())
                  if surface.get_at((x, fila_y))[:3] == color)

    ancho_inicio = ancho_de_grieta(bv.SWEEP_TELEGRAPH)     # progreso ~0.0
    ancho_final = ancho_de_grieta(0.01)                    # progreso ~1.0
    assert ancho_final > ancho_inicio, (
        "las grietas de VINE_SWEEP no crecen con el progreso del aviso")


# ──────────────────────────────────────────────
# Pulido AAA fase 2 (diseño 2026-08-21) — _frame_vivo() y destello de STOMP
# ──────────────────────────────────────────────

def test_frame_vivo_replica_la_seleccion_de_boss_base():
    """_frame_vivo() debe devolver EXACTAMENTE el mismo frame/destino que
    pintaría BossBase.draw() en este instante -- sin filtro de fase ni
    tinte de transición (boss no está transicionando en este test)."""
    boss, _ = make_boss()
    boss.facing_direction = 1
    vivo = boss._frame_vivo()
    assert vivo is not None
    frame, destino, clave = vivo
    anim_key = boss._get_animation_state()
    assert clave == (anim_key, boss._animation_frame, 1, boss.escala_de_fase)
    esperado_x = int(boss.position.x) + (boss.rect.width - frame.get_width()) // 2
    esperado_y = int(boss.position.y) + boss.rect.height - frame.get_height()
    assert destino == (esperado_x, esperado_y)


def test_frame_vivo_cachea_el_frame_escalado_por_clave():
    boss, _ = make_boss()
    boss.current_phase = 1
    boss.set_phases([bv.BossPhase(phase_index=0, health_threshold=12.0, attack_patterns=["STOMP"],
                                   movement_type="sine", speed_multiplier=1.0),
                      bv.BossPhase(phase_index=1, health_threshold=6.0, attack_patterns=["STOMP"],
                                   movement_type="bezier", speed_multiplier=1.5, escala=1.25)])
    boss.current_phase = 1
    v1 = boss._frame_vivo()
    v2 = boss._frame_vivo()
    assert v1 is not None and v2 is not None
    assert v1[0] is v2[0], "la segunda llamada con la misma clave debe reusar la Surface cacheada"
    assert len(boss._cache_frames_vivos) == 1


def test_frame_vivo_none_si_no_hay_frames_para_la_animacion():
    boss, _ = make_boss()
    boss._sprite_frames = {}  # fuerza el caso sin frames
    assert boss._frame_vivo() is None


def test_destello_de_stomp_dura_exactamente_flash_pisoton_frames_dibujados():
    boss, _ = make_boss()
    boss._flash_frames = bv.FLASH_PISOTON_FRAMES
    surface = pygame.Surface((200, 200))
    surface.fill((10, 10, 10))
    boss.draw(surface, pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100))
    assert boss._flash_frames == bv.FLASH_PISOTON_FRAMES - 1
    boss.draw(surface, pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100))
    assert boss._flash_frames == 0
    # una tercera llamada no debe fallar ni reintroducir el destello
    boss.draw(surface, pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100))
    assert boss._flash_frames == 0


# ──────────────────────────────────────────────
# Pulido AAA fase 2 (diseño 2026-08-21) — STOMP completo: puerto de efectos +
# cresta/anillo overlay (Tarea 4 del plan Parte 2)
# ──────────────────────────────────────────────

def test_do_stomp_llama_al_puerto_de_efectos_y_arma_flash_y_cresta():
    boss, _ = make_boss()
    registrados = EfectosRegistrados()
    boss.conectar_efectos(registrados)
    cx = float(boss.rect.centerx)
    boss._do_stomp()
    assert registrados.sacudidas == [(4.0, 0.2, (0.0, 1.0))]
    assert len(registrados.particulas_dirigidas_emitidas) == 1
    assert registrados.particulas_dirigidas_emitidas[0] == (cx, bv.FLOOR_Y, -90.0, POLVO_PISOTON)
    assert len(registrados.particulas_emitidas) == 1
    assert registrados.particulas_emitidas[0] == (cx, bv.FLOOR_Y - 20.0, HOJAS)
    assert boss._flash_frames == bv.FLASH_PISOTON_FRAMES
    assert boss._cresta_pisoton is not None
    assert boss._cresta_pisoton.centro_x == cx


def test_do_stomp_no_cambia_el_rect_de_dano_ni_los_tiempos():
    """El pulido visual NO debe tocar balance -- mismo rect/mismo STOMP_WINDOW
    que antes del diseño AAA fase 2."""
    boss, _ = make_boss()
    boss._do_stomp()
    assert boss._stomp_rect == pygame.Rect(boss.rect.centerx - 48, int(bv.FLOOR_Y) - 8, 96, 8)
    assert boss._stomp_window == bv.STOMP_WINDOW


def test_stomp_telegraph_ya_no_deja_estela_rectangular_y_polvo_durante_recover():
    """(B) del coordinador, Task 14 (2026-08-22): la llamada a
    ``self.efectos.estela(...)`` durante el aviso de STOMP se ELIMINA --
    ese rectángulo verde translúcido del tamaño del jefe se quedaba ENCIMA
    del ciervo mientras apenas se movía (zoom_stomp.png f1800-f1826:
    "bloque verde con el venado apenas visible dentro"). Reemplaza al test
    homónimo de la Task 4 (anotado aquí: antes esperaba >=5 estelas en 30
    frames de aviso, ahora exige CERO)."""
    boss, _ = make_boss()
    registrados = EfectosRegistrados()
    boss.conectar_efectos(registrados)
    boss._telegraph = "STOMP"
    boss._telegraph_timer = bv.STOMP_TELEGRAPH
    for _ in range(30):                     # 0.5s a 60fps: de sobra para varias cadencias de 3 frames
        boss._frames_vfx += 1
        boss._update_vfx(DT)
    assert registrados.estelas == [], (
        "el aviso de STOMP ya no debe pedir estela() -- el rectángulo verde tapaba al jefe")

    boss._telegraph = ""
    boss._stomp_recover = bv.STOMP_RECOVER
    registrados2 = EfectosRegistrados()
    boss.conectar_efectos(registrados2)
    for _ in range(int(bv.STOMP_RECOVER / DT) + 5):
        boss._frames_vfx += 1
        boss._update_vfx(DT)
    assert len(registrados2.particulas_emitidas) >= 1, "cadencia de 10 frames durante el recover debe emitir polvo"


def test_stomp_telegraph_pinta_anillo_no_la_raya_plana():
    import pygame
    boss, _ = make_boss()
    boss._telegraph = "STOMP"
    boss._telegraph_timer = bv.STOMP_TELEGRAPH
    surface = pygame.Surface((200, 200))
    surface.fill((10, 10, 10))
    offset = pygame.Vector2(int(boss.rect.centerx) - 100, int(bv.FLOOR_Y) - 100)
    boss._draw_telegraphs(surface, offset)
    color = boss._TELEGRAPH_WARN_COLOR
    raya_plana = pygame.Rect(int(boss.rect.centerx - 48 - offset.x), int(bv.FLOOR_Y - 6 - offset.y), 96, 4)
    pixeles_raya = [surface.get_at((raya_plana.x + i, raya_plana.y + 2))[:3] for i in range(0, 96, 8)]
    assert not all(p == color for p in pixeles_raya), "la raya 96x4 plana ya no debe pintarse completa"
    arr = pygame.surfarray.array3d(surface)
    import numpy as np
    assert np.all(arr == color, axis=-1).any(), "el anillo de caída sí debe pintar algo del color de aviso"


def test_stomp_window_pinta_cresta_overlay_no_la_barra_plana():
    import pygame
    boss, _ = make_boss()
    boss._do_stomp()
    surface = pygame.Surface((200, 200))
    surface.fill((10, 10, 10))
    offset = pygame.Vector2(int(boss.rect.centerx) - 100, int(bv.FLOOR_Y) - 100)
    boss._draw_telegraphs(surface, offset)
    barra_plana = boss._stomp_rect.move(int(-offset.x), int(-offset.y))
    pixeles_barra = [surface.get_at((barra_plana.x + i, barra_plana.y + 4))[:3] for i in range(0, 96, 8)]
    assert not all(p == (250, 220, 120) for p in pixeles_barra), (
        "la barra amarilla 96x8 sólida ya no debe pintarse completa")


# ──────────────────────────────────────────────
# Task 5 (pulido AAA fase 2, 2026-08-21/22) — SenalDeCastigo integrada:
# condición de apertura de la ventana de castigo y verificación de que el
# despacho directo desde _draw_telegraphs realmente pinta (vía la caché de
# siluetas de _senal, ya cableado en el Task 4 Step 9).
# ──────────────────────────────────────────────

@pytest.mark.parametrize("campo,valor", [
    ("_stomp_recover", 0.1),
    ("_charge_recover", 0.1),
    ("_sweep_rooted", 0.1),
])
def test_ventana_de_castigo_abierta_por_cada_fuente(campo, valor):
    boss, _ = make_boss()
    assert not boss._ventana_de_castigo_abierta()
    setattr(boss, campo, valor)
    assert boss._ventana_de_castigo_abierta()


def test_senal_de_castigo_se_pinta_durante_stomp_recover():
    import pygame
    boss, _ = make_boss()
    boss._stomp_recover = 0.3
    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))
    offset = pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100)
    surface_sin = surface.copy()
    boss._draw_telegraphs(surface_sin, offset)   # con _senal ya conectada, pero SIN llamar dibujar_overlay a mano
    # basta con que la caché de siluetas de _senal haya recibido al menos una clave
    assert boss._senal.tamano_cache() >= 1


# ──────────────────────────────────────────────
# Task 6 (pulido AAA fase 2, 2026-08-22) — Esporas: MOTAS en el aviso (ya
# cableado desde el Task 4 Step 6, se re-verifica aquí), POLEN en vuelo (ídem)
# y NUBE_ESPORA al expirar por distancia/vida o al impactar al jugador
# (nuevo en esta tarea).
# ──────────────────────────────────────────────

from src.stages.boss_venado.efectos_venado import NUBE_ESPORA, POLEN


def test_nube_espora_al_expirar_por_distancia():
    boss, _ = make_boss()
    registrados = EfectosRegistrados()
    boss.conectar_efectos(registrados)
    boss._projectiles.append({
        "type": "spore", "pos": pygame.Vector2(0.0, 0.0), "origin": pygame.Vector2(0.0, 0.0),
        "vel": pygame.Vector2(1000.0, 0.0), "damage": 0.25, "alive": True, "age": 0.0,
    })
    boss._update_projectiles(1.0)   # 1000px en 1s >> SPORE_RANGE=420
    assert len(registrados.particulas_emitidas) == 1
    x, y, config = registrados.particulas_emitidas[0]
    assert config is NUBE_ESPORA


def test_nube_espora_al_impactar_al_jugador():
    boss, _ = make_boss()
    registrados = EfectosRegistrados()
    boss.conectar_efectos(registrados)
    pos = pygame.Vector2(100.0, 100.0)
    boss._projectiles.append({
        "type": "spore", "pos": pos, "origin": pygame.Vector2(pos), "vel": pygame.Vector2(0, 0),
        "damage": 0.25, "alive": True, "age": 0.0,
    })

    class JugadorFalso:
        rect = pygame.Rect(int(pos.x) - 10, int(pos.y) - 10, 20, 20)
        hurtbox = rect
        velocity = pygame.Vector2(0, 0)
        centerx = rect.centerx

        def apply_damage(self, *a, **kw):
            pass

    boss.set_player_ref(JugadorFalso.rect)
    boss._check_player_contact(JugadorFalso())
    assert any(c is NUBE_ESPORA for (_, _, c) in registrados.particulas_emitidas)


def test_polen_por_espora_viva_cada_5_frames():
    boss, _ = make_boss()
    registrados = EfectosRegistrados()
    boss.conectar_efectos(registrados)
    boss._projectiles.append({
        "type": "spore", "pos": pygame.Vector2(50.0, 50.0), "origin": pygame.Vector2(50.0, 50.0),
        "vel": pygame.Vector2(0.0, 0.0), "damage": 0.25, "alive": True, "age": 0.0,
    })
    for _ in range(30):
        boss._frames_vfx += 1
        boss._update_vfx(DT)
    assert any(c is POLEN for (_, _, c) in registrados.particulas_emitidas)


def test_motas_durante_telegraph_de_mushroom_spore():
    boss, _ = make_boss()
    registrados = EfectosRegistrados()
    boss.conectar_efectos(registrados)
    boss._telegraph = "MUSHROOM_SPORE"
    boss._telegraph_timer = bv.SPORE_TELEGRAPH
    for _ in range(20):
        boss._frames_vfx += 1
        boss._update_vfx(DT)
    assert len(registrados.particulas_dirigidas_emitidas) >= 1
    _x, _y, angulo, config = registrados.particulas_dirigidas_emitidas[0]
    assert angulo == -90.0
    from src.stages.boss_venado.efectos_venado import MOTAS
    assert config is MOTAS


# ──────────────────────────────────────────────
# Task 7 (pulido AAA fase 2, 2026-08-22) — CHARGE de fase 2: la cadencia de
# telegraph/carrera ya quedó gateada por current_phase en el Task 4 Step 6
# (se re-verifica aquí); lo nuevo es el VFX del choque con pared, que solo
# debe aparecer en fase 2 y con el ángulo de escombros según el lado.
# ──────────────────────────────────────────────

from src.stages.boss_venado.efectos_venado import POLVO_RASPADO, POLVO_PEZUNAS, ESCOMBROS


def test_charge_telegraph_vfx_solo_en_fase_2():
    boss, _ = make_boss()
    boss.current_phase = 0
    registrados0 = EfectosRegistrados()
    boss.conectar_efectos(registrados0)
    boss._telegraph = "CHARGE"
    for _ in range(20):
        boss._frames_vfx += 1
        boss._update_vfx(DT)
    assert registrados0.particulas_dirigidas_emitidas == [], "fase 0 (índice 0) no debe emitir POLVO_RASPADO"

    boss.current_phase = 1
    registrados1 = EfectosRegistrados()
    boss.conectar_efectos(registrados1)
    for _ in range(20):
        boss._frames_vfx += 1
        boss._update_vfx(DT)
    assert any(c is POLVO_RASPADO for (_, _, _, c) in registrados1.particulas_dirigidas_emitidas)


def test_charge_active_vfx_solo_en_fase_2():
    """(B) del coordinador, Task 14 (2026-08-22): la embestida ya NO pide
    ``efectos.estela()`` (rectángulo verde del motor) -- agrega fantasmas
    de SPRITE propios a ``boss._fantasmas`` en su lugar. Reemplaza al test
    homónimo de la Task 7 (anotado aquí: antes esperaba >=1 en
    ``registrados1.estelas``, ahora exige CERO ahí y >=1 en
    ``boss._fantasmas.cantidad()``)."""
    boss, _ = make_boss()
    boss._charge_active = True
    boss._charge_direction = 1
    boss.current_phase = 0
    registrados0 = EfectosRegistrados()
    boss.conectar_efectos(registrados0)
    for _ in range(20):
        boss._frames_vfx += 1
        boss._update_vfx(DT)
    assert registrados0.estelas == [] and registrados0.particulas_dirigidas_emitidas == []
    assert boss._fantasmas.cantidad() == 0, "fase 0 (índice 0) no debe agregar fantasmas"

    boss.current_phase = 1
    registrados1 = EfectosRegistrados()
    boss.conectar_efectos(registrados1)
    for _ in range(20):
        boss._frames_vfx += 1
        boss._update_vfx(DT)
    assert registrados1.estelas == [], "el puerto estela() ya no se usa -- ver docstring del puerto"
    assert boss._fantasmas.cantidad() >= 1, "la embestida en fase 2 debe agregar fantasmas de sprite"
    assert any(c is POLVO_PEZUNAS for (_, _, _, c) in registrados1.particulas_dirigidas_emitidas)


def test_charge_choque_con_pared_vfx_solo_en_fase_2_y_angulo_por_lado():
    boss, _ = make_boss()
    boss.current_phase = 0
    boss._charge_active, boss._charge_direction = True, -1
    boss.position.x = bv.ARENA_X0 + 1
    registrados0 = EfectosRegistrados()
    boss.conectar_efectos(registrados0)
    boss._update_charge(1.0)
    assert registrados0.sacudidas == [] and registrados0.particulas_dirigidas_emitidas == []

    boss.current_phase = 1
    boss._charge_active, boss._charge_direction = True, -1
    boss.position.x = bv.ARENA_X0 + 1
    registrados_izq = EfectosRegistrados()
    boss.conectar_efectos(registrados_izq)
    boss._update_charge(1.0)
    assert registrados_izq.sacudidas == [(3.0, 0.15, (-1.0, 0.0))]
    assert len(registrados_izq.particulas_dirigidas_emitidas) == 1
    x, y, angulo, config = registrados_izq.particulas_dirigidas_emitidas[0]
    assert angulo == 0.0 and config is ESCOMBROS

    boss._charge_active, boss._charge_direction = True, 1
    boss.position.x = bv.ARENA_X1 - 16.0 - float(boss.rect.width) - 1
    registrados_der = EfectosRegistrados()
    boss.conectar_efectos(registrados_der)
    boss._update_charge(1.0)
    assert registrados_der.sacudidas == [(3.0, 0.15, (1.0, 0.0))]
    _x, _y, angulo_der, config_der = registrados_der.particulas_dirigidas_emitidas[0]
    assert angulo_der == 180.0 and config_der is ESCOMBROS


# ──────────────────────────────────────────────
# Correcciones visuales del coordinador -- Task 14 (2026-08-22): anillo de
# castigo, fantasmas de sprite, tinte de transición enmascarado
# ──────────────────────────────────────────────

def test_fantasmas_jamas_se_agregan_durante_el_aviso_de_stomp():
    """(B) del coordinador: la carrera de fase >= 1 agrega fantasmas, pero
    el aviso de STOMP (ningún desplazamiento real que "arrastrar") NUNCA
    debe hacerlo -- distingue el gate de _charge_active del gate viejo de
    _telegraph == "STOMP" que sí llamaba estela()."""
    boss, _ = make_boss()
    boss.current_phase = 1
    boss._telegraph = "STOMP"
    boss._telegraph_timer = bv.STOMP_TELEGRAPH
    for _ in range(30):
        boss._frames_vfx += 1
        boss._update_vfx(DT)
    assert boss._fantasmas.cantidad() == 0, "el aviso de STOMP no debe agregar fantasmas de sprite"


def test_cancelar_ataques_en_vuelo_limpia_los_fantasmas():
    """M-1 extendido a (B): el salto de teletransporte de fase invalida la
    geometría vieja -- los fantasmas dejados en la posición ANTERIOR no
    deben sobrevivir, igual que las cajas de daño en vuelo."""
    boss, _ = make_boss()
    boss.current_phase = 1
    boss._fantasmas.agregar(boss._frame_vivo()[0], (0.0, 0.0))
    assert boss._fantasmas.cantidad() >= 1
    boss._cancelar_ataques_en_vuelo()
    assert boss._fantasmas.cantidad() == 0


def test_on_defeated_limpia_los_fantasmas():
    boss, _ = make_boss()
    boss.current_phase = 1
    boss._fantasmas.agregar(boss._frame_vivo()[0], (0.0, 0.0))
    assert boss._fantasmas.cantidad() >= 1
    boss.on_defeated()
    assert boss._fantasmas.cantidad() == 0


def test_draw_pinta_los_fantasmas_antes_del_cuerpo():
    """(B): dibujar_mundo() de los fantasmas debe correr ANTES de
    super().draw() (painter's order: los fantasmas quedan DETRÁS del
    cuerpo). Se mide agregando un fantasma en la MISMA posición que el
    cuerpo real -- si el orden fuera al revés el cuerpo opaco taparía
    completamente al fantasma y el trazo no se notaría, pero como este
    candado solo verifica que draw() no truene y que el puerto se haya
    consumido, se comprueba por un efecto observable más simple: tras
    draw(), la lista de fantasmas sigue teniendo el mismo contenido (drawn,
    no consumido) -- el candado de ORDEN real vive en los filmstrips
    (Step 14.6), aquí solo se fija el contrato de que draw() no lo salta."""
    boss, _ = make_boss()
    boss.current_phase = 1
    frame, destino, _clave = boss._frame_vivo()
    boss._fantasmas.agregar(frame, destino)
    surface = pygame.Surface((200, 200))
    surface.fill((10, 10, 10))
    boss.draw(surface, pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100))
    assert boss._fantasmas.cantidad() == 1, "draw() no debe consumir/purgar los fantasmas"


# ──────────────────────────────────────────────
# (C) del coordinador, Task 14: B-038 -- compensación del tinte amarillo
# aditivo de BossBase.draw() durante is_transitioning
# ──────────────────────────────────────────────

def test_transicion_tine_el_cuerpo_sin_cuadrado_de_fondo():
    """B-038: durante is_transitioning, BossBase.draw() (motor) suma
    (200,200,0,80) con BLEND_RGBA_ADD sobre TODO el rect del frame,
    incluidos los píxeles transparentes -- el jefe se ve como un cuadrado
    amarillo semitransparente (zoom_sweep.png f5808). La compensación en
    nuestro draw() reemplaza la llamada a super().draw() mientras dura la
    transición: sobre una superficie negra, un píxel dentro del rect pero
    FUERA del cuerpo debe quedar (0,0,0) y un píxel del cuerpo debe quedar
    teñido (canal rojo y verde por encima de los del frame sin tinte)."""
    import numpy as np

    boss, _ = make_boss()
    boss.is_transitioning = True
    frame, destino, _clave = boss._frame_vivo()
    # localiza un pixel transparente y uno opaco DEL FRAME REAL por su
    # canal alfa -- no se asume la forma del sprite (nunca la esquina del
    # rect: podría caer dentro de la silueta según el sprite real).
    alfa = pygame.surfarray.array_alpha(frame)
    coords_transparentes = np.argwhere(alfa == 0)
    coords_opacas = np.argwhere(alfa == 255)
    assert coords_transparentes.size > 0 and coords_opacas.size > 0, (
        "el sprite de prueba debe tener zonas transparentes y opacas para que el candado tenga sentido")
    fx_t, fy_t = (int(v) for v in coords_transparentes[0])
    fx_o, fy_o = (int(v) for v in coords_opacas[len(coords_opacas) // 2])
    sin_tinte = frame.get_at((fx_o, fy_o))[:3]

    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 255))
    camera_offset = pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100)
    boss.draw(surface, camera_offset)

    dx_t = int(destino[0] - camera_offset.x) + fx_t
    dy_t = int(destino[1] - camera_offset.y) + fy_t
    pixel_transparente = surface.get_at((dx_t, dy_t))[:3]
    assert pixel_transparente == (0, 0, 0), (
        f"un pixel transparente del frame se tiñó -- deberia seguir negro: {pixel_transparente}")

    dx_o = int(destino[0] - camera_offset.x) + fx_o
    dy_o = int(destino[1] - camera_offset.y) + fy_o
    pixel_opaco = surface.get_at((dx_o, dy_o))[:3]
    assert pixel_opaco[0] > sin_tinte[0] and pixel_opaco[1] > sin_tinte[1], (
        f"el cuerpo debe quedar teñido de amarillo: {pixel_opaco} vs sin tinte {tuple(sin_tinte)}")


def test_transicion_no_muta_el_frame_cacheado_del_motor():
    """Efecto colateral positivo de la compensación: al NO llamar a
    super().draw() durante la transición, el bug de mutación del motor
    (BossBase.draw hace ``frame.blit(overlay, ..., BLEND_RGBA_ADD)``
    directo sobre la Surface CACHEADA en ``self._sprite_frames``, sin
    copiarla primero) nunca se ejercita desde nuestro boss -- el frame
    original debe seguir intacto después de dibujar en transición."""
    boss, _ = make_boss()
    anim_key = boss._get_animation_state()
    frame_original = boss._sprite_frames[anim_key][0]
    copia_previa = frame_original.copy()
    boss.is_transitioning = True
    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    boss.draw(surface, pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100))
    assert pygame.image.tobytes(frame_original, "RGBA") == pygame.image.tobytes(copia_previa, "RGBA"), (
        "draw() en transición no debe mutar la Surface cacheada del motor")
