from __future__ import annotations

from typing import TYPE_CHECKING

from src.framework.entities.states.base import PlayerStateBase, _InputSnapshot

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.player import Player


class StaggerState(PlayerStateBase):
    """Tambaleo tras BODY_SLAM o parry fallido — 0.6s sin atacar, 0.5x daño."""

    def __init__(self, duration: float = 0.6) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.STAGGER)
        self._timer = float(duration)

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._animation_timer = 0.0
        player._animation_frame = 0
        # Reduce daño infligido temporalmente
        player._damage_mult = 0.5

    def update(self, player: Player, dt: float, input_manager: InputManager | None) -> None:
        self._timer -= dt
        # No permite atacar ni dash durante stagger
        if self._timer <= 0:
            player._damage_mult = 1.0
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())
            return
        # Solo gravedad y fricción, sin input
        _ = _InputSnapshot(None)

    def exit(self, player: Player) -> None:
        player._damage_mult = 1.0


class PossessedState(PlayerStateBase):
    """Veneno nivel 2 — inputs invertidos 2s, cura con ITEM_CONSUMED."""

    def __init__(self, duration: float = 2.0) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.POSSESSED)
        self._timer = float(duration)
        self._cured = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._animation_timer = 0.0
        player._animation_frame = 0
        # Suscribe cura
        try:
            player._event_bus.subscribe("ITEM_CONSUMED", self._on_cure)
        except Exception:
            pass

    def _on_cure(self, **_data: object) -> None:
        self._cured = True

    def update(self, player: Player, dt: float, input_manager: InputManager | None) -> None:
        if self._cured:
            self._timer = 0
        self._timer -= dt
        if self._timer <= 0:
            try:
                player._event_bus.unsubscribe("ITEM_CONSUMED", self._on_cure)
            except Exception:
                pass
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())
            return
        # Invierte movimiento horizontal
        inp = _InputSnapshot(input_manager)
        # Si hay input, lo invertimos antes de que el motor lo lea
        # Se hace aquí para no tocar helpers: el estado posee el input
        if input_manager is not None:
            # No podemos mutar InputManager, pero sí la velocidad que fijará el próximo estado
            # Truco: si el jugador pulsa derecha, lo movemos a izquierda con la misma velocidad
            if inp.move_x != 0:
                # Fuerza velocidad invertida directamente
                # Usa walk_speed invertido
                inv = -inp.move_x
                player.velocity.x = float(inv) * player.walk_speed

    def exit(self, player: Player) -> None:
        try:
            player._event_bus.unsubscribe("ITEM_CONSUMED", self._on_cure)
        except Exception:
            pass
