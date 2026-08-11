#!/usr/bin/env python3
"""Genera `stage_cenital.tmx` — el mapa que demuestra la vista de arriba.

Por qué existe (AUD-383, GAP-052)
=================================
El motor sabe jugar en **vista cenital** desde AUD-129: `vista=cenital` quita la
gravedad, deja el movimiento en dos ejes y da los tres presets de cámara. Tiene
su preset de física (`PhysicsProfile.cenital()`), sus pruebas
(`test_vista_cenital.py`) y su documentación.

Y **ningún mapa del repositorio lo declaraba**. Un modo de juego entero que el
estudiante no podía descubrir: no lo ve jugando, no lo encuentra abriendo un
mapa en Tiled, y sólo podía enterarse leyendo la especificación — que es justo
lo que no se hace. Lo destapó AUD-378 al arreglar el punto ciego del guardián de
cobertura, y la decisión de hacerlo es del dueño: *«la idea es que todo este
cableado sea para que los estudiantes lo usen»*.

Qué demuestra, y qué no
-----------------------
Cuatro propiedades de mapa que ningún otro declara: `vista`, `camara`,
`profundidad_min` y `profundidad_max`. Nada más. **No es un nivel**: es la
respuesta a «¿cómo se hace un mapa cenital?», y por eso cabe en una pantalla y
media y se lee de un vistazo en Tiled.

Sigue el molde de `stage_mecanicas`: la clase de escenario no tiene lógica
propia, así que todo lo que hace este mapa se puede copiar sin escribir una
línea de Python. Si hiciera falta código, no demostraría lo que pretende.

Por qué tres salas y no una
---------------------------
Porque `camara` tiene tres modos y el mapa existe para enseñarlos. Una sala por
modo, comunicadas, para que se note la diferencia **andando**: `seguir` va
pegada, `zona_muerta` deja moverse sin que la cámara reaccione, y `sala`
encuadra el recinto entero. El mapa declara `sala`, que es el que da sentido a
una planta con habitaciones; los otros dos van comentados en el TMX, a un
carácter de distancia de probarlos.

Por qué sin enemigos
--------------------
Un enemigo en cenital necesita su propia conversación —los arquetipos actuales
asumen plataformas— y mezclarla aquí convertiría «así se declara una vista
cenital» en «así se hace un nivel cenital». El primero es lo que falta.
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESTINO = PROJECT_ROOT / "assets" / "maps" / "stage_cenital" / "stage_cenital.tmx"
TILESET = "../../tilesets/tileset_stage0.png"

TS = 16
#: Tres salas de 18x14 con muros de 1 baldosa entre ellas. Cabe en pantalla y
#: media a 800x600, que es lo que se puede leer de un vistazo en Tiled.
SALA_W, SALA_H = 18, 14
MW = SALA_W * 3 + 4
MH = SALA_H + 2

TS_COLUMNAS = 64
TS_TOTAL = 4096
TS_IMAGEN_PX = 1024

VACIO = 0
#: Los mismos identificadores que usa `stage_mecanicas`, para que el mapa se vea
#: con el tileset del curso y no haya que explicar dos paletas.
SUELO = 409
MURO = 153


def _sala_x(n: int) -> int:
    """Columna donde empieza la sala `n` (0, 1, 2)."""
    return 1 + n * (SALA_W + 1)


def _terreno() -> list[list[int]]:
    """Planta de tres habitaciones: suelo en todas, muros alrededor.

    En cenital el «suelo» es lo que se pisa mirando desde arriba y los muros
    son lo que corta el paso. Es la diferencia que más cuesta ver viniendo de
    plataformas: aquí una baldosa de muro no es una pared que se salta, es una
    pared que se rodea.
    """
    g = [[MURO] * MW for _ in range(MH)]
    for n in range(3):
        x0 = _sala_x(n)
        for y in range(1, MH - 1):
            for x in range(x0, x0 + SALA_W):
                g[y][x] = SUELO
    # Puertas entre salas: una abertura de dos baldosas a media altura, para
    # que se pueda pasar andando y se vea que la camara reacciona al cambiar
    # de recinto.
    for n in range(2):
        x = _sala_x(n) + SALA_W
        for y in (MH // 2 - 1, MH // 2):
            g[y][x] = SUELO
    return g


def _colisiones() -> list[str]:
    """Un rectángulo por tramo de muro, fusionando filas contiguas.

    Se emiten fusionados y no baldosa a baldosa a propósito: un mapa de
    ejemplo con doscientos rectángulos de un tile enseña a hacerlo mal, y el
    resolutor recorre la lista entera (AUD-379).
    """
    g = _terreno()
    salida: list[str] = []
    ident = 100
    for y in range(MH):
        x = 0
        while x < MW:
            if g[y][x] != MURO:
                x += 1
                continue
            inicio = x
            while x < MW and g[y][x] == MURO:
                x += 1
            salida.append(
                f'  <object id="{ident}" x="{inicio * TS}" y="{y * TS}" '
                f'width="{(x - inicio) * TS}" height="{TS}"/>'
            )
            ident += 1
    return salida


def _objetos() -> list[str]:
    """Lo mínimo para que el mapa se pueda jugar: dónde nace el jugador."""
    x = (_sala_x(0) + SALA_W // 2) * TS
    y = (MH // 2) * TS
    return [
        f'  <object id="10" name="PlayerSpawn" type="PlayerSpawn" '
        f'x="{x}" y="{y}" width="{TS}" height="{TS}"/>',
    ]


def generar() -> str:
    g = _terreno()
    csv_terreno = ",".join(str(g[y][x]) for y in range(MH) for x in range(MW))
    ceros = ",".join(["0"] * (MW * MH))

    def capa(i: int, n: str, d: str) -> str:
        return (
            f' <layer id="{i}" name="{n}" width="{MW}" height="{MH}">\n'
            f'  <data encoding="csv">\n{d}\n</data>\n </layer>'
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" \
renderorder="right-down" width="{MW}" height="{MH}" tilewidth="{TS}" \
tileheight="{TS}" infinite="0" nextlayerid="20" nextobjectid="900">
 <properties>
  <property name="schema_version" value="1"/>
  <property name="stage_id" value="stage_cenital"/>
  <property name="stage_name" value="LABORATORIO DE VISTA CENITAL"/>
  <property name="author" value="Equipo docente — Legacy of Infest"/>
  <property name="bgm_track" value="bgm_stage0"/>
  <property name="background_zone" value="stage0"/>
  <property name="climate" value="clear"/>
  <property name="time_limit" value="0"/>
  <property name="zone" type="int" value="0"/>
  <property name="ambient_light" type="float" value="0.85"/>
  <!-- AUD-383 (GAP-052): LA propiedad de este mapa. `cenital` quita la
       gravedad y deja el movimiento en dos ejes; el valor por defecto es
       `lateral`. Cambiar esta linea a `lateral` y volver a jugar es la forma
       mas rapida de entender que hace. -->
  <property name="vista" value="cenital"/>
  <!-- AUD-383: los tres modos de camara, que ningun mapa declaraba. `sala`
       encuadra el recinto entero, que es lo que da sentido a una planta con
       habitaciones. Los otros dos estan a un cambio de palabra:
         seguir       — pegada al jugador, la de siempre
         zona_muerta  — no reacciona hasta salir de un margen central -->
  <property name="camara" value="sala"/>
  <!-- AUD-383: el rango de escala por profundidad (2.5D). En cenital se ve
       distinto que en lateral, y por eso el rango se declara aqui: con
       min == max la escala es plana, que es lo que quiere una vista en planta
       pura. Subir el maximo devuelve la perspectiva. -->
  <property name="profundidad_min" type="float" value="1.0"/>
  <property name="profundidad_max" type="float" value="1.0"/>
  <!-- AUD-384 (GAP-052): la niebla de guerra, que no declaraba ningun mapa.
       Va AQUI y no en el laboratorio de mecanicas por una razon de lectura:
       una vista en planta con niebla es la mazmorra clasica -Zelda- y se
       entiende sola, mientras que oscurecer el laboratorio lateral taparia
       las once mecanicas que ese mapa existe para ensenar.

       220 px de radio deja ver la sala en la que estas y esconde las otras
       dos, que es exactamente lo que la caracteristica hace. Con 0 se apaga
       y el mapa se ve entero: es la comparacion de un solo cambio. -->
  <property name="fog_of_war" type="float" value="220"/>
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
