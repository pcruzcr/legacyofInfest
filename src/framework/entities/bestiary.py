"""
Module: bestiary
System: framework.entities
Academic Unit: N/A
Description: Bestiary/Codex system — tracks enemy encounters, kills, and lore.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import orjson

from src.engine.core import settings
from src.engine.core.user_settings import user_data_dir

logger = logging.getLogger(__name__)

# AUD-157 — el estado del jugador va al directorio del usuario.
#
# `PROJECT_ROOT` es el árbol de instalación, y una versión empaquetada puede
# estar en un sitio de sólo lectura. Es la misma corrección que AUD-032 aplicó
# a las preferencias y a los logros y que aquí se quedó sin aplicar.
_DEFAULT_BESTIARY_PATH: Path = user_data_dir() / "saves" / "bestiary.json"

#: Los textos de las fichas clásicas viven en `data/bestiary.json` (AUD-199):
#: editar un nombre o un lore ya no exige tocar el motor, y
#: `scripts/check_bestiary.py` valida el fichero.
_DATOS_BESTIARIO: Path = settings.PROJECT_ROOT / "data" / "bestiary.json"


class BestiaryEntry:
    """A single bestiary entry for an enemy type."""

    def __init__(self, enemy_id: str, name: str, description: str,
                 lore: str = "", drops: list[str] | None = None,
                 hp: int = 1, damage: float = 1.0) -> None:
        self.enemy_id: str = enemy_id
        self.name: str = name
        self.description: str = description
        self.lore: str = lore
        self.drops: list[str] = drops or []
        self.hp: int = hp
        self.damage: float = damage
        self.encountered: bool = False
        self.kills: int = 0
        self.times_hit_by_player: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "enemy_id": self.enemy_id,
            "encountered": self.encountered,
            "kills": self.kills,
            "times_hit_by_player": self.times_hit_by_player,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], base: BestiaryEntry) -> BestiaryEntry:
        base.encountered = data.get("encountered", False)
        base.kills = data.get("kills", 0)
        base.times_hit_by_player = data.get("times_hit_by_player", 0)
        return base


class Bestiary:
    """Tracks all enemy types encountered and killed."""

    _instance: Bestiary | None = None

    def __init__(self) -> None:
        self._entries: dict[str, BestiaryEntry] = {}
        self._init_defaults()

    #: Cómo se convierte el nombre de una clase en un identificador de
    #: bestiario. Es la regla que ya seguían las nueve entradas escritas a
    #: mano: `EnemyWalker` → `walker`, `BossVenado` → `boss_venado`.
    @staticmethod
    def id_de(enemigo: object) -> str:
        """El identificador de bestiario de un enemigo.

        AUD-154 — antes esto no existía y `StageScene` hacía::

            if hasattr(enemy, "enemy_id"):
                self._bestiary.record_kill(enemy.enemy_id)

        Ninguna clase de enemigo definía `enemy_id`, así que la condición era
        **siempre falsa** y el bestiario no registró nunca nada. La pantalla del
        bestiario filtra por `encountered`, de modo que salía vacía siempre y
        parecía que faltaba contenido en vez de que faltaba el cableado.
        """
        declarado = getattr(enemigo, "enemy_id", "")
        if declarado:
            return str(declarado)
        nombre = type(enemigo).__name__
        if nombre.startswith("Enemy"):
            return nombre[len("Enemy"):].lower()
        # `BossVenado` → `boss_venado`; cualquier otra cosa, tal cual en
        # minúsculas con guiones bajos.
        salida = []
        for i, ch in enumerate(nombre):
            if ch.isupper() and i:
                salida.append("_")
            salida.append(ch.lower())
        return "".join(salida)

    def _asegurar(self, enemy_id: str) -> BestiaryEntry:
        """La entrada de ese id, creándola si es la primera vez que se ve.

        Antes los tres `record_*` hacían `if entry:` y salían callados cuando el
        id no estaba en la tabla. Como la tabla tenía nueve entradas fijas y el
        registro de especies tiene veintiuna, matar un `WalkerInsect` no se
        anotaba en ninguna parte y no había forma de enterarse. Un bestiario
        que descarta lo que no conoce es un bestiario que nunca crece.
        """
        entrada = self._entries.get(enemy_id)
        if entrada is None:
            from src.framework.entities import bestiary_registry

            spec = bestiary_registry.get(enemy_id)
            entrada = BestiaryEntry(
                enemy_id,
                spec.display_name if spec is not None else enemy_id,
                spec.display_name if spec is not None else "Sin descripción.",
                hp=int(float((spec.params if spec else {}).get("max_health", 1))),
                damage=float((spec.params if spec else {}).get(
                    "damage_on_contact", 1.0)),
            )
            self._entries[enemy_id] = entrada
        return entrada

    def _init_defaults(self) -> None:
        """Las fichas clásicas se leen de `data/bestiary.json`.

        AUD-199 — los textos (nombre, descripción, lore) estaban escritos a
        mano en el código y mezclados con la lógica. Un nombre mal escrito se
        arreglaba tocando el motor; ahora se arregla en el fichero de datos, y
        el validador lo vacuna antes de que llegue a la pantalla.
        """
        try:
            datos: Any = orjson.loads(_DATOS_BESTIARIO.read_bytes())
        except FileNotFoundError:
            logger.warning(
                "bestiary: no existe %s; sólo quedan las especies del registro",
                _DATOS_BESTIARIO,
            )
            datos = None
        except (ValueError, TypeError):
            logger.warning(
                "bestiary: %s ilegible; sólo quedan las especies del registro",
                _DATOS_BESTIARIO, exc_info=True,
            )
            datos = None

        if isinstance(datos, dict):
            for e in datos.get("species", []):
                if not isinstance(e, dict):
                    continue
                eid = e.get("id")
                if not eid or eid in self._entries:
                    continue
                try:
                    self._entries[eid] = BestiaryEntry(
                        eid,
                        e.get("name", eid),
                        e.get("description", ""),
                        lore=e.get("lore", ""),
                        drops=e.get("drops"),
                        hp=int(e.get("hp", 1)),
                        damage=float(e.get("damage", 1.0)),
                    )
                except (TypeError, ValueError):
                    logger.warning(
                        "bestiary: entrada «%s» de %s con estadísticas raras; "
                        "se omite", eid, _DATOS_BESTIARIO,
                    )

        # Y las especies con nombre del registro (`WalkerInsect`,
        # `ShooterQuetzal`…). Estaban en el motor, se podían colocar en Tiled y
        # el bestiario no las conocía: matar una no se anotaba en ningún sitio.
        from src.framework.entities import bestiary_registry

        for spec in bestiary_registry.SPECIES.values():
            if spec.species_id in self._entries:
                continue
            self._entries[spec.species_id] = BestiaryEntry(
                spec.species_id,
                spec.display_name,
                f"Especie de zona {spec.zone}.",
                hp=int(float(spec.params.get("max_health", 1))),
                damage=float(spec.params.get("damage_on_contact", 1.0)),
            )

    @classmethod
    def get_instance(cls) -> Bestiary:
        if cls._instance is None:
            cls._instance = Bestiary()
        return cls._instance

    def get_entry(self, enemy_id: str) -> BestiaryEntry | None:
        return self._entries.get(enemy_id)

    def get_all_entries(self) -> list[BestiaryEntry]:
        return list(self._entries.values())

    def record_encounter(self, enemy_id: str) -> None:
        if enemy_id:
            self._asegurar(enemy_id).encountered = True

    def record_kill(self, enemy_id: str) -> None:
        if not enemy_id:
            return
        entry = self._asegurar(enemy_id)
        entry.encountered = True
        entry.kills += 1

    def record_hit(self, enemy_id: str) -> None:
        if not enemy_id:
            return
        entry = self._asegurar(enemy_id)
        entry.encountered = True
        entry.times_hit_by_player += 1

    def save(self, path: str | Path | None = None) -> None:
        data = {eid: entry.to_dict() for eid, entry in self._entries.items()}
        path = Path(path) if path is not None else _DEFAULT_BESTIARY_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))

    def load(self, path: str | Path | None = None) -> None:
        """Lee el bestiario del disco. Un fichero ilegible no tumba el juego.

        AUD-100 — la corrupción se tragaba en silencio
        ----------------------------------------------
        El `except` era ``(FileNotFoundError, orjson.JSONEncodeError,
        ValueError)`` seguido de un ``pass``. Dos cosas mal:

        1. `orjson.JSONEncodeError` **es `TypeError`**, y codificar no puede
           fallar dentro de un `loads`. Sobraba. Lo que de verdad atrapaba un
           fichero corrupto era `ValueError`, del que `orjson.JSONDecodeError`
           hereda: el bloque funcionaba, pero por una razón distinta de la que
           aparentaba, y eso invita a «simplificarlo» quitando lo que hace
           falta.
        2. El `pass`. Las bajas acumuladas de un semestre desaparecían sin una
           línea en el registro, y el estudiante veía un bestiario vacío sin
           ninguna pista. `ProgresoAcademico.cargar` ya avisaba ante lo mismo;
           tres sitios del proyecto hacían lo contrario.
        """
        destino = Path(path) if path is not None else _DEFAULT_BESTIARY_PATH
        try:
            data = orjson.loads(destino.read_bytes())
            for eid, entry_data in data.items():
                base = self._entries.get(eid)
                if base:
                    BestiaryEntry.from_dict(entry_data, base)
        except FileNotFoundError:
            logger.debug("bestiary: sin fichero previo en %s; se empieza de cero", destino)
        except (ValueError, TypeError):
            # Se nombra `destino` y no la ruta por defecto: quien pasa una
            # ruta necesita saber cuál falló, no cuál se habría usado.
            logger.warning(
                "bestiary: %s ilegible; se empieza de cero y se sobrescribirá "
                "al primer guardado", destino, exc_info=True,
            )