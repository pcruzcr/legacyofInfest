"""
Modulo: test_map_residencias
Sistema: tests
Descripcion: TMX del mapa residencias - contrato de 06_TMX_SPEC y spec 2026-07-23.
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
    # RONDA-11 (enmienda deliberada de la spec): el mapa se ensancho a 205x38 (3280x608)
    # con una nueva zona CARPORT insertada y todas las zonas hechas un poco mas extensas.
    assert (r.get("width"), r.get("height")) == ("205", "38")
    props = {p.get("name"): p.get("value") for p in r.find("properties")}
    assert props["stage_id"] == "boss_venado"
    assert props["bgm_track"] == "bgm_zone1_boss"
    assert props["time_limit"] == "0"
    # contrato de propiedad tipada: leer los elementos de propiedad (dict de nombre -> elemento)
    prop_els = {p.get("name"): p for p in r.find("properties")}
    assert prop_els["time_limit"].get("type") == "int"
    assert props["stage_name"] == "VENADO"
    assert props["background_zone"] == "zone1"


def test_eight_layers_in_order() -> None:
    r = _root()
    names = [el.get("name") for el in r if el.tag in ("layer", "objectgroup")]
    assert names == LAYERS


def test_objects_contract() -> None:
    """Historia completa de ``ArenaZone_01`` (para quien audite el porque,
    no solo la presencia del objeto):

    - NACIO en la ronda 11 como marcador PURAMENTE descriptivo (type=
      "ArenaZone") que dibujaba en Tiled el mismo rectangulo que las
      constantes ``ARENA_X0``/``ARENA_X1`` de
      ``boss_venado.py``/``boss_venado_scene.py`` ya fijaban en codigo --
      ningun loader lo leia jamas.
    - MOTOR V2 lo elimino: el validador de objetos de StageLoader V2
      (``tmx_diagnostics.BUILTIN_OBJECT_TYPES``) empezo a lanzar
      ``FrameworkUsageError`` ante cualquier tipo de objeto que no
      reconociera, y "ArenaZone" no estaba en esa lista blanca. El
      generador lo quito (``gen_level_residencias._objects_xml``) y esta
      prueba paso a candado ANTI-ArenaZone (``assert "ArenaZone_01" not in
      objs``) durante mas de un mes -- el rectangulo que documentaba
      se seguia verificando indirectamente via ``CameraLock_01``.
    - DROP #6 del motor (2026-08-25, AUD-605, commit ``6bf2914``) lo trajo
      de vuelta como tipo BUILTIN oficial: ``stage_objetos.py:131-133``
      despacha ``type=="ArenaZone"`` a ``_handle_zona_arena`` (484-501),
      que lee SOLO x/y/width/height del objeto (sin properties -- un rect
      degenerado se ignora) y lo agrega a ``stage_data.zonas_arena``;
      ``stage_scene.py`` le entrega al jefe la primera zona cuyo centro
      contiene, via ``set_arena_bounds`` (81-91, 483-496). Ya NO pasa por
      el camino de kwargs-al-constructor-de-entidad que rompio V2 (ese
      crash era especifico de objetos con clase de entidad registrada,
      p. ej. ``BossVenado`` -- ``ArenaZone`` no instancia nada).
    - READOPCION 2026-08-26 (hallazgo H-19, "Tarea de adopcion" abierta en
      FINDINGS.md tras el drop #6; decision del usuario de ejecutarla):
      se reintroduce el objeto en el TMX, ahora como fuente-en-Tiled de la
      arena, ADEMAS del override manual en codigo que
      ``boss_venado_scene.py`` sigue llamando -- doble candado deliberado,
      no retirado en esta tarea (H-19 sigue "vigente y necesaria": el
      ``on_enter()`` del motor entrega el rect ANTES que nuestro override
      explicito lo pise en el mismo fotograma, asi que si algun dia se
      retira el override, el TMX ya deja la arena correcta como fallback).
      El rectangulo declarado NO coincide con el de ``CameraLock_01`` (800
      de ancho, hasta el borde este del mapa en x=3280): ``ArenaZone_01``
      mide 784 de ancho, terminando exactamente en x=3264 -- el arranque
      de ``RightWall_Arena`` -- para que la arena de combate del jefe
      jamas incluya la columna de la pared. Ver
      ``test_arenazone_geometria_coincide_con_las_constantes_python`` para
      el candado de fuente unica de verdad contra ``ARENA_BOUNDS``/
      ``ARENA_RECT``.
    """
    r = _root()
    objs = {o.get("name"): o for og in r.findall("objectgroup") if og.get("name") == "Objects" for o in og}
    assert "PlayerSpawn_01" in objs and "BossVenado_01" in objs
    assert "ArenaZone_01" in objs
    az = objs["ArenaZone_01"]
    assert az.get("type") == "ArenaZone"
    assert (az.get("x"), az.get("y"), az.get("width"), az.get("height")) == ("2480", "0", "784", "608")
    assert "CameraLock_01" in objs
    assert not any(n.startswith("NextTrigger") for n in objs)
    cl = objs["CameraLock_01"]
    assert (cl.get("x"), cl.get("y"), cl.get("width"), cl.get("height")) == ("2480", "0", "800", "608")
    # las propiedades interruptor de CameraLock son booleanos tipados puestos en true
    cl_props = {p.get("name"): p for p in cl.find("properties")}
    for key in ("lock_x", "lock_y"):
        assert cl_props[key].get("type") == "bool"
        assert cl_props[key].get("value") == "true"
    # PlayerSpawn en el inicio de la pradera (pies en el plano del suelo)
    ps = objs["PlayerSpawn_01"]
    assert (ps.get("x"), ps.get("y")) == ("48", "560")
    # El spawn del boss se desplazo con la arena a x=2880/y=240 (r11), luego se
    # movio al extremo derecho de la arena (x=3168/y=240, r12 -- feedback del
    # usuario "pon el boss al final del mapa": pasando el gazebo, cerca de
    # RightWall_Arena), aun SIN propiedades custom: el BossVenado.__init__(spawn_position)
    # original del profesor no acepta kwargs y StageLoader pasa cada propiedad
    # de objeto TMX como kwarg, asi que cualquier propiedad aqui haria crashear
    # el juego real (ver test_entities_instantiate_from_tmx).
    bv = objs["BossVenado_01"]
    assert (bv.get("x"), bv.get("y")) == ("3168", "240")
    bv_props_el = bv.find("properties")
    assert bv_props_el is None or len(bv_props_el) == 0


def test_arenazone_geometria_coincide_con_las_constantes_python() -> None:
    """H-19 (drop #6, AUD-605), candado de fuente unica de verdad: el
    rectangulo que ``ArenaZone_01`` declara en el TMX no puede desviarse en
    silencio de ``ARENA_RECT``/``ARENA_BOUNDS`` en codigo -- las tres
    representaciones del mismo rectangulo (Tiled, ``boss_venado.py``,
    ``boss_venado_scene.py``) tienen que coincidir byte por byte, o esto se
    pone rojo AQUI, en vez de manifestarse como un jefe que se comporta
    raro cerca del borde de su arena, descubierto jugando.

    Autocontenido y portable con cwd=game (sin tocar ``playtest``): importa
    directamente los modulos del boss, igual que hace
    ``test_entities_instantiate_from_tmx`` mas abajo.
    """
    from src.stages.boss_venado.boss_venado import ARENA_RECT
    from src.stages.boss_venado.boss_venado_scene import ARENA_BOUNDS

    r = _root()
    objs = [o for og in r.findall("objectgroup") if og.get("name") == "Objects" for o in og]
    zonas = [o for o in objs if o.get("type") == "ArenaZone"]
    assert len(zonas) == 1, f"se esperaba exactamente un objeto ArenaZone, se encontraron {len(zonas)}"
    zona = zonas[0]
    rect_tmx = (int(zona.get("x")), int(zona.get("y")), int(zona.get("width")), int(zona.get("height")))
    assert rect_tmx == (2480, 0, 784, 608)
    assert rect_tmx == (ARENA_BOUNDS.x, ARENA_BOUNDS.y, ARENA_BOUNDS.width, ARENA_BOUNDS.height)
    assert rect_tmx == (ARENA_RECT.x, ARENA_RECT.y, ARENA_RECT.width, ARENA_RECT.height)


def test_collision_floor_and_walls() -> None:
    r = _root()
    col = {o.get("name"): o for og in r.findall("objectgroup") if og.get("name") == "Collision" for o in og}
    assert col["Floor"].get("y") == "560" and col["Floor"].get("width") == "3280"   # r11: ancho completo
    assert "LeftWall_World" in col and "RightWall_Arena" in col
    assert col["RightWall_Arena"].get("x") == "3264"                                 # (W-1)*16, ancho del mapa menos 1 columna


def test_gids_reference_tileset() -> None:
    """TAREA 13 adapto esta prueba: desde que BG_Far usa un SEGUNDO tileset
    (el de profundidad de campo, ver test_bg_far_referencia_el_tileset_de_bruma
    mas abajo -- solo-blur hasta 2026-08-24, blur+contraste "bruma" desde
    2026-08-27), sus GIDs caen fuera del rango [firstgid, firstgid+TILECOUNT)
    del tileset principal POR DISENO -- ya no es un candado valido para esa
    capa. Las otras 5 capas de tiles siguen sin tocar y se verifican igual
    que antes."""
    from src.stages.boss_venado.tools.gen_level_residencias import TILECOUNT
    r = _root()
    tilesets = r.findall("tileset")
    ts = tilesets[0]
    assert ts.get("tilecount") == str(TILECOUNT)      # fuente unica de verdad conectada
    firstgid = int(ts.get("firstgid"))
    maxgid = firstgid + TILECOUNT
    ts_bruma = tilesets[1]
    firstgid_bruma = int(ts_bruma.get("firstgid"))
    maxgid_bruma = firstgid_bruma + int(ts_bruma.get("tilecount"))
    for layer in r.findall("layer"):
        data = layer.find("data").text
        gids = [int(g) for g in data.replace("\n", "").split(",")]
        assert min(gids) >= 0
        if layer.get("name") == "BG_Far":
            assert max(gids) < maxgid_bruma
            assert max(gids) >= firstgid_bruma   # BG_Far no debe quedar vacio
        else:
            assert max(gids) < maxgid


def test_bg_far_referencia_el_tileset_de_bruma() -> None:
    """Historia del segundo tileset de BG_Far (profundidad de campo):

    - TAREA 13 (Unidad VII (b), 2026-08-24, campana "La Peregrinacion al
      Venado") lo creo como un atlas SOLO-blur: gaussian_blur aplicado a
      cada tile de compose_sky() (ver
      gen_tileset_bgfar_blur.generar_tileset_borroso). Este test se llamaba
      "test_bg_far_referencia_el_tileset_borroso" y candado el nombre
      "tileset_residencias_crepusculo_bgfar_blur".
    - TAREA (2026-08-27, decision del usuario, diseno aprobado con dictamen
      doc-guardian AMARILLO): el atlas que BG_Far referencia pasa a ser
      blur + REDUCCION DE CONTRASTE (FilterTools.adjust_contrast,
      CONTRASTE_BRUMA < 1.0) -- "bruma", perspectiva atmosferica real: los
      planos lejanos, ademas de desenfocarse, pierden contraste local. El
      PNG solo-blur NUNCA se sobrescribe (zona de creacion permitida,
      CLAUDE.md "ZONAS EDITABLES" punto 3) -- queda huerfano en disco, sin
      referencia alguna en el TMX; el archivo nuevo
      (``generar_tileset_bruma``, ``gen_tileset_bgfar_blur.py``) es el que
      BG_Far referencia ahora. Este test se renombro para reflejar eso: el
      nombre viejo ("...borroso") ya no describe lo que el tileset
      declarado en el TMX realmente contiene."""
    r = _root()
    tilesets = r.findall("tileset")
    assert len(tilesets) == 2
    nombres = {t.get("name") for t in tilesets}
    assert "tileset_residencias_crepusculo_bgfar_bruma" in nombres
    assert "tileset_residencias_crepusculo_bgfar_blur" not in nombres   # atlas solo-blur: huerfano, fuera del TMX
    firstgid_bruma = max(int(t.get("firstgid")) for t in tilesets)
    bg_far = next(layer for layer in r.findall("layer") if layer.get("name") == "BG_Far")
    csv = bg_far.find("data").text
    gids = [int(v) for row in csv.strip().split(",\n") for v in row.split(",") if v != "0"]
    assert gids, "BG_Far no debe quedar vacio"
    assert min(gids) >= firstgid_bruma   # TODOS los gids no-vacios de BG_Far vienen del tileset bruma


def test_layer_grid_integrity() -> None:
    r = _root()
    layers = r.findall("layer")
    assert len(layers) == 6                            # las seis capas de tiles
    for layer in layers:
        cells = layer.find("data").text.replace("\n", "").split(",")
        assert len(cells) == 205 * 38                  # exactamente un gid por celda del mapa (r11)


def test_tileset_image_has_colorkey() -> None:
    r = _root()
    img = r.find("tileset").find("image")
    assert img.get("trans") == "000000"                # negro -> transparente (overlays/telescopio)


def test_tileset_image_size_matches_atlas_png() -> None:
    """Anti-regresion de la RONDA-11 para el bug de la ronda 10: el ancho/alto
    de <image> que el TMX DECLARA debe ser igual al tamaño REAL del PNG del
    atlas. pytmx recorta el tileset por la altura declarada, asi que si el
    atlas crece (mas tiles -> mas filas) pero la altura declarada se queda
    atras, cada tile de las filas extra se DESCARTA silenciosamente al
    renderizar (que es exactamente lo que dejo el renderizado base del
    gazebo como un vacio de cielo en la ronda 10). Barato de proteger, lo
    atrapa para siempre.

    Deliberadamente lee el PNG del atlas DESPLEGADO directamente del arbol
    del juego (solo lectura, nunca regenerado aqui): el invariante bajo
    prueba es que el artefacto realmente entregado en disco -- el mismo que
    pytmx carga en tiempo de ejecucion -- sigue coincidiendo con lo que el
    TMX declara. Regenerar una copia de descarte en su lugar volveria esta
    proteccion inutil (siempre pasaria aunque nadie hubiera vuelto a correr
    ``python -m tools.gen_tileset_residencias`` tras hacer crecer el atlas).
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
    assert g.build_tmx() == g.build_tmx()              # composicion pura, sin estado oculto
    g.main()
    with open(TMX, "rb") as f:
        first = f.read()
    g.main()
    with open(TMX, "rb") as f:
        second = f.read()
    assert first == second                             # los bytes escritos son estables


def test_loads_in_engine_headless() -> None:
    from src.framework.stage.stage_loader import StageLoader
    stage = StageLoader.load(TMX)
    assert stage is not None


def test_tmx_declares_lighting_properties() -> None:
    """Feature B, recalibrada dos veces.

    Ronda 2 de critica visual (decision del usuario): se retiraron
    ``start_hour``/``season`` porque dejarlas puestas hacia que el motor
    recortara el ambiente compuesto al piso rechazado ``MIN_AMBIENTE=0.45``.

    Adopcion V3 / H-18: ``start_hour`` VUELVE (el doc 86, normativo y
    posterior, exige que los jefes de Zona 1 declaren la noche), y para que el
    ambiente COMPUESTO no se mueva del 0.594 aprobado, el ``ambient_light``
    crudo sube de 0.55 a 1.0 y el ``bloom`` crudo baja de 0.22 a 0.08 -- ver el
    comentario de ``gen_level_residencias.build_tmx`` para los multiplicadores
    medidos. Los valores crudos y los compuestos siguen sin ser el mismo
    numero: los compuestos se fijan aparte, en
    test_effective_ambient_stays_above_playable_floor.
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
    assert float(props["ambient_light"]) == 1.0
    assert float(props["bloom"]) == 0.08
    assert props["ambient_fx"] == "leaves"


def test_tmx_omits_climate_and_season() -> None:
    """No-adopcion deliberada, reducida a dos por la adopcion V3:

    - ``climate="storm"`` implica VFX de clima jamas vistos/aprobados en las
      12 rondas de critica del mapa (spec sec. 2.1) -- sin cambios.
    - ``season`` sigue omitida por la decision de la ronda 2: la paleta del
      tileset ya esta pintada para el crepusculo, y declarar otono ademas
      encendia lluvia en silencio (via ``estacion.clima``) que la critica
      aprobada nunca pidio.

    ``start_hour`` y ``day_length`` YA NO se omiten: el doc 86
    (``86_ESPECIFICACION_DE_NIVELES_Y_JEFES`` sec. 3.2, normativo y posterior a
    esa ronda) exige que los jefes de Zona 1 declaren ``start_hour=22`` (aqui
    en su forma nombrada, ``night``) y ``day_length=0``. Su prueba propia es
    test_tmx_declares_night_frozen_clock, en test_adopcion_v3.py.
    """
    r = _root()
    prop_names = {p.get("name") for p in r.find("properties")}
    assert "climate" not in prop_names
    assert "season" not in prop_names


def test_effective_ambient_stays_above_playable_floor() -> None:
    """Candado de regresion para la recalibracion de la ronda 2: lo que
    importa no es la propiedad cruda ``ambient_light`` sino el ambiente que
    el MOTOR realmente aplica en tiempo de ejecucion, compuesto con exactamente
    la misma formula/constantes que ``StageScene._aplicar_hora``
    (stage_scene.py:518-526) -- llamada aqui solo lectura, no re-derivada a
    mano, para que esto no pueda desviarse silenciosamente de la logica real
    del motor. El usuario rechazo explicitamente caer en el piso estructural
    ("el look nocturno 0.45 queda descartado"), asi que esto verifica que el
    valor compuesto lo supere con margen real, no solo tecnicamente por encima.
    """
    from src.framework.scenes.stage_scene import StageScene
    from src.framework.stage.day_night import RelojDeMundo
    from src.framework.stage.seasons import estacion
    from src.framework.stage.stage_loader import StageLoader

    _root()
    stage = StageLoader.load(TMX)
    # Adopcion V3: ``start_hour`` ya se declara (noche = 22.0) y ``season``
    # sigue omitida. Esto fija el fallback exacto que el motor toma para cada
    # una, del cual depende la matematica de la re-calibracion.
    assert stage.start_hour == 22.0
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
    # Candado exacto de la re-calibracion: el ambiente compuesto debe ser
    # BYTE POR BYTE el mismo 0.594 que el usuario aprobo jugando antes de que
    # el mapa declarara la noche. Si alguien toca ``ambient_light`` o
    # ``start_hour`` por separado, esto se pone rojo aqui y no en el playtest.
    assert abs(composed - 0.594) <= 1e-6, (
        f"composed ambient {composed:.6f} se movio del 0.594 aprobado"
    )


def test_tmx_has_twelve_light_objects() -> None:
    """Eran 5 (feature B, adopcion V2); la Tarea 3 del plan
    "La Peregrinacion al Venado" (2026-08-24) suma 7 luces atmosfericas
    nuevas de build-up narrativo -- ver ``_LIGHTS`` en
    ``gen_level_residencias.py``."""
    r = _root()
    objs = [o for og in r.findall("objectgroup") if og.get("name") == "Objects" for o in og]
    lights = [o for o in objs if o.get("type") == "Light"]
    assert len(lights) == 12


def test_light_positions_match_lamp_props() -> None:
    """El rectangulo declarado de cada luz 'lamp', centrado de la misma forma
    en que ``StageLoader._handle_light`` lo centra, debe caer exactamente
    sobre el tile que el compositor ya estampo con ``lamp_top`` -- para que
    un futuro desplazamiento de zona (las columnas son constantes, p. ej.
    ``CARPORT.start + 3``) no pueda desprender silenciosamente una luz de su
    prop de lampara. El acento frio del oculo no tiene una prop de lampara a
    la cual anclarse (spec sec. 2.1) asi que solo se verifica contra su
    propio tile declarado.
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
    """Prueba de humo: ``Light`` sigue siendo un tipo de objeto builtin
    reconocido y ninguna de las nuevas propiedades float/string/bool hace
    tropezar ``_safe_float``/``_safe_int`` tras las adiciones de este feature.
    """
    from src.framework.stage.stage_loader import StageLoader

    _root()
    stage = StageLoader.load(TMX)
    assert stage is not None
    assert len(stage.lights) == 12    # Tarea 3 (2026-08-24): 5 -> 12 luces
    assert stage.ambient_light is not None
    assert stage.ambient_light == 1.0     # re-calibrado por la adopcion V3 (era 0.55)


def test_entities_instantiate_from_tmx() -> None:
    """Reproduce la ruta REAL del juego (App.__init__ -> ensure_registered()).

    ``test_loads_in_engine_headless`` de arriba carga el TMX con un registro
    de entidades VACIO (este proceso pytest nunca arranca App), asi que
    StageLoader OMITE silenciosamente el objeto ``BossVenado`` por su
    fallthrough if/elif sin ``else`` -- nunca llega a instanciar el boss, que
    es exactamente por que el desajuste constructor/propiedad-TMX
    (arena_origin_x/y) se le escapo al CI y solo exploto cuando
    ``capture_map.py`` arranco una App real.

    Aqui registramos las clases de entidad de la misma forma que lo hace
    ``App.__init__`` (``entity_factory.ensure_registered()`` ->
    ``StageLoader.register_entity``), y luego cargamos el TMX. Ahora el
    loader toma la rama ``obj_type in _entity_registry`` y ejecuta
    ``BossVenado(Vector2(2000, 240), **props)``: una propiedad TMX suelta
    lanzaria ``TypeError`` y abortaria toda la carga del stage (== el crash
    real de ``python main.py --boss boss_venado``). Que pase == el objeto
    boss se instancia y aterriza en ``entity_list``.
    """
    from src.framework.entities.boss_base import BossBase
    from src.framework.entities.entity_factory import ensure_registered
    from src.framework.stage.stage_loader import StageLoader

    _root()  # (re)genera el TMX actual en disco
    ensure_registered()  # idempotente; registra "BossVenado" -> clase BossVenado
    assert "BossVenado" in StageLoader._entity_registry

    stage = StageLoader.load(TMX)  # NO debe lanzar TypeError en BossVenado_01
    bosses = [e for e in stage.entity_list if isinstance(e, BossBase)]
    assert len(bosses) == 1, f"expected exactly one boss entity, got {len(bosses)}"


# ===========================================================================
# TAREA 3 (plan "La Peregrinacion al Venado"): propiedades bpm/compas +
# 7 luces nuevas con familias de color y densidad decreciente hacia el Acto 3.
# ===========================================================================
def test_bpm_y_compas_declarados() -> None:
    r = _root()
    props = {p.get("name"): p.get("value") for p in r.find("properties")}
    # Revision del coordinador: la pista real (``bgm_zone1_boss``) se compuso
    # a 100 BPM (``legacyofInfest/tools/generate_all_assets.py:2315``), y
    # ``RelojMusical`` deriva el pulso UNICAMENTE de este valor declarado --
    # no escucha la pista -- asi que tiene que coincidir con el tempo real o
    # el pulso visual queda a destiempo del tambor.
    assert props["bpm"] == "100"
    assert props["compas"] == "4"


def test_siete_luces_nuevas_con_familias_de_color() -> None:
    r = _root()
    objs = {o.get("name"): o for og in r.findall("objectgroup") if og.get("name") == "Objects" for o in og}
    nuevas = ("Light_HogarLampA_01", "Light_HogarLampB_01", "Light_HogarLampC_01",
              "Light_AbandonoLamp_01", "Light_UmbralFrio_01",
              "Light_UmbralSangre_01", "Light_UmbralSangre_02")
    for nombre in nuevas:
        assert nombre in objs, f"falta {nombre}"
        assert objs[nombre].get("type") == "Light"
    colores = {n: {p.get("name"): p.get("value") for p in objs[n].find("properties")}["color"]
               for n in nuevas}
    assert colores["Light_HogarLampA_01"] == "warm"
    assert colores["Light_HogarLampB_01"] == "warm"
    assert colores["Light_HogarLampC_01"] == "warm"
    assert colores["Light_AbandonoLamp_01"] == "warm"
    assert colores["Light_UmbralFrio_01"] == "cold"
    assert colores["Light_UmbralSangre_01"] == "blood"
    assert colores["Light_UmbralSangre_02"] == "blood"
    # densidad/temperatura DECRECIENTE por zona narrativa (limites en pixeles
    # de la tabla del plan: PRADERA [0,1040) Acto 1 "el hogar", CARPORT
    # [1040,1520) Acto 2 "el abandono", ARCOS [1520,2480) Acto 3 "el umbral").
    # Rangos deliberadamente amplios (por zona, no por columna exacta) para
    # que futuros ajustes visuales puedan mover col/row +/- sin romper esto.
    x_hogar_a = int(objs["Light_HogarLampA_01"].get("x"))
    x_hogar_b = int(objs["Light_HogarLampB_01"].get("x"))
    x_hogar_c = int(objs["Light_HogarLampC_01"].get("x"))
    for nombre, x in (("Light_HogarLampA_01", x_hogar_a),
                       ("Light_HogarLampB_01", x_hogar_b),
                       ("Light_HogarLampC_01", x_hogar_c)):
        assert 0 <= x < 1040, f"{nombre} fuera de PRADERA: x={x}"
    x_abandono = int(objs["Light_AbandonoLamp_01"].get("x"))
    assert 1040 <= x_abandono < 1520, f"Light_AbandonoLamp_01 fuera de CARPORT: x={x_abandono}"
    # UmbralFrio: dentro de ARCOS pero ANTES del tramo de sangre (que empieza
    # en 2200) -- el frio precede a la sangre segun la narrativa decreciente.
    x_umbral_frio = int(objs["Light_UmbralFrio_01"].get("x"))
    assert 1520 <= x_umbral_frio < 2200, f"Light_UmbralFrio_01 fuera de su tramo de ARCOS: x={x_umbral_frio}"
    # densidad: las luces de sangre solo aparecen en el tramo final del Acto 3
    # (x entre 2200 y 2480, antes de la arena)
    x_sangre_1 = int(objs["Light_UmbralSangre_01"].get("x"))
    x_sangre_2 = int(objs["Light_UmbralSangre_02"].get("x"))
    assert 2200 <= x_sangre_1 < 2480
    assert 2200 <= x_sangre_2 < 2480


def test_bpm_y_compas_expuestos_por_stage_loader() -> None:
    """Round-trip del TMX -> ``StageData``: ``StageLoader._build_stage_data``
    (stage_loader.py:441-442) parsea ``bpm``/``compas`` con
    ``_safe_float``/``_safe_int`` y los pasa directo al constructor de
    ``StageData`` (stage_loader.py:534-535), que los expone como atributos
    ``float``/``int`` (stage_data.py:398-404) -- el mismo objeto que
    ``StageScene._montar_reloj_musical`` lee para alimentar ``RelojMusical``
    (stage_scene.py:1225-1231). Verificado por lectura del mecanismo real,
    no asumido.
    """
    from src.framework.stage.stage_loader import StageLoader

    _root()
    stage = StageLoader.load(TMX)
    assert stage.bpm == 100.0
    assert stage.compas == 4


def test_cutscene_de_presentacion_no_bloqueante_y_saltable() -> None:
    """Tarea 9 (plan 2026-08-24 "La Peregrinacion al Venado"): un objeto
    ``Cutscene`` de presentacion, NO bloqueante (``bloquea=false``) y
    saltable, con guion de espera + temblor.

    Sin orden ``camara`` desde la correccion del 2026-08-25 (verificacion
    visual del coordinador contra la sonda
    ``reports\\mcp_filmstrip\\20260825_052131_sonda_t9_cutscene_apertura``):
    el paneo era imperceptible porque ``_update_camera_map(dt)``
    (stage_scene.py:775-779) corre el MISMO fotograma y sobreescribe
    ``camera.offset`` justo despues de que ``CameraMoveAction`` lo
    escribiera (``bloquea=false`` -> la camara de seguimiento nunca cede
    el paso). El "panel" que parecia chrome de la cutscene tampoco lo era:
    para este guion, ``CutsceneScript.draw()`` no dibuja nada (ver el
    comentario de ``_cutscene_object_xml()`` en el generador para la
    evidencia completa) -- lo que se veia era ``ScreenBanner`` +
    ``TutorialOverlay``, chrome incondicional de CUALQUIER escenario,
    ajeno a este objeto ``Cutscene``.

    Nota de implementacion -- desviacion deliberada del snippet del plan,
    verificada contra el parser real y no asumida: la propiedad ``guion``
    es MULTILINEA (varias ordenes, una por linea) y por eso NO puede viajar
    en el atributo ``value`` de ``<property>``. XML normaliza cualquier
    salto de linea LITERAL dentro de un valor de atributo a un espacio
    (confirmado empiricamente con ``xml.etree.ElementTree.fromstring`` --
    el mismo parser que usa pytmx por debajo, ver ``pytmx/pytmx.py:34``):
    un guion escrito como ``value="camara ...\\nesperar ..."`` llegaria al
    analizador (``cutscene_guion.analizar_guion``, que separa por
    ``splitlines()``) como una unica linea con las ordenes pegadas por
    espacios, y la segunda orden nunca se ejecutaria. La propiedad viaja
    en cambio como TEXTO del elemento (``<property name="guion">...
    texto...</property>``, sin atributo ``value`` y sin ``type``), que SI
    atraviesa el parser intacto -- por eso aqui se lee con
    ``p.get("value") or p.text``, la misma precedencia exacta que usa
    ``pytmx.pytmx.parse_properties`` (pytmx.py:363).
    """
    r = _root()
    objs_by_tag = [o for og in r.findall("objectgroup") if og.get("name") == "Objects" for o in og]
    cutscenes = [o for o in objs_by_tag if o.get("type") == "Cutscene"]
    assert len(cutscenes) == 1
    cs = cutscenes[0]
    props_els = {p.get("name"): p for p in cs.find("properties")}
    props = {nombre: (p.get("value") or p.text) for nombre, p in props_els.items()}
    assert props["bloquea"] == "false"
    assert props["saltable"] == "true"
    assert "guion" in props and props["guion"].strip() != ""
    assert "camara" not in props["guion"]   # retirado 2026-08-25: paneo futil contra la camara de seguimiento
    assert "temblor" in props["guion"]
    # Candado de regresion: el guion tiene que seguir viajando como texto
    # del elemento, nunca como atributo ``value`` (ver docstring de arriba)
    # -- y sin ``type``: con ``type="string"`` y sin ``value``, pytmx
    # reescribe el resultado con la cadena literal "None"
    # (pytmx.py:364-365, ``cls(subnode.get("value"))`` con
    # ``subnode.get("value")`` ausente). Si alguien "simplifica" esto de
    # vuelta a ``_prop()`` con el atributo ``value``, este candado revienta
    # antes que el guion se rompa en silencio en producción.
    guion_el = props_els["guion"]
    assert guion_el.get("value") is None
    assert guion_el.get("type") is None
    # Umbral >= 3 (revisión de calidad 2026-08-25, verificado coherente con
    # el guion vigente): tras retirar la orden `camara` (2026-08-25,
    # paneo fútil -- ver el comentario de `_cutscene_object_xml()` en el
    # generador), `_GUION_PRESENTACION` quedó en EXACTAMENTE 3 líneas no
    # vacías (`esperar 0.6` / `temblor 0.18 3.0` / `esperar 1.0`), así que
    # este candado sigue siendo ajustado y no un margen falso: falla si
    # alguien colapsa el guion multilínea de vuelta a una sola línea (el
    # bug real de XML que este archivo entero existe para prevenir, ver
    # docstring de la función) y no falla si una futura orden legítima
    # AÑADE una línea más. `>=` en vez de `==`: el candado es sobre "sigue
    # siendo multilínea", no sobre el conteo exacto de órdenes narrativas,
    # que es asunto del diseño del guion, no de la serialización XML.
    lineas_no_vacias = [linea for linea in props["guion"].splitlines() if linea.strip()]
    assert len(lineas_no_vacias) >= 3


def test_prop_guion_escapa_caracteres_especiales_xml() -> None:
    """Revisión de calidad de la Tarea 9 (2026-08-25): ``_prop_guion()``
    tiene que escapar ``&``, ``<`` y ``>`` con
    ``xml.sax.saxutils.escape()`` ANTES de interpolar el texto en el XML.

    ``_GUION_PRESENTACION`` (el único guion real hoy) no usa ninguno de
    esos caracteres, así que esta prueba no depende de él -- es una prueba
    PURA y directa del helper, con un texto que sí los usa (algo tan
    plausible en un guion futuro como ``"HP < 6 & jefe vivo"``). Sin el
    escape, ``_prop_guion()`` seguiría devolviendo una cadena de Python sin
    quejarse (es una f-string, no un serializador XML), y el fragmento
    resultante rompería la carga del `.tmx` entero recién en tiempo de
    ejecución -- un ``xml.etree.ElementTree.ParseError`` al primer
    ``pytmx.load_pygame()``, no un error en el propio generador.
    """
    from src.stages.boss_venado.tools.gen_level_residencias import _prop_guion

    crudo = "HP < 6 & jefe vivo > 0\nsiguiente orden\n"
    fragmento = _prop_guion("guion", crudo, "    ")

    # candado directo: los caracteres especiales viajan como entidades en el
    # texto CRUDO del fragmento, nunca literales
    assert "&lt;" in fragmento
    assert "&amp;" in fragmento
    assert "&gt;" in fragmento
    assert "HP < 6 & jefe vivo > 0" not in fragmento

    # candado de fondo: el fragmento, insertado en un documento minimo, es
    # XML bien formado y hace round-trip exacto al texto original -- la
    # prueba real de que el escape (y no otra cosa) es lo que arregla esto
    root = ET.fromstring(f"<raiz>{fragmento}</raiz>")
    prop = root.find("property")
    assert prop.get("name") == "guion"
    assert prop.get("value") is None   # sigue viajando como texto del elemento, no como atributo
    assert prop.text == crudo


# ══════════════════════════════════════════════════════════════════════════
# Tarea 10 — Checkpoints (vía el generador)
# ══════════════════════════════════════════════════════════════════════════

def test_tres_checkpoints_en_los_umbrales_narrativos():
    r = _root()
    objs = {o.get("name"): o for og in r.findall("objectgroup") if og.get("name") == "Objects" for o in og}
    checkpoints = {n: o for n, o in objs.items() if o.get("type") == "Checkpoint"}
    assert len(checkpoints) == 3
    ids = sorted(int({p.get("name"): p for p in o.find("properties")}["checkpoint_id"].get("value"))
                 for o in checkpoints.values())
    assert ids == [1, 2, 3]
    xs = sorted(int(o.get("x")) for o in checkpoints.values())
    assert xs == [1040, 1740, 2440]   # frontera real CARPORT + dentro de "El umbral" + aproximación final


# ══════════════════════════════════════════════════════════════════════════
# Tarea 11 — Pickups/Chest + decoración narrativa muda (vía el generador)
# ══════════════════════════════════════════════════════════════════════════

def test_pickups_y_chest_ofrecen_dos_rutas():
    r = _root()
    objs = [o for og in r.findall("objectgroup") if og.get("name") == "Objects" for o in og]
    pickups = [o for o in objs if o.get("type") == "Pickup"]
    chests = [o for o in objs if o.get("type") == "Chest"]
    assert len(pickups) == 3
    assert len(chests) == 1
    # ruta baja (nivel del suelo, sin salto) vs ruta alta (sobre una plataforma).
    # El eje Y de Tiled crece hacia ABAJO: el pickup a nivel de suelo tiene el
    # y MAYOR (mas abajo en pantalla) y los de plataforma el y MENOR (mas
    # arriba) -- por eso el candado real es sobre ys[-1]/ys[0], no al reves
    # (el texto original del plan tenia los indices intercambiados).
    ys = sorted(int(o.get("y")) for o in pickups)
    assert ys[-1] >= 500         # el mas bajo en pantalla, a nivel de suelo
    assert ys[0] <= 470          # el mas alto en pantalla, requiere saltar a una plataforma
    # ninguno cae fuera del corredor pre-arena
    for o in pickups + chests:
        assert int(o.get("x")) < 2480


def test_banco_roto_nuevo_en_el_carport():
    """place_bench() ya se usa en PRADERA/ARCOS/ARENA (ver el modulo) -- esta
    prueba fija que Tarea 11 añade la llamada que faltaba en CARPORT,
    reforzando el motivo "algo se perdio" del Acto 2."""
    r = _root()
    detail = next(layer for layer in r.findall("layer") if layer.get("name") == "Terrain_Detail")
    csv = detail.find("data").text
    filas = [row.split(",") for row in csv.strip().split(",\n")]
    # col86, BASE_ROW(34) y col87, BASE_ROW -- bench_broken_l/r (ver place_bench).
    # NO col85/86 como decia el plan literal: col85 es la esquina del bloque
    # del tractor (compose_carport, place_block col0=_CARPORT_C1+3, ancho 3
    # -> cols 83-85) y el banco lo pisaria; se desplazo una columna al este,
    # a _CARPORT_C1 + 6 (ver el comentario junto a la llamada real).
    from src.stages.boss_venado.tools.gen_tileset_residencias import NAME_TO_INDEX
    gid_l = NAME_TO_INDEX["bench_broken_l"] + 1   # FIRSTGID=1
    gid_r = NAME_TO_INDEX["bench_broken_r"] + 1
    assert int(filas[34][86]) == gid_l
    assert int(filas[34][87]) == gid_r
