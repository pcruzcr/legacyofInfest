from __future__ import annotations

import logging
from typing import TypedDict

import orjson
import pygame
from pydantic import BaseModel

from src.engine.core import settings

logger = logging.getLogger(__name__)


class _NotificationData(TypedDict):
    id: str
    name: str
    description: str
    color: tuple[int, int, int]
    timer: float


_INVENTORY_PATH = settings.PROJECT_ROOT / "data/inventory.json"


class ItemDef(BaseModel):
    id: str
    name: str
    description: str
    icon_color: tuple[int, int, int] = (200, 200, 100)
    max_hp_bonus: float = 0.0
    speed_bonus: float = 0.0
    damage_bonus: float = 0.0


_ITEM_DEFS: dict[str, ItemDef] = {
    "heart_vessel": ItemDef(
        id="heart_vessel", name="Heart Vessel",
        description="+1 max HP",
        icon_color=(220, 60, 60), max_hp_bonus=1.0,
    ),
    "hollow_eye": ItemDef(
        id="hollow_eye", name="Hollow Eye",
        description="See enemy telegraphs clearer (damage +0.3)",
        icon_color=(180, 100, 220), damage_bonus=0.3,
    ),
    "ancients_rib": ItemDef(
        id="ancients_rib", name="Ancient's Rib",
        description="+2 max HP, resists decay",
        icon_color=(200, 180, 100), max_hp_bonus=2.0,
    ),
    "swift_feather": ItemDef(
        id="swift_feather", name="Swift Feather",
        description="Move 10% faster",
        icon_color=(100, 200, 220), speed_bonus=10.0,
    ),
    "thorn_ring": ItemDef(
        id="thorn_ring", name="Thorn Ring",
        description="Damage +0.5",
        icon_color=(60, 180, 60), damage_bonus=0.5,
    ),
    "sunken_crown": ItemDef(
        id="sunken_crown", name="Sunken Crown",
        description="+3 max HP, damage +0.8",
        icon_color=(220, 200, 40), max_hp_bonus=3.0, damage_bonus=0.8,
    ),
}


class Inventory:
    _instance: Inventory | None = None
    _initialized: bool = False

    def __new__(cls) -> Inventory:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._items: dict[str, int] = {}
        self._collect_notifications: list[_NotificationData] = []
        self._current_notify: _NotificationData | None = None
        self._notif_bg: pygame.Surface | None = None
        self.load()

    def collect(self, item_id: str) -> bool:
        if item_id not in _ITEM_DEFS:
            return False
        self._items[item_id] = self._items.get(item_id, 0) + 1
        defn = _ITEM_DEFS[item_id]
        self._collect_notifications.append({
            "id": defn.id,
            "name": defn.name,
            "description": defn.description,
            "color": defn.icon_color,
            "timer": 3.0,
        })
        self.save()
        from src.engine.core.achievements import AchievementSystem
        AchievementSystem.get_instance().progress("collector")
        return True

    def has(self, item_id: str) -> bool:
        return self._items.get(item_id, 0) > 0

    def count(self, item_id: str) -> int:
        return self._items.get(item_id, 0)

    def get_def(self, item_id: str) -> ItemDef | None:
        return _ITEM_DEFS.get(item_id)

    def get_total_hp_bonus(self) -> float:
        total = 0.0
        for item_id, count in self._items.items():
            defn = _ITEM_DEFS.get(item_id)
            if defn:
                total += defn.max_hp_bonus * count
        return total

    def get_total_speed_bonus(self) -> float:
        total = 0.0
        for item_id, count in self._items.items():
            defn = _ITEM_DEFS.get(item_id)
            if defn:
                total += defn.speed_bonus * count
        return total

    def get_total_damage_bonus(self) -> float:
        total = 0.0
        for item_id, count in self._items.items():
            defn = _ITEM_DEFS.get(item_id)
            if defn:
                total += defn.damage_bonus * count
        return total

    @property
    def items(self) -> dict[str, int]:
        return self._items

    def get_all_collected(self) -> list[tuple[str, int]]:
        return [(iid, cnt) for iid, cnt in self._items.items()]

    def save(self) -> None:
        data = {"items": dict(self._items)}
        _INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        _INVENTORY_PATH.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))

    def load(self) -> None:
        try:
            raw = _INVENTORY_PATH.read_bytes()
            data = orjson.loads(raw)
            self._items = {k: v for k, v in data.get("items", {}).items() if k in _ITEM_DEFS}
        # AUD-100 — la corrupción se tragaba en silencio.
        #
        # `orjson.JSONEncodeError` **es `TypeError`**, y codificar no puede
        # fallar dentro de un `loads`: estaba de más. Lo que de verdad atrapa
        # un fichero corrupto es `ValueError`, del que `orjson.JSONDecodeError`
        # hereda. Así que el `except` funcionaba, pero por una razón distinta
        # de la que aparentaba.
        #
        # El defecto real era el silencio. Los objetos recogidos se perdían sin una línea en
        # el registro, y el estudiante veía un inventario vacío sin ninguna pista de por
        # qué. `ProgresoAcademico.cargar` ya avisaba en el mismo caso; tres
        # sitios del proyecto hacían lo contrario ante el mismo problema.
        except FileNotFoundError:
            logger.debug("inventory: sin fichero previo; se empieza de cero")
            self._items = {}
        except (ValueError, TypeError):
            logger.warning(
                "inventory: %s ilegible; se empieza de cero",
                _INVENTORY_PATH, exc_info=True,
            )
            self._items = {}

    def update_notifications(self, dt: float) -> None:
        if self._current_notify is not None:
            self._current_notify["timer"] -= dt
            if self._current_notify["timer"] <= 0:
                self._current_notify = None
        if self._current_notify is None and self._collect_notifications:
            self._current_notify = self._collect_notifications.pop(0)

    def draw_notifications(self, surface: pygame.Surface) -> None:
        if self._current_notify is None:
            return
        n = self._current_notify
        w = settings.INTERNAL_WIDTH
        bar_w = 240
        bar_h = 32
        bx = (w - bar_w) // 2
        by = 8
        if self._notif_bg is None or self._notif_bg.get_size() != (bar_w, bar_h):
            self._notif_bg = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        bg = self._notif_bg
        bg.fill((10, 10, 10, 200))
        surface.blit(bg, (bx, by))
        pygame.draw.rect(surface, n["color"], (bx, by, bar_w, bar_h), 2)
        font = pygame.font.Font(None, 14)
        parts = [
            (font.render("ITEM: ", True, (200, 200, 200)), 8),
            (font.render(n["name"], True, n["color"]), None),
        ]
        cx = bx + 8
        for surf, _ in parts:
            surface.blit(surf, (cx, by + 8))
            cx += surf.get_width() + 4


def get_inventory() -> Inventory:
    return Inventory()
