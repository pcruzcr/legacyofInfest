#!/usr/bin/env python3
"""
Genera `assets/maps/stage4_1/stage4_1.tmx` — El Cementerio Sagrado.

El nivel, en una frase
=======================
Un **descenso** de 288 filas sin un solo enemigo y sin una sola trampa
mortal, donde el cementerio cambia de piel —color, blanco y negro, grises,
vintage, noche, color y verde— mientras los espíritus de Venado, Rey
Terciopelo y Gavilán ascienden uno a uno. La ficha
(`docs/niveles/13_STAGE_4_1.md`) fija las reglas; el diseño
(`15_DISENO_4_1_EL_CEMENTERIO.md`) fija los números de cada una de las seis
fases.

Qué hereda del diseño anterior, y qué no (AUD-462)
----------------------------------------------------
Se hereda la forma de pozo, las repisas en zigzag y la regla de superficies
visibles (ver `trazado.py`). Se retiran los braseros-progreso, las lápidas
con nombres, las losas rompibles/rítmicas/fantasma y las huellas de la
visión espectral: eran mecánica del diseño de La Cegua que este guion no
pide. En su lugar: musgo y lodo juntos en la Fase 2, un slope en la Fase 3,
un silencio con camera shake en la Fase 4 (código de escena, no geometría),
un ciclo de luna en la Fase 5, y grietas que se iluminan al paso en la Fase 6.

Aquí sólo se coloca **lo que es geometría**; la gradación de color, el ciclo
de luna, el shake y las siluetas de los espíritus los mueve la escena
(`stage4_1.py`). Las columnas y filas de cada cosa viven en
`src/stages/stage4_1/trazado.py`, que es también de donde las lee la escena.

Por qué se genera con código
-----------------------------
Igual que `generate_stage0_tmx.py`: un TMX a mano son miles de números en CSV
que nadie puede revisar en un *pull request*. Generado, el diff es de diez
líneas de Python y se lee lo que cambió.

La regla de oro: **cero enemigos**
-----------------------------------
No se coloca ni uno. `tests/test_stage4_1.py` lo comprueba cargando el mapa y
contando `entity_list`, no leyendo el XML.
"""
from __future__ import annotations

import sys
from pathlib import Path

# AUD-177: imprime `→` y la consola de Windows usa cp1252, que no lo tiene.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.stages.stage4_1.trazado import (  # noqa: E402
    ALTO_FASE,
    ARRASTRE_DEL_MUSGO,
    FRENO_DEL_LODO,
    GROSOR_REPISA,
    MH,
    MURO_ANCHO,
    MW,
    SUELO_FINAL,
    TS,
    checkpoints,
    fase_de_la_fila,
    grietas_de_pisada,
    loma,
    repisas,
    superficies,
)

DESTINO = PROJECT_ROOT / "assets" / "maps" / "stage4_1" / "stage4_1.tmx"

# La misma hoja del diseño anterior (AUD-237) — el cementerio sigue pisando su
# propia piedra, y el rediseño no toca el arte del terreno, sólo el guion.
TILESET = "../../tilesets/tileset_cemetery.png"

TS_COLUMNAS = 8
TS_TOTAL = 64
TS_IMAGEN_PX = 128

# Los GID son `índice + 1` sobre `CEM_ORDEN` de `tools/generate_all_assets.py`
# — un contrato que defiende `tests/test_stage4_1.py`.
VACIO = 0
PIEDRA = 2                # la losa que se pisa
RELLENO = 3               # tierra bajo la superficie
MURO = 4                  # piedra de cierre del pozo
MUSGO = 5                 # losa con musgo y matas — arrastra
MUSGO_RELLENO = 6
LODO = 7                  # losa con barro y raíces — frena
LODO_RELLENO = 8

BALDOSAS = {
    "piedra": (PIEDRA, RELLENO),
    "musgo": (MUSGO, MUSGO_RELLENO),
    "lodo": (LODO, LODO_RELLENO),
}


def _terreno() -> list[list[int]]:
    """La geometría del pozo, repisa a repisa."""
    g = [[VACIO] * MW for _ in range(MH)]

    for y in range(MH):
        for x in range(MURO_ANCHO):
            g[y][x] = MURO
            g[y][MW - 1 - x] = MURO

    for x in range(MURO_ANCHO, MW - MURO_ANCHO):
        g[0][x] = MURO

    for x0, ancho, fila, material in superficies():
        arriba, abajo = BALDOSAS[material]
        for x in range(x0, x0 + ancho):
            g[fila][x] = arriba
            for d in range(1, GROSOR_REPISA):
                g[fila + d][x] = abajo

    for y in range(SUELO_FINAL, MH):
        for x in range(MURO_ANCHO, MW - MURO_ANCHO):
            g[y][x] = PIEDRA if y == SUELO_FINAL else RELLENO

    return g


def _colisiones() -> list[str]:
    """La capa `Collision`: los muros, las repisas y el suelo del umbral."""
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

    # Las repisas son `Solid` y no `Platform` a propósito: se cae desde
    # arriba a velocidad sobre una repisa de 16 px de grosor, y un
    # colisionador de un solo sentido se atravesaría por velocidad.
    for x0, ancho, fila in repisas():
        solido(x0 * TS, fila * TS, ancho * TS, GROSOR_REPISA * TS)

    solido(MURO_ANCHO * TS, SUELO_FINAL * TS,
           (MW - 2 * MURO_ANCHO) * TS, (MH - SUELO_FINAL) * TS)

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

    lista = repisas()
    primera = lista[0]

    obj("PlayerSpawn", (primera[0] + 3) * TS, (primera[2] - 3) * TS, 16, 32)

    # ── Un mensaje al entrar en cada fase ──────────────────────
    textos = {
        1: "El Cementerio Sagrado. Los muertos de Tilaran, y algo mas.",
        2: "El Venado testifica. El musgo tira, el lodo frena.",
        3: "El Rey Terciopelo se enrosca entre las lapidas. Sube la loma.",
        4: "El Gavilan vuela sobre el bosque cortado. Escucha el silencio.",
        5: "La Planicie de los Muertos. Solo la luna alumbra.",
        6: "El Camino hacia Paburu. Cada paso enciende una grieta.",
    }
    vistos: set[int] = set()
    for x0, ancho, fila in lista:
        fase = fase_de_la_fila(fila)
        if fase in vistos:
            continue
        vistos.add(fase)
        obj("MessageTrigger_Once", (x0 + ancho // 2) * TS, (fila - 3) * TS,
            48, 48, text=textos[fase])

    # ── Los puntos de reaparición ─────────────────────────────
    for i, (cx, fila) in enumerate(checkpoints(), start=1):
        obj("Checkpoint", cx * TS, (fila - 2) * TS, 16, 32, checkpoint_id=i)

    # ── Las superficies que mueven al jugador (Fase 2) ────────
    for x0, ancho, fila, material in superficies():
        if material == "musgo":
            sentido = 1.0 if x0 == MURO_ANCHO else -1.0
            obj("FrictionZone", x0 * TS, (fila - 2) * TS, ancho * TS, 2 * TS,
                arrastre=ARRASTRE_DEL_MUSGO * sentido)
        elif material == "lodo":
            obj("FrictionZone", x0 * TS, (fila - 2) * TS, ancho * TS, 2 * TS,
                multiplicador=FRENO_DEL_LODO)

    # ── Fase 3 — la loma: un Slope de verdad ──────────────────
    #
    # Ocupa sólo parte del hueco de su repisa; el resto sigue libre para
    # caer. `sube="derecha"` — el borde derecho del rectángulo es el alto de
    # la hipotenuse.
    lx, lfila, lancho, lalto, lsube = loma()
    obj("Slope", lx * TS, (lfila - lalto) * TS, lancho * TS, lalto * TS,
        sube=lsube)

    # ── Fase 3 — el viento del guion («carácter ventoso» de Tilarán) ──
    obj("WindZone", MURO_ANCHO * TS, 2 * ALTO_FASE * TS,
        (MW - 2 * MURO_ANCHO) * TS, ALTO_FASE * TS,
        fuerza_x=-60.0, fuerza_y=0.0, periodo=3.2)

    # ── Fase 6 — las grietas, apagadas: las enciende la escena ────
    for cx, fila in grietas_de_pisada():
        obj("Light", cx * TS, (fila - 2) * TS, TS, TS,
            radius=70.0, color="#7CFFA0", intensity=0.0)

    # ── El umbral ──────────────────────────────────────────────
    obj("MessageTrigger_Once", (MW // 2 - 6) * TS, (SUELO_FINAL - 5) * TS,
        2 * TS, 5 * TS, text="Paburu despierta.")
    obj("NextTrigger", (MW - MURO_ANCHO - 4) * TS, (SUELO_FINAL - 3) * TS,
        2 * TS, 3 * TS)

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
  <!-- El clima ARRANCA en calma (Fase 1) y lo cambia la escena por fase. -->
  <property name="climate" value="clear"/>
  <property name="ambient_fx" value="ash"/>
  <property name="ambient_fx_rate" type="float" value="5"/>
  <property name="start_hour" type="float" value="18"/>
  <property name="day_length" type="float" value="1200"/>
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
    musgo = sum(1 for *_, m in superficies() if m == "musgo")
    lodo = sum(1 for *_, m in superficies() if m == "lodo")
    print(f"escrito {DESTINO.relative_to(PROJECT_ROOT)} "
          f"({MW}×{MH} baldosas, {len(repisas())} repisas, "
          f"{len(checkpoints())} checkpoints, {musgo} de musgo, {lodo} de lodo, "
          f"1 loma, {len(grietas_de_pisada())} grietas de la Fase 6, "
          f"0 enemigos, 0 fosos, 0 zonas de daño)")


if __name__ == "__main__":
    main()
