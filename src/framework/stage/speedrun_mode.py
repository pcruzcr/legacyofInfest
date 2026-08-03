"""
Module: speedrun_mode
System: framework.stage
Academic Unit: N/A
Description: Speedrun mode with global timer, splits per stage, and ghost data.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import orjson

# AUD-157 — el estado del jugador va al directorio del usuario.
#
# `PROJECT_ROOT` es el árbol de instalación, y una versión empaquetada
# puede estar en un sitio de sólo lectura. Es la misma corrección que
# AUD-032 aplicó a las preferencias y a los logros y que aquí se quedó
# sin aplicar.
from src.engine.core.user_settings import user_data_dir

logger = logging.getLogger(__name__)

_DEFAULT_SAVE_PATH: Path = user_data_dir() / "saves" / "speedrun.json"


#: Marca de «aquí no hay nada que cargar». No se usa `None` porque `null` es
#: un contenido JSON válido: un fichero con `null` dentro devolvería `None` y
#: se confundiría con «el fichero no existe», que es el único caso que no
#: merece aviso.
_AUSENTE = object()


def _leer_json(ruta: Path) -> Any:
    """Lee un fichero de datos del jugador. `_AUSENTE` si no se puede usar.

    AUD-171. Distingue tres situaciones que antes eran una sola:

    * **no existe** — normal la primera vez que se juega; ni aviso ni ruido;
    * **existe y no es JSON** — se avisa nombrando la ruta y se sigue con los
      valores por defecto;
    * **existe, es JSON válido y tiene otra forma** — igual que el anterior.
      Éste es el caso que el `except (FileNotFoundError, JSONDecodeError)`
      anterior *no* cubría, y el que de verdad rompía: un fichero con `[]`
      dentro hacía saltar un `AttributeError` sin capturar desde `.get()`.

    La forma concreta la comprueba cada `load`; aquí sólo se garantiza que lo
    devuelto viene de un JSON que se pudo parsear.
    """
    try:
        crudo = ruta.read_bytes()
    except FileNotFoundError:
        return _AUSENTE
    except OSError as e:
        # Permisos, disco desconectado, ruta que es un directorio. No es
        # motivo para tumbar la partida, sí para dejar rastro.
        logger.warning("speedrun: %s es ilegible (%s); se empieza de cero", ruta, e)
        return _AUSENTE

    try:
        return orjson.loads(crudo)
    except orjson.JSONDecodeError:
        logger.warning("speedrun: %s es ilegible (JSON corrupto); se empieza de cero", ruta)
        return _AUSENTE


class SpeedrunTimer:
    """Global speedrun timer with per-stage splits."""

    def __init__(self) -> None:
        self._global_time: float = 0.0
        self._running: bool = False
        self._splits: list[dict[str, Any]] = []
        self._current_stage: str = ""

    def start(self) -> None:
        self._global_time = 0.0
        self._running = True
        self._splits = []

    def stop(self) -> None:
        self._running = False

    def reset(self) -> None:
        self._global_time = 0.0
        self._running = False
        self._splits = []
        self._current_stage = ""

    def update(self, dt: float) -> None:
        if self._running:
            self._global_time += dt

    def start_stage(self, stage_id: str) -> None:
        self._current_stage = stage_id

    def split(self, stage_id: str) -> None:
        self._splits.append({
            "stage_id": stage_id,
            "time": self._global_time,
        })

    def get_formatted_time(self, t: float | None = None) -> str:
        total_seconds = int(t if t is not None else self._global_time)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_splits(self) -> list[dict[str, Any]]:
        return list(self._splits)

    def save(self, path: str | Path | None = None) -> None:
        data = {
            "global_time": self._global_time,
            "splits": self._splits,
        }
        path = Path(path) if path is not None else _DEFAULT_SAVE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))

    def load(self, path: str | Path | None = None) -> None:
        ruta = Path(path) if path is not None else _DEFAULT_SAVE_PATH
        datos = _leer_json(ruta)
        if datos is _AUSENTE:
            return

        # AUD-171: un fichero con `[]`, `42` o `null` es JSON perfectamente
        # válido, y el `.get()` de abajo sólo existe en un diccionario.
        if not isinstance(datos, dict):
            logger.warning(
                "speedrun: %s es ilegible (se esperaba un objeto y hay %s); "
                "se empieza de cero", ruta, type(datos).__name__,
            )
            return

        tiempo = datos.get("global_time", 0.0)
        parciales = datos.get("splits", [])
        if not isinstance(tiempo, (int, float)) or isinstance(tiempo, bool) or not isinstance(parciales, list):
            logger.warning(
                "speedrun: %s es ilegible (campos con el tipo equivocado); "
                "se empieza de cero", ruta,
            )
            return

        self._global_time = float(tiempo)
        self._splits = parciales

    @property
    def global_time(self) -> float:
        return self._global_time

    @property
    def running(self) -> bool:
        return self._running


class GhostData:
    """La grabación de una carrera: dónde estaba el jugador en cada fotograma.

    AUD-142 — estaba escrita entera y **no la usaba nadie**.

    Tenía `record`, `get_frame`, `save`, `load`, `clear` y `frame_count`, todo
    correcto, y cero llamadas en el proyecto: ni se grababa ni se reproducía.
    Es el mismo patrón que el sistema de diálogo (AUD-127) y el de escenas
    (AUD-136): la pieza estaba, faltaba quien la usara.

    Ahora `StageScene` graba mientras se juega y dibuja la carrera anterior.
    El fantasma es la forma más barata que existe de hacer que repetir un
    nivel tenga sentido: no hace falta un adversario, basta con quien fuiste.

    Grabación a intervalo fijo
    --------------------------
    Se graba cada `INTERVALO` segundos y no cada fotograma. A 60 fps, un nivel
    de tres minutos serían 10.800 puntos —un fichero de medio mega para dibujar
    un muñeco— y la diferencia no se ve: a 30 muestras por segundo el fantasma
    se mueve igual de fluido para el ojo, y el fichero baja a la mitad.
    """

    #: Segundos entre muestras. 1/30 basta: el ojo no distingue más.
    INTERVALO: float = 1.0 / 30.0

    def __init__(self) -> None:
        self._frames: list[dict[str, float]] = []
        self._t: float = 0.0
        self._desde_ultima: float = 0.0

    def grabar_si_toca(self, dt: float, x: float, y: float,
                       state: str = "") -> bool:
        """Graba una muestra si ha pasado el intervalo. Devuelve si grabó."""
        self._t += dt
        self._desde_ultima += dt
        if self._desde_ultima < self.INTERVALO:
            return False
        self._desde_ultima = 0.0
        self.record(x, y, state)
        return True

    def posicion_en(self, segundos: float) -> tuple[float, float] | None:
        """Dónde estaba el fantasma en ese instante de SU carrera.

        Devuelve `None` cuando la carrera grabada ya terminó, que es la señal
        de que el jugador va por detrás de su propio récord — y es justo la
        información que hace útil a un fantasma.
        """
        if not self._frames:
            return None
        indice = int(segundos / self.INTERVALO)
        if indice >= len(self._frames):
            return None
        marco = self._frames[max(0, indice)]
        return float(marco.get("x", 0.0)), float(marco.get("y", 0.0))

    @property
    def duracion(self) -> float:
        return len(self._frames) * self.INTERVALO

    def record(self, x: float, y: float, state: str) -> None:
        self._frames.append({"x": x, "y": y, "state": state})

    def get_frame(self, index: int) -> dict[str, float] | None:
        if 0 <= index < len(self._frames):
            return self._frames[index]
        return None

    def clear(self) -> None:
        self._frames.clear()
        self._t = 0.0
        self._desde_ultima = 0.0

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(orjson.dumps(self._frames, option=orjson.OPT_INDENT_2))

    def load(self, path: str | Path) -> None:
        ruta = Path(path)
        datos = _leer_json(ruta)
        if datos is _AUSENTE:
            return

        # AUD-171: esto se asignaba a `self._frames` sin mirarlo. Con una
        # cadena dentro del fichero, `frame_count` devolvía su longitud y
        # `get_frame(0)` devolvía una letra: el fantasma no fallaba, mentía.
        if not isinstance(datos, list) or not all(isinstance(f, dict) for f in datos):
            logger.warning(
                "speedrun: %s es ilegible (se esperaba una lista de fotogramas); "
                "no se carga el fantasma", ruta,
            )
            return

        self._frames = datos

    @property
    def frame_count(self) -> int:
        return len(self._frames)

def registrar_marca(
    stage_id: str, tiempo: float, path: str | Path | None = None,
) -> None:
    """Anota el tiempo de un escenario en el libro de récords.

    AUD-231 — por qué no vale `SpeedrunTimer.save()` para esto
    ==========================================================
    AUD-202 conectó `save()` al final de cada escenario, y con eso la pantalla
    de récords dejó de inventarse los tiempos. Pero seguía sin servir de nada.

    `StageScene.on_enter` llama a `SpeedrunTimer.start()`, y `start()` hace
    ``_splits = []``: entrar a un nivel vacía los parciales. Así que el `save()`
    del final escribía un fichero con **una sola marca**, encima del anterior.
    Medido: terminar `stage0` en 30 s y luego `stage1_1` en 45 dejaba en disco
    sólo la de `stage1_1`. La tabla podía enseñar el último nivel jugado y
    ``--:--.--`` en los otros diez.

    La distinción que faltaba es de qué es cada cosa. `save()` vuelca el estado
    de **una carrera** —lo que el cronómetro lleva medido ahora mismo— y es lo
    correcto para retomar una partida. El fichero que lee la pantalla de récords
    no es eso: es un **libro de marcas**, acumulativo, donde una entrada sólo se
    pisa a sí misma y sólo cuando mejora.

    Se conserva una entrada por escenario en lugar de añadir una por partida:
    con la lista completa el fichero crecería sin límite a cambio de nada, ya
    que la pantalla sólo muestra la mejor.

    No lanza nunca. Esto corre al terminar un nivel, y perder una marca es
    molesto mientras que quedarse sin terminar el nivel es peor. Un fichero
    ilegible se sustituye por uno nuevo con esta marca: es lo único recuperable
    y deja al jugador en mejor sitio que borrarlo del todo.
    """
    ruta = Path(path) if path is not None else _DEFAULT_SAVE_PATH

    datos = _leer_json(ruta)
    marcas: dict[str, float] = {}
    if isinstance(datos, dict):
        for parcial in datos.get("splits", []) or []:
            if not isinstance(parcial, dict):
                continue
            sid = parcial.get("stage_id")
            t = parcial.get("time")
            if isinstance(sid, str) and isinstance(t, (int, float)) and not isinstance(t, bool):
                marcas[sid] = float(t)

    previa = marcas.get(stage_id)
    if previa is None or tiempo < previa:
        marcas[stage_id] = float(tiempo)

    contenido = {
        # La suma de las mejores marcas, no el tiempo de una partida seguida.
        # Se escribe para que `SpeedrunTimer.load()` siga encontrando el campo
        # que espera; quien lea récords usa `splits`.
        "global_time": sum(marcas.values()),
        "splits": [{"stage_id": sid, "time": t} for sid, t in sorted(marcas.items())],
    }
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(orjson.dumps(contenido, option=orjson.OPT_INDENT_2))
    except OSError:
        logger.warning("speedrun: no se pudo anotar la marca en %s", ruta,
                       exc_info=True)
