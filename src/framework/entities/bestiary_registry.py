"""
Module: bestiary_registry
System: framework.entities
Academic Unit: N/A

Las 35 especies de enemigo que `docs/18_ENEMY_ROSTER.md` especifica.

Por qué existe este módulo (AUD-046)
------------------------------------
La auditoría automática de documentación encontró la divergencia más grande del
proyecto: `docs/18_ENEMY_ROSTER.md` describe **21 especies con nombre y
estadísticas concretas** (`WalkerInsect`, `FlyingBird`, `ShooterQuetzal`…), y el
código sólo tenía **8 arquetipos genéricos** sin ninguna de ellas. Los alumnos
leían una tabla de 21 enemigos y encontraban `Walker`, `Flying`, `Shooter` en el
factory.

La respuesta *no* es escribir 21 clases. Las especies difieren únicamente en
parámetros — vida, velocidad de patrulla, cadencia de disparo, amplitud de la
onda — que las clases base ya aceptan por constructor. Veintiuna subclases de
tres líneas serían herencia usada como base de datos.

Lo que sí es correcto: una tabla de datos. Cada especie es un `SpeciesSpec`
inmutable, el factory las registra todas, y `tests/test_bestiary_roster.py`
**parsea el markdown y compara** — de modo que si alguien edita la tabla del doc
o cambia un valor aquí, el test falla y nombra el campo divergente. La
documentación pasa a ser verificable por máquina en lugar de aspiracional.

Añadir una especie: añádela a `SPECIES`, añade su fila al doc. El test exige
ambas cosas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.framework.entities.enemy_base import EnemyBase


@dataclass(frozen=True)
class SpeciesSpec:
    """Una especie: nombre, clase base y los parámetros que la distinguen."""

    species_id: str
    base: str            # "EnemyWalker" | "EnemyFlying" | "EnemyShooter"
    zone: int
    display_name: str
    params: dict[str, Any] = field(default_factory=dict)

    def build(self, spawn_position: Any, **overrides: Any) -> EnemyBase:
        """Instancia la especie. Los overrides del TMX ganan sobre la tabla."""
        cls = _BASE_CLASSES[self.base]()
        kwargs = dict(self.params)
        kwargs.update(overrides)
        kwargs.setdefault("zone", self.zone)
        # AUD-XXX — el species_id debe estar disponible antes de que
        # EnemyBase._load_zone_sprites intente cargar
        # enemy_{sid}_{key}.png; antes se fijaba después de construir y
        # nunca se recargaban los sprites, dejando walk/hurt/die en
        # placeholder genérico o rojo cuando fw,fh no cuadraba.
        # Se pasa también como kwarg por si la subclase lo recoge en su
        # __init__; si lo ignora, se reasigna tras construir y se fuerza
        # recarga.
        kwargs.setdefault("species_id", self.species_id)
        try:
            ent = cls(spawn_position, **kwargs)
        except TypeError:
            # la subclase no acepta species_id → construir sin él y fijar después
            kwargs.pop("species_id", None)
            ent = cls(spawn_position, **kwargs)
        try:
            ent.species_id = self.species_id
            ent._species_id = self.species_id
        except Exception:
            pass
        # Recarga con species_id ya conocido para que el fallback por zona
        # use fw,fh correctos y no quede garbled (ej. Archer 12×14 sobre
        # hoja 16×12 → 0 filas).
        try:
            if hasattr(ent, "_sprite_fw") and hasattr(ent, "_sprite_fh") and hasattr(ent, "_sprite_zone"):
                ent._load_zone_sprites(ent._sprite_zone, ent._sprite_fw, ent._sprite_fh)
        except Exception:
            pass
        return ent


def _walker() -> type:
    from src.framework.entities.enemy_walker import EnemyWalker
    return EnemyWalker


def _flying() -> type:
    from src.framework.entities.enemy_flying import EnemyFlying
    return EnemyFlying


def _shooter() -> type:
    from src.framework.entities.enemy_shooter import EnemyShooter
    return EnemyShooter


def _shielded() -> type:
    from src.framework.entities.enemy_shielded import EnemyShielded
    return EnemyShielded


def _swimmer() -> type:
    from src.framework.entities.enemy_swimmer import EnemySwimmer
    return EnemySwimmer


def _cangrejo() -> type:
    from src.framework.entities.enemy_cangrejo import EnemyCangrejo
    return EnemyCangrejo


def _medusa() -> type:
    from src.framework.entities.enemy_medusa import EnemyMedusa
    return EnemyMedusa


def _pezabismal() -> type:
    from src.framework.entities.enemy_pez_abismal import EnemyPezAbismal
    return EnemyPezAbismal


def _climber() -> type:
    from src.framework.entities.enemy_climber import EnemyClimber
    return EnemyClimber


def _flying_bomber() -> type:
    from src.framework.entities.enemy_flying_bomber import EnemyFlyingBomber
    return EnemyFlyingBomber


def _terrain_shaper() -> type:
    from src.framework.entities.enemy_terrain_shaper import EnemyTerrainShaper
    return EnemyTerrainShaper


def _summoner() -> type:
    from src.framework.entities.enemy_summoner import EnemySummoner
    return EnemySummoner


def _archer() -> type:
    from src.framework.entities.enemy_archer import EnemyArcher
    return EnemyArcher


def _brute() -> type:
    from src.framework.entities.enemy_brute import EnemyBrute
    return EnemyBrute


def _charger() -> type:
    from src.framework.entities.enemy_charger import EnemyCharger
    return EnemyCharger


def _caster() -> type:
    from src.framework.entities.enemy_caster import EnemyCaster
    return EnemyCaster


def _assassin() -> type:
    from src.framework.entities.enemy_assassin import EnemyAssassin
    return EnemyAssassin


_BASE_CLASSES = {
    "EnemyWalker": _walker,
    "EnemyFlying": _flying,
    "EnemyShooter": _shooter,
    "EnemyShielded": _shielded,
    "EnemySwimmer": _swimmer,
    "EnemyCangrejo": _cangrejo,
    "EnemyMedusa": _medusa,
    "EnemyPezAbismal": _pezabismal,
    "EnemyClimber": _climber,
    "EnemyFlyingBomber": _flying_bomber,
    "EnemyTerrainShaper": _terrain_shaper,
    "EnemySummoner": _summoner,
    "EnemyArcher": _archer,
    "EnemyBrute": _brute,
    "EnemyCharger": _charger,
    "EnemyCaster": _caster,
    "EnemyAssassin": _assassin,
}


# ── Zona 1 — Universidad Invenio ──────────────────────────────────
# Introduce cada arquetipo por separado y con margen: el jugador aprende a
# leer un enemigo por vez antes de que se combinen.

_ZONE1 = [
    SpeciesSpec("WalkerInsect", "EnemyWalker", 1, "Insecto de suelo", {
        "max_health": 1.0, "damage_on_contact": 0.25, "patrol_speed": 35.0, "alert_speed": 55.0, "patrol_length": 64.0,
    }),
    SpeciesSpec("FlyingBird", "EnemyFlying", 1, "Ave de selva", {
        "max_health": 1.0, "damage_on_contact": 0.25, "flight_mode": 'sine',
        "flight_speed": 55.0, "sine_amplitude": 24.0, "sine_frequency": 1.4,
    }),
    SpeciesSpec("ShooterFrog", "EnemyShooter", 1, "Rana dardo", {
        "max_health": 2.0, "damage_on_contact": 0.25, "patrol_length": 0.0,
        "fire_rate": 0.4, "projectile_speed": 90.0, "projectile_damage": 0.25,
    }),
    SpeciesSpec("WalkerRaton", "EnemyWalker", 1, "Rata de laboratorio", {
        "max_health": 1.0, "damage_on_contact": 0.25, "patrol_speed": 55.0, "alert_speed": 90.0, "patrol_length": 48.0,
    }),
    SpeciesSpec("FlyingCucaracha", "EnemyFlying", 1, "Cucaracha voladora", {
        "max_health": 1.0, "damage_on_contact": 0.25, "flight_mode": 'sine',
        "flight_speed": 45.0, "sine_amplitude": 16.0, "sine_frequency": 2.0,
    }),
    SpeciesSpec("ShooterCocinero", "EnemyShooter", 1, "Cocinero de cafetería", {
        "max_health": 3.0, "damage_on_contact": 0.25, "fire_rate": 0.5,
        "projectile_speed": 110.0, "projectile_damage": 0.5,
    }),
    SpeciesSpec("WalkerEstudiante", "EnemyWalker", 1, "Estudiante infestado", {
        "max_health": 1.5, "damage_on_contact": 0.5, "patrol_speed": 40.0, "alert_speed": 70.0, "patrol_length": 80.0,
    }),
    SpeciesSpec("FlyingNotebook", "EnemyFlying", 1, "Cuaderno poseído", {
        "max_health": 0.5, "damage_on_contact": 0.25, "flight_mode": 'sine',
        "flight_speed": 50.0, "sine_amplitude": 32.0, "sine_frequency": 1.0,
    }),
    SpeciesSpec("ShooterTiza", "EnemyShooter", 1, "Tiza voladora", {
        "max_health": 2.5, "patrol_length": 0.0, "fire_rate": 1.0, "projectile_speed": 130.0, "projectile_damage": 0.25,
    }),
]

# ── Zona 2 — Selva de Terciopelo ──────────────────────────────────
# Sube la presión: más vida, más alcance, comportamientos que castigan
# quedarse quieto.

_ZONE2 = [
    SpeciesSpec("WalkerSerpientePequena", "EnemyWalker", 2, "Serpiente pequeña", {
        "max_health": 1.0, "damage_on_contact": 0.5, "patrol_speed": 55.0, "alert_speed": 100.0,
    }),
    SpeciesSpec("FlyingBoa", "EnemyFlying", 2, "Boa arborícola", {
        "max_health": 2.0, "damage_on_contact": 0.5, "flight_mode": 'sine',
        "flight_speed": 45.0, "sine_amplitude": 30.0, "sine_frequency": 0.8,
    }),
    SpeciesSpec("ShooterSerpienteArbol", "EnemyShooter", 2, "Serpiente de árbol", {
        "max_health": 2.0, "patrol_length": 0.0, "fire_rate": 0.6, "projectile_speed": 100.0, "projectile_damage": 0.5,
    }),
    SpeciesSpec("WalkerTerciopelo", "EnemyWalker", 2, "Terciopelo", {
        "max_health": 2.5, "damage_on_contact": 0.75, "patrol_speed": 40.0, "alert_speed": 80.0,
    }),
    SpeciesSpec("ShooterVenomoLargo", "EnemyShooter", 2, "Venomo largo", {
        "max_health": 3.0, "fire_rate": 0.4, "projectile_speed": 150.0, "projectile_damage": 0.5,
    }),
    SpeciesSpec("FlyingTerciovolador", "EnemyFlying", 2, "Terciovolador", {
        "max_health": 1.5, "damage_on_contact": 0.5, "flight_mode": 'sine', "flight_speed": 70.0,
    }),
    SpeciesSpec("WalkerGuardia", "EnemyWalker", 2, "Guardia infestado", {
        "max_health": 3.0, "damage_on_contact": 0.5, "patrol_speed": 45.0, "alert_speed": 65.0,
    }),
]

# ── Zona 3 — Heredia ──────────────────────────────────────────────
# Enemigos de cierre: exigen usar todo el kit del jugador a la vez.

_ZONE3 = [
    SpeciesSpec("WalkerGarza", "EnemyWalker", 3, "Garza", {
        "max_health": 2.0, "damage_on_contact": 0.5, "patrol_speed": 35.0, "alert_speed": 60.0,
    }),
    # El roster §5.3 especifica "Sine + alert dive": patrulla en sinusoide y
    # pica cuando detecta al jugador. `alert_flight_mode` selecciona la
    # estrategia usada en estado ALERT (AUD-047).
    SpeciesSpec("FlyingHalcon", "EnemyFlying", 3, "Halcón", {
        "max_health": 2.0, "damage_on_contact": 0.75, "flight_mode": 'sine',
        "flight_speed": 65.0, "sine_amplitude": 20.0, "sine_frequency": 0.6,
        "alert_flight_mode": "dive",
    }),
    SpeciesSpec("ShooterQuetzal", "EnemyShooter", 3, "Quetzal", {
        "max_health": 2.5, "patrol_length": 0.0, "fire_rate": 0.8, "projectile_speed": 120.0, "projectile_damage": 0.25,
    }),
    SpeciesSpec("WalkerPalom", "EnemyWalker", 3, "Paloma infestada", {
        "max_health": 2.5, "damage_on_contact": 0.5, "patrol_speed": 30.0, "alert_speed": 55.0,
    }),
    SpeciesSpec("ShooterBuitre", "EnemyShooter", 3, "Buitre", {
        "max_health": 3.5, "fire_rate": 0.35, "projectile_speed": 100.0, "projectile_damage": 0.5,
    }),
]

# ── Zona 4 — Cementerio / Mina inundada ─────────────────────────────
# Atemporal: la regla de oro del 4-1 sigue (nada daña en la mina), pero la
# presencia suma lectura ambiental. Estas 4 especies no son combate: enseñan
# volumen, corriente y deriva sin romper la regla del nivel.

_ZONE4 = [
    SpeciesSpec("Cangrejo", "EnemyCangrejo", 4, "Cangrejo de mina", {
        "max_health": 1.0, "damage_on_contact": 0.0, "patrol_length": 80.0, "patrol_speed": 22.0,
    }),
    SpeciesSpec("Medusa", "EnemyMedusa", 4, "Medusa de pozo", {
        "max_health": 1.0, "damage_on_contact": 0.0, "flight_mode": 'sine',
        "flight_speed": 26.0, "sine_amplitude": 14.0, "sine_frequency": 0.4,
    }),
    SpeciesSpec("PezAbismal", "EnemyPezAbismal", 4, "Pez abismal", {
        "max_health": 1.0, "damage_on_contact": 0.0, "flight_mode": 'sine',
        "flight_speed": 85.0, "sine_amplitude": 16.0, "sine_frequency": 0.5,
    }),
    SpeciesSpec("AssassinSombra", "EnemyAssassin", 4, "Sombra del cementerio", {
        "max_health": 2.0, "damage_on_contact": 0.5, "patrol_length": 64.0,
    }),
]

# ── Huérfanos cableados — 5 arquetipos vacíos + 4 mecánicos ──────────
# Antes 5 arquetipos (Archer/Brute/Caster/Charger/Assassin) estaban vacíos
# y 9 clases huérfanas (Shielded, Swimmer, Climber, FlyingBomber,
# TerrainShaper, Summoner + las 3 de mina) no tenían especie ni registro.
# Se cablean con zonas existentes (no nuevos biomas): Datacenter para
# Shielded/Brute/Charger, Heredia para Archer/Caster/Summoner/Shaper,
# Universidad para Climber, Cementerio para Assassin.

_EXTRA_ZONA1 = [
    SpeciesSpec("Climber", "EnemyClimber", 1, "Trepador de lianas", {
        "max_health": 2.0, "damage_on_contact": 0.5, "climb_speed": 70.0, "zipline_speed": 190.0,
    }),
]

_EXTRA_ZONA2 = [
    SpeciesSpec("Shielded", "EnemyShielded", 2, "Guardia con escudo", {
        "max_health": 3.0, "damage_on_contact": 0.5, "shield_health": 3.0, "patrol_length": 80.0, "patrol_speed": 35.0,
    }),
    SpeciesSpec("Swimmer", "EnemySwimmer", 2, "Nadador de esclusa", {
        "max_health": 2.0, "damage_on_contact": 0.5, "swim_speed": 70.0,
    }),
    SpeciesSpec("FlyingBomber", "EnemyFlyingBomber", 2, "Bombardero de datacenter", {
        "max_health": 2.0, "damage_on_contact": 0.5, "flight_mode": 'sine',
        "flight_speed": 50.0, "sine_amplitude": 30.0, "sine_frequency": 1.0,
    }),
    SpeciesSpec("BruteGolemHielo", "EnemyBrute", 2, "Gólem de hielo", {
        "max_health": 5.0, "damage_on_contact": 0.75, "patrol_length": 64.0,
    }),
    SpeciesSpec("ChargerWolf", "EnemyCharger", 2, "Lobo de planicie", {
        "max_health": 3.5, "damage_on_contact": 1.0, "charge_speed": 250.0,
    }),
]

_EXTRA_ZONA3 = [
    SpeciesSpec("ArcherQuetzal", "EnemyArcher", 3, "Arquero quetzal", {
        "max_health": 2.5, "damage_on_contact": 0.25, "fire_rate": 0.5, "projectile_speed": 110.0, "projectile_damage": 0.5,
    }),
    SpeciesSpec("CasterHealer", "EnemyCaster", 3, "Curandero de Heredia", {
        "max_health": 2.5, "damage_on_contact": 0.25,
    }),
    SpeciesSpec("TerrainShaper", "EnemyTerrainShaper", 3, "Modelador de terreno", {
        "max_health": 3.0, "damage_on_contact": 0.5, "patrol_length": 80.0,
    }),
    SpeciesSpec("Summoner", "EnemySummoner", 3, "Invocador de Heredia", {
        "max_health": 4.0, "damage_on_contact": 0.5, "patrol_length": 60.0,
    }),
]

SPECIES: dict[str, SpeciesSpec] = {
    spec.species_id: spec for spec in (*_ZONE1, *_ZONE2, *_ZONE3, *_ZONE4, *_EXTRA_ZONA1, *_EXTRA_ZONA2, *_EXTRA_ZONA3)
}


def get(species_id: str) -> SpeciesSpec | None:
    """La especie con ese id, o None."""
    return SPECIES.get(species_id)


def by_zone(zone: int) -> list[SpeciesSpec]:
    """Todas las especies de una zona, en orden de introducción."""
    return [s for s in SPECIES.values() if s.zone == zone]


def species_ids() -> list[str]:
    return list(SPECIES)
