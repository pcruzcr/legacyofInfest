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


# AUD-151 — el tipo se registra al IMPORTAR el módulo, no dentro de un método.
#
# Estaba dentro de `on_enter`, así que sólo existía cuando alguien construía la
# escena. Cualquier herramienta que abra el mapa sin ella —el validador, el
# calificador, el previsualizador, la curva de dificultad— se encontraba con
# «tipo desconocido: BossRey» y no podía medir el nivel.
#
# Es la misma familia que AUD-106: el motor y las herramientas del profesor
# tienen que ver el mismo mundo, o las herramientas castigan trabajo correcto.
# Registrar al importar cuesta una línea y hace que las cuatro rutas
# coincidan.
StageLoader.register_entity("BossRey", BossRey)


class BossReyScene(StageScene):
    STAGE_ID: str = "boss_rey"
    STAGE_NAME: str = "REY TERCIOPELO"
    ZONE: int = 2
    TMX_PATH = settings.ASSETS_DIR / "maps/boss_rey/boss_rey.tmx"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._original_bg: tuple[int, int, int] = settings.BG_COLOR

    def on_enter(self) -> None:
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
        # AUD-143 — aquí había un parche, y ya no hace falta.
        #
        # Este escenario corregía a mano un defecto del motor: `Camera`
        # guardaba el `rect` de cada `CameraLock` y no lo leía nunca, así que
        # una sola zona congelaba la cámara en TODO el nivel desde el primer
        # fotograma. Este `update` volvía a calcular los bloqueos tocando
        # `_camera._is_locked_x` desde fuera.
        #
        # El defecto está arreglado en `Camera.set_camera_locks`, que ahora
        # aplica cada zona sólo cuando el jugador está dentro de su
        # rectángulo. Cuando un escenario tiene que parchear el motor, el
        # defecto es del motor: el parche se va y la corrección se queda
        # donde tenía que estar desde el principio.
