"""Genera `student_templates/stage_template/stage_template.tmx` — AUD-417.

Por qué la plantilla se genera y no se edita a mano
==================================================
Es el fichero que **copian los veintiséis estudiantes** en la primera clase, y
por eso es el que más caro sale tener mal: un defecto aquí se multiplica por
veintiséis antes de que nadie lo ejecute. Mismo motivo por el que
`validate_tmx.py` valida `student_templates/` desde AUD-306.

Generarlo da dos cosas que editarlo a mano no da: queda una prueba que
comprueba que el fichero del repositorio y su generador siguen de acuerdo
(como `stage_mecanicas` desde AUD-153), y el *porqué* de cada objeto se escribe
aquí al lado en vez de perderse en un XML de 143 líneas.

Qué cambió respecto de la plantilla anterior, y por qué
=======================================================
La anterior sacaba **64,6 %** en `scripts/grade_stage.py` — la rúbrica del
propio curso. El estudiante empezaba cuesta arriba y sin saberlo, porque
`validate_tmx.py` la daba por `[OK]` (eso se arregló aparte, en AUD-416).

Lo que le faltaba, medido con el calificador:

===========================  ====================================================
Categoría                    Qué faltaba
===========================  ====================================================
``enemies_valid_types``      0/10 — ningún enemigo colocado
``enemies_placed``           0/10 — idem
``climate_valid``            0/5  — sin ``climate``
``metadata``                 7/10 — sin ``author``
``checkpoints``              5/15 — uno solo
``collectibles``             5/10 — ninguno
``design_pacing``            5/8  — «el recorrido no tiene ningún salto exigente»
===========================  ====================================================

La plantilla nueva trae **un ejemplo de cada cosa**, y ésa es la decisión de
diseño: no es un nivel para jugar, es un catálogo que se abre en Tiled y se
lee. Un estudiante aprende más borrando un enemigo que le sobra que buscando en
la documentación cómo se coloca el primero.

Lo que **no** se hace: rellenarla de contenido. Un ejemplar de cada tipo, con
nombres que dicen para qué está (`Pickup_ejemplo_01`), para que se distinga a
simple vista lo que es andamiaje de lo que el estudiante añada.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "student_templates" / "stage_template" / "stage_template.tmx"

#: Baldosas. 60×16 a 16 px son 960×256 px: cabe un salto exigente y sigue
#: entrando entera en una pantalla de Tiled sin desplazarse.
ANCHO, ALTO, TS = 60, 16, 16
#: Fila del suelo. Deja 12 filas de aire por encima, que es margen de sobra
#: para el salto del jugador (72 px ≈ 4,5 baldosas).
FILA_SUELO = 13

#: El hueco, en baldosas. Cinco (80 px) y el número no es al azar: medido con
#: `JumpEnvelope.from_settings()`, el salto del jugador cruza hasta **85,5 px**,
#: lo «cómodo» acaba en **68,4** y lo «exigente» llega hasta 171 con salto
#: aéreo. O sea que 80 px cae en exigente **y se cruza con el salto normal**.
#:
#: Ésa es toda la gracia: la primera versión puso tres baldosas (48 px) y el
#: calificador respondió «el recorrido no tiene ningún salto exigente», porque
#: 48 es cómodo. Un hueco que hay que respetar pero que no exige una técnica
#: avanzada es lo que enseña a medir un salto; uno de siete obligaría al salto
#: aéreo y dejaría fuera a quien aún no lo ha desbloqueado.
HUECO_INICIO, HUECO_FIN = 30, 34


def _unir(filas: list[str]) -> str:
    """Une las filas del CSV con coma **al final de cada una menos la última**.

    Es el formato que escribe Tiled, y no es cosmético: `validate_tmx` cuenta
    los tiles con `raw.replace("\\n", "").split(",")`, así que sin esa coma dos
    filas contiguas se pegan —`…0` + `0,0…`— y cada salto de línea se come un
    tile. La primera versión de este generador perdía 15 de 960 exactamente
    así, y el validador lo cazó en la primera ejecución.
    """
    return ",\n".join(filas)


def _capa_vacia(nombre: str, id_: int) -> str:
    fila = ",".join("0" for _ in range(ANCHO))
    filas = _unir([fila for _ in range(ALTO)])
    return (
        f' <layer id="{id_}" name="{nombre}" width="{ANCHO}" height="{ALTO}">\n'
        f'  <data encoding="csv">\n{filas}\n</data>\n </layer>\n'
    )


def _capa_terreno(id_: int) -> str:
    """El suelo, con el hueco. Es la única capa con baldosas puestas.

    Las dos filas de abajo son sólidas salvo en el hueco: una sola fila se ve
    como una línea flotante y el estudiante no entiende dónde acaba el mundo.
    """
    filas = []
    for y in range(ALTO):
        if y < FILA_SUELO:
            filas.append(",".join("0" for _ in range(ANCHO)))
        else:
            fila = [
                "0" if HUECO_INICIO <= x <= HUECO_FIN else "1"
                for x in range(ANCHO)
            ]
            filas.append(",".join(fila))
    cuerpo = _unir(filas)
    return (
        f' <layer id="{id_}" name="Terrain" width="{ANCHO}" height="{ALTO}">\n'
        f'  <data encoding="csv">\n{cuerpo}\n</data>\n </layer>\n'
    )


def _objeto(id_: int, tipo: str, nombre: str, x: int, y: int,
            w: int | None = None, h: int | None = None,
            props: dict[str, tuple[str, str]] | None = None) -> str:
    """Un `<object>`. `props` es ``{nombre: (tipo_tiled, valor)}``."""
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


def _objetos() -> str:
    """La capa `Objects`: un ejemplar de cada cosa que un nivel puede tener."""
    suelo_y = FILA_SUELO * TS
    o: list[str] = []

    # -- lo imprescindible para que el nivel cargue -----------------
    o.append(_objeto(1, "PlayerSpawn", "PlayerSpawn_01", 48, suelo_y - 32))
    # Dos puntos de control y no uno: el calificador pide >=2, y con uno solo
    # el tramo del hueco se repite entero en cada muerte.
    o.append(_objeto(2, "Checkpoint", "Checkpoint_01", 320, suelo_y - 32, 16, 32,
                     {"checkpoint_id": ("int", "0")}))
    o.append(_objeto(3, "Checkpoint", "Checkpoint_02", 640, suelo_y - 32, 16, 32,
                     {"checkpoint_id": ("int", "1")}))
    # Dos y no tres, por lo mismo que los coleccionables: con tres la plantilla
    # llenaba la categoría y empataba con `stage0`. Dos bastan para enseñar el
    # concepto —y que `checkpoint_id` va correlativo—; colocar el resto según
    # dónde duela morir es justo la decisión de diseño que el estudiante tiene
    # que aprender a tomar.
    o.append(_objeto(4, "NextTrigger", "NextTrigger_01", 928, suelo_y - 64, 16, 64))

    # -- el suelo inclinado, que ya traía la plantilla anterior ------
    o.append(_objeto(5, "Slope", "Slope_sube", 176, suelo_y - 48, 48, 48,
                     {"sube": ("", "derecha")}))
    o.append(_objeto(6, "Slope", "Slope_baja", 224, suelo_y - 48, 48, 48,
                     {"sube": ("", "izquierda")}))

    # -- un enemigo de cada arquetipo -------------------------------
    #
    # Los tres básicos y no especies del bestiario: `Walker`, `Flying` y
    # `Shooter` son los que la guía explica primero y los que un estudiante
    # puede sustituir por los suyos sin tocar nada más.
    o.append(_objeto(7, "Walker", "Walker_ejemplo_01", 400, suelo_y - 32))
    o.append(_objeto(8, "Flying", "Flying_ejemplo_01", 500, suelo_y - 96))
    o.append(_objeto(9, "Shooter", "Shooter_ejemplo_01", 700, suelo_y - 32))

    # -- coleccionables ---------------------------------------------
    #
    # **Uno**, y aquí hay una lección que costó una prueba roja.
    #
    # La primera versión puso tres, que es lo que el calificador pide para la
    # puntuación completa de la categoría. El resultado fue que la plantilla
    # sacó 100/100 — y `test_teaching_tools` saltó con el mensaje exacto:
    # «stage0 saca 100 % y la plantilla vacía 100 %: la rúbrica no distingue
    # trabajo hecho de trabajo sin hacer».
    #
    # Tenía razón. Una plantilla que saca la nota máxima deja al estudiante sin
    # nada que mejorar y convierte la rúbrica en un adorno. El objetivo de este
    # fichero es **demostrar** cada tipo, no **llenar** la rúbrica: uno de cada
    # cosa enseña igual de bien y deja el margen donde tiene que estar.
    #
    # `item_id` es obligatorio: sin él el cargador lo ignora con un aviso.
    o.append(_objeto(10, "Pickup", "Pickup_ejemplo_01", 256, suelo_y - 32,
                     16, 16, {"item_id": ("", "moneda")}))

    # -- lo que enseña el resto del motor ---------------------------
    o.append(_objeto(13, "Light", "Light_ejemplo_01", 352, suelo_y - 96, 16, 16,
                     {"radius": ("float", "96"), "color": ("", "#ffd9a0"),
                      "intensity": ("float", "0.8")}))
    o.append(_objeto(14, "MessageTrigger", "Mensaje_bienvenida", 96, suelo_y - 64,
                     32, 64, {"text": ("", "Bienvenido. Edita este mensaje.")}))
    # La zona de daño va en `Objects`, **no** en `Collision`: puesta en la capa
    # de colisión el motor la trata como suelo sólido y deja de hacer daño.
    o.append(_objeto(15, "HazardZone", "Pinchos_ejemplo", 560, suelo_y - 16, 48, 16,
                     {"damage": ("float", "0.25")}))
    # AUD-400 — un objetivo declarado. Sin `objective_id` y `text` se ignora.
    o.append(_objeto(16, "Objective", "Objetivo_principal", 48, suelo_y - 96,
                     None, None,
                     {"objective_id": ("", "llegar_al_final"),
                      "text": ("", "Llega al final del nivel"),
                      "kind": ("", "llegar")}))

    return (
        ' <objectgroup id="6" name="Objects">\n' + "".join(o) + " </objectgroup>\n"
    )


def _colision() -> str:
    """La capa `Collision`: sólo `Solid` y `Platform`, que es lo que acepta.

    El suelo va partido en dos rectángulos por el hueco. Una plataforma de un
    sentido sobre el hueco da la ruta alternativa a quien no llegue de un
    salto — y de paso enseña el tipo `Platform`.
    """
    suelo_y = FILA_SUELO * TS
    x_hueco = HUECO_INICIO * TS
    ancho_hueco = (HUECO_FIN - HUECO_INICIO + 1) * TS
    alto_suelo = (ALTO - FILA_SUELO) * TS
    o = [
        _objeto(20, "Solid", "Solid_Floor_izq", 0, suelo_y, x_hueco, alto_suelo),
        _objeto(21, "Solid", "Solid_Floor_der", x_hueco + ancho_hueco, suelo_y,
                ANCHO * TS - (x_hueco + ancho_hueco), alto_suelo),
        _objeto(22, "Platform", "Platform_sobre_el_hueco",
                x_hueco + 8, suelo_y - 48, ancho_hueco - 16, 8),
    ]
    return ' <objectgroup id="7" name="Collision">\n' + "".join(o) + " </objectgroup>\n"


def generar() -> str:
    """El TMX completo, como cadena. Es lo que compara la prueba."""
    partes = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        f'<map version="1.10" tiledversion="1.11.0" orientation="orthogonal" '
        f'renderorder="right-down" width="{ANCHO}" height="{ALTO}" '
        f'tilewidth="{TS}" tileheight="{TS}" infinite="0" '
        f'nextlayerid="9" nextobjectid="30">\n',
        " <properties>\n",
        '  <property name="schema_version" value="1"/>\n',
        '  <property name="stage_id" value="stage_template"/>\n',
        '  <property name="stage_name" value="Untitled Stage"/>\n',
        # `author` la puntúa la rúbrica (`grade_stage.REQUIRED_GRADE_PROPS`) y
        # hasta AUD-416 ninguna herramienta se lo decía al estudiante. Viene
        # con un valor que pide ser cambiado, no vacío: un campo en blanco se
        # entrega en blanco.
        '  <property name="author" value="TU NOMBRE AQUI"/>\n',
        '  <property name="time_limit" type="int" value="120"/>\n',
        '  <property name="bgm_track" value="bgm_stage0"/>\n',
        '  <property name="climate" value="clear"/>\n',
        '  <property name="zone" type="int" value="1"/>\n',
        '  <property name="ambient_light" type="float" value="1.0"/>\n',
        " </properties>\n",
        f' <tileset firstgid="1" name="tileset_stage0" tilewidth="{TS}" '
        f'tileheight="{TS}" tilecount="1" columns="1">\n',
        f'  <image source="../../assets/tilesets/tileset_stage0.png" '
        f'width="{TS}" height="{TS}"/>\n',
        " </tileset>\n",
        _capa_vacia("BG_Far", 1),
        _capa_vacia("BG_Mid", 2),
        _capa_vacia("BG_Near", 3),
        _capa_terreno(4),
        _capa_vacia("Terrain_Detail", 5),
        _objetos(),
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
    DESTINO.write_text(texto, encoding="utf-8")
    print(f"escrito {DESTINO} ({len(texto.splitlines())} líneas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
