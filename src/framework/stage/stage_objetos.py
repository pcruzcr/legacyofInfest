"""
Cada objeto de Tiled que el escenario entiende, y cómo se convierte.

Extraído de `stage_loader.py` en AUD-350 sin cambiar una línea de lógica.
Es un mixin de `StageLoader`: un mismo despachador (`_process_objects`)
recorre la capa `Objects` y reparte cada `type` a su manejador.

Un tipo desconocido no se descarta (AUD-055): se diagnostica y se acumula
en `TmxReport` para que el estudiante vea las erratas todas a la vez. Los
manejadores comparten un lenguaje de propiedades pensado para Tiled —un
estudiante escribe `fuerza_x`, no el nombre de la clase— y convertidores
que recortan en vez de rechazar (`_parse_unit_prop`).
"""

from __future__ import annotations

import logging
from typing import Any

import pygame

from src.engine.core import settings
from src.framework import FrameworkUsageError
from src.framework.stage.bloques import (
    BloqueDestructible,
    BloqueEmpujable,
)
from src.framework.stage.interactables import (
    Cerradura,
    Cofre,
    Disparador,
    Recogible,
    ZonaDeWarp,
)
from src.framework.stage.pendientes import Pendiente
from src.framework.stage.stage_data import (
    _BOOL_PROPS,
    _NUMERIC_PROPS,
    _TIPOS_DE_COMPONENTE,
    CameraLock,
    DeathPit,
    EscenaGuionizada,
    HazardZone,
    LightSpec,
    MessageTrigger,
    StageData,
    ZonaLuzAmbienteSpec,
    ZonaMusicaSpec,
    ZonaZoomSpec,
)
from src.framework.stage.tmx_diagnostics import (
    TmxObjectProblem,
    TmxReport,
    known_object_types,
    suggest_types,
)

logger = logging.getLogger(__name__)

class ObjetosDeTiled:
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

            elif obj_type == "PushBlock":
                cls._handle_bloque(stage, obj, props, empujable=True)

            elif obj_type == "BreakableBlock":
                cls._handle_bloque(stage, obj, props, empujable=False)

            elif obj_type == "Cutscene":
                cls._handle_cutscene(stage, obj, props)

            elif obj_type == "Objective":
                cls._handle_objetivo(stage, obj, props, obj_name)

            elif obj_type == "DeathPit":
                if obj.width > 0 and obj.height > 0:
                    stage.death_pits.append(DeathPit(rect=pygame.Rect(obj.x, obj.y, obj.width, obj.height)))

            elif obj_type == "CameraLock":
                cls._handle_camera_lock(stage, obj, props)

            elif obj_type == "Light":
                cls._handle_light(stage, obj, props)

            elif obj_type == "AmbientLightZone":
                cls._handle_zona_luz_ambiente(stage, obj, props)

            elif obj_type == "MusicZone":
                cls._handle_zona_musica(stage, obj, props)

            elif obj_type == "CameraZoomZone":
                cls._handle_zona_zoom(stage, obj, props)

            # AUD-605 — la arena del jefe, dibujada en Tiled.
            elif obj_type == "ArenaZone":
                cls._handle_zona_arena(stage, obj)

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

            elif obj_type == "BossSpawn":
                problema = cls._handle_boss_spawn(stage, obj)
                if problema is not None:
                    report.add(problema)

            elif obj_type == "ScrollZone":
                cls._handle_scroll_forzado(stage, obj, props)

            elif obj_type == "WarpZone":
                cls._handle_warp(stage, obj, props)

            elif obj_type == "Slope":
                cls._handle_pendiente(stage, obj, props)

            # F5.3–F5.6 — mecánicas del Top 200 declaradas desde Tiled.
            elif obj_type in _TIPOS_DE_COMPONENTE:
                cls._handle_componente(stage, obj, props, obj_type)

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
        # AUD-127 — `dialogue` abre un árbol de diálogo en vez de un mensaje.
        #
        # Un `MessageTrigger` con `dialogue` y sin `text` es una conversación;
        # con `text` y sin `dialogue`, un aviso de una línea. Con los dos, el
        # aviso se muestra y la conversación se abre después: no se pierde
        # ninguno de los dos, que es lo que ocurriría si uno tuviera prioridad
        # sobre el otro en silencio.
        arbol = str(props.get("dialogue", "") or props.get("dialogue_tree", ""))
        stage.message_triggers.append(
            MessageTrigger(rect=rect, text=text, dialogue_tree_id=arbol),
        )

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
        # AUD-387 - las resistencias por canal, si el objeto las declara. Se
        # asignan despues de construir y no como argumento del constructor
        # porque las 30 especies tienen firmas distintas y varias las heredan
        # de entregas: un `**cleaned` con una clave que su `__init__` no espera
        # revienta el nivel entero.
        resistencias = cls._resistencias_de(props.get("resistencias"))
        if resistencias:
            entity.resistencias = resistencias
        stage.entity_list.append(entity)

    @classmethod
    def _handle_boss_spawn(cls, stage: StageData, obj: Any) -> TmxObjectProblem | None:
        """`BossSpawn` — dónde entra el jefe que el mapa nombra (AUD-259).

        `17_BOSS_SPEC.md` §8.2 lo exige en todo mapa de jefe desde que se
        escribió, y el cargador **no lo conocía**: un estudiante que siguiera
        su propia especificación recibía un aviso de tipo desconocido y su
        jefe no aparecía.

        No construye «un jefe» —el motor no sabe cuál— sino el que declara la
        propiedad `boss`, resuelto por el mismo registro de entidades que usan
        `BossVenado` y compañía. Escribir `BossSpawn` con `boss="BossVenado"`
        produce exactamente la misma entidad que escribir `BossVenado`.

        Sin `boss`, o con un nombre no registrado, **avisa** por el camino de
        diagnóstico de AUD-055. Callarse sería repetir el defecto que esto
        arregla: el estudiante escribe algo razonable y no ocurre nada.
        """
        props = dict(obj.properties) if obj.properties else {}
        nombre = str(props.pop("boss", "") or "")
        if not nombre or nombre not in cls._entity_registry:
            problema = cls._diagnose_object(
                obj, "BossSpawn", getattr(obj, "name", "") or "")
            problema.reason = (
                "BossSpawn sin propiedad `boss`" if not nombre
                else f"BossSpawn declara boss='{nombre}', que no está registrado"
            )
            return problema

        entity_class = cls._entity_registry[nombre]
        entity = entity_class(
            pygame.Vector2(obj.x, obj.y), **cls._parse_entity_props(props))
        stage.entity_list.append(entity)
        return None

    @classmethod
    def _handle_boss_spawn_para_pruebas(
        cls, obj: Any, destino: list[Any],
    ) -> TmxObjectProblem | None:
        """Adaptador para probar `_handle_boss_spawn` sin un `StageData`.

        Existe porque el defecto que cierra AUD-259 vive en la resolución del
        tipo, no en el escenario: montar un TMX entero para comprobarlo haría
        la prueba lenta y menos clara sobre qué falló.
        """
        class _Destino:
            entity_list = destino

        return cls._handle_boss_spawn(_Destino(), obj)  # type: ignore[arg-type]

    @classmethod
    def _parse_entity_props(cls, props: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for k, v in props.items():
            if k in ("zone",):
                cleaned[k] = cls._safe_int(v, "zone")
            elif k in _NUMERIC_PROPS:
                cleaned[k] = cls._safe_float(v, k)
            elif k in _BOOL_PROPS:
                cleaned[k] = cls._bool_de(v, por_defecto=False)
            else:
                cleaned[k] = v
        return cleaned

    @classmethod
    def _handle_checkpoint(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        if "checkpoint_id" not in props:
            raise FrameworkUsageError("Checkpoint missing required property: checkpoint_id")
        rect = pygame.Rect(obj.x, obj.y, obj.width or 24, obj.height or 32)
        from src.framework.stage.checkpoint import Checkpoint
        # AUD-523 — el haz de luz es el checkpoint, sin propiedad que lo
        # active: AUD-517 lo dejó opt-in (`brillo=`) para 4.1b/4.1c, pero
        # el dueño pidió reemplazar el sprite fijo en los 26 escenarios,
        # no sólo en esos tres.
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
    def _handle_zona_luz_ambiente(
        cls, stage: StageData, obj: Any, props: dict[str, Any],
    ) -> None:
        """Convierte un objeto `AmbientLightZone` de Tiled en una
        `ZonaLuzAmbienteSpec` (GAP-072.4, AUD-598).

        Propiedades reconocidas:

        ==========  ======  ==================================================
        propiedad   tipo    significado
        ==========  ======  ==================================================
        `valor`     float   brillo ambiental dentro de la zona, 0 a 1
                            (por defecto 1.0 = sin cambio)
        `fundido`   float   ancho de la banda de transición del borde, en px
                            (por defecto 64)
        ==========  ======  ==================================================

        El rectángulo se toma tal cual se dibujó: es la región donde manda
        el `valor`, no un punto.
        """
        rect = pygame.Rect(
            int(float(getattr(obj, "x", 0) or 0)),
            int(float(getattr(obj, "y", 0) or 0)),
            max(1, int(float(getattr(obj, "width", 0) or 0))),
            max(1, int(float(getattr(obj, "height", 0) or 0))),
        )

        def _flave(nombre: str, defecto: float) -> float:
            # `ObjetosDeTiled` es un mixin: `cls._safe_float` vive en
            # `StageLoader`, y este manejador también se llama directo desde
            # las pruebas con la clase sola.
            try:
                return float(props.get(nombre, defecto))
            except (TypeError, ValueError):
                return defecto

        stage.zonas_luz_ambiente.append(ZonaLuzAmbienteSpec(
            rect=rect,
            valor=max(0.0, min(1.0, _flave("valor", 1.0))),
            fundido=max(0, int(_flave("fundido", 64.0))),
        ))

    @classmethod
    def _handle_zona_musica(
        cls, stage: StageData, obj: Any, props: dict[str, Any],
    ) -> None:
        """Convierte un objeto `MusicZone` de Tiled en una `ZonaMusicaSpec`
        (GAP-072.2, AUD-600).

        Propiedades reconocidas:

        ============  ======  =============================================
        propiedad     tipo    significado
        ============  ======  =============================================
        `track`       string  nombre de pista sin extensión; cadena vacía
                              = silencio deliberado (por defecto "")
        `fundido_ms`  float   entrada con fundido, en ms (por defecto 800)
        ============  ======  =============================================
        """
        rect = pygame.Rect(
            int(float(getattr(obj, "x", 0) or 0)),
            int(float(getattr(obj, "y", 0) or 0)),
            max(1, int(float(getattr(obj, "width", 0) or 0))),
            max(1, int(float(getattr(obj, "height", 0) or 0))),
        )
        track = str(props.get("track", "") or "")
        try:
            fundido_ms = max(0, int(float(props.get("fundido_ms", 800))))
        except (TypeError, ValueError):
            fundido_ms = 800
        stage.zonas_musica.append(ZonaMusicaSpec(
            rect=rect, track=track, fundido_ms=fundido_ms))

    @classmethod
    def _handle_zona_zoom(
        cls, stage: StageData, obj: Any, props: dict[str, Any],
    ) -> None:
        """Convierte un objeto `CameraZoomZone` de Tiled en una
        `ZonaZoomSpec` (GAP-072.3, AUD-601).

        Propiedades reconocidas:

        ============  ======  =============================================
        propiedad     tipo    significado
        ============  ======  =============================================
        `factor`      float   zoom mientras el jugador esté dentro:
                              >1 acerca, <1 aleja (0.75 por defecto,
                              saturado a 0.4-2.5)
        `segundos`    float   duración del tween (1.5)
        ============  ======  =============================================
        """
        rect = pygame.Rect(
            int(float(getattr(obj, "x", 0) or 0)),
            int(float(getattr(obj, "y", 0) or 0)),
            max(1, int(float(getattr(obj, "width", 0) or 0))),
            max(1, int(float(getattr(obj, "height", 0) or 0))),
        )
        try:
            factor = float(props.get("factor", 0.75))
        except (TypeError, ValueError):
            factor = 0.75
        try:
            segundos = float(props.get("segundos", 1.5))
        except (TypeError, ValueError):
            segundos = 1.5
        stage.zonas_zoom.append(ZonaZoomSpec(
            rect=rect,
            factor=max(0.4, min(2.5, factor)),
            segundos=max(0.1, segundos),
        ))

    @classmethod
    def _handle_zona_arena(cls, stage: StageData, obj: Any) -> None:
        """Convierte un objeto `ArenaZone` de Tiled en el rect de arena
        del jefe (AUD-605).

        Sin propiedades: la geometría del objeto ES la arena. Un punto
        (ancho o alto 0) no dice nada y se ignora — una arena degenerada
        aplastaría al jefe contra su propio centro vía `clamp_to_arena`.
        """
        ancho = int(float(getattr(obj, "width", 0) or 0))
        alto = int(float(getattr(obj, "height", 0) or 0))
        if ancho <= 0 or alto <= 0:
            return
        stage.zonas_arena.append(pygame.Rect(
            int(float(getattr(obj, "x", 0) or 0)),
            int(float(getattr(obj, "y", 0) or 0)),
            ancho, alto,
        ))

    @classmethod
    def _canal_de(cls, props: dict[str, Any]) -> str:
        """El canal de dano declarado por un objeto, o el fisico.

        AUD-387 - la propiedad se llama `damage_type` y no `canal` porque ese
        es el nombre que `06_TMX_SPEC.md` lleva documentando desde AUD-310,
        aunque marcado como no implementado. Cumplir la promesa con el nombre
        prometido evita que los mapas que ya la escribieron -confiando en el
        documento- tengan que cambiar.
        """
        from src.framework.combate import dano

        return dano.normalizar(props.get("damage_type"))

    @classmethod
    def _resistencias_de(cls, valor: Any) -> dict[str, float]:
        """Lee `resistencias="veneno:0.5, fuego:2"` de un objeto de Tiled.

        AUD-387 — el formato es una cadena y no una propiedad por canal a
        propósito: Tiled no tiene diccionarios, y una propiedad por canal
        obligaría a tocar el motor cada vez que el catálogo crezca. Así, añadir
        un canal a `data/damage_types.json` basta para poder declararlo.

        Multiplicadores: 0,5 resiste, 2 es débil, 0 es inmune.

        **Lo ilegible se ignora y el resto entra.** Un `fuego:x` o un canal
        inventado no puede costarle el nivel entero al estudiante: se avisa en
        el registro y las parejas buenas se aplican. Es la misma decisión que
        toma este cargador con un clima mal escrito o una estación inexistente,
        y por el mismo motivo — el estudiante necesita ver su nivel para darse
        cuenta del error.
        """
        from src.framework.combate import dano

        if not valor or not isinstance(valor, str):
            return {}
        salida: dict[str, float] = {}
        for trozo in valor.split(","):
            if ":" not in trozo:
                if trozo.strip():
                    logger.warning(
                        "resistencias: «%s» no tiene la forma canal:factor",
                        trozo.strip())
                continue
            canal, _, factor = trozo.partition(":")
            canal = canal.strip().lower()
            if not dano.canal_valido(canal):
                logger.warning(
                    "resistencias: canal «%s» desconocido. Válidos: %s",
                    canal, ", ".join(sorted(dano.CANALES)))
                continue
            try:
                salida[canal] = float(factor.strip())
            except ValueError:
                logger.warning(
                    "resistencias: «%s» no es un número para el canal «%s»",
                    factor.strip(), canal)
        return salida

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
            # AUD-132 — interruptor y puerta cronometrada, desde Tiled.
            abre_con_evento=str(props.get("abre_con", "")),
            cierra_en=cls._safe_float(props.get("cierra_en", 0.0), "cierra_en"),
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

    @classmethod
    def _handle_pendiente(cls, stage: StageData, obj: Any,
                          props: dict[str, Any]) -> None:
        """`Slope` — suelo inclinado (AUD-297).

        El rectángulo del objeto es el **triángulo entero**, no la línea de la
        superficie: se dibuja en Tiled como se dibujaría la roca. La hipotenusa
        va de esquina a esquina, y `sube` dice cuál de las dos está arriba.

        `sube` admite `derecha` (por defecto) o `izquierda`. Una palabra y no un
        booleano porque «sube=false» no dice hacia dónde, y en Tiled se lee la
        propiedad sin el código delante.
        """
        sube = str(props.get("sube", "derecha")).strip().lower()
        if sube not in ("derecha", "izquierda"):
            logger.warning(
                "Slope en (%s, %s): `sube` es %r y sólo vale 'derecha' o "
                "'izquierda'. Se toma 'derecha'.", obj.x, obj.y, sube)
            sube = "derecha"
        stage.pendientes.append(Pendiente(
            rect=cls._rect_de(obj),
            sube_a_la_derecha=sube == "derecha",
        ))

    @classmethod
    def _handle_warp(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        """`WarpZone` — teletransporta dentro del mismo mapa (AUD-287).

        Propiedades:

        * `destino_x`, `destino_y` — **obligatorias**, en píxeles de mundo. Es
          adonde va el centro inferior del jugador, o sea sus pies: dar el punto
          en el suelo es lo natural mirando el mapa en Tiled, y evita el error de
          dejarlo medio hundido.
        * `automatico` — al tocar (por defecto) o pulsando usar.
        * `una_vez`, `key_id`, `enfriamiento`, `mensaje`.

        Sin destino no se carga y se avisa. Un warp sin destino no es un warp a
        medio configurar: es un rectángulo que teletransporta al origen del
        mapa, que es peor que no existir porque parece un fallo del motor.
        """
        if "destino_x" not in props or "destino_y" not in props:
            logger.warning(
                "WarpZone en (%s, %s) sin 'destino_x'/'destino_y': se ignora. "
                "Con destino implícito mandaría al jugador a la esquina del "
                "mapa y parecería un fallo del motor.", obj.x, obj.y,
            )
            return
        stage.warps.append(ZonaDeWarp(
            rect=cls._rect_de(obj),
            destino=pygame.Vector2(float(props["destino_x"]),
                                   float(props["destino_y"])),
            automatico=cls._bool_de(props.get("automatico"), por_defecto=True),
            una_vez=cls._bool_de(props.get("una_vez"), por_defecto=False),
            key_id=str(props.get("key_id", "")),
            enfriamiento=float(props.get("enfriamiento", 0.5)),
            mensaje=str(props.get("mensaje", "")),
        ))

    @classmethod
    def _handle_scroll_forzado(
        cls, stage: StageData, obj: Any, props: dict[str, Any],
    ) -> None:
        """`ScrollZone` — la cámara arranca sola al pisar el rectángulo (AUD-249).

        El rectángulo del objeto es el **disparador**, no la zona de muerte: se
        pisa una vez y a partir de ahí manda la cámara. Quien mata es el borde
        izquierdo de la pantalla, con `margen_de_gracia` píxeles de cortesía
        para que la muerte no ocurra mientras el sprite aún se ve.

        Propiedades, todas opcionales:

        * `velocidad_x` / `velocidad_y` — px/s. Por defecto 40 hacia la derecha.
        * `margen_de_gracia` — px que se puede rebasar el borde. Por defecto 24.
        * `parar_en_x` — la cámara se detiene ahí. Sin ella, hasta el final.
        """
        from src.framework.stage.level_mechanics import ScrollForzado

        def f(clave: str, defecto: float) -> float:
            return cls._safe_float(props.get(clave, defecto), f"ScrollZone.{clave}")

        parar = props.get("parar_en_x")
        stage.scroll_forzados.append(ScrollForzado(
            velocidad=pygame.Vector2(f("velocidad_x", 40.0), f("velocidad_y", 0.0)),
            margen_de_gracia=f("margen_de_gracia", 24.0),
            parar_en_x=(
                cls._safe_float(parar, "ScrollZone.parar_en_x")
                if parar is not None else None
            ),
            disparador=cls._rect_de(obj),
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

    # ── F5.3–F5.6: componentes ECS desde el TMX ────────────────

    @classmethod
    def _handle_componente(
        cls, stage: StageData, obj: Any, props: dict[str, Any], obj_type: str,
    ) -> None:
        """Convierte un objeto de Tiled en un componente ECS.

        Una sola función para las once mecánicas nuevas, y no once métodos:
        todas hacen lo mismo —leer un rectángulo, leer unas propiedades,
        construir un `dataclass`— y once copias de eso serían once sitios donde
        olvidar el mismo `_safe_float`.

        Los nombres de las propiedades son los que un estudiante escribiría en
        Tiled sin consultar nada: `fuerza_x`, `velocidad`, `alcance`. Se
        eligieron antes que los del código.
        """
        from src.framework.ecs.components import (
            Acosador,
            Alerta,
            BloqueRitmico,
            ConoDeVision,
            Liana,
            PlataformaHundible,
            PlataformaMovil,
            Resorte,
            Solido,
            Tirolesa,
            Transform,
            ZonaDeAgua,
            ZonaDeFriccion,
            ZonaDeViento,
            ZonaLetalTemporizada,
        )

        rect = cls._rect_de(obj)

        def f(clave: str, defecto: float) -> float:
            return cls._safe_float(props.get(clave, defecto), f"{obj_type}.{clave}")

        def transform() -> Transform:
            """Las mecánicas que se mueven necesitan `Transform`; las zonas no.

            Una zona es un rectángulo quieto y le basta con llevarlo dentro. Una
            plataforma se mueve, así que su posición tiene que estar donde los
            sistemas de movimiento y arrastre saben buscarla.
            """
            return Transform(
                posicion=pygame.Vector2(rect.topleft), rect=rect.copy(),
            )

        # Cada entrada es **la lista de componentes de UNA entidad**. Uniforme
        # para las once mecánicas: la escena hace `mundo.crear(*grupo)` y no
        # tiene que saber cuál es cuál.
        grupo: list[object]

        if obj_type == "Spring":
            # AUD-131 — resorte. El rectángulo es la zona de contacto, así que
            # un resorte dibujado ancho rebota en todo su ancho: es lo que el
            # diseñador ve en Tiled y por tanto lo que espera.
            grupo = [Resorte(
                rect=rect,
                impulso=f("impulso", -520.0),
                rearme=f("rearme", 0.15),
            )]

        elif obj_type == "WindZone":
            grupo = [ZonaDeViento(
                rect=rect,
                fuerza=pygame.Vector2(f("fuerza_x", 0.0), f("fuerza_y", 0.0)),
                periodo=f("periodo", 0.0),
            )]

        elif obj_type in ("FrictionZone", "Conveyor"):
            # `Conveyor` es un alias con otro valor por defecto: una cinta sin
            # arrastre no es una cinta, y obligar al estudiante a recordarlo
            # sería una errata esperando a ocurrir.
            arrastre_defecto = 60.0 if obj_type == "Conveyor" else 0.0
            grupo = [ZonaDeFriccion(
                rect=rect,
                multiplicador=f("multiplicador", 1.0),
                arrastre=f("arrastre", arrastre_defecto),
                # AUD-490 — GAP-039: nombre de `physics.perfil.MATERIALES`.
                # "roca" (sin restitución) es el valor de siempre a
                # propósito: una zona sin declarar `material` no cambia
                # ningún mapa ya entregado.
                material=str(props.get("material", "roca")),
                # AUD-522 — resbalar de verdad (hielo, musgo mojado) en vez
                # de sólo frenar. 0 por defecto: ningún mapa entregado
                # cambia sin declararlo.
                inercia=f("inercia", 0.0),
            )]

        elif obj_type in ("LaserZone", "ShockwaveZone"):
            grupo = [ZonaLetalTemporizada(
                rect=rect,
                dano=f("dano", 99.0),
                encendido=f("encendido", 1.0),
                apagado=f("apagado", 1.0),
                desfase=f("desfase", 0.0),
            )]

        elif obj_type == "WaterZone":
            grupo = [ZonaDeAgua(
                rect=rect,
                corriente=pygame.Vector2(f("corriente_x", 0.0), f("corriente_y", 0.0)),
            )]

        elif obj_type == "MovingPlatform":
            # El destino se declara como desplazamiento y no en coordenadas
            # absolutas: mover la plataforma en Tiled no debería obligar a
            # recalcular su destino a mano, y con absolutas hay que hacerlo
            # siempre.
            grupo = [
                transform(),
                PlataformaMovil(
                    origen=pygame.Vector2(rect.topleft),
                    destino=pygame.Vector2(
                        rect.x + f("destino_dx", 0.0), rect.y + f("destino_dy", 0.0),
                    ),
                    velocidad=f("velocidad", 40.0),
                    espera=f("espera", 0.5),
                ),
                Solido(atravesable_desde_abajo=cls._bool_de(
                    props.get("atravesable"), por_defecto=False)),
            ]

        elif obj_type == "RhythmBlock":
            grupo = [
                transform(),
                BloqueRitmico(
                    # `visible` y `oculto` a secas serían tentadores, pero
                    # **`visible` es un nombre reservado en Tiled**: pytmx
                    # rechaza el mapa entero con «Reserved names and duplicate
                    # names are not allowed». Lo descubrió el escenario de
                    # referencia al cargarlo por primera vez.
                    visible_seg=f("visible_seg", 1.0),
                    oculto_seg=f("oculto_seg", 1.0),
                    desfase=f("desfase", 0.0),
                    # AUD-137: con patrón manda la música y los segundos
                    # dejan de contar. `"x.x."` = sí, no, sí, no.
                    patron=str(props.get("patron", "") or ""),
                ),
            ]

        elif obj_type == "SinkingPlatform":
            grupo = [
                transform(),
                PlataformaHundible(
                    retraso=f("retraso", 0.4),
                    velocidad_caida=f("velocidad_caida", 90.0),
                    reaparece_en=f("reaparece_en", 3.0),
                    y_original=float(rect.y),
                ),
                Solido(atravesable_desde_abajo=True),
            ]

        elif obj_type == "Guard":
            grupo = [
                transform(),
                ConoDeVision(
                    mira=pygame.Vector2(f("mira_x", 1.0), f("mira_y", 0.0)),
                    alcance=f("alcance", 160.0),
                    semiangulo=f("semiangulo", 30.0),
                    barrido=f("barrido", 0.0),
                    velocidad_barrido=f("velocidad_barrido", 45.0),
                ),
                Alerta(),
            ]

        elif obj_type == "Stalker":
            grupo = [
                transform(),
                Acosador(
                    velocidad=f("velocidad", 55.0),
                    distancia_retirada=f("distancia_retirada", 480.0),
                    reaparicion=f("reaparicion", 6.0),
                ),
            ]

        elif obj_type == "Vine":
            grupo = [Liana(
                rect=rect,
                ancho_de_agarre=int(f("ancho_de_agarre", 10.0)),
                velocidad=f("velocidad", 70.0),
            )]

        elif obj_type == "Zipline":
            # El destino va en desplazamiento, igual que en `MovingPlatform`:
            # mover el cable en Tiled no debería obligar a recalcular su
            # extremo a mano.
            grupo = [Tirolesa(
                origen=pygame.Vector2(rect.topleft),
                destino=pygame.Vector2(
                    rect.x + f("destino_dx", 96.0),
                    rect.y + f("destino_dy", 64.0),
                ),
                velocidad=f("velocidad", 190.0),
                radio_de_enganche=f("radio_de_enganche", 14.0),
                solo_de_bajada=cls._bool_de(
                    props.get("solo_de_bajada"), por_defecto=True),
            )]

        else:  # pragma: no cover - `_TIPOS_DE_COMPONENTE` y esto van juntos
            return

        stage.componentes.append(grupo)

    @classmethod
    def _handle_hazard_zone(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        if obj.width == 0 or obj.height == 0:
            return
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        damage = cls._safe_float(props.get("damage", 0.25), "hazard damage")
        # AUD-135 — la inundación. `sube` en píxeles por segundo; `sube_hasta`
        # es una `y` del mapa, así que el diseñador pone el tope donde ve el
        # techo en Tiled y no tiene que calcular alturas.
        sube = cls._safe_float(props.get("sube", 0.0), "hazard sube")
        tope_bruto = props.get("sube_hasta")
        sube_hasta = (
            cls._safe_float(tope_bruto, "hazard sube_hasta")
            if tope_bruto not in (None, "") else None
        )
        stage.hazard_zones.append(HazardZone(
            rect=rect,
            damage=damage,
            sube=max(0.0, sube),
            sube_hasta=sube_hasta,
            arranca_con=str(props.get("arranca_con", "") or ""),
            # AUD-387 - cierra la promesa que 06_TMX_SPEC.md llevaba rota desde
            # AUD-310. Un canal desconocido cae al fisico con un aviso, en vez
            # de impedir la carga: el estudiante necesita ver su nivel.
            damage_type=cls._canal_de(props),
            # Tiled escribe los booleanos como `"true"`/`"false"`, y la cadena
            # `"false"` es verdadera en Python: leerla sin convertir haría que
            # `avisar=false` no apagara nada.
            avisar=str(props.get("avisar", "true")).lower() != "false",
        ))

    @classmethod
    def _handle_bloque(cls, stage: StageData, obj: Any, props: dict[str, Any],
                       *, empujable: bool) -> None:
        """AUD-140 — `PushBlock` y `BreakableBlock`.

        Sin tamaño se ignora con aviso: un bloque de 0×0 sería un sólido
        invisible de área nula, que no estorba a nadie y no se ve. El
        estudiante creería haberlo puesto.
        """
        if obj.width <= 0 or obj.height <= 0:
            logger.warning(
                "bloque sin tamaño en (%s, %s): se ignora", obj.x, obj.y)
            return
        rect = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
        if empujable:
            stage.empujables.append(BloqueEmpujable(
                rect=rect,
                velocidad=max(1.0, cls._safe_float(
                    props.get("velocidad", 45.0), "velocidad del bloque")),
                con_gravedad=cls._bool_de(props.get("con_gravedad"),
                                          por_defecto=True),
            ))
        else:
            stage.destructibles.append(BloqueDestructible(
                rect=rect,
                golpes=max(1, cls._safe_int(props.get("golpes", 1), "golpes")),
                evento_al_romper=str(props.get("evento_al_romper", "") or ""),
            ))

    @classmethod
    def _handle_objetivo(cls, stage: StageData, obj: Any, props: dict[str, Any],
                         nombre: str = "") -> None:
        """AUD-400 — `Objective` en Tiled. Cierra GAP-047.

        Es un objeto **punto**: no tiene geometría porque un objetivo no ocurre
        en un sitio, ocurre cuando pasa algo. Se pone donde el diseñador quiera
        verlo al abrir el mapa.

        La conversión vive en `objetivos.py` y no aquí para que se pueda probar
        sin cargar un TMX; esto sólo la llama y guarda el resultado. Un
        objetivo mal declarado se ignora con aviso —lo decide
        `objetivo_desde_tiled`— en vez de romper el nivel, que es el trato que
        el resto del cargador da al dato incompleto.
        """
        from src.framework.stage.objetivos import objetivo_desde_tiled

        objetivo = objetivo_desde_tiled(props, nombre)
        if objetivo is not None:
            stage.objetivos.append(objetivo)

    @classmethod
    def _handle_cutscene(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        """AUD-136 — `Cutscene` en Tiled.

        Con rectángulo, se dispara al entrar el jugador; como punto, al empezar
        el escenario. Sin `guion` se ignora con un aviso: una escena vacía no
        haría nada y quitaría el mando durante un instante, que es peor que no
        estar.
        """
        guion = str(props.get("guion", "") or props.get("script", "") or "")
        if not guion.strip():
            logger.warning(
                "Cutscene sin propiedad 'guion' en (%s, %s): se ignora",
                getattr(obj, "x", "?"), getattr(obj, "y", "?"),
            )
            return
        stage.escenas.append(EscenaGuionizada(
            rect=pygame.Rect(obj.x, obj.y, obj.width, obj.height),
            guion=guion,
            bloquea=cls._bool_de(props.get("bloquea"), por_defecto=True),
            saltable=cls._bool_de(props.get("saltable"), por_defecto=True),
            una_vez=cls._bool_de(props.get("una_vez"), por_defecto=True),
            arranca_con=str(props.get("arranca_con", "") or ""),
        ))

    @classmethod
    def _handle_camera_lock(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        if obj.width == 0 or obj.height == 0:
            return
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        lock_x = props.get("lock_x", False) in (True, "true", "True", 1, "1")
        lock_y = props.get("lock_y", False) in (True, "true", "True", 1, "1")
        stage.camera_locks.append(CameraLock(rect=rect, lock_x=lock_x, lock_y=lock_y))
