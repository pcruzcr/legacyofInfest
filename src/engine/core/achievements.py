from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import orjson
import pygame
from pydantic import BaseModel

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.core.user_settings import user_data_dir

logger = logging.getLogger(__name__)

#: Dónde se guarda el progreso por defecto de los logros. Un estudiante
#: identificado tiene su propio fichero junto a éste (AUD-200).
ACHIEVEMENTS_PATH = user_data_dir() / "achievements.json"

#: Las definiciones de logros viven en un fichero de datos (AUD-197): se
#: validan en CI y se editan sin tocar el motor. El campo `hidden` es la
#: medalla secreta (AUD-198): no se muestra hasta desbloquearse.
DEFINICIONES_PATH = settings.PROJECT_ROOT / "data" / "achievements.json"


class AchievementDef(BaseModel):
    id: str
    name: str
    description: str
    icon: str = "trophy"
    hidden: bool = False
    target: int = 1
    event: str = ""


class AchievementProgress(BaseModel):
    current: int = 0
    unlocked: bool = False


def esta_oculta(definicion: AchievementDef, progreso: AchievementProgress) -> bool:
    """Una medalla secreta no se muestra mientras esté bloqueada.

    AUD-198 — el campo `hidden` existía en `AchievementDef` y nadie lo leía:
    un logro marcado oculto aparecía en la pantalla con su nombre y su
    descripción, que es el único lugar donde el jugador podía descubrir qué
    le faltaba. Esta es la regla única de lo oculto: secreto = marcado así Y
    todavía sin desbloquear. Desbloqueado, se muestra con orgullo.
    """
    return definicion.hidden and not progreso.unlocked


def _slug_estudiante(correo: str) -> str:
    """Un correo como nombre de fichero: legible y seguro en cualquier sistema."""
    return "".join(c if c.isalnum() else "_" for c in correo.lower())


#: Quién decide dónde vive el fichero de logros (AUD-200). El núcleo del motor
#: no puede conocer a `src.framework`, así que la resolución por estudiante la
#: **inyecta** la sesión académica (`sesion.py`) a través de
#: `bind_ruta_resolver`; sin resolver, es el fichero histórico del proceso.
_ruta_resolver = None


def bind_ruta_resolver(implementacion) -> None:
    """Declara quién traduce «estudiante activo» a ruta de logros.

    Esto separa lo que L1 exige separar: `engine/core` define el mecanismo de
    persistencia y `framework` aporta la política (un fichero por correo).
    """
    global _ruta_resolver
    _ruta_resolver = implementacion


def _ruta_de_logros() -> Path:
    """El fichero donde viven los logros del estudiante activo.

    AUD-200 — los logros eran del proceso entero: dos estudiantes en la misma
    máquina compartían el mismo `achievements.json` y el segundo veía los
    logros del primero. Si la sesión académica registró un resolver, éste
    decide el fichero (uno por correo); si no, se conserva la ruta histórica,
    de modo que una partida anterior no se pierde al actualizar el motor.
    """
    if _ruta_resolver is not None:
        ruta = _ruta_resolver()
        if ruta is not None:
            return ruta
    return ACHIEVEMENTS_PATH


def _cargar_definiciones() -> list[AchievementDef]:
    """Las definiciones del catálogo `data/achievements.json`.

    AUD-197 — antes estaban escritas a mano en `_init_achievements`: diez
    `AchievementDef(...)` que sólo podía tocar quien tocara el motor. Un JSON
    se edita sin miedo, y `scripts/check_achievements.py` lo valida antes de
    que un texto roto o un objetivo en cero llegue a la pantalla.
    """
    try:
        raw: Any = orjson.loads(DEFINICIONES_PATH.read_bytes())
    except FileNotFoundError:
        logger.warning(
            "achievements: no existe %s; el juego arranca sin logros",
            DEFINICIONES_PATH,
        )
        return []
    except (ValueError, TypeError):
        logger.warning(
            "achievements: %s ilegible; el juego arranca sin logros",
            DEFINICIONES_PATH, exc_info=True,
        )
        return []

    definiciones: list[AchievementDef] = []
    entradas = raw.get("achievements", []) if isinstance(raw, dict) else []
    for entrada in entradas:
        if not isinstance(entrada, dict):
            continue
        try:
            definiciones.append(AchievementDef.model_validate(entrada))
        except ValueError as e:
            logger.warning(
                "achievements: entrada inválida en %s (%s); se omite",
                DEFINICIONES_PATH, e,
            )
    return definiciones


class AchievementSystem:
    """Tracks achievement progress and surfaces unlock notifications.

    Still a process-wide singleton (achievements are genuinely global player
    state), but with two defects removed:

    * **AUD-019** — it no longer reaches for a module-level default event bus.
      The bus is injected via :meth:`bind_bus`, which ``StageScene`` calls with
      the context bus. Without a bound bus the system tracks progress silently
      rather than emitting into a bus nobody is listening to.
    * **AUD-030** — the notification font is created lazily on first draw
      instead of in ``__init__``. Constructing a ``pygame.font.Font`` in the
      constructor meant ``get_instance()`` raised ``pygame.error: font not
      initialized`` for any caller that ran before ``pygame.font.init()`` —
      and, being a singleton, it then held that font for the process lifetime.
    """

    _instance: AchievementSystem | None = None

    @classmethod
    def init_instance(cls) -> AchievementSystem:
        """Sustituye el singleton por uno limpio. **Sólo para pruebas.**

        AUD-366 — esto salía como huérfano real desde AUD-233 y la pregunta
        llevaba abierta desde entonces. Respuesta, con el código delante: no
        tiene ni debe tener llamante de producción. Cambiar de estudiante ya se
        resuelve con `load()`, que vuelve el progreso a cero antes de leer
        (AUD-200) **sobre la misma instancia**, y ésa es la forma correcta.

        Aquí está el peligro que justifica el aviso: esto no reinicia el
        sistema, lo **reemplaza**. Cualquiera que guardara la instancia
        anterior —`inventory.py:193`, `progress_scene.py:102` y tres sitios
        más la piden por `get_instance()` cada vez, pero nada impide
        guardarla— seguiría escribiendo logros en un objeto que ya no lee
        nadie, y el jugador vería desaparecer medallas sin ningún error.

        Se conserva porque una prueba necesita un singleton limpio de verdad
        (`test_guia_del_motor.py:74`) y `load()` no da eso: da uno recargado.
        """
        cls._instance = AchievementSystem()
        return cls._instance

    @classmethod
    def get_instance(cls) -> AchievementSystem:
        if cls._instance is None:
            cls._instance = AchievementSystem()
        return cls._instance

    def __init__(self) -> None:
        self._defs: dict[str, AchievementDef] = {}
        self._progress: dict[str, AchievementProgress] = {}
        self._notifications: list[dict[str, Any]] = []
        self._notify_timer: float = 0.0
        self._current_notify: dict[str, Any] | None = None
        self._subscribed: bool = False
        self._stats: dict[str, int] = {}
        #: Escenarios distintos ya visitados. Es un conjunto, no un
        #: contador, y por eso no cabe en `_stats` (AUD-124).
        self._explored_stages: list[str] = []
        self._notif_bg: pygame.Surface | None = None
        self._notif_font: pygame.font.Font | None = None
        self._bus: EventBus | None = None
        self._init_achievements()

    # ── bus binding (AUD-019) ──────────────────────────────────

    def bind_bus(self, bus: EventBus | None) -> None:
        """Attach the event bus this system should publish and listen on.

        Re-binding while subscribed moves the subscriptions across, so a scene
        transition that swaps buses cannot leave handlers on the old one.
        """
        if bus is self._bus:
            return
        was_subscribed = self._subscribed
        if was_subscribed:
            self.unsubscribe_events()
        self._bus = bus
        if was_subscribed:
            self.subscribe_events()

    @property
    def _font(self) -> pygame.font.Font:
        """Notification font, created on first use (AUD-030)."""
        if self._notif_font is None:
            if not pygame.font.get_init():
                pygame.font.init()
            self._notif_font = pygame.font.Font(None, 14)
        return self._notif_font

    def _init_achievements(self) -> None:
        """Registra las definiciones que llegan de `data/achievements.json`.

        AUD-197 — este método escribía las diez definiciones a mano, en inglés
        mezclado con español, en medio del código del motor. Ahora se leen del
        catálogo; la lógica no cambia.
        """
        for definicion in _cargar_definiciones():
            self.register(definicion)

    def register(self, ach: AchievementDef) -> None:
        self._defs[ach.id] = ach
        if ach.id not in self._progress:
            self._progress[ach.id] = AchievementProgress()

    def subscribe_events(self) -> None:
        if self._subscribed or self._bus is None:
            return
        self._subscribed = True
        self._bus.subscribe(Events.ENEMY_DIED, self._on_enemy_died)
        self._bus.subscribe(Events.VFX_PARRY, self._on_parry)

    def unsubscribe_events(self) -> None:
        if not self._subscribed:
            return
        self._subscribed = False
        if self._bus is not None:
            self._bus.unsubscribe(Events.ENEMY_DIED, self._on_enemy_died)
            self._bus.unsubscribe(Events.VFX_PARRY, self._on_parry)

    def _on_enemy_died(self, **data: object) -> None:
        self._stats["enemies_killed"] = self._stats.get("enemies_killed", 0) + 1
        self.progress("exterminator")
        self.progress("first_blood")

    def _on_parry(self, **data: object) -> None:
        self._stats["parries"] = self._stats.get("parries", 0) + 1
        self.progress("parry_master")

    def progress(self, achievement_id: str, amount: int = 1) -> None:
        ach = self._defs.get(achievement_id)
        prog = self._progress.get(achievement_id)
        if ach is None or prog is None or prog.unlocked:
            return
        prog.current = min(prog.current + amount, ach.target)
        if self._bus is not None:
            self._bus.emit(
                Events.ACHIEVEMENT_PROGRESS,
                achievement_id=achievement_id,
                progress=prog.current,
                target=ach.target,
            )
        if prog.current >= ach.target:
            self._unlock(achievement_id)

    def _unlock(self, achievement_id: str) -> None:
        ach = self._defs.get(achievement_id)
        prog = self._progress.get(achievement_id)
        if ach is None or prog is None:
            return
        prog.unlocked = True
        self._notifications.append({
            "id": ach.id,
            "name": ach.name,
            "description": ach.description,
            "timer": 3.0,
        })
        if self._bus is not None:
            self._bus.emit(
                Events.ACHIEVEMENT_UNLOCKED,
                achievement_id=ach.id,
                name=ach.name,
            )

    def _set_progress(self, achievement_id: str, value: int) -> None:
        prog = self._progress.get(achievement_id)
        if prog is not None:
            prog.current = value

    def is_unlocked(self, achievement_id: str) -> bool:
        prog = self._progress.get(achievement_id)
        return prog is not None and prog.unlocked

    def mark_survived_low_health(self) -> None:
        if not self.is_unlocked("survivor"):
            self._set_progress("survivor", 1)
            self._unlock("survivor")

    def mark_untouchable(self) -> None:
        if not self.is_unlocked("untouchable"):
            self._set_progress("untouchable", 1)
            self._unlock("untouchable")

    def mark_speed_demon(self) -> None:
        if not self.is_unlocked("speed_demon"):
            self._set_progress("speed_demon", 1)
            self._unlock("speed_demon")

    def mark_air_assault(self, combo_count: int) -> None:
        if not self.is_unlocked("air_assault") and combo_count >= 3:
            self._set_progress("air_assault", 1)
            self._unlock("air_assault")

    def mark_combo_king(self, combo_count: int) -> None:
        if not self.is_unlocked("combo_king") and combo_count >= 10:
            self._set_progress("combo_king", 1)
            self._unlock("combo_king")

    def mark_explorer(self, stage_id: str) -> None:
        """AUD-124 — `_stats` está declarado `dict[str, int]` y guardaba una lista.

        La línea era::

            self._stats["explored_stages"] = seen   # seen: list[str]

        Funcionaba, porque Python no comprueba anotaciones en tiempo de
        ejecución. Pero la anotación mentía, y una anotación que miente es
        peor que no tenerla: quien lee `dict[str, int]` asume que puede sumar
        cualquier valor del diccionario, y `_stats["explored_stages"] + 1`
        revienta en la partida de alguien.

        Los escenarios visitados no son un contador: son un **conjunto**. Ahora
        viven en su propio atributo, con el tipo que les corresponde. El
        formato en disco no cambia —se siguen serializando dentro de `stats`—
        para no invalidar los logros de quien ya tenga partida.
        """
        if self.is_unlocked("explorer"):
            return
        if stage_id and stage_id not in self._explored_stages:
            self._explored_stages.append(stage_id)
        self._set_progress("explorer", len(self._explored_stages))
        # AUD-197 — el objetivo ya no es una constante del código: se lee del
        # catálogo, la misma fuente de la cifra que ve el jugador.
        objetivo = self._defs.get("explorer")
        if objetivo is not None and len(self._explored_stages) >= objetivo.target:
            self._unlock("explorer")

    @property
    def achievements(self) -> list[tuple[AchievementDef, AchievementProgress]]:
        return [(self._defs[aid], self._progress[aid]) for aid in self._defs]

    def save(self) -> None:
        destino = _ruta_de_logros()
        data = {
            "progress": {
                aid: p.model_dump()
                for aid, p in self._progress.items()
            },
            # El formato en disco no cambia: los escenarios visitados
            # siguen viajando dentro de `stats` para no invalidar los
            # logros de quien ya tenga partida (AUD-124).
            "stats": {**self._stats, "explored_stages": self._explored_stages},
        }
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))

    def load(self) -> None:
        # AUD-200 — antes de leer, se vuelve a cero: este sistema es un
        # singleton de proceso, y cambiar de estudiante sin limpiar dejaría
        # los logros del anterior mezclados con los del nuevo.
        self._progress = {aid: AchievementProgress() for aid in self._defs}
        self._explored_stages = []
        self._stats = {}
        destino = _ruta_de_logros()
        try:
            raw = destino.read_bytes()
            data = orjson.loads(raw)
            saved_progress = data.get("progress", {}) if isinstance(data, dict) else {}
            for aid, pdata in saved_progress.items():
                if aid in self._progress:
                    self._progress[aid] = AchievementProgress.model_validate(pdata)
            guardado = data.get("stats", {}) if isinstance(data, dict) else {}
            if isinstance(guardado, dict):
                visitados = guardado.pop("explored_stages", [])
                self._explored_stages = [
                    s for s in visitados if isinstance(s, str)
                ] if isinstance(visitados, list) else []
                self._stats = {
                    k: v for k, v in guardado.items() if isinstance(v, int)
                }
        # AUD-100 — la corrupción se tragaba en silencio.
        #
        # `orjson.JSONEncodeError` **es `TypeError`**, y codificar no puede
        # fallar dentro de un `loads`: estaba de más. Lo que de verdad atrapa
        # un fichero corrupto es `ValueError`, del que `orjson.JSONDecodeError`
        # hereda. Así que el `except` funcionaba, pero por una razón distinta
        # de la que aparentaba.
        #
        # El defecto real era el silencio. Los logros de un semestre se perdían sin una línea en
        # el registro, y el estudiante veía todo bloqueado otra vez sin ninguna pista de por
        # qué. `ProgresoAcademico.cargar` ya avisaba en el mismo caso; tres
        # sitios del proyecto hacían lo contrario ante el mismo problema.
        except FileNotFoundError:
            logger.debug(
                "achievements: sin fichero previo en %s; se empieza de cero",
                destino,
            )
        except (ValueError, TypeError):
            logger.warning(
                "achievements: %s ilegible; se empieza de cero",
                destino, exc_info=True,
            )

    def get_all_achievements(self) -> list[tuple[AchievementDef, AchievementProgress]]:
        return [(self._defs[aid], self._progress[aid])
                for aid in self._defs
                if aid in self._progress]

    def update_notifications(self, dt: float) -> None:
        if self._current_notify is not None:
            self._current_notify["timer"] -= dt
            if self._current_notify["timer"] <= 0:
                self._current_notify = None
        if self._current_notify is None and self._notifications:
            self._current_notify = self._notifications.pop(0)

    def draw_notifications(self, surface: pygame.Surface) -> None:
        if self._current_notify is None:
            return
        n = self._current_notify
        w = settings.INTERNAL_WIDTH
        bar_w = 240
        bar_h = 32
        bx = (w - bar_w) // 2
        by = 60

        if self._notif_bg is None or self._notif_bg.get_size() != (bar_w, bar_h):
            self._notif_bg = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        bg = self._notif_bg
        bg.fill((0, 0, 0, 200))
        surface.blit(bg, (bx, by))

        pygame.draw.rect(surface, (255, 215, 0), (bx, by, bar_w, bar_h), 1)

        title = self._font.render(f"Achievement Unlocked: {n['name']}", True, (255, 215, 0))
        surface.blit(title, (bx + 8, by + 3))
        desc = self._font.render(n['description'], True, (200, 200, 200))
        surface.blit(desc, (bx + 8, by + 17))

    @classmethod
    def _reset_instance(cls) -> None:
        cls._instance = None

    def get_progress(self, achievement_id: str) -> int:
        prog = self._progress.get(achievement_id)
        return prog.current if prog else 0
