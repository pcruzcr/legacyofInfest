"""
Editor visual stub — para motor genérico 100%.

Hoy es CLI que valida TMX; mañana puede ser GUI.
"""

from __future__ import annotations

from pathlib import Path


def validate(path: Path) -> bool:
    return path.exists() and path.suffix == ".tmx"


def launch() -> None:
    print("Editor visual — stub: usa Tiled + validate_tmx.py --ci")
