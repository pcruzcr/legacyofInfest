"""Módulo para gestionar datos de guardado del juego.

Proporciona el modelo SaveData con validación, migración
y serialización/deserialización en JSON.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar

import orjson
from pydantic import BaseModel, Field, field_validator, model_validator

SAVE_VERSION = 6
MAX_SLOTS = 5

#: Primera versión que guarda el inventario dentro de la partida (AUD-292).
#:
#: AUD-438 — hace falta el número, no un `>= SAVE_VERSION`. Desde aquí hacia
#: arriba, un inventario vacío significa **vacío** y se aplica tal cual; por
#: debajo se conserva el que hubiera, porque esas partidas no pudieron
#: guardarlo. Sin esta distinción, «vacío porque es antiguo» y «vacío porque
#: acaba de empezar» se escriben igual, y una ranura nueva heredaba la cartera
#: de la anterior.
VERSION_CON_INVENTARIO = 3

#: Primera versión que guarda los logros dentro de la partida (AUD-438).
VERSION_CON_LOGROS = 4


class SaveData(BaseModel):
    """Modelo de datos para una partida guardada.

    Incluye validación de campos, migración automática entre
    versiones de guardado y métodos de serialización.
    """
    slot_id: int = 0
    timestamp: str = ""
    version: int = SAVE_VERSION

    stage_id: str = ""
    stage_index: int = 0
    checkpoint_x: float = 0.0
    checkpoint_y: float = 0.0

    health: float = 5.0
    max_health: float = 5.0

    zone_flags: dict[str, bool] = Field(default_factory=dict)
    completed_stages: list[str] = Field(default_factory=list)
    #: AUD-267 — experiencia acumulada. `ExperienceSystem` la calculaba desde
    #: AUD-249 y no había dónde guardarla: cerrar el juego la borraba, así que
    #: la moneda con la que se paga el árbol de habilidades no llegaba viva a
    #: la sesión siguiente. Con reserva 0, las partidas anteriores se cargan
    #: sin tocar nada.
    exp_total: int = 0
    #: AUD-292 — la partida se lleva **todo** lo que el jugador acumuló.
    #:
    #: Hasta hoy estaba repartido en tres sitios que no se hablaban: la
    #: puntuación en `data/score.json`, el inventario —y con él las monedas—
    #: en `data/inventory.json`, y sólo la experiencia dentro del slot. Los tres
    #: primeros eran **globales**: cargar la partida de otro slot dejaba el
    #: dinero y la ropa del anterior, y empezar una partida nueva no vaciaba
    #: nada. Dos personas turnándose en el mismo equipo compartían cartera.
    #:
    #: Con esto, un slot es una partida entera. Los ficheros globales siguen
    #: existiendo para quien juega sin identificarse y sin guardar — desde
    #: AUD-337 ya viven en el directorio del usuario, no en `data/`.
    score: int = 0
    inventory_items: dict[str, int] = Field(default_factory=dict)
    inventory_equipped: dict[str, str] = Field(default_factory=dict)
    #: Los tres números de `ExperienceSystem`, no sólo el total.
    #:
    #: `exp_total` sola no basta y su propio módulo lo dice: los puntos ya
    #: **gastados** no se deducen de la experiencia. Restaurando sólo el total,
    #: cargar una partida le devolvería al jugador todos los puntos que ya se
    #: había gastado en el árbol — y con ellos podría comprarlo dos veces.
    exp_estado: dict[str, int] = Field(default_factory=dict)
    #: AUD-293 — los rangos comprados del árbol de habilidades.
    arbol: dict[str, int] = Field(default_factory=dict)
    #: AUD-442 — quién es esta partida, no sólo por dónde va.
    #:
    #: Sin estos tres campos la pantalla de selección enseña cinco filas
    #: indistinguibles y elegir partida es elegir por marca de tiempo.
    #:
    #: No suben `SAVE_VERSION` a propósito: son aditivos y con valores por
    #: defecto sanos, así que una partida anterior se lee sin nombre y la
    #: pantalla la muestra como «Partida N». Ningún comportamiento depende de
    #: la versión aquí, y un escalón de migración que no hace nada sólo añade
    #: ruido donde luego hay que leer para entender por qué una partida vieja
    #: no carga.
    profile_name: str = ""
    #: El personaje elegido al crear la partida. Hoy sólo hay uno; el campo
    #: existe porque la elección es parte de crear el perfil y añadirlo
    #: después obligaría a migrar todas las partidas.
    character: str = "paburu"
    #: Segundos jugados, acumulados. Lo suma `SaveManager.anotar_tiempo_jugado`
    #: al guardar; no se deduce de la marca de tiempo del fichero, que contaría
    #: también las horas con el juego cerrado.
    play_time: float = 0.0
    #: AUD-438 — con qué versión se escribió esta partida **antes** de migrar.
    #:
    #: Hace falta porque `migrate()` reescribe `version` a la última: para
    #: cuando alguien la lee, toda partida dice ser de la versión actual y no
    #: hay forma de saber si su inventario vacío es «no tenía» o «no pudo
    #: guardarlo». Ese olvido convertía la indulgencia de AUD-292 en letra
    #: muerta y le vaciaba la cartera a quien cargara una partida de la
    #: versión 2 — lo cazó `test_una_partida_vieja_no_vacia_la_cartera`.
    #:
    #: Una partida nueva nace con la versión actual, que es lo correcto: sus
    #: campos vacíos significan vacío.
    version_original: int = SAVE_VERSION
    #: AUD-518 — qué variante de 4-1 le tocó a esta partida (cementerio,
    #: y más adelante acuático/aéreo). Vacío = todavía no se sorteó.
    #:
    #: Aditivo, sin subir `SAVE_VERSION` — mismo criterio que
    #: `character`/`profile_name`: valor por defecto sano, así que una
    #: partida anterior a este campo se lee con `""` y vuelve a sortear la
    #: primera vez que llega a la Fase 4, que es exactamente el
    #: comportamiento correcto para una partida vieja (no había nada que
    #: preservar).
    stage4_1_variante: str = ""
    #: ZONA 4 — semilla con la que se sorteó la variante (§6, §14, §18).
    #:
    #: Aditivo sin subir `SAVE_VERSION`: ``None`` = partida anterior a Zona 4
    #: sin semilla que preservar — se sortea de nuevo, igual que con
    #: ``stage4_1_variante`` vacío. Con valor, permite reproducir exactamente
    #: la misma variante: ``seed = X → misma variante`` (§6).
    zone4_semilla: int | None = None
    #: ZONA 4 — identificador de layout de la variante procedural 4_1C (§14).
    #:
    #: Para 4_1C, la variante ``aereo`` no basta: el propio nivel cambia de
    #: plantilla/ruta en cada entrada. ``zone4_layout_id`` conserva cuál se
    #: generó (``"a"``/``"b"``/``"c"`` para plantillas congeladas, o hash de
    #: semilla para generación procedural). Vacío = aún no se generó.
    zone4_layout_id: str = ""
    #: ZONA 4 — alias de compatibilidad: algunas herramientas leen
    #: ``stage4_1c_plantilla``; se mantiene sincronizado con ``zone4_layout_id``
    #: cuando la variante es ``aereo``.
    stage4_1c_plantilla: str = ""
    #: ZONA 4 — semilla específica de la generación procedural 4_1C (§13-§14).
    #:
    #: Si es ``None``, la plantilla se sorteó con el azar del proceso; con
    #: valor, la ruta es reproducible vía ``trazado.generar_ruta(semilla)``.
    stage4_1c_semilla: int | None = None
    #: AUD-438 — los logros, dentro de la partida y no en un fichero global.
    #:
    #: `AchievementSystem` persistía en `achievements.json`, uno por
    #: instalación: lo desbloqueado jugando una ranura aparecía desbloqueado en
    #: todas. Un logro es progreso, y el progreso pertenece al perfil.
    #:
    #: Se guarda el progreso completo —no sólo qué está desbloqueado— porque un
    #: logro de contador («mata 50 enemigos») lleva su cuenta a medias, y
    #: perderla al cargar sería peor que no guardarlo.
    logros: dict[str, dict[str, Any]] = Field(default_factory=dict)
    #: B1 — NG+ (Nueva Partida Plus) — cuántas veces se ha completado el juego.
    #: Cada NG+ sube la dificultad (ver difficulty.py). Se incrementa al ver
    #: los créditos tras `hub_backtracking` o `boss_paburu`.
    ng_plus: int = Field(default=0, ge=0)
    #: B3 — Item Completion — por mapa, qué ítems se han recogido (persistencia per-map).
    #: La clave es stage_id (MAP_ID), el valor es sorted(list[str]) de ITEM keys
    #: "MAP_ID:TMX_ID:ITEM_ID". Runtime se usa como set para O(1) y anti-duplicado,
    #: serializado como lista ordenada para JSON determinista.
    map_item_collected: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("health", "max_health")
    @classmethod
    def _round_health(cls, v: float) -> float:
        return round(v, 1)

    #: Tope del nombre de partida, en caracteres — AUD-442.
    #:
    #: La fila de la pantalla de selección tiene un ancho, y el fichero tiene
    #: un lector humano. Sin tope, un nombre pegado desde el portapapeles
    #: desborda la fila y empuja la marca de tiempo fuera de la pantalla.
    LARGO_MAXIMO_DEL_NOMBRE: ClassVar[int] = 24

    @field_validator("profile_name")
    @classmethod
    def _limpiar_nombre(cls, v: str) -> str:
        return str(v).strip()[: cls.LARGO_MAXIMO_DEL_NOMBRE]

    @field_validator("map_item_collected", mode="before")
    @classmethod
    def _normalize_map_item_collected(cls, v: Any) -> Any:
        """Normaliza map_item_collected a dict[str, list[str]] ordenado.

        Acepta dict[str, list|set|None] y rechaza tipos corruptos con {}.
        Cada lista se deduplica y ordena para JSON determinista (B3 §46).
        """
        if v is None:
            return {}
        if not isinstance(v, dict):
            return {}
        out: dict[str, list[str]] = {}
        for k, val in v.items():
            if not isinstance(k, str):
                continue
            if val is None:
                out[k] = []
                continue
            if isinstance(val, (list, set, tuple)):
                try:
                    # Filtra no-string y deduplica
                    lst = [str(x) for x in val if isinstance(x, (str, int, float))]
                    # Para int/float convertidos, mantener como string
                    uniq = sorted(set(lst))
                    out[k] = uniq
                except Exception:
                    out[k] = []
            else:
                out[k] = []
        return out

    @field_validator("checkpoint_x", "checkpoint_y")
    @classmethod
    def _round_pos(cls, v: float) -> float:
        return round(v, 1)

    @model_validator(mode="before")
    @classmethod
    def _migrate_validator(cls, data: Any) -> Any:
        """Run schema migration before field validation.

        AUD-031: this used to carry its own copy of the migration ladder,
        duplicating :meth:`migrate`. The two already differed stylistically and
        would have drifted apart the first time a version 3 was added — with
        the validator path and the explicit path silently disagreeing about
        what a migrated save looks like. There is now exactly one ladder.

        Guards against non-dict input: pydantic passes ``model_validate`` an
        arbitrary object, and ``data.get`` on a ``SaveData`` instance raised
        ``AttributeError``.
        """
        if not isinstance(data, dict):
            return data
        return cls.migrate(dict(data))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SaveData:
        """Construye una instancia desde un diccionario **leído de fuera**.

        AUD-438 — aquí, y no en `migrate()`, se anota de qué versión viene la
        partida. La diferencia importa: por el validador pasa **todo**,
        incluida una `SaveData()` construida en código, y ahí el diccionario
        crudo tampoco trae `version` porque es un valor por defecto. Anotando
        el origen dentro de la migración, una partida nueva se marcaba como
        versión 0 y recibía la indulgencia pensada para las antiguas — o sea,
        heredaba el inventario de la ranura anterior, que es el defecto que
        todo esto viene a cerrar.

        Este método es el que se usa al leer de disco (`from_json` delega
        aquí), así que es el único sitio donde «de dónde viene» tiene
        respuesta. Sin `version` se asume antigua y se es indulgente: una
        partida anterior a que existiera el campo no pudo guardar su
        inventario, y vaciárselo sería cobrarle la migración (AUD-292).
        """
        crudo = dict(data)
        crudo.setdefault("version_original", crudo.get("version", 0))
        return cls.model_validate(crudo)

    # ── B3 helpers ──────────────────────────────────────────────────
    def _collected_set(self, map_id: str) -> set[str]:
        """Set runtime de ítems recogidos en map_id (vacío si no existe)."""
        lst = self.map_item_collected.get(map_id) or []
        return set(lst)

    def is_item_collected(self, map_id: str, item_key: str) -> bool:
        return item_key in self._collected_set(map_id)

    def mark_item_collected(self, map_id: str, item_key: str) -> bool:
        """Añade item_key a map_id. Devuelve True si era nuevo.

        Mantiene lista ordenada para JSON determinista.
        """
        if not map_id or not item_key:
            return False
        lst = self.map_item_collected.get(map_id)
        if lst is None:
            self.map_item_collected[map_id] = [item_key]
            return True
        # Normalizar a set para deduplicar
        s = set(lst)
        if item_key in s:
            return False
        s.add(item_key)
        self.map_item_collected[map_id] = sorted(s)
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convierte la instancia a diccionario, asignando timestamp si está vacío.

        El timestamp generado es UTC con zona horaria, para que ``newest_slot()``
        pueda ordenar ranuras comparando cadenas sin equivocarse en los cambios
        de horario de verano (AUD-014).
        """
        data = self.model_dump()
        if not data["timestamp"]:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
        # B3 — asegurar listas ordenadas (determinismo JSON)
        mic = data.get("map_item_collected")
        if isinstance(mic, dict):
            norm: dict[str, list[str]] = {}
            for k, v in mic.items():
                if isinstance(v, (list, set, tuple)):
                    norm[k] = sorted(set(str(x) for x in v))
                else:
                    norm[k] = []
            data["map_item_collected"] = norm
        return data

    @staticmethod
    def migrate(data: dict[str, Any]) -> dict[str, Any]:
        """Migra un diccionario de datos a la versión más reciente.

        Única fuente de verdad de la migración de esquema (AUD-031): el
        validador ``_migrate_validator`` delega aquí en lugar de repetir la
        escalera de versiones.

        Para añadir la versión N: añade un bloque ``if ver < N`` que rellene
        los campos nuevos y fije ``data["version"] = N``.
        """
        ver = data.get("version", 0)
        if ver < 1:
            data.setdefault("zone_flags", {})
            data.setdefault("exp_total", 0)
            data["version"] = 1
        if ver < 2:
            data.setdefault("completed_stages", [])
            data["version"] = 2
        if ver < 3:
            # AUD-292. Con reserva vacía, una partida de la versión 2 se carga
            # y **conserva** el inventario global que hubiera: la primera
            # grabación la vuelca dentro del slot y a partir de ahí viaja con
            # ella. Migrar copiando el fichero global aquí sería peor — daría a
            # los cinco slots la misma cartera.
            data.setdefault("score", 0)
            data.setdefault("inventory_items", {})
            data.setdefault("inventory_equipped", {})
            data.setdefault("exp_estado", {})
            data.setdefault("arbol", {})
            data["version"] = 3
        if ver < 4:
            # AUD-438. Vacío a propósito, y con la misma lógica que AUD-292
            # aplicó al inventario: una partida anterior a la versión 4 no
            # pudo guardar sus logros, así que al cargarla se **conservan**
            # los que hubiera en el fichero global. La primera grabación los
            # vuelca dentro de la partida y a partir de ahí viajan con ella.
            # Copiarlos aquí desde el fichero global sería peor: les daría a
            # las cinco ranuras el mismo historial.
            data.setdefault("logros", {})
            data["version"] = 4
        if ver < 5:
            data.setdefault("ng_plus", 0)
            data["version"] = 5
        if ver < 6:
            # B3 — per-map item completion. Partida vieja sin campo → {} → 0% correcto.
            # Si viene como set (runtime previo) se normalizará en validator.
            data.setdefault("map_item_collected", {})
            data["version"] = 6
        return data

    def to_json(self) -> bytes:
        """Serializa los datos a JSON binario, **firmado** (AUD-295)."""
        from src.engine.core.integridad import volcar

        return volcar(self.to_dict(), indentado=False)

    @classmethod
    def from_json(cls, raw: bytes | str) -> SaveData:
        """Deserializa datos desde JSON (bytes o string), comprobando la firma.

        AUD-295 — una firma que no cuadra lanza `ValueError`, igual que un JSON
        roto, y por el mismo motivo: quien llama ya sabe qué hacer con una
        partida que no se puede leer —`SaveManager.load` la registra y devuelve
        `None`— y no sabría qué hacer con datos a medias.

        Los ficheros escritos antes de AUD-295 no llevan firma y se aceptan:
        rechazarlos sería borrarle la partida a todo el que actualice.
        """
        from src.engine.core.integridad import CAMPO_FIRMA, verificar

        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        data = orjson.loads(raw)
        if not verificar(data):
            raise ValueError(
                "la firma de la partida no cuadra: se escribió a medias o "
                "alguien la editó",
            )
        data.pop(CAMPO_FIRMA, None)
        return cls.from_dict(data)
