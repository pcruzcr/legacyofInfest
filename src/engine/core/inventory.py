from __future__ import annotations

import logging
from typing import TypedDict

import orjson
import pygame
from pydantic import BaseModel

from src.engine.core import settings
from src.engine.core.save_manager import migrar_desde_el_arbol
from src.engine.core.user_settings import user_data_dir

logger = logging.getLogger(__name__)


class _NotificationData(TypedDict):
    id: str
    name: str
    description: str
    color: tuple[int, int, int]
    timer: float


#: Dónde vive el inventario del jugador. AUD-337 - nació en
#: data/inventory.json, dentro del árbol del proyecto; una instalación
#: empaquetada puede tener ese árbol en un sitio de solo lectura, así que
#: el estado del jugador va al directorio del usuario, como las partidas
#: (AUD-157) y los logros. El fichero viejo se migra una vez (no se borra).
_RUTA_POR_DEFECTO = user_data_dir() / "inventory.json"
_INVENTORY_PATH = _RUTA_POR_DEFECTO
#: De dónde se migra: el sitio histórico, solo lectura en empaquetado.
_RUTA_ANTIGUA = settings.PROJECT_ROOT / "data/inventory.json"


class ItemDef(BaseModel):
    id: str
    name: str
    description: str
    icon_color: tuple[int, int, int] = (200, 200, 100)
    max_hp_bonus: float = 0.0
    speed_bonus: float = 0.0
    damage_bonus: float = 0.0
    #: Ropa equipable. None = objeto de mejora o llave, no se equipa.
    slot: str | None = None
    #: Precio en monedas.  = no se compra ni se vende (mejora/llave).
    price: int = 0
    # AUD-559 - la propuesta de economía del dueño: la tienda solo tenía
    #: ropa permanente, nada que gastarse en un apuro puntual.
    #: consumible=True es la mitad que falta: un objeto que se **usa**
    #: (una unidad menos, un efecto inmediato) en vez de equiparse o
    #: acumular estadística para siempre.
    consumible: bool = False
    #: Vida que restaura al usarse. Sólo tiene sentido con
    #: consumible=True - separado de max_hp_bonus a propósito: ese
    #: campo es un bono *permanente* que Inventory._sumar_bonus suma
    #: mientras el objeto está en la mochila (o puesto); esto es un
    #: efecto de una sola vez que no debe contarse dos veces.
    heal_hp: float = 0.0


_ITEM_DEFS: dict[str, ItemDef] = {
    # Mejoras permanentes (se recogen en el mapa)
    "heart_vessel": ItemDef(
        id="heart_vessel", name="Vasija de corazón",
        description="+1 de vida máxima",
        icon_color=(220, 60, 60), max_hp_bonus=1.0,
    ),
    "hollow_eye": ItemDef(
        id="hollow_eye", name="Ojo hueco",
        description="Lees mejor los avisos del enemigo (+0,3 de daño)",
        icon_color=(180, 100, 220), damage_bonus=0.3,
    ),
    "ancients_rib": ItemDef(
        id="ancients_rib", name="Costilla del anciano",
        description="+2 de vida máxima, resiste la putrefacción",
        icon_color=(200, 180, 100), max_hp_bonus=2.0,
    ),
    "swift_feather": ItemDef(
        id="swift_feather", name="Pluma veloz",
        description="Te mueves un 10 % más rápido",
        icon_color=(100, 200, 220), speed_bonus=10.0,
    ),
    "thorn_ring": ItemDef(
        id="thorn_ring", name="Anillo de espinas",
        description="+0,5 de daño",
        icon_color=(60, 180, 60), damage_bonus=0.5,
    ),
    "sunken_crown": ItemDef(
        id="sunk_crown", name="Corona hundida",
        description="+3 de vida máxima, +0,8 de daño",
        icon_color=(220, 200, 40), max_hp_bonus=3.0, damage_bonus=0.8,
    ),
    # Moneda
    "coin": ItemDef(
        id="coin", name="Moneda",
        description="La moneda de la tienda",
        icon_color=(255, 215, 0),
    ),
    # Ropa equipable (se compra en la tienda)
    "hood_leaf": ItemDef(
        id="hood_leaf", name="Capucha de hoja",
        description="Capucha de selva. +0,2 de daño",
        icon_color=(80, 160, 60), slot="head", damage_bonus=0.2, price=30,
    ),
    "hood_ember": ItemDef(
        id="hood_ember", name="Capucha de brasa",
        description="Capucha abrigada. +0,5 de vida máxima",
        icon_color=(220, 120, 40), slot="head", max_hp_bonus=0.5, price=40,
    ),
    "cloak_reed": ItemDef(
        id="cloak_reed", name="Capa de junco",
        description="Capa ligera. +5 % de velocidad",
        icon_color=(120, 180, 120), slot="body", speed_bonus=5.0, price=35,
    ),
    "cloak_serpent": ItemDef(
        id="cloak_serpent", name="Capa de serpiente",
        description="Capa venenosa. +0,4 de daño",
        icon_color=(60, 140, 60), slot="body", damage_bonus=0.4, price=50,
    ),
    "boots_swift": ItemDef(
        id="boots_swift", name="Botas veloces",
        description="+8 % de velocidad",
        icon_color=(100, 200, 220), slot="feet", speed_bonus=8.0, price=45,
    ),
    "boots_stone": ItemDef(
        id="boots_stone", name="Botas de piedra",
        description="+1 de vida máxima",
        icon_color=(160, 160, 160), slot="feet", max_hp_bonus=1.0, price=40,
    ),
    # AUD-559 - el objeto "capa abisal" combina vida + daño
    "cloak_abyssal": ItemDef(
        id="cloak_abyssal", name="Capa abisal",
        description="Capa de las profundidades. +1,5 de vida máxima, +0,6 de daño",
        icon_color=(40, 60, 90), slot="body",
        max_hp_bonus=1.5, damage_bonus=0.6, price=90,
    ),
    # AUD-559 - el primer objeto consumible de la tienda
    "tonic_sap": ItemDef(
        id="tonic_sap", name="Tónico de savia",
        description="Se usa una vez: restaura 2 de vida",
        icon_color=(120, 200, 90), price=15,
        consumible=True, heal_hp=2.0,
    ),
    # Habilidades (drops de jefes)
    "skill_double_jump": ItemDef(
        id="skill_double_jump", name="Salto doble",
        description="Botón de jefe: saltas otra vez en el aire",
        icon_color=(200, 100, 255), slot="skill",
    ),
    "skill_dash": ItemDef(
        id="skill_dash", name="Impulso",
        description="Botón de jefe: impulso rápido hacia delante",
        icon_color=(100, 200, 255), slot="skill",
    ),
    "skill_parry": ItemDef(
        id="skill_parry", name="Parada",
        description="Botón de jefe: desvías los ataques",
        icon_color=(255, 200, 100), slot="skill",
),
}


def _migrar_inventario() -> None:
    """Migra el fichero viejo una vez, y sólo con la ruta de producción.
    Las pruebas redirigen _INVENTORY_PATH a un directorio temporal: ahí no
    se migra nada, el fichero viejo del repositorio es de desarrollo y no
    tiene por qué colarse en una prueba.
    """
    if _INVENTORY_PATH == _RUTA_POR_DEFECTO:
        migrar_desde_el_arbol(_INVENTORY_PATH, _RUTA_ANTIGUA)


class Inventory:
    _instance: Inventory | None = None
    _initialized: bool = False

    #: AUD-609 — nivel mínimo para reencarnar. Diez niveles cuestan
    #: `_EXP_BASE * 10 * 11 / 2` = 5.500 XP de la curva cuadrática: unas
    #: cuantas horas de partida. Menos que eso y reencarnar sería un botón
    #: de rutina en vez de una decisión.
    NIVEL_DE_REENCARNACION: int = 10

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
        self._collect_notifications: list = []
        self._current_notify = None
        self._notif_bg: pygame.Surface | None = None
        # AUD-609 — puntos de prestigio ganados al reencarnar. Vive en el
        # inventario y no en `ExperienceSystem` porque sobrevive al reseteo
        # de la experiencia: es exactamente lo que la reencarnación compra.
        self.prestigio: int = 0
        self.load()

    def collect(self, item_id: str, cantidad: int = 1) -> bool:
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

    def get_def(self, item_id: str):
        return _ITEM_DEFS.get(item_id)

    def _sumar_bonus(self, extraer):
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

    @property
    def coins(self) -> int:
        return self._items.get("coin", 0)

    def add_coins(self, amount: int) -> None:
        if amount <= 0:
            return
        self._items["coin"] = self._items.get("coin", 0) + amount
        self.save()

    def spend_coins(self, amount: int) -> bool:
        if amount <= 0:
            return True
        if self.coins < amount:
            return False
        self._items["coin"] = self.coins - amount
        self.save()
        return True

    def buy(self, item_id: str) -> bool:
        defn = _ITEM_DEFS.get(item_id)
        if defn is None or defn.price <= 0:
            return False
        if not self.spend_coins(defn.price):
            return False
        self._items[item_id] = self._items.get(item_id, 0) + 1
        self.save()
        return True

    def sell(self, item_id: str) -> bool:
        defn = _ITEM_DEFS.get(item_id)
        if defn is None or defn.price <= 0:
            return False
        if self._items.get(item_id, 0) <= 0:
            return False
        self._items[item_id] -= 1
        if self._items[item_id] <= 0:
            del self._items[item_id]
            if self._equipped.get(defn.slot or "") == item_id:
                del self._equipped[defn.slot or ""]
        self.add_coins(defn.price // 2)
        return True

    def usar(self, item_id: str) -> float:
        defn = _ITEM_DEFS.get(item_id)
        if defn is None or not defn.consumible:
            return 0.0
        if self._items.get(item_id, 0) <= 0:
            return 0.0
        self._items[item_id] -= 1
        if self._items[item_id] <= 0:
            del self._items[item_id]
        self.save()
        return defn.heal_hp

    def equip(self, item_id: str) -> bool:
        defn = _ITEM_DEFS.get(item_id)
        if defn is None or defn.slot is None or defn.slot == "skill":
            return False
        if self._items.get(item_id, 0) <= 0:
            return False
        self._equipped[defn.slot] = item_id
        self.save()
        return True

    def unequip(self, slot: str) -> bool:
        if slot not in self._equipped:
            return False
        del self._equipped[slot]
        self.save()
        return True

    def get_equipped(self) -> dict[str, str]:
        return dict(self._equipped)

    def has_skill(self, skill_id: str) -> bool:
        return self._items.get(skill_id, 0) > 0

    # ── prestigio (AUD-609) ───────────────────────────────────────
    def get_xp_multiplier(self) -> float:
        """Multiplicador de XP por punto de prestigio: +5 % cada uno.

        Lo consume `ExperienceSystem.grant`, así que el beneficio es real
        desde el primer punto y no depende de ninguna pantalla.
        """
        return 1.0 + 0.05 * self.prestigio

    def reencarnar(self, experiencia, arbol) -> bool:
        """Reinicia la partida progresiva a cambio de un punto de prestigio.

        AUD-609 — el *prestigio* de toda la vida en RPGs: se tira la
        experiencia (y con ella los rangos del árbol, que se pagaron con
        sus puntos) y se gana +5 % de XP para siempre. Requiere
        `NIVEL_DE_REENCARNACION`; todo o nada, como los gastos del motor.

        Los objetos y las monedas NO se tocan: lo que la reencarnación
        reinicia es el progreso **de habilidad**, no la economía. La ropa
        comprada sigue puesta; perderla convertiría el prestigio en un castigo.

        Pendiente su pantalla (`GAP-073`): hoy sólo las pruebas y una futura
        escena de menú la llaman — el mismo orden en que llegó la tienda:
        primero el motor, después el sitio donde pulsarla.
        """
        from src.engine.core.skill_tree import ArbolDeHabilidades

        if experiencia is None or arbol is None:
            return False
        if experiencia.nivel < self.NIVEL_DE_REENCARNACION:
            return False
        self.prestigio += 1
        experiencia.reset()
        if isinstance(arbol, ArbolDeHabilidades):
            arbol.reset()
        self.save()
        return True

    def all_items(self) -> dict[str, int]:
        return dict(self._items)

    def restaurar(self, items: dict[str, int],
                  equipado: dict[str, str] | None = None) -> None:
        self._items = {
            str(k): max(0, int(v))
            for k, v in dict(items or {}).items()
            if k in _ITEM_DEFS and int(v) > 0
        }
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
        _migrar_inventario()
        data = {
            "items": dict(self._items),
            "equipped": dict(self._equipped),
            # AUD-609 — el prestigio viaja con el inventario: es estado de
            # partida y sobrevive al reseteo de la experiencia.
            "prestigio": int(self.prestigio),
        }
        _INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        _INVENTORY_PATH.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))

    def load(self) -> None:
        _migrar_inventario()
        try:
            raw = _INVENTORY_PATH.read_bytes()
            data = orjson.loads(raw)
            self._items = {k: v for k, v in data.get("items", {}).items() if k in _ITEM_DEFS}
            # AUD-609 — un fichero viejo sin la clave deja 0; uno editado a
            # mano con basura también, que es mejor que un multiplicador
            # roto. No se aceptan negativos: el prestigio sólo se gana.
            try:
                self.prestigio = max(0, int(data.get("prestigio", 0)))
            except (TypeError, ValueError):
                self.prestigio = 0
            self._equipped = {
                slot: item_id
                for slot, item_id in data.get("equipped", {}).items()
                if (defn := _ITEM_DEFS.get(item_id)) is not None
                and defn.slot == slot
                and defn.slot != "skill"
                and self._items.get(item_id, 0) > 0
            }
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

    @classmethod
    def _reset_instance(cls) -> None:
        cls._instance = None


def get_inventory() -> Inventory:
    return Inventory()
