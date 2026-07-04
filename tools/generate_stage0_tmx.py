#!/usr/bin/env python3
"""Generate the full Stage 0 TMX map with all 7 zones (A-G), 240 tiles wide."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TMX_PATH = PROJECT_ROOT / "assets" / "maps" / "stage0" / "stage0.tmx"
TILESET_PATH = "../../tilesets/tileset_stage0.png"

MW, MH = 240, 14  # map dimensions in tiles
TS = 16  # tile size

# ── Tile indices (0=empty, 1=floor, 2=wall, 3=platform) ──
# Generate terrain grid
terrain = [[0] * MW for _ in range(MH)]

# Floor (rows 12-13)
for y in range(12, 14):
    for x in range(MW):
        terrain[y][x] = 1

# Zone A platforms (X=280-360, 420-500, Y=160 -> tile row 10)
for x in range(17, 23):
    terrain[10][x] = 3  # platform 1
for x in range(26, 32):
    terrain[10][x] = 3  # platform 2

# Zone C platforms (X=1200-1360, 1440-1600, Y=160 -> tile row 10)
for x in range(75, 86):
    terrain[10][x] = 3  # platform 1
for x in range(90, 101):
    terrain[10][x] = 3  # platform 2

# Zone E death pit (X=2240-2304 -> tile col 140-144)
for y in range(12, 14):
    for x in range(140, 145):
        terrain[y][x] = 0

# Zone E one-way platform over pit (tile row 11, Y=176)
for x in range(140, 145):
    terrain[11][x] = 3

# Walls at stage edges
# Left wall (tile col 0)
for y in range(12):
    terrain[y][0] = 2
# Right wall
for y in range(12):
    terrain[y][MW-1] = 2


def _gen_collision_rects():
    """Generate TMX rect objects from the terrain grid, merging contiguous solid tiles.
    Tile 1=floor, 2=wall → type Solid.
    Tile 3=platform → type Platform (one-way: passable from below)."""
    solid_rects = []
    platform_rects = []
    oid = 100
    for y in range(MH):
        start_x = None
        tile_type = None
        for x in range(MW):
            t = terrain[y][x]
            if t in (1, 2, 3):
                if start_x is None:
                    start_x = x
                    tile_type = t
            else:
                if start_x is not None:
                    rx = start_x * TS
                    rw = (x - start_x) * TS
                    entry = (oid, rx, y * TS, rw, TS)
                    if tile_type == 3:
                        platform_rects.append(entry)
                    else:
                        solid_rects.append(entry)
                    oid += 1
                    start_x = None
                    tile_type = None
        if start_x is not None:
            rx = start_x * TS
            rw = (MW - start_x) * TS
            entry = (oid, rx, y * TS, rw, TS)
            if tile_type == 3:
                platform_rects.append(entry)
            else:
                solid_rects.append(entry)
            oid += 1
    for oid, rx, ry, rw, rh in solid_rects:
        yield f'  <object id="{oid}" name="Solid" type="Solid" x="{rx}" y="{ry}" width="{rw}" height="{rh}"/>'
    for oid, rx, ry, rw, rh in platform_rects:
        yield f'  <object id="{oid}" name="Platform" type="Platform" x="{rx}" y="{ry}" width="{rw}" height="{rh}"/>'


def _iter_objects():
    """Yield TMX object entries for all entities, triggers, and zones."""
    # PlayerSpawn (y = floor surface = terrain row 12 * TS = 192)
    yield """  <object id="1" name="PlayerSpawn" type="PlayerSpawn" x="48" y="192" width="16" height="16"/>"""

    # ── Zone A: Messages ──
    objs = [
        (2, "MSG_01", "MessageTrigger", 160, 192, 32, 32, {"text": "Use arrow keys or left stick to walk. Press Space or A to jump."}),
        (3, "MSG_02", "MessageTrigger", 260, 192, 32, 32, {"text": "Jump to reach elevated platforms. You have 6 frames of coyote time at ledge edges."}),
        (4, "MSG_03", "MessageTrigger", 400, 192, 32, 32, {"text": "Hold jump longer for a higher jump. Release early for a short hop."}),
        (5, "MSG_04", "MessageTrigger", 520, 192, 32, 32, {"text": "Press Down to crouch. Crouching reduces your hurtbox size."}),
    ]

    # ── Zone B: Messages + Walkers ──
    objs += [
        (6, "MSG_05", "MessageTrigger", 640, 192, 32, 32, {"text": "Press Z for Short Attack (fists). Press X for Long Attack (stick)."}),
        (7, "MSG_06", "MessageTrigger", 700, 192, 32, 32, {"text": "Short Attack: 0.5 heart damage, fast recovery. Long Attack: 1.0 heart damage, wider reach."}),
        (8, "MSG_07", "MessageTrigger", 840, 192, 32, 32, {"text": "Notice the hitstop effect on hit. Time briefly slows."}),
        (9, "MSG_08", "MessageTrigger", 1000, 192, 32, 32, {"text": "Try crouching then attacking. The hitbox shifts to hit low targets."}),
        # Walkers in Zone B
        (10, "Walker_01", "Walker", 760, 164, 16, 16, {}),
        (11, "Walker_02", "Walker", 900, 164, 16, 16, {}),
        (12, "Walker_03", "Walker", 1040, 164, 16, 16, {}),
        # Checkpoint 1
        (13, "Checkpoint_01", "Checkpoint", 1080, 160, 24, 32, {"checkpoint_id": "0"}),
    ]

    # ── Zone C: Messages + Walkers + Platform ──
    objs += [
        (14, "MSG_09", "MessageTrigger", 1120, 192, 32, 32, {"text": "Walker enemies patrol back and forth. They detect ledge edges automatically."}),
        (15, "MSG_10", "MessageTrigger", 1200, 192, 32, 32, {"text": "When you enter their detection range, Walkers accelerate toward you."}),
        (16, "MSG_11", "MessageTrigger", 1360, 192, 32, 32, {"text": "If a Walker touches you, you lose 0.5 hearts. You become invincible briefly."}),
        (17, "MSG_12", "MessageTrigger", 1520, 192, 32, 32, {"text": "Watch the sprite flash during invincibility. This is damage feedback."}),
        # Walkers in Zone C
        (18, "Walker_04", "Walker", 1260, 132, 16, 16, {}),
        (19, "Walker_05", "Walker", 1480, 164, 16, 16, {}),
        # Checkpoint 2
        (20, "Checkpoint_02", "Checkpoint", 1560, 160, 24, 32, {"checkpoint_id": "1"}),
    ]

    # ── Zone D: Messages + Flying enemies ──
    objs += [
        (21, "MSG_13", "MessageTrigger", 1600, 192, 32, 32, {"text": "Flying enemies move along computed paths. The first uses a sine wave trajectory."}),
        (22, "MSG_14", "MessageTrigger", 1780, 192, 32, 32, {"text": "Sine wave: pos.y = origin + A * sin(2*pi*f*t). Amplitude and frequency are TMX properties."}),
        (23, "MSG_15", "MessageTrigger", 1880, 192, 32, 32, {"text": "The second Flying enemy uses a Bezier curve path. Four control points define the trajectory."}),
        (24, "MSG_16", "MessageTrigger", 2000, 192, 32, 32, {"text": "Press F1 to toggle debug view. You can see Bezier control points and sampled path."}),
        # Flying enemies
        (25, "Flying_01", "Flying", 1700, 112, 16, 12, {"flight_mode": "sine"}),
        (26, "Flying_02", "Flying", 1900, 80, 16, 12, {"flight_mode": "bezier"}),
        # Waypoints for Flying_02 (S-curve)
        (49, "Waypoint_01", "Waypoint", 1900, 80, 8, 8, {"owner_id": "Flying_02"}),
        (50, "Waypoint_02", "Waypoint", 1800, 40, 8, 8, {"owner_id": "Flying_02"}),
        (51, "Waypoint_03", "Waypoint", 1700, 80, 8, 8, {"owner_id": "Flying_02"}),
        (52, "Waypoint_04", "Waypoint", 1800, 120, 8, 8, {"owner_id": "Flying_02"}),
        # Checkpoint 3
        (27, "Checkpoint_03", "Checkpoint", 2040, 160, 24, 32, {"checkpoint_id": "2"}),
    ]

    # ── Zone E: Messages + Shooter + DeathPit ──
    objs += [
        (28, "MSG_17", "MessageTrigger", 2080, 192, 32, 32, {"text": "Shooter enemies fire projectiles when you enter range. Angle computed with atan2."}),
        (29, "MSG_18", "MessageTrigger", 2160, 192, 32, 32, {"text": "angle = atan2(dy, dx) from shooter to player. This is Unit II vector math."}),
        (30, "MSG_19", "MessageTrigger", 2240, 192, 32, 32, {"text": "The gap ahead has a one-way platform. Jump up through it; fall back down."}),
        (31, "MSG_20", "MessageTrigger", 2360, 192, 32, 32, {"text": "Crouch to avoid projectiles that fly high. Time movement between shots."}),
        # Shooter enemies
        (32, "Shooter_01", "Shooter", 2400, 192, 16, 16, {}),
        (33, "Shooter_02", "Shooter", 2500, 192, 16, 16, {}),
        # Death pit
        (34, "DeathPit_01", "DeathPit", 2240, 208, 64, 16, {}),
        # Checkpoint 4
        (35, "Checkpoint_04", "Checkpoint", 2520, 160, 24, 32, {"checkpoint_id": "3"}),
    ]

    # ── Zone F: Messages + Walkers + Hazard ──
    objs += [
        (36, "MSG_21", "MessageTrigger", 2560, 192, 32, 32, {"text": "The HUD shows health (hearts) and the stage timer. Portrait is the player avatar."}),
        (37, "MSG_22", "MessageTrigger", 2640, 192, 32, 32, {"text": "The red Walker deals 1.0 heart damage. Heavy damage enemies are marked differently."}),
        (38, "MSG_23", "MessageTrigger", 2760, 192, 32, 32, {"text": "If health reaches 0, Game Over appears. You can continue from the last checkpoint."}),
        (39, "MSG_24", "MessageTrigger", 3040, 192, 32, 32, {"text": "The spike floor deals 0.25 heart damage per tick. This is the Light damage tier."}),
        # Walkers in Zone F
        (40, "Walker_06", "Walker", 2680, 164, 16, 16, {"damage_on_contact": "1.0"}),
        (41, "Walker_07", "Walker", 2820, 164, 16, 16, {}),
        (42, "Walker_08", "Walker", 2960, 164, 16, 16, {}),
        # Hazard zone
        (43, "HazardZone_A", "HazardZone", 3040, 176, 48, 16, {"damage": "0.25"}),
        # Checkpoint 5
        (44, "Checkpoint_05", "Checkpoint", 3160, 160, 24, 32, {"checkpoint_id": "4"}),
    ]

    # ── Zone G: Messages + NextTrigger ──
    objs += [
        (45, "MSG_25", "MessageTrigger", 3200, 192, 32, 32, {"text": "You have demonstrated all framework systems. Walk right to complete Stage 0."}),
        (46, "MSG_26", "MessageTrigger", 3500, 192, 32, 32, {"text": "Your stages (1, 2, 3) build on everything shown here. Study the source code."}),
        (47, "MSG_27", "MessageTrigger", 3680, 192, 32, 32, {"text": "Step through the arch to proceed. Good luck."}),
        # Exit
        (48, "NextTrigger_01", "NextTrigger", 3720, 160, 40, 64, {}),
    ]

    for oid, name, otype, x, y, w, h, props in objs:
        prop_str = ""
        if props:
            pxml = "".join(f'<property name="{k}" value="{v}"/>' for k, v in props.items())
            prop_str = f" <properties>{pxml}</properties>"
        yield f'  <object id="{oid}" name="{name}" type="{otype}" x="{x}" y="{y}" width="{w}" height="{h}">{prop_str}</object>'


def generate_tmx():
    # CSV terrain data (single-line to avoid pytmx newline issues)
    csv_data = ",".join(str(terrain[y][x]) for y in range(MH) for x in range(MW))
    zeros_csv = ",".join(["0"] * (MW * MH))

    object_entries = "\n".join(_iter_objects())
    collision_entries = "\n".join(_gen_collision_rects())

    tmx = f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.11.0" orientation="orthogonal"
     renderorder="right-down" width="{MW}" height="{MH}"
     tilewidth="{TS}" tileheight="{TS}" infinite="0"
     nextlayerid="9" nextobjectid="150">
 <properties>
  <property name="stage_id" value="stage0"/>
  <property name="stage_name" value="STAGE 0  PROLOGUE"/>
  <property name="time_limit" value="0"/>
  <property name="bgm_track" value="bgm_stage0"/>
 </properties>
 <tileset firstgid="1" name="tileset_stage0" tilewidth="{TS}"
          tileheight="{TS}" tilecount="64" columns="8">
  <image source="{TILESET_PATH}"
         width="{TS * 8}" height="{TS * 8}"/>
 </tileset>
 <layer id="1" name="BG_Far" width="{MW}" height="{MH}">
  <data encoding="csv">
{zeros_csv}
  </data>
 </layer>
 <layer id="2" name="BG_Mid" width="{MW}" height="{MH}">
  <data encoding="csv">
{zeros_csv}
  </data>
 </layer>
 <layer id="3" name="BG_Near" width="{MW}" height="{MH}">
  <data encoding="csv">
{zeros_csv}
  </data>
 </layer>
 <layer id="4" name="Terrain" width="{MW}" height="{MH}">
  <data encoding="csv">
{csv_data}
  </data>
 </layer>
 <layer id="5" name="Terrain_Detail" width="{MW}" height="{MH}">
  <data encoding="csv">
{zeros_csv}
  </data>
 </layer>
 <layer id="6" name="FG_Overlay" width="{MW}" height="{MH}">
  <data encoding="csv">
{zeros_csv}
  </data>
 </layer>
 <objectgroup id="7" name="Collision">
{collision_entries}
 </objectgroup>
 <objectgroup id="8" name="Objects">
{object_entries}
 </objectgroup>
</map>"""

    TMX_PATH.parent.mkdir(parents=True, exist_ok=True)
    TMX_PATH.write_text(tmx, encoding="utf-8")
    n_collision = sum(1 for _ in _gen_collision_rects())
    print(f"Created Stage 0 TMX: {TMX_PATH}")
    print(f"  Map: {MW}x{MH} tiles ({MW*TS}x{MH*TS} px)")
    print("  Zones: A-G with 27 message triggers, 8 walkers, 2 flying, 2 shooters")
    print("  Checkpoints: 5, Death pits: 1, Hazard zones: 1")
    print(f"  Collision rects: {n_collision} (merged from terrain grid)")


if __name__ == "__main__":
    generate_tmx()
