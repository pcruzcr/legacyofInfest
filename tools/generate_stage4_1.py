#!/usr/bin/env python3
"""
Genera `assets/maps/stage4_1/stage4_1.tmx` — La Entrada al Cementerio.

El nivel, en una frase
=======================
Un sendero de 100 baldosas sin un solo enemigo, donde **el fondo avanza con el
jugador**: cada tramo enciende braseros, baja la luna, sube la tormenta y
acerca las siluetas. La ficha (`docs/niveles/13_STAGE_4_1.md`) lo llama
«travesía atmosférica»; el diseño (`15_DISENO_4_1_EL_CEMENTERIO.md`) lo
estructura en cinco actos con la pelea de Magus como referencia.

Por qué se genera con código
-----------------------------
Igual que `generate_stage0_tmx.py` y `generate_stage_mecanicas.py`: un TMX a
mano son miles de números en CSV que nadie puede revisar en un *pull request*.
Generado, el diff es de diez líneas de Python y se lee lo que cambió.

Los cinco actos, y dónde empieza cada uno
------------------------------------------
El mapa mide 100 baldosas. Los actos se reparten en tramos de 20, y la escena
(`src/stages/stage4_1/stage4_1.py`) lee la `x` del jugador para saber en cuál
está. Aquí sólo se coloca **lo que es geometría**; el clima, la luna y las
siluetas los mueve la escena.

    0-19    I   La Entrada              suelo continuo, sin peligros
    20-39   II  El Sendero de los Nombres   lápidas con nombres, grietas visibles
    40-59   III La Niebla que Respira   primer tramo de saltos (grietas)
    60-79   IV  La Tormenta             losas que ceden + grietas
    80-99   V   El Umbral               suelo firme, la lápida «LA PRUEBA»

La regla de oro: **cero enemigos**
-----------------------------------
No se coloca ni uno. `tests/test_stage4_1.py` lo comprueba cargando el mapa y
contando `entity_list`, no leyendo el XML: un enemigo colocado por una
propiedad rara también contaría.

Sobre el «Portal» de la ficha
------------------------------
La ficha pide «1 `Portal`». Ese tipo **no existe en el motor** — la auditoría
de documentación ya lo tenía señalado. La salida de un escenario es
`NextTrigger`, que es lo que se coloca aquí. Es la misma cosa con otro nombre;
lo que no se puede es escribir en el mapa un tipo que el cargador rechaza.
"""
from __future__ import annotations

import sys
from pathlib import Path

# AUD-177: imprime `→` y la consola de Windows usa cp1252, que no lo tiene.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESTINO = PROJECT_ROOT / "assets" / "maps" / "stage4_1" / "stage4_1.tmx"
TILESET = "../../tilesets/tileset_stage0.png"

TS = 16
MW, MH = 100, 38          # 1600 × 608 px — el mínimo que pide la ficha
SUELO_Y = 30              # fila del suelo; deja 30 filas de cielo para la luna
ACTO = 20                 # ancho de cada acto, en baldosas

# ── Baldosas ────────────────────────────────────────────────────────────────
# La cabecera del tileset se copia del mapa que ya funciona. Inventarla es lo
# que dejó `stage_mecanicas` pintando las tres primeras baldosas de la hoja
# durante semanas (AUD-115).
TS_COLUMNAS = 64
TS_TOTAL = 4096
TS_IMAGEN_PX = 1024

VACIO = 0
SUELO = 409               # la losa que se pisa
MURO = 153                # piedra de cierre
LOSA = 666                # lápida caída / repisa
RELLENO = 665             # tierra bajo la superficie


#: Los doce braseros, en `x` de baldosa. El último es el del umbral: grande y
#: central, en el acto V. La escena los enciende por proximidad y **no los
#: apaga**, así que el sendero queda marcado de luz por detrás del jugador.
BRASEROS: tuple[int, ...] = (
    6, 13,                    # I  — dos, fríos, para que se vea qué es un brasero
    22, 30, 37,               # II — el sendero de los nombres
    42, 48, 54,               # III— acompañan el primer tramo de saltos
    62, 71,                   # IV — la tormenta
    84, 94,                   # V  — el umbral; el último es el grande
)

def _terreno() -> list[list[int]]:
    """La geometría del cementerio, acto por acto."""
    g = [[VACIO] * MW for _ in range(MH)]

    # Suelo continuo. Los huecos se abren después, donde toca.
    for y in range(SUELO_Y, MH):
        for x in range(MW):
            g[y][x] = SUELO if y == SUELO_Y else RELLENO

    # Acto III — el primer tramo de saltos. Tres grietas anchas que se cruzan
    # de una en una: es la presentación de la mecánica, no el examen.
    for x0 in (44, 50, 56):
        for y in range(SUELO_Y, MH):
            for x in range(x0, x0 + 3):
                g[y][x] = VACIO

    # Acto IV — la tormenta. Cuatro huecos más juntos; entre ellos van las
    # losas que ceden, así que el suelo no puede estar.
    for x0 in (63, 68, 73, 78):
        for y in range(SUELO_Y, MH):
            for x in range(x0, x0 + 4):
                g[y][x] = VACIO

    # Lápidas caídas: peldaños de piedra sobre el sendero. Están en los actos
    # II y V, donde no hay huecos, para que se lean como decoración jugable y
    # no como parte del tramo de saltos.
    for x in (24, 25, 33, 34, 86, 87):
        g[SUELO_Y - 2][x] = LOSA
    for x in (28, 29, 90, 91):
        g[SUELO_Y - 4][x] = LOSA

    # Muros laterales: el cementerio está cerrado. El de la derecha deja pasar
    # al 4-2 por el disparador, no por el borde.
    for y in range(MH):
        g[y][0] = MURO

    return g


def _colisiones() -> list[str]:
    """La capa `Collision`: suelo por tramos y las repisas de lápida."""
    r: list[str] = []
    ident = [1]

    def solido(x: int, y: int, w: int, h: int, tipo: str = "Solid") -> None:
        ident[0] += 1
        r.append(
            f'  <object id="{ident[0]}" type="{tipo}" x="{x}" y="{y}"'
            f' width="{w}" height="{h}"/>',
        )

    suelo_px = SUELO_Y * TS
    alto = (MH - SUELO_Y) * TS

    # Tramos de suelo, saltando los siete huecos. Se calculan a partir de la
    # misma lista que los abre para que no puedan divergir.
    huecos = [(44, 3), (50, 3), (56, 3), (63, 4), (68, 4), (73, 4), (78, 4)]
    x = 0
    for inicio, ancho in huecos:
        if inicio > x:
            solido(x * TS, suelo_px, (inicio - x) * TS, alto)
        x = inicio + ancho
    solido(x * TS, suelo_px, (MW - x) * TS, alto)

    # Muros laterales.
    solido(-TS, 0, TS, MH * TS)
    solido(MW * TS, 0, TS, MH * TS)

    # Lápidas caídas, atravesables desde abajo: son peldaños, no techo.
    for x0 in (24, 33, 86):
        solido(x0 * TS, (SUELO_Y - 2) * TS, 2 * TS, 8, "Platform")
    for x0 in (28, 90):
        solido(x0 * TS, (SUELO_Y - 4) * TS, 2 * TS, 8, "Platform")

    # El borde de cada cuenco de fuego, también atravesable desde abajo: se
    # puede subir encima de un brasero. El último no lleva —es el del umbral,
    # y subirse a él rompería la imagen del final.
    for bx in BRASEROS[:-1]:
        solido(bx * TS, (SUELO_Y - 1) * TS, 2 * TS, 8, "Platform")

    return r


#: Los nombres de los estudiantes van aquí. Se dejan como marcador de posición
#: a propósito: el diseño (§7) exige que los cargue el profesor, que todos
#: estén sin distinción de nota, y que ninguna inscripción se burle de nadie.
#: Escribir yo una lista inventada sería justo lo contrario.
EPITAFIOS: tuple[tuple[int, str], ...] = (
    (23, "[NOMBRE] — Computo Grafico, 2026"),
    (31, "[NOMBRE] — Procesamiento de Imagenes, 2026"),
    (38, "[NOMBRE] — Vision por Computadora, 2026"),
    (88, "[NOMBRE] — Reconocimiento de Patrones, 2026"),
)


def _objetos() -> list[str]:
    """Los objetos del TMX. Ni un solo enemigo: es la regla de oro."""
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

    suelo_px = SUELO_Y * TS

    obj("PlayerSpawn", 3 * TS, suelo_px - 48, 16, 32)

    # ── Acto I — La Entrada ───────────────────────────────────
    obj("MessageTrigger_Once", 5 * TS, suelo_px - 64, 48, 48,
        text="El cementerio no ataca. Testifica.")

    # ── Los doce braseros ─────────────────────────────────────
    #
    # Cada uno es una luz de Tiled. El motor las coloca desde el centro del
    # rectángulo, así que se dibujan como un cuadro alrededor del cuenco.
    # `flicker` las hace respirar: un fuego que no parpadea se lee como una
    # bombilla.
    for i, bx in enumerate(BRASEROS):
        ultimo = i == len(BRASEROS) - 1
        obj("Light", bx * TS, suelo_px - 3 * TS, 2 * TS, 2 * TS,
            radius=140.0 if ultimo else 90.0,
            color="#7CFFA0",          # verde espectral: el color del canon
            intensity=0.95 if ultimo else 0.75,
            flicker=True, flicker_speed=2.2, flicker_amount=0.28)
        # El cuenco en sí es una repisa. Va en la capa `Collision`, no aquí:
        # `Platform` es un tipo de colisión y el validador lo rechaza en
        # `Objects`. Ver `_colisiones()`.

    # ── Acto II — El Sendero de los Nombres ───────────────────
    obj("MessageTrigger_Once", 21 * TS, suelo_px - 64, 48, 48,
        text="Los nombres de los que pasaron por aqui.")
    for bx, texto in EPITAFIOS[:3]:
        obj("MessageTrigger_Once", bx * TS, suelo_px - 3 * TS, 2 * TS, 3 * TS,
            text=texto)

    # Grietas del acto II: **visibles y sin daño mortal**, para que el jugador
    # aprenda a leerlas antes de que importen. Es la regla del §5 del diseño:
    # ningún peligro aparece sin haberse mostrado antes.
    obj("HazardZone", 27 * TS, suelo_px - 4, 3 * TS, 4, damage=0.0)
    obj("HazardZone", 35 * TS, suelo_px - 4, 3 * TS, 4, damage=0.0)

    obj("Checkpoint", 39 * TS, suelo_px - 32, 16, 32, checkpoint_id=1)

    # ── Acto III — La Niebla que Respira ──────────────────────
    obj("MessageTrigger_Once", 41 * TS, suelo_px - 64, 48, 48,
        text="Las grietas respiran. Salta cuando exhalen.")
    for x0 in (44, 50, 56):
        obj("DeathPit", x0 * TS, (MH - 1) * TS, 3 * TS, TS)
        # La grieta pulsa en el borde: se ve el peligro antes de caer en él.
        obj("HazardZone", x0 * TS, suelo_px - 6, 3 * TS, 6, damage=0.25)

    # ── Acto IV — La Tormenta ─────────────────────────────────
    obj("MessageTrigger_Once", 61 * TS, suelo_px - 64, 48, 48,
        text="No te pares. La piedra cede.")
    for x0 in (63, 68, 73, 78):
        obj("DeathPit", x0 * TS, (MH - 1) * TS, 4 * TS, TS)
    # Las losas que ceden: aguantan medio segundo y se hunden. Reaparecen a los
    # 3 s para que morir no cierre el camino.
    for x0 in (64, 69, 74, 79):
        obj("SinkingPlatform", x0 * TS, suelo_px - 2 * TS, 3 * TS, 8,
            retraso=0.55, velocidad_caida=110.0, reaparece_en=3.0)
    # El viento de la tormenta empuja hacia adelante, nunca contra el salto:
    # ayuda a leer que hay tormenta sin castigar por ella.
    obj("WindZone", 62 * TS, (SUELO_Y - 8) * TS, 20 * TS, 8 * TS,
        fuerza_x=90.0, fuerza_y=0.0, periodo=2.6)

    obj("Checkpoint", 82 * TS, suelo_px - 32, 16, 32, checkpoint_id=2)

    # ── Acto V — El Umbral ────────────────────────────────────
    obj("MessageTrigger_Once", 85 * TS, suelo_px - 64, 48, 48,
        text="Silencio. Los doce arden.")
    obj("MessageTrigger_Once", EPITAFIOS[3][0] * TS, suelo_px - 3 * TS,
        2 * TS, 3 * TS, text=EPITAFIOS[3][1])
    # La lápida central. No lleva nombre: lleva la inscripción del diseño (§7).
    obj("MessageTrigger_Once", 95 * TS, suelo_px - 5 * TS, 2 * TS, 5 * TS,
        text="LA PRUEBA")

    # La salida al 4-2. La ficha la llama «Portal»; el motor la llama
    # `NextTrigger` y es el único tipo que el cargador acepta para salir.
    obj("NextTrigger", (MW - 3) * TS, suelo_px - 3 * TS, 2 * TS, 3 * TS)

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
  <property name="stage_id" value="stage4_1"/>
  <property name="stage_name" value="4-1  LA ENTRADA AL CEMENTERIO"/>
  <property name="author" value="Equipo docente — Legacy of Infest"/>
  <property name="bgm_track" value="bgm_zone3"/>
  <property name="background_zone" value="stage0"/>
  <!-- El clima ARRANCA en niebla y lo cambia la escena por acto: fog al
       principio, storm en el acto IV, clear en el umbral. -->
  <property name="climate" value="fog"/>
  <!-- Partículas verdes: `spores` es el único efecto del motor que sale en
       verde (150,255,130), y es exactamente la «luz espectral verde» que el
       lore le pone al cementerio. La escena sube el ritmo con los actos. -->
  <property name="ambient_fx" value="spores"/>
  <property name="ambient_fx_rate" type="float" value="10"/>
  <!-- 19:00 → 23:00 en 900 s, como pide la ficha. -->
  <property name="start_hour" type="float" value="19"/>
  <property name="day_length" type="float" value="900"/>
  <property name="time_limit" type="int" value="0"/>
  <property name="zone" type="int" value="4"/>
  <!-- Oscuro, pero no injugable: el suelo de MIN_AMBIENTE del motor (0,45)
       protege de que la noche haga imposible ver las grietas. -->
  <property name="ambient_light" type="float" value="0.42"/>
  <property name="bloom" type="float" value="0.34"/>
  <property name="vignette" type="float" value="0.52"/>
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
          f"({MW}×{MH} baldosas, {len(BRASEROS)} braseros, 0 enemigos)")


if __name__ == "__main__":
    main()
