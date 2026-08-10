"""
Module: world
System: framework.world
Description: AUD-358 — el mundo como una simulación, no como tres sistemas sueltos.

El paquete que va a llevar `WorldSimulation` (lote 5 de `docs/91_PLAN_DE_CIERRE.md`).
Hoy contiene sólo el **contrato**, que es la mitad que importa: `EnvironmentState`,
la foto inmutable del ambiente en un fotograma, que la simulación producirá y
que el render, el audio y la jugabilidad consumirán sin conocerse entre sí.

El contrato se entrega antes que el productor a propósito. Es la pieza sobre
la que se acuerda; el reloj, el calendario y la astronomía que la rellenan son
detalles reemplazables una vez que está fijada.
"""
from src.framework.world.environment import (
    DIAS_DEL_MES_LUNAR,
    FASES_DEL_DIA,
    PERDIDA_MAXIMA_DE_FRICCION,
    UMBRAL_SUELO_MOJADO,
    EnvironmentState,
)
from src.framework.world.simulation import CLIMAS, WorldSimulation

__all__ = [
    "CLIMAS",
    "DIAS_DEL_MES_LUNAR",
    "FASES_DEL_DIA",
    "PERDIDA_MAXIMA_DE_FRICCION",
    "UMBRAL_SUELO_MOJADO",
    "EnvironmentState",
    "WorldSimulation",
]
