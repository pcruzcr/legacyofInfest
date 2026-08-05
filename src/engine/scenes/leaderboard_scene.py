"""
LeaderboardScene — Local leaderboards for speedrun and boss rush.

Reads from save data to display:
  - Best speedrun times per stage
  - Boss rush completion times
  - Kill counts and scores

AUD-202 — la cabecera de arriba era mentira y llevaba serlo desde siempre
=========================================================================
«Reads from save data» describía una intención, no el código. La pantalla no
abría ningún fichero: las marcas eran literales escritos a mano —«Stage 0:
1:23.45», «Boss Venado: 0:45.12»— presentados como récords del jugador.

Un jugador recién instalado veía tiempos que nunca había hecho. Eso no es un
adorno pendiente de rellenar: es una pantalla que miente sobre la partida de
quien la mira, y enseña a no fiarse del resto de lo que el juego afirma.

Ahora se leen de `saves/speedrun.json`, que es donde `SpeedrunTimer.save()`
escribe al terminar un escenario. Sin partidas jugadas la tabla enseña
`--:--.--`, que es la verdad.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.engine.core.user_settings import user_data_dir
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_MEDIUM,
    FONT_SMALL,
    TOP_BAR_H,
    draw_bottom_bar,
    draw_top_bar,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


MODE_NAMES = ["SPEEDRUN TIMES", "BOSS RUSH", "SCORES"]

logger = logging.getLogger(__name__)

#: De dónde salen las marcas. Módulo y no constante de clase para que una
#: prueba pueda apuntarlo a un directorio temporal sin tocar la partida real.
#:
#: AUD-157 — el speedrun escribe en el directorio del usuario
#: (`user_data_dir()/saves/speedrun.json`), igual que las preferencias, los
#: logros y el bestiario. Esta pantalla leía de `PROJECT_ROOT/saves/`, así que
#: nunca veía las marcas que `registrar_marca()` acababa de escribir: la tabla
#: enseñaba `--:--.--` aunque hubiera récords. La ruta de lectura tiene que ser
#: la misma que la de escritura.
_RUTA_SPEEDRUN: Path = user_data_dir() / "saves" / "speedrun.json"

#: Lo que se enseña cuando de un escenario no hay marca. Se repite tal cual en
#: las tres columnas: un hueco vacío es un dato, y fingir un tiempo no lo es.
SIN_MARCA = "--:--.--"

#: Los escenarios de travesía, en orden, con el nombre que ve el jugador.
_ESCENARIOS: tuple[tuple[str, str], ...] = (
    ("stage0", "Stage 0"),
    ("stage1_1", "Stage 1-1"),
    ("stage1_2", "Stage 1-2"),
    ("stage1_3", "Stage 1-3"),
    ("stage2_1", "Stage 2-1"),
    ("stage2_2", "Stage 2-2"),
    ("stage2_3", "Stage 2-3"),
    ("stage3_1", "Stage 3-1"),
    ("stage3_2", "Stage 3-2"),
    ("stage3_3", "Stage 3-3"),
    ("stage4_1", "Stage 4-1"),
)

_JEFES: tuple[tuple[str, str], ...] = (
    ("stage1_4_boss_venado", "Boss Venado"),
    ("stage2_4_boss_rey", "Rey Terciopelo"),
    ("stage3_4_boss_gavilan", "El Gavilan"),
    ("stage4_2_boss_paburu", "Gran Shaman"),
)


def mejores_tiempos(ruta: Path | None = None) -> dict[str, float]:
    """El mejor tiempo por escenario, leído de la partida.

    Devuelve un diccionario vacío si el fichero no está o no se puede leer: sin
    datos la tabla enseña huecos, que es lo honesto. Nunca lanza — esta pantalla
    tiene que poder abrirse aunque la partida esté corrupta.

    Se queda con el **mínimo** por escenario y no con el último: son marcas, y
    una marca sólo mejora.
    """
    import orjson

    destino = _RUTA_SPEEDRUN if ruta is None else Path(ruta)
    try:
        datos: Any = orjson.loads(destino.read_bytes())
    except (OSError, ValueError) as e:
        logger.debug("récords: no se pudo leer %s (%s)", destino, e)
        return {}

    if not isinstance(datos, dict):
        logger.warning("récords: %s no contiene un objeto JSON", destino)
        return {}

    marcas: dict[str, float] = {}
    for parcial in datos.get("splits", []) or []:
        if not isinstance(parcial, dict):
            continue
        stage_id = parcial.get("stage_id")
        tiempo = parcial.get("time")
        if not isinstance(stage_id, str):
            continue
        if not isinstance(tiempo, (int, float)) or isinstance(tiempo, bool):
            continue
        previo = marcas.get(stage_id)
        if previo is None or tiempo < previo:
            marcas[stage_id] = float(tiempo)
    return marcas


class LeaderboardScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._marcas: dict[str, float] = {}
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)

    def on_enter(self) -> None:
        self._mode = 0
        self._marcas = mejores_tiempos()

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        if im.is_raw_key_pressed(pygame.K_TAB):
            self._mode = (self._mode + 1) % len(MODE_NAMES)
        if im.is_action_just_pressed(Action.CANCEL):
            # AUD-202: volvía al menú de demos académicas. Daba igual mientras
            # no se llegaba aquí desde ningún sitio; ahora se entra desde el
            # título, y salir de los récords a las demos es un desvío que el
            # jugador no pidió.
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))
            return

    def _format_time(self, seconds: float) -> str:
        m = int(seconds // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 100)
        return f"{m}:{s:02d}.{ms:02d}"

    def _lineas_de_tiempos(self) -> list[str]:
        """Las filas de la pestaña actual, con las marcas de la partida.

        Se recarga en cada `on_enter` y no en el constructor: el jugador puede
        haber terminado un escenario entre una visita y otra.
        """
        filas = _ESCENARIOS if self._mode == 0 else _JEFES
        ancho = max(len(nombre) for _, nombre in filas) + 2
        lineas = [
            f"{nombre + ':':<{ancho}}"
            + (self._format_time(self._marcas[stage_id])
               if stage_id in self._marcas else SIN_MARCA)
            for stage_id, nombre in filas
        ]
        if self._mode == 1:
            tiempos = [self._marcas[sid] for sid, _ in _JEFES
                       if sid in self._marcas]
            # El total sólo se enseña con los cuatro jefes batidos: sumar tres
            # y llamarlo «total» sería inventarse el cuarto.
            total = (self._format_time(sum(tiempos))
                     if len(tiempos) == len(_JEFES) else SIN_MARCA)
            lineas += ["", f"{'Boss Rush Total:':<{ancho}}{total}"]
        return lineas

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, f"LEADERBOARDS — {MODE_NAMES[self._mode]}", "RECORDS")

        lines: list[str] = []
        if self._mode in (0, 1):
            lines = self._lineas_de_tiempos()
        else:
            from src.engine.core.achievements import AchievementSystem
            ach = AchievementSystem.get_instance()
            stats = getattr(ach, "_stats", {})
            lines = [
                f"Enemies Killed:  {stats.get('enemies_killed', 0)}",
                f"Parries:         {stats.get('parries', 0)}",
                f"Stages Explored: {len(stats.get('explored_stages', []))}",
            ]

        for i, line in enumerate(lines):
            if not line.strip():
                continue
            color = COLOR_HIGHLIGHT if ":" in line else COLOR_TEXT
            txt = self._font_small.render(f"  {line}", True, color)
            surface.blit(txt, (10, TOP_BAR_H + 16 + i * 16))

        draw_bottom_bar(surface, "  [TAB] Switch  |  ESC: Back to Menu")
