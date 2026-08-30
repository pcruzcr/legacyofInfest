"""Construye las seis capas visuales del Stage 3-1 desde el perfil del terreno.

Todo sale de `ruta.py`: el suelo, los cantos, dónde caben los bosquecillos
y dónde van los muros. No hay ninguna coordenada escrita a mano que pueda
desincronizarse con la colisión — si el perfil cambia, cambia todo con él.
"""
import json
import os as _os
import sys

_AQUI = _os.path.dirname(_os.path.abspath(__file__))
_ART = _AQUI if _os.path.basename(_AQUI) == "art" else _os.path.join(_AQUI, "art")
_BASE = _os.path.dirname(_ART)
sys.path.insert(0, _ART)


def _ruta(nombre):
    a = _os.path.join(_ART, nombre)
    return a if _os.path.exists(a) else _os.path.join(_BASE, nombre)


import ruta as R                                     # noqa: E402
from palette import tile_variant_index               # noqa: E402

W, H = R.COLUMNAS, R.ALTO_MAPA
FILA_SUELO = R.FILA_SUELO
GRID_W = 8
FIRSTGID = 1

meta = json.load(open(_ruta("tileset_meta.json")))
PLACE = meta["placements"]
GRID_W = meta["grid_w"]

ALTURAS, TRAMOS = R.comprobar(verboso=False)


def gid(name, dx=0, dy=0):
    c, r, tw, th = PLACE[name]
    return FIRSTGID + (r + dy) * GRID_W + (c + dx)


def new_grid():
    return [[0] * W for _ in range(H)]


def put_block(grid, name, col, row):
    c0, r0, tw, th = PLACE[name]
    for dy in range(th):
        for dx in range(tw):
            gy, gx = row + dy, col + dx
            if 0 <= gy < H and 0 <= gx < W:
                grid[gy][gx] = gid(name, dx, dy)


def csv_of(grid):
    return ",\n".join(",".join(str(v) for v in row) for row in grid)


bg_far = new_grid()
bg_mid = new_grid()
bg_near = new_grid()
terrain = new_grid()
terrain_detail = new_grid()
fg_overlay = new_grid()


def fila_sup(col):
    """Fila de la baldosa de superficie en una columna, o None si es pozo."""
    a = ALTURAS[col]
    return None if a is None else FILA_SUELO - a


# ═══ TERRENO ═══════════════════════════════════════════════════════════
# Autotile de cinco piezas. La clave es la esquina: el césped no termina
# en el canto, dobla y baja por el costado. Sin esa pieza un escalón se ve
# como un rectángulo recortado y no como un trozo de tierra con volumen.
for c in range(W):
    f = fila_sup(c)
    if f is None:
        continue
    izq = ALTURAS[c - 1] if c > 0 else None
    der = ALTURAS[c + 1] if c + 1 < W else None
    canto_izq = izq is None or izq < ALTURAS[c]
    canto_der = der is None or der < ALTURAS[c]

    if canto_izq:
        sup = f"suelo_esq_izq_{tile_variant_index(c, f, 2, seed=41)}"
    elif canto_der:
        sup = f"suelo_esq_der_{tile_variant_index(c, f, 2, seed=43)}"
    else:
        sup = f"suelo_canto_{tile_variant_index(c, f, 4, seed=47)}"
    put_block(terrain, sup, c, f)

    for fila in range(f + 1, H):
        if canto_izq:
            pieza = f"suelo_lado_izq_{tile_variant_index(c, fila, 2, seed=51)}"
        elif canto_der:
            pieza = f"suelo_lado_der_{tile_variant_index(c, fila, 2, seed=53)}"
        else:
            pieza = f"suelo_relleno_{tile_variant_index(c, fila, 4, seed=57)}"
        put_block(terrain, pieza, c, fila)

# ── El camino de adoquín, sólo en los tramos llanos y largos ───────────
# No en todo el suelo: un camino que sube escaleras y bordea cornisas no
# es un camino. Va donde el terreno es plano y ancho, que es donde de
# verdad andaría la gente.
for t in TRAMOS:
    if t.tipo not in ("camino", "descanso") or t.ancho < 4:
        continue
    f = FILA_SUELO - t.altura
    for c in range(t.col0 + 1, t.col1 - 1):
        if ALTURAS[c] is None:
            continue
        put_block(terrain_detail, f"adoquin_{tile_variant_index(c, f, 6)}", c, f)


# ═══ MUROS DEL CAMPUS (BG_Mid) ═════════════════════════════════════════
# Kit modular: almena, cornisa, cuerpo con pilastras y huecos, zócalo de
# sillar basto, y escombro al pie. El escombro es lo que apoya el muro en
# el terreno en vez de recortarlo sobre él.
#
# Los paños se detienen donde está el gran arco y donde están las losas:
# el hito visual y la mecánica protagonista necesitan fondo limpio.
# Los paños van a una altura FIJA y bajan hasta el fondo del mapa. La
# versión anterior los hacía seguir el perfil del terreno y el resultado
# era ilegible: muro y suelo quedaban entrelazados a la misma altura y con
# el mismo valor, y no se distinguía por dónde se podía caminar.
#
# Bajando hasta el fondo, el terreno —que se dibuja en una capa posterior—
# les tapa la base. Lo que queda a la vista es sólo la parte alta, que es
# la que hace de horizonte urbano. La regla del curso es explícita: si
# algo compite con la geometría jugable, se reduce la decoración, no se
# sube el contraste del jugador.
MUROS = [(1, 18, 20), (22, 38, 17), (62, 78, 19)]
for c0, c1, cima in MUROS:
    for c in range(c0, c1):
        put_block(bg_mid, "almena_0", c, cima)
        put_block(bg_mid, "cornisa_0", c, cima + 1)
        for f in range(cima + 2, H):
            if (c - c0) % 5 == 0:
                pieza = "pilastra_0"
            elif (c - c0) % 5 == 2 and (f - cima) % 3 == 0:
                pieza = ("ojival_on" if tile_variant_index(c, f, 3, seed=13)
                         else "ojival_off")
            elif (c - c0) % 5 == 3 and f > cima + 2:
                pieza = f"arco_ciego_{tile_variant_index(c, f, 2, seed=17)}"
            else:
                pieza = f"pano_{tile_variant_index(c, f, 4, seed=19)}"
            put_block(bg_mid, pieza, c, f)


# ═══ EL GRAN ARCO ══════════════════════════════════════════════════════
# El hito. Va justo antes de la salida: se vislumbra de lejos, se reconoce
# al acercarse y se cruza al salir.
_col_arco = 88
_base_arco = fila_sup(_col_arco) or FILA_SUELO
put_block(bg_mid, "arco_invenio", _col_arco, _base_arco - 13)


# ═══ BOSQUECILLOS Y ROCAS (BG_Near) ════════════════════════════════════
# Sólo se plantan sobre tramos llanos de anchura suficiente: un bosquecillo
# a caballo de un escalón se vería flotando por un lado. Se buscan los
# tramos válidos y se reparten en parejas con claros entre medias.
BOSQUES = [(1, "bosque_c"), (8, "bosque_b"), (27, "bosque_a"),
           (35, "bosque_d"), (57, "bosque_b"), (62, "bosque_c"),
           (77, "bosque_a")]
ROCAS = [(6, "roca_c"), (14, "roca_b"), (33, "roca_a"), (43, "roca_c"),
         (55, "roca_b"), (70, "roca_a"), (82, "roca_b")]


def llano(col, ancho):
    """¿Hay `ancho` columnas de altura constante a partir de `col`?"""
    if col + ancho > W:
        return False
    base = ALTURAS[col]
    if base is None:
        return False
    return all(ALTURAS[c] == base for c in range(col, col + ancho))


for col, nombre in BOSQUES + ROCAS:
    ancho, alto = PLACE[nombre][2], PLACE[nombre][3]
    if not llano(col, ancho):
        continue
    f = fila_sup(col)
    put_block(bg_near, nombre, col, f - alto)


# ── Farolas: al borde del camino, en los tramos llanos ─────────────────
for c in (5, 17, 30, 48, 60, 74, 86):
    f = fila_sup(c)
    if f is not None and llano(c, 1):
        put_block(bg_near, "farola_0", c, f - 2)


# ═══ FLORES: acento, no alfombra ═══════════════════════════════════════
# Reglas de colocación, de las referencias: mayor probabilidad al pie de
# rocas y bosquecillos, en los cantos del terreno y al arranque de las
# escaleras —sitios con sombra y humedad—; menor en medio del camino.
#
# Se colocan en `Terrain_Detail`, que va detrás del jugador, y nunca sobre
# el tramo de las losas: ahí la atención tiene que estar en la mecánica.
_anclas = [c for c, _ in ROCAS] + [c for c, _ in BOSQUES]
_sitios = set()
for a in _anclas:
    for d in (-2, -1, 1, 2, 3):
        _sitios.add(a + d)
# Cantos del terreno: donde cambia la altura crece lo que no se pisa.
for c in range(1, W - 1):
    if ALTURAS[c] is not None and ALTURAS[c - 1] is not None \
            and ALTURAS[c] != ALTURAS[c - 1]:
        _sitios.add(c)
        _sitios.add(c - 1)

for c in sorted(_sitios):
    if not (0 <= c < W) or ALTURAS[c] is None:
        continue
    if 57 <= c <= 72:                     # tramo de las losas: despejado
        continue
    if tile_variant_index(c, 0, 5, seed=61) != 0:
        continue                          # sólo una de cada cinco: acento
    f = fila_sup(c)
    if terrain_detail[f][c] == 0:
        put_block(terrain_detail, f"mata_{tile_variant_index(c, f, 4, seed=63)}",
                  c, f - 1)


# ═══ PRIMER PLANO (FG_Overlay) ═════════════════════════════════════════
# Uno a tres elementos por pantalla, nunca sobre un punto de aterrizaje.
# El primer plano suma profundidad; si tapa información, la resta.
for c in (4, 23, 47, 68, 94):
    f = fila_sup(c)
    if f is not None:
        put_block(fg_overlay, "arbusto_0", c, f - 1)
for c in (12, 38, 72):
    f = fila_sup(c)
    if f is not None:
        put_block(fg_overlay, "ivy_0", c, f)


layers = {"BG_Far": bg_far, "BG_Mid": bg_mid, "BG_Near": bg_near,
          "Terrain": terrain, "Terrain_Detail": terrain_detail,
          "FG_Overlay": fg_overlay}
for name, g in layers.items():
    with open(_ruta(f"{name}.csv"), "w") as f:
        f.write(csv_of(g))

print(f"capas construidas · {len(R.bloques_solidos(ALTURAS))} bloques de suelo · "
      f"alturas de {min(a for a in ALTURAS if a is not None)} a "
      f"{max(a for a in ALTURAS if a is not None)} baldosas")
