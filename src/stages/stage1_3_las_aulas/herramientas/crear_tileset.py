"""Dibuja un tileset propio de aula: 16x16 px, rejilla 8x8 = 64 tiles.

Cada tile se define como 16 lineas de 16 caracteres. Cada caracter es un
color de la paleta. Asi el arte queda legible y editable en el codigo.
"""
import sys

from PIL import Image

TILE, COLS, FILAS = 16, 8, 8

# AUD-Yariel-01: reskin a la paleta "aula moderna" que pidio el profesor para
# la Practica II (blanco/hueso + gris concreto/carbon + azul electrico como
# acento tecnologico). Se cambian solo los VALORES de color de las letras que
# ya existian -no las formas de los tiles-, asi que ningun art() de mas abajo
# se toca: pintan lo mismo, con otro color. "a"/"A" (antes amarillo del marco
# de la pizarra) y "r"/"R" (antes casilleros rojos) pasan a azul electrico:
# es el "toque tecnologico" que pidio la paleta, sin redibujar nada.
PALETA = {
    ".": (0, 0, 0, 0),          # transparente
    "b": (198, 201, 203, 255),  # piso: concreto claro
    "B": (244, 244, 244, 255),  # pared: gris hueso (#F4F4F4)
    "s": (168, 172, 174, 255),  # sombra sobre piso/pared
    "m": (140, 105, 70, 255),   # madera media (estante — se deja: es la señal
                                 # visual de "aqui se pisa", no tocar el contraste)
    "M": (126, 136, 140, 255),  # gris concreto (#7E888C): marcos, patas, puertas
    "d": (58, 58, 58, 255),     # gris carbon (#3A3A3A): contorno / estructura
    "z": (0, 60, 120, 255),     # azul electrico oscuro
    "Z": (120, 175, 230, 255),  # azul claro (vidrio de ventanal grande)
    "t": (248, 248, 246, 255),  # tiza / blanco
    "r": (0, 85, 165, 255),     # casillero: azul electrico (#0055A5)
    "R": (0, 60, 120, 255),     # casillero, sombra
    "g": (126, 136, 140, 255),  # gris concreto (#7E888C): metal / mobiliario
    "k": (40, 40, 44, 255),     # negro suave
    "w": (255, 255, 255, 255),  # blanco puro (pizarra acrilica)
    "W": (222, 222, 220, 255),  # sombra del blanco
    "a": (0, 85, 165, 255),     # acento: azul electrico (#0055A5) — antes amarillo
    "A": (0, 60, 120, 255),     # acento en sombra
    "n": (35, 35, 38, 255),     # negro de las sillas
    "c": (196, 120, 60, 255),   # marcador naranja
    "e": (70, 130, 90, 255),    # marcador verde
    "U": (200, 225, 255, 255),  # luz LED encendida (glow azul-blanco)
    "u": (30, 70, 130, 255),    # luz LED apagada/tenue
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

# AUD-Yariel-01 (seguimiento): el afiche usaba "z" y "r" para su foto y su
# franja de acento -- las mismas letras que crear_tileset.py reutiliza para
# los casilleros y el marco de la pizarra en la paleta "aula moderna". Al
# recolorear esas letras a azul electrico, el afiche completo se volvio azul
# de casualidad (parecia un objeto nuevo repitiendose por el mapa, no un
# poster). Usa "g" y "c" -- ya definidas, ninguna compartida con el acento
# de los casilleros -- para que un cambio de paleta ahi no vuelva a
# arrastrar al afiche sin querer.
AFICHE = art(
    "................",
    "..dddddddddddd..",
    "..dttttttttttd..",
    "..dtggggggggtd..",
    "..dtgttttttgtd..",
    "..dtgttttttgtd..",
    "..dtggggggggtd..",
    "..dttttttttttd..",
    "..dtcccccccctd..",
    "..dttttttttttd..",
    "..dtmmmmmmmmtd..",
    "..dtttttttttd...",
    "..dddddddddddd..",
    "................",
    "................",
    "................",
)

# Panel LED de techo, "toque tecnologico" pedido en la paleta. Dos tiles con
# la misma forma que solo cambian el color del foco (U brillante / u tenue):
# generar_mapa.py declara una <animation> en el TMX que alterna entre los dos,
# como la lampara parpadeante del cementerio (stage4_1) que sirvio de referencia.
LUZ_LED_ON = art(
    "................",
    "..dddddddddddd..",
    "..dggggggggggd..",
    "..dUUUUUUUUUUd..",
    "..dUUUUUUUUUUd..",
    "..dddddddddddd..",
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

LUZ_LED_OFF = art(
    "................",
    "..dddddddddddd..",
    "..dggggggggggd..",
    "..duuuuuuuuuud..",
    "..duuuuuuuuuud..",
    "..dddddddddddd..",
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
    ("LUZ_LED_ON", LUZ_LED_ON),             # 25
    ("LUZ_LED_OFF", LUZ_LED_OFF),           # 26
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
