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

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)
        self._swim_timer += dt
        self._bubble_timer += dt

        # AUD-528 — nado omnidireccional real, pedido explícito: "el botón
        # de salto debe funcionar como impulso de nado... emulando la
        # sensación de los niveles de agua clásicos de Super Mario Bros".
        #
        # El modelo anterior aplicaba gravedad constante (`GRAVITY * 0.3`)
        # y un único impulso de salto que se recargaba al tocar fondo
        # (AUD-526): sin mantener la tecla pulsada, el jugador se hundía
        # sin parar y se quedaba posado en el lecho — cuatro segundos de
        # prueba sin soltar una tecla lo dejan clavado en el fondo,
        # indistinguible de caminar, que es exactamente el reporte
        # "camina sobre el agua". El eje vertical ahora se mueve con el
        # mismo lenguaje que ya usa el horizontal (aceleración mientras se
        # mantiene la tecla, freno suave al soltarla): flotar en el sitio
        # es el comportamiento neutral, no hundirse. Mantener salto (o
        # arriba) empuja hacia la superficie; mantener agachar empuja
        # hacia el fondo — las dos direcciones son simétricas y continuas,
        # no un pulso de una vez.
        empuje_vertical = 0
        if inp.jump_held or inp.move_y_up:
            empuje_vertical = -1
        elif inp.crouch_held:
            empuje_vertical = 1

        if empuje_vertical != 0:
            player.velocity.y += empuje_vertical * 90.0 * dt
            player.velocity.y = max(-100.0, min(100.0, player.velocity.y))
        else:
            # Sin tecla vertical: freno hacia flotar en el sitio, no caída
            # libre. Un peso residual —mucho menor que la gravedad real—
            # evita que el nado se sienta completamente ingrávido; sigue
            # habiendo una razón para nadar hacia arriba de vez en cuando.
            player.velocity.y *= 0.88 ** (dt * 60.0)
            player.velocity.y += settings.GRAVITY * 0.05 * dt
            player.velocity.y = max(-100.0, min(60.0, player.velocity.y))

        if inp.move_x != 0:
            player.velocity.x += inp.move_x * 60.0 * dt
            player.velocity.x = max(-120.0, min(120.0, player.velocity.x))
            player.facing_direction = inp.move_x
        else:
            player.velocity.x *= 0.9 ** (dt * 60.0)

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
        # del agua de verdad. Con el empuje vertical continuo de AUD-528
        # ya no hace falta reiniciar ningún contador de impulsos al tocar
        # fondo — no hay ningún contador que reiniciar.
