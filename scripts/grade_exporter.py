"""
grade_exporter.py — Export grading results to CSV/JSON.

Usage:
    python scripts/grade_exporter.py --input results.json --output grades.csv
    python scripts/grade_exporter.py --input results/ --format json --output grades.json
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse CLI: --input (file or dir), --output (path), --format (csv|json)."""
    p = argparse.ArgumentParser(description="Export grading results")
    p.add_argument("--input", required=True, help="Input JSON file or dir of JSONs")
    p.add_argument("--output", default="grades.csv", help="Output file")
    p.add_argument("--format", choices=["csv", "json"], default="csv")
    return p.parse_args()


def load_results(path: Path) -> list[dict]:
    """Load one or more JSON grade files. If path is a directory, merge all *.json."""
    if path.is_dir():
        results = []
        for f in sorted(path.glob("*.json")):
            with open(f) as fh:
                results.append(json.load(fh))
        return results
    with open(path) as f:
        return [json.load(f)]


def flatten(d: dict, prefix: str = "") -> dict:
    """Recursively flatten nested dict for CSV export (keys become 'parent.child')."""
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten(v, key))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    out.update(flatten(item, f"{key}_{i}"))
                else:
                    out[f"{key}_{i}"] = item
        else:
            out[key] = v
    return out


def export_csv(results: list[dict], output: Path) -> None:
    """Write flattened grade dicts to CSV with auto-detected fieldnames."""
    flat = [flatten(r) for r in results]
    fieldnames = set()
    for row in flat:
        fieldnames.update(row.keys())
    fieldnames = sorted(fieldnames)
    with open(output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in flat:
            w.writerow(row)
    print(f"Exported {len(results)} results to {output}")


def export_json(results: list[dict], output: Path) -> None:
    """Write grade dicts to pretty-printed JSON."""
    with open(output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Exported {len(results)} results to {output}")


def main() -> None:
    """Load grades from --input, flatten, export to --output in --format."""
    args = parse_args()
    results = load_results(Path(args.input))
    output = Path(args.output)

    if args.format == "csv":
        export_csv(results, output)
    else:
        export_json(results, output)


if __name__ == "__main__":
    main()
