"""
Objetos con los que el jugador interactúa: recogibles, cerraduras, cofres y disparadores.

F4.1 — de dónde sale esto
=========================
Petición literal de los estudiantes tras jugar la fase 1: *«si se podía agarrar
objetos y llevar[los], abrir jaulas o puertas, además de abrir cofres
misteriosos o activar eventos»*.

El motor ya tenía un `Inventory` con seis mejoras permanentes —vasija de
corazón, pluma veloz— pero **nada recogible en el mapa**: no había forma de
poner un objeto en Tiled y que el jugador lo cogiera. Tampoco había puertas,
ni cofres, ni manera de disparar un evento desde el escenario.

Qué se añade, y por qué estas cuatro cosas
-------------------------------------------
Son las cuatro piezas mínimas con las que se puede construir cualquier
puzle de llave y puerta, que es el patrón que pedían:

- `Recogible` — algo que se coge al pasar por encima o con el botón de agarrar.
- `Cerradura` — puerta o jaula que se abre con una llave concreta.
- `Cofre` — se abre con el botón y entrega su contenido una sola vez.
- `Disparador` — emite un evento del bus; el escenario decide qué significa.

Deliberadamente **no** se añade un sistema de diálogo, ni de comercio, ni de
crafteo. Cada uno de esos exige interfaz propia y ninguno hace falta para lo
que se pidió.

Dónde vive el estado
--------------------
Aquí sólo hay datos y reglas. Ni se dibuja ni se leen teclas: eso lo hace
`InteractableSystem`, que la escena actualiza. La razón es la de siempre en
este proyecto —que el estudiante pueda leer estas reglas sin pelearse con
pygame— y una práctica: así se pueden probar sin abrir una ventana.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pygame

#: Distancia, en píxeles, a la que el jugador puede accionar algo con el botón
#: de agarrar. Generosa a propósito: obligar a la precisión de un píxel para
#: abrir una puerta no añade dificultad, añade frustración.
ALCANCE_DE_USO: int = 24


@dataclass
class Recogible:
    """Un objeto en el suelo. Al cogerlo entra en el llavero o en el inventario.

    `item_id` es libre: `"llave_roja"`, `"heart_vessel"`, `"tuerca"`. Si
    coincide con un objeto de `engine.core.inventory` se aplica su efecto; si
    no, se guarda como llave, que es lo que hace útil el sistema sin obligar
    al estudiante a registrar nada en Python.
    """

    rect: pygame.Rect
    item_id: str
    #: Con `False` hay que pulsar el botón de agarrar. Con `True` basta pasar
    #: por encima, que es lo natural para monedas y objetos menores.
    automatico: bool = True
    #: Texto que se muestra al recogerlo. Vacío = el motor compone uno.
    mensaje: str = ""
    recogido: bool = False


@dataclass
class Cerradura:
    """Puerta o jaula. Se abre con `key_id` y deja de bloquear el paso.

    Mientras está cerrada, su rectángulo es sólido: el jugador choca. Al
    abrirse deja de estarlo, y ahí está toda la mecánica.

    `consume_llave` decide si la llave desaparece al usarse. Por defecto no:
    una llave que se gasta obliga al estudiante a contar cuántas puso, y el
    fallo típico —dejar una puerta imposible— no se ve hasta que alguien juega
    el nivel entero.
    """

    rect: pygame.Rect
    key_id: str
    #: `"puerta"` o `"jaula"`. Sólo cambia el mensaje y el color; se separan
    #: porque una jaula suele contener algo y una puerta da paso.
    clase: str = "puerta"
    consume_llave: bool = False
    mensaje_bloqueado: str = ""
    abierta: bool = False
    #: Evento del bus que se emite al abrirla, si el escenario quiere reaccionar.
    evento_al_abrir: str = ""


@dataclass
class Cofre:
    """Se abre con el botón de agarrar y entrega su contenido una sola vez."""

    rect: pygame.Rect
    contenido: str = ""
    #: Si no está vacío, hace falta esta llave para abrirlo.
    key_id: str = ""
    mensaje: str = ""
    abierto: bool = False
    evento_al_abrir: str = ""


@dataclass
class Disparador:
    """Emite un evento del bus. El escenario decide qué significa.

    Es la pieza que convierte el resto en un sistema abierto: un estudiante
    puede poner un `Disparador` con `evento="ABRIR_COMPUERTA"` y escuchar ese
    nombre desde su escena sin tocar el motor.
    """

    rect: pygame.Rect
    evento: str
    #: Con `True` se dispara al entrar; con `False`, al pulsar el botón.
    automatico: bool = True
    una_vez: bool = True
    #: Si no está vacío, hace falta esta llave para activarlo.
    key_id: str = ""
    disparado: bool = False


@dataclass
class Llavero:
    """Lo que el jugador lleva encima durante el escenario.

    Es un conjunto, no una lista: llevar dos llaves rojas no abre dos puertas
    rojas, y contar duplicados sólo daría oportunidades de equivocarse.
    """

    llaves: set[str] = field(default_factory=set)

    def tiene(self, key_id: str) -> bool:
        return not key_id or key_id in self.llaves

    def coger(self, key_id: str) -> None:
        if key_id:
            self.llaves.add(key_id)

    def gastar(self, key_id: str) -> None:
        self.llaves.discard(key_id)


def alcanza(jugador: pygame.Rect, objetivo: pygame.Rect, margen: int = ALCANCE_DE_USO) -> bool:
    """¿Está el jugador lo bastante cerca para accionar esto?

    Se infla el rectángulo del objetivo en vez del del jugador porque así el
    alcance no depende del tamaño del personaje, que cambia al agacharse.
    """
    return objetivo.inflate(margen * 2, margen * 2).colliderect(jugador)
