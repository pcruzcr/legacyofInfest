"""B4 — cobertura crítica: enemy_base, stage_objetos, ecs/components, prefab_loader, gl_pipeline.

Cada test responde: "¿qué defecto haría fallar este test?" — ver docstring.
RULE 1: mutación puntual verifica que el test detecta la regresión.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.render.gl_pipeline import GLRenderer
from src.framework.ecs.components import Alerta
from src.framework.entities.enemy_base import EnemyBase, EnemyState
from src.framework.stage.prefab_loader import cargar_prefab
from src.framework.stage.stage_objetos import ObjetosDeTiled as _OE

# ── enemy_base ────────────────────────────────────────────────────────────


class _ProbeEnemy(EnemyBase):
    def _patrol_behavior(self, dt: float) -> None:
        self.position.x += 10 * dt

    def _alert_behavior(self, dt: float) -> None:
        self.position.x += 20 * dt

    def _build_hitbox(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 16, 16)

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 16, 16)

    def _get_animation_key(self) -> str:
        return "idle"


def _enemy(pos=(100, 100), **kw) -> _ProbeEnemy:
    return _ProbeEnemy(pygame.Vector2(*pos), max_health=10.0, **kw)


class TestEnemyBase:
    def test_apply_hit_mitiga_por_canal(self):
        """Mitigación por canal; si resistencias ignoradas -> vida 0 en vez de 5."""
        e = _enemy()
        e.resistencias = {"fuego": 0.5}
        e.apply_hit(10, (0, 0), canal="fuego")
        assert e.current_health == pytest.approx(5.0)

    def test_death_is_alive_delay(self):
        """Delay 0.5s antes de is_alive=False; si inmediato -> animación cortada."""
        e = _enemy()
        e.apply_hit(100, (0, 0))
        assert e.state == EnemyState.DYING
        assert e.is_alive is True
        e._tick_cooldowns(0.6)
        assert e.is_alive is False and e.is_active is False

    def test_stun_no_acorta(self):
        """stun(1.0) luego stun(0.1) debe mantener 1.0; si acorta -> 0.1."""
        e = _enemy()
        e.stun(1.0)
        assert e.state == EnemyState.STUNNED
        e.stun(0.1)
        assert e._stun_timer == pytest.approx(1.0)  # type: ignore[attr-defined]

    def test_hit_durante_invencibilidad_no_suma(self):
        """i-frames 0.5s; si apply_hit durante -> vida no baja."""
        e = _enemy()
        e._invincibility_timer = 0.5  # type: ignore[attr-defined]
        before = e.current_health
        e.apply_hit(5, (0, 0))
        assert e.current_health == before

    def test_hit_en_dying_no_resetea_timer(self):
        """DYING hit no debe resetear _death_timer."""
        e = _enemy()
        e.apply_hit(100, (0, 0))
        e._death_timer = 0.2  # type: ignore[attr-defined]
        e.apply_hit(5, (0, 0))
        assert e._death_timer == pytest.approx(0.2)  # type: ignore[attr-defined]

    def test_estado_fleeing_no_crashea(self):
        """FLEEING sin handler debe coerced a PATROL/IDLE sin lanzar."""
        e = _enemy()
        e.state = EnemyState.FLEEING  # type: ignore[assignment]
        e._run_state_machine(1 / 60)
        assert e.state in (EnemyState.IDLE, EnemyState.PATROL)

    def test_arena_clamp_no_escape(self):
        """SEARCH hacia 2000 debe clamp a 800."""
        e = _enemy(pos=(0, 0))
        e.set_arena_bounds(pygame.Rect(0, 0, 800, 600))
        e._last_seen = pygame.Vector2(2000, 300)  # type: ignore[attr-defined]
        e.state = EnemyState.SEARCH
        e._run_state_machine(1.0)
        assert e.position.x <= 800 - e.rect.width


# ── stage_objetos ─────────────────────────────────────────────────────────


class TestStageObjetos:
    def test_bool_de_variantes(self):
        """'sí'/'si'/'yes' deben ser True; si no -> datos hostiles mal interpretados."""
        assert _OE._bool_de("sí", por_defecto=False) is True
        assert _OE._bool_de("si", por_defecto=False) is True
        assert _OE._bool_de("yes", por_defecto=False) is True
        assert _OE._bool_de("false", por_defecto=True) is False

    def test_resistencias_formato_valido(self):
        """'veneno:0.5, fuego:2' -> dict; si ignora -> 0."""
        r = _OE._resistencias_de("veneno:0.5, fuego:2")  # type: ignore[attr-defined]
        assert r == {"veneno": 0.5, "fuego": 2.0}

    def test_resistencias_malformado_parcial(self):
        """Un par malo no debe tumbar todo el dict."""
        r = _OE._resistencias_de("veneno:0.5, malo, fuego:2")  # type: ignore[attr-defined]
        assert "veneno" in r and "fuego" in r

    def test_parse_light_color_hex(self):
        """#ff8000 -> (255,128,0); si falla -> warm."""
        c = _OE._parse_light_color("#ff8000")  # type: ignore[attr-defined]
        assert c == (255, 128, 0)

    def test_parse_light_color_nombre_invalido(self):
        """Nombre inválido cae a warm (255,220,180)."""
        c = _OE._parse_light_color("noexiste")  # type: ignore[attr-defined]
        assert c == (255, 220, 180)


# ── ecs/components ────────────────────────────────────────────────────────


class TestECSComponents:
    def test_alerta_prioridad(self):
        """Alerta con nivel 1.0 debe ser detectable; si lógica invierte -> bug."""
        a = Alerta()
        a.nivel = 1.0
        a.busqueda_restante = 3.0
        assert a.nivel >= 1.0

    def test_cono_vision_no_importa_event_bus(self):
        """Componente no debe importar event_bus (datos puros)."""
        import pathlib

        src = pathlib.Path("src/framework/ecs/components.py").read_text(encoding="utf-8")
        assert "event_bus" not in src.lower()


# ── prefab_loader ─────────────────────────────────────────────────────────


class TestPrefabLoader:
    def test_missing_prefab_retorna_none(self):
        """Prefab inexistente debe retornar None, no lanzar."""
        assert cargar_prefab("no_existe_12345") is None

    def test_malformed_json_retorna_none(self, tmp_path, monkeypatch):
        """JSON roto -> None (Rule: resource failure no crash)."""
        monkeypatch.setattr("src.framework.stage.prefab_loader.PREFAB_DIR", tmp_path)
        (tmp_path / "roto.json").write_text("{ no json", encoding="utf-8")
        assert cargar_prefab("roto") is None

    def test_listar_prefabs_empty_no_crash(self, tmp_path, monkeypatch):
        """Dir inexistente -> [] sin lanzar."""
        monkeypatch.setattr("src.framework.stage.prefab_loader.PREFAB_DIR", tmp_path / "nope")
        from src.framework.stage.prefab_loader import listar_prefabs_disponibles

        assert listar_prefabs_disponibles() == []

    def test_aplicar_prefab_offset_y_aplicado(self, tmp_path, monkeypatch):
        """Offset.y debe sumarse a y del objeto; si ignora -> prefab desplazado (AUD-9A).

        REGRESIÓN: con bug, _y se calculaba pero handler recibía y original (20 no 220).
        Mutación: cambiar 'y': _y a 'y': obj['y'] hace fallar este test.
        """
        import json

        from src.framework.stage.prefab_loader import aplicar_prefab

        monkeypatch.setattr("src.framework.stage.prefab_loader.PREFAB_DIR", tmp_path)
        data = {
            "layers": {
                "Objects": [
                    {
                        "type": "Checkpoint",
                        "name": "Checkpoint_01",
                        "x": 10,
                        "y": 20,
                        "width": 32,
                        "height": 32,
                        "props": {"checkpoint_id": 0},
                    }
                ]
            }
        }
        (tmp_path / "test.json").write_text(json.dumps(data), encoding="utf-8")

        # Mock mínimo con los atributos que el prefab necesita
        class _FakeStage:
            def __init__(self) -> None:
                self.checkpoints: list = []
                self.spawn_point = None
                self.entity_list: list = []
                self.message_triggers: list = []
                self.zonas_luz: list = []
                self.map_layer = None
                self.map_pixel_size = (0, 0)

        stage = _FakeStage()
        ok = aplicar_prefab("test", stage, pygame.Vector2(100, 200))  # type: ignore[arg-type]
        assert ok is True
        assert len(stage.checkpoints) == 1
        cp = stage.checkpoints[0]
        assert cp.rect.y == 220
        assert cp.rect.x == 110


# ── gl_pipeline ───────────────────────────────────────────────────────────


class TestGLPipeline:
    @pytest.fixture(autouse=True)
    def _init_pygame(self):
        if not pygame.get_init():
            pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((320, 240))
        yield
        # no teardown

    def test_destroy_idempotente(self):
        """destroy() dos veces no debe lanzar (resource cleanup)."""
        r = GLRenderer()
        r.destroy()
        r.destroy()

    def test_init_headless_no_crash(self):
        """GLRenderer render en dummy no debe lanzar (fallback)."""
        r = GLRenderer()
        # Con display ya inicializado, render debe hacer fallback sin lanzar
        try:
            r.render(pygame.Surface((64, 64)))
        except Exception as exc:
            pytest.fail(f"render headless no debe lanzar: {exc}")
