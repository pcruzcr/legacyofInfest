"""
Module: conftest
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: N/A
Description: Configuración común a todas las pruebas del escenario.

Inicializa pygame en modo headless (sin ventana ni audio) una sola vez por
sesión, para que las pruebas corran en cualquier máquina y en integración
continua sin depender de un escritorio.
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame


@pytest.fixture(scope="session", autouse=True)
def _pygame_iniciado():
    pygame.init()
    pygame.display.set_mode((320, 224))
    yield
    pygame.quit()
