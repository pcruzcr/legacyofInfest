"""
Constantes geométricas de la arena de Paburu (Stage 4-2).

Fuente única de verdad para los números que también viven en
`tools/gen_paburu_tmx.py`. Si se regenera el TMX con otra geometría,
este archivo se actualiza con él.

No se leen del TMX en runtime a propósito: los ataques necesitan la
geometría en el `__init__` del boss, antes de que el loader publique
los rects, y duplicar 8 constantes es más barato y más legible que
inferirlas de la lista de colisiones.
"""
from __future__ import annotations

# ── Dimensiones de la arena (px) ──────────────────────────────────
ARENA_W = 800
ARENA_H = 608

WALL_W = 16
FLOOR_Y = 560          # superficie del suelo: los "pies" apoyan aquí

# Límites jugables horizontales (entre muros)
PLAY_LEFT = WALL_W
PLAY_RIGHT = ARENA_W - WALL_W

# ── Zona del sello (GDD §3.1) ─────────────────────────────────────
# Franja central libre de plataformas donde EL SELLO graba las marcas.
SEAL_ZONE_X0 = 288
SEAL_ZONE_X1 = 512

# ── Paleta del cementerio (Asset Bible, GDD §3.1) ─────────────────
COL_SKY = (26, 13, 38)          # #1a0d26 púrpura-negro
COL_STONE_PALE = (200, 195, 184)  # #c8c3b8 piedra pálida
COL_SPECTRAL = (0, 200, 100)    # #00c864 verde espectral
COL_GOLD = (232, 177, 44)       # #e8b12c dorado
COL_PEARL = (13, 13, 20)        # #0d0d14 negro perla
