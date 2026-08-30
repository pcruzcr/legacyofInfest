"""
RoomTransition genérica — extraída de Guillermo 1-2, nativa.

Antes solo stage1_2 tenía ROOM_LIMIT_X vs TRIGGER_X con CutsceneScript.
Ahora cualquier stage declara RoomTransition(rect, trigger_x) y el sistema la maneja.
"""

from __future__ import annotations

import pygame


class RoomTransition:
    def __init__(self, rect: pygame.Rect, trigger_x: float, limit_x: float) -> None:
        self.rect = rect
        self.trigger_x = trigger_x
        self.limit_x = limit_x
        self.activa = False

    def update(self, player_rect: pygame.Rect) -> bool:
        if player_rect.centerx >= self.trigger_x:
            self.activa = True
            return True
        return False
