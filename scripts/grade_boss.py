"""
grade_boss.py — Auto-grade student boss Python files.

Evaluates:
  - Boss class inherits from BossBase
  - Phase transitions implemented (at least 2 phases)
  - Attack patterns defined (at least 2)
  - Events connected (PLAYER_DAMAGED, etc.)
  - HP thresholds for phase changes
  - Telegraph state exists (wind-up before attacks)
  - Hurt/Damage states implemented
  - Boss has unique name and appearance config

Usage:
    python scripts/grade_boss.py path/to/student_boss.py
    python scripts/grade_boss.py --dir submissions/boss1/
    python scripts/grade_boss.py --json submissions/boss1/boss.py
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


RUBRIC: dict[str, int] = {
    "inherits_bossbase": 10,
    "phase_transitions": 15,
    "attack_patterns": 15,
    "hp_thresholds": 10,
    "telegraph_state": 10,
    "hurt_damage_states": 10,
    "event_connections": 10,
    "boss_name_config": 10,
    "imports_valid": 5,
    "class_structure": 5,
}


def grade_boss(path: Path) -> dict[str, Any]:
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
    if path.suffix != ".py":
        result["errors"].append(f"Not a .py file (got {path.suffix})")

    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        result["errors"].append(f"Cannot read file: {e}")
        result["percentage"] = 0.0
        return result

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        result["errors"].append(f"Syntax error: {e}")
        result["percentage"] = 0.0
        return result

    # Imports valid
    has_correct_imports = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names = [n.name for n in node.names]
            if "BossBase" in names:
                has_correct_imports = True
    if has_correct_imports:
        result["categories"]["imports_valid"] = {"score": RUBRIC["imports_valid"], "max": RUBRIC["imports_valid"], "msg": "Imports BossBase"}
    else:
        result["categories"]["imports_valid"] = {"score": 0, "max": RUBRIC["imports_valid"], "msg": "Missing BossBase import"}
        result["warnings"].append("Add 'from src.framework.entities.boss_base import BossBase'")

    # Find boss class
    boss_class: ast.ClassDef | None = None
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            bases = [b.id if isinstance(b, ast.Name) else "" for b in node.bases]
            if "BossBase" in bases:
                boss_class = node
                break

    if boss_class is None:
        result["categories"]["inherits_bossbase"] = {"score": 0, "max": RUBRIC["inherits_bossbase"], "msg": "No class inherits BossBase"}
        result["errors"].append("Create a class that inherits from BossBase")
        result["percentage"] = 0.0
        return result
    result["categories"]["inherits_bossbase"] = {"score": RUBRIC["inherits_bossbase"], "max": RUBRIC["inherits_bossbase"], "msg": f"Class '{boss_class.name}' inherits BossBase"}

    # Boss name config  # BUG-079 FIX: también acepta set_boss_name()
    has_boss_config = False
    for node in ast.walk(boss_class):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr == "boss_name":
                    has_boss_config = True
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "set_boss_name":
                has_boss_config = True
    if has_boss_config:
        result["categories"]["boss_name_config"] = {"score": RUBRIC["boss_name_config"], "max": RUBRIC["boss_name_config"], "msg": "Has boss_name config"}
    else:
        result["categories"]["boss_name_config"] = {"score": 5, "max": RUBRIC["boss_name_config"], "msg": "No explicit boss_name found"}

    # Find methods
    methods: dict[str, ast.FunctionDef] = {}
    for node in ast.iter_child_nodes(boss_class):
        if isinstance(node, ast.FunctionDef):
            methods[node.name] = node

    # Phase transitions (look for phase-related methods or state changes)
    phase_methods = [n for n in methods if "phase" in n.lower() or "phase" in n.lower()]
    state_transitions = 0
    for _name, func in methods.items():
        for node in ast.walk(func):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                doc = node.value.value
                if isinstance(doc, str) and "phase" in doc.lower():
                    state_transitions += 1
            if isinstance(node, ast.Attribute) and node.attr == "change_state":
                state_transitions += 1
    total_phase_indicators = len(phase_methods) + state_transitions
    if total_phase_indicators >= 2:
        result["categories"]["phase_transitions"] = {"score": RUBRIC["phase_transitions"], "max": RUBRIC["phase_transitions"], "msg": f"{total_phase_indicators} phase indicator(s)"}
    elif total_phase_indicators == 1:
        result["categories"]["phase_transitions"] = {"score": 8, "max": RUBRIC["phase_transitions"], "msg": "Only 1 phase indicator (need ≥2)"}
        result["warnings"].append("Add a second phase (e.g. phase2 method or change_state call)")
    else:
        result["categories"]["phase_transitions"] = {"score": 0, "max": RUBRIC["phase_transitions"], "msg": "No phase transitions detected"}

    # Attack patterns
    attack_methods = [n for n in methods if "attack" in n.lower() or "pattern" in n.lower()]
    if len(attack_methods) >= 2:
        result["categories"]["attack_patterns"] = {"score": RUBRIC["attack_patterns"], "max": RUBRIC["attack_patterns"], "msg": f"{len(attack_methods)} attack method(s)"}
    elif len(attack_methods) == 1:
        result["categories"]["attack_patterns"] = {"score": 8, "max": RUBRIC["attack_patterns"], "msg": "Only 1 attack pattern (need ≥2)"}
    else:
        result["categories"]["attack_patterns"] = {"score": 0, "max": RUBRIC["attack_patterns"], "msg": "No attack patterns found"}

    # HP thresholds
    hp_thresholds = 0
    for _name, func in methods.items():
        for node in ast.walk(func):
            if isinstance(node, ast.Compare):
                for c in [node.left, node.comparators]:
                    if isinstance(c, ast.Attribute) and "hp" in c.attr.lower():
                        hp_thresholds += 1
                    elif isinstance(c, ast.Name) and c.id == "self":
                        hp_thresholds += 1
            if isinstance(node, ast.If):
                for child in ast.walk(node):
                    if isinstance(child, ast.Attribute) and "hp" in child.attr.lower():
                        hp_thresholds += 1
    if hp_thresholds >= 2:
        result["categories"]["hp_thresholds"] = {"score": RUBRIC["hp_thresholds"], "max": RUBRIC["hp_thresholds"], "msg": f"{hp_thresholds} HP threshold check(s)"}
    elif hp_thresholds == 1:
        result["categories"]["hp_thresholds"] = {"score": 5, "max": RUBRIC["hp_thresholds"], "msg": "Only 1 HP threshold (need ≥2 for 2 phases)"}
    else:
        result["categories"]["hp_thresholds"] = {"score": 0, "max": RUBRIC["hp_thresholds"], "msg": "No HP threshold checks"}

    # Telegraph state
    has_telegraph = "telegraph" in methods or "telegraph" in str(source).lower()
    if has_telegraph:
        result["categories"]["telegraph_state"] = {"score": RUBRIC["telegraph_state"], "max": RUBRIC["telegraph_state"], "msg": "telegraph state/method found"}
    else:
        result["categories"]["telegraph_state"] = {"score": 0, "max": RUBRIC["telegraph_state"], "msg": "No telegraph state"}
        result["warnings"].append("Add a telegraph/wind-up state before attacks")

    # Hurt/damage states
    has_hurt = "hurt" in methods or "damage" in methods or "take_damage" in methods
    if has_hurt:
        result["categories"]["hurt_damage_states"] = {"score": RUBRIC["hurt_damage_states"], "max": RUBRIC["hurt_damage_states"], "msg": "Has hurt/damage handler"}
    else:
        result["categories"]["hurt_damage_states"] = {"score": 0, "max": RUBRIC["hurt_damage_states"], "msg": "No hurt/damage handler"}
        result["errors"].append("Add a take_damage or hurt method")

    # Event connections
    event_refs = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and "emit" in func.attr.lower():
                event_refs += 1
            if isinstance(func, ast.Attribute) and "subscribe" in func.attr.lower():
                event_refs += 1
            if isinstance(func, ast.Attribute) and "publish" in func.attr.lower():
                event_refs += 1
    if event_refs >= 2:
        result["categories"]["event_connections"] = {"score": RUBRIC["event_connections"], "max": RUBRIC["event_connections"], "msg": f"{event_refs} event interaction(s)"}
    elif event_refs == 1:
        result["categories"]["event_connections"] = {"score": 5, "max": RUBRIC["event_connections"], "msg": "Only 1 event reference"}
    else:
        result["categories"]["event_connections"] = {"score": 0, "max": RUBRIC["event_connections"], "msg": "No event connections"}

    # Class structure
    method_count = len(methods)
    if method_count >= 5:
        result["categories"]["class_structure"] = {"score": RUBRIC["class_structure"], "max": RUBRIC["class_structure"], "msg": f"{method_count} methods"}
    elif method_count >= 3:
        result["categories"]["class_structure"] = {"score": 3, "max": RUBRIC["class_structure"], "msg": f"Only {method_count} methods"}
    else:
        result["categories"]["class_structure"] = {"score": 0, "max": RUBRIC["class_structure"], "msg": f"Only {method_count} methods (need ≥5)"}

    total = sum(c["score"] for c in result["categories"].values())
    result["score"] = total
    result["max_score"] = sum(RUBRIC.values())
    result["percentage"] = round(total / result["max_score"] * 100, 1)
    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Grade student boss Python files")
    parser.add_argument("paths", nargs="+", help="Python files or directories")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--dir", help="Scan directory for .py files")
    args = parser.parse_args()

    py_files: list[Path] = []
    if args.dir:
        d = Path(args.dir)
        if d.exists():
            py_files.extend(d.rglob("*.py"))
    for p_str in args.paths:
        p = Path(p_str)
        if p.is_dir():
            py_files.extend(p.rglob("*.py"))
        elif p.exists():
            py_files.append(p)

    if not py_files:
        print("No Python files found.")
        return 1

    py_files = list(set(py_files))

    all_results: list[dict[str, Any]] = []
    for pyf in sorted(py_files):
        r = grade_boss(pyf)
        all_results.append(r)
        if not args.json:  # BUG-080 FIX: rutas relativas
            try:
                rel = pyf.resolve().relative_to(_PROJECT_ROOT)
            except ValueError:
                rel = pyf
            print(f"\n{'='*50}")
            print(f"  {rel}")
            print(f"{'='*50}")
            for cat, data in sorted(r["categories"].items()):
                status = "[PASS]" if data["score"] >= data["max"] else "[WARN]️ " if data["score"] > 0 else "[FAIL]"
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
