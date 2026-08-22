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
import re
import warnings
from pathlib import Path
from typing import Any

import pygame
import pyscroll
import pyscroll.data
from pytmx.util_pygame import load_pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework import FrameworkUsageError
from src.framework.entities.base_entity import BaseEntity
from src.framework.physics.capas import Capa
from src.framework.stage.stage_data import (
    _TIPOS_DE_COMPONENTE,
    MODOS_DE_CAMARA,
    REQUIRED_LAYERS,
    VISTAS_VALIDAS,
    CameraLock,
    DeathPit,
    EscenaGuionizada,
    HazardZone,
    LightSpec,
    MessageTrigger,
    StageData,
)
from src.framework.stage.stage_objetos import ObjetosDeTiled
from src.framework.stage.tmx_diagnostics import (
    TmxReport,
    known_object_types,
)

logger = logging.getLogger(__name__)

#: AUD-393 — la versión del contrato TMX que este cargador entiende.
#:
#: Cierra la mitad viva de GAP-048. El problema que resuelve no es hipotético:
#: sin versión, un mapa escrito para otra época del motor —una propiedad
#: renombrada, un tipo de objeto que cambió de significado— falla como **dato
#: malo**. El mensaje habla de una capa que falta, y quien lo lee busca el
#: error dentro de su mapa en vez de en la distancia entre su mapa y este
#: motor.
#:
#: Sube cuando cambie el significado de algo que ya existe —renombrar una
#: propiedad, cambiar unidades, retirar un tipo de objeto—. **No** sube por
#: añadir una propiedad nueva: un mapa que no la declara sigue cargando igual,
#: que es justo lo que la hace compatible hacia atrás.
SCHEMA_VERSION = 1

__all__ = [
    "MODOS_DE_CAMARA",
    "REQUIRED_LAYERS",
    "SCHEMA_VERSION",
    "VISTAS_VALIDAS",
    "_TIPOS_DE_COMPONENTE",
    "CameraLock",
    "DeathPit",
    "EscenaGuionizada",
    "HazardZone",
    "LightSpec",
    "MessageTrigger",
    "StageData",
    "StageLoader",
]

class StageLoader(ObjetosDeTiled):
    _entity_registry: dict[str, type[BaseEntity]] = {}

    #: Todo lo que se registró alguna vez (AUD-144).
    #:
    #: Varias pruebas hacen `StageLoader._entity_registry.clear()` para
    #: empezar de cero. Eso vacía también los tipos que registran los
    #: escenarios a nivel de módulo —`LaSodaWalkerRaton`, `BossGavilan`…— y,
    #: como el módulo ya está importado, sus efectos de importación no se
    #: repiten. Este registro histórico no se vacía nunca: el cargador lo
    #: usa para devolver al registro lo que falte antes de procesar el mapa.

    _registro_historico: dict[str, type[BaseEntity]] = {}

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

        AUD-144: antes de importar se restauran del registro histórico los
        tipos que alguien vació. Un módulo re-importado no repetiría sus
        efectos, así que esta copia es lo único que puede devolverlos.
        """
        import importlib
        import pkgutil

        faltan = {
            k: v for k, v in cls._registro_historico.items()
            if k not in cls._entity_registry
        }
        if faltan:
            cls._entity_registry.update(faltan)
            return True

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
        cls._registro_historico[type_name] = entity_class

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

        cls._rechazar_mapa_hostil(resolved)
        tmx_data = load_pygame(str(resolved))
        # Only ever keep one parse in flight; stages are large and holding
        # several maps' tilesets resident is not worth the memory.
        cls._tmx_cache.clear()
        cls._tmx_cache[key] = tmx_data
        return tmx_data

    #: `source="..."` aparece en `<tileset>`, `<image>` y `<objecttemplate>`.
    #: Es la lista de rutas que pytmx abrirá por su cuenta.

    _FUENTE_TMX = re.compile(rb'source="([^"]*)"')

    @classmethod
    def _rechazar_mapa_hostil(cls, tmx_path: Path) -> None:
        """AUD-317 — dos cosas que pytmx hace sin preguntar y que un TMX
        hostil puede explotar:

        * **Expansión de entidades XML** (*billion laughs*): el parser de
          pytmx expande `<!ENTITY>` sin límite; un mapa de 400 bytes puede
          pedir gigabytes de RAM. Tiled jamás exporta entidades propias, así
          que cualquier `<!ENTITY>` es un ataque y se corta antes de parsear.
        * **Travesía de rutas**: las `source="..."` se resuelven contra el
          directorio del mapa y pytmx abre el resultado sin preguntar. Para
          los mapas dentro del árbol del juego, ninguna source puede resolver
          fuera de él (los mapas reales usan `../../../assets/...`, que
          vuelve a entrar en el árbol). Los mapas fuera del árbol —pruebas,
          herramientas— no se juzgan: no hay raíz que usar como contención.

        Falla duro y pronto: un mapa envenenado no debe llegar a abrir ficheros.
        """
        try:
            crudo = tmx_path.read_bytes()
        except OSError:
            # El fichero no se puede leer: pytmx ya dirá su error. No cambia
            # el comportamiento, sólo no mete una lectura extra en el camino.
            return

        if b"<!ENTITY" in crudo.upper():
            raise ValueError(
                f"mapa hostil: {tmx_path.name} declara entidades XML "
                "(<!ENTITY>); el parser las expande sin límite. Se rechaza "
                "antes de parsear para que no haya expansión que acotar."
            )

        if cls._bajo(tmx_path, settings.PROJECT_ROOT):
            cls._rechazar_travesia_en(tmx_path, crudo)

    @classmethod
    def _rechazar_travesia_en(cls, tmx_path: Path, crudo: bytes) -> None:
        """Recorre las `source="..."` del TMX y de sus TSX comprobando que
        ninguna resuelva fuera de `PROJECT_ROOT`."""
        pendientes: list[tuple[Path, bytes]] = [(tmx_path, crudo)]
        vistos: set[Path] = set()
        while pendientes:
            archivo, texto = pendientes.pop()
            vistos.add(archivo)
            for m in cls._FUENTE_TMX.finditer(texto):
                referencia = m.group(1).decode("utf-8", "replace")
                if not referencia:
                    continue
                destino = (archivo.parent / referencia).resolve()
                if not cls._bajo(destino, settings.PROJECT_ROOT):
                    raise ValueError(
                        f"mapa hostil: {tmx_path.name} referencia {referencia!r}, "
                        f"que resuelve fuera del árbol del juego ({destino}). "
                        "Los mapas y sus tilesets viven dentro del proyecto."
                    )
                if destino.suffix.lower() == ".tsx" and destino not in vistos:
                    try:
                        pendientes.append((destino, destino.read_bytes()))
                    except OSError:
                        pass  # pytmx dirá que falta; aquí no hay travesía que juzgar

    @staticmethod
    def _bajo(ruta: Path, raiz: Path) -> bool:
        try:
            ruta.relative_to(raiz)
            return True
        except ValueError:
            return False

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
        # AUD-393 — la versión, antes que las capas. Si el mapa es de otra
        # época, «falta la capa Collision» es un diagnóstico engañoso: la capa
        # no falta, en esa versión se llamaba de otra manera.
        cls._validate_schema_version(tmx_data)
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
                stage.scroll_forzados.clear()
                stage.escenas.clear()
                stage.empujables.clear()
                stage.destructibles.clear()
                stage.camera_locks.clear()
                stage.lights.clear()
                stage.zonas_luz_ambiente.clear()
                stage.zonas_musica.clear()
                stage.zonas_zoom.clear()
                stage.recogibles.clear()
                stage.cerraduras.clear()
                stage.cofres.clear()
                stage.disparadores.clear()
                stage.componentes.clear()
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
    def _validate_schema_version(cls, tmx_data: Any) -> None:
        """Rechaza un mapa escrito para una versión del motor posterior a ésta.

        AUD-393 — las tres ramas, y por qué no son simétricas
        -----------------------------------------------------
        * **No la declara**: se asume `1` y se sigue en silencio. Ningún TMX
          anterior a este lote la lleva, incluidas las entregas ya calificadas,
          y llenarles la consola de avisos por una propiedad inventada después
          no ayuda a nadie. Quien quiera la queja tiene
          `scripts/validate_tmx.py`, que sí avisa — ahí es donde se arreglan
          los mapas.
        * **Mayor que la del motor**: se rechaza. Ese mapa usa cosas que este
          cargador no entiende; abrirlo a medias da comportamiento incorrecto
          en silencio, que es peor que no abrirlo. Es la única rama que
          interrumpe.
        * **No es un número**: aviso y se sigue. Es dato malo, no
          incompatibilidad, y el resto del cargador trata el dato malo así
          (`_safe_int`, `_safe_float`, la vista y la cámara desconocidas).

        Una versión **menor** que la actual carga sin decir nada: ése es el
        sentido de tener versiones. El día que un cambio rompa la
        compatibilidad hacia atrás, aquí es donde se escribe la conversión.
        """
        declarada = tmx_data.properties.get("schema_version")
        if declarada is None:
            return
        try:
            version = int(str(declarada).strip())
        except (TypeError, ValueError):
            logger.warning(
                "StageLoader: schema_version %r no es un número — se asume %d",
                declarada, SCHEMA_VERSION,
            )
            return
        if version > SCHEMA_VERSION:
            raise FrameworkUsageError(
                f"El mapa declara schema_version={version} y este motor "
                f"entiende hasta la {SCHEMA_VERSION}. El mapa es más nuevo que "
                "el código: actualiza el motor, o vuelve a exportar el mapa "
                "con la versión de esquema que este motor lee."
            )

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
        # AUD-137 — el compás. Sin `bpm` no hay reloj musical y el escenario se
        # comporta como siempre.
        bpm = max(0.0, cls._safe_float(props.get("bpm", 0.0), "bpm"))
        compas = max(1, cls._safe_int(props.get("compas", 4), "compas"))
        desfase_audio = cls._safe_float(
            props.get("desfase_audio", 0.0), "desfase_audio")
        estamina = max(0.0, cls._safe_float(props.get("estamina", 0.0), "estamina"))
        tiempo_bala = max(
            0.0, cls._safe_float(props.get("tiempo_bala", 0.0), "tiempo_bala"))
        profundidad_min = max(0.05, cls._safe_float(
            props.get("profundidad_min", 1.0), "profundidad_min"))
        profundidad_max = max(0.05, cls._safe_float(
            props.get("profundidad_max", 1.0), "profundidad_max"))
        # AUD-339 — la curva comparte el suelo de 0.05 con los extremos: una
        # curva negativa invertiría el degradado y una de 0.0 lo congelaría.
        profundidad_curva = max(0.05, cls._safe_float(
            props.get("profundidad_curva", 1.0), "profundidad_curva"))
        orden_por_y = cls._bool_de(
            props.get("orden_por_y"), por_defecto=False)
        sombras_proyectadas = cls._bool_de(
            props.get("sombras_proyectadas"), por_defecto=False)
        habilidades_libres = cls._bool_de(
            props.get("habilidades_libres"), por_defecto=False)
        camara = str(props.get("camara") or props.get("camera") or "seguir").strip().lower()
        if camara not in MODOS_DE_CAMARA:
            logger.warning(
                "StageLoader: camara %r desconocida — se usa 'seguir'. "
                "Valores válidos: %s", camara, ", ".join(sorted(MODOS_DE_CAMARA)),
            )
            camara = "seguir"
        climate = props.get("climate", "")
        # AUD-129 — una vista desconocida cae a lateral con aviso, no rompe.
        # `view` en inglés se acepta igual: el proyecto es bilingüe en las
        # propiedades desde F3.1 y obligar a recordar cuál lleva cada una es
        # la clase de fricción que produce mapas que no cargan.
        vista = str(props.get("vista") or props.get("view") or "lateral").strip().lower()
        if vista not in VISTAS_VALIDAS:
            logger.warning(
                "StageLoader: vista %r desconocida — se usa 'lateral'. "
                "Valores válidos: %s", vista, ", ".join(sorted(VISTAS_VALIDAS)),
            )
            vista = "lateral"
        zone = cls._safe_int(props.get("zone", 0), "zone")
        ambient_light = cls._parse_ambient_light(props)
        bloom = cls._parse_unit_prop(props, "bloom", 0.0, 1.0)
        vignette = cls._parse_unit_prop(props, "vignette", 0.0, 0.6)
        ambient_fx = cls._parse_ambient_fx(props)
        ambient_fx_rate = cls._parse_unit_prop(props, "ambient_fx_rate", 0.0, 120.0)
        start_hour, day_length = cls._parse_day_night(props)
        season = cls._parse_season(props)
        # AUD-111 — VFX opcionales. Apagados salvo que el mapa los pida.
        fog_of_war = cls._safe_float(props.get("fog_of_war", 0.0), "fog_of_war")
        water_effect = cls._bool_de(props.get("water_effect"), por_defecto=False)
        # AUD-426 — cielo procedural. Apagado salvo que el mapa lo pida.
        cielo = cls._bool_de(props.get("cielo"), por_defecto=False)
        # AUD-240 — los mandos del agua. Los rangos no son decorativos: una
        # amplitud de 40 px convierte la lámina en ruido y un alfa de 255 tapa
        # el escenario. Se acotan aquí y no en el efecto para que un mapa mal
        # escrito se vea raro pero jugable, que es la regla del resto del
        # cargador.
        # `_parse_unit_prop` devuelve `None` cuando el mapa no dice nada, y su
        # tercer argumento es el MÍNIMO del rango, no el valor por defecto: los
        # defectos se aplican aquí, y son los de `WaterEffect`, para que un mapa
        # que no declare nada se vea exactamente igual que antes de AUD-240.
        water_speed = cls._parse_unit_prop(props, "water_speed", 0.0, 8.0)
        water_amplitude = cls._parse_unit_prop(props, "water_amplitude", 0.0, 16.0)
        water_frequency = cls._parse_unit_prop(props, "water_frequency", 0.0, 1.0)
        water_alpha = cls._parse_unit_prop(props, "water_alpha", 0.0, 255.0)
        water_tint = (cls._parse_light_color(props["water_tint"])
                      if props.get("water_tint") is not None else (40, 80, 160))
        god_rays = cls._safe_float(props.get("god_rays", 0.0), "god_rays")

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
            vista=vista,
            bpm=bpm,
            compas=compas,
            desfase_audio=desfase_audio,
            estamina=estamina,
            tiempo_bala=tiempo_bala,
            profundidad_min=profundidad_min,
            profundidad_max=profundidad_max,
            profundidad_curva=profundidad_curva,
            orden_por_y=orden_por_y,
            sombras_proyectadas=sombras_proyectadas,
            habilidades_libres=habilidades_libres,
            camara=camara,
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
            fog_of_war=fog_of_war,
            water_effect=water_effect,
            cielo=cielo,
            water_speed=1.5 if water_speed is None else water_speed,
            water_amplitude=4 if water_amplitude is None else int(water_amplitude),
            water_frequency=0.04 if water_frequency is None else water_frequency,
            water_alpha=100 if water_alpha is None else int(water_alpha),
            water_tint=water_tint,
            god_rays=god_rays,
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

    #: AUD-272 — las capas de fondo, de lo más lejano a lo más cercano.
    #:
    #: Eran tres y el dibujado ya admitía cuatro velocidades: la profundidad
    #: estaba limitada por el lado que menos costaba cambiar. `sky` y `deep`
    #: son nuevas.

    CAPAS_DE_FONDO: tuple[str, ...] = ("sky", "deep", "far", "mid", "near")

    #: Las que un mapa puede no tener sin que eso sea una errata. Las tres de
    #: siempre siguen avisando si faltan, porque ahí sí lo es.

    CAPAS_OPCIONALES: frozenset[str] = frozenset({"sky", "deep"})

    #: Cuánto se mueve cada capa respecto a la cámara, **por nombre**.
    #:
    #: Por nombre y no por posición: antes el factor salía del índice de carga,
    #: así que un mapa que añadiera una capa delante hacía que `far` pasara de
    #: 0,15 a 0,35 y el mismo fondo se moviera distinto en dos escenarios sin
    #: que nadie lo pidiera.
    #:
    #: Ninguna llega a 1,0: un fondo a la velocidad de la cámara se pega al
    #: terreno y deja de leerse como fondo.

    VELOCIDAD_DE_FONDO: dict[str, float] = {
        "sky": 0.06,     # casi quieto; un cielo que sigue a la cámara no es cielo
        "deep": 0.10,
        "far": 0.15,     # los tres de siempre conservan su velocidad exacta
        "mid": 0.35,
        "near": 0.60,
    }

    @classmethod
    def _load_backgrounds(cls, stage: StageData, background_zone: str) -> None:
        if not background_zone:
            return
        bg_dir = settings.ASSETS_DIR / "backgrounds" / background_zone
        base = bg_dir if bg_dir.is_dir() else settings.ASSETS_DIR / "backgrounds"
        for bg_name in cls.CAPAS_DE_FONDO:
            bg_path = base / f"bg_{background_zone}_{bg_name}.png"
            if bg_name in cls.CAPAS_OPCIONALES and not bg_path.is_file():
                continue
            if cls._try_append_bg(stage, bg_path):
                stage.background_factors.append(cls.VELOCIDAD_DE_FONDO[bg_name])

    @classmethod
    def _try_append_bg(cls, stage: StageData, bg_path: Path) -> bool:
        """Carga una capa de fondo. Devuelve si se pudo (AUD-272).

        Devuelve algo, y no nada, porque quien llama necesita saberlo para
        apuntar la velocidad de la capa **sólo si la capa existe**: si no, los
        dos listados se desincronizarían en cuanto faltara un fichero.
        """
        try:
            bg_surf = AssetLoader.load_image(
                bg_path, size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
            )
            stage.background_layers.append(bg_surf)
            return True
        except (pygame.error, FileNotFoundError, PermissionError):
            logger.warning("StageLoader: missing bg %s", bg_path)
            return False

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

        # AUD-395 — la misma clasificación, indexada por capa (GAP-038).
        #
        # Aquí ya se decidía la clase de cada caja —`Platform` o no— y se
        # guardaba esa decisión en *qué lista* iba a parar. Eso es una capa,
        # sólo que expresada de una forma que no se puede consultar ni ampliar:
        # para preguntar «¿qué frena a esta entidad?» había que saberse las
        # listas y sumarlas a mano en cada sitio.
        #
        # Se publican las dos vistas de la misma verdad, y se llenan juntas
        # para que no puedan discrepar.
        stage.capas.poner(Capa.SOLIDO, stage.collision_rects)
        stage.capas.poner(Capa.PLATAFORMA, stage.one_way_rects)

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
