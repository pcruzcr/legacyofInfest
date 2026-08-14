#!/usr/bin/env python3
"""
Genera `assets/maps/stage4_1/stage4_1.tmx` — El Cementerio Sagrado.

El nivel, en una frase (AUD-467)
==================================
Un **pasillo horizontal** de 900 columnas, seis secciones de 150 cada una,
sin un solo enemigo y sin una sola trampa mortal (el suelo es firme en todas
partes salvo la loma de la Fase 3, que sube, no perfora). Reemplaza al pozo
vertical de AUD-462…466, que el dueño del proyecto rechazó jugado: *«el
nuevo nivel es horizontal completamente»* leía como una repisa ancha en
pantalla, no como un pozo — y el guion original pide justo eso, un pasillo
que atraviesa espacios distintos.

Este generador usa todavía el tileset del cementerio
(`tileset_cemetery.png`) como marcador de posición para el terreno — el
tileset propio de seis familias (`tileset_stage4_1.png`) llega en el
siguiente lote (AUD-468). Lo que ya es definitivo aquí es la **geometría**:
la forma del pasillo, la loma real, los segmentos de musgo/lodo, la
cutscene de introducción, el diálogo y el easter egg.

Aquí sólo se coloca lo que es geometría; la gradación de color, el ciclo de
luna, el shake, la serpiente de fondo y la sombra del Gavilán los mueve la
escena (`stage4_1.py`). Las columnas de cada cosa viven en
`src/stages/stage4_1/trazado.py`, que es también de donde las lee la escena.

La regla de oro: **cero enemigos**
-----------------------------------
No se coloca ni uno. `tests/test_stage4_1.py` lo comprueba cargando el mapa
y contando `entity_list`.
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.stages.stage4_1.trazado import (  # noqa: E402
    ARBOLES_FASE4,
    ARRASTRE_DEL_MUSGO,
    COLUMNA_LAPIDA_HUGO,
    COLUMNA_LAPIDA_TERESA,
    FRENO_DEL_LODO,
    HUESOS_FASE3,
    LOMA_FIN_BAJADA,
    LOMA_INICIO_SUBIDA,
    MH,
    MURO_ANCHO,
    MW,
    NOMBRE_LAPIDA_HUGO,
    NOMBRE_LAPIDA_TERESA,
    SEGMENTOS_FASE2,
    TS,
    TUMBAS_FASE5,
    checkpoints,
    grietas_de_pisada,
    loma,
    perfil_del_suelo,
)

DESTINO = PROJECT_ROOT / "assets" / "maps" / "stage4_1" / "stage4_1.tmx"

# Marcador de posición: el tileset propio llega en AUD-468. Reusa el
# cementerio para no bloquear la geometría en lo que se genera el nuevo.
TILESET = "../../tilesets/tileset_cemetery.png"
TS_COLUMNAS = 8
TS_TOTAL = 64
TS_IMAGEN_PX = 128

VACIO = 0
PIEDRA = 2
RELLENO = 3
MURO = 4
MUSGO = 5
MUSGO_RELLENO = 6
LODO = 7
LODO_RELLENO = 8
LAPIDA_ALTA = 9
LOSA = 10
CRUZ = 11

BALDOSAS = {
    "piedra": (PIEDRA, RELLENO),
    "musgo": (MUSGO, MUSGO_RELLENO),
    "lodo": (LODO, LODO_RELLENO),
}


def _material_de(columna: int) -> str:
    for inicio, ancho, material in SEGMENTOS_FASE2:
        if inicio <= columna < inicio + ancho:
            return material
    return "piedra"


def _terreno() -> list[list[int]]:
    """La geometría del pasillo, columna a columna."""
    g = [[VACIO] * MW for _ in range(MH)]
    perfil = perfil_del_suelo()

    for x in range(MW):
        superficie = perfil[x]
        material = _material_de(x)
        arriba, abajo = BALDOSAS[material]
        g[superficie][x] = arriba
        for fila in range(superficie + 1, MH):
            g[fila][x] = abajo

    # Muros en los dos extremos — el pasillo no se sale por los lados.
    for y in range(MH):
        for x in range(MURO_ANCHO):
            g[y][x] = MURO
            g[y][MW - 1 - x] = MURO

    # El easter egg: dos lápidas.
    suelo_egg = perfil[COLUMNA_LAPIDA_TERESA]
    g[suelo_egg - 1][COLUMNA_LAPIDA_TERESA] = LOSA
    g[suelo_egg - 2][COLUMNA_LAPIDA_TERESA] = LAPIDA_ALTA
    suelo_egg2 = perfil[COLUMNA_LAPIDA_HUGO]
    g[suelo_egg2 - 1][COLUMNA_LAPIDA_HUGO] = LOSA
    g[suelo_egg2 - 2][COLUMNA_LAPIDA_HUGO] = LAPIDA_ALTA

    # Los huesos de la Fase 3 — marcador de posición hasta AUD-468.
    for col in HUESOS_FASE3:
        fila = perfil[col]
        g[fila - 1][col] = CRUZ

    # Las tumbas de conquistador de la Fase 5 — cruces en el suelo.
    for col in TUMBAS_FASE5:
        fila = perfil[col]
        g[fila - 1][col] = CRUZ

    return g


def _colisiones() -> list[str]:
    """La capa `Collision`: los muros y el suelo, columna a columna."""
    r: list[str] = []
    ident = [1]

    def solido(x: int, y: int, w: int, h: int, tipo: str = "Solid") -> None:
        ident[0] += 1
        r.append(
            f'  <object id="{ident[0]}" type="{tipo}" x="{x}" y="{y}"'
            f' width="{w}" height="{h}"/>',
        )

    solido(0, 0, MURO_ANCHO * TS, MH * TS)
    solido((MW - MURO_ANCHO) * TS, 0, MURO_ANCHO * TS, MH * TS)

    # El suelo se agrupa en tramos de la misma altura, en vez de una caja
    # por columna: 900 cajas de 16 px serían el mismo defecto que
    # `check_los_mapas_no_traen_miles_de_rectangulos.py` vigila en el resto
    # del proyecto.
    perfil = perfil_del_suelo()
    inicio = MURO_ANCHO
    for x in range(MURO_ANCHO + 1, MW - MURO_ANCHO + 1):
        if x == MW - MURO_ANCHO or perfil[x] != perfil[inicio]:
            fila = perfil[inicio]
            solido(inicio * TS, fila * TS, (x - inicio) * TS, (MH - fila) * TS)
            inicio = x

    return r


def _objetos() -> list[str]:
    """Los objetos del TMX. Ni un enemigo, ni un `DeathPit`, ni una `HazardZone`."""
    o: list[str] = []
    ident = [100]

    def obj(tipo: str, x: int, y: int, w: int, h: int, **props: object) -> None:
        ident[0] += 1
        cuerpo = (
            f'  <object id="{ident[0]}" name="{tipo}_{ident[0]}" type="{tipo}"'
            f' x="{x}" y="{y}" width="{w}" height="{h}">'
        )
        if props:
            cuerpo += "\n   <properties>"
            for k, v in props.items():
                if isinstance(v, bool):
                    cuerpo += f'\n    <property name="{k}" type="bool" value="{str(v).lower()}"/>'
                elif isinstance(v, int):
                    cuerpo += f'\n    <property name="{k}" type="int" value="{v}"/>'
                elif isinstance(v, float):
                    cuerpo += f'\n    <property name="{k}" type="float" value="{v}"/>'
                else:
                    texto = (str(v).replace("&", "&amp;").replace("<", "&lt;")
                             .replace('"', "&quot;").replace("\n", "&#10;"))
                    cuerpo += f'\n    <property name="{k}" value="{texto}"/>'
            cuerpo += "\n   </properties>"
        cuerpo += "\n  </object>"
        o.append(cuerpo)

    perfil = perfil_del_suelo()
    spawn_col = MURO_ANCHO + 3
    obj("PlayerSpawn", spawn_col * TS, (perfil[spawn_col] - 3) * TS, 16, 32)

    # ── La cutscene de introducción ────────────────────────────
    #
    # Objeto-punto (ancho y alto 0): dispara al empezar el escenario, sin
    # que el jugador tenga que cruzar ninguna zona (AUD-136,
    # `stage_objetos.py::_handle_cutscene`). El guion está en el
    # mini-lenguaje de `cutscene_guion.py` — nada de Python nuevo.
    guion_intro = (
        "fundido entrada 1.5\n"
        "dialogo Voces;Los espiritus hablan de Paburu, en una lengua antigua.;2.5\n"
        "camara . . 2.0\n"
        "dialogo Jhon;Este lugar... lo reconozco.;2.0\n"
    )
    obj("Cutscene", spawn_col * TS, (perfil[spawn_col] - 3) * TS, 0, 0,
        guion=guion_intro, bloquea=True, saltable=True, una_vez=True)

    # ── Los puntos de reaparición ──────────────────────────────
    for i, (col, fila) in enumerate(checkpoints(), start=1):
        obj("Checkpoint", col * TS, (fila - 2) * TS, 16, 32, checkpoint_id=i)

    # ── El easter egg de la Fase 1 ──────────────────────────────
    obj("MessageTrigger_Once",
        (COLUMNA_LAPIDA_TERESA - 1) * TS, (perfil[COLUMNA_LAPIDA_TERESA] - 4) * TS,
        3 * TS, 3 * TS, text=NOMBRE_LAPIDA_TERESA)
    obj("MessageTrigger_Once",
        (COLUMNA_LAPIDA_HUGO - 1) * TS, (perfil[COLUMNA_LAPIDA_HUGO] - 4) * TS,
        3 * TS, 3 * TS, text=NOMBRE_LAPIDA_HUGO)

    # ── El diálogo de los tres espíritus ────────────────────────
    #
    # `data/dialogues/stage4_1.json` trae los árboles; esto sólo coloca el
    # disparador. Uno hacia la mitad de cada sección con espíritu.
    from src.stages.stage4_1.fases import FASES

    for fase in FASES:
        if fase.dialogo_id is None:
            continue
        col = fase.desde_columna + 60
        obj("MessageTrigger_Once", col * TS, (perfil[col] - 3) * TS, 32, 32,
            dialogue=fase.dialogo_id)

    # ── Las superficies de la Fase 2 (musgo y lodo) ────────────
    for inicio, ancho, material in SEGMENTOS_FASE2:
        fila = perfil[inicio]
        if material == "musgo":
            obj("FrictionZone", inicio * TS, (fila - 2) * TS, ancho * TS, 2 * TS,
                arrastre=ARRASTRE_DEL_MUSGO)
        elif material == "lodo":
            obj("FrictionZone", inicio * TS, (fila - 2) * TS, ancho * TS, 2 * TS,
                multiplicador=FRENO_DEL_LODO)

    # ── La loma de la Fase 3: dos `Slope` reales ────────────────
    for lx, lfila_arriba, lancho, lalto, lsube in loma():
        obj("Slope", lx * TS, lfila_arriba * TS, lancho * TS, lalto * TS,
            sube=lsube)

    # ── El viento de la Fase 3 («carácter ventoso» de Tilarán) ──
    obj("WindZone", (LOMA_INICIO_SUBIDA - 40) * TS, 0,
        (LOMA_FIN_BAJADA - LOMA_INICIO_SUBIDA + 80) * TS, MH * TS,
        fuerza_x=-60.0, fuerza_y=0.0, periodo=3.2)

    # ── Las grietas de la Fase 6, apagadas: las enciende la escena ──
    for col, fila in grietas_de_pisada():
        obj("Light", col * TS, (fila - 2) * TS, TS, TS,
            radius=70.0, color="#7CFFA0", intensity=0.0)

    # ── El umbral ──────────────────────────────────────────────
    ultima = MW - MURO_ANCHO - 4
    obj("MessageTrigger_Once", ultima * TS, (perfil[ultima] - 5) * TS,
        2 * TS, 5 * TS, text="Paburu despierta.")
    obj("NextTrigger", ultima * TS, (perfil[ultima] - 3) * TS, 2 * TS, 3 * TS)

    return [x for x in o if x]


def generar() -> str:
    g = _terreno()
    csv_terreno = ",".join(str(g[y][x]) for y in range(MH) for x in range(MW))
    ceros = ",".join(["0"] * (MW * MH))
    capa = lambda i, n, d: (  # noqa: E731
        f' <layer id="{i}" name="{n}" width="{MW}" height="{MH}">\n'
        f'  <data encoding="csv">\n{d}\n</data>\n </layer>'
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" \
renderorder="right-down" width="{MW}" height="{MH}" tilewidth="{TS}" \
tileheight="{TS}" infinite="0" nextlayerid="20" nextobjectid="900">
 <properties>
  <property name="schema_version" value="1"/>
  <property name="stage_id" value="stage4_1"/>
  <property name="stage_name" value="4-1  EL CEMENTERIO SAGRADO"/>
  <property name="author" value="Equipo docente — Legacy of Infest"/>
  <property name="bgm_track" value="bgm_final_approach"/>
  <property name="background_zone" value="final"/>
  <property name="climate" value="clear"/>
  <property name="ambient_fx" value="ash"/>
  <property name="ambient_fx_rate" type="float" value="5"/>
  <property name="start_hour" type="float" value="18"/>
  <property name="day_length" type="float" value="1400"/>
  <property name="time_limit" type="int" value="0"/>
  <property name="zone" type="int" value="4"/>
  <property name="ambient_light" type="float" value="0.60"/>
  <property name="bloom" type="float" value="0.30"/>
  <property name="vignette" type="float" value="0.45"/>
 </properties>
 <tileset firstgid="1" name="tileset_stage0" tilewidth="{TS}" tileheight="{TS}" \
tilecount="{TS_TOTAL}" columns="{TS_COLUMNAS}">
  <image source="{TILESET}" width="{TS_IMAGEN_PX}" height="{TS_IMAGEN_PX}"/>
 </tileset>
{capa(1, "BG_Far", ceros)}
{capa(2, "BG_Mid", ceros)}
{capa(3, "BG_Near", ceros)}
{capa(4, "Terrain", csv_terreno)}
{capa(5, "Terrain_Detail", ceros)}
 <objectgroup id="7" name="Collision">
{chr(10).join(_colisiones())}
 </objectgroup>
 <objectgroup id="8" name="Objects">
{chr(10).join(_objetos())}
 </objectgroup>
{capa(9, "FG_Overlay", ceros)}
</map>
"""


def main() -> None:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(generar(), encoding="utf-8")
    print(f"escrito {DESTINO.relative_to(PROJECT_ROOT)} "
          f"({MW}×{MH} baldosas, 6 secciones, {len(checkpoints())} checkpoints, "
          f"{len(ARBOLES_FASE4)} tocones, {len(TUMBAS_FASE5)} tumbas, "
          f"{len(grietas_de_pisada())} grietas, 1 loma, "
          f"0 enemigos, 0 fosos, 0 zonas de daño)")


if __name__ == "__main__":
    main()
