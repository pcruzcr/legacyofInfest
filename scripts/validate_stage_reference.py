#!/usr/bin/env python3
"""Valida Stage0 como referencia canónica 1280x720 80x45 16 ground 608."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STAGE0 = PROJECT_ROOT / "assets/maps/stage0/stage0.tmx"
TEMPLATE = PROJECT_ROOT / "student_templates/stage_template/stage_template.tmx"

def check_tmx(path, expected_w, expected_h, expected_ground_y):
    tree = ET.parse(path)
    el = tree.getroot()
    w = int(el.get("width"))
    h = int(el.get("height"))
    tw = int(el.get("tilewidth"))
    assert w == expected_w, f"{path} width {w} != {expected_w}"
    assert h == expected_h, f"{path} height {h} != {expected_h}"
    assert tw == 16, f"{path} tile {tw} !=16"
    # ground y
    coll = el.find(".//objectgroup[@name='Collision']")
    floors = [o for o in coll.findall("object") if o.get("type") == "Solid" and int(float(o.get("width", 0))) > 500]
    wide_y = max(int(float(o.get("y"))) for o in floors) if floors else None
    assert wide_y == expected_ground_y, f"{path} ground {wide_y} != {expected_ground_y}"
    # layers
    for name in ["BG_Far", "BG_Mid", "BG_Near", "Terrain", "Collision", "Objects", "FG_Overlay"]:
        has_layer = el.find(f".//layer[@name='{name}']") is not None
        has_group = el.find(f".//objectgroup[@name='{name}']") is not None
        assert has_layer or has_group, f"{path} missing {name}"
    # objects
    objs = el.find(".//objectgroup[@name='Objects']")
    spawn = [o for o in objs.findall("object") if o.get("type") == "PlayerSpawn"]
    assert len(spawn) == 1, f"{path} PlayerSpawn {len(spawn)} !=1"
    y = float(spawn[0].get("y"))
    # player feet should be ground: spawn y +64 == ground
    # spawn y is top of 16x32 rect, but player rect 40x64, feetmidbottom
    # For validation, check spawn y == ground -64 (player height)
    delta = y + 64 - expected_ground_y
    assert abs(delta) <= 2, f"{path} spawn {y}+64 != ground {expected_ground_y} delta {delta}"
    # checkpoint
    cps=[o for o in objs.findall("object") if o.get("type")=="Checkpoint"]
    assert len(cps)>=1, f"{path} checkpoint 0"
    # next trigger
    nxt=[o for o in objs.findall("object") if o.get("type")=="NextTrigger"]
    assert len(nxt)>=1, f"{path} next trigger 0"
    print(f"OK {path.name} {w}x{h} ground {wide_y} spawn {y}")

def main():
    ok=True
    try:
        check_tmx(STAGE0, 160,45,608)
    except AssertionError as e:
        print(f"FAIL stage0: {e}")
        ok=False
    try:
        check_tmx(TEMPLATE, 80,45,608)
    except AssertionError as e:
        print(f"FAIL template: {e}")
        ok=False
    if ok:
        print("All stage reference checks PASS")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__=="__main__":
    main()
