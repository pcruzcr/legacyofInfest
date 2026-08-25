"""
`framework.ecs` — entidades, componentes y sistemas.

Se añade **debajo** de la jerarquía existente, no en su lugar: las 26 clases de
estudiantes que heredan de `BaseEntity`, `EnemyBase`, `BossBase` y `StageScene`
siguen funcionando sin cambios. Ver `world.py` para el porqué.
"""
from src.framework.ecs.components import (
    Acosador,
    Alerta,
    BombDropComponent,
    BloqueRitmico,
    ChargeComponent,
    ConoDeVision,
    GroundPoundComponent,
    PatrolComponent,
    PredictiveAimComponent,
    PlataformaHundible,
    PlataformaMovil,
    Resorte,
    Salud,
    ShieldComponent,
    Solido,
    SummonComponent,
    TerrainActionComponent,
    Transform,
    Velocidad,
    ZonaDeAgua,
    ZonaDeFriccion,
    ZonaDeViento,
    ZonaLetalTemporizada,
)
from src.framework.ecs.scheduler import Fase, Planificador, Sistema
from src.framework.ecs.world import EntityId, World

__all__ = [
    "Acosador",
    "Alerta",
    "BombDropComponent",
    "BloqueRitmico",
    "ChargeComponent",
    "ConoDeVision",
    "EntityId",
    "Fase",
    "GroundPoundComponent",
    "PatrolComponent",
    "Planificador",
    "PredictiveAimComponent",
    "PlataformaHundible",
    "PlataformaMovil",
    "Resorte",
    "Salud",
    "ShieldComponent",
    "Solido",
    "SummonComponent",
    "TerrainActionComponent",
    "Transform",
    "Velocidad",
    "World",
    "ZonaDeAgua",
    "ZonaDeFriccion",
    "ZonaDeViento",
    "ZonaLetalTemporizada",
]
