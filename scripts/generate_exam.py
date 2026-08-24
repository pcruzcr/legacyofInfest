"""
Script: generate_exam.py
Description: Generate a practice exam PDF from a question bank.
Run:  python scripts/generate_exam.py [--unit UNIT] [--num-questions N]

Output:  exams/practice_exam_{unit}_{timestamp}.pdf

Question bank loaded from: docs/exam_questions.json (or embedded defaults).
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

EXAM_DIR = Path(__file__).resolve().parent.parent / "exams"
DEFAULT_BANK_PATH = Path(__file__).resolve().parent.parent / "docs" / "exam_questions.json"

DEFAULT_QUESTIONS = [
    {"unit": "II", "question": "Explain the difference between a vector and a scalar.",
     "type": "essay", "points": 5},
    {"unit": "II", "question": "Given vector v = (3, 4), compute its length and a unit vector in the same direction.",
     "type": "problem", "points": 10},
    {"unit": "III", "question": "What is a Bézier curve? Describe the role of control points.",
     "type": "essay", "points": 5},
    {"unit": "III", "question": "How does Catmull-Rom interpolation differ from linear interpolation?",
     "type": "essay", "points": 5},
    {"unit": "IV", "question": "Define lerp. Write the formula for linear interpolation between A and B at time t.",
     "type": "problem", "points": 5},
    {"unit": "IV", "question": "What is the purpose of an easing function? Give an example.",
     "type": "essay", "points": 5},
    {"unit": "V", "question": "Explain the RGBA color model. How is alpha blending computed?",
     "type": "essay", "points": 5},
    {"unit": "V", "question": "What is the difference between additive and subtractive color mixing?",
     "type": "essay", "points": 5},
    {"unit": "VI", "question": "Describe the axis-separated (X-first) collision resolution algorithm.",
     "type": "essay", "points": 10},
    {"unit": "VI", "question": "What is the wall-climb bug, and how does it occur in Y-first resolution?",
     "type": "essay", "points": 5},
    {"unit": "VII", "question": "Write the formula for a 3x3 convolution kernel operation on a grayscale image.",
     "type": "problem", "points": 10},
    {"unit": "VII", "question": "What is histogram equalization and when would you use it?",
     "type": "essay", "points": 5},
    {"unit": "VIII", "question": "Explain Otsu's method for automatic threshold selection.",
     "type": "essay", "points": 10},
    {"unit": "VIII", "question": "What is the watershed algorithm used for in image segmentation?",
     "type": "essay", "points": 5},
    {"unit": "IX", "question": "Describe how HOG features are computed for a 32x32 image patch.",
     "type": "essay", "points": 10},
    {"unit": "IX", "question": "What is a confusion matrix and how is accuracy derived from it?",
     "type": "essay", "points": 5},
]


def load_question_bank(path: Path | None) -> list[dict]:
    if path is not None and path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {path}: {e}", file=sys.stderr)
    return DEFAULT_QUESTIONS


def generate_exam(bank: list[dict], unit: str | None, num_questions: int) -> list[dict]:
    if unit:
        filtered = [q for q in bank if q.get("unit", "").lower() == unit.lower()]
        if not filtered:
            print(f"No questions found for unit {unit}, using all.", file=sys.stderr)
            filtered = bank
    else:
        filtered = bank

    random.shuffle(filtered)
    selected = filtered[:num_questions]
    return selected


def write_exam_txt(exam: list[dict], path: Path) -> None:
    EXAM_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("=" * 60)
    lines.append("  PRACTICE EXAM — Legacy of InFest")
    lines.append(f"  Questions: {len(exam)}")
    lines.append("=" * 60)
    lines.append("")
    for i, q in enumerate(exam, 1):
        lines.append(f"{i}. [{q.get('unit', '?')}] ({q.get('points', 5)} pts) {q['question']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a practice exam")
    parser.add_argument("--unit", type=str, default=None,
                        help="Filter by unit (e.g., 'VII')")
    parser.add_argument("--num-questions", type=int, default=10,
                        help="Number of questions (default: 10)")
    args = parser.parse_args()

    bank = load_question_bank(DEFAULT_BANK_PATH)
    exam = generate_exam(bank, args.unit, args.num_questions)

    ts = int(time.time())
    unit_tag = f"unit{args.unit}" if args.unit else "all"
    out_path = EXAM_DIR / f"practice_exam_{unit_tag}_{ts}.txt"
    write_exam_txt(exam, out_path)

    print(f"Generated exam with {len(exam)} questions.")
    print(f"  Output: {out_path}")
    print()
    for i, q in enumerate(exam, 1):
        print(f"  {i}. [{q['unit']}] ({q['points']} pts) {q['question']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
