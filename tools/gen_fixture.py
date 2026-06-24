from pathlib import Path


def main() -> None:
    fixture_path = Path("tests/fixtures/minimal_stage.tmx")
    fixture_path.parent.mkdir(parents=True, exist_ok=True)

    empty = ",".join(["0"] * 280)
    terrain = empty[:-2] + ",1" + ",1" * 19

    layers = "\n".join(
        f'  <layer name="{n}" width="20" height="14">\n'
        f'    <data encoding="csv">{empty}</data>\n'
        f"  </layer>"
        for n in [
            "BG_Far",
            "BG_Mid",
            "BG_Near",
            "Terrain_Detail",
            "FG_Overlay",
        ]
    )

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" orientation="orthogonal" renderorder="right-down"
     width="20" height="14" tilewidth="16" tileheight="16"
     infinite="0" nextobjectid="1">
  <properties>
    <property name="stage_id" value="minimal"/>
    <property name="stage_name" value="Minimal Stage"/>
    <property name="time_limit" type="int" value="120"/>
    <property name="bgm_track" value="bgm_test"/>
  </properties>
  <tileset firstgid="1" source="../assets/tileset_stage0.tsx"/>
  <layer name="Terrain" width="20" height="14">
    <data encoding="csv">{terrain}</data>
  </layer>
{layers}
  <objectgroup name="Objects">
    <object id="1" type="PlayerSpawn" name="PlayerSpawn_01" x="32" y="192"/>
    <object id="2" type="Walker" name="Walker_01" x="120" y="192"/>
    <object id="3" type="Checkpoint" name="Checkpoint_01" x="200" y="160" width="24" height="32">
      <properties><property name="checkpoint_id" type="int" value="0"/></properties>
    </object>
    <object id="4" type="NextTrigger" name="NextTrigger_01" x="280" y="160" width="40" height="64"/>
  </objectgroup>
  <objectgroup name="Collision">
    <object id="5" name="Solid_Floor" x="0" y="208" width="320" height="16"/>
    <object id="6" name="Solid_plat" x="100" y="176" width="64" height="8"/>
  </objectgroup>
</map>
"""

    fixture_path.write_text(xml, encoding="utf-8")
    print(f"Generated: {fixture_path}")


if __name__ == "__main__":
    main()