"""Genera las capas `Objects` y `Collision` a partir del perfil del terreno.

Antes estas dos capas se mantenían a mano en un `objects_source.tmx` y el
dibujo se calculaba aparte. Con un suelo plano eso era llevadero; con un
perfil de alturas es una fuente de errores garantizada — cada vez que un
tramo sube o baja, todo lo que se apoya en él tiene que moverse: el
jugador, las garzas, los checkpoints, los coleccionables, las losas.

Así que aquí no se escriben coordenadas `y`. Se escribe **en qué columna
va cada cosa**, y la `y` la calcula el perfil. Es imposible que una garza
quede flotando o enterrada.
"""
from __future__ import annotations

import ruta
from ruta import COLUMNAS, T, superficie_y

# ── Dónde va cada cosa, en columnas ────────────────────────────────────

COL_SPAWN = 2
COL_SALIDA = 96
#: Tres checkpoints. `grade_stage.py` da 5 puntos por cada uno hasta 15, y
#: penaliza cualquier tramo de más de 500 px sin uno. Con 1600 px de mapa,
#: tres repartidos dejan tramos de 400 px.
# Se eligen sobre tramos llanos, y a menos de 500 px unos de otros —el
# umbral que penaliza `grade_stage.py`—: aquí quedan a 336, 400, 336 y
# 400 px, con el último tramo hasta la salida por debajo también.
COLS_CHECKPOINT = (21, 46, 67, 88)

#: Garzas: en el suelo, en el primer tercio. "Falsa calma" (ficha del
#: nivel). La primera aparece sola.
COLS_GARZA = (12, 20, 33, 43)
#: Halcones: sólo en el último tramo. El nivel enseña a mirar el cielo y
#: el examen va al final. La separación con la garza más a la derecha
#: supera los 800 px de una pantalla, así que no coinciden en cámara.
COLS_HALCON = (76, 81, 87, 93)
#: Quetzales sobre los arcos, quietos.
COLS_QUETZAL = (34, 79)
#: Coleccionables: uno de ellos al otro lado del pozo.
# Uno en la ruta alta opcional del acto I, uno al otro lado del pozo, y
# uno encima del muro más alto del nivel: los coleccionables premian
# haber tomado el camino difícil.
COLS_PICKUP = (7, 22, 34, 60, 84)
#: Las cinco losas de la Unidad VI, en el tramo llano y sin enemigos.
COLS_LOSA = (59, 62, 65, 68, 71)

ALTO_ENEMIGO = 32
ALTO_CHECKPOINT = 32
ALTO_SALIDA = 64


def _y_suelo(alturas, col):
    """`y` de la superficie caminable en una columna."""
    c = max(0, min(COLUMNAS - 1, col))
    while alturas[c] is None and c > 0:
        c -= 1
    return superficie_y(alturas[c] or 0)


def generar(alturas):
    """Devuelve (xml_objects, xml_collision)."""
    obj, col_xml = [], []
    oid = 1

    def añadir(tipo, nombre, col, dy=0, w=None, h=None, props=None, y=None):
        nonlocal oid
        x = col * T
        yy = (_y_suelo(alturas, col) + dy) if y is None else y
        dims = ""
        if w is not None:
            dims = f' width="{w}" height="{h}"'
        if props:
            cuerpo = "\n".join(
                f'    <property name="{k}" value="{v}"/>' for k, v in props.items())
            obj.append(f'  <object id="{oid}" type="{tipo}" name="{nombre}" '
                       f'x="{x}" y="{yy}"{dims}>\n   <properties>\n{cuerpo}\n'
                       f'   </properties>\n  </object>')
        else:
            obj.append(f'  <object id="{oid}" type="{tipo}" name="{nombre}" '
                       f'x="{x}" y="{yy}"{dims}/>')
        oid += 1

    obj.append("  <!-- Inicio, control y salida -->")
    añadir("PlayerSpawn", "PlayerSpawn_01", COL_SPAWN)
    for i, c in enumerate(COLS_CHECKPOINT, 1):
        añadir("Checkpoint", f"Checkpoint_{i:02d}", c, dy=-ALTO_CHECKPOINT,
               w=16, h=ALTO_CHECKPOINT, props={"checkpoint_id": i - 1})
    añadir("NextTrigger", "NextTrigger_01", COL_SALIDA, dy=-ALTO_SALIDA,
           w=16, h=ALTO_SALIDA)

    obj.append("\n  <!-- Aviso que presenta las losas -->")
    añadir("MessageTrigger_Once", "MessageTrigger_Losas", COL_SPAWN + 3,
           dy=-48, w=48, h=48,
           props={"text": "Las losas del camino responden al peso. "
                          "Pisalas en orden."})

    obj.append("\n  <!-- Suelo: garzas, la primera sola -->")
    for i, c in enumerate(COLS_GARZA, 1):
        añadir("WalkerGarza", f"WalkerGarza_{i:02d}", c, dy=-ALTO_ENEMIGO,
               props={"patrol_length": 80.0, "patrol_speed": 55.0})

    obj.append("\n  <!-- Fondo: quetzales sobre los arcos -->")
    for i, c in enumerate(COLS_QUETZAL, 1):
        añadir("ShooterQuetzal", f"ShooterQuetzal_{i:02d}", c,
               y=_y_suelo(alturas, c) - 112)

    obj.append("\n  <!-- Aire: halcones, sólo en el último tramo -->")
    for i, c in enumerate(COLS_HALCON, 1):
        añadir("FlyingHalcon", f"FlyingHalcon_{i:02d}", c, y=T * 6)

    obj.append("\n  <!-- Coleccionables -->")
    for i, c in enumerate(COLS_PICKUP, 1):
        añadir("Pickup", f"Pickup_{i:02d}", c, dy=-24, w=16, h=16)

    # ── Colisión ───────────────────────────────────────────────────────
    col_xml.append("  <!-- Suelo: un bloque por tramo de altura constante -->")
    for i, (x, y, w, h) in enumerate(ruta.bloques_solidos(alturas), 1):
        col_xml.append(f'  <object id="{oid}" type="Solid" name="Suelo_{i:02d}" '
                       f'x="{x}" y="{y}" width="{w}" height="{h}"/>')
        oid += 1

    col_xml.append("\n  <!-- Repisas: cubierta y rutas alternativas -->")
    for nombre, c, alt, ancho in ruta.REPISAS:
        y = _y_suelo(alturas, c) - alt * T
        col_xml.append(f'  <object id="{oid}" type="Platform" name="{nombre}" '
                       f'x="{c * T}" y="{y}" width="{ancho * T}" height="16"/>')
        oid += 1

    col_xml.append("\n  <!-- El pozo mata: caer tiene consecuencia limpia -->")
    for pc0, pn, recorte in ruta.POZOS:
        col_xml.append(f'  <object id="{oid}" type="DeathPit" name="DeathPit_01" '
                       f'x="{pc0 * T - recorte}" y="{superficie_y(0) + 24}" '
                       f'width="{pn * T + recorte}" height="24"/>')
        oid += 1

    objects = ('<objectgroup id="6" name="Objects">\n'
               + "\n".join(obj) + "\n </objectgroup>")
    collision = ('<objectgroup id="7" name="Collision">\n'
                 + "\n".join(col_xml) + "\n </objectgroup>")
    return objects, collision, oid
