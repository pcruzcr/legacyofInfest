"""Pruebas de las hojas de sprites propias de las cinco plagas (AUD-648).

Archivo NUEVO, separado de `test_la_soda.py` (que otro subagente está
editando en paralelo) para no pisarle cambios. Mismo patrón de arranque
—`SDL_VIDEODRIVER`/`SDL_AUDIODRIVER` a `dummy` ANTES de importar pygame— que
usa `test_la_soda.py`, porque este módulo tampoco hereda el `conftest.py` de
`tests/` (`tests/` es del profesor).

Qué verifica cada bloque:
  1. Las 5 hojas existen en `assets/maps/stage1_2_la_soda/` con el ancho
     esperado (cuadros x ancho_cuadro) y el alto de cuadro esperado.
  2. Cada cuadro tiene cobertura alfa entre 15% y 80% (ni vacío ni bloque
     sólido) y un contorno oscuro real (>= N píxeles muy oscuros).
  3. Contraste: la luminancia media del CUERPO de cada cuadro (píxeles
     opacos y no-oscuros -- se excluye el contorno de 1px, casi negro por
     diseño) difiere >= 40/255 de la luminancia del piso de la cocina y del
     pasto exterior, medidos sobre tiles reales de
     `tileset_soda_real.png` (mismas coordenadas de tile que usa
     `Claude - Uso General/playtest/dibujar_sprites_plagas.py`).
  4. Cada una de las 5 clases, instanciada en la escena real
     (`_construir_escena_la_soda()`, IMPORTADA de `test_la_soda.py` -- no se
     copia), tiene sus animaciones cargadas desde su hoja PROPIA (se mide
     comprobando que `_sprite_fw`/`_sprite_fh` quedaron en el tamaño de
     cuadro propio, no en el de zona por defecto del motor -- eso sólo pasa
     si el `try` de `_load_extra_sprites` cargó el PNG propio con éxito) y
     el cuadro actual no está vacío.
  5. Cocinero: al forzar el estado TELEGRAPHING, el cuadro que elige
     `_get_animation_state()` es el de "brazo atrás" -- el tercer cuadro
     (índice 2) de `sprite_cocinero.png`, no el de "lanzar" que comparte
     `EnemyShooter` para TELEGRAPHING y FIRING.
  6. `TestGolpeYMuerteVisibles` (AUD-649) -- el mixin `_GolpeYMuerteVisibles`
     de `entities.py`: el destello blanco + retroceso de 2px que dura
     exactamente 4 `draw()` tras un golpe no letal, sin tocar `rect`; las
     6-8 partículas que genera una muerte (caen con la misma gravedad y
     desaparecen antes de 0.7s); el desvanecido del sprite siguiendo
     `255*(1-ease_out_quad(t))`; y que el destello de telegrafiado del
     cocinero (AUD-648) sigue intacto con el mixin insertado en su MRO.

Se corre con:
    python -m pytest src/stages/stage1_2_la_soda/test_la_soda_sprites.py -q
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pathlib import Path

import pygame
import pytest

from src.stages.stage1_2_la_soda.entities import (
    FlyingCucaracha,
    FlyingZancudo,
    ShooterCocinero,
    WalkerCulebra,
    WalkerRaton,
)
from src.stages.stage1_2_la_soda.test_la_soda import _construir_escena_la_soda

RAIZ = Path(__file__).resolve().parents[3]
ASSETS_DIR = RAIZ / "assets" / "maps" / "stage1_2_la_soda"
TILESET_REAL = ASSETS_DIR / "tileset_soda_real.png"

#: (nombre, clase, archivo, ancho_cuadro, alto_cuadro, n_cuadros)
ESPECIFICACIONES = [
    ("raton", WalkerRaton, "sprite_raton.png", 24, 24, 4),
    ("cucaracha", FlyingCucaracha, "sprite_cucaracha.png", 24, 24, 3),
    ("culebra", WalkerCulebra, "sprite_culebra.png", 32, 16, 4),
    ("zancudo", FlyingZancudo, "sprite_zancudo.png", 24, 24, 3),
    ("cocinero", ShooterCocinero, "sprite_cocinero.png", 32, 32, 5),
]

#: Cobertura alfa aceptable por cuadro: ni vacío ni un bloque sólido.
ALFA_MIN = 0.15
ALFA_MAX = 0.80

#: Un cuadro real trae de sobra este mínimo de píxeles de contorno (medido
#: en la hoja generada: los cuadros más chicos -- 3 por criatura -- superan
#: las 20 unidades incluso en el cuadro con menos silueta).
CONTORNO_MIN_PIXELES = 10
#: Luminancia por debajo de la cual un píxel opaco se considera "contorno"
#: (casi negro por diseño -- ver `OUTLINE` en el generador) y no "cuerpo".
LUM_CONTORNO = 30.0

#: Diferencia mínima de luminancia exigida entre el cuerpo de un sprite y
#: el piso/pasto de referencia.
CONTRASTE_MIN = 40.0


def _pygame_listo():
    if not pygame.get_init():
        pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


@pytest.fixture(scope="module", autouse=True)
def _video():
    _pygame_listo()
    yield


def _luminancia(rgb) -> float:
    r, g, b = rgb[0], rgb[1], rgb[2]
    return 0.299 * r + 0.587 * g + 0.114 * b


def _cargar_hoja(nombre_archivo: str) -> pygame.Surface:
    _pygame_listo()
    ruta = ASSETS_DIR / nombre_archivo
    assert ruta.exists(), f"falta la hoja {ruta}"
    return pygame.image.load(str(ruta)).convert_alpha()


def _cuadros(hoja: pygame.Surface, fw: int, fh: int) -> list[pygame.Surface]:
    n = hoja.get_width() // fw
    return [hoja.subsurface((i * fw, 0, fw, fh)) for i in range(n)]


def _pixeles_opacos(cuadro: pygame.Surface) -> list[tuple[int, int, int, int]]:
    w, h = cuadro.get_size()
    return [cuadro.get_at((x, y)) for y in range(h) for x in range(w) if cuadro.get_at((x, y))[3] == 255]


def _color_medio_tile(box) -> tuple[float, float, float]:
    im = pygame.image.load(str(TILESET_REAL)).convert_alpha()
    crop = im.subsurface(box)
    w, h = crop.get_size()
    pixeles = [crop.get_at((x, y)) for y in range(h) for x in range(w)]
    pixeles = [p for p in pixeles if p[3] > 10]
    n = len(pixeles)
    return (
        sum(p[0] for p in pixeles) / n,
        sum(p[1] for p in pixeles) / n,
        sum(p[2] for p in pixeles) / n,
    )


# Mismas coordenadas de tile (16x16) que usa el generador de sprites para
# medir el piso de la cocina (terracota) y el pasto del exterior, sobre
# `tileset_soda_real.png` -- ver `dibujar_sprites_plagas.py::main`.
#
# `pygame.image.load(...).convert_alpha()` exige un display ya inicializado
# (AUD-024 lo documenta en `asset_loader.py`) y los fixtures no corren
# todavía durante la RECOLECCIÓN de pruebas (este módulo se importa antes de
# que arranque ningún test) -- por eso el `_pygame_listo()` explícito acá,
# en vez de depender del fixture `_video` de más abajo.
_pygame_listo()
LUM_PISO = _luminancia(_color_medio_tile((80, 80, 16, 16)))
LUM_PASTO = _luminancia(_color_medio_tile((0, 48, 16, 16)))


# ──────────────────────────────────────────────────────────────
# 1-3: las hojas en disco
# ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("nombre,cls,archivo,fw,fh,n", ESPECIFICACIONES)
def test_la_hoja_existe_con_el_tamano_esperado(nombre, cls, archivo, fw, fh, n):
    hoja = _cargar_hoja(archivo)
    assert hoja.get_size() == (fw * n, fh), (
        f"{archivo}: se esperaba {fw * n}x{fh} ({n} cuadros de {fw}x{fh}), "
        f"dio {hoja.get_size()}"
    )


@pytest.mark.parametrize("nombre,cls,archivo,fw,fh,n", ESPECIFICACIONES)
def test_cada_cuadro_tiene_cobertura_alfa_razonable(nombre, cls, archivo, fw, fh, n):
    hoja = _cargar_hoja(archivo)
    for i, cuadro in enumerate(_cuadros(hoja, fw, fh)):
        total = fw * fh
        opacos = sum(
            1 for y in range(fh) for x in range(fw) if cuadro.get_at((x, y))[3] > 10
        )
        cobertura = opacos / total
        assert ALFA_MIN <= cobertura <= ALFA_MAX, (
            f"{archivo} cuadro {i}: cobertura alfa {cobertura:.2f} fuera de "
            f"[{ALFA_MIN}, {ALFA_MAX}] -- ¿cuadro vacío o bloque sólido?"
        )


@pytest.mark.parametrize("nombre,cls,archivo,fw,fh,n", ESPECIFICACIONES)
def test_cada_cuadro_tiene_contorno_oscuro(nombre, cls, archivo, fw, fh, n):
    hoja = _cargar_hoja(archivo)
    for i, cuadro in enumerate(_cuadros(hoja, fw, fh)):
        oscuros = sum(
            1 for y in range(fh) for x in range(fw)
            if cuadro.get_at((x, y))[3] > 10 and _luminancia(cuadro.get_at((x, y))) < LUM_CONTORNO
        )
        assert oscuros >= CONTORNO_MIN_PIXELES, (
            f"{archivo} cuadro {i}: sólo {oscuros} píxeles de contorno "
            f"oscuro (mínimo {CONTORNO_MIN_PIXELES}) -- ¿le falta el "
            f"contorno de 1px?"
        )


@pytest.mark.parametrize("nombre,cls,archivo,fw,fh,n", ESPECIFICACIONES)
def test_contraste_del_cuerpo_contra_piso_y_pasto(nombre, cls, archivo, fw, fh, n):
    hoja = _cargar_hoja(archivo)
    for i, cuadro in enumerate(_cuadros(hoja, fw, fh)):
        cuerpo = [
            p for p in _pixeles_opacos(cuadro) if _luminancia(p) >= LUM_CONTORNO
        ]
        assert cuerpo, f"{archivo} cuadro {i}: no quedan píxeles de cuerpo tras excluir el contorno"
        lum = sum(_luminancia(p) for p in cuerpo) / len(cuerpo)
        diff_piso = abs(lum - LUM_PISO)
        diff_pasto = abs(lum - LUM_PASTO)
        assert diff_piso >= CONTRASTE_MIN, (
            f"{archivo} cuadro {i}: luminancia de cuerpo {lum:.1f} muy "
            f"cerca del piso de cocina ({LUM_PISO:.1f}, diff={diff_piso:.1f})"
        )
        assert diff_pasto >= CONTRASTE_MIN, (
            f"{archivo} cuadro {i}: luminancia de cuerpo {lum:.1f} muy "
            f"cerca del pasto exterior ({LUM_PASTO:.1f}, diff={diff_pasto:.1f})"
        )


# ──────────────────────────────────────────────────────────────
# 4: cada clase, instanciada en la escena real, usa su hoja propia
# ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("nombre,cls,archivo,fw,fh,n", ESPECIFICACIONES)
def test_la_clase_en_la_escena_real_carga_su_hoja_propia(nombre, cls, archivo, fw, fh, n):
    """`_sprite_fw`/`_sprite_fh` sólo quedan en el tamaño de cuadro propio
    (24x24 / 32x16 / 32x32) si el `try` de `_load_extra_sprites` cargó con
    éxito el PNG propio y lo reasignó -- si el archivo faltara o fallara la
    carga, se quedarían en el tamaño de zona del motor (16x12 / 14x10 /
    12x12), que es exactamente lo que este test distingue.
    """
    sc = _construir_escena_la_soda()
    entidad = next(e for e in sc._stage_data.entity_list if isinstance(e, cls))
    assert entidad._sprite_fw == fw and entidad._sprite_fh == fh, (
        f"{cls.__name__}: _sprite_fw/_fh quedaron en "
        f"({entidad._sprite_fw}, {entidad._sprite_fh}), no en ({fw}, {fh}) "
        f"-- la hoja propia no se cargó (¿cayó al tamaño de zona del motor?)"
    )
    anim_key = entidad._get_animation_state()
    frames = entidad._sprite_frames.get(anim_key)
    assert frames, f"{cls.__name__}: sin cuadros cargados para el estado {anim_key!r}"
    idx = min(entidad._animation_frame, len(frames) - 1)
    cuadro = frames[idx]
    assert cuadro.get_size() == (fw, fh), (
        f"{cls.__name__}: el cuadro activo mide {cuadro.get_size()}, no ({fw}, {fh})"
    )
    opacos = sum(
        1 for y in range(cuadro.get_height()) for x in range(cuadro.get_width())
        if cuadro.get_at((x, y))[3] > 10
    )
    assert opacos > 0, f"{cls.__name__}: el cuadro activo está vacío"


# ──────────────────────────────────────────────────────────────
# 5: el cocinero telegrafía con el cuadro de "brazo atrás"
# ──────────────────────────────────────────────────────────────


def test_cocinero_en_telegraphing_usa_el_cuadro_de_brazo_atras():
    from src.framework.entities.enemy_base import EnemyState

    sc = _construir_escena_la_soda()
    cocinero = next(
        e for e in sc._stage_data.entity_list if isinstance(e, ShooterCocinero)
    )
    cocinero.state = EnemyState.TELEGRAPHING

    anim_key = cocinero._get_animation_state()
    assert anim_key == "telegraph", (
        f"en TELEGRAPHING, _get_animation_state() devolvió {anim_key!r}, no "
        f"'telegraph' -- EnemyShooter._get_animation_key comparte 'fire' "
        f"entre TELEGRAPHING y FIRING (enemy_shooter.py:376-382); "
        f"ShooterCocinero debe separarlas"
    )
    cuadro_activo = cocinero._sprite_frames[anim_key][0]

    hoja = _cargar_hoja("sprite_cocinero.png")
    cuadros = _cuadros(hoja, 32, 32)
    brazo_atras = cuadros[2]  # orden fijo del generador: idle0,idle1,telegraph,fire,herido
    lanzar = cuadros[3]

    assert pygame.image.tobytes(cuadro_activo, "RGBA") == pygame.image.tobytes(brazo_atras, "RGBA"), (
        "el cuadro de TELEGRAPHING no es el de 'brazo atrás' (índice 2 de "
        "sprite_cocinero.png)"
    )
    assert pygame.image.tobytes(cuadro_activo, "RGBA") != pygame.image.tobytes(lanzar, "RGBA"), (
        "el cuadro de TELEGRAPHING es igual al de 'lanzar' -- el "
        "telegrafiado no se distingue del disparo"
    )


def test_cocinero_en_firing_usa_el_cuadro_de_lanzar_no_el_de_telegrafiar():
    from src.framework.entities.enemy_base import EnemyState

    sc = _construir_escena_la_soda()
    cocinero = next(
        e for e in sc._stage_data.entity_list if isinstance(e, ShooterCocinero)
    )
    cocinero.state = EnemyState.FIRING

    anim_key = cocinero._get_animation_state()
    assert anim_key == "fire"
    cuadro_activo = cocinero._sprite_frames[anim_key][0]

    hoja = _cargar_hoja("sprite_cocinero.png")
    cuadros = _cuadros(hoja, 32, 32)
    lanzar = cuadros[3]

    assert pygame.image.tobytes(cuadro_activo, "RGBA") == pygame.image.tobytes(lanzar, "RGBA")


def test_cocinero_destello_de_telegrafiado_parpadea_2_de_cada_6_fotogramas():
    """El destello blanco de `ShooterCocinero.draw()` sólo se activa 2 de
    cada 6 fotogramas DIBUJADOS mientras el estado es TELEGRAPHING -- se
    mide contando cuántos de una tanda de `draw()` seguidos añaden algún
    píxel blanco puro por encima del cuerpo del cocinero."""
    from src.framework.entities.enemy_base import EnemyState

    sc = _construir_escena_la_soda()
    cocinero = next(
        e for e in sc._stage_data.entity_list if isinstance(e, ShooterCocinero)
    )
    cocinero.state = EnemyState.TELEGRAPHING
    cocinero._telegraph_timer = cocinero._telegraph_duration

    superficie = pygame.Surface((800, 600))
    offset = pygame.Vector2(cocinero.rect.centerx - 400, cocinero.rect.centery - 300)

    destellos = 0
    for _ in range(12):
        superficie.fill((10, 10, 10))
        cocinero.draw(superficie, offset)
        screen_x = int(cocinero.position.x - offset.x)
        screen_y = int(cocinero.position.y - offset.y)
        ox = (cocinero.rect.width - cocinero._sprite_fw) // 2
        oy = cocinero.rect.height - cocinero._sprite_fh
        region = pygame.Rect(
            screen_x + ox, screen_y + oy, cocinero._sprite_fw, cocinero._sprite_fh,
        ).clip(superficie.get_rect())
        hay_blanco_puro = any(
            superficie.get_at((x, y))[:3] == (255, 255, 255)
            for x in range(region.left, region.right)
            for y in range(region.top, region.bottom)
        )
        if hay_blanco_puro:
            destellos += 1

    assert destellos == 4, (
        f"12 fotogramas a 2 destellos de cada 6 deberían dar 4 destellos, "
        f"dio {destellos}"
    )


# ──────────────────────────────────────────────────────────────
# AUD-649 -- feedback visual de golpe y muerte (_GolpeYMuerteVisibles)
# ──────────────────────────────────────────────────────────────


class TestGolpeYMuerteVisibles:
    """`_GolpeYMuerteVisibles` (entities.py) -- destello+retroceso al
    golpe, partículas+desvanecido al morir. Ver el docstring del mixin
    para el porqué completo; acá sólo se verifica el comportamiento."""

    def test_destello_de_golpe_aclara_el_area_del_sprite_por_4_fotogramas(self):
        """Golpe no letal -> 4 `draw()` con la zona del sprite más clara
        que sin destello, y al 5to ya no."""
        sc = _construir_escena_la_soda()
        raton = next(
            e for e in sc._stage_data.entity_list if isinstance(e, WalkerRaton)
        )

        superficie = pygame.Surface((200, 200))
        offset = pygame.Vector2(raton.rect.centerx - 100, raton.rect.centery - 100)
        ox = (raton.rect.width - raton._sprite_fw) // 2
        oy = raton.rect.height - raton._sprite_fh
        base_x = int(raton.position.x - offset.x) + ox
        base_y = int(raton.position.y - offset.y) + oy
        region = pygame.Rect(
            base_x - raton._GOLPE_RETROCESO_PX - 1, base_y - 1,
            raton._sprite_fw + 2 * raton._GOLPE_RETROCESO_PX + 2, raton._sprite_fh + 2,
        ).clip(superficie.get_rect())

        def _lum_media():
            superficie.fill((40, 40, 40))
            raton.draw(superficie, offset)
            pixeles = [
                superficie.get_at((x, y))
                for y in range(region.top, region.bottom)
                for x in range(region.left, region.right)
            ]
            return sum(_luminancia(p) for p in pixeles) / len(pixeles)

        # damage=0.1 < max_health=1.0: HURT, no letal -- no se mezcla con
        # las partículas/desvanecido de muerte de las pruebas de abajo.
        raton.apply_hit(0.1, (raton.rect.centerx - 40.0, raton.rect.centery))
        assert raton._golpe_flash_restante == raton._GOLPE_FLASH_FRAMES

        luminancias_con_flash = [_lum_media() for _ in range(raton._GOLPE_FLASH_FRAMES)]
        assert raton._golpe_flash_restante == 0, (
            "el contador de destello debería agotarse en exactamente "
            f"{raton._GOLPE_FLASH_FRAMES} draw()"
        )

        # Mismo cuadro "hurt" que durante el destello -- comparación justa
        # (pose contra pose, no "hurt" contra "walk").
        lum_sin_flash = _lum_media()
        lum_sin_flash_control = _lum_media()
        assert abs(lum_sin_flash_control - lum_sin_flash) < 1.0, (
            "la luminancia sin destello debería ser estable entre fotogramas"
        )

        for i, lum in enumerate(luminancias_con_flash):
            assert lum > lum_sin_flash + 15.0, (
                f"fotograma {i} con destello: luminancia {lum:.1f} no supera "
                f"a la normal ({lum_sin_flash:.1f}) por un margen razonable"
            )

    def test_retroceso_del_destello_es_2px_sin_tocar_el_rect(self):
        sc = _construir_escena_la_soda()
        raton = next(
            e for e in sc._stage_data.entity_list if isinstance(e, WalkerRaton)
        )
        rect_antes = raton.rect.copy()
        pos_antes = pygame.Vector2(raton.position)

        superficie = pygame.Surface((200, 200))
        offset = pygame.Vector2(raton.rect.centerx - 100, raton.rect.centery - 100)

        def _bbox_blanco_puro(direccion):
            raton._golpe_retroceso_dir = direccion
            raton._golpe_flash_restante = 1
            superficie.fill((10, 10, 10))
            raton.draw(superficie, offset)
            xs = [
                x for y in range(superficie.get_height())
                for x in range(superficie.get_width())
                if superficie.get_at((x, y))[:3] == (255, 255, 255)
            ]
            assert xs, f"no se encontró ningún píxel blanco puro con dir={direccion}"
            return min(xs), max(xs)

        izq_min, izq_max = _bbox_blanco_puro(-1)
        der_min, der_max = _bbox_blanco_puro(1)

        esperado = 2 * raton._GOLPE_RETROCESO_PX
        assert der_min - izq_min == esperado, (
            f"el borde izquierdo del destello no se corrió {esperado}px "
            f"entre dir=-1 (x={izq_min}) y dir=1 (x={der_min})"
        )
        assert der_max - izq_max == esperado, (
            f"el borde derecho del destello no se corrió {esperado}px "
            f"entre dir=-1 (x={izq_max}) y dir=1 (x={der_max})"
        )

        assert raton.rect == rect_antes, "draw() no debe tocar rect"
        assert raton.position == pos_antes, "draw() no debe tocar position"

    def test_muerte_genera_particulas_que_caen_y_desaparecen(self):
        from src.framework.entities.enemy_base import EnemyState

        sc = _construir_escena_la_soda()
        raton = next(
            e for e in sc._stage_data.entity_list if isinstance(e, WalkerRaton)
        )

        # damage=10.0 > max_health=1.0: golpe letal de un solo tiro, mismo
        # patrón que `_matar_al_cocinero` de test_la_soda.py.
        raton.apply_hit(10.0, (raton.rect.centerx - 40.0, raton.rect.centery))
        assert raton.state == EnemyState.DYING
        raton.update(1 / 60)  # primer update() en DYING: genera las partículas

        n = len(raton._muerte_particulas)
        assert 6 <= n <= 8, f"se esperaban 6-8 partículas, se generaron {n}"

        y_iniciales = {id(p): p.y for p in raton._muerte_particulas}
        raton.update(1 / 60)
        for p in raton._muerte_particulas:
            assert p.y > y_iniciales[id(p)], (
                "la 'y' de cada partícula debería crecer con la gravedad"
            )

        for _ in range(int(0.7 * 60) - 2):
            raton.update(1 / 60)
        assert raton._muerte_particulas == [], (
            "las partículas deberían haber desaparecido antes de 0.7s"
        )

    def test_alpha_de_muerte_sigue_ease_out_quad(self):
        from src.engine.utils.math_utils import ease_out_quad
        from src.stages.stage1_2_la_soda.entities import _MUERTE_FADE_DURATION

        sc = _construir_escena_la_soda()
        raton = next(
            e for e in sc._stage_data.entity_list if isinstance(e, WalkerRaton)
        )
        raton.apply_hit(10.0, (raton.rect.centerx - 40.0, raton.rect.centery))
        raton.update(1 / 60)  # entra en DYING, el temporizador de fade arranca

        for t in (0.0, 0.5, 1.0):
            raton._muerte_fade_timer = t * _MUERTE_FADE_DURATION
            esperado = int(255 * (1.0 - ease_out_quad(t)))
            obtenido = raton._alpha_de_muerte()
            assert obtenido == esperado, (
                f"t={t}: alpha {obtenido} distinto del esperado {esperado} "
                f"= 255*(1-ease_out_quad(t))"
            )

    def test_cocinero_conserva_destello_de_telegrafiado_con_el_mixin(self):
        """Regresión: insertar `_GolpeYMuerteVisibles` en el MRO de
        `ShooterCocinero` (entre la clase y `EnemyShooter`) no debe romper
        el destello de telegrafiado de AUD-648 -- mismo montaje que
        `test_cocinero_destello_de_telegrafiado_parpadea_2_de_cada_6_
        fotogramas` de más arriba, repetido acá como prueba dedicada de
        este mixin."""
        from src.framework.entities.enemy_base import EnemyState

        sc = _construir_escena_la_soda()
        cocinero = next(
            e for e in sc._stage_data.entity_list if isinstance(e, ShooterCocinero)
        )
        cocinero.state = EnemyState.TELEGRAPHING
        cocinero._telegraph_timer = cocinero._telegraph_duration

        superficie = pygame.Surface((800, 600))
        offset = pygame.Vector2(cocinero.rect.centerx - 400, cocinero.rect.centery - 300)

        destellos = 0
        for _ in range(12):
            superficie.fill((10, 10, 10))
            cocinero.draw(superficie, offset)
            screen_x = int(cocinero.position.x - offset.x)
            screen_y = int(cocinero.position.y - offset.y)
            ox = (cocinero.rect.width - cocinero._sprite_fw) // 2
            oy = cocinero.rect.height - cocinero._sprite_fh
            region = pygame.Rect(
                screen_x + ox, screen_y + oy, cocinero._sprite_fw, cocinero._sprite_fh,
            ).clip(superficie.get_rect())
            hay_blanco_puro = any(
                superficie.get_at((x, y))[:3] == (255, 255, 255)
                for x in range(region.left, region.right)
                for y in range(region.top, region.bottom)
            )
            if hay_blanco_puro:
                destellos += 1

        assert destellos == 4, (
            "con _GolpeYMuerteVisibles insertado en el MRO, el destello de "
            f"telegrafiado debería seguir parpadeando 4 veces en 12 "
            f"fotogramas (2 de cada 6); dio {destellos}"
        )
