from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.stage_loader import StageLoader
from src.stages.boss_rey.boss_rey import BossRey

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

# Gris claro para que el jugador y el boss sean visibles durante la pelea.
# Se restaura el color original al salir de la escena.
_ARENA_BG: tuple[int, int, int] = (180, 180, 190)


class BossReyScene(StageScene):
    STAGE_ID: str = "boss_rey"
    STAGE_NAME: str = "REY TERCIOPELO"
    ZONE: int = 2
    TMX_PATH = settings.ASSETS_DIR / "maps/boss_rey/boss_rey.tmx"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._original_bg: tuple[int, int, int] = settings.BG_COLOR

    def on_enter(self) -> None:
        # El objeto "BossRey" del TMX necesita una clase Python registrada
        # para poder aparecer. Esa tabla vive en
        # src/framework/entities/entity_factory.py, fuera de mi carpeta, así
        # que en vez de tocarla registro mi propio tipo aquí, antes de que
        # StageScene.on_enter() cargue el TMX. StageLoader.load() llama
        # internamente a ensure_registered(), que solo completa lo que falte
        # y no borra lo ya registrado, así que esta línea persiste sin tocar
        # nada del profesor.
        StageLoader.register_entity("BossRey", BossRey)
        settings.BG_COLOR = _ARENA_BG
        super().on_enter()
        # Iluminación al máximo para que el jugador y el boss sean visibles
        # sobre el fondo gris durante el prototipo funcional (Práctica I).
        self._lighting.ambient_brightness = 1.0

        # stage_scene.py fija arena_bounds = TODO el mapa (map_pixel_size),
        # sin saber que ahora el mapa incluye el corredor de entrada además
        # de la sala del jefe. Lo corrijo aquí al rect exacto de la sala
        # (el mismo CameraLock que ya defino en el TMX), para que el Rey
        # Terciopelo no camine fuera de su sala hacia el corredor.
        #
        # El suelo se informa aparte, desde el rect de colisión "Floor": la
        # altura a la que camina el jefe no debe depender de dónde esté
        # encuadrada la cámara. Ver `BossRey._floor_y`.
        if self._stage_data is not None and self._stage_data.camera_locks:
            room_rect = self._stage_data.camera_locks[0].rect
            floor_y = self._find_floor_surface_y(room_rect)
            for entity in self._stage_data.entity_list:
                if isinstance(entity, BossRey):
                    entity.set_arena_bounds(room_rect)
                    if floor_y is not None:
                        entity.floor_surface_y = floor_y

    def _find_floor_surface_y(self, room_rect: pygame.Rect) -> float | None:
        """Borde superior del suelo bajo la sala del jefe.

        Entre los rects de colisión busca los que cruzan la sala a lo ancho
        y quedan por debajo de su centro; el suelo es el más alto de ellos
        (el de menor `top`), que es sobre el que se camina.
        """
        if self._stage_data is None:
            return None
        candidates = [
            rect for rect in self._stage_data.collision_rects
            if rect.top >= room_rect.centery
            and rect.left <= room_rect.centerx <= rect.right
        ]
        return float(min(rect.top for rect in candidates)) if candidates else None

    def on_exit(self) -> None:
        settings.BG_COLOR = self._original_bg
        super().on_exit()

    def update(self, dt: float) -> None:
        super().update(dt)
        # stage_scene.py llama a camera.set_camera_locks(stage.camera_locks)
        # cada frame sin condición de posición: en Camera.set_camera_locks
        # (src/framework/stage/camera.py) el campo `rect` de cada CameraLock
        # se guarda pero nunca se lee -- solo hace
        # `any(line.lock_x for line in locks)`, así que un solo CameraLock en
        # el mapa congela la cámara en TODO el nivel desde el frame 1, no
        # solo dentro de su rect. Con el corredor nuevo eso bloquearía la
        # cámara también ahí. Lo corrijo aquí, después de que el framework
        # ya aplicó su lock global, activándolo solo cuando el jugador está
        # dentro del rect real de la sala del jefe.
        if self._stage_data is not None and self._stage_data.camera_locks and self._player is not None:
            room_rect = self._stage_data.camera_locks[0].rect
            in_room = room_rect.collidepoint(self._player.rect.center)
            self._camera._is_locked_x = in_room
            self._camera._is_locked_y = in_room
