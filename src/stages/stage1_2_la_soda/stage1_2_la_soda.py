"""
Módulo: stage1_2_la_soda
Sistema: stage (asignación del estudiante)
Unidad académica: ver el front-matter de README.md para units_demonstrated.

Copiado y adaptado desde student_templates/stage_template/ siguiendo sus
propias instrucciones. No modifica StageScene ni ningún código del
engine/framework.

Probar con:
   python main.py --stage stage1_2_la_soda
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.framework.entities.enemy_base import EnemyBase
from src.framework.processing.color_tools import ColorTools
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.stage_loader import StageLoader
from src.stages.stage1_2_la_soda.entities import FlyingCucaracha, WalkerRaton

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

# Registra las entidades propias para que el .tmx pueda referenciarlas por
# nombre de tipo. Corre una sola vez al importar el módulo, mucho antes de
# que cualquier StageScene cargue el mapa. Claves con prefijo "LaSoda" para
# evitar choque con bestiary_registry.py del profe, que auto-registra las
# especies genéricas "WalkerRaton" / "FlyingCucaracha" y, si no, las
# pisaría en silencio.
StageLoader.register_entity("LaSodaWalkerRaton", WalkerRaton)
StageLoader.register_entity("LaSodaFlyingCucaracha", FlyingCucaracha)


class Stage1_2_LaSoda(StageScene):
    """Stage 1-2 — La Soda. Cafetería universitaria, en pleno caos.
    Demo básica de movimiento/traversal — todavía no es la asignación
    completa (ver docs/16_WORLD_DESIGN.md §3.3 para el brief de diseño
    completo)."""

    STAGE_ID: str = "stage1_2_la_soda"
    STAGE_NAME: str = "1-2  LA SODA"
    ZONE: int = 1
    TIME_LIMIT: int = 150
    BGM_TRACK: str = "bgm_zone1"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path("assets/maps/stage1_2_la_soda/stage1_2_la_soda.tmx"))

    def on_stage_start(self) -> None:
        super().on_stage_start()
        # Esta stage entra completa en una sola pantalla (mapa de 768x608
        # vs. un viewport de 800x600), así que el fog-of-war del minimapa
        # que se revela a medida que avanzás (StageScene._update_minimap,
        # que solo hace explore_rect() de una caja de 160x120 alrededor
        # del jugador cada frame) nunca tiene nada más que revelar —
        # simplemente se ve como "el mapa parece sin explorar" sin ninguna
        # razón real. Marcar todo el mapa como explorado de una vez, al
        # inicio, hace que se vea como un mapa estático real desde el
        # primer frame. Los enemigos ya se dibujan como puntos rojos ahí
        # automáticamente (StageScene lee cada EnemyBase vivo en
        # entity_list) — no hace falta cablear nada extra.
        if self._stage_data is not None:
            self._minimap.explore_rect(
                pygame.Rect(0, 0, *self._stage_data.map_pixel_size),
            )

    def on_player_landed(self) -> None:
        super().on_player_landed()

    def on_enemy_died(self, enemy) -> None:
        super().on_enemy_died(enemy)

    def on_next_trigger_entered(self) -> None:
        super().on_next_trigger_entered()

    def on_debug_toggle(self, enabled: bool) -> None:
        super().on_debug_toggle(enabled)

    def draw(self, surface: pygame.Surface) -> None:
        """Extiende el renderizado del framework con una barra de vida por
        enemigo. Nunca sobreescribe internals del framework directamente —
        solo dibuja UI extra encima, después de llamar a la implementación
        base."""
        super().draw(surface)
        self._draw_enemy_health_bars(surface)

    def _draw_enemy_health_bars(self, surface: pygame.Surface) -> None:
        if self._stage_data is None:
            return
        offset = self._camera.offset
        for entity in self._stage_data.entity_list:
            if not (isinstance(entity, EnemyBase) and entity.is_alive):
                continue
            pct = max(0.0, min(1.0, entity.current_health / max(entity.max_health, 0.001)))
            if pct >= 1.0:
                continue  # solo se muestra una vez que efectivamente recibió daño
            bar_w = entity.rect.width
            x = int(entity.rect.x - offset.x)
            y = int(entity.rect.y - offset.y) - 6
            pygame.draw.rect(surface, (40, 10, 10), (x, y, bar_w, 3))
            # Unidad V — operación de espacio de color (ColorTools): el
            # matiz del relleno se desliza de verde (120 grados) con vida
            # completa a rojo (0 grados) a medida que baja pct, convertido
            # de HSV a RGB vía ColorTools.hsv_to_rgb, y luego horneado
            # sobre una pequeña superficie blanca con ColorTools.apply_tint
            # (Surface -> Surface) antes de dibujarla. Se observa
            # visualmente en el juego: la barra pasa de verde a amarillo a
            # rojo mientras el enemigo recibe daño.
            fill_w = max(1, int(bar_w * pct))
            hue_deg = 120.0 * pct
            tint_rgb = ColorTools.hsv_to_rgb(hue_deg, 1.0, 1.0)
            fill_surf = pygame.Surface((fill_w, 3))
            fill_surf.fill((255, 255, 255))
            fill_surf = ColorTools.apply_tint(fill_surf, tint_rgb)
            surface.blit(fill_surf, (x, y))
