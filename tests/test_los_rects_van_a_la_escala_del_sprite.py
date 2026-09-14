"""
Module: test_los_rects_van_a_la_escala_del_sprite
System: tests
Description: AUD-821 (P16) — la colisión lógica va a la escala del frame
que se dibuja. d1676cf duplicó tres rects sin tocar sprites ni dibujo:
el enemigo golpeaba y recibía a 10-14 px de donde se veía.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.entities.enemy_charger import EnemyCharger
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import EnemyShooter

_ESPECIES = [
    (EnemyFlying, 20, 14),
    (EnemyShooter, 16, 24),
    (EnemyCharger, 28, 24),
]


@pytest.mark.parametrize("cls,w,h", _ESPECIES)
def test_el_rect_es_el_tamano_logico(cls: type, w: int, h: int) -> None:
    enemigo = cls(pygame.Vector2(0.0, 0.0))
    assert (enemigo.rect.width, enemigo.rect.height) == (w, h), (
        "rect duplicado respecto al tamaño lógico (P16)"
    )


@pytest.mark.parametrize("cls,w,h", _ESPECIES)
def test_el_rect_no_duplica_al_frame_que_dibuja(
    cls: type, w: int, h: int,
) -> None:
    """Guarda genérica contra la familia del bug: el rect no puede exceder
    el doble del frame que `draw` centra en él (`enemy_base`: el sprite se
    centra en el rect). `_sprite_fw/_fh` es el tamaño intencional aunque el
    asset falte y haya placeholder."""
    enemigo = cls(pygame.Vector2(0.0, 0.0))
    fw = int(getattr(enemigo, "_sprite_fw", w))
    fh = int(getattr(enemigo, "_sprite_fh", h))
    assert enemigo.rect.width <= 2 * fw, (
        f"ancho {enemigo.rect.width} duplica al frame {fw} (P16)"
    )
    assert enemigo.rect.height <= 2 * fh, (
        f"alto {enemigo.rect.height} duplica al frame {fh} (P16)"
    )
