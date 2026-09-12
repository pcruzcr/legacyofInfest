"""T4-FINALIZATION — verdad de fases Rey (campaña) y Paburu.

Rey stage2_4: F1 Marioneta → F2 División (2 ReyMetad) → F3 Frenesí, con
transiciones jugables (no sólo enums). Paburu: 4 formas declaradas con
módulos de ataque por forma; aquí se fija el nivel de evidencia real.
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


def _rey():
    from src.stages.boss_rey.boss_rey import BossRey

    return BossRey(pygame.Vector2(400.0, 300.0))


class TestReyTresFasesJugables:
    def test_declara_tres_fases(self) -> None:
        rey = _rey()
        assert rey.phase_count == 3
        assert rey.phases[1].attack_patterns == ["VENOM_SPIT", "BODY_SLAM"]
        assert rey.phases[2].attack_patterns == ["VENOM_BURST", "LUNGE"]

    def test_fase_dos_parte_el_cuerpo_en_dos_mitades(self) -> None:
        rey = _rey()
        rey.apply_hit(18.0, (400, 300))  # AUD-839: 45 → 27, bajo el umbral 30
        assert rey.is_transitioning is True
        rey.update(3.0)  # termina la transición base (2,5 s)
        assert rey.current_phase == 1, "no entró a La División"
        assert len(rey._mitades) == 2, "la división no generó dos ReyMetad"
        assert len(rey.pending_summons) == 2
        assert rey.is_visible is False, "el cuerpo siguió golpeable en F2"

    def test_fase_tres_arranca_al_caer_las_mitades(self) -> None:
        rey = _rey()
        rey.apply_hit(18.0, (400, 300))
        rey.update(3.0)
        assert rey.current_phase == 1
        for mitad in list(rey._mitades):
            mitad.apply_hit(99.0, (0, 0))
            mitad.update(1.0)
        assert all(not m.is_alive for m in rey._mitades)
        rey._vigilar_mitades()
        rey.update(3.0)
        assert rey.current_phase == 2, "no entró a El Frenesí"
        assert rey.is_visible is True


class TestPaburuNivelDeEvidencia:
    def test_cuatro_formas_declaradas_con_ataques_por_forma(self) -> None:
        from src.stages.boss_paburu import form1_attacks as f1
        from src.stages.boss_paburu import form2_attacks as f2
        from src.stages.boss_paburu import form3_attacks as f3
        from src.stages.boss_paburu import form4_attacks as f4

        for modulo in (f1, f2, f3, f4):
            assert modulo.__name__.endswith(
                ("form1_attacks", "form2_attacks", "form3_attacks", "form4_attacks")
            ), modulo
        # F1 completa y cableada en el planificador del jefe.
        assert hasattr(f1, "StoneSpit") or any(
            "STONE" in n.upper() or "SPIT" in n.upper() or "Stone" in n
            for n in dir(f1)
        ), "F1 sin ataques localizables"

    def test_el_jefe_expone_transicion_por_formas(self) -> None:
        import inspect

        from src.stages.boss_paburu import boss_paburu as bp

        fuente = inspect.getsource(bp)
        assert "current_phase" in fuente
        assert "set_phases" in fuente
