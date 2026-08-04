"""
StudentLoginScene — dónde el estudiante escribe su correo de la universidad.

AUD-098 — el eslabón que faltaba
================================
AUD-095 dejó el progreso académico funcionando y probado: se guarda por
estudiante, en JSON, al terminar cada examen. Y sin embargo **nada volvía a
leerlo nunca**. `SesionAcademica.entrar()` sólo se llamaba desde las pruebas,
no había pantalla que pidiera el correo, y `App` no reanudaba nada al
arrancar.

El efecto para un estudiante: aprobar cinco unidades, cerrar el juego, y
volver a encontrarse el temario entero bloqueado, con sus notas intactas en el
disco pero inalcanzables.

Es el mismo defecto que la iluminación que no iluminaba un solo píxel y que
las trece demos que dibujaban en una esquina: código correcto, probado en
aislamiento, que no llegaba a la pantalla. Lo escribo aquí porque es la
tercera vez esta sesión y conviene que quede por escrito en el sitio donde
alguien lo va a leer.

Sobre la entrada de texto
-------------------------
Se leen los eventos `KEYDOWN` en `process_events` y no el estado de teclas de
`InputManager`. El estado dice *qué teclas están pulsadas ahora*, que no basta
para escribir: no distingue una pulsación de la misma tecla mantenida, ni
respeta la distribución del teclado. `event.unicode` sí, y es lo que hace que
una eñe o un acento acaben en el buffer tal y como se teclearon.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_ERROR,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_MEDIUM,
    FONT_SMALL,
    draw_bottom_bar,
    draw_top_bar,
)
from src.engine.scenes.demo_layout import area_de_contenido
from src.engine.utils.asset_loader import AssetLoader
from src.framework.academic.progress import es_correo_valido
from src.framework.academic.sesion import SesionAcademica

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

#: Longitud máxima del correo. Suficiente para cualquier dirección
#: universitaria real y corta como para que quepa en pantalla de una vez.
MAX_LONGITUD = 64

#: Caracteres admitidos. No se filtra por elegancia: un correo con un espacio
#: o una comilla acabaría en un nombre de fichero, y aunque
#: `nombre_de_fichero()` ya lo sanea, es mejor que el estudiante vea que ese
#: carácter no entra a que descubra luego que su correo se guardó de otra
#: forma.
PERMITIDOS = set("abcdefghijklmnopqrstuvwxyz0123456789@._-+")


class StudentLoginScene(BaseScene):
    """Pide el correo, carga el progreso y vuelve al temario."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._buffer: str = ""
        self._mensaje: str = ""
        self._cursor_visible: bool = True
        self._cursor_timer: float = 0.0
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM,
        )
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL,
        )

    # -- ciclo de vida ---------------------------------------------
    def on_enter(self) -> None:
        # Se precarga el correo actual: lo normal en un aula es corregir una
        # letra, no volver a escribirlo entero.
        self._buffer = SesionAcademica.instancia().correo
        self._mensaje = ""
        self._cursor_visible = True
        self._cursor_timer = 0.0

    def on_exit(self) -> None:
        pass

    # -- entrada ---------------------------------------------------
    def process_events(self, events: list[pygame.event.Event]) -> None:
        for evento in events:
            if evento.type != pygame.KEYDOWN:
                continue
            if evento.key == pygame.K_BACKSPACE:
                self._buffer = self._buffer[:-1]
                self._mensaje = ""
                continue
            caracter = (getattr(evento, "unicode", "") or "").lower()
            if caracter in PERMITIDOS and len(self._buffer) < MAX_LONGITUD:
                self._buffer += caracter
                self._mensaje = ""

    def update(self, dt: float) -> None:
        self._cursor_timer += dt
        if self._cursor_timer >= 0.5:
            self._cursor_timer = 0.0
            self._cursor_visible = not self._cursor_visible

        im = self.input
        if im is None:
            return

        if im.is_action_just_pressed(Action.CONFIRM):
            self._confirmar()
        elif im.is_action_just_pressed(Action.CANCEL):
            self._volver()
        elif im.is_raw_key_pressed(pygame.K_DELETE):
            self._salir_de_la_sesion()

    def _confirmar(self) -> None:
        if SesionAcademica.instancia().entrar(self._buffer):
            self._recargar_logros()
            self.context.event_bus.emit(Events.SFX_MENU_CONFIRM)
            self._volver()
            return
        self.context.event_bus.emit(Events.SFX_MENU_CANCEL)
        self._mensaje = (
            "Eso no tiene forma de correo. Hace falta algo como "
            "nombre@universidad.edu"
        )

    def _salir_de_la_sesion(self) -> None:
        """Deja de recordar a este estudiante. No borra sus notas."""
        SesionAcademica.instancia().salir()
        self._recargar_logros()
        self._buffer = ""
        self._mensaje = "Sesión cerrada. El progreso guardado sigue en el disco."
        self.context.event_bus.emit(Events.SFX_MENU_CANCEL)

    def _recargar_logros(self) -> None:
        """Vuelve a leer los logros del perfil recién activado.

        AUD-200 — los logros viven en un fichero por estudiante. Al cambiar de
        perfil hay que pedirle al sistema que recargue desde el fichero del
        nuevo dueño; si no, la pantalla de logros mostraría los del anterior,
        que siguen en la memoria del singleton.
        """
        from src.engine.core.achievements import AchievementSystem

        AchievementSystem.get_instance().load()

    def _volver(self) -> None:
        from src.engine.scenes.demo_menu_scene import DemoMenuScene

        self.context.scene_manager.replace(DemoMenuScene(self.context))

    # -- dibujado --------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "IDENTIFICACIÓN", "ESTUDIANTE")

        area = area_de_contenido()
        cx = area.centerx
        y = area.y + 40

        explicacion = [
            "Escribe el correo de la universidad para que tu progreso se guarde.",
            "Sin identificarte también puedes jugar: no se guardará nada.",
        ]
        for linea in explicacion:
            render = self._font_small.render(linea, True, COLOR_TEXT)
            surface.blit(render, (cx - render.get_width() // 2, y))
            y += render.get_height() + 6
        y += 26

        # Campo de texto
        ancho_campo = min(560, area.w - 80)
        campo = pygame.Rect(cx - ancho_campo // 2, y, ancho_campo, 46)
        valido = es_correo_valido(self._buffer)
        borde = COLOR_ACCENT if valido else (90, 90, 110)
        pygame.draw.rect(surface, (18, 18, 34), campo, border_radius=4)
        pygame.draw.rect(surface, borde, campo, 2, border_radius=4)

        texto = self._buffer + ("_" if self._cursor_visible else " ")
        render = self._font_medium.render(texto, True, COLOR_HIGHLIGHT)
        surface.blit(render, (campo.x + 12, campo.centery - render.get_height() // 2))
        y = campo.bottom + 16

        # Estado: se dice si el correo vale **antes** de pulsar Enter, que es
        # cuando sirve de algo.
        if self._buffer:
            estado = "Correo válido." if valido else "Todavía no es un correo completo."
            render = self._font_small.render(
                estado, True, (110, 205, 140) if valido else (170, 170, 185),
            )
            surface.blit(render, (cx - render.get_width() // 2, y))
            y += render.get_height() + 10

        if self._mensaje:
            render = self._font_small.render(self._mensaje, True, COLOR_ERROR)
            surface.blit(render, (cx - render.get_width() // 2, y))
            y += render.get_height() + 10

        sesion = SesionAcademica.instancia()
        if sesion.identificado:
            aprobadas = len(sesion.progreso.unidades_aprobadas())
            actual = self._font_small.render(
                f"Sesión actual: {sesion.correo} · {aprobadas} unidad(es) aprobadas",
                True, COLOR_ACCENT,
            )
            surface.blit(actual, (cx - actual.get_width() // 2, y + 14))

        draw_bottom_bar(
            surface,
            "Escribe el correo  |  ENTER: Entrar  |  SUPR: Cerrar sesión  |  ESC: Volver",
        )
