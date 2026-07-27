"""El código y `docs/18_ENEMY_ROSTER.md` deben describir el mismo bestiario.

Por qué (AUD-046)
-----------------
Una auditoría automática de los 68 documentos encontró que el roster de
enemigos era la divergencia mayor del proyecto: el doc especifica **21 especies
con nombre y estadísticas concretas**, y el registro de entidades sólo conocía
**8 arquetipos genéricos**. Un alumno que siguiera
`docs/30_ASSIGNMENT_01_STAGE_DESIGN.md` y colocara `WalkerInsect` en Tiled
obtenía un nivel sin ese enemigo, sin ningún error visible.

Este módulo **parsea el markdown** y lo compara contra
`bestiary_registry.SPECIES`. La consecuencia es que la tabla del documento deja
de ser una aspiración y pasa a ser una especificación ejecutable: si alguien
edita el doc o cambia un valor en el código sin tocar el otro, el test falla y
nombra el campo divergente.

Es el patrón que faltaba en todo el proyecto — la auditoría encontró ocho
afirmaciones falsas en docstrings precisamente porque nada comprobaba que la
prosa siguiera siendo cierta.
"""
from __future__ import annotations

import os
import pathlib
import re

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROSTER_DOC = ROOT / "docs" / "18_ENEMY_ROSTER.md"


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))
    yield


@pytest.fixture(scope="module")
def documented() -> dict[str, dict[str, str]]:
    """Las especies tal y como las declara el documento."""
    text = ROSTER_DOC.read_text(encoding="utf-8")
    blocks = re.split(r"^### [0-9.]+ `(\w+)`", text, flags=re.M)
    species: dict[str, dict[str, str]] = {}
    for i in range(1, len(blocks) - 1, 2):
        name, body = blocks[i], blocks[i + 1]
        # Sólo la tabla inmediatamente posterior al encabezado.
        table = body.split("\n---")[0]
        rows = dict(re.findall(r"\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|", table))
        species[name] = {
            k.strip(): v.strip().strip("`")
            for k, v in rows.items()
            if k.strip() not in ("Property", "---")
        }
    return species


def _number(value: str) -> float | None:
    """Primer número de una celda como '1.0 heart' o '35 px/s'."""
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(match.group()) if match else None


# ── el documento y el código listan las mismas especies ──────────


def test_document_declares_species(documented) -> None:
    assert len(documented) >= 21, (
        f"se esperaban al menos 21 especies documentadas, se encontraron "
        f"{len(documented)}"
    )


def test_every_documented_species_exists_in_code(documented) -> None:
    """Ningún alumno debe poder colocar en Tiled un enemigo que no existe."""
    from src.framework.entities import bestiary_registry

    missing = sorted(set(documented) - set(bestiary_registry.SPECIES))
    assert not missing, (
        f"estas especies están documentadas pero no existen en el código: "
        f"{missing}. Un TMX que las use cargará un nivel sin esos enemigos."
    )


def test_no_undocumented_species_in_code(documented) -> None:
    """La deriva funciona en ambos sentidos."""
    from src.framework.entities import bestiary_registry

    extra = sorted(set(bestiary_registry.SPECIES) - set(documented))
    assert not extra, (
        f"estas especies existen en el código pero no en el roster: {extra}. "
        f"Añádelas a docs/18_ENEMY_ROSTER.md."
    )


# ── las estadísticas coinciden ───────────────────────────────────


DOC_TO_PARAM = {
    "Health": "max_health",
    "Contact Damage": "damage_on_contact",
    "Patrol Speed": "patrol_speed",
    "Alert Speed": "alert_speed",
    "Flight Speed": "flight_speed",
    "Sine Amplitude": "sine_amplitude",
    "Sine Frequency": "sine_frequency",
    "Fire Rate": "fire_rate",
    "Projectile Speed": "projectile_speed",
    "Projectile Damage": "projectile_damage",
}


def test_documented_stats_match_the_code(documented) -> None:
    """Cada cifra del doc debe ser la que el juego usa realmente."""
    from src.framework.entities import bestiary_registry

    mismatches: list[str] = []
    for species_id, doc_props in documented.items():
        spec = bestiary_registry.SPECIES.get(species_id)
        if spec is None:
            continue  # cubierto por otro test
        for doc_key, param in DOC_TO_PARAM.items():
            if doc_key not in doc_props or param not in spec.params:
                continue
            expected = _number(doc_props[doc_key])
            if expected is None:
                continue
            actual = float(spec.params[param])
            if abs(expected - actual) > 1e-6:
                mismatches.append(
                    f"{species_id}.{param}: doc dice {expected}, código usa {actual}"
                )

    assert not mismatches, (
        "el roster documentado y el código discrepan:\n  " + "\n  ".join(mismatches)
    )


def test_documented_base_class_matches(documented) -> None:
    from src.framework.entities import bestiary_registry

    wrong: list[str] = []
    for species_id, doc_props in documented.items():
        spec = bestiary_registry.SPECIES.get(species_id)
        declared = doc_props.get("Base Class", "").strip()
        if spec is None or not declared:
            continue
        if declared != spec.base:
            wrong.append(f"{species_id}: doc dice {declared}, código usa {spec.base}")
    assert not wrong, "clase base incorrecta:\n  " + "\n  ".join(wrong)


# ── las especies funcionan de verdad ─────────────────────────────


def _all_species():
    from src.framework.entities import bestiary_registry

    return sorted(bestiary_registry.SPECIES)


@pytest.mark.parametrize("species_id", _all_species())
def test_species_builds_and_updates(species_id: str, display) -> None:
    """Construir no basta: la especie debe sobrevivir fotogramas reales.

    Es la misma lección que AUD-039: un objeto que se instancia y luego revienta
    en el primer `update()` es tan inútil como uno que no se instancia, y sólo
    la segunda mitad se nota al jugar.
    """
    from src.framework.entities import bestiary_registry

    spec = bestiary_registry.SPECIES[species_id]
    enemy = spec.build(pygame.Vector2(100.0, 100.0))
    for _ in range(10):
        enemy.update(1 / 60)


@pytest.mark.parametrize("species_id", _all_species())
def test_species_is_registered_for_tmx(species_id: str, display) -> None:
    """El id debe ser resoluble desde un TMX, que es como se usan."""
    from src.framework.entities import entity_factory
    from src.framework.stage.stage_loader import StageLoader

    entity_factory.ensure_registered()
    assert species_id in StageLoader._entity_registry, (
        f"'{species_id}' no está registrado; colocarlo en Tiled no haría nada"
    )


def test_species_span_all_three_zones() -> None:
    from src.framework.entities import bestiary_registry

    for zone in (1, 2, 3):
        assert bestiary_registry.by_zone(zone), f"la zona {zone} no tiene especies"


def test_difficulty_escalates_across_zones() -> None:
    """La vida media debe subir por zona.

    `docs/18_ENEMY_ROSTER.md` §8 afirma que "la dificultad escala
    deliberadamente entre zonas". Esto lo comprueba en lugar de confiar en ello.
    """
    from src.framework.entities import bestiary_registry

    averages = []
    for zone in (1, 2, 3):
        healths = [
            float(s.params.get("max_health", 0))
            for s in bestiary_registry.by_zone(zone)
        ]
        averages.append(sum(healths) / len(healths))

    assert averages[0] < averages[1] < averages[2], (
        f"la vida media por zona no escala: {[round(a, 2) for a in averages]}"
    )


def test_chase_flight_mode_exists() -> None:
    """Varias especies declaran vuelo 'chase'; la estrategia debe existir.

    `make_strategy` cae en SineFlight ante un modo desconocido, así que una
    especie perseguidora se habría comportado como una sinusoide sin avisar.
    """
    from src.framework.entities.flight_strategies import ChaseFlight, make_strategy

    assert isinstance(make_strategy("chase"), ChaseFlight)


def test_chase_flight_accelerates_toward_the_target(display) -> None:
    """El perseguidor debe acercarse — y sobrepasar, que es lo que lo hace justo."""
    from src.framework.entities.enemy_flying import EnemyFlying

    enemy = EnemyFlying(pygame.Vector2(0.0, 0.0), flight_mode="chase",
                        flight_speed=80.0)
    enemy._player_ref = pygame.Rect(300, 0, 20, 32)

    start = enemy.position.x
    from src.framework.entities.flight_strategies import ChaseFlight

    strategy = ChaseFlight()
    for _ in range(60):
        strategy.execute(enemy, 1 / 60)

    assert enemy.position.x > start, "el perseguidor no se acercó al objetivo"


def test_chase_flight_without_target_does_not_crash(display) -> None:
    """Sin jugador asignado debe degradar, no lanzar."""
    from src.framework.entities.enemy_flying import EnemyFlying
    from src.framework.entities.flight_strategies import ChaseFlight

    enemy = EnemyFlying(pygame.Vector2(0.0, 0.0), flight_mode="chase")
    enemy._player_ref = None
    ChaseFlight().execute(enemy, 1 / 60)
