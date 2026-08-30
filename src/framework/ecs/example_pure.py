"""
Ejemplo ECS puro — sin BaseEntity, solo World + componentes.

Demuestra que el motor genérico no necesita herencia para "cualquier juego".
"""

from __future__ import annotations

import pygame

from src.framework.ecs.components import Transform, Velocidad
from src.framework.ecs.world import World


def ejemplo() -> World:
    mundo = World()
    # Entidad solo con Transform y Velocidad — sin clase
    mundo.crear(
        Transform(posicion=pygame.Vector2(10, 20)),
        Velocidad(pygame.Vector2(50, 0)),
    )
    # Sistema puro
    for _eid in mundo.con(Transform, Velocidad):
        tr = mundo.obtener(_eid, Transform)
        vel = mundo.obtener(_eid, Velocidad)
        if tr and vel:
            tr.posicion.x += vel.v.x * 0.016
    return mundo


if __name__ == "__main__":
    w = ejemplo()
    print("ECS puro:", w.censo())
