"""
Module: bloques
System: framework.stage
Academic Unit: N/A
Description: AUD-140 — bloques que se empujan y bloques que se rompen, las dos
últimas filas del catálogo de mecánicas.

Por qué aquí y no como componentes ECS
=======================================
Las mecánicas de F5 —viento, plataformas, láseres— son componentes porque sólo
tienen que moverse y empujar. Estas dos, no: tienen que **participar en la
lista de sólidos del jugador** y **recibir el golpe del jugador**, y las dos
cosas se resuelven a nivel de escenario, no dentro del planificador ECS.

`Cerradura` ya sentó el precedente en F4.1 con `rects_solidos()`, y la escena
compone la lista así:

.. code-block:: python

    solidos = stage.collision_rects + cerradas + bloques.rects_solidos()

Sumar en vez de mutar `stage.collision_rects` es deliberado: esa lista la
construye el cargador y la leen los enemigos, el arco del jefe y la cámara.
Cambiarla para simular un estado es el atajo que después nadie sabe deshacer.

Qué aporta cada uno al diseño de un nivel
------------------------------------------
* **Empujable**: convierte una sala en un problema. Es el único objeto del
  motor que el jugador puede *colocar*, y con eso se hacen puentes sobre
  pinchos, escalones para alcanzar una cornisa y bloqueos de proyectiles.
* **Destructible**: convierte una pared en una pregunta. Un muro que cede a
  golpes premia probar cosas, que es lo contrario de un muro normal.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pygame

logger = logging.getLogger(__name__)

#: Gravedad de los bloques, en px/s². Más lenta que la del jugador a
#: propósito: un bloque que cae como una piedra no se puede seguir con la
#: vista, y colocarlo bien es justo lo que el jugador está intentando hacer.
GRAVEDAD_BLOQUE: float = 700.0

#: Píxeles de aire que aún cuentan como «estar tocando el bloque».
HOLGURA: int = 3


@dataclass
class BloqueEmpujable:
    """Se mueve cuando el jugador camina contra él, y cae si le quitan el suelo."""

    rect: pygame.Rect
    #: Píxeles por segundo mientras se empuja. Lento a propósito: empujar tiene
    #: que **costar**, o el bloque deja de ser un problema y pasa a ser una
    #: tecla que se mantiene pulsada.
    velocidad: float = 45.0
    #: Con `False` no cae; se queda flotando donde lo dejen. Para escenarios
    #: cenitales, donde «abajo» no significa nada.
    con_gravedad: bool = True
    inicial: pygame.Rect = field(default=None, repr=False)  # type: ignore[assignment]
    _vy: float = 0.0
    #: Posición horizontal en float. El `rect` va en enteros, y acumular el
    #: redondeo fotograma a fotograma haría que a 45 px/s y 60 fps cada
    #: fotograma redondeara 0,75 px a 1 y el bloque fuera a 60 px/s. Es el
    #: mismo defecto que la inundación (AUD-135), y aquí se nota más porque
    #: el jugador está midiendo a ojo dónde va a quedar el bloque.
    _x: float = 0.0

    def __post_init__(self) -> None:
        self.inicial = pygame.Rect(self.rect)
        self._x = float(self.rect.x)

    def reiniciar(self) -> None:
        """Al reaparecer, el bloque vuelve a su sitio.

        Sin esto, un bloque empujado a un foso deja el nivel sin solución y el
        jugador no tiene forma de saber que ya no se puede pasar. Es el mismo
        defecto que la inundación que no bajaba (AUD-135).
        """
        self.rect.update(self.inicial)
        self._vy = 0.0
        self._x = float(self.rect.x)


@dataclass
class BloqueDestructible:
    """Cede al cabo de unos golpes. Mientras tanto, es una pared."""

    rect: pygame.Rect
    #: Golpes que aguanta. Uno es un secreto; tres, un obstáculo.
    golpes: int = 1
    #: Evento del bus al romperse. Cierra el circuito con todo lo demás:
    #: abrir puertas (AUD-132), arrancar inundaciones (AUD-135), lanzar una
    #: escena (AUD-136).
    evento_al_romper: str = ""
    roto: bool = False
    _recibidos: int = 0

    def golpear(self) -> bool:
        """Devuelve `True` si este golpe lo rompió."""
        if self.roto:
            return False
        self._recibidos += 1
        if self._recibidos >= max(1, self.golpes):
            self.roto = True
            return True
        return False

    def reiniciar(self) -> None:
        self.roto = False
        self._recibidos = 0


class SistemaDeBloques:
    """Los mantiene, los mueve, los rompe y dice cuáles son sólidos."""

    def __init__(self, empujables: list[BloqueEmpujable] | None = None,
                 destructibles: list[BloqueDestructible] | None = None,
                 bus: object = None) -> None:
        self.empujables = list(empujables or [])
        self.destructibles = list(destructibles or [])
        self._bus = bus

    # ── lo que ve el resto del motor ──────────────────────────────
    def rects_solidos(self) -> list[pygame.Rect]:
        """Todo lo que ahora mismo estorba el paso."""
        solidos = [b.rect for b in self.empujables]
        solidos += [b.rect for b in self.destructibles if not b.roto]
        return solidos

    # ── empujar ───────────────────────────────────────────────────
    def empujar(self, jugador: pygame.Rect, direccion: int, dt: float,
                solidos: list[pygame.Rect]) -> int:
        """Mueve los bloques contra los que el jugador esté caminando.

        `direccion` es -1, 0 o 1. Devuelve cuántos se movieron.

        Sólo se empuja **de lado**: pisar un bloque no lo arrastra. Sin esa
        condición, quedarse quieto encima de un bloque lo iría desplazando y
        el jugador vería moverse el suelo sin tocar nada.
        """
        if direccion == 0 or dt <= 0.0:
            return 0
        movidos = 0
        for bloque in self.empujables:
            if not self._toca_de_lado(jugador, bloque.rect, direccion):
                continue
            nueva_x = bloque._x + direccion * bloque.velocidad * dt
            destino = pygame.Rect(bloque.rect)
            destino.x = round(nueva_x)
            if destino.x != bloque.rect.x and self._chocaria(destino, solidos, bloque):
                # Contra la pared: se para y se olvida del sobrante, para que
                # soltar y volver a empujar no dé un salto acumulado.
                bloque._x = float(bloque.rect.x)
                continue
            bloque._x = nueva_x
            if destino.x != bloque.rect.x:
                bloque.rect = destino
                movidos += 1
        return movidos

    @staticmethod
    def _toca_de_lado(jugador: pygame.Rect, bloque: pygame.Rect,
                      direccion: int) -> bool:
        # Se exige solape vertical real —no rozar una esquina— para que
        # pasar por encima rozando el canto no cuente como empujar.
        if jugador.bottom <= bloque.top + 2 or jugador.top >= bloque.bottom - 2:
            return False
        # `HOLGURA` existe porque el bloque se aparta antes de que el jugador
        # avance: durante ese fotograma quedan uno o dos píxeles de aire entre
        # los dos. Sin holgura el contacto se rompe cada fotograma y el bloque
        # avanza a tirones de un píxel; con ella, el empuje es continuo.
        if direccion > 0:
            return bloque.left - HOLGURA <= jugador.right <= bloque.left + jugador.width
        return bloque.right - jugador.width <= jugador.left <= bloque.right + HOLGURA

    def _chocaria(self, destino: pygame.Rect, solidos: list[pygame.Rect],
                  quien: BloqueEmpujable) -> bool:
        for rect in solidos:
            if rect is quien.rect:
                continue
            if destino.colliderect(rect):
                return True
        for otro in self.empujables:
            if otro is not quien and destino.colliderect(otro.rect):
                return True
        for roto in self.destructibles:
            if not roto.roto and destino.colliderect(roto.rect):
                return True
        return False

    def caer(self, dt: float, solidos: list[pygame.Rect]) -> None:
        """Gravedad de los bloques, resuelta por pasos de un píxel.

        Por pasos y no de un salto porque un bloque que cae rápido con un
        `dt` grande se metería dentro del suelo y habría que sacarlo; bajar de
        uno en uno hasta chocar no puede atravesar nada, y como caen pocos
        píxeles por fotograma no cuesta nada.
        """
        if dt <= 0.0:
            return
        for bloque in self.empujables:
            if not bloque.con_gravedad:
                continue
            bloque._vy = min(bloque._vy + GRAVEDAD_BLOQUE * dt, 600.0)
            restante = int(bloque._vy * dt)
            if restante <= 0:
                continue
            for _ in range(restante):
                siguiente = bloque.rect.move(0, 1)
                if self._chocaria(siguiente, solidos, bloque):
                    bloque._vy = 0.0
                    break
                bloque.rect = siguiente
            bloque._x = float(bloque.rect.x)

    # ── romper ────────────────────────────────────────────────────
    def golpear(self, hitbox: pygame.Rect | None) -> int:
        """Aplica un golpe del jugador. Devuelve cuántos bloques rompió."""
        if hitbox is None:
            return 0
        rotos = 0
        for bloque in self.destructibles:
            if bloque.roto or not hitbox.colliderect(bloque.rect):
                continue
            if bloque.golpear():
                rotos += 1
                self._emitir(bloque.evento_al_romper)
        return rotos

    def _emitir(self, evento: str) -> None:
        if not evento or self._bus is None:
            return
        emitir = getattr(self._bus, "emit", None)
        if callable(emitir):
            emitir(evento)

    # ── ciclo ─────────────────────────────────────────────────────
    def reiniciar(self) -> None:
        for bloque in self.empujables:
            bloque.reiniciar()
        for roto in self.destructibles:
            roto.reiniciar()
