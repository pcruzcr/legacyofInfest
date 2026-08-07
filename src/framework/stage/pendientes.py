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

Las entradas laterales (AUD-323)
================================
El eje X se mueve libre y el eje Y coloca sobre la hipotenusa; eso deja dos
huecos que `resolver_lateral` tapa: la **cara empinada** —el segmento
vertical del extremo alto, que se atraviesa y luego el eje Y absorbe hacia
arriba— y la hipotenusa a media altura de una rampa estrecha. La regla que
los hace seguros es una sola: **el centro sobre la rampa es territorio del
eje Y**, y un jugador que está pisando la hipotenusa tiene la esquina
hundida unos píxeles en la roca —al subir y al bajar— que es el precio
normal de un suelo de un solo punto de apoyo. Frenar esa esquina rompería
la marcha, así que la pared lateral sólo existe para quien tiene el centro
fuera de la rampa y entra por un lado.

Proyección de velocidad al aterrizar (AUD-324)
==============================================
`docs/87` §11 pidió por escrito "normales de superficie y proyección de
velocidad". La normal está implícita en la hipotenusa; la proyección es
`componente_de_deslizamiento`: al aterrizar, el impulso de la caída se
descompone en el vector director de la superficie, y la componente
perpendicular la absorbe el suelo. Caer en vertical sobre una cuesta de 45°
empuja al jugador cuesta abajo a la mitad de la velocidad de caída — es
seno por coseno, la misma cuenta de la Unidad II — en vez de pararlo en
seco, que es lo que hace que una cuesta se sienta como un suelo y no como
un escalón gigante.
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
    margen: float = MARGEN_DE_PEGADO,
) -> float | None:
    """A qué `y` hay que poner los pies, o `None` si ninguna pendiente manda.

    Devuelve la coordenada y no muta el rectángulo: quien lo posee es el
    jugador, y un módulo de geometría que mueve entidades ajenas es cómo se
    acaba con dos sistemas discutiendo la misma posición.

    Reglas, y las tres importan:

    * **Cayendo o quieto** (`velocidad_y >= 0`). Subiendo no: saltar desde
      una cuesta tiene que despegar, no re-pegar al fotograma siguiente.
    * **Los pies dentro de la franja** de la pendiente. Por encima de lo alto
      se está volando por encima; por debajo del pie, se está debajo del
      triángulo y ahí no hay suelo.
    * **Al bajar, con margen.** Ver `MARGEN_DE_PEGADO`; AUD-333 — el margen
      es parámetro porque un contexto de física distinto (un suelo con otro
      agarre) lo declara en su perfil en vez de heredarlo por defecto.
    """
    mejor, _ = resolver_con_ganadora(
        rect, velocidad_y, en_el_suelo, pendientes, margen=margen)
    return mejor


def resolver_con_ganadora(
    rect: pygame.Rect,
    velocidad_y: float,
    en_el_suelo: bool,
    pendientes: list[Pendiente],
    margen: float = MARGEN_DE_PEGADO,
) -> tuple[float | None, Pendiente | None]:
    """Lo que devuelve `resolver`, más la pendiente que gana (AUD-324).

    Quien proyecta la velocidad al aterrizar necesita saber **sobre qué**
    aterriza, no sólo a qué altura. `resolver` conserva su contrato (un
    `float`) y esta función es la que lleva el trabajo de verdad.
    """
    if not pendientes or velocidad_y < 0:
        return None, None

    x = float(rect.centerx)
    pies = float(rect.bottom)
    mejor: float | None = None
    ganadora: Pendiente | None = None
    for pendiente in pendientes:
        superficie = pendiente.altura_en(x)
        if superficie is None:
            continue
        # Por debajo del triángulo: el jugador pasa por dentro de la roca, no
        # sobre ella. No es suelo.
        if pies > pendiente.rect.bottom + 1.0:
            continue
        margen_efectivo = margen if en_el_suelo else 1.0
        if pies < superficie - margen_efectivo:
            continue
        # Con dos pendientes solapadas gana la más alta: es la que el jugador
        # está pisando de verdad.
        if mejor is None or superficie < mejor:
            mejor = superficie
            ganadora = pendiente
    return mejor, ganadora


def resolver_lateral(
    rect: pygame.Rect,
    pendientes: list[Pendiente],
    margen: float = MARGEN_DE_PEGADO,
) -> float | None:
    """A qué `x` hay que mover el rectángulo, o `None` si nada lo frena.

    La pared lateral de la rampa (AUD-323), con la misma convención que
    `resolver`: devuelve una coordenada y no muta el rectángulo, que es de
    quien lo posee. Dos paredes, en el orden en que se cruzan:

    * **La cara empinada**: el segmento vertical del extremo alto. Es la
      entrada que dejaba ver el hueco de AUD-297 — el jugador la cruzaba y
      luego el eje Y lo absorbía hacia la superficie de la cuesta.
    * **La hipotenusa a media altura**: en una rampa normal la resuelve el
      eje Y antes de que llegue a importar (el centro entra en el rango
      antes que el borde), pero en una rampa más estrecha que el jugador la
      roca a la altura de los pies tiene huella y hay que frenar en el
      cruce.

    Las dos son **independientes de la dirección**: cruzarse con la pared
    *es* la detección — el rectángulo que la cruza está incrustado, y se
    empuja hacia fuera el mínimo. Quien sólo está rozando la esquina al
    subir o al bajar tiene el centro sobre la rampa y se salta por la regla
    del eje Y; y el pie de la cuesta tampoco es pared, porque quien sube
    desde el suelo llano lo hace por el margen de pegado y frenarlo ahí lo
    congelaría en el primer escalón.
    """
    if not pendientes:
        return None
    px = pygame.Rect(rect)
    pies = float(px.bottom)
    nueva_x: float | None = None
    for pendiente in pendientes:
        # Franja vertical del triángulo: sobrevolando la cima o bajo el pie
        # no hay pared, igual que en `resolver`.
        if (pies < pendiente.rect.top + 1.0
                or pies > pendiente.rect.bottom + 1.0):
            continue
        # El centro sobre la rampa lo resuelve el eje Y: ni pared, ni freno.
        if pendiente.altura_en(px.centerx) is not None:
            continue
        # Cara empinada: el extremo alto es un muro en toda su altura.
        if pendiente.sube_a_la_derecha:
            pared = float(pendiente.rect.right)
            if px.left < pared < px.right:
                px.left = pared
                nueva_x = pared
        else:
            pared = float(pendiente.rect.left)
            if px.left < pared < px.right:
                px.right = pared
                nueva_x = pared - rect.width
        # Hipotenusa: la roca a la altura de los pies ocupa de `cruce` al
        # lado alto (sube a la derecha) o del lado alto a `cruce` (sube a la
        # izquierda); cruzarse con `cruce` es estar incrustado.
        if pendiente.rect.height <= 0:
            continue
        # Cerca del pie la huella es de un píxel y el eje Y la resuelve con
        # el margen de pegado: frenar aquí congelaría al jugador al bajarse.
        if pies >= pendiente.rect.bottom - margen:
            continue
        factor = pendiente.rect.width / pendiente.rect.height
        if pendiente.sube_a_la_derecha:
            cruce = pendiente.rect.left + (pendiente.rect.bottom - pies) * factor
            if px.left <= cruce < px.right:
                px.right = cruce
                nueva_x = cruce - rect.width
        else:
            cruce = pendiente.rect.right - (pendiente.rect.bottom - pies) * factor
            if px.left < cruce <= px.right:
                px.left = cruce
                nueva_x = cruce
    if nueva_x is None or px.x == rect.x:
        return None
    return nueva_x


def componente_de_deslizamiento(
    pendiente: Pendiente,
    velocidad_y: float,
) -> float:
    """Cuánto del impulso de la caída se vuelve horizontal al aterrizar.

    AUD-324 — la proyección de velocidad que `docs/87` §11 pidió por
    escrito. Al caer con `velocidad_y` sobre una cuesta, la componente del
    vector de caída a lo largo de la hipotenusa es
    `sin(fi)·cos(fi)·velocidad_y`, donde `fi` es la inclinación: la
    superficie empuja al jugador cuesta abajo. La componente perpendicular
    la absorbe el suelo.

    El signo lleva la dirección de bajada: `sube_a_la_derecha` baja hacia
    la izquierda (negativo) y su espejo hacia la derecha. Devuelve 0 si no
    hay caída o la pendiente es degenerada.
    """
    if velocidad_y <= 0 or pendiente.rect.height <= 0:
        return 0.0
    ancho = pendiente.rect.width
    alto = pendiente.rect.height
    factor = (ancho * alto) / (ancho * ancho + alto * alto)
    signo = -1.0 if pendiente.sube_a_la_derecha else 1.0
    return signo * velocidad_y * factor
