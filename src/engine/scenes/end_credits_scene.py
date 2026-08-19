from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.stage_registry import STAGE_ORDER, ruta_del_mapa
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.title_scene import TitleScene
from src.engine.ui.theme import Theme, font
from src.engine.ui.widgets import draw_key_hints

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

#: AUD-548 — quién cuenta como "equipo docente" y no como estudiante. Los
#: mapas del profesorado (stage0, los laboratorios, los jefes de
#: referencia, las variantes de 4-1) declaran uno de estos dos valores
#: —hay una variante con guion y otra con "de" en vez de "of", ambas
#: escritas a mano en distintos generadores— en vez de un nombre propio.
_AUTOR_DOCENTE: frozenset[str] = frozenset({
    "Equipo docente — Legacy of Infest",
    "Equipo docente — Legacy de Infest",
})


def _propiedad(texto: str, clave: str) -> str:
    """El valor de una propiedad de mapa, o cadena vacía si no está.

    Acepta `name="..." value="..."` en cualquier orden de atributos —
    los generadores no son consistentes en cuál va primero.
    """
    patron = re.compile(
        rf'<property[^>]*\bname="{re.escape(clave)}"[^>]*\bvalue="([^"]*)"'
        rf'|<property[^>]*\bvalue="([^"]*)"[^>]*\bname="{re.escape(clave)}"',
    )
    m = patron.search(texto)
    if not m:
        return ""
    return m.group(1) or m.group(2) or ""


def _creditos_por_escenario() -> list[tuple[str, str]]:
    """(nombre de escenario, autor) para cada entrada de `STAGE_ORDER`,
    leído directamente del `author`/`stage_name` de su `.tmx`.

    AUD-548 — antes esta lista era literal: "Student A: Stage 1-1",
    "Student B: Stage 1-2"… nombres inventados que no correspondían a
    quién entregó qué. Los `.tmx` reales ya declaran `author` desde que
    se entregaron (`César Ubáu Calvo`, `Fabrizio E`, `Jose Pablo
    Monestel Cruz`, `Saul`, `Yariel`); nadie los leía. Se lee el XML con
    una expresión regular en vez de `pytmx`/`StageLoader` a propósito:
    los créditos sólo necesitan dos cadenas de las propiedades del mapa,
    y montar el cargador completo —colisión, ECS, validación— por cada
    uno de los 15 escenarios sólo para leer metadatos sería caro y
    innecesario.
    """
    resultado: list[tuple[str, str]] = []
    for stage_id in STAGE_ORDER:
        ruta = ruta_del_mapa(stage_id)
        if ruta is None:
            continue
        try:
            texto = ruta.read_text(encoding="utf-8")
        except OSError:
            continue
        nombre = _propiedad(texto, "stage_name") or stage_id
        autor = _propiedad(texto, "author") or "Equipo docente — Legacy of Infest"
        resultado.append((nombre, autor))
    return resultado


class EndCreditsScene(BaseScene):
    """End Credits screen shown after all stages are complete."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        # AUD-069: escala del tema y su caché.
        self._font_title = font(Theme.FONT_SMALL)
        self._font_text = font(Theme.FONT_TINY)
        self._elapsed: float = 0.0
        self._scroll_y: float = settings.INTERNAL_HEIGHT
        self._done: bool = False

        # AUD-548 — la lista se arma de verdad, no se copia a mano: un
        # escenario nuevo (o un cambio de autor en Tiled) aparece aquí
        # sin tocar este archivo.
        self._lines = self._armar_lineas()

    @staticmethod
    def _armar_lineas() -> list[tuple[str, int]]:
        docentes: list[str] = []
        estudiantes: list[tuple[str, str]] = []
        for nombre, autor in _creditos_por_escenario():
            if autor in _AUTOR_DOCENTE:
                docentes.append(nombre)
            else:
                estudiantes.append((nombre, autor))

        lineas: list[tuple[str, int]] = [
            ("", 0),
            ("LEGACY OF INFEST", 0),
            ("", 0),
            ("A Game by Professor & Students", 0),
            ("", 0),
        ]
        if docentes:
            lineas.append(("--- Professor ---", 0))
            # Una línea por escenario, igual que la de los estudiantes —
            # no un solo renglón con los diez nombres separados por
            # comas, que en una pantalla de créditos que se desplaza se
            # sale del ancho y se lee peor que la lista de abajo.
            for nombre in docentes:
                lineas.append((f"Equipo docente: {nombre}", 0))
            lineas.append(("", 0))
        if estudiantes:
            lineas.append(("--- Students ---", 0))
            for nombre, autor in estudiantes:
                lineas.append((f"{autor}: {nombre}", 0))
            lineas.append(("", 0))
        lineas.append(("Thanks for playing!", 0))
        return lineas

    def on_enter(self) -> None:
        self._elapsed = 0.0
        self._scroll_y = settings.INTERNAL_HEIGHT
        self._done = False

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self._elapsed += dt
        im = self.input
        if im is None:
            return

        if self._done and im.is_action_just_pressed(Action.CONFIRM):
            self.context.scene_manager.replace(TitleScene(self.context))
            return

        if self._elapsed > 1.0 and im.is_action_just_pressed(Action.CONFIRM):
            self._done = True
            return

        self._scroll_y -= 24 * dt

        last_line_y = self._scroll_y + len(self._lines) * 22
        if last_line_y < -50:
            self._done = True

    def draw(self, surface: pygame.Surface) -> None:
        # Los créditos ruedan sobre el fondo del juego, sin cabecera: el título
        # forma parte del propio texto que sube.
        surface.fill(Theme.BG)

        y = int(self._scroll_y)
        for text, _ in self._lines:
            if y < -30 or y > settings.INTERNAL_HEIGHT + 10:
                y += 22
                continue
            # Cuatro niveles de jerarquía con los tres tonos de texto del tema
            # más el acento para el título del juego. Antes eran cuatro colores
            # inventados que no aparecían en ninguna otra pantalla.
            if text.startswith("LEGACY"):
                surf = self._font_title.render(text, True, Theme.ACCENT)
            elif text.startswith("---"):
                surf = self._font_title.render(text, True, Theme.TEXT)
            elif ":" in text:
                surf = self._font_text.render(text, True, Theme.TEXT)
            else:
                surf = self._font_text.render(text, True, Theme.TEXT_MUTED)
            sx = (settings.INTERNAL_WIDTH - surf.get_width()) // 2
            surface.blit(surf, (sx, y))
            y += 22

        if self._done:
            draw_key_hints(surface, [("Enter", "Volver al título")])

