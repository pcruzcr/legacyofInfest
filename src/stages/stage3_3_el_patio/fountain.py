"""
Module: fountain
System: stage (student assignment - stage3_3_el_patio)
Academic Unit: II (Vectores), III (Curvas), V (Color), VII (Filtros)

La fuente central de El Patio (docs/16_WORLD_DESIGN.md, Stage 3-3 "Fountain
Special"). Cura al jugador si se acerca (matematica vectorial explicita),
dispara un chorro de agua que sigue una curva Catmull-Rom (CurveTools), tiene
un tinte dorado aplicado con ColorTools, y usa FilterTools dos veces: un
histograma decide si hay que aclarar el sprite antes de teñirlo, y un
desenfoque gaussiano genera el aura de luz que se ve detras de la fuente.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.math_utils import vec2_normalize, vec2_distance, vec2_dot
from src.framework.processing.curve_tools import CurveTools
from src.framework.processing.color_tools import ColorTools
from src.framework.processing.filter_tools import FilterTools


class Fountain:
    """Fuente decorativa e interactiva del patio (no es un enemigo)."""

    HEAL_RADIUS = 28.0
    HEAL_AMOUNT = 0.25
    HEAL_COOLDOWN = 6.0
    TINT_COLOR = (255, 214, 140)  # luz dorada de tarde (docs/16_WORLD_DESIGN.md Zona 3)

    def __init__(self, center: pygame.Vector2) -> None:
        self.center = pygame.Vector2(center)

        # ── Unidad III: curva del chorro de agua ──────────────────────
        # Catmull-Rom pasando exactamente por estos 5 puntos: sale de la
        # boquilla, sube en arco, y vuelve a caer sobre el mismo punto.
        cx, cy = self.center.x, self.center.y
        control_points = [
            (cx, cy),
            (cx - 18, cy - 60),
            (cx, cy - 84),
            (cx + 18, cy - 60),
            (cx, cy),
        ]
        self._path: list[tuple[float, float]] = CurveTools.catmull_rom(control_points, n_samples=48)

        self._n_drops = 6
        self._t = 0.0
        self._cycle_duration = 1.4  # segundos para recorrer la curva completa

        self._heal_cooldown = 0.0
        self._heal_flash_timer = 0.0
        self._heal_flash_side = 1.0

        # ── Unidad VII: histograma decide si hace falta aclarar el sprite ──
        # Se mide el brillo real del primer frame (antes de tenir) con
        # compute_histogram(). Si la media de luminancia queda por debajo del
        # umbral, se lo aclara con adjust_brightness() antes de tenirlo: el
        # tinte dorado sobre un sprite oscuro se veia apagado, y esto lo
        # decide el histograma, no un numero fijo puesto a ojo.
        sprite_path = settings.ASSETS_DIR / "sprites" / "shared" / "fountain_anim.png"
        frames_raw = AssetLoader.load_sprite_sheet(sprite_path, 24, 24)

        hist = FilterTools.compute_histogram(frames_raw[0])
        luminancia = hist["luminance"]
        total = int(hist["total_pixels"])
        # media = suma(i * cantidad_de_pixeles_con_luminancia_i) / total
        brillo_medio = float(sum(i * int(c) for i, c in enumerate(luminancia))) / total if total else 255.0
        if brillo_medio < 140.0:
            frames_raw = [FilterTools.adjust_brightness(f, 1.35) for f in frames_raw]

        # ── Unidad V: color ─────────────────────────────────────────
        self._frames = [ColorTools.apply_tint(f, self.TINT_COLOR) for f in frames_raw]
        self._frame_index = 0
        self._frame_timer = 0.0
        self._frame_duration = 0.12

        # ── Unidad VII: desenfoque gaussiano para el aura de luz ──────
        # Un circulo blanco solido sobre fondo negro, desenfocado con
        # gaussian_blur(): el resultado es un degradado suave del centro
        # hacia afuera, en RGB (el filtro no toca canal alfa). Ese brillo
        # (0 a 255) se reutiliza como canal alfa: donde quedo negro por el
        # desenfoque, queda transparente; donde quedo blanco, opaco. Asi el
        # halo se funde con el fondo en vez de verse como un cuadro recortado.
        import numpy as np
        base = pygame.Surface((48, 48))
        base.fill((0, 0, 0))
        pygame.draw.circle(base, (255, 255, 255), (24, 24), 14)
        borrosa = FilterTools.gaussian_blur(base, sigma=6.0)
        brillo = pygame.surfarray.array3d(borrosa)[:, :, 0]  # ya es gris puro
        aura = pygame.Surface((48, 48), pygame.SRCALPHA)
        color_rgb = np.array(self.TINT_COLOR, dtype=np.uint8)
        rgb_plano = np.tile(color_rgb, (48, 48, 1))
        pygame.surfarray.pixels3d(aura)[:, :, :] = rgb_plano
        pygame.surfarray.pixels_alpha(aura)[:, :] = brillo
        self._aura = aura

    def update(self, dt: float, player) -> None:
        self._t = (self._t + dt / self._cycle_duration) % 1.0
        self._heal_cooldown = max(0.0, self._heal_cooldown - dt)
        self._heal_flash_timer = max(0.0, self._heal_flash_timer - dt)

        self._frame_timer += dt
        if self._frame_timer >= self._frame_duration:
            self._frame_timer -= self._frame_duration
            self._frame_index = (self._frame_index + 1) % len(self._frames)

        if player is None:
            return

        # ── Unidad II: matematica vectorial explicita ─────────────────
        player_center = pygame.Vector2(player.rect.centerx, player.rect.centery)

        # vec2_distance: distancia euclidiana fuente -> jugador.
        # d = sqrt((px-cx)^2 + (py-cy)^2)
        distance = vec2_distance(self.center, player_center)

        if distance <= self.HEAL_RADIUS and self._heal_cooldown <= 0.0:
            to_player = player_center - self.center

            # vec2_normalize: vector unitario de direccion fuente -> jugador.
            # u = v / |v|
            direction = vec2_normalize(to_player)

            # vec2_dot: proyeccion de la direccion sobre el eje horizontal
            # (1, 0). dot > 0 => jugador a la derecha, dot < 0 => a la
            # izquierda. Se usa para saber de que lado dibujar el destello
            # de curacion.
            side = vec2_dot(direction, pygame.Vector2(1.0, 0.0))
            self._heal_flash_side = 1.0 if side >= 0 else -1.0
            self._heal_flash_timer = 0.6

            player.heal(self.HEAL_AMOUNT)
            self._heal_cooldown = self.HEAL_COOLDOWN

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        # Aura borrosa (gaussian_blur, Unidad VII), detras del sprite.
        ax = int(self.center.x - camera_offset.x - self._aura.get_width() / 2)
        ay = int(self.center.y - camera_offset.y - self._aura.get_height() / 2 - 8)
        surface.blit(self._aura, (ax, ay))

        frame = self._frames[self._frame_index]
        sx = int(self.center.x - camera_offset.x - frame.get_width() / 2)
        sy = int(self.center.y - camera_offset.y - frame.get_height())
        surface.blit(frame, (sx, sy))

        # Gotas de agua recorriendo la curva Catmull-Rom, con fases
        # distintas para que no vayan todas pegadas.
        for i in range(self._n_drops):
            phase = i / self._n_drops
            t = (self._t + phase) % 1.0
            idx = int(t * (len(self._path) - 1))
            px, py = self._path[idx]
            dx = int(px - camera_offset.x)
            dy = int(py - camera_offset.y)
            pygame.draw.circle(surface, (140, 200, 255), (dx, dy), 2)

        if self._heal_flash_timer > 0.0:
            fx = int(self.center.x - camera_offset.x + self._heal_flash_side * 14)
            fy = int(self.center.y - camera_offset.y - 30)
            alpha = int(255 * (self._heal_flash_timer / 0.6))
            glow = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(glow, (180, 255, 200, alpha), (5, 5), 5)
            surface.blit(glow, (fx - 5, fy - 5))
