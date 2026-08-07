from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import orjson

from src.engine.core import settings
from src.engine.core.save_data import MAX_SLOTS, SaveData
from src.engine.core.user_settings import user_data_dir

logger = logging.getLogger(__name__)

#: Dónde vivían las partidas antes de AUD-157: dentro del proyecto.
_SAVES_HEREDADO = settings.PROJECT_ROOT / "saves"


def escribir_atomicamente(path: Path, datos: bytes) -> None:
    """Escribe `datos` en `path` sin poder dejar el fichero a medias (AUD-316).

    La misma receta que `save()` de abajo —fichero temporal en el mismo
    directorio, `fsync` y `os.replace`— exportada para los demás datos del
    jugador. `write_bytes` pisa el fichero en su sitio, y un corte a mitad de
    la escritura (disco lleno, apagón) dejaba roto lo que había; con el
    temporal, el fichero bueno sigue entero hasta que el nuevo está listo.

    Lanza `OSError` si algo falla —con el temporal limpiado—; cada llamador
    decide si eso se avisa o se traga.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        try:
            f = os.fdopen(fd, "wb")
        except Exception:
            os.close(fd)
            os.unlink(tmp)
            raise
        with f:
            f.write(datos)
            # Flush to the OS *and* to the platter before the rename:
            # without the fsync, a power loss can leave the new entry pointing
            # at unwritten (zero-filled) blocks.
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(path))
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def volcar_estado_en(data: SaveData) -> None:
    """Copia inventario y puntuación **actuales** dentro de la partida — AUD-292.

    Se lee del estado vivo y no de los ficheros globales: en el instante de
    guardar, lo que el jugador tiene es lo que hay en memoria, y los ficheros
    pueden llevar un segundo de retraso.

    No lanza. Guardar es lo último que hace un escenario al llegar a un
    checkpoint, y quedarse sin guardar la posición por no poder leer el
    inventario sería cambiar un dato importante por uno accesorio.
    """
    try:
        from src.engine.core.experience import ExperienceSystem
        from src.engine.core.inventory import get_inventory
        from src.engine.core.score_system import ScoreSystem

        inventario = get_inventory()
        data.inventory_items = dict(inventario.all_items())
        data.inventory_equipped = dict(inventario.get_equipped())
        data.score = int(ScoreSystem.get_instance().score)
        data.exp_estado = dict(ExperienceSystem.get_instance().to_dict())
        from src.engine.core.skill_tree import ArbolDeHabilidades

        data.arbol = dict(ArbolDeHabilidades.get_instance().to_dict())
    except Exception:  # pragma: no cover - nunca a costa de la posición
        logger.warning("no se pudo volcar inventario/puntuación en la partida",
                       exc_info=True)


def aplicar_estado_de(data: SaveData) -> None:
    """Lo contrario: deja el juego como lo dejó esa partida — AUD-292.

    Se llama al **cargar** un slot, y es la mitad que faltaba: sin esto, elegir
    la partida 2 dejaba el dinero y la ropa de la partida 1, porque el
    inventario nunca supo de slots.

    Una partida de la versión 2 llega con los tres campos vacíos. Ahí no se
    toca nada: vaciar la cartera de quien cargó una partida antigua sería
    cobrarle la migración.
    """
    try:
        from src.engine.core.experience import ExperienceSystem
        from src.engine.core.inventory import get_inventory
        from src.engine.core.score_system import ScoreSystem

        if data.inventory_items or data.inventory_equipped:
            get_inventory().restaurar(data.inventory_items, data.inventory_equipped)
        if data.version >= 3:
            ScoreSystem.get_instance().set_score(int(data.score))
        from src.engine.core.skill_tree import ArbolDeHabilidades

        ArbolDeHabilidades.get_instance().from_dict(data.arbol)
        if data.exp_estado:
            ExperienceSystem.get_instance().from_dict(data.exp_estado)
        elif data.exp_total:
            # Partida de la versión 2: sólo hay el total. Se restaura lo que
            # hay y se acepta el efecto conocido —los puntos gastados vuelven—
            # porque la alternativa es empezar de cero, que es peor.
            ExperienceSystem.get_instance().from_dict({"exp": int(data.exp_total)})
    except Exception:  # pragma: no cover
        logger.warning("no se pudo aplicar el inventario de la partida",
                       exc_info=True)


class SaveManager:
    """Las partidas guardadas, en el directorio del usuario.

    AUD-157 — la contradicción que quedó a medias
    ==============================================
    `user_data_dir()` existe desde AUD-032 y su docstring explica por qué:
    *«una versión empaquetada puede estar instalada en un sitio de sólo
    lectura (Program Files, /Applications), y escribir el estado del jugador
    dentro del árbol de instalación es lo que metió `saves/slot_1.json` en el
    control de versiones»*.

    Ese arreglo se aplicó a las preferencias y a los logros, y **no a las
    partidas**, que son el estado más importante de todos: `SAVES_DIR` seguía
    siendo `PROJECT_ROOT / "saves"`. En el ejecutable de PyInstaller (F3.3)
    instalado en Program Files, guardar la partida falla. El proyecto ya había
    escrito por qué eso está mal y siguió haciéndolo.

    Las partidas que estén en el sitio viejo se copian una vez al nuevo. No se
    borran: si alguien vuelve a una versión anterior, siguen ahí.
    """

    #: Se mantiene como atributo de clase porque hay pruebas y herramientas que
    #: lo redirigen a un directorio temporal. Cambiarlo a propiedad rompería
    #: `SaveManager.SAVES_DIR = tmp` sin avisar.
    SAVES_DIR = user_data_dir() / "saves"

    def __init__(self) -> None:
        self.SAVES_DIR.mkdir(parents=True, exist_ok=True)
        self._migrar_partidas_antiguas()

    def _migrar_partidas_antiguas(self) -> None:
        """Copia las partidas del sitio viejo si el nuevo no las tiene."""
        if self.SAVES_DIR == _SAVES_HEREDADO or not _SAVES_HEREDADO.is_dir():
            return
        for origen in _SAVES_HEREDADO.glob("slot_*.json"):
            destino = self.SAVES_DIR / origen.name
            if destino.exists():
                continue
            try:
                destino.write_bytes(origen.read_bytes())
                logger.info(
                    "SaveManager: partida migrada %s -> %s", origen, destino)
            except OSError as exc:
                # Que no se pueda migrar no puede impedir jugar: se arranca
                # con una partida nueva y queda dicho por qué.
                logger.warning(
                    "SaveManager: no se pudo migrar %s (%s)", origen, exc)

    def _slot_path(self, slot: int) -> Path:
        return self.SAVES_DIR / f"slot_{slot}.json"

    def save(self, slot: int, data: SaveData) -> str:
        if slot < 1 or slot > MAX_SLOTS:
            raise ValueError(f"Slot must be 1-{MAX_SLOTS}, got {slot}")
        data.slot_id = slot
        path = self._slot_path(slot)
        fd, tmp = tempfile.mkstemp(dir=str(self.SAVES_DIR), suffix=".tmp")
        try:
            try:
                f = os.fdopen(fd, "wb")
            except Exception:
                os.close(fd)
                os.unlink(tmp)
                raise
            with f:
                f.write(data.to_json())
                # Flush to the OS *and* to the platter before the rename.
                # os.replace is atomic w.r.t. the directory entry, but without
                # the fsync a power loss can leave the new entry pointing at
                # unwritten (zero-filled) blocks — i.e. the atomic rename
                # atomically installs a corrupt save over a good one.
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, str(path))
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        logger.info("SaveManager: saved slot %d -> %s", slot, path)
        return str(path)

    def load(self, slot: int) -> SaveData | None:
        if slot < 1 or slot > MAX_SLOTS:
            return None
        path = self._slot_path(slot)
        if not path.exists():
            return None
        try:
            raw = path.read_bytes()
            return SaveData.from_json(raw)
        except (orjson.JSONEncodeError, OSError, KeyError, ValueError) as e:
            logger.warning("SaveManager: corrupt save slot %d: %s", slot, e)
            return None

    def delete(self, slot: int) -> None:
        if slot < 1 or slot > MAX_SLOTS:
            return
        path = self._slot_path(slot)
        if path.exists():
            path.unlink()
            logger.info("SaveManager: deleted slot %d", slot)

    def list_slots(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for slot in range(1, MAX_SLOTS + 1):
            data = self.load(slot)
            if data is not None:
                result.append({
                    "slot": slot,
                    "stage_id": data.stage_id,
                    "timestamp": data.timestamp,
                    "health": data.health,
                    "max_health": data.max_health,
                })
        return result

    def has_saves(self) -> bool:
        for slot in range(1, MAX_SLOTS + 1):
            if self._slot_path(slot).exists():
                return True
        return False

    def newest_slot(self) -> int | None:
        best = None
        best_time = ""
        for slot in range(1, MAX_SLOTS + 1):
            data = self.load(slot)
            if data is not None and data.timestamp > best_time:
                best_time = data.timestamp
                best = slot
        return best

    def auto_save(self, stage_id: str, stage_index: int,
                  checkpoint_x: float, checkpoint_y: float,
                  health: float, max_health: float,
                  zone_flags: dict[str, bool] | None = None,
                  exp_total: int | None = None) -> str | None:
        """Update the progress fields of the newest save, preserving the rest.

        AUD-005: this used to construct a brand-new ``SaveData`` from only the
        six arguments below and write it over the newest slot. Every field the
        arguments did not cover — ``completed_stages``, ``zone_flags`` — was
        silently reset to its default. Because ``SceneManager._on_stage_complete``
        appends to ``completed_stages``, saves, and *then* calls ``auto_save``
        on the same slot, the freshly recorded stage completion was erased
        microseconds after it was written. Players could never accumulate
        completed stages.

        The fix is read-modify-write: load whatever is already in the slot and
        mutate only the fields autosave actually owns.
        """
        slot = self.newest_slot()
        if slot is None:
            slot = 1

        data = self.load(slot)
        if data is None:
            data = SaveData(slot_id=slot)

        data.slot_id = slot
        # Timezone-aware and lexicographically sortable, so newest_slot()'s
        # string comparison stays correct across DST changes (AUD-014).
        data.timestamp = datetime.now(timezone.utc).isoformat()
        data.stage_id = stage_id
        data.stage_index = stage_index
        data.checkpoint_x = checkpoint_x
        data.checkpoint_y = checkpoint_y
        data.health = health
        data.max_health = max_health
        # AUD-251: las banderas se **funden**, no se sustituyen. El autoguardado
        # sólo sabe de las de la partida en curso; borrar las que trae el hueco
        # sería repetir el defecto que documenta el párrafo de arriba, esta vez
        # con lo que abrió el jugador hace tres salas.
        if zone_flags:
            data.zone_flags.update(zone_flags)
        # AUD-267: la experiencia sólo sube, así que se queda la mayor. Un
        # autoguardado disparado por una escena que aún no leyó el sistema no
        # puede hacer retroceder el nivel del jugador.
        if exp_total is not None:
            data.exp_total = max(data.exp_total, int(exp_total))
        # AUD-292 — y la cartera, la ropa y la puntuación, que hasta hoy vivían
        # en ficheros globales fuera de la partida.
        volcar_estado_en(data)
        return self.save(slot, data)
