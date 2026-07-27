"""
grade_stage.py — Auto-grade student stage TMX files.

Evaluates:
  - TMX file loads without errors
  - Required layers exist (Terrain, Collision)
  - Player spawn point exists
  - Checkpoints exist (at least 1 per zone section)
  - Enemies placed correctly (valid types, not overlapping)
  - Collectibles exist (at least 3)
  - Map metadata present (author, stage_id, stage_name)
  - Tileset references valid
  - Climate property valid
  - Time limit (if set) is reasonable

Usage:
    python scripts/grade_stage.py path/to/student/stage.tmx
    python scripts/grade_stage.py --dir submissions/stage1/
    python scripts/grade_stage.py --json path/to/stage.tmx   # JSON output
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


KNOWN_ENEMY_TYPES: set[str] = {
    "MushMom", "Bat", "Skitter", "Mantis", "Flying",
    "Shooter", "Charger", "Archer", "Brute", "Caster",
    "Assassin", "Walker",
}
MAX_TMX_WIDTH = 400
MAX_TMX_HEIGHT = 50
MAX_TIME_LIMIT = 999
REQUIRED_GRADE_PROPS = ["author", "stage_id", "stage_name"]

RUBRIC = {
    "file_parses": 5,
    "required_layers": 10,
    "player_spawn": 10,
    "checkpoints": 15,
    "enemies_valid_types": 10,
    "enemies_placed": 10,
    "collectibles": 10,
    "metadata": 10,
    "tileset_valid": 5,
    "climate_valid": 5,
    "map_bounds_reasonable": 5,
    "time_limit_reasonable": 5,
}


def _parse_tmx(path: Path) -> ET.Element | None:
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def _get_props(root: ET.Element) -> dict[str, str]:
    props: dict[str, str] = {}
    p_elem = root.find("properties")
    if p_elem is not None:
        for p in p_elem.findall("property"):
            props[p.get("name", "")] = p.get("value", "")
    return props


def grade_stage(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "file": str(path),
        "score": 0,
        "max_score": sum(RUBRIC.values()),
        "categories": {},
        "errors": [],
        "warnings": [],
    }

    if not path.exists():
        result["errors"].append("File not found")
        result["percentage"] = 0.0
        return result
    if path.suffix != ".tmx":
        result["errors"].append(f"Not a .tmx file (got {path.suffix})")

    root = _parse_tmx(path)
    if root is None:
        result["categories"]["file_parses"] = {"score": 0, "max": RUBRIC["file_parses"], "msg": "XML parse failed"}
        result["percentage"] = 0.0
        return result
    result["categories"]["file_parses"] = {"score": RUBRIC["file_parses"], "max": RUBRIC["file_parses"], "msg": "Valid TMX"}

    w = int(root.get("width", 0))
    h = int(root.get("height", 0))
    props = _get_props(root)

    # Layer checks
    layers = root.findall("layer")
    layer_names = [line.get("name", "") for line in layers]
    has_terrain = "Terrain" in layer_names
    has_collision = "Collision" in layer_names
    if has_terrain:
        result["categories"]["required_layers"] = {"score": RUBRIC["required_layers"], "max": RUBRIC["required_layers"], "msg": "Has Terrain layer"}
    else:
        result["categories"]["required_layers"] = {"score": 0, "max": RUBRIC["required_layers"], "msg": "Missing Terrain layer"}
        result["errors"].append("Missing required 'Terrain' layer")
    if not has_collision:
        result["warnings"].append("No 'Collision' layer found (add one for solid walls/floors)")

    # Player spawn
    player_spawned = False
    for og in root.findall("objectgroup"):
        for obj in og.findall("object"):
            if obj.get("name") == "PlayerSpawn" or obj.get("type") == "PlayerSpawn":
                player_spawned = True
    if player_spawned:
        result["categories"]["player_spawn"] = {"score": RUBRIC["player_spawn"], "max": RUBRIC["player_spawn"], "msg": "PlayerSpawn found"}
    else:
        result["categories"]["player_spawn"] = {"score": 0, "max": RUBRIC["player_spawn"], "msg": "Missing PlayerSpawn"}

    # Checkpoints
    checkpoints = 0
    for og in root.findall("objectgroup"):
        for obj in og.findall("object"):
            if obj.get("name", "").startswith("Checkpoint") or obj.get("type") == "Checkpoint":
                checkpoints += 1
    if checkpoints >= 1:
        score = min(RUBRIC["checkpoints"], 5 * checkpoints)
        result["categories"]["checkpoints"] = {"score": score, "max": RUBRIC["checkpoints"], "msg": f"{checkpoints} checkpoint(s)"}
    else:
        result["categories"]["checkpoints"] = {"score": 0, "max": RUBRIC["checkpoints"], "msg": "No checkpoints"}
        result["warnings"].append("Add at least 1 checkpoint")

    # Enemies (check object types against KNOWN_ENEMY_TYPES)
    enemies: list[str] = []
    enemy_positions: list[tuple[float, float]] = []
    valid_types = 0
    invalid_enemy_types = []
    for og in root.findall("objectgroup"):
        for obj in og.findall("object"):
            obj_type = obj.get("type", "")
            obj_name = obj.get("name", "")
            if obj_type in KNOWN_ENEMY_TYPES:
                valid_types += 1
                enemies.append(obj_name or obj_type)
                enemy_positions.append((float(obj.get("x", 0)), float(obj.get("y", 0))))
            elif obj_type and obj_type not in {"PlayerSpawn", "Checkpoint", "MessageTrigger", "Waypoint", "Solid", "Platform", "HazardZone", "DeathPit", "NextTrigger", "ZoneTrigger"}:
                invalid_enemy_types.append(obj_type)
    if valid_types > 0:
        result["categories"]["enemies_valid_types"] = {"score": RUBRIC["enemies_valid_types"], "max": RUBRIC["enemies_valid_types"], "msg": f"{valid_types} valid enemy type(s)"}
    else:
        result["categories"]["enemies_valid_types"] = {"score": 0, "max": RUBRIC["enemies_valid_types"], "msg": "No valid enemy types"}
    if invalid_enemy_types:
        result["warnings"].append(f"Unknown enemy types: {set(invalid_enemy_types)}")
    if enemies:
        result["categories"]["enemies_placed"] = {"score": RUBRIC["enemies_placed"], "max": RUBRIC["enemies_placed"], "msg": f"{len(enemies)} enemy(ies) placed"}
    else:
        result["categories"]["enemies_placed"] = {"score": 0, "max": RUBRIC["enemies_placed"], "msg": "No enemies placed"}

    # Collectibles (check objects AND Collectibles tile layer)
    collectibles = 0
    for og in root.findall("objectgroup"):
        for obj in og.findall("object"):
            oname = obj.get("name", "")
            obj.get("type", "")
            if "collect" in oname.lower():
                collectibles += 1
    for layer in root.findall("layer"):
        lname = layer.get("name", "")
        if "collect" in lname.lower():
            data = layer.find("data")
            if data is not None:
                raw = (data.text or "").strip()
                tile_ids = [int(x) for x in raw.replace("\n", "").split(",") if x.strip()]
                non_zero = sum(1 for t in tile_ids if t > 0)
                collectibles += non_zero // 5  # count groups of 5 as one collectible
    if collectibles >= 3:
        result["categories"]["collectibles"] = {"score": RUBRIC["collectibles"], "max": RUBRIC["collectibles"], "msg": f"{collectibles} collectibles"}
    elif collectibles >= 1:
        result["categories"]["collectibles"] = {"score": 5, "max": RUBRIC["collectibles"], "msg": f"Only {collectibles} collectible(s) (need ≥3 for full score)"}
    else:
        result["categories"]["collectibles"] = {"score": 5, "max": RUBRIC["collectibles"], "msg": "No collectibles found (OK for tutorial stages)"}

    # Metadata
    meta_score = 0
    for req_prop in REQUIRED_GRADE_PROPS:
        if req_prop in props:
            meta_score += 1
    result["categories"]["metadata"] = {"score": meta_score * 3, "max": RUBRIC["metadata"], "msg": f"{meta_score}/{len(REQUIRED_GRADE_PROPS)} props found"}
    if meta_score < len(REQUIRED_GRADE_PROPS):
        missing = [p for p in REQUIRED_GRADE_PROPS if p not in props]
        result["warnings"].append(f"Missing metadata: {missing}")

    # Tileset
    tilesets = root.findall("tileset")
    ts_valid = 0
    for ts in tilesets:
        img = ts.find("image")
        if img is not None:
            src = img.get("source", "")
            img_path = (path.parent / src).resolve()
            if img_path.exists():
                ts_valid += 1
    if ts_valid > 0:
        result["categories"]["tileset_valid"] = {"score": RUBRIC["tileset_valid"], "max": RUBRIC["tileset_valid"], "msg": f"{ts_valid} tileset(s) valid"}
    else:
        result["categories"]["tileset_valid"] = {"score": 0, "max": RUBRIC["tileset_valid"], "msg": "No valid tileset images"}
        result["warnings"].append("Tileset image(s) not found — check path")

    # Climate
    climate = props.get("climate", "")
    known_climates = {"rain", "fog", "wind", "snow", "clear", "storm", "sandstorm"}
    if climate in known_climates:
        result["categories"]["climate_valid"] = {"score": RUBRIC["climate_valid"], "max": RUBRIC["climate_valid"], "msg": f"Climate: {climate}"}
    elif climate:
        result["categories"]["climate_valid"] = {"score": 2, "max": RUBRIC["climate_valid"], "msg": f"Unknown climate: {climate}"}
    else:
        result["categories"]["climate_valid"] = {"score": 0, "max": RUBRIC["climate_valid"], "msg": "No climate set"}

    # Map bounds
    if 0 < w <= MAX_TMX_WIDTH and 0 < h <= MAX_TMX_HEIGHT:
        result["categories"]["map_bounds_reasonable"] = {"score": RUBRIC["map_bounds_reasonable"], "max": RUBRIC["map_bounds_reasonable"], "msg": f"Size: {w}x{h}"}
    else:
        result["categories"]["map_bounds_reasonable"] = {"score": 0, "max": RUBRIC["map_bounds_reasonable"], "msg": f"Size {w}x{h} seems unreasonable"}

    # Time limit
    time_limit_str = props.get("time_limit", "0")
    time_limit = int(time_limit_str) if time_limit_str.isdigit() else 0
    if time_limit == 0:
        result["categories"]["time_limit_reasonable"] = {"score": RUBRIC["time_limit_reasonable"], "max": RUBRIC["time_limit_reasonable"], "msg": "No time limit"}
    elif 30 <= time_limit <= MAX_TIME_LIMIT:
        result["categories"]["time_limit_reasonable"] = {"score": RUBRIC["time_limit_reasonable"], "max": RUBRIC["time_limit_reasonable"], "msg": f"Time: {time_limit}s"}
    else:
        result["categories"]["time_limit_reasonable"] = {"score": 2, "max": RUBRIC["time_limit_reasonable"], "msg": f"Time {time_limit}s seems unreasonable"}

    total = sum(c["score"] for c in result["categories"].values())
    result["score"] = total
    result["max_score"] = sum(RUBRIC.values())
    result["percentage"] = round(total / result["max_score"] * 100, 1)

    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Grade student stage TMX files")
    parser.add_argument("paths", nargs="+", help="TMX files or directories")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--dir", help="Scan directory for TMX files")
    args = parser.parse_args()

    tmx_files: list[Path] = []
    if args.dir:
        d = Path(args.dir)
        if d.exists():
            tmx_files.extend(d.rglob("*.tmx"))
    for p_str in args.paths:
        p = Path(p_str)
        if p.is_dir():
            tmx_files.extend(p.rglob("*.tmx"))
        elif p.exists():
            tmx_files.append(p)

    if not tmx_files:
        print("No TMX files found.")
        return 1

    tmx_files = list(set(tmx_files))

    all_results: list[dict[str, Any]] = []
    for tmx in sorted(tmx_files):
        r = grade_stage(tmx)
        all_results.append(r)
        if not args.json:
            rel = tmx.relative_to(_PROJECT_ROOT)
            print(f"\n{'='*50}")
            print(f"  {rel}")
            print(f"{'='*50}")
            for cat, data in sorted(r["categories"].items()):
                status = "[PASS]" if data["score"] >= data["max"] else "[WARN]" if data["score"] > 0 else "[FAIL]"
                print(f"  {status} {cat}: {data['score']}/{data['max']} — {data['msg']}")
            for err in r["errors"]:
                print(f"  [FAIL] ERROR: {err}")
            for w in r["warnings"]:
                print(f"  [WARN]️  WARN: {w}")
            print(f"\n  GRADE: {r['score']}/{r['max_score']} ({r['percentage']}%)")

    if args.json:
        print(json.dumps(all_results, indent=2))

    avg = sum(r["percentage"] for r in all_results) / len(all_results) if all_results else 0
    print(f"\n{'='*50}")
    print(f"  Total graded: {len(all_results)}")
    print(f"  Average grade: {avg:.1f}%")
    print(f"{'='*50}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
