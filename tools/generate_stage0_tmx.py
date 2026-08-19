#!/usr/bin/env python3
"""
Genera `assets/maps/stage0/stage0.tmx`: el prólogo y escenario de referencia.

AUD-491 — rediseño completo, no un repintado
==============================================
El trazado anterior (AUD-112..115) tenía siete zonas correctas y bien medidas,
pero se congeló ahí: dos sistemas construidos después de esa fecha —capas de
colisión con material por zona (AUD-490, GAP-039) y el impulso al golpear un
proyectil (AUD-305, *bash*)— llevaban desde entonces sin aparecer en ningún
nivel real. El escenario que enseña el motor no enseñaba lo último que el
motor aprendió a hacer. `stage0.py` (la lógica en Python: colecciones,
umbrales de zona) también se había desincronizado del trazado real — su
docstring describía seis zonas con otros nombres y sus coleccionables
apuntaban a posiciones que ningún `.tmx` había tenido nunca.

Qué cambia de verdad, no sólo de número
-----------------------------------------
* **Orden nuevo.** El combate a distancia entra en la zona D, antes de la
  variedad cuerpo a cuerpo — un estudiante aprende a esquivar un proyectil
  antes de tener que gestionar tres tipos de enemigo a la vez.
* **Materiales por zona (AUD-490), su primer uso real.** Una plataforma de
  hielo en la zona C obliga a soltar el salto con margen; una zona de goma en
  el foso (zona F) es la tercera forma de cruzarlo, además de saltar o
  cronometrar los bloques.
* **El *bash* (AUD-305), su primer uso real.** El arquero de la zona D dispara
  flechas con `admite_bash=True` y un mensaje lo explica — hasta ahora la
  mecánica existía, probada, y ningún nivel la mostraba.
* **Física sin tocar.** El salto sigue midiendo 72 px; los obstáculos
  interiores siguen en 2 y 3 baldosas por el mismo motivo de siempre —el
  primero se salta desde parado, el segundo exige impulso—. Cambiar eso
  habría exigido recalibrar `grade_stage.py` y los 16 mapas que comparten su
  vara de medir, que es justo el coste que `KNOWN_GAPS.md` (GAP-036) ya
  documentó como desproporcionado para un rediseño de contenido.

Estructura: siete zonas, en el orden nuevo
---------------------------------------------
    A  primeros pasos             movimiento, salto, primer sólido
    B  contacto y consecuencia    Walker inevitable — lección de Mario 1-1
    C  la ruta vertical           plataformas, liana, hielo, salto exigente
    D  fuego de respuesta         arquero con bash, esquivar a distancia
    E  la llave guardada          combate variado cuerpo a cuerpo, puerta
    F  el foso                    salto, bloques rítmicos, o goma — tres rutas
    G  todo junto                 viento, tirolesa, cofre, la despedida
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
# AUD-115: `tileset_stage0.png` mide 1024×1024 px, 4096 baldosas de 64
# columnas. Declarar otra cosa aquí pinta el terreno equivocado sin que el
# validador ni el calificador lo detecten — los dos comprueban que el
# tileset exista, no que su tamaño declarado coincida con el real.
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

#: El foso de la zona F, en baldosas. Tres soluciones para el mismo
#: obstáculo: saltarlo, cronometrar los bloques rítmicos, o cruzar la zona
#: de goma que rebota — es lo que separa un nivel de un pasillo con examen.
#:
#: AUD-536 — el foso medía 6 baldosas (96 px) y la envolvente real del
#: jugador pone el techo experto en 85,5 px (`JumpEnvelope.max_gap_expert`,
#: AUD-504): "saltar el foso" —la primera de las tres rutas que el propio
#: cartel anuncia— era físicamente imposible, y el calificador de referencia
#: (`grade_stage stage0 --minimo 100`) perdía 3 pts por la plataforma del
#: otro lado (huérfana para el grafo) y 3 por "ningún salto exigente".
#: Con 5 baldosas (80 px) el salto entra en la banda exigente (34,2–85,5):
#: el grafo conecta el otro lado, el nivel vuelve a puntuar 130/130 y la
#: técnica de soltar la dirección al despegar (documentada en
#: `level_metrics.JumpEnvelope`) tiene dónde enseñarse. Los bloques
#: rítmicos y la goma siguen siendo las rutas cómodas.
FOSO_X0, FOSO_X1 = 67, 72

#: Obstáculos sólidos interiores `(columna, alto en baldosas)`.
#:
#: Dos alturas a propósito, y el número no cambia con el rediseño porque no
#: es una decisión de contenido: **2 baldosas se salta desde parado, 3
#: obliga a aprovechar el impulso**, medido contra los 72 px reales del
#: salto del jugador (`tests/playtest/jump_bench.py`). Subir esto exigiría
#: recalibrar el salto entero, no repintar un nivel.
#:
#: Columna 18 y no 50 (AUD-506): la colina de la zona C ocupa 24-50, y un
#: obstáculo de pared ahí quedaría enterrado dentro del propio sólido de la
#: colina —mismo tramo, misma altura, cero efecto—. 18 sigue en terreno llano,
#: entre el primer obstáculo y el pie de la colina.
OBSTACULOS: tuple[tuple[int, int], ...] = ((10, 2), (18, 3))


def _relleno(y: int) -> int:
    """Alterna las dos baldosas de relleno para que el suelo no se vea liso."""
    return SUELO_RELLENO_A if (y - SUELO_Y) % 2 else SUELO_RELLENO_B


#: AUD-506 — fuente única de la colina de la zona C.
#:
#: `_terreno()` y `_colisiones()` leían el mismo dibujo de dos sitios
#: distintos: el primero lo pintaba baldosa a baldosa y el segundo seguía
#: colocando dos `Platform` de la versión anterior (dos repisas flotando en
#: otra posición y otra altura), sin relación con la escalera nueva. El
#: resultado: una colina que se ve y no se pisa — el suelo real seguía siendo
#: la fila plana de siempre por debajo del dibujo. Con una sola función que
#: devuelve la altura en baldosas de cada columna, pintar y colisionar no
#: pueden divergir otra vez.
def _altura_colina(x: int) -> int:
    """Altura de la colina en baldosas sobre `SUELO_Y`, o 0 fuera de ella."""
    if 24 <= x <= 29:
        return x - 24
    if 30 <= x <= 44:
        return 6
    if 45 <= x <= 50:
        return 6 - (x - 45)
    return 0


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

    # Zona C — AUD-491 (segunda pasada): una colina de verdad, no dos
    # repisas flotando sobre suelo llano. Escalones de 1 baldosa —se suben
    # de un salto corto, no hace falta una `Slope` diagonal— y `_colisiones`
    # usa la misma `_altura_colina` para que el sólido nunca se desvíe del
    # dibujo (AUD-506: antes se desviaba, y la colina se veía y no se pisaba).
    for x in range(24, 51):
        alto = _altura_colina(x)
        if alto == 0:
            continue
        for y in range(SUELO_Y - alto, SUELO_Y):
            g[y][x] = BORDE
        g[SUELO_Y - alto][x] = SUELO_SUPERFICIE

    # Zona E — AUD-491: la ruta alta que bordea el muro y la puerta, la
    # bifurcación real de la zona (no un desnivel puntual). Se pinta como
    # repisa de un solo sentido; el `Platform` que la hace sólida vive en
    # `_colisiones`.
    for x in range(58, 68):
        g[SUELO_Y - 9][x] = PLATAFORMA

    # Zona G — la plataforma alta del tramo final.
    for x in range(88, 96):
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

    # ── Zona A — primeros pasos, sin nada que pueda matarte ────
    obj("MessageTrigger_Once", 5 * TS, suelo - 64, 48, 48,
        text="Flechas para moverte. Espacio para saltar.")

    # ── Zona B — contacto y consecuencia ────────────────────────
    # En el camino y no a un lado: la lección de Mario 1-1, castigo por
    # contacto sin una línea de texto. Va después del mensaje de salto para
    # que el jugador ya sepa saltar cuando se le ofrece esa salida.
    obj("MessageTrigger_Once", 14 * TS, suelo - 64, 48, 48,
        text="Z ataca. Tambien puedes saltar por encima.")
    obj("Walker", 18 * TS, suelo - 28, 24, 28,
        max_health=2.0, patrol_length=80.0, patrol_speed=60.0, alert_speed=90.0)
    obj("Checkpoint", 22 * TS, suelo - 32, 16, 32, checkpoint_id=0)

    # ── Zona C — la ruta vertical, con hielo ────────────────────
    # AUD-506: todo este bloque se repuso sobre `_altura_colina` — la colina
    # ahora es sólida (antes se veía y no se pisaba), así que lo que colgaba
    # o se apoyaba a la altura de las dos `Platform` que había antes tenía
    # que moverse a la altura real del escalón o la meseta bajo cada objeto.
    obj("MessageTrigger_Once", 25 * TS, suelo - 64, 48, 48,
        text="Sube. Con X te agarras a la liana.")
    # La liana cuelga desde encima de la meseta (fila 19) hasta su superficie
    # (fila 24, `_altura_colina(33) == 6`) — antes bajaba hasta la fila 30 y
    # el tramo final quedaba enterrado dentro del sólido nuevo de la meseta.
    obj("Vine", 33 * TS, (SUELO_Y - 11) * TS, 8, 5 * TS,
        velocidad=75.0, ancho_de_agarre=12.0)
    obj("Pickup", 29 * TS, (SUELO_Y - 4) * TS - TS, 16, 16,
        item_id="fragmento_1", automatico=True, mensaje="Fragmento 1 de 3.")
    obj("Flying", 30 * TS, suelo - 7 * TS, 20, 14,
        flight_mode="sine", flight_speed=60.0,
        sine_amplitude=32.0, sine_frequency=2.0)
    # AUD-491/AUD-490 — primer uso real de una zona de material. El hielo no
    # es una baldosa distinta: es la misma repisa con una propiedad de
    # física encima, para que se lea «esta repisa está tomada», no «hay tres
    # tipos de suelo». Fila 24: la superficie real de la meseta.
    obj("MessageTrigger_Once", 36 * TS, (SUELO_Y - 6) * TS - 48, 48, 48,
        text="Hielo. Sueltas menos el salto, no mas.")
    obj("FrictionZone", 36 * TS, (SUELO_Y - 6) * TS, 7 * TS, TS,
        multiplicador=0.55, material="hielo")
    obj("Checkpoint", 43 * TS, (SUELO_Y - 6) * TS - 32, 16, 32, checkpoint_id=1)

    # ── Zona D — fuego de respuesta ──────────────────────────────
    # AUD-305/AUD-491 — primer uso real del bash: un proyectil marcado
    # `admite_bash` y un mensaje que explica que golpearlo, no sólo
    # esquivarlo, es una opción.
    obj("MessageTrigger_Once", 45 * TS, suelo - 64, 48, 48,
        text="Esa flecha se puede golpear para impulsarte.")
    obj("Archer", 49 * TS, suelo - 28, 16, 28, fire_rate=1.6,
        projectile_speed=90.0, projectile_damage=1.5, admite_bash=True)
    obj("Caster", 52 * TS, suelo - 28, 20, 28)
    obj("Pickup", 54 * TS, suelo - 20, 16, 16,
        item_id="fragmento_2", automatico=True, mensaje="Fragmento 2 de 3.")
    obj("Checkpoint", 55 * TS, suelo - 32, 16, 32, checkpoint_id=2)

    # ── Zona E — la llave guardada ────────────────────────────────
    obj("MessageTrigger_Once", 57 * TS, suelo - 64, 48, 48,
        text="La llave abre la puerta del fondo.")
    obj("Key", 59 * TS, suelo - 20, 16, 16,
        item_id="llave_prologo", automatico=True, mensaje="Has cogido la llave.")
    obj("Charger", 62 * TS, suelo - 24, 28, 24, charge_speed=250.0)
    obj("Brute", 65 * TS, suelo - 60, 100, 60, max_health=6.0)
    obj("LockedDoor", FOSO_X0 * TS - TS, suelo - 3 * TS, TS, 3 * TS,
        key_id="llave_prologo", clase="puerta",
        mensaje_bloqueado="Cerrada. Busca la llave.")
    obj("Checkpoint", 65 * TS, suelo - 32, 16, 32, checkpoint_id=3)

    # ── Zona F — el foso, tres formas de cruzarlo ────────────────
    # A una baldosa del borde del foso, no ocho: ocho caía dentro de la
    # zona E y el aviso llegaba antes de que el jugador hubiera visto la
    # llave.
    obj("MessageTrigger_Once", (FOSO_X0 - 1) * TS - TS, suelo - 64, 48, 48,
        text="Salta, cronometra los bloques, o prueba la goma.")
    obj("DeathPit", FOSO_X0 * TS, (MH - 2) * TS, (FOSO_X1 - FOSO_X0) * TS, 2 * TS)
    for i in range(3):
        obj("RhythmBlock", (FOSO_X0 + 1 + i) * TS, suelo - 5 * TS, TS, TS,
            visible_seg=1.8, oculto_seg=1.0, desfase=i * 0.6)
    # AUD-490/AUD-491 — la goma es la tercera ruta: aterrizar aquí devuelve
    # velocidad vertical (`Material.GOMA`, restitución 0,6) en vez de
    # frenar en seco, así que cruza el foso rebotando en dos tiempos.
    obj("FrictionZone", (FOSO_X0 - 1) * TS, (MH - 2) * TS, TS, 2 * TS,
        material="goma")
    obj("HazardZone", (FOSO_X1 + 2) * TS, suelo - TS, 3 * TS, TS, damage=0.25)

    # ── Zona G — todo junto ───────────────────────────────────────
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

    # ── Focos ──────────────────────────────────────────────────────────
    # La iluminación es material de la Unidad V y el prólogo es donde se
    # enseña, pero el número y la potencia de los focos no son decoración:
    # stage 0 declara `day_length=420`, así que a mitad de partida se hace
    # de noche y el ambiente cae al suelo de 0,45. Los números de abajo
    # están calibrados contra `test_de_noche_el_nivel_sigue_siendo_jugable`,
    # que mide píxeles en pantalla, no propiedades del TMX.
    obj("Light", 6 * TS, suelo - 5 * TS, 16, 16,
        radius=150.0, color="fire", intensity=0.95, flicker=True,
        flicker_speed=3.2, flicker_amount=0.18)
    for i, x in enumerate((14, 22, 30, 38, 46, 54, 62, 70, 78, 86, 94)):
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
    # AUD-506 — la colina de la zona C, un sólido por columna con
    # `_altura_colina` (la misma función que pinta `_terreno`), rellenando
    # desde el escalón hasta el suelo plano de abajo. Antes de esto la colina
    # se veía y no se pisaba: el suelo real seguía siendo la fila plana bajo
    # el dibujo, y los dos `Platform` que había aquí eran repisas de un
    # diseño anterior en otra posición y otra altura.
    for x in range(24, 51):
        alto = _altura_colina(x)
        if alto:
            solido(x * TS, (SUELO_Y - alto) * TS, TS, alto * TS)
    # Zona E — la ruta alta bypass, atravesable desde abajo (por eso es
    # "Platform" y no "Solid": se puede saltar a través de ella y aterrizar
    # encima, como el bypass gemelo de la zona G, dos líneas más abajo).
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
