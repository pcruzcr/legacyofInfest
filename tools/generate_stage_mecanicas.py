#!/usr/bin/env python3
"""
Genera `assets/maps/stage_mecanicas/stage_mecanicas.tmx`: el escenario que
enseña las once mecánicas nuevas de la fase 5.

F5.13 — la tercera deuda de la fase 5
======================================
Las once mecánicas estaban en el motor, probadas y documentadas, y **ninguna
entrega las usaba**. Es la misma forma de fallo que este proyecto lleva un mes
cazando —la iluminación que no iluminaba, el nado inalcanzable— sólo que un
paso más allá: aquí el camino existe y no hay nadie andándolo.

Un estudiante no adopta una mecánica leyendo su tabla de propiedades. La adopta
viéndola funcionar en un mapa que puede abrir en Tiled, mirar cómo está hecho, y
copiar. Este fichero genera ese mapa.

Por qué se genera con código y no se dibuja en Tiled
-----------------------------------------------------
Igual que `generate_stage0_tmx.py`: un TMX escrito a mano son ocho mil números
en CSV que nadie puede revisar en un *pull request*. Generado, el diff es de
diez líneas de Python y se lee lo que cambió de verdad.

Estructura: siete salas, una mecánica por sala
-----------------------------------------------
Cada sala introduce **una** cosa, en un sitio donde equivocarse no mata, y la
siguiente la combina con la anterior. Es la lección de Mario 1-1 del dossier:
enseñar por colocación, sin texto.

    Sala 1   viento                     ← empuja mientras saltas
    Sala 2   cinta transportadora       ← el suelo se mueve
    Sala 3   plataformas móviles        ← y te llevan encima
    Sala 4   bloques rítmicos           ← aparecen a compás
    Sala 5   láseres con desfase        ← patrón, no muro
    Sala 6   agua y oxígeno             ← el reloj bajo el agua
    Sala 7   guardia y acosador         ← sigilo
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESTINO = PROJECT_ROOT / "assets" / "maps" / "stage_mecanicas" / "stage_mecanicas.tmx"
TILESET = "../../tilesets/tileset_stage0.png"

TS = 16
MW, MH = 220, 24          # 3520 × 384 px
SUELO_Y = 20              # fila del suelo
SALA = 30                 # ancho de cada sala en baldosas

# ── Baldosas ────────────────────────────────────────────────────────────────
# AUD-115: aquí también se declaraba el tileset como `tilecount="64"
# columns="8"` con una imagen de 128 × 128 px. `tileset_stage0.png` mide
# **1024 × 1024** y tiene 4096 baldosas en 64 columnas, así que este mapa
# pintaba las tres primeras baldosas de la hoja —casi negras— en vez del
# corredor de piedra. El mismo error que en `generate_stage0_tmx.py`, cometido
# el mismo día y por la misma razón: inventé la cabecera del tileset en vez de
# copiar la del mapa que ya funcionaba.
TS_COLUMNAS = 64
TS_TOTAL = 4096
TS_IMAGEN_PX = 1024

VACIO = 0
SUELO = 409               # la fila que se pisa
MURO = 153                # columna de cierre
PLATAFORMA = 666          # repisa atravesable
RELLENO = 665             # relleno bajo la superficie


def _terreno() -> list[list[int]]:
    """La geometría del mapa, sala por sala."""
    g = [[VACIO] * MW for _ in range(MH)]

    # Suelo continuo, salvo donde una sala lo quita a propósito.
    for y in range(SUELO_Y, MH):
        for x in range(MW):
            g[y][x] = SUELO

    # Sala 4 — hueco que sólo se cruza por los bloques rítmicos.
    for y in range(SUELO_Y, MH):
        for x in range(3 * SALA + 8, 3 * SALA + 22):
            g[y][x] = VACIO

    # Sala 6 — depresión que contiene el agua.
    for y in range(SUELO_Y - 4, MH):
        for x in range(5 * SALA + 4, 5 * SALA + 26):
            g[y][x] = VACIO
    for x in range(5 * SALA + 4, 5 * SALA + 26):
        g[MH - 1][x] = SUELO

    # Techo en las salas cerradas, para que el viento y los láseres se lean
    # como pasillos y no como campo abierto.
    for x in range(0, SALA):
        g[4][x] = MURO
    for x in range(4 * SALA, 5 * SALA):
        g[4][x] = MURO

    # Repisas para descansar entre salas: son las «válvulas de escape» del
    # dossier, y sin ellas siete mecánicas seguidas se leen como una sola
    # cuesta arriba.
    for sala in range(1, 7):
        for x in range(sala * SALA - 4, sala * SALA + 4):
            g[SUELO_Y - 5][x] = PLATAFORMA
    return g


def _objetos() -> list[str]:
    """Los objetos del TMX, uno por mecánica, con sus propiedades."""
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
                    cuerpo += f'\n    <property name="{k}" value="{v}"/>'
            cuerpo += "\n   </properties>"
        cuerpo += "\n  </object>"
        o.append(cuerpo)

    suelo_px = SUELO_Y * TS

    obj("PlayerSpawn", 2 * TS, suelo_px - 48, 16, 32)

    # ── Sala 1: viento ────────────────────────────────────────
    # Sopla a rachas y no en continuo: constante se convierte en «el nivel va
    # más despacio»; a rachas hay que elegir cuándo saltar.
    obj("MessageTrigger_Once", 3 * TS, suelo_px - 64, 48, 48,
        text="El viento empuja. Salta cuando amaine.")
    obj("WindZone", 6 * TS, 5 * TS, 18 * TS, 15 * TS,
        fuerza_x=260.0, fuerza_y=0.0, periodo=3.0)
    obj("Checkpoint", 26 * TS, suelo_px - 32, 16, 32, checkpoint_id=1)

    # ── Sala 2: cinta transportadora ──────────────────────────
    obj("MessageTrigger_Once", (SALA + 2) * TS, suelo_px - 64, 48, 48,
        text="El suelo se mueve. Correr a favor es mas rapido.")
    obj("Conveyor", (SALA + 6) * TS, suelo_px - TS, 16 * TS, TS, arrastre=-70.0)
    obj("Checkpoint", (2 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=2)

    # ── Sala 3: plataformas móviles ───────────────────────────
    obj("MessageTrigger_Once", (2 * SALA + 2) * TS, suelo_px - 64, 48, 48,
        text="Sube. La plataforma te lleva.")
    obj("MovingPlatform", (2 * SALA + 8) * TS, suelo_px - 3 * TS, 3 * TS, 8,
        destino_dx=0.0, destino_dy=-6 * TS, velocidad=45.0, espera=0.8)
    obj("MovingPlatform", (2 * SALA + 16) * TS, suelo_px - 8 * TS, 3 * TS, 8,
        destino_dx=7 * TS, destino_dy=0.0, velocidad=55.0, espera=0.5)
    obj("Checkpoint", (3 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=3)

    # ── Sala 4: bloques rítmicos sobre el hueco ───────────────
    obj("MessageTrigger_Once", (3 * SALA + 2) * TS, suelo_px - 64, 48, 48,
        text="Aparecen a compas. Cuenta antes de saltar.")
    # AUD-137: los dos primeros siguen contando segundos —para que el mapa
    # siga sirviendo de ejemplo del modo de siempre— y los dos ultimos van
    # con la musica. Los patrones estan desplazados entre si: «x.x.» y
    # «.x.x» se turnan, que es lo que obliga a saltar a tiempo.
    patrones = ["", "", "x.x.", ".x.x"]
    for i in range(4):
        obj("RhythmBlock", (3 * SALA + 9 + i * 3) * TS, suelo_px - 2 * TS,
            2 * TS, TS, visible_seg=1.6, oculto_seg=1.2, desfase=i * 0.7,
            patron=patrones[i])
    obj("DeathPit", (3 * SALA + 8) * TS, (MH - 1) * TS, 14 * TS, TS)
    obj("Checkpoint", (4 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=4)

    # ── Sala 5: láseres en cascada ────────────────────────────
    obj("MessageTrigger_Once", (4 * SALA + 2) * TS, suelo_px - 64, 48, 48,
        text="Se encienden en cascada. Hay un hueco: buscalo.")
    for i in range(5):
        obj("LaserZone", (4 * SALA + 8 + i * 4) * TS, 5 * TS, 8, 15 * TS,
            dano=99.0, encendido=1.1, apagado=2.2, desfase=i * 0.66)
    obj("SinkingPlatform", (4 * SALA + 24) * TS, suelo_px - 4 * TS, 3 * TS, 8,
        retraso=0.5, reaparece_en=2.5)
    obj("Checkpoint", (5 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=5)

    # ── Sala 6: agua y oxígeno ────────────────────────────────
    obj("MessageTrigger_Once", (5 * SALA + 1) * TS, suelo_px - 64, 48, 48,
        text="Bajo el agua se acaba el aire. Sal a respirar.")
    obj("WaterZone", (5 * SALA + 4) * TS, (SUELO_Y - 4) * TS, 22 * TS, 8 * TS,
        corriente_x=25.0, corriente_y=0.0)
    obj("Checkpoint", (6 * SALA - 3) * TS, suelo_px - 32, 16, 32, checkpoint_id=6)

    # ── Sala 7: sigilo ────────────────────────────────────────
    obj("MessageTrigger_Once", (6 * SALA + 2) * TS, suelo_px - 64, 48, 48,
        text="Te estan mirando. Y algo te sigue.")
    obj("Guard", (6 * SALA + 12) * TS, suelo_px - 2 * TS, TS, 2 * TS,
        mira_x=-1.0, mira_y=0.0, alcance=180.0, semiangulo=28.0,
        barrido=35.0, velocidad_barrido=40.0)
    obj("Guard", (6 * SALA + 22) * TS, suelo_px - 2 * TS, TS, 2 * TS,
        mira_x=1.0, mira_y=0.0, alcance=180.0, semiangulo=28.0)
    obj("Stalker", (6 * SALA + 4) * TS, suelo_px - 2 * TS, TS, 2 * TS,
        velocidad=42.0, distancia_retirada=420.0, reaparicion=7.0)

    # Salida
    obj("NextTrigger", (MW - 4) * TS, suelo_px - 3 * TS, 2 * TS, 3 * TS)

    # Un par de enemigos normales, para que el escenario no sea sólo un museo.
    obj("Walker", (SALA + 20) * TS, suelo_px - 28, 24, 28)
    obj("FlyingBoa", (2 * SALA + 12) * TS, suelo_px - 6 * TS, 20, 14)
    return o


def _colisiones() -> list[str]:
    """La capa `Collision`: el suelo y los muros, como rectángulos."""
    r: list[str] = []
    ident = [1]

    def solido(x: int, y: int, w: int, h: int, tipo: str = "Solid") -> None:
        ident[0] += 1
        r.append(
            f'  <object id="{ident[0]}" type="{tipo}" x="{x}" y="{y}"'
            f' width="{w}" height="{h}"/>',
        )

    suelo_px = SUELO_Y * TS
    # Tramos de suelo, saltando los dos huecos.
    solido(0, suelo_px, (3 * SALA + 8) * TS, (MH - SUELO_Y) * TS)
    solido((3 * SALA + 22) * TS, suelo_px, (2 * SALA - 18) * TS, (MH - SUELO_Y) * TS)
    solido((5 * SALA + 26) * TS, suelo_px, (MW - 5 * SALA - 26) * TS,
           (MH - SUELO_Y) * TS)
    # Fondo de la piscina.
    solido((5 * SALA + 4) * TS, (MH - 1) * TS, 22 * TS, TS)
    # Muros laterales.
    solido(-TS, 0, TS, MH * TS)
    solido(MW * TS, 0, TS, MH * TS)
    # Repisas de descanso, atravesables desde abajo.
    for sala in range(1, 7):
        solido((sala * SALA - 4) * TS, (SUELO_Y - 5) * TS, 8 * TS, 8, "Platform")
    return r


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
  <property name="stage_id" value="stage_mecanicas"/>
  <property name="stage_name" value="LABORATORIO DE MECANICAS"/>
  <property name="author" value="Equipo docente — Legacy of Infest"/>
  <property name="bgm_track" value="bgm_stage0"/>
  <!-- AUD-137 (F6): el compas del escenario. Con `bpm`, los bloques que
       declaran `patron` dejan de contar segundos y siguen a la musica. -->
  <property name="bpm" type="float" value="120"/>
  <property name="compas" type="int" value="4"/>
  <property name="background_zone" value="stage0"/>
  <property name="climate" value="clear"/>
  <property name="time_limit" value="0"/>
  <property name="zone" type="int" value="0"/>
  <property name="ambient_light" type="float" value="0.78"/>
  <property name="bloom" type="float" value="0.15"/>
  <property name="vignette" type="float" value="0.25"/>
  <property name="ambient_fx" value="dust"/>
  <property name="ambient_fx_rate" type="float" value="8"/>
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
    print(f"escrito {DESTINO.relative_to(PROJECT_ROOT)} ({MW}×{MH} baldosas)")


if __name__ == "__main__":
    main()
