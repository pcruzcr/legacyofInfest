#!/usr/bin/env python3
"""AUD-814 — Genera desde cero assets/maps/stage4_1/stage4_1.tmx.

Mapa nuevo del Stage 4.1 «La Entrada al Cementerio Sagrado»: 960x40
baldosas (15360x640 px), seis secciones de 160 columnas, suelo en la fila
32, sin fosos. Todo sale de src/stages/stage4_1/trazado.py y fases.py: si
el diseño cambia allí, el mapa cambia aquí.

Uso:
    python tools/generar_stage41_tmx.py
"""
from __future__ import annotations

import os
import random
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stages.stage4_1 import trazado

TS = trazado.TS
MW, MH = trazado.MW, trazado.MH
DESTINO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "assets", "maps", "stage4_1", "stage4_1.tmx")

TILESETS = [(f"tileset_stage41_f{f}",
             f"../../tilesets/tileset_stage41_f{f}.png",
             (f - 1) * 256 + 1) for f in range(1, 7)]

# Índices locales (ver tools/generar_stage41_activos.py).
SUP, RELLENO, SUP_VAR, REL_VAR = 0, 1, 2, 3
DEC_A, DEC_B, DEC_C, DEC_D, DEC_E, DEC_F = 4, 5, 6, 7, 12, 13
TRANS_A, TRANS_B = 8, 9
BG_FAR, BG_MID, BG_NEAR, FG_OSCURO = 16, 20, 24, 32

GUIÓN_INTRO = (
    "fundido entra 1.5\n"
    "texto Voces antiguas: Paburu sueña... y su sueño nos llama por el nombre.\n"
    "esperar 2.5\n"
    "texto Jhon: Este cementerio... lo he visto en sueños.\n"
    "esperar 2.0\n"
    "texto Jin: Entonces no venimos por primera vez. Los espíritus nos trajeron.\n"
    "esperar 1.0\n"
    "fundido sale 1.0\n"
)
GUIÓN_MIRADOR = (
    "fundido entra 0.3\n"
    "camara 14200 300 2.0\n"
    "esperar 2.5\n"
    "texto Jhon: Ahí está. Después de los muertos, la luz.\n"
    "esperar 2.0\n"
    "camara 15000 400 1.5\n"
    "esperar 0.4\n"
    "fundido sale 0.4\n"
)


def _gid(fase: int, local: int) -> int:
    return (fase - 1) * 256 + 1 + local


def _fase_de(col: int) -> int:
    return trazado.fase_de_la_columna(col)


def _en_transicion(col: int) -> bool:
    f = _fase_de(col)
    return f < 6 and col >= f * trazado.ANCHO_SECCION - 12


def _capa_terreno(rng: random.Random) -> list[int]:
    suelo = trazado.perfil_del_suelo()
    datos = [0] * (MW * MH)
    for col in range(MW):
        fase = _fase_de(col)
        fs = suelo[col]
        lodo = fase == 2 and 240 <= col <= 279
        for fila in range(fs, MH):
            if fila == fs:
                if _en_transicion(col):
                    local = TRANS_A if rng.random() < 0.7 else TRANS_B
                elif lodo:
                    local = SUP_VAR
                elif rng.random() < 0.12:
                    local = SUP_VAR if fase != 6 else SUP
                else:
                    local = SUP
            else:
                local = RELLENO if rng.random() < 0.85 else REL_VAR
            datos[fila * MW + col] = _gid(fase, local)
    return datos


def _capa_detalle(rng: random.Random) -> list[int]:
    suelo = trazado.perfil_del_suelo()
    datos = [0] * (MW * MH)
    # AUD-816: composición por grupos (denso, vacío, dominante, camino),
    # no una pieza cada 7 columnas. F1/F5 con tumbas variadas (14/15).
    decor = {1: (DEC_A, DEC_B, DEC_C, DEC_D, DEC_E, DEC_F, 14, 15),
             2: (DEC_A, DEC_B, DEC_C, DEC_D, DEC_E, DEC_F),
             3: (DEC_A, DEC_B, DEC_C, DEC_D, DEC_E, DEC_F),
             4: (DEC_A, DEC_B, DEC_C, DEC_D, DEC_E, DEC_F),
             5: (DEC_A, DEC_B, DEC_C, DEC_D, DEC_E, DEC_F, 14, 15),
             6: (DEC_A, DEC_B, DEC_C, DEC_D, DEC_E, DEC_F)}
    for col in range(MW):
        fase = _fase_de(col)
        # F2 bosque cerrado: grupos más seguidos que en el resto.
        seg, hueco = (4, 10) if fase == 2 else (6, 18)
        # Grupos deterministas por sección: denso, vacío, dominante.
        pos = (col - (fase - 1) * trazado.ANCHO_SECCION) % (seg + hueco)
        if pos >= seg:
            continue
        if _en_transicion(col) and rng.random() < 0.5:
            continue
        fs = suelo[col]
        fila = fs - 1
        local = rng.choice(decor[fase])
        datos[fila * MW + col] = _gid(fase, local)
    # Lápidas del easter egg sobre el detalle de la F1.
    for col in (trazado.COLUMNA_LAPIDA_CAMPANERO, trazado.COLUMNA_LAPIDA_MAESTRA):
        fs = suelo[col]
        datos[(fs - 1) * MW + col] = _gid(1, DEC_A)
    return datos


def _capa_motivos(rng: random.Random, base: int,
                  filas: tuple[int, ...]) -> list[int]:
    """Siluetas por grupos con huecos, nunca en línea continua.

    AUD-816: las bandas uniformes de puntos eran la señal de "debug".
    Cada grupo es una secuencia l+c..+r a una fila propia del grupo, con
    anchos y separaciones sorteadas por sección.
    """
    datos = [0] * (MW * MH)
    for fase in range(1, 7):
        c0, c1 = (fase - 1) * trazado.ANCHO_SECCION, fase * trazado.ANCHO_SECCION
        col = c0 + rng.randrange(4, 12)
        while col < c1 - 8:
            ancho = rng.randrange(3, 8)
            fila = rng.choice(filas)
            for k in range(ancho):
                if col + k >= c1:
                    break
                if k == 0:
                    local = base
                elif k == ancho - 1:
                    local = base + 2
                else:
                    local = base + 1
                datos[fila * MW + col + k] = _gid(fase, local)
            col += ancho + rng.randrange(6, 20)
    return datos


def _capa_frente(rng: random.Random) -> list[int]:
    """Frente irregular: grupos colgantes arriba y hierba alta abajo, con
    huecos. Reutiliza los motivos cercanos (25-27) de cada familia."""
    datos = [0] * (MW * MH)
    for fase in range(1, 7):
        c0 = (fase - 1) * trazado.ANCHO_SECCION
        c1 = fase * trazado.ANCHO_SECCION
        for filas in ((0, 1, 2), (37, 38, 39)):
            col = c0 + rng.randrange(2, 10)
            while col < c1 - 8:
                ancho = rng.randrange(4, 9)
                fila = rng.choice(filas)
                for k in range(ancho):
                    if col + k >= c1:
                        break
                    local = 25 if k == 0 else (27 if k == ancho - 1 else 26)
                    datos[fila * MW + col + k] = _gid(fase, local)
                col += ancho + rng.randrange(8, 26)
    return datos


def _capa(ident: int, nombre: str, datos: list[int]) -> ET.Element:
    capa = ET.Element("layer", {"id": str(ident), "name": nombre,
                                "width": str(MW), "height": str(MH)})
    data = ET.SubElement(capa, "data", {"encoding": "csv"})
    filas = [",".join(str(datos[y * MW + x]) for x in range(MW)) for y in range(MH)]
    data.text = "\n" + ",\n".join(filas) + "\n"
    return capa


def _obj(grupo: ET.Element, oid: int, tipo: str, nombre: str,
         x: float, y: float, w: float, h: float, props: dict | None = None) -> None:
    o = ET.SubElement(grupo, "object", {
        "id": str(oid), "name": nombre, "type": tipo,
        "x": str(x), "y": str(y), "width": str(w), "height": str(h)})
    if props:
        pp = ET.SubElement(o, "properties")
        for k, v in props.items():
            ET.SubElement(pp, "property", {"name": k, "value": str(v)})


def _tramos_llanos() -> list[tuple[int, int]]:
    """Tramos de suelo llano (columnas) entre elevaciones y muros."""
    cortes = sorted({trazado.MURO_ANCHO, MW - trazado.MURO_ANCHO}
                    | {e[0] for e in trazado.ELEVACIONES}
                    | {e[0] + e[1] + e[2] + e[3] for e in trazado.ELEVACIONES})
    return [(cortes[i], cortes[i + 1] - 1) for i in range(len(cortes) - 1)]


def construir() -> ET.Element:
    rng = random.Random(812)
    mapa = ET.Element("map", {
        "version": "1.10", "tiledversion": "1.10.2", "orientation": "orthogonal",
        "renderorder": "right-down", "width": str(MW), "height": str(MH),
        "tilewidth": str(TS), "tileheight": str(TS), "infinite": "0",
        "nextlayerid": "20", "nextobjectid": "900"})
    props = ET.SubElement(mapa, "properties")
    for k, v in (("schema_version", 1), ("stage_id", "stage4_1"),
                 ("stage_name", "4-1  LA ENTRADA AL CEMENTERIO SAGRADO"),
                 ("author", "Equipo docente — Legacy of InFest"),
                 ("bgm_track", "mus_stage41_f1"),
                 # AUD-814: sin cielo=true el motor cree que es interior
                 # (_es_indoor) y anula lluvia/tormenta/niebla del VFX.
                 ("cielo", "true"),
                 ("background_zone", ""), ("climate", "clear"),
                 ("ambient_fx", "dust"), ("ambient_fx_rate", 6),
                 ("start_hour", 10), ("day_length", 3600), ("time_limit", 0),
                 ("zone", 4), ("ambient_light", 0.80),
                 ("bloom", 0.30), ("vignette", 0.40)):
        ET.SubElement(props, "property", {"name": k, "value": str(v)})
    for nombre, imagen, firstgid in TILESETS:
        ts = ET.SubElement(mapa, "tileset", {
            "firstgid": str(firstgid), "name": nombre, "tilewidth": str(TS),
            "tileheight": str(TS), "tilecount": "256", "columns": "16"})
        ET.SubElement(ts, "image", {"source": imagen, "width": "256", "height": "256"})

    mapa.append(_capa(1, "BG_Far", _capa_motivos(rng, 17, (6, 7, 8, 9, 10, 11))))
    mapa.append(_capa(2, "BG_Mid", _capa_motivos(rng, 21, (14, 15, 16, 17, 18, 19))))
    mapa.append(_capa(3, "BG_Near", _capa_motivos(rng, 25, (22, 23, 24, 25, 26))))
    mapa.append(_capa(4, "Terrain", _capa_terreno(rng)))
    mapa.append(_capa(5, "Terrain_Detail", _capa_detalle(rng)))

    colision = ET.SubElement(mapa, "objectgroup", {"id": "6", "name": "Collision"})
    objetos = ET.SubElement(mapa, "objectgroup", {"id": "7", "name": "Objects"})
    oid = 100
    y_suelo = trazado.FILA_SUELO * TS
    _obj(colision, 2, "Solid", "muro_oeste", 0, 0, 32, MH * TS)
    _obj(colision, 3, "Solid", "muro_este", (MW - 2) * TS, 0, 32, MH * TS)
    cid = 4
    for c0, c1 in _tramos_llanos():
        _obj(colision, cid, "Solid", f"suelo_{c0}_{c1}",
             c0 * TS, y_suelo, (c1 - c0 + 1) * TS, (MH - trazado.FILA_SUELO) * TS)
        cid += 1
    # Pendientes: el rectángulo es el triángulo entero (ver Slope en el motor).
    for inicio, sub, cima, baj, fila_cima in trazado.ELEVACIONES:
        h = (trazado.FILA_SUELO - fila_cima) * TS
        apice = (inicio + sub + cima) * TS
        _obj(objetos, oid, "Slope", f"rampa_subida_{inicio}",
             inicio * TS, y_suelo - h, sub * TS, h, {"sube": "derecha"})
        oid += 1
        _obj(objetos, oid, "Slope", f"rampa_bajada_{inicio}",
             apice, y_suelo - h, baj * TS, h,
             {"sube": "izquierda"})
        oid += 1
        # AUD-814 (patrón AUD-477): la cima llana es otro Slope, plano.
        # Sin ella, la cara empinada de la bajada (un muro por diseño,
        # `resolver_lateral`) clava al jugador justo antes del vértice:
        # el cuerpo toca la cara con los pies ya bajo su borde. Sobre la
        # cima plana los pies van a la altura del borde y la cara se salta.
        _obj(objetos, oid, "Slope", f"cima_llana_{inicio}",
             apice - TS, fila_cima * TS - 1, 2 * TS, 1,
             {"sube": "derecha"})
        oid += 1
        # AUD-814: base de seguridad bajo el tramo. Sin ella, quien salte
        # fuera de la rampa cae al vacío (no hay suelo sólido en el vano y
        # el nivel no tiene fosos por diseño). La cara superior está a
        # nivel del suelo llano, así que no interrumpe la subida.
        fin = inicio + sub + cima + baj
        _obj(colision, cid, "Solid", f"base_{inicio}",
             inicio * TS, y_suelo, (fin - inicio) * TS,
             (MH - trazado.FILA_SUELO) * TS)
        cid += 1

    _obj(objetos, oid, "PlayerSpawn", "spawn_jhon_jin",
         trazado.COLUMNA_SPAWN * TS, y_suelo - 32, 16, 32)
    oid += 1
    _obj(objetos, oid, "Cutscene", "intro_cementerio",
         trazado.COLUMNA_SPAWN * TS, y_suelo - 32, 0, 0,
         {"guion": GUIÓN_INTRO, "bloquea": "true", "saltable": "true",
          "una_vez": "true"})
    oid += 1
    _obj(objetos, oid, "Cutscene", "mirador_paburu",
         trazado.COLUMNA_MIRADOR_FINAL * TS, y_suelo - 64, 48, 80,
         {"guion": GUIÓN_MIRADOR, "bloquea": "true", "saltable": "true",
          "una_vez": "true"})
    oid += 1
    for i, col in enumerate(trazado.COLUMNAS_CHECKPOINT, start=1):
        _obj(objetos, oid, "Checkpoint", f"checkpoint_{i}",
             col * TS, y_suelo - 32, 16, 32, {"checkpoint_id": i})
        oid += 1
    # Easter egg: dos lápidas cuidadas en la F1.
    _obj(objetos, oid, "MessageTrigger_Once", "lapida_campanero",
         trazado.COLUMNA_LAPIDA_CAMPANERO * TS, y_suelo - 48, 48, 48,
         {"dialogue": "campanero"})
    oid += 1
    _obj(objetos, oid, "MessageTrigger_Once", "lapida_maestra",
         trazado.COLUMNA_LAPIDA_MAESTRA * TS, y_suelo - 48, 48, 48,
         {"dialogue": "maestra"})
    oid += 1
    # Diálogos de los tres espíritus (árboles en data/dialogues/stage4_1.json).
    for nombre, arbol, col in (("venado", "venado", trazado.COLUMNA_DIALOGO_VENADO),
                               ("serpiente", "serpiente", trazado.COLUMNA_DIALOGO_SERPIENTE),
                               ("halcon", "halcon", trazado.COLUMNA_DIALOGO_HALCON)):
        _obj(objetos, oid, "MessageTrigger_Once", f"dialogo_{nombre}",
             col * TS, y_suelo - 48, 32, 48, {"dialogue": arbol})
        oid += 1
    # Altares de liberación (pulsar usar; el escenario otorga la llave).
    for altar, col in (("altar_venado", trazado.COLUMNA_ALTAR_VENADO),
                       ("altar_serpiente", trazado.COLUMNA_ALTAR_SERPIENTE),
                       ("altar_halcon", trazado.COLUMNA_ALTAR_HALCON)):
        _obj(objetos, oid, "EventTrigger", altar, col * TS, y_suelo - 48, 48, 48,
             {"evento": altar, "automatico": "false", "una_vez": "true"})
        oid += 1
    # Fricción: sendero (normal), musgo (resbala), lodo (frena), polvo (normal).
    for c0, c1, material in trazado.SEGMENTOS_FRICCION:
        props: dict[str, str] = {"material": material}
        if material == "musgo":
            props["inercia"] = str(trazado.INERCIA_DEL_MUSGO)
        elif material == "lodo":
            props["multiplicador"] = str(trazado.FRENO_DEL_LODO)
        else:
            props["multiplicador"] = "1.0"
        _obj(objetos, oid, "FrictionZone",
             f"friccion_{material}_{c0}",
             c0 * TS, y_suelo - 32, (c1 - c0 + 1) * TS, 48, props)
        oid += 1
    # Viento de la Fase 3 (cubre el repiso y las dos lomas).
    _obj(objetos, oid, "WindZone", "viento_serpiente",
         340 * TS, 0, (470 - 340) * TS, MH * TS,
         {"fuerza_x": "-50.0", "fuerza_y": "0.0", "periodo": "3.0"})
    oid += 1
    # Luces verdes de la Fase 6 (apagadas; cada paso enciende la más cercana).
    for col in trazado.COLUMNAS_DE_LUZ:
        _obj(objetos, oid, "Light", f"grieta_{col}", col * TS, y_suelo - 16,
             16, 16, {"radius": "70.0", "color": "#6EFF96", "intensity": "0.0"})
        oid += 1
    # Canto de la planicie + mensaje final + diálogo de Paburu.
    _obj(objetos, oid, "MessageTrigger_Once", "canto_planicie",
         trazado.COLUMNA_CANTO_PLANICIE * TS, y_suelo - 48, 64, 48,
         {"text": "Cánticos antiguos... los muertos van en camino."})
    oid += 1
    _obj(objetos, oid, "MessageTrigger_Once", "mensaje_paburu",
         (trazado.COLUMNA_PORTAL_PABURU + 5) * TS, y_suelo - 80, 32, 80,
         {"text": "Paburu despierta."})
    oid += 1
    _obj(objetos, oid, "MessageTrigger_Once", "dialogo_paburu",
         948 * TS, y_suelo - 80, 32, 80, {"dialogue": "paburu"})
    oid += 1
    # Portal final: warp con llave. Sin los tres espíritus no hay despertar
    # (la causalidad la impone el motor, no un comentario).
    _obj(objetos, oid, "WarpZone", "portal_paburu",
         trazado.COLUMNA_PORTAL_PABURU * TS, y_suelo - 64, 32, 64,
         {"destino_stage_id": "boss_paburu", "key_id": trazado.LLAVE_PABURU,
          "automatico": "false", "una_vez": "true",
          "mensaje": "El portal duerme: libera a los tres espíritus."})
    oid += 1
    mapa.append(_capa(6, "FG_Overlay", _capa_frente(rng)))
    grupo_col = ET.SubElement(mapa, "objectgroup", {"id": "7", "name": "Collision"})
    grupo_obj = ET.SubElement(mapa, "objectgroup", {"id": "8", "name": "Objects"})
    # Mueve los objetos ya creados a sus grupos (se construyeron aparte).
    for o in list(colision):
        grupo_col.append(o)
    for o in list(objetos):
        grupo_obj.append(o)
    # AUD-814: ElementTree no desvincula al re-anexar; sin esto cada objeto
    # quedaría en dos grupos y el validador contaría dos PlayerSpawn.
    mapa.remove(colision)
    mapa.remove(objetos)
    return mapa


def main() -> None:
    mapa = construir()
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    arbol = ET.ElementTree(mapa)
    ET.indent(arbol, space=" ")
    arbol.write(DESTINO, encoding="unicode", xml_declaration=True)
    print("TMX stage4_1 nuevo:", DESTINO)


if __name__ == "__main__":
    main()