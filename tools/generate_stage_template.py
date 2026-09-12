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

# AUD-839 — hueco exigente de 4 baldosas (64 px): enseña el salto que el
# calificador clasifica "exigente" sin ser imposible.
HUECO_X0, HUECO_X1 = 40, 44

def generar():
    # Terrain: suelo en y 38..44, con hueco exigente de ejemplo
    g=[[VACIO]*MW for _ in range(MH)]
    for x in range(MW):
        if HUECO_X0 <= x < HUECO_X1:
            continue
        g[SUELO_Y][x]=SUELO_SUPERFICIE
        for y in range(SUELO_Y+1, MH):
            g[y][x]=SUELO_SUPERFICIE
    csv = ",".join(str(g[y][x]) for y in range(MH) for x in range(MW))
    ceros = ",".join(["0"] * (MW * MH))

    def capa(n, id_, datos):
        return (
            f' <layer id="{id_}" name="{n}" width="{MW}" height="{MH}">\n'
            f"  <data encoding=\"csv\">\n{datos}\n</data>\n </layer>"
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.11.0" orientation="orthogonal"
 renderorder="right-down" width="{MW}" height="{MH}"
 tilewidth="{TS}" tileheight="{TS}" infinite="0"
 nextlayerid="9" nextobjectid="30">
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
    <properties>
     <property name="radius" type="float" value="96"/>
     <property name="color" value="#ffd9a0"/>
     <property name="intensity" type="float" value="0.8"/>
    </properties>
   </object>
   <object id="6" type="Slope" name="Slope_Sube_Ejemplo" x="500" y="560" width="96" height="48">
    <properties><property name="sube" value="derecha"/></properties>
   </object>
   <object id="7" type="Slope" name="Slope_Baja_Ejemplo" x="700" y="560" width="96" height="48">
    <properties><property name="sube" value="izquierda"/></properties>
   </object>
   <object id="8" type="Checkpoint" name="Checkpoint_02" x="768" y="544" width="16" height="32">
    <properties><property name="checkpoint_id" type="int" value="1"/></properties>
   </object>
   <object id="9" type="Pickup" name="Pickup_moneda_01" x="640" y="560" width="16" height="16">
    <properties>
     <property name="item_id" value="moneda"/>
     <property name="automatico" type="bool" value="true"/>
    </properties>
   </object>
   <object id="10" type="Pickup" name="Pickup_moneda_02" x="656" y="560" width="16" height="16">
    <properties>
     <property name="item_id" value="moneda"/>
     <property name="automatico" type="bool" value="true"/>
    </properties>
   </object>
   <object id="11" type="Flying" name="Flying_ejemplo_01" x="560" y="400" width="24" height="20"/>
   <object id="12" type="Shooter" name="Shooter_ejemplo_01" x="1000" y="544" width="16" height="24">
    <properties>
     <property name="fire_rate" type="float" value="2.0"/>
     <property name="projectile_speed" type="float" value="100.0"/>
     <property name="projectile_damage" type="float" value="1.0"/>
    </properties>
   </object>
   <object id="13" type="HazardZone" name="HazardZone_ejemplo_01" x="896" y="576" width="48" height="32">
    <properties><property name="dano" type="float" value="0.5"/></properties>
   </object>
   <object id="14" type="MessageTrigger" name="MessageTrigger_bienvenida" x="200" y="544" width="48" height="48">
    <properties><property name="text" value="Flechas para moverte, Espacio para saltar."/></properties>
   </object>
   <object id="15" type="Objective" name="Objective_llegar_al_final" x="1184" y="528" width="0" height="0">
    <properties>
     <property name="objective_id" value="llegar_al_final"/>
     <property name="text" value="Llega a la salida"/>
     <property name="kind" value="bandera"/>
    </properties>
   </object>
  </objectgroup>
  <objectgroup id="7" name="Collision">
   <object id="20" type="Solid" name="Solid_Floor_A" x="0" y="608" width="640" height="112"/>
   <object id="23" type="Solid" name="Solid_Floor_B" x="704" y="608" width="576" height="112"/>
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
