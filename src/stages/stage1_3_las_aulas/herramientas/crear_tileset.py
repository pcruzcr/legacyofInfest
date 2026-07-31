"""Dibuja un tileset propio de aula: 16x16 px, rejilla 8x8 = 64 tiles.

Cada tile se define como 16 lineas de 16 caracteres. Cada caracter es un
color de la paleta. Asi el arte queda legible y editable en el codigo.
"""
import sys

from PIL import Image

TILE, COLS, FILAS = 16, 8, 8

PALETA = {
    ".": (0, 0, 0, 0),          # transparente
    "b": (175, 155, 115, 255),  # beige claro (piso)
    "B": (160, 140, 100, 255),  # beige (pared)
    "s": (140, 122, 88, 255),   # beige sombra
    "m": (140, 105, 70, 255),   # madera media
    "M": (108, 82, 52, 255),    # madera oscura
    "d": (78, 58, 36, 255),     # madera muy oscura / contorno
    "z": (45, 65, 110, 255),    # azul pizarra
    "Z": (70, 95, 150, 255),    # azul claro (vidrio)
    "t": (230, 225, 210, 255),  # tiza / blanco
    "r": (161, 71, 62, 255),    # rojo casillero
    "R": (120, 52, 46, 255),    # rojo oscuro
    "g": (120, 120, 130, 255),  # gris metal
    "k": (60, 45, 30, 255),     # negro suave
    # Colores tomados de las fotos del aula real
    "w": (238, 238, 232, 255),  # blanco de la pizarra
    "W": (208, 208, 200, 255),  # sombra del blanco
    "a": (224, 186, 62, 255),   # amarillo de la pared de acento
    "A": (188, 152, 44, 255),   # amarillo en sombra
    "n": (38, 38, 42, 255),     # negro de las sillas
    "c": (196, 120, 60, 255),   # marcador naranja
    "e": (70, 130, 90, 255),    # marcador verde
}

VACIO = ["." * 16] * 16


def art(*filas):
    assert len(filas) == 16, f"se esperaban 16 filas, hay {len(filas)}"
    for f in filas:
        assert len(f) == 16, f"fila de {len(f)} caracteres: {f!r}"
    return list(filas)


PISO = art(
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbsbbbbbbbs",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "ssssssssssssssss",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "sbbbbbbbsbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "ssssssssssssssss",
)

PISO_BORDE = art(
    "dddddddddddddddd",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbsbbbbbbbs",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "ssssssssssssssss",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "sbbbbbbbsbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbbbbbbbbbbb",
    "ssssssssssssssss",
)

PARED = art(*(["BBBBBBBBBBBBBBBB"] * 16))

PARED_ZOCALO = art(
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "ssssssssssssssss",
    "MMMMMMMMMMMMMMMM",
    "MMMMMMMMMMMMMMMM",
    "dddddddddddddddd",
    "dddddddddddddddd",
)

# Plataforma pisable.  Lleva un filo claro arriba para que se lea "se puede
# pisar aqui", y el cuerpo en madera oscura para diferenciarla del mobiliario.
ESTANTE = art(
    "tttttttttttttttt",
    "mmmmmmmmmmmmmmmm",
    "mmmmmmmmmmmmmmmm",
    "MMMMMMMMMMMMMMMM",
    "dddddddddddddddd",
    "d..d........d..d",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
)

# --- Mesa de 2 tiles de ancho ---
# Mesas plegables color crema con patas de metal, como las del aula real.
MESA_IZQ = art(
    "................",
    "................",
    "................",
    "................",
    "....wwwwwwwwwwww",
    "....wwwwwwwwwwww",
    "....WWWWWWWWWWWW",
    "....kkkkkkkkkkkk",
    "....gg..........",
    "....gg..........",
    "....gg..........",
    "....gg..........",
    "....gg..........",
    "....gg..........",
    "....gg..........",
    "....gg..........",
)

MESA_DER = art(
    "................",
    "................",
    "................",
    "................",
    "wwwwwwwwww......",
    "wwwwwwwwww......",
    "WWWWWWWWWW......",
    "kkkkkkkkkk......",
    "........gg......",
    "........gg......",
    "........gg......",
    "........gg......",
    "........gg......",
    "........gg......",
    "........gg......",
    "........gg......",
)

# --- Sillas (vista lateral) ---
# Sillas NEGRAS con patas de metal, como las del aula real.
SILLA_DER = art(  # respaldo a la izquierda, mira a la derecha
    "................",
    "...nn...........",
    "...nn...........",
    "...nn...........",
    "...nn...........",
    "...nn...........",
    "...nn...........",
    "...nn...........",
    "...nnnnnnnnnn...",
    "...nnnnnnnnnn...",
    "...kkkkkkkkkk...",
    "...gg......gg...",
    "...gg......gg...",
    "...gg......gg...",
    "...gg......gg...",
    "...gg......gg...",
)

SILLA_IZQ = art(  # respaldo a la derecha, mira a la izquierda
    "................",
    "...........nn...",
    "...........nn...",
    "...........nn...",
    "...........nn...",
    "...........nn...",
    "...........nn...",
    "...........nn...",
    "...nnnnnnnnnn...",
    "...nnnnnnnnnn...",
    "...kkkkkkkkkk...",
    "...gg......gg...",
    "...gg......gg...",
    "...gg......gg...",
    "...gg......gg...",
    "...gg......gg...",
)

# --- Pizarra de 3 tiles de ancho ---
# Pizarra BLANCA sobre pared amarilla, igual que en el aula real.
# Ocupa DOS filas de alto (32 px, tan alta como el jugador) para que se lea
# claramente como pizarra y no como una plataforma.
# Fila de arriba: marco superior + area de escritura.
PIZARRA_IZQ = art(
    "aaaaaaaaaaaaaaaa",
    "aaaaaaaaaaaaaaaa",
    "aaaddddddddddddd",
    "aaadwwwwwwwwwwww",
    "aaadwwwwwwwwwwww",
    "aaadwwwwwccccccw",
    "aaadwwwwwwwwwwww",
    "aaadwwwwwwwwwwww",
    "aaadwwweeeeeewww",
    "aaadwwwwwwwwwwww",
    "aaadwwwwwwwwwwww",
    "aaadwwwwwwwwwwww",
    "aaadwwwwnnnnwwww",
    "aaadwwwwwwwwwwww",
    "aaadwwwwwwwwwwww",
    "aaadwwwwwwwwwwww",
)

PIZARRA_CEN = art(
    "aaaaaaaaaaaaaaaa",
    "aaaaaaaaaaaaaaaa",
    "dddddddddddddddd",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "ccccccccwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwweeeeeeeeeeww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwnnnnnnww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
)

PIZARRA_DER = art(
    "aaaaaaaaaaaaaaaa",
    "aaaaaaaaaaaaaaaa",
    "dddddddddddddaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwnnnnnwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
)

# Fila de abajo: area de escritura + marco inferior + bandeja de marcadores.
PIZARRA_INF_IZQ = art(
    "aaadwwwwwwwwwwww",
    "aaadwwwwwwwwwwww",
    "aaadwwwwcccccwww",
    "aaadwwwwwwwwwwww",
    "aaadwwwwwwwwwwww",
    "aaadwwwwwwwwwwww",
    "aaadwwweeeewwwww",
    "aaadwwwwwwwwwwww",
    "aaadwwwwwwwwwwww",
    "aaadWWWWWWWWWWWW",
    "aaaddddddddddddd",
    "aaadgggggggggggg",
    "aaadkkkkkkkkkkkk",
    "aaaaaaaaaaaaaaaa",
    "aaaaaaaaaaaaaaaa",
    "AAAAAAAAAAAAAAAA",
)

PIZARRA_INF_CEN = art(
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwnnnnnnnnwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwwwwwwwwww",
    "wwwwwwwccccccccw",
    "wwwwwwwwwwwwwwww",
    "WWWWWWWWWWWWWWWW",
    "dddddddddddddddd",
    "gggggggggggggggg",
    "kkkkkkkkkkkkkkkk",
    "aaaaaaaaaaaaaaaa",
    "aaaaaaaaaaaaaaaa",
    "AAAAAAAAAAAAAAAA",
)

PIZARRA_INF_DER = art(
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwweeeeewwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "wwwwwwwwwwwwdaaa",
    "WWWWWWWWWWWWdaaa",
    "dddddddddddddaaa",
    "ggggggggggggdaaa",
    "kkkkkkkkkkkkdaaa",
    "aaaaaaaaaaaaaaaa",
    "aaaaaaaaaaaaaaaa",
    "AAAAAAAAAAAAAAAA",
)

# --- Ventana de DOS tiles de alto ---
VENTANA = art(  # mitad superior
    "gggggggggggggggg",
    "gkkkkkkkkkkkkkkg",
    "gkZZZZZZZZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkkkkkkkkkkkkkkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
)

VENTANA_INF = art(  # mitad inferior
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkkkkkkkkkkkkkkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkZZZZZZkZZZZZkg",
    "gkkkkkkkkkkkkkkg",
    "gggggggggggggggg",
    "................",
    "................",
    "................",
)

# --- Puerta de 2 tiles de alto ---
PUERTA_SUP = art(
    "..dddddddddddd..",
    "..dMMMMMMMMMMd..",
    "..dMZZZZZZZZMd..",
    "..dMZZZZZZZZMd..",
    "..dMZZZZZZZZMd..",
    "..dMZZZZZZZZMd..",
    "..dMZZZZZZZZMd..",
    "..dMZZZZZZZZMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
)

PUERTA_INF = art(
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMgg MMMMd..".replace(" ", "M"),
    "..dMMMgg MMMMd..".replace(" ", "M"),
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dMMMMMMMMMMd..",
    "..dddddddddddd..",
)

CASILLERO_SUP = art(
    "dddddddddddddddd",
    "drrrrrrddrrrrrrd",
    "drrrrrrddrrrrrrd",
    "drrrrrrddrrrrrrd",
    "drRRRRrddrRRRRrd",
    "drrrrrrddrrrrrrd",
    "drrrrrrddrrrrrrd",
    "drrrgrrddrrgrrrd",
    "drrrrrrddrrrrrrd",
    "drrrrrrddrrrrrrd",
    "drrrrrrddrrrrrrd",
    "drRRRRrddrRRRRrd",
    "drrrrrrddrrrrrrd",
    "drrrrrrddrrrrrrd",
    "drrrrrrddrrrrrrd",
    "dddddddddddddddd",
)

PAPELERA = art(
    "................",
    "................",
    "................",
    "................",
    "................",
    "....gggggggg....",
    "....g......g....",
    "....gkkkkkkg....",
    "....gkkkkkkg....",
    "....gkkkkkkg....",
    ".....gkkkkg.....",
    ".....gkkkkg.....",
    ".....gkkkkg.....",
    "......gkkg......",
    "......gggg......",
    "................",
)

RELOJ = art(
    "................",
    "................",
    "....dddddddd....",
    "...dttttttttd...",
    "..dtttttttttttd.",
    "..dtttttkttttd..",
    "..dtttttkttttd..",
    "..dtttttkttttd..",
    "..dtttttkkkttd..",
    "..dtttttttttd...",
    "..dtttttttttd...",
    "...dttttttttd...",
    "....dddddddd....",
    "................",
    "................",
    "................",
)

AFICHE = art(
    "................",
    "..dddddddddddd..",
    "..dttttttttttd..",
    "..dtzzzzzzzztd..",
    "..dtzttttttztd..",
    "..dtzttttttztd..",
    "..dtzzzzzzzztd..",
    "..dttttttttttd..",
    "..dtrrrrrrrrtd..",
    "..dttttttttttd..",
    "..dtmmmmmmmmtd..",
    "..dtttttttttd...",
    "..dddddddddddd..",
    "................",
    "................",
    "................",
)

TECHO = art(
    "dddddddddddddddd",
    "ssssssssssssssss",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBB",
)

# Orden = GID. El primero es GID 1.
TILES = [
    ("PISO", PISO),                    # 1
    ("PISO_BORDE", PISO_BORDE),        # 2
    ("PARED", PARED),                  # 3
    ("PARED_ZOCALO", PARED_ZOCALO),    # 4
    ("TECHO", TECHO),                  # 5
    ("ESTANTE", ESTANTE),              # 6
    ("MESA_IZQ", MESA_IZQ),            # 7
    ("MESA_DER", MESA_DER),            # 8
    ("SILLA_DER", SILLA_DER),          # 9
    ("SILLA_IZQ", SILLA_IZQ),          # 10
    ("PIZARRA_IZQ", PIZARRA_IZQ),      # 11
    ("PIZARRA_CEN", PIZARRA_CEN),      # 12
    ("PIZARRA_DER", PIZARRA_DER),      # 13
    ("VENTANA", VENTANA),              # 14
    ("PUERTA_SUP", PUERTA_SUP),        # 15
    ("PUERTA_INF", PUERTA_INF),        # 16
    ("CASILLERO", CASILLERO_SUP),      # 17
    ("PAPELERA", PAPELERA),            # 18
    ("RELOJ", RELOJ),                  # 19
    ("AFICHE", AFICHE),                # 20
    ("PIZARRA_INF_IZQ", PIZARRA_INF_IZQ),  # 21
    ("PIZARRA_INF_CEN", PIZARRA_INF_CEN),  # 22
    ("PIZARRA_INF_DER", PIZARRA_INF_DER),  # 23
    ("VENTANA_INF", VENTANA_INF),          # 24
]

hoja = Image.new("RGBA", (COLS * TILE, FILAS * TILE), (0, 0, 0, 0))
for idx, (nombre, arte) in enumerate(TILES):
    col, fila = idx % COLS, idx // COLS
    for y, linea in enumerate(arte):
        for x, ch in enumerate(linea):
            hoja.putpixel((col * TILE + x, fila * TILE + y), PALETA[ch])

destino = sys.argv[1]
hoja.save(destino)
print("tileset creado:", destino)
print(f"  {COLS}x{FILAS} = {COLS * FILAS} tiles de {TILE}x{TILE} px")
print("  GIDs definidos:")
for idx, (nombre, _a) in enumerate(TILES):
    print(f"    GID {idx + 1:2d} = {nombre}")
