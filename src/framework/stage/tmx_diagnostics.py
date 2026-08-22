"""
Module: tmx_diagnostics
System: framework.stage
Academic Unit: Unit IV (Game Architecture)

Diagnóstico de mapas TMX: convierte un error de tecleo en un mensaje que
enseña, en lugar de en un enemigo que no aparece.

Por qué existe (AUD-055)
------------------------
`StageLoader._process_objects` era una cadena de `if/elif` **sin `else`**::

    if obj_type == "PlayerSpawn":      ...
    elif obj_type == "MessageTrigger": ...
    elif obj_type in cls._entity_registry: ...
    elif obj_type == "Checkpoint":     ...
    # ...y si no coincide con nada, no pasa nada.

Un objeto cuyo `type` estuviera mal escrito —`Waker`, `walker`, `FlyingBrid`—
se ignoraba **en silencio**. El estudiante coloca el enemigo en Tiled, guarda,
ejecuta el juego y el enemigo no está. Sin error, sin aviso, sin nada en el
log. No hay forma de distinguir «escribí mal el tipo» de «el enemigo se creó
pero no lo veo» o de «el engine está roto».

Ese es el peor fallo posible en una herramienta pensada para aprender: no
enseña nada y consume el tiempo que debería ir al diseño del nivel. Es también
el fallo más barato de arreglar bien, porque en el momento de fallar sabemos
exactamente qué escribió el estudiante y qué podría haber querido escribir.

Principio: fallar pronto, fallar entero, fallar sugiriendo
-----------------------------------------------------------
* **Pronto** — al cargar, no cuando el jugador llega a esa zona del mapa.
* **Entero** — se recogen *todos* los problemas del mapa y se informan juntos.
  Reportar el primero y abortar obliga a ejecutar el juego seis veces para
  encontrar seis erratas.
* **Sugiriendo** — «Waker desconocido» es la mitad del trabajo; «¿quisiste
  decir Walker?» es la otra mitad.
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field

#: Tipos que el cargador entiende y que no son entidades del bestiario.
#: Se declaran aquí, y no dispersos por la cadena de condiciones, para que el
#: diagnóstico y el validador de CI puedan leerlos sin duplicarlos.
BUILTIN_OBJECT_TYPES: tuple[str, ...] = (
    "PlayerSpawn",
    "Checkpoint",
    "NextTrigger",
    "MessageTrigger",
    "MessageTrigger_Once",
    "HazardZone",
    "DeathPit",
    "CameraLock",
    "Waypoint",
    "Light",
    #: AUD-598 — GAP-072.4: brillo ambiental por tramo (el descenso del
    #: blueprint §46 del 4-1b).
    "AmbientLightZone",
    #: AUD-600 — GAP-072.2: música por sección (el silencio del abismo en
    #: el 4-1b, blueprint §20/35).
    "MusicZone",
    #: AUD-136 (D3) — una escena narrativa con su guion en una propiedad.
    "Cutscene",
    #: AUD-140 — bloques que el jugador mueve o rompe.
    "PushBlock",
    "BreakableBlock",
    # F4.1 — objetos con los que el jugador interactúa.
    #
    # `Key` es un alias de `Pickup` y `LockedDoor` de `Door`: el motor los
    # trata igual, pero poder escribir en Tiled lo que la cosa *es* hace el
    # mapa legible sin abrir el código. Los alias cuestan una línea aquí y
    # ahorran una explicación en clase.
    "Pickup",
    "Key",
    "Door",
    "LockedDoor",
    "Cage",
    "Chest",
    "EventTrigger",
    #: AUD-400 — un objetivo del nivel, declarado en el mapa (GAP-047). Es un
    #: punto sin geometría: un objetivo no ocurre en un sitio, ocurre cuando
    #: pasa algo.
    "Objective",
    # F5.3/F5.4/F5.6 — las mecánicas de los dossiers del Top 200, puestas al
    # alcance de Tiled. Cada una nace de niveles concretos, y el nombre se
    # eligió por lo que la cosa **es** y no por cómo está implementada: un
    # estudiante que quiere una cinta transportadora busca «Conveyor», no
    # «ZonaDeFriccionConArrastre».
    "WindZone",        # Mega Man 2 (Air Man), Celeste (Golden Ridge)
    "FrictionZone",    # Hollow Knight (la miel de The Hive), hielo
    "Conveyor",        # Mega Man 2 (Metal Man)
    "LaserZone",       # MGS, Mega Man 2 (Quick Man), Celeste (Mirror Temple)
    "ShockwaveZone",   # Inside (las ondas de choque de la mina)
    "WaterZone",       # Sonic (Labyrinth), SMB3 (Water Land), Inside
    "MovingPlatform",  # Mega Man 2, Sonic, Donkey Kong Country
    "RhythmBlock",     # Mega Man 2 (Wily 1), Celeste (bloques de cassette)
    "SinkingPlatform", "Spring",  # Cuphead (Perilous Piers)
    "Guard",           # MGS (Tank Hangar): cono de visión y alerta
    "Stalker",         # RE3 (Nemesis), Celeste (el conserje), Metroid Dread
    # AUD-249 — SMB3 (Airship), Cuphead, Ori, Terraria (Wall of Flesh).
    #
    # `ScrollForzado` existía entera, probada, y **sin forma de encenderla
    # desde Tiled**: `StageScene` la construía y no la tocaba nunca. Un
    # arquetipo de nivel completo —la persecución— estaba fuera del alcance de
    # cualquier alumno que no escribiera Python (`GAP-032`).
    "ScrollZone",
    # AUD-287 — teletransporte **dentro** del mismo mapa. `NextTrigger` cambia
    # de escenario y `Door` abre un paso; mover al jugador de una punta del mapa
    # a la otra no se podía declarar de ninguna forma, así que un mapa grande no
    # tenía manera de conectar sus extremos.
    "WarpZone",        # Zelda (cuevas), Metroid (ascensores), Hollow Knight
    # AUD-297 — suelo inclinado. Hasta aquí, una cuesta había que fingirla
    # apilando bloques escalonados, y eso no es una cuesta: es una escalera que
    # frena al jugador en cada peldaño.
    "Slope",           # Sonic, DKC, Celeste
    # F5.14 — de escalada no había **nada**: ni `Ladder`, ni `Rope`, ni `Climb`,
    # ni un estado que suspendiera la gravedad. Y no se podía improvisar:
    # apilar `Solid` estrechos para simular una cuerda deja al jugador al lado
    # de la columna, no dentro, y para subir tiene que saltar — que es justo lo
    # que una liana existe para evitar.
    "Vine",            # DKC (Ropey Rampage), Zelda, Spelunky, Castlevania
    "Zipline",         # DKC, Rayman, Ori
    # AUD-259 — `17_BOSS_SPEC.md` §8.2 exige un `BossSpawn` en todo mapa de
    # jefe desde que se escribió, y el cargador no lo conocía: quien siguiera
    # su propia especificación recibía «tipo desconocido». Declara **dónde
    # entra** el jefe que nombra su propiedad `boss`, resuelto por el registro
    # de entidades.
    "BossSpawn",
)

#: Tipos válidos en la capa `Collision`, que se procesa aparte. `Platform`
#: convierte el rectángulo en plataforma atravesable desde abajo; cualquier
#: otro valor, incluida la ausencia de tipo, lo deja como suelo sólido.
#:
#: Se declaran por separado de los de `Objects` porque son dos vocabularios
#: distintos, y confundirlos produce errores desconcertantes: poner `Platform`
#: en `Objects` no crea ninguna plataforma, y poner `Walker` en `Collision`
#: crea un bloque de suelo con forma de enemigo.
COLLISION_OBJECT_TYPES: tuple[str, ...] = ("Platform", "Solid")

#: Cuántas sugerencias ofrecer como máximo. Más de tres deja de ser una pista
#: y pasa a ser una lista que hay que leer entera.
_MAX_SUGGESTIONS = 3

#: Umbral de parecido de `difflib`. 0.6 es su valor por defecto y acierta con
#: erratas de una o dos letras sin proponer cosas sin relación.
_SIMILARITY_CUTOFF = 0.6


@dataclass
class TmxObjectProblem:
    """Un objeto del mapa que el cargador no supo interpretar."""

    object_id: int
    object_name: str
    object_type: str
    x: float
    y: float
    suggestions: tuple[str, ...] = ()
    #: Motivo legible. Se separa de las sugerencias porque «sin tipo» y «tipo
    #: desconocido» son errores distintos con arreglos distintos.
    reason: str = "tipo desconocido"

    def describe(self) -> str:
        where = f"en ({int(self.x)}, {int(self.y)})"
        label = f"«{self.object_name}» " if self.object_name else ""
        head = (
            f"  · objeto id={self.object_id} {label}{where}: {self.reason}"
            f" — type=«{self.object_type}»"
            if self.object_type
            else f"  · objeto id={self.object_id} {label}{where}: {self.reason}"
        )
        if not self.suggestions:
            return head
        if len(self.suggestions) == 1:
            return f"{head}\n      ¿quisiste decir «{self.suggestions[0]}»?"
        opciones = ", ".join(f"«{s}»" for s in self.suggestions)
        return f"{head}\n      ¿quisiste decir alguno de estos? {opciones}"


@dataclass
class TmxReport:
    """Todo lo que está mal en un mapa, junto."""

    tmx_path: str = ""
    problems: list[TmxObjectProblem] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def add(self, problem: TmxObjectProblem) -> None:
        self.problems.append(problem)

    def format(self, known_types: list[str] | None = None) -> str:
        """Mensaje completo para consola y para la pantalla de error."""
        lines = [
            f"El mapa tiene {len(self.problems)} objeto(s) que el engine no "
            f"sabe interpretar:",
            "",
        ]
        if self.tmx_path:
            lines.insert(0, f"TMX: {self.tmx_path}")
            lines.insert(1, "")
        lines.extend(p.describe() for p in self.problems)
        lines.append("")
        lines.append(
            "En Tiled, selecciona el objeto y revisa el campo «Type» (en "
            "versiones recientes se llama «Class»). Distingue mayúsculas: "
            "«walker» no es «Walker».",
        )
        if known_types:
            lines.append("")
            lines.append("Tipos válidos:")
            lines.extend(_columns(sorted(known_types)))
        return "\n".join(lines)


def suggest_types(unknown: str, known: list[str]) -> tuple[str, ...]:
    """Tipos válidos parecidos al que se escribió.

    El primer caso que se comprueba es el que más ocurre: acertar el nombre y
    fallar las mayúsculas. `difflib` también lo encontraría, pero mezclado con
    otras opciones; cuando existe una coincidencia exacta salvo capitalización
    es *la* respuesta, y ofrecer alternativas junto a ella sólo añade dudas.
    """
    if not unknown:
        return ()

    lowered = unknown.lower()
    exact_ignoring_case = [k for k in known if k.lower() == lowered]
    if exact_ignoring_case:
        return tuple(exact_ignoring_case)

    return tuple(
        difflib.get_close_matches(
            unknown, known, n=_MAX_SUGGESTIONS, cutoff=_SIMILARITY_CUTOFF,
        ),
    )


def known_object_types(entity_types: list[str]) -> list[str]:
    """Todos los tipos aceptables en la capa `Objects`."""
    return sorted({*BUILTIN_OBJECT_TYPES, *entity_types})


def _columns(items: list[str], per_row: int = 4, width: int = 24) -> list[str]:
    """Lista en columnas: 30 tipos en una línea por tipo no se lee."""
    rows: list[str] = []
    for i in range(0, len(items), per_row):
        chunk = items[i:i + per_row]
        rows.append("  " + "".join(name.ljust(width) for name in chunk).rstrip())
    return rows
