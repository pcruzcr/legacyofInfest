"""Genera `assets/maps/stage4_1b/stage4_1b.tmx` — AUD-519, rediseñado en
AUD-575.

4.1b es una de las tres variantes que puede tocarle al jugador en el slot
de la Fase 4 (AUD-518, sorteo persistido por partida). Mismo largo y
misma forma que el 4-1 —900×38 baldosas, seis secciones de 150, pasillo
horizontal (AUD-467)—, pero es la **mina inundada** (AUD-575): el agua
llega a la fila 11, no al techo; el jugador nada bajo once filas de aire
con estalactitas, emerge en los andenes secos, esquivando la maleza, los
cangrejos y las medusas mientras el pez abismal aparece y desaparece.

Todo el terreno que no es lecho (andenes, estribos, pilares, vigas) vive
en `BLOQUES_DE_TERRENO` de `trazado.py` — una sola fuente de verdad para
las baldosas y la colisión. La decoración (estalactitas, algas, vigas,
óxido) usa la fila extra del tileset de la mina (`_gen_tileset_stage4_1b`
en `generate_all_assets.py`, GIDs 65-72), y la fauna fija (cangrejos y
medusas) la instancia la escena, no el TMX — como el pez abismal.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.stages.stage4_1b.trazado import (  # noqa: E402
    ALGAS,
    BLOQUES_DE_MINERAL,
    BLOQUES_DE_TERRENO,
    CADENAS,
    ESTALACTITAS,
    FILA_FONDO_AGUA,
    FILA_SUELO,
    FILA_SUPERFICIE_AGUA,
    HERRAMIENTAS,
    LAMPARAS_APAGADAS,
    LUCES,
    MH,
    MURO_ANCHO,
    MW,
    OXIDO_EN_EL_LECHO,
    TS,
    VAGONETAS,
    VIGAS_DEL_PATIO,
    ZONAS_DE_CORRIENTE,
    checkpoints,
)

DESTINO = RAIZ / "assets" / "maps" / "stage4_1b" / "stage4_1b.tmx"

#: GID del tileset de la mina (`_gen_tileset_stage4_1b`, AUD-575/576):
#: índice 0 = "floor" llano. `firstgid=1`, así que GID = índice+1. Las
#: filas 0-7 son las ocho baldosas genéricas (AUD-519); la fila 8
#: (GIDs 65-72) es la decoración de la mina: estalactitas, algas, viga
#: oxidada, planta, roca con óxido y soporte con riel; la fila 9
#: (GIDs 73-76, AUD-576) es la narrativa ambiental: vagoneta, cadena,
#: lámpara apagada y pico. Los muros de los extremos son objetos `Solid`
#: en la capa `Collision`, no baldosas —el mismo criterio que ya usa el
#: 4-1 para sus dos muros.
GID_FLOOR = 1
GID_DECO = 2
GID_TABLONES = 5
GID_OXIDO = 6
GID_ESTALACTITA_GRANDE = 65
GID_ESTALACTITA_PEQUENA = 66
GID_ALGA = 67
GID_ALGA_ALTA = 68
GID_VIGA = 69
GID_ROCA_OXIDO = 71
GID_VAGONETA = 73
GID_CADENA = 74
GID_LAMPARA_APAGADA = 75
GID_PICO = 76
TILESET_COLS, TILESET_ROWS = 8, 10


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
    """El lecho de la mina y todo el terreno que no es lecho (andenes,
    estribos, pilares, vigas sumergidas) — la misma geometría que la
    capa `Collision` (BLOQUES_DE_TERRENO). Por encima, vacío: el agua no
    es una baldosa, es la `ZonaDeAgua` de la capa `Objects`."""
    celdas: list[list[int]] = [[0] * MW for _ in range(MH)]

    def llenar(col_ini: int, col_fin: int, fila_techo: int, fila_fondo: int,
               gid: int) -> None:
        for y in range(fila_techo, fila_fondo):
            for x in range(col_ini, col_fin):
                celdas[y][x] = gid

    # Lecho continuo (fila 32 a 37): baldosa de piedra con algún tile de
    # óxido salpicado, para que el suelo no sea un monobloque.
    for x in range(MW):
        for y in range(FILA_SUELO, MH):
            celdas[y][x] = GID_FLOOR
    for col, fila in OXIDO_EN_EL_LECHO:
        celdas[fila][col] = GID_ROCA_OXIDO

    # Terreno levantado: andenes y pilares con la baldosa "deco" (piedra
    # con veta), estribos y vigas con los tablones.
    for col_ini, col_fin, fila_techo, fila_fondo in BLOQUES_DE_TERRENO:
        gid = GID_DECO if fila_techo <= FILA_SUPERFICIE_AGUA else GID_TABLONES
        llenar(col_ini, col_fin, fila_techo, fila_fondo, gid)

    filas = []
    for y in range(MH):
        filas.append(",".join(str(c) for c in celdas[y]))
    cuerpo = _unir(filas)
    return (
        f' <layer id="{id_}" name="Terrain" width="{MW}" height="{MH}">\n'
        f'  <data encoding="csv">\n{cuerpo}\n</data>\n </layer>\n'
    )


def _capa_de_tiles(nombre: str, id_: int, puntos: list[tuple[int, int, int]]) -> str:
    """Capa de decoración (BG_Near / Terrain_Detail): `(col, fila, gid)`
    sobre fondo vacío — la mina no necesita ni un solo tile más."""
    celdas: list[list[int]] = [[0] * MW for _ in range(MH)]
    for col, fila, gid in puntos:
        celdas[fila][col] = gid
    filas = _unir([",".join(str(c) for c in celdas[y]) for y in range(MH)])
    return (
        f' <layer id="{id_}" name="{nombre}" width="{MW}" height="{MH}">\n'
        f'  <data encoding="csv">\n{filas}\n</data>\n </layer>\n'
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

    # AUD-575 — el jugador nace en la boca de la mina: sobre el andén
    # seco de la entrada (techo en la fila 8), no sumergido. La primera
    # decisión del nivel es ya "¿entro al agua?".
    obj("PlayerSpawn", 8 * TS, (8 - 2) * TS, TS, TS * 2)

    # -- la zona de agua: de la superficie (fila 11) al lecho --
    #
    # AUD-575 — el agua ya NO cubre la columna entera: la superficie está
    # a 176 px del techo, y las once filas de aire son el colchón de la
    # cueva (el techo con estalactitas se ve cerca, inalcanzable — "estar
    # encerrados bajo una gran cantidad de agua"). Emerger es de verdad
    # salir del agua: `ControlDeNado._salir` expulsa a la superficie y el
    # aire se recupera (docs/45_SWIMMING_SPEC.md).
    obj("WaterZone", 0, FILA_SUPERFICIE_AGUA * TS, MW * TS,
        (FILA_FONDO_AGUA + 1 - FILA_SUPERFICIE_AGUA) * TS)

    # AUD-543/575 — corrientes y maleza: `WaterZone` adicionales, más
    # angostas, superpuestas a la de arriba. `sistema_corriente_de_agua`
    # (motor) suma la `corriente` de **cada** zona que toca al jugador, y
    # una corriente en cero no hace nada (`continue` inmediato) — así que
    # la zona grande (corriente cero, sólo marca "esto es agua") y estas
    # franjas conviven sin pisarse. La maleza es corriente en contra: las
    # algas agarran al que nada por ellas (flora como obstáculo, AUD-575).
    for col_ini, col_fin, corriente_x in ZONAS_DE_CORRIENTE:
        obj("WaterZone", col_ini * TS, FILA_SUPERFICIE_AGUA * TS,
            (col_fin - col_ini) * TS,
            (FILA_FONDO_AGUA + 1 - FILA_SUPERFICIE_AGUA) * TS,
            corriente_x=corriente_x, corriente_y=0.0)

    # AUD-557/575 — bloques de mineral: se rompen con el ataque acuático
    # (o el de tierra, sobre el andén). Uno por sección y medio, apoyados
    # en el lecho, en las vigas del pozo o en el andén del patio — los de
    # las vigas (S5) abren el hueco para emerger bajo el techo cortado.
    for col, fila_techo in BLOQUES_DE_MINERAL:
        obj("BreakableBlock", col * TS, (fila_techo - 2) * TS, TS * 2, TS * 2,
            golpes=1)

    for i, (col, fila) in enumerate(checkpoints(), start=1):
        # AUD-523 — el haz de luz es el checkpoint en los 26 escenarios.
        obj("Checkpoint", col * TS, (fila - 2) * TS, 16, 32,
            checkpoint_id=i)

    obj("NextTrigger", (MW - MURO_ANCHO - 8) * TS, (FILA_SUELO - 4) * TS,
        TS * 2, TS * 6)

    # AUD-531/574/575 — las luces de la mina. `LUCES` del trazado define
    # tres familias:
    #   · `warm`  — faroles del techo (el "techo de luz" que marca el
    #     límite); el haz llega a la franja de nado y se lee contra el
    #     aire y la superficie del agua.
    #   · `blood` — alarma de peligro (maleza, esclusa, pozo): la mina
    #     avisa dónde no conviene bucear. Parpadeo más rápido que el de
    #     una antorcha — es una alarma, no una llama.
    #   · `white` — luz de trabajo (entrada, patio, desagüe): lugares
    #     donde se sale del agua y se respira. Estable, sin parpadeo:
    #     la seguridad no tiembla.
    for col, fila, color in LUCES:
        if color == "blood":
            radio, intensidad, flicker = 180.0, 0.95, True
        elif color == "white":
            radio, intensidad, flicker = 200.0, 1.0, False
        else:
            radio, intensidad, flicker = 230.0, 1.0, True
        obj("Light", col * TS, fila * TS, radius=radio, color=color,
            intensity=intensidad, flicker=flicker,
            flicker_speed=2.2 if color == "blood" else 1.3,
            flicker_amount=0.3 if color == "blood" else 0.2)

    return [x for x in o if x]


def _colision() -> str:
    """El lecho, los andenes/pilares/vigas y los muros de los extremos —
    mismo patrón que el 4-1: pared sólida en las dos puntas, suelo sólido
    en `FILA_SUELO` y `Solid` por cada bloque de `BLOQUES_DE_TERRENO`."""
    o = [
        _objeto(6, "Solid", "Solid_Seabed", 0, FILA_SUELO * TS,
                MW * TS, (MH - FILA_SUELO) * TS),
        _objeto(7, "Solid", "Solid_Muro_izq", 0, 0, MURO_ANCHO * TS,
                FILA_SUELO * TS),
        _objeto(8, "Solid", "Solid_Muro_der",
                (MW - MURO_ANCHO) * TS, 0, MURO_ANCHO * TS, FILA_SUELO * TS),
    ]
    for i, (col_ini, col_fin, fila_techo, fila_fondo) in enumerate(BLOQUES_DE_TERRENO):
        o.append(_objeto(9 + i, "Solid", f"Solid_Anden_{i}",
                         col_ini * TS, fila_techo * TS,
                         (col_fin - col_ini) * TS,
                         (fila_fondo - fila_techo) * TS))
    return ' <objectgroup id="7" name="Collision">\n' + "".join(o) + " </objectgroup>\n"


def generar() -> str:
    objetos = _objetos()
    estalactitas = [
        (col, fila, GID_ESTALACTITA_GRANDE if i % 2 == 0 else GID_ESTALACTITA_PEQUENA)
        for i, (col, fila) in enumerate(ESTALACTITAS)
    ]
    detalle = [
        (col, fila, GID_VIGA) for col, fila in VIGAS_DEL_PATIO
    ] + [
        (col, fila, GID_ALGA_ALTA if i % 3 == 0 else GID_ALGA)
        for i, (col, fila) in enumerate(ALGAS)
    ] + [
        (col, fila, GID_VAGONETA) for col, fila in VAGONETAS
    ] + [
        (col, fila, GID_CADENA) for col, fila in CADENAS
    ] + [
        (col, fila, GID_LAMPARA_APAGADA) for col, fila in LAMPARAS_APAGADAS
    ] + [
        (col, fila, GID_PICO) for col, fila in HERRAMIENTAS
    ]
    partes = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        f'<map version="1.10" tiledversion="1.11.0" orientation="orthogonal" '
        f'renderorder="right-down" width="{MW}" height="{MH}" '
        f'tilewidth="{TS}" tileheight="{TS}" infinite="0" '
        f'nextlayerid="9" nextobjectid="900">\n',
        " <properties>\n",
        '  <property name="schema_version" value="1"/>\n',
        '  <property name="stage_id" value="stage4_1b"/>\n',
        '  <property name="stage_name" value="4-1b  LA MINA INUNDADA"/>\n',
        '  <property name="author" value="Equipo docente — Legacy of Infest"/>\n',
        # AUD-575 — la música propia del nivel: `assets/music/4_1_b.mp3`
        # (el tema en loop de la mina). El motor resuelve el nombre a
        # archivo por convención (`resolver_pista_de_musica`, .ogg > .wav
        # > .mp3) y lo reproduce en loop desde `StageScene.on_enter`.
        '  <property name="bgm_track" value="4_1_b"/>\n',
        '  <property name="climate" value="clear"/>\n',
        '  <property name="zone" type="int" value="4"/>\n',
        # Abisal pero legible: `day_length=0` congela la hora, igual que
        # un jefe (docs/86 §3) — no hay ciclo día/noche a 900 baldosas
        # bajo la montaña. 0.45 (AUD-574) deja ver el agua, el lecho y al
        # propio jugador — la misma lectura que un nivel acuático clásico
        # (SMB 2-2): agua clara y todo visible, oscuridad sólo en la
        # decoración.
        '  <property name="ambient_light" type="float" value="0.45"/>\n',
        '  <property name="day_length" type="float" value="0"/>\n',
        '  <property name="start_hour" type="float" value="2"/>\n',
        # AUD-525 — el agua es `ZonaDeAgua` (física: nado, oxígeno,
        # corriente) pero `WaterEffect` (lo que se ve) es un componente
        # aparte que hay que encender a propósito (AUD-111) — sin esto la
        # mina se juega sumergida y se ve seca.
        #
        # AUD-574/575 — el tinte `#1a5c6e` con alpha 150: azul de fosa
        # (ni piscina turquesa ni tinta), las ondas se leen en toda la
        # columna y marcan dónde empieza el agua contra el aire de la
        # cueva — la superficie con olas que se ve al instante, como en
        # SMB 2-2.
        '  <property name="water_effect" type="bool" value="true"/>\n',
        '  <property name="water_tint" value="#1a5c6e"/>\n',
        '  <property name="water_alpha" type="float" value="150"/>\n',
        # AUD-543 — «fauna nueva (calamares, peces de colores)» y «coral
        # que cae»: los tres en un solo tipo de partícula porque un mapa
        # sólo declara un `ambient_fx` a la vez (`AmbientParticleSystem.
        # TIPOS`, ver la nota ahí de por qué no son tres tipos separados).
        # AUD-575 — el ecosistema vivo lo completan los cangrejos y las
        # medusas que la escena instancia (presencia, nunca daño).
        '  <property name="ambient_fx" value="vida_abisal"/>\n',
        '  <property name="ambient_fx_rate" type="float" value="14"/>\n',
        " </properties>\n",
        f' <tileset firstgid="1" name="tileset_stage4_1b" tilewidth="{TS}" '
        f'tileheight="{TS}" tilecount="{TILESET_COLS * TILESET_ROWS}" '
        f'columns="{TILESET_COLS}">\n',
        f'  <image source="../../tilesets/tileset_stage4_1b.png" '
        f'width="{TILESET_COLS * TS}" height="{TILESET_ROWS * TS}"/>\n',
        " </tileset>\n",
        _capa_vacia("BG_Far", 1),
        _capa_vacia("BG_Mid", 2),
        _capa_de_tiles("BG_Near", 3, estalactitas),
        _capa_terreno(4),
        _capa_de_tiles("Terrain_Detail", 5, detalle),
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