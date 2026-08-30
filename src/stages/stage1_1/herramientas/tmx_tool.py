"""Operaciones semanticas sobre un .tmx, sin regenerarlo.

POR QUE EXISTE
--------------
El mapa se construia con `generate_stage1_1_tmx.py`, que reescribe el fichero
entero desde cero. Con eso, cualquier retoque hecho en Tiled se perdia en la
siguiente ejecucion, asi que Tiled no se podia usar. Esta herramienta hace lo
contrario: **edita el .tmx que ya existe**, tocando solo lo que se le pide.

El .tmx pasa a ser la fuente de verdad. Tiled y esta herramienta escriben sobre
el mismo fichero sin pisarse.

No duplica al validador ni al calificador del profesor: `medir` los ejecuta.

Uso:
    python tmx_tool.py <tmx> capas
    python tmx_tool.py <tmx> tilesets
    python tmx_tool.py <tmx> listar [--tipo Checkpoint]
    python tmx_tool.py <tmx> plataforma --col 120 --fila 28 --ancho 4 --gid 3
    python tmx_tool.py <tmx> mover --id 1042 --x 1920 --y 448
    python tmx_tool.py <tmx> borrar --id 1042
    python tmx_tool.py <tmx> medir --repo <ruta_repo>
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ── Lectura ──────────────────────────────────────────────────────────
def _abrir(ruta: Path) -> tuple[ET.ElementTree, ET.Element]:
    arbol = ET.parse(ruta)
    return arbol, arbol.getroot()


def _rejilla(capa: ET.Element, ancho: int) -> list[list[int]]:
    """CSV de la capa -> matriz de enteros."""
    crudo = capa.find("data").text or ""
    plana = [int(v) for v in crudo.replace("\n", "").split(",") if v.strip()]
    return [plana[i:i + ancho] for i in range(0, len(plana), ancho)]


def _guardar_rejilla(capa: ET.Element, rejilla: list[list[int]]) -> None:
    filas = [",".join(str(v) for v in fila) for fila in rejilla]
    capa.find("data").text = "\n" + ",\n".join(filas) + "\n"


def _escribir(arbol: ET.ElementTree, ruta: Path) -> None:
    arbol.write(ruta, encoding="UTF-8", xml_declaration=True)


# ── Comandos ─────────────────────────────────────────────────────────
def cmd_capas(raiz: ET.Element, _a) -> int:
    print(f"mapa {raiz.get('width')}x{raiz.get('height')} tiles "
          f"de {raiz.get('tilewidth')}x{raiz.get('tileheight')}px")
    for capa in raiz.findall("layer"):
        rej = _rejilla(capa, int(capa.get("width")))
        usados = sum(1 for f in rej for v in f if v)
        print(f"  [tiles ] {capa.get('name'):<16} {usados:>6} tiles pintados")
    for grupo in raiz.findall("objectgroup"):
        print(f"  [objetos] {grupo.get('name'):<15} {len(grupo.findall('object')):>6} objetos")
    return 0


def cmd_tilesets(raiz: ET.Element, _a) -> int:
    for ts in raiz.findall("tileset"):
        img = ts.find("image")
        primero = int(ts.get("firstgid"))
        cuenta = int(ts.get("tilecount"))
        print(f"  gid {primero:>4}..{primero + cuenta - 1:<4} {ts.get('name'):<22} "
              f"{img.get('source') if img is not None else '?'}")
    return 0


def cmd_listar(raiz: ET.Element, a) -> int:
    for grupo in raiz.findall("objectgroup"):
        for obj in grupo.findall("object"):
            tipo = obj.get("type") or obj.get("class") or ""
            if a.tipo and tipo != a.tipo:
                continue
            print(f"  id={obj.get('id'):<6} {tipo:<18} {obj.get('name') or '':<20} "
                  f"x={float(obj.get('x', 0)):>7.0f} y={float(obj.get('y', 0)):>6.0f} "
                  f"[{grupo.get('name')}]")
    return 0


def _siguiente_id(raiz: ET.Element) -> int:
    """Un id libre. Respeta `nextobjectid`, que es lo que Tiled mira al abrir."""
    usados = [int(o.get("id", 0)) for o in raiz.iter("object")]
    siguiente = max(usados + [0]) + 1
    declarado = int(raiz.get("nextobjectid", 0))
    return max(siguiente, declarado)


def cmd_plataforma(raiz: ET.Element, a) -> int:
    """Anade una plataforma: tiles en Terrain + rectangulo solido en Collision.

    Las dos cosas hacen falta. `Terrain` es lo que se VE; el grupo de objetos
    `Collision` es lo que el motor usa para chocar (rectangulos type="Solid",
    no tiles). Pintar solo una de las dos da una plataforma fantasma —visible
    y atravesable— o invisible y solida.

    `--inset` mete la colision N pixeles por lado respecto de los tiles. En una
    roca de borde redondeado eso es lo fisicamente correcto —los pixeles de la
    esquina no son suelo— y ademas es la unica forma de ajustar un hueco con
    precision: los tiles son de 16 px, asi que sin inset un hueco solo puede
    medir 16, 32 o 48, y el umbral de «exigente» del calificador cae en 34,2.
    """
    tile = int(raiz.get("tilewidth"))
    ancho_mapa = int(raiz.get("width"))
    if a.col < 0 or a.col + a.ancho > ancho_mapa:
        print(f"columnas {a.col}..{a.col + a.ancho - 1} fuera del mapa (0..{ancho_mapa - 1})",
              file=sys.stderr)
        return 1

    capa = next((c for c in raiz.findall("layer") if c.get("name") == "Terrain"), None)
    if capa is None:
        print("no hay capa Terrain", file=sys.stderr)
        return 1
    rej = _rejilla(capa, ancho_mapa)
    if not (0 <= a.fila < len(rej)):
        print(f"fila {a.fila} fuera del mapa (0..{len(rej) - 1})", file=sys.stderr)
        return 1
    cuerpo = a.gid_cuerpo if a.gid_cuerpo is not None else a.gid
    for f in range(a.fila, min(a.fila + a.alto, len(rej))):
        for c in range(a.col, a.col + a.ancho):
            rej[f][c] = a.gid if f == a.fila else cuerpo
    _guardar_rejilla(capa, rej)

    grupo = next((g for g in raiz.findall("objectgroup") if g.get("name") == "Collision"), None)
    if grupo is None:
        print("no hay grupo de objetos Collision", file=sys.stderr)
        return 1
    x = a.col * tile + a.inset
    ancho_px = a.ancho * tile - 2 * a.inset
    if ancho_px <= 0:
        print(f"inset {a.inset} se come la plataforma entera", file=sys.stderr)
        return 1
    nid = _siguiente_id(raiz)
    ET.SubElement(grupo, "object", {
        "id": str(nid), "name": a.nombre or f"Plat_{nid}", "type": "Solid",
        "x": str(x), "y": str(a.fila * tile),
        "width": str(ancho_px), "height": str(a.alto * tile),
    })
    raiz.set("nextobjectid", str(nid + 1))

    print(f"  Terrain  filas {a.fila}..{a.fila + a.alto - 1}, cols "
          f"{a.col}..{a.col + a.ancho - 1}, gid {a.gid}/{cuerpo}")
    print(f"  Collision id={nid} x={x}..{x + ancho_px} y={a.fila * tile} "
          f"({ancho_px}x{a.alto * tile}, inset {a.inset})")
    return 0


def cmd_mover(raiz: ET.Element, a) -> int:
    for obj in raiz.iter("object"):
        if obj.get("id") == str(a.id):
            antes = (obj.get("x"), obj.get("y"))
            if a.x is not None:
                obj.set("x", str(a.x))
            if a.y is not None:
                obj.set("y", str(a.y))
            print(f"  id={a.id}  {antes} -> ({obj.get('x')}, {obj.get('y')})")
            return 0
    print(f"no existe el objeto id={a.id}", file=sys.stderr)
    return 1


def cmd_borrar(raiz: ET.Element, a) -> int:
    for grupo in raiz.findall("objectgroup"):
        for obj in grupo.findall("object"):
            if obj.get("id") == str(a.id):
                grupo.remove(obj)
                print(f"  borrado id={a.id} de [{grupo.get('name')}]")
                return 0
    print(f"no existe el objeto id={a.id}", file=sys.stderr)
    return 1


def cmd_medir(_raiz, a) -> int:
    """Delega en el calificador del profesor. No reimplementa sus reglas."""
    repo = Path(a.repo)
    orden = [str(repo / ".venv/Scripts/python.exe"), "scripts/grade_stage.py", str(Path(a.tmx).resolve())]
    return subprocess.run(orden, cwd=repo, check=False).returncode


ESCRIBEN = {"plataforma", "mover", "borrar"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tmx")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("capas")
    sub.add_parser("tilesets")
    p = sub.add_parser("listar"); p.add_argument("--tipo")
    p = sub.add_parser("plataforma")
    p.add_argument("--col", type=int, required=True); p.add_argument("--fila", type=int, required=True)
    p.add_argument("--ancho", type=int, default=1); p.add_argument("--gid", type=int, required=True)
    p.add_argument("--alto", type=int, default=1); p.add_argument("--nombre")
    p.add_argument("--gid-cuerpo", type=int, dest="gid_cuerpo")
    p.add_argument("--inset", type=int, default=0)
    p = sub.add_parser("mover")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--x", type=float); p.add_argument("--y", type=float)
    p = sub.add_parser("borrar"); p.add_argument("--id", type=int, required=True)
    p = sub.add_parser("medir"); p.add_argument("--repo", required=True)

    a = ap.parse_args()
    ruta = Path(a.tmx)
    if a.cmd == "medir":
        return cmd_medir(None, a)

    arbol, raiz = _abrir(ruta)
    codigo = {"capas": cmd_capas, "tilesets": cmd_tilesets, "listar": cmd_listar,
              "plataforma": cmd_plataforma, "mover": cmd_mover, "borrar": cmd_borrar}[a.cmd](raiz, a)
    if codigo == 0 and a.cmd in ESCRIBEN:
        _escribir(arbol, ruta)
        print(f"  escrito {ruta}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
