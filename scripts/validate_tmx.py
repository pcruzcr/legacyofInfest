"""
validate_tmx.py — Validate TMX map files for common errors.

Exits with code 0 if all maps pass, 1 if any fail.
Can also be run in interactive mode (--fix) to suggest fixes.

Usage:
    python scripts/validate_tmx.py
    python scripts/validate_tmx.py assets/maps/stage0/stage0.tmx
    python scripts/validate_tmx.py --fix
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

MAPS_DIR = _PROJECT_ROOT / "assets" / "maps"
KNOWN_TILESETS = ["tileset_stage0", "tileset_zone1", "tileset_zone2", "tileset_zone3"]
KNOWN_TMX_PROPERTIES = {
    "stage_id", "stage_name", "bgm_track", "time_limit",
    "climate", "background_zone", "gravity_multiplier",
}
KNOWN_CLIMATES = {"rain", "fog", "wind", "snow", "clear", "storm", "sandstorm"}
KNOWN_LAYER_PREFIXES = {"BG_", "Terrain", "Collision", "Objects", "FG_"}
REQUIRED_MAP_PROPS = ["stage_id", "stage_name", "bgm_track"]


def _loader_required_layers() -> list[str]:
    """Las capas que `StageLoader` exige, leídas del propio cargador.

    Este script declaraba ``REQUIRED_LAYERS = ["Terrain"]`` mientras el
    cargador exigía ocho. Un mapa con sólo Terrain pasaba la validación y el
    juego lo rechazaba al abrirlo — un validador que aprueba lo que el motor
    rechaza es peor que no tener validador: enseña a no fiarse de él (AUD-058).
    """
    from src.framework.stage.stage_loader import REQUIRED_LAYERS as LOADER_LAYERS

    return list(LOADER_LAYERS)


def _valid_object_types() -> list[str]:
    """Tipos aceptados en la capa `Objects`, tomados del registro real."""
    from src.framework.entities import entity_factory
    from src.framework.stage.stage_loader import StageLoader
    from src.framework.stage.tmx_diagnostics import known_object_types

    entity_factory.ensure_registered()
    return known_object_types(list(StageLoader._entity_registry))


_errors: list[str] = []
_warnings: list[str] = []


def error(msg: str) -> None:
    _errors.append(msg)


def warn(msg: str) -> None:
    _warnings.append(msg)


def validate_tmx(path: Path) -> bool:
    _errors.clear()
    _warnings.clear()
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as e:
        error(f"XML parse error: {e}")
        return False

    tag = root.tag
    if tag != "map":
        error(f"Root element is '{tag}', expected 'map'")
        return False

    w = int(root.get("width", 0))
    h = int(root.get("height", 0))
    tw = int(root.get("tilewidth", 0))
    th = int(root.get("tileheight", 0))

    if w <= 0 or h <= 0:
        error(f"Invalid map dimensions: {w}x{h}")
    if tw <= 0 or th <= 0:
        error(f"Invalid tile size: {tw}x{th}")

    tilesets = root.findall("tileset")
    if not tilesets:
        error("No tilesets defined")
    for ts in tilesets:
        name = ts.get("name", "")
        int(ts.get("firstgid", 1))
        img = ts.find("image")
        if img is not None:
            src = img.get("source", "")
            img_path = (path.parent / src).resolve()
            if not img_path.exists():
                warn(f"Tileset '{name}' image not found: {img_path}")

    props = root.find("properties")
    prop_dict: dict[str, str] = {}
    if props is not None:
        for p in props.findall("property"):
            prop_dict[p.get("name", "")] = p.get("value", "")
    for req in REQUIRED_MAP_PROPS:
        if req not in prop_dict:
            error(f"Missing required map property: '{req}'")
    if "climate" in prop_dict and prop_dict["climate"] not in KNOWN_CLIMATES:
        warn(f"Unknown climate '{prop_dict['climate']}', known: {sorted(KNOWN_CLIMATES)}")

    layers = root.findall("layer")
    object_group_names = [og.get("name", "") for og in root.findall("objectgroup")]
    layer_names = [line.get("name", "") for line in layers]
    all_layer_names = layer_names + object_group_names
    for req_layer in _loader_required_layers():
        if req_layer not in all_layer_names:
            error(
                f"Falta la capa obligatoria '{req_layer}'. "
                f"El escenario no cargará sin ella."
            )

    for ln in layer_names:
        if not any(ln.startswith(p) for p in KNOWN_LAYER_PREFIXES):
            warn(f"Layer name '{ln}' doesn't match known prefixes: {KNOWN_LAYER_PREFIXES}")

    for layer in layers:
        data = layer.find("data")
        if data is None:
            error(f"Layer '{layer.get('name')}' has no <data> element")
            continue
        encoding = data.get("encoding", "csv")
        if encoding != "csv":
            warn(f"Layer '{layer.get('name')}' uses '{encoding}' encoding (expected 'csv')")
        raw = (data.text or "").strip()
        tile_ids = [int(x) for x in raw.replace("\n", "").split(",") if x.strip()]
        expected = w * h
        if len(tile_ids) != expected:
            # Era un aviso, y por eso llevaba tiempo desatendido en
            # `boss_venado.tmx`, donde cinco de seis capas tenían longitudes de
            # 613 a 815 en vez de 800. pytmx acepta el CSV torcido y construye
            # una matriz de la altura equivocada, así que **cada tile de esa
            # capa queda desplazado**: un fondo pintado saldría movido y no
            # habría ningún mensaje que lo explicara. Es un error, no un aviso
            # (AUD-058).
            error(
                f"La capa '{layer.get('name')}' tiene {len(tile_ids)} tiles y el "
                f"mapa es {w}x{h} = {expected}. Con esa longitud los tiles se "
                f"desplazan al cargar."
            )

    _validate_objects(root, path)

    return len(_errors) == 0


def _validate_objects(root: ET.Element, path: Path) -> None:
    """Comprueba tipos y propiedades de cada objeto (AUD-058).

    Antes esto sólo buscaba un PlayerSpawn, y lo aceptaba tanto por `type`
    como por `name`. El cargador lee únicamente `type`, así que un objeto
    *llamado* PlayerSpawn pero sin tipo pasaba la validación y hacía fallar la
    carga con «No PlayerSpawn found» — el validador decía que el mapa estaba
    bien y el juego decía lo contrario sobre el mismo archivo.
    """
    from src.framework.stage.tmx_diagnostics import (
        COLLISION_OBJECT_TYPES,
        suggest_types,
    )

    valid_types = _valid_object_types()
    spawns = 0

    for og in root.findall("objectgroup"):
        group = og.get("name", "")
        for obj in og.findall("object"):
            # Tiled 1.9+ escribe `class`; las versiones anteriores, `type`.
            obj_type = obj.get("type") or obj.get("class") or ""
            obj_id = obj.get("id", "?")
            where = f"objeto id={obj_id} en la capa '{group}'"

            if group == "Collision":
                if obj_type and obj_type not in COLLISION_OBJECT_TYPES:
                    warn(
                        f"{where}: type='{obj_type}' no significa nada en la capa "
                        f"Collision; se tratará como suelo sólido. "
                        f"Válidos: {', '.join(COLLISION_OBJECT_TYPES)}"
                    )
                continue

            if group != "Objects":
                continue

            if not obj_type:
                error(f"{where}: sin type. El cargador lo ignoraría por completo.")
                continue

            if obj_type not in valid_types:
                hint = suggest_types(obj_type, valid_types)
                extra = f" ¿Quisiste decir {', '.join(hint)}?" if hint else ""
                error(f"{where}: type='{obj_type}' no existe.{extra}")
                continue

            if obj_type == "PlayerSpawn":
                spawns += 1

            if obj_type == "Checkpoint":
                props = {
                    p.get("name", "")
                    for p in obj.findall("./properties/property")
                }
                if "checkpoint_id" not in props:
                    error(
                        f"{where}: un Checkpoint necesita la propiedad int "
                        f"'checkpoint_id'. Sin ella el escenario no carga."
                    )

    if spawns == 0:
        error(
            "No hay ningún objeto con type='PlayerSpawn' en la capa 'Objects'. "
            "Es donde aparece el jugador: sin él el escenario no carga."
        )
    elif spawns > 1:
        error(f"Hay {spawns} objetos PlayerSpawn; debe haber exactamente uno.")


def find_tmx_files(base: Path) -> list[Path]:
    if base.is_file() and base.suffix == ".tmx":
        return [base]
    tmx_files: list[Path] = []
    for p in base.rglob("*.tmx"):
        tmx_files.append(p)
    return tmx_files


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Validate TMX map files")
    parser.add_argument("paths", nargs="*", help="TMX files or directories to validate")
    parser.add_argument("--fix", action="store_true", help="Suggest fixes for common issues")
    parser.add_argument("--ci", action="store_true", help="CI mode: only fail on errors (ignore warnings)")
    args = parser.parse_args()

    if args.paths:
        tmx_files: list[Path] = []
        for p_str in args.paths:
            p = Path(p_str)
            if not p.exists():
                print(f"Path not found: {p}")
                return 1
            tmx_files.extend(find_tmx_files(p))
    else:
        tmx_files = find_tmx_files(MAPS_DIR)

    if not tmx_files:
        print("No TMX files found.")
        return 1

    tmx_files = list(set(tmx_files))
    total = len(tmx_files)
    passed = 0
    failed = 0

    print(f"Validating {total} TMX file(s)...\n")
    for tmx in sorted(tmx_files):
        ok = validate_tmx(tmx)
        rel = tmx.relative_to(_PROJECT_ROOT)
        # Use ASCII-safe markers
        if ok and not _errors and not _warnings:
            print(f"  [OK] {rel}")
            passed += 1
        elif ok and _warnings:
            print(f"  [WARN] {rel}")
            for w in _warnings:
                print(f"       [WARN] {w}")
            passed += 1
        else:
            print(f"  [FAIL] {rel}")
            for e in _errors:
                print(f"       [ERROR] {e}")
            for w in _warnings:
                print(f"       [WARN] {w}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"  {passed}/{total} passed{' with warnings' if _warnings else ''}")
    if failed:
        print(f"  {failed}/{total} FAILED")
    if args.fix:
        print("\n--- Fix suggestions ---")
        print("  1. Add missing map properties via <properties> in TMX")
        print("  2. Ensure 'Terrain' layer exists as base collision layer")
        print("  3. Add PlayerSpawn point in an objectgroup")
        print("  4. Verify tile counts match width*height")
        print("  5. Use known prefixes for layer names")

    if args.ci:
        return 1 if _errors else 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
