"""
Module: skill_tree_scene
System: engine.scenes
Academic Unit: N/A

La pantalla del árbol de habilidades — AUD-293.

Qué enseña, y por qué en este orden
===================================
Arriba, **los puntos que hay**. Es lo primero que mira quien entra aquí, y una
pantalla de compra que esconde el saldo obliga a salir a buscarlo.

Después, un nodo por línea con su rango actual, su tope y lo que cuesta el
siguiente. Una línea por nodo y no una rejilla de iconos: son tres, y una
rejilla de tres celdas es una lista con más pasos.

Y abajo, **por qué no se puede comprar** lo que está seleccionado, cuando no se
puede. Un botón apagado sin explicación es la forma más rápida de que alguien
concluya que el juego está roto — de ahí que `ArbolDeHabilidades` tenga
`motivo_para_no_comprar` y no un simple booleano.

Lo que esta pantalla no hace
============================
No guarda. Guardar aquí escribiría el árbol en el slot sin el resto del estado
de la partida, y dos escrituras parciales que se pisan son peor que una
completa: la escribe el autoguardado del escenario, que ya vuelca todo junto
(AUD-292).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core.events import Events
from src.engine.core.experience import ExperienceSystem
from src.engine.core.skill_tree import CATALOGO, ArbolDeHabilidades
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.theme import Theme, font
from src.engine.ui.widgets import draw_key_hints, draw_screen

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class SkillTreeScene(BaseScene):
    """Gastar puntos de experiencia en estadísticas."""

    def __init__(self, context: GameContext, *, standalone: bool = True) -> None:
        super().__init__(context)
        self._seleccion: int = 0
        self._mensaje: str = ""
        self._mensaje_timer: float = 0.0
        self._font_nodo = font(Theme.FONT_SMALL)
        self._font_desc = font(Theme.FONT_TINY)
        #: AUD-555 — ver la nota gemela en `InventoryScene.__init__`:
        #: `False` cuando `PausePanel` embebe esta escena como pestaña
        #: "Habilidades", donde Cancelar no puede hacer `pop()` de la pila
        #: real.
        self._standalone = standalone

    def on_enter(self) -> None:
        self._seleccion = 0
        self._mensaje = ""

    def on_exit(self) -> None:
        pass

    # ── entrada ───────────────────────────────────────────────────
    def update(self, dt: float) -> None:
        if self._mensaje_timer > 0.0:
            self._mensaje_timer = max(0.0, self._mensaje_timer - dt)
            if self._mensaje_timer == 0.0:
                self._mensaje = ""

        im = self.input
        if im is None:
            return
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._mover(-1)
        elif im.is_action_just_pressed(Action.MOVE_DOWN):
            self._mover(1)
        elif im.is_action_just_pressed(Action.CONFIRM):
            self._comprar()
        elif im.is_action_just_pressed(Action.CANCEL):
            self._volver()

    def _mover(self, paso: int) -> None:
        self._seleccion = (self._seleccion + paso) % len(CATALOGO)
        self.context.event_bus.emit(Events.SFX_MENU_HOVER)

    def _comprar(self) -> None:
        arbol = ArbolDeHabilidades.get_instance()
        nodo = CATALOGO[self._seleccion]
        motivo = arbol.motivo_para_no_comprar(nodo.id)
        if motivo:
            self._avisar(motivo)
            self.context.event_bus.emit(Events.SFX_MENU_CANCEL)
            return
        arbol.comprar(nodo.id)
        self._avisar(f"{nodo.nombre} sube a rango {arbol.rango(nodo.id)}.")
        self.context.event_bus.emit(Events.SFX_MENU_CONFIRM)

    def _avisar(self, texto: str) -> None:
        self._mensaje = texto
        self._mensaje_timer = 3.0

    def _volver(self) -> None:
        # AUD-533 — mismo arreglo que `InventoryScene`: `pop()` vuelve a
        # quien haya empujado esta pantalla (el título o una partida en
        # pausa), en vez de mandar siempre al título.
        if self._standalone:
            self.context.scene_manager.pop()

    # ── dibujado ──────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface) -> None:
        draw_screen(surface, "ÁRBOL DE HABILIDADES", "EXPERIENCIA")

        arbol = ArbolDeHabilidades.get_instance()
        exp = ExperienceSystem.get_instance()

        y = 46
        saldo = self._font_nodo.render(
            f"Nivel {exp.nivel}  ·  {exp.puntos} punto(s) sin gastar",
            True, Theme.ACCENT,
        )
        surface.blit(saldo, (Theme.SPACE_L, y))
        y += saldo.get_height() + Theme.SPACE_M

        for indice, nodo in enumerate(CATALOGO):
            elegido = indice == self._seleccion
            rango = arbol.rango(nodo.id)
            coste = arbol.coste(nodo.id)

            if not arbol.desbloqueado(nodo.id):
                color = Theme.TEXT_MUTED
            elif elegido:
                color = Theme.ACCENT
            else:
                color = Theme.TEXT

            estado = "MÁX." if arbol.al_maximo(nodo.id) else f"{coste} pto(s)"
            linea = (f"{'>' if elegido else ' '} {nodo.nombre:<12}"
                     f"{rango}/{nodo.rangos}   {estado}")
            surface.blit(self._font_nodo.render(linea, True, color),
                         (Theme.SPACE_L, y))
            y += self._font_nodo.get_height() + 2
            surface.blit(
                self._font_desc.render("    " + nodo.descripcion, True,
                                       Theme.TEXT_MUTED),
                (Theme.SPACE_L, y))
            y += self._font_desc.get_height() + Theme.SPACE_S

        if self._mensaje:
            surface.blit(self._font_desc.render(self._mensaje, True, Theme.ACCENT),
                         (Theme.SPACE_L, y + Theme.SPACE_S))

        draw_key_hints(surface, [("↑↓", "Elegir"), ("Enter", "Subir rango"),
                                 ("Esc", "Volver")])
