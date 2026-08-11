"""Capas de colisión sobre el resolutor AABB — AUD-395. Cierra GAP-038.

Por qué existe, y por qué NO vuelve pymunk
==========================================
El filtrado de colisión de este motor estaba escrito a mano en cada sitio que
lo necesitaba. El cargador clasifica la capa `Collision` del TMX en dos listas
—`one_way_rects` si el objeto es de tipo `Platform`, `collision_rects` en
cualquier otro caso— y a partir de ahí cada consumidor recompone lo que
necesita sumando listas: `stage.collision_rects + cerradas + bloques.rects_solidos()`
en `bloques.py`, `self._collision_rects + self._one_way_rects` dentro de una
entrega de estudiante, y una lista distinta por enemigo en `StageScene`.

Funciona, y es exactamente el problema: **la pregunta «¿qué frena a esta
entidad?» no tiene un sitio donde vivir**, así que se responde otra vez, a
mano, en cada llamada. Añadir una clase de sólido —cristal que sólo frena a los
proyectiles, una verja que el jugador cruza y los enemigos no— obliga a tocar
todos esos sitios y a acordarse de todos.

Decisión del dueño (2026-08-11): **capas propias sobre el resolutor AABB
actual, no reintroducir pymunk.** El aviso heredado de la auditoría de julio
sigue en pie y es el motivo: `add_static_collision` creaba un cuerpo y una
forma por *tile*, miles de cajas, y la fachada que se retiró en AUD-004
aparentaba tener categorías de colisión sin tenerlas —asignaba las constantes
`_CAT_*` a `shape.collision_type`, que es la clave de despacho, en vez de a
`shape.filter`, que es el bitmask real, y nunca registró un manejador—. Se
quitó en vez de dejarla mintiendo. Esto es lo que aquella fachada aparentaba
ser, en 60 líneas y sin dependencia nueva.

Cómo se usa
===========
Una entidad declara contra qué choca; el escenario responde con los rectángulos
que le tocan::

    class Fantasma(EnemyBase):
        mascara_de_colision = Capa.SOLIDO      # las plataformas no le frenan

    solidos = stage.capas.solidos_para(enemigo.mascara_de_colision)

Lo que **no** hace, a propósito: no resuelve la colisión ni sustituye a
`resolucion.py`. Devuelve qué rectángulos entran en el cálculo; el cálculo
sigue donde estaba. Un sistema de capas que además resolviera sería el
principio de la tubería de cuerpo rígido que esta decisión descarta.
"""
from __future__ import annotations

from enum import IntFlag

import pygame

__all__ = ["MASCARA_POR_DEFECTO", "Capa", "MapaDeCapas"]


class Capa(IntFlag):
    """Clases de sólido. Es un *bitmask*: se combinan con `|`.

    `IntFlag` y no `Enum` porque la pregunta que se hace no es «¿de qué clase
    eres?» sino «¿estás entre las que me frenan?», y eso es una intersección de
    bits, no una igualdad.
    """

    NADA = 0
    #: Pared, suelo, techo. Lo que frena a todo el mundo por defecto.
    SOLIDO = 1
    #: Plataforma atravesable desde abajo (`Platform` en el TMX). Es la capa
    #: que ya existía de hecho, separada en su propia lista por el cargador.
    PLATAFORMA = 2
    #: Muro que cede a golpes (`bloques.py`). Sólido mientras siga en pie.
    DESTRUCTIBLE = 4
    #: Puerta con cerradura: sólida cerrada, aire abierta.
    PUERTA = 8

    TODO = SOLIDO | PLATAFORMA | DESTRUCTIBLE | PUERTA


#: Lo que frena a una entidad que no dice nada.
#:
#: Son las dos capas que el cargador ya producía, y en ese orden importa el
#: motivo: cualquier entidad anterior a AUD-395 se comportaba como si chocara
#: con los sólidos y con las plataformas, así que ése —y no `TODO`— es el valor
#: que deja el juego exactamente igual que antes. Poner `TODO` habría hecho que
#: entidades que nunca vieron un destructible empezaran a chocar con él.
MASCARA_POR_DEFECTO = Capa.SOLIDO | Capa.PLATAFORMA


class MapaDeCapas:
    """Los rectángulos del escenario, indexados por la clase de sólido que son.

    Se rellena una vez al cargar y se consulta por fotograma, así que la
    consulta compone listas y no las cachea: el número de capas es de un dígito
    y el coste está en el resolutor, no aquí. Si algún día se mide lo
    contrario, éste es el sitio donde poner la caché — y hay que medirlo antes,
    que es la regla de la casa (AUD-329, AUD-330).
    """

    __slots__ = ("_por_capa",)

    def __init__(self) -> None:
        self._por_capa: dict[Capa, list[pygame.Rect]] = {}

    def poner(self, capa: Capa, rects: list[pygame.Rect]) -> None:
        """Declara los rectángulos de una capa. Reemplaza los anteriores."""
        self._por_capa[capa] = rects

    def de(self, capa: Capa) -> list[pygame.Rect]:
        """Los rectángulos de **una** capa concreta."""
        return self._por_capa.get(capa, [])

    def solidos_para(self, mascara: Capa = MASCARA_POR_DEFECTO) -> list[pygame.Rect]:
        """Los rectángulos que frenan a quien lleve esa máscara.

        Devuelve una lista nueva y no una vista: el resolutor la recorre varias
        veces por fotograma y las que se le pasan hoy son listas de verdad.
        Devolver un generador convertiría en un fallo silencioso el segundo
        recorrido, que es peor que copiar unas decenas de referencias.
        """
        if mascara == Capa.NADA:
            return []
        salida: list[pygame.Rect] = []
        for capa, rects in self._por_capa.items():
            if capa & mascara:
                salida.extend(rects)
        return salida

    @property
    def capas_declaradas(self) -> list[Capa]:
        """Qué capas tienen algo. Para el panel de depuración y las pruebas."""
        return [c for c, rects in self._por_capa.items() if rects]
