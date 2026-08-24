#!/usr/bin/env python3
"""Fail CI when the dependency manifests drift apart.

AUD-007 was possible because three files each claimed to describe the
project's dependencies and none of them agreed:

  * ``pyproject.toml``  — 21 packages, including numba/pymunk/pydantic/orjson
  * ``requirements.txt`` — 12 packages, missing five that ``src/`` imports
    unguarded, so the README's documented install produced a game that could
    not start
  * ``requirements.lock`` — hand-written, internally unsatisfiable, and pinning
    versions that did not exist

This guard makes that class of drift a build failure instead of a bug report.
It compares the *distribution names* declared in ``[project].dependencies``
against those in ``requirements.txt`` (extras are deliberately excluded — they
are optional by definition and must not appear in the base requirements file).

Exit status: 0 when the manifests agree, 1 otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:  # Python >= 3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        print(
            "check_dependency_sync: needs Python >= 3.11 or the 'tomli' "
            "package; skipping.",
            file=sys.stderr,
        )
        raise SystemExit(0) from None

ROOT = Path(__file__).resolve().parent.parent

# Strip everything after the distribution name: version specifiers, extras,
# environment markers. "numpy>=1.26,<2" -> "numpy"; "foo[bar]==1" -> "foo".
_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _canon(raw: str) -> str:
    """PEP 503 normalised name, so Pillow == pillow and pygame_gui == pygame-gui."""
    match = _NAME.match(raw)
    if match is None:
        return ""
    return re.sub(r"[-_.]+", "-", match.group(1)).lower()


def _from_pyproject(path: Path) -> set[str]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    deps = data.get("project", {}).get("dependencies", [])
    return {name for name in (_canon(d) for d in deps) if name}


def _from_requirements(path: Path) -> set[str]:
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-")):
            continue
        name = _canon(line)
        if name:
            names.add(name)
    return names


def main() -> int:
    pyproject = ROOT / "pyproject.toml"
    requirements = ROOT / "requirements.txt"

    for path in (pyproject, requirements):
        if not path.exists():
            print(f"FAIL  missing manifest: {path.relative_to(ROOT)}")
            return 1

    declared = _from_pyproject(pyproject)
    pinned = _from_requirements(requirements)

    missing = sorted(declared - pinned)
    extra = sorted(pinned - declared)

    if not missing and not extra:
        print(f"OK    {len(declared)} dependencies agree across "
              f"pyproject.toml and requirements.txt")
        return 0

    print("FAIL  dependency manifests have drifted apart\n")
    if missing:
        print("  Declared in pyproject.toml but absent from requirements.txt:")
        for name in missing:
            print(f"    - {name}")
    if extra:
        print("  Present in requirements.txt but not declared in pyproject.toml:")
        for name in extra:
            print(f"    - {name}")
    print("\n  Fix: edit [project].dependencies in pyproject.toml, then mirror "
          "it into requirements.txt (or regenerate with pip-compile).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
