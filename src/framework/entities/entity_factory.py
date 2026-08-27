"""
Module: entity_factory
System: framework.entities
Academic Unit: N/A
Description: Centralized entity factory using the registry pattern.
All known enemy types are auto-registered on import, eliminating the need
for stage files to call StageLoader.register_entity() manually.

FACTORY PATTERN (Fase 4): Entity creation is centralized here rather than
scattered across stage files. StageLoader.load() looks up entity types in
StageLoader._entity_registry, which is populated by ensure_registered().
Adding a new enemy type requires only importing it in the registry dict below.
"""
from __future__ import annotations

from typing import Any

from src.framework.entities.enemy_archer import EnemyArcher
from src.framework.entities.enemy_assassin import EnemyAssassin
from src.framework.entities.enemy_base import EnemyBase
from src.framework.entities.enemy_brute import EnemyBrute
from src.framework.entities.enemy_buddies import BuddyEnguarde, BuddyExpresso, BuddyRino
from src.framework.entities.enemy_cangrejo import EnemyCangrejo
from src.framework.entities.enemy_caster import EnemyCaster
from src.framework.entities.enemy_charger import EnemyCharger
from src.framework.entities.enemy_climber import EnemyClimber
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_flying_bomber import EnemyFlyingBomber
from src.framework.entities.enemy_medusa import EnemyMedusa
from src.framework.entities.enemy_pez_abismal import EnemyPezAbismal
from src.framework.entities.enemy_shielded import EnemyShielded
from src.framework.entities.enemy_shooter import EnemyShooter
from src.framework.entities.enemy_summoner import EnemySummoner
from src.framework.entities.enemy_swimmer import EnemySwimmer
from src.framework.entities.enemy_terrain_shaper import EnemyTerrainShaper
from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.stage.stage_loader import StageLoader

_registered: bool = False

#: Nombres que esta función dio de alta la última vez. Se usa para detectar que
#: alguien vació o recortó el registro después, y volver a poblarlo.
_REGISTERED_NAMES: set[str] = set()


def ensure_registered() -> None:
    """
    Register all known entity types with StageLoader.
    Idempotent - safe to call multiple times.
    Call once before loading any stage (e.g., in App.__init__).
    Boss entities are imported lazily to avoid paying numpy/sklearn
    import cost at game startup (~3.4s).
    """
    global _registered
    # AUD-056: la condición era sólo `if _registered: return`, así que el
    # indicador podía afirmar que el registro estaba hecho cuando alguien lo
    # había vaciado después —`StageLoader._entity_registry.clear()`, algo que
    # varias pruebas hacen—. A partir de ahí toda carga de mapa perdía
    # entidades en silencio mientras esta función aseguraba que todo estaba
    # bien.
    #
    # Se comprueba que estén *todos* los tipos, no que el registro tenga algo:
    # «no vacío» no es «completo», y una comprobación que se conforma con lo
    # primero deja pasar exactamente el caso que se quería detectar — un
    # registro parcial con tres tipos dados de alta a mano.
    if _registered and _REGISTERED_NAMES <= StageLoader._entity_registry.keys():
        return

    from src.stages.boss_venado.boss_venado import BossVenado

    _ENTITY_REGISTRY: dict[str, type[EnemyBase]] = {
        "Walker": EnemyWalker,
        "Flying": EnemyFlying,
        "Shooter": EnemyShooter,
        "Charger": EnemyCharger,
        "Archer": EnemyArcher,
        "Brute": EnemyBrute,
        "Caster": EnemyCaster,
        "Assassin": EnemyAssassin,
        "Shielded": EnemyShielded,
        "Swimmer": EnemySwimmer,
        "Cangrejo": EnemyCangrejo,
        "Medusa": EnemyMedusa,
        "PezAbismal": EnemyPezAbismal,
        "Climber": EnemyClimber,
        "FlyingBomber": EnemyFlyingBomber,
        "TerrainShaper": EnemyTerrainShaper,
        "Summoner": EnemySummoner,
        "BossVenado": BossVenado,
        "BuddyRino": BuddyRino,
        "BuddyExpresso": BuddyExpresso,
        "BuddyEnguarde": BuddyEnguarde,
    }

    for type_name, entity_class in _ENTITY_REGISTRY.items():
        StageLoader.register_entity(type_name, entity_class)

    species_names = _register_named_species()
    _REGISTERED_NAMES.clear()
    _REGISTERED_NAMES.update(_ENTITY_REGISTRY)
    _REGISTERED_NAMES.update(species_names)
    _registered = True


def _register_named_species() -> set[str]:
    """Registra las 21 especies con nombre de `docs/18_ENEMY_ROSTER.md`.

    AUD-046: el doc especifica 21 especies (`WalkerInsect`, `ShooterQuetzal`…)
    con estadísticas concretas; el registro sólo conocía los 8 arquetipos
    genéricos. Un TMX que colocaba `WalkerInsect` — exactamente lo que el doc
    de diseño de niveles indica a los alumnos — no encontraba la clase y el
    enemigo no aparecía.

    Cada especie se registra como una factoría que aplica sus parámetros y deja
    que las propiedades del TMX los sobreescriban, de modo que un alumno puede
    partir de la especie documentada y ajustarla en Tiled sin tocar código.
    """
    from src.framework.entities import bestiary_registry

    for species_id, spec in bestiary_registry.SPECIES.items():
        StageLoader.register_entity(species_id, _species_factory(spec))
    return set(bestiary_registry.SPECIES)


def _species_factory(spec: Any) -> Any:
    """Envuelve un SpeciesSpec en un invocable con la firma que espera el loader."""
    def _build(spawn_position: Any, **kwargs: Any) -> EnemyBase:
        enemigo = spec.build(spawn_position, **kwargs)
        # AUD-154 — la especie se queda pegada a la entidad.
        #
        # Las veintiuna especies comparten tres clases base, así que sin esto
        # un `WalkerInsect` y un `WalkerRaton` son los dos `EnemyWalker` y el
        # bestiario los contaría como el mismo bicho. El sitio correcto es
        # aquí: es lo único que sabe con qué especie se construyó.
        enemigo.enemy_id = spec.species_id
        return enemigo

    # El loader y el bestiario muestran este nombre; sin él saldría "_build".
    _build.__name__ = spec.species_id
    return _build
