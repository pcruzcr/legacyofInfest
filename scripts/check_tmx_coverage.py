"""
check_tmx_coverage.py — ¿usa el escenario de referencia todo lo que el motor ofrece?

Por qué existe
--------------
Una característica que el motor lee del TMX pero que **ningún mapa del juego
declara** es, en la práctica, una característica que no existe: el estudiante
no la ve al jugar, no la encuentra abriendo `stage0.tmx` en Tiled, y sólo puede
enterarse leyendo la documentación —que es justo lo que no se hace—.

Este guion cruza tres cosas:

  1. Las propiedades de mapa que `StageLoader` lee de verdad.
  2. Los tipos de objeto que reconoce.
  3. Lo que los mapas del juego declaran realmente.

Y dice qué queda sin demostrar. Es la versión automática de la pregunta
«¿está todo implementado y usado en stage0?».

Uso:
    python scripts/check_tmx_coverage.py
    python scripts/check_tmx_coverage.py --ci    # falla si baja la cobertura
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

#: Propiedades de mapa que el motor lee. Se declaran a mano y hay una prueba
#: que las contrasta con `stage_loader.py`: extraerlas con expresiones
#: regulares mezclaba las de mapa con las de objeto —`radius`, `color`,
#: `damage`— y daba un recuento sin sentido.
PROPIEDADES_MAPA: tuple[str, ...] = (
    "stage_id", "stage_name", "time_limit", "bgm_track", "background_zone",
    "gravity_multiplier", "zone", "climate",
    "ambient_light", "bloom", "vignette",
    "ambient_fx", "ambient_fx_rate",
    "start_hour", "day_length", "season",
    "profundidad_curva", "orden_por_y",
)

#: Las que un mapa **debe** tener para cargar.
OBLIGATORIAS: frozenset[str] = frozenset({"stage_id", "stage_name"})

#: Propiedades del objeto `Light`.
PROPIEDADES_LUZ: tuple[str, ...] = (
    "radius", "color", "intensity", "flicker", "flicker_speed", "flicker_amount",
)

#: El mapa que hace de ejemplo para los estudiantes.
MAPA_REFERENCIA = "assets/maps/stage0/stage0.tmx"


def _props_de_mapa(raiz: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "")
            for p in raiz.findall("./properties/property")}


def _tipos_de_objeto(raiz: ET.Element) -> set[str]:
    return {(o.get("type") or o.get("class") or "")
            for o in raiz.iter("object")} - {""}


def _props_de_luces(raiz: ET.Element) -> set[str]:
    usadas: set[str] = set()
    for o in raiz.iter("object"):
        if (o.get("type") or o.get("class")) != "Light":
            continue
        usadas |= {p.get("name", "")
                   for p in o.findall("./properties/property")}
    return usadas - {""}


def tipos_del_motor() -> set[str]:
    """Todos los tipos de objeto que el cargador reconoce."""
    from src.framework.entities import entity_factory
    from src.framework.stage.stage_loader import StageLoader
    from src.framework.stage.tmx_diagnostics import (
        COLLISION_OBJECT_TYPES,
        known_object_types,
    )

    entity_factory.ensure_registered()
    return (set(known_object_types(list(StageLoader._entity_registry)))
            | set(COLLISION_OBJECT_TYPES))


def analizar(ruta: Path) -> dict:
    raiz = ET.parse(ruta).getroot()
    props = _props_de_mapa(raiz)
    tipos = _tipos_de_objeto(raiz)
    return {
        "props_usadas": {p for p in PROPIEDADES_MAPA if p in props},
        "props_sin_usar": {p for p in PROPIEDADES_MAPA if p not in props},
        "tipos_usados": tipos,
        "props_luz_usadas": _props_de_luces(raiz),
        "valores": props,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cobertura de las características TMX en los mapas del juego")
    parser.add_argument("--ci", action="store_true",
                        help="falla si el mapa de referencia no cubre el mínimo")
    parser.add_argument("--minimo", type=float, default=0.85,
                        help="fracción mínima de propiedades cubiertas (0-1)")
    args = parser.parse_args()

    del_motor = tipos_del_motor()
    mapas = sorted((_RAIZ / "assets" / "maps").rglob("*.tmx"))
    if not mapas:
        print("No se encontró ningún mapa.")
        return 1

    print(f"El motor reconoce {len(PROPIEDADES_MAPA)} propiedades de mapa y "
          f"{len(del_motor)} tipos de objeto.\n")

    problemas = 0
    cubiertos_por_algun_mapa: set[str] = set()
    tipos_en_algun_mapa: set[str] = set()

    for mapa in mapas:
        rel = mapa.relative_to(_RAIZ)
        r = analizar(mapa)
        cubiertos_por_algun_mapa |= r["props_usadas"]
        tipos_en_algun_mapa |= r["tipos_usados"]

        cobertura = len(r["props_usadas"]) / len(PROPIEDADES_MAPA)
        print(f"  {rel}")
        print(f"    propiedades declaradas : {len(r['props_usadas'])}/"
              f"{len(PROPIEDADES_MAPA)}  ({cobertura:.0%})")
        print(f"    tipos de objeto usados : {len(r['tipos_usados'])}")
        if r["props_luz_usadas"]:
            print(f"    propiedades de Light   : "
                  f"{len(r['props_luz_usadas'])}/{len(PROPIEDADES_LUZ)}")
        faltan_obligatorias = OBLIGATORIAS - r["props_usadas"]
        if faltan_obligatorias:
            print(f"    [ERROR] faltan obligatorias: {sorted(faltan_obligatorias)}")
            problemas += 1
        if r["props_sin_usar"]:
            print(f"    sin declarar           : "
                  f"{', '.join(sorted(r['props_sin_usar']))}")
        print()

    # El mapa de referencia es el que los estudiantes abren para copiar.
    referencia = _RAIZ / MAPA_REFERENCIA
    if referencia.exists():
        r = analizar(referencia)
        cobertura = len(r["props_usadas"]) / len(PROPIEDADES_MAPA)
        luz = len(r["props_luz_usadas"]) / len(PROPIEDADES_LUZ)
        print(f"Mapa de referencia ({MAPA_REFERENCIA}):")
        print(f"  cobertura de propiedades : {cobertura:.0%}")
        print(f"  cobertura de Light       : {luz:.0%}")
        if cobertura < args.minimo:
            print(f"  [AVISO] por debajo del mínimo pedido ({args.minimo:.0%}). "
                  "Una característica que el mapa de ejemplo no usa es una que "
                  "el estudiante no descubre.")
            if args.ci:
                problemas += 1

    sin_demostrar = set(PROPIEDADES_MAPA) - cubiertos_por_algun_mapa
    tipos_sin_usar = del_motor - tipos_en_algun_mapa
    print()
    if sin_demostrar:
        print(f"Propiedades que NINGÚN mapa usa ({len(sin_demostrar)}):")
        print("  " + ", ".join(sorted(sin_demostrar)))
    else:
        print("Todas las propiedades de mapa están demostradas en algún mapa.")
    if tipos_sin_usar:
        print(f"\nTipos de objeto que ningún mapa usa ({len(tipos_sin_usar)} de "
              f"{len(del_motor)}):")
        print("  " + ", ".join(sorted(tipos_sin_usar)))

    print()
    if problemas:
        print(f"{problemas} problema(s).")
        return 1
    print("Cobertura correcta.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
