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

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.stages.stage4_1.trazado import (  # noqa: E402
    ARBOLES_FASE4,
    COLUMNA_LAPIDA_HUGO,
    COLUMNA_LAPIDA_TERESA,
    COLUMNA_MIRADOR_FASE6,
    DESVIO_COLUMNA_DIALOGO,
    DESVIO_COLUMNA_LIBERACION,
    FRENO_DEL_LODO,
    HUESOS_FASE3,
    MH,
    MURO_ANCHO,
    MW,
    NOMBRE_LAPIDA_HUGO,
    NOMBRE_LAPIDA_TERESA,
    RESBALON_DEL_MUSGO,
    SEGMENTOS_FASE2,
    TEXTO_FINAL_BASE,
    TS,
    TUMBAS_FASE5,
    checkpoints,
    es_meseta,
    evento_de_liberacion,
    extremos_de_las_lomas,
    fase_de_la_columna,
    grietas_de_pisada,
    loma,
    mesetas_de_las_lomas,
    perfil_de_colision,
    perfil_del_suelo,
)

DESTINO = PROJECT_ROOT / "assets" / "maps" / "stage4_1" / "stage4_1.tmx"

# AUD-469: el tileset propio de seis familias, una por sección. El GID es
# `índice + 1` sobre `STAGE4_1_ORDEN` de `tools/generate_all_assets.py` —
# un contrato que defiende `tests/test_stage4_1.py` (AUD-115: cambiar el
# orden en un sitio sin cambiarlo en el otro repinta el nivel entero con la
# baldosa equivocada).
TILESET = "../../tilesets/tileset_stage4_1.png"
TS_COLUMNAS = 8
TS_FILAS = 3
TS_TOTAL = TS_COLUMNAS * TS_FILAS
TS_IMAGEN_PX_X = TS_COLUMNAS * TS
TS_IMAGEN_PX_Y = TS_FILAS * TS

VACIO = 0
CRIPTA = 2
CRIPTA_RELLENO = 3
MURO = 4
BOSQUE = 5
BOSQUE_RELLENO = 6
MUSGO = 7
MUSGO_RELLENO = 8
LODO = 9
LODO_RELLENO = 10
HUESOS = 11
HUESOS_RELLENO = 12
QUEMADO = 13
QUEMADO_RELLENO = 14
TUMBAS = 15
TUMBAS_RELLENO = 16
SAGRADA = 17
SAGRADA_RELLENO = 18
LAPIDA_ALTA = 19
LAPIDA_BAJA = 20
CRUZ = 21
CALAVERA = 22

#: Qué baldosa pinta el suelo de cada sección, en `(superficie, relleno)`.
BALDOSAS_POR_FASE = {
    1: (CRIPTA, CRIPTA_RELLENO),
    2: (BOSQUE, BOSQUE_RELLENO),
    3: (HUESOS, HUESOS_RELLENO),
    4: (QUEMADO, QUEMADO_RELLENO),
    5: (TUMBAS, TUMBAS_RELLENO),
    6: (SAGRADA, SAGRADA_RELLENO),
}
BALDOSAS = {
    "musgo": (MUSGO, MUSGO_RELLENO),
    "lodo": (LODO, LODO_RELLENO),
}


def _material_de(columna: int) -> tuple[int, int]:
    for inicio, ancho, material in SEGMENTOS_FASE2:
        if inicio <= columna < inicio + ancho:
            return BALDOSAS[material]
    return BALDOSAS_POR_FASE[fase_de_la_columna(columna)]


def _terreno() -> list[list[int]]:
    """La geometría del pasillo, columna a columna."""
    g = [[VACIO] * MW for _ in range(MH)]
    perfil = perfil_del_suelo()

    for x in range(MW):
        superficie = perfil[x]
        arriba, abajo = _material_de(x)
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
    g[suelo_egg - 1][COLUMNA_LAPIDA_TERESA] = LAPIDA_BAJA
    g[suelo_egg - 2][COLUMNA_LAPIDA_TERESA] = LAPIDA_ALTA
    suelo_egg2 = perfil[COLUMNA_LAPIDA_HUGO]
    g[suelo_egg2 - 1][COLUMNA_LAPIDA_HUGO] = LAPIDA_BAJA
    g[suelo_egg2 - 2][COLUMNA_LAPIDA_HUGO] = LAPIDA_ALTA

    # Los huesos y calaveras del camino de la Fase 3.
    for col in HUESOS_FASE3:
        fila = perfil[col]
        g[fila - 1][col] = CALAVERA

    # Las cruces de conquistador de la Fase 5.
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
    #
    # Es `perfil_de_colision()` y no `perfil_del_suelo()` a propósito
    # (AUD-470): la colisión de la rampa se queda plana y es el `Slope`
    # quien empuja al jugador hacia arriba — un escalón sólido por columna
    # bloqueaba el paso antes de que el `Slope` llegara a intervenir.
    #
    # AUD-477 — las mesetas de las lomas (`es_meseta`) tampoco llevan bloque
    # sólido: las cubre un `Pendiente` prácticamente plano
    # (`mesetas_de_las_lomas`, más abajo). Un recorrido real encontró que
    # una meseta sólida justo al final de una rampa deja al jugador clavado
    # en la unión —el AABB del fotograma usa la `y` con la que la rampa
    # **aún no** llegó del todo a la altura de la meseta— sin que importe
    # cuán suave sea la rampa; el detalle completo vive en
    # `trazado.py::altura_de_colision`.
    perfil = perfil_de_colision()
    inicio = MURO_ANCHO
    for x in range(MURO_ANCHO + 1, MW - MURO_ANCHO + 1):
        cambia = (x == MW - MURO_ANCHO or perfil[x] != perfil[inicio]
                  or es_meseta(x) != es_meseta(inicio))
        if cambia:
            if not es_meseta(inicio):
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

    # `perfil_de_colision()`: todo lo que se coloca aquí tiene que apoyarse
    # en dónde el jugador **puede pisar de verdad**, no en la baldosa que
    # se pinta (AUD-470) — si no, un disparador dentro de la rampa quedaría
    # flotando sobre el suelo sólido real.
    perfil = perfil_de_colision()
    spawn_col = MURO_ANCHO + 3
    obj("PlayerSpawn", spawn_col * TS, (perfil[spawn_col] - 3) * TS, 16, 32)

    # ── La cutscene de introducción ────────────────────────────
    #
    # Objeto-punto (ancho y alto 0): dispara al empezar el escenario, sin
    # que el jugador tenga que cruzar ninguna zona (AUD-136,
    # `stage_objetos.py::_handle_cutscene`). El guion está en el
    # mini-lenguaje de `cutscene_guion.py` — nada de Python nuevo.
    guion_intro = (
        "fundido entra 1.5\n"
        "texto Voces: Los espiritus hablan de Paburu, en una lengua antigua.\n"
        "esperar 2.5\n"
        "texto Jhon: Este lugar... lo reconozco.\n"
        "esperar 2.0\n"
        "fundido sale 1.0\n"
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
        col = fase.desde_columna + DESVIO_COLUMNA_DIALOGO
        obj("MessageTrigger_Once", col * TS, (perfil[col] - 3) * TS, 32, 32,
            dialogue=fase.dialogo_id)

    # ── Liberar a cada espíritu es algo que el jugador hace, no algo
    # que pasa solo (AUD-474) ────────────────────────────────────
    #
    # Antes, el espíritu ascendía por caminar el 85-100% de la sección —
    # nada distinguía a quien lo vio pasar de quien se detuvo a
    # escucharlo. Unos pasos después del punto donde habla, un
    # `EventTrigger` con `automatico=False` exige el botón de usar: quien
    # no lo pulsa deja al espíritu sin liberar, y `Stage4_1` lo nota (ver
    # `_espiritu_liberado` y el mensaje final, que cuenta cuántos se
    # liberaron de verdad).
    for fase in FASES:
        if fase.espiritu is None:
            continue
        col = fase.desde_columna + DESVIO_COLUMNA_LIBERACION
        obj("EventTrigger", col * TS, (perfil[col] - 3) * TS, 48, 32,
            evento=evento_de_liberacion(fase.numero), automatico=False)

    # ── Las superficies de la Fase 2 (musgo y lodo) ────────────
    #
    # AUD-513, GAP-060 punto 14 — la escena escala el freno con la
    # intensidad de la lluvia (`Stage4_1._actualizar_friccion_de_la_lluvia`).
    # Sigue reconociendo cada zona por su valor de fábrica, no por
    # `material=`: aunque el musgo ya declara `material="musgo"` desde
    # AUD-522 (para encender la pisada y la partícula propias,
    # `states/grounded.py`), la escena no puede depender de que el TMX
    # comprometido ya lo traiga — `assets/maps/stage4_1/stage4_1.tmx`
    # sigue con `BG_Far`/`BG_Mid` pintados a mano, y
    # `tools/generate_stage4_1.py` se niega a regenerar las capas de
    # baldosa sin `--forzar` (`tiene_arte_pintado()`). Cada cambio de
    # propiedades de `Objects` se aplica con un parche quirúrgico que sólo
    # toca esa capa — el mismo patrón que ya usan el mirador (AUD-515) y
    # los checkpoints (AUD-516) — y éste ya se aplicó, pero la próxima
    # persona que cambie algo aquí no puede asumir que el mapa real está al
    # día sin comprobarlo (`TestElMapaSigueAtadoASuGenerador`).
    #
    # AUD-522 — el musgo resbala (`inercia`), el lodo frena
    # (`multiplicador`, sin cambios): son campos distintos a propósito, ver
    # la nota junto a `RESBALON_DEL_MUSGO` en `trazado.py`.
    for inicio, ancho, material in SEGMENTOS_FASE2:
        fila = perfil[inicio]
        if material == "musgo":
            # `material="musgo"` (además de `inercia`) es lo que enciende
            # la pisada y la partícula propias (AUD-522,
            # `states/grounded.py`): sin declararlo, `Transform.material_actual`
            # se queda en "roca" y el jugador nunca se entera de que está
            # sobre musgo salvo por cómo resbala.
            obj("FrictionZone", inicio * TS, (fila - 2) * TS, ancho * TS, 2 * TS,
                inercia=RESBALON_DEL_MUSGO, material="musgo")
        elif material == "lodo":
            obj("FrictionZone", inicio * TS, (fila - 2) * TS, ancho * TS, 2 * TS,
                multiplicador=FRENO_DEL_LODO)

    # ── Las lomas de la Fase 3: dos parejas de `Slope` reales (AUD-477) ──
    for lx, lfila_arriba, lancho, lalto, lsube in loma():
        obj("Slope", lx * TS, lfila_arriba * TS, lancho * TS, lalto * TS,
            sube=lsube)

    # ── Las cimas llanas: 1 px de alto, no 0 (ver `mesetas_de_las_lomas`,
    # el porqué del píxel en vez de la fila) ──
    for mx, mfila, mancho in mesetas_de_las_lomas():
        obj("Slope", mx * TS, mfila * TS, mancho * TS, 1, sube="derecha")

    # ── El viento de la Fase 3 («carácter ventoso» de Tilarán) ──
    #
    # Cubre las dos lomas, no sólo la primera que se declaró — el margen
    # (40 antes, 80 después) es el mismo de siempre, ahora medido desde los
    # extremos reales de `LOMAS_FASE3` en vez de una sola loma con nombre.
    _inicio_lomas, _fin_lomas = extremos_de_las_lomas()
    obj("WindZone", (_inicio_lomas - 40) * TS, 0,
        (_fin_lomas - _inicio_lomas + 80) * TS, MH * TS,
        fuerza_x=-60.0, fuerza_y=0.0, periodo=3.2)

    # ── Las grietas de la Fase 6, apagadas: las enciende la escena ──
    for col, fila in grietas_de_pisada():
        obj("Light", col * TS, (fila - 2) * TS, TS, TS,
            radius=70.0, color="#7CFFA0", intensity=0.0)

    # ── El umbral ──────────────────────────────────────────────
    ultima = MW - MURO_ANCHO - 4
    obj("MessageTrigger_Once", ultima * TS, (perfil[ultima] - 5) * TS,
        2 * TS, 5 * TS, text=TEXTO_FINAL_BASE)
    obj("NextTrigger", ultima * TS, (perfil[ultima] - 3) * TS, 2 * TS, 3 * TS)

    # ── El mirador (AUD-515, GAP-064 punto 17) ──────────────────
    #
    # Se dispara al entrar el jugador (rectángulo, no punto): la cámara se
    # aleja hacia atrás, se queda un momento —el jugador no puede moverse
    # mientras tanto, `bloquea=True`, que es la pausa contemplativa del
    # punto 23-24— y vuelve. Las coordenadas de cámara son absolutas
    # (`camara x y duración` no acepta «.» como `mover` sí): se calculan
    # sobre dónde queda centrado normalmente el jugador en esta columna
    # (`x·TS - INTERNAL_WIDTH/2`, la misma cuenta que hace `Camera.update`
    # al seguirlo) y se aleja 280 px a la izquierda, menos que una pantalla
    # completa (800 px) para que se lea como girar la cabeza, no como
    # teletransportarse.
    col_mirador = COLUMNA_MIRADOR_FASE6
    x_centrado = col_mirador * TS - 400
    x_alejado = x_centrado - 280
    y_camara = 180  # altura vertical típica del jugador de pie, centrado
    guion_mirador = (
        "fundido entra 0.3\n"
        f"camara {x_alejado} {y_camara} 2.2\n"
        "esperar 2.5\n"
        f"camara {x_centrado} {y_camara} 1.6\n"
        "fundido sale 0.2\n"
    )
    obj("Cutscene", col_mirador * TS, (perfil[col_mirador] - 4) * TS, 3 * TS, 5 * TS,
        guion=guion_mirador, bloquea=True, saltable=True, una_vez=True)

    return [x for x in o if x]


def generar() -> str:
    # AUD-546 — `bgm_track` (abajo, en las propiedades del mapa) es sólo
    # lo que `StageScene` arranca en el primerísimo fotograma; a partir de
    # ahí manda `fases.py` (`Fase.musica`, `_actualizar_musica_de_fase`
    # en `stage4_1.py`) con una pista por fase. Declararlo como la pista
    # de la Fase 1 —no la del clímax, como antes de AUD-546— evita un
    # parpadeo de un fotograma con la pista equivocada sonando de más.
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
  <property name="bgm_track" value="bgm_stage4_1_fase1"/>
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
 <tileset firstgid="1" name="tileset_stage4_1" tilewidth="{TS}" tileheight="{TS}" \
tilecount="{TS_TOTAL}" columns="{TS_COLUMNAS}">
  <image source="{TILESET}" width="{TS_IMAGEN_PX_X}" height="{TS_IMAGEN_PX_Y}"/>
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


#: Las capas que pinta una persona en Tiled y que el generador no produce.
#: `Terrain` no está aquí: la geometría es del código (`trazado.py`), y que
#: siga siéndolo es justo lo que defiende `comparar_geometria`.
CAPAS_DE_ARTE: tuple[str, ...] = (
    "BG_Far", "BG_Mid", "BG_Near", "Terrain_Detail", "FG_Overlay",
)


def _normalizar(valor: str) -> str:
    """`0.60`, `0.6` y `70.0` son el mismo número escrito de tres maneras.

    Tiled reescribe los flotantes al guardar (`-60.0` → `-60`), así que
    compararlos como texto da diferencias que no significan nada.
    """
    try:
        return repr(float(valor))
    except ValueError:
        return "\n".join(linea.strip() for linea in valor.strip().splitlines())


def _propiedades(nodo: ET.Element) -> dict[str, str]:
    """Las propiedades de un nodo, ordenadas y con los números normalizados.

    Tiled las reordena alfabéticamente y mueve los textos largos de atributo
    `value` a contenido del elemento; las dos formas significan lo mismo.
    """
    props: dict[str, str] = {}
    for p in nodo.findall("./properties/property"):
        nombre = p.get("name", "")
        crudo = p.get("value")
        if crudo is None:
            crudo = p.text or ""
        props[nombre] = _normalizar(crudo)
    return props


def geometria_de(tmx: str) -> dict[str, object]:
    """Lo que el generador posee de un mapa, en forma comparable.

    AUD-495. La prueba original comparaba el TMX con `generar()` byte a
    byte, y eso dejó de funcionar en cuanto el mapa se abrió en Tiled: al
    guardar, Tiled sube su `tiledversion`, reordena las propiedades
    alfabéticamente, normaliza los flotantes y cierra los objetos vacíos con
    `/>`. Ninguna de esas diferencias cambia el nivel.

    Lo que sí importa —y lo que AUD-115 quería proteger de verdad— es que la
    geometría no se separe de `trazado.py`: si alguien mueve el suelo a mano
    en Tiled, o cambia el orden de las baldosas en un fichero y no en el
    otro, el nivel se repinta mal. Eso es lo que se compara aquí.

    Se ignora a propósito: las capas de `CAPAS_DE_ARTE` (son autoría manual),
    los tilesets añadidos desde Tiled, el orden de las propiedades, el
    formato de los números y la versión de la herramienta.
    """
    raiz = ET.fromstring(tmx)
    # El CSV se compara por sus números, no por su formato: el generador lo
    # escribe todo en una línea y Tiled lo parte por filas y deja una coma
    # al final de cada una. Son el mismo mapa.
    capas = {
        c.get("name", ""): ",".join(
            g.strip() for g in (c.findtext("data") or "").split(",") if g.strip()
        )
        for c in raiz.findall("layer")
        if c.get("name") not in CAPAS_DE_ARTE
    }
    grupos: dict[str, list[tuple]] = {}
    for grupo in raiz.findall("objectgroup"):
        objetos = []
        for o in grupo.findall("object"):
            objetos.append((
                o.get("id"), o.get("type"),
                *(_normalizar(o.get(k, "0")) for k in ("x", "y", "width", "height")),
                tuple(sorted(_propiedades(o).items())),
            ))
        grupos[grupo.get("name", "")] = sorted(objetos)
    return {
        "dimensiones": (raiz.get("width"), raiz.get("height")),
        "propiedades": _propiedades(raiz),
        "capas": capas,
        "objetos": grupos,
    }


def comparar_geometria() -> list[str]:
    """Las diferencias reales entre el mapa en disco y su generador."""
    if not DESTINO.exists():
        return [f"{DESTINO} no existe: ejecuta el generador"]
    actual = geometria_de(DESTINO.read_text(encoding="utf-8"))
    esperado = geometria_de(generar())
    fallos = []
    for clave in esperado:
        if actual[clave] != esperado[clave]:
            if clave == "capas":
                for nombre, datos in esperado["capas"].items():  # type: ignore[union-attr]
                    if actual["capas"].get(nombre) != datos:  # type: ignore[union-attr]
                        fallos.append(f"la capa {nombre!r} no es la del generador")
            else:
                fallos.append(f"{clave} no coincide con el generador")
    return fallos


def tiene_arte_pintado() -> bool:
    """¿Hay trabajo hecho a mano en el mapa que el generador borraría?"""
    if not DESTINO.exists():
        return False
    raiz = ET.fromstring(DESTINO.read_text(encoding="utf-8"))
    for capa in raiz.findall("layer"):
        if capa.get("name") not in CAPAS_DE_ARTE:
            continue
        if any(g.strip() not in ("", "0")
               for g in (capa.findtext("data") or "").split(",")):
            return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Regenera el TMX del 4-1.")
    ap.add_argument(
        "--forzar", action="store_true",
        help="sobrescribe aunque el mapa tenga capas de arte pintadas a mano",
    )
    ap.add_argument(
        "--comprobar", action="store_true",
        help="no escribe: sólo dice si la geometría del mapa sigue siendo la "
             "del generador",
    )
    args = ap.parse_args()

    if args.comprobar:
        fallos = comparar_geometria()
        for f in fallos:
            print(f"  {f}")
        print("la geometría coincide" if not fallos else "la geometría NO coincide")
        raise SystemExit(1 if fallos else 0)

    # AUD-495 — el pie de plomo que faltaba. El 4-1 tiene 13 240 celdas
    # pintadas a mano en Tiled (parallax y decoración); regenerar sin más
    # las borraba todas y sin aviso, porque `generar()` escribe esas capas
    # a ceros. Quien de verdad quiera rehacer el mapa entero lo dice.
    if tiene_arte_pintado() and not args.forzar:
        raise SystemExit(
            f"{DESTINO.name} tiene capas de arte pintadas a mano "
            f"({', '.join(CAPAS_DE_ARTE)}) y regenerar las borraría.\n"
            f"Si es lo que quieres, repite con --forzar."
        )

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(generar(), encoding="utf-8")
    print(f"escrito {DESTINO.relative_to(PROJECT_ROOT)} "
          f"({MW}×{MH} baldosas, 6 secciones, {len(checkpoints())} checkpoints, "
          f"{len(ARBOLES_FASE4)} tocones, {len(TUMBAS_FASE5)} tumbas, "
          f"{len(grietas_de_pisada())} grietas, {len(loma()) // 2} lomas, "
          f"0 enemigos, 0 fosos, 0 zonas de daño)")


if __name__ == "__main__":
    main()
