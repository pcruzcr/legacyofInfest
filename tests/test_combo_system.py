"""
Module: test_combo_system
System: tests
Description: Tests for combo counting, combo timer, and multiplier calculation.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings
from src.framework.entities.player import Player
from src.framework.entities.states import (
    _reset_combo,
    _start_attack,
)


class TestComboSystem:
    def _reset_to_idle(self, player: Player) -> None:
        """Force player back to IdleState so next _start_attack starts fresh."""
        from src.framework.entities.states import IdleState
        player._change_state_instance(IdleState(), force=True)

    def _conectar(self, player: Player) -> None:
        """Un tajo que toca: hitbox viva + aviso de `CollisionSystem`.

        AUD-818 (P13) — `consume_hitbox` es la única puerta de producción
        (`collision_system.py`, con `connected=True`); aquí se usa directo
        para no montar escena en un test de unidad.
        """
        player._active_hitbox = pygame.Rect(0, 0, 10, 10)
        player._hitbox_consumed = False
        player.consume_hitbox()

    def _golpear(self, player: Player, attack_type: object) -> None:
        """Arrancar el ataque y conectarlo, como un tajo que sí pega."""
        self._reset_to_idle(player)
        _start_attack(player, attack_type)
        self._conectar(player)

    def test_pulsar_sin_pegar_no_sube_el_combo(self) -> None:
        """AUD-818 (P13) — tres botonazos al aire: combo en cero, cero golpes.

        Antes `_start_attack` contaba al arrancar y `current_attack_damage`
        regalaba daño por abanicar; ahora el arranque sólo arma la ventana.
        """
        player = Player(pygame.Vector2(0, 0))
        for _ in range(3):
            self._reset_to_idle(player)
            _start_attack(player, Player.SHORT_ATTACK)
        assert player.combo_count == 0
        assert not player.combo_active

    def test_combo_count_increments(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        assert player.combo_count == 0
        self._golpear(player, Player.SHORT_ATTACK)
        assert player.combo_count == 1
        self._golpear(player, Player.SHORT_ATTACK)
        assert player.combo_count == 2
        self._golpear(player, Player.SHORT_ATTACK)
        assert player.combo_count == 3

    def test_un_tajo_que_toca_a_varios_cuenta_un_paso(self) -> None:
        """AUD-818 (P13) — `connected` es un booleano por tajo: dos avisos
        del mismo swing no hacen dos pasos (la guarda de hitbox viva)."""
        player = Player(pygame.Vector2(0, 0))
        _start_attack(player, Player.SHORT_ATTACK)
        self._conectar(player)
        assert player.combo_count == 1
        player._active_hitbox = pygame.Rect(0, 0, 10, 10)
        player.consume_hitbox()
        assert player.combo_count == 1

    def test_combo_resets_on_type_change(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        self._golpear(player, Player.SHORT_ATTACK)
        assert player.combo_count == 1
        self._golpear(player, Player.LONG_ATTACK)
        assert player.combo_count == 1

    def test_combo_capped_at_max(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        for _ in range(5):
            self._golpear(player, Player.SHORT_ATTACK)
        assert player.combo_count <= settings.COMBO_MAX

    def test_combo_timer_decrements(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        _start_attack(player, Player.SHORT_ATTACK)
        # La ventana la manda la dificultad (`get_config`), no la base fija:
        # comparar contra la misma fuente que usa el código (fallo
        # preexistente: 0.49 de config contra 0.5 de `settings`).
        from src.engine.core.difficulty import get_config
        assert player.combo_timer == float(get_config().combo_window)
        player.combo_timer = 0.01
        player._tick_timers(0.02)
        assert player.combo_timer <= 0
        assert not player.combo_active
        assert player.combo_count == 0

    def test_combo_active_flag(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        _start_attack(player, Player.SHORT_ATTACK)
        assert not player.combo_active, (
            "el arranque arma la ventana pero no activa el combo: "
            "sin impacto no hay combo (P13)"
        )
        self._conectar(player)
        assert player.combo_active
        _reset_combo(player)
        assert not player.combo_active
        assert player.combo_count == 0

    def test_last_attack_type_tracked(self) -> None:
        """AUD-818 — el tipo se registra al CONECTAR, no al pulsar: un
        arranque fallado no debe mover la referencia del encadenado."""
        player = Player(pygame.Vector2(0, 0))
        _start_attack(player, Player.SHORT_ATTACK)
        assert player.last_attack_type == ""
        self._conectar(player)
        assert player.last_attack_type == "SHORT_ATTACK"
        self._golpear(player, Player.LONG_ATTACK)
        assert player.last_attack_type == "LONG_ATTACK"

    def test_combo_within_window(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        self._golpear(player, Player.SHORT_ATTACK)
        player.combo_timer = 0.1
        self._golpear(player, Player.SHORT_ATTACK)
        assert player.combo_count == 2

    def test_combo_expired_window_resets(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        self._golpear(player, Player.SHORT_ATTACK)
        player.combo_timer = 0.0
        player.combo_active = False
        player.combo_count = 0
        self._golpear(player, Player.SHORT_ATTACK)
        assert player.combo_count == 1

    def test_current_attack_damage_scales_with_combo(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        _start_attack(player, Player.SHORT_ATTACK)
        player.combo_count = 2
        player.combo_active = True
        from src.framework.entities.states import ShortAttackState
        player._state_instance = ShortAttackState()
        player._active_hitbox = pygame.Rect(0, 0, 10, 10)
        dmg = player.current_attack_damage
        expected_base = 0.5
        idx = min(1, len(settings.COMBO_DAMAGE_MULT) - 1)
        assert dmg == expected_base * settings.COMBO_DAMAGE_MULT[idx]

    def test_combo_resets_on_hit(self) -> None:
        """AUD-721 — recibir daño rompe el combo (reporte: no se reiniciaba)."""
        player = Player(pygame.Vector2(0, 0))
        self._golpear(player, Player.SHORT_ATTACK)
        self._golpear(player, Player.SHORT_ATTACK)
        assert player.combo_count == 2
        assert player.combo_active
        player.apply_damage(1.0, (0, 0))
        assert player.combo_count == 0
        assert player.combo_timer == 0.0
        assert not player.combo_active
        assert player.last_attack_type == ""

    def test_combo_resets_on_hit_even_with_invincibility_later(self) -> None:
        """El primer golpe rompe combo aunque el segundo se ignore por i-frame."""
        player = Player(pygame.Vector2(0, 0))
        self._golpear(player, Player.SHORT_ATTACK)
        assert player.combo_count == 1
        player.apply_damage(1.0, (0, 0))
        assert player.combo_count == 0
        # segundo golpe dentro de invencibilidad no debe revivir combo
        player.apply_damage(1.0, (0, 0))
        assert player.combo_count == 0
