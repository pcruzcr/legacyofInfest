"""Un bot que juega niveles sin pantalla y registra qué le pasa.

Por qué inyección de eventos y no PyAutoGUI (AUD-049)
-----------------------------------------------------
PyAutoGUI automatiza el ratón y el teclado a nivel de sistema operativo. Para
este proyecto es la herramienta equivocada por tres razones medidas:

* **Necesita pantalla real.** Toda la suite corre con
  ``SDL_VIDEODRIVER=dummy``; PyAutoGUI no puede operar ahí, así que estas
  pruebas no correrían en CI — que es exactamente donde tienen valor.
* **Es ~73.000x más lenta.** Inyectar un evento directamente en el
  ``InputManager`` cuesta 0,7 µs medidos; PyAutoGUI ronda los 10-50 ms por
  acción con su pausa por defecto. Un bot que juega 30 s de nivel a 60 fps
  necesita 1.800 entradas: 1,3 ms contra ~90 s.
* **Es no determinista.** Depende del foco de ventana, del compositor y de la
  latencia del SO. Un test de QA que falla por dónde estaba el cursor no es un
  test de QA.

La inyección directa da control fotograma a fotograma y reproducibilidad exacta,
que es lo que un bot de playtest necesita. PyAutoGUI tiene su lugar —probar el
ejecutable empaquetado en la máquina del usuario final— pero eso es una prueba
de instalación, no de diseño de nivel.
"""
from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass, field
from itertools import pairwise

import pygame

from src.engine.input.action_map import Action


@dataclass
class PlaythroughLog:
    """Lo que le ocurrió al bot durante un intento."""

    frames: int = 0
    elapsed: float = 0.0
    max_x: float = 0.0
    deaths: list[tuple[float, float]] = field(default_factory=list)
    damage_events: list[tuple[float, float, float]] = field(default_factory=list)
    reached_exit: bool = False
    stuck_frames: int = 0
    positions: list[tuple[float, float]] = field(default_factory=list)

    @property
    def progress_ratio(self) -> float:
        """Fracción del avance horizontal logrado (0-1) si se conoce la meta."""
        return self._progress

    _progress: float = 0.0


class ScriptedBot:
    """Reproduce una secuencia de acciones, fotograma a fotograma.

    Es deliberadamente tonto: no planifica rutas. Su utilidad no es jugar bien,
    sino ser **reproducible**. Un bot que siempre hace lo mismo convierte "el
    nivel cambió" en una señal detectable, mientras que un bot inteligente
    introduce su propia varianza y hace imposible distinguir una regresión del
    nivel de una regresión del bot.
    """

    def __init__(self, script: list[tuple[int, set[Action]]]) -> None:
        """``script`` es una lista de (fotogramas, acciones mantenidas)."""
        self._script = script

    def actions(self) -> Iterator[set[Action]]:
        for frames, held in self._script:
            for _ in range(frames):
                yield held


def walk_right_bot(seconds: float = 30.0, jump_every: int = 45) -> ScriptedBot:
    """Camina a la derecha saltando periódicamente.

    Es el bot de referencia para "¿se puede avanzar por este nivel?". No resuelve
    puzzles, pero un nivel donde ni siquiera puede progresar horizontalmente
    tiene un problema de geometría, no de habilidad.
    """
    total = int(seconds * 60)
    script: list[tuple[int, set[Action]]] = []
    frames_done = 0
    while frames_done < total:
        run = min(jump_every, total - frames_done)
        script.append((run - 1, {Action.MOVE_RIGHT}))
        script.append((1, {Action.MOVE_RIGHT, Action.JUMP}))
        frames_done += run
    return ScriptedBot(script)


class _StubInput:
    """InputManager mínimo que devuelve lo que el bot decide.

    Los nombres importan y no son los obvios. ``_InputSnapshot`` en
    ``states/base.py`` consulta:

    * ``is_action_held(a)``    — la acción se mantiene pulsada este fotograma
    * ``is_action_pressed(a)`` — flanco de bajada (equivale a "just pressed")

    Nótese que ``is_action_pressed`` significa *flanco*, no *mantenida*, al
    contrario de lo que sugiere el nombre. Una primera versión de este stub
    implementó los nombres que yo asumí y devolvió ``False`` a todo lo demás vía
    ``__getattr__`` — así que el bot no se movía y el test culpó al nivel. El
    ``__getattr__`` permisivo convirtió un stub incompleto en un diagnóstico
    equivocado, que es exactamente el patrón que este arnés existe para evitar.

    Por eso ahora las consultas desconocidas **lanzan**: si el jugador empieza a
    leer una acción nueva, preferimos un fallo ruidoso a un bot que finge jugar.
    """

    #: Consultas conocidas que legítimamente devuelven False para un bot.
    _SAFE_FALSE = frozenset({
        "is_raw_key_pressed", "is_raw_key_held", "is_action_just_released",
    })

    def __init__(self) -> None:
        self._held: set[Action] = set()
        self._prev: set[Action] = set()

    def set_actions(self, actions: set[Action]) -> None:
        self._prev = self._held
        self._held = set(actions)

    # ── la API que el jugador realmente usa ────────────────────

    def is_action_held(self, action: Action) -> bool:
        return action in self._held

    def is_action_pressed(self, action: Action) -> bool:
        """Flanco de bajada: pulsada ahora y no en el fotograma anterior."""
        return action in self._held and action not in self._prev

    def is_action_just_pressed(self, action: Action) -> bool:
        return self.is_action_pressed(action)

    def __getattr__(self, name: str):
        if name in self._SAFE_FALSE:
            return lambda *a, **k: False
        raise AttributeError(
            f"_StubInput no implementa {name!r}. El jugador consulta una acción "
            f"que el bot no sabe simular; añádela en lugar de dejar que devuelva "
            f"False silenciosamente."
        )


def run_playthrough(
    scene,
    bot: ScriptedBot,
    *,
    surface: pygame.Surface | None = None,
    dt: float = 1 / 60,
    stuck_threshold: float = 1.0,
) -> PlaythroughLog:
    """Ejecuta al bot sobre una escena ya inicializada y devuelve el registro.

    La escena debe haber pasado ya por ``on_enter()``. No se dibuja salvo que se
    pase ``surface``: el análisis de geometría no lo necesita, y omitirlo hace
    el recorrido varias veces más rápido.
    """
    log = PlaythroughLog()
    stub = _StubInput()
    original = scene.context.input_manager
    scene.context.input_manager = stub

    player = getattr(scene, "_player", None)
    stage = getattr(scene, "_stage_data", None)
    exit_rect = getattr(stage, "next_trigger", None) if stage else None

    last_x = player.position.x if player else 0.0
    stuck_run = 0.0

    try:
        for held in bot.actions():
            stub.set_actions(held)
            scene.update(dt)
            if surface is not None:
                scene.draw(surface)

            log.frames += 1
            log.elapsed += dt

            player = getattr(scene, "_player", None)
            if player is None:
                break

            x, y = float(player.position.x), float(player.position.y)
            log.positions.append((x, y))
            log.max_x = max(log.max_x, x)

            # Atasco: sin avance horizontal apreciable durante N segundos.
            if abs(x - last_x) < 1.0:
                stuck_run += dt
                if stuck_run >= stuck_threshold:
                    log.stuck_frames += 1
            else:
                stuck_run = 0.0
            last_x = x

            if player.current_health <= 0:
                log.deaths.append((x, y))
                break

            if exit_rect is not None and player.rect.colliderect(exit_rect):
                log.reached_exit = True
                break
    finally:
        scene.context.input_manager = original

    if exit_rect is not None:
        spawn_x = float(stage.spawn_point.x) if stage else 0.0
        span = max(abs(exit_rect.centerx - spawn_x), 1.0)
        log._progress = min(1.0, abs(log.max_x - spawn_x) / span)

    return log


def death_heatmap(
    logs: list[PlaythroughLog], bucket_px: float = 128.0,
) -> dict[int, int]:
    """Agrupa las muertes por tramo horizontal.

    Un pico en un solo cubo señala un punto de frustración: el sitio donde el
    nivel mata repetidamente. Que ese pico sea un problema o un pico de
    dificultad *intencionado* lo decide el diseñador; la métrica sólo lo hace
    visible.
    """
    buckets: dict[int, int] = {}
    for log in logs:
        for x, _y in log.deaths:
            key = int(x // bucket_px)
            buckets[key] = buckets.get(key, 0) + 1
    return dict(sorted(buckets.items()))


def traversal_stats(logs: list[PlaythroughLog]) -> dict[str, float]:
    """Estadísticas agregadas de varios intentos."""
    if not logs:
        return {}
    completions = [lg for lg in logs if lg.reached_exit]
    times = [lg.elapsed for lg in completions]
    return {
        "intentos": float(len(logs)),
        "completados": float(len(completions)),
        "tasa_exito": len(completions) / len(logs),
        "tiempo_medio": sum(times) / len(times) if times else 0.0,
        "tiempo_min": min(times) if times else 0.0,
        "avance_medio": sum(lg.progress_ratio for lg in logs) / len(logs),
        "muertes": float(sum(len(lg.deaths) for lg in logs)),
    }


def furthest_reachable(logs: list[PlaythroughLog]) -> float:
    return max((lg.max_x for lg in logs), default=0.0)


def path_length(log: PlaythroughLog) -> float:
    """Distancia recorrida, útil para detectar rodeos o vaivenes."""
    return sum(
        math.dist(a, b) for a, b in pairwise(log.positions)
    )
