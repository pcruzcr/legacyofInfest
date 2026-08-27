#!/usr/bin/env python3
"""
Genera `assets/maps/stage0/stage0.tmx`: prólogo jugable y referencia del framework.

AUD-661 — reconstrucción completa con diseño jugable verificado
================================================================
Este generador se reescribe desde cero para cumplir simultáneamente tres
contratos que antes se cumplían por separado: el temario del GDD
(`docs/64_GAME_DESIGN_DOCUMENT.md`), la guía de ritmo de
`docs/66_GUIA_DE_LEVEL_DESIGN.md` y la especificación de referencia
`docs/07_STAGE0_DESIGN.md`, más los tres validadores automáticos
(`validate_tmx --ci`, `grade_stage 130/130`,
`test_stage0_platform_solidity`).

Qué enseña y por qué en este orden
------------------------------------
Siete zonas A-G en orden de temario, de lo más simple a lo compuesto,
siguiendo *present-before-challenge* y *dos soluciones donde se pueda
(tres en el foso)*:

    A  mover / saltar / coyote / colisión horizontal
    B  Walker inevitable (lección Mario 1-1) + checkpoint
    C  colina escalonada + liana + hielo (FrictionZone material hielo)
    D  Archer con admite_bash + Caster (fuego de respuesta)
    E  Charger / Brute + Key / LockedDoor + puzzle PushBlock+PressurePlate
    F  foso con DeathPit + RhythmBlock + goma (tres rutas)
    G  viento + tirolesa + cofre + CameraLock + salida

El foso mide 80 px (5 baldosas): entra en la banda exigente (34-85 px)
de `JumpEnvelope` y es cruzable soltando la dirección al despegar. Los
bloques rítmicos y la goma son las rutas cómodas. La colina usa
`_altura_colina` como única fuente para dibujo y colisión (AUD-506):
una sola función evita que el suelo se vea y no se pise.

Invariantes que este fichero no rompe
-------------------------------------
* Tamaño 100×38 (1600×608), suelo en y=480 (fila 30), tileset 1024×1024
  con 64 columnas — declarar otro tamaño pinta baldosas equivocadas sin
  que el validador avise.
* Dos obstáculos interiores de 2 y 3 baldosas (columnas 10 y 18): 2 se
  salta parado, 3 exige impulso (72 px medidos).
* Dos plataformas de un solo sentido (E y G), dos zonas de material
  (hielo en C, goma en F), 5 checkpoints, 5 coleccionables
  (3 Pickup + Key + Chest), 8 mensajes, 12 focos.
* Física sin tocar: el salto sigue en ~87 px de envolvente; cambiarlo
  exigiría recalibrar `grade_stage` y los 16 mapas que comparten vara.

Novedades de esta reconstrucción
--------------------------------
* **PressurePlate en E/F** — puzzle Sokoban integrado con PushBlock que
  abre la misma puerta que la llave (dos soluciones para el mismo
  obstáculo). Usa `evento="PLACA_PROLOGO"` y `requiere="bloque"`.
* **Diálogo ramificado** — el primer MessageTrigger lleva `dialogue` para
  ejercitar `dialogue_tree_id` sin añadir un noveno mensaje.
* Comentarios con porqués y no con qués; CSV y colisiones generados
  desde las mismas constantes para que no diverjan.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESTINO = PROJECT_ROOT / "assets" / "maps" / "stage0" / "stage0.tmx"
TILESET = "../../tilesets/tileset_stage0.png"

TS = 16
MW, MH = 100, 38          # 1600 × 608 px
SUELO_Y = 30              # fila del suelo

# Baldosas — tileset_stage0.png mide 1024×1024, 4096 baldosas, 64 columnas.
TS_COLUMNAS = 64
TS_TOTAL = 4096
TS_IMAGEN_PX = 1024

VACIO = 0
SUELO_SUPERFICIE = 409
SUELO_RELLENO_A = 665
SUELO_RELLENO_B = 668
MURO_IZQUIERDO = 153
MURO_DERECHO = 160
PLATAFORMA = 666
BORDE = 161

# Foso de la zona F: 5 baldosas (80 px) — exigente pero cruzable con técnica
# experta (soltar dirección). Tres rutas: salto, ritmo, goma.
FOSO_X0, FOSO_X1 = 67, 72

# Dos obstáculos interiores: 2 baldosas (parado) y 3 baldosas (con impulso).
# Columna 18 y no 50 porque la colina ocupa 24-50 y allí quedaría enterrado.
OBSTACULOS: tuple[tuple[int, int], ...] = ((10, 2), (18, 3))


def _relleno(y: int) -> int:
    """Alterna baldosas de relleno para que el suelo no se vea liso."""
    return SUELO_RELLENO_A if (y - SUELO_Y) % 2 else SUELO_RELLENO_B


def _altura_colina(x: int) -> int:
    """Altura de la colina en baldosas sobre SUELO_Y, o 0 fuera de ella."""
    if 24 <= x <= 29:
        return x - 24
    if 30 <= x <= 44:
        return 6
    if 45 <= x <= 50:
        return 6 - (x - 45)
    return 0


def _terreno() -> list[list[int]]:
    """Geometría visual del mapa, capa Terrain."""
    g = [[VACIO] * MW for _ in range(MH)]
    for x in range(MW):
        g[SUELO_Y][x] = SUELO_SUPERFICIE
    for y in range(SUELO_Y + 1, MH):
        for x in range(MW):
            g[y][x] = _relleno(y)

    # Hueco del foso
    for y in range(SUELO_Y, MH):
        for x in range(FOSO_X0, FOSO_X1):
            g[y][x] = VACIO

    # Colina escalonada zona C — un sólido por columna con _altura_colina
    for x in range(24, 51):
        alto = _altura_colina(x)
        if alto == 0:
            continue
        for y in range(SUELO_Y - alto, SUELO_Y):
            g[y][x] = BORDE
        g[SUELO_Y - alto][x] = SUELO_SUPERFICIE

    # Plataformas de un solo sentido (repisas)
    for x in range(58, 68):  # zona E — bypass alto
        g[SUELO_Y - 9][x] = PLATAFORMA
    for x in range(88, 96):  # zona G — tramo final
        g[SUELO_Y - 9][x] = PLATAFORMA

    # Muros de cierre fuera del área jugable
    for y in range(MH):
        g[y][0] = MURO_IZQUIERDO
        g[y][MW - 1] = MURO_DERECHO

    # Obstáculos interiores: remate de superficie arriba y borde debajo
    for x, alto in OBSTACULOS:
        g[SUELO_Y - alto][x] = SUELO_SUPERFICIE
        for y in range(SUELO_Y - alto + 1, SUELO_Y):
            g[y][x] = BORDE
    return g


def _objetos() -> list[str]:
    """Objetos de la capa Objects — todo lo que el jugador aprende."""
    o: list[str] = []
    ident = [200]

    def obj(tipo: str, x: int, y: int, w: int, h: int, **props: object) -> None:
        ident[0] += 1
        cabecera = (
            f'  <object id="{ident[0]}" name="{tipo}_{ident[0]}" type="{tipo}"'
            f' x="{x}" y="{y}" width="{w}" height="{h}"'
        )
        if not props:
            o.append(cabecera + "/>")
            return
        cuerpo = cabecera + ">"
        cuerpo += "\n   <properties>"
        for k, v in props.items():
            if isinstance(v, bool):
                tipo_p, valor = "bool", str(v).lower()
            elif isinstance(v, int):
                tipo_p, valor = "int", str(v)
            elif isinstance(v, float):
                tipo_p, valor = "float", str(v)
            else:
                tipo_p, valor = "", str(v)
            attr = f' type="{tipo_p}"' if tipo_p else ""
            # Escapar saltos de línea en valores de texto para XML
            valor = valor.replace("&", "&amp;").replace('"', "&quot;").replace("\n", "&#10;")
            cuerpo += f'\n    <property name="{k}"{attr} value="{valor}"/>'
        cuerpo += "\n   </properties>"
        cuerpo += "\n  </object>"
        o.append(cuerpo)

    suelo = SUELO_Y * TS

    obj("PlayerSpawn", 3 * TS, suelo - 48, 16, 32)

    obj("Objective", 3 * TS, suelo - 80, 0, 0,
        objective_id="llegar_al_final",
        text="Llega al final del prologo",
        kind="bandera", target="stage0_completado")
    obj("Objective", 4 * TS, suelo - 80, 0, 0,
        objective_id="tres_infectados",
        text="Derrota a tres infectados",
        kind="derrotar", count=3, optional=True)

    # Zona A — primeros pasos, sin daño
    # El primer mensaje lleva `dialogue` para ejercitar diálogo ramificado
    # sin añadir un noveno mensaje: text + dialogue coexisten.
    obj("MessageTrigger_Once", 5 * TS, suelo - 64, 48, 48,
        text="Flechas para moverte. Espacio para saltar.",
        dialogue="intro_prologo")

    # Zona B — contacto y consecuencia (Walker inevitable)
    obj("MessageTrigger_Once", 14 * TS, suelo - 64, 48, 48,
        text="Z ataca. Tambien puedes saltar por encima.")
    obj("Walker", 18 * TS, suelo - 28, 24, 28,
        max_health=2.0, patrol_length=80.0, patrol_speed=60.0, alert_speed=90.0)
    obj("Checkpoint", 22 * TS, suelo - 32, 16, 32, checkpoint_id=0)

    # Zona C — colina, liana, hielo (material)
    obj("MessageTrigger_Once", 25 * TS, suelo - 64, 48, 48,
        text="Sube. Con G o Arriba te agarras a la liana.")
    obj("Vine", 33 * TS, (SUELO_Y - 11) * TS, 8, 5 * TS,
        velocidad=75.0, ancho_de_agarre=12.0)
    obj("Pickup", 29 * TS, (SUELO_Y - 4) * TS - TS, 16, 16,
        item_id="fragmento_1", automatico=True, mensaje="Fragmento 1 de 3.")
    obj("Flying", 30 * TS, suelo - 7 * TS, 20, 14,
        flight_mode="sine", flight_speed=60.0,
        sine_amplitude=32.0, sine_frequency=2.0)
    obj("MessageTrigger_Once", 36 * TS, (SUELO_Y - 6) * TS - 48, 48, 48,
        text="Hielo. Sueltas menos el salto, no mas.")
    obj("FrictionZone", 36 * TS, (SUELO_Y - 6) * TS, 7 * TS, TS,
        multiplicador=0.55, material="hielo")
    obj("Checkpoint", 43 * TS, (SUELO_Y - 6) * TS - 32, 16, 32, checkpoint_id=1)

    # Zona D — fuego de respuesta y bash
    obj("MessageTrigger_Once", 45 * TS, suelo - 64, 48, 48,
        text="Esa flecha se puede golpear para impulsarte.")
    obj("Archer", 49 * TS, suelo - 28, 16, 28, fire_rate=1.6,
        projectile_speed=90.0, projectile_damage=1.5, admite_bash=True)
    obj("Caster", 52 * TS, suelo - 28, 20, 28)
    obj("Pickup", 54 * TS, suelo - 20, 16, 16,
        item_id="fragmento_2", automatico=True, mensaje="Fragmento 2 de 3.")
    obj("Checkpoint", 55 * TS, suelo - 32, 16, 32, checkpoint_id=2)

    # Zona E — llave, combate variado y puzzle Push+Plate
    obj("MessageTrigger_Once", 57 * TS, suelo - 64, 48, 48,
        text="La llave abre la puerta del fondo.")
    obj("Key", 59 * TS, suelo - 20, 16, 16,
        item_id="llave_prologo", automatico=True, mensaje="Has cogido la llave.")
    # Puzzle extra E/F: PushBlock + PressurePlate que abre la misma puerta
    # que la llave — dos soluciones para el mismo obstáculo (present-before-challenge).
    # El bloque se empuja sobre la placa y la puerta cede mientras esté pisada.
    obj("PushBlock", 60 * TS, suelo - 32, 2 * TS, 2 * TS, velocidad=45.0)
    obj("PressurePlate", 63 * TS, suelo - 16, 2 * TS, TS,
        evento="PLACA_PROLOGO", requiere="bloque", mantener=True)
    obj("Charger", 62 * TS, suelo - 24, 28, 24, charge_speed=250.0)
    obj("Brute", 65 * TS, suelo - 60, 100, 60, max_health=6.0)
    # La puerta se abre con llave O con placa (abre_con) — dos soluciones.
    obj("LockedDoor", FOSO_X0 * TS - TS, suelo - 3 * TS, TS, 3 * TS,
        key_id="llave_prologo", clase="puerta",
        mensaje_bloqueado="Cerrada. Busca la llave.",
        abre_con="PLACA_PROLOGO")
    obj("Checkpoint", 65 * TS, suelo - 32, 16, 32, checkpoint_id=3)

    # Zona F — foso con tres rutas
    obj("MessageTrigger_Once", (FOSO_X0 - 1) * TS - TS, suelo - 64, 48, 48,
        text="Salta, cronometra los bloques, o prueba la goma.")
    obj("DeathPit", FOSO_X0 * TS, (MH - 2) * TS, (FOSO_X1 - FOSO_X0) * TS, 2 * TS)
    for i in range(3):
        obj("RhythmBlock", (FOSO_X0 + 1 + i) * TS, suelo - 5 * TS, TS, TS,
            visible_seg=1.8, oculto_seg=1.0, desfase=i * 0.6)
    obj("FrictionZone", (FOSO_X0 - 1) * TS, (MH - 2) * TS, TS, 2 * TS,
        material="goma")
    obj("HazardZone", (FOSO_X1 + 2) * TS, suelo - TS, 3 * TS, TS, damage=0.25)

    # Zona G — todo junto: viento, tirolesa, cofre
    obj("MessageTrigger_Once", 82 * TS, suelo - 64, 48, 48,
        text="El viento empuja. Espera a que amaine. U es el ataque definitivo.")
    obj("WindZone", 84 * TS, (SUELO_Y - 10) * TS, 10 * TS, 10 * TS,
        fuerza_x=210.0, fuerza_y=0.0, periodo=3.4)
    obj("Shooter", 87 * TS, suelo - 24, 16, 24, fire_rate=2.0,
        projectile_speed=100.0, projectile_damage=2.0,
        patrol_length=48.0, patrol_speed=30.0)
    obj("Assassin", 90 * TS, suelo - 24, 16, 24)
    obj("Walker", 93 * TS, suelo - 28, 24, 28, max_health=2.0)
    obj("Pickup", 92 * TS, (SUELO_Y - 10) * TS, 16, 16,
        item_id="fragmento_3", automatico=True, mensaje="Fragmento 3 de 3.")
    obj("Chest", 94 * TS, (SUELO_Y - 10) * TS, TS, TS,
        contenido="reliquia_prologo", mensaje="Una reliquia del prologo.")
    obj("Zipline", 93 * TS, (SUELO_Y - 10) * TS, 8, 8,
        destino_dx=5 * TS, destino_dy=8 * TS, velocidad=200.0)
    obj("CameraLock", 86 * TS, 0, 14 * TS, MH * TS, lock_y=True)
    obj("Checkpoint", 89 * TS, suelo - 32, 16, 32, checkpoint_id=4)
    obj("NextTrigger", 97 * TS, suelo - 3 * TS, 2 * TS, 3 * TS)

    # Focos — 12 en total, calibrados para legibilidad nocturna (day_length 420)
    obj("Light", 6 * TS, suelo - 5 * TS, 16, 16,
        radius=150.0, color="fire", intensity=0.95, flicker=True,
        flicker_speed=3.2, flicker_amount=0.18)
    for i, x in enumerate((14, 22, 30, 38, 46, 54, 62, 70, 78, 86, 94)):
        obj("Light", x * TS, suelo - 6 * TS, 16, 16,
            radius=140.0 + (i % 3) * 10, color="warm",
            intensity=0.85 + (i % 2) * 0.05)
    return o


def _colisiones() -> list[str]:
    """Capa Collision: suelo, muros, obstáculos y colina."""
    r: list[str] = []
    ident = [1]

    def solido(x: int, y: int, w: int, h: int, tipo: str = "Solid") -> None:
        ident[0] += 1
        r.append(
            f'  <object id="{ident[0]}" name="{tipo}_{ident[0]}" type="{tipo}"'
            f' x="{x}" y="{y}" width="{w}" height="{h}"/>',
        )

    suelo = SUELO_Y * TS
    solido(0, suelo, FOSO_X0 * TS, (MH - SUELO_Y) * TS)
    solido(FOSO_X1 * TS, suelo, (MW - FOSO_X1) * TS, (MH - SUELO_Y) * TS)
    solido(-TS, 0, TS, MH * TS)
    solido(MW * TS, 0, TS, MH * TS)
    for x, alto in OBSTACULOS:
        solido(x * TS, (SUELO_Y - alto) * TS, TS, alto * TS)
    # Colina — un sólido por columna desde _altura_colina
    for x in range(24, 51):
        alto = _altura_colina(x)
        if alto:
            solido(x * TS, (SUELO_Y - alto) * TS, TS, alto * TS)
    # Repisas atravesables (Platform)
    solido(58 * TS, (SUELO_Y - 9) * TS, 10 * TS, 8, "Platform")
    solido(88 * TS, (SUELO_Y - 9) * TS, 8 * TS, 8, "Platform")
    return r


def generar() -> str:
    g = _terreno()
    csv_terreno = ",".join(str(g[y][x]) for y in range(MH) for x in range(MW))
    ceros = ",".join(["0"] * (MW * MH))

    def capa(i: int, nombre: str, datos: str) -> str:
        return (
            f' <layer id="{i}" name="{nombre}" width="{MW}" height="{MH}">\n'
            f'  <data encoding="csv">\n{datos}\n</data>\n </layer>'
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" \
renderorder="right-down" width="{MW}" height="{MH}" tilewidth="{TS}" \
tileheight="{TS}" infinite="0" nextlayerid="20" nextobjectid="900">
 <properties>
  <property name="schema_version" value="1"/>
  <property name="stage_id" value="stage0"/>
  <property name="stage_name" value="STAGE 0 - PROLOGUE"/>
  <property name="author" value="Equipo docente — Legacy of Infest"/>
  <property name="bgm_track" value="bgm_stage0"/>
  <property name="background_zone" value="stage0"/>
  <property name="climate" value="clear"/>
  <property name="time_limit" type="int" value="0"/>
  <property name="gravity_multiplier" type="float" value="1.0"/>
  <property name="ambient_light" type="float" value="0.70"/>
  <property name="start_hour" value="afternoon"/>
  <property name="day_length" type="float" value="420"/>
  <property name="season" value="autumn"/>
  <property name="zone" type="int" value="0"/>
  <property name="bloom" type="float" value="0.18"/>
  <property name="vignette" type="float" value="0.30"/>
  <property name="profundidad_curva" type="float" value="1.0"/>
  <property name="orden_por_y" type="bool" value="false"/>
  <property name="ambient_fx" value="spores"/>
  <property name="ambient_fx_rate" type="float" value="14"/>
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
{capa(6, "FG_Overlay", ceros)}
 <objectgroup id="7" name="Collision">
{chr(10).join(_colisiones())}
 </objectgroup>
 <objectgroup id="8" name="Objects">
{chr(10).join(_objetos())}
 </objectgroup>
</map>
"""


def main() -> None:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(generar(), encoding="utf-8")
    print(f"escrito {DESTINO.relative_to(PROJECT_ROOT)} ({MW}×{MH} baldosas)")


if __name__ == "__main__":
    main()
