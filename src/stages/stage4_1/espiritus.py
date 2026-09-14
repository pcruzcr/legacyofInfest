"""AUD-814 — Presencias del Stage 4.1 nuevo: dibujo procedural propio.

Venado, Serpiente y Halcón como siluetas espectrales (contornos sin
colisión ni IA: testifican, no atacan), más la ascensión de cada uno, la
sombra del Halcón, la serpiente de fondo de la Fase 3, la luna de la Fase 5
y la silueta de Paburu. Todo se dibuja con la cámara del escenario; nada
aquí toca física ni estado.
"""
from __future__ import annotations

import math

import pygame

VERDE_ESPECTRAL = (140, 230, 170)
BLANCO_HUESO = (225, 220, 205)
AMBAR_VIEJO = (230, 180, 110)


def _con_alfa(color: tuple[int, int, int], alfa: int) -> tuple[int, int, int, int]:
    return (color[0], color[1], color[2], max(0, min(255, alfa)))


def dibujar_venado(sup: pygame.Surface, x: float, y: float, escala: float,
                   color: tuple[int, int, int], alfa: int, t: float) -> None:
    """Venado de perfil con cornamenta ramificada, flotando levemente."""
    capa = pygame.Surface((160, 140), pygame.SRCALPHA)
    c = _con_alfa(color, alfa)
    flote = math.sin(t * 1.7) * 3.0
    # Cuerpo, cuello y cabeza.
    pygame.draw.ellipse(capa, c, (35, 70 + flote, 70, 34))
    pygame.draw.line(capa, c, (95, 78 + flote), (118, 48 + flote), max(1, int(7 * escala)))
    pygame.draw.circle(capa, c, (122, 44 + flote), int(9 * escala))
    # Patas.
    for px in (45, 60, 80, 95):
        pygame.draw.line(capa, c, (px, 100 + flote), (px - 3, 132), max(1, int(4 * escala)))
    # Cornamenta: dos astas con tres puntas cada una.
    for base_x, dx in ((118, -1), (126, 1)):
        for lx, ly in ((-14, -18), (-6, -26), (4, -30)):
            pygame.draw.line(capa, c, (base_x, 38 + flote),
                             (base_x + dx * 6 + lx, 38 + flote + ly), 2)
    # Ojo.
    pygame.draw.circle(capa, _con_alfa((255, 255, 255), alfa), (124, 42 + flote), 2)
    sup.blit(pygame.transform.smoothscale(capa, (int(160 * escala), int(140 * escala))),
             (x - 80 * escala, y - 140 * escala))


def dibujar_serpiente(sup: pygame.Surface, x: float, y: float, escala: float,
                      color: tuple[int, int, int], alfa: int, t: float) -> None:
    """Serpiente enroscada con cabeza en alto y lengua bífida."""
    capa = pygame.Surface((150, 130), pygame.SRCALPHA)
    c = _con_alfa(color, alfa)
    for i in range(3):
        yy = 100 - i * 18 + math.sin(t * 2.0 + i) * 2.0
        pygame.draw.ellipse(capa, c, (30 + i * 8, yy, 90 - i * 16, 16), 5)
    pygame.draw.line(capa, c, (105, 52), (118, 22), 7)
    pygame.draw.polygon(capa, c, [(110, 14), (128, 16), (119, 30)])
    pygame.draw.line(capa, _con_alfa((255, 120, 120), alfa), (119, 28), (113, 38), 1)
    pygame.draw.line(capa, _con_alfa((255, 120, 120), alfa), (119, 28), (123, 38), 1)
    pygame.draw.circle(capa, _con_alfa((255, 255, 255), alfa), (121, 21), 2)
    sup.blit(pygame.transform.smoothscale(capa, (int(150 * escala), int(130 * escala))),
             (x - 75 * escala, y - 130 * escala))


def dibujar_halcon(sup: pygame.Surface, x: float, y: float, escala: float,
                   color: tuple[int, int, int], alfa: int, t: float,
                   planeo: bool = True) -> None:
    """Halcón planeando: alas en V lenta, cola en abanico."""
    capa = pygame.Surface((170, 90), pygame.SRCALPHA)
    c = _con_alfa(color, alfa)
    batir = math.sin(t * 1.2) * (10 if planeo else 26)
    pygame.draw.polygon(capa, c, [(85, 45), (15, 20 - batir), (40, 48), (85, 52)])
    pygame.draw.polygon(capa, c, [(85, 45), (155, 20 - batir), (130, 48), (85, 52)])
    pygame.draw.ellipse(capa, c, (70, 40, 30, 16))
    pygame.draw.polygon(capa, c, [(70, 44), (48, 52), (70, 54)])
    pygame.draw.circle(capa, c, (96, 42), 7)
    pygame.draw.polygon(capa, c, [(100, 40), (108, 43), (100, 46)])
    sup.blit(pygame.transform.smoothscale(capa, (int(170 * escala), int(90 * escala))),
             (x - 85 * escala, y - 45 * escala))


def dibujar_ascension(sup: pygame.Surface, x: float, y_base: float, alto: float,
                      color: tuple[int, int, int], alfa: int, t: float) -> None:
    """Columna de luz de la ascensión con dos anillos que suben."""
    for w, a in ((26, 0.5), (14, 0.8)):
        capa = pygame.Surface((w * 2, int(alto)), pygame.SRCALPHA)
        capa.fill(_con_alfa(color, int(alfa * a)))
        sup.blit(capa, (x - w, y_base - alto))
    for i in range(2):
        yy = y_base - ((t * 90 + i * alto / 2) % alto)
        pygame.draw.ellipse(sup, _con_alfa(color, alfa), (x - 30, yy - 5, 60, 10), 2)


def dibujar_sombra_de_ave(sup: pygame.Surface, x: float, y: float, escala: float,
                          alfa: int) -> None:
    """Sombra rápida que cruza el cielo (presencia periférica del Halcón)."""
    capa = pygame.Surface((120, 40), pygame.SRCALPHA)
    c = _con_alfa((20, 16, 14), alfa)
    pygame.draw.polygon(capa, c, [(60, 20), (10, 8), (35, 22), (60, 24)])
    pygame.draw.polygon(capa, c, [(60, 20), (110, 8), (85, 22), (60, 24)])
    sup.blit(capa, (x - 60 * escala, y))


def dibujar_serpiente_de_fondo(sup: pygame.Surface, x0: float, y0: float,
                               ancho: float, color: tuple[int, int, int],
                               alfa: int, t: float) -> None:
    """Rastro sinuoso que repta entre los huesos: ¿se vio o no se vio?"""
    puntos = []
    pasos = 24
    for i in range(pasos + 1):
        x = x0 + ancho * i / pasos
        y = y0 + math.sin(i * 0.9 + t * 2.2) * 8 - i * 0.6
        puntos.append((x, y))
    if len(puntos) > 1:
        pygame.draw.lines(sup, _con_alfa(color, alfa), False, puntos, 4)


def dibujar_luna(sup: pygame.Surface, x: int, y: int, radio: int,
                 alfa: int = 235) -> None:
    """Luna craterizada de la planicie (y del Halcón, más pequeña)."""
    capa = pygame.Surface((radio * 2 + 4, radio * 2 + 4), pygame.SRCALPHA)
    cx = cy = radio + 2
    pygame.draw.circle(capa, _con_alfa((232, 236, 250), alfa), (cx, cy), radio)
    for ox, oy, rr in ((-radio // 3, -radio // 5, radio // 5),
                       (radio // 4, radio // 6, radio // 7),
                       (0, -radio // 2, radio // 9)):
        pygame.draw.circle(capa, _con_alfa((200, 206, 222), alfa), (cx + ox, cy + oy), rr)
    sup.blit(capa, (x - cx, y - cy))


def dibujar_paburu(sup: pygame.Surface, x: float, y_base: float, escala: float,
                   alfa: int, t: float) -> None:
    """La silueta que despierta: nunca completa, siempre parcial (diseño)."""
    capa = pygame.Surface((220, 240), pygame.SRCALPHA)
    c = _con_alfa((120, 200, 150), alfa)
    pulso = (math.sin(t * 0.9) + 1.0) / 2.0
    pygame.draw.ellipse(capa, c, (60, 90, 100, 140))
    pygame.draw.circle(capa, c, (110, 60), 34)
    pygame.draw.line(capa, c, (70, 130), (30, 200), 16)
    pygame.draw.line(capa, c, (150, 130), (190, 200), 16)
    borde = _con_alfa((170, 255, 200), min(255, alfa + int(40 * pulso)))
    pygame.draw.ellipse(capa, borde, (60, 90, 100, 140), 2)
    pygame.draw.circle(capa, borde, (110, 60), 34, 2)
    sup.blit(pygame.transform.smoothscale(
        capa, (int(220 * escala), int(240 * escala))),
        (x - 110 * escala, y_base - 240 * escala))


def dibujar_llama_simple(sup: pygame.Surface, x: float, y_base: float,
                         alto: float, t: float, desfase: float = 0.0) -> None:
    """Llama de tres lenguas con parpadeo temporal."""
    a = 0.85 + 0.15 * math.sin(t * 11.0 + desfase)
    capas = [((255, 80, 30), 0.50, 1.00), ((255, 160, 40), 0.32, 0.78),
             ((255, 230, 130), 0.16, 0.55)]
    for color, fr_w, fr_h in capas:
        w = alto * fr_w * a
        h = alto * fr_h * (0.92 + 0.08 * math.sin(t * 13.0 + desfase * 2))
        dx = math.sin(t * 7.0 + desfase) * 3.0
        pygame.draw.polygon(sup, color, [
            (x - w / 2, y_base), (x - w / 5 + dx, y_base - h * 0.62),
            (x + dx, y_base - h), (x + w / 5 + dx, y_base - h * 0.62),
            (x + w / 2, y_base)])


def dibujar_humo(sup: pygame.Surface, x: float, y_base: float, alto: float,
                 t: float, desfase: float = 0.0, alfa: int = 90) -> None:
    """Columna de humo que se ensancha y se disipa al subir."""
    for i in range(5):
        f = (t * 0.35 + desfase + i / 5) % 1.0
        yy = y_base - f * alto
        r = 8 + f * 26
        a = int(alfa * (1.0 - f))
        capa = pygame.Surface((int(r * 2), int(r * 2)), pygame.SRCALPHA)
        pygame.draw.circle(capa, (60, 58, 60, a), (int(r), int(r)), int(r))
        sup.blit(capa, (x - r + math.sin(f * 9 + desfase * 5) * 10, yy - r))


def dibujar_revelacion_serpiente(sup: pygame.Surface, x: float, y: float,
                                 escala: float, alfa: int) -> None:
    """Lo que el rayo revela un instante: la sombra de la Serpiente."""
    capa = pygame.Surface((360, 120), pygame.SRCALPHA)
    c = _con_alfa((15, 14, 16), alfa)
    puntos = []
    for i in range(25):
        px = 10 + i * 14
        py = 60 + math.sin(i * 0.8) * 30
        puntos.append((px, py))
    if len(puntos) > 1:
        pygame.draw.lines(capa, c, False, puntos, 12)
    pygame.draw.polygon(capa, c, [(330, 30), (356, 38), (332, 52)])
    sup.blit(capa, (x - 180 * escala, y))


def dibujar_mausoleo(sup: pygame.Surface, x: float, y_base: float,
                     piedra: tuple[int, int, int],
                     sombra: tuple[int, int, int]) -> None:
    """Mausoleo F1: cuerpo, frontón, puerta y cruz. Hito, no baldosa."""
    pygame.draw.rect(sup, sombra, (x - 70, y_base - 130, 140, 130))
    pygame.draw.rect(sup, piedra, (x - 66, y_base - 126, 132, 126))
    pygame.draw.polygon(sup, piedra, [(x - 76, y_base - 126), (x, y_base - 168),
                                      (x + 76, y_base - 126)])
    pygame.draw.polygon(sup, sombra, [(x - 76, y_base - 126), (x, y_base - 168),
                                      (x + 76, y_base - 126)], 2)
    pygame.draw.rect(sup, sombra, (x - 18, y_base - 80, 36, 80))
    pygame.draw.line(sup, piedra, (x, y_base - 190), (x, y_base - 168), 3)
    pygame.draw.line(sup, piedra, (x - 8, y_base - 184), (x + 8, y_base - 184), 3)


def dibujar_costillar(sup: pygame.Surface, x: float, y_base: float,
                      hueso: tuple[int, int, int]) -> None:
    """Costillar F3: cinco arcos que se alzan del polvo."""
    for i in range(5):
        cx = x - 80 + i * 40
        alto = 90 - abs(i - 2) * 14
        pygame.draw.arc(sup, hueso, (cx - 26, y_base - alto, 52, alto), 3.4,
                        6.0, 5)


def dibujar_gran_quemado(sup: pygame.Surface, x: float, y_base: float,
                         corteza: tuple[int, int, int]) -> None:
    """Gran quemado F4: tronco partido con ramas retorcidas."""
    pygame.draw.polygon(sup, corteza,
                        [(x - 26, y_base), (x - 14, y_base - 220),
                         (x + 14, y_base - 220), (x + 26, y_base)])
    pygame.draw.line(sup, corteza, (x - 6, y_base - 150), (x - 70, y_base - 200), 7)
    pygame.draw.line(sup, corteza, (x + 6, y_base - 120), (x + 66, y_base - 170), 7)
    pygame.draw.line(sup, corteza, (x, y_base - 200), (x + 30, y_base - 250), 5)


def dibujar_gran_cruz(sup: pygame.Surface, x: float, y_base: float,
                      piedra: tuple[int, int, int]) -> None:
    """Gran cruz F5 sobre montículo: el conquistador mayor."""
    pygame.draw.ellipse(sup, piedra, (x - 60, y_base - 18, 120, 18))
    pygame.draw.rect(sup, piedra, (x - 9, y_base - 170, 18, 155))
    pygame.draw.rect(sup, piedra, (x - 42, y_base - 140, 84, 16))


def dibujar_arco_templo(sup: pygame.Surface, x: float, y_base: float,
                        piedra: tuple[int, int, int],
                        brillo: tuple[int, int, int], t: float) -> None:
    """Templo de entrada: escalinata, columnas con capitel, arquitrabe con
    dentellones, frontón con ojo, alas laterales y vegetación.

    AUD-817: el arco de rectángulos + triángulo era "estructura de
    bloques". La silueta manda: escalones anchos, vano alto, remate.
    """
    sombra = tuple(max(0, c - 46) for c in piedra)
    luz = tuple(min(255, c + 26) for c in piedra)
    # Escalinata (3 peldaños que se ensanchan).
    for i in range(3):
        w = 200 - i * 24
        pygame.draw.rect(sup, sombra, (x - w / 2, y_base - 12 - i * 12, w, 12))
        pygame.draw.line(sup, luz, (x - w / 2, y_base - 12 - i * 12), (x + w / 2, y_base - 12 - i * 12), 2)
    base_y = y_base - 48
    # Columnas con capitel y basa.
    for cx in (x - 74, x - 30, x + 30, x + 74):
        pygame.draw.rect(sup, sombra, (cx - 11, base_y - 150, 22, 150))
        pygame.draw.rect(sup, piedra, (cx - 9, base_y - 150, 18, 150))
        for vy in range(int(base_y - 148), int(base_y - 4), 7):
            pygame.draw.line(sup, sombra, (cx - 9, vy), (cx + 9, vy), 1)
        pygame.draw.rect(sup, luz, (cx - 13, base_y - 160, 26, 10))
        pygame.draw.rect(sup, piedra, (cx - 13, base_y - 10, 26, 10))
    # Arquitrabe con dentellones.
    pygame.draw.rect(sup, sombra, (x - 104, base_y - 186, 208, 26))
    pygame.draw.rect(sup, piedra, (x - 100, base_y - 184, 200, 22))
    for dx in range(-92, 96, 12):
        pygame.draw.rect(sup, sombra, (x + dx, base_y - 168, 6, 8))
    # Frontón con ojo central.
    pygame.draw.polygon(sup, piedra, [(x - 104, base_y - 186), (x, base_y - 236),
                                      (x + 104, base_y - 186)])
    pygame.draw.polygon(sup, sombra, [(x - 104, base_y - 186), (x, base_y - 236),
                                      (x + 104, base_y - 186)], 2)
    pygame.draw.circle(sup, brillo, (int(x), int(base_y - 204)), 7)
    # Alas laterales bajas con vegetación.
    for sx in (x - 128, x + 128):
        pygame.draw.rect(sup, sombra, (sx - 26, base_y - 60, 52, 60))
        pygame.draw.rect(sup, piedra, (sx - 24, base_y - 58, 48, 58))
        pygame.draw.circle(sup, (52, 96, 58), (int(sx - 14), int(base_y - 62)), 7)
        pygame.draw.circle(sup, (44, 84, 50), (int(sx + 12), int(base_y - 58)), 5)
    # Vano con resplandor que respira.
    pulso = 0.6 + 0.4 * math.sin(t * 1.4)
    capa = pygame.Surface((120, 200), pygame.SRCALPHA)
    capa.fill((brillo[0], brillo[1], brillo[2], int(30 * pulso)))
    sup.blit(capa, (x - 60, base_y - 190))
