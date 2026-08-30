import json
import os as _os
import sys

# Las rutas se derivan de la ubicación de este fichero, no de una carpeta
# fija de la máquina donde se construyó. Los generadores viajan dentro de
# la entrega, así que tienen que poder ejecutarse desde donde caigan: un
# `/tmp/...` incrustado convierte el código en algo que sólo corre en un
# ordenador, y entonces "el arte se genera por código" deja de ser cierto
# para quien lo recibe.
_AQUI = _os.path.dirname(_os.path.abspath(__file__))
_ART = _AQUI if _os.path.basename(_AQUI) == "art" else _os.path.join(_AQUI, "art")
_BASE = _os.path.dirname(_ART)
sys.path.insert(0, _ART)

def _ruta(nombre):
    """Busca un fichero junto a los generadores y, si no, un nivel arriba.

    Los mismos scripts se usan desde la carpeta de trabajo (donde los CSV
    y `objects_source.tmx` viven al lado del TMX) y desde dentro de `art/`
    en la entrega empaquetada. Probar los dos sitios evita tener que
    mantener dos versiones del generador.
    """
    a = _os.path.join(_ART, nombre)
    return a if _os.path.exists(a) else _os.path.join(_BASE, nombre)





# Objects/Collision se extraen VERBATIM de objects_source.tmx, que es la
# version curada a mano de la capa de objetos (3 checkpoints, 5 Pickup,
# suelo partido por el pozo de 40 px). Las capas visuales se regeneran.

def layer_xml(id_, name, csv_path):
    data = open(csv_path).read().strip()
    return f'''<layer id="{id_}" name="{name}" width="100" height="38">
  <data encoding="csv">
{data}
</data>
 </layer>'''

_meta = json.load(open(_os.path.join(_ART, "tileset_meta.json")))
GRID_W = _meta["grid_w"]
N_ROWS = _meta["n_rows"]
TILECOUNT = GRID_W * N_ROWS
IMG_W = GRID_W * 16
IMG_H = N_ROWS * 16

# Animaciones de baldosa (Entrega II). pyscroll las lee del propio TMX y
# sustituye la imagen en caliente: no hace falta tocar el motor.
ANIM_XML = "".join(
    '\n  <tile id="%s">\n   <animation>\n%s   </animation>\n  </tile>' % (
        tid,
        "".join('    <frame tileid="%d" duration="%d"/>\n' % (f["tileid"], f["duration"])
                for f in frames),
    )
    for tid, frames in sorted(_meta["animations"].items(), key=lambda kv: int(kv[0]))
)

import ruta as _R
import objetos as _O
_ALTURAS, _ = _R.comprobar(verboso=False)
objects_block, collision_block, _nextid = _O.generar(_ALTURAS)

tmx = f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.11.0" orientation="orthogonal" renderorder="right-down" width="100" height="38" tilewidth="16" tileheight="16" infinite="0" nextlayerid="9" nextobjectid="{_nextid + 10}">
 <properties>
  <property name="schema_version" type="int" value="1"/>
  <property name="stage_id" value="3-1"/>
  <property name="stage_name" value="3-1 LA ENTRADA DE PIEDRA"/>
  <property name="author" value="Avril"/>
  <property name="time_limit" type="int" value="160"/>
  <property name="bgm_track" value="bgm_zone3_traverse"/>
  <property name="climate" value="clear"/>
  <!-- Ficha del nivel, regla 1: el 3-1 es el nivel inicial de la Zona 3 y
       declara donde empieza la NOCHE. 22:00 -> 05:00 en 500 s reales. -->
  <property name="start_hour" value="night"/>
  <property name="day_length" type="float" value="500.0"/>
  <property name="zone" type="int" value="3"/>
  <property name="background_zone" value="zone3"/>
  <property name="ambient_light" type="float" value="0.55"/>
  <property name="bloom" type="float" value="0.30"/>
  <property name="vignette" type="float" value="0.35"/>
 </properties>
 <tileset firstgid="1" name="tileset_invenio_gothic_v5" tilewidth="16" tileheight="16" tilecount="{TILECOUNT}" columns="{GRID_W}">
  <image source="../../../student_assets/tilesets/tileset_invenio_gothic_v5.png" width="{IMG_W}" height="{IMG_H}"/>{ANIM_XML}
 </tileset>
 {layer_xml(1, "BG_Far", _ruta("BG_Far.csv"))}
 {layer_xml(2, "BG_Mid", _ruta("BG_Mid.csv"))}
 {layer_xml(3, "BG_Near", _ruta("BG_Near.csv"))}
 {layer_xml(4, "Terrain", _ruta("Terrain.csv"))}
 {layer_xml(5, "Terrain_Detail", _ruta("Terrain_Detail.csv"))}
 {objects_block}
 {collision_block}
 {layer_xml(8, "FG_Overlay", _ruta("FG_Overlay.csv"))}
</map>
'''

out = _ruta("stage3_1_la_entrada_de_piedra.tmx")
open(out, "w").write(tmx)
print("written", out, len(tmx), "bytes")
