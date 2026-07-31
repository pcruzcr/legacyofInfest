"""
Module: debug_overlay
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: II (Vectores), III (Curvas) — visualización
Description: Dibuja la matemática de las entidades sobre la pantalla al
pulsar F1. Convierte trabajo que hay que hacer igual en las evidencias
visuales que exige el checklist del README.

Qué muestra:
  · La polilínea de la curva de Bézier de cada CanopyBird (las 64 muestras)
  · Sus 4 puntos de control, numerados P₀..P₃, tal como salieron del TMX
  · El punto actual sobre la curva y el valor de t
  · El radio de detección de cada JungleFrog (círculo, no caja)
  · El vector velocidad de cada proyectil, dibujado desde su posición

TRANSFORMACIÓN MUNDO → PANTALLA
    p_pantalla = p_mundo − offset_camara
Es la misma que aplica el motor en Camera.world_to_screen (camera.py:88).
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

import pygame

from src.stages.stage1_1.entities.canopy_bird import CanopyBird
from src.stages.stage1_1.entities.jungle_frog import JungleFrog

_COL_CURVA = (90, 220, 255)
_COL_CONTROL = (255, 210, 60)
_COL_ACTUAL = (255, 120, 255)
_COL_RADIO = (255, 90, 90)
_COL_VECTOR = (140, 255, 140)
_COL_TEXTO = (235, 235, 235)


class DebugOverlay:
    """Overlay de depuración. Apagado por defecto; F1 lo alterna."""

    def __init__(self) -> None:
        self.enabled: bool = False
        self._font: pygame.font.Font | None = None

    def toggle(self, enabled: bool) -> None:
        self.enabled = bool(enabled)

    # ── Transformación mundo → pantalla ─────────────────────────────

    @staticmethod
    def to_screen(
        points: Sequence[tuple[float, float]],
        camera_offset: pygame.Vector2,
    ) -> list[tuple[int, int]]:
        # ── Transformación Mundo → Pantalla ────────
        # Convierte coordenadas absolutas del mundo del juego a coordenadas 
        # relativas a la vista de la cámara.
        # p_pantalla = p_mundo - offset_camara
        # Se redondea a entero (int) porque Pygame dibuja en píxeles discretos 
        # y pasar floats a las funciones de dibujo suele causar truncamientos 
        # inesperados o errores de tipo.
        ox, oy = camera_offset.x, camera_offset.y
        return [(int(x - ox), int(y - oy)) for x, y in points]

    # ── Dibujo ──────────────────────────────────────────────────────

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
        birds: Iterable[CanopyBird],
        frogs: Iterable[JungleFrog],
    ) -> None:
        if not self.enabled:
            return
        if self._font is None:
            self._font = pygame.font.Font(None, 12)

        for ave in birds:
            self._draw_bird(surface, camera_offset, ave)
        for rana in frogs:
            self._draw_frog(surface, camera_offset, rana)

    # ── Unidad III — la curva y sus puntos de control ───────────────

    def _draw_bird(self, surface: pygame.Surface,
                   off: pygame.Vector2, ave: CanopyBird) -> None:
        ruta = self.to_screen(ave.path, off)
        if len(ruta) >= 2:
            pygame.draw.lines(surface, _COL_CURVA, False, ruta, 1)

        # los 4 puntos de control, numerados como en el README
        for i, (cx, cy) in enumerate(self.to_screen(ave.control_points, off)):
            pygame.draw.rect(surface, _COL_CONTROL, (cx - 2, cy - 2, 5, 5))
            if self._font is not None:
                etiqueta = self._font.render(f"P{i}", True, _COL_CONTROL)
                surface.blit(etiqueta, (cx + 4, cy - 4))

        # posición actual sobre la curva + valor del parámetro
        px, py = self.to_screen([(ave.position.x, ave.position.y)], off)[0]
        pygame.draw.circle(surface, _COL_ACTUAL, (px + 8, py + 6), 4, 1)
        if self._font is not None:
            texto = self._font.render(f"t={ave.t:.2f}", True, _COL_TEXTO)
            surface.blit(texto, (px + 12, py - 8))

    # ── Unidad II — radio de detección y vectores ───────────────────

    def _draw_frog(self, surface: pygame.Surface,
                   off: pygame.Vector2, rana: JungleFrog) -> None:
        cx, cy = rana.rect.center
        centro = (int(cx - off.x), int(cy - off.y))

        # ── Círculo de detección radial ────────
        # Se dibuja un círculo y NO una caja (AABB) para evidenciar visualmente
        # la diferencia con la detección heredada del motor (EnemyBase).
        # Esto demuestra que la rana detecta al jugador usando la distancia 
        # euclidiana verdadera (Unidad II), dejando fuera las esquinas que una 
        # caja sí detectaría.
        pygame.draw.circle(surface, _COL_RADIO, centro,
                           int(rana.detection_radius), 1)

        if self._font is not None:
            d = rana.distance_to_player()
            etiqueta = "d=inf" if d == float("inf") else f"d={d:.0f}"
            texto = self._font.render(
                f"R={rana.detection_radius:.0f} {etiqueta}", True, _COL_TEXTO,
            )
            surface.blit(texto, (centro[0] - 20, centro[1] - int(rana.detection_radius) - 10))

        # ── Vector velocidad del proyectil ────────
        # Se dibuja una línea desde la posición del proyectil en la dirección 
        # de su vector de velocidad `p.velocity`. 
        # El vector de velocidad representa píxeles por SEGUNDO (ej: magnitud 90), 
        # lo que en pantalla se vería como una línea gigantesca de 90 píxeles de largo. 
        # Por eso se multiplica por un factor de escala (x0.25) puramente estético, 
        # para que la flecha quepa en pantalla de forma legible.
        for p in rana.projectiles:
            ini = (int(p.position.x - off.x) + 3, int(p.position.y - off.y) + 3)
            fin = (int(ini[0] + p.velocity.x * 0.25),
                   int(ini[1] + p.velocity.y * 0.25))
            pygame.draw.line(surface, _COL_VECTOR, ini, fin, 1)
            pygame.draw.circle(surface, _COL_VECTOR, fin, 2)
