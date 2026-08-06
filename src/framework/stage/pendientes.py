"""
Module: pendientes
System: framework.stage
Academic Unit: Unidad II — álgebra vectorial
Description: AUD-297 — suelo inclinado, dentro de la resolución de colisión.

Por qué esto no se pudo hacer antes
===================================
`docs/87` §11 lo dejó escrito: las pendientes son «viables con coste», y el
coste es que **cambian la resolución de colisión**, que es el sistema del que
dependen las veintiséis entregas. La recomendación era hacerlo aditivo o no
hacerlo. Se hizo integrado, por decisión explícita, y con la calificación de los
dieciséis mapas como control: antes y después, 79,9 % de media.

Que salga bien no lo garantiza el cuidado, lo garantiza esto: **una pendiente es
un tipo de objeto nuevo y ningún mapa entregado tiene ninguno.** La lista llega
vacía y el paso entero se salta. Lo que cambia para ellos es una comprobación
de lista vacía por fotograma.

Cómo se resuelve, y por qué no es una caja más
==============================================
Una pendiente **no entra en `collision_rects`**. Si entrara, el eje X la trataría
como pared y el jugador se pararía en seco al pie de la rampa — que es
exactamente lo que pasa cuando alguien intenta simular una cuesta apilando
bloques escalonados.

En vez de eso: el eje X se mueve libre, y después se pregunta a la pendiente a
qué altura está su superficie **en la x del jugador**. Si los pies quedan por
debajo de esa altura, suben. Es interpolación lineal, y es la razón de que este
módulo cite la Unidad II: es el mismo cálculo del vector director de una recta
que se enseña en clase, aplicado a algo que se ve.

Bajar también hay que resolverlo
================================
Sin más, al bajar una cuesta el jugador queda un instante en el aire cada
fotograma y desciende a saltitos. `MARGEN_DE_PEGADO` es lo que lo arregla:
estando ya en el suelo, se pega a la superficie aunque esté unos píxeles por
debajo. Es lo que hacen todos los plataformas 2D con cuestas, y sin ello la
mecánica se siente rota aunque los números sean correctos.
"""
from __future__ import annotations

from dataclasses import dataclass

import pygame

#: Píxeles que el jugador puede «caer» de golpe siguiendo la cuesta al bajar.
#:
#: Ocho: la mitad de una baldosa. Con menos se ve el traqueteo al descender;
#: con mucho más, el jugador se pegaría al suelo al salir de la rampa por el
#: borde superior en vez de despegar, que es peor porque impide saltar desde el
#: final de una cuesta.
MARGEN_DE_PEGADO: float = 8.0


@dataclass(frozen=True)
class Pendiente:
    """Un triángulo rectángulo de suelo. La hipotenusa es lo que se pisa."""

    rect: pygame.Rect
    #: `True` si el lado alto está a la derecha.
    sube_a_la_derecha: bool = True

    def altura_en(self, x: float) -> float | None:
        """La `y` de la superficie en esa `x`, o `None` si cae fuera.

        El extremo derecho entra (`<=`): dos pendientes seguidas comparten el
        píxel del borde, y excluirlo dejaría un hueco de un píxel por el que el
        jugador se cuela hasta el suelo de abajo. Un fallo de un píxel que
        aparece una vez de cada veinte es de los que se tarda una tarde en
        reproducir.
        """
        if not (self.rect.left <= x <= self.rect.right):
            return None
        if self.rect.width <= 0:
            return float(self.rect.top)
        avance = (x - self.rect.left) / self.rect.width
        if not self.sube_a_la_derecha:
            avance = 1.0 - avance
        # avance 0 = pie de la cuesta (abajo), 1 = lo alto (arriba).
        return float(self.rect.bottom - avance * self.rect.height)


def resolver(
    rect: pygame.Rect,
    velocidad_y: float,
    en_el_suelo: bool,
    pendientes: list[Pendiente],
) -> float | None:
    """A qué `y` hay que poner los pies, o `None` si ninguna pendiente manda.

    Devuelve la coordenada y no muta el rectángulo: quien lo posee es el
    jugador, y un módulo de geometría que mueve entidades ajenas es cómo se
    acaba con dos sistemas discutiendo la misma posición.

    Reglas, y las tres importan:

    * **Cayendo o quieto** (`velocidad_y >= 0`). Subiendo no: saltar desde una
      cuesta tiene que despegar, no re-pegar al fotograma siguiente.
    * **Los pies dentro de la franja** de la pendiente. Por encima de lo alto
      se está volando por encima; por debajo del pie, se está debajo del
      triángulo y ahí no hay suelo.
    * **Al bajar, con margen.** Ver `MARGEN_DE_PEGADO`.
    """
    if not pendientes or velocidad_y < 0:
        return None

    x = float(rect.centerx)
    pies = float(rect.bottom)
    mejor: float | None = None
    for pendiente in pendientes:
        superficie = pendiente.altura_en(x)
        if superficie is None:
            continue
        # Por debajo del triángulo: el jugador pasa por dentro de la roca, no
        # sobre ella. No es suelo.
        if pies > pendiente.rect.bottom + 1.0:
            continue
        margen = MARGEN_DE_PEGADO if en_el_suelo else 1.0
        if pies < superficie - margen:
            continue
        # Con dos pendientes solapadas gana la más alta: es la que el jugador
        # está pisando de verdad.
        if mejor is None or superficie < mejor:
            mejor = superficie
    return mejor
