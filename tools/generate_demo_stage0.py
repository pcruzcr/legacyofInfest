"""Generate a comprehensive Stage 0 TMX (100x38 tiles, 1600x608px)
with 6 progressive learning zones demonstrating ALL framework features.

Zone layout:
  A (cols  2-15): Movement — A/D, W/S, platforms, ground
  B (cols 16-35): Basic Combat — Walkers, dash, parry
  C (cols 36-51): Ranged Combat — Flying, Shooter, Charger
  D (cols 52-67): Verticality — wall-slide, ledge-grab, pit, Archer
  E (cols 68-84): Hazards — death pit, hazard zone, Brute
  F (cols 85-98): Culmination — Caster, Assassin, storm, exit
"""
import os
import shutil
import xml.etree.ElementTree as ET

OUT_DIR = "assets/maps/stage0"
OUT_PATH = os.path.join(OUT_DIR, "stage0.tmx")
BACKUP_DIR = "assets/maps/stage0_backup"
TILESET_PATH = "../../tilesets/tileset_stage0.png"

MAP_W = 100
MAP_H = 38
TILE = 16

# Zone column boundaries
Z = {
    "A": (2, 15),
    "B": (16, 35),
    "C": (36, 51),
    "D": (52, 67),
    "E": (68, 84),
    "F": (85, 98),
}

# Tile GIDs
WALL = 153
WALL_R = 160
FLOOR = 665
FLOOR_V = 668
FLOOR_B = 409
PLAT = 666
WATER = 161

# Column helpers
PIT_C1, PIT_C2 = 54, 56          # death pit gap cols
P1_C1, P1_C2 = 6, 11          # zone-A platform
P2_C1, P2_C2 = 58, 62            # zone-D high platform


def csv_row(values):
    return ",".join(str(v) for v in values)


def make_tmx():
    if os.path.exists(OUT_PATH):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        bak = os.path.join(BACKUP_DIR, "stage0_backup.tmx")
        shutil.copy2(OUT_PATH, bak)
        print(f"Backed up old TMX to {bak}")

    props = {
        "stage_id": "stage0",
        "stage_name": "STAGE 0 - PROLOGUE",
        "bgm_track": "bgm_stage0",
        "background_zone": "stage0",
        "climate": "clear",
        "time_limit": "0",
        "gravity_multiplier": "1.0",
    }

    # ── Terrain layer ──
    g = [[0] * MAP_W for _ in range(MAP_H)]

    # Walls col 0 and 99
    for y in range(MAP_H):
        g[y][0] = WALL
        g[y][MAP_W - 1] = WALL_R

    # Floor: rows 32-37 (gap at cols PIT_C1-PIT_C2)
    for y in range(32, MAP_H):
        for x in range(1, MAP_W - 1):
            if PIT_C1 <= x <= PIT_C2:
                continue
            if y == 32:
                g[y][x] = FLOOR_B
            elif y in (35, 37):
                g[y][x] = FLOOR_V
            else:
                g[y][x] = FLOOR

    # Zone A: Platform (col 6-11, row 30) — player-head level wall
    for x in range(P1_C1, P1_C2 + 1):
        g[30][x] = PLAT

    # Zone A: Double-jump platform (col 11-13, row 28)
    for x in range(11, 14):
        g[28][x] = PLAT

    # Zone C: Flying platform (col 38-40, row 28)
    for x in range(38, 41):
        g[28][x] = PLAT

    # Zone C: Shooter platform (col 45-47, row 29)
    for x in range(45, 48):
        g[29][x] = PLAT

    # Zone D: Pit cover (col 54-56, row 32) — one-way at floor level
    for x in range(PIT_C1, PIT_C2 + 1):
        g[32][x] = FLOOR_B

    # Zone D: High platform (col 58-62, row 30) — head-level, passable from below
    for x in range(P2_C1, P2_C2 + 1):
        g[30][x] = PLAT

    # Zone E: Hazard-side platform (col 74-78, row 29)
    for x in range(74, 79):
        g[29][x] = PLAT

    # Zone F: Final platform (col 88-92, row 27)
    for x in range(88, 93):
        g[27][x] = PLAT

    # Zone A: Decorative water
    for x in range(13, 15):
        g[31][x] = WATER

    # ── Detail layer ──
    detail = [[0] * MAP_W for _ in range(MAP_H)]

    # ── Generate XML ──
    root = ET.Element("map")
    root.set("version", "1.10")
    root.set("tiledversion", "1.12.2")
    root.set("orientation", "orthogonal")
    root.set("renderorder", "right-down")
    root.set("width", str(MAP_W))
    root.set("height", str(MAP_H))
    root.set("tilewidth", str(TILE))
    root.set("tileheight", str(TILE))
    root.set("infinite", "0")
    root.set("nextlayerid", "9")
    root.set("nextobjectid", "200")

    prop_el = ET.SubElement(root, "properties")
    for k, v in props.items():
        p = ET.SubElement(prop_el, "property")
        p.set("name", k)
        p.set("value", str(v))

    ts = ET.SubElement(root, "tileset")
    ts.set("firstgid", "1")
    ts.set("name", "tileset_stage0")
    ts.set("tilewidth", str(TILE))
    ts.set("tileheight", str(TILE))
    ts.set("tilecount", "4096")
    ts.set("columns", "64")
    img = ET.SubElement(ts, "image")
    img.set("source", TILESET_PATH)
    img.set("width", "1024")
    img.set("height", "1024")

    layer_names = ["BG_Far", "BG_Mid", "BG_Near", "Terrain", "Terrain_Detail", "FG_Overlay"]
    for i, name in enumerate(layer_names, 1):
        layer = ET.SubElement(root, "layer")
        layer.set("id", str(i))
        layer.set("name", name)
        layer.set("width", str(MAP_W))
        layer.set("height", str(MAP_H))
        data = ET.SubElement(layer, "data")
        data.set("encoding", "csv")
        if name == "Terrain":
            csv_lines = [csv_row(row) for row in g]
            data.text = "\n" + ",\n".join(csv_lines) + "\n"
        elif name == "Terrain_Detail":
            csv_lines = [csv_row(row) for row in detail]
            data.text = "\n" + ",\n".join(csv_lines) + "\n"
        else:
            empty = "0," * (MAP_W - 1) + "0"
            data.text = "\n" + ",\n".join([empty] * MAP_H) + "\n"

    # ── Collision layer ──
    collision = ET.SubElement(root, "objectgroup")
    collision.set("id", "7")
    collision.set("name", "Collision")

    def solid(oid, name, x, y, w, h, obj_type="Solid"):
        o = ET.SubElement(collision, "object")
        o.set("id", str(oid))
        o.set("name", name)
        o.set("type", obj_type)
        o.set("x", str(x))
        o.set("y", str(y))
        o.set("width", str(w))
        o.set("height", str(h))
        return o

    oid = 1
    # Walls
    solid(oid, "LeftWall", 0, 0, TILE, MAP_H * TILE); oid += 1
    solid(oid, "RightWall", (MAP_W - 1) * TILE, 0, TILE, MAP_H * TILE); oid += 1
    # Floor left (cols 1-53)
    solid(oid, "FloorLeft", TILE, 32 * TILE, (PIT_C1 - 1) * TILE, 6 * TILE); oid += 1
    # Floor right (cols 57-98)
    solid(oid, "FloorRight", (PIT_C2 + 1) * TILE, 32 * TILE, (MAP_W - PIT_C2 - 2) * TILE, 6 * TILE); oid += 1
    # Zone A: Platform 1 (col 6-8, row 30)
    solid(oid, "Plat_A1", P1_C1 * TILE, 30 * TILE, (P1_C2 - P1_C1 + 1) * TILE, TILE); oid += 1
    # Zone A: Platform 2 (col 11-13, row 28)
    solid(oid, "Plat_A2", 11 * TILE, 28 * TILE, 3 * TILE, TILE); oid += 1
    # Zone C: Flying platform (col 38-40, row 28)
    solid(oid, "Plat_C1", 38 * TILE, 28 * TILE, 3 * TILE, TILE); oid += 1
    # Zone C: Shooter platform (col 45-47, row 29)
    solid(oid, "Plat_C2", 45 * TILE, 29 * TILE, 3 * TILE, TILE); oid += 1
    # Zone D: High platform (col 58-62, row 30) — one-way, player jumps through from below
    solid(oid, "Plat_D1", P2_C1 * TILE, 30 * TILE, (P2_C2 - P2_C1 + 1) * TILE, TILE, "Platform"); oid += 1
    # Zone D: Pit cover (col 54-56, row 32) — ONE-WAY at floor level
    solid(oid, "PitCover", PIT_C1 * TILE, 32 * TILE, (PIT_C2 - PIT_C1 + 1) * TILE, TILE, "Platform"); oid += 1
    # Zone E: Hazard-side platform (col 74-78, row 29)
    solid(oid, "Plat_E1", 74 * TILE, 29 * TILE, 5 * TILE, TILE); oid += 1
    # Zone F: Final platform (col 88-92, row 27)
    solid(oid, "Plat_F1", 88 * TILE, 27 * TILE, 5 * TILE, TILE); oid += 1

    # ── Objects layer ──
    objects = ET.SubElement(root, "objectgroup")
    objects.set("id", "8")
    objects.set("name", "Objects")

    def obj(o2id, name, otype, x, y, w=16, h=32, props=None):
        o = ET.SubElement(objects, "object")
        o.set("id", str(o2id))
        o.set("name", name)
        o.set("type", otype)
        o.set("x", str(x))
        o.set("y", str(y))
        o.set("width", str(w))
        o.set("height", str(h))
        if props:
            p_el = ET.SubElement(o, "properties")
            for pk, pv in props.items():
                pp = ET.SubElement(p_el, "property")
                pp.set("name", pk)
                pp.set("value", str(pv))
        return o

    o2 = 1
    # Player spawn (Zone A, col 4, floor surface y=512 — Player rect offset handles height)
    obj(o2, "PlayerSpawn", "PlayerSpawn", 4 * TILE, 32 * TILE, TILE, 32); o2 += 1

    # ── ENEMIES ──
    # Enemy constructors expect `spawn_position.y` = FEET position (bottom of rect).
    # They internally do `position.y -= self.rect.height` to convert to top-left.
    # So for floor-standing: y = 512 (floor surface).
    # For platform: y = row * TILE (platform surface).

    # ── DAMAGE BALANCE ──
    # Player max HP = 5.0 (settings.PLAYER_MAX_HEALTH).
    # Demo values: 0.5-1.5 dmg/contact so player loses 1-3 hearts per hit.
    # Walker (patrol melee)
    D_WALKER = "1.0"
    # Flying (aerial, hard to hit)
    D_FLYING = "0.75"
    # Shooter (ranged, projectile does extra)
    D_SHOOTER = "0.75"
    P_SHOOTER = "2.0"
    # Charger (charge = big hit)
    D_CHARGER = "1.0"
    # Archer (ranged arc)
    D_ARCHER = "0.75"
    P_ARCHER = "2.0"
    # Brute (slow, heavy)
    D_BRUTE = "1.5"
    # Caster (homing orbs)
    D_CASTER = "0.75"
    P_CASTER = "2.0"
    # Assassin (squishy, burst)
    D_ASSASSIN = "1.0"

    # Zone B: 2 Walkers on floor
    obj(o2, "Walker_01", "Walker", 18 * TILE, 512,
        props={"zone": "0", "max_health": "3", "damage_on_contact": D_WALKER,
               "patrol_length": "64", "patrol_speed": "45", "alert_speed": "75"}); o2 += 1
    obj(o2, "Walker_02", "Walker", 28 * TILE, 512,
        props={"zone": "0", "max_health": "3", "damage_on_contact": D_WALKER,
               "patrol_length": "64", "patrol_speed": "45", "alert_speed": "75"}); o2 += 1

    # Zone C: Flying + Shooter + Charger
    obj(o2, "Flying_01", "Flying", 39 * TILE, 448,
        props={"zone": "0", "max_health": "2", "damage_on_contact": D_FLYING,
               "flight_mode": "sine", "flight_speed": "60",
               "sine_amplitude": "32", "sine_frequency": "2.0"}); o2 += 1
    obj(o2, "Shooter_01", "Shooter", 46 * TILE, 464,
        props={"zone": "0", "max_health": "3", "damage_on_contact": D_SHOOTER,
               "fire_rate": "1.5", "projectile_speed": "120",
               "projectile_damage": P_SHOOTER, "patrol_length": "32"}); o2 += 1
    obj(o2, "Charger_01", "Charger", 42 * TILE, 512,
        props={"zone": "0", "max_health": "4", "damage_on_contact": D_CHARGER,
               "charge_speed": "250"}); o2 += 1

    # Zone D: Archer on high platform row 30
    obj(o2, "Archer_01", "Archer", 60 * TILE, 480,
        props={"zone": "0", "max_health": "3", "damage_on_contact": D_ARCHER,
               "fire_rate": "2.0", "projectile_speed": "90",
               "projectile_damage": P_ARCHER}); o2 += 1

    # Zone E: Brute on floor
    obj(o2, "Brute_01", "Brute", 76 * TILE, 512,
        props={"zone": "0", "max_health": "5", "damage_on_contact": D_BRUTE}); o2 += 1

    # Zone F: Caster + Assassin
    obj(o2, "Caster_01", "Caster", 90 * TILE, 432,
        props={"zone": "0", "max_health": "3", "damage_on_contact": D_CASTER,
               "fire_rate": "2.0", "projectile_speed": "100",
               "projectile_damage": P_CASTER}); o2 += 1
    obj(o2, "Assassin_01", "Assassin", 86 * TILE, 512,
        props={"zone": "0", "max_health": "2", "damage_on_contact": D_ASSASSIN,
               "patrol_length": "80", "patrol_speed": "60", "alert_speed": "90"}); o2 += 1

    # ── CHECKPOINTS ──
    for i, x in enumerate([22, 44, 74, 94]):
        obj(o2, f"Checkpoint_{i}", "Checkpoint", x * TILE, (32 * TILE) - 32,
            props={"checkpoint_id": str(i)}); o2 += 1

    # ── MESSAGE TRIGGERS ──
    msgs = [
        (5,  "Presiona A/D para moverte, W para saltar, S para agacharte"),
        (17, "Presiona ESPACIO o J para atacar. SHIFT para dashear!"),
        (37, "¡Enemigos voladores y a distancia! Usa P o K para parry."),
        (52, "�Saltos verticales! Algunas plataformas estan muy altas. Agachate (S) para caer por plataformas de una via."),
        (69, "¡Zonas rojas son peligrosas! Evita las areas de daño."),
        (85, "¡Combina todas tus habilidades! Presiona U para ataque definitivo."),
    ]
    for x_col, txt in msgs:
        obj(o2, f"MsgTrigger_{x_col}", "MessageTrigger_Once",
            x_col * TILE, (32 * TILE) - 4, 4 * TILE, TILE,
            props={"text": txt}); o2 += 1

    # ── DEATH PIT (below floor gap) ──
    obj(o2, "DeathPit", "DeathPit",
        PIT_C1 * TILE, (32 * TILE) + 4, (PIT_C2 - PIT_C1 + 1) * TILE, TILE); o2 += 1

    # ── HAZARD ZONE (spikes on floor) ──
    obj(o2, "HazardZone", "HazardZone",
        70 * TILE, (32 * TILE) - 4, 3 * TILE, TILE,
        props={"damage": "0.25"}); o2 += 1

    # ── NEXT TRIGGER (stage exit) ──
    obj(o2, "NextTrigger", "NextTrigger",
        96 * TILE, (32 * TILE) - 64, 2 * TILE, 6 * TILE); o2 += 1

    # ── CAMERA LOCK ZONES (optional) ──
    # Zone A: locked at start (reveal on move)
    # Zone D: unlock near pit

    # Write
    tree = ET.ElementTree(root)
    os.makedirs(OUT_DIR, exist_ok=True)
    ET.indent(tree, space="  ")
    tree.write(OUT_PATH, encoding="utf-8", xml_declaration=True)
    print(f"Generated {OUT_PATH} ({MAP_W}x{MAP_H} tiles, {MAP_W * TILE}x{MAP_H * TILE} px)")
    print("Zones: A(cols 2-15) B(16-35) C(36-51) D(52-67) E(68-84) F(85-98)")
    print("Enemies: 2 Walkers, 1 Flying, 1 Shooter, 1 Charger, 1 Archer, 1 Brute, 1 Caster, 1 Assassin")
    print("Checkpoints: 4 | Messages: 6 | Platforms: 8 (1 one-way)")


if __name__ == "__main__":
    make_tmx()
