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


# ── ESCALERAS: cada escalon sube 2 filas (32 px) y avanza 3 col (48 px) ─
# Con subida de 32 px el alcance con margen es 69*0.7 = 48 px exactos.
def escalera(col_inicio, fila_inicio, escalones, sentido=1, ancho=4):
    """Genera escalones que suben desde el piso hacia un entrepiso."""
    salida = []
    for i in range(escalones):
        col = col_inicio + sentido * i * (ancho + 1)
        fila = fila_inicio - 2 * (i + 1)
        salida.append((f"Plat_Esc{col_inicio}_{i}", col, fila, ancho))
    return salida


PLATAFORMAS = []
# Escalera A: sube desde el aula 1 hasta el entrepiso izquierdo
PLATAFORMAS += escalera(20, FILA_PISO, 5)
# Escalera B: sube en el aula 2
PLATAFORMAS += escalera(96, FILA_PISO, 5)
# Escalera C: sube en el aula 3
PLATAFORMAS += escalera(140, FILA_PISO, 5)

# Entrepisos: quedan a la altura del ultimo escalon de cada escalera
ENTREPISOS = [("Plat_Entrepiso1", 44, 26, 18),
              ("Plat_Entrepiso2", 120, 26, 18),
              ("Plat_Entrepiso3", 164, 26, 20)]
PLATAFORMAS += ENTREPISOS

# Plataformas sueltas sobre los huecos: dan una ruta alternativa por arriba
for _c, _w in HUECOS:
    PLATAFORMAS.append((f"Plat_Puente{_c}", _c, FILA_PISO - 4, _w + 1))


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
# Pizarras de la planta baja: 2 filas de alto (30-31), justo sobre el piso
for _c in (5, 76, 148):
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

# Checkpoint justo antes de cada hueco + uno al inicio de cada escalera
_cols_cp = [18, 44, 84, 94, 126, 138, 164]
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
  <property name="stage_id" value="stage1_3_las_aulas"/>
  <property name="stage_name" value="STAGE 1-3 — LAS AULAS"/>
  <property name="time_limit" type="int" value="0"/>
  <property name="bgm_track" value="bgm_zone1_traverse"/>
  <property name="background_zone" value="aulas"/>
  <property name="gravity_multiplier" type="float" value="1.0"/>
  <property name="climate" value="clear"/>
 </properties>
 <tileset firstgid="1" name="tileset_aulas_yariel" tilewidth="{TILE}" tileheight="{TILE}" tilecount="64" columns="8">
  <image source="../../tilesets/tileset_aulas_yariel.png" width="128" height="128"/>
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
    _pasos = [(f"Plat_Esc{_base}_{i}", *_por_nombre[f"Plat_Esc{_base}_{i}"])
              for i in range(5)]
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
