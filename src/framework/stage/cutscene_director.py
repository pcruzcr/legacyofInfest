"""
Module: cutscene_director
System: framework.stage
Academic Unit: N/A
Description: AUD-136 (D3) — quien decide cuándo se reproduce una escena, si
quita el mando al jugador y qué pasa al saltarla.

El hueco que llenaba
=====================
`CutsceneSystem` estaba escrito y probado, y **ninguna escena del motor lo
ejecutaba**. El único sitio del proyecto que reproducía una cutscene era
`Stage0`, a mano, con tres líneas que apagaban el guion tocando `_active`
—un atributo privado— desde fuera:

.. code-block:: python

    if im.is_action_just_pressed(Action.CANCEL):
        self._cutscene._active = False
        self._cutscene = None

Eso no es saltar una escena: es tirarla a la basura a medias. Si el guion
movía al jugador hasta la puerta, quien pulsaba CANCEL se quedaba donde
estaba, con la escena a medio ejecutar. Y cada escenario que quisiera una
cutscene tenía que reescribir esas tres líneas, con el mismo defecto.

Este director es el sitio único donde eso se decide bien.
"""
from __future__ import annotations

import logging
from typing import Any

import pygame

from src.framework.stage.cutscene_guion import ContextoDeGuion, analizar_guion
from src.framework.stage.cutscene_system import CutsceneScript

logger = logging.getLogger(__name__)

#: Evento del bus que emiten los `EventTrigger` del mapa (AUD-132), con el
#: nombre del evento del estudiante en `nombre=`.
_EVENTO_DISPARADOR = "INTERACT_TRIGGER_FIRED"


class CutsceneDirector:
    """Dispara, ejecuta y dibuja las escenas de un escenario."""

    def __init__(self, contexto: ContextoDeGuion, escenas: list[Any] | None = None,
                 bus: Any = None, vistas: set[str] | None = None) -> None:
        self._ctx = contexto
        self._escenas = list(escenas or [])
        self._bus = bus
        #: Escenas ya reproducidas, POR REFERENCIA y no por copia.
        #:
        #: Morir recarga el escenario desde el TMX, así que los objetos
        #: `EscenaGuionizada` son nuevos y su `disparada` vuelve a `False`.
        #: Sin una memoria que sobreviva a la recarga, cada muerte reproduce
        #: otra vez la introducción de veinte segundos — la forma más rápida
        #: que hay de que alguien deje un juego. La escena de juego es dueña
        #: del conjunto y se lo presta al director.
        self.vistas: set[str] = vistas if vistas is not None else set()
        self._activos: list[tuple[Any, CutsceneScript]] = []
        self._eventos_vistos: set[str] = set()
        self.errores: list[str] = []
        if bus is not None:
            bus.subscribe(_EVENTO_DISPARADOR, self._al_dispararse)
        self._arrancar_las_del_principio()

    # -- disparo ---------------------------------------------------
    def _al_dispararse(self, nombre: str = "", **_datos: Any) -> None:
        if nombre:
            self._eventos_vistos.add(str(nombre))

    @staticmethod
    def _clave(escena: Any) -> str:
        """Identifica una escena entre recargas del mapa.

        No vale `id()` ni el índice: el TMX se vuelve a leer y los objetos son
        otros. Su sitio y su guion sí son los mismos.
        """
        r = escena.rect
        return f"{r.x},{r.y},{r.width},{r.height}|{escena.guion[:64]}"

    def _ya_vista(self, escena: Any) -> bool:
        return escena.una_vez and self._clave(escena) in self.vistas

    def _arrancar_las_del_principio(self) -> None:
        for escena in self._escenas:
            if escena.al_empezar and not escena.arranca_con and not self._ya_vista(escena):
                self._reproducir(escena)

    def _reproducir(self, escena: Any) -> CutsceneScript | None:
        guion, errores = analizar_guion(
            escena.guion, self._ctx,
            bloquea=escena.bloquea, saltable=escena.saltable,
        )
        if errores:
            self.errores.extend(errores)
        escena.disparada = True
        self.vistas.add(self._clave(escena))
        guion.start()
        self._activos.append((escena, guion))
        return guion

    def reproducir_texto(self, guion: str, *, bloquea: bool = True,
                         saltable: bool = True) -> CutsceneScript:
        """Lanza un guion escrito en código, sin pasar por el TMX.

        Es la puerta para los escenarios que montan su escena en Python —la
        introducción de stage 0, por ejemplo—. Antes cada uno se guardaba su
        `CutsceneScript` y lo apagaba a mano tocando atributos privados; ahora
        pasa por el mismo sitio que las del mapa y hereda el salto que ejecuta
        el final, las bandas y el bloqueo opcional.
        """
        escena, errores = analizar_guion(
            guion, self._ctx, bloquea=bloquea, saltable=saltable)
        if errores:
            self.errores.extend(errores)
            for error in errores:
                logger.warning("guion en código: %s", error)
        escena.start()
        self._activos.append((None, escena))
        return escena

    # -- ciclo -----------------------------------------------------
    @property
    def bloquea(self) -> bool:
        """`True` si alguna escena en curso le ha quitado el mando al jugador.

        Que esto sea una pregunta y no un modo es lo que permite las escenas
        que **no** bloquean: un compañero que grita desde una cornisa mientras
        se sigue jugando. Bloquear siempre convertía cada detalle narrativo en
        una interrupción, y a la tercera el jugador se las salta todas sin
        leerlas.
        """
        return any(g.active and g.bloquea for _e, g in self._activos)

    def update(self, dt: float, jugador_rect: pygame.Rect | None = None,
               saltar: bool = False) -> None:
        if jugador_rect is not None:
            self._comprobar_disparadores(jugador_rect)

        if saltar:
            self.saltar()

        for _escena, guion in list(self._activos):
            guion.update(dt)
        self._activos = [(e, g) for e, g in self._activos if not g.terminada]

    def _comprobar_disparadores(self, jugador: pygame.Rect) -> None:
        for escena in self._escenas:
            if self._ya_vista(escena):
                continue
            if any(e is escena for e, _g in self._activos):
                continue
            if escena.arranca_con:
                if escena.arranca_con in self._eventos_vistos:
                    self._reproducir(escena)
                continue
            if not escena.al_empezar and jugador.colliderect(escena.rect):
                self._reproducir(escena)

    def saltar(self) -> int:
        """Salta las escenas saltables que estén en curso.

        Saltar ejecuta el final de todo lo que quedaba —ver
        `CutsceneScript.saltar`—, así que el mundo queda igual que si se
        hubiera visto entera. Las marcadas `saltable = false` no se saltan:
        existen para las escenas que cambian el estado del nivel de una forma
        que no se puede resumir.
        """
        saltadas = 0
        for _escena, guion in self._activos:
            if guion.active and guion.saltable:
                guion.saltar()
                saltadas += 1
        return saltadas

    def draw(self, surface: pygame.Surface) -> None:
        for _escena, guion in self._activos:
            guion.draw(surface)

    def reset(self) -> None:
        """Al reaparecer: nada en curso y las de «una vez» siguen gastadas.

        Que no se repitan al morir es deliberado, y por eso `vistas` **no** se
        limpia aquí: volver a ver la misma introducción de veinte segundos en
        cada intento es la forma más rápida de que alguien deje un juego.
        """
        self._activos.clear()
        self._eventos_vistos.clear()
