"""Genera las tres plantillas de `assets/maps/stage4_1c/` — AUD-520.

4.1c es la tercera variante del slot de la Fase 4 (AUD-518): un pasillo
horizontal en el aire, sin suelo salvo un colchón de contención muy por
debajo (`src/stages/stage4_1c/trazado.py`), cruzado con plataformas
`RhythmBlock` que aparecen y desaparecen con la música de verdad
(`bpm`/`compas` del mapa → `RelojMusical`, no un temporizador propio).

Por qué tres ficheros y no uno con parámetro
==============================================
El guion pedía que el propio nivel "cambie cada vez que se ingrese". La
decisión (2026-08-17, confirmada con el dueño): no generación procedural
en tiempo real —sin precedente en este motor, con riesgo real de romper
la garantía de nivel siempre completable—, sino varias plantillas
pre-diseñadas elegidas al azar en cada entrada. `trazado.generar_ruta`
sortea una ruta cruzable de verdad (verificada contra `JumpEnvelope`,
`tests/test_stage4_1c.py`) para una semilla dada; este generador congela
tres semillas en tres TMX de verdad, y `Stage4_1C` elige uno al azar en
cada `__init__` — cada entrada al nivel, no una vez por partida.
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.stages.stage4_1c.trazado import (  # noqa: E402
    FILA_DE_CONTENCION,
    MH,
    MURO_ANCHO,
    MW,
    TS,
    generar_ruta,
)

DIRECTORIO = RAIZ / "assets" / "maps" / "stage4_1c"

#: Semilla -> nombre de fichero. Tres plantillas — ni una (no habría
#: variedad) ni una docena (mantenimiento sin beneficio añadido: el
#: mecanismo de sorteo no distingue tres de treinta).
PLANTILLAS: dict[str, int] = {"a": 1, "b": 2, "c": 3}

GID_FLOOR = 1
TILESET_COLS, TILESET_ROWS = 8, 8


def _unir(filas: list[str]) -> str:
    return ",\n".join(filas)


def _capa_vacia(nombre: str, id_: int) -> str:
    fila = ",".join("0" for _ in range(MW))
    filas = _unir([fila for _ in range(MH)])
    return (
        f' <layer id="{id_}" name="{nombre}" width="{MW}" height="{MH}">\n'
        f'  <data encoding="csv">\n{filas}\n</data>\n </layer>\n'
    )


def _capa_terreno(id_: int, ruta) -> str:
    """Sólo dos cosas llevan baldosa: las plataformas sólidas (para que
    se vean, no sólo colisionen) y el colchón de contención del fondo.
    Los bloques rítmicos no llevan tile — se dibujan solos, coloreados
    según `presente` (`dibujo_mecanicas.py::dibujar_mecanicas_ecs`)."""
    filas = [["0"] * MW for _ in range(MH)]
    for p in ruta:
        if p.patron is not None:
            continue
        for dx in range(p.ancho):
            col = p.columna + dx
            if 0 <= col < MW:
                filas[p.fila][col] = str(GID_FLOOR)
    for col in range(MW):
        filas[FILA_DE_CONTENCION][col] = str(GID_FLOOR)
    cuerpo = _unir([",".join(f) for f in filas])
    return (
        f' <layer id="{id_}" name="Terrain" width="{MW}" height="{MH}">\n'
        f'  <data encoding="csv">\n{cuerpo}\n</data>\n </layer>\n'
    )


def _objeto(id_: int, tipo: str, nombre: str, x: int, y: int,
            w: int | None = None, h: int | None = None,
            props: dict[str, tuple[str, str]] | None = None) -> str:
    medidas = ""
    if w is not None and h is not None:
        medidas = f' width="{w}" height="{h}"'
    if not props:
        return f'  <object id="{id_}" type="{tipo}" name="{nombre}" x="{x}" y="{y}"{medidas}/>\n'
    lineas = [
        f'  <object id="{id_}" type="{tipo}" name="{nombre}" x="{x}" y="{y}"{medidas}>',
        "   <properties>",
    ]
    for clave, (tipo_p, valor) in props.items():
        attr = f' type="{tipo_p}"' if tipo_p else ""
        lineas.append(f'    <property name="{clave}"{attr} value="{valor}"/>')
    lineas += ["   </properties>", "  </object>"]
    return "\n".join(lineas) + "\n"


def _objetos(ruta) -> list[str]:
    o: list[str] = []
    ident = [100]

    def obj(tipo, x, y, w=None, h=None, **props):
        ident[0] += 1
        props_tipadas = {
            k: ("bool" if isinstance(v, bool) else
                "float" if isinstance(v, float) else
                "int" if isinstance(v, int) else "", str(v))
            for k, v in props.items()
        }
        o.append(_objeto(ident[0], tipo, f"{tipo}_{ident[0]}", x, y, w, h,
                         props_tipadas or None))

    primera = ruta[0]
    obj("PlayerSpawn", (primera.columna + 1) * TS, (primera.fila - 2) * TS, TS, TS * 2)

    for p in ruta[1:-1]:
        if p.patron is not None:
            obj("RhythmBlock", p.columna * TS, p.fila * TS, p.ancho * TS, TS,
                patron=p.patron, desfase=p.desfase)
        elif p.checkpoint_id is not None:
            # AUD-523 — el haz de luz es el checkpoint en los 26
            # escenarios; no hace falta pedirlo.
            obj("Checkpoint", (p.columna + 1) * TS, (p.fila - 2) * TS, 16, 32,
                checkpoint_id=p.checkpoint_id)

    ultima = ruta[-1]
    obj("NextTrigger", (ultima.columna + ultima.ancho - 2) * TS,
        (ultima.fila - 4) * TS, TS * 2, TS * 6)

    return [x for x in o if x]


def _colision(ruta) -> str:
    """AUD-520 — `scripts/grade_stage.py`/`level_metrics.analyse_geometry`
    marcan huecos y repechos "imposibles" contra este mapa (verificado
    con `assets/maps/stage4_1c/stage4_1c_a.tmx` real): analiza TODOS los
    `Solid` como si formaran una única ruta de salto, y aquí `Solid_Muro_*`
    (los límites laterales) y `Solid_Contencion` (el colchón del fondo,
    fila `FILA_DE_CONTENCION`) no están pensados para saltarse **entre
    sí** — son contención, no plataformas. Entre las plataformas reales
    (las que trae `ruta`) el análisis no encuentra ni un solo hueco ni
    repecho imposible; sólo aparecen al incluir las paredes y el colchón.
    El propio calificador ya avisa de esta clase de falso positivo
    ("el nivel usa... plataformas móviles, que el analizador de rutas no
    modela") porque tampoco sabe leer `RhythmBlock` — no se corrige
    aquí, se documenta.
    """
    o = []
    n = 6
    for p in ruta:
        if p.patron is not None:
            continue  # el sistema ECS pone/quita Solido según la música
        n += 1
        o.append(_objeto(n, "Solid", f"Solid_{n}", p.columna * TS, p.fila * TS,
                         p.ancho * TS, TS))
    n += 1
    o.append(_objeto(n, "Solid", "Solid_Contencion", 0, FILA_DE_CONTENCION * TS,
                     MW * TS, (MH - FILA_DE_CONTENCION) * TS))
    n += 1
    o.append(_objeto(n, "Solid", "Solid_Muro_izq", 0, 0, MURO_ANCHO * TS, MH * TS))
    n += 1
    o.append(_objeto(n, "Solid", "Solid_Muro_der", (MW - MURO_ANCHO) * TS, 0,
                     MURO_ANCHO * TS, MH * TS))
    return ' <objectgroup id="7" name="Collision">\n' + "".join(o) + " </objectgroup>\n"


def generar(semilla: int) -> str:
    ruta = generar_ruta(semilla)
    objetos = _objetos(ruta)
    partes = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        f'<map version="1.10" tiledversion="1.11.0" orientation="orthogonal" '
        f'renderorder="right-down" width="{MW}" height="{MH}" '
        f'tilewidth="{TS}" tileheight="{TS}" infinite="0" '
        f'nextlayerid="9" nextobjectid="900">\n',
        " <properties>\n",
        '  <property name="schema_version" value="1"/>\n',
        '  <property name="stage_id" value="stage4_1c"/>\n',
        '  <property name="stage_name" value="4-1c  LO QUE FLOTA EN LA NIEBLA"/>\n',
        '  <property name="author" value="Equipo docente — Legacy de Infest"/>\n',
        '  <property name="bgm_track" value="bgm_zone1_traverse"/>\n',
        '  <property name="climate" value="clear"/>\n',
        '  <property name="zone" type="int" value="4"/>\n',
        '  <property name="ambient_light" type="float" value="0.55"/>\n',
        '  <property name="day_length" type="float" value="0"/>\n',
        '  <property name="start_hour" type="float" value="5"/>\n',
        # AUD-520 — lo que hace "completamente musical" al nivel: sin
        # esto, RhythmBlock cae al modo por segundos (docstring de
        # `BloqueRitmico`) y dos bloques con el mismo patrón dejan de
        # coincidir con la canción a los cinco minutos.
        '  <property name="bpm" type="float" value="100"/>\n',
        '  <property name="compas" type="int" value="4"/>\n',
        " </properties>\n",
        f' <tileset firstgid="1" name="tileset_stage4_1c" tilewidth="{TS}" '
        f'tileheight="{TS}" tilecount="{TILESET_COLS * TILESET_ROWS}" '
        f'columns="{TILESET_COLS}">\n',
        f'  <image source="../../tilesets/tileset_stage4_1c.png" '
        f'width="{TILESET_COLS * TS}" height="{TILESET_ROWS * TS}"/>\n',
        " </tileset>\n",
        _capa_vacia("BG_Far", 1),
        _capa_vacia("BG_Mid", 2),
        _capa_vacia("BG_Near", 3),
        _capa_terreno(4, ruta),
        _capa_vacia("Terrain_Detail", 5),
        ' <objectgroup id="6" name="Objects">\n' + "\n".join(objetos) + "\n </objectgroup>\n",
        _colision(ruta),
        _capa_vacia("FG_Overlay", 8),
        "</map>\n",
    ]
    return "".join(partes)


def main() -> int:
    revisar = "--check" in sys.argv
    algo_desactualizado = False
    for nombre, semilla in PLANTILLAS.items():
        destino = DIRECTORIO / f"stage4_1c_{nombre}.tmx"
        texto = generar(semilla)
        if revisar:
            actual = destino.read_text(encoding="utf-8") if destino.exists() else ""
            if actual != texto:
                print(f"{destino}: desactualizado — ejecuta este guion sin --check")
                algo_desactualizado = True
            else:
                print(f"{destino}: al día")
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8", newline="\n")
        print(f"escrito {destino} ({len(texto.splitlines())} líneas)")
    return 1 if algo_desactualizado else 0


if __name__ == "__main__":
    sys.exit(main())
