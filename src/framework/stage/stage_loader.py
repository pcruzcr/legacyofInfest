"""
Module: stage_loader
System: framework.stage
Academic Unit: Unit II (Collision Detection), Unit IV (Game Architecture)
Description: Parses TMX map files using pytmx and pyscroll to assemble
a complete stage environment: tile layers, entity spawn points, collision
zones, checkpoints, and the next-trigger portal.
"""
from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame
import pyscroll
import pyscroll.data
from pytmx.util_pygame import load_pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework import FrameworkUsageError
from src.framework.entities.base_entity import BaseEntity
from src.framework.stage.interactables import (
    Cerradura,
    Cofre,
    Disparador,
    Recogible,
)
from src.framework.stage.tmx_diagnostics import (
    TmxObjectProblem,
    TmxReport,
    known_object_types,
    suggest_types,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.framework.stage.checkpoint import Checkpoint


@dataclass
class MessageTrigger:
    rect: pygame.Rect
    text: str
    triggered: bool = False


@dataclass
class HazardZone:
    rect: pygame.Rect
    damage: float = 0.25
    cooldown: float = 0.5
    timer: float = 0.5


@dataclass
class DeathPit:
    rect: pygame.Rect


@dataclass
class CameraLock:
    rect: pygame.Rect
    lock_x: bool = False
    lock_y: bool = False


@dataclass
class LightSpec:
    """Un foco declarado en el TMX, en coordenadas del mapa.

    F1.1 — por qué esto es un dato y no un objeto de VFX
    ----------------------------------------------------
    El cargador no debe construir `LightSource`: eso ataría el módulo de
    escenarios al de efectos y obligaría a importar pygame-surface machinery
    para leer un mapa. Aquí sólo se describe *qué* pidió el diseñador; la
    escena decide cómo materializarlo.

    Antes de esto, las luces estaban **escritas a mano en el motor**, en una
    cadena `if zone == 0: ... elif zone == 1: ...` con coordenadas fijas. Un
    estudiante que construyera un escenario en Tiled no podía colocar ni una
    sola luz: heredaba las dos del zone 0, en (80, 80) y (240, 80), estuviera
    ahí su nivel o no.
    """

    position: tuple[float, float]
    radius: float = 80.0
    color: tuple[int, int, int] = (255, 220, 180)
    intensity: float = 0.8
    flicker: bool = False
    flicker_speed: float = 4.0
    flicker_amount: float = 0.15


@dataclass
class StageData:
    map_layer: pyscroll.PyscrollGroup
    map_pixel_size: tuple[int, int] = (0, 0)
    collision_rects: list[pygame.Rect] = field(default_factory=list)
    one_way_rects: list[pygame.Rect] = field(default_factory=list)
    entity_list: list[BaseEntity] = field(default_factory=list)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    spawn_point: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    next_trigger: pygame.Rect | None = None
    background_layers: list[pygame.Surface] = field(default_factory=list)
    message_triggers: list[MessageTrigger] = field(default_factory=list)
    hazard_zones: list[HazardZone] = field(default_factory=list)
    death_pits: list[DeathPit] = field(default_factory=list)
    camera_locks: list[CameraLock] = field(default_factory=list)
    lights: list[LightSpec] = field(default_factory=list)
    #: F4.1 — objetos con los que el jugador interactúa.
    recogibles: list[Recogible] = field(default_factory=list)
    cerraduras: list[Cerradura] = field(default_factory=list)
    cofres: list[Cofre] = field(default_factory=list)
    disparadores: list[Disparador] = field(default_factory=list)
    zone: int = 0
    stage_id: str = ""
    stage_name: str = ""
    time_limit: int = 0
    bgm_track: str = ""
    gravity_multiplier: float = 1.0
    climate: str = ""
    #: Brillo ambiente del escenario, de 0 (oscuridad total) a 1 (sin
    #: oscurecer). `None` significa "no declarado": la escena caerá a su tabla
    #: por zona. Se distingue de 1.0 a propósito, porque 1.0 es una decisión
    #: explícita de diseño —"este nivel es a plena luz"— y `None` es la
    #: ausencia de decisión.
    ambient_light: float | None = None
    #: Bloom permanente del escenario, 0 a 1. `None` = no declarado.
    bloom: float | None = None
    #: Viñeta del escenario, 0 a 0,6. `None` = no declarado.
    vignette: float | None = None
    #: Partículas de ambiente: tipo y partículas por segundo. Cadena vacía =
    #: no declarado; la escena caerá a su tabla por zona.
    ambient_fx: str = ""
    ambient_fx_rate: float | None = None
    #: Hora inicial del escenario, 0 a 24. `None` = no declarada (mediodía).
    start_hour: float | None = None
    #: Segundos reales que dura un ciclo completo. 0 congela el reloj, que es
    #: el comportamiento de un escenario sin ciclo día/noche.
    day_length: float = 0.0
    #: Estación del escenario. Cadena vacía = no declarada; la escena usará la
    #: de por defecto. Las estaciones no avanzan solas: un escenario dura
    #: minutos y cambiar de invierno a primavera a mitad sería ruido.
    season: str = ""


REQUIRED_LAYERS: tuple[str, ...] = (
    "BG_Far", "BG_Mid", "BG_Near", "Terrain",
    "Terrain_Detail", "Objects", "Collision", "FG_Overlay",
)


_NUMERIC_PROPS: tuple[str, ...] = (
    "max_health", "damage_on_contact", "patrol_length",
    "fire_rate", "projectile_speed", "projectile_damage",
    "sine_amplitude", "sine_frequency", "flight_speed",
    "patrol_speed", "alert_speed", "contact_knockback",
    "detection_range_x", "detection_range_y", "charge_speed",
)


class StageLoader:
    _entity_registry: dict[str, type[BaseEntity]] = {}
    #: Escenarios cuyo paquete ya se intentó importar (AUD-106).
    _escenarios_ya_importados: set[str] = set()
    # (resolved path, mtime_ns, size) -> parsed pytmx map. See _parse_tmx.
    _tmx_cache: dict[tuple[str, int, int], Any] = {}

    @classmethod
    def _registrar_tipos_del_escenario(cls, tmx_path: Path) -> bool:
        """Importa el paquete del escenario para que registre sus entidades.

        Devuelve `True` si importó algo nuevo. Convención:
        ``assets/maps/<nombre>/<nombre>.tmx`` ↔ ``src/stages/<nombre>/``.

        Se importa el paquete entero porque el framework no dice desde qué
        fichero hay que registrar: sobre las entregas reales, unos lo hacen en
        el módulo principal, otros en un módulo de entidades aparte, y otros
        dentro de la escena. Sólo se hace **una vez por escenario** y sólo
        cuando ya ha habido un tipo desconocido, así que no cuesta nada en el
        camino normal.
        """
        import importlib
        import pkgutil

        nombre = tmx_path.parent.name
        if nombre in cls._escenarios_ya_importados:
            return False
        cls._escenarios_ya_importados.add(nombre)

        antes = len(cls._entity_registry)
        raiz = f"src.stages.{nombre}"
        try:
            paquete = importlib.import_module(raiz)
        except ImportError:
            return False
        except Exception:
            logger.warning("stage_loader: '%s' no se pudo importar", raiz, exc_info=True)
            return False

        for info in pkgutil.walk_packages(getattr(paquete, "__path__", []), f"{raiz}."):
            if any(p in info.name for p in (".tools", ".tests", ".herramientas")):
                continue
            try:
                importlib.import_module(info.name)
            except Exception:
                logger.debug("stage_loader: '%s' no se pudo importar", info.name, exc_info=True)

        return len(cls._entity_registry) > antes

    @classmethod
    def register_entity(cls, type_name: str, entity_class: type[BaseEntity]) -> None:
        cls._entity_registry[type_name] = entity_class

    @classmethod
    def _parse_tmx(cls, tmx_path: Path) -> Any:
        """Parse a TMX file, reusing a previous parse when the file is unchanged.

        AUD-027: ``StageScene.respawn()`` calls ``on_enter()``, which called
        ``load()``, which re-parsed the entire TMX and re-decoded every tileset
        image on **every player death** — a guaranteed hitch at the worst
        possible moment for game feel.

        ``tmx_data`` is read-only map geometry; entities are constructed fresh
        from it on each load, so the parse result is safe to share. The cache is
        keyed on the file's modification time and size, so editing a map in
        Tiled and re-running still picks up the change — important, since this
        engine is used by students iterating on level design.
        """
        resolved = tmx_path.resolve()
        try:
            stat = resolved.stat()
            key = (str(resolved), stat.st_mtime_ns, stat.st_size)
        except OSError:
            key = (str(resolved), 0, 0)

        cached = cls._tmx_cache.get(key)
        if cached is not None:
            return cached

        tmx_data = load_pygame(str(resolved))
        # Only ever keep one parse in flight; stages are large and holding
        # several maps' tilesets resident is not worth the memory.
        cls._tmx_cache.clear()
        cls._tmx_cache[key] = tmx_data
        return tmx_data

    @classmethod
    def clear_tmx_cache(cls) -> None:
        """Drop the parsed-TMX cache (test teardown, or on low memory)."""
        cls._tmx_cache.clear()

    @classmethod
    def _ensure_entities_registered(cls) -> None:
        """Registra el bestiario si nadie lo ha hecho todavía (AUD-056).

        Hasta ahora el único sitio que llamaba a `ensure_registered()` era
        `App.__init__`, así que `StageLoader.load()` sólo reconocía las
        entidades si alguien había construido la aplicación antes. Cargar un
        mapa desde un script, una prueba o una herramienta producía un escenario
        al que **le faltaban enemigos, sin decirlo**: `tests/test_stage0_smoke.py`
        cargaba stage0 con 5 de sus enemigos descartados en silencio
        —Charger, Archer, Brute, Caster y Assassin— y a continuación afirmaba
        que el escenario tenía enemigos. Pasaba, porque Walker y Flying sí
        sobrevivían.

        Una dependencia de orden que no se puede ver desde el sitio donde se
        incumple es una trampa, y en un framework que usan estudiantes es una
        trampa que van a pisar. La importación es local porque `entity_factory`
        importa este módulo; la llamada es idempotente y cuesta un `if`.
        """
        from src.framework.entities.entity_factory import ensure_registered

        ensure_registered()

    @classmethod
    def load(cls, tmx_path: Path) -> StageData:
        tmx_path = Path(tmx_path)
        if not tmx_path.exists():
            raise FrameworkUsageError(f"TMX file not found: {tmx_path}")

        cls._ensure_entities_registered()

        tmx_data = cls._parse_tmx(tmx_path)
        cls._validate_layers(tmx_data)
        stage = cls._build_stage_data(tmx_data)

        cls._load_backgrounds(stage, tmx_data.properties.get("background_zone", ""))
        waypoints_by_owner = cls._build_waypoints(tmx_data)
        report = TmxReport(tmx_path=str(tmx_path))
        spawn_found = cls._process_objects(tmx_data, stage, waypoints_by_owner, report)

        # AUD-055: los objetos no interpretables se informan **antes** que la
        # falta de PlayerSpawn, porque lo más habitual es que sean la causa: un
        # «PlayerSpwan» mal escrito produce las dos cosas a la vez, y decir
        # «falta el PlayerSpawn» cuando está ahí, mal escrito, manda a buscar
        # en la dirección contraria.
        if not report.ok:
            # AUD-106: antes de rendirse, dar al escenario la oportunidad de
            # registrar sus propios tipos.
            #
            # El curso pide que quien inventa un enemigo o un jefe lo registre
            # desde su paquete. Al jugar funciona, porque la escena importa su
            # módulo antes de cargar el mapa. Pero cargar el TMX **suelto** —el
            # validador, el previsualizador, el calificador, esta suite— fallaba
            # con «type='BossPaburu' no existe», y entonces la herramienta del
            # profesor contradecía al juego.
            #
            # Importar el paquete aquí hace que las cuatro rutas coincidan, que
            # es lo único que hace fiable a un validador.
            if cls._registrar_tipos_del_escenario(tmx_path):
                # Se rehace la pasada desde cero: la primera dejó a medias las
                # listas del escenario, y duplicar entidades sería peor que el
                # fallo que se está intentando arreglar.
                report = TmxReport(tmx_path=str(tmx_path))
                stage.entity_list.clear()
                stage.checkpoints.clear()
                stage.message_triggers.clear()
                stage.hazard_zones.clear()
                stage.death_pits.clear()
                stage.camera_locks.clear()
                stage.lights.clear()
                stage.recogibles.clear()
                stage.cerraduras.clear()
                stage.cofres.clear()
                stage.disparadores.clear()
                stage.next_trigger = None
                waypoints_by_owner.clear()
                spawn_found = cls._process_objects(
                    tmx_data, stage, waypoints_by_owner, report,
                )

        if not report.ok:
            raise FrameworkUsageError(
                report.format(known_object_types(list(cls._entity_registry))),
            )

        if not spawn_found:
            raise FrameworkUsageError(
                f"No hay ningún objeto de tipo «PlayerSpawn» en {tmx_path}.\n"
                f"Añade un objeto de tipo punto en la capa «Objects» con "
                f"type=PlayerSpawn: es donde aparece el jugador al empezar y "
                f"al reaparecer.",
            )

        cls._load_collision(tmx_data, stage)
        return stage

    # ── Internal helpers ──────────────────────────────────────────

    @classmethod
    def _validate_layers(cls, tmx_data: Any) -> None:
        tmx_layer_names = {layer.name for layer in tmx_data.visible_layers}
        tmx_layer_names.update({layer.name for layer in tmx_data.layers})
        for name in REQUIRED_LAYERS:
            if name not in tmx_layer_names:
                raise FrameworkUsageError(f"Missing required layer: {name}")

    @classmethod
    def _build_stage_data(cls, tmx_data: Any) -> StageData:
        props = tmx_data.properties
        stage_id = props.get("stage_id", "")
        stage_name = props.get("stage_name", "")
        time_limit = cls._safe_int(props.get("time_limit", 0), "time_limit")
        bgm_track = props.get("bgm_track", "")
        gravity_multiplier = cls._safe_float(props.get("gravity_multiplier", 1.0), "gravity_multiplier")
        climate = props.get("climate", "")
        zone = cls._safe_int(props.get("zone", 0), "zone")
        ambient_light = cls._parse_ambient_light(props)
        bloom = cls._parse_unit_prop(props, "bloom", 0.0, 1.0)
        vignette = cls._parse_unit_prop(props, "vignette", 0.0, 0.6)
        ambient_fx = cls._parse_ambient_fx(props)
        ambient_fx_rate = cls._parse_unit_prop(props, "ambient_fx_rate", 0.0, 120.0)
        start_hour, day_length = cls._parse_day_night(props)
        season = cls._parse_season(props)

        map_data = pyscroll.data.TiledMapData(tmx_data)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            renderer = pyscroll.BufferedRenderer(
                map_data,
                (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
                clamp_camera=True,
                alpha=True,
            )
        group = pyscroll.PyscrollGroup(map_layer=renderer, default_layer=4)

        map_w = tmx_data.width * tmx_data.tilewidth
        map_h = tmx_data.height * tmx_data.tileheight

        return StageData(
            map_layer=group,
            map_pixel_size=(map_w, map_h),
            stage_id=stage_id,
            stage_name=stage_name,
            time_limit=time_limit,
            bgm_track=bgm_track,
            gravity_multiplier=gravity_multiplier,
            climate=climate,
            zone=zone,
            ambient_light=ambient_light,
            bloom=bloom,
            vignette=vignette,
            ambient_fx=ambient_fx,
            ambient_fx_rate=ambient_fx_rate,
            start_hour=start_hour,
            day_length=day_length,
            season=season,
        )

    @classmethod
    def _parse_season(cls, props: dict[str, Any]) -> str:
        """Lee `season` del mapa y avisa si el nombre no existe.

        Igual que con `ambient_fx`: una errata no puede dejar el escenario a
        medias en silencio. Se avisa con la lista de nombres válidos y se
        devuelve cadena vacía para que la escena use su valor por defecto.
        """
        from src.framework.stage.seasons import ESTACIONES, es_valida

        valor = str(props.get("season", "") or "").strip().lower()
        if not valor:
            return ""
        if not es_valida(valor):
            logger.warning(
                "season: '%s' no es una estación conocida. Válidas: %s",
                valor, ", ".join(sorted(ESTACIONES)),
            )
            return ""
        return valor

    @classmethod
    def _parse_day_night(cls, props: dict[str, Any]) -> tuple[float | None, float]:
        """Lee `start_hour` y `day_length` del mapa.

        `start_hour` acepta un nombre (`dawn`, `dusk`, `night`...), un número
        (`18.5`) o `HH:MM`. Los tres se admiten porque el nombre es lo que un
        diseñador tiene en la cabeza, el número es lo que quiere quien está
        ajustando, y `HH:MM` es lo que se escribe sin pensar.

        `day_length` va en **segundos reales**: 300 significa que el ciclo
        completo dura cinco minutos de partida. Cero congela el reloj.
        """
        from src.framework.stage.day_night import RelojDeMundo

        hora = None
        if "start_hour" in props:
            hora = RelojDeMundo.hora_desde_texto(props.get("start_hour"))
        duracion = cls._parse_unit_prop(props, "day_length", 0.0, 36000.0) or 0.0
        return hora, duracion

    @classmethod
    def _parse_ambient_fx(cls, props: dict[str, Any]) -> str:
        """Lee `ambient_fx` del mapa y avisa si el tipo no existe.

        Una errata aquí no puede fallar en silencio: escribir `leafs` en vez de
        `leaves` dejaría el nivel sin partículas y sin ninguna pista de por qué.
        Se avisa por el registro y se devuelve cadena vacía, para que la escena
        caiga a su valor por zona en vez de quedarse a medias.
        """
        from src.framework.vfx.ambient_particles import AmbientParticleSystem

        valor = str(props.get("ambient_fx", "") or "").strip().lower()
        if not valor or valor == "none":
            return ""
        if valor not in AmbientParticleSystem.TIPOS:
            logger.warning(
                "ambient_fx: '%s' no es un tipo conocido. Válidos: %s, none",
                valor, ", ".join(AmbientParticleSystem.TIPOS),
            )
            return ""
        return valor

    @classmethod
    def _parse_unit_prop(
        cls, props: dict[str, Any], nombre: str, minimo: float, maximo: float,
    ) -> float | None:
        """Lee una propiedad numérica acotada del mapa, o `None` si no está.

        Se recorta al rango en vez de rechazar: un estudiante que escriba
        `bloom = 5` quiere "mucho brillo", y abortar la carga del nivel por eso
        no le enseña nada. Un valor no numérico sí es un error, porque ahí no
        hay intención que adivinar.
        """
        if nombre not in props:
            return None
        valor = cls._safe_float(props.get(nombre, minimo), nombre)
        return max(minimo, min(maximo, valor))

    @classmethod
    def _parse_ambient_light(cls, props: dict[str, Any]) -> float | None:
        """Lee `ambient_light` del mapa, o `None` si no está declarado.

        Se recorta a [0, 1] en vez de rechazar los valores fuera de rango: un
        estudiante que escriba `2` quiere "muy iluminado", y castigarle con un
        error de carga por eso no le enseña nada. Un valor no numérico sí es
        un error, porque ahí no hay intención que adivinar.
        """
        if "ambient_light" not in props:
            return None
        valor = cls._safe_float(props.get("ambient_light", 1.0), "ambient_light")
        return max(0.0, min(1.0, valor))

    @classmethod
    def _load_backgrounds(cls, stage: StageData, background_zone: str) -> None:
        if not background_zone:
            return
        bg_dir = settings.ASSETS_DIR / "backgrounds" / background_zone
        if bg_dir.is_dir():
            for bg_name in ("far", "mid", "near"):
                bg_path = bg_dir / f"bg_{background_zone}_{bg_name}.png"
                cls._try_append_bg(stage, bg_path)
        else:
            for bg_name in ("far", "mid", "near"):
                bg_path = settings.ASSETS_DIR / "backgrounds" / f"bg_{background_zone}_{bg_name}.png"
                cls._try_append_bg(stage, bg_path)

    @classmethod
    def _try_append_bg(cls, stage: StageData, bg_path: Path) -> None:
        try:
            bg_surf = AssetLoader.load_image(
                bg_path, size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
            )
            stage.background_layers.append(bg_surf)
        except (pygame.error, FileNotFoundError, PermissionError):
            logger.warning("StageLoader: missing bg %s", bg_path)

    @classmethod
    def _build_waypoints(cls, tmx_data: Any) -> dict[str, list[tuple[float, float]]]:
        waypoints_by_owner: dict[str, list[tuple[float, float]]] = {}
        for obj in tmx_data.get_layer_by_name("Objects"):
            obj_type = getattr(obj, "type", None) or ""
            if obj_type == "Waypoint":
                props = dict(obj.properties) if obj.properties else {}
                owner_id = props.get("owner_id", "")
                if owner_id:
                    waypoints_by_owner.setdefault(owner_id, []).append((float(obj.x), float(obj.y)))
        return waypoints_by_owner

    @classmethod
    def _process_objects(
        cls,
        tmx_data: Any,
        stage: StageData,
        waypoints_by_owner: dict[str, list[tuple[float, float]]],
        report: TmxReport,
    ) -> bool:
        player_spawn_found = False
        for obj in tmx_data.get_layer_by_name("Objects"):
            obj_type = getattr(obj, "type", None) or ""
            obj_name = getattr(obj, "name", "") or ""
            props = dict(obj.properties) if obj.properties else {}

            if obj_type == "PlayerSpawn":
                if player_spawn_found:
                    raise FrameworkUsageError("More than one PlayerSpawn object found")
                cls._handle_player_spawn(stage, obj)
                player_spawn_found = True

            elif obj_type == "MessageTrigger":
                cls._handle_message_trigger(stage, obj, props)

            elif obj_type == "MessageTrigger_Once":
                cls._handle_message_trigger(stage, obj, props)

            elif obj_type in cls._entity_registry:
                cls._handle_entity_spawn(stage, obj, obj_name, props, waypoints_by_owner)

            elif obj_type == "Checkpoint":
                cls._handle_checkpoint(stage, obj, props)

            elif obj_type == "NextTrigger":
                if obj.width > 0 and obj.height > 0:
                    stage.next_trigger = pygame.Rect(obj.x, obj.y, obj.width, obj.height)

            elif obj_type == "HazardZone":
                cls._handle_hazard_zone(stage, obj, props)

            elif obj_type == "DeathPit":
                if obj.width > 0 and obj.height > 0:
                    stage.death_pits.append(DeathPit(rect=pygame.Rect(obj.x, obj.y, obj.width, obj.height)))

            elif obj_type == "CameraLock":
                cls._handle_camera_lock(stage, obj, props)

            elif obj_type == "Light":
                cls._handle_light(stage, obj, props)

            # F4.1 — objetos con los que el jugador interactúa. Pedidos por los
            # estudiantes tras jugar la fase 1: llaves, puertas, jaulas, cofres
            # y disparadores de evento.
            elif obj_type in ("Pickup", "Key"):
                cls._handle_recogible(stage, obj, props)

            elif obj_type in ("Door", "Cage", "LockedDoor"):
                cls._handle_cerradura(stage, obj, props, obj_type)

            elif obj_type == "Chest":
                cls._handle_cofre(stage, obj, props)

            elif obj_type == "EventTrigger":
                cls._handle_disparador(stage, obj, props)

            elif obj_type != "Waypoint":
                # AUD-055. Esta rama no existía: cualquier `type` que no
                # coincidiera se descartaba en silencio, así que una errata en
                # Tiled producía un enemigo que simplemente no aparecía. Los
                # problemas se acumulan en lugar de abortar en el primero,
                # porque encontrar seis erratas de una vez es una corrección y
                # encontrarlas de una en una son seis ejecuciones del juego.
                report.add(cls._diagnose_object(obj, obj_type, obj_name))

        return player_spawn_found

    @classmethod
    def _diagnose_object(cls, obj: Any, obj_type: str, obj_name: str) -> TmxObjectProblem:
        """Describe un objeto que el cargador no supo interpretar."""
        known = known_object_types(list(cls._entity_registry))
        return TmxObjectProblem(
            object_id=int(getattr(obj, "id", 0) or 0),
            object_name=obj_name,
            object_type=obj_type,
            x=float(getattr(obj, "x", 0.0) or 0.0),
            y=float(getattr(obj, "y", 0.0) or 0.0),
            suggestions=suggest_types(obj_type, known),
            reason="objeto sin type" if not obj_type else "tipo desconocido",
        )

    @classmethod
    def _handle_player_spawn(cls, stage: StageData, obj: Any) -> None:
        stage.spawn_point = pygame.Vector2(obj.x, obj.y - 32)

    @classmethod
    def _handle_message_trigger(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        rect = pygame.Rect(obj.x, obj.y, obj.width or 32, obj.height or 32)
        text = props.get("text", "")
        stage.message_triggers.append(MessageTrigger(rect=rect, text=text))

    @classmethod
    def _handle_entity_spawn(
        cls,
        stage: StageData,
        obj: Any,
        obj_name: str,
        props: dict[str, Any],
        waypoints_by_owner: dict[str, list[tuple[float, float]]],
    ) -> None:
        obj_type = getattr(obj, "type", None) or ""
        entity_class = cls._entity_registry[obj_type]
        cleaned = cls._parse_entity_props(props)
        if obj_name and obj_name in waypoints_by_owner:
            cleaned["waypoints"] = waypoints_by_owner[obj_name]
        entity = entity_class(pygame.Vector2(obj.x, obj.y), **cleaned)
        stage.entity_list.append(entity)

    @classmethod
    def _parse_entity_props(cls, props: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for k, v in props.items():
            if k in ("zone",):
                cleaned[k] = cls._safe_int(v, "zone")
            elif k in _NUMERIC_PROPS:
                cleaned[k] = cls._safe_float(v, k)
            else:
                cleaned[k] = v
        return cleaned

    @classmethod
    def _handle_checkpoint(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        if "checkpoint_id" not in props:
            raise FrameworkUsageError("Checkpoint missing required property: checkpoint_id")
        rect = pygame.Rect(obj.x, obj.y, obj.width or 24, obj.height or 32)
        from src.framework.stage.checkpoint import Checkpoint
        cp = Checkpoint(pygame.Vector2(obj.x, obj.y), rect, int(props["checkpoint_id"]))
        stage.checkpoints.append(cp)

    #: Colores con nombre para la propiedad `color` de un objeto `Light`.
    #: Existen porque escribir `#ffdcb4` en Tiled es un obstáculo real para
    #: alguien que está aprendiendo, y porque una paleta corta produce
    #: escenarios más coherentes que la libertad total.
    LIGHT_COLORS: dict[str, tuple[int, int, int]] = {
        "warm": (255, 220, 180),      # antorcha, lámpara
        "cold": (180, 210, 255),      # luna, hielo
        "fire": (255, 120, 50),       # fuego, lava
        "toxic": (150, 255, 130),     # esporas, veneno
        "blood": (255, 60, 60),       # alarma, sangre
        "white": (255, 255, 255),
    }

    @classmethod
    def _handle_light(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        """Convierte un objeto `Light` de Tiled en un `LightSpec`.

        Propiedades reconocidas, todas opcionales:

        ==============  ======  ===========================================
        propiedad       tipo    significado
        ==============  ======  ===========================================
        `radius`        float   alcance en píxeles (por defecto 80)
        `color`         string  nombre de `LIGHT_COLORS` o `#rrggbb`
        `intensity`     float   0 a 1 (por defecto 0.8)
        `flicker`       bool    parpadeo tipo antorcha
        `flicker_speed` float   oscilaciones por segundo
        `flicker_amount` float  amplitud del parpadeo, 0 a 1
        ==============  ======  ===========================================

        El punto de luz se toma del **centro** del rectángulo dibujado en
        Tiled, no de su esquina. Es lo que espera cualquiera que dibuje un
        recuadro alrededor de una antorcha; usar la esquina desplazaría la luz
        y el estudiante no sabría por qué.
        """
        ancho = float(getattr(obj, "width", 0) or 0)
        alto = float(getattr(obj, "height", 0) or 0)
        centro = (float(obj.x) + ancho / 2.0, float(obj.y) + alto / 2.0)

        radio = cls._safe_float(props.get("radius", 80.0), "light radius")
        if radio <= 0:
            radio = 80.0

        stage.lights.append(LightSpec(
            position=centro,
            radius=radio,
            color=cls._parse_light_color(props.get("color")),
            intensity=max(0.0, min(1.0, cls._safe_float(
                props.get("intensity", 0.8), "light intensity"))),
            flicker=bool(props.get("flicker", False)),
            flicker_speed=cls._safe_float(
                props.get("flicker_speed", 4.0), "light flicker_speed"),
            flicker_amount=max(0.0, min(1.0, cls._safe_float(
                props.get("flicker_amount", 0.15), "light flicker_amount"))),
        ))

    @classmethod
    def _parse_light_color(cls, valor: Any) -> tuple[int, int, int]:
        """Acepta un nombre de la paleta, `#rrggbb`, o el formato de Tiled.

        Tiled guarda los colores como `#aarrggbb` —con alfa delante—, que es
        justo lo que nadie espera. Se aceptan las tres formas y se cae al
        color cálido ante cualquier cosa ininteligible, porque una luz del
        color equivocado se ve y se corrige, mientras que un error de carga
        deja al estudiante sin nivel.
        """
        if valor is None:
            return cls.LIGHT_COLORS["warm"]
        texto = str(valor).strip().lower()
        if texto in cls.LIGHT_COLORS:
            return cls.LIGHT_COLORS[texto]
        if texto.startswith("#"):
            digitos = texto[1:]
            if len(digitos) == 8:      # #aarrggbb de Tiled: se descarta el alfa
                digitos = digitos[2:]
            if len(digitos) == 6:
                try:
                    return (
                        int(digitos[0:2], 16),
                        int(digitos[2:4], 16),
                        int(digitos[4:6], 16),
                    )
                except ValueError:
                    pass
        logger.warning(
            "Light: color '%s' no reconocido; se usa 'warm'. Válidos: %s o #rrggbb",
            valor, ", ".join(sorted(cls.LIGHT_COLORS)),
        )
        return cls.LIGHT_COLORS["warm"]

    @classmethod
    def _handle_recogible(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        """`Pickup` / `Key` — algo que el jugador coge del suelo.

        `Key` es un alias de `Pickup`: nombrar el tipo por lo que es hace el
        mapa legible en Tiled, y a efectos del motor son lo mismo.
        """
        item_id = str(props.get("item_id") or props.get("key_id") or obj.name or "")
        if not item_id:
            logger.warning(
                "Pickup en (%s, %s) sin 'item_id': se ignora. Ponle un item_id "
                "o dale nombre al objeto en Tiled.", obj.x, obj.y,
            )
            return
        stage.recogibles.append(Recogible(
            rect=cls._rect_de(obj),
            item_id=item_id,
            automatico=cls._bool_de(props.get("automatico"), por_defecto=True),
            mensaje=str(props.get("mensaje", "")),
        ))

    @classmethod
    def _handle_cerradura(
        cls, stage: StageData, obj: Any, props: dict[str, Any], obj_type: str,
    ) -> None:
        """`Door` / `Cage` / `LockedDoor` — bloquea el paso hasta tener la llave."""
        if obj.width == 0 or obj.height == 0:
            logger.warning(
                "%s en (%s, %s) no tiene tamaño: una puerta sin área no bloquea "
                "nada. Dibújala como rectángulo en Tiled.", obj_type, obj.x, obj.y,
            )
            return
        stage.cerraduras.append(Cerradura(
            rect=cls._rect_de(obj),
            key_id=str(props.get("key_id", "")),
            clase="jaula" if obj_type == "Cage" else "puerta",
            consume_llave=cls._bool_de(props.get("consume_llave"), por_defecto=False),
            mensaje_bloqueado=str(props.get("mensaje", "")),
            evento_al_abrir=str(props.get("evento", "")),
        ))

    @classmethod
    def _handle_cofre(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        """`Chest` — se abre con el botón y entrega su contenido una vez."""
        stage.cofres.append(Cofre(
            rect=cls._rect_de(obj),
            contenido=str(props.get("contenido") or props.get("item_id") or ""),
            key_id=str(props.get("key_id", "")),
            mensaje=str(props.get("mensaje", "")),
            evento_al_abrir=str(props.get("evento", "")),
        ))

    @classmethod
    def _handle_disparador(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        """`EventTrigger` — emite un evento del bus; el escenario decide qué hace."""
        evento = str(props.get("evento") or obj.name or "")
        if not evento:
            logger.warning(
                "EventTrigger en (%s, %s) sin 'evento': no emitiría nada, así "
                "que se ignora.", obj.x, obj.y,
            )
            return
        stage.disparadores.append(Disparador(
            rect=cls._rect_de(obj),
            evento=evento,
            automatico=cls._bool_de(props.get("automatico"), por_defecto=True),
            una_vez=cls._bool_de(props.get("una_vez"), por_defecto=True),
            key_id=str(props.get("key_id", "")),
        ))

    @staticmethod
    def _rect_de(obj: Any) -> pygame.Rect:
        """El rectángulo de un objeto de Tiled, con un mínimo utilizable.

        Un objeto de tipo punto tiene ancho y alto 0 y sería imposible de
        tocar. Se le da el tamaño de una baldosa, que es lo que el diseñador
        ve en Tiled cuando coloca el punto.
        """
        ancho = int(obj.width) or settings.TILE_SIZE
        alto = int(obj.height) or settings.TILE_SIZE
        return pygame.Rect(int(obj.x), int(obj.y), ancho, alto)

    @staticmethod
    def _bool_de(valor: Any, *, por_defecto: bool) -> bool:
        """Tiled entrega los booleanos como bool, como 'true' o como '1'."""
        if valor is None or valor == "":
            return por_defecto
        if isinstance(valor, bool):
            return valor
        return str(valor).strip().lower() in ("true", "1", "si", "sí", "yes")

    @classmethod
    def _handle_hazard_zone(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        if obj.width == 0 or obj.height == 0:
            return
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        damage = cls._safe_float(props.get("damage", 0.25), "hazard damage")
        stage.hazard_zones.append(HazardZone(rect=rect, damage=damage))

    @classmethod
    def _handle_camera_lock(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        if obj.width == 0 or obj.height == 0:
            return
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        lock_x = props.get("lock_x", False) in (True, "true", "True", 1, "1")
        lock_y = props.get("lock_y", False) in (True, "true", "True", 1, "1")
        stage.camera_locks.append(CameraLock(rect=rect, lock_x=lock_x, lock_y=lock_y))

    @classmethod
    def _load_collision(cls, tmx_data: Any, stage: StageData) -> None:
        try:
            collision_layer = tmx_data.get_layer_by_name("Collision")
            for obj in collision_layer:
                rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                if rect.width > 0 and rect.height > 0:
                    obj_type = getattr(obj, "type", None) or ""
                    if obj_type == "Platform":
                        stage.one_way_rects.append(rect)
                    else:
                        stage.collision_rects.append(rect)
        except ValueError:
            logger.warning("StageLoader: Collision layer not found")

    # ── Safe converters ───────────────────────────────────────────

    @classmethod
    def _safe_int(cls, value: Any, name: str) -> int:
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning("StageLoader: invalid %s value '%s', using 0", name, value)
            return 0

    @classmethod
    def _safe_float(cls, value: Any, name: str) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning("StageLoader: invalid %s value '%s', using 0.0", name, value)
            return 0.0
