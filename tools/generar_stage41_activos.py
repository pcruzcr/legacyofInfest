#!/usr/bin/env python3
"""AUD-814 — Activos visuales nuevos del Stage 4.1.

Genera desde cero (sin reutilizar el arte anterior del stage4_1):
  assets/tilesets/tileset_stage41_f1..f6.png  (256x256, baldosas de 16 px)
  assets/backgrounds/stage41/f{N}_{far,mid,near}.png  (1280x720, parallax)

Cada familia tiene paleta y motivos propios para que las seis fases se
distingan en capturas consecutivas (criterio S41-VIS del pliego):
  F1 cementerio de día | F2 bosque B&N | F3 osamentas grises |
  F4 bosque muerto ámbar | F5 planicie nocturna | F6 camino verde.

Índices locales por familia (los usa tools/generar_stage41_tmx.py):
  0 superficie, 1 relleno, 2/3 variantes, 8/9 transición,
  4-7 y 12-13 decoración, 16/20/24 bandas de fondo, 32 frente oscuro.
La base (0,0,0) significa transparente: el parallax PNG se ve a través.

Uso:
    python tools/generar_stage41_activos.py
"""
from __future__ import annotations

import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TS = 16

SUP, RELLENO, SUP_VAR, REL_VAR = 0, 1, 2, 3
DEC_A, DEC_B, DEC_C, DEC_D, DEC_E, DEC_F = 4, 5, 6, 7, 12, 13
TRANS_A, TRANS_B = 8, 9
BG_FAR, BG_MID, BG_NEAR, FG_OSCURO = 16, 20, 24, 32


def _baldosa(sup: pygame.Surface, idx: int, base: tuple) -> pygame.Rect:
    r = pygame.Rect((idx % 16) * TS, (idx // 16) * TS, TS, TS)
    if base == (0, 0, 0):
        sup.fill((0, 0, 0, 0), r)
    else:
        sup.fill(base, r)
    return r


def _filo_luz(sup: pygame.Surface, luz: tuple, sombra: tuple) -> None:
    """Filo de luz en el borde superior del tile de superficie (índice 0).

    AUD-817 FASE A: sin una línea de suelo legible, el ojo pierde el plano
    y el jugador "flota" aunque los pies claven la colisión al píxel.
    """
    x0 = 0
    sup.fill(luz, (x0, 0, TS, 1))
    sup.fill(sombra, (x0, 1, TS, 1))


def _ruido(sup: pygame.Surface, x0: int, y0: int, w: int, h: int,
           colores: list, rng: random.Random, prob: float = 0.16) -> None:
    for _ in range(int(w * h * prob)):
        sup.set_at((x0 + rng.randrange(w), y0 + rng.randrange(h)),
                   rng.choice(colores))


def _cruz(sup: pygame.Surface, cx: int, y0: int, h: int, color: tuple,
          grosor: int = 2) -> None:
    pygame.draw.rect(sup, color, (cx - grosor // 2, y0, grosor, h))
    pygame.draw.rect(sup, color, (cx - h // 4, y0 + h // 5, h // 2, grosor))


def _lapida(sup: pygame.Surface, r: pygame.Rect, piedra: tuple, borde: tuple,
            rng: random.Random) -> None:
    """Lápida con cara de luz, cara de sombra y mancha de musgo.

    AUD-817: el bloque plano sin sombreado es "primitiva".
    """
    x, y = r.x + 3, r.y + 4
    pygame.draw.rect(sup, piedra, (x, y, 10, 11))
    pygame.draw.rect(sup, borde, (x, y, 10, 11), 1)
    sup.fill(tuple(max(0, c - 34) for c in piedra), (x + 6, y + 1, 4, 10))
    sup.fill(tuple(min(255, c + 18) for c in piedra), (x + 1, y + 1, 2, 10))
    _cruz(sup, x + 5, y + 2, 6, borde, 1)
    for _ in range(4):
        sup.set_at((x + rng.randrange(10), y + 7 + rng.randrange(4)),
                   (90, 140, 70))


def _arbol(sup: pygame.Surface, r: pygame.Rect, tronco: tuple, copa: tuple,
           rng: random.Random, copa_ancha: bool = True) -> None:
    """Copa por cúmulos superpuestos (3 tonos) + vetas en el tronco.

    AUD-817: puntos sueltos sobre un rectángulo = "árbol geométrico".
    """
    base = [copa, tuple(max(0, c - 28) for c in copa),
            tuple(min(255, c + 26) for c in copa)]
    pygame.draw.rect(sup, tronco, (r.x + 7, r.y + 8, 2, 8))
    for yy in range(r.y + 9, r.y + 15, 2):
        sup.set_at((r.x + 7, yy), tuple(max(0, c - 20) for c in tronco))
    n = 9 if copa_ancha else 5
    for _ in range(n):
        cx = r.x + rng.randrange(2, 14)
        cy = r.y + rng.randrange(0, 8)
        rr = rng.randrange(2, 4 if copa_ancha else 3)
        pygame.draw.circle(sup, rng.choice(base), (cx, cy), rr)


def _calavera(sup: pygame.Surface, r: pygame.Rect, hueso: tuple,
              sombra: tuple) -> None:
    cx, cy = r.x + 8, r.y + 7
    pygame.draw.circle(sup, hueso, (cx, cy), 4)
    pygame.draw.circle(sup, sombra, (cx + 1, cy + 1), 4, 1)
    pygame.draw.rect(sup, hueso, (cx - 2, cy + 2, 4, 4))
    pygame.draw.line(sup, sombra, (cx - 1, cy + 3), (cx - 1, cy + 5), 1)
    pygame.draw.circle(sup, sombra, (cx - 1, cy - 1), 1)
    pygame.draw.circle(sup, sombra, (cx + 2, cy - 1), 1)
    pygame.draw.line(sup, sombra, (cx - 3, cy - 3), (cx - 1, cy - 1), 1)


def _hueso(sup: pygame.Surface, r: pygame.Rect, hueso: tuple,
           rng: random.Random) -> None:
    y = r.y + rng.randrange(4, 12)
    pygame.draw.line(sup, hueso, (r.x + 2, y), (r.x + 13, y), 2)
    for ex in (r.x + 2, r.x + 13):
        pygame.draw.circle(sup, hueso, (ex, y), 2)


def _tronco_cortado(sup: pygame.Surface, r: pygame.Rect, corteza: tuple,
                    anillo: tuple, rng: random.Random) -> None:
    pygame.draw.rect(sup, corteza, (r.x + 3, r.y + 6, 10, 9))
    pygame.draw.ellipse(sup, anillo, (r.x + 3, r.y + 4, 10, 5))
    pygame.draw.ellipse(sup, corteza, (r.x + 5, r.y + 5, 6, 3))
    _ruido(sup, r.x + 3, r.y + 6, 10, 9, [anillo], rng, 0.12)


def _tumba_alta(sup: pygame.Surface, r: pygame.Rect, piedra: tuple,
                borde: tuple) -> None:
    pygame.draw.rect(sup, piedra, (r.x + 6, r.y + 1, 4, 14))
    pygame.draw.line(sup, borde, (r.x + 4, r.y + 4), (r.x + 12, r.y + 4), 1)
    pygame.draw.rect(sup, borde, (r.x + 6, r.y + 1, 4, 14), 1)


def _grieta(sup: pygame.Surface, r: pygame.Rect, verde: tuple,
            rng: random.Random) -> None:
    x, y = r.x + 2, r.y + 2
    while y < r.y + 14:
        sup.set_at((x, y), verde)
        sup.set_at((x + 1, y), verde)
        x = max(r.x + 1, min(r.x + 14, x + rng.choice((-1, 0, 1))))
        y += 1


def _franja(sup: pygame.Surface, idx: int, alto: int, color: tuple,
            detalle: tuple | None, rng: random.Random) -> None:
    r = _baldosa(sup, idx, (0, 0, 0))
    sup.fill(color, (r.x, r.y + TS - alto, TS, alto))
    if detalle is not None:
        for x in range(r.x, r.x + TS, 2):
            h = rng.randrange(2, alto)
            sup.fill(detalle, (x, r.y + TS - h, 1, h))


def _motivo(sup: pygame.Surface, idx: int, forma: str, color: tuple,
            rng: random.Random) -> None:
    """Una pieza de silueta (izq/centro/der se elige por `forma`):
    "l" (borde izquierdo), "c" (relleno), "r" (borde derecho).

    AUD-816: las franjas punteadas uniformes eran la señal de "debug".
    Las siluetas se componen por secuencias l+c..+r a alturas variadas,
    en grupos con huecos, nunca en línea continua.
    """
    r = _baldosa(sup, idx, (0, 0, 0))
    x0, y0 = r.x, r.y
    if forma == "l":
        xs = (x0 + 6, x0 + 16, x0 + 16, x0 + 6)
    elif forma == "r":
        xs = (x0, x0 + 10, x0 + 10, x0)
    else:
        xs = (x0, x0 + 16, x0 + 16, x0)
    tope = y0 + rng.randrange(6, 12)
    pygame.draw.polygon(sup, color, [(xs[0], y0 + 16), (xs[0], tope + 3),
                                     (xs[1], tope), (xs[1], y0 + 16)])
    for _ in range(14):
        sup.set_at((x0 + rng.randrange(16), y0 + rng.randrange(16)),
                   color)


def _motivos_familia(sup: pygame.Surface, rng: random.Random,
                     c_far: tuple, c_mid: tuple, c_near: tuple) -> None:
    """Tres piezas por plano (l/c/r) con el color de silueta de la fase."""
    for idx, forma in ((17, "l"), (18, "c"), (19, "r")):
        _motivo(sup, idx, forma, c_far, rng)
    for idx, forma in ((21, "l"), (22, "c"), (23, "r")):
        _motivo(sup, idx, forma, c_mid, rng)
    for idx, forma in ((25, "l"), (26, "c"), (27, "r")):
        _motivo(sup, idx, forma, c_near, rng)


def _familia_f1(sup: pygame.Surface, rng: random.Random) -> None:
    """Cementerio de día: tierra cálida, césped, lápidas claras, verja."""
    tierra, tierra_o = (168, 129, 92), (122, 90, 62)
    cesped, cesped_o = (96, 158, 74), (64, 118, 52)
    piedra, borde = (214, 208, 192), (140, 132, 116)
    # AUD-816 P0: la masa densa empieza en la fila 0. La colisión apoya
    # los pies en el borde superior del tile; si lo denso empieza 10 px
    # abajo, el jugador "flota" sobre la hierba. Franja fina (3 px).
    r = _baldosa(sup, SUP, tierra)
    sup.fill(cesped, (r.x, r.y, TS, 3))
    _ruido(sup, r.x, r.y, TS, TS, [cesped_o, tierra_o], rng)
    r = _baldosa(sup, RELLENO, tierra)
    _ruido(sup, r.x, r.y, TS, TS, [tierra_o], rng, 0.22)
    r = _baldosa(sup, SUP_VAR, tierra)
    for x in range(r.x + 1, r.x + TS, 3):
        sup.fill(cesped_o, (x, r.y, 1, 3))
    _ruido(sup, r.x, r.y + 3, TS, TS - 3, [tierra_o], rng, 0.18)
    r = _baldosa(sup, REL_VAR, tierra_o)
    _ruido(sup, r.x, r.y, TS, TS, [tierra], rng, 0.22)
    _baldosa(sup, TRANS_A, cesped)
    _baldosa(sup, TRANS_B, (150, 150, 150))
    _lapida(sup, _baldosa(sup, DEC_A, (0, 0, 0)), piedra, borde, rng)
    r = _baldosa(sup, DEC_B, (0, 0, 0))
    _cruz(sup, r.x + 8, r.y + 3, 10, piedra, 2)
    sup.fill(tierra, (r.x, r.y + 13, TS, 3))
    r = _baldosa(sup, DEC_C, (0, 0, 0))
    for i in range(4):
        sup.fill(borde, (r.x + 1 + i * 4, r.y + 3, 2, 10))
    sup.fill(borde, (r.x + 1, r.y + 6, 15, 1))
    _arbol(sup, _baldosa(sup, DEC_D, (0, 0, 0)), (58, 90, 44),
           (44, 110, 52), rng)
    _arbol(sup, _baldosa(sup, DEC_E, (0, 0, 0)), (58, 90, 44),
           (44, 110, 52), rng, False)
    r = _baldosa(sup, DEC_F, (0, 0, 0))
    sup.fill((200, 190, 170), (r.x + 2, r.y + 9, 12, 4))
    for x in range(r.x + 3, r.x + 14, 2):
        sup.fill((90, 140, 70), (x, r.y + 7, 1, 2))
    # AUD-816: variedad de tumbas (inclinadas, partidas).
    r = _baldosa(sup, 14, (0, 0, 0))
    pygame.draw.polygon(sup, piedra, [(r.x + 4, r.y + 15), (r.x + 7, r.y + 4),
                                      (r.x + 12, r.y + 6), (r.x + 9, r.y + 15)])
    r = _baldosa(sup, 15, (0, 0, 0))
    pygame.draw.rect(sup, piedra, (r.x + 4, r.y + 10, 8, 5))
    _cruz(sup, r.x + 8, r.y + 4, 6, borde, 1)
    _franja(sup, BG_FAR, 7, (110, 150, 190), (140, 170, 200), rng)
    _franja(sup, BG_MID, 9, (70, 120, 80), (50, 95, 60), rng)
    _franja(sup, BG_NEAR, 12, (35, 60, 40), (25, 45, 30), rng)
    _franja(sup, FG_OSCURO, 16, (12, 18, 14), None, rng)
    _motivos_familia(sup, rng, (110, 150, 190), (70, 120, 80),
                     (35, 60, 40))
    _filo_luz(sup, (150, 200, 120), (70, 110, 55))


def _familia_f2(sup: pygame.Surface, rng: random.Random) -> None:
    """Bosque B&N: tierra gris, musgo pálido, lodo, troncos gruesos."""
    gris, gris_o = (168, 168, 172), (120, 120, 126)
    musgo, musgo_o = (200, 205, 190), (150, 158, 140)
    lodo = (92, 90, 88)
    # AUD-816 P0: masa densa desde la fila 0 (ver F1).
    r = _baldosa(sup, SUP, gris)
    sup.fill(musgo, (r.x, r.y, TS, 3))
    _ruido(sup, r.x, r.y, TS, TS, [musgo_o, gris_o], rng)
    r = _baldosa(sup, RELLENO, gris)
    _ruido(sup, r.x, r.y, TS, TS, [gris_o], rng, 0.22)
    r = _baldosa(sup, SUP_VAR, lodo)
    sup.fill((110, 108, 106), (r.x, r.y, TS, 2))
    _ruido(sup, r.x, r.y, TS, TS, [(70, 68, 66)], rng, 0.20)
    r = _baldosa(sup, REL_VAR, gris_o)
    _ruido(sup, r.x, r.y, TS, TS, [gris], rng, 0.22)
    _baldosa(sup, TRANS_A, musgo)
    _baldosa(sup, TRANS_B, (150, 150, 150))
    r = _baldosa(sup, DEC_A, (0, 0, 0))
    pygame.draw.rect(sup, (60, 60, 64), (r.x + 5, r.y + 1, 6, 15))
    _ruido(sup, r.x + 5, r.y + 1, 6, 15, [(90, 90, 96)], rng, 0.20)
    r = _baldosa(sup, DEC_B, (0, 0, 0))
    for i in range(5):
        sup.fill((60, 60, 64), (r.x + 1 + i * 3, r.y + 2, 2, 12))
    r = _baldosa(sup, DEC_C, (0, 0, 0))
    pygame.draw.circle(sup, musgo_o, (r.x + 8, r.y + 12), 5)
    sup.fill(musgo, (r.x + 2, r.y + 10, 12, 3))
    _arbol(sup, _baldosa(sup, DEC_D, (0, 0, 0)), (70, 70, 74),
           (150, 150, 154), rng)
    _arbol(sup, _baldosa(sup, DEC_E, (0, 0, 0)), (70, 70, 74),
           (150, 150, 154), rng, False)
    r = _baldosa(sup, DEC_F, (0, 0, 0))
    sup.fill((60, 60, 64), (r.x + 2, r.y + 12, 12, 2))
    sup.fill((110, 110, 114), (r.x + 7, r.y + 4, 2, 8))
    _franja(sup, BG_FAR, 8, (130, 132, 138), (150, 152, 158), rng)
    _franja(sup, BG_MID, 10, (85, 87, 93), (105, 107, 113), rng)
    _franja(sup, BG_NEAR, 13, (40, 42, 48), (60, 62, 68), rng)
    _franja(sup, FG_OSCURO, 16, (10, 10, 12), None, rng)
    _motivos_familia(sup, rng, (130, 132, 138), (85, 87, 93),
                     (40, 42, 48))
    _filo_luz(sup, (215, 220, 205), (140, 146, 130))


def _familia_f3(sup: pygame.Surface, rng: random.Random) -> None:
    """Osamentas grises: polvo de hueso, roca, calaveras, costillas."""
    polvo, polvo_o = (186, 180, 168), (140, 134, 122)
    roca, roca_o = (110, 108, 104), (80, 78, 76)
    hueso, sombra = (228, 222, 205), (150, 144, 128)
    # AUD-816 P0: masa densa desde la fila 0 (ver F1).
    r = _baldosa(sup, SUP, roca)
    sup.fill(polvo, (r.x, r.y, TS, 3))
    _ruido(sup, r.x, r.y, TS, TS, [polvo_o, hueso], rng)
    r = _baldosa(sup, RELLENO, roca)
    _ruido(sup, r.x, r.y, TS, TS, [roca_o, polvo], rng, 0.22)
    r = _baldosa(sup, SUP_VAR, roca)
    sup.fill(polvo_o, (r.x, r.y, TS, 2))
    _ruido(sup, r.x, r.y, TS, TS, [polvo], rng, 0.20)
    r = _baldosa(sup, REL_VAR, roca_o)
    _ruido(sup, r.x, r.y, TS, TS, [roca], rng, 0.22)
    _baldosa(sup, TRANS_A, polvo)
    _baldosa(sup, TRANS_B, (150, 150, 150))
    _calavera(sup, _baldosa(sup, DEC_A, (0, 0, 0)), hueso, sombra)
    _hueso(sup, _baldosa(sup, DEC_B, (0, 0, 0)), hueso, rng)
    r = _baldosa(sup, DEC_C, (0, 0, 0))
    for i in range(4):
        x = r.x + 2 + i * 4
        pygame.draw.arc(sup, hueso, (x - 2, r.y + 3, 6, 10), 3.4, 6.0, 1)
    sup.fill(polvo, (r.x, r.y + 13, TS, 3))
    r = _baldosa(sup, DEC_D, (0, 0, 0))
    pygame.draw.polygon(sup, roca, [(r.x + 2, r.y + 15), (r.x + 8, r.y + 4),
                                    (r.x + 14, r.y + 15)])
    r = _baldosa(sup, DEC_E, (0, 0, 0))
    _calavera(sup, r, hueso, sombra)
    _hueso(sup, r, sombra, rng)
    r = _baldosa(sup, DEC_F, (0, 0, 0))
    sup.fill(hueso, (r.x + 1, r.y + 12, 14, 2))
    for x in range(r.x + 2, r.x + 15, 3):
        sup.fill(hueso, (x, r.y + 8, 1, 4))
    _franja(sup, BG_FAR, 8, (120, 118, 115), (140, 138, 135), rng)
    _franja(sup, BG_MID, 10, (80, 78, 76), (100, 98, 95), rng)
    _franja(sup, BG_NEAR, 13, (38, 37, 35), (58, 56, 54), rng)
    _franja(sup, FG_OSCURO, 16, (10, 10, 10), None, rng)
    _motivos_familia(sup, rng, (120, 118, 115), (80, 78, 76),
                     (38, 37, 35))
    _filo_luz(sup, (205, 198, 185), (130, 124, 112))


def _familia_f4(sup: pygame.Surface, rng: random.Random) -> None:
    """Bosque muerto ámbar: tierra quemada, tocones, ramas secas."""
    tierra, tierra_o = (172, 118, 66), (128, 84, 46)
    corteza, anillo = (96, 62, 36), (190, 150, 100)
    ceniza = (60, 52, 48)
    # AUD-816 P0: masa densa desde la fila 0 (ver F1).
    r = _baldosa(sup, SUP, tierra_o)
    sup.fill(tierra, (r.x, r.y, TS, 3))
    _ruido(sup, r.x, r.y, TS, TS, [tierra_o, ceniza], rng)
    r = _baldosa(sup, RELLENO, tierra_o)
    _ruido(sup, r.x, r.y, TS, TS, [tierra, ceniza], rng, 0.22)
    r = _baldosa(sup, SUP_VAR, tierra_o)
    sup.fill(ceniza, (r.x, r.y, TS, 2))
    _ruido(sup, r.x, r.y, TS, TS, [tierra], rng, 0.20)
    r = _baldosa(sup, REL_VAR, (110, 72, 40))
    _ruido(sup, r.x, r.y, TS, TS, [tierra_o], rng, 0.22)
    _baldosa(sup, TRANS_A, tierra)
    _baldosa(sup, TRANS_B, (150, 150, 150))
    _tronco_cortado(sup, _baldosa(sup, DEC_A, (0, 0, 0)), corteza, anillo,
                    rng)
    r = _baldosa(sup, DEC_B, (0, 0, 0))
    pygame.draw.line(sup, corteza, (r.x + 3, r.y + 15), (r.x + 12, r.y + 3),
                     2)
    pygame.draw.line(sup, corteza, (r.x + 8, r.y + 9), (r.x + 13, r.y + 6),
                     1)
    sup.fill(tierra, (r.x, r.y + 14, TS, 2))
    r = _baldosa(sup, DEC_C, (0, 0, 0))
    for i in range(3):
        sup.fill(ceniza, (r.x + 2 + i * 5, r.y + 11, 3, 4))
    sup.fill((200, 120, 60), (r.x + 3, r.y + 11, 1, 1))
    r = _baldosa(sup, DEC_D, (0, 0, 0))
    pygame.draw.rect(sup, corteza, (r.x + 7, r.y + 2, 2, 13))
    pygame.draw.line(sup, corteza, (r.x + 7, r.y + 6), (r.x + 3, r.y + 3),
                     1)
    pygame.draw.line(sup, corteza, (r.x + 8, r.y + 8), (r.x + 13, r.y + 5),
                     1)
    _tronco_cortado(sup, _baldosa(sup, DEC_E, (0, 0, 0)), corteza, anillo,
                    rng)
    r = _baldosa(sup, DEC_F, (0, 0, 0))
    sup.fill(corteza, (r.x + 1, r.y + 12, 14, 2))
    sup.fill(anillo, (r.x + 4, r.y + 5, 2, 7))
    _franja(sup, BG_FAR, 8, (190, 130, 70), (215, 160, 95), rng)
    _franja(sup, BG_MID, 10, (130, 85, 45), (160, 110, 60), rng)
    _franja(sup, BG_NEAR, 13, (60, 40, 26), (85, 58, 36), rng)
    _franja(sup, FG_OSCURO, 16, (16, 10, 8), None, rng)
    _motivos_familia(sup, rng, (190, 130, 70), (130, 85, 45),
                     (60, 40, 26))
    _filo_luz(sup, (210, 150, 90), (120, 80, 42))


def _familia_f5(sup: pygame.Surface, rng: random.Random) -> None:
    """Planicie nocturna: tierra azulada, tumbas de conquistador, losas."""
    tierra, tierra_o = (44, 52, 78), (30, 36, 58)
    piedra, borde = (120, 128, 150), (70, 76, 100)
    # AUD-816 P0: masa densa desde la fila 0 (ver F1).
    r = _baldosa(sup, SUP, tierra)
    _ruido(sup, r.x, r.y, TS, TS, [borde, tierra_o], rng, 0.14)
    r = _baldosa(sup, RELLENO, tierra_o)
    _ruido(sup, r.x, r.y, TS, TS, [tierra], rng, 0.20)
    r = _baldosa(sup, SUP_VAR, tierra)
    for x in range(r.x + 1, r.x + TS, 4):
        sup.fill((58, 70, 96), (x, r.y, 1, 3))
    r = _baldosa(sup, REL_VAR, (26, 30, 50))
    _ruido(sup, r.x, r.y, TS, TS, [tierra_o], rng, 0.20)
    _baldosa(sup, TRANS_A, tierra)
    _baldosa(sup, TRANS_B, (150, 150, 150))
    _tumba_alta(sup, _baldosa(sup, DEC_A, (0, 0, 0)), piedra, borde)
    r = _baldosa(sup, DEC_B, (0, 0, 0))
    sup.fill(piedra, (r.x + 2, r.y + 10, 12, 4))
    sup.fill(borde, (r.x + 2, r.y + 10, 12, 1))
    _cruz(sup, r.x + 8, r.y + 2, 8, piedra, 2)
    r = _baldosa(sup, DEC_C, (0, 0, 0))
    pygame.draw.circle(sup, borde, (r.x + 8, r.y + 11), 4)
    pygame.draw.circle(sup, tierra, (r.x + 8, r.y + 11), 2)
    _tumba_alta(sup, _baldosa(sup, DEC_D, (0, 0, 0)), borde, piedra)
    r = _baldosa(sup, DEC_E, (0, 0, 0))
    sup.fill(piedra, (r.x + 4, r.y + 8, 8, 6))
    pygame.draw.line(sup, borde, (r.x + 4, r.y + 8), (r.x + 12, r.y + 8),
                     1)
    r = _baldosa(sup, DEC_F, (0, 0, 0))
    for x in range(r.x + 1, r.x + 15, 3):
        sup.fill((52, 64, 92), (x, r.y + 12, 1, 3))
    # AUD-816: variedad de tumbas (losas bajas, cruz partida).
    r = _baldosa(sup, 14, (0, 0, 0))
    sup.fill(piedra, (r.x + 3, r.y + 11, 10, 3))
    sup.fill(borde, (r.x + 3, r.y + 11, 10, 1))
    r = _baldosa(sup, 15, (0, 0, 0))
    pygame.draw.rect(sup, piedra, (r.x + 7, r.y + 6, 2, 9))
    pygame.draw.line(sup, piedra, (r.x + 4, r.y + 8), (r.x + 9, r.y + 8), 1)
    _franja(sup, BG_FAR, 8, (16, 20, 40), (28, 34, 60), rng)
    _franja(sup, BG_MID, 10, (12, 15, 30), (22, 27, 48), rng)
    _franja(sup, BG_NEAR, 13, (8, 10, 20), (16, 20, 36), rng)
    _franja(sup, FG_OSCURO, 16, (4, 5, 10), None, rng)
    _motivos_familia(sup, rng, (16, 20, 40), (12, 15, 30), (8, 10, 20))
    _filo_luz(sup, (80, 90, 120), (36, 42, 62))


def _familia_f6(sup: pygame.Surface, rng: random.Random) -> None:
    """Camino a Paburu: piedra clara, grietas verdes, flores de luz."""
    piedra, piedra_o = (178, 186, 170), (132, 140, 126)
    verde, verde_o = (110, 255, 150), (60, 180, 100)
    # AUD-816 P0: masa densa desde la fila 0 (ver F1).
    r = _baldosa(sup, SUP, piedra)
    _grieta(sup, r, verde, rng)
    _ruido(sup, r.x, r.y, TS, TS, [piedra_o], rng, 0.12)
    r = _baldosa(sup, RELLENO, piedra_o)
    _ruido(sup, r.x, r.y, TS, TS, [piedra], rng, 0.20)
    r = _baldosa(sup, SUP_VAR, piedra)
    sup.fill((150, 158, 144), (r.x, r.y, TS, 2))
    _ruido(sup, r.x, r.y, TS, TS, [verde_o], rng, 0.08)
    r = _baldosa(sup, REL_VAR, (120, 128, 114))
    _ruido(sup, r.x, r.y, TS, TS, [piedra_o], rng, 0.20)
    _baldosa(sup, TRANS_A, piedra)
    _baldosa(sup, TRANS_B, (150, 150, 150))
    r = _baldosa(sup, DEC_A, (0, 0, 0))
    _grieta(sup, r, verde, rng)
    pygame.draw.circle(sup, verde, (r.x + 12, r.y + 4), 1)
    r = _baldosa(sup, DEC_B, (0, 0, 0))
    sup.fill(verde_o, (r.x + 7, r.y + 8, 2, 6))
    pygame.draw.circle(sup, verde, (r.x + 8, r.y + 6), 2)
    r = _baldosa(sup, DEC_C, (0, 0, 0))
    pygame.draw.rect(sup, piedra_o, (r.x + 5, r.y + 3, 6, 12))
    _grieta(sup, r, verde_o, rng)
    r = _baldosa(sup, DEC_D, (0, 0, 0))
    for dx, dy in ((4, 4), (11, 7), (7, 11)):
        pygame.draw.circle(sup, verde, (r.x + dx, r.y + dy), 1)
        sup.fill(verde_o, (r.x + dx, r.y + dy + 1, 1, 3))
    r = _baldosa(sup, DEC_E, (0, 0, 0))
    _grieta(sup, r, verde, rng)
    _grieta(sup, pygame.Rect(r.x + 6, r.y, 10, 16), verde_o, rng)
    r = _baldosa(sup, DEC_F, (0, 0, 0))
    sup.fill(piedra, (r.x + 2, r.y + 11, 12, 3))
    sup.fill(verde, (r.x + 2, r.y + 11, 12, 1))
    _franja(sup, BG_FAR, 8, (40, 90, 70), (70, 140, 105), rng)
    _franja(sup, BG_MID, 10, (28, 64, 50), (50, 100, 75), rng)
    _franja(sup, BG_NEAR, 13, (16, 38, 30), (30, 66, 50), rng)
    _franja(sup, FG_OSCURO, 16, (6, 14, 11), None, rng)
    _motivos_familia(sup, rng, (40, 90, 70), (28, 64, 50), (16, 38, 30))
    _filo_luz(sup, (150, 220, 170), (90, 140, 110))


_FAMILIAS = (_familia_f1, _familia_f2, _familia_f3, _familia_f4, _familia_f5,
             _familia_f6)


def _fondo(fase: int, plano: str, rng: random.Random) -> pygame.Surface:
    """Un plano de parallax 1280x720 con identidad propia por fase."""
    import math

    W, H = 1280, 720
    sup = pygame.Surface((W, H), pygame.SRCALPHA)
    paletas = {
        1: ((126, 170, 214), (88, 132, 92), (52, 84, 60), (250, 244, 220)),
        2: ((150, 152, 158), (100, 102, 108), (58, 60, 66), (225, 225, 230)),
        3: ((110, 108, 106), (74, 72, 70), (42, 41, 40), (240, 238, 230)),
        4: ((214, 148, 74), (150, 96, 50), (84, 54, 30), (255, 220, 150)),
        5: ((10, 14, 34), (16, 22, 44), (8, 10, 22), (232, 236, 250)),
        6: ((60, 130, 100), (40, 92, 70), (22, 58, 44), (140, 255, 180)),
    }
    cielo, tierra, silueta, extra = paletas[fase]
    for y in range(H):
        t = y / H
        c = tuple(round(cielo[i] + (tierra[i] - cielo[i]) * t)
                  for i in range(3))
        pygame.draw.line(sup, c, (0, y), (W, y))
    if plano == "far":
        if fase in (1, 2, 3, 4):
            pygame.draw.circle(sup, extra, (1020, 130), 46 if fase != 4
                               else 60)
            if fase == 4:
                pygame.draw.circle(sup, cielo, (1005, 120), 52)
        if fase == 5:
            for _ in range(130):
                sup.set_at((rng.randrange(W), rng.randrange(420)), extra)
            pygame.draw.circle(sup, extra, (320, 150), 58)
            for cx, cy, rr in ((300, 140, 9), (335, 165, 6), (315, 130, 5)):
                pygame.draw.circle(sup, (200, 206, 222), (cx, cy), rr)
        if fase == 6:
            # AUD-817: aurora apenas insinuada (2 velos finos). El bloom
            # del escenario (0.30) multiplica lo brillante: con alfa 30
            # las bandas salían neón sólido en runtime.
            for i, y in enumerate((90, 210)):
                for x in range(0, W, 6):
                    a = int(6 + 8 * (0.5 + 0.5 * math.sin(x / 260 + i * 2.1)))
                    sup.fill((90, 200, 140, a), (x, y, 6, 10 - i * 2))
        base = 560
        for x in range(0, W, 8):
            h = 40 + int(30 * (0.5 + 0.5 * math.sin(x / 170 + fase)))
            if fase == 1 and 560 < x < 720:
                pygame.draw.rect(sup, silueta, (x, base - h - 60, 90, 60))
                pygame.draw.polygon(sup, silueta, [
                    (x - 10, base - h - 60), (x + 45, base - h - 110),
                    (x + 100, base - h - 60)])
                continue
            sup.fill(silueta, (x, base - h, 8, h + 160))
    elif plano == "mid":
        # AUD-817: arboleda irregular por grupos con huecos y alturas
        # sembradas; la fila uniforme de árboles iguales era "procedural".
        sup.fill((0, 0, 0, 0))
        base = 620
        x = -40
        while x < W + 40:
            if rng.random() < 0.28:
                x += rng.randrange(60, 170)
                continue
            ancho = rng.randrange(50, 150)
            h_base = 60 + rng.randrange(110)
            n = rng.randrange(2, 5)
            for j in range(n):
                xx = x + j * (ancho // max(1, n)) + rng.randrange(-8, 8)
                h = h_base + rng.randrange(-30, 30)
                if fase == 1 and rng.random() < 0.18:
                    sup.fill(silueta, (xx, base - h - 40, 26, 40))
                    pygame.draw.polygon(sup, silueta, [
                        (xx - 6, base - h - 40), (xx + 13, base - h - 80),
                        (xx + 32, base - h - 40)])
                elif fase == 3 and rng.random() < 0.25:
                    pygame.draw.arc(sup, silueta, (xx, base - h, 40, 60),
                                    0.4, 2.7, 4)
                elif fase == 4 and rng.random() < 0.3:
                    sup.fill(silueta, (xx + 10, base - h, 14, h))
                elif fase == 5 and rng.random() < 0.3:
                    _cruz(sup, xx + 13, base - h - 30, 30, silueta, 3)
                elif fase == 6 and rng.random() < 0.25:
                    pygame.draw.circle(sup, extra, (xx + 13, base - h), 5)
                    sup.fill(silueta, (xx + 12, base - h + 4, 2, 26))
                else:
                    for xxx in range(xx, xx + 26, 4):
                        hh = h - abs(xxx - xx - 13)
                        sup.fill(silueta, (xxx, base - hh, 4, hh + 100))
            x += ancho + rng.randrange(20, 90)
    else:
        # Primer plano irregular: grupos con huecos amplios. F5 casi
        # vacío (planicie abierta: el vacío incomoda).
        sup.fill((0, 0, 0, 0))
        oscuro = tuple(max(0, c - 30) for c in silueta)
        x = 0
        while x < W:
            hueco = rng.randrange(90, 260) if fase != 5 else rng.randrange(220, 420)
            x += hueco
            if x >= W:
                break
            if fase == 5 and rng.random() < 0.5:
                # Cruz solitaria lejana en vez de árbol.
                _cruz(sup, x, 470, 60, oscuro, 5)
                x += 30
                continue
            sup.fill(oscuro, (x, 430, 14, 290))
            pygame.draw.line(sup, oscuro, (x + 7, 470), (x - 40, 430), 5)
            pygame.draw.line(sup, oscuro, (x + 7, 500), (x + 54, 455), 5)
            x += rng.randrange(20, 70)
        sup.fill(oscuro, (0, 690, W, 30))
    return sup


def main() -> None:
    pygame.init()
    dir_ts = os.path.join(RAIZ, "assets", "tilesets")
    dir_bg = os.path.join(RAIZ, "assets", "backgrounds", "stage41")
    os.makedirs(dir_ts, exist_ok=True)
    os.makedirs(dir_bg, exist_ok=True)
    for fase, fn in enumerate(_FAMILIAS, start=1):
        rng = random.Random(4100 + fase)
        sup = pygame.Surface((256, 256), pygame.SRCALPHA)
        fn(sup, rng)
        pygame.image.save(
            sup, os.path.join(dir_ts, f"tileset_stage41_f{fase}.png"))
        for plano in ("far", "mid", "near"):
            img = _fondo(fase, plano,
                         random.Random(7400 + fase * 10 + len(plano)))
            pygame.image.save(
                img, os.path.join(dir_bg, f"f{fase}_{plano}.png"))
    print("activos stage41: 6 tilesets + 18 fondos en stage41/")


if __name__ == "__main__":
    main()