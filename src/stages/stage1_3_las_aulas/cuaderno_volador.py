"""
Module: cuaderno_volador
System: stage1_3_las_aulas (entidad propia del estudiante)
Academic Unit: Unidad III — Curvas basicas (Bezier)

Autor: Yariel — nivel "Las Aulas"

Cuaderno infectado que recorre el aula siguiendo una CURVA DE BEZIER calculada
matematicamente con `CurveTools.bezier()`.

FORMULA (base de Bernstein), tal como la implementa
`CurveTools._eval_bernstein()`:

    B(t) = SUMA_{i=0}^{n}  C(n, i) * t^i * (1 - t)^(n - i) * P_i ,   t en [0, 1]

con C(n, i) = n! / (i! (n - i)!)  el coeficiente binomial.

Para los 4 puntos de control que usa este nivel (curva cubica, n = 3) queda:

    B(t) = (1-t)^3 P0  +  3(1-t)^2 t P1  +  3(1-t) t^2 P2  +  t^3 P3

Propiedades que se aprovechan:
  - B(0) = P0 y B(1) = P3: la curva ARRANCA y TERMINA en los extremos, asi
    que el recorrido es predecible y se puede alinear con la geometria del aula.
  - P1 y P2 NO se tocan: solo "atraen" a la curva.  Por eso el cuaderno hace
    un arco suave por encima de los pupitres en vez de pasar entre ellos.
  - La curva vive dentro del poligono convexo de sus puntos de control, o sea
    que nunca se sale de la caja formada por P0..P3: no puede atravesar el
    techo ni el piso si los puntos estan bien puestos.

NOTA TECNICA: el motor ya trae `EnemyFlying` con `flight_mode="bezier"`, pero
ese camino llama a `CurveTools.build_bezier_path()`, que internamente evalua
`_eval_catmull()` — es una spline de Catmull-Rom, no una Bezier.  Esta entidad
usa `CurveTools.bezier()`, que si evalua la base de Bernstein.

RENDIMIENTO: la curva se muestrea UNA sola vez al crear la entidad
(`CurveTools.bezier`) y despues cada frame solo se interpola sobre esa lista
con `CurveTools.sample_path()`.  Evaluar Bernstein 60 veces por segundo seria
desperdiciar CPU calculando siempre los mismos puntos.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.math_utils import vec2_normalize
from src.framework.entities.enemy_base import EnemyBase, EnemyState
from src.framework.processing.curve_tools import CurveTools
from src.framework.stage.stage_loader import StageLoader


def _a_float(valor, por_defecto: float) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return por_defecto


class CuadernoVolador(EnemyBase):
    """Cuaderno que planea por el aula siguiendo una curva de Bezier."""

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        waypoints: list[tuple[float, float]] | None = None,
        periodo=6.0,
        muestras=160,
        factor_alerta=1.8,
        max_health: float = 1.0,
        damage_on_contact: float = 0.5,
        zone: int = 1,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=180.0,
            detection_range_y=120.0,
        )

        # El sprite enemy_fly_zone1.png mide 56x10 = 4 marcos de 14x10.
        # El rect debe coincidir para que el dibujo y las cajas no se
        # desalineen (cortarlo en 16x12 da 0 marcos y sale el placeholder).
        self.rect.width = 14
        self.rect.height = 10

        self.periodo: float = max(0.5, _a_float(periodo, 6.0))
        self.factor_alerta: float = _a_float(factor_alerta, 1.8)
        n_muestras = max(16, int(_a_float(muestras, 160.0)))

        # --- Puntos de control ---
        # Vienen de los objetos type="Waypoint" del TMX cuyo owner_id coincide
        # con el nombre de esta entidad (StageLoader los inyecta como kwarg).
        # Si no hay, se usa un arco por defecto relativo al spawn.
        if waypoints and len(waypoints) >= 2:
            self.puntos_control: list[tuple[float, float]] = [
                (float(x), float(y)) for x, y in waypoints
            ]
        else:
            ox, oy = float(spawn_position.x), float(spawn_position.y)
            self.puntos_control = [
                (ox, oy),
                (ox + 80.0, oy - 96.0),
                (ox + 176.0, oy - 96.0),
                (ox + 256.0, oy),
            ]

        # --- Muestreo de la curva: UNA sola vez ---
        self.camino: list[tuple[float, float]] = CurveTools.bezier(
            self.puntos_control, n_muestras
        )

        # Parametro de recorrido y sentido (va y vuelve sobre la misma curva)
        self._t: float = 0.0
        self._sentido: float = 1.0

        self.mostrar_curva: bool = False
        self._sup_curva: pygame.Surface | None = None

        self._load_zone_sprites(int(zone) if zone else 1, 14, 10)

        # Colocarse ya sobre el inicio de la curva
        self._ubicar_en(self._t)

    # ── Recorrido de la curva ──────────────────────────────────────────

    def _ubicar_en(self, t: float) -> None:
        """Coloca la entidad en B(t) usando el camino ya muestreado."""
        x, y = CurveTools.sample_path(self.camino, t)
        self.position.x = x - self.rect.width / 2.0
        self.position.y = y - self.rect.height / 2.0

    def _orientar(self, t: float) -> None:
        """Mira hacia donde avanza, usando la direccion entre dos muestras
        consecutivas de la curva (aproximacion de la tangente):

            tangente ~ vec2_normalize( B(t + h) - B(t) )
        """
        h = 0.01
        t_sig = min(1.0, max(0.0, t + h * self._sentido))
        ax, ay = CurveTools.sample_path(self.camino, t)
        bx, by = CurveTools.sample_path(self.camino, t_sig)
        avance = pygame.Vector2(bx - ax, by - ay)
        if avance.length_squared() > 0.0:
            tangente = vec2_normalize(avance)
            if abs(tangente.x) > 1e-6:
                self.facing_direction = 1 if tangente.x > 0 else -1

    def _recorrer(self, dt: float, velocidad: float = 1.0) -> None:
        """Avanza el parametro t y reubica la entidad.

        t va de 0 a 1 y vuelve de 1 a 0 (ida y vuelta), a razon de
        1/periodo por segundo.  Como t es adimensional, cambiar `periodo`
        cambia la rapidez SIN tocar la forma de la curva: la geometria y el
        tiempo quedan desacoplados.
        """
        self._t += self._sentido * velocidad * dt / self.periodo
        if self._t >= 1.0:
            self._t = 1.0
            self._sentido = -1.0
        elif self._t <= 0.0:
            self._t = 0.0
            self._sentido = 1.0
        self._orientar(self._t)
        self._ubicar_en(self._t)

    def _patrol_behavior(self, dt: float) -> None:
        self._recorrer(dt, 1.0)

    def _alert_behavior(self, dt: float) -> None:
        """Misma curva, mas rapido: el jugador lo altera pero no lo saca de
        su trayectoria."""
        self._recorrer(dt, self.factor_alerta)

    # ── Presentacion ───────────────────────────────────────────────────

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        ruta = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key / f"enemy_fly_{zone_key}.png"
        try:
            self._sprite_frames["fly"] = AssetLoader.load_sprite_sheet(Path(ruta), fw, fh)
        except (pygame.error, FileNotFoundError, PermissionError):
            logging.warning("cuaderno_volador: no se pudo cargar %s", ruta)

    def _get_animation_key(self) -> str:
        return "fly"

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 14, 10)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Dibuja el cuaderno y, con F1, la curva y sus puntos de control."""
        if self.mostrar_curva and self.state != EnemyState.DYING:
            puntos = [
                (int(x - camera_offset.x), int(y - camera_offset.y))
                for x, y in self.camino
            ]
            if len(puntos) >= 2:
                pygame.draw.lines(surface, (120, 220, 255), False, puntos, 1)
            for i, (cx, cy) in enumerate(self.puntos_control):
                px = int(cx - camera_offset.x)
                py = int(cy - camera_offset.y)
                # P0 y P3 (la curva pasa por ellos) en verde; P1 y P2 en naranja
                extremo = i in (0, len(self.puntos_control) - 1)
                color = (80, 255, 120) if extremo else (255, 170, 60)
                pygame.draw.circle(surface, color, (px, py), 3)
        super().draw(surface, camera_offset)


StageLoader.register_entity("CuadernoVolador", CuadernoVolador)
