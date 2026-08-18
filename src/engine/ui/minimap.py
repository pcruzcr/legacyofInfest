from __future__ import annotations

from collections.abc import Sequence

import pygame

from src.engine.ui.hud import minimap_rect_por_defecto


class Minimap:
    """Minimap overlay showing explored rooms, player position, and enemies."""

    def __init__(self, x: int | None = None, y: int | None = None) -> None:
        self._map_size: tuple[int, int] = (0, 0)
        self._explored_rects: list[pygame.Rect] = []
        self._player_pos: tuple[float, float] = (0.0, 0.0)
        self._player_dir: int = 1
        self._enemy_positions: Sequence[tuple[float, float]] = []
        self._boss_positions: Sequence[tuple[float, float]] = []
        self._checkpoint_positions: Sequence[tuple[float, float]] = []
        self._activated_checkpoints: set[int] = set()
        self._visible: bool = True

        # Minimap dimensions — AUD-499.
        #
        # Antes eran 80x56 fijos en `INTERNAL_WIDTH - 84, 4`: píxeles de
        # pantalla, sin pasar por la escala de interfaz. Eso dejaba una caja
        # del tamaño del diseño de 320 clavada en el borde de una pantalla de
        # 800 — pequeña de más y, peor, encima del cronómetro, que ocupa el
        # borde derecho de la maqueta del HUD.
        #
        # Ahora el hueco lo decide el HUD (`HUD.minimap_rect`), que es quien
        # conoce la franja entera; esto sólo lo obedece. Los valores de aquí
        # son la reserva para quien construya un `Minimap` suelto —las
        # pruebas y las entregas de estudiantes lo hacen— y van a la misma
        # escala que el resto de la interfaz.
        recuadro = minimap_rect_por_defecto()
        self._minimap_w: int = recuadro.width
        self._minimap_h: int = recuadro.height
        self._minimap_x: int = x if x is not None else recuadro.x
        self._minimap_y: int = y if y is not None else recuadro.y

    def colocar(self, rect: pygame.Rect) -> None:
        """Mueve y redimensiona el minimapa a ese recuadro (AUD-499).

        Lo llama `StageScene` con `HUD.minimap_rect()`. Se recalcula la
        escala porque depende del tamaño: sin esto, cambiar el recuadro
        dibujaría el mapa con la proporción del anterior.
        """
        self._minimap_x, self._minimap_y = rect.x, rect.y
        self._minimap_w, self._minimap_h = rect.width, rect.height
        ancho, alto = getattr(self, "_map_size", (0, 0))
        if ancho and alto:
            self.set_map_size(ancho, alto)

        # Pixel per world unit scaling - auto-calculated
        self._scale: float = 1.0

        self._bg_color: tuple[int, int, int] = (10, 10, 20)
        self._border_color: tuple[int, int, int] = (60, 60, 80)
        self._explored_color: tuple[int, int, int] = (30, 40, 60)
        self._player_color: tuple[int, int, int] = (100, 220, 255)
        self._enemy_color: tuple[int, int, int] = (255, 80, 80)
        self._boss_color: tuple[int, int, int] = (255, 50, 50)
        self._checkpoint_color: tuple[int, int, int] = (255, 220, 80)
        self._fog_color: tuple[int, int, int] = (5, 5, 15)

        self._fow_surf: pygame.Surface | None = None
        # Se declara aquí aunque se cree perezosamente en `draw`. Antes nacía
        # dentro de `draw` tras un `hasattr(self, '_bg_surf')`, lo que significa
        # que entre construir un Minimap y dibujarlo el objeto tenía un
        # conjunto de atributos distinto: cualquier código que lo inspeccionara
        # —una prueba, un panel de depuración, un serializador— veía una cosa
        # u otra según el momento. Un atributo que a veces existe es más difícil
        # de razonar que uno que a veces es None.
        self._bg_surf: pygame.Surface | None = None
        # AUD-535 — "máscara circular o de bordes totalmente redondeados,
        # eliminando los bordes cuadrados agresivos". El recuadro no es
        # cuadrado (62×44 en la maqueta), así que un círculo de verdad
        # desperdiciaría espacio a los lados; el radio máximo que cabe
        # (`min(w,h)//2`) da la variante "bordes totalmente redondeados"
        # que el propio pedido ofrece como alternativa. La máscara se
        # reconstruye sólo aquí (al colocar/redimensionar), no en cada
        # `draw()` — mismo criterio de rendimiento que AUD-527.
        self._radio_del_marco: int = min(self._minimap_w, self._minimap_h) // 2
        self._mascara_redondeada: pygame.Surface | None = None

    def set_map_size(self, world_w: int, world_h: int) -> None:
        self._map_size = (world_w, world_h)
        sx = self._minimap_w / max(world_w, 1)
        sy = self._minimap_h / max(world_h, 1)
        self._scale = min(sx, sy, 1.0)

    def explore_rect(self, rect: pygame.Rect) -> None:
        for er in self._explored_rects:
            if er.contains(rect):
                return
        self._explored_rects.append(rect.copy())

    def update(
        self,
        player_pos: tuple[float, float],
        player_dir: int,
        enemy_positions: Sequence[tuple[float, float]],
        boss_positions: Sequence[tuple[float, float]],
        checkpoint_positions: Sequence[tuple[float, float]],
        activated_checkpoints: set[int],
    ) -> None:
        self._player_pos = player_pos
        self._player_dir = player_dir
        self._enemy_positions = enemy_positions
        self._boss_positions = boss_positions
        self._checkpoint_positions = checkpoint_positions
        self._activated_checkpoints = activated_checkpoints

    def _world_to_minimap_local(self, wx: float, wy: float) -> tuple[int, int]:
        """Coordenadas dentro del lienzo local del minimapa (0,0 = su
        propia esquina), no de la pantalla — AUD-535: todo el contenido se
        compone en `self._bg_surf` antes de recortarlo en redondo."""
        mx = int(wx * self._scale)
        my = int(wy * self._scale)
        return mx, my

    def draw(self, surface: pygame.Surface) -> None:
        if not self._visible:
            return

        if self._bg_surf is None or self._bg_surf.get_size() != (self._minimap_w, self._minimap_h):
            self._bg_surf = pygame.Surface((self._minimap_w, self._minimap_h), pygame.SRCALPHA)
        lienzo = self._bg_surf
        lienzo.fill((*self._bg_color, 200))

        # Explored areas
        for rect in self._explored_rects:
            rx, ry = self._world_to_minimap_local(rect.x, rect.y)
            rw = max(1, int(rect.width * self._scale))
            rh = max(1, int(rect.height * self._scale))
            pygame.draw.rect(lienzo, self._explored_color, (rx, ry, rw, rh))

        # Checkpoints
        for i, (cx, cy) in enumerate(self._checkpoint_positions):
            color = self._checkpoint_color if i in self._activated_checkpoints else (80, 70, 40)
            mx, my = self._world_to_minimap_local(cx, cy)
            pygame.draw.rect(lienzo, color, (mx - 1, my - 1, 3, 3))

        # Enemies
        for ex, ey in self._enemy_positions:
            mx, my = self._world_to_minimap_local(ex, ey)
            pygame.draw.rect(lienzo, self._enemy_color, (mx - 1, my - 1, 2, 2))

        # Bosses
        for bx, by in self._boss_positions:
            mx, my = self._world_to_minimap_local(bx, by)
            pygame.draw.rect(lienzo, self._boss_color, (mx - 2, my - 2, 4, 4))

        # Player arrow
        px, py = self._player_pos
        mx, my = self._world_to_minimap_local(px, py)
        dir_arrow = self._player_dir
        points = [
            (mx + dir_arrow * 3, my),
            (mx - dir_arrow * 2, my - 2),
            (mx - dir_arrow * 2, my + 2),
        ]
        pygame.draw.polygon(lienzo, self._player_color, points)

        # AUD-535 — recorte de bordes redondeados: todo lo de arriba se
        # dibujó en el lienzo local, y aquí se recorta de una sola vez en
        # vez de recortar cada elemento por separado.
        if (self._mascara_redondeada is None
                or self._mascara_redondeada.get_size() != (self._minimap_w, self._minimap_h)):
            mascara = pygame.Surface((self._minimap_w, self._minimap_h), pygame.SRCALPHA)
            pygame.draw.rect(mascara, (255, 255, 255, 255), mascara.get_rect(),
                             border_radius=self._radio_del_marco)
            self._mascara_redondeada = mascara
        lienzo.blit(self._mascara_redondeada, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(lienzo, (self._minimap_x, self._minimap_y))

        pygame.draw.rect(
            surface, self._border_color,
            (self._minimap_x, self._minimap_y, self._minimap_w, self._minimap_h),
            width=1, border_radius=self._radio_del_marco,
        )
