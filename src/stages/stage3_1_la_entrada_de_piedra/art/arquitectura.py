"""Kit modular de muro gótico: piezas combinables, no edificios cerrados.

Lo que se aprende mirando el tileset de Dark Castle no es cómo dibujar una
piedra — es **cómo se organiza un muro**. Ese pack no tiene un sprite por
edificio: tiene siete u ocho piezas y con ellas construye todo. Y las
piezas no son arbitrarias, son las que usa la arquitectura de verdad:

1. **El muro lleva marco.** Hay un borde de dos píxeles alrededor de cada
   paño. Sin él, un muro es una textura de ladrillos que se extiende sin
   fin; con él, es un volumen con cantos. Es lo que más separa
   «arquitectura» de «relleno».

2. **Hay dos escalas de sillar.** Fino para el cuerpo, basto para el
   arranque. Es una convención real —la fábrica pesada va abajo— y de
   paso resuelve el encuentro con el suelo, que era justo el problema.

3. **Pilastras que dividen en tramos.** Franjas verticales más claras cada
   pocas columnas. Rompen la horizontal de las hiladas y dan ritmo a un
   paño largo sin necesidad de más detalle.

4. **Cornisa que vuela.** Una hilada que sobresale marca dónde termina un
   cuerpo y empieza otro.

5. **El ladrillo no es un rectángulo.** Es un canto redondeado con brillo
   arriba a la izquierda y sombra abajo. A 16 px eso son tres píxeles bien
   puestos, y es la diferencia entre pared y cuadrícula.

Todo eso aquí, en la rampa de piedra y grafito del Stage 3-1.
"""
from __future__ import annotations

import hashlib

from PIL import Image

from palette import CESPED, GRAFITO, PIEDRA, ramp_rgb

T = 16


def _u(semilla: int, i: int) -> float:
    h = hashlib.md5(f"arq{semilla}:{i}".encode()).digest()
    return int.from_bytes(h[:4], "big") / 0xFFFFFFFF


def _tile():
    return Image.new("RGBA", (T, T), (0, 0, 0, 0))


def _sillar(px, x0, y0, w, h, rampa, tono, semilla):
    """Un sillar: canto redondeado, brillo arriba-izquierda, sombra abajo.

    La esquina superior izquierda va un tono por encima y la inferior
    derecha uno por debajo. Con tres píxeles se pasa de cuadrícula a
    fábrica.
    """
    for y in range(y0, min(T, y0 + h)):
        for x in range(x0, min(T, x0 + w)):
            if x < 0 or y < 0:
                continue
            esquina = ((x == x0 or x == x0 + w - 1) and
                       (y == y0 or y == y0 + h - 1))
            if esquina:
                continue                      # canto redondeado
            t = tono
            if y == y0 or x == x0:
                t = min(4, tono + 1)          # luz arriba e izquierda
            elif y == y0 + h - 1 or x == x0 + w - 1:
                t = max(0, tono - 1)          # sombra abajo y derecha
            px[x, y] = rampa[t] + (255,)


def paño(rampa=PIEDRA, tono=2, semilla=0, alto_hilada=4, ancho=8, traba=True):
    """Paño de sillería: la pieza de relleno."""
    img = _tile()
    px = img.load()
    r = ramp_rgb(rampa)
    for y in range(0, T, alto_hilada):
        fila = y // alto_hilada
        # Traba: cada hilada se desplaza media pieza respecto a la anterior.
        # Sin traba las juntas verticales se alinean y el muro se ve como
        # una rejilla, que es exactamente lo que no es un muro.
        desp = (ancho // 2) * (fila % 2) if traba else 0
        for x in range(-desp, T, ancho):
            t = tono
            if _u(semilla, fila * 17 + x) > 0.82:
                t = max(0, tono - 1)          # algún sillar más oscuro
            _sillar(px, x, y, ancho, alto_hilada, r, t, semilla)
    return img


def zocalo(rampa=PIEDRA, semilla=0):
    """Arranque del muro: sillar basto, más grande y más oscuro.

    Resuelve el encuentro con el suelo. Un muro que baja con el mismo
    aparejo hasta la hierba parece cortado con tijera; uno que engorda al
    llegar abajo parece apoyado.
    """
    img = paño(rampa, tono=1, semilla=semilla, alto_hilada=8, ancho=16,
               traba=False)
    px = img.load()
    r = ramp_rgb(rampa)
    for x in range(T):                        # vuelo de 1 px en la coronación
        px[x, 0] = r[3] + (255,)
    return img


def pilastra(rampa=PIEDRA, semilla=0):
    """Franja vertical que divide el paño en tramos."""
    img = paño(rampa, tono=2, semilla=semilla, alto_hilada=6, ancho=16,
               traba=False)
    px = img.load()
    r = ramp_rgb(rampa)
    for y in range(T):
        px[3, y] = r[4] + (255,)              # arista iluminada
        px[4, y] = r[3] + (255,)
        px[11, y] = r[1] + (255,)             # arista en sombra
        px[12, y] = r[0] + (255,)
    return img


def cornisa(rampa=PIEDRA):
    """Hilada en voladizo. Marca el final de un cuerpo."""
    img = _tile()
    px = img.load()
    r = ramp_rgb(rampa)
    for x in range(T):
        for y in range(5, 11):
            t = 4 if y == 5 else (3 if y < 8 else 1)
            px[x, y] = r[t] + (255,)
        # Ménsulas: pequeños apoyos bajo el vuelo, cada cuatro píxeles.
        if x % 4 == 1:
            for y in range(11, 14):
                px[x, y] = r[2] + (255,)
    return img


def almena(rampa=PIEDRA):
    """Coronación almenada: silueta dentada contra el cielo."""
    img = _tile()
    px = img.load()
    r = ramp_rgb(rampa)
    for x in range(T):
        alto = 4 if (x // 4) % 2 == 0 else 10
        for y in range(alto, T):
            t = 3 if y == alto else (2 if x % 8 < 6 else 1)
            px[x, y] = r[t] + (255,)
    return img


def ventana_ojival(rampa=PIEDRA, encendida=True):
    """Ventana apuntada con derrame y alféizar.

    El derrame —la jamba en talud— es lo que da profundidad: sin él, el
    hueco se lee como una pegatina sobre el muro y no como un agujero en
    un muro de medio metro de espesor.
    """
    img = paño(rampa, tono=2, semilla=77, alto_hilada=4, ancho=8)
    px = img.load()
    r = ramp_rgb(rampa)
    luz = (0xff, 0xc2, 0x6a) if encendida else (0x18, 0x12, 0x24)

    for y in range(2, 14):
        # Ancho del hueco: arranca en punta arriba y se abre hacia abajo.
        if y < 6:
            semi = max(0, y - 2)
        else:
            semi = 4
        for x in range(8 - semi, 8 + semi):
            px[x, y] = luz + (255,)
        # Derrame: un píxel de piedra clara a cada lado del hueco.
        if semi:
            for lado in (8 - semi - 1, 8 + semi):
                if 0 <= lado < T:
                    px[lado, y] = r[3 if lado > 8 else 1] + (255,)
    for x in range(3, 13):                    # alféizar
        px[x, 14] = r[4] + (255,)
        px[x, 15] = r[1] + (255,)
    return img


def escombro(rampa=PIEDRA, semilla=0):
    """Cascote acumulado al pie del muro.

    La transición arquitectura → suelo. Un muro que termina en una línea
    recta sobre la hierba se ve recortado; con cascotes y hierba trepando,
    se ve asentado. Es la misma idea que la grava al pie de una roca.
    """
    img = _tile()
    px = img.load()
    r = ramp_rgb(rampa)
    ces = ramp_rgb(CESPED)
    for k in range(7):
        cx = int(_u(semilla, k) * T)
        cy = T - 1 - int(_u(semilla, k + 20) * 5)
        rad = 1 + int(_u(semilla, k + 40) * 2)
        for y in range(cy - rad, cy + rad + 1):
            for x in range(cx - rad, cx + rad + 1):
                if not (0 <= x < T and 0 <= y < T):
                    continue
                if (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad:
                    px[x, y] = r[3 if y == cy - rad else 2] + (255,)
    for k in range(5):                        # hierba entre los cascotes
        bx = int(_u(semilla, k + 60) * T)
        for j in range(2 + int(_u(semilla, k + 80) * 3)):
            if 0 <= bx < T and T - 1 - j >= 0:
                px[bx, T - 1 - j] = ces[2 + (j % 2)] + (255,)
    return img


def arco_ciego(rampa=PIEDRA, semilla=0):
    """Arcada ciega: arco apuntado hundido en el muro, sin hueco.

    Es el recurso más barato para que un paño largo no sea una pared
    plana. No abre nada; sólo hunde la piedra un par de tonos siguiendo un
    trazado apuntado, y el muro pasa a tener ritmo.
    """
    img = paño(rampa, tono=2, semilla=semilla, alto_hilada=4, ancho=8)
    px = img.load()
    r = ramp_rgb(rampa)
    for y in range(3, T):
        semi = max(0, min(6, y - 3))
        for x in range(8 - semi, 8 + semi):
            if 0 <= x < T:
                px[x, y] = r[1] + (255,)
        if semi:
            for lado in (8 - semi - 1, 8 + semi):
                if 0 <= lado < T:
                    px[lado, y] = r[3] + (255,)
    return img
