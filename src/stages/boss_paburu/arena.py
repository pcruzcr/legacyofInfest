# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
"""
Constantes geométricas de la arena de Paburu — LA SALA DEL JUICIO.

Fuente única de verdad para los números que también viven en
`tools/gen_paburu_tmx.py` (bloque «La catacumba»). Si se regenera el TMX
con otra geometría, este archivo se actualiza con él — y desde PAB-07 esa
promesa tiene guardián: `tests/test_cementerio_paburu.py` compara estas
constantes contra las propiedades reales del mapa en cada suite.

PAB-07 (auditoría final, 2026-08-14). Este archivo se quedó con la
geometría de la arena ORIGINAL de 800×608 en el origen del mapa a través
de dos rediseños (cementerio de 4160 px, catacumba a 1312 de profundidad),
y nadie lo notó porque los tests de la Forma 1 contaban lanzamientos, no
posiciones. El resultado, medido en la sala real:

  · EL SELLO emergía en y=512 — la SUPERFICIE, 700 px sobre la pelea:
    columnas, marcas y ánimas invisibles e inofensivas.
  · El rayo ocular moría al primer fotograma: su chequeo de límites era
    `0 ≤ y ≤ 608` y el rayo vive en y≈1200.
  · Las piedras «tocaban el suelo» al nacer: FLOOR_Y=560 quedaba por
    encima de la boca que las escupe.

Tres de tres ataques de la forma rotos por constantes viejas. La lección
va más allá de este archivo: un contador de eventos no verifica geometría.

No se leen del TMX en runtime a propósito: los ataques necesitan la
geometría en el `__init__` del boss, antes de que el loader publique los
rects, y duplicar estas constantes con guardián es más barato y más
legible que inferirlas de la lista de colisiones.
"""
from __future__ import annotations

# ── El interior de la catacumba (px de MUNDO, no locales) ─────────
# gen_paburu_tmx.py: CAT_X0=3296 · CAT_W=800 · CAT_TOP=736 · CAT_FLOOR=1296
ARENA_W = 800
#: Alto del MAPA entero. Los chequeos de «se salió por arriba/abajo» de los
#: proyectiles usan esta cota: en un mapa de dos plantas, lo que está por
#: encima del interior sigue siendo mapa, no el vacío.
ARENA_H = 1312

WALL_W = 16
FLOOR_Y = 1296         # cara superior del suelo de la Sala: los pies apoyan aquí

# Límites jugables horizontales (entre las paredes de roca del interior).
PLAY_LEFT = 3296 + WALL_W          # 3312
PLAY_RIGHT = 4096 - WALL_W         # 4080

# ── Zona del sello (GDD §3.1) ─────────────────────────────────────
# La franja de losas grabadas del suelo de la Sala, donde EL SELLO graba.
# gen_paburu_tmx.py: CAT_SELLO = (CAT_X0 + 176, ·, 224, ·)
SEAL_ZONE_X0 = 3472
SEAL_ZONE_X1 = 3696

# ── Paleta del cementerio (Asset Bible, GDD §3.1) ─────────────────
COL_SKY = (26, 13, 38)          # #1a0d26 púrpura-negro
COL_STONE_PALE = (200, 195, 184)  # #c8c3b8 piedra pálida
COL_SPECTRAL = (0, 200, 100)    # #00c864 verde espectral
COL_GOLD = (232, 177, 44)       # #e8b12c dorado
COL_PEARL = (13, 13, 20)        # #0d0d14 negro perla
