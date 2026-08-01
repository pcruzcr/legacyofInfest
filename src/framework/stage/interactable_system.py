"""
El sistema que hace vivir a recogibles, cerraduras, cofres y disparadores.

F4.1 — qué hace y qué no
========================
Toma el estado que declaró el TMX (`framework.stage.interactables`), lo cruza
con la posición del jugador y con el botón de agarrar, y emite eventos.

**No dibuja.** El dibujado va en `DrawingSystem`, donde está el resto del
orden de capas. Separarlo permite probar toda la lógica de llaves y puertas
sin abrir una ventana, que es como se han escrito las pruebas de este módulo.

Las cerraduras y la colisión
----------------------------
Una puerta cerrada tiene que ser sólida, y al abrirse dejar de serlo. En vez
de manipular `stage.collision_rects` —una lista que el cargador construye y
varios sistemas leen— el sistema publica `rects_solidos()`, y la escena la
suma a las suyas en cada fotograma. Mutar una lista compartida para simular un
cambio de estado es la clase de atajo que después nadie sabe deshacer.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.framework.stage.interactables import (
    Cerradura,
    Cofre,
    Disparador,
    Llavero,
    Recogible,
    alcanza,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.event_bus import EventBus

#: Eventos que emite este sistema. Se nombran aquí y no en `engine.core.events`
#: porque son del framework: un juego construido sobre este motor podría no
#: tener llaves.
EVENTO_RECOGIDO = "INTERACT_ITEM_PICKED"
EVENTO_ABIERTA = "INTERACT_LOCK_OPENED"
EVENTO_BLOQUEADA = "INTERACT_LOCK_BLOCKED"
EVENTO_COFRE = "INTERACT_CHEST_OPENED"
EVENTO_DISPARADOR = "INTERACT_TRIGGER_FIRED"


class InteractableSystem:
    """Recogibles, cerraduras, cofres y disparadores de un escenario."""

    def __init__(
        self,
        recogibles: list[Recogible] | None = None,
        cerraduras: list[Cerradura] | None = None,
        cofres: list[Cofre] | None = None,
        disparadores: list[Disparador] | None = None,
        bus: EventBus | None = None,
    ) -> None:
        self.recogibles = list(recogibles or [])
        self.cerraduras = list(cerraduras or [])
        self.cofres = list(cofres or [])
        self.disparadores = list(disparadores or [])
        self.llavero = Llavero()
        self._bus = bus
        #: Último mensaje para la interfaz. La escena lo lee y lo muestra.
        self.mensaje: str = ""
        self.mensaje_timer: float = 0.0

    # -- consulta --------------------------------------------------
    def rects_solidos(self) -> list[pygame.Rect]:
        """Las cerraduras que siguen cerradas bloquean el paso."""
        return [c.rect for c in self.cerraduras if not c.abierta]

    @property
    def hay_algo_que_hacer(self) -> bool:
        """¿Queda alguna interacción pendiente? Útil para el calificador."""
        return bool(
            [r for r in self.recogibles if not r.recogido]
            or [c for c in self.cerraduras if not c.abierta]
            or [c for c in self.cofres if not c.abierto]
            or [d for d in self.disparadores if not (d.una_vez and d.disparado)],
        )

    # -- ciclo -----------------------------------------------------
    def update(self, dt: float, jugador: pygame.Rect, usar: bool = False) -> None:
        """Un fotograma. `usar` es el botón de agarrar recién pulsado."""
        if self.mensaje_timer > 0.0:
            self.mensaje_timer -= dt
            if self.mensaje_timer <= 0.0:
                self.mensaje = ""

        self._recoger(jugador, usar)
        self._disparar(jugador, usar)
        self._cerrar_las_cronometradas(dt, jugador)
        if usar:
            self._abrir_cerraduras(jugador)
            self._abrir_cofres(jugador)

    # -- reglas ----------------------------------------------------
    def _recoger(self, jugador: pygame.Rect, usar: bool) -> None:
        for objeto in self.recogibles:
            if objeto.recogido:
                continue
            # Los automáticos se cogen al tocarlos; los demás piden el botón y
            # admiten el alcance, para que no haya que estar encima exacto.
            if objeto.automatico:
                if not objeto.rect.colliderect(jugador):
                    continue
            elif not (usar and alcanza(jugador, objeto.rect)):
                continue

            objeto.recogido = True
            self.llavero.coger(objeto.item_id)
            self._avisar(objeto.mensaje or f"Has cogido: {objeto.item_id}")
            self._emitir(EVENTO_RECOGIDO, item_id=objeto.item_id)

    def abrir_por_evento(self, evento: str) -> int:
        """Abre las cerraduras que declaran `abre_con_evento == evento`.

        AUD-132 — el receptor que faltaba.

        `Disparador` emitía su evento al bus y **nadie escuchaba**. Un
        estudiante podía poner un interruptor en Tiled, verlo aparecer en el
        registro y no conseguir que abriera nada sin escribir Python. El
        circuito se cierra aquí: interruptor → bus → puerta, con dos
        propiedades en Tiled y ninguna línea de código.

        Devuelve cuántas se abrieron, para que el llamante pueda avisar o no.
        """
        if not evento:
            return 0
        abiertas = 0
        for cerradura in self.cerraduras:
            if cerradura.abierta or cerradura.abre_con_evento != evento:
                continue
            cerradura.abrir()
            abiertas += 1
            self._emitir(EVENTO_ABIERTA, key_id=cerradura.key_id,
                         clase=cerradura.clase)
            if cerradura.evento_al_abrir:
                self._emitir(cerradura.evento_al_abrir)
        if abiertas:
            self._avisar(f"Se ha abierto algo. ({abiertas})")
        return abiertas

    def _cerrar_las_cronometradas(self, dt: float, jugador: pygame.Rect) -> None:
        """Cierra las puertas cuyo temporizador se agota.

        **Nunca sobre el jugador.** Cerrar una puerta con el jugador dentro lo
        aplastaría contra la geometría o lo dejaría atrapado dentro del
        rectángulo sólido, y las dos cosas se leen como un fallo del juego.
        Si está encima, el temporizador se prorroga hasta que salga: es lo que
        el jugador espera y no requiere que él lo entienda.
        """
        for cerradura in self.cerraduras:
            if not cerradura.abierta or cerradura._cierre <= 0.0:
                continue
            if cerradura.rect.colliderect(jugador):
                continue
            if cerradura.avanzar(dt):
                self._avisar(f"La {cerradura.clase} se ha cerrado.")

    def _abrir_cerraduras(self, jugador: pygame.Rect) -> None:
        for cerradura in self.cerraduras:
            if cerradura.abierta or not alcanza(jugador, cerradura.rect):
                continue
            if not self.llavero.tiene(cerradura.key_id):
                self._avisar(
                    cerradura.mensaje_bloqueado
                    or f"Necesitas «{cerradura.key_id}» para abrir esta {cerradura.clase}.",
                )
                self._emitir(EVENTO_BLOQUEADA, key_id=cerradura.key_id)
                continue

            cerradura.abrir(temporal=False)
            if cerradura.consume_llave:
                self.llavero.gastar(cerradura.key_id)
            self._avisar(f"{cerradura.clase.capitalize()} abierta.")
            self._emitir(EVENTO_ABIERTA, key_id=cerradura.key_id, clase=cerradura.clase)
            if cerradura.evento_al_abrir:
                self._emitir(cerradura.evento_al_abrir)

    def _abrir_cofres(self, jugador: pygame.Rect) -> None:
        for cofre in self.cofres:
            if cofre.abierto or not alcanza(jugador, cofre.rect):
                continue
            if not self.llavero.tiene(cofre.key_id):
                self._avisar(f"El cofre está cerrado. Necesitas «{cofre.key_id}».")
                self._emitir(EVENTO_BLOQUEADA, key_id=cofre.key_id)
                continue

            cofre.abierto = True
            if cofre.contenido:
                self.llavero.coger(cofre.contenido)
            self._avisar(cofre.mensaje or (
                f"El cofre contenía: {cofre.contenido}" if cofre.contenido
                else "El cofre estaba vacío."
            ))
            self._emitir(EVENTO_COFRE, contenido=cofre.contenido)
            if cofre.evento_al_abrir:
                self._emitir(cofre.evento_al_abrir)

    def _disparar(self, jugador: pygame.Rect, usar: bool) -> None:
        for disparador in self.disparadores:
            if disparador.una_vez and disparador.disparado:
                continue
            if disparador.automatico:
                if not disparador.rect.colliderect(jugador):
                    continue
            elif not (usar and alcanza(jugador, disparador.rect)):
                continue
            if not self.llavero.tiene(disparador.key_id):
                continue

            disparador.disparado = True
            # `nombre=` y no `evento=`: el primer parámetro de `_emitir` ya se
            # llama `evento`, y pasar los dos chocaba con un TypeError. Lo
            # cazó la prueba en cuanto se ejecutó, que es exactamente para lo
            # que sirve tener una.
            self._emitir(EVENTO_DISPARADOR, nombre=disparador.evento)
            self._emitir(disparador.evento)
            # AUD-132 — y además abre lo que escuche ese nombre. El bus sigue
            # emitiendo para quien quiera enterarse desde su escena; esto es
            # el camino que no exige escribir Python.
            self.abrir_por_evento(disparador.evento)

    # -- salida ----------------------------------------------------
    def _avisar(self, texto: str, duracion: float = 2.0) -> None:
        self.mensaje = texto
        self.mensaje_timer = duracion

    def _emitir(self, evento: str, **datos: object) -> None:
        if self._bus is None:
            return
        try:
            self._bus.emit(evento, **datos)
        except Exception:
            # Un escenario de estudiante puede tener un suscriptor que lance.
            # Que su fallo tumbe la partida entera sería desproporcionado, y
            # perder el rastro sería peor: se registra con traza.
            logger.warning(
                "interactables: un suscriptor de '%s' lanzó", evento, exc_info=True,
            )
