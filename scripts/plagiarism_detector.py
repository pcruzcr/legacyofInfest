"""
plagiarism_detector.py — Compare TMX and code between student submissions.

Usage:
    python scripts/plagiarism_detector.py submissions/ --threshold 0.85
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse CLI: submissions dir, --threshold (0-1), --pattern (glob)."""
    p = argparse.ArgumentParser(description="Detect plagiarism in student submissions")
    p.add_argument("submissions", help="Directory with per-student submission folders")
    p.add_argument("--threshold", type=float, default=0.85, help="Similarity threshold (0-1)")
    p.add_argument("--pattern", default="**/*.tmx", help="Glob pattern to compare")
    return p.parse_args()


def file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file's raw bytes."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def normalize_content(path: Path) -> str:
    """Strip whitespace/comments for comparison."""
    text = path.read_text()
    import re
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"<!--.*?-->", "", text)
    return text


def simhash(text: str) -> int:
    """Simple hash-based fingerprint."""
    h = hashlib.md5(text.encode("utf-8"))
    return int(h.hexdigest(), 16)


def jaccard_similarity(a: set, b: set) -> float:
    """Compute Jaccard similarity (intersection / union) of two sets."""
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def main() -> None:
    """Walk submission dirs pairwise, compare matched files by Jaccard similarity, report matches above threshold."""
    args = parse_args()
    base = Path(args.submissions)
    if not base.is_dir():
        print(f"Error: {base} is not a directory")
        sys.exit(1)

    students = sorted(d.name for d in base.iterdir() if d.is_dir())
    print(f"Found {len(students)} submissions")

    student_files: dict[str, list[Path]] = {}
    for s in students:
        files = list(base.glob(f"{s}/{args.pattern}"))
        if files:
            student_files[s] = files

    reports = []
    names = list(student_files.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a_files = student_files[names[i]]
            for af in a_files:
                rel = af.relative_to(base / names[i])
                bf = base / names[j] / rel
                if not bf.exists():
                    continue
                content_a = normalize_content(af)
                content_b = normalize_content(bf)
                tokens_a = set(content_a.split(","))
                tokens_b = set(content_b.split(","))
                sim = jaccard_similarity(tokens_a, tokens_b)

                if sim >= args.threshold:
                    reports.append((names[i], names[j], str(rel), sim))
                    print(f"  SIMILAR ({sim:.2f}): {names[i]} <-> {names[j]} ({rel})")

    if not reports:
        print("No suspicious similarities found.")
        return

    print(f"\nFound {len(reports)} suspicious pairs above {args.threshold:.0%} threshold.")


if __name__ == "__main__":
    main()
