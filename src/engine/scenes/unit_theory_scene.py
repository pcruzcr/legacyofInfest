"""
UnitTheoryScene — la teoría de una unidad, y el examen que la aprueba.

AUD-095
=======
Esto es lo que faltaba entre «la demo dibuja una Bézier» y «el estudiante
sabe de dónde sale el polinomio de Bernstein». La escena tiene dos modos:

- **Teoría.** Los bloques de la unidad: enunciado, fórmula y explicación, más
  el fichero del motor donde esa fórmula está implementada. Esa última línea
  es deliberada: lo que hace valioso este proyecto como material docente es
  que la distancia entre la pizarra y el código que la ejecuta sea de un
  clic.
- **Examen.** Las cinco preguntas de la unidad. Al terminar se registra el
  resultado en la sesión académica, que lo guarda en el acto y —si se
  aprueba— abre la unidad siguiente.

Por qué el examen vive aquí y no dentro de cada demo
----------------------------------------------------
`QuizManager` ya existía y se abría con Q dentro de cuatro laboratorios,
pero no contaba para nada: se contestaba y se olvidaba al salir. Meter el
registro dentro de cada demo habría obligado a repetir el mismo cableado
diez veces y a que cada laboratorio supiera de progreso académico. Aquí hay
un único sitio que conoce el temario, y las demos siguen sin saber que
existe una asignatura.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core.events import Events
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    BOTTOM_BAR_Y,
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
from src.engine.ui.theme import font
from src.framework.academic.curriculum import Unidad, unidad
from src.framework.academic.progress import ACIERTOS_PARA_APROBAR
from src.framework.academic.sesion import SesionAcademica

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

#: Modos de la escena.
TEORIA = "teoria"
EXAMEN = "examen"
RESULTADO = "resultado"

#: Ancho máximo de una línea de texto, en píxeles. Más allá de unos 90
#: caracteres la vista pierde el renglón al volver a la izquierda.
_ANCHO_TEXTO_MAX = 660


def _partir(texto: str, fuente: pygame.font.Font, ancho: int) -> list[str]:
    """Parte un párrafo en líneas que caben en `ancho`.

    Se parte por palabras y respetando los saltos de línea que ya traiga el
    texto: las fórmulas de varias líneas —la rotación 2D, por ejemplo— se
    escriben con `\\n` y tienen que conservarlo.
    """
    lineas: list[str] = []
    for parrafo in texto.split("\n"):
        if not parrafo:
            lineas.append("")
            continue
        actual = ""
        for palabra in parrafo.split(" "):
            prueba = f"{actual} {palabra}".strip()
            if actual and fuente.size(prueba)[0] > ancho:
                lineas.append(actual)
                actual = palabra
            else:
                actual = prueba
        if actual:
            lineas.append(actual)
    return lineas


class UnitTheoryScene(BaseScene):
    """Teoría y examen de una unidad del temario."""

    def __init__(self, context: GameContext, id_unidad: str) -> None:
        super().__init__(context)
        self._id = id_unidad
        self._unidad: Unidad | None = unidad(id_unidad)
        self._modo: str = TEORIA
        self._bloque: int = 0
        self._pregunta: int = 0
        self._opcion: int = 0
        self._respondida: bool = False
        self._aciertos: int = 0
        self._resultado = None
        self._font_medium = font(FONT_MEDIUM)
        self._font_small = font(FONT_SMALL)

    # -- ciclo de vida ---------------------------------------------
    def on_enter(self) -> None:
        self._modo = TEORIA
        self._bloque = 0
        self._reiniciar_examen()

    def on_exit(self) -> None:
        pass

    def _reiniciar_examen(self) -> None:
        self._pregunta = 0
        self._opcion = 0
        self._respondida = False
        self._aciertos = 0
        self._resultado = None

    # -- entrada ---------------------------------------------------
    def update(self, dt: float) -> None:
        im = self.input
        if im is None or self._unidad is None:
            if im is not None and im.is_action_just_pressed(Action.CANCEL):
                self._volver()
            return

        if im.is_action_just_pressed(Action.CANCEL):
            if self._modo == EXAMEN:
                # Salirse a mitad del examen no cuenta como intento: no se
                # penaliza a quien abre por error y cierra.
                self._modo = TEORIA
                self._reiniciar_examen()
            else:
                self._volver()
            return

        if self._modo == TEORIA:
            self._update_teoria(im)
        elif self._modo == EXAMEN:
            self._update_examen(im)
        elif self._modo == RESULTADO and im.is_action_just_pressed(Action.CONFIRM):
            self._volver()

    def _update_teoria(self, im: object) -> None:
        total = len(self._unidad.teoria) if self._unidad else 0
        if im.is_raw_key_pressed(pygame.K_RIGHT) and self._bloque < total - 1:
            self._bloque += 1
            self.context.event_bus.emit(Events.SFX_MENU_HOVER)
        if im.is_raw_key_pressed(pygame.K_LEFT) and self._bloque > 0:
            self._bloque -= 1
            self.context.event_bus.emit(Events.SFX_MENU_HOVER)
        if im.is_action_just_pressed(Action.CONFIRM):
            self._modo = EXAMEN
            self._reiniciar_examen()
            self.context.event_bus.emit(Events.SFX_MENU_CONFIRM)

    def _update_examen(self, im: object) -> None:
        assert self._unidad is not None
        preguntas = self._unidad.preguntas
        if not preguntas:
            self._modo = TEORIA
            return
        actual = preguntas[self._pregunta]

        if self._respondida:
            if im.is_action_just_pressed(Action.CONFIRM):
                self._avanzar_pregunta()
            return

        if im.is_raw_key_pressed(pygame.K_DOWN):
            self._opcion = (self._opcion + 1) % len(actual.opciones)
            self.context.event_bus.emit(Events.SFX_MENU_HOVER)
        if im.is_raw_key_pressed(pygame.K_UP):
            self._opcion = (self._opcion - 1) % len(actual.opciones)
            self.context.event_bus.emit(Events.SFX_MENU_HOVER)
        if im.is_action_just_pressed(Action.CONFIRM):
            self._respondida = True
            if self._opcion == actual.correcta:
                self._aciertos += 1
                self.context.event_bus.emit(Events.SFX_MENU_CONFIRM)
            else:
                self.context.event_bus.emit(Events.SFX_MENU_CANCEL)

    def _avanzar_pregunta(self) -> None:
        assert self._unidad is not None
        self._respondida = False
        self._opcion = 0
        if self._pregunta + 1 < len(self._unidad.preguntas):
            self._pregunta += 1
            return
        # Fin del examen: se registra una sola vez, aquí.
        self._resultado = SesionAcademica.instancia().registrar_examen(
            self._id, self._aciertos,
        )
        self._modo = RESULTADO

    def _volver(self) -> None:
        from src.engine.scenes.demo_menu_scene import DemoMenuScene
        self.context.scene_manager.replace(DemoMenuScene(self.context))

    # -- dibujado --------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        if self._unidad is None:
            draw_top_bar(surface, "UNIDAD DESCONOCIDA", "—")
            draw_bottom_bar(surface, "ESC: Volver")
            return

        draw_top_bar(surface, self._unidad.titulo.upper(), f"UNIDAD {self._unidad.numero}")
        if self._modo == TEORIA:
            self._draw_teoria(surface)
        elif self._modo == EXAMEN:
            self._draw_examen(surface)
        else:
            self._draw_resultado(surface)

    def _draw_teoria(self, surface: pygame.Surface) -> None:
        assert self._unidad is not None
        area = area_de_contenido()
        ancho = min(_ANCHO_TEXTO_MAX, area.w - 80)
        x = area.centerx - ancho // 2
        y = area.y + 20

        bloques = self._unidad.teoria
        if not bloques:
            surface.blit(self._font_small.render("Sin teoría cargada.", True, COLOR_TEXT), (x, y))
            draw_bottom_bar(surface, "ENTER: Examen  |  ESC: Volver")
            return

        bloque = bloques[self._bloque]
        cabecera = self._font_small.render(
            f"{self._bloque + 1} de {len(bloques)}", True, COLOR_ACCENT,
        )
        surface.blit(cabecera, (x, y))
        y += cabecera.get_height() + 10

        titulo = self._font_medium.render(bloque.titulo, True, COLOR_HIGHLIGHT)
        surface.blit(titulo, (x, y))
        y += titulo.get_height() + 12

        # La fórmula, sobre su propio recuadro para que destaque del párrafo.
        lineas_formula = _partir(bloque.formula, self._font_medium, ancho - 24)
        alto_formula = len(lineas_formula) * (self._font_medium.get_height() + 4) + 16
        pygame.draw.rect(surface, (18, 18, 34), pygame.Rect(x, y, ancho, alto_formula),
                         border_radius=4)
        pygame.draw.rect(surface, (54, 54, 84), pygame.Rect(x, y, ancho, alto_formula),
                         1, border_radius=4)
        yf = y + 8
        for linea in lineas_formula:
            surface.blit(self._font_medium.render(linea, True, COLOR_ACCENT), (x + 12, yf))
            yf += self._font_medium.get_height() + 4
        y += alto_formula + 14

        salto = self._font_small.get_height() + 3
        for linea in _partir(bloque.explicacion, self._font_small, ancho):
            if y + salto > BOTTOM_BAR_Y - 46:
                break
            surface.blit(self._font_small.render(linea, True, COLOR_TEXT), (x, y))
            y += salto

        codigo = self._font_small.render(f"En el código: {bloque.codigo}", True, (140, 140, 160))
        surface.blit(codigo, (x, BOTTOM_BAR_Y - 40))

        draw_bottom_bar(surface, "←→: Cambiar de idea  |  ENTER: Hacer el examen  |  ESC: Volver")

    def _draw_examen(self, surface: pygame.Surface) -> None:
        assert self._unidad is not None
        preguntas = self._unidad.preguntas
        actual = preguntas[self._pregunta]
        area = area_de_contenido()
        ancho = min(_ANCHO_TEXTO_MAX, area.w - 80)
        x = area.centerx - ancho // 2
        y = area.y + 20

        contador = self._font_small.render(
            f"Pregunta {self._pregunta + 1} de {len(preguntas)}   ·   "
            f"aciertos: {self._aciertos}", True, COLOR_ACCENT,
        )
        surface.blit(contador, (x, y))
        y += contador.get_height() + 14

        for linea in _partir(actual.enunciado, self._font_medium, ancho):
            surface.blit(self._font_medium.render(linea, True, COLOR_HIGHLIGHT), (x, y))
            y += self._font_medium.get_height() + 4
        y += 12

        for i, opcion in enumerate(actual.opciones):
            elegida = i == self._opcion
            if self._respondida:
                if i == actual.correcta:
                    color = (110, 205, 140)
                elif elegida:
                    color = COLOR_ERROR
                else:
                    color = (110, 110, 125)
            else:
                color = COLOR_HIGHLIGHT if elegida else COLOR_TEXT
            marca = "▸ " if elegida else "  "
            render = self._font_small.render(f"{marca}{opcion}", True, color)
            surface.blit(render, (x + 12, y))
            y += render.get_height() + 8

        if self._respondida:
            y += 10
            veredicto = "Correcto." if self._opcion == actual.correcta else "No era ésa."
            surface.blit(self._font_medium.render(veredicto, True, COLOR_ACCENT), (x, y))
            y += self._font_medium.get_height() + 6
            salto = self._font_small.get_height() + 3
            for linea in _partir(actual.porque, self._font_small, ancho):
                if y + salto > BOTTOM_BAR_Y - 10:
                    break
                surface.blit(self._font_small.render(linea, True, COLOR_TEXT), (x, y))
                y += salto

        pie = ("ENTER: Siguiente  |  ESC: Dejarlo (no cuenta)"
               if self._respondida
               else "↑↓: Elegir  |  ENTER: Responder  |  ESC: Dejarlo (no cuenta)")
        draw_bottom_bar(surface, pie)

    def _draw_resultado(self, surface: pygame.Surface) -> None:
        assert self._unidad is not None
        area = area_de_contenido()
        total = len(self._unidad.preguntas)
        aprobado = self._aciertos >= ACIERTOS_PARA_APROBAR

        titulo = self._font_medium.render(
            f"{self._aciertos} de {total}", True,
            (110, 205, 140) if aprobado else COLOR_ERROR,
        )
        surface.blit(titulo, (area.centerx - titulo.get_width() // 2, area.centery - 60))

        if aprobado:
            mensaje = "Unidad aprobada."
        else:
            mensaje = f"Hacen falta {ACIERTOS_PARA_APROBAR}. Repasa la teoría y vuelve a intentarlo."
        render = self._font_small.render(mensaje, True, COLOR_TEXT)
        surface.blit(render, (area.centerx - render.get_width() // 2, area.centery - 16))

        siguiente = getattr(self._resultado, "desbloqueada", None)
        if siguiente:
            desbloqueada = unidad(siguiente)
            if desbloqueada is not None:
                aviso = self._font_small.render(
                    f"Se abre la unidad {desbloqueada.numero} · {desbloqueada.titulo}",
                    True, COLOR_ACCENT,
                )
                surface.blit(aviso, (area.centerx - aviso.get_width() // 2, area.centery + 16))

        draw_bottom_bar(surface, "ENTER o ESC: Volver al temario")
