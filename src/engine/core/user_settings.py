"""
Module: user_settings
System: engine.core
Academic Unit: N/A

Player-controlled preferences: accessibility, volumes, difficulty.

Why this module exists (AUD-021 / AUD-036)
------------------------------------------
``settings.py`` mixes two very different things: engine constants that must
never change at runtime (tile size, gravity, internal resolution) and player
preferences that must. The preferences were declared as bare module-level
globals — ``COLORBLIND_MODE``, ``SUBTITLES_ENABLED`` — which meant:

* any module could mutate them from anywhere, with no audit trail;
* they were never persisted, so a preference was lost on quit;
* they leaked between tests, because a test that set one left it set;
* and most importantly, **nothing ever wrote to them**. The options screen
  saved ``colorblind_mode`` into ``config.json`` and the post-processing pass
  read ``settings.COLORBLIND_MODE``, but no code connected the two. A player
  could select "deuteranopia", see it persist across restarts in the UI, and
  never have a single frame actually filtered. ``SUBTITLES_ENABLED`` had no UI
  and no reader at all.

Preferences now live in one owned, persisted, injectable object. Reads go
through :func:`get`; writes go through :meth:`UserSettings.save`.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Final

import orjson

logger = logging.getLogger(__name__)

CONFIG_FILENAME: Final = "config.json"

COLORBLIND_MODES: Final[tuple[str, ...]] = (
    "off", "protanopia", "deuteranopia", "tritanopia",
)

# ── Accesibilidad (AUD-126) ───────────────────────────────────────────────
#
# El proyecto ya tenía `colorblind_mode` conectado de punta a punta —opciones,
# preferencias, post-procesado— y ahí se quedó. Faltaban las tres barreras que
# más gente encuentran en un plataformas:
#
# * **Texto pequeño.** La resolución interna es de 800 × 600 y la tipografía
#   base mide 14 px. En una pantalla grande a dos metros, eso no se lee. Es la
#   petición número uno en cualquier estudio de accesibilidad de videojuegos,
#   por delante del daltonismo.
# * **Movimiento.** Sacudida de pantalla, estelas, partículas y destellos
#   provocan náusea a quien tiene sensibilidad vestibular, y hacen ilegible el
#   juego a quien tiene déficit de atención.
# * **Mantener pulsado.** Correr y cargar el ataque exigen mantener una tecla.
#   Para quien tiene temblor, artritis o usa un conmutador, mantener es la
#   diferencia entre jugar y no jugar.
#
# Los tres se guardan aquí porque son preferencias del jugador, no del
# escenario: viajan con la persona entre partidas y entre niveles.

#: Multiplicadores de tamaño de texto ofrecidos en la pantalla de opciones.
#: 1,0 es el diseño original; 2,0 duplica y sigue cabiendo en 800 × 600 sin
#: recortar los diálogos, que es el límite que se comprobó.
ESCALAS_DE_TEXTO: Final[tuple[float, ...]] = (1.0, 1.25, 1.5, 2.0)

#: Cuánto se atenúa cada efecto con «movimiento reducido» activado. No es cero
#: para todos a propósito: quitar del todo la estela del dash borra la única
#: señal de que el dash ocurrió, y eso deja de ser accesibilidad para pasar a
#: ser información perdida.
MOVIMIENTO_REDUCIDO_FACTOR: Final[float] = 0.25

#: Velocidades de la máquina de escribir de los diálogos (AUD-128).
#:
#: La velocidad de lectura es una necesidad de accesibilidad, no una
#: preferencia estética: 30 caracteres por segundo fijos dejan fuera a quien
#: lee despacio y aburren a quien lee rápido, y las dos cosas terminan igual —
#: el jugador aprende a saltarse los diálogos.
VELOCIDADES_DE_TEXTO_VALIDAS: Final[tuple[str, ...]] = (
    "slow", "normal", "fast", "instant",
)


def user_data_dir() -> Path:
    """The per-user directory this game stores its state in.

    Deliberately *not* inside the project directory: a packaged build may be
    installed somewhere read-only (Program Files, /Applications), and writing
    player state into the install tree is what put ``saves/slot_1.json`` into
    version control in the first place.

    AUD-032: four modules — ``achievements``, ``keybinding_scene``,
    ``title_scene`` and this one — each open-coded
    ``Path(os.environ.get("APPDATA", "~/.config")) / "legacyofinfest" / ...``.
    Besides being duplicated four ways, that spelling ignores
    ``XDG_CONFIG_HOME`` on Linux and mis-locates data on macOS. One helper, one
    place to fix.
    """
    import os

    if os.name == "nt":
        base = os.environ.get("APPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Roaming"
    else:
        base = os.environ.get("XDG_CONFIG_HOME")
        root = Path(base) if base else Path.home() / ".config"
    return root / "legacyofinfest"


def _default_config_path() -> Path:
    """Full path to the preferences file."""
    return user_data_dir() / CONFIG_FILENAME


@dataclass
class UserSettings:
    """Persisted player preferences.

    Field names match the keys written by the options screen, so an existing
    ``config.json`` is read without migration.
    """

    music_volume: float = 0.7
    sfx_volume: float = 0.8
    difficulty: str = "normal"
    colorblind_mode: str = "off"
    subtitles_enabled: bool = False
    #: Idioma de la interfaz. Español por defecto: es el idioma del curso.
    language: str = "es"
    #: Correo del último estudiante que se identificó (AUD-098).
    #:
    #: Aquí sólo se guarda **quién** era, nunca sus notas: el progreso vive en
    #: su propio fichero, en `saves/academico/`. Se recuerda para que en un
    #: aula no haya que teclear el correo en cada arranque, que es la clase de
    #: fricción por la que una función correcta acaba sin usarse.
    student_email: str = ""

    # ── Accesibilidad (AUD-126) ────────────────────────────────
    #: Multiplicador del tamaño de todo el texto. Ver `ESCALAS_DE_TEXTO`.
    text_scale: float = 1.0
    #: Atenúa sacudida de pantalla, estelas, partículas y destellos.
    reduced_motion: bool = False
    #: Convierte las acciones de mantener —correr, cargar— en pulsar/soltar.
    hold_to_press: bool = False
    #: Velocidad de la máquina de escribir. `instant` muestra el texto entero.
    text_speed: str = "normal"

    # Not persisted: resolved at load time so callers need not handle None.
    _path: Path | None = field(default=None, repr=False, compare=False)

    # ── validation ─────────────────────────────────────────────

    def __post_init__(self) -> None:
        self.music_volume = _clamp01(self.music_volume)
        self.sfx_volume = _clamp01(self.sfx_volume)
        if self.colorblind_mode not in COLORBLIND_MODES:
            logger.warning(
                "UserSettings: unknown colorblind_mode %r — falling back to 'off'",
                self.colorblind_mode,
            )
            self.colorblind_mode = "off"
        self.subtitles_enabled = bool(self.subtitles_enabled)

        # AUD-126 — la escala se **recorta**, no se rechaza.
        #
        # Un `config.json` con `text_scale: 40` viene de una edición a mano o
        # de un fichero corrupto, y negarse a arrancar por eso deja al jugador
        # sin juego. Recortar a 2,0 le deja el texto grande, que es lo que
        # pedía. El mismo criterio que las propiedades de mapa.
        try:
            escala = float(self.text_scale)
        except (TypeError, ValueError):
            escala = 1.0
        self.text_scale = min(max(escala, ESCALAS_DE_TEXTO[0]), ESCALAS_DE_TEXTO[-1])
        self.reduced_motion = bool(self.reduced_motion)
        self.hold_to_press = bool(self.hold_to_press)
        if self.text_speed not in VELOCIDADES_DE_TEXTO_VALIDAS:
            logger.warning(
                "UserSettings: velocidad de texto %r desconocida — se usa "
                "'normal'", self.text_speed,
            )
            self.text_speed = "normal"

        from src.engine.core.i18n import IDIOMA_POR_DEFECTO, IDIOMAS
        if self.language not in IDIOMAS:
            logger.warning(
                "UserSettings: idioma %r desconocido — se usa %r",
                self.language, IDIOMA_POR_DEFECTO,
            )
            self.language = IDIOMA_POR_DEFECTO

    # ── persistence ────────────────────────────────────────────

    @classmethod
    def load(cls, path: Path | None = None) -> UserSettings:
        """Read preferences from disk, falling back to defaults."""
        resolved = path or _default_config_path()
        try:
            raw = orjson.loads(resolved.read_bytes())
        except FileNotFoundError:
            return cls(_path=resolved)
        except (OSError, ValueError, TypeError) as exc:
            logger.warning(
                "UserSettings: could not read %s (%s) — using defaults",
                resolved, exc,
            )
            return cls(_path=resolved)

        if not isinstance(raw, dict):
            logger.warning("UserSettings: %s is not an object — using defaults", resolved)
            return cls(_path=resolved)

        # pylint: disable=no-member  # `__dataclass_fields__` lo genera @dataclass
        known = {f for f in cls.__dataclass_fields__ if not f.startswith("_")}
        kwargs: dict[str, Any] = {k: v for k, v in raw.items() if k in known}
        try:
            return cls(**kwargs, _path=resolved)
        except (TypeError, ValueError) as exc:
            logger.warning(
                "UserSettings: %s has invalid values (%s) — using defaults",
                resolved, exc,
            )
            return cls(_path=resolved)

    def save(self, path: Path | None = None) -> bool:
        """Write preferences to disk. Returns True on success.

        Never raises: failing to persist a volume slider must not crash a game.
        """
        target = path or self._path or _default_config_path()
        payload = {
            k: v for k, v in asdict(self).items() if not k.startswith("_")
        }
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
        except OSError as exc:
            logger.warning("UserSettings: could not write %s (%s)", target, exc)
            return False
        self._path = target
        return True


def _clamp01(value: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


# ── process-wide accessor ──────────────────────────────────────
#
# Preferences are genuinely global to a running game, so a single instance is
# the right model — but unlike the previous bare module globals it is loaded
# once, validated, persisted, and replaceable in tests via set_settings().

_current: UserSettings | None = None


def get() -> UserSettings:
    """The active preferences, loading them from disk on first access."""
    global _current
    if _current is None:
        _current = UserSettings.load()
    return _current


def set_settings(settings_obj: UserSettings) -> None:
    """Replace the active preferences (used by App at startup, and by tests)."""
    global _current
    _current = settings_obj


def reset() -> None:
    """Forget the loaded preferences so the next get() re-reads them."""
    global _current
    _current = None
