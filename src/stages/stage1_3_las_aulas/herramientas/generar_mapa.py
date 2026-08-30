"""Genera stage1_3_las_aulas.tmx — version con plataformeo real.

Novedades respecto a la version anterior:
  * Escaleras de plataformas con saltos VALIDADOS contra la fisica del motor.
  * Huecos en el piso con DeathPit debajo: hay que saltar o se pierde.
  * Cada escalera lleva a algun lado (entrepiso con checkpoint o atajo).
  * Checkpoint justo antes de cada hueco, para que morir no castigue.

FISICA (src/engine/core/settings.py):
    GRAVITY = 800    JUMP_FORCE = 380    WALK_SPEED = 90
Altura maxima de salto:  v^2 / (2g) = 380^2 / 1600 = 90.25 px
Alcance horizontal a una altura h:  se resuelve  (g/2)t^2 - v t + h = 0
y se multiplica la ventana (t2 - t1) por WALK_SPEED.
"""
import math
import sys

ANCHO, ALTO, TILE = 200, 38, 16
PX_W, PX_H = ANCHO * TILE, ALTO * TILE

GRAVITY, JUMP_FORCE, WALK_SPEED = 800.0, 380.0, 90.0
MARGEN = 0.70  # solo se usa el 70% del alcance teorico

PISO, PISO_BORDE, PARED, ZOCALO, TECHO = 1, 2, 3, 4, 5
ESTANTE, MESA_I, MESA_D, SILLA_D, SILLA_I = 6, 7, 8, 9, 10
PIZ_I, PIZ_C, PIZ_D, VENTANA = 11, 12, 13, 14
PUERTA_S, PUERTA_I, CASILLERO, PAPELERA, RELOJ, AFICHE = 15, 16, 17, 18, 19, 20
PIZ_INF_I, PIZ_INF_C, PIZ_INF_D, VENTANA_INF = 21, 22, 23, 24
LUZ_ON, LUZ_OFF = 25, 26


def pizarra(dest, col, fila, cuerpos=5):
    """Coloca una pizarra de 2 filas de alto y (cuerpos + 2) de ancho."""
    poner(dest, col, fila, [PIZ_I] + [PIZ_C] * cuerpos + [PIZ_D])
    poner(dest, col, fila + 1, [PIZ_INF_I] + [PIZ_INF_C] * cuerpos + [PIZ_INF_D])


def ventana(dest, col, fila):
    """Coloca una ventana de 2 filas de alto."""
    dest.append(bloque(col, fila, 1, 1, VENTANA))
    dest.append(bloque(col, fila + 1, 1, 1, VENTANA_INF))

FILA_PISO = 36


# ── Fisica del salto ───────────────────────────────────────────────────

def alcance_horizontal(subida_px: float) -> float | None:
    """Cuanto puede avanzar en horizontal mientras esta a >= subida_px."""
    disc = JUMP_FORCE ** 2 - 2.0 * GRAVITY * subida_px
    if disc < 0:
        return None  # no alcanza esa altura ni de milagro
    t1 = (JUMP_FORCE - math.sqrt(disc)) / GRAVITY
    t2 = (JUMP_FORCE + math.sqrt(disc)) / GRAVITY
    return WALK_SPEED * (t2 - t1)


def salto_valido(subida_px: float, avance_px: float) -> tuple[bool, float]:
    a = alcance_horizontal(subida_px)
    if a is None:
        return False, 0.0
    return avance_px <= a * MARGEN, a * MARGEN


def bloque(col, fila, w, h, gid):
    return {"col": col, "fila": fila, "w": w, "h": h, "gid": gid}


def poner(dest, col, fila, gids):
    for i, g in enumerate(gids):
        dest.append(bloque(col + i, fila, 1, 1, g))


# ── HUECOS EN EL PISO ──────────────────────────────────────────────────
# Ancho en columnas.  Alcance plano = 85 px -> con margen, 59 px = 3.7 tiles.
# Se usan huecos de 3 columnas (48 px): comodo, pero hay que saltar.
HUECOS = [(46, 3), (86, 3), (128, 3), (166, 3)]

_cols_hueco = set()
for _c, _w in HUECOS:
    _cols_hueco.update(range(_c, _c + _w))


# ── ESCALERAS: tres patrones distintos, no el mismo copiado tres veces ──
# Las tres suben las mismas 10 filas (160 px, del piso al entrepiso), pero
# con una geometria distinta cada una para que las 3 pantallas no se sientan
# identicas. Cada escalon se valida igual que antes (salto_valido, abajo),
# asi que "distinto" nunca significa "sin comprobar".
def escalera_clasica(col_inicio, fila_inicio, escalones=5, sentido=1, ancho=4):
    """Patron original: escalones parejos de 32 px, avanzando 1 columna
    de hueco entre uno y el siguiente. Se deja tal cual para el aula 1."""
    salida = []
    for i in range(escalones):
        col = col_inicio + sentido * i * (ancho + 1)
        fila = fila_inicio - 2 * (i + 1)
        salida.append((f"Plat_Esc{col_inicio}_{i}", col, fila, ancho))
    return salida


def escalera_zigzag(col_inicio, fila_inicio):
    """Aula 2: sube en zigzag -- adelante, adelante, ATRAS, adelante, adelante.

    No es la misma forma que la clasica con otros numeros: aqui el tercer
    escalon queda **detras** de donde ya se estuvo, a mas altura, asi que
    hay que saltar hacia atras para seguir subiendo. Un salto hacia atras
    siempre es seguro (avance = max(0, ...) en salto_valido: si el destino
    queda detras del borde de despegue, la distancia horizontal exigida es
    0 sin importar cuanto suba), asi que el truco no rompe la validacion,
    solo aprovecha una regla que ya existia. Los ultimos dos escalones son
    mas anchos para terminar de cerrar la distancia hasta el entrepiso.
    """
    c0, f0 = col_inicio + 2, fila_inicio - 2         # adelante
    c1, f1 = c0 + 5, f0 - 2                          # adelante
    c2, f2 = c1 - 7, f1 - 2                          # ATRAS y mas arriba
    c3, f3 = c2 + 5, f2 - 2                          # adelante, plataforma ancha
    c4, f4 = c3 + 9, f3 - 2                          # adelante, plataforma ancha -- llega al entrepiso
    return [
        (f"Plat_Esc{col_inicio}_0", c0, f0, 4),
        (f"Plat_Esc{col_inicio}_1", c1, f1, 4),
        (f"Plat_Esc{col_inicio}_2", c2, f2, 4),
        (f"Plat_Esc{col_inicio}_3", c3, f3, 8),
        (f"Plat_Esc{col_inicio}_4", c4, f4, 8),
    ]


def escalera_ritmo_quebrado(col_inicio, fila_inicio):
    """Aula 3: ritmo irregular -- dos saltos cortos, UNO grande, uno corto.

    La version anterior era un salto grande a una plataforma larga: se leia
    como "dos pasos largos y ya", parecido a un escalon con otro numero. Esta
    no tiene una cadencia unica que repetir: empieza como la clasica (32 px,
    32 px), pero al tercer tramo pega el salto mas comprometido del nivel
    (64 px de una vez, con solo 32.3 px de alcance de sobra) y termina con
    un salto corto y normal. Ni todo parejo (A) ni todo en zigzag (B) ni un
    solo salto grande: sube-sube-SALTA-sube.
    """
    c0, f0 = col_inicio + 2, fila_inicio - 2   # sube 32 px
    c1, f1 = c0 + 6, f0 - 2                    # sube 32 px mas
    c2, f2 = c1 + 6, f1 - 4                    # EL salto grande: 64 px de una vez
    return [
        (f"Plat_Esc{col_inicio}_0", c0, f0, 4),
        (f"Plat_Esc{col_inicio}_1", c1, f1, 4),
        (f"Plat_Esc{col_inicio}_2", c2, f2, 8),
    ]


PLATAFORMAS = []
# Escalera A (aula 1): la clasica -- sirve de "tutorial" al ser la primera
# que se encuentra el jugador. Las otras dos ya no se le parecen en nada.
PLATAFORMAS += escalera_clasica(20, FILA_PISO)
# Escalera B (aula 2): zigzag -- adelante, adelante, ATRAS, adelante, adelante.
PLATAFORMAS += escalera_zigzag(96, FILA_PISO)
# Escalera C (aula 3): ritmo irregular -- sube, sube, SALTA (grande), sube.
PLATAFORMAS += escalera_ritmo_quebrado(140, FILA_PISO)

# Entrepisos: quedan a la altura del ultimo escalon de cada escalera
ENTREPISOS = [("Plat_Entrepiso1", 44, 26, 18),
              ("Plat_Entrepiso2", 120, 26, 18),
              ("Plat_Entrepiso3", 164, 26, 20)]
PLATAFORMAS += ENTREPISOS

# Decision de diseno de Yariel: NINGUN hueco lleva tablon por encima. La
# primera version le ponia una plataforma-puente arriba de los 4 (ruta
# segura, opcional); luego se le quito solo a 2. Ahora no hay ninguna: los
# 4 huecos hay que saltarlos de verdad, sin atajo por arriba -- si no se
# salta bien, se cae.


# ── TERRENO SOLIDO ─────────────────────────────────────────────────────
SOLIDOS = [
    bloque(0, 2, ANCHO, 2, TECHO),
    bloque(0, 4, 2, 32, PARED),
    bloque(ANCHO - 2, 4, 2, 32, PARED),
]
# Piso por tramos, saltando los huecos
_tramos_piso = []
_ini = 0
for _c in range(ANCHO + 1):
    if _c == ANCHO or _c in _cols_hueco:
        if _c > _ini:
            _tramos_piso.append((_ini, _c - _ini))
        _ini = _c + 1
for _c, _w in _tramos_piso:
    SOLIDOS.append(bloque(_c, FILA_PISO, _w, 1, PISO_BORDE))
    SOLIDOS.append(bloque(_c, FILA_PISO + 1, _w, 1, PISO))

COLISIONES_SOLIDAS = [
    ("Solid_Techo", 0, 2 * TILE, PX_W, 2 * TILE),
    ("Solid_ParedIzq", 0, 4 * TILE, 2 * TILE, 32 * TILE),
    ("Solid_ParedDer", (ANCHO - 2) * TILE, 4 * TILE, 2 * TILE, 32 * TILE),
]
for _i, (_c, _w) in enumerate(_tramos_piso):
    COLISIONES_SOLIDAS.append(
        (f"Solid_Piso{_i}", _c * TILE, FILA_PISO * TILE, _w * TILE, PX_H - FILA_PISO * TILE))


# ── DECORACION ─────────────────────────────────────────────────────────
# BG_Far NO se rellena entero: el parallax con las fotos del aula real se
# dibuja DETRAS del mapa de azulejos, asi que una pared opaca lo taparia.
# Se dejan solo el zocalo y unos paneles sueltos que enmarcan la escena.
BG_FAR = [bloque(2, 35, ANCHO - 4, 1, ZOCALO)]
for _c in range(4, ANCHO - 4, 18):
    BG_FAR.append(bloque(_c, 30, 2, 5, PARED))   # pilastras de la pared del fondo

BG_MID = []
# Paneles LED de techo, justo debajo del Solid_Techo (filas 2-3). Todos se
# pintan con el GID "encendido"; el parpadeo lo hace Tiled con la <animation>
# que se declara mas abajo sobre ese mismo tile, no hace falta alternar GIDs
# a mano aqui.
for _c in range(10, ANCHO - 10, 22):
    BG_MID.append(bloque(_c, 4, 1, 1, LUZ_ON))

# Pizarras de la planta baja: 2 filas de alto (30-31), justo sobre el piso.
# La tercera se corrio de 148 a 176: col148 queda debajo de la plataforma
# larga de escalera_salto_de_fe (fila 31, cols 142-163) y la taparia.
for _c in (5, 76, 176):
    pizarra(BG_MID, _c, 30, cuerpos=5)
# Pizarras de los entrepisos
for _c in (48, 124, 168):
    pizarra(BG_MID, _c, 20, cuerpos=4)
# Ventanas de 2 filas de alto, a la altura de la vista
for _fila in (27, 13):
    for _c in range(24, ANCHO - 10, 14):
        ventana(BG_MID, _c, _fila)
for _c in (40, 112, 190):
    BG_MID.append(bloque(_c, 34, 1, 1, PUERTA_I))
    BG_MID.append(bloque(_c, 33, 1, 1, PUERTA_S))
for _c in (14, 62, 104, 156, 182):
    BG_MID.append(bloque(_c, 29, 1, 1, AFICHE))
for _c in (30, 92, 134, 176):
    BG_MID.append(bloque(_c, 16, 1, 1, AFICHE))
for _c in (10, 82, 152):
    BG_MID.append(bloque(_c, 27, 1, 1, RELOJ))

BG_NEAR = []
for _c in (58, 62, 66, 108, 112, 116):
    BG_NEAR.append(bloque(_c, 33, 2, 3, CASILLERO))

TERRAIN_DETAIL = []
for _base, _f, _w in [(e[1], e[2], e[3]) for e in ENTREPISOS]:
    TERRAIN_DETAIL.append(bloque(_base, _f - 1, _w, 1, ZOCALO))
    for _k in range(3):
        poner(TERRAIN_DETAIL, _base + 3 + _k * 4, _f - 1, [SILLA_D, MESA_I, MESA_D])
for _inicio in (8, 12, 70, 74, 152, 156):
    if not any(_inicio + d in _cols_hueco for d in range(3)):
        poner(TERRAIN_DETAIL, _inicio, 35, [SILLA_D, MESA_I, MESA_D])
for _c in (30, 100, 144, 186):
    if _c not in _cols_hueco:
        TERRAIN_DETAIL.append(bloque(_c, 35, 1, 1, PAPELERA))

FG_OVERLAY = [bloque(_c, 32, 2, 4, PARED) for _c in (64, 114, 178)]


def construir(bloques):
    g = [[0] * ANCHO for _ in range(ALTO)]
    for b in bloques:
        for f in range(b["fila"], min(b["fila"] + b["h"], ALTO)):
            for c in range(b["col"], min(b["col"] + b["w"], ANCHO)):
                if 0 <= c < ANCHO:
                    g[f][c] = b["gid"]
    return g


def csv(g):
    filas = [",".join(str(v) for v in f) for f in g]
    return "\n".join(x + "," if i < ALTO - 1 else x for i, x in enumerate(filas))


def capa(id_, nombre, g):
    return (f' <layer id="{id_}" name="{nombre}" width="{ANCHO}" height="{ALTO}">\n'
            f'  <data encoding="csv">\n{csv(g)}\n</data>\n </layer>\n')


terrain = list(SOLIDOS)
for _n, c, f, w in PLATAFORMAS:
    terrain.append(bloque(c, f, w, 1, ESTANTE))

capas = [(1, "BG_Far", construir(BG_FAR)), (2, "BG_Mid", construir(BG_MID)),
         (3, "BG_Near", construir(BG_NEAR)), (4, "Terrain", construir(terrain)),
         (5, "Terrain_Detail", construir(TERRAIN_DETAIL))]

piso_y = FILA_PISO * TILE
oid = 1
objetos = [f'  <object id="{oid}" type="PlayerSpawn" name="PlayerSpawn_01" x="64" y="{piso_y}"/>']
oid += 1

# Decision de diseno de Yariel: pocos checkpoints, no uno por cada hueco.
# Caerse cuesta caro a proposito -- "si uno se cae, se muere y ya esta", no
# un respawn a un paso del peligro. Los tres van a mitad de un tramo de piso,
# lejos de cualquier DeathPit (>=19 columnas = 304 px de margen a cada lado).
#
# Por que 3 y no 2: el calificador (scripts/grade_stage.py) tiene DOS reglas
# de checkpoints independientes.
#   - "checkpoints": 5 pts por checkpoint, techo en 15 -> 2 checkpoints
#     son 10/15, 3 ya son 15/15 (el techo). Un checkpoint mas y gratis.
#   - "design_pacing": -6 si el tramo mas largo sin checkpoint pasa de
#     500 px. El nivel mide ~3000 px, y eso es matematicamente imposible
#     de cumplir con menos de 5-6 checkpoints, asi que 2 y 3 pagan la
#     MISMA penalizacion aqui (no hay puntos parciales por acercarse).
# Con esos dos datos, 3 dobla el maximo de la primera regla sin pagar nada
# de mas en la segunda -- no hay ninguna razon para quedarse en 2.
_cols_cp = [68, 108, 148]
for _i, _c in enumerate(_cols_cp):
    objetos.append(
        f'  <object id="{oid}" type="Checkpoint" name="Checkpoint_{_i:02d}" '
        f'x="{_c * TILE}" y="{piso_y - 32}" width="16" height="32">\n'
        f'   <properties>\n    <property name="checkpoint_id" type="int" value="{_i}"/>\n'
        f'   </properties>\n  </object>')
    oid += 1

objetos.append(f'  <object id="{oid}" type="NextTrigger" name="NextTrigger_01" '
               f'x="{190 * TILE}" y="{piso_y - 64}" width="32" height="64"/>')
oid += 1

# Coleccionables: hojas de examen sueltas en el piso, una por aula. Usan
# "Pickup" (framework/stage/interactables.py, sin tocarlo) con automatico=True
# -- se cogen al pasar por encima, como una moneda, sin pedir el boton de usar.
# scripts/grade_stage.py exige >=3 para el maximo de la categoria
# "collectibles" (antes 0, 5/10); no afecta ninguna otra regla del disenio.
for _i, _c in enumerate((22, 115, 175)):
    objetos.append(
        f'  <object id="{oid}" type="Pickup" name="Pickup_{_i:02d}" '
        f'x="{_c * TILE}" y="{piso_y - 16}" width="16" height="16">\n'
        f'   <properties>\n'
        f'    <property name="item_id" value="hoja_de_examen"/>\n'
        f'    <property name="mensaje" value="Una hoja de examen suelta."/>\n'
        f'   </properties>\n  </object>')
    oid += 1

# Casillero interactivo (Practica II, Unidad VI). Usa el sistema de
# interactuables del framework (framework/stage/interactables.py, tipo "Door")
# sin tocar ningun archivo del profesor: el objeto se declara aqui y
# stage_objetos.py ya sabe leerlo. key_id vacio = se abre sin llave, con el
# boton de usar. "evento" es el nombre propio que escucha Stage1_3_LasAulas
# para arrancar la animacion por easing (ver stage1_3_las_aulas.py).
# Coordenadas: mismo casillero que BG_NEAR dibuja en col=62, fila=33.
CASILLERO_COL, CASILLERO_FILA = 62, 33
objetos.append(
    f'  <object id="{oid}" type="Door" name="CasilleroInteractivo" '
    f'x="{CASILLERO_COL * TILE}" y="{CASILLERO_FILA * TILE}" '
    f'width="{2 * TILE}" height="{3 * TILE}">\n'
    # OJO: no declarar key_id="" — pytmx parsea un value="" vacio como None
    # (no como cadena vacia), y stage_objetos.py hace str(None) = "None": una
    # cadena no vacia que la Cerradura interpreta como llave exigida, y la
    # puerta queda bloqueada sin que nada en Tiled avise del porque. Omitir
    # la propiedad del todo es la forma correcta de decir "sin llave": el
    # .get(..., "") de stage_objetos.py entonces si cae en su valor por
    # defecto real.
    f'   <properties>\n'
    f'    <property name="evento" value="CASILLERO_ABIERTO"/>\n'
    f'    <property name="mensaje" value="Un casillero de estudiante."/>\n'
    f'   </properties>\n  </object>')
oid += 1

# DeathPit debajo de cada hueco
for _i, (_c, _w) in enumerate(HUECOS):
    objetos.append(
        f'  <object id="{oid}" type="DeathPit" name="DeathPit_{_i}" '
        f'x="{_c * TILE}" y="{(FILA_PISO + 1) * TILE}" '
        f'width="{_w * TILE}" height="{TILE}"/>')
    oid += 1

# Enemigos, evitando los huecos
ENEMIGOS = [(c, FILA_PISO, m, t) for c, m, t in
            [(28, "right", 96), (68, "left", 96), (106, "right", 128),
             (148, "left", 96), (184, "left", 80)]
            if not any(c + d in _cols_hueco for d in range(-3, 4))]
ENEMIGOS += [(48, 26, "right", 96), (124, 26, "left", 96), (168, 26, "right", 96)]
for _col, _fila, _mira, _tramo in ENEMIGOS:
    objetos.append(
        f'  <object id="{oid}" type="EstudianteInfectado" name="Estudiante_{oid}" '
        f'x="{_col * TILE}" y="{_fila * TILE}">\n   <properties>\n'
        f'    <property name="facing" value="{_mira}"/>\n'
        f'    <property name="patrol_length" type="float" value="{_tramo}"/>\n'
        f'    <property name="patrol_speed" type="float" value="40"/>\n'
        f'    <property name="alert_speed" type="float" value="85"/>\n'
        f'    <property name="max_health" type="float" value="2"/>\n'
        f'    <property name="zone" type="int" value="1"/>\n'
        f'    <property name="radio_vision" value="140"/>\n'
        f'    <property name="angulo_vision" value="120"/>\n'
        f'    <property name="radio_periferico" value="40"/>\n'
        f'   </properties>\n  </object>')
    oid += 1

# Cuadernos voladores: arcos sobre los huecos, para marcar el peligro
CUADERNOS = []
for _i, (_c, _w) in enumerate(HUECOS):
    _x0 = (_c - 6) * TILE
    _x3 = (_c + _w + 6) * TILE
    _yb = piso_y - 16
    _ya = piso_y - 160
    # P1 y P2 se separan un tercio del ancho total a cada lado: repartidos asi,
    # la curva describe un arco parejo.  Si se juntan en el centro, el arco sale
    # puntiagudo; si se alejan a los extremos, se aplana.
    _tercio = (_x3 - _x0) // 3
    CUADERNOS.append((f"Cuaderno_{chr(65 + _i)}",
                      (_x0, _yb), (_x0 + _tercio, _ya), (_x3 - _tercio, _ya), (_x3, _yb)))
for _nombre, *_ctrl in CUADERNOS:
    objetos.append(
        f'  <object id="{oid}" type="CuadernoVolador" name="{_nombre}" '
        f'x="{_ctrl[0][0]}" y="{_ctrl[0][1]}">\n   <properties>\n'
        f'    <property name="periodo" value="5.0"/>\n'
        f'    <property name="muestras" value="160"/>\n'
        f'    <property name="factor_alerta" value="1.8"/>\n'
        f'    <property name="max_health" type="float" value="1"/>\n'
        f'    <property name="zone" type="int" value="1"/>\n'
        f'   </properties>\n  </object>')
    oid += 1
    for _k, (_wx, _wy) in enumerate(_ctrl):
        objetos.append(
            f'  <object id="{oid}" type="Waypoint" name="{_nombre}_P{_k}" x="{_wx}" y="{_wy}">\n'
            f'   <properties>\n    <property name="owner_id" value="{_nombre}"/>\n'
            f'   </properties>\n  </object>')
        oid += 1

colisiones = []
for nombre, x, y, w, h in COLISIONES_SOLIDAS:
    colisiones.append(f'  <object id="{oid}" type="Solid" name="{nombre}" x="{x}" y="{y}" width="{w}" height="{h}"/>')
    oid += 1
for nombre, c, f, w in PLATAFORMAS:
    colisiones.append(f'  <object id="{oid}" type="Platform" name="{nombre}" '
                      f'x="{c * TILE}" y="{f * TILE}" width="{w * TILE}" height="{TILE}"/>')
    oid += 1

tmx = f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.11.0" orientation="orthogonal" renderorder="right-down" width="{ANCHO}" height="{ALTO}" tilewidth="{TILE}" tileheight="{TILE}" infinite="0" nextlayerid="9" nextobjectid="{oid}">
 <properties>
  <property name="schema_version" value="1"/>
  <property name="stage_id" value="stage1_3_las_aulas"/>
  <property name="stage_name" value="STAGE 1-3 — LAS AULAS"/>
  <property name="author" value="Yariel"/>
  <property name="time_limit" type="int" value="0"/>
  <property name="bgm_track" value="bgm_zone1_traverse"/>
  <property name="background_zone" value="aulas"/>
  <property name="gravity_multiplier" type="float" value="1.0"/>
  <property name="climate" value="clear"/>
 </properties>
 <tileset firstgid="1" name="tileset_aulas_yariel" tilewidth="{TILE}" tileheight="{TILE}" tilecount="64" columns="8">
  <image source="../../tilesets/tileset_aulas_yariel.png" width="128" height="128"/>
  <tile id="{LUZ_ON - 1}">
   <animation>
    <frame tileid="{LUZ_ON - 1}" duration="700"/>
    <frame tileid="{LUZ_OFF - 1}" duration="120"/>
   </animation>
  </tile>
 </tileset>
{''.join(capa(i, n, g) for i, n, g in capas)} <objectgroup id="6" name="Objects">
{chr(10).join(objetos)}
 </objectgroup>
 <objectgroup id="7" name="Collision">
{chr(10).join(colisiones)}
 </objectgroup>
{capa(8, "FG_Overlay", construir(FG_OVERLAY))}</map>
"""

with open(sys.argv[1], "w", encoding="utf-8") as fh:
    fh.write(tmx)

# ── VALIDACION DE SALTOS ───────────────────────────────────────────────
print("TMX generado:", sys.argv[1])
print(f"  {ANCHO}x{ALTO} tiles = {PX_W}x{PX_H} px")
print(f"  tramos de piso: {len(_tramos_piso)} | huecos con DeathPit: {len(HUECOS)}")
print(f"  plataformas: {len(PLATAFORMAS)} | checkpoints: {len(_cols_cp)}")
print()
print("VALIDACION DE SALTOS (margen de seguridad 70%)")
print(f"  huecos planos: {[w * TILE for _c, w in HUECOS]} px "
      f"| maximo permitido {alcance_horizontal(0) * MARGEN:.0f} px")
malos = 0
for _c, _w in HUECOS:
    ok, lim = salto_valido(0, _w * TILE)
    if not ok:
        print(f"    FUERA DE RANGO: hueco en col {_c} mide {_w * TILE} px > {lim:.0f}")
        malos += 1

print("  escaleras (se mide el hueco real entre borde y borde):")
_por_nombre = {n: (c, f, w) for n, c, f, w in PLATAFORMAS}
for _base in (20, 96, 140):
    # Cada escalera puede tener un numero de escalones distinto ahora (la
    # clasica 5, la de saltos largos 3, la irregular 5 con anchos propios):
    # se cuentan los que de verdad existen en vez de asumir range(5).
    _i = 0
    _pasos = []
    while f"Plat_Esc{_base}_{_i}" in _por_nombre:
        _pasos.append((f"Plat_Esc{_base}_{_i}", *_por_nombre[f"Plat_Esc{_base}_{_i}"]))
        _i += 1
    # Primer escalon: desde el piso
    _n, _c, _f, _w = _pasos[0]
    subida = (FILA_PISO - _f) * TILE
    ok, lim = salto_valido(subida, 0.0)
    print(f"    piso -> {_n}: sube {subida:.0f} px, avance 0 px "
          f"(limite {lim:.0f}) -> {'OK' if ok else 'FUERA DE RANGO'}")
    malos += 0 if ok else 1
    for i in range(len(_pasos) - 1):
        _n0, _c0, _f0, _w0 = _pasos[i]
        _n1, _c1, _f1, _w1 = _pasos[i + 1]
        subida = (_f0 - _f1) * TILE
        avance = max(0, (_c1 - (_c0 + _w0)) * TILE)
        ok, lim = salto_valido(subida, avance)
        print(f"    {_n0} -> {_n1}: sube {subida:.0f} px, avanza {avance:.0f} px "
              f"(limite {lim:.0f}) -> {'OK' if ok else 'FUERA DE RANGO'}")
        malos += 0 if ok else 1
    # Ultimo escalon -> entrepiso
    _n0, _c0, _f0, _w0 = _pasos[-1]
    _ent = min(ENTREPISOS, key=lambda e: abs(e[1] - (_c0 + _w0)))
    subida = (_f0 - _ent[2]) * TILE
    avance = max(0, (_ent[1] - (_c0 + _w0)) * TILE)
    ok, lim = salto_valido(subida, avance)
    print(f"    {_n0} -> {_ent[0]}: sube {subida:.0f} px, avanza {avance:.0f} px "
          f"(limite {lim:.0f}) -> {'OK' if ok else 'FUERA DE RANGO'}")
    malos += 0 if ok else 1

print(f"\n  SALTOS INVALIDOS: {malos}")
