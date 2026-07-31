"""
Module: test_jungle_frog
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: II (Vectores)
Description: Normalizacion, distancia euclidiana, producto punto y alcance.

Ejecutar toda la suite con:
   python -m pytest src/stages/stage1_1/tests/ -v
"""
from __future__ import annotations

import math

import pygame
import pytest

from src.stages.stage1_1.entities.jungle_frog import (
    FrogProjectile,
    JungleFrog,
)

# ── Unidad II — normalización y rapidez constante ───────────────────

@pytest.mark.parametrize("angulo_grados", list(range(0, 360, 15)))
def test_rapidez_del_proyectil_es_igual_en_toda_direccion(angulo_grados: int) -> None:
    """La normalización garantiza ‖v‖ = RAPIDEZ sin importar el ángulo.

    Es la propiedad que justifica usar vec2_normalize: si se disparara con el
    vector diferencia sin normalizar, un objetivo lejano daría un proyectil
    rapidísimo y uno cercano uno lentísimo.
    """
    origen = pygame.Vector2(100.0, 100.0)
    rad = math.radians(angulo_grados)
    objetivo = origen + pygame.Vector2(math.cos(rad), math.sin(rad)) * 137.0

    proyectil = FrogProjectile(origen, objetivo, speed=90.0)

    assert proyectil.velocity.length() == pytest.approx(90.0, abs=1e-6)


def test_rapidez_no_depende_de_la_distancia_al_objetivo() -> None:
    """Dos objetivos en la misma dirección pero a distinta distancia producen
    exactamente la misma velocidad."""
    origen = pygame.Vector2(0.0, 0.0)
    cerca = FrogProjectile(origen, pygame.Vector2(10.0, 0.0), speed=90.0)
    lejos = FrogProjectile(origen, pygame.Vector2(500.0, 0.0), speed=90.0)

    assert cerca.velocity.x == pytest.approx(lejos.velocity.x, abs=1e-6)
    assert cerca.velocity.y == pytest.approx(lejos.velocity.y, abs=1e-6)


def test_direccion_apunta_al_objetivo() -> None:
    """El vector unitario apunta del origen hacia el objetivo."""
    proyectil = FrogProjectile(
        pygame.Vector2(50.0, 50.0), pygame.Vector2(50.0, 150.0), speed=60.0,
    )
    assert proyectil.velocity.x == pytest.approx(0.0, abs=1e-6)
    assert proyectil.velocity.y == pytest.approx(60.0, abs=1e-6)


def test_objetivo_sobre_el_origen_no_revienta() -> None:
    """vec2_normalize devuelve el vector cero si la longitud es ~0.
    El proyectil debe quedar inerte, no lanzar ZeroDivisionError."""
    p = pygame.Vector2(80.0, 80.0)
    proyectil = FrogProjectile(p, pygame.Vector2(p), speed=90.0)

    assert proyectil.velocity.length() == pytest.approx(0.0, abs=1e-9)


# ── Unidad II — integración del movimiento ──────────────────────────

def test_el_proyectil_avanza_segun_su_velocidad() -> None:
    """p(t+Δt) = p(t) + v·Δt (Euler explícito, v constante)."""
    proyectil = FrogProjectile(
        pygame.Vector2(0.0, 0.0), pygame.Vector2(100.0, 0.0), speed=50.0,
    )
    proyectil.update(0.5)

    assert proyectil.position.x == pytest.approx(25.0, abs=1e-6)
    assert proyectil.position.y == pytest.approx(0.0, abs=1e-6)


def test_el_proyectil_muere_al_superar_su_alcance() -> None:
    """El descarte usa vec2_length sobre el desplazamiento desde el origen."""
    proyectil = FrogProjectile(
        pygame.Vector2(0.0, 0.0), pygame.Vector2(1.0, 0.0),
        speed=100.0, max_range=50.0,
    )
    proyectil.update(0.4)          # recorre 40 px < 50
    assert proyectil.is_active

    proyectil.update(0.2)          # acumula 60 px > 50
    assert not proyectil.is_active


def test_el_proyectil_sigue_vivo_dentro_de_su_alcance() -> None:
    proyectil = FrogProjectile(
        pygame.Vector2(0.0, 0.0), pygame.Vector2(0.0, 1.0),
        speed=100.0, max_range=200.0,
    )
    for _ in range(10):
        proyectil.update(0.1)      # 100 px en total
    assert proyectil.is_active


# ── Unidad II — ángulo de orientación ───────────────────────────────

def test_el_angulo_coincide_con_atan2() -> None:
    """θ = atan2(dy, dx), usado para orientar el sprite."""
    origen = pygame.Vector2(0.0, 0.0)
    proyectil = FrogProjectile(origen, pygame.Vector2(1.0, 1.0), speed=10.0)

    assert proyectil.angle == pytest.approx(math.atan2(1.0, 1.0), abs=1e-6)


def test_el_rect_sigue_a_la_posicion() -> None:
    """El hitbox se define en espacio local y se traslada al mundo con
    (tx, ty) = position."""
    proyectil = FrogProjectile(
        pygame.Vector2(10.0, 20.0), pygame.Vector2(110.0, 20.0), speed=100.0,
    )
    proyectil.update(0.1)

    assert proyectil.rect.x == int(proyectil.position.x)
    assert proyectil.rect.y == int(proyectil.position.y)


# ════════════════════════════════════════════════════════════════════
# JungleFrog — Unidad II: distancia euclidiana y producto punto
# ════════════════════════════════════════════════════════════════════

def _rana(**kw) -> JungleFrog:
    return JungleFrog(pygame.Vector2(100.0, 100.0), **kw)


def _jugador_en(rana: JungleFrog, dx: float, dy: float) -> pygame.Rect:
    """Coloca un rect de jugador desplazado (dx, dy) del centro de la rana."""
    cx, cy = rana.rect.center
    r = pygame.Rect(0, 0, 16, 32)
    r.center = (int(cx + dx), int(cy + dy))
    return r


def test_la_y_del_tmx_marca_los_pies_de_la_rana() -> None:
    """Convención del profesor: la `y` de un objeto de enemigo en el TMX es
    la posición de los PIES, no la esquina superior.

    `EnemyWalker.__init__` lo hace explícito en enemy_walker.py:56 con
    `self.position.y -= self.rect.height`. Sin ese ajuste la entidad queda
    enterrada su propia altura dentro del terreno — que es exactamente el
    bug que se observó al jugar.
    """
    Y_SUELO = 200.0
    rana = JungleFrog(pygame.Vector2(100.0, Y_SUELO))

    pies = rana.position.y + rana.rect.height
    assert pies == pytest.approx(Y_SUELO, abs=0.5)


def test_sin_jugador_no_hay_deteccion() -> None:
    assert _rana()._check_detection_range() is False


def test_no_detecta_al_jugador_fuera_del_radio() -> None:
    rana = _rana(detection_range_x=96.0)
    rana.set_player_ref(_jugador_en(rana, 150.0, 0.0))

    assert rana._check_detection_range() is False


def test_detecta_al_jugador_dentro_del_radio() -> None:
    rana = _rana(detection_range_x=96.0)
    rana.set_player_ref(_jugador_en(rana, 60.0, 0.0))

    assert rana._check_detection_range() is True


def test_la_deteccion_es_radial_y_no_rectangular() -> None:
    """Prueba clave: el framework detecta con una caja alineada a los ejes
    (|dx| ≤ range_x y |dy| ≤ range_y). La rana debe usar la DISTANCIA
    EUCLIDIANA, que es lo que pide la Unidad II.

    Con radio 96, un jugador en (90, 60) cae DENTRO de la caja
    (90 ≤ 96 y 60 ≤ 64) pero FUERA del círculo:
        d = √(90² + 60²) = √11700 ≈ 108,2 > 96
    """
    rana = _rana(detection_range_x=96.0, detection_range_y=64.0)
    rana.set_player_ref(_jugador_en(rana, 90.0, 60.0))

    assert math.hypot(90.0, 60.0) > 96.0        # fuera del círculo
    assert abs(90.0) <= 96.0 and abs(60.0) <= 64.0   # dentro de la caja
    assert rana._check_detection_range() is False


def test_el_facing_es_el_signo_del_producto_punto() -> None:
    """facing = signo de (v · x̂), con x̂ = (1, 0). Como v·x̂ = vx, el signo
    del producto punto es el signo de la componente horizontal."""
    rana = _rana()

    rana.set_player_ref(_jugador_en(rana, 40.0, 0.0))
    rana.aim_at_player()
    assert rana.facing_direction == 1

    rana.set_player_ref(_jugador_en(rana, -40.0, 0.0))
    rana.aim_at_player()
    assert rana.facing_direction == -1


# ── Disparo ─────────────────────────────────────────────────────────

def test_al_disparar_nace_un_proyectil_hacia_el_jugador() -> None:
    rana = _rana(projectile_speed=90.0)
    rana.set_player_ref(_jugador_en(rana, 0.0, 80.0))

    rana.fire()

    assert len(rana.projectiles) == 1
    v = rana.projectiles[0].velocity
    assert v.length() == pytest.approx(90.0, abs=1e-6)
    assert v.y > 0                       # el jugador está abajo
    assert v.x == pytest.approx(0.0, abs=1e-6)


def test_no_dispara_sin_referencia_al_jugador() -> None:
    rana = _rana()
    rana.fire()
    assert rana.projectiles == []


# ── Impacto contra el jugador y parry ───────────────────────────────

class _JugadorFalso:
    """Sustituto mínimo del Player para probar el impacto del escupitajo.

    Expone lo que consulta `_check_player_contact`: hurtbox, apply_damage y
    las tres banderas del parry (ver enemy_shooter.py:193-207).
    """

    def __init__(self, rect: pygame.Rect, pareando: bool = False) -> None:
        self.hurtbox = rect
        self.rect = rect
        self.dano_recibido = 0.0
        self._parry_active = pareando
        self._parry_window = 0.2 if pareando else 0.0
        self._parry_success = False

    def apply_damage(self, cantidad: float, origen) -> None:
        self.dano_recibido += cantidad


def _rana_con_escupitajo_encima(pareando: bool):
    rana = _rana(projectile_speed=90.0, projectile_damage=0.5)
    objetivo = pygame.Rect(0, 0, 20, 32)
    objetivo.center = rana.rect.center
    rana.set_player_ref(_jugador_en(rana, 40.0, 0.0))
    rana.fire()
    # se coloca el proyectil justo encima del jugador
    jugador = _JugadorFalso(objetivo, pareando)
    rana.projectiles[0].position.update(objetivo.centerx, objetivo.centery)
    rana.projectiles[0].rect.topleft = (objetivo.centerx, objetivo.centery)
    return rana, jugador


def test_el_escupitajo_dana_al_jugador() -> None:
    """Sin este cableado los proyectiles eran decorativos: viajaban bonito
    pero no hacían absolutamente nada al tocar al jugador."""
    rana, jugador = _rana_con_escupitajo_encima(pareando=False)

    rana._check_player_contact(jugador)

    assert jugador.dano_recibido == pytest.approx(0.5)
    assert rana.projectiles[0].is_active is False


def test_el_escupitajo_se_puede_parear() -> None:
    """Con el parry activo (Z + abajo) el escupitajo se anula y no hace
    daño. Mismo contrato que EnemyShooter del profesor
    (enemy_shooter.py:198-204)."""
    rana, jugador = _rana_con_escupitajo_encima(pareando=True)

    rana._check_player_contact(jugador)

    assert jugador.dano_recibido == pytest.approx(0.0)
    assert jugador._parry_success is True
    assert rana.projectiles[0].is_active is False


def test_un_escupitajo_lejano_no_hace_nada() -> None:
    rana = _rana()
    rana.set_player_ref(_jugador_en(rana, 40.0, 0.0))
    rana.fire()
    lejos = pygame.Rect(9000, 9000, 20, 32)
    jugador = _JugadorFalso(lejos)

    rana._check_player_contact(jugador)

    assert jugador.dano_recibido == pytest.approx(0.0)
    assert rana.projectiles[0].is_active is True


def test_los_proyectiles_agotados_se_purgan() -> None:
    rana = _rana(projectile_speed=100.0)
    rana.set_player_ref(_jugador_en(rana, 200.0, 0.0))
    rana.fire()
    assert len(rana.projectiles) == 1

    # alcance por defecto 200 px → a 100 px/s se agota pasados 2 s
    for _ in range(30):
        rana.update_projectiles(0.1)

    assert rana.projectiles == []
