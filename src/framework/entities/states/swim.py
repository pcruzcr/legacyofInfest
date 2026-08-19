from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

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

        # AUD-558 — GAP-069: el ataque acuático. Antes de este cambio el
        # jugador no tenía ninguna transición a un estado de ataque bajo
        # el agua —comprobado leyendo el archivo entero— así que
        # `BloqueDestructible.golpear()`
        # (`StageScene.update`, ya genérico para cualquier estado que
        # ponga `player._active_hitbox`) nunca se llamaba con un
        # `active_hitbox` real dentro de una `ZonaDeAgua`. Decisión del
        # dueño: un ataque acuático nuevo, no ruptura por proximidad —
        # ver GAP-069 en KNOWN_GAPS.md.
        if inp.short_attack:
            from src.framework.entities.states import SwimAttackState
            player._change_state_instance(SwimAttackState())
            return

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


class SwimAttackState(PlayerStateBase):
    """AUD-558 — GAP-069: el golpe acuático. Existe para una sola cosa —
    que `BloqueDestructible.golpear(player.active_hitbox)`
    (`StageScene.update`, ya genérico) tenga un `active_hitbox` real
    bajo el agua — así que no hereda de `_AttackState`
    (`states/attack.py`): esa base vuelve siempre a `IdleState` y
    comprueba salto/dash de tierra firme al terminar, ninguno de los
    dos tiene sentido nadando. Se escribe su propio ciclo, corto,
    frenando en vez de deteniendo en seco (un golpe bajo el agua no
    debería sentirse como chocar contra una pared invisible)."""

    #: A 14 fps (más lento que el ataque corto en tierra, 18 fps): el
    #: agua frena todo, un golpe submarino no debería sentirse tan
    #: rápido como uno en tierra firme.
    TOTAL_FRAMES: int = 6
    FPS: float = 14.0
    #: Los mismos fotogramas activos que `ShortAttackState` (comparten
    #: sprite, `player_short_attack.png` — ver `player.py`), para que la
    #: silueta del golpe coincida con el momento en que el arma
    #: realmente se extiende.
    ACTIVE_FRAMES: tuple[int, ...] = (2, 3, 4)

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SWIM_ATTACK)
        self._timer: float = 0.0
        self._frame: int = 0

    def enter(self, player: Player) -> None:
        super().enter(player)
        self._timer = 0.0
        self._frame = 0
        player._active_hitbox = None
        player._hitbox_consumed = False
        # Frena, no detiene en seco — ver el docstring de la clase.
        player.velocity.x *= 0.4
        player.velocity.y *= 0.4

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt
        frame_duration = 1.0 / self.FPS
        while self._timer >= frame_duration and self._frame < self.TOTAL_FRAMES:
            self._timer -= frame_duration
            self._frame += 1
            player._animation_frame = self._frame

        current_frame = self._frame + 1
        if current_frame in self.ACTIVE_FRAMES and not player._hitbox_consumed:
            player._active_hitbox = self._construir_hitbox(player)
        else:
            player._active_hitbox = None

        # Sigue frenando mientras dura el golpe — no queda inmóvil del
        # todo (el agua no lo permite), pero tampoco acelera: es un
        # golpe, no una brazada.
        player.velocity.x *= 0.9 ** (dt * 60.0)
        player.velocity.y *= 0.9 ** (dt * 60.0)

        if self._frame >= self.TOTAL_FRAMES:
            player._active_hitbox = None
            from src.framework.entities.states import SwimmingState
            player._change_state_instance(SwimmingState())

    def _construir_hitbox(self, player: Player) -> pygame.Rect:
        """Mismo tamaño que el ataque corto en tierra (36×20,
        `_build_attack_hitbox` en `states/helpers.py`) — no se reutiliza
        esa función porque sólo reconoce `ShortAttackState`/
        `LongAttackState` por `isinstance` y da un rect vacío para
        cualquier otro estado; aquí es más simple construirlo aparte que
        enseñarle a esa función un tercer caso que sólo aplica bajo el
        agua."""
        w, h = 36, 20
        cx = player.rect.centerx + (8 * player.facing_direction)
        cy = player.rect.centery
        return pygame.Rect(cx - w // 2, cy - h // 2, w, h)

    def exit(self, player: Player) -> None:
        player._active_hitbox = None
