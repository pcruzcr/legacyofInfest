# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
"""
Carga de los spritesheets propios de Paburu.

Por qué existe este módulo y no se usa `BossBase._load_boss_sprites`:
ese helper busca **seis claves fijas** heredadas del Venado —
`drift`, `hurt`, `charge`, `stomp`, `vine`, `death` — así que nunca
buscaría `boss_paburu_stone.png` ni ninguna de las hojas por forma que
define el canon (17_BOSS_SPEC §6.2). Tampoco admite un tamaño de frame
distinto por hoja, y las formas de Paburu van de 32×32 a 64×80.

Se usa `AssetLoader.load_sprite_sheet`, que es API pública del engine:
no se modifica nada del profesor.

Las hojas viven en `assets/sprites/boss_paburu/`, no en la carpeta
compartida `assets/sprites/bosses/`. Motivo concreto:
`tools/generate_all_assets.py` (código del profesor) tiene a Paburu en
su tabla de bosses y regenera ahí `stone/stone_slam/mask/gold/black/
spirit/hurt/transcend` como placeholders de 64×64. Cualquiera que corra
ese script pisaría el arte. La carpeta propia es la que manda el GDD §8.

Se regenera con: `python tools/gen_paburu_art.py`
"""
from __future__ import annotations

import logging

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader

SPRITE_DIR = settings.ASSETS_DIR / "sprites" / "boss_paburu"

_LOG = logging.getLogger(__name__)
_CACHE: dict[str, list[pygame.Surface]] = {}


def load_sheet(name: str, fw: int, fh: int) -> list[pygame.Surface]:
    """Frames de `boss_paburu_{name}.png`, o [] si el archivo no está.

    Devolver lista vacía en vez de fallar es deliberado: el boss dibuja
    sus placeholders grises cuando falta una hoja, así que el juego corre
    igual con arte a medio hacer. Es lo que permite trabajar "primero en
    gris, el arte después" sin ramas muertas en el código de dibujo.
    """
    key = f"{name}:{fw}x{fh}"
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    path = SPRITE_DIR / f"boss_paburu_{name}.png"
    frames: list[pygame.Surface] = []
    if path.exists():
        try:
            frames = AssetLoader.load_sprite_sheet(path, fw, fh)
        except (pygame.error, FileNotFoundError, PermissionError):
            _LOG.warning("boss_paburu: no se pudo cargar %s", path)
    _CACHE[key] = frames
    return frames


def clear_cache() -> None:
    """Para los tests, y para recargar arte sin reiniciar el juego."""
    _CACHE.clear()
