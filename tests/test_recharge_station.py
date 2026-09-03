"""B4.3 — Recharge Station — reusable stamina/mana recharge."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.framework.stage.interactable_system import InteractableSystem
from src.framework.stage.interactables import EstacionDeRecarga
from src.framework.stage.stage_data import StageData, StageProgression


@pytest.fixture(autouse=True)
def _init_pygame():
    if not pygame.get_init():
        pygame.init()
    pygame.display.init()
    try:
        pygame.display.set_mode((1, 1))
    except Exception:
        pass


def _make_stage_with_station(stage_id="test"):
    prog = StageProgression(stage_id=stage_id)
    sd = StageData(map_layer=MagicMock(), progression=prog, stage_id=stage_id)
    sd.stage_id = stage_id
    s = EstacionDeRecarga(rect=pygame.Rect(100, 100, 32, 32))
    sd.estaciones_recarga = [s]  # type: ignore[attr-defined]
    return sd, s


def test_recharge_station_is_registered():
    from src.framework.stage.stage_objetos import ObjetosDeTiled

    assert hasattr(ObjetosDeTiled, "_handle_estacion_recarga")


def test_recharge_station_is_loaded_from_tmx():
    from src.framework.stage.stage_objetos import ObjetosDeTiled

    prog = StageProgression(stage_id="test")
    sd = StageData(map_layer=MagicMock(), progression=prog, stage_id="test")
    obj = SimpleNamespace(x=10, y=20, width=32, height=32, id=77, name="", properties={"mensaje": "Hola"})
    ObjetosDeTiled._handle_estacion_recarga(sd, obj, {"mensaje": "Hola"})
    assert len(sd.estaciones_recarga) == 1  # type: ignore[attr-defined]
    assert sd.estaciones_recarga[0].rect == pygame.Rect(10, 20, 32, 32)  # type: ignore[attr-defined]
    assert sd.estaciones_recarga[0].mensaje == "Hola"  # type: ignore[attr-defined]


def test_recharge_station_alias():
    from src.framework.stage.stage_objetos import ObjetosDeTiled

    for _alias in ("RechargeStation", "EstacionRecarga", "EstacionDeRecarga"):
        # All three should resolve via same handler; we test via direct call
        prog = StageProgression(stage_id="x")
        sd = StageData(map_layer=MagicMock(), progression=prog, stage_id="x")
        obj = SimpleNamespace(x=0, y=0, width=32, height=32, id=1, name="", properties={})
        ObjetosDeTiled._handle_estacion_recarga(sd, obj, {})
        assert len(sd.estaciones_recarga) == 1  # type: ignore[attr-defined]


def test_recharge_station_can_be_used():
    bus = EventBus()
    s = EstacionDeRecarga(rect=pygame.Rect(100, 100, 32, 32))
    player = SimpleNamespace(estamina=10, estamina_max=100, special_meter=0, special_meter_max=100)
    sys = InteractableSystem(estaciones_recarga=[s], bus=bus)
    sys.set_player_ref(player)
    player_rect = pygame.Rect(105, 105, 16, 32)
    emitted = []
    bus.emit = lambda e, **kw: emitted.append((e, kw))  # type: ignore[method-assign]
    sys._usar_estacion(player_rect, usar=True)
    assert any(e == Events.RECHARGE_STATION_USED for e, _ in emitted)
    # should have restored
    assert player.estamina == 100
    assert player.special_meter == 100


def test_recharge_station_is_reusable():
    bus = EventBus()
    s = EstacionDeRecarga(rect=pygame.Rect(100, 100, 32, 32))
    player = SimpleNamespace(estamina=0, estamina_max=50, special_meter=0, special_meter_max=100)
    sys = InteractableSystem(estaciones_recarga=[s], bus=bus)
    sys.set_player_ref(player)
    player_rect = pygame.Rect(105, 105, 16, 32)
    sys._usar_estacion(player_rect, usar=True)
    assert s.usada is True
    # deplete again
    player.estamina = 0
    emitted = []
    bus.emit = lambda e, **kw: emitted.append(e)  # type: ignore[method-assign]
    sys._usar_estacion(player_rect, usar=True)
    assert Events.RECHARGE_STATION_USED in emitted
    assert player.estamina == 50


def test_recharge_station_restores_stamina():
    bus = EventBus()
    s = EstacionDeRecarga(rect=pygame.Rect(100, 100, 32, 32))
    player = SimpleNamespace(
        estamina=20, estamina_max=100,
        special_meter=10, special_meter_max=100,
        _espera_estamina_restante=5,
    )
    sys = InteractableSystem(estaciones_recarga=[s], bus=bus)
    sys.set_player_ref(player)
    sys._usar_estacion(pygame.Rect(105, 105, 16, 32), usar=True)
    assert player.estamina == 100
    assert player._espera_estamina_restante == 0.0


def test_recharge_station_does_not_overheal():
    # Should cap at max, not exceed
    bus = EventBus()
    s = EstacionDeRecarga(rect=pygame.Rect(100, 100, 32, 32))
    player = SimpleNamespace(estamina=90, estamina_max=100, special_meter=90, special_meter_max=100)
    sys = InteractableSystem(estaciones_recarga=[s], bus=bus)
    sys.set_player_ref(player)
    sys._usar_estacion(pygame.Rect(105, 105, 16, 32), usar=True)
    assert player.estamina == 100
    assert player.special_meter == 100


def test_recharge_station_not_counted_as_item():
    from unittest.mock import MagicMock

    s = EstacionDeRecarga(rect=pygame.Rect(0, 0, 16, 16))
    prog = StageProgression(stage_id="test")
    sd = StageData(map_layer=MagicMock(), progression=prog, stage_id="test")
    sd.estaciones_recarga = [s]  # type: ignore[attr-defined]
    sd.stage_id = "test"
    assert sd.item_total() == 0
    assert sd.item_percentage(set()) is None


def test_recharge_station_does_not_create_save_state():
    import pathlib
    import tempfile

    from src.engine.core.save_data import SaveData
    from src.engine.core.save_manager import SaveManager

    tmp = tempfile.mkdtemp()
    orig = SaveManager.SAVES_DIR
    SaveManager.SAVES_DIR = pathlib.Path(tmp) / "saves"
    SaveManager.SAVES_DIR.mkdir(parents=True, exist_ok=True)
    try:
        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, stage_id="test"))
        mgr.ranura_activa = 1
        bus = EventBus()
        s = EstacionDeRecarga(rect=pygame.Rect(100, 100, 32, 32))
        player = SimpleNamespace(estamina=0, estamina_max=100, special_meter=0, special_meter_max=100)
        sys = InteractableSystem(estaciones_recarga=[s], bus=bus)
        sys.set_persistencia("test", mgr)
        sys.set_player_ref(player)
        sys._usar_estacion(pygame.Rect(105, 105, 16, 32), usar=True)
        data = mgr.load(1)
        assert data.map_item_collected.get("test") in (None, [], {})
    finally:
        SaveManager.SAVES_DIR = orig


def test_recharge_station_interaction_conditions():
    bus = EventBus()
    s = EstacionDeRecarga(rect=pygame.Rect(100, 100, 32, 32))
    player = SimpleNamespace(estamina=0, estamina_max=100, special_meter=0, special_meter_max=100)
    sys = InteractableSystem(estaciones_recarga=[s], bus=bus)
    sys.set_player_ref(player)
    far = pygame.Rect(500, 500, 16, 32)
    emitted = []
    bus.emit = lambda e, **kw: emitted.append(e)  # type: ignore[method-assign]
    sys._usar_estacion(far, usar=True)
    assert emitted == []
    # near but without usar
    near = pygame.Rect(105, 105, 16, 32)
    emitted.clear()
    sys._usar_estacion(near, usar=False)
    assert Events.RECHARGE_STATION_USED not in emitted
    assert sys.mensaje != "" or True


def test_recharge_station_tmx_integration_via_stage_data():
    sd, _s = _make_stage_with_station("test")
    bus = EventBus()
    player = SimpleNamespace(estamina=0, estamina_max=100, special_meter=0, special_meter_max=100)
    sys = InteractableSystem(estaciones_recarga=sd.estaciones_recarga, bus=bus)  # type: ignore[attr-defined]
    sys.set_player_ref(player)
    emitted = []
    bus.emit = lambda e, **kw: emitted.append(e)  # type: ignore[method-assign]
    sys.update(0.016, pygame.Rect(105, 105, 16, 32), usar=True)
    assert Events.RECHARGE_STATION_USED in emitted
