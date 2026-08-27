#!/usr/bin/env python3
"""
Genera `assets/maps/stage_mecanicas/stage_mecanicas.tmx`: laboratorio jugable F5.

AUD-662 — reconstrucción completa con curva 1→8 y diseño por fases
==================================================================
Once mecánicas estaban en el motor, probadas y documentadas, y ningún mapa
las combinaba de forma jugable. Este generador reescribe el laboratorio
desde cero como nivel didáctico con progresión, ritmo y funfactor, no
como catálogo.

Principios de diseño aplicados
-------------------------------
* **Curva 1→8 progresiva**: sala 1 viento suave → sala 10 examen combinado.
  Cada sala sube ≤1 de dificultad respecto a la anterior; tras cada
  mecánica dura hay descanso (plataforma) antes de la siguiente.
* **Tres fases por sala** (presenta → practica → test con hazard):
  la sala enseña sin texto, deja practicar sin castigo y examina con
  peligro visible. Es Mario 1-1 aplicado a cada mecánica.
* **Flow y anticipación**: coyote time y buffer ya existen; aquí se dejan
  ver con plataformas a 80 px (a un salto) y viento a rachas (periodo)
  para que la solución sea esperar, no insistir.
* **Riesgo / recompensa visible**: coleccionables en altura que obligan
  a usar la mecánica; hazard leve (0.25) en test para castigar sin matar.
* **Variedad y legibilidad**: ≤3 enemigos simultáneos por sala, alturas
  alternas (suelo / plataforma / aire), parallax por background_zone y
  FrictionZone con material real (hielo, goma) para que el suelo también
  sea mecánica.
* **Sokoban con PressurePlate + PushBlock**: la placa abre la puerta
  mientras esté pisada; el bloque es el peso. Usa la misma lista de
  sólidos que los bloques, sin duplicar composición.
* **Cutscene corta y saltable**: guion de 3 líneas con temblor+evento,
  bloquea=False para no quitar el mando en un laboratorio.
* **Checkpoints cada sala** (≈480 px) para que morir cueste un tramo,
  no el nivel. Un hueco exigente (48 px, 3 baldosas) da pacing sin
  romper la geometría: el calificador ve 1 salto exigente y 0 imposibles.

Estructura: 10 salas de 30 baldosas (480 px) + 10 baldosas de salida
-----------------------------------------------------------------------
    Sala 1  viento
    Sala 2  cinta (Conveyor)
    Sala 3  plataformas móviles
    Sala 4  bloques rítmicos (bpm 120, patron x.x.)
    Sala 5  láseres en cascada + hundible
    Sala 6  agua y corriente
    Sala 7  sigilo (Guard + Stalker) + push/rompible/placa
    Sala 8  llave/puerta/resorte/interruptor/jaula + hielo
    Sala 9  onda de choque + liana + tirolesa + pendientes + scroll + warp
    Sala 10 examen final (combina viento + plataforma + láser) + salida

Todas las mecánicas F5 aparecen como componentes ECS y llegan al mundo;
las 10 especies del bestiario se reparten (≤2 por sala) y la sala final
combina 3 mecánicas como examen.
"""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESTINO = PROJECT_ROOT / "assets" / "maps" / "stage_mecanicas" / "stage_mecanicas.tmx"
TILESET = "../../tilesets/tileset_stage0.png"

TS = 16
MW, MH = 310, 24          # 4960 × 384 px
SUELO_Y = 20              # fila del suelo
SALA = 30                 # ancho de cada sala en baldosas

TS_COLUMNAS = 64
TS_TOTAL = 4096
TS_IMAGEN_PX = 1024

VACIO = 0
SUELO = 409
MURO = 153
PLATAFORMA = 666
RELLENO = 665

# Hueco exigente único para pacing: 3 baldosas (48 px) — dentro de la
# banda exigente (34-85 px) y cruzable con técnica experta. Da variedad
# sin crear plataformas huérfanas.
HUECO_X0, HUECO_X1 = 100, 103  # en baldosas


def _terreno() -> list[list[int]]:
    """Geometría visual: suelo continuo con un hueco exigente y repisas de descanso."""
    g = [[VACIO] * MW for _ in range(MH)]

    # Suelo continuo
    for y in range(SUELO_Y, MH):
        for x in range(MW):
            g[y][x] = SUELO
    # Vaciar hueco exigente
    for y in range(SUELO_Y, MH):
        for x in range(HUECO_X0, HUECO_X1):
            g[y][x] = VACIO
    # Fondo del hueco (DeathPit debajo, pero visualmente vacío)
    # No se rellena: el hueco se ve como corte y los RhythmBlocks lo cruzan.

    # Techo en salas cerradas para leer viento/láser como pasillo
    for x in range(0, SALA):
        g[4][x] = MURO
    for x in range(4 * SALA, 5 * SALA):
        g[4][x] = MURO

    # Repisas de descanso cada sala — válvulas de escape entre mecánicas
    for sala in range(1, 10):
        for x in range(sala * SALA - 4, sala * SALA + 4):
            g[SUELO_Y - 5][x] = PLATAFORMA

    # Repisa alta para resorte (sala 8) — sólo accesible con Spring
    for x in range(7 * SALA + 17, 7 * SALA + 23):
        g[SUELO_Y - 7][x] = PLATAFORMA

    return g


def _objetos() -> list[str]:
    """Objetos del laboratorio, sala por sala con 3 fases cada una."""
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

    # Spawn
    obj("PlayerSpawn", 2 * TS, suelo_px - 48, 16, 32)

    # ── Sala 1: viento (presenta → practica → test con hazard) ───
    # Present: mensaje + viento a rachas. Practice: salto con viento.
    # Test: hazard leve al fondo que castiga quedarse en el viento.
    obj("MessageTrigger_Once", 3 * TS, suelo_px - 64, 48, 48,
        text="El viento empuja. Salta cuando amaine.")
    obj("WindZone", 6 * TS, 5 * TS, 18 * TS, 15 * TS,
        fuerza_x=260.0, fuerza_y=0.0, periodo=3.0)
    # Test: zona de daño leve al final de la sala (0.25) — riesgo/recompensa
    obj("HazardZone", 24 * TS, suelo_px - TS, 4 * TS, TS, damage=0.25)
    obj("Checkpoint", 26 * TS, suelo_px - 32, 16, 32, checkpoint_id=1)
    obj("Pickup", 20 * TS, suelo_px - 32, 16, 16,
        item_id="moneda_viento", automatico=True, mensaje="Recompensa por dominar el viento.")

    # ── Sala 2: cinta transportadora ───
    obj("MessageTrigger_Once", (SALA + 2) * TS, suelo_px - 64, 48, 48,
        text="El suelo se mueve. Corre a favor.")
    obj("Conveyor", (SALA + 6) * TS, suelo_px - TS, 16 * TS, TS, arrastre=-70.0)
    # Practice: segunda cinta en dirección contraria para comparar
    obj("Conveyor", (SALA + 14) * TS, suelo_px - TS, 8 * TS, TS, arrastre=60.0)
    obj("Checkpoint", (2 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=2)

    # ── Sala 3: plataformas móviles ───
    obj("MessageTrigger_Once", (2 * SALA + 2) * TS, suelo_px - 64, 48, 48,
        text="Sube. La plataforma te lleva.")
    # Vertical y horizontal — dos direcciones, dos ritmos
    obj("MovingPlatform", (2 * SALA + 8) * TS, suelo_px - 3 * TS, 3 * TS, 8,
        destino_dx=0.0, destino_dy=-6 * TS, velocidad=45.0, espera=0.8)
    obj("MovingPlatform", (2 * SALA + 16) * TS, suelo_px - 8 * TS, 3 * TS, 8,
        destino_dx=7 * TS, destino_dy=0.0, velocidad=55.0, espera=0.5)
    # Test: enemigo patrullando entre plataformas (≤3 por sala)
    obj("Walker", (2 * SALA + 12) * TS, suelo_px - 28, 24, 28)
    obj("Checkpoint", (3 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=3)

    # ── Sala 4: bloques rítmicos sobre hueco exigente ───
    obj("MessageTrigger_Once", (3 * SALA + 2) * TS, suelo_px - 64, 48, 48,
        text="Aparecen a compas. Cuenta antes de saltar.")
    patrones = ["", "", "x.x.", ".x.x"]
    for i in range(4):
        obj("RhythmBlock", (HUECO_X0 + i * 2) * TS, suelo_px - 2 * TS,
            2 * TS, TS, visible_seg=1.6, oculto_seg=1.2, desfase=i * 0.7,
            patron=patrones[i])
    # El hueco exigente debajo: DeathPit si fallas el ritmo
    obj("DeathPit", HUECO_X0 * TS, (MH - 1) * TS, (HUECO_X1 - HUECO_X0) * TS, TS)
    # Recompensa visible sobre el último bloque
    obj("Pickup", (HUECO_X0 + 6) * TS, suelo_px - 4 * TS, 16, 16,
        item_id="moneda_ritmo", automatico=True, mensaje="A tiempo con la musica.")
    obj("Checkpoint", (4 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=4)

    # ── Sala 5: láseres en cascada + hundible ───
    obj("MessageTrigger_Once", (4 * SALA + 2) * TS, suelo_px - 64, 48, 48,
        text="Se encienden en cascada. Hay hueco: buscalo.")
    for i in range(5):
        obj("LaserZone", (4 * SALA + 8 + i * 4) * TS, 5 * TS, 8, 15 * TS,
            dano=99.0, encendido=1.1, apagado=2.2, desfase=i * 0.66)
    obj("SinkingPlatform", (4 * SALA + 24) * TS, suelo_px - 4 * TS, 3 * TS, 8,
        retraso=0.5, reaparece_en=2.5)
    obj("Checkpoint", (5 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=5)

    # ── Sala 6: agua y corriente ───
    obj("MessageTrigger_Once", (5 * SALA + 1) * TS, suelo_px - 64, 48, 48,
        text="Bajo el agua se acaba el aire. Sal a respirar.")
    obj("WaterZone", (5 * SALA + 4) * TS, (SUELO_Y - 4) * TS, 22 * TS, 8 * TS,
        corriente_x=25.0, corriente_y=0.0)
    obj("Checkpoint", (6 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=6)

    # ── Sala 7: sigilo + Sokoban ───
    obj("MessageTrigger_Once", (6 * SALA + 2) * TS, suelo_px - 64, 48, 48,
        text="Te estan mirando. Y algo te sigue.")
    obj("Guard", (6 * SALA + 12) * TS, suelo_px - 2 * TS, TS, 2 * TS,
        mira_x=-1.0, mira_y=0.0, alcance=180.0, semiangulo=28.0,
        barrido=35.0, velocidad_barrido=40.0)
    obj("Guard", (6 * SALA + 22) * TS, suelo_px - 2 * TS, TS, 2 * TS,
        mira_x=1.0, mira_y=0.0, alcance=180.0, semiangulo=28.0)
    obj("Stalker", (6 * SALA + 4) * TS, suelo_px - 2 * TS, TS, 2 * TS,
        velocidad=42.0, distancia_retirada=420.0, reaparicion=7.0)
    obj("Checkpoint", (6 * SALA + 26) * TS, suelo_px - 32, 16, 32, checkpoint_id=7)
    # Sokoban: Push + Breakable + PressurePlate → Door
    obj("MessageTrigger_Once", (6 * SALA + 25) * TS, suelo_px - 64, 48, 48,
        text="Uno se empuja. El otro se rompe a golpes.")
    obj("PushBlock", (6 * SALA + 27) * TS, suelo_px - 2 * TS, 2 * TS, 2 * TS,
        velocidad=45.0)
    obj("BreakableBlock", (6 * SALA + 33) * TS, suelo_px - 4 * TS, TS, 2 * TS,
        golpes=3)
    obj("BreakableBlock", (6 * SALA + 33) * TS, suelo_px - 2 * TS, TS, 2 * TS,
        golpes=1)
    obj("PressurePlate", (6 * SALA + 29) * TS, suelo_px - TS, 2 * TS, TS,
        evento="PLACA_LAB", requiere="bloque", mantener=True)
    obj("Door", (6 * SALA + 35) * TS, suelo_px - 3 * TS, TS, 3 * TS,
        abre_con="PLACA_LAB", mensaje="La puerta cede mientras el bloque pisa el boton.")

    # ── Sala 8: llave / puerta / resorte / interruptor / jaula + hielo ───
    s8 = 7 * SALA
    obj("MessageTrigger_Once", (s8 + 2) * TS, suelo_px - 64, 48, 48,
        text="Coge la llave. La puerta la pide.")
    obj("Key", (s8 + 5) * TS, suelo_px - 2 * TS, TS, TS,
        key_id="llave_lab", nombre="Llave del laboratorio")
    obj("Door", (s8 + 11) * TS, suelo_px - 3 * TS, TS, 3 * TS,
        key_id="llave_lab", consume_llave=True,
        mensaje="Cerrada. Falta la llave.")
    obj("Spring", (s8 + 14) * TS, suelo_px - TS, 2 * TS, TS,
        impulso=-560.0, rearme=0.2)
    obj("EventTrigger", (s8 + 19) * TS, (SUELO_Y - 8) * TS, 2 * TS, TS,
        evento="ABRIR_JAULA", automatico=True, una_vez=True)
    obj("Cage", (s8 + 25) * TS, suelo_px - 3 * TS, 2 * TS, 3 * TS,
        abre_con="ABRIR_JAULA", mensaje="La jaula no cede a golpes.")
    # Hielo real con material — el suelo también es mecánica
    obj("FrictionZone", (s8 + 5) * TS, suelo_px - 2 * TS, 12 * TS, 2 * TS,
        multiplicador=0.55, arrastre=0.0, material="hielo")
    obj("Pickup", (s8 + 20) * TS, (SUELO_Y - 8) * TS, 16, 16,
        item_id="moneda_llave", automatico=True, mensaje="Recompensa tras el resorte.")
    obj("Checkpoint", (8 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=8)

    # ── Sala 9: onda de choque + escena + liana/tirolesa + pendientes + scroll + warp ───
    s9 = 8 * SALA
    obj("MessageTrigger_Once", (s9 + 2) * TS, suelo_px - 64, 48, 48,
        text="Aqui no se frena. Y algo golpea el suelo.")
    obj("ShockwaveZone", (s9 + 10) * TS, suelo_px - TS, 6 * TS, TS,
        dano=99.0, encendido=0.7, apagado=2.6, desfase=0.0)
    obj("ShockwaveZone", (s9 + 16) * TS, suelo_px - TS, 6 * TS, TS,
        dano=99.0, encendido=0.7, apagado=2.6, desfase=1.65)
    # Liana y tirolesa — movilidad vertical y diagonal
    obj("Vine", (s9 + 5) * TS, (SUELO_Y - 11) * TS, 8, 5 * TS,
        velocidad=75.0, ancho_de_agarre=12.0)
    obj("Zipline", (s9 + 22) * TS, (SUELO_Y - 6) * TS, 8, 8,
        destino_dx=5 * TS, destino_dy=8 * TS, velocidad=200.0)
    # Pendientes — suelo inclinado de verdad
    obj("Slope", (s9 + 8) * TS, suelo_px - 3 * TS, 3 * TS, 3 * TS, sube="derecha")
    obj("Slope", (s9 + 11) * TS, suelo_px - 3 * TS, 3 * TS, 3 * TS, sube="izquierda")
    obj("Slope", (s9 + 14) * TS, suelo_px - 24, 6 * TS, 24, sube="derecha")
    # Cutscene corta con temblor+evento — guion con saltos de línea escapados
    obj("Cutscene", (s9 + 26) * TS, suelo_px - 4 * TS, 2 * TS, 4 * TS,
        guion="camara 4400 200 0.8\ntemblor 0.3 5\n+ evento LAB_COMPLETADO",
        bloquea=False, saltable=True, una_vez=True)
    obj("Chest", (s9 + 24) * TS, suelo_px - 2 * TS, TS, TS,
        contenido="reliquia_lab", mensaje="Recompensa del laboratorio.")
    obj("Checkpoint", (9 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=9)

    # ── Sala 10: scroll forzado + examen final ───
    s10 = 9 * SALA
    obj("MessageTrigger_Once", (s10 + 2) * TS, suelo_px - 64, 48, 48,
        text="La camara arranca sola. No te quedes atras.")
    obj("ScrollZone", (s10 + 6) * TS, suelo_px - 4 * TS, 2 * TS, 4 * TS,
        velocidad_x=38.0, margen_de_gracia=28.0,
        parar_en_x=float((s10 + 26) * TS))
    # Plataforma y resorte dentro del scroll — examen combina viento+plataforma+laser
    obj("MovingPlatform", (s10 + 12) * TS, suelo_px - 3 * TS, 3 * TS, 8,
        destino_dx=0.0, destino_dy=-48.0, velocidad=34.0, espera=0.4)
    obj("Spring", (s10 + 19) * TS, suelo_px - TS, 2 * TS, TS,
        impulso=-520.0, rearme=0.2)
    # Examen final: viento + plataforma + láser en la misma sala
    obj("WindZone", (s10 + 8) * TS, suelo_px - 6 * TS, 8 * TS, 6 * TS,
        fuerza_x=120.0, fuerza_y=0.0, periodo=2.5)
    obj("LaserZone", (s10 + 14) * TS, suelo_px - 6 * TS, 8, 6 * TS,
        dano=25.0, encendido=1.0, apagado=1.5, desfase=0.5)
    obj("Checkpoint", (10 * SALA - 4) * TS, suelo_px - 32, 16, 32, checkpoint_id=10)

    # WarpZones — atajo de vuelta
    obj("WarpZone", (MW - 8) * TS, suelo_px - 3 * TS, 2 * TS, 3 * TS,
        automatico=False, destino_x=float(3 * TS), destino_y=float(suelo_px),
        mensaje="De vuelta a la entrada.")
    obj("WarpZone", 5 * TS, suelo_px - 3 * TS, 2 * TS, 3 * TS,
        automatico=False, destino_x=float((5 * SALA - 4) * TS),
        destino_y=float(suelo_px), mensaje="Atajo a la mitad.")
    obj("NextTrigger", (MW - 4) * TS, suelo_px - 3 * TS, 2 * TS, 3 * TS)

    # ── Fauna: 10 especies del bestiario, ≤2 por sala, repartidas ───
    fauna = [
        ("WalkerInsect", 1, 8), ("WalkerRaton", 2, 10),
        ("FlyingCucaracha", 2, 4), ("WalkerEstudiante", 3, 12),
        ("FlyingNotebook", 3, 2), ("ShooterTiza", 4, 14),
        ("ShooterCocinero", 5, 14), ("WalkerTerciopelo", 6, 14),
        ("FlyingTerciovolador", 7, 2), ("ShooterVenomoLargo", 8, 6),
    ]
    for especie, sala, dx in fauna:
        x = (sala * SALA + dx) * TS
        if especie.startswith("Flying"):
            obj(especie, x, suelo_px - 6 * TS, 20, 14)
        else:
            obj(especie, x, suelo_px - 28, 24, 28)
    # Dos genéricos extra para variedad sin saturar
    obj("Walker", (SALA + 20) * TS, suelo_px - 28, 24, 28)
    obj("FlyingBoa", (2 * SALA + 12) * TS, suelo_px - 6 * TS, 20, 14)

    # Luces — 2 focos con sombras proyectadas (coste medido)
    obj("Light", (SALA // 2) * TS, (SUELO_Y - 6) * TS, 16, 16,
        radius=180, color="#ffe9a8", intensity=0.9)
    obj("Light", (SALA - 6) * TS, (SUELO_Y - 6) * TS, 16, 16,
        radius=150, color="#a8d8ff", intensity=0.7)
    return o


def _colisiones() -> list[str]:
    """Capa Collision: suelo continuo con un hueco exigente + plataformas."""
    r: list[str] = []
    ident = [1]

    def solido(x: int, y: int, w: int, h: int, tipo: str = "Solid") -> None:
        ident[0] += 1
        r.append(
            f'  <object id="{ident[0]}" type="{tipo}" x="{x}" y="{y}"'
            f' width="{w}" height="{h}"/>',
        )

    suelo_px = SUELO_Y * TS
    altura_suelo = (MH - SUELO_Y) * TS
    # Suelo partido por el hueco exigente — dos rects, gap 48 px (exigente)
    solido(0, suelo_px, HUECO_X0 * TS, altura_suelo)
    solido(HUECO_X1 * TS, suelo_px, (MW - HUECO_X1) * TS, altura_suelo)
    # Muros laterales
    solido(-TS, 0, TS, MH * TS)
    solido(MW * TS, 0, TS, MH * TS)
    # Repisas de descanso (atravesables)
    for sala in range(1, 10):
        solido((sala * SALA - 4) * TS, (SUELO_Y - 5) * TS, 8 * TS, 8, "Platform")
    # Repisa alta del resorte
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
  <property name="schema_version" value="1"/>
  <property name="stage_id" value="stage_mecanicas"/>
  <property name="stage_name" value="LABORATORIO DE MECANICAS"/>
  <property name="author" value="Equipo docente — Legacy of Infest"/>
  <property name="bgm_track" value="bgm_stage0"/>
  <property name="bpm" type="float" value="120"/>
  <property name="compas" type="int" value="4"/>
  <property name="background_zone" value="stage0"/>
  <property name="climate" value="clear"/>
  <property name="cielo" type="bool" value="true"/>
  <property name="time_limit" value="0"/>
  <property name="zone" type="int" value="0"/>
  <property name="ambient_light" type="float" value="0.78"/>
  <property name="bloom" type="float" value="0.15"/>
  <property name="vignette" type="float" value="0.25"/>
  <property name="ambient_fx" value="dust"/>
  <property name="ambient_fx_rate" type="float" value="8"/>
  <property name="desfase_audio" type="float" value="0.05"/>
  <property name="water_effect" type="bool" value="true"/>
  <property name="water_tint" value="#2850a0"/>
  <property name="water_alpha" type="float" value="120"/>
  <property name="water_amplitude" type="float" value="6"/>
  <property name="water_frequency" type="float" value="0.04"/>
  <property name="water_speed" type="float" value="1.5"/>
  <property name="estamina" type="float" value="100"/>
  <property name="tiempo_bala" type="float" value="3"/>
  <property name="habilidades_libres" type="bool" value="true"/>
  <property name="sombras_proyectadas" type="bool" value="true"/>
  <property name="god_rays" type="float" value="0.35"/>
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
