"""Panorama del cielo: degradado, cordilleras y perfil urbano.

El nivel tenía 24 filas de cielo vacío. Llenarlas colocando sprites sueltos
no funciona —una montaña no es un objeto, es una silueta continua de 1600 px
que ninguna baldosa individual puede describir—, así que aquí se hace al
revés: se **pinta el panorama entero** como imágenes de 1600 px de ancho.

El primer intento las rebanaba en baldosas de 16 × 16 para meterlas en el
TMX. Funcionaba, pero tenía un defecto que lo invalidaba: una capa del mapa
se desplaza a la misma velocidad que el suelo, y una cordillera a treinta
kilómetros que se mueve como el empedrado que pisas no se lee como lejanía,
se lee como un telón pintado. Por eso el panorama sale en **tres bandas
separadas** que el escenario dibuja en `dibujar_fondo` con factores de
parallax distintos: el cielo quieto, las cordilleras lejanas casi quietas y
las cercanas con los campanarios moviéndose el doble. La profundidad no la
da el color, la da la diferencia de velocidad.

Las cordilleras se generan por **desplazamiento del punto medio**: se parte
de una recta, se parte por la mitad, se desplaza ese punto una cantidad
aleatoria, y se repite sobre cada mitad reduciendo el desplazamiento. Es el
algoritmo clásico de terreno fractal, y da perfiles con la
autosemejanza de una montaña real — cimas grandes con estribaciones
pequeñas encima — que una senoidal o un ruido plano no dan.
"""
from __future__ import annotations

import hashlib
import math

from PIL import Image

T = 16
ANCHO = 1600
FILAS_CIELO = 24
ALTO = FILAS_CIELO * T  # 384

# ── Paleta del acto: atardecer violeta, de arriba a abajo ────────────────
# Se conserva el registro de la Entrega I por decisión de Avril. Lo que
# cambia no es el color, es la cantidad de planos que lo usan.
CIELO = [
    (0x14, 0x0c, 0x22),
    (0x1e, 0x11, 0x2e),
    (0x2c, 0x17, 0x3c),
    (0x3e, 0x1d, 0x48),
    (0x52, 0x24, 0x50),
    (0x68, 0x2c, 0x58),
    (0x82, 0x38, 0x5e),
    (0x9e, 0x48, 0x60),
    (0xbe, 0x60, 0x62),
    (0xd8, 0x7c, 0x62),
    (0xee, 0x9c, 0x6a),
]

#: Las cuatro cordilleras, de más lejana a más cercana. Cada una es
#: (color, altura base en px desde arriba, amplitud, semilla, rugosidad).
#: La perspectiva aérea se hace sola: cuanto más lejos, más claro y más
#: cerca del tono del cielo, porque hay más aire de por medio.
# Perspectiva aérea: la cordillera más LEJANA es la más CLARA, no la más
# oscura. Entre ella y el ojo hay más aire, y el aire dispersa el color del
# cielo. El primer intento las pintó todas oscuras y el resultado fue una
# mancha plana en la que no se distinguía un plano de otro.
CORDILLERAS = [
    ((0x86, 0x52, 0x74), 152, 96, 101, 0.48),
    ((0x62, 0x37, 0x5e), 212, 84, 202, 0.50),
    ((0x44, 0x24, 0x48), 252, 72, 303, 0.55),
    ((0x28, 0x15, 0x30), 312, 56, 404, 0.58),
]

BAYER = ((0, 2), (3, 1))


def _azar(semilla: int, i: int) -> float:
    """Aleatorio determinista en [-1, 1). Nunca `random()`: el mismo mapa
    tiene que salir idéntico en cualquier máquina y en cualquier ejecución."""
    h = hashlib.md5(f"{semilla}:{i}".encode()).digest()
    return (int.from_bytes(h[:4], "big") / 0x7FFFFFFF) - 1.0


def perfil_por_punto_medio(ancho: int, base: float, amplitud: float,
                           semilla: int, rugosidad: float) -> list[float]:
    """Devuelve una altura por columna de píxel, por desplazamiento del
    punto medio."""
    n = 1
    while n < ancho:
        n *= 2
    alturas = [base] * (n + 1)
    alturas[0] = base + _azar(semilla, 0) * amplitud
    alturas[n] = base + _azar(semilla, 1) * amplitud

    paso = n
    amp = amplitud
    contador = 2
    while paso > 1:
        medio = paso // 2
        for i in range(medio, n, paso):
            alturas[i] = (alturas[i - medio] + alturas[i + medio]) / 2.0
            alturas[i] += _azar(semilla, contador) * amp
            contador += 1
        paso = medio
        amp *= rugosidad
    return alturas[:ancho]


def _mezcla(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _lienzo(transparente: bool = False) -> Image.Image:
    return Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))


def pintar_cielo() -> Image.Image:
    """Banda 0: sólo el degradado. Quieta, sin parallax."""
    img = _lienzo()
    px = img.load()

    # ── Cielo: degradado vertical con dithering en las fronteras ────────
    # El dithering va SOLO donde dos tonos se tocan, nunca sobre el relleno.
    # Ruido por píxel en un cielo se lee como suciedad, no como aire.
    tramos = len(CIELO) - 1
    for y in range(ALTO):
        t = y / (ALTO - 1)
        pos = t * tramos
        i = min(tramos - 1, int(pos))
        f = pos - i
        c0, c1 = CIELO[i], CIELO[i + 1]
        base = _mezcla(c0, c1, f)
        # Franja de transición: el 22 % central de cada tramo.
        mezclar = 0.39 < f < 0.61
        for x in range(ANCHO):
            if mezclar and BAYER[y % 2][x % 2] < 2:
                col = _mezcla(c0, c1, f + 0.2)
            else:
                col = base
            px[x, y] = col + (255,)
    return img


def pintar_cordilleras(cuales) -> Image.Image:
    """Bandas 1 y 2: cordilleras sobre fondo transparente."""
    img = _lienzo()
    px = img.load()
    for color, base, amp, semilla, rug in cuales:
        perfil = perfil_por_punto_medio(ANCHO, base, amp, semilla, rug)
        for x in range(ANCHO):
            cima = int(perfil[x])
            # ¿Esta ladera mira al sol? El sol se pone a la derecha, así que
            # la cara iluminada es la que desciende hacia la derecha.
            siguiente = int(perfil[min(ANCHO - 1, x + 1)])
            mira_al_sol = siguiente > cima
            for y in range(max(0, cima), ALTO):
                # La ladera se oscurece con la profundidad bajo la cresta,
                # en CUATRO bandas y no en un degradado continuo. Es una
                # decisión de coste, no de estilo: un degradado continuo
                # hace única cada baldosa de la ladera y el rebanado deja
                # de ahorrar nada. Con bandas, todo lo que queda por debajo
                # de la cresta es color plano y colapsa en una baldosa.
                banda = min(3, (y - cima) * 4 // 90)
                col = _mezcla(color, (0x00, 0x00, 0x00), banda * 0.11)
                px[x, y] = col + (255,)
            # Filo de 1 px en la cresta, SOLO en la cara que mira al sol.
            # El primer intento lo puso en toda la cresta y el resultado fue
            # una línea continua de lado a lado: se leía como un trazo de
            # rotulador, no como luz rasante.
            if 0 <= cima < ALTO and mira_al_sol:
                px[x, cima] = _mezcla(color, (0xff, 0xc0, 0x88), 0.30) + (255,)

    return img


def _pintar_torres(px) -> None:
    """Campanarios góticos contra el cielo.

    Góticos quiere decir tres cosas concretas y no una silueta genérica:
    **estrechos** —más altos que anchos, con proporción de al menos 1 a 4—,
    rematados en **aguja** y no en tejado, y con **ventanas de lanceta**:
    huecos de 3 px de ancho por 9 de alto, no ventanales cuadrados. El
    primer intento salió con torres anchas de sombrero triangular y
    ventanas grandes: eran rascacielos, no campanarios.
    """
    muro = (0x2a, 0x1c, 0x38)
    canto = (0x3e, 0x2a, 0x4c)
    sombra = (0x1a, 0x11, 0x24)
    luz = (0xff, 0xc2, 0x6a)

    # (x, ancho, y del alero). Agrupadas en tres macizos —la sede tiene
    # cuerpos, no torres sueltas— y ausentes en el centro, que es donde
    # el jugador cruza el pozo y no conviene competirle la atención.
    torres = [
        (96, 26, 168), (130, 34, 132), (172, 22, 190), (200, 30, 152),
        (1016, 24, 176), (1046, 32, 140), (1086, 22, 196),
        (1392, 30, 148), (1428, 22, 184), (1456, 34, 160),
    ]
    for tx, tw, ty in torres:
        for x in range(tx, min(ANCHO, tx + tw)):
            # Contrafuerte: el canto izquierdo recibe luz, el derecho no.
            if x == tx:
                col = canto
            elif x >= tx + tw - 2:
                col = sombra
            else:
                col = muro
            for y in range(ty, ALTO):
                px[x, y] = col + (255,)

        # Aguja: alta y afilada, 1,7 veces el ancho de la torre.
        alto_aguja = int(tw * 1.7)
        for j in range(alto_aguja):
            # OJO: `j` cuenta desde ARRIBA, así que el ancho tiene que
            # CRECER con j. La primera versión usaba (1 - j/alto) y salían
            # triángulos invertidos, anchos arriba y en punta abajo: unos
            # embudos colgados sobre las torres.
            ancho = max(1, int(tw * (j / alto_aguja) ** 0.80))
            x0 = tx + (tw - ancho) // 2
            y = ty - alto_aguja + j
            if not (0 <= y < ALTO):
                continue
            for x in range(x0, min(ANCHO, x0 + ancho)):
                px[x, y] = (canto if x == x0 else muro) + (255,)

        # Cornisa de 2 px en el arranque de la aguja.
        for x in range(max(0, tx - 2), min(ANCHO, tx + tw + 2)):
            for y in (ty, ty + 1):
                if 0 <= y < ALTO:
                    px[x, y] = canto + (255,)

        # Lancetas: estrechas, en pares, encendidas de forma irregular.
        for fila, wy in enumerate(range(ty + 10, ALTO - 12, 22)):
            huecos = max(1, (tw - 8) // 10)
            for k in range(huecos):
                wx = tx + 4 + k * 10
                if wx + 3 > tx + tw - 3:
                    break
                encendida = _azar(tx + fila * 7, k) > -0.2
                col = luz if encendida else (0x14, 0x0e, 0x1e)
                for x in range(wx, min(ANCHO, wx + 3)):
                    for y in range(wy + (0 if x != wx + 1 else -2), wy + 9):
                        if 0 <= y < ALTO:
                            px[x, y] = col + (255,)
                if encendida:
                    for x in range(wx - 2, wx + 5):
                        for y in range(wy - 3, wy + 11):
                            if 0 <= x < ANCHO and 0 <= y < ALTO and \
                                    not (wx <= x < wx + 3 and wy - 2 <= y < wy + 9):
                                px[x, y] = _mezcla(px[x, y][:3], luz, 0.13) + (255,)


def construir() -> dict[str, Image.Image]:
    """Las tres bandas, listas para guardarse como PNG."""
    cerca = pintar_cordilleras(CORDILLERAS[2:])
    _pintar_torres(cerca.load())
    return {
        "pan_cielo": pintar_cielo(),
        "pan_lejos": pintar_cordilleras(CORDILLERAS[:2]),
        "pan_cerca": cerca,
    }


if __name__ == "__main__":
    import os
    destino = "/tmp/build5/student_assets/backgrounds"
    os.makedirs(destino, exist_ok=True)
    for nombre, im in construir().items():
        im.save(f"{destino}/{nombre}.png")
        print("escrito", nombre, im.size)
