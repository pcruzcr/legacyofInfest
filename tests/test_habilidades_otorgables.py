"""GPL-CIERRE R-001/R-002 — verdad del sistema de habilidades.

Toda habilidad con candado (`_tiene_habilidad`) o con otorgante
(`skill_drop`) tiene que existir en el catálogo; si no, el botín se
filtra en silencio (`economia.py`) o el candado no se puede abrir nunca
en un mapa nuevo. Y `skill_coraza` tiene que hacer lo que promete.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.inventory import get_inventory
from src.framework.entities.player import Player


def _todas_las_habilidades_mencionadas() -> set[str]:
    """Candados + botines declarados en el código."""
    return {
        "skill_double_jump",   # helpers.py::_can_jump
        "skill_dash",          # helpers.py::_can_dash
        "skill_ground_pound",  # airborne.py (candado del pisotón)
        "skill_parry",         # botín del Venado
        "skill_coraza",        # botín del Gavilán (boss_gavilan.py:79)
    }


def test_toda_habilidad_con_candado_u_otorgante_esta_en_catalogo() -> None:
    inv = get_inventory()
    faltan = [s for s in _todas_las_habilidades_mencionadas()
              if inv.get_def(s) is None]
    assert faltan == [], f"habilidades fantasma sin entrada: {faltan}"


def test_el_botin_del_gavilan_pasa_el_filtro_de_la_economia() -> None:
    """`economia.py:60` descarta lo que no está en catálogo."""
    from src.stages.stage3_4_boss_gavilan.boss_gavilan import BossGavilan

    inv = get_inventory()
    for parte in str(BossGavilan.skill_drop).split(","):
        assert inv.get_def(parte) is not None, (
            f"el Gavilán suelta {parte!r} y la economía lo tiraría al suelo "
            "para nada"
        )


def test_los_botines_de_todos_los_jefes_pasan_el_filtro() -> None:
    from src.framework.entities.boss_base import normalizar_skill_drop
    from src.stages.boss_rey.boss_rey import BossRey
    from src.stages.boss_rey.boss_rey import BossRey as BossRey24
    from src.stages.boss_venado.boss_venado import BossVenado
    from src.stages.stage3_4_boss_gavilan.boss_gavilan import BossGavilan

    inv = get_inventory()
    for jefe in (BossVenado, BossRey, BossRey24, BossGavilan):
        for parte in normalizar_skill_drop(getattr(jefe, "skill_drop", "")):
            assert inv.get_def(parte) is not None, (
                f"{jefe.__name__} suelta {parte!r} sin entrada en catálogo"
            )


def test_coraza_reduce_el_dano_un_cuarto() -> None:
    inv = get_inventory()
    respaldo = dict(inv.all_items())
    try:
        sin = Player(pygame.Vector2(50.0, 0.0))
        vida0 = sin.current_health
        sin.apply_damage(1.0, (50.0, 0.0))
        dano_sin = vida0 - sin.current_health

        assert inv.collect("skill_coraza"), "coraza no se puede recoger"
        con = Player(pygame.Vector2(50.0, 0.0))
        vida1 = con.current_health
        con.apply_damage(1.0, (50.0, 0.0))
        dano_con = vida1 - con.current_health

        assert dano_con == pytest.approx(dano_sin * 0.75), (
            f"coraza promete -25 %: sin={dano_sin} con={dano_con}"
        )
    finally:
        inv.restaurar(respaldo)


def test_pison_se_puede_otorgar_y_el_candado_lo_respeta() -> None:
    """En un mapa nuevo (sin exención) el pisotón depende del inventario."""
    from src.framework.entities.states.helpers import _tiene_habilidad

    inv = get_inventory()
    respaldo = dict(inv.all_items())
    try:
        assert inv.collect("skill_ground_pound"), "el pisotón no se puede otorgar"
        jugador = Player(pygame.Vector2(100.0, 100.0))
        jugador._habilidades_libres = False
        assert _tiene_habilidad("skill_ground_pound", jugador) is True
    finally:
        inv.restaurar(respaldo)
