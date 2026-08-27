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

from src.engine.core.events import Events
from src.framework.stage.interactables import (
    Cerradura,
    Cofre,
    Disparador,
    Llavero,
    PlacaDePresion,
    Recogible,
    ZonaDeWarp,
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
#: AUD-287 — el jugador ha pisado una zona de warp. Lleva `destino` y `origen`.
EVENTO_WARP = "INTERACT_WARP"
#: Placa de presión activada / desactivada.
EVENTO_PLACA_ACTIVADA = "INTERACT_PLATE_ACTIVATED"
EVENTO_PLACA_DESACTIVADA = "INTERACT_PLATE_DEACTIVATED"


class InteractableSystem:
    """Recogibles, cerraduras, cofres y disparadores de un escenario."""

    def __init__(
        self,
        recogibles: list[Recogible] | None = None,
        cerraduras: list[Cerradura] | None = None,
        cofres: list[Cofre] | None = None,
        disparadores: list[Disparador] | None = None,
        bus: EventBus | None = None,
        warps: list[ZonaDeWarp] | None = None,
        placas: list[PlacaDePresion] | None = None,
    ) -> None:
        self.recogibles = list(recogibles or [])
        self.cerraduras = list(cerraduras or [])
        self.cofres = list(cofres or [])
        self.disparadores = list(disparadores or [])
        #: AUD-287 — zonas de warp. Al final de la firma y con valor por
        #: defecto: las 26 clases de escenario construyen esto por posición.
        self.warps = list(warps or [])
        #: Placas de presión (PressurePlate) — botones por peso.
        self.placas: list[PlacaDePresion] = list(placas or [])
        self.llavero = Llavero()
        self._bus = bus
        #: De qué cadáveres ya salió el botín (AUD-218). Vive aquí y no en el
        #: mixin de señales porque es estado del mundo: se va con el escenario.
        self._botin_soltado: set[str] = set()
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
        self._warpear(dt, jugador, usar)
        self._cerrar_las_cronometradas(dt, jugador)
        if usar:
            self._abrir_cerraduras(jugador)
            self._abrir_cofres(jugador)

    def actualizar_placas(
        self,
        bloques: list[object],
        jugador: pygame.Rect,
    ) -> None:
        """Actualiza las placas de presión con el peso real del nivel.

        Se llama desde ``StageScene._update_gameplay`` DESPUES de que
        ``SistemaDeBloques.empujar/caer`` hayan dejado los empujables en su
        sitio definitivo del fotograma, y usa la **misma** lista de solidos
        (``con_cerradas``) que los bloques para no duplicar composición.
        Mientras la placa este activa, abre las puertas cuyo ``abre_con``
        coincida; al liberarse (si ``mantener``) las cierra — nunca sobre el
        jugador (misma guarda que las cronometradas).
        """
        # --- Fase 1: detecta peso y actualiza activa (sin emitir) ---
        cambios: list[tuple[PlacaDePresion, bool, bool]] = []
        for placa in self.placas:
            if placa.una_vez and placa.disparada and placa.activa:
                # Enclavada para siempre — no re-evalua.
                continue
            bloque_presente = False
            for b in bloques:
                rect = getattr(b, "rect", None)
                if rect is None:
                    continue
                if self._bloque_sobre_placa(rect, placa.rect):
                    bloque_presente = True
                    break
            jugador_presente = self._jugador_sobre_placa(jugador, placa.rect)
            requiere = (placa.requiere or "bloque").lower()
            if requiere == "bloque":
                activa = bloque_presente
            elif requiere == "jugador":
                activa = jugador_presente
            elif requiere == "ambos":
                activa = bloque_presente and jugador_presente
            elif requiere in ("cualquiera", "any", "ambos_o", "either"):
                activa = bloque_presente or jugador_presente
            else:
                activa = bloque_presente

            previa = placa.activa
            if activa != previa:
                # ``una_vez`` enclavada no se deja desactivar.
                if not activa and previa and placa.una_vez:
                    continue
                placa._activa_previa = previa
                placa.activa = activa
                cambios.append((placa, previa, activa))
                if activa and placa.una_vez:
                    placa.disparada = True

        # --- Fase 2: flancos de subida — abre y emite ---
        for placa, previa, activa in cambios:
            if activa and not previa:
                self._emitir(placa.evento)
                self._emitir(EVENTO_PLACA_ACTIVADA, nombre=placa.evento)
                abiertas = self.abrir_por_evento(placa.evento)
                if placa.mensaje:
                    self._avisar(placa.mensaje)
                elif abiertas:
                    self._avisar(f"Placa activada: {placa.evento}")
            elif not activa and previa:
                if not placa.mantener:
                    continue
                # Si otra placa con el mismo evento sigue activa, no cierres.
                otro_activo = any(
                    p is not placa and p.activa and p.evento == placa.evento
                    for p in self.placas
                )
                if otro_activo:
                    continue
                cerradas = self._cerrar_por_evento(placa.evento, jugador)
                self._emitir(EVENTO_PLACA_DESACTIVADA, nombre=placa.evento)
                if cerradas:
                    self._avisar(f"Placa liberada: {placa.evento}")

        # --- Fase 3: cierre diferido — si se bloqueo por jugador dentro, reintenta ---
        # Ocurre fuera de ``cambios``: la placa ya esta inactiva pero la puerta
        # quedo abierta porque el jugador la pisaba. Al salir, debe cerrarse sin
        # nuevo flanco (misma guarda que ``_cerrar_las_cronometradas``).
        eventos_activos = {p.evento for p in self.placas if p.activa}
        for cerradura in self.cerraduras:
            if not cerradura.abierta:
                continue
            ev = cerradura.abre_con_evento
            if not ev or ev in eventos_activos:
                continue
            # Solo puertas que alguna placa reversible controla.
            reversible = any(p.evento == ev and p.mantener for p in self.placas)
            if not reversible:
                continue
            # Enclavada por una_vez nunca se cierra.
            if any(p.evento == ev and p.una_vez and p.disparada for p in self.placas):
                continue
            if cerradura.rect.colliderect(jugador):
                continue
            cerradura.abierta = False
            cerradura._cierre = 0.0
            self._avisar(f"Se ha cerrado algo. ({ev})")

    @staticmethod
    def _bloque_sobre_placa(bloque: pygame.Rect, placa: pygame.Rect) -> bool:
        """¿Esta el bloque pisando la placa?

        Un ``BloqueEmpujable`` reposando exactamente sobre la placa toca el
        borde sin solaparse (bottom == top), asi que ``colliderect`` solo
        fallaria. Se infla la placa 4 px en vertical (y 2 en horizontal) para
        capturar tanto el apoyo exacto como el solape interior.
        """
        inflada = placa.inflate(4, 8)
        if inflada.colliderect(bloque):
            return True
        # Apoyo exacto: bloque justo encima con solape horizontal.
        if bloque.right <= placa.left or bloque.left >= placa.right:
            return False
        # Distancia vertical entre la base del bloque y el techo de la placa.
        gap = bloque.bottom - placa.top
        return -6 <= gap <= placa.height + 6

    @staticmethod
    def _jugador_sobre_placa(jugador: pygame.Rect, placa: pygame.Rect) -> bool:
        inflada = placa.inflate(4, 6)
        if inflada.colliderect(jugador):
            return True
        if jugador.right <= placa.left or jugador.left >= placa.right:
            return False
        gap = jugador.bottom - placa.top
        return -6 <= gap <= placa.height + 6

    def _cerrar_por_evento(self, evento: str, jugador: pygame.Rect) -> int:
        """Cierra las puertas que se abrieron con ``evento`` de una placa.

        Nunca sobre el jugador — misma guarda que ``_cerrar_las_cronometradas``.
        Devuelve cuantas se cerraron.
        """
        if not evento:
            return 0
        cerradas = 0
        for cerradura in self.cerraduras:
            if not cerradura.abierta:
                continue
            if cerradura.abre_con_evento != evento:
                continue
            if cerradura.rect.colliderect(jugador):
                continue
            cerradura.abierta = False
            cerradura._cierre = 0.0
            cerradas += 1
        if cerradas:
            self._avisar(f"Se ha cerrado algo. ({cerradas})")
        return cerradas

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
            self._emitir(
                EVENTO_RECOGIDO,
                item_id=objeto.item_id,
                cantidad=objeto.cantidad,
                # AUD-281 — dónde ocurrió. Sin esto no hay ni partículas ni
                # sonido panoramizado: el evento llegaba sin lugar y quien lo
                # escuchaba sólo podía sumar al inventario.
                pos=objeto.rect.center,
            )

    def soltar_botin(self, entity_id: str, recogible: Recogible) -> bool:
        """Deja el botín de `entity_id` en el suelo. `False` si ya pagó.

        AUD-218. El descarte por `entity_id` evita que un evento repetido
        —o un enemigo que revive y vuelve a morir, que `EnemyBase` permite a
        propósito desde BUG-058— pague dos veces por el mismo cadáver.
        """
        if not entity_id or entity_id in self._botin_soltado:
            return False
        self._botin_soltado.add(entity_id)
        self.recogibles.append(recogible)
        return True

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

    def _warpear(self, dt: float, jugador: pygame.Rect, usar: bool) -> None:
        """AUD-287 — cruzar de un punto del mapa a otro.

        El sistema **no mueve al jugador**: emite dónde debería aparecer. Mover
        un rectángulo que este módulo no posee es la clase de atajo que después
        deja al jugador dentro de una pared sin que nadie sepa quién lo puso
        ahí. La escena, que sí es dueña del jugador y de la cámara, es quien
        aplica el salto.
        """
        for warp in self.warps:
            if warp._espera > 0.0:
                warp._espera = max(0.0, warp._espera - dt)
                continue
            if warp.una_vez and warp.usado:
                continue
            if warp.automatico:
                if not warp.rect.colliderect(jugador):
                    continue
            elif not (usar and alcanza(jugador, warp.rect)):
                continue
            if not self.llavero.tiene(warp.key_id):
                continue
            # AUD-635 — requires_skill: el warp exige una habilidad desbloqueada.
            if warp.requires_skill and not self.llavero.tiene(warp.requires_skill):
                continue

            warp.usado = True
            warp._espera = warp.enfriamiento
            if warp.mensaje:
                self._avisar(warp.mensaje)
            self._emitir(
                EVENTO_WARP,
                destino=(float(warp.destino.x), float(warp.destino.y)),
                origen=warp.rect.center,
            )

    # -- salida ----------------------------------------------------
    def _avisar(self, texto: str, duracion: float = 2.0) -> None:
        self.mensaje = texto
        self.mensaje_timer = duracion
        # Fix reporte Guillermo 7b: el mensaje de bloqueo quedaba invisible.
        # Además de guardar estado interno, se emite al bus para que MessageBox/HUD lo pinte.
        if texto and self._bus is not None:
            try:
                self._bus.emit(Events.SHOW_MESSAGE, text=texto, duration=duracion)
            except Exception:
                pass

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
