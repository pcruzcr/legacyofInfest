"""
Module: stage3_1_la_entrada_de_piedra
System: stage (student assignment)
Academic Unit: See README.md front-matter for units_demonstrated.

Zona 3 - Heredia. Stage 3-1: "La Entrada de Piedra" — el camino de
entrada a la sede INVENIO Heredia, inspirado en la entrada real del
campus (edificio principal, pasillo techado y camino ajardinado).

Test with:
   python main.py --stage stage3_1_la_entrada_de_piedra
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core.events import Events
from src.engine.utils.math_utils import vec2_distance, vec2_normalize
from src.framework.entities.enemy_shooter import EnemyShooter
from src.framework.processing.color_tools import ColorTools
from src.framework.processing.curve_tools import CurveTools
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage3_1_LaEntradaDePiedra(StageScene):
    """Zona 3, Heredia: camino de entrada a INVENIO Heredia.

    Bloque A: detección vectorial explícita sobre los ShooterQuetzal
    (Unidad II) y un ornamento decorativo que sigue una trayectoria
    curva calculada con CurveTools (Unidad III). Ninguna de las dos
    cosas modifica entidades del framework ni el registro de tipos:
    ambas viven enteramente en esta clase de escenario.
    """

    STAGE_ID: str = "3-1"
    STAGE_NAME: str = "3-1 LA ENTRADA DE PIEDRA"
    ZONE: int = 3

    # AUD-106 — ruta corregida al integrar la entrega.
    #
    # El mapa estaba junto al código. La convención del proyecto es
    # `assets/maps/<nombre>/<nombre>.tmx`, que es donde lo buscan el
    # validador, el calificador y el previsualizador. Duplicar el TMX en
    # dos sitios habría garantizado que algún día divergieran.
    TMX_PATH = "assets/maps/stage3_1_la_entrada_de_piedra/stage3_1_la_entrada_de_piedra.tmx"

    # ── Unidad II: detección vectorial explícita ──────────────────────
    # Distancia (px) a partir de la cual telegrafiamos la línea de tiro
    # de un ShooterQuetzal. No sustituye la detección propia de
    # EnemyShooter (que sigue intacta); es una capa de aviso adicional
    # que opera sobre las entidades ya existentes usando vec2_distance
    # y vec2_normalize de math_utils.py, tal como se acordó (opción
    # conservadora, sin subclases ni registro de entidades).
    QUETZAL_TELEGRAPH_RANGE: float = 180.0

    # ── Unidad III: ornamento con trayectoria curva (CurveTools) ──────
    # Un farol de piedra que oscila entre los dos arcos siguiendo una
    # trayectoria Catmull-Rom (CurveTools.build_bezier_path), distinta
    # del vuelo senoidal del FlyingHalcon (que no usa CurveTools).
    CURVE_WAYPOINTS: tuple[tuple[float, float], ...] = (
        (592.0, 60.0),
        (612.0, 92.0),
        (628.0, 92.0),
        (648.0, 60.0),
    )
    CURVE_PERIOD: float = 6.0

    # ── Unidad V: paso de nubes (HSL) ─────────────────────────────────
    # Transición sol cálido <-> sombra fría sobre el camino, calculada
    # con ColorTools.hsl_to_rgb (no con el sistema de hora/estación de
    # StageScene, que usa su propio tinte y no ColorTools). La nube es
    # una forma visible que recorre el mapa; la sombra se oscurece en
    # función de qué tan cerca está la nube del jugador, no de un
    # cronómetro desacoplado — así la causa (la nube) y el efecto (la
    # sombra) están visiblemente conectados.
    CLOUD_SPEED: float = 150.0      # px/s, recorrido por el mapa
    CLOUD_WIDTH: float = 150.0      # ancho de la sombra que proyecta
    SUN_HUE: float = 45.0
    SUN_LIGHT: float = 0.80
    SHADE_HUE: float = 215.0
    SHADE_LIGHT: float = 0.40
    CLOUD_SATURATION: float = 0.35

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))
        self._quetzal_telegraphs: list[tuple[pygame.Vector2, pygame.Vector2, float]] = []
        self._quetzal_in_range: set[int] = set()
        self._curve_t: float = 0.0
        self._curve_waypoints = [pygame.Vector2(p) for p in self.CURVE_WAYPOINTS]
        self._curve_ornament_pos: pygame.Vector2 | None = self._curve_waypoints[0]
        self._cloud_t: float = 0.0
        self._cloud_x: float = -self.CLOUD_WIDTH

    # ── Lifecycle hooks ──────────────────────────────────────────────
    # Sin hooks de StageScene sobreescritos: el comportamiento por
    # defecto (tutorial, checkpoints, trigger de fin de nivel) corre
    # sin cambios. La lógica propia de esta etapa vive en update()/
    # draw(), siempre llamando a super() primero.

    def update(self, dt: float) -> None:
        super().update(dt)
        self._update_quetzal_telegraphs()
        self._update_curve_ornament(dt)
        self._update_cloud(dt)

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        self._draw_cloud_shadow(surface)
        self._draw_cloud_shape(surface)
        self._draw_quetzal_telegraphs(surface)
        self._draw_curve_ornament(surface)

    # ── Unidad II: implementación ─────────────────────────────────────

    def _update_quetzal_telegraphs(self) -> None:
        """Recalcula, cada frame, la línea de tiro de cada ShooterQuetzal
        vivo, usando aritmética vectorial explícita (vec2_distance,
        vec2_normalize). La distancia no solo decide si se dibuja la
        línea: decide si el jugador ACABA de entrar en rango de disparo,
        y en ese caso dispara un aviso en pantalla una sola vez (no en
        cada frame que permanezca dentro) — una decisión real, no solo
        un dato para dibujar."""
        self._quetzal_telegraphs = []
        if self._player is None or self._stage_data is None:
            return
        player_pos = pygame.Vector2(self._player.rect.center)
        currently_in_range: set[int] = set()
        for entity in self._stage_data.entity_list:
            if not isinstance(entity, EnemyShooter) or not entity.is_alive:
                continue
            shooter_pos = pygame.Vector2(entity.rect.center)
            distance = vec2_distance(shooter_pos, player_pos)
            in_range = distance <= self.QUETZAL_TELEGRAPH_RANGE
            if in_range:
                direction = vec2_normalize(player_pos - shooter_pos)
                self._quetzal_telegraphs.append((shooter_pos, direction, distance))
                currently_in_range.add(id(entity))
                # Flanco de subida: la entidad recién entró en rango de
                # disparo. La decisión de avisar depende únicamente del
                # resultado de vec2_distance, no de un temporizador ni
                # de la lógica interna del EnemyShooter.
                if id(entity) not in self._quetzal_in_range:
                    self.context.event_bus.emit(
                        Events.SHOW_MESSAGE,
                        text="¡Quetzal en rango de disparo!",
                        duration=1.5,
                    )
        self._quetzal_in_range = currently_in_range

    def _draw_quetzal_telegraphs(self, surface: pygame.Surface) -> None:
        offset = self._camera.offset
        for shooter_pos, direction, distance in self._quetzal_telegraphs:
            end = shooter_pos + direction * distance
            start = (shooter_pos.x - offset.x, shooter_pos.y - offset.y)
            finish = (end.x - offset.x, end.y - offset.y)
            pygame.draw.line(surface, (255, 70, 70), start, finish, 1)

    # ── Unidad III: implementación ────────────────────────────────────

    def _update_curve_ornament(self, dt: float) -> None:
        """Mueve el farol decorativo a lo largo de una trayectoria
        Catmull-Rom entre los dos arcos, con un avance triangular
        (ida y vuelta) en vez de un simple reinicio brusco."""
        self._curve_t += dt
        cycle = (self._curve_t % self.CURVE_PERIOD) / self.CURVE_PERIOD
        progress = cycle * 2.0 if cycle <= 0.5 else 2.0 - cycle * 2.0
        self._curve_ornament_pos = CurveTools.build_bezier_path(
            self._curve_waypoints, progress,
        )

    def _draw_curve_ornament(self, surface: pygame.Surface) -> None:
        if self._curve_ornament_pos is None:
            return
        offset = self._camera.offset
        pos = self._curve_ornament_pos
        x = int(pos.x - offset.x)
        y = int(pos.y - offset.y)
        pygame.draw.line(surface, (90, 70, 55), (x, y - 8), (x, y), 1)
        pygame.draw.circle(surface, (170, 90, 60), (x, y + 2), 3)

    # ── Unidad V: implementación ──────────────────────────────────────

    def _update_cloud(self, dt: float) -> None:
        """Avanza la nube a lo largo del mapa (de punta a punta y de
        vuelta), a velocidad constante en px/s."""
        map_w = self._stage_data.map_pixel_size[0] if self._stage_data else 560
        travel = map_w + self.CLOUD_WIDTH * 2
        self._cloud_t += dt
        offset = (self._cloud_t * self.CLOUD_SPEED) % (travel * 2)
        if offset <= travel:
            self._cloud_x = -self.CLOUD_WIDTH + offset
        else:
            self._cloud_x = -self.CLOUD_WIDTH + (travel * 2 - offset)

    def _current_shade_factor(self) -> float:
        """0 = sol pleno, 1 = sombra máxima. Depende de la distancia
        real entre la nube y el jugador, no de un cronómetro suelto."""
        if self._player is None:
            return 0.0
        dist = abs(self._player.position.x - self._cloud_x)
        return max(0.0, 1.0 - dist / self.CLOUD_WIDTH)

    def _draw_cloud_shadow(self, surface: pygame.Surface) -> None:
        """Tiñe la escena entre un tono cálido de sol y uno frío de
        sombra, usando ColorTools.hsl_to_rgb, más marcado cuanto más
        cerca esté la nube del jugador."""
        shade = self._current_shade_factor()
        hue = self.SUN_HUE + (self.SHADE_HUE - self.SUN_HUE) * shade
        light = self.SUN_LIGHT + (self.SHADE_LIGHT - self.SUN_LIGHT) * shade
        r, g, b = ColorTools.hsl_to_rgb(hue, self.CLOUD_SATURATION, light)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        alpha = int(10 + shade * 120)
        overlay.fill((r, g, b, alpha))
        surface.blit(overlay, (0, 0))

    def _draw_cloud_shape(self, surface: pygame.Surface) -> None:
        """Dibuja la nube en sí (no solo su efecto) para que el paso de
        nubes sea reconocible a simple vista, no solo un cambio de
        tinte ambiguo."""
        offset = self._camera.offset
        cx = int(self._cloud_x - offset.x)
        cy = 30
        cloud_r, cloud_g, cloud_b = ColorTools.hsl_to_rgb(self.SHADE_HUE, 0.10, 0.85)
        for dx, dy, radius in ((-30, 4, 16), (0, -6, 22), (30, 4, 18), (55, 6, 13)):
            pygame.draw.circle(surface, (cloud_r, cloud_g, cloud_b), (cx + dx, cy + dy), radius)
