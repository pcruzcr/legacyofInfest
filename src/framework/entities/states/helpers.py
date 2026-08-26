from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.framework.entities.states.base import _InputSnapshot

if TYPE_CHECKING:
    from src.framework.entities.player import Player


def _handle_parry_input(player: Player, inp: _InputSnapshot) -> bool:
    if inp.short_attack and inp.crouch_held and player._parry_window <= 0:
        from src.framework.entities.states import ParryState
        player._change_state_instance(ParryState())
        return True
    return False


def _handle_charge_input(player: Player, inp: _InputSnapshot) -> bool:
    from src.framework.entities.player import PlayerState
    if inp.long_attack and player._cooldown_timer <= 0:
        if player._state_instance.state_enum not in (PlayerState.CHARGE_ATTACK,):
            from src.framework.entities.states import ChargingState
            player._change_state_instance(ChargingState())
            return True
    return False


def _handle_wall_jump(player: Player, inp: _InputSnapshot) -> bool:
    if player._can_wall_jump and inp.jump_pressed:
        wall_dir = player._wall_side
        player._air_jumps_used = 0
        player.velocity.y = player.perfil.salto_impulso * 0.85
        player.is_grounded = False
        player._coyote_counter = player.perfil.coyote_frames + 1
        player._jump_cut_applied = False
        player._wall_side = 0
        player._can_wall_jump = False
        player.facing_direction = -wall_dir
        from src.framework.entities.states import JumpingState
        player._change_state_instance(JumpingState())
        player._event_bus.emit(Events.SFX_PLAYER_JUMP)
        return True
    return False


def _handle_grounded_attack_input(
    player: Player, inp: _InputSnapshot,
) -> bool:
    if inp.short_attack:
        _start_attack(player, player.SHORT_ATTACK)
        return True
    if inp.long_attack:
        _start_attack(player, player.LONG_ATTACK)
        return True
    return False


def _handle_aerial_attack_input(
    player: Player, inp: _InputSnapshot,
) -> bool:
    if inp.short_attack:
        from src.framework.entities.states import AerialAttackState
        player._change_state_instance(AerialAttackState(short=True))
        player._event_bus.emit(Events.SFX_PLAYER_SHORT_ATTACK)
        return True
    if inp.long_attack:
        from src.framework.entities.states import AerialAttackState
        player._change_state_instance(AerialAttackState(short=False))
        player._event_bus.emit(Events.SFX_PLAYER_LONG_ATTACK)
        return True
    return False


def _handle_grounded_jump_input(
    player: Player, inp: _InputSnapshot,
) -> bool:
    if inp.jump_pressed and _can_jump(player):
        _do_jump(player)
        return True
    return False


def _tiene_habilidad(skill_id: str, player: Player | None = None) -> bool:
    """¿Está desbloqueada esta habilidad? (AUD-238, AUD-294)

    Dos salidas rápidas antes de tocar el inventario:

    * `PLAYER_SKILLS_REQUIRE_UNLOCK` apagado — el candado entero fuera;
    * el **escenario** exime, que es lo que mantiene intactas las entregas
      anteriores a AUD-294. La escena pone `_habilidades_libres` al entrar
      según `ESCENARIOS_CON_HABILIDADES_LIBRES` o la propiedad del mapa.

    Se pregunta al jugador y no a un global porque la exención es por
    escenario: pasar de un mapa exento a uno con candado dentro de la misma
    partida tiene que cambiar la respuesta.
    """
    if not settings.PLAYER_SKILLS_REQUIRE_UNLOCK:
        return True
    if player is not None and getattr(player, "_habilidades_libres", False):
        return True
    from src.engine.core.inventory import get_inventory
    return get_inventory().has_skill(skill_id)


def _can_jump(player: Player) -> bool:
    # El salto desde el suelo y el coyote **nunca** se condicionan: el coyote
    # son fotogramas de gracia del salto normal llegando tarde, no un salto
    # aéreo. Bloquearlos dejaría al jugador sin poder subir un escalón, que no
    # es progresión sino un juego roto.
    if player.is_grounded or player._coyote_counter < player.perfil.coyote_frames:
        return True
    
    # Assist mode: saltos infinitos sin requerir habilidad
    from src.engine.core.user_settings import get
    if get().assist_infinite_jumps:
        return True
    
    return (
        player._air_jumps_used < player.perfil.saltos_aereos
        and _tiene_habilidad("skill_double_jump", player)
    )


def _do_jump(player: Player) -> None:
    was_grounded = player.is_grounded
    was_truly_airborne = not was_grounded and player._coyote_counter >= player.perfil.coyote_frames
    player.velocity.y = player.perfil.salto_impulso
    # AUD-636 — estirar al despegar. Va después de fijar la velocidad para
    # que el fotograma del impulso ya se vea alargado.
    player.aplicar_stretch_por_salto()
    player.is_grounded = False
    player._coyote_counter = player.perfil.coyote_frames + 1
    player._jump_cut_applied = False
    if was_truly_airborne and player._air_jumps_used < player.perfil.saltos_aereos:
        player._air_jumps_used += 1
    from src.framework.entities.states import JumpingState
    player._change_state_instance(JumpingState())


def _reset_air_jumps(player: Player) -> None:
    player._air_jumps_used = 0


def _start_attack(player: Player, attack_type: object) -> None:
    atk_name = "SHORT_ATTACK" if attack_type == player.SHORT_ATTACK else "LONG_ATTACK"

    from src.framework.entities.states import (
        LongAttackState,
        ShortAttackState,
    )
    changed = False
    if attack_type == player.SHORT_ATTACK:
        changed = player._change_state_instance(ShortAttackState())
        player._event_bus.emit(Events.SFX_PLAYER_SHORT_ATTACK)
    else:
        changed = player._change_state_instance(LongAttackState())
        player._event_bus.emit(Events.SFX_PLAYER_LONG_ATTACK)

    if changed:
        if (player.combo_active
                and player.combo_timer > 0
                and player.last_attack_type == atk_name
                and player.combo_count < settings.COMBO_MAX):
            player.combo_count += 1
        else:
            player.combo_count = 1
        # AUD-154 — la ventana de combo sale de la dificultad, no de `settings`.
        #
        # Los tres presets declaran `combo_window` (0,60 en fácil; 0,35 en
        # difícil) y nadie los leía: todo el mundo encadenaba con los 0,50 de
        # `settings.COMBO_WINDOW`. Era el segundo de los ocho mandos de la
        # dificultad sin conectar.
        from src.engine.core.difficulty import get_config

        player.combo_timer = float(
            getattr(get_config(), "combo_window", settings.COMBO_WINDOW))
        player.last_attack_type = atk_name
        player.combo_active = True

        from src.framework.entities.states import CrouchingState
        player._crouching_at_attack_start = isinstance(
            player._state_instance,
            CrouchingState,
        ) if hasattr(player, "_state_instance") else False


def _can_dash(player: Player, inp: _InputSnapshot) -> bool:
    if player._dash_cooldown > 0:
        return False
    # AUD-141 — la estamina se consulta AQUÍ, que es el único sitio del motor
    # donde se decide si un dash empieza. Ponerla en cada estado que lo
    # permite —hay seis— habría garantizado que alguno se quedara sin ella.
    if not player.hay_estamina_para_correr:
        return False
    # AUD-238: la habilidad se comprueba aquí por el mismo motivo que la
    # estamina — es el único sitio del motor donde se decide si un dash
    # empieza. Con el candado apagado no se consulta nada.
    if not _tiene_habilidad("skill_dash", player):
        return False
    if player.is_grounded:
        return True
    return player._air_dash_count < settings.PLAYER_AIR_DASH_LIMIT


def _handle_grab_input(player: Player, inp: _InputSnapshot) -> bool:
    if inp.grab_pressed or (inp.long_attack and inp.crouch_held and not inp.short_attack):
        from src.framework.entities.states import GrabState
        player._change_state_instance(GrabState())
        return True
    return False


def _handle_ultimate_input(player: Player, inp: _InputSnapshot) -> bool:
    # F4.2: se consulta `ultimate_listo` y no el medidor a pelo, para que
    # la comparación con margen viva en un solo sitio. Antes había un
    # `>=` literal aquí y el redondeo lo dejaba en falso con la barra llena.
    if inp.short_attack and inp.long_attack and player.ultimate_listo:
        from src.framework.entities.states import UltimateState
        player._change_state_instance(UltimateState())
        return True
    return False


def _reset_combo(player: Player) -> None:
    player.combo_count = 0
    player.combo_timer = 0.0
    player.combo_active = False


def _build_attack_hitbox(player: Player, frame: int) -> pygame.Rect:
    attack_state = player._state_instance
    from src.framework.entities.states import CrouchingState, LongAttackState, ShortAttackState
    is_short = isinstance(attack_state, ShortAttackState)
    is_long = isinstance(attack_state, LongAttackState)
    is_crouching = getattr(player, "_crouching_at_attack_start",
                           isinstance(player._prev_state_instance, CrouchingState))

    cx = player.rect.centerx
    cy = player.rect.centery

    if is_short:
        offset_x = 8
        offset_y = -4 if not is_crouching else 8
        w, h = 36, 20
        if not is_crouching:
            h = 20
    elif is_long:
        frame_offsets = {
            4: (12, -10, 36, 20),
            5: (18, -4, 36, 20),
            6: (18, 0, 36, 20),
            7: (12, 6, 36, 20),
        }
        if frame in frame_offsets:
            offset_x, offset_y, w, h = frame_offsets[frame]
        else:
            return pygame.Rect(0, 0, 0, 0)
        if is_crouching:
            offset_y += 12
            h = 12
    else:
        return pygame.Rect(0, 0, 0, 0)

    hx = cx + (offset_x * player.facing_direction) - (w // 2)
    hy = cy + offset_y - (h // 2)
    return pygame.Rect(hx, hy, w, h)
