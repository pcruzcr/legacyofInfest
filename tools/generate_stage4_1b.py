"""Genera `assets/maps/stage4_1b/stage4_1b.tmx` — AUD-519.

4.1b es una de las tres variantes que puede tocarle al jugador en el slot
de la Fase 4 (AUD-518, sorteo persistido por partida). Mismo largo y
misma forma que el 4-1 —900×38 baldosas, seis secciones de 150, pasillo
horizontal (AUD-467)— pero sumergido: el jugador nada, no camina, y un
pez abismal (`EnemyPezAbismal`) aparece y desaparece a intervalos,
persiguiendo sin poder tocar ni ser tocado (`src/stages/stage4_1b/stage4_1b.py`).

Sigue el idioma simple de `generate_stage_template.py` (helpers de cadena
pequeños, sin la maquinaria de seis familias de baldosa del 4-1) porque
4.1b no necesita seis identidades de terreno distintas: es agua abierta
sobre un lecho marino continuo, y la variedad la pone la persecución, no
el terreno.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.stages.stage4_1b.trazado import (  # noqa: E402
    FILA_SUELO,
    MH,
    MURO_ANCHO,
    MW,
    TS,
    checkpoints,
)

DESTINO = RAIZ / "assets" / "maps" / "stage4_1b" / "stage4_1b.tmx"

#: GID del tileset genérico (`_gen_procedural_tileset`, AUD-519): índice 0
#: = "floor" llano. `firstgid=1`, así que GID = índice+1. Los muros de los
#: extremos son objetos `Solid` en la capa `Collision`, no baldosas —el
#: mismo criterio que ya usa el 4-1 para sus dos muros.
GID_FLOOR = 1
TILESET_COLS, TILESET_ROWS = 8, 8


def _unir(filas: list[str]) -> str:
    """Mismo formato que escribe Tiled — ver `generate_stage_template.py`
    para el porqué exacto de la coma al final de cada fila."""
    return ",\n".join(filas)


def _capa_vacia(nombre: str, id_: int) -> str:
    fila = ",".join("0" for _ in range(MW))
    filas = _unir([fila for _ in range(MH)])
    return (
        f' <layer id="{id_}" name="{nombre}" width="{MW}" height="{MH}">\n'
        f'  <data encoding="csv">\n{filas}\n</data>\n </layer>\n'
    )


def _capa_terreno(id_: int) -> str:
    """El lecho marino: sólido desde `FILA_SUELO` hasta el fondo. Por
    encima, vacío — el agua no es una baldosa, es la `ZonaDeAgua` de la
    capa `Objects`."""
    filas = []
    for y in range(MH):
        if y < FILA_SUELO:
            filas.append(",".join("0" for _ in range(MW)))
        else:
            filas.append(",".join(str(GID_FLOOR) for _ in range(MW)))
    cuerpo = _unir(filas)
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


def _objetos() -> list[str]:
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

    spawn_col = 10
    obj("PlayerSpawn", spawn_col * TS, (FILA_SUELO - 2) * TS, TS, TS * 2)

    # -- la zona de agua: casi todo el mapa vertical, de punta a punta --
    #
    # Un único objeto grande y no uno por sección: `ZonaDeAgua` no tiene
    # noción de "sección", y partirlo no cambiaría la física, sólo
    # complicaría el generador. `docs/45_SWIMMING_SPEC.md` — la superficie
    # de expulsión se fija al **entrar**, así que con el jugador
    # apareciendo ya sumergido, cerca de la fila 0, no hay a dónde
    # "emerger": este nivel es sumergido de principio a fin.
    obj("WaterZone", 0, 0, MW * TS, (FILA_SUELO - 1) * TS)

    for i, (col, fila) in enumerate(checkpoints(), start=1):
        # AUD-523 — el haz de luz es el checkpoint en los 26 escenarios;
        # no hace falta pedirlo (`brillo=` ya no es una propiedad).
        obj("Checkpoint", col * TS, (fila - 2) * TS, 16, 32,
            checkpoint_id=i)

    obj("NextTrigger", (MW - MURO_ANCHO - 8) * TS, (FILA_SUELO - 4) * TS,
        TS * 2, TS * 6)

    # AUD-531 — «en la parte superior del nivel deben colocarse lámparas
    # que iluminen hacia el agua... un límite visual inalcanzable». El
    # jugador aparece ya sumergido cerca de la fila 0 (§ arriba) y nunca
    # llega a la superficie en este nivel — una hilera de faroles cada
    # ~1200 px marca ese techo sin necesitar geometría sólida: se ve la
    # luz, no se llega a ella. `warm` es el mismo color que ya usa
    # `LIGHT_COLORS` para antorchas/lámparas en el resto del motor.
    # y=80: por debajo de la franja del HUD (retrato/corazones ocupan hasta
    # ~65 px de pantalla a la escala real, AUD-451) para que la luz se lea
    # contra el agua y no quede tapada por la interfaz — y sigue siendo la
    # quinta parte superior de la columna de agua (496 px), bien arriba.
    for col_lampara in range(6, MW - MURO_ANCHO, 75):
        obj("Light", col_lampara * TS, 80, radius=170.0, color="warm",
            intensity=0.9, flicker=True, flicker_speed=1.3, flicker_amount=0.2)

    return [x for x in o if x]


def _colision() -> str:
    """El lecho marino y los muros de los extremos — mismo patrón que el
    4-1: pared sólida en las dos puntas, suelo sólido en `FILA_SUELO`."""
    suelo_y = FILA_SUELO * TS
    alto_suelo = (MH - FILA_SUELO) * TS
    o = [
        _objeto(6, "Solid", "Solid_Seabed", 0, suelo_y, MW * TS, alto_suelo),
        _objeto(7, "Solid", "Solid_Muro_izq", 0, 0, MURO_ANCHO * TS, suelo_y),
        _objeto(8, "Solid", "Solid_Muro_der",
                (MW - MURO_ANCHO) * TS, 0, MURO_ANCHO * TS, suelo_y),
    ]
    return ' <objectgroup id="7" name="Collision">\n' + "".join(o) + " </objectgroup>\n"


def generar() -> str:
    objetos = _objetos()
    partes = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        f'<map version="1.10" tiledversion="1.11.0" orientation="orthogonal" '
        f'renderorder="right-down" width="{MW}" height="{MH}" '
        f'tilewidth="{TS}" tileheight="{TS}" infinite="0" '
        f'nextlayerid="9" nextobjectid="900">\n',
        " <properties>\n",
        '  <property name="schema_version" value="1"/>\n',
        '  <property name="stage_id" value="stage4_1b"/>\n',
        '  <property name="stage_name" value="4-1b  LA FOSA ABISAL"/>\n',
        '  <property name="author" value="Equipo docente — Legacy of Infest"/>\n',
        '  <property name="bgm_track" value="bgm_splash"/>\n',
        '  <property name="climate" value="clear"/>\n',
        '  <property name="zone" type="int" value="4"/>\n',
        # Abisal: oscuro y quieto. `day_length=0` congela la hora, igual
        # que un jefe (docs/86 §3) — no hay ciclo día/noche a 900 baldosas
        # bajo el agua.
        '  <property name="ambient_light" type="float" value="0.28"/>\n',
        '  <property name="day_length" type="float" value="0"/>\n',
        '  <property name="start_hour" type="float" value="2"/>\n',
        # AUD-525 — el nivel entero es `ZonaDeAgua` (física: nado, oxígeno,
        # corriente) pero `WaterEffect` (lo que se ve) es un componente
        # aparte que hay que encender a propósito (AUD-111) — sin esto la
        # fosa se juega sumergida y se ve seca. Tinte más verdoso/oscuro que
        # el azul por defecto de `stage_mecanicas`: abisal, no piscina.
        '  <property name="water_effect" type="bool" value="true"/>\n',
        '  <property name="water_tint" value="#0a3038"/>\n',
        '  <property name="water_alpha" type="float" value="130"/>\n',
        " </properties>\n",
        f' <tileset firstgid="1" name="tileset_stage4_1b" tilewidth="{TS}" '
        f'tileheight="{TS}" tilecount="{TILESET_COLS * TILESET_ROWS}" '
        f'columns="{TILESET_COLS}">\n',
        f'  <image source="../../tilesets/tileset_stage4_1b.png" '
        f'width="{TILESET_COLS * TS}" height="{TILESET_ROWS * TS}"/>\n',
        " </tileset>\n",
        _capa_vacia("BG_Far", 1),
        _capa_vacia("BG_Mid", 2),
        _capa_vacia("BG_Near", 3),
        _capa_terreno(4),
        _capa_vacia("Terrain_Detail", 5),
        ' <objectgroup id="6" name="Objects">\n' + "\n".join(objetos) + "\n </objectgroup>\n",
        _colision(),
        _capa_vacia("FG_Overlay", 8),
        "</map>\n",
    ]
    return "".join(partes)


def main() -> int:
    texto = generar()
    if "--check" in sys.argv:
        actual = DESTINO.read_text(encoding="utf-8") if DESTINO.exists() else ""
        if actual != texto:
            print(f"{DESTINO}: desactualizado — ejecuta este guion sin --check")
            return 1
        print(f"{DESTINO}: al día")
        return 0
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(texto, encoding="utf-8", newline="\n")
    print(f"escrito {DESTINO} ({len(texto.splitlines())} líneas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
