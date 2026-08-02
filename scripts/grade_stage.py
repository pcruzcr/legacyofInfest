"""
grade_stage.py — Auto-grade student stage TMX files.

Evaluates:
  - TMX file loads without errors
  - Required layers exist (Terrain, Collision)
  - Player spawn point exists
  - Checkpoints exist (at least 1 per zone section)
  - Enemies placed correctly (valid types, not overlapping)
  - Collectibles exist (at least 3)
  - Map metadata present (author, stage_id, stage_name)
  - Tileset references valid
  - Climate property valid
  - Time limit (if set) is reasonable

Usage:
    python scripts/grade_stage.py path/to/student/stage.tmx
    python scripts/grade_stage.py --dir submissions/stage1/
    python scripts/grade_stage.py --json path/to/stage.tmx   # JSON output
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts._cli_paths import display_path  # noqa: E402  (tras ajustar sys.path)

#: Copia de emergencia de los tipos de enemigo. **No es la fuente de verdad**:
#: sólo se usa si no se puede importar el motor (faltan dependencias, se
#: califica desde una máquina sin instalar). La lista real la da
#: `_tipos_de_enemigo()`, que lee el registro de entidades.
_ENEMIGOS_DE_RESPALDO: frozenset[str] = frozenset({
    "Walker", "Flying", "Shooter", "Charger", "Archer",
    "Brute", "Caster", "Assassin",
})
MAX_TMX_WIDTH = 400
MAX_TMX_HEIGHT = 50
MAX_TIME_LIMIT = 999
REQUIRED_GRADE_PROPS = ["author", "stage_id", "stage_name"]

RUBRIC = {
    "file_parses": 5,
    "required_layers": 10,
    "player_spawn": 10,
    "checkpoints": 15,
    "enemies_valid_types": 10,
    "enemies_placed": 10,
    "collectibles": 10,
    "metadata": 10,
    "tileset_valid": 5,
    "climate_valid": 5,
    "map_bounds_reasonable": 5,
    "time_limit_reasonable": 5,
    # F2.4 — diseño, no estructura. Todo lo de arriba se puede satisfacer
    # colocando objetos en un rectángulo vacío; esto pregunta si el nivel se
    # puede jugar. Pesa 30 de 130, un 23 % de la nota.
    "design_completable": 12,
    "design_geometry": 10,
    "design_pacing": 8,
}


def _tipos_de_enemigo(escenario: Path | None = None) -> set[str]:
    """Los tipos que el motor sabe convertir en enemigo.

    AUD-107 — por qué dejó de ser una lista escrita a mano
    ------------------------------------------------------
    Lo era, y decía esto::

        {"MushMom", "Bat", "Skitter", "Mantis", "Flying", "Shooter",
         "Charger", "Archer", "Brute", "Caster", "Assassin", "Walker"}

    De esos doce nombres, **cuatro no existen** en el motor —`MushMom`, `Bat`,
    `Skitter` y `Mantis` son de un bestiario anterior— y **faltaban veintidós**
    de los treinta que el registro tiene hoy. El efecto se vio calificando la
    entrega de stage2_2: el mapa coloca siete enemigos y el informe decía
    «2 enemy(ies) placed», porque `WalkerGuardia`, `FlyingBoa`,
    `ShooterSerpienteArbol` y `WalkerSerpientePequena` —las cuatro del
    bestiario oficial de la Zona 2— no estaban en la lista.

    No le costó puntos a nadie, porque las dos categorías puntúan por
    presencia y no por cantidad. Costó algo peor: el informe que el estudiante
    lee le decía que cinco de sus enemigos no contaban.

    Es el tercer caso esta semana de una herramienta del profesor con su propia
    copia desfasada de lo que el motor sabe (AUD-104 en el calificador de
    jefes, AUD-106 en el validador de TMX). La cura es la misma: preguntarle al
    registro en vez de recordar.

    `escenario` permite además contar los enemigos que el propio estudiante
    registró con `register_entity`, igual que hace el validador.
    """
    try:
        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader
        entity_factory.ensure_registered()
        tipos = set(StageLoader._entity_registry)
    except Exception:
        return set(_ENEMIGOS_DE_RESPALDO)

    if escenario is not None:
        tipos |= _tipos_registrados_por_el_estudiante(escenario)
    return tipos


def _tipos_registrados_por_el_estudiante(escenario: Path) -> set[str]:
    """Nombres pasados a `register_entity(...)` dentro del paquete del escenario.

    Se lee por AST y no importando: calificar el trabajo de otro no debería
    ejecutar su código. Misma técnica que `validate_tmx.py` (AUD-106).
    """
    import ast

    encontrados: set[str] = set()
    if not escenario.is_dir():
        return encontrados
    for fichero in escenario.rglob("*.py"):
        try:
            arbol = ast.parse(fichero.read_text(encoding="utf-8-sig", errors="replace"))
        except (OSError, SyntaxError):
            continue
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call) or not nodo.args:
                continue
            nombre = nodo.func.attr if isinstance(nodo.func, ast.Attribute) else (
                nodo.func.id if isinstance(nodo.func, ast.Name) else ""
            )
            if nombre == "register_entity" and isinstance(nodo.args[0], ast.Constant):
                valor = nodo.args[0].value
                if isinstance(valor, str):
                    encontrados.add(valor)
    return encontrados


def _paquete_del_escenario(tmx: Path) -> Path | None:
    """El directorio `src/stages/<x>/` que corresponde a este mapa.

    No se puede deducir del nombre: los estudiantes bautizan la carpeta por el
    sitio —`la_soda`, `las_aulas`, `oficinas`— y el mapa por la ranura. Se
    busca el paquete que nombre el fichero, que es la única relación real.
    """
    stages = _PROJECT_ROOT / "src" / "stages"
    if not stages.is_dir():
        return None
    directo = stages / tmx.parent.name
    if directo.is_dir():
        return directo
    for paquete in sorted(p for p in stages.iterdir() if p.is_dir()):
        for fichero in paquete.rglob("*.py"):
            try:
                if tmx.name in fichero.read_text(encoding="utf-8-sig", errors="replace"):
                    return paquete
            except OSError:
                continue
    return None


def _tipos_no_enemigos() -> set[str]:
    """Tipos de objeto que existen y no son enemigos.

    F2.4 — antes esto era una lista escrita a mano en este archivo, y llevaba
    desfasada desde que se añadieron tipos nuevos: calificar stage0 avisaba de
    "Unknown enemy types: {MessageTrigger_Once, Light}" sobre objetos
    perfectamente válidos. Un calificador que marca como error lo que el motor
    acepta enseña a desconfiar de él.

    Ahora la lista sale del registro real. Si falla la importación —porque
    falten dependencias— se cae a la copia antigua en vez de reventar: la
    parte estructural de la rúbrica no necesita el motor.
    """
    try:
        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader
        from src.framework.stage.tmx_diagnostics import (
            COLLISION_OBJECT_TYPES,
            known_object_types,
        )
        entity_factory.ensure_registered()
        todos = set(known_object_types(list(StageLoader._entity_registry)))
        return (todos | set(COLLISION_OBJECT_TYPES)) - _tipos_de_enemigo()
    except Exception:
        return {
            "PlayerSpawn", "Checkpoint", "MessageTrigger", "MessageTrigger_Once",
            "Waypoint", "Solid", "Platform", "HazardZone", "DeathPit",
            "NextTrigger", "ZoneTrigger", "CameraLock", "Light",
        }


def _parse_tmx(path: Path) -> ET.Element | None:
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def _get_props(root: ET.Element) -> dict[str, str]:
    props: dict[str, str] = {}
    p_elem = root.find("properties")
    if p_elem is not None:
        for p in p_elem.findall("property"):
            props[p.get("name", "")] = p.get("value", "")
    return props


def grade_stage(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "file": str(path),
        "score": 0,
        "max_score": sum(RUBRIC.values()),
        "categories": {},
        "errors": [],
        "warnings": [],
    }

    if not path.exists():
        result["errors"].append("File not found")
        result["percentage"] = 0.0
        return result
    if path.suffix != ".tmx":
        result["errors"].append(f"Not a .tmx file (got {path.suffix})")

    root = _parse_tmx(path)
    if root is None:
        result["categories"]["file_parses"] = {"score": 0, "max": RUBRIC["file_parses"], "msg": "XML parse failed"}
        result["percentage"] = 0.0
        return result
    result["categories"]["file_parses"] = {"score": RUBRIC["file_parses"], "max": RUBRIC["file_parses"], "msg": "Valid TMX"}

    w = int(root.get("width", 0))
    h = int(root.get("height", 0))
    props = _get_props(root)

    # Layer checks
    #
    # AUD-110 — la colisión de este motor es un `<objectgroup>`, no un `<layer>`.
    #
    # Esto miraba sólo `root.findall("layer")`, que en Tiled son las capas de
    # baldosas. La capa `Collision` del motor es un grupo de objetos —así la
    # produce `generate_stage0_tmx.py`, así la documenta `06_TMX_SPEC.md` y así
    # la leen `StageLoader` y el validador—. Resultado: **los quince mapas del
    # proyecto recibían el aviso «No 'Collision' layer found (add one for solid
    # walls/floors)», y los quince la tienen.**
    #
    # Es el cuarto caso este mes de una herramienta del profesor que corrige lo
    # que está bien (AUD-104, AUD-106, AUD-107). Un aviso que sale siempre deja
    # de leerse, y con él dejan de leerse los que sí importan.
    layers = root.findall("layer")
    grupos = root.findall("objectgroup")
    layer_names = [line.get("name", "") for line in layers]
    nombres_de_grupo = [g.get("name", "") for g in grupos]
    has_terrain = "Terrain" in layer_names
    has_collision = "Collision" in layer_names or "Collision" in nombres_de_grupo
    if has_terrain:
        result["categories"]["required_layers"] = {"score": RUBRIC["required_layers"], "max": RUBRIC["required_layers"], "msg": "Has Terrain layer"}
    else:
        result["categories"]["required_layers"] = {"score": 0, "max": RUBRIC["required_layers"], "msg": "Missing Terrain layer"}
        result["errors"].append("Missing required 'Terrain' layer")
    if not has_collision:
        result["warnings"].append("No 'Collision' layer found (add one for solid walls/floors)")

    # Player spawn
    player_spawned = False
    for og in root.findall("objectgroup"):
        for obj in og.findall("object"):
            if obj.get("name") == "PlayerSpawn" or obj.get("type") == "PlayerSpawn":
                player_spawned = True
    if player_spawned:
        result["categories"]["player_spawn"] = {"score": RUBRIC["player_spawn"], "max": RUBRIC["player_spawn"], "msg": "PlayerSpawn found"}
    else:
        result["categories"]["player_spawn"] = {"score": 0, "max": RUBRIC["player_spawn"], "msg": "Missing PlayerSpawn"}

    # Checkpoints
    checkpoints = 0
    for og in root.findall("objectgroup"):
        for obj in og.findall("object"):
            if obj.get("name", "").startswith("Checkpoint") or obj.get("type") == "Checkpoint":
                checkpoints += 1
    if checkpoints >= 1:
        score = min(RUBRIC["checkpoints"], 5 * checkpoints)
        result["categories"]["checkpoints"] = {"score": score, "max": RUBRIC["checkpoints"], "msg": f"{checkpoints} checkpoint(s)"}
    else:
        result["categories"]["checkpoints"] = {"score": 0, "max": RUBRIC["checkpoints"], "msg": "No checkpoints"}
        result["warnings"].append("Add at least 1 checkpoint")

    # Enemigos. Los tipos válidos salen del registro del motor más los que el
    # estudiante haya registrado en su propio paquete (AUD-107).
    tipos_enemigo = _tipos_de_enemigo(_paquete_del_escenario(path))
    enemies: list[str] = []
    valid_types = 0
    invalid_enemy_types = []
    for og in root.findall("objectgroup"):
        for obj in og.findall("object"):
            obj_type = obj.get("type", "")
            obj_name = obj.get("name", "")
            if obj_type in tipos_enemigo:
                valid_types += 1
                enemies.append(obj_name or obj_type)
            elif obj_type and obj_type not in _tipos_no_enemigos():
                invalid_enemy_types.append(obj_type)
    if valid_types > 0:
        result["categories"]["enemies_valid_types"] = {"score": RUBRIC["enemies_valid_types"], "max": RUBRIC["enemies_valid_types"], "msg": f"{valid_types} valid enemy type(s)"}
    else:
        result["categories"]["enemies_valid_types"] = {"score": 0, "max": RUBRIC["enemies_valid_types"], "msg": "No valid enemy types"}
    if invalid_enemy_types:
        result["warnings"].append(f"Unknown enemy types: {set(invalid_enemy_types)}")
    if enemies:
        result["categories"]["enemies_placed"] = {"score": RUBRIC["enemies_placed"], "max": RUBRIC["enemies_placed"], "msg": f"{len(enemies)} enemy(ies) placed"}
    else:
        result["categories"]["enemies_placed"] = {"score": 0, "max": RUBRIC["enemies_placed"], "msg": "No enemies placed"}

    # Collectibles (check objects AND Collectibles tile layer)
    #
    # AUD-112 — esto no contaba los coleccionables del motor.
    #
    # Buscaba la cadena «collect» en el **nombre** del objeto, y dejaba
    # `obj.get("type", "")` en una línea suelta sin asignar a nada: la huella de
    # una edición a medias, alguien empezó a mirar el tipo y no terminó.
    #
    # El resultado es que `Pickup`, `Key` y `Chest` —los tipos que el motor
    # tiene para esto desde F4.1, los que están en la guía del estudiante y los
    # que el validador acepta— **no contaban como coleccionables**. Sólo contaba
    # quien bautizara su objeto «collectible_1» por casualidad.
    #
    # Sexta vez este mes que una herramienta del profesor ignora lo que el motor
    # sabe hacer. Se cuenta por tipo, y se deja la heurística del nombre para no
    # invalidar a quien ya la estuviera usando.
    TIPOS_COLECCIONABLES = {"Pickup", "Key", "Chest"}
    collectibles = 0
    for og in root.findall("objectgroup"):
        for obj in og.findall("object"):
            oname = obj.get("name", "")
            otype = obj.get("type", "")
            if otype in TIPOS_COLECCIONABLES or "collect" in oname.lower():
                collectibles += 1
    for layer in root.findall("layer"):
        lname = layer.get("name", "")
        if "collect" in lname.lower():
            data = layer.find("data")
            if data is not None:
                raw = (data.text or "").strip()
                tile_ids = [int(x) for x in raw.replace("\n", "").split(",") if x.strip()]
                non_zero = sum(1 for t in tile_ids if t > 0)
                collectibles += non_zero // 5  # count groups of 5 as one collectible
    if collectibles >= 3:
        result["categories"]["collectibles"] = {"score": RUBRIC["collectibles"], "max": RUBRIC["collectibles"], "msg": f"{collectibles} collectibles"}
    elif collectibles >= 1:
        result["categories"]["collectibles"] = {"score": 5, "max": RUBRIC["collectibles"], "msg": f"Only {collectibles} collectible(s) (need >=3 for full score)"}
    else:
        result["categories"]["collectibles"] = {"score": 5, "max": RUBRIC["collectibles"], "msg": "No collectibles found (OK for tutorial stages)"}

    # Metadata
    meta_score = 0
    for req_prop in REQUIRED_GRADE_PROPS:
        if req_prop in props:
            meta_score += 1
    # AUD-113 — `meta_score * 3` con tres propiedades daba 9 sobre 10: el 10/10
    # era **inalcanzable**, y la casilla salía en amarillo aunque el estudiante
    # hubiera puesto todo lo que se le pedía. Se reparte el peso completo entre
    # las propiedades que de verdad se exigen, sea cual sea su número.
    total_props = len(REQUIRED_GRADE_PROPS)
    puntos = round(RUBRIC["metadata"] * meta_score / total_props) if total_props else RUBRIC["metadata"]
    result["categories"]["metadata"] = {"score": puntos, "max": RUBRIC["metadata"], "msg": f"{meta_score}/{total_props} props found"}
    if meta_score < len(REQUIRED_GRADE_PROPS):
        missing = [p for p in REQUIRED_GRADE_PROPS if p not in props]
        result["warnings"].append(f"Missing metadata: {missing}")

    # Tileset
    #
    # AUD-107 — Tiled ofrece dos formas de declarar un tileset: incrustado en
    # el propio `.tmx` (`<tileset><image .../></tileset>`) o en un fichero
    # `.tsx` aparte al que el mapa apunta con `source=`. La segunda es la que
    # recomienda Tiled y la que permite compartir un tileset entre mapas, y es
    # la que usó la entrega del Lobby.
    #
    # Este bloque sólo miraba la primera: buscaba `<image>` como hijo directo
    # y, al no encontrarlo, daba «No valid tileset images» y restaba 5 puntos a
    # un mapa cuyo tileset estaba perfectamente en su sitio. Ahora se sigue el
    # `.tsx`, que es donde vive la imagen en ese caso.
    tilesets = root.findall("tileset")
    ts_valid = 0
    for ts in tilesets:
        img = ts.find("image")
        if img is not None:
            if (path.parent / img.get("source", "")).resolve().exists():
                ts_valid += 1
            continue
        externo = ts.get("source", "")
        if not externo:
            continue
        tsx = (path.parent / externo).resolve()
        if not tsx.exists():
            continue
        try:
            img_ext = ET.parse(tsx).getroot().find("image")
        except ET.ParseError:
            result["warnings"].append(f"El tileset externo {externo} no se puede leer")
            continue
        if img_ext is not None and (
            tsx.parent / img_ext.get("source", "")
        ).resolve().exists():
            ts_valid += 1
    if ts_valid > 0:
        result["categories"]["tileset_valid"] = {"score": RUBRIC["tileset_valid"], "max": RUBRIC["tileset_valid"], "msg": f"{ts_valid} tileset(s) valid"}
    else:
        result["categories"]["tileset_valid"] = {"score": 0, "max": RUBRIC["tileset_valid"], "msg": "No valid tileset images"}
        result["warnings"].append("Tileset image(s) not found — check path")

    # Climate
    climate = props.get("climate", "")
    known_climates = {"rain", "fog", "wind", "snow", "clear", "storm", "sandstorm"}
    if climate in known_climates:
        result["categories"]["climate_valid"] = {"score": RUBRIC["climate_valid"], "max": RUBRIC["climate_valid"], "msg": f"Climate: {climate}"}
    elif climate:
        result["categories"]["climate_valid"] = {"score": 2, "max": RUBRIC["climate_valid"], "msg": f"Unknown climate: {climate}"}
    else:
        result["categories"]["climate_valid"] = {"score": 0, "max": RUBRIC["climate_valid"], "msg": "No climate set"}

    # Map bounds
    if 0 < w <= MAX_TMX_WIDTH and 0 < h <= MAX_TMX_HEIGHT:
        result["categories"]["map_bounds_reasonable"] = {"score": RUBRIC["map_bounds_reasonable"], "max": RUBRIC["map_bounds_reasonable"], "msg": f"Size: {w}x{h}"}
    else:
        result["categories"]["map_bounds_reasonable"] = {"score": 0, "max": RUBRIC["map_bounds_reasonable"], "msg": f"Size {w}x{h} seems unreasonable"}

    # Time limit
    time_limit_str = props.get("time_limit", "0")
    time_limit = int(time_limit_str) if time_limit_str.isdigit() else 0
    if time_limit == 0:
        result["categories"]["time_limit_reasonable"] = {"score": RUBRIC["time_limit_reasonable"], "max": RUBRIC["time_limit_reasonable"], "msg": "No time limit"}
    elif 30 <= time_limit <= MAX_TIME_LIMIT:
        result["categories"]["time_limit_reasonable"] = {"score": RUBRIC["time_limit_reasonable"], "max": RUBRIC["time_limit_reasonable"], "msg": f"Time: {time_limit}s"}
    else:
        result["categories"]["time_limit_reasonable"] = {"score": 2, "max": RUBRIC["time_limit_reasonable"], "msg": f"Time {time_limit}s seems unreasonable"}

    _grade_design(path, result)

    total = sum(c["score"] for c in result["categories"].values())
    result["score"] = total
    result["max_score"] = sum(RUBRIC.values())
    result["percentage"] = round(total / result["max_score"] * 100, 1)

    return result


def _grade_design(path: Path, result: dict[str, Any]) -> None:
    """Puntúa el **diseño** del nivel, no sólo su estructura.

    F2.4 — el hueco que esto cierra
    -------------------------------
    Todo lo anterior de esta rúbrica se puede satisfacer sin diseñar nada: un
    estudiante que coloque las capas obligatorias, un spawn, cuatro checkpoints
    y algunos enemigos en un rectángulo vacío saca más del 90 %. La rúbrica
    medía que los objetos **estuvieran**, no que el nivel se pudiera jugar.

    `framework.stage.level_metrics` ya sabía responder a las preguntas que
    importan —¿se llega a la salida?, ¿hay saltos imposibles?, ¿hay plataformas
    huérfanas?, ¿está el recorrido cubierto por checkpoints?— y llevaba desde
    su creación sin conectarse a nada que calificara.

    Se puntúa aparte y de forma tolerante a fallos: si el nivel no se puede
    cargar —falta una capa, un tileset roto— el resto de la nota sigue siendo
    válida y aquí se explica por qué no se pudo analizar. Un calificador que se
    cae con una entrega mala es un calificador inútil justo cuando más falta
    hace.
    """
    from src.framework.stage.level_metrics import analyse_stage

    def poner(cat: str, score: int, msg: str) -> None:
        result["categories"][cat] = {"score": score, "max": RUBRIC[cat], "msg": msg}

    try:
        # `StageLoader` construye un renderizador de pyscroll, que necesita un
        # modo de vídeo activo. Se pide el controlador ficticio para poder
        # calificar sin pantalla —en un servidor de integración continua o por
        # SSH— y se hace aquí y no al importar para no exigirlo a quien sólo
        # quiere la parte estructural de la rúbrica.
        import os
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        import pygame
        if not pygame.display.get_init():
            pygame.display.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))

        from src.framework.stage.stage_loader import StageLoader
        stage_data = StageLoader.load(path)
        informe = analyse_stage(stage_data)
    except Exception as e:
        for cat in ("design_completable", "design_geometry", "design_pacing"):
            poner(cat, 0, f"no se pudo analizar el diseño: {type(e).__name__}")
        result["warnings"].append(
            "el nivel no se pudo cargar para analizar su diseño; corrige "
            "primero los errores de estructura"
        )
        return

    result["design"] = {
        "exit_reachable": informe.exit_reachable,
        "orphan_platforms": informe.orphan_platforms,
        "impossible_ledges": len(informe.impossible_ledges),
        "impossible_gaps": len(informe.impossible_gaps),
        "demanding_gaps": len(informe.demanding_gaps),
        "worst_checkpoint_gap": max(informe.checkpoint_gaps, default=0.0),
    }

    # 1. ¿Se puede terminar? Es binario y es lo único de la rúbrica que puede
    #    hacer que un nivel valga cero por diseño.
    if informe.exit_reachable:
        poner("design_completable", RUBRIC["design_completable"],
              "la salida es alcanzable andando desde el spawn")
    elif _tiene_movilidad(stage_data):
        # AUD-192 — no penalizar a quien use las mecánicas del motor.
        #
        # `exit_is_reachable` construye un grafo de saltos, y su propio
        # docstring reconoce el límite: «no modela dash, salto de pared ni
        # plataformas móviles». Tampoco resortes, lianas ni tirolesas. Un nivel
        # cuyo camino pasa por un `Spring` sale marcado como incompletable.
        #
        # Medido: `stage_mecanicas.tmx` —el escenario que el propio motor usa
        # para enseñar las once mecánicas, con 11 objetos de movilidad— perdía
        # 12 de 130 puntos por usarlas. Con él, cualquier alumno que resolviera
        # un tramo con un resorte en vez de con un salto.
        #
        # No se afirma que el nivel sea completable: se dice que esta métrica
        # no puede juzgarlo y no se cobra por ello. Es la misma decisión que ya
        # se tomó con las arenas de jefe, y por la misma razón: aplicar la
        # rúbrica equivocada y suspender por ella es peor que no medir.
        poner("design_completable", RUBRIC["design_completable"],
              "hay mecánicas de movilidad: la ruta no se juzga sólo por saltos")
        result["warnings"].append(
            "el nivel usa resortes, tirolesas, lianas o plataformas móviles, "
            "que el analizador de rutas no modela. No se penaliza la ruta, "
            "pero **compruébala jugando**: aquí ninguna herramienta puede "
            "garantizar que se llegue a la salida"
        )
    else:
        poner("design_completable", 0, "NO se llega a la salida andando")
        result["errors"].append(
            "no hay ruta de plataformas desde el spawn hasta el NextTrigger: "
            "el nivel no se puede completar saltando"
        )
        # Aviso honesto sobre lo que esta métrica NO sabe.
        #
        # `exit_is_reachable` recorre plataformas. En una arena de jefe la
        # salida se abre al derrotarlo, no al llegar andando, así que la arena
        # de referencia del propio juego puntúa 0 aquí. No es un fallo de la
        # arena: es que se le está aplicando la rúbrica equivocada. Decirlo en
        # el informe evita que un profesor suspenda una entrega correcta.
        result["warnings"].append(
            "si el escenario es una arena donde la salida se abre al derrotar "
            "a un jefe, esta métrica no aplica: califícalo con "
            "scripts/grade_boss.py"
        )

    # 2. Geometría: saltos imposibles y plataformas a las que no se llega.
    #    Se descuenta por cada uno en vez de suspender de golpe, porque un
    #    repecho imposible en un nivel de treinta plataformas es un error
    #    puntual y no un diseño equivocado.
    fallos = len(informe.impossible_ledges) + informe.orphan_platforms
    puntos = max(0, RUBRIC["design_geometry"] - fallos * 3)
    if fallos == 0:
        poner("design_geometry", puntos, "sin saltos imposibles ni zonas aisladas")
    else:
        poner("design_geometry", puntos,
              f"{len(informe.impossible_ledges)} repecho(s) imposible(s), "
              f"{informe.orphan_platforms} plataforma(s) aislada(s)")
        for y, x, alto in informe.impossible_ledges[:3]:
            result["warnings"].append(
                f"repecho de {alto:.0f} px en ({x:.0f}, {y:.0f}): el jugador no "
                "salta tan alto"
            )
        if informe.orphan_platforms:
            result["warnings"].append(
                f"{informe.orphan_platforms} plataforma(s) sin ruta desde el "
                "spawn: o sobran, o falta un camino"
            )

    # 3. Ritmo: cuánto se anda entre puntos de control, y si hay saltos
    #    exigentes que den variedad. Un nivel sin ningún salto difícil es
    #    correcto y aburrido; uno con un tramo larguísimo sin checkpoint
    #    castiga al jugador por un error.
    peor = max(informe.checkpoint_gaps, default=0.0)
    exigentes = len(informe.demanding_gaps)
    if peor > MAX_CHECKPOINT_GAP:
        poner("design_pacing", 2,
              f"{peor:.0f} px sin checkpoint (máximo recomendado "
              f"{MAX_CHECKPOINT_GAP})")
        result["warnings"].append(
            f"hay {peor:.0f} px entre checkpoints: morir ahí cuesta demasiado "
            "camino rehecho"
        )
    elif exigentes == 0:
        poner("design_pacing", RUBRIC["design_pacing"] - 3,
              "el recorrido no tiene ningún salto exigente")
        result["warnings"].append(
            "ningún salto pone a prueba al jugador: el nivel se recorre solo"
        )
    else:
        poner("design_pacing", RUBRIC["design_pacing"],
              f"checkpoints bien repartidos, {exigentes} salto(s) exigente(s)")


#: Distancia máxima recomendada entre puntos de control, en píxeles.
#: Stage 0 mide 1600 px y coloca cuatro, así que ~350 px es lo que el
#: escenario de referencia considera aceptable.
MAX_CHECKPOINT_GAP = 500.0

#: Componentes que mueven al jugador por sitios a los que no llegaría saltando.
#:
#: AUD-192. Se nombran por su clase de componente y no por el tipo del TMX
#: porque es lo que sobrevive a la carga: `Conveyor` y `FrictionZone` son el
#: mismo `ZonaDeFriccion`, y `LaserZone` y `ShockwaveZone` la misma zona letal.
#: `ZonaDeAgua` entra porque nadar es otra forma de recorrer el mapa que el
#: grafo de saltos tampoco modela.
COMPONENTES_DE_MOVILIDAD: frozenset[str] = frozenset({
    "Resorte",            # Spring
    "Tirolesa",           # Zipline
    "Liana",              # Vine
    "PlataformaMovil",    # MovingPlatform
    "PlataformaHundible", # SinkingPlatform
    "BloqueRitmico",      # RhythmBlock
    "ZonaDeViento",       # WindZone
    "ZonaDeFriccion",     # Conveyor / FrictionZone
    "ZonaDeAgua",         # WaterZone
})


def _tiene_movilidad(stage_data: object) -> bool:
    """¿El nivel se recorre con algo más que saltos?

    Se mira el resultado de la carga y no el XML: así vale igual para un mapa
    escrito a mano en Tiled que para uno generado, y no hay que mantener una
    lista de nombres de tipo en dos sitios.
    """
    for grupo in getattr(stage_data, "componentes", []) or []:
        for componente in grupo:
            if type(componente).__name__ in COMPONENTES_DE_MOVILIDAD:
                return True
    return False


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Grade student stage TMX files")
    parser.add_argument("paths", nargs="+", help="TMX files or directories")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--dir", help="Scan directory for TMX files")
    args = parser.parse_args()

    tmx_files: list[Path] = []
    if args.dir:
        d = Path(args.dir)
        if d.exists():
            tmx_files.extend(d.rglob("*.tmx"))
    for p_str in args.paths:
        p = Path(p_str)
        if p.is_dir():
            tmx_files.extend(p.rglob("*.tmx"))
        elif p.exists():
            tmx_files.append(p)

    if not tmx_files:
        print("No TMX files found.")
        return 1

    tmx_files = list(set(tmx_files))

    all_results: list[dict[str, Any]] = []
    for tmx in sorted(tmx_files):
        r = grade_stage(tmx)
        all_results.append(r)
        if not args.json:
            rel = display_path(tmx, _PROJECT_ROOT)
            print(f"\n{'='*50}")
            print(f"  {rel}")
            print(f"{'='*50}")
            for cat, data in sorted(r["categories"].items()):
                status = "[PASS]" if data["score"] >= data["max"] else "[WARN]" if data["score"] > 0 else "[FAIL]"
                print(f"  {status} {cat}: {data['score']}/{data['max']} — {data['msg']}")
            for err in r["errors"]:
                print(f"  [FAIL] ERROR: {err}")
            for w in r["warnings"]:
                print(f"  [WARN]  WARN: {w}")
            print(f"\n  GRADE: {r['score']}/{r['max_score']} ({r['percentage']}%)")

    if args.json:
        print(json.dumps(all_results, indent=2))

    avg = sum(r["percentage"] for r in all_results) / len(all_results) if all_results else 0
    print(f"\n{'='*50}")
    print(f"  Total graded: {len(all_results)}")
    print(f"  Average grade: {avg:.1f}%")
    print(f"{'='*50}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
