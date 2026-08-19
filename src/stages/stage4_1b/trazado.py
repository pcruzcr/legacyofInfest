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


# AUD-543 — «corrientes de agua», pedido tras jugarlo. `ZonaDeAgua.corriente`
# (`src/framework/ecs/components.py`) ya existía en el motor —lo aplica
# `sistema_corriente_de_agua`— y ningún escenario lo declaraba nunca: cero
# menciones de `corriente_x` en los 26 TMX de referencia antes de esto.
#
# Sólo empuje horizontal, nunca vertical: `SwimmingState.update` fija
# `_surface_y` una sola vez, al entrar al estado (la Y del jugador en ese
# instante), y si luego sube más de 8px por encima de esa referencia sale
# de nado hacia `JumpingState` — pensado para niveles con una superficie de
# verdad a la que emerger. 4.1b no tiene superficie (`docs/45_SWIMMING_SPEC.md`,
# "sumergido de principio a fin"): una corriente vertical fuerte empujaría
# al jugador fuera del estado de nado en pleno abismo. Se documenta aquí y
# no se toca `swim.py` — ese comportamiento es correcto para los niveles
# que sí tienen superficie, y "arreglarlo" sin uno a mano rompería esos.
#
# (columna_inicio, columna_fin, corriente_x). El signo sigue la lectura del
# mapa: positivo empuja hacia la derecha (con el sentido normal de avance),
# negativo hacia la izquierda (en contra).
#
# Magnitud verificada por simulación, no a ojo (el nado no clampa la
# velocidad total tras sumar la corriente — sólo clampa el empuje que pone
# el propio jugador — así que el efecto de la corriente sí se acumula
# fotograma a fotograma en vez de borrarse en el siguiente):
#   · -30.0 en contra: nadando a fondo, la velocidad converge a un régimen
#     estable de 90 px/s (contra 120 px/s sin corriente) — un 25% más
#     lento, un 44% menos de distancia recorrida en los mismos 3 s. Se
#     nota, no bloquea: a 90 px/s se cruzan los 2400 px de la sección en
#     ~27 s, bastante menos que cualquier persecución del pez (5-9 s).
#   · +35.0 / +45.0 a favor: nadando a fondo no cambia casi nada (el tope
#     de 120 px/s ya estaba saturado sin corriente) — donde sí se nota es
#     a la deriva, sin tecla pulsada: ahí la corriente empuja a un régimen
#     estable de ±5 a 6 px/s (antes, cero). Es un efecto sutil a propósito
#     — "el agua te lleva si dejas de nadar", no un raíl que mueva solo.
ZONAS_DE_CORRIENTE: tuple[tuple[int, int, float], ...] = (
    # Sección 2: a favor — un tramo de respiro tras el primer susto del pez.
    (ANCHO_SECCION * 1, ANCHO_SECCION * 2, 35.0),
    # Sección 4: en contra — resistencia justo antes de la mitad del tramo,
    # cuando el pez ya volvió a aparecer al menos una vez.
    (ANCHO_SECCION * 3, ANCHO_SECCION * 4, -30.0),
    # Cola de la sección 6: a favor, un empujón final hacia la salida.
    (ANCHO_SECCION * 5 + 50, ANCHO_SECCION * 6, 45.0),
)
