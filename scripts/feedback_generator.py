"""
feedback_generator.py — Auto feedback based on common errors detected in TMX/code.

Usage:
    python scripts/feedback_generator.py --grade results.json --output feedback.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FEEDBACK_RULES: dict[str, list[dict]] = {
    "tmx_missing_checkpoint": [
        {"pattern": "No checkpoint layer", "msg": "Add a tile layer named 'Checkpoint' (or object group with checkpoint objects)."},
        {"pattern": "score.*checkpoint.*<", "msg": "Add at least one checkpoint object to 'Checkpoint' layer."},
    ],
    "tmx_missing_spawn": [
        {"pattern": "PlayerSpawn", "msg": "Place a PlayerSpawn point (object with type='PlayerSpawn' in an object group)."},
    ],
    "tmx_no_enemies": [
        {"pattern": "enemies", "msg": "Place at least 2-3 enemies in your stage. Use a tile layer or object group 'Enemies'."},
    ],
    "tmx_no_collectibles": [
        {"pattern": "collectibles", "msg": "Add collectibles (coins, items) to make the stage engaging."},
    ],
    "boss_no_phases": [
        {"pattern": "phase", "msg": "Implement at least 2 phase transitions (e.g., self._phase = 1/2). Look at BossBase for examples."},
    ],
    "boss_no_attacks": [
        {"pattern": "attack", "msg": "Add at least 2 distinct attack patterns. See BossBase.attack_patterns for reference."},
    ],
    "boss_no_events": [
        {"pattern": "event", "msg": "Connect boss events (on_phase_change, on_death, on_hurt) to game systems."},
    ],
    "boss_no_methods": [
        {"pattern": "method", "msg": "Override at least 5 methods from BossBase for full credit."},
    ],
}


def parse_args() -> argparse.Namespace:
    """Parse CLI: --grade (input JSON), --output (markdown path)."""
    p = argparse.ArgumentParser(description="Generate feedback from grade results")
    p.add_argument("--grade", required=True, help="Grade JSON file")
    p.add_argument("--output", default="feedback.md", help="Output markdown file")
    return p.parse_args()


def generate_feedback(grade_data: dict) -> str:
    """Build markdown feedback string from grade JSON by matching rubric categories against FEEDBACK_RULES."""
    lines = ["# Feedback Report\n", f"**Student:** {grade_data.get('student', 'unknown')}\n", ""]

    categories = grade_data.get("categories", {})
    for cat, info in categories.items():
        score = info.get("score", 0)
        max_score = info.get("max", 1)
        pct = (score / max_score * 100) if max_score else 0
        lines.append(f"## {cat}: {score}/{max_score} ({pct:.0f}%)\n")

        if pct >= 90:
            lines.append("Well done!\n")
        elif pct >= 70:
            lines.append("Good progress, but room for improvement.\n")
        else:
            lines.append("Needs significant work.\n")

        for rule_cat, suggestions in FEEDBACK_RULES.items():
            if rule_cat.startswith(cat.lower()[:3]):
                for rule in suggestions:
                    if rule["pattern"].lower() in str(info).lower():
                        lines.append(f"- {rule['msg']}\n")

        lines.append("")

    overall = grade_data.get("overall", {})
    if overall:
        pct = overall.get("percentage", 0)
        lines.append(f"## Overall: {overall.get('score', 0)}/{overall.get('max', 1)} ({pct:.0f}%)\n")
        if pct >= 90:
            lines.append("Excellent work!\n")
        elif pct >= 70:
            lines.append("Good effort. Review the suggestions above.\n")
        else:
            lines.append("Please review the rubric and address the issues above.\n")

    return "\n".join(lines)


def main() -> None:
    """Read grade JSON, generate feedback markdown, write to --output."""
    args = parse_args()
    with open(args.grade) as f:
        grade_data = json.load(f)
    feedback = generate_feedback(grade_data)
    Path(args.output).write_text(feedback)
    print(f"Feedback written to {args.output}")


if __name__ == "__main__":
    main()
