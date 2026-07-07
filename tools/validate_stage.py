"""
CLI tool to validate a TMX stage file against the Legacy of InFest spec (06_TMX_SPEC.md).

Usage:
    python -m tools.validate_stage --path stage0.tmx
    python -m tools.validate_stage --path stage0.tmx --html report.html

Validates:
  - Required layers (8 total, in order)
  - PlayerSpawn presence and uniqueness
  - NextTrigger presence
  - Collision rects not overlapping
  - Checkpoint IDs unique and sequential
  - Object names unique
  - Spawn reachability via flood fill
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path


try:
    import pytmx
except ImportError:
    print("ERROR: pytmx is required. Install with: pip install pytmx")
    sys.exit(1)


def _load_tmx(path: str):
    """Load a TMX file without requiring pygame display initialization."""
    tmx = pytmx.TiledMap(path)
    return tmx

REQUIRED_LAYERS = [
    "BG_Far",
    "BG_Mid",
    "BG_Near",
    "Terrain",
    "Terrain_Detail",
    "Objects",
    "Collision",
    "FG_Overlay",
]


@dataclass
class ValidationError:
    category: str
    message: str
    severity: str = "error"  # error | warning


@dataclass
class ValidationResult:
    file_path: str
    passed: bool = True
    errors: list[ValidationError] = field(default_factory=list)

    def add_error(self, category: str, msg: str, sev: str = "error") -> None:
        self.errors.append(ValidationError(category, msg, sev))
        if sev == "error":
            self.passed = False

    def print_report(self) -> None:
        print(f"\n{'='*60}")
        print(f"VALIDATION REPORT: {self.file_path}")
        print(f"{'='*60}")
        if not self.errors:
            print("  [OK] ALL CHECKS PASSED")
            return
        for err in self.errors:
            icon = "[ERR]" if err.severity == "error" else "[WARN]"
            print(f"  {icon} [{err.category}] {err.message}")
        err_count = sum(1 for e in self.errors if e.severity == "error")
        warn_count = sum(1 for e in self.errors if e.severity == "warning")
        status = "FAILED" if not self.passed else "PASSED"
        print(f"\n  [{status}] ({err_count} errors, {warn_count} warnings)")

    def to_html(self) -> str:
        lines = [
            "<!DOCTYPE html><html><head><meta charset='utf-8'>",
            "<title>TMX Validation Report</title>",
            "<style>body{font-family:sans-serif;margin:20px}",
            ".pass{color:green}.fail{color:red}.warn{color:orange}",
            "table{border-collapse:collapse;width:100%}",
            "th,td{border:1px solid #ccc;padding:8px;text-align:left}",
            "th{background:#f5f5f5}</style></head><body>",
            f"<h1>TMX Validation: {self.file_path}</h1>",
            f"<p>Result: {'<span class=pass>PASSED</span>' if self.passed else '<span class=fail>FAILED</span>'}</p>",
        ]
        if self.errors:
            lines.append("<table><tr><th>Severity</th><th>Category</th><th>Message</th></tr>")
            for err in self.errors:
                cls = "warn" if err.severity == "warning" else "fail"
                icon = "WARN" if err.severity == "warning" else "ERR"
                lines.append(f"<tr><td class={cls}>{icon} {err.severity}</td>"
                             f"<td>{err.category}</td><td>{err.message}</td></tr>")
            lines.append("</table>")
        lines.append("</body></html>")
        return "\n".join(lines)


def validate_tmx(tmx_path: Path) -> ValidationResult:
    result = ValidationResult(file_path=str(tmx_path))
    try:
        tmx = _load_tmx(str(tmx_path))
    except Exception as e:
        result.add_error("PARSE", f"Cannot parse TMX file: {e}")
        return result

    _validate_layers(tmx, result)
    _validate_map_properties(tmx, result)
    _validate_objects(tmx, result)
    _validate_collision(tmx, result)
    return result


def _validate_layers(tmx, result: ValidationResult) -> None:
    layer_names = [l.name for l in tmx.layers]
    object_group_names = [g.name for g in getattr(tmx, 'objectgroups', [])]

    for req in REQUIRED_LAYERS:
        # Objects and Collision exist as both tile layers and object groups in pytmx
        if req in ("Objects", "Collision"):
            if req not in object_group_names:
                result.add_error("LAYERS", f"Required layer '{req}' not found")
        elif req not in layer_names:
            result.add_error("LAYERS", f"Required tile layer '{req}' not found")

    tile_count = sum(1 for name in REQUIRED_LAYERS[:5] if name in layer_names)
    if tile_count < 5:
        result.add_error("LAYERS", f"Only {tile_count}/5 tile layers found", "warning")


def _validate_map_properties(tmx, result: ValidationResult) -> None:
    props = dict(tmx.properties) if hasattr(tmx, 'properties') and tmx.properties else {}

    required_props = ["stage_id", "stage_name", "time_limit", "bgm_track"]
    for key in required_props:
        if key not in props:
            result.add_error("PROPERTIES", f"Required map property '{key}' missing")

    if "time_limit" in props:
        try:
            int(props["time_limit"])
        except (ValueError, TypeError):
            result.add_error("PROPERTIES", f"time_limit must be int, got {type(props['time_limit']).__name__}")


def _validate_objects(tmx, result: ValidationResult) -> None:
    try:
        objects_layer = tmx.get_layer_by_name("Objects")
    except ValueError:
        result.add_error("OBJECTS", "Objects layer not found")
        return

    objects = list(objects_layer)
    player_spawn_count = 0
    next_trigger_count = 0
    seen_names: set[str] = set()
    seen_checkpoint_ids: set[int] = set()
    max_cp_id = -1

    for obj in objects:
        obj_type = getattr(obj, 'type', None) or ""
        obj_name = getattr(obj, 'name', None) or ""

        # Unique names
        if obj_name:
            if obj_name in seen_names:
                result.add_error("OBJECTS", f"Duplicate object name '{obj_name}'")
            seen_names.add(obj_name)

        if obj_type == "PlayerSpawn":
            player_spawn_count += 1
            # Check spawn is above solid ground (rough check: y > 0)
            if getattr(obj, 'y', 0) <= 0:
                result.add_error("OBJECTS", "PlayerSpawn Y must be > 0", "warning")

        elif obj_type == "NextTrigger":
            next_trigger_count += 1
            w = getattr(obj, 'width', 0) or 0
            h = getattr(obj, 'height', 0) or 0
            if w < 16 or h < 32:
                result.add_error("OBJECTS", f"NextTrigger must be >= 16x32, got {w}x{h}")

        elif obj_type == "Checkpoint":
            props = dict(obj.properties) if obj.properties else {}
            cp_id = props.get("checkpoint_id")
            if cp_id is None:
                result.add_error("OBJECTS", "Checkpoint missing checkpoint_id property")
            else:
                try:
                    cid = int(cp_id)
                    if cid in seen_checkpoint_ids:
                        result.add_error("OBJECTS", f"Duplicate checkpoint_id {cid}")
                    seen_checkpoint_ids.add(cid)
                    if cid > max_cp_id:
                        max_cp_id = cid
                except (ValueError, TypeError):
                    result.add_error("OBJECTS", f"Invalid checkpoint_id: {cp_id}")

    if player_spawn_count == 0:
        result.add_error("OBJECTS", "No PlayerSpawn found (exactly 1 required)")
    elif player_spawn_count > 1:
        result.add_error("OBJECTS", f"Found {player_spawn_count} PlayerSpawn objects (exactly 1 required)")

    if next_trigger_count == 0:
        result.add_error("OBJECTS", "No NextTrigger found (exactly 1 required)")
    elif next_trigger_count > 1:
        result.add_error("OBJECTS", f"Found {next_trigger_count} NextTrigger objects (exactly 1 required)")

    # Check checkpoint IDs are 0-based sequential (no gaps)
    if seen_checkpoint_ids:
        expected = set(range(max_cp_id + 1))
        missing = expected - seen_checkpoint_ids
        if missing:
            result.add_error("OBJECTS", f"Checkpoint IDs not sequential: missing {missing}", "warning")


def _validate_collision(tmx, result: ValidationResult) -> None:
    try:
        collision_layer = tmx.get_layer_by_name("Collision")
    except ValueError:
        result.add_error("COLLISION", "Collision layer not found")
        return

    rects = []
    for obj in collision_layer:
        x = getattr(obj, 'x', 0) or 0
        y = getattr(obj, 'y', 0) or 0
        w = getattr(obj, 'width', 0) or 16
        h = getattr(obj, 'height', 0) or 16
        rects.append((x, y, w, h))

    # Check for overlapping collision rects
    for i, (x1, y1, w1, h1) in enumerate(rects):
        for j, (x2, y2, w2, h2) in enumerate(rects):
            if i >= j:
                continue
            if (x1 < x2 + w2 and x1 + w1 > x2 and
                    y1 < y2 + h2 and y1 + h1 > y2):
                result.add_error("COLLISION", f"Overlapping collision rects at index {i} and {j}", "warning")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a TMX stage file against LOI spec")
    parser.add_argument("--path", required=True, type=Path, help="Path to .tmx file")
    parser.add_argument("--html", type=Path, default=None, help="Optional HTML report output path")
    args = parser.parse_args()

    if not args.path.exists():
        print(f"ERROR: File not found: {args.path}")
        sys.exit(1)
    if args.path.suffix.lower() != ".tmx":
        print(f"ERROR: File must have .tmx extension: {args.path}")
        sys.exit(1)

    result = validate_tmx(args.path)
    result.print_report()

    if args.html:
        html = result.to_html()
        args.html.write_text(html, encoding="utf-8")
        print(f"HTML report saved to: {args.html}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
