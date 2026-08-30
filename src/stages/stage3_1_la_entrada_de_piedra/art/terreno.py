"""Baldosas de terreno con cantos y esquinas.

Con el suelo plano bastaba una baldosa de césped y otra de adoquín. Con un
perfil de alturas ya no: cada bloque de tierra tiene un canto superior, dos
caras laterales expuestas y dos esquinas donde el césped dobla. Sin esas
piezas, un escalón se ve como un rectángulo recortado.

La lección viene del pack Forest minimal: su juego de terreno es un
**autotile de nueve piezas**, y lo que lo hace funcionar es que el césped
**dobla por la esquina** — no termina en el canto, baja un par de píxeles
por el costado. Es lo que convierte un bloque en un trozo de tierra con
volumen en vez de una losa vista de frente.

Segunda lección: el relleno de tierra lleva **detalle escaso** —piedrecitas
y raicillas sueltas, unas pocas por baldosa— y no ruido por píxel. El ruido
uniforme se lee como grano de televisión; cuatro piedras bien puestas se
leen como tierra.
"""
from __future__ import annotations

import hashlib

from PIL import Image

from palette import CESPED, PIEDRA, TRONCO, ramp_rgb

T = 16


def _u(semilla: int, i: int) -> float:
    h = hashlib.md5(f"ter{semilla}:{i}".encode()).digest()
    return int.from_bytes(h[:4], "big") / 0xFFFFFFFF


def _tile():
    return Image.new("RGBA", (T, T), (0, 0, 0, 0))


def _tierra(px, semilla, x0=0, x1=T, y0=0, y1=T, tono=1):
    """Relleno de tierra con detalle escaso."""
    pie = ramp_rgb(PIEDRA)
    tro = ramp_rgb(TRONCO)
    for y in range(y0, y1):
        for x in range(x0, x1):
            # Estratos: bandas horizontales muy sutiles, un tono arriba y
            # abajo de la banda. La tierra se deposita en capas y eso se
            # nota aunque sea a 16 px.
            t = tono + (1 if (y // 5) % 2 == 0 else 0)
            px[x, y] = pie[max(0, min(4, t))] + (255,)
    # Piedrecitas y raicillas: cuatro o cinco por baldosa, no más.
    for k in range(4 + int(_u(semilla, 0) * 2)):
        cx = x0 + int(_u(semilla, k * 3 + 1) * max(1, x1 - x0))
        cy = y0 + int(_u(semilla, k * 3 + 2) * max(1, y1 - y0))
        raiz = _u(semilla, k * 3 + 3) > 0.65
        color = tro[2] if raiz else pie[3]
        largo = 3 if raiz else 2
        for j in range(largo):
            xx, yy = cx + j, cy + (j // 2 if raiz else 0)
            if x0 <= xx < x1 and y0 <= yy < y1:
                px[xx, yy] = color + (255,)


def _cesped(px, semilla, x0=0, x1=T, y=0, alto=4):
    """Capa de césped con borde superior irregular.

    El borde no es una línea: cada columna tiene su propia altura, con
    variación de un par de píxeles. Una franja verde de canto recto es lo
    que más delata que el terreno está hecho de baldosas.
    """
    ces = ramp_rgb(CESPED)
    for x in range(x0, x1):
        sube = int(_u(semilla, x) * 3)          # 0..2 px de irregularidad
        for j in range(alto + sube):
            yy = y - sube + j
            if not (0 <= yy < T):
                continue
            # Sólo la primera línea recibe el tono claro; el cuerpo del
            # césped baja un escalón. La vegetación no puede ser la fuente
            # principal de saturación de la pantalla — pero el canto sí
            # tiene que seguir leyéndose, porque es lo que le dice al
            # jugador dónde puede pararse. Por eso se oscurece la masa y
            # se conserva el filo.
            t = 3 if j == 0 else (2 if j < alto else 1)
            px[x, yy] = ces[t] + (255,)
        # Briznas sueltas asomando por encima del canto.
        if _u(semilla, x + 90) > 0.72:
            yy = y - sube - 1
            if 0 <= yy < T:
                px[x, yy] = ces[3] + (255,)


def canto_superior(semilla=0):
    """Superficie caminable: césped encima de tierra."""
    img = _tile()
    px = img.load()
    _tierra(px, semilla, y0=4)
    _cesped(px, semilla, y=0, alto=4)
    return img


def canto_esquina(semilla=0, izquierda=True):
    """Esquina superior: el césped dobla y baja por el costado.

    Ésta es la pieza clave del autotile. El césped no termina en el canto:
    baja cinco o seis píxeles por la cara lateral. Sin ese doblez el bloque
    parece una losa vista de frente; con él, un trozo de tierra con
    volumen.
    """
    img = canto_superior(semilla)
    px = img.load()
    ces = ramp_rgb(CESPED)
    pie = ramp_rgb(PIEDRA)
    borde = 0 if izquierda else T - 1
    dentro = 1 if izquierda else -1
    for j in range(6 + int(_u(semilla, 7) * 3)):
        for k in range(2):
            x = borde + dentro * k
            y = 4 + j
            if 0 <= x < T and y < T:
                px[x, y] = ces[2 if k == 0 else 1] + (255,)
    # Arista de tierra iluminada u oscurecida según el lado: la luz viene
    # del poniente, o sea de la derecha.
    for y in range(4, T):
        x = borde
        if 0 <= x < T:
            px[x, y] = (pie[3] if not izquierda else pie[0]) + (255,)
    return img


def cara_lateral(semilla=0, izquierda=True):
    """Costado expuesto de un bloque de tierra."""
    img = _tile()
    px = img.load()
    _tierra(px, semilla)
    pie = ramp_rgb(PIEDRA)
    borde = 0 if izquierda else T - 1
    for y in range(T):

        px[borde, y] = (pie[3] if not izquierda else pie[0]) + (255,)
        x2 = 1 if izquierda else T - 2
        px[x2, y] = pie[2 if izquierda else 3] + (255,)
    return img


def relleno(semilla=0):
    """Interior del bloque: nunca se ve entero, pero se ve por los huecos."""
    img = _tile()
    _tierra(img.load(), semilla)
    return img


def adoquin_camino(semilla=0):
    """Superficie del camino: adoquín irregular con desgaste por zonas.

    La variación es de BAJA frecuencia: la mayoría de las baldosas son
    limpias y de vez en cuando aparece una gastada. Poner un detalle
    distinto en cada baldosa produce ruido; la jerarquía —zona limpia,
    pequeña variación, zona limpia, desgaste— es lo que produce textura.
    """
    img = _tile()
    px = img.load()
    pie = ramp_rgb(PIEDRA)
    gastada = _u(semilla, 100) > 0.72
    for fila in range(0, T, 5):
        desp = (fila // 5 % 2) * 4
        for x0 in range(-desp, T, 8):
            for y in range(fila, min(T, fila + 5)):
                for x in range(max(0, x0), min(T, x0 + 8)):
                    junta = (y == fila) or (x == x0)
                    t = 2 if not junta else 1
                    if y == fila + 1 or x == x0 + 1:
                        t = 3
                    px[x, y] = pie[t] + (255,)
    if gastada:
        # Erosión: una mancha de tierra que se come una esquina.
        cx = int(_u(semilla, 101) * T)
        cy = int(_u(semilla, 102) * T)
        r = 3 + int(_u(semilla, 103) * 3)
        for y in range(max(0, cy - r), min(T, cy + r)):
            for x in range(max(0, cx - r), min(T, cx + r)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    px[x, y] = pie[1] + (255,)
    return img
