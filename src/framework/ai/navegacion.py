"""
Module: navegacion
System: framework.ai
Academic Unit: VI (grafos y búsqueda de caminos)

AUD-389 — A* sobre la rejilla de tiles. Cierra GAP-045.

El hueco, y su consumidor
=========================
`sistema_acosador` perseguía al jugador con `hacia.normalize()`: línea recta,
atravesando muros. Un perseguidor que se empotra en una pared y tiembla contra
ella no da la tensión de Nemesis que su propio docstring describe.

Este módulo no es un sistema nuevo buscando quién lo use: es la pieza que le
faltaba a un comportamiento que ya estaba mal.

Por qué A* y no lo que ya había
===============================
`RejillaEspacial` (AUD-276) contesta «¿qué hay **entre** estos dos puntos?»,
que sirve para la línea de visión (AUD-381) y no para rodear: saber que hay un
muro no dice por dónde pasar. Y los `Waypoint` del TMX son una **ruta
declarada**, útil cuando el diseñador quiere control y muda cuando el jugador
está en un sitio que nadie previó.

Por qué no se re-planifica cada fotograma
------------------------------------------
Porque el coste no sería «un A*», sería «un A* por enemigo y por fotograma».
La cadencia es de cuatro veces por segundo y **escalonada**: cada navegante
nace con una espera inicial distinta, así que treinta enemigos que aparecen
juntos no piensan juntos. Es el mismo patrón que `SquadBrain` usa con su
predicción por lote (AUD-050), y por el mismo motivo — el coste por fotograma
queda acotado en vez de depender de cuántos hayan decidido pensar a la vez.

El tope de nodos es la red de seguridad: en un mapa grande sin camino posible,
A* exploraría la superficie entera antes de rendirse. Con tope devuelve «no hay
ruta» y el que llama decide, que es mejor que un fotograma de 300 ms.

Lo que cuesta, medido
=====================
Sobre `stage4_1` —el mapa más grande: malla de 60 × 240 celdas, 3.230
bloqueadas— y con consultas a la distancia real a la que persigue el acosador
(480 px = 30 celdas):

| Tope de nodos | ms por consulta | Rutas halladas |
|---|---|---|
| 1.500 | 3,616 | 192 de 200 |
| 400 | 1,830 | 80 de 200 |
| 150 | 0,877 | 39 de 200 |

Bajar el tope abarata y **rompe la característica**: con 400 falla más de la
mitad de las veces, y un perseguidor que no encuentra ruta se empotra
exactamente igual que antes de este módulo. Por eso el tope se queda alto y lo
que se acota es **cuántas consultas por fotograma**, no cuánto cuesta cada una.

Con la cadencia de 4 Hz escalonada, el coste por fotograma sale de multiplicar
navegantes × 4 ÷ 60:

    1 navegante  → 0,241 ms   (1,4 % del presupuesto)
    4 navegantes → 0,964 ms   (5,8 %)
   30 navegantes → 7,232 ms   (43,4 %)

**El envolvente utilizable son unos pocos navegantes**, que es justo el caso
para el que existe: el acosador es un enemigo especial —Nemesis, el conserje de
Celeste— y un mapa lleva uno o dos. Treinta perseguidores simultáneos se comen
casi la mitad del fotograma, y conviene saberlo antes de llenar una sala y no
después.

Construir la malla cuesta 0,65 ms y se hace **una vez por escenario**, no por
fotograma: es el mismo razonamiento que AUD-379 aplicó a la rejilla espacial.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field

import pygame

#: Cada cuánto re-planifica un navegante, en segundos. Cuatro veces por segundo
#: es lo que usa `SquadBrain` para su reevaluación táctica, y por la misma
#: razón: por debajo no se nota, y por encima se paga sin que se vea.
CADENCIA: float = 0.25

#: Tope de nodos que A* expande antes de rendirse. 1.500 cubre de sobra un
#: recorrido con rodeos en los mapas de este repositorio —el mayor tiene 310×24
#: tiles y el envolvente útil de un perseguidor es mucho menor— y acota el peor
#: caso, que es un mapa cerrado donde no hay camino.
TOPE_DE_NODOS: int = 1_500

#: Los cuatro vecinos, sin diagonales. Sin diagonales a propósito: en un
#: plataformas con tiles, un paso diagonal atraviesa la esquina entre dos muros
#: y produce rutas que el cuerpo no puede recorrer.
_VECINOS: tuple[tuple[int, int], ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass(slots=True)
class MallaDeNavegacion:
    """Qué celdas se pueden pisar. Se construye una vez por escenario."""

    ancho: int
    alto: int
    tile: int
    bloqueadas: set = field(default_factory=set)

    @classmethod
    def desde_rects(cls, solidos, ancho_px: int, alto_px: int,
                    tile: int = 16) -> MallaDeNavegacion:
        """Marca como intransitable toda celda que toque un sólido.

        Se redondea hacia fuera —una celda tocada a medias cuenta como
        bloqueada— porque el error caro es el contrario: una ruta que pasa por
        media pared es una ruta que el cuerpo no puede recorrer, y el enemigo
        se queda encallado exactamente igual que antes de este módulo.
        """
        malla = cls(ancho=max(1, ancho_px // tile), alto=max(1, alto_px // tile),
                    tile=tile)
        for r in solidos:
            cx0, cy0 = r.left // tile, r.top // tile
            cx1 = (r.right - 1) // tile
            cy1 = (r.bottom - 1) // tile
            for cy in range(cy0, cy1 + 1):
                for cx in range(cx0, cx1 + 1):
                    malla.bloqueadas.add((cx, cy))
        return malla

    def transitable(self, cx: int, cy: int) -> bool:
        if not (0 <= cx < self.ancho and 0 <= cy < self.alto):
            return False
        return (cx, cy) not in self.bloqueadas

    def celda_de(self, punto: pygame.Vector2) -> tuple[int, int]:
        return (int(punto.x) // self.tile, int(punto.y) // self.tile)

    def centro_de(self, celda: tuple[int, int]) -> pygame.Vector2:
        return pygame.Vector2(
            celda[0] * self.tile + self.tile / 2,
            celda[1] * self.tile + self.tile / 2,
        )


def a_estrella(malla: MallaDeNavegacion, inicio: tuple[int, int],
               meta: tuple[int, int], tope: int = TOPE_DE_NODOS) -> list:
    """El camino de `inicio` a `meta`, sin incluir el origen.

    Devuelve **lista vacía** cuando no hay camino, cuando ya se está en la
    meta, cuando la meta está dentro de un muro o cuando se agota el tope. Es
    deliberado que los cuatro casos se vean igual desde fuera: el que llama
    sólo necesita saber si tiene ruta, y distinguirlos le obligaría a cuatro
    ramas que trataría igual.

    La heurística es Manhattan, que es la admisible para movimiento en cuatro
    direcciones: nunca sobreestima, así que A* sigue devolviendo el camino más
    corto. Con diagonales habría que cambiarla, y por eso no las hay.
    """
    if inicio == meta:
        return []
    if not malla.transitable(*meta) or not malla.transitable(*inicio):
        return []

    def h(c: tuple[int, int]) -> int:
        return abs(c[0] - meta[0]) + abs(c[1] - meta[1])

    abiertos: list = [(h(inicio), 0, inicio)]
    de_donde: dict = {}
    coste: dict = {inicio: 0}
    expandidos = 0

    while abiertos:
        _, g, actual = heapq.heappop(abiertos)
        if actual == meta:
            ruta = [actual]
            while ruta[-1] in de_donde:
                ruta.append(de_donde[ruta[-1]])
            ruta.reverse()
            return ruta[1:]

        expandidos += 1
        if expandidos > tope:
            return []

        for dx, dy in _VECINOS:
            vecino = (actual[0] + dx, actual[1] + dy)
            if not malla.transitable(*vecino):
                continue
            nuevo = g + 1
            if nuevo < coste.get(vecino, 1 << 30):
                coste[vecino] = nuevo
                de_donde[vecino] = actual
                heapq.heappush(abiertos, (nuevo + h(vecino), nuevo, vecino))
    return []
