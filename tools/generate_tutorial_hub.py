#!/usr/bin/env python3
"""
Genera `assets/maps/tutorial_hub/tutorial_hub.tmx`: hub tutorial guiado.

AUD-721 — reemplazo del tutorial de texto por niveles jugables con recompensa
------------------------------------------------------------------------
El tutorial anterior (`TutorialScene`) era 4 pasos de texto sin prueba:
el jugador leía y pulsaba Enter sin usar la mecánica. Este hub es el
reemplazo pedido: 5 salas, una mecánica por sala, mensaje + práctica
+ recompensa (moneda + puntos + XP + logro). Se aprende haciendo.

Diseño (Mario 1-1: enseñar sin texto, luego con texto, luego examen):
  Sala 1 Movimiento: suelo con 2 huecos 1-2 baldosas, coyote visible
  Sala 2 Combate: 2 Walkers débiles, ventana combo 0.5s, 3 golpes = moneda
  Sala 3 Defensa: Shooter + pared, parry (agachado+Z) y dash (SHIFT/click medio)
  Sala 4 Mundo: cinta + plataforma móvil + agua corta
  Sala 5 Jefe lite: 1 Brute + 1 Shooter telegrafiado, ventana castigo

Entre salas: repisa de descanso + Checkpoint + Pickup moneda + Objective.
Al completar cada objetivo suena y el HUD tacha; al final, logro tutorial.
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESTINO = PROJECT_ROOT / "assets" / "maps" / "tutorial_hub" / "tutorial_hub.tmx"
DESTINO_CENITAL = PROJECT_ROOT / "assets" / "maps" / "tutorial_hub_cenital" / "tutorial_hub_cenital.tmx"
TILESET = "../../tilesets/tileset_stage0.png"

TS = 16
MW, MH = 175, 24
SUELO_Y = 20
SALA = 35

VACIO = 0
SUELO = 409
PLATAFORMA = 666


def _terreno() -> list[list[int]]:
    g = [[VACIO] * MW for _ in range(MH)]
    for y in range(SUELO_Y, MH):
        for x in range(MW):
            g[y][x] = SUELO
    # Huecos sala 1: 2 huecos cortos 16 y 32 px para practicar salto
    for y in range(SUELO_Y, MH):
        for x in range(30, 31):
            g[y][x] = VACIO
        for x in range(34, 36):
            g[y][x] = VACIO
    # Repisas descanso entre salas
    for sala in range(1, 5):
        for x in range(sala * SALA - 3, sala * SALA + 3):
            g[SUELO_Y - 4][x] = PLATAFORMA
    # Repisa alta sala 4 (plataforma móvil la alcanza)
    for x in range(3 * SALA + 10, 3 * SALA + 16):
        g[SUELO_Y - 6][x] = PLATAFORMA
    return g


def _objetos() -> list[str]:
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

    # ── Sala 1: Movimiento (flechas/WASD, ratón alternativo) ──
    obj("MessageTrigger_Once", 3 * TS, suelo_px - 64, 64, 48,
        text="Sala 1/5 — Movimiento. Flechas o WASD para moverte, Espacio/W/Arriba para saltar. "
             "Ratón: click izq=ataque corto, der=largo. Mando: stick izq + A. Supera los huecos.")
    obj("MessageTrigger_Once", 18 * TS, suelo_px - 64, 48, 32,
        text="Consejo: el coyote te deja saltar 6 fotogramas tarde. Usa el borde.")
    obj("Checkpoint", 6 * TS, suelo_px - 32, 16, 32, checkpoint_id=1)
    obj("Checkpoint", 18 * TS, suelo_px - 32, 16, 32, checkpoint_id=101)
    obj("Pickup", 12 * TS, suelo_px - 32, 16, 16,
        item_id="moneda", automatico=True, mensaje="¡Bien! Moneda +10 pts")
    # Objetivo 1
    obj("Objective", 1 * SALA * TS, suelo_px - 48, 32, 48,
        objective_id="tutorial_movimiento", text="Supera la zona de saltos",
        obligatorio=True)

    # ── Sala 2: Combate + combo ──
    x0 = 1 * SALA * TS
    obj("MessageTrigger_Once", x0 + 2 * TS, suelo_px - 64, 64, 48,
        text="Sala 2/5 — Combate. Z/J corto, X/K largo. Ratón izq/der igual. "
             "Cadena 3 golpes del mismo tipo dentro de 0.5s para combo x2. Prueba con los maniquíes.")
    obj("Walker", x0 + 10 * TS, suelo_px - 28, 24, 28, max_health=1.0, damage_on_contact=0.0)
    obj("Walker", x0 + 18 * TS, suelo_px - 28, 24, 28, max_health=1.0, damage_on_contact=0.0)
    # Enemigo que camina y vuelve al borde (no camina en aire)
    obj("Walker", x0 + 26 * TS, suelo_px - 28, 24, 28, patrol_length=48.0)
    obj("Checkpoint", x0 + 6 * TS, suelo_px - 32, 16, 32, checkpoint_id=2)
    obj("Checkpoint", x0 + 22 * TS, suelo_px - 32, 16, 32, checkpoint_id=102)
    obj("Pickup", x0 + 32 * TS, suelo_px - 32, 16, 16,
        item_id="moneda", automatico=True, mensaje="¡Combo! Moneda +25 pts")
    obj("Objective", x0 + 8 * TS, suelo_px - 48, 32, 48,
        objective_id="tutorial_combate", text="Derrota a los maniquíes con combo",
        obligatorio=True)

    # ── Sala 3: Defensa (parry + dash) ──
    x0 = 2 * SALA * TS
    obj("MessageTrigger_Once", x0 + 2 * TS, suelo_px - 64, 64, 48,
        text="Sala 3/5 — Defensa. Agáchate+S para parry (Z al mismo tiempo), SHIFT/click medio para dash. "
             "Haz parry al disparo: aturde 1s y abre ventana.")
    obj("Shooter", x0 + 16 * TS, suelo_px - 28, 24, 28, max_health=1.0, damage_on_contact=0.25,
        fire_rate=1.2, projectile_speed=90.0)
    obj("MessageTrigger_Once", x0 + 20 * TS, suelo_px - 64, 48, 32,
        text="Pista: mando B=parry, LB=dash. Teclado: flechas o WASD, ambos sirven.")
    obj("Checkpoint", x0 + 6 * TS, suelo_px - 32, 16, 32, checkpoint_id=3)
    obj("Checkpoint", x0 + 22 * TS, suelo_px - 32, 16, 32, checkpoint_id=103)
    obj("Pickup", x0 + 30 * TS, suelo_px - 32, 16, 16,
        item_id="moneda", automatico=True, mensaje="¡Parry! Moneda +25 pts")
    obj("Objective", x0 + 12 * TS, suelo_px - 48, 32, 48,
        objective_id="tutorial_defensa", text="Haz un parry al proyectil",
        obligatorio=True)

    # ── Sala 4: Mundo (cinta + plataforma + agua) ──
    x0 = 3 * SALA * TS
    obj("MessageTrigger_Once", x0 + 2 * TS, suelo_px - 64, 64, 48,
        text="Sala 4/5 — Mundo. Cinta te arrastra, plataforma te lleva, agua te frena y gasta aire. "
             "Usa todo a la vez.")
    obj("Conveyor", x0 + 8 * TS, suelo_px - TS, 10 * TS, TS, arrastre=-60.0)
    obj("MovingPlatform", x0 + 20 * TS, suelo_px - 3 * TS, 3 * TS, 8,
        destino_dx=0.0, destino_dy=-6 * TS, velocidad=40.0, espera=0.6)
    obj("WaterZone", x0 + 28 * TS, (SUELO_Y - 3) * TS, 8 * TS, 4 * TS,
        corriente_x=15.0, corriente_y=0.0)
    obj("Checkpoint", x0 + 6 * TS, suelo_px - 32, 16, 32, checkpoint_id=4)
    obj("Checkpoint", x0 + 22 * TS, suelo_px - 32, 16, 32, checkpoint_id=104)
    obj("Pickup", x0 + 32 * TS, suelo_px - 32, 16, 16,
        item_id="moneda", automatico=True, mensaje="¡Plataformas! Moneda +25 pts")
    obj("Objective", x0 + 10 * TS, suelo_px - 48, 32, 48,
        objective_id="tutorial_mundo", text="Cruza con cinta y plataforma",
        obligatorio=True)

    # ── Sala 5: Jefe lite (telegrafía + castigo) + sigilo introductorio ──
    x0 = 4 * SALA * TS
    obj("MessageTrigger_Once", x0 + 2 * TS, suelo_px - 64, 64, 48,
        text="Sala 5/5 — Jefe lite. El enemigo telegrafía (círculo rojo) 0.4s antes. "
             "Esquiva y castiga en RECOVER. Salta o dash.")
    # AUD-GAME-01: enseñar sigilo ANTES de exigirlo en stage_mecanicas sala 6.
    # Guard aislado con 1.5s de barrido lento = ver sin morir, probar esconderse.
    obj("Guard", x0 + 8 * TS, suelo_px - 32, 16, 32, mira_x=1.0, mira_y=0.0,
        alcance=96.0, semiangulo=30.0, barrido=30.0, velocidad_barrido=25.0)
    obj("Walker", x0 + 14 * TS, suelo_px - 28, 24, 28, max_health=2.0, damage_on_contact=0.5, patrol_length=64.0)
    obj("Shooter", x0 + 22 * TS, suelo_px - 28, 24, 28, max_health=2.0, fire_rate=0.8, projectile_speed=110.0)
    # Luz y parallax visibles en 2.5D
    obj("Light", x0 + 10 * TS, suelo_px - 80, 16, 16, radius=140, color="#ffe9a8", intensity=0.85)
    obj("Checkpoint", x0 + 6 * TS, suelo_px - 32, 16, 32, checkpoint_id=5)
    obj("Checkpoint", x0 + 22 * TS, suelo_px - 32, 16, 32, checkpoint_id=105)
    obj("Pickup", x0 + 30 * TS, suelo_px - 32, 16, 16,
        item_id="corazon_extra", automatico=True, mensaje="¡Jefe lite! Corazón extra")
    obj("Objective", x0 + 12 * TS, suelo_px - 48, 32, 48,
        objective_id="tutorial_jefe", text="Vence a los guardianes finales",
        obligatorio=True)

    # Salida
    obj("NextTrigger", (MW - 4) * TS, suelo_px - 48, 2 * TS, 48)
    # Warp de vuelta al inicio por si se quiere repetir sala
    obj("WarpZone", 5 * TS, suelo_px - 32, 2 * TS, 32,
        automatico=False, destino_x=float(1 * SALA * TS + 10), destino_y=float(suelo_px - 32),
        mensaje="Volver a sala 2")

    return o


def _colisiones() -> list[str]:
    r: list[str] = []
    ident = [1]

    def solido(x: int, y: int, w: int, h: int, tipo: str = "Solid") -> None:
        ident[0] += 1
        r.append(f'  <object id="{ident[0]}" type="{tipo}" x="{x}" y="{y}" width="{w}" height="{h}"/>')

    suelo_px = SUELO_Y * TS
    altura = (MH - SUELO_Y) * TS
    # Suelo partido por 2 huecos sala 1
    solido(0, suelo_px, 30 * TS, altura)
    solido(31 * TS, suelo_px, 3 * TS, altura)
    solido(36 * TS, suelo_px, (MW - 36) * TS, altura)
    # Muros
    solido(-TS, 0, TS, MH * TS)
    solido(MW * TS, 0, TS, MH * TS)
    # Repisas
    for sala in range(1, 5):
        solido((sala * SALA - 3) * TS, (SUELO_Y - 4) * TS, 6 * TS, 8, "Platform")
    solido((3 * SALA + 10) * TS, (SUELO_Y - 6) * TS, 6 * TS, 8, "Platform")
    return r


def _capa(idx: int, nombre: str, datos: str) -> str:
    return (
        f' <layer id="{idx}" name="{nombre}" width="{MW}" height="{MH}">\n'
        f'  <data encoding="csv">\n{datos}\n</data>\n </layer>'
    )


def generar(vista: str = "lateral") -> str:
    g = _terreno()
    csv = ",".join(str(g[y][x]) for y in range(MH) for x in range(MW))
    ceros = ",".join(["0"] * (MW * MH))
    stage_id = "tutorial_hub" if vista == "lateral" else "tutorial_hub_cenital"
    stage_name = "TUTORIAL GUIADO" if vista == "lateral" else "TUTORIAL CENITAL"
    camara = "seguir"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal"
 renderorder="right-down" width="{MW}" height="{MH}"
 tilewidth="{TS}" tileheight="{TS}" infinite="0"
 nextlayerid="20" nextobjectid="900">
 <properties>
  <property name="schema_version" value="1"/>
  <property name="stage_id" value="{stage_id}"/>
  <property name="stage_name" value="{stage_name}"/>
  <property name="author" value="Equipo docente — Legacy of Infest"/>
  <property name="bgm_track" value="bgm_stage0"/>
  <property name="background_zone" value="stage0"/>
  <property name="bpm" type="float" value="120"/>
  <property name="compas" type="int" value="4"/>
  <property name="climate" value="clear"/>
  <property name="cielo" type="bool" value="true"/>
  <property name="time_limit" value="0"/>
  <property name="zone" type="int" value="0"/>
  <property name="ambient_light" type="float" value="0.85"/>
  <property name="estamina" type="float" value="100"/>
  <property name="tiempo_bala" type="float" value="2"/>
  <property name="habilidades_libres" type="bool" value="true"/>
  <property name="profundidad_min" type="float" value="0.85"/>
  <property name="profundidad_max" type="float" value="1.0"/>
  <property name="vista" value="{vista}"/>
  <property name="camara" value="{camara}"/>
 </properties>
 <tileset firstgid="1" name="tileset_stage0" tilewidth="{TS}"
 tileheight="{TS}" tilecount="4096" columns="64">
  <image source="{TILESET}" width="1024" height="1024"/>
 </tileset>
{_capa(1, "BG_Far", ceros)}
{_capa(2, "BG_Mid", ceros)}
{_capa(3, "BG_Near", ceros)}
{_capa(4, "Terrain", csv)}
{_capa(5, "Terrain_Detail", ceros)}
  <objectgroup id="7" name="Collision">
{chr(10).join(_colisiones())}
  </objectgroup>
  <objectgroup id="8" name="Objects">
{chr(10).join(_objetos())}
  </objectgroup>
{_capa(9, "FG_Overlay", ceros)}
</map>
"""


def main() -> None:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(generar(vista="lateral"), encoding="utf-8")
    print(f"escrito {DESTINO.relative_to(PROJECT_ROOT)} ({MW}x{MH})")
    DESTINO_CENITAL.parent.mkdir(parents=True, exist_ok=True)
    DESTINO_CENITAL.write_text(generar(vista="cenital"), encoding="utf-8")
    print(f"escrito {DESTINO_CENITAL.relative_to(PROJECT_ROOT)} ({MW}x{MH})")


if __name__ == "__main__":
    main()
