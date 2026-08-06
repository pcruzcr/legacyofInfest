from __future__ import annotations

import logging
from collections.abc import Callable
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
    #: Ropa equipable. `None` = objeto de mejora o llave, no se equipa.
    slot: str | None = None
    #: Precio en monedas. `0` = no se compra ni se vende (mejora/llave).
    price: int = 0


_ITEM_DEFS: dict[str, ItemDef] = {
    # ── Mejoras permanentes (se recogen en el mapa) ────────────────
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
    # ── Moneda ─────────────────────────────────────────────────────
    "coin": ItemDef(
        id="coin", name="Coin",
        description="Currency for the shop",
        icon_color=(255, 215, 0),
    ),
    # ── Ropa equipable (se compra en la tienda) ────────────────────
    "hood_leaf": ItemDef(
        id="hood_leaf", name="Leaf Hood",
        description="Jungle hood. +0.2 damage",
        icon_color=(80, 160, 60), slot="head", damage_bonus=0.2, price=30,
    ),
    "hood_ember": ItemDef(
        id="hood_ember", name="Ember Hood",
        description="Warm hood. +0.5 max HP",
        icon_color=(220, 120, 40), slot="head", max_hp_bonus=0.5, price=40,
    ),
    "cloak_reed": ItemDef(
        id="cloak_reed", name="Reed Cloak",
        description="Light cloak. +5% speed",
        icon_color=(120, 180, 120), slot="body", speed_bonus=5.0, price=35,
    ),
    "cloak_serpent": ItemDef(
        id="cloak_serpent", name="Serpent Cloak",
        description="Venom cloak. +0.4 damage",
        icon_color=(60, 140, 60), slot="body", damage_bonus=0.4, price=50,
    ),
    "boots_swift": ItemDef(
        id="boots_swift", name="Swift Boots",
        description="+8% speed",
        icon_color=(100, 200, 220), slot="feet", speed_bonus=8.0, price=45,
    ),
    "boots_stone": ItemDef(
        id="boots_stone", name="Stone Boots",
        description="+1 max HP",
        icon_color=(160, 160, 160), slot="feet", max_hp_bonus=1.0, price=40,
    ),
    # ── Habilidades (drops de jefes) ───────────────────────────────
    "skill_double_jump": ItemDef(
        id="skill_double_jump", name="Double Jump",
        description="Boss drop: jump again in mid-air",
        icon_color=(200, 100, 255), slot="skill",
    ),
    "skill_dash": ItemDef(
        id="skill_dash", name="Dash",
        description="Boss drop: quick dash forward",
        icon_color=(100, 200, 255), slot="skill",
    ),
    "skill_parry": ItemDef(
        id="skill_parry", name="Parry",
        description="Boss drop: deflect attacks",
        icon_color=(255, 200, 100), slot="skill",
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
        self._equipped: dict[str, str] = {}
        self._collect_notifications: list[_NotificationData] = []
        self._current_notify: _NotificationData | None = None
        self._notif_bg: pygame.Surface | None = None
        self.load()

    def collect(self, item_id: str, cantidad: int = 1) -> bool:
        """Entra `cantidad` unidades del objeto y avisa **una vez**.

        AUD-218: el aviso se emite una sola vez por recogida, no una por
        unidad. Una bolsa de diez monedas encolaba diez notificaciones de tres
        segundos cada una y tapaba la pantalla medio minuto.
        """
        if item_id not in _ITEM_DEFS:
            return False
        if cantidad < 1:
            return False
        self._items[item_id] = self._items.get(item_id, 0) + cantidad
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

    def _sumar_bonus(self, extraer: Callable[[ItemDef], float]) -> float:
        """Suma un bonus sobre las dos familias de objetos, que cuentan
        distinto (AUD-207).

        Antes esto recorría `_items` entero multiplicando por la cantidad, sin
        mirar `_equipped` ni una vez. Con ese cálculo la ropa daba su bonus
        guardada en la mochila, las dos capuchas apilaban pese a compartir
        `slot="head"`, y comprar la misma prenda dos veces valía el doble. La
        tienda vendía números en lugar de ropa, y no había nada que elegir.

        * **Mejoras permanentes** (`slot is None`): se recogen en el mapa y
          apilan por cantidad. Dos vasijas de corazón son +2 de vida, y así
          debe seguir — los niveles están diseñados contando con eso.
        * **Ropa** (`slot` de ropa): cuenta una vez y sólo si está puesta. El
          hueco es el que obliga a elegir; sin esta regla no es un hueco.
        * **Habilidades** (`slot="skill"`): no dan estadísticas. No entran por
          ninguna de las dos ramas porque `equip()` las rechaza.
        """
        total = 0.0
        for item_id, count in self._items.items():
            defn = _ITEM_DEFS.get(item_id)
            if defn is not None and defn.slot is None:
                total += extraer(defn) * count
        for item_id in self._equipped.values():
            defn = _ITEM_DEFS.get(item_id)
            if defn is not None:
                total += extraer(defn)
        return total

    def get_total_hp_bonus(self) -> float:
        return self._sumar_bonus(lambda d: d.max_hp_bonus)

    def get_total_speed_bonus(self) -> float:
        return self._sumar_bonus(lambda d: d.speed_bonus)

    def get_total_damage_bonus(self) -> float:
        return self._sumar_bonus(lambda d: d.damage_bonus)

    @property
    def items(self) -> dict[str, int]:
        return self._items

    def get_all_collected(self) -> list[tuple[str, int]]:
        return [(iid, cnt) for iid, cnt in self._items.items()]

    # ── Monedas ────────────────────────────────────────────────────
    @property
    def coins(self) -> int:
        """Saldo de monedas (el item `coin` es la moneda del juego)."""
        return self._items.get("coin", 0)

    def add_coins(self, amount: int) -> None:
        """Suma monedas al saldo y persiste."""
        if amount <= 0:
            return
        self._items["coin"] = self._items.get("coin", 0) + amount
        self.save()

    def spend_coins(self, amount: int) -> bool:
        """Resta monedas si hay saldo. Devuelve `True` si se pudo gastar."""
        if amount <= 0:
            return True
        if self.coins < amount:
            return False
        self._items["coin"] = self.coins - amount
        self.save()
        return True

    # ── Tienda: comprar y vender ───────────────────────────────────
    def buy(self, item_id: str) -> bool:
        """Compra un item de ropa/habilidad con monedas. Devuelve `True` si se compró."""
        defn = _ITEM_DEFS.get(item_id)
        if defn is None or defn.price <= 0:
            return False
        if not self.spend_coins(defn.price):
            return False
        self._items[item_id] = self._items.get(item_id, 0) + 1
        self.save()
        return True

    def sell(self, item_id: str) -> bool:
        """Vende un item de ropa/habilidad por la mitad de su precio. Devuelve `True` si se vendió."""
        defn = _ITEM_DEFS.get(item_id)
        if defn is None or defn.price <= 0:
            return False
        if self._items.get(item_id, 0) <= 0:
            return False
        self._items[item_id] -= 1
        if self._items[item_id] <= 0:
            del self._items[item_id]
            # AUD-207: vender la última copia no la quitaba de `_equipped`, así
            # que te quedabas el bonus de una prenda que ya no tienes —y podías
            # repetirlo con cada prenda hasta llevarlas todas puestas sin
            # ninguna. Se desequipa sólo cuando se va la última: con dos copias
            # sigues teniendo una que ponerte.
            if self._equipped.get(defn.slot or "") == item_id:
                del self._equipped[defn.slot or ""]
        self.add_coins(defn.price // 2)
        return True

    # ── Equipamiento ──────────────────────────────────────────────
    def equip(self, item_id: str) -> bool:
        """Equipa un item de ropa en su slot. Devuelve `True` si se equipó."""
        defn = _ITEM_DEFS.get(item_id)
        if defn is None or defn.slot is None or defn.slot == "skill":
            return False
        if self._items.get(item_id, 0) <= 0:
            return False
        self._equipped[defn.slot] = item_id
        self.save()
        return True

    def unequip(self, slot: str) -> bool:
        """Quita la ropa del slot. Devuelve `True` si había algo equipado."""
        if slot not in self._equipped:
            return False
        del self._equipped[slot]
        self.save()
        return True

    def get_equipped(self) -> dict[str, str]:
        """Devuelve `{slot: item_id}` de la ropa equipada."""
        return dict(self._equipped)

    def has_skill(self, skill_id: str) -> bool:
        """¿Tiene el jugador esta habilidad (drop de jefe)?"""
        return self._items.get(skill_id, 0) > 0

    def all_items(self) -> dict[str, int]:
        """Copia de lo que lleva encima. Para volcarlo en la partida (AUD-292)."""
        return dict(self._items)

    def restaurar(self, items: dict[str, int],
                  equipado: dict[str, str] | None = None) -> None:
        """Sustituye el inventario entero por el de una partida — AUD-292.

        **Sustituye, no funde.** Cargar la partida 2 tiene que dejar la cartera
        de la partida 2; fundirla con lo que hubiera en memoria daría a quien
        cambia de slot el dinero de los dos, que es exactamente el defecto que
        esto viene a cerrar.

        Se descarta lo que no está en el catálogo, por lo mismo que `load`: un
        fichero editado a mano no debe poder meter objetos inventados.
        """
        self._items = {
            str(k): max(0, int(v))
            for k, v in dict(items or {}).items()
            if k in _ITEM_DEFS and int(v) > 0
        }
        # Y la ropa con el mismo filtro que `load`: sólo prendas que se tienen
        # y en su propia ranura. Una partida editada a mano no debe poder
        # cobrar el bonus de algo que no está en el inventario (AUD-207).
        self._equipped = {
            str(slot): str(iid)
            for slot, iid in dict(equipado or {}).items()
            if (defn := _ITEM_DEFS.get(str(iid))) is not None
            and defn.slot == slot
            and defn.slot != "skill"
            and self._items.get(str(iid), 0) > 0
        }
        self.save()

    def save(self) -> None:
        data = {"items": dict(self._items), "equipped": dict(self._equipped)}
        _INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        _INVENTORY_PATH.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))

    def load(self) -> None:
        try:
            raw = _INVENTORY_PATH.read_bytes()
            data = orjson.loads(raw)
            self._items = {k: v for k, v in data.get("items", {}).items() if k in _ITEM_DEFS}
            # Solo se restauran slots de ropa válidos (no habilidades).
            #
            # AUD-207: y sólo de prendas que de verdad se tienen. Sin el último
            # filtro, un `inventory.json` editado a mano —o dejado a medias por
            # un guardado interrumpido— podía declarar puesta una prenda que no
            # está en `items` y cobrar su bonus gratis. Ahora que los totales
            # leen `_equipped`, ese fichero es una entrada más que validar.
            self._equipped = {
                slot: item_id
                for slot, item_id in data.get("equipped", {}).items()
                if (defn := _ITEM_DEFS.get(item_id)) is not None
                and defn.slot == slot
                and defn.slot != "skill"
                and self._items.get(item_id, 0) > 0
            }
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
        # AUD-207: «de cero» incluye lo que se lleva puesto. Estas dos ramas
        # vaciaban `_items` y dejaban `_equipped` como estuviera; daba igual
        # mientras nadie leyera ese diccionario, pero ahora los totales sí lo
        # leen: recargar sobre un fichero ilegible conservaba los bonus de una
        # ropa que ya no está en el inventario.
        except FileNotFoundError:
            logger.debug("inventory: sin fichero previo; se empieza de cero")
            self._items = {}
            self._equipped = {}
        except (ValueError, TypeError):
            logger.warning(
                "inventory: %s ilegible; se empieza de cero",
                _INVENTORY_PATH, exc_info=True,
            )
            self._items = {}
            self._equipped = {}

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
