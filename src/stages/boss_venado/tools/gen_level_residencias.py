"""
Modulo: gen_level_residencias
Sistema: tools (composicion de mapas)
Descripcion: Compone el TMX completo del nivel del boss "Residencias al Crepusculo"
    (205x38 tiles, 3280x608 px, side-scroller, tiles de 16x16). Este es el
    COMPOSITOR del nivel: organiza los tiles con nombre producidos por
    ``gen_tileset_residencias`` en ocho capas ordenadas mas dos grupos de
    objetos, siguiendo la vineta crepuscular aprobada (``art_proof.png`` /
    ``concept_master.png``, 2026-07-23) y el contrato TMX de
    ``docs/06_TMX_SPEC.md``.

Reglas de diseno (restricciones duras de la spec)
--------------------------------------------
- Todo esta anclado al suelo: la superficie caminable es la fila 35 (y=560),
  el cuerpo visual del suelo abarca las filas 35-37, y toda estructura apoya
  su tile inferior en la fila 34 (sus pies en y=560). Nada estructural flota.
- Cuatro zonas por columna de tile (ensanche de la ronda 11 + el nuevo carport,
  feedback del usuario "extender aun mas el mapa, cada zona un poco mas
  extensa, y hacer el lugar donde estaban los carros"): PRADERA [0,65) (un
  camino de tierra sinuoso mas largo, dos arboles grandes, casas lejanas con
  ventanas iluminadas/tapiadas, cerca caida, tendedero); CARPORT [65,95) (un
  cochera oscura de techo corrugado sobre postes de metal negro encima de una
  bahia de grava, un sedan plateado + una pickup blanca estacionados debajo y
  un tractor cargador naranja al lado, todo en silueta de crepusculo); ARCOS
  [95,155) (dos arcos hastiales transitables espaciados mas ampliamente para
  que el telescopio de un arco distante entre ellos respire, una linea de
  arboles/seto de patio continua entre ellos, revelados de piedra cercanos en
  FG_Overlay para que el jugador camine A TRAVES de cada portal, una lampara
  inclinada y una banca rota); ARENA [155,205) (la explanada de cesped con el
  gazebo de 7x6, su plaza de piedra, setos, luciernagas y hojas a la deriva,
  donde se pelea contra el boss).
- El tileset se referencia con ``trans="000000"`` para que los pixeles negro
  puro "vacio visual" de los tiles de overlay/estructura se lean como
  transparentes; esto es lo que permite que los props, setos, luciernagas, el
  interior del gazebo y las caras de los arcos se compongan sobre el
  cielo/suelo en lugar de estampar cajas negras.

Salida (idempotente; ``main()`` puede llamarse repetidamente, estable byte a byte)
--------------------------------------------------------------------
- ``<game>/assets/maps/boss_venado/boss_venado.tmx``
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from xml.sax.saxutils import escape as _escapar_xml

from src.framework.stage.stage_loader import SCHEMA_VERSION
from src.stages.boss_venado.tools.gen_tileset_residencias import NAME_TO_INDEX

# Autor del nivel (adopcion V3). ``grade_stage.py:61`` lo PUNTUA dentro de
# REQUIRED_GRADE_PROPS y el TMX no lo declaraba: era un tercio de la categoria
# de metadatos regalado.
AUTHOR = "José Jahel Morales Briceño"

# ---------------------------------------------------------------------------
# Rutas / constantes del mapa (derivadas de __file__ para que el cwd nunca importe)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
GAME_ROOT = _HERE.parents[4]                     # .../game
OUT_TMX = GAME_ROOT / "assets" / "maps" / "boss_venado" / "boss_venado.tmx"

W, H = 205, 38                                    # tamano del mapa en tiles (ensanche de ronda-11)
TILE = 16
FIRSTGID = 1
TILECOUNT = len(NAME_TO_INDEX)                    # unica fuente de verdad (atlas importado)
COLUMNS = 12
TILESET_NAME = "tileset_residencias_crepusculo"
TILESET_IMG = "../../tilesets/tileset_residencias_crepusculo.png"

# TAREA 13 (Unidad VII (b), profundidad de campo): segundo tileset, SOLO para
# BG_Far, con las tiles de compose_sky() pre-difuminadas por
# gen_tileset_bgfar_blur.generar_tileset_borroso() (build-time, coste cero en
# runtime -- ver el docstring de ese modulo). El nombre/ruta son constantes
# de texto independientes (no importadas de ese modulo: ver
# ADVERTENCIA DE IMPORT CIRCULAR mas abajo, junto a ``_nombres_bg_far()``).
#
# TAREA (2026-08-27, cierre de brechas del Entregable 2, decision del
# usuario, dictamen doc-guardian AMARILLO): el atlas que BG_Far referencia
# pasa de "solo blur" a "bruma" (blur + FilterTools.adjust_contrast,
# gen_tileset_bgfar_blur.generar_tileset_bruma()) -- perspectiva atmosferica
# real, los planos lejanos tambien pierden contraste local. Las constantes
# se RENOMBRARON (no solo cambiaron de valor): un grep confirmo que
# TILESET_BLUR_NAME/TILESET_BLUR_IMG solo se usaban DENTRO de este modulo
# (nadie mas las importaba), asi que el nombre viejo ya no era honesto --
# habria seguido diciendo "blur" mientras el TMX referenciaba un atlas
# distinto. El PNG solo-blur no se borra (zona de creacion, CLAUDE.md
# "ZONAS EDITABLES" punto 3) pero queda huerfano en disco, sin GID que lo
# apunte; su borrado queda a decision del usuario.
TILESET_BRUMA_NAME = "tileset_residencias_crepusculo_bgfar_bruma"
TILESET_BRUMA_IMG = "../../tilesets/tileset_residencias_crepusculo_bgfar_bruma.png"
FIRSTGID_BRUMA = FIRSTGID + TILECOUNT              # continua el rango de GIDs del tileset principal (sin cambios: mismo TILECOUNT)
# FIX RONDA-10 (causa raiz del "kiosco cortado"): DERIVAR la altura de imagen
# declarada a partir del conteo real de tiles para que siempre coincida con el
# atlas que emite el generador del tileset. Habia estado fijada en 240 (15
# filas) desde las primeras rondas mientras el atlas crecio a 19 filas
# (304 px). pytmx corta un tileset por la <image height> DECLARADA, asi que
# CADA tile en la fila >= 15 del atlas (indice de gid >= 180) -- las dos
# filas inferiores del gazebo (bases de piedra, plataforma, silueta de mesa,
# el charco de luz r8) Y la nueva plaza -- se estaba DESCARTANDO en silencio
# al renderizar, dejando un vacio de cielo bajo el kiosco. Derivar la altura
# (redondeando el conteo de tiles hacia arriba a filas completas) arregla el
# renderizado de forma definitiva.
TILESET_W = COLUMNS * TILE                        # 192 (12 cols x 16 px)
TILESET_H = ((TILECOUNT + COLUMNS - 1) // COLUMNS) * TILE   # filas completas para caber todos los tiles

GROUND_ROW = 35                                   # fila de superficie caminable (y=560)
SUB_ROWS = (36, 37)                               # filas de relleno subterraneo
BASE_ROW = 34                                     # fila del tile inferior de las estructuras

# Limites de zona en columnas de tile. Estas son la UNICA fuente de verdad de
# donde empieza/termina una zona: los umbrales de la superficie del suelo y el
# ``col0`` de cada estructura se derivan de ellos (p. ej. ARCOS.start + 4), asi
# que mover una zona es una sola edicion.
# NOTA: un puñado de posiciones DECORATIVAS ajustadas finamente por balance
# quedan absolutas dentro de su zona (las coordenadas del enjambre de
# luciernagas de la arena, y los tramos de pixeles de la cerca/tendedero) - no
# pueden "derivarse razonablemente" de un limite y estan marcadas en sus
# sitios de uso.
PRADERA = range(0, 65)
CARPORT = range(65, 95)                           # ronda-11: "el lugar donde estaban los carros"
ARCOS = range(95, 155)
ARENA = range(155, 205)

# RONDA-8 (feedback del usuario: el gazebo -- la pieza central de la arena --
# es "poco visible", su cuerpo iluminado se fusiona con el bosque oscuro
# detras). Se abre un CLARO despejado alrededor del gazebo para que su
# silueta de techo+cuerpo-iluminado se lea contra el cielo/pradera abierta del
# crepusculo en vez de una linea de arboles apretada. El bloque del gazebo
# mide 7 de ancho en ARENA.start+22 (columnas 177-183 tras el desplazamiento
# de ronda-11); el claro se abre ~4 columnas a cada flanco, con un HOMBRO de
# monticulo bajo de 2 columnas suavizando cada borde para que se lea como un
# claro en el bosque (no un agujero rectangular duro) y el ritmo de
# agrupacion-y-hueco de rondas 5/6 retoma mas alla de este. Solo se consulta
# dentro de ARENA (>= 171).
_GAZEBO_C0 = ARENA.start + 22                                       # 177 (columna izquierda del gazebo)
_GAZEBO_C1 = _GAZEBO_C0 + 6                                         # 183 (columna derecha del gazebo)
_ARENA_GAZEBO_GLADE = range(_GAZEBO_C0 - 4, _GAZEBO_C1 + 5)         # 173..187: sin agrupaciones altas
_ARENA_GLADE_SHOULDER = (set(range(_GAZEBO_C0 - 6, _GAZEBO_C0 - 4))  # 171-172 hombros de monticulo bajo
                         | set(range(_GAZEBO_C1 + 5, _GAZEBO_C1 + 7)))  # 188-189 hombros de monticulo bajo

# RONDA-9 (usuario: "el retoque esta bien, le falta que no lo tapen los
# arbustos del fondo"). La franja verde continua de la linea de suelo (la
# banda de pradera en las filas 33-34) mas los mechones de cesped en FG
# estaban enterrando las bases de piedra del gazebo, sus postes de la puerta
# y el portal. Su HUELLA -- las 7 columnas del gazebo mas 2 de margen a cada
# lado -- se mantiene LIBRE de la banda de pradera Y de los mechones de
# cesped en FG, para que la pieza central quede sobre suelo limpio (sus
# propias bases de piedra crema + el cesped iluminado de r7 en la fila 35
# debajo) con cielo abierto de crepusculo en sus flancos inmediatos: nada
# brota frente al portal. El resto de la arena conserva su pradera/mechones
# (ritmo). Solo siempre en ARENA (>=120).
_GAZEBO_FOOTPRINT = range(_GAZEBO_C0 - 2, _GAZEBO_C1 + 3)          # 175..185

# RONDA-11 (usuario: "hacer el lugar donde estaban los carros"). El carport
# es un techo corrugado oscuro de 10 columnas sobre postes de metal negro
# encima de una bahia de grava oscura, con un sedan plateado + una pickup
# blanca estacionados debajo y un tractor cargador naranja al lado. Igual que
# el gazebo, se abre un CLARO despejado a su alrededor para que su silueta
# oscura se lea contra el cielo/horizonte abierto del crepusculo en vez de
# una linea de arboles apretada, y la bahia de grava reemplaza la banda de
# pradera a lo largo de su huella. Todas las posiciones se derivan de
# CARPORT.start para que todo el conjunto se mueva con su zona.
_CARPORT_C0 = CARPORT.start + 6                                    # 71 (columna izquierda del techo)
_CARPORT_ROOF_W = 10
_CARPORT_C1 = _CARPORT_C0 + _CARPORT_ROOF_W - 1                    # 80 (columna derecha del techo)
_CARPORT_POSTS = (_CARPORT_C0, _CARPORT_C0 + 5, _CARPORT_C1)       # 71, 76, 80
_CARPORT_GRAVEL = range(_CARPORT_C0 - 1, _CARPORT_C1 + 4)          # 70..83 (bahia + explanada del tractor)
_CARPORT_GLADE = range(_CARPORT_C0 - 2, _CARPORT_C1 + 6)           # 69..85 cielo abierto detras

Layer = list[list[str | None]]


# ---------------------------------------------------------------------------
# Ayudantes de grilla de bajo nivel
# ---------------------------------------------------------------------------
def _blank() -> Layer:
    """Una grilla fresca de HxW celdas vacias (None -> gid 0)."""
    return [[None for _ in range(W)] for _ in range(H)]


def _gid(name: str) -> int:
    """GID de un tile con nombre: indice del atlas + firstgid (0 se reserva como vacio)."""
    try:
        return NAME_TO_INDEX[name] + FIRSTGID
    except KeyError:
        raise KeyError(f"unknown tile name '{name}'") from None


def _gid_bruma(name: str, mapping: dict[str, int]) -> int:
    """GID de un tile de BG_Far dentro del tileset bruma (TAREA 13, extendida
    TAREA 2026-08-27): indice en ``mapping`` (posicion en el atlas nuevo, no
    en el original) + ``FIRSTGID_BRUMA``. Renombrada junto con las
    constantes (ver el comentario de TILESET_BRUMA_NAME) -- sigue siendo
    intra-modulo, solo la llama ``_csv_layer_bg_far`` mas abajo."""
    return mapping[name] + FIRSTGID_BRUMA


def put(layer: Layer, x: int, y: int, name: str) -> None:
    """Fija una sola celda, recortando en silencio a los limites del mapa."""
    if 0 <= x < W and 0 <= y < H:
        layer[y][x] = name


def hband(layer: Layer, y0: int, y1: int, name: str, x0: int = 0, x1: int = W) -> None:
    """Rellena las filas [y0, y1) a lo ancho de las columnas [x0, x1) con un solo tile."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            put(layer, x, y, name)


def pick(options: list[str], x: int, y: int) -> str:
    """Selector de variante deterministico (funcion pura de la posicion -> idempotente)."""
    return options[(x * 7 + y * 13) % len(options)]


def place_block(
    layer: Layer,
    prefix: str,
    cols: int,
    rows: int,
    col0: int,
    row0: int,
    sep: str = "_",
    skip: set[tuple[int, int]] | None = None,
) -> None:
    """Estampa un bloque de tiles con nombre de (cols x rows) con su esquina
    superior izquierda en (col0, row0).

    Las celdas se nombran ``{prefix}{sep}{c}{r}`` (digito de columna primero),
    coincidiendo con el inventario producido por ``register_block`` (p. ej. la
    esquina inferior derecha de un gazebo de 7x6 es ``gaz_65``; un arbol usa
    ``sep=""`` -> ``tree_c33``). ``skip`` omite celdas del bloque dadas como
    pares ``(c, r)`` (usado para perforar las aberturas transitables de los
    arcos).

    Un bloque debe caber por completo en el mapa: a diferencia de ``put``
    (que recorta en silencio los tiles sueltos), un bloque que se sale del
    borde es un error de composicion y lanza excepcion, para que una
    estructura multi-tile mal colocada falle ruidosamente en vez de recortar
    de vuelta un sprite cortado.
    """
    if col0 < 0 or row0 < 0 or col0 + cols > W or row0 + rows > H:
        raise ValueError(
            f"block '{prefix}' at ({col0},{row0}) size {cols}x{rows} exceeds map {W}x{H}"
        )
    skip = skip or set()
    for c in range(cols):
        for r in range(rows):
            if (c, r) in skip:
                continue
            put(layer, col0 + c, row0 + r, f"{prefix}{sep}{c}{r}")


def place_hedge_column(layer: Layer, x0: int, x1: int, r_top: int) -> None:
    """Una masa de jardinera/seto desde la fila de copa ``r_top`` hasta el suelo (BASE_ROW).

    Se usa como soporte visual coherente, anclado al suelo, debajo de las plataformas de un solo sentido.
    """
    for x in range(x0, x1):
        put(layer, x, r_top, pick(["hedge_top_a", "hedge_top_b"], x, r_top))
        for y in range(r_top + 1, BASE_ROW + 1):
            name = "hedge_flower" if (x + y) % 7 == 0 else "hedge_fill"
            put(layer, x, y, name)


def place_bench(layer: Layer, x: int) -> None:
    """Un prop de banca rota de dos tiles apoyado en el suelo en las columnas x..x+1."""
    put(layer, x, BASE_ROW, "bench_broken_l")
    put(layer, x + 1, BASE_ROW, "bench_broken_r")


def scatter_leaves(layer: Layer, xs: Iterable[int]) -> None:
    """Deja caer tiles de hojas a la deriva en el suelo en cada columna de ``xs``."""
    for x in xs:
        put(layer, x, BASE_ROW, pick(["leaves_drift_a", "leaves_drift_b"], x, BASE_ROW))


def scatter_fg_grass(layer: Layer, xs: Iterable[int]) -> None:
    """Mechones de cesped en primer plano a lo largo del suelo en cada columna de ``xs`` (profundidad)."""
    for x in xs:
        put(layer, x, BASE_ROW, pick(["fg_grass_a", "fg_grass_b", "fg_grass_c"], x, BASE_ROW))


# ===========================================================================
# COMPOSICION GLOBAL: cielo + bosque distante
# ===========================================================================
def compose_sky(*, bg_far: Layer, bg_mid: Layer) -> None:
    """Gradiente de cielo crepuscular (BG_Far) + la vida del cielo dentro de la ventana (BG_Mid).

    NOTA DE METODOLOGIA (ronda 6): la resolucion interna REAL del motor es
    800x600 (settings.py; la rama de 320x224 es codigo muerto), y el mapa
    mide 2400x608, asi que el jugador ve esencialmente TODA la altura del
    mapa a la vez -- las filas 0..37 estan todas en pantalla, NO solo una
    ventana inferior de 320x224 como asumian las rondas 1-5. El diseno de
    bandas de abajo no cambia (sigue posando el horizonte calido en la linea
    de arboles), pero el cielo superior que antes era "solo para la
    postal, extendido" (filas 0..23) ahora es totalmente visible en el juego
    y lo compone ``compose_celestial`` (luna, nubes, estrellas, cresta lejana)
    en vez de dejarse como bandas de gradiente vacias.

    El gradiente corre desde violeta profundo (arriba) bajando por
    purpura/rosa y es unido por bandas de transicion CON DITHERING (sin
    costuras horizontales duras). El nucleo calido concentrado de puesta de
    sol ``sky_horizon`` + su resplandor difuso ``sky_glow`` se bajan hasta
    las filas ~27-30, justo en la linea de arboles/techos, para que en el
    juego los edificios se siluetean contra la puesta de sol en vez de una
    pared malva plana. BG_Far sigue completamente rellenado para que ningun
    pixel transparente de estructura revele negro.

    Las estrellas/nubes altas/murcielagos se quedan en el cielo superior
    profundo en bandas cuyo tono base coincide con el suyo (costuras
    invisibles). Las nubes/murcielagos *dentro de la ventana* van en cambio en
    BG_Mid sobre un fondo transparente, para que se compongan sobre las
    bandas calidas sin ningun parche rectangular.
    """
    # --- gradiente de BG_Far (arriba -> abajo) --------------------------------------
    # Las bandas moteadas planas hacen el grueso (se enlosan sin costuras
    # porque son uniformes); un tile de RAMPA con dithering conecta cada par,
    # colocado en EXACTAMENTE UNA fila para que su gradiente aparezca una sola
    # vez. (Apilar una rampa sobre varias filas es lo que repetia el
    # gradiente en las viejas franjas "neon"). La puesta de sol calida es una
    # secuencia continua S3->S4->S5->S4->S3: resplandor / nucleo brillante /
    # resplandor descendente.
    hband(bg_far, 0, 4, "sky_top")                # violeta profundo   (extendido)
    hband(bg_far, 4, 5, "sky_tr_01")              # rampa de 1 fila
    hband(bg_far, 5, 10, "sky_high")              # indigo        (extendido)
    hband(bg_far, 10, 11, "sky_tr_12")            # rampa de 1 fila
    hband(bg_far, 11, 24, "sky_mid")              # purpura; llega a la fila 23
    hband(bg_far, 24, 25, "sky_tr_23")            # rampa de 1 fila -> rosa (fila 24, tope de la ventana)
    hband(bg_far, 25, 27, "sky_low")              # crepusculo rosado      (filas 25-26)
    hband(bg_far, 27, 28, "sky_glow")             # subida del resplandor calido (fila 27)
    hband(bg_far, 28, 29, "sky_horizon")          # nucleo brillante de puesta de sol (fila 28, sobre los apices)
    hband(bg_far, 29, 30, "sky_glow_dn")          # caida calida       (fila 29)
    hband(bg_far, 30, H, "sky_low")               # crepusculo fresco detras de la linea de arboles/edificios/suelo

    # estrellas dispersas por el cielo superior profundo (el tono base coincide con sky_top/high).
    # RONDA-11: repartidas por todo el ancho de 205 columnas para que ninguna ventana de 800px quede vacia.
    stars = [(5, 1), (14, 3), (23, 2), (34, 4), (47, 1), (61, 3),
             (76, 2), (89, 4), (102, 1), (116, 3), (129, 2), (141, 4),
             (9, 6), (52, 8), (95, 7), (138, 9),
             (156, 2), (168, 4), (181, 1), (193, 3), (201, 2),
             (160, 7), (176, 9), (188, 6)]
    for i, (x, y) in enumerate(stars):
        put(bg_far, x, y, "sky_star_a" if i % 2 == 0 else "sky_star_b")

    # murcielagos altos + nubes etereas de postal (el tono base coincide con su banda), repartidos anchos
    for x, y in [(30, 5), (58, 8), (118, 6), (150, 5), (186, 7)]:
        put(bg_far, x, y, pick(["bat_a", "bat_b"], x, y))
    clouds = [(8, 5, True), (40, 8, False), (70, 4, False),
              (96, 7, True), (120, 5, False), (134, 9, True),
              (158, 6, False), (176, 4, True), (196, 8, False)]
    for x, y, rim in clouds:
        l, m, r = ("cloud_rim_l", "cloud_rim_m", "cloud_rim_r") if rim else ("cloud_l", "cloud_m", "cloud_r")
        put(bg_far, x, y, l)
        put(bg_far, x + 1, y, m)
        put(bg_far, x + 2, y, r)

    # --- vida del cielo dentro de la ventana (BG_Mid, fondo transparente -> sin costura de tono base) -----
    # RONDA-11: repartida para que CADA ventana de camara de ~800px (spawn 0-50,
    # carport 50-100, arcos 100-150, arena 150-205) enmarque una nube a la
    # deriva, todas en las filas 25-26 -> completamente DENTRO del cuadro. Se
    # mantiene escasa (checklist: moderacion).
    for x, y in [(3, 25), (28, 26), (60, 25), (82, 26), (116, 26), (140, 25),
                 (160, 26), (184, 25), (198, 26)]:
        put(bg_mid, x, y, "cloud_soft_l")
        put(bg_mid, x + 1, y, "cloud_soft_m")
        put(bg_mid, x + 2, y, "cloud_soft_r")
    for x, y in [(12, 26), (66, 27), (124, 26), (172, 27)]:
        put(bg_mid, x, y, "bat_soft")


def _nombres_bg_far() -> frozenset[str]:
    """Nombres unicos de tile que ``compose_sky()`` escribe en BG_Far
    (TAREA 13, Unidad VII (b)).

    ADVERTENCIA DE IMPORT CIRCULAR (por que esto NO se importa de
    ``gen_tileset_bgfar_blur.NOMBRES_BG_FAR``, aunque ese modulo calcula
    exactamente lo mismo): ``gen_tileset_bgfar_blur.py`` ya importa
    ``COLUMNS``/``TILE``/``_blank``/``compose_sky`` DESDE ESTE modulo. Si
    este modulo importara de vuelta ``NOMBRES_BG_FAR`` de ese, quedaria un
    ciclo real -- confirmado empiricamente insertando el import propuesto
    por el spec original y ejecutandolo: ``ImportError: cannot import name
    '_blank' from partially initialized module
    'src.stages.boss_venado.tools.gen_level_residencias' (most likely due to
    a circular import)``, porque este modulo aun no habia terminado de
    definir ``_blank``/``compose_sky`` cuando el import intentaba resolverse.

    La solucion: derivar el conjunto AQUI, invocando la MISMA funcion pura
    ``compose_sky`` (literalmente el mismo objeto de funcion que
    ``gen_tileset_bgfar_blur`` importa de este modulo) sobre capas en
    blanco propias. Como ``compose_sky`` es pura (su salida depende solo de
    sus argumentos), llamarla aqui y llamarla en ``gen_tileset_bgfar_blur``
    produce, por construccion, el MISMO conjunto -- no es una duplicacion de
    logica que pueda desincronizarse, es la misma logica invocada dos veces.
    Blindado por partida doble: ``test_nombres_bg_far_no_esta_vacio_y_coincide_con_compose_sky``
    fija el comportamiento de ``compose_sky`` de forma independiente, y
    ``test_bg_far_referencia_el_tileset_de_bruma`` (test_map_residencias.py;
    renombrado en la TAREA 2026-08-27 -- se llamaba
    "...tileset_borroso" cuando el atlas de BG_Far era solo-blur)
    verifica que el TMX resultante efectivamente solo usa GIDs del tileset
    bruma en BG_Far -- si los dos conjuntos alguna vez discreparan, ese
    test fallaria con un ``KeyError`` al buscar un nombre ausente en
    ``mapping``.
    """
    bg_far, bg_mid = _blank(), _blank()
    compose_sky(bg_far=bg_far, bg_mid=bg_mid)
    return frozenset(nombre for fila in bg_far for nombre in fila if nombre is not None)


def compose_celestial(*, bg_mid: Layer) -> None:
    """"Vista real" de la ronda 6: puebla el ~65% superior del cuadro de 800x600.

    El motor renderiza a 800x600 (settings.py) y el mapa mide 2400x608, asi
    que el jugador ve TODA la altura del mapa a la vez -- el cielo sobre la
    linea de arboles NO esta fuera de camara (como asumian las rondas 1-5 con
    una ventana de 320x224) sino totalmente en pantalla. Esto lo rellena con
    una vista de crepusculo compuesta, todo como overlays TRANSPARENTES sobre
    BG_Mid (se compone sobre la rampa de BG_Far, sin parche de tono base):

      * UNA luna grande y baja, asimetrica (columnas 33-35, filas 6-8), en la ventana de spawn;
      * cumulos de estrellas mas densos a traves del cielo alto de las tres ventanas;
      * bancos de nubes altas y frias en dos altitudes (filas ~4-6 y ~14-16),
        algunos de 6 tiles de largo, repartidos para que CADA ventana de 800px
        enmarque interes de nubes;
      * una linea de silueta de cresta/campus lejano (filas 18-20) -- el mas
        DISTANTE de tres planos de profundidad (esta cresta -> el bosque
        cercano -> la escena cercana).

    Las tres ventanas de camara son exactamente las columnas [0,50] (spawn),
    [50,100] (arcos), [100,150] (arena) en esta resolucion, asi que las
    colocaciones de abajo se eligen para que cada ventana obtenga una luna O
    nubes, estrellas, y la cresta.
    """
    # --- luna protagonista (bloque de 3x3), arriba-izquierda en la ventana de spawn --------------
    place_block(bg_mid, "moon", 3, 3, col0=33, row0=6)

    # --- cumulos de estrellas, repartidos por el cielo alto de LAS CUATRO ventanas (r11) ---
    stars = [(4, 2), (14, 8), (23, 3), (44, 5), (9, 12), (47, 11),          # spawn
             (55, 3), (66, 9), (78, 2), (90, 6), (95, 12), (60, 14),        # carport
             (104, 4), (116, 8), (128, 3), (140, 6), (110, 13), (146, 11),  # arcos
             (158, 4), (170, 9), (182, 3), (196, 6), (164, 13), (200, 11)]   # arena
    for i, (x, y) in enumerate(stars):
        put(bg_mid, x, y, "star_cluster_a" if i % 2 == 0 else "star_cluster_b")

    # --- bancos de nubes altas y frias en dos altitudes (tiras de l/m/r de 3
    # tiles; un par duplicado a 6 tiles). Cada ventana de ~800px recibe un
    # banco alto (filas 4-6) y uno medio (14-16) para que ninguna porcion del
    # cielo quede vacia (ronda-11: extendido a la arena).
    cloud_banks = [(6, 5), (44, 4), (20, 15),               # spawn
                   (58, 5), (61, 5), (82, 15), (88, 16),    # carport (58/61 = 6 tiles)
                   (120, 6), (104, 16), (128, 14), (131, 14),  # arcos (128/131 = 6 tiles)
                   (158, 5), (196, 4), (172, 15), (175, 15)]  # arena (172/175 = 6 tiles)
    for x, y in cloud_banks:
        put(bg_mid, x, y, "cloud_high_l")
        put(bg_mid, x + 1, y, "cloud_high_m")
        put(bg_mid, x + 2, y, "cloud_high_r")

    # --- linea de cresta lejana (el plano mas distante): cresta en fila 18,
    # neblina en filas 19-20. Colocada en la banda de cielo purpura S2 para
    # que su tono S2->S3 se lea como "apenas mas claro que el cielo"
    # (perspectiva atmosferica), bien por encima del bosque cercano.
    for x in range(W):
        put(bg_mid, x, 18, pick(["ridge_far_a", "ridge_far_b"], x, 18))
        put(bg_mid, x, 19, "ridge_haze")
        put(bg_mid, x, 20, "ridge_haze")
    # siluetas de campus lejanas asomando sobre la cresta, repartidas por el ancho
    for cx in (12, 40, 70, 106, 138, 168, 198):
        put(bg_mid, cx, 18, "campus_far")


def compose_forest(*, bg_mid: Layer) -> None:
    """Silueta de bosque distante en el horizonte (BG_Mid), detras de los edificios.

    Bajada HASTA la ventana de camara como una linea de arboles delgada de 3
    filas (copa 31, follaje iluminado 32, base con neblina 33) para que se
    lea como una banda distante en el horizonte, no como una pared pesada:
    debajo de ella (fila 34) el crepusculo rosado se muestra hasta el suelo
    cercano en la fila 35, exactamente como en la vineta donde el cesped se
    eleva POR DELANTE del bosque. Las estructuras altas (hastial, cupula del
    gazebo: fila de apice 29) se alzan sobre la linea de arboles hacia la
    puesta de sol. Los tiles de copa son transparentes por encima de su
    silueta, asi que el horizonte calido se muestra a traves de los huecos
    entre copas, y la base con neblina disuelve el bosque en el crepusculo
    (perspectiva atmosferica).
    """
    tops = ["forest_top_a", "forest_top_b", "forest_top_c"]
    for x in range(W):
        if x in ARCOS:
            # ARCOS conserva una linea de arboles/seto CONTINUA entre las
            # casas -- se lee como el patio/corredor cerrado que el director
            # quiere mantener.
            put(bg_mid, x, 31, pick(tops, x, 31))
            put(bg_mid, x, 32, "forest_canopy")
            put(bg_mid, x, 33, "forest_fill")             # transicion verde
            put(bg_mid, x, BASE_ROW, "meadow_base")       # pradera en la fila 34 (sombra de contacto)
        else:
            # PRADERA / ARENA: la vegetacion media son grupos de arboles
            # redondeados SEPARADOS (1-3 filas) con HUECOS DE CIELO entre
            # ellos, sobre una banda de PRADERA VERDE ABIERTA CONTINUA (filas
            # 33-34). La puesta de sol respira a traves de los huecos y el
            # camino de tierra se lee contra el verde -- ninguna pared solida
            # en el termino medio. (Correcciones #1 + #2 del director en
            # ronda-5.)
            # RONDA-8: dentro de ARENA, las agrupaciones altas alrededor del
            # gazebo se DESPEJAN (un claro) con hombros suaves de monticulo
            # bajo en sus bordes, para que la silueta iluminada de la pieza
            # central se lea contra el cielo abierto del crepusculo
            # (feedback del usuario).
            cyc = x % 13                                  # agrupacion de 5 columnas, luego un hueco de 8 columnas
            if x in _ARENA_GLADE_SHOULDER:
                # una sola fila de monticulo bajo: un hombro suave que
                # suaviza el claro hacia la linea de arboles circundante (sin
                # agujero rectangular duro).
                put(bg_mid, x, 32, pick(tops, x, 32))
            elif x not in _ARENA_GAZEBO_GLADE and x not in _CARPORT_GLADE and cyc < 5:
                # monticulo redondeado; la columna central llega a la fila 29
                # -> una agrupacion de 4 filas que se asoma al horizonte
                # calido (punto 5 de ronda-6: bosque cercano de 3-4 filas
                # "donde convenga"), mientras que los HUECOS de 8 columnas
                # quedan vacios para que la puesta de sol siga respirando
                # entre agrupaciones -- ninguna pared solida (rondas 4-5).
                crown = [32, 31, 29, 31, 32][cyc]         # monticulo redondeado (mas alto al centro)
                put(bg_mid, x, crown, pick(tops, x, crown))
                for y in range(crown + 1, 33):            # follaje/relleno hacia abajo hasta la fila 32
                    put(bg_mid, x, y, "forest_canopy" if y == crown + 1 else "forest_fill")
            if x not in _GAZEBO_FOOTPRINT and x not in _CARPORT_GRAVEL:
                # la huella del gazebo de RONDA-9 + la bahia de grava del
                # carport de RONDA-11 se mantienen LIBRES de la banda de
                # pradera (la grava/plaza es el suelo alli).
                put(bg_mid, x, 33, "meadow_far")          # banda de pradera abierta del crepusculo (retrocede)...
                put(bg_mid, x, BASE_ROW, "meadow_base")   # ...la fila 34 lleva la sombra de contacto
            # ...se mantiene LIBRE de la banda de pradera para que sus bases/portal no se entierren;
            # el cielo crepuscular de BG_Far se muestra en los flancos, el cesped de r7 (fila 35) es su piso.


# ===========================================================================
# SUPERFICIE DEL SUELO (Terrain filas 35-37)
# ===========================================================================
def compose_ground(*, terrain: Layer) -> None:
    """Superficie caminable (fila 35) por zona + tierra subterranea (filas 36-37).

    Los umbrales de zona estan conectados a los limites de
    PRADERA/ARCOS/ARENA para que la superficie siga a una zona cuando esta se mueve.
    """
    walk = ["grass_walk_a", "grass_walk_b", "grass_walk_c"]
    for x in range(W):
        if x < PRADERA.start + 3:                          # una franja de cesped abierto en el spawn
            surf = pick(walk, x, GROUND_ROW)
        elif x == PRADERA.start + 3:                       # cesped -> comienza el camino de tierra
            surf = "path_edge_l"
        elif x < CARPORT.start - 4:                         # EL CAMINO (tierra caminable), ahora mas largo
            surf = pick(["dirt_path_a", "dirt_path_b"], x, GROUND_ROW)
        elif x == CARPORT.start - 4:                       # tierra -> cesped (el camino termina en el carport)
            surf = "path_edge_r"
        elif x < ARCOS.start - 2:                           # cesped del CARPORT (cesped caminable; la grava es fondo)
            surf = "grass_walk_bald" if x % 13 == 0 else pick(walk, x, GROUND_ROW)
        elif x < ARCOS.start:                              # cesped -> acera de acceso
            surf = pick(["sidewalk_slab_a", "sidewalk_slab_b"], x, GROUND_ROW)
        elif x < ARENA.start:                              # acera de los arcos
            surf = _sidewalk_variant(x)
        elif x < ARENA.start + 5:                          # acera -> cesped
            surf = "sidewalk_moss" if x % 2 else "sidewalk_slab_c"
        else:                                              # cesped de la explanada de la arena
            surf = "grass_walk_bald" if x % 11 == 0 else pick(walk, x, GROUND_ROW)
        put(terrain, x, GROUND_ROW, surf)
        # tierra subterranea: se oscurece hacia abajo, piedras + raices (fila 36 luego 37)
        put(terrain, x, SUB_ROWS[0], "subsoil_top")
        put(terrain, x, SUB_ROWS[1], "subsoil_deep")

    # EL CAMINO, hecho LEGIBLE (correccion #1 del director en ronda-5): el
    # camino de tierra de la pradera mide 2 tiles de alto donde "se hincha"
    # hacia el espectador y baja a 1 tile (la pradera verde se asoma encima)
    # donde se curva alejandose, para que se lea como un camino de tierra
    # SERPENTEANDO por la pradera -- nace en el spawn (columna 3) y serpentea
    # hacia la derecha. El eje se desplaza en un ciclo de 11 columnas; las
    # costuras cesped/tierra usan tiles path_edge.
    px0, px1 = PRADERA.start + 4, CARPORT.start - 4
    for x in range(px0, px1):
        seg = (x - px0) % 11
        if seg < 5:                                        # hinchazon: la tierra sube a la fila 34
            if seg == 0:
                put(terrain, x, BASE_ROW, "path_edge_l")   # pradera(izquierda) -> camino(derecha)
            elif seg == 4:
                put(terrain, x, BASE_ROW, "path_edge_r")   # camino(izquierda) -> pradera(derecha)
            else:
                put(terrain, x, BASE_ROW, pick(["dirt_path_a", "dirt_path_b"], x, BASE_ROW))
        # si no, seg 5-10: el camino se curva alejandose -> la fila 34 sigue siendo pradera de fondo (meadow_base)


def _sidewalk_variant(x: int) -> str:
    """Mezcla de pavimento desgastado para la acera de los arcos."""
    m = x % 9
    if m == 0:
        return "sidewalk_crack"
    if m == 3:
        return "sidewalk_moss"
    if m == 6:
        return "sidewalk_broken_corner"
    return pick(["sidewalk_slab_a", "sidewalk_slab_b", "sidewalk_slab_c"], x, GROUND_ROW)


# ===========================================================================
# ZONA: PRADERA [0, 50)
# ===========================================================================
def compose_pradera(*, bg_near: Layer, terrain_detail: Layer, fg: Layer) -> None:
    """Pradera: arbol grande, casas distantes, cerca caida, tendedero, mechones."""
    # arbol grande (BG_Near, detras del jugador), enraizado en el suelo. Su
    # propio bloque ya lleva el tronco + raices, asi que no se estampa ningun
    # tile de tronco extra (eso se leia como una caja separada bajo el follaje).
    place_block(bg_near, "tree_c", 4, 4, col0=PRADERA.start + 6, row0=BASE_ROW - 3, sep="")
    # RONDA-11: un SEGUNDO arbol grande en la pradera ensanchada para que la
    # pradera mas larga mantenga interes hacia la derecha (usuario: "cada
    # zona un poco mas extensa").
    place_block(bg_near, "tree_c", 4, 4, col0=PRADERA.start + 52, row0=BASE_ROW - 3, sep="")

    # una casa cercana e iluminada DENTRO de la ventana de spawn (columnas
    # 11-13, BG_Near) para que el cuadro de apertura tenga escala + una senal
    # calida de vida, no solo un arbol solitario
    bung_spawn = PRADERA.start + 11
    place_block(bg_near, "bung", 3, 3, col0=bung_spawn, row0=BASE_ROW - 2)
    put(bg_near, bung_spawn + 1, BASE_ROW - 1, "bung_win_lit")

    # dos casas mas distantes con ventanas iluminadas / tapiadas (BG_Near)
    bung_a = PRADERA.start + 26
    place_block(bg_near, "bung", 3, 3, col0=bung_a, row0=BASE_ROW - 2)
    put(bg_near, bung_a + 1, BASE_ROW - 1, "bung_win_lit")             # sobrescribe una celda del cuerpo -> ventana
    bung_b = PRADERA.start + 34
    place_block(bg_near, "bung", 3, 3, col0=bung_b, row0=BASE_ROW - 2)
    put(bg_near, bung_b + 1, BASE_ROW - 1, "bung_win_board")

    # cerca con tramos caidos (Terrain_Detail, en el suelo); empieza en la
    # columna 15 para que despeje la casa del spawn. Las columnas caidas se
    # mantienen absolutas (ver nota de zona)
    for x in range(PRADERA.start + 15, PRADERA.start + 25):
        name = "fence_fallen" if x in (18, 19) else pick(["fence_a", "fence_b", "fence_c"], x, BASE_ROW)
        put(terrain_detail, x, BASE_ROW, name)

    # tendedero tendido entre dos postes inclinados (bajo, cerca del suelo)
    cl0 = PRADERA.start + 40
    put(terrain_detail, cl0, BASE_ROW - 1, "clothesline_l")
    put(terrain_detail, cl0 + 1, BASE_ROW - 1, "clothesline_m")
    put(terrain_detail, cl0 + 2, BASE_ROW - 1, "clothesline_r")

    # densidad del corredor (FIX 3 del director): props de abandono +
    # arbustos redondeados PUNTUALES salpicados en el cesped (no una banda de
    # seto continua, sin cubos flotantes).
    put(terrain_detail, PRADERA.start + 2, BASE_ROW, "branch_fallen")   # prop de la ventana de spawn
    put(terrain_detail, PRADERA.start + 9, BASE_ROW, "branch_fallen")
    put(terrain_detail, PRADERA.start + 57, BASE_ROW, "branch_fallen")  # r11: rellena la pradera ensanchada
    for bx in (PRADERA.start + 20, PRADERA.start + 32, PRADERA.start + 43,
               PRADERA.start + 50, PRADERA.start + 60):                 # r11: mas arbustos hacia la derecha
        put(terrain_detail, bx, BASE_ROW, "bush")                       # arbustos individuales, enraizados en el suelo
    place_bench(terrain_detail, PRADERA.start + 46)                     # banca rota en la pradera
    scatter_leaves(terrain_detail, (PRADERA.start + 7, PRADERA.start + 15, PRADERA.start + 37,
                                    PRADERA.start + 55, PRADERA.start + 62))

    # mechones de cesped en primer plano (FG_Overlay), ahora ESCASOS (cada 6
    # columnas) para que se lean como bordes junto al camino de tierra en vez
    # de un fleco verde que lo entierra -- el camino debe seguir siendo
    # legible (correccion #1 del director en ronda-5).
    scatter_fg_grass(fg, range(PRADERA.start + 1, PRADERA.stop, 6))


# ===========================================================================
# ZONA: CARPORT [65, 95)  (ronda-11: "el lugar donde estaban los carros")
# ===========================================================================
def compose_carport(*, bg_near: Layer, terrain_detail: Layer, fg: Layer) -> None:
    """La bahia de estacionamiento: cochera oscura de techo corrugado sobre
    postes negros encima de una bahia de grava, un sedan plateado + una
    pickup blanca estacionados debajo, un tractor naranja al lado.

    La estructura del carport + la grava van en BG_Near (detras del
    jugador); los vehiculos y los props del suelo van en Terrain_Detail (por
    delante de los postes/grava); la hiedra, las hojas del techo y los
    mechones de borde van en FG_Overlay. La superficie caminable (Terrain
    fila 35) sigue siendo cesped -- la grava es puramente el telon visual de
    la bahia (tarea: "la gravilla es el fondo visual del aparcadero ... no
    cambia la colision"), y compose_forest ya despejo un claro para que la
    silueta oscura del carport contraste contra el cielo abierto del crepusculo.
    """
    # bahia de grava oscura (BG_Near, detras de los vehiculos) con un bordillo de concreto iluminado
    for x in _CARPORT_GRAVEL:
        put(bg_near, x, BASE_ROW - 1, "gravel")            # fila 33
        put(bg_near, x, BASE_ROW, "gravel_curb")           # fila 34 (borde de concreto frontal)

    # techo del carport (10x2) + postes de metal NEGRO hasta bases de concreto agrietadas
    place_block(bg_near, "carroof", _CARPORT_ROOF_W, 2, col0=_CARPORT_C0, row0=BASE_ROW - 5)
    for pc in _CARPORT_POSTS:
        for r in range(BASE_ROW - 4, BASE_ROW):            # filas 30..33 (fuste del poste)
            put(bg_near, pc, r, "carport_post")
        put(bg_near, pc, BASE_ROW, "carport_post_base")    # fila 34 (poste + basa)

    # vehiculos estacionados (Terrain_Detail, dibujados sobre los
    # postes/grava), pies en la fila 34
    place_block(terrain_detail, "sedan", 4, 2, col0=_CARPORT_C0 + 1, row0=BASE_ROW - 1)   # 72-75
    place_block(terrain_detail, "pickup", 4, 2, col0=_CARPORT_C0 + 5, row0=BASE_ROW - 1)  # 76-79
    place_block(terrain_detail, "tractor", 3, 2, col0=_CARPORT_C1 + 3, row0=BASE_ROW - 1)  # 83-85

    # detalles de abandono: una llanta gastada apoyada en el ultimo poste, una
    # lampara apagada junto a la entrada, hojas a la deriva + un par de
    # arbustos enmarcando la bahia.
    put(terrain_detail, _CARPORT_C1 + 1, BASE_ROW, "tire")             # col 81 (contra el poste 80)
    put(terrain_detail, CARPORT.start + 3, BASE_ROW - 1, "lamp_top")   # col 68 (lampara inclinada)
    put(terrain_detail, CARPORT.start + 3, BASE_ROW, "lamp_base")
    put(terrain_detail, CARPORT.start + 1, BASE_ROW, "bush")           # col 66 (arbusto de acceso)
    put(terrain_detail, ARCOS.start - 3, BASE_ROW, "bush")             # col 92 (arbusto de salida)
    scatter_leaves(terrain_detail, (CARPORT.start + 6, ARCOS.start - 5))
    # Tarea 11 ("algo se perdio" del Acto 2): banco roto junto a
    # Light_AbandonoLamp_01 (_LIGHTS, col=CARPORT.start+20=85). El plan pedia
    # CARPORT.start + 20 (col 85), pero esa columna es la ESQUINA del bloque
    # del tractor (place_block col0=_CARPORT_C1+3=83, ancho 3 -> cols 83-85,
    # fila BASE_ROW incluida): sobrescribiria su tile visible. Se desplaza
    # una columna al este, a _CARPORT_C1 + 6 (col 86), libre en todas las
    # capas -- sigue "junto a" la lampara apagada (una columna de distancia).
    place_bench(terrain_detail, _CARPORT_C1 + 6)

    # hiedra trepando el tractor (FG_Overlay) + hojas acumuladas en los techos de los autos
    put(fg, _CARPORT_C1 + 5, BASE_ROW - 2, "ivy_b")                    # col 85, enredadera hacia la parte trasera
    put(fg, _CARPORT_C1 + 5, BASE_ROW - 1, "ivy_a")
    put(fg, _CARPORT_C0 + 2, BASE_ROW - 1, pick(["leaves_drift_a", "leaves_drift_b"], _CARPORT_C0, 0))  # techo del sedan
    put(fg, _CARPORT_C0 + 6, BASE_ROW - 1, pick(["leaves_drift_a", "leaves_drift_b"], _CARPORT_C1, 0))  # techo de la cabina de la pickup

    # mechones de cesped en primer plano escasos enmarcando la bahia (se salta el tramo de grava/vehiculos)
    reserved = set(_CARPORT_GRAVEL) | set(range(_CARPORT_C1 + 3, _CARPORT_C1 + 6))
    scatter_fg_grass(fg, [x for x in range(CARPORT.start + 2, CARPORT.stop, 6) if x not in reserved])


# ===========================================================================
# ZONA: ARCOS [95, 155)
# ===========================================================================
# Arcos hastiales transitables. Cada hastial de 6x6 se apoya en BASE_ROW; su
# abertura de arco ocupa las celdas del bloque (columna 2..3, fila 4..5).
# Perforamos esas celdas fuera de Terrain (dejandolas transparentes) para que
# un resplandor calido de portal lejano colocado en BG_Near se muestre A
# TRAVES, luego dibujamos el revelado de piedra cercano en FG_Overlay para
# que el jugador pase dentro del portal. Un hastial distante en el callejon
# entre los dos da el telescopio (arco-dentro-de-arco) de profundidad.
_ARCH_SKIP = {(2, 4), (3, 4), (2, 5), (3, 5)}


def _passable_arch(bg_near: Layer, terrain: Layer, fg: Layer, col0: int) -> None:
    row0 = BASE_ROW - 5                                   # 6 de alto -> filas 29..34
    place_block(terrain, "hast", 6, 6, col0=col0, row0=row0, skip=_ARCH_SKIP)
    ocx, orow = col0 + 2, BASE_ROW - 1                    # abertura: columnas ocx..ocx+1, filas orow..BASE_ROW
    # resplandor calido de portal lejano revelado a traves de la abertura perforada (BG_Near)
    for dx in (0, 1):
        put(bg_near, ocx + dx, orow, "arch_glow_top")
        put(bg_near, ocx + dx, BASE_ROW, "arch_glow_bottom")
    # revelado de piedra cercano dibujado POR DELANTE del jugador (FG_Overlay), 3 de ancho x 2 de alto
    faces_top = ("arch_front_l_top", "arch_front_m_top", "arch_front_r_top")
    faces_bot = ("arch_front_l_bot", "arch_front_m_bot", "arch_front_r_bot")
    for i in range(3):
        put(fg, col0 + 1 + i, orow, faces_top[i])
        put(fg, col0 + 1 + i, BASE_ROW, faces_bot[i])


def compose_arcos(*, bg_near: Layer, terrain: Layer, terrain_detail: Layer, fg: Layer) -> None:
    """Dos arcos transitables con un telescopio de un arco distante, lampara y banca."""
    # RONDA-11: los dos arcos frontales se espacian MAS ANCHO (era +4/+23 en
    # una zona de 50 columnas; ahora +5/+38 en una zona de 60 columnas) para
    # que el arco telescopio distante entre ellos tenga espacio para respirar,
    # con la linea de arboles/seto de patio continua corriendo entre ellos.
    _passable_arch(bg_near, terrain, fg, col0=ARCOS.start + 5)         # hastial frontal #1 (100)
    _passable_arch(bg_near, terrain, fg, col0=ARCOS.start + 38)        # hastial frontal #2 (133)

    # hastial distante en el callejon entre ellos (BG_Near) -> profundidad de telescopio
    place_block(bg_near, "hast", 6, 6, col0=ARCOS.start + 22, row0=BASE_ROW - 5)   # 117

    # lampara inclinada (apagada) enraizada en la acera
    put(terrain_detail, ARCOS.start + 2, BASE_ROW - 1, "lamp_top")
    put(terrain_detail, ARCOS.start + 2, BASE_ROW, "lamp_base")

    # banca rota en el suelo en el callejon/patio entre los arcos
    place_bench(terrain_detail, ARCOS.start + 28)

    # hojas a la deriva sobre el pavimento, repartidas a lo largo del corredor mas ancho
    scatter_leaves(terrain_detail, (ARCOS.start + 13, ARCOS.start + 46, ARCOS.start + 54))


# ===========================================================================
# ZONA: ARENA [155, 205)
# ===========================================================================
def compose_arena(*, bg_mid: Layer, bg_near: Layer, terrain_detail: Layer, fg: Layer) -> None:
    """Explanada de cesped con el gazebo centrado, su plaza de piedra, luciernagas, hojas."""
    # pieza central del gazebo (BG_Near), 7x6 centrado ~columnas 122-128, enraizado en el suelo
    place_block(bg_near, "gaz", 7, 6, col0=ARENA.start + 22, row0=BASE_ROW - 5)

    # RONDA-10 (usuario: "hay que construir su parte faltante" / no dejar el
    # kiosco cortado): sentar el gazebo sobre una PLAZA/PLINTO de piedra
    # calida rellenando la huella despejada en la fila base (BG_Mid, DETRAS
    # del gazebo para que se dibuje sobre el y la plaza solo se muestre en la
    # rendija transparente de la base del kiosco + sus flancos). Esto cierra
    # el vacio rosado de cielo a nivel del suelo (su terraza BAJA = el cierre
    # de la directiva #3 que pide 1 fila pegada al suelo) mientras el cielo
    # crepuscular sigue respirando POR ENCIMA de la terraza y a traves del
    # interior del kiosco. Los tiles de escalon rematan los extremos. Las
    # bases de piedra gaz_* se asientan sobre el borde iluminado -> el kiosco
    # se lee sentado.
    put(bg_mid, _GAZEBO_FOOTPRINT.start, BASE_ROW, "plaza_step_l")          # col 120 (extremo izquierdo)
    for x in range(_GAZEBO_FOOTPRINT.start + 1, _GAZEBO_FOOTPRINT.stop - 1):  # 121..129
        put(bg_mid, x, BASE_ROW, "plaza_slab")
    put(bg_mid, _GAZEBO_FOOTPRINT.stop - 1, BASE_ROW, "plaza_step_r")       # col 130 (extremo derecho)

    # ambiente de PLAZOLETA (directiva #2): dos ornamentos bajos de flanco --
    # lamparas inclinadas apagadas justo FUERA del kiosco (columnas 121/129)
    # para que nada cubra el portal -- mas un par de derivas de hojas caidas
    # a un lado. Bajos, hacia los flancos.
    for lc in (_GAZEBO_C0 - 1, _GAZEBO_C1 + 1):                             # columnas 121, 129
        put(terrain_detail, lc, BASE_ROW - 1, "lamp_top")
        put(terrain_detail, lc, BASE_ROW, "lamp_base")
    scatter_leaves(terrain_detail, (_GAZEBO_C1 + 2, _GAZEBO_C1 + 3))        # deriva de hojas de la plazoleta (130-131)

    # explanada enmarcada por arbustos redondeados PUNTUALES sobre el cesped (no una banda de seto)
    for bx in (ARENA.start + 2, ARENA.start + 6, ARENA.stop - 3, ARENA.stop - 7):
        put(terrain_detail, bx, BASE_ROW, "bush")

    # prop de banca rota independiente
    place_bench(terrain_detail, ARENA.start + 12)

    # luciernagas a la deriva sobre la arena (FG_Overlay); las coordenadas del
    # enjambre son un salpicado decorativo ajustado finamente que se mantiene
    # absoluto dentro de la zona (ver nota de zona).
    # RONDA-8: el enjambre esta SESGADO hacia el gazebo (columnas 118-133)
    # para reforzar el foco en la pieza central iluminada, adelgazandose
    # hacia los bordes de la arena; cada luciernaga ya lleva un halo calido
    # de 1px. Se mantiene en 9 en total (moderacion).
    fireflies = [(159, 31), (167, 28), (173, 33), (176, 31), (181, 27),
                 (184, 32), (188, 30), (179, 29), (195, 29)]
    for x, y in fireflies:
        put(fg, x, y, "firefly")

    # hojas a la deriva + mechones de cesped en primer plano. RONDA-9: los
    # mechones de cesped en FG SALTAN la huella del gazebo para que nada
    # brote frente a sus bases/portal (la queja restante del usuario); los
    # mechones siguen salpicando el resto de la arena.
    scatter_fg_grass(fg, [x for x in range(ARENA.start + 1, ARENA.stop, 3)
                          if x not in _GAZEBO_FOOTPRINT])
    scatter_leaves(terrain_detail, (ARENA.start + 6, ARENA.start + 20, ARENA.start + 36, ARENA.start + 48))


# ===========================================================================
# PLATAFORMAS (bordes de un solo sentido) con decoracion coherente anclada al suelo.
# Cada entrada: (x, y, w) en pixeles + el tramo de columnas de tile de su seto de soporte.
# ===========================================================================
# RONDA-11: las 5 plataformas (2 de corredor + 3 de arena) mantienen sus
# ALTURAS pero se redistribuyen en las zonas ensanchadas/desplazadas (los
# bordes del corredor en la pradera + corredor de arcos mas largos; los 3
# bordes de la arena desplazados +55 columnas / +880px con la arena,
# manteniendo su disposicion alrededor del gazebo). El contrato del test fija
# solo que EXISTAN 2 plataformas de corredor + 3 de arena, no sus posiciones x.
_PLATFORMS: list[tuple[int, int, int]] = [
    (768, 488, 48),      # corredor C1  (columnas 48-50, pradera)
    (1776, 472, 48),     # corredor C2  (columnas 111-113, callejon de arcos, libre de los arcos)
    (2576, 488, 64),     # arena P1     (columnas 161-164)
    (2768, 472, 48),     # arena P2     (columnas 173-175, a la izquierda del gazebo)
    (2992, 488, 48),     # arena P3     (columnas 187-189, a la derecha del gazebo)
]


def place_arbor(layer: Layer, x0: int, x1: int, r_top: int) -> None:
    """Un cenador/pergola de jardin soportando un borde de un solo sentido desde r_top hasta el suelo.

    Una viga transversal caminable y frondosa (r_top) sobre dos postes en los
    extremos, con un enrejado de vid ABIERTO entre ellos para que la puesta
    de sol/bosque se muestren a traves (nunca una torre solida), enraizado en
    una jardinera de piedra baja en BASE_ROW. Compuesto sobre el cielo en
    Terrain_Detail; no lleva colision propia (el borde es el objeto Platform
    del mapa), asi que el jugador pasa a traves del cuerpo aireado.
    """
    for x in range(x0, x1):
        put(layer, x, r_top, "arbor_beam")
        for y in range(r_top + 1, BASE_ROW):
            put(layer, x, y, "arbor_post" if x in (x0, x1 - 1) else "arbor_lattice")
        put(layer, x, BASE_ROW, "arbor_base")


def compose_platform_decor(*, terrain_detail: Layer) -> None:
    """Dibuja un cenador de jardin bajo cada plataforma para que ningun borde flote."""
    for x, y, w in _PLATFORMS:
        c0 = x // TILE
        c1 = (x + w) // TILE
        r_top = y // TILE                                 # viga justo debajo del borde
        place_arbor(terrain_detail, c0, c1, r_top)


# ===========================================================================
# LUCES (feature B, spec 2026-07-29 "adopcion V2: sfx/luces/weakpoints" sec.
# 2). Cinco objetos ``type="Light"``: cuatro lamparas calidas ancladas al
# tile exacto que compose_carport()/compose_arcos()/compose_arena() ya
# estampan con un par ``lamp_top``/``lamp_base`` (decoracion de "lampara
# apagada" que ya existe -- iluminarla es una lectura literal de un prop ya
# dibujado, no arte nuevo), mas un acento frio en el oculo del hastial
# distante de ARCOS (la pista de profundidad del gable "telescopio"). No se
# inventa ningun pixel: cada ``col``/``row`` de abajo es una formula sobre
# las MISMAS constantes de zona que usa ``compose_*()`` para colocar su
# lampara (citado por entrada), asi que un futuro desplazamiento de zona
# (p. ej. ensanchar CARPORT de nuevo) lleva la luz consigo.
# ``StageLoader._handle_light`` lee el CENTRO de un rectangulo de Tiled, y
# una caja de TILE x TILE (16x16) enraizada en ``(col*TILE, row*TILE)``
# centra exactamente en ese tile -- asi que tampoco hace falta mantener
# sincronizada ninguna matematica de pixeles por separado.
# ===========================================================================
_LAMP_ROW = BASE_ROW - 1   # 33: la fila donde se asienta cada par lamp_top/lamp_base

_LIGHTS: list[dict] = [
    dict(
        obj_id=5, name="Light_CarportLamp_01", anchor="lamp",
        col=CARPORT.start + 3, row=_LAMP_ROW,       # lamp_top de compose_carport()
        radius="90", color="warm", intensity="0.75",
        flicker=True, flicker_speed="4.0", flicker_amount="0.20",
    ),
    dict(
        obj_id=6, name="Light_ArcosLamp_01", anchor="lamp",
        col=ARCOS.start + 2, row=_LAMP_ROW,         # lamp_top de compose_arcos()
        radius="80", color="warm", intensity="0.65",
        flicker=True, flicker_speed="4.0", flicker_amount="0.20",
    ),
    dict(
        obj_id=7, name="Light_ArenaLampWest_01", anchor="lamp",
        col=_GAZEBO_C0 - 1, row=_LAMP_ROW,          # lamp_top de compose_arena() (flanco oeste)
        radius="100", color="warm", intensity="0.85",
        flicker=True, flicker_speed="4.5", flicker_amount="0.22",
    ),
    dict(
        obj_id=8, name="Light_ArenaLampEast_01", anchor="lamp",
        col=_GAZEBO_C1 + 1, row=_LAMP_ROW,          # lamp_top de compose_arena() (flanco este)
        radius="100", color="warm", intensity="0.85",
        flicker=True, flicker_speed="4.5", flicker_amount="0.22",
    ),
    dict(
        obj_id=9, name="Light_ArcosOculo_01", anchor="oculo",
        col=ARCOS.start + 22, row=31,               # bloque de hastial distante de compose_arcos() (telescopio)
        radius="140", color="cold", intensity="0.5",
        flicker=False, flicker_speed=None, flicker_amount=None,
    ),
    # TAREA 3 (plan 2026-08-24 "La Peregrinacion al Venado"): 7 luces nuevas
    # con densidad y temperatura de color DECRECIENTES a lo largo del
    # corredor, de "el hogar" (Acto 1, calidas) a "el umbral" (Acto 3, frias
    # y luego de sangre justo antes de la arena). A diferencia de las cinco
    # de arriba, estas NO se anclan sobre un tile ``lamp_top`` ya estampado
    # por ningun ``compose_*()`` -- por eso su ``anchor`` NO es la cadena
    # literal "lamp": ``test_light_positions_match_lamp_props`` (arriba en el
    # archivo de tests) itera TODO ``_LIGHTS`` y, para cualquier entrada con
    # ``anchor == "lamp"``, exige que el tile bajo su centro sea
    # ``lamp_top`` real. Estas son acentos atmosfericos puros (glow ambiental
    # sobre la pradera/cochera/arcos, sin prop de lampara dedicada) -- un
    # ``anchor`` descriptivo distinto documenta la intencion con precision y
    # deja ese candado de regresion intacto para las 5 luces originales que
    # si estan ancladas a una lampara dibujada. ``anchor`` no lo lee
    # ``_light_object_xml`` (es metadato puro para el test), asi que este
    # cambio no toca el XML emitido salvo el rectangulo/propiedades del
    # objeto Light en si.
    # INSTRUCCION FUTURA: si una tarea posterior estampa un ``lamp_top`` real
    # (con ``put(terrain_detail, ...)``) exactamente bajo alguna de estas
    # luces (p. ej. la Tarea 11 y el banco roto de ``Light_AbandonoLamp_01``),
    # su ``anchor`` debe reconvertirse a la cadena literal "lamp" en ese
    # momento para heredar el candado de ``test_light_positions_match_lamp_props``
    # -- no antes, porque hoy fallaria contra un tile que no existe.
    dict(
        obj_id=30, name="Light_HogarLampA_01", anchor="hogar",
        col=PRADERA.start + 12, row=_LAMP_ROW,
        radius="70", color="warm", intensity="0.65",
        flicker=True, flicker_speed="3.5", flicker_amount="0.18",
    ),
    dict(
        obj_id=31, name="Light_HogarLampB_01", anchor="hogar",
        col=PRADERA.start + 40, row=_LAMP_ROW,
        radius="70", color="warm", intensity="0.60",
        flicker=True, flicker_speed="3.5", flicker_amount="0.18",
    ),
    dict(
        obj_id=32, name="Light_HogarLampC_01", anchor="hogar",
        col=PRADERA.start + 58, row=_LAMP_ROW,   # cerca del limite con CARPORT (col 65): mas tenue
        radius="60", color="warm", intensity="0.50",
        flicker=True, flicker_speed="3.5", flicker_amount="0.18",
    ),
    dict(
        obj_id=33, name="Light_AbandonoLamp_01", anchor="abandono",
        col=CARPORT.start + 20, row=_LAMP_ROW,   # junto al banco roto nuevo de la Tarea 11
        radius="55", color="warm", intensity="0.40",   # mas tenue que CarportLamp_01 (0.75): decae
        flicker=True, flicker_speed="2.5", flicker_amount="0.25",
    ),
    dict(
        # anchor propio ("umbral_frio", no "oculo") para no confundirse con
        # el oculo real del hastial distante (Light_ArcosOculo_01, arriba) --
        # metadato puro, mismo motivo que el resto del bloque.
        obj_id=34, name="Light_UmbralFrio_01", anchor="umbral_frio",
        col=ARCOS.start + 35, row=_LAMP_ROW,
        radius="90", color="cold", intensity="0.35",
        flicker=False, flicker_speed=None, flicker_amount=None,
    ),
    dict(
        obj_id=35, name="Light_UmbralSangre_01", anchor="umbral_sangre",
        col=ARCOS.start + 50, row=_LAMP_ROW,   # col150 -> x=2320, dentro del tramo final del Acto 3
        radius="45", color="blood", intensity="0.30",
        flicker=True, flicker_speed="6.0", flicker_amount="0.30",
    ),
    dict(
        obj_id=36, name="Light_UmbralSangre_02", anchor="umbral_sangre",
        col=ARCOS.start + 58, row=_LAMP_ROW,   # col153 -> x=2448, justo antes de la arena
        radius="40", color="blood", intensity="0.25",
        flicker=True, flicker_speed="6.0", flicker_amount="0.30",
    ),
]


def _light_object_xml(spec: dict) -> str:
    """Un objeto ``type="Light"`` a partir de una entrada de ``_LIGHTS``
    (formato copiado del TMX de referencia del profesor,
    ``reference/v2_boss_profesor/maps/boss_venado.tmx`` -- un rectangulo del
    tamano de un TILE con radius/color/intensity/flicker* como
    ``<properties>`` tipadas)."""
    x, y = spec["col"] * TILE, spec["row"] * TILE
    props = (
        _prop("radius", spec["radius"], "float", "    ")
        + _prop("color", spec["color"], "string", "    ")
        + _prop("intensity", spec["intensity"], "float", "    ")
    )
    if spec["flicker"]:
        props += (
            _prop("flicker", "true", "bool", "    ")
            + _prop("flicker_speed", spec["flicker_speed"], "float", "    ")
            + _prop("flicker_amount", spec["flicker_amount"], "float", "    ")
        )
    return (
        f'  <object id="{spec["obj_id"]}" name="{spec["name"]}" type="Light" '
        f'x="{x}" y="{y}" width="{TILE}" height="{TILE}">\n'
        '   <properties>\n'
        + props +
        '   </properties>\n'
        '  </object>\n'
    )


# TAREA 9 (plan 2026-08-24 "La Peregrinacion al Venado"): cutscene de
# presentacion. `StageScene.on_enter()` ya llama `_montar_director_de_escenas()`
# y `StageScene.update()` ya llama `self._actualizar_escenas(dt)`
# (cinematicas.py) para TODA escena -- incluida la nuestra, que hereda de
# `StageScene` sin sobrescribir ninguno de los dos. No hace falta codigo
# nuevo en `boss_venado_scene.py`: basta con declarar el objeto `Cutscene`
# aqui, en el generador del TMX.
#
# La orden `sonido` del lenguaje de guion (`cutscene_guion.py:_orden_sonido`)
# se OMITE a proposito: emite el nombre de evento tal cual por el bus
# (`SonidoAction.start()` -> `bus.emit(evento)`), sin validarlo contra
# ningun `Events.SFX_*` ya cableado en `sonido.py`. Ninguno de los eventos
# de sonido existentes encaja semanticamente con "presentacion del jefe", y
# escribir uno indebidamente (o inventar un nombre que nadie escucha) seria
# un guion silenciosamente roto disfrazado de sonido -- se prefiere omitirlo
# a fabricar una senal falsa. Desviacion documentada de la lista de ejemplo
# del spec S3.7 (SonidoAction ahi era un ejemplo generico, no obligatorio).
#
# CORRECCION 2026-08-25 (verificacion visual del coordinador contra la
# sonda `reports\mcp_filmstrip\20260825_052131_sonda_t9_cutscene_apertura`,
# idle seed 1, f16-f160) -- dos hallazgos con evidencia de codigo, no
# supuestos:
#
# (a) El paneo `camara 250 180 1.4` es IMPERCEPTIBLE. `StageScene.update()`
#     (stage_scene.py:775-779) corre `_actualizar_escenas(dt)` -> como
#     `bloquea=false`, `en_escena` da `False` -> `_update_camera_map(dt)`
#     corre IGUAL ese mismo fotograma y sobreescribe `camera.offset`, que
#     `CameraMoveAction.update()` (cutscene_system.py:131-137) acababa de
#     escribir un instante antes. La camara de seguimiento gana SIEMPRE,
#     cada fotograma: el paneo nunca llega a verse. Retirado (sustituido
#     por `esperar`, tal como sugirio el coordinador) -- es la "pugna" que
#     el propio coordinador anticipo mirando la tira.
#
# (b) El "panel de UI grande enmarcado con una cajita de texto dentro" que
#     parecia chrome de esta cutscene NO lo es. Leido `cutscene_system.py`
#     entero: para nuestro guion (esperar/temblor/esperar) `CutsceneScript.
#     draw()` (cutscene_system.py:520-545) no dibuja NADA -- `bandas=False`
#     porque `bloquea=false`, y ni `WaitAction` ni `TemblorAction`
#     sobreescriben `draw()` (heredan el no-op de `CutsceneAction.draw()`).
#     El panel real son DOS overlays del motor, INCONDICIONALES en TODO
#     `on_enter()` de CUALQUIER escenario, sin relacion alguna con el
#     objeto `Cutscene` del TMX: `ScreenBanner` (stage_scene.py:579-583,
#     dispara siempre que `stage_data.stage_name` no este vacio -- aqui
#     "VENADO" -- 2.9s: 0.5s entrada + 2.0s espera + 0.4s salida, el marco
#     dorado ancho) y `TutorialOverlay.show("move", duration=6.0)`
#     (stage_scene.py:636, la cajita "TIP" con los controles de
#     movimiento -- confirmado letra por letra contra
#     `tutorial_overlay.py:TUTORIAL_TIPS["move"]`). Ambos aparecerian
#     IGUAL con o sin este objeto `Cutscene` en el mapa; se solapan con el
#     guion por pura coincidencia de arranque.
#
# Decision: no se convierte esto en tarjeta de titulo con la orden `texto`.
# `DialogueAction` (lo que produce `texto` en este parser,
# cutscene_guion.py:211-217) dibuja una caja de dialogo AL PIE de la
# pantalla (no el panel observado) y con `duration=0.0` fijo -- la sintaxis
# del guion no admite pasarle un tiempo -- se queda esperando ENTER/SPACE
# INDEFINIDAMENTE (`DialogueAction.update`, cutscene_system.py:163-172): un
# bot que nunca pulsa esas teclas dejaria esa caja colgada en pantalla toda
# la pelea, precisamente el "chrome intrusivo" que se queria evitar, solo
# que esta vez si causado por nosotros. La alternativa con duracion real,
# `dialogo <arbol>` (`DialogoArbolAction`), exige un arbol JSON en
# `data/dialogues/boss_venado.json` -- fuera de las zonas editables del
# proyecto (CLAUDE.md). El nombre del nivel YA se muestra gratis por
# `ScreenBanner` en cada entrada al escenario, sin ningun codigo nuestro.
# Se conserva el `temblor` (funciona de verdad, es sutil, y "screen shake"
# es un criterio de bonus explicito de la rubrica del boss) como el unico
# efecto de apertura que aporta esta cutscene.
# Guion orden por orden (2026-08-25) -- cada linea con su porque:
#   esperar 0.6   -- asentado: deja que el jugador vea el escenario un
#                    instante ANTES del acento, en vez de que el temblor
#                    llegue en el fotograma cero pisando el fundido de
#                    entrada de la escena (start_fade_in(0.5), stage_scene.
#                    py:509) y el propio ScreenBanner, que recien empieza a
#                    deslizarse.
#   temblor 0.18 3.0
#                 -- el UNICO efecto real de esta cutscene (ver el bloque de
#                    arriba): un acento sutil de apertura, NO un impacto de
#                    combate -- por eso magnitudes bajas comparadas con las
#                    del boss (p. ej. el temblor del STOMP es mas fuerte y
#                    mas largo). 0.18s de duracion visual, intensidad 3.0
#                    (unidades de `Camera.apply_shake`); queda por debajo de
#                    cualquier sacudida de combate para no confundirse con
#                    un telegraph. La orden en si es INSTANTANEA para el
#                    guion (`TemblorAction.update()` siempre devuelve True
#                    en su primer fotograma, cutscene_system.py:345-346): la
#                    duracion 0.18 la consume la CAMARA de forma asincrona,
#                    no el guion.
#   esperar 1.0   -- espera final: deja que el temblor se termine de sentir
#                    y que el jugador tenga un respiro antes de que la
#                    cutscene se de por terminada (`una_vez=true`, no vuelve
#                    a dispararse) y el juego quede completamente en manos
#                    del jugador sin ningun efecto de apertura pendiente.
# Total: 0.6 + ~0 (temblor es instantaneo para el guion) + 1.0 = 1.6s.
_GUION_PRESENTACION = (
    "esperar 0.6\n"
    "temblor 0.18 3.0\n"
    "esperar 1.0\n"
)


_CHECKPOINTS = (
    dict(obj_id=40, checkpoint_id=1, x=1040, y=496),   # fin de "El hogar" == inicio CARPORT
    dict(obj_id=41, checkpoint_id=2, x=1740, y=496),   # dentro de 'El umbral', hueco 700 px conforme guia 66
    # aproximacion final, hueco 700 px conforme guia 66; el rect 32px termina
    # en 2472, antes del CameraLock (2480)
    dict(obj_id=42, checkpoint_id=3, x=2440, y=496),
)


def _checkpoint_object_xml(spec: dict) -> str:
    """Objeto Checkpoint -- Tarea 10. Rect 32x64 anclado al suelo
    (y=496..560, la fila del Floor global del generador): un jugador
    caminando por la superficie normal siempre lo solapa de pies a cabeza.

    NOTA sobre el checkpoint 3 (dictamen doc-guardian 2026-08-24, riesgo
    #1): su respawn (centro x=2456, ver playtest/invariants.py::
    CHECKPOINT_POSITIONS) cae DENTRO del rango de aggro del boss
    (AGGRO_X=2384, boss_venado.py) -- re-aggro inmediato al reaparecer tras
    morir cerca del jefe, deliberado (reintentar sin recorrer todo el
    corredor de vuelta), cubierto por GRACIA_DE_AGGRO=0.6s (H-26) para que
    el primer ataque no llegue sin telegraph visible."""
    return (
        f'  <object id="{spec["obj_id"]}" name="Checkpoint_{spec["checkpoint_id"]:02d}" '
        f'type="Checkpoint" x="{spec["x"]}" y="{spec["y"]}" width="32" height="64">\n'
        '   <properties>\n'
        + _prop("checkpoint_id", str(spec["checkpoint_id"]), "int", "    ")
        + '   </properties>\n'
        '  </object>\n'
    )


# ===========================================================================
# PICKUPS + COFRE (Tarea 11, guia 66: "dos rutas" de exploracion -- una ruta
# baja a nivel de suelo sin salto y una ruta alta que exige saltar a una
# plataforma). Cada fragmento lleva su propio "mensaje" narrativo breve
# (revision de calidad del coordinador, 2026-08-25): sin el, el fallback
# crudo del motor (``interactable_system._recoger``, linea ~129:
# ``f"Has cogido: {objeto.item_id}"``) le enseñaria al jugador el item_id en
# snake_case. El cofre queda junto al banco roto nuevo del carport
# (``compose_carport``) y a ``Light_AbandonoLamp_01`` (ver ``_LIGHTS``),
# reforzando "algo se perdio" del Acto 2.
# ===========================================================================
_PICKUPS = (
    # PRADERA, a nivel de suelo (Acto 1 "El hogar")
    dict(obj_id=50, item_id="fragmento_recuerdo_01", x=250, y=520,
         mensaje="Un recuerdo cálido: risas que ya no están."),
    # sobre Platform(768,488): requiere saltar (Acto 1, algo de hogar/juego)
    dict(obj_id=51, item_id="fragmento_recuerdo_02", x=790, y=468,
         mensaje="Un juguete varado en el tejado, esperando volver a jugar."),
    # sobre Platform(1776,472): requiere saltar (Acto 3 "El umbral")
    dict(obj_id=52, item_id="fragmento_recuerdo_03", x=1798, y=452,
         mensaje="Alguien dejó esto antes de cruzar el último umbral."),
)
# y=536 (no 520): 24 de alto -> base en 560, el mismo nivel de apoyo del
# banco/tractor de compose_carport() (verificado por render, Paso 6 del
# coordinador). Los coleccionables (_PICKUPS) flotan como lenguaje visual de
# "objeto recogible"; los muebles (cofre, banco, vehiculos) asientan en el
# suelo -- por eso el cofre NO comparte el y=520 de los pickups.
_CHEST = dict(obj_id=55, x=1360, y=536)   # CARPORT, junto al banco roto y Light_AbandonoLamp_01


def _pickup_object_xml(spec: dict) -> str:
    """Objeto Pickup -- Tarea 11. ``stage_objetos._handle_recogible`` exige
    ``item_id`` (cae al ``name`` del objeto si falta) y opcionalmente
    ``mensaje``: cada entrada de ``_PICKUPS`` trae el suyo (revision de
    calidad del coordinador, 2026-08-25) porque sin el, ``_recoger()``
    (``interactable_system.py``, linea ~129) usa el fallback crudo
    ``f"Has cogido: {objeto.item_id}"`` -- el item_id en snake_case a la
    vista del jugador. ``automatico`` no se fija explicito: hereda el valor
    por defecto del motor (True)."""
    return (
        f'  <object id="{spec["obj_id"]}" name="Pickup_{spec["item_id"]}" type="Pickup" '
        f'x="{spec["x"]}" y="{spec["y"]}" width="16" height="16">\n'
        '   <properties>\n'
        + _prop("item_id", spec["item_id"], None, "    ")
        + _prop("mensaje", spec["mensaje"], None, "    ")
        + '   </properties>\n'
        '  </object>\n'
    )


def _chest_object_xml(spec: dict) -> str:
    """Objeto Chest -- Tarea 11. ``stage_objetos._handle_cofre`` solo recibe
    ``mensaje`` (sin ``contenido``/``key_id``/``evento``): pieza puramente
    narrativa, ninguna progresion de juego depende de ella."""
    return (
        f'  <object id="{spec["obj_id"]}" name="Chest_Carport_01" type="Chest" '
        f'x="{spec["x"]}" y="{spec["y"]}" width="24" height="24">\n'
        '   <properties>\n'
        + _prop("mensaje", "Recuerdos de quienes vivieron aquí.", None, "    ")
        + '   </properties>\n'
        '  </object>\n'
    )


def _cutscene_object_xml() -> str:
    """Cutscene de presentacion -- Tarea 9. Cubre la columna de spawn
    (x=0..96) para que se dispare al entrar/moverse el jugador
    (PlayerSpawn_01 esta en x=48). bloquea=false: el jugador conserva el
    control en todo momento -- NO es una cinematica que congele el juego
    (candado de la Tarea 9: frames identicos de los bots con y sin la
    cutscene disparada, ver test_boss_scene.py). Sin orden `camara` desde
    la correccion del 2026-08-25 (ver comentario arriba): el unico efecto
    es un `temblor` sutil de apertura."""
    return (
        '  <object id="45" name="Cutscene_Presentacion_01" type="Cutscene" '
        'x="0" y="0" width="96" height="608">\n'
        '   <properties>\n'
        + _prop_guion("guion", _GUION_PRESENTACION, "    ")
        + _prop("bloquea", "false", "bool", "    ")
        + _prop("saltable", "true", "bool", "    ")
        + _prop("una_vez", "true", "bool", "    ")
        + '   </properties>\n'
        '  </object>\n'
    )


# ===========================================================================
# SERIALIZACION XML
# ===========================================================================
def _prop(name: str, value: str, ptype: str | None = None, indent: str = "  ") -> str:
    """Una linea tipada ``<property/>`` (el atributo ``type`` se omite cuando es None)."""
    type_attr = f' type="{ptype}"' if ptype else ""
    return f'{indent}<property name="{name}"{type_attr} value="{value}"/>\n'


def _prop_guion(name: str, texto: str, indent: str = "  ") -> str:
    """Propiedad de texto MULTILINEA -- el guion de una ``Cutscene`` (Tarea 9).

    A diferencia de ``_prop()``, esta NUNCA usa el atributo ``value``: XML
    normaliza cualquier salto de linea LITERAL dentro de un valor de
    atributo a un espacio (verificado con ``xml.etree.ElementTree`` --
    exactamente el parser que usa pytmx, ``pytmx/pytmx.py:34``). Un guion de
    varias ordenes escrito como ``value="camara ...\\nesperar ..."`` llegaria
    a ``cutscene_guion.analizar_guion`` (que separa por ``splitlines()``)
    como una sola linea con las ordenes pegadas por espacios, y la segunda
    orden jamas se ejecutaria.

    Por eso el texto va como CONTENIDO del elemento
    (``<property name="...">texto</property>``), que SI atraviesa el parser
    intacto -- y sin ``type``: ``pytmx.pytmx.parse_properties`` (pytmx.py:
    347-365) solo usa el texto del elemento cuando NO hay ``type`` (linea
    363, ``subnode.get("value") or subnode.text``); con ``type="string"`` y
    sin ``value`` reescribiria el resultado con la cadena literal "None"
    (linea 365, ``cls(subnode.get("value"))``, ``cls = str``).

    Revision de calidad (2026-08-25): ``texto`` se escapa con
    ``xml.sax.saxutils.escape()`` (``&``, ``<``, ``>`` -> entidades) ANTES de
    interpolarlo en el XML. Hoy el unico guion real (``_GUION_PRESENTACION``)
    no lleva ninguno de esos caracteres, pero un guion futuro que citara, por
    ejemplo, ``HP < 6`` o ``jefe & jugador`` sin este escape produciria XML
    mal formado -- `ElementTree` no lo detecta al ESCRIBIR (esto es una
    f-string, no un serializador), asi que el error saldria recien al
    CARGAR el mapa (``ET.ParseError`` silencioso hasta que algo intente leer
    el TMX), tumbando la carga de TODO el stage por un caracter perdido en
    una sola propiedad.
    """
    return f'{indent}<property name="{name}">{_escapar_xml(texto)}</property>\n'


def _csv_layer(layer: Layer, layer_name: str) -> str:
    """CSV de GIDs por fila: valores unidos por comas, un salto de linea tras la coma de cada fila.

    Las filas se unen con ``",\\n"`` para que al quitar los saltos de linea
    quede un solo flujo limpio separado por comas (sin valores fusionados,
    sin coma final). Un nombre de tile desconocido se relanza con su capa y
    celda (x, y) para una correccion precisa.
    """
    rows: list[str] = []
    for y, row in enumerate(layer):
        cells: list[str] = []
        for x, name in enumerate(row):
            if name is None:
                cells.append("0")
                continue
            try:
                cells.append(str(_gid(name)))
            except KeyError as exc:
                raise KeyError(f"layer '{layer_name}' cell ({x},{y}): {exc}") from exc
        rows.append(",".join(cells))
    return ",\n".join(rows)


def _csv_layer_bg_far(layer: Layer, mapping: dict[str, int]) -> str:
    """Igual que ``_csv_layer``, pero resolviendo SOLO los nombres de
    ``_nombres_bg_far()`` contra el tileset bruma (TAREA 13, extendida
    TAREA 2026-08-27) -- BG_Far es la unica capa poblada exclusivamente por
    ``compose_sky()``, asi que todo nombre que aparezca aqui esta, por
    construccion, en ``mapping``."""
    rows: list[str] = []
    for row in layer:
        cells: list[str] = []
        for name in row:
            if name is None:
                cells.append("0")
                continue
            cells.append(str(_gid_bruma(name, mapping)))
        rows.append(",".join(cells))
    return ",\n".join(rows)


def _tile_layer_xml(lid: int, name: str, layer: Layer) -> str:
    return (
        f' <layer id="{lid}" name="{name}" width="{W}" height="{H}">\n'
        f'  <data encoding="csv">\n{_csv_layer(layer, name)}\n</data>\n'
        f' </layer>\n'
    )


def _objects_xml() -> str:
    return (
        ' <objectgroup id="6" name="Objects">\n'
        '  <object id="1" name="PlayerSpawn_01" type="PlayerSpawn" x="48" y="560">\n'
        '   <point/>\n'
        '  </object>\n'
        # BossVenado_01 es un objeto POINT desnudo: solo name/type/x/y, SIN
        # propiedades personalizadas. StageLoader.load() pasa CADA propiedad
        # de objeto TMX a la entidad como argumento nombrado
        # (stage_loader.py ~L239: ``entity_class(Vector2(obj.x, obj.y),
        # **cleaned)``), y el boss original del profesor es
        # ``BossVenado.__init__(self, spawn_position)`` -- un constructor
        # desnudo sin kwargs. Asi que CUALQUIER propiedad aqui (el viejo
        # arena_origin_x/y, copiado de un generador ya superado) lanza
        # ``TypeError: __init__() got an unexpected keyword argument`` y
        # aborta toda la carga del stage -- haciendo crashear tambien
        # ``python main.py --boss boss_venado``, no solo el arnes. El
        # rectangulo de la arena en el que pelea el boss ya lo lleva
        # CameraLock_01 (x=2480 = ARENA.start*16, w=800 = 50 columnas) abajo;
        # un futuro boss de fase 2 que necesite un origen de arena lo
        # reintroducira COMO UN KWARG DEL CONSTRUCTOR primero. RONDA-11:
        # boss + arena desplazados con la zona de la arena (ARENA ahora
        # [155,205); arena x=2480).
        # RONDA-12 (feedback del usuario: "pon el boss al final del mapa"):
        # el punto del boss se mueve del centro de la arena (columna 180 ->
        # x=2880) a su extremo DERECHO, pasado el gazebo (columnas 177-183) y
        # cerca de RightWall_Arena
        # (col 204 -> x=3264): columna 198 -> x=3168. La zona de la arena en si
        # (CameraLock_01, x=2480 w=800) no cambia -- solo se mueve el punto de spawn del boss dentro de ella.
        '  <object id="2" name="BossVenado_01" type="BossVenado" x="3168" y="240">\n'
        '   <point/>\n'
        '  </object>\n'
        # ArenaZone_01: nacio en la ronda 11 como marcador puramente
        # descriptivo (ningun codigo lo leia). MOTOR V2 lo elimino porque su
        # validador de objetos (tmx_diagnostics.BUILTIN_OBJECT_TYPES) aborta
        # la carga del stage ante cualquier type que no reconoce, y
        # "ArenaZone" no estaba en esa lista -- ver el historial completo en
        # el docstring de test_objects_contract (test_map_residencias.py).
        # DROP #6 del motor (2026-08-25, AUD-605, commit 6bf2914) lo
        # convirtio en tipo builtin OFICIAL: stage_objetos.py:131-133
        # despacha type=="ArenaZone" a _handle_zona_arena (484-501), que lee
        # SOLO x/y/width/height (sin properties) y alimenta
        # stage_data.zonas_arena; stage_scene.py le entrega al jefe la
        # primera zona cuyo centro contiene, via set_arena_bounds. Ya no
        # pasa por el camino de kwargs-de-entidad que rompio V2 (ArenaZone
        # no instancia ninguna entidad).
        # READOPCION 2026-08-26 (hallazgo H-19; decision del usuario de
        # ejecutar la "tarea de adopcion" anotada en FINDINGS.md tras el
        # drop #6): se reintroduce el objeto, ahora leido de verdad por el
        # motor, como fuente-en-Tiled de la arena ADEMAS del override manual
        # en boss_venado_scene.py (doble candado deliberado, no retirado en
        # esta tarea). El rect es EXACTAMENTE ARENA_RECT/ARENA_BOUNDS
        # (x=2480, w=784, hasta el arranque de RightWall_Arena en x=3264) --
        # NO el de CameraLock_01 (w=800, que llega hasta el borde este del
        # mapa en x=3280): la arena de combate del jefe jamas debe incluir
        # la columna de la pared. Reutiliza el id="3" original, libre desde
        # que V2 lo elimino (ver el hueco 2/4 en los ids de abajo antes de
        # esta reintroduccion).
        '  <object id="3" name="ArenaZone_01" type="ArenaZone" x="2480" y="0" width="784" height="608"/>\n'
        '  <object id="4" name="CameraLock_01" type="CameraLock" x="2480" y="0" width="800" height="608">\n'
        '   <properties>\n'
        + _prop("lock_x", "true", "bool", "    ")
        + _prop("lock_y", "true", "bool", "    ")
        + '   </properties>\n'
        '  </object>\n'
        + "".join(_light_object_xml(spec) for spec in _LIGHTS)
        + _cutscene_object_xml()
        + "".join(_checkpoint_object_xml(spec) for spec in _CHECKPOINTS)
        + "".join(_pickup_object_xml(spec) for spec in _PICKUPS)
        + _chest_object_xml(_CHEST)
        + ' </objectgroup>\n'
    )


def _collision_xml() -> str:
    lines = [
        ' <objectgroup id="7" name="Collision">',
        # RONDA-11: Floor abarca todo el mapa ensanchado (W*16 = 3280) y la pared
        # derecha se ubica en la ultima columna ((W-1)*16 = 3264).
        '  <object id="10" name="Floor" x="0" y="560" width="3280" height="48"/>',
        '  <object id="11" name="LeftWall_World" x="0" y="0" width="16" height="608"/>',
        '  <object id="12" name="RightWall_Arena" x="3264" y="0" width="16" height="608"/>',
    ]
    for i, (x, y, w) in enumerate(_PLATFORMS):
        lines.append(
            f'  <object id="{20 + i}" name="Platform" type="Platform" '
            f'x="{x}" y="{y}" width="{w}" height="16"/>'
        )
    lines.append(' </objectgroup>\n')
    return "\n".join(lines)


def build_tmx() -> str:
    """Compone cada capa y devuelve el documento TMX completo como texto."""
    bg_far, bg_mid, bg_near = _blank(), _blank(), _blank()
    terrain, terrain_detail, fg = _blank(), _blank(), _blank()

    compose_sky(bg_far=bg_far, bg_mid=bg_mid)
    compose_celestial(bg_mid=bg_mid)
    compose_forest(bg_mid=bg_mid)
    compose_ground(terrain=terrain)
    compose_pradera(bg_near=bg_near, terrain_detail=terrain_detail, fg=fg)
    compose_carport(bg_near=bg_near, terrain_detail=terrain_detail, fg=fg)
    compose_arcos(bg_near=bg_near, terrain=terrain, terrain_detail=terrain_detail, fg=fg)
    compose_arena(bg_mid=bg_mid, bg_near=bg_near, terrain_detail=terrain_detail, fg=fg)
    compose_platform_decor(terrain_detail=terrain_detail)

    # TAREA 13 (extendida TAREA 2026-08-27): mapa {nombre -> indice en el
    # tileset bruma}, determinista (orden alfabetico) y sin tocar disco --
    # ver ``_nombres_bg_far()`` para la nota de import circular. El mismo
    # criterio de orden lo usa ``gen_tileset_bgfar_blur.generar_tileset_bruma``
    # para ASIGNAR esos indices al construir el PNG real, asi que los GIDs
    # que este mapping produce apuntan a la celda correcta del atlas bruma.
    mapping_bruma = {nombre: i for i, nombre in enumerate(sorted(_nombres_bg_far()))}

    header = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<map version="1.10" tiledversion="1.12.2" orientation="orthogonal" '
        f'renderorder="right-down" width="{W}" height="{H}" '
        f'tilewidth="{TILE}" tileheight="{TILE}" infinite="0" '
        f'nextlayerid="20" nextobjectid="99">\n'
        ' <properties>\n'
        + _prop("stage_id", "boss_venado")
        + _prop("stage_name", "VENADO")
        + _prop("time_limit", "0", "int")
        + _prop("bgm_track", "bgm_zone1_boss")
        + _prop("background_zone", "zone1")
        # Feature B (spec 2026-07-29 sec. 2.1): propiedades de
        # iluminacion/atmosfera, adoptadas del TMX de referencia del profesor
        # pero llevadas hacia el ambiente ya aprobado en las rondas 7-12 del
        # mapa (el ambient/bloom/vignette implicito de la zona 1,
        # 0.62/0.18/0.30, "leaves" ambient_fx), NO los numeros mas oscuros de
        # "tormenta" de la referencia. ``climate`` y ``day_length`` se omiten
        # deliberadamente -- ver
        # test_tmx_omits_climate_day_length_start_hour_and_season.
        #
        # RECALIBRACION (decision del usuario, ronda 2 de critica visual): la
        # primera pasada tambien declaraba start_hour="dusk" + season="autumn",
        # esperando que el ciclo dia/noche del motor HICIERA ATERRIZAR el
        # ambiente compuesto cerca de 0.60. Medido en tiempo de ejecucion en
        # vez de asumido: no lo hace.
        # ``StageScene._aplicar_hora`` (stage_scene.py:518-526) calcula
        #     ambient = max(MIN_AMBIENTE, ambient_light * luz.factor_ambiente
        #                                  * estacion.factor_luz)
        # (``MIN_AMBIENTE = 0.45``, stage_scene.py:516). "dusk" se resuelve a
        # la hora 19.0 (``RelojDeMundo.MOMENTOS["dusk"]``, day_night.py:150),
        # que interpola entre las paradas de 18h/20h (factor_ambiente
        # 0.80/0.66, day_night.py:61-62) a 0.73; "autumn" aporta
        # ``factor_luz = 0.94`` (seasons.py:66). 0.60 * 0.73 * 0.94 = 0.412,
        # POR DEBAJO del piso de 0.45 -- asi que el ambiente compuesto
        # siempre se recortaba al piso que el usuario acababa de rechazar,
        # sin importar cuanto se subiera ``ambient_light`` aisladamente a ~0.60.
        #
        # La paleta propia del tileset ya esta pintada para el crepusculo
        # (vineta crepuscular de rondas 6/7), asi que el TINTADO de
        # hora-del-dia/estacion del motor es redundante encima de ella --
        # opcion (a) del informe de recalibracion: eliminar
        # ``start_hour``/``season`` por completo en vez de pelear contra el
        # multiplicador. Omitidos, el motor NO retrocede a un multiplicador
        # neutral (x1) para ninguno de los dos factores por su cuenta:
        #   - sin start_hour -> ``StageData.start_hour is None`` ->
        #     ``StageScene.HORA_POR_DEFECTO = 12.0`` (mediodia, stage_scene.py:
        #     505) -> las paradas de 10h-14h son AMBAS 1.00 (day_night.py:59-60),
        #     asi que factor_ambiente es exactamente 1.0 (genuinamente neutral).
        #   - sin season -> ``StageData.season == ""`` -> ``seasons.estacion("")``
        #     cae a ``POR_DEFECTO = "summer"`` (seasons.py:79,90), cuyo
        #     ``factor_luz = 1.08`` (seasons.py:60) -- NO neutral.
        # Asi que el multiplicador compuesto real con ambos omitidos es
        # 1.0 * 1.08 = 1.08, no 1.0. ``ambient_light`` se resuelve contra ese
        # multiplicador medido, no asumido: 0.55 * 1.08 = 0.594, dentro de la
        # banda ~0.58-0.60 pedida y lejos de MIN_AMBIENTE. Bloqueado por
        # regresion mediante
        # test_effective_ambient_stays_above_playable_floor, que llama la
        # MISMA formula/constantes de produccion en vez de re-derivarlas.
        #
        # Hallazgo adicional: con ``climate`` sin declarar, el clima efectivo
        # del motor (``StageScene._clima_efectivo``, stage_scene.py:456-469)
        # cae a ``estacion.clima`` -- "rain" para otono, "clear" para el
        # valor por defecto de verano. Eliminar ``season`` por lo tanto
        # tambien retira un VFX de clima de lluvia no intencionado que
        # "autumn" habia activado en silencio (la critica crepuscular
        # aprobada del mapa nunca pidio lluvia).
        #
        # bloom/vignette (paso 2 de la recalibracion): ``_aplicar_hora``
        # tambien suma ``luz.bloom_extra`` encima del ``bloom`` declarado
        # (stage_scene.py:527-528). A la hora de crepusculo/otono ese extra
        # era ~0.085 (paradas de 18h/20h 0.06/0.11 interpoladas,
        # day_night.py:61-62), empujando el bloom aplicado a ~0.305 -- ya el
        # caso "desproporcionado" que advierte el paso 2. En el valor neutral
        # por defecto de mediodia, bloom_extra es exactamente 0.00
        # (day_night.py:59-60), asi que el 0.22 declarado ahora se aplica SIN
        # MODIFICAR -- ya sutil, sin necesidad de mas cambios.
        # ``vignette`` nunca lo toca el ciclo dia/noche ni la estacion
        # (grepeado: solo ``_setup_post_processing`` lo lee), asi que 0.32 no
        # se ve afectado de ninguna forma y se deja tal cual.
        #
        # ADOPCION V3 / H-18 (2026-08-14) -- la recalibracion de arriba se
        # mantiene como historia, pero DOS de sus omisiones se revierten porque
        # el doc 86 (`86_ESPECIFICACION_DE_NIVELES_Y_JEFES`, normativo y
        # posterior a la ronda 2 de critica) las exige para los jefes de Zona 1:
        # la zona termina de noche y su reloj esta congelado.
        #
        #   - ``start_hour="night"`` -- la forma NOMBRADA, no ``22``.
        #     ``RelojDeMundo.MOMENTOS["night"] == 22.0`` (day_night.py:151), o
        #     sea exactamente el mismo valor, y es la forma que enumeran el doc
        #     86 y la ficha del nivel: un ``22`` suelto en Tiled no dice que
        #     significa.
        #   - ``day_length=0`` -- reloj congelado, que es lo que la omision
        #     anterior conseguia por accidente y ahora se declara a proposito.
        #
        # RE-CALIBRACION OBLIGATORIA (medida, no razonada). Declarar la noche
        # cambia los dos multiplicadores que la ronda 2 dejo cuadrados a
        # mediodia, asi que los valores crudos se recalculan para que el
        # resultado COMPUESTO no se mueva ni un decimal del que el usuario
        # aprobo jugando:
        #     factor_ambiente   mediodia 1.00  ->  night 0.55
        #     bloom_extra       mediodia 0.00  ->  night +0.14
        #   ambient_light: 0.55 -> 1.00   (1.00 * 0.55 * 1.08 = 0.594, identico)
        #   bloom:         0.22 -> 0.08   (0.08 + 0.14          = 0.22,  identico)
        # El piso nocturno de `simulacion.py` es
        # ``MIN_AMBIENTE + LUNA_LLENA_SUMA * luz_lunar`` = 0.45 + 0.10*luna <=
        # 0.55 < 0.594, asi que ni con luna llena llega a recortar. ``vignette``
        # no lo toca nadie mas que ``_setup_post_processing`` (grepeado): 0.32
        # se deja tal cual. ``season`` y ``climate`` siguen omitidas -- esa
        # parte de la decision de la ronda 2 no cambia.
        #
        # Lo que NO se puede compensar y por eso lleva firma del usuario
        # jugando: el TINTE pasa de crema (255,252,245) a azul lunar
        # (170,185,238). Es exactamente lo que la ficha pide ("la Zona 1
        # termina de noche y asi debe verse"), pero es un cambio visual real.
        #
        # ``schema_version`` (AUD-393) y ``author`` son de metadatos:
        # ``validate_tmx.py`` avisa si falta la primera y ``grade_stage.py:61``
        # PUNTUA la segunda (REQUIRED_GRADE_PROPS) -- hasta hoy se perdia un
        # tercio de la categoria de metadatos por no declararla.
        + _prop("schema_version", str(SCHEMA_VERSION), "int")
        + _prop("author", AUTHOR)
        + _prop("zone", "1", "int")
        + _prop("start_hour", "night")
        + _prop("day_length", "0", "float")
        + _prop("ambient_light", "1.0", "float")
        + _prop("bloom", "0.08", "float")
        + _prop("vignette", "0.32", "float")
        + _prop("ambient_fx", "leaves", "string")
        + _prop("ambient_fx_rate", "10", "float")
        # TAREA 3: ``bpm``/``compas`` activan ``pulso.py::factor_de_luz`` sin
        # codigo adicional -- ``StageScene._montar_reloj_musical()``
        # (stage_scene.py:1213-1235) ya los lee automaticamente del stage
        # cuando ``bpm > 0``. ``RelojMusical`` deriva el pulso UNICAMENTE del
        # valor declarado aqui -- no escucha la pista real -- asi que tiene
        # que coincidir con el tempo con el que esa pista se compuso o el
        # latido visual queda a destiempo del tambor real. La pista de este
        # stage es ``bgm_zone1_boss``, compuesta a 100 BPM
        # (``legacyofInfest\tools\generate_all_assets.py:2315``,
        # ``MUSIC_DEFS["bgm_zone1_boss"] = {"bpm": 100, ...}`` -- fuente de
        # verdad del tempo real, verificada en el motor). compas de 4 tiempos:
        # el pulso que la Tarea 9 (build-up narrativo) usa para sincronizar el
        # parpadeo ambiental con el corredor, ahora respirando CON la musica.
        + _prop("bpm", "100", "float")
        + _prop("compas", "4", "int")
        + ' </properties>\n'
        f' <tileset firstgid="{FIRSTGID}" name="{TILESET_NAME}" '
        f'tilewidth="{TILE}" tileheight="{TILE}" tilecount="{TILECOUNT}" columns="{COLUMNS}">\n'
        f'  <image source="{TILESET_IMG}" width="{TILESET_W}" height="{TILESET_H}" trans="000000"/>\n'
        ' </tileset>\n'
        # TAREA 13 -- segundo tileset, SOLO usado por BG_Far (profundidad de
        # campo pre-difuminada, ver gen_tileset_bgfar_blur.py). Ancho/alto
        # declarados se derivan de len(mapping_bruma) exactamente igual que
        # TILESET_W/TILESET_H arriba, para no repetir el bug de la ronda 10
        # (altura declarada desincronizada del PNG real).
        # TAREA 2026-08-27: el atlas paso de solo-blur a bruma (blur +
        # adjust_contrast) -- ver el comentario junto a TILESET_BRUMA_NAME
        # mas arriba. El firstgid/tilecount no cambian (mismo conjunto de
        # nombres BG_Far, mismo orden alfabetico -- solo cambio el contenido
        # visual de cada tile del PNG, no cuantos hay ni en que orden).
        f' <tileset firstgid="{FIRSTGID_BRUMA}" name="{TILESET_BRUMA_NAME}" '
        f'tilewidth="{TILE}" tileheight="{TILE}" '
        f'tilecount="{len(mapping_bruma)}" columns="{COLUMNS}">\n'
        f'  <image source="{TILESET_BRUMA_IMG}" '
        f'width="{COLUMNS * TILE}" height="{((len(mapping_bruma) + COLUMNS - 1) // COLUMNS) * TILE}" '
        f'trans="000000"/>\n'
        ' </tileset>\n'
    )

    body = (
        f' <layer id="1" name="BG_Far" width="{W}" height="{H}">\n'
        f'  <data encoding="csv">\n{_csv_layer_bg_far(bg_far, mapping_bruma)}\n</data>\n'
        f' </layer>\n'
        + _tile_layer_xml(2, "BG_Mid", bg_mid)
        + _tile_layer_xml(3, "BG_Near", bg_near)
        + _tile_layer_xml(4, "Terrain", terrain)
        + _tile_layer_xml(5, "Terrain_Detail", terrain_detail)
        + _objects_xml()
        + _collision_xml()
        + _tile_layer_xml(8, "FG_Overlay", fg)
    )

    return header + body + "</map>\n"


def main() -> None:
    """Escribe el TMX (idempotente; estable byte a byte a traves de llamadas repetidas)."""
    OUT_TMX.parent.mkdir(parents=True, exist_ok=True)
    OUT_TMX.write_text(build_tmx(), encoding="utf-8")
    print(f"tmx -> {OUT_TMX} ({W}x{H} tiles, {len(_PLATFORMS)} platforms)")


if __name__ == "__main__":
    main()
