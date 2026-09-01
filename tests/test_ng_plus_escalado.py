"""AUD-760 — NG+ realmente cambia el juego y sigue siendo completable.

El defecto original: `ng_plus` existía en SaveData pero nadie lo incrementaba,
así que `get_config()` siempre devolvía la base (NORMAL) aunque el jugador
hubiera visto los créditos. El escalado ya estaba escrito (+10 % HP/daño por
vuelta), pero era código muerto.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.difficulty import Difficulty, get_config
from src.engine.core.save_data import SaveData
from src.engine.core.save_manager import SaveManager
from src.engine.scene.base_scene import BaseScene
from src.engine.scene.scene_manager import SceneManager


@pytest.fixture(autouse=True)
def _tmp_saves(tmp_path):
    orig = SaveManager.SAVES_DIR
    SaveManager.SAVES_DIR = tmp_path / "saves"
    SaveManager.SAVES_DIR.mkdir(parents=True, exist_ok=True)
    yield
    SaveManager.SAVES_DIR = orig


# ── el escalado existe ───────────────────────────────────────────────────


class TestNGPlusEscaladoExiste:
    def test_normal_distinto_de_ng_plus_1(self) -> None:
        c0 = get_config(Difficulty.NORMAL, ng_plus=0)
        c1 = get_config(Difficulty.NORMAL, ng_plus=1)
        assert c1.incoming_damage_mult > c0.incoming_damage_mult
        assert c1.enemy_health_mult > c0.enemy_health_mult
        assert c1.heal_mult < c0.heal_mult

    def test_cada_vuelta_sube_un_10_por_ciento(self) -> None:
        c1 = get_config(Difficulty.NORMAL, ng_plus=1)
        c2 = get_config(Difficulty.NORMAL, ng_plus=2)
        # 1.1 -> 1.2 sobre base 1.0
        assert c1.incoming_damage_mult == pytest.approx(1.10)
        assert c2.incoming_damage_mult == pytest.approx(1.20)
        assert c1.enemy_health_mult == pytest.approx(1.10)

    def test_parry_y_iframe_se_estrechan_leve(self) -> None:
        c0 = get_config(Difficulty.NORMAL, ng_plus=0)
        c1 = get_config(Difficulty.NORMAL, ng_plus=1)
        assert c1.parry_window < c0.parry_window
        assert c1.invincibility_duration < c0.invincibility_duration

    def test_no_usa_multiplicadores_arbitrarios_no_acotados(self) -> None:
        """El tope (3.0) y el suelo (0.1/0.05) evitan escalados imposibles."""
        c20 = get_config(Difficulty.NORMAL, ng_plus=20)
        assert c20.incoming_damage_mult <= 3.0
        assert c20.enemy_health_mult <= 3.0
        assert c20.heal_mult >= 0.1
        assert c20.parry_window >= 0.05


class TestNGPlusCompletable:
    def test_ng_plus_5_sigue_siendo_jugable(self) -> None:
        """A NG+5 NORMAL: 1.5x daño/HP, 0.75x cura, parry 0.20s — duro pero no roto."""
        c5 = get_config(Difficulty.NORMAL, ng_plus=5)
        assert c5.incoming_damage_mult == pytest.approx(1.5)
        assert c5.heal_mult == pytest.approx(0.75)
        # La cura sigue curando y la ventana sigue siendo pulsable
        assert c5.heal_mult > 0.5
        assert c5.parry_window >= 0.15
        assert c5.invincibility_duration >= 1.0

    def test_ng_plus_10_aun_tiene_iframe_y_combo(self) -> None:
        c10 = get_config(Difficulty.NORMAL, ng_plus=10)
        assert c10.invincibility_duration >= 0.5
        assert c10.combo_window >= 0.2


# ── el ciclo de vida ─────────────────────────────────────────────────────


class TestNGPlusCicloDeVida:
    """SAVE → LOAD → NG+ detection → difficulty config → ENEMY/DAMAGE."""

    def test_save_y_load_con_ng_plus(self) -> None:
        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, ng_plus=2, stage_id="stage0"))
        rec = mgr.load(1)
        assert rec is not None and rec.ng_plus == 2

    def test_get_config_lee_ng_plus_del_guardado(self) -> None:
        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, ng_plus=3))
        # Sin parámetro explícito, get_config lee del slot más reciente
        cfg = get_config(Difficulty.NORMAL, ng_plus=None)
        assert cfg.enemy_health_mult == pytest.approx(1.30)

    def test_get_config_prefiere_ranura_activa_a_mas_reciente(self) -> None:
        """Con dos partidas, la activa manda (AUD-441)."""
        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, ng_plus=1))
        mgr.save(2, SaveData(slot_id=2, ng_plus=5))
        mgr.ranura_activa = 1
        cfg = get_config(Difficulty.NORMAL)
        assert cfg.enemy_health_mult == pytest.approx(1.10)
        mgr.ranura_activa = 2
        cfg2 = get_config(Difficulty.NORMAL)
        assert cfg2.enemy_health_mult == pytest.approx(1.50)

    def test_enemy_health_escala_con_ng_plus(self) -> None:
        """El HP enemigo usa get_config().enemy_health_mult."""
        from src.framework.entities.enemy_base import EnemyBase

        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, ng_plus=2))
        mgr.ranura_activa = 1

        # Crear un enemigo mínimo
        class _DummyEnemy(EnemyBase):
            def _patrol_behavior(self, dt: float) -> None:
                pass

            def _alert_behavior(self, dt: float) -> None:
                pass

            def _build_hitbox(self) -> pygame.Rect:
                return pygame.Rect(0, 0, 16, 16)

            def _build_hurtbox(self) -> pygame.Rect:
                return pygame.Rect(0, 0, 16, 16)

            def _get_animation_key(self) -> str:
                return "idle"

        e = _DummyEnemy(pygame.Vector2(0, 0), max_health=10.0)
        # Con NG+2 NORMAL, 10 * 1.2 = 12
        assert e.max_health == pytest.approx(12.0)

    def test_player_damage_escala_con_ng_plus(self) -> None:
        """El daño recibido usa incoming_damage_mult."""
        from src.framework.entities.player import Player

        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, ng_plus=1))
        mgr.ranura_activa = 1

        p = Player(pygame.Vector2(0, 0))
        vida_antes = p.current_health
        # 1.0 de daño con NG+1 NORMAL (1.1x) = 1.1
        p.apply_damage(1.0, (0.0, 0.0))
        assert vida_antes - p.current_health == pytest.approx(1.1)


class TestNGPlusSeIncrementaAlTerminar:
    """Al agotar la cola de escenarios, el slot sube ng_plus y resetea índice."""

    def test_agotar_cola_incrementa_ng_plus(self) -> None:
        from unittest.mock import MagicMock

        from src.engine.core.event_bus import EventBus

        bus = EventBus()
        mgr = SaveManager()
        mgr.ranura_activa = 1
        mgr.save(1, SaveData(slot_id=1, ng_plus=0, stage_id="stage0"))

        # Dummy context con save_manager real
        ctx = MagicMock()
        ctx.event_bus = bus
        ctx.save_manager = mgr
        ctx.clock = None

        sm = SceneManager(ctx)  # type: ignore[arg-type]
        ctx.scene_manager = sm

        class _Stage(BaseScene):
            def on_enter(self) -> None:
                pass

            def on_exit(self) -> None:
                pass

            def update(self, dt: float) -> None:
                pass

            def draw(self, surface: pygame.Surface) -> None:
                pass

        sm.set_stage_queue([lambda c: _Stage(c)])
        sm.push(_Stage(ctx))
        # Completar el único stage -> créditos + NG+
        sm._on_stage_complete(stage_id="unico")

        rec = mgr.load(1)
        assert rec is not None
        assert rec.ng_plus == 1
        assert rec.stage_index == 0

    def test_sin_partida_no_se_incrementa(self) -> None:
        """Sin slot no hay donde guardar NG+ — no revienta."""
        from unittest.mock import MagicMock

        from src.engine.core.event_bus import EventBus

        bus = EventBus()
        ctx = MagicMock()
        ctx.event_bus = bus
        ctx.save_manager = SaveManager()
        # Borrar todo: sin saves
        for p in SaveManager.SAVES_DIR.glob("slot_*.json"):
            p.unlink()
        ctx.save_manager.ranura_activa = None
        ctx.clock = None

        sm = SceneManager(ctx)  # type: ignore[arg-type]
        ctx.scene_manager = sm

        class _Stage(BaseScene):
            def on_enter(self) -> None:
                pass

            def on_exit(self) -> None:
                pass

            def update(self, dt: float) -> None:
                pass

            def draw(self, surface: pygame.Surface) -> None:
                pass

        sm.set_stage_queue([lambda c: _Stage(c)])
        sm.push(_Stage(ctx))
        # No debe lanzar
        sm._on_stage_complete(stage_id="unico")
        assert sm._stack[-1].__class__.__name__ == "EndCreditsScene"
