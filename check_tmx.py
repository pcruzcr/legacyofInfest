import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init()
pygame.display.set_mode((320, 240))

import pytmx
from pytmx.util_pygame import load_pygame
tmx = load_pygame("assets/maps/stage0/stage0.tmx")
print("Layers:", [l.name for l in tmx.layers])
print("Visible layers:", [l.name for l in tmx.visible_layers])

# Check tilesets
for ts in tmx.tilesets:
    print(f"Tileset: {ts.name}, firstgid={ts.firstgid}, tilecount={ts.tilecount}")

# Check terrain tile GIDs used
terrain = tmx.get_layer_by_name("Terrain")
gids_used = set()
for y in range(tmx.height):
    for x in range(tmx.width):
        gid = terrain.data[y][x]
        if gid:
            gids_used.add(gid)
print(f"Terrain unique GIDs: {sorted(gids_used)}")

# Same for other layers
for lname in ("BG_Far", "BG_Mid", "BG_Near", "Terrain_Detail", "FG_Overlay"):
    layer = tmx.get_layer_by_name(lname)
    gids = set()
    for y in range(tmx.height):
        for x in range(tmx.width):
            gid = layer.data[y][x]
            if gid:
                gids.add(gid)
    print(f"{lname} unique GIDs: {sorted(gids)}")

try:
    col = tmx.get_layer_by_name("Collision")
    count = 0
    for obj in col:
        count += 1
        if count <= 3:
            print(f"  Collision obj: x={obj.x}, y={obj.y}, w={obj.width}, h={obj.height}, type={getattr(obj, 'type', None)}")
    print(f"  Total collision objects: {count}")
except Exception as e:
    print(f"Collision error: {type(e).__name__}: {e}")
try:
    objs = tmx.get_layer_by_name("Objects")
    obj_count = 0
    for obj in objs:
        obj_count += 1
        if obj_count <= 3:
            print(f"  Obj: name={getattr(obj,'name','')}, type={getattr(obj,'type','')}, x={obj.x}, y={obj.y}")
    print(f"  Total objects: {obj_count}")
except Exception as e:
    print(f"Objects error: {type(e).__name__}: {e}")
print(f"Map size: {tmx.width}x{tmx.height} tiles = {tmx.width*tmx.tilewidth}x{tmx.height*tmx.tileheight}px")
print(f"Properties: stage_id={tmx.properties.get('stage_id')}, bgm={tmx.properties.get('bgm_track')}")
