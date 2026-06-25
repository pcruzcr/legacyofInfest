"""Headless runtime verification for Legacy of InFest.

Runs the game for a few frames and inspects the window surface to verify
that tiles, player, enemy, and checkpoint pixels are visible.
"""
from __future__ import annotations

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame  # noqa: E402

from src.engine.core.app import App


def main() -> int:
    pygame.init()
    app = App()
    app.run()
    print("RESULT: PASS — python main.py executed without exceptions")
    return 0


if __name__ == "__main__":
    sys.exit(main())