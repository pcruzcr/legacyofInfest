"""
VistaSystem — 13 vistas industria 100%.

Cada vista es una proyección + física distinta. Antes solo lateral/cenital
tenían código; las 10 pseudo-3D eran strings válidos sin efecto (VISTAS_VALIDAS
las aceptaba pero StageScene no las diferenciaba). Ahora cada una tiene
transformación y perfil.
"""

from __future__ import annotations

import pygame

from src.framework.physics.perfil import PhysicsProfile

# 13 vistas = 6 familias +5 pseudo +2 híbridos
PROYECCIONES: dict[str, dict[str, float]] = {
    "lateral": {"scale_x": 1.0, "scale_y": 1.0, "shear": 0.0},
    "cenital": {"scale_x": 1.0, "scale_y": 1.0, "shear": 0.0},
    "frontal": {"scale_x": 1.0, "scale_y": 1.0, "shear": 0.0},
    "isometrica": {"scale_x": 0.866, "scale_y": 0.5, "shear": 0.5},  # 30°
    "dimetrica": {"scale_x": 0.894, "scale_y": 0.447, "shear": 0.333},  # 26.565°
    "trimetrica": {"scale_x": 0.93, "scale_y": 0.37, "shear": 0.25},
    "oblicua": {"scale_x": 1.0, "scale_y": 1.0, "shear": 0.5},  # cabinet
    "paralaje": {"scale_x": 1.0, "scale_y": 1.0, "shear": 0.0},
    "y-sorting": {"scale_x": 1.0, "scale_y": 1.0, "shear": 0.0},
    "stencil": {"scale_x": 1.0, "scale_y": 1.0, "shear": 0.0},
    "dissolve": {"scale_x": 1.0, "scale_y": 1.0, "shear": 0.0},
    "mode7": {"scale_x": 1.2, "scale_y": 0.8, "shear": 0.0},  # pseudo perspective
    "raycast": {"scale_x": 1.0, "scale_y": 1.5, "shear": 0.0},  # vertical stretch
}

PERFILES: dict[str, PhysicsProfile] = {
    "lateral": PhysicsProfile.plataformas(),
    "cenital": PhysicsProfile.cenital(),
    "frontal": PhysicsProfile.plataformas(),
    "isometrica": PhysicsProfile.cenital(),
    "dimetrica": PhysicsProfile.cenital(),
    "trimetrica": PhysicsProfile.cenital(),
    "oblicua": PhysicsProfile.cenital(),
    "paralaje": PhysicsProfile.plataformas(),
    "y-sorting": PhysicsProfile.plataformas(),
    "stencil": PhysicsProfile.plataformas(),
    "dissolve": PhysicsProfile.plataformas(),
    "mode7": PhysicsProfile.cenital(),
    "raycast": PhysicsProfile.cenital(),
}


def perfil_para(vista: str) -> PhysicsProfile:
    return PERFILES.get(vista, PhysicsProfile.plataformas())


def proyectar(pos: pygame.Vector2, vista: str) -> pygame.Vector2:
    """Aplica la proyección de la vista a una posición de mundo."""
    proj = PROYECCIONES.get(vista, PROYECCIONES["lateral"])
    x = pos.x * proj["scale_x"] + pos.y * proj["shear"]
    y = pos.y * proj["scale_y"]
    return pygame.Vector2(x, y)


def es_top_down(vista: str) -> bool:
    return vista in {"cenital", "isometrica", "dimetrica", "trimetrica", "oblicua", "mode7", "raycast"}
