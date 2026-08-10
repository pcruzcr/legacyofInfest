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

#: **Todas** las propiedades de mapa que el motor lee — AUD-378.
#:
#: `PROPIEDADES_MAPA` de arriba mide otra cosa y por eso no vale para esto: es
#: la lista **de enseñanza**, la que se le pide al mapa de referencia porque un
#: estudiante la descubre abriéndolo en Tiled. Confundir las dos era el punto
#: ciego: el guion vigilaba 18 propiedades mientras el cargador leía 35, y el
#: informe cerraba con «todas demostradas» sin haber mirado diecisiete —entre
#: ellas `sombras_proyectadas`, que **ningún mapa enciende** desde AUD-278—.
#:
#: Son dos preguntas distintas y ahora se responden por separado:
#:
#:   * ¿lo **enseña** el mapa de referencia?  → `PROPIEDADES_MAPA`, con su 85%
#:   * ¿lo ejercita **algún** mapa?           → esta lista
#:
#: Se declara a mano por el mismo motivo que la otra —extraerla con regex
#: mezclaba propiedades de mapa con las de objeto— y la mantiene honesta
#: `test_el_guardian_de_tmx_lo_mira_todo.py`, que compara **en los dos
#: sentidos** contra el AST de `stage_loader.py`. La comprobación de un solo
#: sentido es lo que dejó crecer el punto ciego durante meses.
PROPIEDADES_DEL_MOTOR: tuple[str, ...] = tuple(sorted({
    *PROPIEDADES_MAPA,
    "bpm", "compas", "desfase_audio",
    "camara", "vista",
    "estamina", "habilidades_libres", "tiempo_bala",
    "fog_of_war", "god_rays",
    # Las cinco del agua. Las cuatro últimas no aparecían en un barrido por
    # `props.get`: se leen con `_parse_unit_prop`, que es justo el motivo de
    # que este contraste vaya por AST y no por texto — la primera versión de
    # esta lista se dejó cuatro fuera y la prueba las cazó.
    "water_effect", "water_tint",
    "water_alpha", "water_amplitude", "water_frequency", "water_speed",
    "sombras_proyectadas",
    "profundidad_min", "profundidad_max",
}))

#: Propiedades **de objeto** que se leen dentro de `stage_loader.py`, y que por
#: eso aparecen en un barrido del fichero sin ser de mapa.
#:
#: AUD-350 se llevó los 19 manejadores `_handle_*` a `stage_objetos.py`, lo que
#: hacía razonable suponer que lo que queda es nivel de mapa. No del todo:
#: `_build_waypoints` recorre los objetos `Waypoint` y lee su `owner_id` con la
#: misma forma `props.get(...)`. El primer barrido lo contó como propiedad de
#: mapa y el informe lo dio por «no demostrado» mientras cinco mapas lo
#: declaran —en objetos—. Se excluye con su motivo escrito en vez de afinar el
#: AST: distinguir el ámbito exigiría resolver de dónde viene cada `props`, que
#: es el mismo problema que ya hizo descartar las expresiones regulares.
PROPIEDADES_DE_OBJETO: dict[str, str] = {
    "owner_id": (
        "propiedad del objeto `Waypoint`, no del mapa: la lee "
        "`StageLoader._build_waypoints` recorriendo la capa `Objects`"
    ),
}

#: Grafías alternativas de la misma propiedad. Mismo caso que `ALTERNATIVAS`
#: con los tipos de objeto (AUD-366): contarlas por separado da una cobertura
#: peor de lo que es y manda a alguien a perseguir un hueco inexistente.
#: `stage_loader.py` las lee con un `or` —la castellana primero—, así que
#: declarar cualquiera de las dos enciende la característica.
ALIAS_DE_PROPIEDAD: dict[str, str] = {
    "camera": "camara",
    "view": "vista",
}

#: Las que un mapa **debe** tener para cargar.
OBLIGATORIAS: frozenset[str] = frozenset({"stage_id", "stage_name"})

#: Propiedades del objeto `Light`.
PROPIEDADES_LUZ: tuple[str, ...] = (
    "radius", "color", "intensity", "flicker", "flicker_speed", "flicker_amount",
)

#: El mapa que hace de ejemplo para los estudiantes.
MAPA_REFERENCIA = "assets/maps/stage0/stage0.tmx"


#: Tipos que son **grafía alternativa** de otro, no características aparte.
#: AUD-366 — medido: cambiar la arena del venado de `BossVenado` a `BossSpawn`
#: deja `BossVenado` sin usar. El conteo no mejora porque no hay nada que
#: mejorar: los dos producen la misma entidad (`stage_objetos.py:222` lo dice
#: literalmente), así que cubrir uno descubre el otro. Es un límite de la
#: métrica, no un hueco del contenido, y el informe lo dice en vez de dejar
#: que alguien lo persiga cada seis meses.
ALTERNATIVAS: dict[str, str] = {
    "BossSpawn": (
        "grafía indirecta de los tipos de jefe: `BossSpawn` con `boss=\"X\"` "
        "construye exactamente lo mismo que el tipo `X`. Las cuatro arenas usan "
        "el tipo directo; cubrir éste descubriría aquéllos"
    ),
}


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
    # AUD-378 — el mapa puede declarar la grafía inglesa; cuenta igual, porque
    # `stage_loader` las lee con un `or` y encienden la misma característica.
    declaradas = {ALIAS_DE_PROPIEDAD.get(p, p) for p in props}
    return {
        "props_usadas": {p for p in PROPIEDADES_MAPA if p in props},
        "props_sin_usar": {p for p in PROPIEDADES_MAPA if p not in props},
        #: Sobre todo lo que el motor lee, para la detección de características
        #: que ningún mapa ejercita. Es otra pregunta que la cobertura del mapa
        #: de referencia, y por eso va en otra clave.
        "del_motor_usadas": {p for p in PROPIEDADES_DEL_MOTOR
                             if p in declaradas},
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
        # AUD-378 — se acumula sobre **todo** lo que el motor lee, no sobre la
        # lista de enseñanza. Acumular la pedagógica y restarla de la completa
        # daba un informe que llamaba «no usada» a cualquier propiedad fuera de
        # las 18, incluidas las que sí declara un mapa: `bpm` sale en
        # `stage4_1.tmx:20` y aparecía como sin demostrar.
        cubiertos_por_algun_mapa |= r["del_motor_usadas"]
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

    # AUD-378 — sobre **todo** lo que el motor lee, no sobre la lista de
    # enseñanza. Ésta es la pregunta que el guion decía responder y llevaba sin
    # responder: mirando sólo las 18 pedagógicas, el informe cerraba con «todas
    # demostradas» mientras veintiuna características quedaban sin que ningún
    # mapa las ejercitara y nadie podía enterarse.
    sin_demostrar = set(PROPIEDADES_DEL_MOTOR) - cubiertos_por_algun_mapa
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
        for tipo in sorted(tipos_sin_usar):
            if tipo in ALTERNATIVAS:
                print(f"    ({tipo}: {ALTERNATIVAS[tipo]})")

    print()
    if problemas:
        print(f"{problemas} problema(s).")
        return 1
    print("Cobertura correcta.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
