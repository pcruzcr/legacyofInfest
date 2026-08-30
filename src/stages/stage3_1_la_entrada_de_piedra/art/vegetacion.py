"""Sistemas de vegetación y roca: conjuntos, no objetos sueltos.

El defecto que esto viene a arreglar es concreto: los árboles parecían
apoyados *encima* del suelo y las piedras, objetos independientes flotando
cerca. Mirando cómo lo resuelven los packs de referencia, el truco no está
en dibujar mejor el árbol — está en que **nada aparece solo**.

En Pixel Woods, ningún árbol es una silueta plantada en el césped: el
tronco se ensancha abajo y se abre en tres o cuatro raíces que se van de
lado, hay una sombra de contacto oscura debajo, matas de hierba pegadas al
arranque y dos o tres piedrecitas alrededor. Y ninguna roca va suelta:
siempre es una grande con una mediana y varias pequeñas, con grava en la
base y hierba en la junta con el suelo. Esa cadena de tamaños decrecientes
—grande, mediano, chico, grava— es lo que hace que la piedra parezca salir
del terreno en vez de estar posada sobre él.

Así que aquí no se generan árboles ni piedras: se generan **bosquecillos**
y **formaciones**, cada uno con su zona de integración completa dibujada de
una vez:

    árbol  → raíces → sombra → hierba → piedrecitas → suelo
    roca   → rocas secundarias → grava → sombra → vegetación → suelo

Todo en la paleta violeta/verde del nivel y en baldosas de 16 px.
"""
from __future__ import annotations

import hashlib

from PIL import Image

from palette import CESPED, FLOR, FOLLAJE, PIEDRA, TRONCO, ramp_rgb

T = 16


def _azar(semilla: int, i: int) -> float:
    """Determinista en [-1, 1). Mismo mapa en cualquier máquina."""
    h = hashlib.md5(f"veg{semilla}:{i}".encode()).digest()
    return (int.from_bytes(h[:4], "big") / 0x7FFFFFFF) - 1.0


def _u(semilla: int, i: int) -> float:
    """Determinista en [0, 1)."""
    return (_azar(semilla, i) + 1.0) * 0.5


def _disco(px, W, H, cx, cy, r, color):
    r2 = r * r
    for y in range(max(0, int(cy - r)), min(H, int(cy + r) + 1)):
        for x in range(max(0, int(cx - r)), min(W, int(cx + r) + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                px[x, y] = color


def _sombra_de_contacto(px, W, H, cx, base_y, radio):
    """Elipse oscura y aplastada bajo el objeto.

    Es la pieza más barata y la que más trabajo hace: sin ella, cualquier
    cosa parece flotar un par de píxeles por encima del césped. Va en el
    tono más oscuro del césped —no en negro— para que se lea como sombra
    proyectada sobre hierba y no como un agujero.
    """
    ces = ramp_rgb(CESPED)
    for y in range(max(0, base_y - 3), min(H, base_y + 3)):
        for x in range(max(0, int(cx - radio)), min(W, int(cx + radio) + 1)):
            dx = (x - cx) / radio
            dy = (y - base_y) / 3.0
            if dx * dx + dy * dy <= 1.0:
                borde = dx * dx + dy * dy > 0.55
                px[x, y] = (ces[1] if borde else ces[0]) + (255,)


def _mata_de_hierba(px, W, H, x0, base_y, semilla, altura=6):
    """Tres a seis briznas de alturas distintas saliendo del mismo punto."""
    ces = ramp_rgb(CESPED)
    n = 3 + int(_u(semilla, 0) * 4)
    for i in range(n):
        bx = x0 + i - n // 2
        h = int(altura * (0.45 + 0.55 * _u(semilla, i + 1)))
        incl = 1 if _azar(semilla, i + 40) > 0 else -1
        for j in range(h):
            xx = bx + (incl if j > h * 0.6 else 0)
            yy = base_y - j
            if 0 <= xx < W and 0 <= yy < H:
                px[xx, yy] = ces[2 + (j * 2 // max(1, h))] + (255,)


def _piedrecita(px, W, H, cx, base_y, semilla, tam=3):
    """Canto rodado de 2-4 px, con su micro-sombra."""
    pie = ramp_rgb(PIEDRA)
    r = tam + int(_u(semilla, 0) * 2)
    for y in range(base_y - r, base_y + 1):
        for x in range(cx - r, cx + r + 1):
            if not (0 <= x < W and 0 <= y < H):
                continue
            dx = (x - cx) / r
            dy = (y - base_y) / max(1.0, r * 0.9)
            if dx * dx + dy * dy <= 1.0:
                # Luz desde la derecha: el lado derecho un tono más claro.
                t = 3 if (x - cx) > r * 0.2 else 2
                if y >= base_y - 1:
                    t = 1
                px[x, y] = pie[t] + (255,)


def _arbol(px, W, H, base_x, base_y, alto, ancho, semilla, con_flores):
    """Un árbol con raíces, no un tronco clavado en el suelo.

    El tronco se ensancha hacia abajo y en los últimos píxeles se abre en
    tres o cuatro raíces que se van de lado y se hunden. Eso es lo único
    que separa «árbol» de «poste con hojas»: en la naturaleza el tronco
    nunca corta en seco contra el suelo, se ensancha y se ramifica.
    """
    tron = ramp_rgb(TRONCO)
    foll = ramp_rgb(FOLLAJE)
    flor = ramp_rgb(FLOR)

    # El tronco se lleva el 58 % de la altura, no el 52 %. Con el reparto
    # anterior la copa bajaba tanto que tapaba el arranque y las raíces —
    # que son justo lo que se quería enseñar— quedaban debajo del follaje.
    tronco_alto = int(alto * 0.58)
    grosor_arriba = max(3, ancho // 8)
    # Cinco píxeles de ensanche, no tres. El ensanche del tronco hacia la
    # base es la mitad del efecto «raíz»: si es sutil, el tronco sigue
    # leyéndose como un poste de grosor constante.
    grosor_abajo = grosor_arriba + 5

    # ── Tronco, ensanchando hacia abajo ─────────────────────────────────
    for j in range(tronco_alto):
        t = j / max(1, tronco_alto - 1)          # 0 arriba, 1 abajo
        g = grosor_arriba + (grosor_abajo - grosor_arriba) * t
        # Ligera curvatura: un tronco perfectamente recto delata el script.
        desv = int(_azar(semilla, 900) * 2 * (1.0 - t))
        cx = base_x + desv
        y = base_y - tronco_alto + j
        for x in range(int(cx - g / 2), int(cx + g / 2) + 1):
            if not (0 <= x < W and 0 <= y < H):
                continue
            # Luz desde la derecha, sombra en el borde izquierdo.
            lado = (x - cx) / max(1.0, g / 2)
            # El tronco se queda en los tres tonos oscuros. Los dos
            # claros de la rampa se reservan para las raíces y el canto
            # iluminado: un tronco marrón claro en un atardecer violeta
            # canta tanto como una copa verde brillante.
            t_col = 2 if lado > 0.35 else (0 if lado < -0.35 else 1)
            px[x, y] = tron[t_col] + (255,)

    # ── Raíces: 3-4 patas que se abren en los últimos píxeles ───────────
    # Arrancan ALTO —a un tercio del ensanche— y bajan describiendo una
    # curva hasta hundirse en la hierba. Arrancando al ras del suelo
    # quedaban escondidas bajo las matas y no se veía ninguna.
    n_raices = 3 + (1 if _azar(semilla, 12) > 0 else 0)
    for k in range(n_raices):
        dirn = -1 if k % 2 == 0 else 1
        largo = 5 + int(_u(semilla, 30 + k) * 6)
        alt_ini = 5 + int(_u(semilla, 40 + k) * 4)
        for paso in range(largo):
            t = paso / max(1, largo - 1)
            xx = base_x + int(dirn * (grosor_abajo * 0.35 + paso))
            # Curva cóncava: baja despacio al principio y se desploma al
            # final, que es como se dobla una raíz al buscar el suelo.
            yy = base_y - int(alt_ini * (1.0 - t) ** 1.7)
            grosor = 3 if t < 0.4 else (2 if t < 0.75 else 1)
            for e in range(grosor):
                if 0 <= xx < W and 0 <= yy + e < H:
                    px[xx, yy + e] = tron[3 if dirn > 0 else 1] + (255,)

    # ── Copa: racimos superpuestos, nunca un círculo ────────────────────
    copa_cy = base_y - alto + int(alto * 0.28)
    n_racimos = 5 + int(_u(semilla, 3) * 4)
    racimos = []
    for i in range(n_racimos):
        rx = base_x + _azar(semilla, i * 5 + 1) * ancho * 0.28
        ry = copa_cy + _azar(semilla, i * 5 + 2) * alto * 0.13
        rr = ancho * (0.13 + 0.10 * _u(semilla, i * 5 + 3))
        racimos.append((rx, ry, rr))

    # La distribución de tonos baja dos escalones respecto a la primera
    # versión. Antes la silueta iba en el tono 2 y los volúmenes en el 3 y
    # el 4, y el resultado era un bosque verde normal: la vegetación era
    # la fuente principal de saturación de la pantalla, compitiendo con
    # las farolas y con el arco.
    #
    # Ahora la masa va en el tono 1 —verde petróleo, casi negro—, el
    # volumen en el 2, y el 3 sólo como reflejo pequeño del cielo. El 4 no
    # se usa en las copas: queda reservado para casos excepcionales.
    # La copa tiene que funcionar como silueta oscura contra el cielo
    # violeta, no como una mancha verde.
    for rx, ry, rr in racimos:
        _disco(px, W, H, rx, ry, rr, foll[1] + (255,))
    for rx, ry, rr in racimos:
        _disco(px, W, H, rx + rr * 0.24, ry - rr * 0.26, rr * 0.60,
               foll[2] + (255,))
    # Reflejo del cielo: SÓLO en las hojas de arriba y sólo en la mitad de
    # los racimos. Un contorno claro alrededor de toda la copa se lee como
    # borde dibujado, no como luz.
    for rx, ry, rr in racimos[::2]:
        _disco(px, W, H, rx + rr * 0.34, ry - rr * 0.46, rr * 0.24,
               foll[3] + (255,))
    # Sombra propia bajo la copa. Va en el tono 1 y MUY pequeña: el primer
    # intento usaba discos de 0,34 del radio bajo cada racimo y en pantalla
    # eran agujeros negros dentro del follaje. Una sombra propia sugiere el
    # hueco entre masas de hoja; no dibuja el hueco.
    for rx, ry, rr in racimos[::2]:
        _disco(px, W, H, rx - rr * 0.30, ry + rr * 0.52, rr * 0.20,
               foll[0] + (255,))

    # Hojas sueltas fuera del contorno: rompen el borde y dan aire.
    for i in range(6):
        hx = int(base_x + _azar(semilla, 200 + i) * ancho * 0.62)
        hy = int(copa_cy + _azar(semilla, 220 + i) * alto * 0.30)
        if 0 <= hx < W and 0 <= hy < H:
            px[hx, hy] = foll[2] + (255,)

    if con_flores:
        for i in range(9):
            fx = int(base_x + _azar(semilla, 300 + i) * ancho * 0.46)
            fy = int(copa_cy + _azar(semilla, 320 + i) * alto * 0.24)
            if 0 <= fx < W and 0 <= fy < H and px[fx, fy][3]:
                px[fx, fy] = flor[3 + (i % 2)] + (255,)


def bosquecillo(w_tiles, h_tiles, semilla, n_arboles=3, flores=False):
    """Un GRUPO de árboles con su zona de integración con el suelo.

    No devuelve un árbol: devuelve un trozo de bosque. Los árboles se
    solapan, tienen alturas distintas y la base entera lleva sombra,
    hierba y piedrecitas. Colocar tres de estos en el mapa da un bosque;
    colocar treinta árboles sueltos da una valla.
    """
    W, H = w_tiles * T, h_tiles * T
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    base_y = H - 2

    # Posiciones: repartidas pero no equidistantes, y ordenadas de atrás
    # hacia delante para que los de delante tapen a los de detrás.
    arboles = []
    for i in range(n_arboles):
        frac = (i + 0.5) / n_arboles + _azar(semilla, i * 7) * 0.16
        bx = int(W * min(0.92, max(0.08, frac)))
        # El de en medio es el mayor: un grupo con un ejemplar dominante se
        # lee como grupo; tres iguales se leen como repetición.
        dom = 1.0 - abs((i + 0.5) / n_arboles - 0.5) * 0.9
        alto = int(H * (0.52 + 0.34 * dom) * (0.90 + 0.16 * _u(semilla, 50 + i)))
        # Tope para que la copa no se recorte contra el borde de arriba.
        alto = min(alto, H - 10)
        # El ancho se limita por el sitio que le toca en el grupo, no por su
        # propia altura. Sin este tope, tres árboles de copa ancha en una
        # lámina de siete baldosas se desbordaban por los lados y se
        # recortaban contra el borde del sprite.
        ancho = int(min(W / n_arboles * 1.55, alto * 0.80)
                    * (0.80 + 0.28 * _u(semilla, 70 + i)))
        arboles.append((bx, alto, ancho, i))
    arboles.sort(key=lambda a: a[1], reverse=True)   # altos primero (detrás)

    # 1. Sombras de contacto, todas antes que los troncos.
    for bx, alto, ancho, i in arboles:
        _sombra_de_contacto(px, W, H, bx, base_y, max(6, ancho // 3))

    # 2. Los árboles.
    for bx, alto, ancho, i in arboles:
        _arbol(px, W, H, bx, base_y, min(alto, H - 4), ancho,
               semilla + i * 131, flores)

    # 3. Integración con el suelo: piedrecitas primero (quedan detrás de la
    #    hierba), después las matas. El orden importa — hierba delante de
    #    piedra es lo que hace que la piedra parezca medio enterrada.
    for k in range(3 + int(_u(semilla, 91) * 4)):
        cx = int(W * _u(semilla, 100 + k))
        _piedrecita(px, W, H, cx, base_y + 1, semilla + k * 17,
                    2 + int(_u(semilla, 120 + k) * 2))
    for k in range(5 + int(_u(semilla, 92) * 5)):
        cx = int(W * _u(semilla, 140 + k))
        _mata_de_hierba(px, W, H, cx, base_y + 2, semilla + k * 23,
                        5 + int(_u(semilla, 160 + k) * 4))
    # Matas pegadas al arranque de cada tronco: es donde de verdad crece.
    # Matas al pie de cada tronco, pero APARTADAS del eje: pegadas al
    # centro tapaban las raíces, que son lo que se quiere enseñar. Van a
    # partir de 6 px, justo donde la raíz ya se ha hundido.
    for bx, alto, ancho, i in arboles:
        for d in (-9, -6, 6, 9):
            _mata_de_hierba(px, W, H, bx + d, base_y + 2,
                            semilla + i * 61 + d, 7)
    return img


def formacion_rocosa(w_tiles, h_tiles, semilla, con_musgo=True):
    """Una FORMACIÓN: roca grande, secundarias, grava, sombra y vegetación.

    Una piedra sola es un objeto; una piedra grande con dos medianas y un
    reguero de grava alrededor es terreno. La cadena de tamaños
    decrecientes es lo que da la transición — sin la grava, el canto de la
    roca choca contra el césped y se ve el recorte.
    """
    W, H = w_tiles * T, h_tiles * T
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    pie = ramp_rgb(PIEDRA)
    base_y = H - 3

    def bloque_de_roca(cx, cy, rx, ry, sem):
        """Roca de silueta facetada, no una elipse lisa."""
        for y in range(max(0, int(cy - ry)), min(H, int(cy + ry) + 1)):
            for x in range(max(0, int(cx - rx)), min(W, int(cx + rx) + 1)):
                dx = (x - cx) / rx
                dy = (y - cy) / ry
                # El exponente 2,6 en vez de 2 aplana los lados: da una
                # silueta de canto rodado, entre elipse y hexágono.
                if abs(dx) ** 2.6 + abs(dy) ** 2.6 > 1.0:
                    continue
                # Facetas: tres bandas de tono según la altura relativa,
                # con la cara superior derecha iluminada.
                marca = (-dy) * 0.72 + dx * 0.28
                t = 1 if marca < -0.25 else (2 if marca < 0.35 else 3)
                if marca > 0.72:
                    t = 4
                px[x, y] = pie[t] + (255,)
        # Filo iluminado en la arista superior derecha.
        for x in range(int(cx), min(W, int(cx + rx))):
            for y in range(max(0, int(cy - ry)), min(H, int(cy + ry))):
                if px[x, y][3] and not (y > 0 and px[x, y - 1][3]):
                    px[x, y] = pie[4] + (255,)
                    break

    # 1. Sombra de todo el conjunto, antes que nada.
    _sombra_de_contacto(px, W, H, W * 0.5, base_y + 2, W * 0.46)

    # 2. Roca principal, descentrada.
    px_cx = W * (0.36 + 0.22 * _u(semilla, 1))
    rx = W * (0.26 + 0.08 * _u(semilla, 2))
    ry = H * (0.34 + 0.12 * _u(semilla, 3))
    bloque_de_roca(px_cx, base_y - ry * 0.85, rx, ry, semilla)

    # 3. Secundarias: dos, a distinto lado y bastante más pequeñas.
    for k in range(2):
        lado = -1 if k == 0 else 1
        sx = px_cx + lado * rx * (0.95 + 0.35 * _u(semilla, 10 + k))
        srx = rx * (0.40 + 0.18 * _u(semilla, 20 + k))
        sry = ry * (0.44 + 0.20 * _u(semilla, 30 + k))
        bloque_de_roca(sx, base_y - sry * 0.8, srx, sry, semilla + 7 + k)

    # 4. Grava: el reguero que funde la formación con el suelo.
    for k in range(6 + int(_u(semilla, 40) * 5)):
        gx = int(W * _u(semilla, 50 + k))
        _piedrecita(px, W, H, gx, base_y + 2, semilla + 300 + k,
                    1 + int(_u(semilla, 70 + k) * 2))

    # 5. Vegetación en la junta: hierba delante de la piedra, y musgo
    #    encima. La hierba por delante es lo que entierra el canto.
    for k in range(4 + int(_u(semilla, 80) * 4)):
        gx = int(W * (0.06 + 0.88 * _u(semilla, 90 + k)))
        _mata_de_hierba(px, W, H, gx, base_y + 3, semilla + 400 + k, 6)

    if con_musgo:
        ces = ramp_rgb(CESPED)
        for x in range(W):
            for y in range(H):
                if not px[x, y][3]:
                    continue
                arriba_libre = y == 0 or not px[x, y - 1][3]
                if arriba_libre and _u(semilla, x * 3 + y) > 0.45:
                    px[x, y] = ces[2 + (x % 2)] + (255,)
                    if y + 1 < H and px[x, y + 1][3] and _u(semilla, x * 7) > 0.6:
                        px[x, y + 1] = ces[1] + (255,)
    return img


def mata_de_flores(semilla, densidad=1.0):
    """Mata de flores: tallos con tres a cinco corolas pequeñas.

    Del Idylwild's Foliage Pack se saca una regla concreta: alli no hay
    flores sueltas. Cada una es una MATA — dos o tres tallos verdes que
    salen del mismo punto, con corolas de dos o tres pixeles arriba. Y el
    color claro aparece en unos pocos pixeles, nunca en masa: sus arbustos
    de bayas son el mismo arbusto verde con seis puntos de color encima.

    Eso es exactamente lo que necesita este nivel: la paleta es violeta
    fria y el rosa claro tiene que funcionar como acento, no como color
    dominante. Aqui el tono mas claro de la rampa sale en el 20 % de las
    corolas y el resto se queda en los dos medios.
    """
    img = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    px = img.load()
    ces = ramp_rgb(CESPED)
    flo = ramp_rgb(FLOR)
    base_y = T - 1

    n = max(2, int((2 + int(_u(semilla, 0) * 3)) * densidad))
    for i in range(n):
        bx = 3 + int(_u(semilla, i * 4 + 1) * (T - 6))
        alto = 4 + int(_u(semilla, i * 4 + 2) * 5)
        incl = 1 if _azar(semilla, i * 4 + 3) > 0 else -1
        # Tallo: recto abajo y curvado en el ultimo tercio, como una planta
        # que se inclina por su propio peso.
        for j in range(alto):
            xx = bx + (incl if j > alto * 0.65 else 0)
            yy = base_y - j
            if 0 <= xx < T and 0 <= yy < T:
                px[xx, yy] = ces[1 + (j % 2)] + (255,)
        # Corola: dos o tres pixeles. El tono mas claro es raro.
        cx, cy = bx + incl, base_y - alto
        claro = _u(semilla, i * 4 + 9) > 0.80
        tono = 4 if claro else (3 if _u(semilla, i * 4 + 10) > 0.45 else 2)
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1)):
            xx, yy = cx + dx, cy + dy
            if 0 <= xx < T and 0 <= yy < T:
                px[xx, yy] = flo[tono if (dx or dy) == 0 else max(1, tono - 1)] + (255,)
    return img


def bayas_sobre(img, semilla, cuantas=7):
    """Salpica puntos de color sobre un sprite verde ya dibujado.

    El truco de los arbustos de baya del pack: no es otro sprite, es el
    mismo con seis puntos encima. Cuesta seis pixeles y multiplica la
    variedad aparente del follaje sin tocar la silueta.
    """
    out = img.copy()
    px = out.load()
    flo = ramp_rgb(FLOR)
    W, H = out.size
    puestas = 0
    intentos = 0
    while puestas < cuantas and intentos < cuantas * 12:
        intentos += 1
        x = int(_u(semilla, intentos * 2) * W)
        y = int(_u(semilla, intentos * 2 + 1) * H)
        if 0 <= x < W and 0 <= y < H and px[x, y][3] > 200:
            px[x, y] = flo[3 if _u(semilla, intentos) > 0.7 else 2] + (255,)
            puestas += 1
    return out
