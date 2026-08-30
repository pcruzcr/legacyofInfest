"""Genera tileset_invenio_gothic_v5.png (Fase F2-F4 condensadas).
Aplica seccion 5.2 del brief: rampas 5 tonos, dithering, AO, ruido,
variantes deterministicas, luz direccional (horizonte = derecha, Acto I).
"""
import os as _os
# Las rutas se derivan de la ubicación de este fichero, no de una carpeta
# fija de la máquina donde se construyó. Los generadores viajan dentro de
# la entrega, así que tienen que poder ejecutarse desde donde caigan: un
# `/tmp/...` incrustado convierte el código en algo que sólo corre en un
# ordenador, y entonces "el arte se genera por código" deja de ser cierto
# para quien lo recibe.
_AQUI = _os.path.dirname(_os.path.abspath(__file__))
_ART = _AQUI if _os.path.basename(_AQUI) == "art" else _os.path.join(_AQUI, "art")
_BASE = _os.path.dirname(_ART)

def _ruta(nombre):
    """Busca un fichero junto a los generadores y, si no, un nivel arriba.

    Los mismos scripts se usan desde la carpeta de trabajo (donde los CSV
    y `objects_source.tmx` viven al lado del TMX) y desde dentro de `art/`
    en la entrega empaquetada. Probar los dos sitios evita tener que
    mantener dos versiones del generador.
    """
    a = _os.path.join(_ART, nombre)
    return a if _os.path.exists(a) else _os.path.join(_BASE, nombre)


import sys, json
sys.path.insert(0, _ART)
from PIL import Image
from pixelart import (
    terrain_variant, gothic_window, column_tile, cloud_sprite, tree_sprite,
    bush_sprite, flower_cluster, farola, ivy_strand, new_tile, ramp_fill_dithered,
    grass_top_variant, fog_tile, haze_band, darken, gothic_gate,
    ivy_strand_frame, flower_cluster_frame, farola_frame, gothic_window_frame,
    fog_tile_frame,
)
from palette import PIEDRA, GRAFITO, TERRACOTA, CESPED, VIDRIO, METAL, ramp_rgb
from vegetacion import bosquecillo, formacion_rocosa, mata_de_flores, bayas_sobre
import arquitectura as ARQ
import terreno as TER




T = 16
GRID_W = 8  # tiles por fila en el tileset

animations = {}  # nombre del fotograma 0 -> [(nombre_frame, duracion_ms), ...]


def add_anim(base, frames, duration, tw=1, th=1):
    """Registra una secuencia. El fotograma 0 es la baldosa que se coloca
    en el mapa; el resto viven en el atlas y solo se alcanzan por la
    animacion declarada en el TMX (pyscroll los sustituye en caliente)."""
    names = []
    for i, img in enumerate(frames):
        nm = base if i == 0 else f"{base}__f{i}"
        add(nm, img, tw, th)
        names.append(nm)
    animations[base] = [(nm, duration) for nm in names]


tiles = []      # lista de (nombre, PIL.Image de tiles_w*T x tiles_h*T, tiles_w, tiles_h)
catalog = {}    # nombre -> {"col":c,"row":r,"w":tw,"h":th,"gid_local": idx_primer_tile}


def add(name, img, tw=1, th=1):
    tiles.append((name, img, tw, th))


# --- Terreno: adoquin (6 variantes) ---
for i in range(6):
    add(f"adoquin_{i}", TER.adoquin_camino(1000 + i))

# --- Cesped (6 variantes): tierra en estratos + briznas, borde irregular ---
for i in range(6):
    add(f"cesped_{i}", grass_top_variant(i, seed=2000 + i))

# --- Muro piedra (4 variantes) ---
for i in range(4):
    add(f"muro_piedra_{i}", terrain_variant(PIEDRA, i, kind="wall", seed=3000 + i))

# --- Muro grafito / INVENIO (4 variantes) ---
for i in range(4):
    add(f"muro_grafito_{i}", terrain_variant(GRAFITO, i, kind="wall", seed=4000 + i))

# --- Base del edificio: mismo muro, en sombra ---
# La fachada terminaba en un canto recto flotando sobre el cesped. Un
# edificio que no toca el suelo se lee como cartel, no como arquitectura.
for i in range(4):
    add(f"muro_base_{i}", darken(terrain_variant(GRAFITO, i, kind="wall", seed=13000 + i), 0.62))
add("zocalo_0", darken(terrain_variant(PIEDRA, 1, kind="wall", seed=13100), 0.75))

# --- Losa del sendero (Unidad VI): adoquin mas grande y de junta marcada,
#     para que se distinga del empedrado normal antes de encenderse ---
losa = terrain_variant(PIEDRA, 3, kind="ground", seed=14000)
lpx = losa.load()
_pied = ramp_rgb(PIEDRA)
for _i in range(16):
    lpx[_i, 0] = _pied[0] + (255,)
    lpx[0, _i] = _pied[0] + (255,)
    lpx[_i, 15] = _pied[1] + (255,)
add("losa_0", losa)

# --- Subsuelo: misma roca, oscurecida por profundidad ---
for i in range(4):
    add(f"subsuelo_{i}", darken(terrain_variant(PIEDRA, i, kind="wall", seed=11000 + i), 0.52))
for i in range(4):
    add(f"subsuelo_hondo_{i}", darken(terrain_variant(PIEDRA, i, kind="wall", seed=12000 + i), 0.34))

# --- Bloque terracota (3 variantes) ---
for i in range(3):
    add(f"terracota_{i}", terrain_variant(TERRACOTA, i, kind="block", seed=5000 + i))

# --- Vidrio planta baja ---
v = new_tile()
ramp_fill_dithered(v, VIDRIO, top_light=True, ao_bottom=True, noise=2)
add("vidrio_0", v)

# --- Ventana gotica ---
# Vela temblando tras el vidrio (4 fotogramas, 220 ms -> ~1.1 s por ciclo)
add_anim("ventana_lit", [gothic_window_frame(VIDRIO, GRAFITO, i) for i in range(4)], 220)
add("ventana_dark", gothic_window(VIDRIO, GRAFITO, lit=False))

# --- Puerta (arco simple sobre grafito) ---
door = terrain_variant(GRAFITO, 0, kind="wall", seed=6000)
dpx = door.load()
terr = ramp_rgb(TERRACOTA)
for y in range(4, T):
    for x in range(4, T - 4):
        dpx[x, y] = terr[1] + (255,)
for x in range(5, T - 5):
    dpx[x, 4] = terr[3] + (255,)
add("puerta_0", door)

# --- Columnas pergola ---
add("columna_fuste", column_tile(PIEDRA, part="shaft"))
add("columna_capitel", column_tile(PIEDRA, part="capital"))

# --- Viga (dintel horizontal de la pergola) ---
beam = new_tile()
ramp_fill_dithered(beam, PIEDRA, top_light=True, ao_bottom=True, noise=3, y0=5, h=6)
add("viga_0", beam)

# --- Jardinera (borde plataforma) ---
jard = terrain_variant(TERRACOTA, 0, kind="wall", seed=7000)
jpx = jard.load()
ces = ramp_rgb(CESPED)
for x in range(T):
    for y in range(0, 4):
        jpx[x, y] = ces[3 if x % 3 else 2] + (255,)
add("jardinera_top", jard)

# --- Plataforma flotante (delgada, un solo sentido) ---
plat = terrain_variant(PIEDRA, 2, kind="wall", seed=8000)
add("plataforma_0", plat)

# --- Arbustos, flores, farola, ivy ---
add("arbusto_0", bush_sprite(1, 1, 9001))
add("arbusto_1", bush_sprite(1, 1, 9002))
# Flores meciendose (mismo ciclo que la hiedra, desfasado para que el
# conjunto no lata al unisono)
# Matas de flores: tallos con corolas de dos o tres pixeles. Van como
# acento —al pie de rocas y arboles, en los cantos del terreno— y nunca
# en medio del paso. El tono mas claro de la rampa sale en una de cada
# cinco corolas: en una paleta violeta fria, el rosa claro es acento.
for i in range(4):
    add(f"mata_{i}", mata_de_flores(9100 + i))
add("arbusto_bayas", bayas_sobre(bush_sprite(1, 1, 9003), 9500))

add_anim("flor_0", [flower_cluster_frame(9101, i) for i in range(4)], 300)
add_anim("flor_1", [flower_cluster_frame(9102, (i + 2) % 4) for i in range(4)], 360)
# Llama de la farola (4 fotogramas, 150 ms -> ciclo corto, nervioso)
add_anim("farola_0", [farola_frame(i) for i in range(4)], 150)
# Hiedra meciendose (4 fotogramas, 320 ms -> ciclo lento, vegetal)
add_anim("ivy_0", [ivy_strand_frame(9201, i) for i in range(4)], 320)
add_anim("ivy_1", [ivy_strand_frame(9202, i) for i in range(4)], 340)

# --- Terreno: autotile de cinco piezas (leccion del Forest minimal) ---
# La pieza clave es la esquina: el cesped no termina en el canto, dobla y
# baja por el costado. Sin ella un escalon se ve como un rectangulo.
for i in range(4):
    add(f"suelo_canto_{i}", TER.canto_superior(700 + i))
for i in range(2):
    add(f"suelo_esq_izq_{i}", TER.canto_esquina(720 + i, True))
    add(f"suelo_esq_der_{i}", TER.canto_esquina(740 + i, False))
    add(f"suelo_lado_izq_{i}", TER.cara_lateral(760 + i, True))
    add(f"suelo_lado_der_{i}", TER.cara_lateral(780 + i, False))
for i in range(4):
    add(f"suelo_relleno_{i}", TER.relleno(800 + i))

# --- Kit modular de muro gotico (leccion del Dark Castle) -------------
# Piezas combinables, no edificios cerrados: con doce baldosas se levanta
# cualquier paño de cualquier tamaño. El muro lleva marco (pilastras y
# cornisa), dos escalas de sillar (fino arriba, basto en el zocalo) y su
# propia transicion al suelo (escombro), que era el problema de fondo.
# Los muros van OSCURECIDOS al 62 %. Estan en BG_Mid, o sea detras de la
# zona jugable, y con el mismo valor que el terreno la pantalla se volvia
# una mancha en la que no se distinguia por donde se camina. La regla del
# curso es explicita: el fondo puede tener detalle, pero menos contraste
# local. Oscurecer es mas barato y mas fiable que subir el contraste del
# jugador, que es lo que habria que hacer si no.
_F = 0.48
for i in range(4):
    add(f"pano_{i}", darken(ARQ.paño(PIEDRA, 2, 900 + i), _F))
for i in range(2):
    add(f"pano_graf_{i}", darken(ARQ.paño(GRAFITO, 2, 940 + i), _F))
for i in range(2):
    add(f"zocalo_m_{i}", darken(ARQ.zocalo(PIEDRA, 960 + i), _F))
add("pilastra_0", darken(ARQ.pilastra(PIEDRA, 970), _F))
add("cornisa_0", darken(ARQ.cornisa(PIEDRA), _F))
add("almena_0", darken(ARQ.almena(PIEDRA), _F))
# Las ventanas encendidas NO se oscurecen: son el unico calido del fondo y
# lo que hace que el muro se lea como habitado.
add("ojival_on", ARQ.ventana_ojival(PIEDRA, True))
add("ojival_off", darken(ARQ.ventana_ojival(PIEDRA, False), _F))
for i in range(2):
    add(f"arco_ciego_{i}", darken(ARQ.arco_ciego(PIEDRA, 980 + i), _F))
for i in range(3):
    add(f"escombro_{i}", darken(ARQ.escombro(PIEDRA, 990 + i), _F))

# --- Bosquecillos y formaciones rocosas -------------------------------
# Ya no se generan arboles ni piedras sueltos: se generan CONJUNTOS, cada
# uno con su zona de integracion con el suelo dibujada de una vez
# (raices, sombra de contacto, hierba, piedrecitas). Un arbol solo se lee
# como estampa; un bosquecillo se lee como bosque.
add("bosque_a", bosquecillo(7, 7, 5001, 3, flores=True), 7, 7)
add("bosque_b", bosquecillo(5, 6, 5002, 2, flores=False), 5, 6)
add("bosque_c", bosquecillo(6, 7, 5003, 4, flores=True), 6, 7)
add("bosque_d", bosquecillo(4, 5, 5004, 2, flores=False), 4, 5)
add("roca_a", formacion_rocosa(4, 2, 6001), 4, 2)
add("roca_b", formacion_rocosa(3, 2, 6002), 3, 2)
add("roca_c", formacion_rocosa(2, 2, 6003), 2, 2)

# --- Arboles unicos (2 variantes, 2x3 tiles c/u, con flores rosadas Acto I) ---
add("arbol_a", tree_sprite(2, 3, 9301, flowers=True), 2, 3)
add("arbol_b", tree_sprite(2, 3, 9302, flowers=True), 2, 3)
add("arbol_c", tree_sprite(2, 3, 9303, flowers=False), 2, 3)

# --- El gran arco de entrada: hito visual del nivel (8 x 14 baldosas) ---
add("arco_invenio", gothic_gate(8, 14), 8, 14)

# --- Nubes (Plan 6.4 corregido): base plana oscura, banda por luz, rim ---
# Rampa propia de nube (violeta oscuro -> rosa polvo), separada del cielo
# para que no se lea como piel: mismo espiritu atardecer, mas fria/gris.
cloud_tones = [(0x22, 0x17, 0x33, 255), (0x3e, 0x2c, 0x4e, 255), (0x63, 0x45, 0x63, 255),
               (0x9c, 0x6a, 0x82, 255), (0xd8, 0xa8, 0xac, 255)]
cloud_a = cloud_sprite(6 * T, 3 * T, 9401, cloud_tones, light_from="right", size_class="media")
cloud_b = cloud_sprite(5 * T, 2 * T, 9402, cloud_tones, light_from="right", size_class="lejana")
add("nube_a", cloud_a, 6, 3)
add("nube_b", cloud_b, 5, 2)

# --- Niebla entre planos + calima (Plan 6.1, lo mas rentable) ---
SKY_MID = (0x5e, 0x2a, 0x56)     # tono medio del cielo Acto I (para la niebla)
SKY_WARM = (0xf0, 0x89, 0x5f)    # tono calido del horizonte (calima)
# Niebla a la deriva (4 fotogramas, 500 ms -> ciclo muy lento, ambiental)
add_anim("niebla_0", [fog_tile_frame(SKY_MID, i, bottom_alpha=80) for i in range(4)], 500)
add("calima_0", haze_band(SKY_WARM, alpha=28))


# --- Empaquetar en grilla, ocupando bloques w x h de celdas ---
def pack(tiles):
    grid_w = GRID_W
    occupied = set()
    row_cursor = 0

    def fits(c, r, w, h):
        if c + w > grid_w:
            return False
        for yy in range(r, r + h):
            for xx in range(c, c + w):
                if (xx, yy) in occupied:
                    return False
        return True

    placements = {}
    max_row = 0
    for name, img, tw, th in tiles:
        placed = False
        r = 0
        while not placed:
            for c in range(0, grid_w):
                if fits(c, r, tw, th):
                    for yy in range(r, r + th):
                        for xx in range(c, c + tw):
                            occupied.add((xx, yy))
                    placements[name] = (c, r, tw, th)
                    max_row = max(max_row, r + th)
                    placed = True
                    break
            r += 1
    return placements, max_row


placements, n_rows = pack(tiles)
sheet = Image.new("RGBA", (GRID_W * T, n_rows * T), (0, 0, 0, 0))
for name, img, tw, th in tiles:
    c, r, w, h = placements[name]
    sheet.alpha_composite(img, (c * T, r * T))

sheet.save(_os.path.join(_ART, "tileset_invenio_gothic_v5.png"))

def local_id(name):
    c, r, w, h = placements[name]
    return r * GRID_W + c


anim_meta = {
    str(local_id(base)): [{"tileid": local_id(nm), "duration": d} for nm, d in seq]
    for base, seq in animations.items()
}

meta = {"grid_w": GRID_W, "n_rows": n_rows, "tile_size": T,
        "placements": placements, "animations": anim_meta}
with open(_os.path.join(_ART, "tileset_meta.json"), "w") as f:
    json.dump(meta, f, indent=2)

print("OK", GRID_W, n_rows, len(placements), "sprites")
