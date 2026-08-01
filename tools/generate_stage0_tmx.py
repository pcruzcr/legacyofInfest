#!/usr/bin/env python3
"""
Genera `assets/maps/stage0/stage0.tmx`: el prólogo y escenario de referencia.

AUD-112 — por qué se reescribió este generador
===============================================
El generador anterior declaraba un mapa de **240 × 14** baldosas. El fichero del
repositorio mide **100 × 38**. Llevaban desincronizados el tiempo suficiente
para que nadie recuerde cuál era el bueno: ejecutar el generador habría borrado
el escenario que el juego usa de verdad.

Es el mismo defecto que `stage_mecanicas` previno con una prueba que compara el
fichero con lo que produce su generador. Aquí ya había ocurrido, así que este
generador se reescribe **desde el TMX que hay en producción** —sus ocho capas,
sus dieciocho tipos de objeto, sus diecisiete propiedades de mapa— y se le añade
la misma prueba.

Qué cambia respecto al stage 0 anterior
----------------------------------------
El calificador daba **121/130 (93,1 %)** y señalaba dos cosas reales:

* `design_pacing: 5/8` — «el recorrido no tiene ningún salto exigente». El
  escenario de referencia del profesor **se recorría solo**, y es la misma
  métrica con la que se califica a los estudiantes. Predicar con el ejemplo
  contrario cuesta autoridad.
* `collectibles: 5/10` — sin coleccionables. Tolerable en un tutorial, pero
  `Pickup` existe desde F4.1 y stage 0 es donde un estudiante va a mirar cómo
  se usa.

Y una carencia que el calificador no mide: de las **once mecánicas** de la fase
5 y de los **cuatro objetos interactivos** de F4.1, el prólogo no usaba
ninguno. El escenario que enseña el motor no enseñaba la mitad del motor.

Estructura: siete zonas, las del documento de diseño
------------------------------------------------------
    A  movimiento y salto        (sin peligro)
    B  primer enemigo            (Walker, inevitable — lección de Mario 1-1)
    C  plataformas               + una liana, y el primer salto exigente
    D  combate variado           + llave y puerta
    E  foso                      + bloques rítmicos y pasarela
    F  enemigos a distancia      + viento
    G  todas las habilidades     + tirolesa y cofre
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESTINO = PROJECT_ROOT / "assets" / "maps" / "stage0" / "stage0.tmx"
TILESET = "../../tilesets/tileset_stage0.png"

TS = 16
MW, MH = 100, 38          # 1600 × 608 px — el tamaño que el juego usa de verdad
SUELO_Y = 30              # fila del suelo

# ── Baldosas ────────────────────────────────────────────────────────────────
# AUD-115: la primera versión de este generador declaraba el tileset como
# `tilecount="64" columns="8"` con la imagen de 128 × 128 px, y pintaba todo el
# terreno con las baldosas 1, 2 y 3. `tileset_stage0.png` mide **1024 × 1024**
# y tiene **4096** baldosas de 64 columnas: el mapa regenerado dibujaba las
# baldosas equivocadas —las tres primeras de la hoja, casi negras— en vez del
# corredor de piedra.
#
# Ni el calificador ni el validador de TMX lo vieron: los dos comprueban que el
# tileset **exista**, no que la hoja declarada tenga el tamaño de la hoja real.
# Lo delató `test_de_noche_el_nivel_sigue_siendo_jugable`, que mide píxeles en
# pantalla, con un 24 % de legibilidad a medianoche frente al 38 % de antes.
#
# Los identificadores de abajo son los que usaba el mapa en producción.
TS_COLUMNAS = 64
TS_TOTAL = 4096
TS_IMAGEN_PX = 1024

VACIO = 0
SUELO_SUPERFICIE = 409        # la fila que se pisa
SUELO_RELLENO_A = 665         # relleno, filas pares
SUELO_RELLENO_B = 668         # relleno, filas impares
MURO_IZQUIERDO = 153          # columna de cierre de la izquierda
MURO_DERECHO = 160            # columna de cierre de la derecha
PLATAFORMA = 666              # repisa atravesable
BORDE = 161                   # remate bajo las repisas

#: El foso de la zona E, en baldosas. Se cruza saltando o por la pasarela de
#: encima: dos soluciones para el mismo obstáculo es lo que separa un nivel de
#: un pasillo.
FOSO_X0, FOSO_X1 = 62, 68

#: Obstáculos sólidos interiores `(columna, alto en baldosas)`.
#:
#: El prólogo no tenía ninguno: sus únicas cajas sólidas eran el suelo y los dos
#: muros de cierre del mapa. Un escenario sin nada contra lo que chocar no
#: enseña la mitad más básica de la colisión —el eje horizontal— y la prueba
#: `test_andar_contra_un_solido_detiene_al_jugador` se saltaba en silencio por
#: no encontrar contra qué chocar. Una prueba que se salta es una prueba que no
#: existe.
#:
#: Dos alturas a propósito: 2 baldosas se salta desde parado, 3 obliga a
#: aprovechar el impulso. La segunda guarda la llave de la zona D.
OBSTACULOS: tuple[tuple[int, int], ...] = ((10, 2), (46, 3))


def _relleno(y: int) -> int:
    """Alterna las dos baldosas de relleno para que el suelo no se vea liso."""
    return SUELO_RELLENO_A if (y - SUELO_Y) % 2 else SUELO_RELLENO_B


def _terreno() -> list[list[int]]:
    g = [[VACIO] * MW for _ in range(MH)]
    for x in range(MW):
        g[SUELO_Y][x] = SUELO_SUPERFICIE
    for y in range(SUELO_Y + 1, MH):
        for x in range(MW):
            g[y][x] = _relleno(y)

    for y in range(SUELO_Y, MH):
        for x in range(FOSO_X0, FOSO_X1):
            g[y][x] = VACIO

    for x in range(26, 32):
        g[SUELO_Y - 4][x] = PLATAFORMA
    for x in range(36, 42):
        g[SUELO_Y - 7][x] = PLATAFORMA
    for x in range(86, 94):
        g[SUELO_Y - 9][x] = PLATAFORMA

    for y in range(MH):
        g[y][0] = MURO_IZQUIERDO
        g[y][MW - 1] = MURO_DERECHO

    # Los obstáculos se rematan con la baldosa de superficie arriba y relleno
    # debajo: se leen como un bloque de terreno, no como una pared flotante.
    for x, alto in OBSTACULOS:
        g[SUELO_Y - alto][x] = SUELO_SUPERFICIE
        for y in range(SUELO_Y - alto + 1, SUELO_Y):
            g[y][x] = BORDE
    return g


def _objetos() -> list[str]:
    o: list[str] = []
    ident = [200]

    def obj(tipo: str, x: int, y: int, w: int, h: int, **props: object) -> None:
        ident[0] += 1
        cabecera = (
            f'  <object id="{ident[0]}" name="{tipo}_{ident[0]}" type="{tipo}"'
            f' x="{x}" y="{y}" width="{w}" height="{h}"'
        )
        # Sin propiedades, Tiled cierra la etiqueta en la misma línea. Emitir
        # `<object ...></object>` es XML válido pero no es lo que un estudiante
        # ve al abrir su mapa, y una prueba del validador buscaba precisamente
        # la forma auto-cerrada.
        if not props:
            o.append(cabecera + "/>")
            return
        cuerpo = cabecera + ">"
        if props:
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
                cuerpo += f'\n    <property name="{k}"{attr} value="{valor}"/>'
            cuerpo += "\n   </properties>"
        cuerpo += "\n  </object>"
        o.append(cuerpo)

    suelo = SUELO_Y * TS

    obj("PlayerSpawn", 3 * TS, suelo - 48, 16, 32)

    # ── Zona A — moverse y saltar, sin nada que pueda matarte ──
    obj("MessageTrigger_Once", 5 * TS, suelo - 64, 48, 48,
        text="Flechas para moverte. Espacio para saltar.")

    # ── Zona B — el primer enemigo, inevitable ─────────────────
    # En el camino y no a un lado: es la lección de Mario 1-1 del dossier del
    # Top 200, enseñar el castigo por contacto sin una línea de texto. Va
    # después del mensaje de salto para que el jugador ya sepa saltar.
    obj("MessageTrigger_Once", 14 * TS, suelo - 64, 48, 48,
        text="Z ataca. Tambien puedes saltar por encima.")
    obj("Walker", 18 * TS, suelo - 28, 24, 28,
        max_health=2.0, patrol_length=80.0, patrol_speed=60.0, alert_speed=90.0)
    obj("Checkpoint", 22 * TS, suelo - 32, 16, 32, checkpoint_id=0)

    # ── Zona C — plataformas, liana y el primer salto exigente ─
    obj("MessageTrigger_Once", 25 * TS, suelo - 64, 48, 48,
        text="Sube. Con X te agarras a la liana.")
    obj("Vine", 33 * TS, (SUELO_Y - 11) * TS, 8, 11 * TS,
        velocidad=75.0, ancho_de_agarre=12.0)
    obj("Pickup", 38 * TS, (SUELO_Y - 9) * TS, 16, 16,
        item_id="fragmento_1", automatico=True, mensaje="Fragmento 1 de 3.")
    obj("Flying", 30 * TS, suelo - 7 * TS, 20, 14,
        flight_mode="sine", flight_speed=60.0,
        sine_amplitude=32.0, sine_frequency=2.0)
    obj("Checkpoint", 43 * TS, suelo - 32, 16, 32, checkpoint_id=1)

    # ── Zona D — combate variado, llave y puerta ───────────────
    obj("MessageTrigger_Once", 45 * TS, suelo - 64, 48, 48,
        text="La llave abre la puerta del fondo.")
    obj("Key", 47 * TS, suelo - 20, 16, 16,
        item_id="llave_prologo", automatico=True, mensaje="Has cogido la llave.")
    obj("Charger", 50 * TS, suelo - 24, 28, 24, charge_speed=250.0)
    obj("Archer", 54 * TS, suelo - 28, 16, 28, fire_rate=2.0,
        projectile_speed=100.0, projectile_damage=2.0)
    obj("Brute", 57 * TS, suelo - 60, 100, 60, max_health=6.0)
    obj("LockedDoor", 60 * TS, suelo - 3 * TS, TS, 3 * TS,
        key_id="llave_prologo", clase="puerta",
        mensaje_bloqueado="Cerrada. Busca la llave.")
    obj("Checkpoint", 61 * TS, suelo - 32, 16, 32, checkpoint_id=2)

    # ── Zona E — el foso, con dos formas de cruzarlo ───────────
    obj("MessageTrigger_Once", 59 * TS, suelo - 64, 48, 48,
        text="Salta el foso, o cruza por encima.")
    obj("DeathPit", FOSO_X0 * TS, (MH - 2) * TS, (FOSO_X1 - FOSO_X0) * TS, 2 * TS)
    for i in range(3):
        obj("RhythmBlock", (FOSO_X0 + 1 + i * 2) * TS, suelo - 5 * TS, 2 * TS, TS,
            visible_seg=1.8, oculto_seg=1.0, desfase=i * 0.6)
    obj("HazardZone", 70 * TS, suelo - TS, 3 * TS, TS, damage=0.25)

    # ── Zona F — enemigos a distancia y viento ─────────────────
    obj("MessageTrigger_Once", 72 * TS, suelo - 64, 48, 48,
        text="El viento empuja. Espera a que amaine.")
    obj("WindZone", 74 * TS, (SUELO_Y - 10) * TS, 10 * TS, 10 * TS,
        fuerza_x=210.0, fuerza_y=0.0, periodo=3.4)
    # `patrol_length` explícito: sin él el Shooter se queda clavado, y un
    # enemigo a distancia inmóvil se resuelve andando dos pasos a un lado.
    obj("Shooter", 78 * TS, suelo - 24, 16, 24, fire_rate=2.0,
        projectile_speed=100.0, projectile_damage=2.0,
        patrol_length=48.0, patrol_speed=30.0)
    obj("Caster", 81 * TS, suelo - 28, 20, 28)
    obj("Pickup", 76 * TS, suelo - 20, 16, 16,
        item_id="fragmento_2", automatico=True, mensaje="Fragmento 2 de 3.")
    obj("Checkpoint", 84 * TS, suelo - 32, 16, 32, checkpoint_id=3)

    # ── Zona G — todo junto, tirolesa y cofre ──────────────────
    obj("MessageTrigger_Once", 85 * TS, suelo - 64, 48, 48,
        text="Combina todo. U es el ataque definitivo.")
    obj("Assassin", 88 * TS, suelo - 24, 16, 24)
    obj("Walker", 91 * TS, suelo - 28, 24, 28, max_health=2.0)
    obj("Pickup", 90 * TS, (SUELO_Y - 10) * TS, 16, 16,
        item_id="fragmento_3", automatico=True, mensaje="Fragmento 3 de 3.")
    obj("Chest", 93 * TS, (SUELO_Y - 10) * TS, TS, TS,
        contenido="reliquia_prologo", mensaje="Una reliquia del prologo.")
    obj("Zipline", 92 * TS, (SUELO_Y - 10) * TS, 8, 8,
        destino_dx=5 * TS, destino_dy=8 * TS, velocidad=200.0)
    obj("CameraLock", 86 * TS, 0, 14 * TS, MH * TS, lock_y=True)
    obj("NextTrigger", 97 * TS, suelo - 3 * TS, 2 * TS, 3 * TS)

    # ── Focos ──────────────────────────────────────────────────────────
    # La iluminación es material de la Unidad V y el prólogo es donde se
    # enseña, pero el número y la potencia de los focos **no son decoración**:
    # stage 0 declara `day_length=420`, así que a mitad de partida se hace de
    # noche y el ambiente cae al suelo de 0,45.
    #
    # La primera versión de este generador puso 7 focos de intensidad 0,7 en
    # lugar de los 9 de hasta 0,9 que tenía el mapa anterior, y a medianoche
    # sólo el **24 %** de la pantalla quedaba por encima del umbral de
    # legibilidad; a las 20:00, el 17 %. El nivel se volvía injugable a oscuras
    # y nadie lo habría notado hasta jugarlo siete minutos seguidos.
    #
    # Lo cazó `test_de_noche_el_nivel_sigue_siendo_jugable`, que mide píxeles
    # en pantalla y no propiedades del TMX. Los números de abajo están ajustados
    # contra esa medición, no a ojo.
    obj("Light", 6 * TS, suelo - 5 * TS, 16, 16,
        radius=150.0, color="fire", intensity=0.95, flicker=True,
        flicker_speed=3.2, flicker_amount=0.18)
    for i, x in enumerate((14, 22, 30, 38, 46, 54, 60, 70, 78, 86, 94)):
        obj("Light", x * TS, suelo - 6 * TS, 16, 16,
            radius=140.0 + (i % 3) * 10, color="warm",
            intensity=0.85 + (i % 2) * 0.05)
    return o


def _colisiones() -> list[str]:
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
    # Obstáculos interiores: lo único del prólogo contra lo que se choca de lado.
    for x, alto in OBSTACULOS:
        solido(x * TS, (SUELO_Y - alto) * TS, TS, alto * TS)
    # Repisas atravesables desde abajo, que es lo que las hace útiles.
    solido(26 * TS, (SUELO_Y - 4) * TS, 6 * TS, 8, "Platform")
    solido(36 * TS, (SUELO_Y - 7) * TS, 6 * TS, 8, "Platform")
    solido(86 * TS, (SUELO_Y - 9) * TS, 8 * TS, 8, "Platform")
    # La pasarela sobre el foso: la segunda forma de cruzarlo.
    solido((FOSO_X0 - 1) * TS, (SUELO_Y - 8) * TS,
           (FOSO_X1 - FOSO_X0 + 2) * TS, 8, "Platform")
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
