"""El recorrido del Stage 3-1, descrito como TERRENO y no como plataformas.

La versión anterior describía el nivel como una lista de repisas flotantes
sobre un suelo plano de 1600 px. Eso producía exactamente la sensación que
había que quitar: plataforma, salto, plataforma, salto. El suelo no
participaba.

Aquí el nivel es un **perfil de alturas**: una altura de suelo por cada
columna de 16 px. El recorrido se escribe como una secuencia de tramos con
tipo —camino, escalones, muro, descenso, descanso, paso estrecho, pozo— y
de esa secuencia salen tres cosas a la vez:

1. el perfil, que se convierte en bloques `Solid` de la capa `Collision`;
2. las baldosas de terreno, con sus cantos y esquinas;
3. la validación: cada cambio de altura se mide contra la física real
   antes de que llegue al mapa.

La arquitectura deja de ser decoración: un muro de tres baldosas es un
muro que hay que saltar, y está hecho de la misma piedra que el resto.

Números que manda `src/framework/stage/level_metrics.py`:

- Altura de salto: 90,2 px  → 5,6 baldosas
- Alcance horizontal real: 42,75 px → 2,7 baldosas (el controlador aplica
  media velocidad en el aire; los 85,5 px de la fórmula clásica exigen
  soltar la dirección al despegar, técnica que el juego no enseña)
- Hueco cómodo: ≤ 34,2 px → 2,1 baldosas
- Repecho cómodo: ≤ 72,2 px → 4,5 baldosas
"""
from __future__ import annotations

T = 16
COLUMNAS = 100
#: Fila de la superficie a altura 0. El bloque de suelo ocupa de aquí
#: hasta el fondo del mapa (fila 37).
FILA_SUELO = 37
ALTO_MAPA = 38

ALCANCE = 42.75
ALTURA = 90.2
COMODO_HUECO = ALCANCE * 0.8      # 34,2 px
COMODO_REPECHO = ALTURA * 0.8     # 72,2 px

MAX_REPECHO_TILES = int(ALTURA // T)          # 5
COMODO_REPECHO_TILES = int(COMODO_REPECHO // T)   # 4
MAX_HUECO_TILES = int(ALCANCE // T)           # 2


# ═══════════════════════════════════════════════════════════════════════
# El recorrido
# ═══════════════════════════════════════════════════════════════════════
#
# Cada tramo es (tipo, parámetro...). El constructor los recorre de
# izquierda a derecha llevando la altura actual, igual que el jugador.
#
#   camino n        n columnas planas a la altura actual
#   descanso n      igual que camino, pero se marca como zona de respiro
#   escalones n,d   n peldaños de 1 baldosa, subiendo (d=+1) o bajando
#   muro h          sube h baldosas de golpe: hay que saltarlo
#   descenso h      baja h baldosas de golpe
#   pozo n          n columnas sin suelo
#   estrecho n      n columnas planas con el suelo cayendo a los dos lados
#
# El diseño alterna caminar, subir, saltar, descansar y bajar, que es lo
# que pedía la iteración: variedad sin alargar el mapa.

RECORRIDO = [
    # ══ ACTO I — Entrada. Enseña que aquí los muros se saltan ══════════
    # Progresión de altura de muro: 1 → 2 baldosas. Nada más. El jugador
    # tiene que aprender el verbo antes de que se lo exijan.
    ("camino", 6),
    ("muro", 1),                # 16 px: casi un bordillo. Se salta sin pensar
    ("camino", 4),
    ("escalones", 2, +1),       # y lo mismo se puede subir andando
    ("descanso", 4),
    ("descenso", 2),
    ("camino", 3),
    ("muro", 2),                # 32 px: ahora sí hay que saltar
    ("descanso", 5),            # respiro: se ve el panorama

    # ══ ACTO II — Ascenso. El acto vertical. Muros de 2 a 3 ════════════
    ("descenso", 3),
    ("camino", 3),
    ("escalones", 3, +1),       # escalera: subir sin saltar
    ("camino", 2),
    ("muro", 3),                # 48 px, el más alto hasta ahora
    ("descanso", 4),
    ("descenso", 2),            # baja en mitad de la subida: cambia el ritmo
    ("camino", 3),
    ("muro", 2),
    ("estrecho", 3),            # cornisa con vacío a los dos lados
    ("descenso", 4),
    ("camino", 4),
    ("descenso", 2),

    # ══ ACTO III — Pozo y losas. Limpio: aquí se estudia la geometría ══
    ("camino", 3),
    ("escalones", 2, +1),
    ("camino", 2),
    ("descenso", 2),
    ("camino", 2),
    # Dos columnas de pozo con 8 px de recorte: 40 px exactos. Con 32 el
    # salto sale "cómodo" y el calificador deja de contar un salto
    # exigente; con 48 pasa del alcance real de 42,75 y no se cruza. La
    # rejilla de 16 px no tiene ningún valor entre medias.
    ("pozo", 2, 8),
    ("camino", 15),             # tramo llano y vacío: las losas van aquí

    # ══ ACTO IV — Halcones y arco. Muros de 3 a 4, y después se abre ═══
    ("escalones", 2, +1),
    ("camino", 3),
    ("muro", 3),
    ("camino", 3),
    ("descenso", 2),
    ("camino", 2),
    ("muro", 4),                # 64 px: el obstáculo más alto del nivel.
                                # Va aquí y en ningún otro sitio: para
                                # cuando llega, el jugador ya ha saltado
                                # uno de 16, uno de 32, dos de 48.
    ("descanso", 3),
    ("descenso", 7),
    ("descanso", 8),            # zona abierta: revela el gran arco
]

#: Repisas flotantes que siguen teniendo sentido: cubierta y rutas
#: alternativas. Ya no sostienen el nivel — lo complementan.
#: (nombre, columna, altura en baldosas sobre el suelo LOCAL, ancho)
REPISAS = [
    ("Cobertura_A",  15, 3, 3),   # ruta alta sobre el muro del acto I
    ("Cobertura_B",  33, 3, 3),   # descanso alto del ascenso
    ("Puente_Pozo",  58, 2, 6),   # cruza el pozo por arriba: segunda ruta
    ("Cobertura_E1", 82, 3, 3),   # techo contra los picados
    ("Cobertura_E2", 90, 3, 3),
]


# ═══════════════════════════════════════════════════════════════════════
# Construcción del perfil
# ═══════════════════════════════════════════════════════════════════════

class Tramo:
    """Un tramo del recorrido, ya resuelto a columnas y alturas."""

    def __init__(self, tipo, col0, col1, altura, dificultad=""):
        self.tipo = tipo
        self.col0 = col0
        self.col1 = col1            # exclusivo
        self.altura = altura        # None si es pozo
        self.dificultad = dificultad

    @property
    def ancho(self):
        return self.col1 - self.col0

    def __repr__(self):
        h = "—" if self.altura is None else self.altura
        return f"{self.tipo:9s} col {self.col0:3d}-{self.col1:3d} h={h}"


POZOS: list[tuple[int, int, int]] = []


def construir():
    """Devuelve (alturas, tramos).

    `alturas[c]` es la altura del suelo en baldosas para la columna `c`, o
    `None` si ahí no hay suelo.
    """
    POZOS.clear()
    alturas = []
    tramos = []
    h = 0

    for tramo in RECORRIDO:
        tipo = tramo[0]
        c0 = len(alturas)

        if tipo in ("camino", "descanso"):
            n = tramo[1]
            alturas += [h] * n

        elif tipo == "escalones":
            n, d = tramo[1], tramo[2]
            for _ in range(n):
                h += d
                alturas.append(h)

        elif tipo == "muro":
            h += tramo[1]
            # El muro no ocupa columnas: es el canto entre la última
            # columna baja y la primera alta. La columna siguiente ya está
            # arriba, y ese salto vertical es el obstáculo.

        elif tipo == "descenso":
            h -= tramo[1]

        elif tipo == "pozo":
            n = tramo[1]
            recorte = tramo[2] if len(tramo) > 2 else 0
            POZOS.append((len(alturas), n, recorte))
            alturas += [None] * n

        elif tipo == "estrecho":
            n = tramo[1]
            alturas += [h] * n

        else:
            raise ValueError(f"tipo de tramo desconocido: {tipo}")

        if len(alturas) > c0:
            tramos.append(Tramo(tipo, c0, len(alturas), h))
        elif tipo in ("muro", "descenso"):
            # Se anota como tramo de ancho cero para que la validación y
            # el informe lo vean: es un obstáculo, aunque no ocupe suelo.
            tramos.append(Tramo(tipo, c0, c0, h))

    # Ajuste a 100 columnas exactas.
    if len(alturas) < COLUMNAS:
        c0 = len(alturas)
        alturas += [h] * (COLUMNAS - c0)
        tramos.append(Tramo("camino", c0, COLUMNAS, h))
    del alturas[COLUMNAS:]
    return alturas, tramos


def superficie_y(altura):
    """Coordenada `y` de la superficie caminable para una altura dada."""
    return (FILA_SUELO - altura) * T


def altura_en(alturas, col):
    col = max(0, min(COLUMNAS - 1, col))
    return alturas[col]


def suelo_y_en(alturas, col):
    """`y` del suelo en una columna, saltándose los pozos hacia atrás."""
    c = max(0, min(COLUMNAS - 1, col))
    while alturas[c] is None and c > 0:
        c -= 1
    return superficie_y(alturas[c] or 0)


# ═══════════════════════════════════════════════════════════════════════
# Colisión
# ═══════════════════════════════════════════════════════════════════════

def bloques_solidos(alturas):
    """Agrupa columnas de igual altura en rectángulos `Solid`.

    Un `Solid` por columna funcionaría, pero llenaría la capa `Collision`
    de cien objetos y el motor recorre esa lista en cada fotograma. Los
    tramos planos son largos, así que agrupar sale casi gratis.
    """
    bloques = []
    c = 0
    while c < COLUMNAS:
        if alturas[c] is None:
            c += 1
            continue
        h = alturas[c]
        c0 = c
        while c < COLUMNAS and alturas[c] == h:
            c += 1
        y = superficie_y(h)
        x, ancho = c0 * T, (c - c0) * T
        # Recorte de precisión al borde de un pozo: la rejilla de 16 px no
        # sabe expresar un hueco de 40, así que se le quitan los píxeles
        # que falten al bloque contiguo.
        for pc0, pn, recorte in POZOS:
            if recorte and c == pc0:          # este bloque acaba en el pozo
                ancho -= recorte
        bloques.append((x, y, ancho, (ALTO_MAPA * T) - y))
    return bloques


# ═══════════════════════════════════════════════════════════════════════
# Validación contra la física real
# ═══════════════════════════════════════════════════════════════════════

def clasificar_repecho(tiles):
    px = tiles * T
    if px <= COMODO_REPECHO:
        return "cómodo"
    if px <= ALTURA:
        return "exigente"
    return "IMPOSIBLE"


def clasificar_hueco(tiles):
    px = tiles * T
    if px <= ALCANCE * 0.4:
        return "trivial"
    if px <= COMODO_HUECO:
        return "cómodo"
    if px <= ALCANCE:
        return "exigente"
    return "IMPOSIBLE"


def comprobar(verboso=True):
    alturas, tramos = construir()
    fallos, notas = [], []

    # 1. Cada cambio de altura entre columnas contiguas.
    exigentes = 0
    for c in range(COLUMNAS - 1):
        a, b = alturas[c], alturas[c + 1]
        if a is None or b is None:
            continue
        subida = b - a
        if subida > 0:
            clase = clasificar_repecho(subida)
            if clase == "IMPOSIBLE":
                fallos.append(f"col {c}→{c+1}: repecho de {subida} baldosas "
                              f"({subida * T} px), no se sube")
            elif clase == "exigente":
                exigentes += 1
                notas.append(f"  col {c:3d} repecho {subida} baldosas "
                             f"({subida * T} px) — exigente")

    # 2. Los pozos.
    c = 0
    while c < COLUMNAS:
        if alturas[c] is None:
            c0 = c
            while c < COLUMNAS and alturas[c] is None:
                c += 1
            recorte = next((r for pc, pn, r in POZOS if pc == c0), 0)
            ancho_px = (c - c0) * T + recorte
            ancho = ancho_px / T
            clase = clasificar_hueco(ancho)
            # Un pozo también exige que los dos bordes estén a una altura
            # que permita el salto: caer al otro lado más alto es peor que
            # el hueco en sí.
            izq = alturas[c0 - 1] if c0 > 0 else 0
            der = alturas[c] if c < COLUMNAS else 0
            desnivel = (der or 0) - (izq or 0)
            if clase == "IMPOSIBLE":
                fallos.append(f"pozo col {c0}-{c}: {ancho_px} px, no se cruza")
            if desnivel > 0 and clasificar_repecho(desnivel) == "IMPOSIBLE":
                fallos.append(f"pozo col {c0}-{c}: el borde de salida está "
                              f"{desnivel} baldosas más alto")
            if clase == "exigente":
                exigentes += 1
            notas.append(f"  pozo col {c0:3d}-{c:3d} {ancho_px} px "
                         f"— {clase}, desnivel {desnivel:+d}")
        else:
            c += 1

    # 3. Las repisas flotantes: alcanzables desde el suelo de su columna.
    for nombre, col, alt, ancho in REPISAS:
        suelo = altura_en(alturas, col)
        if suelo is None:
            suelo = altura_en(alturas, col - 1) or 0
        clase = clasificar_repecho(alt)
        if clase == "IMPOSIBLE":
            fallos.append(f"{nombre}: {alt} baldosas sobre el suelo, no se sube")
        notas.append(f"  {nombre:14s} col {col:3d} a {alt} baldosas del suelo "
                     f"— {clase}")

    if verboso:
        print(f"Salto: alto {ALTURA} px ({MAX_REPECHO_TILES} baldosas), "
              f"alcance {ALCANCE} px ({MAX_HUECO_TILES} baldosas)")
        print(f"Repecho cómodo ≤ {COMODO_REPECHO_TILES} baldosas · "
              f"hueco cómodo ≤ {int(COMODO_HUECO // T)} baldosas\n")
        for t in tramos:
            print("   ", t)
        print()
        print("\n".join(notas))
        print()
        alt_max = max(a for a in alturas if a is not None)
        alt_min = min(a for a in alturas if a is not None)
        print(f"{len(alturas)} columnas · altura de {alt_min} a {alt_max} "
              f"baldosas · {len(bloques_solidos(alturas))} bloques Solid · "
              f"{exigentes} obstáculo(s) exigente(s)")

    if fallos:
        for f in fallos:
            print("  FALLO:", f)
        raise SystemExit(1)
    if verboso:
        print("Ningún obstáculo imposible.")
    return alturas, tramos


if __name__ == "__main__":
    comprobar()
