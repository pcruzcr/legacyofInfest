"""El trazado del 4-1b: la misma travesía horizontal del 4-1
(AUD-467/518), pero sumergida.

Por qué el mismo largo y la misma forma
=========================================
4.1b es una de las tres variantes que puede tocarle al jugador en el slot
de la Fase 4 (AUD-518, `src/stages/stage4_1/selector.py`) — no un nivel
aparte con su propia identidad estructural. Que sea horizontal, de
900×38 baldosas en seis secciones de 150, es la misma decisión de diseño
que AUD-467 cerró para el cementerio, aplicada al agua: el guion pide una
travesía, y una travesía es horizontal por definición, esté seca o
sumergida.

Por qué no hay suelo sólido en casi todo el mapa
==================================================
El jugador nada, no camina: `FILA_SUELO` marca el lecho marino como
referencia (ahí se apoyan el spawn y los checkpoints, igual que en el
4-1), pero desde la fila 0 hasta un par de filas por encima del lecho es
todo `ZonaDeAgua` — ver `docs/45_SWIMMING_SPEC.md`. No hay lomas, no hay
huecos que saltar: el desafío de este nivel es la persecución del pez
abismal, no la plataforma.
"""
from __future__ import annotations

#: Lado de la baldosa, en píxeles.
TS = 16

#: Mismas proporciones que `stage4_1/trazado.py` — seis secciones de 150
#: columnas (AUD-518: es la misma travesía, sumergida).
ANCHO_SECCION = 150
MW = ANCHO_SECCION * 6
MH = 38

#: El lecho marino. Referencia para el spawn y los checkpoints — el
#: jugador nada libremente por encima, no camina sobre él.
FILA_SUELO = 32

#: Grosor de los muros de los extremos, en columnas.
MURO_ANCHO = 2

#: Hasta qué fila llega el agua, desde arriba (fila 0). Dos filas de
#: margen sobre el lecho marino: lo bastante para que el lecho se vea
#: como fondo, no para dejar aire por encima en el que emerger — este
#: nivel no tiene superficie a la que salir, es sumergido de principio a
#: fin.
FILA_SUPERFICIE_AGUA = 0
FILA_FONDO_AGUA = FILA_SUELO - 1


def fase_de_la_columna(columna: int) -> int:
    """La sección, 1 a 6, a la que pertenece esa columna del mapa —mismo
    cálculo que `stage4_1.trazado.fase_de_la_columna`, para que las
    pruebas y el diseño de checkpoints puedan razonar igual en las dos
    variantes."""
    return min(6, columna // ANCHO_SECCION + 1)


#: Seis checkpoints, uno por sección — misma densidad y mismo motivo que
#: AUD-516 en el 4-1: un escenario psicológico de terror no reaparece
#: casi al instante. Columnas elegidas cerca del principio de cada
#: sección, en terreno llano (aquí todo el lecho es llano, no hace falta
#: esquivar un set piece como en el 4-1).
COLUMNAS_CHECKPOINT: tuple[int, ...] = (20, 170, 320, 470, 620, 770)


def checkpoints() -> tuple[tuple[int, int], ...]:
    """Los puntos de reaparición, en `(columna, fila)` — sobre el lecho
    marino, igual que en el 4-1 se apoyan en el suelo sólido."""
    return tuple((c, FILA_SUELO) for c in COLUMNAS_CHECKPOINT)
