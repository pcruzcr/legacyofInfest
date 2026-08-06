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
    Sala 8   llave, puerta, resorte,
             interruptor y jaula        ← abrir cosas (AUD-153)
    Sala 9   hielo, onda de choque
             y una escena               ← el suelo también es mecánica

AUD-153 — las salas 8 y 9, y la fauna
======================================
Diecisiete tipos de objeto que el cargador reconoce no aparecían en **ningún**
mapa del juego: siete de escenario —`Key`, `Door`, `Cage`, `EventTrigger`,
`Spring`, `FrictionZone`, `ShockwaveZone`, `Cutscene`— y diez especies del
bestiario.

Es la versión más barata del fallo que este proyecto lleva un mes cazando. No
es código roto: es código que nadie recorre. Una regresión en `_handle_cerradura`
no la habría visto nadie hasta que un estudiante pusiera su primera puerta en
Tiled y no funcionara, que es el peor momento posible para descubrirlo.

Van al laboratorio y no repartidos por los escenarios de zona 1 a 3 porque
esos mapas los escribieron catorce estudiantes, y cambiar la población de un
nivel ajeno es una decisión de diseño de su autor. El laboratorio es el mapa
del profesor y su trabajo es justo éste.

Esto los hace **alcanzables y ejercitados**. No arregla la curva de dificultad
del juego; eso está medido aparte en `docs/67_CURVA_DE_DIFICULTAD.md`.
"""
from __future__ import annotations

import sys
from pathlib import Path

# AUD-177: imprime `←` y la consola de Windows usa cp1252, que no lo tiene.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESTINO = PROJECT_ROOT / "assets" / "maps" / "stage_mecanicas" / "stage_mecanicas.tmx"
TILESET = "../../tilesets/tileset_stage0.png"

TS = 16
# AUD-258: 280 → 310 para meter la sala 10, la del scroll forzado. `ScrollZone`
# se declaró en AUD-249 y **ningún mapa lo colocaba**, así que la mecánica era
# inalcanzable jugando y `test_todos_los_tipos_se_usan` estaba en rojo. Es el
# mismo remedio que AUD-153 aplicó a los diecisiete tipos huérfanos: el
# laboratorio es el mapa del profesor y su trabajo es ser donde todo lo que el
# motor sabe hacer se puede ver.
MW, MH = 310, 24          # 4960 × 384 px
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
    for sala in range(1, 10):
        for x in range(sala * SALA - 4, sala * SALA + 4):
            g[SUELO_Y - 5][x] = PLATAFORMA

    # Sala 8 — repisa alta a la que sólo se llega con el resorte. Es lo que
    # convierte el resorte en algo que hay que usar y no en un adorno que se
    # pisa de paso.
    for x in range(7 * SALA + 17, 7 * SALA + 23):
        g[SUELO_Y - 7][x] = PLATAFORMA
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
                    # Los saltos de línea van como `&#10;` y no como carácter.
                    #
                    # AUD-153: un XML normaliza los espacios en blanco dentro
                    # de un valor de atributo, así que un `\n` literal se
                    # convierte en un espacio al leerlo. El guion de la
                    # `Cutscene` llegaba al motor como **una sola línea** —
                    # «camara 4400 200 0.8 temblor 0.3 5 …»— y ninguna de sus
                    # órdenes se entendía. Lo escribí, lo cargué y lo vi; sin
                    # imprimir el guion cargado habría dado la escena por buena.
                    # La referencia de carácter sobrevive a la normalización.
                    texto = (str(v).replace("&", "&amp;").replace("<", "&lt;")
                             .replace('"', "&quot;").replace("\n", "&#10;"))
                    cuerpo += f'\n    <property name="{k}" value="{texto}"/>'
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

    # ── Sala 7 bis: bloques que se empujan y que se rompen ────
    #
    # AUD-140. Van juntos a proposito: el empujable sirve de escalon y el
    # destructible tapa lo que hay detras, asi que la sala se lee sola —hay
    # que colocar uno para llegar a golpear el otro—.
    obj("MessageTrigger_Once", (6 * SALA + 25) * TS, suelo_px - 64, 48, 48,
        text="Uno se empuja. El otro se rompe a golpes.")
    obj("PushBlock", (6 * SALA + 27) * TS, suelo_px - 2 * TS, 2 * TS, 2 * TS,
        velocidad=45.0)
    obj("BreakableBlock", (6 * SALA + 33) * TS, suelo_px - 4 * TS, TS, 2 * TS,
        golpes=3)
    obj("BreakableBlock", (6 * SALA + 33) * TS, suelo_px - 2 * TS, TS, 2 * TS,
        golpes=1)

    # ── Sala 8: llave, puerta, resorte, interruptor y jaula ───
    #
    # AUD-153. Los cinco tipos de esta sala estaban escritos en el cargador,
    # con pruebas unitarias, y **ningún mapa del juego los colocaba**. Es la
    # forma más barata del fallo que este proyecto lleva un mes cazando: no
    # código roto, sino código que nadie recorre, de modo que una regresión en
    # `_handle_cerradura` no la habría visto nadie hasta que un estudiante
    # pusiera su primera puerta y no funcionara.
    #
    # La sala se lee sola y en un orden: la llave está antes que la puerta, el
    # resorte es la única forma de llegar al interruptor, y el interruptor es
    # la única forma de abrir la jaula.
    s8 = 7 * SALA
    obj("MessageTrigger_Once", (s8 + 2) * TS, suelo_px - 64, 48, 48,
        text="Coge la llave. La puerta la pide.")
    obj("Key", (s8 + 5) * TS, suelo_px - 2 * TS, TS, TS,
        key_id="llave_lab", nombre="Llave del laboratorio")
    obj("Door", (s8 + 11) * TS, suelo_px - 3 * TS, TS, 3 * TS,
        key_id="llave_lab", consume_llave=True,
        mensaje="Cerrada. Falta la llave.")
    # El resorte sube a la repisa alta; sin él no se alcanza el interruptor.
    obj("Spring", (s8 + 14) * TS, suelo_px - TS, 2 * TS, TS,
        impulso=-560.0, rearme=0.2)
    obj("EventTrigger", (s8 + 19) * TS, (SUELO_Y - 8) * TS, 2 * TS, TS,
        evento="ABRIR_JAULA", automatico=True, una_vez=True)
    obj("Cage", (s8 + 25) * TS, suelo_px - 3 * TS, 2 * TS, 3 * TS,
        abre_con="ABRIR_JAULA", mensaje="La jaula no cede a golpes.")
    obj("Checkpoint", (8 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=7)

    # ── Sala 9: hielo, onda de choque y una escena ────────────
    #
    # La `FrictionZone` con multiplicador bajo es hielo: el jugador conserva la
    # velocidad y frena tarde, así que la onda de choque que viene después
    # castiga entrar corriendo. Las dos juntas enseñan lo mismo que por
    # separado no se ve — que el suelo también es una mecánica.
    s9 = 8 * SALA
    obj("MessageTrigger_Once", (s9 + 2) * TS, suelo_px - 64, 48, 48,
        text="Aqui no se frena. Y algo golpea el suelo.")
    obj("FrictionZone", (s9 + 5) * TS, suelo_px - 2 * TS, 12 * TS, 2 * TS,
        multiplicador=0.25, arrastre=0.0)
    obj("ShockwaveZone", (s9 + 18) * TS, suelo_px - TS, 6 * TS, TS,
        dano=99.0, encendido=0.7, apagado=2.6, desfase=0.0)
    obj("ShockwaveZone", (s9 + 24) * TS, suelo_px - TS, 6 * TS, TS,
        dano=99.0, encendido=0.7, apagado=2.6, desfase=1.65)
    # `Cutscene` como rectángulo: se dispara al entrar. Es corta y saltable a
    # propósito — una escena que quita el mando en un mapa de laboratorio sería
    # justo el ejemplo que no hay que copiar.
    obj("Cutscene", (s9 + 28) * TS, suelo_px - 4 * TS, 2 * TS, 4 * TS,
        guion="camara 4400 200 0.8\ntemblor 0.3 5\n+ evento LAB_COMPLETADO",
        bloquea=False, saltable=True, una_vez=True)

    # ── Sala 10: el nivel dice «sígueme» ──────────────────────
    #
    # AUD-258. `ScrollZone` (AUD-249) es la única mecánica del motor que le
    # quita al jugador el control del ritmo: se pisa el rectángulo y a partir
    # de ahí manda la cámara; quien se queda atrás muere contra el borde
    # izquierdo. Estaba escrita, probada y **en ningún mapa**.
    #
    # La sala está acotada a propósito, y ésa es la decisión de diseño:
    # `parar_en_x` detiene la cámara antes de la salida, así que el tramo con
    # presión dura lo que dura la sala y el laboratorio no se vuelve hostil
    # para quien viene a leer un cartel. El checkpoint va **antes** del
    # disparador: morir aquí tiene que costar el tramo, no la sala anterior.
    s10 = 9 * SALA
    obj("Checkpoint", (s10 + 1) * TS, suelo_px - 32, 16, 32, checkpoint_id=8)
    obj("MessageTrigger_Once", (s10 + 3) * TS, suelo_px - 64, 48, 48,
        text="La camara arranca sola. No te quedes atras.")
    obj("ScrollZone", (s10 + 6) * TS, suelo_px - 4 * TS, 2 * TS, 4 * TS,
        velocidad_x=38.0, margen_de_gracia=28.0,
        parar_en_x=float((s10 + 26) * TS))
    # Dos repisas dentro del tramo: sin nada que hacer, el scroll forzado es
    # sólo una caminata con prisa. Con ellas hay que decidir si se sube o se
    # rodea, que es lo que la mecánica enseña.
    obj("MovingPlatform", (s10 + 12) * TS, suelo_px - 3 * TS, 3 * TS, 8,
        dx=0.0, dy=-48.0, velocidad=34.0, espera=0.4)
    obj("Spring", (s10 + 19) * TS, suelo_px - TS, 2 * TS, TS,
        impulso=-520.0, rearme=0.2)

    # ── La cuesta ─────────────────────────────────────────────
    #
    # AUD-297. Hasta aquí, una cuesta había que fingirla apilando bloques
    # escalonados, y eso no es una cuesta: es una escalera que frena al jugador
    # en cada peldaño. `Slope` es suelo de verdad, con su hipotenusa.
    #
    # Van dos, subiendo y bajando, y pegadas: bajar es el caso que se rompe
    # solo si nadie lo prueba —el jugador desciende a saltitos— y ponerlas
    # juntas obliga a que el laboratorio lo enseñe.
    s11 = 2 * SALA + 4
    obj("Slope", s11 * TS, suelo_px - 3 * TS, 3 * TS, 3 * TS, sube="derecha")
    obj("Slope", (s11 + 3) * TS, suelo_px - 3 * TS, 3 * TS, 3 * TS,
        sube="izquierda")
    obj("MessageTrigger_Once", (s11 - 2) * TS, suelo_px - 64, 48, 48,
        text="Una cuesta de verdad. Subela y bajala.")

    # ── El atajo de vuelta ────────────────────────────────────
    #
    # AUD-287. `WarpZone` teletransporta **dentro del mismo mapa**, que es lo
    # único que faltaba para conectar los extremos de un nivel grande: hasta
    # ahora `NextTrigger` cambiaba de escenario y `Door` abría un paso, y no
    # había nada entre medias.
    #
    # Aquí se coloca donde el laboratorio lo pide de verdad: el mapa mide 4.960
    # px y quien llega al final y quiere volver a leer un cartel de la sala 2
    # tiene que caminar los diez tramos otra vez. El warp del final devuelve a
    # la entrada; el de la entrada lleva a la sala 5, que es la mitad.
    #
    # Los dos son manuales (`automatico=false`). Un warp automático en un
    # corredor por el que se pasa andando se dispara sin querer, y en un mapa
    # que además tiene scroll forzado eso sería una trampa.
    obj("WarpZone", (MW - 8) * TS, suelo_px - 3 * TS, 2 * TS, 3 * TS,
        automatico=False, destino_x=float(3 * TS), destino_y=float(suelo_px),
        mensaje="De vuelta a la entrada.")
    obj("WarpZone", 5 * TS, suelo_px - 3 * TS, 2 * TS, 3 * TS,
        automatico=False, destino_x=float((5 * SALA - 4) * TS),
        destino_y=float(suelo_px), mensaje="Atajo a la mitad del laboratorio.")

    # Salida
    obj("NextTrigger", (MW - 4) * TS, suelo_px - 3 * TS, 2 * TS, 3 * TS)

    # ── La fauna que nadie había visto ────────────────────────
    #
    # AUD-153. Diez especies del bestiario estaban registradas, con sus
    # parámetros y sus pruebas, y no aparecían en un solo TMX del juego: el
    # jugador no las ha visto nunca y el cargador no las había construido
    # nunca desde un mapa real.
    #
    # Van aquí y no repartidas por los escenarios de zona 1 a 3 porque esos
    # mapas los escribieron catorce estudiantes: cambiar la población de un
    # nivel ajeno es una decisión de diseño de su autor, no mía. El
    # laboratorio es el mapa del profesor y su trabajo es exactamente éste,
    # ser el sitio donde todo lo que el motor sabe hacer se puede ver.
    #
    # Esto las hace **alcanzables y ejercitadas**; no arregla la curva de
    # dificultad del juego (ver `docs/67_CURVA_DE_DIFICULTAD.md`).
    fauna = [
        ("WalkerInsect", 1, 20), ("WalkerRaton", 2, 20),
        ("FlyingCucaracha", 2, 12), ("WalkerEstudiante", 3, 24),
        ("FlyingNotebook", 3, 6), ("ShooterTiza", 4, 26),
        ("ShooterCocinero", 5, 26), ("WalkerTerciopelo", 6, 27),
        ("FlyingTerciovolador", 7, 8), ("ShooterVenomoLargo", 8, 10),
    ]
    for especie, sala, dx in fauna:
        x = (sala * SALA + dx) * TS
        if especie.startswith("Flying"):
            obj(especie, x, suelo_px - 6 * TS, 20, 14)
        else:
            obj(especie, x, suelo_px - 28, 24, 28)

    # Los dos de siempre, para que el escenario no sea sólo un museo.
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
    for sala in range(1, 9):
        solido((sala * SALA - 4) * TS, (SUELO_Y - 5) * TS, 8 * TS, 8, "Platform")
    # Sala 8 — la repisa del resorte, con el interruptor encima.
    solido((7 * SALA + 17) * TS, (SUELO_Y - 7) * TS, 6 * TS, 8, "Platform")
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
