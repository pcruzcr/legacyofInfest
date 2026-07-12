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
KNOWN_LAYER_PREFIXES = {"BG_", "Terrain", "Collision", "Hazards", "Collectibles", "Entities", "FG_"}
REQUIRED_LAYERS = ["Terrain"]
REQUIRED_MAP_PROPS = ["stage_id", "stage_name", "bgm_track"]


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
        first_gid = int(ts.get("firstgid", 1))
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
    layer_names = [l.get("name", "") for l in layers]
    for req_layer in REQUIRED_LAYERS:
        if req_layer not in layer_names:
            error(f"Missing required layer: '{req_layer}'")

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
            warn(f"Layer '{layer.get('name')}' has {len(tile_ids)} tiles, expected {expected} ({w}x{h})")

    object_groups = root.findall("objectgroup")
    has_player_spawn = False
    for og in object_groups:
        og_name = og.get("name", "")
        for obj in og.findall("object"):
            obj_type = obj.get("type", "")
            obj_name = obj.get("name", "")
            if obj_name == "PlayerSpawn" or obj_type == "PlayerSpawn":
                has_player_spawn = True

    if not has_player_spawn:
        warn("No PlayerSpawn object found in any objectgroup")

    return len(_errors) == 0


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
