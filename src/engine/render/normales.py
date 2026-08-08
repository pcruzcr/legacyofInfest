"""
Module: normales
System: engine.render
Academic Unit: N/A
Description: AUD-340 — mapas de normales procedurales para los sprites.

La fase 5 (GPU) pide normal mapping, y este proyecto no tiene un pipeline de
assets del que salgan mapas de normales: los sprites son procedimentales o de
los estudiantes, y pedir a un estudiante un fichero normal extra por sprite
multiplicaría su trabajo. Así que la normal se **deriva** del propio sprite:
se trata el canal alfa como un mapa de alturas —lo opaco sobresale, lo
transparente se hunde— y el gradiente de esa altura es la pendiente del
relieve.

El pipeline sigue siendo procedural y sigue siendo el del motor: un sprite
sin fichero de normales se ilumina, porque su mapa sale de aquí. Quien quiera
una normal hecha a mano (una armadura con costuras, una piedra tallada) puede
pasarla como segundo atlas, y el gradiente del alfa nunca la contradice
porque entonces no se usa.
"""
from __future__ import annotations

import numpy as np
import pygame


def generar_normales_desde_alfa(
    superficie: pygame.Surface, fuerza: float = 1.0,
) -> pygame.Surface:
    """Mapa de normales en espacio tangente derivado del alfa del sprite.

    Cada píxel del mapa codifica una normal unitaria como RGB = 0.5 + 0.5·n,
    con n = (nx, ny, nz) apuntando hacia fuera de la pantalla (una superficie
    plana sale azul puro, (0.5, 0.5, 1.0)). El alfa del mapa se deja a 255
    porque el alfa del sprite ya viaja en su atlas de color.

    Convención de signos, razonada y no adivinada: el gradiente numpy `gx`
    crece a la derecha de la pantalla y `gy` hacia abajo. En la textura GL, u
    crece a la derecha y v hacia arriba (la subida voltea la superficie), así
    que du = dx y dv = -dy. La normal de una altura H es n = (-dH/du, -dH/dv,
    1) normalizado: la pendiente se inclina hacia la dirección donde la
    altura **baja** —un bulto de alfa alta a la derecha tira de la normal
    hacia la derecha—. Con las sustituciones de arriba:

        nx = -dH/dx            ny = -dH/dv = dH/dy

    o sea `nx` es el gradiente horizontal NEGADO y `ny` es el gradiente
    vertical SIN negar. Metido el signo al revés, un bulto iluminado por la
    izquierda se vería iluminado por la derecha — un espejo, y no se nota en
    el momento, se nota viendo la escena entera.

    `fuerza` escala la pendiente antes de normalizar: 1.0 es el relieve que
    el alfa da naturalmente, y subirlo exagera el bulto para sprites donde el
    alfa varía poco (una sombra redonda con borde suave apenas tiene
    pendiente).
    """
    alto, ancho = superficie.get_height(), superficie.get_width()
    if alto <= 0 or ancho <= 0:
        raise ValueError("el sprite no puede estar vacío para sacarle normales")

    # `tobytes` con "RGBA" devuelve los canales en ese orden vengan de donde
    # vengan las máscaras de la superficie (AUD-229: no se asume el formato).
    # Es `tostring` renombrado desde pygame 2.3; el viejo nombre avisa.
    rgba = np.frombuffer(
        pygame.image.tobytes(superficie, "RGBA", False), np.uint8,
    )
    alfa = (
        rgba[3::4].astype(np.float32).reshape(alto, ancho) / 255.0
    )

    # AUD-340 — numpy ya da los gradientes centrales; lo que hay que acertar
    # son los signos y la normalización, y eso está arriba en el docstring.
    # Ojo con el orden: `np.gradient` devuelve (d/dy, d/dx) — el gradiente
    # del eje 0 primero —, así que `gy` es el de las filas y `gx` el de las
    # columnas. Desempaquetarlos al revés mezcla los canales y el relieve
    # queda como un espejo girado.
    gy, gx = np.gradient(alfa)
    raw = np.empty((alto, ancho, 3), dtype=np.float32)
    raw[..., 0] = -gx * fuerza
    raw[..., 1] = gy * fuerza
    raw[..., 2] = 1.0

    norma = np.sqrt(np.sum(raw * raw, axis=-1, keepdims=True))
    # El gradiente de un alfa normalizado nunca llega a anularse del todo
    # (z = 1), pero una superficie completamente plana lo intenta.
    norma = np.maximum(norma, 1e-6)
    n = raw / norma

    rgb = (n * 0.5 + 0.5) * 255.0
    pixels = np.empty((alto, ancho, 4), dtype=np.uint8)
    pixels[..., 0] = rgb[..., 0].astype(np.uint8)
    pixels[..., 1] = rgb[..., 1].astype(np.uint8)
    pixels[..., 2] = rgb[..., 2].astype(np.uint8)
    pixels[..., 3] = 255

    mapa = pygame.image.frombuffer(pixels.tobytes(), (ancho, alto), "RGBA")
    # Sin `convert_alpha()`: convierte contra la pantalla y en CI no la hay
    # (pygame.error "cannot convert without display"). La superficie de
    # `frombuffer` se sube igual en el lote.
    return mapa
