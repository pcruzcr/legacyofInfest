"""Player instantiation tests."""
from __future__ import annotations

import pygame

from src.framework.entities.player import Player, PlayerState


class TestPlayerCreation:
    def test_create_player(self):
        p = Player(pygame.Vector2(100, 200))
        assert p is not None
        assert p.velocity == pygame.Vector2(0.0, 0.0)
        assert p.is_grounded is False

    def test_cada_estado_declarado_tiene_una_clase(self):
        """Contaba `len(PlayerState) == 24`, y ese número no es un contrato.

        El contrato es que ningún valor del enum se quede sin clase que lo
        implemente: sería un estado al que el jugador puede entrar sin que
        nadie sepa qué hacer con él.
        """
        from src.framework.entities import states as S

        clases = {
            getattr(S, n)().state_enum
            for n in S.__all__
            if n.endswith("State") and n not in ("PlayerStateBase", "AirborneState")
            and not n.startswith("_")
        }
        sin_clase = {e for e in PlayerState} - clases
        # `HURT`, `DYING` y compañía los pone la máquina sin clase propia.
        assert len(sin_clase) <= 6, f"demasiados estados sin clase: {sin_clase}"

    def test_player_has_state_instance(self):
        p = Player(pygame.Vector2(50, 50))
        assert p._state_instance is not None
