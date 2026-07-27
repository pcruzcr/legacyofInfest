"""
generate_tmx_reference.py — Genera la tabla de tipos de objeto TMX desde el código.

Por qué existe (AUD-057)
------------------------
`docs/STAGE_CREATION.md` documentaba 8 tipos de enemigo. El motor registra 30.
Las 21 especies con nombre de `docs/18_ENEMY_ROSTER.md` —`WalkerInsect`,
`ShooterQuetzal`, `FlyingHalcon`…— estaban registradas y eran **inalcanzables
en la práctica**: nadie las iba a escribir en Tiled porque la guía de creación
de escenarios no decía que existieran.

Mantener esa tabla a mano garantiza que vuelva a desincronizarse la próxima vez
que alguien añada una especie. Este script la genera desde el registro real y
la escribe entre dos marcadores del documento, de modo que la lista publicada
no puede diferir de la que el cargador acepta.

Uso::

    python scripts/generate_tmx_reference.py           # reescribe el doc
    python scripts/generate_tmx_reference.py --check   # falla si está desfasado

El modo `--check` es el que corre en CI: no arregla nada, sólo avisa de que el
documento y el código han dejado de coincidir.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# El registro importa pygame, que sin esto intenta abrir una ventana real.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

DOC = ROOT / "docs" / "STAGE_CREATION.md"
BEGIN = "<!-- BEGIN GENERATED: tipos de objeto -->"
END = "<!-- END GENERATED: tipos de objeto -->"


def build_table() -> str:
    """Tabla markdown con cada tipo aceptado en la capa `Objects`."""
    from src.framework.entities import bestiary_registry, entity_factory
    from src.framework.stage.stage_loader import StageLoader
    from src.framework.stage.tmx_diagnostics import BUILTIN_OBJECT_TYPES

    entity_factory.ensure_registered()
    registered = sorted(StageLoader._entity_registry)
    species = bestiary_registry.SPECIES

    lines = [
        BEGIN,
        "",
        "> Tabla generada por `scripts/generate_tmx_reference.py` desde el",
        "> registro real de entidades. No la edites a mano: añade la especie a",
        "> `bestiary_registry.SPECIES` y vuelve a ejecutar el script.",
        "",
        "### Tipos estructurales (capa `Objects`)",
        "",
        "| Type | Geometría | Propiedades |",
        "|---|---|---|",
    ]
    structural = {
        "PlayerSpawn": ("Punto", "— (la Y son los pies del jugador)"),
        "Checkpoint": ("Rectángulo", "`checkpoint_id` (int) **obligatoria**"),
        "NextTrigger": ("Rectángulo", "— (completa el escenario)"),
        "MessageTrigger": ("Rectángulo", "`text`, `duration`"),
        "MessageTrigger_Once": ("Rectángulo", "`text`, `duration` (una sola vez)"),
        "HazardZone": ("Rectángulo", "`damage` (float, 0.25 por defecto)"),
        "DeathPit": ("Rectángulo", "— (caer aquí mata)"),
        "CameraLock": ("Rectángulo", "`lock_x`, `lock_y` (bool)"),
        "Waypoint": ("Punto", "`owner_id` — ruta para la entidad con ese nombre"),
    }
    for name in BUILTIN_OBJECT_TYPES:
        geometry, props = structural.get(name, ("—", "—"))
        lines.append(f"| `{name}` | {geometry} | {props} |")

    lines += [
        "",
        "### Arquetipos de enemigo (capa `Objects`, objetos punto)",
        "",
        "| Type | Ajustable con propiedades |",
        "|---|---|",
    ]
    archetype_props = {
        "Walker": "`patrol_length`, `facing`, `patrol_speed`, `alert_speed`, `damage_on_contact`",
        "Flying": "`flight_mode`, `flight_speed`, `sine_amplitude`, `sine_frequency`",
        "Shooter": "`fire_rate`, `projectile_speed`, `projectile_damage`, `patrol_length`",
        "Charger": "`charge_speed`, `patrol_speed`, `alert_speed`",
        "Archer": "`fire_rate`, `projectile_speed`",
        "Brute": "`patrol_speed`, `alert_speed`, `max_health`",
        "Caster": "`fire_rate`, `projectile_damage`",
        "Assassin": "`patrol_speed`, `alert_speed`",
    }
    for name, props in archetype_props.items():
        if name in registered:
            lines.append(f"| `{name}` | {props} |")

    lines += [
        "",
        "### Especies con nombre (capa `Objects`, objetos punto)",
        "",
        "Cada una es un arquetipo con sus valores ya puestos, tomados de",
        "`docs/18_ENEMY_ROSTER.md`. Puedes sobreescribir cualquiera con una",
        "propiedad del objeto en Tiled.",
        "",
        "| Type | Nombre | Zona | Vida |",
        "|---|---|---|---|",
    ]
    for species_id in sorted(species):
        spec = species[species_id]
        health = spec.params.get("max_health", "—")
        lines.append(
            f"| `{species_id}` | {spec.display_name} | {spec.zone} | {health} |",
        )

    lines += [
        "",
        "### Capa `Collision` (vocabulario distinto)",
        "",
        "| Type | Comportamiento |",
        "|---|---|",
        "| *(ninguno)* o `Solid` | Colisión AABB completa |",
        "| `Platform` | Plataforma atravesable desde abajo |",
        "",
        f"Total aceptado en `Objects`: **{len(registered) + len(BUILTIN_OBJECT_TYPES)}** tipos.",
        "",
        END,
    ]
    return "\n".join(lines)


def splice(document: str, table: str) -> str:
    """Sustituye el bloque generado, o lo añade si aún no existe."""
    if BEGIN in document and END in document:
        head = document[: document.index(BEGIN)]
        tail = document[document.index(END) + len(END):]
        return head + table + tail
    return document.rstrip() + "\n\n---\n\n## Referencia de tipos de objeto\n\n" + table + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="No escribe; devuelve 1 si el documento está desfasado.",
    )
    args = parser.parse_args()

    document = DOC.read_text(encoding="utf-8")
    updated = splice(document, build_table())

    if args.check:
        if updated != document:
            print(
                f"{DOC.relative_to(ROOT)} está desfasado respecto al registro de "
                f"entidades.\nEjecuta: python scripts/generate_tmx_reference.py",
                file=sys.stderr,
            )
            return 1
        print(f"{DOC.relative_to(ROOT)}: al día")
        return 0

    if updated == document:
        print(f"{DOC.relative_to(ROOT)}: sin cambios")
        return 0

    DOC.write_text(updated, encoding="utf-8")
    print(f"{DOC.relative_to(ROOT)}: tabla de tipos actualizada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
