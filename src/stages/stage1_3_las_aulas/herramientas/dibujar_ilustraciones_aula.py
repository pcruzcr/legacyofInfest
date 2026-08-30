"""Dibuja 3 ilustraciones pixel-art del aula (lejos/medio/cerca).

Reemplazan las 3 fotografias reales que se usaban antes como entrada de
generar_fondos.py. El profesor senalo que un fondo fotografico no encaja con
la estetica pixel art del motor (docs/20_ASSET_BIBLE.md: paleta limitada, sin
antialiasing). El pipeline de perspectiva atmosferica (HSV) de
generar_fondos.py -la entrega calificada de la Unidad V- no cambia: solo
cambia de donde saca la imagen de entrada.

Paleta "aula moderna" pedida para la Practica II: blanco/hueso (#FFFFFF /
#F4F4F4), gris carbon / concreto (#3A3A3A / #7E888C) y azul electrico como
acento tecnologico (#0055A5) — la misma que usa crear_tileset.py.

AUD-Yariel-02 -- por que todo lleva difuminado desde aqui, no solo el "far"
--------------------------------------------------------------------------
La primera version dibujaba ventanas y casilleros con bordes duros (marco
solido, esquinas rectas) en las 3 capas. Jugando se veian a traves de los
huecos del primer plano y, como el fondo se mueve a otra velocidad que el
terreno (parallax: far 0.15x, mid 0.35x, near 0.70x contra el 1x del
jugador), un rectangulo con bordes nitidos se lee como "algo" que se mueve
por su cuenta -- se confundio con un objeto nuevo, no con fondo. La regla
del propio README (Unidad V, S5.2): "el fondo tiene que leerse como fondo y
no competir con el pixel art del primer plano". Aqui se aplica literal:
`ImageFilter.GaussianBlur` sobre cada ilustracion antes de guardarla, mas
fuerte cuanto mas lejos, para que nada tenga un borde recto que se pueda
confundir con un casillero, una puerta o un personaje.

Uso:
    python dibujar_ilustraciones_aula.py <carpeta_destino>
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

random.seed(7)

W, H = 640, 480

BLANCO = (244, 244, 244)
BLANCO2 = (255, 255, 255)
CARBON = (58, 58, 58)
CONCRETO = (126, 136, 140)
AZUL = (0, 85, 165)
AZUL_CLARO = (150, 195, 235)
NEGRO_SUAVE = (40, 40, 44)


def gradiente_vertical(draw, top, bottom, w, h, y0=0):
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y0 + y), (w, y0 + y)], fill=(r, g, b))


def particulas(draw, n, y_rango, color, w=W):
    """Motas de polvo sueltas en la luz — el mismo recurso que usan los
    fondos genericos zone1/zone2 del motor para dar ambiente sin ser
    fotograficos."""
    for _ in range(n):
        x = random.randint(0, w)
        y = random.randint(*y_rango)
        r = random.choice([1, 1, 2])
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


def franja_de_luz(draw, y_centro, alto, color, w=W):
    """Una banda horizontal muy tenue -- el "recuerdo" de una fila de
    ventanas, sin dibujar ninguna ventana de verdad. Nunca se confunde con
    un objeto porque no tiene bordes: es solo un cambio de tono."""
    draw.rectangle([0, y_centro - alto // 2, w, y_centro + alto // 2], fill=color)


def dibujar_lejos() -> Image.Image:
    """Fondo lejano: solo gradiente + una franja de luz + polvo. Nada con
    forma reconocible -- es la capa que menos se debe notar."""
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    gradiente_vertical(d, BLANCO2, BLANCO, W, H)
    franja_de_luz(d, 130, 90, (208, 222, 236))
    d.rectangle([0, H - 40, W, H], fill=(214, 216, 217))
    particulas(d, 40, (20, H - 60), (225, 235, 245))
    return img.filter(ImageFilter.GaussianBlur(8))


def dibujar_medio() -> Image.Image:
    """Fondo medio: gradiente + dos franjas de luz a distinta altura + polvo.
    Un poco mas de estructura que "lejos", pero sigue sin haber ninguna
    forma con bordes rectos que se pueda confundir con un objeto real."""
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    gradiente_vertical(d, BLANCO2, (232, 233, 234), W, H)
    franja_de_luz(d, 100, 70, (200, 218, 235))
    franja_de_luz(d, 260, 50, (215, 227, 238))
    d.rectangle([0, H - 50, W, H], fill=(210, 212, 214))
    particulas(d, 55, (30, H - 70), (200, 220, 245))
    return img.filter(ImageFilter.GaussianBlur(6))


def dibujar_cerca() -> Image.Image:
    """Fondo cercano: la mas visible de las tres. Un unico bloque de luz
    (que sugiere un ventanal sin dibujarlo con marco) + polvo mas denso, con
    el mismo cuidado de no usar bordes duros ni siluetas grandes."""
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    gradiente_vertical(d, (255, 255, 255), (236, 237, 238), W, H)
    franja_de_luz(d, 140, 180, (206, 224, 242))
    d.rectangle([0, H - 60, W, H], fill=(206, 208, 210))
    particulas(d, 70, (10, H - 90), (215, 230, 250))
    return img.filter(ImageFilter.GaussianBlur(5))


if __name__ == "__main__":
    destino = Path(sys.argv[1])
    destino.mkdir(parents=True, exist_ok=True)
    dibujar_lejos().save(destino / "aula_lejos.png")
    dibujar_medio().save(destino / "aula_medio.png")
    dibujar_cerca().save(destino / "aula_cerca.png")
    print("3 ilustraciones creadas en", destino)
