"""AUD-610 — GAP-073: la reencarnación ya tiene pantalla.

`Inventory.reencarnar()` existía (AUD-609) sin ningún sitio donde
pulsarlo — el mismo patrón que GAP-029 documentó para la tienda. Ahora
`SkillTreeScene` lo ofrece con confirmación en dos pasos, y estas pruebas
fijan su contrato:

* por debajo del nivel exigido, ni pregunta;
* la primera pulsación pregunta, la segunda ejecuta;
* Cancelar deshace la pregunta antes que salir del menú;
* tras reencarnar: prestigio +1, experiencia y árbol a cero.
"""
from __future__ import annotations

import types

import pygame
import pytest

from src.engine.core import inventory as inv_mod
from src.engine.core.inventory import Inventory
from src.engine.input.action_map import Action


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


@pytest.fixture(autouse=True)
def _estado_aislado(tmp_path, monkeypatch):
    """Inventario a fichero temporal; singletons de exp/árbol recién hechos."""
    from src.engine.core.experience import ExperienceSystem
    from src.engine.core.skill_tree import ArbolDeHabilidades

    monkeypatch.setattr(inv_mod, "_INVENTORY_PATH", tmp_path / "inventory.json")
    inv = Inventory()
    inv._items.clear()
    inv._equipped.clear()
    inv.prestigio = 0

    ExperienceSystem._reset_instance()
    ArbolDeHabilidades._reset_instance()
    yield
    inv.prestigio = 0
    inv._items.clear()
    inv._equipped.clear()
    Inventory._reset_instance()
    ExperienceSystem._reset_instance()
    ArbolDeHabilidades._reset_instance()


class _Input:
    def __init__(self) -> None:
        self._pendientes: list[Action] = []

    def pulsar(self, accion: Action) -> None:
        self._pendientes.append(accion)

    def is_action_just_pressed(self, accion: Action) -> bool:
        if accion in self._pendientes:
            self._pendientes.remove(accion)
            return True
        return False


@pytest.fixture
def escena():
    from src.engine.scenes.skill_tree_scene import SkillTreeScene

    entrada = _Input()
    gestor = types.SimpleNamespace(
        transition=types.SimpleNamespace(start_fade_in=lambda *a, **k: None),
        pop=lambda: setattr(gestor, "salio_por_pop", True),
        salio_por_pop=False,
    )
    bus = types.SimpleNamespace(
        emit=lambda *a, **k: bus.recibidos.append((a, k)),
        recibidos=[],
    )
    contexto = types.SimpleNamespace(
        input_manager=entrada,
        scene_manager=gestor,
        audio_manager=None,
        event_bus=bus,
    )
    escena = SkillTreeScene(contexto)
    return escena


def _subir_a(escena, nivel: int) -> None:
    from src.engine.core.experience import exp_para_nivel

    exp = ExperienceSystem_get()
    exp.grant(exp_para_nivel(nivel) + 10)


def ExperienceSystem_get():
    from src.engine.core.experience import ExperienceSystem

    return ExperienceSystem.get_instance()


class TestLaReencarnacionEnPantalla:
    def test_por_debajo_del_nivel_no_hay_prestigio(self, escena) -> None:
        _subir_a(escena, 3)
        inventario = Inventory()

        escena._intentar_reencarnar()

        assert inventario.prestigio == 0
        assert "nivel" in escena._mensaje.lower()
        assert escena._confirmar_reencarnar is False

    def test_dos_pulsaciones_reencarnan(self, escena) -> None:
        _subir_a(escena, Inventory.NIVEL_DE_REENCARNACION)
        from src.engine.core.skill_tree import ArbolDeHabilidades

        ArbolDeHabilidades.get_instance().comprar("vitalidad")
        inventario = Inventory()

        # Primera pulsación: pregunta, no ejecuta.
        escena._intentar_reencarnar()
        assert escena._confirmar_reencarnar is True
        assert inventario.prestigio == 0
        assert ExperienceSystem_get().exp > 0

        # Segunda: ejecuta.
        escena._intentar_reencarnar()
        assert inventario.prestigio == 1
        assert inventario.get_xp_multiplier() == pytest.approx(1.05)
        assert ExperienceSystem_get().exp == 0
        assert ArbolDeHabilidades.get_instance().to_dict() == {}
        assert escena._confirmar_reencarnar is False

    def test_cancelar_deshace_la_pregunta_y_luego_sale(self, escena) -> None:
        _subir_a(escena, Inventory.NIVEL_DE_REENCARNACION)
        entrada = escena.context.input_manager

        escena._intentar_reencarnar()
        assert escena._confirmar_reencarnar is True

        entrada.pulsar(Action.CANCEL)
        escena.update(0.016)
        assert escena._confirmar_reencarnar is False
        # No salió del menú: sólo se deshizo la pregunta.
        assert escena.context.scene_manager.salio_por_pop is False

        entrada.pulsar(Action.CANCEL)
        escena.update(0.016)
        assert escena.context.scene_manager.salio_por_pop is True

    def test_el_camino_por_update_llega_al_mismo_sitio(self, escena) -> None:
        _subir_a(escena, Inventory.NIVEL_DE_REENCARNACION)
        entrada = escena.context.input_manager

        entrada.pulsar(Action.RANGED_ATTACK)
        escena.update(0.016)
        entrada.pulsar(Action.RANGED_ATTACK)
        escena.update(0.016)

        assert Inventory().prestigio == 1
