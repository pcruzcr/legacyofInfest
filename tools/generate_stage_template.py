#!/usr/bin/env python3
"""
Genera student_templates/stage_template/stage_template.tmx alineado a nativo 80×45.
"""
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESTINO = PROJECT_ROOT / "student_templates" / "stage_template" / "stage_template.tmx"
TS=16
MW,MH=80,45
SUELO_Y=38
SUELO_SUPERFICIE=1
VACIO=0

def generar():
    # Terrain: suelo en y 38..44
    g=[[VACIO]*MW for _ in range(MH)]
    for x in range(MW):
        g[SUELO_Y][x]=SUELO_SUPERFICIE
        for y in range(SUELO_Y+1, MH):
            g[y][x]=SUELO_SUPERFICIE
    # hueco ejemplo? no, mantener suelo continuo para template
    csv=",".join(str(g[y][x]) for y in range(MH) for x in range(MW))
    ceros=",".join(["0"]*(MW*MH))
    def capa(n,id_,datos):
        return f' <layer id="{id_}" name="{n}" width="{MW}" height="{MH}">\n  <data encoding="csv">\n{datos}\n</data>\n </layer>'
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.11.0" orientation="orthogonal" renderorder="right-down" width="{MW}" height="{MH}" tilewidth="{TS}" tileheight="{TS}" infinite="0" nextlayerid="9" nextobjectid="30">
 <properties>
  <property name="schema_version" value="1"/>
  <property name="stage_id" value="stage_template"/>
  <property name="stage_name" value="Untitled Stage"/>
  <property name="author" value="TU NOMBRE AQUI"/>
  <property name="time_limit" type="int" value="120"/>
  <property name="bgm_track" value="bgm_stage0"/>
  <property name="climate" value="clear"/>
  <property name="zone" type="int" value="1"/>
  <property name="ambient_light" type="float" value="1.0"/>
 </properties>
 <tileset firstgid="1" name="tileset_stage0" tilewidth="16" tileheight="16" tilecount="1" columns="1">
  <image source="../../assets/tilesets/tileset_stage0.png" width="16" height="16"/>
 </tileset>
{capa("BG_Far",1,ceros)}
{capa("BG_Mid",2,ceros)}
{capa("BG_Near",3,ceros)}
{capa("Terrain",4,csv)}
{capa("Terrain_Detail",5,ceros)}
 <objectgroup id="6" name="Objects">
  <object id="1" type="PlayerSpawn" name="PlayerSpawn_01" x="48" y="544"/>
  <object id="2" type="Checkpoint" name="Checkpoint_01" x="320" y="544" width="16" height="32">
   <properties><property name="checkpoint_id" type="int" value="0"/></properties>
  </object>
  <object id="3" type="NextTrigger" name="NextTrigger_01" x="1200" y="544" width="16" height="64"/>
  <object id="4" type="Walker" name="Walker_ejemplo_01" x="400" y="544"/>
  <object id="5" type="Light" name="Light_ejemplo" x="352" y="480" width="16" height="16">
   <properties><property name="radius" type="float" value="96"/><property name="color" value="#ffd9a0"/><property name="intensity" type="float" value="0.8"/></properties>
  </object>
 </objectgroup>
 <objectgroup id="7" name="Collision">
  <object id="20" type="Solid" name="Solid_Floor" x="0" y="608" width="1280" height="112"/>
  <object id="21" type="Solid" name="Solid_LeftWall" x="-16" y="0" width="16" height="720"/>
  <object id="22" type="Solid" name="Solid_RightWall" x="1280" y="0" width="16" height="720"/>
 </objectgroup>
 <layer id="8" name="FG_Overlay" width="{MW}" height="{MH}">
  <data encoding="csv">
{ceros}
</data>
 </layer>
</map>
"""
if __name__=="__main__":
    DESTINO.write_text(generar(), encoding="utf-8")
    print(f"escrito {DESTINO} {MW}x{MH}")
