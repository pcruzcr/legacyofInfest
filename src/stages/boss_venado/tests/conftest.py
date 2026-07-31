"""Arnés de pruebas headless: pygame con driver dummy + raíz del juego en sys.path."""
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[4]  # -> legacyofInfest
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)  # AssetLoader usa rutas relativas assets/...

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((320, 224))
