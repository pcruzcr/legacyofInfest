#!/usr/bin/env python3
"""
Genera `assets/maps/stage4_1/stage4_1.tmx` — La Entrada al Cementerio.

El nivel, en una frase
=======================
Un **descenso** de 240 filas sin un solo enemigo y sin una sola trampa mortal,
donde el fondo avanza con el jugador: cada tramo enciende braseros, sube la
tormenta y acerca las siluetas. La ficha (`docs/niveles/13_STAGE_4_1.md`) lo
llama «travesía atmosférica»; el diseño (`15_DISENO_4_1_EL_CEMENTERIO.md`) lo
estructura en cinco actos con la pelea de Magus como referencia.

Qué cambió, y por qué (AUD-225)
--------------------------------
El nivel era horizontal y tenía siete `DeathPit`. Jugado no funcionaba:

* **Los fosos contradecían la ficha.** «Travesía atmosférica», sin enemigos,
  porque *«la tensión ya está»*. Siete agujeros mortales lo convertían en un
  nivel de memorizar caídas. **Ya no hay ninguno.**
* **Las `HazardZone` no se veían.** El motor sólo pinta las que suben (la
  inundación de AUD-135); una fija espera a que el diseñador dibuje pinchos en
  las baldosas, y aquí no había ninguno. Se recibía daño de la nada.
  **Ya no hay ninguna.** Las grietas siguen ahí, pero como luz verde que dibuja
  la escena y que no hace daño.
* **Un cementerio se baja, no se cruza.** Ahora es un pozo de 60 × 240.

Lo que sustituye al peligro son **superficies que se ven**: musgo que arrastra
hacia el hueco y lodo que frena, cada una con su baldosa. La regla es que nada
cambie el movimiento del jugador sin que se vea por qué.

Por qué se genera con código
-----------------------------
Igual que `generate_stage0_tmx.py` y `generate_stage_mecanicas.py`: un TMX a
mano son miles de números en CSV que nadie puede revisar en un *pull request*.
Generado, el diff es de diez líneas de Python y se lee lo que cambió.

Los cinco actos, y en qué fila empieza cada uno
-----------------------------------------------
    0-47     I   La Entrada                el brocal, suelo firme, primer salto
    48-95    II  El Sendero de los Nombres las lápidas con los nombres
    96-143   III La Niebla que Respira     aparece el musgo: arrastra
    144-191  IV  La Tormenta               lluvia, rayos, viento y lodo
    192-239  V   El Umbral                 el fondo del pozo y «LA PRUEBA»

Aquí sólo se coloca **lo que es geometría**; el clima, la luna, los rayos y las
siluetas los mueve la escena. Las columnas y filas de cada cosa viven en
`src/stages/stage4_1/trazado.py`, que es también de donde las lee la escena.

La regla de oro: **cero enemigos**
-----------------------------------
No se coloca ni uno. `tests/test_stage4_1.py` lo comprueba cargando el mapa y
contando `entity_list`, no leyendo el XML: un enemigo colocado por una
propiedad rara también contaría.

Sobre el «Portal» de la ficha
------------------------------
La ficha pide «1 `Portal`». Ese tipo **no existe en el motor** — la auditoría
de documentación ya lo tenía señalado. La salida de un escenario es
`NextTrigger`, que es lo que se coloca aquí.
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

# El trazado —dónde está cada repisa, cada brasero y cada lápida— es el mismo
# objeto que lee la escena. Ver la cabecera de `trazado.py`: cuando eran dos
# listas, la huella de la visión espectral acabó flotando sobre el vacío.
from src.stages.stage4_1.trazado import (  # noqa: E402
    ALTO_ACTO,
    ANCHO_LOSA_EXTRA,
    ARRASTRE_DEL_MUSGO,
    DESFASE_RITMICO,
    EPITAFIOS,
    FRENO_DEL_LODO,
    GOLPES_DE_LA_LOSA,
    GROSOR_REPISA,
    INDICES_FANTASMA,
    INDICES_RITMICAS,
    INDICES_ROMPIBLES,
    MH,
    MURO_ANCHO,
    MW,
    PATRON_RITMICO,
    SUELO_FINAL,
    TS,
    braseros,
    checkpoints,
    losa_extra,
    repisas,
    superficies,
)

DESTINO = PROJECT_ROOT / "assets" / "maps" / "stage4_1" / "stage4_1.tmx"

# AUD-237: el nivel pintaba su suelo con `tileset_stage0.png`, la piedra del
# castillo del prólogo, mientras `tileset_cemetery.png` existía sin que lo usara
# nadie. No era un descuido: la hoja del cementerio eran ocho baldosas genéricas
# —piedra lisa, tablones, ladrillo rojo— repetidas, y cambiar a ella habría hecho
# que el nivel se viera **peor**. Ahora la hoja se dibuja de verdad
# (`_gen_tileset_cementerio`) y el cementerio pisa su propia piedra.
TILESET = "../../tilesets/tileset_cemetery.png"

# ── Baldosas ────────────────────────────────────────────────────────────────
# La cabecera describe la hoja real: 128x128 px, 8 columnas, 64 baldosas.
# Inventarla es lo que dejó `stage_mecanicas` pintando las tres primeras
# baldosas de la hoja durante semanas (AUD-115).
TS_COLUMNAS = 8
TS_TOTAL = 64
TS_IMAGEN_PX = 128

# Los GID son `índice + 1` sobre `CEM_ORDEN` de `tools/generate_all_assets.py`.
# Esa lista y estos números son un contrato: cambiar el orden allí sin cambiarlo
# aquí repinta el nivel entero con las baldosas equivocadas, y hay una prueba
# que compara las dos listas para que no pase.
VACIO = 0
PIEDRA = 2                # la losa que se pisa
RELLENO = 3               # tierra bajo la superficie
MURO = 4                  # piedra de cierre del pozo
LOSA = 10                 # lápida — el cuerpo

# Las dos superficies que cambian el movimiento. Son **la misma losa con otra
# cosa encima**, a propósito: si fueran tres materiales distintos el jugador
# leería «tres suelos», y siendo piedra cubierta lee «esta losa está tomada»,
# que es lo que explica por qué resbala. Una superficie que cambia el
# movimiento y se ve igual que el suelo normal es una trampa, y este nivel no
# tiene trampas.
MUSGO = 5                 # losa con musgo y matas — arrastra
MUSGO_RELLENO = 6
LODO = 7                  # losa con barro y raíces — frena
LODO_RELLENO = 8
LAPIDA_ALTA = 9           # la cabeza redondeada, con inscripción

#: Qué baldosa pinta cada material, en `(superficie, relleno)`.
BALDOSAS = {
    "piedra": (PIEDRA, RELLENO),
    "musgo": (MUSGO, MUSGO_RELLENO),
    "lodo": (LODO, LODO_RELLENO),
}


def _terreno() -> list[list[int]]:
    """La geometría del pozo, repisa a repisa."""
    g = [[VACIO] * MW for _ in range(MH)]

    # Los dos muros del pozo, de arriba abajo. El cementerio está cerrado: no
    # se sale por los lados, se baja.
    for y in range(MH):
        for x in range(MURO_ANCHO):
            g[y][x] = MURO
            g[y][MW - 1 - x] = MURO

    # El techo: el brocal por el que se entra.
    for x in range(MURO_ANCHO, MW - MURO_ANCHO):
        g[0][x] = MURO

    # Las repisas, cada una con su material a la vista.
    for x0, ancho, fila, material in superficies():
        arriba, abajo = BALDOSAS[material]
        for x in range(x0, x0 + ancho):
            g[fila][x] = arriba
            for d in range(1, GROSOR_REPISA):
                g[fila + d][x] = abajo

    # El suelo del umbral: firme, de pared a pared.
    for y in range(SUELO_FINAL, MH):
        for x in range(MURO_ANCHO, MW - MURO_ANCHO):
            g[y][x] = PIEDRA if y == SUELO_FINAL else RELLENO

    # Las lápidas de los nombres, apoyadas en su repisa.
    lista = repisas()
    for indice, _texto in EPITAFIOS:
        x0, ancho, fila = lista[indice]
        cx = x0 + ancho // 3
        g[fila - 1][cx] = LOSA          # el cuerpo, apoyado en la repisa
        g[fila - 2][cx] = LAPIDA_ALTA   # la cabeza con la inscripción

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

    # Muros laterales. No hay techo de colisión: un rectángulo por encima de la
    # fila 0 lo cuenta el calificador como una plataforma a la que no llega
    # nadie, y no hace falta — arriba del brocal no hay nada a donde ir.
    solido(0, 0, MURO_ANCHO * TS, MH * TS)
    solido((MW - MURO_ANCHO) * TS, 0, MURO_ANCHO * TS, MH * TS)

    # Las repisas. Son `Solid` y no `Platform` a propósito. Una `Platform` se
    # atraviesa desde abajo, y aquí se cae desde arriba a 400 px/s sobre una
    # repisa de 16 px de grosor: es justo la situación en la que un colisionador
    # de un solo sentido se atraviesa por velocidad. `Solid` para en los dos
    # sentidos y el precio —darse en la cabeza al saltar debajo de una— se paga
    # una vez y se entiende.
    for x0, ancho, fila in repisas():
        solido(x0 * TS, fila * TS, ancho * TS, GROSOR_REPISA * TS)

    # Las losas fantasma del acto IV: sólidas y sin baldosa que las pinte. Se
    # ven sólo con el relámpago o con la visión espectral (AUD-247).
    for indice in INDICES_FANTASMA:
        cx, fila = losa_extra(indice)
        solido(cx * TS, fila * TS, ANCHO_LOSA_EXTRA * TS, TS)

    # El suelo del umbral.
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

    # ── Los mensajes: uno al entrar en cada acto ──────────────
    #
    # Van a la altura de la primera repisa de su acto, no en la fila del
    # umbral: un disparador colocado en el aire no lo cruza nadie.
    textos = {
        1: "El cementerio no ataca. Testifica.",
        2: "Los nombres de los que bajaron antes.",
        3: "El musgo tira hacia el hueco. Dejate llevar.",
        4: "No te pares. El lodo frena y el viento empuja.",
        5: "Silencio. Los doce arden.",
    }
    vistos: set[int] = set()
    for x0, ancho, fila in lista:
        acto = min(5, fila // ALTO_ACTO + 1)
        if acto in vistos:
            continue
        vistos.add(acto)
        obj("MessageTrigger_Once", (x0 + ancho // 2) * TS, (fila - 3) * TS,
            48, 48, text=textos[acto])

    # ── Los doce braseros ─────────────────────────────────────
    #
    # Cada uno es una luz de Tiled. El motor las coloca desde el centro del
    # rectángulo. `flicker` las hace respirar: un fuego que no parpadea se lee
    # como una bombilla.
    fuegos = braseros()
    for i, (bx, fila) in enumerate(fuegos):
        ultimo = i == len(fuegos) - 1
        obj("Light", bx * TS, (fila - 3) * TS, 2 * TS, 2 * TS,
            radius=160.0 if ultimo else 100.0,
            color="#7CFFA0",          # verde espectral: el color del canon
            intensity=0.95 if ultimo else 0.75,
            flicker=True, flicker_speed=2.2, flicker_amount=0.28)

    # ── Los puntos de reaparición ─────────────────────────────
    #
    # Uno por brasero. El descenso es de un solo sentido —96 px entre repisas
    # contra 90 de salto—, así que sin ellos un error costaría el pozo entero.
    for i, (cx, fila) in enumerate(checkpoints(), start=1):
        obj("Checkpoint", cx * TS, (fila - 2) * TS, 16, 32, checkpoint_id=i)

    # ── Las superficies que mueven al jugador ─────────────────
    #
    # Ni una hace daño. El musgo arrastra hacia el hueco de su repisa y el lodo
    # frena; las dos están pintadas con su baldosa, así que se ve por qué.
    for x0, ancho, fila, material in superficies():
        if material == "musgo":
            # Hacia el hueco: si la repisa empieza en el muro, el hueco está a
            # la derecha, y al revés.
            sentido = 1.0 if x0 == MURO_ANCHO else -1.0
            obj("FrictionZone", x0 * TS, (fila - 2) * TS, ancho * TS, 2 * TS,
                arrastre=ARRASTRE_DEL_MUSGO * sentido)
        elif material == "lodo":
            obj("FrictionZone", x0 * TS, (fila - 2) * TS, ancho * TS, 2 * TS,
                multiplicador=FRENO_DEL_LODO)

    # ── Acto IV — el viento de la tormenta ────────────────────
    #
    # Empuja hacia el centro del pozo, nunca contra una pared: el viento tiene
    # que hacer que la tormenta se note, no que el descenso se pierda.
    obj("WindZone", MURO_ANCHO * TS, 3 * ALTO_ACTO * TS,
        (MW - 2 * MURO_ANCHO) * TS, ALTO_ACTO * TS,
        fuerza_x=-70.0, fuerza_y=0.0, periodo=3.2)

    # ── Las lápidas con los nombres ───────────────────────────
    for indice, texto in EPITAFIOS:
        x0, ancho, fila = lista[indice]
        obj("MessageTrigger_Once", (x0 + ancho // 3) * TS, (fila - 3) * TS,
            2 * TS, 3 * TS, text=texto)

    # ── Lo que hace que el pozo dé miedo (AUD-247) ────────────
    #
    # Tres ideas, una por acto, y ninguna hace daño. Todas van en el hueco de su
    # repisa y ninguna lo tapa entero: siempre se puede bajar por al lado.

    # Acto II — losas de tumba que se rompen a golpes. El motor las pinta con
    # grietas que cuentan lo que queda, así que golpear da señal de avance.
    for indice in INDICES_ROMPIBLES:
        cx, fila = losa_extra(indice)
        obj("BreakableBlock", cx * TS, fila * TS, ANCHO_LOSA_EXTRA * TS, TS,
            golpes=GOLPES_DE_LA_LOSA)

    # Acto III — el tramo musical. `patron` manda sobre los segundos, y con
    # `bpm = 60` un pulso es un segundo: los cuatro del patrón son un acorde
    # entero del órgano, así que la losa entra y sale **con la música**.
    for orden, indice in enumerate(INDICES_RITMICAS):
        cx, fila = losa_extra(indice)
        obj("RhythmBlock", cx * TS, fila * TS, ANCHO_LOSA_EXTRA * TS, TS,
            patron=PATRON_RITMICO,
            desfase=orden * DESFASE_RITMICO)

    # Acto IV — las losas fantasma. Sólidas y **sin baldosa**: no se ven hasta
    # que un relámpago las enseña o la visión espectral las revela. La colisión
    # va en `_colisiones()`; aquí no hay nada que poner, y ése es el punto.

    # ── Acto V — El Umbral ────────────────────────────────────
    #
    # La lápida central. No lleva nombre: lleva la inscripción del diseño (§7).
    obj("MessageTrigger_Once", (MW // 2 - 6) * TS, (SUELO_FINAL - 5) * TS,
        2 * TS, 5 * TS, text="LA PRUEBA")

    # La salida al 4-2, al fondo del pozo.
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
  <property name="stage_name" value="4-1  LA ENTRADA AL CEMENTERIO"/>
  <property name="author" value="Equipo docente — Legacy of Infest"/>
  <!-- AUD-209: aquí ponía `bgm_zone3` y `stage0`, o sea la música de la zona 3
       y el fondo del prólogo. Las dos cosas ya tenían dueño en el Asset Bible
       (`docs/20_ASSET_BIBLE.md`): `bgm_final_approach.wav` está listado como
       «Stage 4-1» y las capas del cementerio son `final/bg_final_*.png`. -->
  <property name="bgm_track" value="bgm_final_approach"/>
  <property name="background_zone" value="final"/>
  <!-- El clima ARRANCA en niebla y lo cambia la escena por acto: fog al
       principio, storm en el acto IV, clear en el umbral. -->
  <!-- AUD-247: el compás del nivel. Sin `bpm` no hay reloj musical y el
       `patron` de los bloques rítmicos no se puede seguir (AUD-137). 60 pulsos
       por minuto es un pulso por segundo, y cuatro pulsos son los cuatro
       segundos que dura cada acorde del órgano: las losas del acto III entran y
       salen con la música que suena, no con un temporizador que coincide. -->
  <property name="bpm" type="float" value="60"/>
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
       protege de que la noche haga imposible ver los cantos. -->
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
    musgo = sum(1 for *_, m in superficies() if m == "musgo")
    lodo = sum(1 for *_, m in superficies() if m == "lodo")
    print(f"escrito {DESTINO.relative_to(PROJECT_ROOT)} "
          f"({MW}×{MH} baldosas, {len(repisas())} repisas, "
          f"{len(braseros())} braseros, {musgo} de musgo, {lodo} de lodo, "
          f"0 enemigos, 0 fosos, 0 zonas de daño)")


if __name__ == "__main__":
    main()
