"""
downloader.py — Download student repos, organize by milestone.

Usage:
    python scripts/downloader.py --org <github-org> --assignment <slug> --output <dir>
    python scripts/downloader.py --csv students.csv --output submissions/
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments: --org/--assignment/--csv/--output."""
    p = argparse.ArgumentParser(description="Download student repos")
    p.add_argument("--org", help="GitHub organization name")
    p.add_argument("--assignment", help="GitHub Classroom assignment slug")
    p.add_argument("--csv", help="CSV with columns: student,repo_url")
    p.add_argument("--output", default="submissions", help="Output directory")
    return p.parse_args()


def clone_repo(url: str, dest: Path) -> bool:
    """Clone a single repo by URL into dest. Returns True on success."""
    if dest.exists():
        print(f"  [SKIP] {dest.name} already exists")
        return True
    try:
        subprocess.check_call(
            ["git", "clone", url, str(dest)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
        )
        print(f"  [OK]   {dest.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [FAIL] {dest.name}: {e}")
        return False


def from_csv(csv_path: str, output: Path) -> None:
    """Read student list from CSV (columns: student,repo_url) and clone each repo."""
    output.mkdir(parents=True, exist_ok=True)
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        with_summary(output, lambda: [
            clone_repo(row["repo_url"], output / row["student"])
            for row in reader
        ])


def from_org(org: str, assignment: str, output: Path) -> None:
    """Use gh CLI classroom extension to clone all student repos for an org+assignment."""
    print(f"Fetching repos for {org}/{assignment} via gh CLI...")
    output.mkdir(parents=True, exist_ok=True)
    try:
            subprocess.check_call([
            "gh", "classroom", "clone", assignment,
            "--confirm", "--directory", str(output),
        ], timeout=120)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: gh CLI not found or classroom extension missing.")
        print("Install: gh extension install github/gh-classroom")
        sys.exit(1)


def with_summary(output: Path, fn):
    """Execute clone function and print success/fail summary."""
    results = list(fn())
    success = sum(1 for r in results if r)
    print(f"\nDownloaded {success}/{len(results)} repos to {output}")


def main() -> None:
    """Entry point: dispatch to CSV or org mode based on args."""
    args = parse_args()
    output = Path(args.output)

    if args.csv:
        from_csv(args.csv, output)
    elif args.org and args.assignment:
        from_org(args.org, args.assignment, output)
    else:
        print("Provide --org+--assignment or --csv")
        sys.exit(1)


if __name__ == "__main__":
    main()
