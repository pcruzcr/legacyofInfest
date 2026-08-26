"""
Module: bestiary_registry
System: framework.entities
Academic Unit: N/A

Las 21 especies de enemigo que `docs/18_ENEMY_ROSTER.md` especifica.

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
        ent = cls(spawn_position, **kwargs)
        try:
            ent.species_id = self.species_id
            ent._species_id = self.species_id
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


_BASE_CLASSES = {
    "EnemyWalker": _walker,
    "EnemyFlying": _flying,
    "EnemyShooter": _shooter,
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

SPECIES: dict[str, SpeciesSpec] = {
    spec.species_id: spec for spec in (*_ZONE1, *_ZONE2, *_ZONE3)
}


def get(species_id: str) -> SpeciesSpec | None:
    """La especie con ese id, o None."""
    return SPECIES.get(species_id)


def by_zone(zone: int) -> list[SpeciesSpec]:
    """Todas las especies de una zona, en orden de introducción."""
    return [s for s in SPECIES.values() if s.zone == zone]


def species_ids() -> list[str]:
    return list(SPECIES)
