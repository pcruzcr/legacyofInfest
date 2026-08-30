from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.framework.entities.states.base import PlayerStateBase, _InputSnapshot
from src.framework.entities.states.helpers import (
    _can_dash,
    _handle_grounded_jump_input,
)

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.player import Player


# ── Dash ──────────────────────────────────────────────────────────

_DASH_DURATION = 0.15

#: AUD-620 — ventana de cancelación del dash con salto, en segundos.
#:
#: El dash ya se cancelaba con ataque (`DashAttackState`, en cualquier
#: instante); con salto no se cancelaba nunca, y eso convertía el dash en
#: un carril fijo de 0,15 s: quien dash-ea y quiere saltar encima de algo
#: tiene que esperar a que termine. La ventana —y no el dash entero— es lo
#: que separa una decisión temprana del spam: pasada ella, el salto espera.
_VENTANA_CANCELACION_SALTO = 0.1


class DashingState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.DASHING)
        self._transcurrido: float = 0.0
        self._dir_x: float = 0.0
        self._dir_y: float = 0.0
        self._dir_inicializado: bool = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        # AUD-141: se cobra al ENTRAR, no al pulsar. `_can_dash` ya ha
        # comprobado que hay bastante; cobrar en el sitio donde el dash
        # empieza de verdad evita el caso de gastar por un dash que después
        # otra condición cancela.
        # P0: estamina check global — si no hay, no se entra (defensivo por si _can_dash se saltó)
        if not player.hay_estamina_para_correr:
            from src.framework.entities.states import FallingState, IdleState
            target = IdleState if player.is_grounded else FallingState
            player._change_state_instance(target())
            return
        player.gastar_estamina()
        player._dash_timer = _DASH_DURATION
        self._transcurrido = 0.0
        self._dir_inicializado = False
        if not player.is_grounded:
            player._air_dash_count += 1
        player.velocity.y = 0.0
        player._invincibility_timer = max(player._invincibility_timer, _DASH_DURATION)
        # P0: VFX_SLAM al dash — feedback de impacto
        player._event_bus.emit(Events.VFX_SLAM, pos=(player.position.x, player.position.y))

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._transcurrido += dt
        player._dash_timer -= dt

        inp = _InputSnapshot(input_manager)
        # P0: 8-dir global — captura dirección al primer fotograma (suelo y aire)
        if not self._dir_inicializado:
            if inp.move_x != 0 or inp.move_y != 0:
                dx = float(inp.move_x)
                dy = float(inp.move_y)
            else:
                dx = float(player.facing_direction)
                dy = 0.0
            # cenital ya normaliza 0.707 en player.py:882; aquí igual para 8-dir
            if dx != 0.0 and dy != 0.0:
                dx *= 0.70710678
                dy *= 0.70710678
            self._dir_x = dx
            self._dir_y = dy
            self._dir_inicializado = True
            # actualizar facing según componente x
            if self._dir_x > 0:
                player.facing_direction = 1
            elif self._dir_x < 0:
                player.facing_direction = -1
        # 8-dir: velocidad en ambos ejes
        player.velocity.x = self._dir_x * settings.PLAYER_DASH_SPEED
        # P0 8-dir global: vertical en suelo lo frena la colisión si no aplica
        player.velocity.y = self._dir_y * settings.PLAYER_DASH_SPEED

        if inp.short_attack or inp.long_attack:
            from src.framework.entities.states import DashAttackState
            player._change_state_instance(DashAttackState())
            return

        # AUD-620 — cancelación con salto, sólo dentro de la ventana. Se
        # hace a mano y NO con `_do_jump` a propósito: aquél vería al
        # jugador realmente aéreo (`was_truly_airborne`) y CONSUMIRÍA un
        # salto del aire por cancelar un dash — castigar la técnica mejor.
        # La velocidad horizontal NO se toca: conservar los 200 px/s del
        # dash es toda la recompensa (el mismo contrato de AUD-204, que
        # conserva la inercia cuando se suelta la dirección).
        if inp.jump_pressed and self._transcurrido <= _VENTANA_CANCELACION_SALTO:
            player.velocity.y = player.perfil.salto_impulso
            player._coyote_counter = player.perfil.coyote_frames + 1
            player._jump_cut_applied = False
            # Mismo cooldown que el fin natural: sin él, cancelar y
            # re-dash en fotogramas consecutivos sería un dash infinito.
            player._dash_cooldown = 0.1
            player._event_bus.emit(Events.SFX_PLAYER_JUMP)
            from src.framework.entities.states import JumpingState
            player._change_state_instance(JumpingState())
            return

        if player._dash_timer <= 0:
            player._dash_cooldown = 0.1
            if player.is_grounded:
                from src.framework.entities.states import IdleState
                player._change_state_instance(IdleState())
            else:
                from src.framework.entities.states import FallingState
                player._change_state_instance(FallingState())
            return


# ── Parry ─────────────────────────────────────────────────────────

#: Ventana de parry cuando no hay configuración de dificultad que consultar.
#:
#: AUD-154 — esto era una constante y punto, así que los tres presets de
#: dificultad declaraban `parry_window` (0,30 en fácil; 0,15 en difícil) y
#: **nadie los leía**: todo el mundo jugaba con 0,20. Uno de los ocho mandos de
#: la dificultad no estaba conectado a nada.
#: P0: 0.20→0.25s (NORMAL ahora 0.25)
_PARRY_DURATION = 0.25


def _ventana_de_parry() -> float:
    """La ventana que toca según la dificultad elegida.

    Se consulta al entrar en el estado y no se guarda en el jugador: cambiar la
    dificultad a mitad de partida tiene que notarse en el siguiente parry, no
    en la siguiente partida.
    """
    from src.engine.core.difficulty import get_config

    return float(getattr(get_config(), "parry_window", _PARRY_DURATION))


class ParryState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.PARRY)

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._parry_window = _ventana_de_parry()
        player._parry_active = True
        player._parry_success = False
        player.velocity.x = 0.0
        player.velocity.y = 0.0
        player._event_bus.emit(Events.VFX_PARRY, pos=(player.position.x, player.position.y))

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        player._parry_window -= dt
        if player._parry_window <= 0:
            player._parry_active = False
            player._parry_window = 0.0
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._parry_active = False
        player._parry_window = 0.0


# ── Ultimate ──────────────────────────────────────────────────────


class UltimateState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.ULTIMATE)
        self._timer: float = 0.0
        #: AUD-293 — el árbol puede alargarlo. Se lee al entrar en el estado
        #: y no en el constructor: el jugador puede comprar el rango entre dos
        #: usos, y una duración leída una vez obligaría a reiniciar el nivel.
        self._duration: float = 0.6
        self._has_hit: bool = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        player.velocity.x = 0.0
        player.velocity.y = 0.0
        player.special_meter = 0.0
        player._event_bus.emit(Events.VFX_ULTIMATE, pos=(player.position.x, player.position.y))

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt

        if 0.1 <= self._timer < 0.4 and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = 96, 64
            hx = cx - (w // 2)
            hy = cy - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
            player._damage_mult = 3.0
        else:
            player._active_hitbox = None
            player._damage_mult = 1.0

        if self._timer >= self._duration + getattr(player, "_bonus_ultimate", 0.0):
            player._active_hitbox = None
            player._damage_mult = 1.0
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None
        player._damage_mult = 1.0


# ── Grab / Throw ──────────────────────────────────────────────────


class GrabState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.GRAB)
        self._timer: float = 0.0
        self._has_grabbed: bool = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        player.velocity.x = float(player.facing_direction) * 30.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt
        inp = _InputSnapshot(input_manager)

        if self._timer < 0.15 and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = 20, 16
            hx = cx + (8 * player.facing_direction) - (w // 2)
            hy = cy - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
        else:
            player._active_hitbox = None

        if player._hitbox_consumed and not self._has_grabbed:
            self._has_grabbed = True
            player._active_hitbox = None
            if inp.short_attack or inp.long_attack:
                from src.framework.entities.states import ThrowState
                player._change_state_instance(ThrowState())
                return

        if self._timer >= 0.3:
            player._active_hitbox = None
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None


class ThrowState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.THROW)
        self._timer: float = 0.0

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        player.velocity.x = float(player.facing_direction) * 50.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt

        if self._timer < 0.08 and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = 36, 20
            hx = cx + (14 * player.facing_direction) - (w // 2)
            hy = cy - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
        else:
            player._active_hitbox = None

        if player._hitbox_consumed:
            player._active_hitbox = None

        if self._timer >= 0.2:
            player._active_hitbox = None
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None


# ── Charging ──────────────────────────────────────────────────────

_CHARGE_MAX_TIME = 1.0
_CHARGE_LEVELS = [(0.5, 1.0), (1.0, 1.5), (1.5, 2.0)]


class ChargingState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.CHARGE_ATTACK)

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._charging = True
        player._charge_timer = 0.0
        player._charge_level = 0
        player.velocity.x = 0.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        player._charge_timer += dt

        if player._charge_timer >= _CHARGE_MAX_TIME:
            player._charge_level = 2
        elif player._charge_timer >= 0.5:
            player._charge_level = 1

        player._event_bus.emit(
            Events.VFX_CHARGE,
            pos=(player.position.x, player.position.y),
            level=player._charge_level,
        )

        inp = _InputSnapshot(input_manager)
        if not inp.long_attack and player._charge_timer > 0.1:
            self._release_charge(player)
            return

        if inp.short_attack and inp.crouch_held:
            from src.framework.entities.states import ParryState
            player._change_state_instance(ParryState())
            return

    def _release_charge(self, player: Player) -> None:
        level = min(player._charge_level, len(_CHARGE_LEVELS) - 1)
        dmg_mult = _CHARGE_LEVELS[level][1]
        player._charge_level = 0
        player._charging = False
        from src.framework.entities.states import ChargeReleaseState
        player._change_state_instance(ChargeReleaseState(dmg_mult))

    def exit(self, player: Player) -> None:
        player._charging = False


class ChargeReleaseState(PlayerStateBase):
    def __init__(self, damage_mult: float = 1.0) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.CHARGE_RELEASE)
        self._dmg_mult = damage_mult
        self._timer: float = 0.0
        self._has_hit: bool = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        player.velocity.x = float(player.facing_direction) * player.walk_speed * 1.5

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt
        inp = _InputSnapshot(input_manager)

        if self._timer < 0.15 and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = 48, 40
            hx = cx + (16 * player.facing_direction) - (w // 2)
            hy = cy - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
        else:
            player._active_hitbox = None

        player._damage_mult = self._dmg_mult

        if self._timer >= 0.15:
            if inp.dash_pressed and _can_dash(player, inp):
                from src.framework.entities.states import DashingState
                player._change_state_instance(DashingState())
                return
            if _handle_grounded_jump_input(player, inp):
                return

        if self._timer >= 0.3:
            player._damage_mult = 1.0
            player._active_hitbox = None
            player._cooldown_timer = 0.15
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None
        player._damage_mult = 1.0
