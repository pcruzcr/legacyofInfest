"""
Module: rejilla
System: framework.stage
Academic Unit: VI (colisiones y particionado del espacio)

AUD-276 — la rejilla espacial y el trazado de rayos.

Qué problema resuelve
=====================
Todo lo que pregunta «¿qué hay aquí?» recorría `stage.collision_rects` de punta
a punta: la sombra bajo los pies (AUD-273), el suelo del jugador, las zonas de
daño. `stage4_1` trae miles de rectángulos y la inmensa mayoría están a
pantallas de distancia de la pregunta.

Y no había forma de preguntar «¿qué hay **entre** este punto y aquel otro?».
Sin eso no se puede hacer la línea de visión de un guardia, ni un disparo
instantáneo, ni comprobar si una plataforma tapa un foco.

Por qué una rejilla uniforme y no un árbol
-------------------------------------------
Porque los rectángulos de un TMX son **estáticos** y están repartidos de forma
bastante pareja: es justo el caso en el que una rejilla uniforme iguala o gana
a un quadtree, sin su coste de construcción ni su código.

Y porque esto es material de curso: una rejilla se explica en tres líneas —el
mundo en celdas, cada cosa apuntada en las que toca— y un quadtree no.

Cómo se usa
-----------
Es **aditiva**: se construye desde la lista que el cargador ya produce y no
cambia ningún contrato. Nada del motor la usa todavía; quien no la use no paga
nada.

    rejilla = RejillaEspacial(stage.collision_rects)
    cerca = rejilla.cercanos(jugador.rect.inflate(64, 64))
    if rejilla.hay_vision(guardia.pos, jugador.pos):
        ...
"""
from __future__ import annotations

import pygame

#: Lado de la celda en píxeles. Cuatro baldosas de 16.
#:
#: Ni muy pequeña ni muy grande, y las dos puntas duelen: con celdas de una
#: baldosa, el suelo de un mapa largo se apunta en cientos de ellas y construir
#: la rejilla cuesta más que la búsqueda que ahorra; con celdas de media
#: pantalla, cada consulta devuelve medio mapa y no se ahorra nada.
LADO_DE_CELDA: int = 64


class RejillaEspacial:
    """Rectángulos estáticos indexados por celda.

    Se construye una vez por escenario. **No se actualiza**: es para geometría
    que no se mueve, que es lo que hay en `collision_rects`. Una puerta que se
    abre o un bloque que se empuja no van aquí — ésos se suman aparte, como ya
    hace `StageScene`.
    """

    def __init__(self, rects: list[pygame.Rect],
                 lado: int = LADO_DE_CELDA) -> None:
        self.lado = max(1, int(lado))
        self._celdas: dict[tuple[int, int], list[pygame.Rect]] = {}
        for rect in rects:
            for celda in self._celdas_de(rect):
                self._celdas.setdefault(celda, []).append(rect)

    def _celdas_de(self, rect: pygame.Rect):
        """Las celdas que toca un rectángulo.

        El `+ 1` de los rangos es la parte que se equivoca sola: sin él, un
        rectángulo que acaba justo en el borde de una celda no se apunta en
        ella y desaparece de las consultas que la miran.
        """
        lado = self.lado
        x0, y0 = rect.left // lado, rect.top // lado
        x1, y1 = (rect.right - 1) // lado, (rect.bottom - 1) // lado
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                yield (cx, cy)

    def cercanos(self, zona: pygame.Rect) -> list[pygame.Rect]:
        """Los rectángulos que **podrían** tocar `zona`, sin repetidos.

        Devuelve candidatos, no colisiones: quien pregunta hace el
        `colliderect` final. Filtrar aquí obligaría a decidir por el que llama
        si quiere solape estricto o contacto, y esa decisión es suya.

        Sin repetidos porque un suelo largo cruza muchas celdas, y devolverlo
        una vez por celda haría que quien lo procese lo cuente varias veces.
        """
        vistos: set[int] = set()
        fuera: list[pygame.Rect] = []
        for celda in self._celdas_de(zona):
            for rect in self._celdas.get(celda, ()):
                if id(rect) not in vistos:
                    vistos.add(id(rect))
                    fuera.append(rect)
        return fuera

    def rayo(self, origen: pygame.Vector2,
             destino: pygame.Vector2) -> pygame.Rect | None:
        """El primer rectángulo que corta el segmento, o `None`.

        **El primero desde el origen**, no uno cualquiera: para una línea de
        visión da igual, pero para un disparo instantáneo es toda la mecánica.

        Se avanza a pasos de media celda y se comprueba lo que hay en cada uno.
        No es un DDA exacto —eso sería el algoritmo de Amanatides y Woo— y
        aquí no hace falta: con paso de media celda no se puede saltar un
        rectángulo, porque el más pequeño que el juego admite es una baldosa de
        16 px y la celda mide 64.
        """
        segmento = destino - origen
        largo = segmento.length()
        if largo <= 0.0:
            return None
        paso = self.lado / 2.0
        direccion = segmento / largo
        recorrido = 0.0
        while recorrido <= largo:
            punto = origen + direccion * recorrido
            zona = pygame.Rect(int(punto.x) - 1, int(punto.y) - 1, 3, 3)
            candidatos = self.cercanos(zona)
            if candidatos:
                # Entre los de este paso, gana el más cercano al origen: dentro
                # de una misma celda puede haber varios y el orden de la lista
                # es el de construcción, que no significa nada.
                tocados = [r for r in candidatos if r.clipline(origen, destino)]
                if tocados:
                    return min(tocados, key=lambda r: (
                        pygame.Vector2(r.center) - origen).length_squared())
            recorrido += paso
        return None

    def hay_vision(self, desde: pygame.Vector2, hasta: pygame.Vector2) -> bool:
        """¿Hay línea recta sin geometría en medio?"""
        return self.rayo(desde, hasta) is None
