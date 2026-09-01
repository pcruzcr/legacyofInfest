"""
Crafting 100% — recetas simples para montura y artesanía.
Vista-agnóstico: usa Inventory, funciona en lateral/cenital/isométrica.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Receta:
    resultado: str
    ingredientes: dict[str, int]
    requiere_mesa: bool = False

RECETAS: tuple[Receta, ...] = (
    Receta("buddy_token", {"coin": 10, "relic_fragment": 1}),
    Receta("mount_flute", {"buddy_token": 1, "coin": 20}),
    Receta("heart_vessel", {"heart_piece": 4}),
    Receta("tonic_sap", {"coin": 5, "relic_fragment": 1}),
)

_POR_RESULTADO = {r.resultado: r for r in RECETAS}

def puede_craftear(inventario, resultado: str) -> bool:
    r = _POR_RESULTADO.get(resultado)
    if not r:
        return False
    return all(inventario.count(k) >= v for k, v in r.ingredientes.items())

def craftear(inventario, resultado: str) -> bool:
    if not puede_craftear(inventario, resultado):
        return False
    r = _POR_RESULTADO[resultado]
    for k, v in r.ingredientes.items():
        # gastar
        for _ in range(v):
            inventario._items[k] -= 1
            if inventario._items[k] <= 0:
                del inventario._items[k]
    inventario.collect(resultado, 1)
    return True
