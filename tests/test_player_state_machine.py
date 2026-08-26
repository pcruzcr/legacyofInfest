import pygame
import pytest

from src.framework.entities.player import Player, PlayerState
from src.framework.entities.states import (
    AerialAttackState,
    AerialSlamState,
    AirChaseState,
    ChargeReleaseState,
    ChargingState,
    CrouchingState,
    DashAttackState,
    DashingState,
    DyingState,
    FallingState,
    GrabState,
    GroundPoundState,
    HurtState,
    IdleState,
    JumpingState,
    LedgeGrabState,
    LongAttackState,
    ParryState,
    PlayerStateBase,
    ShortAttackState,
    SlideState,
    SwimmingState,
    ThrowState,
    UltimateState,
    WalkingState,
    WallSlideState,
)


def test_cada_valor_del_enum_tiene_sprite_y_velocidad_de_animacion() -> None:
    """Se cuenta lo que importa, no cuántos hay.

    Esta prueba decía `assert len(PlayerState) == 24` y se llamaba
    `test_player_state_enum_has_19_values`: el nombre y el número ya no
    coincidían, señal de que a alguien le tocó editarla y sólo cambió el
    número. Una prueba que hay que actualizar cada vez que se añade un estado
    no protege nada; enseña a editar pruebas.

    Lo que sí es un contrato: **todo estado declarado tiene que poder
    dibujarse**. Un valor del enum sin entrada en la tabla de sprites es un
    jugador que desaparece al entrar en él, y eso sí es un fallo.
    """
    from src.framework.entities.player import _PLAYER_ANIM_FPS, _PLAYER_SPRITE_MAP

    sin_sprite = [e.value for e in PlayerState if e.value not in _PLAYER_SPRITE_MAP]
    sin_velocidad = [e.value for e in PlayerState if e.value not in _PLAYER_ANIM_FPS]
    assert not sin_sprite, f"estados sin hoja de sprites: {sin_sprite}"
    assert not sin_velocidad, f"estados sin velocidad de animación: {sin_velocidad}"


def test_nadar_tiene_hoja_propia_y_no_esta_congelado() -> None:
    """AUD-525: `SWIMMING` reutilizaba `player_jump.png` — cuatro copias del
    mismo fotograma quieto (`_gen_player_sprite` no varía entre frames), así
    que nadar se veía como quedarse de pie clavado bajo el agua. Ahora tiene
    hoja propia (`player_swim.png`, generada por `_gen_player_swim`) y esa
    hoja alterna entre dos poses distintas — si algún día alguien la vuelve
    a apuntar a una hoja ajena o a copias idénticas, esta prueba lo nota.
    """
    from src.engine.core import settings
    from src.engine.utils.asset_loader import AssetLoader
    from src.framework.entities.player import _PLAYER_SPRITE_MAP

    hoja_swim, frames = _PLAYER_SPRITE_MAP["SWIMMING"]
    assert hoja_swim != _PLAYER_SPRITE_MAP["JUMPING"][0], (
        "nadar no debería compartir hoja con saltar: no hay brazada posible "
        "si son el mismo dibujo"
    )

    ruta = settings.ASSETS_DIR / "sprites" / "player" / hoja_swim
    assert ruta.exists(), f"falta la hoja de sprites de nado: {ruta}"

    sheet = AssetLoader.load_sprite_sheet(str(ruta), 32, 32)
    assert len(sheet) == frames
    contenidos = {pygame.image.tobytes(f, "RGBA") for f in sheet}
    assert len(contenidos) > 1, (
        "todos los fotogramas de nado son idénticos — sigue leyéndose como "
        "una pose fija, no como movimiento"
    )


def test_initial_state_is_idle() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    assert player.state == PlayerState.IDLE
    assert isinstance(player._state_instance, IdleState)


_ENUM_MAP: list[tuple[type[PlayerStateBase], PlayerState]] = [
    (IdleState, PlayerState.IDLE),
    (WalkingState, PlayerState.WALKING),
    (JumpingState, PlayerState.JUMPING),
    (FallingState, PlayerState.FALLING),
    (CrouchingState, PlayerState.CROUCHING),
    (ShortAttackState, PlayerState.SHORT_ATTACK),
    (LongAttackState, PlayerState.LONG_ATTACK),
    (HurtState, PlayerState.HURT),
    (DyingState, PlayerState.DYING),
    (DashingState, PlayerState.DASHING),
    (ParryState, PlayerState.PARRY),
    (ChargingState, PlayerState.CHARGE_ATTACK),
    (DashAttackState, PlayerState.DASH_ATTACK),
    (WallSlideState, PlayerState.WALL_SLIDE),
    (LedgeGrabState, PlayerState.LEDGE_GRAB),
    (GrabState, PlayerState.GRAB),
    (ThrowState, PlayerState.THROW),
    (SlideState, PlayerState.SLIDE),
    (SwimmingState, PlayerState.SWIMMING),
    (UltimateState, PlayerState.ULTIMATE),
    (ChargeReleaseState, PlayerState.CHARGE_RELEASE),
    (AerialAttackState, PlayerState.AERIAL_ATTACK),
    (AerialSlamState, PlayerState.AERIAL_SLAM),
    # AUD-619 — el pisotón aéreo entra al contrato del enum como los demás.
    (GroundPoundState, PlayerState.GROUND_POUND),
    (AirChaseState, PlayerState.AIR_CHASE),
    (ChargeReleaseState, PlayerState.CHARGE_RELEASE),
]


@pytest.mark.parametrize("cls,expected", _ENUM_MAP)
def test_each_state_has_correct_enum(cls: type[PlayerStateBase], expected: PlayerState) -> None:
    instance = cls()
    assert instance.state_enum == expected


def test_each_state_has_enter_update_exit() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    for cls, _ in _ENUM_MAP:
        instance = cls()
        assert hasattr(instance, "enter")
        assert hasattr(instance, "update")
        assert hasattr(instance, "exit")
        instance.enter(player)
        instance.update(player, 1.0 / 60.0, None)
        instance.exit(player)


def test_transition_from_idle_to_walking() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(WalkingState())
    assert player.state == PlayerState.WALKING


def test_transition_from_walking_to_idle() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(WalkingState())
    player._change_state_instance(IdleState())
    assert player.state == PlayerState.IDLE


def test_idle_to_walking_through_update() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.is_grounded = True
    player._change_state_instance(IdleState())
    player._state_instance.update(player, 1.0 / 60.0, None)
    assert player.state == PlayerState.IDLE


def test_walking_to_idle_through_update() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.is_grounded = True
    player._change_state_instance(WalkingState())
    player.velocity.x = 90.0
    player._state_instance.update(player, 1.0 / 60.0, None)
    assert player.state == PlayerState.IDLE


def test_transition_from_idle_to_jumping() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(JumpingState())
    assert player.state == PlayerState.JUMPING


def test_transition_from_jumping_to_falling() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(JumpingState())
    player.velocity.y = 100.0
    player._state_instance.update(player, 1.0 / 60.0, None)
    assert player.state == PlayerState.FALLING


def test_transition_from_falling_to_idle_when_grounded() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(FallingState())
    player.is_grounded = True
    player._state_instance.update(player, 1.0 / 60.0, None)
    assert player.state == PlayerState.IDLE


def test_transition_from_falling_to_jumping_on_rise() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(FallingState())
    player.velocity.y = -100.0
    player._state_instance.update(player, 1.0 / 60.0, None)
    assert player.state == PlayerState.JUMPING


def test_transition_from_idle_to_crouching() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.is_grounded = True
    player._change_state_instance(CrouchingState())
    assert player.state == PlayerState.CROUCHING


def test_transition_from_crouching_to_idle_through_update() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(CrouchingState())
    player._state_instance.update(player, 1.0 / 60.0, None)
    assert player.state == PlayerState.IDLE


def test_transition_to_short_attack() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(ShortAttackState())
    assert player.state == PlayerState.SHORT_ATTACK


def test_transition_to_long_attack() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(LongAttackState())
    assert player.state == PlayerState.LONG_ATTACK


def test_transition_to_hurt_state_via_damage() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(0.5, (50.0, 0.0))
    assert player.state == PlayerState.HURT


def test_transition_to_dying_state_at_zero_health() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(100.0, (50.0, 0.0))
    assert player.state == PlayerState.DYING


def test_transition_to_dashing() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(DashingState())
    assert player.state == PlayerState.DASHING


def test_transition_to_slide() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(SlideState())
    assert player.state == PlayerState.SLIDE


def test_transition_to_parry() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(ParryState())
    assert player.state == PlayerState.PARRY


def test_transition_to_wall_slide() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(WallSlideState())
    assert player.state == PlayerState.WALL_SLIDE


def test_transition_to_ledge_grab() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(LedgeGrabState())
    assert player.state == PlayerState.LEDGE_GRAB


def test_no_transition_to_same_state_enum() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(IdleState())
    prev = player._state_instance
    player._change_state_instance(IdleState())
    assert player._state_instance is prev


def test_enter_resets_animation_timer() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._animation_timer = 99.0
    player._animation_frame = 99
    player._change_state_instance(FallingState())
    assert player._animation_timer == 0.0
    assert player._animation_frame == 0


def test_dying_state_is_terminal() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._change_state_instance(DyingState())
    player.apply_damage(999.0, (50.0, 0.0))
    assert player.state == PlayerState.DYING
