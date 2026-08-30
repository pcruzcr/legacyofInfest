"""
Módulo: test_la_soda_cocinero
Sistema: stages.stage1_2_la_soda
Unidad académica: Unidad II (Vectores) / Unidad III (Curvas) -- ver el
docstring de `ShooterCocinero` en `entities.py` para el detalle completo.
Descripción: pruebas de AUD-651 -- el `ShooterCocinero` sube a 5.0 de vida
y agrega una fase 2 "enfurecido" al <=50%: cooldown x0.6, telegrafiado
x0.75, lanzamiento doble ±12°, tinte rojizo + `SHOW_MESSAGE` único.

Sólo importa `_construir_escena_la_soda` de `test_la_soda.py` -- ese
archivo lo edita en paralelo otro subagente (barra de jefe/sacudida) y no
se toca acá.
"""
from __future__ import annotations

import math

import pygame
import pytest

from src.engine.core.events import Events
from src.framework.entities.enemy_base import EnemyState
from src.stages.stage1_2_la_soda.entities import ShooterCocinero
from src.stages.stage1_2_la_soda.test_la_soda import _construir_escena_la_soda

DT = 1 / 60


def _pygame_listo() -> None:
    if not pygame.get_init():
        pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


@pytest.fixture(scope="module", autouse=True)
def _video():
    """`pygame.init()` con una superficie liviana -- mismo patrón que
    `test_la_soda_sprites.py::_video` (archivo aparte, así que su fixture
    no alcanza a éste; `Stage1_2_LaSoda.__init__` construye `DrawingSystem`,
    que necesita `pygame.font` inicializado)."""
    _pygame_listo()
    yield

#: Mismas fracciones que `_muestrear_colores_de_sprite` en `entities.py`
#: -- ya probadas para caer dentro del cuerpo opaco de las cinco hojas de
#: AUD-648 (incluida `sprite_cocinero.png`), así que sirven igual acá
#: para muestrear el resultado DIBUJADO en vez del cuadro crudo.
_PUNTOS_MUESTREO = [(0.35, 0.35), (0.6, 0.5), (0.45, 0.7), (0.7, 0.35), (0.3, 0.6)]


def _cocinero(sc) -> ShooterCocinero:
    """El `ShooterCocinero` vivo de la escena -- mismo patrón que
    `TestElCocineroNoQuedaFlotando._cocinero` en `test_la_soda.py`."""
    return next(
        e for e in sc._stage_data.entity_list if isinstance(e, ShooterCocinero)
    )


def _escena_con_cocinero():
    """Escena real, con la cámara ya clampeada al cuarto interior (donde
    vive el cocinero) vía `disarm_to_interior()` -- mismo patrón que
    `TestElCocineroNoQuedaFlotando`/`TestPuertaDelCocinero` en
    `test_la_soda.py`.

    Sin esto, `culling.se_simula` (`framework/stage/culling.py:109-122`)
    no le llama `update()` al cocinero mientras la cámara siga clampeada
    al cuarto EXTERIOR (`_RoomTransition.apply_camera_box`, llamado cada
    fotograma desde `Stage1_2_LaSoda.update()`): el cocinero no tiene
    `siempre_activo` ni proyectiles en vuelo al empezar, así que queda
    fuera de la "zona activa" (encuadre de cámara + margen) y ninguna
    prueba de esta clase vería avanzar la fase 2, el lanzamiento doble ni
    nada más de `update()` -- diagnosticado en headless: sin este
    `disarm_to_interior()`, `_fase2` se queda en `False` para siempre y
    `state` congelado en `LAUNCHED` tras un golpe, ambos síntomas de que
    `update()` sencillamente nunca corre."""
    sc = _construir_escena_la_soda()
    sc._room_transition.disarm_to_interior()
    return sc, _cocinero(sc)


def _avanzar(sc, frames: int, dt: float = DT) -> None:
    """`frames` fotogramas reales de la escena -- dispatch + update, mismo
    patrón que ya usan `TestElCocineroNoQuedaFlotando`/`TestPuertaDelCocinero`
    en `test_la_soda.py`. Un solo fotograma alcanza para que
    `StageScene` arme `_player_ref`/`_collision_rects` del cocinero (ver
    `stage_scene.py:1102`), que `_fire()` necesita para apuntar."""
    for _ in range(frames):
        sc.context.event_bus.dispatch()
        sc.update(dt)


def _pixeles_dibujados(cocinero: ShooterCocinero) -> list[tuple[int, int, int, int]]:
    """Dibuja al cocinero en una `Surface` chica y devuelve los colores
    RGBA de `_PUNTOS_MUESTREO` sobre el cuadro de 32x32 -- traduce las
    mismas fracciones que usa `_muestrear_colores_de_sprite` (cuerpo
    opaco garantizado) del espacio del cuadro al de la `Surface` de
    destino, con el mismo offset que usa `draw()` (`ox`/`oy`,
    `entities.py`)."""
    surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    camera_offset = pygame.Vector2(cocinero.position.x - 16.0, cocinero.position.y - 16.0)
    cocinero.draw(surface, camera_offset)
    ox = (cocinero.rect.width - cocinero._sprite_fw) // 2
    oy = cocinero.rect.height - cocinero._sprite_fh
    base_x = int(cocinero.position.x - camera_offset.x) + ox
    base_y = int(cocinero.position.y - camera_offset.y) + oy
    colores = []
    for fx, fy in _PUNTOS_MUESTREO:
        x = base_x + int(cocinero._sprite_fw * fx)
        y = base_y + int(cocinero._sprite_fh * fy)
        if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
            colores.append(tuple(surface.get_at((x, y))))
    return colores


class TestCocineroEnfurecido:
    """AUD-651 -- `ShooterCocinero` con 5.0 de vida y fase 2 "enfurecido"."""

    # -- 1. max_health sube a 5.0 --------------------------------------

    def test_max_health_es_5(self) -> None:
        sc, cocinero = _escena_con_cocinero()
        assert cocinero.max_health == 5.0

    # -- 2. con vida > 50%, los tiempos son los normales -----------------

    def test_con_vida_por_encima_del_50_por_ciento_los_tiempos_son_normales(self) -> None:
        sc, cocinero = _escena_con_cocinero()
        _avanzar(sc, 5)
        assert cocinero.current_health > cocinero.max_health * 0.5
        assert cocinero._fase2 is False
        assert cocinero.fire_rate == pytest.approx(0.5)
        assert cocinero._telegraph_duration == pytest.approx(0.4)

    # -- 3. al bajar a <=50%, cambian cooldown y telegrafiado ------------

    def test_al_bajar_al_50_por_ciento_entra_en_fase2_y_cambian_los_tiempos(self) -> None:
        sc, cocinero = _escena_con_cocinero()
        _avanzar(sc, 1)
        # Vida exacta al 50% (5.0 -> 2.5): el umbral es "<=", así que esto
        # ya tiene que activar la fase 2.
        cocinero.apply_hit(2.5, (cocinero.rect.centerx - 40.0, cocinero.rect.centery))
        assert cocinero.current_health == pytest.approx(2.5)
        assert cocinero._fase2 is False, "apply_hit no debería activar la fase 2 por sí solo"
        _avanzar(sc, 1)
        assert cocinero._fase2 is True
        assert cocinero.fire_rate == pytest.approx(0.5 / 0.6)
        assert cocinero._telegraph_duration == pytest.approx(0.4 * 0.75)

    def test_la_fase2_no_se_reactiva_ni_cambia_los_tiempos_de_nuevo(self) -> None:
        """Golpear de nuevo estando ya en fase 2 no debe volver a dividir
        `fire_rate`/multiplicar `_telegraph_duration` -- `_fase2` es la
        guardia contra re-entradas (ver el docstring de `_entrar_en_fase2`
        en `entities.py`)."""
        sc, cocinero = _escena_con_cocinero()
        _avanzar(sc, 1)
        cocinero.apply_hit(3.0, (cocinero.rect.centerx - 40.0, cocinero.rect.centery))
        _avanzar(sc, 1)
        assert cocinero._fase2 is True
        fire_rate_fase2 = cocinero.fire_rate
        telegraph_fase2 = cocinero._telegraph_duration
        # `EnemyShooter`/`EnemyBase` arman `invincibility_duration=0.4s`
        # (`enemy_shooter.py:180`) tras CUALQUIER golpe no letal -- hay que
        # esperar a que se agote para que este segundo golpe conecte de
        # verdad y no sea un no-op silencioso (`apply_hit`,
        # `enemy_base.py:507-508`).
        _avanzar(sc, 30)
        vida_antes = cocinero.current_health
        cocinero.apply_hit(0.3, (cocinero.rect.centerx - 40.0, cocinero.rect.centery))
        assert cocinero.current_health < vida_antes, "el segundo golpe no conectó (no-op)"
        _avanzar(sc, 1)
        assert cocinero.fire_rate == pytest.approx(fire_rate_fase2)
        assert cocinero._telegraph_duration == pytest.approx(telegraph_fase2)

    # -- 4. lanzamiento doble: dos proyectiles, ángulos distintos ---------

    def test_lanzamiento_doble_crea_un_segundo_proyectil_con_angulo_distinto(self) -> None:
        sc, cocinero = _escena_con_cocinero()
        _avanzar(sc, 1)
        cocinero._entrar_en_fase2()
        assert len(cocinero._active_projectiles) == 0

        disparo_hecho = cocinero._fire()
        assert disparo_hecho is True
        assert len(cocinero._active_projectiles) == 1, (
            "el primer proyectil nace en el acto, el segundo debe quedar agendado"
        )
        primero = cocinero._active_projectiles[0]
        angulo_primero = math.degrees(math.atan2(primero.velocity.y, primero.velocity.x))
        # Capturado ACÁ, antes de avanzar ningún fotograma: `primero` es
        # la misma instancia viva que se sigue moviendo con cada
        # `_avanzar` de abajo, así que comparar su `position` al final
        # del test mediría cuánto viajó, no de dónde salió.
        origen_primero = pygame.Vector2(primero.position)

        # Un fotograma antes de que se cumpla la demora: todavía no debe
        # existir el segundo.
        _avanzar(sc, round(ShooterCocinero.SEGUNDO_DISPARO_RETRASO * 60) - 1)
        assert len(cocinero._active_projectiles) == 1
        _avanzar(sc, 2)
        assert len(cocinero._active_projectiles) == 2, (
            "el lanzamiento doble no creó el segundo proyectil tras "
            "SEGUNDO_DISPARO_RETRASO"
        )
        segundo = cocinero._active_projectiles[1]
        angulo_segundo = math.degrees(math.atan2(segundo.velocity.y, segundo.velocity.x))
        diferencia = abs(angulo_segundo - angulo_primero)
        assert diferencia == pytest.approx(ShooterCocinero.SEGUNDO_DISPARO_ANGULO, abs=0.5), (
            f"el segundo proyectil debería salir a "
            f"{ShooterCocinero.SEGUNDO_DISPARO_ANGULO}° del primero, dio {diferencia:.2f}°"
        )
        # Mismo origen que el primero (no vuelve a apuntar al jugador) y
        # mismo daño.
        assert segundo.position.x == pytest.approx(origen_primero.x, abs=0.5)
        assert segundo.position.y == pytest.approx(origen_primero.y, abs=0.5)
        assert segundo.damage == pytest.approx(primero.damage)

    def test_sin_fase2_un_disparo_no_agenda_un_segundo_proyectil(self) -> None:
        sc, cocinero = _escena_con_cocinero()
        _avanzar(sc, 1)
        assert cocinero._fase2 is False
        cocinero._fire()
        assert len(cocinero._active_projectiles) == 1
        _avanzar(sc, round(ShooterCocinero.SEGUNDO_DISPARO_RETRASO * 60) + 5)
        assert len(cocinero._active_projectiles) == 1, (
            "en fase 1 no debería aparecer un segundo proyectil"
        )

    # -- 5. SHOW_MESSAGE se emite exactamente una vez ---------------------

    def test_show_message_de_enfurecido_se_emite_exactamente_una_vez(self) -> None:
        sc, cocinero = _escena_con_cocinero()
        mensajes: list[dict] = []

        def _escuchar(**datos: object) -> None:
            if datos.get("text") == ShooterCocinero.MENSAJE_ENFURECIDO:
                mensajes.append(datos)

        sc.context.event_bus.subscribe(Events.SHOW_MESSAGE, _escuchar)
        _avanzar(sc, 1)
        cocinero.apply_hit(3.5, (cocinero.rect.centerx - 40.0, cocinero.rect.centery))
        _avanzar(sc, 90)  # 1.5s -- de sobra para que el bus despache el evento
        # Un golpe más, ya en fase 2: no debe reencolar el mismo aviso.
        cocinero.apply_hit(0.3, (cocinero.rect.centerx - 40.0, cocinero.rect.centery))
        _avanzar(sc, 90)
        assert len(mensajes) == 1, f"SHOW_MESSAGE de enfurecido se emitió {len(mensajes)} veces"

    # -- 6. el sprite queda teñido de rojizo en fase 2 ---------------------

    def test_el_sprite_queda_tenido_de_rojo_en_fase2(self) -> None:
        sc, cocinero = _escena_con_cocinero()
        _avanzar(sc, 1)

        colores_fase1 = _pixeles_dibujados(cocinero)
        opacos_fase1 = [c for c in colores_fase1 if c[3] > 10]
        assert opacos_fase1, "no se encontró ningún píxel opaco del cocinero en fase 1"

        cocinero._entrar_en_fase2()
        colores_fase2 = _pixeles_dibujados(cocinero)
        opacos_fase2 = [c for c in colores_fase2 if c[3] > 10]
        assert opacos_fase2, "no se encontró ningún píxel opaco del cocinero en fase 2"

        dominante_rojo = [r >= g and r >= b for r, g, b, _a in opacos_fase2]
        assert any(dominante_rojo), (
            f"ningún píxel muestreado en fase 2 quedó con el canal rojo "
            f"dominante: {opacos_fase2!r}"
        )
        # El multiplicador (255,150,150) deja el canal rojo intacto y
        # reduce verde/azul -- comprobado sobre el mismo punto de muestreo
        # antes/después, no sólo "algún" punto.
        for (r1, g1, b1, a1), (r2, g2, b2, a2) in zip(colores_fase1, colores_fase2):
            if a1 <= 10 or a2 <= 10:
                continue
            assert r2 == pytest.approx(r1, abs=2)
            assert g2 <= g1
            assert b2 <= b1

    # -- 7. respawn: nueva instancia, fase 1, 5.0 de vida ------------------

    def test_respawn_repone_el_cocinero_en_fase1_con_5_de_vida(self) -> None:
        sc, cocinero = _escena_con_cocinero()
        _avanzar(sc, 1)
        cocinero.apply_hit(3.5, (cocinero.rect.centerx - 40.0, cocinero.rect.centery))
        _avanzar(sc, 5)
        assert cocinero._fase2 is True
        # Esperar a que expire `invincibility_duration` (0.4s = 24
        # fotogramas, `enemy_shooter.py:180`) del primer golpe -- si no,
        # el golpe letal de abajo es un no-op silencioso (`apply_hit`,
        # `enemy_base.py:507-508`) y el cocinero nunca muere.
        _avanzar(sc, 25)
        cocinero.apply_hit(10.0, (cocinero.rect.centerx - 40.0, cocinero.rect.centery))
        _avanzar(sc, 40)
        assert not cocinero.is_alive

        sc.respawn()

        nuevo = _cocinero(sc)
        assert nuevo is not cocinero, "el respawn debería recrear la entidad, no reciclarla"
        assert nuevo.max_health == 5.0
        assert nuevo.current_health == 5.0
        assert nuevo._fase2 is False
        assert nuevo.fire_rate == pytest.approx(0.5)
        assert nuevo._telegraph_duration == pytest.approx(0.4)
        assert nuevo.state != EnemyState.DYING
