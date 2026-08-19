from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core.events import Events
from src.framework.entities.states.base import PlayerStateBase, _InputSnapshot
from src.framework.entities.states.helpers import (
    _can_dash,
    _handle_charge_input,
    _handle_grab_input,
    _handle_grounded_attack_input,
    _handle_grounded_jump_input,
    _handle_parry_input,
    _handle_ultimate_input,
)

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.player import Player


class IdleState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.IDLE)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        if _handle_ultimate_input(player, inp):
            return

        if _handle_grab_input(player, inp):
            return

        if _handle_parry_input(player, inp):
            return

        if _handle_charge_input(player, inp):
            return

        if inp.move_x != 0:
            player.facing_direction = inp.move_x

        if _handle_grounded_attack_input(player, inp):
            return

        # AUD-373 — el dash también se perdona (GAP-040). Pulsarlo un fotograma
        # antes de tocar el suelo lo tiraba: el estado aéreo lo veía, `_can_dash`
        # decía que no, y ahí moría la pulsación. El salto llevaba años con
        # este perdón y ninguna otra acción lo tenía.
        from src.engine.input.action_map import Action
        if (inp.dash_pressed or inp.dash_en_buffer) and _can_dash(player, inp):
            inp.consumir(Action.DASH)
            from src.framework.entities.states import DashingState
            player._change_state_instance(DashingState())
            return

        if inp.crouch_held and player.is_grounded:
            from src.framework.entities.states import CrouchingState
            player._change_state_instance(CrouchingState())
            player.velocity.x = 0.0
            return

        if _handle_grounded_jump_input(player, inp):
            return

        if inp.move_x != 0 and player.is_grounded:
            from src.framework.entities.states import WalkingState
            player._change_state_instance(WalkingState())
            player.velocity.x = float(inp.move_x) * player.walk_speed
        else:
            player.velocity.x = 0.0

        if not player.is_grounded:
            if player.velocity.y < 0:
                from src.framework.entities.states import JumpingState
                player._change_state_instance(JumpingState())
            else:
                from src.framework.entities.states import FallingState
                player._change_state_instance(FallingState())


class WalkingState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.WALKING)
        self._footstep_timer: float = 0.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._footstep_timer += dt
        if self._footstep_timer >= 0.35:
            self._footstep_timer = 0.0
            # AUD-522 — el musgo resbala y hasta ahora no se oía ni se
            # veía, sólo se calculaba (`ZonaDeFriccion.inercia`). El
            # material lo pone `sistema_friccion` en cada fotograma
            # (`Transform.material_actual`, AUD-490); aquí sólo se lee.
            material = player._material_de_zona
            if material is not None and material.nombre == "musgo":
                pos = (player.position.x, player.position.y)
                player._event_bus.emit(Events.SFX_PLAYER_FOOTSTEP_MUSGO)
                player._event_bus.emit(Events.VFX_MUSGO_STEP, pos=pos)
            elif material is not None and material.nombre == "lodo":
                # AUD-551 — GAP-070 punto 1: el lodo frenaba de verdad
                # (`ZonaDeFriccion.multiplicador`, AUD-522) pero sonaba
                # igual que tierra firme — sólo el musgo tenía voz
                # propia pese a que los dos se declaran por separado en
                # Fase 2 del 4-1.
                player._event_bus.emit(Events.SFX_PLAYER_FOOTSTEP_LODO)
            elif material is not None and material.nombre == "grava":
                # AUD-554 — GAP-070 "Pasos sobre Tierra/Grava" (Fase 1 del
                # 4-1): mismo mecanismo, terreno nuevo.
                player._event_bus.emit(Events.SFX_PLAYER_FOOTSTEP_GRAVA)
            elif material is not None and material.nombre == "ahogado":
                # AUD-554 — GAP-070 "Pasos Ahogados" (Fase 5 del 4-1).
                player._event_bus.emit(Events.SFX_PLAYER_FOOTSTEP_AHOGADO)
            else:
                player._event_bus.emit(Events.SFX_PLAYER_FOOTSTEP)
        inp = _InputSnapshot(input_manager)

        if _handle_ultimate_input(player, inp):
            return

        if _handle_grab_input(player, inp):
            return

        if _handle_parry_input(player, inp):
            return

        if _handle_charge_input(player, inp):
            return

        if inp.move_x != 0:
            player.facing_direction = inp.move_x

        if _handle_grounded_attack_input(player, inp):
            return

        # AUD-373 — el dash también se perdona (GAP-040). Pulsarlo un fotograma
        # antes de tocar el suelo lo tiraba: el estado aéreo lo veía, `_can_dash`
        # decía que no, y ahí moría la pulsación. El salto llevaba años con
        # este perdón y ninguna otra acción lo tenía.
        from src.engine.input.action_map import Action
        if (inp.dash_pressed or inp.dash_en_buffer) and _can_dash(player, inp):
            inp.consumir(Action.DASH)
            from src.framework.entities.states import DashingState
            player._change_state_instance(DashingState())
            return

        if inp.crouch_held and player.is_grounded and abs(player.velocity.x) > 30.0:
            from src.framework.entities.states import SlideState
            player._change_state_instance(SlideState())
            return

        if inp.crouch_held and player.is_grounded:
            from src.framework.entities.states import CrouchingState
            player._change_state_instance(CrouchingState())
            player.velocity.x = 0.0
            return

        if _handle_grounded_jump_input(player, inp):
            return

        if inp.move_x != 0 and player.is_grounded:
            player.velocity.x = float(inp.move_x) * player.walk_speed
        elif inp.move_x == 0 and player.is_grounded:
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())
            player.velocity.x = 0.0

        if not player.is_grounded:
            if player.velocity.y < 0:
                from src.framework.entities.states import JumpingState
                player._change_state_instance(JumpingState())
            else:
                from src.framework.entities.states import FallingState
                player._change_state_instance(FallingState())


class CrouchingState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.CROUCHING)

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._update_rect_size()
        # AUD-255 — `SFX_PLAYER_CROUCH` existía con fichero y sin emisor. Va en
        # `enter` y no en `update` porque agacharse es un gesto, no un estado
        # que suene: emitirlo por fotograma sería un zumbido.
        if player._event_bus is not None:
            player._event_bus.emit(Events.SFX_PLAYER_CROUCH)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        if _handle_ultimate_input(player, inp):
            return

        if _handle_parry_input(player, inp):
            return

        if _handle_grounded_attack_input(player, inp):
            return

        # AUD-373 — el dash también se perdona (GAP-040). Pulsarlo un fotograma
        # antes de tocar el suelo lo tiraba: el estado aéreo lo veía, `_can_dash`
        # decía que no, y ahí moría la pulsación. El salto llevaba años con
        # este perdón y ninguna otra acción lo tenía.
        from src.engine.input.action_map import Action
        if (inp.dash_pressed or inp.dash_en_buffer) and _can_dash(player, inp):
            inp.consumir(Action.DASH)
            from src.framework.entities.states import DashingState
            player._change_state_instance(DashingState())
            return

        if not inp.crouch_held or not player.is_grounded:
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())
            player.velocity.x = 0.0
            return

        player.velocity.x = 0.0

    def exit(self, player: Player) -> None:
        player._update_rect_size()


class SlideState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SLIDE)
        self._timer: float = 0.0
        self._slide_dir: float = 1.0

    def enter(self, player: Player) -> None:
        super().enter(player)
        self._timer = player._slide_duration
        self._slide_dir = 1.0 if abs(player.velocity.x) > 0 else float(player.facing_direction)
        player.velocity.x = self._slide_dir * player._slide_speed
        old_bottom = player.rect.bottom
        player.rect.h = 18
        player.rect.y = old_bottom - 18
        player.position.y = float(player.rect.y)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        self._timer -= dt
        player.velocity.x = self._slide_dir * player._slide_speed

        if self._timer <= 0.0 or (player.is_grounded and not inp.crouch_held):
            player.velocity.x *= 0.3 ** (dt * 60.0)
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())
            return

        if not player.is_grounded:
            from src.framework.entities.states import FallingState
            player._change_state_instance(FallingState())
            return

    def exit(self, player: Player) -> None:
        player._update_rect_size()
        player.velocity.x = 0.0
