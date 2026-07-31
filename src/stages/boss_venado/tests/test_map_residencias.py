"""
Module: test_map_residencias
System: tests
Description: TMX del mapa residencias - contrato de 06_TMX_SPEC y spec 2026-07-23.
"""
from __future__ import annotations

import importlib
import os
import xml.etree.ElementTree as ET

TMX = os.path.join("assets", "maps", "boss_venado", "boss_venado.tmx")
LAYERS = ["BG_Far", "BG_Mid", "BG_Near", "Terrain", "Terrain_Detail", "Objects", "Collision", "FG_Overlay"]


def _root() -> ET.Element:
    importlib.import_module("src.stages.boss_venado.tools.gen_level_residencias").main()
    return ET.parse(TMX).getroot()


def test_dimensions_and_properties() -> None:
    r = _root()
    # ROUND-11 (deliberate spec amendment): map widened to 205x38 (3280x608) with a
    # new CARPORT zone inserted and every zone made a bit more extensive.
    assert (r.get("width"), r.get("height")) == ("205", "38")
    props = {p.get("name"): p.get("value") for p in r.find("properties")}
    assert props["stage_id"] == "boss_venado"
    assert props["bgm_track"] == "bgm_zone1_boss"
    assert props["time_limit"] == "0"
    # typed-property contract: read the property elements (dict of name -> element)
    prop_els = {p.get("name"): p for p in r.find("properties")}
    assert prop_els["time_limit"].get("type") == "int"
    assert props["stage_name"] == "VENADO"
    assert props["background_zone"] == "zone1"


def test_eight_layers_in_order() -> None:
    r = _root()
    names = [el.get("name") for el in r if el.tag in ("layer", "objectgroup")]
    assert names == LAYERS


def test_objects_contract() -> None:
    """ENGINE V2 note: this map used to also carry an ``ArenaZone_01`` marker
    object (type="ArenaZone", purely descriptive -- no code ever read it, the
    arena bounds live in the ``ARENA_X0``/``ARENA_X1`` constants in
    ``boss_venado.py``/``boss_venado_scene.py``). StageLoader V2's object
    validator (``tmx_diagnostics.BUILTIN_OBJECT_TYPES``) now raises
    ``FrameworkUsageError`` on any object type it doesn't recognize, and there
    is no generic inert marker type to re-tag it as, so the generator dropped
    it (see ``gen_level_residencias._objects_xml``). The arena rect it used to
    document is still verified below through ``CameraLock_01``, a builtin type
    the loader does accept, which covers the exact same rect.
    """
    r = _root()
    objs = {o.get("name"): o for og in r.findall("objectgroup") if og.get("name") == "Objects" for o in og}
    assert "PlayerSpawn_01" in objs and "BossVenado_01" in objs
    assert "ArenaZone_01" not in objs
    assert "CameraLock_01" in objs
    assert not any(n.startswith("NextTrigger") for n in objs)
    cl = objs["CameraLock_01"]
    assert (cl.get("x"), cl.get("y"), cl.get("width"), cl.get("height")) == ("2480", "0", "800", "608")
    # CameraLock switch properties are typed booleans set true
    cl_props = {p.get("name"): p for p in cl.find("properties")}
    for key in ("lock_x", "lock_y"):
        assert cl_props[key].get("type") == "bool"
        assert cl_props[key].get("value") == "true"
    # PlayerSpawn at the meadow start (feet at the ground plane)
    ps = objs["PlayerSpawn_01"]
    assert (ps.get("x"), ps.get("y")) == ("48", "560")
    # Boss spawn shifted with the arena to x=2880/y=240 (r11), then moved to the
    # arena's far right (x=3168/y=240, r12 -- user feedback "pon el boss al final
    # del mapa": past the gazebo, close to RightWall_Arena), still with NO custom
    # properties: the professor's original BossVenado.__init__(spawn_position) takes
    # no kwargs and StageLoader passes every TMX object property as a kwarg, so any
    # property here would crash the real game (see test_entities_instantiate_from_tmx).
    bv = objs["BossVenado_01"]
    assert (bv.get("x"), bv.get("y")) == ("3168", "240")
    bv_props_el = bv.find("properties")
    assert bv_props_el is None or len(bv_props_el) == 0


def test_collision_floor_and_walls() -> None:
    r = _root()
    col = {o.get("name"): o for og in r.findall("objectgroup") if og.get("name") == "Collision" for o in og}
    assert col["Floor"].get("y") == "560" and col["Floor"].get("width") == "3280"   # r11: full width
    assert "LeftWall_World" in col and "RightWall_Arena" in col
    assert col["RightWall_Arena"].get("x") == "3264"                                 # (W-1)*16


def test_gids_reference_tileset() -> None:
    from src.stages.boss_venado.tools.gen_level_residencias import TILECOUNT
    r = _root()
    ts = r.find("tileset")
    assert ts.get("tilecount") == str(TILECOUNT)      # single source of truth wired in
    firstgid = int(ts.get("firstgid"))
    maxgid = firstgid + TILECOUNT
    for layer in r.findall("layer"):
        data = layer.find("data").text
        gids = [int(g) for g in data.replace("\n", "").split(",")]
        assert max(gids) < maxgid
        assert min(gids) >= 0


def test_layer_grid_integrity() -> None:
    r = _root()
    layers = r.findall("layer")
    assert len(layers) == 6                            # the six tile layers
    for layer in layers:
        cells = layer.find("data").text.replace("\n", "").split(",")
        assert len(cells) == 205 * 38                  # exactly one gid per map cell (r11)


def test_tileset_image_has_colorkey() -> None:
    r = _root()
    img = r.find("tileset").find("image")
    assert img.get("trans") == "000000"                # black -> transparent (overlays/telescope)


def test_tileset_image_size_matches_atlas_png() -> None:
    """ROUND-11 anti-regression for the round-10 bug: the <image> width/height the
    TMX DECLARES must equal the ACTUAL size of the atlas PNG. pytmx slices the
    tileset by the declared height, so if the atlas grows (more tiles -> more rows)
    but the declared height lags, every tile in the extra rows is silently DROPPED
    at render time (which is exactly what left the gazebo's base rendering as a
    sky-void in round 10). Cheap to guard, catches it forever.

    Deliberately reads the DEPLOYED atlas PNG straight from the game tree
    (read-only, never regenerated here): the invariant under test is that the
    artifact actually shipped on disk -- the one pytmx loads at runtime --
    still matches what the TMX declares. Regenerating a scratch copy instead
    would make this guard vacuous (it would always pass even if nobody re-ran
    ``python -m tools.gen_tileset_residencias`` after growing the atlas).
    """
    from PIL import Image

    r = _root()
    img_el = r.find("tileset").find("image")
    declared = (int(img_el.get("width")), int(img_el.get("height")))
    atlas = os.path.join("assets", "tilesets", "tileset_residencias_crepusculo.png")
    with Image.open(atlas) as im:
        assert im.size == declared, f"declared {declared} != atlas PNG {im.size}"


def test_build_is_byte_idempotent() -> None:
    g = importlib.import_module("src.stages.boss_venado.tools.gen_level_residencias")
    assert g.build_tmx() == g.build_tmx()              # pure composition, no hidden state
    g.main()
    with open(TMX, "rb") as f:
        first = f.read()
    g.main()
    with open(TMX, "rb") as f:
        second = f.read()
    assert first == second                             # written bytes are stable


def test_loads_in_engine_headless() -> None:
    from src.framework.stage.stage_loader import StageLoader
    stage = StageLoader.load(TMX)
    assert stage is not None


def test_tmx_declares_lighting_properties() -> None:
    """Feature B, recalibrated (user decision, visual critique round 2): only
    6 lighting/atmosphere properties are declared -- ``start_hour``/``season``
    were retired (see test below), because leaving them in made the engine
    clamp the composed ambient to the rejected ``MIN_AMBIENTE=0.45`` floor
    (see the calculation in ``gen_level_residencias.build_tmx``). The raw
    ``ambient_light`` here is 0.55; the actual runtime-composed value is
    locked separately by test_effective_ambient_stays_above_playable_floor,
    since the two are NOT the same number (the engine still applies a
    default-season multiplier even with no season declared).
    """
    r = _root()
    prop_els = {p.get("name"): p for p in r.find("properties")}
    expected_types = {
        "zone": "int",
        "ambient_light": "float",
        "bloom": "float",
        "vignette": "float",
        "ambient_fx": "string",
        "ambient_fx_rate": "float",
    }
    for name, ptype in expected_types.items():
        assert name in prop_els, f"missing property {name}"
        assert prop_els[name].get("type") == ptype

    props = {p.get("name"): p.get("value") for p in r.find("properties")}
    assert props["zone"] == "1"
    assert float(props["ambient_light"]) == 0.55
    assert props["ambient_fx"] == "leaves"


def test_tmx_omits_climate_day_length_start_hour_and_season() -> None:
    """Deliberate non-adoption, extended by the recalibration:

    - ``climate="storm"`` implies weather VFX never seen/approved in the 12
      map-critique rounds (spec sec. 2.1) -- unchanged.
    - ``day_length`` would unfreeze the day/night clock mid-fight -- unchanged.
    - ``start_hour``/``season`` are a NEW omission (user decision, round 2):
      the tileset's palette is already painted for dusk, so letting the
      engine's time-of-day/season tinting multiply on top of it is redundant
      -- and measurably harmful (it clamped the composed ambient to the
      rejected 0.45 floor; see gen_level_residencias.build_tmx's comment for
      the exact numbers). None of these four are a gap: all four are
      decisions, and this test keeps that intent executable.
    """
    r = _root()
    prop_names = {p.get("name") for p in r.find("properties")}
    assert "climate" not in prop_names
    assert "day_length" not in prop_names
    assert "start_hour" not in prop_names
    assert "season" not in prop_names


def test_effective_ambient_stays_above_playable_floor() -> None:
    """Regression lock for the round-2 recalibration: what matters is not the
    raw ``ambient_light`` property but the ambient the ENGINE actually
    applies at runtime, composed through the exact same formula/constants as
    ``StageScene._aplicar_hora`` (stage_scene.py:518-526) -- called here
    read-only, not re-derived by hand, so this can't silently drift from the
    real motor logic. The user explicitly rejected landing on the structural
    floor ("el look nocturno 0.45 queda descartado"), so this asserts the
    composed value clears it with real margin, not just technically above it.
    """
    from src.framework.scenes.stage_scene import StageScene
    from src.framework.stage.day_night import RelojDeMundo
    from src.framework.stage.seasons import estacion
    from src.framework.stage.stage_loader import StageLoader

    _root()
    stage = StageLoader.load(TMX)
    # Both omitted (see test above); this pins the exact fallback the engine
    # takes for each, which is what the recalibration comment's math depends on.
    assert stage.start_hour is None
    assert stage.season == ""

    hora = stage.start_hour if stage.start_hour is not None else StageScene.HORA_POR_DEFECTO
    reloj = RelojDeMundo(hora_inicial=hora, duracion_dia=stage.day_length or 0.0)
    luz = reloj.luz()
    est = estacion(stage.season)
    composed = max(
        StageScene.MIN_AMBIENTE,
        stage.ambient_light * luz.factor_ambiente * est.factor_luz,
    )

    assert 0.58 <= composed <= 0.60, (
        f"composed ambient {composed:.4f} left the requested ~0.58-0.60 band"
    )
    assert composed >= 0.55
    assert composed > StageScene.MIN_AMBIENTE + 0.05, (
        f"composed ambient {composed:.4f} is too close to the rejected "
        f"MIN_AMBIENTE={StageScene.MIN_AMBIENTE} floor"
    )


def test_tmx_has_five_light_objects() -> None:
    r = _root()
    objs = [o for og in r.findall("objectgroup") if og.get("name") == "Objects" for o in og]
    lights = [o for o in objs if o.get("type") == "Light"]
    assert len(lights) == 5


def test_light_positions_match_lamp_props() -> None:
    """Each 'lamp' light's declared rect, centred the way
    ``StageLoader._handle_light`` centres it, must fall on the exact tile the
    compositor already stamped with ``lamp_top`` -- so a future zone shift
    (the columns are constants, e.g. ``CARPORT.start + 3``) can't silently
    detach a light from its lamp prop. The cold oculo accent has no lamp prop
    to anchor to (spec sec. 2.1) so it is only checked against its own
    declared tile.
    """
    from src.stages.boss_venado.tools.gen_level_residencias import _gid, _LIGHTS, TILE, W

    r = _root()
    objs = [o for og in r.findall("objectgroup") if og.get("name") == "Objects" for o in og]
    lights_by_name = {o.get("name"): o for o in objs if o.get("type") == "Light"}
    assert set(lights_by_name) == {spec["name"] for spec in _LIGHTS}

    detail_layer = next(layer for layer in r.findall("layer") if layer.get("name") == "Terrain_Detail")
    gids = [int(g) for g in detail_layer.find("data").text.replace("\n", "").split(",")]
    lamp_gid = _gid("lamp_top")

    for spec in _LIGHTS:
        light = lights_by_name[spec["name"]]
        x, y = float(light.get("x")), float(light.get("y"))
        w, h = float(light.get("width", 0)), float(light.get("height", 0))
        cx, cy = x + w / 2, y + h / 2
        col, row = spec["col"], spec["row"]
        assert col * TILE <= cx < (col + 1) * TILE
        assert row * TILE <= cy < (row + 1) * TILE
        if spec.get("anchor") == "lamp":
            assert gids[row * W + col] == lamp_gid, f"{spec['name']} is not over a lamp_top tile"


def test_tmx_still_loads_with_stage_loader() -> None:
    """Smoke: ``Light`` stays a recognized builtin object type and none of
    the new float/string/bool properties trips ``_safe_float``/``_safe_int``
    after this feature's additions.
    """
    from src.framework.stage.stage_loader import StageLoader

    _root()
    stage = StageLoader.load(TMX)
    assert stage is not None
    assert len(stage.lights) == 5
    assert stage.ambient_light is not None
    assert stage.ambient_light == 0.55


def test_entities_instantiate_from_tmx() -> None:
    """Reproduce the REAL game path (App.__init__ -> ensure_registered()).

    ``test_loads_in_engine_headless`` above loads the TMX with an EMPTY entity
    registry (this pytest process never boots App), so StageLoader silently
    SKIPS the ``BossVenado`` object via its no-``else`` if/elif fallthrough --
    it never actually instantiates the boss, which is exactly why the
    constructor/TMX-property mismatch (arena_origin_x/y) slipped past CI and
    only blew up once ``capture_map.py`` booted a real App.

    Here we register the entity classes the way ``App.__init__`` does
    (``entity_factory.ensure_registered()`` -> ``StageLoader.register_entity``),
    then load the TMX. Now the loader takes the ``obj_type in _entity_registry``
    branch and runs ``BossVenado(Vector2(2000, 240), **props)``: a stray TMX
    property would raise ``TypeError`` and abort the whole stage load (== the
    real ``python main.py --boss boss_venado`` crash). Passing == the boss
    object instantiates and lands in ``entity_list``.
    """
    from src.framework.entities.boss_base import BossBase
    from src.framework.entities.entity_factory import ensure_registered
    from src.framework.stage.stage_loader import StageLoader

    _root()  # (re)generate the current TMX on disk
    ensure_registered()  # idempotent; registers "BossVenado" -> BossVenado class
    assert "BossVenado" in StageLoader._entity_registry

    stage = StageLoader.load(TMX)  # must NOT raise TypeError on BossVenado_01
    bosses = [e for e in stage.entity_list if isinstance(e, BossBase)]
    assert len(bosses) == 1, f"expected exactly one boss entity, got {len(bosses)}"
