"""
F5.14 — trepar por una liana y deslizarse por una tirolesa.

Por qué hacían falta dos estados y no bastaba con geometría
============================================================
La pregunta era si se podían crear obstáculos, lianas y tirolesas. Obstáculos sí
—hay dieciocho tipos de objeto que los hacen—, pero de escalada **no había
nada**: ni `Ladder`, ni `Rope`, ni `Climb`, ni un estado que suspendiera la
gravedad. Comprobado por búsqueda sobre todo `src/`.

Y no se puede improvisar con lo que había. Un estudiante intentaría apilar
`Solid` estrechos para hacer una cuerda, y lo que consigue es una pared: el
jugador queda **al lado** de la columna, no dentro, y para subir tiene que
saltar. Trepar exige tres cosas que ningún componente daba:

1. suspender la gravedad mientras se está agarrado,
2. movimiento vertical libre gobernado por el mando,
3. una forma de soltarse que no sea caerse.

Eso es un estado del jugador. De ahí estos dos.

La diferencia entre los dos, en una frase
------------------------------------------
En la liana **tú** decides la velocidad; en la tirolesa la decide la pendiente.
Por eso una sirve para descansar y explorar, y la otra para acelerar y
comprometerse. Mezclarlas —una liana que baja sola, una tirolesa que se sube a
voluntad— quita a cada una lo que la hace útil.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core.events import Events
from src.framework.entities.states.base import PlayerStateBase, _InputSnapshot

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.ecs.components import Liana, Tirolesa
    from src.framework.entities.player import Player


class TrepandoState(PlayerStateBase):
    """Agarrado a una liana: sube, baja, y salta para soltarse.

    Donkey Kong Country, Zelda, Spelunky, Castlevania.
    """

    #: Impulso horizontal al soltarse saltando. Sin él, saltar desde una liana
    #: te deja caer en vertical sobre el mismo sitio y la liana no sirve para
    #: cruzar nada, que es justo para lo que existe.
    IMPULSO_AL_SALTAR: float = 130.0

    def __init__(self, liana: Liana | None = None) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.CLIMBING)
        self._liana = liana
        #: Tiempo agarrado. Se usa para no re-agarrarse en el mismo fotograma
        #: en que se ha soltado, que produce el clásico «no puedo saltar de la
        #: cuerda» al mantener pulsado el botón.
        self._t = 0.0

    def enter(self, player: Player) -> None:
        super().enter(player)
        player.velocity.update(0.0, 0.0)
        player.is_grounded = False
        player._air_jumps_used = 0
        player._air_dash_count = 0
        self._t = 0.0
        if self._liana is not None:
            # Centrarse en la cuerda. Sin esto se trepa en diagonal si te
            # agarraste torcido, y el sprite se sale visualmente de la liana.
            player.rect.centerx = self._liana.rect.centerx
            player.position.x = float(player.rect.x)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)
        self._t += dt

        velocidad = self._liana.velocidad if self._liana is not None else 70.0
        if inp.move_y_up:
            player.velocity.y = -velocidad
        elif inp.crouch_held:
            player.velocity.y = velocidad
        else:
            player.velocity.y = 0.0
        player.velocity.x = 0.0

        # Soltarse saltando, con impulso hacia donde se mire.
        if inp.jump_pressed and self._t > 0.08:
            player.velocity.y = player.perfil.salto_impulso * 0.9
            player.velocity.x = float(inp.move_x or player.facing_direction) * (
                self.IMPULSO_AL_SALTAR
            )
            player._event_bus.emit(Events.SFX_PLAYER_JUMP)
            from src.framework.entities.states import JumpingState
            player._change_state_instance(JumpingState())
            return

        # Salirse por arriba o por abajo de la cuerda.
        if self._liana is not None and not self._liana.rect.colliderect(player.rect):
            from src.framework.entities.states import FallingState, IdleState
            player._change_state_instance(
                IdleState() if player.is_grounded else FallingState(),
            )


class TirolesaState(PlayerStateBase):
    """Colgado de un cable: la pendiente manda. DKC, Rayman, Ori."""

    def __init__(self, cable: Tirolesa | None = None) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.ZIPLINE)
        self._cable = cable
        self._t = 0.0

    def enter(self, player: Player) -> None:
        super().enter(player)
        player.is_grounded = False
        player._air_jumps_used = 0
        self._t = 0.0
        if self._cable is not None:
            enganche = self._cable.punto_mas_cercano(
                pygame.Vector2(player.rect.center),
            )
            # Se cuelga **por debajo** del cable, no centrado en él: el jugador
            # va agarrado con las manos, y dibujarlo atravesado por el cable se
            # lee como un fallo de capas.
            player.rect.centerx = int(enganche.x)
            player.rect.top = int(enganche.y)
            player.position.update(float(player.rect.x), float(player.rect.y))
        player.velocity.update(0.0, 0.0)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)
        self._t += dt

        if self._cable is None:
            from src.framework.entities.states import FallingState
            player._change_state_instance(FallingState())
            return

        direccion = self._cable.destino - self._cable.origen
        if direccion.length_squared() > 0.0:
            direccion = direccion.normalize()
        avance = direccion * self._cable.velocidad * dt
        player.position += avance
        player.rect.topleft = (int(player.position.x), int(player.position.y))

        # Soltarse: saltando, o al llegar al final del cable.
        llego = self._cable.progreso(pygame.Vector2(player.rect.center)) >= 0.995
        if (inp.jump_pressed and self._t > 0.08) or llego:
            if inp.jump_pressed and self._t > 0.08:
                player.velocity.y = player.perfil.salto_impulso * 0.8
                player._event_bus.emit(Events.SFX_PLAYER_JUMP)
            else:
                # Al llegar al final se conserva el impulso del cable. Frenar en
                # seco convertiría el final de la tirolesa en una caída vertical
                # y desperdiciaría toda la velocidad que el tramo acumuló.
                player.velocity.update(direccion * self._cable.velocidad * 0.6)
            from src.framework.entities.states import FallingState, JumpingState
            player._change_state_instance(
                JumpingState() if inp.jump_pressed else FallingState(),
            )
