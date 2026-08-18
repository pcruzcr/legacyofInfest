from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core import settings
from src.engine.core.events import Events
from src.framework.entities.states.base import PlayerStateBase, _InputSnapshot

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.player import Player


class SwimmingState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SWIMMING)
        self._swim_timer: float = 0.0
        self._bubble_timer: float = 0.0
        self._surface_y: float = 0.0

    def enter(self, player: Player) -> None:
        super().enter(player)
        player.velocity.y = 0.0
        player.velocity.x *= 0.5
        self._swim_timer = 0.0
        self._bubble_timer = 0.0
        self._surface_y = player.position.y - 16.0
        player._swim_boosts = 0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)
        self._swim_timer += dt
        self._bubble_timer += dt

        player.velocity.y += settings.GRAVITY * 0.3 * dt
        player.velocity.y = max(-60.0, min(120.0, player.velocity.y))

        if inp.move_x != 0:
            player.velocity.x += inp.move_x * 60.0 * dt
            player.velocity.x = max(-120.0, min(120.0, player.velocity.x))
            player.facing_direction = inp.move_x
        else:
            player.velocity.x *= 0.9 ** (dt * 60.0)

        if inp.jump_pressed and player._swim_boosts < 1:
            player.velocity.y = -120.0
            player._swim_boosts += 1
            player._event_bus.emit(Events.SFX_PLAYER_JUMP)

        if inp.crouch_held:
            player.velocity.y += 200.0 * dt

        if self._bubble_timer >= 0.3:
            self._bubble_timer = 0.0
            player._event_bus.emit(Events.VFX_BUBBLE, pos=(player.position.x, player.position.y))

        if player.position.y < self._surface_y - 8.0:
            player.velocity.y = -200.0
            from src.framework.entities.states import JumpingState
            player._change_state_instance(JumpingState())
            return

        # AUD-526 — pisar el lecho marino (o cualquier suelo dentro de la
        # `ZonaDeAgua`, como el de 4.1b) disparaba `is_grounded` y esto
        # saltaba a `IdleState` aunque el jugador siguiera sumergido: el
        # efecto de agua seguía en pantalla pero el personaje ya caminaba
        # como en tierra firme, sin nadar. `ControlDeNado` es la única
        # autoridad para entrar y salir del agua (comprueba `en_agua()`
        # cada fotograma); duplicar el criterio aquí con `is_grounded`
        # sacaba al jugador del estado sin que el jugador hubiera salido
        # del agua de verdad.
        #
        # `_swim_boosts` sólo se reinicia en `enter()`, y con la salida por
        # `is_grounded` ya retirada el jugador puede pasar el nivel entero
        # sin volver a entrar al estado — así que sin este reinicio el
        # impulso hacia arriba sería de una sola vez por partida entera de
        # 4.1b, no por inmersión. Tocar fondo es el punto natural para
        # recargarlo: empujarse desde el lecho marino es la mecánica, no un
        # descuido.
        if player.is_grounded:
            player._swim_boosts = 0
